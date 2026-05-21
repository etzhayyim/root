---
id: adr-2605181400-bpmn-extract-to-etzhayyim-root
title: BPMN ownership extraction to etzhayyim-root repo
status: active
doc_type: adr
topic: bpmn-ownership
authoritative: true
last_verified: 2026-05-18
authoritative_for:
  - bpmn-process-definition-ownership
  - bpmn-engine-infra-ownership
related:
  - 90-docs/adr/2605172000-etzhayyim-rw-free-substrate.md
  - 90-docs/adr/2605091400-mcp-as-cell-membrane-lexicon-xrpc-demotion.md
  - 90-docs/adr/2605081200-spiffworkflow-bpmn-engine-replacement.md
  - 90-docs/adr/2605082200-pyzeebe-handler-thin-dispatcher-contract.md
supersedes: []
superseded_by: []
---

# Context

CEO 河崎 directive 2026-05-18「bpmn は etzhayyim-root に移動」。BPMN
ownership を religious-corp substrate (etzhayyim-root) に集約し、
ai-gftd-apps-gftdcojp は AT Protocol app surface 専念に絞る。

背景:
- ADR-2605172000 で `@etzhayyim/sdk` を RW-free substrate (AT Protocol
  MST + IPFS + Base L2 anchor) として独立 repo 化。
- ADR-2605091400 で XRPC + Lexicon JSON を cohort 内部 (cytoplasm) 通信
  専用に降格、MCP を sole external API として cell membrane 化。
- BPMN は process orchestration の SSoT であり、religious-corp 視点では
  「membership lifecycle / sacrament workflow / consent gate」の
  authority artefact。AT Protocol app 視点では「derive rule 実行基盤」。
  両 repo 間で重複所有していると drift する。
- etzhayyim-root には既に `00-contracts/bpmn` / `20-actors/etzhayyim-bpmn-sdk`
  / `50-infra/k8s/bpmn-timers` が定着しつつあり、BPMN 中心化の動きが
  進行中だった。

# Decision

1. **BPMN file ownership = etzhayyim-root** に集約。
2. ai-gftd-apps-gftdcojp branch `iter144-bpmn-extract` で以下を `git rm`:
   - `00-contracts/bpmn/ai/gftd/*` (4,443 files; AT-Protocol-app process defs)
   - `60-apps/ai-gftd-project-bpmn/` (28 files; BPMN appview)
   - `60-apps/*/bpmn/` (53 per-project subdirs, 3,370 files)
   - `50-infra/k8s/bpmn-engine-host` (SpiffWorkflow engine, ADR-2605081200)
   - `50-infra/k8s/yata-zeebe-worker` (legacy Zeebe replacement target)
   - `50-infra/vultr/zeebe` (legacy Zeebe infra)
3. etzhayyim-root branch `import-bpmn-from-ai-gftd` で同 file 群を copy:
   - 1,322 files changed (+32,299 / -3,361)
   - 481 new file additions, 841 overwrites of pre-existing etzhayyim
     versions (ai-gftd side = source-of-truth on conflict)
4. **References 873 件は本 ADR 範囲外** (file move only):
   - Worker handler / `magatama.jsonld` `derive` rule / lexicon registry /
     docs 内の `00-contracts/bpmn/` / `60-apps/*/bpmn/` パス参照は
     ai-gftd 側で一時的に broken。
   - 後続 iter (iter145+) で `@etzhayyim/bpmn-*` package 経由参照 / pnpm
     workspace `file:` リンク / submodule のいずれかに書き換える。
   - Build/deploy chain は当面 broken (lawfirm Stream A は HTML/SPA で
     完結しており BPMN dispatcher 未稼働=`replicas=0` (iter138/143) なので
     paying-client critical path は無影響)。

# Consequences

**Positive**
- BPMN drift 排除: 同名 process def が 2 repo に併存しなくなる。
- etzhayyim-root が religious-corp substrate として self-contained に
  近づく (membership + sacrament + BPMN engine 全てが 1 repo)。
