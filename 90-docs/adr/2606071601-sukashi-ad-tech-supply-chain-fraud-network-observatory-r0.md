---
id: adr-2606071600
renumbered_from: "2606071600"
title: "ADR-2606071601: 透かし (sukashi) — Ad-Tech Supply-Chain + Delivery-Infra + Fraud-Network Observatory Tier-B Actor R0"
status: proposed
doc_type: adr
topic: sukashi-ad-tech-supply-chain-fraud-network
authoritative: true
last_verified: 2026-06-07
priority: 6.0
axis: architecture
weight: 0.60
priority_note: "Ad-tech-supply-chain + delivery-infra + fraud-network sibling of akashi 証 (ad-library disclosure); first kotoba KG over the programmatic ad-tech supply chain (ads.txt/sellers.json) + serving infrastructure + scam-ad networks, framed as a fraud-protection observatory that preserves the Charter 広告排除 invariant"
authoritative_for:
  - sukashi actor charter (R0)
  - ad-tech supply-chain + fraud-network knowledge-graph constitutional gates G1..G13
  - ad-supply-chain-ontology.kotoba.edn vocabulary
related:
  - adr-2606022300-akashi-public-ad-disclosure-kotoba-actor-r0
  - adr-2606031600-ipaddress-yabai-kotoba-eavt-refactor-active-collection
  - adr-2605301400-tadori-onchain-tx-tracing-actor
  - adr-2605312500-kurashimori-consumer-protection-concierge
  - adr-2606060900-tasuke-cybercrime-victim-support-membrane
  - adr-2605301600-danjo-public-accountability-oversight-tier-b-actor-r0
  - adr-2606022000-kabuto-public-company-intel-supply-chain
  - adr-2606013600-kotoba-wasm-browser-node
supersedes: []
superseded_by: []
depends_on:
  - ADR-2606022300 (akashi — ad-library disclosure sibling + the malakEvidenceCandidate bridge sukashi hands fraud evidence to)
  - ADR-2606031600 (ipaddress/yabai — the ip-network + passive-dns-cti ontologies sukashi reuses for delivery infra)
  - ADR-2605301400 (tadori — authorized IP/ASN/WHOIS/passive-DNS substrate)
  - ADR-2605312500 (kurashimori — consumer-protection routing target)
  - ADR-2606060900 (tasuke — cybercrime-victim-support routing target)
  - ADR-2605301600 (danjo — non-adjudicating public-accountability boundary + routing target)
  - ADR-2605262130 (kotoba storage substrate)
  - ADR-2605312345 (kotoba Datom log = first-class canonical state)
  - ADR-2606013600 (kotoba-wasm browser node — the render target)
  - ADR-2606013800 (actor-profile SSoT + dynamic did.json — the registration path)
  - ADR-2605231525 (no-server-key signing capability boundary)
  - ADR-2605215000 (Murakumo-only inference)
  - ADR-2605192100 (Charter — 広告排除 invariant this actor must preserve)
---

# ADR-2606071601: 透かし (sukashi) — Ad-Tech Supply-Chain + Delivery-Infra + Fraud-Network Observatory Tier-B Actor R0

**Date**: 2026-06-07
**Status**: PROPOSED (R0 design-only; live full-web ingest + live posting + live malak handoff Council + operator gated)
**Deciders**: Jun Kawasaki (author), Council Lv6+ (ratify)

# Context

The founder asked to ingest ad-network ad-placement activity, build intel on **which companies /
organisations broadcast which messages**, visualize the **social-dependency / follow / supply-chain
graph**, identify **fraudulent ads and fraud actors**, and ingest the **delivery-source IP / DNS /
WHOIS / organisational status** of the serving infrastructure — all persisted in the kotoba Datom
log + IPFS, with autonomous maturity improvement on a `/loop`.

The monorepo already has **half** of this:

