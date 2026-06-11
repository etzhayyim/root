"""Web3 concrete impl wrapping YobelReleaseRegistry.sol.

This port is used by the release_settlement cell to mirror its release record
on-chain. It is NOT a full Protocol implementation of CreditorEnrollmentPort
(that one wraps the encrypted AT MST). Instead it provides utility methods
the orchestrator calls after the cell completes to push to chain.
"""

from __future__ import annotations

import json
from pathlib import Path

from web3 import Web3
from web3.contract import Contract


_RELEASE_METHOD_BY_NAME = {
    "voluntary_bookkeeping": 0,
    "base_l2_transfer": 1,
    "court_order": 2,
    "sovereign_decree": 3,
    "ecclesiastical_indulgence": 4,
}


class Web3ReleaseRegistryPort:
    """Thin wrapper around YobelReleaseRegistry for orchestrator post-cell writes."""

    def __init__(self, w3: Web3, address: str, sender_address: str, abi_path: Path | None = None):
        self.w3 = w3
        self.sender = Web3.to_checksum_address(sender_address)
        path = abi_path or Path(__file__).parent.parent / "abi" / "YobelReleaseRegistry.json"
        abi_data = json.loads(path.read_text())
        self.contract: Contract = w3.eth.contract(
            address=Web3.to_checksum_address(address),
            abi=abi_data["abi"],
        )

    # ─── Writes ──────────────────────────────────────────────────────

    def register_debt_cap(
        self,
        rite_id: str | bytes,
        debt_id: str | bytes,
        principal_micro_usdc: int,
        accrued_micro_usdc: int,
    ) -> str:
        rite_b = self._to_bytes32(rite_id)
        debt_b = self._to_bytes32(debt_id)
        tx_hash = self.contract.functions.registerDebtCap(
            rite_b, debt_b, principal_micro_usdc, accrued_micro_usdc
        ).transact({"from": self.sender})
        self.w3.eth.wait_for_transaction_receipt(tx_hash)
        return tx_hash.hex()

    def record_release(
        self,
        *,
        release_id: str | bytes,
        rite_id: str | bytes,
        debt_id: str | bytes,
        debtor_did: str,
        creditor_did: str,
        released_micro_usdc: int,
        release_method: str,
        base_l2_tx_hash_cross_ref: bytes = b"\x00" * 32,
    ) -> str:
        method_idx = _RELEASE_METHOD_BY_NAME.get(release_method)
        if method_idx is None:
            raise ValueError(f"unknown release_method: {release_method}")
        tx_hash = self.contract.functions.recordRelease(
            self._to_bytes32(release_id),
            self._to_bytes32(rite_id),
            self._to_bytes32(debt_id),
            self._did_hash(debtor_did),
            self._did_hash(creditor_did),
            released_micro_usdc,
            method_idx,
            base_l2_tx_hash_cross_ref,
        ).transact({"from": self.sender})
        self.w3.eth.wait_for_transaction_receipt(tx_hash)
        return tx_hash.hex()

    # ─── Reads ───────────────────────────────────────────────────────

    def get_debt_cap(self, rite_id: str | bytes, debt_id: str | bytes) -> dict:
        row = self.contract.functions.getDebtCap(
            self._to_bytes32(rite_id), self._to_bytes32(debt_id)
        ).call()
        return {
            "principal_micro_usdc": row[0],
            "accrued_micro_usdc": row[1],
            "total_released_micro_usdc": row[2],
            "registrar": row[3],
            "registered_at": row[4],
        }

    def release_count(self) -> int:
        return self.contract.functions.releaseCount().call()

    def release_count_by_rite(self, rite_id: str | bytes) -> int:
        return self.contract.functions.releaseCountByRite(self._to_bytes32(rite_id)).call()

    # ─── Helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _to_bytes32(v: str | bytes) -> bytes:
        if isinstance(v, (bytes, bytearray)):
            if len(v) != 32:
                raise ValueError(f"bytes32 must be 32 bytes, got {len(v)}")
            return bytes(v)
        if v.startswith("0x") and len(v) == 66:
            return bytes.fromhex(v[2:])
        return Web3.keccak(text=v)

    @staticmethod
    def _did_hash(did: str) -> bytes:
        return Web3.keccak(text=did)
