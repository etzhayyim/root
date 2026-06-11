"""tsutae cells — R0 scaffold (ADR-2605261300).

8 Pregel cells in linear smartphone assembly sequence:

    pcb_smt → chassis_assembly → display_attachment → firmware_load
       → final_qc → packaging → device_attestation → recycling_intake (EOL)

All cells are import-clean but raise RuntimeError on .solve() until Council Lv6+
ratifies the R1 activation ADR (2605261315, reserved). The pure, langgraph-free
state_machine.py transition functions ARE exercised (see test_state_machines.py)
so the smartphone-manufacturing workflow + constitutional guards (G9 open-SoC,
G6 mic kill switch, G3 repair-rightful) have real coverage in R0.
"""
