# etzhayyim-project-comprehend

`etzhayyim-comprehend` is a legacy runtime-cron-driven collector that writes JSON-LD (RDF) observations and run manifests into `60-apps/etzhayyim-project-resources/content/` via `gitstate`.

## Runtime

- Cron: `infra/legacy-runtime/components/cron-comprehend.yaml` calls `POST /jobs/comprehend-tick`
- Git flush: `infra/legacy-runtime/components/cron-gitstate.yaml` calls `/jobs/git-flush`

## Config

Targets file:

- `60-apps/etzhayyim-project-comprehend/config/targets.json`

## Service (Go)

- Path: `60-apps/etzhayyim-project-comprehend/legacy-runtime/etzhayyim-comprehend-scheduler-6k2q1n9p/cmd/server/main.go`

Env vars:

- `HTTP_PORT` (default `80`)
- `APP_HTTP_ENDPOINT` (default `http://localhost:3500`)
- `REPO_DIR` (default repo root)
- `CONTENT_DIR` (default `60-apps/etzhayyim-project-resources/content`)
- `TARGETS_PATH` (default `60-apps/etzhayyim-project-comprehend/config/targets.json`)
- `WWW_CRAWLER_APP_ID` (default `www-crawler`)

## SHACL

Shapes (JSON-LD):

- `60-apps/etzhayyim-project-resources/shacl/comprehend/shapes.jsonld`
