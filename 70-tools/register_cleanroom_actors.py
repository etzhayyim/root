#!/usr/bin/env python3
"""
Register the clean-room actor corpus (ADR 260607) as etzhayyim.com actors that
run BROWSER-LOCAL on IPFS + kotoba-WASM — the "one Worker, many WASM actors"
model (ADR-2606014500 / 2606014600 / 2606013800).

For every `20-actors/<platform>-compat`, this:

  1. Computes a content-addressed CIDv1 (raw, sha2-256, base32 → `bafkrei…`)
     over the actor's deterministic program bundle (schema + main.py). This is
     the same CID shape the apex Worker validates (`isRawCidV1`) and turns into
     an `EtzhayyimWasmComponent` service `ipfs://<cid>` with
     `x-runtime: kotoba-wasm`, `x-exec: browser-local|donated-mesh`. (The WASM
     build re-derives the same program CID at build time per ADR-2606036000;
     until then this is the program-source CID stand-in.)

  2. Emits a self-describing `20-actors/<platform>-compat/manifest.json`
     declaring FOUR capability surfaces, all running on the one WASM component:
       - api         : the generated CRUD REST surface
       - supplychain : a CycloneDX-style SBOM (deps from deps.toml) + purl
       - socialpost  : Datom-event → social-post surface (dry-run gated, G8)
       - mcp         : Model-Context-Protocol tool manifest (one tool per
                       CRUD op derived from the actor's entities)

  3. Writes a global registration seed for the `actors-v1` kotoba graph
     (`00-contracts/schemas/cleanroom-actors-seed.kotoba.edn`) — the same shape
     as `actor-profile-seed.kotoba.edn`, with `:actor/wasm-cid` set — plus a
     compact `cleanroom-actors.index.json` (actors.json-style index for the
     apex Worker / ameno actor panel).

No server keys, no per-actor server, no network credentials (Charter
no-server-key, ADR-2605231525). Idempotent.
"""

import os
import re
import json
import base64
import hashlib
import importlib.util

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS_DIR)
ACTORS_DIR = os.path.join(ROOT, "20-actors")

# Reuse the EXACT domain models + category map from the deepening generator.
_spec = importlib.util.spec_from_file_location(
    "deepen_actors", os.path.join(TOOLS_DIR, "deepen_actors.py"))
deepen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(deepen)

