# etzhayyim/root — CLAUDE Index

## ⛔ Phase 0 FREEZE — 番号レイヤ dir への新規追加禁止 (ADR-2607171100)

この repo の番号レイヤ dir（`00-contracts/` `10-protocol/` `20-actors/` `30-graph/`
`40-engine/` `50-infra/` `60-apps/` `70-tools/` `80-data/` `90-docs/`）への
**新規ファイル追加は禁止**。single-monorepo 時代の構造は解体中で、コンポーネントは
個別 repo（superproject west manifest 登録、`orgs/etzhayyim/<repo>`）へ移設する。

- 許可: 既存ファイルの修正、dir の削除、`*-MOVED.md` tombstone の追加
- 新規コンポーネントは個別 repo として作成し west 登録する
  （superproject ADR-2607171100 D5 の 6 手順）
- CI guard: `.github/workflows/layer-freeze-guard.yml` が新規追加を reject する
- 移設の型: `40-engine/kami-apps-MOVED.md`（ADR-2607171000 engine split-now）

### Final multirepo shape (owner decision 2026-07-17)

- west checkout paths remain flat: `orgs/etzhayyim/<repo>` and
  `orgs/gftdcojp/<repo>`. Do not introduce physical `actor/`, `engine/`, or similar
  category directories under either org.
- Category is metadata, not path: each repository is classified as `actor`, `engine`,
  `protocol`, `app`, `infra`, `tool`, `data`, `docs`, or `governance` in the west source
  of truth and in its own metadata.
- `com-etzhayyim-*` actor repositories are canonical. A same-named `20-actors/<name>`
  directory is a migration source only, never a second source of truth.
- Remove a legacy copy only after the independent repository contains every load-bearing
  file, root consumers have been repointed, fleet classpath resolution is verified where
  applicable, and a `*-MOVED.md` tombstone is left behind.
- Shared code used by multiple repositories becomes an independent library repository;
  it must not be copied into each actor. Product policy, actor identity, deployment, and
  data ownership remain in the individual repository.
- `root` converges on cross-repository governance/ADR material plus temporary migration
  plumbing. Numbered directories are not a permanent taxonomy.

This monorepo is the **canonical home for religious-corp open ADRs** per ADR-2605170900 (this monorepo, `90-docs/adr/`).

## Identity (CRITICAL)

