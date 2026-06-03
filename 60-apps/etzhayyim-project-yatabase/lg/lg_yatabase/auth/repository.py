"""Yatabase auth repository — INSERT-only writes against vertex_api_key.

Per ADR-2605111200 the CF Worker no longer touches Hyperdrive; this
pod is the single writer. Row shape matches the legacy Worker INSERT
in src/auth-signup.ts (kept identical so existing /api/leads + auth
resolution paths keep reading the same columns).

Record-log semantics:
  * No UPDATE — `revoke` writes a fresh row with status='revoked' and
    a different vertex_id (or the same one to PK-upsert; see comments).
  * No ON CONFLICT — RW PK re-INSERT is implicit upsert.
  * Every row carries owner_did + created_at; mv_yata_api_key_active is
    the operator's read view.
"""

from __future__ import annotations

import hashlib
import logging
import random
import secrets
import string
import time
from datetime import datetime, timezone

from lg_yatabase.bmc.db import execute, fetchrow

_log = logging.getLogger(__name__)


_API_KEY_CHARS = string.ascii_letters + string.digits
_AWS_ID_CHARS = string.ascii_uppercase + string.digits


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def generate_api_key() -> str:
    """Mint `sk_live_yata_<24-rand-chars>`. Matches Worker generateApiKey()."""
    suffix = "".join(secrets.choice(_API_KEY_CHARS) for _ in range(24))
    return f"sk_live_yata_{suffix}"


def generate_aws_pair() -> tuple[str, str]:
    """Return (access_key_id, secret_access_key). Matches Worker shape."""
    aid = "etzhayyim_" + "".join(secrets.choice(_AWS_ID_CHARS) for _ in range(20))
    sec = secrets.token_hex(40)  # 80 hex chars
    return aid, sec


def generate_org_did(ts_ms: int | None = None) -> tuple[str, str]:
    """Return (org_did, tenant_name). Matches Worker shape."""
    ts = ts_ms if ts_ms is not None else int(time.time() * 1000)
    rand_a = format(random.SystemRandom().randint(0, 10**9), "x")
    rand_b = format(random.SystemRandom().randint(0, 10**9), "x")
    suffix = (rand_a + rand_b)[:16]
    return f"did:web:t-{suffix}.yata-tenant.etzhayyim.com", f"yata-tenant-{ts}"


async def insert_api_key(
    *,
    key_id: str,
    owner_did: str,
    key_hash: str,
    name: str,
    aws_access_key_id: str,
    aws_secret_access_key: str,
    status: str = "active",
    scopes: str = "atproto,include:com.etzhayyim.apps.yata",
    product_scope: str = "yata",
    key_prefix: str = "sk_live_yata_",
) -> dict[str, str]:
    """Insert one vertex_api_key row. Returns the persisted shape."""
    now_iso = _now_iso()
    await execute(
        """
        INSERT INTO vertex_api_key (
            vertex_id, owner_did, key_hash, key_prefix, name, scopes,
            status, product_scope, aws_access_key_id, aws_secret_access_key,
            created_at
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11
        )
        """,
        key_id,
        owner_did,
        key_hash,
        key_prefix,
        name,
        scopes,
        status,
        product_scope,
        aws_access_key_id,
        aws_secret_access_key,
        now_iso,
    )
    return {
        "vertex_id": key_id,
        "owner_did": owner_did,
        "name": name,
        "status": status,
        "created_at": now_iso,
    }


