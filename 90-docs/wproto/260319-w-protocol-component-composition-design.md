---
id: 260319-w-protocol-component-composition-design
title: W Protocol Component Composition Design
status: active
doc_type: explanation
topic: w-protocol-component-composition
authoritative: true
last_verified: 2026-03-20
authoritative_for:
  - cross app wit level typed function call over w protocol
related:
  - 260317-w-protocol-design
  - 260317-w-protocol-wrpc-design
  - 260320-magatama-cloudflare-containers-evaluation
supersedes: []
superseded_by: []
---

# W Protocol Component Composition Design

Date: 2026-03-19

## Problem

Each App runs in its own account-level Worker. Apps communicate via W Protocol conversation channels (`wrpc-transport-wproto`, 583µs), but there is no WIT-level typed function call between apps. Extensions are limited to same-Worker prebuild components.

## Solution

`wrpc-transport-wproto`: cross-app WIT function calls over W Protocol.

```
App A                                    App B
┌─────────────────────┐                  ┌─────────────────────┐
│ Invoke("",          │                  │ app.Handle(   │
│   "magatama:i18n@1.0.0",│                  │   "translate",      │
│   "translate",       │                  │   "translate-text", │
│   "translate-text",  │                  │   handler)          │
│   params)            │                  │                     │
└────────┬────────────┘                  └────────┬────────────┘
         │ WIT: remote-call                       │ WIT: serve
┌────────▼────────────┐   wrpc.call      ┌────────▼────────────┐
│ host/remote_call.rs │ ────────────►    │ host/remote_handler │
│  1. resolve         │                  │  1. decode          │
│  2. governance      │ ◄────────────    │  2. call export     │
│  3. dispatch        │   wrpc.reply     │  3. reply           │
└─────────────────────┘                  └─────────────────────┘
```

## Architecture Layers

| Layer | Responsibility | Crate |
|---|---|---|
| Wire format | CBOR envelope encode/decode, inflight correlation | `wproto::wrpc_transport` |
| Registry trait | `InterfaceRegistry` (resolve, discover_by_tags) | `wproto::wrpc_transport` |
| Registry impl | `CypherInterfaceRegistry` (Cypher graph backed) | `magatama-engine/src/host/remote_call.rs` |
| Host import | `invoke` (ai-gftd:invoke/invoke) (invoke, invoke-async, discover) | `magatama-engine/src/host/remote_call.rs` |
| Host export | `serve` (ai-gftd:serve/serve) (handle-call dispatch) | `magatama-engine/src/host/remote_handler.rs` |
| Go SDK | `Invoke("",)`, `app.Handle()` | `magatama-go/invoke.go` + `remote_types.go` |
| Audit | `WrpcAuditBlock` (MDAG-committed automatically) | `wproto::blocks` |

## WIT Interface

```wit
// magatama:core@1.0.0

interface remote-call {
    invoke: func(%package: string, iface: string, %function: string, params-cbor: list<u8>) -> result<list<u8>, string>;
    invoke-async: func(%package: string, iface: string, %function: string, params-cbor: list<u8>) -> result<string, string>;
    discover: func(%package: string, iface: string) -> result<list<u8>, string>;
}

interface serve {
    handle-call: func(iface: string, %function: string, params-cbor: list<u8>, caller-did: string, caller-org-id: string) -> result<list<u8>, string>;
}
```

## Wire Format

### wrpc.call (machine path)

```rust
pub struct WrpcCallEnvelope {
    pub target_package: String,      // "magatama:i18n@1.0.0"
    pub target_interface: String,    // "translate"
    pub target_function: String,     // "translate-text"
    pub params: Vec<u8>,             // CBOR
    pub caller_did: String,
    pub caller_nanoid: String,
    pub caller_org_id: String,
    pub correlation_id: String,      // ULID
    pub reply_channel_id: String,
}
```

### agent.skill-request (agent path)

```rust
pub struct SkillRequest {
    pub text: String,                    // NL context
    pub skill_call: Option<SkillCall>,   // structured call (optional)
    pub conversation_id: String,
    pub urgency: String,
}
```

## Envelope Kinds

| kind | Path | Description |
|---|---|---|
| `wrpc.call` | Machine | Direct WIT function call |
| `wrpc.reply` | Machine | Response |
| `agent.skill-request` | Agent | NL + optional SkillCall |
| `agent.skill-result` | Agent | NL + result |
| `agent.negotiate` | Agent | Capability negotiation |
| `agent.delegate` | Agent | Responsibility delegation |

## Configuration

```toml
[interfaces]
package = "magatama:handotai@1.0.0"

[[interfaces.provides]]
name = "news-feed"
functions = [{ name = "latest", params = "limit: u32", returns = "result<list<u8>, string>" }]
tags = ["semiconductor", "news"]
phase = "operational"
skill_prompt = "Use when asking about semiconductor news"

[[interfaces.requires]]
package = "magatama:i18n@1.0.0"
interface = "translate"
functions = ["translate-text"]
```

## Cypher Graph Schema

```cypher
(:ProvidedInterface {id, package, name, phase, tags_json, functions_json, skill_prompt})
  -[:PROVIDED_BY]->(:App {nanoid})

(:RequiredInterface {id, package, interface, required_functions_json})
  -[:REQUIRED_BY]->(:App {nanoid})

(:RequiredInterface)-[:SATISFIED_BY]->(:ProvidedInterface)
(:ProvidedInterface)-[:HAS_ACCESS_POLICY]->(:AccessPolicy {allow_packages, require_same_org})
```

## Governance

`host/remote_call.rs` checks `AccessPolicy` before dispatch:
- `allow_packages`: glob patterns (e.g. `["gftd:*"]`)
- `require_same_org`: caller org_id must match target
- No policy = allow by default

## Key Design Decisions

1. **wproto is storage-agnostic**: `InterfaceRegistry` is a trait, not Cypher-bound
2. **Cypher impl in host layer**: `CypherInterfaceRegistry` in `magatama-engine`
3. **MDAG audit automatic**: wrpc.call/reply are standard W Protocol envelopes → existing pipeline commits them
4. **Two paths**: machine (wrpc.call, lowest latency) and agent (agent.skill-*, with NL reasoning)
5. **WIT rebuild required**: adding remote-call/serve to world.wit triggers full component rebuild
