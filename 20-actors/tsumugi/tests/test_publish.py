#!/usr/bin/env python3
"""tsumugi publish.py tests — etzhayyim as a self-sovereign linked-data PROVIDER (ADR-2606092000).

Verifies:
  - N-Triples are well-formed (every line `<s> <p> <o|"lit"> .`)
  - JSON-LD parses, carries the etzhayyim @context (epw vocabulary), one node per seed org
  - the DERIVED original layer (per-locality concentration) is published as etzhayyim's own data
  - manifest declares license + publisher DID + content-hash + honest provenance
  - S2 person-exclusion survives the projection (only Org/PublicSeat/Locality types)
  - counts match the seed; content-hash is deterministic
"""
import sys, json, pathlib, tempfile

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))
import publish as P  # noqa: E402
import analyze_scale as A  # noqa: E402

PASS, FAIL = "\033[32mPASS\033[0m", "\033[31mFAIL\033[0m"
results = []

def check(name, cond):
    results.append(bool(cond))
    print(f"  [{PASS if cond else FAIL}] {name}")


def main():
    print("\n=== tsumugi publish (provider) tests ===")
    with tempfile.TemporaryDirectory() as d:
        out = pathlib.Path(d)
        manifest = P.publish(out)
        nt = (out / "etzhayyim-power-graph.nt").read_text(encoding="utf-8").splitlines()
        jsonld = json.loads((out / "etzhayyim-power-graph.jsonld").read_text(encoding="utf-8"))
        man2 = json.loads((out / "dataset-manifest.json").read_text(encoding="utf-8"))

    nodes, ties = A.load()

    # N-Triples well-formed
    check("N-Triples emitted", len(nt) > 1000)
    check("every triple ends with ' .' and starts with '<'",
          all(line.startswith("<") and line.endswith(" .") for line in nt if line))

    # JSON-LD shape
    check("JSON-LD has etzhayyim vocabulary @context",
          jsonld["@context"]["epw"] == P.NS)
    graph_ids = {n["@id"] for n in jsonld["@graph"]}
    check("one entity IRI per seed node",
          all(P.ID + nid in graph_ids for nid in list(nodes)[:50]))
    check("entity IRIs live under etzhayyim's namespace",
          all(i.startswith(P.ID) for i in graph_ids))

    # derived ORIGINAL layer published (the value nobody else has)
    check("derived 産官学報 concentration is published",
          any("ns/power#concentration" in line for line in nt))
    check("derived layer attributes etzhayyim as author",
          any("derivedBy" in line and P.PUBLISHER_DID in line for line in nt))

    # manifest = a real dataset descriptor
    check("manifest declares the Charter license", "Charter Compliance Rider" in man2["license"])
    check("manifest declares the publisher DID", man2["publisher"] == P.PUBLISHER_DID)
    check("manifest carries a content-hash (self-sovereign identity)",
          man2["contentHash"].startswith("sha256:") and len(man2["contentHash"]) == 71)
    check("manifest provenance names upstreams + etzhayyim-derived layers",
          man2["provenance"]["upstreamSources"] and man2["provenance"]["etzhayyimDerived"])
    check("manifest node count matches seed", man2["counts"]["nodes"] == len(nodes))

    # S2 — projection never emits a person; only Org / PublicSeat / Locality classes
    types = {n.get("@type") for n in jsonld["@graph"]}
    check("S2: only Org/PublicSeat/Locality types (no person class)",
          types <= {"epw:Org", "epw:PublicSeat", "epw:Locality"})

    # deterministic identity
    with tempfile.TemporaryDirectory() as d2:
        m2 = P.publish(pathlib.Path(d2))
    check("content-hash is deterministic", manifest["contentHash"] == m2["contentHash"])

    print(f"\n{sum(results)}/{len(results)} passed")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
