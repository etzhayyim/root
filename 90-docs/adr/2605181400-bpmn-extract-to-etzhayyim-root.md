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
  - adr-2605172000-etzhayyim-rw-free-substrate
  - adr-2605091400-mcp-as-cell-membrane-lexicon-xrpc-demotion
  - adr-2605081200-spiffworkflow-bpmn-engine-replacement
  - adr-2605082200-pyzeebe-handler-thin-dispatcher-contract
supersedes: []
superseded_by: []
---

# Context

CEO 河崎 directive 2026-05-18「bpmn は etzhayyim-root に移動」。BPMN
ownership を religious-corp substrate (etzhayyim-root) に集約し、
etzhayyim-root は AT Protocol app surface 専念に絞る。

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
2. etzhayyim-root branch `iter144-bpmn-extract` で以下を `git rm`:
   - `00-contracts/bpmn/com/etzhayyim/*` (4,443 files; AT-Protocol-app process defs)
   - `60-apps/etzhayyim-project-bpmn/` (28 files; BPMN appview)
   - `60-apps/*/bpmn/` (53 per-project subdirs, 3,370 files)
   - `50-infra/k8s/bpmn-engine-host` (SpiffWorkflow engine, ADR-2605081200)
   - `50-infra/k8s/yata-zeebe-worker` (legacy Zeebe replacement target)
   - `50-infra/vultr/zeebe` (legacy Zeebe infra)
3. etzhayyim-root branch `import-bpmn-from-etzhayyim` で同 file 群を copy:
   - 1,322 files changed (+32,299 / -3,361)
   - 481 new file additions, 841 overwrites of pre-existing etzhayyim
     versions (etzhayyim side = source-of-truth on conflict)
4. **References 873 件は本 ADR 範囲外** (file move only):
   - Worker handler / `magatama.jsonld` `derive` rule / lexicon registry /
     docs 内の `00-contracts/bpmn/` / `60-apps/*/bpmn/` パス参照は
     etzhayyim 側で一時的に broken。
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
- etzhayyim-root は AT Protocol app surface に集中、
  「選択と集中」原則 (iter143 Stream A) と整合。

**Negative / リスク**
- etzhayyim 側 build chain が 873 参照分 broken。CI fail 想定。
- per-project `bpmn/` を import している magatama actor は path
  resolution 失敗。
- ADR-2605082200 PyZeebe handler thin-dispatcher contract 内の
  BPMN path 参照が `etzhayyim-root` 側にしかなくなるため、
  bpmn-dispatcher 配置を再設計する必要がある。
- 履歴分断: etzhayyim 側 git log では `00-contracts/bpmn` の commit 履歴
  が 4,558 deletes で打ち切られる (filter-branch しないため source 履歴
  は etzhayyim に残るが「past tense」扱い)。

**Pending operator actions** (deps.toml `[[migrations]]
bpmn-extract-to-etzhayyim-root-2026-05-18` で追跡):

1. etzhayyim-root iter145+ で `00-contracts/bpmn/` 参照 873 件を
   `@etzhayyim/bpmn-*` package 参照 or pnpm workspace path に sed。
2. magatama actor の `magatama.jsonld` `derive` rule が参照する BPMN path
   を package import 経由に書き換え。
3. bpmn-dispatcher 配置先決定: etzhayyim-root K8s cluster に移すか、
   etzhayyim 側に残し etzhayyim BPMN を fetch する形にするか。
4. CI lint (deps-score / lint-nsid-regression / bundle-lexicons)
   の cross-repo path resolution 対応。
5. `90-docs/CLAUDE.md` Key Conventions の BPMN 関連 pointer を
   etzhayyim-root 側 path に更新。
6. etzhayyim-root `deps.toml [directory_index]` から bpmn entry
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

## D2: bpmn-dispatcher 配置 = etzhayyim 側残置

bpmn-dispatcher の source は `20-actors/magatama/py/src/pymagatama/
dispatcher_main.py` (74KB Python, pymagatama package の一部) で、
pymagatama は etzhayyim-root 側にある (etzhayyim-root に
移してない)。判断:

- dispatcher を etzhayyim-root へ移すには pymagatama 全体 (or
  dispatcher subset) を切り出す必要があり、Stream A critical path
  (lawfirm 集客) と関係薄い。
