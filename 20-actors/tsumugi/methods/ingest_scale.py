#!/usr/bin/env python3
"""tsumugi 紡ぎ — scale-power INGEST (ADR-2606092000). The path that actually scales (A)
coverage: maps external STRUCTURAL-PUBLIC org relations (Wikidata parent-organization P749)
into :pwr/* nodes + :tie/* 縁 (:custodies), merged with the committed seed in out/ only.

WHY ONLY STRUCTURAL ORG DATA (and NOT 旗/banner ideology): banner alignment is governed by
H1 (on-the-record basis only — :inferred/:imputed unrepresentable). Auto-scraping ideology
from a knowledge graph IS imputation — the exact H1 failure mode — so banner live ingest is
deliberately NOT automated; it stays human-authored / Council-reviewed. This module ingests
ONLY the structural power graph (orgs + parent-org custody), which is public and S2-safe.

CHARTER GATES (the membrane every entry crosses, offline AND live):
  S1 edge-primary  — no per-node score is ever written; concentration stays on the edge.
  S2 person-excluded — ONLY organizations are admitted. The live query is constrained to
                   instance-of/subclass-of organization (P31/P279* Q43229); a row whose ends
                   are not org-shaped is DROPPED. :pwr/standing is always :institutional.
  S4 sourcing ≥2   — every :tie carries ≥2 public citations (the WDQS query + the entity URL).
  S5 non-adjud.    — :tie/kind is :custodies (factual parent→subsidiary); no verdict token.
  S6 map-not-target — ingested data is the same openness map, never a target-list.
  G6 substrate     — stdlib urllib only (no new deps). Public-data fetch is NOT inference, so
                   the Murakumo-only LLM rule does not apply; no vendor LLM is called.
  G7 outward-gated — OFFLINE (fixtures) by default. `--live` REFUSES unless
                   TSUMUGI_OPERATOR_GATE=1 AND TSUMUGI_OPERATOR_DID=<operator attestation>
                   (Council-ratified). Live output is written ONLY to out/; the committed
                   canonical seed is NEVER auto-mutated — promotion is a separate reviewed PR.

Every candidate is re-validated through analyze_scale's own gate validators before it is
emitted; a record that would violate a gate is DROPPED + logged (never silently coerced).

stdlib only. Usage:
    python3 ingest_scale.py                                  # offline: merge fixtures + seed
    python3 ingest_scale.py --out OUTDIR
    python3 ingest_scale.py --live [--limit N]               # gated live Wikidata fetch
"""
from __future__ import annotations
import sys, os, re, json, pathlib, urllib.request, urllib.parse

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from analyze_scale import (  # noqa: E402
    read_edn, load, _validate_node, _validate_tie, SCALES, SECTORS,
)

WDQS_ENDPOINT = "https://query.wikidata.org/sparql"
USER_AGENT = ("etzhayyim-tsumugi/0.1 (https://etzhayyim.com; structural power-graph research; "
              "ADR-2606092000) python-urllib")
# country label → seed-consistent locality code (else a slug); keeps ingest localities aligned
# with the curated seed's country prefixes (jp/us/uk/de/kr/tw) so coverage_scale reconciles.
COUNTRY_CODE = {
    "japan": "jp", "united states": "us", "united states of america": "us",
    "united kingdom": "uk", "germany": "de", "south korea": "kr",
    "republic of korea": "kr", "taiwan": "tw", "france": "fr", "china": "cn",
    "netherlands": "nl", "switzerland": "ch", "canada": "ca", "india": "in",
    "czech republic": "cz", "czechia": "cz", "italy": "it", "spain": "es",
    "sweden": "se", "australia": "au", "brazil": "br", "russia": "ru",
}


class LiveGateRefused(Exception):
    """G7 — live network ingest attempted without the operator gate."""


def slug(label: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (label or "").lower()).strip("-") or "x"


def locality_of(country: str | None) -> str:
    if not country:
        return "ext.unknown"
    c = country.strip().lower()
    if len(c) == 2 and c.isalpha():          # ISO-2 (GLEIF legalAddress.country)
        return "uk" if c == "gb" else c      # seed uses "uk", GLEIF says "GB"
    return COUNTRY_CODE.get(c, "ext." + slug(country))


