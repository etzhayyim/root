---
id: adr-2605191659-vultr-stays-for-etzhayyim
title: "ADR-2605191659: Vultr stays for etzhayyim.com — supersede step 6 of ADR-2605191358"
status: active
doc_type: adr
topic: vultr-stays-for-etzhayyim
authoritative: true
last_verified: 2026-05-19
priority: 7.0
axis: governance
weight: 0.70
priority_note: "Reinforces operator directive: 50-infra/vultr/* dirs remain in etzhayyim/root as etzhayyim.com legacy resources; no archive sweep. Removes a misleading step from ADR-2605191358 that implied otherwise."
authoritative_for:
  - 50-infra/vultr/* retention policy in etzhayyim/root
  - supersession of ADR-2605191358 §step 6 (Vultr archive sweep)
depends_on:
  - adr-2605170900-etzhayyim-root-adr-canonical-home
  - 2605191346-etzhayyim-vultr-free-murakumo-control-plane
  - adr-2605191358-yoro-murakumo-rw-free-rewrite-map
related: []
supersedes:
  - "(strengthens, does not delete) 2605191358-yoro-murakumo-rw-free-rewrite-map §step 6"
superseded_by: []
---

# ADR-2605191659: Vultr stays for etzhayyim.com — supersede step 6 of ADR-2605191358

**Status**: active
**Date**: 2026-05-19
**Deciders**: Jun Kawasaki

# Context

ADR-2605191346 established the hard boundary: `etzhayyim/*` workloads run on the Murakumo Mac-mini fleet only; the Vultr-based legacy cluster manifests under `50-infra/vultr/*` are explicitly marked **etzhayyim.com legacy** and OUT of that ADR's archive scope.

ADR-2605191358 §Ordering then listed:

> 6. **Vultr archive sweep** — multicluster + yoro-actors-raw Postgres removed; legacy Vultr dirs move to `50-infra/_archive/vultr/`.

That phrasing contradicts ADR-2605191346 §2 (which keeps `50-infra/vultr/` for etzhayyim.com use) and was over-eager. The operator confirmed on 2026-05-19:

> "vulter は etzhayyim.com としては使うので、それは残しておいて"
> (Vultr is used for etzhayyim.com, leave it as-is.)

This ADR records the correction.

# Decision

1. **`50-infra/vultr/*` remains in `etzhayyim/root`** unchanged. No `_archive/vultr/` move; no rename; no physical separation in this ADR.
2. **The substrate boundary is unaffected**. `etzhayyim/*` workloads still must not target Vultr (ADR-2605191346 §1). The lefthook substrate-boundary gate (ADR-2605191648) continues to block new direct imports of RW / Hyperdrive / Kysely / fiat-payment SDKs in app code.
3. **Step 6 of ADR-2605191358 is superseded** by this ADR. The follow-ups it implied (move multicluster, move yoro-actors-raw Postgres) are dropped. The underlying substrate fixes for those workloads are addressed by:
   - The rewrite map (ADR-2605191358 steps 1-5) for any etzhayyim-branded surface
   - etzhayyim.com operator's discretion for anything Vultr-hosted that is NOT etzhayyim-branded
4. **Physical separation to a different repo** (e.g. `etzhayyim-co-jp/legacy-vultr-manifests`) remains a follow-up task tracked alongside repo-root `CLAUDE.md` Step 8 cutover, at the operator's pace. This ADR does not schedule it.

## Hard rule recap (no change)

| Path | Tenant | Vultr allowed? |
|---|---|---|
| `50-infra/vultr/*` | **etzhayyim.com legacy** | ✅ stays (no archive sweep) |
| `50-infra/k8s/*` | etzhayyim | ❌ Murakumo Mac-mini only |
| `50-infra/etzhayyim-*` | etzhayyim | ❌ Murakumo / Cloudflare only |
| `60-apps/etzhayyim-project-*` | etzhayyim (during rename grace) | ❌ |
| `20-actors/*` | etzhayyim | ❌ |

(Identical to ADR-2605191346 §2; reproduced here for cross-reference.)

# Consequences

**Positive**:

- Clear operator-visible signal that the Vultr manifests are NOT going to disappear from this repo.
- ADR-2605191358 is no longer self-contradictory with ADR-2605191346.
- No CI work needed — substrate boundary enforcement is already in place at the lint layer (ADR-2605191648).

**Negative**:

- The `50-infra/vultr/` tree contains substrate-violating manifests (RisingWave, Postgres, Hyperdrive references) by design (these are the etzhayyim.com legacy stack). The lefthook substrate-boundary gate (`70-tools/scripts/lint/substrate-boundary.mjs`) must continue to allowlist the `50-infra/vultr/*` path so the gate doesn't block routine etzhayyim.com-side commits. Verify on next commit that touches anything under `50-infra/vultr/`; tune the allowlist if needed.

**Required follow-ups**:

- ADR-2605191358 progress table (in past PRs and READMEs) updates: step 6 is marked **superseded** rather than ⏳ pending.
- Substrate-boundary lefthook allowlist: confirm `50-infra/vultr/` is treated as etzhayyim-legacy and not gated against the etzhayyim allowlist.

# Alternatives Considered

**A. Honour ADR-2605191358 step 6 literally and move 50-infra/vultr/ to _archive/.**
Rejected. Contradicts the operator directive and ADR-2605191346 §2. Would also break etzhayyim.com's running deployment path.

**B. Move 50-infra/vultr/ to a separate repo immediately.**
Rejected for this ADR. Operator decision deferred to repo-root `CLAUDE.md` Step 8 cutover; not scheduled here. Cross-cutting concern (deployment scripts, CI references, docs) requires its own cutover ADR.

**C. Hide 50-infra/vultr/ from CI gate via path-level allowlist only, no policy ADR.**
Rejected. The policy needs to be discoverable as an ADR, not buried in a lint script.

# References

- ADR-2605170900 (etzhayyim/root canonical home for open ADRs)
- ADR-2605191346 (Vultr-free + Murakumo Mac-mini Tier-1 — this ADR reinforces §2)
- ADR-2605191358 (yoro/murakumo RW-free rewrite map — this ADR supersedes §step 6)
- ADR-2605191648 (substrate-boundary lefthook — allowlist gate verifier)
- Operator directive: 2026-05-19 conversation logs
