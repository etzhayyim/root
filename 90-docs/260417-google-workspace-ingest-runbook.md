# Google Workspace Ingest — Runbook

**Status**: Phase 0 (schema + scaffold) — 2026-04-17
**Request**: 「Google Workspace で使っているデータをすべて取り込みたい」 (継続, 1Password にある全アカウント)

## Scope

| Service | API | App folder | Ingest status |
|---|---|---|---|
| Gmail | Gmail API v1 | `60-apps/etzhayyim-project-gmail/` | ✅ Live (multi-account OAuth, cron 15m incremental via `history.list`) |
| Calendar | Calendar API v3 | `60-apps/etzhayyim-project-calendar/` | ⏳ Scaffold — existing AT record store, Google API sync TODO |
| Drive | Drive API v3 | `60-apps/etzhayyim-project-drive/` | ⏳ Scaffold — UI only, needs OAuth + `changes.list` + `files.watch` |
| Contacts | People API v1 | `60-apps/etzhayyim-project-contacts/` | ❌ Not built |
| Tasks | Tasks API v1 | `60-apps/etzhayyim-project-tasks/` | ❌ Not built |
| Docs | Docs API v1 | `60-apps/etzhayyim-project-docs/` | ❌ Not built |
| Sheets | Sheets API v4 | `60-apps/etzhayyim-project-sheets/` | ❌ Not built |
| Slides | Slides API v1 | `60-apps/etzhayyim-project-slides/` | ❌ Not built |
| Meet | Meet REST API v2 | `60-apps/etzhayyim-project-meet/` | ❌ Not built |
| **Keep** | no public API | — | 🚫 **Out of scope** (no ingest path) |
| **Sites** | v1 classic read-metadata only | — | 🚫 **Out of scope** (near-zero value) |
| **Chat** | requires bot-install per Workspace | — | ⏸ **Deferred** (different auth model) |

## Token & auth strategy

### Why 1Password can't be the token source
1Password stores **passwords**, not OAuth2 refresh tokens. Mixed-domain
accounts (`jun@etzhayyim.com`, `root@junkawasaki.com`, `root@jk.luxury`, …)
cannot share a Service Account + Domain-Wide Delegation (DWD only works
inside a single Workspace tenant). Therefore:

- 1Password role = **account-list source only** (discover which Google
  accounts exist + handle hints for OAuth `login_hint` param).
- Per-account OAuth2 consent flow is **unavoidable** — one browser
  roundtrip per `(account, service)` pair (service scopes unioned; one
  consent per account works if all scopes requested together).
- Refresh tokens stored with **KEK envelope encryption** in each app's
  D1 `vertex_*_oauth_token` table (same ADR-0010 Stage 1 pattern the
  gmail worker uses). Future: migrate to `vault.etzhayyim.com`
  (`com.etzhayyim.vault.*`) per CLAUDE.md Vault Zero-Knowledge Invariant.

### Consent scopes (unified per account)

Request every scope needed for the 8 services in a single consent so the
user grants once per account. User revoke path:
<https://myaccount.google.com/permissions>.

```
openid email profile
https://www.googleapis.com/auth/gmail.modify
https://www.googleapis.com/auth/calendar
https://www.googleapis.com/auth/drive
https://www.googleapis.com/auth/contacts.readonly
https://www.googleapis.com/auth/contacts.other.readonly
https://www.googleapis.com/auth/directory.readonly
https://www.googleapis.com/auth/tasks
https://www.googleapis.com/auth/documents.readonly
https://www.googleapis.com/auth/spreadsheets.readonly
https://www.googleapis.com/auth/presentations.readonly
https://www.googleapis.com/auth/meetings.space.readonly
```

Google Cloud Console → single OAuth2 Web client (same `client_id` /
`client_secret` reused by every app Worker via wrangler secrets
`SS_GOOGLE_OAUTH_CLIENT_ID` / `SS_GOOGLE_OAUTH_CLIENT_SECRET`).