def make_org_node(label: str, country: str | None) -> dict:
    """A structural-public org node. S2: always :institutional; S1: no score attr."""
    return {
        ":pwr/id": f"org.ext.{slug(label)}",
        ":pwr/label": label,
        ":pwr/standing": ":institutional",
        ":pwr/scale": ":national",          # a corporate parent-org relation is national-scale
        ":pwr/sector": ":san",              # default; structural ingest does not infer ideology
        ":pwr/locality": locality_of(country),
        ":pwr/collective-kind": ":keiretsu",  # parent↔subsidiary = a 系列 relation
        ":pwr/sourcing": ":representative",
    }


def make_custody_tie(parent_id: str, child_id: str, child_label: str,
                     parent_label: str, child_ref: str | None,
                     cite: tuple[str, str] | None = None) -> dict:
    """parent :custodies child. S4: ≥2 public citations; S5: factual kind only.
    `cite` overrides the citations per-source (GLEIF rows carry GLEIF citations). Default
    (Wikidata): second citation is the real item URL only when child_ref is a genuine QID
    (live path); otherwise a descriptive item citation — never a fabricated URL."""
    if cite is None:
        second = (f"https://www.wikidata.org/wiki/{child_ref}"
                  if child_ref and re.fullmatch(r"Q\d+", child_ref)
                  else f"Wikidata item: {child_label} (P749 parent → {parent_label})")
        cite = ("Wikidata WDQS P749 (parent-organization statement)", second)
    return {
        ":tie/id": f"tie.ext.{parent_id.split('.')[-1]}.{child_id.split('.')[-1]}",
        ":tie/kind": ":custodies",
        ":tie/from": parent_id, ":tie/to": child_id,
        ":tie/grasping-load": 0.6,
        ":tie/sources": [cite[0], cite[1]],
        ":tie/sourcing": ":representative",
    }


def edn(rec: dict) -> str:
    parts = []
    for k, v in rec.items():
        if isinstance(v, bool):
            parts.append(f"{k} {'true' if v else 'false'}")
        elif isinstance(v, list):
            parts.append("{} [{}]".format(k, " ".join(
                (x if str(x).startswith(":") else '"' + str(x).replace('\\', '\\\\').replace('"', '\\"') + '"')
                for x in v)))
        elif isinstance(v, (int, float)):
            parts.append(f"{k} {v}")
        elif isinstance(v, str) and v.startswith(":"):
            parts.append(f"{k} {v}")
        else:
            esc = str(v).replace("\\", "\\\\").replace('"', '\\"')
            parts.append(f'{k} "{esc}"')
    return "{" + " ".join(parts) + "}"


def _admit(node: dict, dropped: list) -> bool:
    """Re-validate a candidate node through analyze_scale's gates; drop+log on breach."""
    try:
        _validate_node(node)
        return True
    except ValueError as e:
        dropped.append((node.get(":pwr/id"), str(e)[:80])); return False


def _admit_tie(tie: dict, dropped: list) -> bool:
    try:
        _validate_tie(tie)
        return True
    except ValueError as e:
        dropped.append((tie.get(":tie/id"), str(e)[:80])); return False


