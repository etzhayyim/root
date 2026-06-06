"""noroshi (烽) ISAC simulator — the sensing-communication-fusion face (ADR-2606051600). Stdlib only.

ISAC = Integrated Sensing And Communication (a.k.a. JCAS, joint communication-and-sensing): one
waveform that simultaneously carries data AND illuminates the environment, so the same photonic /
RF front-end that runs the link also senses range + radial velocity. The 烽火台 (beacon-watchtower)
metaphor: the fire both CARRIES a coded message (communication) and is SEEN at a distance
(sensing) — one emission, two functions.

This implements the OFDM-radar reciprocal-processing model (Sturm & Wiesbeck): the transmitter
knows its own data symbols X[n,m], so it divides them out of the echo to get a pure
delay-Doppler grid and recovers a target by a 2-D periodogram. It also gives the
communication-vs-sensing power-split tradeoff that makes JCAS a DESIGN choice, not a free lunch.

CIVILIAN sensing only (collision-avoidance / presence / range-rate). The target is an OBJECT with a
range and a velocity — never a person, never a pattern-of-life (watari G4). Fire-control / weapon-cue
sensing is structurally absent (N1). Deterministic + offline: no hardware, no live emission (G7).

Conventions: SI units. c = speed of light. Range R[m], radial velocity v[m/s] (closing > 0).
"""

from __future__ import annotations

import cmath
import math
from dataclasses import dataclass

C_LIGHT = 299_792_458.0
TWO_PI = 2.0 * math.pi


@dataclass(frozen=True)
class IsacWaveform:
    """An OFDM-JCAS frame: n_sub subcarriers × n_sym symbols at carrier f_c."""

    n_sub: int = 64           # subcarriers  → range processing dimension
    n_sym: int = 16           # OFDM symbols → Doppler processing dimension
    subcarrier_hz: float = 1.0e6   # Δf = 1 MHz  → bandwidth B = n_sub·Δf = 64 MHz
    symbol_s: float = 1.2e-6       # OFDM symbol duration incl. cyclic prefix
    carrier_hz: float = 28.0e9     # f_c (mmWave; sets velocity↔Doppler scale)

    @property
    def bandwidth_hz(self) -> float:
        return self.n_sub * self.subcarrier_hz

    @property
    def wavelength_m(self) -> float:
        return C_LIGHT / self.carrier_hz

    @property
    def range_resolution_m(self) -> float:
        """ΔR = c / (2·B)."""
        return C_LIGHT / (2.0 * self.bandwidth_hz)

    @property
    def velocity_resolution_mps(self) -> float:
        """Δv = λ / (2·M·T)."""
        return self.wavelength_m / (2.0 * self.n_sym * self.symbol_s)

    @property
    def max_unambiguous_range_m(self) -> float:
        """R_max = c / (2·Δf)."""
        return C_LIGHT / (2.0 * self.subcarrier_hz)


@dataclass(frozen=True)
class Target:
    range_m: float
    velocity_mps: float
    rcs: float = 1.0          # reflectivity α² (linear); civilian object, never a person


@dataclass(frozen=True)
class SenseEstimate:
    range_m: float
    velocity_mps: float
    range_bin: int
    doppler_bin: int
    peak_magnitude: float


def _qpsk_symbol(n: int, m: int) -> complex:
    """Deterministic unit-magnitude QPSK data symbol (no RNG → reproducible tests)."""
    quadrant = (n * 3 + m * 5) % 4
    return cmath.exp(1j * (math.pi / 4 + quadrant * math.pi / 2))


def _validate_waveform(wf: IsacWaveform) -> None:
    """Reject a degenerate waveform before it silently misbehaves (div-by-zero / empty grid)."""
    if wf.n_sub < 1 or wf.n_sym < 1:
        raise ValueError("waveform needs at least 1 subcarrier and 1 symbol")
    if wf.subcarrier_hz <= 0 or wf.symbol_s <= 0 or wf.carrier_hz <= 0:
        raise ValueError("subcarrier spacing, symbol duration, and carrier must be positive")


