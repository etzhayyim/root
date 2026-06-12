#!/usr/bin/env python3
"""tate 盾 — case-actor generator (wave 41).

「documents/case ごとに actor を用意し, profile から必要なデータの DL と相談先に
届くように」: registry の 1 手続き (case) = 1 keyless mirror-actor
(`did:web:etzhayyim.com:actor:tate-<case>`) を entity-as-actor (ADR-2606042330) /
actor-profile (ADR-2606013800) の形式で生成する。

各 case-actor は 4 ファイル:
  did.json      — keyless mirror DID 文書 (verificationMethod 空 — no-server-key)
  profile.json  — 表示名・説明・ダウンロード一覧・相談先 (shionome 形式準拠)
  case.json     — 手続きの全データ (期限・選択肢・相談先・管轄ディレクトリ) の機械可読 DL
  checklist.md  — 自己提出チェックリストの人間可読 DL (⚠ critical 強調・免責常設)

+ /actor/tate/cases.json — 全 case-actor の索引。

CONSTITUTIONAL: 非裁定/UPL 免責を case.json と checklist.md の両方に常設;
相談 = 各管轄の公的・無料ディレクトリ (+ yoro convo は将来の operator ゲート) —
本生成系はサーバ鍵・送信機能を一切持たない (静的ファイルのみ)。

Pure stdlib. Usage:
    python3 case_actors_gen.py [--out ACTOR_DIR] [--root https://etzhayyim.com]
"""
from __future__ import annotations
import sys, json, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from respond_plan import load_procs, load_jurisdictions  # noqa: E402
from terms_scan import HERE  # noqa: E402

ROOT_DEFAULT = "https://etzhayyim.com"

DISCLAIMER = ("一般的な法情報であり個別の法的助言ではありません (非裁定/UPL)。"
              "期限の起算点 (送達日) は必ず自分で確認し, 重要な判断は記載の無料相談窓口・専門家へ。"
              "法令は改正されます — アンカーは現行条文で要確認。")


def slug(proc_id: str) -> str:
    return "tate-" + proc_id.split(":", 1)[1]


def did_doc(p: dict, root: str) -> dict:
    s = slug(p[":proc/id"])
    did = f"did:web:etzhayyim.com:actor:{s}"
    return {
        "@context": ["https://www.w3.org/ns/did/v1",
                     "https://w3id.org/security/suites/jws-2020/v1"],
        "id": did,
        "alsoKnownAs": [],
        "verificationMethod": [],
        "service": [
            {"id": f"{did}#case-data", "type": "EtzhayyimCaseData",
             "serviceEndpoint": f"{root}/actor/{s}/case.json"},
            {"id": f"{did}#checklist", "type": "EtzhayyimCaseChecklist",
             "serviceEndpoint": f"{root}/actor/{s}/checklist.md"},
            {"id": f"{did}#guide", "type": "EtzhayyimCaseGuide",
             "serviceEndpoint": f"{root}/tate/{p.get(':proc/jurisdiction', ':jp').lstrip(':')}.html"}],
        "_meta": {"adr": ["2606112300", "2606112400", "2606122000"],
                  "source": "tate procedure-registry", "kind": "case-mirror",
                  "parent": "did:web:etzhayyim.com:actor:tate",
                  "track": p.get(":proc/track", ":civil"),
                  "jurisdiction": p.get(":proc/jurisdiction", ":jp"),
                  "note": ("verificationMethod empty — keyless case mirror; did:web trust root = "
                           "TLS (no server-minted key, ADR-2605231525)")}}


def profile(p: dict, juris: dict, root: str) -> dict:
    s = slug(p[":proc/id"])
    j = juris[p.get(":proc/jurisdiction", ":jp")]
    return {
        "did": f"did:web:etzhayyim.com:actor:{s}",
        "handle": f"{s}.etzhayyim.com",
        "displayName": f"{p[':proc/label']} — case actor",
        "description": (f"{j[':juris/label']} の『{p[':proc/label']}』を受け取った人のための "
                        f"case actor。期限ルール・防御選択肢・無料相談先のデータ DL と相談導線。"
                        f" {DISCLAIMER}"),
        "performerType": "system", "uiType": "document",
        "labels": [], "viewer": {},
        "_etzhayyim": {
            "kind": "case-mirror", "parent": "tate",
            "track": p.get(":proc/track", ":civil"),
            "jurisdiction": p.get(":proc/jurisdiction", ":jp"),
            "didDocument": f"{root}/actor/{s}/did.json",
            "downloads": {
                "case_json": f"{root}/actor/{s}/case.json",
                "checklist_md": f"{root}/actor/{s}/checklist.md",
                "jurisdiction_guide": f"{root}/tate/{p.get(':proc/jurisdiction', ':jp').lstrip(':')}.html"},
            "consultation": {
                "free_referrals": j[":juris/referrals"],
                "fraud_help": j[":juris/fake-help"],
                "yoro_convo": ("PLANNED — yoro convo chat 経由の相談は operator/Council "
                               "ゲートの R+ レグ (現状は上記の公的・無料窓口へ)")}}}


