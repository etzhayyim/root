#!/usr/bin/env python3
"""tsumugi 紡ぎ — influence-history INGEST (ADR-2606061500). The path that actually scales
coverage: maps external documented-influence sources (Wikidata `influenced by` P737 / Pantheon
notables) into `:hist/*` nodes + `:flow/*` influence 縁, merged with the seed.

CHARTER GATES (the membrane every entry crosses, offline AND live):
  N1 edge-primary — notability/HPI is NEVER turned into a node score; influence on the edge.
  N2 mirror      — every ingested node gets :mirror/is-mirror true + disclaimer + performer-type.
  N3 non-adjud.  — :flow records documented influence, never a truth verdict.
  N4 public+settled+no PII — an entity is admitted ONLY if it has a death date (historical,
                   settled). Living/uncertain entities are REFUSED (the Council-Lv7+ :human
                   scale). No PII is read or written — only public dates/labels/relations.
  N5 temporal DAG — an edge is dropped if source.year-from > receiver.year-to (reported).
  G5 sourcing    — everything ingested is :sourcing :representative, :source :scholarship.
  G6 substrate   — stdlib urllib only (no new deps). Public-data fetch is NOT inference, so the
                   Murakumo-only rule (LLM) does not apply; no vendor LLM is called.
  G7 outward-gated — OFFLINE (fixtures) by default. `--live` REFUSES unless
                   TSUMUGI_OPERATOR_GATE=1 AND TSUMUGI_OPERATOR_DID=<operator attestation>
                   (Council-ratified). Live output is written ONLY to out/ (gitignored);
                   the committed canonical seed is NEVER auto-mutated — promotion into the
                   seed is a separate human-reviewed PR (preserves 1 SBT = 1 vote integrity).

stdlib only. Usage:
    python3 ingest_influence.py                       # offline: merge fixtures + seed
    python3 ingest_influence.py --out OUTDIR
    python3 ingest_influence.py --live [--limit N] [--no-pantheon]   # gated live fetch
"""
from __future__ import annotations
import sys, os, re, json, pathlib, urllib.request, urllib.parse
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from analyze_influence import load, node_year  # noqa: E402

DISCLAIMER_FIG = "観察像 — 本人ではない (an observational mirror, not the person)"
WDQS_ENDPOINT = "https://query.wikidata.org/sparql"
PANTHEON_CSV = "https://raw.githubusercontent.com/pantheon-world/data/master/people.csv"  # best-effort
USER_AGENT = ("etzhayyim-tsumugi/0.1 (https://etzhayyim.com; influence-history research; "
              "ADR-2606061500) python-urllib")


class LiveGateRefused(Exception):
    """G7 — live network ingest attempted without the operator gate."""


