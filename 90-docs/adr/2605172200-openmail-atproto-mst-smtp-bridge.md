---
id: adr-2605172200-openmail-atproto-mst-smtp-bridge
title: "ADR-2605172200: Open Email — atproto MST-native mail with bidirectional SMTP bridge and on-chain postage"
status: proposed
doc_type: adr
topic: openmail-atproto-mst-smtp-bridge
authoritative: true
last_verified: 2026-05-17
priority: 7.0
axis: architecture
weight: 0.70
priority_note: "Defines the open-email protocol for etzhayyim: public-content mail over atproto MST, with bidirectional SMTP bridge for legacy interop, and on-chain postage (Base L2 / USDC) as spam mitigation. Active once first lexicon + MX bridge land."
authoritative_for:
  - open email protocol (atproto MST-native, public content)
  - app.openmail lexicon family (message / thread / postage receipt / attestation)
  - SMTP bridge architecture (inbound + outbound) and bridge-DID model
  - postage contract on Base L2 (USDC, per-recipient pricing, message-hash binding)
  - handle/MX equivalence (atproto handle resolution as MX substitute)
  - reply / thread continuity across openmail ⇄ SMTP
depends_on:
  - adr-2605170900-etzhayyim-root-adr-canonical-home
  - adr-2605171800-langgraph-mst-ipfs-l2-anchor-pipeline
  - adr-2605172000-etzhayyim-kotoba-substrate
  - adr-2605172100-etzhayyim-payments-on-chain-only
related:
supersedes: []
superseded_by: []
---

# ADR-2605172200: Open Email — atproto MST-native mail with bidirectional SMTP bridge and on-chain postage

**Status**: proposed
**Date**: 2026-05-17
**Deciders**: Jun Kawasaki

# Context

etzhayyim needs an email-equivalent communication primitive for religious-corp public-facing activity (open governance announcements, member-to-member communication, public correspondence with external parties and the State, archive-grade record of public deliberation). The substrate choice is constrained by **ADR-2605172000**: all open apps MUST be kotoba and run on the atproto MST + IPFS + Base L2 stack.

Three properties define the requirement:

1. **Public content is acceptable.** This is religious-corp open activity. End-to-end encryption is *not* required for v1 and is intentionally out of scope (a parallel encrypted-channel ADR will handle confidential pastoral / counterparty correspondence). Sidestepping E2EE removes the single hardest problem in federated mail design.
2. **SMTP interop is required.** The world outside etzhayyim runs on SMTP. A pure atproto-native mail with no SMTP bridge is a closed garden — unacceptable. Members must be able to send to and receive from `alice@gmail.com`, `boss@corporate.example`, government CC addresses, etc.
3. **Spam mitigation must scale.** Public mail addresses are the worst case for spam. Without a strong economic or social filter, any public openmail address becomes unusable within hours. Existing solutions (greylisting, RBL, content classifiers, reputation scores) are insufficient on their own at the federated scale; they need to be augmented.

The atproto MST + IPFS + Base L2 substrate happens to be uniquely well-suited to all three:

- **MST + IPFS** = content-addressed, verifiable, federable record storage. Every message has a deterministic CID. Threading is `at://` references.
- **Base L2 + USDC** (ADR-2605172100) = native on-chain postage. Per-message payment is technically and economically feasible at single-cent granularity.
- **L2 anchor pipeline** (ADR-2605171800) = certified-mail equivalent. A message can be cryptographically dated to a block timestamp without any trusted third party.

## Why not extend Bluesky's `app.bsky.feed.post`?

