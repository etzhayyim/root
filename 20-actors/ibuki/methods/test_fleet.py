"""test_fleet.py — 息吹 (ibuki) R1 fleet binding: 18,342 organisms on durable checkpoints.

ADR-2606101200 §R1. Uses the real committed registry (00-contracts/actor-registry/
unispsc.json) for universe/partition facts, and a small synthetic registry for sweep
mechanics (hermetic + fast).
"""
from __future__ import annotations

import json
import pathlib
import tempfile

import datoms
import fleet
from _t import expect_raises, run


def _synthetic_registry(dr, n=10, segment=10):
    """A tiny registry file shaped exactly like the real one."""
    agents = [{"code": f"{segment}{i:06d}", "handle": f"c{segment}{i:06d}",
               "did": f"did:web:etzhayyim.com:actor:c{segment}{i:06d}",
               "title": f"Synthetic organism {i}", "segment": str(segment)}
              for i in range(n)]
    p = pathlib.Path(dr) / "registry.json"
    p.write_text(json.dumps({"agents": agents}), encoding="utf-8")
    return p


def _fleet_run(dr, cycles, *, batch, fresh, reg=None, shard=0):
    return fleet.fleet_autorun(
        cycles, shard_index=shard, batch_size=batch, fresh=fresh,
        log_path=pathlib.Path(dr) / "log.edn",
        queue_path=pathlib.Path(dr) / "queue.ndjson",
        registry_path=reg)


# ── the real universe (committed monorepo registry) ───────────────────────


def test_real_registry_is_the_full_fleet():
    agents = fleet.load_registry()
    assert len(agents) == 18342
    sample = agents[0]
    assert set(sample) == {"code", "did", "title", "segment"}
    assert sample["did"].startswith("did:web:etzhayyim.com:actor:")


def test_shards_partition_the_fleet_completely():
    agents = fleet.load_registry()
    named = [fleet.shard_agents(agents, i) for i in (0, 1, 2)]
    codes = [c["code"] for s in named for c in s]
    assert len(codes) == 18342 and len(set(codes)) == 18342    # disjoint + complete
    assert len(fleet.shard_agents(agents, -1)) == 18342        # jacob = whole fleet


def test_unknown_shard_raises():
    expect_raises(lambda: fleet.shard_agents([], 7), contains="unknown shard")


def test_resolve_shard_env_order():
    import os
    saved = {k: os.environ.pop(k, None) for k in
             ("UNISPSC_ORGANISM_SHARD_ALL", "UNISPSC_ORGANISM_SHARD_INDEX", "ETZHAYYIM_NODE")}
    try:
        assert fleet.resolve_shard() == 0
        os.environ["ETZHAYYIM_NODE"] = "dan"
        assert fleet.resolve_shard() == 2
        os.environ["UNISPSC_ORGANISM_SHARD_INDEX"] = "1"
        assert fleet.resolve_shard() == 1
        os.environ["UNISPSC_ORGANISM_SHARD_ALL"] = "1"
        assert fleet.resolve_shard() == -1
    finally:
        for k, v in saved.items():
            os.environ.pop(k, None)
            if v is not None:
                os.environ[k] = v


# ── sweep mechanics (synthetic registry, hermetic) ────────────────────────


def test_durable_cursor_sweeps_whole_shard():
    with tempfile.TemporaryDirectory() as dr:
        reg = _synthetic_registry(dr, n=10)
        res = _fleet_run(dr, 5, batch=4, fresh=True, reg=reg)
        # 5 beats × batch 4 over 10 organisms: every organism ticked ≥1 time
        assert res["organisms_alive"] == 10
        assert res["cursor"] == (5 * 4) % 10


def test_crash_resume_equals_uninterrupted_sweep():
    """The R1 durability claim at fleet scale: kill the runner mid-sweep, resume — the head
    CID is byte-identical to never having crashed (cursor + organism state all on-log)."""
    with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
        reg1 = _synthetic_registry(d1, n=10)
        _fleet_run(d1, 2, batch=4, fresh=True, reg=reg1)
        resumed = _fleet_run(d1, 3, batch=4, fresh=False, reg=reg1)   # new process, resumes
        reg2 = _synthetic_registry(d2, n=10)
        straight = _fleet_run(d2, 5, batch=4, fresh=True, reg=reg2)
        assert resumed["head"] == straight["head"]


def test_deterministic_head_cid():
    with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
        r1 = _fleet_run(d1, 3, batch=5, fresh=True, reg=_synthetic_registry(d1))
        r2 = _fleet_run(d2, 3, batch=5, fresh=True, reg=_synthetic_registry(d2))
        assert r1["head"] == r2["head"]


def test_index_log_matches_per_entity_folds():
    """The single-pass fleet index must recover exactly what the O(n²) per-entity folds
    would — same events, same heartbeat state."""
    import heartbeat
    with tempfile.TemporaryDirectory() as dr:
        reg = _synthetic_registry(dr, n=6)
        _fleet_run(dr, 3, batch=6, fresh=True, reg=reg)
        txs = datoms.read_log(pathlib.Path(dr) / "log.edn")
        idx = fleet.index_log(txs)
        for code in list(idx.hb)[:3]:
            assert idx.events[code] == datoms.events_for(txs, code)
            assert idx.hb[code] == heartbeat.replay(txs, code)