- BPMN file の所有権は etzhayyim-root、dispatcher の所有権は
  etzhayyim-root で OK。dispatcher は起動時に
  `${ETZHAYYIM_ROOT:-../etzhayyim-root}/00-contracts/bpmn/` を読み
  込む形 (env var で sibling path 解決)。
- K8s 配置: `bpmn-dispatcher` Deployment は etzhayyim 側 cluster
  (lax VKE) に残置。`replicas=0` (iter137 から、Vultr cap
  TUO-21FNS pending) のままで、再起動時は etzhayyim BPMN を
  fetch するように環境変数を設定する。
- Cloudflared tunnel `50-infra/vultr/cloudflared/bpmn-dispatcher-tunnel.yaml`
  も etzhayyim 側残置 (dispatcher と同 cluster)。

## D3: CI lint cross-repo path resolution

`70-tools/scripts/contract/*` 配下の linter (`deps-score`,
`lint-nsid-regression`, `bundle-lexicons`) は `00-contracts/bpmn/`
を読まなくなった。`etzhayyim-root/...` prefix を含む path 参照は
linter が file resolution に失敗するため、etzhayyim 側 lint hook は
当面 BPMN path 検証を skip する。

- 短期: `70-tools/scripts/lint/bpmn-coverage-manifest.mjs` 等の
  `00-contracts/bpmn/` walk を `etzhayyim-root/00-contracts/bpmn/`
  に変更 + `ETZHAYYIM_ROOT` env var fallback で sibling repo を
  resolve。
- 中期: `etzhayyim-root` を etzhayyim の pnpm workspace か git
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
- `[directory_index."60-apps"]` の `etzhayyim-project-bpmn` 行を
  削除 (etzhayyim-root へ移管)
- `[directory_index."50-infra"]` の `k8s/bpmn-engine-host`,
  `k8s/yata-zeebe-worker`, `vultr/zeebe` 行を削除
- `[[migrations]]` に
  `bpmn-extract-to-etzhayyim-root-2026-05-18` entry を `done`
  status で追加 (decision = D1-D5)

# Alternatives Considered

- **A. submodule で etzhayyim-root を etzhayyim に取り込む**: build chain
  は壊さないが、religious-corp substrate の独立性が薄れ「だったら分け
  ない方が良い」議論に戻る。**却下**。
- **B. file copy のまま両 repo に冗長保持**: drift リスク高、過去の
  「同じ判断を 2 repo に複写しない」原則 (CLAUDE.md docs SSoT) 違反。
  **却下**。
- **C. 参照 873 件を本 iter で同時 sed**: atomic だが、sed 誤作動リスク
  + Worker binding / wrangler.jsonc / lexicon registrar 等の細やかな
  context-sensitive 書き換え失敗時に 1 commit revert で巻き戻る範囲が
  巨大。**却下** — file-move と path-rewrite を分離。

# Amendment 2026-05-22: D2 superseded — bpmn-dispatcher extracted

`§D2 (bpmn-dispatcher = etzhayyim 側残置)` の前提が崩壊したため、
当該条項を以下で置換する。

**実態の変化** (2026-05-18 以降):
- pymagatama 全体が etzhayyim-root へ移管完了
  (`etzhayyim/20-actors/magatama/py/src/pymagatama/`)
- etzhayyim-apps-etzhayyimcojp 側 `20-actors/magatama/` は削除済
- D2 の rationale (「pymagatama が etzhayyim にあるので dispatcher も残置」)
  は無効化

**新 D2 (active)**: bpmn-dispatcher infra も etzhayyim-root 側に集約。
配置先 = `50-infra/k8s/bpmn-dispatcher/`:

| ファイル | 出典 (etzhayyim-apps-etzhayyimcojp, 削除済) |
|---|---|
| `deployment-dispatcher.yaml` | `50-infra/vultr/mitama-udf-pool/templates/dispatcher.yaml` (Helm → plain manifest) |
| `tunnel.yaml` | `50-infra/vultr/cloudflared/bpmn-dispatcher-tunnel.yaml` |
| `ingress-dispatcher.yaml` | `50-infra/vultr/mitama-udf-app-raw/manifests/ingress-networking-k8s-io-dispatcher-etzhayyim-ai.json` |
| `configmap-pymagatama-cache-fix.yaml` | `…/configmap-pymagatama-dispatcher-main-cache-fix.json` |
| `configmap-pymagatama-sse-fix.yaml` | `…/configmap-pymagatama-dispatcher-main-sse-fix.json` |
| `configmap-mailer-direct-patch.yaml` | `…/configmap-bpmn-dispatcher-mailer-direct-patch.json` |
| `README.md` + `RUNBOOK.md` | new |