# Human-readable blurb per category key (for actor descriptions).
CATEGORY_BLURB = {
    "crm_sales": "CRM / sales-pipeline", "erp_finance": "ERP / finance ledger",
    "iaas_cloud": "cloud infrastructure (IaaS)", "office_productivity": "office / productivity suite",
    "devops_ci": "DevOps / CI-CD", "ehr_health": "EHR / clinical records",
    "ecommerce": "e-commerce storefront", "payments": "payments / money movement",
    "data_analytics": "data / analytics", "design_tools": "design / creative tooling",
    "ai_ml": "AI / ML inference", "martech": "marketing technology",
    "security_iam": "security / IAM", "hrtech": "HR technology",
    "devtools_apm": "developer tools / APM", "headless_ec_logistics": "headless commerce / logistics",
    "fintech_web3": "fintech / web3", "comms_social": "communications / social",
    "cx_survey": "customer experience / survey", "vertical_saas": "vertical SaaS",
    "lowcode_ipaas": "low-code / iPaaS", "rpa": "RPA / process automation",
    "modern_data_stack": "modern data stack", "iot_edge": "IoT / edge",
    "regtech_privacy": "RegTech / privacy", "aec_govtech": "AEC / GovTech",
    "media_video_cms": "media / video / CMS", "event_npo_creator": "events / NPO / creator",
    "core_banking_insurtech": "core banking / InsurTech", "devsecops_serverless": "DevSecOps / serverless",
    "enterprise_commerce_spend": "enterprise commerce / spend", "dpg_india_stack": "digital public infrastructure",
    "us_federal": "US federal / sovereign API", "uk_eu_egov": "UK / EU e-government",
    "japan_apac_egov": "Japan / APAC e-government", "intl_orgs_central_banks": "intl org / central bank data",
    "open_banking_finreg": "open banking / financial regulation", "customs_trade_logistics": "customs / trade / logistics",
    "public_health_env_ip": "public health / environment / IP", "public_safety_law": "public safety / law / justice",
    "transit_smart_cities": "transit / smart cities", "fin_market_hft": "financial market data / trading",
    "web3_rpc": "web3 / blockchain RPC", "telecom_satellite": "telecom / satellite",
    "healthcare_fhir_bio": "healthcare HL7-FHIR / bioinformatics", "energy_grid_utilities": "energy / smart grid",
    "travel_aviation_hospitality": "travel / aviation / hospitality", "os_kernel": "OS / kernel interface",
    "ai_ml_infra_chips": "AI/ML infrastructure / chips", "cyber_threat_intel": "cyber threat intelligence",
    "manufacturing_plm_robotics": "manufacturing / PLM / robotics", "isa_quantum": "hardware ISA / quantum",
    "internet_routing": "deep internet / core routing", "mobility_auto_ev": "mobility / auto / EV",
    "space_ocean_earth": "space / ocean / earth physics", "agritech_food": "AgriTech / food",
    "meta_knowledge_publishing": "meta-knowledge / scientific publishing", "deep_logistics_supply": "deep logistics / supply chain",
    "materials_bio_chemical": "materials / bio / chemical", "energy_commodities": "energy commodities",
    "physical_benchmarks_classifications": "physical benchmarks / classifications",
    "superapp": "regional super-app", "delivery_logistics": "delivery / local logistics",
    "ride_hailing": "ride-hailing / micro-mobility", "mainframe": "mainframe / legacy substrate",
    "scada": "industrial SCADA", "pharmacy_rx": "pharmacy benefit / Rx network",
    "real_estate": "real estate / MLS / PropTech", "gaming_backend": "gaming backend / metaverse",
    "legal_ediscovery": "legal / eDiscovery", "bci_neuro": "brain-computer interface / neurotech",
    "synbio": "synthetic biology / DNA", "xr_spatial": "spatial computing / XR",
    "drone_robotics": "drone swarm / aerial robotics", "agent_protocol": "AI agent protocol",
    "qkd": "quantum key distribution", "fusion_energy": "fusion / plasma energy",
}

DID_BASE = "did:web:etzhayyim.com:actor"


# --------------------------------------------------------------------------
# CIDv1 raw, sha2-256, base32 — byte-for-byte match to the apex Worker's
# cidV1Raw() (50-infra/etzhayyim-did-web/src/cid.ts): prefix 01 55 12 20.
# --------------------------------------------------------------------------

def cid_v1_raw(data: bytes) -> str:
    digest = hashlib.sha256(data).digest()
    cid = bytes([0x01, 0x55, 0x12, 0x20]) + digest
    b32 = base64.b32encode(cid).decode("ascii").lower().rstrip("=")
    return "b" + b32


RAW_CID_RE = re.compile(r"^bafkrei[a-z2-7]{52}$")


def program_bundle(adir: str, platform: str) -> bytes:
    """Deterministic program bundle: schema + main.py, length-prefixed."""
    parts = []
    for rel in (f"schema/{platform}.kotoba", "src/main.py", "deps.toml"):
        p = os.path.join(adir, rel)
        body = open(p, "rb").read() if os.path.exists(p) else b""
        parts.append(f"--- {rel} ({len(body)}) ---\n".encode("utf-8"))
        parts.append(body)
        parts.append(b"\n")
    return b"".join(parts)


def _snake(name):
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def _pluralize(name):
    return deepen._pluralize(name)


