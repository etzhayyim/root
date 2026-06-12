#!/usr/bin/env python3
"""mimamori coverage tests — aggregate-only (G5): no DID ever appears in the report."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "methods"))
from bond import load_seed  # noqa: E402
from coverage_report import coverage, render  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent.parent
PASS = []


def t(name, fn):
    fn()
    PASS.append(name)
    print(f"  ok  {name}")


def test_aggregates_on_seed():
    c = coverage(load_seed(HERE / "data" / "seed-mimamori-bonds.json"))
    assert c["members_total"] == 12
    # active keepers: bet (by aleph), gimel (by bet), he (by vav after relay) = 3
    assert c["with_keeper"] == 3
    assert c["offers_pending"] == 1          # het (offer from zayin, unanswered)
    assert c["unkept_count"] == 8            # the gap, counted not named
    assert c["relays"] == 1
    assert c["with_keeper"] + c["offers_pending"] + c["unkept_count"] == c["members_total"]


def test_g5_no_did_in_report():
    rep = render(coverage(load_seed(HERE / "data" / "seed-mimamori-bonds.json")))
    assert "did:" not in rep                 # no person named, ever
    assert "fictional" not in rep
    assert "unkept" in rep                   # the gap IS reported — as a count


def test_deterministic_report():
    seed = load_seed(HERE / "data" / "seed-mimamori-bonds.json")
    assert render(coverage(seed)) == render(coverage(seed))


if __name__ == "__main__":
    t("aggregates correct on synthetic seed", test_aggregates_on_seed)
    t("G5 no DID / no name in report", test_g5_no_did_in_report)
    t("deterministic report", test_deterministic_report)
    print(f"test_coverage: {len(PASS)}/3 green")
