#!/usr/bin/env python3
"""wasm-sbom — attach a CycloneDX SBOM to a kotoba-deployed WASM actor.

A WASM actor deployed to a kotoba node (`invoke.run` / `block.put`) is
content-addressed by its **kotoba program CID** = `KotobaCid::from_bytes(wasm)`
(CIDv1 dag-cbor sha2-256, see 40-engine/kotoba/crates/kotoba-core/src/cid.rs).
Until now that CID told you *what* the binary is and *who* deployed it, but not
*what it is made of*. This tool closes that gap, per ADR-2606036000:

  1. it recomputes the exact kotoba program CID from the built `.wasm` (so the
     SBOM is keyed by the same identity the server stores), and
  2. emits, bound to that CID:
       <stem>.wasm.cdx.json         — a portable CycloneDX 1.5 SBOM (ships next
                                       to the binary / can be pinned to IPFS)
       <stem>.wasm.sbom.ingest.json — a kotoba `kg.ingest_batch` body that binds
                                       the image entity + one component entity
                                       per dependency into the EAVT log, with a
                                       `wasm/componentOf` relation edge.

The component entities carry `cdx/purl`, so the EXISTING purl↔CVE matcher
(`70-tools/scripts/sbom/purl_vuln_match.py`, ADR-2605312330) matches a deployed
wasm's dependencies with zero changes — the wasm supply chain joins the same
VulnMatch surface as the giemon hardware SBOMs.

Two component sources (substrate-wide — componentize-py *and* Rust actors):
  --requirements <requirements.txt>  Python / componentize-py actors (sumitsubo,
                                     okaimono, …). Optional --freeze <pip-freeze>
                                     supplies resolved (locked) versions.
  --from-cdx <existing.cdx.json>     Rust actors built with `cargo cyclonedx`
                                     (tsumugi, kanae, …): re-key that SBOM by the
                                     kotoba program CID and emit the ingest body.

stdlib-only (no third-party deps) so it runs anywhere the edge does.

Usage:
  python3 wasm_sbom_gen.py --wasm py/agent.wasm --actor sumitsubo \\
      --world kotoba-actor --requirements py/requirements.txt \\
      [--freeze py/requirements.lock] [--built-by componentize-py@0.23.0] \\
      [--sourcing representative] [--adr 2606036000] [--out-dir .]

  python3 wasm_sbom_gen.py --wasm target/wasm32-wasi/release/tsumugi.wasm \\
      --actor tsumugi --from-cdx tsumugi.cdx.json
"""
import argparse
import base64
import hashlib
import json
import re
import sys
from pathlib import Path

SPEC_VERSION = "1.5"
TOOL_NAME = "etzhayyim-wasm-sbom"
TOOL_VERSION = "0.1.0"


# ── kotoba program CID (must match KotobaCid::from_bytes → to_multibase) ──────
# CIDv1 dag-cbor sha2-256, base32lower ('b' multibase prefix). See
# 40-engine/kotoba/crates/kotoba-core/src/cid.rs.
def kotoba_program_cid(wasm: bytes) -> tuple[str, str]:
    """Return (multibase_cid, sha256_hex) for a wasm payload."""
    digest = hashlib.sha256(wasm).digest()
    cid_bytes = bytes([0x01, 0x71, 0x12, 0x20]) + digest  # ver, dag-cbor, sha2-256, len32
    b32 = base64.b32encode(cid_bytes).decode("ascii").rstrip("=").lower()
    return "b" + b32, digest.hex()


# ── deterministic urn:uuid serialNumber derived from the program CID ──────────
def _det_serial(cid: str) -> str:
    h = hashlib.sha256(("urn:" + cid).encode()).hexdigest()
    return f"urn:uuid:{h[0:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"


# ── requirements / freeze parsing → pypi components ───────────────────────────
_REQ_RE = re.compile(
    r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)\s*"            # name
    r"(?:\[[^\]]*\])?\s*"                              # optional extras
    r"(==|>=|<=|~=|!=|>|<|===)?\s*"                    # comparator
    r"([A-Za-z0-9][A-Za-z0-9._*+-]*)?"                 # version
)


def _norm_pypi(name: str) -> str:
    # PEP 503 normalization for the purl name component.
    return re.sub(r"[-_.]+", "-", name).lower()


