from __future__ import annotations

from electrolysis import kotoba_datoms, render_report, run_comparison


def test_actor_uses_kami_engine_simulation():
    comparison = run_comparison()
    assert comparison["actor"] == "hydrogen_electrolysis"
    assert comparison["engine"] == "kami-hydrogen-electrolysis-sim"
    assert comparison["results"]


def test_best_low_temperature_candidate():
    comparison = run_comparison()
    assert comparison["best_low_temperature"]["name"] == "cfe-zero-gap-aem-high-pressure"


def test_kotoba_datoms_include_recommendation():
    datoms = kotoba_datoms(run_comparison())
    assert any(row.get(":hydrogen.electrolysis/recommended-case") == "cfe-zero-gap-aem-high-pressure" for row in datoms)


def test_report_renders_table():
    report = render_report(run_comparison())
    assert "efficiency comparison" in report
    assert "electrical kWh/kg-H2" in report


if __name__ == "__main__":
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
    print(f"{len(tests)}/{len(tests)} passed")
