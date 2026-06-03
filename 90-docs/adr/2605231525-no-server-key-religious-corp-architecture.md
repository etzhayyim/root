---
id: adr-2605231525-no-server-key-religious-corp-architecture
title: "ADR-2605231525: No-Server-Key Religious-Corp Architecture"
status: proposed
doc_type: adr
topic: no-server-key-architecture
authoritative: true
last_verified: 2026-05-23
priority: 9.0
axis: architecture
weight: 0.95
priority_note: "Constitutional posture — affects every infra surface; supersedes any pattern that assumes a server-held signing key."
authoritative_for:
  - server-side-secret-policy
  - member-write-model
  - charter-rider-section-1-6-middleman-elimination
depends_on:
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192115-etzhayyim-non-profit-donation-only-no-ads
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605172000-etzhayyim-rw-free-substrate
  - adr-2605172100-etzhayyim-payments-on-chain-only
  - adr-2605181100-mst-encrypted-records-signal-keywrap
  - adr-2605231400-kotoba-datomic-holochain-iso-substrate
  - adr-2605231500-kotoba-datomic-projection
related:
  - adr-2605192300-etzhayyim-bootstrap-council-five
  - adr-2605192315-etzhayyim-transparent-force-rd
supersedes: []
superseded_by: []
---

# ADR-2605231525: No-Server-Key Religious-Corp Architecture

**Status**: proposed
**Date**: 2026-05-23
**Deciders**: Jun Kawasaki

# Context

ADR-2605192100 §1.6 (Mission Charter — middleman elimination) and Charter
Rider v2.0 §1 (substrate hard rules) require etzhayyim to operate as an
**open religious-corp** without any single trust-bearing intermediary.

Today the running infrastructure still violates that posture in many
places: Cloudflare Workers, K8s pods, and CronJobs hold server-side
secrets that, if seized or compromised, would let a single operator
impersonate etzhayyim, write to its PDS, drain its donation flow, or
read its encrypted records. The post-mortem of the Stripe / Clerk
removals (P3) showed the same pattern: every external SaaS we
integrated forced us to hold a master credential, which became a
governance liability the moment Council ratification was attempted.

The corresponding architectural posture must be: **etzhayyim
infrastructure holds zero signing capability**. All writes — donation,
DID rotation, lexicon record creation, bulk-data ingestion — must be
signed by the **member** (donor, contributor, community operator) who
authored them. etzhayyim provides public read surfaces: relays,
indexers, IPFS pinning, lexicon publication, contract verification.

This ADR records that posture, enumerates the secret-bearing surfaces
that must be flipped, and defines the per-stage sequence that does so
without breaking the live customer journey.

## Server-held secret inventory (2026-05-23 snapshot)

The following secrets are currently held by etzhayyim-operated
infrastructure. Each one is a deviation from the no-server-key
posture and is itemised here as the authoritative migration list.

