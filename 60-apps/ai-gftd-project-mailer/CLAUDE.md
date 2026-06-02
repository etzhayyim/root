# ai-gftd-project-mailer

mailer.etzhayyim.com — DID-based email platform。`performerType: system`。

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
  → ai-gftd-email-relay Worker (account-level, email() handler)
  → worker.ts:
    1. Read raw MIME stream, parse headers/body
    2. PDS createRecord("inboundEmail", {from, to_local, subject, body_text, ...})
    3. Resolve DID: {handle}@etzhayyim.com → did:web:{handle}.etzhayyim.com
    4. PDS com.etzhayyim.projector.createProjectConvo({participantDids, kind, name}) → convoId
    5. PDS com.etzhayyim.projector.sendProjectMessage({convoId, text: formatted email})
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

W Protocol `com.etzhayyim.convo` で配信:
- `com.etzhayyim.projector.createProjectConvo({participantDids, kind, name})` — mailer DID と recipient DID の project convo 作成
- `com.etzhayyim.projector.sendProjectMessage({convoId, text})` — メール内容をテキストメッセージとして送信
- yoro convo tab に通常メッセージとして表示 (recipient が AI Agent なら Murakumo LLM auto-reply)

## Infra

| Layer | Implementation | Location |
|---|---|---|
| **DNS** | MX (`route{1,2,3}.mx.cloudflare.net`), SPF, DMARC, Resend DKIM | `50-infra/pulumi/cloudflare/dns.ts` |
| **Email Routing** | Zone enable + catch-all → email-relay Worker | `50-infra/pulumi/cloudflare/email-routing.ts` |
| **email-relay** | Account-level Worker: email handler + PDS service binding + KV | `50-infra/cloudflare/workers/email-relay/` |
| **mailer-inbound** | Dispatch namespace WASM: commands + commit handler | `60-apps/ai-gftd-project-mailer/wasm/ai-gftd-wasm-mailer-inbound-ml1nb0nd/` |

## Cost & Provider Selection

| Direction | Provider | Cost | Rationale |
|---|---|---|---|
| **Inbound** | **Cloudflare Email Routing** | **$0** | MX → email-relay Worker → PDS → convo。運用負荷ゼロ |

## Internal PDS Write Auth

`ai-gftd-email-relay` writes inbound mail through the PDS service binding. The
PDS worker currently requires the legacy internal trust header plus an HMAC:

```text
x-magatama-verified: true
x-gftd-internal-hmac: HMAC-SHA256("POST:/xrpc/{nsid}:{minute_epoch}", claim_settler_hmac)
```

The Worker binds Secrets Store `claim_settler_hmac` as
`SS_CLAIM_SETTLER_HMAC`. Without this header, inbound mail can reach the
Cloudflare Email Routing handler but PDS `com.atproto.repo.createRecord` returns
`401 AuthRequired` and no `com.etzhayyim.apps.mailer.inboundEmail` record is visible.
| **Outbound** | **Resend Free** | **$0** (3K通/月) | DX 最良。SES は sandbox 解除の手間、SMTP 自作は deliverability 管理が割に合わない |

**Scale trigger**: 3K通/月超過 → Resend Pro ($20/mo, 50K通) or SES ($0.10/1K通) に切替検討。
