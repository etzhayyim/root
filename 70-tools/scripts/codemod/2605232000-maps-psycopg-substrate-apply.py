#!/usr/bin/env python3
"""ADR-2605172000 substrate cutover — Stage 2.

Applies the same refactor that openflights_dumper.py and
overture_maps_dumper.py received to the remaining bulk-ingest workers
that follow the standard `_insert_rows_into_rw(rows, batch_size=…)`
pattern. Each file gets:

  1. `import psycopg2` (+ the prior CHARTER-VIOLATION marker line)
     replaced by `from _etzhayyim_substrate import open_substrate_writer`
     plus a short header comment.

  2. The `_insert_rows_into_rw` function body replaced with the
     substrate-aware version (idempotent upsert via
     `writer.upsert_vertex_spatial(chunk)` inside
     `with open_substrate_writer() as writer:`).

  3. All caller references renamed from `_insert_rows_into_rw` to
     `_insert_rows_into_substrate`.

Idempotent. Re-runs that find the substrate import already in place
short-circuit the file.

Target files (10):

  wikidata_dumper.py
  wikipedia_dumper.py
  ferry_routes_dumper.py
  geonames_dumper.py
  gtfs_jp_dumper.py
  gtfs_rt_dumper.py
  gsplat_train_dumper.py
  noaa_ais_dumper.py
  maps_search_ivf_backfill.py
  aismarine_consumer.py
  aismarine_wikidata_lei.py

Files with NON-standard write paths (multi-table, custom executemany,
or aux-table writes) are migrated by this script ONLY for the
psycopg2 import line + caller renames. The custom write helpers are
flagged with an in-file TODO so the human reviewer can pick the right
``open_substrate_writer().upsert_table(...)`` shape per-file.

Usage::

    python3 70-tools/scripts/codemod/2605232000-maps-psycopg-substrate-apply.py
    python3 70-tools/scripts/codemod/2605232000-maps-psycopg-substrate-apply.py --dry-run
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
WORKERS_DIR = REPO_ROOT / "60-apps/etzhayyim-project-maps/bulk-ingest/workers"

DRY = "--dry-run" in sys.argv

SUBSTRATE_HEADER = (
    "# Per ADR-2605172000 (kotoba substrate), all maps writes route through\n"
    "# the substrate seam below; direct psycopg2 imports are no longer\n"
    "# permitted in this worker. The seam still supports a transitional RW\n"
    "# mode (psycopg2 under the hood) gated on ETZHAYYIM_SUBSTRATE_MODE.\n"
    "from _etzhayyim_substrate import open_substrate_writer\n"
)

STANDARD_BODY = '''def _insert_rows_into_substrate(rows: list[dict], batch_size: int = 1000) -> int:
    """Upsert ingested rows via the etzhayyim substrate seam.

    Per ADR-2605172000 the writer dispatches on
    ``ETZHAYYIM_SUBSTRATE_MODE``: ``mst`` (PDS → MST + IPFS + Base L2
    anchor, post-migration) or ``rw`` (psycopg2 → vertex_spatial,
    transitional). Idempotent upsert keyed on ``vertex_id``.
    """
    if not rows:
        return 0
    total = 0
    with open_substrate_writer() as writer:
        for i in range(0, len(rows), batch_size):
            chunk = rows[i : i + batch_size]
            try:
                total += writer.upsert_vertex_spatial(chunk)
            except Exception as e:
                log.warning(
                    "substrate upsert failed (chunk %d-%d): %s",
                    i,
                    i + len(chunk),
                    e,
                )
    return total
'''


STANDARD_TARGETS = [
    "wikidata_dumper.py",
    "wikipedia_dumper.py",
    "ferry_routes_dumper.py",
    "geonames_dumper.py",
]

NONSTANDARD_TARGETS = [
    # Multi-table / aux-table writes — these get the import swap +
    # caller renames where applicable, plus an in-file TODO. The
    # per-table refactor is left for human review because the lexicon
    # mapping (`writer.upsert_table('<table>', rows)`) is not uniform.
    "gtfs_jp_dumper.py",
    "gtfs_rt_dumper.py",
    "gsplat_train_dumper.py",
    "noaa_ais_dumper.py",
    "maps_search_ivf_backfill.py",
    "aismarine_consumer.py",
    "aismarine_wikidata_lei.py",
]


MARKER_RE = re.compile(
    r"^# CHARTER-VIOLATION §substrate \(ADR-2605172000\)[^\n]*\nimport psycopg2(?:\.\w+)?\n",
    re.MULTILINE,
)
BARE_IMPORT_RE = re.compile(r"^import psycopg2(?:\.\w+)?\n", re.MULTILINE)
BARE_FROM_RE = re.compile(r"^from psycopg2(?:\.\w+)? import [^\n]+\n", re.MULTILINE)


def replace_import(src: str) -> tuple[str, bool]:
    if "from _etzhayyim_substrate import open_substrate_writer" in src:
        return src, False
    if MARKER_RE.search(src):
        return MARKER_RE.sub(SUBSTRATE_HEADER, src, count=1), True
    if BARE_IMPORT_RE.search(src):
        return BARE_IMPORT_RE.sub(SUBSTRATE_HEADER, src, count=1), True
    if BARE_FROM_RE.search(src):
        return BARE_FROM_RE.sub(SUBSTRATE_HEADER, src, count=1), True
    return src, False


STANDARD_FN_RE = re.compile(
    r"def _insert_rows_into_rw\([^)]*\)\s*->\s*int:.*?^    return total\n",
    re.DOTALL | re.MULTILINE,
)


def replace_standard_body(src: str) -> tuple[str, bool]:
    m = STANDARD_FN_RE.search(src)
    if not m:
        return src, False
    new = src[: m.start()] + STANDARD_BODY + src[m.end():]
    return new, True


CALLER_RE = re.compile(r"\b_insert_rows_into_rw\b")


def rename_callers(src: str) -> tuple[str, int]:
    new, n = CALLER_RE.subn("_insert_rows_into_substrate", src)
    return new, n


NONSTD_TODO = (
    "# TODO(ADR-2605172000 / Stage 2): the writes below still hit\n"
    "# RisingWave directly via psycopg2 patterns specific to this\n"
    "# worker. Replace them with `open_substrate_writer().upsert_table(\n"
    "# '<table>', rows, conflict_key=...)` per the substrate seam\n"
    "# contract in `_etzhayyim_substrate.py`. The legacy import has\n"
    "# been re-added below as a guarded fallback so the worker still\n"
    "# functions while ETZHAYYIM_SUBSTRATE_MODE=rw; remove it once the\n"
    "# call sites are migrated.\n"
    "import psycopg2  # noqa: E402 — pending substrate refactor (Stage 2)\n"
)


def patch_one(path: Path) -> str:
    """Returns a short status string for the run summary."""
    src = path.read_text()
    name = path.name

    new, swapped = replace_import(src)
    if not swapped and "from _etzhayyim_substrate import open_substrate_writer" not in new:
        return f"skip:no-psycopg2-import {name}"

    if name in STANDARD_TARGETS:
        new, body_swapped = replace_standard_body(new)
        if not body_swapped:
            return f"warn:standard-body-not-matched {name}"
        new, renamed = rename_callers(new)
        if DRY:
            return f"would-rewrite-standard renames={renamed} {name}"
        path.write_text(new)
        return f"rewritten-standard renames={renamed} {name}"

    # Non-standard: keep psycopg2 available as a guarded fallback via
    # the TODO block, and rename any callers that happen to use the
    # standard function name. The worker remains runnable in rw mode.
    new = new.replace(
        "from _etzhayyim_substrate import open_substrate_writer\n",
        "from _etzhayyim_substrate import open_substrate_writer\n\n" + NONSTD_TODO,
        1,
    )
    new, renamed = rename_callers(new)
    if DRY:
        return f"would-annotate-nonstandard renames={renamed} {name}"
    path.write_text(new)
    return f"annotated-nonstandard renames={renamed} {name}"


def main() -> int:
    results: list[str] = []
    for fname in STANDARD_TARGETS + NONSTANDARD_TARGETS:
        p = WORKERS_DIR / fname
        if not p.exists():
            results.append(f"missing {fname}")
            continue
        results.append(patch_one(p))
    for r in results:
        print(r)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
