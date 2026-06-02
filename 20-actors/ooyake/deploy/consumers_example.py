#!/usr/bin/env python3
"""ooyake 公 — gov-atlas consumer examples (ADR-2606021600).

Concrete read patterns for the FIVE consumers the manifest names — each reads the
read-side SSoT via the shared GovAtlas client; none re-derives government structure.
READ-ONLY (G9), offline, no fabrication.

  toritsugi (deliver)  : resolve a procedure → 所管 + 窓口 + 住所 + 書式 + 根拠法令
  danjo (audit)        : enumerate units in a jurisdiction to cross-reference open-data
  kanae (fiscal viz)   : ministries + agencies as the nodes to render fiscal flows over
  himotoki (disclosure): resolve which authority + 窓口 + 住所 to file a 開示請求/FOIA at
  tsumugi (power-graph): the structural ancestry its 縁/取 karma overlays
                         (:gov.unit/organism is the reconcile attr, populated when the
                          engi graph is wired)
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gov_atlas_client import GovAtlas  # noqa: E402


def toritsugi_guide(a: GovAtlas, toritsugi_ref: str):
    """toritsugi: hand a citizen the who/where/how to file a procedure themselves."""
    return a.resolve_procedure(toritsugi_ref)


def danjo_units(a: GovAtlas, cc: str):
    """danjo: the unit list in a jurisdiction to cross-reference against open-data."""
    return [{"id": u[":gov.unit/id"], "name": u.get(":gov.unit/name-local"),
             "level": (u.get(":gov.unit/level") or "")[1:]} for u in a.by_jurisdiction(cc)]


def kanae_fiscal_nodes(a: GovAtlas, cc: str):
    """kanae: ministries + agencies in a jurisdiction = the nodes a fiscal-flow map renders."""
    out = []
    for lvl in ("ministry", "agency"):
        for u in a.by_level(lvl):
            if (u.get(":gov.unit/jurisdiction") or "").split("-")[0] == cc:
                out.append({"id": u[":gov.unit/id"], "name": u.get(":gov.unit/name-local"), "level": lvl})
    return out


def himotoki_route(a: GovAtlas, toritsugi_ref: str):
    """himotoki: which authority + 窓口 + 住所 to direct a 開示請求 / FOIA at."""
    r = a.resolve_procedure(toritsugi_ref)
    if not r:
        return None
    w = r["windows"][0] if r["windows"] else {}
    return {"authority": r["owner"], "legalBasis": r["legalBasis"],
            "window": w.get("name"), "address": (w.get("address") or {}).get("line")}


def tsumugi_structure(a: GovAtlas, uid: str):
    """tsumugi: the structural ancestry chain its 縁/取 karma graph overlays."""
    chain = a.resolve_path(uid)
    return [{"id": u[":gov.unit/id"], "name": u.get(":gov.unit/name-local"),
             "organism": u.get(":gov.unit/organism")} for u in chain]


# ── self-test ─────────────────────────────────────────────────────────────────
def _test():
    a = GovAtlas()
    # toritsugi
    g = toritsugi_guide(a, "jp-juminhyo-utsushi")
    assert g and g["owner"]["name"] == "新宿区"
    # danjo
    du = danjo_units(a, "jpn")
    assert len(du) >= 20 and any(u["id"] == "gov.jpn.mof" for u in du)
    # kanae
    kn = kanae_fiscal_nodes(a, "jpn")
    assert any(n["name"] == "財務省" for n in kn) and any(n["level"] == "agency" for n in kn)
    # himotoki
    hr = himotoki_route(a, "jp-juminhyo-utsushi")
    assert hr and hr["authority"]["name"] == "新宿区" and "歌舞伎町" in (hr["address"] or "")
    assert himotoki_route(a, "nope") is None
    # tsumugi
    ts = tsumugi_structure(a, "gov.jpn.mof.nta.tokyo.kojimachi")
    assert [u["name"] for u in ts] == ["日本国", "財務省", "国税庁", "東京国税局", "麹町税務署"], ts
    print("PASS consumers_example self-test (toritsugi/danjo/kanae/himotoki/tsumugi)")


if __name__ == "__main__":
    a = GovAtlas()
    print("ooyake gov-atlas consumer examples —", len(a.units), "units")
    print("  danjo   units(jpn):", len(danjo_units(a, "jpn")))
    print("  kanae   fiscal-nodes(jpn):", [n["name"] for n in kanae_fiscal_nodes(a, "jpn")][:6], "…")
    print("  himotoki route(住民票):", himotoki_route(a, "jp-juminhyo-utsushi"))
    print("  tsumugi structure(麹町):", " → ".join(u["name"] for u in tsumugi_structure(a, "gov.jpn.mof.nta.tokyo.kojimachi")))
    _test()
