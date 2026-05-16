"""End-to-end smoke for Public Malak artifact persistence and read paths."""

from __future__ import annotations

import json
import os
import time
import urllib.request
from dataclasses import dataclass
from typing import Any

import psycopg

from pymagatama.primitives import public_malak_ads as ads


OWNER_DID = "did:web:public-malak.gftd.ai"
PUBLIC_USER_AGENT = "public-malak-smoke/1 (+https://public-malak.gftd.ai)"


@dataclass(frozen=True)
class SmokeConfig:
    public_base_url: str
    dispatcher_url: str
    query_base: str
    rw_url: str
    internal_trust: str = ""
    snapshot_wait_sec: float = 300.0
    list_wait_sec: float = 90.0
    artifact_wait_sec: float = 240.0
    sleep_sec: float = 3.0


def config_from_env() -> SmokeConfig:
    return SmokeConfig(
        public_base_url=os.environ.get(
            "PUBLIC_MALAK_SMOKE_PUBLIC_BASE_URL",
            "https://public-malak.gftd.ai",
        ).rstrip("/"),
        dispatcher_url=os.environ.get(
            "PUBLIC_MALAK_SMOKE_DISPATCHER_URL",
            "http://bpmn-dispatcher.mitama-udf.svc.cluster.local:8080",
        ).rstrip("/"),
        query_base=os.environ.get("PUBLIC_MALAK_SMOKE_QUERY", "public malak smoke"),
        rw_url=os.environ["RW_URL"],
        internal_trust=os.environ.get("DISPATCHER_INTERNAL_SECRET", ""),
    )


def build_smoke_observation(query_base: str, now: int | None = None) -> tuple[str, dict[str, Any], dict[str, Any]]:
    suffix = str(now if now is not None else int(time.time()))
    query = f"{query_base} {suffix}"
    run_id = f"run-smoke-{suffix}"
    source_url = ads._ads_library_url("telegram", query, "US")
    run = {
        "platform": "telegram",
        "query_kind": "search",
        "query_value": query,
        "country": "US",
        "vertex_id": f"at://{OWNER_DID}/ai.gftd.apps.publicMalak.adScraperRun/{run_id}",
    }
    fetch_result = {
        "httpStatus": 200,
        "statusText": "OK",
        "headers": {"content-type": "text/html; charset=utf-8"},
        "finalUrl": source_url,
        "elapsedMs": 1,
        "text": f"<html><title>{query}</title><body>Public Malak smoke artifact {query}</body></html>",
        "error": "",
    }
    return run_id, run, fetch_result


def wait_for_snapshot(
    *,
    rw_url: str,
    creative_vertex_id: str,
    timeout_sec: float,
    sleep_sec: float,
) -> tuple[str, str, Any]:
    deadline = time.time() + timeout_sec
    row = None
    while time.time() < deadline:
        with psycopg.connect(rw_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT html_cid, har_cid, scraped_at
                    FROM vertex_ads_snapshot
                    WHERE creative_vertex_id = %s
                    ORDER BY scraped_at DESC, vertex_id DESC
                    LIMIT 1
                    """,
                    (creative_vertex_id,),
                )
                row = cur.fetchone()
        if row:
            html_cid, har_cid, scraped_at = row
            if not html_cid or not har_cid:
                raise RuntimeError(
                    f"snapshot missing artifact cids: html_cid={html_cid!r} har_cid={har_cid!r}"
                )
            return str(html_cid), str(har_cid), scraped_at
        time.sleep(sleep_sec)
    raise RuntimeError(f"snapshot row not found for {creative_vertex_id}")


def wait_for_list_snapshots(
    *,
    dispatcher_url: str,
    internal_trust: str,
    creative_vertex_id: str,
    html_cid: str,
    har_cid: str,
    timeout_sec: float,
    sleep_sec: float,
) -> dict[str, Any]:
    url = f"{dispatcher_url}/xrpc/ai.gftd.apps.publicMalak.listSnapshots"
    payload = json.dumps({"creativeVertexId": creative_vertex_id, "limit": 1}).encode()
    deadline = time.time() + timeout_sec
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            req = urllib.request.Request(
                url,
                data=payload,
                method="POST",
                headers={
                    "content-type": "application/json",
                    "x-internal-trust": internal_trust,
                },
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            snapshots = data.get("snapshots") or []
            if (
                snapshots
                and snapshots[0].get("htmlCid") == html_cid
                and snapshots[0].get("harCid") == har_cid
            ):
                return {"status": 200, "count": len(snapshots)}
            last_error = RuntimeError(f"latest snapshot mismatch: {data}")
        except Exception as exc:  # noqa: BLE001
            last_error = exc
        time.sleep(sleep_sec)
    raise RuntimeError(f"listSnapshots did not expose smoke snapshot: {last_error}")


def wait_for_artifact(
    *,
    public_base_url: str,
    kind: str,
    cid: str,
    timeout_sec: float,
    sleep_sec: float,
) -> dict[str, Any]:
    url = f"{public_base_url}/artifacts/{kind}/{cid}"
    deadline = time.time() + timeout_sec
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "accept": "*/*",
                    "user-agent": PUBLIC_USER_AGENT,
                },
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read()
                if resp.status != 200:
                    raise RuntimeError(f"{url} returned HTTP {resp.status}")
                if not body:
                    raise RuntimeError(f"{url} returned empty body")
                return {
                    "status": resp.status,
                    "bytes": len(body),
                    "store": resp.headers.get("x-artifact-store"),
                }
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            time.sleep(sleep_sec)
    raise RuntimeError(f"{url} did not become readable: {last_error}")


def run_smoke(config: SmokeConfig) -> dict[str, Any]:
    run_id, run, fetch_result = build_smoke_observation(config.query_base)
    written = ads._write_observation(run, fetch_result)
    creative_vertex_id = written.get("creativeVertexId")
    if not creative_vertex_id:
        raise RuntimeError(f"write_observation did not return creativeVertexId: {written}")
    print(json.dumps({"phase": "written", "creativeVertexId": creative_vertex_id, "runId": run_id}, sort_keys=True))

    html_cid, har_cid, scraped_at = wait_for_snapshot(
        rw_url=config.rw_url,
        creative_vertex_id=str(creative_vertex_id),
        timeout_sec=config.snapshot_wait_sec,
        sleep_sec=min(config.sleep_sec, 2.0),
    )
    snapshots = wait_for_list_snapshots(
        dispatcher_url=config.dispatcher_url,
        internal_trust=config.internal_trust,
        creative_vertex_id=str(creative_vertex_id),
        html_cid=html_cid,
        har_cid=har_cid,
        timeout_sec=config.list_wait_sec,
        sleep_sec=config.sleep_sec,
    )
    html = wait_for_artifact(
        public_base_url=config.public_base_url,
        kind="html",
        cid=html_cid,
        timeout_sec=config.artifact_wait_sec,
        sleep_sec=config.sleep_sec,
    )
    har = wait_for_artifact(
        public_base_url=config.public_base_url,
        kind="har",
        cid=har_cid,
        timeout_sec=config.artifact_wait_sec,
        sleep_sec=config.sleep_sec,
    )
    return {
        "ok": True,
        "platform": "telegram",
        "runId": run_id,
        "creativeVertexId": creative_vertex_id,
        "htmlCid": html_cid,
        "harCid": har_cid,
        "scrapedAt": str(scraped_at),
        "listSnapshots": snapshots,
        "html": html,
        "har": har,
    }


def main() -> None:
    print(json.dumps(run_smoke(config_from_env()), sort_keys=True))


if __name__ == "__main__":
    main()
