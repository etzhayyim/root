#!/usr/bin/env python3
"""business-manager — kotoba-native internal ERP langgraph actor (kotoba WASM cell).

ADR-2606072000 (Phase A of the substrate remediation wave, ADR-2606071800). Replaces the
legacy RisingWave/Cypher `graph.query`/`graph.write` pipeline with append-only double-entry
bookkeeping on the kotoba Datom log. Handlers over one kotoba EAVT graph:

  post_journal_entry   validate double-entry balance (G2) + approval routing (G6) → member-signed posting (G4)
  post_purchase_order  PO approval routing (G6) → member-signed posting (G4)
  authorize_posting    only a member-origin signature posts (G4 no-server-key)
  fiscal_year_of       JP fiscal year (Apr 1 - Mar 31) derivation
  trial_balance        Σdebit / Σcredit roll-up over journal entries (must net to 0)

Hard invariants encoded so they are structurally unrepresentable, not policy:
  - double-entry balanced (G2): an entry whose Σdebit ≠ Σcredit is REJECTED, never posted.
  - approval thresholds (G6): `approved` is DERIVED from the amount (journal >1M JPY, PO >5M
    JPY → approval-required); the caller cannot self-approve.
  - append-only audit trail (G7): postings are Datoms; no mutate/delete — toritate audits them.
  - no-server-key (G4): only a member signature posts; a server signature is refused.
  - internal-only (G1): there is no tenant/customer field — the ledger is etzhayyim's own.

Murakumo-only for any narration (G8). R1 computes + validates postings; on-chain settlement of
AP is via warifu (intent-only at R0).
"""
from __future__ import annotations

from typing import TypedDict

try:
    from kotoba import datalog, llm  # type: ignore
except ImportError:  # local dev fallback
    datalog = llm = None  # type: ignore

# Approval thresholds (G6), JPY minor units (1 JPY = 100 minor).
JOURNAL_APPROVAL_MINOR = 1_000_000 * 100
PO_APPROVAL_MINOR = 5_000_000 * 100


# --------------------------------------------------------------------------- #
# fiscal year (JP: Apr 1 - Mar 31)
# --------------------------------------------------------------------------- #
def fiscal_year_of(iso_date: str) -> str:
    """Return the JP fiscal-year label for an ISO date (YYYY-MM-DD). Apr–Dec → FY of that
    calendar year; Jan–Mar → FY of the previous calendar year. e.g. 2027-03-15 → FY2026."""
    y, m, _ = (int(p) for p in iso_date.split("-")[:3]) if iso_date.count("-") >= 2 else (0, 0, 0)
    return f"FY{y if m >= 4 else y - 1}"


# --------------------------------------------------------------------------- #
# double-entry balance (G2)
# --------------------------------------------------------------------------- #
def is_balanced(lines: list) -> bool:
    """True iff Σ debitMinor == Σ creditMinor and there are ≥2 lines (a real double entry)."""
    if len(lines) < 2:
        return False
    debit = sum(int(l.get("debitMinor", 0)) for l in lines)
    credit = sum(int(l.get("creditMinor", 0)) for l in lines)
    return debit == credit and debit > 0


# --------------------------------------------------------------------------- #
# approval routing (G6) — `approved` is DERIVED, never caller-set
# --------------------------------------------------------------------------- #
def approval_status(amount_minor: int, threshold_minor: int) -> str:
    return "approval-required" if int(amount_minor) > threshold_minor else "auto-approved"


# --------------------------------------------------------------------------- #
# postings (G4 no-server-key, G7 append-only)
# --------------------------------------------------------------------------- #
class JournalEntry(TypedDict, total=False):
    entryId: str
    lines: list
    description: str
    postedBy: str


def post_journal_entry(entry: JournalEntry, posted_at: str) -> dict:
    """Validate + stage a journal entry. Rejects an unbalanced entry (G2). Derives `approved`
    from the entry magnitude (G6) and `fiscalYear` from the date. Produces an UNSIGNED posting
    that only the member can authorize (G4). Never mutates — append-only (G7)."""
    lines = entry.get("lines", [])
    if not is_balanced(lines):
        return {"state": "rejected", "reason": "entry does not balance: Σdebit ≠ Σcredit (G2)"}
    if not entry.get("postedBy"):
        return {"state": "rejected", "reason": "missing member postedBy (G4)"}
    amount = sum(int(l.get("debitMinor", 0)) for l in lines)
    return {
        "state": "staged",
        "kind": "journalEntry",
        "entryId": entry["entryId"],
        "lines": lines,
        "amountMinor": amount,
        "currency": "JPY",
        "fiscalYear": fiscal_year_of(posted_at),
        "approved": approval_status(amount, JOURNAL_APPROVAL_MINOR),   # G6 derived
        "postedBy": entry["postedBy"],
        "postedSig": None,                                            # G4: unsigned until member authorizes
        "appendOnly": True,                                           # G7
    }


def post_purchase_order(po: dict, posted_at: str) -> dict:
    """Stage a purchase order; derive `approved` from the PO threshold (G6); member-signed (G4)."""
    if not po.get("postedBy"):
        return {"state": "rejected", "reason": "missing member postedBy (G4)"}
    amount = int(po.get("amountMinor", 0))
    return {
        "state": "staged",
        "kind": "purchaseOrder",
        "poId": po["poId"],
        "vendor": po.get("vendor", ""),
        "amountMinor": amount,
        "currency": "JPY",
        "items": po.get("items", []),
        "fiscalYear": fiscal_year_of(posted_at),
        "approved": approval_status(amount, PO_APPROVAL_MINOR),       # G6 derived
        "postedBy": po["postedBy"],
        "postedSig": None,
        "appendOnly": True,
    }