def mcp_tools(model):
    """One MCP tool per CRUD op per entity, derived from the domain model."""
    tools = []
    for ent, fields in model.items():
        plural = _pluralize(ent).lower()
        props = {f: {"type": _json_type(t)} for f, t in fields.items()}
        required = deepen._required_fields(fields)
        tools.append({
            "name": f"create_{_snake(ent)}",
            "description": f"Create a {ent}.",
            "inputSchema": {"type": "object", "properties": props, "required": required},
        })
        tools.append({
            "name": f"list_{_snake(_pluralize(ent))}",
            "description": f"List {_pluralize(ent)}.",
            "inputSchema": {"type": "object", "properties": {}},
        })
        tools.append({
            "name": f"get_{_snake(ent)}",
            "description": f"Get a {ent} by id.",
            "inputSchema": {"type": "object", "properties": {"id": {"type": "string"}}, "required": ["id"]},
        })
        tools.append({
            "name": f"update_{_snake(ent)}",
            "description": f"Update a {ent}.",
            "inputSchema": {"type": "object", "properties": {"id": {"type": "string"}, **props}, "required": ["id"]},
        })
        tools.append({
            "name": f"delete_{_snake(ent)}",
            "description": f"Delete a {ent}.",
            "inputSchema": {"type": "object", "properties": {"id": {"type": "string"}}, "required": ["id"]},
        })
    return tools


def _json_type(t):
    return {"string": "string", "integer": "integer", "float": "number",
            "boolean": "boolean", "datetime": "string"}.get(t, "string")


def rest_routes(model):
    routes = []
    for ent in model:
        plural = _pluralize(ent).lower()
        routes.append({"method": "POST", "path": f"/v1/{plural}", "op": f"create {ent}"})
        routes.append({"method": "GET", "path": f"/v1/{plural}", "op": f"list {ent}"})
        routes.append({"method": "GET", "path": f"/v1/{plural}/{{id}}", "op": f"get {ent}"})
        routes.append({"method": "PATCH", "path": f"/v1/{plural}/{{id}}", "op": f"update {ent}"})
        routes.append({"method": "DELETE", "path": f"/v1/{plural}/{{id}}", "op": f"delete {ent}"})
    return routes


def sbom(platform, adir):
    """Minimal CycloneDX 1.5 SBOM from deps.toml (supplychain capability)."""
    deps = []
    dpath = os.path.join(adir, "deps.toml")
    if os.path.exists(dpath):
        in_deps = False
        for line in open(dpath):
            s = line.strip()
            if s.startswith("[dependencies]"):
                in_deps = True
                continue
            if s.startswith("[") and in_deps:
                break
            if in_deps and "=" in s:
                name = s.split("=", 1)[0].strip()
                deps.append(name)
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "metadata": {"component": {"type": "application", "name": f"{platform}-compat",
                                   "purl": f"pkg:etzhayyim/{platform}-compat"}},
        "components": [
            {"type": "library", "name": d, "scope": "required",
             "purl": f"pkg:etzhayyim/{d}"} for d in deps
        ],
    }


