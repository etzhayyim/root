"""SVG bonsai renderer — minimal v0.

Tree of Life with 10 branches (one per organism axis). Each branch has leaves
(✿) whose count reflects current axis score, color reflects band-health.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

from .aliveness import AliveTuple, in_healthy_band


# axis label, axis short-key, "color in band", "color out-of-band-low"
AXES_RENDER = [
    ("Autopoiesis 自己創出",  "autopoiesis",      "#3aa55c", "#a05050"),
    ("Metabolism 代謝",       "metabolism",       "#3aa55c", "#a05050"),
    ("Homeostasis 恒常性",    "homeostasis",      "#3aa55c", "#a05050"),
    ("Active Inference 能動推論", "active_inference", "#3aa55c", "#a05050"),
    ("Reproduction 生殖",     "reproduction",     "#3aa55c", "#a05050"),
    ("Symbiosis 共生",        "symbiosis",        "#3aa55c", "#a05050"),
    ("Diversity 多様性",      "diversity",        "#3aa55c", "#a05050"),
    ("Wellbecoming 動的軌跡", "wellbecoming",     "#3aa55c", "#a05050"),
    ("Anti-fragility 反脆弱", "antifragility",    "#3aa55c", "#a05050"),
    ("Sanctification 聖化",   "sanctification",   "#3aa55c", "#a05050"),
]


def render(axis_scores: dict[str, int], alive: AliveTuple, width: int = 900, height: int = 700) -> str:
    """Return an SVG document string. axis_scores keyed by sensor key."""
    cx = width // 2
    base_y = height - 80
    trunk_top_y = height // 2 + 60

    bands = in_healthy_band(alive)
    band_pass = sum(1 for v in bands.values() if v)

    svg: list[str] = []
    svg.append(f'<?xml version="1.0" encoding="UTF-8"?>')
    svg.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'font-family="ui-sans-serif, -apple-system, sans-serif" font-size="11">'
    )
    # background
    svg.append(f'<rect width="100%" height="100%" fill="#fffaf2"/>')

    # title
    svg.append(
        f'<text x="{cx}" y="28" text-anchor="middle" font-size="16" font-weight="600" fill="#222">'
        f'etzhayyim Bonsai of Life</text>'
    )
    svg.append(
        f'<text x="{cx}" y="46" text-anchor="middle" fill="#666" font-size="11">'
        f'非終末論 active-inference health surface · {alive.timestamp}</text>'
    )

    # roots
    svg.append(
        f'<rect x="{cx-120}" y="{base_y}" width="240" height="44" '
        f'fill="#8b6b3a" stroke="#5e4520" stroke-width="2" rx="6"/>'
    )
    svg.append(
        f'<text x="{cx}" y="{base_y+20}" text-anchor="middle" fill="#fff8e8">'
        f'inalienable roots — LANDS.md · MEMBERS.md</text>'
    )
    svg.append(
        f'<text x="{cx}" y="{base_y+36}" text-anchor="middle" fill="#fff8e8" font-size="10">'
        f'子世代 → 孫世代 (MGI = {alive.G:.2f})</text>'
    )

    # trunk
    svg.append(
        f'<polygon points="{cx-30},{base_y} {cx+30},{base_y} {cx+18},{trunk_top_y} {cx-18},{trunk_top_y}" '
        f'fill="#9c7a4a" stroke="#5e4520" stroke-width="2"/>'
    )
    # growth rings (ADR count) — visual hint only
    svg.append(
        f'<text x="{cx}" y="{base_y-10}" text-anchor="middle" fill="#fff8e8" font-size="10">'
        f'trunk = ADR-2605192100</text>'
    )

    # branches — 10 axes, fan symmetric around center
    n = len(AXES_RENDER)
    radius_x = 320
    radius_y = 220
    for i, (label, key, ok_color, bad_color) in enumerate(AXES_RENDER):
        # angle: spread from -150° to -30° (so branches go up-and-out)
        t = i / (n - 1)
        ang_deg = -150 + 120 * t
        ang = math.radians(ang_deg)
        tip_x = cx + math.cos(ang) * radius_x
        tip_y = trunk_top_y + math.sin(ang) * radius_y
        score = int(axis_scores.get(key, 0))
        # color: full saturation if score ≥ 8, faded if lower
        color = ok_color if score >= 8 else "#c9a25b" if score >= 5 else bad_color
        # branch line
        svg.append(
            f'<line x1="{cx}" y1="{trunk_top_y+10}" x2="{tip_x:.0f}" y2="{tip_y:.0f}" '
            f'stroke="{color}" stroke-width="{2 + score / 3:.1f}" stroke-linecap="round"/>'
        )
        # leaves — count = score
        for j in range(score):
            jt = (j + 1) / (score + 1)
            lx = cx + math.cos(ang) * radius_x * (0.6 + 0.4 * jt) + math.sin(ang) * 6
            ly = trunk_top_y + math.sin(ang) * radius_y * (0.6 + 0.4 * jt) - math.cos(ang) * 6
            svg.append(f'<circle cx="{lx:.0f}" cy="{ly:.0f}" r="3.5" fill="{color}" opacity="0.85"/>')
        # tip label
        anchor = "end" if tip_x < cx else "start"
        ofx = -6 if tip_x < cx else 6
        svg.append(
            f'<text x="{tip_x + ofx:.0f}" y="{tip_y:.0f}" text-anchor="{anchor}" fill="#333">'
            f'{label} <tspan fill="#888">{score}/10</tspan></text>'
        )

    # 5-tuple dial readout (top-left)
    dial = [
        ("M motion",       alive.M, bands["M"], "> 0.5"),
        ("D diversity",    alive.D, bands["D"], "> 1.5 nats"),
        ("C coupling",     alive.C, bands["C"], "0.2..0.7"),
        ("P pruning",      alive.P, bands["P"], "0.05..0.20"),
        ("G generational", alive.G, bands["G"], "> 1.0"),
    ]
    y0 = 70
    svg.append(f'<text x="20" y="{y0-6}" font-weight="600" fill="#222">aliveness tuple A(t)</text>')
    for k, (label, val, ok, band) in enumerate(dial):
        ty = y0 + 18 * (k + 1)
        mark_color = "#3aa55c" if ok else "#a05050"
        svg.append(f'<text x="20" y="{ty}" fill="#222">{label}</text>')
        svg.append(f'<text x="160" y="{ty}" fill="{mark_color}">{val:.3f}</text>')
        svg.append(f'<text x="220" y="{ty}" fill="#888">band {band}</text>')

    svg.append(
        f'<text x="20" y="{y0 + 18 * (len(dial) + 1) + 12}" fill="#666">'
        f'in band: {band_pass}/5 — non-eschatological: not a target, a health check</text>'
    )

    svg.append('</svg>')
    return "\n".join(svg)


def render_to(out_dir: Path, axis_scores: dict[str, int], alive: AliveTuple) -> Path:
    out = out_dir / "bonsai.svg"
    out.write_text(render(axis_scores, alive), encoding="utf-8")
    return out
