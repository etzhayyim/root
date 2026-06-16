---
id: adr-2606162355-torifune-subaru-transparent-space-access-and-connectivity-commons
title: "ADR-2606162355: torifune 鳥船 + subaru 昴 — Transparent open space-access + connectivity-commons wave (the SpaceX/Starlink charter-clean inversion)"
status: proposed
doc_type: adr
topic: torifune-subaru-space-access-and-connectivity-commons
authoritative: true
last_verified: 2026-06-16
priority: 5.5
axis: architecture
weight: 0.55
priority_note: "Closes the space-ACCESS + orbital-CONNECTIVITY gap left open by hoshimori (which only OBSERVES orbit). torifune = the launch-vehicle builder (船大工 of the sky); subaru = the Transparent connectivity-commons constellation (Starlink inversion). Both gated HARD on §1.12 Transparent-Force + no-weapon + no-surveillance."
authoritative_for:
  - torifune 鳥船 actor (zero-net-carbon open launch-vehicle manufacturing + Transparent space access)
  - subaru 昴 actor (Transparent connectivity-commons satellite constellation; Starlink/OneWeb inversion)
  - launch-vehicle-ontology
  - constellation-ontology
depends_on:
  - 2605192100
  - 2605192330
  - 2605302357
  - 2606073600
  - 2606013400
  - 2606032130
  - 2606051600
  - 2605181100
  - 2605312345
  - 2605215000
related:
  - 2606012600
  - 2606041827
  - 2605261300
  - 2606062100
  - 2606082400
supersedes: []
superseded_by: []
---

# ADR-2606162355: torifune 鳥船 + subaru 昴 — Transparent open space-access + connectivity-commons wave

**Status**: proposed (R0 design draft — Council/Lv7+ attestation required before any live leg; see §7)
**Date**: 2026-06-16
**Deciders**: Jun Kawasaki

# Context

The roster has a structural asymmetry in the off-Earth domain. `hoshimori 星守`
(ADR-2606073600) **observes** orbit — it mirrors public catalogs of regimes / operators /
hazards / services and routes congestion to stewardship — but it operates no spacecraft and
launches nothing (its G8 is "observation-only"). Meanwhile the Charter's land-sovereignty
claim **already extends to orbit** (ADR-2605192330), and §1.16 Social Security for Humanity
(ADR-2605302357) makes **connectivity** a candidate in-kind entitlement, yet there is **no
actor that accesses space** and **no actor that provides orbital connectivity**. The only
SpaceX/Starlink-shaped entries in the tree are `-compat` data adapters
(`spacex_telemetry-compat`, `starlink-compat`, `oneweb-compat`, `rocket_lab-compat`,
`blue_origin_api-compat`, …) — read-only interop mirrors that *do* nothing.

This is the deliberately-deferred gap, because **space access and orbital connectivity are the
single most dual-use capabilities the corp could build**:

- A reusable launch vehicle is, modulo payload, a ballistic missile. Ascent GNC that can fly a
  payload to orbit can fly a depressed/suborbital strike trajectory.
- A global low-latency comms constellation is, modulo intent, a military C2 + ISR backbone
  (cf. Starshield). A connectivity network that can route packets can do deep-packet
  inspection, user-geolocation-as-product, and targeting relay.

The Charter does not forbid these capabilities — it forbids the **proprietary / covert /
asymmetric** forms of them. §1.12 permits **Transparent Religious Force** *only* under three
simultaneous conditions: **open-source + on-chain 監視 + 1 SBT = 1 vote**. Charter Rider v3.1
§2(a) reframes the weapons line as *transparent-defensive-force-permitted, offensive-weapon
unrepresentable*; §2(c) (ADR-2606082400) reframes surveillance onto the **reciprocity axis**
(monetized OR asymmetric watching prohibited; reciprocal/symmetric 相互監視 affirmed; privacy
preserved by **encryption**, not forgetting). The lineage already has the build-pattern
(`funadaiku 船大工` zero-emission cargo-ship building, ADR-2606013400; `sarutahiko` trucks;
`giemon` factory 4D-BIM) and the labor-liberation dividend coupling (ADR-2606032130).

