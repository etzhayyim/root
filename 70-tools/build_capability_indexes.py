#!/usr/bin/env python3
"""
Build corpus-level capability indexes for the clean-room actor corpus so the
four per-actor surfaces (api / supplychain / socialpost / mcp) are DISCOVERABLE
and CONSUMABLE corpus-wide — the "稼働するように" (operational) step.

Reads the per-actor manifests (written by register_cleanroom_actors.py) + the
domain models (deepen_actors.py) and emits, under 00-contracts/schemas/:

  cleanroom-mcp-index.json          one MCP server per actor (ipfs+kotoba-wasm
                                    endpoint + tool count); the MCP discovery doc
  cleanroom-openapi-index.json      one REST API per actor (basePath + endpoint
                                    count + ipfs + per-actor openapi ref)
  cleanroom-supplychain-index.json  aggregate CycloneDX SBOM: component → actors
  cleanroom-socialpost-index.json   one Datom-event feed per actor (lexicon/gate)

and, for the L4 production cohort only, a full per-actor OpenAPI 3.1 spec:
  20-actors/<platform>-compat/openapi.json

Idempotent. No network, no keys.
"""

import os
import re
import json
import importlib.util

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS_DIR)
ACTORS_DIR = os.path.join(ROOT, "20-actors")
SCHEMAS_DIR = os.path.join(ROOT, "00-contracts", "schemas")

_spec = importlib.util.spec_from_file_location(
    "deepen_actors", os.path.join(TOOLS_DIR, "deepen_actors.py"))
deepen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(deepen)

OPENAPI_TYPE = {"string": "string", "integer": "integer", "float": "number",
                "boolean": "boolean", "datetime": "string"}


def _pluralize(n):
    return deepen._pluralize(n)


def openapi_spec(platform, model, manifest, enums=None):
    """OpenAPI 3.1 from the domain model (L4 cohort); L5 verified enums inlined."""
    enums = enums or {}            # {EntityName: {field: [allowed values]}}
    schemas = {}
    paths = {}
    for ent, fields in model.items():
        ent_enums = {f: v for f, v in (enums.get(ent) or {}).items() if f in fields}
        props = {"id": {"type": "string"}}
        for f, t in fields.items():
            props[f] = {"type": OPENAPI_TYPE.get(t, "string")}
            if t == "datetime":
                props[f]["format"] = "date-time"
            if f in ent_enums:
                props[f]["enum"] = list(ent_enums[f])
        props["createdAt"] = {"type": "string", "format": "date-time"}
        props["updatedAt"] = {"type": "string", "format": "date-time"}
        schemas[ent] = {"type": "object", "properties": props}
        required = deepen._required_fields(fields)
        create_props = {}
        for f, t in fields.items():
            create_props[f] = {"type": OPENAPI_TYPE.get(t, "string")}
            if f in ent_enums:
                create_props[f]["enum"] = list(ent_enums[f])
        schemas[f"{ent}Create"] = {"type": "object", "properties": create_props,
                                   "required": required}
        plural = _pluralize(ent).lower()
        base = f"/v1/{plural}"
        ref = f"#/components/schemas/{ent}"
        paths[base] = {
            "get": {
                "summary": f"List {_pluralize(ent)}",
                "parameters": [
                    {"name": "limit", "in": "query", "schema": {"type": "integer", "default": 20, "maximum": 100}},
                    {"name": "starting_after", "in": "query", "schema": {"type": "string"}},
                    {"name": "expand", "in": "query", "schema": {"type": "string"}},
                ],
                "responses": {"200": {"description": "list",
                    "content": {"application/json": {"schema": {"type": "object", "properties": {
                        "object": {"type": "string"}, "data": {"type": "array", "items": {"$ref": ref}},
                        "has_more": {"type": "boolean"}, "count": {"type": "integer"},
                        "total": {"type": "integer"}}}}}}},
            },
            "post": {
                "summary": f"Create a {ent}",
                "requestBody": {"required": True, "content": {"application/json": {
                    "schema": {"$ref": f"#/components/schemas/{ent}Create"}}}},
                "responses": {"201": {"description": "created",
                    "content": {"application/json": {"schema": {"$ref": ref}}}},
                              "400": {"description": "invalid_request_error"}},
            },
        }
        paths[f"{base}/{{id}}"] = {
            "get": {"summary": f"Get a {ent}",
                    "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}},
                                   {"name": "expand", "in": "query", "schema": {"type": "string"}}],
                    "responses": {"200": {"description": "ok", "content": {"application/json": {"schema": {"$ref": ref}}}},
                                  "404": {"description": "not_found"}}},
            "patch": {"summary": f"Update a {ent}",
                      "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}],
                      "requestBody": {"content": {"application/json": {"schema": {"$ref": f"#/components/schemas/{ent}Create"}}}},
                      "responses": {"200": {"description": "ok", "content": {"application/json": {"schema": {"$ref": ref}}}},
                                    "404": {"description": "not_found"}}},
            "delete": {"summary": f"Delete a {ent}",
                       "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}],
                       "responses": {"200": {"description": "deleted"}, "404": {"description": "not_found"}}},
        }
    paths["/healthz"] = {"get": {"summary": "Health probe",
                                 "responses": {"200": {"description": "ok"}}}}
    return {
        "openapi": "3.1.0",
        "info": {"title": f"{platform} clean-room API", "version": "1.0.0",
                 "description": manifest.get("description", ""),
                 "x-etzhayyim-did": manifest["did"],
                 "x-wasm-cid": manifest["wasmCid"],
                 "x-runtime": "kotoba-wasm", "x-exec": "browser-local|donated-mesh",
                 "x-tier": manifest.get("tier", "L3")},
        "servers": [{"url": f"ipfs://{manifest['wasmCid']}", "description": "browser-local kotoba-wasm component"}],
        "paths": paths,
        "components": {"schemas": schemas},
    }


