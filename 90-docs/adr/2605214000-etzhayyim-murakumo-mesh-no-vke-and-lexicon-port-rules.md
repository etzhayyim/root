---
id: adr-2605214000-etzhayyim-murakumo-mesh-no-vke-and-lexicon-port-rules
title: "ADR-2605214000: Murakumo distributed cluster (no-VKE mesh) + vendor→religious-corp lexicon port verdict taxonomy + atomic identifier cutover"
status: active
doc_type: adr
topic: murakumo-mesh-and-lexicon-port-rules
authoritative: true
last_verified: 2026-05-25
priority: 7.0
axis: infrastructure
weight: 0.65
priority_note: "Referenced as authoritative by 6 SUBSTRATE-PORT-PENDING markers, 2 MIGRATION-NOTES.md sidecars, ADR-2605215000, ADR-2605212100, ADR-2605242330, ADR-2605211845, and CLAUDE.md §Do-Not / §Status row 21 — back-authored 2026-05-25 to close the ghost reference."
authoritative_for:
  - murakumo-no-vke-mesh-placement
  - lexicon-port-verdict-taxonomy
  - atomic-identifier-cutover-rules
depends_on:
  - 2605191346-etzhayyim-vultr-free-murakumo-control-plane
  - adr-2605192415-etzhayyim-religious-corp-daemon-architecture
  - 2605182312-local-bring-up-murakumo-gemma4
  - adr-2605201400-etzhayyim-kuni-umi-planetary-infra-fleet
related:
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605215100-etzhayyim-maps-sentinel-mlx-murakumo-fleet
  - adr-2605215200-shinka-pregel-mst
  - adr-2605215300-yoro-python-primitives
  - adr-2605212100-etzhayyim-to-etzhayyim-migration-batch
  - adr-2605242330-gov-procedure-pregel-mcp-coverage
supersedes: []
superseded_by: []
---

# ADR-2605214000: Murakumo distributed cluster (no-VKE mesh) + vendor→religious-corp lexicon port verdict taxonomy + atomic identifier cutover

**Status**: active
**Date**: 2026-05-21 (work landed) / 2026-05-25 (this ADR back-authored to close the dangling reference)
**Deciders**: Jun Kawasaki

# Context

Three pieces of work landed on 2026-05-21 that share a single authoritative ADR slot:

1. **Murakumo no-VKE mesh placement contract** — a YAML manifest at `50-infra/multicluster/murakumo-mesh/placement-contract.yaml` that maps the 10-node Mac-mini fleet (12-tribes-named per [ADR-2605182312](/90-docs/adr/2605182312-local-bring-up-murakumo-gemma4.md)) to Pregel cell groups per [ADR-2605192415](/90-docs/adr/2605192415-etzhayyim-religious-corp-daemon-architecture.md) §4, deliberately *without* a Virtual Kubernetes Environment (VKE / managed control plane). The mesh runs k3s with local nodeSelector pinning.
2. **Vendor → religious-corp lexicon port verdict taxonomy** — a 3-verdict classifier (REDIRECT / VENDOR-ONLY / REIMPLEMENT) used by the per-package MIGRATION-NOTES.md sidecars to classify each etzhayyim-side file's port path.
3. **Atomic identifier cutover** — the §3 cited 14 times across the repo (6 SUBSTRATE-PORT-PENDING markers, 2 MIGRATION-NOTES.md sidecars, ADR-2605215000 §3, ADR-2605212100, CLAUDE.md §Do-Not / §Status). This specifies the rules for the 220-file `etzhayyim-*` → `etzhayyim-*` identifier rename and the master gating condition.

The ADR file was never committed to `90-docs/adr/`. The sidecar artifacts (placement-contract.yaml + 2 MIGRATION-NOTES.md + CLAUDE.md row 21 entry) carry the actual decisions; this file is the canonical decision-record document that closes the dangling reference and gives downstream readers (subagents, future operators, CI hooks) a single place to navigate.

# Decision

## §1 Murakumo no-VKE mesh placement contract

### §1.1 What "no-VKE" means

No Virtual Kubernetes Environment — meaning no cloud-managed control plane (no GKE / EKS / AKS / kOps / Rancher Mesh Cloud). The Murakumo cluster runs:

