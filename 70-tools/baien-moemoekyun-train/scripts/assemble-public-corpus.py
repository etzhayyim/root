#!/usr/bin/env python3
"""assemble-public-corpus.py — cold-path corpus assembler.

Per ADR-2605262400 §4. Two modes:

  --dry-run     : recipe validation + summary only. Placeholder
                  datasetPin AT-URIs are accepted. Default in CI.
  (default)     : full assembly. Walks each source's shards under the
                  annex-store, streams rows through Charter Rider §2
                  scan + PII filter, and emits NDJSON shards into the
                  output subdataset with per-row {source, license,
                  tier, internal_only, pin_revision} tags. The seed
                  block is copied verbatim. A manifest is emitted at
                  ``<out_dir>/manifest.json``.

Usage:

    python assemble-public-corpus.py --recipe <path.toml> \\
        [--annex-root <path>] [--out-dir <path>] [--dry-run]

Behavior contract (per §4):

  1. Parse + validate the recipe (TOML); G5 NC-infix gate enforced.
  2. For each source, resolve the shard directory under the annex-store.
  3. Stream NDJSON / zone-file rows through Charter Rider §2 +
     pii_filter.redact_payload. Charter violations ⇒ abort fail-closed.
  4. Emit NDJSON shards into the output subdataset with per-row
     {source, license, tier, internal_only, pin_revision}.
  5. Copy the seed block verbatim.
  6. Write manifest.json summarizing the run.

The assembler does NOT run `datalad save` / `publish-ipfs` /
`datasetPin emit` on the OUTPUT subdataset — that's the operator's
explicit step, mirroring the e7m-dataset add chain.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator

try:
    import tomllib  # Python 3.11+
except ImportError:  # pragma: no cover
    import tomli as tomllib  # type: ignore


SCHEMA_VERSION = 1
TIER_ORDER = {"A": 0, "B": 1, "C": 2, "D": 3}

# Charter Rider scan sampling — every Nth NDJSON row is forwarded to the
# scanner. The full row is still passed through the PII filter.
_CHARTER_SAMPLE_EVERY = 100


@dataclass
class SourceSpec:
    subdataset: str
    dataset_pin_at: str
    shard_glob: str
    tier: str
    license: str
    weight: float
    sa_propagates: bool = False
    max_rows: int = 0  # 0 = no cap (full file); per-source override
    max_bytes: int = 0  # 0 = no cap (full file); per-source override
    description: str = ""  # per-source operator-facing context (free-form)


@dataclass
class SeedBlock:
    weight: float
    seed_path: Path
    description: str = ""


@dataclass
class Recipe:
    target_artifact: str
    output_subdataset: str
    max_tier_cap: str
    output_metadata: dict[str, Any]
    sources: list[SourceSpec]
    seed_block: SeedBlock | None = None
    recipe_path: Path | None = None
    description: str = ""  # operator-facing context (free-form)

    @property
    def computed_max_tier(self) -> str:
        rank = max((TIER_ORDER[s.tier] for s in self.sources), default=0)
        for k, v in TIER_ORDER.items():
            if v == rank:
                return k
        return "A"

    def validate(self) -> list[str]:
        errors: list[str] = []
        cap = TIER_ORDER.get(self.max_tier_cap)
        if cap is None:
            errors.append(f"invalid max_tier_cap {self.max_tier_cap!r}")
        else:
            for s in self.sources:
                if TIER_ORDER[s.tier] > cap:
                    errors.append(
                        f"source '{s.subdataset}' tier {s.tier} exceeds cap "
                        f"{self.max_tier_cap}"
                    )
        # NC infix gate (G5). Require `nc` to appear as its own dash-
        # delimited token — substring match alone would pass things like
        # "no-nc-infix" or "non-conformist".
        if self.computed_max_tier == "C":
            tokens = self.target_artifact.split("-")
            if "nc" not in tokens:
                errors.append(
                    f"target_artifact '{self.target_artifact}' must contain "
                    f"a standalone '-nc-' infix (dash-delimited token 'nc') "
                    f"because at least one source is Tier C "
                    f"(G5 in ADR-2605262400 §9)"
                )
        total_weight = sum(s.weight for s in self.sources)
        if self.seed_block is not None:
            total_weight += self.seed_block.weight
        if not (0.99 <= total_weight <= 1.01):
            errors.append(
                f"weights sum to {total_weight:.3f}, expected ≈ 1.0"
            )
        return errors

    def warnings(self) -> list[str]:
        """Non-fatal advisories. Returned alongside `validate()` errors
        but DON'T block assembly. Mirrors the pattern of compiler
        warnings: things the operator probably wants to know about
        but that aren't constitutional violations.
        """
        warns: list[str] = []
        # Missing seed-block file — declared weight, but the file won't
        # contribute. Pairs with the dry-run / manifest / markdown
        # honesty fix in commit e333b097a.
        if (
            self.seed_block is not None
            and not self.seed_block.seed_path.exists()
        ):
            warns.append(
                f"seed_block declares weight={self.seed_block.weight:.2f} "
                f"but seed_path '{self.seed_block.seed_path}' doesn't exist "
                f"on disk; assembly will silently emit ZERO seed rows for "
                f"this block. Author the file or remove [seed_block]."
            )
        # Placeholder pins detected at parse time. Distinct from the
        # hard-fail-at-assembly check in main() — surfacing here lets
        # `--dry-run` and `--summary` show the operator the gap before
        # they start any real work.
        placeholders = [
            s.subdataset for s in self.sources
            if "PLACEHOLDER_" in s.dataset_pin_at
        ]
        if placeholders:
            warns.append(
                f"{len(placeholders)} source(s) carry placeholder "
                f"datasetPin AT-URIs (will block actual assembly): "
                f"{', '.join(placeholders)}"
            )
        return warns


def load_recipe(path: Path) -> Recipe:
    raw = tomllib.loads(path.read_text(encoding="utf-8"))
    sources_raw = raw.get("source", [])
    sources = [
        SourceSpec(
            subdataset=s["subdataset"],
            dataset_pin_at=s["datasetPin_at"],
            shard_glob=s["shard_glob"],
            tier=s["tier"],
            license=s["license"],
            weight=float(s["weight"]),
            sa_propagates=bool(s.get("sa_propagates", False)),
            max_rows=int(s.get("max_rows", 0)),
            max_bytes=int(s.get("max_bytes", 0)),
            description=str(s.get("description", "")),
        )
        for s in sources_raw
    ]
    seed_raw = raw.get("seed_block")
    seed_block = None
    if seed_raw is not None:
        seed_block = SeedBlock(
            weight=float(seed_raw["weight"]),
            seed_path=Path(seed_raw["seed_path"]),
            description=seed_raw.get("description", ""),
        )
    return Recipe(
        target_artifact=raw["target_artifact"],
        output_subdataset=raw["output_subdataset"],
        max_tier_cap=raw.get("max_tier_cap", "A"),
        output_metadata=raw.get("output_metadata", {}),
        sources=sources,
        seed_block=seed_block,
        recipe_path=path,
        description=str(raw.get("description", "")),
    )


def _is_placeholder(at_uri: str) -> bool:
    return "PLACEHOLDER_" in at_uri


def dry_run_summary(recipe: Recipe) -> dict[str, Any]:
    placeholders = [
        s.subdataset for s in recipe.sources if _is_placeholder(s.dataset_pin_at)
    ]
    # Lightweight per-source preview (operator-facing). Helpful when the
    # operator is browsing recipes via `--dry-run` and wants to see what
    # each source actually contributes without opening the TOML.
    sources_preview = [
        {
            "subdataset": s.subdataset,
            "tier": s.tier,
            "license": s.license,
            "weight": s.weight,
            "description": s.description,
        }
        for s in recipe.sources
    ]
    return {
        "recipePath": str(recipe.recipe_path) if recipe.recipe_path else None,
        "targetArtifact": recipe.target_artifact,
        "outputSubdataset": recipe.output_subdataset,
        "description": recipe.description,
        "outputMetadata": recipe.output_metadata,
        "maxTierCap": recipe.max_tier_cap,
        "computedMaxTier": recipe.computed_max_tier,
        "sourceCount": len(recipe.sources),
        "sources": sources_preview,
        "placeholderPins": placeholders,
        "warnings": recipe.warnings(),
        "seedBlock": (
            {
                "weight": recipe.seed_block.weight,
                "seedPath": str(recipe.seed_block.seed_path),
                # Honestly report whether the file is actually present
                # on disk. Operators have been bitten by recipes that
                # claim weight=0.50 seed but silently emit zero seed
                # rows because the seed_path doesn't resolve (the
                # assembler does an .exists() check before copying).
                "exists": recipe.seed_block.seed_path.exists(),
            }
            if recipe.seed_block
            else None
        ),
    }


def summary_markdown(recipe: Recipe) -> str:
    """Render the recipe as an operator-facing markdown summary.

    Consumes the operator-readability fields (top-level description +
    output_metadata + per-source description) added in commits
    2fbe6b4ad / 3d90961b5 / 503856f7b. Useful as `--summary` CLI
    output or as a sidecar `.md` per recipe.
    """
    lines: list[str] = []
    lines.append(f"# Recipe — {recipe.target_artifact}")
    lines.append("")
    if recipe.description:
        lines.append(recipe.description)
        lines.append("")

    lines.append(f"- **Output subdataset**: `{recipe.output_subdataset}`")
    lines.append(f"- **Max tier cap**: {recipe.max_tier_cap}")
    lines.append(f"- **Computed max tier**: {recipe.computed_max_tier}")
    lines.append(f"- **Source count**: {len(recipe.sources)}")
    if recipe.recipe_path:
        lines.append(f"- **Recipe path**: `{recipe.recipe_path}`")

    if recipe.output_metadata:
        lines.append("")
        lines.append("## Output metadata")
        lines.append("")
        for k, v in recipe.output_metadata.items():
            # Multi-line strings (e.g. existing `description = """..."""`)
            # render as blockquotes; everything else as inline `key: value`.
            v_str = str(v).strip()
            if "\n" in v_str:
                lines.append(f"**{k}**:")
                lines.append("")
                for line in v_str.split("\n"):
                    lines.append(f"> {line}")
                lines.append("")
            else:
                lines.append(f"- **{k}**: {v_str}")

    # Surface non-fatal advisories prominently — ahead of the Sources
    # section so an operator browsing the doc sees them first.
    warns = recipe.warnings()
    if warns:
        lines.append("")
        lines.append(
            f"## ⚠ Issues ({len(warns)} non-fatal advisor"
            f"{'y' if len(warns) == 1 else 'ies'})"
        )
        lines.append("")
        for w in warns:
            lines.append(f"- {w}")

    lines.append("")
    lines.append("## Sources")
    lines.append("")
    for i, s in enumerate(recipe.sources, 1):
        lines.append(
            f"### {i}. `{s.subdataset}` "
            f"(Tier {s.tier}, weight {s.weight:.2f})"
        )
        lines.append("")
        if s.description:
            lines.append(s.description)
            lines.append("")
        lines.append(f"- **License**: {s.license}")
        lines.append(f"- **Dataset pin**: `{s.dataset_pin_at}`")
        lines.append(f"- **Shard glob**: `{s.shard_glob}`")
        if s.sa_propagates:
            lines.append("- **SA propagates**: yes")
        if s.max_rows > 0:
            lines.append(f"- **Per-source row cap**: {s.max_rows:,}")
        if s.max_bytes > 0:
            lines.append(f"- **Per-source byte cap**: {s.max_bytes:,}")
        lines.append("")

    if recipe.seed_block is not None:
        exists = recipe.seed_block.seed_path.exists()
        header = "## Seed block" if exists else "## Seed block — ⚠ MISSING"
        lines.append(header)
        lines.append("")
        if not exists:
            lines.append(
                f"> The seed_path does not exist on disk. The assembler "
                f"silently skips missing seed blocks, so a recipe declaring "
                f"`weight = {recipe.seed_block.weight:.2f}` seed will in fact "
                f"emit ZERO seed rows. Author the file or remove `[seed_block]` "
                f"to keep the corpus honest about its composition."
            )
            lines.append("")
        if recipe.seed_block.description:
            lines.append(recipe.seed_block.description)
            lines.append("")
        lines.append(f"- **Weight**: {recipe.seed_block.weight:.2f}")
        lines.append(f"- **Path**: `{recipe.seed_block.seed_path}`")
        lines.append(f"- **Exists on disk**: {'yes' if exists else 'NO'}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Assemble a public-data training corpus per ADR-2605262400."
    )
    p.add_argument("--recipe", required=True, type=Path)
    p.add_argument(
        "--annex-root",
        type=Path,
        default=None,
        help="Annex-store root holding the source subdatasets "
             "(default: ${ETZ_DATASET_ROOT}/annex-store).",
    )
    p.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Override output staging dir (default = "
             "${ETZ_DATASET_ROOT}/datasets-staging/<output_subdataset>).",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate recipe + emit JSON summary, do NOT resolve pins "
             "or stream shards.",
    )
    p.add_argument(
        "--summary",
        action="store_true",
        help="Print an operator-facing markdown summary of the recipe "
             "to stdout, then exit. Consumes the top-level description, "
             "output_metadata, and per-source description fields. "
             "Mutually exclusive with --dry-run.",
    )
    p.add_argument(
        "--max-rows-per-source",
        type=int,
        default=0,
        help="Cap row emission per source at N rows (head-biased; uses "
             "itertools.islice-style early exit). 0 (default) = no cap "
             "= full file iteration. Useful for partial corpora from "
             "huge sources (e.g. RIPE-RIS bview NDJSON sidecars with "
             "5-10M rows). Per-source override available via the recipe's "
             "[[source]] `max_rows` field (takes precedence over this flag).",
    )
    p.add_argument(
        "--max-bytes-per-source",
        type=int,
        default=0,
        help="Cap emitted output bytes per source at N bytes (head-biased; "
             "stops emission once total bytes written to the per-source "
             "output shard reaches the cap, AFTER the row that crossed the "
             "threshold is emitted). 0 (default) = no cap. Useful when an "
             "operator has a disk-budget constraint rather than a row "
             "count constraint (e.g. 'give me ≤10 MB of RIPE-RIS rows'). "
             "Per-source override available via the recipe's [[source]] "
             "`max_bytes` field (takes precedence). Both row and byte "
             "caps can be active together — whichever fires first wins.",
    )
    args = p.parse_args(argv)

    if args.summary and args.dry_run:
        print(
            "--summary and --dry-run are mutually exclusive; pick one.",
            file=sys.stderr,
        )
        return 2

    recipe = load_recipe(args.recipe)
    errors = recipe.validate()
    if errors:
        print("Recipe validation FAILED:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 2

    # Non-fatal advisories. Surfaced to stderr so they're visible at
    # dry-run + summary time AND when piping stdout to a file.
    for w in recipe.warnings():
        print(f"WARN: {w}", file=sys.stderr)

    if args.summary:
        print(summary_markdown(recipe), end="")
        return 0

    summary = dry_run_summary(recipe)
    print(json.dumps(summary, indent=2, ensure_ascii=False))

    if args.dry_run:
        return 0

    placeholders = summary.get("placeholderPins", [])
    if placeholders:
        print(
            "Refusing to assemble: placeholder datasetPin AT-URIs present "
            "for sources: " + ", ".join(placeholders),
            file=sys.stderr,
        )
        return 3

    annex_root = _resolve_annex_root(args.annex_root)
    if annex_root is None:
        print(
            "Refusing to assemble: cannot resolve annex-store root. "
            "Pass --annex-root or set ETZ_DATASET_ROOT.",
            file=sys.stderr,
        )
        return 5

    out_dir = _resolve_out_dir(recipe, args.out_dir)
    try:
        result = assemble(
            recipe,
            annex_root=annex_root,
            out_dir=out_dir,
            max_rows_per_source=args.max_rows_per_source,
            max_bytes_per_source=args.max_bytes_per_source,
        )
    except CorpusAssemblyError as exc:
        print(f"Assembly aborted: {exc}", file=sys.stderr)
        return 6

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


# ── Charter / PII / shard streaming ────────────────────────────────────


class CorpusAssemblyError(RuntimeError):
    """Raised when an assembly step decides to abort fail-closed."""


def _direct_load(module_name: str, file_path: Path):
    """Load a Python file as a standalone module.

    Avoids triggering ``kotodama/__init__.py`` (which imports
    langchain → pydantic; on systems with a broken pydantic-core
    pinning this poisons the import). The Charter scanner + PII filter
    are pure stdlib + regex; they don't need the rest of the package.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise CorpusAssemblyError(f"could not build spec for {file_path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


