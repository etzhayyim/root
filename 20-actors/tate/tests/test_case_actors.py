#!/usr/bin/env python3
"""tate 盾 — case-actor generator tests (wave 41). Pure stdlib.

1 case = 1 keyless mirror-actor: profile からデータ DL (case.json/checklist.md) と
相談先に届くこと, no-server-key (verificationMethod 空) と免責常設を検証する。
deploy copy (worker public/actor/) は fresh 生成と機械照合 — registry が伸びたら
再生成を強制 (forcing function)。
"""
import sys
import json
import pathlib
import tempfile

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))

from case_actors_gen import generate, slug  # noqa: E402
from respond_plan import load_procs  # noqa: E402

_TMP = pathlib.Path(tempfile.mkdtemp()) / "actor"
_INDEX = generate(_TMP, root="https://example.test")


def test_one_actor_per_procedure():
    procs = load_procs()
    assert len(_INDEX) == len(procs)
    for p in procs:
        d = _TMP / slug(p[":proc/id"])
        for f in ("did.json", "profile.json", "case.json", "checklist.md"):
            assert (d / f).exists(), (d, f)


def test_did_keyless_no_server_key():
    d = json.loads((_TMP / "tate-shiharai-tokusoku" / "did.json").read_text(encoding="utf-8"))
    assert d["id"] == "did:web:etzhayyim.com:actor:tate-shiharai-tokusoku"
    assert d["verificationMethod"] == []  # keyless mirror — no-server-key
    types = {s["type"] for s in d["service"]}
    assert {"EtzhayyimCaseData", "EtzhayyimCaseChecklist", "EtzhayyimCaseGuide"} <= types


def test_profile_downloads_and_consultation():
    p = json.loads((_TMP / "tate-de-kuendigung" / "profile.json").read_text(encoding="utf-8"))
    dl = p["_etzhayyim"]["downloads"]
    assert dl["case_json"].endswith("/actor/tate-de-kuendigung/case.json")
    assert dl["checklist_md"].endswith("/checklist.md")
    cons = p["_etzhayyim"]["consultation"]
    assert cons["free_referrals"] and cons["fraud_help"]
    assert "operator" in cons["yoro_convo"]  # 相談チャットは将来レグと正直に


def test_case_json_faithful_and_disclaimed():
    c = json.loads((_TMP / "tate-ch-zahlungsbefehl" / "case.json").read_text(encoding="utf-8"))
    assert "法的助言ではありません" in c["disclaimer"]
    assert any(d["critical"] and "SchKG" in d["anchor"] for d in c["deadlines"])
    assert all(d["verify_service_date"] for d in c["deadlines"])
    assert c["verify_current_law"] is True


def test_checklist_disclaimer_and_critical():
    md = (_TMP / "tate-au-unfair-dismissal" / "checklist.md").read_text(encoding="utf-8")
    assert "法的助言ではありません" in md and "⚠" in md and "🛡" in md


def test_cases_index():
    idx = json.loads((_TMP / "tate" / "cases.json").read_text(encoding="utf-8"))
    assert idx["count"] == len(_INDEX)
    tracks = {c["track"] for c in idx["cases"]}
    assert ":labor" in tracks and ":housing" in tracks


def test_deploy_copy_in_sync():
    """worker public/actor の deploy copy は fresh 生成と同じ case-actor 集合."""
    deploy = ACTOR_DIR.parent.parent / "50-infra" / "etzhayyim-did-web" / "public" / "actor"
    deployed = {d.name for d in deploy.iterdir() if d.name.startswith("tate-")}
    fresh = {c["slug"] for c in _INDEX}
    assert deployed == fresh, (sorted(fresh - deployed)[:3], sorted(deployed - fresh)[:3])
    assert (deploy / "tate" / "cases.json").exists()


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok {fn.__name__}")
    print(f"{len(fns)} passed")
