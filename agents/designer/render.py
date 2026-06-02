"""Render Designer's HTML+Tailwind to PNG via playwright."""
from __future__ import annotations
from pathlib import Path
from uuid import uuid4
from playwright.async_api import async_playwright


HTML_WRAPPER = """<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<script src="https://cdn.tailwindcss.com"></script>
<style>body {{ margin: 0; }}</style>
</head>
<body>
{html}
</body>
</html>"""


async def render_to_png(html: str, out_dir: str = "/app/mockups", width: int = 1280, height: int = 1600) -> str:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    fname = out / f"mockup-{uuid4().hex[:8]}.png"
    full_html = HTML_WRAPPER.format(html=html)
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        ctx = await browser.new_context(viewport={"width": width, "height": height})
        page = await ctx.new_page()
        await page.set_content(full_html, wait_until="networkidle")
        await page.screenshot(path=str(fname), full_page=True)
        await browser.close()
    return str(fname)
