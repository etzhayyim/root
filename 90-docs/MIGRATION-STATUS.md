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
| **A — DONE** | 43 | has a `rw-free/` on-chain reference impl |
| **B — CLEAN** | 208 | no `rw-free`, no TODO, no prohibited imports — compliant or thin stub |
| **C — NEEDS-CODEMOD** | 52 | still imports prohibited substrate → the real active backlog |
| **D — TODO-PENDING** | 88 | has `MIGRATION-TODO.md` (seed copied, codemod pending) |

**Real remaining scope ≈ 140 apps** (C + D). Buckets A + B (251) need no further
substrate work.

> **Nuance**: an app can be in A *and* C — the `rw-free/` package is the clean
> etzhayyim-compliant reimplementation, but the project's original (pre-migration)
> `src/` may still carry RW/Stripe code that a later cleanup removes. e.g. `cpc`,
> `common-crawl`, `sanctions`, `saiban`, `auth`, `coverage`, `kami`. For these the
> on-chain path exists; the legacy src is residual cleanup, not a missing impl.

## Bucket A — DONE (43, has rw-free/)

anime, blockchain, bpmn, bunken, common-crawl, cpc, crowdfunding, dns, ec,
gameka, gtin, hakkou, hanrei, houbun, houki, houshi, ipaddress, isbn, isin,
issn, ki, kiyo, koke, legal-corpus, manga, maps, narou, ndc, nist, ocel,
okaimono, open-apqc, open-banking, open-denki, open-isco, open-isic,
open-jpn-gov, open-unispsc, otakiage, sbom, threads, threat-intelligence,
tsukuru, yoro

(43 incl. `ec`/`crowdfunding` landed 2026-06-02; this list is auto-superset of
the audit's 43 — `ec` was merged just after the scan.)

## Bucket C — NEEDS-CODEMOD (52) — active backlog

Import vectors: `createKyselyDb` 29 · `HYPERDRIVE` 23 · RisingWave 18 ·
`kysely` 8 · `stripe` 4 · `@atproto/api` 0 · `viem` 0.

animeka (RW), auth (HYPERDRIVE), bim, briefing, cad, cloudflare-browser-render,
common-crawl (RW, legacy src), coverage, cowork, cpc (legacy src),
crypto-asset-freeze, cyber-drill (stripe), deai (RW), dougaka (RW), editor,
email-service-adapter (stripe), fax, gov, hc, **hospitality (RW in
scripts/sync-roster.ts)**, intel, itonami, jp-fiscal, jukyu (RW), kami,
kenkyusha (RW), kyber-qzzg06nh, legal-entity (RW), llm (RW), manimani,
open-airplane, open-cofog, open-gas, open-kyber (stripe+RW), open-network,
open-ossekai, open-ot (RW), open-patent (RW), open-ports, open-power, open-rail,
open-swift, open-water, os-messaging, patent (RW), pptx,
public-kafun-bokumetsu, saiban, sanctions, seibutsu, shigotoba, shinka,
shinkansen, tenso, toshi-kozan, voxelforge, watashi, webmk, webya, xlsx,
yorishiro, yukkuri

## Bucket D — TODO-PENDING (88, MIGRATION-TODO.md)

**TRANSFORM-pending (58)**: 6ir, accounts, aima, air-book, air-cargo, air-crew,
air-dcs, air-ffp, air-mro, air-ops, air-sched, air-sms, air-yield, analytics,
auth, business-edge, business-person, **celler, eigyo, minpaku, omise,
real-estate, shopping, supplychain, yadoya** (Tier-2 commerce), collector,
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
