// SPDX-License-Identifier: Apache-2.0
//
// economy_xrpc.rs — R1.3d scaffold (NOT YET WIRED into lib.rs route table)
//
// XRPC endpoints for the mKOTO economy per ADR-2605282100. This file ships
// the handler signatures + body shapes so the Python side
// (`kotoba_murakumo.economy`) and the Council-attestation tooling can iterate
// against a stable contract before the Rust wiring lands.
//
// R1.3d-wiring (separate ADR) will:
//   1. Add `pub mod economy_xrpc;` to lib.rs
//   2. Register routes in xrpc.rs:
//        GET  /xrpc/app.etzhayyim.kotoba.economy.tariff           → tariff
//        GET  /xrpc/app.etzhayyim.kotoba.economy.balance?did=...   → balance
//        POST /xrpc/app.etzhayyim.kotoba.economy.debit             → debit
//        POST /xrpc/app.etzhayyim.kotoba.economy.creditFromDonation → credit
//   3. Wire Quad I/O via the existing QuadStore + CACAO auth via the existing
//      check_read_access / require_did_ownership patterns.
//
// Until R1.3d-wiring lands, this module is NOT included in lib.rs and the
// `#[cfg(any())]` gate keeps the file out of the compilation. The file
// exists as committed R&D so the contract is reviewable by Council
// pre-attestation of the tariff schedule shape.
//
// References:
//   - ADR-2605282100 (mKOTO economy charter; 6-layer architecture)
//   - ADR-2605282000 (kotoba_murakumo facade — consumer of these XRPC)
//   - ADR-2605192300 (Council Lv6+ governance — tariff attestation)
//   - ADR-2605231525 (server-side signing capability — caller auth)
//   - ADR-2605240001 (kotoba cleanroom — Mkoto unit, gas, CitationLedger)
//   - 00-contracts/lexicons/app/etzhayyim/kotoba/economy/{tariff,balanceSnapshot,usageRecord}.json
//
// Status: R1.3d-scaffold (gate: #[cfg(any())])

#![cfg(any())]                          // R1.3d-wiring: remove this line.

use std::sync::Arc;

use axum::{
    extract::{Query, State},
    http::HeaderMap,
    response::Json as JsonResp,
    Json,
};
use serde::{Deserialize, Serialize};

use crate::server::KotobaState;

// ── NSIDs (canonical strings; lib.rs ALL_NSIDS will extend on wiring) ───────

pub const NSID_ECONOMY_TARIFF: &str = "app.etzhayyim.kotoba.economy.tariff";
pub const NSID_ECONOMY_BALANCE: &str = "app.etzhayyim.kotoba.economy.balance";
pub const NSID_ECONOMY_DEBIT: &str = "app.etzhayyim.kotoba.economy.debit";
pub const NSID_ECONOMY_CREDIT_FROM_DONATION: &str =
    "app.etzhayyim.kotoba.economy.creditFromDonation";

// ── tariff (GET) ────────────────────────────────────────────────────────────
//
// Returns the active Council-attested tariff schedule. Sourced from the
// `tariff/active` Quad emitted by the most recent Council Lv6+ ≥3
// attestation chain. Cached in-process with 60s TTL; invalidated on Quad
// commit of a new `tariff/active`.

#[derive(Debug, Clone, Serialize)]
pub struct TariffRow {
    pub backend: String,
    pub gpu_second_mkoto: u64,
    pub egress_mb_mkoto: u64,
    pub gas_per_1k_mkoto: u64,
}

#[derive(Debug, Clone, Serialize)]
pub struct TariffResponse {
    pub version: String,
    pub rows: Vec<TariffRow>,
    pub council_attestations: Vec<String>,
    pub signed_at: String,
}

pub async fn get_tariff(
    State(_state): State<Arc<KotobaState>>,
) -> JsonResp<TariffResponse> {
    // R1.3d-wiring: read tariff/active Quad → decode → return.
    // For now this is a placeholder shape; the real implementation will:
    //   1. arrangement.spo_lookup("tariff/active", "version") → version string
    //   2. arrangement.range_scan("tariff/row/<version>/*") → row list
    //   3. arrangement.range_scan("tariff/attestation/<version>/*") → DIDs
    //   4. compose TariffResponse + 60s in-process cache key
    unimplemented!("R1.3d-wiring: read tariff/active Quad chain via QuadStore")
}

// ── balance (GET) ───────────────────────────────────────────────────────────

#[derive(Debug, Clone, Deserialize)]
pub struct BalanceQuery {
    pub did: String,
}

#[derive(Debug, Clone, Serialize)]
pub struct BalanceResponse {
    pub did: String,
    pub balance_mkoto: i64,        // saturated to i64::MAX at Quad boundary
    pub last_updated_seq: u64,
    pub tariff_version_in_force: String,
    pub sbt_bearer: bool,
}

