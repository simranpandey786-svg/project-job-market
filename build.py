#!/usr/bin/env python3
"""Assemble the static dashboard after analysis data has been generated."""
from pathlib import Path
import shutil

ROOT = Path(__file__).parent
WEB = ROOT / "web"
DIST = ROOT / "dist"

DIST.mkdir(exist_ok=True)
(DIST / "assets").mkdir(exist_ok=True)
shutil.copy2(WEB / "index.html", DIST / "index.html")
shutil.copy2(WEB / "styles.css", DIST / "assets" / "styles.css")
shutil.copy2(WEB / "app.js", DIST / "assets" / "app.js")

chart_candidates = [
    ROOT / "node_modules" / "chart.js" / "dist" / "chart.umd.js",
    ROOT / "node_modules" / "chart.js" / "dist" / "chart.umd.min.js",
]
chart = next((p for p in chart_candidates if p.exists()), None)
if not chart:
    raise SystemExit("Chart.js is missing. Run: npm install")
shutil.copy2(chart, DIST / "assets" / "chart.umd.js")
print(f"Built {DIST}")