def _find_kotodama_src() -> Path | None:
    """Locate the in-tree kotodama source. Strategies:

    1. ``ETZ_PYKOTODAMA_SRC`` env var (highest priority).
    2. Walk up from this file looking for ``40-engine/kotoba/crates/kotoba-kotodama/py/src/``.
    """
    env = os.environ.get("ETZ_PYKOTODAMA_SRC")
    if env:
        p = Path(env)
        if (p / "kotodama/organism/sensors/charter_rider.py").exists():
            return p
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "40-engine/kotoba/crates/kotoba-kotodama/py/src"
        if (candidate / "kotodama/organism/sensors/charter_rider.py").exists():
            return candidate
    return None


def _try_import_charter_scanner():
    """Resolve the Charter Rider scanner.

    Uses the canonical ``e7m_dataset.charter._load_scanner`` (which
    itself does the spec_from_file_location direct-load fallback).
    Falls back to the bespoke direct-loader only if e7m_dataset is not
    importable.
    """
    try:
        from e7m_dataset.charter import _load_scanner  # type: ignore
        mod = _load_scanner()
        if mod is None:
            raise CorpusAssemblyError(
                "Charter Rider scanner could not be loaded via "
                "e7m_dataset.charter._load_scanner. Install kotodama "
                "or set ETZ_PYKOTODAMA_SRC."
            )
        return mod.scan
    except ImportError:
        pass

    # Legacy fallback — preserved so the standalone script keeps
    # working from any checkout that pre-dates the e7m_dataset.charter
    # canonical wrapper.
    src = _find_kotodama_src()
    if src is None:
        raise CorpusAssemblyError(
            "Could not locate kotodama source. Set ETZ_PYKOTODAMA_SRC "
            "or run from inside the etzhayyim-root tree, or install "
            "e7m_dataset (which exposes the canonical wrapper)."
        )
    mod = _direct_load(
        "_corpus_assembler_charter_rider",
        src / "kotodama/organism/sensors/charter_rider.py",
    )
    return mod.scan


