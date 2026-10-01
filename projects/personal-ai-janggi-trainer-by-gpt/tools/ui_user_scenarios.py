#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright, expect


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
PORT = int(os.environ.get("UI_TEST_PORT", "8765"))
BASE = f"http://127.0.0.1:{PORT}"


def wait_health(timeout=20):
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"{BASE}/api/health", timeout=2) as response:
                if response.status == 200:
                    return
        except Exception as exc:
            last = exc
        time.sleep(0.25)
    raise RuntimeError(f"server did not become healthy: {last}")


def state(page):
    return page.evaluate("""async () => {
      const r = await fetch('/api/state', {cache:'no-store'});
      return await r.json();
    }""")


def geometry(page):
    return page.evaluate("""() => {
      const rect = el => {
        const r = document.querySelector(el)?.getBoundingClientRect();
        if (!r) return null;
        return {
          x:r.x, y:r.y, width:r.width, height:r.height,
          right:r.right, bottom:r.bottom
        };
      };
      const viewport = {width:innerWidth, height:innerHeight};
      const board = rect('#board');
      const topbar = rect('.topbar');
      const players = rect('.players');
      const status = rect('.status-bar');
      const controls = rect('.game-controls');
      const left = rect('.rail-left');
      const right = rect('.rail-right');
      return {
        viewport, board, topbar, players, status, controls, left, right,
        htmlWidth:document.documentElement.scrollWidth,
        bodyWidth:document.body.scrollWidth,
        htmlHeight:document.documentElement.scrollHeight,
        bodyHeight:document.body.scrollHeight
      };
    }""")


def assert_no_viewport_overflow(page, label):
    g = geometry(page)
    vp = g["viewport"]
    assert g["htmlWidth"] <= vp["width"] + 1, (label, g)
    assert g["bodyWidth"] <= vp["width"] + 1, (label, g)
    assert g["htmlHeight"] <= vp["height"] + 1, (label, g)
    assert g["bodyHeight"] <= vp["height"] + 1, (label, g)
    board = g["board"]
    assert board, (label, "board missing")
    ratio = board["width"] / board["height"]
    assert abs(ratio - (8 / 9)) < 0.025, (label, "board ratio", ratio, g)
    assert board["x"] >= -1 and board["right"] <= vp["width"] + 1, (label, "board horizontal", g)
    assert board["y"] >= -1 and board["bottom"] <= vp["height"] + 1, (label, "board vertical", g)
    return g


def click_first_player_piece_and_move(page):
    pieces = page.locator('button.cell[aria-label^="초 "]')
    count = pieces.count()
    assert count > 0, "no Cho pieces found"
    pieces.first.click()
    expect(page.locator(".cell.legal").first).to_be_visible(timeout=3000)
    page.locator(".cell.legal").first.click()


def wait_player_turn(page, timeout=15000):
    page.wait_for_function(
        """() => {
          const s = document.querySelector('#status-context')?.textContent || '';
          return s.includes('내 차례') || s.includes('대국 종료');
        }""",
        timeout=timeout,
    )


