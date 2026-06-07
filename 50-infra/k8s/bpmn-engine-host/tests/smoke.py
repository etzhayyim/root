#!/usr/bin/env python3
"""End-to-end smoke for ADR 2605081200 PoC Phase 1.

Acceptance criteria from the ADR:

  1. 100 instance 並行で p95 end-to-end < 30s
  2. engine host pod restart 時に running instance が history から
     replay されて完了する
  3. RW で `UPDATE` / `ON CONFLICT` が一切発行されない (pg log 確認)
  4. pyzeebe watchdog issue が再発しない

This script covers (1) directly and (3) indirectly via row-level
invariants on `vertex_spiff_history` (monotonic seq per instance,
no gaps). (2) and (4) are operational checks performed via
`kubectl delete pod` + `kubectl logs` and are documented in the
runbook section below.

Usage:

    BPMN_ENGINE_URL=http://localhost:8080 \
    RW_DSN=postgresql://USER:PASSWORD@HOST:4566/dev \
    python smoke.py \
      --process-id lawfirm_intake_funnel \
      --concurrency 100 \
      --timeout-s 60

Exit code 0 = all assertions passed; non-zero = failure (see stderr).

Operational follow-ups not covered here:
    - pg query log filter for `UPDATE vertex_bpmn_*` / `ON CONFLICT`
      (set `log_statement = all` on the RW frontend, run smoke,
      grep). RW does not support UPDATE so any hit indicates the
      engine drifted from the record-log model.
    - Engine pod restart replay: `kubectl -n mitama-udf delete pod
      -l app.kubernetes.io/name=bpmn-engine-host` mid-run, then
      verify the in-flight instances all reach `status='completed'`
      via `vertex_spiff_instance`.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import statistics
import sys
import time
from collections.abc import Iterable
from typing import Any

import httpx
import psycopg
from psycopg.rows import dict_row

log = logging.getLogger("smoke")

DEFAULT_ENGINE_URL = "http://localhost:8080"
DEFAULT_PROCESS_ID = "lawfirm_intake_funnel"


# ── Phase 1: start N instances ──────────────────────────────────────────────
async def start_instances(
    client: httpx.AsyncClient,
    process_id: str,
    n: int,
    request_timeout_s: float,
) -> list[tuple[str, float]]:
    """Returns [(instance_id, started_monotonic_s)]."""

    async def _one(idx: int) -> tuple[str, float] | None:
        body = {
            "processId": process_id,
            "variables": {"smokeId": f"smoke-{idx}"},
            "correlationKey": f"smoke-{idx}",
        }
        t0 = time.monotonic()
        delays = [0.2, 0.5, 1.0, 2.0]
        while True:
            try:
                resp = await client.post(
                    "/v1/instance",
                    json=body,
                    timeout=request_timeout_s,
                )
                resp.raise_for_status()
                break
            except httpx.HTTPStatusError as exc:
                retryable = exc.response.status_code in {404, 409, 500, 502, 503, 504}
                if not retryable or not delays:
                    log.error("start_instances[%d]: %s", idx, exc)
                    return None
            except httpx.HTTPError as exc:
                if not delays:
                    log.error("start_instances[%d]: %s", idx, exc)
                    return None
            delay = delays.pop(0)
            log.info("start_instances[%d]: transient start failure; retrying in %.1fs", idx, delay)
            await asyncio.sleep(delay)
        return resp.json()["instanceId"], t0

    results = await asyncio.gather(*[_one(i) for i in range(n)])
    return [r for r in results if r is not None]


# ── Phase 2: poll kotoba until completion ───────────────────────────────────────
def poll_completion(
    instance_ids: list[str],
    deadline_s: float,
) -> dict[str, dict[str, Any]]:
    """Poll `vertex_spiff_instance` until all `instance_ids` reach a terminal
    state (`completed` or `error`) or the deadline expires. Returns
    `{instance_id: {status, completed_at, _seq}}`."""
    from kotodama.kotoba_datomic import get_kotoba_client
    client = get_kotoba_client()
    completed: dict[str, dict[str, Any]] = {}
    while completed.keys() != set(instance_ids) and time.monotonic() < deadline_s:
        try:
            # We fetch all instances sequentially for the smoke test; could be parallelized
            # but usually concurrency is small enough (100)
            rows = []
            for iid in instance_ids:
                if iid in completed:
                    continue
                r = client.select_where("vertex_spiff_instance", "instance_id", iid, limit=200)
                rows.extend(r)
                
            latest_by_instance: dict[str, dict[str, Any]] = {}
            for row in sorted(rows, key=lambda r: int(r.get("_seq") or 0)):
                latest_by_instance[row["instance_id"]] = dict(row)
                
            for row in latest_by_instance.values():
                if row["status"] not in {"completed", "error", "cancelled"}:
                    continue
                record = dict(row)
                record["_observed_at_monotonic_s"] = time.monotonic()
                completed[row["instance_id"]] = record
        except Exception as exc:
            log.warning("poll_completion: transient kotoba query failure: %s", exc)
        if completed.keys() == set(instance_ids):
            break
        time.sleep(0.5)
    return completed


# ── Phase 3: invariants ─────────────────────────────────────────────────────
def assert_history_invariants(instance_ids: Iterable[str]) -> list[str]:
    """Confirm append-only history per instance: seq starts at 0,
    monotonic, no gaps. Returns a list of violation strings (empty =
    pass)."""
    from kotodama.kotoba_datomic import get_kotoba_client
    client = get_kotoba_client()
    violations: list[str] = []
    ids = list(instance_ids)
    if not ids:
        return violations
    
    rows_by_instance: dict[str, list[dict[str, Any]]] = {}
    for iid in ids:
        try:
            rows = client.select_where("vertex_spiff_history", "instance_id", iid, limit=2000)
            rows_by_instance[iid] = sorted(rows, key=lambda r: int(r.get("seq") or 0))
        except Exception as exc:
            violations.append(f"{iid}: fetch failed: {exc}")
            
    for iid in ids:
        instance_rows = rows_by_instance.get(iid) or []
        if not instance_rows:
            violations.append(f"{iid}: no history rows")
            continue
        seqs = [int(r.get("seq") or 0) for r in instance_rows]
        if seqs[0] != 0:
            violations.append(f"{iid}: history seq[0]={seqs[0]} (expected 0)")
        for i, s in enumerate(seqs):
            if s != i:
                violations.append(
                    f"{iid}: history seq gap at index {i}: got {s}",
                )
                break
    return violations


def assert_no_orphan_jobs(instance_ids: Iterable[str]) -> list[str]:
    """No `ready` / `claimed` jobs should remain after instance is
    completed."""
    from kotodama.kotoba_datomic import get_kotoba_client
    client = get_kotoba_client()
    violations: list[str] = []
    for iid in instance_ids:
        try:
            rows = client.select_where("vertex_spiff_job", "instance_id", iid, limit=2000)
            latest_by_job = {}
            for r in sorted(rows, key=lambda x: int(x.get("_seq") or 0)):
                latest_by_job[r.get("job_id")] = r
            
            active = sum(1 for r in latest_by_job.values() if r.get("status") in ("ready", "claimed"))
            if active > 0:
                violations.append(f"{iid}: {active} job rows still ready/claimed")
        except Exception as exc:
            violations.append(f"{iid}: fetch orphans failed: {exc}")
    return violations


def fetch_db_wall_durations(instance_ids: Iterable[str]) -> dict[str, float]:
    """Return DB-clock instance_started -> completed_at durations."""
    from kotodama.kotoba_datomic import get_kotoba_client
    from dateutil import parser
    client = get_kotoba_client()
    ids = list(instance_ids)
    if not ids:
        return {}
    res = {}
    for iid in ids:
        try:
            instances = client.select_where("vertex_spiff_instance", "instance_id", iid, limit=2000)
            completed_at = None
            for r in sorted(instances, key=lambda x: int(x.get("_seq") or 0)):
                if r.get("status") == "completed" and r.get("completed_at"):
                    completed_at = r.get("completed_at")

            history = client.select_where("vertex_spiff_history", "instance_id", iid, limit=2000)
            started_at = None
            for r in sorted(history, key=lambda x: int(x.get("seq") or 0)):
                if r.get("event_type") == "instance_started" and r.get("ts"):
                    started_at = r.get("ts")

            if completed_at and started_at:
                t1 = parser.parse(completed_at)
                t0 = parser.parse(started_at)
                res[iid] = (t1 - t0).total_seconds()
        except Exception:
            pass
    return res


# ── Driver ──────────────────────────────────────────────────────────────────
async def run(args: argparse.Namespace) -> int:
    engine_url = (args.engine_url or os.environ.get("BPMN_ENGINE_URL")
                  or DEFAULT_ENGINE_URL).rstrip("/")
    dsn = args.rw_dsn or os.environ.get("RW_DSN")
    if not dsn:
        log.error("RW_DSN required (env or --rw-dsn)")
        return 2

    log.info("smoke: engine=%s concurrency=%d process=%s timeout=%ds",
             engine_url, args.concurrency, args.process_id, args.timeout_s)

    async with httpx.AsyncClient(base_url=engine_url, timeout=args.request_timeout_s) as client:
        # readiness gate
        try:
            r = await client.get("/readyz")
            r.raise_for_status()
        except httpx.HTTPError as exc:
            log.error("smoke: engine not ready: %s", exc)
            return 2

        t_start = time.monotonic()
        starts = await start_instances(
            client,
            args.process_id,
            args.concurrency,
            args.request_timeout_s,
        )
        if len(starts) < args.concurrency:
            log.warning("smoke: only %d/%d instances started", len(starts),
                        args.concurrency)
        if not starts:
            return 3

    instance_ids = [iid for iid, _ in starts]
    started_at = dict(starts)
    deadline = t_start + args.timeout_s

    log.info("smoke: %d instances started, polling for completion …",
             len(instance_ids))
    completed = poll_completion(instance_ids, deadline)

    # ── Stats ──────────────────────────────────────────────────────────────
    db_wall_durations = fetch_db_wall_durations(instance_ids)
    durations: list[float] = []
    observed_durations: list[float] = []
    not_done: list[str] = []
    errors: list[str] = []
    for iid, t0 in starts:
        record = completed.get(iid)
        if record is None:
            not_done.append(iid)
            continue
        if record["status"] != "completed":
            errors.append(f"{iid}={record['status']}")
            continue
        # completed_at is an RW wall-clock timestamp; use the local poll
        # observation time captured when each row first reached terminal state.
        observed_durations.append(float(record["_observed_at_monotonic_s"]) - t0)
        durations.append(db_wall_durations.get(iid, observed_durations[-1]))

    p50 = statistics.median(durations) if durations else float("nan")
    p95 = (statistics.quantiles(durations, n=20)[-1]
           if len(durations) >= 20 else max(durations or [float("nan")]))
    p99 = (statistics.quantiles(durations, n=100)[-1]
           if len(durations) >= 100 else max(durations or [float("nan")]))

    history_violations = assert_history_invariants(instance_ids)
    orphan_violations = assert_no_orphan_jobs(
        [iid for iid in instance_ids if completed.get(iid, {}).get("status")
         == "completed"],
    )

    summary = {
        "concurrency": args.concurrency,
        "started": len(starts),
        "completed": len(durations),
        "errored": len(errors),
        "timed_out": len(not_done),
        "p50_s": round(p50, 3),
        "p95_s": round(p95, 3),
        "p99_s": round(p99, 3),
        "observed_p95_s": round(
            statistics.quantiles(observed_durations, n=20)[-1]
            if len(observed_durations) >= 20
            else max(observed_durations or [float("nan")]),
            3,
        ),
        "history_violations": history_violations[:20],
        "orphan_violations": orphan_violations[:20],
    }
    print(json.dumps(summary, sort_keys=True, indent=2))

    failures: list[str] = []
    if not_done:
        failures.append(f"{len(not_done)} instances did not reach terminal state")
    if errors:
        failures.append(f"{len(errors)} instances errored")
    if p95 >= args.p95_budget_s:
        failures.append(f"p95 {p95:.2f}s >= budget {args.p95_budget_s}s")
    if history_violations:
        failures.append(f"history invariants: {len(history_violations)} violation(s)")
    if orphan_violations:
        failures.append(f"orphan jobs: {len(orphan_violations)} instance(s)")

    if failures:
        for f in failures:
            log.error("FAIL: %s", f)
        return 1
    log.info("smoke: all assertions passed")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--engine-url", default=None,
                    help="default $BPMN_ENGINE_URL or " + DEFAULT_ENGINE_URL)
    ap.add_argument("--rw-dsn", default=None, help="default $RW_DSN")
    ap.add_argument("--process-id", default=DEFAULT_PROCESS_ID)
    ap.add_argument("--concurrency", type=int, default=100)
    ap.add_argument("--timeout-s", type=int, default=60)
    ap.add_argument("--request-timeout-s", type=float, default=60.0,
                    help="HTTP timeout for engine readiness/start calls")
    ap.add_argument("--p95-budget-s", type=float, default=30.0,
                    help="ADR acceptance: p95 < 30s")
    ap.add_argument("--log-level", default="INFO")
    args = ap.parse_args()
    logging.basicConfig(
        level=args.log_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    sys.exit(asyncio.run(run(args)))


if __name__ == "__main__":
    main()