def build():
    cats = deepen.parse_platform_categories()
    actor_dirs = sorted(d for d in os.listdir(ACTORS_DIR) if d.endswith("-compat"))
    seed_entries = []
    index = []
    bad_cid = []
    # CIDs of actually-built WASM components (gen_rust_actor.py), keyed by handle.
    global BUILT_CIDS
    BUILT_CIDS = {}
    _built = os.path.join(ROOT, "00-contracts", "schemas", "cleanroom-built-actors.json")
    if os.path.exists(_built):
        for a in json.load(open(_built)).get("actors", []):
            if a.get("wasmCid"):
                BUILT_CIDS[a["handle"]] = a["wasmCid"]
    for actor in actor_dirs:
        platform = actor[:-len("-compat")].strip()
        adir = os.path.join(ACTORS_DIR, actor)
        pkey = platform
        model = (deepen.PLATFORM_OVERRIDES.get(pkey)
                 or deepen.CATEGORY_MODELS.get(cats.get(pkey))
                 or deepen.GENERIC_MODEL)
        catkey = cats.get(pkey, "generic")
        blurb = CATEGORY_BLURB.get(catkey, "clean-room API")
        ns = re.sub(r"[^a-z0-9_]", "_", platform.lower()) or "actor"

        # DID-safe handle: strip the sibling " coherence" leading-space typo and
        # any char outside [a-z0-9_-] so the did:web path component is valid.
        handle = re.sub(r"[^a-z0-9_-]", "", actor.strip().lower()) or "actor"

        # Prefer the CID of an ACTUALLY-BUILT WASM component (gen_rust_actor.py /
        # cleanroom-built-actors.json) over the source-bundle stand-in.
        if handle in BUILT_CIDS:
            cid = BUILT_CIDS[handle]
            wasm_provenance = "built-rust-raw"
        else:
            cid = cid_v1_raw(program_bundle(adir, platform))
            wasm_provenance = "source-bundle"
        if not RAW_CID_RE.match(cid):
            bad_cid.append((actor, cid))
        did = f"{DID_BASE}:{handle}"
        entities = list(model.keys())
        routes = rest_routes(model)
        tools = mcp_tools(model)

        # Tier detection: an actor is L4 once promote_l4.py has given it the
        # production surface (pagination + filtering + strict validation) and a
        # contract test; otherwise L3 (the deepened CRUD baseline).
        main_src = ""
        mp = os.path.join(adir, "src", "main.py")
        if os.path.exists(mp):
            main_src = open(mp, encoding="utf-8").read()
        tdir = os.path.join(adir, "tests")
        has_tests = os.path.isdir(tdir) and any(
            f.startswith("test_") and f.endswith(".py") for f in os.listdir(tdir))
        api_features = {
            "pagination": "_paginate(" in main_src,
            "filtering": "_apply_filters(" in main_src,
            "relationExpansion": "_expand(" in main_src,
            "strictValidation": "_reject_unknown(" in main_src,
            "contractTest": has_tests,
        }
        tier = "L4" if (all(api_features.values())) else "L3"

        # ---- per-actor manifest.json (4 capabilities on one WASM component) --
        manifest = {
            "schemaVersion": "1.0",
            "handle": handle,
            "did": did,
            "kind": "compat",
            "title": f"{platform} clean-room actor",
            "description": f"Clean-room, API-compatible {blurb} actor ({platform}); "
                           f"runs browser-local on IPFS + kotoba-WASM.",
            "wasmCid": cid,
            "wasmProvenance": wasm_provenance,
            "runtime": "kotoba-wasm",
            "exec": "browser-local|donated-mesh",
            "ipfs": f"ipfs://{cid}",
            "schema": f"schema/{platform}.kotoba",
            "tier": tier,
            "entities": entities,
            "adr": ["260607", "2606014500", "2606013800", "2606036000"],
            "capabilities": {
                "api": {
                    "type": "rest",
                    "runtime": "kotoba-wasm",
                    "endpointCount": len(routes),
                    "routes": routes,
                    "features": api_features,
                    "health": "/healthz",
                },
                "supplychain": {
                    "type": "cyclonedx-sbom",
                    "runtime": "kotoba-wasm",
                    "sbom": "manifest:supplychain.sbom",
                    "sbomData": sbom(platform, adir),
                    "adr": ["2606036000"],
                },
                "socialpost": {
                    "type": "datom-event-feed",
                    "runtime": "kotoba-wasm",
                    "lexicon": "app.bsky.feed.post",
                    "source": f"{ns}.* Datom events",
                    "mode": "dry-run",          # outward posting G8-gated
                    "gate": "G8",
                },
                "mcp": {
                    "type": "model-context-protocol",
                    "runtime": "kotoba-wasm",
                    "transport": "ipfs+kotoba-wasm",
                    "toolCount": len(tools),
                    "tools": tools,
                },
            },
        }
        with open(os.path.join(adir, "manifest.json"), "w") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
            f.write("\n")

        # ---- actors-v1 seed entry (EDN) -------------------------------------
        services = [
            {"id": f"{did}#api", "type": "EtzhayyimRestApi",
             "serviceEndpoint": f"ipfs://{cid}", "x-runtime": "kotoba-wasm"},
            {"id": f"{did}#supplychain", "type": "EtzhayyimSbom",
             "serviceEndpoint": f"ipfs://{cid}", "x-runtime": "kotoba-wasm"},
            {"id": f"{did}#socialpost", "type": "EtzhayyimSocialPost",
             "serviceEndpoint": f"ipfs://{cid}", "x-runtime": "kotoba-wasm", "x-gate": "G8"},
            {"id": f"{did}#mcp", "type": "EtzhayyimMcpServer",
             "serviceEndpoint": f"ipfs://{cid}", "x-runtime": "kotoba-wasm"},
        ]
        seed_entries.append({
            "handle": handle, "did": did, "platform": platform,
            "description": manifest["description"], "ns": ns,
            "cid": cid, "services": services,
        })
        index.append({
            "handle": handle, "did": did, "wasmCid": cid, "kind": "compat",
            "wasmProvenance": wasm_provenance,
            "tier": tier, "title": manifest["title"], "category": catkey,
            "capabilities": ["api", "supplychain", "socialpost", "mcp"],
            "exec": "browser-local|donated-mesh", "runtime": "kotoba-wasm",
        })

    _write_seed_edn(seed_entries)
    _write_index_json(index)
    print(f"Registered {len(seed_entries)} clean-room actors.")
    print(f"  manifest.json per actor + seed EDN + index JSON written.")
    if bad_cid:
        print(f"  WARNING: {len(bad_cid)} malformed CIDs (first: {bad_cid[0]})")
    else:
        print(f"  All {len(seed_entries)} wasm CIDs match bafkrei raw-CIDv1 shape.")
    return seed_entries


