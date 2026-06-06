"""noroshi (烽) optical link-budget core — the chip face (ADR-2606051600). Stdlib only.

Computes the end-to-end power budget of a silicon-photonic / co-packaged-optics (CPO) link, the
光電融合 (photonics-electronics convergence) communication primitive: a laser source feeds an
electro-optic modulator on a photonic IC (PIC), light couples off-chip through a grating coupler,
traverses a waveguide / fibre span, and is detected by a photodiode against a receiver sensitivity
set by the target bit-error-rate. The link "closes" when the received power exceeds the sensitivity
with positive margin.

It is a deterministic dB ledger plus an energy-per-bit figure of merit — the number that makes CPO
worth building: by moving the optics into the package and shortening the electrical reach, the same
bit costs far less energy than a front-panel pluggable transceiver. No hardware, no foundry, no live
laser (G7 outward-gated); this is arithmetic over a design, verifiable before any silicon exists.

Sign convention: gains/sources are +dB(m), losses are positive numbers SUBTRACTED. All optical
powers in dBm (0 dBm = 1 mW).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field


@dataclass(frozen=True)
class LinkDesign:
    """One photonic link design. Distances in cm (on-PIC) and m (fibre); losses in dB."""

    name: str = "cpo-2km-100g"
    # ── source ───────────────────────────────────────────────────────────────
    laser_power_dbm: float = 10.0          # CW laser launch into the PIC (10 dBm = 10 mW)
    # ── transmit PIC ─────────────────────────────────────────────────────────
    modulator_il_db: float = 4.0           # electro-optic modulator insertion loss (MZM / micro-ring)
    tx_waveguide_cm: float = 1.5           # on-chip routing length, transmit side
    tx_grating_coupler_db: float = 1.5     # off-chip grating/edge coupler loss, transmit
    # ── span ─────────────────────────────────────────────────────────────────
    fibre_m: float = 2000.0                # fibre / external span length
    fibre_loss_db_per_km: float = 0.35     # SMF @1310nm ~0.35 dB/km
    connector_db: float = 0.5              # connector / splice budget
    # ── receive PIC ──────────────────────────────────────────────────────────
    rx_grating_coupler_db: float = 1.5     # coupler loss, receive
    rx_waveguide_cm: float = 1.0           # on-chip routing length, receive
    # ── shared physical constants ────────────────────────────────────────────
    waveguide_loss_db_per_cm: float = 1.5  # Si rib/strip waveguide propagation loss
    # ── receiver ─────────────────────────────────────────────────────────────
    rx_responsivity_a_per_w: float = 0.9   # photodiode responsivity
    rx_sensitivity_dbm: float = -12.0      # min received power for the target BER (e.g. 1e-12 w/ FEC)
    # ── electrical / throughput ──────────────────────────────────────────────
    line_rate_gbps: float = 106.25         # per-lane line rate (100G + FEC overhead)
    tx_energy_pj_per_bit: float = 1.2      # modulator-driver + serializer energy
    rx_energy_pj_per_bit: float = 1.0      # TIA + deserializer energy
    laser_wall_plug_eff: float = 0.10      # laser electrical→optical efficiency (for energy/bit)


@dataclass(frozen=True)
class LinkBudget:
    name: str
    received_dbm: float
    margin_db: float
    closes: bool
    total_loss_db: float
    energy_pj_per_bit: float
    received_current_ua: float
    breakdown: dict = field(default_factory=dict)


def _waveguide_loss(design: LinkDesign) -> float:
    return (design.tx_waveguide_cm + design.rx_waveguide_cm) * design.waveguide_loss_db_per_cm


def _fibre_loss(design: LinkDesign) -> float:
    return (design.fibre_m / 1000.0) * design.fibre_loss_db_per_km


def compute(design: LinkDesign) -> LinkBudget:
    """Return the closed-form power budget + energy-per-bit for one link design."""
    if design.line_rate_gbps <= 0:
        raise ValueError("line_rate_gbps must be positive")

    losses = {
        "modulator_il": design.modulator_il_db,
        "tx_grating_coupler": design.tx_grating_coupler_db,
        "rx_grating_coupler": design.rx_grating_coupler_db,
        "waveguide": _waveguide_loss(design),
        "fibre": _fibre_loss(design),
        "connector": design.connector_db,
    }
    total_loss = sum(losses.values())
    received_dbm = design.laser_power_dbm - total_loss
    margin = received_dbm - design.rx_sensitivity_dbm

    # Received photocurrent: P[mW] = 10**(dBm/10); I = R * P.
    received_mw = 10.0 ** (received_dbm / 10.0)
    received_current_ua = design.rx_responsivity_a_per_w * received_mw * 1e3  # mW→µA via mA·… (mW*A/W = mA) *1e3=µA

    # Energy per bit: tx + rx electrical + the laser's wall-plug cost amortised over the line rate.
    laser_optical_w = 10.0 ** (design.laser_power_dbm / 10.0) / 1e3            # dBm→W
    laser_electrical_w = laser_optical_w / max(design.laser_wall_plug_eff, 1e-9)
    laser_pj_per_bit = laser_electrical_w / (design.line_rate_gbps * 1e9) * 1e12
    energy_pj_per_bit = design.tx_energy_pj_per_bit + design.rx_energy_pj_per_bit + laser_pj_per_bit

    return LinkBudget(
        name=design.name,
        received_dbm=round(received_dbm, 3),
        margin_db=round(margin, 3),
        closes=margin >= 0.0,
        total_loss_db=round(total_loss, 3),
        energy_pj_per_bit=round(energy_pj_per_bit, 3),
        received_current_ua=round(received_current_ua, 3),
        breakdown={k: round(v, 3) for k, v in losses.items()},
    )


# ── receiver sensitivity from a target BER (Q-factor + thermal-noise model) ──────────────────────
_K_BOLTZMANN = 1.380649e-23   # J/K


def q_factor_for_ber(ber: float) -> float:
    """Solve BER = ½·erfc(Q/√2) for the Q-factor (NRZ-OOK direct detection), via bisection.

    Stdlib erfc only (no erfcinv). Monotone: a stricter BER needs a larger Q (e.g. 1e-9 → ~6.0,
    1e-12 → ~7.03). Defined for 0 < BER < 0.5.
    """
    if not 0.0 < ber < 0.5:
        raise ValueError("BER must lie in (0, 0.5)")
    lo, hi = 0.0, 12.0
    for _ in range(100):                      # ~2^-100 precision; erfc is monotone decreasing in Q
        mid = 0.5 * (lo + hi)
        if 0.5 * math.erfc(mid / math.sqrt(2.0)) > ber:
            lo = mid                          # too much error → need larger Q
        else:
            hi = mid
    return 0.5 * (lo + hi)


def receiver_sensitivity_dbm(
    ber: float, line_rate_gbps: float, responsivity_a_per_w: float = 0.9,
    temperature_k: float = 300.0, load_ohm: float = 50.0,
) -> float:
    """Thermal-noise-limited receiver sensitivity (min received optical power, dBm) for a target BER.

    σ_thermal = √(4·k·T·B / R_load); required current = Q·σ_thermal; P_min = required_current /
    responsivity. B ≈ 0.7·line-rate (NRZ noise bandwidth). A simplified, honest model (thermal-limited,
    NRZ-OOK) — not a measured device-sheet figure (G10).
    """
    if line_rate_gbps <= 0:
        raise ValueError("line_rate_gbps must be positive")
    q = q_factor_for_ber(ber)
    bandwidth_hz = 0.7 * line_rate_gbps * 1e9
    sigma_thermal_a = math.sqrt(4.0 * _K_BOLTZMANN * temperature_k * bandwidth_hz / load_ohm)
    p_min_w = q * sigma_thermal_a / responsivity_a_per_w
    return 10.0 * math.log10(p_min_w * 1e3)   # W → dBm


def with_ber_sensitivity(design: LinkDesign, ber: float) -> LinkDesign:
    """Return a copy of `design` whose rx_sensitivity_dbm is derived from a target BER (not assumed)."""
    from dataclasses import replace
    sens = receiver_sensitivity_dbm(ber, design.line_rate_gbps, design.rx_responsivity_a_per_w)
    return replace(design, rx_sensitivity_dbm=round(sens, 3))


# ── APD (avalanche photodiode) receiver: avalanche gain vs excess noise ──────────────────────────
def excess_noise_factor(gain_m: float, k_eff: float = 0.3) -> float:
    """McIntyre excess-noise factor F(M) = k·M + (1−k)·(2 − 1/M). F(1)=1; grows with M and with k_eff."""
    if gain_m < 1:
        raise ValueError("APD gain M must be ≥ 1")
    if not 0.0 <= k_eff <= 1.0:
        raise ValueError("k_eff (ionization ratio) must lie in [0,1]")
    return k_eff * gain_m + (1.0 - k_eff) * (2.0 - 1.0 / gain_m)


def apd_sensitivity_dbm(
    ber: float, line_rate_gbps: float, gain_m: float = 10.0, k_eff: float = 0.3,
    responsivity_a_per_w: float = 0.9, temperature_k: float = 300.0, load_ohm: float = 50.0,
) -> float:
    """APD receiver sensitivity (dBm) — the PIN thermal-limited value improved by M/√F(M).

    An APD multiplies the photocurrent by gain M (so the signal rises above the thermal floor) at the
    cost of an excess-noise factor F(M); the net SNR improvement over a PIN in the thermal-limited
    regime is M/√F(M), giving a more-negative (more sensitive) figure. HONEST (G10/N4): this is the
    thermal-limited bound only — the real optimal M is set by the thermal/APD-shot-noise balance, which
    eventually caps the benefit and is not modelled here.
    """
    pin = receiver_sensitivity_dbm(ber, line_rate_gbps, responsivity_a_per_w, temperature_k, load_ohm)
    improvement_db = 10.0 * math.log10(gain_m / math.sqrt(excess_noise_factor(gain_m, k_eff)))
    return pin - improvement_db


# ── reference designs: CPO (co-packaged, short reach) vs front-panel pluggable ───────────────────
CPO_REFERENCE = LinkDesign(
    name="cpo-2km-100g",
    laser_power_dbm=10.0, modulator_il_db=4.0,
    tx_grating_coupler_db=1.5, rx_grating_coupler_db=1.5,
    tx_waveguide_cm=1.5, rx_waveguide_cm=1.0,
    fibre_m=2000.0, tx_energy_pj_per_bit=1.2, rx_energy_pj_per_bit=1.0,
)

PLUGGABLE_REFERENCE = LinkDesign(
    name="pluggable-2km-100g",
    laser_power_dbm=10.0, modulator_il_db=5.0,
    tx_grating_coupler_db=2.0, rx_grating_coupler_db=2.0,
    tx_waveguide_cm=2.0, rx_waveguide_cm=2.0,
    fibre_m=2000.0,
    # Pluggable pays a much larger SerDes/retimer budget driving the front-panel electrical reach.
    tx_energy_pj_per_bit=6.0, rx_energy_pj_per_bit=5.5,
)


def report(designs: list[LinkDesign] | None = None) -> str:
    """Render a human-readable link-budget comparison (the chip-face out/ artifact)."""
    designs = designs or [CPO_REFERENCE, PLUGGABLE_REFERENCE]
    budgets = [compute(d) for d in designs]
    lines = ["# noroshi 烽 — optical link budget (光電融合 / CPO)", ""]
    for b in budgets:
        verdict = "CLOSES" if b.closes else "FAILS (insufficient margin)"
        lines += [
            f"## {b.name}",
            f"- received power : {b.received_dbm} dBm  (total loss {b.total_loss_db} dB)",
            f"- link margin    : {b.margin_db} dB  → {verdict}",
            f"- photocurrent   : {b.received_current_ua} µA",
            f"- energy/bit     : {b.energy_pj_per_bit} pJ/bit",
            f"- loss breakdown : {b.breakdown}",
            "",
        ]
    if len(budgets) >= 2 and budgets[1].energy_pj_per_bit > 0:
        ratio = budgets[1].energy_pj_per_bit / budgets[0].energy_pj_per_bit
        lines.append(
            f"**CPO energy advantage**: {budgets[0].name} costs "
            f"{budgets[0].energy_pj_per_bit} pJ/bit vs {budgets[1].name} "
            f"{budgets[1].energy_pj_per_bit} pJ/bit — **{ratio:.2f}× lower energy/bit**."
        )
    lines.append("")
    lines.append("> R0 design arithmetic only. No foundry tapeout, no measured device, no live "
                 "laser (G7 outward-gated). `:representative` device parameters.")
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover — offline demo
    print(report())
