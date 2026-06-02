"""telecom Phase 18 primitives — eSIM / eUICC Lifecycle (GSMA SGP.22 / SGP.02).

Eight BPMN service tasks:

  - telecom.esim.euicc.provision   EID registration
  - telecom.esim.profile.download  SM-DP+ profile download
  - telecom.esim.profile.enable    SGP.22 §3.2 enable
  - telecom.esim.profile.disable   SGP.22 §3.2 disable
  - telecom.esim.profile.delete    SGP.22 §3.3 delete
  - telecom.esim.smds.register     SM-DS event registration (SGP.22 §3.6)
  - telecom.esim.euicc.audit       eUICC state snapshot
  - telecom.esim.profile.transfer  MNO-to-MNO ownership transfer

PII discipline:
  eid  → sha256: hashed (device-bound, quasi-PII)
  iccid → sha256: hashed (quasi-PII)
  sensitivity_ord = 2 for all tables
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime
from typing import Any

from pymagatama.db_sync import sync_cursor


TELECOM_DID = "did:web:telecom.etzhayyim.com"
ACTOR_TAG = "sys.worker.telecom.esim"

DEVICE_KINDS = {"smartphone", "tablet", "wearable", "iot", "automotive", "cpe"}
PROFILE_TYPES = {"telecom", "iot", "m2m", "enterprise"}
PROFILE_STATES = {"downloaded", "installed", "enabled", "disabled", "deleted"}
OP_KINDS = {"enable", "disable", "delete"}
DISABLE_REASONS = {"suspended", "lostDevice", "fraudPrevention", "maintenanceMode", "userRequest"}
DELETE_REASONS = {"contractTerminated", "deviceReplaced", "mnoMigration", "euiccReset", "userRequest"}
EVENT_TYPES = {"profileDownload", "profileUpdate", "policyUpdate"}


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _new_id(prefix: str, *parts: Any) -> str:
    if parts:
        digest = hashlib.sha256("|".join(str(p) for p in parts).encode()).hexdigest()[:24]
        return f"{prefix}_{digest}"
    return f"{prefix}_{secrets.token_hex(10)}"


def _vid(kind: str, key: str) -> str:
    return f"at://{TELECOM_DID}/com.etzhayyim.apps.telecom.{kind}/{key}"


def _hash(value: str | None) -> str | None:
    if not value:
        return None
    if value.startswith("sha256:"):
        return value
    return "sha256:" + hashlib.sha256(value.encode()).hexdigest()


def _require(payload: dict[str, Any], fields: list[str]) -> None:
    missing = [f for f in fields if payload.get(f) in (None, "")]
    if missing:
        raise ValueError(f"Missing required fields: {missing}")


# ─── provisionEuicc ──────────────────────────────────────────────────────────

def handle_provision_euicc(payload: dict[str, Any]) -> dict[str, Any]:
    _require(payload, ["eid", "deviceKind"])

    eid_hash = _hash(payload["eid"])
    device_kind = payload["deviceKind"]
    if device_kind not in DEVICE_KINDS:
        device_kind = "smartphone"

    observed_at = payload.get("observedAt") or _now_iso()
    vertex_id = _vid("euicc", _new_id("euicc", eid_hash))

    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_telecom_esim_euicc (
              vertex_id, owner_did, eid, device_kind, manufacturer_name,
              platform_version, smdp_address, smds_address, profile_slots,
              observed_at, status, created_at, sensitivity_ord,
              org_id, user_id, actor_id
            ) VALUES (
              %s, %s, %s, %s, %s,
              %s, %s, %s, %s,
              %s, %s, %s, %s,
              %s, %s, %s
            )
            """,
            (
                vertex_id, TELECOM_DID, eid_hash, device_kind,
                payload.get("manufacturerName"), payload.get("platformVersion"),
                payload.get("smdpAddress"), payload.get("smdsAddress"),
                payload.get("profileSlots"),
                observed_at, "active", observed_at, 2,
                payload.get("callerDid", TELECOM_DID),
                payload.get("callerDid", TELECOM_DID),
                ACTOR_TAG,
            ),
        )

    return {"vertexId": vertex_id, "eid": eid_hash, "status": "active"}


