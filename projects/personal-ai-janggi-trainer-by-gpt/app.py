from __future__ import annotations

import json
import os
import secrets
from http.cookies import SimpleCookie
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import RLock
from urllib.parse import urlparse

from janggi import AILevel, Analyzer, GameRecord, Match, Move, NegamaxEngine, SearchConfig, Side, adaptive_problem_priority, adaptive_reason_priority, ai_level_payload, coach_move, generate_training_problems, get_ai_level, review_record, select_adaptive_training_problems, state_to_dict
from janggi.analysis import MoveAnalysis
from janggi.review import DEFAULT_REVIEW_LIMIT
from janggi.training_metrics import TrainingSessionMetrics
from janggi.training_problems import DEFAULT_PROBLEM_LIMIT, MAX_PROBLEM_LIMIT
from janggi.engine import EngineAnalysis, validate_engine_analysis, validate_engine_move


ROOT = Path(__file__).resolve().parent
INDEX_HTML = ROOT / "index.html"
ENGINE_SEARCH_DEPTH = 1
ENGINE_QUIESCENCE_DEPTH = 0
ENGINE_ROOT_REFINEMENT_COUNT = 0
ANALYSIS_SEARCH_DEPTH = 2
DEFAULT_PLAYER_SIDE = Side.CHO
DEFAULT_AI_SIDE = Side.HAN
DEFAULT_AI_LEVEL = AILevel.BEGINNER
SESSION_COOKIE_NAME = "janggi_session"
SESSION_TOKEN_BYTES = 32
MAX_SESSIONS = 512


def _is_valid_session_id(value: object) -> bool:
    return isinstance(value, str) and 32 <= len(value) <= 128 and all(
        char.isalnum() or char in "_-" for char in value
    )


class TrainerSessionStore:
    """Keep each browser session isolated within this server process."""

    def __init__(self, max_sessions: int = MAX_SESSIONS) -> None:
        if not isinstance(max_sessions, int) or isinstance(max_sessions, bool) or max_sessions < 1:
            raise ValueError("max_sessions must be a positive integer")
        self._lock = RLock()
        self._max_sessions = max_sessions
        self._sessions: dict[str, TrainerApplication] = {}

    def get_or_create(self, session_id: object = None) -> tuple[str, TrainerApplication, bool]:
        with self._lock:
            if _is_valid_session_id(session_id) and session_id in self._sessions:
                return session_id, self._sessions[session_id], False

            if len(self._sessions) >= self._max_sessions:
                oldest_session_id = next(iter(self._sessions))
                del self._sessions[oldest_session_id]

            new_session_id = secrets.token_urlsafe(SESSION_TOKEN_BYTES)
            application = TrainerApplication()
            self._sessions[new_session_id] = application
            return new_session_id, application, True

    def size(self) -> int:
        with self._lock:
            return len(self._sessions)


