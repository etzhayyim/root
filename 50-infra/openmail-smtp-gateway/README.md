# openmail-smtp-gateway

SMTP **bridge plane** for etzhayyim openmail — terminates legacy SMTP and relays
to `kotoba-server`'s email XRPC. Implements ADR-2605172200 §3 against the *current*
canonical storage path (kotoba Datom log + `com.etzhayyim.apps.kotoba.email.*`), not the
original atproto-MST AppView design.

License: Apache-2.0 + etzhayyim Charter Compliance Rider v2.0 (see `/CHARTER-RIDER.md`).

## Why a separate process

The gateway speaks **only HTTP** to kotoba-server and links no kotoba crates
(kotoba is a git subrepo; a path-dep across that boundary would be fragile). This
also isolates the SMTP abuse surface in its own service — the same stance the ADR
takes in *"Why not use the PDS as an SMTP MX directly"*.

## Two regimes (by construction)

| Path | Encryption | Server can read? | Handled by |
|---|---|---|---|
| **Native** member ⇄ member | Signal E2E (`email.send`) | **No** (zero-access) | kotoba-server — *not this gateway* |
| **Bridged** legacy SMTP ⇄ member | kotoba at-rest `AgentCrypto` (`email.ingest`) | Yes | **this gateway** |

Legacy senders (gmail, corp, gov) cannot Signal-seal, so bridged mail is
server-readable at rest — expected and consistent with the ADR (bridged legacy
mail is public-content / non-E2E). True E2E is reserved for the native path.

```
  外部 MTA ──SMTP──▶  openmail-smtp-gateway  ──HTTP email.ingest──▶  kotoba-server
 (gmail等)            (this crate)                                  (recipient inbox graph)

  recipient inbox ──email.list/read──▶ gateway ──render+DKIM+SMTP──▶ 外部 MTA   (outbound, R0 TODO)
```

## Layout

| File | Role | Tested |
|---|---|---|
| `src/smtp_in.rs` | RFC 5321 inbound command state machine + STARTTLS (socket-free) | ✅ 20 tests |
| `src/spf.rs`     | SPF (RFC 7208) parse + evaluate (ip4/ip6/all + injected DNS resolver) | ✅ 12 tests |
| `src/dmarc.rs`   | DMARC (RFC 7489) record parse + DKIM/SPF alignment + disposition | ✅ 9 tests |
| `src/attestation.rs`| `app.openmail.smtpAttestation` builder + DMARC-reject SMTP gate | ✅ 5 tests |
| `src/routing.rs` | recipient address → DID (ADR §3.4) + inline base32 | ✅ 11 tests |
| `src/render.rs`  | structured message → RFC 5322 bytes (+ dot-stuffing, header-injection guard, RFC 2047) | ✅ 8 tests |
| `src/dkim.rs`    | DKIM `ed25519-sha256` + `rsa-sha256` sign + verify (RFC 6376/8463), DNS TXT builder | ✅ 15 tests (incl. both RFC 8463 KATs) |
| `src/outbound.rs`| render → DKIM-sign assembly, single + dual (ed25519+rsa) | ✅ 4 tests |
| `src/orchestrate.rs`| **outbound pipeline planner** — partition → postage gate → dual-sign → per-MX grouping | ✅ 6 tests (full-compose) |
| `src/smtp_out.rs`| SMTP **client** send state machine + STARTTLS + MX selection + retry schedule | ✅ 10 tests |
| `src/outbound_route.rs`| recipient classification (local/external) + per-domain MX grouping | ✅ 7 tests |
| `src/provision.rs`| per-member DKIM provisioning + Cloudflare TXT request + ARK-enrollment batch | ✅ 9 tests |
| `src/postage.rs` | `Postage.sol` keccak256 binding + receipt verify + `Paid`-log decode + `eth_getLogs` filter | ✅ 15 tests |
| `src/threading.rs`| bridge `Message-ID ⇄ at-uri` map + reply/thread resolution | ✅ 7 tests |
| `src/status.rs`  | per-recipient delivery → SMTP reply-code mapping | ✅ 6 tests |
| `src/ingest.rs`  | build the `email.ingest` request body/URL | ✅ 3 tests |
| `src/daemon.rs`  | inbound listener + `relay_to_mx`/`execute_plan` + `publish_dkim_records` + `fetch_postage_receipt` (feature `daemon`) | R0 edge |
| `src/main.rs`    | binary entrypoint | — |

The pure core builds and tests **without** tokio/reqwest (141 tests). The listener
is behind the `daemon` feature so `cargo test` is fast and offline.

## Outbound pipeline (assembled)

`orchestrate::plan_outbound` composes the whole outbound path as one pure function:

```
native message + member DKIM keys + postage receipt
   │
   ├─ outbound_route::partition      → local DIDs / external addrs / invalid
   ├─ postage::message_hash + verify → gate external on a valid, bound receipt
   ├─ outbound::render_and_dual_sign → ed25519 + rsa DKIM over the RFC 5322
   └─ outbound_route::group_by_domain→ one OutboundMessage per destination MX
        │
        ▼  OutboundPlan { Planned | Held(verdict) | NoExternal }
   daemon::execute_plan(plan, resolve_mx) → relay_to_mx per domain (MX try-order)
```

A `Held` plan (missing/underpaid/mis-bound postage) relays nothing. The integration
test signs a real plan and verifies the transmitted bytes pass DKIM.

## Outbound DKIM — option (b): per-member self-signed, no platform key

