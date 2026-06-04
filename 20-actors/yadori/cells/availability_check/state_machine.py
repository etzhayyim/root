"""Phase state machine for the yadori availability_check (宿り) cell.

normalize → resolve-rdap → classify → availability-recorded. The transitions wrap the real RDAP
classifier in methods/availability.py and are pure + unit-tested. The cell's .solve() raises until
Council activation.

Gates enforced here:
  G1 — read-only: only RDAP `domain` lookups; never zone enumeration / AXFR.
  G7 — outward-gated: the LIVE RDAP fetch is reachable only when BOTH an operator attestation is
       present in the state (`operator_gate=True`) AND the process env flag YADORI_ALLOW_LIVE_RDAP=1
       is set. With either missing, the cell stays offline (fixtures or :unknown) and never opens a
       socket. Default is offline.
  G8 — sourcing-honesty: offline results are marked representative; with no fixture and live not
       allowed, the verdict is :unknown (never a guessed :available).
"""

from __future__ import annotations

import importlib.util
import os
import pathlib
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# Load methods/availability.py (sibling top-level module) without a package import.
# Register in sys.modules before exec so its @dataclass annotations resolve (PEP 563 / py3.14).
_AVAIL_PATH = pathlib.Path(__file__).resolve().parents[2] / "methods" / "availability.py"
_spec = importlib.util.spec_from_file_location("yadori_availability", _AVAIL_PATH)
availability = importlib.util.module_from_spec(_spec)
sys.modules["yadori_availability"] = availability
_spec.loader.exec_module(availability)  # type: ignore[union-attr]

LIVE_ENV_FLAG = "YADORI_ALLOW_LIVE_RDAP"


class AvailabilityPhase(Enum):
    INIT = "init"
    NORMALIZED = "normalized"
    RDAP_RESOLVED = "rdap_resolved"
    CLASSIFIED = "classified"
    AVAILABILITY_RECORDED = "availability_recorded"


@dataclass
class AvailabilityCheckState:
    phase: str = AvailabilityPhase.INIT.value
    fqdn: str = "example.com"
    ascii_fqdn: str = ""
    tld: str = ""
    invalid: bool = False
    rdap_url: str = ""
    live_allowed: bool = False     # G7: resolved from operator_gate AND env flag
    status: str = ""
    source: str = "none"
    representative: bool = True
    payload: dict = field(default_factory=dict)


def _state(d: dict[str, Any]) -> AvailabilityCheckState:
    return AvailabilityCheckState(**d.get("cell_state", {}))


def live_rdap_allowed(state: dict[str, Any]) -> bool:
    """G7 gate: an operator attestation in-state AND the process env flag must BOTH be present."""
    operator_attested = bool(state.get("operator_gate"))
    env_enabled = os.environ.get(LIVE_ENV_FLAG) == "1"
    return operator_attested and env_enabled


def transition_to_normalized(state: dict[str, Any]) -> dict[str, Any]:
    """G1: normalize (IDNA/punycode). Invalid names are flagged, not raised."""
    cs = _state(state)
    cs.fqdn = state.get("fqdn", cs.fqdn)
    try:
        cs.ascii_fqdn = availability.normalize(cs.fqdn)
        cs.tld = availability.tld_of(cs.ascii_fqdn)
        cs.invalid = False
    except ValueError:
        cs.ascii_fqdn = ""
        cs.tld = ""
        cs.invalid = True
    cs.phase = AvailabilityPhase.NORMALIZED.value
    return {"cell_state": cs.__dict__, "next_node": "resolve_rdap"}


def transition_to_rdap_resolved(state: dict[str, Any]) -> dict[str, Any]:
    """Resolve the RDAP URL and the G7 live-fetch decision (no network here)."""
    cs = _state(state)
    cs.live_allowed = live_rdap_allowed(state)
    if not cs.invalid:
        url = availability.rdap_url(cs.ascii_fqdn)
        cs.rdap_url = url or ""
    cs.phase = AvailabilityPhase.RDAP_RESOLVED.value
    return {"cell_state": cs.__dict__, "next_node": "classify"}


def transition_to_classified(state: dict[str, Any]) -> dict[str, Any]:
    """Classify via the real RDAP classifier. Live fetch happens ONLY if G7 allowed it."""
    cs = _state(state)
    fixtures = state.get("fixtures") or {}
    result = availability.check_availability(
        cs.fqdn, fixtures=fixtures, allow_live=cs.live_allowed
    )
    cs.status = result.status
    cs.source = result.source
    cs.representative = result.representative
    cs.rdap_url = result.rdap_url or cs.rdap_url
    cs.tld = result.tld or cs.tld
    cs.phase = AvailabilityPhase.CLASSIFIED.value
    return {"cell_state": cs.__dict__, "next_node": "availability_recorded"}


def transition_to_availability_recorded(state: dict[str, Any]) -> dict[str, Any]:
    """Emit the com.etzhayyim.yadori.availabilityRecord payload."""
    cs = _state(state)
    cs.phase = AvailabilityPhase.AVAILABILITY_RECORDED.value
    cs.payload["availability_record"] = {
        "fqdn": cs.fqdn,
        "asciiFqdn": cs.ascii_fqdn,
        "tld": cs.tld,
        "availability": cs.status,
        "rdapUrl": cs.rdap_url,
        "source": cs.source,            # "fixture" | "live" | "none"
        "representative": cs.representative,
    }
    return {"cell_state": cs.__dict__, "next_node": "end"}