class TrainerApplication:
    def __init__(self) -> None:
        self._lock = RLock()
        self.player_side = DEFAULT_PLAYER_SIDE
        self.ai_side = DEFAULT_AI_SIDE
        self.ai_level = DEFAULT_AI_LEVEL
        self.match = Match.new()
        self.engine = NegamaxEngine(get_ai_level(self.ai_level).config)
        self.analysis_engine = NegamaxEngine(SearchConfig(depth=ANALYSIS_SEARCH_DEPTH))
        self.analyzer = Analyzer(self.analysis_engine)
        self.training_metrics = TrainingSessionMetrics()

    def snapshot(self) -> dict[str, object]:
        with self._lock:
            return {
                "status": self.match.status.value,
                "setup": self.match.setup,
                "player_side": self.player_side.value,
                "ai_side": self.ai_side.value,
                "ai_level": self.ai_level.value,
                "ai_level_name": get_ai_level(self.ai_level).name,
                "can_undo": self.can_undo(),
                "state": state_to_dict(self.match.state, setup=self.match.setup),
                "legal_moves": [
                    {"src": list(move.src) if move.src is not None else None,
                     "dst": list(move.dst) if move.dst is not None else None,
                     "pass": move.is_pass}
                    for move in self.match.legal_moves()
                ],
            }

    def record(self) -> dict[str, object]:
        with self._lock:
            status = self.match.status.value
            result = status if status != "playing" else None
            record = GameRecord(
                setup=self.match.setup,
                moves=self.match.state.history,
                result=result,
                source="personal",
            )
            return record.to_dict()

    def reset(
        self,
        setup: str = "classic",
        player_side: str = "cho",
        ai_level: str = DEFAULT_AI_LEVEL.value,
    ) -> dict[str, object]:
        selected_side = self._side_from_value(player_side)
        selected_level = get_ai_level(ai_level)
        with self._lock:
            self.player_side = selected_side
            self.ai_side = selected_side.opponent
            self.ai_level = selected_level.level
            self.engine = NegamaxEngine(selected_level.config)
            self.match = Match.new(setup=setup)
            self.training_metrics.reset()
            if self.match.status.value == "playing" and self.match.state.turn is self.ai_side:
                self._apply_ai_move()
            return self.snapshot()

    def play(self, payload: dict[str, object]) -> dict[str, object]:
        move = self._move_from_payload(payload)
        with self._lock:
            self._ensure_player_turn()
            self.match = self.match.play(move)
            return self.snapshot()

    def play_player_turn(self, payload: dict[str, object]) -> dict[str, object]:
        """Apply one human move and one AI reply as one atomic application turn.

        The gameplay path deliberately does not run the heavyweight coaching
        analyzer. A played move must either complete the full turn or leave
        the match unchanged; detailed move analysis remains available through
        /api/analyze/move.
        """
        move = self._move_from_payload(payload)
        with self._lock:
            self._ensure_player_turn()
            original_match = self.match
            state_before = self.match.state
            moved_piece = None
            captured_piece = None
            if move.src is not None:
                source = state_before.piece_at(move.src)
                moved_piece = source.kind if source is not None else None
            if move.dst is not None:
                target = state_before.piece_at(move.dst)
                captured_piece = target.kind if target is not None else None

            try:
                self.match = self.match.play(move)
                player_analysis = MoveAnalysis(
                    move=move,
                    recommended_move=None,
                    score_before_cp=None,
                    score_after_cp=None,
                    score_delta_cp=None,
                    depth=None,
                    nodes=None,
                    perspective=state_before.turn,
                    moved_piece=moved_piece,
                    captured_piece=captured_piece,
                    gives_check=self.match.state.is_in_check(state_before.turn.opponent),
                )
                player_coaching = coach_move(player_analysis)

                engine_analysis = EngineAnalysis(perspective=self.match.state.turn)
                if self.match.status.value == "playing" and self.match.state.turn is self.ai_side:
                    engine_analysis = validate_engine_analysis(
                        self.match.state,
                        self.engine.analyze(self.match.state),
                    )
                    if engine_analysis.best_move is not None:
                        validate_engine_move(self.engine, self.match.state, engine_analysis.best_move)
                        self.match = self.match.play(engine_analysis.best_move)

                return {
                    "player_analysis": _analysis_to_dict(player_analysis),
                    "player_coaching": _coaching_to_dict(player_coaching),
                    "engine_analysis": _analysis_to_dict(engine_analysis),
                    "snapshot": self.snapshot(),
                }
            except Exception:
                self.match = original_match
                raise

    def undo(self) -> dict[str, object]:
        with self._lock:
            if not self.can_undo():
                raise ValueError("cannot undo before the player's first move")
            last_move_was_ai = self.match.state.turn is self.player_side
            self.match = self.match.undo()
            if last_move_was_ai and self.match.state.history:
                self.match = self.match.undo()
            return self.snapshot()

    def can_undo(self) -> bool:
        if not self.match.state.history:
            return False
        if (
            self.player_side is Side.HAN
            and len(self.match.state.history) == 1
            and self.match.state.turn is self.player_side
        ):
            return False
        return True

    def analyze_move(self, payload: dict[str, object]) -> dict[str, object]:
        move = self._move_from_payload(payload)
        with self._lock:
            analysis = self.analyzer.analyze_move(self.match.state, move)
            coaching = coach_move(analysis)
            return {
                "analysis": _analysis_to_dict(analysis),
                "coaching": _coaching_to_dict(coaching),
                "snapshot": self.snapshot(),
            }

    def review(self, payload: dict[str, object]) -> dict[str, object]:
        limit = payload.get("limit", DEFAULT_REVIEW_LIMIT)
        if not isinstance(limit, int) or isinstance(limit, bool):
            raise ValueError("limit must be an integer")
        with self._lock:
            status = self.match.status.value
            result = status if status != "playing" else None
            record = GameRecord(
                setup=self.match.setup,
                moves=self.match.state.history,
                result=result,
                source="personal",
            )
            review = review_record(
                record,
                self.analyzer,
                max_moves=limit,
                side=self.player_side,
            )
            return _review_to_dict(review)

    def training_problems(self, payload: dict[str, object]) -> dict[str, object]:
        review_limit = payload.get("review_limit", DEFAULT_REVIEW_LIMIT)
        problem_limit = payload.get("problem_limit", DEFAULT_PROBLEM_LIMIT)
        include_solution = payload.get("include_solution", False)
        if not isinstance(review_limit, int) or isinstance(review_limit, bool):
            raise ValueError("review_limit must be an integer")
        if not isinstance(problem_limit, int) or isinstance(problem_limit, bool):
            raise ValueError("problem_limit must be an integer")
        if not isinstance(include_solution, bool):
            raise ValueError("include_solution must be boolean")

        with self._lock:
            status = self.match.status.value
            result = status if status != "playing" else None
            record = GameRecord(
                setup=self.match.setup,
                moves=self.match.state.history,
                result=result,
                source="personal",
            )
            review = review_record(
                record,
                self.analyzer,
                max_moves=review_limit,
                side=self.player_side,
            )
            metrics = self.training_metrics.snapshot()
            candidates = generate_training_problems(review, max_problems=MAX_PROBLEM_LIMIT)
            problems = select_adaptive_training_problems(
                candidates,
                metrics,
                max_problems=problem_limit,
            )
            return {
                "reviewed_moves": review.reviewed_moves,
                "problem_count": len(problems),
                "priority_reason_codes": [reason.value for reason in adaptive_reason_priority(metrics)],
                "priority_problem_ids": list(adaptive_problem_priority(metrics)),
                "problems": [_training_problem_to_dict(problem, include_solution=include_solution) for problem in problems],
                "metrics": _training_metrics_to_dict(metrics),
            }

    def training_problem_answer(self, payload: dict[str, object]) -> dict[str, object]:
        problem_id = payload.get("problem_id")
        if not isinstance(problem_id, str):
            raise ValueError("problem_id must be a string")
        move = self._move_from_payload(payload)
        with self._lock:
            status = self.match.status.value
            result = status if status != "playing" else None
            record = GameRecord(
                setup=self.match.setup,
                moves=self.match.state.history,
                result=result,
                source="personal",
            )
            review = review_record(
                record,
                self.analyzer,
                max_moves=DEFAULT_REVIEW_LIMIT,
                side=self.player_side,
            )
            problems = generate_training_problems(review, max_problems=MAX_PROBLEM_LIMIT)
            problem = next((item for item in problems if item.problem_id == problem_id), None)
            if problem is None:
                raise ValueError("training problem not found")
            try:
                move_is_legal = problem.state.apply(move) is not None
            except (TypeError, ValueError, IndexError):
                move_is_legal = False
            if not move_is_legal:
                return {
                    "correct": False,
                    "legal": False,
                    "target_move": _move_to_dict(problem.target_move),
                    "message": "그 수는 이 훈련 포지션에서 둘 수 없습니다.",
                    "next_action": problem.next_action,
                }
            correct = move == problem.target_move
            self.training_metrics.record_attempt(
                problem_id=problem.problem_id,
                correct=correct,
                reason_codes=problem.reason_codes,
            )
            return {
                "correct": correct,
                "legal": True,
                "target_move": _move_to_dict(problem.target_move),
                "original_move": _move_to_dict(problem.original_move),
                "message": problem.explanation if correct else "추천수와 다른 수입니다. 같은 포지션의 핵심 문제를 다시 확인하세요.",
                "next_action": problem.next_action,
                "reason_codes": [reason.value for reason in problem.reason_codes],
                "metrics": _training_metrics_to_dict(self.training_metrics.snapshot()),
            }

    def training_metrics_snapshot(self) -> dict[str, object]:
        with self._lock:
            return _training_metrics_to_dict(self.training_metrics.snapshot())

    def engine_move(self) -> dict[str, object]:
        with self._lock:
            self._ensure_ai_turn()
            analysis = self._apply_ai_move()
            return {"analysis": _analysis_to_dict(analysis), "snapshot": self.snapshot()}

    def _apply_ai_move(self) -> EngineAnalysis:
        analysis = validate_engine_analysis(self.match.state, self.engine.analyze(self.match.state))
        if analysis.best_move is not None:
            validate_engine_move(self.engine, self.match.state, analysis.best_move)
            self.match = self.match.play(analysis.best_move)
        return analysis

    @staticmethod
    def _side_from_value(value: str) -> Side:
        try:
            return Side(value)
        except ValueError as exc:
            raise ValueError("player_side must be cho or han") from exc

    def _ensure_player_turn(self) -> None:
        if self.match.status.value != "playing":
            raise ValueError("game is not in progress")
        if self.match.state.turn is not self.player_side:
            raise ValueError("it is the AI's turn")

    def _ensure_ai_turn(self) -> None:
        if self.match.status.value != "playing":
            raise ValueError("game is not in progress")
        if self.match.state.turn is not self.ai_side:
            raise ValueError("it is the player's turn")

    @staticmethod
    def _move_from_payload(payload: dict[str, object]) -> Move:
        src = payload.get("src")
        dst = payload.get("dst")
        if not isinstance(src, list) or not isinstance(dst, list):
            raise ValueError("src and dst must be [x, y] lists")
        if len(src) != 2 or len(dst) != 2 or not all(
            isinstance(value, int) and not isinstance(value, bool)
            for value in (*src, *dst)
        ):
            raise ValueError("src and dst must contain two integer coordinates")
        return Move((src[0], src[1]), (dst[0], dst[1]))


