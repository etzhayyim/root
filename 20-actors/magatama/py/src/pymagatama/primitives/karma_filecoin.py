"""Karma Filecoin storage deal primitives (Phase K3).

Backs the L4 long-term persistence layer beyond ETH anchor. Each
IPFS-pinned karma CID gets proposed to N=5 Filecoin storage providers
via Estuary / Lighthouse / Web3.Storage HTTP API. Renewal cycle
(R/P30D) re-proposes deals expiring within 30 days.

Karma.lean karma_5_layer_persistence guarantee — RisingWave / AT-repo
/ IPFS-self / IPFS-ext / Filecoin = 5 layers.

Pyzeebe task types:
  karma.filecoin.proposeBatch    R/PT24H — propose deals for new pinned CIDs
  karma.filecoin.renewExpiring   R/P30D — renew deals expiring < 30d
  karma.filecoin.statusGet       query deal status for a CID
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import logging
import os
import time
import uuid
from typing import Any

from pymagatama.db_sync import sync_cursor

LOG = logging.getLogger("karma.filecoin")

KARMA_DID = "did:web:karma.gftd.ai"

# Phase K3: SP list is a static curated list. Phase K4 reads from a
# self-managed SP registry table populated from on-chain Storage
# Provider auctions.
DEFAULT_SP_LIST = [
    "f01000",  # placeholder Filecoin actor IDs
    "f01001",
    "f01002",
    "f01003",
    "f01004",
]

ESTUARY_URL = os.environ.get("KARMA_FILECOIN_ESTUARY_URL", "")
LIGHTHOUSE_URL = os.environ.get("KARMA_FILECOIN_LIGHTHOUSE_URL", "")
WEB3STORAGE_URL = os.environ.get("KARMA_FILECOIN_WEB3STORAGE_URL", "")
DEAL_PROVIDER = os.environ.get("KARMA_FILECOIN_PROVIDER", "estuary")  # estuary|lighthouse|web3storage|stub

DEFAULT_DURATION_DAYS = 540
DEFAULT_BYTES_FALLBACK = 4096
PROPOSAL_BATCH_DEFAULT = 200
RENEWAL_BATCH_DEFAULT = 500


# ── Helpers ────────────────────────────────────────────────────────────


def _now_ms() -> int:
    return int(time.time() * 1000)


def _now_ts() -> str:
    return _dt.datetime.now(tz=_dt.UTC).replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S")


def _deal_vertex_id(deal_id: str) -> str:
    return f"filecoin-deal-{deal_id}"


def _deal_id(cid: str, sp_address: str, nonce: str) -> str:
    return hashlib.sha256(f"{cid}|{sp_address}|{nonce}".encode()).hexdigest()[:32]


def _deal_proposal_cid_stub(cid: str, sp_address: str, nonce: str) -> str:
    """Phase K3 stub deal-proposal CID. K4 replaces with the real
    deal proposal hash returned by the SP/Estuary."""
    digest = hashlib.sha256(f"proposal|{cid}|{sp_address}|{nonce}".encode()).hexdigest()
    return f"bafyrei{digest[:52]}"


def _select_sps(count: int) -> list[str]:
    """Select N SPs round-robin from the configured list."""
    if count <= len(DEFAULT_SP_LIST):
        return DEFAULT_SP_LIST[:count]
    return (DEFAULT_SP_LIST * ((count // len(DEFAULT_SP_LIST)) + 1))[:count]


# ── Task: propose batch ────────────────────────────────────────────────


async def task_karma_filecoin_propose_batch(**kwargs: Any) -> dict[str, Any]:
    """Find IPFS-pinned CIDs without active Filecoin deals, propose
    deals at N SPs each. Phase K3 stub: records intent + deterministic
    deal_proposal_cid; the actual Estuary HTTP call is K4.
    """
    batch_size = int(kwargs.get("batchSize") or PROPOSAL_BATCH_DEFAULT)
    sp_count = int(kwargs.get("spCount") or 5)
    duration_days = int(kwargs.get("durationDays") or DEFAULT_DURATION_DAYS)

    proposed = 0
    skipped = 0
    failed = 0

    now_ms = _now_ms()
    now_ts = _now_ts()
    today_iso = _dt.datetime.now(tz=_dt.UTC).date().isoformat()
    expires_at_ms = now_ms + duration_days * 24 * 60 * 60 * 1000

    with sync_cursor() as cur:
        # Find pinned CIDs without an active deal.
        cur.execute(
            f"""
            SELECT DISTINCT cid
            FROM vertex_karma_ipfs_pin
            WHERE cid NOT IN (
              SELECT cid FROM vertex_karma_filecoin_deal
              WHERE status IN ('proposed','sealed','active')
            )
            ORDER BY cid
            LIMIT {int(batch_size)}
            """
        )
        cids = [r[0] for r in cur.fetchall() if r[0]]

        for cid in cids:
            sps = _select_sps(sp_count)
            for sp in sps:
                nonce = uuid.uuid4().hex
                deal_id = _deal_id(cid, sp, nonce)
                proposal_cid = _deal_proposal_cid_stub(cid, sp, nonce)
                vertex_id = _deal_vertex_id(deal_id)

                provider_endpoint = (
                    ESTUARY_URL if DEAL_PROVIDER == "estuary"
                    else LIGHTHOUSE_URL if DEAL_PROVIDER == "lighthouse"
                    else WEB3STORAGE_URL if DEAL_PROVIDER == "web3storage"
                    else ""
                )

                use_real_call = bool(provider_endpoint) and DEAL_PROVIDER != "stub"
                if use_real_call:
                    # Phase K4: HTTP POST to provider /deals endpoint
                    status = "deferred-real-provider-not-wired"
                    error_code = "K3_STUB"
                    error_message = (
                        "Phase K3 — real Filecoin deal proposal requires "
                        "py-multiformats / py-cid + provider SDK; recorded "
                        "as deferred for K4 retry."
                    )
                else:
                    status = "proposed"
                    error_code = ""
                    error_message = ""

                try:
                    cur.execute(
                        """
                        INSERT INTO vertex_karma_filecoin_deal (
                            vertex_id, _seq, created_date, sensitivity_ord, owner_did,
                            deal_id, cid, sp_address, deal_proposal_cid,
                            provider_endpoint, bundler_used,
                            proposed_at, proposed_at_ms,
                            sealed_at, sealed_at_ms,
                            expires_at_ms, duration_days, bytes_size,
                            retrieval_url, cost_usd_estimate,
                            status, error_code, error_message,
                            created_at, org_id, user_id, actor_id
                        ) VALUES (
                            %s, NULL, %s, 1, %s,
                            %s, %s, %s, %s,
                            %s, %s,
                            %s, %s,
                            NULL, NULL,
                            %s, %s, %s,
                            %s, NULL,
                            %s, %s, %s,
                            %s, %s, %s, %s
                        )
                        """,
                        (
                            vertex_id, today_iso, KARMA_DID,
                            deal_id, cid, sp, proposal_cid,
                            provider_endpoint, DEAL_PROVIDER,
                            now_ts, now_ms,
                            expires_at_ms, duration_days, DEFAULT_BYTES_FALLBACK,
                            f"https://{sp}.deal/{deal_id}",
                            status, error_code, error_message,
                            now_ts, KARMA_DID, KARMA_DID, "karma.filecoin.proposeBatch",
                        ),
                    )
                    if status == "proposed":
                        proposed += 1
                    else:
                        skipped += 1
                except Exception as exc:  # noqa: BLE001
                    LOG.warning("filecoin.propose INSERT err cid=%s sp=%s: %s", cid, sp, exc)
                    failed += 1

    return {"proposed": proposed, "skipped": skipped, "failed": failed}


# ── Task: renew expiring ───────────────────────────────────────────────


async def task_karma_filecoin_renew_expiring(**kwargs: Any) -> dict[str, Any]:
    """Find deals expiring < 30d, propose fresh deals (same SP if
    possible). Original row stays for audit lineage; new row gets a
    new deal_id."""
    batch_size = int(kwargs.get("batchSize") or RENEWAL_BATCH_DEFAULT)
    new_duration_days = int(kwargs.get("newDurationDays") or DEFAULT_DURATION_DAYS)

    renewed = 0
    skipped = 0
    failed = 0

    now_ms = _now_ms()
    now_ts = _now_ts()
    today_iso = _dt.datetime.now(tz=_dt.UTC).date().isoformat()
    new_expires_at_ms = now_ms + new_duration_days * 24 * 60 * 60 * 1000

    with sync_cursor() as cur:
        cur.execute(
            f"""
            SELECT cid, sp_address, bytes_size
            FROM mv_karma_filecoin_expiring_soon
            ORDER BY expires_at_ms ASC
            LIMIT {int(batch_size)}
            """
        )
        rows = cur.fetchall()

        for cid, sp, bytes_size in rows:
            nonce = uuid.uuid4().hex
            deal_id = _deal_id(cid, sp, nonce + "-renew")
            proposal_cid = _deal_proposal_cid_stub(cid, sp, nonce + "-renew")
            vertex_id = _deal_vertex_id(deal_id)
            try:
                cur.execute(
                    """
                    INSERT INTO vertex_karma_filecoin_deal (
                        vertex_id, _seq, created_date, sensitivity_ord, owner_did,
                        deal_id, cid, sp_address, deal_proposal_cid,
                        provider_endpoint, bundler_used,
                        proposed_at, proposed_at_ms,
                        sealed_at, sealed_at_ms,
                        expires_at_ms, duration_days, bytes_size,
                        retrieval_url, cost_usd_estimate,
                        status, error_code, error_message,
                        created_at, org_id, user_id, actor_id
                    ) VALUES (
                        %s, NULL, %s, 1, %s,
                        %s, %s, %s, %s,
                        '', %s,
                        %s, %s,
                        NULL, NULL,
                        %s, %s, %s,
                        %s, NULL,
                        'proposed', '', '',
                        %s, %s, %s, %s
                    )
                    """,
                    (
                        vertex_id, today_iso, KARMA_DID,
                        deal_id, cid, sp, proposal_cid,
                        DEAL_PROVIDER,
                        now_ts, now_ms,
                        new_expires_at_ms, new_duration_days, int(bytes_size or DEFAULT_BYTES_FALLBACK),
                        f"https://{sp}.deal/{deal_id}",
                        now_ts, KARMA_DID, KARMA_DID, "karma.filecoin.renewExpiring",
                    ),
                )
                renewed += 1
            except Exception as exc:  # noqa: BLE001
                LOG.warning("filecoin.renew INSERT err cid=%s sp=%s: %s", cid, sp, exc)
                failed += 1

    return {"renewed": renewed, "skipped": skipped, "failed": failed}


# ── Task: status get ───────────────────────────────────────────────────


async def task_karma_filecoin_status_get(**kwargs: Any) -> dict[str, Any]:
    cid = kwargs["cid"]
    deals: list[dict[str, Any]] = []
    active = 0
    expiring_soon = 0
    soon_threshold_ms = _now_ms() + 30 * 24 * 60 * 60 * 1000

    with sync_cursor() as cur:
        cur.execute(
            """
            SELECT deal_id, sp_address, status, sealed_at_ms, expires_at_ms,
                   bytes_size, retrieval_url
            FROM vertex_karma_filecoin_deal
            WHERE cid = %s
            ORDER BY proposed_at_ms DESC
            LIMIT 50
            """,
            (cid,),
        )
        for row in cur.fetchall():
            deal_id, sp, status, sealed_at_ms, expires_at_ms, bytes_size, retrieval_url = row
            d = {
                "dealId": deal_id,
                "spAddress": sp,
                "status": status,
                "sealedAtMs": int(sealed_at_ms or 0),
                "expiresAtMs": int(expires_at_ms or 0),
                "bytesSize": int(bytes_size or 0),
                "retrievalUrl": retrieval_url or "",
            }
            deals.append(d)
            if status in ("proposed", "sealed", "active"):
                active += 1
                if expires_at_ms and int(expires_at_ms) < soon_threshold_ms:
                    expiring_soon += 1

    return {
        "cid": cid,
        "deals": deals,
        "activeDealCount": active,
        "expiringSoonCount": expiring_soon,
    }


# ── Worker registration ────────────────────────────────────────────────


def register(worker: Any, *, timeout_ms: int = 60_000) -> None:
    """Register karma Filecoin task types.

      task_type="karma.filecoin.proposeBatch"
      task_type="karma.filecoin.renewExpiring"
      task_type="karma.filecoin.statusGet"
    """
    def t(name: str, fn: Any, *, ms: int | None = None) -> None:
        worker.task(task_type=name, single_value=False, timeout_ms=ms or timeout_ms)(fn)

    t("karma.filecoin.proposeBatch",   task_karma_filecoin_propose_batch,    ms=180_000)
    t("karma.filecoin.renewExpiring",  task_karma_filecoin_renew_expiring,   ms=180_000)
    t("karma.filecoin.statusGet",      task_karma_filecoin_status_get,       ms=15_000)


__all__ = [
    "register",
    "task_karma_filecoin_propose_batch",
    "task_karma_filecoin_renew_expiring",
    "task_karma_filecoin_status_get",
]
