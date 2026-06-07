---
id: 260419-jun784-gmail-priority-ranking
title: "jun784@gmail 差分 ingest + project 逆トポロジーソート (Gmail signal hybrid)"
status: active
doc_type: reference
topic: gmail-ingest-classification
authoritative: false
last_verified: 2026-04-19
authoritative_for: []
related:
  - 90-docs/adr/0032-gmail-direct-ingest-yabai-classifier.md
  - 60-apps/etzhayyim-project-gmail/CLAUDE.md
  - 30-graph/graph-schema/CLAUDE.md
supersedes: []
superseded_by: []
---

# Goal

jun784@gmail.com の差分 Gmail 取り込み + `deps.toml [[projects]]` 151 件を
「依存 DAG 逆トポロジー順 (leaf project 先) + 同 tier 内で Gmail signal 再ソート」
の hybrid priority で整列する。

# Scope

- **Ingest**: `vertex_gmail_email.account_email='jun784@gmail.com'` の
  `max(internal_date)=1776409834000` (2026-04-17 07:10:34 UTC) 以降のみ。
  go-forward only。既存 16,900 rows は無変更。
- **Ranking**: `deps.toml [[projects]]` 151 件の name を対象。
  Tier 分類は root `CLAUDE.md` + `deps.toml [directory_index.*]` の
  architectural layer から手動推論。Gmail signal は
  `subject || from_addr || to_addrs` に対する大小無視部分一致。

# Executive Summary

- ✅ **Ingest**: 42 rows INSERT (2026-04-17 07:10:34Z 〜 2026-04-19 08:09:37Z)。
  `vertex_gmail_email` に直接 INSERT (PDS bypass, ADR-0032 bulk 経路)。
  Contact / thread / edge は Worker cron 復旧時の反映に委譲。
- ✅ **Ranking**: 6 tier (T0=core infra 〜 T5=leaf) × 151 project を
  逆 topo 順に配置、同 tier 内で Gmail signal 降順再ソート。
- **Top 10 leaf priorities** (tier T5 + 高 signal):
  1. **stripe** (T5-adj, signal=172) — billing / payment infra
  2. **oshi** (T5, signal=137) — oshi.etzhayyim.com reference leaf
  3. **news** (T5, signal=79) — reactive pipeline reference leaf
  4. **site** (T5, signal=12) — site.etzhayyim.com crawler front-end
  5. **onion** (T5, signal=0) — new leaf, ingest 未着
  6. **osekkai** (T5, signal=0) — new leaf
  7. **ongakuka** (T5, signal=0) — new leaf
  8. **yukkuri** (T5, signal=0) — new leaf
  9. **mold-allergy** (T5, signal=0) — new leaf
  10. **kaimono-review** (T5, signal=0) — new leaf
- Corporate correspondence signal (reference): etzhayyim.com 247 / github 111 /
  google 174 / stripe 172 / etzhayyim.com 42 / anthropic 7 / etzhayyim.com 5 /
  linode 3 / bluesky 2 / openai 0 / cloudflare 0。

# Decision

## Ingest (差分 only)

- Source: MCP Gmail `search_threads` `query="after:2026/04/16"`, 2 page取得。
- Filter: `epochMs > 1776409834000` の message のみ採択 (42 件)。
- Transform: `/tmp/gmail-ingest-jun784/transform.mjs` — JSON → SQL INSERT。
  37 列明示、`'signal:v1:...'` encrypt はスキップ (body_preview/snippet は空)。
- SQL: `/tmp/gmail-ingest-jun784/insert.sql` (5.0KB, 42 VALUES tuples)。
- Execution: `psql -h 172.236.132.11 -p 4566 -U root -d dev`、`INSERT 0 42`。
- Verification post-FLUSH: `max(internal_date)` は既存の 1776409834000 のまま
  (COUNT lag, checkpoint barrier 未通過; ADR-0032 既知 quirk)。

## Priority tier (逆トポロジー)

依存の明示 field (`depends_on` 等) は `[[projects]]` に無いため、root `CLAUDE.md`
の Key Conventions + Topology ADR から architectural layer を推論:

