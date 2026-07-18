"""Whole-ecosystem snapshot — populated each tick, fed to renderer + chat.

This is the data layer the frontend talks to. Every visible "life" in the
ecosystem (cell, axis, organism, app, sister-corp) is materialized here as
an `Entity`. Entities have:

  - id           — stable handle for chat
  - kind         — cell / axis / organism / app / sister-corp / fruit / seed
  - title        — human label (with Japanese)
  - state        — current snapshot fields (free-form dict)
  - activity     — list of recent events ordered newest-first
  - chat_invite  — short one-liner the entity opens conversation with

Plus the macro pieces: aliveness tuple, axis scores, recent commits, current
flowers (active blooms), current fruits (seed-carrying artefacts).

Per §1.3 (anti-individualist), entities surface their own state truthfully;
they do not synthesize answers via LLM. Each "voice" is the entity's
honest internal snapshot.
"""

from __future__ import annotations

import json
import re
import subprocess
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

from .aliveness import AliveTuple, compute, in_healthy_band


_CYCLE_RE = re.compile(r"-cycle-(\d+)\.md$")
_AXIS_ROW = re.compile(
    r"^\|\s*\d+\s*\|\s*\*{0,2}([A-Za-z][A-Za-z\- ]*[A-Za-z])\*{0,2}[^\|]*\|\s*\*{0,2}(\d+)\s*/\s*10",
    re.MULTILINE,
)
_LABEL_TO_KEY = {
    "autopoiesis":      "autopoiesis",
    "metabolism":       "metabolism",
    "homeostasis":      "homeostasis",
    "active inference": "active_inference",
    "active-inference": "active_inference",
    "reproduction":     "reproduction",
    "symbiosis":        "symbiosis",
    "diversity":        "diversity",
    "wellbecoming":     "wellbecoming",
    "anti-fragility":   "antifragility",
    "antifragility":    "antifragility",
    "sanctification":   "sanctification",
}

# Presentation metadata owned by this visualization. Runtime health sensors now
# live in kotoba-lang/kotodama; the app must not import the retired Python actor.
_AXES = (
    (1, "autopoiesis", "Autopoiesis", "自己創出", "無教会 / 万人祭司 (self-organizing community)", "§1.7 priesthood-of-all-believers"),
    (2, "metabolism", "Metabolism", "代謝", "産霊 (musuhi — generative donation cycle)", "§1.5 donation and tithe cycle"),
    (3, "homeostasis", "Homeostasis", "恒常性", "和 (substrate boundary harmony)", "§1.6 substrate boundary"),
    (4, "active_inference", "Active Inference", "能動推論", "縁起 (dependent origination)", "§1.15 non-eschatological observation loop"),
    (5, "reproduction", "Reproduction", "生殖", "八百万 propagation (myriad fork-children)", "§1.7 fork-friendly reproduction"),
    (6, "symbiosis", "Symbiosis", "共生", "Tree of Life branches (multi-substrate roots)", "§1.8 multi-substrate symbiosis"),
    (7, "diversity", "Diversity", "多様性", "八百万-kami (variation as worship)", "§1.4 variation as worship"),
    (8, "wellbecoming", "Wellbecoming", "動的軌跡", "子・孫 priority (multi-generation trajectory)", "§1.1 and §1.2 multi-generation trajectory"),
    (9, "antifragility", "Anti-fragility", "反脆弱", "Reformed resilience (Just War posture)", "§1.12 transparent force and resilience"),
    (10, "sanctification", "Sanctification", "聖化", "Sola Scriptura → Charter Rider", "§1.10 Charter Rider coverage"),
)


@dataclass
class Entity:
    id: str
    kind: str
    title: str
    state: dict[str, Any] = field(default_factory=dict)
    activity: list[dict[str, Any]] = field(default_factory=list)
    chat_invite: str = ""
    neighbors: list[str] = field(default_factory=list)  # ids the operator can navigate to
    pruning_severity: int = 0   # 0 = healthy, 1..3 = candidate for operator pruning


