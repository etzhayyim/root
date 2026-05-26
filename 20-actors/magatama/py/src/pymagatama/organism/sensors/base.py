"""DatasetSensor Protocol — read-only IPFS-CID-resolved view of a subdataset.

Per ADR-2605262400 §3. A DatasetSensor lets a `pymagatama.organism`
heartbeat tick consume a bounded sample from a public-domain corpus
without breaking the substrate boundary:

  - bytes are resolved via `app.etzhayyim.substrate.datasetPin` AT records
    (ADR-2605241500) + IPFS CID map; no separate projection layer;
  - the sensor runs in-memory only — it does NOT write back into the
    DataLad annex; the cold-path corpus assembler is the persistence
    boundary;
  - tier="C" observations carry `internal_only=True` and MUST be dropped
    by `PostSink` on external paths (G4 + R9 backstop);
  - sensor implementations MUST NOT perform active network probes
    against third-party hosts (G8; enforced by
    `70-tools/scripts/lint/sensor-no-active-probe.mjs`).
"""

from __future__ import annotations

import enum
import time
from dataclasses import dataclass, field
from typing import Any, Iterator, Literal, Protocol, runtime_checkable

Tier = Literal["A", "B", "C", "D"]


class PiiFilterPolicy(enum.Enum):
    """How aggressively the sensor redacts PII before yielding observations.

    `STRICT` (default) over-redacts; `BALANCED` runs the full Wave-1
    rule set without speculative pattern broadening; `OFF` is reserved
    for in-tree unit tests with synthetic fixtures only — production
    sensors MUST NOT use OFF.
    """

    STRICT = "strict"
    BALANCED = "balanced"
    OFF = "off"


@dataclass(frozen=True)
class DatasetPin:
    """A receipt for one IPFS-pinned subdataset version.

    Resolved from an `app.etzhayyim.substrate.datasetPin` AT record. The
    sensor consumes `cid_map` (a sha256e-key → IPFS CID mapping) to
    fetch individual annex objects on demand via Kubo HTTP API.
    """

    name: str
    revision: str
    cid_map_cid: str
    license: str
    tier: Tier
    created_at: str
    assigned_nodes: tuple[str, ...] = ()
    at_uri: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SensorObservation:
    """One yielded data point from a sensor.

    Distinct from `pymagatama.organism.kaizen.Observation` (that one is
    an observer-tick aggregate of shard healthz). This is a per-record
    observation from a public-data sensor.
    """

    sensor: str
    tier: Tier
    pin_revision: str
    payload: dict[str, Any]
    captured_at_ms: int = 0
    internal_only: bool = False

    def with_internal_only(self, flag: bool) -> "SensorObservation":
        return SensorObservation(
            sensor=self.sensor,
            tier=self.tier,
            pin_revision=self.pin_revision,
            payload=self.payload,
            captured_at_ms=self.captured_at_ms,
            internal_only=flag,
        )


@runtime_checkable
class DatasetSensor(Protocol):
    """Read-only IPFS-resolved view of a subdataset.

    Implementations MUST be deterministic on `hot_sample(pin, n)` given
    a fixed `pin.revision` (G9 in ADR-2605262400). Implementations MUST
    NOT touch any network resource other than the religious-corp DID
    infrastructure and the local Kubo HTTP API (G8).
    """

    name: str
    license: str
    tier: Tier
    refresh_cadence_sec: int
    pii_filter: PiiFilterPolicy

    def latest_pin(self) -> DatasetPin: ...

    def stream(self, pin: DatasetPin) -> Iterator[SensorObservation]: ...

    def hot_sample(self, pin: DatasetPin, n: int) -> list[SensorObservation]: ...


@dataclass
class StaticPinResolver:
    """A minimal pin resolver suitable for tests + W1 single-machine use.

    Wave-1 sensors use this; W3 will replace it with an
    `at://did:web:dataset-pinner.etzhayyim.com/...` resolver that hits
    the religious-corp PDS and verifies the DID-signed datasetPin
    record.
    """

    pins: dict[str, DatasetPin] = field(default_factory=dict)

    def latest(self, name: str) -> DatasetPin:
        if name not in self.pins:
            raise LookupError(f"no pin registered for subdataset '{name}'")
        return self.pins[name]


def now_ms() -> int:
    return int(time.time() * 1000)


def make_observation(
    *,
    sensor: str,
    tier: Tier,
    pin: DatasetPin,
    payload: dict[str, Any],
) -> SensorObservation:
    """Helper that fills `internal_only=True` when tier == 'C'.

    Sensors should ALWAYS use this helper rather than constructing
    SensorObservation directly — that way G4 is enforced at the
    construction site and a sensor cannot accidentally emit a tier-C
    observation as externally-shareable.
    """
    return SensorObservation(
        sensor=sensor,
        tier=tier,
        pin_revision=pin.revision,
        payload=payload,
        captured_at_ms=now_ms(),
        internal_only=(tier == "C"),
    )


__all__ = [
    "DatasetPin",
    "DatasetSensor",
    "PiiFilterPolicy",
    "SensorObservation",
    "StaticPinResolver",
    "Tier",
    "make_observation",
    "now_ms",
]
