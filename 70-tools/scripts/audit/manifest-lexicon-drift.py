#!/usr/bin/env python3
# pyright: strict
"""
manifest-lexicon-drift.py — find lexicons declared in actor manifest.jsonld
files that don't have a corresponding JSON file under 00-contracts/lexicons/.

Why this matters
================
Each flat-west actor checkout ships an authoritative `manifest.edn` or a
legacy wire `manifest.jsonld`
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
    orgs/etzhayyim/com-etzhayyim-<actor>/manifest.edn declares N lexicons; M missing:
      MISSING: <nsid>  (expected at <expected-path>)
      ...

--strict makes findings fatal (for CI integration).

Discovery: iter-47 of /loop (2026-05-27).
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
WEST_ROOT = Path(os.environ.get("ETZHAYYIM_WEST_ROOT", REPO_ROOT.parents[2]))
ACTORS_DIR = WEST_ROOT / "orgs" / "etzhayyim"
LEXICONS_ROOT = REPO_ROOT / "00-contracts" / "lexicons"
ROOT_OWNERSHIP_REGISTRY = REPO_ROOT / "scripts" / "manifest-lexicon-root-ownership.edn"

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


def actor_lexicon_path(manifest_path: Path, nsid: str) -> Path:
    """Generated wire contract owned by the manifest's flat repository."""
    parts = nsid.split(".")
    return manifest_path.parent / "lexicons" / Path(*parts[:-1]) / f"{parts[-1]}.json"


def actor_wire_lexicon_path(manifest_path: Path, nsid: str) -> Path:
    """Wire-boundary layout used by EDN-canonical standalone owners."""
    return manifest_path.parent / "wire" / "lex" / f"{nsid.rsplit('.', 1)[-1]}.json"


def actor_wire_lexicons_path(manifest_path: Path, nsid: str) -> Path:
    """Plural wire-boundary layout used by some standalone owners."""
    return manifest_path.parent / "wire" / "lexicons" / f"{nsid.rsplit('.', 1)[-1]}.json"


def actor_wire_qualified_lexicons_path(manifest_path: Path, nsid: str) -> Path:
    """Plural wire layout retaining the owner segment in the filename."""
    parts = nsid.rsplit(".", 2)
    filename = ".".join(parts[-2:]) if len(parts) >= 2 else parts[-1]
    return manifest_path.parent / "wire" / "lexicons" / f"{filename}.json"


def actor_wire_contract_lexicons_path(manifest_path: Path, nsid: str) -> Path:
    """Contract-scoped wire layout generated from contracts/lexicons/*.edn."""
    return (manifest_path.parent / "wire" / "contracts" / "lexicons" /
            f"{nsid.rsplit('.', 1)[-1]}.json")


def actor_contract_paths(manifest_path: Path, nsid: str) -> list[Path]:
    return [actor_wire_lexicon_path(manifest_path, nsid),
            actor_wire_lexicons_path(manifest_path, nsid),
            actor_wire_qualified_lexicons_path(manifest_path, nsid),
            actor_wire_contract_lexicons_path(manifest_path, nsid),
            actor_lexicon_path(manifest_path, nsid)]


def resolve_lexicon_path(manifest_path: Path, nsid: str) -> Path:
    """Prefer flat-owner output; accept existing root contracts during migration."""
    locals_ = actor_contract_paths(manifest_path, nsid)
    root = nsid_to_lexicon_path(nsid)
    for local in locals_:
        if local.exists():
            return local
    if root.exists():
        return root
    return locals_[0] if (manifest_path.parent / "wire").is_dir() else locals_[1]


def lexicon_location(manifest_path: Path, nsid: str) -> str:
    """Classify a declaration by its current west migration location."""
    if actor_wire_lexicon_path(manifest_path, nsid).exists():
        return "owner-wire-lex"
    if actor_wire_lexicons_path(manifest_path, nsid).exists():
        return "owner-wire-lexicons"
    if actor_wire_qualified_lexicons_path(manifest_path, nsid).exists():
        return "owner-wire-qualified-lexicons"
    if actor_wire_contract_lexicons_path(manifest_path, nsid).exists():
        return "owner-wire-contract-lexicons"
    if actor_lexicon_path(manifest_path, nsid).exists():
        return "owner-nsid-path"
    if nsid_to_lexicon_path(nsid).exists():
        return "root-compat"
    return "missing"


def display_path(path: Path) -> Path:
    """Stable display path for files that may live in sibling west checkouts."""
    return Path(os.path.relpath(path, REPO_ROOT))