def _try_import_pii_filter():
    """Resolve the PII redactor.

    Uses the canonical ``e7m_dataset.pii`` wrapper (which itself does
    the spec_from_file_location direct-load fallback). Falls back to
    the bespoke direct-loader only if e7m_dataset is not importable
    (e.g. when this script is run from a checkout with the wrapper
    module missing).
    """
    try:
        from e7m_dataset.pii import redact_payload  # type: ignore
        return redact_payload
    except ImportError:
        pass

    # Legacy fallback path — preserved so the standalone script keeps
    # working from any checkout that pre-dates the e7m_dataset.pii
    # canonical wrapper. Same direct-load semantics as the wrapper.
    src = _find_kotodama_src()
    if src is None:
        raise CorpusAssemblyError(
            "Could not locate kotodama source. Set ETZ_PYKOTODAMA_SRC "
            "or run from inside the etzhayyim-root tree, or install "
            "e7m_dataset (which exposes the canonical wrapper)."
        )
    base_mod = _direct_load(
        "_corpus_assembler_kotodama_base",
        src / "kotodama/organism/sensors/base.py",
    )
    src_text = (src / "kotodama/organism/sensors/pii_filter.py").read_text(encoding="utf-8")
    src_text = src_text.replace(
        "from .base import PiiFilterPolicy",
        "from _corpus_assembler_kotodama_base import PiiFilterPolicy",
    )
    import importlib.util
    spec = importlib.util.spec_from_loader(
        "_corpus_assembler_pii_filter", loader=None,
    )
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    sys.modules["_corpus_assembler_pii_filter"] = mod
    exec(compile(src_text, str(src / "kotodama/organism/sensors/pii_filter.py"), "exec"), mod.__dict__)
    return mod.redact_payload


