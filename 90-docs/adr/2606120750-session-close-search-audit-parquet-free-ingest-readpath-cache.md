---
id: adr-2606120750-session-close-search-audit-parquet-free-ingest-readpath-cache
title: "ADR-2606120750: Session close — search-actor audit → parquet-free CC ingest → kotoba read-path resident cache LIVE"
status: active
doc_type: adr
topic: session-close-search-readpath
authoritative: false
last_verified: 2026-06-12
priority: 5.0
axis: architecture
weight: 0.50
priority_note: "Documentation-only session-close record for the 2026-06-11 session: live audit of the hybrid web search actor, parquet elimination from the CC ingest wire (ADR-2606111900), and the kotoba#111 read-path resident cache shipped + DEPLOYED to the live :8077 node (cc.status 325s→0.20s, search.web 333s→0.37s)."
authoritative_for:
  - session-close record for the 2026-06-11 search/ingest/read-path session
depends_on:
  - adr-2606111900-cc-wet-direct-datom-ingest-no-parquet
  - adr-2606012300-kotoba-hybrid-web-search
related:
  - adr-2605312345-kotoba-datom-first-class-canonical-state
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2606041151
supersedes: []
superseded_by: []
---

# ADR-2606120750: Session close — search-actor audit → parquet-free CC ingest → kotoba read-path resident cache LIVE

**Status**: active (documentation-only session-close record)
**Date**: 2026-06-12 (session of 2026-06-11)
**Deciders**: Jun Kawasaki

# Context

起点質問: 「etzhayyim.com の search actor は google scale の検索エンジン、
crawler, spider は設計、動作している?」。1 セッションで監査 → 欠落の補完 →
発見したスケーリング壁の根治 → 本番反映まで到達した。

# Session arc (all landed)

## 1. Live audit — Google-shaped: YES / Google-scale: NO / crawler: 無し (by design)

ADR-2606012300 のハイブリッド検索 (BM25 + IVF semantic + PageRank + RRF) は
実装済みで `:8077` の live kotoba-server に組込み済みと**実測で**確認
(operator JWT で `cc.status` / `search.web` を実呼び出し)。ただし
**コーパスは完全に空** (chunks 0 / bm25 0 / pagerank 0) — 「エンジンは回って
いるが何も索引していない」が正直な答えだった。crawler/spider は意図的に
存在しない (CC ingest のみ)。

## 2. parquet-free 永続化の実証 (質問「parquet ではなく kotoba datomic, ipfs で永続化したい」)

監査: 永続化は最初から Datom log (canonical) + IPFS block backend
(ADR-2605312345) で、parquet は `cc.ingest` の**入力ワイヤ**にしか存在しな
かった。汎用 `datomic.transact` (EDN tx) で `cc:2026-12:chunks` に
`cc/chunk/*` datoms を直書き → `search.reindex` → `search.web` ヒット
(CJK バイグラム含む) を e2e 実証。commit block + 全 6 index root が Kubo に
dag-cbor として実在 (`dag get` 可読) を確認。

**発見**: 2026-06-03 の disk-full で cold-put が **14,436 件 silent fail**
していた (fire-and-forget)。`KOTOBA_FS_BLOCKS_DIR` (ADR-2606041151 A) か
ディスク監視が大量 ingest の前提。

## 3. cc-direct-ingest — parquet を入力ワイヤからも排除 (ADR-2606111900, PR #1632)

pure-stdlib WET ingester (`70-tools/scripts/cc-direct-ingest/`): CC 公開 WET
を有界 HTTP ストリーミング → 行境界チャンク → `datomic.transact`。
**multi-member gzip バグを実地検出・修正** (CC の .gz は 1 record = 1 gzip
member — 単一 decompressobj では warcinfo で止まり 0 page)。live e2e:
CC-MAIN-2025-47 実ページ **137 chunks + BM25 30,507 terms** 着地、
`search.web` が実 CC ページにヒット。15 unit tests。follow-up PR #1639 で
5xx/timeout retry + backoff (決定的 subject = 冪等再送)。

## 4. R0 read-path 壁の発見 → kotoba#111 で根治 → 本番 LIVE

