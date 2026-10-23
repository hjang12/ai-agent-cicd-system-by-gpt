from __future__ import annotations

import threading
import unittest
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class QuietStaticHandler(SimpleHTTPRequestHandler):
    def log_message(self, _format: str, *_args: object) -> None:
        return


class GatefrontBrowserAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        handler = partial(QuietStaticHandler, directory=str(PROJECT_ROOT))
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}/"
        cls.playwright_manager = sync_playwright()
        cls.playwright = cls.playwright_manager.start()
        cls.browser = cls.playwright.chromium.launch()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.browser.close()
        cls.playwright_manager.stop()
        cls.server.shutdown()
        cls.server.server_close()
        cls.server_thread.join(timeout=2)

    def test_one_round_starts_gate_applies_and_reset_works(self) -> None:
        page = self.browser.new_page(viewport={"width": 1280, "height": 900})
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(self.base_url + "?testMode=1", wait_until="networkidle")

        self.assertIn("Gatefront", page.title())
        self.assertTrue(page.get_by_role("heading", name="ONE RUN. BUILD YOUR SQUAD.").is_visible())
        self.assertEqual("12", page.locator("#soldierCount").inner_text().strip())
        self.assertEqual("0 / 12", page.locator("#progressCount").inner_text().strip())
        self.assertTrue(page.locator("#gameCanvas").is_visible())

        page.get_by_role("button", name="START RUN").click()
        self.assertEqual("IN RUN", page.locator("#statusPill").inner_text().strip())

        canvas = page.locator("#gameCanvas")
        bounds = canvas.bounding_box()
        assert bounds is not None
        right_x = bounds["x"] + bounds["width"] * 0.82
        drag_y = bounds["y"] + bounds["height"] * 0.78
        page.mouse.move(right_x, drag_y)
        page.mouse.down()
        page.mouse.move(right_x - 6, drag_y, steps=3)

        page.wait_for_function(
            """() => document.querySelector('#progressCount').textContent.trim() === '1 / 12'
                && document.querySelector('#soldierCount').textContent.trim() === '18'""",
            timeout=7000,
        )
        page.mouse.up()
        self.assertIn("Gate 1", page.locator("#gameMessage").inner_text())
        self.assertEqual([], errors, "Browser JavaScript errors were reported")

        page.get_by_role("button", name="RESET RUN").click()
        self.assertTrue(page.locator("#startOverlay").is_visible())
        self.assertEqual("READY", page.locator("#statusPill").inner_text().strip())
        self.assertEqual("12", page.locator("#soldierCount").inner_text().strip())
        self.assertEqual("0 / 12", page.locator("#progressCount").inner_text().strip())
        page.close()

    def test_mobile_canvas_fits_viewport(self) -> None:
        page = self.browser.new_page(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
        page.goto(self.base_url, wait_until="networkidle")
        self.assertTrue(page.locator("#startButton").is_visible())
        canvas = page.locator("#gameCanvas").bounding_box()
        assert canvas is not None
        self.assertLessEqual(canvas["width"], 390)
        self.assertLessEqual(page.evaluate("document.documentElement.scrollWidth"), 390)
        page.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