# ─── downloadEsimProfile ─────────────────────────────────────────────────────

def handle_download_esim_profile(payload: dict[str, Any]) -> dict[str, Any]:
    _require(payload, ["downloadId", "eid", "iccid", "smdpAddress"])

    eid_hash = _hash(payload["eid"])
    iccid_hash = _hash(payload["iccid"])
    profile_type = payload.get("profileType")
    if profile_type and profile_type not in PROFILE_TYPES:
        profile_type = "telecom"

    observed_at = payload.get("observedAt") or _now_iso()
    vertex_id = _vid("esimProfile", payload["downloadId"])

    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_telecom_esim_profile (
              vertex_id, owner_did, download_id, eid, iccid,
              matching_id, smdp_address, profile_type, mno,
              profile_state, observed_at, status, created_at,
              sensitivity_ord, org_id, user_id, actor_id
            ) VALUES (
              %s, %s, %s, %s, %s,
              %s, %s, %s, %s,
              %s, %s, %s, %s,
              %s, %s, %s, %s
            )
            """,
            (
                vertex_id, TELECOM_DID, payload["downloadId"],
                eid_hash, iccid_hash,
                payload.get("matchingId"), payload["smdpAddress"],
                profile_type, payload.get("mno"),
                "installed", observed_at, "completed", observed_at,
                2,
                payload.get("callerDid", TELECOM_DID),
                payload.get("callerDid", TELECOM_DID),
                ACTOR_TAG,
            ),
        )

    return {"vertexId": vertex_id, "iccid": iccid_hash, "status": "completed"}


# ─── enableEsimProfile ───────────────────────────────────────────────────────

def handle_enable_esim_profile(payload: dict[str, Any]) -> dict[str, Any]:
    _require(payload, ["operationId", "eid", "iccid"])

    eid_hash = _hash(payload["eid"])
    iccid_hash = _hash(payload["iccid"])
    observed_at = payload.get("observedAt") or _now_iso()
    vertex_id = _vid("esimProfileOp", payload["operationId"])

    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_telecom_esim_profile_op (
              vertex_id, owner_did, operation_id, eid, iccid,
              op_kind, refresh_flag, reason,
              observed_at, status, created_at, sensitivity_ord,
              org_id, user_id, actor_id
            ) VALUES (
              %s, %s, %s, %s, %s,
              %s, %s, %s,
              %s, %s, %s, %s,
              %s, %s, %s
            )
            """,
            (
                vertex_id, TELECOM_DID, payload["operationId"],
                eid_hash, iccid_hash,
                "enable", payload.get("refreshFlag", False), None,
                observed_at, "enabled", observed_at, 2,
                payload.get("callerDid", TELECOM_DID),
                payload.get("callerDid", TELECOM_DID),
                ACTOR_TAG,
            ),
        )

    return {"vertexId": vertex_id, "iccid": iccid_hash, "status": "enabled"}


# ─── disableEsimProfile ──────────────────────────────────────────────────────

