# gyotaku.gftd.ai — Internet Archive (Wayback Machine)

site.gftd.ai が収集した WET/WAT/WebP スナップショットを時系列で閲覧する Internet Archive ビューア。

## Architecture

- **Read-only viewer**: site.gftd.ai の既存データ (WET/WAT/screenshot) を SQL query で読み取り表示
- **DID**: `did:web:gyotaku.gftd.ai` (1 primary DID, sub-DID なし)
- **Data source**: site.gftd.ai の AT Record (`ai.gftd.apps.site.wet`, `ai.gftd.apps.site.wat`, `ai.gftd.apps.site.screenshot`)

## UI

Wayback Machine スタイル:
1. **URL 検索バー**: URL or ドメイン入力 → 過去スナップショット一覧
2. **ドメイン一覧**: crawl 済みドメインのブラウズ
3. **タイムライン**: 特定 URL の時系列スナップショット表示
4. **スナップショット詳細**: WET (Markdown テキスト) + WAT (メタデータ) + WebP (スクリーンショット)

## Commands

| Command | NSID | Purpose |
|---|---|---|
| `search-snapshots` | `ai.gftd.apps.gyotaku.searchSnapshots` | URL/ドメイン/キーワードでスナップショット検索 |
| `list-domains` | `ai.gftd.apps.gyotaku.listDomains` | crawl 済みドメイン一覧 |
| `get-snapshot` | `ai.gftd.apps.gyotaku.getSnapshot` | 特定 URL+timestamp のスナップショット詳細取得 |
| `get-timeline` | `ai.gftd.apps.gyotaku.getTimeline` | 特定 URL の全スナップショットタイムライン |
| `get-stats` | `ai.gftd.apps.gyotaku.getStats` | アーカイブ統計 (総ドメイン数、ページ数、WET/WAT/SS 数) |
