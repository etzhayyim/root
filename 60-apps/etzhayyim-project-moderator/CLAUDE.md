# ai-gftd-project-moderator — moderator.gftd.ai

**yoro.gftd.ai 管理パネル** — ユーザー・ポスト・アカウント・決済・課金・広告の一元管理。

## Architecture

| 項目 | 値 |
|---|---|
| Domain | `moderator.gftd.ai` |
| Runtime | **Single Worker** — TS Native + SvelteKit SSR |
| nanoid | `m0d3r8t0` |
| performerType | `system` |
| uiType | `iframe` (full SvelteKit admin panel) |
| Admin | `igmyn1ab` のみ (CRITICAL — 他ユーザーは全機能アクセス不可) |

## CRITICAL: Admin Gate

→ `gftd dodaf tv1 query --id ai-gftd-project-moderator-admin-gate` / MCP `gftd.dodaf.tv1.query`

## Domain Model

### 1. User Management (ユーザー管理)

| Command | 説明 |
|---|---|
| `search_users` | DID/handle/displayName で検索 |
| `get_user` | ユーザー詳細 (profile + posts + credits + trust score) |
| `suspend_user` | アカウント停止 (理由必須) |
| `unsuspend_user` | アカウント復帰 |
| `update_user_role` | ロール変更 (user/moderator/admin) |

### 2. Post Management (ポスト管理)

| Command | 説明 |
|---|---|
| `search_posts` | キーワード/DID/日付で検索 |
| `get_post` | ポスト詳細 (engagement + reports) |
| `delete_post` | ポスト削除 (理由必須、audit record 作成) |
| `label_post` | コンテンツラベル付与 (sensitivity tagging) |

### 3. Account Management (アカウント管理 — Org-Account-Based)

| Command | 説明 |
|---|---|
| `list_accounts` | アカウント (org DID) 一覧 (pagination, org_type filter) |
| `get_account` | アカウント詳細 (org DID + person DID + all path DIDs + credentials) |
| `set_org_type` | org_type 変更 (personal → company/npo/community/team) |
| `list_org_dids` | org DID の全 path-based DID 一覧 |
| `create_org_did` | org 配下に path-based DID 追加 (部署/チーム/bot) |
| `deactivate_org_did` | org 配下の path-based DID 無効化 |
| `invite_member` | 他ユーザーの person DID を org に招待 |
| `remove_member` | org から member 除外 |
| `set_member_role` | member の org 内ロール設定 (admin/editor/viewer) |

### 4. Payment & Billing (決済・課金)

| Command | 説明 |
|---|---|
| `list_transactions` | 決済履歴 (credits purchase/spend) |
| `get_transaction` | 決済詳細 |
| `adjust_credits` | クレジット手動調整 (理由必須、audit record) |
| `list_subscriptions` | サブスクリプション一覧 |
| `cancel_subscription` | サブスクリプション強制キャンセル |

### 5. Ad Management (広告管理)

| Command | 説明 |
|---|---|
| `list_ads` | 広告一覧 (status filter) |
| `get_ad` | 広告詳細 (impressions + clicks + spend) |
| `approve_ad` | 広告承認 |
| `reject_ad` | 広告却下 (理由必須) |
| `suspend_ad` | 広告停止 |

## CRITICAL: Org-Account-Based Identity Design (DEFAULT)

→ `gftd dodaf tv1 query --id ai-gftd-project-moderator-org-account-based-identity-design` / MCP `gftd.dodaf.tv1.query`

## Graph Labels

| Label | 用途 |
|---|---|
| `:ModAction` | 管理アクション audit trail |
| `:AdCampaign` | 広告キャンペーン |
| `:AdCreative` | 広告クリエイティブ |
| `:CreditAdjustment` | クレジット手動調整 |

## Collections (camelCase, Design E Tier 2)

| Collection | NSID | 用途 |
|---|---|---|
| `mod_action` | `ai.gftd.apps.moderator.mod_action` | 管理アクション record |
| `ad_campaign` | `ai.gftd.apps.moderator.ad_campaign` | 広告キャンペーン |
| `ad_creative` | `ai.gftd.apps.moderator.ad_creative` | 広告クリエイティブ |
| `credit_adjustment` | `ai.gftd.apps.moderator.credit_adjustment` | クレジット調整 |
| `org_type_change` | `ai.gftd.apps.moderator.org_type_change` | org_type 変更 record |
| `member_action` | `ai.gftd.apps.moderator.member_action` | member invite/remove/role change |

## Reactive Pipeline

```
ComAtprotoSyncSubscribeRepos
  ├─ app.bsky.feed.post → auto-moderation check (spam/sensitivity)
  ├─ ai.gftd.apps.moderator.mod_action → audit log
  ├─ ai.gftd.apps.moderator.ad_campaign → ad approval queue
  └─ ai.gftd.apps.credits.* → credit transaction tracking
```

## UI Structure

### moderator.gftd.ai (Admin Panel — igmyn1ab only, iframe mode)

```
/                        → Dashboard (accounts: total/personal/expanded, posts, ads, mod_actions)
/users                   → User search & list (person DID search)
/users/[did]             → User detail (person profile + parent org + mod actions)
/posts                   → Post search & list
/posts/[uri]             → Post detail (reports + mod actions)
/accounts                → Account (org DID) list, org_type filter
/accounts/[did]          → Account detail (org DID + person profile + all path DIDs + members)
/payments                → Transaction list
/payments/[id]           → Transaction detail
/ads                     → Ad campaign list
/ads/[id]                → Ad detail + approve/reject
/audit                   → Audit log (mod_action records)
```

### yoro.gftd.ai Profile 統合 (User-Facing Org Management)

```
/profile/[handle]        → AgentProfile + Org tab (isSelf && isOrgController)
/settings/account        → DID Switcher (active_did 切替)
```

**組織管理 UI は profile ページの「Org」タブに統合。** 詳細は §Org Management UIUX 参照。
