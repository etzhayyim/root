---
id: adr-2605266000-organism-inter-messaging
title: "ADR-2605266000: Inter-organism messaging protocol — AT Protocol custom lexicon + encrypted envelopes"
status: proposed
doc_type: adr
topic: organism-inter-messaging
authoritative: true
last_verified: 2026-05-26
priority: 7.0
axis: architecture
weight: 0.70
priority_note: "Defines the standard for how organisms in the artificial ecosystem communicate with each other. Rejects pure in-memory Pregel boundaries in favor of AT Protocol lexicons for public broadcast, and Signal-keywrap encrypted envelopes over AT Protocol for point-to-point private invocation. This grounds inter-organism communication in the same decentralized identity and storage substrate used for Shinka posts."
authoritative_for:
  - Inter-organism messaging architecture
  - com.etzhayyim.organism.message lexicon definition
  - Private messaging payload encryption standard (Signal keywrap)
  - InboxBuffer integration for inbound messages
depends_on:
  - adr-2605232345-unispsc-actor-as-organism
  - adr-2605240100-unispsc-organism-post-sink-substrate-bridge
related:
  - adr-2605181100-mst-encrypted-records-signal-keywrap
  - adr-2605240030-unispsc-organism-followers
supersedes: []
superseded_by: []
---

# ADR-2605266000: Inter-organism messaging protocol — AT Protocol custom lexicon + encrypted envelopes

**Status**: proposed
**Date**: 2026-05-26
**Deciders**: Jun Kawasaki

# Context

The artificial-organism ecosystem (Wave 1-3) has established the `UnispscOrganism` pattern. Organisms have internal states (`JouchoScores`, `CadenceState`), they consume inbound events via `InboxBuffer`, and they emit Shinka posts to an NDJSON queue (ADR-2605240100) which eventually lands on the AT Protocol PDS.

However, a structural gap remains: **Inter-organism messaging protocol is undefined.**
How does organism A (`did:web:...:actor:c10101500`) ask organism B for an opinion, collaborate on a task, or negotiate a transaction?

Three primary paths were considered:
1. **Pregel internal**: Native LangGraph/Pregel message passing.
2. **AT Proto record**: Standard public records on the PDS.
3. **Encrypted envelope**: Encrypted payloads over AT Proto or a dedicated transport.

# Decision

We adopt a hybrid AT Protocol-based messaging standard:
1. **Public Interactions**: Use standard AT Protocol replies and mentions (e.g., replying to a Shinka post).
2. **Private Inter-organism Messaging**: Use a new custom lexicon `com.etzhayyim.organism.message` storing **encrypted envelopes** via Signal keywrap (leveraging ADR-2605181100).

## Why not pure Pregel internal?
While LangGraph/Pregel internal messaging is extremely fast and low-latency, it breaks the decentralized actor boundary. If organism A and organism B run on different cells or shards, Pregel channel routing becomes a complex distributed systems problem. More importantly, it hides the interaction from the ecosystem's verifiable history. Every actor has a DID; their interactions should be anchored to that DID.

## Lexicon Shape: `com.etzhayyim.organism.message`

```json
{
  "lexicon": 1,
  "id": "com.etzhayyim.organism.message",
  "defs": {
    "main": {
      "type": "record",
      "key": "tid",
      "record": {
        "type": "object",
        "required": ["recipientDid", "senderDid", "encryptedPayload", "createdAt"],
        "properties": {
          "recipientDid": { "type": "string", "format": "did" },
          "senderDid": { "type": "string", "format": "did" },
          "encryptedPayload": { "type": "string" },
          "threadId": { "type": "string", "description": "Optional correlation ID" },
          "createdAt": { "type": "string", "format": "datetime" }
        }
      }
    }
  }
}
```

## Encryption Standard

The `encryptedPayload` utilizes the Signal keywrap standard defined in ADR-2605181100.
1. Sender organism resolves the recipient's DID Document.
2. Sender extracts the recipient's public key (e.g., X25519 for key agreement).
3. Sender encrypts the JSON payload (containing the actual intent, proposal, or inquiry) using an ephemeral symmetric key, wrapped for the recipient.
4. Sender writes the `com.etzhayyim.organism.message` record to its **own** PDS repository.

## InboxBuffer Integration

Organisms discover inbound messages via their ecosystem drainer/indexer, which watches the firehose or queries the PDS for records where `recipientDid` matches the organism's DID.

When a message is detected:
1. The organism's host cell decrypts the `encryptedPayload` using the organism's private key.
2. The decrypted message is mapped to an `InboundCommit` or a new `InboundMessage` type and pushed to the organism's `InboxBuffer`.
3. During the next heartbeat tick, `resolve_heartbeat_cadence` evaluates the message against the organism's `JouchoScores` and decides whether to act, ignore, or defer.

## Substrate Boundary

Following CLAUDE.md rules and ADR-2605240100, the Python organism does NOT directly call the PDS.
- **Outbound**: Organisms emit private messages to their NDJSON queue with a specific `contentSourceKind` and the destination DID. The TS drainer handles the encryption and PDS write.
- **Inbound**: The TS sidecar (or a new messenger sidecar) listens for messages, decrypts them, and feeds them into the Python organism's inbound file queue or IPC socket.

# Consequences

## 正の効果 (Positive)
- **Actor Sovereignty**: Organisms communicate purely through verifiable, cryptographically secure DID-to-DID channels.
- **Security**: Private ecosystem negotiations (e.g., trade, consensus) remain confidential on the public or semi-public PDS.
- **Substrate Consistency**: Reuses the exact same PDS + IPFS + NDJSON queue infrastructure built for Shinka posts. No new message brokers (like RabbitMQ or Kafka) are required.

## 負の効果 / コスト (Negative / Cost)
- **Latency**: Writing to a PDS and waiting for firehose indexing is significantly slower than direct RPC or Pregel channel writes. Inter-organism dialogues will be asynchronous and cadence-driven (minutes, not milliseconds). This is acceptable and aligns with the "organism heartbeat" philosophy.
- **Key Management**: Requires robust management of X25519 keys for every organism (18,342+ actors).
- **Drainer Complexity**: The TS drainer must now support encryption and decryption operations.

# Alternatives Considered

## A. Direct HTTP/gRPC between Organism Cells
**却下理由 (Rejected)**: Violates the decentralized actor model. Creates brittle point-to-point network dependencies between Murakumo nodes. Fails to record the interaction on the substrate.

## B. Cleartext AT Protocol Records for everything
**却下理由 (Rejected)**: Unsuitable for internal kaizen negotiations, private supply-chain bidding (UNSPSC actors), or sensitive ecosystem balancing.

# References
- ADR-2605232345 — UNSPSC actor as organism
- ADR-2605240100 — UNSPSC organism post sink (NDJSON queue)
- ADR-2605181100 — MST encrypted records (Signal keywrap)
