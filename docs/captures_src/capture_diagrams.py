# -*- coding: utf-8 -*-
"""다이어그램 HTML(정적 SVG) → 고해상도 PNG 캡처.

실행: python capture_diagrams.py
산출: docs/captures/usecase.png, architecture.png (scale 2 → 3000px+ 폭)
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SRC = Path(r"D:\JB_Fin_AI\JB_AI Challenge\majung\docs\captures_src")
OUT = Path(r"D:\JB_Fin_AI\JB_AI Challenge\majung\docs\captures")

TARGETS = [
    ("usecase.html", "usecase.png", 1600, 1160),
    ("architecture.html", "architecture.png", 1660, 812),
    ("flow.html", "flow.png", 1560, 990),
]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = None
        for ch in ("msedge", "chrome"):
            try:
                browser = p.chromium.launch(channel=ch, headless=True)
                print("[launch]", ch, flush=True)
                break
            except Exception as e:  # noqa: BLE001
                print("[launch-fail]", ch, repr(e)[:120], flush=True)
        if browser is None:
            sys.exit("no system browser channel available")

        for html, png, w, h in TARGETS:
            ctx = browser.new_context(
                viewport={"width": w + 20, "height": h + 20},
                device_scale_factor=1,
            )
            page = ctx.new_page()
            page.goto((SRC / html).as_uri())
            page.wait_for_timeout(500)  # 폰트 로드
            page.locator("svg").screenshot(path=str(OUT / png))
            print("[saved]", png, flush=True)
            ctx.close()
        browser.close()
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