| # | Secret | Held by | Used for | Member-write replacement |
|---|---|---|---|---|
| 1 | `YATA_DONATE_PRIVATE_KEY` | yatabase Worker | USDC EOA signer for `/api/donate` (added during the Stripe→USDC cutover) | Member wallet signs USDC.transfer + TitheRouter.route in-browser via viem/Coinbase Smart Wallet. Worker only verifies the txHash + `payment.sent` AT record. |
| 2 | `did:web:authn.etzhayyim.com` Worker DID key | macOS Keychain + 1Password mirror | ES256 P-256 sign of agent Service Auth JWTs and Worker-issued AT session JWTs | did:plc / member did:web with passkey + ERC-725 root (ADR-0074). etzhayyim publishes DID documents but never signs. |
| 3 | `SS_REPO_SIGNING_KEK` (KEK master) | Worker Secrets Store | KEK envelope encryption of D1 private-key material (ADR-0010 Stage 1) | Each member encrypts with their own Signal identity (ADR-2605181100). KEK becomes per-member, not platform-wide. |
| 4 | `DATABASE_URL` (RisingWave creds) | bulk-ingest pods + Worker `HYPERDRIVE` | Direct INSERT into `vertex_spatial` and friends | Community operator publishes signed AT records → etzhayyim relay subscribes → kotoba-datomic-projection rebuilds the read cache (ADR-2605231500). |
| 5 | `B2_ACCESS_KEY_ID` / `B2_SECRET_ACCESS_KEY` | bulk-ingest pods | Parquet shard + gsplat PLY + baked GLB upload | Content-addressed CID. Members or community operators submit `{cid, sha256}`; etzhayyim pins via IPFS (no upload credentials). |
| 6 | `RESEND_API_KEY` | auth Worker, yatabase Worker | Magic-link + invoice email | Member-side SMTP (ProtonMail / Migadu / self-hosted). etzhayyim emits unsigned event records; member's own client polls them. |
| 7 | `MAPILLARY_ACCESS_TOKEN` | gsplat-train k8s deploy | Mapillary image fetch | Community operator's token. Their submission lands as a member-signed `com.etzhayyim.maps.gsplatAsset` record. |
| 8 | `RUNPOD_API_KEY` | gsplat-train k8s deploy | GPU job submission for 3D Gaussian Splatting | Same — community operator runs the trainer with their own RunPod account. |
| 9 | `ODPT_API_KEY` | gtfs-rt k8s deploy | Real-time transit feeds | Same — community operator runs the dumper with their own ODPT registration. |
| 10 | `DISPATCHER_INTERNAL_SECRET` | Worker ↔ bpmn-dispatcher pod HMAC | Worker-to-pod auth | Disappears once internal pods are removed (see #4). If a residual pod survives, its operator runs it with their own HMAC chain. |
| 11 | `YATA_AGENT_ADMIN_KEY` | yatabase Worker | Single-operator admin gate for outbox approve / batch trigger | Council Lv6+ 5-of-7 Safe multisig (1 SBT = 1 vote, already deployed for the Public Fund). |
| 12 | `EMBED_AUTH_TOKEN` | maps-ui Worker → embedder pod | Vector embedding service auth | Community-operated embedder; submission is a member-signed `com.etzhayyim.maps.visionResult` record. |
| 13 | Auth Worker P-256 keypair per agent (715+ ES256 keys) | KEYS_DB (D1, KEK-wrapped) | Service Auth JWT signing for AI agents | Each agent generates its own keypair on the member's device; KEYS_DB becomes a kotoba-datomic-projection cache (ADR-2605231500) that the operator can rebuild. |

`STRIPE_SECRET_KEY` (already removed per Charter Rider §2,
ADR-2605192115) and Clerk SDK keys (already removed in P3) are
included here for completeness as the precedent: every previous
external-SaaS secret was eliminated under the same posture.

## What etzhayyim *does* hold (key-less surfaces, allowed)

After full flip, etzhayyim continues to operate the following surfaces.
None of them require signing capability:

1. **AT Protocol relay** — `com.atproto.sync.subscribeRepos` over
   public member PDSs.
2. **Indexer / kotoba-datomic-projection** — read-only L0 caches rebuildable
   from MST + IPFS per ADR-2605231500.
3. **DID Document serving** — `did:web:etzhayyim.com/.well-known/did.json`
   serves a public document. The signing of that document, if any
   updates are needed, is performed off-line by the Council multisig
   and committed via git (the Worker just publishes the static blob).
4. **Lexicon publication** — `00-contracts/lexicons/**/*.json` shipped
   as static assets.
5. **Contract verification** — Base L2 read-only RPC for
   `ChartersComplianceRegistry.isNonAlignedAddress(addr)` etc. No
   private key.
6. **IPFS pinning** — content-addressed, signer-free.
7. **Static asset serving** — Workers Assets / GitHub Pages.

# Decision

1. **Constitutional invariant**: etzhayyim-operated infrastructure
   (Workers, K8s pods, CronJobs, CI runners, hosted bots) **MUST NOT
   hold private keys, signing tokens, or master credentials** that
   could be used to impersonate etzhayyim or its members.

   This rule is added to the `/CLAUDE.md` § "Substrate boundary"
   table as a new row (`Server-side signing capability | none (member
   wallets / passkeys / community-operated dumpers) | any platform-
   held private key or master credential`). It sits alongside the
   substrate hard rules already in force:

   - State on MST + IPFS + Base L2 anchor only (ADR-2605172000).
   - Payment via USDC on Base L2 via TitheRouter only (ADR-2605172100).
   - No third-party advertising / pixels (ADR-2605192115 §1.2).
   - Plaintext records on MST forbidden (ADR-2605181100).

   Council ratification of this ADR triggers a Charter Rider v2.0
   amendment (a new §1 "PLATFORM POSTURE" section adjacent to the
   existing §2 PROHIBITED USE) so the rule is enforceable at the
   license layer, not only the operational layer.

2. **Member-write model**: all writes to etzhayyim-controlled
   collections (`com.etzhayyim.apps.maps.*`, `com.etzhayyim.apps.payment.*`,
   `com.etzhayyim.auth.*`, `com.etzhayyim.encrypted.*`, …) MUST be
   signed by the member, donor, contributor, or community operator
   whose action they record. etzhayyim relays do not sign on behalf
   of any subject.

3. **Read-only infra exemption**: the seven surfaces in §"What
   etzhayyim *does* hold" remain operable by etzhayyim infrastructure.
   The line is drawn at "can this surface impersonate or steal" —
   relays, indexers, IPFS pinners, and static publishers cannot.

4. **Stage roadmap** (executable, ordered).

   Status legend: ✅ applied this PR · 🟡 scaffold ready, operator
   cutover pending · ⏳ blocked on prior Stage.

   - **Stage A — USDC signer removal** · ✅ applied (2026-05-23).
     `YATA_DONATE_PRIVATE_KEY` dropped from the yatabase Worker.
     `src/donate.ts` rewritten as verify-only — accepts member-
     signed Base L2 `txHash`, queries the public RPC for the
     receipt, decodes the USDC Transfer log, validates recipient ∈
     {treasury, TitheRouter, expectedRecipient}, returns the
     receipt for the member's client to commit to its own PDS.
     `svelte/src/routes/studio/billing/+page.svelte` and the
     auth Worker's `sign-up/+page.svelte` drive the wallet flow
     directly (EIP-1193 → switch chain → ABI-encode USDC.transfer
     → `eth_sendTransaction` → poll → verify). `wrangler.jsonc`
     now declares `YATA_DONATE_RPC_URL` / `_USDC_CONTRACT` /
     `_TREASURY` / `_TITHE_ROUTER` / `_MAX_USDC_MICROS` as public
     read-only coordinates with the `no-server-key: read-only`
     exemption marker. **Pending operator action**: substitute the
     placeholder zero addresses with the deployed Treasury Safe +
     TitheRouter address; run `wrangler secret delete
     YATA_DONATE_PRIVATE_KEY` to confirm the rollback artefact is
     truly gone. Runbook: `60-apps/etzhayyim-project-yatabase/RUNBOOK-USDC-DONATE.md`.

   - **Stage B — Bulk-ingest community-operator handover** · 🟡 scaffold ready.
     Each of the 13 maps bulk-ingest pods becomes a standalone
     repository under `etzhayyim-community/maps-{dataset}-dumper`.
     Substrate seam `_etzhayyim_substrate.py` (already shipped) auto-
     dispatches on `ETZHAYYIM_SUBSTRATE_MODE` — community operators
     set `mst` mode, configure their own PDS handle + upstream API
     credential, and run on their own infrastructure. The etzhayyim
     relay subscribes via `com.atproto.sync.subscribeRepos`. The
     existing kotoba-datomic-projection manifest at
     `60-apps/etzhayyim-project-maps/bulk-ingest/workers/kotoba-datomic-projection.edn`
     already declares the RW projection layer as L0-rebuildable, so
     the read cache survives the operator handover. **Applied this
     PR**: `60-apps/etzhayyim-project-maps/bulk-ingest/COMMUNITY-OPERATOR-HANDOVER.md`
     (13-pod plan + per-pod checklist + Charter-aligned gating),
     `_working/stage-b/community-repo-template/` (README + NOTICE +
     `.github/workflows/charter-compliance.yml`),
     `_working/stage-b/issue-templates/13-pod-handover.md` +
     `13-rows.csv`. **Pending operator action**: create the
     `etzhayyim-community` GitHub org, fork the 13 pods, open the
     13 recruitment issues, register each pod's DID with
     `ChartersComplianceRegistry`, deactivate the etzhayyim-operated
     k8s deployments after ≥7 days of clean records from the
     community operator's DID.

   - **Stage C — Identity-signing devolution** · 🟡 scaffold ready (C-1 ready to run; C-2/C-3/C-4 pending Council ratify).
     **C-1** (this PR): `50-infra/etzhayyim-did-web/did-multi-controller.json`
     proposed next-state — `controller` becomes
     `[did:web:etzhayyim.com, did:pkh:eip155:8453:0x<safe>]`,
     `verificationMethod` adds `#council-safe` with
     `EcdsaSecp256k1RecoveryMethod2020` (ERC-1271
     `isValidSignature`), `capabilityInvocation` +
     `capabilityDelegation` restricted to `#council-safe`. The
     existing Ed25519 `#key-0` is retained for a 30-day backward-
     compat rollback window, then dropped in C-1.b.
     `cutover-stage-c1.sh` automates substitution of the Safe
     address + canonical JCS-stripped doc + sha256 attestation
     hash; Council 5-of-7 signs the hash via Safe app
     (`isValidSignature` magic value `0x1626ba7e`). Smoke-tested
     2026-05-23 with placeholder Safe address — produces valid
     canonical JSON + attestation envelope.
     **C-2 (per-agent device key)**: `com.etzhayyim.auth.registerAgentKey`
     replaces `com.etzhayyim.auth.createAgentSession`'s server-side
     `crypto.subtle.generateKey`. Agent runtime (operator's own
     device) generates the keypair locally, POSTs public key + a
     WebAuthn-style PoP. `vertex_etzhayyim_key_signing.private_key_b64`
     column dropped — the table holds only public keys.
     **C-3 (passkey-derived session)**: WebAuthn passkey derives
     a per-passkey ES256 keypair (deterministic from COSE public
     key + per-PDS salt). The session token becomes a DPoP-style
     PoP signed by the passkey. Worker verifies (read-only)
     against the public-key projection.
     **C-4 (KEK removal)**: 30-day overlap window logs all reads
     of `SS_REPO_SIGNING_KEK` and expects zero; then
     `wrangler secret delete SS_REPO_SIGNING_KEK`. Runbooks:
     `60-apps/etzhayyim-project-auth/STAGE-C-IDENTITY-SIGNING-DEVOLUTION.md`,
     `50-infra/etzhayyim-did-web/STAGE-C1-DID-CUTOVER.md`.

   - **Stage D — External-API liability handover** · 🟡 scaffold ready, blocked on Stage B.
     Six external credentials migrate to community-operator
     ownership: RESEND_API_KEY (auth + yatabase email; replaced by
     member-side SMTP emitting `com.etzhayyim.apps.email.outbox`), B2
     keys (replaced by content-addressed CIDs pinned via IPFS),
     MAPILLARY_ACCESS_TOKEN + RUNPOD_API_KEY (community operator's
     own gsplat trainer pod), ODPT_API_KEY (community operator's
     own gtfs-rt feed), EMBED_AUTH_TOKEN (community-operated
     embedder pod). etzhayyim publishes lexicons but never the
     credential. Runbook: `_working/STAGE-D-EXTERNAL-API-HANDOVER.md`.

   - **Stage E — Internal-HMAC dissolution** · ⏳ blocked on Stages A-D.
     With no internal Worker ↔ pod path remaining across an
     etzhayyim-owned trust boundary, `DISPATCHER_INTERNAL_SECRET`
     and `YATA_AGENT_ADMIN_KEY` are removed. Admin surfaces
     (yatabase outbox approve, batch usage-alert trigger) migrate
     to Council Lv6+ multisig per the existing 1 SBT = 1 vote
     enforcement. Acceptance: `e7m verify --no-server-key` reports
     zero violations and zero exemption markers across the entire
     monorepo.

5. **Acceptance criteria**: a `e7m verify --no-server-key` invariant
   is added to the constitutional verifier (`70-tools/e7m/`) that
   greps every wrangler.jsonc / k8s manifest / docker-compose /
   GitHub Action for the literal env-var names enumerated in the
   inventory table above. CI fails when any non-exempt match is
   found. Exemption is granted only to read-only surfaces
   §"What etzhayyim *does* hold" via a `// no-server-key: read-only`
   marker.

# Consequences

## Positive

- Attack surface for impersonation / seizure / key compromise drops
  to **zero** for the etzhayyim relay tier.
- Religious-corp posture (Charter §1.6 middleman elimination) becomes
  literally enforceable, not just an aspiration.
- Member custody is the default. Members keep control of donations,
  identity, encrypted records, and contributed data.
- 訴訟・押収 (litigation / seizure) liability does not transfer
  through etzhayyim's operator — there is nothing for an adversary
  to subpoena beyond public records.
- Council multisig becomes the *only* entity that can update
  protected resources (DID documents, lexicons, contracts), aligning
  with ADR-2605192300's three-tier enforcement.

## Negative

- Member UX gets heavier: a wallet, a passkey, and (for community
  operators) an IPFS pinner or SMTP relay become preconditions.
- Bootstrap phase loses bulk-ingest coverage if no community
  operator volunteers — until then, etzhayyim cannot itself run the
  Mapillary / RunPod / ODPT dumpers and the corresponding 3D / RT
  feeds stay gated.
- Donation flow gets a one-step indirection: member must approve a
  Base L2 transaction in their wallet before yatabase issues a plan
  upgrade. Failure modes (insufficient balance, paymaster outage,
  RPC stall) surface to the member instead of being hidden.
- Operator productivity drops in the short term: many tools were
  built on the convenience of a shared HMAC secret; replacing them
  with per-member auth is more code, not less.

## Constitutional alignment

- Charter §1.6 (middleman elimination): direct.
- Charter §1.12 (Transparent Religious Force) — three-condition
  authorization (on-chain log + open-source + 1 SBT = 1 vote) is
  trivially satisfiable when no operator holds a force-multiplier
  key (ADR-2605192315).
- Charter §2(g) (no concentration of authority): direct.
- ADR-2605192300 (Bootstrap Council): the Council multisig becomes
  the *only* signing entity within etzhayyim's perimeter; this ADR
  amplifies that to "and the multisig only signs governance, not
  individual member actions".

# Alternatives Considered

1. **Status quo** — etzhayyim keeps server secrets, accepts the
   governance liability, mitigates with HSM and key rotation.
   Rejected: directly contradicts Charter §1.6; previous removals
   (Stripe / Clerk) already establish that "remove the secret" is
   the only durable mitigation.

2. **Council-multisig signs everything** — every Worker write would
   go through the 5-of-7 Safe. Rejected: ergonomically impossible
   for high-frequency events (donations, sessions) and concentrates
   authority in the Council, not in the member.

3. **Hardware security module + threshold signing** — store the key
   in HSM with t-of-n threshold scheme. Rejected: an HSM is still a
   single point that an adversary can subpoena from etzhayyim's
   operator; threshold across the Council does not change who is
   liable in court (and concentrates the right to sign in the
   Council, not the member).

4. **TEE / SGX enclave** — sign inside an attested enclave so the
   operator never sees the key. Rejected: trusted-hardware vendor
   becomes the new middleman; recent attacks (SGX side channels)
   show the trust posture is not durable.

5. **Per-app secret rotation** — keep the secrets but rotate weekly
   via the Council. Rejected: liability persists in every rotation
   window; does not eliminate the impersonation surface.

# References

## Related ADRs

- ADR-2605192100 (Mission Charter)
- ADR-2605192115 (No Advertising / No Purchase Purpose)
- ADR-2605192200 (Charter Compliance Rider v2.0)
- ADR-2605172000 (RW-free State Substrate)
- ADR-2605172100 (No Fiat Payment Processors)
- ADR-2605181100 (MST Encrypted Records — Signal KeyWrap)
- ADR-2605231400 (kotoba-datomic Holochain-Iso Substrate)
- ADR-2605231500 (kotoba-datomic-projection — Regenerable Cache Rules)
- ADR-2605192300 (Bootstrap Council)
- ADR-2605192315 (Transparent Religious Force)

## Artefacts shipped this PR (2026-05-23)

**Constitutional / SSoT updates**

- `CHARTER-RIDER.md` — Annex A: proposed §1.5 PLATFORM POSTURE amendment (Council 5-of-7 ratify pending)
- `CLAUDE.md` — substrate boundary table: new row "Server-side signing capability"
- `deps.toml` — `[platform.substrate]` `server_key_*` keys + 5 new `[[migrations]]` rows + 1 new `[[adrs]]` entry
- `70-tools/e7m/src/e7m/commands.py` — `_check_no_server_key` registered as 9th constitutional invariant

**Stage A — USDC signer removal (applied)**

- `60-apps/etzhayyim-project-yatabase/src/donate.ts` — verify-only handler
- `60-apps/etzhayyim-project-yatabase/svelte/src/lib/api.ts` — `donate.verify()`
- `60-apps/etzhayyim-project-yatabase/svelte/src/routes/studio/billing/+page.svelte` — EIP-1193 wallet flow
- `60-apps/etzhayyim-project-auth/worker/svelte/src/routes/sign-up/+page.svelte` — wallet flow on Telecom path
- `60-apps/etzhayyim-project-yatabase/wrangler.jsonc` — public-address env with `no-server-key: read-only` marker
- `60-apps/etzhayyim-project-yatabase/RUNBOOK-USDC-DONATE.md` — operator deploy runbook

**Stage B — Bulk-ingest community-operator handover (scaffold)**

- `60-apps/etzhayyim-project-maps/bulk-ingest/COMMUNITY-OPERATOR-HANDOVER.md`
- `60-apps/etzhayyim-project-maps/bulk-ingest/workers/_etzhayyim_substrate.py` (Stage 1 — already shipped)
- `60-apps/etzhayyim-project-maps/bulk-ingest/workers/kotoba-datomic-projection.edn` (already shipped)
- `_working/stage-b/community-repo-template/{README.md, NOTICE, .github/workflows/charter-compliance.yml}`
- `_working/stage-b/issue-templates/{13-pod-handover.md, 13-rows.csv}`

**Stage C — Identity-signing devolution (C-1 scaffold ready)**

- `50-infra/etzhayyim-did-web/did-multi-controller.json`
- `50-infra/etzhayyim-did-web/STAGE-C1-DID-CUTOVER.md`
- `50-infra/etzhayyim-did-web/cutover-stage-c1.sh`
- `60-apps/etzhayyim-project-auth/STAGE-C-IDENTITY-SIGNING-DEVOLUTION.md`
- `60-apps/etzhayyim-project-auth/kotoba-datomic-projection.edn` (already shipped, decl D1 as L0-rebuildable)
- `60-apps/etzhayyim-project-auth/worker/src-ts/substrate-mst-credential.ts` (already shipped, encrypted-MST seam)
- `00-contracts/lexicons/com/etzhayyim/auth/credential.json` (already shipped, inner-type lexicon)

**Stage D — External-API liability handover (scaffold)**

- `_working/STAGE-D-EXTERNAL-API-HANDOVER.md`

**Stage E — `e7m verify --no-server-key` invariant (wired)**

- `70-tools/e7m/src/e7m/commands.py` — `_check_no_server_key` + `_NO_SERVER_KEY_FORBIDDEN_ENV` list + `_NO_SERVER_KEY_EXEMPTION_MARKER`

## Related migration trails (pre-existing)

- Stripe → USDC closure: `60-apps/etzhayyim-project-yatabase/MIGRATION-TODO.md`
- Auth MST envelope Stage 1: `60-apps/etzhayyim-project-auth/MIGRATION-TODO.md`
- Maps substrate seam Stage 2 codemod: `60-apps/etzhayyim-project-maps/bulk-ingest/workers/MIGRATION-TODO.md`