実 ingest で壁が露出: ~30k datoms で **`cc.status` 325s / `search.web` 333s**
(リクエスト毎の full commit-chain replay)。修正 = `current_db_for_graph`
(20 呼び出し元の共通ヘルパ) を transact 側既存の per-graph resident cache
(`datomic_live_slot`) から配信、miss 時のみ 1 回 `db_from_head` (CEAVT
O(state) fast path) + 再シード。回帰テスト追加、main lineage で
**455/455 tests green**。

**Deploy**: release build → `~/.local/bin/kotoba-server` 差し替え
(バックアップ `.bak-pre-readfix`) → launchd 再起動 → 実測:

| read | before | after (warm) |
|---|---|---|
| `cc.status` | 325s 毎回 | **0.20s** |
| `search.web` | 333s 毎回 | **0.37s** (実ヒット, CJK 含む) |

cold は再起動後 1 回のみ (設計どおり)。再起動後もコーパス無傷 = IPFS 永続化
の実地証明。**ノード DID は再起動で Keychain 由来
`did:key:z6MktEjtemApq4cjE2DwpHWtaphnXYwtXY3YEiyK921yziQz` に変わった**
(旧プロセスは Keychain 投入前 identity を保持していただけ)。

## 5. 整備 (全 merge 済み)

- **Pin 事故の発見と収束**: monorepo の kotoba pin `46e0bdaa` は sibling の
  feature branch (`feat/dna-integrity-engine-hook`) のコミットで upstream
  main に不在 → kotoba#111 を origin/main からの clean cherry-pick に作り
  直して merge し、pin を upstream main `4056912b` へ収束 (PR #1642、#1402
  前例)。dna-integrity は feature branch に無傷 (monorepo 参照は docs のみ)。
- **substrate-remediation-audit の非決定性バグ修正** (PR #1639): full-tree
  audit が populate 済み submodule の中まで walk し、worktree で
  `git submodule update --init` しただけで pre-push が 14 件の偽 "NEW"
  violation で落ちた → gitlink `.git` ファイル検出で nested repo をスキップ。
- worktree / branch 全片付け (merged のみ削除、CLAUDE.md 手順)。

## 6. Incident (closing 中に発見・修復): PR #1680 による main tree-wipe

本 session-close の landing 中、**origin/main がほぼ空になっている**のを検出
(reset --hard origin/main で worktree が 40-engine だけになった)。原因 =
PR #1680「chore(kotoba): bump pin」— 意図は 1 行の gitlink bump だったが、
commit された tree は **77,504 files / 10,022,515 deletions(-) / 1
insertion(+)** で 40-engine 以外を全削除していた (壊れた shared worktree から
の commit — root CLAUDE.md §Worktree isolation が警告するまさにその failure
mode)。**修復 = PR #1682**: parent `f808a379f2` の full tree を復元しつつ
#1680 の意図した pin (`1083e6e4`) は保持 — fix branch の対 parent diff が
gitlink 1 行のみであることを commit 前に検証してから admin-merge。main は
wipe から修復まで約 30 分で復旧。教訓: pin-bump のような「1 行 PR」でも
merge 前に `files changed` を見る / 壊れた tree からの commit は wholesale
になる。

# Open / next

- **semantic leg**: `cc/embed/*` は Murakumo embed パス (既存 `cc.ingest`
  経路) — transact 直書きでは付かない。
- **authority leg**: WET にリンク無し — WAT / CC host-level webgraph ingest
  が次の data increment (ADR-2606012300 と同じ deferral)。
- **write-side scaling**: commit が corpus 成長で 21ms→9s (read は治った、
  write の ProllyTree/Kubo 書き込みコストは残る)。大規模 ingest は Rust
  `cc.ingest.wet` endpoint (R1 候補) + `KOTOBA_FS_BLOCKS_DIR`。
- **dna-integrity re-pin**: sibling の kotoba PR が main に landed したら
  pin を再 bump。
- 旧ノード DID `did:key:ze2e16…` を参照していた箇所があれば Keychain DID へ
  追従 (operator JWT の `sub`)。

# References

- ADR-2606111900 (CC WET direct datom-native ingest — 本セッションの authoritative design)
- ADR-2606012300 (kotoba hybrid web search)
- etzhayyim/root PR #1632, #1639, #1642 / etzhayyim/kotoba PR #111 (+ live benchmark comment)
- `70-tools/scripts/cc-direct-ingest/{ingest_wet.py,test_ingest_wet.py,README.md}`
