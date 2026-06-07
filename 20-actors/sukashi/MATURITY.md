# sukashi 透かし — maturity ladder

> The self-paced `/loop` tracks this file. Each iteration should tick ≥1 box, grow real coverage,
> and keep `./run_tests.sh` green. ADR-2606071600. Live ingest/publish stay outward-gated (G7/G11)
> — the reachable goal for an agent is **deploy-readiness**, not a human gate flip.

## R0 — design + tested core (current)

- [x] Actor identity (manifest.jsonld, DID, glyph, role) + CLAUDE.md + README
- [x] Ontology `ad-supply-chain-ontology.kotoba.edn` (`:adtech`/`:adauth.edge`/`:adcreative`/`:addelivery.edge`/`:adfraud.signal` + derived)
- [x] Reuse (not re-model) ip-network + passive-dns ontologies for delivery infra
- [x] Bounded real seed (30 ad-tech entities / 8 auth edges / 4 creatives / 4 delivery / 6 fraud)
- [x] `ingest.py` real ads.txt / sellers.json / WHOIS parsers (offline default, G7-gated live)
- [x] `analyze.py` aggregate-first: unconfirmed-rate, account-id-collision, infra-concentration, scam-network clustering, category load, routing tally
- [x] `transact.py` kotoba `datomic.transact` save-path (dry-run default, no-server-key)
- [x] `viz/build_viz_data.py` self-contained force-graph (browser-native)
- [x] 6 `com.etzhayyim.sukashi.*` lexicons
- [x] 16 invariant + analyzer tests green (G2/G4/G5/G9 pinned in code)
- [x] Registered: deps.toml + INFRA_ACTORS + root CLAUDE.md Tier-B row

## R0.x — maturity loop (agent-reachable; no gate flip)

Coverage growth (each is a `/loop` increment):
- [x] seed → 60+ real ad-tech entities (add CTV/DOOH SSPs, mobile networks, retail-media networks) — 69 entities across all 10 roles (DSP/exchange/SSP/network/publisher/verification/data-broker/ad-server/cmp/advertiser); real firms :representative, no fraud signal; test_seed_coverage_breadth
- [ ] seed → 25+ real public ads.txt/sellers.json authorization edges (real publishers' public files)
- [x] add `:adauth.edge/app` (app-ads.txt / CTV) coverage + a parser test — ingest `--source appads --app <bundle>`; seed CTV publisher + a legit + a FICTIONAL spoof app-ads.txt edge; test_app_ads_txt_carries_bundle + test_ads_txt_parser + test_whois_bridge_drops_personal_pii
- [ ] seed → 12+ illustrative fraud archetypes (cloaking, typosquat-delivery, malvertising-redirect, sellers-json-mismatch) — all `:synthesized` on fictional entities
- [ ] cross-link listed ad-tech firms to `org.corp.*` (`:adtech/listed-org`) so kabuto/tsumugi share the entity

Analysis depth:
- [ ] add `:adsupply/reseller-depth` (longest reseller chain) to analyze.py + report + test
- [x] add an authorization-graph "follow/depends" centrality (seller betweenness) metric — `:adsupply/seller-betweenness` ∝ C(fan-in,2) = publisher-pairs a seller bridges; report section + derived datoms; test_seller_betweenness_centrality
- [x] add a fraud-cluster confidence-aggregation (multi-signal corroboration) metric — distinct fraud-KINDS per cluster weights network-rank (`:adfraud/cluster-corroboration`); test_cluster_multi_signal_corroboration
- [x] add per-registrar / per-WHOIS-org fraud co-occurrence ranking to the derived datoms — `:adsupply/registrar-cooccurrence` + `:adsupply/whois-cooccurrence` (fraud-flagged creatives sharing one registrar / registrant ORG, public WHOIS org-only G9); report section + derived datoms; test_registrar_and_whois_cooccurrence_ranking

Integration / readiness:
- [x] wire `cell:sukashi.fraud-bridge` shape to akashi's `malakEvidenceCandidate` (fixture round-trip, ≥2 source CIDs) — methods/fraud_bridge.py maps :akashi-malak-routed signals → akashi records (candidate-only, non-adjudicating, sourceCids = evidence + method-note); TestAkashiMalakBridge validates against akashi's real lexicon
- [x] add a `transact.py` empirical dry-run readiness check (schema attrs + datom count assertion in tests) — TestTransactReadiness: 51 schema attrs + 340 datoms from seed, dry-run offline returns 0 (G7 holds)
- [ ] add a Murakumo-narration design note (G6) for report summaries (no live call)
- [ ] viz: render the fraud-cluster as a highlighted sub-graph + a "routed-to" badge per signal

## R1 — gated (Council Lv6+ + operator; an agent cannot flip these)

- [ ] live full-web ads.txt / sellers.json crawl (`SUKASHI_OPERATOR_GATE`) → `data/live/` (G8 gitignored)
- [ ] live RDAP/WHOIS + passive-DNS join for real delivery infra (via tadori, registrant ORG only)
- [ ] live kotoba write (`--graph <CID>` + operator JWT/CACAO)
- [ ] live atproto publish (`SUKASHI_LIVE_POST` + Charter Rider §2 scan)
- [ ] live akashi malak handoff (akashi review gate)

## Honesty

R0 is bounded + illustrative; real firms carry no fraud signal; every fraud example is fictional +
`:synthesized`. "Cover the whole ad-tech web" is the R1 goal and is constitutionally outward-gated.
The maturity loop raises **coverage + analysis + readiness**, never the gates.