So the gap is closable **iff** the two new actors are built as the *inversions* of SpaceX and
Starlink: open-design, zero-net-carbon, weapon-unrepresentable, surveillance-unrepresentable,
debris-responsible, cash≡0, Council-gated for every live leg.

# Decision

Create a two-actor wave (siblings, tightly coupled: torifune **builds + launches** the bus
that subaru **operates**; hoshimori **observes** the result; together = build → fly → connect →
steward). Both are Tier-B, R0 **design-only**.

## 1. torifune 鳥船 — zero-net-carbon open launch-vehicle manufacturing + Transparent space access

The "船大工 of the sky" — the `funadaiku`/`sarutahiko` build-pattern pointed at space access.
torifune designs and (Council-gated) manufactures a **reusable, open-design launch vehicle**
(the **Ama 天 class**, two-stage hydrolox), runs the **plant** (grand-block / 4D-BIM, the
`giemon-factory` + `funadaiku` pattern) and the **ascent + staging + recovery GNC simulation**
on `kami-genesis` (the Featherstone rigid-body engine `funadaiku` ShipHydro and `niyaku`
Cartpole already use, clean-room `isaacsim.core.api`, no NVIDIA binary). The name is **天鳥船**
(Ame-no-Torifune) — the Shinto heavenly bird-boat: the vessel that flies to heaven.

**Constitutional gates** (full text in `20-actors/torifune/CLAUDE.md`):

- **G1 — civilian launch ONLY, NEVER a weapon-delivery / ballistic-strike vehicle** (the
  defining, load-bearing inversion). Weaponizable flight profiles — depressed/suborbital-strike
  trajectories, MIRV/PBV deployment buses, kinetic re-entry-vehicle delivery, fractional-orbital
  bombardment — are **structurally unrepresentable** in the GNC/sim (the trajectory class enum
  has no strike member; the payload class enum has no munition/kinetic member). Payloads are
  restricted to civilian classes (connectivity / EO-at-hoshimori-posture / science / crewed /
  cargo). A dedicated test asserts no strike-trajectory / munition-payload attribute exists
  (Charter §1.12 + Rider §2(a)).
- **G2 — zero-net-carbon propellant only.** Primary = green-H₂ hydrolox (LH₂/LOX from
  renewable electrolysis); permitted alternative = `kamado`-synthetic methalox at net≤0
  closed-carbon. Fossil-derived and toxic-hypergolic (UDMH/N₂O₄) propellants are
  discouraged/representable-only-as-disfavored; carbon-balance is **measured** (Rider §2(d)),
  never assumed.
- **G3 — open-design + dividend-coupled.** Open-source vehicle + GNC + plant (the robotics-actor
  default); space-access labor that is automated frees workers → Displacement Dividend
  (ADR-2606032130).
- **G4 — Transparent space access.** Open-source + on-chain flight/ops log + 1 SBT = 1 vote
  (§1.12). Never a covert / proprietary / state-military-aligned launch arm.
- **G5 — debris-responsibility (couples hoshimori).** Every mission carries a mandatory disposal
  / deorbit plan; no intentional debris generation; stage recovery preferred; the plan is an
  input to `hoshimori` stewardship — torifune may not create the congestion hoshimori routes
  around.
- **G6 — no-server-key.** The simulation is dry-run; actual launch operation is Council +
  operator-DID gated (you do not fly a rocket from a CF Worker). R0 ships sim + plant model +
  ontology only.
- **G7 — Murakumo-only narration** (ADR-2605215000).
- **G8 — sourcing honesty.** Every record `:authoritative | :representative`; sim numbers are
  representative engineering estimates, never measured flight data, until a Council-gated flight
  campaign exists.

## 2. subaru 昴 — Transparent connectivity-commons satellite constellation (Starlink/OneWeb inversion)