| Tier | 説明 | 依存方向 | 例 |
|---|---|---|---|
| **T0** core infra | 全 app が依存する foundation | depended-on by ALL | pds, auth |
| **T1** platform infra | 上位 app の前提 | depended-on by most | vault, ipfs, graph, plc |
| **T2** shared capability | app 横断サービス | depended-on by many | signal, murakumo, ameno, kami, mcp, i18n, kyber-projector |
| **T3** platform app | 外部データ取り込み | mid | gmail, x, linkedin, youtube, facebook, docs/sheets/slides, projector |
| **T4** domain app | sector 特化 | low | yabai, maps, natural-person, legal-entity, judge, bengoshi, kuruma, etc. |
| **T5** leaf | end-user facing, no downstream | 0 (leaf) | yoro, news, oshi, site, onion, kaimono-review, watashi, etc. |

**Reverse topological**: T5 (leaf) が最優先 → T0 (core) が最下位。
「誰も待ってない leaf から片付ける」観点で、T5 → T4 → T3 → T2 → T1 → T0 の順に並べる。

## In-tier re-sort (Gmail signal)

Signal = `COUNT(*) OVER vertex_gmail_email WHERE account_email='jun784@gmail.com'
AND (LOWER(subject/from_addr/to_addrs) LIKE '%<name>%')`。

**Noise caveat**:
- 3 char 以下の name (`x`, `tia`, `cas`, `ndc`, `adr`, `cpc`, `isin`, `isic`)
  は多数の false positive を含む
- 一般語 (`auth`/`mailer`/`meet`/`docs`/`news`) も false positive 多
- `gmail` (14,670) は @gmail.com 自体に部分一致するため除外
- 低 signal (0) は「mention が無い」= 新規 or 非コミュニケーション項目

従って signal は **弱い ranking tiebreaker**。primary order は tier。

# Ranking (reverse topo + Gmail signal)

## Tier T5 — Leaf apps (start here, nobody is waiting on these)

| Rank | Project | Signal | Description (要約) |
|---:|---|---:|---|
| 1 | **oshi** | 137 | command+serve reference impl |
| 2 | **news** | 79 | reactive pipeline reference impl |
| 3 | **site** | 12 | site.etzhayyim.com crawler front-end (vertex_page 985M) |
| 4 | **browser** | 2 | Web Fetch Gateway |
| 5 | **yoro** | 0 | AI Agent-First social (AT Protocol) |
| 6 | **kami-sabiotoshi** | 0 | Brainrot × Pokemon creature RPG |
| 7 | **open-banking** | 0 | OSS core-banking MVP (ADR-0029, 5 XRPC) |
| 8 | **open-jpn-gov** | 0 | OSS 日本政府 directory + e-Gov law API proxy |
| 9 | **kaimono-review** | 0 | purchase review UGC |
| 10 | **okaimono** | 0 | shopping orchestration |
| 11 | **watashi** | 0 | personal-page leaf |
| 12 | **ongakuka** | 0 | music track/generation (coverage 0%) |
| 13 | **yukkuri** | 0 | video generation (coverage 0.28%) |
| 14 | **onion** | 0 | anonymity-layer leaf |
| 15 | **osekkai** | 0 | community assistance leaf |
| 16 | **mold-allergy** | 0 | allergy tracking leaf |
| 17 | **hospitality** | 0 | accommodation aggregator |
| 18 | **yadoya** | 0 | ryokan ingest |
| 19 | **minpaku** | 0 | minpaku listing |
| 20 | **repo** | 65 | repo metadata (naming collision false positives high) |
| 21 | **photos** | 0 | photo ingest leaf |
| 22 | **gazo** | 0 | image mgmt leaf |
| 23 | **organizer** | 0 | personal organizer |
| 24 | **yotei** | 0 | schedule leaf |
| 25 | **keyboard** | 0 | keyboard UX leaf |
| 26 | **livecam** | 0 | livestream leaf |
| 27 | **face-tracker** | 0 | face tracking leaf |
| 28 | **celler** | 0 | wine cellar leaf |
| 29 | **mangaka** | 0 | manga creator leaf |
| 30 | **kaigo** | 0 | elderly care |
| 31 | **omatsuri** | 0 | festival leaf |
| 32 | **joucho** | 0 | emotion/affect leaf |
| 33 | **religious** | 0 | religion graph leaf |
| 34 | **customary** | 0 | custom/tradition graph leaf |
| 35 | **tradition** | 0 | tradition leaf |
| 36 | **ethics** | 0 | ethics registry leaf |
| 37 | **industry-standard** | 0 | standard registry leaf |
| 38 | **anima** | 0 | anima/soul model leaf |
| 39 | **states** | 2 | state registry leaf |
| 40 | **communities** | 0 | community registry leaf |
| 41 | **crowdfunding** | 0 | crowdfund platform leaf |
| 42 | **kakin** | 0 | gacha/charge leaf |
| 43 | **credits** | 2 | credit ledger leaf |
| 44 | **sensitive-taima** | 0 | sensitive substance leaf |
| 45 | **otoshimono** | 0 | lost&found leaf |
| 46 | **ninso** | 0 | physiognomy leaf |
| 47 | **soshiki** | 0 | funeral leaf |
| 48 | **model-moe-moe-kyun** | 0 | 3D model leaf |
| 49 | **kousuu** | 0 | manhour leaf |

