"""types — typed dataclasses matching the app.etzhayyim.* lexicons authored 2026-05-21.

Lexicons live in:
  00-contracts/lexicons/app/etzhayyim/shinka/        (6 NSIDs)
  00-contracts/lexicons/app/etzhayyim/translationLink.json
  00-contracts/lexicons/app/etzhayyim/bpmnActivityEvent.json
  00-contracts/lexicons/app/etzhayyim/actorQualityReport.json
  00-contracts/lexicons/app/etzhayyim/productIngest.json

ADR references:
  ADR-2605215200 §3 — shinka lexicons (evolutionEvent, kyumeiSignal, shinkaHeartbeat,
                       observeAdherent, validateEvolution, tick)
  ADR-2605215300 §2 — yoro lexicons (translationLink, bpmnActivityEvent, actorQualityReport)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# shinka lexicons (ADR-2605215200 §3)
# ---------------------------------------------------------------------------


@dataclass
class ShinkaHeartbeatRecord:
    """Wire shape for app.etzhayyim.shinka.shinkaHeartbeat.

    MST-only — no IPFS pin or Base L2 anchor (per ADR-2605215200 §1 ShinkaHeartbeatCell).

    Required fields per lexicon:
      nodeName, cycle, recordedAt, cellsObserved, cellsValidated, cellsEmitted
    """

    node_name: str          # enum: naphtali|simeon|judah|zebulun|levi|joseph|issachar|dan|benjamin|asher
    cycle: int              # monotonically increasing tick cycle counter
    recorded_at: str        # ISO 8601 datetime
    cells_observed: int     # number of adherent cells observed this tick
    cells_validated: int    # number of evolution claims validated
    cells_emitted: int      # number of evolution events emitted
    errors: list[str] = field(default_factory=list)

    def to_mst_record(self) -> dict[str, Any]:
        """Return the AT MST record dict matching the lexicon wire shape."""
        record: dict[str, Any] = {
            "$type": "app.etzhayyim.shinka.shinkaHeartbeat",
            "nodeName": self.node_name,
            "cycle": self.cycle,
            "recordedAt": self.recorded_at,
            "cellsObserved": self.cells_observed,
            "cellsValidated": self.cells_validated,
            "cellsEmitted": self.cells_emitted,
        }
        if self.errors:
            record["errors"] = self.errors
        return record


@dataclass
class KyumeiSignalRecord:
    """Wire shape for app.etzhayyim.shinka.kyumeiSignal.

    Consumed by KarmaHegemonObservationCell on levi (ADR-2605215200 §1).

    Required fields per lexicon:
      adherentDid, signalKind, weight, recordedAt, evidenceCid
    """

    adherent_did: str       # DID of the adherent
    signal_kind: str        # enum: ritual|oath|contribution|governance-participation|kuniUmi-witness
    weight: int             # 0–1000 permille
    recorded_at: str        # ISO 8601 datetime
    evidence_cid: str       # IPFS CID of the evidence record
    notes: str = ""

    def to_mst_record(self) -> dict[str, Any]:
        record: dict[str, Any] = {
            "$type": "app.etzhayyim.shinka.kyumeiSignal",
            "adherentDid": self.adherent_did,
            "signalKind": self.signal_kind,
            "weight": self.weight,
            "recordedAt": self.recorded_at,
            "evidenceCid": self.evidence_cid,
        }
        if self.notes:
            record["notes"] = self.notes
        return record


@dataclass
class EvolutionEventRecord:
    """Wire shape for app.etzhayyim.shinka.evolutionEvent.

    Written by EvolutionEmissionCell on simeon to MST + IPFS + Base L2 anchor
    (ADR-2605171800 Stage 3-5 pipeline). Wire-compatible with vendor
    shinka_tick_actor JSON output shape for interop at Step 8.
    """

    actor_did: str
    tick_ms: int
    mood: str
    actions: list[str] = field(default_factory=list)
    heartbeat_written: bool = False
    evolution_written: bool = False
    knowledge_written: bool = False
    evolution_level: int = 0
    base_l2_anchor_tx: str = ""    # Base L2 anchor tx hash
    ipfs_cid: str = ""             # IPFS CID of pinned evolution evidence

    def to_mst_record(self) -> dict[str, Any]:
        return {
            "$type": "app.etzhayyim.shinka.evolutionEvent",
            "actorDid": self.actor_did,
            "tickMs": self.tick_ms,
            "mood": self.mood,
            "actions": self.actions,
            "heartbeatWritten": self.heartbeat_written,
            "evolutionWritten": self.evolution_written,
            "knowledgeWritten": self.knowledge_written,
            "evolutionLevel": self.evolution_level,
            "baseL2AnchorTx": self.base_l2_anchor_tx,
            "ipfsCid": self.ipfs_cid,
        }


# ---------------------------------------------------------------------------
# yoro lexicons (ADR-2605215300 §2)
# ---------------------------------------------------------------------------


@dataclass
class TranslationLinkRecord:
    """Wire shape for app.etzhayyim.translationLink.

    Required fields per lexicon:
      sourceUri, sourceLang, targetUri, targetLang, translatedAt,
      qualityScore (0–1000 permille), translatorDid
    """

    source_uri: str         # AT URI of source post (at-uri format)
    source_lang: str        # ISO 639-1 code, e.g. "ja"
    target_uri: str         # AT URI of translated post (at-uri format)
    target_lang: str        # ISO 639-1 code, e.g. "en"
    translated_at: str      # ISO 8601 datetime
    quality_score: int      # 0–1000 permille
    translator_did: str     # DID of translator (human or agent)
    model: str = ""         # optional LLM model identifier
    notes: str = ""

    def to_mst_record(self) -> dict[str, Any]:
        record: dict[str, Any] = {
            "$type": "app.etzhayyim.translationLink",
            "sourceUri": self.source_uri,
            "sourceLang": self.source_lang,
            "targetUri": self.target_uri,
            "targetLang": self.target_lang,
            "translatedAt": self.translated_at,
            "qualityScore": self.quality_score,
            "translatorDid": self.translator_did,
        }
        if self.model:
            record["model"] = self.model
        if self.notes:
            record["notes"] = self.notes
        return record


@dataclass
class BpmnActivityEventRecord:
    """Wire shape for app.etzhayyim.bpmnActivityEvent.

    Required fields per lexicon:
      caseId, taskType, lifecycle, actorDid, eventType, payloadJson, occurredAt
    """

    case_id: str
    task_type: str
    lifecycle: str          # e.g. "started", "completed", "failed"
    actor_did: str
    event_type: str
    payload_json: str       # JSON string of event payload
    occurred_at: str        # ISO 8601 datetime

    def to_mst_record(self) -> dict[str, Any]:
        return {
            "$type": "app.etzhayyim.bpmnActivityEvent",
            "caseId": self.case_id,
            "taskType": self.task_type,
            "lifecycle": self.lifecycle,
            "actorDid": self.actor_did,
            "eventType": self.event_type,
            "payloadJson": self.payload_json,
            "occurredAt": self.occurred_at,
        }


@dataclass
class ActorQualityReportRecord:
    """Wire shape for app.etzhayyim.actorQualityReport.

    Recommended lexicon per ADR-2605215300 §2.
    Replaces in-memory return value with durable MST record.
    """

    actor_did: str
    quality_score: float    # 0.0–1.0
    missing_fields: list[str] = field(default_factory=list)
    posts_count: int = 0
    inspected_at: str = ""

    def to_mst_record(self) -> dict[str, Any]:
        return {
            "$type": "app.etzhayyim.actorQualityReport",
            "actorDid": self.actor_did,
            "qualityScore": self.quality_score,
            "missingFields": self.missing_fields,
            "postsCount": self.posts_count,
            "inspectedAt": self.inspected_at,
        }