- k3s servers + agents on each of 10 Mac-mini nodes (12-tribes naming).
- LAN-only mesh (private mDNS + ARP-resolved IPs, recorded in `fleet.toml`).
- No external control plane. The mesh's source-of-truth is two flat files: `50-infra/murakumo/fleet.toml` (node ↔ cell placement) + `50-infra/multicluster/murakumo-mesh/placement-contract.yaml` (multicluster-readable contract surface).

### §1.2 Cell placement is fleet.toml-authoritative

`fleet.toml` is canonical. `placement-contract.yaml` is a *projection* of fleet.toml for multi-cluster readability (kustomize generator at `70-tools/fleet-to-kustomize/`). Operators MUST edit `fleet.toml`; never edit `placement-contract.yaml` directly.

### §1.3 k8sResourcesAllowed: false invariant

Per `placement-contract.yaml` line 14, the contract's `spec.k8sResourcesAllowed` is `false`. Meaning: no Deployment / CronJob / DaemonSet / StatefulSet is authoritative *in this file*. K8s resources may exist in sibling kustomize overlays (and the cluster will apply them), but the canonical placement decision lives in `fleet.toml`. This guards against drift: if someone edits `kind: DaemonSet` thinking it's the source of truth, they're wrong, and lefthook checks (future) catch it.

### §1.4 Bind to existing ADRs

The placement contract's `metadata.adr` field already references the underlying ADRs: 2605191346 (fleet baseline) / 2605192415 (daemon architecture) / 2605182312 (12-tribes naming) / 2605201400 (Tier-B planetary infra). This ADR (2605214000) is the *master* that gathers all three pieces; the metadata stays as-is.

## §2 Vendor → religious-corp lexicon port verdict taxonomy

Three-verdict classifier used by all etzhayyim → etzhayyim port work:

| Verdict | Meaning | Action |
|---|---|---|
| **REDIRECT** | The line/file shape stays; only environment URL / variable name / package name changes. LiteLLM gateway / dispatcher / XRPC router abstracts the backend. | Identifier swap in the §3 atomic cutover wave. No behaviour change. |
| **VENDOR-ONLY** | The code path serves a commercial-SaaS workload (vendor `etzhayyim.com` paid pipeline). Religious-corp does not use it. | Code stays on the etzhayyim side; religious-corp callers must not invoke. Lefthook enforces caller-side rejection (see ADR-2605215000 §2). |
| **REIMPLEMENT** | Behaviour incompatible with religious-corp substrate boundary (e.g. RunPod cold-start protocol → EVO-X2 native protocol). | Rewrite required; cannot redirect. Tracked as a separate ADR per surface (e.g. ADR-2605215100 for maps-sentinel). |

This taxonomy is used by the two existing MIGRATION-NOTES.md sidecars:

- `50-infra/cluster/murakumo/MIGRATION-NOTES.md` (35 line-items, mostly REDIRECT — env var / DNS suffix / launchd label / config dir renames)
- `20-actors/magatama/py/PYMAGATAMA-MIGRATION-NOTES.md` (~30 line-items, mix of REDIRECT + VENDOR-ONLY + REIMPLEMENT)

New MIGRATION-NOTES.md sidecars MUST use the same 3-verdict taxonomy. Lefthook (future) checks the format.

## §3 Atomic identifier cutover

### §3.1 The 220-file cutover wave

The two MIGRATION-NOTES.md sidecars itemise ≈220 `etzhayyim-*` → `etzhayyim-*` identifier sites across two scopes:

- **Murakumo runtime** (`50-infra/cluster/murakumo/src/`): env var prefix (`etzhayyim_*` → `ETZHAYYIM_*`), config dir (`~/.etzhayyim/` → `~/.etzhayyim/`), DNS suffix (`.mesh.etzhayyim.com` → `.mesh.etzhayyim.com`), control plane URL, launchd label (`com.etzhayyim.murakumo` → `com.etzhayyim.murakumo`), systemd unit, binary name (`etzhayyim-murakumo` → `etzhayyim-murakumo`), cargo crate name, CDN URL.
- **pymagatama runtime** (`20-actors/magatama/py/`): RunPod-coupled call sites (REDIRECT / VENDOR-ONLY / REIMPLEMENT classified).

