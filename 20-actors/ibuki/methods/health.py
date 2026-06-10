"""health.py — colony 健全性 (Wellbecoming) audit, derived purely from the Datom log.

ADR-2606101200 §健全化 (2026-06-10 health wave). The 100-beat audit that found the
homeostasis-loss bug proved two things: (1) the as-of log is sufficient evidence to diagnose
a growth pathology after the fact, and (2) health must be a CONTINUOUSLY MEASURED property,
not a one-off audit. This module makes it one — Wellbecoming as as-of history
(ADR-2606011500's discipline): a trajectory judgment, never a score-of-soul.

`audit(txs)` reads NOTHING but the log (single pass, fleet-scale safe) and reports, per
organism and for the colony:

  - **muted**       — mood `stressed` for ≥ MUTED_STREAK consecutive recent beats (the
                      pathology the bug caused: a muted organism cannot post). Structural
                      note: with baseline stress bounded [25,65] and idle drift, muteness is
                      always RECOVERABLE — this detector verifies that recovery happens.
  - **saturation**  — any axis pinned at the 0/100 clamp (emotion ceiling = no headroom).
  - **stress_excess** — head stress above the designed equilibrium band (baseline + BAND).
  - **divergence**  — the `:joucho/*` checkpoint at the organism's last beat disagrees with
                      the pure as-of replay (two views of one history — the bug's signature).
  - **posting drought** — beats since last post far beyond the slowest mood cooldown.
  - **colony**      — mood diversity (a healthy colony is not a monoculture), totals, verdict.

Pathologies become **KaizenProposal lines** (same shape kaizen_feedback consumes: proposalId
+ rule), so the colony's own Wave-4 loop carries its health complaints to humans. `:health/*`
checkpoint datoms put the verdict itself on the log — the colony's health history is as-of
queryable like everything else.

No per-organism "wellbeing score" exists here (edge-primary discipline): every readout is a
named, bounded PATHOLOGY check or a colony aggregate. Stdlib only. Deterministic.
"""

from __future__ import annotations

import json
import pathlib

import datoms
import joucho

STRESS_BAND = 4          # designed equilibrium: stress ≤ baseline + BAND under idle drift
MUTED_STREAK = 12        # consecutive stressed beats before an organism counts as muted
DROUGHT_FACTOR = 3       # beats-without-post > FACTOR × slowest cooldown (in beats) = drought
BEAT_MS = 45 * 60_000    # autorun/fleet logical beat

RULES = ("organism-muted", "axis-saturation", "stress-excess",
         "checkpoint-divergence", "posting-drought", "mood-monoculture")


def _walk(txs: list[dict]) -> dict:
    """ONE pass over the log → per-organism {events: [(beat, kind)...], joucho_ck: latest
    checkpoint attrs, hb: latest heartbeat attrs}. Fleet-scale safe (no per-entity refolds)."""
    ev_entity: dict[str, dict] = {}
    ev_order: list[str] = []
    joucho_ck: dict[str, dict] = {}
    hb: dict[str, dict] = {}
    for tx in txs:
        for _op, e, a, v in tx.get(":tx/datoms", []):
            if a.startswith(":joucho.event/"):
                if e not in ev_entity:
                    ev_entity[e] = {}
                    ev_order.append(e)
                ev_entity[e][a] = v
            elif a.startswith(":joucho/"):
                joucho_ck.setdefault(e, {})[a] = v
            elif a.startswith(":heartbeat/"):
                hb.setdefault(e, {})[a] = v
    per: dict[str, dict] = {}
    for e in ev_order:
        ent = ev_entity[e]
        of, kind = ent.get(":joucho.event/of"), ent.get(":joucho.event/kind")
        if of and kind:
            per.setdefault(of, {"events": [], "joucho_ck": None, "hb": None})
            per[of]["events"].append((ent.get(":joucho.event/beat", 0), kind))
    latest_ck: dict[str, int] = {}
    for ent in joucho_ck.values():
        of, beat = ent.get(":joucho/of"), ent.get(":joucho/beat", -1)
        if of in per and beat > latest_ck.get(of, -1):
            per[of]["joucho_ck"] = ent
            latest_ck[of] = beat
    latest_hb: dict[str, int] = {}
    for ent in hb.values():
        of, beat = ent.get(":heartbeat/of"), ent.get(":heartbeat/beat", -1)
        if of in per and beat > latest_hb.get(of, -1):
            per[of]["hb"] = ent
            latest_hb[of] = beat
    return per


