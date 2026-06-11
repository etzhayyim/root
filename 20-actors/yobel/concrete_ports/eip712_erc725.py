"""Real EIP-712 signed-consent verifier for the Erc725Port Protocol.

Per ADR-0074 (Ethereum Identity Bridge — CACAO + WebAuthn). For yobel, the
creditor signs a canonical EIP-712 typed-data envelope over the rite +
debts payload; this port recovers the signer and asserts it matches the
creditor DID's registered ERC725 owner address.

EIP-712 domain:
    name      = "YobelCreditorConsent"
    version   = "1"
    chainId   = the chain where YobelRiteRegistry is deployed
    verifyingContract = YobelRiteRegistry address (anchors the consent semantics)

Type definition:
    CreditorConsent {
        bytes32 riteId
        bytes32 creditorDidHash    // keccak256(creditor_did)
        bytes32 debtsRootHash      // keccak256 of canonical-encoded debts[]
    }
"""

from __future__ import annotations

import json
from typing import Callable

from eth_account.messages import encode_typed_data
from eth_account.account import Account
from web3 import Web3


_DOMAIN_TEMPLATE = {
    "name": "YobelCreditorConsent",
    "version": "1",
}

_TYPES = {
    "EIP712Domain": [
        {"name": "name", "type": "string"},
        {"name": "version", "type": "string"},
        {"name": "chainId", "type": "uint256"},
        {"name": "verifyingContract", "type": "address"},
    ],
    "CreditorConsent": [
        {"name": "riteId", "type": "bytes32"},
        {"name": "creditorDidHash", "type": "bytes32"},
        {"name": "debtsRootHash", "type": "bytes32"},
    ],
}


class Eip712Erc725Port:
    """Verify creditor signed_consent against the (rite, debts) payload.

    Implements yobel.ports.Erc725Port. Holds a resolver function that maps
    a creditor DID to its registered ERC725 owner address.
    """

    def __init__(
        self,
        chain_id: int,
        verifying_contract: str,
        did_to_address_resolver: Callable[[str], str | None],
    ):
        self.chain_id = chain_id
        self.verifying_contract = Web3.to_checksum_address(verifying_contract)
        self.resolve = did_to_address_resolver

    def verify_eip712_signed_consent(
        self, signer_did: str, payload: dict, signature: str
    ) -> bool:
        expected_owner = self.resolve(signer_did)
        if expected_owner is None:
            return False
        domain = {
            **_DOMAIN_TEMPLATE,
            "chainId": self.chain_id,
            "verifyingContract": self.verifying_contract,
        }
        message = {
            "riteId": self._normalize_bytes32(payload.get("rite_id", "")),
            "creditorDidHash": Web3.keccak(text=payload.get("creditor_did", "")),
            "debtsRootHash": self._canonical_debts_root(payload.get("debts", [])),
        }
        try:
            signable = encode_typed_data(
                domain_data=domain,
                message_types={"CreditorConsent": _TYPES["CreditorConsent"]},
                message_data=message,
            )
            recovered = Account.recover_message(signable, signature=signature)
        except Exception:
            return False
        return Web3.to_checksum_address(recovered) == Web3.to_checksum_address(expected_owner)

    @staticmethod
    def _normalize_bytes32(v: str | bytes) -> bytes:
        if isinstance(v, (bytes, bytearray)):
            return bytes(v)
        if v.startswith("0x") and len(v) == 66:
            return bytes.fromhex(v[2:])
        return Web3.keccak(text=v)

    @staticmethod
    def _canonical_debts_root(debts: list[dict]) -> bytes:
        """Canonical encoding: keccak256(JSON-canonical(debts)) — deterministic for replay safety."""
        canonical = json.dumps(debts, sort_keys=True, separators=(",", ":"))
        return Web3.keccak(text=canonical)