The charter-clean inversion of Starlink/OneWeb: a **connectivity COMMONS**, not a subscription
ISP. The name is **昴** (Subaru = the Pleiades star cluster; verb root すばる = "to gather / to
unite") — a constellation of satellites that *unites/connects*. subaru is the payload
`torifune` launches, the footprint `hoshimori` observes for stewardship, the orbital sibling of
`watatsuna` (submarine cable) and `tsutae` (handheld comms ground terminal), using `noroshi`
(光電融合 photonics) for inter-satellite + ground links. Connectivity is delivered as **§1.16
Social Security in-kind** (ADR-2605302357) — to the unconnected, to disaster zones, covenantal-
universal — **cash≡0, no ads, no subscription, no surveillance**.

Unlike hoshimori, subaru **operates spacecraft** — so its gates *invert* hoshimori's
observation-only posture into an operate-but-only-Transparently posture.

**Constitutional gates** (full text in `20-actors/subaru/CLAUDE.md`):

- **G1 — connectivity COMMONS, NEVER a surveillance / targeting / military-C2 platform** (the
  defining inversion). No deep-packet inspection; no traffic-content inspection; no
  user-geolocation-as-product; no ISR / targeting relay; military-exclusive C2 and
  jamming-as-weapon are **unrepresentable** (§1.12 + Rider §2(a),(c)). A dedicated test asserts
  no DPI / user-location-product / targeting-relay attribute exists.
- **G2 — no person-tracking; reciprocal-symmetric only (Rider §2(c) v3.1).** Subscriber content
  is end-to-end encrypted via `com.etzhayyim.encrypted.*` (ADR-2605181100); the constellation
  routes ciphertext it cannot read; no traffic-metadata retention-as-product. Privacy by
  encryption, not by a metadata graph.
- **G3 — non-profit / no-ads / cash≡0.** Connectivity is §1.16 in-kind social security
  (covenantal-universal, conversion-gated for Level-0 entitlement); external = donation /
  in-kind only; the SBT↔SBT internal carve-out (ADR-2605192115) covers internal use. NO
  subscription, NO advertising, NO data-as-payment model.
- **G4 — Transparent constellation.** Open-source bus + protocol + on-chain ops log + 1 SBT =
  1 vote (§1.12). Never a covert / proprietary constellation.
- **G5 — orbital stewardship (couples hoshimori + torifune G5).** Low-deorbit-debt orbit +
  mandatory disposal plan + **night-sky brightness mitigation** (darksat — the astronomy /
  Wellbecoming §1.13 night-sky commons); no new debris; subaru's footprint is an input to
  hoshimori's congestion integral, and subaru must reduce, not add to, it.
- **G6 — spectrum / coordination honesty.** ITU + national spectrum coordination is DISCLOSED
  and respected (non-adjudicating, N3); no harmful interference; no unlicensed/covert band use.
- **G7 — Murakumo-only narration** (ADR-2605215000).
- **G8 — no-server-key; live ops Council-gated.** R0 = link-budget + coverage + constellation-
  design sim + ontology only; live constellation operation is Council + operator-DID gated.

## 3. launch-vehicle-ontology + constellation-ontology (kotoba Datom log)

- `00-contracts/schemas/launch-vehicle-ontology.kotoba.edn` — nodes (`:vehicle`/`:stage`/
  `:engine`/`:propellant`/`:plant-cell`/`:mission`/`:payload`/`:trajectory`/`:disposal-plan`);
  縁 (`:powers`/`:stages-to`/`:fuels`/`:builds`/`:lofts`/`:disposes`) carrying engineering
  attributes; **the trajectory node's `:traj/class` enum admits only civilian profiles** (ascent
  / orbit-insertion / rendezvous / deorbit) — **no strike/depressed/FOBS member exists** (G1 by
  construction); the payload `:payload/class` enum has **no munition/kinetic member** (G1).
- `00-contracts/schemas/constellation-ontology.kotoba.edn` — nodes (`:constellation`/`:bus`/
  `:shell`/`:link`/`:ground-station`/`:service-area`/`:entitlement`/`:disposal-plan`); 縁
  (`:occupies`/`:relays`/`:serves`/`:coordinates-spectrum`/`:disposes`); **there is no
  `:link/inspect` / `:user/location` / `:relay/targeting` attribute in the schema** (G1/G2 by
  construction); service is keyed to `:service-area` (aggregate region), never to a tracked
  person.
