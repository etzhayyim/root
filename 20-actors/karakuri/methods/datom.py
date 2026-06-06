"""karakuri (絡繰) kotoba Datom audit projector — every ServiceOp is a Datom (G7), stdlib.

Projects a planned (or, post-activation, executed) ServiceOp / CommandPlan / ExportArtifact into
kotoba EAVT entity maps that mirror kotoba/schema.edn (and seed.edn shape), and assembles a
`kg.ingest_batch` body. This is the G7 audit trail: as-of, replayable, 非終末論 — a member can audit
exactly what touched their account. Two safety rules:

  - G3 no-secret-leak: only flag KEYS are serialized into `:op/args` (never values, which could carry a
    token); the encrypted session-grant lives elsewhere as an encref, never here.
  - G6 dry-run: `:op/dry-run` is True at R0; live ingest into kotoba is operator-gated (refused here).

`planned_at` is supplied by the caller (a runtime stamps it; tests pass a fixed value) — this module
performs no clock reads, so its output is deterministic.
"""

from __future__ import annotations

import hashlib
import os

from command import ServiceOp

AUDIT_GRAPH = "karakuri-audit-v1"
LIVE_INGEST_FLAG = "KARAKURI_ALLOW_LIVE_INGEST"

# EDN keyword → :db keyword string mapping for op safety / gates (kept as the seed.edn spelling).
_SAFETY_KW = {"read": ":read", "create": ":create", "update": ":update", "delete": ":delete"}
_TIER_KW = {
    "t1-official-api": ":t1-official-api",
    "t2-headless-browser": ":t2-headless-browser",
    "t3-structured-export": ":t3-structured-export",
    "": None,
}
_TOS_KW = {"ok": ":ok", "refused-automation-prohibited": ":refused-automation-prohibited"}
_MUTATE_KW = {"read-allowed": ":read-allowed", "awaiting-member-sig": ":awaiting-member-sig",
              "authorized": ":authorized"}


class LiveIngestRefused(RuntimeError):
    """Raised when a live kotoba ingest is requested without the operator gate (default-deny; G6)."""


def op_id(op: ServiceOp, planned_at: str) -> str:
    """Deterministic, content-derived op id: op:<service>:<noun>.<verb>:<8-hex>."""
    h = hashlib.sha256(f"{op.service}|{op.noun}|{op.verb}|{planned_at}".encode()).hexdigest()[:8]
    return f"op:{op.service}:{op.noun}.{op.verb}:{h}"


def _args_keys(op: ServiceOp) -> str:
    """G3: serialize only the flag KEYS (sorted), never values (a value could be a secret/token)."""
    return ",".join(sorted(op.args.keys()))


def _require(mapping: dict, value: str, field: str) -> str:
    """G7: map a gate value to its EDN keyword, REFUSING an unknown value rather than fail-open.

    A silent default on a security-relevant audit field (tos-gate / mutate-gate) could record a
    refused/mutating op as permitted/read-allowed; the audit must never misreport, so drift raises."""
    if value not in mapping:
        raise ValueError(f"G7 audit: unknown {field} value {value!r}; refuse to project a misleading datom")
    return mapping[value]


def op_to_entity(op: ServiceOp, planned_at: str, *, oid: str | None = None) -> dict:
    """Project one ServiceOp into a kotoba `:op/*` entity map (mirrors seed.edn; G7)."""
    ent = {
        ":op/id": oid or op_id(op, planned_at),
        ":op/noun": op.noun,
        ":op/verb": op.verb,
        # safety defaults conservatively to :update (fail-CLOSED — an unknown verb is treated as mutating).
        ":op/safety": _SAFETY_KW.get(op.safety, ":update"),
        ":op/destructive": op.destructive,
        ":op/dry-run": True,                              # G6 invariant at R0
        # gate fields are strict (no fail-open default): an unknown value refuses to project (G7).
        ":op/tos-gate": _require(_TOS_KW, op.tos_gate, "tos-gate"),
        ":op/mutate-gate": _require(_MUTATE_KW, op.mutate_gate, "mutate-gate"),
        ":op/planned-at": planned_at,                     # as-of audit history (G7)
    }
    tier = _TIER_KW.get(op.adapter_tier)
    if tier is not None:
        ent[":op/adapter-tier"] = tier
    if op.t2_engine:
        ent[":op/t2-engine"] = f":{op.t2_engine}"        # :browser-use
    keys = _args_keys(op)
    if keys:
        ent[":op/args"] = keys                            # G3 — keys only
    return ent


def plan_to_entities(command_plan, planned_at: str) -> list[dict]:
    """Project a CommandPlan (brief + ops) into a `:plan/*` entity + its `:op/*` entities (G7)."""
    op_entities = [op_to_entity(op, planned_at) for op in command_plan.ops]
    plan_ent = {
        ":plan/id": "plan:" + hashlib.sha256(
            f"{command_plan.brief}|{planned_at}".encode()).hexdigest()[:8],
        ":plan/brief": command_plan.brief,
        ":plan/op": [e[":op/id"] for e in op_entities],   # ref-by-id (G7 join)
        ":plan/charter-clean": command_plan.charter_clean,  # N6
    }
    return [plan_ent, *op_entities]


def export_to_entity(artifact, *, eid: str | None = None) -> dict:
    """Project an ExportArtifact into a kotoba `:export/*` entity map (G7/G9)."""
    return {
        ":export/id": eid or f"export:{artifact.service}:{artifact.fmt}",
        ":export/service": artifact.service,   # schema :export/service ref — audit which service (G7)
        ":export/format": f":{artifact.fmt}",
        ":export/owner": ":member",        # G9
        ":export/encrypted": True,         # G9
        **({":export/cid": artifact.cid} if artifact.cid else {}),
    }


def to_ingest_batch(entities: list[dict], *, graph: str = AUDIT_GRAPH) -> dict:
    """Assemble a kotoba `kg.ingest_batch` body from entity maps (offline; G6 dry-run)."""
    return {"op": "kg.ingest_batch", "graph": graph, "entities": entities}


def ingest_live(batch: dict, *, operator_attestation: str | None = None, env: dict | None = None):
    """G6: live ingest into the kotoba Datom log is operator-gated — refused by default at R0."""
    flag = (env or os.environ).get(LIVE_INGEST_FLAG)
    if flag != "1" or not operator_attestation:
        raise LiveIngestRefused(
            f"G6: live kotoba ingest is operator-gated ({LIVE_INGEST_FLAG}=1 + operator attestation); "
            "R0 emits the batch but never writes"
        )
    raise LiveIngestRefused("live kotoba ingest client not wired at R0 (Council activation pending)")