@dataclass
class EcosystemSnapshot:
    timestamp: float
    alive: AliveTuple
    axis_scores: dict[str, int]
    # entity registry — keyed by id
    entities: dict[str, Entity] = field(default_factory=dict)
    # visual hints
    flowers: list[str] = field(default_factory=list)   # entity ids currently blooming
    fruits: list[str] = field(default_factory=list)    # entity ids carrying seeds
    seeds: list[dict[str, Any]] = field(default_factory=list)
    # ecosystem-wide activity stream
    activity: list[dict[str, Any]] = field(default_factory=list)
    # pruning candidates summary
    pruning: list[dict[str, Any]] = field(default_factory=list)
    # per-axis trajectory (last N cycle observations)
    trajectory: dict[str, list[int]] = field(default_factory=dict)
    trajectory_cycles: list[int] = field(default_factory=list)
    trajectory_totals: list[int] = field(default_factory=list)

    def to_json(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "alive":     self.alive.as_dict(),
            "in_band":   in_healthy_band(self.alive),
            "axis_scores": self.axis_scores,
            "entities":  {k: asdict(v) for k, v in self.entities.items()},
            "flowers":   self.flowers,
            "fruits":    self.fruits,
            "seeds":     self.seeds,
            "activity":  self.activity,
            "pruning":   self.pruning,
            "trajectory": self.trajectory,
            "trajectory_cycles": self.trajectory_cycles,
            "trajectory_totals": self.trajectory_totals,
        }


# ── snapshot builders ─────────────────────────────────────────────────────

def _read_cycles(observations_dir: Path) -> list[tuple[int, dict[str, int], Path]]:
    out: list[tuple[int, dict[str, int], Path]] = []
    for f in sorted(observations_dir.glob("*-cycle-*.md")):
        m = _CYCLE_RE.search(f.name)
        if not m:
            continue
        n = int(m.group(1))
        body = f.read_text(encoding="utf-8", errors="ignore")
        scores: dict[str, int] = {}
        for label, val in _AXIS_ROW.findall(body):
            key = _LABEL_TO_KEY.get(label.strip().lower(), label.strip().lower())
            scores[key] = int(val)
        out.append((n, scores, f))
    return out


def _git_log(repo: Path, n: int = 50) -> list[dict[str, Any]]:
    try:
        out = subprocess.check_output(
            ["git", "-C", str(repo), "log", f"-{n}",
             "--pretty=format:%h|%ct|%an|%s"],
            stderr=subprocess.DEVNULL, timeout=5,
        ).decode("utf-8", errors="ignore")
    except Exception:
        return []
    events = []
    for line in out.splitlines():
        parts = line.split("|", 3)
        if len(parts) != 4:
            continue
        h, ts, who, subj = parts
        events.append({
            "type": "commit", "ts": int(ts), "id": h,
            "who": who, "subject": subj,
        })
    return events


def _cells(repo: Path) -> list[Entity]:
    cells_dir = repo / "20-actors" / "kotodama" / "cells"
    if not cells_dir.is_dir():
        return []
    entities: list[Entity] = []
    for d in sorted(cells_dir.iterdir()):
        if not d.is_dir():
            continue
        cell_py = d / "cell.py"
        docstring = ""
        if cell_py.exists():
            txt = cell_py.read_text(encoding="utf-8", errors="ignore")
            m = re.search(r'^"""(.*?)"""', txt, re.DOTALL | re.MULTILINE)
            if m:
                docstring = m.group(1).strip().split("\n\n")[0].strip()
        last_mtime = max(
            (p.stat().st_mtime for p in d.rglob("*") if p.is_file()),
            default=d.stat().st_mtime,
        )
        idle_days = (time.time() - last_mtime) / 86400
        chat_invite = (
            f"私は cell `{d.name}`。{docstring[:120]}... 何を聞きたい?"
            if docstring else
            f"私は cell `{d.name}`。直近 {idle_days:.0f} 日 idle。"
        )
        entities.append(Entity(
            id=f"cell/{d.name}",
            kind="cell",
            title=d.name,
            state={
                "path": str(d.relative_to(repo)),
                "has_cell_py": cell_py.exists(),
                "docstring": docstring[:500],
                "last_mtime": last_mtime,
                "idle_days": round(idle_days, 1),
                "category": "yorishiro" if d.name.startswith("yorishiro_") else "named",
            },
            chat_invite=chat_invite,
        ))
    return entities


