"""hataori (機織) garment-robotics cells — R0 scaffold.

All cells raise RuntimeError on .solve() until a Council activation ADR enables them
(ADR-2606032100 §Design). Only state_machine transitions are unit-tested at R0.
"""
