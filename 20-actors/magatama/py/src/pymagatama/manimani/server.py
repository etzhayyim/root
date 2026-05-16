"""Granian / FastAPI entrypoint for the manimani LangGraph actor
(ADR-2605080600 + ADR-2605080800 Phase 2).

Run with::

    granian --interface asgi pymagatama.manimani.server:app \
            --host 0.0.0.0 --port 8000 --workers 1

The Helm chart ``mitama-manimani-pool`` provides this command line.

Endpoints:

  - ``POST /runs``                          submit an ingest run
  - ``GET  /runs/{run_id}``                 poll status / artifacts
  - ``GET  /health`` / ``/_app/meta``       probes
  - ``POST /xrpc/ai.gftd.apps.manimani.{ingest,classify,process}``
  - ``GET  /xrpc/ai.gftd.apps.manimani.{getProject,listProjects,coverage}``

bpmn-dispatcher (ADR-2604282300) routes ``ai.gftd.apps.manimani.*`` to
this service via in-cluster ClusterIP
``manimani-langgraph.mitama-udf.svc.cluster.local:8000``.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import time
from typing import Any, Optional

try:
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.responses import JSONResponse
except ImportError:  # pragma: no cover
    FastAPI = None  # type: ignore[assignment]


from pymagatama.manimani.graph import (
    _build_artifact,
    _make_project_did,
    _make_project_vertex_id,
    build_graph,
)
from pymagatama.manimani.persistence import (
    coverage_snapshot,
    demote_primary_edges_for_intake,
    get_intake_by_vertex_id,
    get_project_by_slug,
    get_project_by_vertex_id,
    get_run_record,
    insert_artifacts,
    insert_belongs_to_edge,
    insert_intake,
    insert_project,
    insert_run,
    list_active_intake_count_for_projects,
    list_artifacts_for_project,
    list_pending_runs,
    list_projects_for_actor,
    update_run_status,
)
from pymagatama.manimani.processors import (
    PROCESSOR_BY_KIND,
    PROCESSOR_DEFAULT_TIER,
    defer_for_user_review,
    expand_todo,
    extract_facts,
    summarize,
)
from pymagatama.manimani.state import (
    ArtifactKind,
    IngestInput,
    ManimaniState,
    ProjectKind,
    SourceKind,
)


PROCESSOR_FN: dict[str, Any] = {
    "extract_facts": extract_facts,
    "expand_todo": expand_todo,
    "summarize": summarize,
    "defer_for_user_review": defer_for_user_review,
}


def _utc_now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _make_intake_vertex_id(actor_did: str, ts_ms: int, intake_hash: str) -> str:
    digest = hashlib.sha256(f"{actor_did}|{ts_ms}|{intake_hash}".encode("utf-8")).hexdigest()
    return f"at://{actor_did}/ai.gftd.apps.manimani.intake/{digest[:16]}"


def _make_run_id(intake_vertex_id: str, salt: str = "") -> str:
    seed = f"{intake_vertex_id}|{salt}" if salt else intake_vertex_id
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:32]


def _make_run_vertex_id(actor_did: str, run_id: str) -> str:
    return f"at://{actor_did}/ai.gftd.apps.manimani.run/{run_id[:16]}"


def _estimate_seconds(kind: SourceKind) -> int:
    if kind is SourceKind.TEXT:
        return 3
    if kind is SourceKind.URL:
        return 8
    return 12  # file_ref


def _resolve_checkpointer() -> Any:
    """Lazy-construct the RisingWave-backed BaseCheckpointSaver.

    Disabled when ``MANIMANI_CHECKPOINTER=off`` (smoke tests / dry-run)
    or when the langgraph_checkpoint_rw module is unavailable. Otherwise
    a process-level singleton is reused across requests so the graph
    stays single-instantiated.
    """

    if os.environ.get("MANIMANI_CHECKPOINTER", "").strip().lower() == "off":
        return None
    if os.environ.get("GFTD_MANIMANI_DRY_RUN") == "1":
        return None
    try:  # pragma: no cover — module is present in the runtime image
        from pymagatama.langgraph_checkpoint_rw import RisingWaveCheckpointSaver
    except Exception:
        return None
    try:
        return RisingWaveCheckpointSaver()
    except Exception:
        return None


def build_app() -> Any:
    if FastAPI is None:  # pragma: no cover
        raise RuntimeError("fastapi not installed")
    api = FastAPI(title="manimani-langgraph", version="0.3.0")
    checkpointer = _resolve_checkpointer()
    graph = build_graph(checkpointer=checkpointer)
    runs: dict[str, dict[str, Any]] = {}

    def _internal_trust_ok(req: Request) -> bool:
        if os.environ.get("GFTD_MANIMANI_DEV") == "1":
            return True
        return bool(req.headers.get("x-internal-trust"))

    def _resolve_caller(req: Request) -> tuple[str, str]:
        actor = (
            req.headers.get("x-gftd-actor-did")
            or os.environ.get("GFTD_DEV_ACTOR_DID", "did:web:manimani.gftd.ai")
        )
        org = (
            req.headers.get("x-gftd-org-did")
            or os.environ.get("GFTD_DEV_ORG_DID", "did:erc725:gftd:260425:dev")
        )
        return actor, org

    @api.get("/health")
    async def health() -> dict[str, Any]:
        return {"ok": True, "app": "manimani-langgraph", "ts": _utc_now_iso()}

    @api.get("/_app/meta")
    async def meta() -> dict[str, Any]:
        return {
            "app": "manimani-langgraph",
            "did": "did:web:manimani.gftd.ai",
            "layer": "L3-execution",
            "runtime": "langgraph-server+granian",
            "graph_nodes": [
                "parse_input",
                "classify_project",
                "await_human_review",
                "route_processor",
                "extract_facts",
                "expand_todo",
                "summarize",
                "defer_for_user_review",
                "persist_artifact",
                "emit_audit",
            ],
            "phase": os.environ.get("MANIMANI_PHASE", "7"),
            "classifier": os.environ.get("MANIMANI_CLASSIFIER", "llm"),
            "checkpointer": "rw" if checkpointer is not None else "off",
            "hitl_new_project": os.environ.get("MANIMANI_HITL_NEW_PROJECT", "0"),
            "federable": False,
        }

    def _unwrap_envelope(body: dict) -> tuple[dict, str | None, str | None]:
        if not isinstance(body, dict):
            return {}, None, None
        looks_like_envelope = (
            isinstance(body.get("input"), dict) or "assistant_id" in body
        )
        if looks_like_envelope:
            return (
                body.get("input") or {},
                body.get("actor_did") or body.get("actorDid"),
                body.get("thread_id") or body.get("threadId"),
            )
        return body, None, None

    async def _start_run(input_payload: dict, actor_did: str, org_did: str) -> dict[str, Any]:
        ingest_input = IngestInput.model_validate(input_payload)
        ts_ms = int(time.time() * 1000)

        body_for_hash = (
            ingest_input.raw_text
            or ingest_input.source_uri
            or json.dumps(input_payload, sort_keys=True)
        )
        intake_hash = hashlib.sha256(body_for_hash.encode("utf-8")).hexdigest()
        intake_vertex_id = _make_intake_vertex_id(actor_did, ts_ms, intake_hash)
        run_id = _make_run_id(intake_vertex_id)
        run_vertex_id = _make_run_vertex_id(actor_did, run_id)
        started_at = _utc_now_iso()

        insert_intake(
            intake_vertex_id=intake_vertex_id,
            source_kind=ingest_input.source_kind.value,
            raw_text=ingest_input.raw_text,
            source_uri=ingest_input.source_uri,
            parsed_text=None,
            lang=ingest_input.lang,
            sensitivity_ord=ingest_input.sensitivity_ord,
            byte_size=None,
            ts_ms=ts_ms,
            actor_did=actor_did,
            org_did=org_did,
        )
        insert_run(
            run_vertex_id=run_vertex_id,
            run_id=run_id,
            intake_vertex_id=intake_vertex_id,
            project_vertex_id=None,
            status="running",
            started_at=started_at,
            actor_did=actor_did,
            org_did=org_did,
        )

        state = ManimaniState(
            input=ingest_input,
            actor_did=actor_did,
            org_did=org_did,
            intake_vertex_id=intake_vertex_id,
            run_id=run_id,
            started_at=started_at,
        )
        runs[run_id] = {
            "status": "running",
            "intakeId": intake_vertex_id,
            "projectId": None,
            "startedAt": started_at,
            "currentNode": "parse_input",
            "artifacts": [],
            "errorText": None,
        }

        async def _run() -> None:
            try:
                final_state: Any = None
                # thread_id keys the BaseCheckpointSaver checkpoint chain
                # (one row per node transition in vertex_langgraph_checkpoint).
                run_config = {
                    "configurable": {
                        "thread_id": run_id,
                        "checkpoint_ns": "manimani",
                    }
                }
                async for ev in graph.astream(
                    state.model_dump(), config=run_config, stream_mode="values",
                ):
                    final_state = ev
                    if isinstance(ev, dict) and ev.get("current_node"):
                        runs[run_id]["currentNode"] = ev["current_node"]
                    if isinstance(ev, dict) and ev.get("error_text"):
                        runs[run_id]["errorText"] = ev["error_text"]
                if final_state and isinstance(final_state, dict):
                    runs[run_id]["projectId"] = final_state.get("project_vertex_id")
                    runs[run_id]["artifacts"] = [
                        a if isinstance(a, dict) else a.model_dump(mode="json")  # type: ignore[union-attr]
                        for a in (final_state.get("artifacts") or [])
                    ]
                    if final_state.get("awaiting_human_review"):
                        # HITL gate fired (Phase 4). The run is paused;
                        # caller must invoke resumeRun. We carry the
                        # classifier proposal so the resume side can
                        # surface it to the user.
                        runs[run_id]["status"] = "interrupted"
                        cls = final_state.get("classification") or {}
                        if hasattr(cls, "model_dump"):
                            cls = cls.model_dump(mode="json")  # type: ignore[union-attr]
                        runs[run_id]["pendingClassification"] = cls
                        runs[run_id]["finishedAt"] = None
                    else:
                        runs[run_id]["finishedAt"] = _utc_now_iso()
                        if runs[run_id].get("errorText"):
                            runs[run_id]["status"] = "completed_with_error"
                        else:
                            runs[run_id]["status"] = "completed"
            except Exception as exc:  # pragma: no cover — defense in depth
                runs[run_id]["status"] = "failed"
                runs[run_id]["errorText"] = f"{type(exc).__name__}: {exc}"
                runs[run_id]["finishedAt"] = _utc_now_iso()
            finally:
                # Phase 5: persist terminal run state into vertex_manimani_run
                # so cross-pod GET /runs/{id} + resumeRun can recover it.
                _persist_run_terminal(run_id, run_vertex_id, runs[run_id], actor_did, org_did)

        asyncio.create_task(_run())

        return {
            "run_id": run_id,
            "thread_id": run_id,
            "status": "running",
            "runId": run_id,
            "intakeId": intake_vertex_id,
            "estimatedSeconds": _estimate_seconds(ingest_input.source_kind),
        }

    # ── native LangGraph-style endpoints ────────────────────────────

    @api.post("/runs")
    async def post_run(req: Request) -> JSONResponse:
        if not _internal_trust_ok(req):
            raise HTTPException(status_code=401, detail="x-internal-trust required")
        body = await req.json()

        # bpmn-dispatcher always POSTs to /runs with `{assistant_id, input,
        # actor_did?, thread_id?, config?}`. We route by assistant_id to the
        # correct handler — queries (coverage / listProjects / getProject /
        # listPendingRuns) are dispatched here even though they're "queries"
        # in the lexicon, because the dispatcher has no NSID→handler map.
        assistant = ""
        if isinstance(body, dict):
            assistant = str(body.get("assistant_id") or body.get("assistantId") or "")
        ingest_payload, env_actor, _env_thread = _unwrap_envelope(body or {})
        header_actor, header_org = _resolve_caller(req)
        actor_did = env_actor or header_actor
        org_did = header_org
        params = (
            (ingest_payload if isinstance(ingest_payload, dict) else {}) or {}
        )

        # Read-only dispatch table. The handlers here are inlined copies of
        # the same logic the /xrpc/* bridge exposes, so the response shape
        # matches whichever path the caller takes.
        if assistant == "manimani_coverage":
            try:
                window_days = max(1, min(int(params.get("windowDays", 7)), 90))
            except (TypeError, ValueError):
                window_days = 7
            snap = coverage_snapshot(
                actor_did=actor_did, org_did=org_did, window_days=window_days,
            )
            snap["windowDays"] = window_days
            return JSONResponse(snap)

        if assistant == "manimani_list_projects":
            status_filter = params.get("status")
            kind_filter = params.get("kind")
            try:
                limit = max(1, min(int(params.get("limit", 50)), 200))
            except (TypeError, ValueError):
                limit = 50
            projects = list_projects_for_actor(
                actor_did=actor_did, org_did=org_did,
                status=status_filter, kind=kind_filter, limit=limit,
            )
            active_counts = list_active_intake_count_for_projects(
                actor_did=actor_did, org_did=org_did,
            )
            out_rows: list[dict[str, Any]] = []
            for p in projects:
                row = _project_to_camel(p)
                row["intakeCount30d"] = int(
                    active_counts.get(str(p.get("vertex_id") or ""), 0)
                )
                out_rows.append(row)
            return JSONResponse({"projects": out_rows})

        if assistant == "manimani_get_project":
            project_id = params.get("projectId")
            slug = params.get("slug")
            try:
                limit = max(1, min(int(params.get("limit", 50)), 200))
            except (TypeError, ValueError):
                limit = 50
            if (project_id and slug) or (not project_id and not slug):
                raise HTTPException(
                    status_code=400,
                    detail="Pass exactly one of: projectId, slug",
                )
            if project_id:
                project = get_project_by_vertex_id(
                    actor_did=actor_did, org_did=org_did, vertex_id=str(project_id),
                )
            else:
                project = get_project_by_slug(
                    actor_did=actor_did, org_did=org_did, slug=str(slug),
                )
            if project is None:
                raise HTTPException(status_code=404, detail="project not found")
            artifacts = list_artifacts_for_project(
                actor_did=actor_did, org_did=org_did,
                project_vertex_id=str(project.get("vertex_id") or ""),
                limit=limit,
            )
            return JSONResponse(
                {
                    "project": _project_to_camel(project),
                    "artifacts": [_artifact_row_to_camel(a) for a in artifacts],
                }
            )

        if assistant == "manimani_list_pending_runs":
            try:
                limit = max(1, min(int(params.get("limit", 25)), 100))
            except (TypeError, ValueError):
                limit = 25
            rows = list_pending_runs(
                actor_did=actor_did, org_did=org_did, limit=limit,
            )
            out_rows = []
            for row in rows:
                run_id = str(row.get("run_id") or "")
                entry: dict[str, Any] = {
                    "runId": run_id,
                    "intakeId": row.get("intake_vertex_id"),
                    "status": row.get("status"),
                    "startedAt": row.get("started_at"),
                    "currentNode": row.get("current_node"),
                }
                if checkpointer is not None and run_id:
                    try:
                        cfg = {
                            "configurable": {
                                "thread_id": run_id,
                                "checkpoint_ns": "manimani",
                            }
                        }
                        tup = await checkpointer.aget_tuple(cfg)
                        if tup is not None:
                            cp = getattr(tup, "checkpoint", None) or {}
                            channel_values = (cp.get("channel_values") if isinstance(cp, dict) else None) or {}
                            cls = channel_values.get("classification")
                            if cls:
                                if hasattr(cls, "model_dump"):
                                    cls = cls.model_dump(mode="json")
                                entry["pendingClassification"] = cls
                    except Exception:
                        pass
                out_rows.append(entry)
            return JSONResponse({"runs": out_rows})

        # Default — treat as ingest. assistant_id == 'manimani_ingest' or any
        # other unknown procedure falls through to the LangGraph StateGraph
        # entry path. Phase 8 will wire classify / process / resumeRun
        # explicitly when those XRPCs gain non-ingest semantics.
        return JSONResponse(await _start_run(ingest_payload, actor_did, org_did))

    @api.get("/runs/{run_id}")
    async def get_run(run_id: str, req: Request) -> JSONResponse:
        if not _internal_trust_ok(req):
            raise HTTPException(status_code=401, detail="x-internal-trust required")
        rec = runs.get(run_id)
        if rec:
            return JSONResponse(_run_record_response(run_id, rec))
        # Phase 5: cross-pod fallback. The run row was written by another
        # pod; recover from RW. Pending classification (if interrupted)
        # is recovered from the LangGraph checkpoint chain.
        actor_did, org_did = _resolve_caller(req)
        rec_remote = await _load_run_cross_pod(run_id, actor_did, org_did, checkpointer)
        if rec_remote is None:
            raise HTTPException(status_code=404, detail="NotFound")
        return JSONResponse(_run_record_response(run_id, rec_remote))

    # ── XRPC: ingest ────────────────────────────────────────────────

    @api.post("/xrpc/ai.gftd.apps.manimani.ingest")
    async def xrpc_ingest(req: Request) -> JSONResponse:
        if not _internal_trust_ok(req):
            raise HTTPException(status_code=401, detail="x-internal-trust required")
        body = await req.json()
        ingest_payload, env_actor, _env_thread = _unwrap_envelope(body or {})
        header_actor, header_org = _resolve_caller(req)
        actor_did = env_actor or header_actor
        org_did = header_org
        return JSONResponse(await _start_run(ingest_payload, actor_did, org_did))

    # ── XRPC: classify (re-classification) ──────────────────────────

    @api.post("/xrpc/ai.gftd.apps.manimani.classify")
    async def xrpc_classify(req: Request) -> JSONResponse:
        if not _internal_trust_ok(req):
            raise HTTPException(status_code=401, detail="x-internal-trust required")
        body, env_actor, _ = _unwrap_envelope(await req.json() or {})
        header_actor, header_org = _resolve_caller(req)
        actor_did = env_actor or header_actor
        org_did = header_org

        intake_id = str(body.get("intakeId") or "").strip()
        if not intake_id:
            raise HTTPException(status_code=400, detail="intakeId required")

        target_id = body.get("targetProjectId")
        new_project = body.get("newProject")
        if (target_id and new_project) or (not target_id and not new_project):
            raise HTTPException(
                status_code=400,
                detail="Pass exactly one of: targetProjectId, newProject",
            )

        # Verify intake exists in actor scope.
        intake = get_intake_by_vertex_id(
            actor_did=actor_did, org_did=org_did, vertex_id=intake_id,
        )
        if intake is None and not _dry_run_mode():
            raise HTTPException(status_code=404, detail="intake not found in actor scope")

        # Resolve target project (existing or new).
        if target_id:
            project = get_project_by_vertex_id(
                actor_did=actor_did, org_did=org_did, vertex_id=str(target_id),
            )
            if project is None and not _dry_run_mode():
                raise HTTPException(status_code=404, detail="targetProjectId not found")
            project_vertex_id = str(target_id)
        else:
            np = new_project if isinstance(new_project, dict) else {}
            slug = str(np.get("slug") or "").strip().lower()
            title = str(np.get("title") or "").strip()
            kind_raw = str(np.get("kind") or "unsorted").strip().lower()
            tags_csv = np.get("initialTagsCsv") or np.get("initial_tags_csv")
            if not slug or not title:
                raise HTTPException(status_code=400, detail="newProject.slug + .title required")
            try:
                kind_enum = ProjectKind(kind_raw)
            except ValueError:
                kind_enum = ProjectKind.UNSORTED

            existing = get_project_by_slug(
                actor_did=actor_did, org_did=org_did, slug=slug,
            )
            if existing:
                project_vertex_id = str(existing.get("vertex_id") or "")
            else:
                project_vertex_id = _make_project_vertex_id(actor_did, slug)
                insert_project(
                    project_vertex_id=project_vertex_id,
                    project_did=_make_project_did(slug),
                    slug=slug,
                    title=title,
                    kind=kind_enum.value,
                    initial_tags_csv=str(tags_csv) if tags_csv else None,
                    ts_ms=int(time.time() * 1000),
                    actor_did=actor_did,
                    org_did=org_did,
                )

        # Demote prior primary edges + insert new primary edge.
        demoted = demote_primary_edges_for_intake(
            intake_vertex_id=intake_id,
            actor_did=actor_did,
            org_did=org_did,
        )
        edge_id = insert_belongs_to_edge(
            intake_vertex_id=intake_id,
            project_vertex_id=project_vertex_id,
            confidence=1.0,  # user-driven manual classification
            is_primary=True,
            classification_method="manual_user",
            actor_did=actor_did,
            org_did=org_did,
        )
        return JSONResponse(
            {
                "intakeId": intake_id,
                "projectId": project_vertex_id,
                "edgeId": edge_id,
                "demoted": demoted,
            }
        )

    # ── XRPC: resumeRun (HITL Phase 4) ──────────────────────────────

    @api.post("/xrpc/ai.gftd.apps.manimani.resumeRun")
    async def xrpc_resume_run(req: Request) -> JSONResponse:
        if not _internal_trust_ok(req):
            raise HTTPException(status_code=401, detail="x-internal-trust required")
        body, env_actor, _ = _unwrap_envelope(await req.json() or {})
        header_actor, header_org = _resolve_caller(req)
        actor_did = env_actor or header_actor
        org_did = header_org

        original_run_id = str(body.get("runId") or "").strip()
        decision = str(body.get("decision") or "").strip().lower()
        target_project_id = body.get("targetProjectId") or body.get("target_project_id")

        if not original_run_id:
            raise HTTPException(status_code=400, detail="runId required")
        if decision not in ("approve", "reject", "reassign"):
            raise HTTPException(status_code=400, detail="decision must be approve|reject|reassign")
        if decision == "reassign" and not target_project_id:
            raise HTTPException(status_code=400, detail="decision=reassign requires targetProjectId")

        prev = runs.get(original_run_id)
        if prev is None:
            # Phase 5 cross-pod path: rehydrate from RW + checkpoint chain.
            prev = await _load_run_cross_pod(
                original_run_id, actor_did, org_did, checkpointer,
            )
        if prev is None:
            raise HTTPException(status_code=404, detail="paused run not found")
        if prev.get("status") != "interrupted":
            raise HTTPException(status_code=409, detail=f"run not interrupted (status={prev.get('status')})")

        intake_id = str(prev.get("intakeId") or "")
        intake = get_intake_by_vertex_id(
            actor_did=actor_did, org_did=org_did, vertex_id=intake_id,
        )
        if intake is None and not _dry_run_mode():
            raise HTTPException(status_code=404, detail="paused run's intake not found")
        intake = intake or {}

        ts_ms = int(time.time() * 1000)
        new_run_id = _make_run_id(intake_id, salt=f"resume|{decision}|{ts_ms}")
        new_run_vertex_id = _make_run_vertex_id(actor_did, new_run_id)
        started_at = _utc_now_iso()

        insert_run(
            run_vertex_id=new_run_vertex_id,
            run_id=new_run_id,
            intake_vertex_id=intake_id,
            project_vertex_id=str(target_project_id) if target_project_id else None,
            status="running",
            started_at=started_at,
            actor_did=actor_did,
            org_did=org_did,
        )

        try:
            ingest_input = IngestInput(
                source_kind=SourceKind(str(intake.get("source_kind") or "text")),
                raw_text=intake.get("raw_text"),
                source_uri=intake.get("source_uri"),
                lang=intake.get("lang"),
                sensitivity_ord=int(intake.get("sensitivity_ord") or 2),
            )
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"failed to rebuild input: {exc}")

        # Carry the prior classification proposal across the resume so
        # the (approve) decision uses the LLM's original suggestion
        # rather than re-running the classifier.
        pending = prev.get("pendingClassification") or {}
        try:
            from pymagatama.manimani.state import ProjectClassification
            classification = (
                ProjectClassification.model_validate(pending) if pending else None
            )
        except Exception:
            classification = None

        state = ManimaniState(
            input=ingest_input,
            actor_did=actor_did,
            org_did=org_did,
            intake_vertex_id=intake_id,
            run_id=new_run_id,
            started_at=started_at,
            classification=classification,
            human_decision=decision,
            human_decision_target_project_id=str(target_project_id) if target_project_id else None,
            parent_run_id=original_run_id,
        )
        runs[new_run_id] = {
            "status": "running",
            "intakeId": intake_id,
            "projectId": str(target_project_id) if target_project_id else None,
            "startedAt": started_at,
            "currentNode": "parse_input",
            "artifacts": [],
            "errorText": None,
            "parentRunId": original_run_id,
        }

        async def _resume() -> None:
            try:
                final_state: Any = None
                run_config = {
                    "configurable": {
                        "thread_id": new_run_id,
                        "checkpoint_ns": "manimani",
                    }
                }
                async for ev in graph.astream(
                    state.model_dump(), config=run_config, stream_mode="values",
                ):
                    final_state = ev
                    if isinstance(ev, dict) and ev.get("current_node"):
                        runs[new_run_id]["currentNode"] = ev["current_node"]
                    if isinstance(ev, dict) and ev.get("error_text"):
                        runs[new_run_id]["errorText"] = ev["error_text"]
                if final_state and isinstance(final_state, dict):
                    runs[new_run_id]["projectId"] = final_state.get("project_vertex_id")
                    runs[new_run_id]["artifacts"] = [
                        a if isinstance(a, dict) else a.model_dump(mode="json")  # type: ignore[union-attr]
                        for a in (final_state.get("artifacts") or [])
                    ]
                    runs[new_run_id]["finishedAt"] = _utc_now_iso()
                    if runs[new_run_id].get("errorText"):
                        runs[new_run_id]["status"] = "completed_with_error"
                    else:
                        runs[new_run_id]["status"] = "completed"
                # Mark the original paused run as superseded.
                runs[original_run_id]["status"] = "completed"
                runs[original_run_id]["resumedAs"] = new_run_id
                runs[original_run_id]["finishedAt"] = _utc_now_iso()
            except Exception as exc:  # pragma: no cover
                runs[new_run_id]["status"] = "failed"
                runs[new_run_id]["errorText"] = f"{type(exc).__name__}: {exc}"
                runs[new_run_id]["finishedAt"] = _utc_now_iso()
            finally:
                _persist_run_terminal(
                    new_run_id, new_run_vertex_id, runs[new_run_id], actor_did, org_did,
                )
                # Persist the original paused run's terminal status too,
                # so cross-pod GET /runs/{original_run_id} reflects the
                # supersession.
                orig_vid = _make_run_vertex_id(actor_did, original_run_id)
                _persist_run_terminal(
                    original_run_id, orig_vid, runs[original_run_id], actor_did, org_did,
                )

        asyncio.create_task(_resume())

        return JSONResponse(
            {
                "runId": new_run_id,
                "originalRunId": original_run_id,
                "status": "running",
                "estimatedSeconds": 4,
            }
        )

    # ── XRPC: process (re-process existing intake) ──────────────────

    @api.post("/xrpc/ai.gftd.apps.manimani.process")
    async def xrpc_process(req: Request) -> JSONResponse:
        if not _internal_trust_ok(req):
            raise HTTPException(status_code=401, detail="x-internal-trust required")
        body, env_actor, _ = _unwrap_envelope(await req.json() or {})
        header_actor, header_org = _resolve_caller(req)
        actor_did = env_actor or header_actor
        org_did = header_org

        intake_id = str(body.get("intakeId") or "").strip()
        if not intake_id:
            raise HTTPException(status_code=400, detail="intakeId required")

        force_processor = body.get("forceProcessor") or body.get("force_processor")
        model_tier = body.get("modelTier") or body.get("model_tier")

        intake = get_intake_by_vertex_id(
            actor_did=actor_did, org_did=org_did, vertex_id=intake_id,
        )
        if intake is None and not _dry_run_mode():
            raise HTTPException(status_code=404, detail="intake not found in actor scope")
        intake = intake or {}

        # Find the intake's current primary project (if any). Phase 2:
        # require an explicit project. If the user wants to process
        # without binding, they can call classify first.
        # Lookup the primary edge from a small helper SELECT.
        project_vertex_id = _find_primary_project_for_intake(
            intake_vertex_id=intake_id,
            actor_did=actor_did, org_did=org_did,
        )
        if project_vertex_id is None and not _dry_run_mode():
            raise HTTPException(
                status_code=409,
                detail="intake has no primary project; call classify first",
            )

        project = (
            get_project_by_vertex_id(
                actor_did=actor_did, org_did=org_did, vertex_id=project_vertex_id or "",
            )
            if project_vertex_id
            else None
        )
        try:
            project_kind = ProjectKind(str((project or {}).get("kind") or "unsorted"))
        except ValueError:
            project_kind = ProjectKind.UNSORTED

        # Resolve processor.
        if force_processor:
            processor = str(force_processor).strip()
        else:
            processor = PROCESSOR_BY_KIND.get(project_kind.value, "defer_for_user_review")
        fn = PROCESSOR_FN.get(processor)
        if fn is None:
            raise HTTPException(status_code=400, detail=f"unknown processor: {processor}")

        tier = (model_tier or PROCESSOR_DEFAULT_TIER.get(processor, "fast")).strip()
        if tier:
            os.environ.setdefault("MANIMANI_PROCESSOR_TIER_FACTS", tier) if processor == "extract_facts" else None

        # New run id (stable per intake + processor + tier + ts_ms).
        ts_ms = int(time.time() * 1000)
        run_id = _make_run_id(intake_id, salt=f"{processor}|{tier}|{ts_ms}")
        run_vertex_id = _make_run_vertex_id(actor_did, run_id)
        started_at = _utc_now_iso()
        insert_run(
            run_vertex_id=run_vertex_id,
            run_id=run_id,
            intake_vertex_id=intake_id,
            project_vertex_id=project_vertex_id,
            status="running",
            started_at=started_at,
            actor_did=actor_did,
            org_did=org_did,
        )
        runs[run_id] = {
            "status": "running",
            "intakeId": intake_id,
            "projectId": project_vertex_id,
            "startedAt": started_at,
            "currentNode": processor,
            "artifacts": [],
            "errorText": None,
        }

        parsed = str(intake.get("parsed_text") or intake.get("raw_text") or intake.get("source_uri") or "")

        async def _reprocess() -> None:
            try:
                out = fn(
                    parsed_text=parsed,
                    project_meta={
                        "project_vertex_id": project_vertex_id,
                        "project_kind": project_kind.value,
                    },
                    actor_did=actor_did,
                )
                # Build a synthetic state purely to get _build_artifact's signature.
                synth_state = ManimaniState(
                    input=IngestInput(
                        source_kind=SourceKind(str(intake.get("source_kind") or "text")),
                        raw_text=intake.get("raw_text"),
                        source_uri=intake.get("source_uri"),
                    ),
                    actor_did=actor_did,
                    org_did=org_did,
                    intake_vertex_id=intake_id,
                    run_id=run_id,
                    started_at=started_at,
                    parsed_text=parsed,
                    project_vertex_id=project_vertex_id,
                    project_kind=project_kind,
                    processor=processor,
                )
                artifact = _build_artifact(synth_state, out)
                insert_artifacts(
                    artifacts=[artifact], actor_did=actor_did, org_did=org_did,
                )
                runs[run_id]["artifacts"] = [artifact.model_dump(mode="json")]
                runs[run_id]["currentNode"] = "persist_artifact"
                runs[run_id]["finishedAt"] = _utc_now_iso()
                runs[run_id]["status"] = (
                    "completed_with_error" if out.get("error_text") else "completed"
                )
                runs[run_id]["errorText"] = out.get("error_text")
            except Exception as exc:  # pragma: no cover
                runs[run_id]["status"] = "failed"
                runs[run_id]["errorText"] = f"{type(exc).__name__}: {exc}"
                runs[run_id]["finishedAt"] = _utc_now_iso()
            finally:
                _persist_run_terminal(run_id, run_vertex_id, runs[run_id], actor_did, org_did)

        asyncio.create_task(_reprocess())

        return JSONResponse(
            {
                "run_id": run_id,
                "thread_id": run_id,
                "status": "running",
                "runId": run_id,
                "intakeId": intake_id,
                "estimatedSeconds": 4 if processor in ("summarize", "defer_for_user_review") else 8,
            }
        )

    # ── XRPC: getProject ────────────────────────────────────────────

    @api.get("/xrpc/ai.gftd.apps.manimani.getProject")
    async def xrpc_get_project(req: Request) -> JSONResponse:
        if not _internal_trust_ok(req):
            raise HTTPException(status_code=401, detail="x-internal-trust required")
        actor_did, org_did = _resolve_caller(req)
        params = req.query_params
        project_id = params.get("projectId")
        slug = params.get("slug")
        try:
            limit = max(1, min(int(params.get("limit", "50")), 200))
        except ValueError:
            limit = 50
        if (project_id and slug) or (not project_id and not slug):
            raise HTTPException(status_code=400, detail="Pass exactly one of: projectId, slug")

        project: dict[str, Any] | None
        if project_id:
            project = get_project_by_vertex_id(
                actor_did=actor_did, org_did=org_did, vertex_id=str(project_id),
            )
        else:
            project = get_project_by_slug(
                actor_did=actor_did, org_did=org_did, slug=str(slug),
            )
        if project is None:
            raise HTTPException(status_code=404, detail="project not found")

        artifacts = list_artifacts_for_project(
            actor_did=actor_did, org_did=org_did,
            project_vertex_id=str(project.get("vertex_id") or ""),
            limit=limit,
        )
        return JSONResponse(
            {
                "project": _project_to_camel(project),
                "artifacts": [_artifact_row_to_camel(a) for a in artifacts],
            }
        )

    # ── XRPC: listProjects ──────────────────────────────────────────

    @api.get("/xrpc/ai.gftd.apps.manimani.listProjects")
    async def xrpc_list_projects(req: Request) -> JSONResponse:
        if not _internal_trust_ok(req):
            raise HTTPException(status_code=401, detail="x-internal-trust required")
        actor_did, org_did = _resolve_caller(req)
        params = req.query_params
        status = params.get("status")
        kind = params.get("kind")
        try:
            limit = max(1, min(int(params.get("limit", "50")), 200))
        except ValueError:
            limit = 50

        projects = list_projects_for_actor(
            actor_did=actor_did, org_did=org_did,
            status=status, kind=kind, limit=limit,
        )
        active_counts = list_active_intake_count_for_projects(
            actor_did=actor_did, org_did=org_did,
        )
        out: list[dict[str, Any]] = []
        for p in projects:
            row = _project_to_camel(p)
            row["intakeCount30d"] = int(
                active_counts.get(str(p.get("vertex_id") or ""), 0)
            )
            out.append(row)
        return JSONResponse({"projects": out})

    # ── XRPC: listPendingRuns (Phase 7) ─────────────────────────────

    @api.get("/xrpc/ai.gftd.apps.manimani.listPendingRuns")
    async def xrpc_list_pending_runs(req: Request) -> JSONResponse:
        if not _internal_trust_ok(req):
            raise HTTPException(status_code=401, detail="x-internal-trust required")
        actor_did, org_did = _resolve_caller(req)
        try:
            limit = max(1, min(int(req.query_params.get("limit", "25")), 100))
        except ValueError:
            limit = 25

        rows = list_pending_runs(actor_did=actor_did, org_did=org_did, limit=limit)
        out: list[dict[str, Any]] = []
        for row in rows:
            run_id = str(row.get("run_id") or "")
            entry: dict[str, Any] = {
                "runId": run_id,
                "intakeId": row.get("intake_vertex_id"),
                "status": row.get("status"),
                "startedAt": row.get("started_at"),
                "currentNode": row.get("current_node"),
            }
            # Hydrate pendingClassification from the LangGraph checkpoint
            # chain, exactly like _load_run_cross_pod does for /runs/{id}.
            if checkpointer is not None and run_id:
                try:
                    cfg = {
                        "configurable": {
                            "thread_id": run_id,
                            "checkpoint_ns": "manimani",
                        }
                    }
                    tup = await checkpointer.aget_tuple(cfg)
                    if tup is not None:
                        cp = getattr(tup, "checkpoint", None) or {}
                        channel_values = (cp.get("channel_values") if isinstance(cp, dict) else None) or {}
                        cls = channel_values.get("classification")
                        if cls:
                            if hasattr(cls, "model_dump"):
                                cls = cls.model_dump(mode="json")
                            entry["pendingClassification"] = cls
                except Exception:  # pragma: no cover
                    pass
            out.append(entry)
        return JSONResponse({"runs": out})

    # ── XRPC: coverage ──────────────────────────────────────────────

    @api.get("/xrpc/ai.gftd.apps.manimani.coverage")
    async def xrpc_coverage(req: Request) -> JSONResponse:
        if not _internal_trust_ok(req):
            raise HTTPException(status_code=401, detail="x-internal-trust required")
        actor_did, org_did = _resolve_caller(req)
        try:
            window_days = max(1, min(int(req.query_params.get("windowDays", "7")), 90))
        except ValueError:
            window_days = 7

        snap = coverage_snapshot(
            actor_did=actor_did, org_did=org_did, window_days=window_days,
        )
        snap["windowDays"] = window_days
        return JSONResponse(snap)

    return api


# ── helpers ──────────────────────────────────────────────────────────


def _dry_run_mode() -> bool:
    return os.environ.get("GFTD_MANIMANI_DRY_RUN") == "1"


def _persist_run_terminal(
    run_id: str,
    run_vertex_id: str,
    rec: dict[str, Any],
    actor_did: str,
    org_did: str,
) -> None:
    """Phase 5: write the terminal run state back into vertex_manimani_run.

    Called from the ``finally`` block of every async run loop (start_run,
    resume, reprocess). Best-effort — swallows DB errors to avoid masking
    the underlying graph-loop exception.
    """

    try:
        update_run_status(
            run_vertex_id=run_vertex_id,
            actor_did=actor_did,
            org_did=org_did,
            status=str(rec.get("status") or "running"),
            current_node=rec.get("currentNode"),
            error_text=rec.get("errorText"),
            finished_at=rec.get("finishedAt"),
            project_vertex_id=rec.get("projectId"),
        )
    except Exception:  # pragma: no cover — defense in depth
        pass


async def _load_run_cross_pod(
    run_id: str,
    actor_did: str,
    org_did: str,
    checkpointer: Any,
) -> Optional[dict[str, Any]]:
    """Phase 5: reconstruct a /runs/{run_id}-shaped record from RW.

    Reads the row from ``vertex_manimani_run`` and, when the run is
    interrupted, rehydrates the classifier proposal from the LangGraph
    checkpoint chain (``vertex_langgraph_checkpoint``) keyed by
    ``thread_id == run_id``. Returns None when neither source has the
    run.
    """

    row = get_run_record(run_id=run_id, actor_did=actor_did, org_did=org_did)
    if row is None:
        return None

    rec: dict[str, Any] = {
        "status": str(row.get("status") or "running"),
        "intakeId": str(row.get("intake_vertex_id") or ""),
        "projectId": row.get("project_vertex_id"),
        "startedAt": row.get("started_at"),
        "finishedAt": row.get("finished_at"),
        "currentNode": row.get("current_node"),
        "errorText": row.get("error_text"),
        "artifacts": [],
    }

    # Pending classification — only meaningful when the run paused at
    # the HITL gate. Recover it from the LangGraph checkpoint chain.
    if rec["status"] == "interrupted" and checkpointer is not None:
        try:
            cfg = {
                "configurable": {
                    "thread_id": run_id,
                    "checkpoint_ns": "manimani",
                }
            }
            tup = await checkpointer.aget_tuple(cfg)
            if tup is not None:
                cp = getattr(tup, "checkpoint", None) or {}
                channel_values = (cp.get("channel_values") if isinstance(cp, dict) else None) or {}
                cls = channel_values.get("classification")
                if cls:
                    if hasattr(cls, "model_dump"):
                        cls = cls.model_dump(mode="json")
                    rec["pendingClassification"] = cls
        except Exception:  # pragma: no cover
            pass

    return rec


def _find_primary_project_for_intake(
    *,
    intake_vertex_id: str,
    actor_did: str,
    org_did: str,
) -> str | None:
    """Look up the (singleton) primary project edge for an intake.

    Returns None in dry-run mode and on absence.
    """

    if _dry_run_mode():
        return None
    from pymagatama.manimani.persistence import _dict_query as _dq

    rows = _dq("""
        SELECT dst_vid FROM edge_manimani_belongs_to
         WHERE src_vid = %(intake)s
           AND actor_did = %(actor_did)s
           AND org_did = %(org_did)s
           AND is_primary = true
         LIMIT 1
        """,
        {"intake": intake_vertex_id, "actor_did": actor_did, "org_did": org_did},
    )
    if not rows:
        return None
    return str(rows[0].get("dst_vid") or "") or None


def _project_to_camel(p: dict[str, Any]) -> dict[str, Any]:
    return {
        "vertexId": str(p.get("vertex_id") or ""),
        "projectDid": str(p.get("project_did") or ""),
        "slug": str(p.get("slug") or ""),
        "title": str(p.get("title") or ""),
        "kind": str(p.get("kind") or "unsorted"),
        "initialTagsCsv": p.get("initial_tags_csv"),
        "intakeCount": int(p.get("intake_count") or 0) if p.get("intake_count") is not None else 0,
        "lastIntakeAt": p.get("last_intake_at"),
        "status": str(p.get("status") or "active"),
        "createdAt": p.get("created_at"),
    }


def _artifact_row_to_camel(a: dict[str, Any]) -> dict[str, Any]:
    return {
        "vertexId": str(a.get("vertex_id") or ""),
        "intakeVertexId": str(a.get("intake_vertex_id") or ""),
        "runVertexId": str(a.get("run_vertex_id") or ""),
        "artifactKind": str(a.get("artifact_kind") or "raw_passthrough"),
        "content": a.get("content"),
        "modelId": a.get("model_id"),
        "errorText": a.get("error_text"),
        "createdAt": a.get("created_at"),
    }


def _run_record_response(run_id: str, rec: dict[str, Any]) -> dict[str, Any]:
    return {
        "runId": run_id,
        "intakeId": rec.get("intakeId"),
        "projectId": rec.get("projectId"),
        "status": rec.get("status"),
        "currentNode": rec.get("currentNode"),
        "errorText": rec.get("errorText"),
        "startedAt": rec.get("startedAt"),
        "finishedAt": rec.get("finishedAt"),
        "artifacts": rec.get("artifacts", []),
    }


app = build_app() if FastAPI is not None else None
