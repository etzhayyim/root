#!/usr/bin/env python3
"""Generate per-class ISIC LangGraph Pregel agents using Claude Haiku (Batch API).

Output: one Python file per ISIC Rev. 4 class at
    20-actors/magatama/py/src/pymagatama/langgraph_graphs/isic_agents/c{code}.py

Pattern mirrors unispsc_agents/c{commodity}.py: each file exposes a compiled
`graph = StateGraph(...).compile()` at module top-level, loadable via importlib
from the langserver's lazy registry.

Cost: 428 classes x ~2k tokens prompt + ~500 tokens output via Haiku 4.5 Batch API
(50% discount) is approximately $0.30 per full run.

Usage:
    # Plan only (no API calls; print the prompts that would be sent)
    python gen_isic_agents.py --dry-run

    # Real run (creates a batch job, polls completion, writes files)
    python gen_isic_agents.py --execute

    # Resume a previously created batch by ID
    python gen_isic_agents.py --resume msgbatch_01ABC...

The script never writes files until the batch is fully completed and every
result file has parsed clean via ast.parse().
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
CLASS_DIR = REPO_ROOT / "60-apps" / "etzhayyim-project-open-isic" / "data" / "classes"
OUT_DIR = (
    REPO_ROOT
    / "20-actors"
    / "magatama"
    / "py"
    / "src"
    / "pymagatama"
    / "langgraph_graphs"
    / "isic_agents"
)

# ───── Prompt template ───────────────────────────────────────────────────────

SYSTEM_PROMPT = """You author single-file LangGraph Pregel agents.

Output ONLY valid Python source. No markdown fences. No prose. No commentary.
The file MUST compile cleanly via ast.parse() and MUST expose a compiled
`graph` object at module top-level.

Pattern (mirror this exactly):

    from typing import TypedDict, List
    from langgraph.graph import StateGraph, END

    class XxxState(TypedDict):
        # 3-6 fields specific to the domain
        ...

    def step_one(state: XxxState) -> XxxState:
        # short stateless transition; return state
        ...

    def step_two(state: XxxState) -> XxxState:
        ...

    graph = StateGraph(XxxState)
    graph.add_node('node_one', step_one)
    graph.add_node('node_two', step_two)
    graph.set_entry_point('node_one')
    graph.add_edge('node_one', 'node_two')
    graph.add_edge('node_two', END)
    graph = graph.compile()

Rules:
- Keep the StateGraph small: 2-4 nodes max.
- Use only stdlib + `langgraph.graph` imports. NO external HTTP, NO LLM calls
  from inside the agent — the agent is a deterministic state transducer.
- TypedDict field names: snake_case. Function names: snake_case verbs.
- The state shape MUST reflect the ISIC class's economic activity domain
  (e.g. for class 0111 "growing of cereals": fields like `crop_id`,
  `seed_certified`, `harvest_yield_kg`, `quality_grade`).
- Output MUST be the Python source only — no leading whitespace, no fences,
  no `# Output:` marker.
"""

USER_PROMPT_TEMPLATE = """ISIC Rev. 4 class: {code} — {name_en}

Group: {group}

Description: {description}

Includes (examples):
{includes_block}

Generate a single-file LangGraph Pregel agent representing a deterministic
state machine for entities in this class. The state fields should reflect the
domain (regulatory checks, lifecycle stages, evidence captured, outputs
produced) appropriate to this kind of economic activity.