# ── shared membrane helpers ──────────────────────────────────────────────────
def slug(label: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")
    return s.split("-")[-1] if "-" in s else s  # prefer surname-ish tail, keep short


def to_node_id(ref: str, label_to_id: dict) -> str:
    if ref.startswith(("fig.", "doc.", "trad.", "event.", "self.")):
        return ref
    if ref in label_to_id:
        return label_to_id[ref]
    return f"fig.{slug(ref)}"


def make_node(label: str, birth: int, death: int, trad, era: str) -> dict:
    trad = [t if t.startswith(":") else ":" + t for t in (trad or ["secular-philosophy"])]
    return {
        ":organism/id": f"fig.{slug(label)}",
        ":organism/kind": ":institutional",
        ":organism/label": label,
        ":organism/standing": ":historical-public",
        ":hist/subkind": ":figure",
        ":hist/year-from": int(birth),
        ":hist/year-to": int(death),
        ":hist/era": era if era.startswith(":") else ":" + era,
        ":hist/tradition": trad,
        ":hist/dating-confidence": ":attested",
        ":mirror/is-mirror": True,
        ":mirror/performer-type": ":historical-figure",
        ":mirror/disclaimer": DISCLAIMER_FIG,
        ":influence/affect-class": ":inquiring",
        ":hist/sourcing": ":representative",
    }


def make_edge(src: str, dst: str) -> dict:
    return {
        ":flow/id": f"fl.{slug(src)}.{slug(dst)}", ":flow/kind": ":influences",
        ":flow/from": src, ":flow/to": dst,
        ":flow/signed-weight": 0.5, ":flow/strain": 0.5, ":flow/thermo-length": 0.5,
        ":flow/source": ":scholarship", ":flow/sourcing": ":representative",
    }


def era_for_year(y: int) -> str:
    for hi, era in [(-1200, ":bronze-age"), (-800, ":iron-age"), (-200, ":axial"),
                    (0, ":2nd-temple"), (476, ":late-antiquity"), (1000, ":early-medieval"),
                    (1450, ":medieval"), (1648, ":reformation"), (1800, ":enlightenment"),
                    (1945, ":modern")]:
        if y < hi:
            return era
    return ":contemporary"


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


# ── OFFLINE fixture ingest (Wikidata-shaped JSON) ────────────────────────────
def normalize_entity(e: dict) -> dict | None:
    if "deathYear" not in e:            # N4: living/unsettled → refuse
        return None
    return make_node(e["label"], int(e["birthYear"]), int(e["deathYear"]),
                     e.get("tradition"), e.get("era", "modern"))


def ingest_offline(fixtures_dir: pathlib.Path, seed: str):
    nodes, flows = load(seed)
    seen_nodes, seen_flows = set(nodes), {f[":flow/id"] for f in flows}
    new_nodes, new_flows, dropped = [], [], []
    raw, label_to_id = [], {}
    for fx in sorted(fixtures_dir.glob("*.json")):
        for e in json.loads(fx.read_text(encoding="utf-8")).get("entities", []):
            raw.append(e)
            if "deathYear" in e:
                label_to_id[e["label"]] = f"fig.{slug(e['label'])}"
    yr = {nid: (node_year(nd, ":hist/year-from"), node_year(nd, ":hist/year-to"))
          for nid, nd in nodes.items()}
    for e in raw:
        if "deathYear" in e:
            yr[f"fig.{slug(e['label'])}"] = (int(e["birthYear"]), int(e["deathYear"]))
    for e in raw:
        n = normalize_entity(e)
        if n is None:
            dropped.append((e.get("label"), "N4 living/unsettled (no deathYear)")); continue
        nid = n[":organism/id"]
        if nid not in seen_nodes:
            new_nodes.append(n); seen_nodes.add(nid)
        for ref in e.get("influencedBy", []):
            src, dst = to_node_id(ref, label_to_id), nid
            if src not in yr or dst not in yr:
                dropped.append((f"{src}->{dst}", "unknown endpoint")); continue
            if yr[src][0] > yr[dst][1]:
                dropped.append((f"{src}->{dst}", "N5 backward-in-time")); continue
            fid = f"fl.{slug(src)}.{slug(dst)}"
            if fid in seen_flows:
                continue
            seen_flows.add(fid); new_flows.append(make_edge(src, dst))
    return nodes, flows, new_nodes, new_flows, dropped


# ── LIVE Wikidata SPARQL ingest (G7-gated) ───────────────────────────────────
WIKIDATA_INFLUENCE_SPARQL = """
SELECT ?p ?pLabel ?pBirth ?pDeath ?inf ?infLabel ?infBirth ?infDeath WHERE {
  ?p   wdt:P737 ?inf .
  ?p   wdt:P569 ?pBirth .   ?p   wdt:P570 ?pDeath .
  ?inf wdt:P569 ?infBirth . ?inf wdt:P570 ?infDeath .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en,ja". }
}
LIMIT %d
"""


def _year(iso: str | None):
    """Wikidata ISO date → signed year int (BCE negative). '-0563-..' → -563."""
    if not iso:
        return None
    s = iso.strip()
    neg = s.startswith("-")
    if neg:
        s = s[1:]
    head = s.split("-", 1)[0]
    try:
        y = int(head)
    except ValueError:
        return None
    return -y if neg else y


def parse_wikidata_sparql(obj: dict) -> list[dict]:
    """WDQS JSON → list of {pLabel,pBirth,pDeath,infLabel,infBirth,infDeath} rows."""
    rows = []
    for b in obj.get("results", {}).get("bindings", []):
        def g(k):
            return b.get(k, {}).get("value")
        rows.append({
            "pLabel": g("pLabel"), "pBirth": _year(g("pBirth")), "pDeath": _year(g("pDeath")),
            "infLabel": g("infLabel"), "infBirth": _year(g("infBirth")), "infDeath": _year(g("infDeath")),
        })
    return rows


def normalize_wikidata_rows(rows: list[dict], seed: str):
    """Rows → (nodes, flows, new_nodes, new_flows, dropped) through the full charter membrane."""
    nodes, flows = load(seed)
    seen_nodes, seen_flows = set(nodes), {f[":flow/id"] for f in flows}
    yr = {nid: (node_year(nd, ":hist/year-from"), node_year(nd, ":hist/year-to"))
          for nid, nd in nodes.items()}
    new_nodes, new_flows, dropped = [], [], []

    def ensure(label, birth, death):
        if not label or birth is None or death is None:     # N4 settled-only
            dropped.append((label or "?", "N4 missing dates")); return None
        nid = f"fig.{slug(label)}"
        if nid not in seen_nodes:
            new_nodes.append(make_node(label, birth, death, None, era_for_year(death)))
            seen_nodes.add(nid)
        yr[nid] = (birth, death)
        return nid

    for r in rows:
        src = ensure(r["infLabel"], r["infBirth"], r["infDeath"])
        dst = ensure(r["pLabel"], r["pBirth"], r["pDeath"])
        if not src or not dst or src == dst:
            continue
        if yr[src][0] > yr[dst][1]:                          # N5 forward-in-time
            dropped.append((f"{src}->{dst}", "N5 backward-in-time")); continue
        fid = f"fl.{slug(src)}.{slug(dst)}"
        if fid in seen_flows:
            continue
        seen_flows.add(fid); new_flows.append(make_edge(src, dst))
    return nodes, flows, new_nodes, new_flows, dropped


def fetch_wikidata_influence(limit: int = 200, timeout: int = 60) -> list[dict]:
    """Live WDQS fetch (G7 path). Returns parsed rows. Network required."""
    q = WIKIDATA_INFLUENCE_SPARQL % int(limit)
    url = WDQS_ENDPOINT + "?" + urllib.parse.urlencode({"query": q, "format": "json"})
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT,
                                               "Accept": "application/sparql-results+json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:   # nosec: public read-only endpoint
        return parse_wikidata_sparql(json.loads(resp.read().decode("utf-8")))


def fetch_pantheon_people(limit: int = 200, timeout: int = 60) -> list[dict]:
    """Best-effort Pantheon node-candidate fetch (CSV). Returns [{label,birth,death}].
    Pantheon gives NODES not edges (N1: HPI is NOT used as a score). Gracefully empty on failure."""
    try:
        req = urllib.request.Request(PANTHEON_CSV, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout) as resp:   # nosec
            text = resp.read().decode("utf-8", "replace")
    except Exception as ex:  # noqa: BLE001
        print(f"  (pantheon skipped: {ex})")
        return []
    import csv, io
    out = []
    rd = csv.DictReader(io.StringIO(text))
    for i, row in enumerate(rd):
        if i >= limit:
            break
        b = row.get("birthyear") or row.get("birth")
        d = row.get("deathyear") or row.get("death")
        name = row.get("name") or ""
        try:
            if name and b and d:
                out.append({"label": name, "birth": int(float(b)), "death": int(float(d))})
        except (ValueError, TypeError):
            continue
    return out


def write_merge(outdir: pathlib.Path, seed: str, new_nodes, new_flows, tag: str):
    add_file = outdir / f"influence-ingested{tag}.kotoba.edn"
    lines = [f";; tsumugi 紡ぎ — GENERATED ingest{tag} (ADR-2606061500). DO NOT hand-edit.",
             ";; :representative :scholarship; mirror-only (N2); N1/N4/N5 enforced. out/ only — "
             "promotion into the committed seed is a separate human-reviewed PR.",
             "[", ";; ── ingested figure nodes ──"]
    lines += [" " + edn_node(n) for n in new_nodes]
    lines += [";; ── ingested influence 縁 ──"] + [" " + edn_node(f) for f in new_flows] + ["]"]
    add_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    base = pathlib.Path(seed).read_text(encoding="utf-8").rstrip()
    assert base.endswith("]")
    add = ("\n ;; ── INGESTED" + tag + " ──\n"
           + "\n".join(" " + edn_node(n) for n in new_nodes) + "\n"
           + "\n".join(" " + edn_node(f) for f in new_flows) + "]\n")
    combined = outdir / f"seed-plus-ingest{tag}.kotoba.edn"
    combined.write_text(base[:-1] + add, encoding="utf-8")
    return add_file, combined


def main():
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = str(here / "data" / "seed-influence-history.kotoba.edn")
    fixtures = here / "data" / "ingest-influence"
    outdir = pathlib.Path(sys.argv[sys.argv.index('--out') + 1]) if '--out' in sys.argv else here / "out"
    outdir.mkdir(parents=True, exist_ok=True)
    limit = int(sys.argv[sys.argv.index('--limit') + 1]) if '--limit' in sys.argv else 200

    if "--live" in sys.argv:
        if not (os.environ.get("TSUMUGI_OPERATOR_GATE") == "1" and os.environ.get("TSUMUGI_OPERATOR_DID")):
            raise LiveGateRefused(
                "G7 — live influence ingest refused. Requires TSUMUGI_OPERATOR_GATE=1 + "
                "TSUMUGI_OPERATOR_DID=<operator attestation> (Council-ratified). "
                "Offline fixture ingest runs without --live.")
        print(f"⚠ G7 live gate satisfied (operator={os.environ['TSUMUGI_OPERATOR_DID']}) — "
              f"fetching Wikidata P737 (limit {limit})…")
        rows = fetch_wikidata_influence(limit)
        print(f"✓ WDQS returned {len(rows)} influence rows")
        if "--no-pantheon" not in sys.argv:
            pan = fetch_pantheon_people(limit)
            print(f"✓ Pantheon node-candidates: {len(pan)} (nodes only; N1 = no HPI score)")
        nodes, flows, new_nodes, new_flows, dropped = normalize_wikidata_rows(rows, seed)
        add_file, combined = write_merge(outdir, seed, new_nodes, new_flows, "-live")
        print(f"✓ live ingest: +{len(new_nodes)} nodes / +{len(new_flows)} 縁 "
              f"(seed {len(nodes)}/{len(flows)}); dropped {len(dropped)}")
        print(f"✓ wrote {add_file}\n✓ wrote {combined}  (out/ only — seed NOT auto-mutated)")
        return

    nodes, flows, new_nodes, new_flows, dropped = ingest_offline(fixtures, seed)
    add_file, combined = write_merge(outdir, seed, new_nodes, new_flows, "")
    print(f"✓ ingested {len(new_nodes)} new nodes · {len(new_flows)} new 縁 "
          f"(seed had {len(nodes)} nodes / {len(flows)} 縁)")
    if dropped:
        print(f"✓ refused/dropped {len(dropped)}:")
        for what, why in dropped:
            print(f"    - {what}: {why}")
    print(f"✓ wrote {add_file}\n✓ wrote {combined}  (run analyze/coverage on this to see the lift)")


if __name__ == "__main__":
    main()
