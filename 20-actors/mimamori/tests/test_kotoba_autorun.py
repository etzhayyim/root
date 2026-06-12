#!/usr/bin/env python3
"""mimamori R1 implementation tests — kotoba commit-DAG + match cell + autorun heartbeat."""
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "methods"))
from bond import load_seed, replay  # noqa: E402
from match import MAX_KEPT, match_cycle  # noqa: E402
from kotoba import append_tx, make_tx, read_log, verify_chain, head_cid  # noqa: E402
from autorun import run_cycle  # noqa: E402

SEED = load_seed(HERE / "data" / "seed-mimamori-bonds.json")
PASS = []


def t(name, fn):
    fn()
    PASS.append(name)
    print(f"  ok  {name}")


def tmplog():
    return pathlib.Path(tempfile.mkdtemp()) / "log.kotoba.edn"


def test_match_closes_gap():
    eng = replay(SEED)
    s = match_cycle(eng, SEED["roster"])
    assert s["unkept_before"] == 8           # the baseline gap
    assert s["offers_emitted"] >= 6          # most unkept reached this pass
    # every emitted offer is a real :offered bond addressed to its parties
    offered = sum(1 for st in eng._state.values() if st == ":offered")
    assert offered >= s["offers_emitted"]


def test_match_capacity_cap():
    eng = replay(SEED)
    match_cycle(eng, SEED["roster"])
    for did in SEED["roster"]:
        load = sum(1 for b in eng.bonds_of(did)
                   if b["keeper"] == did and b["state"] in (":active", ":offered"))
        assert load <= MAX_KEPT              # keeping is covenant, not a queue


def test_match_aggregate_only():
    s = match_cycle(replay(SEED), SEED["roster"])
    assert all(isinstance(v, int) for v in s.values())   # counts only, never names (G5)


def test_chain_appends_and_verifies():
    log = tmplog()
    cid1 = append_tx(make_tx([[":db/add", "e1", ":mishmeret.bond/cycle", 1]],
                             tx_id=1, as_of=1, prev_cid=""), log)
    cid2 = append_tx(make_tx([[":db/add", "e2", ":mishmeret.bond/cycle", 2]],
                             tx_id=2, as_of=2, prev_cid=cid1), log)
    assert head_cid(log) == cid2
    v = verify_chain(log)
    assert v["ok"] and v["length"] == 2


def test_tamper_detect():
    log = tmplog()
    cid1 = append_tx(make_tx([[":db/add", "e1", ":mishmeret.bond/cycle", 1]],
                             tx_id=1, as_of=1, prev_cid=""), log)
    append_tx(make_tx([[":db/add", "e2", ":mishmeret.bond/cycle", 2]],
                      tx_id=2, as_of=2, prev_cid=cid1), log)
    txt = log.read_text(encoding="utf-8").replace('"e1"', '"eX"', 1)
    log.write_text(txt, encoding="utf-8")
    v = verify_chain(log)
    assert not v["ok"] and v["broken_at"] == 0           # earliest tamper breaks the DAG


def test_autorun_deterministic_and_resume_safe():
    log_a, log_b = tmplog(), tmplog()
    s1 = run_cycle(SEED, log_a)
    s2 = run_cycle(SEED, log_b)
    assert s1["cid"] == s2["cid"]                        # same seed+cycle → same CID
    s3 = run_cycle(SEED, log_a)                          # resume: cycle derives from log
    assert s3["cycle"] == 2 and s3["cid"] != s1["cid"]   # prev-linked → new CID
    assert verify_chain(log_a)["ok"] and len(read_log(log_a)) == 2


def test_autorun_summary_no_did():
    log = tmplog()
    s = run_cycle(SEED, log)
    flat = str(s)
    assert "did:" not in flat and "fictional" not in flat  # G5 aggregate-only summary
    # post-match coverage: every emitted offer moved an unkept member to pending
    assert s["coverage"]["unkept_count"] == s["unkept_before"] - s["offers_emitted"]
    assert s["offers_emitted"] >= 6


def test_log_roundtrip_preserves_datoms():
    log = tmplog()
    run_cycle(SEED, log)
    txs = read_log(log)
    attrs = {d[2] for d in txs[0][":tx/datoms"]}
    assert any(a.startswith(":mishmeret.bond/") for a in attrs)
    assert any(a.startswith(":mimamori.coverage/") for a in attrs)
    assert all(d[0] == ":db/add" for d in txs[0][":tx/datoms"])  # append-only ops


if __name__ == "__main__":
    t("match closes the unkept gap", test_match_closes_gap)
    t("match respects keeper capacity cap", test_match_capacity_cap)
    t("match summary aggregate-only (G5)", test_match_aggregate_only)
    t("commit-DAG appends + verifies", test_chain_appends_and_verifies)
    t("tamper detected at earliest break", test_tamper_detect)
    t("autorun deterministic + resume-safe", test_autorun_deterministic_and_resume_safe)
    t("autorun summary has no DID (G5)", test_autorun_summary_no_did)
    t("log roundtrip preserves :db/add datoms", test_log_roundtrip_preserves_datoms)
    print(f"test_kotoba_autorun: {len(PASS)}/8 green")
