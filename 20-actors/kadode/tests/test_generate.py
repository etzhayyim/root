#!/usr/bin/env python3
"""kadode 門出 — document-generator + 使者-relay tests (ADR-2606112238). Pure stdlib.

Verifies:
  - the 退職届 renders deterministically, states its statutory basis (民法627), and contains
    ONLY "一身上の都合" — never a demand / negotiation / settlement figure (G1)
  - missing fields render as explicit blanks, never invented (G2)
  - assert_no_negotiation() rejects demand/negotiation language injected into a free-text field
  - build_relay() RELAYS a non-negotiating scenario but REFUSES a negotiation-needing one and
    returns the escalation route instead (the action-layer UPL boundary, G1)
  - the relay record is drafted-UNSENT (no-server-key); document is content-addressed
"""
import sys, pathlib
ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))
from analyze import load  # noqa: E402
from cid import cidv1_raw  # noqa: E402
import generate  # noqa: E402

SEED = ACTOR_DIR / "data" / "seed-resignation-graph.kotoba.edn"


def test_taishokutodoke_renders_unilateral_and_traceable():
    doc = generate.render("taishoku-todoke", {"worker": "山田太郎", "employer": "株式会社ABC",
                                              "date": "令和8年7月15日"})
    assert doc == generate.render("taishoku-todoke", {"worker": "山田太郎", "employer": "株式会社ABC",
                                                     "date": "令和8年7月15日"}), "not deterministic"
    assert "退職届" in doc and "一身上の都合" in doc
    assert "民法627条" in doc, "missing statutory basis"
    assert "承諾を要しません" in doc, "must state the employer's consent is not required"
    # no negotiation/demand language ever appears in a kadode resignation
    for bad in generate.PROHIBITED_NEGOTIATION:
        assert bad not in doc


def test_missing_fields_render_as_blanks():
    doc = generate.render("taishoku-todoke", {"worker": "山田太郎"})
    assert "［　　］" in doc, "missing fields must render as explicit blanks, never invented"


def test_assert_no_negotiation_rejects_demands():
    for bad in ("示談金を支払えと請求します", "退職金を増額する条件交渉をしたい", "慰謝料を請求"):
        try:
            generate.assert_no_negotiation(bad)
            assert False, f"negotiation text accepted: {bad}"
        except ValueError:
            pass
    generate.assert_no_negotiation("一身上の都合により退職します")  # clean text passes


def test_render_rejects_negotiation_in_note_field():
    try:
        generate.render("taishoku-todoke", {"worker": "A", "note": "解決金を請求します"})
        assert False, "render accepted negotiation language in note"
    except ValueError:
        pass


def test_relay_conveys_non_negotiating_scenario():
    nodes, edges = load(SEED)
    doc = generate.render("taishoku-todoke", {"worker": "山田太郎", "employer": "株式会社ABC",
                                              "date": "令和8年7月15日"})
    rec = generate.build_relay("sc.permanent-cant-face", doc, "did:plc:worker", "employer-hash",
                               nodes, edges, created_at="2026-06-11T00:00:00Z")
    assert rec["$type"] == "com.etzhayyim.kadode.resignationRelay"
    assert rec["relayed"] is False and rec["status"] == "drafted-unsent"  # no-server-key
    assert rec["negotiates"] is False and rec["role"] == "messenger-使者"
    assert rec["documentCid"] == cidv1_raw(doc.encode("utf-8"))


def test_relay_refuses_negotiation_scenario_and_escalates():
    """G1 at the action layer: a 使者 must never relay a matter needing negotiation."""
    nodes, edges = load(SEED)
    doc = generate.render("taishoku-todoke", {"worker": "山田太郎", "employer": "X", "date": "令和8年8月1日"})
    for sid in ("sc.damages-threatened", "sc.unpaid-wages", "sc.harassment", "sc.yukyu-refused"):
        rec = generate.build_relay(sid, doc, "did:plc:worker", "employer-hash", nodes, edges)
        assert rec["$type"] == "com.etzhayyim.kadode.escalation", f"{sid} should escalate"
        assert rec["relayed"] is False
        assert rec["escalateActor"] in (":labor-union", ":lawyer"), \
            f"{sid} must escalate to union/lawyer, got {rec['escalateActor']}"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn(); print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")
