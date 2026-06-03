# News Metrics

This folder documents the source-of-truth and the manual update flow for
`etzhayyim-project-news` survival indicators.

## Metrics Keys

- `requests` (window: `1d`)
- `gccCredit` (window: `1d`)
- `adsRevenueJPYDaily` (window: `1d`)
- `adsRevenueJPYMonthly` (window: `1mo`)

These values live in `data/project-metrics.json` and can be applied into
`projects/*/PROJECT.jsonld` with:

```bash
python3 70-tools/70-tools/70-tools/scripts/project_metadata.py apply-metrics --metrics data/project-metrics.json
```

## Source-of-Truth (Proposed)

- `requests`
  - Primary: CDN access logs for `news.etzhayyim.com` (bucket `etzhayyim-static-sites`, prefix `news.etzhayyim.com`).
  - Fallback: GA4 page_view counts.
- `gccCredit`
  - Primary: GCC credit dashboard / credits service export.
- `adsRevenueJPYDaily` / `adsRevenueJPYMonthly`
  - Primary: ExoClick dashboard daily and monthly totals.

## Manual Update Flow

1. Collect daily numbers from the sources above.
2. Update the metrics file:

```bash
python3 70-tools/70-tools/70-tools/scripts/update_project_metrics.py \
  --project etzhayyim-project-news \
  --requests 12345 \
  --gcc-credit 678.9 \
  --ads-revenue-daily 1234 \
  --ads-revenue-monthly 56789
```

3. Apply the metrics into `PROJECT.jsonld` (optional but recommended):

```bash
python3 70-tools/70-tools/70-tools/scripts/project_metadata.py apply-metrics --metrics data/project-metrics.json
```

Notes:
- Do not commit credentials or API keys.
- Values are numeric and represent totals for the indicated window.

## ExoClick CSV Helper

If you export daily revenue from ExoClick as CSV, you can summarize the latest
(or a specific) day/month and optionally write it into `data/project-metrics.json`.

```bash
python3 70-tools/70-tools/70-tools/scripts/import_exoclick_csv.py \
  --csv /path/to/exoclick.csv \
  --date-column Date \
  --revenue-column Revenue
```

To write directly into the metrics file:

```bash
python3 70-tools/70-tools/70-tools/scripts/import_exoclick_csv.py \
  --csv /path/to/exoclick.csv \
  --date-column Date \
  --revenue-column Revenue \
  --write
```

If the export uses different column names or date formats, inspect the columns
first and set `--date-format`:

```bash
python3 70-tools/70-tools/70-tools/scripts/import_exoclick_csv.py --csv /path/to/exoclick.csv --list-columns
python3 70-tools/70-tools/70-tools/scripts/import_exoclick_csv.py \
  --csv /path/to/exoclick.csv \
  --date-column day \
  --revenue-column earnings \
  --date-format "%Y/%m/%d"
```
