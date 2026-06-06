"""moyai 舫い — append-only, non-monetary, non-transferable reciprocity-credit ledger.

This is the *give-to-get* substrate: contributing verified inference to the commons
MINTS moyai credit; drawing discretionary surplus inference from the commons BURNS it.
"To draw from the well you must have fed it" (情報を得るには情報を生成する).

Charter invariants enforced HERE by construction (ADR-2606062100), not by policy:

  - **cash≡0 / non-monetary** — there is no USDC/amount field anywhere in an entry;
    `redeemable_usd_micros()` is a const-0 function. moyai credit can NEVER be sold,
    cashed out, or counted as income. It does not touch Basic High Income (N1).
  - **non-transferable** — the ledger exposes ONLY `mint` and `burn`. There is no
    `transfer`, `gift`, `merge`, or `pool` operation; a sybil farm cannot aggregate
    credit across identities because the operation that would do so does not exist.
  - **conservation (sink ≤ source)** — credit is only minted from VERIFIED contribution
    (see proof_of_contribution.py) and a burn can never exceed the holder's live balance.
    No inflation, no negative balances.
  - **decay (anti-hoarding / Wellbecoming flow)** — credit decays with a half-life, so it
    is a *flow*, never a *store of wealth/power*. It cannot accumulate into a class lever
    (anti-class, ADR-2605301020 §7); 1 SBT = 1 vote is untouched.

The ledger is an append-only event log (kotoba-Datom-isomorphic): every entry is an
immutable fact stamped with a transaction epoch; balances are a fold over the log, never
a mutable row that gets overwritten (ADR-2605312345; 非終末論 — no final-state balance).

Time is modelled as integer **epochs** (deterministic; the production binding stamps each
entry with the kotoba commit-DAG tx-time). All arithmetic is deterministic — no wall-clock,
no RNG — so the ledger replays bit-identically (resume-safe).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Literal

# Credit is integer "units" (one unit ≈ one reference inference-token-equivalent of
# verified contribution / one of discretionary draw). Integer-with-implied-units, no floats
# on the persisted record (ADR-2605190900); decay is computed at read time only.
Op = Literal["mint", "burn"]

# Anti-hoarding: a moyai credit loses half its drawing power every HALF_LIFE_EPOCHS.
# Keeps credit a flow, not a hoardable store (anti-class). Method-versioned + Council-attested
# in production; the constant lives here as the reference value.
HALF_LIFE_EPOCHS = 30


@dataclass(frozen=True)
class LedgerEntry:
    """One immutable, append-only reciprocity fact. No monetary field exists by design."""

    holder_did: str          # the contributing/drawing identity (donor DID or node DID)
    op: Op                   # "mint" (earned from verified work) | "burn" (spent on a draw)
    units: int               # integer credit units (> 0)
    epoch: int               # transaction epoch (monotone, kotoba tx-time in production)
    ref: str                 # provenance: contribution-attestation id (mint) | draw-receipt id (burn)

    def __post_init__(self) -> None:
        if self.units <= 0:
            raise ValueError("moyai ledger: units must be a positive integer")
        if self.op not in ("mint", "burn"):
            raise ValueError(f"moyai ledger: unknown op {self.op!r} (only mint/burn exist)")


def redeemable_usd_micros(_entry: "LedgerEntry | None" = None) -> int:
    """INVARIANT: moyai credit is non-monetary. Always 0, for every entry, forever.

    Its presence as a const-0 function is the on-chain proof that moyai does not touch
    cash≡0 (N1) and does not affect Basic High Income (the explicit constraint of this
    design): there is simply no path from a credit unit to a USD figure.
    """
    return 0


class MoyaiLedger:
    """Append-only reciprocity-credit ledger. mint + burn are the ONLY mutations."""

    def __init__(self) -> None:
        self._log: List[LedgerEntry] = []

    # --- the only two mutation verbs (no transfer/gift/pool exists) -------------------

    def mint(self, holder_did: str, units: int, epoch: int, ref: str) -> LedgerEntry:
        """Mint credit from VERIFIED contribution. Callers MUST route through
        proof_of_contribution.mint_from_verified — minting raw, unverified units is the
        thing the verification layer exists to prevent. Enforces monotone epochs."""
        self._guard_epoch(epoch)
        entry = LedgerEntry(holder_did, "mint", units, epoch, ref)
        self._log.append(entry)
        return entry

    def burn(self, holder_did: str, units: int, epoch: int, ref: str) -> LedgerEntry:
        """Spend credit on a discretionary surplus draw. Refuses to overdraw — a burn can
        never exceed the holder's live (decayed) balance, so balances never go negative
        and sink ≤ source holds by construction."""
        self._guard_epoch(epoch)
        avail = self.balance(holder_did, epoch)
        if units > avail + 1e-9:
            raise ValueError(
                f"moyai ledger: overdraw refused — {holder_did} has {avail:.3f} credit, "
                f"tried to burn {units}. Contribute first (情報を得るには情報を生成する)."
            )
        entry = LedgerEntry(holder_did, "burn", units, epoch, ref)
        self._log.append(entry)
        return entry

    # --- read path: balances are a decayed fold over the immutable log ----------------

    def balance(self, holder_did: str, now_epoch: int) -> float:
        """Live, decayed balance for one identity. Event-sourced fold: between events the
        running balance decays by the half-life; mint adds, burn subtracts. Pure function
        of the log — never a stored, overwritable number."""
        bal = 0.0
        last = None
        for e in self._log:
            if e.holder_did != holder_did:
                continue
            if last is not None:
                bal = _decay(bal, e.epoch - last, HALF_LIFE_EPOCHS)
            last = e.epoch
            bal = bal + e.units if e.op == "mint" else bal - e.units
            if bal < 0:
                bal = 0.0  # defensive; burn() already prevents this
        if last is not None and now_epoch > last:
            bal = _decay(bal, now_epoch - last, HALF_LIFE_EPOCHS)
        return bal

    # --- conservation / audit ---------------------------------------------------------

    def total_minted(self, holder_did: str | None = None) -> int:
        return sum(e.units for e in self._log
                   if e.op == "mint" and (holder_did is None or e.holder_did == holder_did))

    def total_burned(self, holder_did: str | None = None) -> int:
        return sum(e.units for e in self._log
                   if e.op == "burn" and (holder_did is None or e.holder_did == holder_did))

    def assert_conservation(self) -> None:
        """sink ≤ source: you can never have spent more than was ever verifiably minted."""
        if self.total_burned() > self.total_minted():
            raise AssertionError("moyai ledger: conservation violated — burned > minted")

    @property
    def log(self) -> List[LedgerEntry]:
        return list(self._log)

    def _guard_epoch(self, epoch: int) -> None:
        if self._log and epoch < self._log[-1].epoch:
            raise ValueError("moyai ledger: append-only — epoch must be monotone non-decreasing")


def _decay(amount: float, dt_epochs: int, half_life: int) -> float:
    """Exponential half-life decay. Deterministic; dt in integer epochs."""
    if amount <= 0 or dt_epochs <= 0:
        return max(amount, 0.0)
    return amount * (0.5 ** (dt_epochs / half_life))
