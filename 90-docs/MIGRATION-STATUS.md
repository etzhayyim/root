# etzhayyim/root — on-chain migration status (audit 2026-06-02)

Substrate posture per ADR-2605172000 (RW-free) + ADR-2606011400 (on-chain-only).
This is a point-in-time classification of all `60-apps/` projects, resolving the
previously-opaque status of the ~312 apps that carry no `MIGRATION-TODO.md`.

**Total apps: 391.** Each is bucketed by: has a clean `rw-free/` reference impl?
has a `MIGRATION-TODO.md`? still imports prohibited substrate
(`createKyselyDb` / `kysely` / RisingWave / `HYPERDRIVE` / `stripe` / `viem` /
`@atproto/api`) in its non-`rw-free` source?

| Bucket | Count | Meaning |
|--------|------:|---------|
| **A — DONE** | 61 | has a `rw-free/` on-chain reference impl |
| **B — CLEAN** | 208 | no `rw-free`, no TODO, no prohibited imports — compliant or thin stub |
| **C — NEEDS-CODEMOD** | 41 | still imports prohibited substrate → the real active backlog |
| **D — TODO-PENDING** | 79 | has `MIGRATION-TODO.md` (seed copied, codemod pending) |
| **V — VENDOR-RESIDENT** | 1 | judged correctly gftd-resident (regulated-infra axis) — no migration |

**Real remaining scope ≈ 120 apps** (C + D = 41 + 79; the 8 Tier-2 commerce apps
celler/eigyo/minpaku/omise/real-estate/shopping/supplychain/yadoya already had
rw-free impls and are reconciled into Bucket A). Buckets A + B (260) need no
further substrate work. The open-* commodity-data backlog is **fully cleared** —
every open-* app now has an rw-free impl. The loop now proceeds over the
remaining C/D apps with a per-app judgment gate (etzhayyim-front vs
vendor-resident, per the Consensys pattern + 3-axis OR-test).

> **Nuance**: an app can be in A *and* C — the `rw-free/` package is the clean
> etzhayyim-compliant reimplementation, but the project's original (pre-migration)
> `src/` may still carry RW/Stripe code that a later cleanup removes. e.g. `cpc`,
> `common-crawl`, `sanctions`, `saiban`, `coverage`, `kami`. For these the
> on-chain path exists; the legacy src is residual cleanup, not a missing impl.
> (`auth` was an example here previously but is now Bucket V — vendor-resident,
> no on-chain path; see below.)

## Bucket A — DONE (61, has rw-free/)

anime, animeka (mixed split — catalog front), blockchain, bpmn, bunken,
celler, common-crawl, cpc, crowdfunding, dns, ec, eigyo,
gameka, gtin, hakkou, hanrei, houbun, houki, houshi, ipaddress, isbn, isin,
issn, ki, kiyo, koke, legal-corpus, manga, maps, minpaku, narou, ndc, nist,
ocel, okaimono, omise, open-airplane, open-apqc, open-banking, open-cofog,
open-denki, open-gas, open-isco, open-isic, open-jpn-gov, open-network,
open-ports, open-power, open-rail, open-swift, open-unispsc, open-water,
otakiage, real-estate, sbom, shopping, supplychain, threads,
threat-intelligence, tsukuru, yadoya, yoro

