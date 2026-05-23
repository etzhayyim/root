"""yatabase QA ReAct graph — smoke test runner.

Runs yatabase-smoke.mjs as a subprocess, parses PASS/FAIL/SKIP output,
optionally calls LLM to analyze failures, and returns a structured QA report.

ReAct loop:
  run_tests → analyze_failures → build_report

NSID: ai.gftd.apps.yata.lg.qaReact.run
Graph ID: qa_react
Triggered: manually or pre-deploy gate
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import time
import uuid
from pathlib import Path
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from lg_yatabase.graphs._llm import call_llm_json

_log = logging.getLogger(__name__)

# Path to smoke.mjs relative to repo root (resolved at runtime).
# Falls back to env var YATA_SMOKE_SCRIPT when run inside a container.
try:
    _SMOKE_SCRIPT = Path(__file__).parents[5] / "70-tools" / "scripts" / "yatabase-smoke.mjs"
except IndexError:
    _SMOKE_SCRIPT = Path(os.environ.get("YATA_SMOKE_SCRIPT", "/opt/smoke/yatabase-smoke.mjs"))

_HOST = os.environ.get("YATABASE_HOST", "https://yatabase.gftd.ai")
_API_KEY = os.environ.get("YATA_API_KEY", "")
_NODE_BIN = os.environ.get("NODE_BIN", "node")
_SMOKE_TIMEOUT = int(os.environ.get("YATA_SMOKE_TIMEOUT_SEC", "600"))


class QAState(TypedDict, total=False):
    run_id: str
    host: str
    api_key: str
    raw_output: str
    test_results: list[dict[str, Any]]
    passed: int
    failed: int
    skipped: int
    analysis: str
    report: dict[str, Any]
    error: str


# ── Nodes ─────────────────────────────────────────────────────────────────────

async def run_tests(state: QAState) -> QAState:
    host = state.get("host") or _HOST
    api_key = state.get("api_key") or _API_KEY
    run_id = state.get("run_id") or str(uuid.uuid4())[:8]

    # Fast-path: caller pre-collected results (e.g. run outside the container).
    if state.get("test_results") is not None:
        results = state["test_results"]
        passed = sum(1 for r in results if r.get("status") == "PASS")
        failed = sum(1 for r in results if r.get("status") == "FAIL")
        skipped = sum(1 for r in results if r.get("status") == "SKIP")
        _log.info("[qa_react][%s] pre-collected: pass=%d fail=%d skip=%d", run_id, passed, failed, skipped)
        return {
            "run_id": run_id,
            "host": host,
            "raw_output": state.get("raw_output", "pre-collected"),
            "test_results": results,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
        }

    env = os.environ.copy()
    env["YATABASE_HOST"] = host
    if api_key:
        env["YATA_API_KEY"] = api_key

    script = str(_SMOKE_SCRIPT)
    _log.info("[qa_react][%s] running smoke: %s host=%s auth=%s", run_id, script, host, bool(api_key))

    try:
        proc = await asyncio.create_subprocess_exec(
            _NODE_BIN, script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            env=env,
        )
        try:
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=_SMOKE_TIMEOUT)
        except asyncio.TimeoutError:
            proc.kill()
            return {
                "run_id": run_id,
                "raw_output": f"TIMEOUT after {_SMOKE_TIMEOUT}s",
                "test_results": [],
                "passed": 0, "failed": 0, "skipped": 0,
                "error": f"smoke script timed out after {_SMOKE_TIMEOUT}s",
            }
        raw = stdout.decode("utf-8", errors="replace")
    except Exception as exc:
        _log.exception("[qa_react][%s] subprocess failed: %s", run_id, exc)
        return {
            "run_id": run_id,
            "raw_output": str(exc),
            "test_results": [],
            "passed": 0, "failed": 0, "skipped": 0,
            "error": str(exc),
        }

    results: list[dict[str, Any]] = []
    for line in raw.splitlines():
        m = re.match(r'^(PASS|FAIL|SKIP)\s+(.+?)(?:\s+—\s+(.+))?$', line)
        if not m:
            continue
        status, name, detail = m.group(1), m.group(2).strip(), (m.group(3) or "").strip()
        results.append({
            "status": status,
            "name": name,
            "detail": detail,
            "ok": status != "FAIL",
            "skipped": status == "SKIP",
        })

    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    skipped = sum(1 for r in results if r["status"] == "SKIP")

    _log.info("[qa_react][%s] smoke done: pass=%d fail=%d skip=%d", run_id, passed, failed, skipped)
    return {
        "run_id": run_id,
        "host": host,
        "raw_output": raw,
        "test_results": results,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
    }


def analyze_failures(state: QAState) -> QAState:
    failures = [r for r in (state.get("test_results") or []) if r["status"] == "FAIL"]
    if not failures:
        return {"analysis": "All tests passed or skipped — no failures to analyze."}

    failure_lines = "\n".join(
        f"FAIL {r['name']}" + (f" — {r['detail']}" if r["detail"] else "")
        for r in failures
    )
    prompt = (
        f"The following yatabase smoke tests failed:\n\n{failure_lines}\n\n"
        "For each failure, briefly state (1) the likely root cause and "
        "(2) the recommended fix. Output JSON: "
        '{\"analyses\": [{\"test\": str, \"root_cause\": str, \"fix\": str}]}'
    )
    parsed, source = call_llm_json(prompt, max_tokens=512)
    if parsed and isinstance(parsed.get("analyses"), list):
        lines = [
            f"• {a['test']}: {a['root_cause']} → {a['fix']}"
            for a in parsed["analyses"]
        ]
        analysis = f"LLM analysis ({source}):\n" + "\n".join(lines)
    else:
        analysis = (
            f"LLM unavailable ({source}). Manual review needed:\n" + failure_lines
        )
    return {"analysis": analysis}


def build_report(state: QAState) -> QAState:
    results = state.get("test_results") or []
    failed_tests = [r for r in results if r["status"] == "FAIL"]
    report = {
        "run_id": state.get("run_id"),
        "host": state.get("host") or _HOST,
        "ts": int(time.time() * 1000),
        "summary": {
            "passed": state.get("passed", 0),
            "failed": state.get("failed", 0),
            "skipped": state.get("skipped", 0),
            "total": len(results),
            "ok": state.get("failed", 0) == 0,
        },
        "failures": [
            {"name": r["name"], "detail": r["detail"]} for r in failed_tests
        ],
        "analysis": state.get("analysis", ""),
        "error": state.get("error", ""),
    }
    _log.info(
        "[qa_react][%s] report: pass=%d fail=%d skip=%d ok=%s",
        state.get("run_id"), report["summary"]["passed"],
        report["summary"]["failed"], report["summary"]["skipped"],
        report["summary"]["ok"],
    )
    return {"report": report}


# ── Graph ─────────────────────────────────────────────────────────────────────

_g: StateGraph = StateGraph(QAState)
_g.add_node("run_tests", run_tests)
_g.add_node("analyze_failures", analyze_failures)
_g.add_node("build_report", build_report)
_g.add_edge(START, "run_tests")
_g.add_edge("run_tests", "analyze_failures")
_g.add_edge("analyze_failures", "build_report")
_g.add_edge("build_report", END)
GRAPH = _g.compile()
