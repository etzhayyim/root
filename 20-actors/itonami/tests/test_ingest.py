#!/usr/bin/env python3
"""itonami 営み — R3 SCADA/OT scan-cycle ingest tests (ADR-2606082300). Pure stdlib."""
import sys
import pathlib

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))

from analyze import load, analyze, read_edn  # noqa: E402
import ingest  # noqa: E402

STREAM = ACTOR_DIR / "data" / "seed-scancycle-stream.kotoba.edn"
OPS = ACTOR_DIR / "data" / "seed-factory-ops.kotoba.edn"


def _datoms():
    return ingest.parse_scan_datoms(STREAM.read_text(encoding="utf-8"))


def test_parse_scan_datoms():
    d = _datoms()
    assert len(d) == 12 * 7, f"expected 12 reports × 7 attrs, got {len(d)}"
    for e, a, v, tx, op in d:
        assert a.startswith(":scan/") and op == ":add"


def test_fold_reconstructs_ticks():
    ticks = ingest.fold_to_ticks(_datoms())
    # 2 stations × 3 intervals = 6 ticks
    assert len(ticks) == 6
    stations = {tk[":tick/station"] for tk in ticks}
    assert stations == {":st.cab-weld", ":st.paint"}


def test_energy_wh_to_kwh_conversion():
    ticks = ingest.fold_to_ticks(_datoms())
    cab0 = next(tk for tk in ticks if tk[":tick/station"] == ":st.cab-weld" and tk[":tick/t"] == 0)
    # 25000 + 25000 Wh → 50 kWh
    assert cab0[":tick/kwh"] == 50.0
    assert cab0[":tick/interval-s"] == 3600.0  # 1800 + 1800
    assert cab0[":tick/cycles"] == cab0[":tick/good"] + cab0[":tick/scrap"]


def test_ingested_cab_weld_matches_ops_seed():
    """The fold must reproduce the hand-authored cab-weld ticks exactly (cross-check)."""
    ingested = {tk[":tick/t"]: tk for tk in ingest.fold_to_ticks(_datoms())
                if tk[":tick/station"] == ":st.cab-weld"}
    _, seed_ticks = load(OPS)
    seed_cab = {tk[":tick/t"]: tk for tk in seed_ticks if tk[":tick/station"] == ":st.cab-weld"}
    assert set(ingested) == set(seed_cab)
    for t in seed_cab:
        for k in (":tick/good", ":tick/scrap", ":tick/cycles", ":tick/kwh",
                  ":tick/state", ":tick/interval-s"):
            assert ingested[t][k] == seed_cab[t][k], f"t={t} {k}: {ingested[t][k]} != {seed_cab[t][k]}"


def test_most_severe_state_wins_no_hidden_stop():
    """If any report in a window is idle/down, the tick state reflects the stop (not averaged)."""
    paint1 = next(tk for tk in ingest.fold_to_ticks(_datoms())
                  if tk[":tick/station"] == ":st.paint" and tk[":tick/t"] == 1)
    assert paint1[":tick/state"] == ":idle"


def test_ingested_ticks_feed_analyze():
    """End-to-end: scan datoms → ticks → analyze produces well-formed OEE (the gap-(3) loop)."""
    ticks = ingest.fold_to_ticks(_datoms())
    stations, _ = load(OPS)
    res = analyze(stations, ticks)
    for sid in (s for s in res if not s.startswith("_")):
        assert 0.0 <= res[sid]["oee"] <= 1.0 + 1e-9
    # paint carries idle energy → its idle_kwh must be > 0 after ingest
    assert res[":st.paint"]["idle_kwh"] == 45.0


def test_to_tick_edn_round_trips():
    ticks = ingest.fold_to_ticks(_datoms())
    edn = ingest.to_tick_edn(ticks)
    forms = [f for f in read_edn(edn) if isinstance(f, dict) and ":tick/station" in f]
    assert len(forms) == len(ticks)
    a = {(t[":tick/station"], t[":tick/t"]): t for t in ticks}
    b = {(t[":tick/station"], t[":tick/t"]): t for t in forms}
    assert set(a) == set(b)
    for k in a:
        assert a[k][":tick/good"] == b[k][":tick/good"]
        assert a[k][":tick/kwh"] == b[k][":tick/kwh"]


def test_live_ingest_is_gated():
    """G6: a live OT socket must refuse by construction."""
    try:
        ingest.ingest_live("opc.tcp://plc:4840")
    except NotImplementedError as ex:
        assert "G6" in str(ex) and "Council" in str(ex)
    else:
        raise AssertionError("ingest_live must refuse (G6 live-OT gate)")


def test_g2_rejects_person_attr():
    """G2: a scan stream carrying a worker/person attr is rejected."""
    bad = [["scan.x", ":scan/station", ":st.a", 1, ":add"],
           ["scan.x", ":worker/id", "w-7", 2, ":add"]]
    # parse_scan_datoms only keeps :scan/* so feed fold directly with a person attr present
    try:
        ingest.fold_to_ticks(bad)
    except ValueError as ex:
        assert "G2" in str(ex)
    else:
        raise AssertionError("fold_to_ticks must reject a person/worker attr (G2)")


def test_determinism():
    a = ingest.to_tick_edn(ingest.fold_to_ticks(_datoms()))
    b = ingest.to_tick_edn(ingest.fold_to_ticks(_datoms()))
    assert a == b


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")