(51 incl. `ec`/`crowdfunding` (2026-06-02) and the 8 open-* commodity-data apps
— open-airplane/cofog/gas/network/ports/power/rail/swift — migrated through the
one-at-a-time loop; superset of the original audit's 43.)

## Bucket V — CONFIRMED VENDOR-RESIDENT (1)

Apps judged (per-app gate) to have a **regulated-infra primary function** that
correctly stays gftd vendor under the Consensys boundary + 3-axis OR-test. These
are NOT migrated; the etzhayyim front consumes them via consent-capability.

- **auth** — axis: **Custody** (+ identity-assurance liability). Primary function
  is credential / private-key / session custody: `vertex_gftd_auth_*` (WebAuthn
  passkey credentials, account secrets) in D1 AUTH_DB, `vertex_gftd_key_*`
  (private keys, revocation) in D1 KEYS_DB, session JWT issuance. Operator-
  producible secrets ⇒ stays gftd. NOTE: the *decentralized-identity primitives*
  it also touches — did:web / did:plc issuance + `vertex_gftd_identity` public
  governance — are etzhayyim-exclusive per ADR-2605211950 and tracked as separate
  relocate targets in `/CLAUDE.md` migrations, not as an rw-free registry here.

## Bucket C — NEEDS-CODEMOD (41) — active backlog

Import vectors: `createKyselyDb` 29 · `HYPERDRIVE` 23 · RisingWave 18 ·
`kysely` 8 · `stripe` 4 · `@atproto/api` 0 · `viem` 0.

bim, briefing, cad, cloudflare-browser-render,
common-crawl (RW, legacy src), coverage, cowork, cpc (legacy src),
crypto-asset-freeze, cyber-drill (stripe), deai (RW), dougaka (RW), editor,
email-service-adapter (stripe), fax, gov, hc, **hospitality (RW in
scripts/sync-roster.ts)**, intel, itonami, jp-fiscal, jukyu (RW), kami,
kenkyusha (RW), kyber-qzzg06nh, legal-entity (RW), llm (RW), manimani,
open-kyber (stripe+RW),
open-ossekai, open-ot (RW), open-patent (RW),
os-messaging, patent (RW), pptx,
public-kafun-bokumetsu, saiban, sanctions, seibutsu, shigotoba, shinka,
shinkansen, tenso, toshi-kozan, voxelforge, watashi, webmk, webya, xlsx,
yorishiro, yukkuri

## Bucket D — TODO-PENDING (79, MIGRATION-TODO.md)

**TRANSFORM-pending (49)**: 6ir, accounts, aima, air-book, air-cargo, air-crew,
air-dcs, air-ffp, air-mro, air-ops, air-sched, air-sms, air-yield, analytics,
business-edge, business-person, collector,
completer, coverage, cowork, credits, fleamarket, flight-offer, ge, gftdcojp,
harai, hrse, hub, kaikei, keiei, ops, resource-flow, resource-planner,
resource-provider, robot, scheduler, shiharai, tia, web4, webpage, wire, worlds,
yabai, yatabase

**Ad-pixel codemod complete (26)**: animeka*, briefing*, communicator,
email-service-adapter*, external-service-adapter, facebook, fax*,
game-play-uploader, github, gmail, live, mailer, mangaka, media-gamers, meet,
meeting-recorder, messenger, microsoft, microsoft-graph, news, newsletter,
ongakuka, outreach, phone, recap, ses, society6, x
(\* also in Bucket C — ad-pixel done but substrate codemod incomplete)

**Substrate-boundary violation flagged (6)**: cloudflare-browser-render, insatsu,
open-jpn-mynumber, playwright, repository, site

## In-progress (2026-06-02)

- **Tier-2 commerce** (okaimono/ec on-chain pattern): `crowdfunding` + `ec` DONE
  (in A). Remaining 8 (`shopping` `omise` `minpaku` `yadoya` `hospitality`
  `real-estate` `eigyo` `supplychain` `celler`) being shipped one-by-one.
- **hospitality** is the only Tier-2 in Bucket C (RW in `scripts/sync-roster.ts`);
  its rw-free build also strips that legacy script reference.

## Recommended sequencing

1. **Tier-2 commerce** (10) — okaimono/ec pattern; in progress.
2. **Bucket C open-* infra standards** (open-airplane/cofog/gas/network/ports/
   power/rail/swift/water etc.) — registry pattern like the Tier-1 standards
   (createKyselyDb → AT PDS), high-volume but mechanical.
3. **Bucket C RW data apps** (patent/jukyu/legal-entity/llm/deai/kenkyusha/...) —
   re-platform to kotoba datomic / AT PDS per ADR-2606011400 amendment 2026-06-01b.
4. **Bucket D non-commerce TODO seeds** (accounts/kaikei/keiei/hrse/...) — apply
   the 3-axis function-split per app (some are regulated → vendor function).
5. **Residual legacy-src cleanup** for Bucket A∩C apps (cpc/common-crawl/...).

Must-stay-vendor (NOT in scope, regulated): gambling / adult / payment-SaaS /
weapons-surveillance-finance / vendor cores — per vendor deps.toml
`phase5-vendor-deletion-248-projects-2026-05-23`.
