# Job Market Analysis and Recommendation System

## Executive summary

This analysis uses **242,359 Upwork postings** from the continuous collection window **2024-02-13 to 2024-03-23**. It excludes 2,468 sparse out-of-window or partial-day records to avoid distorting time trends. The cleaned hourly midpoint averages **$28.41/hour** (median **$22.50**), while fixed-price jobs have a median budget of **$100**. Hourly and fixed-price compensation are never combined.

## 1. Job-title keywords and offered salaries

Keyword presence is compared with hourly range midpoint using point-biserial correlation. Only keywords with at least 100 valid hourly observations are tested. A small p-value indicates a repeatable association in this dataset, not causation.

### Strongest positive rate differences

|Keyword|n|Avg $/hr|Difference|r|p|
|---|---|---|---|---|---|
|attorney|186|98.8|+70.39|0.1216|0.0|
|lawyer|212|86.08|+57.67|0.1064|0.0|
|advice|108|75.93|+47.52|0.0625|0.0|
|you|325|66.38|+37.97|0.0868|0.0|
|money|115|61.22|+32.81|0.0446|0.0|
|llc|104|60.75|+32.34|0.0418|0.0|
|cpa|187|57.9|+29.49|0.0511|0.0|
|cryptocurrency|234|57.64|+29.23|0.0567|0.0|

### Strongest negative rate differences

|Keyword|n|Avg $/hr|Difference|r|p|
|---|---|---|---|---|---|
|onlyfans|276|9.13|-19.28|-0.0406|0.0|
|virtual|2674|11.55|-16.86|-0.1119|0.0|
|caller|380|11.69|-16.72|-0.0413|0.0|
|assistant|4144|12.6|-15.81|-0.1315|0.0|
|entry|934|14.66|-13.75|-0.0535|0.0|
|cold|1033|15.16|-13.25|-0.0542|0.0|

## 2. Emerging categories

Growth compares average daily volume in the first and last 14-day windows.

|Category|Early/day|Recent/day|Growth|
|---|---|---|---|
|Cybersecurity & Cloud|43.9|52.1|+18.6%|
|AI & Machine Learning|138.3|161.5|+16.7%|
|Sales & Marketing|554.5|645.1|+16.3%|
|Web Development|843.4|960.2|+13.9%|
|Design & Creative|580.7|657.6|+13.2%|
|Finance & Accounting|104.5|116.6|+11.6%|

## 3. High-demand role forecast

The model fits a linear time trend plus sine/cosine day-of-week seasonality. Evaluation is chronological (first 80% train, final 20% test); the displayed 14-day forecast is then refit on all complete days.

|Category|Forecast/day|Change|MAE|RMSE|R²|
|---|---|---|---|---|---|
|Web Development|1024.1|+8.9%|95.06|121.71|0.403|
|Design & Creative|704.5|+9.1%|104.1|116.32|-0.357|
|Sales & Marketing|693.8|+9.9%|106.1|117.43|0.165|
|Writing & Translation|410.6|-2.0%|60.28|68.5|0.06|
|AI & Machine Learning|175.9|+10.2%|34.24|40.63|-1.099|
|Mobile Development|140.2|+8.7%|27.01|29.75|-2.147|

Negative R² values are retained because they honestly show when a short-window linear model performs worse than a mean baseline. Forecasts are directional scenarios, not guaranteed counts.

## 4. Hourly rates by country

Only countries with at least 20 valid hourly postings are ranked.

|Country|Average|Median|n|
|---|---|---|---|
|Malaysia|$47.54|$22.5|325|
|Thailand|$41.71|$22.5|292|
|Zambia|$38.52|$25.0|21|
|Azerbaijan|$34.08|$25.0|24|
|Latvia|$31.71|$30.0|111|
|Oman|$31.17|$30.0|45|
|United States|$31.15|$25.0|47680|
|Kenya|$30.95|$26.5|363|
|Guatemala|$30.5|$29.5|25|
|Ecuador|$30.34|$18.25|38|

## 5. Recommendation engine

The dashboard includes a transparent content-based matcher over 1,600 recent, category-balanced jobs. Browser ranking uses title skill overlap (55%), category preference (25%), pay fit (15% including a default budget signal), and recency (5%). A Flask endpoint exposes equivalent filtering for integrations. No personal data is collected.

## 6. Monthly tracking

`analysis.py` is the repeatable update pipeline. Replace the input CSV and run it monthly; the dashboard consumes regenerated JSON without code changes. The dataset currently covers only one continuous 40-day period, so a true month-over-month comparison is not claimed.

## 7. Remote-work landscape

Explicit remote/WFH/distributed language appears in **0.55%** of titles. The signal changed by **-0.01 percentage points** between the first and final 14-day windows. This is a conservative text signal because Upwork jobs are already remote-friendly.

## 8. Future scenarios

- **Baseline:** The statistical forecast assumes the observed trend and weekly posting rhythm continue for 14 days.
- **Upside:** Demand could concentrate in Other, Web Development, Design & Creative, the highest-volume forecast categories.
- **Risk:** The dataset covers a short window, so platform events, seasonality and macroeconomic shocks can outweigh the fitted trend.

## Limitations

- The source is one platform and may not represent the whole labour market.
- The useful time window is 40 complete days, which limits seasonality and long-horizon inference.
- Offered rates are not accepted or final rates.
- Countries are client locations, not necessarily worker locations.
- Category assignment is deterministic keyword classification and can misclassify ambiguous titles.
- Historical posting links may have expired.