def build():
    cats = deepen.parse_platform_categories()
    actor_dirs = sorted(d for d in os.listdir(ACTORS_DIR) if d.endswith("-compat"))
    mcp_servers, openapis, social_feeds = [], [], []
    component_to_actors = {}
    actor_sbom = []
    openapi_written = 0
    # L5 verified enums per handle: {handle: {Entity: {field: [allowed]}}}
    l5_enums = {}
    _l5 = os.path.join(SCHEMAS_DIR, "cleanroom-l5-verification.json")
    if os.path.exists(_l5):
        for a in json.load(open(_l5)).get("actors", []):
            em = {r["entity"]: dict(r["discoveredEnums"])
                  for r in a.get("resources", []) if r.get("discoveredEnums")}
            if em:
                l5_enums[a["handle"]] = em

    for actor in actor_dirs:
        adir = os.path.join(ACTORS_DIR, actor)
        man_path = os.path.join(adir, "manifest.json")
        if not os.path.exists(man_path):
            continue
        m = json.load(open(man_path, encoding="utf-8"))
        handle, did, cid = m["handle"], m["did"], m["wasmCid"]
        tier = m.get("tier", "L3")
        caps = m.get("capabilities", {})

        mcp_servers.append({
            "handle": handle, "did": did, "tier": tier,
            "endpoint": f"ipfs://{cid}", "transport": "ipfs+kotoba-wasm",
            "toolCount": caps.get("mcp", {}).get("toolCount", 0),
            "manifest": f"20-actors/{actor}/manifest.json#/capabilities/mcp",
        })
        api = caps.get("api", {})
        openapis.append({
            "handle": handle, "did": did, "tier": tier,
            "basePath": "/v1", "endpointCount": api.get("endpointCount", 0),
            "ipfs": f"ipfs://{cid}", "health": "/healthz",
            "features": api.get("features", {}),
            "openapi": f"20-actors/{actor}/openapi.json" if tier in ("L4", "L5") else None,
        })
        sp = caps.get("socialpost", {})
        social_feeds.append({
            "handle": handle, "did": did,
            "lexicon": sp.get("lexicon", "app.bsky.feed.post"),
            "source": sp.get("source", ""), "mode": sp.get("mode", "dry-run"),
            "gate": sp.get("gate", "G8"),
        })
        comps = caps.get("supplychain", {}).get("sbomData", {}).get("components", [])
        actor_sbom.append({"handle": handle, "components": [c["name"] for c in comps]})
        for c in comps:
            component_to_actors.setdefault(c["name"], []).append(handle)

        # full OpenAPI for the L4 production cohort
        if tier in ("L4", "L5"):
            platform = actor[:-len("-compat")].strip()
            model = (deepen.PLATFORM_OVERRIDES.get(platform)
                     or deepen.CATEGORY_MODELS.get(cats.get(platform))
                     or deepen.GENERIC_MODEL)
            spec = openapi_spec(platform, model, m, l5_enums.get(m["handle"]))
            with open(os.path.join(adir, "openapi.json"), "w") as f:
                json.dump(spec, f, indent=2, ensure_ascii=False)
                f.write("\n")
            openapi_written += 1

    _w("cleanroom-mcp-index.json", {
        "schemaVersion": "1.0", "kind": "mcp-server-registry",
        "transport": "ipfs+kotoba-wasm", "adr": ["260607", "2606014500"],
        "count": len(mcp_servers),
        "totalTools": sum(s["toolCount"] for s in mcp_servers),
        "servers": mcp_servers,
    })
    _w("cleanroom-openapi-index.json", {
        "schemaVersion": "1.0", "kind": "openapi-registry",
        "adr": ["260607", "2606014500"], "count": len(openapis),
        "totalEndpoints": sum(a["endpointCount"] for a in openapis),
        "l4SpecsAvailable": openapi_written, "apis": openapis,
    })
    _w("cleanroom-supplychain-index.json", {
        "schemaVersion": "1.0", "kind": "supplychain-sbom-index",
        "adr": ["260607", "2606036000"], "count": len(actor_sbom),
        "componentToActors": {k: sorted(set(v)) for k, v in sorted(component_to_actors.items())},
        "actors": actor_sbom,
    })
    _w("cleanroom-socialpost-index.json", {
        "schemaVersion": "1.0", "kind": "socialpost-feed-registry",
        "lexicon": "app.bsky.feed.post", "gate": "G8 (outward posting gated)",
        "adr": ["260607"], "count": len(social_feeds), "feeds": social_feeds,
    })
    print(f"Built capability indexes for {len(mcp_servers)} actors:")
    print(f"  mcp servers: {len(mcp_servers)} ({sum(s['toolCount'] for s in mcp_servers)} tools)")
    print(f"  openapi apis: {len(openapis)} ({sum(a['endpointCount'] for a in openapis)} endpoints; {openapi_written} L4 full specs)")
    print(f"  supplychain components: {len(component_to_actors)}")
    print(f"  socialpost feeds: {len(social_feeds)}")


def _w(name, doc):
    with open(os.path.join(SCHEMAS_DIR, name), "w") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)
        f.write("\n")


if __name__ == "__main__":
    build()