def main():
    screenshots = Path(os.environ.get("UI_TEST_ARTIFACT_DIR", str(ROOT / "ui-test-artifacts")))
    screenshots.mkdir(parents=True, exist_ok=True)

    server = subprocess.Popen(
        [sys.executable, str(APP)],
        cwd=ROOT,
        env={**os.environ, "PORT": str(PORT)},
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        wait_health()

        with sync_playwright() as p:
            browser = p.chromium.launch()
            try:
                # Scenario 1: first launch -> initial state and desktop geometry.
                context = browser.new_context(viewport={"width": 1440, "height": 900})
                page = context.new_page()
                page.goto(BASE, wait_until="networkidle")
                s = state(page)
                assert s["player_side"] == "cho"
                assert s["ai_level"] == "1"
                g = assert_no_viewport_overflow(page, "initial desktop")
                page.screenshot(path=screenshots / "01-initial-desktop.png", full_page=False)

                # Scenario 2: settings -> choose Han + Lv.6 -> reset -> verify first AI move.
                page.click("#settings-toggle")
                page.select_option("#player-side", "han")
                page.select_option("#ai-level", "6")
                page.click("#reset")
                page.wait_for_timeout(300)
                s = state(page)
                assert s["player_side"] == "han"
                assert s["ai_side"] == "cho"
                assert s["ai_level"] == "6"
                assert len(s["state"]["history"]) >= 1
                assert s["state"]["turn"] == "han"
                assert "한" in page.locator("#player-name").text_content()
                page.screenshot(path=screenshots / "02-han-lv6.png", full_page=False)
                assert_no_viewport_overflow(page, "Han Lv6 desktop")

                # Scenario 3: start another game mid-game; settings must apply and board must reset.
                # Choose Cho/Lv.2 and reset while a previous game exists.
                page.click("#settings-toggle")
                page.select_option("#player-side", "cho")
                page.select_option("#ai-level", "2")
                page.click("#reset")
                page.wait_for_timeout(250)
                s = state(page)
                assert s["player_side"] == "cho" and s["ai_level"] == "2"
                assert len(s["state"]["history"]) == 0
                assert s["state"]["turn"] == "cho"
                assert not page.locator("#settings-toggle").get_attribute("aria-expanded") == "true"

                # Scenario 4: human move rendering before AI computation.
                # Slow only /api/move to force the pending-player-move render to be observable.
                page.route("**/api/move", lambda route: (time.sleep(0.8), route.continue_())[1])
                click_first_player_piece_and_move(page)
                page.wait_for_timeout(120)
                pending_status = page.locator("#status").text_content() or ""
                assert "내 수를 먼저 반영했습니다" in pending_status, pending_status
                page.screenshot(path=screenshots / "03-pending-human-move.png", full_page=False)
                page.unroute("**/api/move")
                def delayed_move(route):
                    import time as _time
                    request = route.request
                    import urllib.request as _urllib
                    # Forward the request manually and delay the response.
                    req = _urllib.Request(
                        BASE + "/api/move",
                        data=request.post_data.encode() if request.post_data else b"{}",
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    )
                    with _urllib.urlopen(req, timeout=15) as upstream:
                        body = upstream.read()
                        status = upstream.status
                        headers = dict(upstream.headers.items())
                    _time.sleep(0.8)
                    route.fulfill(status=status, headers=headers, body=body)
                page.route("**/api/move", delayed_move)
                click_first_player_piece_and_move(page)
                page.wait_for_timeout(120)
                pending_status = page.locator("#status").text_content() or ""
                assert "내 수를 먼저 반영했습니다" in pending_status, pending_status
                page.screenshot(path=screenshots / "03-pending-human-move.png", full_page=False)
                page.unroute("**/api/move")
                wait_player_turn(page)
                s = state(page)
                assert len(s["state"]["history"]) >= 2
                assert s["state"]["turn"] == "cho"

                # Scenario 5: undo returns to player's pre-move turn.
                page.click("#undo")
                page.wait_for_timeout(250)
                s = state(page)
                assert s["state"]["turn"] == s["player_side"] == "cho"
                assert len(s["state"]["history"]) == 0
                assert page.locator("#undo").is_disabled()

                # Scenario 6: review -> training; verify the learning rail does not silently overflow.
                # Create one move again.
                click_first_player_piece_and_move(page)
                wait_player_turn(page)
                page.click("#learning-toggle")
                page.wait_for_timeout(100)
                assert page.locator("#learning-toggle").get_attribute("aria-expanded") == "true"
                page.screenshot(path=screenshots / "04-learning-open.png", full_page=False)
                assert_no_viewport_overflow(page, "learning desktop")

                # Review then training; both panels becoming visible would be a likely clipping risk.
                page.click("#review")
                expect(page.locator("#review-panel")).to_be_visible()
                page.click("#training")
                expect(page.locator("#training-panel")).to_be_visible()
                g = geometry(page)
                right = g["right"]
                if right:
                    visible_panels = page.locator(".rail-right > section:not([hidden])").count()
                    assert visible_panels <= 1, (
                        "learning rail exposes multiple stacked panels; likely clipping",
                        visible_panels,
                        right,
                    )

                # Scenario 7: independent browser sessions do not share game state.
                c2 = browser.new_context(viewport={"width": 1280, "height": 800})
                p2 = c2.new_page()
                p2.goto(BASE, wait_until="networkidle")
                assert len(state(p2)["state"]["history"]) == 0
                c2.close()

                context.close()

                # Scenario 8: responsive checks at common desktop/mobile viewports.
                for idx, vp in enumerate([
                    (1280, 720), (1024, 768), (821, 700),
                    (820, 1180), (390, 844), (360, 800), (320, 568),
                ], start=1):
                    ctx = browser.new_context(viewport={"width": vp[0], "height": vp[1]})
                    pg = ctx.new_page()
                    pg.goto(BASE, wait_until="networkidle")
                    assert_no_viewport_overflow(pg, f"responsive {vp[0]}x{vp[1]} initial")
                    pg.click("#settings-toggle")
                    pg.wait_for_timeout(100)
                    assert_no_viewport_overflow(pg, f"responsive {vp[0]}x{vp[1]} settings")
                    pg.click("#settings-toggle")
                    pg.click("#learning-toggle")
                    pg.wait_for_timeout(100)
                    assert_no_viewport_overflow(pg, f"responsive {vp[0]}x{vp[1]} learning")
                    pg.screenshot(path=screenshots / f"05-responsive-{idx}-{vp[0]}x{vp[1]}.png", full_page=False)
                    ctx.close()

            finally:
                browser.close()
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    main()