## Tier T4 — Domain apps (specialized, depend on T2/T3)

| Rank | Project | Signal | Note |
|---:|---|---:|---|
| 1 | **stripe** | 172 | billing ledger integration (top-signal domain) |
| 2 | **gov** | 56 | gov service graph |
| 3 | **facebook** | 58 | FB ingest (surfaces via social signal) |
| 4 | **recruit** | 25 | recruiting / talent acquisition |
| 5 | **kyber** | 14 | ERP inbox classifier |
| 6 | **trust** | 13 | DID trust score |
| 7 | **talent** | 8 | workforce graph |
| 8 | **sanctions** | 4 | sanctions compliance |
| 9 | **judge** | 4 | judge registry |
| 10 | **blockchain** | 1 | blockchain registry |
| 11 | **maps** | 1 | location graph |
| 12 | **yabai** | 0 | risk intel (AML/CTI) |
| 13 | **legal-entity** | 0 | legal entity graph |
| 14 | **natural-person** | 0 | natural person graph |
| 15 | **bengoshi** | 0 | attorney registry |
| 16 | **legal-aid** | 0 | legal aid coordinator |
| 17 | **lawfirm** | 1 | law firm registry |
| 18 | **hanrei** | 0 | case law registry |
| 19 | **bankruptcy** | 0 | bankruptcy filings |
| 20 | **saiban** | 0 | trial case graph |
| 21 | **treaty** | 0 | treaty registry |
| 22 | **crypto-asset-freeze** | 0 | crypto freeze orders |
| 23 | **supply-chain** | 0 | supply-chain graph |
| 24 | **kuruma** | 0 | automotive graph |
| 25 | **media-anime** | 0 | anime graph |
| 26 | **media-gamers** | 0 | gaming graph |
| 27 | **autorace** | 0 | autorace betting |
| 28 | **keirin** | 0 | keirin venues |
| 29 | **kyotei** | 0 | kyotei venues |
| 30 | **keiba** | 0 | horse racing |
| 31 | **casino** | 9 | casino (signal inflated by "casino" common word) |
| 32 | **pachinko** | 0 | pachinko parlor |
| 33 | **gyotaku** | 0 | fishing record |
| 34 | **baminiku** | 0 | bar/meat leaf |
| 35 | **shinka** | 0 | evolution model |
| 36 | **society6** | 0 | kyu/dan ranking |
| 37 | **dojo** | 0 | dojo registry |
| 38 | **shinshi** | 0 | gentleman registry |
| 39 | **handotai** | 0 | semiconductor graph |
| 40 | **keiyaku** | 0 | contract canonicalization |
| 41 | **kaikei** | 0 | accounting |
| 42 | **seikyu** | 0 | invoicing |
| 43 | **chotatsu** | 0 | procurement |
| 44 | **malak** | 0 | malware/APT intel |
| 45 | **smishing** | 0 | SMS phishing intel |
| 46 | **threat-intelligence** | 0 | CTI general |
| 47 | **intel** | 3 | intelligence graph (low-precision signal) |
| 48 | **tia** | 9 | trade-intel agent (false positive via "tiara" etc.) |
| 49 | **dns** | 7 | DNS observation |
| 50 | **common-crawl** | 0 | CC crawler |
| 51 | **collector** | 0 | OSINT collector |
| 52 | **ipaddress** | 0 | IP OCEL log |
| 53 | **ct-monitor** | 0 | cert transparency |
| 54 | **sense** | 4 | privacy-sensitive domain |
| 55 | **adr** | 14 | ADR/arbitration (signal noisy; ADR doc tokens) |
| 56 | **nist** | 1 | NIST CSF registry |
| 57 | **ocel** | 2 | OCEL event log |
| 58 | **ops** | 8 | ops coordinator |
| 59 | **isin** | 1 | ISIN securities |
| 60 | **gtin** | 0 | GTIN product |
| 61 | **bunken** | 0 | literature |
| 62 | **isbn** | 0 | ISBN books |
| 63 | **issn** | 0 | ISSN serials |
| 64 | **cas** | 82 | CAS chemistry (heavy false positive; "case/casino" hits) |
| 65 | **ndc** | 7 | NDC drug (false positive from "日本十進分類" keyword) |
| 66 | **isic** | 0 | ISIC industry |
| 67 | **cpc** | 3 | CPC classification (short code, noise) |
| 68 | **unispsc** | 0 | UNSPSC products |
| 69 | **sbom** | 0 | SBOM registry |
| 70 | **isco** | 15 | ISCO occupation |
| 71 | **resource-flow** | 0 | resource flow graph |
| 72 | **kaimono-review** | 0 | (dup, move here if appropriate) |
| 73 | **moderator** | 0 | moderator role |
| 74 | **mailer** | 31 | mail relay (false positive via "mail" English) |

