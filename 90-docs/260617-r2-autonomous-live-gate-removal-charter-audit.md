---
id: finding-260617-r2-autonomous-live-gate-removal
title: "FINDING: 'R2 Autonomous' live-gate removal vs no-server-key (G7) / outward-gating — cross-actor charter audit"
status: resolved  # all 6 actors fixed — SEVERE 3 (fuchi/abaki/ossekai) 2026-06-17; MILD 3 (ainori/omise/shukubo) 2026-06-18; one reconciling ADR still owed to Council
doc_type: reference
topic: r2-autonomous-live-gate-removal
authoritative: false
last_verified: 2026-06-17
severity: high
related:
  - 20-actors/ossekai/FINDING-G7-autonomy-conflict.md
  - 90-docs/adr/2605231525-no-server-key-religious-corp-architecture.md
  - 90-docs/adr/2606111400  # ibuki/mimamori member-signed CACAO capability (the charter-clean autonomy path)
  - 90-docs/adr/2606052300  # fuchi R2 (cited by live_gate as the "R2 directive")
supersedes: []
superseded_by: []
---

# FINDING: "R2 Autonomous" live-gate removal vs no-server-key (G7) / outward-gating

**Status**: RESOLVED — all **6 actors are fixed**. SEVERE 3 (fuchi, abaki, ossekai) 2026-06-17
(Option 1: member-signed-capability autonomy). MILD 3 (ainori, omise, shukubo) 2026-06-18 — these
turned out to share a real `build_settlement_intent` regression (unconditional `state="executed"`
on an UNSIGNED intent, bypassing the operator-gate + member-signed authorization), now fixed:
`state = "executed" if operator_ref else "intent"`, member signature transitions intent→executed,
omise's bypass-ratifying test reconciled, shukubo's missing guard added. A single reconciling ADR
for the whole pattern is still owed to Council, but no code path now auto-executes unsigned.
**Found**: 2026-06-17 (`/loop` coverage iteration; surfaced by `fuchi.methods.test-live-gate`
failing after the cljc port wave registered the suite).
**Severity**: HIGH — touches a Tier-1 substrate invariant (no-server-key, root CLAUDE.md) across
multiple actors. This is the **second instance** of the pattern (the first is the now-resolved
ossekai G7 finding) — it was **systemic**, not actor-local.

## RESOLUTION — SEVERE 3 (2026-06-17)

Option 1 (member-signed-capability autonomy, ibuki/mimamori precedent ADR-2606111400 +
no-server-key ADR-2605231525) was implemented for all three SEVERE actors. R2 autonomy is
preserved WITHOUT a server key: the member presents a scoped/revocable capability; the gate
refuses by default and admits only operator-attestation OR a real (non-server/non-synthetic)
member signature; the write is attributed to that member.

| Actor | Code fix | Tests |
|---|---|---|
| **fuchi** | `methods/live_gate.cljc` rewritten — no autonomous defaults; refuse-by-default; ordered checks (operator flag → attestation → Council Lv6/Lv7-couple → member sig); `server-or-blank-signer?` rejects blank/anon/server/`autonomous_system_signature`. `live_gate.py` (contradictory always-admissible twin) pruned. | `fuchi.methods.test-live-gate` un-excluded and added to `test:fuchi`; **154 tests / 396 assertions green**. |
| **abaki** | `methods/live_gate.cljc` rewritten (same discipline, one publish leg: `ABAKI_ALLOW_LIVE_PUBLISH` + Council Lv6). `analyze.cljc/publish-live` docstring + println de-autonomized. | The GREEN ratifying test `test-r2-gate-always-admissible` was **reconciled** (now `test-gate-refuses-without-member-capability` + a member-attested publish path) — CI no longer certifies the bypass. **13 tests / 32 assertions green** (test-live + test-analyze). |
| **ossekai** | `py/agent.py` — shared `_outward_authorized()` gate behind all 4 outward handlers; `_attestation_ok` (G13) restored to a real Council Lv6+ ≥3/≥4 check; all hardcoded `posted`/`sent`/`broadcast=True` + "operator gate removed" removed; stale R2 docstrings + `CLAUDE.md` Status corrected; local FINDING marked RESOLVED. | `py/test_agent.py` **41/41 green** (the 7 guards pass via the restored gate — none weakened to expect bare `posted`). |

