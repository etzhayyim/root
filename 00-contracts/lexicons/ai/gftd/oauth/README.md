# `ai.gftd.oauth.*` — DID-bound OAuth flow extensions

Open spec for the DID-bound OAuth flow used by atproto / etzhayyim agents.
Extends `com.atproto.server.*` with DID-method-aware authorization, DPoP
proof binding, and capability-scoped service-to-service tokens.

## Status

Tranche F scaffolding (Phase 2) per ADR-2605172400.

This is the **spec / lexicon side** of the auth/iam SPLIT. The running
auth Worker + D1 KEYS_DB (session storage, revocation list) remains in
vendor scope per the Custody axis (session state is operator-held).

## NSIDs (planned)

- `ai.gftd.oauth.getAuthorizationServer` — discovery doc (RFC 8414 extended)
- `ai.gftd.oauth.authorizeWithDpop` — DPoP-bound authorization request
- `ai.gftd.oauth.exchangeServiceAuth` — service-to-service token exchange (`x-internal-trust` callers)
- `ai.gftd.oauth.revokeBindingByDid` — revoke all bindings for a DID

## See also

- `10-protocol/did-etzhayyim/` (DID method spec, Wave 2)
- ADR-2605172400 (vendor: 3-axis split rule + Tranche F)
- [ADR-2604231821 atproto OAuth wire-format snake_case](https://github.com/gftdcojp/ai-gftd-apps-gftdcojp/blob/main/90-docs/adr/2604231821-atproto-oauth-wire-format-snake-case.md) (foundational)
- [ADR-2604240914 OAuth RS DPoP + revoke + introspect](https://github.com/gftdcojp/ai-gftd-apps-gftdcojp/blob/main/90-docs/adr/2604240914-oauth-rs-binding-revocation-introspection.md) (foundational)
- [ADR-2605152100 Phase 3 callsite migration](https://github.com/gftdcojp/ai-gftd-apps-gftdcojp/blob/main/90-docs/adr/2605152100-etzhayyim-github-org-boundary.md) (vendor-side auth callsite work)

## Wire-format note

Per ADR-2604231821, OAuth wire-format fields are `snake_case` (this is the
sole exception to the camelCase identifier convention; it preserves
compatibility with RFC 6749 / 8414 / 8707 / 9449).
