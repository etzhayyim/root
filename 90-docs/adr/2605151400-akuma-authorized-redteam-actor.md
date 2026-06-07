---
id: akuma-authorized-redteam-actor
title: Akuma — authorized red team actor with scope-gated probing
status: active
doc_type: adr
topic: authorized-redteam
authoritative: true
last_verified: 2026-05-15
authoritative_for:
  - authorized-redteam
  - red-team-scope-contract
  - probe-intrusiveness-tier
  - red-team-audit
related:
  - 0018-pii-tier3-cohort-first
  - adr-2605091800-pruning-protocol
  - adr-2605091400-mcp-as-cell-membrane-lexicon-xrpc-demotion
  - adr-2605131500-malak-surveillance-collapse-from-mehikari
supersedes: []
superseded_by: []
---

# Context

The platform has defensive security infrastructure (`yabai` risk scoring, `nist`
CSF mapping, `malak` cybercrime OSINT, `cybersec-web-vuln` reporting,
`threat-intelligence` IOC collection) but **no actor designed to perform
authorized active security testing** against permitted IPs and servers. When
threats appear in `_working/malak/THREAT-LEDGER.md` or in `yabai` IP risk
graph, there is no closed-loop: the platform records and scores, but cannot
itself probe a permitted target to confirm an exposure or verify that an
entry point has been closed.

External requests to "perform authorized red team probing of permitted IPs
and servers" therefore have no canonical home, no scope contract, no
authorization gate, and no audit substrate. Without an explicit ADR,
ad-hoc tooling would either (a) be wired into an existing actor and erode
its defensive identity, or (b) bypass the authority chain entirely.

# Decision

Introduce a new actor `akuma` (悪魔) at `did:web:akuma.etzhayyim.com`,
nanoid `ak0m4r3d`, `performer_type = service`, governed by etzhayyim
under the standard operating-entity boundary (CLAUDE.md root rule).

Akuma's only purpose is **scope-bound, authorized active security testing**
of targets that have been explicitly registered, attested by their owner,
and approved by etzhayyim authority. It is not a generic offensive
tool. It cannot operate on a target that is not in its scope graph.

## Scope contract (cytoplasmic)

Each engagement is a graph object:

- `vertex_akuma_scope` — owner-attested target set
  - `target_kind`: `ip` | `cidr` | `hostname` | `url`
  - `targets[]`: explicit IPs / CIDRs / hostnames (no wildcards beyond CIDR)
  - `allowed_ports[]`: explicit ports (default = empty = no probing)
  - `allowed_paths[]`: for `url` kind, explicit path prefixes
  - `intrusiveness_tier`: `passive` | `safe-active` | `intrusive` (see below)
  - `owner_did`: target owner DID (ERC725 / did:web / did:plc)
  - `owner_signature`: detached signature over the scope payload
  - `authority_did`: etzhayyim approver DID
  - `authority_signature`: detached signature over the same payload
  - `valid_from`, `valid_until`: ISO timestamps; default window = 14 days
  - `legal_basis`: free-text reference (SOW id, contract clause, CTF rules,
    bug bounty program URL, written authorization document CID)
  - `excluded_targets[]`: targets that MUST be skipped even if covered by CIDR
  - `rate_limit_rps`: max requests per second per target
  - `revoked`: boolean; revocation is one-way and immediate

A scope is valid only if:

1. `owner_signature` verifies against `owner_did`
2. `authority_signature` verifies against `authority_did` ∈ etzhayyim
   authority chain
3. `valid_from <= now < valid_until`
4. `revoked == false`

## Intrusiveness tiers

| tier | examples | requires |
|---|---|---|
| `passive` | DNS / WHOIS / TLS cert chain / passive ASN lookups | scope only |
| `safe-active` | TCP connect, banner grab, HTTP HEAD, nuclei `-severity info,low`, robots.txt fetch | scope + owner signature + authority signature |
| `intrusive` | nmap `-A`, nuclei mid/high, sqlmap, ZAP active scan, dirbuster | scope + owner signature + authority signature + per-engagement DMN approval row |

