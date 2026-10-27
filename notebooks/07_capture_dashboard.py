"""Capture une image statique du dashboard (pour LinkedIn / README), via Chromium headless."""
from pathlib import Path

from playwright.sync_api import sync_playwright

html_path = Path("reports/dashboard.html").resolve()
out_path = Path("reports/dashboard.png").resolve()

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1800, "height": 1000})
    page.goto(html_path.as_uri())
    page.wait_for_timeout(1200)  # laisser Plotly terminer son rendu JS
    page.screenshot(path=str(out_path))
    browser.close()

print(f"Capture écrite : {out_path}")
