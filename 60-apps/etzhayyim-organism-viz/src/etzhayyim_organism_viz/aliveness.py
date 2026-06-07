"""Aliveness functional A(t) — 5-tuple, NOT a scalar.

A(t) = ⟨ M, D, C, P, G ⟩

  M = motion       — Σ |Δ_axis| over last N cycles / N
  D = diversity    — Shannon entropy over cell types (nats)
  C = coupling     — mean pairwise correlation of axis trajectories
  P = pruning      — (new_cells − pruned_cells) / total over last 90 days
  G = generational — MGI: land_inherited(gen+1) / land_inherited(gen)

Each band is encoded in `ideal_state.HomeostaticRange` style. We DO NOT
compute a scalar sum — that would re-introduce eschatology by allowing
trade-offs between dimensions. The dashboard renders 5 dials; the operator
reads all five.
"""

from __future__ import annotations

import math
import re
import statistics
from dataclasses import dataclass, field
from pathlib import Path

_CYCLE_FILE = re.compile(r"-cycle-(\d+)\.md$")
_AXIS_ROW = re.compile(
    r"^\|\s*\d+\s*\|\s*\*{0,2}([A-Za-z][A-Za-z\- ]*[A-Za-z])\*{0,2}[^\|]*\|\s*\*{0,2}(\d+)\s*/\s*10",
    re.MULTILINE,
)


@dataclass
class AliveTuple:
    M: float
    D: float
    C: float
    P: float
    G: float
    timestamp: str = ""
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "M_motion":       round(self.M, 4),
            "D_diversity":    round(self.D, 4),
            "C_coupling":     round(self.C, 4),
            "P_pruning":      round(self.P, 4),
            "G_generational": round(self.G, 4),
            "timestamp":      self.timestamp,
            "notes":          self.notes,
        }


# ── helpers ────────────────────────────────────────────────────────────────

def _read_cycles(observations_dir: Path) -> list[tuple[int, dict[str, int]]]:
    """Return [(cycle_number, {axis_name: score}), ...] sorted by cycle."""
    out: list[tuple[int, dict[str, int]]] = []
    for f in sorted(observations_dir.glob("*-cycle-*.md")):
        m = _CYCLE_FILE.search(f.name)
        if not m:
            continue
        n = int(m.group(1))
        body = f.read_text(encoding="utf-8", errors="ignore")
        axes: dict[str, int] = {}
        for name, score in _AXIS_ROW.findall(body):
            axes[name.strip().lower()] = int(score)
        if axes:
            out.append((n, axes))
    return out


# ── M motion ───────────────────────────────────────────────────────────────

