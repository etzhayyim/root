# etzhayyim-project-facebook — Facebook Intelligence Platform

## App Identity

| Key | Value |
|---|---|
| **nanoid** | `fb0k0x01` |
| **domain** | `facebook.etzhayyim.com` |
| **AT bot DID** | `did:web:facebook-fb0k0x01.etzhayyim.com` |
| **Runtime** | **Single Worker** (TS Native, appview mode) |
| **Data store** | **W Protocol Event Stream** — Write: `ComAtprotoRepoCreateRecord()` + `DIDCreate()` + `DIDWrite()`. Read: `G()` SQL |
| **UI mode** | `appview` (Protocol Canvas card, zero frontend) |
| **Capabilities** | facebook-sync, profile-collection, friend-graph, post-collection, messenger-bridge |

## Architecture

**Facebook account OAuth connect -> DID per friend/page -> yoro messenger bridge.**

### Data Flow

```
[OAuth2 Connect]
  User -> yoro profile -> MCP tool "connect_account" -> OAuth2 flow (Facebook Login) -> account_binding record

[Sync]
  User -> MCP tool "sync_profile" -> sync_job record (Collection Job)
  -> PDS pipeline -> Facebook Graph API incremental sync -> profile/friends/posts records
  -> handleComAtprotoSyncSubscribeReposCommit: processNewData
    -> DIDCreate("friend:{user_id}") per friend
    -> DIDCreate("page:{page_id}") per page
    -> AppBskyFeedPostAs(friendDID, name + status)  <- appears in yoro messenger
    -> Murakumo AI analysis -> report record

[Receive (facebook -> messenger)]
  Facebook feed -> sync -> post record -> friend/page DID posts in yoro
  -> governance-connected users see posts in messenger

[Send (messenger -> facebook)]
  User -> yoro messenger -> Invoke(facebook, "send_message", {friend_did, text})
  -> handleSendMessage: resolve friend DID -> Facebook user, resolve caller -> Facebook account
  -> outbound_message record -> PDS pipeline -> Facebook Messenger API send
```

### Design E 3-Tier Write

| Tier | Usage |
|---|---|
| **T1 Social** | `AppBskyFeedPostAs(friendDID, ...)` — friend/page posts as DID posts. `AppBskyFeedPost(...)` — sync events, analysis alerts |
| **T2 Domain** | `ComAtprotoRepoCreateRecord()` — facebook_entity (profile, friend, post, page, group), facebook_event (sync_job, account_binding), facebook_report (analysis) |
| **T3 State** | `Preferences()` — sync frequency, notification settings |

### Multi-DID Architecture

```
did:web:facebook.etzhayyim.com                                <- primary (controller)
  +- did:web:facebook.etzhayyim.com:friend:123456789           <- friend DID
  +- did:web:facebook.etzhayyim.com:friend:987654321           <- friend DID
  +- did:web:facebook.etzhayyim.com:page:cocacola              <- page DID
  +- did:web:facebook.etzhayyim.com:group:developers           <- group DID
  +- did:web:facebook.etzhayyim.com:profile:me                 <- user's own profile DID
```

Each Facebook friend/page = path-based DID -> appears as actor in yoro -> messageable.

### Governance

- `HandleFollowRequest`: auto-approve all followers (onboarding entry point)
- `processFollow`: welcome post with connect instructions on follow
- `app.Handle("", "send_message", ..., RequireCallerRole("member"))`: only followers can send

## UX Flow (yoro.etzhayyim.com/profile/did:web:facebook.etzhayyim.com?app=1)

```
Step 1: Follow
  [Follow] -> auto-approve -> welcome post
  "Welcome to Facebook Intelligence! Connect your Facebook account to..."

Step 2: Facebook Connect (MCP tool "connect_account")
  -> account_binding (pending_oauth) -> OAuth2 redirect -> Facebook Login
  -> Scopes: public_profile, email, user_friends, user_posts, user_likes, pages_read_engagement
  -> account_binding (active) -> processAccountBinding:
    "Facebook connected: John Doe — Syncing profile..."
  -> auto-trigger sync_job (full sync)

Step 3: Sync -> friend/page DID auto-creation
  sync_job -> PDS pipeline -> Facebook Graph API -> profile/friends/posts records
  -> DIDCreate("friend:{user_id}") per friend
  -> DIDCreate("page:{page_id}") per page
  -> AppBskyFeedPostAs(friendDID, name + status)
  -> Murakumo AI analysis -> report

Step 4: Messenger bridge
  yoro messenger -> friend/page DID conversation list
  -> reply input -> Invoke(facebook, "send_message", {friend_did, text})
  -> DID -> Facebook user resolve -> outbound_message -> Facebook Messenger API
```

## Commands (MCP Tools on yoro profile)

| Command | Description |
|---|---|
| `connect_account` | OAuth2 flow -> Facebook account binding |
| `disconnect_account` | Remove Facebook account |
| `sync_profile` | Collection Job for profile + feed sync |
| `list_friends` | List friends (pagination) |
| `get_friend` | Get friend profile by ID |
| `search_friends` | Search friends by name/query |
| `list_posts` | List feed posts (pagination) |
| `get_post` | Get single post by ID |
| `list_pages` | List liked/managed pages |
| `list_groups` | List joined groups |
| `get_profile` | Get connected Facebook profile |

## Invoke/Serve (Messenger Bridge)

| Method | Handler | Governance |
|---|---|---|
| `send_message` | `handleSendMessage` | `RequireCallerRole("member")` — followers only |

## Build & Deploy

```bash
cd 60-apps/etzhayyim-project-facebook/wasm/etzhayyim-wasm-facebook-fb0k0x01
GOROOT=$(/opt/homebrew/opt/go@1.25/bin/go env GOROOT) PATH="/opt/homebrew/opt/go@1.25/bin:$PATH" etzhayyim build
etzhayyim deploy
```