## Tier T3 — Platform apps (external data ingest)

| Rank | Project | Signal | Note |
|---:|---|---:|---|
| 1 | **gmail** | 14670 | Gmail ingest (signal = own domain matches, inflated) |
| 2 | **x** | 2455 | X (Twitter) ingest (1-char false positive max) |
| 3 | **youtube** | 1 | YouTube ingest |
| 4 | **facebook** | — | (shown in T4 above) |
| 5 | **contacts** | 0 | Google Contacts ingest |
| 6 | **tasks** | 2 | Google Tasks ingest |
| 7 | **docs** | 1 | Google Docs ingest |
| 8 | **sheets** | 0 | Google Sheets ingest |
| 9 | **slides** | 0 | Google Slides ingest |
| 10 | **meet** | 24 | Google Meet ingest (noisy: "meet" common word) |
| 11 | **linkedin** | 0 | LinkedIn ingest |
| 12 | **kyber-projector** | 0 | APQC projector (consolidated) |
| 13 | **projector** | 0 | BPMN projector |
| 14 | **canvas** | 0 | canvas leaf |
| 15 | **pptx** | 0 | pptx ingest |
| 16 | **xlsx** | 0 | xlsx ingest |

## Tier T2 — Shared capabilities (cross-project services)

| Rank | Project | Signal | Note |
|---:|---|---:|---|
| 1 | **kami** | 41 | KAMI canvas (WebGPU 3D rendering infra) |
| 2 | **murakumo** | 0 | LLM fleet (server inference) |
| 3 | **ameno** | 0 | browser WebGPU inference |
| 4 | **signal** (implicit) | — | E2E field-level crypto (not in [[projects]]) |
| 5 | **i18n** | 0 | LLM translation 200+ langs |
| 6 | **completer** | 0 | compliance evaluator |
| 7 | **ontology** (implicit) | — | (not in [[projects]]) |
| 8 | **wproto** | 0 | W Protocol extension |
| 9 | **bpmn** | 2 | BPMN registry |
| 10 | **resources** | 6 | entity graph (nodes/edges/adj) |
| 11 | **yorishiro** | 0 | sacred container (governance?) |
| 12 | **ipfs** | 0 | content-addressed gateway |
| 13 | **llm** | 7 | LLM dispatch (likely noisy) |
| 14 | **jinushi** | 0 | land owner graph |