def _analysis_to_dict(analysis: object) -> dict[str, object]:
    return {
        "best_move": _move_to_dict(getattr(analysis, "best_move", None)),
        "score_cp": getattr(analysis, "score_cp", None),
        "depth": getattr(analysis, "depth", None),
        "nodes": getattr(analysis, "nodes", None),
        "principal_variation": [
            _move_to_dict(move) for move in getattr(analysis, "principal_variation", ())
        ],
        "perspective": getattr(getattr(analysis, "perspective", None), "value", None),
        "move": _move_to_dict(getattr(analysis, "move", None)),
        "recommended_move": _move_to_dict(getattr(analysis, "recommended_move", None)),
        "score_before_cp": getattr(analysis, "score_before_cp", None),
        "score_after_cp": getattr(analysis, "score_after_cp", None),
        "score_delta_cp": getattr(analysis, "score_delta_cp", None),
        "is_best_move": getattr(analysis, "is_best_move", None),
        "moved_piece": getattr(getattr(analysis, "moved_piece", None), "value", None),
        "captured_piece": getattr(getattr(analysis, "captured_piece", None), "value", None),
        "gives_check": getattr(analysis, "gives_check", False),
        "destination_attacked": getattr(analysis, "destination_attacked", False),
        "tactical_risk": getattr(getattr(analysis, "tactical_risk", None), "value", None),
        "tactical_motifs": [
            motif.value for motif in getattr(analysis, "tactical_motifs", ())
        ],
    }


