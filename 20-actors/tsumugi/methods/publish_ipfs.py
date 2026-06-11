#!/usr/bin/env python3
"""tsumugi 紡ぎ — PIN the published power-graph to kotoba IPFS + serve it at etzhayyim.com.

publish.py makes the linked data; this makes it PERSIST and be VERIFIABLE without trusting a
host (ADR-2606092000 wave 5, mirroring rasen 80-data/genome / ADR-2606101000):

  (A) content-address each artifact to a kotoba IPFS CIDv1 (raw, sha2-256) — byte-identical to
      `ipfs add --cid-version=1 --raw-leaves`, verifiable with NO daemon. Artifacts are gzipped
      with mtime=0 so the bytes (hence the CID) are DETERMINISTIC and < the 256 KiB single-block
      limit. Written to 80-data/tsumugi-power/ (the G8 DataLad→IPFS dataset home) — committed,
      so the dataset is durable in git AND pin-able by CID (`ipfs add` yields the same CID).
  (B) write a small descriptor into the apex Worker's static dir (50-infra/etzhayyim-did-web/
      public/), so https://etzhayyim.com/ns/power (the vocabulary) and
      https://etzhayyim.com/dataset/tsumugi-power.json (CIDs + gateway links) RESOLVE — closing
      the 404. The big data lives on IPFS (host-independent); etzhayyim.com only advertises it.

stdlib only. Usage:  python3 publish_ipfs.py
"""
from __future__ import annotations
import sys, gzip, json, hashlib, pathlib, tempfile

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
ROOT = ACTOR_DIR.parents[1]
sys.path.insert(0, str(ACTOR_DIR / "methods"))
import publish  # noqa: E402

DATA_DIR = ROOT / "80-data" / "tsumugi-power"
APEX_PUBLIC = ROOT / "50-infra" / "etzhayyim-did-web" / "public"
PUBLISHED_AT = "2026-06-11"           # fixed → deterministic descriptor (CIDs are over .gz bytes)
GATEWAYS = ["https://ipfs.io/ipfs/", "https://dweb.link/ipfs/", "https://cloudflare-ipfs.com/ipfs/"]

# ── kotoba IPFS CIDv1 (raw, sha2-256, base32) — copied from rasen/methods/cid.py (ADR-2606101000);
#    byte-identical to `ipfs add --cid-version=1 --raw-leaves` for a single < 256 KiB raw block.
_B32 = "abcdefghijklmnopqrstuvwxyz234567"

def _base32(data: bytes) -> str:
    bits = val = 0; out = []
    for b in data:
        val = (val << 8) | b; bits += 8
        while bits >= 5:
            out.append(_B32[(val >> (bits - 5)) & 31]); bits -= 5
    if bits > 0:
        out.append(_B32[(val << (5 - bits)) & 31])
    return "".join(out)

def cidv1_raw(data: bytes) -> str:
    mh = bytes([0x12, 0x20]) + hashlib.sha256(data).digest()
    return "b" + _base32(bytes([0x01, 0x55]) + mh)

SINGLE_BLOCK = 256 * 1024


def _gz(data: bytes) -> bytes:
    """gzip with mtime=0 → deterministic bytes (so the CID is reproducible)."""
    return gzip.compress(data, compresslevel=9, mtime=0)


