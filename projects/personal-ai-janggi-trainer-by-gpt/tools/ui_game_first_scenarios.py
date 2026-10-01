#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
PORT = int(os.environ.get("UI_TEST_PORT", "8766"))
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
        return {x:r.x,y:r.y,width:r.width,height:r.height,right:r.right,bottom:r.bottom};
      };
      return {
        viewport:{width:innerWidth,height:innerHeight},
        setup:rect('#setup-screen'),
        setupCard:rect('#setup-screen .setup-card'),
        game:rect('#game-screen'),
        board:rect('#board'),
        footer:rect('.game-footer'),
        htmlWidth:document.documentElement.scrollWidth,
        htmlHeight:document.documentElement.scrollHeight,
        bodyWidth:document.body.scrollWidth,
        bodyHeight:document.body.scrollHeight
      };
    }""")


def assert_clean_viewport(page, label):
    g = geometry(page)
    vp = g["viewport"]
    assert g["htmlWidth"] <= vp["width"] + 1, (label, g)
    assert g["bodyWidth"] <= vp["width"] + 1, (label, g)
    assert g["htmlHeight"] <= vp["height"] + 1, (label, g)
    assert g["bodyHeight"] <= vp["height"] + 1, (label, g)
    board = g["board"]
    if board:
        ratio = board["width"] / board["height"]
        assert abs(ratio - 8/9) < 0.025, (label, "board ratio", ratio, g)
        assert board["x"] >= -1 and board["right"] <= vp["width"] + 1, (label, g)
        assert board["y"] >= -1 and board["bottom"] <= vp["height"] + 1, (label, g)


def wait_idle(page, timeout=20000):
    page.wait_for_function(
        "() => !document.querySelector('#player-side')?.disabled && !document.querySelector('#ai-level')?.disabled",
        timeout=timeout,
    )


def move_one_piece(page, side_label):
    pieces = page.locator(f'button.cell[aria-label^="{side_label} "]')
    assert pieces.count() > 0, f"no {side_label} pieces"
    pieces.first.click()
    expect(page.locator(".cell.legal").first).to_be_visible(timeout=4000)
    page.locator(".cell.legal").first.click()


def main():
    artifact_dir = Path(os.environ.get("UI_TEST_ARTIFACT_DIR", str(ROOT / "ui-test-artifacts")))
    artifact_dir.mkdir(parents=True, exist_ok=True)

    server = subprocess.Popen(
        [sys.executable, str(ROOT / "app.py")],
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
                # Scenario 1: first screen must be setup-only; board must not be shown.
                ctx = browser.new_context(viewport={"width": 1440, "height": 900})
                page = ctx.new_page()
                page_errors = []
                page.on("pageerror", lambda e: page_errors.append(str(e)))
                page.goto(BASE, wait_until="networkidle")
                expect(page.locator("#setup-screen")).to_be_visible()
                expect(page.locator("#game-screen")).to_be_hidden()
                assert page.locator("#board").bounding_box() is None
                assert not page_errors, page_errors
                assert_clean_viewport(page, "initial desktop")
                page.screenshot(path=artifact_dir / "01-setup-desktop.png", full_page=False)

                # Scenario 2: choose Lv.6 + Han, start, and verify game screen transition.
                page.click('[data-level="6"]')
                page.click('[data-side="han"]')
                page.click("#reset")
                wait_idle(page)
                expect(page.locator("#setup-screen")).to_be_hidden()
                expect(page.locator("#game-screen")).to_be_visible()
                s = state(page)
                assert s["ai_level"] == "6"
                assert s["player_side"] == "han"
                assert "한" in page.locator("#player-name").text_content()
                page.screenshot(path=artifact_dir / "02-han-lv6-game.png", full_page=False)
                assert_clean_viewport(page, "Han Lv6 game")

                # Scenario 3: replay opens a modal setup, does not navigate or clip the underlying game.
                page.click("#replay-button")
                expect(page.locator("#setup-screen")).to_be_visible()
                assert "modal" in (page.locator("#setup-screen").get_attribute("class") or "")
                assert page.locator("#game-screen").is_visible()
                assert_clean_viewport(page, "replay modal desktop")
                page.screenshot(path=artifact_dir / "03-replay-modal.png", full_page=False)

                # Scenario 4: cancel keeps current game; reopening and starting switches settings.
                page.click("#setup-cancel")
                expect(page.locator("#setup-screen")).to_be_hidden()
                page.click("#replay-button")
                page.click('[data-level="2"]')
                page.click('[data-side="cho"]')
                page.click("#reset")
                wait_idle(page)
                s = state(page)
                assert s["ai_level"] == "2"
                assert s["player_side"] == "cho"
                assert len(s["state"]["history"]) == 0
                expect(page.locator("#game-screen")).to_be_visible()
                page.screenshot(path=artifact_dir / "04-cho-lv2-game.png", full_page=False)

                # Scenario 5: human move renders immediately and a compact evaluation comment appears.
                page.evaluate("""() => {
                  window.__origFetch = window.fetch;
                  const originalFetch = window.fetch;
                  window.fetch = async (...args) => {
                    const url = typeof args[0] === 'string' ? args[0] : args[0]?.url || '';
                    if (url.endsWith('/api/analyze/move') || url.endsWith('/api/move')) {
                      await new Promise(resolve => setTimeout(resolve, 450));
                    }
                    return originalFetch(...args);
                  };
                }""")
                move_one_piece(page, "초")
                page.wait_for_timeout(120)
                assert "착수 평가 중" in (page.locator("#status").text_content() or ""), page.locator("#status").text_content()
                page.screenshot(path=artifact_dir / "05-move-evaluation-pending.png", full_page=False)
                page.evaluate("() => { window.fetch = window.__origFetch; }")
                wait_idle(page)
                assert page.locator("#status").text_content()
                page.screenshot(path=artifact_dir / "06-after-ai-response.png", full_page=False)

                # Scenario 6: narrow responsive setup and game states remain single-screen.
                for idx, vp in enumerate([
                    (1024, 768), (820, 1180), (390, 844), (360, 800), (320, 568)
                ], start=1):
                    c = browser.new_context(viewport={"width": vp[0], "height": vp[1]})
                    pg = c.new_page()
                    errors = []
                    pg.on("pageerror", lambda e: errors.append(str(e)))
                    pg.goto(BASE, wait_until="networkidle")
                    expect(pg.locator("#setup-screen")).to_be_visible()
                    assert_clean_viewport(pg, f"setup {vp[0]}x{vp[1]}")
                    pg.click('[data-level="3"]')
                    pg.click("#reset")
                    wait_idle(pg)
                    expect(pg.locator("#game-screen")).to_be_visible()
                    assert_clean_viewport(pg, f"game {vp[0]}x{vp[1]}")
                    pg.click("#replay-button")
                    assert "modal" in (pg.locator("#setup-screen").get_attribute("class") or "")
                    assert_clean_viewport(pg, f"replay {vp[0]}x{vp[1]}")
                    assert not errors, errors
                    pg.screenshot(path=artifact_dir / f"07-responsive-{idx}-{vp[0]}x{vp[1]}.png", full_page=False)
                    c.close()

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
