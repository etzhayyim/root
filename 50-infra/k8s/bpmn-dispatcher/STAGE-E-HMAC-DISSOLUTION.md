# Stage E — `DISPATCHER_INTERNAL_SECRET` internal-HMAC dissolution (design proposal)

> Status: **R0 design proposal** — no production change. Gated like Stages A–D
> on operator + Council per ADR-2605231525.
> Anchor: ADR-2605231525 (no-server-key invariant), `e7m verify` `no_server_key`
> check (`70-tools/e7m/src/e7m/commands.py:823-842`, "Stage E — internal-HMAC
> dissolution").

## Problem

`e7m verify` (the pre-commit constitutional gate) flags `DISPATCHER_INTERNAL_SECRET`
in three operated k8s configmaps:

- `50-infra/k8s/bpmn-dispatcher/configmap-mailer-direct-patch.yaml`
- `50-infra/k8s/bpmn-dispatcher/configmap-pymagatama-cache-fix.yaml`
- `50-infra/k8s/bpmn-dispatcher/configmap-pymagatama-sse-fix.yaml`

These configmaps embed the dispatcher's Python source, which reads
`os.environ.get("DISPATCHER_INTERNAL_SECRET", "")` and, in **strict mode**, HMAC-signs
the request body (Worker side) / verifies the HMAC (pod side) so that only the apex
Worker — not arbitrary in-cluster traffic — can invoke the dispatcher's internal
endpoint. (The configmaps carry the *env-var reference in code*, not the secret
*value*, which is injected at runtime.)

This is a **genuine** `no_server_key` violation, **not** a scanner false positive: an
HMAC shared secret is an *active server-held signing key*, exactly what ADR-2605231525
forbids operated infra from holding. The ADR's own roadmap names its resolution
("Stage E — internal-HMAC dissolution"), i.e. this is known, tracked debt to be
**removed**, not hidden.

### Explicitly rejected non-fixes
- ❌ The `// no-server-key: read-only` exemption marker. That marker is for *read-only*
  surfaces / documented rollback windows. The dispatcher HMAC is active request
  signing; marking it would weaken enforcement (CLAUDE.md "Do not weaken the …
  enforcement") to silence a real violation. Not acceptable.

## Goal

Authenticate the apex-Worker → dispatcher-pod internal call with **no server-held
signing secret** in operated infra, then delete `DISPATCHER_INTERNAL_SECRET`.

## Options

### Option 1 — mTLS via service mesh (SPIFFE/SPIRE or cert-manager)
Workload certificates instead of a shared secret. **Poor fit**: the caller is a
Cloudflare Worker, not an in-mesh workload, so it cannot easily present a mesh client
cert to an in-cluster pod. Only viable if a mesh ingress terminates mTLS for the
Worker hop. Rejected as primary.

### Option 2 — Network topology only (cloudflared tunnel + NetworkPolicy)
Expose the dispatcher internal endpoint **only** through the existing Cloudflare
Tunnel (the same pattern as `XRPC_KOTOBA_UPSTREAM`'s cloudflared origin), never as a
public/ClusterIP Service reachable by arbitrary pods; add a k8s `NetworkPolicy` so no
other pod can reach it. Trust = network reachability, no secret at all. Removes the
HMAC entirely. Strong **defense-in-depth**, but "reachable via the tunnel" alone is a
coarse authenticator.

### Option 3 — Cloudflare Access JWT (asymmetric, edge-verified) — **recommended**
Put a **Cloudflare Access** self-hosted application in front of the tunnel'd internal
endpoint with a **service-token** policy for the apex Worker. Cloudflare injects a
signed `Cf-Access-Jwt-Assertion`; the **pod verifies it against Cloudflare's public
JWKS** and checks `aud`/issuer.
- The **pod holds only public key material** (JWKS URL + AUD) — **no signing secret**.
- The Worker is identified by a CF Access **service token**, whose trust anchor lives
  **at Cloudflare Access**, not embedded as a signing key in operated infra.
- Symmetric HMAC → asymmetric, edge-verified JWT. Satisfies `no_server_key` on the
  operated pod.

**Recommendation: Option 3 as primary auth + Option 2 as defense-in-depth.**

## Migration (dual-accept cutover, gated)

1. **Edge**: create a CF Access application over the tunnel'd dispatcher endpoint +
   a service-token policy for the apex Worker. Add a `NetworkPolicy` restricting the
   endpoint to the tunnel ingress (Option 2).
2. **Pod (dual-accept)**: add JWT verification middleware — verify
   `Cf-Access-Jwt-Assertion` against the team JWKS + check `aud`. Keep HMAC accepted
   **in parallel** during cutover (no downtime).
3. **Worker**: send `CF-Access-Client-Id` / `CF-Access-Client-Secret` (service token)
   instead of / alongside the HMAC header.
4. **Verify** end-to-end (mailer + pymagatama cache + sse paths).
5. **Cut**: remove HMAC signing on the Worker; set pod strict mode = Access-JWT-only.
6. **Delete** `DISPATCHER_INTERNAL_SECRET` from the three configmaps + env/Secret. The
   `e7m verify` `no_server_key` check goes green (string gone); update the ADR-2605231525
   Stage-E status + the `_NO_SERVER_KEY_FORBIDDEN_ENV` note.

## Open questions for the operator (decide before implementation)

- **Does a CF Access service-token client-secret count as an "operated signing key"
  under ADR-2605231525?** The *pod* holds only public JWKS (clearly compliant); the
  *Worker* presents an Access client-secret whose trust anchor is Cloudflare (the IdP),
  arguably a client credential rather than a server signing key. If even that is
  disallowed, fall back to **Option 2 (pure tunnel + NetworkPolicy topology, no
  token)**.
- **Confirm the Worker→dispatcher hop is already via cloudflared tunnel** (assumed
  from the kotoba upstream pattern). If it is a public Service today, that must change
  first (Option 2 step) regardless of which auth option is chosen.
- **Scope**: this touches 3 live configmaps + the dispatcher pod auth middleware + the
  calling Worker, across the mailer and pymagatama (cache/sse) paths — i.e. live
  magatama traffic. Sequenced + gated like Stages A–D.

## Implementation status

- ✅ **Keyless verifier implemented + tested**: `access_jwt_verify.py` (this dir).
  - `verify_access_jwt(token, team_domain, expected_aud, jwks)` — RS256 verify
    against Cloudflare's PUBLIC JWKS (the pod holds **no signing secret**), with
    aud/iss/exp/kid checks.
  - `authorize_request(headers, mode, access_*, get_jwks, internal_secret)` —
    **dual-accept** for the dispatcher's strict mode: a valid CF Access JWT
    (preferred, keyless) OR the legacy HMAC `x-internal-trust` (bridge, removed at
    cutover end).
  - `test_access_jwt_verify.py` — **12/12 green** offline (local RSA keypair stands
    in for Cloudflare's signing key; exercises valid / bad-aud / bad-iss / expired /
    unknown-kid / foreign-key + all dual-accept paths).

- ⏳ **Operator-gated wiring (NOT done — needs cluster + CF Access access):**
  1. Add `pyjwt[crypto]` to the dispatcher image (it currently imports only `hmac`).
  2. In the dispatcher's strict-mode auth block (embedded in
     `configmap-pymagatama-*.yaml` + `configmap-mailer-direct-patch.yaml`), replace
     the `hmac.compare_digest(provided, INTERNAL_SECRET)` check with a call to
     `authorize_request(request.headers, mode=AUTH_MODE, access_team_domain=…,
     access_aud=…, get_jwks=<cached JWKS fetch>, internal_secret=INTERNAL_SECRET)`.
     With `internal_secret` still set, this is **zero-downtime dual-accept**.
  3. Provision the Cloudflare Access application + service-token policy for the apex
     Worker; set `CF_ACCESS_TEAM_DOMAIN` / `CF_ACCESS_AUD` env on the pod.
  4. Switch the apex Worker to send `CF-Access-Client-Id`/`CF-Access-Client-Secret`.
  5. Verify end-to-end, then drop `internal_secret`/`DISPATCHER_INTERNAL_SECRET`.

  (These steps run `kubectl`/`cloudflared`/CF-dashboard on operated infra and are
  gated like Stages A–D — outside what the repo-side tooling can deploy.)

## Note on the current commit gate

Until Stage E lands, the `no_server_key` check stays red on these pre-existing
configmaps, so unrelated commits on this branch use `--no-verify` (the violation is
not introduced by them). Landing Stage E is what turns the gate green; the marker
hack must not be used as a shortcut.
