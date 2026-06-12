---
id: adr-2606121225-session-close-worktree-cleanup-pr-merge-ruleset-bypass
title: "ADR-2606121225: Session close — worktree/branch cleanup sweep + open-PR review & merge wave + main ruleset admin-bypass governance"
status: active
doc_type: adr
topic: session-close-cleanup-merge-governance
authoritative: false
last_verified: 2026-06-12
priority: 5.0
axis: governance
weight: 0.50
priority_note: "Documentation-only session-close record for the 2026-06-12 cleanup/merge session: 18 merged-or-superseded local branches deleted, 3 preservation PRs opened, 3 PRs reviewed+merged (#1685/#1686/#1689 incl. toml→EDN conflict port), #1687 closed as superseded, and the main ruleset unmergeable-deadlock resolved by founder decision (review rule kept + RepositoryRole-admin bypass)."
authoritative_for:
  - session-close record for the 2026-06-12 worktree-cleanup + PR review/merge + ruleset-bypass session
depends_on:
  - adr-2606121143-deps-edn-line-split-canonical-format
related:
  - adr-2606110955-session-close-pr-backlog-merge-sweep
  - adr-2606111824-session-close-review-merge-wave-adr-id-races
  - adr-2606111830-yabai-kotoba-datomic-checkpointer-close
supersedes: []
superseded_by: []
---

# ADR-2606121225: Session close — worktree/branch cleanup sweep + open-PR review & merge wave + main ruleset admin-bypass governance

**Status**: active (documentation-only session-close record)
**Date**: 2026-06-12
**Deciders**: Jun Kawasaki (founder, Council Lv7+ 1/1)

# Context

共有 checkout に 24+ のローカルブランチと 6 worktree が滞留していたため、
CLAUDE.md §「worktree cleanup」コマンド仕様どおりの掃引を実行し、続けて
open PR 全件 (4 件) の review & merge を行った。途中、main ruleset の
当日変更により**誰も PR をマージできないデッドロック**が発覚し、founder
判断で解消した。本 ADR はその記録である。

# Session arc (all landed)

## 1. Worktree cleanup sweep

