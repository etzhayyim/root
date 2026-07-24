#!/usr/bin/env python3
"""yirah-presence-warn — non-blocking reminder for ADR-2606112200 D4.

A staged actor wire manifest (orgs/etzhayyim/com-etzhayyim-*/wire/manifest.jsonld) without a top-level
`yirah` declaration block gets a WARNING, never a block: absent ≠ violating —
declarations are adopted only where an invariant is meaningful for the actor's
scope, and that judgment belongs to the author, not this script. Always exits 0
(mirrors paywall-warn). Compat facades and `_`-prefixed dirs are skipped.

Usage (lefthook): python3 yirah-presence-warn.py {staged_files}
"""
import json
import pathlib
import sys


def main(argv):
    warned = 0
    for arg in argv[1:]:
        p = pathlib.Path(arg)
        if p.name != "manifest.jsonld" or p.parent.name != "wire" or not p.parent.parent.name.startswith("com-etzhayyim-"):
            continue
        actor = p.parent.parent.name.removeprefix("com-etzhayyim-")
        if actor.endswith("-compat") or actor.startswith("_"):
            continue
        try:
            m = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue  # JSON validity is another hook's job
        if "yirah" not in m:
            warned += 1
            print(f"{arg}: no `yirah` declaration block "
                  f"(ADR-2606112200 D4 — declare the invariants that fit this "
                  f"actor's scope, grounded in its gates; see "
                  f"90-docs/yirah-attest-snapshot.md)")
    if warned:
        print(f"⚠ yirah-presence-warn: {warned} manifest(s) without declarations.")
        print("  Non-blocking — absent ≠ violating; adopt only where meaningful.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