Add each app's redirect URI in Console:
```
https://gmail.etzhayyim.com/oauth/callback
https://calendar.etzhayyim.com/oauth/callback
https://drive.etzhayyim.com/oauth/callback
https://contacts.etzhayyim.com/oauth/callback
https://tasks.etzhayyim.com/oauth/callback
https://docs.etzhayyim.com/oauth/callback
https://sheets.etzhayyim.com/oauth/callback
https://slides.etzhayyim.com/oauth/callback
https://meet.etzhayyim.com/oauth/callback
```

## Continuous sync strategy

| Service | Primary trigger | Backup / first-run |
|---|---|---|
| Gmail | `users.watch` → Pub/Sub (future); currently **cron 15m** `history.list(startHistoryId=...)` | `messages.list` seed (25 msgs) |
| Calendar | `events.watch` → webhook (7-day TTL, cron renewal); `events.list(syncToken=...)` each tick | `events.list` seed full year |
| Drive | `files.watch` → webhook (7-day TTL, cron renewal); `changes.list(pageToken=...)` each tick | `changes.getStartPageToken` |
| Contacts | `people.connections.list(syncToken=...)` cron 30m | full list seed |
| Tasks | `tasks.list(updatedMin=...)` cron 1h | full list seed |
| Docs / Sheets / Slides | Drive `changes.list` identifies mutated `file_id` → fetch via respective API, cron 15m | initial backfill by mimeType filter |
| Meet | `conferenceRecords.list(filter="start_time>...")` cron 1h | full list seed (90-day retention) |

**Watch channel renewal**: store channel meta in
`vertex_gcal_watch_channel` / `vertex_gdrive_watch_channel`
(`channel_id`, `resource_id`, `expiration`, `renew_at`). Cron checks
`renew_at < now + 1h` → `channels.stop` + `events.watch`/`files.watch`
again.

**Webhook endpoint**: `https://{app}.etzhayyim.com/webhook/google` receives
`X-Goog-Channel-ID`/`X-Goog-Resource-ID` headers → push syncToken-based
delta to B2 → cron processes.

## Schema

All tables created by migration
`30-graph/graph-schema/migrations/20260417140000_vertex_google_workspace_tables.ts`.

P10v2 GraphAr-native: 1 AT record = 1 row, typed columns, RLS 3-col,
`signal:v1:{ciphertext}` for private text (subject, notes, body
fragments, contact info). Schema map:

| Service | Vertex tables | Edge tables |
|---|---|---|
| calendar | `vertex_gcal_{account,calendar,event,attendee,watch_channel}` | `edge_gcal_{event_in_calendar,event_attendee}` |
| drive | `vertex_gdrive_{account,file,permission,revision,watch_channel}` | `edge_gdrive_{file_parent,file_permission}` |
| contacts | `vertex_gcontacts_{account,contact,group}` | `edge_gcontacts_contact_group` |
| tasks | `vertex_gtasks_{account,list,task}` | `edge_gtasks_{task_in_list,task_parent}` |
| docs | `vertex_gdocs_{account,document,revision}` | — |
| sheets | `vertex_gsheets_{account,spreadsheet,sheet}` | `edge_gsheets_sheet_in_spreadsheet` |
| slides | `vertex_gslides_{account,presentation,slide}` | `edge_gslides_slide_in_presentation` |
| meet | `vertex_gmeet_{account,conference,participant,recording}` | `edge_gmeet_{conference_participant,conference_calendar_event,recording_drive_file}` |
| cross | `mv_gworkspace_account_health` (MV) | — |

**Content-level granularity (Docs/Sheets/Slides)**: store structural
JSON blobs under `body_content_json` / `grid_values_json` /
`page_elements_json` with a trimmed preview field. Full
element-by-element vertex projection is deferred (10x schema cost,
negligible early value until a consumer app needs it).

## Prerequisites (do these first — Phase 0 is NOT ready until done)

1. **Google Cloud Console**: create one OAuth2 Web client; add the
   redirect URIs listed above; enable Gmail / Calendar / Drive / People /
   Tasks / Docs / Sheets / Slides / Meet APIs in the same project.
