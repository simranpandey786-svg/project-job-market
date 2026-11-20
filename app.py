"""Flask API and web server for the dashboard."""
from __future__ import annotations
import json
import re
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory

ROOT = Path(__file__).parent
DIST = ROOT / "dist"
app = Flask(__name__, static_folder=str(DIST), static_url_path="")


def read_json(name):
    return json.loads((DIST / "data" / name).read_text(encoding="utf-8"))


@app.get("/")
def index():
    return send_from_directory(DIST, "index.html")


@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/api/insights")
def insights():
    return jsonify(read_json("insights.json"))


@app.get("/api/recommend")
def recommend():
    jobs = read_json("jobs.json")
    tokens = [x for x in re.split(r"[,\s]+", request.args.get("q", "").lower()) if len(x) > 1]
    category = request.args.get("category", "").lower()
    country = request.args.get("country", "").lower()
    min_rate = request.args.get("min_rate", type=float, default=0)
    limit = min(request.args.get("limit", type=int, default=20), 100)
    scored = []
    for job in jobs:
        title = job["title"].lower()
        score = 20 if not tokens else 55 * sum(t in title for t in tokens) / len(tokens)
        score += 25 if category and job["category"].lower() == category else (12 if not category else 0)
        score += 10 if country and country in job["country"].lower() else (5 if not country else 0)
        low, high = job.get("hourly_low") or 0, job.get("hourly_high") or 0
        midpoint = (low + (high or low)) / 2
        score += 10 if not min_rate or midpoint >= min_rate else -30
        if score > 25:
            scored.append({**job, "match_score": round(min(99, score))})
    scored.sort(key=lambda x: (x["match_score"], x["date"]), reverse=True)
    return jsonify({"count": len(scored[:limit]), "results": scored[:limit]})


@app.get("/<path:path>")
def static_files(path):
    return send_from_directory(DIST, path)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
