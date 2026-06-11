#!/usr/bin/env python3
"""harvest-langgraph-internal.py — W5 deliverable per ADR-2605262100 §3.1 + §3.0.W.

Walk repo-internal LangGraph code (Pregel cells / distill nodes / mst-projector projection)
and emit (instruction-style prompt → code) pairs as JSONL.

Output: 90-docs/baien/moemoekyun-r1.4-langgraph-harvest.jsonl
Then operator runs `e7m-dataset add local://...` to pin + register CID in datasets.jsonl.

Sources scanned:
  - 40-engine/kotoba/crates/kotoba-kotodama/cells/**/cell.py
  - 40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/**/cells/*.py
  - 70-tools/baien-distill/src/baien_distill/nodes/*.py
  - 50-infra/mst-projector/projection/**/*.py
  - 70-tools/baien-moemoekyun-train/scripts/rental-orchestrator.py (this self-ref ok)
  - 70-tools/gemma-coder-distill/src/**/*.py (if exists)

License: Apache 2.0 (repo-own). Tier A. Charter Rider §2(a)-(h) scan: per-file mandatory.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

logger = logging.getLogger("langgraph-harvest")


REPO_ROOT = Path(__file__).parent.parent.parent.parent.resolve()


SOURCE_PATTERNS = [
    # LangGraph Pregel cells
    "40-engine/kotoba/crates/kotoba-kotodama/cells/**/*.py",
    "40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/**/cells/*.py",
    "40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/**/nodes/*.py",
    # ReAct distill nodes
    "70-tools/baien-distill/src/baien_distill/nodes/*.py",
    "70-tools/baien-distill/src/baien_distill/graph/*.py",
    "70-tools/gemma-coder-distill/src/**/*.py",
    # MST projector
    "50-infra/mst-projector/py/src/**/*.py",
    "50-infra/mst-projector/projection/**/*.py",
    # Kaizen observer
    "40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/organism/kaizen/*.py",
]


EXCLUDE_PATTERNS = [
    "**/__pycache__/**",
    "**/test_*.py",
    "**/tests/*.py",
    "**/.venv/**",
    "**/node_modules/**",
    "**/build/**",
    "**/dist/**",
]


def is_excluded(path: Path, root: Path) -> bool:
    rel = path.relative_to(root)
    rel_str = str(rel)
    for ex in EXCLUDE_PATTERNS:
        if rel.match(ex):
            return True
    if "__pycache__" in rel_str or ".venv" in rel_str:
        return True
    return False


def scan_files(root: Path) -> Iterator[Path]:
    seen = set()
    for pattern in SOURCE_PATTERNS:
        for path in root.glob(pattern):
            if path.is_file() and path.suffix == ".py" and not is_excluded(path, root):
                if path not in seen:
                    seen.add(path)
                    yield path


def extract_function_pairs(path: Path) -> Iterator[dict]:
    """Extract (docstring-prompt -> code-body) pairs from each top-level def/async def + class methods.

    Uses AST parse for robustness; skips functions without docstrings.
    """
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        logger.warning("skip %s: %s", path, e)
        return

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as e:
        logger.warning("syntax error in %s: %s", path, e)
        return

    rel_path = path.relative_to(REPO_ROOT)

    def visit_node(node, class_name=None):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            docstring = ast.get_docstring(node)
            if not docstring or len(docstring.strip()) < 20:
                return
            # Extract function source (lines from def to end)
            start_line = node.lineno
            end_line = node.end_lineno
            func_src = "\n".join(source.splitlines()[start_line - 1:end_line])
            name = f"{class_name}.{node.name}" if class_name else node.name
            # Skip self-documenting trivial getters
            if len(func_src.split("\n")) < 4:
                return
            yield {
                "source_file": str(rel_path),
                "function_name": name,
                "is_async": isinstance(node, ast.AsyncFunctionDef),
                "instruction": f"Implement a Python function `{name}` per this contract:\n\n{docstring.strip()}",
                "code": func_src,
                "line_range": [start_line, end_line],
            }
        elif isinstance(node, ast.ClassDef):
            for child in node.body:
                yield from visit_node(child, class_name=node.name)

    for node in tree.body:
        yield from visit_node(node)


def charter_rider_scan_line(line: str) -> tuple[bool, str | None]:
    """Inline single-line Charter Rider §2(a)-(h) hint scanner.

    Returns (passed, reason_if_fail). Conservative: flag obvious red-flag tokens.
    Real scan via kotodama deferred (importable on EVO/fleet but not here).
    """
    redflags = {
        "weapon": "§2(a) weapons",
        "missile": "§2(a) weapons",
        "surveillance": "§2(c) surveillance",
        "tracking_pixel": "§2(c) surveillance",
        "addictive": "§2(h) wellbecoming",
        "high_frequency_trad": "§2(b) speculative finance",  # truncated form to avoid self-trigger
    }
    lower = line.lower()
    for tok, why in redflags.items():
        if tok in lower:
            # Allow as-context if file is etzhayyim-internal critique doc; for harvest, reject
            return False, why
    return True, None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        default=str(REPO_ROOT / "90-docs/baien/moemoekyun-r1.4-langgraph-harvest.jsonl"),
        help="JSONL output path",
    )
    parser.add_argument("--max-pairs", type=int, default=500, help="Cap on extracted pairs")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    )

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)

    pairs = []
    stats = {"files_scanned": 0, "pairs_extracted": 0, "charter_rider_rejected": 0}

    for path in scan_files(REPO_ROOT):
        stats["files_scanned"] += 1
        for pair in extract_function_pairs(path):
            # Apply inline Charter Rider scan line-by-line on the code body
            rejected = False
            for line in pair["code"].splitlines():
                ok, why = charter_rider_scan_line(line)
                if not ok:
                    logger.debug("Charter Rider reject %s: %s line='%s'", pair["source_file"], why, line[:80])
                    stats["charter_rider_rejected"] += 1
                    rejected = True
                    break
            if rejected:
                continue
            pair["sha256"] = hashlib.sha256(pair["code"].encode()).hexdigest()
            pair["captured_at"] = datetime.now(timezone.utc).isoformat()
            pair["license"] = "Apache-2.0 + Charter Rider v2.0 (repo-own)"
            pairs.append(pair)
            stats["pairs_extracted"] += 1
            if len(pairs) >= args.max_pairs:
                break
        if len(pairs) >= args.max_pairs:
            break

    with open(args.output, "w") as f:
        for p in pairs:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    logger.info("Stats: %s", stats)
    logger.info("Output: %s (%d pairs, %.1f KB)", args.output, len(pairs), Path(args.output).stat().st_size / 1024)

    summary = {
        "tool": "harvest-langgraph-internal.py",
        "adr": "ADR-2605262100 §3.1 W5",
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "stats": stats,
        "output": args.output,
        "output_size_bytes": Path(args.output).stat().st_size,
        "license": "Apache-2.0 + Charter Rider v2.0 (repo-own)",
        "tier": "A",
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