def motion(observations_dir: Path, repo: Path | None = None, window: int = 7) -> tuple[float, list[str]]:
    """Motion = axis-trajectory motion + ecosystem creation rate.

    M = axis_Δ_per_cycle + 0.3 · artefacts_per_day

    Rationale: axes converging at 10/10 is a *good* steady state — they
    shouldn't keep moving. But the organism should still be CREATING:
    new ADRs, new observation cycles, new cells, sister-corps. So motion
    also includes daily creation count (weighted by 0.3 so one daily
    artefact contributes 0.3 to M).
    """
    import time as _time
    cycles = _read_cycles(observations_dir)
    # axis motion
    axis_M = 0.0
    transitions = 0
    if len(cycles) >= 2:
        recent = cycles[-(window + 1):]
        deltas: list[float] = []
        for (_, a), (_, b) in zip(recent, recent[1:]):
            keys = set(a) | set(b)
            for k in keys:
                deltas.append(abs(b.get(k, 0) - a.get(k, 0)))
        if deltas:
            axis_M = statistics.mean(deltas)
            transitions = len(recent) - 1
    # creation rate (artefacts per day over last `window` days).
    # Use filename-encoded timestamps (YYMMDDHHMM-...) for ADRs and cycles
    # — robust against checkout mtime artifacts. Cell creation we cannot
    # detect from filesystem alone (no timestamped name), so excluded.
    import datetime as _dt, re as _re
    now = _time.time()
    cutoff = now - window * 86400
    new_adrs = 0
    new_obs = 0
    if repo is not None:
        ts_pat = _re.compile(r"^(\d{10,12})[-_.]")
        def _filename_ts(p: Path) -> float:
            m = ts_pat.match(p.name)
            if not m:
                return 0.0
            try:
                # YYMMDDHHMM = 10 chars; YYMMDDHHMMSS = 12 chars
                raw = m.group(1)
                if len(raw) == 10:
                    dt = _dt.datetime.strptime(raw, "%y%m%d%H%M")
                elif len(raw) == 12:
                    dt = _dt.datetime.strptime(raw, "%y%m%d%H%M%S")
                else:
                    return 0.0
                return dt.replace(tzinfo=_dt.timezone(_dt.timedelta(hours=9))).timestamp()
            except ValueError:
                return 0.0
        adr_dir = repo / "90-docs" / "adr"
        if adr_dir.is_dir():
            for f in adr_dir.glob("*.md"):
                ts = _filename_ts(f)
                if ts and ts > cutoff:
                    new_adrs += 1
        if observations_dir.is_dir():
            for f in observations_dir.glob("*-cycle-*.md"):
                ts = _filename_ts(f)
                if ts and ts > cutoff:
                    new_obs += 1
    creation_per_day = (new_adrs + new_obs) / max(1, window)
    M = axis_M + 0.3 * creation_per_day
    return M, [
        f"motion: axis_Δ={axis_M:.3f}/cycle ({transitions} transitions) + 0.3·creation={creation_per_day:.2f}/day → M={M:.3f}",
        f"  creation last {window}d (filename-dated): {new_adrs} ADR + {new_obs} cycle obs",
    ]


# ── D diversity ────────────────────────────────────────────────────────────

def diversity(repo: Path) -> tuple[float, list[str]]:
    """Shannon entropy over cell-type counts (nats).

    Each cell directory under 40-engine/kotoba/crates/kotoba-kotodama/cells/ is its own category.
    The earlier version collapsed yorishiro_* into one bucket which
    systematically under-counted the 八百万 (variation as worship) signal —
    each yorishiro binding is a distinct external integration.
    """
    cells_dir = repo / "20-actors" / "kotodama" / "cells"
    if not cells_dir.is_dir():
        return 0.0, ["diversity: cells dir missing"]
    counts: dict[str, int] = {}
    for child in cells_dir.iterdir():
        if not child.is_dir():
            continue
        counts[child.name] = 1
    total = sum(counts.values())
    if total == 0:
        return 0.0, ["diversity: no cells"]
    H = -sum((c / total) * math.log(c / total) for c in counts.values())
    return H, [f"diversity: H = {H:.3f} nats over {len(counts)} distinct cells (八百万)"]


# ── C coupling ─────────────────────────────────────────────────────────────

def coupling(observations_dir: Path) -> tuple[float, list[str]]:
    """Mean pairwise Pearson correlation between axis trajectories."""
    cycles = _read_cycles(observations_dir)
    if len(cycles) < 3:
        return 0.0, ["coupling: <3 cycles → undefined; returning 0"]
    # build per-axis time series
    axis_keys: set[str] = set()
    for _, a in cycles:
        axis_keys |= set(a)
    series: dict[str, list[float]] = {k: [] for k in axis_keys}
    for _, a in cycles:
        for k in axis_keys:
            series[k].append(float(a.get(k, 0)))
    # Pearson correlation, pairwise
    def pearson(x: list[float], y: list[float]) -> float | None:
        n = len(x)
        if n < 2:
            return None
        mx, my = statistics.mean(x), statistics.mean(y)
        num = sum((a - mx) * (b - my) for a, b in zip(x, y))
        dx = math.sqrt(sum((a - mx) ** 2 for a in x))
        dy = math.sqrt(sum((b - my) ** 2 for b in y))
        if dx == 0 or dy == 0:
            return None
        return num / (dx * dy)
    keys = sorted(series)
    corrs: list[float] = []
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            r = pearson(series[keys[i]], series[keys[j]])
            if r is not None and not math.isnan(r):
                corrs.append(r)
    if not corrs:
        return 0.0, ["coupling: no valid correlations"]
    C = statistics.mean(corrs)
    return C, [f"coupling: mean pairwise r = {C:.3f} across {len(corrs)} axis pairs"]


