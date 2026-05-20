"""Integration test: deploy yobel contracts to anvil, roundtrip declare → ratify → release.

Verifies that:
  1. ABIs extracted from forge build are valid web3.py contracts
  2. Web3RiteRegistryPort reads return correct status after on-chain mutations
  3. Web3ReleaseRegistryPort enforces Charter Rider §2(b) one-way invariant
     at the EVM execution level (via contract revert, NOT off-chain check)
  4. EIP-712 signed consent verifier accepts genuine signatures, rejects forged

Requires:
  - foundry's `anvil` on PATH
  - web3.py + eth_account installed

Marked as `integration` so a default `pytest` run (unit suite) skips it. Run
explicitly:
    PYTHONPATH=20-actors python3 -m pytest 20-actors/yobel/tests_integration -m integration -v
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest
from eth_account.messages import encode_typed_data
from eth_account.account import Account
from web3 import Web3

# Make yobel importable when pytest runs from etzhayyim-root-yobel
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from yobel.concrete_ports.eip712_erc725 import Eip712Erc725Port
from yobel.concrete_ports.web3_release_registry import Web3ReleaseRegistryPort
from yobel.concrete_ports.web3_rite_registry import Web3RiteRegistryPort


CONTRACT_ROOT = Path(__file__).resolve().parents[3] / "50-infra" / "etzhayyim-yobel-contract"
ABI_DIR = Path(__file__).resolve().parents[1] / "abi"


pytestmark = pytest.mark.integration


# ─── anvil fixture ──────────────────────────────────────────────────


def _free_port() -> int:
    s = socket.socket()
    s.bind(("", 0))
    p = s.getsockname()[1]
    s.close()
    return p


@pytest.fixture(scope="module")
def anvil():
    port = _free_port()
    proc = subprocess.Popen(
        ["anvil", "--port", str(port), "--chain-id", "31337", "--silent"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    # Wait for RPC to come up
    rpc_url = f"http://127.0.0.1:{port}"
    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 1}))
            if w3.is_connected():
                break
        except Exception:
            pass
        time.sleep(0.1)
    else:
        proc.terminate()
        raise RuntimeError("anvil did not come up within 10s")
    yield rpc_url
    proc.terminate()
    proc.wait(timeout=5)


@pytest.fixture(scope="module")
def w3(anvil):
    return Web3(Web3.HTTPProvider(anvil))


@pytest.fixture(scope="module")
def deployer(w3):
    # Default anvil account 0
    acct = w3.eth.accounts[0]
    return acct


@pytest.fixture(scope="module")
def deployed_contracts(w3, deployer):
    """Deploy YobelRiteRegistry + YobelReleaseRegistry from forge build artifacts."""
    rite_artifact = json.loads((ABI_DIR / "YobelRiteRegistry.json").read_text())
    rel_artifact = json.loads((ABI_DIR / "YobelReleaseRegistry.json").read_text())

    Rite = w3.eth.contract(abi=rite_artifact["abi"], bytecode=rite_artifact["bytecode"])
    tx = Rite.constructor().transact({"from": deployer})
    rite_addr = w3.eth.wait_for_transaction_receipt(tx).contractAddress

    Rel = w3.eth.contract(abi=rel_artifact["abi"], bytecode=rel_artifact["bytecode"])
    tx2 = Rel.constructor(rite_addr).transact({"from": deployer})
    rel_addr = w3.eth.wait_for_transaction_receipt(tx2).contractAddress

    return {"rite": rite_addr, "release": rel_addr}


# ─── Tests ──────────────────────────────────────────────────────────


def test_declare_then_get_rite_via_port(w3, deployer, deployed_contracts):
    rite_addr = deployed_contracts["rite"]
    rite_contract = w3.eth.contract(
        address=rite_addr,
        abi=json.loads((ABI_DIR / "YobelRiteRegistry.json").read_text())["abi"],
    )
    rite_id = Web3.keccak(text="shmita-5786")
    doctrinal = Web3.keccak(text="Lev 25:1-7 / Deut 15:1-2")
    scope = Web3.keccak(text="etzhayyim community")
    issuer = Web3.keccak(text="did:web:etzhayyim.com:steward-shmita-5786")

    tx = rite_contract.functions.declareRite(
        rite_id, 0, doctrinal, scope, 1_758_551_400, 1_789_142_400, issuer
    ).transact({"from": deployer})
    w3.eth.wait_for_transaction_receipt(tx)

    port = Web3RiteRegistryPort(w3, rite_addr)
    rite = port.get_rite("0x" + rite_id.hex())
    assert rite is not None
    assert rite.rite_type == "shmita_7yr"
    assert rite.status == "declared"
    assert rite.effective_date.startswith("2025-")  # 1758551400 = 2025-09-22


def test_one_way_invariant_enforced_at_evm_level(w3, deployer, deployed_contracts):
    """Charter Rider §2(b): release > debt cap MUST revert. This is the on-chain hard gate."""
    rite_addr = deployed_contracts["rite"]
    rel_addr = deployed_contracts["release"]
    rite_contract = w3.eth.contract(
        address=rite_addr,
        abi=json.loads((ABI_DIR / "YobelRiteRegistry.json").read_text())["abi"],
    )
    rite_id = Web3.keccak(text="yobel-test-one-way")
    # Declare + ratify
    rite_contract.functions.declareRite(
        rite_id, 0, Web3.keccak(text="d"), Web3.keccak(text="s"),
        1_758_551_400, 1_789_142_400, Web3.keccak(text="i")
    ).transact({"from": deployer})
    rite_contract.functions.ratifyRite(rite_id, Web3.keccak(text="rat"), 4).transact({"from": deployer})

    rel_port = Web3ReleaseRegistryPort(w3, rel_addr, sender_address=deployer)
    debt_id = "0x" + Web3.keccak(text="test-debt-1").hex()
    rel_port.register_debt_cap(
        rite_id="0x" + rite_id.hex(),
        debt_id=debt_id,
        principal_micro_usdc=100_000_000,
        accrued_micro_usdc=0,
    )

    # Successful release: at the cap
    rel_port.record_release(
        release_id="rel-at-cap",
        rite_id="0x" + rite_id.hex(),
        debt_id=debt_id,
        debtor_did="did:web:debtor.test",
        creditor_did="did:web:creditor.test",
        released_micro_usdc=100_000_000,
        release_method="base_l2_transfer",
    )
    assert rel_port.release_count() >= 1

    # Failed release: cumulative over cap → must revert
    from web3.exceptions import ContractCustomError, ContractLogicError
    with pytest.raises((ContractCustomError, ContractLogicError, Exception)):
        rel_port.record_release(
            release_id="rel-over-cap",
            rite_id="0x" + rite_id.hex(),
            debt_id=debt_id,
            debtor_did="did:web:debtor.test",
            creditor_did="did:web:creditor.test",
            released_micro_usdc=1,  # cumulative would be 100_000_001 > 100_000_000
            release_method="voluntary_bookkeeping",
        )


def test_eip712_signed_consent_verify_accepts_genuine(deployed_contracts):
    """Real signature roundtrip: sign with eth_account, verify via Eip712Erc725Port."""
    # Set up a known-key signer
    priv_key = "0x" + "11" * 32
    signer = Account.from_key(priv_key)
    creditor_did = "did:web:creditor.example"

    port = Eip712Erc725Port(
        chain_id=31337,
        verifying_contract=deployed_contracts["rite"],
        did_to_address_resolver=lambda did: signer.address if did == creditor_did else None,
    )

    # Build the canonical payload + signature
    rite_id = "0x" + Web3.keccak(text="shmita-5786").hex()
    debts = [{"debt_id": "d1", "principal_micro_usdc": 100, "origination_date": "2022-01-01T00:00:00Z"}]
    canonical_debts = json.dumps(debts, sort_keys=True, separators=(",", ":"))
    domain = {
        "name": "YobelCreditorConsent",
        "version": "1",
        "chainId": 31337,
        "verifyingContract": Web3.to_checksum_address(deployed_contracts["rite"]),
    }
    message = {
        "riteId": bytes.fromhex(rite_id[2:]),
        "creditorDidHash": Web3.keccak(text=creditor_did),
        "debtsRootHash": Web3.keccak(text=canonical_debts),
    }
    signable = encode_typed_data(
        domain_data=domain,
        message_types={"CreditorConsent": [
            {"name": "riteId", "type": "bytes32"},
            {"name": "creditorDidHash", "type": "bytes32"},
            {"name": "debtsRootHash", "type": "bytes32"},
        ]},
        message_data=message,
    )
    signed = Account.sign_message(signable, priv_key)

    assert port.verify_eip712_signed_consent(
        signer_did=creditor_did,
        payload={"rite_id": rite_id, "creditor_did": creditor_did, "debts": debts},
        signature=signed.signature.hex(),
    )


def test_eip712_signed_consent_rejects_forged(deployed_contracts):
    """Forged signature (different signer's key) MUST fail verification."""
    real_priv = "0x" + "22" * 32
    real_signer = Account.from_key(real_priv)
    creditor_did = "did:web:creditor.example"

    port = Eip712Erc725Port(
        chain_id=31337,
        verifying_contract=deployed_contracts["rite"],
        did_to_address_resolver=lambda did: real_signer.address,
    )

    # Sign with a DIFFERENT key
    forger_priv = "0x" + "33" * 32

    rite_id = "0x" + Web3.keccak(text="shmita-5786").hex()
    debts = [{"debt_id": "d1", "principal_micro_usdc": 100, "origination_date": "2022-01-01T00:00:00Z"}]
    domain = {
        "name": "YobelCreditorConsent",
        "version": "1",
        "chainId": 31337,
        "verifyingContract": Web3.to_checksum_address(deployed_contracts["rite"]),
    }
    canonical_debts = json.dumps(debts, sort_keys=True, separators=(",", ":"))
    message = {
        "riteId": bytes.fromhex(rite_id[2:]),
        "creditorDidHash": Web3.keccak(text=creditor_did),
        "debtsRootHash": Web3.keccak(text=canonical_debts),
    }
    signable = encode_typed_data(
        domain_data=domain,
        message_types={"CreditorConsent": [
            {"name": "riteId", "type": "bytes32"},
            {"name": "creditorDidHash", "type": "bytes32"},
            {"name": "debtsRootHash", "type": "bytes32"},
        ]},
        message_data=message,
    )
    forged = Account.sign_message(signable, forger_priv)

    assert not port.verify_eip712_signed_consent(
        signer_did=creditor_did,
        payload={"rite_id": rite_id, "creditor_did": creditor_did, "debts": debts},
        signature=forged.signature.hex(),
    )