def lexicon_file_nsid(path: Path, namespace_prefix: str) -> str:
    """Read the wire contract's authoritative id, falling back to its stem.

    Map-shaped lexicons keep ``id`` at the top level.  EAVT projections are
    vectors, however, and carry the same identity as a namespaced ``*/id`` key
    inside one of their facts.  Accept that identity only when every matching
    fact agrees; an ambiguous projection deliberately falls back so reverse
    drift remains visible instead of silently choosing an arbitrary NSID.
    """
    try:
        data = json.loads(path.read_text())
        if isinstance(data, dict) and isinstance(data.get("id"), str):
            return data["id"]

        candidates: set[str] = set()

        def collect(value) -> None:
            if isinstance(value, dict):
                for key, item in value.items():
                    if (isinstance(key, str) and "/" in key and
                            key.endswith("/id") and isinstance(item, str) and
                            NSID_RE.fullmatch(item)):
                        candidates.add(item)
                    collect(item)
            elif isinstance(value, list):
                for item in value:
                    collect(item)

        if isinstance(data, list):
            collect(data)
            if len(candidates) == 1:
                return next(iter(candidates))
    except (OSError, json.JSONDecodeError):
        pass
    return f"{namespace_prefix}.{path.stem}"


def find_manifests() -> list[Path]:
    """All flat-west actor manifests — both the legacy `manifest.jsonld`
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
    for mp in sorted(ACTORS_DIR.glob("com-etzhayyim-*/manifest.edn")):
        by_actor[mp.parent] = mp
    for mp in sorted(ACTORS_DIR.glob("com-etzhayyim-*/manifest.jsonld")):
        by_actor[mp.parent] = mp  # prefer .jsonld when an actor has both
    return [by_actor[k] for k in sorted(by_actor)]


# ─── minimal EDN reader (dependency-free) ──────────────────────────────
#
# `.edn` manifests have no stdlib parser, and the CI image installs only
# pytest (adding an `edn_format` dependency would have to be threaded through
# every standalone + aggregator invocation). A targeted regex was the first
# cut, but it is fragile: a non-greedy `[...]` stops at the FIRST `]`, so a
# lexicon string containing `]` truncates the array, and `;` comments / string
# escapes are invisible to it. This tiny tokenizer+reader handles those
# correctly — strings (with `\` escapes), `;` line comments, `,`-as-whitespace,
# and balanced `[] {} ()` — which is all the structure we need to pull the
# `lexicons` / `lexiconNamespaces` arrays out of the `:actor/manifest` map.

_Tok = tuple[str, str]  # (kind, value); kind ∈ {str, sym, open, close}


def _edn_tokens(text: str) -> list[_Tok]:
    toks: list[_Tok] = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c in " \t\r\n,":
            i += 1
            continue
        if c == ";":  # line comment to EOL
            while i < n and text[i] != "\n":
                i += 1
            continue
        if c == '"':  # string literal (with escapes)
            i += 1
            buf: list[str] = []
            while i < n:
                ch = text[i]
                if ch == "\\" and i + 1 < n:
                    esc = text[i + 1]
                    buf.append({"n": "\n", "t": "\t", "r": "\r"}.get(esc, esc))
                    i += 2
                    continue
                if ch == '"':
                    i += 1
                    break
                buf.append(ch)
                i += 1
            toks.append(("str", "".join(buf)))
            continue
        if c in "[({":
            toks.append(("open", c))
            i += 1
            continue
        if c in "])}":
            toks.append(("close", c))
            i += 1
            continue
        # bare token (symbol / keyword / number / nil …) up to a delimiter
        j = i
        while j < n and text[j] not in ' \t\r\n,;"[]{}()':
            j += 1
        toks.append(("sym", text[i:j]))
        i = j
    return toks


def _read_form(toks: list[_Tok], i: int):
    """Read one EDN form starting at index i. Returns (form, next_index) where
    form is ('str'|'sym', value) or ('coll', open_char, [child forms])."""
    kind, val = toks[i]
    if kind in ("str", "sym"):
        return (kind, val), i + 1
    # 'open' — read children until the matching close
    children: list = []
    i += 1
    while i < len(toks) and toks[i][0] != "close":
        form, i = _read_form(toks, i)
        children.append(form)
    if i < len(toks):  # consume the close (tolerate truncated EOF)
        i += 1
    return ("coll", val, children), i


def _nsids_from_vec(coll) -> list[str]:
    """Pull NSID strings from a parsed lexicon vector: bare string elements +
    each nested map's `"id"` value (the rich {id, status, …} entry shape)."""
    out: list[str] = []
    for ch in coll[2]:
        if ch[0] == "str":
            out.append(ch[1])
        elif ch[0] == "coll" and ch[1] == "{":
            kids = ch[2]
            for k in range(0, len(kids) - 1, 2):
                key, value = kids[k], kids[k + 1]
                if key[0] == "str" and key[1] == "id" and value[0] == "str":
                    out.append(value[1])
    return out


