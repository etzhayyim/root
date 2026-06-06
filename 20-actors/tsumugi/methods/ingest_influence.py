#!/usr/bin/env python3
"""tsumugi 紡ぎ — influence-history INGEST (ADR-2606061500). The path that actually scales
coverage: maps external documented-influence sources (Wikidata `influenced by` P737 / Pantheon
notables) into `:hist/*` nodes + `:flow/*` influence 縁, merged with the seed.

CHARTER GATES (the membrane every entry crosses):
  N2 mirror      — every ingested node gets :mirror/is-mirror true + disclaimer + performer-type.
  N3 non-adjud.  — :flow records documented influence, never a truth verdict.
  N4 public+settled+no PII — an entity is admitted ONLY if it has a deathYear (historical,
                   settled). Living/uncertain entities are REFUSED (that is the Council-Lv7+
                   :human scale). No PII is read or written.
  N5 temporal DAG — an edge is dropped if source.year-from > receiver.year-to (reported).
  G5 sourcing    — everything ingested is :sourcing :representative, :source :scholarship.
  G7 outward-gated — OFFLINE (fixtures) by default. `--live` REFUSES unless TSUMUGI_OPERATOR_GATE=1
                   AND an operator attestation is supplied; live network fetch is wired-but-gated.

Pantheon gives NODES (which figures exist) but NOT edges; influence edges come only from a
documented relation source (Wikidata P737). HPI/notability is NEVER turned into a node score
(N1 edge-primary) — it may only gate WHICH nodes are candidates.

stdlib only (reuses analyze_influence's loader). Usage:
    python3 ingest_influence.py                       # offline: merge fixtures + seed
    python3 ingest_influence.py --out OUTDIR
    python3 ingest_influence.py --live                # refused unless gated (G7)
"""
from __future__ import annotations
import sys, os, re, json, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from analyze_influence import load, node_year  # noqa: E402

DISCLAIMER_FIG = "観察像 — 本人ではない (an observational mirror, not the person)"


class LiveGateRefused(Exception):
    """G7 — live network ingest attempted without the operator gate."""


