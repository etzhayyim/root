"""warifu EAVT datom schema — the kotoba write contract for the `warifu/*` namespace.

ADR-2605302000 / ADR-2605262130. Cells emit facts as (E, A, V, T) tuples; this module is the
single definition of which attributes exist and what value types/invariants they carry. The real
`@etzhayyim/sdk`-backed kotoba adapter MUST call `assert_valid()` before writing, so malformed or
fee-leaking datoms can never reach the QuadStore. Mirrors the tadori `tadori/*` schema pattern.

Entity classes (warifu/kind): auth_hold | capture | settlement | refund | dispute
"""

from __future__ import annotations

KINDS = frozenset({"auth_hold", "capture", "settlement", "refund", "dispute"})
FUNDINGS = frozenset({"debit", "credit"})
DISPUTE_STATUSES = frozenset({"open", "evidence", "chigiri", "resolved", "absorbed"})

# attribute -> (python value type, optional invariant predicate)
ATTRS: dict[str, tuple[type, object]] = {
    "warifu/kind": (str, lambda v: v in KINDS),
    "warifu/card_token": (str, None),
    "warifu/amount_usdc": (int, lambda v: v >= 0),
    "warifu/remaining_usdc": (int, lambda v: v >= 0),
    "warifu/funding": (str, lambda v: v in FUNDINGS),
    "warifu/purpose": (str, None),
    "warifu/merchant_did": (str, None),
    "warifu/fee_usdc": (int, lambda v: v == 0),          # 決済手数料ゼロ invariant
    "warifu/note": (str, None),
    "warifu/auth_id": (str, None),
    "warifu/settlement_id": (str, None),
    "warifu/finality": (str, lambda v: v == "T+0"),       # T+0 final invariant
    "warifu/tx": (str, None),
    "warifu/reason_code": (str, None),
    "warifu/opened_by": (str, None),
    "warifu/status": (str, lambda v: v in DISPUTE_STATUSES),
    "warifu/evidence_cid": (str, None),
}


def validate_facts(facts) -> list[str]:
    """Return a list of violation strings (empty == all facts conform to the schema)."""
    violations: list[str] = []
    for i, fact in enumerate(facts):
        if not (isinstance(fact, tuple) and len(fact) == 4):
            violations.append(f"[{i}] not a 4-tuple (E,A,V,T): {fact!r}")
            continue
        e, a, v, t = fact
        if not isinstance(e, str) or not isinstance(t, str):
            violations.append(f"[{i}] E and T must be str (entity id / tx): {fact!r}")
        spec = ATTRS.get(a)
        if spec is None:
            violations.append(f"[{i}] unknown attribute '{a}'")
            continue
        vtype, pred = spec
        if not isinstance(v, vtype):
            violations.append(f"[{i}] '{a}' expects {vtype.__name__}, got {type(v).__name__}={v!r}")
            continue
        if pred is not None and not pred(v):
            violations.append(f"[{i}] '{a}' invariant violated: value={v!r}")
    return violations


def assert_valid(facts) -> None:
    """Raise AssertionError if any fact violates the schema. Use before kotoba write."""
    violations = validate_facts(facts)
    assert not violations, "EAVT schema violations:\n  " + "\n  ".join(violations)
