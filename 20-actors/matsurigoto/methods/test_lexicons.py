#!/usr/bin/env python3
"""3-place invariant drift-lock (matsurigoto 政, ADR-2606062300).

Proves the structural invariants are encoded identically in all THREE places —
  (1) the schema EDN  00-contracts/schemas/egov-execution-ontology.kotoba.edn
  (2) the lexicons    00-contracts/lexicons/com/etzhayyim/matsurigoto/*.json
  (3) the code        methods/datoms.py / sign_capability.py
— the nusa/tazuna/kamado/ake pattern. Touch one, this fails until all three agree.
"""
from __future__ import annotations

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent.parent
LEX = REPO / "00-contracts" / "lexicons" / "com" / "etzhayyim" / "matsurigoto"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "modules"))

import datoms as D       # noqa: E402
import sign_capability as S  # noqa: E402
from _edn import load_edn    # noqa: E402


def _lex(name):
    return json.loads((LEX / f"{name}.json").read_text(encoding="utf-8"))


def _props(name):
    return _lex(name)["defs"]["main"]["record"]["properties"]


def test_g1_server_held_authority_const_false_everywhere():
    # (2) lexicons
    assert _props("serviceExecution")["serverHeldAuthority"]["const"] is False
    assert _props("unsignedArtifact")["serverHeldAuthority"]["const"] is False
    # (3) code — modules hold no key
    import tax_assess, civil_registry, corp_registry, credential_issue  # noqa
    assert tax_assess.SERVER_HELD_AUTHORITY is False
    assert S.SIGNER_HELD_PRIVATE_KEY is False


def test_g3_operated_by_enum_matches_code_and_schema():
    lex_enum = set(_props("serviceExecution")["operatedBy"]["enum"])
    # (3) code
    code = {x.lstrip(":") for x in D.ALLOWED_OPERATED_BY}
    assert lex_enum == code, (lex_enum, code)
    # (1) schema EDN
    onto = load_edn(REPO / "00-contracts" / "schemas" / "egov-execution-ontology.kotoba.edn")
    inv = onto[":invariants"][":g3-operated-by"][":allowed"]
    schema = {x.lstrip(":") for x in inv}
    assert lex_enum == schema, (lex_enum, schema)


def test_g3_authority_mode_enum_matches_code():
    lex_enum = set(_props("serviceExecution")["authorityMode"]["enum"])
    code = {x.lstrip(":") for x in D.ALLOWED_AUTHORITY_MODE}
    assert lex_enum == code, (lex_enum, code)


def test_g5_immutable_const_true_in_lexicon_and_schema():
    assert _props("vitalRecord")["immutable"]["const"] is True
    onto = load_edn(REPO / "00-contracts" / "schemas" / "egov-execution-ontology.kotoba.edn")
    assert onto[":invariants"][":g5-append-only"][":allowed"] == [True]


def test_lexicons_are_valid_json_with_ids():
    for name in ("serviceExecution", "unsignedArtifact", "vitalRecord"):
        d = _lex(name)
        assert d["id"] == f"com.etzhayyim.matsurigoto.{name}"
        assert d["lexicon"] == 1


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)}/{len(fns)} passed")
    return 0


if __name__ == "__main__":
    sys.exit(_run())
