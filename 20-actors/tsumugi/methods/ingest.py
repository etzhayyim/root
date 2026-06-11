#!/usr/bin/env python3
"""tsumugi 紡ぎ — §D7.1 ingester: weave public follow/deps sources into the graph.

Merges the curated power seed with ingest sources (atproto follow fixtures, deps, …)
into one woven kotoba-EDN graph — claimed-first, aggregate-first, :representative —
then hands off to analyze.py. Latent organisms are minted from public handles
(:organism/claimed? false, :organism/standing :latent); they become :member only on
the §D5 covenant claim.

CONSTITUTIONAL GATES:
  G1 power/public only — institutions & public-role nodes; the powerless are absent
     by construction (the fixtures contain no private persons).
  G7 outward-gated — LIVE atproto fetch (app.bsky.graph.getFollows over real accounts)
     requires --live AND env TSUMUGI_OPERATOR_GATE=<council-token>. Without it the
     ingester runs in FIXTURE mode (no network), per §D7.1 R0 posture.
  G5 sourcing honesty — every ingested record stays :representative until a live,
     operator-gated, attributed fetch replaces it.

Usage:
    python3 ingest.py                 # weave seed + data/ingest/*.edn  → out/woven-graph
    python3 ingest.py --live HANDLE…  # REFUSED unless operator gate present
"""
from __future__ import annotations
import sys, os, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from analyze import read_edn  # reuse the EDN reader

ACTOR = pathlib.Path(__file__).resolve().parent.parent

def _records(path: pathlib.Path):
    return read_edn(path.read_text(encoding="utf-8"))

def _key(rec):
    return ("org", rec[":organism/id"]) if ":organism/id" in rec else \
           ("en", rec[":en/id"]) if ":en/id" in rec else None

def weave():
    seed = ACTOR / "data" / "seed-power-graph.kotoba.edn"
    sources = [seed] + sorted((ACTOR / "data" / "ingest").glob("*.edn"))
    merged, seen = [], set()
    counts = {}
    for src in sources:
        n_new = 0
        for rec in _records(src):
            k = _key(rec)
            if k is None or k in seen:
                continue
            # G1/G5: enforce latent + sourcing flags on ingested (non-seed) organisms
            if src != seed and k[0] == "org":
                rec.setdefault(":organism/claimed?", False)
                rec.setdefault(":organism/standing", ":latent")
            rec.setdefault(":organism/sourcing" if k[0] == "org" else ":en/sourcing",
                           ":representative")
            seen.add(k); merged.append(rec); n_new += 1
        counts[src.name] = n_new
    return merged, counts

def to_edn(recs):
    def v(x):
        if isinstance(x, bool):  return "true" if x else "false"
        if isinstance(x, str):
            return x if x.startswith(":") else f'"{x}"'
        return str(x)
    lines = [";; tsumugi 紡ぎ — GENERATED woven graph (seed + ingest). DO NOT hand-edit.",
             ";; claimed-first + aggregate-first + :representative (ADR-2606011800 §D7.1).", "["]
    for r in recs:
        lines.append("{" + " ".join(f"{k} {v(val)}" for k, val in r.items()) + "}")
    lines.append("]")
    return "\n".join(lines) + "\n"

def main():
    if "--live" in sys.argv:
        gate = os.environ.get("TSUMUGI_OPERATOR_GATE")
        if not gate:
            sys.exit("REFUSED: live atproto ingest is G11/Council-gated. Set "
                     "TSUMUGI_OPERATOR_GATE=<council-token> and supply an operator DID. "
                     "Running fixture mode requires no flag.")
        sys.exit("REFUSED: live fetch path is a scaffold only in R0 — not implemented. "
                 "Wire app.bsky.graph.getFollows via @etzhayyim/sdk + MST membrane "
                 "(ADR-2605231902) under Council ratification, then re-run.")

    merged, counts = weave()
    orgs = [r for r in merged if ":organism/id" in r]
    edges = [r for r in merged if ":en/id" in r]
    latent = sum(1 for r in orgs if r.get(":organism/claimed?") is False)
    out = ACTOR / "out" / "woven-graph.kotoba.edn"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(to_edn(merged), encoding="utf-8")

    print("woven (fixture mode — no network):")
    for name, n in counts.items():
        print(f"  + {n:3d} new records from {name}")
    print(f"= {len(orgs)} organisms ({latent} latent/unclaimed) · {len(edges)} 縁")
    print(f"✓ wrote {out}")
    print(f"→ next: python3 methods/analyze.py {out} --out out")

if __name__ == "__main__":
    main()
