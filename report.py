#!/usr/bin/env python3
"""Generate the concise analytical report from machine-readable insights."""
import json
from pathlib import Path

ROOT = Path(__file__).parent
d = json.loads((ROOT / "dist/data/insights.json").read_text())
m, s = d["metadata"], d["summary"]
emerging = [x for x in d["emerging_categories"] if x["emerging"]][:6]
forecast = [x for x in d["demand_model"]["metrics"] if x["category"] != "Other"][:6]
positive = sorted((x for x in d["keyword_salary"] if x["difference"] > 0), key=lambda x: x["difference"], reverse=True)[:8]
negative = sorted((x for x in d["keyword_salary"] if x["difference"] < 0), key=lambda x: x["difference"])[:6]
countries = d["country_rates"][:10]

def table(headers, rows):
    return "|" + "|".join(headers) + "|\n|" + "|".join("---" for _ in headers) + "|\n" + "\n".join("|"+"|".join(map(str,r))+"|" for r in rows)

text = f"""# Job Market Analysis and Recommendation System

## Executive summary

This analysis uses **{m['valid_rows']:,} Upwork postings** from the continuous collection window **{m['start_date']} to {m['end_date']}**. It excludes {m['excluded_outside_continuous_window']:,} sparse out-of-window or partial-day records to avoid distorting time trends. The cleaned hourly midpoint averages **${s['average_hourly']:.2f}/hour** (median **${s['median_hourly']:.2f}**), while fixed-price jobs have a median budget of **${s['median_fixed_budget']:.0f}**. Hourly and fixed-price compensation are never combined.

## 1. Job-title keywords and offered salaries

Keyword presence is compared with hourly range midpoint using point-biserial correlation. Only keywords with at least 100 valid hourly observations are tested. A small p-value indicates a repeatable association in this dataset, not causation.

### Strongest positive rate differences

{table(['Keyword','n','Avg $/hr','Difference','r','p'], [[x['keyword'],x['count'],x['avg_hourly'],f"+{x['difference']}",x['correlation'],x['p_value']] for x in positive])}

### Strongest negative rate differences

{table(['Keyword','n','Avg $/hr','Difference','r','p'], [[x['keyword'],x['count'],x['avg_hourly'],x['difference'],x['correlation'],x['p_value']] for x in negative])}

## 2. Emerging categories

Growth compares average daily volume in the first and last 14-day windows.

{table(['Category','Early/day','Recent/day','Growth'], [[x['category'],x['early_daily_avg'],x['recent_daily_avg'],f"{x['growth_pct']:+.1f}%"] for x in emerging])}

## 3. High-demand role forecast

The model fits a linear time trend plus sine/cosine day-of-week seasonality. Evaluation is chronological (first 80% train, final 20% test); the displayed 14-day forecast is then refit on all complete days.

{table(['Category','Forecast/day','Change','MAE','RMSE','R²'], [[x['category'],x['forecast_daily_avg'],f"{x['expected_change_pct']:+.1f}%",x['mae'],x['rmse'],x['r2']] for x in forecast])}

Negative R² values are retained because they honestly show when a short-window linear model performs worse than a mean baseline. Forecasts are directional scenarios, not guaranteed counts.

## 4. Hourly rates by country

Only countries with at least 20 valid hourly postings are ranked.

{table(['Country','Average','Median','n'], [[x['country'],f"${x['average']}",f"${x['median']}",x['postings']] for x in countries])}

## 5. Recommendation engine

The dashboard includes a transparent content-based matcher over 1,600 recent, category-balanced jobs. Browser ranking uses title skill overlap (55%), category preference (25%), pay fit (15% including a default budget signal), and recency (5%). A Flask endpoint exposes equivalent filtering for integrations. No personal data is collected.

## 6. Monthly tracking

`analysis.py` is the repeatable update pipeline. Replace the input CSV and run it monthly; the dashboard consumes regenerated JSON without code changes. The dataset currently covers only one continuous 40-day period, so a true month-over-month comparison is not claimed.

## 7. Remote-work landscape

Explicit remote/WFH/distributed language appears in **{s['explicit_remote_share']:.2f}%** of titles. The signal changed by **{d['remote_work']['change_percentage_points']:+.2f} percentage points** between the first and final 14-day windows. This is a conservative text signal because Upwork jobs are already remote-friendly.

## 8. Future scenarios

- **Baseline:** {d['future_scenarios']['baseline']}
- **Upside:** {d['future_scenarios']['upside']}
- **Risk:** {d['future_scenarios']['risk']}

## Limitations

- The source is one platform and may not represent the whole labour market.
- The useful time window is 40 complete days, which limits seasonality and long-horizon inference.
- Offered rates are not accepted or final rates.
- Countries are client locations, not necessarily worker locations.
- Category assignment is deterministic keyword classification and can misclassify ambiguous titles.
- Historical posting links may have expired.
"""
(ROOT / "REPORT.md").write_text(text, encoding="utf-8")
print("Wrote REPORT.md")
