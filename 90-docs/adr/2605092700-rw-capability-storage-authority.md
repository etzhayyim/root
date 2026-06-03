---
id: adr-2605092700-rw-capability-storage-authority
title: "RisingWave Capability Storage and Authority Boundary"
status: accepted
doc_type: adr
topic: rw-capability-storage-authority
authoritative: true
last_verified: 2026-05-09
authoritative_for:
  - RisingWave capability storage target design
  - DID-bound authority evaluation over RW writes and reads
  - Tahoe-like read/write/verify capability mapping for etzhayyim storage
  - auth.etzhayyim.com / DID / ERC725 alignment for capability checks
priority: 9.1
axis: security
weight: 0.91
depends_on:
  - adr-2605091400-mcp-as-cell-membrane-lexicon-xrpc-demotion
  - adr-2605080700-graph-schema-live-risingwave-baseline
  - adr-2604231800-atproto-permission-spec-integration
related:
  - 90-docs/dt/260324-dt-secure-file-transfer-design.md
  - 10-protocol/signal/src/signal.ts
  - 30-graph/deps.toml
  - doc-260424-oauth-strict-mode-cutover
  - adr-2604262100-erc725-erc8004-k8s-ipfs-agent-runtime
  - 50-infra/vultr/geth-private/contracts/ADDRESSES.md
supersedes: []
superseded_by: []
---

# Context

Current RisingWave (RW) is the canonical queryable graph/projection store for
`com.etzhayyim.apps.*` domain rows. It is not an end-to-end encrypted database and not
a Tahoe-LAFS style capability store. Private fields may use the `signal:v1:`
field convention, and Tenso stores encrypted file manifests/blobs, but RW still
contains plaintext graph metadata and application rows.

The target is to support **capability storage** and **authority** without turning
RW into a bearer-secret database:

- RW remains the queryable graph and materialized-view engine.
- RW stores no plaintext protected object content and no bearer capability
  secret.
- RW stores capability hashes, verify-cap indexes, grant facts, delegation
  chains, caveats, revocation state, and audit rows.
- Read/write authority is enforced at the MCP/Worker gateway before any RW read
  or write that touches protected storage.

# Decision

## Compatibility Position

This design is compatible with the current `auth.etzhayyim.com`, DID, and ERC725
architecture only under these constraints:

- `auth.etzhayyim.com` remains the session issuer and proof-of-possession boundary.
  Capability checks consume auth context from OAuth/DPoP-bound sessions; they do
  not mint independent login sessions.
- The canonical authority key is the ERC725 root DID:
  `did:erc725:etzhayyim:260425:<identity>`.
- `did:web` / `did:plc` values are facade/profile/federation DIDs. They may be
  accepted as input, but must be resolved to the ERC725 root before capability
  evaluation.
- ERC725 / ERC-8004 remain the public trust and discovery anchors. RW stores
  operational projections and hashes; it does not replace the onchain root
  identity registry.
- DID `capabilityInvocation` / `assertionMethod` keys are used to verify
  grant/delegation/revocation signatures where the signer is not an EVM account.
  EVM contract/account signers use ERC-1271/EOA verification against the root
  identity binding.

## A. Storage Model

Protected objects are split into two planes.

```
Client / agent
  owns read/write/admin cap secret + encryption keys
  encrypts payload before upload
        |
        v
Blob plane: B2 / object storage
  encrypted chunks only
  addressed by content hash / storage locator
        |
        v
RW graph plane
  verify indexes, encrypted manifests, capability grants, caveats, revocations
  no DEK, no bearer cap, no protected plaintext
```

RW may store public metadata needed for routing and analytics. Any field that
would reveal protected content or policy-sensitive detail must be one of:

- `signal:v1:{ciphertext}` field value,
- encrypted manifest blob reference,
- blinded index token with documented leakage,
- content hash / verify hash that is not sufficient to decrypt.

## B. Capability Types

Use Tahoe-like semantics, but bind them to DID authority and MCP calls.

| Capability | Holder Can | RW Stores | Holder Keeps |
|---|---|---|---|
| `verify` | prove object identity/integrity, locate metadata | object id, content hash, verify hash | optional verify cap URI |
| `read` | fetch encrypted chunks and decrypt manifest/content | `cap_hash`, grant facts, encrypted recipient wrap | read secret, DEK unwrap material |
| `write` | create/append/mutate object under policy | write `cap_hash`, caveats, delegation edge | write secret or signing key |
| `admin` | delegate, revoke, rotate keys, alter policy | admin grant hash, revocation lineage | admin secret/signing key |