- Both project to canonical **EAVT Datoms** `[e a v tx op]` (ADR-2605312345) via
  `methods/datom_emit.py`: ground nodes/edges durable (`:add`); derived readouts (coverage %,
  link budget margin, deorbit-debt, carbon balance) flagged `:bond/is-transient` (computed on
  read, never persisted).

## 4. kotoba pywasm actor design

Both actors follow the established posture: pure-stdlib (no numpy) methods → componentize-py
WASM Component, browser-local (ameno) / mesh (e7m-wasm-runner), no-server-key. A read-only,
content-addressed, dry-run sim component **cannot** fly a rocket or operate a constellation —
which is exactly the correct posture for G1/G6/G8. WIT world + build/verify + trust model in
each actor's `wasm/README.md` (R1).

## 5. R0 + R1 deliverables (this ADR — all green, still pre-live)

Both R0 (design) and R1 (offline sim) landed together; neither ships any **live capability**
(every live leg stays Council + operator-DID gated, G6/G8).

**R0 — design**:
- ADR (this file)
- `20-actors/torifune/` and `20-actors/subaru/`: `manifest.jsonld` + `CLAUDE.md`
- `00-contracts/schemas/launch-vehicle-ontology.kotoba.edn` +
  `constellation-ontology.kotoba.edn`

**R1 — pure-stdlib offline sim (no numpy, kotoba-pywasm-ready)**:
- torifune: `methods/ascent_sim.py` (staged Tsiolkovsky Δv + G1 `check_g1`),
  `carbon_balance.py` (G2 net-carbon), `disposal_plan.py` (G5 mandatory-disposal, refuses a
  mission without one), `datom_emit.py` (EAVT); `data/seed-ama-vehicle.kotoba.edn` (18 nodes /
  13 縁); `tests/test_torifune.py` — **7 green** incl. `test_g1_no_strike_profile` (a
  depressed-strike trajectory + a munition payload are both REFUSED). The Ama-class seed shows
  +3,359 m/s Δv margin to LEO, net 0 kgCO₂e (hydrolox), deorbit-debt 0.
- subaru: `methods/link_budget.py` (per-link margin + G1/G3 `check_g1`), `coverage.py` (§1.16
  reach), `stewardship.py` (G5 disposal + darksat, refuses an undisposed occupied shell),
  `datom_emit.py` (EAVT); `data/seed-constellation.kotoba.edn` (15 nodes / 12 縁);
  `tests/test_subaru.py` — **8 green** incl. `test_g1_no_surveillance_relay` (a DPI link, a
  user-location attribute, and a subscription entitlement are all REFUSED). All links close;
  §1.16 reach counts only unconnected/disaster areas; urban baseline excluded.

**R2+ (separate PRs, gated)**: `wasm/README.md` + componentize-py build, `.cljc` port (the
ADR-2606131300 corpus arc), live launch/ops legs (Council + operator-DID).

## 6. Lineage

```
torifune 鳥船  builds + (gated) launches  ──▶  subaru 昴  operates the constellation
     │  (船大工-of-the-sky: funadaiku/sarutahiko/giemon pattern)        │
     │  zero-net-carbon · weapon-unrepresentable                       │  connectivity COMMENS · §1.16 in-kind
     └────────────── debris-responsibility (G5) ──────────────────────┘
                                   │
                                   ▼
                           hoshimori 星守  observes orbit → stewardship (no-targeting)
```

Ground siblings: `watatsuna` (submarine cable), `tsutae` (handheld terminal), `noroshi`
(photonics links), `watari` (live position KG). subaru is the orbital member of the
connectivity family; together with hoshimori the corp now **builds → flies → connects →
stewards** off-Earth, every leg Transparent and gated.

# Consequences