def _resolve_annex_root(cli_override: Path | None) -> Path | None:
    if cli_override is not None:
        return cli_override.resolve()
    env = os.environ.get("ETZ_DATASET_ROOT")
    if env:
        return (Path(env) / "annex-store").resolve()
    return None


def _resolve_out_dir(recipe: Recipe, cli_override: Path | None) -> Path:
    if cli_override is not None:
        return cli_override.resolve()
    root = os.environ.get("ETZ_DATASET_ROOT")
    if root:
        return (Path(root) / "datasets-staging" / recipe.output_subdataset).resolve()
    # Fallback: write under the recipe's own parent dir.
    base = (recipe.recipe_path or Path.cwd()).parent
    return (base / "assembled" / recipe.output_subdataset).resolve()


def _find_source_shards(
    annex_root: Path,
    subdataset: str,
    shard_glob: str,
) -> list[Path]:
    """Resolve shards for `<annex_root>/<subdataset>/<latest-snap>/<shard_glob>`.

    The snapshot directory is the most-recent (lexicographic) subdir,
    matching the sensors' ``_resolve_*_path`` convention. Multi-snapshot
    sources will get a follow-up wave that respects a pin's
    cid_map_cid — for W3's full-path landing, latest-snapshot is the
    contract.
    """
    subdir = annex_root / subdataset
    if not subdir.exists():
        raise CorpusAssemblyError(
            f"subdataset '{subdataset}' not present at {subdir}"
        )
    snapshots = sorted(
        (p for p in subdir.iterdir() if p.is_dir()),
        reverse=True,
    )
    if not snapshots:
        raise CorpusAssemblyError(
            f"no snapshot directory under {subdir}"
        )
    latest = snapshots[0]
    shards = sorted(latest.glob(shard_glob))
    if not shards:
        raise CorpusAssemblyError(
            f"no shards matching '{shard_glob}' in {latest}"
        )
    return shards


