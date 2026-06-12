"""kuni-umi robotics — shared infra-robotics operational substrate (R0 :representative).

This package is the canonical 3-layer reference for the planetary-infrastructure
robotics fleet (ADR-2605201400 + the 3-layer operational-substrate ADR):

  Layer 1  plant       deterministic physical-plant simulation (the kami-genesis
                       stand-in until 40-engine/kami-engine submodule is checked
                       out; honest `:representative`, sims-only per G10)
  Layer 2  control     closed-loop controllers (PID / droop) + a closed-loop
                       runner — the Python reference of the open-ot field-tier
                       WASM PLC (60-apps/etzhayyim-project-open-ot/cells/*).
                       Hard-RT servo stays in open-ot Rust; this is the
                       <=10 Hz coordination + acceptance-test reference.
  Layer 3  kinematics  install-robot motion model (planar serial arm FK/IK +
                       joint-space trajectory) — what places a panel / reaches
                       a cut point / aligns a fibre / sets a pump.

  safety               cross-cutting gates shared by every domain actor:
                       civilian-only (N1), no-server-key (G15/G7),
                       witness-quorum >=2 (G8), motion safety envelope.

Import convention (matches 20-actors/noroshi/methods): modules are flat. A
consumer adds this directory to sys.path and imports the modules directly, e.g.

    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]
                          / "kuni-umi" / "robotics"))
    from control import PID, simulate
    from kinematics import PlanarArm
    from safety import assert_civilian, witness_quorum_ok

Everything is deterministic and dependency-free (stdlib only). Live actuation is
NOT enabled here: domain `cell.py .solve()` entrypoints stay gated (Council
Lv6+; R0 = offline sim + dry-run only). This package only proves the loops
converge and the gates hold.
"""
