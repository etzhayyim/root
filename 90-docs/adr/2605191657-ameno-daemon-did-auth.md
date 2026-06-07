---
id: 2605191657-ameno-daemon-did-auth
title: Ameno daemon — did:key Ed25519 challenge-response auth
status: proposed
doc_type: adr
topic: ameno-auth
authoritative: true
last_verified: 2026-05-19
depends_on:
  - 2605191407-ameno-browser-viewer-mode
  - 2605191229-ameno-daemon-path-a-bun-langgraph
  - 2605191257-ameno-daemon-path-b-kotodama-python
related:
V05191135-ameno-tier2-daemon-residency
---

# ADR 2605191657: Ameno daemon — did:key Ed25519 challenge-response auth

## Context

ADR-2605191407 / ameno-ingress(2026-05-19)で **bearer token** に
よる daemon 認証を入れた。これは v0.1 として localhost / 単一
オペレータ用途で十分だが、 multi-user / 公開 deploy には弱い:

- token が 1 つ — rotation = 全 browser session 切断
- 漏洩しても誰が漏らしたか分からない
- per-actor identity を表現できない

ADR-2605191135 が worker DID(`did:web:browser:…`)を確立しており、
worker 単位の signed challenge-response 認証への upgrade は自然な
次ステップ。

## Decision

**`did:key` Ed25519 を使ったシンプルな nonce challenge-response を
導入。 bearer token は legacy として残し、両方サポート。**

### Wire format

```
GET  /auth/nonce
  → 200 { "nonce_id": "<8 bytes b64url>",
          "nonce":    "<16 bytes b64url>",
          "expires_at_ms": <epoch ms, +60_000> }

POST /threads/:tid/stream    (or any auth-required endpoint)
  Authorization: DIDSig did:key:z<base58btc>:<nonce_id>:<sig_b64url>
  ...

  daemon:
    look up nonce_id → entry
      not found → 401 "nonce unknown or already consumed"
      used     → 401 "nonce already consumed"
      expired  → 401 "nonce expired"
    decode did:key → 32-byte Ed25519 pubkey
    Ed25519.verify(sig, Encode(`${nonce_id}.${nonce}`), pubkey)
    → ok: mark used + proceed
    → fail: 401 "signature verification failed"
```

### did:key encoding

- 32 byte Ed25519 public key
- prefixed with multicodec `0xed 0x01` (Ed25519-pub)
- base58btc encoded
- prepended with multibase `z`
- final form: `did:key:z<base58btc(0xed01 || pubkey)>`

This is self-resolving — no did:web / did:plc lookup needed.
Verifiers only need a base58 decoder + the raw Ed25519 verify
primitive.

### Browser side

- `svelte/src/lib/did-auth.ts` generates the keypair on first call
  (`@noble/curves` Ed25519), persists JWK-ish in localStorage as
  `ameno.did-auth.keypair.v1`. DID is self-describing.
- `buildDidSigHeader(baseUrl)` fetches a fresh nonce, signs it, returns
  the `DIDSig …` header string.
- `viewer-mode.ts` consumes the header builder — bearer token remains
  as a fallback when DID auth isn't enabled or when the daemon is
  loopback-only.

### Daemon side (TS Path A)

- `daemon/src/did-auth.ts` exposes `issueNonce()` + `verifyDidSig()`.
- `server.ts` middleware accepts:
  1. `Authorization: DIDSig …` — verify + single-use consume
  2. `Authorization: Bearer …` — legacy match
  3. neither + `AMENO_AUTH_TOKEN` unset — loopback dev pass-through
- `GET /auth/nonce` is exempt from auth (it IS the bootstrap).

### Daemon side (Python Path B)

- `kotodama/projects/ameno/did_auth.py` mirrors the TS module.
- Pure-Python base58btc decode, `cryptography.Ed25519PublicKey` for
  verify (lazy-imported so hosts without `cryptography` installed
  fail loudly only when DID auth is actually used).
- FastAPI middleware in `server.py` follows the same accept-order.

### Header parsing rule

`DIDSig <did:key>:<nonce_id>:<sig>` — split on the **last two `:`**
(`lastIndexOf`). This is robust even though `did:key:z…` itself
contains `:` characters.

### Threat model (v0.1 scope)

- ✅ nonce single-use, 60s TTL → replay-safe within window
- ✅ Ed25519 keypair never leaves the browser (localStorage)
- ⚠️ key is exfiltrable by any same-origin XSS → mitigated by COEP
  `credentialless` + CSP rules, but XSS = compromise. Acceptable for
  single-operator deployments
- ⚠️ no key rotation cadence prescribed → manual via `rotateAuthKey()`
- ❌ not yet integrated with `com.etzhayyim.identity.signalIdentity`
  (Signal Protocol DID binding, ADR-2605181100). Future composition

### Compatibility / migration

| state | daemon accepts |
|---|---|
| `AMENO_AUTH_TOKEN` unset(localhost dev)| both DIDSig and "no auth"; if a DIDSig is present and invalid → 401 |
| `AMENO_AUTH_TOKEN` set, no DIDSig | Bearer required |
| `AMENO_AUTH_TOKEN` set, DIDSig present | DIDSig verified — Bearer not required when DIDSig valid |

This keeps `ameno-ingress` deployments(ADR-2605191407 + bearer secret)
working unchanged while letting browser clients opt into DID auth.

## Consequences

- ameno daemon が **per-actor 認証** をサポート開始。public deploy
  の道筋が立つ
- browser localStorage の keypair → user gesture なしで永続。private
  browsing では tab 終了で失われる(意図通り)
- 既存 bearer 経路は維持 — `kubectl` operator / curl テストの摩擦ゼロ
- `did:key` は self-describing、外部 resolver 不要。daemon に
  base58btc decoder の ~50 行コード以外の依存追加なし(TS は `@scure/base`、Python は pure-Python 実装)
- v0.2(将来 ADR)で:
  - HTTP Message Signatures(RFC 9421)に拡張
  - actor allowlist 機能(`AMENO_ALLOWED_DIDS` env で whitelist)
  - did:web 認証(per-DID resolver)
  - Signal Protocol binding(ADR-2605181100 と統合)

## Alternatives Considered

1. **JWT bearer with rotating signing key** — central authority、
   distributed worker DID と相性悪い
2. **HTTP Message Signatures(RFC 9421)full implementation** — header
   parsing が重い、簡易 schema で先行して body だけ署名する v0.2
3. **mTLS** — browser に client cert を持たせるのが地獄、reject
4. **WebAuthn / Passkey** — per-actor だが daemon 側に rp-id verifier
   が必要、 inter-actor 相互運用が複雑

## References

- ADR-2605191407(viewer mode、 bearer 経路の前提)
- ADR-2605191135(worker DID)
- did:key Method Specification:
  <https://w3c-ccg.github.io/did-method-key/>
- multicodec ed25519-pub = 0xed:
  <https://github.com/multiformats/multicodec/blob/master/table.csv>
- @noble/curves Ed25519:
  <https://github.com/paulmillr/noble-curves>
