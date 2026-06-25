#!/usr/bin/env python3
# pyright: strict
"""
manifest-lexicon-drift.py — find lexicons declared in actor manifest.jsonld
files that don't have a corresponding JSON file under 00-contracts/lexicons/.

Why this matters
================
Each Tier-B actor under `20-actors/<actor>/` ships a `manifest.jsonld`
that declares which lexicons the actor implements:

    "lexicons": [
      "com.etzhayyim.supply.supplierSelection",
      "com.etzhayyim.supply.purchaseOrder",
      ...
    ]

By convention the NSID `com.etzhayyim.X.Y` maps to the file
`00-contracts/lexicons/com/etzhayyim/X/Y.json`. When the JSON file
doesn't exist, the actor's contract surface is incomplete — clients
can't validate writes/reads against a schema that isn't there.

This drift accumulates because actor manifests are often authored
ahead of the lexicon JSON files (the manifest is the planning
artifact; the JSON is the implementation). Without an audit, the
drift is silent — a new actor could ship with 0 of N declared
lexicons actually existing and no test would catch it.

Distinguished from `nsid-lexicon-exists.mjs` (pre-existing lefthook
lint): that linter only scans static code patterns like
`atProcedure("nsid")` / `atQuery("nsid")` / `.api.call("nsid")`. It
does NOT inspect manifest.jsonld declarations. This audit covers the
declaration gap.

Output
======
For each manifest with missing lexicons, prints:
    20-actors/<actor>/manifest.jsonld declares N lexicons; M missing:
      MISSING: <nsid>  (expected at <expected-path>)
      ...

--strict makes findings fatal (for CI integration).

Discovery: iter-47 of /loop (2026-05-27).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
ACTORS_DIR = REPO_ROOT / "20-actors"
LEXICONS_ROOT = REPO_ROOT / "00-contracts" / "lexicons"

# NSID convention check — at least 3 dot-segments (e.g. com.etzhayyim.X.Y).
# Per AT Protocol Lexicon spec the last segment is camelCase/PascalCase
# (a type identifier), while domain segments are reverse-domain lowercase.
# This repo also uses camelCase in some MIDDLE segments (e.g. `kuniUmi`),
# so we accept mixed case in any segment for the existence check — the
# audit's job is "does the corresponding file exist", not "is the NSID
# strict-spec-compliant" (that's a separate concern).
NSID_RE = re.compile(r"^[a-z][a-zA-Z0-9-]*(?:\.[a-zA-Z][a-zA-Z0-9-]*){2,}$")


def nsid_to_lexicon_path(nsid: str) -> Path:
    """Convert `com.etzhayyim.X.Y` to `00-contracts/lexicons/com/etzhayyim/X/Y.json`."""
    parts = nsid.split(".")
    return LEXICONS_ROOT / Path(*parts[:-1]) / f"{parts[-1]}.json"


def find_manifests() -> list[Path]:
    """All actor manifests under 20-actors/ — both the legacy `manifest.jsonld`
    and the migrated `manifest.edn` (the jsonld→edn / py→cljc wave). One manifest
    per actor dir; when an actor (transiently) ships both, the `.jsonld` wins.

    Before this, the audit globbed only `manifest.jsonld` and so went silently
    blind to the 140+ actors that migrated to `manifest.edn` — exactly the
    "silent drift" this script exists to prevent. The `.edn` manifest carries
    the original jsonld content under the `:actor/manifest` key (string-keyed),
    including the `lexicons` / `lexiconNamespaces` arrays (see declared_nsids)."""
    if not ACTORS_DIR.is_dir():
        return []
    by_actor: dict[Path, Path] = {}
    for mp in sorted(ACTORS_DIR.glob("*/manifest.edn")):
        by_actor[mp.parent] = mp
    for mp in sorted(ACTORS_DIR.glob("*/manifest.jsonld")):
        by_actor[mp.parent] = mp  # prefer .jsonld when an actor has both
    return [by_actor[k] for k in sorted(by_actor)]


def declared_nsids(mpath: Path) -> list[str]:
    """Lexicon NSIDs declared by a manifest, normalised to the NSID string.

    `.jsonld` is parsed as JSON; both the legacy `lexicons` and the newer
    `lexiconNamespaces` keys are read, and the two entry shapes — a bare NSID
    string, or a rich object {id, status, emittedBy} — are both handled.

    `.edn` has no stdlib parser (and the CI image installs only pytest), so the
    `lexicons` / `lexiconNamespaces` arrays are extracted with a targeted regex
    over the (string-keyed) `:actor/manifest` map. These arrays are flat lists
    of quoted NSID strings, so the extraction is exact for the real corpus
    (verified: 158 NSIDs across 143 .edn manifests, 0 false drift)."""
    text = mpath.read_text()
    if mpath.suffix == ".jsonld":
        data = json.loads(text)
        out: list[str] = []
        for key in ("lexicons", "lexiconNamespaces"):
            v = data.get(key, [])
            if not isinstance(v, list):
                continue
            for item in v:
                if isinstance(item, str):
                    out.append(item)
                elif isinstance(item, dict) and isinstance(item.get("id"), str):
                    out.append(item["id"])
        return out
    # .edn
    out_edn: list[str] = []
    for key in ("lexiconNamespaces", "lexicons"):
        for m in re.finditer(r'"' + key + r'"\s*\[(.*?)\]', text, re.S):
            out_edn += re.findall(r'"([a-zA-Z][\w.-]*\.[\w.-]+)"', m.group(1))
    return out_edn


def main() -> int:
    strict = "--strict" in sys.argv
    manifests = find_manifests()

    total_declared = 0
    total_missing = 0
    actors_with_drift: list[tuple[Path, list[tuple[str, Path]]]] = []
    invalid_nsids: list[tuple[Path, str]] = []
    declared_global: set[str] = set()
    # dir → set of NSIDs declared into it by some manifest (the dir is "owned").
    owned_dirs: dict[Path, set[str]] = {}

    for mpath in manifests:
        try:
            declared = declared_nsids(mpath)
        except (OSError, json.JSONDecodeError) as e:
            print(f"warning: could not parse {mpath.relative_to(REPO_ROOT)}: {e}", file=sys.stderr)
            continue
        if not declared:
            continue

        missing_in_actor: list[tuple[str, Path]] = []
        for nsid in declared:
            if not isinstance(nsid, str):
                continue
            total_declared += 1
            if not NSID_RE.match(nsid):
                invalid_nsids.append((mpath, nsid))
                continue
            declared_global.add(nsid)
            lex_path = nsid_to_lexicon_path(nsid)
            owned_dirs.setdefault(lex_path.parent, set()).add(nsid)
            if not lex_path.exists():
                missing_in_actor.append((nsid, lex_path))
                total_missing += 1

        if missing_in_actor:
            actors_with_drift.append((mpath, missing_in_actor))

    # Reverse direction: a lexicon JSON file that lives in an actor-owned dir
    # (some manifest declares into it) but is itself UNDECLARED by any manifest.
    # This is the iyashi/phlebotomyAttestation class of drift — an orphan
    # contract surface. Tracked informationally (not fed into the rollup, so the
    # aggregator baseline is unaffected); surfaced for follow-up declaration.
    orphans: list[str] = []
    for dirp in sorted(owned_dirs, key=str):
        if not dirp.is_dir():
            continue
        for jf in sorted(dirp.glob("*.json")):
            if jf.stem.startswith("_"):
                continue
            nsid = ".".join(jf.relative_to(LEXICONS_ROOT).with_suffix("").parts)
            if nsid not in declared_global:
                orphans.append(nsid)

    # Reporting. The aggregator script picks the LAST `: N$` line as
    # this script's rollup count, so put the headline number last.
    print(f"Manifests scanned: {len(manifests)}")
    print(f"Lexicons declared (total): {total_declared}")
    print(f"Actors with drift: {len(actors_with_drift)}")
    print(f"Undeclared orphan lexicon files (tracked, not in rollup): {len(orphans)}")
    if invalid_nsids:
        print(f"Invalid NSIDs (don't match `a.b.c` pattern): {len(invalid_nsids)}")

    if actors_with_drift:
        print()
        for mpath, missing in actors_with_drift:
            rel = mpath.relative_to(REPO_ROOT)
            print(f"{rel} — {len(missing)} missing:")
            for nsid, lex_path in missing[:10]:
                lex_rel = lex_path.relative_to(REPO_ROOT)
                print(f"  MISSING: {nsid}")
                print(f"    expected at: {lex_rel}")
            if len(missing) > 10:
                print(f"  ... and {len(missing) - 10} more")

    if invalid_nsids:
        print()
        print("Invalid NSIDs:")
        for mpath, nsid in invalid_nsids[:10]:
            rel = mpath.relative_to(REPO_ROOT)
            print(f"  {rel}: {nsid!r}")

    if orphans:
        print()
        print("Undeclared orphan lexicon files (exist on disk, no manifest declares them):")
        for nsid in orphans[:20]:
            print(f"  ORPHAN: {nsid}")
        if len(orphans) > 20:
            print(f"  ... and {len(orphans) - 20} more")

    # Final summary line — what the aggregator picks up. Kept as the
    # forward (declared-but-missing) count so the rollup baseline is stable;
    # orphans are tracked above but intentionally excluded from this number.
    print()
    print(f"Lexicons declared in manifest but missing as JSON file: {total_missing}")

    if strict and (actors_with_drift or invalid_nsids):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