Output only the Python source.
"""


def build_user_prompt(class_data: dict[str, Any]) -> str:
    includes = class_data.get("includes", [])[:6]
    if not includes:
        includes_block = "(none specified)"
    else:
        includes_block = "\n".join(f"  - {item}" for item in includes)
    return USER_PROMPT_TEMPLATE.format(
        code=class_data["code"],
        name_en=class_data.get("nameEn", "(unknown)"),
        group=class_data.get("group", "(unknown)"),
        description=(class_data.get("description") or "").strip()[:1500],
        includes_block=includes_block,
    )


# ───── Batch request build ───────────────────────────────────────────────────


def load_classes() -> list[dict[str, Any]]:
    files = sorted(CLASS_DIR.glob("*.json"))
    classes = []
    for f in files:
        with f.open() as fh:
            classes.append(json.load(fh))
    return classes


def build_batch_requests(
    classes: list[dict[str, Any]], model: str
) -> list[dict[str, Any]]:
    requests = []
    for c in classes:
        requests.append(
            {
                "custom_id": f"isic-{c['code']}",
                "params": {
                    "model": model,
                    "max_tokens": 1024,
                    "system": SYSTEM_PROMPT,
                    "messages": [{"role": "user", "content": build_user_prompt(c)}],
                },
            }
        )
    return requests


# ───── Validation + write ────────────────────────────────────────────────────


def extract_source(content_blocks: list[dict[str, Any]]) -> str:
    text = "".join(b.get("text", "") for b in content_blocks if b.get("type") == "text")
    text = text.strip()
    if text.startswith("```"):
        first_nl = text.find("\n")
        last_fence = text.rfind("```")
        if first_nl != -1 and last_fence > first_nl:
            text = text[first_nl + 1 : last_fence].strip()
    return text


def validate_and_write(code: str, source: str, out_dir: Path) -> tuple[bool, str]:
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return False, f"SyntaxError: {e}"

    has_graph_assignment = any(
        isinstance(node, ast.Assign)
        and any(
            isinstance(t, ast.Name) and t.id == "graph" for t in node.targets
        )
        for node in tree.body
    )
    if not has_graph_assignment:
        return False, "Missing top-level `graph = ...` assignment"

    target = out_dir / f"c{code}.py"
    target.write_text(source + "\n", encoding="utf-8")
    return True, str(target)


# ───── Main ──────────────────────────────────────────────────────────────────


def cmd_dry_run(args: argparse.Namespace) -> int:
    classes = load_classes()
    print(f"Would generate {len(classes)} ISIC class agents.", file=sys.stderr)
    print(f"Output dir: {OUT_DIR}", file=sys.stderr)
    print(f"Model: {args.model}", file=sys.stderr)
    if args.show_first:
        first = classes[0]
        print("\n--- SYSTEM PROMPT ---")
        print(SYSTEM_PROMPT)
        print(f"\n--- USER PROMPT for class {first['code']} ---")
        print(build_user_prompt(first))
    return 0


def cmd_execute(args: argparse.Namespace) -> int:
    try:
        import anthropic
    except ImportError:
        print(
            "ERROR: anthropic package required. Install via `uv add anthropic`.",
            file=sys.stderr,
        )
        return 2

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print(
            "ERROR: ANTHROPIC_API_KEY not set. Source it from 1Password before running.",
            file=sys.stderr,
        )
        return 2

    classes = load_classes()
    print(f"Loaded {len(classes)} class JSONs.", file=sys.stderr)

    client = anthropic.Anthropic(api_key=api_key)
    requests = build_batch_requests(classes, args.model)

    print(f"Submitting batch of {len(requests)} requests to {args.model}...",
          file=sys.stderr)
    batch = client.messages.batches.create(requests=requests)
    print(f"Batch created: {batch.id}", file=sys.stderr)
    print(f"To resume later: --resume {batch.id}", file=sys.stderr)

    return _poll_and_write(client, batch.id)


def cmd_resume(args: argparse.Namespace) -> int:
    try:
        import anthropic
    except ImportError:
        print("ERROR: anthropic package required.", file=sys.stderr)
        return 2

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set.", file=sys.stderr)
        return 2

    client = anthropic.Anthropic(api_key=api_key)
    return _poll_and_write(client, args.resume)


def _poll_and_write(client: Any, batch_id: str) -> int:
    print(f"Polling batch {batch_id}...", file=sys.stderr)
    while True:
        batch = client.messages.batches.retrieve(batch_id)
        status = batch.processing_status
        counts = batch.request_counts
        print(
            f"  status={status} processing={counts.processing} "
            f"succeeded={counts.succeeded} errored={counts.errored}",
            file=sys.stderr,
        )
        if status == "ended":
            break
        time.sleep(30)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    init_path = OUT_DIR / "__init__.py"
    if not init_path.exists():
        init_path.write_text(
            '"""Generated ISIC Rev. 4 per-class LangGraph Pregel agents.\n\n'
            'See ADR-2605180900 + 70-tools/scripts/gen-isic/gen_isic_agents.py.\n'
            '"""\n',
            encoding="utf-8",
        )

    ok_count = 0
    fail_count = 0
    failures: list[tuple[str, str]] = []
    for result in client.messages.batches.results(batch_id):
        custom_id = result.custom_id
        code = custom_id.removeprefix("isic-")
        if result.result.type != "succeeded":
            fail_count += 1
            failures.append((code, str(result.result.type)))
            continue
        msg = result.result.message
        source = extract_source([b.model_dump() for b in msg.content])
        ok, info = validate_and_write(code, source, OUT_DIR)
        if ok:
            ok_count += 1
        else:
            fail_count += 1
            failures.append((code, info))

    print(f"\nDone. wrote={ok_count} failed={fail_count}", file=sys.stderr)
    if failures:
        print("\nFailures:", file=sys.stderr)
        for code, reason in failures[:20]:
            print(f"  {code}: {reason}", file=sys.stderr)
        if len(failures) > 20:
            print(f"  ... +{len(failures) - 20} more", file=sys.stderr)
    return 0 if fail_count == 0 else 1


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Plan only; print sample prompts.",
    )
    p.add_argument(
        "--show-first",
        action="store_true",
        help="With --dry-run, print the first class's full prompt.",
    )
    p.add_argument(
        "--execute",
        action="store_true",
        help="Submit a batch job to Anthropic.",
    )
    p.add_argument(
        "--resume",
        default=None,
        help="Resume polling/writing for an existing batch by ID.",
    )
    p.add_argument(
        "--model",
        default="claude-haiku-4-5-20251001",
        help="Anthropic model ID (default: Haiku 4.5).",
    )
    args = p.parse_args()

    if args.dry_run:
        return cmd_dry_run(args)
    if args.resume:
        return cmd_resume(args)
    if args.execute:
        return cmd_execute(args)
    p.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
