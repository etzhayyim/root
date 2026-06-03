# etzhayyim-project-deai — Project Runbook

## Project Overview

`decom.etzhayyim.ai` — Spirit-in-Physics 研究データ収集フロントエンド + 出会い・マッチングアプリ。

**主目的は研究データ収集。** 出会い・マッチング機能は参加インセンティブ。
全データは spirit-in-physics.com（研究 SSoT）に送信される。

感情を熱力学的情報量として定義した Jun Kawasaki et al. の研究 "Spirit in Physics: Spirit as a Thermodynamic Information Quantity" を基盤とし、Spirit Type（Hero / Sage / Lover / Caregiver）適合度と感情テンセグリティ共鳴でマッチングする。

**Component**: `appview/deai-cgxi8oem/`
**nanoid**: `cgxi8oem`
**Runtime**: TS Native Worker + SvelteKit SPA (PWA) + Capacitor (iOS/Android)
**Operating entity**: etzhayyim（alias: amanomibashira / 天御柱 / עץ חיים）

## 研究 SSoT — spirit-in-physics.com/api

| エンドポイント | 役割 |
|---|---|
| `POST /api/participants` | 参加者登録（upsert） |
| `POST /api/assessments/start` | アセスメント開始 |
| `POST /api/assessments/session-start` | セッション開始 |
| `POST /api/assessments/word-response` | 語応答 + 反応時間 |
| `POST /api/assessments/artifact` | Hume スコア / 生理指標 JSON |
| `POST /api/assessments/complete` | セッション完了 |
| `GET /api/timeline/integrated` | 分析済みタイムライン |
| `GET /api/timeline/emotion-vectors` | 感情ベクトル |
| `GET /api/stimulus-words` | Jung 100語リスト |

研究者フロントエンド: `https://researcher.spirit-in-physics.com`

## Spirit-in-Physics 理論基盤

論文: "Spirit in Physics: Spirit as a Thermodynamic Information Quantity" (Kawasaki et al., 2026)

### 核心仮定
1. 情報は熱力学量（Shannon 1948 + Jaynes 1957 + Landauer 1961）
2. 霊性（Spirit）= 高次元情報構造（自己の情報的定義）
3. Spirit は開放熱力学系として自由エネルギーを最小化（Friston 2010）

### 測定式
```
P(w_O | w_I) = exp(w_I · w_O) × r^α × exp(γ·ΔSP/λ) × exp(η·F) / Z
```
- `r` = 反応時間の逆数（語連想実験）
- `ΔSP` = 皮膚電位変化（GSR / HRV 近似）
- `F` = 感情表現スコア（Hume AI 10次元ベクトル）

### Spirit Types（Jung 分析心理学）
| Type | 特徴 | 補完関係 |
|---|---|---|
| Hero | 使命・達成・保護 | Caregiver（保護↔養育） |
| Sage | 知恵・省察・真実 | Lover（思考↔体感） |
| Lover | 美・感性・つながり | Sage（体感↔思考） |
| Caregiver | 養育・共感・奉仕 | Hero（養育↔保護） |

### テンセグリティ・マッチング
- 感情空間内の距離 = RBF カーネル `W_ij = exp(-||e_i - e_j||^2 / σ^2)`
- 安定な関係 = 感情テンセグリティで自由エネルギーを最小化するペア
- マッチスコア = `U_spirit × U_resonance × (1 - separation_entropy)`

## Multi-DID Architecture

| DID | 用途 |
|---|---|
| `did:web:decom.etzhayyim.ai` (primary) | Platform agent (controller) |
| `did:web:decom.etzhayyim.ai:{cohort-hash}` | コホートユーザー（統計的個体群） |
| `did:web:decom.etzhayyim.ai:type:{spirit-type}` | Spirit Type アーキタイプ DID |

## Runtime

| 項目 | 値 |
|---|---|
| Worker | `appview/deai-cgxi8oem/src-ts/app.ts` |
| Frontend | `appview/deai-cgxi8oem/svelte/` (SvelteKit 5 SPA, CSR only) |
| Mobile | `appview/deai-cgxi8oem/mobile/` (Capacitor 6 iOS/Android) |
| nanoid | `cgxi8oem` |
| Domain | `decom.etzhayyim.ai` |
| Deploy | `cd appview/deai-cgxi8oem && etzhayyim deploy` |

