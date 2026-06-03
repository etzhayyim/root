# etzhayyim-project-trademark — Trademark Registry

> **T1 Logical Actor**: Manifest-driven (`20-actors/trademark/actor-manifest.jsonld`). No Worker deploy — PDS Shared Executor runs 5 pipelines (get/list/madrid.members/coverage/cron) against `vertex_trademark` + `edge_owned_by` + `edge_classified_as` (migration 0037).

`trademark.etzhayyim.com` (nanoid: `tm4rk001`) — 商標登録 coverage actor。JPO / USPTO (TESS/TSDR) / EUIPO / WIPO Madrid を 2 次ソースとして統合。

## Role

trademark = **標章 (商標・サービスマーク・団体商標) perspective**。出願・公告・登録・更新・Madrid 国際登録を `com.etzhayyim.apps.trademark.*` に正規化し、権利者 (owner) を LEI / natural-person と相互リンク。

## Architecture

**1 Worker + N path-based DID per jurisdiction** (+ `:wo:madrid` for international):

| Level | DID | 用途 |
|---|---|---|
| Primary | `did:web:trademark.etzhayyim.com` | Coordinator, heartbeat |
| Jurisdiction | `did:web:trademark.etzhayyim.com:jp` / `:us` / `:eu` / `:wo` | 国/地域別 coverage |

## Lexicon (`com.etzhayyim.apps.trademark.*`)

| Collection | 用途 |
|---|---|
| `trademark` | 標章 record (primary: `{jurisdiction}-{regNumber}`) |
| `owner` | 権利者 (LegalEntity or NaturalPerson link) |
| `niceClass` | Nice Classification (45 class) |
| `viennaCode` | Vienna 図形分類 |
| `madridRegistration` | WIPO Madrid 国際登録 |
| `opposition` | 異議申立 |
| `coverageReport` | jurisdiction 毎 coverage |

## Cross-Links

```
(:Trademark {regNumber})
  -[:OWNED_BY]->(:LegalEntity {lei}) or -[:OWNED_BY]->(:NaturalPerson)
  -[:CLASSIFIED_AS {source:"nice"|"vienna"}]->(:NiceClass|:ViennaCode)
  -[:MADRID_LINKED]->(:MadridRegistration {intlRegNumber})
  -[:SIMILAR_TO]->(:Trademark)
```

## Data Sources (Follow-based)

| Source | 1 次 Worker |
|---|---|
| JPO 商標公報 | `webpage` |
| USPTO TESS / TSDR | `webpage` |
| EUIPO eSearch plus | `webpage` |
| WIPO Madrid Monitor | `webpage` |

## Component

| Component | nanoid |
|---|---|
| `etzhayyim-wasm-trademark-tm4rk001` | `tm4rk001` |
