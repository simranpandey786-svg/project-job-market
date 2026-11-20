# MarketPulse — Job Market Intelligence

A complete analysis and recommendation prototype built from the supplied Upwork posting dataset. It covers keyword/rate relationships, emerging categories, demand forecasting, country comparisons, monthly refresh, remote-work language, future scenarios, and personalized job matching.

## What is included

- Interactive responsive dashboard in `dist/`
- Reproducible analysis pipeline in `analysis.py`
- Saved demand models in `models/`
- Flask recommendation API in `app.py`
- Statistical write-up in `REPORT.md`
- Docker and Docker Compose deployment
- Unit/API tests in `tests/`

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
npm install
python analysis.py --input "/path/to/all_upwork_jobs.csv"
python build.py
python report.py
python app.py
```

Open `http://localhost:8000`.

## Docker

```bash
docker compose up --build
```

Then open `http://localhost:8000`. The image serves the already generated analysis. Regenerate `dist/data` before rebuilding when a new monthly CSV arrives.

## Tests

```bash
python -m unittest discover -s tests -v
```

## Monthly refresh

Run the analysis, build, report, and container rebuild commands with the newest CSV. The pipeline automatically identifies the continuous high-volume collection window and excludes a final incomplete day from trend modelling. See [API.md](API.md) for integration endpoints and [REPORT.md](REPORT.md) for findings and limitations.