## Data Model

### AT Protocol Collections (Tier 1 Social)
| Collection | 用途 |
|---|---|
| `com.etzhayyim.apps.deai.checkin` | 毎日の Spirit Check-in（感情 snapshot） |

### Domain Tables (Tier 2, K8s Pod → RisingWave)
| Table | 主要カラム |
|---|---|
| `vertex_deai_profile` | actor_did, spirit_type, emotion_vector_json, cohort_hash |
| `vertex_deai_session` | session_id, actor_did, stimulus_words_json, started_at |
| `vertex_deai_response` | session_id, word, reaction_time_ms, hume_score_json, sp_delta |
| `vertex_deai_match` | actor_did_a, actor_did_b, resonance_score, spirit_compatibility |
| `vertex_deai_message` | from_did, to_did, ciphertext, iv, created_at |

### PII (Tier 3 = Vault / Preferences のみ)
- 顔画像 = Hume 処理後に即削除（クライアント側で処理）
- 音声 = Hume 処理後に即削除
- メール・電話 = Vault zero-knowledge（暗号化してのみ保持）
- マッチ履歴 = cohort DID のみ（実 DID は server 非保持）

## XRPC Endpoints

| NSID | 型 | 説明 |
|---|---|---|
| `com.etzhayyim.apps.deai.startAssessment` | procedure | 語連想セッション開始 |
| `com.etzhayyim.apps.deai.submitResponse` | procedure | 語 + 感情応答送信 |
| `com.etzhayyim.apps.deai.getProfile` | query | Spirit プロファイル取得 |
| `com.etzhayyim.apps.deai.listMatches` | query | マッチ一覧取得 |
| `com.etzhayyim.apps.deai.createCheckin` | procedure | Spirit Check-in 作成 |
| `com.etzhayyim.apps.deai.sendMessage` | procedure | 暗号化メッセージ送信 |
| `com.etzhayyim.apps.deai.listMessages` | query | メッセージ一覧取得 |

## LangGraph Graphs

| Graph | ファイル | 説明 |
|---|---|---|
| `deaiSpiritAssessment` | `langgraph_graphs/deai_spirit_assessment.py` | 語連想 + Hume → Spirit Type 判定 |
| `deaiMatchEngine` | `langgraph_graphs/deai_match_engine.py` | テンセグリティ・マッチスコア計算 |

## Mobile (Capacitor)

| 項目 | 値 |
|---|---|
| App ID | `com.etzhayyim.deai` |
| App Name | `deai — Spirit Match` |
| Web Dir | `../svelte/build` |
| iOS | `mobile/ios/` |
| Android | `mobile/android/` |
| Plugins | Camera (Hume face), Voice Recorder (Hume voice), Preferences (token store) |

### Capacitor Build
```bash
cd appview/deai-cgxi8oem/svelte && pnpm build
cd ../mobile && npx cap sync
npx cap open ios      # Xcode
npx cap open android  # Android Studio
```

## Security / Privacy

- **Vault zero-knowledge**: 生体データ（顔・音声）は client 側で Hume API 呼び出し後に即破棄。スコアのみ送信。
- **Cohort DID**: 個人識別子は server に保持しない。cohort DID (`did:web:decom.etzhayyim.ai:{hash}`) のみ。
- **Signal protocol**: DM は E2E 暗号化 `signal:v1:{ciphertext}` フィールド。
- **Consent gate**: マッチング・感情データ共有はユーザー明示同意が必要。
- **PII Tier 3**: 年齢・性別・地域は Cohort 次元として統計化。raw PII は Vault のみ。

## 刺激語 SSoT

Jung の語連想実験オリジナル 100語（日本語適応版）。
SSoT: `com-junkawasaki/spirit-in-physics/apps/api-worker/src/stimulus-words.ts`
deai コピー: `svelte/src/lib/sip-api.ts` の `JUNG_STIMULUS_WORDS`（同期維持必須）

## Well-Becoming Objective Function 適用

```
U_total = U_spirit(接続度) × U_wellbecoming × U_feeling × U_buffer
```
deai は `U_spirit` (Rank 2, weight 0.95) を直接最大化する。孤独・分離を増やすマッチは reject。