- `akashi` 証 (ADR-2606022300) observes platform **ad-LIBRARY disclosures** (Meta/X/Google/
  TikTok/LINE/EU-DSA). But akashi is **constitutionally bounded away** from exactly the rest of the
  ask: its ADR §Non-Goals states it is "NOT an ad network, auction exchange, DSP, SSP, or campaign
  manager", its **G9** forbids a commercial ad-intel product, and it ingests **landing URLs only**
  (no IP/DNS/WHOIS/ASN). The ad-tech **supply chain** (ads.txt/sellers.json), the **delivery
  infrastructure**, and **fraud-network detection** are out of akashi's scope by design.
- `tadori` 辿 + the `ipaddress`/`yabai` → kotoba refactor (ADR-2606031600) already provide the
  authorized **IP / ASN / WHOIS / passive-DNS** substrate as kotoba ontologies
  (`ip-network-ontology`, `passive-dns-cti-ontology`). The serving-infrastructure layer the founder
  asked for **already exists** and must be *reused*, not re-modelled.
- `kabuto` 兜 / `watatsuna` 綿津綱 / `tsumugi` 紡ぎ establish the intel-weaver pattern: a kotoba-
  native EAVT ontology + first-class edges + an aggregate-first analyzer + a self-contained viz,
  framed as a **resilience / transparency map, never a target-list**.
- the **kotoba-wasm browser node** (ADR-2606013600) renders `/actors` + `/search` client-side.
- `kurashimori` 暮らし守 (consumer protection), `tasuke` 助 (cybercrime-victim support), and
  `danjo` 弾正 (accountability) are the actors that should *act* on fraud findings.

What is missing is the actor that holds the **programmatic ad-tech supply chain + its serving
infrastructure + the scam-ad networks** as one knowledge graph and routes fraud findings to the
actors that act. **sukashi** 透かし fills that gap as the supply-chain + fraud sibling of akashi.

The hard constraint is the **Charter 広告排除 invariant** (ADR-2605192100): etzhayyim
constitutionally excludes advertising. An actor "about ads" is only admissible if it is an
**observatory OF advertising for fraud protection** — never an ad network, buying tool, targeting
tool, or commercial ad-intel terminal. The name 透かし (*watermark* / holding paper to the light)
is chosen deliberately: ads.txt + sellers.json are the ad-tech industry's own authenticity
watermark, and sukashi holds the supply chain up to the light to *see through* deceptive ads.

# Decision

## A. Actor definition

Create **sukashi** (透かし), DID `did:web:etzhayyim.com:actor:sukashi`, as a **Tier-B kotoba-native
ad-tech supply-chain + delivery-infra + fraud-network observatory** in **R0 design-only**. It is the
supply-chain + fraud sibling of akashi 証; it reuses tadori's `ip-network` + `passive-dns` ontologies
for the delivery layer and the shared `org.corp.*` id space for listed ad-tech firms; and it hands
fraud evidence to akashi's existing `com.etzhayyim.akashi.malakEvidenceCandidate` bridge rather than
running its own malak import.

## B. Vocabulary (`00-contracts/schemas/ad-supply-chain-ontology.kotoba.edn`)

- `:adtech/*` — an ad-tech entity (advertiser / agency / dsp / ad-exchange / ssp / ad-network /
  publisher / verification / data-broker / ad-server / cmp), reusing `org.corp.*` for listed firms
  (`:adtech/listed-org` → kabuto/tsumugi).
- `:adauth.edge/*` — **first-class authorization edge** parsed from the PUBLIC IAB files ads.txt /
  app-ads.txt (publisher → seller, `:direct`/`:reseller`) and sellers.json. The two-sided handshake:
  `declared` (in the publisher's ads.txt) + `confirmed` (in the seller's sellers.json). A
  `declared && !confirmed` edge is the **unauthorized / spoofed-inventory surface**.
- `:adcreative/*` — an observed creative (who broadcasts what message), linked to its advertiser
  and the network that served it.
