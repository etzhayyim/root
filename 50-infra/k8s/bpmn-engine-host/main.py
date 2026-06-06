"""FastAPI control surface for the SpiffWorkflow engine host.

Cluster-internal HTTP API (`bpmn-engine-host` ClusterIP). Public XRPC
surface (`com.etzhayyim.apps.bpmn.startInstance` etc.) terminates at the
edge Worker and forwards here via Service Binding / fetch.

PoC endpoints implemented:
    GET  /healthz                     liveness
    GET  /readyz                      readiness (kotoba ping)
    POST /v1/instance                 { processId, variables?, correlationKey? }
                                      → { instanceId, completed, readyJobs }
    POST /v1/instance/{id}/advance    re-run do_engine_steps (no-op if blocked)
                                      → { instanceId, completed, readyJobs }
    POST /v1/job/{id}/complete        worker callback to inject result + advance
                                      → { jobStatus, instanceId, completed, readyJobs }
    POST /v1/job/{id}/fail            worker hard-failure (retryable by default)
                                      → { jobStatus, retryable, instanceId }
    POST /v1/job/{id}/throwBpmnError  route token along boundary error event
                                      → { jobStatus, errorCode, caught, instanceId }
    POST /v1/instance/{id}/tick       refresh waiting tasks for one instance
                                      → { instanceId, completed, readyJobs[], persisted }
    POST /v1/timer/tick               bulk: refresh all running instances
                                      → { scanned, ticked, completed, errors }
    POST /v1/process/{id}/reload      drop spec cache for bpmn_process_id

Out of scope (Phase 2):
    POST /v1/instance/{id}/signal     message/signal correlation
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from engine import SpiffEngine
from pymagatama.kotoba_datomic import get_kotoba_client

log = logging.getLogger("bpmn_engine_host")
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = get_kotoba_client()
    engine = SpiffEngine(client)
    app.state.client = client
    app.state.engine = engine
    log.info("bpmn-engine-host: started")
    try:
        yield
    finally:
        log.info("bpmn-engine-host: stopped")


app = FastAPI(title="bpmn-engine-host", lifespan=lifespan)


class CreateInstanceReq(BaseModel):
    processId: str
    variables: dict[str, Any] | None = None
    correlationKey: str | None = None
    orgId: str | None = None
    userId: str | None = None
    actorId: str | None = None


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz")
def readyz() -> dict[str, Any]:
    try:
        client = get_kotoba_client()
        # Ping the datomic client
        client.q('[:find ?e :where [?e :db/ident :db/ident]]')
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(503, detail=f"kotoba not reachable: {exc!r}") from exc
    return {"status": "ready"}


@app.post("/v1/instance")
def create_instance(req: CreateInstanceReq) -> dict[str, Any]:
    engine: SpiffEngine = app.state.engine
    try:
        instance_id = engine.create_instance(
            req.processId,
            variables=req.variables,
            correlation_key=req.correlationKey,
            org_id=req.orgId,
            user_id=req.userId,
            actor_id=req.actorId,
        )
    except KeyError as exc:
        raise HTTPException(404, detail=str(exc)) from exc
    return {"instanceId": instance_id}


@app.post("/v1/instance/{instance_id}/advance")
def advance_instance(instance_id: str) -> dict[str, Any]:
    engine: SpiffEngine = app.state.engine
    try:
        return engine.advance_instance(instance_id)
    except KeyError as exc:
        raise HTTPException(404, detail=str(exc)) from exc


class CompleteJobReq(BaseModel):
    result: dict[str, Any] | None = None
    workerId: str | None = None


class RecentReadyReq(BaseModel):
    taskTypes: list[str]
    limit: int = 100


@app.post("/v1/jobs/recent-ready")
def recent_ready_jobs(req: RecentReadyReq) -> dict[str, Any]:
    engine: SpiffEngine = app.state.engine
    return {
        "jobs": engine.claim_recent_ready_jobs(
            req.taskTypes,
            limit=max(1, min(int(req.limit), 500)),
        ),
    }


class FailJobReq(BaseModel):
    errorMsg: str
    workerId: str | None = None
    retryable: bool = True


@app.post("/v1/job/{job_id}/complete")
def complete_job(job_id: str, req: CompleteJobReq) -> dict[str, Any]:
    engine: SpiffEngine = app.state.engine
    try:
        return engine.complete_job(job_id, req.result, worker_id=req.workerId)
    except KeyError as exc:
        raise HTTPException(404, detail=str(exc)) from exc
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(409, detail=str(exc)) from exc


@app.post("/v1/job/{job_id}/fail")
def fail_job(job_id: str, req: FailJobReq) -> dict[str, Any]:
    engine: SpiffEngine = app.state.engine
    try:
        return engine.fail_job(
            job_id, req.errorMsg,
            worker_id=req.workerId, retryable=req.retryable,
        )
    except KeyError as exc:
        raise HTTPException(404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(409, detail=str(exc)) from exc


class ThrowBpmnErrorReq(BaseModel):
    errorCode: str
    message: str | None = None
    variables: dict[str, Any] | None = None
    workerId: str | None = None


@app.post("/v1/job/{job_id}/throwBpmnError")
def throw_bpmn_error(job_id: str, req: ThrowBpmnErrorReq) -> dict[str, Any]:
    engine: SpiffEngine = app.state.engine
    try:
        return engine.throw_bpmn_error(
            job_id, req.errorCode,
            message=req.message,
            variables=req.variables,
            worker_id=req.workerId,
        )
    except KeyError as exc:
        raise HTTPException(404, detail=str(exc)) from exc
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(409, detail=str(exc)) from exc


@app.post("/v1/instance/{instance_id}/tick")
def tick_instance(instance_id: str) -> dict[str, Any]:
    """Refresh waiting tasks (timer events) for one instance and persist."""
    engine: SpiffEngine = app.state.engine
    try:
        return engine.tick_instance_timers(instance_id)
    except KeyError as exc:
        raise HTTPException(404, detail=str(exc)) from exc


@app.post("/v1/timer/tick")
def tick_all_running(max_instances: int = 200) -> dict[str, Any]:
    """Bulk tick — drives every running instance forward by one timer
    refresh + engine step. Operator drives this from a Kubernetes
    CronJob (`schedule: */1 * * * *`)."""
    engine: SpiffEngine = app.state.engine
    return engine.tick_all_running(max_instances=max_instances)


@app.post("/v1/process/{process_id}/reload")
def reload_process(process_id: str) -> dict[str, Any]:
    engine: SpiffEngine = app.state.engine
    cached = engine._registry.reload(process_id)  # noqa: SLF001 — admin path
    return {
        "processId": cached.bpmn_process_id,
        "version": cached.version,
        "xmlByteSize": cached.xml_byte_size,
        "loadedAt": cached.loaded_at,
    }
