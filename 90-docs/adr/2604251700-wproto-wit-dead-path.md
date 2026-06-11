---
id: 2604251700-wproto-wit-dead-path
title: wproto / WIT を legacy dead path とし、AT Protocol 標準 API と Lexicon JSON に統一する
status: active
doc_type: adr
topic: protocol-contract-cleanup
authoritative: true
last_verified: 2026-04-25
authoritative_for:
  - wproto deprecation
  - WIT contract deprecation
  - AT Protocol client/library selection
related:
  - adr-2604231811-atproto-extension-service-layers
  - adr-2604231821-atproto-oauth-wire-format-snake-case
  - 0049-python-udf-shared-pool-runtime
supersedes: []
superseded_by: []
---

# Context

`@etzhayyim/wproto` and WIT were transitional layers:

- `@etzhayyim/wproto` duplicated client/session/XRPC concerns now covered by official AT Protocol libraries and plain XRPC wire calls.
- WIT duplicated contract ownership now held by AT Protocol Lexicon JSON for active TS Native and Worker paths.
- The `W*` naming surface in yoro made legacy protocol details look like active product/domain concepts.

Keeping these paths active creates Shannon redundancy: multiple sources appear authoritative for the same client API, session model, command schema, and transport behavior.

# Decision

`wproto` and WIT are legacy dead paths for active application code.

Active code must use:

- `@atproto/api` and other official AT Protocol libraries for standard AT Protocol client/session behavior.
- AT Protocol XRPC wire format (`/xrpc/{nsid}`) for app-specific `com.etzhayyim.*` procedures and queries.
- AT Protocol Lexicon JSON as the contract SSoT for active command/query schemas.
- Domain names such as `PostView`, `FeedItem`, `FeedGeneratorView`, `Session`, `isDid`, and `subscribeAtprotoStream`; do not introduce new protocol-derived `W*` names.

Allowed legacy references:

- Historical ADRs and migration notes may mention `wproto` / WIT as prior art.
- Archived paths may remain for git history and forensic comparison.
- Existing generated or external artifacts may be removed in follow-up cleanup when their owning build path is retired.

# Consequences

- New code must not import `@etzhayyim/wproto`.
- `10-protocol/wproto` must not be a workspace dependency or active app layer.
- WIT must not be used as the active contract source for TS Native / Worker apps.
- `@etzhayyim/xrpc` remains server-side infrastructure only where it provides Worker dispatch, service-binding transport, NSID utilities, or service-auth primitives.
- Browser and UI code should prefer official AT Protocol SDKs or local app-specific adapters built on the AT Protocol XRPC wire format.

# Alternatives Considered

1. Keep `@etzhayyim/wproto` as an adapter facade.
   - Rejected: preserves the dead path and keeps `W*` naming alive.

2. Rename `wproto` internals but keep WIT for schemas.
   - Rejected: still leaves two contract SSoTs and makes code generation ownership ambiguous.

3. Delete all historical references immediately.
   - Rejected: too much churn and loses useful migration context. Historical/archived references are acceptable when clearly marked non-active.

# References

- `@atproto/api`
- `00-contracts/lexicons/`
- `10-protocol/xrpc`