The outbound signer ([`dkim`] + [`outbound`]) implements **option (b)**: each member
signs with their *own* Ed25519 key (derived in their passkey ARK hierarchy,
client-side), and the gateway holds **no signing key** — it relays already-signed
bytes. This resolves the only collision between the openmail outbound path and the
no-server-key invariant.

- **Private key**: member's ARK (client-side). `render_and_sign` is pure +
  wasm32-compilable so it runs in the member's browser.
- **Public key**: published in DNS at `<selector>._domainkey.etzhayyim.com` via
  `dkim::txt_record` / `dkim::dns_record_name` — public material only, automated at
  enrollment (no secret custody).
- **DMARC**: `d=etzhayyim.com` aligns with the `From:` domain; the authorising key
  is the member's. A leaked member key forges only that member; revocation = delete
  one TXT record.
- **Correctness**: `dkim.rs` is pinned to the RFC 8463 Appendix A known-answer
  vectors (both `ed25519-sha256` and `rsa-sha256`) — the test suite *verifies the
  RFC's own authoritative signatures*, so the canonicalization is byte-exact and
  interop-correct with real verifiers (Gmail etc.).
- **Deliverability**: `outbound::render_and_dual_sign` emits both an `ed25519-sha256`
  and an `rsa-sha256` signature (RFC 8463 dual-signing). Both keys are member-held;
  RSA is what receivers that don't yet accept ed25519 (Gmail today) validate against.

`verify` is also used for **inbound** DKIM checking. See ADR-2606022800.

## Build / test

```sh
cargo test                       # pure core (34 tests, no network deps)
cargo clippy                     # clean
cargo run --features daemon      # run the SMTP-in listener
```

### Listener env (feature `daemon`)

| Var | Default | Meaning |
|---|---|---|
| `OPENMAIL_BIND` | `0.0.0.0:2525` | listen address |
| `OPENMAIL_HOSTNAME` | `mx.openmail.etzhayyim.com` | EHLO/banner hostname |
| `OPENMAIL_KOTOBA_BASE` | `http://127.0.0.1:8077` | kotoba-server base URL |
| `OPENMAIL_OPERATOR_TOKEN` | *(required)* | Bearer for `email.ingest` (operator DID) |

## Address forms (R0)

- `<localpart>@etzhayyim.com` → `did:web:etzhayyim.com:actor:<localpart>`
- `_did_<base32-of-did>@etzhayyim.com` → embedded DID verbatim (handle-less fallback)

Foreign domains are relay-denied; unknown localparts are 550 *no such user*.

## R0 caveats / next steps

Done (pure cores, tested) — what was the "remaining glue":

- **Outbound driver** — SMTP-out client conversation, MX-order selection, retry
  schedule (`smtp_out`), recipient classification + per-MX grouping (`outbound_route`),
  and the on-the-wire relay (`daemon::relay_to_mx`).
- **Key provisioning + DNS publication** — per-member ed25519+rsa selectors and the
  Cloudflare TXT request builder (`provision`) — public material only.
- **Postage** — keccak256 message-hash binding, receipt verification, and the
  `Paid` event `eth_getLogs` filter (`postage`).
- **Per-recipient SMTP status mapping** — delivery outcomes → one final reply
  (`status`), wired into the inbound `daemon` path.
- **Threading map** — `Message-ID ⇄ at-uri` bidi map + reply/thread resolution (`threading`).

Done since (all *decision* logic, pure + tested; real HTTP adapters where feasible):

- **TLS** — STARTTLS is implemented at the protocol layer both ways (`smtp_in`
  advertises + handles it; `smtp_out::new_with_starttls` negotiates + re-EHLOs).
- **Inbound SPF / DMARC** — `spf` (parse + evaluate) and `dmarc` (alignment +
  disposition) are implemented; `attestation` builds the `smtpAttestation` record and
  the DMARC-reject SMTP gate.
- **Live IO adapters** — `daemon::publish_dkim_records` (Cloudflare POST) and
  `fetch_postage_receipt` (`eth_getLogs` + `Paid`-log decode) are wired with reqwest.
- **Key provisioning** — `provision::enrollment_requests` is the ARK-enrollment hook's
  pure output (both CF calls, public keys only); `publish_dkim_records` issues them.

Honest remaining scope — the irreducible OS/ops edges:

1. **TLS handshake + certs** — the *protocol* is done; the actual rustls handshake is
   not: inbound STARTTLS replies 454 until a server cert is provisioned
   (`OPENMAIL_TLS_CERT/KEY` + tokio-rustls Acceptor), and outbound `relay_to_mx`
   aborts on `Action::StartTls` until a tokio-rustls client is wired.
2. **Live MX DNS lookup** — inject a resolver into `execute_plan`'s `resolve_mx`
   (e.g. hickory-resolver) — `select_mx` ordering is already tested.
3. **The poller** — subscribe to native records and run `plan_outbound` →
   `fetch_postage_receipt` → `execute_plan`; and feed inbound SPF/DMARC from the
   connecting IP + DNS into `attestation::build`. The pure pieces all exist + compose.

## References

- ADR-2605172200 — Open Email: atproto MST-native mail + bidirectional SMTP bridge + on-chain postage
- `40-engine/kotoba/crates/kotoba-server/src/email_xrpc.rs` — `email.{list,read,ingest,send}` endpoints
- `50-infra/openmail-postage/` — `Postage.sol` (Base L2 USDC postage)
- `00-contracts/lexicons/app/openmail/` — openmail lexicon family
- RFC 5321 (SMTP), RFC 5322 (message format), RFC 2047 (encoded-words), RFC 4648 (base32)
