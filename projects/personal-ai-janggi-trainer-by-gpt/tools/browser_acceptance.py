from __future__ import annotations

import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import unittest
from pathlib import Path
from typing import Any

from playwright.sync_api import Browser, BrowserContext, Page, expect, sync_playwright


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROGRESS_KEY = "personal-ai-janggi-progress-v1"
SETUPS = ("classic", "left", "right", "both")
LEVELS = ("1", "2", "3", "4", "5", "6")


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def _get_health(base_url: str) -> dict[str, Any]:
    with urllib.request.urlopen(f"{base_url}/api/health", timeout=3) as response:
        if response.status != 200:
            raise RuntimeError(f"Health endpoint returned HTTP {response.status}")
        return json.loads(response.read().decode("utf-8"))


class JanggiBrowserAcceptanceTests(unittest.TestCase):
    """Chromium smoke tests for setup, turn feedback, learning, and local growth data.

    If JANGGI_BASE_URL is unset, the checked-out app is started locally. Set it
    to run the same interactions against the live service after a deployment.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.base_url = os.environ.get("JANGGI_BASE_URL", "").rstrip("/")
        cls.server: subprocess.Popen[str] | None = None
        cls.server_log = None

        if not cls.base_url:
            port = _free_port()
            cls.base_url = f"http://127.0.0.1:{port}"
            environment = os.environ.copy()
            environment["PORT"] = str(port)
            environment["PYTHONUNBUFFERED"] = "1"
            cls.server_log = tempfile.TemporaryFile(mode="w+")
            cls.server = subprocess.Popen(
                [sys.executable, "app.py"],
                cwd=PROJECT_ROOT,
                env=environment,
                stdout=cls.server_log,
                stderr=subprocess.STDOUT,
                text=True,
            )
            deadline = time.monotonic() + 20
            last_error: Exception | None = None
            while time.monotonic() < deadline:
                if cls.server.poll() is not None:
                    cls.server_log.seek(0)
                    raise RuntimeError(
                        "Local app exited before becoming healthy. Logs:\n" + cls.server_log.read()
                    )
                try:
                    health = _get_health(cls.base_url)
                    if health.get("status") == "ok":
                        break
                except (urllib.error.URLError, TimeoutError, ValueError, RuntimeError) as exc:
                    last_error = exc
                time.sleep(0.2)
            else:
                cls.server_log.seek(0)
                raise RuntimeError(
                    f"Local app health check timed out: {last_error}\nLogs:\n{cls.server_log.read()}"
                )
        else:
            health = _get_health(cls.base_url)
            if health.get("status") != "ok":
                raise RuntimeError(f"Unexpected health payload: {health!r}")

        cls.playwright = sync_playwright().start()
        cls.browser: Browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls) -> None:
        browser = getattr(cls, "browser", None)
        if browser:
            browser.close()
        playwright = getattr(cls, "playwright", None)
        if playwright:
            playwright.stop()
        server = getattr(cls, "server", None)
        if server and server.poll() is None:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=5)
        server_log = getattr(cls, "server_log", None)
        if server_log:
            server_log.close()

    def setUp(self) -> None:
        self.context: BrowserContext = self.browser.new_context(
            viewport={"width": 1440, "height": 900}
        )
        self.page: Page = self.context.new_page()
        self.page_errors: list[str] = []
        self.page.on("pageerror", lambda error: self.page_errors.append(str(error)))
        self._open_app()

    def tearDown(self) -> None:
        self.context.close()
        self.assertEqual([], self.page_errors, "Unexpected uncaught browser JavaScript error")

    def _open_app(self) -> None:
        response = self.page.goto(self.base_url, wait_until="domcontentloaded", timeout=30_000)
        self.assertIsNotNone(response, "App navigation did not produce an HTTP response")
        self.assertEqual(response.status, 200, "App root should return HTTP 200")
        expect(self.page.locator("#setup-screen")).to_be_visible(timeout=15_000)
        self.page.wait_for_function(
            "() => document.querySelector('#ai-level-note')?.textContent.includes('Lv.')",
            timeout=15_000,
        )

    def _state(self) -> dict[str, Any]:
        return self.page.evaluate(
            """async () => {
              const response = await fetch('/api/state', {cache:'no-store'});
              if (!response.ok) throw new Error('State API returned ' + response.status);
              return await response.json();
            }"""
        )

    def _start_game(self, level: str = "1", side: str = "cho", setup: str = "classic") -> dict[str, Any]:
        setup_screen = self.page.locator("#setup-screen")
        if not setup_screen.is_visible():
            self.page.locator("#replay-button").click()
            expect(setup_screen).to_be_visible(timeout=5_000)
        self.page.locator(f'.level-option[data-level="{level}"]').click()
        self.page.locator(f'.side-option[data-side="{side}"]').click()
        self.page.locator(f'.setup-variant[data-setup="{setup}"]').click()
        self.page.locator("#reset").click()
        expect(setup_screen).to_be_hidden(timeout=20_000)
        expect(self.page.locator("#board .cell")).to_have_count(90, timeout=10_000)
        return self._state()

    @staticmethod
    def _square_selector(position: list[int]) -> str:
        x, y = position
        coordinate = f"{chr(ord('a') + x)}{y + 1}"
        return f'#board .cell[aria-label$="{coordinate}"]'

    def _play_move(self, move: dict[str, Any]) -> None:
        source = self.page.locator(self._square_selector(move["src"]))
        destination = self.page.locator(self._square_selector(move["dst"]))
        expect(source).to_have_count(1)
        expect(destination).to_have_count(1)
        source.click()
        expect(source).to_have_class(re.compile(r"\bselected\b"), timeout=3_000)
        expect(destination).to_have_class(re.compile(r"\blegal\b"), timeout=3_000)
        destination.click()

    def _first_legal_move(self) -> dict[str, Any]:
        for move in self._state().get("legal_moves", []):
            if move.get("src") is not None and move.get("dst") is not None:
                return move
        self.fail("No non-pass legal move is available in the current state")

    def _wait_for_side_to_move(self, side: str, timeout: int = 20_000) -> None:
        label = "초" if side == "cho" else "한"
        self.page.wait_for_function(
            "(label) => document.querySelector('#turn')?.textContent === '현재 차례: ' + label",
            arg=label,
            timeout=timeout,
        )

    def test_all_six_levels_and_four_initial_setups_start(self) -> None:
        self.assertEqual(6, self.page.locator("#ai-level-options .level-option").count())
        self.assertEqual(4, self.page.locator("#setup-variant-options .setup-variant").count())
        self.assertEqual(2, self.page.locator("#side-options .side-option").count())
        for level in LEVELS:
            for setup in SETUPS:
                state = self._start_game(level=level, side="cho", setup=setup)
                self.assertEqual(level, state["ai_level"], f"Wrong selected level for {setup}")
                self.assertEqual(setup, state["setup"], f"Wrong initial setup for level {level}")
                self.assertEqual("cho", state["player_side"])
                self.assertEqual("cho", state["state"]["turn"])
                self.assertEqual([], state["state"]["history"])
                self.assertEqual(90, len(state["state"]["board"]))

    def test_han_side_waits_for_ai_opening_and_returns_the_turn_to_han(self) -> None:
        state = self._start_game(level="1", side="han", setup="classic")
        self.assertEqual("han", state["player_side"])
        self.assertEqual("cho", state["ai_side"])
        self.assertEqual("han", state["state"]["turn"])
        self.assertEqual(1, len(state["state"]["history"]))
        self._wait_for_side_to_move("han")
        self.assertIn("초", self.page.locator("#heading").inner_text())

    def test_undo_reverts_a_full_turn_and_replay_applies_new_settings(self) -> None:
        initial = self._start_game(level="2", side="cho", setup="left")
        player_move = self._first_legal_move()
        self._play_move(player_move)
        self._wait_for_side_to_move("cho")

        self.page.wait_for_function(
            """async () => {
              const response = await fetch('/api/state', {cache:'no-store'});
              if (!response.ok) return false;
              const state = await response.json();
              return state.state.history.length === 2;
            }""",
            timeout=15_000,
        )
        after_turn = self._state()
        self.assertEqual(2, len(after_turn["state"]["history"]))

        self.page.locator("#undo").click()
        self.page.wait_for_function(
            """async () => {
              const response = await fetch('/api/state', {cache:'no-store'});
              if (!response.ok) return false;
              const state = await response.json();
              return state.state.history.length === 0 && state.state.turn === 'cho';
            }""",
            timeout=15_000,
        )
        undone = self._state()
        self.assertEqual([], undone["state"]["history"])
        self.assertEqual(initial["state"]["board"], undone["state"]["board"])

        self.page.locator("#replay-button").click()
        expect(self.page.locator("#setup-screen")).to_be_visible(timeout=5_000)
        self.page.locator('.level-option[data-level="3"]').click()
        self.page.locator('.side-option[data-side="han"]').click()
        self.page.locator('.setup-variant[data-setup="both"]').click()
        self.page.locator("#reset").click()
        expect(self.page.locator("#setup-screen")).to_be_hidden(timeout=15_000)
        replayed = self._state()
        self.assertEqual("3", replayed["ai_level"])
        self.assertEqual("han", replayed["player_side"])
        self.assertEqual("both", replayed["setup"])
        self.assertEqual("han", replayed["state"]["turn"])
        self.assertEqual(1, len(replayed["state"]["history"]))
        self._wait_for_side_to_move("han")

    def test_human_move_is_shown_before_ai_reply_and_learning_analysis_opens(self) -> None:
        self.page.add_init_script(
            """(() => {
              const originalFetch = window.fetch.bind(window);
              window.fetch = async (input, init) => {
                const url = typeof input === 'string' ? input : (input && input.url) || '';
                if (url.endsWith('/api/engine/move')) {
                  await new Promise(resolve => setTimeout(resolve, 1200));
                }
                return originalFetch(input, init);
              };
            })();"""
        )
        self.page.reload(wait_until="domcontentloaded")
        expect(self.page.locator("#setup-screen")).to_be_visible(timeout=10_000)
        self._start_game(level="1", side="cho", setup="classic")
        move = self._first_legal_move()
        self._play_move(move)
        self.page.wait_for_function(
            "() => document.querySelector('#board .board-message-title')?.textContent === 'AI 생각 중…'",
            timeout=8_000,
        )
        destination = self.page.locator(self._square_selector(move["dst"]))
        expect(destination).to_have_class(re.compile(r"\blast-move-to\b"), timeout=3_000)
        self.page.wait_for_function(
            "() => document.querySelector('#turn')?.textContent === '현재 차례: 초'",
            timeout=20_000,
        )
        expect(self.page.locator("#board .board-message")).not_to_have_class(
            re.compile(r"\bvisible\b"), timeout=3_000
        )
        expect(self.page.locator("#analysis-open")).to_be_visible(timeout=3_000)
        before_analysis_state = self._state()
        self.page.locator("#analysis-open").click()
        expect(self.page.locator("#learning-modal")).to_be_visible(timeout=5_000)
        expect(self.page.locator("#analysis")).to_be_visible()
        self.assertIn("착수 분석", self.page.locator("#learning-modal-title").inner_text())
        after_analysis_state = self._state()
        self.assertEqual(before_analysis_state["status"], after_analysis_state["status"])
        self.assertEqual(before_analysis_state["state"], after_analysis_state["state"])
        self.page.locator("#learning-close").click()
        self._wait_for_side_to_move("cho")

    def test_check_message_is_visible_after_ai_reply(self) -> None:
        def inject_check(route: Any) -> None:
            response = route.fetch()
            payload = response.json()
            payload["snapshot"]["in_check"] = True
            route.fulfill(response=response, json=payload)

        self.page.route("**/api/engine/move", inject_check)
        self._start_game(level="1", side="cho", setup="classic")
        self._play_move(self._first_legal_move())

        self.page.wait_for_function(
            "() => document.querySelector('#game-message')?.textContent.includes('장군!')",
            timeout=20_000,
        )
        expect(self.page.locator("#board .board-message")).to_have_class(
            re.compile(r"\bvisible\b"), timeout=3_000
        )
        self.assertIn("장군!", self.page.locator("#board .board-message-title").inner_text())

    def test_bikjang_terminal_message_is_visible(self) -> None:
        def inject_bikjang(route: Any) -> None:
            response = route.fetch()
            payload = response.json()
            payload["snapshot"]["status"] = "draw_bikjang"
            route.fulfill(response=response, json=payload)

        self.page.route("**/api/engine/move", inject_bikjang)
        self._start_game(level="1", side="cho", setup="classic")
        self._play_move(self._first_legal_move())

        expect(self.page.locator("#match-result")).to_be_visible(timeout=20_000)
        self.assertIn("무승부", self.page.locator("#match-result-title").inner_text())
        expect(self.page.locator("#board .board-message")).to_have_class(
            re.compile(r"\bvisible\b"), timeout=3_000
        )
        self.assertIn("빅장으로 무승부", self.page.locator("#board .board-message-title").inner_text())

    def test_ai_api_error_clears_thinking_overlay_and_recovers_the_board(self) -> None:
        self.page.route("**/api/engine/move", lambda route: route.abort())
        self._start_game(level="1", side="cho", setup="classic")
        move = self._first_legal_move()
        self._play_move(move)

        self.page.wait_for_function(
            "() => document.querySelector('#heading')?.textContent === 'AI 응수 상태 확인'",
            timeout=20_000,
        )
        expect(self.page.locator("#board .board-message")).not_to_have_class(
            re.compile(r"\bvisible\b"), timeout=3_000
        )
        self.assertIn("AI 응수 상태를 다시 확인했습니다.", self.page.locator("#game-message").inner_text())
        recovered = self._state()
        self.assertEqual("playing", recovered["status"])
        self.assertEqual("han", recovered["state"]["turn"])
        self.assertEqual(1, len(recovered["state"]["history"]))

    def test_review_training_answer_and_local_progress_persist_after_reload(self) -> None:
        human_move_count = {"value": 0}
        training_responses: list[dict[str, Any]] = []

        def terminalize_third_human_move(route: Any) -> None:
            response = route.fetch()
            payload = response.json()
            human_move_count["value"] += 1
            if human_move_count["value"] == 3 and payload.get("status") == "playing":
                # Force the browser's result surface after three valid moves; keep the
                # server-side session isolated and its legal move handling real.
                payload["status"] = "cho_win"
            route.fulfill(response=response, json=payload)

        self.page.route("**/api/move", terminalize_third_human_move)

        def capture_training(response: Any) -> None:
            if response.url.endswith("/api/training/problems") and response.request.method == "POST":
                training_responses.append(response.json())

        self.page.on("response", capture_training)
        self._start_game(level="1", side="cho", setup="classic")
        for index in range(3):
            self._play_move(self._first_legal_move())
            if index < 2:
                self._wait_for_side_to_move("cho")
            else:
                expect(self.page.locator("#match-result")).to_be_visible(timeout=10_000)
                self.assertIn("승리", self.page.locator("#match-result-title").inner_text())

        saved = self.page.evaluate("(key) => JSON.parse(window.localStorage.getItem(key))", PROGRESS_KEY)
        self.assertEqual(1, saved["totals"]["games"], "One completed game should be recorded")
        self.assertEqual(1, len(saved["games"]), "The completed game detail should be idempotent")
        self.assertEqual("1", saved["games"][0]["level"], "The result must retain the selected AI level")

        self.page.locator("#postgame-review").click()
        expect(self.page.locator("#learning-modal")).to_be_visible(timeout=20_000)
        expect(self.page.locator("#review-panel")).to_be_visible()
        self.assertGreater(int(self.page.locator("#reviewed-count").inner_text()), 0)
        self.page.locator("#learning-close").click()
        expect(self.page.locator("#match-result")).to_be_visible()
        self.assertIn("승리", self.page.locator("#match-result-title").inner_text())

        self.page.locator("#postgame-training").click()
        expect(self.page.locator("#learning-modal")).to_be_visible(timeout=20_000)
        expect(self.page.locator("#training-panel")).to_be_visible()
        self.assertTrue(training_responses, "Training API response was not captured")
        problems = training_responses[-1].get("problems", [])
        self.assertGreater(
            len(problems), 0,
            "Representative legal game should yield at least one review-derived training problem",
        )
        expect(self.page.locator("#training-list button").first).to_be_visible(timeout=5_000)
        # The regular training response intentionally omits target_move so the UI
        # does not reveal the answer before the learner submits it. Obtain the
        # deterministic test solution through the explicit include_solution API.
        target = self.page.evaluate(
            """async (problemId) => {
              const response = await fetch('/api/training/problems', {
                method: 'POST',
                headers: {'Content-Type':'application/json'},
                body: JSON.stringify({review_limit:20, problem_limit:5, include_solution:true})
              });
              if (!response.ok) throw new Error('Solution fixture request returned ' + response.status);
              const payload = await response.json();
              const problem = (payload.problems || []).find(item => item.problem_id === problemId);
              return problem?.target_move || null;
            }""",
            problems[0]["problem_id"],
        )
        self.assertIsNotNone(target, "Explicit test solution was not returned for the visible problem")
        self.page.locator("#training-list button").first.click()
        self._play_move({"src": target["src"], "dst": target["dst"]})
        expect(self.page.locator("#learning-modal")).to_be_visible(timeout=15_000)
        expect(self.page.locator("#training-result")).to_be_visible()
        self.assertIn("정답입니다", self.page.locator("#training-result").inner_text())

        saved = self.page.evaluate("(key) => JSON.parse(window.localStorage.getItem(key))", PROGRESS_KEY)
        self.assertEqual(1, saved["totals"]["trainingAttempts"])
        self.assertEqual(1, saved["totals"]["trainingCorrect"])
        self.assertEqual("100%", self.page.locator("#training-accuracy").inner_text())
        self.assertEqual(1, saved["totals"]["games"], "Repeated renders must not record the same completed game twice")
        self.assertEqual(1, len(saved["games"]), "Completed-game history must remain idempotent")

        self.page.locator("#learning-close").click()
        self.page.locator("#postgame-reset").click()
        expect(self.page.locator("#setup-screen")).to_be_visible(timeout=5_000)
        self.page.locator("#progress-open").click()
        expect(self.page.locator("#progress-modal")).to_be_visible(timeout=5_000)
        self.assertIn("1전", self.page.locator("#progress-summary").inner_text())
        level_history = self.page.locator("#progress-level-list").inner_text()
        self.assertIn("Lv.1 입문", level_history)
        self.assertIn("1전 · 1승 0무 0패", level_history)
        self.page.locator("#progress-close").click()

        self.page.reload(wait_until="domcontentloaded")
        expect(self.page.locator("#setup-screen")).to_be_visible(timeout=10_000)
        self.page.wait_for_function(
            "() => document.querySelector('#ai-level-note')?.textContent.includes('Lv.')",
            timeout=10_000,
        )
        self.page.locator("#progress-open").click()
        expect(self.page.locator("#progress-modal")).to_be_visible(timeout=5_000)
        self.assertIn("1전", self.page.locator("#progress-summary").inner_text())
        self.assertIn("훈련", self.page.locator("#progress-modal").inner_text())

    def test_malformed_local_progress_does_not_block_starting_a_game(self) -> None:
        self.page.close()
        self.context.close()
        self.context = self.browser.new_context(viewport={"width": 1440, "height": 900})
        self.page = self.context.new_page()
        self.page_errors = []
        self.page.on("pageerror", lambda error: self.page_errors.append(str(error)))
        self.page.add_init_script(
            """() => {
              try { localStorage.setItem('personal-ai-janggi-progress-v1', '{not-json'); }
              catch (_) {}
            }"""
        )
        self._open_app()
        self.page.locator("#progress-open").click()
        expect(self.page.locator("#progress-modal")).to_be_visible()
        self.assertTrue(self.page.locator("#progress-note").inner_text().strip())
        self.page.locator("#progress-close").click()
        self.assertEqual("playing", self._start_game()["status"])

    def test_unavailable_local_storage_does_not_block_the_app(self) -> None:
        self.page.close()
        self.context.close()
        self.context = self.browser.new_context(viewport={"width": 1440, "height": 900})
        self.page = self.context.new_page()
        self.page_errors = []
        self.page.on("pageerror", lambda error: self.page_errors.append(str(error)))
        self.page.add_init_script(
            """() => {
              Object.defineProperty(window, 'localStorage', {
                configurable: true,
                get() { throw new DOMException('blocked', 'SecurityError'); }
              });
            }"""
        )
        self._open_app()
        self.page.locator("#progress-open").click()
        expect(self.page.locator("#progress-modal")).to_be_visible()
        self.assertIn("저장", self.page.locator("#progress-note").inner_text())
        self.page.locator("#progress-close").click()
        self.assertEqual("playing", self._start_game()["status"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
