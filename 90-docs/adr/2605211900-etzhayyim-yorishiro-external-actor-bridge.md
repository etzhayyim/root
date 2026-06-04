---
id: adr-2605211900-etzhayyim-yorishiro-external-actor-bridge
title: "ADR-2605211900: etzhayyim-yorishiro — 外部 app / webservice を Lexicon + Pregel cell + MCP server の 3-layer に自動 wrap し、agent 駆動可能な依代 (vessel) として substrate に組み込む generator"
status: proposed
doc_type: adr
topic: yorishiro-external-actor-bridge
authoritative: true
last_verified: 2026-05-21
priority: 6.0
axis: architecture
weight: 0.60
priority_note: "HKUDS/CLI-Anything (任意 software → Click CLI + JSON + REPL + SKILL.md で agent 駆動可) と等価な scaffolding を etzhayyim 側に持ち込む。ただし出力先は CLI ではなく etzhayyim-native な 3-layer (Lexicon SSoT + magatama Pregel cell + MCP server)。すでに `unispsc-isic-mcp` (ADR-2605180900 Phase 8) で 1 件 hand-written 実装済み — その pattern を generator template として正典化し、~130 個ある 60-apps/ + 任意の外部 webservice を同 pattern で量産可能にする。命名: 神道の依代 (kami が宿る vessel) の語に従い、外部 software = kami、生成された 3-layer artifact = yorishiro と定義。"
authoritative_for:
  - external app / webservice の magatama actor 化の 3-layer 出力契約
  - yorishiro generator CLI 仕様 (etzhayyim-cli yorishiro <name> --from <source>)
  - Lexicon 拡張フィールド (x-yorishiro-external / x-charter-purpose) の意味論
  - Charter purpose enforcement の lefthook hook 拡張点
depends_on:
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192115-etzhayyim-non-profit-donation-only-no-ads
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605180900-unispsc-isic-langserver-actor-lexicon-xrpc-mcp
  - adr-2605202200-etzhayyim-cell-runtime-contract
  - adr-2605172000-etzhayyim-rw-free-substrate
  - adr-2605172100-etzhayyim-payments-on-chain-only
related:
  - 20-actors/magatama/mcp/unispsc-isic-mcp/
  - 20-actors/magatama/cells/
  - 20-actors/magatama/py/src/pymagatama/primitives/
  - 00-contracts/lexicons/ai/etzhayyim/
  - 70-tools/etzhayyim-cli/
  - 70-tools/charter-rider-applicator/
  - https://github.com/HKUDS/CLI-Anything
supersedes: []
superseded_by: []
---

# ADR-2605211900: etzhayyim-yorishiro — external app/webservice → 3-layer vessel generator

**Status**: proposed
**Date**: 2026-05-21
**Deciders**: Jun Kawasaki

# Context

## 1. 観察された需要

`60-apps/` には現在 ~130 個の `etzhayyim-project-*` および religious-corp app があり、その多くは外部 vendor API (HuggingFace / arXiv / NDL / Sentinel / OpenStreetMap / Bluesky / OpenAlex / 各国 government open data など) や、ローカル software (LibreOffice / GIMP / Blender / ComfyUI / FFmpeg など) を駆動して religious-corp の mission (人類の構造的労働解放, ADR-2605192100) に資する成果物を produce する。

これらは現状すべて **hand-written** で:

1. app ごとに `src/app.ts` (CF Worker) または `pymagatama/primitives/*.py` (Pregel cell) を個別実装
2. Lexicon contract (`00-contracts/lexicons/com/etzhayyim/apps/*/` または `ai/etzhayyim/*/`) を手書き
3. MCP exposure は `20-actors/magatama/mcp/unispsc-isic-mcp/` (1 件のみ) を除き未整備

この hand-written-per-app 流儀は Shannon 冗長度が高く、Charter compliance (ADR-2605192200 §2 の 8 prohibited categories) の per-app 確認も人手依存で drift する。

## 2. 参照したい外部知見

