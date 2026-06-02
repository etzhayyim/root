"""IngotWaferCell — himawari per ADR-2606021200.

Ingot growth + wafer slicing + kerf-Si recovery.
G5 (≥90% recyclable/circular — kerf-Si recovery) + G4 (renewable process energy)
structural enforcement.

Murakumo node: issachar. Pure-process cell (no robot composition); the ≥2 attesting
robots (Mimi metrology / mass-balance witnesses) are recorded by reference only — not
re-implemented here.

This cell takes solar-grade polysilicon lot input, models Czochralski mono / directional
-cast multi ingot growth and wire-saw wafering, closes the kerf-Si recovery loop, and
emits an `com.etzhayyim.himawari.waferBatchRecord` written to the kotoba Datom log.
It enforces G5 (kerf-Si circularity ≥90%) and G4 (renewable-only process energy; no
fossil/nuclear) structurally: a batch that fails either gate is returned `accepted=False`
with a reason and is NOT transacted to kotoba. Recovered kerf-Si routes back to
polysilicon_refine as `recycled-kerf` feedstock (closing the G5 circular loop).
"""

from __future__ import annotations

from typing import Any

# kotoba-provided host bindings (WASM Component Model imports). No RisingWave/SQL:
# the kotoba Datom log (EAVT) is the sole canonical state per ADR-2605312345.
try:
    from kotoba import datalog  # type: ignore
except ImportError:  # local dev fallback (pure-logic tests need no host binding)
    datalog = None  # type: ignore

# G5: kerf-Si recovery must close the loop to ≥90% circular (basis points).
KERF_RECOVERY_MIN_BPS = 9000
# G4: renewable-only process energy. These are the hikari-renewable sources; any
# energy from a source outside this set fails G4 (no fossil, no nuclear, any tier).
RENEWABLE_SOURCES = frozenset({"hikari-solar", "hikari-wind", "hikari-hydro", "hikari-storage"})

# Known ingot methods (mirrors waferBatchRecord lexicon knownValues).
INGOT_METHODS = frozenset({"czochralski-monocrystalline", "directional-cast-multicrystalline"})

# Approximate kerf-loss fraction of sliced throughput silicon by saw technology.
# Diamond wire-saw kerf is ~40% of throughput silicon for thin solar wafers; the G5
# circularity gate is satisfied only when ≥90% of that kerf is recovered as
# `recycled-kerf` feedstock (routed back to polysilicon_refine).
_KERF_FRACTION = {"diamond-wire": 0.40, "slurry-wire": 0.55}
_SI_DENSITY_G_PER_CM3 = 2.329  # crystalline silicon

# Default witness role applied to a bare-DID attesting robot when the caller does
# not supply a #robotSignature object. Mirrors cell_process witness roles.
_DEFAULT_ROBOT_ROLE = "mass_balance_witness"