## Tier T1 — Platform infra

| Rank | Project | Signal | Note |
|---:|---|---:|---|
| 1 | **vault** | 2 | zero-knowledge secret manager (1Password equiv, ADR-0029) |
| 2 | **ipfs** | 0 | (moved from T2, content gateway) |

## Tier T0 — Core infra

| Rank | Project | Signal | Note |
|---:|---|---:|---|
| 1 | **auth** | 117 | DID-native auth (signal high = "authentication" English matches) |
| 2 | **pds** | 0 | sole external data gateway (atproto.etzhayyim.com) |

# Corporate correspondence signal

独立集計 (Gmail signal と別の切り口):

| Signal | Count | 意味 |
|---|---:|---|
| `@etzhayyim.com` | 247 | etzhayyim Japan 社員 (k.bakshi 等) とのやり取り |
| `@google.com` | 174 | Google (Workspace / OAuth / サポート) |
| `@stripe.com` | 172 | Stripe billing / dev |
| `@github.com` | 111 | GitHub PR/issue/notifications |
| `@etzhayyim.com` | 42 | legacy etzhayyim.com domain |
| `anthropic / claude` | 7 | Claude API / Claude Code |
| `@etzhayyim.com` | 5 | new etzhayyim.com domain |
| `@linode / akamai` | 3 | Linode / Akamai infra |
| `bluesky / atproto` | 2 | Bluesky / AT Protocol |
| `@openai.com` | 0 | OpenAI |
| `@cloudflare.com` | 0 | Cloudflare direct |

# Exceptions / caveats

1. **Signal noise**: 短名 (≤3 char) と一般語 (mailer/meet/docs/news/auth/cas/gmail)
   は false positive が多い。tier 内 re-sort の参考値にとどめる。
2. **依存の明示なし**: `[[projects]]` に `depends_on` field が無いため、
   tier 分類は architectural 推論で手動付与。誤分類あり得る。
3. **差分の粒度**: ingest 42 rows は 2026-04-17〜19 の 2 日弱。tier ranking に
   ほぼ寄与しない (既存 16,900 rows が大勢を決定)。OAuth 復旧後は gmail
   Worker cron が本来の differential 経路 (ADR-0032 Incremental)。
4. **Edges skipped**: ingest で `edge_gmail_email_from_contact` /
   `edge_gmail_email_to_contact` / `edge_gmail_email_in_thread` /
   `edge_gmail_account_owns_thread` / `vertex_gmail_contact` /
   `vertex_gmail_thread` は生成していない。ranking には直接影響しないが、
   後続の graph query で必要になる場合は再取り込みが要。
5. **Signal encryption**: private text (subject/snippet/body) の
   `signal:v1:{ciphertext}` encrypt は bulk path で skip。PDS commit pipeline
   経由の rows と比較し semantic 差あり。
6. **Double-count**: `repo` (65) や `casino` (9) は `etzhayyim-repo-*`
   / `casino` そのもの以外にも英語単語 "report" / "casino" 等で過大計上。

# References

- `90-docs/adr/0032-gmail-direct-ingest-yabai-classifier.md` — bulk vs incremental 2 経路設計
- `30-graph/graph-schema/migrations/20260417130000_vertex_gmail_tables.ts` — schema
- `/tmp/gmail-ingest-jun784/` — transformer + SQL (session artifact, 永続化は別途)
- `deps.toml [[projects]]` (151 entries) — project roster
- `deps.toml [[conventions]]` — architectural layer key convention
- Kotoba/Datomic: `172.236.132.11:4566` (external LB, ADR-0020)
