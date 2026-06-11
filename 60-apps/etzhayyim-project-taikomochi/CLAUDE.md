# etzhayyim-project-taikomochi — Twitch AI Agent

太鼓持ち (taikomochi) = Twitch 配信を視聴し、文脈に応じたコメントを自動投稿する AI Agent。

## Target Channel

- **Channel**: https://www.twitch.tv/panomaru2025
- **Channel Name**: `panomaru2025`

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    taikomochi-twitch-agent                       │
│                  (Native Go Provider Binary)                     │
│                                                                 │
│  ┌───────────────┐   ┌────────────────┐   ┌──────────────────┐ │
│  │ Twitch IRC     │   │ Stream Monitor │   │ AI Commentator   │ │
│  │ Client         │   │ (Helix API)    │   │ (OpenRouter)     │ │
│  │                │   │                │   │                  │ │
│  │ • Read chat    │   │ • Stream status│   │ • Claude Ops 4.6 │ │
│  │ • Send message │   │ • Game/Title   │   │ • Context window │ │
│  │ • Join channel │   │ • Viewer count │   │ • Persona prompt │ │
│  └───────┬───────┘   └───────┬────────┘   └────────┬─────────┘ │
│          │                   │                     │            │
│  ┌───────▼───────────────────▼─────────────────────▼──────────┐ │
│  │                    Agent Core Loop                          │ │
│  │                                                            │ │
│  │  1. チャットメッセージ受信 → context buffer に蓄積          │ │
│  │  2. 配信情報 (ゲーム名、タイトル) 取得                      │ │
│  │  3. 一定間隔 or トリガー条件で AI にコメント生成依頼        │ │
│  │  4. 生成されたコメントを Twitch IRC で投稿                  │ │
│  │  5. 投稿履歴を ClickHouse に保存 (重複・スパム防止)          │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                 ClickHouse State (schema.hcl)                              │ │
│  │  • chat_history: 直近 N 件のチャットログ                   │ │
│  │  • sent_comments: 投稿済みコメント履歴                     │ │
│  │  • stream_context: 配信メタデータ                          │ │
│  │  • agent_config: 動的設定 (persona, interval, etc.)        │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │           wRPC Export: etzhayyim:taikomochi/agent@0.1.0         │ │
│  │  • get-status() → AgentStatus                              │ │
│  │  • set-config(key, value) → result                         │ │
│  │  • send-comment(text) → result (手動投稿)                  │ │
│  │  • get-chat-history(count) → list<ChatMessage>             │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Component Classification

| 分類 | 値 |
|------|------|
| Type | **Native Go Provider** (goroutine, net/http, WebSocket 必須) |
| WIT namespace | `etzhayyim:taikomochi` |
| Deploy target | `kotodama-runtime` namespace |
| Image registry | `ghcr.io/etzhayyim/taikomochi-twitch-agent` |

## Key Design Decisions

### Why Native Go Provider (not TS Native)

1. **WebSocket 常時接続**: Twitch IRC は WebSocket (`wss://irc-ws.chat.twitch.tv:443`) 常時接続が必要
2. **Goroutine 必須**: チャット受信ループ + AI 応答生成 + 定期ポーリングが並行動作
3. **net/http クライアント**: OpenRouter API + Twitch Helix API への HTTP リクエスト
4. **長時間実行プロセス**: 配信中ずっと動作する daemon 型

### OpenRouter + Claude Opus 4.6

- **Endpoint**: `https://openrouter.ai/api/v1/chat/completions`
- **Model**: `anthropic/claude-opus-4-6`
- **Reason**: OpenRouter 経由で Claude Opus 4.6 を利用、API key 管理を統一
