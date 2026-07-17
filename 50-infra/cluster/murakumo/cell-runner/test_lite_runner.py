#!/usr/bin/env python3
"""lite_runner tests (ADR-2606161645). Pure stdlib; no daemons, no network — a fake cell module +
injected clock so a full `--once` tick runs offline."""
import sys
import time
import pathlib
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lite_runner as lr  # noqa: E402

CELLS_EDN = '''{:runner {:node_name_env "ETZHAYYIM_NODE_NAME"}
 :cell [{:name "FakeHeartbeatCell" :module "fakeactor.cell" :entry "fire" :node "issachar"
         :trigger {:kind "cron" :expr "42 * * * *"} :healthz_port 13099}
        {:name "OtherNodeCell" :module "x.cell" :entry "fire" :node "dan"
         :trigger {:kind "cron" :expr "42 * * * *"}}
        {:name "ListenerCell" :module "y.cell" :entry "serve" :node "issachar"
         :trigger {:kind "mst-listener" :listens_to ["foo"]}}]}'''


def _cells_root_with_fake(dr):
    root = pathlib.Path(dr) / "cells"
    (root / "fakeactor").mkdir(parents=True)
    (root / "fakeactor" / "cell.py").write_text(
        "def fire():\n    return {'cid': 'bfakecid0000000000'}\n", encoding="utf-8")
    return root


def test_load_cells_filters_node_and_cron():
    with tempfile.TemporaryDirectory() as dr:
        reg = pathlib.Path(dr) / "cells.edn"
        reg.write_text(CELLS_EDN, encoding="utf-8")
        cells = lr.load_cells(reg, "issachar")
        names = {c[":name"] for c in cells}
        assert names == {"FakeHeartbeatCell"}, f"expected only issachar cron cell, got {names}"
        # OtherNodeCell (dan) and ListenerCell (non-cron) excluded


def test_cron_minute_parsing():
    assert lr.cron_minute("42 * * * *") == {42}
    assert lr.cron_minute("*/15 * * * *") == {0, 15, 30, 45}
    assert lr.cron_minute("*") == set(range(60))
    assert lr.cron_minute("0,30 * * * *") == {0, 30}


def test_fire_cell_imports_and_calls():
    with tempfile.TemporaryDirectory() as dr:
        root = _cells_root_with_fake(dr)
        status, detail = lr.fire_cell({":module": "fakeactor.cell", ":entry": "fire"}, root)
        assert status == ":ok", f"fire failed: {detail}"
        assert detail.startswith("bfakecid")


def test_fire_cell_error_is_caught_not_raised():
    status, detail = lr.fire_cell({":module": "nonexistent.module", ":entry": "fire"}, "/tmp")
    assert status == ":error" and "ModuleNotFoundError" in detail


def test_ops_log_commit_dag_appendonly():
    with tempfile.TemporaryDirectory() as dr:
        log = pathlib.Path(dr) / "ops.kotoba.edn"
        c1 = lr.append_run(log, node="issachar", cell="FakeHeartbeatCell", status=":ok",
                           detail="bfakecid", as_of=202606161642)
        c2 = lr.append_run(log, node="issachar", cell="FakeHeartbeatCell", status=":ok",
                           detail="bfakecid", as_of=202606161742)
        txs = lr._read_log(log)
        assert len(txs) == 2 and txs[1][":tx/prev"] == c1 and txs[1][":tx/cid"] == c2
        # chain verifies (recompute)
        prev = ""
        for tx in txs:
            assert tx[":tx/cid"] == lr._tx_cid(tx[":tx/datoms"], prev)
            prev = tx[":tx/cid"]


def test_run_once_fires_due_cell_and_records():
    with tempfile.TemporaryDirectory() as dr:
        reg = pathlib.Path(dr) / "cells.edn"
        reg.write_text(CELLS_EDN, encoding="utf-8")
        root = _cells_root_with_fake(dr)
        ops = pathlib.Path(dr) / "ops.kotoba.edn"
        # clock pinned to :42 so the cron cell is due
        clock = lambda: time.struct_time((2026, 6, 16, 17, 42, 0, 0, 167, -1))  # noqa: E731
        st = lr.run("issachar", reg, root, ops, once=True, clock=clock)
        assert st["last"]["FakeHeartbeatCell"]["status"] == ":ok"
        flat = [d for tx in lr._read_log(ops) for d in tx[":tx/datoms"]]
        assert any(d[2] == ":cell.run/cell" and d[3] == "FakeHeartbeatCell" for d in flat)
        assert any(d[2] == ":cell.run/status" and d[3] == ":ok" for d in flat)


