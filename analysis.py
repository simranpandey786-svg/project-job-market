#!/usr/bin/env python3
"""Build the data products used by the Job Market Intelligence dashboard.

The input is the Upwork CSV supplied with the assignment.  The script keeps
hourly rates and fixed-price budgets separate because they measure different
things and should not be averaged together.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from scipy.stats import pointbiserialr
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


CATEGORY_RULES = {
    "AI & Machine Learning": r"\b(ai|artificial intelligence|machine learning|ml|llm|gpt|chatgpt|computer vision|nlp|neural|data scien)",
    "Legal": r"\b(legal|lawyer|attorney|paralegal|law firm|contract law)\b",
    "Finance & Accounting": r"\b(accounting|accountant|bookkeep|tax|financial|finance|cpa|quickbooks|xero)\b",
    "Web Development": r"\b(web|website|wordpress|shopify|frontend|front-end|backend|back-end|full.?stack|react|vue|angular|laravel|django|flask|php|javascript|node\.?(js)?)\b",
    "Mobile Development": r"\b(mobile|android|ios|flutter|react native|swift|kotlin|app developer)\b",
    "Data & Analytics": r"\b(data analy|analyst|power bi|tableau|excel|sql|business intelligence|dashboard|data entry|web scraping)\b",
    "Design & Creative": r"\b(design|designer|figma|logo|graphic|illustrat|ui.?ux|animation|video edit|3d|canva)\b",
    "Sales & Marketing": r"\b(marketing|seo|sales|lead generation|social media|facebook ads|google ads|media buyer|email campaign|appointment setter)\b",
    "Writing & Translation": r"\b(writer|writing|copywrit|content|translation|translator|proofread|editor|blog|article)\b",
    "Admin & Support": r"\b(virtual assistant|customer support|customer service|administrative|admin assistant|bookkeep|recruit|project manager|operations)\b",
    "Engineering & CAD": r"\b(engineer|engineering|autocad|cad|solidworks|architect|mechanical|electrical|civil|revit)\b",
    "Cybersecurity & Cloud": r"\b(cyber|security|aws|azure|cloud|devops|docker|kubernetes|penetration test|network)\b",
}

STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in",
    "is", "it", "job", "looking", "need", "needed", "of", "on", "our", "project",
    "required", "the", "to", "with", "work", "expert", "specialist", "developer",
    "development", "experienced", "create", "help", "using", "wanted", "services",
}


def classify_title(title: str) -> str:
    title = str(title).lower()
    for category, pattern in CATEGORY_RULES.items():
        if re.search(pattern, title):
            return category
    return "Other"


def words(title: str) -> set[str]:
    return {
        token for token in re.findall(r"[a-z][a-z+#.-]{2,}", str(title).lower())
        if token not in STOP_WORDS and not token.startswith("http")
    }


def safe_number(value, digits=2):
    if pd.isna(value) or not math.isfinite(float(value)):
        return None
    return round(float(value), digits)


def keyword_salary_analysis(hourly: pd.DataFrame, min_count: int = 100) -> list[dict]:
    salary = hourly["hourly_mid"].to_numpy(dtype=float)
    token_rows = [words(t) for t in hourly["title"]]
    counts = Counter(token for row in token_rows for token in row)
    overall = float(np.mean(salary))
    results = []
    for token, count in counts.items():
        if count < min_count or count > len(hourly) * 0.45:
            continue
        present = np.fromiter((token in row for row in token_rows), dtype=np.int8)
        corr, p_value = pointbiserialr(present, salary)
        if not np.isfinite(corr):
            continue
        token_mean = float(np.mean(salary[present == 1]))
        results.append({
            "keyword": token,
            "count": int(count),
            "avg_hourly": round(token_mean, 2),
            "difference": round(token_mean - overall, 2),
            "correlation": round(float(corr), 4),
            "p_value": round(float(p_value), 6),
        })
    return sorted(results, key=lambda x: abs(x["correlation"]), reverse=True)[:40]


def daily_category_counts(df: pd.DataFrame, full_dates: pd.DatetimeIndex) -> pd.DataFrame:
    counts = (
        df.groupby([df["published_date"].dt.floor("D"), "category"])
        .size().unstack(fill_value=0)
        .reindex(full_dates, fill_value=0)
    )
    return counts


def model_demand(daily: pd.DataFrame, forecast_days: int = 14):
    day_index = np.arange(len(daily))
    dow = daily.index.day_of_week.to_numpy()
    features = np.column_stack([
        day_index,
        np.sin(2 * np.pi * dow / 7),
        np.cos(2 * np.pi * dow / 7),
    ])
    split = max(14, int(len(daily) * 0.8))
    split = min(split, len(daily) - 7)
    future_i = np.arange(len(daily), len(daily) + forecast_days)
    future_dates = pd.date_range(daily.index.max() + pd.Timedelta(days=1), periods=forecast_days)
    future_dow = future_dates.day_of_week.to_numpy()
    future_features = np.column_stack([
        future_i,
        np.sin(2 * np.pi * future_dow / 7),
        np.cos(2 * np.pi * future_dow / 7),
    ])

    metrics, forecasts, saved = [], {}, {}
    for category in daily.columns:
        y = daily[category].to_numpy(dtype=float)
        evaluation_model = LinearRegression().fit(features[:split], y[:split])
        predicted_test = np.clip(evaluation_model.predict(features[split:]), 0, None)
        actual_test = y[split:]
        mae = mean_absolute_error(actual_test, predicted_test)
        rmse = mean_squared_error(actual_test, predicted_test) ** 0.5
        r2 = r2_score(actual_test, predicted_test) if len(actual_test) > 1 else np.nan
        denom = np.maximum(actual_test, 1)
        mape = float(np.mean(np.abs(actual_test - predicted_test) / denom) * 100)

        model = LinearRegression().fit(features, y)
        future = np.clip(model.predict(future_features), 0, None)
        forecasts[category] = [round(float(v), 1) for v in future]
        saved[category] = model
        metrics.append({
            "category": category,
            "test_days": int(len(actual_test)),
            "mae": round(float(mae), 2),
            "rmse": round(float(rmse), 2),
            "r2": safe_number(r2, 3),
            "mape": round(mape, 1),
            "forecast_daily_avg": round(float(np.mean(future)), 1),
            "recent_daily_avg": round(float(np.mean(y[-14:])), 1),
            "expected_change_pct": round(float((np.mean(future) - np.mean(y[-14:])) / max(np.mean(y[-14:]), 1) * 100), 1),
        })
    metrics.sort(key=lambda x: x["forecast_daily_avg"], reverse=True)
    return metrics, forecasts, [d.strftime("%Y-%m-%d") for d in future_dates], saved


def emerging_categories(daily: pd.DataFrame) -> list[dict]:
    window = min(14, max(7, len(daily) // 3))
    early = daily.iloc[:window].mean()
    recent = daily.iloc[-window:].mean()
    output = []
    for category in daily.columns:
        base, current = float(early[category]), float(recent[category])
        growth = (current - base) / max(base, 1) * 100
        output.append({
            "category": category,
            "early_daily_avg": round(base, 1),
            "recent_daily_avg": round(current, 1),
            "growth_pct": round(growth, 1),
            "emerging": bool(growth >= 10 and current >= 20),
        })
    return sorted(output, key=lambda x: x["growth_pct"], reverse=True)


def build(input_path: Path, output_dir: Path, model_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    model_dir.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(input_path)
    raw_rows = len(df)
    df["published_date"] = pd.to_datetime(df["published_date"], utc=True, errors="coerce")
    for col in ["hourly_low", "hourly_high", "budget"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["is_hourly"] = df["is_hourly"].astype(str).str.lower().eq("true")
    df = df.dropna(subset=["title", "published_date"]).copy()
    # Detect the continuous high-volume collection window. A few stale rows
    # precede the filename's stated period, and the final day may be partial.
    raw_daily = df.groupby(df["published_date"].dt.floor("D")).size().sort_index()
    active_dates = raw_daily[raw_daily >= 100].index
    coverage_start = active_dates.min()
    coverage_end = active_dates.max()
    previous_week_median = raw_daily.loc[raw_daily.index < coverage_end].tail(7).median()
    partial_last_day = bool(raw_daily.loc[coverage_end] < previous_week_median * 0.60)
    if partial_last_day:
        coverage_end = raw_daily.loc[raw_daily.index < coverage_end].index.max()
    before_window = len(df)
    df = df[(df["published_date"] >= coverage_start) & (df["published_date"] < coverage_end + pd.Timedelta(days=1))].copy()
    excluded_outside_window = before_window - len(df)
    # A midpoint is an interpretable summary of an offered hourly range.
    df["hourly_mid"] = df[["hourly_low", "hourly_high"]].mean(axis=1)
    df["category"] = df["title"].map(classify_title)
    df["country"] = df["country"].fillna("").str.strip().replace("", "Unknown")
    df["remote_explicit"] = df["title"].str.contains(r"\b(?:remote|work from home|wfh|distributed)\b", case=False, regex=True, na=False)

    start = df["published_date"].min().floor("D")
    end = df["published_date"].max().floor("D")
    dates = pd.date_range(start, end, freq="D", tz="UTC")
    daily = daily_category_counts(df, dates)
    demand_metrics, forecast, forecast_dates, models = model_demand(daily)
    joblib.dump({"models": models, "categories": list(daily.columns)}, model_dir / "demand_models.joblib")

    valid_hourly = df[df["is_hourly"] & df["hourly_mid"].between(1, 300)].copy()
    valid_fixed = df[(~df["is_hourly"]) & df["budget"].between(1, 1_000_000)].copy()
    keyword_stats = keyword_salary_analysis(valid_hourly)

    country = (
        valid_hourly[valid_hourly["country"] != "Unknown"]
        .groupby("country")["hourly_mid"].agg(["mean", "median", "count"])
        .query("count >= 20").sort_values("mean", ascending=False).head(35)
    )
    country_rates = [
        {"country": idx, "average": round(float(row["mean"]), 2), "median": round(float(row["median"]), 2), "postings": int(row["count"])}
        for idx, row in country.iterrows()
    ]

    emerging = emerging_categories(daily)
    category_totals = df["category"].value_counts()
    category_stats = []
    for category, total in category_totals.items():
        h = valid_hourly[valid_hourly["category"] == category]["hourly_mid"]
        f = valid_fixed[valid_fixed["category"] == category]["budget"]
        category_stats.append({
            "category": category,
            "postings": int(total),
            "share_pct": round(float(total / len(df) * 100), 1),
            "avg_hourly": safe_number(h.mean()),
            "median_fixed_budget": safe_number(f.median()),
        })

    daily_total = df.groupby(df["published_date"].dt.floor("D")).size().reindex(dates, fill_value=0)
    daily_remote = df[df["remote_explicit"]].groupby(df.loc[df["remote_explicit"], "published_date"].dt.floor("D")).size().reindex(dates, fill_value=0)
    remote_share = daily_remote / daily_total.replace(0, np.nan) * 100
    remote_first = float(remote_share.iloc[:14].mean())
    remote_last = float(remote_share.iloc[-14:].mean())

    trend_series = []
    for date in dates:
        row = {"date": date.strftime("%Y-%m-%d"), "total": int(daily_total.loc[date]), "remote": int(daily_remote.loc[date])}
        for category in daily.columns:
            row[category] = int(daily.loc[date, category])
        trend_series.append(row)

    # Limit browser payload while retaining varied, recent recommendations.
    recommendations = (
        df.sort_values("published_date", ascending=False)
        .drop_duplicates(subset=["link"])
        .groupby("category", group_keys=False).head(180)
        .sort_values("published_date", ascending=False).head(1600)
    )
    jobs = []
    for _, row in recommendations.iterrows():
        jobs.append({
            "title": row["title"], "url": row["link"], "date": row["published_date"].strftime("%Y-%m-%d"),
            "category": row["category"], "country": row["country"], "is_hourly": bool(row["is_hourly"]),
            "hourly_low": safe_number(row["hourly_low"]), "hourly_high": safe_number(row["hourly_high"]),
            "budget": safe_number(row["budget"]),
        })

    top_future = demand_metrics[:5]
    insights = {
        "metadata": {
            "source": input_path.name, "generated_at": pd.Timestamp.now(tz="UTC").isoformat(),
            "raw_rows": raw_rows, "valid_rows": int(len(df)), "excluded_outside_continuous_window": int(excluded_outside_window),
            "partial_last_day_excluded": partial_last_day, "start_date": start.strftime("%Y-%m-%d"),
            "end_date": end.strftime("%Y-%m-%d"), "days": int(len(dates)),
            "hourly_rows": int(len(valid_hourly)), "fixed_rows": int(len(valid_fixed)),
        },
        "summary": {
            "average_hourly": round(float(valid_hourly["hourly_mid"].mean()), 2),
            "median_hourly": round(float(valid_hourly["hourly_mid"].median()), 2),
            "median_fixed_budget": round(float(valid_fixed["budget"].median()), 2),
            "top_category": category_totals.index[0],
            "explicit_remote_share": round(float(df["remote_explicit"].mean() * 100), 2),
        },
        "category_stats": category_stats,
        "keyword_salary": keyword_stats,
        "emerging_categories": emerging,
        "demand_model": {"algorithm": "Linear regression with weekly seasonality", "metrics": demand_metrics, "forecast_dates": forecast_dates, "forecast": forecast},
        "country_rates": country_rates,
        "daily_trends": trend_series,
        "remote_work": {
            "first_14_day_share": round(remote_first, 2), "last_14_day_share": round(remote_last, 2),
            "change_percentage_points": round(remote_last - remote_first, 2),
            "note": "Upwork is inherently remote-friendly; this metric only counts titles that explicitly say remote/WFH/distributed.",
        },
        "future_scenarios": {
            "baseline": "The statistical forecast assumes the observed trend and weekly posting rhythm continue for 14 days.",
            "upside": f"Demand could concentrate in {', '.join(x['category'] for x in top_future[:3])}, the highest-volume forecast categories.",
            "risk": "The dataset covers a short window, so platform events, seasonality and macroeconomic shocks can outweigh the fitted trend.",
        },
        "methodology": {
            "salary": "Hourly range midpoint; values outside $1-$300/hour excluded. Fixed budgets analyzed separately.",
            "keywords": "Point-biserial correlation between keyword presence and hourly midpoint; only keywords with at least 100 observations.",
            "emerging": "First 14 days versus last 14 days by average daily category posting count.",
            "forecast": "Chronological 80/20 evaluation, linear time trend plus sine/cosine day-of-week seasonality, then 14-day forecast.",
        },
    }
    (output_dir / "insights.json").write_text(json.dumps(insights, ensure_ascii=False, indent=2), encoding="utf-8")
    (output_dir / "jobs.json").write_text(json.dumps(jobs, ensure_ascii=False), encoding="utf-8")
    return insights


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", default=Path("dist/data"), type=Path)
    parser.add_argument("--models", default=Path("models"), type=Path)
    args = parser.parse_args()
    insights = build(args.input, args.output, args.models)
    print(json.dumps({"metadata": insights["metadata"], "summary": insights["summary"]}, indent=2))


if __name__ == "__main__":
    main()
