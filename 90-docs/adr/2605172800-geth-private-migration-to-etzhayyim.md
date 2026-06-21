---
id: adr-2605172800-geth-private-migration-to-etzhayyim
title: "ADR-2605172800: geth-private migration to etzhayyim — domain (legacy → geth.etzhayyim.com), responsibility, and eventual operatorship"
status: proposed
doc_type: adr
topic: geth-private-migration-to-etzhayyim
authoritative: true
last_verified: 2026-05-17
priority: 7.5
axis: organization
weight: 0.75
priority_note: "Stage 1 (DNS placeholder on etzhayyim.com zone) lands in this commit. Stages 2-4 (Worker proxy, K8s rehoming, sealer governance migration) are scheduled follow-ups. The chain itself (chainId 260425, data, contracts at ADR-2605172300 S0) is unchanged — only the operator branding + DNS canonical move."
authoritative_for:
  - canonical RPC URL for the etzhayyim private chain (geth.etzhayyim.com)
  - operational responsibility transfer from upstream operator to etzhayyim
  - sealer governance migration plan (single-sealer → etzhayyim multisig)
  - 12-month redirect grace window for the legacy private-chain RPC host
depends_on:
  - adr-2605170900-etzhayyim-root-adr-canonical-home
  - adr-2605172000-etzhayyim-kotoba-substrate
  - adr-2605172300-etzhayyim-bi-asset-substrate
related:
supersedes: []
superseded_by: []
---

# ADR-2605172800: geth-private migration to etzhayyim — domain + responsibility + operatorship

**Status**: proposed (Stage 1 in this commit, Stages 2-4 pending)
**Date**: 2026-05-17
**Deciders**: Jun Kawasaki

# Context

The etzhayyim ecosystem has TWO Ethereum-substrate concerns:

1. **Base L2 (Coinbase)** — public, third-party-anchorable; hosts EtzhayyimAnchor + EtzhayyimPaymaster + EtzhayyimMembership per ADRs 2605171800 / 2605172100 / 2605172600. The 信者 (Shinja) self-sovereign membership flow lives here.
2. **`geth-private` (chainId 260425)** — the religious-corp's internal Clique-PoA private chain. Hosts the [`etzhayyim-chain-contracts/`](../../50-infra/etzhayyim-chain-contracts/) suite per ADR-2605172300 (AdherentRegistry + KishaStream + Constitution + Governance + CorpusRegistry + HoldingAttestation + AnchorBridge + Phenotype + TreasuryMirror). The officer-witnessed Adherent SBT membership flow lives here.

The private chain currently runs on:

- Vultr VKE cluster in a legacy upstream cloud account
- K8s namespace `geth-private` (legacy-operator-controlled)
- Single sealer EOA `0xaFed0Cb7633EDBd26aA52658e71528309F562501` (legacy-held key)
- Canonical RPC at the legacy private-chain RPC host (legacy CF zone, Worker proxy)

This is fine as a legacy-operated bootstrap. But per the operating-entity boundary (`etzhayyim` → `etzhayyim`, ADR-2605102200 + ADR-2605152100): the **religious-corp internal chain** belongs to etzhayyim, not to its upstream operator. The current state is a hold-over from before the org boundary was established. Now is the time to actualize the move.

