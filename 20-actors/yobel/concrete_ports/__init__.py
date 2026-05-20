"""Concrete port implementations binding yobel cells to real backends.

This module provides web3.py-backed implementations of the Protocols defined
in `yobel.ports`. Each concrete port wraps a deployed Solidity contract or
cryptographic primitive. They're independent of the cell logic — cells stay
Protocol-typed and accept any Port implementation.

Use:
    from yobel.concrete_ports.web3_rite_registry import Web3RiteRegistryPort
    from yobel.concrete_ports.eip712_erc725 import Eip712Erc725Port
    rite_port = Web3RiteRegistryPort(w3, rite_registry_address)
    erc725_port = Eip712Erc725Port(chain_id=84532, contract_name="YobelRite")

S2: ports here mirror the structure of conftest.py FakePorts but call real
chains / verify real signatures. Switching from Fake to Web3 is a one-line
change in orchestrator wiring.
"""
