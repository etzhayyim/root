---
id: adr-2604231349-timestamp-numbering-policy
title: "ADR: Timestamp-based ADR numbering (YYMMDDHHMM) — collision-proof by construction"
status: active
doc_type: adr
topic: adr-governance
authoritative: true
last_verified: 2026-04-23
authoritative_for:
  - ADR file naming convention (forward-only)
  - ADR id scheme
  - collision-avoidance guarantee
related:
  - adr-0058-unified-5-pillar-platform-architecture
  - adr-0060-adr-number-registry-collision-rename
supersedes: []
superseded_by: []
---

# Context

ADR-0060 で 21 collision groups / 52 files の rename を実行 (Phase 4 完了)
した。全部で 31 ADR が renumber を経た。

この痛みの根本原因は **逐次 4 桁採番** (0001, 0002, ...) にあった:

- 新 ADR 起草時に "次の空き番号" を確認する必要がある
- 複数 agent / 人間が並行で起草すると同番号で commit → merge 時に collision
- rebase 時に検出できないことも多い (git は別ファイル扱い)

`lefthook` + `validate-adrs.py` V6 で id ↔ filename 一致を gate してはいるが、
**採番そのものの衝突**は防げない。CI 経由で merge すれば 2 branches が独立に
`0092-xxx.md` を作って両方 land するケースが起きうる。

# Decision

**ADR 番号を分単位 Unix timestamp (`YYMMDDHHMM`) に切り替える**。2026-04-23 以降
起草する ADR は本 ADR を含めて timestamp 形式を採用する。既存 0001–0091 は
そのまま保持 (retroactive rename はしない)。

## Format

```
ファイル名:  90-docs/adr/YYMMDDHHMM-<slug>.md
id (frontmatter):  adr-YYMMDDHHMM-<slug>
```

例:

```
90-docs/adr/2604231349-timestamp-numbering-policy.md
         ↓
id: adr-2604231349-timestamp-numbering-policy
```

- `YY` = 2-digit year (2026 → `26`)
- `MM` = 2-digit month
- `DD` = 2-digit day
- `HH` = 2-digit hour (24h, UTC+9 JST で統一)
- `MM` = 2-digit minute
- 合計 10 桁

## 取得方法

```bash
date +"%y%m%d%H%M"
# → 2604231349
```

## Collision の確率

同一 minute に 2 ADR を起草する確率は、同時作業 author N 人 × 平均起草間隔 T 日
とすれば `(N / (T × 1440))^2`。N=10, T=1 で約 `0.0048%`。さらに slug が違えば
OS 上の衝突もゼロ。同 minute 内に複数 ADR が必要なら `2604231349-a` / `-b` suffix で
解消 (validator V6 regex `\d{10}` は minute を要求し、suffix は slug 内扱い)。

## Alphabetical ordering

10-digit > 4-digit lexically なので、既存 `0001..0091` が list の頭、timestamp 群が
尾に並ぶ。`ls 90-docs/adr/` の sort で "old first, new last" になり、読む順序としても
自然。

# Consequences

## Positive

- **衝突ゼロ** by construction。gh pr create 時に branch 間衝突が発生しない
- **起草順序が自明**: 番号を見るだけで作成時刻 (分単位) が分かる
- **次番号を確認するオーバーヘッド無し**: `ls | tail` が不要
- **retroactive rename 不要**: 既存 0001–0091 はそのまま、ADR-0060 の registry が
  historical index として残る

## Negative

- **可読性**: 10 桁は 4 桁より読みにくい。"ADR-2604231349" vs "ADR-0092"
  mitigation: `ADR-<slug>` 省略形で話すことを許容 (既に多くの ADR で運用)
- **入力**: 手打ちすると typo しやすい。validator V6 が gate するので即検出
- **mixed numbering**: 既存 0001–0091 と timestamp が同居する奇妙さ
  mitigation: ADR-0060 registry + 本 ADR で明文化

## Neutral

- **cross-ADR reference**: `adr-XXXXXXXXXX-<slug>` 形式は長いが一意。`grep` は速い

# Validator changes

`70-tools/scripts/docs/validate-adrs.py` V6 の regex を `\d{4}` → `\d{4}|\d{10}` に
拡張 (同 commit)。既存 ADR と timestamp ADR の両方を受け入れる。

```python
# before
m = re.match(r"^adr-(\d{4})-", actual_id)
# after
m = re.match(r"^adr-(\d{4}|\d{10})-", actual_id)
```

lefthook pre-commit がこの validator を起動するので、誤って既存番号と衝突する
形式で書くと commit 時点で gate される。

# Migration

- **forward-only**: 既存 0001–0091 は renumber しない
- 新規 ADR は本日以降 timestamp 形式
- ADR-0060 の "future allocation rule" block を本 ADR で上書き (→ §References)

# References

- `date +"%y%m%d%H%M"` — 採番 command
- `90-docs/adr/0060-adr-number-registry-collision-rename.md` §Future allocation rule
  — 本 ADR が置き換える policy
- `70-tools/scripts/docs/validate-adrs.py` V6 — regex update in the same commit
- `lefthook.yml` pre-commit `adr-validate` — gate
