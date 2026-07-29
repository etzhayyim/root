package etzhayyim.claim.decision

# Claim dispute arbiter — V1 policy (ADR-2604261717 Phase 2-B)
#
# Called by rego-arbiter-settler after reading on-chain claim state and
# fetching evidence from IPFS. The settler posts:
#
#   POST /v1/data/etzhayyim/claim/decision
#   { "input": {
#       "claimId":    "0x…",        // bytes32
#       "claimant":   "0x…",        // address
#       "challenger":  "0x…",        // address
#       "bond":        "1000000000000000000",  // bigint as string (wei)
#       "counterBond": "500000000000000000",   // bigint as string (wei)
#       "evidenceCid": "0x…",        // bytes32 (zero = no evidence)
#       "evidence":    { … } | null  // JSON fetched from IPFS; null if unreachable
#   }}
#
# Decision rules (V1 — minimal substantiation bar):
#   CLAIMANT WINS  — evidence CID is non-zero AND evidence.statement is a
#                    non-empty string. The claim is substantiated.
#   CHALLENGER WINS — any other case: no CID, unreachable IPFS, or evidence
#                    JSON is missing the statement field.
#
# This policy is deliberately conservative: a challenger who puts up a
# counter-bond wins by default unless the claimant can produce real content.
# Phase 2 will extend this with DID authority checks and content classifiers.

default wins := false
default reason := "challenger-wins-default"

# ── Evidence helpers ──────────────────────────────────────────────────────────

_zero_cid if {
    input.evidenceCid == "0x0000000000000000000000000000000000000000000000000000000000000000"
}

_evidence_present if {
    input.evidence != null
    is_object(input.evidence)
}

_evidence_has_statement if {
    _evidence_present
    is_string(input.evidence.statement)
    count(input.evidence.statement) > 10
}

# ── Decision ─────────────────────────────────────────────────────────────────

wins if {
    not _zero_cid
    _evidence_has_statement
}

# ── Reason ───────────────────────────────────────────────────────────────────
# Exhaustive, mutually exclusive partition of input space (no `not wins` guards).
# Phase 2 extensions must add new branches that preserve mutual exclusion.

reason := "evidence-valid" if {
    not _zero_cid
    _evidence_has_statement
}

reason := "no-evidence-cid" if {
    _zero_cid
}

reason := "evidence-unreachable" if {
    not _zero_cid
    not _evidence_present
}

reason := "evidence-missing-statement" if {
    not _zero_cid
    _evidence_present
    not _evidence_has_statement
}

# ── Top-level result consumed by the settler ──────────────────────────────────

decision := {
    "wins":   wins,
    "reason": reason,
}