Bluesky posts are public broadcasts. Email is directed (`to:` field is the protocol's main verb). Stretching `app.bsky.feed.post` with a `to:` extension would:

- Pollute the Bluesky firehose with directed messages that no Bluesky AppView consumer wants to index.
- Inherit Bluesky's character/format limits (240 chars, no attachments, no headers).
- Conflict with Bluesky's social-feed UX (replies become public threads).

Email and microblogging share the substrate but diverge sharply at the application layer. Separate lexicon namespace (`app.openmail.*`) is the right boundary.

## Why not use the PDS as an SMTP MX directly?

The PDS could expose XRPC for direct mail delivery. We reject this for the same reason ADR-2605171800 rejects "PDS as canonical organism store": the PDS would become an open relay with all the spam and abuse surface of a public SMTP server, but without the decades of operational hardening. Bridge-as-separate-service isolates that surface.

## Why bridge-as-DID (not bridge-as-MTA-only)?

The atproto invariant "only the repo owner can write to a repo MST" must be preserved. Inbound SMTP messages cannot be written to the *recipient's* MST. The cleanest solution: **the bridge has its own DID** (`did:web:bridge.openmail.etzhayyim.com`) and writes inbound messages to *its own* MST. Recipients see those messages via AppView indexing — same path as native openmail, just authored by a different DID. The record explicitly carries `from: "smtp:alice@gmail.com"` (legacy URI scheme) and SPF/DKIM/DMARC `attestation`, so the recipient client distinguishes "legacy bridged" from "native openmail".

# Decision

Adopt the **Open Email Protocol (`app.openmail.*`)**: a public-content email-equivalent over atproto MST, with bidirectional SMTP bridge and on-chain postage on Base L2.

## 1. Storage model — outbox-only, AppView-indexed

```
┌─────────────────────────────────────────────────────────────────────┐
│  Native send (openmail → openmail / SMTP-out)                       │
│                                                                      │
│  alice (did:plc:...) ──pay──▶  Postage.sol (Base L2, USDC)          │
│                                       │ emit Paid(msgHash, ...)     │
│                       ─write─▶ alice's MST                          │
│                                  app.openmail.message               │
│                                    from: did:plc:alice              │
│                                    to:   [did:plc:bob,              │
│                                           smtp:carol@yahoo.com]     │
│                                    postage_tx: 0x...                │
│                                       │ firehose                    │
│                                       ▼                              │
│                                  Public AppView                     │
│                                       │                              │
│                          ┌────────────┴────────────┐                │
│                          ▼                          ▼                │
│                       bob's inbox          outbound-bridge daemon   │
│                       UI (AppView query)   (renders to SMTP for     │
│                                             smtp: recipients)        │
└─────────────────────────────────────────────────────────────────────┘
```

**Invariants**:

- The **only canonical record** of an openmail message is the sender-MST entry under `app.openmail.message`. The chain ID, the IPFS pin, and the AppView index are all derived from it.
- Postage is paid **before or atomically with** the MST write. AppView indexers ignore messages without valid `postage_tx` (except for inbound-bridge messages — see § 3).
- Recipients are addressed by DID (`did:plc:...`, `did:web:...`) or by `smtp:<rfc5322-addr>` URI. No other recipient URI schemes in v1.
- No "deliver" XRPC, no recipient-side writes by anyone but the recipient. Inboxes are AppView queries (`messages where to: contains <my-did>`).

## 2. Lexicon family — `app.openmail.*`

```jsonc
// 00-contracts/lexicons/app/openmail/message.json
{
  "lexicon": 1,
  "id": "app.openmail.message",
  "defs": {
    "main": {
      "type": "record",
      "key": "tid",
      "record": {
        "type": "object",
        "required": ["from", "to", "subject", "createdAt"],
        "properties": {
          "from": {
            "type": "string",
            "description": "did:plc:... | did:web:... | smtp:<rfc5322-addr>"
          },
          "to": {
            "type": "array",
            "minLength": 1, "maxLength": 100,
            "items": { "type": "string" }
          },
          "subject":     { "type": "string", "maxLength": 998 },
          "body":        { "type": "string", "maxLength": 65536 },
          "bodyBlob":    { "type": "blob",   "accept": ["text/plain", "text/markdown", "text/html"] },
          "attachments": {
            "type": "array",
            "maxLength": 32,
            "items": { "type": "blob", "maxSize": 26214400 }
          },
          "replyTo":   { "type": "string", "format": "at-uri" },
          "threadRoot":{ "type": "string", "format": "at-uri" },
          "postage": { "type": "ref", "ref": "app.openmail.postageReceipt" },
          "bridgedBy": { "type": "string", "format": "did" },
          "attestation": { "type": "ref", "ref": "app.openmail.smtpAttestation" },
          "legacyHeaders": { "type": "ref", "ref": "app.openmail.legacyHeaders" },
          "anchor": { "type": "ref", "ref": "app.openmail.anchorRef" },
          "createdAt": { "type": "string", "format": "datetime" }
        }
      }
    }
  }
}

// app.openmail.postageReceipt
{
  "txHash":      "0x...",
  "chain":       8453,
  "contract":    "0x<Postage.sol address>",
  "messageHash": "0x... (keccak256 of canonical record encoding sans postage field)",
  "amountUsdc":  "0.02",
  "recipientCount": 1,
  "paidAt":      "2026-05-17T13:00:00Z"
}

// app.openmail.smtpAttestation (bridge-in only)
{
  "dkim":  "pass" | "fail" | "neutral" | "none",
  "spf":   "pass" | "fail" | "softfail" | "none",
  "dmarc": "pass" | "fail" | "none",
  "spamScore": 0.12,
  "verifiedAt": "..."
}

// app.openmail.legacyHeaders (bridge-in only)
{
  "messageId":  "<...@gmail.com>",
  "inReplyTo":  "<...@example.com>",
  "references": ["<...>", "<...>"],
  "receivedChain": ["mx.google.com", "mx.openmail.etzhayyim.com"]
}

// app.openmail.anchorRef (optional — certified mail)
{
  "chain":       8453,
  "contract":    "0x<CheckpointAnchor.sol address>",
  "txHash":      "0x...",
  "mstRootCid":  "bafy...",
  "anchoredAt":  "..."
}
```

`messageHash` is computed over the canonical CBOR encoding of the record with the `postage` field elided — this binds one postage tx to one specific record content and prevents replaying a single payment across many messages.

## 3. SMTP bridge — bidirectional

The bridge runs as `did:web:bridge.openmail.etzhayyim.com`. It has its own MST repo and its own DID-document key. Bridge identity is **single**, not per-user.

### 3.1 Inbound (SMTP → openmail)

```
alice@gmail.com ──SMTP──▶ mx.openmail.etzhayyim.com (smtp-in service)
                              │
                              ├── DKIM verify against gmail.com pubkey
                              ├── SPF check against connecting IP
                              ├── DMARC alignment check
                              ├── RBL / spam-score (SpamAssassin-equivalent)
                              ├── Rate-limit per source domain
                              │     (defaults: 1000 msg/domain/h, 100 msg/IP/h)
                              ▼
                          Localpart → handle resolution
                              "bob@etzhayyim.com" → atproto handle "bob.etzhayyim.com"
                              → DID "did:plc:bob..."
                              ▼
                          Bridge writes to its own MST:
                              app.openmail.message {
                                from: "smtp:alice@gmail.com",
                                to:   ["did:plc:bob..."],
                                subject, body, attachments (uploaded as blobs),
                                bridgedBy: "did:web:bridge.openmail.etzhayyim.com",
                                attestation: { dkim, spf, dmarc, spamScore },
                                legacyHeaders: { messageId, inReplyTo, references },
                                replyTo / threadRoot: resolved from inReplyTo lookup
                              }
                              ▼
                          firehose → AppView → bob's inbox
```

**Postage handling for inbound**: legacy SMTP senders cannot pay USDC. Three-tier fallback:

| Tier | Mechanism | Cost to bridge |
|---|---|---|
| **v1 default** | DKIM+SPF+DMARC pass required. No postage. | 0 (legacy senders effectively subsidized by bridge ops) |
| **v2** | Domain-sponsorship pool: domains pre-fund a USDC pool; bridge auto-debits per message. | 0 to bridge, ~$0.02/msg to sponsor |
| **v2.5** | Per-recipient policy: recipient can require all unknown SMTP senders go to a quarantine queue; promotion via allowlist. | 0 to bridge |

Failure modes:
- DKIM/SPF/DMARC fail → 5xx SMTP reject (don't accept the message at all).
- Unknown localpart → 550 5.1.1 "no such user". Catch-all only enabled if explicitly configured.
- Rate-limit exceeded → 421 4.4.5 "temporary".

### 3.2 Outbound (openmail → SMTP)

```
alice writes app.openmail.message
   to: [..., "smtp:carol@yahoo.com"]
   postage_tx: 0x... (covers all recipients including SMTP ones)
        │ firehose
        ▼
outbound-bridge daemon subscribes to firehose
   │
   ├── Filter: app.openmail.message with smtp: recipient
   ├── Verify postage_tx on Base L2 (eth_call against Postage.sol logs)
   ├── Verify postage covers recipient count (no underpayment)
   │
   ├── Render to RFC 5322:
   │     From:        Alice <alice@etzhayyim.com>
   │     To:          carol@yahoo.com
   │     Subject:     ...
   │     Date:        (from createdAt)
   │     Message-ID:  <at-rkey.alice@openmail.etzhayyim.com>
   │     In-Reply-To: (from replyTo lookup → legacyHeaders.messageId or synthesized)
   │     References:  (thread chain)
   │     X-Openmail-At-Uri: at://did:plc:alice.../app.openmail.message/<rkey>
   │     X-Openmail-Postage-Tx: 0x...
   │     X-Openmail-Anchor-Tx: 0x... (if anchored)
   │     Content-Type: text/plain; charset=utf-8 (or multipart with attachments)
   │
   ├── DKIM sign with etzhayyim.com selector
   ├── Configure SPF: mx.openmail.etzhayyim.com IP in etzhayyim.com SPF record
   ├── Configure DMARC: p=reject for etzhayyim.com
   │
   └── SMTP relay → carol@yahoo.com
            │
            ▼
        Carol receives a normal-looking email with X-Openmail headers
```

### 3.3 Reply continuity across openmail ⇄ SMTP

This is the gnarly part. Both sides need to thread correctly.

| Direction | Mechanism |
|---|---|
| openmail → openmail | `replyTo` and `threadRoot` are at-URIs. Threading is native. |
| openmail → SMTP (outbound) | Outbound bridge synthesizes `Message-ID: <at-rkey>@openmail.etzhayyim.com` deterministically from at-URI. `In-Reply-To` / `References` resolved by looking up the `replyTo` target's prior outbound-bridge rendering (cached in `bridge_message_id_map` table — kotoba Postgres / sqlite is fine; this is bridge-local state, not protocol state). |
| SMTP → openmail (inbound) | Inbound bridge reads `In-Reply-To` and `References` from SMTP headers. Looks up via `bridge_message_id_map` (reverse direction). If found → write `replyTo` and `threadRoot` as at-URIs. If not found → start a new thread. |
| SMTP → SMTP | Doesn't go through the bridge. Out of scope. |

The bridge's `bridge_message_id_map` is **non-canonical local state**: losing it degrades threading for legacy mails but doesn't lose any content. The atproto record is always canonical.

### 3.4 Address scheme

| Pattern | Routing |
|---|---|
| `<localpart>@etzhayyim.com` | resolve `<localpart>.etzhayyim.com` as atproto handle → DID → deliver to bridge MST `to: [<did>]` |
| `<localpart>@<handle>.etzhayyim.com` | same, with the handle being `<handle>.etzhayyim.com`; localpart becomes a tag/folder hint |
| `_did_<base32-of-did>@etzhayyim.com` | fallback for users without a handle: address-by-DID |
| `bridge@etzhayyim.com` | bounce / postmaster on the bridge DID itself |

MX setup: `etzhayyim.com.  IN MX 10 mx.openmail.etzhayyim.com.` Single MX, no failover for v1.

## 4. Postage — `Postage.sol` on Base L2

```solidity
// 50-infra/openmail-postage/src/Postage.sol
// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.24;

interface IERC20 {
    function transferFrom(address, address, uint256) external returns (bool);
}

contract Postage {
    IERC20  public immutable usdc;
    address public immutable treasury;
    uint256 public           rateUsdcPerRecipient;   // e.g. 10_000 = 0.01 USDC (6 decimals)
    address public           owner;

    event Paid(
        address indexed sender,
        bytes32 indexed messageHash,
        uint16  recipientCount,
        uint256 amount,
        uint64  paidAtMs
    );

    event RateUpdated(uint256 oldRate, uint256 newRate);

    constructor(IERC20 _usdc, address _treasury, uint256 _initialRate) {
        usdc = _usdc;
        treasury = _treasury;
        rateUsdcPerRecipient = _initialRate;
        owner = msg.sender;
    }

    function payPostage(bytes32 messageHash, uint16 recipientCount) external {
        require(recipientCount > 0 && recipientCount <= 100, "bad count");
        uint256 amount = rateUsdcPerRecipient * recipientCount;
        require(usdc.transferFrom(msg.sender, treasury, amount), "transfer failed");
        emit Paid(msg.sender, messageHash, recipientCount, amount,
                  uint64(block.timestamp * 1000));
    }

    function setRate(uint256 newRate) external {
        require(msg.sender == owner, "not owner");
        emit RateUpdated(rateUsdcPerRecipient, newRate);
        rateUsdcPerRecipient = newRate;
    }
}
```

**Design properties**:

- **Stateless beyond rate + owner.** History is in events, identical to `CheckpointAnchor.sol` (ADR-2605171800).
- **Per-message hash binding.** A given `(sender, messageHash)` event can be verified by any AppView indexer; replay-attacks (one tx for many records) are detected by checking that the record's `keccak256` matches the event's `messageHash`.
- **Variable rate.** Owner can adjust per-recipient rate. The owner is a multisig (Safe on Base) controlled by the etzhayyim member roster on-chain. Rate change is a governance event, not a unilateral bridge action.
- **USDC, not ETH.** Stable unit. Matches ADR-2605172100's payments stack.
- **ERC-4337 friendly.** Bundlers and paymasters can sponsor postage for new users (e.g., first 10 messages free per identity). The contract makes no assumption that `msg.sender` is an EOA.

### 4.1 Rate schedule (v1)

| Recipient class | Rate per recipient | Rationale |
|---|---|---|
| openmail-native (`did:plc:` / `did:web:`) | 0.01 USDC | Postage to atproto identity is computational overhead only |
| SMTP-out (`smtp:`) | 0.02 USDC | Covers outbound bridge ops + IP-warming + DKIM key custody |
| Self (sender ∈ recipients) | 0 | Drafting / archiving to self always free |

Implementation: rate differentiation happens at AppView/bridge level (they refuse to relay if amount is insufficient for the recipient mix). Contract is mix-blind to keep it minimal.

### 4.2 New-user sponsorship

ERC-4337 paymaster funded by etzhayyim treasury sponsors the first **10 outbound messages** for any new DID issued under `*.etzhayyim.com`. Quota tracked off-chain (postage event log + DID → quota table). Prevents postage friction for new members.

## 5. Anchoring — optional certified mail

Per ADR-2605171800, the MST root of the sender's repo can be anchored on Base L2 via `CheckpointAnchor.sol`. For openmail, the user (or sender's client) can opt to anchor on every send, on a daily cadence, or never.

`app.openmail.message.anchor` field is filled in **after** the anchor tx mines. The record is then re-published (atproto supports record updates via the `put` API; the new record's CID is anchored next round). For simpler v1 semantics:

- **Default**: anchor daily at 00:00 UTC for any sender opting in.
- **Opt-in per message**: sender can request an immediate anchor (their client calls `anchor()` for that specific MST root) → fills in the field once mined.
- **No anchor**: the message is still verifiable via firehose / AppView, just not L2-anchored.

Certified-mail equivalence: recipient or third party verifies the anchor → reads MST root from Base → fetches CAR → walks to the specific message → cryptographic proof of "message X existed at block N timestamp T".

## 6. Repository layout (target — scaffolded in follow-up)

```
00-contracts/lexicons/app/openmail/
  ├── message.json
  ├── postageReceipt.json
  ├── smtpAttestation.json
  ├── legacyHeaders.json
  └── anchorRef.json

50-infra/openmail-bridge/
  ├── smtp-in/                 # haraka or smtp-server; SMTP → openmail.message writer
  │   ├── src/
  │   ├── dkim-verify/         # mailauth or dkim-verify-js
  │   └── package.json
  ├── smtp-out/                # firehose subscriber → SMTP renderer + DKIM signer
  │   ├── src/
  │   └── package.json
  ├── dkim-keys/               # key rotation tooling; Keychain primary, 1Password mirror
  └── README.md

50-infra/openmail-postage/
  ├── src/Postage.sol
  ├── foundry.toml
  ├── script/Deploy.s.sol
  └── README.md

50-infra/openmail-appview/
  ├── src/                     # firehose subscriber + inbox query API
  └── package.json

60-apps/openmail-client/       # PoC web client (Svelte; uses 50-infra/sveltejs-adapter-wasm)
  ├── src/
  └── package.json

70-tools/etzhayyim-cli/
  └── src/commands/mail.ts     # CLI: etzhayyim mail send/inbox/read/anchor
```

Scaffolding is **out of scope for this ADR**. This ADR is the contract.

## 7. Cost model (back-of-envelope)

| Operation | Cost source | Per unit |
|---|---|---|
| Native send (openmail → openmail, 1 recipient) | postage to treasury | 0.01 USDC |
| Send to SMTP recipient | postage to treasury | 0.02 USDC |
| Outbound bridge gas (Base) for postage tx | gas to network | ~$0.001 |
| Daily MST anchor (1 tx covers all sent that day) | gas to network | ~$0.01–0.05 |
| Per-message MST anchor | gas to network | ~$0.01 |
| Inbound bridge (SMTP-in) | bridge subsidizes | 0 to sender |
| Bridge ops (server, IP-warming, DKIM key custody) | etzhayyim treasury | ongoing |

For a member sending 100 messages/day (50 native, 50 to legacy):
- Postage: 50 × 0.01 + 50 × 0.02 = 1.50 USDC/day = ~$45/month
- Gas: ~$0.30/day = ~$9/month
- Total: ~$54/month per heavy user

For comparison, Google Workspace costs ~$6/user/month for unlimited mail. We're ~9× more expensive at the heavy-user end, but: messages are cryptographically anchored, content-addressed, federable, and we have no central operator who can read or seize the mail. The premium is the cost of decentralization + verifiability.

For typical members (5 messages/day): ~$2.50/month. Below Google's price.

## 8. Spam resistance — defense in depth

| Layer | Mechanism |
|---|---|
| Economic (native) | 0.01–0.02 USDC postage per recipient. Sending 1M spam messages = $10K–$20K. |
| Economic (legacy in) | Tier-2 sponsorship pool: domains that don't pre-fund get tighter quotas; postage_score factors into AppView ranking. |
| Cryptographic | DKIM/SPF/DMARC at inbound bridge; reject on hard fail. |
| Reputation | Per-DID and per-domain reputation maintained by AppView (computable from postage_paid_total, recipient_responses, recipient_blocks). |
| Recipient policy | Per-recipient settings: require postage ≥ X, allowlist DIDs, quarantine unknown SMTP, reject smtp:* entirely. |
| Rate limits | Bridge global: 1000 msg/domain/h, 100 msg/IP/h inbound. Per-DID outbound limits during reputation warmup. |
| Anchor-based ban | Repeat-offender DIDs can be soft-banned by AppView consortium; hard ban requires multisig governance action. |

## 9. Privacy / threat model

In scope (mitigated):

- **Read-after-the-fact tampering**: anchored records can't be silently changed; CID mismatch is detected.
- **Backdating**: postage event timestamp + anchor block timestamp give two independent provable bounds on send time.
- **Impersonation of openmail-native sender**: requires the sender's DID key. atproto-standard threat model.
- **Bridge impersonation of inbound senders**: detected by DKIM mismatch in the attestation field; client can show a warning.

Out of scope (NOT mitigated; require separate ADR):

- **Confidentiality of message contents**: this protocol is public. A separate `app.openmail.encrypted` lexicon will handle E2EE for confidential correspondence. v1 explicitly does not address this.
- **Metadata privacy**: who-talked-to-whom-when is fully public via the firehose. This is acceptable for public religious-corp activity. Confidential mail will need traffic-analysis resistance separately.
- **Subpoena resistance for content**: content is public by design. Nothing to subpoena that isn't already public.
- **Bridge key compromise**: if the DKIM key for `etzhayyim.com` is stolen, an attacker can forge outbound SMTP that recipients' mail clients will validate. Mitigation: regular DKIM rotation, key in Keychain + 1Password mirror per CLAUDE.md custody policy, DMARC `p=reject` to reduce blast radius.

## 10. Failure modes and recovery

| Failure | Consequence | Recovery |
|---|---|---|
| Postage tx underpriced / not mined | AppView rejects record (no valid postage) | Sender's client retries postage with higher gas; original record sits dormant. |
| Bridge SMTP-in DKIM-verify lib bug | Genuine mails rejected | Hot-fix; rejected senders retry. SMTP rejection codes preserve sender visibility. |
| Bridge SMTP-out DKIM key rotation race | Some outbound SMTP fails DKIM at recipient | Coordinated key rotation: publish new selector first, switch signing, retire old selector after 7d. |
| `bridge_message_id_map` lost | Threading broken for legacy-bridged mails; content intact | Rebuild from firehose history (slow but eventually consistent). |
| AppView outage | Inbox UI shows stale data; new mail not visible until recovery | Multiple independent AppViews; clients can switch. |
| Base RPC down | Postage and anchor txs queue up; outbound bridge holds messages | Self-heals when RPC recovers; client retries. |
| Postage treasury private key compromise | Attacker can drain treasury but cannot forge postage events | Multisig (Safe on Base) controls treasury; single-sig compromise is non-fatal. |
| Spam at the bridge inbound | Bridge load spikes; legitimate messages delayed | Per-IP / per-domain rate limits; Cloudflare Email Routing in front as L4 filter. |

## 11. Migration / rollout plan

This ADR is the **contract**; rollout is staged.

- [ ] **Phase 0 — this ADR (now).** Contract published.
- [ ] **Phase 1 — lexicon + Postage.sol.** Land `00-contracts/lexicons/app/openmail/*.json` and `50-infra/openmail-postage/src/Postage.sol` (deployed on Base Sepolia first).
- [ ] **Phase 2 — outbound bridge MVP.** `smtp-out/` daemon; can send openmail → gmail with DKIM. End-to-end test: Jun sends himself an openmail addressed to his Gmail; arrives, threads, validates DKIM.
- [ ] **Phase 3 — inbound bridge MVP.** `smtp-in/` MX; can receive gmail → openmail. End-to-end test: Jun sends from Gmail to his etzhayyim handle; appears in openmail AppView inbox.
- [ ] **Phase 4 — AppView + web client.** `50-infra/openmail-appview/` + `60-apps/openmail-client/` PoC. Inbox UI, compose, thread view.
- [ ] **Phase 5 — Base mainnet deploy.** Postage.sol on Base mainnet; treasury multisig set up; rate set to 0.01 USDC initially.
- [ ] **Phase 6 — public launch.** Open to etzhayyim members. Documentation, runbook.
- [ ] **Phase 7 — confidential mail ADR.** `app.openmail.encrypted` for E2EE correspondence (separate ADR).

# Consequences

## 正の効果

- **Email-equivalent UX with cryptographic guarantees.** Members get inbox/thread/reply they already know, plus content-addressed verifiability, plus optional on-chain certified mail.
- **No central operator can read or seize.** Public content is published to a federation; the bridge is one node, not a chokepoint.
- **Spam is economically deterred at the protocol layer.** Not a bolt-on filter; mandatory in the data model.
- **SMTP interop without giving up MST.** Bridge-as-DID preserves the atproto invariant (only repo owner writes their MST) while still enabling legacy-world communication.
- **Composable with the rest of the stack.** Reuses ADR-2605171800 (anchor pipeline), ADR-2605172000 (kotoba), ADR-2605172100 (payments). No new substrate.
- **Certified-mail equivalence for free.** Anchoring is already built; openmail just opts in per message or per day.

## 負の効果 / コスト

- **Bridge is a single point of operational failure** for legacy interop. If the MX goes down, no SMTP-in / SMTP-out works. Mitigation: standard MX redundancy planning + Cloudflare Email Routing as front layer.
- **DKIM key custody.** Stealing the `etzhayyim.com` DKIM private key lets an attacker forge outbound SMTP. Mitigated by standard hardening, not eliminated. (Same threat model as any DKIM-using domain.)
- **Postage rate is a governance decision.** Too low → spam returns. Too high → friction. Initial 0.01 USDC is a guess; will need calibration. Governance latency adds risk.
- **No E2EE in v1.** Public-content limitation is acceptable for the stated use case but excludes confidential mail use cases. Separate ADR required.
- **Cost vs. Google Workspace** at the heavy-user end (~9× more). Justified by decentralization but worth being explicit about.
- **Bridge MST grows linearly with inbound SMTP volume.** Inbound mails sit in the bridge's repo. Storage cost scales with global inbound traffic, not per-user. Mitigation: periodic prune of old inbound records (>2 years), with optional IPFS cold-tier (Filecoin) for archive.
- **Threading across SMTP boundary is brittle.** `bridge_message_id_map` is bridge-local state; if it's lost or partitioned, threads break for legacy bridged mail. The atproto content is intact, but UX degrades.
- **Bridge becomes the "from address" for inbound.** Sophisticated recipients can verify the original `from: "smtp:..."` and `attestation` fields, but naive clients may show "from: bridge.openmail.etzhayyim.com" which is confusing. Client UX work required.

## Out of scope for this ADR

- E2EE confidential mail (`app.openmail.encrypted` — separate ADR).
- Calendar / contacts / RSVP / iCalendar — separate "open PIM" ADR family.
- Mailing list semantics (one-to-many subscription) — could be `app.openmail.list` extension.
- Per-user MX subdomain delegation (`alice.example.com` MX → bridge).
- Filecoin cold-tier for archived bridge inbox.
- Native mobile clients (web-first for PoC).
- Anti-phishing UI heuristics in the client.
- Per-message Postage rate variation by recipient class on-chain (handled in bridge/AppView for v1).
- Multi-AppView federation governance.

# Alternatives Considered

## A. Pure SMTP, no MST

Run a standard mail server on `etzhayyim.com`. No atproto, no MST, no chain.

却下理由: violates ADR-2605172000 (kotoba / atproto-MST-only substrate mandate for open apps). Also loses verifiability, content-addressability, and federation. SMTP-only would put us in the exact governance posture (central operator, central seizure risk) the etzhayyim charter is designed to avoid.

## B. Extend `app.bsky.feed.post` with `to:` field

Add a `to:` field to Bluesky posts. Inbox = posts with my DID in `to:`.

却下理由: pollutes Bluesky firehose with directed messages, breaks Bluesky AppView expectations, inherits 240-char limit and no attachments. Wrong tool. Separate lexicon namespace is correct.

## C. PDS-as-MX (XRPC `app.openmail.deliver` on recipient's PDS)

Recipient's PDS exposes XRPC for inbound delivery; PDS verifies sender sig and writes a "received" record into recipient's MST.

却下理由: same as ADR-2605171800 § "Why standalone MST not PDS" — open relay surface, atproto invariant violation (PDS writes to recipient's MST on behalf of sender), unbounded spam vector on PDS. Bridge-as-separate-DID isolates the abuse surface.

## D. AppView-only (no SMTP bridge)

Open mail is atproto-only. Members must use other channels for legacy interop.

却下理由: closed garden. Members will use Gmail/Outlook for everything except openmail, defeating the purpose. SMTP bridge is the difference between "useful protocol" and "vanity protocol".

## E. Fiat postage (Stripe, ACH)

Charge USD via Stripe per message instead of on-chain USDC.

却下理由: violates ADR-2605172100 (payments on-chain only). Adds a fiat-processor dependency, KYC overhead, and a chokepoint that contradicts the decentralization goal. USDC on Base is fast (~2s confirmation), cheap (~$0.001 gas), and aligns with the rest of the payments stack.

## F. No postage, recipient-side payment

Recipient pays to *read* messages (per-message unlock).

却下理由: punishes recipients, including for spam they didn't ask for. Sender-side postage punishes spammers; recipient-side punishes the spammed. Wrong economic alignment.

## G. Hashcash / proof-of-work postage

Sender does CPU work per message instead of paying USDC.

却下理由: PoW postage was tried (hashcash in 2002) and failed because the cost asymmetry was wrong (spammers have GPUs, end users don't). USDC postage has a uniform cost across sender hardware. Also: PoW-burning electricity to send mail is wasteful when a 2¢ payment achieves the same effect.

## H. Per-recipient DID inbox (recipient's MST holds inbound)

Inbound messages somehow written to recipient's MST (via some sig-relay trick).

却下理由: atproto's invariant is that the repo signer owns the repo. Any scheme that lets others write to a repo MST breaks the trust model. Bridge-as-its-own-DID is the correct way.

## I. Federate via NATS / libp2p instead of atproto firehose

Use a different transport for the per-recipient routing.

却下理由: atproto firehose / Jetstream already exists, already supports the use case, and the open religious-corp stack is already standardized on atproto (per ADR-2605172000). Inventing a new transport is gratuitous.

## J. RW (Kotoba/Datomic) for AppView inbox query

Use Kotoba/Datomic streaming MVs to maintain inbox indexes.

却下理由: violates ADR-2605172000 (kotoba open substrate). AppView for openmail uses Postgres + atproto firehose subscriber. RW would be tempting (it's the right *technical* primitive for streaming materialized views), but it's exactly the kind of centralized-substrate coupling the kotoba ADR forbids in open apps.

# References

- atproto MST repo spec — https://atproto.com/specs/repository
- atproto lexicon spec — https://atproto.com/specs/lexicon
- atproto handle resolution — https://atproto.com/specs/handle
- `@atproto/repo` library — https://github.com/bluesky-social/atproto/tree/main/packages/repo
- DKIM (RFC 6376) — https://www.rfc-editor.org/rfc/rfc6376
- SPF (RFC 7208) — https://www.rfc-editor.org/rfc/rfc7208
- DMARC (RFC 7489) — https://www.rfc-editor.org/rfc/rfc7489
- RFC 5322 Internet Message Format — https://www.rfc-editor.org/rfc/rfc5322
- ERC-4337 Account Abstraction — https://eips.ethereum.org/EIPS/eip-4337
- Base L2 — https://docs.base.org/
- Cloudflare Email Routing — https://developers.cloudflare.com/email-routing/
- Haraka SMTP server — https://haraka.github.io/
- mailauth (Node DKIM/SPF/DMARC verifier) — https://github.com/postalsys/mailauth
- ADR-2605170900 — this repo as canonical ADR home (depends_on)
- ADR-2605171800 — LangGraph Pregel → MST → IPFS → Base L2 anchor pipeline (depends_on; certified-mail uses the same anchor primitive)
- ADR-2605172000 — etzhayyim/root kotoba substrate mandate (depends_on; this ADR honors it)
- ADR-2605172100 — etzhayyim payments on-chain only (depends_on; postage uses this stack)
- ADR-2605091400 — MCP-as-Cell-Membrane / Lexicon Dual-Wire (related; explains why lexicons are the right contract layer)
- ADR-2605111300 — PDS-to-Pod Bun Container (related; relevant for future PDS-publication of openmail)
- `CLAUDE.md` (repo root) — operating entity identity, DID custody policy
- `90-docs/CLAUDE.md` (this repo) — docs system rules