- `:addelivery.edge/*` — **first-class edge** binding a creative / landing domain to the serving
  infrastructure: `:addelivery.edge/ip` → `:ip/id`, `:addelivery.edge/asn` → `:asn/id` (ip-network-
  ontology), `:addelivery.edge/landing-domain` → `:domain/id` (passive-dns), plus public WHOIS-org
  + registrar. **sukashi does not re-model the network layer** — these are refs into tadori's ontologies.
- `:adfraud.signal/*` — an evidence-bearing, **non-adjudicating** fraud signal (`kind`, `confidence`,
  `evidence-cid`, `routed-to`, `non-adjudicating const true`).
- derived (`:adsupply/*`, `:adfraud/*`) — unconfirmed-rate, seller fan-out, infra-concentration,
  scam-network clusters, category load. Computed by `analyze.py`, flagged `:derived`, never re-ingested.

## C. Cells

- `cell:sukashi.ingest` → `methods/ingest.py` — real ads.txt / sellers.json / WHOIS parsers →
  kotoba EAVT bridge, dedup-merged with the seed (seed wins). Offline default; live full-web crawl
  is **G7**-gated. WHOIS keeps the registrant **organisation** only (G9).
- `cell:sukashi.analyze` → `methods/analyze.py` (stdlib). authorization-handshake integrity
  (unconfirmed-rate) → account-id collision (domain-spoof surface) → delivery-infra concentration
  (ASN/registrar) → shared-infra scam-ad-network clustering → category load → routing tally.
  Aggregate-first, idempotent. Emits `out/intel-report.md` + `out/ad-fraud-clusters.kotoba.edn`.
- `cell:sukashi.transact` → `methods/transact.py` — kotoba `datomic.transact` save-path; dry-run
  default; live write needs operator JWT or CACAO (no platform-held key, ADR-2605231525). **G7**.
- `cell:sukashi.viz` → `viz/build_viz_data.py` — self-contained ad-tech supply-chain + fraud
  force-graph (browser-native via the kotoba-wasm node; inlined payload = offline data contract).
- `cell:sukashi.fraud-bridge` (design) — hands `:routed-to :akashi-malak` signals to akashi's
  `malakEvidenceCandidate` bridge (candidate-evidence only). **G11/G13**.

## D. Lexicons (`00-contracts/lexicons/com/etzhayyim/sukashi/`)