def _coaching_to_dict(coaching: object) -> dict[str, object]:
    severity = getattr(getattr(coaching, "severity", None), "value", None)
    return {
        "severity": severity,
        "message": getattr(coaching, "message", None),
        "score_delta_cp": getattr(coaching, "score_delta_cp", None),
        "next_action": getattr(coaching, "next_action", None),
        "reason_codes": [
            reason.value for reason in getattr(coaching, "reason_codes", ())
        ],
    }


def _review_to_dict(review: object) -> dict[str, object]:
    return {
        "total_moves": getattr(review, "total_moves", 0),
        "reviewed_moves": getattr(review, "reviewed_moves", 0),
        "skipped_moves": getattr(review, "skipped_moves", 0),
        "reason_counts": {
            reason.value: count
            for reason, count in getattr(review, "reason_counts", ())
        },
        "severity_counts": {
            severity.value: count
            for severity, count in getattr(review, "severity_counts", ())
        },
        "entries": [
            {
                "ply": entry.ply,
                "side": entry.side.value,
                "move": _move_to_dict(entry.move),
                "recommended_move": _move_to_dict(entry.analysis.recommended_move),
                "severity": entry.insight.severity.value,
                "score_delta_cp": entry.insight.score_delta_cp,
                "message": entry.insight.message,
                "next_action": entry.insight.next_action,
                "reason_codes": [reason.value for reason in entry.insight.reason_codes],
            }
            for entry in getattr(review, "entries", ())
        ],
    }


