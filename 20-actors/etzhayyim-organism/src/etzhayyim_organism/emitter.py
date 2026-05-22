"""Action emitter — persists one observation file per tick.

Writes `_observations/YYMMDDHHMM-cycle-NN.md` matching the schema documented
in `_observations/README.md` (5 sections). Commit/push are intentionally NOT
done from the pod — that's a separate operator gesture so the religious-corp
identity stays with humans, not daemons (ADR-2605192100 §1.3 anti-individualist
+ accountability requirement).
"""

from __future__ import annotations

import datetime as _dt
from pathlib import Path

from .constitution import AXES
from .cns import TickResult


def _tz_jst() -> _dt.timezone:
    return _dt.timezone(_dt.timedelta(hours=9))


def render_observation(result: TickResult, source: str = "etzhayyim-organism pod") -> str:
    now = _dt.datetime.now(_tz_jst())
    ts = now.strftime("%Y-%m-%d %H:%M JST")
    lines: list[str] = []
    lines.append(f"# Cycle {result.cycle} — {ts}")
    lines.append("")
    lines.append(f"_Emitted by: {source}_")
    lines.append("")

    lines.append("## 1. Observation")
    lines.append("")
    for k, r in result.readings.items():
        lines.append(f"- **{k}**: " + "; ".join(r.evidence) if r.evidence else f"- **{k}**: (no evidence)")
    lines.append("")

    lines.append("## 2. Verification of last tick's prediction")
    lines.append("")
    if result.prev_scores:
        moved = {k: v for k, v in result.deltas.items() if v != 0}
        if moved:
            lines.append("Axes that moved this tick:")
            for k, v in moved.items():
                sign = "+" if v > 0 else ""
                lines.append(f"- {k}: {sign}{v}")
        else:
            lines.append("Δ=0 on all axes (steady-state tick).")
    else:
        lines.append("First persisted observation — no prior to verify against.")
    lines.append("")

    lines.append("## 3. Scores (10 axes)")
    lines.append("")
    lines.append("| # | Axis | Score | Δ vs prev | Reason |")
    lines.append("|---|---|---|---|---|")
    for ax in AXES:
        r = result.readings[ax.key]
        d = result.deltas.get(ax.key, 0)
        d_str = "—" if d == 0 else (f"+{d}" if d > 0 else str(d))
        reason = (r.evidence[0] if r.evidence else "")
        lines.append(f"| {ax.n} | **{ax.name_en}** {ax.name_jp} | {r.score} / 10 | {d_str} | {reason} |")
    delta_total = result.total - result.prev_total if result.prev_scores else 0
    dt_str = "—" if delta_total == 0 else (f"+{delta_total}" if delta_total > 0 else str(delta_total))
    lines.append(f"| | **Total** | **{result.total} / 100** | **{dt_str}** | |")
    lines.append("")

    lines.append("## 4. Action emitted this tick")
    lines.append("")
    chosen = result.readings[result.chosen_axis]
    lines.append(f"**Target axis**: {result.chosen_axis} ({result.chosen_reason})")
    lines.append("")
    lines.append(f"**Next-action**: {chosen.next_action}")
    lines.append("")
    lines.append("Concrete artefact: this observation file. Follow-on artefacts ")
    lines.append("(ADRs, code, docs) are emitted by operator-supervised ticks per ")
    lines.append("ADR-2605192100 §1.3 — the organism does not commit on its own.")
    lines.append("")

    lines.append("## 5. Prediction for next tick")
    lines.append("")
    lines.append(
        f"If the operator closes the action above, expect axis `{result.chosen_axis}` "
        f"to move from {chosen.score}/10 toward {min(chosen.score + chosen.leverage, 10)}/10 "
        f"(leverage={chosen.leverage}). Otherwise Δ=0 across the board "
        f"(steady-state tick, contributing to anti-fragility stall-detection per Axis 4)."
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("_Constitutional prior: ADR-2605192100 §1. Non-eschatological — the trajectory is the wellbecoming._")
    lines.append("")
    return "\n".join(lines)


def emit(result: TickResult, observations_dir: Path, source: str = "etzhayyim-organism pod") -> Path:
    """Write the cycle file and return its path."""
    now = _dt.datetime.now(_tz_jst())
    stamp = now.strftime("%y%m%d%H%M")
    fname = f"{stamp}-cycle-{result.cycle:02d}.md"
    out = observations_dir / fname
    if out.exists():
        # avoid overwriting an existing cycle file from another tick in the same minute
        for suffix in ("b", "c", "d", "e"):
            alt = observations_dir / f"{stamp}{suffix}-cycle-{result.cycle:02d}.md"
            if not alt.exists():
                out = alt
                break
    out.write_text(render_observation(result, source=source), encoding="utf-8")
    return out
