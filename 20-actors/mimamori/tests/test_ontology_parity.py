#!/usr/bin/env python3
"""mishmeret ontology EDN ↔ runtime validator parity — schema and code never drift."""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "methods"))
from _edn import _parse, _tokens  # noqa: E402
from bond import ATTR_WHITELIST, CARE_WHITELIST, STATES  # noqa: E402

ONTOLOGY = HERE.parents[1] / "00-contracts" / "schemas" / "mishmeret-ontology.kotoba.edn"
PASS = []


def t(name, fn):
    fn()
    PASS.append(name)
    print(f"  ok  {name}")


def _load():
    text = "\n".join(l for l in ONTOLOGY.read_text(encoding="utf-8").splitlines()
                     if not l.lstrip().startswith(";"))
    return _parse(_tokens(text))


def test_edge_attrs_match_validator_whitelist():
    o = _load()
    declared = {e[":attr"] for e in o[":edge/attrs"]}
    assert declared == ATTR_WHITELIST, (
        f"drift: ontology-only={sorted(declared - ATTR_WHITELIST)} "
        f"code-only={sorted(ATTR_WHITELIST - declared)}")


def test_coverage_attrs_match_emitter():
    from coverage_report import coverage
    from kotoba import coverage_datoms
    from bond import load_seed
    o = _load()
    declared = {e[":attr"] for e in o[":coverage/attrs"]}
    seed = load_seed(HERE / "data" / "seed-mimamori-bonds.json")
    emitted = {d[2] for d in coverage_datoms(coverage(seed), 1)}
    assert declared == emitted


def test_social_capital_attrs_match_emitter():
    from bond import replay, load_seed
    from shakai import MoyaiLedger, mint_from_keeping, social_capital_datoms
    o = _load()
    declared = {e[":attr"] for e in o[":social-capital/attrs"]}
    eng = replay(load_seed(HERE / "data" / "seed-mimamori-bonds.json"))
    led = MoyaiLedger()
    mint_from_keeping(eng, led, 1)
    emitted = {d[2] for d in social_capital_datoms(led, 1)}
    assert declared == emitted


def test_negative_space_documented():
    o = _load()
    blocked = " ".join(u[":ns"] for u in o[":unrepresentable"])
    assert ":mishmeret.person/*" in blocked       # G2
    assert ":police" in blocked                   # G1
    assert ":db/retract" in blocked               # append-only
    # and the doc'd enums really are the code's whole surface:
    assert CARE_WHITELIST == {":kokoro", ":wakai", ":iyashi"}
    assert STATES == {":offered", ":active", ":declined", ":exited", ":handed-off"}


if __name__ == "__main__":
    t("edge attrs ≡ validator whitelist", test_edge_attrs_match_validator_whitelist)
    t("coverage attrs ≡ emitter output", test_coverage_attrs_match_emitter)
    t("social-capital attrs ≡ emitter output", test_social_capital_attrs_match_emitter)
    t("negative space documented + enums exact", test_negative_space_documented)
    print(f"test_ontology_parity: {len(PASS)}/4 green")
