"""analyze.py — 朱 (ake) end-to-end membrane over the :representative seed. ADR-2606052100.

Runs each seed edit through the full Wikipedia-stance pipeline:
    propose → triage (risk+quality+route) → [optimistic | sbt-vote | council-lv7 | refused]
            → append revision (append-only) → contributor trajectory

and emits an offline scorecard (Markdown) + derived datoms (edn). NO live ingest / publish /
promotion — all of that is G8 (Council Lv6+ + operator). This is a dry-run demonstration.
"""

from __future__ import annotations

import pathlib

import contributor as contrib
from _edn import load_edn
from revision import append_revision, current, history_of
from triage import _kw, score_edit

_ROOT = pathlib.Path(__file__).resolve().parents[1]
_SEED = _ROOT / "data" / "seed-edit-graph.kotoba.edn"
_OUT = _ROOT / "methods" / "out"

TIMELOCK_H = 48      # the standard SBT-vote window


def run(seed_path: pathlib.Path = _SEED) -> dict:
    seed = load_edn(seed_path)
    edits = seed[":edit/batch"]

    history: list[dict] = []
    traj = contrib.empty()      # Wellbecoming contributor trajectory (G9)
    rows = []

    as_of = 2000
    for e in edits:
        as_of += 10
        author = e.get(":edit/author", "?")

        try:
            tri = score_edit(e)
        except ValueError as exc:
            rows.append({"edit": e.get(":edit/id"), "route": ":refused-at-intake",
                         "risk": "-", "quality": "-", "accepted": False, "note": str(exc)})
            traj = contrib.record(traj, author, "refused", as_of)
            continue

        route = _kw(tri[":triage/route"])
        risk = _kw(tri[":triage/risk"])
        quality = tri[":triage/quality"]
        accepted = False
        decided = True          # council-pending is NOT yet decided → no trajectory event
        note = ""

        if route == "auto-accept":
            accepted = True
            note = "optimistic fast-path (low risk + high quality)"
        elif route == "vote":
            yes = int(e.get(":review/yes", 0))
            no = int(e.get(":review/no", 0))
            accepted = yes > no
            note = f"1 SBT=1 vote {yes}-{no} / {TIMELOCK_H}h → {'accepted' if accepted else 'rejected'}"
        elif route == "council-lv7":
            decided = False
            note = "escalated to Council Lv7+ (invariant-adjacent) → pending (G7)"
        elif route == "refused":
            note = f"Charter-Rider §2 hit {tri.get(':triage/rider-token')!r} → unpromotable (no vote)"

        if accepted:
            history = append_revision(history, e, as_of)
        if decided:
            traj = contrib.record(traj, author, "accepted" if accepted else "refused", as_of)

        rows.append({"edit": e.get(":edit/id"), "route": ":" + route, "risk": risk,
                     "quality": quality, "accepted": accepted, "note": note})

    return {"rows": rows, "history": history, "trajectory": traj, "edits": edits}


def _report(res: dict) -> str:
    out = ["# 朱 (ake) — community-edit membrane dry-run\n",
           "Wikipedia-stance pipeline over the `:representative` seed. "
           "No live ingest / publish / promotion (G8).\n",
           "## Routing\n",
           "| edit | risk | quality | route | accepted | note |",
           "|---|---|---|---|---|---|"]
    for r in res["rows"]:
        out.append(f"| {r['edit']} | {r['risk']} | {r['quality']} | {r['route']} | "
                   f"{'✅' if r['accepted'] else '—'} | {r['note']} |")
    out.append("\n## Revision history (append-only, latest = current)\n")
    seen = set()
    for rev in res["history"]:
        key = (rev[":revision/entity"], rev[":revision/attr"])
        if key in seen:
            continue
        seen.add(key)
        cur = current(res["history"], *key)
        n = len(history_of(res["history"], *key))
        out.append(f"- `{key[0]}` `{key[1]}` → {cur[':revision/sourcing']} "
                   f"(`{cur[':revision/value'][:48]}…`), {n} revision(s)")
    out.append("\n## Contributor trajectory (Wellbecoming, not a score-of-soul)\n")
    for did in res["trajectory"]:
        t = contrib.trajectory(res["trajectory"], did)
        rate = "—" if t["acceptanceRate"] is None else f"{t['acceptanceRate']:.2f}"
        flag = " ⚠ throttled" if t["throttled"] else ""
        out.append(f"- `{did}` — accepted {t['accepted']}, refused {t['refused']}, "
                   f"acceptance {rate}{flag}")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    res = run()
    report = _report(res)
    _OUT.mkdir(parents=True, exist_ok=True)
    (_OUT / "membrane-dryrun.md").write_text(report, encoding="utf-8")
    print(report)