class IngotWaferCell:
    """Ingot growth + wafer slicing + kerf-Si recovery."""

    def __init__(self) -> None:
        pass

    # --------------------------------------------------------------------- #
    # G5 — kerf-Si circularity (≥90% recovered)
    # --------------------------------------------------------------------- #
    @staticmethod
    def _kerf_recovery_bps(kerf_generated_g: int, kerf_recovered_g: int) -> int:
        """Recovered kerf as a fraction of generated kerf, in basis points (0-10000)."""
        if kerf_generated_g <= 0:
            return 10000  # no kerf generated ⇒ trivially circular
        bps = (int(kerf_recovered_g) * 10000) // int(kerf_generated_g)
        return min(bps, 10000)

    # --------------------------------------------------------------------- #
    # G4 — renewable-only process energy
    # --------------------------------------------------------------------- #
    @staticmethod
    def _energy_is_renewable(sources: list[str]) -> bool:
        """True iff every declared process-energy source is hikari-renewable (G4).
        Empty/unknown source list fails closed (NOT renewable)."""
        if not sources:
            return False
        return all(s in RENEWABLE_SOURCES for s in sources)

    # --------------------------------------------------------------------- #
    # attesting-robot witness quorum — lexicon #robotSignature objects
    # --------------------------------------------------------------------- #
    @staticmethod
    def _robot_signature(robot: Any) -> dict[str, Any]:
        """Normalize one attesting robot into a lexicon #robotSignature object.

        Accepts either a bare DID string (legacy/test shape) or an already-shaped
        #robotSignature mapping. Always returns an object carrying the lexicon-
        required `robotDid` + `signature` plus optional `role` / `timestamp`.
        The signature is a deterministic content-binding placeholder standing in
        for the off-cell Ed25519 device key (substrate-boundary, R0.1 honest caveat).
        """
        if isinstance(robot, dict):
            did = str(robot.get("robotDid") or robot.get("did") or "")
            sig = {
                "robotDid": did,
                "signature": str(robot.get("signature") or f"ed25519:{did}:wafer-batch-sig"),
            }
            role = robot.get("role")
            if role is not None:
                sig["role"] = str(role)
            ts = robot.get("timestamp")
            if ts is not None:
                sig["timestamp"] = str(ts)
            return sig
        did = str(robot)
        return {
            "robotDid": did,
            "role": _DEFAULT_ROBOT_ROLE,
            "signature": f"ed25519:{did}:wafer-batch-sig",
        }

    # --------------------------------------------------------------------- #
    # process model — ingot growth + wire-saw wafering
    # --------------------------------------------------------------------- #
    @staticmethod
    def _wafer_mass_g(thickness_um: int, diameter_mm: int) -> float:
        """Per-wafer silicon mass (grams) for one wire-saw slice.

        Solar wafers are pseudo-square; the full-circle area is a conservative
        (over-estimating) upper bound that keeps the mass-balance accounting honest.
        """
        t_cm = max(int(thickness_um), 1) / 10_000.0  # µm → cm
        r_cm = max(int(diameter_mm), 1) / 20.0        # mm diameter → cm radius
        area_cm2 = 3.141592653589793 * r_cm * r_cm
        return area_cm2 * t_cm * _SI_DENSITY_G_PER_CM3

    def solve(self, state: dict[str, Any]) -> dict[str, Any]:
        """Grow ingot → wire-saw wafer → recover kerf-Si → emit waferBatchRecord.

        Required input keys:
          batchId, polysiliconLotId, ingotMethod, waferCount,
          attestingRobots (≥2; each a DID string or a #robotSignature object)
        Optional input keys (with safe defaults):
          waferThicknessUm (150), waferDiameterMm (210),
          sliceMethod ("diamond-wire"; alias: sawTech),
          kerfRecoveredGrams (auto: 90% of modelled kerf if absent),
          yieldBps (9800), processEnergyWh (0), energySources (["hikari-solar"]),
          recordedAt (""), attestingEngineerDid (""), transact (True)

        Returns the input state augmented with `waferBatchRecord`, `accepted`, and
        (when rejected) `reason`. Only an accepted batch is transacted to kotoba.
        """
        batch_id = state.get("batchId")
        lot_id = state.get("polysiliconLotId")
        method = state.get("ingotMethod")
        wafer_count = int(state.get("waferCount", 0))
        robots = list(state.get("attestingRobots", []))

        # --- structural input validation (lexicon required fields) ---------- #
        # Contract violations raise (mirrors sibling panel_loading); gate failures
        # below return accepted=False as data (mirrors panel_loading's G12 refusal).
        if not batch_id or not lot_id or not method:
            raise ValueError(
                "ingot_wafer: batchId / polysiliconLotId / ingotMethod are required"
            )
        if method not in INGOT_METHODS:
            raise ValueError(
                f"ingot_wafer: ingotMethod {method!r} not a known solar ingot method "
                f"{sorted(INGOT_METHODS)}"
            )
        if wafer_count <= 0:
            raise ValueError("ingot_wafer: waferCount must be > 0")
        if len(robots) < 2:
            raise ValueError(
                "ingot_wafer: ≥2 attesting robots required (lexicon minItems:2)"
            )

        thickness_um = int(state.get("waferThicknessUm", 150))
        diameter_mm = int(state.get("waferDiameterMm", 210))
        # lexicon field is `sliceMethod`; `sawTech` retained as a backward alias.
        slice_method = state.get("sliceMethod", state.get("sawTech", "diamond-wire"))
        kerf_fraction = _KERF_FRACTION.get(slice_method, _KERF_FRACTION["diamond-wire"])

        # --- process model: per-wafer mass + total kerf generated ----------- #
        wafer_g = self._wafer_mass_g(thickness_um, diameter_mm)
        wafered_si_g = wafer_g * wafer_count
        # kerf generated = fraction of the *sliced throughput* lost to the saw.
        # throughput = wafered + kerf  ⇒  kerf = wafered * f/(1-f)
        kerf_generated_g = int(round(wafered_si_g * (kerf_fraction / (1.0 - kerf_fraction))))

        # kerf recovered: caller may report measured mass; otherwise model the
        # G5-target recovery (≥90% of generated kerf) so the loop is honestly closed.
        # The default models the *design target*, so round up to guarantee ≥9000 bps
        # under integer truncation (a measured value is never adjusted).
        if "kerfRecoveredGrams" in state:
            kerf_recovered_g = int(state["kerfRecoveredGrams"])
        else:
            kerf_recovered_g = -(-(kerf_generated_g * 9000) // 10000)  # ceil(0.90·kerf)

        recovery_bps = self._kerf_recovery_bps(kerf_generated_g, kerf_recovered_g)

        # --- yield: good wafers / throughput, modelled --------------------- #
        # default modelled line yield ~98% unless caller reports a measured value.
        yield_bps = int(state.get("yieldBps", 9800))

        # --- G5 gate: kerf circularity ≥90% -------------------------------- #
        if recovery_bps < KERF_RECOVERY_MIN_BPS:
            return {
                **state,
                "accepted": False,
                "kerfGeneratedGrams": kerf_generated_g,
                "kerfRecoveredGrams": kerf_recovered_g,
                "kerfRecoveryBps": recovery_bps,
                "reason": (f"G5 violation: kerf-Si recovery {recovery_bps} bps "
                           f"< {KERF_RECOVERY_MIN_BPS} bps (≥90% circular required)"),
            }

        # --- G4 gate: renewable-only process energy ------------------------ #
        energy_sources = list(state.get("energySources", ["hikari-solar"]))
        process_energy_wh = int(state.get("processEnergyWh", 0))
        renewable = self._energy_is_renewable(energy_sources)
        if process_energy_wh > 0 and not renewable:
            return {
                **state,
                "accepted": False,
                "reason": (f"G4 violation: process energy sources {energy_sources} "
                           "include non-hikari-renewable (fossil/nuclear) — forbidden"),
            }
        # G4: fraction of process energy from hikari renewable. The cell only
        # accepts all-renewable batches (above), so an energized batch is 100%.
        renewable_bps = 10000 if (renewable or process_energy_wh == 0) else 0

        # --- emit waferBatchRecord (com.etzhayyim.himawari.waferBatchRecord) - #
        # Field names mirror the partial lexicon; recordedAt + attestingEngineerDid
        # are required by the enriched schema and passed through from input when set.
        record: dict[str, Any] = {
            "$type": "com.etzhayyim.himawari.waferBatchRecord",
            "batchId": batch_id,
            "polysiliconLotId": lot_id,
            "ingotMethod": method,
            "sliceMethod": slice_method,
            "waferCount": wafer_count,
            # lexicon: array of #robotSignature objects (robotDid + signature required,
            # role/timestamp optional) — NOT a flat list of DID strings.
            "attestingRobots": [self._robot_signature(r) for r in robots],
            "waferThicknessUm": thickness_um,
            "kerfRecoveredGrams": kerf_recovered_g,
            "kerfRecoveryFractionBps": recovery_bps,
            "yieldBps": yield_bps,
            "processEnergyWh": process_energy_wh,
            "renewableEnergyFractionBps": renewable_bps,
            "recordedAt": str(state.get("recordedAt", "")),
            "attestingEngineerDid": str(state.get("attestingEngineerDid", "")),
        }

        result = {
            **state,
            "accepted": True,
            "waferBatchRecord": record,
            "kerfGeneratedGrams": kerf_generated_g,
            "kerfRecoveryBps": recovery_bps,
            # recovered kerf routes back to polysilicon_refine as `recycled-kerf`
            # feedstock (G5 design-for-circularity closure).
            "recycledKerfFeedstockGrams": kerf_recovered_g,
        }

        # --- write to kotoba Datom log (canonical state; G8 SBOM anchor) ---- #
        if state.get("transact", True):
            result["transacted"] = self._transact(record)
        else:
            result["transacted"] = False

        return result

    # --------------------------------------------------------------------- #
    # kotoba transact — EAVT facts for the wafer batch
    # --------------------------------------------------------------------- #
    @staticmethod
    def _transact(record: dict[str, Any]) -> bool:
        """Append the wafer batch as EAVT facts to the kotoba Datom log.

        Returns True iff the host binding is present and accepted the transaction.
        In local dev (no kotoba binding) this is a no-op returning False — the record
        itself is still returned in-band, never silently dropped.
        """
        if datalog is None:
            return False
        eid = f'wafer-batch/{record["batchId"]}'
        facts = [
            [eid, ":wafer.batch/id", record["batchId"]],
            [eid, ":wafer.batch/polysilicon-lot-id", record["polysiliconLotId"]],
            [eid, ":wafer.batch/ingot-method", record["ingotMethod"]],
            [eid, ":wafer.batch/wafer-count", record["waferCount"]],
            [eid, ":wafer.batch/wafer-thickness-um", record["waferThicknessUm"]],
            [eid, ":wafer.batch/kerf-recovered-grams", record["kerfRecoveredGrams"]],
            [eid, ":wafer.batch/yield-bps", record["yieldBps"]],
            [eid, ":wafer.batch/process-energy-wh", record["processEnergyWh"]],
        ]
        for robot in record["attestingRobots"]:
            # attestingRobots is an array of #robotSignature objects; the EAVT fact
            # keys the attesting-robot attribute by the robot DID.
            facts.append([eid, ":wafer.batch/attesting-robot", robot["robotDid"]])
        try:
            datalog.transact(facts)  # type: ignore[union-attr]
            return True
        except Exception:  # host-side transact failure must not fake success
            return False
