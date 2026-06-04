---
id: adr-2606038400-yadori-dns-availability-and-domain-acquisition
title: "ADR-2606038400: yadori (宿り) — DNS-availability + domain-acquisition Tier-B actor (R0)"
status: proposed
doc_type: adr
topic: yadori-domain-acquisition
authoritative: true
last_verified: 2026-06-03
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - 20-actors/yadori
  - com.etzhayyim.yadori.*
depends_on:
  - "2606012100"
  - "2605231525"
  - "2605215000"
  - "2605192115"
  - "2605222330"
related:
  - "2605211757"
  - "2606031600"
  - "2606013800"
  - "2605181100"
supersedes: []
superseded_by: []
---

# ADR-2606038400: yadori (宿り) — DNS-availability + domain-acquisition Tier-B actor (R0)

**Status**: proposed
**Date**: 2026-06-03
**Deciders**: Jun Kawasaki

# Context

The repo registers actor DIDs under `did:web:etzhayyim.com:actor:<handle>` and runs the apex
CF Worker that issues each `did.json` (ADR-2606013800). But **acquiring the underlying domain
name** — checking whether a name is free, then reserving/registering it — was never an actor. It
was a **manual** Cloudflare-Registrar action: `etzhayyim.com` was registered by hand on 2026-05-15
(CLAUDE.md §Identity; ADR-2605222330), and the only registrar-touching code is
`20-actors/magatama/py/.../ingest/dns.py`, which orchestrates an inbound **transfer** (Squarespace →
Cloudflare), not availability lookup or new acquisition.

The triggering question (a GoDaddy ad link): *「DNS の空きを確認、予約を行う actor は設計されているか」*
The honest answer was **no**. This ADR designs that actor — but **inverts** the GoDaddy/retail-registrar
shape the way `okaimono` inverts Amazon (ADR-2606012100), because three retail-registrar defaults are
constitutional violations here:

1. **Fiat purchase inflow** — registrar fees on a credit card / fiat processor violate §1.3
   (external `purchase` inflow) + the substrate Payment rules (no Stripe/PayPal/fiat).
2. **Markup + upsell + parking/affiliate revenue** — GoDaddy's economics (premium-domain markup,
   privacy upsell, parking-page ads, affiliate) collide with the Charter Rider §2 ad-free /
   anti-gatekeeping posture.
3. **Domain speculation** — warehousing/reselling names for profit is the opposite of a non-profit
   provisioning commons.

A domain is where an actor *dwells* (宿り = taking up lodging). yadori provides the name without
importing the retail-registrar pathologies.

# Decision

Create **yadori (宿り)**, a Tier-B R0 actor at `did:web:etzhayyim.com:actor:yadori`.

**Mission.** Check DNS/domain availability and shepherd a *member-principal* acquisition of a name
the etzhayyim substrate needs (e.g. a new actor subdomain, a donated project domain), via the
**Cloudflare Registrar at-cost path** by default — never as a fiat buyer, never as a speculator.

**Scope by ring (acquisition = okaimono assisted-checkout, member-principal):**

- **Availability (read-only, ships at R0).** RDAP `domain` lookup (modern public successor to
  WHOIS port-43) classifies a name `available` / `registered` / `unsupported-tld` / `invalid`.
  Offline-default against a `:representative` RDAP bootstrap table + fixtures; live RDAP fetch is
  G7-gated. EPP `<check>` is the registrar-side equivalent for R1.
- **Naming (Murakumo-only).** NL → candidate names + cross-TLD alternatives when a name is taken;
  every candidate passes the Charter-Rider §2(a)–(h) scanner and a **no-squatting eligibility
  screen** (G6) before it is ever surfaced.
- **Quote.** Registrar selection (Cloudflare default, at-cost) + TLD policy/price as *data only* —
  affiliate/upsell stripped by construction (mirrors okaimono `strip_affiliate`).
- **Reservation/registration.** An **unsigned reservation intent** (`serverHeldKey=false`); the
  member is the registrant-of-record and the payer; yadori is **never** the buyer. Authorization =
  member signature only — a server signature is refused (G5, ADR-2605231525). Live registrar mutate
  is Council Lv6+ + operator gated (G7).
- **Provision.** Post-acquisition DNS zone + `did:web` wiring **plan** (records for the apex Worker,
  ADR-2606013800; cutover pattern from ADR-2605211757). Plan only at R0.

**Cells (5; langgraph → WASM; Murakumo-only; `.solve()` raises at R0):**
`availability_check` · `name_suggest` · `registrar_quote` · **`reservation`** (coded reference cell)
· `dns_provision`.

**Gates (immutable R0→R3):**

- **G1 read-only-availability** — availability via RDAP / EPP `<check>` / public WHOIS only;
  rate-limited; **no third-party zone enumeration** (no AXFR brute, no subdomain-enum-as-product).
- **G2 no-fiat-inflow / member-principal** — registrar fees are **never** paid from religious-corp
  funds or any fiat processor; acquisition runs through okaimono member-principal assisted-checkout
  (ADR-2606012100), so §1.3 holds **without** a Lv7+ amendment. yadori is never the buyer-of-record.
- **G3 cloudflare-registrar-default** — Cloudflare Registrar (at-cost, no markup) is the default,
  consistent with existing did:web operations; **GoDaddy and other fiat-markup registrars are not
  recommended**, and any external registrar is Council-gated.