def authorize_posting(posting: dict, signature: dict) -> dict:
    """Post a staged entry. ONLY a member-origin signature authorizes (G4 no-server-key); a
    server signature is refused. Posting is append-only (G7) — the returned datom is final."""
    if posting.get("state") != "staged":
        return {**posting, "refused": True, "reason": "posting is not in :staged state"}
    if signature.get("origin") != "member":
        return {**posting, "refused": True,
                "reason": "only a member passkey/wallet signature posts to the ledger (G4 no-server-key)"}
    return {**posting, "state": "posted", "postedSig": signature.get("ref")}


# --------------------------------------------------------------------------- #
# trial balance (must net to 0 across the ledger)
# --------------------------------------------------------------------------- #
def trial_balance(entries: list) -> dict:
    """Roll up Σdebit / Σcredit across posted journal entries. A consistent ledger nets to 0
    (G2 holds per-entry, so the total holds too)."""
    debit = sum(int(l.get("debitMinor", 0)) for e in entries for l in e.get("lines", []))
    credit = sum(int(l.get("creditMinor", 0)) for e in entries for l in e.get("lines", []))
    return {"totalDebitMinor": debit, "totalCreditMinor": credit, "balanced": debit == credit}


# --------------------------------------------------------------------------- #
# invoice — AP (payable) / AR (receivable), member-signed, approval-routed (G6)
# --------------------------------------------------------------------------- #
INVOICE_APPROVAL_MINOR = 1_000_000 * 100  # same threshold as a journal entry (>1M JPY)
_INVOICE_DIRECTIONS = ("payable", "receivable")


def post_invoice(inv: dict, posted_at: str) -> dict:
    """Stage an invoice. `direction` is payable (AP) or receivable (AR). `approved` is DERIVED
    from the amount (G6); `fiscalYear` from the date. Member-signed (G4). Starts :open."""
    direction = inv.get("direction")
    if direction not in _INVOICE_DIRECTIONS:
        return {"state": "rejected", "reason": f"direction must be one of {_INVOICE_DIRECTIONS} (got {direction!r})"}
    if not inv.get("postedBy"):
        return {"state": "rejected", "reason": "missing member postedBy (G4)"}
    amount = int(inv.get("amountMinor", 0))
    if amount <= 0:
        return {"state": "rejected", "reason": "invoice amount must be positive"}
    return {
        "state": "staged",
        "kind": "invoice",
        "invoiceId": inv["invoiceId"],
        "direction": direction,
        "party": inv.get("party", ""),       # vendor (AP) or customer (AR)
        "amountMinor": amount,
        "currency": "JPY",
        "dueDate": inv.get("dueDate", ""),
        "fiscalYear": fiscal_year_of(posted_at),
        "approved": approval_status(amount, INVOICE_APPROVAL_MINOR),  # G6 derived
        "paymentStatus": "open",
        "postedBy": inv["postedBy"],
        "postedSig": None,
        "appendOnly": True,
    }


def settle_invoice(invoice: dict, paid_at: str, signature: dict) -> dict:
    """Mark a posted invoice paid. Member-signed only (G4 no-server-key). Append-only: emits a
    new :paid state (the original is never mutated, G7)."""
    if invoice.get("paymentStatus") not in ("open", "overdue"):
        return {**invoice, "refused": True, "reason": "invoice is not open/overdue"}
    if signature.get("origin") != "member":
        return {**invoice, "refused": True,
                "reason": "only a member signature settles an invoice (G4 no-server-key)"}
    return {**invoice, "paymentStatus": "paid", "paidAt": paid_at, "settledSig": signature.get("ref")}


def invoice_aging(invoices: list, as_of_date: str) -> dict:
    """Aging summary: open AP vs AR totals and which invoices are overdue (dueDate < as_of and
    still open). Pure date-string comparison (ISO dates sort lexically)."""
    ap_open = ar_open = 0
    overdue = []
    for inv in invoices:
        if inv.get("paymentStatus") != "open":
            continue
        amt = int(inv.get("amountMinor", 0))
        if inv.get("direction") == "payable":
            ap_open += amt
        elif inv.get("direction") == "receivable":
            ar_open += amt
        due = inv.get("dueDate", "")
        if due and due < as_of_date:
            overdue.append(inv.get("invoiceId"))
    return {"apOpenMinor": ap_open, "arOpenMinor": ar_open, "overdue": overdue}


# --------------------------------------------------------------------------- #
# budget allocation — budget vs actual / variance, over-budget flag
# --------------------------------------------------------------------------- #
def budget_vs_actual(budget: dict, journal_entries: list) -> dict:
    """Compare a budget allocation (account + fiscalYear + allocatedMinor) to actual spend on
    that account in that fiscal year (Σ debit on the account across posted entries). Returns
    spent / remaining / over flag. Over-budget is a flag, never a silent overwrite."""
    account = budget["account"]
    fy = budget["fiscalYear"]
    allocated = int(budget["allocatedMinor"])
    spent = 0
    for e in journal_entries:
        if e.get("fiscalYear") != fy:
            continue
        for l in e.get("lines", []):
            if l.get("account") == account:
                spent += int(l.get("debitMinor", 0))
    return {
        "account": account,
        "fiscalYear": fy,
        "allocatedMinor": allocated,
        "spentMinor": spent,
        "remainingMinor": allocated - spent,
        "over": spent > allocated,
    }
