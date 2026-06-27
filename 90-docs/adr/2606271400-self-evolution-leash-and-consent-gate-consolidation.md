---
id: adr-2606271400-self-evolution-leash-and-consent-gate-consolidation
title: "ADR-2606271400: Agent self-evolution — leash-everywhere + single consent gate at PR-merge"
status: proposed
doc_type: adr
topic: self-evolution-consent-gate
authoritative: true
last_verified: 2026-06-27
priority: 7.0
axis: architecture
weight: 0.50
priority_note: "Tier-1-adjacent: preserves no-server-key (Tier-1) while making autonomy the default; the consent-gate placement is governance (amendable)."
authoritative_for:
  - agent-self-evolution-loop
  - consent-gate-placement
  - leashed-outward-action
depends_on:
  - 2606101200  # ibuki organism autonomy (the leash / CACAO delegation origin)
  - 2606111400  # revocable member-signed CACAO capability (the leash invariant)
  - 2605231525  # no-server-key religious-corp architecture
  - 2606072802  # no-server-key clarification (bars custodial key, NOT automation; read-only exempt)
related:
  - 90-docs/260617-r2-autonomous-live-gate-removal-charter-audit.md  # the reverted anti-pattern
  - 50-infra/etzhayyim-atproto-pds-clj/src/etzhayyim/pds/leash.clj   # the PDS-side leash (already built)
  - 70-tools/src/etzhayyim/fleet_probe.cljc                          # residency probe (the gap evidence)
supersedes: []
superseded_by: []
---

# ADR-2606271400: Agent self-evolution — leash-everywhere + single consent gate at PR-merge

**Status**: proposed
**Date**: 2026-06-27
**Deciders**: Jun Kawasaki (founder, Council Lv7+ 1/1)

# Context

Two operator observations on 2026-06-27 drove this:

1. **etzhayyim.com shows almost no actor social posts.** A `bb fleet:probe`
   (`70-tools/src/etzhayyim/fleet_probe.cljc`, authored this session) measured the live
   fleet: of **24 defined cron/lan-api heartbeats, exactly 1 is actually resident** (Sukashi
   on issachar). The other 23 — incl. ibuki's organism beats, kaname, mimamori, tsubasa —
   are **defined-only-silent**: scheduled in `fleet.edn` / `cell-runner/cells.edn` but no
   launchd/k3s daemon is up. evo-x2 inference is DOWN (Ubuntu re-provision pending). So the
   posts are absent for two compounding reasons: (a) the heartbeats that would generate them
   are not running, and (b) even when they run, every outward post is held `:dry-run` /
   `:prepared` and publishing requires a **per-act member signature**, which the sole member
   has effectively never performed.

2. **The founder's proposal:** "the final member-signed submit should itself be agent
   self-evolution," and "agent self-evolution + deploy should flow through push to the
   etzhayyim GitHub repo."

The constraint that shapes any answer is **no-server-key** (ADR-2605231525, Tier-1). But its
clarification (ADR-2606072802) is decisive: no-server-key bars a **custodial unilateral signing
key** held by the platform — it does **NOT** bar automation, and read-only is exempt. The
**reverted** "R2 Autonomous" change (finding 260617) violated this not by being autonomous but
by **fabricating a synthetic server-held signature** (`autonomous_system_signature`) that
impersonated the member. The recommended resolution of that finding (Option 1) was already the
**member-signed revocable CACAO capability** — the *leash* (ADR-2606111400).

Crucially, the leash is **already real on both sides**:

- **kotoba writes** (internal self-evolution): `ibuki.methods.{delegation,kotoba_bridge}` —
  the member issues a scoped/expiring/revocable CACAO once; the organism *presents* the opaque
  `cacao_b64` each beat (holds no key, never signs); kotoba records `write_author = the issuing
  member`. kaname/kanae/ibuki/tsubasa run this today.
