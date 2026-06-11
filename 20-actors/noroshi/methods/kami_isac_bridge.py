"""noroshi (烽) ↔ kami-autodrive ISAC sensor bridge (ADR-2606051600 §R1a). Stdlib only.

kami-autodrive (ADR-2606010600) runs a perception→planning→control GNC loop over a world of moving
agents. noroshi's ISAC waveform is the natural **sensor** for that loop: the same photonic/RF
front-end that carries the link also senses the range + radial velocity of the civilian objects around
the ego-craft, feeding collision-avoidance. This bridge drives the noroshi ISAC estimator from a
kami-autodrive-style **scenario** (objects with a range and a constant radial velocity, sampled over
frames) and produces a per-object **track** — the data contract an eventual Rust `kami-isac` crate /
kami-autodrive `IsacSensor` plant would implement.

HONEST INTEGRATION STATE (G10): the `40-engine/kami-engine` submodule is unpopulated in this checkout,
so the live Rust wiring is expressed as a WIT contract (`wit/kami-isac.wit`) + this Python reference,
not a compiled crate (the sumitsubo "op-list now, live kami-app binding follow-up" pattern). Sensing is
CIVILIAN object range/velocity only — never a person, never fire-control (G3/G4/N1/N2). No live
emission (G8); deterministic offline DSP.
"""

from __future__ import annotations

from dataclasses import dataclass

from isac_sim import IsacWaveform, SenseEstimate, Target, estimate_target, estimate_targets


@dataclass(frozen=True)
class ScenarioObject:
    """A civilian object the ego-craft must sense for collision-avoidance (NEVER a person — N2/G4)."""

    object_id: str
    range0_m: float          # initial range at frame 0
    velocity_mps: float      # radial velocity (closing > 0); constant over the window


@dataclass(frozen=True)
class TrackPoint:
    frame: int
    time_s: float
    range_m: float
    velocity_mps: float
    range_bin: int
    doppler_bin: int


def track_object(
    wf: IsacWaveform, obj: ScenarioObject, frames: int = 8, frame_dt_s: float = 0.002
) -> list[TrackPoint]:
    """Sense one object across `frames` snapshots → a kinematic track (range closes at its velocity)."""
    track: list[TrackPoint] = []
    for k in range(frames):
        t = k * frame_dt_s
        rng = obj.range0_m - obj.velocity_mps * t           # range closes over time
        if rng <= 0:
            break                                            # passed the ego-craft; stop sensing
        est: SenseEstimate = estimate_target(wf, Target(range_m=rng, velocity_mps=obj.velocity_mps))
        track.append(TrackPoint(k, round(t, 4), est.range_m, est.velocity_mps,
                                est.range_bin, est.doppler_bin))
    return track


def run_scenario(
    objects: list[ScenarioObject], wf: IsacWaveform | None = None,
    frames: int = 8, frame_dt_s: float = 0.002,
) -> dict[str, list[TrackPoint]]:
    """Run the ISAC sensor over a kami-autodrive-style multi-object scenario → {object_id: track}.

    Per-object tracking (single-target periodogram per object, ground-truth-associated) for a clean
    per-object trajectory. For one-shot scene sensing of the COMBINED echo, use `sense_frame`.
    NOTE (N4): this waveform's velocity bin is coarse (Δv≈279 m/s — a short 16-symbol frame), so the
    scenario samples FAST objects on a short interval; fine automotive velocity needs many more OFDM
    symbols (a longer coherent interval), a kami-autodrive-side configuration choice. Cross-frame
    data-association (assigning detections to tracks) remains the kami-autodrive-side follow-up.
    """
    wf = wf or IsacWaveform()
    return {o.object_id: track_object(wf, o, frames, frame_dt_s) for o in objects}


def sense_frame(objects: list[ScenarioObject], wf: IsacWaveform | None = None) -> list[SenseEstimate]:
    """One-shot multi-target scene sense: detect ALL objects from a single combined echo (CLEAN).

    The realistic GNC-frame primitive — the sensor sees one superimposed return, not one object at a
    time. Returns an unlabelled detection set (range/velocity per object); track association is the
    kami-autodrive-side step. Objects already at/behind the ego (range ≤ 0) are dropped.
    """
    wf = wf or IsacWaveform()
    targets = [Target(range_m=o.range0_m, velocity_mps=o.velocity_mps)
               for o in objects if o.range0_m > 0]
    return estimate_targets(wf, targets)


# A :representative kami-autodrive scenario: two civilian objects on a converging course with the ego.
DEMO_SCENARIO = [
    ScenarioObject("lead-vehicle", range0_m=4 * IsacWaveform().range_resolution_m,
                   velocity_mps=2 * IsacWaveform().velocity_resolution_mps),
    ScenarioObject("cross-object", range0_m=10 * IsacWaveform().range_resolution_m,
                   velocity_mps=1 * IsacWaveform().velocity_resolution_mps),
]


def report(objects: list[ScenarioObject] | None = None) -> str:
    wf = IsacWaveform()
    tracks = run_scenario(objects or DEMO_SCENARIO, wf)
    lines = [
        "# noroshi 烽 × kami-autodrive — ISAC sensor in the GNC loop",
        "",
        f"waveform: {wf.bandwidth_hz/1e6:.0f} MHz, ΔR={wf.range_resolution_m:.2f} m, "
        f"Δv={wf.velocity_resolution_mps:.1f} m/s. Civilian objects only (collision-avoidance; N1/N2).",
        "",
    ]
    for oid, track in tracks.items():
        lines.append(f"## track: {oid}  ({len(track)} frames)")
        lines.append("| frame | t (s) | range (m) | velocity (m/s) | bins (k,l) |")
        lines.append("|---|---|---|---|---|")
        for p in track:
            lines.append(f"| {p.frame} | {p.time_s} | {p.range_m:.2f} | {p.velocity_mps:.1f} | ({p.range_bin},{p.doppler_bin}) |")
        lines.append("")
    lines += [
        "> The ISAC estimate feeds kami-autodrive perception (the `IsacSensor` plant the WIT contract "
        "`wit/kami-isac.wit` defines). HONEST: the kami-engine submodule is unpopulated here, so this is "
        "the data bridge + interface contract, not a compiled crate; live emission is G8-gated.",
    ]
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover — offline demo
    print(report())