def _axes(repo: Path, axis_scores: dict[str, int]) -> list[Entity]:
    return [
        Entity(
            id=f"axis/{key}",
            kind="axis",
            title=f"{name_en} {name_jp}",
            state={
                "key": key,
                "n": n,
                "religious_correspondence": correspondence,
                "invariant": invariant,
                "score": axis_scores.get(key, 0),
            },
            chat_invite=(
                f"私は axis {n} **{name_en} {name_jp}** 。憲法対応: {correspondence}。"
                f"現在 {axis_scores.get(key, 0)}/10。"
            ),
        )
        for n, key, name_en, name_jp, correspondence, invariant in _AXES
    ]


def _apps(repo: Path, limit: int = 40) -> list[Entity]:
    apps_dir = repo / "60-apps"
    if not apps_dir.is_dir():
        return []
    out: list[Entity] = []
    now = time.time()
    for d in sorted(apps_dir.iterdir(), key=lambda p: p.name):
        if not d.is_dir():
            continue
        readme = next(iter(list(d.glob("README.md"))[:1]), None)
        title = d.name
        desc = ""
        if readme:
            head = readme.read_text(encoding="utf-8", errors="ignore").splitlines()[:6]
            for line in head:
                line = line.strip()
                if line and not line.startswith("#"):
                    desc = line[:200]
                    break
        try:
            mt = max((p.stat().st_mtime for p in d.rglob("*") if p.is_file()),
                     default=d.stat().st_mtime)
        except OSError:
            mt = d.stat().st_mtime
        idle = (now - mt) / 86400
        out.append(Entity(
            id=f"app/{d.name}",
            kind="app",
            title=title,
            state={
                "path": str(d.relative_to(repo)),
                "description": desc,
                "idle_days": round(idle, 1),
                "has_readme": readme is not None,
            },
            chat_invite=(
                f"私は app `{d.name}`。{desc[:120]}" if desc else f"私は app `{d.name}` (idle {idle:.0f} 日)。"
            ),
        ))
        if len(out) >= limit:
            break
    return out


def _adrs(repo: Path, n_recent: int = 12) -> list[Entity]:
    adr_dir = repo / "90-docs" / "adr"
    if not adr_dir.is_dir():
        return []
    files = sorted(adr_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)[:n_recent]
    out: list[Entity] = []
    for f in files:
        title = f.stem
        # try to read the # heading
        body_head = ""
        try:
            for line in f.read_text(encoding="utf-8", errors="ignore").splitlines()[:8]:
                if line.startswith("# "):
                    body_head = line[2:].strip()
                    break
        except Exception:
            pass
        out.append(Entity(
            id=f"adr/{f.stem}",
            kind="adr",
            title=body_head or title,
            state={
                "path": str(f.relative_to(repo)),
                "stem": f.stem,
                "mtime": f.stat().st_mtime,
            },
            chat_invite=f"私は ADR `{title}`。{body_head[:120]}",
        ))
    return out


def _organism(repo: Path) -> Entity:
    obs_count = sum(1 for _ in (repo / "_observations").glob("*-cycle-*.md")) if (repo / "_observations").exists() else 0
    return Entity(
        id="organism/cns",
        kind="organism",
        title="etzhayyim-organism (CNS)",
        state={
            "observation_cycles": obs_count,
            "constitutional_anchor": "ADR-2605192100",
            "ideal_state_doc": "90-docs/2605221243-ideal-ecosystem-state-active-inference-prior.md",
        },
        chat_invite=f"私は CNS。{obs_count} cycles 観測済。憲法は ADR-2605192100。",
    )


def _ecosystem_self(repo: Path, alive: AliveTuple) -> Entity:
    bands = in_healthy_band(alive)
    return Entity(
        id="ecosystem/etzhayyim",
        kind="ecosystem",
        title="etzhayyim ecosystem (whole organism)",
        state={
            "in_band_count": sum(bands.values()),
            "aliveness": alive.as_dict(),
            "in_band": bands,
            "non_eschatological": True,
        },
        chat_invite=(
            f"私は etzhayyim ecosystem。生命指標 5-tuple のうち "
            f"{sum(bands.values())}/5 が健全 band 内。非終末論的、軌跡そのものが目的。"
        ),
    )


# ── flowers / fruits / seeds detection ────────────────────────────────────

