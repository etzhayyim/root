"""kotoba-os scan-cycle reference model (ADR-2606031600 §D3).

Executable semantics for the central claim of the WIT contract
(`00-contracts/wit/kotoba-os/kotoba-os.wit`): **a PLC scan cycle is a Datom
transaction**, so the entire control history is an immutable, content-addressed,
replayable log (Datomic preserved — ADR-2605312345; machine state IS the Datom
log). This is a stdlib-only reference (no kotoba subrepo dependency); it models
the *semantics* the host (L2 kernel) + guest (L5 control program) must honor, so
the invariants can be regression-tested before the real Rust host exists.

Invariants encoded here (each maps to a Non-goal / Decision in the ADR):

* N7  — the ONLY durable state path is the Datom log; no bypass-the-log store.
* N3  — `write_*` are STAGED (deferred), never applied mid-cycle; a faulted
        cycle commits atomically-all or atomically-nothing.
* N2  — soft-RT only: we record `duration_us` per cycle for jitter analysis,
        we do NOT claim hard-RT / SIL.
* D3  — read inputs -> compute -> stage outputs -> assert facts -> COMMIT, with
        T = monotonic cycle index; `as_of(T)` reconstructs machine state.

A "Datom" here is the immutable 5-tuple (E, A, V, T, added) of ADR-2605312345.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class Datom:
    """Immutable 5-tuple (E, A, V, T, added). Content addressing (CIDv1 blake3)
    is the real substrate's job; here identity is structural equality."""
    e: str          # entity
    a: str          # attribute
    v: object       # value
    t: int          # transaction time = scan cycle index
    added: bool = True


class FaultedCycle(Exception):
    """Raised by a control program to abort a cycle. Nothing staged this cycle
    is committed (N3 atomicity)."""


class ScanHost:
    """The L2 host: owns the device buses (simulated), the Datom log, and drives
    the read -> compute -> stage -> commit scan cycle. The guest never writes the
    log or a bus directly; it only stages through the host (capability-scoped)."""

    def __init__(self) -> None:
        # Simulated field buses. In the real host these are modbus/opcua/gpio/...
        self._inputs: dict[int, object] = {}
        self._outputs: dict[int, object] = {}      # applied (committed) bus state
        # The canonical, append-only Datom log. THE source of truth (N7).
        self.log: list[Datom] = []
        # Per-cycle staging buffers — discarded on fault, flushed on commit (N3).
        self._staged_outputs: dict[int, object] = {}
        self._staged_facts: list[tuple[str, str, object]] = []
        self._cycle = 0

    # ----- device surface offered to the guest (a subset = its capabilities) ---
    def set_input(self, ch: int, value: object) -> None:
        """Test/sim harness sets a field input (host side)."""
        self._inputs[ch] = value

    def read_input(self, ch: int) -> object:
        if ch not in self._inputs:
            raise KeyError(f"channel {ch} not in granted/known input set")
        return self._inputs[ch]

    def write_output(self, ch: int, value: object) -> None:
        """STAGE an output (N3): not applied to the bus until commit."""
        self._staged_outputs[ch] = value

    def assert_fact(self, e: str, a: str, v: object) -> None:
        """Buffer a Datom assertion for this cycle's transaction (N7)."""
        self._staged_facts.append((e, a, v))

    def applied_output(self, ch: int) -> object:
        """Committed bus state — what the field device actually sees."""
        return self._outputs.get(ch)

    # ----- the scan cycle ------------------------------------------------------
    def run_cycle(self, control: Callable[["ScanHost", int], None],
                  duration_us: int = 0) -> dict:
        """Run one scan cycle. `control` is the L5 guest's `scan(cycle)`.

        read -> compute(guest stages outputs + facts) -> COMMIT atomically.
        Returns the scan-report dict mirroring the WIT `scan-report` record.
        """
        t = self._cycle
        self._staged_outputs = {}
        self._staged_facts = []
        n_inputs_before = len(self._inputs)
        try:
            control(self, t)
        except FaultedCycle:
            # N3: abort — nothing staged is committed; outputs untouched; log clean.
            self._staged_outputs = {}
            self._staged_facts = []
            self._cycle += 1
            return {"cycle": t, "inputs_read": n_inputs_before,
                    "outputs_staged": 0, "facts_asserted": 0,
                    "duration_us": duration_us, "faulted": True}

        # --- atomic commit (D3): staged outputs + facts become one Datom txn ---
        for ch, value in self._staged_outputs.items():
            self._outputs[ch] = value
            self.log.append(Datom(e=f"out:{ch}", a=":io/output", v=value, t=t))
        for (e, a, v) in self._staged_facts:
            self.log.append(Datom(e=e, a=a, v=v, t=t))
        # Cycle audit fact (mirrors scan-report; supports N2 jitter analysis).
        self.log.append(Datom(e="machine", a=":scan/duration-us",
                              v=duration_us, t=t))

        report = {"cycle": t, "inputs_read": n_inputs_before,
                  "outputs_staged": len(self._staged_outputs),
                  "facts_asserted": len(self._staged_facts),
                  "duration_us": duration_us, "faulted": False}
        self._cycle += 1
        return report

    # ----- Datomic as-of / replay ---------------------------------------------
    def as_of(self, t: int) -> dict[str, object]:
        """Reconstruct machine state (latest value per (E,A)) as of cycle <= t.
        This is the Datomic `as-of` over the immutable log — the replay claim."""
        state: dict[tuple[str, str], object] = {}
        for d in self.log:
            if d.t <= t and d.added:
                state[(d.e, d.a)] = d.v
        return {f"{e}|{a}": v for (e, a), v in state.items()}

    def replay_outputs(self, t: int) -> dict[int, object]:
        """Reconstruct applied outputs as of cycle t purely from the Datom log,
        proving the bus state is a projection of the log (N7)."""
        out: dict[int, object] = {}
        for d in self.log:
            if d.t <= t and d.a == ":io/output" and d.added:
                ch = int(d.e.split(":", 1)[1])
                out[ch] = d.v
        return out