def handle_disable_esim_profile(payload: dict[str, Any]) -> dict[str, Any]:
    _require(payload, ["operationId", "eid", "iccid"])

    eid_hash = _hash(payload["eid"])
    iccid_hash = _hash(payload["iccid"])
    reason = payload.get("reason")
    if reason and reason not in DISABLE_REASONS:
        reason = "userRequest"

    observed_at = payload.get("observedAt") or _now_iso()
    vertex_id = _vid("esimProfileOp", payload["operationId"])

    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_telecom_esim_profile_op (
              vertex_id, owner_did, operation_id, eid, iccid,
              op_kind, reason, refresh_flag,
              observed_at, status, created_at, sensitivity_ord,
              org_id, user_id, actor_id
            ) VALUES (
              %s, %s, %s, %s, %s,
              %s, %s, %s,
              %s, %s, %s, %s,
              %s, %s, %s
            )
            """,
            (
                vertex_id, TELECOM_DID, payload["operationId"],
                eid_hash, iccid_hash,
                "disable", reason, False,
                observed_at, "disabled", observed_at, 2,
                payload.get("callerDid", TELECOM_DID),
                payload.get("callerDid", TELECOM_DID),
                ACTOR_TAG,
            ),
        )

    return {"vertexId": vertex_id, "iccid": iccid_hash, "status": "disabled"}


# ─── deleteEsimProfile ───────────────────────────────────────────────────────

def handle_delete_esim_profile(payload: dict[str, Any]) -> dict[str, Any]:
    _require(payload, ["operationId", "eid", "iccid"])

    eid_hash = _hash(payload["eid"])
    iccid_hash = _hash(payload["iccid"])
    reason = payload.get("reason")
    if reason and reason not in DELETE_REASONS:
        reason = "userRequest"

    observed_at = payload.get("observedAt") or _now_iso()
    vertex_id = _vid("esimProfileOp", payload["operationId"])

    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_telecom_esim_profile_op (
              vertex_id, owner_did, operation_id, eid, iccid,
              op_kind, reason, refresh_flag,
              observed_at, status, created_at, sensitivity_ord,
              org_id, user_id, actor_id
            ) VALUES (
              %s, %s, %s, %s, %s,
              %s, %s, %s,
              %s, %s, %s, %s,
              %s, %s, %s
            )
            """,
            (
                vertex_id, TELECOM_DID, payload["operationId"],
                eid_hash, iccid_hash,
                "delete", reason, False,
                observed_at, "deleted", observed_at, 2,
                payload.get("callerDid", TELECOM_DID),
                payload.get("callerDid", TELECOM_DID),
                ACTOR_TAG,
            ),
        )

    return {"vertexId": vertex_id, "iccid": iccid_hash, "status": "deleted"}


# ─── registerSmdpEvent ───────────────────────────────────────────────────────

def handle_register_smdp_event(payload: dict[str, Any]) -> dict[str, Any]:
    _require(payload, ["eventId", "eid", "smdpAddress", "eventType"])

    eid_hash = _hash(payload["eid"])
    event_type = payload["eventType"]
    if event_type not in EVENT_TYPES:
        event_type = "profileDownload"

    observed_at = payload.get("observedAt") or _now_iso()
    vertex_id = _vid("smdsEvent", payload["eventId"])

    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_telecom_esim_smds_event (
              vertex_id, owner_did, event_id, eid, smdp_address, smds_address,
              event_type, iccid, expires_at,
              observed_at, status, created_at, sensitivity_ord,
              org_id, user_id, actor_id
            ) VALUES (
              %s, %s, %s, %s, %s, %s,
              %s, %s, %s,
              %s, %s, %s, %s,
              %s, %s, %s
            )
            """,
            (
                vertex_id, TELECOM_DID, payload["eventId"],
                eid_hash, payload["smdpAddress"],
                payload.get("smdsAddress"),
                event_type,
                _hash(payload.get("iccid")),
                payload.get("expiresAt"),
                observed_at, "pending", observed_at, 2,
                payload.get("callerDid", TELECOM_DID),
                payload.get("callerDid", TELECOM_DID),
                ACTOR_TAG,
            ),
        )

    return {"vertexId": vertex_id, "eventId": payload["eventId"], "status": "pending"}


# ─── auditEuiccState ─────────────────────────────────────────────────────────

def handle_audit_euicc_state(payload: dict[str, Any]) -> dict[str, Any]:
    _require(payload, ["auditId", "eid"])

    eid_hash = _hash(payload["eid"])
    observed_at = payload.get("observedAt") or _now_iso()
    vertex_id = _vid("esimAudit", payload["auditId"])

    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_telecom_esim_audit (
              vertex_id, owner_did, audit_id, eid, profile_count,
              active_iccid, free_memory_bytes, last_contact_at,
              observed_at, status, created_at, sensitivity_ord,
              org_id, user_id, actor_id
            ) VALUES (
              %s, %s, %s, %s, %s,
              %s, %s, %s,
              %s, %s, %s, %s,
              %s, %s, %s
            )
            """,
            (
                vertex_id, TELECOM_DID, payload["auditId"], eid_hash,
                payload.get("profileCount"),
                _hash(payload.get("activeIccid")),
                payload.get("freeMemoryBytes"),
                payload.get("lastContactAt"),
                observed_at, "recorded", observed_at, 2,
                payload.get("callerDid", TELECOM_DID),
                payload.get("callerDid", TELECOM_DID),
                ACTOR_TAG,
            ),
        )

    return {"vertexId": vertex_id, "eid": eid_hash, "status": "recorded"}


