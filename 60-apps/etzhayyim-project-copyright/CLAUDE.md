# etzhayyim-project-copyright — Copyright Registry

> **T1 Logical Actor**: Manifest-driven (`20-actors/copyright/actor-manifest.jsonld`). No Worker deploy — PDS Shared Executor runs 6 pipelines (resolve/list/license.inspect/coverage/orphanWorks.detect/cron) against `vertex_work` + `edge_authored_by` + `edge_owned_by` (migration 0037). Berne-aware: `berne_automatic=true` default when no registry specified.

`copyright.etzhayyim.com` (nanoid: `c0pyr1g7`) — 著作権 coverage actor。US Copyright Office / JASRAC / CISAC / Crossref (DOI) / ISBN / ORCID を 2 次ソースとして統合。

## Role

copyright = **著作物 (literary, musical, visual, software, audiovisual) perspective**。登録・ライセンス・DOI・ISBN を `com.etzhayyim.apps.copyright.*` に正規化。Berne Convention → 自動発生 / 登録任意の二層モデルを扱う。

## Architecture

**1 Worker + N path-based DID per registry** (jurisdiction + CMO):

| Level | DID | 用途 |
|---|---|---|
| Primary | `did:web:copyright.etzhayyim.com` | Coordinator |
| Registry | `did:web:copyright.etzhayyim.com:us-copyright` / `:jasrac` / `:crossref` / `:isbn` | registry 別 coverage |

## Lexicon (`com.etzhayyim.apps.copyright.*`)

| Collection | 用途 |
|---|---|
| `work` | 著作物 record (primary: `{registry}-{regId}` or `doi:{doi}` or `isbn:{isbn13}`) |
| `rightsHolder` | 権利者 (author / publisher / CMO) |
| `registration` | 登録 (US CO / JASRAC 等) |
| `license` | ライセンス (CC / commercial / CMO blanket) |
| `doi` | DOI (Crossref / DataCite / mEDRA) |
| `isbn` | ISBN-13 |
| `isrc` | ISRC (音源) |
| `iswc` | ISWC (楽曲) |
| `coverageReport` | registry 毎 coverage |

## Cross-Links

```
(:Work {id})
  -[:AUTHORED_BY]->(:NaturalPerson {orcid})
  -[:PUBLISHED_BY]->(:LegalEntity {lei})
  -[:REGISTERED_AT]->(:Registration {registry, regId})
  -[:LICENSED_UNDER]->(:License {spdxId|ccId|cmoId})
  -[:HAS_DOI]->(:Doi {doi})
  -[:HAS_ISBN]->(:Isbn {isbn13})
  -[:DERIVED_FROM]->(:Work)   // translation / adaptation
```

| 軸 | Source Project |
|---|---|
| author | `etzhayyim-project-natural-person` (ORCID) |
| publisher | `etzhayyim-project-legal-entity` (LEI) |
| 楽曲 metadata | `etzhayyim-project-music` (existing) |
| 書籍 metadata | `etzhayyim-project-book` (if exists) |

## Data Sources (Follow-based)

| Source | 1 次 Worker | 内容 |
|---|---|---|
| US Copyright Office | `webpage` | 登録 record |
| JASRAC | `webpage` | 日本楽曲管理 |
| CISAC IPI | `webpage` | 国際権利者 ID |
| Crossref | `webpage` | DOI (学術) |
| DataCite | `webpage` | DOI (研究データ) |
| ISBN Agency | `webpage` | 書籍 |
| ORCID | `webpage` | author ID |

## License Taxonomy

| Type | Enum | 例 |
|---|---|---|
| CC | `cc-by`, `cc-by-sa`, `cc-by-nc`, `cc0`, `cc-by-nd`, `cc-by-nc-sa`, `cc-by-nc-nd` | 7 variants |
| SPDX (software) | SPDX ID | `MIT`, `Apache-2.0`, `GPL-3.0` |
| CMO blanket | `jasrac-blanket`, `ascap-blanket`, `prs-blanket` | — |
| Commercial | `commercial-exclusive`, `commercial-non-exclusive` | — |
| Public Domain | `pd`, `pd-us`, `pd-life+70` | — |

## Component

| Component | nanoid |
|---|---|
| `etzhayyim-wasm-copyright-c0pyr1g7` | `c0pyr1g7` |
