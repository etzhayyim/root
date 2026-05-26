#!/usr/bin/env python3
"""assemble-public-corpus.py — Wave-1 cold-path corpus assembler.

Per ADR-2605262400 §4. Wave-1 scope: Tier-A-only path. Tier-C handling
+ `-nc-` infix gate + judah LiteLLM / SBT-gate plumbing land in W3.

Usage:

    python assemble-public-corpus.py --recipe <path.toml> \\
        [--out-dir <staging-dir>] [--dry-run]

Behavior:

  1. Parse the recipe (TOML).
  2. Validate: declared `max_tier_cap` >= every source's declared tier.
  3. Compute the max tier across sources. If any source.tier == "C" and
     target_artifact has no `-nc-` infix → fail closed (G5).
  4. For each source, resolve its `datasetPin_at` (PLACEHOLDER_* values
     are accepted in --dry-run; real AT-URI lookup is W3).
  5. Stream shards through Charter Rider §2 scan + PII filter. Any
     violation = abort.
  6. Emit NDJSON shards into the output subdataset, with a
     per-row `source` + `license` + `tier` tag.
  7. Write a manifest summarizing what landed.

The Wave-1 implementation deliberately stops at step 7 — operator runs
`datalad save` + `e7m-dataset publish-ipfs` + `datasetPin emit` on the
output subdataset manually.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import tomllib  # Python 3.11+
except ImportError:  # pragma: no cover
    import tomli as tomllib  # type: ignore


TIER_ORDER = {"A": 0, "B": 1, "C": 2, "D": 3}


@dataclass
class SourceSpec:
    subdataset: str
    dataset_pin_at: str
    shard_glob: str
    tier: str
    license: str
    weight: float
    sa_propagates: bool = False


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
        "--out-dir",
        type=Path,
        default=None,
        help="Override output staging dir (default = "
             "${ETZ_DATASET_ROOT}/datasets-staging/<output_subdataset>)",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate recipe + emit summary, do NOT resolve pins or "
             "stream shards. Wave-1 default.",
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

    print(
        "Full assembly path lands in Wave-3. Use --dry-run for now.",
        file=sys.stderr,
    )
    return 4


if __name__ == "__main__":
    raise SystemExit(main())