pub async fn get_balance(
    headers: HeaderMap,
    State(_state): State<Arc<KotobaState>>,
    Query(_query): Query<BalanceQuery>,
) -> JsonResp<BalanceResponse> {
    // R1.3d-wiring:
    //   1. CACAO auth: caller DID MUST match query.did (or be operator DID).
    //      Use existing check_read_access / require_did_ownership patterns
    //      from kotobase_xrpc.rs.
    //   2. arrangement.spo_lookup(query.did, "balance/mkoto") → i64
    //   3. arrangement.spo_lookup(query.did, "membership/sbt") → bool
    //   4. journal.head_seq() → last_updated_seq
    unimplemented!("R1.3d-wiring: CACAO auth + Quad lookup")
}

// ── debit (POST) ────────────────────────────────────────────────────────────

#[derive(Debug, Clone, Deserialize)]
pub struct DebitRequest {
    pub caller_did: String,
    pub invocation_id: String,
    pub cost_mkoto: u64,
    pub backend: String,
    pub tariff_version: String,
    pub usage: UsageBreakdownIn,
}

#[derive(Debug, Clone, Deserialize)]
pub struct UsageBreakdownIn {
    pub gpu_seconds: f64,
    pub egress_bytes: u64,
    pub prompt_chars: u64,
    pub completion_chars: u64,
    pub latency_ms: u64,
}

#[derive(Debug, Clone, Serialize)]
pub struct DebitResponse {
    pub new_balance_mkoto: i64,
    pub debited_at_seq: u64,
}

pub async fn post_debit(
    _headers: HeaderMap,
    State(_state): State<Arc<KotobaState>>,
    Json(_body): Json<DebitRequest>,
) -> JsonResp<DebitResponse> {
    // R1.3d-wiring:
    //   1. CACAO auth: signer DID MUST match caller_did (no operator override
    //      for debits — caller must self-sign).
    //   2. Charter Rider §2 scan on usage breakdown — already done by
    //      kotoba_murakumo before reaching here; redundant defense.
    //   3. Atomic Quad mutation:
    //        a. read current balance/mkoto/<caller_did>
    //        b. if balance < cost_mkoto AND caller is not SBT bearer →
    //           reject HTTP 402 InsufficientCredit (mirrors quota_for_tier
    //           pattern in kotobase_xrpc.rs).
    //        c. retract balance/mkoto/<caller_did> with old value
    //        d. assert balance/mkoto/<caller_did> with new value
    //        e. assert usage/{dim}_mkoto/<caller_did>/<epoch> Quads
    //           (per-dimension audit trail).
    //   4. Return new_balance + debited_at_seq.
    unimplemented!("R1.3d-wiring: atomic balance Quad debit + usage audit")
}

// ── credit_from_donation (POST, operator-only) ──────────────────────────────

#[derive(Debug, Clone, Deserialize)]
pub struct CreditFromDonationRequest {
    pub donor_did: String,
    pub usdc_amount: String,           // serialized BigUint to avoid f64 loss
    pub donation_tx_hash: String,      // Base L2 tx hash of TitheRouter.donate
    pub tithed_to_fund_usdc: String,
    pub mkoto_credit_at_ratio: u64,
    pub ratio_version: String,         // links to Council-set USDC→mKOTO ratio
}

#[derive(Debug, Clone, Serialize)]
pub struct CreditFromDonationResponse {
    pub new_balance_mkoto: i64,
    pub credited_at_seq: u64,
}

pub async fn post_credit_from_donation(
    _headers: HeaderMap,
    State(_state): State<Arc<KotobaState>>,
    Json(_body): Json<CreditFromDonationRequest>,
) -> JsonResp<CreditFromDonationResponse> {
    // R1.3d-wiring:
    //   1. Operator-only — signer DID MUST be in the kotoba-server donation
    //      indexer cell's allow-list. Use existing require_did_ownership
    //      pattern.
    //   2. Verify donation_tx_hash is a real Base L2 TitheRouter.donate event
    //      (sourced from the donation indexer cell that subscribes to Base
    //      L2 events; this XRPC trusts the indexer's signature).
    //   3. Verify tithed_to_fund_usdc == usdc_amount * 0.10 (constitutional
    //      invariant per ADR-2605192130; reject if mismatch).
    //   4. Atomic Quad mutation:
    //        a. read current balance/mkoto/<donor_did>
    //        b. retract + assert with new value = current + mkoto_credit
    //        c. assert credit/mkoto/<donor_did>/<epoch> audit Quad
    //   5. Return new balance + seq.
    unimplemented!("R1.3d-wiring: operator-auth + TitheRouter event verify + atomic credit")
}
