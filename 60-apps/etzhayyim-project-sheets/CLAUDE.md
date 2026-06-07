# etzhayyim-project-sheets — Google Sheets v4 + Microsoft Graph (workbook) compatible spreadsheet API

**sheets.etzhayyim.com** — a spreadsheet API whose external surface is shaped like **both**
Google Sheets v4 and Microsoft Graph workbook, over **one** canonical store on **kotoba
datomic** (graph `sheets-v1`). Third vertical of the workspace-compat program.

SSoT: `90-docs/adr/2606010500-workspace-compat-datomic-schema.md`

## 一行定義

Sheets ≝ CanonicalSpreadsheet[:sheet/*, gridJson] × KotobaDatomic[sheets-v1] × {GoogleSkin[/v4/spreadsheets], MicrosoftSkin[/v1.0/me/drive/.../workbook]}

## アーキテクチャ

```
Google SDK  → sheets.etzhayyim.com/v4/spreadsheets/{id}/values/{range}                  ┐
MS Graph SDK→ sheets.etzhayyim.com/v1.0/me/drive/items/{id}/workbook/worksheets/{s}/range ┘
  CF Worker sheets-compat (50-infra/cloudflare/workers/sheets-compat)
   ├─ /xrpc/ai.etzhayyim.apps.sheets.*  → pod (actor-worker passthrough)
   └─ provider REST → canonical XRPC → pod → reshape to provider JSON
  lg-sheets pod (60-apps/etzhayyim-project-sheets/lg, FastAPI server.py)
   → kotoba datomic transact/q/pull on graph sheets-v1 (:sheet/* namespace)
```

Same edge/routing/persistence rules as calendar/drive (ADR-2605111200; atproto
catch-all actor:true → pipethroughActorWorker → sheets.etzhayyim.com/xrpc → `SHEETS_POD_URL`
tunnel → pod; dedicated graph `sheets-v1`).

## Canonical XRPC methods (ai.etzhayyim.apps.sheets.*)

| method | Google Sheets v4 | Microsoft Graph workbook |
|---|---|---|
| `spreadsheetsGet` | spreadsheets.get | GET …/workbook/worksheets |
| `spreadsheetsCreate` | spreadsheets.create | POST /me/drive/root/children |
| `valuesGet` | spreadsheets.values.get | GET …/range(address='…') |
| `valuesUpdate` | spreadsheets.values.update (PUT) | PATCH …/range(address='…') |
| `valuesBatchUpdate` | spreadsheets.values:batchUpdate | (workbook session batch) |

Lexicons: `00-contracts/lexicons/ai/etzhayyim/apps/sheets/`. **Storage model (ADR D6)**: one
spreadsheet = one datomic entity; worksheet metadata in `:sheet/sheetsJson`, cell values in
`:sheet/gridJson` = `{title: [[stringified cells]]}` (no-float rule — cells are strings, cast
at the edge per valueRenderOption). A1 notation parsing in `lg_sheets/a1.py`. ETag/If-Match ←
`:sheet/revision`.

## Edge specifics
- MS function-form `range(address='Sheet1!A1:C10')` is normalized to `/range?address=…` by a
  pre-router middleware in `sheets-compat/src/index.ts`.
- Google `values:batchUpdate` (colon path) matched via a Hono regex param.

## ファイル構成
```
lg/  (Dockerfile, pyproject.toml, langgraph.json)
└── lg_sheets/{server,handlers,store,mapping,a1,kotoba_datomic,edn,ids}.py + graphs/health.py
tests/test_handlers.py        # 8 tests (A1 parse, grid round-trip, COLUMNS, batch, revision)
(edge) 50-infra/cloudflare/workers/sheets-compat/  # Google + MS skins (12 tests)
(infra) 50-infra/vultr/lg-sheets-pool/             # Helm (mirror lg-drive-pool)
```

## Test
```bash
cd 60-apps/etzhayyim-project-sheets/lg && python3 -m pytest tests/ -q
cd 50-infra/cloudflare/workers/sheets-compat && node --test test/*.test.ts
```