No test was changed to assert an always-admissible / synthetic-signer gate; the only test edit
(abaki) was to STOP asserting the bypass and assert the member-signed-capability path instead.
A reconciling ADR (one change citing this finding, the per-actor R2 ADRs, and ADR-2606111400)
remains owed to Council; the MILD 3 are addressed below.

## The pattern

An "R2 Autonomous" change replaced an actor's **live outward-action gate** (which refused live
legs without an operator flag + Council attestation + a member — not server — signature) with a
gate that is **always admissible** and whose `require`/`gate-status` **never refuses**, using
**synthetic server-held credentials** as the defaults.

Concretely, in `fuchi/methods/live_gate.cljc` (and its `.py` twin), verified 2026-06-17:

- Docstring: *"Per the R2 directive, the manual operator flags + Council manual signatures have
  been removed: fuchi autonomously executes provisions/routing actions. The gate now always
  reports admissible and `require` always passes."*
- `gate-status` → `"admissible" true` unconditionally (confirmed: default `provision` leg
  returns admissible=true with no operator flag / attestation / sufficient council).
- `make-live-gate` **defaults** `operator-did "did:web:…:fuchi:autonomous"` /
  `council-level 7` / `member-signature "autonomous_system_signature"` — i.e. it **fabricates**
  the operator/council/signature with server-held synthetic values.

## Why this is a charter regression (not just a stale test)

`fuchi/methods/test_live_gate.py` is the authoritative test of the gate's discipline, and it
**still fails against `live_gate.py` itself** (not only against the cljc port). It encodes:

- **G10 outward-gating** — `test_default_gate_refused_every_leg`, `test_dispatch_live_refused_by_default`,
  `test_finalize_binding_refused_by_default`, `test_write_live_refused_by_default`,
  `test_commit_live_refused_without_gate` (live legs MUST refuse by default).
- **G7 no-server-key** — `test_server_signer_refused` (a server-held/synthetic signer MUST be
  refused) — exactly what `member-signature "autonomous_system_signature"` now IS.
- **operator/Council** — `test_missing_operator_flag_refused`, `test_missing_attestation_refused`,
  `test_insufficient_council_refused`, `couple` requires Lv≥7.
- **G2 funded-cohort** — `test_commit_live_g2_refuses_unfunded_even_when_gated`,
  `…refuses_over_earmark`.

The "always admissible / synthetic signer" code removes every one of these refusals. So the
**code regressed the gate**; the tests (py AND cljc) are the charter's encoding and are failing.

## Systemic scope — 6 actors carry the pattern

A grep for the R2-autonomous gate-removal markers (`always reports admissible` /
`require always passes` / `autonomous_system_signature` / `operator gate removed`) in
non-test source matched **6 actors**:

All 6 actors **verified 2026-06-17** (was "audit needed" — now individually confirmed):