- ai-gftd-apps-gftdcojp は AT Protocol app surface に集中、
  「選択と集中」原則 (iter143 Stream A) と整合。

**Negative / リスク**
- ai-gftd 側 build chain が 873 参照分 broken。CI fail 想定。
- per-project `bpmn/` を import している magatama actor は path
  resolution 失敗。
- ADR-2605082200 PyZeebe handler thin-dispatcher contract 内の
  BPMN path 参照が `etzhayyim-root` 側にしかなくなるため、
  bpmn-dispatcher 配置を再設計する必要がある。
- 履歴分断: ai-gftd 側 git log では `00-contracts/bpmn` の commit 履歴
  が 4,558 deletes で打ち切られる (filter-branch しないため source 履歴
  は ai-gftd に残るが「past tense」扱い)。

**Pending operator actions** (deps.toml `[[migrations]]
bpmn-extract-to-etzhayyim-root-2026-05-18` で追跡):

1. ai-gftd-apps-gftdcojp iter145+ で `00-contracts/bpmn/` 参照 873 件を
   `@etzhayyim/bpmn-*` package 参照 or pnpm workspace path に sed。
2. magatama actor の `magatama.jsonld` `derive` rule が参照する BPMN path
   を package import 経由に書き換え。
3. bpmn-dispatcher 配置先決定: etzhayyim-root K8s cluster に移すか、
   ai-gftd 側に残し etzhayyim BPMN を fetch する形にするか。
4. CI lint (deps-score / lint-nsid-regression / bundle-lexicons)
   の cross-repo path resolution 対応。
5. `90-docs/CLAUDE.md` Key Conventions の BPMN 関連 pointer を
   etzhayyim-root 側 path に更新。
6. ai-gftd-apps-gftdcojp `deps.toml [directory_index]` から bpmn entry
   削除 + etzhayyim-root 側 deps.toml に追記。

# Decisions (resolved in iter144, 2026-05-18 follow-up)

## D1: Path-rewrite scheme = `etzhayyim-root/` prefix

873+ cross-references (実測 1,499 files) を blanket sed で
`00-contracts/bpmn/` → `etzhayyim-root/00-contracts/bpmn/` ほか
5 patterns に書き換え。判断理由:

- `@etzhayyim/bpmn-*` npm package 経由は **import 文** には適すが、
  BPMN は `.bpmn` XML として fs.readFile される runtime artefact が
  多い。npm package で wrap すると遅延 + 単純な path lookup が壊れる。
- pnpm workspace `file:` link は単一 mono-repo 前提。cross-repo (別
  Git remote) では再現性が薄い。
- 単純な相対 path prefix `etzhayyim-root/` は (a) loader/resolver 側で
  `process.env.ETZHAYYIM_ROOT` か固定 sibling path で解決すれば足り、
  (b) grep visibility 高、(c) 後から package 化 / submodule 化に変更
  しても sed 1 回で済む。
- Excluded: `90-docs/adr/2605181400-*.md` と `_working/.../DECISION-LOG.md`
  は本 ADR + iter144 row そのもので、移動の **過去状態** を記述するため
  prefix しない。

## D2: bpmn-dispatcher 配置 = ai-gftd 側残置

bpmn-dispatcher の source は `20-actors/magatama/py/src/pymagatama/
dispatcher_main.py` (74KB Python, pymagatama package の一部) で、
pymagatama は ai-gftd-apps-gftdcojp 側にある (etzhayyim-root に
移してない)。判断:

- dispatcher を etzhayyim-root へ移すには pymagatama 全体 (or
  dispatcher subset) を切り出す必要があり、Stream A critical path
  (lawfirm 集客) と関係薄い。
- BPMN file の所有権は etzhayyim-root、dispatcher の所有権は
  ai-gftd-apps-gftdcojp で OK。dispatcher は起動時に
  `${ETZHAYYIM_ROOT:-../etzhayyim-root}/00-contracts/bpmn/` を読み
  込む形 (env var で sibling path 解決)。
