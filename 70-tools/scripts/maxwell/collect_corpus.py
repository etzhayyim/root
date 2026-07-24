"""Maxwell M1 SFT corpus collector.

Extracts verified (Python fn, Clojure defn) pairs from the unit_refactor
results.  Only includes Clojure defns that are NOT port-failed stubs and
passed the clj-kondo + bb gate (i.e. they came from a successful unit).

Usage:
    python3 collect_corpus.py [--results JSONL] [--out JSONL] [--dry-run]

Output: maxwell-sft-corpus.jsonl  (one line per training example)
  {
    "id": "<actor>/<file>/<fn>",
    "messages": [
      {"role": "system", "content": "..."},
      {"role": "user",   "content": "..."},
      {"role": "model",  "content": "..."}
    ],
    "meta": {"src_py": "...", "src_clj": "...", "fn": "...", "scan": "ok"}
  }
"""

from __future__ import annotations

import ast
import json
import pathlib
import re
import sys
import textwrap

ROOT = pathlib.Path(__file__).resolve().parents[3]  # etzhayyim/root
RESULTS_JSONL = ROOT / "70-tools/scripts/fleet-refactor/unit-refactor-results.jsonl"
OUT_JSONL = ROOT / "90-docs/baien/maxwell-sft-corpus.jsonl"
CHARTER_RIDER_SRC = ROOT / "70-tools/scripts/maxwell/retired-charter-rider"

sys.path.insert(0, str(CHARTER_RIDER_SRC))
# also add the package parent so `etzhayyim_organism` resolves
if str(CHARTER_RIDER_SRC) not in sys.path:
    sys.path.insert(0, str(CHARTER_RIDER_SRC))
from etzhayyim_organism.sensors.charter_rider import scan  # noqa: E402

SYSTEM = (
    "You are Maxwell, etzhayyim's Murakumo fleet model. "
    "Convert Python actor methods to idiomatic Clojure that follows the "
    "kotoba Datom log conventions (namespaced keywords, pure stdlib, EAVT). "
    "Output only the `defn` form — no `ns` declaration, no prose."
)

INSTRUCTION = """\
Convert this Python method to Clojure following kotoba Datom log idioms:

```python
{py_src}
```

Output only the Clojure `defn` form."""


# ── Python extraction ──────────────────────────────────────────────────────────

def extract_py_fns(py_path: pathlib.Path) -> dict[str, str]:
    """Return {fn_name: source_text} for every module-level def."""
    src = py_path.read_text()
    lines = src.splitlines()
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return {}
    out: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not isinstance(node.col_offset, int) or node.col_offset != 0:
                continue  # skip nested
            fn_lines = lines[node.lineno - 1 : node.end_lineno]
            out[node.name] = "\n".join(fn_lines)
    return out


# ── Clojure extraction ─────────────────────────────────────────────────────────

_PORT_FAILED = re.compile(r'\(throw\s+\(ex-info\s+"TODO:\s+port-failed"')
_DEFN_START   = re.compile(r'^\(defn[- !]?\s+(\S+)')


def _paren_extent(lines: list[str], start: int) -> int:
    """Return the line index (inclusive) where the defn form closes."""
    depth = 0
    for i, line in enumerate(lines[start:], start):
        for ch in line:
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    return i
    return len(lines) - 1


def extract_clj_defns(clj_path: pathlib.Path) -> dict[str, str]:
    """Return {defn_name: full_defn_text} skipping port-failed stubs."""
    lines = clj_path.read_text().splitlines()
    out: dict[str, str] = {}
    i = 0
    while i < len(lines):
        m = _DEFN_START.match(lines[i].strip())
        if m:
            # find line index of actual (defn ...) (may have leading comment)
            defn_start = i
            end = _paren_extent(lines, defn_start)
            body = "\n".join(lines[defn_start : end + 1])
            if not _PORT_FAILED.search(body):
                out[m.group(1)] = body
            i = end + 1
        else:
            i += 1
    return out


def py_name_to_clj(name: str) -> str:
    """snake_case → kebab-case (simple heuristic)."""
    return name.replace("_", "-")


# ── Main ───────────────────────────────────────────────────────────────────────

def load_results() -> list[dict]:
    if not RESULTS_JSONL.exists():
        sys.exit(f"results not found: {RESULTS_JSONL}")
    rows = []
    with open(RESULTS_JSONL) as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def collect(dry_run: bool = False) -> list[dict]:
    results = load_results()
    examples: list[dict] = []
    skipped_scan = 0
    skipped_nopair = 0

    for row in results:
        if row.get("unit_ok", 0) == 0:
            continue
        py_path = pathlib.Path(row["src"])
        clj_path = pathlib.Path(row["out"])
        if not py_path.exists() or not clj_path.exists():
            continue

        py_fns  = extract_py_fns(py_path)
        clj_defs = extract_clj_defns(clj_path)

        # actor/file label for id
        parts = py_path.parts
        try:
            actor_idx = next(i for i, part in enumerate(parts) if part.startswith("com-etzhayyim-"))
            label = "/".join(parts[actor_idx:]).replace(".py", "")
        except ValueError:
            label = py_path.stem

        for py_name, py_src in py_fns.items():
            clj_name = py_name_to_clj(py_name)
            clj_src  = clj_defs.get(clj_name)
            if clj_src is None:
                # try without leading underscore
                clj_src = clj_defs.get(py_name_to_clj(py_name.lstrip("_")))
            if clj_src is None:
                skipped_nopair += 1
                continue

            combined = py_src + "\n" + clj_src
            scan_result = scan(combined)
            if not scan_result.ok:
                skipped_scan += 1
                print(f"  SCAN FAIL {label}/{py_name}: {scan_result.reason()}",
                      file=sys.stderr)
                continue

            ex = {
                "id": f"{label}/{py_name}",
                "messages": [
                    {"role": "system",  "content": SYSTEM},
                    {"role": "user",    "content": INSTRUCTION.format(py_src=py_src)},
                    {"role": "model",   "content": clj_src},
                ],
                "meta": {
                    "src_py":  str(py_path),
                    "src_clj": str(clj_path),
                    "fn":      py_name,
                    "scan":    "ok",
                },
            }
            examples.append(ex)

    print(f"\ncollected {len(examples)} pairs "
          f"(skipped: {skipped_nopair} no-pair, {skipped_scan} scan-fail)")

    if not dry_run:
        OUT_JSONL.parent.mkdir(parents=True, exist_ok=True)
        existing = set()
        if OUT_JSONL.exists():
            with open(OUT_JSONL) as f:
                for line in f:
                    if line.strip():
                        existing.add(json.loads(line)["id"])
        new = [e for e in examples if e["id"] not in existing]
        with open(OUT_JSONL, "a") as f:
            for e in new:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")
        print(f"wrote {len(new)} new examples → {OUT_JSONL}")
    else:
        print("[dry-run] nothing written")
        for e in examples[:3]:
            print(f"\n--- {e['id']} ---")
            print("USER:", e["messages"][1]["content"][:120], "…")
            print("MODEL:", e["messages"][2]["content"][:120], "…")

    return examples


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    collect(dry_run=dry)
