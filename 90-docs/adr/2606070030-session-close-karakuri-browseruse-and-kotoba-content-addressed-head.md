---
id: adr-2606070030-session-close-karakuri-browseruse-and-kotoba-content-addressed-head
title: "ADR-2606070030: session close — karakuri browser-use + kotoba content-addressed feed head (IPNS commit-head)"
status: active
doc_type: adr
topic: session-close-2026-06-06-07
authoritative: false
last_verified: 2026-06-07
priority_note: "Documentation-only closure of the 2026-06-06→07 session. Authoritative designs = ADR-2606039200 (karakuri) + ADR-2606066000 (content-addressed head)."
depends_on:
  - adr-2606039200-karakuri-web-service-to-cli
  - adr-2606066000-kotoba-content-addressed-head-ipns-commit
  - adr-2606065500-kotoba-browser-only-social-feed
  - adr-2606013600-kotoba-persistent-ipns-graph-heads
related:
  - "https://github.com/etzhayyim/kotoba/pull/47"
  - "https://github.com/etzhayyim/kotoba/pull/48"
  - "https://github.com/etzhayyim/kotoba/pull/49"
supersedes: []
superseded_by: []
---

# ADR-2606070030: session close — karakuri browser-use + kotoba content-addressed feed head

**Status**: active (documentation-only closure)
**Date**: 2026-06-07
**Deciders**: Jun Kawasaki

# Context

Two threads landed across the 2026-06-06→07 session. This is a documentation-only
closure recording the PR ledger + outcomes; the authoritative designs live in
ADR-2606039200 (karakuri) and ADR-2606066000 (content-addressed head).

# Decision (what landed)

## Thread A — karakuri 絡繰 browser-use + Google/Facebook (ADR-2606039200)

Answers *「google, facebook の browser 操作を browser-use/langgraph で CLI 化する
kotoba/pywasm/langgraph actor は設計されているか」* — yes (karakuri), and this
session extended it:

- **monorepo #1196** — browser-use named as the **T2 engine**; two-axis service
  stance (`:service/tos-stance` official-API → T1 · `:service/t2-stance`
  browser-automation → T2). **Google + Facebook = `:api-ok` yet browser-prohibited**
  → routed to T1, T2 refused by construction. `methods/t2_browser.py` builds a
  dry-run browser-use action plan where **detection-evasion is unrepresentable**
  (proxy/captcha/stealth verbs absent; `_make_step` raises). All 5 cells coded as
  reference cells + NL planner (`nl_plan.py`, Murakumo G4) + T3 export (G9) +
  live-exec membrane (`adapter_live.py`, refuse-by-default) + kotoba Datom audit
  (`datom.py`, G7; args keys-only). adapter_invoke wires the planner + browser-use
  builder. methods 87 / cells 31 tests green. **R0; no live execution.**

## Thread B — content-addressed feed head (ADR-2606066000)

Resolved the head-primitive OPEN question of ADR-2606065500: the authoritative
head is the **kotoba IPNS commit-head** — a member-signed `IpnsRecord` whose
`value` is a content-addressed `DistributedDatomCommit` CID — reusing the canonical
engine (ADR-2606013600), NOT a Durable Object and NOT a trusted KV value.

- **monorepo #1203** — ADR-2606066000 (the decision) + registry.
- **kotoba #47** — wasm-safe `kotoba-ipns-record` crate (`IpnsRecord` + Ed25519
  sign/verify factored out of `kotoba-ipfs`, re-exported unchanged) + `kotoba-wasm`
  **`commitHeadSigned`** producer binding. record 5/5 · ipfs 12/12.
- **kotoba #48** — `kotoba-store` made native-only in `kotoba-datomic` so
  `kotoba-wasm` LINKS for `wasm32` (was blocked by a `reqwest→tokio/net→mio` leak;
  `distributed` mod already `cfg(not(wasm32))`). First clean wasm32 link.
- **kotoba #49** — **`verifyIpnsRecord`** reader binding + a JSON round-trip
  interop test (TS↔Rust vector: a Rust-signed record verifies after JSON transport).
  record 6/6.
- **monorepo #1205** — apex `block.put` accepts + stores the signed `IpnsRecord`
  in the head manifest (only when `value == root` ∧ `controller_did == did`);
  `GET root` serves it; apex stays a NON-authoritative relay (still gates on the
  root-sig verify). 8/8 integration tests + lexicon docs. Submodule bump → f0bc3da0.
- **monorepo #1208** — submodule bump → `9157ea3e` (the verify binding).

## Housekeeping

- **monorepo #1191 CLOSED not-merged** — re-introduced the `KotobaRoot` Durable
  Object that #1192 removed on substrate-boundary grounds (ADR-2605262130 /
  2605312345 / 2605231525) + was conflicting. Its charter-clean, DO-independent
  parts (publish-API lexicons corrected to the KV-CAS reality + crypto regression
  tests) were salvaged in **#1198** and merged.

# Consequences

- The full chain **DID → member-signed `IpnsRecord` (content-addressed commit DAG)
  → apex relay → reader-verify** exists in code; the browser node compiles to
  `wasm32` with both bindings. No invariant amendments anywhere (strengthens
  no-server-key + kotoba-canonical-state).
- karakuri's browser-use answer is charter-clean by construction (own-account-only,
  official-API-first, ToS-honest, detection-evasion unrepresentable).

# Remaining (operator-coordinated, browser-E2E + deploy)

Per ADR-2606066000 § Implementation status: (1) rebuild the 3 checked-in
`kotoba_wasm` bundle copies (`build-kotoba-wasm.sh`); (2) route the yoro write path
(`block-publish.ts`, currently pure-TS) through `commitHeadSigned` + gate reads on
`verifyIpnsRecord`; (3) flip `block.put` CAS from `prevRoot` to the record
`sequence`, then browser E2E + `wrangler deploy`. karakuri live adapter execution
stays Council Lv6+ + operator gated.

# References

- ADR-2606039200 (karakuri web-service-to-CLI — authoritative)
- ADR-2606066000 (content-addressed feed head — authoritative)
- ADR-2606065500 (browser-only kotoba social feed; the OPEN question closed)
- ADR-2606013600 (kotoba persistent IPNS graph heads — the reused mechanism)
- kotoba PRs #47 / #48 / #49; monorepo PRs #1196 / #1198 / #1203 / #1205 / #1208