- K8s 配置: `bpmn-dispatcher` Deployment は ai-gftd 側 cluster
  (lax VKE) に残置。`replicas=0` (iter137 から、Vultr cap
  TUO-21FNS pending) のままで、再起動時は etzhayyim BPMN を
  fetch するように環境変数を設定する。
- Cloudflared tunnel `50-infra/vultr/cloudflared/bpmn-dispatcher-tunnel.yaml`
  も ai-gftd 側残置 (dispatcher と同 cluster)。

## D3: CI lint cross-repo path resolution

`70-tools/scripts/contract/*` 配下の linter (`deps-score`,
`lint-nsid-regression`, `bundle-lexicons`) は `00-contracts/bpmn/`
を読まなくなった。`etzhayyim-root/...` prefix を含む path 参照は
linter が file resolution に失敗するため、ai-gftd 側 lint hook は
当面 BPMN path 検証を skip する。

- 短期: `70-tools/scripts/lint/bpmn-coverage-manifest.mjs` 等の
  `00-contracts/bpmn/` walk を `etzhayyim-root/00-contracts/bpmn/`
  に変更 + `ETZHAYYIM_ROOT` env var fallback で sibling repo を
  resolve。
- 中期: `etzhayyim-root` を ai-gftd の pnpm workspace か git
  submodule として取り込むか、`@etzhayyim/bpmn-contracts` npm
  package を publish して `node_modules` 経由で resolve する。

## D4: Key Conventions pointer update

`CLAUDE.md` Actor / Worker section の以下を更新:

- `**BPMN engine = SpiffWorkflow** → 90-docs/adr/2605081200-... +
  50-infra/k8s/bpmn-engine-host/RUNBOOK.md`
  → `... + etzhayyim-root/50-infra/k8s/bpmn-engine-host/RUNBOOK.md`
- LLM Coding Guardrails の BPMN/Zeebe 関連エントリは引き続き有効
  だが、path は `etzhayyim-root/` prefix を使う。

iter144 sed で path prefix は自動更新済 (`CLAUDE.md` は sed 対象)。

## D5: deps.toml [directory_index] cleanup

`deps.toml` の以下を整理:

- `[directory_index."00-contracts"]` の `pointer` から bpmn を削除
  (移管先 = etzhayyim-root)
- `[directory_index."60-apps"]` の `ai-gftd-project-bpmn` 行を
  削除 (etzhayyim-root へ移管)
- `[directory_index."50-infra"]` の `k8s/bpmn-engine-host`,
  `k8s/yata-zeebe-worker`, `vultr/zeebe` 行を削除
- `[[migrations]]` に
  `bpmn-extract-to-etzhayyim-root-2026-05-18` entry を `done`
  status で追加 (decision = D1-D5)

# Alternatives Considered

- **A. submodule で etzhayyim-root を ai-gftd に取り込む**: build chain
  は壊さないが、religious-corp substrate の独立性が薄れ「だったら分け
  ない方が良い」議論に戻る。**却下**。
- **B. file copy のまま両 repo に冗長保持**: drift リスク高、過去の
  「同じ判断を 2 repo に複写しない」原則 (CLAUDE.md docs SSoT) 違反。
  **却下**。
- **C. 参照 873 件を本 iter で同時 sed**: atomic だが、sed 誤作動リスク
  + Worker binding / wrangler.jsonc / lexicon registrar 等の細やかな
  context-sensitive 書き換え失敗時に 1 commit revert で巻き戻る範囲が
  巨大。**却下** — file-move と path-rewrite を分離。

# References

- CEO 河崎 directive 2026-05-18「bpmn は etzhayyim-root に移動」
- `_working/gftdcojp-revenue/DECISION-LOG.md` iter144 (本 iter)
- etzhayyim-root commit `Import BPMN from ai-gftd-apps-gftdcojp`
  (branch `import-bpmn-from-ai-gftd`)
- ai-gftd-apps-gftdcojp branch `iter144-bpmn-extract`
- ADR-2605172000 (etzhayyim RW-free substrate SDK)
- ADR-2605091400 (MCP-as-cell-membrane; XRPC demotion)
- ADR-2605081200 (SpiffWorkflow BPMN engine)