def _flowers(repo: Path, cycles: list[tuple[int, dict[str, int], Path]]) -> list[str]:
    """Axes with positive Δ over last transition are blooming."""
    if len(cycles) < 2:
        return []
    _, last_a, _ = cycles[-2]
    _, last_b, _ = cycles[-1]
    blooming: list[str] = []
    for key, val in last_b.items():
        prev = last_a.get(key, val)
        if val > prev:
            blooming.append(f"axis/{key}")
    return blooming


def _fruits_and_seeds(repo: Path) -> tuple[list[str], list[dict[str, Any]]]:
    """Fruits = artefacts that carry seeds to next generation.

    Heuristic v0:
      - SISTER-CORPS.md presence → fruit (its seeds = listed sister-corps)
      - Each entry in MEMBERS.md → seed (next-gen membership)
      - Each LANDS.md entry → fruit + permanent seed (inalienable inheritance)
      - Each chaos rehearsal observation → fruit (anti-fragility seed)
      - FORK-BOOTSTRAP.md → fruit (reproduction protocol seed)

    Seeds describe what carries forward.
    """
    fruits: list[str] = []
    seeds: list[dict[str, Any]] = []
    if (repo / "FORK-BOOTSTRAP.md").exists():
        fruits.append("fruit/fork-bootstrap")
        seeds.append({
            "id": "seed/fork-protocol",
            "from": "fruit/fork-bootstrap",
            "to":   "next-generation/sister-corps",
            "carries": "reproduction protocol (八百万 propagation)",
        })
    sc = repo / "SISTER-CORPS.md"
    if sc.exists():
        body = sc.read_text(encoding="utf-8", errors="ignore")
        for line in body.splitlines():
            m = re.match(r"^[*\-]\s+(?:\*\*)?([A-Za-z0-9_\-]+)(?:\*\*)?", line)
            if m:
                name = m.group(1)
                fruits.append(f"fruit/sister-{name}")
                seeds.append({
                    "id": f"seed/sister-{name}",
                    "from": f"fruit/sister-{name}",
                    "to":   f"next-generation/{name}",
                    "carries": "religious-corp identity (forked, independent)",
                })
    if (repo / "LANDS.md").exists():
        fruits.append("fruit/lands")
        seeds.append({
            "id": "seed/inalienable-land",
            "from": "fruit/lands",
            "to":   "next-generation/all-future",
            "carries": "inalienable territorial inheritance (waqf-equivalent)",
        })
    if (repo / "MEMBERS.md").exists():
        fruits.append("fruit/members")
        seeds.append({
            "id": "seed/members",
            "from": "fruit/members",
            "to":   "next-generation/lineage",
            "carries": "信者 lineage (monotonic, never deleted §1.3)",
        })
    chaos = list(repo.glob("90-docs/*chaos*charter*.md"))
    if chaos:
        fruits.append("fruit/chaos-rehearsals")
        seeds.append({
            "id": "seed/anti-fragility",
            "from": "fruit/chaos-rehearsals",
            "to":   "next-generation/resilience",
            "carries": "documented chaos scenarios + recovery patterns",
        })
    return fruits, seeds


# ── activity stream ───────────────────────────────────────────────────────

