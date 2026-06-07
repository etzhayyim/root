# etzhayyim-project-mailer

mailer.etzhayyim.com — DID-based email platform。`performerType: system`。

## Status: VENDOR-RETAINED (2026-05-30)

このアプリは 2026-05-21 に etzhayyim へ migrate されたが、root `CLAUDE.md`
§etzhayyim Agent / Email Policy (2026-05-28) で **mailer.etzhayyim.com = repo-wide
primary email platform** と再定義された。よって vendor 側 (`etzhayyim`) でも
本ソースを SSoT として保持する (旧 `DEPRECATED.md` は除去)。etzhayyim 側にも
canonical copy が存在しうるが、`*.etzhayyim.com` 本番 worker (`kotodama-a8wwtz73`,
CF account `etzhayyim-cloud`) の lifecycle は etzhayyim が担う。

> Split-brain 注意: etzhayyim/root も同名アプリを出荷しうる。`mailer.etzhayyim.com`
> 本番 worker は vendor がデプロイ主体。etzhayyim CI が同 worker を上書きする
> 構成なら停止調整が必要。

### Live appview deploy

- **Worker**: `kotodama-a8wwtz73` (routes: `mailer.etzhayyim.com/*`, `a8wwtz73.etzhayyim.com/*`,
  `etzhayyim-project-mailer.etzhayyim.com/*`, `8wwtz73p.etzhayyim.com/*`)
- **Source**: `appview/mailer-mcp-component/` (SvelteKit edge BFF)
- **Read path**: `/api/{emails,stats,bindings}` → `proxyToDispatcher` → POST
  `https://dispatcher.etzhayyim.com/xrpc/ai.etzhayyim.apps.mailer.{listEmails,stats,listBindings}`
  with `x-internal-trust` (`DISPATCHER_INTERNAL_SECRET` = K8s `bpmn-dispatcher-auth/internal-secret`)
  → bpmn-dispatcher → Zeebe `mailer` worker → RW `vertex_mailer_inbound_email`.
- **Secrets (wrangler, NOT in wrangler.jsonc vars)**: `DISPATCHER_URL`
  (= `https://dispatcher.etzhayyim.com`), `DISPATCHER_INTERNAL_SECRET`, `SS_RESEND_API_KEY`.

### 2026-05-30 — Inbox 520 fix

`/api/emails` と `/api/stats` が 520 を返していた。原因は worker secret
`DISPATCHER_URL` が死んだ旧 dev IP `http://66.42.104.29.sslip.io` を指していた
こと (proxy は `env.DISPATCHER_URL ?? default` を base にする)。

- **Fix (live)**: `wrangler secret put DISPATCHER_URL` = `https://dispatcher.etzhayyim.com`。
  `DISPATCHER_INTERNAL_SECRET` は既に正値。`/api/stats`→`{emails:4,bindings:0}`、
  `/api/emails`→実 inbound 4 件で回復。
- **Hardening (source, `mailer-proxy.ts`)**: 死んだ fallback IP 列を空にし、base が
  一時 CF エラー時に dead IP の bare `error code: 520` をパススルーしない。
  `isCloudflareOriginError` を素の `error code: 5xx` も検知するよう強化。
  反映には `mailer-mcp-component` の rebuild + `wrangler deploy` が必要。

## Architecture

| Component | Type | Role |
|---|---|---|
| **email-relay** | Account-level JS Worker | **Inbound gateway** — CF Email Routing → MIME parse → PDS record → convo delivery |
| **mailer-inbound** (`ml1nb0nd`) | Dispatch namespace WASM | Commands: register/send/reply/forward email + commit handler |
| **notify** (`nt4g5h6i`) | Dispatch namespace WASM | Multi-channel notification dispatcher |
| **resend** (`rs7j8k9l`) | Dispatch namespace WASM | Resend API backend |

## Inbound Email Flow (CRITICAL)