The bearer capability URI is never stored raw in RW. The proposed URI shape is:

```text
etzhayyim-cap:v1:rw:<cap-type>:<object-id>:<secret-or-proof>
```

RW stores only:

```text
cap_id        = stable public grant id
cap_hash      = BLAKE3/HKDF hash of canonical cap URI or proof material
object_id     = protected object vertex id
cap_type      = verify | read | write | admin
issuer_root_did  = ERC725 root DID of grant issuer
subject_root_did = ERC725 root DID of intended holder, org, or agent
issuer_facade_did  = optional did:web / did:plc input/display DID
subject_facade_did = optional did:web / did:plc input/display DID
caveats_json  = scope, method, row/table, TTL, max uses, IP/device constraints
revoked_at    = null unless revoked
```

## C. Authority Boundary

RW is not the enforcement boundary for external principals. The enforcement
boundary is:

```
external principal
  -> MCP facade
  -> auth.etzhayyim.com OAuth/DPoP validation
  -> facade DID to ERC725 root DID resolution
  -> capability verifier / authority evaluator
  -> internal XRPC or Worker handler
  -> Kysely/Hyperdrive/RW
```

Direct external XRPC and direct external SQL are prohibited. Application Workers
must not perform protected reads or writes by table access alone; they must call
the capability verifier for the operation being attempted.

This means:

- MCP tool call includes DID-bound authentication plus capability proof.
- The presented token is validated as an `auth.etzhayyim.com` issued OAuth access
  token, including DPoP `cnf.jkt` proof-of-possession where applicable.
- The caller's facade DID is normalized through `etzhayyimRootIdentityRegistry` or
  the RW projection of it before matching any grant.
- Gateway hashes/verifies the supplied capability without persisting the secret.
- Gateway checks grant, caveats, delegation, expiry, revocation, and object state
  from RW materialized views.
- Only then does it issue the RW query/write.

Root/operator SQL remains break-glass infrastructure authority, not application
authority. Production app credentials should be scoped so protected tables are
only reachable through the gateway path.

## D. Proposed RW Schema Additions

The exact Alembic migration can be staged later. Target logical relations:

```sql
vertex_cap_object (
  vertex_id text primary key,
  object_id text not null,
  object_kind text not null,
  owner_did text not null,
  storage_locator text,
  verify_hash text not null,
  manifest_cipher text,
  public_metadata_json jsonb,
  created_at timestamptz not null,
  status text not null
);

vertex_cap_grant (
  vertex_id text primary key,
  cap_id text not null,
  object_id text not null,
  cap_type text not null,
  cap_hash text not null,
  issuer_root_did text not null,
  subject_root_did text not null,
  issuer_facade_did text,
  subject_facade_did text,
  issuer_erc725_address text,
  subject_erc725_address text,
  caveats_json jsonb not null,
  wrapped_cap_cipher text,
  created_at timestamptz not null,
  expires_at timestamptz,
  revoked_at timestamptz,
  status text not null
);

edge_cap_delegates (
  vertex_id text primary key,
  parent_cap_id text not null,
  child_cap_id text not null,
  issuer_root_did text not null,
  subject_root_did text not null,
  caveats_json jsonb not null,
  signature_scheme text not null,
  signature text not null,
  created_at timestamptz not null,
  revoked_at timestamptz
);

vertex_cap_revocation (
  vertex_id text primary key,
  cap_id text not null,
  object_id text not null,
  revoked_by_root_did text not null,
  reason text,
  signature_scheme text not null,
  signature text not null,
  created_at timestamptz not null
);

vertex_cap_audit (
  vertex_id text primary key,
  cap_id text,
  object_id text,
  actor_root_did text not null,
  actor_facade_did text,
  operation text not null,
  decision text not null,
  decision_reason text,
  request_hash text,
  created_at timestamptz not null
);
```

Derived materialized views:

- `mv_cap_effective_grant`: current non-revoked, non-expired grants.
- `mv_cap_subject_authority`: flattened subject/object/operation authority.
- `mv_cap_object_visibility`: object rows visible to a DID/org/agent cohort.
- `mv_cap_revocation_closure`: parent revocation invalidates delegated children.

## E. Write Path