**Positive.** The off-Earth domain becomes *active*, not merely observed: the orbital land-
sovereignty claim (ADR-2605192330) gets a launch + connectivity substrate, and §1.16 Social
Security gains an in-kind connectivity rail for the unconnected and for disaster zones. The
two-actor wave demonstrates that the most dual-use capabilities in the roster *can* be expressed
charter-cleanly — by making the prohibited mode (weapon, surveillance, covert, for-profit)
structurally unrepresentable rather than merely policy-banned.

**Costs / risks.** (1) G1 is load-bearing twice over — torifune must never gain a strike-
trajectory/munition-payload attribute, subaru must never gain a DPI/user-location/targeting
attribute; the schemas omit them and R1 CI must assert their absence. (2) Real space access is
capital-, regulatory-, and safety-heavy; R0 is honestly design-only and every live leg is
Council + operator gated (no-server-key). (3) Propellant carbon-balance and debris-debt are
real obligations, not slogans — G2/G5 require measurement, and torifune/subaru are coupled to
hoshimori's stewardship integral so the corp cannot launch into the congestion it elsewhere
routes around. (4) Spectrum and launch licensing are sovereign functions the corp routes
*through* transparently (§1.12 parallel-substrate), not around — G6 keeps coordination honest.

# Alternatives Considered

- **Fold launch + connectivity into hoshimori.** Rejected: hoshimori is constitutionally
  observation-only (its G8); making it operate spacecraft would destroy the no-targeting posture
  that makes the orbital mirror safe. Build/operate must be *separate* actors with *inverted*
  gates.
- **A single "space" actor doing both build and operate.** Rejected: launch (manufacturing,
  funadaiku-pattern) and connectivity (operation, §1.16 service) have different ontologies, gate
  sets, and dividend couplings; the funadaiku (builds) ↔ niyaku (operates) precedent argues for
  two siblings.
- **Skip launch; buy rides on `-compat` providers.** Considered and left open as the *interim*
  path (the `rocket_lab-compat` / `spacex_telemetry-compat` adapters already exist); torifune is
  the charter-preferred long-run substrate (open-design + zero-net-carbon + dividend-coupled),
  but nothing here forbids gated interim use of external launch while torifune matures.
- **A subscription/for-profit connectivity ISP (actual Starlink shape).** Rejected outright:
  ads + subscription + data-as-payment + asymmetric surveillance violate constitutional
  invariants (non-profit-only, no-ads, Rider §2(c)). subaru is cash≡0 §1.16 in-kind by
  construction.
- **Defer the whole domain.** Rejected: the gap is real (active off-Earth) and the design can be
  expressed safely now at R0; deferring leaves the orbital-sovereignty claim without a substrate.

# References

- `20-actors/torifune/` · `20-actors/subaru/` — the two actors (manifest, CLAUDE.md; methods/
  tests/seed/wasm = R1)
- `00-contracts/schemas/launch-vehicle-ontology.kotoba.edn` · `constellation-ontology.kotoba.edn`
- ADR-2605192100 (Mission Charter — §1.12 Transparent Force, §1.13 Wellbecoming, non-profit-only)
- ADR-2605192330 (extended land sovereignty — ocean/river/air/**orbit**)
- ADR-2605302357 (Social Security for Humanity — §1.16 in-kind, covenantal-universal)
- ADR-2606073600 (hoshimori — orbital stewardship mirror; the observe sibling)
- ADR-2606013400 (funadaiku — zero-emission shipbuilding; the build-pattern precedent)
- ADR-2606032130 (Displacement Dividend — robotics-actor labor-liberation coupling)
- ADR-2606051600 (noroshi — 光電融合 photonics comm links)
- ADR-2605181100 (com.etzhayyim.encrypted — E2E confidentiality)
- ADR-2605312345 (kotoba Datom = first-class canonical state)
- ADR-2605215000 (Murakumo-only inference)
- ADR-2606062100 / 2606082400 (Charter Rider v3.0/v3.1 — §2(a) force, §2(c) reciprocity axis)
- related: ADR-2606012600 (watatsuna), 2606041827 (watari), 2605261300 (tsutae)