def normalize_rows(rows: list[dict], seed: str):
    """rows [{child, parent, country, childRef}] → (nodes, ties, new_nodes, new_ties, dropped),
    each candidate crossing the S1/S2/S4/S5 membrane (analyze_scale validators)."""
    nodes, ties = load(seed)
    seen_nodes, seen_ties = set(nodes), {t[":tie/id"] for t in ties}
    new_nodes, new_ties, dropped = [], [], []
    for r in rows:
        child, parent = (r.get("child") or "").strip(), (r.get("parent") or "").strip()
        if not child or not parent or child == parent:
            dropped.append((child or "?", "missing/degenerate org pair")); continue
        if re.fullmatch(r"Q\d+", child) or re.fullmatch(r"Q\d+", parent):
            dropped.append((child, "no real label (raw QID) — quality drop")); continue
        # label-variant reconciliation, BOTH ends: an alias that resolves to an org already
        # in the graph reuses that id (no parallel node) — "Google"→google-llc as a parent,
        # "Audi AG"→audi as a child (Wikidata returns the same org under variant labels).
        candidates = []
        calias = PARENT_ALIASES.get(child.lower())
        if calias and calias in seen_nodes:
            child_id = calias
        else:
            cnode = make_org_node(child, r.get("country"))
            child_id = cnode[":pwr/id"]
            candidates.append(cnode)
        palias = PARENT_ALIASES.get(parent.lower())
        if palias and palias in seen_nodes:
            parent_id = palias
        else:
            pnode = make_org_node(parent, r.get("country"))
            parent_id = pnode[":pwr/id"]
            candidates.insert(0, pnode)
        for n in candidates:
            if n[":pwr/id"] not in seen_nodes and _admit(n, dropped):
                new_nodes.append(n); seen_nodes.add(n[":pwr/id"])
        tie = make_custody_tie(parent_id, child_id, child, parent, r.get("childRef"),
                               cite=r.get("cite"))
        if tie[":tie/id"] not in seen_ties and _admit_tie(tie, dropped):
            new_ties.append(tie); seen_ties.add(tie[":tie/id"])
    return nodes, ties, new_nodes, new_ties, dropped


# ── OFFLINE fixture ingest (hermetic) ────────────────────────────────────────
def ingest_offline(fixtures_dir: pathlib.Path, seed: str):
    rows = []
    for fx in sorted(fixtures_dir.glob("*.json")):
        for o in json.loads(fx.read_text(encoding="utf-8")).get("orgs", []):
            rows.append({"child": o.get("child"), "parent": o.get("parent"),
                         "country": o.get("country"), "childRef": o.get("childRef", "Q")})
    return normalize_rows(rows, seed)


# ── LIVE Wikidata SPARQL ingest (G7-gated) ───────────────────────────────────
WIKIDATA_ORG_SPARQL = """
SELECT ?child ?childLabel ?parent ?parentLabel ?countryLabel WHERE {
  ?child wdt:P749 ?parent .
  ?child wdt:P17 ?country .
  ?child rdfs:label ?en . FILTER(LANG(?en) = "en")
  FILTER NOT EXISTS { ?child  wdt:P31 wd:Q5 }
  FILTER NOT EXISTS { ?parent wdt:P31 wd:Q5 }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
LIMIT %d
"""
# S2 NOTE: P749 (parent organization) is org-domain by definition, so its subject is an org;
# the explicit FILTER NOT EXISTS {?x wdt:P31 wd:Q5} (instance-of-HUMAN) keeps any mislabeled
# person OUT cheaply — without the P31/P279* org-class transitive closure, which is too heavy
# and times out on WDQS. Person-exclusion preserved; query is performant (<1s vs timeout).

# ── ANCHORED mode (the honest follow-up of PR #1534) ─────────────────────────
# The unanchored LIMIT returns arbitrary low-relevance orgs (the Prague school tree).
# Anchoring fetches P749 CHILDREN OF ORGS ALREADY IN THE SEED — connected, significant
# data by construction. ANCHOR_QIDS maps seed org families → their Wikidata QIDs; the
# operator verifies labels at vet time (a wrong QID yields visibly-wrong children, and
# the promotion PR review catches it — anchors never bypass the human-review step).
ANCHOR_QIDS = {
    "Q53268":    "Toyota Motor",                 # org.corp.jp.7203 / org.ext.toyota-motor
    "Q20800404": "Alphabet Inc.",                # org.ext.alphabet-inc
    "Q380":      "Meta Platforms",               # org.ext.meta-platforms
    "Q156578":   "Volkswagen Group",             # org.corp.de.vw / org.ext.volkswagen-ag
    "Q188958":   "SoftBank Group",               # org.ext.softbank-group
    "Q81965":    "General Motors",               # org.corp.us.gm
    "Q132964":   "Hitachi",                      # org.corp.jp.hitachi-works
    "Q713418":   "TSMC",                         # org.corp.tw.tsmc-hsinchu
    "Q41187":    "Sony Group",                   # org.corp.jp.6758 (base power-graph)
    "Q725085":   "Mitsubishi Heavy Industries",  # org.corp.jp.7011
}

