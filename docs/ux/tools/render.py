"""Render every wireframe section to PNG (vi + en) and fail on untranslated labels.

Usage: python3 docs/ux/tools/render.py [wave1|wave2 ...]
Requires: pip install playwright && playwright install chromium (or a local Chrome).
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PAGES = sys.argv[1:] or ["wave1", "wave2"]
LANGS = ["vi", "en"]


def main() -> int:
    problems = []
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="chrome")
        except Exception:
            browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1600, "height": 1000}, device_scale_factor=1)
        for name in PAGES:
            html = ROOT / "wireframes" / f"{name}.html"
            for lang in LANGS:
                page.goto(f"{html.as_uri()}?lang={lang}")
                page.wait_for_load_state("load")
                page.add_style_tag(content=".doc-header{display:none!important}")
                leftovers = page.evaluate(
                    "() => [...document.querySelectorAll('body *')]"
                    ".filter(e => e.childElementCount === 0 && e.textContent.includes('\u00a6'))"
                    ".map(e => e.textContent.trim()).slice(0, 20)"
                )
                for text in leftovers:
                    problems.append(f"{name}/{lang}: untranslated label -> {text}")
                out = ROOT / "png" / lang
                out.mkdir(parents=True, exist_ok=True)
                for section in page.query_selector_all("section.screen"):
                    sid = section.get_attribute("id")
                    section.screenshot(path=str(out / f"{name}-{sid}.png"))
                    print(f"wrote png/{lang}/{name}-{sid}.png")
        browser.close()
    for line in problems:
        print(line, file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
