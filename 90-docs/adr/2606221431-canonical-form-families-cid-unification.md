---
id: adr-2606221431-canonical-form-families-cid-unification
title: "ADR-2606221431: kotoba commit-DAG canonical-form families — CID unification decision"
status: proposed
doc_type: adr
topic: canonical-form-families-cid-unification
authoritative: true
last_verified: 2026-06-22
priority: 6.0
axis: architecture
weight: 0.55
priority_note: "Resolves the cross-actor content-addressing split that blocks the kanjo/kabuto/watatsuna test suites; CID-breaking, so Council-gated."
authoritative_for:
  - kotoba-commit-dag-canonical-form
depends_on:
  - adr-2605312345-kotoba-datom-first-class-canonical-state
  - adr-2606152000-session-close-food-logistics-clj-coverage-supervised-wave
related:
  - adr-2606131300-determinism-golden-file
  - adr-2606022000-kabuto-public-company-supply-chain
supersedes: []
superseded_by: []
---

# ADR-2606221431: kotoba commit-DAG canonical-form families — CID unification decision

**Status**: proposed (decision-framing; requires Council Lv6+ ratification — CID-breaking)
**Date**: 2026-06-22
**Deciders**: Jun Kawasaki (founder) + Bootstrap Council

# Context

The kotoba commit-DAG emitters content-address each transaction by hashing a canonical
serialization of `{datoms, prev-cid}` (ADR-2605312345). A cross-actor invariant test discovered
during the determinism sweep — `70-tools/scripts/clj-test-sweep/canonical_form_invariant.clj` —
documents that the emitters do **not** share one canonicalization. They fall into **two
content-addressing families**:

| Family | Canonical form | empty-tx CID | Actors |
|---|---|---|---|
| **A** | Clojure `{:datoms <pr-str> :prev <pr-str>}` | `b752d9f3…` | **kabuto · watatsuna · watari · kanjo** |
| **B** | JSON `{"datoms":[…],"prev":…}` (mirrors Python `json.dumps`) | `b2fc787b…` | **kakaku · meyasu · uchiwake** |

Within a family every emitter hashes byte-identically; **across families a transaction hashes to a
different CID**. The split is pre-existing heterogeneity in the Python reference corpus: the
food/logistics clj-coverage wave (ADR-2606152000) ported each actor's methods to `.clj`
**byte-identical to that actor's `python3` reference** (the determinism oracle, ADR-2606131300),
faithfully preserving whichever serialization each Python actor already used. The sweep test pins
the topology so that an accidental per-actor drift, a migration to the wrong family, or a silent
unification is caught structurally — and explicitly defers the unification itself to "a separate,
CID-breaking change for a future ADR." **This is that ADR.**

## Why it surfaces now: the blocked test suites

