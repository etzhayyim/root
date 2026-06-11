# open-cofog.etzhayyim.com — UN COFOG (Classification of the Functions of Government) (OSS)

**Status**: MVP scaffold (2026-04-20). Companion to `open-isic` — read-only
DID-addressed lookup of UN Statistics Division's COFOG classification.
Apache-2.0.

## OSS mirror pattern (mirrors `open-isic`)

> 1 Worker, 1 primary DID. No D1 — pure static taxonomy + per-class JSON
> loaded at build time. Classes grow **one per cron iteration** the same way
> `open-isic` does.

- **Route**: `open-cofog.etzhayyim.com/*` (1 Worker, `did:web:open-cofog.etzhayyim.com`)
- **Impl**: `worker/src/app.ts` (single file, no DB)
- **Class addition unit**: 1 PR = `data/classes/{4digit}.json` + 1 line in
  `worker/src/classes-index.ts` = 1 cron iteration
- **Progress**: `IMPLEMENTED_COUNT / TOTAL_CLASSES` in `classes-index.ts`
- **XRPC**:
  - `com.etzhayyim.apps.openCofog.listDivisions`
  - `com.etzhayyim.apps.openCofog.listGroups`
  - `com.etzhayyim.apps.openCofog.listClasses`
  - `com.etzhayyim.apps.openCofog.getClass`
- **OSS repo**: `github.com/etzhayyim/etzhayyim-project-open-cofog` (Apache-2.0)
- **Cron**: `*/10 * * * *` for class-by-class implementation (`loop` session)

## COFOG hierarchy

UN COFOG (1999, last update 2014). 3-level taxonomy:

| Level | Count | Code format | DID form | Example |
|---|---|---|---|---|
| **Division** | **10** | 2-digit (`01`–`10`) | `did:web:open-cofog.etzhayyim.com:division:01` | 01 General public services |
| **Group** | **~65** | 3-digit (`011`, `021`, …) | `did:web:open-cofog.etzhayyim.com:group:011` | 011 Executive and legislative organs |
| **Class** | **96** (this monorepo) | 4-digit (`0111`, `0210`, …) | `did:web:open-cofog.etzhayyim.com:class:0111` | 0111 Executive and legislative organs |

Code packing: `{division XX}{group Y}{class Z}` → 4-digit `XXYZ`. Group code
= first 3 digits of class code; division code = first 2 digits of class code.

### 10 Divisions

| Code | Name |
|---|---|
| 01 | General public services |
| 02 | Defence |
| 03 | Public order and safety |
| 04 | Economic affairs |
| 05 | Environmental protection |
| 06 | Housing and community amenities |
| 07 | Health |
| 08 | Recreation, culture and religion |
| 09 | Education |
| 10 | Social protection |

## Cross-project links

| Link | Use |
|---|---|
| `etzhayyim-project-cofog` | Per-class actor APP (96 actors). open-cofog provides the taxonomy lookup; `cofog` provides the live actors. |
| `etzhayyim-project-open-isic` | Section O (Public administration) ↔ COFOG division 01 — government activity classified two ways (statistical vs functional). |
| `etzhayyim-project-states` | Government organisations are tagged with the COFOG class(es) they fund / execute. |
| `etzhayyim-project-open-isco` | Civil-servant occupations (ISCO) by COFOG function. |

## Layout

```
data/classes/{4digit}.json       one file per 4-digit Class (authoritative data)
worker/src/taxonomy.ts           Division + Group skeleton (10 + ~65 entries)
worker/src/classes-index.ts      generated import index + IMPLEMENTED_COUNT
worker/src/app.ts                XRPC router (single file, no DB)
worker/kotodama.jsonld           profile + space + triggers
worker/wrangler.jsonc            CF Worker config (no D1)
```

## Class JSON shape

```json
{
  "code": "0111",
  "nameEn": "Executive and legislative organs",
  "group": "011",
  "description": "Administration, operation or support of...",
  "includes": ["..."],
  "excludes": ["...; see 0xxx"],
  "implementedAt": "2026-04-20T00:00:00Z"
}
```

## Local dev / deploy

```bash
cd 60-apps/etzhayyim-project-open-cofog/worker
wrangler dev --local                  # static, no D1 binding
e7m actor deploy .   # standard monorepo deploy
```
