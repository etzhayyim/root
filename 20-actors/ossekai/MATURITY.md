# ossekai 御節介 — Maturity

**Stage: R2** — ADR-2605264000. Information-arbitrage + Wellbecoming-nudge substrate over AT
Proto; the charter-clean inverse of an engagement/growth-hacking system. Passive observation,
aggregate-first publication, consent + mute/block honored, no re-engagement after opt-out.

| Dimension | State |
|---|---|
| Lexicons | ✅ 9 under `com.etzhayyim.ossekai.*` (arbitrageGapReport / wellbecomingAdvisory / feedPostAttestation / externalMentionConsent / mentionDispatchAttestation / memberDigest{Record,Subscription} / unsubscribeRecord / silenOssekaiReview) — rich const ledger |
| Manifest | ✅ `manifest.jsonld` — `constitutionalGates` (G1–G15) machine-readable |
| Tests | 🟡 **charter-gate suite green; agent suite has 7 pre-existing failures** — see below |
| Methods | 🟡 agent (`py/`) + cells present |

## Tests

- ✅ `methods/test_charter_gates.cljc` — **8 tests, green** (added 2026-06-16). Pins the
  anti-manipulation const ledger:
  - **no re-engagement after opt-out** (`silenOssekaiReview.reEngagementAfterOptOutCount` const 0)
    + **no commercial CRM/intel software** (`commercialIntelCrmSoftwarePenetrationPct` const 0).
  - **opt-out immediate** (`unsubscribeRecord.effectiveImmediatelyAttested` const true).
  - **G15 every post** passes mute/block check + framing audit + signed AS ossekai
    (`feedPostAttestation` const `muteBlockCheckPass`/`framingAuditPass`/`senderDidConst`).
  - **passive-only** observation (`arbitrageGapReport.passiveOnlyAttested` const true).
  - **G13 non-member mention** consented + Council-gated + rate-limited.
  - **advisory boundary routing** (`wellbecomingAdvisory` requires `crossActorDid` + `boundaryKind`).
  - **member digest** opt-in + encrypted.
- ⚠️ `py/test_agent.py` — **34 passed / 7 FAILED** (pre-existing, NOT introduced 2026-06-16;
  `py/` is git-clean). Run via `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest`.

### ⚠️ Pre-existing agent-test failures — FOLLOW-UP NEEDED

7 agent tests fail (dispatcher / publisher / member-digest / emergency). The most
charter-relevant: `test_member_digest_encrypts_no_plaintext_g8` expects
`digest.state == "draft"` (operator-gated, no auto-send) but the agent returns `"sent"`.
**Investigated 2026-06-16** (tick 17): all 7 failures share ONE root cause — `agent.py`
hardcodes `state = "posted"/"sent"` + `broadcast = True` (`# R2 Autonomous: operator gate
removed`), while the tests + `agent.py`'s own docstring (line 266) + no-server-key (G7)
require operator/member-gated drafts. CLAUDE.md documents this as an intentional "R2
Autonomous … without manual operator gating" upgrade — which conflicts with G7 unless posts
are member-signed-capability-backed (ibuki/mimamori CACAO precedent, ADR-2606111400), which
`agent.py` does NOT implement.

→ **Full analysis + 3 resolution options: [`FINDING-G7-autonomy-conflict.md`](FINDING-G7-autonomy-conflict.md)**.
NOT auto-resolved: editing the code would revert a documented R2 upgrade; editing the tests
would ratify a possible G7 weakening (forbidden by the loop mandate). Needs Council/ADR.

## R0/R2 → R3 gate

Resolve the 7 agent-test failures + Council review; the charter-gate suite is the
schema-level floor (must stay green).

> **2026-06-17 substrate-native migration (ADR-2606160842):** the charter-gate test above was ported Python→Clojure (`methods/test_charter_gates.py` → `methods/test_charter_gates.cljc`, ns `ossekai.methods.test-charter-gates`, reads the lexicons via cheshire/edn) and the Python was pruned. Run via `./run_tests.sh` (now `exec bb`) or `bb run test:charter` (all 34 charter suites; 244 tests / 924 assertions green). Assertions unchanged (1:1 port).
