#!/usr/bin/env python3
"""reconcile-adr-ids — resolve ADR id races (distinct files sharing one id).

Parallel agent sessions repeatedly minted the same YYMMDDhhmm ADR id for
different ADRs (the root CLAUDE.md tracked 2605263400/2605263500 for "a
future ADR-id reconciliation"; the 2026-06-12 deps.edn :adrs backfill made
the full worklist visible: 46 ids across ~96 files).

Per duplicated id, ONE file keeps the id and every other file is renumbered
to the nearest free id (+1, +2, …), following the existing in-repo precedent
("Renumbered from 2606112300 — ID race", kaiyaku/tate, 2026-06-11).

Keep rule (deterministic, reference-preserving):
  1. the file with MORE inbound path references repo-wide keeps the id
     (so e.g. lefthook.yml's pointer to the remediation-wave ADR stays true);
  2. tie → the file whose first git commit is older keeps it (the racer that
     landed second renames, matching the precedent's semantics).

A renumbered file gets:
  - `git mv` to the new id (slug unchanged),
  - front-matter `id:`/`title:` self-references updated old→new,
  - a machine-readable `renumbered_from: "<old-id>"` front-matter key,
  - its deps.edn :adrs entry updated (id + path) via the structural editor,
  - its 90-docs/adr/README.md index row link updated (when present).

Cross-references of the bare form "ADR-<id>" elsewhere are NOT rewritten:
they were ambiguous while the race existed and stay textually unchanged —
after reconciliation the bare id resolves to the keeper, which the keep
rule chose to be the most-referenced file.

Usage:
  reconcile-adr-ids.py --plan      # print the keep/renumber plan, change nothing
  reconcile-adr-ids.py --execute   # apply (run from the repo root)
"""

from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path.cwd()
ADR_DIR = REPO / "90-docs" / "adr"

_spec = importlib.util.spec_from_file_location(
    "fde", REPO / "70-tools/scripts/lint/format-deps-edn.py"
)
fde = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fde)


def adr_files() -> dict[str, list[Path]]:
    byid: dict[str, list[Path]] = defaultdict(list)
    for f in sorted(ADR_DIR.glob("*.md")):
        n = f.name
        if len(n) > 11 and n[:10].isdigit() and n[10] == "-":
            byid[n[:10]].append(f)
    return byid


def inbound_refs(fname: str) -> int:
    """Count repo-wide mentions of this exact filename (path-level refs),
    excluding the registry sidecars and the index (we update those)."""
    out = subprocess.run(
        ["git", "grep", "-l", "--fixed-strings", fname, "--",
         ":(exclude)90-docs/_registry", ":(exclude)90-docs/adr/README.md",
         ":(exclude)deps.edn"],
        capture_output=True, text=True, cwd=REPO,
    )
    hits = [l for l in out.stdout.splitlines() if l and not l.endswith(fname)]
    return len(hits)


def first_added_epoch(path: Path) -> int:
    out = subprocess.run(
        ["git", "log", "--follow", "--diff-filter=A", "--format=%at", "--",
         str(path.relative_to(REPO))],
        capture_output=True, text=True, cwd=REPO,
    )
    times = [int(t) for t in out.stdout.split()]
    return min(times) if times else 2**62


def build_plan():
    byid = adr_files()
    races = {i: fs for i, fs in byid.items() if len(fs) > 1}
    used = set(byid.keys())
    plan = []  # (old_id, keep_path, [(loser_path, new_id), …])
    for adr_id in sorted(races):
        files = races[adr_id]
        scored = sorted(
            files,
            key=lambda f: (-inbound_refs(f.name), first_added_epoch(f), f.name),
        )
        keeper, losers = scored[0], scored[1:]
        renames = []
        for loser in losers:
            k = 1
            while f"{int(adr_id) + k:010d}" in used:
                k += 1
            new_id = f"{int(adr_id) + k:010d}"
            used.add(new_id)
            renames.append((loser, new_id))
        plan.append((adr_id, keeper, renames))
    return plan


def rewrite_front_matter(path: Path, old_id: str, new_id: str) -> None:
    text = path.read_text(encoding="utf-8")
    # self-references in front matter + the H1 heading
    text = text.replace(f"id: adr-{old_id}-", f"id: adr-{new_id}-", 1)
    text = text.replace(f"ADR-{old_id}:", f"ADR-{new_id}:")
    # machine-readable provenance, right after the id: line
    lines = text.splitlines(keepends=True)
    for i, line in enumerate(lines):
        if line.startswith("id: "):
            lines.insert(i + 1, f'renumbered_from: "{old_id}"\n')
            break
    path.write_text("".join(lines), encoding="utf-8")


def update_readme(old_name: str, new_name: str, old_id: str, new_id: str) -> bool:
    readme = ADR_DIR / "README.md"
    text = readme.read_text(encoding="utf-8")
    link_old = f"[{old_id}](./{old_name})"
    if link_old not in text:
        return False
    text = text.replace(
        link_old,
        f"[{new_id}](./{new_name})",
    )
    readme.write_text(text, encoding="utf-8")
    return True


def update_deps_edn(old_id: str, old_rel: str, new_id: str, new_rel: str) -> None:
    src = (REPO / "deps.edn").read_text(encoding="utf-8")
    root = fde.parse(fde.tokenize(src))
    kids = root.children
    for k in range(0, len(kids), 2):
        if kids[k] != ":adrs":
            continue
        for el in kids[k + 1].children:
            ek = el.children
            m = {ek[j]: j for j in range(0, len(ek) - 1, 2)}
            pid = m.get(":id")
            ppath = m.get(":path")
            if pid is None or ppath is None:
                continue
            if ek[pid + 1] == f'"{old_id}"' and ek[ppath + 1].strip('"') == old_rel:
                ek[pid + 1] = f'"{new_id}"'
                ek[ppath + 1] = f'"{new_rel}"'
    out = fde.render_top(root)
    assert fde.format_once(out) == out
    (REPO / "deps.edn").write_text(out, encoding="utf-8")


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "--plan"
    plan = build_plan()
    n_renames = sum(len(r) for _, _, r in plan)
    print(f"id races: {len(plan)} / files to renumber: {n_renames}\n")
    for adr_id, keeper, renames in plan:
        print(f"{adr_id}: KEEP {keeper.name}")
        for loser, new_id in renames:
            print(f"          {loser.name} → {new_id}")
    if mode != "--execute":
        print("\n(plan only — pass --execute to apply)")
        return 0

    for adr_id, keeper, renames in plan:
        for loser, new_id in renames:
            old_name = loser.name
            new_name = new_id + old_name[10:]
            old_rel = f"90-docs/adr/{old_name}"
            new_rel = f"90-docs/adr/{new_name}"
            subprocess.run(["git", "mv", old_rel, new_rel], check=True, cwd=REPO)
            rewrite_front_matter(ADR_DIR / new_name, adr_id, new_id)
            update_readme(old_name, new_name, adr_id, new_id)
            update_deps_edn(adr_id, old_rel, new_id, new_rel)
    print("\napplied. Run registry regen + verifiers next.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
