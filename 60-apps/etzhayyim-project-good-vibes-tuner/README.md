# etzhayyim-project-good-vibes-tuner

`good-vibes-tuner` は、ユーザーが「今どんな vibes で集中したいか」を選び、
表示情報・通知密度・提案スタイルを調整する capability の設計コンセプトです。

## 目的
- Focus vibes（例: Deep Focus / Creative Flow / Execution Sprint）を 1 クリックで切り替える
- 画面内の情報量を目的別にチューニングする
- チューニング結果をセッションに保存し、次回も同じ集中体験を再現する

## Capability 設計

### 1. Vibe Preset Engine
- 入力: `vibe_id`, `session_context`, `organization_context`
- 出力:
  - 優先表示する signal（例: 締切、未読、リスク）
  - 抑制する noise（例: 低優先通知）
  - 提案トーン（短文 / 探索型 / 実行チェックリスト）

### 2. Information Surface Tuner
- 調整対象:
  - Priority Lane（重要情報を上位表示）
  - Context Capsule（関連資料・会話の要約）
  - Energy Meter（通知頻度の調整）
  - Ambient Feed（背景情報の低ノイズ表示）
- フロントでは toggle の組み合わせで表示面を変更

### 3. Focus Session Memory
- `org_id + user_id + vibe_id` をキーに tuning 設定を保持
- 「直近の成功セッション」を再利用して復帰時間を短縮

### 4. Feedback Loop
- セッション終了時に「集中できたか」を 1-5 で収集
- 次回の preset 推薦に反映（軽量なオンライン学習）

## UI エントリポイント
- `etzhayyim-www-nkupwzos` の左上に `⚙️ Tuning` メニューを追加
- 展開時に:
  - Focus vibe selector
  - Tune option toggles
  - Tuned info preview を表示

## 今後の実装候補
1. store 化して各 mode（chat / scheduler / cowork）に反映
2. API 化して server 側で vibe recommendation を提供
3. org policy と連携し、表示可能な情報範囲を制御
