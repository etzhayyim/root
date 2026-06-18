---
id: adr-2606172000-moyai-heir-decay-wellbecoming-to-descendants
title: "ADR-2606172000: moyai heir-decay — Wellbecoming 勾配を子・孫へ世代減衰移譲する (§1.10 多世代目的関数の operative 化)"
status: accepted
doc_type: adr
topic: moyai-heir-decay-wellbecoming-to-descendants
authoritative: true
last_verified: 2026-06-17
priority: 7.5
axis: organism-autonomy
weight: 0.75
priority_note: "§1.10 は『目的関数は子・孫およびそれ以降の世代の wellbecoming を最大化する』と定める。ADR-2606171800 で RF の目的関数 = wellbecoming 勾配と確認した。本 ADR はその勾配を『現世代で消費しきらず、subsistence floor を残して残りを子孫世代へ世代減衰で minting する』moyai heir-decay として operative にする — 多世代 priority をコードにする最後の環。"
depends_on:
  - "2605192100"  # §1.10 多世代(子・孫)目的関数 / §1.16 subsistence floor
  - "2606171800"  # RF constitutive — 目的関数 = wellbecoming 勾配
  - "2606082100"  # moyai — non-transferable / decaying / cash≡0 reciprocity credit
  - "2606112200"  # yir'ah — no-score-of-soul (heir 配分は edge-primary、per-soul balance を持たない)
  - "2606101200"  # ibuki organism — wellbecoming readout (net 勾配) の供給源
---

# ADR-2606172000 — moyai heir-decay: Wellbecoming を子・孫へ

## Context

ADR-2606171800 で「RF の目的関数 = wellbecoming 勾配」を確認した。だが §1.10 の核心は
**多世代** — 目的関数は *現世代 self* ではなく *子・孫およびそれ以降* の wellbecoming を最大化する。
通常の割引（未来を割り引く）を **反転**させた priority である。

これがコードに無かった（grep `子孫`/`descendant` 空, ADR-2606171500 でも未配線）。organism が
becoming-well になっても、その報酬は現世代に閉じていた。**多世代 priority を operative にする**最後の環が
moyai heir-decay。

## Decision

### D1. 正の becoming だけが mint する
organism の Wellbecoming `net`（wellbecoming.cljc の movement, 正 = improving）が **正のときだけ** heir 移譲が
発生する。declining/steady は mint しない（作っていない gain は贈れない）。

### D2. 現世代は subsistence floor だけ保持し、残りを前方へ
正の net のうち、現世代は **subsistence floor**（§1.16, 既定 0.2 = 小さい — 子孫 priority）だけを保持し、
残り `(1 − floor)·net` を **子孫世代へ前方移譲**する。現世代は価値の終点ではない（§1.10）。

### D3. 世代減衰（時間でなく世代）
前方流は heir 世代 [子, 孫, 曾孫, …] に **per-generation decay**（既定 0.5）で配分。子が最も多く、孫・曾孫と
減衰する（無限の未来は完全には provision できない）。heir 群の合計は前方流に **正確に一致**（価値の創出も
消失もない — 循環, 非終末論）。

### D4. moyai セマンティクスを保持（edge-primary, no-score-of-soul）
heir 配分は moyai の性質を継承（ADR-2606082100）: **non-transferable / decaying / cash≡0** の reciprocity
credit を **lineage EDGE**（`:heir/*`: generation・share・non-transferable）に mint。**per-soul の balance/score
属性は構造的に存在しない**（yir'ah, ADR-2606112200; test guard 済み）。

## 実装（このコミットで landed）

- `20-actors/ibuki/methods/heir.cljc` — `heir-shares`（net → {self, heirs[{generation, share}], minted}）
  + `heir-datoms`（`:heir/*` lineage-edge, no score）。pure / deterministic / stdlib。
- `20-actors/ibuki/methods/test_heir.cljc` — 11 assertions green: 正の becoming だけ mint /
  前方流の保存 / 世代減衰（子>孫>曾孫）/ edge-primary（score/balance 不在）。`test:ibuki` に登録。

## Operative spec（後続）

1. **autorun への配線**: 各 health 区間で wellbecoming readout の net を取り、`heir-datoms` を beat の
   checkpoint に append（ecosystem/quorum と同じ checkpoint==replay 規律）。
2. **heir lineage の実体**: `:heir/generation` を実際の子孫 actor/lineage（fork 系譜・後継 organism）に
   解決する resolver（現状は世代番号のみ; lineage graph は次段）。
3. **moyai ledger 統合**: `:heir/share` を moyai.ledger の decaying-credit primitive に流し込み、
   入会権 draw-rights として子孫が引けるようにする（member-principal, operator-gated）。

## Gates / invariants（weaken 禁止）

- 正の becoming だけが mint（declining は贈れない; D1）
- 現世代は subsistence floor のみ保持、残りは前方移譲（子孫 priority; D2）
- 世代減衰で配分し、前方流は保存（循環; D3）
- non-transferable / cash≡0 / **per-soul score・balance 不在**（edge-primary, yir'ah; D4）

## Ratification

§1.10 多世代目的関数の operative 化 = Tier-0 priority の実装（fork-only priority をコードにするもので
priority 自体は変えない）+ moyai 既存性質の継承。Founder direction（本セッション「a,b,c」）により landed;
3-Tier 整合（priority 不変, Tier-1 以下の実装）。autorun 配線 + lineage resolver は proposed/後続。