def test_run_once_not_due_minute_fires_nothing():
    with tempfile.TemporaryDirectory() as dr:
        reg = pathlib.Path(dr) / "cells.edn"
        reg.write_text(CELLS_EDN, encoding="utf-8")
        root = _cells_root_with_fake(dr)
        ops = pathlib.Path(dr) / "ops.kotoba.edn"
        clock = lambda: time.struct_time((2026, 6, 16, 17, 10, 0, 0, 167, -1))  # noqa: E731 (:10 ≠ :42)
        lr.run("issachar", reg, root, ops, once=True, clock=clock)
        # the durable signal: nothing was recorded to this run's (fresh) ops log
        assert lr._read_log(ops) == [], "a non-due minute must fire nothing"


import deploy_node as dn  # noqa: E402

_STATUS = "100.89.204.30 issachar com-junkawasaki@ macOS -\n100.89.204.31 judah com-junkawasaki@ macOS -\n100.98.142.59 dan com-junkawasaki@ macOS -\n"


def test_deploy_actors_for_node_from_real_registry():
    # the committed cells.edn places SukashiObservatoryHeartbeatCell (module sukashi.cell) on issachar
    actors = dn.actors_for_node(dn.REGISTRY, "issachar")
    assert "sukashi" in actors, f"sukashi not resolved for issachar: {actors}"


def test_deploy_plan_has_stage_actor_and_daemon():
    pl = dn.plan("issachar")
    kinds = [k for k, _ in pl["steps"]]
    assert "stage-actor" in kinds and "install-daemon" in kinds
    assert "sukashi" in pl["actors"]


def test_deploy_executes_injected_runner_steps():
    calls = []
    def runner(kind, **kw):
        calls.append(kind)
    res = dn.deploy("issachar", runner=runner, status_text=_STATUS)
    assert res["status"] == "deployed" and res["ip"] == "100.89.204.30"
    # the codified deploy: mkdirs → put lite_runner → cells.edn → stage each actor → install daemon
    assert calls[0] == "mkdirs" and "put-file" in calls and "git-show" in calls
    assert "git-archive" in calls and calls[-1] == "install-daemon"


def test_deploy_mio_uses_pinned_west_repository():
    calls = []
    def runner(kind, **kw):
        calls.append((kind, kw))
    res = dn.deploy("judah", runner=runner, status_text=_STATUS)
    mio = next(kw for kind, kw in calls if kind == "git-archive-repo")
    assert res["status"] == "deployed"
    assert mio["repository"] == "orgs/etzhayyim/com-etzhayyim-mio"
    assert mio["revision"] == "a0b6697f3708d67e0bda2a23fe4ab853555aed0d"


def test_tawami_source_is_pinned_west_repository():
    source = dn.actor_source("tawami")
    assert source[":path"] == "orgs/etzhayyim/com-etzhayyim-tawami"
    assert source[":revision"] == "f8c8011124319953c5775beb3879d299e433c48f"


def test_energy_order_sibling_sources_are_pinned_west_repositories():
    expected = {
        "okibi": "2cffb76d15da8c37ceb212bed817c8c5700e0eb6",
        "toi": "973cb4deacff97b9b5259053fdf36d9c940f3552",
        "yudane": "6e80373d226add518a9eb841ced288b626c18a5a",
    }
    for actor, revision in expected.items():
        source = dn.actor_source(actor)
        assert source[":kind"] == ":west-repository"
        assert source[":revision"] == revision


def test_deploy_unreachable_node():
    res = dn.deploy("ghost", runner=lambda *a, **k: None, status_text=_STATUS)
    assert res["status"] == "unreachable"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")
