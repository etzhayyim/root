#!/usr/bin/env python3
"""tsubasa 翼 — flight discovery commons langgraph actor (kotoba WASM cell).

ADR-2606072800. The Skyscanner inversion. Honest fare/route meta-search; every onward link is
affiliate-stripped and the member self-books on the airline's own site (no inflow). Handlers
over one kotoba EAVT graph:

  search_fares      query → honest ranked options (total cost + emissions SURFACED, G4)
  compare           cheapest / greenest / fastest — emissions is a first-class axis, never hidden
  self_book_handoff affiliate-stripped handoff to the airline's OWN page (G1)

Hard invariants encoded so they are structurally unrepresentable, not policy:
  - no-affiliate-no-inflow (G1): strip_affiliate removes tracking/affiliate params; the handoff
    carries no commission/tithe and names the member as principal — tsubasa never books.
  - emissions-honest (G4): every result carries co2Kg; `compare` exposes the greenest option as a
    first-class result, so a high-emission option cannot be ranked-away invisibly.
  - anti-dark (G3): there is no urgency / "price will rise" / scarcity field — the function cannot
    emit one.
  - no-person-tracking (G5): search takes the query + fares only; nothing about the searcher.

Murakumo-only for NL parsing (G6). R1 ranks a :representative fare set; live ingest is gated (G8).
"""
from __future__ import annotations

from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

try:
    from kotoba import datalog, llm  # type: ignore
except ImportError:  # local dev fallback
    datalog = llm = None  # type: ignore

# Affiliate / tracking params stripped from an onward airline link (G1). Mirrors okaimono.
_AFFILIATE_PARAMS = frozenset({
    "aff", "affid", "affiliate", "partner", "partner_id", "clickid", "click_id", "subid",
    "tag", "ref", "referrer", "gclid", "fbclid", "msclkid", "irclickid", "ranmid", "siteid",
})
_AFFILIATE_PREFIXES = ("utm_", "aff_", "pk_")


def total_cost_minor(fare: dict) -> int:
    """True total cost a traveller pays: base fare + checked-bag fee (G4 honesty — never just the
    headline fare)."""
    return int(fare.get("fareMinor", 0)) + int(fare.get("baggageMinor", 0))


def strip_affiliate(url: str) -> str:
    """Remove affiliate + tracking parameters from an airline URL (G1) — tsubasa earns no
    referral. Functional params (flight, date, cabin) are preserved; order is kept stable."""
    parts = urlsplit(url)
    kept = [
        (k, v) for (k, v) in parse_qsl(parts.query, keep_blank_values=True)
        if k.lower() not in _AFFILIATE_PARAMS
        and not any(k.lower().startswith(p) for p in _AFFILIATE_PREFIXES)
    ]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(kept), ""))


# --------------------------------------------------------------------------- #
# search (G4 emissions surfaced, G3 honest, G5 stateless-w.r.t.-searcher)
# --------------------------------------------------------------------------- #
_SORTS = {
    "total": total_cost_minor,
    "emissions": lambda f: float(f.get("co2Kg", 0.0)),
    "duration": lambda f: int(f.get("durationMin", 0)),
}


def search_fares(origin: str, destination: str, depart_date: str, fares: list,
                 sort: str = "total") -> list:
    """Return matching fares, each annotated with totalMinor + co2Kg (G4 — emissions on every
    option), ranked by `sort` (total cost default; or emissions / duration). Honest availability:
    no manufactured scarcity, no per-searcher state (G3/G5). Unknown sort falls back to total."""
    key = _SORTS.get(sort, total_cost_minor)
    matches = [
        {**f, "totalMinor": total_cost_minor(f), "co2Kg": float(f.get("co2Kg", 0.0))}
        for f in fares
        if f.get("origin") == origin and f.get("destination") == destination
        and f.get("departDate") == depart_date
    ]
    return sorted(matches, key=key)


# --------------------------------------------------------------------------- #
# compare — cheapest / greenest / fastest as first-class results (G4)
# --------------------------------------------------------------------------- #
def compare(fares: list) -> dict:
    """Expose the cheapest, greenest, and fastest options together so emissions is a first-class
    axis (G4) — a low-fare/high-CO₂ option cannot be presented while hiding a greener one."""
    if not fares:
        return {"cheapest": None, "greenest": None, "fastest": None}
    return {
        "cheapest": min(fares, key=total_cost_minor),
        "greenest": min(fares, key=lambda f: float(f.get("co2Kg", 0.0))),
        "fastest": min(fares, key=lambda f: int(f.get("durationMin", 0))),
    }


# --------------------------------------------------------------------------- #
# self-book handoff (G1 — member books on the airline's own site, no inflow)
# --------------------------------------------------------------------------- #
def self_book_handoff(fare: dict) -> dict:
    """Hand the member to the airline's OWN booking page, affiliate-stripped (G1). tsubasa is not
    the merchant-of-record: no commission, no tithe (external, no internal value flow), principal
    is the member."""
    return {
        "mode": "self-book-handoff",
        "principal": "member",            # tsubasa never books (G1)
        "carrier": fare.get("carrier"),
        "bookUrl": strip_affiliate(fare.get("bookUrl", "")),
        "commissionMinor": 0,             # structural zero (G1)
        "titheMinor": 0,                  # external: no internal value flow
    }
