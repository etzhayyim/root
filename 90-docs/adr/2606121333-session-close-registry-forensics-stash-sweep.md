---
id: adr-2606121333-session-close-registry-forensics-stash-sweep
title: "ADR-2606121333: Session close — deps.edn 行分割 hardening → registry forensics (sonae/abaki 復元) → stash 完全 sweep"
status: active
doc_type: adr
topic: session-close-registry-forensics
authoritative: false
last_verified: 2026-06-12
priority: 5.0
axis: architecture
weight: 0.50
priority_note: "Documentation-only session-close record for the 2026-06-12 後半 arc: deps.edn line-split + 破損修復 (ADR-2606121143) → path 監査移植 → sonae 備え 15 files を stash から完全復元 → abaki 暴 登録復元 → 5 stash の会計→archive→drop。"
authoritative_for:
  - session-close record for the 2026-06-12 registry-forensics/stash-sweep arc
depends_on:
  - adr-2606121143-deps-edn-line-split-canonical-format
related:
  - adr-2606120750-session-close-search-audit-parquet-free-ingest-readpath-cache
  - adr-2606091200-sonae-pre-disaster-foresight-tier-b-actor-r0
  - adr-2606073100-abaki-anti-monopoly-intelligence-membrane-r0
supersedes: []
superseded_by: []
---

# ADR-2606121333: Session close — deps.edn hardening → registry forensics → stash 完全 sweep

**Status**: active (documentation-only session-close record)
**Date**: 2026-06-12
**Deciders**: Jun Kawasaki

# Context

ADR-2606120750 (前半 arc: 検索 audit → parquet-free ingest → read-path cache
本番反映 + #1680 main 復旧) の続き。起点は「deps.edn の行分割フォーマット化を
検討」— 検討が forensics に発展し、**失われたと思われた actor 2 体の復元**と
**stash 全 5 件の損失ゼロ sweep** まで到達した。

# Session arc (all landed)

## 1. deps.edn canonical line-split + 破損修復 (ADR-2606121143, PR #1688)

1 行 ~1.3 MB の deps.edn を canonical 行分割 (922 行) へ。実装過程で
**deps.edn が数 merge にわたり invalid EDN だった**ことを発見 — 生 bracket
カウントの string-surgery append が 3 エントリを別エントリの title 文字列内部
へ挿入していた (自分の #1679 分も含む)。pure-stdlib formatter
(`format-deps-edn.py`: token 列保存 + 冪等性 assert) + **`--append-adrs`
構造的 append** (parse 必須 = 壊せない) + `deps-edn-canonical` pre-commit
gate (parse = 破損 gate 兼任)。最後の valid 版から全 diff 純挿入を検証して
誤位置 3 エントリ再配置、**データ喪失ゼロ**。19 tests。

## 2. orphan-path 監査の deps.edn 移植 (PR #1690)

deps.toml 消滅で死んでいた verifier を `verify_deps_edn_paths.py` として移植。
marker/duplicate 意味論継承 + **決定性の新設** (`.gitmodules` root 配下 =
submodule-unverifiable / URL・`~`・絶対パス = external — populate 状態依存の
偽 drift 143 件を排除) + **shrink-only baseline ratchet** (legacy drift 12 件
凍結、NEW drift のみ FAIL)。10 tests。初回監査が次の発見を生んだ。

## 3. sonae 備え の復元 — 「未 commit のまま wipe」は早計だった (PR #1693 → #1694)

path 監査が「登録あり・実体なし」の sonae 三点セットを検出。第一結論
(#1693) は「shared checkout の untracked が wipe され消失、(reserved) マーク」
— しかしユーザー指摘で stash/dangling まで深掘りした結果、**stash@{0} の
untracked-files commit `7bb422cb86` に 15 files 完全生存**を発見 (toml→edn
migration session の `git stash -u` が他 session の loose files を巻き込んで
いた)。原本どおり復元: ADR 2606091200 + actor 一式 + lexicon 7 本 + tests
(20/20 pass)。適合修正 1 点のみ — 原本は pre-commit gate 未通過で Lexicon v1
違反 4 件 (`number` 型) → ADR-2605190900 慣例で整数化 (`magnitudeE2` ×100 /
`depthM` / whole units)。registry 再整合 ((reserved) 解除 + CLAUDE.md 行 +
index 行)。

## 4. stash 完全 sweep — 会計 → archive → drop (PR #1695)

全 5 stash を「全内容を main と照合 → 未着陸物を回収 → top-commit を
`stash-archive/*` branch として push → drop」で処理。**stash list は 0 件**。

- migration ×2: sonae 回収済み / rasen deps.toml・CLAUDE.md 行は superseded
  (main に edn 版・新版あり) / warifu-零利 ISO-8583 は owner-call (archive 保全)
- cleanroom-l3: chaos_monitor profile + milestone — **全 landed**
- yoro-search-xrpc: 27 files 中 **1 件回収 = abaki 暴 の ADR index 行** —
  ADR と `20-actors/abaki` は landed 済みなのに登録 3 点 (index/deps.edn/
  CLAUDE.md) が全欠落していた。3 点とも復元。
- docs-branch (25,016 files / 1.87M deletions の壊れた tree): main 不在 816
  件中 **765 = `magatama`→`kotodama` rename 前の旧名**、残りは `ai-gftd-*`
  (org rename 前)・旧 deps.toml・junk — 回収価値なし。

## 5. worktree cleanup ×2

hinagata-coverage-wave-4 (merged #1685、迷子の生成物 1 件は /tmp 退避) を削除。
fleet-refactor-clj / kaiyaku-r0 / tanemaki は active session のため不可触
(fleet-refactor は **merged PR の branch 上で作業継続中** — 本人の新 PR 待ち)。

# 教訓 (運用へ)

1. **registry と実体の整合は双方向に監査が要る**: path 監査 (登録→実体) が
   sonae を、stash 会計 (実体→登録) が abaki を見つけた。「ADR ファイルは
   あるが未登録」の逆方向検査が verifier の次の増分候補。
2. **`git stash -u` は shared checkout では他 session の untracked を飲む** —
   消失調査では ref/tree 走査に加えて stash 第3親 commit への pickaxe を必ず
   含めること (worktree cleanup 手順への追記候補)。
3. 1 行 registry は conflict 源であるだけでなく**破損隠蔽装置**だった。
   構造 (canonical line-split + parse gate) で fix し、運用ルール
   (`--append-adrs` 経由のみ) で再発を塞いだ。

# Open / next

- verifier 逆方向検査 (ADR ファイル存在 × :adrs 未登録の検出)。
- duplicate ADR id 13 件の reconciliation (既知の id race、機械可読化済み)。
- `stash-archive/*` 5 本は 1 R-cycle 保持後に削除検討 (warifu ISO-8583 の
  owner 判断が出たら)。
- baseline 残 9 drift (karute/vultr/moemoekyun recipes/2606032330/Formula) は
  各 owner へ。
- fleet-refactor-clj session の merged-branch 継続作業 → 新 PR 化。

# References

- ADR-2606121143 (deps.edn line-split — 本 arc の authoritative design)
- etzhayyim/root PR #1688 #1690 #1693 #1694 #1695
- `stash-archive/{toml-edn-migration-untracked,toml-edn-migration-wip,cleanroom-l3-blocking-edits,yoro-search-xrpc-wip,docs-branch-messy-state}`