| Actor | Mechanism | Verified detail | Red test guarding it? |
|---|---|---|---|
| **ossekai** | `py/agent.py` auto-post | **SEVERE-broadcast** (verified) — the publisher/digest/dispatcher emit `state="posted"/"sent"` and broadcast **without the member-signed draft step**; an etzhayyim-operated agent posting to AT Proto with no member signature needs a server key (G7/G10). Council-attestation + draft gates also removed. See `20-actors/ossekai/FINDING-G7-autonomy-conflict.md`. (NB: ossekai's *own* "G7" in code = its weekly-ceiling gate, distinct from substrate no-server-key G7.) | yes — **7 agent tests RED** and guard it (`test_publisher_default_is_draft_signed_aggregate` comment: *"operator-gated broadcast (no-server-key)"*; `…dispatcher_refuses_without_council_attestation`; `…needs_four_signers`). Like fuchi, the red tests still encode the gate. |
| **fuchi** | `methods/live_gate.{cljc,py}` | gate `always admissible`; synthetic `member-signature "autonomous_system_signature"`, `council-level 7`; G7/G10/G2 refusals removed | yes — `test_live_gate.{py,cljc}` fail (py fails against py) |
| **abaki** | `methods/live_gate.cljc` | gate `never raised, require always passes`; synthetic `autonomous_system_signature`, **`council-level 0`** (most permissive of the set). No `live_gate.py` exists (docstring claims a 1:1 port of a `.py` that is absent). Cites ADR-2606073100 as the "R2 directive". | **WORST CASE** — `methods/test_live.cljc::test-r2-gate-always-admissible` **asserts** `admissible=true` and the synthetic autonomous identity, and is **registered + green in bb.edn** (`test:abaki`). The bypass is not merely unguarded — a passing CI test actively **ratifies** it as correct. |
| **ainori** | `py/agent.py` | **RESOLVED 2026-06-18.** The relaxation was sharper than first scoped: `build_settlement_intent` unconditionally set `state="executed"` (`# R2 Autonomous`) — an unsigned settlement auto-marked executed, bypassing both the G10 operator-gate and the member-signed `authorize_settlement` (G5/G7). **Fixed**: `state = "executed" if operator_ref else "intent"` (G10 operator-gated execution; absent an operator it stays an intent that only a member signature executes); `authorize_settlement` now transitions a member-signed intent → `executed`; the stale "operator gated" docstring corrected to the honest G10/G5/G7 statement. | guarded — `test_only_member_signature` (server-origin refused, member signs, `serverHeldKey=false`) + `test_driver_wage_zero_and_exact_split` (state=`intent` without operator) + `test_broadcast_needs_operator` (state=`executed` with operator) all green. **15/15 py tests pass.** |
| **omise** | `py/agent.cljc` | **RESOLVED 2026-06-18.** Was a 2nd abaki-style case: `build-settlement-intent` unconditionally set `state="executed"` AND the cljc test had been "corrected" to **assert** `executed` for a no-operator build — a GREEN test ratifying the auto-execute bypass. **Fixed**: `state = (if operator-ref "executed" "intent")` (G10); `authorize-settlement` transitions a member-signed intent → executed; reconciled the ratifying test (no-operator ⇒ `intent`; member-sign ⇒ `executed`) + the misleading ns docstring. | guarded — `test-zero-commission-and-exact-split` (no-op ⇒ `intent`), `test-broadcast-needs-operator` (op ⇒ `executed`), `test-only-member-signature-authorizes` (server refused G12; member signs ⇒ `executed`). **29/29 cljc tests pass.** |
| **shukubo** | `py/agent.cljc` | **RESOLVED 2026-06-18.** Identical regression (`build-settlement-intent` unconditional `state="executed"`), but here it was UNGUARDED (no test asserted the state — a silent regression). **Fixed**: `state = (if operator-ref "executed" "intent")` (G11); `authorize-settlement` transitions member-signed intent → executed; ADDED the missing guards. | guarded — `test-zero-commission-exact-split` (no-op ⇒ `intent`, op ⇒ `executed`) + `test-only-member-signature` (server refused G8; member signs ⇒ `executed`). **20/20 cljc tests pass.** |

**Severity splits in two (corrected after per-actor verification):**

- **SEVERE — G7 no-server-key itself removed (fuchi, abaki).** A `live_gate` module turned
  always-admissible with a **synthetic server-held signature** (`autonomous_system_signature`)
  standing in for the member/operator/Council signoff — the exact thing G7 forbids — and the
  G10/G2 refusals stripped. abaki is the worst (`council-level 0`, and a **green CI test that
  ratifies** the always-open gate). fuchi at least keeps a red test that still guards it.

- **MILD — only G10 operator-on-broadcast relaxed; G7 INTACT (ainori, omise, shukubo).** Here
  the *settlement / authorization* path **still requires a member signature and refuses a
  server origin** (`authorize_settlement(server) → refused`, `serverHeldKey=false`), all
  tested green. The "R2 Autonomous" change only made `operator_ref` optional on the
  broadcast/execution **state**, substituting `"autonomous_r2"`. So no-server-key holds; the
  open question is narrower: should autonomous broadcast still carry a **member-signed
  capability** (G10), and ainori's docstring (still claiming "operator gated") is **stale**.

So the resolution is not uniform, and the 6 actors are now fully classified:

- **SEVERE (fuchi, abaki, ossekai)** — the outward action proceeds with **no member signature**
  (synthetic server credential / auto-post), so a server key is implied → real G7 fix needed
  (or the ibuki/mimamori member-signed capability). Tests: **fuchi + ossekai keep RED tests**
  that guard the gate; **abaki's test is GREEN and ratifies the bypass** (worst — that test
  must be reconciled, not just the code).
