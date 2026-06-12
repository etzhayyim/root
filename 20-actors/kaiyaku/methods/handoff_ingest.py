#!/usr/bin/env python3
"""kaiyaku 解約 — tate 盾 handoff ingest (wave 26, ADR-2606112201/2606112301).

tate の不利条項スキャンが :kaiyaku ルートで検出した自動更新条項・解約窓
(out/kaiyaku-handoff.edn) を読み、縁-ledger 側の **notice-window ワークリスト**に
変換する — tate detects → kaiyaku severs の配線が往復で閉じる。

各候補は「この契約には自動更新/解約窓条項がある — 縁-ledger の該当 tie に
:svc/notice-days をカレンダー化せよ」という ingest 指示で、severance の実行系
(plan.py) には触れない (G5/G6 のゲートは不変)。

Pure stdlib — runnable inside a kotoba pywasm actor (componentize-py).
Usage:
    python3 handoff_ingest.py [handoff.edn] [--out OUTDIR]
    (引数なしなら同 repo の tate からライブ生成して ingest — 開発時の e2e)
"""
from __future__ import annotations
import sys, pathlib

HERE = pathlib.Path(__file__).resolve().parent.parent
TATE = HERE.parent / "tate"
sys.path.insert(0, str(HERE / "methods"))
sys.path.insert(0, str(TATE / "methods"))
from analyze import read_edn  # noqa: E402  (kaiyaku's own EDN reader)


def ingest(handoff_text: str) -> list:
    """Parse tate's handoff EDN → notice-window candidates for the 縁-ledger."""
    out = []
    for h in read_edn(handoff_text):
        if not isinstance(h, dict) or ":handoff/clause" not in h:
            continue
        out.append({
            "doc": h[":handoff/doc"],
            "jurisdiction": h.get(":handoff/jurisdiction", ":jp"),
            "clause": h[":handoff/clause"],
            "matched": h.get(":handoff/matched", ""),
            "anchor": h.get(":handoff/anchor", ""),
            "action": h.get(":handoff/action"),
        })
    return out


def to_datoms(cands: list, tx: int = 1) -> str:
    L = [";; kaiyaku 解約 — tate handoff ingest datoms — GENERATED. DO NOT hand-edit.",
         ";; GROUND :add — notice-window worklist (縁-ledger の :svc/notice-days 化候補).", ""]
    for i, c in enumerate(cands):
        eid = f'"handoff:{i:03d}"'
        L.append(f'[{eid} :kaiyaku.handoff/doc "{c["doc"]}" {tx} :add]')
        L.append(f'[{eid} :kaiyaku.handoff/jurisdiction {c["jurisdiction"]} {tx} :add]')
        L.append(f'[{eid} :kaiyaku.handoff/clause "{c["clause"]}" {tx} :add]')
        L.append(f'[{eid} :kaiyaku.handoff/action {c["action"]} {tx} :add]')
    L.append("")
    L.append(f";; candidates={len(cands)}")
    return "\n".join(L) + "\n"


def worklist_md(cands: list) -> str:
    L = ["# kaiyaku — tate handoff 取込ワークリスト (notice-window カレンダー化候補)", ""]
    L.append("| doc | juris | clause | 開示アンカー |")
    L.append("|---|---|---|---|")
    for c in cands:
        L.append(f"| {c['doc']} | {c['jurisdiction']} | {c['clause']} | {c['anchor']} |")
    L.append("")
    L.append("各行は tate 盾 が member の契約に発見した自動更新/解約窓条項。縁-ledger の該当 tie に "
             ":svc/notice-days を設定し、解約窓を逃さない (severance 実行は従来どおり G5/G6 ゲート)。")
    return "\n".join(L) + "\n"


def _live_handoff_from_tate() -> str:
    from terms_scan import load_docs, load_patterns, scan, make_kaiyaku_handoff  # noqa: E402
    docs, _ = load_docs()
    return make_kaiyaku_handoff(scan(docs, load_patterns()))


def main(argv):
    out = HERE / "out"
    if "--out" in argv:
        out = pathlib.Path(argv[argv.index("--out") + 1])
    if len(argv) > 1 and not argv[1].startswith("--"):
        text = pathlib.Path(argv[1]).read_text(encoding="utf-8")
    else:
        text = _live_handoff_from_tate()  # 開発時 e2e: tate からライブ生成
    cands = ingest(text)
    out.mkdir(parents=True, exist_ok=True)
    (out / "handoff-worklist.md").write_text(worklist_md(cands), encoding="utf-8")
    (out / "handoff-datoms.kotoba.edn").write_text(to_datoms(cands), encoding="utf-8")
    print(f"kaiyaku: {len(cands)} notice-window candidates ingested from tate "
          f"→ {out / 'handoff-worklist.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