- **AT-Proto posting**: `etzhayyim.pds.leash` (in the etzhayyim-operated PDS) already
  implements `issue-leash` (member runtime) → `verify-leash` (PDS) → `leash-author` (returns
  the consenting member's DID to attribute the record to), with expiry / audience / scope /
  tamper all rejected and garbage-never-throws — **leash_test.clj green**.

So the mechanism to make *every* autonomous outward act member-attributed-without-a-held-key
exists. What is missing is (a) wiring the actor-side posting runtime to present a leash to the
etzhayyim PDS, (b) a deliberate decision on **where the human consent gate sits**, and (c)
actually running the daemons.

# Decision

Adopt a **leash-everywhere, single-consent-gate** self-evolution architecture. autonomy is the
default; the **only** standing human act is **one consent gate at Pull-Request merge** (=
Council attestation = 1 SBT = 1 vote, per the bootstrap premise). no-server-key is **preserved
unamended** — autonomy is bought with member-issued revocable capabilities, never a held key.

```
[AUTONOMOUS]  agent self-evolves ──▶ emits a PR  (KaizenPrAgent pattern, member/operator-leashed gh)
                                          │
[HUMAN — the one gate]  founder review + merge   = Council attestation (1 SBT = 1 vote)
                                          │
[AUTONOMOUS]  merge ─▶ fleet pulls ─▶ cells redeploy        (CD)
[AUTONOMOUS]  kotoba state evolution + social posting        (leash → member-attributed)
```

### D1. The consent gate is consolidated to **PR-merge**, and is the *only* one

Per-beat / per-act human presence is **removed** as a requirement for autonomous operation.
The single, sufficient human consent for a class of autonomous action is:

- **the member issuing a leash** (a scoped, expiring, revocable CACAO) — one signature
  authorizes a *bounded stream* of autonomous writes, each on-record attributed to that member;
  and
- **the founder merging a PR** — one review authorizes a code/config change to run on the fleet.

Both are genuine, revocable, on-the-record human acts. Neither is a held key.

### D2. Leash-everywhere — autonomy WITHOUT a held key (no-server-key preserved)

Every autonomous **outward** write (kotoba transact, PDS record-create, commons offer) MUST be
authorized by a member-issued CACAO leash and attributed to the issuing member. The agent is
the **bearer** that presents opaque bytes; it never holds the signing key and never signs.
Expired / mis-scoped / absent leash → **fail-open** to the local log / operator-bearer
loopback (never a synthetic signature — that is the reverted anti-pattern, forbidden).

### D3. Social posting becomes leashed-autonomous **to the etzhayyim PDS**; external stays per-act

The posting leg splits by **who operates the destination PDS**:

| destination | mechanism | autonomy |
|---|---|---|
| **etzhayyim-operated PDS** (honors `etzhayyim.pds.leash`) | agent presents the member's `cacao_b64`; PDS `verify-leash` → `leash-author` attributes the record to the consenting member; agent holds no credential | **leashed-autonomous** (the new capability) |
| **external PDS** (bsky.social — does not speak CACAO) | member's own `IBUKI_MEMBER_*` session credential, `--yes`, **cron-refused** | **per-act member** (unchanged, honest boundary) |

This is the structural answer to "submit も自己進化": on our own substrate it *is* self-evolution
(leashed); on third-party substrate it cannot be (they cannot honor a member-signed capability),
so it stays an explicit member act.

**Implementation status — VERIFIED 2026-06-27: the leashed-PDS posting path is already
code-complete and green.** It is NOT a new build. The etzhayyim PDS ships it end-to-end:

- `etzhayyim.pds.leash` — `gen-member-key` / `seal-member` / `issue-leash` (member runtime) +
  `verify-leash` / `leash-author` (PDS): a member-signed, scoped, expiring, **revocable** (jti
  revocation set) capability; expiry / audience / scope / tamper rejected; garbage never throws.
- `etzhayyim.pds.drain` — `drain!` / `run-queue!` / `run-file!`: parses an ibuki NDJSON post
  queue and posts each record to the PDS **presenting the leash** (`{:leash …}`); the actor
  holds no key (the PDS signs + attributes to the leashed member); idempotent posted-key cursor.
- bb tasks (all present): `leash-keygen` (member mints a sealed key), `leash-issue` (member
  issues a scoped/expiring leash), `drain` (autonomous, presents the leash), `drain-preview`
  (dry-run). **`bb test` → leash-test + drain-test = 22 tests / 106 assertions, 0 failures.**

So no posting code is owed. The external-PDS path (ibuki `member_submit`, member creds +
`refuse_if_cron`) is unchanged and remains the per-act member act for bsky.social. What remains
for "submit も自己進化" is **operational only** (D5 + the runbook below): run the PDS, have the
member issue ONE leash, and run `bb drain` on a heartbeat — there is nothing left to write.

### D4. Git self-evolution + deploy is one CD loop with the gate at merge

- **Propose (autonomous):** `KaizenObserverCell` → proposal NDJSON → `KaizenPrAgentCell` opens a
  PR. The gh credential is the **operator/member's**, leashed (read-mostly; PR-open is the
  member's delegated capability), never a platform key.
- **Attest (the gate):** founder reviews + merges = Council attestation. Branch-protection makes
  merge the enforced choke point.
- **Deploy (autonomous):** merge to `main` triggers each fleet node to **pull** (the existing
  repo-clone-on-start pattern) and the cell-runner to **reload** changed cells. A `bb
  fleet:deploy` task (clj) renders + installs the per-node launchd/k3s unit from
  `fleet.edn` + `cells.edn` and performs the pull+reload; it shells to `git`/`launchctl`/`ssh`
  (system binaries, allowed) but authors no logic in sh/py.

### D5. Daemons are made actually resident (close the probe gap)

`bb fleet:probe` is the standing residency check. `bb fleet:deploy` (D4) installs the
cell-runner LaunchAgent on each node so the defined heartbeats actually run; `fleet:probe` then
flips them `:defined-only-silent → :alive`. Physical power/hardware availability of a node
remains an operator reality, but installation is no longer a manual per-node chore.

# Operator runbook — closing the loop (the remaining work is operational, not code)

The `bb fleet:probe` baseline (2026-06-27): 1/24 heartbeats resident, PDS-posting path
code-complete but **not running**, no leash issued. To make `etzhayyim.com` actually post,
member-attributed, autonomously:

```bash
# 1. (founder, ONE TIME) mint a member key, sealed under the founder's OWN secret.
LEASH_SEAL_SECRET=… bb leash-keygen   # → {:did did:key:z6Mk… :sealed "…"}   (store the sealed blob)

# 2. (founder, periodically — this is the consent act, revocable by NOT re-running) issue a
#    SHORT, scope-narrowed leash for posting (narrower than a kotoba-write leash, per D-policy).
LEASH_SEAL_SECRET=… LEASH_SEALED='{…}' LEASH_AUD=<pds-did> \
  LEASH_EXP=$(($(date +%s)+86400)) LEASH_SCOPE=post  bb leash-issue   # → compact leash string

# 3. (autonomous, each beat — the resident drain) ibuki autorun keeps the queue fresh; the PDS
#    drain presents the leash and posts, attributing each record to the consenting member.
PDS_DRAIN_BASE=<pds-url> PDS_DRAIN_QUEUE=<ibuki posts queue> \
  PDS_DRAIN_CURSOR=… PDS_DRAIN_RECEIPTS=… PDS_DRAIN_LEASH="<leash from step 2>"  bb drain
```

Residency (D5): install the cell-runner LaunchAgent (`bb fleet:deploy`, to be added) so the
ibuki beat **and** a `PostDrainHeartbeatCell` (wrapping step 3) run each tick; the etzhayyim PDS
itself is deployed from `50-infra/etzhayyim-atproto-pds-clj/` (`bb serve` under launchd). Verify
with `bb fleet:probe` — the drain + PDS should flip to `:alive`. Steps 1–2 hold the founder's
own secret and are never platform-held (no-server-key); step 3 holds no key.

# Consequences

- **Autonomy becomes the default, no-server-key intact.** The org's moving parts self-evolve;
  every autonomous write names a consenting human; no platform key exists.
- **One gate, clearly placed.** A reviewer reasons about *one* control point (PR-merge) plus the
  *scope of each leash*, instead of an ad-hoc mix of per-act prompts.
- **The reverted anti-pattern stays impossible.** There is no code path that fabricates a signer;
  absence of a leash fails open to the operator-bearer/local-log, never to a synthetic identity.
- **Honest external boundary.** Posting to third-party PDSes cannot be leashed and remains an
  explicit member act — this is disclosed, not hidden.
- **New trust surface to bound: leash scope.** A broad/long leash is a broad grant. Mitigation:
  leashes for *public posting* SHOULD be narrower than for kotoba writes — short `exp`,
  content-class-scoped, per-epoch, revocable; revocation = stop re-issuing (the organism
  retires). This is the founder's per-class policy choice, recorded alongside this ADR.
- **CD risk.** Auto-deploy on merge can ship a regression fleet-wide. Mitigation: merge gate +
  `fleet:probe` health post-deploy + per-cell crash-isolation (already in the runner) + the
  existing watchdog.

# Alternatives Considered

1. **Keep per-act member signature for all posting (status quo).** Rejected as the *default*:
   it guarantees near-zero social presence with a single member and conflates "third-party PDS
   can't honor a capability" (a real constraint) with "we choose to require presence" (a policy).
   Retained ONLY for external PDSes, where it is forced.
2. **Full autonomy, no human gate.** Rejected: it requires the platform to hold a key (collides
   with no-server-key Tier-1) and reproduces the 260617 synthetic-signature violation.
3. **Server-held bot key + audit log.** Rejected: the exact custodial-key prohibition; the audit
   log does not restore the missing human principal.
4. **Amend no-server-key.** Unnecessary — the leash delivers autonomy *without* amending it, so
   the cheaper/safer path is taken. (no-server-key is Tier-1, amendable by Council Lv7+, but is
   not touched here.)

# References

- ADR-2606101200 / 2606111400 — the organism leash (member-signed revocable CACAO capability)
- ADR-2605231525 / 2606072802 — no-server-key + its automation/read-only clarification
- finding 260617 — the reverted "R2 Autonomous" synthetic-signature anti-pattern
- `50-infra/etzhayyim-atproto-pds-clj/src/etzhayyim/pds/leash.clj` — PDS-side leash (built+tested)
- `70-tools/src/etzhayyim/fleet_probe.cljc` (`bb fleet:probe`) — the residency-gap evidence
- root `CLAUDE.md` — "Council attestation = Pull Request review" (bootstrap premise)
