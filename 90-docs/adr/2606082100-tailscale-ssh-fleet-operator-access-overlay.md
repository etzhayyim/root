---
id: adr-2606082100-tailscale-ssh-fleet-operator-access-overlay
title: "ADR-2606082100: Tailscale SSH mesh for the Murakumo Mac-mini fleet — keyless, tailnet-SSO-gated operator remote access"
status: proposed
doc_type: adr
topic: tailscale-ssh-fleet-operator-access-overlay
authoritative: true
last_verified: 2026-06-08
priority: 4.0
axis: infrastructure
weight: 0.35
priority_note: "Operator control-plane only. Records the secure remote-access overlay for the Mac-mini fleet (ADR-2605191346) so deploy/monitor/maintenance reach NAT'd edge nodes without per-node SSH key/password sprawl. Explicitly NOT a religious-corp substrate primitive: Tailscale carries no inference, no kotoba state, and no signing — so it touches none of the substrate-boundary or no-server-key invariants except to align with their spirit (identity, not a stored key, authorizes the session)."
authoritative_for:
  - the fleet operator remote-access overlay (Tailscale) and its auth model
  - the keyless Tailscale-SSH access convention for fleet nodes
depends_on:
  - "2605191346"  # Murakumo Mac-mini fleet = the only Tier-1 substrate
  - "2605215000"  # Murakumo-only inference (the plane this overlay must NOT touch)
  - "2605231525"  # no-server-key invariant (whose spirit this aligns with)
related:
  - "2605201400"  # kuni-umi planetary-infra fleet
supersedes: []
superseded_by: []
---

# ADR-2606082100: Tailscale SSH mesh for the Murakumo Mac-mini fleet — keyless, tailnet-SSO-gated operator remote access

**Status**: proposed
**Date**: 2026-06-08
**Deciders**: Jun Kawasaki

## Context

The Murakumo Mac-mini fleet is etzhayyim's only Tier-1 compute substrate
(ADR-2605191346 — Vultr-free) and the sole inference plane (ADR-2605215000 —
Murakumo-only). Operating it — `deploy.sh` / `monitor.sh`, langserver health,
cell rollout — requires reliable **operator remote access** to every node.

The prior state was per-node OpenSSH (macOS Remote Login) reachable only on the
local network, authenticated by password or per-node public key. That has three
problems for a home/edge fleet spread across NAT:

1. **No cross-NAT reach.** Nodes behind different routers are not mutually
   addressable without port-forwarding or a hand-rolled VPN.
2. **SSH key / password sprawl.** Per-node `authorized_keys` and passwords are a
   manual-rotation liability and sit awkwardly against the spirit of the
   **no-server-key** invariant (ADR-2605231525): a private key copied across the
   fleet is itself a standing credential to manage and leak.
3. **No central revocation.** Removing access means touching every node.

This overlay is **control-plane only**. It must not become a substrate
primitive: it carries no inference, no kotoba Datom state, and no signing, so it
is orthogonal to the substrate-boundary rules (`@etzhayyim/sdk`-only imports,
kotoba-canonical-state, USDC/Base, etc.). Those continue to apply unchanged to
the data plane.

## Decision

Adopt **Tailscale (WireGuard mesh)** as the operator control-plane overlay for
the fleet, and enable **Tailscale SSH** on every reachable node
(`tailscale set --ssh`), so port 22 on the tailnet interface is served by the
tailnet-identity-gated SSH server rather than by OpenSSH password auth.

- **Auth model — keyless, SSO-gated.** Sessions are authorized by tailnet SSO
  identity through a tailnet ACL `ssh` rule
  (`src: autogroup:member`, `dst: autogroup:self`, `users: autogroup:nonroot`)
  with `action: "accept"` for the operator's own single-user devices. Result:
  **no per-node `authorized_keys`, no distributed SSH private keys, no
  passwords** on the tailnet path. Access is granted and revoked centrally by
  the ACL / device list.
- **Enrollment.** A node joins with a **one-off / ephemeral tailnet auth key**
  held only in the operator secret store (macOS Keychain + 1Password), handled
  exactly like the DID private key — **never committed to the repo**.
- **Login convention.** Local account == node hostname (the established
  `<tribe>` convention in `[platform.cell_fleet]`); the primary node uses the
  operator handle. No usernames are recorded in-repo beyond that convention.
- **Scope boundary (load-bearing).** Tailscale is **operator infrastructure, not
  a religious-corp substrate primitive.** It does **not** replace the langserver
  mesh subnet (`10.99.0.0/16`), the geth/IPFS/Base anchor substrate, or the
  Murakumo-only inference path, and it carries none of them. `action: "check"`
  (periodic interactive re-auth) is available if a higher bar is ever wanted;
  `accept` was chosen so automation across the operator's own devices is
  non-interactive.

## Consequences

- **Positive — keyless reach.** Uniform cross-NAT SSH to every node with no
  `authorized_keys`/private-key sprawl; aligns with the no-server-key spirit
  (a tailnet *identity*, not a stored key, authorizes each session); central,
  revocable, SSO-gated.
- **Trade-off — SaaS control-plane dependency.** The Tailscale coordination
  server (`login.tailscale.com`) is a third-party control-plane dependency. The
  **data plane stays peer-to-peer WireGuard** (no traffic transits Tailscale).
  The de-SaaS exit is **Headscale** (self-hosted coordination), kept as a
  deferred future path; recorded here so the dependency is explicit, not silent.
- **Operational notes.** A node with macOS Remote Login disabled stays
  off-mesh-SSH until it is enabled (one such node at adoption time). Once
  Tailscale SSH is enabled, port 22 on the tailnet IP is served by the tailnet
  SSH server, so the legacy OpenSSH password path is shadowed on that interface
  by design.
- **Secrets hygiene (public repo).** No auth keys, passwords, tailnet IPs
  (`100.64.0.0/10` CGNAT, ephemeral per device), or local usernames are recorded
  in this repository. Only the architecture and conventions are documented.

## Alternatives Considered

- **Per-node OpenSSH keys (`authorized_keys` distribution).** Rejected: key
  sprawl + manual rotation, no NAT traversal, and a standing private-key
  liability counter to the no-server-key spirit.
- **Hand-rolled WireGuard mesh.** Rejected: manual peer/key config, no SSO, no
  ACL identity mapping, no SSH-user resolution.
- **Cloudflare Tunnel / `cloudflared` SSH.** Viable, but couples fleet admin to
  a Cloudflare account on the same plane as inference; Tailscale's per-device
  WireGuard + ACL fits the home/edge fleet better. May be revisited.
- **Headscale (self-hosted coordination) now.** Deferred: extra ops surface for
  little immediate gain; retained as the explicit de-SaaS exit if the hosted
  coordination dependency becomes unacceptable.

## References

- ADR-2605191346 — Murakumo Mac-mini fleet as the only Tier-1 substrate
- ADR-2605215000 — etzhayyim inference is Murakumo-fleet-only
- ADR-2605231525 — no-server-key invariant
- `deps.toml` → `[platform.cell_fleet]` (fleet roster + access overlay),
  `[platform.langserver.mesh]` (the separate `10.99.0.0/16` data-plane mesh)
