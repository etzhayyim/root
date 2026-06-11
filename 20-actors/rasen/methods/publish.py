#!/usr/bin/env python3
"""rasen 螺旋 — PUBLISH the ingested public-genetics graph to public IPFS (ADR-2606101000).

OUTWARD-GATED CELL (G7, operator/mesh-side). Takes the locally ingested artifacts
(`out/ingested-genome-*.kotoba.edn`, produced by `methods/ingest.py`) and:

  1. pins them to the local IPFS node (`ipfs add --cid-version=1 --raw-leaves`) and asserts
     the daemon's CID equals the pure-stdlib `cid.py` CID (content-address trust anchor);
  2. publishes the graph CID under the node's IPNS `self` key → a stable `/ipns/<id>` name
     that always resolves to the latest published graph;
  3. snapshots the published artifacts into the monorepo data layer `80-data/genome/` (the
     durable, git-tracked record — small bounded EDN, NOT git-lfs, G8) with a PUBLISH.md +
     publish-manifest.json carrying CIDs, IPNS name, gateway URLs and fetch+verify steps.

PUBLIC reference data only (G1) — the published artifacts contain no individual genotypes;
publishing them is safe by construction. Pinata / other public pinning services are an
operator add-on (API-key, out of scope here); IPNS + a trustless gateway already make the
content publicly fetchable + verifiable.

Usage:
    python3 publish.py [--graph out/ingested-genome-graph.kotoba.edn] [--no-ipns] [--offline-ipns]
"""
from __future__ import annotations
import sys, json, shutil, subprocess, pathlib, datetime
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import cid as cidlib  # noqa: E402

GATEWAYS = ["https://ipfs.io/ipfs/", "https://dweb.link/ipfs/", "https://cloudflare-ipfs.com/ipfs/"]


def _ipfs(*args, timeout=60):
    return subprocess.run(["ipfs", *args], capture_output=True, text=True, timeout=timeout)


