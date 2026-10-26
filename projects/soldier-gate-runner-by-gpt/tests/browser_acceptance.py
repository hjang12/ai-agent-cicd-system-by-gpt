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
        cls.playwright.stop()
        cls.server.shutdown()
        cls.server.server_close()
        cls.server_thread.join(timeout=2)

    def test_one_round_starts_gate_applies_and_reset_works(self) -> None:
        page = self.browser.new_page(viewport={"width": 1280, "height": 900})
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(self.base_url + "?testMode=1", wait_until="networkidle")

        self.assertIn("Gatefront", page.title())
        self.assertFalse(page.locator(".intro").is_visible(), "Nonessential intro should not consume playfield space")
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

    def test_page_uses_viewport_without_document_scroll(self) -> None:
        for viewport, mobile in [
            ({"width": 1280, "height": 900}, False),
            ({"width": 390, "height": 844}, True),
        ]:
            page = self.browser.new_page(
                viewport=viewport,
                is_mobile=mobile,
                has_touch=mobile,
            )
            page.goto(self.base_url, wait_until="networkidle")
            dimensions = page.evaluate("""() => ({
                scrollWidth: document.documentElement.scrollWidth,
                clientWidth: document.documentElement.clientWidth,
                scrollHeight: document.documentElement.scrollHeight,
                clientHeight: document.documentElement.clientHeight
            })""")
            self.assertLessEqual(dimensions["scrollWidth"], dimensions["clientWidth"])
            self.assertLessEqual(dimensions["scrollHeight"], dimensions["clientHeight"])
            canvas = page.locator("#gameCanvas").bounding_box()
            assert canvas is not None
            self.assertGreaterEqual(canvas["width"], viewport["width"] * 0.88)
            self.assertTrue(page.locator("#startButton").is_visible())
            page.close()

    def test_low_squad_boss_counterattack_does_not_throw(self) -> None:
        page = self.browser.new_page(viewport={"width": 1280, "height": 900})
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(
            self.base_url + "?testMode=1&testBossCounterattack=1",
            wait_until="networkidle",
        )
        page.get_by_role("button", name="START RUN").click()
        page.wait_for_function(
            "() => document.querySelector('#statusPill').textContent.trim() === 'DEFEAT'",
            timeout=7000,
        )
        self.assertEqual([], errors, "Low-squad boss counterattack raised a browser error")
        page.close()

    def test_arcade_ui_and_blue_red_soldier_palette_render(self) -> None:
        page = self.browser.new_page(viewport={"width": 1280, "height": 900})
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(self.base_url + "?testMode=1", wait_until="networkidle")

        theme = page.evaluate("""() => ({
            colorScheme: getComputedStyle(document.documentElement).colorScheme,
            topbarBackground: getComputedStyle(document.querySelector('.topbar')).backgroundImage,
            primaryButtonColor: getComputedStyle(document.querySelector('.primary-button')).color
        })""")
        self.assertEqual("light", theme["colorScheme"])
        self.assertIn("linear-gradient", theme["topbarBackground"])
        self.assertIn("255, 255, 255", theme["primaryButtonColor"])

        page.get_by_role("button", name="START RUN").click()
        page.wait_for_function(
            "() => document.querySelector('#enemyCount').textContent.trim() === '18 ENEMIES'",
            timeout=7000,
        )
        page.wait_for_timeout(180)
        pixels = page.evaluate("""() => {
            const canvas = document.querySelector('#gameCanvas');
            const {data, width, height} = canvas.getContext('2d').getImageData(0, 0, canvas.width, canvas.height);
            let blueSquad = 0;
            let redEnemy = 0;
            for (let y = 350; y < 505; y++) {
                for (let x = 350; x < 610; x++) {
                    const i = (y * width + x) * 4;
                    const [r, g, b] = data.slice(i, i + 3);
                    if (b > 105 && b > r * 1.35 && b > g * 1.05) blueSquad++;
                }
            }
            for (let y = 100; y < 250; y++) {
                for (let x = 350; x < 610; x++) {
                    const i = (y * width + x) * 4;
                    const [r, g, b] = data.slice(i, i + 3);
                    if (r > 150 && r > g * 1.35 && r > b * 1.18) redEnemy++;
                }
            }
            let allySkin = 0;
            for (let y = 370; y < 470; y++) {
                for (let x = 425; x < 535; x++) {
                    const i = (y * width + x) * 4;
                    const [r, g, b] = data.slice(i, i + 3);
                    if (r > 165 && r - g > 18 && g > b * 1.18 && g < 195 && b > 65) allySkin++;
                }
            }
            return {blueSquad, redEnemy, allySkin};
        }""")
        self.assertGreater(pixels["blueSquad"], 250, "Blue squad uniform palette was not visible")
        self.assertGreater(pixels["redEnemy"], 100, "Red enemy uniform palette was not visible")
        self.assertLess(pixels["allySkin"], 35, "Allied formation should show the rear-facing soldier silhouette, not frontal faces")
        self.assertEqual([], errors, "Browser JavaScript errors were reported")
        page.close()

    def test_squad_fires_continuously_and_hits_reduce_enemy_count(self) -> None:
        page = self.browser.new_page(viewport={"width": 1280, "height": 900})
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(self.base_url + "?testMode=1", wait_until="networkidle")
        page.get_by_role("button", name="START RUN").click()

        # Fire must continue even before a target enters the combat line.
        page.wait_for_function(
            "() => Number(document.querySelector('#gameCanvas').dataset.projectiles || 0) > 0",
            timeout=3000,
        )
        page.wait_for_function(
            "() => document.querySelector('#enemyCount').textContent.trim() === '18 ENEMIES'",
            timeout=7000,
        )
        # Impacts must change the real enemy count, not just play an effect.
        page.wait_for_function(
            "() => Number(document.querySelector('#gameCanvas').dataset.enemyHits || 0) > 0",
            timeout=5000,
        )
        page.wait_for_function(
            "() => { const n = Number(document.querySelector('#gameCanvas').dataset.enemyCount || 0); return n > 0 && n < 18; }",
            timeout=5000,
        )
        self.assertEqual([], errors, "Browser JavaScript errors were reported")
        page.close()

    def test_shootable_target_value_increases_per_hit_and_applies_when_crossed(self) -> None:
        page = self.browser.new_page(viewport={"width": 1280, "height": 900})
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(self.base_url + "?testMode=1&testShootableTarget=1", wait_until="networkidle")
        page.get_by_role("button", name="START RUN").click()
        canvas = page.locator("#gameCanvas")

        page.wait_for_function(
            "() => Number(document.querySelector('#gameCanvas').dataset.shootTargetHits || 0) >= 2",
            timeout=5000,
        )
        page.wait_for_function(
            "() => document.querySelector('#progressCount').textContent.trim() === '1 / 12'",
            timeout=5000,
        )
        hits = int(canvas.get_attribute("data-shoot-target-hits") or "0")
        final_value = int(canvas.get_attribute("data-shoot-target-value") or "0")
        final_squad = int(page.locator("#soldierCount").inner_text().strip())

        self.assertGreaterEqual(hits, 2, "The target should register repeated projectile impacts")
        self.assertEqual(1 + hits, final_value, "Every hit should raise +1 by one")
        self.assertEqual(12 + final_value, final_squad, "Crossing must apply the final displayed target value")
        self.assertEqual([], errors, "Browser JavaScript errors were reported")
        page.close()

    def test_full_round_can_defeat_final_commander(self) -> None:
        page = self.browser.new_page(viewport={"width": 1280, "height": 900})
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(self.base_url + "?testMode=1", wait_until="networkidle")
        page.get_by_role("button", name="START RUN").click()

        canvas = page.locator("#gameCanvas")
        bounds = canvas.bounding_box()
        assert bounds is not None
        drag_y = bounds["y"] + bounds["height"] * 0.78
        left_x = bounds["x"] + bounds["width"] * 0.20
        right_x = bounds["x"] + bounds["width"] * 0.82

        # A deliberately winning route; the sixth arithmetic slot is now a shot-upgraded +1 target.
        # Enemy waves then leave enough units to defeat the commander.
        page.mouse.move(right_x, drag_y)
        page.mouse.down()
        next_gate_route = {
            1: "left",   # gate 2: ×2
            2: "left",   # gate 3: +20%
            4: "right",  # gate 4: ×2
            5: "right",  # gate 5: +50%
            7: "left",   # gate 6: ×2
            9: "right",  # gate 7: +40%
            10: "left",  # gate 8: ×2
        }
        for completed_event in range(1, 12):
            page.wait_for_function(
                f"() => document.querySelector('#progressCount').textContent.trim() === '{completed_event} / 12'",
                timeout=6000,
            )
            if completed_event == 6:
                self.assertGreater(
                    int(page.locator("#soldierCount").inner_text().strip()),
                    120,
                    "Squad growth should not hit the previous low 120-unit ceiling",
                )
            direction = next_gate_route.get(completed_event)
            if direction:
                page.mouse.move(right_x if direction == "right" else left_x, drag_y, steps=2)

        page.mouse.up()
        page.wait_for_function(
            "() => document.querySelector('#statusPill').textContent.trim() === 'VICTORY'",
            timeout=8000,
        )
        self.assertTrue(page.locator("#endOverlay").is_visible())
        self.assertEqual("OPERATION COMPLETE", page.locator("#endKicker").inner_text().strip())
        self.assertEqual("12 / 12", page.locator("#progressCount").inner_text().strip())
        self.assertGreater(int(page.locator("#endSoldierCount").inner_text().strip()), 0)
        self.assertEqual([], errors, "Browser JavaScript errors were reported")
        page.get_by_role("button", name="RUN IT AGAIN").click()
        self.assertEqual("IN RUN", page.locator("#statusPill").inner_text().strip())
        self.assertEqual("12", page.locator("#soldierCount").inner_text().strip())
        page.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
