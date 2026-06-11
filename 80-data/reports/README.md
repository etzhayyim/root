# Reports

`reports/` は **調査結果、監査結果、生成カタログ、臨時分析** を置く。`90-docs/` のような canonical design docs 置き場ではない。

## Position

- `90-docs/`: authoritative design / policy / reference
- `reports/`: derived analysis / audit / generated summary / temporary evidence

## Read Order

1. `reports/_index.json`
2. 必要なら個別 report
3. canonical 判断が必要なら `90-docs/` に戻る

## Rule

- `reports/` の内容を platform policy の正本にしない
- 長期に正本として参照したいものは `90-docs/` に昇格する
- generated / point-in-time / investigation output は `reports/` に残す