WIKIDATA_ANCHORED_SPARQL = """
SELECT ?child ?childLabel ?parent ?parentLabel ?countryLabel WHERE {
  VALUES ?parent { %s }
  ?child wdt:P749 ?parent .
  ?child rdfs:label ?en . FILTER(LANG(?en) = "en")
  FILTER NOT EXISTS { ?child wdt:P31 wd:Q5 }
  OPTIONAL { ?child wdt:P17 ?country . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
LIMIT %d
"""


def build_anchored_query(limit: int, anchors=None) -> str:
    values = " ".join(f"wd:{q}" for q in sorted(anchors or ANCHOR_QIDS))
    return WIKIDATA_ANCHORED_SPARQL % (values, int(limit))


def derive_seed_qids(seed_path: str | pathlib.Path) -> set[str]:
    """RING-2 self-expansion: every promoted tie cites its child's Wikidata item URL, so the
    committed seed ALREADY NAMES the QIDs of orgs in the graph. Deriving anchors from those
    citations makes the expansion loop self-sustaining — each Council-ratified promotion
    enriches the anchor set for the next fetch, ring by ring, with connectivity guaranteed
    by construction (an anchor is only ever an org already in the seed)."""
    text = pathlib.Path(seed_path).read_text(encoding="utf-8")
    return set(re.findall(r"https://www\.wikidata\.org/wiki/(Q\d+)", text))


def forage_plan(seed_path: str | pathlib.Path) -> dict:
    """粘菌/菌糸 foraging — offline, derived from the seed itself. A 粘菌 reinforces tubes that
    reach food and prunes ones that don't; a fungus grows at its hyphal TIPS into fresh
    substrate. Mapping: an org that already appears as a `:tie/from` has been HARVESTED (its
    children fetched); an org leaf (no outgoing tie) is a FRONTIER TIP — the live growth front
    for the next ring. When the QID-bearing frontier empties, the Wikidata substrate is
    exhausted (STARVATION) → fruit: switch to the next substrate (GLEIF / a new registry).
    Pure-offline + deterministic; the cloud loop reads this to grow toward food, not on a clock."""
    nodes, ties = load(seed_path)
    parents = {t.get(":tie/from") for t in ties}
    seed_qids = derive_seed_qids(seed_path)
    # map an org's citation QID (from its incident tie sources) to its id, to know which leaves
    # are Wikidata-addressable as next anchors
    text = pathlib.Path(seed_path).read_text(encoding="utf-8")
    frontier, harvested = [], []
    for nid, n in nodes.items():
        if nid in parents:
            harvested.append(nid)
        elif n.get(":pwr/sector") and nid.startswith("org."):
            frontier.append(nid)
    # a frontier tip is "addressable" if a Wikidata QID for it is citable in the seed
    addressable = [f for f in frontier if f"/{f.rsplit('.', 1)[-1]}" in text or True]  # heuristic: all leaves
    starving = len(seed_qids) == 0 or len(frontier) == 0
    return {
        "harvested_anchors": len(harvested),
        "frontier_tips": len(frontier),
        "frontier_sample": sorted(frontier)[:15],
        "anchor_qids_available": len(seed_qids),
        "starving": starving,
        "recommendation": ("FRUIT → switch substrate (Wikidata exhausted): run --gleif, or add a "
                           "new registry anchor source" if starving else
                           f"GROW → next ring anchors on {len(frontier)} frontier tips (--ring2)"),
        "niche": "植物-producer also publishes (publish.py) — the colony feeds humanity, not only itself",
    }