def _echo_grid(wf: IsacWaveform, target: Target) -> list[list[complex]]:
    """Reciprocal delay-Doppler grid D[n,m] = echo / data = α·e^{-j2π nΔf τ}·e^{+j2π mT f_d}."""
    tau = 2.0 * target.range_m / C_LIGHT                     # round-trip delay
    f_d = 2.0 * target.velocity_mps / wf.wavelength_m        # Doppler shift
    alpha = math.sqrt(max(target.rcs, 0.0))
    grid: list[list[complex]] = []
    for n in range(wf.n_sub):
        row: list[complex] = []
        for m in range(wf.n_sym):
            x = _qpsk_symbol(n, m)
            echo = x * alpha * cmath.exp(-1j * TWO_PI * n * wf.subcarrier_hz * tau) \
                             * cmath.exp(1j * TWO_PI * m * wf.symbol_s * f_d)
            row.append(echo / x)                            # divide out the known data
        grid.append(row)
    return grid


def _periodogram(wf: IsacWaveform, grid: list[list[complex]]) -> list[list[float]]:
    """2-D range-Doppler periodogram magnitude P[k,l] over the reciprocal grid (range +j, Doppler -j)."""
    mags = [[0.0] * wf.n_sym for _ in range(wf.n_sub)]
    for k in range(wf.n_sub):
        for l in range(wf.n_sym):
            acc = 0j
            for n in range(wf.n_sub):
                rk = cmath.exp(1j * TWO_PI * n * k / wf.n_sub)
                for m in range(wf.n_sym):
                    acc += grid[n][m] * rk * cmath.exp(-1j * TWO_PI * m * l / wf.n_sym)
            mags[k][l] = abs(acc)
    return mags


def _bin_to_estimate(wf: IsacWaveform, k: int, l: int, mag: float) -> SenseEstimate:
    tau = k / (wf.n_sub * wf.subcarrier_hz)
    f_d = l / (wf.n_sym * wf.symbol_s)
    return SenseEstimate(
        range_m=C_LIGHT * tau / 2.0, velocity_mps=wf.wavelength_m * f_d / 2.0,
        range_bin=k, doppler_bin=l, peak_magnitude=mag,
    )


def estimate_target(wf: IsacWaveform, target: Target) -> SenseEstimate:
    """Recover (range, velocity) from one target via the 2-D OFDM-radar periodogram.

    Range transform is +j over subcarriers, Doppler is -j over symbols, so the peak bin (k,l) maps
    to τ = k/(N·Δf) and f_d = l/(M·T). Aliased beyond R_max / the Doppler interval (honest N4).
    """
    _validate_waveform(wf)
    mags = _periodogram(wf, _echo_grid(wf, target))
    k, l = max(((k, l) for k in range(wf.n_sub) for l in range(wf.n_sym)),
               key=lambda kl: mags[kl[0]][kl[1]])
    return _bin_to_estimate(wf, k, l, mags[k][l])


def estimate_targets(
    wf: IsacWaveform, targets: list[Target], top_n: int | None = None, guard: int = 1
) -> list[SenseEstimate]:
    """Multi-target sensing: ONE combined echo → CLEAN top-N peak extraction (matures N4).

    The reciprocal grid is linear in the targets, so their grids sum; a single periodogram then yields
    every target. CLEAN extraction picks the global peak, suppresses a ±`guard` neighbourhood (so one
    target is not detected twice), and repeats `top_n` times (default: one per target). Well-separated
    targets are each recovered on their own bin; closer than the resolution cell they merge (honest).
    """
    _validate_waveform(wf)
    if not targets:
        return []
    top_n = len(targets) if top_n is None else top_n
    mags = _periodogram(wf, _combined_grid(wf, targets))
    return _extract_peaks(wf, mags, top_n=top_n, guard=guard)


def _combined_grid(wf: IsacWaveform, targets: list[Target]) -> list[list[complex]]:
    """Sum the per-target reciprocal grids (the grid is linear in the targets)."""
    grids = [_echo_grid(wf, t) for t in targets]
    return [[sum(g[n][m] for g in grids) for m in range(wf.n_sym)] for n in range(wf.n_sub)]


def _extract_peaks(wf, mags, top_n=None, guard=1, threshold=None):
    """CLEAN peak extraction: pick the global max, suppress a ±guard cell, repeat.

    Stops after `top_n` picks (if set) and/or once the remaining max falls below `threshold` (if set).
    """
    work = [row[:] for row in mags]
    picks: list[SenseEstimate] = []
    cap = wf.n_sub * wf.n_sym if top_n is None else min(top_n, wf.n_sub * wf.n_sym)
    for _ in range(cap):
        k, l = max(((k, l) for k in range(wf.n_sub) for l in range(wf.n_sym)),
                   key=lambda kl: work[kl[0]][kl[1]])
        if threshold is not None and mags[k][l] < threshold:
            break
        picks.append(_bin_to_estimate(wf, k, l, mags[k][l]))
        for dk in range(-guard, guard + 1):                 # suppress a guard cell (toroidal)
            for dl in range(-guard, guard + 1):
                work[(k + dk) % wf.n_sub][(l + dl) % wf.n_sym] = -1.0
    return picks


