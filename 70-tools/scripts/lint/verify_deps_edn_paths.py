#!/usr/bin/env python3
"""verify_deps_edn_paths.py — book-keeping lint for deps.edn path entries.

deps.edn port of verify_deps_toml_paths.py (ADR-2605262500 cycle 27 / cycle
46 markers / cycle 59 duplicates; the toml→edn migration removed deps.toml
and left that verifier dead — follow-up tracked in ADR-2606121143).

Walks every map in the top-level `:adrs` and `:modules` vectors of
`deps.edn`, checks that each `:path` value resolves to an existing file or
directory under the repo root, and reports drift. Parsing reuses the
tokenizer/parser of format-deps-edn.py (same directory), so a file this
script can read is by definition valid EDN.

Reservation markers (unchanged from the toml verifier):

  :path "90-docs/adr/2605250730-tatekata-r1.md (reserved)"
  :path "00-contracts/lexicons/com/etzhayyim/apps/unispsc (deferred-rename)"

  (reserved)        — a future R-cycle will produce this path
  (deferred-rename) — intentionally pre-cutover per CLAUDE.md rename rules

A BARE missing path is drift (exit 1). A missing path WITH a marker is
"accepted-reserved" (owner-asserted, not drift). A path that exists but
still carries a marker is "stale-marker" (warning — drop the suffix).
Paths shaped as ``orgs/<configured-org>/<repo>(/...)`` are west-managed
projects.  Their checkout is intentionally optional in a root-only CI clone,
so they are classified as unverifiable external project paths, not drift.
The org allowlist is derived from ``deps.edn``'s ``:github_org_open`` config;
an arbitrary or misspelled org is never accepted.
Duplicate :modules paths / :adrs ids are reported (warning) in unfiltered
runs, mirroring the cycle-59 toml behaviour.

Usage:
  python3 70-tools/scripts/lint/verify_deps_edn_paths.py
  python3 70-tools/scripts/lint/verify_deps_edn_paths.py --json
  python3 70-tools/scripts/lint/verify_deps_edn_paths.py --filter 2606121143

Exit codes:
  0 — no drift (accepted-reserved / stale-marker / duplicate counts may be >0)
  1 — at least one drift entry (bare missing path)
  2 — usage / parse error
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

_spec = importlib.util.spec_from_file_location(
    "fde", Path(__file__).with_name("format-deps-edn.py")
)
fde = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fde)

_RESERVED_SUFFIX_RE = re.compile(r"\s+\((?P<marker>reserved|deferred-rename)\)\s*$")

BASELINE_PATH = "70-tools/scripts/lint/deps-edn-paths-baseline.json"


def submodule_roots(repo_root: Path) -> list[str]:
    """Submodule paths from .gitmodules — content of these belongs to OTHER
    repos and its presence depends on whether the checkout populated them,
    so existence checks there are non-deterministic across machines/worktrees
    (same failure mode as the substrate-remediation-audit submodule walk)."""
    gm = repo_root / ".gitmodules"
    if not gm.is_file():
        return []
    return [
        line.split("=", 1)[1].strip()
        for line in gm.read_text().splitlines()
        if line.strip().startswith("path =")
    ]


def classify_external(raw: str) -> bool:
    """URLs / home / absolute paths are not repo paths — unverifiable here."""
    return raw.startswith(("http://", "https://", "~", "/"))


_WEST_PROJECT_RE = re.compile(
    r"^orgs/(?P<org>[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)/"
    r"(?P<repo>[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?)(?:/[^/]+)*$"
)
_GITHUB_ORG_OPEN_RE = re.compile(r':github_org_open\s+"(?P<org>[^"]+)"')


def configured_west_orgs(deps_edn: Path) -> set[str]:
    """Return west orgs from the canonical deps config, not module paths.

    Reading the org from module entries themselves would make a typo
    self-authorising. ``:github_org_open`` is the existing root ownership
    registry and is stable in root-only as well as populated west checkouts.
    """
    orgs = {m.group("org") for m in _GITHUB_ORG_OPEN_RE.finditer(
        deps_edn.read_text(encoding="utf-8")
    )}
    return {org for org in orgs if re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?", org)}


def classify_west_project(raw: str, allowed_orgs: set[str]) -> bool:
    """Whether ``raw`` is a well-shaped project path in a configured org."""
    match = _WEST_PROJECT_RE.fullmatch(raw)
    return bool(
        match
        and match.group("org") in allowed_orgs
        and all(part not in (".", "..") for part in raw.split("/"))
    )

_STR_ESCAPES = {'"': '"', "\\": "\\", "n": "\n", "t": "\t", "r": "\r"}


def edn_str(token: str) -> str:
    """Decode an EDN string token ('"…"') to its Python value."""
    if not (token.startswith('"') and token.endswith('"')):
        raise ValueError(f"not a string token: {token[:40]!r}")
    body = token[1:-1]
    out, i = [], 0
    while i < len(body):
        c = body[i]
        if c == "\\" and i + 1 < len(body):
            out.append(_STR_ESCAPES.get(body[i + 1], body[i + 1]))
            i += 2
        else:
            out.append(c)
            i += 1
    return "".join(out)


def _strip_reserved_marker(raw_path: str) -> tuple[str, Optional[str]]:
    m = _RESERVED_SUFFIX_RE.search(raw_path)
    if not m:
        return raw_path, None
    return raw_path[: m.start()], m.group("marker")


def map_fields(node, wanted: tuple[str, ...]) -> dict[str, str]:
    """Extract string-valued `wanted` keys from a parsed EDN map node."""
    out: dict[str, str] = {}
    kids = node.children
    for k in range(0, len(kids) - 1, 2):
        key = kids[k]
        if isinstance(key, str) and key.lstrip(":") in wanted:
            val = kids[k + 1]
            if isinstance(val, str) and val.startswith('"'):
                out[key.lstrip(":")] = edn_str(val)
    return out


@dataclass
class PathCheck:
    section: str
    path: str
    exists: bool
    resolved: str
    adr: Optional[str] = None
    id: Optional[str] = None
    reserved_marker: Optional[str] = None
    unverifiable: Optional[str] = None  # "submodule" | "external" | "west-project" | None

    @property
    def is_drift(self) -> bool:
        return not self.exists and self.reserved_marker is None and self.unverifiable is None

    @property
    def is_accepted_missing(self) -> bool:
        return not self.exists and self.reserved_marker is not None

    @property
    def is_stale_marker(self) -> bool:
        return self.exists and self.reserved_marker is not None


def load_sections(deps_edn: Path) -> dict[str, list[dict[str, str]]]:
    """Parse deps.edn → {'adrs': [fields…], 'modules': [fields…]}."""
    root = fde.parse(fde.tokenize(deps_edn.read_text(encoding="utf-8")))
    if not (isinstance(root, fde.Coll) and root.opener == "{"):
        raise ValueError("deps.edn top-level form is not a map")
    out: dict[str, list[dict[str, str]]] = {"adrs": [], "modules": []}
    kids = root.children
    for k in range(0, len(kids) - 1, 2):
        key = kids[k]
        if key not in (":adrs", ":modules"):
            continue
        vec = kids[k + 1]
        if not (isinstance(vec, fde.Coll) and vec.opener == "["):
            continue
        for el in vec.children:
            if isinstance(el, fde.Coll) and el.opener == "{":
                fields = map_fields(el, ("path", "adr", "id", "title"))
                if "path" in fields or "id" in fields:
                    out[key.lstrip(":")].append(fields)
    return out


def check_paths(
    deps_edn: Path, repo_root: Path, *, filter_token: Optional[str] = None
) -> list[PathCheck]:
    sections = load_sections(deps_edn)
    subs = submodule_roots(repo_root)
    west_orgs = configured_west_orgs(deps_edn)
    results: list[PathCheck] = []
    for section in ("adrs", "modules"):
        for entry in sections[section]:
            raw_path = entry.get("path", "")
            if not raw_path:
                continue
            if filter_token is not None:
                tag = entry.get("adr") or entry.get("id") or ""
                if filter_token not in tag and filter_token not in raw_path:
                    continue
            clean, marker = _strip_reserved_marker(raw_path)
            unverifiable = None
            if classify_external(clean):
                unverifiable = "external"
            elif any(clean == s or clean.startswith(s + "/") for s in subs):
                unverifiable = "submodule"
            elif classify_west_project(clean, west_orgs):
                unverifiable = "west-project"
            resolved = (repo_root / clean).resolve()
            results.append(
                PathCheck(
                    section=section,
                    path=raw_path,
                    exists=resolved.exists(),
                    resolved=str(resolved),
                    adr=entry.get("adr") if section == "modules" else None,
                    id=entry.get("id") if section == "adrs" else None,
                    reserved_marker=marker,
                    unverifiable=unverifiable,
                )
            )
    return results


def find_duplicates(deps_edn: Path) -> dict[str, list[tuple[str, str]]]:
    sections = load_sections(deps_edn)
    seen: dict[tuple[str, str], list[tuple[str, str]]] = {}
    for entry in sections["modules"]:
        path = entry.get("path", "")
        if not path:
            continue
        clean, _ = _strip_reserved_marker(path)
        seen.setdefault(("modules", clean), []).append((path, entry.get("adr", "")))
    for entry in sections["adrs"]:
        aid = entry.get("id", "")
        if not aid:
            continue
        seen.setdefault(("adrs", aid), []).append((aid, entry.get("title", "")[:80]))
    return {f"{k[0]}:{k[1]}": v for k, v in seen.items() if len(v) > 1}


def find_unregistered_adrs(deps_edn: Path, repo_root: Path) -> list[str]:
    """REVERSE audit (the abaki gap, ADR-2606121333 lesson 1): every
    90-docs/adr/<10-digit-id>-*.md file on disk must be registered in the
    :adrs vector (matched by :id or by :path). Returns unregistered paths.

    Forward audit (registered → file exists) catches lost FILES (sonae);
    this direction catches lost REGISTRATIONS (abaki: ADR + actor landed,
    every registration of them missing)."""
    sections = load_sections(deps_edn)
    ids = {e.get("id", "") for e in sections["adrs"]}
    paths = set()
    for e in sections["adrs"]:
        clean, _ = _strip_reserved_marker(e.get("path", ""))
        paths.add(clean)
    out = []
    adr_dir = repo_root / "90-docs" / "adr"
    for f in sorted(adr_dir.glob("*.md")):
        name = f.name
        if len(name) < 11 or not name[:10].isdigit() or name[10] != "-":
            continue  # README / template / non-ADR docs
        rel = f"90-docs/adr/{name}"
        if name[:10] in ids or rel in paths:
            continue
        out.append(rel)
    return out


def _front_matter(p: Path) -> dict[str, str]:
    """Minimal YAML front-matter reader: top-level 'key: value' scalars only."""
    out: dict[str, str] = {}
    lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    if not lines or lines[0].strip() != "---":
        return out
    for line in lines[1:200]:
        if line.strip() == "---":
            break
        if ":" in line and not line.startswith((" ", "\t", "-")):
            k, _, v = line.partition(":")
            v = v.strip()
            if v.startswith('"') and v.endswith('"') and len(v) >= 2:
                v = v[1:-1]
            out[k.strip()] = v
    return out


def _edn_quote(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def register_missing(deps_edn: Path, repo_root: Path) -> int:
    """Backfill every unregistered ADR into :adrs from its front matter,
    via the structural appender (parse-or-die — cannot corrupt the file)."""
    import importlib.util as _il

    unregistered = find_unregistered_adrs(deps_edn, repo_root)
    if not unregistered:
        print("no unregistered ADRs — registry complete")
        return 0
    entries = []
    for rel in unregistered:
        fm = _front_matter(repo_root / rel)
        adr_id = rel.split("/")[-1][:10]
        title = fm.get("title", "") or rel.split("/")[-1]
        # strip the redundant "ADR-XXXXXXXXXX: " prefix most titles carry
        for pref in (f"ADR-{adr_id}: ", f"ADR-{adr_id} "):
            if title.startswith(pref):
                title = title[len(pref):]
        status = fm.get("status", "") or "unknown"
        entries.append(
            "{:id " + _edn_quote(adr_id) + " :title " + _edn_quote(title)
            + " :status " + _edn_quote(status) + " :path " + _edn_quote(rel) + "}"
        )
    out = fde.append_adrs(deps_edn.read_text(encoding="utf-8"), " ".join(entries))
    deps_edn.write_text(out, encoding="utf-8")
    print(f"registered {len(entries)} ADR(s) into :adrs from front matter")
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify every deps.edn :adrs / :modules :path resolves."
    )
    parser.add_argument("--deps-edn", type=Path, default=None)
    parser.add_argument("--repo-root", type=Path, default=None)
    parser.add_argument(
        "--filter",
        dest="filter_token",
        help="Only check entries whose adr/id/path contains this token.",
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--register-missing",
        action="store_true",
        help="Backfill every unregistered ADR into :adrs from its front "
        "matter (structural append — cannot corrupt deps.edn).",
    )
    parser.add_argument(
        "--write-baseline",
        action="store_true",
        help="Freeze CURRENT drift into the shrink-only baseline (review-gated; "
        "never use to launder new debt — the audit mode is what the hook runs).",
    )
    parser.add_argument(
        "--no-baseline",
        action="store_true",
        help="Report every drift entry, ignoring the frozen baseline.",
    )
    args = parser.parse_args(argv)

    repo_root = args.repo_root
    if repo_root is None:
        here = Path(__file__).resolve()
        for cand in [here.parent, *here.parents]:
            if (cand / "deps.edn").is_file():
                repo_root = cand
                break
        if repo_root is None:
            print("verify_deps_edn_paths: cannot find repo root", file=sys.stderr)
            return 2
    deps_edn = args.deps_edn or repo_root / "deps.edn"
    if not deps_edn.is_file():
        print(f"verify_deps_edn_paths: deps.edn not found at {deps_edn}", file=sys.stderr)
        return 2

    if args.register_missing:
        return register_missing(deps_edn, repo_root)

    try:
        results = check_paths(deps_edn, repo_root, filter_token=args.filter_token)
    except (ValueError, AssertionError) as exc:
        print(f"verify_deps_edn_paths: edn parse error: {exc}", file=sys.stderr)
        return 2

    drift = [r for r in results if r.is_drift]

    # Shrink-only baseline ratchet (ADR-2606071800 pattern): legacy drift is
    # frozen; the gate FAILS only on NEW drift. Graduated entries (path now
    # resolves or entry removed) are reported so the list only shrinks.
    baseline_file = repo_root / BASELINE_PATH
    unregistered = (
        find_unregistered_adrs(deps_edn, repo_root)
        if args.filter_token is None
        else []
    )
    if args.write_baseline:
        baseline_file.write_text(
            json.dumps(
                {
                    "drift": sorted({d.path for d in drift}),
                    "unregistered_adrs": sorted(unregistered),
                },
                indent=1,
            )
            + "\n"
        )
        print(
            f"baseline frozen: {len(drift)} drift + {len(unregistered)} "
            f"unregistered ADR(s) → {BASELINE_PATH}"
        )
        return 0
    baseline: set[str] = set()
    baseline_unreg: set[str] = set()
    if baseline_file.is_file() and not args.no_baseline and args.filter_token is None:
        raw = json.loads(baseline_file.read_text())
        if isinstance(raw, list):  # v1 format: drift list only
            baseline = set(raw)
        else:
            baseline = set(raw.get("drift", []))
            baseline_unreg = set(raw.get("unregistered_adrs", []))
    new_drift = [d for d in drift if d.path not in baseline]
    current_drift_paths = {d.path for d in drift}
    graduated = sorted(baseline - current_drift_paths)
    new_unregistered = [u for u in unregistered if u not in baseline_unreg]
    graduated_unreg = sorted(baseline_unreg - set(unregistered))
    drift = new_drift
    accepted_missing = [r for r in results if r.is_accepted_missing]
    stale_markers = [r for r in results if r.is_stale_marker]
    n_total = len(results)
    n_ok = sum(1 for r in results if r.exists and r.reserved_marker is None)
    duplicates = find_duplicates(deps_edn) if args.filter_token is None else {}

    if args.json:
        print(
            json.dumps(
                {
                    "total": n_total,
                    "ok": n_ok,
                    "drift_count": len(drift),
                    "drift": [asdict(d) for d in drift],
                    "accepted_missing_count": len(accepted_missing),
                    "accepted_missing": [asdict(a) for a in accepted_missing],
                    "stale_marker_count": len(stale_markers),
                    "stale_markers": [asdict(s) for s in stale_markers],
                    "duplicate_count": len(duplicates),
                    "duplicates": duplicates,
                    "unregistered_adr_count": len(new_unregistered),
                    "unregistered_adrs": new_unregistered,
                    "filter": args.filter_token,
                },
                indent=2,
            )
        )
    else:
        summary = [f"{n_ok}/{n_total} entries resolve"]
        if accepted_missing:
            summary.append(f"{len(accepted_missing)} accepted-reserved (owner-asserted)")
        if stale_markers:
            summary.append(f"{len(stale_markers)} stale marker(s) — drop the suffix")
        if duplicates:
            summary.append(f"{len(duplicates)} duplicate key(s)")
        if drift:
            summary.append(f"{len(drift)} drift")
        if new_unregistered:
            summary.append(f"{len(new_unregistered)} unregistered ADR(s)")
        print("deps.edn path audit: " + " / ".join(summary))
        for label, items in (("ACCEPTED-RESERVED", accepted_missing), ("STALE-MARKER", stale_markers)):
            if items:
                print(f"{label} ({len(items)}):")
                for r in items:
                    print(f"  [{r.section}] {r.path}  ({r.adr or r.id or '—'})")
        if duplicates:
            print(f"DUPLICATES ({len(duplicates)}):")
            for key, vals in duplicates.items():
                print(f"  {key}: {len(vals)} entries")
        if graduated:
            print(f"GRADUATED ({len(graduated)}) — no longer drift, remove from {BASELINE_PATH}:")
            for p in graduated:
                print(f"  {p}")
        if graduated_unreg:
            print(f"GRADUATED-UNREGISTERED ({len(graduated_unreg)}) — now registered, remove from {BASELINE_PATH}:")
            for p in graduated_unreg:
                print(f"  {p}")
        if drift:
            print(f"NEW DRIFT ({len(drift)}) — bare missing paths not on the frozen baseline:")
            for r in drift:
                print(f"  [{r.section}] {r.path}  ({r.adr or r.id or '—'})")
        if new_unregistered:
            print(f"NEW UNREGISTERED ADR ({len(new_unregistered)}) — on disk but not in :adrs (register via format-deps-edn.py --append-adrs):")
            for p in new_unregistered:
                print(f"  {p}")

    return 1 if (drift or new_unregistered) else 0


if __name__ == "__main__":
    sys.exit(main())
