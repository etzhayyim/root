#!/usr/bin/env python3
"""Validate the CAD-feature ↔ BOM binding for a giemon robot.

Tightens the loose `:part/sim-feature` link: every part's `:part/sim-feature`
must resolve to a REAL feature in the sim (a `<link>` or `<joint>` name in the
robot's URDF). Reports invalid bindings (gate-worthy), bound vs unbound parts,
and sim features that no part covers.

Usage:  python3 sim_part_binding.py <robot.urdf> <parts.edn>
Exit:   non-zero if any :part/sim-feature does not resolve to a URDF feature.
"""
import re
import sys
from pathlib import Path

# reuse the EDN reader from the generator
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "e7m-sim/scenes/giemon_kabitori"))
from sbom_gen import parse_edn  # noqa: E402


def urdf_features(text: str) -> set:
    # <link name="..."> and <joint name="...">
    return set(re.findall(r'<(?:link|joint)\s+name="([^"]+)"', text))


def main():
    if len(sys.argv) < 3:
        sys.exit("usage: sim_part_binding.py <robot.urdf> <parts.edn>")
    urdf = Path(sys.argv[1])
    edn = Path(sys.argv[2])
    feats = urdf_features(urdf.read_text(encoding="utf-8"))
    doc = parse_edn(edn.read_text(encoding="utf-8"))
    parts = doc["bom/parts"]

    invalid, bound, unbound = [], [], []
    covered = set()
    for p in parts:
        sf = p.get("part/sim-feature")
        if not sf:
            unbound.append(p["part/id"])
        elif sf in feats:
            bound.append((p["part/id"], sf))
            covered.add(sf)
        else:
            invalid.append((p["part/id"], sf))

    uncovered = sorted(feats - covered)

    print(f"URDF {urdf.name}: {len(feats)} features ({len(feats & covered)} covered)")
    print(f"parts {edn}: {len(parts)} ({len(bound)} bound / {len(unbound)} unbound / {len(invalid)} INVALID)")
    if bound:
        print("  bound:")
        for pid, sf in bound:
            print(f"    {pid:<22} → {sf}")
    if unbound:
        print(f"  unbound (no sim-feature): {', '.join(unbound)}")
    if uncovered:
        print(f"  uncovered sim features (no part): {', '.join(uncovered)}")
    if invalid:
        print("  INVALID (sim-feature not in URDF):")
        for pid, sf in invalid:
            print(f"    {pid} → {sf}")
        sys.exit(1)
    print("OK — all :part/sim-feature bindings resolve to real URDF features.")


if __name__ == "__main__":
    main()
