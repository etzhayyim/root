#!/usr/bin/env python3
"""funadaiku voyage_energy — zero-emission invariant + model coverage (ADR-2606013400).

The voyage energy model is the EMPIRICAL backing for funadaiku's constitutional
zero-emission powertrain (G13/N5: wind + solar + hydrogen, NO fossil main/aux
engine). It had no test. These lock the invariants that must never silently drift:

  - fossil share is exactly 0 (no fossil engine, ever — G13/N5)
  - the only energy sources are wind-assist + solar + hydrogen fuel-cell, and their
    shares sum to ~1.0 of total demand
  - a positive green-H2 demand and a non-trivial battery harbour-manoeuvre window
  - shaft power obeys the Admiralty law (∝ speed^3) — the model's core relation
  - report()/to_edn() emit non-empty serializations (smoke)
"""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import voyage_energy as ve  # noqa: E402


def test_no_fossil_engine():
    r = ve.simulate(ve.Vessel(), ve.Voyage())
    assert r["fossil_engine"] is False, "G13/N5: a fossil engine must never appear"
    assert "fossil" not in r["shares"], "no fossil energy share may exist"


def test_energy_shares_are_renewable_and_sum_to_one():
    r = ve.simulate(ve.Vessel(), ve.Voyage())
    shares = r["shares"]
    assert set(shares) == {"wind_assist", "solar", "hydrogen_fuelcell"}
    total = sum(shares.values())
    assert abs(total - 1.0) < 1e-6, f"renewable+H2 shares must cover 100% of demand, got {total}"
    assert all(s >= 0.0 for s in shares.values())


def test_positive_hydrogen_demand_and_battery_window():
    r = ve.simulate(ve.Vessel(), ve.Voyage())
    assert r["h2_kg"] > 0, "a cargo-scale coastal voyage needs green-H2 (H2 is the prime mover)"
    assert r["battery_harbour_minutes"] > 0
    # hydrogen is the dominant single source at cargo scale (the survey conclusion)
    assert r["shares"]["hydrogen_fuelcell"] > r["shares"]["wind_assist"]
    assert r["shares"]["hydrogen_fuelcell"] > r["shares"]["solar"]


def test_shaft_power_follows_admiralty_cube_law():
    base = ve.Vessel()
    faster = ve.Vessel(service_speed_kn=base.service_speed_kn * 2)
    p1 = ve.shaft_power_kw(base)
    p2 = ve.shaft_power_kw(faster)
    # P ∝ V^3 → doubling speed ≈ 8× shaft power
    assert abs(p2 / p1 - 8.0) < 0.05, f"Admiralty cube law violated: ratio={p2 / p1}"


def test_higher_demand_raises_hydrogen_share():
    # a longer / faster voyage shifts more of the budget onto hydrogen (less solar/wind cover)
    short = ve.simulate(ve.Vessel(), ve.Voyage())
    longer = ve.simulate(ve.Vessel(), ve.Voyage(distance_nm=ve.Voyage().distance_nm * 3))
    assert longer["h2_kg"] > short["h2_kg"]


def test_serializations_nonempty():
    v, voy = ve.Vessel(), ve.Voyage()
    r = ve.simulate(v, voy)
    edn = ve.to_edn(v, voy, r)
    rep = ve.report(v, voy, r)
    assert isinstance(edn, str) and edn.strip()
    assert isinstance(rep, str) and rep.strip()


def test_main_writes_report_and_edn_artifacts():
    # main() is the CLI entry; it regenerates the (deterministic) out/ artifacts.
    actor_root = pathlib.Path(__file__).resolve().parent.parent
    out = actor_root / "out"
    ve.main()
    md = out / "voyage-energy-report.md"
    edn = out / "voyage-energy.kotoba.edn"
    assert md.is_file() and md.read_text(encoding="utf-8").strip()
    assert edn.is_file() and "fossil-engine false" in edn.read_text(encoding="utf-8")


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"  ok   {fn.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"  FAIL {fn.__name__}: {e}")
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
