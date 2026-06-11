# gyotaku.etzhayyim.com — Internet Archive (Wayback Machine)

site.etzhayyim.com が収集した WET/WAT/WebP スナップショットを時系列で閲覧する Internet Archive ビューア。

## Architecture

- **Read-only viewer**: site.etzhayyim.com の既存データ (WET/WAT/screenshot) を SQL query で読み取り表示
- **DID**: `did:web:gyotaku.etzhayyim.com` (1 primary DID, sub-DID なし)
- **Data source**: site.etzhayyim.com の AT Record (`com.etzhayyim.apps.site.wet`, `com.etzhayyim.apps.site.wat`, `com.etzhayyim.apps.site.screenshot`)

## UI

Wayback Machine スタイル:
1. **URL 検索バー**: URL or ドメイン入力 → 過去スナップショット一覧
2. **ドメイン一覧**: crawl 済みドメインのブラウズ
3. **タイムライン**: 特定 URL の時系列スナップショット表示
4. **スナップショット詳細**: WET (Markdown テキスト) + WAT (メタデータ) + WebP (スクリーンショット)

## Commands

| Command | NSID | Purpose |
|---|---|---|
| `search-snapshots` | `com.etzhayyim.apps.gyotaku.searchSnapshots` | URL/ドメイン/キーワードでスナップショット検索 |
| `list-domains` | `com.etzhayyim.apps.gyotaku.listDomains` | crawl 済みドメイン一覧 |
| `get-snapshot` | `com.etzhayyim.apps.gyotaku.getSnapshot` | 特定 URL+timestamp のスナップショット詳細取得 |
| `get-timeline` | `com.etzhayyim.apps.gyotaku.getTimeline` | 特定 URL の全スナップショットタイムライン |
| `get-stats` | `com.etzhayyim.apps.gyotaku.getStats` | アーカイブ統計 (総ドメイン数、ページ数、WET/WAT/SS 数) |