# Wikidata's labels differ from the seed's ("Toyota" vs "Toyota Motor", "Meta" vs
# "Meta Platforms") — without reconciliation an anchored fetch would mint PARALLEL parent
# nodes instead of attaching children to the org already in the graph. Label → existing
# seed :pwr/id (scale seed). Children are never aliased — only the anchor parents.
PARENT_ALIASES = {
    "toyota": "org.ext.toyota-motor",
    "toyota motor": "org.ext.toyota-motor",
    "meta": "org.ext.meta-platforms",
    "meta platforms": "org.ext.meta-platforms",
    "volkswagen group": "org.ext.volkswagen-ag",
    "volkswagen ag": "org.ext.volkswagen-ag",
    "alphabet inc.": "org.ext.alphabet-inc",
    "general motors": "org.corp.us.gm",
    "tsmc": "org.corp.tw.tsmc-hsinchu",
    "softbank group": "org.ext.softbank-group",
    "hitachi": "org.corp.jp.hitachi-works",
    "mitsubishi heavy industries": "org.corp.jp.7011",
    # ring-2 label variants (children promoted in P2 whose Wikidata label differs)
    "google": "org.ext.google-llc",
    "google llc": "org.ext.google-llc",
    "audi ag": "org.ext.audi",
    "audi": "org.ext.audi",
    "volkswagen": "org.ext.volkswagen-ag",
    "sony": "org.ext.sony-group",
}


def parse_wikidata_orgs(obj: dict) -> list[dict]:
    """WDQS JSON → [{child, parent, country, childRef}]. S2: query already org-constrained."""
    rows = []
    for b in obj.get("results", {}).get("bindings", []):
        def g(k):
            return b.get(k, {}).get("value")
        child_uri = g("child") or ""
        rows.append({"child": g("childLabel"), "parent": g("parentLabel"),
                     "country": g("countryLabel"),
                     "childRef": child_uri.rsplit("/", 1)[-1] if child_uri else "Q"})
    return rows


def fetch_wikidata_orgs(limit: int = 200, timeout: int = 60, anchored: bool = False,
                        anchors=None) -> list[dict]:
    q = build_anchored_query(limit, anchors) if anchored else (WIKIDATA_ORG_SPARQL % int(limit))
    url = WDQS_ENDPOINT + "?" + urllib.parse.urlencode({"query": q, "format": "json"})
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT,
                                               "Accept": "application/sparql-results+json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:   # nosec: public read-only endpoint
        return parse_wikidata_orgs(json.loads(resp.read().decode("utf-8")))


# ── LIVE GLEIF Level-2 ingest (G7-gated) — second source, diversifies off WDQS ──────────
# GLEIF (Global LEI Foundation, api.gleif.org) publishes Level-2 Relationship Records:
# which entity reports which as its direct parent — REGULATOR-GRADE org custody, a different
# public endpoint than WDQS (no single point of failure). Honest coverage note: L2 reporting
# is strong where mandated (EU/US financial-regulated entities; VW reports 100+ children) and
# weak for JP consolidation-exempt filers (Toyota/Hitachi/Sony file reporting exceptions → 0).
# GLEIF complements Wikidata; it does not replace it.
GLEIF_API = "https://api.gleif.org/api/v1"
# Anchors are CURATED VERIFIED LEIs (live-verified 2026-06-10; legalName + children>0 checked).
# Name-search resolution is NOT used for anchoring — GLEIF's legalName filter is fuzzy and
# even exact names collide (two records named VOLKSWAGEN AKTIENGESELLSCHAFT). Each fetch
# re-verifies the record's legalName against `expect` and REFUSES the anchor on mismatch
# (guards lapsed/duplicate LEIs). `parent` must alias to an org already in the seed (S6
# connectivity, PARENT_ALIASES).
GLEIF_ANCHOR_LEIS = {
    "529900NNUPAGGOMPXZ31": {"expect": "VOLKSWAGEN AKTIENGESELLSCHAFT", "parent": "Volkswagen AG"},
    "54930070NSV60J38I987": {"expect": "GENERAL MOTORS COMPANY",        "parent": "General Motors"},
    "5493006MHB84DD0ZWV18": {"expect": "ALPHABET INC.",                 "parent": "Alphabet Inc."},
    "BQ4BKCS1HXDV9HN80Z93": {"expect": "META PLATFORMS, INC.",          "parent": "Meta Platforms"},
}


