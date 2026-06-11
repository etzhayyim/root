#!/usr/bin/env python3
"""tsumugi publish_ipfs.py tests — IPFS-pin persistence + etzhayyim.com serving (ADR-2606092000).

Verifies:
  - cidv1_raw matches the known rasen/cid.py vector (byte-identical to `ipfs add` algorithm)
  - gzip is deterministic (mtime=0) → reproducible CIDs
  - pin() content-addresses 3 artifacts, each a single-block CIDv1 (bafkrei…), < 256 KiB
  - --verify roundtrips (re-content-address == manifest CID)
  - the /ns/power vocabulary is valid JSON-LD; the /dataset descriptor is valid JSON w/ CIDs
  - the manifest carries license + publisher DID + provenance + N-Triples content-hash
"""
import sys, json, gzip, pathlib

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))
import publish_ipfs as P  # noqa: E402

PASS, FAIL = "\033[32mPASS\033[0m", "\033[31mFAIL\033[0m"
results = []

def check(name, cond):
    results.append(bool(cond))
    print(f"  [{PASS if cond else FAIL}] {name}")


def main():
    print("\n=== tsumugi publish_ipfs (pin + serve) tests ===")
    # known vector: the empty-ish / 'hello' raw block CID (matches `ipfs add --cid-version=1 --raw-leaves`)
    check("cidv1_raw matches ipfs-add vector for b'hello'",
          P.cidv1_raw(b"hello") == "bafkreibm6jg3ux5qumhcn2b3flc3tyu6dmlb4xa7u5bf44yegnrjhc4yeq")
    # gzip determinism
    g1, g2 = P._gz(b"x" * 1000), P._gz(b"x" * 1000)
    check("gzip mtime=0 is deterministic", g1 == g2)

    pm = P.pin()
    a = pm["artifacts"]
    check("3 artifacts content-addressed", len(a) == 3)
    check("every CID is a CIDv1 raw (bafkrei…)", all(v["cid"].startswith("bafkrei") for v in a.values()))
    check("every artifact is a single raw block (<256KiB)", all(v["bytes"] < 256*1024 for v in a.values()))

    # --verify roundtrip
    rc = P.main(["--verify"])
    check("--verify roundtrips (re-content-address == manifest)", rc == 0)

    # the gz actually decompresses back to the source (no corruption)
    edn = (ACTOR_DIR / "data" / "seed-scale-power.kotoba.edn").read_bytes()
    got = gzip.decompress((P.DATA_DIR / a["graph"]["file"]).read_bytes())
    check("graph.gz decompresses byte-identical to the seed", got == edn)

    # manifest descriptor
    check("manifest has license + publisher DID + N-Triples content-hash",
          "Charter" in pm["license"] and pm["publisher"] == P.publish.PUBLISHER_DID
          and pm["contentHash_ntriples"].startswith("sha256:"))
    check("manifest declares IPFS gateways", len(pm["gateways"]) >= 2)

    # (B) served descriptors resolve as valid linked data
    vocab = json.loads((P.APEX_PUBLIC / "ns" / "power").read_text())
    check("/ns/power is valid JSON-LD vocabulary", vocab["@context"]["@vocab"] == P.publish.NS
          and any("concentration" in k for k in vocab["terms"]))
    dsd = json.loads((P.APEX_PUBLIC / "dataset" / "tsumugi-power.json").read_text())
    check("/dataset/tsumugi-power.json carries CIDs + gateway fetch links",
          dsd["artifacts"]["graph"]["cid"].startswith("bafkrei")
          and dsd["fetch"]["graph"][0].endswith(dsd["artifacts"]["graph"]["cid"]))

    print(f"\n{sum(results)}/{len(results)} passed")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
