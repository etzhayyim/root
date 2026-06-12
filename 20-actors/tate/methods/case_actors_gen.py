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
            {"id": f"{did}#template", "type": "EtzhayyimCaseTemplate",
             "serviceEndpoint": f"{root}/actor/{s}/template.md"},
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
                "template_md": f"{root}/actor/{s}/template.md",
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


OFFICIAL_FORM_HINTS = ("Form", "様式", "Formular", "formulaire", "FL-120", "용지",
                       "用紙", "Official", "公式")


def template_md(p: dict, juris: dict) -> str:
    """記入式の構造雛形 (書面). member 本人が記入・確定・提出する前提 (UPL —
    tasuke の被害届雛形と同型)。公式様式がある手続きはポインタを優先する。"""
    j = juris[p.get(":proc/jurisdiction", ":jp")]
    subs = [o for o in p.get(":proc/options", []) if o[":opt/kind"] == ":self-submit"]
    L = [f"# {p[':proc/label']} — 提出書面の雛形 (記入式)", "",
         f"> {DISCLAIMER}", "",
         "> この雛形は member 本人が【 】を埋めて確定・提出するための構造テンプレートです。",
         ""]
    if not subs:
        L.append("この手続きは出頭・相談・確認が中心で、定型の提出書面はありません。")
        L.append("checklist.md の手順と相談先に従ってください。")
        return "\n".join(L) + "\n"
    official = [o for o in subs
                if any(h.casefold() in o[":opt/label"].casefold() for h in OFFICIAL_FORM_HINTS)]
    if official:
        L.append("## まず公式様式を確認")
        for o in official:
            L.append(f"- {o[':opt/label']} — **公式様式が存在します。自由書式より様式を優先**してください。")
        L.append("")
    L.append("## 自由書式の構造 (様式がない/補助書面の場合)")
    L.append("")
    L.append("```")
    L.append("【提出先】 " + (subs[0][":opt/label"].split(" (")[0]))
    L.append(f"【件名】   {p[':proc/label']} に対する {subs[0][':opt/label'].split('を')[0].strip()}")
    L.append("")
    L.append("【自分の氏名・住所・連絡先】")
    L.append("【相手方/事件の特定】 事件番号・通知の日付: 【受領した書面の番号と日付】")
    L.append("")
    L.append("1. 私は【通知を受領した日 — 期限の起算点】に標記の通知を受領しました。")
    L.append(f"2. 私は次のとおり申し立てます: 【{subs[0][':opt/label']}】")
    L.append("3. 理由: 【簡潔に。理由不要の手続き (異議のみで足りる類型) は省略可 —")
    L.append("   checklist.md の期限ルール参照】")
    L.append("4. 添付書類: 【受領通知の写し・証拠など】")
    L.append("")
    L.append("【日付】 【署名】")
    L.append("```")
    L.append("")
    L.append("## 提出前チェック")
    for d in p.get(":proc/deadline-rules", []):
        mark = "⚠ " if d.get(":dl/critical") else "- "
        L.append(f"{mark}{d[':dl/label']}: {d[':dl/rule']} ({d[':dl/anchor']})")
    L.append(f"- 提出方法・控えの保管。不安があれば: {' / '.join(j[':juris/referrals'][:2])}")
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
        (d / "template.md").write_text(template_md(p, juris), encoding="utf-8")
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