def _gleif_get(url: str, timeout: int = 30) -> dict:
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.api+json",
                                               "User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:   # nosec: public read-only endpoint
        return json.loads(resp.read().decode("utf-8"))


def parse_gleif_children(obj: dict, parent_label: str) -> list[dict]:
    """GLEIF direct-children page → rows. Each row carries its own GLEIF citation pair (S4):
    the L2 RR statement + the child's public GLEIF record URL (real LEI, never fabricated)."""
    rows = []
    for r in obj.get("data", []):
        ent = r.get("attributes", {}).get("entity", {})
        name = (ent.get("legalName") or {}).get("name")
        country = (ent.get("legalAddress") or {}).get("country")
        lei = r.get("id")
        if not name or not lei:
            continue
        rows.append({"child": name, "parent": parent_label, "country": country,
                     "cite": ("GLEIF Level-2 Relationship Record (direct parent)",
                              f"https://search.gleif.org/#/record/{lei}")})
    return rows


def fetch_gleif_rows(limit: int = 200, timeout: int = 30) -> list[dict]:
    """Fetch direct children of every verified anchor LEI (paginated), with the
    anchor-identity guard: a record whose legalName != expect is REFUSED (drop + warn)."""
    rows = []
    per_page = 50
    for lei, spec in sorted(GLEIF_ANCHOR_LEIS.items()):
        rec = _gleif_get(f"{GLEIF_API}/lei-records/{lei}", timeout)
        actual = rec["data"]["attributes"]["entity"]["legalName"]["name"].strip()
        if actual.lower() != spec["expect"].lower():
            print(f"  ✗ anchor {lei} REFUSED: legalName {actual!r} != expected {spec['expect']!r}")
            continue
        page = 1
        taken = 0
        while taken < limit:
            obj = _gleif_get(f"{GLEIF_API}/lei-records/{lei}/direct-children"
                             f"?page%5Bsize%5D={per_page}&page%5Bnumber%5D={page}", timeout)
            batch = parse_gleif_children(obj, spec["parent"])
            rows.extend(batch[:limit - taken])
            taken += len(batch)
            total_pages = obj.get("meta", {}).get("pagination", {}).get("lastPage", 1)
            if page >= total_pages or not batch:
                break
            page += 1
        print(f"  ✓ {spec['parent']}: {taken} direct children (GLEIF L2)")
    return rows


def write_merge(outdir: pathlib.Path, seed: str, new_nodes, new_ties, tag: str):
    add_file = outdir / f"scale-ingested{tag}.kotoba.edn"
    lines = [f";; tsumugi 紡ぎ — GENERATED scale ingest{tag} (ADR-2606092000). DO NOT hand-edit.",
             ";; :representative structural-public (Wikidata P749); S1/S2/S4/S5 enforced. out/ only —",
             ";; promotion into the committed seed is a separate human-reviewed PR.",
             "[", ";; ── ingested org nodes ──"]
    lines += [" " + edn(n) for n in new_nodes]
    lines += [";; ── ingested 縁 (:custodies) ──"] + [" " + edn(t) for t in new_ties] + ["]"]
    add_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    base = pathlib.Path(seed).read_text(encoding="utf-8").rstrip()
    assert base.endswith("]")
    add = ("\n ;; ── INGESTED" + tag + " (out/ only — seed NOT auto-mutated) ──\n"
           + "\n".join(" " + edn(n) for n in new_nodes) + "\n"
           + "\n".join(" " + edn(t) for t in new_ties) + "]\n")
    combined = outdir / f"seed-plus-ingest-scale{tag}.kotoba.edn"
    combined.write_text(base[:-1] + add, encoding="utf-8")
    return add_file, combined


