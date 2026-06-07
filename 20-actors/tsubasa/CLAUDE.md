# 20-actors/tsubasa 翼

**Flight-route/fare discovery commons — Skyscanner inversion. ADR-2606072800. Status: R0+R1.**

Honest fare/route meta-search; closes the last named-app coverage gap (uber→ainori, airbnb/
hotels→shukubo, salesforce→business-manager, calendly→yotei, drive→organizer, indeed→talent,
shopify→omise, **flight-scanner→tsubasa**). Sibling of `watari` (live position) — tsubasa plans,
watari tracks; both observational, neither an OTA.

## Hard prohibitions (structurally unrepresentable, not policy)
- **No affiliate / no inflow** (G1): onward links affiliate-stripped; member self-books on the
  airline's OWN site; tsubasa is never merchant-of-record (`commissionMinor`/`titheMinor` ≡ 0,
  `principal` = member). No commission field in any lexicon.
- **Emissions-honest** (G4): `co2Kg` is REQUIRED on every fare/result; `compare` exposes the
  greenest option as a first-class result — a high-CO₂ option cannot be ranked-away invisibly.
  Rank by true total cost (fare + baggage), not headline fare.
- **Anti-dark** (G3): no urgency / "price will rise" / scarcity field exists.
- **No person fare-tracking** (G5): search is stateless w.r.t. the searcher.

## Gating
Live GDS/airline fare ingest = **Council Lv7+ + operator** (G8). R0 ships `:representative` data;
tsubasa transacts no booking (member self-books).

py/agent.py (10 tests) + kotoba/schema.edn. See ADR-2606072800 for the full gate table.
