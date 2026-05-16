"""Delegated authority policy loading for resident agent dispatch."""

from __future__ import annotations

import json
from typing import Any


def _json_value(value: Any, default: Any) -> Any:
    if value is None:
        return default
    if isinstance(value, dict | list):
        return value
    try:
        return json.loads(str(value or ""))
    except json.JSONDecodeError:
        return default


def row_to_policy(row: dict[str, Any]) -> dict[str, Any]:
    payload_constraints = _json_value(row.get("payload_constraints_json"), {})
    return {
        "authorityRef": row.get("authority_ref") or "",
        "policyRef": row.get("policy_ref") or "",
        "agentDid": row.get("agent_did") or "",
        "principalDid": row.get("principal_did") or "",
        "allowedChannels": _json_value(row.get("channels_json"), []),
        "allowedEffectClasses": _json_value(row.get("effect_classes_json"), []),
        "allowedTargetRefs": _json_value(row.get("target_bindings_json"), []),
        "allowedRecipientDomains": payload_constraints.get("allowedRecipientDomains", []),
        "payloadConstraints": payload_constraints,
        "budgetRef": row.get("budget_ref") or "",
        "rateLimit": _json_value(row.get("rate_limit_json"), {}),
        "expiresAt": row.get("expires_at") or "",
        "policyCid": row.get("policy_cid") or "",
        "signatureRef": row.get("signature_ref") or "",
        "status": row.get("status") or "",
        "specificPredelegation": bool(payload_constraints.get("specificPredelegation")),
    }


def load_delegated_authority_policy(
    *,
    authority_ref: str,
    policy_ref: str,
    agent_did: str = "",
) -> dict[str, Any]:
    if not authority_ref or not policy_ref:
        return {}
    from pymagatama.db_sync import sync_cursor

    params: list[Any] = [authority_ref, policy_ref]
    agent_filter = ""
    if agent_did:
        agent_filter = " AND agent_did = %s"
        params.append(agent_did)
    with sync_cursor() as cur:
        cur.execute(
            f"""
            SELECT authority_ref, policy_ref, agent_did, principal_did,
                   channels_json, effect_classes_json, target_bindings_json,
                   payload_constraints_json, budget_ref, rate_limit_json,
                   expires_at, policy_cid, signature_ref, status
            FROM vertex_agent_delegated_authority_policy
            WHERE authority_ref = %s
              AND policy_ref = %s
              {agent_filter}
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            tuple(params),
        )
        columns = [desc[0] for desc in cur.description or []]
        row = cur.fetchone()
    if not row:
        return {}
    return row_to_policy(dict(zip(columns, row, strict=False)))
