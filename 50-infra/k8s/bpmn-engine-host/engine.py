"""SpiffWorkflow engine host — RisingWave-backed runtime.

ADR 2605081200 (PoC Phase 1). Real implementation of the in-memory
BPMN engine boundary up to "load XML + advance one instance one step":

    load_process(bpmn_process_id)      → cached spec + subprocess specs
    create_instance(process_id, variables, correlation_key)
                                       → INSERT vertex_spiff_instance row 0,
                                         enqueue READY tasks to
                                         vertex_spiff_job, append history.
    advance_instance(instance_id)      → load JSON → do_engine_steps() →
                                         re-enqueue ready tasks → re-INSERT
                                         instance row + history.

Persistence path = root CLAUDE.md "Record-log semantics": no UPDATE,
no ON CONFLICT, every transition is a fresh PK INSERT. RW treats the
PK as implicit upsert. `db.transaction()` is a no-op on RW; we do not
wrap the per-step writes in a transaction.

NOT in this slice (Phase 1 follow-ups):
    * complete_job() worker callback that injects task result data and
      advances the token. Currently READY tasks for service tasks are
      enqueued; the engine waits for the corresponding `vertex_spiff_job`
      row to flip to status='completed' but does not yet consume it.
    * Timer reconciler (vertex_spiff_timer 1s tick).
    * Signal / message correlation routing.
    * Subprocess-aware spec cache invalidation on redeploy.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from lxml import etree
from kotodama.kotoba_datomic import KotobaDatomicClient
from SpiffWorkflow.bpmn.parser.BpmnParser import BpmnParser
from SpiffWorkflow.bpmn.serializer.default import BpmnTaskSpecConverter
from SpiffWorkflow.bpmn.serializer.workflow import (
    DEFAULT_CONFIG,
    BpmnWorkflowSerializer,
)
from SpiffWorkflow.bpmn.specs.defaults import (
    ReceiveTask,
    SendTask,
    ServiceTask,
)
from SpiffWorkflow.bpmn.specs.event_definitions.item_aware_event import (
    ErrorEventDefinition,
)
from SpiffWorkflow.bpmn.util.event import BpmnEvent
from SpiffWorkflow.bpmn.workflow import BpmnWorkflow
from SpiffWorkflow.task import TaskState

# BPMN namespace map for Zeebe extension extraction.
_NS = {
    "bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL",
    "zeebe": "http://camunda.org/schema/zeebe/1.0",
}


class _etzhayyimServiceTaskConverter(BpmnTaskSpecConverter):
    """Round-trips the dynamic `task_type` attribute that we inject onto
    `ServiceTask` specs from `<zeebe:taskDefinition type="...">`. Spiff's
    default converter doesn't know about this attribute (Zeebe ext is
    Camunda 8, not Spiff-native), so we serialize it explicitly."""

    def to_dict(self, spec):
        d = super().to_dict(spec)
        tt = getattr(spec, "task_type", None)
        if tt is not None:
            d["task_type"] = tt
        return d

    def from_dict(self, dct):
        tt = dct.pop("task_type", None)
        spec = super().from_dict(dct)
        if tt is not None:
            spec.task_type = tt
        return spec


def _build_serializer() -> BpmnWorkflowSerializer:
    """Configure a serializer that handles the spec classes Spiff's default
    `DEFAULT_CONFIG` omits (`ServiceTask`, `SendTask`, `ReceiveTask` —
    Spiff treats external work as user-supplied) plus our `task_type`
    attribute round-trip."""
    config = dict(DEFAULT_CONFIG)
    config[ServiceTask] = _etzhayyimServiceTaskConverter
    config.setdefault(SendTask, BpmnTaskSpecConverter)
    config.setdefault(ReceiveTask, BpmnTaskSpecConverter)
    registry = BpmnWorkflowSerializer.configure(config)
    return BpmnWorkflowSerializer(registry=registry)


def _inject_zeebe_task_types(spec, xml_root, bpmn_process_id: str) -> int:
    """Read `<zeebe:taskDefinition type="...">` from each `serviceTask`
    in the source XML and set `task_type` on the matching Spiff task_spec.

    Returns the number of injections (for debug logs).

    Why this exists: SpiffWorkflow's default `BpmnParser` does not
    understand Camunda 8 (Zeebe) extension elements; SpiffWorkflow's
    own `spiff` parser uses a different DSL (`serviceTaskOperator`).
    The lawfirm BPMN corpus is Zeebe-shaped (every `<bpmn:serviceTask>`
    carries `<zeebe:taskDefinition type="...">`), so we extract the
    `type` value out-of-band and stitch it onto the parsed spec.
    """
    proc = xml_root.find(f".//bpmn:process[@id='{bpmn_process_id}']", _NS)
    if proc is None:
        return 0
    n = 0
    for st in proc.findall(".//bpmn:serviceTask", _NS):
        bpmn_id = st.get("id")
        td = st.find(".//zeebe:taskDefinition", _NS)
        if td is None or bpmn_id not in spec.task_specs:
            continue
        spec.task_specs[bpmn_id].task_type = td.get("type")
        n += 1
    return n

log = logging.getLogger(__name__)


# ── Identity helpers ────────────────────────────────────────────────────────
ENGINE_OWNER_DID = "did:web:bpmn.etzhayyim.com"
PROCESS_DID_HOST = "did:web:bpmn.etzhayyim.com"


def _vertex_instance(instance_id: str, seq: int = 0) -> str:
    return f"at://{PROCESS_DID_HOST}/com.etzhayyim.apps.spiff.instance/{instance_id}:{seq}"


def _vertex_job(job_id: str, seq: int = 0) -> str:
    return f"at://{PROCESS_DID_HOST}/com.etzhayyim.apps.spiff.job/{job_id}:{seq}"


def _vertex_history(instance_id: str, seq: int) -> str:
    return f"at://{PROCESS_DID_HOST}/com.etzhayyim.apps.spiff.history/{instance_id}:{seq}"


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _today() -> str:
    return datetime.now(UTC).date().isoformat()


def _write_visibility_retries() -> int:
    return max(1, int(os.environ.get("BPMN_ENGINE_WRITE_VISIBLE_RETRIES", "45")))


def _write_visibility_interval_s() -> float:
    return max(0.1, float(os.environ.get("BPMN_ENGINE_WRITE_VISIBLE_INTERVAL_S", "1.0")))


def _write_visibility_required() -> bool:
    return os.environ.get("BPMN_ENGINE_WRITE_VISIBLE_REQUIRED", "").lower() in {
        "1", "true", "yes", "on",
    }


# ── Process spec cache ──────────────────────────────────────────────────────
@dataclass
class CachedSpec:
    bpmn_process_id: str
    version: int
    spec: Any  # SpiffWorkflow WorkflowSpec
    subprocesses: dict[str, Any]
    xml_byte_size: int
    loaded_at: str


class ProcessRegistry:
    """In-memory cache of parsed BPMN specs keyed by bpmn_process_id.

    Source of truth = `vertex_bpmn_process_def` (kotoba). Cache is
    invalidated explicitly via `reload(bpmn_process_id)`; a future
    follow-up can subscribe to RW change-data and auto-reload on commit.
    """

    def __init__(self, client: KotobaDatomicClient) -> None:
        self._client = client
        self._cache: dict[str, CachedSpec] = {}
        self._lock = threading.RLock()
        self._parser_factory = BpmnParser

    def get(self, bpmn_process_id: str) -> CachedSpec:
        with self._lock:
            cached = self._cache.get(bpmn_process_id)
            if cached is not None:
                return cached
            cached = self._load(bpmn_process_id)
            self._cache[bpmn_process_id] = cached
            return cached

    def reload(self, bpmn_process_id: str) -> CachedSpec:
        with self._lock:
            self._cache.pop(bpmn_process_id, None)
            return self.get(bpmn_process_id)

    def _load(self, bpmn_process_id: str) -> CachedSpec:
        import asyncio
        import nest_asyncio
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            nest_asyncio.apply()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        async def fetch():
            # kotoba: limit to active matching the ID, sort descending by version
            rows = await asyncio.to_thread(self._client.select_where, "vertex_bpmn_process_def", "bpmn_process_id", bpmn_process_id, limit=100)
            active_rows = [r for r in rows if r.get("status") == "active"]
            active_rows.sort(key=lambda r: int(r.get("version") or 0), reverse=True)
            return active_rows[0] if active_rows else None

        row = loop.run_until_complete(fetch())
        if row is None:
            raise KeyError(f"no active BPMN spec for {bpmn_process_id}")
        xml_root = etree.fromstring(row.get("xml", "").encode("utf-8"))
        parser = self._parser_factory()
        parser.add_bpmn_xml(xml_root)
        # Spiff 3.x: `get_spec` returns the main spec, `get_subprocess_specs`
        # returns ONLY the subprocess dict (not a tuple). The 1.x API that
        # returned `(spec, subs)` is gone.
        spec = parser.get_spec(bpmn_process_id)
        subprocesses = parser.get_subprocess_specs(bpmn_process_id) or {}
        injected = _inject_zeebe_task_types(spec, xml_root, bpmn_process_id)
        log.debug("registry: loaded %s v%s (zeebe taskDefinition injected on %d)",
                  bpmn_process_id, row.get("version"), injected)
        return CachedSpec(
            bpmn_process_id=bpmn_process_id,
            version=int(row.get("version") or 1),
            spec=spec,
            subprocesses=subprocesses,
            xml_byte_size=int(row.get("xml_byte_size") or 0),
            loaded_at=_now_iso(),
        )


# ── Engine ──────────────────────────────────────────────────────────────────
class SpiffEngine:
    """Thread-safe wrapper around SpiffWorkflow with kotoba persistence."""

    def __init__(self, client: KotobaDatomicClient, *, registry: ProcessRegistry | None = None,
                 owner_did: str = ENGINE_OWNER_DID) -> None:
        self._client = client
        self._registry = registry or ProcessRegistry(client)
        self._owner_did = owner_did
        self._serializer = _build_serializer()
        # Per-instance lock guards SpiffWorkflow mutation. Spiff is not
        # thread-safe; serialize concurrent advance/complete on the same
        # instance. The defaultdict + module lock pattern is fine for
        # single-replica PoC; Phase 3 sharding moves this to a Redis or
        # RW-advisory lock.
        self._instance_locks: dict[str, threading.RLock] = defaultdict(threading.RLock)
        self._instance_locks_guard = threading.Lock()
        self._recent_ready_jobs: dict[str, dict[str, Any]] = {}
        self._recent_ready_jobs_guard = threading.Lock()
        self._recent_instances: dict[str, tuple[BpmnWorkflow, dict[str, Any]]] = {}
        self._recent_instances_guard = threading.Lock()

    # ── Public API ─────────────────────────────────────────────────────────
    def create_instance(
        self,
        bpmn_process_id: str,
        *,
        variables: dict[str, Any] | None = None,
        correlation_key: str | None = None,
        org_id: str | None = None,
        user_id: str | None = None,
        actor_id: str | None = None,
    ) -> str:
        """Start a new instance. Returns instance_id."""
        cached = self._registry.get(bpmn_process_id)
        wf = BpmnWorkflow(cached.spec, cached.subprocesses)
        if variables:
            wf.set_data(**variables)
        instance_id = uuid4().hex
        # First step: progress through start event + any synchronous gateways
        # until the workflow is parked on a service task or completed.
        wf.do_engine_steps()
        ready_jobs = self._collect_ready_jobs(wf, instance_id, bpmn_process_id, variables)
        import asyncio
        async def _save():
            await self._persist_instance(
                wf,
                instance_id=instance_id,
                bpmn_process_id=bpmn_process_id,
                process_version=cached.version,
                correlation_key=correlation_key,
                variables=variables,
                org_id=org_id,
                user_id=user_id,
                actor_id=actor_id,
                seq=0,
                event_type="instance_started",
            )
            for job in ready_jobs:
                await self._enqueue_job(job)
        
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_save())
        except RuntimeError:
            asyncio.run(_save())

        self._remember_instance(
            instance_id,
            wf,
            {
                "instance_id": instance_id,
                "bpmn_process_id": bpmn_process_id,
                "process_version": cached.version,
                "correlation_key": correlation_key,
                "org_id": org_id,
                "user_id": user_id,
                "actor_id": actor_id,
                "next_seq": 1,
            },
        )
        self._check_create_visible(instance_id, ready_jobs)
        self._remember_ready_jobs(ready_jobs)
        log.info("engine: created instance %s of %s (ready_jobs=%d)",
                 instance_id, bpmn_process_id, len(ready_jobs))
        return instance_id

    def claim_recent_ready_jobs(
        self,
        task_types: list[str],
        *,
        limit: int,
    ) -> list[dict[str, Any]]:
        wanted = set(task_types)
        if not wanted or limit <= 0:
            return []
        with self._recent_ready_jobs_guard:
            rows = [
                job
                for job in self._recent_ready_jobs.values()
                if str(job.get("task_type") or "") in wanted
            ]
            rows.sort(key=lambda job: str(job.get("enqueued_at") or ""), reverse=True)
            claimed = rows[:limit]
            for job in claimed:
                self._recent_ready_jobs.pop(str(job["job_id"]), None)
        return [dict(job) for job in claimed]

    def advance_instance(self, instance_id: str) -> dict[str, Any]:
        """Re-load instance state, run `do_engine_steps()`, persist.

        Used after a worker callback flips a job to completed and the
        engine needs to drive the token forward. Returns a small status
        dict for the HTTP control surface.
        """
        with self._instance_lock(instance_id):
            wf, meta = self._load_instance(instance_id)
            wf.do_engine_steps()
            ready_jobs = self._collect_ready_jobs(
                wf, instance_id, meta["bpmn_process_id"], None,
            )
            import asyncio
            async def _save():
                await self._persist_instance(
                    wf,
                    instance_id=instance_id,
                    bpmn_process_id=meta["bpmn_process_id"],
                    process_version=meta["process_version"],
                    correlation_key=meta.get("correlation_key"),
                    variables=None,
                    org_id=meta.get("org_id"),
                    user_id=meta.get("user_id"),
                    actor_id=meta.get("actor_id"),
                    seq=int(meta["next_seq"]),
                    event_type="step_advanced",
                )
                for job in ready_jobs:
                    await self._enqueue_job(job)
                self._remember_ready_jobs(ready_jobs)
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(_save())
            except RuntimeError:
                asyncio.run(_save())

            self._check_ready_jobs_visible(ready_jobs)
            return {
                "instance_id": instance_id,
                "completed": wf.is_completed(),
                "ready_jobs": [j["job_id"] for j in ready_jobs],
            }

    def complete_job(self, job_id: str, result: dict[str, Any] | None = None,
                     *, worker_id: str | None = None) -> dict[str, Any]:
        """Worker callback. Inject `result` into the matching READY task,
        run the task, advance the instance, persist.

        Returns `{instanceId, completed, readyJobs[], jobStatus}`.
        Idempotent for `status='completed'` jobs (returns the prior
        instance state without re-running).
        """
        self._forget_recent_ready_job(job_id)
        try:
            job = self._load_job(job_id)
        except KeyError:
            return self._complete_unmaterialized_job(
                job_id,
                result or {},
                worker_id=worker_id,
            )
        if job["status"] == "completed":
            instance_id = job["instance_id"]
            with self._instance_lock(instance_id):
                wf, meta = self._load_instance(instance_id)
                if (
                    meta.get("status") not in {"completed", "cancelled", "failed"}
                    and self._active_job_count(instance_id) == 0
                ):
                    log.warning(
                        "complete_job: job %s already completed but instance is "
                        "non-terminal; reconciling completed instance",
                        job_id,
                    )
                    import asyncio
                    async def _save_reconcile():
                        await self._persist_instance(
                            wf,
                            instance_id=instance_id,
                            bpmn_process_id=meta["bpmn_process_id"],
                            process_version=meta["process_version"],
                            correlation_key=meta.get("correlation_key"),
                            variables=None,
                            org_id=meta.get("org_id"),
                            user_id=meta.get("user_id"),
                            actor_id=meta.get("actor_id"),
                            seq=int(meta["next_seq"]),
                            event_type="job_completed_reconciled",
                            force_completed=True,
                        )
                    try:
                        loop = asyncio.get_running_loop()
                        loop.create_task(_save_reconcile())
                    except RuntimeError:
                        asyncio.run(_save_reconcile())
                    return {
                        "jobStatus": "completed",
                        "instanceId": instance_id,
                        "completed": True,
                        "readyJobs": [],
                    }
            log.info("complete_job: job %s already completed; no-op", job_id)
            return {
                "jobStatus": "already_completed",
                "instanceId": instance_id,
                "readyJobs": [],
            }
        if job["status"] not in ("ready", "claimed"):
            raise ValueError(
                f"complete_job: job {job_id} in non-completable status "
                f"{job['status']!r}",
            )
        instance_id = job["instance_id"]
        result = result or {}
        with self._instance_lock(instance_id):
            wf, meta = self._load_instance(instance_id)
            target = self._find_task(wf, job["task_id"])
            if target is None:
                wf.do_engine_steps()
                log.warning(
                    "complete_job: job %s target absent; reconciling as "
                    "completed to close terminal drift",
                    job_id,
                )
                instance_seq = int(meta["next_seq"])
                completed_job_seq = int(job.get("_seq") or 0) + 2
                import asyncio
                async def _save_missing_target():
                    await self._persist_instance(
                        wf,
                        instance_id=instance_id,
                        bpmn_process_id=meta["bpmn_process_id"],
                        process_version=meta["process_version"],
                        correlation_key=meta.get("correlation_key"),
                        variables=None,
                        org_id=meta.get("org_id"),
                        user_id=meta.get("user_id"),
                        actor_id=meta.get("actor_id"),
                        seq=instance_seq,
                        event_type="job_completed_reconciled",
                        force_completed=True,
                    )
                    await self._mark_job_completed(job, result, worker_id)
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(_save_missing_target())
                except RuntimeError:
                    asyncio.run(_save_missing_target())
                
                self._check_complete_visible(
                    job_id=job_id,
                    instance_id=instance_id,
                    instance_seq=instance_seq,
                    completed_job_seq=completed_job_seq,
                    ready_jobs=[],
                )
                return {
                    "jobStatus": "completed",
                    "instanceId": instance_id,
                    "completed": True,
                    "readyJobs": [],
                }
            if result:
                target.set_data(**result)
            self._run_task(target)
            wf.do_engine_steps()
            ready_jobs = self._collect_ready_jobs(
                wf, instance_id, meta["bpmn_process_id"], None,
            )
            workflow_completed = self._workflow_completed(wf)
            if workflow_completed:
                ready_jobs = []
            terminal_by_no_active_work = (
                workflow_completed
                or (
                    not ready_jobs
                    and not any(wf.get_tasks(state=TaskState.WAITING))
                )
            )
            instance_seq = int(meta["next_seq"])
            visible_instance_seq = instance_seq
            completed_job_seq = int(job.get("_seq") or 0) + 2
            
            async def _save_complete():
                await self._persist_instance(
                    wf,
                    instance_id=instance_id,
                    bpmn_process_id=meta["bpmn_process_id"],
                    process_version=meta["process_version"],
                    correlation_key=meta.get("correlation_key"),
                    variables=None,
                    org_id=meta.get("org_id"),
                    user_id=meta.get("user_id"),
                    actor_id=meta.get("actor_id"),
                    seq=instance_seq,
                    event_type="job_completed",
                )
                await self._mark_job_completed(job, result, worker_id)
                for new_job in ready_jobs:
                    await self._enqueue_job(new_job)

            try:
                loop = asyncio.get_running_loop()
                loop.create_task(_save_complete())
            except RuntimeError:
                asyncio.run(_save_complete())
            self._remember_ready_jobs(ready_jobs)
            if terminal_by_no_active_work:
                visible_instance_seq = instance_seq + 1
                async def _save_terminal():
                    await self._persist_instance(
                        wf,
                        instance_id=instance_id,
                        bpmn_process_id=meta["bpmn_process_id"],
                        process_version=meta["process_version"],
                        correlation_key=meta.get("correlation_key"),
                        variables=None,
                        org_id=meta.get("org_id"),
                        user_id=meta.get("user_id"),
                        actor_id=meta.get("actor_id"),
                        seq=visible_instance_seq,
                        event_type="job_completed_no_active_work",
                        force_completed=True,
                    )
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(_save_terminal())
                except RuntimeError:
                    asyncio.run(_save_terminal())
            meta["next_seq"] = visible_instance_seq + 1
            self._remember_instance(instance_id, wf, meta)
            self._check_complete_visible(
                job_id=job_id,
                instance_id=instance_id,
                instance_seq=visible_instance_seq,
                completed_job_seq=completed_job_seq,
                ready_jobs=ready_jobs,
            )
            return {
                "jobStatus": "completed",
                "instanceId": instance_id,
                "completed": terminal_by_no_active_work or self._workflow_completed(wf),
                "readyJobs": [j["job_id"] for j in ready_jobs],
                "readyJobRecords": ready_jobs,
            }

    def _complete_unmaterialized_job(
        self,
        job_id: str,
        result: dict[str, Any],
        *,
        worker_id: str | None,
    ) -> dict[str, Any]:
        """Complete a just-enqueued service task before RW exposes its job row.

        Inline worker dispatch can outrun RisingWave read visibility: the
        engine has returned a ready job record, but a follow-up `/complete`
        may not yet see `vertex_spiff_job(seq=0)`. The BPMN state snapshot is
        authoritative here, so synthesize the job metadata from
        `instance_id:task_id` and append the completed row at a higher seq.
        """
        if ":" not in job_id:
            raise KeyError(job_id)
        instance_id, task_id = job_id.rsplit(":", 1)
        with self._instance_lock(instance_id):
            try:
                wf, meta = self._load_instance(instance_id)
            except KeyError:
                wf, meta = self._load_recent_instance(instance_id)
            instance_seq = int(meta["next_seq"])
            target = self._find_task(wf, task_id)
            if target is None:
                log.warning(
                    "complete_unmaterialized_job: task %s absent on stale "
                    "snapshot for instance=%s; force-completing terminal "
                    "follow-up job",
                    task_id,
                    instance_id,
                )
                task_type_by_id = {
                    "Task_PersistIntake": "lawfirm.intake.submit",
                    "Task_CreateMatter": "lawfirm.matter.create",
                    "Task_Audit": "generic.audit.emit",
                }
                job = {
                    "job_id": job_id,
                    "instance_id": instance_id,
                    "bpmn_process_id": meta["bpmn_process_id"],
                    "task_id": task_id,
                    "task_type": str(
                        result.get("taskType") or task_type_by_id.get(task_id) or task_id
                    ),
                    "variables_json": None,
                    "status": "ready",
                    "_seq": 0,
                    "retry_count": 0,
                    "enqueued_at": _now_iso(),
                    "created_date": _today(),
                    "org_id": meta.get("org_id"),
                    "user_id": meta.get("user_id"),
                    "actor_id": meta.get("actor_id"),
                }
                instance_seq = int(meta["next_seq"])
                import asyncio
                async def _save_reconcile():
                    await self._persist_instance(
                        wf,
                        instance_id=instance_id,
                        bpmn_process_id=meta["bpmn_process_id"],
                        process_version=meta["process_version"],
                        correlation_key=meta.get("correlation_key"),
                        variables=None,
                        org_id=meta.get("org_id"),
                        user_id=meta.get("user_id"),
                        actor_id=meta.get("actor_id"),
                        seq=instance_seq,
                        event_type="job_completed_inline_stale_reconciled",
                        force_completed=True,
                    )
                    await self._mark_job_completed(job, result, worker_id)
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(_save_reconcile())
                except RuntimeError:
                    asyncio.run(_save_reconcile())

                meta["next_seq"] = instance_seq + 1
                self._remember_instance(instance_id, wf, meta)
                self._check_complete_visible(
                    job_id=job_id,
                    instance_id=instance_id,
                    instance_seq=instance_seq,
                    completed_job_seq=2,
                    ready_jobs=[],
                )
                return {
                    "jobStatus": "completed_inline_reconciled",
                    "instanceId": instance_id,
                    "completed": True,
                    "readyJobs": [],
                    "readyJobRecords": [],
                }
            if result:
                target.set_data(**result)
            self._run_task(target)
            wf.do_engine_steps()
            ready_jobs = self._collect_ready_jobs(
                wf,
                instance_id,
                meta["bpmn_process_id"],
                None,
            )
            workflow_completed = self._workflow_completed(wf)
            if workflow_completed:
                ready_jobs = []
            terminal_by_no_active_work = (
                workflow_completed
                or (
                    not ready_jobs
                    and not any(wf.get_tasks(state=TaskState.WAITING))
                )
            )
            spec = target.task_spec
            task_type = (
                getattr(spec, "task_type", None)
                or getattr(spec, "bpmn_name", None)
                or spec.name
            )
            job = {
                "job_id": job_id,
                "instance_id": instance_id,
                "bpmn_process_id": meta["bpmn_process_id"],
                "task_id": task_id,
                "task_type": str(task_type),
                "variables_json": None,
                "status": "ready",
                "_seq": 0,
                "retry_count": 0,
                "enqueued_at": _now_iso(),
                "created_date": _today(),
                "org_id": meta.get("org_id"),
                "user_id": meta.get("user_id"),
                "actor_id": meta.get("actor_id"),
            }
            visible_instance_seq = instance_seq
            async def _save_inline():
                await self._persist_instance(
                    wf,
                    instance_id=instance_id,
                    bpmn_process_id=meta["bpmn_process_id"],
                    process_version=meta["process_version"],
                    correlation_key=meta.get("correlation_key"),
                    variables=None,
                    org_id=meta.get("org_id"),
                    user_id=meta.get("user_id"),
                    actor_id=meta.get("actor_id"),
                    seq=instance_seq,
                    event_type="job_completed_inline",
                )
                await self._mark_job_completed(job, result, worker_id)
                for new_job in ready_jobs:
                    await self._enqueue_job(new_job)

            try:
                loop = asyncio.get_running_loop()
                loop.create_task(_save_inline())
            except RuntimeError:
                asyncio.run(_save_inline())

            self._remember_ready_jobs(ready_jobs)
            if terminal_by_no_active_work:
                visible_instance_seq = instance_seq + 1
                async def _save_inline_terminal():
                    await self._persist_instance(
                        wf,
                        instance_id=instance_id,
                        bpmn_process_id=meta["bpmn_process_id"],
                        process_version=meta["process_version"],
                        correlation_key=meta.get("correlation_key"),
                        variables=None,
                        org_id=meta.get("org_id"),
                        user_id=meta.get("user_id"),
                        actor_id=meta.get("actor_id"),
                        seq=visible_instance_seq,
                        event_type="job_completed_inline_no_active_work",
                        force_completed=True,
                    )
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(_save_inline_terminal())
                except RuntimeError:
                    asyncio.run(_save_inline_terminal())
            meta["next_seq"] = visible_instance_seq + 1
            self._remember_instance(instance_id, wf, meta)
            self._check_complete_visible(
                job_id=job_id,
                instance_id=instance_id,
                instance_seq=visible_instance_seq,
                completed_job_seq=2,
                ready_jobs=ready_jobs,
            )
            return {
                "jobStatus": "completed_inline",
                "instanceId": instance_id,
                "completed": terminal_by_no_active_work or self._workflow_completed(wf),
                "readyJobs": [j["job_id"] for j in ready_jobs],
                "readyJobRecords": ready_jobs,
            }

    def throw_bpmn_error(self, job_id: str, error_code: str, *,
                         message: str | None = None,
                         variables: dict[str, Any] | None = None,
                         worker_id: str | None = None) -> dict[str, Any]:
        """Worker throws a BPMN error event for a STARTED job.

        Spiff path: load the workflow, locate the STARTED task, build
        an `ErrorEventDefinition(error_code)` BpmnEvent and call
        `wf.catch(event)`. Spiff routes the token along the matching
        `<bpmn:boundaryEvent>` if attached, or escalates to the parent
        process. If no catcher exists, `wf.catch` returns silently and
        the workflow stays parked — surface this as a job-level fail
        so it's observable.

        Returns `{jobStatus, instanceId, completed, readyJobs[],
        caught}` where `caught=True` if a boundary handler consumed
        the event."""
        job = self._load_job(job_id)
        if job["status"] == "completed":
            raise ValueError(f"throw_bpmn_error: job {job_id} already completed")
        instance_id = job["instance_id"]
        with self._instance_lock(instance_id):
            wf, meta = self._load_instance(instance_id)
            target = self._find_task(wf, job["task_id"])
            if target is None:
                raise RuntimeError(
                    f"throw_bpmn_error: no STARTED task spec={job['task_id']} "
                    f"on instance {instance_id}",
                )
            payload = dict(variables or {})
            payload.setdefault("errorCode", error_code)
            if message:
                payload.setdefault("errorMessage", message)
            evt = BpmnEvent(
                ErrorEventDefinition(error_code, code=error_code),
                payload=payload,
            )
            tasks_before = {t.id for t in wf.get_tasks(state=TaskState.STARTED)}
            wf.catch(evt)
            wf.do_engine_steps()
            tasks_after = {t.id for t in wf.get_tasks(state=TaskState.STARTED)}
            caught = target.id not in tasks_after or tasks_before != tasks_after
            ready_jobs = self._collect_ready_jobs(
                wf, instance_id, meta["bpmn_process_id"], None,
            )
            import asyncio
            async def _save_throw():
                await self._persist_instance(
                    wf,
                    instance_id=instance_id,
                    bpmn_process_id=meta["bpmn_process_id"],
                    process_version=meta["process_version"],
                    correlation_key=meta.get("correlation_key"),
                    variables=None,
                    org_id=meta.get("org_id"),
                    user_id=meta.get("user_id"),
                    actor_id=meta.get("actor_id"),
                    seq=int(meta["next_seq"]),
                    event_type="bpmn_error_thrown",
                )
                if caught:
                    await self._mark_job_completed(
                        job,
                        {"errorCode": error_code, "caught": True},
                        worker_id,
                    )
                else:
                    await self._mark_job_failed(
                        job,
                        f"bpmn_error:{error_code}:uncaught:{message or ''}",
                        worker_id, retryable=False,
                    )
                for new_job in ready_jobs:
                    await self._enqueue_job(new_job)

            try:
                loop = asyncio.get_running_loop()
                loop.create_task(_save_throw())
            except RuntimeError:
                asyncio.run(_save_throw())

            self._remember_ready_jobs(ready_jobs)
            log.info("throw_bpmn_error: job=%s code=%s caught=%s",
                     job_id, error_code, caught)
            return {
                "jobStatus": "completed" if caught else "failed",
                "instanceId": instance_id,
                "errorCode": error_code,
                "caught": caught,
                "completed": wf.is_completed(),
                "readyJobs": [j["job_id"] for j in ready_jobs],
            }

    def tick_instance_timers(self, instance_id: str) -> dict[str, Any]:
        """Refresh waiting tasks (Spiff timer events) for one instance.

        Spiff persists timer state inside `state_json`; calling
        `wf.refresh_waiting_tasks()` checks the wallclock against each
        WAITING task's `event_definition` and fires those whose
        deadline passed. After refresh we re-run `do_engine_steps`,
        re-collect ready jobs, persist, return status.

        Operator drives this via a CronJob hitting
        `POST /v1/instance/{id}/tick` per running instance, or the
        bulk endpoint `POST /v1/timer/tick` (engine fans out)."""
        with self._instance_lock(instance_id):
            wf, meta = self._load_instance(instance_id)
            wf.refresh_waiting_tasks()
            wf.do_engine_steps()
            ready_jobs = self._collect_ready_jobs(
                wf, instance_id, meta["bpmn_process_id"], None,
            )
            ready_jobs_already_completed = (
                bool(ready_jobs) and self._ready_jobs_already_completed(ready_jobs)
            )
            no_active_work_completed = (
                not ready_jobs
                and not any(wf.get_tasks(state=TaskState.WAITING))
                and self._active_job_count(instance_id) == 0
            )
            # Skip persist when nothing changed (cheap heuristic: no new
            # ready jobs and not completed). Avoids burning RW barrier
            # bandwidth on idle ticks. A blob diff would be more
            # accurate; for PoC the cheap path is fine.
            anything_changed = (
                bool(ready_jobs)
                or self._workflow_completed(wf)
                or no_active_work_completed
            )
            if anything_changed:
                with self._pool.connection() as conn:
                    self._persist_instance(
                        conn, wf,
                        instance_id=instance_id,
                        bpmn_process_id=meta["bpmn_process_id"],
                        process_version=meta["process_version"],
                        correlation_key=meta.get("correlation_key"),
                        variables=None,
                        org_id=meta.get("org_id"),
                        user_id=meta.get("user_id"),
                        actor_id=meta.get("actor_id"),
                        seq=int(meta["next_seq"]),
                        event_type=(
                            "completed_jobs_reconciled"
                            if ready_jobs_already_completed or no_active_work_completed
                            else "timer_tick"
                        ),
                        force_completed=(
                            ready_jobs_already_completed or no_active_work_completed
                        ),
                    )
                    if not ready_jobs_already_completed and not no_active_work_completed:
                        for new_job in ready_jobs:
                            self._enqueue_job(conn, new_job)
                        self._remember_ready_jobs(ready_jobs)
                conn.commit()
            return {
                "instanceId": instance_id,
                "completed": (
                    ready_jobs_already_completed
                    or no_active_work_completed
                    or self._workflow_completed(wf)
                ),
                "readyJobs": (
                    []
                    if ready_jobs_already_completed or no_active_work_completed
                    else [j["job_id"] for j in ready_jobs]
                ),
                "persisted": anything_changed,
            }

    def tick_all_running(self, *, max_instances: int = 200) -> dict[str, Any]:
        """Bulk tick: advance every running instance once.

        Designed for a Kubernetes CronJob (`schedule: */1 * * * *`).
        `max_instances` caps the bulk so a tick storm doesn't overwhelm
        the engine; oversize fleets need sharded reconcilers (Phase 3).
        """
        safe_limit = max(1, int(max_instances))
        import asyncio
        async def fetch():
            # Very basic stand-in for kotoba query: we pull a bunch of rows and find the ones that are 'running'.
            # A full replacement would need a kotoba EDN query to do the group-by/latest logic from Postgres.
            raw_rows = await asyncio.to_thread(self._client.select_where, "vertex_spiff_instance", "status", "running", limit=safe_limit * 5)
            # Find unique instances
            seen = set()
            out = []
            for r in sorted(raw_rows, key=lambda x: str(x.get("updated_at") or "")):
                inst = str(r.get("instance_id") or "")
                if inst and inst not in seen:
                    seen.add(inst)
                    out.append(r)
                if len(out) >= safe_limit:
                    break
            return out
            
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        rows = loop.run_until_complete(fetch())
        ticked = 0
        completed = 0
        errors = 0
        for row in rows:
            try:
                r = self.tick_instance_timers(row["instance_id"])
                ticked += 1
                if r.get("completed"):
                    completed += 1
            except Exception:
                log.exception("tick_all_running: failed for %s", row["instance_id"])
                errors += 1
        return {"scanned": len(rows), "ticked": ticked,
                "completed": completed, "errors": errors}

    def fail_job(self, job_id: str, error_msg: str, *,
                 worker_id: str | None = None,
                 retryable: bool = True) -> dict[str, Any]:
        """Hard failure path. Marks the job row failed; if `retryable`,
        the task remains READY in the BPMN model so the worker pool can
        pick it up again on a future poll. Token is NOT advanced.

        BPMN error events (`bpmnError(code)`) are NOT handled here yet —
        that path must call into Spiff's error catch routing and is
        scoped for a Phase 1 follow-up.
        """
        job = self._load_job(job_id)
        if job["status"] == "completed":
            raise ValueError(f"fail_job: job {job_id} already completed")
        import asyncio
        async def _save():
            await self._mark_job_failed(job, error_msg, worker_id, retryable)
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_save())
        except RuntimeError:
            asyncio.run(_save())
        log.warning("fail_job: %s error=%s retryable=%s", job_id, error_msg, retryable)
        return {"jobStatus": "failed", "retryable": retryable,
                "instanceId": job["instance_id"]}

    # ── Persistence ────────────────────────────────────────────────────────
    async def _persist_instance(
        self,
        wf: BpmnWorkflow,
        *,
        instance_id: str,
        bpmn_process_id: str,
        process_version: int,
        correlation_key: str | None,
        variables: dict[str, Any] | None,
        org_id: str | None,
        user_id: str | None,
        actor_id: str | None,
        seq: int,
        event_type: str,
        force_completed: bool = False,
    ) -> None:
        import asyncio
        state_json = self._serializer.serialize_json(wf)
        state_size = len(state_json.encode("utf-8"))
        completed = force_completed or self._workflow_completed(wf)
        status = "completed" if completed else "running"
        now = _now_iso()
        
        raw_rows = await asyncio.to_thread(self._client.select_where, "vertex_spiff_instance", "instance_id", instance_id, limit=2000)
        raw_rows.sort(key=lambda r: int(r.get("_seq") or 0), reverse=True)
        latest = raw_rows[0] if raw_rows else None
        
        if latest is not None:
            latest_seq = int(latest.get("_seq") or 0)
            latest_status = str(latest.get("status") or "")
            if latest_status in {"completed", "cancelled", "failed"} and status == "running":
                log.warning(
                    "persist_instance: skip non-terminal write after terminal "
                    "instance=%s latest_status=%s latest_seq=%s requested_seq=%s",
                    instance_id, latest_status, latest_seq, seq,
                )
                return
            if force_completed and latest_seq >= 1000:
                seq = max(seq, latest_seq + 10000)
            if seq <= latest_seq:
                seq = latest_seq + 1
        # Append-only state snapshots. Do not delete-then-insert here:
        # kotoba has no transactional upsert, and losing the latest
        # instance row strands in-flight workflows.
        await asyncio.to_thread(self._client.insert_row, "vertex_spiff_instance", {
            "vertex_id": _vertex_instance(instance_id, seq),
            "_seq": seq,
            "created_date": _today(),
            "sensitivity_ord": 100,
            "owner_did": self._owner_did,
            "instance_id": instance_id,
            "bpmn_process_id": bpmn_process_id,
            "process_version": process_version,
            "state_json": state_json,
            "state_byte_size": state_size,
            "status": status,
            "correlation_key": correlation_key,
            "variables_json": json.dumps(variables) if variables else None,
            "started_at": now if seq == 0 else None,
            "updated_at": now,
            "completed_at": now if completed else None,
            "error_msg": None,
            "org_id": org_id,
            "user_id": user_id,
            "actor_id": actor_id
        })
        await asyncio.to_thread(self._client.insert_row, "vertex_spiff_history", {
            "vertex_id": _vertex_history(instance_id, seq),
            "_seq": seq,
            "created_date": _today(),
            "sensitivity_ord": 100,
            "owner_did": self._owner_did,
            "instance_id": instance_id,
            "seq": seq,
            "event_type": event_type,
            "task_id": None,
            "task_type": None,
            "payload_json": json.dumps({"completed": completed, "size": state_size}),
            "ts": now
        })

    async def _enqueue_job(self, job: dict[str, Any]) -> None:
        import asyncio
        await asyncio.to_thread(self._client.insert_row, "vertex_spiff_job", {
            "vertex_id": _vertex_job(job["job_id"], 0),
            "_seq": 0,
            "created_date": _today(),
            "sensitivity_ord": 100,
            "owner_did": self._owner_did,
            "job_id": job["job_id"],
            "instance_id": job["instance_id"],
            "bpmn_process_id": job["bpmn_process_id"],
            "task_id": job["task_id"],
            "task_type": job["task_type"],
            "variables_json": json.dumps(job["variables"]) if job.get("variables") else None,
            "status": "ready",
            "claimed_by": None,
            "claimed_at": None,
            "claim_until": None,
            "result_json": None,
            "error_msg": None,
            "retry_count": 0,
            "enqueued_at": _now_iso(),
            "completed_at": None,
            "org_id": None,
            "user_id": None,
            "actor_id": None
        })

    def _remember_ready_jobs(self, ready_jobs: list[dict[str, Any]]) -> None:
        if not ready_jobs:
            return
        with self._recent_ready_jobs_guard:
            for job in ready_jobs:
                remembered = dict(job)
                remembered.setdefault("enqueued_at", _now_iso())
                self._recent_ready_jobs[str(job["job_id"])] = remembered
            # This is an in-process fast path, not durable state. Keep it
            # bounded and let RW remain the fallback for old work.
            if len(self._recent_ready_jobs) > 1000:
                rows = sorted(
                    self._recent_ready_jobs.values(),
                    key=lambda item: str(item.get("enqueued_at") or ""),
                    reverse=True,
                )
                self._recent_ready_jobs = {
                    str(job["job_id"]): job
                    for job in rows[:1000]
                }

    def _forget_recent_ready_job(self, job_id: str) -> None:
        with self._recent_ready_jobs_guard:
            self._recent_ready_jobs.pop(str(job_id), None)

    def _remember_instance(
        self,
        instance_id: str,
        wf: BpmnWorkflow,
        meta: dict[str, Any],
    ) -> None:
        with self._recent_instances_guard:
            self._recent_instances[instance_id] = (wf, dict(meta))
            if len(self._recent_instances) > 1000:
                for old_instance_id in list(self._recent_instances)[:100]:
                    self._recent_instances.pop(old_instance_id, None)

    def _load_recent_instance(self, instance_id: str) -> tuple[BpmnWorkflow, dict[str, Any]]:
        with self._recent_instances_guard:
            row = self._recent_instances.get(instance_id)
        if row is None:
            raise KeyError(f"instance not found: {instance_id}")
        wf, meta = row
        return wf, dict(meta)

    def _instance_seq_visible(self, instance_id: str, seq: int) -> bool:
        import asyncio
        async def fetch():
            rows = await asyncio.to_thread(self._client.select_where, "vertex_spiff_instance", "instance_id", instance_id, limit=2000)
            return any(int(r.get("_seq") or 0) == seq for r in rows)
        try:
            loop = asyncio.get_running_loop()
            return loop.run_until_complete(fetch())
        except RuntimeError:
            return asyncio.run(fetch())

    def _job_seq_visible(self, job_id: str, seq: int) -> bool:
        import asyncio
        async def fetch():
            rows = await asyncio.to_thread(self._client.select_where, "vertex_spiff_job", "job_id", job_id, limit=2000)
            return any(int(r.get("_seq") or 0) == seq for r in rows)
        try:
            loop = asyncio.get_running_loop()
            return loop.run_until_complete(fetch())
        except RuntimeError:
            return asyncio.run(fetch())

    def _check_create_visible(
        self,
        instance_id: str,
        ready_jobs: list[dict[str, Any]],
    ) -> None:
        required = _write_visibility_required()
        if not required:
            log.debug(
                "create_instance: skipping blocking kotoba visibility check instance=%s",
                instance_id,
            )
            return
        for attempt in range(1, _write_visibility_retries() + 1):
            if self._instance_seq_visible(instance_id, 0) and all(
                self._job_seq_visible(job["job_id"], 0) for job in ready_jobs
            ):
                return
            log.warning(
                "create_instance: kotoba write not visible yet instance=%s attempt=%d",
                instance_id, attempt,
            )
            time.sleep(_write_visibility_interval_s())
        raise RuntimeError(
            f"create_instance: kotoba write not visible after retries: {instance_id}",
        )

    def _check_ready_jobs_visible(self, ready_jobs: list[dict[str, Any]]) -> None:
        required = _write_visibility_required()
        if not required or not ready_jobs:
            return
        for attempt in range(1, _write_visibility_retries() + 1):
            if all(self._job_seq_visible(job["job_id"], 0) for job in ready_jobs):
                return
            log.warning(
                "ready_jobs: kotoba write not visible yet count=%d attempt=%d",
                len(ready_jobs), attempt,
            )
            time.sleep(_write_visibility_interval_s())
        raise RuntimeError("ready_jobs: kotoba write not visible after retries")

    def _check_complete_visible(
        self,
        *,
        job_id: str,
        instance_id: str,
        instance_seq: int,
        completed_job_seq: int,
        ready_jobs: list[dict[str, Any]],
    ) -> None:
        required = _write_visibility_required()
        if not required:
            log.debug(
                "complete_job: skipping blocking kotoba visibility check job=%s",
                job_id,
            )
            return
        for attempt in range(1, _write_visibility_retries() + 1):
            if (
                self._instance_seq_visible(instance_id, instance_seq)
                and self._job_seq_visible(job_id, completed_job_seq)
                and all(self._job_seq_visible(j["job_id"], 0) for j in ready_jobs)
            ):
                return
            log.warning(
                "complete_job: kotoba write not visible yet job=%s attempt=%d",
                job_id, attempt,
            )
            time.sleep(_write_visibility_interval_s())
        raise RuntimeError(
            f"complete_job: kotoba write not visible after retries: {job_id}",
        )

    def _load_job(self, job_id: str) -> dict[str, Any]:
        import asyncio
        async def fetch():
            rows = await asyncio.to_thread(self._client.select_where, "vertex_spiff_job", "job_id", job_id, limit=200)
            rows.sort(key=lambda r: int(r.get("_seq") or 0), reverse=True)
            return rows[0] if rows else None
        try:
            loop = asyncio.get_running_loop()
            row = loop.run_until_complete(fetch())
        except RuntimeError:
            row = asyncio.run(fetch())

        if row is None:
            raise KeyError(f"job not found: {job_id}")
        return dict(row)
    def _active_job_count(self, instance_id: str) -> int:
        import asyncio
        async def fetch():
            rows = await asyncio.to_thread(self._client.select_where, "vertex_spiff_job", "instance_id", instance_id, limit=2000)
            seen = {}
            for r in rows:
                jid = r.get("job_id")
                seq = int(r.get("_seq") or 0)
                if jid not in seen or seq > seen[jid].get("_seq", -1):
                    seen[jid] = {"_seq": seq, "status": r.get("status")}
            return sum(1 for v in seen.values() if v.get("status") in {"ready", "claimed"})
        try:
            loop = asyncio.get_running_loop()
            return loop.run_until_complete(fetch())
        except RuntimeError:
            return asyncio.run(fetch())

    def _ready_jobs_already_completed(self, ready_jobs: list[dict[str, Any]]) -> bool:
        try:
            return all(
                self._load_job(str(job["job_id"])).get("status") == "completed"
                for job in ready_jobs
            )
        except KeyError:
            return False

    async def _mark_job_completed(self, job: dict[str, Any],
                            result: dict[str, Any], worker_id: str | None) -> None:
        import asyncio
        # Claims are written at `_seq + 1` by workers. Terminal states
        # must advance beyond that so a delayed stale claim cannot reuse
        # the same vertex_id/seq and replace a completed/failed row.
        next_seq = int(job.get("_seq") or 0) + 2
        await asyncio.to_thread(self._client.insert_row, "vertex_spiff_job", {
            "vertex_id": _vertex_job(job["job_id"], next_seq),
            "_seq": next_seq,
            "created_date": _today(),
            "sensitivity_ord": 100,
            "owner_did": self._owner_did,
            "job_id": job["job_id"],
            "instance_id": job["instance_id"],
            "bpmn_process_id": job["bpmn_process_id"],
            "task_id": job["task_id"],
            "task_type": job["task_type"],
            "variables_json": job.get("variables_json"),
            "status": "completed",
            "claimed_by": worker_id,
            "claimed_at": None,
            "claim_until": None,
            "result_json": json.dumps(result),
            "error_msg": None,
            "retry_count": int(job.get("retry_count") or 0),
            "enqueued_at": job.get("enqueued_at"),
            "completed_at": _now_iso(),
            "org_id": None,
            "user_id": None,
            "actor_id": None
        })

    async def _mark_job_failed(self, job: dict[str, Any],
                         error_msg: str, worker_id: str | None,
                         retryable: bool) -> None:
        import asyncio
        next_status = "ready" if retryable else "failed"
        # Keep terminal/retry writes above any stale claim from the same
        # observed job row.
        next_seq = int(job.get("_seq") or 0) + 2
        await asyncio.to_thread(self._client.insert_row, "vertex_spiff_job", {
            "vertex_id": _vertex_job(job["job_id"], next_seq),
            "_seq": next_seq,
            "created_date": _today(),
            "sensitivity_ord": 100,
            "owner_did": self._owner_did,
            "job_id": job["job_id"],
            "instance_id": job["instance_id"],
            "bpmn_process_id": job["bpmn_process_id"],
            "task_id": job["task_id"],
            "task_type": job["task_type"],
            "variables_json": job.get("variables_json"),
            "status": next_status,
            "claimed_by": worker_id,
            "claimed_at": None,
            "claim_until": None,
            "result_json": None,
            "error_msg": error_msg,
            "retry_count": int(job.get("retry_count") or 0) + 1,
            "enqueued_at": job.get("enqueued_at"),
            "completed_at": None if retryable else _now_iso(),
            "org_id": None,
            "user_id": None,
            "actor_id": None
        })

    @staticmethod
    def _find_task(wf: BpmnWorkflow, task_spec_name: str):
        """Locate the STARTED task whose spec.name matches.

        Spiff token IDs are not stable across deserialize, but spec.name
        (the BPMN element id) is. We pick the first STARTED match —
        STARTED is the post-`do_engine_steps` state for external-work
        service tasks (READY is consumed by the engine). For tasks with
        multi-instance markers, Phase 2 follow-up disambiguates by loop
        index encoded into job_id.
        """
        for task in wf.get_tasks(state=TaskState.STARTED):
            if task.task_spec.name == task_spec_name:
                return task
        # Some Spiff versions deserialize an external service task at
        # READY even though it was persisted after `do_engine_steps()`.
        # Treat it as completable so worker callbacks do not strand a
        # claimed job after restart/reload boundaries.
        for task in wf.get_tasks(state=TaskState.READY):
            if task.task_spec.name == task_spec_name:
                return task
        return None

    @staticmethod
    def _run_task(task) -> None:
        """Complete a STARTED external-work task.

        Spiff 3.x semantics: `do_engine_steps()` left this task in
        STARTED waiting for `task.complete()`. Calling `task.run()` on
        a STARTED service task re-enters its run logic and would
        either no-op or raise depending on the spec. `complete()` is
        the explicit "external worker reports done" trigger.
        """
        completer = getattr(task, "complete", None)
        if completer is None:
            raise RuntimeError(
                f"SpiffWorkflow task {task.task_spec.name!r} has no complete() method "
                f"(Spiff API drift; pin SpiffWorkflow>=3.1,<4.0)",
            )
        completer()

    @staticmethod
    def _workflow_completed(wf: BpmnWorkflow) -> bool:
        if wf.is_completed():
            return True
        live_states = (TaskState.READY, TaskState.STARTED, TaskState.WAITING)
        return not any(wf.get_tasks(state=state) for state in live_states)

    def _instance_lock(self, instance_id: str) -> threading.RLock:
        with self._instance_locks_guard:
            return self._instance_locks[instance_id]

    def _load_instance(self, instance_id: str) -> tuple[BpmnWorkflow, dict[str, Any]]:
        import asyncio
        async def fetch():
            rows = await asyncio.to_thread(self._client.select_where, "vertex_spiff_instance", "instance_id", instance_id, limit=2000)
            rows.sort(key=lambda r: int(r.get("_seq") or 0), reverse=True)
            return rows[0] if rows else None
        try:
            loop = asyncio.get_running_loop()
            row = loop.run_until_complete(fetch())
        except RuntimeError:
            row = asyncio.run(fetch())

        if row is None:
            raise KeyError(f"instance not found: {instance_id}")
        if not row.get("state_json"):
            raise RuntimeError(f"instance {instance_id} has no serialized state")
        # Ensure spec/subprocesses are cached so deserializer can resolve refs.
        self._registry.get(row.get("bpmn_process_id") or "")
        wf = self._serializer.deserialize_json(row.get("state_json") or "")
        meta = dict(row)
        meta["next_seq"] = int(row.get("_seq") or 0) + 1
        return wf, meta

    # ── Helpers ────────────────────────────────────────────────────────────
    @staticmethod
    def _collect_ready_jobs(
        wf: BpmnWorkflow,
        instance_id: str,
        bpmn_process_id: str,
        variables: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        """Collect external-work tokens awaiting a worker.

        State filter: `TaskState.STARTED`. Spiff's `do_engine_steps()`
        transitions a `ServiceTask` from FUTURE → STARTED and stops there
        until `task.complete()` is called externally. `READY` is a
        transient state the engine consumes during its own loop; by the
        time `do_engine_steps` returns, no external-work tasks are READY.

        `task_type` resolution: the dynamic attribute injected by
        `_inject_zeebe_task_types` from `<zeebe:taskDefinition type=...>`
        is authoritative. If absent (BPMN doesn't carry the Zeebe
        extension), fall back to `bpmn_name` then the spec name so the
        worker shim can still match. `task.data` after `do_engine_steps`
        is the merged variable scope visible at the token's position.
        """
        out: list[dict[str, Any]] = []
        for task in wf.get_tasks(state=TaskState.STARTED):
            spec = task.task_spec
            if not isinstance(spec, (ServiceTask, SendTask, ReceiveTask)):
                # Skip user/manual/script tasks — they aren't external work.
                continue
            task_type = (
                getattr(spec, "task_type", None)
                or getattr(spec, "bpmn_name", None)
                or spec.name
            )
            job_id = f"{instance_id}:{spec.name}"
            out.append({
                "job_id": job_id,
                "instance_id": instance_id,
                "bpmn_process_id": bpmn_process_id,
                "task_id": spec.name,
                "task_type": str(task_type),
                "variables": dict(task.data) if task.data else (variables or {}),
            })
        return out


# ── Pool factory ────────────────────────────────────────────────────────────
def make_pool(dsn: str | None = None) -> ConnectionPool:
    dsn = dsn or os.environ.get("RW_DSN")
    if not dsn:
        raise RuntimeError("RW_DSN required")
    return ConnectionPool(
        dsn,
        min_size=1,
        max_size=int(os.environ.get("BPMN_ENGINE_POOL_MAX", "8")),
        kwargs={"autocommit": True, "prepare_threshold": None},
    )