- **削除 (PR MERGED 確認済み) 17 本**: kotoba-pin-r3 (#1680) / session-close-2606110955 (#1596)
  / closing-bunken (#1498) / deepen-cleanroom-l3 (#1475) / hydrogen-electrolysis (#1598)
  / kotoba-bump-workspace-roots (#1618) / kadode (#1658) / l5-specialized (#1535)
  / seigyo×3 (#1635/#1653/#1641) / ibuki-delegation (#1593) / meeting-recorder (#1590)
  / ndl-datomic-legal-w1 (#1493) / open-ot-device-in-loop (#1568) / tedai (#1548)
  / toml-to-edn-migration v1 (#1636 CLOSED — merged の v2 #1637 に置換済み)。
  squash-merge 運用のため `git branch -d` は通らず、PR MERGED を根拠に `-D`。
- **保全 PR 化 (PR なし + commits ahead) 3 本**: #1686 fleet-refactor-clj
  (リモートにコピーのない 20 commits)、#1687 cleanroom-l5-maturity (同 25 commits、
  stale 注記つき)、#1689 codex/yabai-murakumo-persistence (push 済み 13 commits)。
- **残置 (現役/OPEN)**: kaiyaku-r0 (#1624 CLOSED 後も wave 40 まで当日進行中、
  origin 同期済み)、hinagata-coverage-wave-4 (#1685)、deps-edn-linesplit
  (未コミット作業中と判断して残置 → owner が掃引中に #1688 として commit→merge。
  **残して正解**)、ci/tree-guard (掃引中に owner が #1684 merge + 自己清掃)。
- **不可 1 本**: 共有 checkout の current branch `chore/toml-to-edn-migration-v2`
  (#1637 MERGED) は、sibling の未コミット作業 (deps.edn / pnpm-lock /
  kotoba submodule) が `git checkout main` を塞ぐため stash せず残置。
  共有ツリーがクリーンになった時点で削除する。

## 2. Open-PR review & merge wave (4/4 処理)

- **#1685 hinagata coverage** (+2,554): MERGE-SAFE — 9 法令追加、EDN valid
  (1,064 nodes parse)、全 URL 公的ソース。→ squash MERGED。
- **#1686 fleet-refactor** (+8,215/−0): MERGE-SAFE — 能力ベース動的ノード同定
  (DHCP 腐敗 .70→.22 の根治)、credential 埋め込みなし、Murakumo-only 準拠、
  失敗 unit は明示的 `port-failed` stub。→ squash MERGED。
- **#1689 yabai murakumo persistence** (+237/−25): MERGE-SAFE — no-server-key
  維持 (KOTOBA_TOKEN は launchd env のみ)、SQLite fallback 排除、Tor=public-exit
  / BitTorrent=case-bound のみ。**CONFLICTING を解消してマージ**: ブランチの
  `cells.toml`/`fleet.toml` 編集 (yabai cell 登録 3 箇所) を、main 側 #1637 の
  toml→EDN 移行後の `cells.edn`/`fleet.edn` へ移植 (単一行 EDN への構造編集 +
  paren-balance 検証)。kotoba submodule は main の新 pin (branch pin の子孫) を採用。
  CI 全緑 (tree-guard 含む) 確認後 squash MERGED。
- **#1687 cleanroom-l5-maturity**: **CLOSE-AS-SUPERSEDED** — 06-09「82 L5」時点の
  スナップショットに対し main は 171 L5。サンプル比較 (algolia/openai-compat) でも
  ブランチ側が旧版で、マージは −14,152 行の退行。固有ファイルは orthogonal な
  インフラ残骸のみ (confidence 95%)。コミットは origin + PR refs に保全。

## 3. main ruleset デッドロックと admin-bypass 決定 (governance)

**発見**: main ruleset (id 16514951, 2026-05-18 作成) が **2026-06-12 11:55 JST に
「approving review 1 件必須・bypass actor なし」へ更新**されており、#1688 (11:55 直前、
review 0 で merge 成功) を最後に **誰も PR をマージできない状態**になっていた —
GitHub は PR author の自己承認を禁止し、本 org の write 権限者は実質 founder
1 名 (com-junkawasaki) のため、「レビュー必須」はどう構成しても単独運用では
充足不能。**変更者は特定不能** (org audit log は Enterprise 限定で 404)。

**決定 (founder 1/1, 本セッション)**: 「admin のレビューを必須にできるか」という
要望に対し、GitHub に該当機能がない (self-approval 禁止が常に優先) ことを確認の上、
最も近い意味論として **review-1-required ルールは維持しつつ
`bypass_actors: [{actor_id: 5 (RepositoryRole admin), bypass_mode: "always"}]` を追加**。

- admin の `gh pr merge --admin` 実行 = founder の明示的 sign-off として機能する。
- bypass 行使は ruleset insights に記録され、相互監視 (Tier-0 永久記憶) と整合。
- 非 admin の write 権限者 (将来の Council seat 等) には review 1 件必須が残る。

**Open**: 11:55 の ruleset 変更の actor / 意図は未特定。意図的な governance
強化だった場合に備え、本 ADR が変更内容と理由を on-record にする。

## 4. 既存バグの修正 (merge 内で同梱)

`deps.edn` の `[modules]` が toml→edn 移行で消えた
`70-tools/scripts/lint/verify_deps_toml_paths.py` を参照したまま (NEW DRIFT 1) で、
`deps-edn-canonical` pre-commit hook が **deps.edn を stage する全コミットを
ブロックする状態**だった (main 由来、#1689 merge とは無関係と diff 0 行で確認)。
`verify_deps_edn_paths.py` へ 1 パス修正し、hook を bypass せず正攻法で通過。

# Lessons

- **zsh `$pipestatus` 罠を再踏**: hook の exit を `cmd | head; echo $?` で読み
  「成功」と誤判定 (CLAUDE.md 既載の gotcha)。exit code はパイプ前に取ること。
- 掃引中も sibling agent は動き続ける (tree-guard / deps-edn-linesplit が
  掃引中に owner 側で merge)。「未コミット作業のある worktree は消さない」
  ルールが今回も正しかった。
- toml→EDN 移行 (#1637) を跨ぐ古い PR の conflict は「toml の編集を EDN へ
  移植 + toml は削除に従う」が正手。単一行 EDN への構造編集は anchor 一意性
  assert + paren-balance 検証をセットで。

# Consequences

- ローカルブランチは 現役 5 本 (main / v2 / kaiyaku-r0 / fleet-refactor /
  hinagata) + worktree 3 つまで縮減。open PR は 0 件。
- main ruleset は「review 必須 + admin bypass」構成が standing。変更には
  本 ADR の追補を要する。
- deps.edn の path audit (verify_deps_edn_paths.py) が再び green。

# Alternatives Considered

- **ruleset の review 必須を 0 に戻す**: 11:55 変更の意図 (governance 強化の
  可能性) を尊重して不採用。bypass 方式ならルール本体を残せる。
- **bot/machine account による approve**: 自己承認の演出にすぎず、監査上の
  意味が bypass 記録より弱い。不採用。
- **#1687 の salvage cherry-pick**: 固有ファイルが orthogonal なインフラ断片
  のみで、必要になった時点で個別ブランチで拾い直す方が安全。不採用。
