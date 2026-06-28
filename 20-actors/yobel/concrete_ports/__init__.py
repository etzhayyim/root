"""Concrete port implementations binding yobel cells to real backends.

Ported off python web3.py/eth_account to bb/cljc (ADR-2605201800; final py→cljc
prune). The live implementations now live in the sibling `.cljc` files —
`web3_rpc.cljc` (JSON-RPC + ABI codec), `web3_rite_registry.cljc`,
`web3_release_registry.cljc`, `eip712_erc725.cljc` — all driven by
eth-crypto-clj (no web3/eth_account). This package marker is retained only so
`concrete_ports/tests/` stays importable; no python port code remains here.
"""
