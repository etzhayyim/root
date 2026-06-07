# kotoba account-publish activation (ADR-2606061800 follow-on, (c))

Same-origin login/signup is **live** (apex Worker + yoro SPA, no authn/mcp). This
directory holds the remaining piece to make **member account publish** to the
kotoba Datom log work — proven end-to-end against a real node, gated only on an
operator-side deploy.

## What was proven

A fresh member `did:key`, with a self-signed CACAO, authorizes a write to the
kotoba `kotobase-kg-v1` graph via the **existing** `kg.ingest` endpoint —
`HTTP 200 {"ok":true, quadCount:6}` (no operator credential, no server key).

The only code change needed in kotoba is `0001-cacao-self-resolve-did-key.patch`.

## The kotoba fix (`0001-cacao-self-resolve-did-key.patch`)

`crates/kotoba-auth/src/cacao.rs :: verify_with_resolver` resolved **every**
EdDSA issuer via the DID resolver. For a fresh member `did:key` (no published DID
document) that forces an IPNS/IPFS DID-doc fetch that **hangs** (the doc does not
exist) → `did resolver error: DID document fetch failed for ipns://…`. A
`did:key` is self-certifying (the Ed25519 key is in the identifier), so it must
be verified via the embedded key. The patch short-circuits `did:key:` issuers to
`verify_signature()` (which `did:web`/`did:plc` still resolve). ~9 lines.

Verified: with the patch, an isolated build authorized the member account write
(`ok:true`); without it the same request hangs on IPNS resolution.

## Proven wire-format for the member account-publish CACAO

Build + sign on the **frontend** (no server key), forward to `kg.ingest`:

- `iss`  = member controller `did:key:z6Mk…` (standard base58 multibase)
- `aud`  = the kotoba node's `operator_did` — **must match exactly**. The running
  node's identity is keychain-persisted (`ephemeral=false`); currently
  `did:key:ze2e169933f9bcc6cb218e083b3d2a80c5a5a2b92fbf3cb41b4d5283ce3f6939f`.
  (Read it from the node's startup log `node identity + roles initialised did=…`.)
- `resources` = `["kotoba://op/datom:transact"]` (capability is required; **no**
  `kotoba://graph/…` and **no** `kotoba://tx/…` needed — both scope checks are
  optional and pass when absent).
- timestamps `iat`/`exp` = **second precision** `YYYY-MM-DDTHH:MM:SSZ` — kotoba's
  delegation check rejects millisecond precision (stricter than the apex verifier).
- signature `s.s` = **base64url, no padding** of the 64 raw Ed25519 bytes (kotoba
  tries base64url first; hex is mis-decoded as base64).
- encode the whole `Cacao {h,p,s}` as **CBOR (ciborium)** → base64 → `cacaoB64`
  (camelCase — `KgIngestReq` is `rename_all="camelCase"`).
- ingest body: `{ id: "account.<member-did>", type: "account",
  claims: [{pred:"account/did",value:did},{pred:"account/handle",value:handle},
  {pred:"account/controller",value:did}], cacaoB64 }`.

(A complete, working reference implementation of this exact request lives in the
session transcript — the `:8078` isolated-node proof.)

## Remaining wiring (small, de-risked)

1. **Worker** (`50-infra/etzhayyim-did-web`): change `putKotobaAccount` /
   `handleRegisterAccount` to forward the member's JSON CACAO → CBOR(ciborium)
   → base64 → POST `kg.ingest` (as above) when `KOTOBA_WRITE_ENDPOINT` is set.
   Worker already has `cid.ts` if a graph CID is ever needed. The Worker holds no
   key — it only re-encodes and relays the member-signed CACAO (NSK preserved).
2. **Frontend** (`same-origin-auth.ts`): build the kotoba-write CACAO with the
   fields above (note: a **second** CACAO, distinct from the apex login CACAO —
   different `aud` + base64url sig + second-precision timestamps).
3. **Config**: set `KOTOBA_WRITE_ENDPOINT` + `KOTOBA_OPERATOR_DID` on the apex
   Worker (`wrangler.toml [vars]`).

## Operator-gated deploy steps

1. **Deploy the kotoba fix**: apply `0001-cacao-self-resolve-did-key.patch` to the
   kotoba submodule, `cargo build --release -p kotoba-server`, swap
   `~/.local/bin/kotoba-server`, restart `com.etzhayyim.kotoba` (launchctl
   bootout/bootstrap). The node identity is keychain-persisted, so `operator_did`
   is unchanged across the restart.
2. **Open a Worker→node write path**: `kotoba.etzhayyim.com` is `403`/Access-gated
   at the edge, so the apex Worker currently has no route to POST writes. Add an
   Access bypass for `/xrpc/com.etzhayyim.apps.kotobase.kg.ingest`, or a service
   binding, then point `KOTOBA_WRITE_ENDPOINT` at it.

Until both land, `registerAccount` honestly returns `gated` (202) and login/signup
work without it (the `did:key` is the identity).