Plus the package-rename half referenced by 3 SUBSTRATE-PORT-PENDING markers in this session:

- `@etzhayyim/magatama-host-sdk` → `@etzhayyim/magatama-host-sdk`
- `@etzhayyim/magatama-gv7ps2m1` → `@etzhayyim/magatama-gv7ps2m1`
- `@etzhayyim/magatama-le9k4x2m` → `@etzhayyim/magatama-le9k4x2m`
- `@etzhayyim/graph-schema` → `@etzhayyim/graph-schema`

### §3.2 The atomic-PR invariant

**The 220-file cutover MUST execute as one atomic PR.** Per `MIGRATION-NOTES.md` headers: "Partial rename breaks the runtime (env vars + config dir + DNS suffix are interdependent)."

Interdependent target categories:

| Category | Why interdependent |
|---|---|
| env var prefix (`etzhayyim_*` / `ETZHAYYIM_*`) | If `src/config.rs` reads `ETZHAYYIM_*` but the launchd plist still exports `etzhayyim_*`, the daemon starts with unset env vars. |
| config dir (`~/.etzhayyim` / `~/.etzhayyim`) | If `src/main.rs` writes to `~/.etzhayyim/daemon.log` but the launchd plist's StandardErrorPath still points at `~/.etzhayyim/daemon.log`, logs go to two paths. |
| DNS suffix (`.mesh.etzhayyim.com` / `.mesh.etzhayyim.com`) | If half the nodes register under one suffix and half under the other, mesh discovery breaks. |
| control plane URL (`murakumo.etzhayyim.com` / `murakumo.etzhayyim.com`) | If the binary defaults to one but the install script `curl`s the other, install instructions silently fail. |
| launchd label (`com.etzhayyim.murakumo` / `com.etzhayyim.murakumo`) | If the plist filename and the Label key disagree, `launchctl load` refuses. |
| cargo crate name (`etzhayyim-murakumo` / `etzhayyim-murakumo`) | If the crate name changes but downstream `Cargo.toml` references the old name, build breaks. |
| package name (`@etzhayyim/*` / `@etzhayyim/*`) | If `src/app.ts` imports `@etzhayyim/sdk` but `package.json` declares `@etzhayyim/magatama-host-sdk` as a dep, npm resolution fails. |

The single-PR rule is the only safe execution path. Splitting it produces *guaranteed runtime breakage* during the migration window.

### §3.3 Master gating condition (legal registration)

§3 cutover does NOT execute until:

- The etzhayyim entity completes legal registration (CLAUDE.md §Status row 8: "amanomibashira → etzhayyim cutover (code identifiers)" is marked ✅, but the *atomic* cutover is row 21's `etzhayyim-*` → `etzhayyim-*` rename which is separately gated).
- Council 5-of-7 Safe attests the cutover wave readiness (ADR-2605192300).

Until both conditions hold, partial renames in `50-infra/cluster/murakumo/` and `20-actors/magatama/py/` are explicitly prohibited (CLAUDE.md §Do-Not item #15).

### §3.4 PR review checklist (for the executing PR)

When the atomic cutover PR opens, reviewers MUST verify all of:

1. All ≈220 itemised line-items from both MIGRATION-NOTES.md sidecars are addressed (no partial).
2. `Cargo.toml` crate name change is paired with all downstream `Cargo.lock` updates.
3. All `package.json` `repository` fields are updated (per CLAUDE.md §Status row 6 sed precedent).
4. launchd plist + systemd unit + binary name changes are simultaneous (any disagreement breaks `launchctl load` / `systemctl daemon-reload`).
5. Charter Rider notice in `NOTICE` files of the 39 first-party Apache-2.0 packages (CLAUDE.md §Status row 11) is preserved.
6. lefthook hooks (CLAUDE.md §Status row 16) still pass on the renamed paths.
7. `fleet.toml` and `placement-contract.yaml` references to old identifiers (if any) are updated together.
8. No remaining occurrences of `etzhayyim.com` in runtime code (comments may retain ADR references — comment-only mentions are allowed and expected).

### §3.5 Anti-checklist (what NOT to do during §3)

- Do not skip the `Cargo.lock` regeneration. Crate-name changes invalidate it.
- Do not use sed across the entire repo without scope filtering. The two MIGRATION-NOTES.md sidecars define the exact scope.
- Do not rename `@etzhayyim/sdk` imports without first verifying `@etzhayyim/sdk` exposes the equivalent surface. The SDK was rewritten, not aliased (per `20-actors/etzhayyim-sdk/README.md`).
- Do not introduce backwards-compatibility aliases (`@etzhayyim/magatama-host-sdk` re-export from `@etzhayyim/magatama-host-sdk`). That defeats the atomic invariant and creates indefinite dual-name maintenance.
- Do not split the §3 PR into multiple PRs across days. The mesh is broken during any non-atomic intermediate state.

# Consequences

- The 14 dangling references to ADR-2605214000 across the repo are now canonical-anchored. Future readers (including subagents in fresh sessions) can navigate to this ADR for the master decision.
- The §3 atomic cutover gating is formal. Partial renames are caught by CLAUDE.md §Do-Not and (future) lefthook hooks rather than by tribal memory.
- The 3-verdict lexicon-port taxonomy (REDIRECT / VENDOR-ONLY / REIMPLEMENT) is now the canonical classifier for all etzhayyim→etzhayyim port work. New MIGRATION-NOTES.md sidecars (future packages) MUST adopt this taxonomy.
- The no-VKE mesh stance is documented as a deliberate decision, not a gap. Operators considering "should we adopt managed Kubernetes?" have a written answer.

# Alternatives Considered

1. **Skip back-authoring — leave the ghost reference, since the work landed**. Rejected. 14 citation sites without a canonical document is an integrity hole; downstream sessions trip on it (this session did).
2. **Split §1, §2, §3 into three separate ADRs (one each for placement-contract, taxonomy, cutover)**. Rejected. CLAUDE.md row 21 explicitly references ADR-2605214000 as the master; renumbering all 14 citation sites to point at three different ADRs is high-churn and adds no clarity.
3. **Adopt VKE / managed Kubernetes for the Murakumo cluster (reverse §1)**. Rejected. LAN-only Mac-mini fleet has no need for a cloud control plane; adding one would add an attack surface and a monthly recurring cost, both incompatible with the religious-corp's non-profit posture.
4. **Allow partial §3 cutover with backwards-compatibility aliases**. Rejected (§3.5). Aliases create dual-name maintenance with no end date.
5. **Move the §3 master gating from "legal registration" to "Council Safe attestation only"**. Rejected. Legal registration is the operationally meaningful prerequisite (changes the entity's name on records that flow through the rename); Council attestation is the governance gate. Both are required, neither is a substitute.

# References

- `50-infra/multicluster/murakumo-mesh/placement-contract.yaml` (§1 canonical)
- `50-infra/cluster/murakumo/MIGRATION-NOTES.md` (§3 itemised, 35 line-items)
- `20-actors/magatama/py/PYMAGATAMA-MIGRATION-NOTES.md` (§3 itemised, ~30 line-items)
- `50-infra/murakumo/fleet.toml` (§1 fleet baseline)
- CLAUDE.md §Status row 21 (this ADR's completion-date anchor)
- CLAUDE.md §Do-Not item #15 (partial-rename prohibition)
- ADR-2605191346 (Murakumo Mac-mini fleet baseline)
- ADR-2605192415 (Religious-corp daemon architecture — §4 cell placement source)
- ADR-2605182312 (12-tribes naming)
- ADR-2605201400 (Tier-B planetary-infra producer)
- ADR-2605215000 §3 (companion identifier audit pattern)
- ADR-2605215100 (REIMPLEMENT example — maps-sentinel)
- ADR-2605212100 (etzhayyim→etzhayyim migration batch; this session's session-output)
- ADR-2605242330 (gov coverage 5-layer taxonomy; references this ADR's §3 gating)
- 6 `SUBSTRATE-PORT-PENDING.md` markers across `60-apps/etzhayyim-project-{gov,lawfirm-admin,legal-entity}/` (this session's outputs)
