"""tedai (手代) kotoba Datom audit projector — every DesktopOp is a Datom (G7/G9), stdlib.

Projects a planned (or, post-activation, executed) DesktopOp into kotoba EAVT entity maps and
assembles a `kg.ingest_batch` body. This is the G7 audit trail: as-of, replayable — a member can
audit exactly what touched their machine. Three safety rules:

  - G3 no-secret-leak: only flag KEYS are serialized into `:op/args` (never values, which could
    carry a path fragment or token); the encrypted pairing grant lives elsewhere as an encref.
  - G9 evidence-minimization: evidence enters the log as a sha256 HASH, never a raw frame; the
    projector refuses a raw-frame payload by construction.
  - G6 dry-run: `:op/dry-run` is True at R0; live ingest into kotoba is operator-gated (refused here).

`planned_at` is supplied by the caller (a runtime stamps it; tests pass a fixed value) — this module
performs no clock reads, so its output is deterministic.
"""

from __future__ import annotations

import hashlib
import os

from desktop import DesktopOp

AUDIT_GRAPH = "tedai-audit-v1"
LIVE_INGEST_FLAG = "TEDAI_ALLOW_LIVE_INGEST"

# EDN keyword → :db keyword string mapping for op safety / gates (kept as the seed.edn spelling).
_SAFETY_KW = {"read": ":read", "create": ":create", "update": ":update", "delete": ":delete",
              "outward": ":outward"}
_TIER_KW = {
    "t1-scripting-api": ":t1-scripting-api",
    "t2-vision-pointer": ":t2-vision-pointer",
    "t3-file-level": ":t3-file-level",
    "": None,
}
_STANCE_KW = {"ok": ":ok",
              "refused-synthetic-input-prohibited": ":refused-synthetic-input-prohibited"}
_MUTATE_KW = {"read-allowed": ":read-allowed",
              "awaiting-member-sig": ":awaiting-member-sig",
              "awaiting-member-sig-and-outward-gate": ":awaiting-member-sig-and-outward-gate",
              "authorized": ":authorized"}


class LiveIngestRefused(RuntimeError):
    """Raised when a live kotoba ingest is requested without the operator gate (default-deny; G6)."""


class RawEvidenceRefused(ValueError):
    """Raised when raw frame bytes are offered as evidence (G9 — only a hash may enter the log)."""


def op_id(op: DesktopOp, planned_at: str) -> str:
    """Deterministic, content-derived op id: op:<app>:<noun>.<verb>:<8-hex>."""
    h = hashlib.sha256(f"{op.app}|{op.noun}|{op.verb}|{planned_at}".encode()).hexdigest()[:8]
    return f"op:{op.app}:{op.noun}.{op.verb}:{h}"


def evidence_hash(frame_bytes: bytes) -> str:
    """G9: the only form in which screen evidence may enter the audit log — a sha256 hex digest.
    The raw frame stays on-device under the member's key; this function is the boundary."""
    return hashlib.sha256(frame_bytes).hexdigest()


def _args_keys(op: DesktopOp) -> str:
    """G3: serialize only the flag KEYS (sorted), never values (a value could be a secret/path)."""
    return ",".join(sorted(op.args.keys()))


def _require(mapping: dict, value: str, fieldname: str) -> str | None:
    """G7: map a gate value to its EDN keyword, REFUSING an unknown value rather than fail-open.

    A silent default on a security-relevant audit field (stance-gate / mutate-gate) could record a
    refused/mutating op as permitted/read-allowed; the audit must never misreport, so drift raises."""
    if value not in mapping:
        raise ValueError(f"G7 audit: unknown {fieldname} value {value!r}; refuse to project a misleading datom")
    return mapping[value]


def op_entity(op: DesktopOp, planned_at: str, evidence_sha256: str | None = None,
              raw_frame: bytes | None = None) -> dict:
    """Project a DesktopOp into one kotoba EAVT entity map (G7). Raw frames are refused (G9)."""
    if raw_frame is not None:
        raise RawEvidenceRefused(
            "G9: raw frame bytes may not enter the audit log; pass evidence_hash(frame) instead"
        )
    ent = {
        ":op/id": op_id(op, planned_at),
        ":op/app": op.app,
        ":op/noun": op.noun,
        ":op/verb": op.verb,
        ":op/safety": _require(_SAFETY_KW, op.safety, "safety"),
        ":op/destructive": op.destructive,
        ":op/adapter-tier": _require(_TIER_KW, op.adapter_tier, "adapter-tier"),
        ":op/stance-gate": _require(_STANCE_KW, op.stance_gate, "stance-gate"),
        ":op/mutate-gate": _require(_MUTATE_KW, op.mutate_gate, "mutate-gate"),
        ":op/args": _args_keys(op),
        ":op/dry-run": op.dry_run,
        ":op/planned-at": planned_at,
    }
    if op.route:
        ent[":op/route"] = f":{op.route}"
    if op.t2_engine:
        ent[":op/t2-engine"] = f":{op.t2_engine}"
    if evidence_sha256:
        ent[":op/evidence-sha256"] = evidence_sha256
    return ent


def ingest_batch(entities: list[dict]) -> dict:
    """Assemble a kg.ingest_batch body over the tedai audit graph (G7)."""
    return {"graph": AUDIT_GRAPH, "entities": entities}


def ingest_live(entities: list[dict], env: dict | None = None) -> dict:
    """Live ingest into kotoba is operator-gated (G6): refused unless the flag is set."""
    environ = os.environ if env is None else env
    if environ.get(LIVE_INGEST_FLAG) != "1":
        raise LiveIngestRefused(
            f"G6: live kotoba ingest refused; set {LIVE_INGEST_FLAG}=1 under operator authority"
        )
    return ingest_batch(entities)