def test_incremental_drain_never_reprepares():
    with tempfile.TemporaryDirectory() as dr:
        reg = _synthetic_registry(dr, n=4)
        _fleet_run(dr, 4, batch=4, fresh=True, reg=reg)
        txs = datoms.read_log(pathlib.Path(dr) / "log.edn")
        queue_lines = len((pathlib.Path(dr) / "queue.ndjson")
                          .read_text(encoding="utf-8").splitlines())
        prepared = [d for tx in txs for d in tx[":tx/datoms"] if d[2] == ":drain/status"]
        assert len(prepared) == queue_lines          # 1 envelope per line, EXACTLY once
        assert {d[3] for d in prepared} == {":prepared"}


def test_fleet_posts_are_dry_run_and_member_signed():
    with tempfile.TemporaryDirectory() as dr:
        _fleet_run(dr, 2, batch=8, fresh=True, reg=_synthetic_registry(dr))
        txs = datoms.read_log(pathlib.Path(dr) / "log.edn")
        flat = [d for tx in txs for d in tx[":tx/datoms"]]
        assert {d[3] for d in flat if d[2] == ":post/status"} == {":dry-run"}      # G8
        assert {d[3] for d in flat if d[2] == ":drain/server-held-key"} == {False}  # G7


def test_real_fleet_slice_beats_on_the_log():
    """Smoke at real-fleet scale: one beat of a 64-organism batch from each shard of the
    ACTUAL 18,342-code registry, all on one durable log."""
    with tempfile.TemporaryDirectory() as dr:
        for shard in (0, 1, 2):
            res = fleet.fleet_autorun(
                1, shard_index=shard, batch_size=64, fresh=False,
                log_path=pathlib.Path(dr) / f"log-{shard}.edn",
                queue_path=pathlib.Path(dr) / f"queue-{shard}.ndjson")
            assert res["organisms_alive"] == 64
            assert res["chain"]["ok"] is True
            assert res["shard"] in ("joseph", "issachar", "dan")


def test_fleet_event_entities_never_shadowed():
    """Same regression as autorun (2026-06-10 health audit): one event_datoms call per
    organism-beat — no jev-* entity may carry two kind assertions."""
    import collections
    with tempfile.TemporaryDirectory() as dr:
        _fleet_run(dr, 6, batch=6, fresh=True, reg=_synthetic_registry(dr, n=6))
        kinds = collections.Counter()
        for tx in datoms.read_log(pathlib.Path(dr) / "log.edn"):
            for _op, e, a, _v in tx[":tx/datoms"]:
                if a == ":joucho.event/kind":
                    kinds[e] += 1
        assert kinds and max(kinds.values()) == 1


def test_fleet_health_checkpoint_past_10_beats():
    """Regression: fleet_beat's periodic health audit (beat % HEALTH_EVERY == 0) needs the
    log — a >=10-beat fleet run must not raise (latent NameError shipped because every prior
    fleet test ran <10 beats)."""
    with tempfile.TemporaryDirectory() as dr:
        reg = _synthetic_registry(dr, n=6)
        res = _fleet_run(dr, 10, batch=6, fresh=True, reg=reg)
        assert res["chain"]["ok"] is True
        txs = datoms.read_log(pathlib.Path(dr) / "log.edn")
        assert any(d[2] == ":health/healthy"
                   for tx in txs for d in tx[":tx/datoms"])


def test_fleet_grows_a_food_web_and_stays_healthy():
    """生態系 at fleet scale: a batch of co-active organisms forms a producer->router->
    decomposer web; humanity is fed; the colony stays healthy + unsaturated over a long run."""
    import ecosystem as eco
    import health
    with tempfile.TemporaryDirectory() as dr:
        reg = _synthetic_registry(dr, n=12)
        _fleet_run(dr, 40, batch=12, fresh=True, reg=reg)
        txs = datoms.read_log(pathlib.Path(dr) / "log.edn")
        web = eco.web_report(txs)
        assert web["commons_metabolites"] > 0 and web["relays"] > 0
        rep = health.audit(txs)
        assert "ecosystem-starved" not in {f["rule"] for f in rep["findings"]}
        # no organism pins an axis at the clamp (satiation holds at fleet scale too)
        assert not any(f["rule"] == "axis-saturation" for f in rep["findings"])


def test_cell_solve_runs_a_durable_beat():
    """R2 (Council gate = PR merge): the Pregel cell RUNS the beat — offline-safe, local
    log only; it can prepare envelopes but can never post (member_submit refuses cron)."""
    import importlib.util
    cell_path = (pathlib.Path(__file__).resolve().parents[1] / "cells" / "fleet_beat"
                 / "cell.py")
    spec = importlib.util.spec_from_file_location("ibuki_fleet_cell", cell_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    with tempfile.TemporaryDirectory() as dr:
        out = mod.FleetBeatCell().solve({
            "cycles": 1, "shard": 0, "batch": 16, "fresh": True,
            "log_path": str(pathlib.Path(dr) / "log.edn"),
            "queue_path": str(pathlib.Path(dr) / "queue.ndjson")})
        assert out["beats"] == 1 and out["chain_ok"] is True
        assert out["shard"] == "joseph" and out["organisms_alive"] == 16


if __name__ == "__main__":
    run("fleet", [(n, f) for n, f in sorted(globals().items())
                  if n.startswith("test_") and callable(f)])
