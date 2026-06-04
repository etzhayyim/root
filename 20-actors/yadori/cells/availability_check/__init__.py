"""yadori availability_check (宿り) cell — R0 scaffold.

Wraps methods/availability.py (RDAP classifier) as pure, unit-tested state transitions. The live
RDAP fetch is reachable only through the G7 operator gate (operator attestation + the
YADORI_ALLOW_LIVE_RDAP=1 environment flag); offline/fixture is the default. .solve() raises until
Council activation (ADR-2606038400).
"""