def _edn_services(services):
    parts = []
    for s in services:
        kvs = " ".join(f'"{k}" "{v}"' for k, v in s.items())
        parts.append("{" + kvs + "}")
    return "[" + " ".join(parts) + "]"


def _write_seed_edn(entries):
    out = [
        ";; cleanroom-actors-seed.kotoba.edn",
        ";;",
        ";; Registration Datoms for the clean-room actor corpus (ADR 260607) into",
        ";; the `actors-v1` kotoba graph (schema: actor-profile.kotoba.edn).",
        ";; Generated by 70-tools/register_cleanroom_actors.py — do not hand-edit.",
        ";;",
        ";; Every actor carries :actor/wasm-cid (content-addressed CIDv1 raw,",
        ";; sha2-256) so the apex Worker emits an EtzhayyimWasmComponent service",
        ";; (ipfs://<cid>) and the actor runs BROWSER-LOCAL on kotoba-WASM — no",
        ";; per-actor server (ADR-2606014500 / 2606013800). Each exposes four",
        ";; capability services: api / supplychain / socialpost / mcp.",
        ";;",
        ";; :actor/vm is [] for every actor (no server-minted key; did:web trust",
        ";; root = TLS, ADR-2605231525).",
        "",
        '{:graph {:name "actors-v1" :visibility :public}',
        "",
        " :seed",
        " [",
    ]
    for e in entries:
        out.append(f'  {{:actor/handle "{e["handle"]}"')
        out.append(f'   :actor/did "{e["did"]}"')
        out.append(f"   :actor/kind :compat")
        out.append(f"   :actor/status :landed")
        out.append(f"   :actor/performer-type :service")
        out.append(f"   :actor/ui-type :iframe")
        out.append(f'   :actor/description "{_edn_str(e["description"])}"')
        out.append(f'   :actor/primary-schema "{e["ns"]}.kotoba"')
        out.append(f'   :actor/wasm-cid "{e["cid"]}"')
        out.append(f'   :actor/adr ["260607" "2606014500" "2606013800"]')
        out.append(f'   :actor/created-at "2026-06-07"')
        out.append(f"   :actor/vm []")
        out.append(f'   :actor/service {_edn_services(e["services"])}}}')
    out.append(" ]}")
    path = os.path.join(ROOT, "00-contracts", "schemas", "cleanroom-actors-seed.kotoba.edn")
    with open(path, "w") as f:
        f.write("\n".join(out) + "\n")


def _edn_str(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')


def _write_index_json(index):
    path = os.path.join(ROOT, "00-contracts", "schemas", "cleanroom-actors.index.json")
    tier_counts = {}
    for a in index:
        tier_counts[a.get("tier", "L3")] = tier_counts.get(a.get("tier", "L3"), 0) + 1
    doc = {
        "schemaVersion": "1.0",
        "graph": "actors-v1",
        "adr": ["260607", "2606014500", "2606013800"],
        "runtime": "kotoba-wasm",
        "exec": "browser-local|donated-mesh",
        "count": len(index),
        "tierCounts": tier_counts,
        "actors": index,
    }
    with open(path, "w") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)
        f.write("\n")


if __name__ == "__main__":
    build()
