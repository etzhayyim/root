# Natural Person App — Arrow Schema + Flight SQL + Matrix Protocol Design

## Component

```
60-apps/ai-gftd-project-resources/wasm/ai-gftd-wasm-natural-person-np7k2m9x/
├── main.go              # HTTP handlers, performer runtime, Matrix command dispatch
├── db_schema.go         # Arrow table schemas (nata.TableSchema)
├── db_persons.go        # natural_persons_current / _events table CRUD
├── db_analytics.go      # analytical projection tables + Flight SQL queries
├── matrix_commands.go   # Matrix event handlers (org.gftd.command.natural-person.*)
├── magatama.toml
├── App manifest
└── wit/world.wit        # imports gftd:natural-person/natural-person (consumer)
```

Nanoid: `np7k2m9x`
Subdomain: `np7k2m9x.gftd.ai`

## Arrow Schema Design

### Table: `natural_persons_events` (append-only event log)

| Column | Arrow Type | Description |
|---|---|---|
| `org_id` | String | RLS tenant key (sort key prefix) |
| `user_id` | String | RLS caller |
| `actor_id` | String | Operation executor |
| `event_id` | String | `_doc_id`, nanoid |
| `person_id` | String | Natural person entity ID |
| `event_type` | String | `created`, `updated`, `deleted`, `id_doc_added`, `id_doc_removed`, `contact_linked`, `contact_unlinked`, `clerk_synced`, `status_changed` |
| `payload_json` | String | Event payload (JSON-serialized delta) |
| `event_at` | String | ISO 8601 timestamp |

設計意図: 全変更を append で記録。分析・監査用。

### Table: `natural_persons_current` (merge-insert projection)

| Column | Arrow Type | Description |
|---|---|---|
| `org_id` | String | RLS sort key prefix |
| `user_id` | String | RLS |
| `actor_id` | String | RLS |
| `person_id` | String | `_doc_id`, primary key |
| `family_name` | String | 姓 |
| `given_name` | String | 名 |
| `family_name_reading` | String | 姓ふりがな |
| `given_name_reading` | String | 名ふりがな |
| `middle_name` | String | |
| `display_name` | String | 表示名 override |
| `birth_date` | String | ISO 8601 |
| `death_date` | String | ISO 8601 |
| `gender` | String | `not-known`, `male`, `female`, `non-binary`, `not-applicable` |
| `nationality` | String | ISO 3166-1 alpha-2 |
| `status` | String | `active`, `inactive`, `deceased`, `merged` |
| `clerk_user_id` | String | Linked Clerk user ID |
| `id_documents_json` | String | JSON array of id-document records |
| `contacts_json` | String | JSON array of contact-link records |
| `families_json` | String | JSON array of family-relation records |
| `person_type_ids_json` | String | JSON array of person type IDs |
| `created_at` | String | ISO 8601 |
| `updated_at` | String | ISO 8601 |

Write path: `UpsertOne("natural_persons_current", person_id, row)`
Read path: `Query` / `QueryOrdered` / `QuerySQL` via nata/client DataFrame API

### Table: `natural_persons_analytics` (analytical projection)

| Column | Arrow Type | Description |
|---|---|---|
| `org_id` | String | RLS |
| `user_id` | String | RLS |
| `actor_id` | String | RLS |
| `person_id` | String | `_doc_id` |
| `gender` | String | Denormalized for filter |
| `nationality` | String | Denormalized for filter |
| `status` | String | Denormalized for filter |
| `birth_year` | Int64 | Extracted from birth_date for cohort analysis |
| `age_bucket` | String | `0-17`, `18-29`, `30-39`, `40-49`, `50-59`, `60-69`, `70+` |
| `person_type_ids_json` | String | For type-based aggregation |
| `family_count` | Int64 | Number of linked families |
| `contact_count` | Int64 | Number of linked contacts |
| `id_doc_count` | Int64 | Number of identity documents |
| `has_clerk_link` | Int64 | 1 if clerk_user_id is set, 0 otherwise |
| `kyc_verified` | Int64 | 1 if any id_document.verified=true |
| `created_at` | String | |
| `updated_at` | String | |

