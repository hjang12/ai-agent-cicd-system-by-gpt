from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock, Thread
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "artifacts" / "ai-level-calibration"
ALLOWED_PAIRS = {"1-2", "2-3", "3-4", "4-5", "5-6"}
ALLOWED_SETUPS = {"classic", "left", "right", "both"}
ALLOWED_FIXTURES = {"initial", "capture", "check", "endgame", "tactical"}
STATUS_PATH = "/api/status"
HEALTH_PATH = "/api/health"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    value = raw.strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be a boolean value")


def _env_int(name: str, default: int, minimum: int = 1) -> int:
    raw = os.environ.get(name)
    value = default if raw is None or not raw.strip() else int(raw)
    if value < minimum:
        raise ValueError(f"{name} must be at least {minimum}")
    return value


def _parse_seeds(raw: str) -> str:
    seeds = [item.strip() for item in raw.split(",") if item.strip()]
    if not seeds:
        raise ValueError("CALIBRATION_SEEDS must contain at least one seed")
    parsed = [int(item) for item in seeds]
    if len(parsed) != len(set(parsed)):
        raise ValueError("CALIBRATION_SEEDS must contain unique seeds")
    return ",".join(str(item) for item in parsed)


def _load_config() -> dict[str, object]:
    pair = os.environ.get("CALIBRATION_PAIR", "2-3").strip()
    if pair not in ALLOWED_PAIRS:
        raise ValueError(f"CALIBRATION_PAIR must be one of {sorted(ALLOWED_PAIRS)}")

    setup = os.environ.get("CALIBRATION_SETUP", "classic").strip()
    if setup not in ALLOWED_SETUPS:
        raise ValueError(f"CALIBRATION_SETUP must be one of {sorted(ALLOWED_SETUPS)}")

    fixture = os.environ.get("CALIBRATION_FIXTURE", "tactical").strip()
    if fixture not in ALLOWED_FIXTURES:
        raise ValueError(f"CALIBRATION_FIXTURE must be one of {sorted(ALLOWED_FIXTURES)}")
    source_revision = os.environ.get("CALIBRATION_SOURCE_REVISION", "").strip() or None
    if fixture != "initial" and setup != "classic":
        raise ValueError("non-initial fixtures require CALIBRATION_SETUP=classic")
    seeds = _parse_seeds(os.environ.get("CALIBRATION_SEEDS", "20261005"))
    games = _env_int("CALIBRATION_GAMES", 2, minimum=2)
    if games % 2:
        raise ValueError("CALIBRATION_GAMES must be an even integer")
    max_plies = _env_int("CALIBRATION_MAX_PLIES", 96)
    output_dir = Path(
        os.environ.get("CALIBRATION_OUTPUT_DIR", str(DEFAULT_OUTPUT_DIR))
    ).expanduser()
    if not output_dir.is_absolute():
        output_dir = (ROOT / output_dir).resolve()
    else:
        output_dir = output_dir.resolve()

    try:
        output_dir.relative_to(ROOT)
    except ValueError as exc:
        raise ValueError("CALIBRATION_OUTPUT_DIR must remain inside the project root") from exc

    return {
        "pair": pair,
        "seeds": seeds,
        "setup": setup,
        "fixture": fixture,
        "source_revision": source_revision,
        "games": games,
        "max_plies": max_plies,
        "output_dir": output_dir,
    }


def _safe_artifact_name(name: str) -> str:
    candidate = Path(name)
    if candidate.name != name or name in {"", ".", ".."}:
        raise ValueError("invalid artifact name")
    return name