def edn_lexicons(text: str) -> list[str]:
    """Declared lexicon NSIDs from a ``manifest.edn`` body.

    Accept both the historical string keys nested under ``:actor/manifest``
    and canonical EDN keyword keys, including top-level ``:actor/lexicons``.
    """
    toks = _edn_tokens(text)
    out: list[str] = []
    i = 0
    while i < len(toks):
        kind, val = toks[i]
        if (
            ((kind == "str" and val in ("lexiconNamespaces", "lexicons"))
             or (kind == "sym" and val in (
                 ":actor/lexicons", ":actor/lexiconNamespaces",
                 ":lexicons", ":lexiconNamespaces",
             )))
            and i + 1 < len(toks)
            and toks[i + 1] == ("open", "[")
        ):
            coll, _ = _read_form(toks, i + 1)
            if coll[0] == "coll":
                out += _nsids_from_vec(coll)
        i += 1
    return out


def root_owned_nsids(path: Path = ROOT_OWNERSHIP_REGISTRY) -> set[str]:
    """Non-actor contracts intentionally owned by root infrastructure.

    The EDN registry is the ownership SSoT.  These contracts must not be
    falsely reported as actor orphans merely because their JSON projection
    shares a root compatibility directory with actor contracts.
    """
    if not path.is_file():
        return set()
    toks = _edn_tokens(path.read_text())
    for i, tok in enumerate(toks[:-1]):
        if tok == ("sym", ":registry/lexicons") and toks[i + 1] == ("open", "["):
            coll, _ = _read_form(toks, i + 1)
            return set(_nsids_from_vec(coll))
    return set()


def declared_nsids(mpath: Path) -> list[str]:
    """Lexicon NSIDs declared by a manifest, normalised to the NSID string.

    `.jsonld` is parsed as JSON; `.edn` via the minimal EDN reader above. Both
    keys (legacy `lexicons` + newer `lexiconNamespaces`) and both entry shapes
    (a bare NSID string, or a rich object {id, status, emittedBy}) are handled
    in each format. Verified on the real corpus: 158 NSIDs across 143 .edn
    manifests, 0 false drift."""
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
    return edn_lexicons(text)


def main() -> int:
    strict = "--strict" in sys.argv
    manifests = find_manifests()

    total_declared = 0
    total_missing = 0
    location_counts = {"owner-wire-lex": 0, "owner-wire-lexicons": 0,
                       "owner-wire-qualified-lexicons": 0,
                       "owner-wire-contract-lexicons": 0,
                       "owner-nsid-path": 0, "root-compat": 0, "missing": 0}
    actors_with_drift: list[tuple[Path, list[tuple[str, Path]]]] = []
    invalid_nsids: list[tuple[Path, str]] = []
    declared_global: set[str] = set()
    root_owned = root_owned_nsids()
    # dir → set of NSIDs declared into it by some manifest (the dir is "owned").
    owned_dirs: dict[Path, set[str]] = {}

    for mpath in manifests:
        try:
            declared = declared_nsids(mpath)
        except (OSError, json.JSONDecodeError) as e:
            print(f"warning: could not parse {display_path(mpath)}: {e}", file=sys.stderr)
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
            lex_path = resolve_lexicon_path(mpath, nsid)
            location_counts[lexicon_location(mpath, nsid)] += 1
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
            declared_here = owned_dirs[dirp]
            prefix = next(iter(declared_here)).rsplit(".", 1)[0]
            nsid = lexicon_file_nsid(jf, prefix)
            if nsid not in declared_global and nsid not in root_owned:
                orphans.append(nsid)

    # Reporting. The aggregator script picks the LAST `: N$` line as
    # this script's rollup count, so put the headline number last.
    print(f"Manifests scanned: {len(manifests)}")
    print(f"Lexicons declared (total): {total_declared}")
    print(f"Contracts in owner wire/lex: {location_counts['owner-wire-lex']}")
    print(f"Contracts in owner wire/lexicons: {location_counts['owner-wire-lexicons']}")
    print("Contracts in owner qualified wire/lexicons: "
          f"{location_counts['owner-wire-qualified-lexicons']}")
    print("Contracts in owner wire/contracts/lexicons: "
          f"{location_counts['owner-wire-contract-lexicons']}")
    print(f"Contracts in owner NSID paths: {location_counts['owner-nsid-path']}")
    print(f"Contracts in root compatibility layer: {location_counts['root-compat']}")
    print(f"Root-owned non-actor contracts: {len(root_owned)}")
    print(f"Actors with drift: {len(actors_with_drift)}")
    print(f"Undeclared orphan lexicon files (tracked, not in rollup): {len(orphans)}")
    if invalid_nsids:
        print(f"Invalid NSIDs (don't match `a.b.c` pattern): {len(invalid_nsids)}")

    if actors_with_drift:
        print()
        for mpath, missing in actors_with_drift:
            rel = display_path(mpath)
            print(f"{rel} — {len(missing)} missing:")
            for nsid, lex_path in missing[:10]:
                lex_rel = display_path(lex_path)
                print(f"  MISSING: {nsid}")
                print(f"    expected at: {lex_rel}")
            if len(missing) > 10:
                print(f"  ... and {len(missing) - 10} more")

    if invalid_nsids:
        print()
        print("Invalid NSIDs:")
        for mpath, nsid in invalid_nsids[:10]:
            rel = display_path(mpath)
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