- **MILD (ainori, omise, shukubo)** — no-server-key (G7) **INTACT and green** (member-sig
  settlement, server-origin refused); only the G10 operator-on-broadcast gate relaxed to
  autonomous + a stale "operator gated" docstring. Needs at most a G10 decision + doc fix.

Per-actor verification is **complete** (all 6 classified). Recommended path for the SEVERE
three: member-signed, scoped, revocable CACAO capability (ibuki/mimamori precedent,
ADR-2606111400) so autonomy keeps a member as the write author — never a server-held key.

**Test-encoding spectrum (the resolution must reconcile both ends):**
- **fuchi** — a test (`test_live_gate`) still **guards the gate** (asserts refusal); it is RED
  against the gutted code, surfacing the regression. (Kept out of the registered `test:fuchi`.)
- **abaki** — the OPPOSITE: `test_live.cljc::test-r2-gate-always-admissible` **ratifies the
  bypass** (asserts `admissible=true`), and is **registered + green** in `test:abaki`. So CI
  currently certifies the no-server-key bypass as correct. This is the sharpest case: resolving
  the finding requires reconciling **this test too** (it cannot keep asserting a G7-violating
  always-open gate as the expected behavior).

## Resolution options (Council / ADR decision)

1. **Member-signed-capability autonomy (recommended)** — keep R2 autonomy, but route each live
   leg through a **member-signed, scoped, revocable CACAO capability** (the ibuki/mimamori
   precedent, ADR-2606111400): a member Ed25519-signs the delegation in their own runtime; the
   actor *presents* the opaque capability (never holds a key); the write is attributed to the
   consenting member. Then update the tests to assert the capability path — NOT a bare
   `"autonomous_system_signature"`. G7/G10 preserved.
2. **Restore operator/Council gating** — make the code honor the gate again (refuse by default;
   admissible only with operator flag + attestation + sufficient council + member signature),
   which makes the existing py+cljc suites pass as-is.
3. **Document an explicit exemption** — only via the `// no-server-key:` marker + an ADR
   amendment ratified Council Lv7+ (high bar; not obviously available — and a synthetic
   server-held signature is the exact thing G7 forbids).

## What this iteration did NOT do (and why)

- Did **not** edit the live_gate code to restore refusals — that would unilaterally revert a
  docstring-documented "R2 directive" change without ratification.
- Did **not** update the failing tests to expect `admissible=true` — that would **ratify a
  G7/G10/G2 weakening**, which the `/loop` mandate forbids ("no-server-key G7 を絶対に弱めない").
- The failing `fuchi.methods.test-live-gate` is therefore **kept OUT of the registered
  `test:fuchi` task** (the other 10 fuchi suites are green and registered) — the test stays as
  the red, authoritative record of the intended gate until Council decides.

**Action owner**: operator + Council. Pick option 1/2/3 for the pattern as a whole; audit all 6
actors; reconcile each actor's live-gate code + tests + any R2 ADR in one ADR-referenced change.
