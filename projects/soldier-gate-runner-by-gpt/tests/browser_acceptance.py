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

    @staticmethod
    def lane_screen_x(page, lane: float) -> float:
        bounds = page.locator("#gameCanvas").bounding_box()
        assert bounds is not None
        world_width = page.locator("#gameCanvas").evaluate("(canvas) => canvas.width")
        road_width = world_width * (220 + 660 * ((424 - 66) / (560 - 66))) / 960
        road_left = (world_width - road_width) / 2
        logical_x = road_left + road_width * lane
        return bounds["x"] + bounds["width"] * logical_x / world_width

    def steer_to_lane(self, page, lane: float, keep_dragging: bool = False) -> None:
        bounds = page.locator("#gameCanvas").bounding_box()
        assert bounds is not None
        x = self.lane_screen_x(page, lane)
        y = bounds["y"] + bounds["height"] * 0.78
        if keep_dragging:
            # The caller already holds the pointer down so continuous steering stays active.
            page.mouse.move(x, y, steps=3)
        else:
            page.mouse.move(x, y)
            page.mouse.down()
            page.mouse.move(x, y, steps=3)
            page.mouse.up()

    def test_one_round_starts_gate_applies_and_reset_works(self) -> None:
        page = self.browser.new_page(viewport={"width": 1280, "height": 900})
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(self.base_url + "?testMode=1", wait_until="networkidle")

        self.assertIn("Gatefront", page.title())
        self.assertFalse(page.locator(".intro").is_visible(), "Nonessential intro should not consume playfield space")
        self.assertEqual("12", page.locator("#soldierCount").inner_text().strip())
        self.assertEqual("0 / 13", page.locator("#progressCount").inner_text().strip())
        self.assertTrue(page.locator("#gameCanvas").is_visible())
        self.assertTrue(page.locator("#resetButton").is_visible())
        self.assertEqual(1, page.locator("#resetButton").evaluate("(button) => button.closest('.topbar') !== null"))
        self.assertFalse(page.locator(".run-footer").count(), "The bottom overlay footer should not cover the road")
        self.assertEqual(4, page.locator(".speed-button").count())

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
            """() => document.querySelector('#progressCount').textContent.trim() === '1 / 13'
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
        self.assertEqual("0 / 13", page.locator("#progressCount").inner_text().strip())
        self.assertEqual("1", page.locator("#gameCanvas").get_attribute("data-game-speed"))
        page.close()

    def test_speed_multiplier_controls_world_time_and_persist_through_reset(self) -> None:
        page = self.browser.new_page(viewport={"width": 1280, "height": 900})
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(self.base_url + "?testMode=1&testSpeedControls=1", wait_until="networkidle")
        canvas = page.locator("#gameCanvas")
        page.get_by_role("button", name="START RUN").click()
        self.assertEqual("1", canvas.get_attribute("data-game-speed"))
        page.wait_for_timeout(350)
        before_x1 = float(canvas.get_attribute("data-simulation-seconds") or "0")
        page.wait_for_timeout(350)
        delta_x1 = float(canvas.get_attribute("data-simulation-seconds") or "0") - before_x1
        page.get_by_role("button", name="Set game speed to ×2").click()
        self.assertEqual("2", canvas.get_attribute("data-game-speed"))
        self.assertEqual("true", page.get_by_role("button", name="Set game speed to ×2").get_attribute("aria-pressed"))
        before_x2 = float(canvas.get_attribute("data-simulation-seconds") or "0")
        page.wait_for_timeout(350)
        delta_x2 = float(canvas.get_attribute("data-simulation-seconds") or "0") - before_x2

        page.get_by_role("button", name="Set game speed to ×3").click()
        self.assertEqual("3", canvas.get_attribute("data-game-speed"))
        self.assertEqual("true", page.get_by_role("button", name="Set game speed to ×3").get_attribute("aria-pressed"))
        before_x3 = float(canvas.get_attribute("data-simulation-seconds") or "0")
        page.wait_for_timeout(350)
        delta_x3 = float(canvas.get_attribute("data-simulation-seconds") or "0") - before_x3
        page.get_by_role("button", name="Set game speed to ×4").click()
        self.assertEqual("4", canvas.get_attribute("data-game-speed"))
        self.assertEqual("true", page.get_by_role("button", name="Set game speed to ×4").get_attribute("aria-pressed"))
        before_x4 = float(canvas.get_attribute("data-simulation-seconds") or "0")
        page.wait_for_timeout(350)
        delta_x4 = float(canvas.get_attribute("data-simulation-seconds") or "0") - before_x4
        self.assertGreater(delta_x1, 0.1, "The world clock should advance at ×1")
        self.assertGreater(delta_x2, delta_x1 * 1.5, "The world clock should advance faster at ×2")
        self.assertGreater(delta_x3, delta_x2 * 1.25, "The world clock should advance faster again at ×3")
        self.assertGreater(delta_x4, delta_x3 * 1.2, "The world clock should advance faster again at ×4")
        page.get_by_role("button", name="RESET RUN").click()
        self.assertTrue(page.locator("#startOverlay").is_visible())
        self.assertEqual("4", canvas.get_attribute("data-game-speed"), "Speed selection should persist across reset")
        self.assertEqual([], errors, "Speed controls raised a browser error")
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
            frame = page.locator("#gameFrame").bounding_box()
            assert canvas is not None and frame is not None
            self.assertAlmostEqual(canvas["x"], 0, delta=1)
            self.assertAlmostEqual(canvas["y"], 0, delta=1)
            self.assertAlmostEqual(canvas["width"], viewport["width"], delta=1)
            self.assertAlmostEqual(canvas["height"], viewport["height"], delta=1)
            self.assertAlmostEqual(frame["x"], 0, delta=1)
            self.assertAlmostEqual(frame["y"], 0, delta=1)
            self.assertAlmostEqual(frame["width"], viewport["width"], delta=1)
            self.assertAlmostEqual(frame["height"], viewport["height"], delta=1)
            self.assertTrue(page.locator("#startButton").is_visible())
            page.close()

    def test_squad_stays_in_one_lane_and_grows_backward(self) -> None:
        measurements = []
        for size in ("small", "large"):
            page = self.browser.new_page(viewport={"width": 1280, "height": 900})
            query = "?testMode=1" if size == "small" else "?testMode=1&testCombatScaling=enemy"
            page.goto(self.base_url + query, wait_until="networkidle")
            page.get_by_role("button", name="START RUN").click()
            expected_soldiers = "12" if size == "small" else "1000"
            self.assertEqual(expected_soldiers, page.locator("#soldierCount").inner_text().strip())
            canvas = page.locator("#gameCanvas")
            expected_visible = "12" if size == "small" else "60"
            page.wait_for_function(
                f"() => document.querySelector('#gameCanvas').dataset.squadVisibleCount === '{expected_visible}'",
                timeout=2000,
            )
            metrics = canvas.evaluate("""canvas => {
                const worldWidth = canvas.width;
                const roadWidth = worldWidth * (220 + 660 * ((424 - 47 - 66) / (560 - 66))) / 960;
                const roadLeft = (worldWidth - roadWidth) / 2;
                const laneIndex = Number(canvas.dataset.squadLane) - 1;
                const laneWidth = roadWidth / 3;
                return {
                    lane: Number(canvas.dataset.squadLane),
                    laneCount: Number(canvas.dataset.laneCount),
                    columns: Number(canvas.dataset.squadColumns),
                    rows: Number(canvas.dataset.squadRows),
                    visibleCount: Number(canvas.dataset.squadVisibleCount),
                    centerX: Number(canvas.dataset.squadCenterX),
                    halfWidth: Number(canvas.dataset.squadHalfWidth),
                    laneLeft: roadLeft + laneWidth * laneIndex,
                    laneRight: roadLeft + laneWidth * (laneIndex + 1)
                };
            }""")
            lane_left = metrics["laneLeft"]
            lane_right = metrics["laneRight"]
            self.assertGreaterEqual(
                metrics["centerX"] - metrics["halfWidth"],
                lane_left,
                "Squad formation must remain inside its selected lane",
            )
            self.assertLessEqual(
                metrics["centerX"] + metrics["halfWidth"],
                lane_right,
                "The complete squad formation must not straddle the road divider",
            )
            measurements.append(metrics)
            page.close()

        small, large = measurements
        self.assertEqual(3, small["laneCount"], "The road should expose three lanes")
        self.assertGreaterEqual(small["columns"], 3, "Squad should be visibly arranged in at least three columns")
        self.assertLessEqual(small["columns"], 4, "Desktop formation should use no more than four columns")
        self.assertEqual(4, small["columns"], "Desktop formation should use four separated columns")
        self.assertEqual(small["lane"], large["lane"], "Squad growth must not move the formation to another lane")
        self.assertEqual(
            small["columns"],
            large["columns"],
            "Adding soldiers must not widen or reshape the formation",
        )
        self.assertGreater(large["rows"], small["rows"], "Additional soldiers should form rows behind the front rank")
        self.assertGreater(large["visibleCount"], small["visibleCount"])
        self.assertLessEqual(large["rows"], 15, "The representative formation should stay inside the screen")

    def test_mobile_formation_stays_inside_selected_lane(self) -> None:
        page = self.browser.new_page(
            viewport={"width": 390, "height": 844},
            is_mobile=True,
            has_touch=True,
        )
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(self.base_url + "?testMode=1", wait_until="networkidle")
        page.get_by_role("button", name="START RUN").click()
        canvas = page.locator("#gameCanvas")
        page.wait_for_function(
            "() => Number(document.querySelector('#gameCanvas').dataset.squadColumns || 0) >= 2",
            timeout=2000,
        )
        metrics = canvas.evaluate("""canvas => {
            const worldWidth = canvas.width;
            const roadWidth = worldWidth * (220 + 660 * ((424 - 47 - 66) / (560 - 66))) / 960;
            const roadLeft = (worldWidth - roadWidth) / 2;
            const laneIndex = Number(canvas.dataset.squadLane) - 1;
            const laneWidth = roadWidth / 3;
            return {
                columns: Number(canvas.dataset.squadColumns),
                centerX: Number(canvas.dataset.squadCenterX),
                halfWidth: Number(canvas.dataset.squadHalfWidth),
                laneLeft: roadLeft + laneWidth * laneIndex,
                laneRight: roadLeft + laneWidth * (laneIndex + 1)
            };
        }""")
        self.assertGreaterEqual(metrics["columns"], 2)
        self.assertLessEqual(metrics["columns"], 4)
        self.assertGreaterEqual(
            metrics["centerX"] - metrics["halfWidth"],
            metrics["laneLeft"],
            "Mobile squad left edge must stay inside the selected lane",
        )
        self.assertLessEqual(
            metrics["centerX"] + metrics["halfWidth"],
            metrics["laneRight"],
            "Mobile squad right edge must stay inside the selected lane",
        )
        self.assertEqual([], errors, "Mobile formation raised a browser error")
        page.close()

    def test_enemies_are_hit_while_still_far_away(self) -> None:
        page = self.browser.new_page(viewport={"width": 1280, "height": 900})
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(
            self.base_url + "?testMode=1&testEarlyEnemy=1",
            wait_until="networkidle",
        )
        page.get_by_role("button", name="START RUN").click()
        canvas = page.locator("#gameCanvas")
        page.wait_for_function(
            "() => Number(document.querySelector('#gameCanvas').dataset.enemyHitsBeforeEngagement || 0) > 0",
            timeout=5000,
        )
        hit_y = float(canvas.get_attribute("data-early-enemy-hit-y") or "9999")
        self.assertGreater(int(canvas.get_attribute("data-enemy-hits") or "0"), 0)
        self.assertLess(
            hit_y,
            424 - 180,
            "At least one real projectile should hit the enemy before it reaches the close-range combat line",
        )
        page.wait_for_function(
            "() => document.querySelector('#gameCanvas').dataset.enemyEngagedId === '3'",
            timeout=6000,
        )
        self.assertEqual("100", canvas.get_attribute("data-enemy-wave-initial-count"))
        self.assertGreater(
            int(canvas.get_attribute("data-enemy-engaged-count") or "0"),
            0,
            "The enemy wave should still be present at engagement for this fixture",
        )
        self.assertLess(
            int(canvas.get_attribute("data-enemy-engaged-count") or "100"),
            100,
            "Long-range hits must persist; engagement must not restore the enemy's initial count",
        )
        self.assertEqual([], errors, "Long-range combat raised a browser error")
        page.close()

    def test_first_enemy_is_hit_soon_after_appearing(self) -> None:
        page = self.browser.new_page(viewport={"width": 1280, "height": 900})
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(self.base_url + "?testMode=1&testFirstContactEnemy=1", wait_until="networkidle")
        page.get_by_role("button", name="START RUN").click()
        canvas = page.locator("#gameCanvas")
        page.wait_for_function(
            "() => document.querySelector('#gameCanvas').dataset.enemyWaveInitialCount === '18'",
            timeout=7000,
        )
        page.wait_for_function(
            "() => Number(document.querySelector('#gameCanvas').dataset.enemyHits || 0) > 0",
            timeout=2500,
        )
        spawn_time = float(canvas.get_attribute("data-enemy-spawn-seconds") or "0")
        first_hit_time = float(canvas.get_attribute("data-first-enemy-hit-seconds") or "99")
        self.assertEqual("true", canvas.get_attribute("data-player-bullets-lane-forward"))
        self.assertGreater(first_hit_time, 0)
        self.assertLess(first_hit_time - spawn_time, 0.8, "The opening contact shot should reach the enemy within 0.8 simulation seconds")
        self.assertEqual([], errors, "First-contact firing raised a browser error")
        self.assertEqual("true", canvas.get_attribute("data-player-bullets-straight"))
        page.close()

    def test_player_bullets_travel_straight_without_target_tracking(self) -> None:
        page = self.browser.new_page(viewport={"width": 1280, "height": 900})
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(self.base_url + "?testMode=1&testEarlyEnemy=1", wait_until="networkidle")
        page.get_by_role("button", name="START RUN").click()
        canvas = page.locator("#gameCanvas")
        page.wait_for_function(
            "() => Number(document.querySelector('#gameCanvas').dataset.straightProjectiles || 0) > 0",
            timeout=2000,
        )
        self.assertEqual("true", canvas.get_attribute("data-player-bullets-straight"))
        page.wait_for_timeout(350)
        self.assertEqual("true", canvas.get_attribute("data-player-bullets-straight"))
        self.assertGreater(int(canvas.get_attribute("data-straight-projectiles") or "0"), 0)
        self.assertEqual([], errors, "Straight-forward fire raised a browser error")
        page.close()

    def test_enemy_formation_shrinks_visibly_as_its_count_falls(self) -> None:
        page = self.browser.new_page(viewport={"width": 1280, "height": 900})
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(self.base_url + "?testMode=1&testEarlyEnemy=1", wait_until="networkidle")
        page.get_by_role("button", name="START RUN").click()
        canvas = page.locator("#gameCanvas")
        page.wait_for_function(
            "() => Number(document.querySelector('#gameCanvas').dataset.enemyVisibleCount || 0) === 32",
            timeout=2000,
        )
        page.wait_for_function(
            "() => Number(document.querySelector('#gameCanvas').dataset.enemyVisibleCount || 32) < 32",
            timeout=4000,
        )
        self.assertLess(int(canvas.get_attribute("data-enemy-count") or "100"), 100)
        self.assertEqual([], errors, "Enemy visual casualty tracking raised a browser error")
        page.close()

    def test_enemy_squad_fires_visible_projectiles_that_can_hit_the_player(self) -> None:
        page = self.browser.new_page(viewport={"width": 1280, "height": 900})
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(self.base_url + "?testMode=1&testEnemyFire=1", wait_until="networkidle")
        page.get_by_role("button", name="START RUN").click()
        canvas = page.locator("#gameCanvas")
        page.wait_for_function(
            "() => Number(document.querySelector('#gameCanvas').dataset.enemyProjectiles || 0) > 0",
            timeout=2500,
        )
        page.wait_for_function(
            "() => Number(document.querySelector('#gameCanvas').dataset.enemyProjectileHits || 0) > 0",
            timeout=3500,
        )
        self.assertLess(int(page.locator("#soldierCount").inner_text().strip()), 60)
        self.assertEqual([], errors, "Enemy projectile combat raised a browser error")
        page.close()

    def test_lane_transition_blends_fire_between_adjacent_lanes(self) -> None:
        page = self.browser.new_page(viewport={"width": 1280, "height": 900})
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(
            self.base_url + "?testMode=1&testLaneTransition=1",
            wait_until="networkidle",
        )
        page.get_by_role("button", name="START RUN").click()
        canvas = page.locator("#gameCanvas")
        page.wait_for_function(
            "() => document.querySelector('#gameCanvas').dataset.fireLaneWeights === '1.000,0.000,0.000'",
            timeout=2000,
        )
        bounds = canvas.bounding_box()
        assert bounds is not None
        drag_y = bounds["y"] + bounds["height"] * 0.78
        lane_one_x = self.lane_screen_x(page, 1 / 6)
        midpoint_x = self.lane_screen_x(page, 1 / 3)
        lane_two_x = self.lane_screen_x(page, 1 / 2)
        page.mouse.move(lane_one_x, drag_y)
        page.mouse.down()
        page.mouse.move(midpoint_x, drag_y, steps=10)
        page.wait_for_function(
            """() => {
                const w = document.querySelector('#gameCanvas').dataset.fireLaneWeights.split(',').map(Number);
                return w[0] > 0.2 && w[0] < 0.8 && w[1] > 0.2 && w[1] < 0.8 && w[2] < 0.01;
            }""",
            timeout=3000,
        )
        weights = [float(value) for value in (canvas.get_attribute("data-fire-lane-weights") or "").split(",")]
        self.assertAlmostEqual(1.0, sum(weights), delta=0.01)
        self.assertGreater(weights[0], 0.2, "Fire should still be directed into lane 1 during the transition")
        self.assertGreater(weights[1], 0.2, "Fire should already be shifting into lane 2 during the transition")
        self.assertLess(weights[2], 0.01, "A lane 1-to-2 transition should not jump to lane 3")
        page.mouse.move(lane_two_x, drag_y, steps=10)
        page.wait_for_function(
            """() => {
                const w = document.querySelector('#gameCanvas').dataset.fireLaneWeights.split(',').map(Number);
                return w[0] < 0.01 && w[1] > 0.98 && w[2] < 0.01;
            }""",
            timeout=3000,
        )
        self.assertGreater(int(canvas.get_attribute("data-fired-shots-lane1") or "0"), 0)
        self.assertGreater(int(canvas.get_attribute("data-fired-shots-lane2") or "0"), 0)
        page.mouse.up()
        self.assertEqual([], errors, "Continuous lane steering raised a browser error")
        page.close()

    def test_clicking_enemy_locks_all_fire_on_that_specific_target(self) -> None:
        page = self.browser.new_page(viewport={"width": 1280, "height": 900})
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(self.base_url + "?testMode=1&testDirectTarget=1", wait_until="networkidle")
        page.get_by_role("button", name="START RUN").click()
        canvas = page.locator("#gameCanvas")
        bounds = canvas.bounding_box()
        assert bounds is not None
        world_width = canvas.evaluate("(node) => node.width")
        road_width = world_width * (220 + 660 * ((160 - 66) / (560 - 66))) / 960
        road_left = (world_width - road_width) / 2
        target_world_x = road_left + road_width / 6
        screen_x = bounds["x"] + bounds["width"] * target_world_x / world_width
        screen_y = bounds["y"] + bounds["height"] * 160 / 560
        page.mouse.click(screen_x, screen_y)
        self.assertEqual("31", canvas.get_attribute("data-last-target-click"), "The click must resolve to the left enemy's hitbox")
        page.wait_for_function(
            "() => document.querySelector('#gameCanvas').dataset.selectedTargetId === '31'",
            timeout=2000,
        )
        self.assertEqual("31", canvas.get_attribute("data-selected-target-id"))
        self.assertEqual("enemy", canvas.get_attribute("data-selected-target-type"))
        self.assertEqual("locked", canvas.get_attribute("data-combat-lane-aligned"))
        page.wait_for_function(
            "() => Number(document.querySelector('#gameCanvas').dataset.selectedTargetHits || 0) >= 3",
            timeout=4000,
        )
        self.assertGreater(int(canvas.get_attribute("data-selected-target-hits") or "0"), 0)
        self.assertEqual([], errors, "Direct target selection raised a browser error")
        page.close()

    def test_500_barrel_hits_unlock_temporary_tank_firepower(self) -> None:
        page = self.browser.new_page(viewport={"width": 1280, "height": 900})
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(self.base_url + "?testMode=1&testTankBarrel=1", wait_until="networkidle")
        page.get_by_role("button", name="START RUN").click()
        canvas = page.locator("#gameCanvas")
        self.assertEqual("500", canvas.get_attribute("data-tank-barrel-hits-required"))
        page.wait_for_function(
            "() => document.querySelector('#gameCanvas').dataset.tankMode === 'true'",
            timeout=8000,
        )
        self.assertEqual("500", canvas.get_attribute("data-tank-barrel-hits"))
        self.assertGreater(float(canvas.get_attribute("data-tank-time-remaining") or "0"), 8)
        self.assertEqual("4", canvas.get_attribute("data-tank-damage"))
        self.assertEqual([], errors, "Tank unlock raised a browser error")
        page.close()

    def test_unresolved_enemy_reduces_squad_by_remaining_count_on_contact(self) -> None:
        page = self.browser.new_page(viewport={"width": 1280, "height": 900})
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(
            self.base_url + "?testMode=1&testEnemyBreach=contact",
            wait_until="networkidle",
        )
        page.get_by_role("button", name="START RUN").click()
        canvas = page.locator("#gameCanvas")
        page.wait_for_function(
            "() => document.querySelector('#gameCanvas').dataset.enemyBreachReason === 'contact'",
            timeout=3000,
        )
        self.assertEqual("5", canvas.get_attribute("data-enemy-breach-count"))
        self.assertEqual("7", page.locator("#soldierCount").inner_text().strip())
        self.assertEqual([], errors, "Enemy contact raised a browser error")
        page.close()

    def test_enemy_contact_damage_is_applied_only_once_until_it_exits(self) -> None:
        page = self.browser.new_page(viewport={"width": 1280, "height": 900})
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(
            self.base_url + "?testMode=1&testEnemyBreach=duplicate",
            wait_until="networkidle",
        )
        page.get_by_role("button", name="START RUN").click()
        canvas = page.locator("#gameCanvas")
        page.wait_for_function(
            "() => document.querySelector('#gameCanvas').dataset.enemyBreachReason === 'contact'",
            timeout=3000,
        )
        page.wait_for_function(
            "() => document.querySelector('#gameCanvas').dataset.enemyBreachExits === '1'",
            timeout=6000,
        )
        self.assertEqual("5", canvas.get_attribute("data-enemy-breach-count"))
        self.assertEqual("1", canvas.get_attribute("data-enemy-breach-applications"))
        self.assertEqual("7", page.locator("#soldierCount").inner_text().strip())
        self.assertEqual([], errors, "Enemy contact/exit handling raised a browser error")
        page.close()

    def test_killed_enemy_does_not_damage_the_squad(self) -> None:
        page = self.browser.new_page(viewport={"width": 1280, "height": 900})
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(
            self.base_url + "?testMode=1&testEnemyBreach=killed",
            wait_until="networkidle",
        )
        page.get_by_role("button", name="START RUN").click()
        canvas = page.locator("#gameCanvas")
        page.wait_for_function(
            "() => document.querySelector('#statusPill').textContent.trim() === 'VICTORY'",
            timeout=3000,
        )
        self.assertEqual("12", page.locator("#soldierCount").inner_text().strip())
        self.assertEqual("0", canvas.get_attribute("data-enemy-breach-applications"))
        self.assertEqual("", canvas.get_attribute("data-enemy-breach-reason"))
        self.assertEqual([], errors, "A defeated enemy caused squad losses")
        page.close()

    def test_unresolved_enemy_exiting_map_causes_mission_failure_at_zero_squad(self) -> None:
        page = self.browser.new_page(viewport={"width": 1280, "height": 900})
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(
            self.base_url + "?testMode=1&testEnemyBreach=exit",
            wait_until="networkidle",
        )
        page.get_by_role("button", name="START RUN").click()
        canvas = page.locator("#gameCanvas")
        page.wait_for_function(
            "() => document.querySelector('#gameCanvas').dataset.enemyBreachReason === 'exit'",
            timeout=3000,
        )
        self.assertEqual("20", canvas.get_attribute("data-enemy-breach-count"))
        self.assertEqual("0", page.locator("#soldierCount").inner_text().strip())
        self.assertEqual("DEFEAT", page.locator("#statusPill").inner_text().strip())
        self.assertTrue(page.locator("#endOverlay").is_visible())
        self.assertEqual([], errors, "Enemy escape raised a browser error")
        page.close()

    def test_undestroyed_tank_barrel_moves_offscreen_without_blocking_run(self) -> None:
        page = self.browser.new_page(viewport={"width": 1280, "height": 900})
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(
            self.base_url + "?testMode=1&testBarrelPass=1",
            wait_until="networkidle",
        )
        page.get_by_role("button", name="START RUN").click()
        canvas = page.locator("#gameCanvas")
        page.wait_for_function(
            "() => document.querySelector('#gameCanvas').dataset.barrelPassed === 'true'",
            timeout=5000,
        )
        self.assertEqual("false", canvas.get_attribute("data-tank-mode"))
        self.assertEqual("0.00", canvas.get_attribute("data-tank-time-remaining"))
        self.assertLess(
            int(canvas.get_attribute("data-tank-barrel-hits") or "0"),
            int(canvas.get_attribute("data-tank-barrel-hits-required") or "0"),
        )
        self.assertEqual("VICTORY", page.locator("#statusPill").inner_text().strip())
        self.assertEqual([], errors, "Passing an undestroyed tank barrel raised a browser error")
        page.close()

    def test_boss_is_hit_by_straight_fire_before_engagement(self) -> None:
        page = self.browser.new_page(viewport={"width": 1280, "height": 900})
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(self.base_url + "?testMode=1&testBossEarlyHits=1", wait_until="networkidle")
        page.get_by_role("button", name="START RUN").click()
        canvas = page.locator("#gameCanvas")
        page.wait_for_function(
            "() => Number(document.querySelector('#gameCanvas').dataset.bossHitsBeforeEngagement || 0) > 0"
            " && document.querySelector('#gameCanvas').dataset.bossEngaged === 'true'",
            timeout=5000,
        )
        self.assertGreater(int(canvas.get_attribute("data-boss-hits-before-engagement") or "0"), 0)
        self.assertLess(float(canvas.get_attribute("data-first-boss-hit-y") or "999"), 300)
        self.assertLess(int(canvas.get_attribute("data-boss-hp") or "999"), int(canvas.get_attribute("data-boss-max-hp") or "0"))
        self.assertEqual("true", canvas.get_attribute("data-player-bullets-lane-forward"))
        self.assertEqual([], errors, "Early boss hits raised a browser error")
        page.close()

    def test_shootable_reinforcement_target_only_takes_hits_in_its_lane(self) -> None:
        page = self.browser.new_page(viewport={"width": 1280, "height": 900})
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(self.base_url + "?testMode=1&testLaneSpecificTarget=target", wait_until="networkidle")
        page.get_by_role("button", name="START RUN").click()
        canvas = page.locator("#gameCanvas")
        page.wait_for_timeout(600)
        self.assertEqual("0", canvas.get_attribute("data-shoot-target-hits"))
        self.assertEqual("0.5", canvas.get_attribute("data-shoot-target-lane"))
        self.assertLessEqual(float(canvas.get_attribute("data-shoot-target-width-ratio") or "1"), 1 / 3)
        self.assertEqual("true", canvas.get_attribute("data-player-bullets-lane-forward"))
        self.steer_to_lane(page, 0.5)
        page.wait_for_function("() => Number(document.querySelector('#gameCanvas').dataset.shootTargetHits || 0) > 0", timeout=2500)
        self.assertGreater(int(canvas.get_attribute("data-shoot-target-hits") or "0"), 0)
        self.assertEqual([], errors, "Lane-specific shootable target raised a browser error")
        page.close()

    def test_tank_barrel_only_takes_hits_in_its_lane(self) -> None:
        page = self.browser.new_page(viewport={"width": 1280, "height": 900})
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(self.base_url + "?testMode=1&testLaneSpecificTarget=barrel", wait_until="networkidle")
        page.get_by_role("button", name="START RUN").click()
        canvas = page.locator("#gameCanvas")
        page.wait_for_timeout(500)
        self.assertEqual("0", canvas.get_attribute("data-tank-barrel-hits"))
        self.assertEqual("true", canvas.get_attribute("data-player-bullets-lane-forward"))
        self.steer_to_lane(page, 0.5)
        page.wait_for_function("() => Number(document.querySelector('#gameCanvas').dataset.tankBarrelHits || 0) >= 5", timeout=2500)
        self.assertEqual("5", canvas.get_attribute("data-tank-barrel-hits"))
        self.assertEqual([], errors, "Lane-specific tank barrel raised a browser error")
        page.close()

    def test_landscape_mode_control_can_be_enabled_and_disabled(self) -> None:
        page = self.browser.new_page(viewport={"width": 1280, "height": 720})
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(self.base_url + "?testMode=1", wait_until="networkidle")
        button = page.get_by_role("button", name="Enable landscape play mode")
        self.assertEqual("false", button.get_attribute("aria-pressed"))
        button.click()
        page.wait_for_function(
            "() => document.documentElement.classList.contains('landscape-mode')"
            " && document.querySelector('#orientationButton').getAttribute('aria-pressed') === 'true'",
            timeout=2000,
        )
        self.assertEqual("LANDSCAPE ON", page.locator("#orientationButton").inner_text().strip())
        page.get_by_role("button", name="Disable landscape play mode").click()
        self.assertEqual("false", page.locator("#orientationButton").get_attribute("aria-pressed"))
        self.assertFalse(page.locator("html").evaluate("(node) => node.classList.contains('landscape-mode')"))
        self.assertEqual([], errors, "Landscape mode toggle raised a browser error")
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
            const squadCenter = Number(canvas.dataset.squadCenterX || canvas.width / 2);
            const squadLeft = Math.max(0, Math.floor(squadCenter - 70));
            const squadRight = Math.min(width, Math.ceil(squadCenter + 70));
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
            let allyFacePixels = 0;
            for (let y = 372; y < 389; y++) {
                for (let x = squadLeft; x < squadRight; x++) {
                    const i = (y * width + x) * 4;
                    const [r, g, b] = data.slice(i, i + 3);
                    if (r > 165 && r - g > 18 && g > b * 1.18 && g < 195 && b > 65) allyFacePixels++;
                }
            }
            let paleUniformPixels = 0;
            for (let y = 392; y < 445; y++) {
                for (let x = squadLeft; x < squadRight; x++) {
                    const i = (y * width + x) * 4;
                    const [r, g, b] = data.slice(i, i + 3);
                    if (r > 220 && g > 200 && b > 165 && r >= g && g >= b) paleUniformPixels++;
                }
            }
            const sideIndex = (300 * width + 30) * 4;
            const sideBackground = Array.from(data.slice(sideIndex, sideIndex + 3));
            return {blueSquad, redEnemy, allyFacePixels, paleUniformPixels, sideBackground};
        }""")
        self.assertGreater(pixels["blueSquad"], 250, "Blue squad helmet/gear palette was not visible")
        self.assertGreater(pixels["redEnemy"], 100, "Red enemy helmet/gear palette was not visible")
        self.assertLess(pixels["allyFacePixels"], 35, "Allied formation should show rear-facing helmets, not frontal faces")
        self.assertGreater(pixels["paleUniformPixels"], 50, "The allied pale shirt should remain visible beside compact blue gear")
        self.assertGreater(pixels["sideBackground"][2], pixels["sideBackground"][1] * 1.15, "The outside field should be blue, not green terrain")
        self.assertEqual([], errors, "Browser JavaScript errors were reported")
        page.close()

    def test_squad_fires_continuously_and_hits_reduce_enemy_count(self) -> None:
        page = self.browser.new_page(viewport={"width": 1280, "height": 900})
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(self.base_url + "?testMode=1&testSquadFire=1", wait_until="networkidle")
        page.get_by_role("button", name="START RUN").click()
        self.steer_to_lane(page, 0.76)

        # Fire must continue even before a target enters the combat line.
        page.wait_for_function(
            "() => Number(document.querySelector('#gameCanvas').dataset.projectiles || 0) > 0",
            timeout=3000,
        )
        page.wait_for_function(
            "() => document.querySelector('#gameCanvas').dataset.enemyWaveInitialCount === '18'",
            timeout=7000,
        )
        # An immediate contact hit may reduce the HUD count before it ever displays 18.
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

    def test_unguided_projectiles_stay_inside_perspective_road_with_large_squad(self) -> None:
        page = self.browser.new_page(viewport={"width": 1280, "height": 900})
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(
            self.base_url + "?testMode=1&testProjectileRoadBounds=1",
            wait_until="networkidle",
        )
        page.get_by_role("button", name="START RUN").click()
        canvas = page.locator("#gameCanvas")
        page.wait_for_function(
            "() => Number(document.querySelector('#gameCanvas').dataset.roadChecks || 0) > 150",
            timeout=5000,
        )
        self.assertEqual("1000000000", page.locator("#soldierCount").inner_text().strip())
        self.assertGreater(
            int(canvas.get_attribute("data-road-checks") or "0"),
            150,
            "The test should inspect many projectile positions over the narrowing road",
        )
        self.assertEqual(
            "0",
            canvas.get_attribute("data-road-violations"),
            "Unguided projectiles must stay inside the road as its perspective width narrows",
        )
        self.assertGreater(int(canvas.get_attribute("data-projectiles") or "0"), 0)
        self.assertEqual([], errors, "Browser JavaScript errors were reported")
        page.close()

    def test_straight_projectiles_stay_inside_road_with_large_squad_at_edge(self) -> None:
        page = self.browser.new_page(viewport={"width": 1280, "height": 900})
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(
            self.base_url + "?testMode=1&testStraightProjectileRoadBounds=1",
            wait_until="networkidle",
        )
        page.get_by_role("button", name="START RUN").click()
        canvas = page.locator("#gameCanvas")
        page.wait_for_function(
            "() => Number(document.querySelector('#gameCanvas').dataset.straightProjectiles || 0) > 0"
            " && Number(document.querySelector('#gameCanvas').dataset.roadChecks || 0) > 150",
            timeout=5000,
        )
        self.assertEqual(
            "0",
            canvas.get_attribute("data-road-violations"),
            "Straight lane-forward projectiles from a wide squad must remain inside the road",
        )
        self.assertEqual("true", canvas.get_attribute("data-player-bullets-lane-forward"))
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
            "() => document.querySelector('#progressCount').textContent.trim() === '1 / 13'",
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
        page.goto(self.base_url + "?testMode=1&testFullRound=1", wait_until="networkidle")
        page.get_by_role("button", name="START RUN").click()

        canvas = page.locator("#gameCanvas")
        bounds = canvas.bounding_box()
        assert bounds is not None
        drag_y = bounds["y"] + bounds["height"] * 0.78
        left_x = self.lane_screen_x(page, 0.26)
        right_x = self.lane_screen_x(page, 0.76)

        # A deliberately winning route; the sixth arithmetic slot is now a shot-upgraded +1 target.
        # Start on the left +8 gate, then use the stronger multipliers and align for each enemy wave.
        page.mouse.move(left_x, drag_y)
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
        enemy_lanes = {4: 5 / 6, 7: 1 / 6, 9: 1 / 2}
        for completed_event in range(1, 14):
            if completed_event in enemy_lanes:
                self.steer_to_lane(page, enemy_lanes[completed_event], keep_dragging=True)
            page.wait_for_function(
                f"() => document.querySelector('#progressCount').textContent.trim() === '{completed_event} / 13'",
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

        self.steer_to_lane(page, 0.5, keep_dragging=True)
        page.mouse.up()
        page.wait_for_function(
            "() => document.querySelector('#statusPill').textContent.trim() === 'VICTORY'",
            timeout=8000,
        )
        self.assertTrue(page.locator("#endOverlay").is_visible())
        self.assertEqual("OPERATION COMPLETE", page.locator("#endKicker").inner_text().strip())
        self.assertEqual("13 / 13", page.locator("#progressCount").inner_text().strip())
        self.assertGreater(int(page.locator("#endSoldierCount").inner_text().strip()), 0)
        self.assertEqual([], errors, "Browser JavaScript errors were reported")
        page.get_by_role("button", name="RUN IT AGAIN").click()
        self.assertEqual("IN RUN", page.locator("#statusPill").inner_text().strip())
        self.assertEqual("12", page.locator("#soldierCount").inner_text().strip())
        page.close()


    def test_enemy_wave_scales_with_large_squad(self) -> None:
        page = self.browser.new_page(viewport={"width": 1280, "height": 900})
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(
            self.base_url + "?testMode=1&testCombatScaling=enemy",
            wait_until="networkidle",
        )
        page.get_by_role("button", name="START RUN").click()
        page.wait_for_function(
            "() => document.querySelector('#gameCanvas').dataset.enemyWaveInitialCount === '210'",
            timeout=3000,
        )
        self.assertEqual("1000", page.locator("#soldierCount").inner_text().strip())
        self.assertEqual("210", page.locator("#gameCanvas").get_attribute("data-enemy-wave-initial-count"))
        self.assertEqual([], errors, "Enemy scaling raised a browser error")
        page.close()

    def test_commander_health_scales_with_large_squad(self) -> None:
        page = self.browser.new_page(viewport={"width": 1280, "height": 900})
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(
            self.base_url + "?testMode=1&testCombatScaling=boss",
            wait_until="networkidle",
        )
        page.get_by_role("button", name="START RUN").click()
        page.wait_for_function(
            "() => Number(document.querySelector('#gameCanvas').dataset.bossMaxHp || 0) === 440",
            timeout=3000,
        )
        self.assertEqual("400", page.locator("#soldierCount").inner_text().strip())
        self.assertEqual("440", page.locator("#gameCanvas").get_attribute("data-boss-max-hp"))
        self.assertEqual([], errors, "Commander scaling raised a browser error")
        page.close()


    def test_combat_requires_matching_lane_and_recovers_after_steering(self) -> None:
        matched = self.browser.new_page(viewport={"width": 1280, "height": 900})
        matched_errors: list[str] = []
        matched.on("pageerror", lambda error: matched_errors.append(str(error)))
        matched.goto(
            self.base_url + "?testMode=1&testLaneCombat=matched",
            wait_until="networkidle",
        )
        matched.get_by_role("button", name="START RUN").click()
        matched.wait_for_function(
            "() => Number(document.querySelector('#gameCanvas').dataset.enemyHits || 0) > 0",
            timeout=3000,
        )
        self.assertEqual("true", matched.locator("#gameCanvas").get_attribute("data-combat-lane-aligned"))
        self.assertEqual([], matched_errors, "Matched-lane combat raised a browser error")
        matched.close()

        mismatched = self.browser.new_page(viewport={"width": 1280, "height": 900})
        mismatched_errors: list[str] = []
        mismatched.on("pageerror", lambda error: mismatched_errors.append(str(error)))
        mismatched.goto(
            self.base_url + "?testMode=1&testLaneCombat=mismatched",
            wait_until="networkidle",
        )
        mismatched.get_by_role("button", name="START RUN").click()
        mismatched.wait_for_function(
            "() => document.querySelector('#gameCanvas').dataset.combatLaneAligned === 'false'",
            timeout=2000,
        )
        mismatched.wait_for_function(
            "() => Number(document.querySelector('#gameCanvas').dataset.enemyHits || 0) > 0",
            timeout=3000,
        )
        opening_hits = int(mismatched.locator("#gameCanvas").get_attribute("data-enemy-hits") or "0")
        self.assertGreater(opening_hits, 0, "The first contact volley should be a fixed straight shot even before steering")
        self.steer_to_lane(mismatched, 0.76)
        mismatched.wait_for_function(
            "() => document.querySelector('#gameCanvas').dataset.combatLaneAligned === 'true'",
            timeout=3000,
        )
        self.assertEqual([], mismatched_errors, "Steering into the enemy lane raised a browser error")
        mismatched.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
