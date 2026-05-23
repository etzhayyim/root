"""Perceive → invoke → record wrapper for UNSPSC actor invocations.

The wrapper is a plain async function, not a nested LangGraph. Composing a
wrapper graph over each of the 18,342 per-actor StateGraphs would double
the compile cost and pollute the cell-runner cache; a pure function around
the inner `.ainvoke(payload)` call is sufficient and keeps the inner
graph's State schema untouched.

The belief store is opened lazily per actor DID and cached in-process. If
the store cannot be opened (no writable ORGANISM_SQLITE_DIR, permissions
error, schema init failure) the wrapper degrades to pass-through — the
actor still runs, just without observation persistence. Substrate failures
must never block actor invocation.
"""

from __future__ import annotations

import datetime as _dt
import json
import logging
import os
import threading
from typing import Any

LOG = logging.getLogger("unispsc-capabilities")

_STORE_CACHE: dict[str, Any] = {}
_STORE_LOCK = threading.Lock()
_STORE_DISABLED = False


def _now_iso() -> str:
    return _dt.datetime.now(tz=_dt.UTC).replace(microsecond=0).isoformat()


def _actor_did(code: str) -> str:
    return f"did:web:etzhayyim.com:actor:c{code}"


def _open_store(agent_did: str) -> Any | None:
    """Return a per-actor belief store, or None if storage is unavailable."""
    global _STORE_DISABLED
    if _STORE_DISABLED:
        return None
    with _STORE_LOCK:
        cached = _STORE_CACHE.get(agent_did)
        if cached is not None:
            return cached
        try:
            from pymagatama.primitives.at_ipfs_belief_store import (
                AtIpfsLocalBeliefStore,
                _sanitize_did,
            )
        except Exception as e:  # noqa: BLE001
            LOG.warning("unispsc-capabilities: belief store import failed (%s); disabling", e)
            _STORE_DISABLED = True
            return None
        env_dir = os.environ.get("ORGANISM_SQLITE_DIR") or "/var/lib/etzhayyim/organism"
        try:
            from pathlib import Path

            Path(env_dir).mkdir(parents=True, exist_ok=True)
            # Publish callback (best-effort) sends each observation to the AT
            # PDS so downstream mst-projector + ipfs-pinner + anchor-cron pick
            # it up — making the record public + IPFS-content-addressed +
            # L2-anchored per ADR-2605231400 yatachain composition. If the
            # PDS endpoint env is unset (or auth fails / network error) the
            # callback returns None and the store stays local-SQLite-only.
            from pymagatama.unispsc_capabilities.pds_publish import (
                make_publish_callback,
            )

            publish_cb = make_publish_callback()
            store = AtIpfsLocalBeliefStore(
                db_path=f"{env_dir}/{_sanitize_did(agent_did)}.db",
                publish=publish_cb,
            )
            if publish_cb is not None:
                LOG.info(
                    "unispsc-capabilities: belief store armed with PDS publish "
                    "(observations will be committed to AT + IPFS + L2 anchor "
                    "pipeline downstream)"
                )
        except Exception as e:  # noqa: BLE001
            LOG.warning(
                "unispsc-capabilities: cannot open belief store at %s (%s); disabling",
                env_dir,
                e,
            )
            _STORE_DISABLED = True
            return None
        _STORE_CACHE[agent_did] = store
        return store


def _read_prior(store: Any, agent_did: str, limit: int) -> list[dict[str, Any]]:
    try:
        records = store.list_observations(agent_did, source_kinds=("unispsc_invoke",), limit=limit)
    except Exception as e:  # noqa: BLE001
        LOG.warning("unispsc-capabilities: list_observations failed (%s); returning empty", e)
        return []
    out: list[dict[str, Any]] = []
    for r in records:
        try:
            payload = json.loads(r.payload_json)
        except Exception:  # noqa: BLE001
            payload = {"raw": r.payload_json}
        out.append(
            {
                "observed_at": r.observed_at,
                "source_ref": r.source_ref,
                "payload": payload,
            }
        )
    return out


def _record_observation(
    store: Any,
    agent_did: str,
    *,
    input_payload: dict[str, Any],
    result: dict[str, Any],
    elapsed_ms: int,
) -> str | None:
    from pymagatama.primitives.active_inference_substrate import ObservationRecord

    log_tail = (result.get("log") or [])[-5:]
    obs_payload = {
        "input": input_payload,
        "log_tail": log_tail,
        "result": result.get("result"),
        "elapsed_ms": elapsed_ms,
    }
    rec = ObservationRecord(
        agent_did=agent_did,
        source_kind="unispsc_invoke",
        observed_at=_now_iso(),
        payload_json=json.dumps(obs_payload, default=str),
        confidence_permille=800,
        uncertainty_permille=200,
        source_ref="invoke",
        sensitivity_ord=1,
    )
    try:
        return store.put_observation(rec) or None
    except Exception as e:  # noqa: BLE001
        LOG.warning("unispsc-capabilities: put_observation failed (%s); skipping persistence", e)
        return None


async def invoke_with_capability(
    code: str,
    graph: Any,
    payload: dict[str, Any],
    *,
    timeout_s: float,
    prior_limit: int = 5,
) -> dict[str, Any]:
    """Run perceive → inner-graph → record. Augments response with
    `_observation_uri` and `_prior_count`. Belief-store failures degrade
    to pass-through.
    """
    import asyncio
    import time

    agent_did = _actor_did(code)
    started = time.time()

    store = _open_store(agent_did)
    prior: list[dict[str, Any]] = []
    if store is not None:
        prior = _read_prior(store, agent_did, prior_limit)

    inner_payload = {**payload, "_prior_observations": prior} if prior else payload

    result = await asyncio.wait_for(graph.ainvoke(inner_payload), timeout=timeout_s)

    elapsed_ms = int((time.time() - started) * 1000)
    observation_uri: str | None = None
    if store is not None and isinstance(result, dict):
        observation_uri = _record_observation(
            store,
            agent_did,
            input_payload=payload,
            result=result,
            elapsed_ms=elapsed_ms,
        )

    if isinstance(result, dict):
        result.setdefault("_observation_uri", observation_uri)
        result.setdefault("_prior_count", len(prior))
    return result


def capability_wrapping_enabled() -> bool:
    return os.environ.get("ETZ_UNISPSC_CAPABILITY_WRAP", "").lower() in ("1", "true", "yes")