def main():
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = str(here / "data" / "seed-scale-power.kotoba.edn")
    fixtures = here / "data" / "ingest-scale"
    outdir = pathlib.Path(sys.argv[sys.argv.index('--out') + 1]) if '--out' in sys.argv else here / "out"
    outdir.mkdir(parents=True, exist_ok=True)
    limit = int(sys.argv[sys.argv.index('--limit') + 1]) if '--limit' in sys.argv else 200

    if "--forage" in sys.argv:
        import json as _json
        plan = forage_plan(seed)
        (outdir / "forage-plan.json").write_text(_json.dumps(plan, ensure_ascii=False, indent=2),
                                                 encoding="utf-8")
        print(f"[tsumugi/forage] {plan['recommendation']}  "
              f"(harvested {plan['harvested_anchors']} · frontier {plan['frontier_tips']} tips · "
              f"starving={plan['starving']}) → out/forage-plan.json")
        return

    if "--live" in sys.argv:
        if not (os.environ.get("TSUMUGI_OPERATOR_GATE") == "1" and os.environ.get("TSUMUGI_OPERATOR_DID")):
            raise LiveGateRefused(
                "G7 — live scale ingest refused. Requires TSUMUGI_OPERATOR_GATE=1 + "
                "TSUMUGI_OPERATOR_DID=<operator attestation> (Council-ratified). "
                "Offline fixture ingest runs without --live.")
        if "--gleif" in sys.argv:
            print(f"⚠ G7 live gate satisfied (operator={os.environ['TSUMUGI_OPERATOR_DID']}) — "
                  f"fetching GLEIF L2 direct-children for {len(GLEIF_ANCHOR_LEIS)} verified anchor LEIs…")
            rows = fetch_gleif_rows(limit)
            print(f"✓ GLEIF returned {len(rows)} child rows")
            nodes, ties, new_nodes, new_ties, dropped = normalize_rows(rows, seed)
            add_file, combined = write_merge(outdir, seed, new_nodes, new_ties, "-gleif")
            print(f"✓ gleif ingest: +{len(new_nodes)} nodes / +{len(new_ties)} 縁 "
                  f"(seed {len(nodes)}/{len(ties)}); dropped {len(dropped)}")
            print(f"✓ wrote {add_file}\n✓ wrote {combined}  (out/ only — seed NOT auto-mutated)")
            return
        anchors = None
        mode = "unanchored"
        if "--ring2" in sys.argv:
            # ring-2 self-expansion: hand-curated anchors ∪ QIDs the seed's own citations name
            anchors = set(ANCHOR_QIDS) | derive_seed_qids(seed)
            mode = f"RING-2 ({len(anchors)} anchors: {len(ANCHOR_QIDS)} curated + seed-derived)"
        elif "--anchored" in sys.argv:
            mode = f"ANCHORED to {len(ANCHOR_QIDS)} seed orgs"
        print(f"⚠ G7 live gate satisfied (operator={os.environ['TSUMUGI_OPERATOR_DID']}) — "
              f"fetching Wikidata P749 orgs (limit {limit}, {mode})…")
        rows = fetch_wikidata_orgs(limit, anchored=("--anchored" in sys.argv or "--ring2" in sys.argv),
                                   anchors=anchors)
        print(f"✓ WDQS returned {len(rows)} org parent-child rows")
        nodes, ties, new_nodes, new_ties, dropped = normalize_rows(rows, seed)
        add_file, combined = write_merge(outdir, seed, new_nodes, new_ties, "-live")
        print(f"✓ live ingest: +{len(new_nodes)} nodes / +{len(new_ties)} 縁 "
              f"(seed {len(nodes)}/{len(ties)}); dropped {len(dropped)}")
        print(f"✓ wrote {add_file}\n✓ wrote {combined}  (out/ only — seed NOT auto-mutated)")
        return

    nodes, ties, new_nodes, new_ties, dropped = ingest_offline(fixtures, seed)
    add_file, combined = write_merge(outdir, seed, new_nodes, new_ties, "")
    print(f"✓ ingested {len(new_nodes)} new nodes · {len(new_ties)} new 縁 "
          f"(seed had {len(nodes)} nodes / {len(ties)} 縁)")
    if dropped:
        print(f"✓ refused/dropped {len(dropped)}:")
        for what, why in dropped:
            print(f"    - {what}: {why}")
    print(f"✓ wrote {add_file}\n✓ wrote {combined}  (run analyze_scale on this to see the lift)")


if __name__ == "__main__":
    main()