`com.etzhayyim.sukashi.{registerAdtech, registerAuthEdge, registerCreative, registerFraudSignal,
publishIntelReport, socialPost}`. `confidenceBp` is integer basis points (0..1000) to avoid floats
(mirrors kabuto's `criticalityBp`; satisfies the Lexicon-v1 no-float rule). `registerFraudSignal`
structurally pins G4 (non-adjudicating) + G13 (akashi malak handoff).

## E. Registration

Registered in `deps.toml` ([[adrs]]), `50-infra/etzhayyim-did-web/src/registry/infra-actors.ts`
(`INFRA_ACTORS.sukashi`), and the repo-root `CLAUDE.md` Tier-B actor roster → discoverable at
`etzhayyim.com/search` + `/actors` via the kotoba-wasm node.

## F. Constitutional gates (G1–G13)

See `20-actors/sukashi/CLAUDE.md` + `manifest.jsonld` for the canonical text. In brief:
**G1** public ad-tech data only; **G2** observatory-not-network (preserves 広告排除); **G3** aggregate-
first; **G4** no adjudication (signals routed, never verdicts; real firms carry no fraud signal);
**G5** sourcing honesty (every fraud signal `:synthesized`); **G6** Murakumo-only; **G7** outward-
gated ingest; **G8** no git-lfs; **G9** no personal PII (WHOIS = org only); **G10** browser-native
render; **G11** outward-gated publish; **G12** no-interaction / no-detection-evasion; **G13**
complements akashi (fraud evidence → akashi's malak bridge).

# Consequences

**Positive.**
- The missing "ad-tech supply chain → kotoba database" actor is explicitly named and bounded,
  completing the founder's ask that akashi was constitutionally unable to cover.
- It *reuses* tadori's IP/DNS/WHOIS substrate instead of re-modelling the network layer — one
  delivery-infra ontology, two lenses.
- Fraud findings flow to the actors that act (akashi-malak / kurashimori / tasuke / danjo) without
  sukashi ever adjudicating — the non-adjudication boundary is structural (`:non-adjudicating true`,
  fraud examples only on fictional entities, tested).
- The 広告排除 invariant is preserved: sukashi is meta-observation OF advertising for fraud
  protection, verified by the repo's `no-advertising` pre-commit gate passing on the whole actor.

**Costs / honest R0 caveats.**
- R0 ships a bounded illustrative seed — not exhaustive coverage. After the post-R0 maturity loop
  (10 iterations, see `MATURITY.md`) it stands at **74 ad-tech entities / 28 ads.txt-sellers.json
  authorization edges / 9 creatives / 4 delivery edges / 12 fraud signals (full 11-kind taxonomy) /
  18 `org.corp.*` cross-links**, **31 tests green**. Real firms + genuinely-public ads.txt/sellers.json
  facts are `:authoritative`/`:representative` and carry NO fraud signal; **every fraud example is
  `:synthesized` on a CLEARLY-FICTIONAL entity** (`.test`/`.example` + RFC-5737 doc IP ranges) so no
  real entity is implicated.
- Live full-web ads.txt/sellers.json/WHOIS crawl is the **R1** goal and is **G7** Council + operator
  gated; live kotoba write, live atproto post, and live akashi malak handoff are gated too.
- Confidence scores are bounded estimates, never findings of guilt.

**Post-R0 maturity loop (landed, agent-reachable — no gate flip).** A self-paced `/loop` advanced
deploy-readiness across 10 iterations, each test-pinned: (1) multi-signal fraud corroboration
(`:adfraud/cluster-corroboration`); (2) transact deploy-readiness assertions; (3) app-ads.txt / CTV
coverage (`:adauth.edge/app`); (4) the akashi `malakEvidenceCandidate` fraud-bridge (`fraud_bridge.py`,
candidate-only, validated vs akashi's real lexicon); (5) seller betweenness centrality
(`:adsupply/seller-betweenness`); (6) registrar / WHOIS-org fraud co-occurrence ranking; (7) seed →
69+ real ad-tech entities (full role taxonomy); (8) authorization graph → 28 edges; (9) full 11-kind
fraud archetype taxonomy (12 signals); (10) 18 listed-firm `org.corp.*` cross-links. Remaining R0.x:
reseller-depth, a Murakumo-narration design note, and a viz fraud-cluster highlight.

**R1 triggers.** Council attestation + operator gate flip unblocks: full-web public-file crawl →
`data/live/` (G8 gitignored), live RDAP/WHOIS + passive-DNS join via tadori, live kotoba write, live
atproto publish, and the live akashi malak handoff. The agent-reachable goal between now and then is
**deploy-readiness** — coverage + analysis depth + integration fixtures, tracked in `MATURITY.md`.

# Alternatives Considered

- **Extend akashi instead of a new actor** — rejected. akashi's ADR + 13 gates constitutionally
  bound it to platform ad-library disclosure and *against* ad-tech SaaS / DSP/SSP / network-layer
  data. Folding the supply-chain + delivery-infra + fraud-network scope into akashi would require
  weakening akashi's G9 and its Non-Goals, breaking a ratified charter. A sibling actor that hands
  evidence *to* akashi's malak bridge keeps both charters intact.
- **Re-model the IP/DNS/WHOIS layer inside sukashi** — rejected. tadori + ADR-2606031600 already own
  `ip-network-ontology` + `passive-dns-cti-ontology`; sukashi references them (`:ip`/`:asn`/`:domain`),
  avoiding a parallel substrate (substrate-boundary rule).
- **Score advertisers / publishers with a fraud verdict** — rejected (G4). sukashi emits evidence-
  bearing signals routed to actors that act; adjudication would cross the UPL/defamation boundary
  (sibling of danjo) and risk defaming real firms. Fraud examples therefore attach only to fictional
  entities, enforced in tests.
- **A general ad-intelligence / competitive-intel product** — rejected (G2 + Charter 広告排除 +
  Charter Rider §2(e) + akashi G9). sukashi is a fraud-protection observatory, never a buying /
  targeting / optimization / detection-evasion tool.

# Implementation update (2026-06-16) — the worldwide ACQUISITION crawler landed

R0 shipped the real parsers (`ingest.parse_ads_txt` / `parse_sellers_json` / `bridge_whois`), the
analyzer (`.cljc`), the kotoba Datom log + gated live transact, and the autonomous heartbeat — but
acquisition was limited to bridging a single local `--in` file. The crawler (the "全世界の広告情報
の取得" leg) was design-only. This update lands it:

- **`methods/crawl.py`** — walks a frontier of REAL publisher / SSP / exchange domains
  (`data/frontier-domains.edn`, 33 real domains) and FETCHES each one's PUBLIC IAB files
  (`/ads.txt`, `/app-ads.txt`, `/sellers.json`) + public RDAP, then feeds them through the existing
  real parsers → kotoba `:adtech` / `:adauth.edge` / `:addelivery.edge` rows. Only those four
  public paths are constructible (`urls_for`); the network leg is **INJECTED** (`fetcher=`), so the
  dry-run and the tests run with zero network. **G7**: a live crawl requires `SUKASHI_OPERATOR_GATE=1`
  + Council — otherwise `crawl()` is a dry-run that returns the URL plan and fetches nothing. **G2/G12**:
  GET-only, honest identifying UA, robots-respecting, no anti-bot bypass (unrepresentable). **G9**:
  RDAP keeps registrant ORG only. Resume-safe (`data/live/` gitignored; fresh-skip by ttl).
- **Proven live**: with the gate set, the crawler fetched `theguardian.com/ads.txt` (5,679 bytes, a
  real public file) and parsed **131** real ad-supply-chain rows. 9 crawler tests green (offline).
- **bb is the runner** (no `.sh`): `bb sukashi:crawl` (dry-run / `SUKASHI_OPERATOR_GATE=1` for live)
  + `bb test:sukashi` (python invariant/heartbeat/crawler + cljc analyzer); `run_tests.sh` removed.

**Honest boundary**: the *capability* for worldwide acquisition is now real and proven on a live
domain; the *full-world run* (the whole frontier, then the IAB Tech Lab / Common Crawl host-list
enumeration) is the Council gate-flip (`SUKASHI_OPERATOR_GATE=1`) — a human step, not done here. The
acquisition leg is `.py` (I/O-coupled, the ingest.py boundary per ADR-2606131800); the analyzer +
EDN reader are `.cljc`; canonical state is the kotoba Datom log.

# References

- `20-actors/sukashi/` — actor (manifest, CLAUDE.md, README, MATURITY, methods, viz, tests)
- `00-contracts/schemas/ad-supply-chain-ontology.kotoba.edn` — vocabulary
- `00-contracts/lexicons/com/etzhayyim/sukashi/` — lexicons
- ADR-2606022300 (akashi — ad-library disclosure sibling)
- ADR-2606031600 / ADR-2605301400 (tadori IP/DNS/WHOIS substrate reused for delivery infra)
- ADR-2605312500 (kurashimori) / ADR-2606060900 (tasuke) / ADR-2605301600 (danjo) — routing targets
- ADR-2606022000 (kabuto) / ADR-2606011800 (tsumugi) / ADR-2606012600 (watatsuna) — intel-weaver pattern
- ADR-2605192100 (Charter — 広告排除 invariant) · ADR-2605262130 / 2605312345 (kotoba substrate)
- IAB Tech Lab: ads.txt 1.1, app-ads.txt, sellers.json 1.0 (the public web standards ingested)