2. **CF secrets store** (one-time): put the three shared secrets:
   - `google_oauth_client_id`
   - `google_oauth_client_secret`
   - `gworkspace_token_kek` (32-byte base64url; `openssl rand -base64 32 | tr '/+' '_-' | tr -d '='`)
3. **D1 databases** (one per service): each scaffolded `wrangler.jsonc`
   has `database_id: "REPLACE_AFTER_wrangler_d1_create"`. Run:
   ```bash
   wrangler d1 create calendar-tokens
   wrangler d1 create drive-tokens
   wrangler d1 create contacts-tokens
   wrangler d1 create tasks-tokens
   wrangler d1 create docs-tokens
   wrangler d1 create sheets-tokens
   wrangler d1 create slides-tokens
   wrangler d1 create meet-tokens
   ```
   Paste each returned `database_id` into the corresponding
   `wrangler.jsonc`.

## Deploy sequence

```bash
# 1. Apply schema migration
cd 30-graph/graph-schema
DATABASE_URL=... pnpm db:migrate
DATABASE_URL=... pnpm db:gen
DATABASE_URL=... pnpm db:drift   # must report OK

# 2. Provision secrets (one-time per app)
cd 60-apps/etzhayyim-project-{service}/appview/<component-dir>
wrangler secret put SS_GOOGLE_OAUTH_CLIENT_ID
wrangler secret put SS_GOOGLE_OAUTH_CLIENT_SECRET
wrangler secret put SS_GWORKSPACE_TOKEN_KEK   # 32-byte base64url, shared across all services

# 3. Build + deploy each app
for svc in gmail calendar drive contacts tasks docs sheets slides meet; do
  cd 60-apps/etzhayyim-project-$svc/appview/*/
  etzhayyim deploy
done

# 4. Per-account OAuth
#    For each account from 70-tools/scripts/google-accounts-from-1p.sh:
#    open https://gmail.etzhayyim.com/xrpc/com.etzhayyim.apps.gmail.connectAccount?email=...
#    → redirects to Google consent → sets tokens in every app's D1 table.
```

## Per-account onboarding flow

```
1. Operator runs: ./70-tools/scripts/google-accounts-from-1p.sh
     → prints JSON: [{ "email": "jun@etzhayyim.com", "label": "…" }, …]
2. For each email:
     a. Open https://gmail.etzhayyim.com in browser signed in as etzhayyim user.
     b. Call com.etzhayyim.apps.gmail.connectAccount { email }
     c. Google consent screen → grants all 12 scopes.
     d. /oauth/callback stores refresh_token in vertex_gmail_oauth_token.
     e. Repeat for calendar/drive/contacts/tasks/docs/sheets/slides/meet
        (same consent grant transparently gives all services a token
        if they request the same scopes + same client_id).
3. Each app's cron picks up new active tokens and begins sync.
```

## Shared OAuth module

Extract the gmail KEK envelope / token table / Google token exchange
into `60-apps/_shared/google-oauth.ts` (or vendor copy per app since the
current etzhayyim deploy pipeline favours single-file TS Native). For Phase
0, each new app **copies** the 8 helper functions from
`etzhayyim-project-gmail/appview/etzhayyim-wasm-gmail-gm4il0x1/src/app.ts`:
`envelopeEncrypt`, `envelopeDecrypt`, `importKek`, `b64u{Encode,Decode}`,
`exchangeAuthCode`, `refreshAccessToken`, `getAccessToken`,
`ensureTokenTable`. Rename the D1 table per service
(`vertex_gcal_oauth_token`, `vertex_gdrive_oauth_token`, …) with
identical shape.

## Known gaps / Phase 1+

- **Vault migration**: refresh tokens currently in per-app D1 KEK
  envelope. Move to `vault.etzhayyim.com` (`com.etzhayyim.vault.putItem` with
  `kind=google_refresh_token`) when the vault app stabilises. CLAUDE.md
  "Vault Zero-Knowledge Invariant".
