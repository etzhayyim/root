#!/usr/bin/env python3
"""Bulk UNSPSC spec generator — processes commodity codes via ollama gemma4.

Usage:
  python bulk_spec_runner.py --input 80-data/unspsc_v26_ucalypt.csv --concurrency 8
  python bulk_spec_runner.py --input 80-data/unspsc_v26_ucalypt.csv --segment 43
  python bulk_spec_runner.py --status --input 80-data/unspsc_v26_ucalypt.csv

CSV column formats accepted (auto-detected):
  Format A (ucalypt/headerless 5-col):
    segment_name,family_name,class_name,commodity_name,code  (NO header row)
  Format B (standard UNSPSC.org):
    Code,Title,Definition,Excludes,Notes,Version
  Format C (minimal with header):
    code,name
  Format D (hierarchy flat with header):
    segment_code,segment_name,family_code,family_name,class_code,class_name,commodity_code,commodity_name

Checkpoint: each processed row is written to <input>.jsonl.
Resume: rows already in the JSONL are skipped.

RisingWave write: set KOTOBA_URL env var. Without it, rows are only written to JSONL.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Locate repo root and add kotodama to path
# ---------------------------------------------------------------------------

_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR
for _ in range(6):
    if (_REPO_ROOT / "20-actors").exists():
        break
    _REPO_ROOT = _REPO_ROOT.parent

_PY_SRC = _REPO_ROOT / "40-engine/kotoba/crates/kotoba-kotodama/py/src"
if str(_PY_SRC) not in sys.path:
    sys.path.insert(0, str(_PY_SRC))


# ---------------------------------------------------------------------------
# CSV loaders
# ---------------------------------------------------------------------------

def _is_ucalypt_format(path: Path) -> bool:
    """Detect headerless 5-col Ucalypt format: last field is 8-digit code."""
    with path.open(encoding="utf-8-sig", newline="") as f:
        first = f.readline().strip()
    if not first:
        return False
    parts = first.split(",")
    last = parts[-1].strip()
    return len(last) == 8 and last.isdigit()


def _detect_format(header: list[str]) -> str:
    h = [c.strip().lower() for c in header]
    if "commodity_code" in h or "commodity_name" in h:
        return "hierarchy"
    if "code" in h and "title" in h:
        return "unspsc_org"
    if "code" in h and "name" in h:
        return "minimal"
    return "unknown"


def load_csv(path: Path, segment_filter: str = "") -> list[dict[str, str]]:
    """Load commodity rows from UNSPSC CSV. Returns [{code, name, segment_name, family_name, class_name}]."""
    rows: list[dict[str, str]] = []

    # Ucalypt / headerless format: segment_name,family_name,class_name,commodity_name,code
    if _is_ucalypt_format(path):
        with path.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)
            for parts in reader:
                if len(parts) < 5:
                    continue
                code = parts[-1].strip()
                name = parts[-2].strip()
                digits = "".join(c for c in code if c.isdigit())
                if len(digits) != 8:
                    continue
                if segment_filter and digits[:2] != segment_filter.zfill(2):
                    continue
                rows.append({
                    "code": digits,
                    "name": name,
                    "segment_name": parts[0].strip(),
                    "family_name": parts[1].strip(),
                    "class_name": parts[2].strip(),
                })
        return rows

    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames or []
        fmt = _detect_format(list(header))

        for row in reader:
            if fmt == "hierarchy":
                code = row.get("commodity_code", "").strip()
                name = row.get("commodity_name", "").strip()
            elif fmt == "unspsc_org":
                raw = row.get("Code", "").strip()
                code = raw.replace(".", "").replace("-", "").replace(" ", "")
                name = row.get("Title", "").strip()
            else:
                code = row.get("code", "").strip()
                name = row.get("name", "").strip()

            digits = "".join(c for c in code if c.isdigit())
            if len(digits) != 8:
                continue
            if segment_filter and digits[:2] != segment_filter.zfill(2):
                continue
            rows.append({"code": digits, "name": name})

    return rows


# ---------------------------------------------------------------------------
# Checkpoint helpers
# ---------------------------------------------------------------------------

def load_checkpoint(jsonl_path: Path) -> set[str]:
    """Return set of commodity_codes already processed."""
    done: set[str] = set()
    if not jsonl_path.exists():
        return done
    with jsonl_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                code = obj.get("commodity_code") or obj.get("commodityCode")
                if code and obj.get("ok"):
                    done.add(str(code))
            except json.JSONDecodeError:
                pass
    return done


def append_checkpoint(jsonl_path: Path, result: dict[str, Any]) -> None:
    with jsonl_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(result, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# Worker
# ---------------------------------------------------------------------------

async def process_one(
    code: str,
    name: str,
    sem: asyncio.Semaphore,
    jsonl_path: Path,
    dry_run: bool,
) -> dict[str, Any]:
    async with sem:
        try:
            from kotodama.langgraph_graphs.open_unispsc_spec_gen import run_spec_gen
            result = await run_spec_gen(
                commodity_code=code,
                commodity_name=name,
                dry_run=dry_run,
            )
        except Exception as exc:
            result = {"ok": False, "commodity_code": code, "error": str(exc)}

        result["commodity_code"] = code
        result["commodity_name"] = name
        result["processed_at"] = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        append_checkpoint(jsonl_path, result)
        return result


# ---------------------------------------------------------------------------
# Status command
# ---------------------------------------------------------------------------

def cmd_status(jsonl_path: Path) -> None:
    if not jsonl_path.exists():
        print("No checkpoint file found.")
        return
    done = load_checkpoint(jsonl_path)
    errors: list[str] = []
    total = 0
    with jsonl_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            total += 1
            try:
                obj = json.loads(line)
                if not obj.get("ok"):
                    errors.append(obj.get("commodity_code", "?"))
            except json.JSONDecodeError:
                pass
    print(f"Processed: {len(done)} ok, {len(errors)} errors, {total} total rows in checkpoint")
    if errors[:10]:
        print(f"First errors: {errors[:10]}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def run(args: argparse.Namespace) -> None:
    if args.status:
        jsonl_path = Path(args.input).with_suffix(".jsonl") if args.input else Path("unspsc_spec.jsonl")
        cmd_status(jsonl_path)
        return

    if not args.input:
        print("ERROR: --input <csv_path> is required unless --status is set.", file=sys.stderr)
        sys.exit(1)

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    jsonl_path = input_path.with_suffix(".jsonl")
    dry_run = args.dry_run

    print(f"Loading CSV: {input_path}")
    rows = load_csv(input_path, segment_filter=args.segment or "")
    print(f"  → {len(rows)} commodity rows loaded")

    done = load_checkpoint(jsonl_path)
    todo = [r for r in rows if r["code"] not in done]
    print(f"  → {len(done)} already processed, {len(todo)} remaining")

    if not todo:
        print("All done.")
        return

    sem = asyncio.Semaphore(args.concurrency)
    tasks = [
        process_one(r["code"], r["name"], sem, jsonl_path, dry_run)
        for r in todo
    ]

    ok_count = 0
    err_count = 0
    batch_size = 100
    for i in range(0, len(tasks), batch_size):
        batch = tasks[i : i + batch_size]
        results = await asyncio.gather(*batch, return_exceptions=True)
        for r in results:
            if isinstance(r, Exception):
                err_count += 1
            elif r.get("ok"):
                ok_count += 1
            else:
                err_count += 1
        pct = (i + len(batch)) / len(tasks) * 100
        print(f"  [{pct:5.1f}%] {i + len(batch)}/{len(tasks)}  ok={ok_count}  err={err_count}")

    print(f"\nDone. ok={ok_count}, err={err_count}. Checkpoint: {jsonl_path}")
    if dry_run:
        print("(dry-run — no DB writes)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", "-i", help="Path to UNSPSC CSV file")
    parser.add_argument("--segment", "-s", help="Filter: 2-digit segment code (e.g. 43)")
    parser.add_argument("--concurrency", "-c", type=int, default=8, help="Parallel workers (default 8)")
    parser.add_argument("--dry-run", action="store_true", help="Generate specs but do not write to DB")
    parser.add_argument("--status", action="store_true", help="Show checkpoint progress and exit")
    parser.add_argument(
        "--model",
        default=os.environ.get("UNSPSC_SPEC_MODEL", "gemma4:latest"),
        help="Ollama model name (default: gemma4:latest)",
    )
    args = parser.parse_args()
    os.environ.setdefault("UNSPSC_SPEC_MODEL", args.model)
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