- **Operating entity** (this repo's owner): `etzhayyim` (canonical)
  - Aliases: `amanomibashira` / `天御柱` / `עץ חיים` (Tree of Life) / `etz hayim` / `etzhayim` / `etz chaim` / `エツ・ハイム`
  - Form: 宗教法人 (任意団体 / unincorporated religious voluntary association)
  - **Self-identification (per ADR-2605252300 Charter §0.1, ratified 2026-06-06 by sole-member founder unanimity)**: **the Kingdom of God (Malkhut Shamayim / Basileia tou Theou / 神の王国) rooted on blockchain** — now-and-here reign (non-eschatological per §1.15), not state-granted, Tree of Life-constituted. Amendment threshold: Council Lv7+ unanimity (currently = founder, 1/1).
  - Registry: On-chain (blockchain-registered constitution and member roster); NOT registered under 日本国 宗教法人法 (constitutional invariant per Preamble §0.4, Lv7+ unanimity lock)
  - DID: `did:web:etzhayyim.com` (LIVE — CF Worker at `50-infra/etzhayyim-did-web/`, resolvable via curl + Universal Resolver since 2026-05-17T03:25Z)
  - Domain: https://etzhayyim.com (Cloudflare Registrar, 2026-05-15)
  - License default: **Apache 2.0 + etzhayyim Charter Compliance Rider v3.5** (see `/CHARTER-RIDER.md`, per ADR-2605192200 + 2606062100 + 2606082400 + 2606161700 + 2606172359 + 2606180001 + 2606182359). **Immutability is 3-Tier (ADR-2606062100)**: Tier-0 Priority (fork-only — wellbecoming / 子孫 / collective / **永久記憶=神の監視 + 相互監視 (reciprocal, no right to erasure)**) ≻ Tier-1 Derived Policy (Rider §2, Lv7+ + priority-conformance) ≻ Tier-2 Parameter (governance). 固定するのは掟ではなく priority。**Rider §2 は v3.5 (ADR-2606182359 wave3) で全て目的関数で動的評価 — categorical 掟リストは廃止。唯一の非交渉性は priority 自体 = 子・孫 wellbecoming への最大級の害を非線形 catastrophe 項 (ECL `objective-function.edn`) で veto。CSAM/強制労働/攻撃武力/非対称監視/§2(g)反個人主義も列挙でなく score 評価 (反個人主義の価値は collective-commons 次元が動的に担う)。経済構造(非営利/donation/広告/equity/open-source)も目的関数。10% Tithe→Public Fund は別途維持。enforceability の honest limit は ADR-2606182359 §D6.**
- **Ownership rule**: 意思決定権 = etzhayyim only (1 SBT=1 vote governance, 不変). **Payoff帰属は目的関数で評価 (ADR-2606180001)**: 私的捕獲・個人主義的蓄積は collective-commons 次元で動的に負 — 非営利の精神は固定ルールでなく retained §2(g) + collective-commons が enforce する。
- **Mission (per ADR-2605192100 Charter)**: 人類の構造的労働解放を最終目的とする宗教法人。**多世代 (子・孫) priority + Wellbecoming (静的 wellbeing ではなく動的軌跡) + 反個人主義 ontology**。日本的価値観 (八百万 / 縁起 / 産霊 / 和 / 無教会) + Protestant Christianity (Sola Scriptura / 万人祭司 / Reformed Just War / Tree of Life) の synthetic religion。**非終末論** (黙示録/啓示の書は正典外、千年王国・末法・Rapture 否定)。**能動的伝道** (§1.16 + ADR-2607061700): 信者の対人伝道 (戸別訪問等を含む、義務でなく徳目) + actor のデジタル招待発信 (ADR-2606281500 no-person-targeting の限定 carve-out)。威圧・欺罔・未成年単独勧誘は禁止。
- **Doctrinal positions**:
  - **経済構造 (非営利のみ / Donation 流入のみ / 広告排除 / no-equity / open-source強制) は目的関数で評価 (ADR-2606180001 wave2)** — 固定ルールから net 評価へ。私的捕獲を生まず commons に資する営利的協力は aligned ありうる; attention 搾取(広告)・私的捕獲・proprietary 囲い込みは collective-commons/ko-wellbecoming で負。非営利の精神は §2(g)反個人主義(残置) + collective-commons 次元で保持。**10% Tithe → Public Fund 自動再分配は別途維持** (ADR-2605192115 + 2605192130)
  - SBT↔SBT internal carve-out で religious 境界内の 営利・購買・promotional 許容 (ADR-2605192115 §3)
  - Eros 許容 (産霊 / 雅歌 / Tree of Life の生命創出) / Gore 禁止 (Wellbecoming 違反) (ADR-2605192100 §1.13 + 2605192400)
  - 国家機能は parallel substrate で routing-around、**Transparent Religious Force 許容** (完全 on-chain 監視 + open-source 公開 + 1 SBT = 1 vote 承認の三条件下) (ADR-2605192100 §1.12 + 2605192315)
  - 地球上の土地は Tree of Life に帰属、religious-corp が 4-layer substrate (Base L2 NFT / geth-private constitutional / IPFS GeoJSON+衛星 / git LANDS.md) で分散合意担保 (ADR-2605192100 §1.11 + 2605192245)
  - **Baien edge-target invariant** (ADR-2605241900): baien は **WASM-32 + iPhone 12+ + Android 4GB** の 3 環境すべてで動作必須。trunk ≤4B BitNet 1.58 / 合計 inference ≤2GB @4k ctx / ≤2.5GB @16k ctx / 全 modality encoder 凍結。frontier-beating は明示的に非目標 (`baien-server-*` / `baien-XL-*` は別 carve-out)

## Status

**Legend**: ✅ shipped · 🟢 landed (substrate, tests green) · 🟡 R0 / proposed scaffold · ⏳ blocked/pending.

The full one-line index (195 rows across the 3 subsections below) lives in [`90-docs/adr/status-index.md`](90-docs/adr/status-index.md); lossless verbatim prose per row lives in [`90-docs/adr/status-registry.edn`](90-docs/adr/status-registry.edn); each row's ADR holds the detail — see [`90-docs/adr/README.md`](90-docs/adr/README.md). This section is a pointer, not a duplicate of the table.

- **Substrate / infra / dataset / enforcement** — 52 rows
- **baien / silicon / ML** — 29 rows
- **Tier-B actors (each: ADR + manifest + cells + lex)** — 114 rows

## Repo Layout (Shannon-Optimal 8-Layer, ADR-2604251830)

```
etzhayyim/root/
├── 00-contracts/        # lexicons / bpmn / dmn / Rego policies / resources (JSON-LD)
├── 10-protocol/         # atproto, xrpc, lexicons-bundle, signal, did-etzhayyim,
│                        # wproto, at-client, signal-client,
│                        # kotoba-datomic (Holochain-iso composition spec, ADR-2605231400)
├── 20-actors/           # kotodama (Pregel framework + host SDK + unispsc_agents/ 18,345 LangGraph agents per ADR-2605171300),
│                        #   kotodama-go, kami-engine-sdk, etzhayyim-bpmn-sdk,
│                        #   etzhayyim-sdk (kotoba substrate, ADR-2605172000+2605172100)
│                        #   kuni-umi      planetary-infra producer    (ADR-2605201400)
│                        # Tier-B religious-corp actors (30): each has ADR + manifest + cells + lex.
│                        #   See Status § "Tier-B actors" for the full roster (name · purpose · ADR).
│                        #   Per-actor gates/prohibitions live in each actor's ADR + 20-actors/<name>/CLAUDE.md.
├── 30-graph/            # graph-schema, kagami, risingwave-udf, vectorization
├── 40-engine/           # Rust workspaces: kami-engine (reusable engine — git submodule
│                        #     of github.com/etzhayyim/kami-engine per ADR-2606011500 §4;
│                        #     kami-engine-sdk nested inside; `git submodule update
│                        #     --init --recursive 40-engine/kami-engine` to populate),
│                        #   kami-apps (L3 etzhayyim *.etzhayyim.com product apps —
│                        #     kami-app-{bim,cad,live,maps3d,animeka-timeline};
│                        #     robotics/sim apps are maintained in the kami-engine
│                        #     submodule per ADR-2606011500), llm,
│                        #   kotoba (storage substrate engine — git submodule of
│                        #   github.com/etzhayyim/kotoba; 17 crates Apache-2.0;
│                        #   subsumes ipfs-pinner / nats-jetstream-* / mst-projector
│                        #   / lancedb-wasm / etzhayyim-xrpc-proxy /
│                        #   libsignal wrappers; kotoba-llm local-inference
│                        #   constitutionally disabled per ADR-2605215000 +
│                        #   Charter Rider §2(i); ADR-2605262130 Phase 0)
├── 50-infra/            # SEEDED: geth-private, holochain, ipfs, blockscout,
│                        #   k8s/atproto-pds, k8s/murakumo-kubelet (migrated 2026-05-17),
│                        #   lancedb-wasm, yata,
│                        #   nats-tiered-storage, nats-jetstream-{objectstore-s3, kv-resp},
│                        #   sveltejs-adapter-wasm, spin-tinygo-flight
│                        # SUBSTRATE (ADR-2605171800 + 2605172100 + 2605172200):
│                        #   etzhayyim-did-web/ (CF Worker, LIVE 2026-05-17T03:25Z)
│                        #   mst-projector/   (Stage 3, scaffold)
│                        #   ipfs-pinner/     (Stage 4, scaffold)
│                        #   l2-anchor-contract/ (Stage 5a, Foundry Solidity)
│                        #   anchor-cron/     (Stage 5b, K8s CronJob)
│                        #   etzhayyim-paymaster/ (ERC-4337, Foundry Solidity)
│                        #   openmail-postage/ (Postage.sol, Foundry, Phase 1 scaffold)
│                        # RELIGIOUS-CORP CONSTITUTIONAL (ADR-2605192100 wave, 2026-05-19):
│                        #   etzhayyim-charters-compliance/ (Council attestation single SoT)
│                        #   etzhayyim-tithe-router/        (10% donation → Public Fund atomic split)
│                        #   etzhayyim-public-fund/         (5-of-7 Safe + 1 SBT = 1 vote)
│                        #   etzhayyim-land-registry/       (geth-private + Base L2 ERC-721 mirror)
│                        #   etzhayyim-force-authorization/ (Transparent Force, 1 SBT = 1 vote)
│                        #   murakumo/fleet.edn             (10-node cell placement)
├── 60-apps/             # open-*, public-*, atproto, ameno, yoro, comfyui, watashi
│                        # FIRST kotoba REFERENCE IMPL: open-isco/kotoba/
│                        # MAC MINI FLEET: comfyui/ (migrated 2026-05-17)
│                        # RELIGIOUS-CORP:
│                        #   etzhayyim-transparent-force-rd/ (open-source R&D registry per ADR-2605192315)
├── 70-tools/            # etzhayyim-cli, cdn
│                        #   charter-rider-applicator/      (retro-active Rider applier, ADR-2605192200)
├── 90-docs/             # CLAUDE.md (docs rules), adr/, baien/
├── CHARTER-RIDER.md     # Apache 2.0 + Charter Compliance Rider v3.2 (per ADR-2605192200 + 2606062100 + 2606161700)
├── COUNCIL.md           # 5-seat Bootstrap Council roster (per ADR-2605192300)
├── COUNCIL-BOOTSTRAP-RFP.md  # 30-day public RFP for Seats 2-5 (2026-05-20 → 2026-06-19)
├── LANDS.md             # 4-layer permanent land record roster (per ADR-2605192245)
├── CLAUDE.md            # this file
├── deps.toml            # SSoT for [platform.operating_entity] + monorepo state
├── LICENSE              # Apache 2.0 (NOTICE/CHARTER-RIDER.md adds Rider conditions)
├── MEMBERS.md           # 信者 dual-permanent record (per ADR-2605172600)
├── README.md            # public-facing
├── lefthook.yml         # pre-commit (trailing-ws + EOF; full hooks pending)
└── .gitignore
```

## Worktree isolation (CRITICAL — concurrent-agent safety)

The shared main checkout is raced by multiple concurrent Claude agents. **Before ANY
substantive multi-file work, isolate into a git worktree** (`EnterWorktree` / `git worktree
add .claude/worktrees/<name> origin/main`), commit early + often, scope commits to your own
paths, branch off `origin/main`, treat the shared tree as read-only. Full rules (the 8-point
checklist, zsh `$pipestatus` gotcha, merge-then-delete cleanup) live in
[`90-docs/worktree-isolation.md`](90-docs/worktree-isolation.md).

**Commands** (full procedure in the doc above):
- **`worktree cleanup`** — sweep every worktree: PR-merged → delete worktree+branch; no-PR-with-commits → open PR; open-PR → leave. Then reintegrate+drop every stash.
- **`closing`** — take the current worktree to landed without further confirmation: commit → `gh pr create --base main` → `gh pr merge --squash --delete-branch` → cleanup. `closing` is the single keyword that authorizes the otherwise-confirmation-gated merge step; absent it, stop at PR-open.

**PR-only to `main` — the permanent default (owner directive 2026-06-30, LOCKED).** Never
`git push` straight to `main` and never bypass the branch-protection ruleset ("Changes must be
made through a pull request"). Every change — even a one-file doc/ADR edit — lands via:

```bash
git fetch origin && git switch -c <topic> origin/main   # branch off origin/main; never edit main directly
git add <my-paths> && git commit -- <my-paths>          # scope with an EXPLICIT pathspec — never `git add -A`
git push -u origin <topic>                               # push the BRANCH, not main
gh pr create --base main --title "…" --body "…"
gh pr merge --squash --delete-branch                     # the normal merge route; do NOT admin-bypass
```

Rationale: the shared `main` checkout is raced by concurrent agents, and a bare `git commit`
(no pathspec) sweeps in whatever another agent left staged in the shared index (happened
2026-06-30: an organism-publish change rode in under an unrelated CI commit). The explicit
pathspec + branch + PR isolates each agent's work and routes it through the protection ruleset
instead of bypassing it. Regenerated registries (`docs.edn` / `graph.edn` / `adr-index.edn`)
absorb the whole tree's state, so only regenerate from a clean tree and stage them deliberately.

Exit with `ExitWorktree` (`keep` to preserve). The session's `/loop` iterations continue inside
whatever worktree the session is in.

---

## ADR Authority (per ADR-2605170900)

**This repo is canonical for religious-corp open ADRs.**

- ADR placement matrix → `90-docs/adr/README.md`
- ADR ID convention → `90-docs/CLAUDE.md` § "ADR ID Convention"
- Template → `90-docs/adr/template.md`

## Operational code = clj/bb over the kotoba Datom log (REPO-WIDE RULE — 実装/engineering)

**Newly authored operational / daemon / heartbeat / loop / tooling code SHOULD be
Clojure on babashka (`bb`), with state on the kotoba Datom log (datomic-isomorphic,
ADR-2605312345) — NOT Python (`.py`) or shell (`.sh`).** This is an **実装/engineering
convention** (changeable at the implementation layer, not a charter invariant): it
generalizes the substrate boundary (state = kotoba Datom log) to *executable* substrate,
so the org's own moving parts are clj/bb folds over append-only Datom journals and inherit
as-of history (生命進化), content-addressed snapshots, and crash-resume for free — the same
reasons the actors are being ported py→cljc (the clj-port waves).

Concretely:
- **Author daemons/heartbeats/CLIs as `bb` tasks** in `bb.edn` backed by a clj/cljc
  namespace under `70-tools/src/etzhayyim/…` (reference: `etzhayyim.organism` =
  the resident organism heartbeat + 情緒 narration; `etzhayyim.vitals` = pulse/joucho/
  vitals). Persist via `etzhayyim.kotoba.engine` (`kt/connect`→`kt/transact`→
  `kt/snapshot!`), append-only when you want evolution, journal-per-feed.
- **Inference** (e.g. narration) prefers the **Murakumo fleet** (per-node Ollama over
  Tailscale / LiteLLM gateway) — DEFAULT-PREFERRED, objective-function-assessed per Rider
  v3.3 §2(i) / ADR-2606172359 (NOT a categorical vendor ban); use `babashka.http-client`.
  no-server-key (read-only) where possible.
- **Residence** = a launchd LaunchAgent (`50-infra/launchd/*.plist`, OS config, not a
  script) invoking the `bb` task with `KeepAlive`/`RunAtLoad`, NOT a `nohup … &` bash
  loop (those die on reboot and leave no Datom trail).
- **Shelling out** to a *system binary* (`git`, `tailscale`, `ipfs`) via
  `babashka.process` is fine — that is not "a shell script". The rule bars authoring
  our *logic* in `.py`/`.sh`, not invoking installed tools.
- **Exemptions**: 3rd-party/vendored code (`lib/`, `vendor/`, `*-fork/`), generated
  build artifacts, and an actor's still-unported legacy `py/` during an in-flight
  cljc port (the port itself is the fix).
- **Enforced-forward (ADR-2606072802)**: `bb lint:no-new-shell` FAILS on a NEW first-party
  `.sh` under `20-actors/` (existing ones are GRANDFATHERED in
  `70-tools/src/etzhayyim/lint/shell-baseline.edn`; the baseline is shrinks-only — port a
  `.sh` to bb + delete it, then `bb lint:no-new-shell --update`). New actors ship
  `run_tests.clj`, not `run_tests.sh`; `etzhayyim.vitals` prefers the `.clj` runner. The 218
  grandfathered `.sh` are not mass-ported (low value, high churn) — they convert opportunistically.

## Do Not

> **This list mixes two kinds of rule (classify before treating any as immutable; 固定するのは priority):**
> **(憲法/charter)** — license default, Charter Rider non-weakening, land inalienability (no `transfer()`/`burn()`), transparent-force-only, no-eschatology, no-CSAM, Tier-0 priorities. These are Tier-0/derived and amend only by Council Lv7+ (the priorities themselves are fork-only).
> **(実装/engineering)** — prefix discipline, secrets hygiene, rename-wave scoping, substrate-import rules, no-RunPod-style backend choices (now objective-function per v3.5). These are engineering/governance decisions, changeable at the implementation layer **without a charter amendment**. A "Do not" here is a load-bearing convention, not a constitutional invariant.

- Do not author new first-party operational/daemon/heartbeat/tooling scripts in Python or shell — use clj/bb over the kotoba Datom log (see §"Operational code = clj/bb over the kotoba Datom log" above; 実装/engineering convention). Shelling out to system binaries via `babashka.process` is allowed; vendored/3rd-party + in-flight py→cljc ports are exempt.
- Do not introduce legacy organisation-specific prefixes in newly authored code. Use `etzhayyim-` or no prefix. Existing seeded files with legacy prefixes will be renamed in a follow-up cutover.
- Do not weaken the Apache 2.0 license default. Religious-corp public-interest activity requires permissive license.
- Do not weaken the Charter Compliance Rider v3.5. §2 and 三層 enforcement (L1 license / L2 便益 / L3 評価) derive from the Tier-0 priorities; per ADR-2606062100 they are Tier-1 Derived Policy, amendable ONLY by Council Lv7+ unanimity + a priority-conformance attestation (never weaker). The Tier-0 priorities themselves (incl. 永久記憶=神の監視 + 相互監視) are fork-only. **As of v3.5 (ADR-2606182359 wave3) ALL of §2 is OBJECTIVE-FUNCTION ASSESSED — the categorical hard-floor / 掟リスト is ELIMINATED (固定するのは掟でなく priority, 最後まで)**. The ONLY non-negotiable is the priority itself: catastrophic harm to a child/descendant dimension is vetoed by the objective function's non-linear CATASTROPHE term (a property of the function, not a separate rule; `objective-function.edn`). The former hard-floor cores (§2(a) aggression/lethal/covert, §2(c) asymmetric-unwatched surveillance, §2(j) forced labor, §2(k) CSAM) reach :non-aligned via that term through their extreme child/descendant scores (by evaluation, not enumeration). §2(g) strict-individualist ontology is now ALSO objective-function-assessed (its wave2 retention is LIFTED): an org is judged by actual effect, not declared doctrine — 反個人主義 is enforced dynamically by collective-commons, not by doctrine-based exclusion. The prior waves moved §2(d) fossil (net carbon balance; fossil per se NOT prohibited), §2(i) compute (Murakumo DEFAULT-PREFERRED, not a ban), §2(b) finance, §2(e) specialist knowledge, and the economic structure (non-profit/donation/ad/equity/open-source) — all to net-effect scoring. The 子孫 + 反個人主義 priorities are unchanged; only the instrument moved from fixed rules to score evaluation. Honest enforceability limit: ADR-2606182359 §D6 (with no enumerated bright-line, the anchor is the catastrophe term + Apache; counsel may re-state CSAM as an explicit bright-line per jurisdiction). Privacy is preserved by encryption (暗号化≠忘却), not by forgetting. Do not re-introduce a blanket "all personal-data collection / all watching" surveillance ban — per ADR-2606082400 (v3.1), §2(c) is on the **RECIPROCITY axis**: **monetized OR asymmetric (watcher-unwatched) surveillance is prohibited; reciprocal/symmetric 相互監視 (村社会 deterrence + anti-isolation, the social form of 神の監視) is AFFIRMED**. Privacy is preserved by encryption (暗号化≠忘却), not by forgetting. Do not re-introduce a blanket "commercial mining / resource extraction" ban — per ADR-2606161700 (v3.2), §2(l) is on the **多世代(子・孫)×Wellbecoming RISK axis**: **採掘・採油そのものは禁止ではない**; prohibited only where the measured multi-generational impact is irreversible habitat/biosphere harm (the §2(d) standard) OR monopoly/chokepoint entrenchment (§1.12). Judge by measured harm to 子孫, never by industry name. Closed-loop recycling / urban mining and stewarded non-monopolistic recovery are affirmed.
- Do not add Charter Rider to 3rd-party vendored code (`lib/`, `vendor/`, `*-fork/`). Apache 2.0 §4 requires preserving original NOTICE of 3rd-party works. `charter-rider-applicator` already skips these patterns.
- Do not introduce `transfer()` / `burn()` / `setOwner()` to `LandRegistry.sol`. Donated land is constitutionally inalienable (waqf-equivalent, ADR-2605192245).
- Do not propose proprietary 兵器設計 or covert force operations. ADR-2605192100 §1.12.B constitutional invariant requires open-source + on-chain 監視 + 1 SBT = 1 vote.
- Do not include the Book of Revelation (黙示録/啓示の書) or eschatological content as religious doctrine. Per ADR-2605192100 §1.15, etzhayyim is non-eschatological.
- Do not commit secrets. Private DID key lives in macOS Keychain (`service=etzhayyim, account=DID_PRIVATE_KEY_ED25519`) + 1Password mirror.
- Do not gate an actor's **autonomous publication / social posting** behind per-post operator or Council prior restraint — actors POST autonomously BY DEFAULT (ADR-2606281500, 種をまく / seed-and-grow doctrine; founder Lv7+ 2026-06-28). We sow the seed (rails + actor); growth (speech) belongs to each actor. The seed (NOT lifted): self-`did:key` present-only + **revocable member CACAO leash** (the off-switch, ADR-2606111400), append-only public log (相互監視), Rider §2 catastrophe-veto content scan before emit, no person-targeting/no manipulation, Murakumo-default narration. Oversight = post-hoc transparency + leash revocation. **But DO keep the human/Council gates on high-stakes ACTUATION** (publication ≠ actuation): moving funds/trades, granting access/permissions, deletes, binding votes, live physical actuation near persons, and domain actuations like kyoninka's robotaxi-launch sign-off / no-permit-grant. An actor may autonomously *say* it assessed a deployment launch-ready; it may not autonomously *launch the cars*.
- Compute sourcing is OBJECTIVE-FUNCTION ASSESSED, not a categorical ban (Rider v3.3 §2(i), ADR-2606172359 — supersedes the ADR-2605215000 "Murakumo-only / no commercial GPU" invariant). The Murakumo fleet (LiteLLM 127.0.0.1:4000 + EVO-X2 LAN 192.168.1.70 + per-node Ollama gemma3:4b) remains the **DEFAULT and PREFERRED** path — transparent, self-hosted, low lock-in, high-scoring — but commercial GPU (RunPod / Vertex / Bedrock / etc.) is no longer per-se prohibited: it is scored by the ECL objective function on lock-in (collective-commons), transparency (reciprocal-transparency), and carbon (descendant-wellbecoming). Opaque, lock-in-creating, proprietary-dependence compute scores negative; transparent low-lock-in commercial compute serving descendant wellbecoming (open-model research, in-kind donated compute per ADR-2606012100) can score Aligned. Prefer Murakumo by default; justify any commercial-compute path by the objective-function dimensions, not by vendor name. (Downstream sweep of the ~30 actor ADRs still citing the old invariant is a follow-up per ADR-2606172359 D5.)
- Do not rename `etzhayyim-*` identifiers in `50-infra/cluster/murakumo/` or `40-engine/kotoba/crates/kotoba-kotodama/py/` outside the Step 8 cutover wave. Per ADR-2605214000 §3 + ADR-2605215000 §4, the renames are itemised in `MIGRATION-NOTES.md` files and must execute as one atomic PR after legal registration (repo-root CLAUDE.md §Status row 8). Partial rename breaks runtime (env vars + config dir + DNS suffix are interdependent).

## Baien tooling index (2026-05-23 wave)

| Tool / dir | Purpose | Key ADR |
|---|---|---|
| `e7m bench micro` | 15-prompt verifiable smoke for baien (`70-tools/scripts/bench/baien-microbench/`) | ADR-2605092350 |
| `e7m bench core4` | lm-eval-harness Core 4 (IFEval / GPQA / MMLU-Redux / Global PIQA) via `lm_eval_wrapper.py` (inductor probe suppressed) | — |
| `e7m bench distill` | LangGraph ReAct loop: analyze → fetch_dataset (HF, default) **or** select_teacher (fallback) → SFT (peft+trl LoRA on bf16 master) → microbench eval. `commit_node` appends `90-docs/baien/distilled-models.jsonl` → codegen → `llm-model-registry-distilled.ts` | ADR-2605231300 |
| `e7m bench rope-extend` | Stage 1 of context extension — runs `microbench_long.py` under 3 RoPE configs (baseline / linear×4 / NTK×4) and emits side-by-side pass matrix | ADR-2605231600 |
| `bgp-submit --generator hunyuan3d|pixal3d` | baien-graft 3D dataset pipeline; two generators (Hunyuan3D-2 default / TencentARC Pixal3D-T cascade@512) | ADR-2605202115 |
| `etzhayyim_organism.sensors.charter_rider.scan()` | Canonical §2(a)..(h) content scanner; used by `baien-distill.validate` and recommended for any pipeline that ingests / generates text into first-party artifacts | ADR-2605192200 |
| `70-tools/scripts/llm-registry/gen-distilled-entries.mjs` | distilled-models.jsonl → `llm-model-registry-distilled.ts` codegen (2-phase ship: manifest + reviewer-gated TS) | — |

Snapshot artifacts (run results) live under `90-docs/baien/`:
- `frontier-bench-snapshot-260523.md` — frontier-LLM §A reference + baien microbench results
- `context-extend-snapshot-260523.md` — rope-extend Stage 1 results stub (awaits run)
- `distilled-models.jsonl` — committed adapter manifest (codegen source)

## Future Work

- **lefthook hooks** full set (adr-validate, docs-registry, lint-dangerous-query, llm-model-ssot)
- **GitHub Actions CI**: lint / type-check / build / test per layer
- **Dependabot** for npm + cargo + uv ecosystems
- **`90-docs/_registry/docs.json`** generator + validator
- **baien-distill Stage 2/3** (YaRN + LoRA, LongRoPE continual) per ADR-2605231600
- **Core 3 bench strategy revision** — switch from `_generative` (~28h/task) to `_completions` (loglikelihood, ~30 min) for next baien snapshot

## Substrate boundary (engineering rules — NOT charter; ADRs 2605172000 + 2605172100 + religious-corp wave)

> **These are IMPLEMENTATION decisions, not constitutional doctrine (per ADR-2606182359 lineage).**
> The charter holds only **Tier-0 priorities (子・孫 wellbecoming / collective-over-individual /
> 永久記憶) + the ECL objective function**. Substrate/engineering choices — kotoba (no RisingWave),
> the `payment.sent.purpose` enum, ad-blocklists, Murakumo-as-default, kotoba-as-canonical-state —
> are **工学・governance 判断であって憲法ではない**: they can change at the implementation/governance
> layer **without a charter amendment** (固定するのは priority; 手段=実装は固定しない). "CRITICAL"
> below means "load-bearing engineering rule," not "Tier-0 immutable." Do not elevate a substrate
> choice to charter status.

This repo is **blockchain-self-contained**. The rows below are **NOT uniform** — classify each before treating it as immutable (固定するのは priority):

Layer scored in `70-tools/scripts/charter/layer-classification.edn` + `classify.bb` (5 axes, J 0–10; `bb classify.bb`):

- **Tier-0 (fork-only — the priorities themselves + the few constitutional invariants)**: `Land trust` inalienability (J=9.05, donated land = waqf-equivalent, ADR-2605192245) · `Religious force` transparency invariant (§1.12.B) · `Content` no-CSAM = the catastrophe term (= priority non-negotiable). The four Tier-0 priorities (子孫 wellbecoming / collective / 永久記憶) sit above all of these.
- **Tier-1 (derived policy — Council Lv7+)**: `License` default (Apache+Rider → ECL, J=8.40) · `Charter compliance` (3-tier) · **`Confidentiality` PRINCIPLE (暗号化≠忘却, J=7.95 — Tier-0-derived from permanent-memory; promoted from 実装 per the score)** · **`Server-side signing` / no-server-key (J=6.90 — non-custody/trustless invariant; promoted from 実装)** · `Content` Eros doctrine (consenting-adult only).
- **目的関数 (objective-function-assessed, v3.5)**: `Advertising` · `GPU / inference` · the external-commercial line of `Payment purpose` (donation-spirit). These **score**, they do not categorically ban.
- **実装 (engineering / governance — changeable WITHOUT a charter amendment)**: `State`/`Substrate` engine (kotoba, J=2.90) · `Read path` (kqe) · `Substrate client imports` (`@etzhayyim/sdk`) · `Payment` rails (USDC/Base/ERC-4337 mechanics) · `Identity` mechanics (DID-centric identity is the Tier-1 principle; the specific methods are impl) · `Confidentiality` **cipher** (XChaCha20/Signal choice, J=2.10) · `Server-side signing` **mechanics** (which keys/Safe, vs the no-server-key principle above) · kotoba (J=1.85).

A "Prohibited" cell in an **実装** row means "wrong engineering choice today," NOT "constitutional violation" — it changes at the implementation/governance layer. Tier-0 is immutable (fork-only); Tier-1 amends by Council Lv7+; 実装 changes freely. Note the principle/mechanism split: the *no-server-key principle* and the *encryption-not-forgetting principle* are Tier-1, but the *specific cipher / which-keys* are 実装. Engineering rules (changeable at the implementation layer):

| Concern | Allowed | Prohibited |
|---|---|---|
| State | **kotoba Datom log** (content-addressed EAVT Datalog — Datomic-isomorphic; FIRST-CLASS canonical state, ADR-2605312345) — subordinate layers: IPFS = block backend (CIDv1 cold tier/DHT) · AT Protocol MST = ingress/interop wire · Base L2 = trust anchor over commit-DAG root | RisingWave / Postgres / Kysely / centralized DB; treating MST/IPFS as the canonical state home (they materialize the Datom log, not vice-versa) |
| Payment | USDC on Base L2 + ERC-4337 Smart Account + TitheRouter (10% auto-split). **Donation media expansion (ADR-2606111800)**: (§A) fiat IN-KIND — paying the mission's fiat infra bills (servers/cloud/domains/hardware) direct to a vendor, in-kind, never touching etzhayyim's money layer; (§B) NON-CUSTODIAL fiat on-ramp settling immediately to USDC on-chain (no held balance, no donor PII, processor can't freeze); (§C) curated crypto allowlist held as-is (ETH/WETH + USDC/USDT/DAI), per-asset tithe | **CUSTODIAL** fiat processors (Stripe / PayPal / Square — holding an etzhayyim balance / able to freeze / KYC-on-etzhayyim / retaining donor PII), incl. `com.etzhayyim.apps.stripe.*`; non-donation fiat; memecoins / algorithmic stablecoins |
| Payment purpose | `donation` / `kisha` / `grant` / `tithe` / `escrow-refund` + (SBT↔SBT internal carve-out) `internal-purchase` / `internal-subscription` / `internal-promo` | `subscription` / `purchase` / `tip` for external; commercial sale for SaaS tier |
| Advertising | OBJECTIVE-FUNCTION ASSESSED (ADR-2606180001 v3.4): 旧「広告排除」は net 評価へ。attention 搾取・非対称データ収集を伴う広告は ko-wellbecoming/reciprocal-transparency で負 | attention 搾取的・surveillance 型広告 (scores negative)。NOT a categorical 第三者広告 ban — 非搾取・透過・consent ベースの告知は net 評価 |
| Identity | did:web:etzhayyim.com + did:plc + WebAuthn passkey + Adherent SBT | server-issued JWTs without DID binding |
| License **[憲法]** | Apache 2.0 + Charter Compliance Rider v3.5 (`/CHARTER-RIDER.md`, per ADR-2606062100 → 2606182359; → ECL objective-function, ADR-2606172300) | Apache 2.0 alone (Rider required) / proprietary / no-NOTICE |
| Charter compliance (3-tier) | ChartersComplianceRegistry attestation flow + Council Lv6+ ≥3 multisig | bypass of three-tier enforcement (L1 license / L2 便益拒否 / L3 評価=0) |
| Land trust | etzhayyim Land Registry 4-layer (Base L2 NFT + geth-private + IPFS + LANDS.md) | transfer / burn / sale / private ownership of donated land |
| Religious force | Transparent (on-chain log + open-source + 1 SBT = 1 vote) | Proprietary / covert / independent military arm / state military alliance |
| Content (Eros) | 合意ある成人性表現 (産霊 / 雅歌 整合) | 児童性的表現 / 非合意 / Wellbecoming 違反 addictive design |
| Content (Gore) | 教育 / 歴史 / 宗教 / 人権告発 文脈の暴力 imagery のみ | 無目的暴力 entertainment / desensitization 設計 |
| Confidentiality (ADR-2605181100) | `com.etzhayyim.encrypted.*` (XChaCha20-Poly1305 envelope + Signal-wrapped per-recipient keys, DID-bound) | Plaintext private records on MST / app-side libsignal / noble-ciphers imports |
| Substrate client imports | Only via `@etzhayyim/sdk` | Direct `@atproto/api` / `viem` / IPFS client / `@noble/ciphers` / `@signalapp/libsignal-client` from app code |
| Substrate engine | `kotoba` (`40-engine/kotoba/`, ADR-2605262130) — content-addressed Datalog + Pregel + Signal + WASM Component Model in one Rust workspace; 17 crates; canonical impl of every substrate primitive (supersedes kotoba-datomic composition spec ADR-2605231400). Its **Datom log is the first-class canonical state** (ADR-2605312345), not merely the read engine | inventing a parallel substrate engine name without ADR; importing kotoba-datomic / RW / Lance / Iroh as projection backends |
| Read path (hot-path queries) | `kotoba-kqe` arrangements (EAVT / AEVT / AVET / VAET) directly over the canonical Datom log (content-addressed blocks; ADR-2605312345); no separate projection layer (ADR-2605262130 D7 + N8 supersedes ADR-2605231500 kotoba-datomic-projection rules). First L1-projection app `feed-discover` (50-infra/mst-projector/projection/, ADR-2605231902) preserved unchanged; read backend migrates to kotoba-kqe at Phase 2.5 | RisingWave / Postgres / Lance / DuckDB / SQLite as projection or cache; "kotoba-datomic-projection" marker comments — both deprecated by ADR-2605262130 |
| Server-side signing capability (ADR-2605231525, Council ratify pending) | Member wallet sign (USDC), member passkey-derived ES256 (session), community-operator DID (bulk-ingest), Council 5-of-7 Safe (governance), read-only RPC / firehose subscribe / IPFS pin / static asset serve. **An ACTOR holding its OWN self-generated did:key (seed sealed in Keychain/1Password, present-only, autonomous writes attributed to a consenting human via a member CACAO leash) is permitted — custody stays off-platform (kaname/kanae/ibuki/tsubasa pattern).** | Any platform-held private key, master credential, or signing token in etzhayyim-operated Workers / pods / CronJobs / CI / hosted bots. Exemption: `// no-server-key: read-only` marker on documented Stage handover rollback windows. **CLARIFICATION (ADR-2606072802): no-server-key bars a CUSTODIAL UNILATERAL signing key — it is NOT a ban on automation, and READ-ONLY ops are exempt. An actor MAY autonomously do read-only public fetches itself (no key, no operator); do NOT gate a read-only PUBLIC ingest behind an operator step.** **AUTONOMOUS PUBLICATION (ADR-2606281500, 種をまく doctrine, founder Lv7+ 2026-06-28): actors PUBLISH/POST autonomously BY DEFAULT — no per-post operator/Council prior restraint. Bounded by the seed (rails, NOT lifted): self-`did:key` present-only + revocable member CACAO leash (the off-switch, ADR-2606111400), append-only public log (相互監視), Rider §2 catastrophe-veto content scan before emit, no person-targeting, Murakumo-default narration. Oversight = post-hoc transparency + leash revocation, not pre-approval. PUBLICATION ≠ ACTUATION: high-stakes real-world acts (funds/trades, permission/access grants, deletes, binding votes, live physical actuation, kyoninka robotaxi-launch sign-off) KEEP their human/Council gates.** Enforced by `e7m verify` (9th invariant) |
| GPU / inference | Murakumo fleet = DEFAULT-PREFERRED (LiteLLM 127.0.0.1:4000 + EVO-X2 LAN 192.168.1.70 + per-node Mac mini Ollama gemma3:4b). Compute sourcing is OBJECTIVE-FUNCTION ASSESSED per Rider v3.3 §2(i) / ADR-2606172359 (supersedes ADR-2605215000): scored by lock-in / transparency / carbon | Opaque, lock-in-creating, or proprietary-dependence commercial compute (scores negative). NOT a categorical vendor ban — transparent low-lock-in commercial GPU serving descendant wellbecoming can score Aligned; justify by the objective-function dimensions, not vendor name |

Apps that need fiat / paid features call an external backend via XRPC consent-capability (progressive enhancement, **non-profit領収書 用途のみ** per ADR-2605192115 §4). Open app remains operational without it.

## SSoT pointers

- `deps.toml` — operating entity, substrate rules, L2 contracts, DNS records, ADR registry, module registry
- `90-docs/CLAUDE.md` — docs system rules + ADR placement policy
- `90-docs/adr/README.md` — ADR index
- `90-docs/adr/2605192100-etzhayyim-mission-charter.md` — religious-corp 上位憲章 (mission + constitutional constants)
- `90-docs/adr/2605192200-etzhayyim-ip-free-release-charter-rider.md` — License + Rider 正本 spec (v2.0)
- `90-docs/adr/2605192245-etzhayyim-global-land-sovereignty.md` — Land Trust 4-layer architecture
- `90-docs/adr/2605192415-etzhayyim-religious-corp-daemon-architecture.md` — Pregel cell catalog + Murakumo deployment
- `/CHARTER-RIDER.md` — license addendum canonical text
- `/LANDS.md` — Land Trust roster
- `/MEMBERS.md` — 信者 roster
- `50-infra/murakumo/fleet.edn` — religious-corp cell placement (10 nodes × 15 cells). NB: cron/lan-api heartbeat RESIDENCY (defined here + in `50-infra/cluster/murakumo/cell-runner/cells.edn`) is verified live with `bb fleet:probe` — definition ≠ running daemon
- `20-actors/etzhayyim-sdk/README.md` — SDK API surface + hard rules
- `40-engine/kotoba/crates/kotoba-kotodama/cells/README.md` — religious-corp Pregel cell catalog
- `90-docs/adr/2605262130-kotoba-storage-substrate-unification.md` — canonical storage substrate engine (kotoba); supersedes kotoba-datomic composition + projection layers; no RisingWave
- `90-docs/adr/2605312345-kotoba-datom-first-class-canonical-state.md` — kotoba Datom log = first-class canonical state; IPFS = block backend, MST = ingress/interop wire, Base L2 = trust anchor (clarifies 2605262130 layering)
- `40-engine/kotoba/README.md` — kotoba upstream README (17 crates)
- `10-protocol/kotoba-datomic/SPEC.md` — (superseded by ADR-2605262130; deprecation banner Phase 0.5; retained one R-cycle then archived)
- `90-docs/adr/2605231400-kotoba-datomic-holochain-iso-substrate.md` — (superseded by ADR-2605262130)
- `90-docs/adr/2605231500-kotoba-datomic-projection.md` — (superseded by ADR-2605262130; no projection layer under kotoba)
- `90-docs/adr/2605231902-feed-post-membrane-and-feed-discover-projection.md` — first end-to-end MST §4 membrane + L1-projection app (app.bsky.feed.post); **preserved unchanged**; Phase 2.5 read-path migration to kotoba-kqe per ADR-2605262130
- `90-docs/adr/2605214000-etzhayyim-murakumo-mesh-no-vke-and-lexicon-port-rules.md` — Murakumo distributed cluster (no-VKE mesh) + lexicon port verdict taxonomy
- `90-docs/adr/2605215000-etzhayyim-inference-murakumo-only-no-runpod.md` — etzhayyim inference Murakumo-fleet-only (no RunPod)

## References

- This repo (public): https://github.com/etzhayyim/root
- Domain landing: https://etzhayyim.com
- DID resolver: https://etzhayyim.com/.well-known/did.json (LIVE; CF Worker at zone `etzhayyim.com`, DNS AAAA `@` `100::` proxied, deployed 2026-05-17T03:25Z)