# ─── transferEsimOwnership ───────────────────────────────────────────────────

def handle_transfer_esim_ownership(payload: dict[str, Any]) -> dict[str, Any]:
    _require(payload, ["transferId", "eid", "iccid", "sourceMno", "targetMno", "targetSmdpAddress"])

    eid_hash = _hash(payload["eid"])
    iccid_hash = _hash(payload["iccid"])
    observed_at = payload.get("observedAt") or _now_iso()
    vertex_id = _vid("esimOwnershipTransfer", payload["transferId"])

    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_telecom_esim_ownership_transfer (
              vertex_id, owner_did, transfer_id, eid, iccid,
              source_mno, target_mno, target_smdp_address, porting_ref,
              observed_at, status, created_at, sensitivity_ord,
              org_id, user_id, actor_id
            ) VALUES (
              %s, %s, %s, %s, %s,
              %s, %s, %s, %s,
              %s, %s, %s, %s,
              %s, %s, %s
            )
            """,
            (
                vertex_id, TELECOM_DID, payload["transferId"],
                eid_hash, iccid_hash,
                payload["sourceMno"], payload["targetMno"],
                payload["targetSmdpAddress"], payload.get("portingRef"),
                observed_at, "initiated", observed_at, 2,
                payload.get("callerDid", TELECOM_DID),
                payload.get("callerDid", TELECOM_DID),
                ACTOR_TAG,
            ),
        )

    return {"vertexId": vertex_id, "transferId": payload["transferId"], "status": "initiated"}


# ─── Worker registration ──────────────────────────────────────────────────────

def register(worker: Any, timeout_ms: int = 30_000) -> None:
    @worker.task(task_type="telecom.esim.euicc.provision", timeout_ms=timeout_ms)
    def _provision(payload: dict) -> dict:
        return handle_provision_euicc(payload)

    @worker.task(task_type="telecom.esim.profile.download", timeout_ms=timeout_ms)
    def _download(payload: dict) -> dict:
        return handle_download_esim_profile(payload)

    @worker.task(task_type="telecom.esim.profile.enable", timeout_ms=timeout_ms)
    def _enable(payload: dict) -> dict:
        return handle_enable_esim_profile(payload)

    @worker.task(task_type="telecom.esim.profile.disable", timeout_ms=timeout_ms)
    def _disable(payload: dict) -> dict:
        return handle_disable_esim_profile(payload)

    @worker.task(task_type="telecom.esim.profile.delete", timeout_ms=timeout_ms)
    def _delete(payload: dict) -> dict:
        return handle_delete_esim_profile(payload)

    @worker.task(task_type="telecom.esim.smds.register", timeout_ms=timeout_ms)
    def _smds(payload: dict) -> dict:
        return handle_register_smdp_event(payload)

    @worker.task(task_type="telecom.esim.euicc.audit", timeout_ms=timeout_ms)
    def _audit(payload: dict) -> dict:
        return handle_audit_euicc_state(payload)

    @worker.task(task_type="telecom.esim.profile.transfer", timeout_ms=timeout_ms)
    def _transfer(payload: dict) -> dict:
        return handle_transfer_esim_ownership(payload)