def _add_noise(wf: IsacWaveform, grid: list[list[complex]], sigma: float, seed: int):
    """Add deterministic complex-Gaussian noise (seeded → reproducible). σ per real/imag component."""
    import random
    rng = random.Random(seed)
    return [[grid[n][m] + complex(rng.gauss(0.0, sigma), rng.gauss(0.0, sigma))
             for m in range(wf.n_sym)] for n in range(wf.n_sub)]


def detect_cfar(
    wf: IsacWaveform, targets: list[Target], noise_sigma: float = 0.0,
    threshold_factor: float = 4.0, seed: int = 0, guard: int = 1,
) -> list[SenseEstimate]:
    """Detect targets in noise with a constant-false-alarm threshold (simplified CA-CFAR).

    Adds seeded complex-Gaussian noise to the combined echo, forms the periodogram, estimates the noise
    floor as the MEAN magnitude (cell-averaging CFAR), and declares detections only where a CLEAN peak
    exceeds `threshold_factor × mean`. Deterministic for a given seed. Honest (N4): a simplified GLOBAL
    CA-CFAR (one floor for the whole map), not a per-cell sliding-window CA-CFAR.
    """
    _validate_waveform(wf)
    if noise_sigma < 0:
        raise ValueError("noise_sigma must be ≥ 0")
    if threshold_factor <= 0:
        raise ValueError("threshold_factor must be positive")
    if not targets and noise_sigma == 0:
        return []                                    # nothing present and no noise → no detections
    grid = _combined_grid(wf, targets) if targets else [[0j] * wf.n_sym for _ in range(wf.n_sub)]
    if noise_sigma > 0:
        grid = _add_noise(wf, grid, noise_sigma, seed)
    mags = _periodogram(wf, grid)
    n_cells = wf.n_sub * wf.n_sym
    mean_floor = sum(v for row in mags for v in row) / n_cells
    threshold = threshold_factor * mean_floor
    return _extract_peaks(wf, mags, top_n=None, guard=guard, threshold=threshold)


def detection_probability(
    wf: IsacWaveform, target: Target, noise_sigma: float,
    threshold_factor: float = 4.0, trials: int = 16,
) -> float:
    """Monte-Carlo Pd: fraction of `trials` seeds in which CFAR detects the target's true bin.

    Deterministic — the seeds are 0..trials-1, so the estimate is reproducible. The "true" bin is the
    noiseless periodogram peak for this target.
    """
    if trials < 1:
        raise ValueError("trials must be ≥ 1")
    truth = estimate_target(wf, target)
    true_bin = (truth.range_bin, truth.doppler_bin)
    hits = 0
    for seed in range(trials):
        dets = detect_cfar(wf, [target], noise_sigma, threshold_factor, seed)
        if true_bin in {(d.range_bin, d.doppler_bin) for d in dets}:
            hits += 1
    return hits / trials


def pd_vs_snr(
    wf: IsacWaveform, target: Target, sigmas: list[float],
    threshold_factor: float = 4.0, trials: int = 16,
) -> list[tuple[float, float]]:
    """Sweep the noise level → [(σ, Pd)] — the detector's operating curve (higher σ ⇒ lower Pd)."""
    return [(s, detection_probability(wf, target, s, threshold_factor, trials)) for s in sigmas]


# ── communication ↔ sensing power-split (the JCAS tradeoff) ──────────────────────────────────────
@dataclass(frozen=True)
class JcasOperatingPoint:
    power_split: float          # ρ ∈ [0,1]: fraction of power to COMMUNICATION
    capacity_gbps: float        # Shannon capacity of the comms half
    range_std_m: float          # CRLB std of the range estimate (sensing half)
    velocity_std_mps: float     # CRLB std of the velocity estimate