設計意図: Flight SQL DataFrame query で高速集計するための projection。`natural_persons_current` 更新時に同時に merge-insert。JSON nested filter を避け、flat column で集計。

## Transport Design (Command=Matrix, Query=XRPC)

### Matrix Command Events

| Event Type | Description | Payload |
|---|---|---|
| `org.gftd.command.natural-person.create` | 新規自然人登録 | `CreatePersonRequest` JSON |
| `org.gftd.command.natural-person.update` | 更新 | `UpdatePersonRequest` JSON |
| `org.gftd.command.natural-person.delete` | 削除 (soft) | `{ "id": "..." }` |
| `org.gftd.command.natural-person.upsert-id-doc` | 本人確認書類追加 | `UpsertIdDocumentRequest` JSON |
| `org.gftd.command.natural-person.remove-id-doc` | 本人確認書類削除 | `RemoveIdDocumentRequest` JSON |
| `org.gftd.command.natural-person.link-contact` | 連絡先紐付け | `LinkContactRequest` JSON |
| `org.gftd.command.natural-person.unlink-contact` | 連絡先解除 | `UnlinkContactRequest` JSON |
| `org.gftd.command.natural-person.sync-clerk` | Clerk user 同期 | `{ "org_id": "..." }` |
| `org.gftd.command.natural-person.collect` | データ収集開始 | `CollectRequest` JSON |
| `org.gftd.command.natural-person.analyze` | 分析実行 | `AnalyzeRequest` JSON |

Matrix room: `#natural-person-commands:gftd.ai` (app-owned room)
Application Service: `np7k2m9x` が user provision + room membership を管理

### XRPC Query Surface

```
POST /xrpc/gftd.natural_person.v1.NaturalPersonQueryService/GetPerson
POST /xrpc/gftd.natural_person.v1.NaturalPersonQueryService/ListPersons
POST /xrpc/gftd.natural_person.v1.NaturalPersonQueryService/SearchPersons
POST /xrpc/gftd.natural_person.v1.NaturalPersonQueryService/GetAnalyticsSummary
POST /xrpc/gftd.natural_person.v1.NaturalPersonQueryService/GetDemographics
POST /xrpc/gftd.natural_person.v1.NaturalPersonQueryService/GetKYCStatus
POST /xrpc/gftd.natural_person.v1.NaturalPersonQueryService/GetFamilyRelations
```

### Flight SQL Analytical Queries

nata/client DataFrame API 経由で `natural_persons_analytics` テーブルに対して実行:

```go
// Demographics breakdown
db.QuerySQL("natural_persons_analytics",
    "SELECT gender, nationality, age_bucket, COUNT(*) as cnt "+
    "FROM natural_persons_analytics "+
    "WHERE org_id = ? GROUP BY gender, nationality, age_bucket")

// KYC verification status
db.QuerySQL("natural_persons_analytics",
    "SELECT kyc_verified, COUNT(*) as cnt "+
    "FROM natural_persons_analytics "+
    "WHERE org_id = ? GROUP BY kyc_verified")

// Cohort analysis by birth year
db.QueryOrdered("natural_persons_analytics",
    "org_id = '"+orgID+"'", "birth_year ASC", limit, offset)
```

## Data Collection (Matrix Command Flow)

```
Human/Agent → Matrix CS API
  → org.gftd.command.natural-person.collect
    → App command handler
      → Workflow: collect-natural-persons
        → Activity: fetch-clerk-directory    → Clerk API → person records
        → Activity: fetch-external-registry  → 外部 registry → normalized records
        → Activity: deduplicate-merge        → merge-insert into current + analytics
        → Activity: emit-events              → append to events table
      → Matrix response event: org.gftd.command.natural-person.collect.result
```

### CollectRequest

```json
{
  "sources": ["clerk", "external-registry"],
  "org_id": "org_xxx",
  "filters": {
    "nationality": "JP",
    "status": "active"
  },
  "dry_run": false
}
```

### AnalyzeRequest