Above `intrusive` (exploit weaponization, RCE proof, lateral movement,
DoS) is **out of scope for akuma** and rejected at policy. Such work must
be performed under a separate human-driven engagement, not by an autonomous
actor.

## Topology

Akuma follows the platform's standard runtime topology:

- **Edge**: SvelteKit CF Worker proxy at `akuma.etzhayyim.com` (no business logic;
  CF Worker = edge only per ADR-2605111200)
- **Runtime**: K8s LangServer pod (Granian L3) under namespace
  `akuma-langserver` invoked via AgentGateway MCP
- **Probe execution**: dedicated egress-restricted K8s namespace
  `akuma-probe` with NetworkPolicy that allows egress only to IPs
  resolved from currently-active scope contracts. The probe pod has no
  cluster-internal egress and no DNS to internal services.
- **External MCP surface**: only `magatama` MCP facade exposes akuma to
  external principals (per ADR-2605091400 cytoplasmic demotion). Direct
  XRPC exposure to external callers is prohibited.
- **Persistence**: append-only `vertex_akuma_*` rows; no soft delete; raw
  finding payloads ciphertext-stored in `vault.etzhayyim.com` (zero-knowledge
  invariant maintained — server holds ciphertext + wrapped keys + metadata
  only)

## Live state (2026-05-15)

The actor is active and ADR-bound. The deployed baseline is:

- RW data plane: `vertex_akuma_scope`, audit, finding, and related edge
  tables are present and were exercised by a smoke round-trip.
- Lexicon/PDS surface: `com.etzhayyim.apps.akuma.*` contract files exist and are
  registered as the protocol surface.
- Policy: `etzhayyim.akuma.scope` is the authorization SSoT; unit coverage
  passed 11/11 for allowed, denied, and tier-bound probe attempts.
- Runtime isolation: probe execution is bound to the `akuma-probe`
  namespace, not `default`, with reconciled egress derived from active
  scope contracts.
- Authority key: the etzhayyim authority signing key was generated;
  human publication to `https://akuma.etzhayyim.com/.well-known/did.json` and
  1Password mirroring remain operational handoff tasks.

Control-plane work remains open and is tracked in `deps.toml`:

- bind the XRPC handlers for register/approve/revoke/run/record/close/query
- bump the reconciler image and probe-runner image through the deployment
  path
- publish the authority verification method in the DID document
- mirror the keychain entries to the shared 1Password vault

## XRPC surface (cytoplasmic only)

NSID prefix `com.etzhayyim.apps.akuma.*`:

- `registerScope` (procedure) — append a draft scope; status = `draft`
- `approveScope` (procedure) — owner + authority signatures; status →
  `active`
- `revokeScope` (procedure) — one-way; status → `revoked`
- `runProbe` (procedure) — execute a probe against an active scope;
  policy-gated against scope tier and target allowlist
- `recordFinding` (procedure) — append finding produced by a probe
- `closeFinding` (procedure) — owner attests remediation; status →
  `closed`; akuma re-runs the same probe to verify
- `getScope` (query)
- `listFindings` (query)

## Authorization gate

A new Rego module `etzhayyim.akuma.scope` evaluates `runProbe`. Inputs:

- `input.scope` — fetched scope contract row
- `input.probe.tool` — `dns` | `whois` | `tls` | `http-head` | `nmap` |
  `nuclei` | `zap` | `sqlmap`
- `input.probe.target` — single target string
- `input.probe.intrusiveness` — declared tier of this single probe call
- `input.now` — request timestamp

Decision rules (see `00-contracts/policies/etzhayyim/akuma/scope/policy.rego`):

1. `deny` if scope status != `active`
2. `deny` if `now` outside `[valid_from, valid_until)`
3. `deny` if `target` not in `targets[]` and not within any `cidr` in
   `targets[]`
4. `deny` if `target` in `excluded_targets[]`
5. `deny` if `probe.intrusiveness` > `scope.intrusiveness_tier`
6. `deny` if `probe.tool` not in tier-allowed tool set
7. `deny` if rate budget for `target` in current second exceeded
   `rate_limit_rps`
8. `allow` otherwise

