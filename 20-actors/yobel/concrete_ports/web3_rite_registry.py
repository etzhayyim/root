"""Web3 concrete impl of RiteRegistryPort backed by YobelRiteRegistry.sol."""

from __future__ import annotations

import json
from pathlib import Path

from web3 import Web3
from web3.contract import Contract

from yobel.ports import Rite


_RITE_TYPE_BY_INDEX = (
    "shmita_7yr",
    "yobel_50yr",
    "tokusei_rei",
    "religious_jubilee",
    "political_amnesty",
)
_STATUS_BY_INDEX = (
    "unknown",
    "declared",
    "active",
    "completed",
    "cancelled",
    "superseded",
)


class Web3RiteRegistryPort:
    """Reads Rite from YobelRiteRegistry contract on a connected chain.

    Implements the `RiteRegistryPort` Protocol (yobel.ports.RiteRegistryPort).
    For writes (declare/ratify/etc.), callers use the contract directly via
    `self.contract.functions.*.transact(...)` — this port is read-side.
    """

    def __init__(self, w3: Web3, address: str, abi_path: Path | None = None):
        self.w3 = w3
        path = abi_path or Path(__file__).parent.parent / "abi" / "YobelRiteRegistry.json"
        abi_data = json.loads(path.read_text())
        self.contract: Contract = w3.eth.contract(
            address=Web3.to_checksum_address(address),
            abi=abi_data["abi"],
        )

    def get_rite(self, rite_id: str) -> Rite | None:
        """Lookup a rite by its keccak256 hex string ID (e.g. '0x1234...')."""
        key = self._normalize_id(rite_id)
        row = self.contract.functions.rites(key).call()
        # `rites` is a public mapping → returns the Rite struct tuple
        # Status.Unknown (0) means uninitialized
        if row[8] == 0:  # status field
            return None
        return Rite(
            rite_id=row[0].hex() if isinstance(row[0], (bytes, bytearray)) else row[0],
            rite_type=_RITE_TYPE_BY_INDEX[row[1]],
            status=_STATUS_BY_INDEX[row[8]],
            effective_date=self._timestamp_to_iso(row[4]),
            expiry_date=self._timestamp_to_iso(row[5]) if row[5] else None,
            scope=f"sha256:{row[3].hex() if isinstance(row[3], (bytes, bytearray)) else row[3]}",
            scope_jurisdictions=[],  # off-chain enrichment; on-chain stores hash only
            issuer_did=f"hash:{row[7].hex() if isinstance(row[7], (bytes, bytearray)) else row[7]}",
            doctrinal_basis=f"sha256:{row[2].hex() if isinstance(row[2], (bytes, bytearray)) else row[2]}",
        )

    @staticmethod
    def _normalize_id(rite_id: str) -> bytes:
        """Accept either a 0x-hex string (32 bytes) or a UTF-8 string to be keccak'd."""
        if rite_id.startswith("0x") and len(rite_id) == 66:
            return bytes.fromhex(rite_id[2:])
        return Web3.keccak(text=rite_id)

    @staticmethod
    def _timestamp_to_iso(ts: int) -> str:
        if ts == 0:
            return ""
        from datetime import datetime, timezone
        return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat().replace("+00:00", "Z")
