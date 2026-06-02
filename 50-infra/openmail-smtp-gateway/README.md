# openmail-smtp-gateway

SMTP **bridge plane** for etzhayyim openmail — terminates legacy SMTP and relays
to `kotoba-server`'s email XRPC. Implements ADR-2605172200 §3 against the *current*
canonical storage path (kotoba Datom log + `ai.gftd.apps.kotoba.email.*`), not the
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
| `src/smtp_in.rs` | RFC 5321 inbound command state machine (socket-free) | ✅ 16 tests |
| `src/routing.rs` | recipient address → DID (ADR §3.4) + inline base32 | ✅ 11 tests |
| `src/render.rs`  | structured message → RFC 5322 bytes (+ dot-stuffing, header-injection guard, RFC 2047) | ✅ 8 tests |
| `src/dkim.rs`    | DKIM `ed25519-sha256` sign + verify (RFC 6376/8463), DNS TXT builder | ✅ 11 tests (incl. RFC 8463 KAT) |
| `src/outbound.rs`| render → DKIM-sign assembly (option b end-to-end) | ✅ 3 tests |
| `src/ingest.rs`  | build the `email.ingest` request body/URL | ✅ 3 tests |
| `src/daemon.rs`  | TCP listener + reqwest relay (feature `daemon`) | R0, untested edge |
| `src/main.rs`    | binary entrypoint | — |

The pure core builds and tests **without** tokio/reqwest (48 tests). The listener
is behind the `daemon` feature so `cargo test` is fast and offline.

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
  vector — the test suite *verifies the RFC's own authoritative signature*, so the
  canonicalization is byte-exact and interop-correct with real verifiers (Gmail etc.).

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

Honest scope — what is **not** yet implemented:

1. **Inbound TLS** — no STARTTLS. Terminate TLS in front (Cloudflare Email Routing
   / stunnel) for now.
2. **Inbound SPF / DMARC** — `dkim::verify` exists (inbound DKIM is checkable), but
   SPF + DMARC alignment and the `app.openmail.smtpAttestation` write are not wired.
3. **Outbound wiring** — the signing core (`outbound::render_and_sign`, option b) is
   **done and tested**; the firehose/inbox poller that drives it, the actual SMTP-out
   relay, per-member key provisioning + DNS publication automation, and `Postage.sol`
   verification are the remaining glue.
4. **`rsa-sha256` co-signature** — Gmail et al. still prefer RSA; RFC 8463 recommends
   dual ed25519+rsa signing. The RSA signer drops in behind the same canonicalization
   (RSA key also client-held). ed25519-only is the R0 deliverable.
5. **Per-recipient SMTP status mapping** — `deliver()` logs failures; it should map
   them back to SMTP 4xx/5xx before the final `.`-reply.
6. **Threading map** (`bridge_message_id_map`, ADR §3.3) — not implemented; inbound
   bridged mail starts new threads.

## References

- ADR-2605172200 — Open Email: atproto MST-native mail + bidirectional SMTP bridge + on-chain postage
- `40-engine/kotoba/crates/kotoba-server/src/email_xrpc.rs` — `email.{list,read,ingest,send}` endpoints
- `50-infra/openmail-postage/` — `Postage.sol` (Base L2 USDC postage)
- `00-contracts/lexicons/app/openmail/` — openmail lexicon family
- RFC 5321 (SMTP), RFC 5322 (message format), RFC 2047 (encoded-words), RFC 4648 (base32)
