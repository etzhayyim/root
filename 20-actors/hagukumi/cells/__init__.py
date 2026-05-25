"""hagukumi Pregel cell catalog (R0 scaffold; all cells gated).

Per ADR-2605261030. Activation requires Council Lv6+ ratify + ≥1 pediatrician
+ ≥1 geriatrician on Council medical advisory + ADR-2605181100 encrypted-
record framework production-deployed in CI.

Privacy invariant: R0 cells raise RuntimeError on import-equivalent
.solve() call specifically to prevent plaintext data flow before encrypted-
record framework is Council-attested production-ready.
"""