def parse_requirements(text: str, freeze: dict[str, str]) -> list[dict]:
    comps = []
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].split(";", 1)[0].strip()  # drop comment + env-marker
        if not line or line.startswith("-"):  # skip blanks and pip flags (-r, -e, --hash)
            continue
        m = _REQ_RE.match(line)
        if not m:
            continue
        name, cmp_, ver = m.group(1), m.group(2), m.group(3)
        norm = _norm_pypi(name)
        locked = freeze.get(norm)
        if locked:
            version, vsrc = locked, "lock"
        elif cmp_ == "==" and ver:
            version, vsrc = ver, "pin"
        elif ver:
            version, vsrc = ver, "constraint"  # honest: lower bound, not resolved
        else:
            version, vsrc = "", "unspecified"
        comp = {
            "type": "library",
            "bom-ref": f"pkg:pypi/{norm}@{version}" if version else f"pkg:pypi/{norm}",
            "name": name,
            "scope": "required",
            "properties": [{"name": "wasm:versionSource", "value": vsrc}],
        }
        if version:
            comp["version"] = version
            comp["purl"] = f"pkg:pypi/{norm}@{version}"
        else:
            comp["purl"] = f"pkg:pypi/{norm}"
        comps.append(comp)
    return comps


def parse_freeze(text: str) -> dict[str, str]:
    out = {}
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or "==" not in line:
            continue
        name, ver = line.split("==", 1)
        out[_norm_pypi(name.strip())] = ver.strip().split(";")[0].strip()
    return out


# ── CycloneDX assembly ────────────────────────────────────────────────────────
def build_cyclonedx(cid: str, sha_hex: str, byte_size: int, args, components: list[dict]) -> dict:
    serial = _det_serial(cid)
    image_props = [
        {"name": "kotoba:programCid", "value": cid},
        {"name": "kotoba:programType", "value": args.program_type},
        {"name": "wasm:sha256", "value": sha_hex},
        {"name": "wasm:byteSize", "value": str(byte_size)},
        {"name": "wasm:sourcing", "value": args.sourcing},
        {"name": "wasm:adr", "value": args.adr},
    ]
    if args.world:
        image_props.append({"name": "wasm:world", "value": args.world})
    if args.built_by:
        image_props.append({"name": "wasm:builtBy", "value": args.built_by})
    return {
        "bomFormat": "CycloneDX",
        "specVersion": SPEC_VERSION,
        "serialNumber": serial,
        "version": 1,
        "metadata": {
            # Note: timestamp intentionally omitted — the SBOM is reproducible /
            # content-addressed by the program CID (no wall-clock nondeterminism).
            "tools": [{"vendor": "etzhayyim", "name": TOOL_NAME, "version": TOOL_VERSION}],
            "component": {
                "type": "application",
                "bom-ref": cid,
                "name": f"{args.actor}-agent.wasm",
                "version": f"sha256:{sha_hex[:16]}",
                "purl": f"pkg:generic/{args.actor}-agent.wasm@sha256:{sha_hex}",
                "hashes": [{"alg": "SHA-256", "content": sha_hex}],
                "properties": image_props,
            },
        },
        "components": components,
    }