def _iter_ndjson_rows(path: Path) -> Iterator[dict]:
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            try:
                yield json.loads(s)
            except json.JSONDecodeError:
                continue


def _emit_corpus_row(
    out_fh,
    *,
    source: SourceSpec,
    payload: dict,
    pin_revision: str,
    internal_only: bool,
) -> int:
    """Write one corpus row. Returns the number of bytes written
    (line + trailing newline). Used by the byte-cap accounting path."""
    row = {
        "v": SCHEMA_VERSION,
        "source": source.subdataset,
        "license": source.license,
        "tier": source.tier,
        "internal_only": internal_only,
        "pinRevision": pin_revision,
        "payload": payload,
    }
    line = json.dumps(row, ensure_ascii=False, separators=(",", ":"))
    encoded_len = len(line.encode("utf-8")) + 1  # +1 for the trailing "\n"
    out_fh.write(line)
    out_fh.write("\n")
    return encoded_len


def _slug_for(subdataset: str) -> str:
    return subdataset.replace("/", "__").replace(":", "_")


def assemble(
    recipe: Recipe,
    *,
    annex_root: Path,
    out_dir: Path,
    max_rows_per_source: int = 0,
    max_bytes_per_source: int = 0,
) -> dict[str, Any]:
    """Run the full assembly path. Returns a manifest dict.

    ``max_rows_per_source`` (default 0 = no cap) caps row emission
    per source. Per-source override available via
    ``SourceSpec.max_rows`` (recipe field ``max_rows``) which takes
    precedence over the global cap. Useful for partial corpora from
    huge sources (e.g. RIPE-RIS bview NDJSON sidecars).

    ``max_bytes_per_source`` (default 0 = no cap) caps emitted output
    bytes per source. Per-source override available via
    ``SourceSpec.max_bytes`` (recipe field ``max_bytes``). When both
    row and byte caps are active, whichever fires first wins —
    accounting checks happen on the same per-row boundary.
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    charter_scan = _try_import_charter_scanner()
    redact_payload = _try_import_pii_filter()

    started_at = datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z")
    per_source: list[dict[str, Any]] = []

    for src in recipe.sources:
        shards = _find_source_shards(annex_root, src.subdataset, src.shard_glob)
        # Pin revision = sha256 of the first shard's first 1 MiB. The
        # real datasetPin lookup will land in a follow-up wave; this is
        # the placeholder that the assembler uses so downstream
        # readers have *some* immutable signal of which bytes went in.
        first_bytes = shards[0].read_bytes()[: 1024 * 1024]
        pin_revision = "sha256:" + hashlib.sha256(first_bytes).hexdigest()

        out_shard = out_dir / f"{_slug_for(src.subdataset)}.ndjson"
        rows_emitted = 0
        bytes_emitted = 0
        rows_scanned_for_charter = 0
        pii_redactions = 0
        charter_violations: list[dict] = []
        internal_only = (src.tier == "C")
        is_ndjson = any(
            s.suffix == ".ndjson" or s.name.endswith(".ndjson") for s in shards
        )

        # Effective row/byte caps for this source: per-source override
        # > CLI flag > 0 (unbounded). 0 means "no cap".
        effective_cap = src.max_rows if src.max_rows > 0 else max_rows_per_source
        effective_byte_cap = (
            src.max_bytes if src.max_bytes > 0 else max_bytes_per_source
        )

        def _cap_reached() -> bool:
            """True once either cap is met. Closes over the per-source
            counters; recomputed at every check point."""
            if effective_cap > 0 and rows_emitted >= effective_cap:
                return True
            if effective_byte_cap > 0 and bytes_emitted >= effective_byte_cap:
                return True
            return False

        with out_shard.open("w", encoding="utf-8") as out_fh:
            for shard in shards:
                # Per-source caps shortcut at the outer shard loop too.
                if _cap_reached():
                    break
                # NDJSON-like: one JSON object per line.
                # `.geojsonl` / `.geojsonseq` are also NDJSON-shaped
                # (RFC 8142 may RS-prefix records but json.loads
                # tolerates that). `.jsonl` is the colloquial form.
                if shard.suffix.lower() in (".ndjson", ".jsonl", ".geojsonl", ".geojsonseq"):
                    for i, payload in enumerate(_iter_ndjson_rows(shard)):
                        # Per-source caps: stop emitting once either cap
                        # is reached. The check is here (before any
                        # other work) so capped rows incur zero PII/
                        # Charter overhead.
                        if _cap_reached():
                            break
                        # PII filter on every row (autodetect string fields).
                        redacted, stats = redact_payload(payload)
                        pii_redactions += stats.total
                        # Charter scan on a sample.
                        if i % _CHARTER_SAMPLE_EVERY == 0:
                            sample = _payload_to_text(redacted)
                            sample_path = (
                                out_dir / ".charter-sample" /
                                f"{_slug_for(src.subdataset)}-{i}.txt"
                            )
                            sample_path.parent.mkdir(parents=True, exist_ok=True)
                            sample_path.write_text(sample, encoding="utf-8")
                            res = charter_scan([sample_path], kind="reference")
                            sample_path.unlink(missing_ok=True)
                            rows_scanned_for_charter += 1
                            if not res.get("passed", True):
                                charter_violations.extend(res.get("violations", []))
                                if len(charter_violations) >= 3:
                                    raise CorpusAssemblyError(
                                        f"Charter Rider §2 violations in source "
                                        f"'{src.subdataset}' "
                                        f"(showing first 3): "
                                        f"{json.dumps(charter_violations[:3])}"
                                    )
                        n_bytes = _emit_corpus_row(
                            out_fh,
                            source=src,
                            payload=redacted,
                            pin_revision=pin_revision,
                            internal_only=internal_only,
                        )
                        rows_emitted += 1
                        bytes_emitted += n_bytes
                elif is_ndjson is False and shard.suffix.lower() in (".zone", ".txt"):
                    if _cap_reached():
                        continue
                    # Treat as a single opaque payload row; the operator
                    # is responsible for downstream parsing.
                    text = shard.read_text(encoding="utf-8", errors="replace")
                    redacted_text, stats = redact_payload({"text": text}, fields=["text"])
                    pii_redactions += stats.total
                    n_bytes = _emit_corpus_row(
                        out_fh,
                        source=src,
                        payload={
                            "kind": "opaque",
                            "filename": shard.name,
                            "text": redacted_text["text"],
                        },
                        pin_revision=pin_revision,
                        internal_only=internal_only,
                    )
                    rows_emitted += 1
                    bytes_emitted += n_bytes
                # Other binary formats (mmdb, .gz, .bz2, .parquet, .pbf)
                # are NOT streamed inline — a sensor-driven path handles
                # them. The assembler records that the source was seen
                # but does not emit per-row entries from binary blobs.

        per_source.append({
            "subdataset": src.subdataset,
            "description": src.description,
            "tier": src.tier,
            "license": src.license,
            "weight": src.weight,
            "internalOnly": internal_only,
            "pinRevision": pin_revision,
            "shardCount": len(shards),
            "rowsEmitted": rows_emitted,
            "bytesEmitted": bytes_emitted,
            "rowsScannedForCharter": rows_scanned_for_charter,
            "piiRedactions": pii_redactions,
            "effectiveRowCap": effective_cap,
            "capHit": effective_cap > 0 and rows_emitted >= effective_cap,
            "effectiveByteCap": effective_byte_cap,
            "byteCapHit": (
                effective_byte_cap > 0 and bytes_emitted >= effective_byte_cap
            ),
            "outShard": str(out_shard),
        })

    # Seed block.
    seed_emitted = 0
    seed_path_out: str | None = None
    if recipe.seed_block is not None and recipe.seed_block.seed_path.exists():
        seed_dst = out_dir / "seed.jsonl"
        shutil.copy2(recipe.seed_block.seed_path, seed_dst)
        seed_path_out = str(seed_dst)
        seed_emitted = sum(
            1 for _ in seed_dst.open("r", encoding="utf-8") if _.strip()
        )

    finished_at = datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z")
    manifest = {
        "v": SCHEMA_VERSION,
        "targetArtifact": recipe.target_artifact,
        "outputSubdataset": recipe.output_subdataset,
        "description": recipe.description,
        "outputMetadata": recipe.output_metadata,
        "computedMaxTier": recipe.computed_max_tier,
        "maxTierCap": recipe.max_tier_cap,
        "startedAt": started_at,
        "finishedAt": finished_at,
        "sources": per_source,
        "seedBlock": {
            "weight": recipe.seed_block.weight if recipe.seed_block else None,
            "emittedRows": seed_emitted,
            "path": seed_path_out,
            "sourcePathExisted": (
                recipe.seed_block.seed_path.exists()
                if recipe.seed_block else False
            ),
        } if recipe.seed_block else None,
        "outDir": str(out_dir),
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return manifest


def _payload_to_text(payload: dict) -> str:
    """Flatten a payload dict to a single text blob for Charter scanning.

    Just joins all string-typed scalar values + JSON-dumped non-scalars.
    """
    parts: list[str] = []
    for k, v in payload.items():
        if isinstance(v, str):
            parts.append(v)
        else:
            try:
                parts.append(json.dumps(v, ensure_ascii=False))
            except (TypeError, ValueError):
                parts.append(repr(v))
    return "\n".join(parts)


if __name__ == "__main__":
    raise SystemExit(main())