# ── P pruning ──────────────────────────────────────────────────────────────

def pruning(repo: Path, *_ignored, **__ignored) -> tuple[float, list[str]]:
    """Bonsai-tending indicator (mtime-independent).

    Without git history (the pod doesn't have it) and with checkout-mtime
    noise in fresh clones, we use a content-based signal: a cell is
    "tended" if it has a `cell.py` AND a docstring. A cell with only a
    stub or no body is a candidate for pruning.

    Semantics:
      P = tended_cells / total_cells       (range 0..1)
      Healthy band: 0.5 .. 0.95
      - P < 0.5 → many half-finished cells; needs operator attention
      - P = 1.0 → all tended (fine; the band tolerates this)
    """
    cells_dir = repo / "20-actors" / "kotodama" / "cells"
    if not cells_dir.is_dir():
        return 0.0, ["pruning: cells dir missing"]
    tended = 0
    total = 0
    for d in cells_dir.iterdir():
        if not d.is_dir():
            continue
        total += 1
        cell_py = d / "cell.py"
        if not cell_py.exists():
            continue
        try:
            txt = cell_py.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if '"""' in txt and len(txt) > 200:
            tended += 1
    if total == 0:
        return 0.0, ["pruning: 0 cells"]
    P = tended / total
    return P, [f"pruning: {tended}/{total} cells with cell.py + docstring + >200 bytes → P={P:.3f}"]


# ── G generational ─────────────────────────────────────────────────────────

def generational(repo: Path) -> tuple[float, list[str]]:
    """MGI estimate from LANDS.md and MEMBERS.md.

    Until on-chain MGI is computable, we use a proxy: presence of
    multi-generation language in LANDS.md + non-empty MEMBERS.md ≥ 1.0.
    Lift toward higher values when generation markers (Gen 0, Gen 1, ...)
    appear in observations.
    """
    lands = repo / "LANDS.md"
    members = repo / "MEMBERS.md"
    base = 1.0
    notes: list[str] = []
    if lands.exists():
        notes.append("LANDS.md present (inalienable inheritance roster)")
    else:
        return 0.0, ["generational: LANDS.md missing → MGI undefined"]
    if members.exists():
        notes.append("MEMBERS.md present (multi-gen roster)")
    obs = repo / "_observations"
    gen_marks = 0
    if obs.is_dir():
        for f in obs.glob("*-cycle-*.md"):
            t = f.read_text(encoding="utf-8", errors="ignore")
            gen_marks += t.count("Gen 0") + t.count("Gen 1") + t.count("multi-generation")
    # bounded lift — every 10 mentions adds 0.05 (NEVER caps; non-eschatological)
    lift = 0.05 * (gen_marks // 10)
    G = base + lift
    notes.append(f"generational: gen_marks={gen_marks} → MGI≈{G:.3f}")
    return G, notes


# ── compose ────────────────────────────────────────────────────────────────

def compute(repo: Path) -> AliveTuple:
    import datetime as _dt
    obs = repo / "_observations"
    M, n1 = motion(obs, repo)
    D, n2 = diversity(repo)
    C, n3 = coupling(obs)
    P, n4 = pruning(repo)
    G, n5 = generational(repo)
    return AliveTuple(
        M=M, D=D, C=C, P=P, G=G,
        timestamp=_dt.datetime.now(_dt.timezone(_dt.timedelta(hours=9))).isoformat(timespec="seconds"),
        notes=n1 + n2 + n3 + n4 + n5,
    )


def in_healthy_band(a: AliveTuple) -> dict[str, bool]:
    return {
        "M": a.M > 0.5,
        "D": a.D > 1.5,
        "C": 0.2 <= a.C <= 0.7,
        "P": 0.5 <= a.P <= 1.0,   # bonsai-tending ratio (cells with cell.py + docstring / total)
        "G": a.G > 1.0,
    }