# ── kotoba kg.ingest_batch body (bound to the program CID) ────────────────────
def build_ingest(cid: str, sha_hex: str, byte_size: int, args, components: list[dict]) -> dict:
    serial = _det_serial(cid)
    image = {
        "id": cid,
        "type": "WasmActorImage",
        "labelEn": f"{args.actor} agent.wasm",
        "claims": [
            {"pred": "wasm/programCid", "value": cid},
            {"pred": "wasm/actor", "value": args.actor},
            {"pred": "wasm/programType", "value": args.program_type},
            {"pred": "wasm/sha256", "value": sha_hex},
            {"pred": "wasm/byteSize", "value": str(byte_size)},
            {"pred": "wasm/sbomSerial", "value": serial},
            {"pred": "wasm/sbomFormat", "value": f"CycloneDX-{SPEC_VERSION}"},
            {"pred": "wasm/sourcing", "value": args.sourcing},
            {"pred": "wasm/adr", "value": args.adr},
        ],
    }
    if args.world:
        image["claims"].append({"pred": "wasm/world", "value": args.world})
    if args.built_by:
        image["claims"].append({"pred": "wasm/builtBy", "value": args.built_by})

    entities = [image]
    for c in components:
        cid_ref = c.get("purl") or c.get("bom-ref") or c.get("name")
        claims = [{"pred": "cdx/sbom", "value": f"{args.actor}-agent.wasm"}]
        if c.get("type"):
            claims.append({"pred": "cdx/type", "value": c["type"]})
        if c.get("version"):
            claims.append({"pred": "cdx/version", "value": str(c["version"])})
        if c.get("purl"):
            claims.append({"pred": "cdx/purl", "value": c["purl"]})  # VulnMatch join key
        if c.get("scope"):
            claims.append({"pred": "cdx/scope", "value": c["scope"]})
        if (c.get("supplier") or {}).get("name"):
            claims.append({"pred": "cdx/supplier", "value": c["supplier"]["name"]})
        if c.get("publisher"):
            claims.append({"pred": "cdx/publisher", "value": c["publisher"]})
        for p in c.get("properties", []) or []:
            claims.append({"pred": f"cdx/prop/{p['name']}", "value": str(p.get("value", ""))})
        entities.append({
            "id": cid_ref,
            "type": "SbomComponent",
            "labelEn": c.get("name", cid_ref),
            "claims": claims,
            # binding edge: this component is part of the deployed image
            "relations": [{"pred": "wasm/componentOf", "dstId": cid}],
        })
    return {"entities": entities}


def components_from_cdx(doc: dict) -> list[dict]:
    assert doc.get("bomFormat") == "CycloneDX", "--from-cdx: not a CycloneDX document"
    return doc.get("components", []) or []


def main() -> int:
    ap = argparse.ArgumentParser(description="attach a CycloneDX SBOM to a kotoba wasm actor")
    ap.add_argument("--wasm", required=True, help="path to the built .wasm")
    ap.add_argument("--actor", required=True, help="actor id, e.g. sumitsubo")
    ap.add_argument("--world", default="", help="componentize-py world (e.g. kotoba-actor)")
    ap.add_argument("--program-type", default="wasm-node",
                    choices=["wasm-node", "wasm-udf", "datalog"])
    ap.add_argument("--requirements", help="requirements.txt (python actors)")
    ap.add_argument("--freeze", help="pip-freeze / lock with resolved == versions")
    ap.add_argument("--from-cdx", help="existing CycloneDX (rust cargo-cyclonedx actors)")
    ap.add_argument("--built-by", default="", help="toolchain, e.g. componentize-py@0.23.0")
    ap.add_argument("--sourcing", default="representative",
                    choices=["representative", "authoritative"])
    ap.add_argument("--adr", default="2606036000")
    ap.add_argument("--out-dir", default="")
    args = ap.parse_args()

    wasm_path = Path(args.wasm)
    if not wasm_path.is_file():
        sys.exit(f"!! wasm not found: {wasm_path}")
    wasm = wasm_path.read_bytes()
    cid, sha_hex = kotoba_program_cid(wasm)

    if args.from_cdx:
        components = components_from_cdx(json.loads(Path(args.from_cdx).read_text("utf-8")))
    elif args.requirements:
        freeze = parse_freeze(Path(args.freeze).read_text("utf-8")) if args.freeze else {}
        components = parse_requirements(Path(args.requirements).read_text("utf-8"), freeze)
    else:
        components = []  # honest: an SBOM with no declared deps is still a valid, signed manifest

    cdx = build_cyclonedx(cid, sha_hex, len(wasm), args, components)
    ing = build_ingest(cid, sha_hex, len(wasm), args, components)

    out_dir = Path(args.out_dir) if args.out_dir else wasm_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = wasm_path.stem  # agent.wasm -> agent
    cdx_path = out_dir / f"{stem}.wasm.cdx.json"
    ing_path = out_dir / f"{stem}.wasm.sbom.ingest.json"
    cdx_path.write_text(json.dumps(cdx, indent=2, ensure_ascii=False) + "\n", "utf-8")
    ing_path.write_text(json.dumps(ing, ensure_ascii=False) + "\n", "utf-8")

    print(f"wasm-sbom: {args.actor}  programCid={cid}")
    print(f"           sha256={sha_hex}  bytes={len(wasm)}  components={len(components)}")
    print(f"wrote {cdx_path}")
    print(f"wrote {ing_path} ({len(ing['entities'])} entities)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
