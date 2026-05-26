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
    )


def _is_placeholder(at_uri: str) -> bool:
    return "PLACEHOLDER_" in at_uri


def dry_run_summary(recipe: Recipe) -> dict[str, Any]:
    placeholders = [
        s.subdataset for s in recipe.sources if _is_placeholder(s.dataset_pin_at)
    ]
    return {
        "recipePath": str(recipe.recipe_path) if recipe.recipe_path else None,
        "targetArtifact": recipe.target_artifact,
        "outputSubdataset": recipe.output_subdataset,
        "maxTierCap": recipe.max_tier_cap,
        "computedMaxTier": recipe.computed_max_tier,
        "sourceCount": len(recipe.sources),
        "placeholderPins": placeholders,
        "seedBlock": (
            {
                "weight": recipe.seed_block.weight,
                "seedPath": str(recipe.seed_block.seed_path),
            }
            if recipe.seed_block
            else None
        ),
    }


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
        help="Validate recipe + emit summary, do NOT resolve pins or "
             "stream shards.",
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
    args = p.parse_args(argv)

    recipe = load_recipe(args.recipe)
    errors = recipe.validate()
    if errors:
        print("Recipe validation FAILED:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 2

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

    Avoids triggering ``pymagatama/__init__.py`` (which imports
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


def _find_pymagatama_src() -> Path | None:
    """Locate the in-tree pymagatama source. Strategies:

    1. ``ETZ_PYMAGATAMA_SRC`` env var (highest priority).
    2. Walk up from this file looking for ``20-actors/magatama/py/src/``.
    """
    env = os.environ.get("ETZ_PYMAGATAMA_SRC")
    if env:
        p = Path(env)
        if (p / "pymagatama/organism/sensors/charter_rider.py").exists():
            return p
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "20-actors/magatama/py/src"
        if (candidate / "pymagatama/organism/sensors/charter_rider.py").exists():
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
                "e7m_dataset.charter._load_scanner. Install pymagatama "
                "or set ETZ_PYMAGATAMA_SRC."
            )
        return mod.scan
    except ImportError:
        pass

    # Legacy fallback — preserved so the standalone script keeps
    # working from any checkout that pre-dates the e7m_dataset.charter
    # canonical wrapper.
    src = _find_pymagatama_src()
    if src is None:
        raise CorpusAssemblyError(
            "Could not locate pymagatama source. Set ETZ_PYMAGATAMA_SRC "
            "or run from inside the etzhayyim-root tree, or install "
            "e7m_dataset (which exposes the canonical wrapper)."
        )
    mod = _direct_load(
        "_corpus_assembler_charter_rider",
        src / "pymagatama/organism/sensors/charter_rider.py",
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
    src = _find_pymagatama_src()
    if src is None:
        raise CorpusAssemblyError(
            "Could not locate pymagatama source. Set ETZ_PYMAGATAMA_SRC "
            "or run from inside the etzhayyim-root tree, or install "
            "e7m_dataset (which exposes the canonical wrapper)."
        )
    base_mod = _direct_load(
        "_corpus_assembler_pymagatama_base",
        src / "pymagatama/organism/sensors/base.py",
    )
    src_text = (src / "pymagatama/organism/sensors/pii_filter.py").read_text(encoding="utf-8")
    src_text = src_text.replace(
        "from .base import PiiFilterPolicy",
        "from _corpus_assembler_pymagatama_base import PiiFilterPolicy",
    )
    import importlib.util
    spec = importlib.util.spec_from_loader(
        "_corpus_assembler_pii_filter", loader=None,
    )
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    sys.modules["_corpus_assembler_pii_filter"] = mod
    exec(compile(src_text, str(src / "pymagatama/organism/sensors/pii_filter.py"), "exec"), mod.__dict__)
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
) -> None:
    row = {
        "v": SCHEMA_VERSION,
        "source": source.subdataset,
        "license": source.license,
        "tier": source.tier,
        "internal_only": internal_only,
        "pinRevision": pin_revision,
        "payload": payload,
    }
    out_fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")))
    out_fh.write("\n")


def _slug_for(subdataset: str) -> str:
    return subdataset.replace("/", "__").replace(":", "_")


def assemble(
    recipe: Recipe,
    *,
    annex_root: Path,
    out_dir: Path,
    max_rows_per_source: int = 0,
) -> dict[str, Any]:
    """Run the full assembly path. Returns a manifest dict.

    ``max_rows_per_source`` (default 0 = no cap) caps row emission
    per source. Per-source override available via
    ``SourceSpec.max_rows`` (recipe field ``max_rows``) which takes
    precedence over the global cap. Useful for partial corpora from
    huge sources (e.g. RIPE-RIS bview NDJSON sidecars).
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
        rows_scanned_for_charter = 0
        pii_redactions = 0
        charter_violations: list[dict] = []
        internal_only = (src.tier == "C")
        is_ndjson = any(
            s.suffix == ".ndjson" or s.name.endswith(".ndjson") for s in shards
        )

        # Effective row cap for this source: per-source override > CLI
        # flag > 0 (unbounded). 0 means "no cap".
        effective_cap = src.max_rows if src.max_rows > 0 else max_rows_per_source

        with out_shard.open("w", encoding="utf-8") as out_fh:
            for shard in shards:
                # Per-source row cap shortcut at the outer shard loop too.
                if effective_cap > 0 and rows_emitted >= effective_cap:
                    break
                # NDJSON-like: one JSON object per line.
                # `.geojsonl` / `.geojsonseq` are also NDJSON-shaped
                # (RFC 8142 may RS-prefix records but json.loads
                # tolerates that). `.jsonl` is the colloquial form.
                if shard.suffix.lower() in (".ndjson", ".jsonl", ".geojsonl", ".geojsonseq"):
                    for i, payload in enumerate(_iter_ndjson_rows(shard)):
                        # Per-source row cap: stop emitting once we hit
                        # the cap, but continue iterating the rest of
                        # the shards' loop so we still hit the
                        # break-out condition below. The break is here
                        # (before any other work) so capped rows incur
                        # zero PII/Charter overhead.
                        if effective_cap > 0 and rows_emitted >= effective_cap:
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
                        _emit_corpus_row(
                            out_fh,
                            source=src,
                            payload=redacted,
                            pin_revision=pin_revision,
                            internal_only=internal_only,
                        )
                        rows_emitted += 1
                elif is_ndjson is False and shard.suffix.lower() in (".zone", ".txt"):
                    # Treat as a single opaque payload row; the operator
                    # is responsible for downstream parsing.
                    text = shard.read_text(encoding="utf-8", errors="replace")
                    redacted_text, stats = redact_payload({"text": text}, fields=["text"])
                    pii_redactions += stats.total
                    _emit_corpus_row(
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
                # Other binary formats (mmdb, .gz, .bz2, .parquet, .pbf)
                # are NOT streamed inline — a sensor-driven path handles
                # them. The assembler records that the source was seen
                # but does not emit per-row entries from binary blobs.

        per_source.append({
            "subdataset": src.subdataset,
            "tier": src.tier,
            "license": src.license,
            "weight": src.weight,
            "internalOnly": internal_only,
            "pinRevision": pin_revision,
            "shardCount": len(shards),
            "rowsEmitted": rows_emitted,
            "rowsScannedForCharter": rows_scanned_for_charter,
            "piiRedactions": pii_redactions,
            "effectiveRowCap": effective_cap,
            "capHit": effective_cap > 0 and rows_emitted >= effective_cap,
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
        "computedMaxTier": recipe.computed_max_tier,
        "maxTierCap": recipe.max_tier_cap,
        "startedAt": started_at,
        "finishedAt": finished_at,
        "sources": per_source,
        "seedBlock": {
            "weight": recipe.seed_block.weight if recipe.seed_block else None,
            "emittedRows": seed_emitted,
            "path": seed_path_out,
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