1. Client creates content locally and derives a per-object DEK.
2. Client encrypts payload/chunks before upload.
3. Client generates object id, verify hash, read cap, write cap, optional admin
   cap.
4. Client wraps read/admin material to recipient DID(s) using Signal/X25519.
5. Client calls MCP `cap.object.create` or domain-specific wrapper with an
   `auth.etzhayyim.com` OAuth/DPoP session.
6. Gateway resolves caller and recipients to ERC725 root DID(s).
7. Gateway verifies caller identity and write/admin authority.
8. Gateway inserts object/grant/audit rows into RW.

No handler accepts caller-provided protected plaintext for storage unless the
field is explicitly public.

## F. Read Path

1. Caller invokes MCP tool with `auth.etzhayyim.com` DID auth and read cap proof.
2. Gateway validates OAuth/DPoP and resolves facade DID to ERC725 root DID.
3. Gateway computes `cap_hash` and looks up effective grant in RW.
4. Gateway evaluates caveats: subject, object, method, TTL, max use, device,
   org, sensitivity, and revocation closure.
5. Gateway returns encrypted manifest / chunk locators / wrapped key material.
6. Caller decrypts locally.

RW and the gateway may learn access metadata. They must not learn content keys
or protected plaintext.

## G. Authority Semantics

Authority is DID-bound and explicit:

- `issuer_root_did` signs or authorizes grants/delegations/revocations.
- `subject_root_did` names the recipient principal, org, device, agent, or
  cohort after facade resolution.
- `issuer_facade_did` / `subject_facade_did` are display and federation inputs,
  never the canonical authority key.
- `cap_type` limits operation class.
- `caveats_json` narrows table, collection, object prefix, time, method, and
  sensitivity.
- Revocation is append-only; materialized views compute current state.

Signature verification order:

1. Resolve `did:web` / `did:plc` / `did:etzhayyim` input to ERC725 root DID.
2. Resolve ERC725 root to identity contract via `etzhayyimRootIdentityRegistry`.
3. If signer is a contract/smart account, verify via ERC-1271.
4. If signer is an EOA, verify ECDSA and root identity binding.
5. If signer is a DID key, verify through DID Document `capabilityInvocation`.

Authority precedence:

1. Revocation wins.
2. Expiry wins.
3. Narrower caveat wins over broader delegation.
4. Admin cap can delegate/revoke within its caveats.
5. Write cap can mutate object content/state within its caveats.
6. Read cap cannot delegate unless explicitly caveated with `may_delegate`.

## H. Query Privacy

Encrypted rows are not magically queryable. Supported patterns:

- public metadata queries,
- verify-hash lookups,
- blinded equality tokens for explicitly approved fields,
- client-side filtering after encrypted manifest fetch,
- derived analytics only over approved public or declassified fields.

Range search, full-text search, and joins over protected content require either
plaintext/public projection, trusted execution, or purpose-built encrypted index
with a written leakage profile.

# Migration Plan

1. Mark protected tables/columns with a schema annotation:
   `protection = public | private_field | cap_object | cap_grant`.
2. Add capability schema relations and MVs via Alembic after RW health gate.
3. Implement `cap.verify`, `cap.grant`, `cap.revoke`, `cap.audit` in the MCP
   facade.
4. Move Tenso manifest/access-control through `vertex_cap_object` and
   `vertex_cap_grant` first.
5. Add lint guard: protected table writes must go through capability gateway.
6. Add drift/audit job: sample protected columns for plaintext violations.
7. Gradually migrate vault/messaging/private domain rows.

# Non-Goals

- RW does not become a decentralized erasure-coded storage network.
- RW does not hold raw Tahoe-style bearer caps.
- RW does not provide cryptographic privacy for SQL query patterns.
- Direct operator SQL is not removed; it is classified as break-glass infra
  authority and audited separately.

# Acceptance Criteria

- A protected object can be read only with DID auth plus a matching read cap.
- A write without effective write/admin authority is rejected before RW mutation.
- RW contains no raw read/write/admin cap secret.
- RW contains no protected plaintext for migrated object classes.
- Revoking an admin/read/write cap invalidates delegated descendants in the
  effective authority MV.
- Tenso file manifests and access-control state can be represented by the new
  object/grant model without losing current behavior.

# Reversibility

Partially reversible. The schema can coexist with current domain tables, and
apps can migrate one object class at a time. Once clients depend on cap URIs and
encrypted manifests, returning to plaintext RW rows would require explicit data
reclassification and client changes.
