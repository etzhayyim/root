#!/usr/bin/env python3
"""Create minimal appview stub dirs for countries in static-profile-data
that lack an appview dir. Only kotodama.jsonld is created — src/app.ts
and wrangler.jsonc remain absent, so `etzhayyim deploy` will fail until those
are added. The stub is enough for `enrich-kotodama-profiles.py` to work.
"""
import json, os, glob
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
APPVIEW = ROOT / "60-apps/etzhayyim-project-states/appview"
STATIC = json.loads((Path(__file__).parent / "static-profile-data.json").read_text())

def nanoid_for(iso: str) -> str:
    # Match existing convention: g0v{iso}01 (4-3-2 = 8 chars)
    return f"g0v{iso.lower()}01"

def existing_isos() -> set:
    out = set()
    for d in glob.glob(str(APPVIEW / "etzhayyim-wasm-states-*")):
        parts = os.path.basename(d).split("-")
        if len(parts) >= 5: out.add(parts[4])
    return out

def make_stub(iso: str, display_name: str) -> dict:
    nanoid = nanoid_for(iso)
    return {
        "@context": "https://etzhayyim.com/ns/kotodama/v1",
        "@id": f"did:web:{iso}.state.etzhayyim.com",
        "convoSystemPrompt": f"You are the {display_name} AI Agent. You represent government organizations as path-based DIDs. Respond professionally.",
        "governance": {"raci": "responsible", "classification": "public", "complianceFrameworks": []},
        "kpi": ["GovOrg DID registration count"],
        "name": f"gov-{iso}",
        "nanoid": nanoid,
        "performerType": "service",
        "profile": {
            "avatar": iso.upper()[:2],
            "banner": "#888888",
            "capabilities": ["gov-actor-registry", "path-did-resolution"],
            "category": "government",
            "country": iso,
            "contract": "Constitutional / basic law",
            "description": f"{display_name} — path-based DID registry (minimal stub; expand for ministries).",
            "displayName": display_name,
            "isBot": True,
            "agentType": "autonomous"
        },
        "project": "states",
        "routes": [{"host": f"{iso}.state.etzhayyim.com", "paths": ["/"], "tls": True}],
        "runtimeType": "worker",
        "space": {
            "channels": [{"default": True, "description": f"{display_name} activity feed", "kind": "public", "name": f"gov-{iso}-feed"}],
            "description": f"{display_name} — AI Agent registry",
            "historyVisibility": "world-readable",
            "joinRule": "public",
            "name": display_name
        },
        "triggers": {
            "subscribeRepos": {"collections": ["app.bsky.feed.post", "app.bsky.feed.like", "app.bsky.graph.follow", "com.etzhayyim.apps.site.wet", "com.etzhayyim.apps.site.wat", "com.etzhayyim.apps.site.page", "com.etzhayyim.apps.site.domain"]}
        },
        "uiType": "yoro",
        "version": "1.0.0"
    }

def main():
    existing = existing_isos()
    created = []
    for iso, entry in STATIC.items():
        if iso in existing: continue
        name = entry.get("displayName") or iso.upper()
        dir_name = f"etzhayyim-wasm-states-{iso}-{nanoid_for(iso)}"
        dir_path = APPVIEW / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        (dir_path / "kotodama.jsonld").write_text(
            json.dumps(make_stub(iso, name), indent=2, ensure_ascii=False) + "\n"
        )
        created.append(iso)
    print(f"created {len(created)} stub kotodama.jsonld files")
    print(' '.join(created[:20]), '...' if len(created) > 20 else '')

if __name__ == "__main__":
    main()
