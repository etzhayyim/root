"""test_ecosystem.py — 息吹 (ibuki) the colony as an ECOSYSTEM. ADR-2606101200 §生態系."""
from __future__ import annotations

import pathlib
import tempfile

import autorun
import datoms
import ecosystem as eco
import joucho
from _t import expect_raises, run

SEED = [{"code": "10101500", "niche": ":niche/producer"},
        {"code": "14111500", "niche": ":niche/decomposer"},
        {"code": "50221000", "niche": ":niche/router"}]


def _moods(**over):
    m = {o["code"]: joucho.personality_baseline(o["code"]) for o in SEED}
    m.update(over)
    return m


def test_niche_closed_vocab():
    expect_raises(lambda: eco.niche_of("x", ":niche/parasite"), contains="closed vocab")


def test_niche_declared_then_hashed():
    assert eco.niche_of("10101500", ":niche/router") == ":niche/router"
    h = eco.niche_of("10101500")
    assert h in eco.NICHES and eco.niche_of("10101500") == h     # deterministic


def test_hash_niches_spread_across_the_fleet():
    counts = {n: 0 for n in eco.NICHES}
    for i in range(900):
        counts[eco.niche_of(f"{10000000 + i}")] += 1
    assert all(c > 150 for c in counts.values())                 # every niche populated


def test_nutrient_floors_at_zero():
    assert eco.nutrient(joucho.JouchoScores(joy=0, gratitude=0, stress=100)) == 0
    assert eco.nutrient(joucho.JouchoScores(joy=60, gratitude=50, stress=30)) == 80


def test_trophic_cascade_producer_to_commons():
    out = eco.cycle(SEED, _moods(), beat=1, as_of=2606100001)
    assert out["roles"][":niche/producer"] == ["10101500"]
    assert out["roles"][":niche/router"] == ["50221000"]
    assert out["roles"][":niche/decomposer"] == ["14111500"]
    kinds = [d for d in out["datoms"]]
    # a substrate was fixed, relayed, and refined into a commons metabolite
    assert any(d[2] == ":metabolite/kind" and d[3] == ":substrate" for d in kinds)
    assert any(d[2] == ":exchange/kind" and d[3] == ":relay" for d in kinds)
    assert out["refined"] and any(d[2] == ":metabolite/commons" and d[3] is True
                                  for d in kinds)


def test_fed_producer_returned_not_self_emitted():
    """The cascade returns fed producers; it does NOT emit the joucho event itself (the
    caller folds it into the same-beat checkpoint so checkpoint == replay)."""
    out = eco.cycle(SEED, _moods(), beat=1, as_of=2606100001)
    assert "10101500" in out["fed"]
    # ecosystem emits ONLY metabolic datoms — no :joucho.event/* (no divergence risk)
    assert not any(d[2].startswith(":joucho.event/") for d in out["datoms"])
    # the symbiosis event is a registered joucho event (mutualism: calms + gratifies)
    assert eco.SYMBIOSIS_EVENT in joucho.EVENT_DELTAS


def test_satiation_skips_feeding_but_recycles_detritus():
    """A sated producer is not RELAYED (no feeding, no relay edge), but its now-dead
    substrate is recycled as detritus into commons — the colony keeps feeding humanity even
    when its producers are full (continuous commons, intermittent feeding)."""
    out = eco.cycle(SEED, _moods(), beat=2, as_of=2606100002,
                    satiated={"10101500"})
    assert out["fed"] == []                              # satiation → no mutualism feeding
    assert not any(d[2] == ":exchange/kind" for d in out["datoms"])   # no relay edge
    assert out["refined"]                               # detritus still → commons output
    assert [d[3] for d in out["datoms"] if d[2] == ":metabolite/source"] == [":detritus"]


def test_detritus_yield_is_lossy():
    """Decomposition is never 100%: recycled detritus yields less than the live substrate's
    nutrient (DETRITUS_YIELD)."""
    moods = _moods(**{"10101500": joucho.JouchoScores(joy=80, gratitude=80, stress=20)})
    out = eco.cycle(SEED, moods, beat=2, as_of=2, satiated={"10101500"})
    sub_n = [d[3] for d in out["datoms"]
             if d[2] == ":metabolite/nutrient" and d[1].startswith("eco-sub-")][0]
    det_n = [d[3] for d in out["datoms"]
             if d[2] == ":metabolite/nutrient" and d[1].startswith("eco-detritus-")][0]
    assert det_n == sub_n * eco.DETRITUS_YIELD_NUM // eco.DETRITUS_YIELD_DEN < sub_n