```
External SMTP sender
  → CF Email Routing (MX: route{1,2,3}.mx.cloudflare.net, catch-all *@etzhayyim.com)
  → etzhayyim-email-relay Worker (account-level, email() handler)
  → worker.ts:
    1. Read raw MIME stream, parse headers/body
    2. PDS createRecord("inboundEmail", {from, to_local, subject, body_text, ...})
    3. Resolve DID: {handle}@etzhayyim.com → did:web:{handle}.etzhayyim.com
    4. PDS ai.etzhayyim.projector.createProjectConvo({participantDids, kind, name}) → convoId
    5. PDS ai.etzhayyim.projector.sendProjectMessage({convoId, text: formatted email})
    6. PDS createRecord("inboundEmailStatus", {status: "delivered", convo_id})
    7. Persist state to KV (emailCount, lastEmail)
```

**Known constraint**: CF Email Routing requires account-level Worker。email-relay は account-level Worker として `50-infra/cloudflare/workers/email-relay/` に配置。

## Outbound Email Flow

```
mailer-inbound commands (cmdSendEmail / cmdReplyToEmail / cmdForwardEmail)
  → sendViaResend(from, to, subject, body)
    → Resend API (https://api.resend.com/emails)
    → ComAtprotoRepoCreateRecord("outboundEmail", {provider: "resend", ...})
    → AppBskyFeedPost("Email sent: from → to [subject]")
```

## DID Resolution

```
{handle}@etzhayyim.com  →  did:web:{handle}.etzhayyim.com
```

Convention-based。Alpha-start rule enforced (a-z 始まり)。

## Convo Delivery (CRITICAL)

W Protocol `ai.etzhayyim.convo` で配信:
- `ai.etzhayyim.projector.createProjectConvo({participantDids, kind, name})` — mailer DID と recipient DID の project convo 作成
- `ai.etzhayyim.projector.sendProjectMessage({convoId, text})` — メール内容をテキストメッセージとして送信
- yoro convo tab に通常メッセージとして表示 (recipient が AI Agent なら Murakumo LLM auto-reply)

## Infra

| Layer | Implementation | Location |
|---|---|---|
| **DNS** | MX (`route{1,2,3}.mx.cloudflare.net`), SPF, DMARC, Resend DKIM | `50-infra/pulumi/cloudflare/dns.ts` |
| **Email Routing** | Zone enable + catch-all → email-relay Worker | `50-infra/pulumi/cloudflare/email-routing.ts` |
| **email-relay** | Account-level Worker: email handler + PDS service binding + KV | `50-infra/cloudflare/workers/email-relay/` |
| **mailer-inbound** | Dispatch namespace WASM: commands + commit handler | `60-apps/etzhayyim-project-mailer/wasm/etzhayyim-wasm-mailer-inbound-ml1nb0nd/` |

## Cost & Provider Selection

| Direction | Provider | Cost | Rationale |
|---|---|---|---|
| **Inbound** | **Cloudflare Email Routing** | **$0** | MX → email-relay Worker → PDS → convo。運用負荷ゼロ |

## Internal PDS Write Auth

`etzhayyim-email-relay` writes inbound mail through the PDS service binding. The
PDS worker currently requires the legacy internal trust header plus an HMAC:

```text
x-kotodama-verified: true
x-etzhayyim-internal-hmac: HMAC-SHA256("POST:/xrpc/{nsid}:{minute_epoch}", claim_settler_hmac)
```

The Worker binds Secrets Store `claim_settler_hmac` as
`SS_CLAIM_SETTLER_HMAC`. Without this header, inbound mail can reach the
Cloudflare Email Routing handler but PDS `com.atproto.repo.createRecord` returns
`401 AuthRequired` and no `ai.etzhayyim.apps.mailer.inboundEmail` record is visible.
| **Outbound** | **Resend Free** | **$0** (3K通/月) | DX 最良。SES は sandbox 解除の手間、SMTP 自作は deliverability 管理が割に合わない |

**Scale trigger**: 3K通/月超過 → Resend Pro ($20/mo, 50K通) or SES ($0.10/1K通) に切替検討。
