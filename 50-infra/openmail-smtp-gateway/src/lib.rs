//! openmail SMTP gateway — bridge legacy SMTP ⇄ kotoba-server email XRPC.
//!
//! Implements the bridge plane of ADR-2605172200 against the **current** canonical
//! storage path: kotoba-server's `com.etzhayyim.apps.kotoba.email.*` endpoints (not the
//! original atproto-MST AppView design). The gateway is a *separate process* that
//! speaks only HTTP to kotoba-server — it never links kotoba crates (kotoba is a
//! git subrepo; crossing that boundary by path-dep would be fragile). This is the
//! same "isolate the SMTP abuse surface in its own service" stance the ADR takes
//! in §"Why not use the PDS as an SMTP MX directly".
//!
//! ## Two regimes, by construction
//!
//! - **Inbound (legacy SMTP → kotoba)**: a remote MTA (gmail, corp, gov) delivers
//!   over SMTP. The plaintext cannot be Signal-sealed — the sender is not a member.
//!   So inbound mail is stored with kotoba's at-rest `AgentCrypto` encryption via
//!   `email.ingest` (server-readable). This is expected and matches the ADR: bridged
//!   legacy mail is public-content / non-E2E.
//! - **Native (member ⇄ member)**: handled entirely by `email.send` (Signal E2E,
//!   zero-access) — NOT this gateway. The gateway exists only for the legacy edge.
//!
//! ## What's pure + tested here
//!
//! - [`smtp_in`] — RFC 5321 inbound command state machine (no sockets).
//! - [`routing`] — recipient address → DID resolution (ADR §3.4).
//! - [`render`] — outbound structured message → RFC 5322 bytes (+ dot-stuffing,
//!   header-injection guard, RFC 2047 subject encoding).
//! - [`ingest`] — build the `email.ingest` request body.
//!
//! The socket listener + HTTP client live behind the `daemon` feature (see
//! `src/main.rs` / `src/daemon.rs`), so the core verifies fast and offline.

pub mod attestation;
pub mod dkim;
pub mod dmarc;
pub mod ingest;
pub mod orchestrate;
pub mod outbound;
pub mod outbound_route;
pub mod postage;
pub mod provision;
pub mod render;
pub mod routing;
pub mod smtp_in;
pub mod smtp_out;
pub mod spf;
pub mod status;
pub mod threading;

#[cfg(feature = "daemon")]
pub mod daemon;