def case_json(p: dict, juris: dict) -> dict:
    j = juris[p.get(":proc/jurisdiction", ":jp")]
    return {"disclaimer": DISCLAIMER,
            "case": p[":proc/id"], "label": p[":proc/label"],
            "jurisdiction": p.get(":proc/jurisdiction", ":jp"),
            "jurisdiction_label": j[":juris/label"],
            "track": p.get(":proc/track", ":civil"),
            "genuine_channels": p.get(":proc/genuine-channels", []),
            "service_note": j[":juris/service-note"],
            "deadlines": [{"label": d[":dl/label"], "rule": d[":dl/rule"],
                           "anchor": d[":dl/anchor"],
                           "critical": bool(d.get(":dl/critical")),
                           "verify_service_date": True}
                          for d in p.get(":proc/deadline-rules", [])],
            "options": [{"id": o[":opt/id"], "kind": o[":opt/kind"],
                         "protective": bool(o.get(":opt/protective")),
                         "label": o[":opt/label"]} for o in p.get(":proc/options", [])],
            "referrals": p.get(":proc/refer-when", []),
            "jurisdiction_referrals": j[":juris/referrals"],
            "fraud_help": j[":juris/fake-help"],
            "verify_current_law": True}


def checklist_md(p: dict, juris: dict) -> str:
    j = juris[p.get(":proc/jurisdiction", ":jp")]
    L = [f"# {p[':proc/label']} — 自己対応チェックリスト", "",
         f"> {DISCLAIMER}", "",
         f"本物の書類の経路: {j[':juris/service-note']}",
         "SMS/メールのみの『裁判所』通知は接触せず: " + " / ".join(j[":juris/fake-help"]), "",
         "## 期限 (起算点=送達日を自分で確認)"]
    for d in p.get(":proc/deadline-rules", []):
        mark = "⚠ " if d.get(":dl/critical") else "- "
        L.append(f"{mark}**{d[':dl/label']}**: {d[':dl/rule']} ({d[':dl/anchor']} — 要改正確認)")
    L.append("")
    L.append("## 選択肢 (member 本人が決めて提出する — 代理はしない)")
    for o in p.get(":proc/options", []):
        star = "🛡 " if o.get(":opt/protective") else "- "
        L.append(f"{star}{o[':opt/label']}")
    L.append("")
    L.append("## 相談先 (無料/公的)")
    for r in list(p.get(":proc/refer-when", [])) + list(j[":juris/referrals"]):
        L.append(f"- {r}")
    return "\n".join(L) + "\n"


def generate(actor_dir: pathlib.Path, root: str = ROOT_DEFAULT) -> list:
    procs = load_procs()
    juris = load_jurisdictions()
    index = []
    for p in procs:
        s = slug(p[":proc/id"])
        d = actor_dir / s
        d.mkdir(parents=True, exist_ok=True)
        (d / "did.json").write_text(
            json.dumps(did_doc(p, root), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (d / "profile.json").write_text(
            json.dumps(profile(p, juris, root), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (d / "case.json").write_text(
            json.dumps(case_json(p, juris), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (d / "checklist.md").write_text(checklist_md(p, juris), encoding="utf-8")
        index.append({"slug": s, "did": f"did:web:etzhayyim.com:actor:{s}",
                      "label": p[":proc/label"],
                      "jurisdiction": p.get(":proc/jurisdiction", ":jp"),
                      "track": p.get(":proc/track", ":civil")})
    tate_dir = actor_dir / "tate"
    tate_dir.mkdir(parents=True, exist_ok=True)
    (tate_dir / "cases.json").write_text(
        json.dumps({"disclaimer": DISCLAIMER, "count": len(index), "cases": index},
                   ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return index


def main(argv):
    out = HERE / "out" / "actor"
    root = ROOT_DEFAULT
    if "--out" in argv:
        out = pathlib.Path(argv[argv.index("--out") + 1])
    if "--root" in argv:
        root = argv[argv.index("--root") + 1].rstrip("/")
    index = generate(out, root)
    print(f"tate: {len(index)} case-actors (did.json/profile.json/case.json/checklist.md) "
          f"+ cases.json index → {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