def jcas_operating_point(
    wf: IsacWaveform,
    power_split: float,
    tx_power_w: float = 1.0,
    channel_gain_db: float = -90.0,
    noise_psd_dbm_hz: float = -174.0,
) -> JcasOperatingPoint:
    """One point on the JCAS tradeoff: split total power ρ:(1-ρ) between comms and sensing.

    Comms half → Shannon capacity over the band. Sensing half → coherent integration gain N·M, then
    the range/velocity CRLB scales as resolution / sqrt(2·SNR). Raising ρ buys data rate at the cost
    of sensing precision and vice-versa — the design knob ISAC exists to expose.
    """
    if not 0.0 <= power_split <= 1.0:
        raise ValueError("power_split ρ must lie in [0,1]")
    _validate_waveform(wf)

    b = wf.bandwidth_hz
    noise_w = 10 ** ((noise_psd_dbm_hz - 30) / 10) * b      # N0·B in watts
    gain = 10 ** (channel_gain_db / 10)

    # Communication: flat-channel Shannon over the whole band, fed ρ of the power.
    snr_comm = max(power_split, 1e-12) * tx_power_w * gain / noise_w
    capacity_bps = b * math.log2(1.0 + snr_comm)

    # Sensing: (1-ρ) of the power, with the full N·M coherent processing gain.
    n_mn = wf.n_sub * wf.n_sym
    snr_sense = max(1.0 - power_split, 1e-12) * tx_power_w * gain / noise_w * n_mn
    crlb_scale = 1.0 / math.sqrt(2.0 * max(snr_sense, 1e-12))
    return JcasOperatingPoint(
        power_split=power_split,
        capacity_gbps=capacity_bps / 1e9,
        range_std_m=wf.range_resolution_m * crlb_scale,
        velocity_std_mps=wf.velocity_resolution_mps * crlb_scale,
    )


def report(wf: IsacWaveform | None = None) -> str:
    """Render the ISAC face out/ artifact: a recovered target + the JCAS tradeoff sweep."""
    wf = wf or IsacWaveform()
    # A target placed on exact bins so the recovery is auditable.
    tgt = Target(range_m=4 * wf.range_resolution_m, velocity_mps=3 * wf.velocity_resolution_mps)
    est = estimate_target(wf, tgt)
    lines = [
        "# noroshi 烽 — ISAC (JCAS) sensing + communication",
        "",
        "## waveform",
        f"- bandwidth        : {wf.bandwidth_hz/1e6:.1f} MHz  ({wf.n_sub} subcarriers × {wf.subcarrier_hz/1e3:.0f} kHz)",
        f"- range resolution : {wf.range_resolution_m:.3f} m   (R_max {wf.max_unambiguous_range_m/1e3:.2f} km)",
        f"- velocity res.    : {wf.velocity_resolution_mps:.3f} m/s",
        "",
        "## sensing recovery (civilian object — never a person, N1/G4)",
        f"- true   : R = {tgt.range_m:.3f} m, v = {tgt.velocity_mps:.3f} m/s",
        f"- est.   : R = {est.range_m:.3f} m, v = {est.velocity_mps:.3f} m/s  (bins k={est.range_bin}, l={est.doppler_bin})",
        "",
        "## JCAS power-split tradeoff (ρ = fraction to COMMS)",
        "| ρ | capacity (Gb/s) | range σ (m) | velocity σ (m/s) |",
        "|---|---|---|---|",
    ]
    for rho in (0.1, 0.3, 0.5, 0.7, 0.9):
        op = jcas_operating_point(wf, rho)
        lines.append(f"| {rho:.1f} | {op.capacity_gbps:.3f} | {op.range_std_m:.4f} | {op.velocity_std_mps:.4f} |")

    # CFAR detector operating curve (small waveform for a fast, deterministic sweep).
    swf = IsacWaveform(n_sub=16, n_sym=8)
    stgt = Target(range_m=4 * swf.range_resolution_m, velocity_mps=2 * swf.velocity_resolution_mps)
    lines += [
        "",
        "## CA-CFAR detection probability vs noise (Pd, seeded Monte-Carlo)",
        "| noise σ | Pd |",
        "|---|---|",
    ]
    for sigma, pd in pd_vs_snr(swf, stgt, sigmas=[0.0, 1.0, 2.0, 4.0, 8.0], trials=8):
        lines.append(f"| {sigma:.1f} | {pd:.2f} |")
    lines += [
        "",
        "> One waveform, two functions: more comms power ⇒ higher data rate but coarser sensing; "
        "Pd degrades as noise rises (constant-false-alarm threshold).",
        "> R0 simulation only — no live emission, no hardware (G7). Sensing is civilian "
        "collision-avoidance/presence; fire-control / targeting is structurally absent (N1).",
    ]
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover — offline demo
    print(report())
