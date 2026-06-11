# kuruma KPI Dashboard Spec (Weekly)

## Purpose

Track whether kuruma is on path to 10M JPY/month ad revenue under "Japan info -> Global" strategy.

## KPI Groups

### 1) Acquisition

- `impressions` (search impressions)
- `clicks` (organic clicks)
- `ctr` (click-through-rate)
- `avg_position` (search average position)
- `non_ja_traffic_share`

### 2) Content Production

- `pages_published_ja`
- `pages_published_en`
- `pages_published_other`
- `pages_refreshed`
- `indexed_pages_total`
- `indexation_latency_days`

### 3) Monetization

- `pv_total`
- `sessions_total`
- `viewability_rate`
- `fill_rate`
- `net_ecpm_jpy`
- `rpm_jpy`
- `ad_revenue_jpy`

### 4) Quality

- `cwv_mobile_pass_rate`
- `engaged_time_sec`
- `bounce_rate`
- `ad_complaint_count`

## Segment Dimensions

- locale: `ja`, `en`, `es`, `pt`, `de`, `fr`, `other`
- page_type: `spec`, `compare`, `review`, `ownership`, `maker`
- device: `mobile`, `desktop`

## Weekly Review Questions

- Are top page clusters gaining rankings and clicks?
- Is non-JA share growing without hurting JA core?
- Is eCPM growth coming with acceptable UX quality?
- Which templates need refresh or ad density adjustment?
