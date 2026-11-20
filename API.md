# Recommendation API

Base URL when running locally: `http://localhost:8000`

## `GET /api/health`

Returns service status.

## `GET /api/insights`

Returns all aggregate analysis, model metrics, trends, country rates, and methodology notes.

## `GET /api/recommend`

Returns ranked job recommendations.

| Parameter | Type | Description |
|---|---:|---|
| `q` | string | Comma- or space-separated title keywords |
| `category` | string | Exact category name |
| `country` | string | Case-insensitive country substring |
| `min_rate` | number | Minimum hourly midpoint in USD |
| `limit` | integer | Results to return; maximum 100 |

Example:

```bash
curl "http://localhost:8000/api/recommend?q=python,ai&category=AI%20%26%20Machine%20Learning&min_rate=25&limit=5"
```

Response shape:

```json
{
  "count": 1,
  "results": [
    {
      "title": "Python AI Developer",
      "category": "AI & Machine Learning",
      "match_score": 92,
      "url": "https://www.upwork.com/jobs/..."
    }
  ]
}
```