def audit(txs: list[dict]) -> dict:
    """The colony health report, from the log alone. Deterministic."""
    per = _walk(txs)
    organisms: dict[str, dict] = {}
    head_moods: dict[str, int] = {}
    findings: list[dict] = []

    for code, rec in sorted(per.items()):
        base = joucho.personality_baseline(code)
        scores = base
        mood_by_beat: list[tuple[int, str]] = []
        for beat, kind in rec["events"]:                    # incremental fold, one pass
            scores = joucho.fold_event(scores, kind, base)
            mood_by_beat.append((beat, joucho.determine_mood(scores)))
        mood = joucho.determine_mood(scores)
        head_moods[mood] = head_moods.get(mood, 0) + 1

        streak = 0
        for _b, m in reversed(mood_by_beat):
            if m != "stressed":
                break
            streak += 1
        muted = streak >= MUTED_STREAK

        saturated = [a for a, v in scores.as_dict().items() if v in (0, 100)]
        stress_excess = max(0, scores.stress - (base.stress + STRESS_BAND))

        diverged = False
        ck = rec["joucho_ck"]
        if ck is not None:
            diverged = any(ck.get(f":joucho/{a}") != v for a, v in scores.as_dict().items())

        drought = False
        hb = rec["hb"]
        if hb is not None and hb.get(":heartbeat/beats", 0) > 0:
            beats = hb[":heartbeat/beats"]
            last_post_ms = hb.get(":heartbeat/last-post-at-ms", -1)
            slowest_beats = max(joucho.POST_COOLDOWN_MS.values()) // BEAT_MS + 1
            since = beats - (last_post_ms // BEAT_MS if last_post_ms >= 0 else 0)
            drought = since > DROUGHT_FACTOR * slowest_beats

        organisms[code] = {"mood": mood, "axes": scores.as_dict(),
                           "stressed_streak": streak, "muted": muted,
                           "saturated_axes": saturated, "stress_excess": stress_excess,
                           "checkpoint_diverged": diverged, "posting_drought": drought}
        for cond, rule, detail in (
                (muted, "organism-muted", f"stressed for {streak} consecutive beats"),
                (bool(saturated), "axis-saturation", f"axes at clamp: {saturated}"),
                (stress_excess > 0, "stress-excess",
                 f"stress {scores.stress} > baseline {base.stress} + {STRESS_BAND}"),
                (diverged, "checkpoint-divergence",
                 "joucho checkpoint != as-of replay (two histories)"),
                (drought, "posting-drought", "no post far beyond slowest cooldown")):
            if cond:
                findings.append({"proposalId": f"health-{rule}-{code}",
                                 "rule": rule, "organism": code, "detail": detail})

    if len(per) >= 3 and len(head_moods) == 1:
        findings.append({"proposalId": "health-mood-monoculture-colony",
                         "rule": "mood-monoculture", "organism": "*",
                         "detail": f"all {len(per)} organisms share mood "
                                   f"{next(iter(head_moods))!r} — personality collapsed"})

    return {"organisms": organisms,
            "colony": {"count": len(per), "mood_diversity": head_moods,
                       "findings": len(findings)},
            "findings": findings,
            "healthy": not findings}


def health_datoms(report: dict, *, beat: int, as_of: int) -> list[list]:
    """Checkpoint the verdict on the log (`:health/*`) — colony aggregate + one flag per
    finding. The health HISTORY becomes as-of queryable; no per-organism wellbeing score
    is ever asserted (edge-primary)."""
    e = f"health-{beat}"
    out = [datoms.add(e, ":health/beat", beat),
           datoms.add(e, ":health/as-of", as_of),
           datoms.add(e, ":health/organisms", report["colony"]["count"]),
           datoms.add(e, ":health/mood-kinds", len(report["colony"]["mood_diversity"])),
           datoms.add(e, ":health/findings", report["colony"]["findings"]),
           datoms.add(e, ":health/healthy", report["healthy"])]
    for i, f in enumerate(report["findings"]):
        fe = f"health-{beat}-f{i}"
        out += [datoms.add(fe, ":health.finding/of", f["organism"]),
                datoms.add(fe, ":health.finding/rule", f["rule"]),
                datoms.add(fe, ":health.finding/beat", beat),
                datoms.add(fe, ":health.finding/as-of", as_of)]
    return out


def write_proposals(report: dict, path: pathlib.Path) -> int:
    """Pathologies → KaizenProposal NDJSON (proposalId + rule — exactly the shape
    kaizen_feedback.read_proposals consumes), so the colony's own Wave-4 loop carries its
    health complaints to humans. Snapshot semantics (overwrite): current pathologies only;
    the as-of history lives on the log via health_datoms."""
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("".join(json.dumps(f, ensure_ascii=False, sort_keys=True) + "\n"
                         for f in report["findings"]), encoding="utf-8")
    return len(report["findings"])


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="ibuki colony health audit (log-derived)")
    ap.add_argument("--log", type=pathlib.Path, default=datoms.LOG_DEFAULT)
    ap.add_argument("--proposals", type=pathlib.Path, default=None)
    args = ap.parse_args()
    rep = audit(datoms.read_log(args.log))
    c = rep["colony"]
    print(f"# ibuki health — {c['count']} organisms, mood diversity "
          f"{c['mood_diversity']}, findings={c['findings']}, "
          f"healthy={'YES' if rep['healthy'] else 'NO'}")
    for f in rep["findings"]:
        print(f"  ! {f['rule']} [{f['organism']}] {f['detail']}")
    if args.proposals is not None:
        n = write_proposals(rep, args.proposals)
        print(f"  → {n} kaizen proposals → {args.proposals}")
