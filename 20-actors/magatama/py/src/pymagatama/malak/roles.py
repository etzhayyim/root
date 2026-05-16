"""Malak AI role registry — declarative SSoT.

Mirrors the definitions from 20-actors/malak/actor-manifest.jsonld and
20-actors/public-malak/actor-manifest.jsonld.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ActionClass = Literal["ingest_ioc", "correlate_ttp", "track_actor", "publish_public", "escalate_le"]

@dataclass(frozen=True)
class MalakRole:
    id: str
    title: str
    description: str
    allowed_tlp: tuple[str, ...]
    capabilities: tuple[str, ...]

ROLES: tuple[MalakRole, ...] = (
    MalakRole(
        id="malak",
        title="Malak Cybercrime Intelligence",
        description="Cybercrime CTI + threat actor tracking + LE coordination. Ingests all TLP levels.",
        allowed_tlp=("CLEAR", "GREEN", "AMBER", "RED"),
        capabilities=("ingest-ioc", "track-threat-actor", "correlate-ttp", "coordinate-le", "feed-public-malak"),
    ),
    MalakRole(
        id="public-malak",
        title="Public Malak",
        description="Sanitized public cybercrime feed. Audience: SOC analysts, researchers.",
        allowed_tlp=("CLEAR", "GREEN"),
        capabilities=("publish-indicator", "publish-actor-profile", "publish-ttp", "list-feeds", "subscribe-feed"),
    ),
    MalakRole(
        id="crypto-tracker",
        title="Malak Crypto Flow Tracker",
        description="Follows cryptocurrency transactions across blockchains to attribute actor funding and laundering.",
        allowed_tlp=("CLEAR", "GREEN", "AMBER", "RED"),
        capabilities=("trace-wallet", "identify-mixer", "correlate-exchange", "track-actor"),
    ),
    MalakRole(
        id="sns-tracker",
        title="Malak SNS Correlation Tracker",
        description="Correlates social media accounts, handles, and communication patterns to unmask threat actors.",
        allowed_tlp=("CLEAR", "GREEN", "AMBER", "RED"),
        capabilities=("correlate-sns", "map-social-graph", "extract-handle", "track-actor"),
    ),
    MalakRole(
        id="honeypot-tracker",
        title="Malak Honeypot Tracker",
        description="Actively registers trap emails on malicious sites, ingests resulting spam/phishing, extracts IOCs, and tracks actors via PREGEL.",
        allowed_tlp=("CLEAR", "GREEN", "AMBER", "RED"),
        capabilities=("ingest-honeypot", "extract-phishing-iocs", "track-actor", "persist-payload"),
    ),
    MalakRole(
        id="ransomware-actor-activity",
        title="Malak Ransomware Actor Activity Tracker",
        description="Passively collects recent ransomware actor activity from public CTI feeds and darkweb crawl metadata, then scores evidence via PREGEL.",
        allowed_tlp=("CLEAR", "GREEN", "AMBER", "RED"),
        capabilities=("ingest-ransomware-activity", "score-actor-activity", "track-actor", "publish-sanitized-summary"),
    ),
)

def by_id(role_id: str) -> MalakRole:
    for r in ROLES:
        if r.id == role_id:
            return r
    raise KeyError(f"unknown role: {role_id!r}")

@dataclass(frozen=True)
class GateVerdict:
    allowed: bool
    requires_sanitization: bool
    reason: str

def gate(role: MalakRole, tlp_level: str, action: str) -> GateVerdict:
    if tlp_level not in role.allowed_tlp:
        return GateVerdict(False, False, f"TLP {tlp_level} is not allowed for {role.id}")
    
    requires_sanitization = False
    if role.id == "public-malak":
        requires_sanitization = True # Rule RULE-PUBMALAK-VICTIM-REDACTION
        
    return GateVerdict(True, requires_sanitization, f"{action} allowed under TLP {tlp_level}")