Domain rewrites: `dispatcher.etzhayyim.com` → `dispatcher.etzhayyim.com`,
`mcp.etzhayyim.com` → `mcp.etzhayyim.com`, `ses-api.etzhayyim.com` →
`ses-api.etzhayyim.com`.

**Substrate-boundary 注記** (ADR-2605172100 hard rule "MUST NOT integrate
fiat payment processors"): 移管した dispatcher Deployment は pymagatama
の `lawfirm_billing` / `lawfirm_checkout` / `ingest.stripe` 依存により
`STRIPE_*` (5 個) + `RW_URL` env を継承する。本 iter では runtime 互換性
維持のため preserve。Substrate purity 回復は pymagatama Stripe 抽出 +
binding registry の AT MST 化を行う別 iter で対応。pymagatama 自体が
2026-05-18 以前から etzhayyim 内に Stripe 関連ファイルを持つため、本
移管は **新規違反を導入していない**。

**Pending operator actions**:
1. CF Tunnel 新規作成: etzhayyim CF account で
   `cloudflared tunnel create bpmn-dispatcher` → `tunnel.yaml` の
   `REPLACE_ME_TUNNEL_ID` + `REPLACE_ME_CREDENTIALS_JSON` を埋める。
2. DNS: `dispatcher.etzhayyim.com` + `mcp.etzhayyim.com`
   (+ `ses-api.etzhayyim.com`) CNAME → `<tunnel>.cfargotunnel.com`
   (proxied=True)。
3. pymagatama image build & push (`ghcr.io/etzhayyim/pymagatama:<tag>`)。
4. Secret provision (`bpmn-dispatcher-auth` /
   `bpmn-dispatcher-rw` / `lawfirm-stripe` 等)、namespace `mitama-udf`。
5. `kubectl apply -f 50-infra/k8s/bpmn-dispatcher/` (etzhayyim VKE)。
6. etzhayyim-apps-etzhayyimcojp CF account の旧 tunnel
   `be2cc0b0-ddee-4ca7-baf1-2bffbef18f31` 削除 + 同 VKE 側
   Deployment `cloudflared-bpmn-dispatcher` + `bpmn-dispatcher`
   削除 (cutover 検証後)。

**触らない範囲** (本 iter 対象外、別 iter で sed):
- etzhayyim-apps-etzhayyimcojp 20+ files の `dispatcher.etzhayyim.com` 参照
  (terraform / ingress RUNBOOK / K8s deployment.yaml / CF Worker
  routing-table.ts 等) — §D3 follow-up と同様 path-rewrite iter で処理。
- `00-contracts/bpmn/` の lexicon binding 列挙はそのまま (ADR-2605091400
  MCP-as-cell-membrane の dual-wire SSoT 規約に従う)。
- etzhayyim-apps-etzhayyimcojp `50-infra/cloudflare/workers/wfp-dispatcher/`
  は別物 (Workers for Platforms dispatcher)、本 iter スコープ外。

# References

- CEO 河崎 directive 2026-05-18「bpmn は etzhayyim-root に移動」
- CEO 河崎 directive 2026-05-22「dispatcher も取り出して」(本 amendment)
- `_working/etzhayyimcojp-revenue/DECISION-LOG.md` iter144 (本 iter)
- etzhayyim-apps-etzhayyimcojp commit `Import BPMN from etzhayyim-apps-etzhayyimcojp`
  (branch `import-bpmn-from-etzhayyim`)
- etzhayyim-apps-etzhayyimcojp branch `iter144-bpmn-extract`
- ADR-2605172000 (etzhayyim RW-free substrate SDK)
- ADR-2605172100 (etzhayyim on-chain payment substrate — Stripe prohibition)
- ADR-2605091400 (MCP-as-cell-membrane; XRPC demotion)
- ADR-2605081200 (SpiffWorkflow BPMN engine)