def _training_metrics_to_dict(metrics: object) -> dict[str, object]:
    return {
        "attempts": getattr(metrics, "attempts", 0),
        "correct": getattr(metrics, "correct", 0),
        "incorrect": getattr(metrics, "incorrect", 0),
        "unique_problems": getattr(metrics, "unique_problems", 0),
        "accuracy": getattr(metrics, "accuracy", 0.0),
        "problem_attempts": dict(getattr(metrics, "problem_attempts", ())),
        "problem_incorrect": dict(getattr(metrics, "problem_incorrect", ())),
        "reason_attempts": {
            reason.value: count
            for reason, count in getattr(metrics, "reason_attempts", ())
        },
        "reason_correct": {
            reason.value: count
            for reason, count in getattr(metrics, "reason_correct", ())
        },
    }


def _training_problem_to_dict(problem: object, *, include_solution: bool) -> dict[str, object]:
    state = getattr(problem, "state")
    payload = {
        "problem_id": getattr(problem, "problem_id"),
        "ply": getattr(problem, "ply"),
        "side": getattr(getattr(problem, "side"), "value", None),
        "state": state_to_dict(state, setup=None),
        "legal_moves": [
            _move_to_dict(move) for move in state.legal_moves(include_pass=True)
        ],
        "original_move": _move_to_dict(getattr(problem, "original_move")),
        "severity": getattr(getattr(problem, "severity"), "value", None),
        "reason_codes": [reason.value for reason in getattr(problem, "reason_codes", ())],
        "prompt": getattr(problem, "prompt"),
        "explanation": getattr(problem, "explanation"),
        "next_action": getattr(problem, "next_action"),
    }
    if include_solution:
        payload["target_move"] = _move_to_dict(getattr(problem, "target_move"))
    return payload


def _move_to_dict(move: object) -> object:
    if move is None:
        return None
    src = getattr(move, "src", None)
    dst = getattr(move, "dst", None)
    return {
        "src": list(src) if src is not None else None,
        "dst": list(dst) if dst is not None else None,
        "pass": getattr(move, "is_pass", False),
    }


SESSION_STORE = TrainerSessionStore()


