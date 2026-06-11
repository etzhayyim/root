"""test_kotoba.py — 潮目 (shionome) kotoba Datom-log writer + content-addressed DAG. ADR-2606072200."""
from __future__ import annotations

import pathlib
import tempfile

import kotoba
from _edn import load_edn
from _t import run
from weave import weave

SEED = pathlib.Path(__file__).resolve().parents[1] / "data" / "seed-capital-flow-graph.kotoba.edn"


def _g():
    return weave(load_edn(SEED))


def test_graph_datoms_are_append_only():
    datoms = kotoba.graph_datoms(_g())
    assert datoms and all(d[0] == ":db/add" for d in datoms)   # no :db/retract (非終末論)


def test_tx_cid_deterministic():
    d = kotoba.graph_datoms(_g())
    assert kotoba.tx_cid(d, "") == kotoba.tx_cid(d, "")


def test_tx_cid_depends_on_prev():
    d = kotoba.graph_datoms(_g())
    assert kotoba.tx_cid(d, "") != kotoba.tx_cid(d, "bdeadbeef")


def test_append_and_read_roundtrip():
    with tempfile.TemporaryDirectory() as dr:
        log = pathlib.Path(dr) / "log.edn"
        tx = kotoba.make_tx(kotoba.graph_datoms(_g()), tx_id=1, as_of=20260607, prev_cid="")
        cid = kotoba.append_tx(tx, log)
        back = kotoba.read_log(log)
        assert len(back) == 1
        assert back[0][":tx/cid"] == cid


def test_chain_verifies_ok():
    with tempfile.TemporaryDirectory() as dr:
        log = pathlib.Path(dr) / "log.edn"
        prev = ""
        for i in range(1, 4):
            tx = kotoba.make_tx(kotoba.graph_datoms(_g()), tx_id=i, as_of=20260607 + i, prev_cid=prev)
            prev = kotoba.append_tx(tx, log)
        v = kotoba.verify_chain(log)
        assert v["ok"] is True and v["length"] == 3


def test_head_cid_is_last():
    with tempfile.TemporaryDirectory() as dr:
        log = pathlib.Path(dr) / "log.edn"
        last = ""
        for i in range(1, 3):
            tx = kotoba.make_tx(kotoba.graph_datoms(_g()), tx_id=i, as_of=20260607 + i,
                                prev_cid=kotoba.head_cid(log))
            last = kotoba.append_tx(tx, log)
        assert kotoba.head_cid(log) == last


def test_tamper_breaks_chain():
    with tempfile.TemporaryDirectory() as dr:
        log = pathlib.Path(dr) / "log.edn"
        for i in range(1, 3):
            tx = kotoba.make_tx(kotoba.graph_datoms(_g()), tx_id=i, as_of=20260607 + i,
                                prev_cid=kotoba.head_cid(log))
            kotoba.append_tx(tx, log)
        # tamper: flip a byte in the first tx's value
        lines = log.read_text(encoding="utf-8").splitlines()
        lines[1] = lines[1].replace("US equities", "TAMPERED")
        log.write_text("\n".join(lines) + "\n", encoding="utf-8")
        assert kotoba.verify_chain(log)["ok"] is False


def test_post_datoms_status_dry_run():
    posts = [{":post/subject": "netflow", ":post/status": ":dry-run", ":post/body": "x"}]
    datoms = kotoba.post_datoms(posts)
    statuses = [d[3] for d in datoms if d[2] == ":post/status"]
    assert statuses == [":dry-run"]


def test_post_body_with_newlines_roundtrips():
    # the bug that broke the DAG: a post body has \n\n; it must survive write→read
    with tempfile.TemporaryDirectory() as dr:
        log = pathlib.Path(dr) / "log.edn"
        posts = [{":post/subject": "regime", ":post/status": ":dry-run",
                  ":post/body": "line one\n\nline two with 日本語"}]
        tx = kotoba.make_tx(kotoba.post_datoms(posts), tx_id=1, as_of=20260607, prev_cid="")
        kotoba.append_tx(tx, log)
        assert kotoba.verify_chain(log)["ok"] is True


if __name__ == "__main__":
    run("kotoba", [(n, f) for n, f in sorted(globals().items())
                   if n.startswith("test_") and callable(f)])
