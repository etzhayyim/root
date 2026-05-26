"""pymagatama.organism.sensors — content / boundary scanners + dataset sensors.

Two distinct kinds of sensor live in this package:

  1. **Scanners** (read-only content gates) — ``charter_rider.scan(...)``
     etc. Return a verdict dict; callers decide what to do.

  2. **Dataset sensors** (per ADR-2605262400) — implementations of the
     ``DatasetSensor`` Protocol that resolve IPFS-pinned subdatasets and
     yield ``SensorObservation`` records into the organism heartbeat
     tick. Sensors are PASSIVE-ONLY — they MUST NOT perform active
     network probes (G8; enforced by
     ``70-tools/scripts/lint/sensor-no-active-probe.mjs``).

Both surfaces are read-only — they never mutate inputs and never write
to PDS. The corpus assembler (cold path) and the organism tick (hot
path) are the persistence boundaries.
"""

from pymagatama.organism.sensors.base import (
    DatasetPin,
    DatasetSensor,
    PiiFilterPolicy,
    SensorObservation,
    StaticPinResolver,
    Tier,
    make_observation,
    now_ms,
)
from pymagatama.organism.sensors.geolite2_sensor import Geolite2Sensor
from pymagatama.organism.sensors.pii_filter import (
    RedactionStats,
    redact_emails,
    redact_payload,
    redact_phones,
    redact_postal,
    redact_text,
    redact_whois_values,
)
from pymagatama.organism.sensors.rir_delegated_sensor import RirDelegatedSensor

__all__ = [
    "DatasetPin",
    "DatasetSensor",
    "Geolite2Sensor",
    "PiiFilterPolicy",
    "RedactionStats",
    "RirDelegatedSensor",
    "SensorObservation",
    "StaticPinResolver",
    "Tier",
    "make_observation",
    "now_ms",
    "redact_emails",
    "redact_payload",
    "redact_phones",
    "redact_postal",
    "redact_text",
    "redact_whois_values",
]