def slug(label: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")
    return s.split("-")[-1] if "-" in s else s  # prefer surname-ish tail, keep short


def to_node_id(ref: str, label_to_id: dict) -> str:
    if ref.startswith(("fig.", "doc.", "trad.", "event.", "self.")):
        return ref                      # already an id (existing seed node)
    if ref in label_to_id:
        return label_to_id[ref]         # a label of another ingested entity
    return f"fig.{slug(ref)}"           # a bare label → derive a figure id


def normalize_entity(e: dict) -> dict | None:
    """Wikidata-shaped entity → kotoba node dict, or None if refused (N4)."""
    if "deathYear" not in e:            # N4: living/unsettled → refuse
        return None
    label = e["label"]
    nid = f"fig.{slug(label)}"
    trad = [t if t.startswith(":") else ":" + t for t in e.get("tradition", ["secular-philosophy"])]
    era = e.get("era", "modern")
    return {
        ":organism/id": nid,
        ":organism/kind": ":institutional",
        ":organism/label": label,
        ":organism/standing": ":historical-public",
        ":hist/subkind": ":figure",
        ":hist/year-from": int(e["birthYear"]),
        ":hist/year-to": int(e["deathYear"]),
        ":hist/era": era if era.startswith(":") else ":" + era,
        ":hist/tradition": trad,
        ":hist/dating-confidence": ":attested",
        ":mirror/is-mirror": True,
        ":mirror/performer-type": ":historical-figure",
        ":mirror/disclaimer": DISCLAIMER_FIG,
        ":influence/affect-class": ":inquiring",
        ":hist/sourcing": ":representative",
    }


def edn_node(n: dict) -> str:
    parts = []
    for k, v in n.items():
        if isinstance(v, bool):
            parts.append(f"{k} {'true' if v else 'false'}")
        elif isinstance(v, list):
            parts.append(f"{k} [{' '.join(v)}]")
        elif isinstance(v, str) and (v.startswith(":") or v.lstrip("-").isdigit()):
            parts.append(f"{k} {v}")
        elif isinstance(v, str):
            esc = v.replace("\\", "\\\\").replace('"', '\\"')
            parts.append(f'{k} "{esc}"')
        else:
            parts.append(f"{k} {v}")
    return "{" + " ".join(parts) + "}"


def ingest_offline(fixtures_dir: pathlib.Path, seed: str):
    nodes, flows = load(seed)
    seen_nodes = set(nodes)
    seen_flows = {f[":flow/id"] for f in flows}
    new_nodes, new_flows, dropped = [], [], []

    # pass 1: figures (collect label→id so cross-references resolve)
    raw = []
    label_to_id = {}
    for fx in sorted(fixtures_dir.glob("*.json")):
        data = json.loads(fx.read_text(encoding="utf-8"))
        for e in data.get("entities", []):
            raw.append(e)
            if "deathYear" in e:
                label_to_id[e["label"]] = f"fig.{slug(e['label'])}"

    # build a year lookup spanning seed + ingested figures (for N5)
    yr = {}
    for nid, nd in nodes.items():
        yr[nid] = (node_year(nd, ":hist/year-from"), node_year(nd, ":hist/year-to"))
    for e in raw:
        if "deathYear" in e:
            yr[f"fig.{slug(e['label'])}"] = (int(e["birthYear"]), int(e["deathYear"]))

    for e in raw:
        n = normalize_entity(e)
        if n is None:
            dropped.append((e.get("label"), "N4 living/unsettled (no deathYear)"))
            continue
        nid = n[":organism/id"]
        if nid not in seen_nodes:
            new_nodes.append(n); seen_nodes.add(nid)
        # influence edges: each influencedBy ref → this entity (forward in time)
        for ref in e.get("influencedBy", []):
            src = to_node_id(ref, label_to_id)
            dst = nid
            if src not in yr or dst not in yr:
                dropped.append((f"{src}->{dst}", "unknown endpoint")); continue
            if yr[src][0] > yr[dst][1]:           # N5: source begins after receiver ends
                dropped.append((f"{src}->{dst}", "N5 backward-in-time")); continue
            fid = f"fl.{slug(src)}.{slug(dst)}"
            if fid in seen_flows:
                continue
            seen_flows.add(fid)
            new_flows.append({
                ":flow/id": fid, ":flow/kind": ":influences",
                ":flow/from": src, ":flow/to": dst,
                ":flow/signed-weight": 0.5, ":flow/strain": 0.5, ":flow/thermo-length": 0.5,
                ":flow/source": ":scholarship", ":flow/sourcing": ":representative",
            })
    return nodes, flows, new_nodes, new_flows, dropped


def main():
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = str(here / "data" / "seed-influence-history.kotoba.edn")
    fixtures = here / "data" / "ingest-influence"
    outdir = pathlib.Path(sys.argv[sys.argv.index('--out') + 1]) if '--out' in sys.argv else here / "out"
    outdir.mkdir(parents=True, exist_ok=True)

    if "--live" in sys.argv:
        gate = os.environ.get("TSUMUGI_OPERATOR_GATE") == "1"
        attest = os.environ.get("TSUMUGI_OPERATOR_DID")
        if not (gate and attest):
            raise LiveGateRefused(
                "G7 — live influence ingest refused. Requires TSUMUGI_OPERATOR_GATE=1 + "
                "TSUMUGI_OPERATOR_DID=<operator attestation> + Council ratification. "
                "Offline fixture ingest runs without --live.")
        print("⚠ live gate satisfied — (live Wikidata/Pantheon fetch wiring is a follow-up)")
        return

    nodes, flows, new_nodes, new_flows, dropped = ingest_offline(fixtures, seed)

    out = outdir / "influence-ingested.kotoba.edn"
    lines = [";; tsumugi 紡ぎ — GENERATED merged seed + offline ingest (ADR-2606061500). DO NOT hand-edit.",
             ";; ingested nodes/edges are :representative :scholarship; mirror-only (N2); N4/N5 enforced.",
             "["]
    # re-emit existing nodes/edges verbatim-ish would require the raw maps; instead we emit a
    # MERGE FILE of just the additions, runnable alongside the seed (analyzer loads either).
    lines.append(";; ── ingested figure nodes ──")
    lines += [" " + edn_node(n) for n in new_nodes]
    lines.append(";; ── ingested influence 縁 ──")
    for f in new_flows:
        lines.append(" " + edn_node(f))
    lines.append("]")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # also emit a combined seed so analyze/coverage can run on the union directly
    combined = outdir / "seed-plus-ingest.kotoba.edn"
    base = pathlib.Path(seed).read_text(encoding="utf-8").rstrip()
    assert base.endswith("]"), "seed must end with ]"
    add = "\n ;; ── INGESTED (offline) ──\n" + "\n".join(
        " " + edn_node(n) for n in new_nodes) + "\n" + "\n".join(
        " " + edn_node(f) for f in new_flows) + "]\n"
    combined.write_text(base[:-1] + add, encoding="utf-8")

    print(f"✓ ingested {len(new_nodes)} new nodes · {len(new_flows)} new 縁 "
          f"(seed had {len(nodes)} nodes / {len(flows)} 縁)")
    if dropped:
        print(f"✓ refused/dropped {len(dropped)}:")
        for what, why in dropped:
            print(f"    - {what}: {why}")
    print(f"✓ wrote {out}")
    print(f"✓ wrote {combined}  (run analyze_influence.py / coverage_report.py on this to see the lift)")


if __name__ == "__main__":
    main()