class CalibrationRunner:
    def __init__(self, config: dict[str, object]) -> None:
        self.config = config
        self.output_dir = config["output_dir"]
        assert isinstance(self.output_dir, Path)
        self._lock = Lock()
        self._status: dict[str, object] = {
            "state": "pending",
            "enabled": False,
            "started_at": None,
            "completed_at": None,
            "return_code": None,
            "error": None,
            "request": {
                "pair": config["pair"],
                "seeds": config["seeds"],
                "setup": config["setup"],
                "fixture": config["fixture"],
                "source_revision": config["source_revision"],
                "games": config["games"],
                "max_plies": config["max_plies"],
                "output_dir": str(self.output_dir.relative_to(ROOT)),
            },
            "artifacts": [],
        }

    def status(self) -> dict[str, object]:
        with self._lock:
            payload = dict(self._status)
            payload["artifacts"] = self._artifact_names()
            return payload

    def run(self) -> None:
        try:
            enabled = _env_bool("CALIBRATION_ENABLED", False)
        except ValueError as exc:
            self._finish_with_error(str(exc), return_code=2)
            return

        with self._lock:
            self._status["enabled"] = enabled

        if not enabled:
            with self._lock:
                self._status["state"] = "disabled"
            print("Calibration runner is idle: CALIBRATION_ENABLED is not true.")
            return

        self.output_dir.mkdir(parents=True, exist_ok=True)
        command = [
            sys.executable,
            "tools/run_ai_level_calibration.py",
            "--pair",
            str(self.config["pair"]),
            "--seed",
            str(self.config["seeds"]),
            "--setup",
            str(self.config["setup"]),
            "--fixture",
            str(self.config["fixture"]),
            "--games",
            str(self.config["games"]),
            "--max-plies",
            str(self.config["max_plies"]),
            "--output-dir",
            str(self.output_dir),
            "--keep-going",
        ]
        source_revision = self.config.get("source_revision")
        if isinstance(source_revision, str) and source_revision:
            command.extend(["--source-revision", source_revision])

        with self._lock:
            self._status["state"] = "running"
            self._status["started_at"] = _utc_now()

        print("Calibration request:")
        print(json.dumps(self.status()["request"], ensure_ascii=False, indent=2))
        print("$", " ".join(command))

        try:
            completed = subprocess.run(
                command,
                cwd=ROOT,
                check=False,
            )
        except Exception as exc:
            self._finish_with_error(
                f"{type(exc).__name__}: {exc}",
                return_code=1,
            )
            return

        with self._lock:
            self._status["return_code"] = completed.returncode
            self._status["completed_at"] = _utc_now()
            self._status["state"] = (
                "completed" if completed.returncode == 0 else "failed"
            )

        print("Calibration artifacts:")
        for artifact_name in self._artifact_names():
            try:
                payload, _ = self.read_artifact(artifact_name)
            except (ValueError, FileNotFoundError, OSError) as exc:
                print(f"ARTIFACT {artifact_name} UNAVAILABLE: {exc}")
                continue
            print(f"ARTIFACT {artifact_name} BEGIN")
            print(payload.decode("utf-8"))
            print(f"ARTIFACT {artifact_name} END")

        print(
            "Calibration runner finished:",
            json.dumps(self.status(), ensure_ascii=False),
        )

    def _finish_with_error(self, message: str, *, return_code: int) -> None:
        with self._lock:
            self._status["error"] = message
            self._status["return_code"] = return_code
            self._status["completed_at"] = _utc_now()
            self._status["state"] = "failed"
        print(f"Calibration runner error: {message}")

    def _artifact_names(self) -> list[str]:
        if not self.output_dir.exists():
            return []
        return sorted(
            path.name
            for path in self.output_dir.iterdir()
            if path.is_file() and path.suffix.lower() == ".json"
        )

    def read_artifact(self, name: str) -> tuple[bytes, str]:
        safe_name = _safe_artifact_name(name)
        path = (self.output_dir / safe_name).resolve()
        try:
            path.relative_to(self.output_dir)
        except ValueError as exc:
            raise ValueError("invalid artifact path") from exc
        if not path.is_file():
            raise FileNotFoundError(name)
        return path.read_bytes(), "application/json; charset=utf-8"


CONFIG = _load_config()
RUNNER = CalibrationRunner(CONFIG)


class RequestHandler(BaseHTTPRequestHandler):
    server_version = "PersonalAIJanggiCalibrationRunner/1.0"

    def _send_json(
        self,
        payload: object,
        status: HTTPStatus = HTTPStatus.OK,
    ) -> None:
        raw = json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        ).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def _send_bytes(
        self,
        payload: bytes,
        content_type: str,
        status: HTTPStatus = HTTPStatus.OK,
    ) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def do_HEAD(self) -> None:
        path = urlparse(self.path).path
        if path == HEALTH_PATH:
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Length", "0")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            return
        self.send_response(HTTPStatus.NOT_FOUND)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == HEALTH_PATH:
            self._send_json({"status": "ok", "runner": RUNNER.status()["state"]})
            return
        if path == STATUS_PATH:
            self._send_json(RUNNER.status())
            return
        prefix = "/api/artifacts/"
        if path.startswith(prefix):
            name = unquote(path[len(prefix):])
            try:
                payload, content_type = RUNNER.read_artifact(name)
            except (ValueError, FileNotFoundError):
                self._send_json({"error": "artifact_not_found"}, HTTPStatus.NOT_FOUND)
                return
            self._send_bytes(payload, content_type)
            return
        self._send_json({"error": "not_found"}, HTTPStatus.NOT_FOUND)

    def log_message(self, format: str, *args: object) -> None:
        print(f"{self.address_string()} - {format % args}")


def main() -> None:
    port = int(os.environ.get("PORT", "10000"))
    server = ThreadingHTTPServer(("0.0.0.0", port), RequestHandler)
    worker = Thread(target=RUNNER.run, name="calibration-runner", daemon=True)
    worker.start()
    print(f"Listening on http://0.0.0.0:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
