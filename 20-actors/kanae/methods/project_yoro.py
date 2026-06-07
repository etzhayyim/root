"""project_yoro.py — project kanae fundFlowEdge records into yoro `:yoro.fiscal/*` datoms.

The yoro Resource Flow tab (60-apps/etzhayyim-project-yoro …/src/lib/fiscal/ResourceFlowTab.svelte)
reads `:yoro.fiscal/*` + `:yoro.ownership/*` datoms from the kotoba Datom log via kotoba-sw.js.
This projector is the kanae→yoro bridge: it maps each fundFlowEdge endpoint (an aggregate
fiscal-authority / recipient-class label) to a stable government mirror-actor DID
(`did:web:etzhayyim.com:actor:<handle>`, entity-as-actor ADR-2606042330) and emits the
{e,a,v_edn,added} datoms the tab consumes.

OFFLINE / representative by construction: this writes into the same-origin seed snapshot, NOT a
live published block. Live publication is kanae G7/G11 + Council-gated (no live publish here).

Stdlib only. Deterministic: same edges → same datoms.
"""

from __future__ import annotations

import json
import re
from typing import Any

# Endpoint label → (yoro mirror-actor handle, stage tier). Aggregate gov nodes only (G10).
_LABEL_DID = [
    (re.compile(r"一般会計|National Treasury|General Account"), "kokko", "L7"),
    (re.compile(r"文部科学省|Ministry of Education"), "gov-jp-mext", "L5"),
    (re.compile(r"国立大学法人"), "gov-jp-mext-univ-grants", "L1"),
    (re.compile(r"科学技術振興"), "gov-jp-mext-sci-tech", "L1"),
]
_ACTOR_PREFIX = "did:web:etzhayyim.com:actor:"

# Minimal profile records so the projected gov nodes resolve as actors on /search + /profile.
_PROFILES = {
    "gov-jp-mext": {
        "handle": "gov-jp-mext.etzhayyim.com",
        "displayName": "文部科学省 (MEXT) — gov mirror",
        "description": "Government mirror-actor (observational, ADR-2606042330). 文教及び科学振興費 fiscal flow assembled by kanae from danjo budget ledger (:representative).",
    },
}


def _slug_did(label: str) -> str:
    for pat, handle, _stage in _LABEL_DID:
        if pat.search(label):
            return _ACTOR_PREFIX + handle
    # fallback: deterministic slug from the label
    slug = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")[:32] or "gov-unknown"
    return _ACTOR_PREFIX + "gov-jp-" + slug


def _stage_for(label: str) -> str:
    for pat, _handle, stage in _LABEL_DID:
        if pat.search(label):
            return stage
    return "L5"


def _datom(e: str, a: str, value: Any) -> dict[str, Any]:
    return {"e": e, "a": a, "v_edn": json.dumps(value, ensure_ascii=False), "added": True}


def project(edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """fundFlowEdge list → `:yoro.fiscal/*` (+ minimal `:yoro.profile/*`) datoms."""
    datoms: list[dict[str, Any]] = []
    seen_profiles: set[str] = set()

    for edge in edges:
        from_did = _slug_did(edge["fromEndpoint"]["label"])
        to_did = _slug_did(edge["toEndpoint"]["label"])
        fy = int(edge["period"].replace("FY", "") or 0)
        stage = _stage_for(edge["fromEndpoint"]["label"])
        e = f"fiscal:{from_did}:{to_did}:{fy}:{edge['flowClass']}"
        datoms += [
            _datom(e, ":yoro.fiscal/from", from_did),
            _datom(e, ":yoro.fiscal/to", to_did),
            _datom(e, ":yoro.fiscal/stage", stage),
            _datom(e, ":yoro.fiscal/fiscalYear", fy),
            _datom(e, ":yoro.fiscal/amountJpy", int(edge["amount"])),
            _datom(e, ":yoro.fiscal/basis", f"{edge['flowClass']} · {edge.get('_programCode', '')} (kanae assembled, :representative)"),
            _datom(e, ":yoro.fiscal/programCode", edge.get("_programCode", "")),
            _datom(e, ":yoro.fiscal/sourceUrl", edge.get("_sourceUrl", "")),
            _datom(e, ":yoro.fiscal/observedAt", edge.get("observedAt", "")),
        ]
        # minimal profiles for endpoints that have one defined
        for label in (edge["fromEndpoint"]["label"], edge["toEndpoint"]["label"]):
            did = _slug_did(label)
            handle = did[len(_ACTOR_PREFIX):]
            prof = _PROFILES.get(handle)
            if prof and did not in seen_profiles:
                seen_profiles.add(did)
                pe = f"profile:{did}"
                datoms += [
                    _datom(pe, ":yoro.profile/did", did),
                    _datom(pe, ":yoro.profile/handle", prof["handle"]),
                    _datom(pe, ":yoro.profile/displayName", prof["displayName"]),
                    _datom(pe, ":yoro.profile/description", prof["description"]),
                ]
    return datoms


def merge_into_seed(seed_path: str, datoms: list[dict[str, Any]]) -> dict[str, int]:
    """Idempotently merge projected datoms into the yoro seed snapshot.

    Removes any prior `:yoro.fiscal/*` entities this projector owns (entity id starts with
    'fiscal:did:web:etzhayyim.com:actor:gov-jp' or the kokko→gov chain) before adding, so re-runs
    don't duplicate. The hand-authored ooyake demo seed (different entity ids) is left untouched.
    """
    with open(seed_path, encoding="utf-8") as fh:
        seed = json.load(fh)

    owned_entities = {d["e"] for d in datoms}
    before = len(seed)
    seed = [d for d in seed if d.get("e") not in owned_entities]
    removed = before - len(seed)
    seed.extend(datoms)

    with open(seed_path, "w", encoding="utf-8") as fh:
        json.dump(seed, fh, ensure_ascii=False, separators=(",", ":"))
    return {"removed": removed, "added": len(datoms), "total": len(seed)}


if __name__ == "__main__":
    import sys
    sys.path.insert(0, "20-actors")
    from danjo.methods.budget_ledger import build_ledger, load_seed
    from kanae.methods.assemble_flows import assemble

    seed_in = "20-actors/danjo/data/gov-fiscal-seed.jp.json"
    edges = assemble(build_ledger(load_seed(seed_in)))
    datoms = project(edges)
    print(f"project_yoro: {len(edges)} edges → {len(datoms)} yoro datoms")
    if len(sys.argv) > 1:
        stats = merge_into_seed(sys.argv[1], datoms)
        print(f"  merged into {sys.argv[1]}: {stats}")
    else:
        print(json.dumps(datoms[:9], ensure_ascii=False, indent=1))