Every `deny` produces an audit row in `vertex_akuma_audit` with
`reason` and `obligations: ["return_403", "audit_authz_denied"]`.
Every `allow` is also audited with the resolved obligations (e.g.,
`record_probe_attempt`, `bind_to_finding`).

## Closed-loop with yabai / malak / threat ledger

- A `yabai` risk score above `Challenge` threshold (≥85) on an IP entity
  in the akuma scope graph triggers a `runProbe` cron candidate (passive
  tier only by default)
- A `_working/malak/THREAT-LEDGER.md` entry that names a target whose
  owner has signed a scope contract triggers a `runProbe` candidate
  (tier capped by the scope contract)
- Findings flow back as `yabai` evidence rows
  (`category: VulnFinding`, weight to be added in a follow-up ADR)

## Pruning

Akuma is subject to the Bonsai pruning protocol (ADR-2605091800):

- Unauthorized probe attempt → `seed` tier prune (full actor freeze +
  human review). One unauthorized attempt removes akuma from the loop
  until reinstated.
- Out-of-scope probe blocked at policy → `branch` tier prune (revoke
  the offending scope contract; akuma continues for other scopes).
- Repeated rate-limit violation → `leaf` tier prune of the offending
  probe step.

# Consequences

- The platform gains a single canonical home for authorized active
  security testing, with scope contracts, dual signatures, intrusiveness
  tiering, and append-only audit
- Threat-ledger and yabai risk signals can close their loop by verifying
  exposure on owner-attested targets, instead of stopping at "scored"
- Akuma's egress-restricted namespace + scope-resolved NetworkPolicy
  ensures that even if akuma is compromised, it cannot reach targets
  outside currently-active scopes
- The intrusiveness ceiling (no exploit weaponization, no RCE, no DoS)
  keeps akuma inside an "autonomous-safe" envelope and pushes higher-risk
  work into human-driven engagements
- Adds maintenance: scope contract lifecycle, signature verification,
  rate budget tracking, NetworkPolicy reconciliation against active
  scopes
- New attack surface: a forged authority signature would let akuma probe
  arbitrary targets. Mitigation: authority signing key lives in the
  etzhayyim HSM path documented under "Local Secret Storage" /
  "Credential Sharing" CRITICAL rules; signature verification is offline
  and audited

# Alternatives Considered

- **Extend `yabai` with active probing**: rejected because it conflates
  defensive scoring with offensive probing and breaks `yabai`'s identity
  as a risk-intelligence actor. Compromise of an active-probing yabai
  would also burn the defensive identity.
- **Use a generic offensive framework (Metasploit / C2)**: rejected.
  Akuma's ceiling is intentional; weaponization belongs to human
  engagements with their own audit chain.
- **Per-target one-shot scripts**: rejected because there is no scope
  contract, no signature chain, no audit graph, and no closed loop with
  the threat ledger.
- **Skip the actor; rely on external pentesters**: viable but does not
  address the threat-ledger closed-loop need; akuma is additive and
  does not replace external engagements.

# Deployment Record

Initial deployment 2026-05-15 (operator: jun@etzhayyim.com on macOS Mac).
This section is the post-deployment companion to "Live state" above and
records the concrete artifact state. It supersedes any earlier
"production_live_pending" framing.

## Live artifacts

