# YABAI Pipeline Runbook

Date: 2026-03-03

## Purpose

Run `etzhayyim-project-yabai` analysis pipeline against `etzhayyim-project-resources` and persist normalized watchlist/source/entity/evidence/risk rows into Tonbo/LanceDB REST tables backed by Arrow-compatible schemas.

## Inputs

- Resources crawl data: `60-apps/etzhayyim-project-resources/content/crawl/page/*.jsonld`
- Resources TI data (optional): `60-apps/etzhayyim-project-resources/content/ti/indicator/**/*.jsonld`
- YABAI watchlist rows: `yabai_watchlist_signals`
- YABAI source rows: `yabai_sources`

## Command

```bash
cd 60-apps/etzhayyim-project-yabai/tools/yabai-pipeline
GOCACHE=/tmp/go-build-yabai go run . --dry-run
GOCACHE=/tmp/go-build-yabai go run .
```

Optional explicit paths:

```bash
GOCACHE=/tmp/go-build-yabai go run . \
  --resources-root /path/to/60-apps/etzhayyim-project-resources/content \
  --output /path/to/60-apps/etzhayyim-project-yabai/content
```

## Outputs

- Arrow-compatible tables via Tonbo/LanceDB REST:
  - `yabai_entities`
  - `yabai_evidences`
  - `yabai_risks`
  - `yabai_watchlist_signals`
  - `yabai_sources`

## Scoring

- `PenaltyScore`: weighted sum of evidence severity and confidence
- `InfoRisk`: Shannon-style `-log2(P(event))` weighted by confidence and severity
- `WellBecomingScore`: baseline minus penalty and information risk
- `YabaiRiskScore`: `clip(100 - WellBecomingScore + PenaltyScore * 0.8)`

## Operational Notes

- Runtime reads from LanceDB tables first. JSON-LD should be treated as compatibility/export material, not the primary store.
- Watchlist and public-source data are seeded/upserted as table rows so the UI and XRPC endpoints read the Arrow-backed store directly.
- If `content/ti` is absent, the pipeline continues with crawler + watchlist only.