Four Family-A actors (kanjo, kabuto, watatsuna; watari is green) sit in the test-health AUDIT
register as un-runnable / red. Each ships BOTH a `.clj` kotoba (Family A — the Python-faithful
form babashka actually loads, since bb prefers `.clj` over `.cljc`) AND a later `.cljc` kotoba
(Family B — JSON). The actors are **paused partway through a `.clj`(A) → `.cljc`(B) migration**:
the `.cljc` modules + several tests were rewritten toward the JSON form and string-keyed datoms,
but the `.clj` originals (and the broken `bb test:<actor>` shim) were left in place, so the suite
neither runs cleanly on A nor on B. The test-health "deeper / divergent-design" sub-class
(README, PR #2049/#2054/#2101) is, at root, **this paused family migration**.

## Technical validation (a green Family-B path exists)

To verify the migration is *mechanically* achievable (not to enact it), a full reconciliation of
**kabuto** onto Family B was carried out and reverted (2026-06-22, PR #2101 records the finding):
removing the stale `.clj` shadows, completing `ingest.cljc` (string-key datoms, re-exposed
`gated-source?` / `merge-bridged`), hoisting `canonical-order` into `kotoba.cljc`, aligning
`run-autonomous` arity + `verify-chain`/run string-key accessors, and **re-pinning the test CIDs
to the canonical JSON form** produced a **fully green 59-test / 273-assertion suite**. The attempt
also confirmed the cost: it flips kabuto's empty-tx CID `b752d9f3…`(A) → `b2fc787b…`(B), which the
sweep test correctly rejects. So the engineering is straightforward; the obstruction is purely the
governance question of *whether* and *onto which family* to unify.

## Cost is low **now** (pre-anchoring window)

Every affected emitter writes only to its **LOCAL** append-only kotoba log; live-node push and
on-chain/IPFS anchoring are G7/G11-gated and have **not** occurred for these actors. There are
therefore **no published or anchored CIDs to invalidate** — a canonical-form change today rewrites
only local, regenerable logs. This window closes the moment any of these actors anchors a head
CID; unifying before then is materially cheaper.

# Decision

**No enactment in this ADR.** This ADR *frames* the decision and records the validated path; the
choice is **CID-breaking and reserved for Council Lv6+ ratification**. The recommended resolution,
for Council deliberation:

1. **Unify on Family B (JSON `json.dumps` form).** Rationale: (a) it is the form ADR-2605312345's
   canonical-state lineage and the kotoba substrate already describe as "byte-mirroring Python
   `json.dumps`"; (b) it is language-neutral (a JSON canonical form is reproducible from any
   runtime — Python, Clojure, JS/wasm — whereas Clojure `pr-str` is Clojure-specific and an
   obstacle to the browser-wasm read path, ADR-2606013600); (c) the larger validated tooling
   (shionome's all-clj loop, the `.cljc` ports) already targets it.
2. **Execute in the pre-anchoring window**, before any Family-A actor anchors a head CID, so only
   local regenerable logs are rewritten.
3. **Per-actor, suite-gated**: complete each Family-A actor's `.cljc` (string-key datoms + JSON
   canonical), delete the `.clj` shadows, repoint the `bb test:<actor>` shim to auto-discovery,
   re-pin the test CIDs, and **move the actor from `family-a` to `family-b` in
   `canonical_form_invariant.clj` in the same commit** (the sweep test stays the guard — it must be
   updated deliberately, never bypassed). kabuto's reconciliation is the worked reference.
4. If Council instead prefers **Family A** or **status quo**, the sweep test already encodes that;
   the broken suites then need the inverse reconciliation (revert each `.cljc` toward the `.clj`
   pr-str form) or remain shimmed-off with an explicit AUDIT annotation.

# Consequences

- **Positive**: unblocks the kanjo/kabuto/watatsuna suites on a principled basis; collapses the
  test-health "divergent-design" debt class to a single tracked migration; one cross-runtime
  canonical form simplifies the browser-wasm read path and any future cross-language verifier.
- **Negative / risk**: CID-breaking — every Family-A actor's local commit-DAG re-hashes from a new
  genesis. Acceptable ONLY in the pre-anchoring window; after anchoring it would fork history.
  Mitigated by suite-gating + updating the sweep test in lockstep.
- **Invariants untouched**: append-only `:db/add`-only (非終末論), verify-chain tamper-evidence,
  no-server-key, and the Datom-log-as-canonical-state boundary (ADR-2605312345) all hold under
  either family — only the *byte serialization* feeding sha256 changes.
- **Until ratified**: the four Family-A actors stay in the AUDIT register as ADR-gated (not
  "owner-must-choose-a-design" but "blocked on this ADR"); no autonomous suite-greening is
  attempted, since a green suite necessarily picks a family.

# Alternatives Considered

- **Unify on Family A (Clojure pr-str).** Rejected as the *recommended* default because pr-str is
  Clojure-specific (harder for the wasm/JS read path and any non-Clojure verifier) and contradicts
  the substrate's stated `json.dumps` mirroring — but left open for Council, as it is the form the
  Python-faithful `.clj` ports currently use, so it minimizes churn for the four A actors.
- **Keep the split permanently.** Tenable (the sweep test already makes it a *documented* invariant
  rather than an accident), but it leaves the broken suites permanently shimmed-off and forces
  every cross-actor CID consumer to be family-aware. Not recommended.
- **Autonomous greening without an ADR.** Explicitly rejected: validated as mechanically possible
  (kabuto, 59 tests green) but it silently migrates a family and is correctly blocked by the sweep
  test. CID topology is a cross-actor architectural property, not a per-actor implementation detail.

# References

- `70-tools/scripts/clj-test-sweep/canonical_form_invariant.clj` — the invariant test that pins the two families
- `70-tools/scripts/test-health/README.md` — the test-debt sub-class taxonomy (this is its root cause)
- ADR-2605312345 — kotoba Datom log = first-class canonical state
- ADR-2606152000 — food/logistics clj-coverage wave (the `.clj` ports byte-identical to Python)
- ADR-2606131300 — determinism + golden-file verification policy
- PR #2101 — the kabuto reconciliation attempt + revert that surfaced this decision