def _add_pin(path: pathlib.Path):
    """ipfs add (pin) → returns (daemon_cid, local_cid, matches)."""
    local_cid = cidlib.cidv1_raw(path.read_bytes())
    out = _ipfs("add", "-Q", "--cid-version=1", "--raw-leaves", "--pin=true", str(path))
    daemon_cid = out.stdout.strip() if out.returncode == 0 else None
    return daemon_cid, local_cid, (daemon_cid == local_cid)


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    graph = here / "out" / "ingested-genome-graph.kotoba.edn"
    if "--graph" in argv:
        graph = pathlib.Path(argv[argv.index("--graph") + 1])
    datoms = graph.with_name("ingested-genome-datoms.kotoba.edn")
    prov_in = here / "out" / "ingest-provenance.json"
    do_ipns = "--no-ipns" not in argv
    offline_ipns = "--offline-ipns" in argv

    if not graph.exists():
        print(f"publish: {graph} not found — run methods/ingest.py first", file=sys.stderr)
        return 1
    if not shutil.which("ipfs"):
        print("publish: ipfs CLI not found (required for pin + IPNS)", file=sys.stderr)
        return 1

    manifest = {
        "actor": "rasen", "adr": "2606101000",
        "published_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "scope": "PUBLIC reference genetics only — no individual genotypes (G1)",
        "artifacts": {}, "ipns": None, "gateways": GATEWAYS,
    }

    # 1. pin graph + datoms, assert CID parity
    for label, p in [("graph", graph), ("datoms", datoms)]:
        if not p.exists():
            continue
        dcid, lcid, ok = _add_pin(p)
        manifest["artifacts"][label] = {
            "file": p.name, "bytes": p.stat().st_size, "cid": lcid,
            "daemon_cid": dcid, "cid_matches": ok,
        }
        flag = "✓" if ok else "✗ MISMATCH"
        print(f"  pin {label}: {lcid} {flag}")
        if not ok:
            print(f"publish: CID mismatch on {label} (daemon={dcid})", file=sys.stderr)
            return 2

    graph_cid = manifest["artifacts"]["graph"]["cid"]

    # 2. IPNS publish (graph CID under the node's self key)
    if do_ipns:
        ipns_args = ["name", "publish", "--key=self"]
        if offline_ipns:
            ipns_args.append("--allow-offline")
        out = _ipfs(*ipns_args, f"/ipfs/{graph_cid}", timeout=150)
        if out.returncode == 0:
            # "Published to <name>: /ipfs/<cid>"
            line = out.stdout.strip()
            name = line.split("Published to", 1)[-1].split(":", 1)[0].strip() if "Published to" in line else None
            manifest["ipns"] = {"name": name, "path": f"/ipns/{name}" if name else None, "points_to": graph_cid}
            print(f"  IPNS: /ipns/{name} → {graph_cid}")
        else:
            manifest["ipns"] = {"error": out.stderr.strip()[:200]}
            print(f"  IPNS publish failed (non-fatal): {out.stderr.strip()[:120]}")

    # 3. snapshot into the durable data layer (80-data/genome/)
    data_dir = here.parents[1] / "80-data" / "genome"  # repo-root/80-data/genome
    data_dir.mkdir(parents=True, exist_ok=True)
    def _copy_nl(src: pathlib.Path, dst: pathlib.Path):
        text = src.read_text(encoding="utf-8")
        if not text.endswith("\n"):
            text += "\n"          # POSIX final-newline (repo end-of-file hook)
        dst.write_text(text, encoding="utf-8")

    for _, p in [("graph", graph), ("datoms", datoms)]:
        if p.exists():
            _copy_nl(p, data_dir / p.name.replace("ingested-", ""))
    if prov_in.exists():
        _copy_nl(prov_in, data_dir / "ingest-provenance.json")
    (data_dir / "publish-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (data_dir / "PUBLISH.md").write_text(_publish_md(manifest), encoding="utf-8")

    print(f"publish: snapshot → {data_dir}  (graph CID {graph_cid})")
    return 0


def _publish_md(m: dict) -> str:
    g = m["artifacts"].get("graph", {})
    d = m["artifacts"].get("datoms", {})
    ipns = m.get("ipns") or {}
    L = [
        "# rasen 螺旋 — published public-genetics graph (80-data/genome)",
        "",
        f"> {m['scope']}  ·  ADR-{m['adr']}  ·  published {m['published_at']}",
        "",
        "PUBLIC reference genetics (genes / variants / phenotypes / population-AGGREGATE allele",
        "frequencies / GO + Reactome pathways), content-addressed to kotoba IPFS (CIDv1, raw,",
        "sha2-256). The CID is byte-identical to `ipfs add --cid-version=1 --raw-leaves` and",
        "verifiable with `20-actors/rasen/methods/cid.py` — no daemon required.",
        "",
        "## Artifacts",
        "",
        "| artifact | file | bytes | CID |",
        "|---|---|---:|---|",
        f"| graph (EDN) | `{g.get('file','—')}` | {g.get('bytes','—')} | `{g.get('cid','—')}` |",
        f"| datoms (EAVT) | `{d.get('file','—')}` | {d.get('bytes','—')} | `{d.get('cid','—')}` |",
        "",
        "## IPNS",
        "",
        (f"Stable name (always resolves to the latest published graph):\n\n    {ipns.get('path')}\n"
         if ipns.get("path") else "_IPNS not published this run._"),
        "",
        "## Fetch + verify (trustless, no daemon trust)",
        "",
        "```bash",
        f"# fetch from any public gateway and re-content-address — must equal the CID above",
        f"curl -sSL https://ipfs.io/ipfs/{g.get('cid','<cid>')} -o graph.edn",
        "python3 20-actors/rasen/methods/cid.py graph.edn   # prints the CID; compare",
        "```",
        "",
        "Gateways: " + ", ".join(m.get("gateways", [])),
        "",
        "---",
        "_Generated by `20-actors/rasen/methods/publish.py` (G7, operator/mesh-side). "
        "Large FASTA/VCF would go via DataLad→IPFS; this bounded EDN snapshot is git-tracked "
        "directly (no git-lfs, G8)._",
    ]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    sys.exit(main(sys.argv))