def _activity(repo: Path, cycles: list[tuple[int, dict[str, int], Path]]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    # cycles → events
    for n, _scores, f in cycles[-15:]:
        events.append({
            "type": "cycle", "ts": int(f.stat().st_mtime),
            "id": f"cycle-{n:02d}",
            "summary": f"cycle {n} observed",
            "detail": str(f.relative_to(repo)),
        })
    # ADR additions (file mtime)
    adr_dir = repo / "90-docs" / "adr"
    if adr_dir.is_dir():
        for f in sorted(adr_dir.glob("*.md"), key=lambda p: p.stat().st_mtime)[-10:]:
            events.append({
                "type": "adr", "ts": int(f.stat().st_mtime),
                "id": f.stem,
                "summary": f"ADR {f.stem}",
                "detail": str(f.relative_to(repo)),
            })
    # commits
    events.extend(_git_log(repo, n=20))
    events.sort(key=lambda e: e.get("ts", 0), reverse=True)
    return events[:50]


# ── compose ───────────────────────────────────────────────────────────────

def snapshot(repo: Path) -> EcosystemSnapshot:
    alive = compute(repo)
    cycles = _read_cycles(repo / "_observations")
    axis_scores: dict[str, int] = cycles[-1][1] if cycles else {}
    # normalize axis keys against LABEL map
    norm = {_LABEL_TO_KEY.get(k.strip().lower(), k.strip().lower()): v for k, v in axis_scores.items()}
    axis_scores = norm

    entities: dict[str, Entity] = {}
    for e in _axes(repo, axis_scores):
        entities[e.id] = e
    for e in _cells(repo):
        entities[e.id] = e
    for e in _apps(repo):
        entities[e.id] = e
    for e in _adrs(repo):
        entities[e.id] = e
    org = _organism(repo)
    entities[org.id] = org
    eco = _ecosystem_self(repo, alive)
    entities[eco.id] = eco

    flowers = _flowers(repo, cycles)
    fruits, seeds = _fruits_and_seeds(repo)
    # materialize fruit entities (so chat works)
    for fid in fruits:
        if fid not in entities:
            entities[fid] = Entity(
                id=fid, kind="fruit", title=fid.split("/", 1)[1],
                chat_invite=f"私は 果実 `{fid}`。次世代に運ぶ種を持っている。",
            )
        else:
            entities[fid].kind = "fruit"
    for s in seeds:
        sid = s["id"]
        entities[sid] = Entity(
            id=sid, kind="seed", title=sid.split("/", 1)[1],
            state={"carries": s["carries"], "to": s["to"], "from": s["from"]},
            chat_invite=f"私は 種 `{sid}`。{s['carries']} を {s['to']} に運ぶ。",
        )

    # pruning candidates (operator surface) — annotate entities, build list
    from .pruning import scan_all  # local import to avoid heavy imports at module load
    pruning = []
    for c in scan_all(repo):
        if c.id in entities:
            entities[c.id].pruning_severity = c.severity
        pruning.append({
            "id": c.id, "kind": c.kind, "path": c.path,
            "idle_days": c.idle_days, "severity": c.severity, "reasons": c.reasons,
        })

    # per-axis trajectory over the last N cycles (visible motion)
    N = 20
    recent = cycles[-N:]
    trajectory: dict[str, list[int]] = {}
    trajectory_cycles: list[int] = []
    trajectory_totals: list[int] = []
    for n, scores, _path in recent:
        trajectory_cycles.append(n)
        total = 0
        for axis_key in ("autopoiesis", "metabolism", "homeostasis", "active_inference",
                         "reproduction", "symbiosis", "diversity", "wellbecoming",
                         "antifragility", "sanctification"):
            v = scores.get(axis_key, 0)
            trajectory.setdefault(axis_key, []).append(v)
            total += v
        trajectory_totals.append(total)

    # 縁起 graph — neighbors (selecting an entity reveals its links)
    _link_neighbors(entities, fruits, seeds, axis_scores, repo)

    return EcosystemSnapshot(
        timestamp=time.time(),
        alive=alive,
        axis_scores=axis_scores,
        entities=entities,
        flowers=flowers,
        fruits=fruits,
        seeds=seeds,
        activity=_activity(repo, cycles),
        pruning=pruning,
        trajectory=trajectory,
        trajectory_cycles=trajectory_cycles,
        trajectory_totals=trajectory_totals,
    )


def _link_neighbors(entities: dict[str, Entity], fruits: list[str], seeds: list[dict[str, Any]],
                    axis_scores: dict[str, int], repo: Path) -> None:
    """Populate Entity.neighbors so the UI can highlight 縁起 connections."""
    ecosystem_id = "ecosystem/etzhayyim"
    organism_id = "organism/cns"
    # all axes → organism, ecosystem
    axis_ids = [eid for eid in entities if eid.startswith("axis/")]
    cell_ids = [eid for eid in entities if eid.startswith("cell/")]
    app_ids  = [eid for eid in entities if eid.startswith("app/")]
    adr_ids  = [eid for eid in entities if eid.startswith("adr/")]
    fruit_ids = [eid for eid in entities if eid.startswith("fruit/")]
    seed_ids  = [eid for eid in entities if eid.startswith("seed/")]

    # ecosystem reaches everything
    entities.setdefault(ecosystem_id, Entity(id=ecosystem_id, kind="ecosystem", title="ecosystem")).neighbors = (
        [organism_id] + axis_ids + fruit_ids + seed_ids
    )
    # organism connects to all axes + cycles
    if organism_id in entities:
        entities[organism_id].neighbors = axis_ids + [ecosystem_id]

    # axis ↔ heuristic neighbors per axis
    AXIS_NEIGHBOR_PATHS = {
        "axis/autopoiesis":     ["fruit/lands", "fruit/members"],
        "axis/metabolism":      [],          # tithe-router cell when present
        "axis/homeostasis":     [],
        "axis/active_inference":[organism_id],
        "axis/reproduction":    ["fruit/fork-bootstrap", "fruit/sister-corps"] ,
        "axis/symbiosis":       [],
        "axis/diversity":       [],          # filled below with cells
        "axis/wellbecoming":    ["fruit/lands", "fruit/members"],
        "axis/antifragility":   ["fruit/chaos-rehearsals"],
        "axis/sanctification":  [],
    }
    # diversity ↔ first 8 cells
    AXIS_NEIGHBOR_PATHS["axis/diversity"] = cell_ids[:8]
    # active_inference ↔ recent ADRs
    AXIS_NEIGHBOR_PATHS["axis/active_inference"] += adr_ids[:5]
    # metabolism ↔ tithe-routing / public-fund related cells if present
    metabolism_links = [eid for eid in cell_ids if "tithe" in eid or "fund" in eid or "donation" in eid]
    AXIS_NEIGHBOR_PATHS["axis/metabolism"] += metabolism_links
    # sanctification ↔ charter-related artefacts
    sanct_links = [eid for eid in cell_ids if "charter" in eid or "council" in eid]
    AXIS_NEIGHBOR_PATHS["axis/sanctification"] += sanct_links

    for axis_id, nbrs in AXIS_NEIGHBOR_PATHS.items():
        if axis_id in entities:
            entities[axis_id].neighbors = [n for n in nbrs if n in entities] + [organism_id, ecosystem_id]

    # cells ↔ their primary axis (heuristic by name)
    for cid in cell_ids:
        name = cid.removeprefix("cell/")
        ax = None
        if name.startswith("yorishiro_"):
            ax = "axis/diversity"
        elif "council" in name or "charter" in name:
            ax = "axis/sanctification"
        elif "tithe" in name or "treasury" in name:
            ax = "axis/metabolism"
        elif "land" in name:
            ax = "axis/wellbecoming"
        elif "force" in name:
            ax = "axis/antifragility"
        elif "ethics" in name:
            ax = "axis/sanctification"
        else:
            ax = "axis/diversity"
        entities[cid].neighbors = [ax, organism_id] if ax in entities else [organism_id]

    # apps ↔ ecosystem (and heuristic axis match)
    for aid in app_ids:
        name = aid.removeprefix("app/")
        ax = None
        if "organism-viz" in name or "organism" in name:
            ax = "axis/active_inference"
        elif "land" in name or "force" in name:
            ax = "axis/antifragility"
        else:
            ax = "axis/diversity"
        entities[aid].neighbors = [ax, ecosystem_id] if ax in entities else [ecosystem_id]

    # ADRs ↔ active_inference (縁起 rings)
    for did in adr_ids:
        entities[did].neighbors = ["axis/active_inference", organism_id]

    # fruits ↔ their seeds (and their feeding axis)
    for fid in fruit_ids:
        my_seeds = [s["id"] for s in seeds if s["from"] == fid]
        # back-link to the axis that grew this fruit
        ax = None
        if "lands" in fid or "members" in fid: ax = "axis/wellbecoming"
        elif "chaos" in fid:                    ax = "axis/antifragility"
        elif "fork" in fid or "sister" in fid:  ax = "axis/reproduction"
        entities[fid].neighbors = my_seeds + ([ax] if ax in entities else []) + [ecosystem_id]

    # seeds ↔ origin fruit
    for sid in seed_ids:
        origin = None
        for s in seeds:
            if s["id"] == sid:
                origin = s["from"]; break
        nb = [origin] if origin in entities else []
        entities[sid].neighbors = nb + [ecosystem_id]