```json
{
  "org_id": "org_xxx",
  "dimensions": ["gender", "nationality", "age_bucket", "kyc_verified"],
  "filters": {
    "status": "active"
  }
}
```

## Runtime Architecture

```
performer.Runtime (np7k2m9x)
├── Matrix ingress
│   ├── org.gftd.command.natural-person.* → command handlers
│   └── response events → Matrix room/thread
├── XRPC (query-only)
│   └── /xrpc/gftd.natural_person.v1.NaturalPersonQueryService/*
├── natad/LanceDB
│   ├── natural_persons_events    (append)
│   ├── natural_persons_current   (merge-insert, key=person_id)
│   └── natural_persons_analytics (merge-insert, key=person_id)
├── Workflow
│   ├── collect-natural-persons   (Clerk sync + external registry)
│   └── analyze-natural-persons   (aggregate + report)
└── Reminder
    └── periodic-sync (1h) → sync-clerk-users
```

## WIT World (consumer)

```wit
// wit/world.wit
package gftd:natural-person-app@0.1.0;

world natural-person-app {
  include gftd:platform/gftd-mcp@0.1.0;

  // wRPC import: read/write natural persons via provider
  import gftd:natural-person/natural-person@0.1.0;

  // wRPC import: family relations
  import gftd:family/family@0.1.0;
}
```

## App Manifest (magatama.toml)

```toml
manifest_version = 2

[application]
name = "natural-person-np7k2m9x"
version = "0.1.0"

[[trigger.http]]
component = "natural-person-np7k2m9x"
route = "/health"

[[trigger.http]]
component = "natural-person-np7k2m9x"
route = "/healthz"

[[trigger.http]]
component = "natural-person-np7k2m9x"
route = "/xrpc/gftd.natural_person.v1.NaturalPersonQueryService/..."

[[trigger.http]]
component = "natural-person-np7k2m9x"
route = "/api/info"

[[trigger.http]]
component = "natural-person-np7k2m9x"
route = "/_matrix/..."

[component."natural-person-np7k2m9x"]
source = "build/natural_person_np7k2m9x_s.wasm"
allowed_outbound_hosts = ["http://*:*", "https://*:*"]

[component."natural-person-np7k2m9x".build]
command = "tinygo build -target=wasip1 -gc=leaking -buildmode=c-shared -no-debug -o build/natural_person_np7k2m9x_s.wasm ."

[[trigger.http]]
route = "/..."
component = "fileserver"

[component.fileserver]
source = { url = "static delivery release artifact", digest = "sha256:ef88708817e107bf49985c7cefe4dd1f199bf26f6727819183571b90f543e420" }
files = [{ source = "svelte/build/", destination = "/" }]
environment = { FALLBACK_PATH = "index.html" }
```

## K8s App

```yaml
apiVersion: core.magatama-runtime.dev/v1alpha1
kind: App
metadata:
  name: np7k2m9x-magatama
  namespace: magatama-runtime
  annotations:
    performer.gftd.ai/subdomains: "np7k2m9x"
  labels:
    app.kubernetes.io/name: np7k2m9x-magatama
spec:
  image: ghcr.io/gftdcojp/natural-person-np7k2m9x:v0.1.0
  replicas: 1
  executor: containerd-shim-magatama
  enableAutoscaling: false
  imagePullSecrets:
    - name: ghcr-pull-secret
```

## Implementation Order

1. `db_schema.go` — Arrow table schemas (`natural_persons_events`, `natural_persons_current`, `natural_persons_analytics`)
2. `db_persons.go` — CRUD via nata/client (UpsertOne, Query, QueryOrdered, Delete)
3. `db_analytics.go` — Analytics projection update + Flight SQL query helpers (QuerySQL)
4. `main.go` — performer.Runtime + Adapter + ContextRoutes + actor integration
5. `matrix_commands.go` — Matrix event type dispatch (org.gftd.command.natural-person.*)
6. `wit/world.wit` — Consumer world importing gftd:natural-person + gftd:family
7. `magatama.toml` + `deploy config`
8. Deploy: `gftd build` → `gftd push` → `kubectl apply`
