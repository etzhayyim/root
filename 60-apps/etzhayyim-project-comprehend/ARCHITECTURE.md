# etzhayyim-project-comprehend: Scheduler Design (v0)

## Goal

Crawler/collector を使って、世界中の以下カテゴリを JSON-LD (RDF) として収集し、SHACL 形状で品質を定義し、`etzhayyim-project-resources` に git 永続化する。

- 法人情報 / 組織情報 / 人物情報
- 法律情報
- 土地情報 / 建物情報
- 電話番号 / メールアドレス
- 契約情報（例: 公的調達、公開契約）
- DNS / IP / Domain

## Non-goals (v0)

- 無差別収集・個人情報の大量蓄積・規約/法令違反のクローリング
- “世界中すべて” を単一のクローラで網羅すること

## Principles

- Source-first: 許諾・ライセンス・robots・rate limit を尊重し、プロベナンス（出典）を必須化。
- Idempotent: 同一入力・同一時点の再実行で同一キーに収束（`latest`）し、必要に応じて履歴（`runs/<run_id>`）を残す。
- Partitioned: カテゴリごとに collector を分離し、失敗を局所化。
- Safe by default: PII が混ざる可能性があるデータ（RDAPのentity/vcard、メール、電話など）は v0 では最小化・赤字化・要レビュー化。

## Architecture (App scheduler + gitstate)

1. `cron-comprehend` が `/jobs/comprehend-tick` を周期実行
2. `etzhayyim-comprehend` が `config/targets.json` を読み、collector を実行
3. collector 出力を JSON-LD に正規化し `gitstate` 経由で `60-apps/etzhayyim-project-resources/content/` 配下に保存
4. `cron-gitstate` が `/jobs/git-flush` を周期実行し push/PR を作る（既存パターン）

## Collectors (v0 scaffold)

- `rdap(domain|ip)`: `rdap.org` から RDAP JSON を取得し、PII を含みやすいフィールドを除外して Observation として保存
- `dns(domain)`: NS/MX/TXT/A/AAAA を収集し Observation として保存
- `www-seed(url)`: `www-crawler` に seed を投げてクローリングを開始（抽出・正規化は v1 で別サービス化推奨）

## Storage Layout (suggested)

- `60-apps/etzhayyim-project-resources/content/comprehend/domain/<domain>/latest.jsonld`
- `60-apps/etzhayyim-project-resources/content/comprehend/ip/<ip>/latest.jsonld`
- `60-apps/etzhayyim-project-resources/content/comprehend/runs/<run_id>.jsonld`

## SHACL

SHACL shapes は JSON-LD で `60-apps/etzhayyim-project-resources/shacl/comprehend/shapes.jsonld` に配置。
v0 では “最低限の必須フィールド” を定義し、厳密な整合性検査は段階導入する。