HKUDS が公開した CLI-Anything (https://github.com/HKUDS/CLI-Anything) は、任意の software (source code accessible なもの) を **automated 7-phase pipeline** で agent-callable な Click CLI (`cli_anything.<name>` namespace + REPL + `--json` + SKILL.md) に変換する。設計上の鉄則:

> **"The CLI MUST call the actual application for rendering."**
> 生成された CLI は real backend (Blender / LibreOffice / GIMP の actual process) を invoke する。模倣・再実装は禁止。

これは etzhayyim が religious-corp として採用する「substrate-edge 経由で外部 software を呼ぶが、結果は MST/IPFS/L2 に anchor する」哲学と整合する。

## 3. 命名: yorishiro (依代)

`wrap` は単なる technical 用語で religious-corp の語彙系 (kami / magatama / yobel / tsukuru / kuni-umi 等) と非整合。

神道において **依代 (yorishiro)** とは「kami が宿るための vessel」で、典型的には鏡・剣・玉・木・人形などの物体。外部 software (HuggingFace API / Blender / arXiv) を kami と見立て、それを substrate 内で agent が駆動できる形 (Lexicon contract + Pregel cell + MCP tool) に整えた **vessel** こそが yorishiro である、という metaphor は:

- religious-corp 語彙系と完全整合
- "the actual application is called" (CLI-Anything 鉄則) と神学的にも一致 — yorishiro は kami の代替ではなく宿る場所
- ADR-2605192100 §1.10 「八百万 ontology」の自然な extension

ゆえに本 ADR は generator の正式名を **etzhayyim-yorishiro** と定める。

## 4. 既存 1 件の実装パターン (reference impl)

`20-actors/magatama/mcp/unispsc-isic-mcp/` (ADR-2605180900 Phase 8) は **UNSPSC + ISIC LangGraph Pregel agent fleets を 9 MCP tools として再露出する** server で、ちょうど本 ADR が量産したい 3-layer の hand-written 第 1 例である:

| Layer | 既存実装 (unispsc-isic-mcp) |
|---|---|
| Lexicon (SSoT) | `00-contracts/lexicons/com/etzhayyim/apps/{unispsc,isic}/*.json` (9 件) |
| Actor (Pregel cell) | `pymagatama/primitives/open_unispsc.py` + `open_isic_*.py` (594 cells) + `20-actors/magatama/sdk/magatama-host-sdk/src/langserver-actor.ts` |
| MCP server | `20-actors/magatama/mcp/unispsc-isic-mcp/src/cli.ts` (stdio + Streamable HTTP) |

本 ADR は **この 3-layer を generator template として正典化** する。

# Decision

## D1. yorishiro = 3-layer 出力契約

外部 software (app / webservice / local binary) を 1 件 wrap するごとに、以下 **3 layer をすべて** 生成することを yorishiro generator の出力契約とする。

| Layer | 出力先 | 役割 | SSoT 位置 |
|---|---|---|---|
| **L1 Lexicon** | `00-contracts/lexicons/ai/etzhayyim/yorishiro/<name>/<op>.json` | op ごとの input/output schema、Charter purpose、external 標識 | 唯一の contract SSoT |
| **L2 Actor (Pregel cell)** | `20-actors/magatama/cells/yorishiro_<name>/cell.py` (Python, ADR-2605202200 cell runtime contract 準拠) または `20-actors/magatama/yorishiro/<name>/src/app.ts` (TS, magatama-host-sdk 準拠) | LangGraph Pregel cell / TS Worker として substrate に hosting | runtime binding |
| **L3 MCP server** | `20-actors/magatama/mcp/yorishiro-<name>-mcp/` | stdio + Streamable HTTP 両 transport で agent (Claude Desktop / Codex / 他 etzhayyim actor) から callable | tool exposure |
| (補助) SKILL.md | `skills/etzhayyim-yorishiro-<name>/SKILL.md` | agent discovery (CLI-Anything format に準拠) | discovery |
| (補助) CLI/REPL | `70-tools/etzhayyim-cli/yorishiro/<name>/` | 人間 fallback (`--json` + REPL、CLI-Anything と同形式) | human-facing |

**禁止**: L1 / L2 / L3 のいずれかを欠いた yorishiro。3 layer を all-or-nothing で生成する (lefthook hook で enforcement)。

## D2. Lexicon 拡張フィールド (Charter compliance compile-time enforcement)

L1 Lexicon JSON は通常の atproto Lexicon schema に加え、以下 **3 拡張フィールド** を持つ:

```json
{
  "lexicon": 1,
  "id": "ai.etzhayyim.yorishiro.huggingface.searchModels",
  "defs": {
    "main": {
      "type": "query",
      "x-yorishiro-external": true,
      "x-yorishiro-kami": "huggingface.co",
      "x-yorishiro-transport": "openapi-v3",
      "x-charter-purpose": ["kisha", "grant"],
      "parameters": { ... },
      "output": { ... }
    }
  }
}
```

| フィールド | 値域 | 意味論 |
|---|---|---|
| `x-yorishiro-external` | `true` (必須) | 外部 substrate 呼出を伴う op の標識。これが true の lexicon は `magatama.Send()` (WIT outbound-http) または `magatama.Invoke()` 経由でのみ実行可。直接 `fetch()` は lefthook hook で reject |
| `x-yorishiro-kami` | string (FQDN / package name / binary name) | 宿る kami の identifier。`huggingface.co` / `org.libreoffice` / `bin:blender` 等 |
| `x-yorishiro-transport` | `openapi-v3` / `source-repo` / `browser-only` / `binary-cli` | 入力 source mode (D4 参照) |
| `x-charter-purpose` | `["donation"\|"kisha"\|"grant"\|"tithe"\|"escrow-refund"\|"internal-purchase"\|"internal-subscription"\|"internal-promo"]` の配列 | ADR-2605192115 で正典化された Charter purposes。**`subscription` / `purchase` / `tip` (external 用) は禁止値**。lefthook hook が違反値を含む lexicon を pre-commit で reject |

`x-charter-purpose` の enforcement は本 ADR が新設する `70-tools/charter-rider-applicator/hooks/no-external-purchase-purpose.mjs` で実装する。

## D3. 既存 generator infrastructure の再利用

- L1 → L2 Python cell の typed I/O: 既存の `pymagatama/cell_registry` (cell runtime contract, ADR-2605202200) をそのまま再利用
- L1 → L2 TS Worker の typed I/O: 既存の `70-tools/scripts/contract/gen-lexicon-nsid-types.mjs` をそのまま再利用 (`parseLexiconInput()` + `LexiconOutput<...>`)
- L1 → L3 MCP zod schema: 既存の `unispsc-isic-mcp` で使われている atproto Lexicon → zod 4 converter (`@etzhayyim/lexicon-to-zod`) を抽出して再利用
- Murakumo fleet placement: `50-infra/cluster/murakumo/cell-runner/cells.toml` に新規 yorishiro cell を 1 行追記するだけで cell-runner が起動 (ADR-2605202100 + 2605202200)

つまり generator は **新規 infra を一切作らず、既存の 6 個の codegen + 1 個の cell-runner pattern を組み合わせて駆動する scaffolding 専用 CLI** とする。

## D4. 入力 source mode (3 種)

| Mode | 入力 | L1 自動生成方針 | 用途例 |
|---|---|---|---|
| **(a) `openapi-v3`** | OpenAPI 3.x JSON/YAML URL or path | 各 path × method を 1 lexicon に展開。`parameters` → input schema、`responses.200.content."application/json".schema` → output schema | HuggingFace Hub API / arXiv / OpenAlex / GitHub / NDL Search / 各国 open-data |
| **(b) `source-repo`** | git URL or local path (Python/TS/Go/Rust ソース) | CLI-Anything と同じ analyze→design phase (Click / argparse / cobra 等の CLI 宣言を AST parse) → 各 subcommand を 1 lexicon | LibreOffice headless / GIMP script-fu / Blender bpy / FFmpeg / ComfyUI |
| **(c) `browser-only`** | base URL + selector hints (DOM/Playwright script) | 既知の UI flow を 1 lexicon = 1 user-task として手動定義 → L2 で mcp__claude-in-chrome ツール (`navigate` / `form_input` / `read_page`) を sequence 化 | SaaS app で公式 API 無し (社内 SaaS / 簡易管理画面) |

(a) と (b) は generator が **input → L1/L2/L3 すべて完全自動生成** 可能。(c) は L1 を半自動 (UI flow hint から op 候補を提案、人間が確定)、L2/L3 は自動。

## D5. CLI 仕様

generator は既存 `70-tools/etzhayyim-cli` の subcommand として実装:

```bash
# (a) OpenAPI v3 から
etzhayyim yorishiro create huggingface \
  --from openapi-v3 \
  --source https://huggingface.co/api/openapi.json \
  --kami huggingface.co \
  --purpose kisha,grant

# (b) source repo から
etzhayyim yorishiro create libreoffice \
  --from source-repo \
  --source https://github.com/LibreOffice/core \
  --kami org.libreoffice \
  --purpose donation,grant

# (c) browser-only から
etzhayyim yorishiro create kintone-our-tenant \
  --from browser-only \
  --source https://our-tenant.cybozu.com \
  --kami cybozu.kintone \
  --purpose internal-promo \
  --ui-script ./ui-flows/kintone.ts

# 既存 yorishiro の lexicon を再生成 (kami 側 API 変更時)
etzhayyim yorishiro regen huggingface

# 一覧
etzhayyim yorishiro list

# Charter compliance audit (1 度の commit ですべて自動 lint)
etzhayyim yorishiro audit
```

`audit` subcommand は本 ADR の D2 enforcement を一発で実行 — `x-charter-purpose` 違反 / `x-yorishiro-external` 欠落 / `fetch()` 直接使用 / L1-L2-L3 不一致を検出。

## D6. Substrate boundary 整理 (RW-free との関係)

yorishiro は外部 substrate へ書込/読込する op を内包するため、ADR-2605172000 (RW-free) の境界条件を以下のように明確化する:

| op 種別 | 許可 | substrate への state landing |
|---|---|---|
| **read 系** (search, fetch, classify, list) | ✓ | 結果は呼出側 cell が MST record として書き戻す (yorishiro 自体は stateless) |
| **write 系 (非営利目的)** (donation receipt / grant disbursement notice / kisha post / tithe split notification / escrow refund) | ✓ | 外部 substrate 側の record id を MST に anchor、L2 anchor は呼出側 cell の責務 |
| **write 系 (営利目的)** (third-party 外部 SaaS への subscribe / purchase / tip) | ✗ | lexicon の `x-charter-purpose` validator が pre-commit で reject (ADR-2605192115 §4) |
| **internal SBT↔SBT carveout** (e7m 信者間 etzhayyim 系 app) | ✓ | `x-charter-purpose: internal-*` を許可、ただし `x-yorishiro-external: false` (yorishiro ではなく通常の internal actor) |

つまり yorishiro は **read 全般 + 非営利 write のみ**。SBT 内部 carveout は yorishiro の対象外で、通常の magatama actor として書く。

## D7. Phase / Milestone

| Phase | 内容 | 完了基準 |
|---|---|---|
| **Phase 1 (本 ADR 承認後 1 week)** | generator skeleton (`70-tools/etzhayyim-cli/yorishiro/`) + (a) OpenAPI mode のみ実装 + lefthook hook 1 本 (`no-external-purchase-purpose`) | `etzhayyim yorishiro create` が arXiv API 1 件で動く |
| **Phase 2 (Phase 1 後 2 weeks)** | (b) source-repo mode 実装、LibreOffice/GIMP/Blender の 3 件で実証 | 3 件で L1/L2/L3 all-or-nothing 生成成功 |
| **Phase 3 (Phase 2 後 1 week)** | (c) browser-only mode + mcp__claude-in-chrome 統合 | 1 件 (社内 SaaS) で実証 |
| **Phase 4 (継続)** | 既存 60-apps/ 内 vendor-API 直叩き箇所を yorishiro 化して migrate | ad-hoc fetch() / vendor SDK import が 0 件 |
| **Phase 5 (継続)** | `etzhayyim yorishiro audit` を CI 必須化 | main branch 上 `x-charter-purpose` 違反 0 件、`x-yorishiro-external: true` 必須 enforcement on |

## D8. ADR-2605180900 (unispsc-isic-mcp) の位置付け再定義

`unispsc-isic-mcp` (ADR-2605180900 Phase 8) は **本 ADR の reference impl** として位置付け直す。同 ADR は実装が先行した正典的 1 例 — 本 ADR が量産パターンを正典化したので、`unispsc-isic-mcp` は Phase 4 migration の対象として将来的に generator 再生成版へ置換可能 (現状は hand-written のまま維持で問題なし、置換は coverage equivalence が確認できた時点で別 ADR)。

# Consequences

## Positive

- **Shannon 冗長度の劇的削減**: 130+ apps の外部 API 叩き箇所を 1 generator + lexicon SSoT に集約。新規 vendor 統合の marginal cost が `etzhayyim yorishiro create <name> --from openapi-v3 --source <url> --purpose <list>` 1 line に圧縮
- **Charter compliance の compile-time enforcement**: ADR-2605192200 §2 の 8 prohibited categories を lexicon validator + lefthook hook で pre-commit reject。人手 review 依存を排除
- **MCP standard exposure**: 全 external integration が自動的に MCP server として露出 → Claude Desktop / Codex / 他 etzhayyim actor から uniform interface で callable
- **religious-corp 語彙系統合**: yorishiro (依代) という命名で kami / magatama / yobel / tsukuru / kuni-umi に並ぶ第一級の概念として substrate に組み込まれる
- **既存 infra 再利用**: 新規 codegen / runtime / fleet を作らず、ADR-2605202200 cell contract + 既存 codegen 6 個 + cell-runner を組み合わせるのみ

## Negative / Tradeoffs

- **state-boundary 増加**: yorishiro が呼ぶ kami の state は etzhayyim substrate 外。読み戻しは呼出側 cell が anchor する義務を負う (D6 で明文化済み) が、規律が乱れると "外部 state を信頼する actor" が再増殖する risk
- **kami 側 API 変更への追随コスト**: OpenAPI/source repo を kami 側が破壊的変更すれば yorishiro lexicon は不整合になる。`etzhayyim yorishiro regen` + CI 上の `audit` で drift 検出は可能だが、人手対応は 0 にできない
- **browser-only mode (c) の脆弱性**: DOM selector 依存。kami 側 UI が変わるたびに breakage。L2 で mcp__claude-in-chrome の `find` を selector-resilient な方針で書く必要 (これは別 ADR)
- **Lexicon 数の爆発**: 130+ apps × 各 vendor の数十 op = 数千 lexicon 追加見込み。既存 2346 lexicon (F2 時点) と合算で >5000 になる。codegen 時間と registry size は要監視
- **`unispsc-isic-mcp` との一時的な dual-path**: Phase 4 migration が完了するまで hand-written と generator 出力が混在 (D8 で許容済み)

## Constitutional invariants (NOT amendable, ADR-2605192100 derived)

以下は本 ADR の implementation 詳細ではなく、religious-corp 憲法的に invariant である:

- yorishiro lexicon は `x-charter-purpose` を必須とし、`subscription` / `purchase` / `tip` (external) を **絶対に** 受け付けない
- yorishiro は黙示録的 (eschatological) kami を宿す対象としない (ADR-2605192100 §1.15、Book of Revelation 系統の整数論的 / 終末論的 API は yorishiro 対象外)
- yorishiro は ad-tech kami (GA4 ads / Meta Pixel / AdSense) を絶対に宿さない (Charter Rider §2(a))
- yorishiro は covert force / closed-source 軍事 kami を絶対に宿さない (ADR-2605192100 §1.12 — Transparent Religious Force のみ、本 ADR は Transparent 系 OSINT/research yorishiro のみ許可)

# Alternatives Considered

## ALT-1: hand-written 継続 (status quo)

- メリット: 個別最適、generator 学習コスト 0
- デメリット: Shannon 冗長度高、Charter compliance drift、新規 vendor 統合 cost が線形
- 棄却理由: 130 → 数百規模に拡大する religious-corp の vendor surface に対し scaling しない

## ALT-2: CLI-Anything をそのまま採用、出力は CLI のみ

- メリット: 上流に追従、メンテ移譲
- デメリット: 出力が CLI で止まる → MCP exposure 別途必要 / Lexicon SSoT を経由しない → Charter compliance enforcement が hook ベースで脆弱 / religious-corp 語彙統合なし
- 棄却理由: etzhayyim substrate の 3-layer (Lexicon / Pregel / MCP) と integration されない

## ALT-3: MCP server のみ生成、Lexicon と Pregel cell は省略

- メリット: 軽量、agent 露出は最短
- デメリット: Lexicon SSoT 不在 → input/output schema drift / Pregel cell 不在 → Murakumo fleet 上で hosting されない / Charter purpose の compile-time enforcement 不可
- 棄却理由: D1 の "3 layer all-or-nothing" 原則は religious-corp の SSoT 規律と直結。妥協しない

## ALT-4: 命名を `wrap` / `bridge` / `adapter` のいずれかにする

- メリット: industry-standard 用語、外部 contributor の理解が早い
- デメリット: religious-corp 語彙系 (kami / magatama / yobel / tsukuru / kuni-umi) と非整合、八百万 ontology (ADR-2605192100 §1.10) の自然な extension 機会を失う
- 棄却理由: religious-corp としてのアイデンティティを技術用語で薄める方向は ADR-2605192100 と整合しない。`yorishiro` を採用

# References

- ADR-2605192100 (etzhayyim mission charter — 八百万 ontology, non-eschatological, Wellbecoming)
- ADR-2605192115 (SBT↔SBT internal carveout — `x-charter-purpose` 値域の正典)
- ADR-2605192200 (IP-free release + Charter Rider v2.0 — §2 8 prohibited categories)
- ADR-2605180900 (LangGraph Pregel fleet + MCP bridge — reference impl `unispsc-isic-mcp`)
- ADR-2605202200 (magatama cell.py runtime contract — L2 Python cell の DI 契約)
- ADR-2605172000 (RW-free substrate architecture — yorishiro の state boundary 規律)
- ADR-2605172100 (etzhayyim-sdk substrate client — L2 TS Worker の client SSoT)
- HKUDS/CLI-Anything (外部参照 — generator 設計の inspiration、ただし出力 layer は etzhayyim-native に翻訳)
- `20-actors/magatama/mcp/unispsc-isic-mcp/README.md` (1 件目の hand-written 3-layer 実装)
- `00-contracts/lexicons/com/etzhayyim/apps/{unispsc,isic}/` (1 件目の hand-written L1 lexicons)
