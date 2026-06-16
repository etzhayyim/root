#!/usr/bin/env python3
"""aburi 炙り — ingest: the member's OWN privacy exports → tracker-exposure graph datoms.
ADR-2606161630.

This is the ACQUISITION leg (実際の取得). Intake = the member's OWN consented exports, produced on
THEIR OWN device:
  - :apple-app-privacy-report  — iOS Settings ▸ Privacy ▸ App Privacy Report (the per-app data
        access + the ad/tracker DOMAINS each app contacted)
  - :play-data-safety          — Google Play "Data safety" section (per-app data shared/collected
        + purpose; "shared for Advertising or marketing" = a flow to an ad collector)
  - :google-takeout-ads        — Google "Data & privacy" / Ads-settings export (ad personalization
        on/off + your advertiser/topic list + activity controls)
  - :android-permission-dump   — on-device granted permissions per app (ACCESS_FINE_LOCATION,
        READ_CONTACTS, AD_ID, …)

ingest does NO network I/O. It maps each export's AD-RELEVANT, DISCLOSED fields onto the
tracker-exposure-ontology (:surface / :permission / :collector / :datatype nodes + :grants /
:flows-to / :collects 縁) and produces append-only kotoba [:db/add e a v] datoms.

CONSTITUTIONAL gates (the meisai discipline, extended):
  - G1 own-data-only — the input is the MEMBER'S OWN export about their OWN device/apps. No other
    person, no third-party PII.
  - G2/G8 — `guard()` RAISES on credential-shaped keys (password/token/…) and on raw-identifier /
    PAN-shaped values (IDFA/GAID/IMEI/email/phone/cookie, 13–19-digit runs). Only exposure
    STRUCTURE (which data-kind flows to which catalogued collector) is emitted, never a raw value:
    `graph_to_datoms` projects ONLY the datom_emit allowlist (NODE_ATTRS/EDGE_ATTRS), so no
    credential/raw-id attr can reach the substrate even by accident.
  - G3 — collectors carry public catalogue provenance (:collector/catalog); a domain→collector
    mapping is a DISCLOSED fact, never a verdict.
  - G5 — every tx carries the intake content CID; re-ingest of the same export is a no-op (dedup).
  - G7 — local-only: exports live under data/local/ (gitignored); the loop does no network I/O.

Pure stdlib. Deterministic (no wall clock, no randomness).
    python3 methods/ingest.py path/to/export.json --kind :play-data-safety
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
from typing import Any

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import kotoba  # noqa: E402
from datom_emit import NODE_ATTRS, EDGE_ATTRS  # G8 allowlist  # noqa: E402

# ── G2/G8 guard ──────────────────────────────────────────────────────────────
_FORBIDDEN_KEY_TOKENS = (
    "password", "passwd", "secret", "otp", "cvv", "credential", "token", "bearer",
    "pin", "session", "cookie", "idfa", "gaid", "aaid", "imei", "imsi", "udid",
    "idfv", "advertising-id", "advertising_id", "device-id", "device_id", "serial",
    "email", "e-mail", "phone", "msisdn", "ssn", "passport",
)
# 13–19 consecutive digits (spaces/dashes allowed) → a PAN / long raw-identifier shape.
_PAN_RE = re.compile(r"(?:\d[ -]?){13,19}")
# an advertising-id (UUID) shape, e.g. 38400000-8cf0-11bd-b23e-10b96e40000d
_ADID_RE = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
                      r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")
# an email shape
_EMAIL_RE = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


def _walk(node: Any, path: str = ""):
    if isinstance(node, dict):
        for k, v in node.items():
            yield path, "key", k
            yield from _walk(v, f"{path}/{k}")
    elif isinstance(node, (list, tuple)):
        for x in node:
            yield from _walk(x, path)
    else:
        yield path, "value", node


def guard(doc: Any) -> None:
    """G2/G8 structural gate: refuse credential-shaped keys and raw-identifier values anywhere
    in the intake. A card number, an ad-id, an email, or a session token cannot enter the log."""
    for path, role, leaf in _walk(doc):
        s = str(leaf)
        low = s.lower()
        if role == "key" and any(tok in low for tok in _FORBIDDEN_KEY_TOKENS):
            raise ValueError(f"G8: credential/raw-identifier key {s!r} is unrepresentable in aburi")
        if role == "value":
            digits = _PAN_RE.search(s)
            if digits and len(re.sub(r"\D", "", digits.group())) >= 13:
                raise ValueError(f"G8: PAN/long-id value at {path or '/'} is unrepresentable")
            if _ADID_RE.search(s):
                raise ValueError(f"G8: advertising-id (UUID) value at {path or '/'} is unrepresentable")
            if _EMAIL_RE.search(s):
                raise ValueError(f"G8: email value at {path or '/'} is unrepresentable")


# ── graph → datoms (G8: only the datom_emit allowlist is ever projected) ──────
def load_graph(forms: list) -> tuple[dict, list]:
    nodes, edges = {}, []
    for f in forms:
        if not isinstance(f, dict):
            continue
        if ":organism/id" in f:
            nodes[f[":organism/id"]] = f
        elif ":en/from" in f and ":en/to" in f:
            edges.append(f)
    return nodes, edges


def graph_to_datoms(nodes: dict, edges: list, *, intake_cid: str, kind: str) -> list[list]:
    """Project a tracker-exposure graph into append-only [:db/add e a v] datoms. ONLY the
    datom_emit NODE_ATTRS/EDGE_ATTRS allowlist is emitted — credential/raw-id attrs cannot pass."""
    out: list[list] = []
    for nid, n in nodes.items():
        for a in NODE_ATTRS:
            if a in n and n[a] is not None:
                out.append(kotoba.add(nid, a, n[a]))
        out.append(kotoba.add(nid, ":aburi.intake/cid", intake_cid))
        out.append(kotoba.add(nid, ":aburi.intake/kind", kind))
    for e in edges:
        eid = f"en.{e[':en/from']}.{str(e[':en/kind']).lstrip(':')}.{e[':en/to']}"
        for a in EDGE_ATTRS:
            if a in e and e[a] is not None:
                out.append(kotoba.add(eid, a, e[a]))
    return out


# ── disclosed mapping tables (PUBLIC facts; extend per export — G3/G5) ─────────
# ad/tracker DOMAINS (Apple App Privacy Report) → catalogued collector node.
DOMAIN_COLLECTOR = {
    "googleadservices.com": "ax.col.google-admanager",
    "doubleclick.net": "ax.col.google-admanager",
    "googlesyndication.com": "ax.col.admob",
    "app-measurement.com": "ax.col.firebase",
    "crashlytics.com": "ax.col.firebase",
    "graph.facebook.com": "ax.col.meta-audience",
    "facebook.com": "ax.col.meta-audience",
    "applovin.com": "ax.col.applovin",
    "applvn.com": "ax.col.applovin",
    "unityads.unity3d.com": "ax.col.unity-ads",
    "unity3d.com": "ax.col.unity-ads",
    "supersonicads.com": "ax.col.ironsource",
    "adsmoloco.com": "ax.col.ironsource",
    "adsrvr.org": "ax.col.the-trade-desk",
    "criteo.com": "ax.col.criteo",
    "amazon-adsystem.com": "ax.col.amazon-ads",
    "appsflyer.com": "ax.col.appsflyer",
    "adjust.com": "ax.col.adjust",
    "ads-twitter.com": "ax.col.x-ads",
    "rlcdn.com": "ax.col.liveramp",
    "pippio.com": "ax.col.liveramp",
}
# Android permission → (permission node id, data-type node id)
PERMISSION_MAP = {
    "ACCESS_FINE_LOCATION": ("ax.perm.precise-location", "ax.dt.precise-location"),
    "ACCESS_COARSE_LOCATION": ("ax.perm.coarse-location", "ax.dt.coarse-location"),
    "READ_CONTACTS": ("ax.perm.contacts", "ax.dt.contacts"),
    "AD_ID": ("ax.perm.ad-id", "ax.dt.device-id"),
    "com.google.android.gms.permission.AD_ID": ("ax.perm.ad-id", "ax.dt.device-id"),
    "RECORD_AUDIO": ("ax.perm.microphone", "ax.dt.app-usage"),
    "READ_MEDIA_IMAGES": ("ax.perm.photos", "ax.dt.photos"),
}
# collector display-name / alias (Play "Data shared" lists names, not domains) → collector node
NAME_COLLECTOR = {
    "admob": "ax.col.admob", "google admob": "ax.col.admob",
    "google ad manager": "ax.col.google-admanager", "doubleclick": "ax.col.google-admanager",
    "ad manager": "ax.col.google-admanager",
    "firebase": "ax.col.firebase", "google analytics": "ax.col.firebase",
    "meta": "ax.col.meta-audience", "facebook": "ax.col.meta-audience",
    "audience network": "ax.col.meta-audience", "meta audience network": "ax.col.meta-audience",
    "applovin": "ax.col.applovin",
    "unity": "ax.col.unity-ads", "unity ads": "ax.col.unity-ads",
    "ironsource": "ax.col.ironsource",
    "trade desk": "ax.col.the-trade-desk", "the trade desk": "ax.col.the-trade-desk",
    "criteo": "ax.col.criteo",
    "amazon": "ax.col.amazon-ads", "amazon advertising": "ax.col.amazon-ads",
    "appsflyer": "ax.col.appsflyer",
    "adjust": "ax.col.adjust",
    "x ads": "ax.col.x-ads", "twitter": "ax.col.x-ads",
    "liveramp": "ax.col.liveramp",
}


def resolve_collector_name(name: str) -> str | None:
    """Map a Play/disclosed collector display name to a catalogued collector node id (exact then
    substring), else None. A name→collector mapping is a DISCLOSED fact (G3)."""
    low = str(name).strip().lower()
    if low in NAME_COLLECTOR:
        return NAME_COLLECTOR[low]
    for alias, cid in NAME_COLLECTOR.items():
        if alias in low or low in alias:
            return cid
    return None


# Apple/Play data CATEGORY → (permission node, data-type node)
CATEGORY_MAP = {
    "Location": ("ax.perm.coarse-location", "ax.dt.coarse-location"),
    "Precise Location": ("ax.perm.precise-location", "ax.dt.precise-location"),
    "Coarse Location": ("ax.perm.coarse-location", "ax.dt.coarse-location"),
    "Identifiers": ("ax.perm.ad-id", "ax.dt.device-id"),
    "Device or other IDs": ("ax.perm.ad-id", "ax.dt.device-id"),
    "Contacts": ("ax.perm.contacts", "ax.dt.contacts"),
    "Contact Info": ("ax.perm.contacts", "ax.dt.contacts"),
    "Browsing History": ("ax.perm.browsing-history", "ax.dt.browsing"),
    "Search History": ("ax.perm.browsing-history", "ax.dt.browsing"),
    "Purchases": ("ax.perm.purchase-history", "ax.dt.purchases"),
    "Purchase History": ("ax.perm.purchase-history", "ax.dt.purchases"),
    "Usage Data": ("ax.perm.app-usage", "ax.dt.app-usage"),
    "App Activity": ("ax.perm.app-usage", "ax.dt.app-usage"),
    "Photos or Videos": ("ax.perm.photos", "ax.dt.photos"),
    "Health and Fitness": ("ax.perm.health", "ax.dt.health-fitness"),
}

# minimal ontology node templates so an ingested graph is self-contained + analyzable.
_PERM_LABELS = {
    "ax.perm.ad-id": ("Advertising ID (GAID / IDFA)", ":ad-id", ":sensitive"),
    "ax.perm.precise-location": ("Precise location", ":precise-location", ":critical"),
    "ax.perm.coarse-location": ("Approximate location", ":location", ":sensitive"),
    "ax.perm.contacts": ("Contacts / address book", ":contacts", ":sensitive"),
    "ax.perm.browsing-history": ("Browsing / search history", ":browsing-history", ":sensitive"),
    "ax.perm.purchase-history": ("Purchase history", ":purchase-history", ":moderate"),
    "ax.perm.app-usage": ("App / device usage", ":app-usage", ":moderate"),
    "ax.perm.photos": ("Photos / media", ":photos", ":sensitive"),
    "ax.perm.microphone": ("Microphone", ":microphone", ":sensitive"),
    "ax.perm.health": ("Health / fitness data", ":health", ":critical"),
}
_DT_LABELS = {
    "ax.dt.precise-location": ("Precise location", ":precise-location", ":critical"),
    "ax.dt.coarse-location": ("Coarse location", ":coarse-location", ":sensitive"),
    "ax.dt.device-id": ("Device / advertising ID", ":device-id", ":sensitive"),
    "ax.dt.contacts": ("Contacts", ":contacts", ":sensitive"),
    "ax.dt.browsing": ("Browsing / search", ":browsing", ":sensitive"),
    "ax.dt.purchases": ("Purchases", ":purchases", ":moderate"),
    "ax.dt.app-usage": ("App usage / events", ":app-usage", ":moderate"),
    "ax.dt.photos": ("Photos / media", ":photos", ":sensitive"),
    "ax.dt.health-fitness": ("Health / fitness", ":health-fitness", ":critical"),
}
_COL_LABELS = {
    "ax.col.admob": ("Google AdMob", ":ad-network", "org.corp.alphabet", ":exodus"),
    "ax.col.google-admanager": ("Google Ad Manager (DoubleClick)", ":exchange", "org.corp.alphabet", ":sellers-json"),
    "ax.col.firebase": ("Google Firebase Analytics", ":analytics", "org.corp.alphabet", ":exodus"),
    "ax.col.meta-audience": ("Meta Audience Network (FB SDK)", ":ad-network", "org.corp.meta", ":exodus"),
    "ax.col.applovin": ("AppLovin", ":ad-network", "org.corp.applovin", ":exodus"),
    "ax.col.unity-ads": ("Unity Ads", ":ad-network", "org.corp.unity", ":exodus"),
    "ax.col.ironsource": ("ironSource (mediation)", ":ssp", "org.corp.unity", ":exodus"),
    "ax.col.the-trade-desk": ("The Trade Desk", ":dsp", "org.corp.ttd", ":sellers-json"),
    "ax.col.criteo": ("Criteo (retargeting)", ":dsp", "org.corp.criteo", ":sellers-json"),
    "ax.col.amazon-ads": ("Amazon Advertising", ":ad-network", "org.corp.amazon", ":sellers-json"),
    "ax.col.appsflyer": ("AppsFlyer (attribution)", ":analytics", "org.corp.appsflyer", ":exodus"),
    "ax.col.adjust": ("Adjust (attribution)", ":analytics", "org.corp.adjust", ":exodus"),
    "ax.col.x-ads": ("X Ads", ":ad-network", "org.corp.x-corp", ":sellers-json"),
    "ax.col.liveramp": ("LiveRamp (identity broker)", ":data-broker", "org.corp.liveramp", ":iab"),
}


class _GraphBuilder:
    """Accumulates ontology nodes + 縁 with dedup; emits the seed-shape form list."""

    def __init__(self):
        self.nodes: dict[str, dict] = {}
        self.edges: dict[tuple, dict] = {}

    def surface(self, sid, label, kind, operator):
        self.nodes.setdefault(sid, {":organism/id": sid, ":organism/kind": ":surface",
                                    ":organism/label": label, ":surface/kind": kind,
                                    ":surface/operator": operator,
                                    ":organism/sourcing": ":representative"})

    def perm(self, pid):
        label, kind, sens = _PERM_LABELS.get(pid, (pid, ":unknown", ":moderate"))
        self.nodes.setdefault(pid, {":organism/id": pid, ":organism/kind": ":permission",
                                    ":organism/label": label, ":permission/kind": kind,
                                    ":permission/sensitivity": sens,
                                    ":organism/sourcing": ":representative"})

    def collector(self, cid):
        if cid in _COL_LABELS:
            label, kind, org, cat = _COL_LABELS[cid]
            sourcing = ":authoritative"
        else:
            label, kind, org, cat, sourcing = (cid, ":tracker-sdk", "org.corp.unknown",
                                               ":exodus", ":representative")
        self.nodes.setdefault(cid, {":organism/id": cid, ":organism/kind": ":collector",
                                    ":organism/label": label, ":collector/kind": kind,
                                    ":collector/org": org, ":collector/catalog": cat,
                                    ":organism/sourcing": sourcing})

    def datatype(self, did):
        label, kind, sens = _DT_LABELS.get(did, (did, ":app-usage", ":moderate"))
        self.nodes.setdefault(did, {":organism/id": did, ":organism/kind": ":datatype",
                                    ":organism/label": label, ":datatype/kind": kind,
                                    ":datatype/sensitivity": sens,
                                    ":organism/sourcing": ":representative"})

    def edge(self, frm, to, kind, load):
        key = (frm, to, kind)
        if key in self.edges:
            self.edges[key][":en/load"] = max(self.edges[key][":en/load"], float(load))
        else:
            self.edges[key] = {":en/from": frm, ":en/to": to, ":en/kind": kind,
                               ":en/load": float(load), ":en/sourcing": ":representative"}

    def forms(self) -> list:
        return list(self.nodes.values()) + list(self.edges.values())


# ── per-format adapters (raw export dict → seed-shape forms) ──────────────────
def adapt_apple_app_privacy_report(raw: dict) -> list:
    """iOS App Privacy Report. raw = {"surface": {...}?, "apps": [{"app": str,
    "accessed": ["Location", ...], "domains": ["doubleclick.net", ...]}]}."""
    g = _GraphBuilder()
    sid = "ax.surface.apple-appstore"
    g.surface(sid, "Apple App Store / iOS", ":app-store", "org.corp.apple")
    for app in raw.get("apps", []):
        for cat in app.get("accessed", []):
            pid, did = CATEGORY_MAP.get(cat, (None, None))
            if pid:
                g.perm(pid); g.datatype(did)
                g.edge(sid, pid, ":grants", 0.7)
                for dom in app.get("domains", []):
                    cid = DOMAIN_COLLECTOR.get(dom.lower().lstrip("."))
                    if cid:
                        g.collector(cid)
                        g.edge(pid, cid, ":flows-to", 0.8)
                        g.edge(cid, did, ":collects", 0.8)
        # a contacted ad domain with no mapped category still evidences a flow (via ad-id)
        for dom in app.get("domains", []):
            cid = DOMAIN_COLLECTOR.get(dom.lower().lstrip("."))
            if cid and not app.get("accessed"):
                g.perm("ax.perm.ad-id"); g.datatype("ax.dt.device-id"); g.collector(cid)
                g.edge(sid, "ax.perm.ad-id", ":grants", 0.6)
                g.edge("ax.perm.ad-id", cid, ":flows-to", 0.7)
                g.edge(cid, "ax.dt.device-id", ":collects", 0.7)
    return g.forms()


def adapt_play_data_safety(raw: dict) -> list:
    """Google Play Data-safety. raw = {"apps": [{"app": str, "shared": [{"type": "Location",
    "purpose": "Advertising or marketing", "collectors": ["AppLovin"]?}], "collected": [...]}]}."""
    g = _GraphBuilder()
    sid = "ax.surface.google-android"
    g.surface(sid, "Google / Android + Play", ":os", "org.corp.alphabet")
    for app in raw.get("apps", []):
        for share in app.get("shared", []):
            cat = share.get("type")
            pid, did = CATEGORY_MAP.get(cat, (None, None))
            if not pid:
                continue
            g.perm(pid); g.datatype(did)
            g.edge(sid, pid, ":grants", 0.7)
            purpose = str(share.get("purpose", "")).lower()
            load = 0.8 if ("advertis" in purpose or "marketing" in purpose) else 0.4
            cols = share.get("collectors") or (["AppLovin"] if "advertis" in purpose else [])
            for cn in cols:
                cid = resolve_collector_name(cn)
                if cid:
                    g.collector(cid)
                    g.edge(pid, cid, ":flows-to", load)
                    g.edge(cid, did, ":collects", load)
    return g.forms()


def adapt_google_takeout_ads(raw: dict) -> list:
    """Google Takeout Ads-settings. raw = {"adPersonalization": bool, "activityControls":
    {"web": bool, "location": bool, "youtube": bool}}. (No advertiser names are ingested — they
    would be PII; only the on/off structure.)"""
    g = _GraphBuilder()
    sid = "ax.surface.google-search"
    g.surface(sid, "Google Search", ":search", "org.corp.alphabet")
    ac = raw.get("activityControls", {})
    if ac.get("web"):
        g.perm("ax.perm.browsing-history"); g.datatype("ax.dt.browsing")
        g.collector("ax.col.google-admanager")
        g.edge(sid, "ax.perm.browsing-history", ":grants", 0.9)
        g.edge("ax.perm.browsing-history", "ax.col.google-admanager", ":flows-to", 0.9)
        g.edge("ax.col.google-admanager", "ax.dt.browsing", ":collects", 0.9)
    if raw.get("adPersonalization"):
        g.perm("ax.perm.ad-personalization"); g.datatype("ax.dt.identifiers")
        g.collector("ax.col.google-admanager")
        g.edge(sid, "ax.perm.ad-personalization", ":grants", 0.8)
        g.edge("ax.perm.ad-personalization", "ax.col.google-admanager", ":flows-to", 0.8)
        g.edge("ax.col.google-admanager", "ax.dt.identifiers", ":collects", 0.7)
    if ac.get("location"):
        g.perm("ax.perm.precise-location"); g.datatype("ax.dt.precise-location")
        g.collector("ax.col.admob")
        g.edge(sid, "ax.perm.precise-location", ":grants", 0.8)
        g.edge("ax.perm.precise-location", "ax.col.admob", ":flows-to", 0.7)
        g.edge("ax.col.admob", "ax.dt.precise-location", ":collects", 0.7)
    return g.forms()


def adapt_android_permission_dump(raw: dict) -> list:
    """On-device permission dump. raw = {"apps": [{"package": str, "grants": ["AD_ID", ...]}]}.
    A granted permission is a :grants edge to its data-type's permission node; the actual flow to a
    collector is unknown from the dump alone (no opt-out info), so it is left as a reciprocity gap."""
    g = _GraphBuilder()
    sid = "ax.surface.free-mobile-app"
    g.surface(sid, "On-device apps (Android)", ":mobile-app", "org.corp.various")
    for app in raw.get("apps", []):
        for perm in app.get("grants", []):
            pid, did = PERMISSION_MAP.get(perm, (None, None))
            if pid:
                g.perm(pid); g.datatype(did)
                g.edge(sid, pid, ":grants", 0.8)
                # a permission that an ad-bearing app holds plausibly flows to AdMob/Meta
                if perm in ("AD_ID", "com.google.android.gms.permission.AD_ID"):
                    g.collector("ax.col.admob"); g.collector("ax.col.meta-audience")
                    g.edge(pid, "ax.col.admob", ":flows-to", 0.7)
                    g.edge(pid, "ax.col.meta-audience", ":flows-to", 0.6)
                    g.edge("ax.col.admob", did, ":collects", 0.7)
                    g.edge("ax.col.meta-audience", did, ":collects", 0.6)
    return g.forms()


ADAPTERS = {
    ":apple-app-privacy-report": adapt_apple_app_privacy_report,
    ":play-data-safety": adapt_play_data_safety,
    ":google-takeout-ads": adapt_google_takeout_ads,
    ":android-permission-dump": adapt_android_permission_dump,
}


def load_export(path: pathlib.Path) -> tuple[Any, str]:
    """Read one local export file (.json / .edn) → (raw_doc, content-cid)."""
    raw_bytes = path.read_bytes()
    text = raw_bytes.decode("utf-8")
    doc = json.loads(text) if path.suffix == ".json" else kotoba.parse_edn(text)
    return doc, kotoba.content_cid(raw_bytes)


def export_to_datoms(raw: Any, kind: str, intake_cid: str) -> list[list]:
    """Adapt one export → guard → graph → append-only datoms (G8 allowlist)."""
    guard(raw)                                  # G2/G8 — raw values screened first
    if kind not in ADAPTERS:
        raise ValueError(f"unknown export kind {kind!r}; one of {sorted(ADAPTERS)}")
    forms = ADAPTERS[kind](raw)
    guard(forms)                                # belt-and-suspenders: screen mapped forms too
    nodes, edges = load_graph(forms)
    return graph_to_datoms(nodes, edges, intake_cid=intake_cid, kind=kind)


def main(argv):
    if len(argv) < 2 or argv[1].startswith("--"):
        print("usage: ingest.py path/to/export.json --kind :play-data-safety", file=sys.stderr)
        return 2
    path = pathlib.Path(argv[1])
    kind = argv[argv.index("--kind") + 1] if "--kind" in argv else ":play-data-safety"
    raw, cid = load_export(path)
    datoms = export_to_datoms(raw, kind, cid)
    nodes, edges = load_graph(ADAPTERS[kind](raw))
    print(f"aburi ingest: {path.name} ({kind}) → {len(nodes)} nodes / {len(edges)} 縁 / "
          f"{len(datoms)} datoms (intake-cid {cid[:14]}…)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