| Layer | Artifact | State |
|---|---|---|
| Authority key | Ed25519 keypair in macOS Keychain `etzhayyim.akuma`; fingerprint `46a0a86b9a8fd180`; public hex `726c7daa...0915` | sign+verify roundtrip OK |
| Kotoba/Datomic tables | `vertex_akuma_{scope,probe,finding,audit}` + 5 indexes on RW Vultr `45.32.79.245` | applied via psycopg2 phased per CLAUDE.md multi-head workaround; revision file `r_20260515150000_vertex_akuma_redteam_scope.py` in `alembic/current_versions/` |
| K8s namespace | `akuma-probe` with default-deny + DNS + langserver-callback NetworkPolicies + RBAC + ServiceAccount `probe-runner` | `kubectl apply -k 50-infra/k8s/akuma-langserver/` succeeded |
| K8s reconciler | `scope-egress-reconciler` CronJob (`* * * * *`) targeting `akuma-probe-scope-allow` NetworkPolicy | applied; **Errors with ModuleNotFoundError** because `pymagatama:latest` predates `pymagatama.akuma` module |
| K8s langserver | `akuma-langserver` Deployment + Service in `mitama-udf` ns | Running 1/1 |
| K8s secrets | `akuma-authority-key` (PUBLIC only) in `mitama-udf`; `akuma-rw-readonly` (KAISYA URL) in `akuma-probe` | created |
| PDS lexicons | 8 NSIDs `com.etzhayyim.apps.akuma.*` live at `atproto.etzhayyim.com` (Worker version `fdfc4c61-ce87-40fd-adaf-7f9e85522359`) | wrangler deploy 2026-05-15; HTTP 401 (auth required), not 404 |
| Rego policy | `etzhayyim.akuma.scope` package | 11/11 unit tests PASS |
| Reconciler module | `pymagatama.akuma.scope_egress_reconciler` | source landed in repo, NOT yet baked into a published `pymagatama` image |
| Smoke test | data plane round-trip (INSERT scope → sign+verify → reconciler SELECT → 5 policy decisions → INSERT audit + finding → count → hard delete) | all 9 steps PASS |

## Remaining human steps

1. Publish `AUTHORITY_SIGNING_KEY_PUBLIC` (`726c7daa...0915`) at
   `https://akuma.etzhayyim.com/.well-known/did.json` `verificationMethod`
   (`Ed25519VerificationKey2020`) so external owners can verify
   `authority_signature` on scope contracts.
2. Mirror Keychain `etzhayyim.akuma` entries to 1Password vault
   `etzhayyim Japan株式会社` per the `op item create` command printed by
   `provision-authority-key.sh`.
3. Rebuild `ghcr.io/etzhayyim/pymagatama` image with the new
   `pymagatama.akuma` module included and bump
   `scope-egress-reconciler` CronJob image tag. Until then the
   reconciler stays in CrashLoopBackoff and `akuma-probe-scope-allow`
   stays empty (probe pods would have no egress allow rules anyway).
4. Implement XRPC handlers for `com.etzhayyim.apps.akuma.{registerScope,
   approveScope, revokeScope, runProbe, recordFinding, closeFinding,
   getScope, listFindings}`. Currently the PDS routes the NSIDs
   (HTTP 401, not 404) but no actor has registered handler bindings
   yet, so calls would dead-end.
5. Build and deploy a `probe-runner` image carrying `nuclei`, `nmap`,
   `zap`, `sqlmap` binaries, scheduled into `akuma-probe` namespace
   under `role=probe-runner` label. Until then `runProbe` would be
   allowed by Rego but would have no executor on the other side of the
   NetworkPolicy.

After step 5, the first end-to-end production test should be
performed against a benign owned target (CTF host, internal lab IP)
before any external scope contract is approved.

# References

- `00-contracts/lexicons/com/etzhayyim/apps/akuma/*.json`
- `00-contracts/policies/etzhayyim/akuma/scope/policy.rego`
- `00-contracts/policies/etzhayyim/akuma/scope/test.rego`
- `20-actors/akuma/actor-manifest.jsonld`
- `20-actors/akuma/CLAUDE.md`
- `20-actors/magatama/py/src/pymagatama/akuma/scope_egress_reconciler.py`
- `30-graph/graph-schema/alembic/current_versions/r_20260515150000_vertex_akuma_redteam_scope.py`
- `30-graph/graph-schema/sql_migrations/20260515150000_vertex_akuma_redteam_scope.up.sql`
- `50-infra/k8s/akuma-langserver/`
- `70-tools/scripts/akuma/provision-authority-key.sh`
- `70-tools/scripts/akuma/load-authority-key.sh`
- ADR-0018 PII Tier 3 + Cohort-First
- ADR-2605091400 MCP-as-Cell-Membrane (Lexicon/XRPC Demotion)
- ADR-2605091800 Pruning Protocol
- ADR-2605111200 CF Worker = Edge-Only
- ADR-2605131500 Malak Surveillance Collapse from Mehikari
- CLAUDE.md root rule "Operating Entity Boundary"
- CLAUDE.md root rule "Vault Zero-Knowledge Invariant"
