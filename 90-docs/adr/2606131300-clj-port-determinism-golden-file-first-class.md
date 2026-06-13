---
id: adr-2606131300-clj-port-determinism-golden-file-first-class
title: "ADR-2606131300: Clojure 移植の検証基準 — 決定性 + golden-file を一級、python3 byte-parity は in-development 便宜オラクル"
status: proposed
doc_type: adr
topic: clj-port-determinism-golden-file-first-class
authoritative: true
last_verified: 2026-06-13
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - 20-actors/*/methods/*.cljc
  - bb.edn
depends_on:
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605312345-kotoba-datom-first-class-canonical-state
  - adr-2606120500-fleet-clojure-refactor-and-gemma4-cpt
related:
  - adr-2606101200
supersedes: []
superseded_by: []
---

# ADR-2606131300: Clojure 移植の検証基準 — 決定性 + golden-file を一級、python3 byte-parity は in-development 便宜オラクル

**Status**: proposed
**Date**: 2026-06-13

## Context

Python→Clojure(.cljc, pywasm-ready)アクター移植は PR #1706 / #1714 / #1716 (+回収 #1718) で
18 アクター・621 tests / 12,428 assertions を達成し、以後 next-tier(actor 計算メソッド:
generate / plan / query / validate / esign / maturity / cid …)へ拡大している。

この移植は一貫して **python3 と byte-identical**(`cmp` 空 diff・CID 文字列一致・siphash13 /
BLAKE2b の bit 一致)を達成基準としてきた。ここで「なぜ byte-identical か。過去データは
開発段階で消えてよいのに」という問いが founder から提起された。正しい問いであり、
byte-identical には **2つの独立した理由**が混在していたことを明文化する。

### 理由A — CID チェーン継続(移行時の連続性)

kotoba は content-addressed Datom log(commit-DAG, ADR-2605312345)。Python が積んだ**既存**
ログの上に Clojure が追記して `verify_chain` / crash-resume を保つには「同じ入力→同じ CID」
が要る。1 byte でも違えば CID が変わり DAG が fork し resume が壊れる。
**これは「過去ログを保持する」前提に依存する理由である。**

### 理由B — 差分テストオラクル(検証手法)

byte-parity-to-python3 は「python3 と `cmp` して空 diff = 移植が意味的に忠実」という、
ほぼ無料で最強の正しさ証明。HALF_EVEN 丸め・dict 挿入順・CIDv1・float repr・set 反復順
といった移植バグが**全部 1 本の `cmp` に集約**されて顕在化する。各アクターの数百〜数千
assertion はこのオラクルが背後で担保している。**過去データの保持/破棄とは無関係。**
実際に本物のバグを検出した:fuchi `analyze._report` の KeyError(上流 R2 化との不整合)、
uchiwake `analyze.py` の **PYTHONHASHSEED 依存の非決定性**(content-addressing を採る限り
Python のままでも壊れていた substrate-bound bug)。

## Decision

開発段階(pre-production)であり**過去ログは破棄可能**である事実を踏まえ、検証基準を
次のとおり再定義する:

1. **一級の不変条件 = 決定性**。substrate が content-addressed である以上、
   「同じ入力 → 同じ bytes → 同じ CID(自己無撞着)」は譲れない。これは Python に
   一致させることとは独立した、kotoba 固有の要件である。

2. **一級の検証成果物 = golden-file**。各アクターの正準出力(report / 派生 EDN / datoms /
   CID)を pin した golden-file が、移植の永続的な正しさ基準。Python 引退後も同じ仕組みで
   回帰を守る(参照が python3 から固定ファイルへ替わるだけ)。

3. **python3 byte-parity = in-development の便宜オラクル**。python3 が存在する間は、
   golden-file の生成元 + 差分検証器として byte-parity を使い続ける(追加コストほぼゼロ、
   現に bug を出している)。これは**達成"目標"ではなく検証"手段"**である。

4. **理由A の義務は破棄する**。旧 Python 産 CID に合わせる移行連続性の縛りを外す。
   必要なら Clojure 側で Datom log を **re-genesis** してよい(pre-production ゆえ legacy CID
   保存義務なし)。これにより「丸め1つ違うと移行ブロッカー」という制約が消える。

5. **Python 引退時**、byte-parity テストは golden-file テストへ自動格下げ(Clojure 出力を
   pin)。本 ADR はその格下げを事前承認する。

## Consequences

- **運用は実質不変**:ポート中は byte-parity-to-python3 を続ける(オラクルとして最良・安価)。
  ただし「legacy CID に縛られない」自由を公式に得る — re-genesis がいつでも許容。
- byte-parity が時折強いる「Python の `{:g}` / 挿入順 / repr 癖の再現」コストは、
  `fmt-g` / `exact-bd`(HALF_EVEN)/ `::order` ヘルパが全アクターで再利用されており限界コストは低い。
  これらは決定性のためにも要る道具なので無駄にならない。
- 非決定的な上流(uchiwake set / PYTHONHASHSEED)は、Clojure 側で**決定的順序に固定**して
  golden-file 化する(byte-parity は同一 line-multiset で確認)。**Clojure 版が正準**となり、
  founder follow-up として Python 側 tie-group の sort 化を推奨(任意 — Python は引退予定)。
- フリート方針(ADR-2606120500)は不変:e4b ~20% / 小コーパス CPT・SFT ±0 のため bulk 生成
  不可、正しさ移植は Claude エージェント、gemma4 **12b-qat**(実測 +7.4pp)を既定ワークホース
  候補とし 27b は品質ティア限定。本 ADR はこの分業を補強する(モデル品質はボトルネックでなく、
  byte 正確性 = test-verify ループが担保する)。

## Status of work (2026-06-13)

- merged(#1706/#1714/#1716): 14 + 完結分。回収 #1718(tate/hakoniwa/rasen-cov/hinagata-datom)
  founder マージ待ち。
- next-tier(#1718 後続 / clj/tier2-compute): kadode/generate(+cid)・kaiyaku/plan・
  hinagata 計算クラスタ(cid/validate/query/esign/maturity)を移植中。