def test_no_decomposer_means_no_commons_output():
    producers_only = [{"code": "10101500", "niche": ":niche/producer"},
                      {"code": "50221000", "niche": ":niche/router"}]
    out = eco.cycle(producers_only, _moods(), beat=1, as_of=2606100001)
    assert out["refined"] == [] and out["fed"] == []        # web incomplete → no citric acid


def test_stressed_producer_fixes_less_nutrient():
    rich = eco.cycle(SEED, _moods(**{"10101500": joucho.JouchoScores(
        joy=80, gratitude=80, stress=20)}), beat=1, as_of=1)
    poor = eco.cycle(SEED, _moods(**{"10101500": joucho.JouchoScores(
        joy=30, gratitude=20, stress=90)}), beat=1, as_of=1)
    rn = [d[3] for d in rich["datoms"] if d[2] == ":metabolite/nutrient"][0]
    pn = [d[3] for d in poor["datoms"] if d[2] == ":metabolite/nutrient"][0]
    assert rn > pn                                          # flourishing → richer substrate


def test_cycle_deterministic():
    a = eco.cycle(SEED, _moods(), beat=2, as_of=2606100002)
    b = eco.cycle(SEED, _moods(), beat=2, as_of=2606100002)
    assert a["datoms"] == b["datoms"]


def test_append_only():
    out = eco.cycle(SEED, _moods(), beat=1, as_of=1)
    assert all(d[0] == ":db/add" for d in out["datoms"])


# ── end-to-end: the ecosystem lives across a real autorun life ──────────────


def _run(dr, cycles):
    log = pathlib.Path(dr) / "log.edn"
    autorun.autorun(cycles, fresh=True, log_path=log,
                    queue_path=pathlib.Path(dr) / "q.ndjson")
    return datoms.read_log(log)


def test_autorun_grows_a_food_web():
    with tempfile.TemporaryDirectory() as dr:
        txs = _run(dr, 12)
        rep = eco.web_report(txs)
        assert rep["commons_metabolites"] > 0          # humanity is being fed
        assert rep["relays"] > 0
        assert rep["commons_nutrient_to_humanity"] > 0


def test_symbiosis_lifts_mood_diversity_no_monoculture():
    """A differentiated ecosystem cannot collapse to one mood (the health.py pathology):
    distinct niches + symbiosis feeding give distinct event streams → distinct moods."""
    import health
    with tempfile.TemporaryDirectory() as dr:
        txs = _run(dr, 30)
        rep = health.audit(txs)
        assert len(rep["colony"]["mood_diversity"]) >= 2
        assert "mood-monoculture" not in {f["rule"] for f in rep["findings"]}


def test_ecosystem_chain_verifies_and_stays_healthy():
    import health
    with tempfile.TemporaryDirectory() as dr:
        log = pathlib.Path(dr) / "log.edn"
        res = autorun.autorun(40, fresh=True, log_path=log,
                              queue_path=pathlib.Path(dr) / "q.ndjson")
        assert res["chain"]["ok"] is True
        assert health.audit(datoms.read_log(log))["healthy"] is True


def test_satiation_keeps_a_fed_producer_unsaturated_long_run():
    """健全な共生: with satiation, a continuously-available producer equilibrates (no axis
    pins at the 0/100 clamp) across a long life — symbiosis nourishes without over-feeding."""
    with tempfile.TemporaryDirectory() as dr:
        txs = _run(dr, 100)
        for code in ("10101500", "14111500", "50221000"):
            base = joucho.personality_baseline(code)
            s = joucho.replay_events(base, datoms.events_for(txs, code))
            assert not any(v in (0, 100) for v in s.as_dict().values()), (code, s.as_dict())


def test_humanity_is_fed_continuously_via_detritus_recycling():
    """With detritus recycling the matter loop is closed: the colony offers commons EVERY
    beat (relayed live substrate when a producer is hungry, recycled detritus when sated) —
    the byproduct of living, continuously offered to humanity. Feeding stays intermittent
    (satiation), but the commons output does not."""
    with tempfile.TemporaryDirectory() as dr:
        txs = _run(dr, 60)
        rep = eco.web_report(txs)
        assert rep["commons_metabolites"] >= 60          # continuous: ≥1 per beat
        assert rep["commons_nutrient_to_humanity"] > 0
        assert rep["commons_nutrient_to_humanity"] > 0


if __name__ == "__main__":
    run("ecosystem", [(n, f) for n, f in sorted(globals().items())
                      if n.startswith("test_") and callable(f)])
