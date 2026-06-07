"""test_lexicons.py — 潮目 (shionome) lexicon well-formedness. ADR-2606072200."""
from __future__ import annotations

import pathlib

from _edn import load_edn
from _t import run

LEX = pathlib.Path(__file__).resolve().parents[1] / "lex"
NAMES = ("capitalFlowObservation.edn", "bucketSnapshot.edn", "rotationFinding.edn", "networkPost.edn")


def test_all_load_and_have_id():
    for n in NAMES:
        lex = load_edn(LEX / n)
        assert lex[":lexicon"] == 1
        assert str(lex[":id"]).startswith("com.etzhayyim.shionome.")


def test_each_has_main_record():
    for n in NAMES:
        lex = load_edn(LEX / n)
        main = lex[":defs"][":main"]
        assert main[":type"] == "record"
        assert ":record" in main


def test_required_lists_nonempty():
    for n in NAMES:
        rec = load_edn(LEX / n)[":defs"][":main"][":record"]
        assert isinstance(rec[":required"], list) and rec[":required"]


def test_namespaces_unique():
    ids = [load_edn(LEX / n)[":id"] for n in NAMES]
    assert len(ids) == len(set(ids))


def test_capitalflow_required_has_no_trade_notice():
    rec = load_edn(LEX / "capitalFlowObservation.edn")[":defs"][":main"][":record"]
    assert "noTradeNotice" in rec[":required"]


if __name__ == "__main__":
    run("lexicons", [(n, f) for n, f in sorted(globals().items())
                     if n.startswith("test_") and callable(f)])