def pin():
    # 1. regenerate the linked data into a temp, read the canonical EDN graph
    with tempfile.TemporaryDirectory() as d:
        manifest = publish.publish(pathlib.Path(d))
        nt = (pathlib.Path(d) / "etzhayyim-power-graph.nt").read_bytes()
        jsonld = (pathlib.Path(d) / "etzhayyim-power-graph.jsonld").read_bytes()
    edn = (ACTOR_DIR / "data" / "seed-scale-power.kotoba.edn").read_bytes()

    # 2. gzip + content-address each artifact (single-block CIDv1)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    artifacts = {}
    for key, fname, raw in (("graph", "power-graph.kotoba.edn.gz", edn),
                            ("ntriples", "power-graph.nt.gz", nt),
                            ("jsonld", "power-graph.jsonld.gz", jsonld)):
        gz = _gz(raw)
        if len(gz) > SINGLE_BLOCK:
            raise ValueError(f"{fname} gz {len(gz)}B > single-block limit — would need dag-pb")
        (DATA_DIR / fname).write_bytes(gz)
        artifacts[key] = {"file": fname, "bytes": len(gz), "raw_bytes": len(raw),
                          "cid": cidv1_raw(gz),
                          "note": "gzip mtime=0; CID == `ipfs add --cid-version=1 --raw-leaves`"}

    # 3. the publish-manifest (genome convention) — license + provenance + DID + CIDs + gateways
    pm = {
        "actor": "tsumugi", "adr": "2606092000", "published_at": PUBLISHED_AT,
        "title": manifest["title"], "publisher": publish.PUBLISHER_DID,
        "license": publish.LICENSE, "vocabulary": publish.NS, "entityNamespace": publish.ID,
        "contentHash_ntriples": manifest["contentHash"],
        "counts": manifest["counts"], "provenance": manifest["provenance"],
        "artifacts": artifacts, "gateways": GATEWAYS,
        "verify": "python3 20-actors/tsumugi/methods/publish_ipfs.py --verify  (re-content-address)",
    }
    (DATA_DIR / "publish-manifest.json").write_text(
        json.dumps(pm, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _write_publish_md(pm)

    # 4. (B) serve a descriptor at etzhayyim.com via the apex static dir
    (APEX_PUBLIC / "ns").mkdir(parents=True, exist_ok=True)
    (APEX_PUBLIC / "dataset").mkdir(parents=True, exist_ok=True)
    (APEX_PUBLIC / "ns" / "power").write_text(_vocab_jsonld() + "\n", encoding="utf-8")
    (APEX_PUBLIC / "dataset" / "tsumugi-power.json").write_text(
        json.dumps({**pm, "fetch": {a: [g + v["cid"] for g in GATEWAYS]
                                     for a, v in artifacts.items()}},
                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return pm


def _vocab_jsonld() -> str:
    """The epw: vocabulary, resolvable at https://etzhayyim.com/ns/power (closes the 404)."""
    terms = {
        "Org": "an organisation / 法人 / institution (a power-holding collective)",
        "PublicSeat": "a public-power SEAT (chair/exec/official) — never a private individual (S2)",
        "Locality": "a place cluster bearing an etzhayyim-derived 産官学報 concentration readout",
        "custodies": "parent organisation controls/owns the object (P749-grade)",
        "dependsOn": "supply / funding / IP dependency", "concentration":
        "etzhayyim-DERIVED 産官学報 cross-sector concentration (edge-primary integral × diversity)",
        "scale": "global→supranational→national→regional→municipal→local→intra-org",
        "sector": "産官学報民金", "collectiveKind": "組織/地域/市区町村/コミュニティ/社内派閥/学閥/系列/審議会",
        "derivedBy": "the DID that authored this (etzhayyim-original) assertion",
    }
    return json.dumps({
        "@context": {"@vocab": publish.NS, "rdfs": "http://www.w3.org/2000/01/rdf-schema#"},
        "@id": publish.NS, "@type": "owl:Ontology",
        "rdfs:label": "etzhayyim power-dynamics vocabulary (tsumugi 紡ぎ)",
        "rdfs:comment": "Self-sovereign linked-data vocabulary. Dataset: /dataset/tsumugi-power.json. "
                        "License: " + publish.LICENSE + ". Publisher: " + publish.PUBLISHER_DID,
        "terms": {publish.NS + k: v for k, v in terms.items()},
    }, ensure_ascii=False, indent=2)


def _write_publish_md(pm: dict):
    a = pm["artifacts"]
    lines = [f"# tsumugi 紡ぎ — published power-graph (80-data/tsumugi-power)", "",
             f"> {pm['title']}  ·  ADR-{pm['adr']}  ·  published {pm['published_at']}  ·  "
             f"publisher `{pm['publisher']}`", "",
             "Self-sovereign linked-data power-graph, content-addressed to kotoba IPFS (CIDv1, raw,",
             "sha2-256). The CID is byte-identical to `ipfs add --cid-version=1 --raw-leaves` and",
             "verifiable with `20-actors/rasen/methods/cid.py` — no daemon required. The data lives",
             "on IPFS (host-independent); `https://etzhayyim.com/dataset/tsumugi-power.json` only",
             "advertises the CIDs + gateway links, and `/ns/power` resolves the vocabulary.", "",
             f"License: {pm['license']}", "",
             "## Artifacts (gzip, mtime=0 → deterministic CID)", "",
             "| artifact | file | bytes | CID |", "|---|---|---:|---|"]
    for k, v in a.items():
        lines.append(f"| {k} | `{v['file']}` | {v['bytes']} | `{v['cid']}` |")
    lines += ["", f"counts: {pm['counts']['nodes']} nodes · {pm['counts']['edges']} edges · "
              f"{pm['counts']['triples']} triples · N-Triples sha256 `{pm['contentHash_ntriples']}`",
              "", "## Pin + fetch + verify (trustless, no daemon trust)", "", "```bash",
              "# operator pins (the CID will match the manifest):",
              f"ipfs add --cid-version=1 --raw-leaves 80-data/tsumugi-power/{a['graph']['file']}",
              "# anyone fetches from a public gateway and re-content-addresses:",
              f"curl -sSL {pm['gateways'][0]}{a['graph']['cid']} -o g.edn.gz",
              "python3 20-actors/rasen/methods/cid.py g.edn.gz   # must equal the CID above",
              "gunzip -c g.edn.gz | head", "```", ""]
    (DATA_DIR / "PUBLISH.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv):
    if "--verify" in argv:
        pm = json.loads((DATA_DIR / "publish-manifest.json").read_text())
        ok = True
        for k, v in pm["artifacts"].items():
            got = cidv1_raw((DATA_DIR / v["file"]).read_bytes())
            match = got == v["cid"]; ok = ok and match
            print(f"  {'✓' if match else '✗'} {v['file']}: {got} {'== manifest' if match else '!= '+v['cid']}")
        return 0 if ok else 1
    pm = pin()
    a = pm["artifacts"]
    print(f"[tsumugi/pin] 80-data/tsumugi-power/ — {len(a)} artifacts content-addressed to IPFS CIDv1:")
    for k, v in a.items():
        print(f"    {v['file']:26} {v['bytes']:>7}B  {v['cid']}")
    print(f"  served: https://etzhayyim.com/ns/power · /dataset/tsumugi-power.json (next deploy)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
