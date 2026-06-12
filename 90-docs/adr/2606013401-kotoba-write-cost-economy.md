---
id: adr-2606013401-kotoba-write-cost-economy
renumbered_from: "2606013400"
title: "ADR-2606013401: kotoba write-cost economy — datomic writes cost mKOTO"
status: active
doc_type: adr
topic: kotoba-write-cost-economy
authoritative: true
last_verified: 2026-06-01
priority: 4.0
axis: architecture
weight: 0.40
priority_note: "Makes datomic.transact writes cost mKOTO so the soft-auth write surface is economically gated (spam-resistant); enables eventual safe public writes."
authoritative_for:
  - kotoba-datomic-write-cost
depends_on:
  - adr-2606013200-yoro-kotoba-feed-readpath-migration
  - adr-2605231525-kotoba-no-server-key
related:
  - "40-engine/kotoba/crates/kotoba-server/src/econ.rs"
supersedes: []
superseded_by: []
---

# ADR-2606013401: kotoba write-cost economy — datomic writes cost mKOTO

**Status**: active
**Date**: 2026-06-01
**Deciders**: Jun Kawasaki

# Context

`datomic.transact` (the kotoba write path) is gated only by **soft auth**:
`graph_auth::require_operator_auth` checks the bearer JWT's `sub == operator_did`
and `exp` — **not the signature** — and a CACAO write checks capability/scope.
No write charges anything: the economy primitives that exist
(`attestation.rs` `stake_mkoto` thresholds, WASM/Datalog gas counters,
mKOTO/CitationLedger) are tracked but **not enforced on `datomic.transact`**, and
there is no per-DID balance ledger that is debited.

When the yoro feed exposed kotoba publicly (ADR-2606013200), the soft-auth write
surface became a concern: anyone deriving the operator DID could write. That was
mitigated by exposing kotoba **read-only** at the edge. To make writes safe to
accept (now or later), they should **cost token** — an economic barrier so spam
is expensive — which is the operator's directive here.

# Decision

**Charge mKOTO per datomic write, debited from the writer's balance.**

- **Ledger** (`crates/kotoba-server/src/econ.rs`, `Econ`): a per-DID
  `HashMap<did, i64 mKOTO>` (in-memory + JSON persistence at
  `${KOTOBA_STORE_PATH}/econ-balances.json`, reloaded at boot). 1 KOTO =
  1e9 mKOTO (matches `attestation.rs`).
- **Charge** (`datomic_transact`): `cost = cost_per_datom × tx_preview.tx_data.len()`,
  charged to `write_author` (operator bearer → operator DID; CACAO → `cacao.iss`)
  **before commit**. Insufficient balance → **HTTP 402** (`PAYMENT_REQUIRED`).
  A commit failure after the charge refunds best-effort.
- **Operator exempt / mint**: the node-owner DID is unlimited (never debited) —
  the node's own substrate writes and the operator-run ingest never block. The
  operator funds external writers via `econ.credit`.
- **XRPC**: `com.etzhayyim.apps.kotoba.econ.balance` (read a DID's balance + cost +
  enabled flag) and `com.etzhayyim.apps.kotoba.econ.credit` (operator-only mint:
  credit/debit a DID).
- **Opt-in**: cost is `KOTOBA_WRITE_COST_MKOTO_PER_DATOM` (default **0 =
  disabled**, so unit/e2e tests and existing CACAO writers are unaffected until
  the operator turns it on). Recommended production value: **10 mKOTO/datom**
  (matches the `assert = 10` gas unit). The etzhayyim kotoba node sets this in
  its launchd plist.

# Consequences

- With cost enabled, an **external (non-operator) writer must hold mKOTO** to
  write — a real spam barrier. Combined with the read-only edge filter
  (ADR-2606013200) this is defense-in-depth; it is the prerequisite for safely
  re-opening public writes later.
- The operator (node owner) writes free (exempt) — the yoro ingest and other
  operator-run writes are unaffected.
- Internal direct-`QuadStore` commits (cc / kg ingest) bypass the HTTP
  `datomic.transact` handler, so they are not charged; only HTTP `datomic.transact`
  callers are metered.
- **Not yet on-chain**: balances are node-local (JSON + in-memory). On-chain
  mKOTO settlement / funding bridges (ERC-4337 / Base L2) remain
  etzhayyim-exclusive (operating-entity boundary) and out of scope here.
- The pre-commit charge can over-charge on the rare commit-after-charge failure;
  refunded best-effort. Signature verification of the operator bearer is still
  not performed (separate concern, ADR-2605231525) — the economy gates cost, not
  identity; combine with CACAO (real Ed25519) for authenticated external writes.

# Alternatives Considered

- **Block public writes only at the edge (no economy).** Done as the immediate
  mitigation (ADR-2606013200 read-only filter), but it cannot *enable* public
  writes; the economy is what makes paid public writes possible.
- **Charge everyone including the operator.** Rejected: the operator funds the
  system; charging the node owner against a finite balance would self-block the
  node's own writes with no benefit. Operator-exempt + mint is the funding model.
- **Enforce via the existing attestation stake.** Rejected: `stake_mkoto` is a
  self-reported threshold with no debited balance; it is not a spend.
- **Full on-chain settlement now.** Deferred: etzhayyim-exclusive; node-local
  ledger is the substrate-side primitive this ADR provides.

# References

- ADR-2606013200 (yoro feed kotoba read-path; read-only edge exposure)
- ADR-2605231525 (kotoba no-server-key — soft-auth identity boundary)
- `40-engine/kotoba/crates/kotoba-server/src/econ.rs` (ledger + cost + mint)
- `40-engine/kotoba/crates/kotoba-server/src/xrpc.rs` (`datomic_transact` charge,
  `econ_balance` / `econ_credit` handlers)
