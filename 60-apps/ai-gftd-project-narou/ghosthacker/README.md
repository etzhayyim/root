
# Ghost Hacker Producer Pipeline

AI駆動型コンテンツ生成システムで、Ghost Hackerストーリーを多様なフォーマット（Webtoon、Wattpad、YouTube動画）で生成します。

## 概要

Ghost Hackerは、2065年の水の都・東京を舞台に、情報生命体（Ghost）と人間の絆を描いた物語です。このProducer Pipelineは、Neo4jベースのストーリーグラフから始まり、AI生成コンテンツを通じて複数のメディアフォーマットでストーリーを展開します。

## アーキテクチャ

Merkle DAGベースのトポロジカル実行パイプライン：

```
Story Graph (Neo4j) → Lore Generation → Prompt Composition → AI Writer
                      ↓
               ┌──────┴──────┐
               │             │
         Image Gen      TTS Narration
               │             │
               ↓             ↓
         Webtoon Panels      │
               ↓             │
         Webtoon Layout      │
               ↓             │
         Webtoon Export      │
               ↓             │
         Video Generation    │
               ↓             │
         Video Render ───────┘
               ↓
         ┌─────┴─────┐
         │           │
    Wattpad Export   YouTube Upload
```

## 特徴

- **マルチフォーマット出力**: Webtoon、Wattpad小説、YouTube動画
- **並行処理**: 画像生成とTTSを並行実行で効率化
- **品質保証**: トポロジカルソートによる依存関係管理
- **拡張性**: Neo4jベースのストーリーグラフで容易な拡張

## 技術スタック

- **Frontend**: Next.js 14, React 18, TypeScript
- **Backend**: Node.js, Neo4j, @neo4j/cypher-builder
- **AI**: GPT-4, Flux 1.1 Pro, Sora
- **Styling**: Tailwind CSS, shadcn/ui
- **State**: Zustand, React Flow (for pipeline visualization)
- **Build**: pnpm, tsup

## プロジェクト構造

```
├── producer/              # Next.jsアプリケーション (メイン)
│   ├── src/
│   │   ├── app/(producer)/canvas/  # PipelineノードごとのUIページ
│   │   │   ├── story/              # ストーリー設定フォーム
│   │   │   ├── lore/               # キャラクター/世界観設定
│   │   │   ├── prompt-story/       # AIプロンプト生成
│   │   │   ├── writer-content/     # コンテンツ書き込み
│   │   │   ├── image-gen/          # 画像生成
│   │   │   ├── webtoon-*/          # Webtoon生成パイプライン
│   │   │   ├── tts-narration/      # 音声合成
│   │   │   ├── video-gen/          # 動画生成
│   │   │   ├── export-wattpad/     # Wattpad出力
│   │   │   └── publish-youtube/    # YouTube公開
│   │   ├── components/             # Reactコンポーネント
│   │   ├── lib/                    # ユーティリティ
│   │   │   ├── ai/                 # AIプロバイダー
│   │   │   ├── story-neo4j.ts      # Neo4jクライアント
│   │   │   └── videoRenderer.ts    # 動画レンダラー
│   │   ├── ontology/               # JSON-LDスキーマ定義
│   │   ├── pipeline/               # パイプライン実行エンジン
│   │   │   ├── node-types/         # 各ノードの実装
│   │   │   ├── executor.ts         # パイプライン実行器
│   │   │   └── buildTopology.ts    # トポロジー構築
│   │   ├── 70-tools/70-tools/70-tools/scripts/                # データ処理スクリプト
│   │   │   ├── create-project.ts   # プロジェクト生成
│   │   │   ├── import-episode-graph.ts # エピソードインポート
│   │   │   └── generate-episode-jsonld.ts # JSON-LD生成
│   │   ├── server/routers/         # tRPC APIルーター
│   │   └── observability/          # 監視・計測
│   └── story.jsonnet               # Pipelineトポロジー定義 (Merkle DAG)
├── 251022/                # 統合ナレッジベース (JSON-LD)
│   └── ghost-hacker.jsonld # RDF/JS準拠の統合データ
├── 250806/                # ストーリー資産・設定
│   ├── episodes/           # エピソード原稿
│   ├── character/          # キャラクター設定
│   ├── setting/            # 世界設定
│   └── drawstyle.md        # 作画スタイルガイド
├── 250805_gemini/         # キャラクター設計・世界構築
├── 250501/                # 原作ストーリードラフト
└── docker-compose.yml      # 開発環境構成
```

## クイックスタート

### 環境構築

```bash
cd producer
pnpm install
pnpm dev
```

### データインポート

ストーリー素材をNeo4jにインポート：

```bash
# キャラクター・世界設定のインポート
pnpm import:lore

# キャラクター分析
pnpm analyze:characters

# エピソードグラフのインポート
pnpm import:episode

# エピソードJSON-LD生成
pnpm generate:episode-jsonld

# 一括分析・インポート
pnpm analyze-and-import
```

### Wattpad自動投稿

英語版エピソードをWattpadに自動投稿：

```bash
# 環境変数の設定（.envrcまたはexport）
export WATTPAD_EMAIL='your-email@example.com'
export WATTPAD_PASSWORD='your-password'
export WATTPAD_WORK_ID='402848261'  # Wattpad作品ID
export WATTPAD_HEADLESS=false       # ブラウザを開く場合はfalse

# 1件のみテスト投稿
pnpm wattpad:publish --limit=1

# 5件テスト投稿
pnpm wattpad:publish --limit=5

# 全件投稿（既存パートも更新）
pnpm wattpad:publish

# ドライラン（実際には投稿しない）
pnpm wattpad:publish --dry-run
```

**機能:**
- 英語版エピソード（`part*.en.md`）の自動検出
- JSON-LDブロックの自動削除
- エピソードタイトルの自動追加（EP1の最初のパートなど）
- パートIDの自動マッピング保存
- タイトル・本文の検証
- ブラウザ可視モードでのデバッグ対応

**ファイル構成:**
- `251022/wattpad/episodes/epXX/partY.en.md`: 英語版エピソード原稿
- `251022/wattpad/part-ids.jsonld`: WattpadパートIDマッピング
- `251022/wattpad/manifest.json`: エピソードメタデータ

## Pipeline実行順序

1. **ストーリーグラフ取得** (Neo4j)
2. **Lore生成** (キャラクター設定、世界観、ナラティブ構造)
3. **プロンプト生成** (AI向け指示生成)
4. **コンテンツ書き込み** (GPT-4)
5. **メディア生成** (画像+TTS並行処理)
6. **フォーマット変換** (Webtoonレイアウト、動画合成)
7. **出力パッケージング** (各プラットフォーム向け)

## ロードマップ

### Phase 1: Core Pipeline (Current)
- [x] Story graph integration (Neo4j)
- [x] Basic lore generation
- [x] AI content writing
- [x] Image generation (Flux)
- [x] Webtoon panel layout
- [x] TTS narration
- [x] Wattpad automated publishing
- [ ] Video generation (Sora)
- [ ] Multi-platform export

### Phase 2: Enhanced Features
- [ ] Interactive story branching
- [ ] Real-time pipeline monitoring
- [ ] Quality assurance automation
- [ ] Multi-language support
- [ ] Collaborative editing

### Phase 3: Production Scale
- [ ] Distributed pipeline execution
- [ ] Advanced AI model integration
- [ ] Analytics & optimization
- [ ] API commercialization

## 貢献

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## ライセンス

MIT License - see the [LICENSE](LICENSE) file for details.

---

*Ghost Hacker: Healing connections in a disconnected world*
 