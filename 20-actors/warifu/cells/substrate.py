"""warifu substrate port — the DI seam between cells and kotoba/@etzhayyim/sdk.

R0 scaffold (ADR-2605302000). Cells depend on the `SubstratePort` Protocol, never on a concrete
client. In production an `@etzhayyim/sdk`-backed adapter is injected (R1); tests inject
`InMemorySubstrate`. Per ADR-2605231525 no platform key is held — the real adapter forwards the
holder's passkey/smart-account authorization; the in-memory fake models balances only.

EAVT writes go through `write_facts` (kotoba QuadStore, ADR-2605262130). Money never lives in the
gateway/cells — `settle_transfer` / `reverse_settlement` emit ERC-4337 UserOps via the adapter.
"""

from __future__ import annotations

from typing import Optional, Protocol, runtime_checkable


@runtime_checkable
class SubstratePort(Protocol):
    # --- identity / balances ----------------------------------------------------------
    def resolve_card(self, card_token: str) -> Optional[str]: ...
    def usdc_balance(self, account: str) -> int: ...
    def credit_available(self, account: str) -> int: ...

    # --- holds / captures / settlements ------------------------------------------------
    def place_hold(
        self, account: str, *, card_token: str, amount_usdc: int, funding: str,
        purpose: str, merchant_did: str,
    ) -> str: ...
    def load_hold(self, auth_id: str) -> Optional[dict]: ...
    def record_capture(self, auth_id: str, amount_usdc: int) -> str: ...
    def settle_transfer(
        self, *, merchant_did: str, amount_usdc: int, funding: str, auth_id: str,
    ) -> tuple[str, str]: ...
    def load_settlement(self, settlement_id: str) -> Optional[dict]: ...
    def reverse_settlement(self, settlement_id: str, amount_usdc: int) -> tuple[str, str]: ...
    def open_dispute(
        self, *, settlement_id: str, reason_code: str, opened_by_did: str,
        amount_usdc: int, evidence_cids: list[str],
    ) -> str: ...

    # --- EAVT ledger -------------------------------------------------------------------
    def write_facts(self, facts: list[tuple]) -> None: ...


class UnwiredSubstrate:
    """Default port. Fails loudly so a forgotten injection never silently settles money."""

    def _fail(self, op: str):
        raise NotImplementedError(
            f"warifu R0: substrate '{op}' not wired — inject @etzhayyim/sdk adapter or InMemorySubstrate"
        )

    def resolve_card(self, card_token: str): self._fail("resolve_card")
    def usdc_balance(self, account: str): self._fail("usdc_balance")
    def credit_available(self, account: str): self._fail("credit_available")
    def place_hold(self, account, **k): self._fail("place_hold")
    def load_hold(self, auth_id): self._fail("load_hold")
    def record_capture(self, auth_id, amount_usdc): self._fail("record_capture")
    def settle_transfer(self, **k): self._fail("settle_transfer")
    def load_settlement(self, settlement_id): self._fail("load_settlement")
    def reverse_settlement(self, settlement_id, amount_usdc): self._fail("reverse_settlement")
    def open_dispute(self, **k): self._fail("open_dispute")
    def write_facts(self, facts): self._fail("write_facts")


class InMemorySubstrate:
    """Deterministic in-memory fake for tests. Models card→account, balances, credit lines,
    holds, settlements, disputes, and an append-only EAVT facts log. No randomness/time."""

    def __init__(self):
        self.cards: dict[str, str] = {}          # card_token -> account
        self.balances: dict[str, int] = {}       # account -> USDC minor
        self.credit: dict[str, int] = {}         # account -> available 0% limit
        self.holds: dict[str, dict] = {}
        self.captures: dict[str, dict] = {}
        self.settlements: dict[str, dict] = {}
        self.disputes: dict[str, dict] = {}
        self.facts: list[tuple] = []
        self._n = 0

    def _id(self, prefix: str) -> str:
        self._n += 1
        return f"{prefix}-{self._n}"

    # --- test setup helpers ------------------------------------------------------------
    def add_card(self, card_token: str, account: str, *, balance=0, credit=0):
        self.cards[card_token] = account
        self.balances[account] = balance
        self.credit[account] = credit

    # --- port impl ---------------------------------------------------------------------
    def resolve_card(self, card_token: str):
        return self.cards.get(card_token)

    def usdc_balance(self, account: str) -> int:
        return self.balances.get(account, 0)

    def credit_available(self, account: str) -> int:
        return self.credit.get(account, 0)

    def place_hold(self, account, *, card_token, amount_usdc, funding, purpose, merchant_did):
        auth_id = self._id("auth")
        self.holds[auth_id] = {
            "holder": account, "card_token": card_token, "amount_usdc": amount_usdc,
            "funding": funding, "purpose": purpose, "merchant_did": merchant_did,
            "captured_usdc": 0, "status": "approve",
        }
        return auth_id

    def load_hold(self, auth_id):
        return self.holds.get(auth_id)

    def record_capture(self, auth_id, amount_usdc):
        cap_id = self._id("cap")
        self.holds[auth_id]["captured_usdc"] += amount_usdc
        self.captures[cap_id] = {"auth_id": auth_id, "amount_usdc": amount_usdc}
        return cap_id

    def settle_transfer(self, *, merchant_did, amount_usdc, funding, auth_id):
        hold = self.holds[auth_id]
        holder = hold["holder"]
        if funding == "debit":
            self.balances[holder] = self.balances.get(holder, 0) - amount_usdc
        else:  # credit: draw the 0% line
            self.credit[holder] = self.credit.get(holder, 0) - amount_usdc
        self.balances[merchant_did] = self.balances.get(merchant_did, 0) + amount_usdc
        sid = self._id("settle")
        self.settlements[sid] = {
            "auth_id": auth_id, "holder": holder, "merchant_did": merchant_did,
            "amount_usdc": amount_usdc, "funding": funding, "refunded_usdc": 0,
        }
        return sid, f"0xtx-{sid}"

    def load_settlement(self, settlement_id):
        return self.settlements.get(settlement_id)

    def reverse_settlement(self, settlement_id, amount_usdc):
        s = self.settlements[settlement_id]
        s["refunded_usdc"] += amount_usdc
        self.balances[s["merchant_did"]] -= amount_usdc
        if s["funding"] == "debit":
            self.balances[s["holder"]] = self.balances.get(s["holder"], 0) + amount_usdc
        else:  # credit repay (0%)
            self.credit[s["holder"]] = self.credit.get(s["holder"], 0) + amount_usdc
        rid = self._id("refund")
        return rid, f"0xtx-{rid}"

    def open_dispute(self, *, settlement_id, reason_code, opened_by_did, amount_usdc, evidence_cids):
        did_id = self._id("dispute")
        self.disputes[did_id] = {
            "settlement_id": settlement_id, "reason_code": reason_code,
            "opened_by": opened_by_did, "amount_usdc": amount_usdc,
            "evidence_cids": list(evidence_cids), "status": "open",
        }
        return did_id

    def write_facts(self, facts):
        self.facts.extend(facts)