- **Pub/Sub (Gmail)**: current gmail app uses cron `history.list`.
  Switch to Pub/Sub via Cloudflare Queues adapter to cut latency from
  15m to seconds.
- **Content extraction (Docs/Sheets/Slides)**: structural vertices
  (paragraph, cell, slide-element) deferred until a downstream consumer
  requires them. Current schema stores `*_json` blobs + trimmed preview.
- **Chat ingest**: requires Workspace-admin to install a Chat bot.
  Design doc out when the first use-case lands.
- **Meet recordings**: `meet.conferenceRecords` is the source of truth;
  recordings+transcripts land in Drive. Must reconcile
  `vertex_gmeet_recording` with `vertex_gdrive_file` via
  `edge_gmeet_recording_drive_file`.
- **Legacy AT records in calendar app**: the current calendar app is a
  generic RFC 5545 event store. Google Calendar sync writes to the same
  `vertex_gcal_event` table with `rkey = event_id`; downstream consumers
  see a uniform graph regardless of source.

## Files touched in Phase 0

- `30-graph/graph-schema/migrations/20260417140000_vertex_google_workspace_tables.ts` — new
- `90-docs/260417-google-workspace-ingest-runbook.md` — this file
- `70-tools/scripts/google-accounts-from-1p.sh` — account-list discovery
- `60-apps/etzhayyim-project-calendar/appview/calendar-mcp-component/src/app.ts` — Google Calendar sync added (full)
- `60-apps/etzhayyim-project-{drive,contacts,tasks,docs,sheets,slides,meet}/appview/*-mcp-component/src/app.ts` — scaffolded by `70-tools/scripts/scaffold-google-app.sh`. drive→`drive-app-component/`, docs→`docs-performers-r5ycqp6x/` (consolidated with existing svelte UI dirs).
- `00-contracts/lexicons/com/etzhayyim/apps/{calendar,drive,contacts,tasks,docs,sheets,slides,meet}/{connectAccount,syncFromGoogle}.json` — 16 new lexicons
- `70-tools/templates/google-workspace-oauth.ts` — inline-copy OAuth/KEK helpers reference
- `70-tools/scripts/scaffold-google-app.sh` — per-service app generator

## Phase 0 completion checklist

- [x] Google Cloud Console OAuth client created + APIs enabled (client_id `96227025012-…`, verified live via gmail.etzhayyim.com)
- [x] CF secrets stored (`google_oauth_client_id`, `google_oauth_client_secret`, `gworkspace_token_kek`) — store id `1824561668fe47cc9127d493961885af`
- [x] **Schema migration `20260417140000_vertex_google_workspace_tables` applied 2026-04-17** — 41 tables (33 vertex + 8 edge). Applied out-of-band via `30-graph/graph-schema/scripts/run-one-migration.mjs` (kysely migrator blocked by pre-existing drift). `kysely_migration` row inserted + `FLUSH`. Migration file fix: JSDoc `vertex_*/edge_*` → `vertex_ / edge_` (the `*/` was terminating the block comment early, causing TS1109)
- [ ] 7 D1 dbs created (`calendar/drive/contacts/tasks/docs/sheets/slides-tokens`) + IDs pasted into 7 `wrangler.jsonc` files (gmail = `gm4il0x1` done)
- [ ] Remaining redirect URIs added to GCP Console (only `gmail.etzhayyim.com` registered; `calendar/drive/…/meet.etzhayyim.com` TODO)
- [ ] Drive worker initial `etzhayyim deploy` / `wrangler deploy` (currently `drive.etzhayyim.com` returns `UnknownActor`)
- [ ] `pnpm db:gen` + `pnpm db:drift` clean (regenerate `database.ts` now that 41 new tables exist)
- [ ] All 9 apps deploy clean (`etzhayyim deploy` per dir)
- [ ] First account OAuth round-trip verified end-to-end (in progress — `jun@etzhayyim.com` Gmail consent pending)
- [ ] Per-service `syncFromGoogle()` body implemented (currently TODO stub for non-calendar/non-gmail)