async def signup_anonymous(
    *,
    email: str | None = None,
    display_name: str | None = None,
) -> dict[str, str]:
    """Mint a fresh tenant + API key. Returns the same shape the legacy
    Worker /auth/v1/signup did (apiKey, keyId, orgDid, tenantName, …).

    The `apiKey` is returned ONCE; the row stores SHA-256(apiKey).
    """
    ts_ms = int(time.time() * 1000)
    org_did, tenant_name = generate_org_did(ts_ms)
    raw_key = generate_api_key()
    key_hash = _sha256_hex(raw_key)
    key_id = f"apikey:{key_hash[:16]}"
    aws_id, aws_secret = generate_aws_pair()

    await insert_api_key(
        key_id=key_id,
        owner_did=org_did,
        key_hash=key_hash,
        name=tenant_name,
        aws_access_key_id=aws_id,
        aws_secret_access_key=aws_secret,
    )

    return {
        "apiKey": raw_key,
        "keyId": key_id,
        "orgDid": org_did,
        "tenantName": tenant_name,
        "awsAccessKeyId": aws_id,
        "awsSecretAccessKey": aws_secret,
    }


async def invite_member(*, inviter_org_did: str, member_name: str) -> dict[str, str]:
    """Mint a fresh sk_live_yata_* key bound to the same owner_did as
    the inviter. Same tenant, new key.
    """
    if not inviter_org_did:
        raise ValueError("inviter_org_did required")
    raw_key = generate_api_key()
    key_hash = _sha256_hex(raw_key)
    key_id = f"apikey:{key_hash[:16]}"
    aws_id, aws_secret = generate_aws_pair()
    await insert_api_key(
        key_id=key_id,
        owner_did=inviter_org_did,
        key_hash=key_hash,
        name=member_name,
        aws_access_key_id=aws_id,
        aws_secret_access_key=aws_secret,
    )
    return {
        "apiKey": raw_key,
        "keyId": key_id,
        "orgDid": inviter_org_did,
        "memberName": member_name,
    }


async def resolve_api_key_by_hash(*, key_hash: str) -> dict[str, str] | None:
    """Resolve `sk_live_yata_*` SHA-256 hash → owner_did + scopes + product_scope.

    Read-only — mirrors the legacy CF Worker `verifyApiKey()` lookup that
    ADR-2605111200 broke (createKyselyDb prohibited in Workers). Returns
    None if the key is missing or revoked.
    """
    row = await fetchrow(
        "SELECT owner_did, scopes, product_scope, status "
        "FROM vertex_api_key WHERE key_hash = $1 AND status = 'active' LIMIT 1",
        key_hash,
    )
    if row is None:
        return None
    return {
        "ownerDid": str(row["owner_did"] or ""),
        "scopes": str(row["scopes"] or "read"),
        "productScope": str(row["product_scope"] or ""),
    }


async def revoke_key(*, vertex_id: str, org_did: str | None = None) -> dict[str, str]:
    """Revoke an API key — record-log style: re-insert with status='revoked'.
    RW PK upsert overrides the active row.
    """
    row = await fetchrow(
        "SELECT owner_did, key_hash, key_prefix, name, scopes, product_scope, "
        "aws_access_key_id, aws_secret_access_key "
        "FROM vertex_api_key WHERE vertex_id = $1 LIMIT 1",
        vertex_id,
    )
    if row is None:
        raise LookupError(f"vertex_api_key {vertex_id} not found")
    if org_did and row["owner_did"] != org_did:
        raise PermissionError(
            f"vertex_api_key {vertex_id} owned by {row['owner_did']}, not {org_did}"
        )
    now_iso = _now_iso()
    await execute(
        """
        INSERT INTO vertex_api_key (
            vertex_id, owner_did, key_hash, key_prefix, name, scopes,
            status, product_scope, aws_access_key_id, aws_secret_access_key,
            created_at
        ) VALUES (
            $1, $2, $3, $4, $5, $6, 'revoked', $7, $8, $9, $10
        )
        """,
        vertex_id,
        row["owner_did"],
        row["key_hash"],
        row["key_prefix"],
        row["name"],
        row["scopes"],
        row["product_scope"],
        row["aws_access_key_id"],
        row["aws_secret_access_key"],
        now_iso,
    )
    return {"vertex_id": vertex_id, "status": "revoked"}