- **G4 murakumo-only** — name/NL inference via LiteLLM `127.0.0.1:4000` only (ADR-2605215000).
- **G5 no-server-key** — registrar/EPP credentials are held by the member-operator, never
  platform-held; registration authorization is a member signature (ADR-2605231525).
- **G6 no-squatting** *(defining)* — no cybersquatting / typosquatting / trademark infringement /
  brand impersonation / speculation / parking / drop-catch warehousing. Every candidate clears a
  held-trademark + confusable screen and the Charter-Rider scanner.
- **G7 outward-gated** — live registrar mutate (reserve/register/transfer) and live RDAP fetch are
  Council Lv6+ + operator gated; R0 = offline availability + intent build only.
- **G8 sourcing-honesty** — `:representative` RDAP bootstrap + fixtures flagged; bounded subset.
- **G9 PII-consent** — registrant contact data (WHOIS) is consent-bound, encrypted
  (`com.etzhayyim.encrypted.*`, ADR-2605181100), WHOIS-privacy proxy default.

**Non-goals:** N1 no domain speculation/investment/resale/parking-for-revenue · N2 no
cybersquatting/typosquatting/trademark infringement/impersonation · N3 no bulk drop-catching /
automated mass registration · N4 no third-party zone surveillance product · N5 no DNS provisioning
for prohibited content or detection-evasion (fast-flux / DGA / phishing infra).

**Empirical artifact.** `methods/availability.py` (stdlib only): IDN/punycode normalization, a
`:representative` IANA RDAP bootstrap table, RDAP-URL construction, status→availability
classification, and cross-TLD alternative suggestion. The **`availability_check` cell wraps it**
(normalize → resolve-rdap → classify → record), with the **live RDAP fetch wired but G7-gated** — it
fires only when an operator passes `operator_gate=True` AND the process env `YADORI_ALLOW_LIVE_RDAP=1`
is set; otherwise the cell stays offline (fixture or `:unknown`, never a socket) and never guesses
`:available` without evidence (G8). A descriptive RDAP `User-Agent` is sent (several registries,
e.g. PIR/.org, 403 a bare request). The defining `reservation` cell's state machine enforces
G2/G3/G5/G6 purely. **31 tests green** (11 classifier + 20 cell state-machine); `.solve()` raises on
both coded cells until a Council activation ADR. The gated live path was **empirically verified**
read-only across `.com`/`.org`/`.dev` (example.com / etzhayyim.com → registered; unregistered names
→ available).

# Consequences

**Positive.** Closes the manual gap between "we minted an actor DID" and "the name exists" with a
charter-clean path. Availability check is genuinely usable today (offline + gated-live). The
member-principal acquisition reuses the already-ratified okaimono pattern, so no new payment
primitive and no §1.3 amendment is needed. Naming + screening keep the substrate off cybersquatting
and speculation by construction.

**Negative / risk.** R0 ships no live registration (intent only) — a real acquisition still needs
operator + Council action (G7). The RDAP bootstrap table is a bounded subset; an unsupported TLD
degrades to `unsupported-tld` rather than a definitive answer (logged, G8). Member-principal means
yadori cannot "just buy" a name; that friction is intentional (G2). EPP integration, registrar API
auth, and the okaimono settlement wiring are deferred to R1+.

# Alternatives Considered

1. **A fiat registrar integration (GoDaddy/Namecheap API + org card).** Rejected — direct §1.3 /
   substrate-Payment violation, plus Rider §2 markup/affiliate/parking conflicts.
2. **Fold it into okaimono as a "domain" SKU.** Rejected as the home, kept as the *mechanism* —
   domains carry registrar/EPP/DNS/did:web concerns (availability, zone, trademark screen) that
   warrant a dedicated actor; yadori *reuses* okaimono's assisted-checkout for the payment leg.
3. **Extend the magatama `dns.py` transfer module.** Rejected — that is transfer orchestration
   (Squarespace→CF) with a different shape; availability + acquisition is new surface.
4. **WHOIS port-43 scraping as the availability primitive.** Rejected in favor of RDAP (structured
   JSON, rate-limit-friendly, the IANA-mandated successor); WHOIS retained only as public fallback.
5. **Server-held registrar credentials for one-click registration.** Rejected — violates G5 /
   ADR-2605231525 no-server-key; the member is registrant + signer.

# References

- ADR-2606012100 — okaimono provisioning commons (member-principal assisted-checkout; the payment leg)
- ADR-2605231525 — no platform-held signing key (G5)
- ADR-2605215000 — Murakumo-only inference (G4)
- ADR-2605192115 — donation-only / SBT↔SBT carve-out / non-profit領収書 path (§1.3 boundary)
- ADR-2605222330 — etzhayyim.com substrate transition (manual CF Registrar registration, 2026-05-15)
- ADR-2605211757 — DNS cutover runbook (zone records / did:web publisher pattern)
- ADR-2606013800 — actor profile + dynamic did.json (apex Worker issues did:web)
- ADR-2606031600 — ipaddress/yabai → kotoba EAVT (RDAP/WHOIS collection prior art)
- ADR-2605181100 — `com.etzhayyim.encrypted.*` envelope (G9 registrant PII)