class RequestHandler(BaseHTTPRequestHandler):
    server_version = "PersonalAIJanggiTrainer/0.1"

    def _session_application(self) -> TrainerApplication:
        if hasattr(self, "_application"):
            return self._application
        cookie = SimpleCookie()
        cookie.load(self.headers.get("Cookie", ""))
        raw_session_id = cookie.get(SESSION_COOKIE_NAME)
        session_id, application, is_new = SESSION_STORE.get_or_create(
            raw_session_id.value if raw_session_id is not None else None
        )
        self._session_id = session_id
        self._application = application
        self._session_cookie_pending = is_new
        return application

    def _set_session_cookie(self) -> None:
        if not getattr(self, "_session_cookie_pending", False):
            return
        attributes = [
            f"{SESSION_COOKIE_NAME}={self._session_id}",
            "HttpOnly",
            "Path=/",
            "SameSite=Lax",
        ]
        if self.headers.get("X-Forwarded-Proto", "").lower() == "https":
            attributes.append("Secure")
        self.send_header("Set-Cookie", "; ".join(attributes))
        self._session_cookie_pending = False

    def _send_json(self, payload: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        raw = json.dumps(
            payload,
            ensure_ascii=False,
            default=lambda value: value.value if hasattr(value, "value") else str(value),
        ).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self._set_session_cookie()
        self.end_headers()
        self.wfile.write(raw)

    def _read_json(self) -> dict[str, object]:
        raw_length = self.headers.get("Content-Length", "0")
        try:
            length = int(raw_length)
        except ValueError as exc:
            raise ValueError("invalid Content-Length") from exc
        if length < 0 or length > 1_000_000:
            raise ValueError("request body is too large")
        data = json.loads(self.rfile.read(length).decode("utf-8")) if length else {}
        if not isinstance(data, dict):
            raise ValueError("JSON body must be an object")
        return data

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/":
            self._session_application()
            self._send_index()
            return
        if path == "/api/health":
            self._send_json({"status": "ok"})
            return
        application = self._session_application()
        if path == "/api/state":
            self._send_json(application.snapshot())
            return
        if path == "/api/ai/levels":
            self._send_json({"levels": ai_level_payload(), "current": application.snapshot()["ai_level"]})
            return
        if path == "/api/record":
            self._send_json(application.record())
            return
        if path == "/api/training/metrics":
            self._send_json(application.training_metrics_snapshot())
            return
        self._send_json({"error": "not_found"}, HTTPStatus.NOT_FOUND)

    def _send_index(self) -> None:
        try:
            raw = INDEX_HTML.read_bytes()
        except OSError:
            self._send_json({"error": "index_unavailable"}, HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self._set_session_cookie()
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
            application = self._session_application()
            if path == "/api/reset":
                payload = self._read_json()
                setup = payload.get("setup", "classic")
                player_side = payload.get("player_side", "cho")
                ai_level = payload.get("ai_level", DEFAULT_AI_LEVEL.value)
                if not isinstance(setup, str):
                    raise ValueError("setup must be a string")
                if not isinstance(player_side, str):
                    raise ValueError("player_side must be a string")
                if not isinstance(ai_level, str):
                    raise ValueError("ai_level must be a string")
                self._send_json(application.reset(setup=setup, player_side=player_side, ai_level=ai_level))
                return
            if path == "/api/move":
                self._send_json(application.play(self._read_json()))
                return
            if path == "/api/player/turn":
                self._send_json(application.play_player_turn(self._read_json()))
                return
            if path == "/api/undo":
                self._send_json(application.undo())
                return
            if path == "/api/analyze/move":
                self._send_json(application.analyze_move(self._read_json()))
                return
            if path == "/api/engine/move":
                self._send_json(application.engine_move())
                return
            if path == "/api/review":
                self._send_json(application.review(self._read_json()))
                return
            if path == "/api/training/problems":
                self._send_json(application.training_problems(self._read_json()))
                return
            if path == "/api/training/answer":
                self._send_json(application.training_problem_answer(self._read_json()))
                return
            self._send_json({"error": "not_found"}, HTTPStatus.NOT_FOUND)
        except (ValueError, KeyError, TypeError) as exc:
            self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)


    def log_message(self, format: str, *args: object) -> None:
        print(f"{self.address_string()} - {format % args}")


def main() -> None:
    host = "0.0.0.0"
    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer((host, port), RequestHandler)
    print(f"Listening on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