The chain itself does **not** need to physically move clouds today. The migration is staged so that brand / DNS / domain / governance shift to etzhayyim immediately, while the K8s deployment can stay on Vultr (under etzhayyim's governance contract with the legacy operator continuing as service provider) until natural infra-refresh time.

# Decision

Migrate the canonical identity + responsibility of the `geth-private` chain from the legacy upstream operator to `etzhayyim` (principal), in 4 stages.

## Stage 1 — Canonical DNS (this commit)

- Create `geth.etzhayyim.com` on the etzhayyim.com CF zone (`54dece4ac787807d4c3410243916a1e6`).
- Initial pointing: AAAA `geth.etzhayyim.com → 100::` proxied (placeholder), matching the apex `etzhayyim.com` and `yoro.etzhayyim.com` pattern. The Worker route binding follows in Stage 2.
- Both the legacy host and `geth.etzhayyim.com` (new canonical) resolve to the same backend during the migration window.
- SSoT update: `deps.toml [platform.l2.private_chain].canonical_domain = "geth.etzhayyim.com"`; the `legacy_domain` field records the legacy host for the grace-period tools.

After this stage, anyone configuring a wallet or RPC client SHOULD use `geth.etzhayyim.com`. The old URL continues to work but is no longer canonical.

## Stage 2 — etzhayyim-owned Worker proxy (follow-up, ~1 day work)

Currently the geth RPC is fronted by a CF Worker living in the legacy upstream CF account (a `geth-rpc-proxy` Worker in the legacy monorepo). For etzhayyim ownership:

- Mirror the Worker into `etzhayyim/root/50-infra/etzhayyim-geth-rpc-proxy/` (Apache 2.0 license, same RPC-proxy logic).
- Bind the Worker to the route `geth.etzhayyim.com/*` on the etzhayyim CF zone.
- The legacy host Worker becomes a 301 redirect to `geth.etzhayyim.com` (12-month grace).
- The K8s backend (still on the legacy Vultr cluster) is reached via the **same Cloudflare Tunnel** that the legacy Worker uses today — re-published into the etzhayyim CF account, OR cross-account tunnel access negotiated as a transitional measure.

## Stage 3 — K8s rehoming (follow-up, weeks-to-months)

Move the `geth-private` namespace + StatefulSet + PVC + Cloudflare Tunnel out of the legacy Vultr cluster and into an etzhayyim-controlled cluster. Options:

- **Option A**: etzhayyim contracts a new Vultr account directly (etzhayyim-controlled billing).
- **Option B**: rent K8s capacity from a different provider (Akash / Vast / specific bare-metal operator).
- **Option C**: rehome onto the Mac-mini fleet locally for the early stage; promote to cloud once stable.

The chain data (chaindata PVC) transfers as a tar archive; chainId 260425 + genesis hash `0x944c4a5e5c95ddad221cd8cb5f2356628b88de9dcebdfbbd0b84d0d8b8ef4c13` are unchanged, so all existing contracts continue at their current addresses.

## Stage 4 — Sealer governance migration (follow-up, months)

The single sealer key (legacy-held EOA) is the chain's **only** consensus authority — whoever holds it can rewrite the next 5-second block. For genuine etzhayyim sovereignty, this must move:

- **Short-term**: rotate to a NEW sealer EOA held by etzhayyim's keychain + 1Password (etzhayyim vault, like the L2 deployer). Genesis amendment is NOT required — Clique sealer set is changeable in-band via signed votes from existing sealer.
- **Medium-term**: add a second sealer for redundancy (Clique allows multi-sealer; 2/3 sign required for finality).
- **Long-term**: deploy a Safe multisig as one of the sealers (Safe-as-sealer requires a wrapper; out of scope for v0).

# Consequences

## 正の効果

- **Brand alignment**: every URL in the etzhayyim ecosystem is on etzhayyim.com.
- **Substrate ownership**: the chain that holds AdherentRegistry + KishaStream + TreasuryMirror is named, branded, and governed by etzhayyim.
- **Foundation for Stage 4**: once governance migration completes, etzhayyim has full sovereignty — no single external operator can rewrite the chain.
- **Service-provider relationship preserved**: the legacy operator continues as a service provider under SOW (operating the K8s + Cloudflare Tunnel infrastructure), but no longer as the chain's owner.

## 負の効果 / コスト

- **DNS cutover risk**: clients hardcoding the legacy host continue to work (12-mo grace) but should migrate. SDK + wallet config updates needed.
- **Worker mirror work**: ~1 day to mirror geth-rpc-proxy, bind route, set up cross-account tunnel access.
- **K8s rehoming work**: weeks-to-months; needs new infra account + tunnel reconfiguration + data transfer.
- **Sealer rotation risk**: until Stage 4 completes, the chain remains legacy-operator-controlled at the consensus layer. Acceptable as a known-finite-window risk.
- **No automatic legal change**: the chain is operated by etzhayyim post-Stage 4, but Japanese law treats the underlying compute as the operator's; etzhayyim's 任意団体 form means the operating entity is whoever signs the cloud bill.

# Alternatives Considered

## A. Status quo: keep geth-private on the legacy operator indefinitely

Cheapest. But violates the operating-entity boundary (ADR-2605152100) and creates a permanent operator-lock on the religious-corp's internal substrate. Rejected: structural misalignment.

## B. Migrate everything at once (DNS + Worker + K8s + sealer in one cutover)

Cleanest end-state but high coordination cost + downtime risk. Rejected: Stage 1 (DNS placeholder) is enough to start now, and each subsequent stage can land independently with grace-window safety.

## C. Deploy a NEW private chain under etzhayyim and migrate contracts

Fresh `etzhayyim-geth` with new chainId. Rejected: existing contracts at known addresses (AdherentRegistry, KishaStream, etc.) would need redeploy + state migration; clients referring to chainId 260425 would break; existing Adherent SBT holders would lose their issuance. The chain stays, the operator changes.

## D. Move to public L1 (Ethereum mainnet)

Decommission private chain entirely, run everything on Ethereum mainnet. Rejected: gas cost (~1000x Base L2), no internal-state privacy posture, loses the "religious-corp internal economy" semantics that justify a private chain.

# Migration plan

- [x] Stage 1.1 — Update `deps.toml [platform.l2.private_chain]` with canonical_domain + legacy_domain fields
- [x] Stage 1.2 — Create CF DNS record `geth.etzhayyim.com` AAAA `100::` proxied (this commit)
- [ ] Stage 2 — Mirror geth-rpc-proxy Worker to `50-infra/etzhayyim-geth-rpc-proxy/` + bind Worker route
- [ ] Stage 2 — Legacy RPC host Worker → 301 redirect to `geth.etzhayyim.com`
- [ ] Stage 3 — K8s rehoming (option selection + execution; etzhayyim's own Vultr account or Mac-mini fleet)
- [ ] Stage 4 — Sealer rotation to etzhayyim-held EOA (keychain + 1Password)
- [ ] Stage 4 — Multi-sealer (add second redundant sealer)
- [ ] Stage 4 — Safe-as-sealer wrapper (long-term)

# References

- ADR-2605152100 [etzhayyim GitHub Org Boundary](./2605152100-etzhayyim-github-org-boundary.md) — operating-entity rule
- ADR-2605172300 [etzhayyim Kisha-Stream / Goji-Treasury (bi-asset substrate)](./2605172300-etzhayyim-bi-asset-substrate.md) — the contracts that live on this chain
- ADR-2605172000 [kotoba substrate](./2605172000-etzhayyim-kotoba-substrate.md)
- ADR-2605172700 [Membership layering](./2605172700-membership-layering-shinto-adherent.md) — 信者 (Base L2) + Adherent (geth-private) tiers
- Legacy upstream `50-infra/vultr/geth-private/CLAUDE.md` — current operational state of the chain (will be referenced + mirrored during Stage 2)
