"""Karma witness invitation primitives.

Triggered by `karma.evaluate` (recommendation = 'require-witness') to
fan-out invitations to candidate witnesses, who can then accept (→
produces vertex_karma_witness row) or decline.

Pyzeebe task types:
  karma.witness.inviteFanOut         per-invitee INSERT
  karma.witness.respondToInvitation  accept/decline persistence
  karma.witness.sweepExpired         R/PT1H sweeper
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import logging
import time
import uuid
from typing import Any

from pymagatama.db_sync import sync_cursor

LOG = logging.getLogger("karma.witness")

KARMA_DID = "did:web:karma.gftd.ai"

VALID_RESPONSES = ("accept", "decline")
VALID_ATTESTATION_KINDS = ("confirms", "disputes", "contextualizes", "addsEvidence")
INVITATION_PENDING_LIMIT = 200


# ── Helpers ────────────────────────────────────────────────────────────


def _now_ms() -> int:
    return int(time.time() * 1000)


def _now_ts() -> str:
    return _dt.datetime.now(tz=_dt.UTC).replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S")


def _now_iso() -> str:
    return (
        _dt.datetime.now(tz=_dt.UTC)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _content_addressed_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("|".join(parts).encode()).hexdigest()
    return f"{prefix}-{digest[:24]}"


# ── Task: invite fan-out ───────────────────────────────────────────────


async def task_karma_witness_invite_fan_out(**kwargs: Any) -> dict[str, Any]:
    edge_id = kwargs.get("edgeId") or ""
    candidate = kwargs.get("candidate")
    inviter_did = kwargs["inviterDid"]
    invitee_dids = kwargs.get("inviteeDids") or []
    if not isinstance(invitee_dids, list):
        invitee_dids = []
    message = kwargs.get("message") or ""
    rationale_cid = kwargs.get("rationaleCid")
    expires_in_days = int(kwargs.get("expiresInDays") or 14)

    invited_at_ms = _now_ms()
    invited_at = _now_ts()
    expires_at_ms = invited_at_ms + expires_in_days * 24 * 60 * 60 * 1000
    today_iso = _dt.datetime.now(tz=_dt.UTC).date().isoformat()

    candidate_json = json.dumps(candidate, separators=(",", ":")) if candidate else None

    invitation_ids: list[str] = []
    seen: set[str] = set()

    with sync_cursor() as cur:
        # Reject inviter from inviting themselves; dedup invitee list.
        for invitee in invitee_dids:
            if not invitee or invitee == inviter_did or invitee in seen:
                continue
            seen.add(invitee)

            # Prevent re-inviting an invitee who already attested this edge.
            if edge_id:
                cur.execute(
                    """
                    SELECT count(*) FROM vertex_karma_witness
                    WHERE edge_id = %s AND witness_did = %s
                    """,
                    (edge_id, invitee),
                )
                if int(cur.fetchone()[0]) > 0:
                    LOG.info("invite skip: %s already witnessed %s", invitee, edge_id)
                    continue

            # Prevent duplicate pending invitation.
            if edge_id:
                cur.execute(
                    """
                    SELECT count(*) FROM vertex_karma_witness_invitation
                    WHERE edge_id = %s AND invitee_did = %s AND status = 'pending'
                    """,
                    (edge_id, invitee),
                )
                if int(cur.fetchone()[0]) > 0:
                    LOG.info("invite skip: pending invitation already exists for %s/%s", invitee, edge_id)
                    continue

            nonce = uuid.uuid4().hex
            invitation_id = _content_addressed_id(
                "inv", edge_id or "candidate", inviter_did, invitee, str(invited_at_ms), nonce
            )
            vertex_id = f"invitation-{invitation_id}"

            cur.execute(
                """
                INSERT INTO vertex_karma_witness_invitation (
                    vertex_id, _seq, created_date, sensitivity_ord, owner_did,
                    invitation_id, edge_id, candidate_json,
                    inviter_did, invitee_did,
                    message, rationale_cid,
                    invited_at, invited_at_ms, expires_at_ms,
                    status,
                    created_at, org_id, user_id, actor_id
                ) VALUES (
                    %s, NULL, %s, 1, %s,
                    %s, %s, %s,
                    %s, %s,
                    %s, %s,
                    %s, %s, %s,
                    'pending',
                    %s, %s, %s, %s
                )
                """,
                (
                    vertex_id, today_iso, inviter_did,
                    invitation_id, edge_id or None, candidate_json,
                    inviter_did, invitee,
                    message, rationale_cid,
                    invited_at, invited_at_ms, expires_at_ms,
                    invited_at, inviter_did, inviter_did, "karma.witness.inviteFanOut",
                ),
            )
            invitation_ids.append(invitation_id)

    return {
        "invitationIds": invitation_ids,
        "inviteCount": len(invitation_ids),
        "expiresAtMs": expires_at_ms,
    }


# ── Task: respond to invitation ────────────────────────────────────────


async def task_karma_witness_respond_to_invitation(**kwargs: Any) -> dict[str, Any]:
    invitation_id = kwargs["invitationId"]
    responder_did = kwargs["responderDid"]
    response = (kwargs["response"] or "").lower()
    attestation_kind = (kwargs.get("attestationKind") or "confirms").lower()
    signature = kwargs.get("signature") or ""
    signature_alg = kwargs.get("signatureAlg") or "es256"
    rationale_cid = kwargs.get("rationaleCid")

    if response not in VALID_RESPONSES:
        raise ValueError(f"karma.witness.respond: invalid response {response}")
    if response == "accept":
        if attestation_kind not in VALID_ATTESTATION_KINDS:
            raise ValueError(
                f"karma.witness.respond: invalid attestationKind {attestation_kind}"
            )
        if not signature:
            raise ValueError("karma.witness.respond: signature required for accept")

    now_ms = _now_ms()
    responded_at = _now_ts()
    today_iso = _dt.datetime.now(tz=_dt.UTC).date().isoformat()
    witness_id = ""

    with sync_cursor() as cur:
        # Load + verify invitation.
        cur.execute(
            """
            SELECT edge_id, invitee_did, expires_at_ms, status
            FROM vertex_karma_witness_invitation
            WHERE invitation_id = %s
            LIMIT 1
            """,
            (invitation_id,),
        )
        row = cur.fetchone()
        if not row:
            raise ValueError(f"invitation {invitation_id} not found")
        edge_id, invitee_did, expires_at_ms, status = row
        if status != "pending":
            raise ValueError(f"invitation already responded (status={status})")
        if int(expires_at_ms) <= now_ms:
            # Lazy expire: mark + reject.
            cur.execute(
                """
                UPDATE vertex_karma_witness_invitation
                SET status = 'expired',
                    responded_at = %s, responded_at_ms = %s
                WHERE invitation_id = %s AND status = 'pending'
                """,
                (responded_at, now_ms, invitation_id),
            )
            raise ValueError("invitation expired")
        if responder_did != invitee_did:
            raise ValueError("responder mismatch")

        if response == "accept":
            witness_id = _content_addressed_id(
                "witness", edge_id or "candidate", responder_did, attestation_kind, str(now_ms)
            )
            vertex_id = f"witness-{witness_id}"
            cur.execute(
                """
                INSERT INTO vertex_karma_witness (
                    vertex_id, _seq, created_date, sensitivity_ord, owner_did,
                    witness_id, edge_id, witness_did, witness_organism_cid,
                    attestation_kind, signature, signature_alg, ts_ms,
                    created_at, org_id, user_id, actor_id
                ) VALUES (
                    %s, NULL, %s, 1, %s,
                    %s, %s, %s, NULL,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s
                )
                """,
                (
                    vertex_id, today_iso, responder_did,
                    witness_id, edge_id or "", responder_did,
                    attestation_kind, signature, signature_alg, now_ms,
                    responded_at, responder_did, responder_did, "karma.witness.respondToInvitation",
                ),
            )

        cur.execute(
            """
            UPDATE vertex_karma_witness_invitation
            SET status = %s,
                response = %s,
                response_witness_id = %s,
                responded_at = %s,
                responded_at_ms = %s
            WHERE invitation_id = %s AND status = 'pending'
            """,
            (
                "accepted" if response == "accept" else "declined",
                response,
                witness_id or None,
                responded_at,
                now_ms,
                invitation_id,
            ),
        )

    return {
        "witnessId": witness_id,
        "respondedAt": responded_at,
    }


# ── Task: sweep expired ────────────────────────────────────────────────


async def task_karma_witness_sweep_expired(**kwargs: Any) -> dict[str, Any]:
    now_ms = _now_ms()
    responded_at = _now_ts()

    with sync_cursor() as cur:
        cur.execute(
            f"""
            SELECT invitation_id
            FROM vertex_karma_witness_invitation
            WHERE status = 'pending' AND expires_at_ms <= %s
            ORDER BY expires_at_ms ASC
            LIMIT {INVITATION_PENDING_LIMIT}
            """,
            (now_ms,),
        )
        expired_ids = [r[0] for r in cur.fetchall()]

        for inv_id in expired_ids:
            cur.execute(
                """
                UPDATE vertex_karma_witness_invitation
                SET status = 'expired',
                    responded_at = %s, responded_at_ms = %s
                WHERE invitation_id = %s AND status = 'pending'
                """,
                (responded_at, now_ms, inv_id),
            )

        cur.execute(
            "SELECT count(*) FROM vertex_karma_witness_invitation WHERE status = 'pending'"
        )
        still_pending = int(cur.fetchone()[0])

    return {"expired": len(expired_ids), "stillPending": still_pending}


# ── Worker registration ────────────────────────────────────────────────


def register(worker: Any, *, timeout_ms: int = 60_000) -> None:
    """Register karma witness invitation task types.

      task_type="karma.witness.inviteFanOut"
      task_type="karma.witness.respondToInvitation"
      task_type="karma.witness.sweepExpired"
    """
    def t(name: str, fn: Any, *, ms: int | None = None) -> None:
        worker.task(task_type=name, single_value=False, timeout_ms=ms or timeout_ms)(fn)

    t("karma.witness.inviteFanOut",        task_karma_witness_invite_fan_out,        ms=60_000)
    t("karma.witness.respondToInvitation", task_karma_witness_respond_to_invitation, ms=30_000)
    t("karma.witness.sweepExpired",        task_karma_witness_sweep_expired,         ms=60_000)


__all__ = [
    "register",
    "task_karma_witness_invite_fan_out",
    "task_karma_witness_respond_to_invitation",
    "task_karma_witness_sweep_expired",
]
