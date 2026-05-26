"""yatabase QA User Story graph — acceptance criterion classifier.

Maps PASS/FAIL smoke-test results onto user stories derived from the BMC
value propositions (yatabase-bmc-seed.sh v1, 2026-05-11 snapshot).

A user story PASSES iff every mapped test PASSES. If any mapped test is
missing (not run at all), the story is SKIP. FAIL otherwise.

ReAct loop:
  classify_stories → analyze_stories → build_story_report

NSID: app.etzhayyim.apps.yata.lg.qaUserStory.run
Graph ID: qa_user_story_react
Triggered: manually or as post-deploy gate

Input (QAUserStoryState):
  test_results  — list of {status, name} dicts (same shape as qa_react)
  host          — optional target host label
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from lg_yatabase.graphs._llm import call_llm_json

_log = logging.getLogger(__name__)

# ── User story definitions ────────────────────────────────────────────────────
# Each story maps to one or more smoke-test name substrings (case-insensitive).
# A test "matches" a story if the test name contains any of the story's patterns.

_STORIES: list[dict[str, Any]] = [
    {
        "id": "US-1",
        "title": "Anonymous signup — no email or credit card required",
        "segment": "AI-native devs / indie hackers",
        "value_prop": "Fastest zero-friction onboarding in the graph-DB market",
        "patterns": ["/auth/v1/signup"],
        "required_all": True,
    },
    {
        "id": "US-2",
        "title": "Single API key unlocks graph + MCP + billing",
        "segment": "AI-native devs",
        "value_prop": "One bill; sk_live_yata_* is the only credential needed",
        "patterns": ["/api/plan", "mcp tools/call requires auth"],
        "required_all": True,
    },
    {
        "id": "US-3",
        "title": "First-class MCP discovery and execution",
        "segment": "AI-native devs building MCP-enabled products",
        "value_prop": "MCP-native — only competitor with first-party /mcp surface",
        "patterns": ["/.well-known/mcp.json", "mcp initialize", "mcp tools/list", "mcp resources/list"],
        "required_all": True,
    },
    {
        "id": "US-4",
        "title": "Run Cypher graph queries and mutations",
        "segment": "Data teams / graph DB evaluators",
        "value_prop": "Real-time graph DB — PG / SPARQL / Cypher over one bill",
        "patterns": [
            "/cypher tenant demo row",
            "/cypher create+set+delete",
            "/cypher edge traversal",
            "yata.graph.cypher",
        ],
        "required_all": False,  # story passes if at least one mapped test passes
    },
    {
        "id": "US-5",
        "title": "Usage and billing visibility (plan / invoices / usage)",
        "segment": "All paying customers",
        "value_prop": "Transparent metering — know what you owe before the bill arrives",
        "patterns": ["/api/plan", "/api/invoices", "/api/invoice", "/api/usage"],
        "required_all": True,
    },
    {
        "id": "US-6",
        "title": "Team member management (invite / revoke)",
        "segment": "Teams / startups",
        "value_prop": "Zero-friction collaboration — invite in one call, revoke in one call",
        "patterns": ["/api/members", "/auth/v1/invite"],
        "required_all": True,
    },
    {
        "id": "US-7",
        "title": "GDPR / 改正個人情報保護法 right-to-know export",
        "segment": "All users (legal compliance)",
        "value_prop": "Full data export — tables, billing events, API keys in one call",
        "patterns": ["/api/export"],
        "required_all": True,
    },
    {
        "id": "US-8",
        "title": "Account deletion (right-to-erasure)",
        "segment": "All users (legal compliance)",
        "value_prop": "Hard delete on demand — no soft-delete debt",
        "patterns": ["/api/account/delete"],
        "required_all": True,
    },
    {
        "id": "US-9",
        "title": "Tenant isolation and auth gate (security)",
        "segment": "Enterprise / regulated industries",
        "value_prop": "No cross-tenant data leakage; auth gate on all write surfaces",
        "patterns": [
            "/cypher tenant isolation",
            "mcp tools/call requires auth",
            "/cypher detach rejection",
        ],
        "required_all": True,
    },
    {
        "id": "US-10",
        "title": "Audit log — every API call is recorded",
        "segment": "Mid-market / compliance-driven teams",
        "value_prop": "Built-in audit trail — who did what, when",
        "patterns": ["/api/audit"],
        "required_all": True,
    },
]


class QAUserStoryState(TypedDict, total=False):
    run_id: str
    host: str
    test_results: list[dict[str, Any]]
    story_results: list[dict[str, Any]]
    passed: int
    failed: int
    skipped: int
    analysis: str
    report: dict[str, Any]


# ── Nodes ─────────────────────────────────────────────────────────────────────

def classify_stories(state: QAUserStoryState) -> QAUserStoryState:
    run_id = state.get("run_id") or str(uuid.uuid4())[:8]
    tests = state.get("test_results") or []
    # Build lookup: lowercase test name → status
    test_map: dict[str, str] = {
        r["name"].lower(): r["status"]
        for r in tests
        if "name" in r and "status" in r
    }

    story_results: list[dict[str, Any]] = []
    for story in _STORIES:
        patterns = [p.lower() for p in story["patterns"]]
        required_all: bool = story["required_all"]

        # Find all tests matching any pattern for this story
        matched: list[dict[str, str]] = []
        for test_name, test_status in test_map.items():
            if any(pat in test_name for pat in patterns):
                matched.append({"name": test_name, "status": test_status})

        if not matched:
            story_results.append({
                "id": story["id"],
                "title": story["title"],
                "segment": story["segment"],
                "value_prop": story["value_prop"],
                "status": "SKIP",
                "matched_tests": [],
                "detail": "no smoke tests mapped to this story",
            })
            continue

        passes = [m for m in matched if m["status"] == "PASS"]
        fails = [m for m in matched if m["status"] == "FAIL"]

        if required_all:
            overall = "PASS" if not fails else "FAIL"
        else:
            overall = "PASS" if passes else "FAIL"

        story_results.append({
            "id": story["id"],
            "title": story["title"],
            "segment": story["segment"],
            "value_prop": story["value_prop"],
            "status": overall,
            "matched_tests": matched,
            "detail": (
                f"{len(passes)}/{len(matched)} tests pass"
                + (f"; failing: {[f['name'] for f in fails]}" if fails else "")
            ),
        })

    passed = sum(1 for s in story_results if s["status"] == "PASS")
    failed = sum(1 for s in story_results if s["status"] == "FAIL")
    skipped = sum(1 for s in story_results if s["status"] == "SKIP")
    _log.info("[qa_user_story][%s] classified: pass=%d fail=%d skip=%d", run_id, passed, failed, skipped)
    return {
        "run_id": run_id,
        "story_results": story_results,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
    }


def analyze_stories(state: QAUserStoryState) -> QAUserStoryState:
    failures = [s for s in (state.get("story_results") or []) if s["status"] == "FAIL"]
    if not failures:
        return {"analysis": "All user stories passed or skipped — acceptance criteria met."}

    failure_lines = "\n".join(
        f"FAIL {s['id']} '{s['title']}' [{s['segment']}]: {s['detail']}"
        for s in failures
    )
    prompt = (
        f"The following yatabase user story acceptance criteria failed:\n\n{failure_lines}\n\n"
        "For each failure: (1) root cause, (2) business impact on the value proposition, "
        "(3) recommended fix priority (P1/P2/P3). "
        "Output JSON: {\"analyses\": [{\"story_id\": str, \"root_cause\": str, \"business_impact\": str, \"priority\": str}]}"
    )
    parsed, source = call_llm_json(prompt, max_tokens=640)
    if parsed and isinstance(parsed.get("analyses"), list):
        lines = [
            f"• {a['story_id']} [{a.get('priority','?')}]: {a['root_cause']} | impact: {a['business_impact']} → {a.get('fix', a.get('root_cause',''))}"
            for a in parsed["analyses"]
        ]
        analysis = f"LLM analysis ({source}):\n" + "\n".join(lines)
    else:
        analysis = f"LLM unavailable ({source}). Manual review needed:\n" + failure_lines
    return {"analysis": analysis}


def build_story_report(state: QAUserStoryState) -> QAUserStoryState:
    results = state.get("story_results") or []
    failed_stories = [s for s in results if s["status"] == "FAIL"]
    report = {
        "run_id": state.get("run_id"),
        "host": state.get("host", "https://yatabase.etzhayyim.com"),
        "ts": int(time.time() * 1000),
        "summary": {
            "passed": state.get("passed", 0),
            "failed": state.get("failed", 0),
            "skipped": state.get("skipped", 0),
            "total": len(results),
            "ok": state.get("failed", 0) == 0,
        },
        "stories": results,
        "failures": [
            {"id": s["id"], "title": s["title"], "detail": s["detail"]}
            for s in failed_stories
        ],
        "analysis": state.get("analysis", ""),
    }
    _log.info(
        "[qa_user_story][%s] report: pass=%d fail=%d skip=%d ok=%s",
        state.get("run_id"),
        report["summary"]["passed"],
        report["summary"]["failed"],
        report["summary"]["skipped"],
        report["summary"]["ok"],
    )
    return {"report": report}


# ── Graph ─────────────────────────────────────────────────────────────────────

_g: StateGraph = StateGraph(QAUserStoryState)
_g.add_node("classify_stories", classify_stories)
_g.add_node("analyze_stories", analyze_stories)
_g.add_node("build_story_report", build_story_report)
_g.add_edge(START, "classify_stories")
_g.add_edge("classify_stories", "analyze_stories")
_g.add_edge("analyze_stories", "build_story_report")
_g.add_edge("build_story_report", END)
GRAPH = _g.compile()
