#!/usr/bin/env python3
"""mimamori cell-runner entry tests — fire() contract + registry consistency."""
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "methods"))
import cell  # noqa: E402

PASS = []


def t(name, fn):
    fn()
    PASS.append(name)
    print(f"  ok  {name}")


def test_fire_runs_one_cycle():
    log = pathlib.Path(tempfile.mkdtemp()) / "log.kotoba.edn"
    s1 = cell.fire(str(log))
    assert s1["cycle"] == 1 and s1["chain_length"] == 1
    assert s1["offers_emitted"] >= 6 and s1["shakai"]["minted_units"] == 2
    s2 = cell.fire(str(log))                  # next fire = next cycle (resume from log)
    assert s2["cycle"] == 2 and s2["cid"] != s1["cid"]


def test_fire_summary_no_did():
    log = pathlib.Path(tempfile.mkdtemp()) / "log.kotoba.edn"
    s = cell.fire(str(log))
    assert "did:" not in str(s) and "fictional" not in str(s)   # G5 aggregate-only


def test_registry_entry_consistent():
    edn = (HERE.parents[1] / "50-infra" / "cluster" / "murakumo" / "cell-runner"
           / "cells.edn").read_text(encoding="utf-8")
    assert edn.count('MimamoriHeartbeatCell') == 1
    assert ':module "mimamori.cell" :entry "fire"' in edn       # contract matches this file
    assert hasattr(cell, "fire")
    assert ':expr "23 * * * *"' in edn                          # off-minute, collision-free
    assert edn.count(':healthz_port 13080') == 1                # unique port


if __name__ == "__main__":
    t("fire() runs one resume-safe cycle", test_fire_runs_one_cycle)
    t("fire() summary has no DID (G5)", test_fire_summary_no_did)
    t("cells.edn entry matches the module contract", test_registry_entry_consistent)
    print(f"test_cell: {len(PASS)}/3 green")
