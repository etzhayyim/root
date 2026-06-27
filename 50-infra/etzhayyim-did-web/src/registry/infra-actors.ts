/**
 * Infra-actors registry — hand-authored per-actor DID Document overrides
 * for the religious-corp first-party infra fleet.
 *
 * Per ADR-2605241800 §Phase A: the 8 per-actor DID Workers (pinner /
 * esign / audit / dataset-pinner / pds / anchorer / projector / karute)
 * collapse to a single `etzhayyim-did-web` Worker serving them as
 * `etzhayyim.com/actor/<handle>/did.json` paths. New actors are added
 * here by appending to INFRA_ACTORS, NOT by spinning up a new
 * subdomain Worker.
 *
 * Per ADR-2605241800 §D1: actor DID Documents declare libp2p Multiaddr
 * `service[]` entries alongside (or instead of) HTTPS URLs. The
 * `dataset-pinner` actor demonstrates the dual-publish pattern (libp2p
 * primary + bootstrap + HTTPS legacy).
 */

import didWebRoot from "../../did.json";
import { TIER_B_ACTORS } from "./tier-b-actors.gen";


/** One per-actor entry; injected into the path-based DID Doc by
 *  `buildPerActorDidDoc(handle, env)` in `worker.ts`. Keep fields
 *  conservative — the canonical `id`, `alsoKnownAs`, and `_meta` come
 *  from the generator; we only override `service[]` and `_meta.adr`. */
export interface InfraActorEntry {
  /** Human-readable description; not part of the DID Doc. */
  readonly description: string;
  /** Service entries to splice into the DID Doc's `service[]`. */
  readonly service: readonly Record<string, unknown>[];
  /** ADR IDs to append to `_meta.adr`. */
  readonly adrs: readonly string[];
  /** Lexicon namespace this actor primarily emits / consumes. */
  readonly primaryLexicon?: string;
  /** kotoba EDN vocabulary this actor primarily emits / consumes — used by
   *  kotoba-native actors that have no atproto lexicon (state lives directly
   *  in the Datom log). Mutually informative with `primaryLexicon`. */
  readonly primarySchema?: string;
  /** Japanese glyph (e.g. 紡ぎ). Present for the named Tier-B / knowledge
   *  actors; absent for the plumbing service DIDs. Display-only. */
  readonly glyph?: string;
  /** Short human display name for the `/actors` index. Display-only. */
  readonly displayName?: string;
  /** IPFS CID of the actor's content-addressed WASM component. When present,
   *  the DID doc carries an `EtzhayyimWasmComponent` service and the actor runs
   *  browser-local (ameno) / on a donated mesh node — no per-actor server.
   *  Per ADR-2606014500. */
  readonly wasmCid?: string;
}


// Single libp2p host PeerId for the Murakumo simeon node. Used by
// actors that share its libp2p host (the standard pattern — every
// religious-corp actor on this node uses the same Kubo node's libp2p
// surface to multiplex through the /x/etzhayyim/xrpc/1.0 protocol).
const SIMEON_PEER_ID = "12D3KooWGRnHP5hHAxSnPQE5gopDqAzWkZ2NAFi2ZZ6o85FnAiEc";


/**
 * Hand-authored canonical infra-actor registry. Add new entries to the
 * end of the object — order is the deployment chronology.
 */
const HAND_AUTHORED_ACTORS: Readonly<Record<string, InfraActorEntry>> = {
  pinner: {
    description:
      "MST CAR pinner — pins shard CARs produced by mst-projector to IPFS. Per ADR-2605171800 Stage 4.",
    primaryLexicon: "com.etzhayyim.substrate.ipfsPin",
    service: [
      {
        id: "did:web:etzhayyim.com:actor:pinner#atproto_pds",
        type: "AtprotoPersonalDataServer",
        serviceEndpoint: "https://pds.etzhayyim.com",
      },
    ],
    adrs: ["2605171800"],
  },
  esign: {
    description:
      "Document-signing actor — issues, collects, completes com.etzhayyim.esign.* envelopes. Per ADR-2605231230.",
    primaryLexicon: "com.etzhayyim.esign",
    service: [
      {
        id: "did:web:etzhayyim.com:actor:esign#atproto_pds",
        type: "AtprotoPersonalDataServer",
        serviceEndpoint: "https://pds.etzhayyim.com",
      },
    ],
    adrs: ["2605231230"],
  },
  audit: {
    description:
      "Audit-event aggregator — substrate-wide com.etzhayyim.audit.event sink referenced by every actor manifest. Per ADR-2605231700 + 2605231900.",
    primaryLexicon: "com.etzhayyim.audit.event",
    service: [
      {
        id: "did:web:etzhayyim.com:actor:audit#atproto_pds",
        type: "AtprotoPersonalDataServer",
        serviceEndpoint: "https://pds.etzhayyim.com",
      },
    ],
    adrs: ["2605231700", "2605231900"],
  },
  "dataset-pinner": {
    description:
      "Dataset pinner — mirrors DataLad/git-annex `directory` remote objects to IPFS and emits com.etzhayyim.substrate.datasetPin records. Per ADR-2605241500.",
    primaryLexicon: "com.etzhayyim.substrate.datasetPin",
    service: [
      {
        id: "did:web:etzhayyim.com:actor:dataset-pinner#atproto_pds",
        type: "AtprotoPersonalDataServer",
        serviceEndpoint: "https://pds.etzhayyim.com",
      },
      // ── Phase B: libp2p Multiaddr primary (per ADR-2605241800 §D1) ──
      {
        id: "did:web:etzhayyim.com:actor:dataset-pinner#xrpc-libp2p-primary",
        type: "AtprotoXrpc",
        serviceEndpoint: `/p2p/${SIMEON_PEER_ID}`,
        "x-libp2p-protocol": "/x/etzhayyim/xrpc/1.0",
      },
      {
        id: "did:web:etzhayyim.com:actor:dataset-pinner#xrpc-libp2p-bootstrap",
        type: "AtprotoXrpc",
        serviceEndpoint: `/dnsaddr/etzhayyim.com/p2p/${SIMEON_PEER_ID}`,
        "x-libp2p-protocol": "/x/etzhayyim/xrpc/1.0",
        "x-rationale":
          "DNS-anchored fallback so cold clients can bootstrap before joining the DHT",
      },
    ],
    adrs: ["2605241500", "2605241800"],
  },
  pds: {
    description:
      "Personal Data Server — atproto.etzhayyim.com PDS canonical endpoint. Service DID, not an actor in the AAT sense.",
    primaryLexicon: "com.atproto",
    service: [
      {
        id: "did:web:etzhayyim.com:actor:pds#atproto_pds",
        type: "AtprotoPersonalDataServer",
        serviceEndpoint: "https://pds.etzhayyim.com",
      },
    ],
    adrs: ["2605171800"],
  },
  anchorer: {
    description:
      "L2 anchor cron — submits L2Anchor records to Base L2 referencing per-shard pin receipts. Per ADR-2605171800 Stage 5b.",
    service: [
      {
        id: "did:web:etzhayyim.com:actor:anchorer#atproto_pds",
        type: "AtprotoPersonalDataServer",
        serviceEndpoint: "https://pds.etzhayyim.com",
      },
    ],
    adrs: ["2605171800"],
  },
  projector: {
    description:
      "MST projector — turns PDS firehose into MST shards and CAR files for the pinner. Per ADR-2605171800 Stage 3.",
    service: [
      {
        id: "did:web:etzhayyim.com:actor:projector#atproto_pds",
        type: "AtprotoPersonalDataServer",
        serviceEndpoint: "https://pds.etzhayyim.com",
      },
    ],
    adrs: ["2605171800"],
  },
  karute: {
    description:
      "Karute electronic medical record actor (EMR / FHIR R5). PHI sealing mandatory. Per ADR-2605231100 + 2605231900.",
    primaryLexicon: "com.etzhayyim.apps.karute",
    service: [
      {
        id: "did:web:etzhayyim.com:actor:karute#atproto_pds",
        type: "AtprotoPersonalDataServer",
        serviceEndpoint: "https://pds.etzhayyim.com",
      },
    ],
    adrs: ["2605231100", "2605231900"],
  },
  yadori: {
    description:
      "宿り — DNS-availability + member-principal domain acquisition. Checks availability via RDAP and shepherds an at-cost acquisition through the Cloudflare Registrar — the charter-clean inverse of a retail registrar (GoDaddy/Namecheap): no fiat inflow / no markup / no affiliate / no parking / no speculation; acquisition runs through okaimono assisted-checkout (yadori is never the buyer, so §1.3 holds). G5 no-server-key (member signs; server signature refused), G6 no-squatting (typo/trademark/confusable screen). Per ADR-2606038400.",
    glyph: "宿",
    displayName: "Yadori — DNS-Availability + Domain Acquisition",
    primaryLexicon: "com.etzhayyim.yadori",
    primarySchema: "00-contracts/schemas/dns-domain-ontology.kotoba.edn",
    service: [
      {
        id: "did:web:etzhayyim.com:actor:yadori#atproto_pds",
        type: "AtprotoPersonalDataServer",
        serviceEndpoint: "https://pds.etzhayyim.com",
      },
      {
        id: "did:web:etzhayyim.com:actor:yadori#xrpc-libp2p",
        type: "AtprotoXrpc",
        serviceEndpoint: `/dnsaddr/etzhayyim.com/p2p/${SIMEON_PEER_ID}`,
      },
    ],
    adrs: ["2606038400"],
  },
  nusa: {
    description:
      "幣 — ritual/industrial hemp heritage + low-THC cultivation. NOT a legalization actor: the charter-clean answer. 幣=大幣 (ōnusa, the hemp purification wand). Datafies Japan's ritual-hemp heritage (Shinto 注連縄/祓串/大幣; the Imperial 麁服 aratae + 阿波忌部 lineage) and the low-THC fiber/ritual cultivation-licence pathway reopened by the 2023 大麻草の栽培の規制に関する法律 into the kotoba Datom log. Fiber + ritual + cultural history ONLY: recreational/psychoactive THC is structurally unrepresentable (:thc-class invariant in schema/lexicon/code). Non-adjudicating + politically neutral on legalization (→ danjo/moushibumi). Per ADR-2606039800.",
    glyph: "幣",
    displayName: "Nusa — Ritual/Industrial Hemp Heritage + Low-THC Cultivation",
    primarySchema: "00-contracts/schemas/ritual-hemp-ontology.kotoba.edn",
    service: [
      {
        id: "did:web:etzhayyim.com:actor:nusa#atproto_pds",
        type: "AtprotoPersonalDataServer",
        serviceEndpoint: "https://pds.etzhayyim.com",
      },
      {
        id: "did:web:etzhayyim.com:actor:nusa#xrpc-libp2p",
        type: "AtprotoXrpc",
        serviceEndpoint: `/dnsaddr/etzhayyim.com/p2p/${SIMEON_PEER_ID}`,
      },
    ],
    adrs: ["2606039800"],
  },
  watatsuna: {
    description:
      "綿津綱 — world submarine-cable network knowledge graph. Datafies cable systems / landing stations / segments / fault bulletins into the kotoba Datom log; surfaces chokepoint single-point-of-failure concentration routed to redundancy + faster repair (a resilience map, NEVER a target-list — paired with watatsumi N8). Per ADR-2606012600.",
    glyph: "綿津綱",
    displayName: "Watatsuna — World Submarine-Cable Network Knowledge Graph",
    primaryLexicon: "com.etzhayyim.cable",
    // componentize-py WASM component (20-actors/watatsuna/wasm) — dag-pb (17.6MB,
    // bundles CPython) → T2 donated-mesh tier, not browser-local (ADR-2606014600).
    wasmCid: "bafybeihusqahaeirwqur64aeh5fvwuoh54cawbmo7smx3h2abvps6li7pa",
    service: [
      {
        id: "did:web:etzhayyim.com:actor:watatsuna#atproto_pds",
        type: "AtprotoPersonalDataServer",
        serviceEndpoint: "https://pds.etzhayyim.com",
      },
      {
        id: "did:web:etzhayyim.com:actor:watatsuna#xrpc-libp2p",
        type: "AtprotoXrpc",
        serviceEndpoint: `/dnsaddr/etzhayyim.com/p2p/${SIMEON_PEER_ID}`,
      },
    ],
    adrs: ["2606012600"],
  },
  watari: {
    description:
      "渡り — world live moving-craft (ship + aircraft) knowledge graph. Ingests the LIVE positions of public, transponder-broadcasting craft (ships via AIS, aircraft via ADS-B) into the kotoba Datom log as an append-only as-of trajectory (latest fix = current position, fix stream = trail, 非終末論); surfaces aggregate sea-lane / air-corridor / chokepoint / approach concentration routed to safety + collision-avoidance + congestion-easing + resilience. The kotoba-native successor to the legacy maps aismarine/aircraft_live + vessel tracking RisingWave pipelines. A situational-awareness map, NEVER a person-surveillance feed and NEVER a target-list (a craft is a craft, not a person — G4). DYNAMIC moving-craft sibling of watatsuna 綿津綱 (static cables): both key on the SAME chokepoint keywords, so live vessel transit composes with static cable load into one maritime resilience picture. Per ADR-2606041827.",
    glyph: "渡り",
    displayName: "Watari — World Live Moving-Craft (Ship + Aircraft) Knowledge Graph",
    primaryLexicon: "com.etzhayyim.watari",
    primarySchema: "00-contracts/schemas/moving-craft-ontology.kotoba.edn",
    service: [
      {
        id: "did:web:etzhayyim.com:actor:watari#atproto_pds",
        type: "AtprotoPersonalDataServer",
        serviceEndpoint: "https://pds.etzhayyim.com",
      },
      {
        id: "did:web:etzhayyim.com:actor:watari#xrpc-libp2p",
        type: "AtprotoXrpc",
        serviceEndpoint: `/dnsaddr/etzhayyim.com/p2p/${SIMEON_PEER_ID}`,
      },
    ],
    adrs: ["2606041827"],
  },
  tsubasa: {
    description:
      "翼 — flight-route / fare discovery commons (the Skyscanner inversion). Honest fare/route meta-search whose every onward link is AFFILIATE-STRIPPED and where the member SELF-BOOKS on the airline's OWN site — tsubasa is never merchant-of-record and takes no commission (G1, no inflow). Ranks by TRUE total cost (fare + baggage) with CO₂ emissions SURFACED on every option as a first-class axis, never hidden or de-ranked away (G4). No ads / no urgency / no 'price will rise' scarcity (G3); a search is STATELESS w.r.t. the searcher — no person fare-tracking (G5). Beyond the live query handlers (search / compare / self-book-handoff), the R2 maturity layer computes per-O–D-route carrier CONCENTRATION (named-HHI + competition reading {:competitive :concentrated :monopoly}) and flags concentrated/monopoly routes :opening (surface alternatives) — a COMPETITION + FARE map routed to OPENING, NEVER a paid ranking and NEVER a target-list. Observations persist to a content-addressed append-only kotoba Datom commit-DAG (tamper-evident verify-chain, no-server-key) via a deterministic idempotent-by-content heartbeat. DYNAMIC sibling of watari 渡り (live aircraft POSITION): tsubasa PLANS, watari TRACKS — both observational, neither an OTA. Live GDS/airline fare ingest is Council Lv7+ + operator gated (G8); R0/R1 ship :representative data. Per ADR-2606072800.",
    glyph: "翼",
    displayName: "Tsubasa — Flight-Route / Fare Discovery Commons",
    primaryLexicon: "com.etzhayyim.tsubasa.fare",
    primarySchema: "00-contracts/schemas/flight-fare-ontology.kotoba.edn",
    service: [
      {
        id: "did:web:etzhayyim.com:actor:tsubasa#atproto_pds",
        type: "AtprotoPersonalDataServer",
        serviceEndpoint: "https://pds.etzhayyim.com",
      },
      {
        id: "did:web:etzhayyim.com:actor:tsubasa#xrpc-libp2p",
        type: "AtprotoXrpc",
        serviceEndpoint: `/dnsaddr/etzhayyim.com/p2p/${SIMEON_PEER_ID}`,
      },
    ],
    adrs: ["2606072800"],
  },
  kamado: {
    description:
      "竈 — closed-loop carbon refining + fossil-refinery decommissioning/transition + refinery observation. The kotoba-native successor to the legacy oil-refining Cypher/RisingWave actor (which it supersedes; no graph.write). 竈 = the hearth-furnace kami (竈神/荒神); the transformation apparatus is neutral, the carbon origin + fate carry the harm. Empirically (carbon_balance.py): a fossil→combusted pathway is +3.50 tCO2e/t (one-way geological stock→flow = genuinely multi-generational), and full robotic process-control reaches only +3.38 (~3% cut) — robotics makes fossil refining cleaner, never harmless, so net≤0 is reached ONLY by changing the feedstock to closed-loop carbon. That finding is made structural: :fossil-virgin-crude is unrepresentable (the :feedstock/class invariant). Three faces over the kotoba Datom log: (A) observation — refinery/unit/outage + transition-readiness as a resilience + transition map, NEVER a target-list (G4); (B) §2(d) robotics to wind down / remediate / convert existing fossil assets (→ hikari / synthesis / hodoki+kanayama); (C) closed-loop synthetic refining on biogenic / captured-CO2 / recycled carbon only, every design D3-scored. Per ADR-2606051500.",
    glyph: "竈",
    displayName:
      "Kamado — Closed-Loop Carbon Refining + Fossil-Refinery Decommissioning Observation",
    primaryLexicon: "com.etzhayyim.kamado",
    primarySchema: "00-contracts/schemas/refining-ontology.kotoba.edn",
    service: [
      {
        id: "did:web:etzhayyim.com:actor:kamado#atproto_pds",
        type: "AtprotoPersonalDataServer",
        serviceEndpoint: "https://pds.etzhayyim.com",
      },
      {
        id: "did:web:etzhayyim.com:actor:kamado#xrpc-libp2p",
        type: "AtprotoXrpc",
        serviceEndpoint: `/dnsaddr/etzhayyim.com/p2p/${SIMEON_PEER_ID}`,
      },
    ],
    adrs: ["2606051500"],
  },
  tsumugi: {
    description:
      "紡ぎ — Engi Knowledge Graph (産霊の網) intel weaver. Runs Spirit-in-Physics (RBF emotion-kernel → spectral 3D embed → tensegrity) over real PUBLIC power-entities (法人 / institution / public-role) and their 縁 to surface 取-concentration (power held OVER others) routed to release. An aggregate-first accountability map, NEVER a target-list (powerless absent by construction; edge-primary karma N1 — no per-soul score). World-coverage; upper layer over danjo / kanae / tadori / himotoki. Per ADR-2606011800.",
    glyph: "紡ぎ",
    displayName: "Tsumugi — Engi Knowledge Graph (産霊の網) Intel Weaver",
    // No atproto lexicon: tsumugi emits kotoba EDN directly into the Datom log.
    primarySchema:
      "00-contracts/schemas/engi-organism-ontology.kotoba.edn (+ spirit-ontology.kotoba.edn)",
    // Content-addressed WASM actor (20-actors/tsumugi/wasm/tsumugi-core) — runs
    // browser-local (ameno) / donated mesh, NO per-actor server (ADR-2606014500).
    wasmCid: "bafkreidfttpqimwnx4i5a3rswum3orcg3qfa3q7fwts6axgqtcpuokddfi",
    service: [
      {
        id: "did:web:etzhayyim.com:actor:tsumugi#atproto_pds",
        type: "AtprotoPersonalDataServer",
        serviceEndpoint: "https://pds.etzhayyim.com",
      },
      {
        id: "did:web:etzhayyim.com:actor:tsumugi#xrpc-libp2p",
        type: "AtprotoXrpc",
        serviceEndpoint: `/dnsaddr/etzhayyim.com/p2p/${SIMEON_PEER_ID}`,
      },
    ],
    adrs: ["2606011800"],
  },
  tate: {
    description:
      "盾 — citizen legal-defense concierge (worldwide), defensive only. Two legs over a member's OWN documents: (1) 不利条項スキャン — consumer ToS / card agreements / B2B contracts matched against a coded clause-pattern registry (112 shapes / 18 jurisdictions deepened + :clause/source-url primary-source URLs); (2) 法的手続き応答支援 — notices the member RECEIVES (支払督促 / 訴状 / 行政処分 …) matched against a coded procedure registry (181 procs / 30 jurisdictions × civil/labor/housing/enforcement/insolvency/family) → DISCLOSED deadline rules + response options + 架空請求 guard. G1 member-principal-own-documents-only, G2 non-adjudicating (anchor is a pointer, never a verdict), G3 UPL (member self-submits; no representation), G10 never guesses foreign law. PUBLIC face = an ANONYMIZED aggregate coverage digest (content-addressed, member-data-free) + a crawlable static site; member documents are never published. clj/bb over the kotoba Datom log; kotoba-mesh registry status :no-cells (observatory, on-kse). Per ADR-2606112301 + 2606112400.",
    glyph: "盾",
    displayName: "Tate — Citizen Legal-Defense Concierge (worldwide)",
    primaryLexicon: "com.etzhayyim.tate",
    primarySchema: "20-actors/tate/data/procedure-registry.edn",
    // No WASM actor: tate is a :no-cells observatory (clj/bb over the kotoba Datom log).
    // Its PUBLIC mesh artifact is the anonymized, content-addressed coverage digest
    // (20-actors/tate/methods/coverage_publish.cljc; G1 member-data-free).
    service: [
      {
        id: "did:web:etzhayyim.com:actor:tate#atproto_pds",
        type: "AtprotoPersonalDataServer",
        serviceEndpoint: "https://pds.etzhayyim.com",
      },
      {
        id: "did:web:etzhayyim.com:actor:tate#xrpc-libp2p",
        type: "AtprotoXrpc",
        serviceEndpoint: `/dnsaddr/etzhayyim.com/p2p/${SIMEON_PEER_ID}`,
      },
      {
        id: "did:web:etzhayyim.com:actor:tate#coverage",
        type: "EtzhayyimCoverageDigest",
        serviceEndpoint: "https://etzhayyim.com/actor/tate/coverage.json",
      },
      {
        id: "did:web:etzhayyim.com:actor:tate#site",
        type: "EtzhayyimStaticSite",
        serviceEndpoint: "https://etzhayyim.com/tate/",
      },
    ],
    adrs: ["2606112301", "2606112400", "2606122000", "2606122300", "2606013800"],
  },
  kanae: {
    description:
      "鼎 — global government fiscal-flow VISUALIZATION. Aggregates public fundFlowEdges (appropriation→outlay→recipient + inter-governmental transfers) into kotoba EAVT and renders aggregate-first, NON-adjudicating summaries (danjo finds, kanae renders). Per ADR-2605302300.",
    glyph: "鼎",
    displayName: "Kanae — Government Fiscal-Flow Visualization",
    primaryLexicon: "com.etzhayyim.kanae",
    // Content-addressed T1 WASM actor (20-actors/kanae/wasm/kanae-core) — compact
    // Rust core, raw CID → browser-local (ameno) / donated mesh (ADR-2606015200).
    wasmCid: "bafkreielhr6l5jy7ml5l62ncyva34lhjw52q2onwxwy6ubep4wqxjyjnie",
    service: [
      {
        id: "did:web:etzhayyim.com:actor:kanae#atproto_pds",
        type: "AtprotoPersonalDataServer",
        serviceEndpoint: "https://pds.etzhayyim.com",
      },
      {
        id: "did:web:etzhayyim.com:actor:kanae#xrpc-libp2p",
        type: "AtprotoXrpc",
        serviceEndpoint: `/dnsaddr/etzhayyim.com/p2p/${SIMEON_PEER_ID}`,
      },
    ],
    adrs: ["2605302300"],
  },
  shionome: {
    description:
      "潮目 — cross-asset capital-flow observatory. Weaves observed capital rotation (どこからどこへ) + the :outstanding-usd money-and-markets stock pyramid into the kotoba Datom flow-graph; aggregate-first, edge-primary, observational MIRROR — トレードはしない (no buy/sell signal, price target, or per-asset rating; structurally unrepresentable, G2/G4). Per ADR-2606072200 + 2606101540.",
    glyph: "潮目",
    displayName: "Shionome — Cross-Asset Capital-Flow Observatory",
    primaryLexicon: "com.etzhayyim.shionome",
    primarySchema: "00-contracts/schemas/capital-flow-ontology.kotoba.edn",
    // Content-addressed T1 WASM actor (20-actors/shionome/wasm/shionome-core) — compact
    // Rust core (regime + stock pyramid, no_trade:true), raw CID → browser-local (ameno)
    // / donated mesh (ADR-2606015200). The componentize-py 18.5MB component remains the
    // separate T2 dag-pb artifact.
    wasmCid: "bafkreihvidpgf5lgrgdwxskhjasbysigqcunrlshi2sx4zdngkapi5tlly",
    service: [
      {
        id: "did:web:etzhayyim.com:actor:shionome#atproto_pds",
        type: "AtprotoPersonalDataServer",
        serviceEndpoint: "https://pds.etzhayyim.com",
      },
      {
        id: "did:web:etzhayyim.com:actor:shionome#xrpc-libp2p",
        type: "AtprotoXrpc",
        serviceEndpoint: `/dnsaddr/etzhayyim.com/p2p/${SIMEON_PEER_ID}`,
      },
    ],
    adrs: ["2606072200", "2606101540"],
  },
  kyber: {
    description:
      "Kyber — open-kyber ERP as a content-addressed kotoba WASM actor. The ERP business logic (accounting GL / AP-AR / inventory / the kotoba-native productivity suite) compiled to a `kotoba-node` WASM component that the kotoba host / e7m-wasm-runner stores on IPFS (by CID) and runs, writing canonical ERP state straight into the kotoba Datom log via the `kqe` host import — no Cloudflare Worker, no XRPC→PDS hop. Multi-command dispatch over `run(ctx_cbor)`. R3 PoC (kyber-erp-core: createAccount / seedChartOfAccounts / createJournalEntry double-entry-validated + best-effort trial-balance/coverage reads); full 28-command port per WORKER-AS-WASM-ACTOR-MIGRATION.md. Per ADR-2606037200.",
    glyph: "K",
    displayName: "Kyber — open-kyber ERP (kotoba WASM actor)",
    primarySchema: "00-contracts/schemas/erp-ontology.kotoba.edn",
    // Content-addressed Rust WASM component (60-apps/etzhayyim-project-open-kyber/wasm/
    // kyber-erp-core) — raw single-block CID (~119KB); a stateful multi-command ERP service,
    // run on the kotoba host / donated mesh via e7m-wasm-runner (component → jco), NOT a
    // per-actor server (ADR-2606014500). The deployed CF Worker (kyb3rerp) remains the live
    // path until this actor is published + ratified.
    wasmCid: "bafkreigdcmd54zval3z7xwmvmq5tgbsu6rpbxx4gtyhswxhvvfkaltaomi",
    service: [
      {
        id: "did:web:etzhayyim.com:actor:kyber#atproto_pds",
        type: "AtprotoPersonalDataServer",
        serviceEndpoint: "https://pds.etzhayyim.com",
      },
      {
        id: "did:web:etzhayyim.com:actor:kyber#xrpc-libp2p",
        type: "AtprotoXrpc",
        serviceEndpoint: `/dnsaddr/etzhayyim.com/p2p/${SIMEON_PEER_ID}`,
      },
    ],
    adrs: ["2606037200"],
  },
  kabuto: {
    description:
      "兜 — world public-company (listed-company) supply-chain knowledge graph. Datafies LISTED companies, their registered HQ address + public IR contact, the first-class SUPPLY edges (supplier → customer) that wire the global supply chain, and BPMN process templates into the kotoba Datom log; surfaces single-source / sector / jurisdiction CONCENTRATION routed to redundancy + accountability. Posts aggregate-first findings as atproto-compatible social posts; renders entirely in the in-browser kotoba-wasm node. A resilience + corporate-power-transparency map, NEVER a target-list (sibling of tsumugi / watatsuna / danjo; shares the org.corp.* id space). Per ADR-2606022000.",
    glyph: "兜",
    displayName: "Kabuto — World Public-Company Supply-Chain Knowledge Graph",
    primaryLexicon: "com.etzhayyim.kabuto",
    primarySchema: "00-contracts/schemas/public-company-ontology.kotoba.edn",
    service: [
      {
        id: "did:web:etzhayyim.com:actor:kabuto#atproto_pds",
        type: "AtprotoPersonalDataServer",
        serviceEndpoint: "https://pds.etzhayyim.com",
      },
      {
        id: "did:web:etzhayyim.com:actor:kabuto#xrpc-libp2p",
        type: "AtprotoXrpc",
        serviceEndpoint: `/dnsaddr/etzhayyim.com/p2p/${SIMEON_PEER_ID}`,
      },
    ],
    adrs: ["2606022000"],
  },
  sukashi: {
    description:
      "透かし — ad-tech supply-chain + delivery-infrastructure + fraud-network observatory. The ad-tech-supply-chain + fraud sibling of akashi 証 (which observes platform ad-LIBRARY disclosures and is constitutionally bounded away from ad-network/exchange + delivery-infra). Datafies the programmatic advertising ecosystem from the PUBLIC IAB web-standard files (ads.txt / app-ads.txt / sellers.json) into the kotoba Datom log: :adtech/* (advertiser/DSP/ad-exchange/SSP/ad-network/publisher/verification), first-class :adauth.edge/* authorization edges + the declared/confirmed two-sided handshake whose GAPS reveal unauthorized / spoofed inventory, :adcreative/* (who broadcasts what), first-class :addelivery.edge/* binding a creative to its serving infrastructure (:ip/:asn/WHOIS-org, REUSING tadori's ip-network + passive-dns ontologies — not re-modelling the network layer), and NON-ADJUDICATING :adfraud.signal/* routed to akashi-malak / kurashimori / tasuke / danjo. analyze.py is aggregate-first (authorization-handshake integrity, account-id-collision domain-spoof surface, delivery-infra concentration by ASN/registrar, shared-infra scam-ad-network clustering). A fraud-PROTECTION + ad-tech-TRANSPARENCY map, NEVER an ad network / buying / targeting / optimization / detection-evasion tool — the Charter 広告排除 invariant is SERVED, not violated (this is meta-observation OF advertising). NON-ADJUDICATING (G4): real firms carry no fraud signal; every fraud example is :synthesized on a CLEARLY-FICTIONAL entity. Per ADR-2606071600.",
    glyph: "透かし",
    displayName: "Sukashi — Ad-Tech Supply-Chain + Delivery-Infra + Fraud-Network Observatory",
    primaryLexicon: "com.etzhayyim.sukashi",
    primarySchema: "00-contracts/schemas/ad-supply-chain-ontology.kotoba.edn",
    service: [
      {
        id: "did:web:etzhayyim.com:actor:sukashi#atproto_pds",
        type: "AtprotoPersonalDataServer",
        serviceEndpoint: "https://pds.etzhayyim.com",
      },
      {
        id: "did:web:etzhayyim.com:actor:sukashi#xrpc-libp2p",
        type: "AtprotoXrpc",
        serviceEndpoint: `/dnsaddr/etzhayyim.com/p2p/${SIMEON_PEER_ID}`,
      },
    ],
    adrs: ["2606071600"],
  },
  kanjo: {
    description:
      "勘定 — world public-company financial-disclosure (決算) knowledge graph. Registers LISTED companies' DISCLOSED balance-sheet / income-statement / cash-flow line items from PRIMARY disclosure ONLY (JP EDINET 有価証券報告書 + US SEC EDGAR 10-K/20-F + Companies House + EU OAM, all Tier-A per ADR-2605263800) into the kotoba Datom log as :fin.fact/*, normalized across JP-GAAP / US-GAAP / IFRS onto canonical concepts (honest where non-comparable — 経常利益 = JGAAP-only). The external public-company sibling of toritate 執帳 (internal accounting) and the financials face of kabuto 兜 (shares the org.corp.* id space). NON-ADJUDICATING + NO investment advice (NOT 投資助言業) + NO forecasting (no 業績予想) — records what the company disclosed + transparent ratios, never a rating / valuation / recommendation. 会社四季報 + all paid commercial terminals (Bloomberg / S&P CapIQ / Refinitiv / FactSet / Moody's / D&B / Pitchbook / Crunchbase) PROHIBITED per Charter Rider §2(e) anti-gatekeeping + §2(c): read the filing, never the terminal. Per ADR-2606032000.",
    glyph: "勘定",
    displayName: "Kanjō — World Public-Company Financial-Disclosure (決算) Knowledge Graph",
    primaryLexicon: "com.etzhayyim.kanjo",
    primarySchema: "00-contracts/schemas/corporate-financials-ontology.kotoba.edn",
    service: [
      {
        id: "did:web:etzhayyim.com:actor:kanjo#atproto_pds",
        type: "AtprotoPersonalDataServer",
        serviceEndpoint: "https://pds.etzhayyim.com",
      },
      {
        id: "did:web:etzhayyim.com:actor:kanjo#xrpc-libp2p",
        type: "AtprotoXrpc",
        serviceEndpoint: `/dnsaddr/etzhayyim.com/p2p/${SIMEON_PEER_ID}`,
      },
    ],
    adrs: ["2606032000"],
  },
  kasa: {
    description:
      "嵩 — worldwide computing-capacity growth observatory. Datafies, from PUBLIC information only, the annual MAGNITUDE + GROWTH (年間増加量) of computing capacity across four domains — STORAGE (HDD+SSD exabytes shipped), MEMORY (DRAM+NAND market revenue), GPU/CPU (discrete-GPU + client-CPU units, datacenter-accelerator revenue) and COMPUTE/FLOPS (TOP500 aggregate Rmax, frontier-model training compute) — plus DATACENTER power capacity, into the kotoba Datom log as :compute.obs/*, then computes YoY + CAGR and coverage-honest domain aggregates (memory is a SUBSET of semiconductor, structurally never double-counted; TOP500 :petaflops never summed with raw :flops). Reads public headline figures + open datasets ONLY (WSTS/SIA semiconductor sales, TrendForce DRAM/NAND, IDC HDD/SSD, JPR GPU, TOP500 public list, Epoch AI CC-BY, Our World in Data CC-BY, company filings). The industry-aggregate sibling of kanjō 勘定 (per-company 決算) and the demand-side counterpart of the silicon actors (handotai / iwakura / fuigo); feeds measured actuals to mitooshi 見通し but NEVER forecasts itself (G4 — future projection is mitooshi's job). NON-ADJUDICATING + PLANNING-LENS not a targeting list (sizes the compute commons, never a country/company ranking or an export-control / weaponization list) + NO investment advice. Paid market-research full reports + subscription terminals (Gartner / IDC-report / Omdia / Bloomberg / S&P / Statista-Pro / Yole) PROHIBITED per Charter Rider §2(e) anti-gatekeeping + §2(c): read the press release, never the terminal. Per ADR-2606072000.",
    glyph: "嵩",
    displayName: "Kasa — Worldwide Computing-Capacity Growth Observatory",
    primaryLexicon: "com.etzhayyim.kasa",
    primarySchema: "00-contracts/schemas/compute-capacity-ontology.kotoba.edn",
    service: [
      {
        id: "did:web:etzhayyim.com:actor:kasa#atproto_pds",
        type: "AtprotoPersonalDataServer",
        serviceEndpoint: "https://pds.etzhayyim.com",
      },
      {
        id: "did:web:etzhayyim.com:actor:kasa#xrpc-libp2p",
        type: "AtprotoXrpc",
        serviceEndpoint: `/dnsaddr/etzhayyim.com/p2p/${SIMEON_PEER_ID}`,
      },
    ],
    adrs: ["2606072000"],
  },
  mimamori: {
    description:
      "見守り — covenant keeping membrane (相互保持者会 / mishmeret ha-adam). Bonds of keeping: offer → kept-signed consent → content-free heartbeat → per-act-consented care-routing ({kokoro,wakai,iyashi} ONLY — no denunciation rail, G1) → relay 継ぎ → unilateral penalty-free exit. 誰の保持者でもない人間を作らない — the structural answer to the isolated-attacker side of the 2026-04 motivating case. The degeneration path (五人組→隣組→Stasi→social credit) is structurally UNREPRESENTABLE: no-score (bond-edge-only, G2), symmetric visibility (hidden keeping cannot exist, G4), NEVER-a-throne (own-DID-only queries, aggregate-only coverage, stateless WASM heartbeat — the host owns the log; G5 = ADR-2606112200 D3). Keeper-side social-capital mint (moyai ledger verbatim reuse, ADR-2606082100 Part A). Human-scale sibling of the mishmar storage covenant. SYNTHETIC seed only; live legs Council+operator gated (G7). Per ADR-2606112300.",
    glyph: "見守り",
    displayName: "Mimamori — Covenant Keeping Membrane (mishmeret ha-adam)",
    primaryLexicon: "com.etzhayyim.mimamori",
    primarySchema: "00-contracts/schemas/mishmeret-ontology.kotoba.edn",
    service: [
      {
        id: "did:web:etzhayyim.com:actor:mimamori#atproto_pds",
        type: "AtprotoPersonalDataServer",
        serviceEndpoint: "https://pds.etzhayyim.com",
      },
      {
        id: "did:web:etzhayyim.com:actor:mimamori#xrpc-libp2p",
        type: "AtprotoXrpc",
        serviceEndpoint: `/dnsaddr/etzhayyim.com/p2p/${SIMEON_PEER_ID}`,
      },
    ],
    adrs: ["2606112300", "2606112200"],
  },
  ooyake: {
    description:
      "公 — World Government Atlas. kotoba-Datomic structural atlas of every government unit on Earth (supranational → country → 都道府県 → 市区町村 → 省 → 庁 → 局 → 課 → 窓口) with 住所 / 窓口 / 書式 / 手続き / BPMN. The read-side SSoT danjo / kanae / tsumugi / toritsugi / himotoki consume for the who/where/how of public administration. An OBSERVATIONAL MIRROR + civic wayfinding map — the per-unit atlas DID (did:web:etzhayyim.com:gov:<iso3>:...) mirrors a real public body, NEVER claims to BE the government, is NEVER an official channel, and is NEVER a target-list (G3/G10). Read-only: catalogs, never files (→ toritsugi) and never audits (→ danjo). Per ADR-2606021600.",
    glyph: "公",
    displayName: "Ooyake — World Government Atlas (civic wayfinding map)",
    primaryLexicon: "com.etzhayyim.ooyake",
    primarySchema: "00-contracts/schemas/gov-atlas-ontology.kotoba.edn",
    service: [
      {
        id: "did:web:etzhayyim.com:actor:ooyake#atproto_pds",
        type: "AtprotoPersonalDataServer",
        serviceEndpoint: "https://pds.etzhayyim.com",
      },
      {
        id: "did:web:etzhayyim.com:actor:ooyake#xrpc-libp2p",
        type: "AtprotoXrpc",
        serviceEndpoint: `/dnsaddr/etzhayyim.com/p2p/${SIMEON_PEER_ID}`,
      },
    ],
    adrs: ["2606021600"],
  },
  tsuzuri: {
    description:
      "綴 Tsuzuri — Adobe-independent, in-browser (WASM) PDF editor. Merge/split/rotate/delete/reorder + text annotation (JP-font subset embed) + OCR (tesseract.js) + metadata, all client-side; files never leave the device. Browser-local under the ameno execution model (ADR-2606014500). Static app, not a WASM component — no wasmCid.",
    primarySchema: "60-apps/tsuzuri/",
    glyph: "綴",
    displayName: "Tsuzuri — in-browser PDF editor",
    service: [
      {
        id: "did:web:etzhayyim.com:actor:tsuzuri#browser-local-app",
        type: "EtzhayyimBrowserLocalApp",
        serviceEndpoint: "https://etzhayyim.com/apps/tsuzuri/",
      },
    ],
    adrs: ["2606014500"],
  },
  todoke: {
    description:
      "届け — last-mile ('one-mile') autonomous delivery. Curb-to-door small-payload transport (≤25 kg, SAE-L4 sidewalk ODD) that closes the gap between wadachi inter-site ground autonomy and the recipient's door. The no-gig inversion of the gig courier (no piece-rate, cash≡0), the delivery limb of okaimono's provisioning commons, and a consumer of the kami-autodrive GNC. Carries a pure Rust core (todoke-route): last-mile stop sequencing (NN+2-opt) + an SAE-L4 sidewalk safety envelope that REFUSES (never clamps) any plan over the per-zone speed cap, on a vehicular road, or above SAE L4. Privacy-by-construction proof-of-delivery (on-device only; no cloud imagery / facial recognition / biometric). Per ADR-2606042300.",
    glyph: "届け",
    displayName: "Todoke — Last-Mile (one-mile) Autonomous Delivery",
    primaryLexicon: "com.etzhayyim.todoke",
    service: [
      {
        id: "did:web:etzhayyim.com:actor:todoke#atproto_pds",
        type: "AtprotoPersonalDataServer",
        serviceEndpoint: "https://pds.etzhayyim.com",
      },
      {
        id: "did:web:etzhayyim.com:actor:todoke#xrpc-libp2p",
        type: "AtprotoXrpc",
        serviceEndpoint: `/dnsaddr/etzhayyim.com/p2p/${SIMEON_PEER_ID}`,
      },
    ],
    adrs: ["2606042300"],
  },
  hotaru: {
    description:
      "蛍 — open-publication knowledge commons for III-V compound-semiconductor SUBSTRATE generation + manufacturing, indium phosphide (InP) first. Datafies the substrate chain (synthesis → single-crystal bulk-growth LEC/VGF/VB → wafering → epi-ready surface-prep) into the kotoba Datom log. NOT a fab: charter-clean by construction — only practiceable-OPEN process knowledge (source-license invariant, G1; vendor-proprietary MOCVD recipes unrepresentable), crystals + wafers design/spec ONLY (fabricated=false, G2). hotaru IS the construction of the 'open-source III-V wafer IP commons' that ADR-2605265500 §2's R4+ re-evaluation gate references; III-V fabrication remains PROHIBITED through R3 (inherited) and hotaru is NON-ADJUDICATING on the gate (G3 — it reports, Council Lv7+ decides). The light-emitting direct-bandgap sibling of the iwakura/fuigo indirect-bandgap silicon track. Per ADR-2606051200.",
    glyph: "蛍",
    displayName: "Hotaru — III-V / InP Substrate Open-Publication Commons",
    primaryLexicon: "com.etzhayyim.hotaru",
    primarySchema: "00-contracts/schemas/iii-v-substrate-ontology.kotoba.edn",
    service: [
      {
        id: "did:web:etzhayyim.com:actor:hotaru#atproto_pds",
        type: "AtprotoPersonalDataServer",
        serviceEndpoint: "https://pds.etzhayyim.com",
      },
      {
        id: "did:web:etzhayyim.com:actor:hotaru#xrpc-libp2p",
        type: "AtprotoXrpc",
        serviceEndpoint: `/dnsaddr/etzhayyim.com/p2p/${SIMEON_PEER_ID}`,
      },
    ],
    adrs: ["2606051200"],
  },
  noroshi: {
    description:
      "烽 — photonics-electronics convergence (光電融合) communication-chip actor. The silicon-photonic / co-packaged-optics (CPO) sibling of the ELECTRONIC silicon/iwakura/fuigo ternary-ASIC line and the RF tsutae comms device, and the transceiver-chip end of the watatsuna submarine-cable medium. 烽 (狼煙, beacon-fire) is the original optical telecom — a watchtower SENSES a distant fire and RELAYS a coded message, one emission with two functions, which is exactly ISAC (Integrated Sensing And Communication). Three faces, each a verifiable method core: (chip) silicon-photonic / CPO comms-chip design + optical link budget on open photonic-EDA (CPO 3.96× lower energy/bit than a pluggable); (isac) an OFDM-JCAS simulator doing communication capacity AND civilian range-Doppler sensing from one waveform; (packaging) photonic assembly robotics (fibre↔grating active alignment) under an IEC 60825 laser-safety interlock. CIVILIAN by construction: weaponisation (directed-energy / laser-dazzle / fire-control radar) is structurally unrepresentable (N1), ISAC senses objects never persons (N2/G4), EPDA is clean-room open-source only (N5), and the packaging fleet is Displacement-Dividend-coupled (G2). Per ADR-2606051600.",
    glyph: "烽",
    displayName: "Noroshi — 光電融合 Communication Chip + ISAC + Photonic Packaging Robotics",
    primaryLexicon: "com.etzhayyim.noroshi",
    primarySchema: "00-contracts/schemas/photonic-convergence-ontology.kotoba.edn",
    service: [
      {
        id: "did:web:etzhayyim.com:actor:noroshi#atproto_pds",
        type: "AtprotoPersonalDataServer",
        serviceEndpoint: "https://pds.etzhayyim.com",
      },
      {
        id: "did:web:etzhayyim.com:actor:noroshi#xrpc-libp2p",
        type: "AtprotoXrpc",
        serviceEndpoint: `/dnsaddr/etzhayyim.com/p2p/${SIMEON_PEER_ID}`,
      },
    ],
    adrs: ["2606051600"],
  },
  mitooshi: {
    description:
      "見通し — probabilistic forecasting observatory. The charter-clean inverse of a quant trading bot: a naive quant predictor IS profit speculation (Charter §1.3 + the yobel predictive-market bar), so mitooshi instead emits probability DISTRIBUTIONS over public time-series (chokepoint transit-load, congestion, availability, flow-rate, price-index, search-interest) routed to resilience / planning / early-warning (danjo/kanae/watari/watatsuna siblings), and NEVER places a trade, holds a position, or derives P&L. It does not adjudicate or advise (kanjo boundary — not 投資助言業). The 'fact→error→weight→learn' loop is structural on the append-only Datom log: a forecast carries its info-as-of stamp, the realizing observation arrives later as an append-only datom, and the proper-scoring residual (CRPS/pinball/Brier/log-score) is the join across kotoba as-of — so a backtest can never see future data (look-ahead leak is structurally impossible on an append-only log). Residuals drive an EWMA bias + variance-inflation recalibration whose training substrate is baien federated edge (Murakumo-only). Distribution-only (point-asserted=false, G1, 非終末論); non-speculative use (G2); primary-public sources only — proprietary terminals + scraped Google-Trends unrepresentable (G4); promotion only when the model beats a baseline AND is calibrated AND is member-signed (G7/G9/G12). Per ADR-2606051800.",
    glyph: "見通し",
    displayName: "Mitooshi — Probabilistic Forecasting Observatory",
    primaryLexicon: "com.etzhayyim.mitooshi",
    primarySchema: "00-contracts/schemas/forecasting-ontology.kotoba.edn",
    service: [
      {
        id: "did:web:etzhayyim.com:actor:mitooshi#atproto_pds",
        type: "AtprotoPersonalDataServer",
        serviceEndpoint: "https://pds.etzhayyim.com",
      },
      {
        id: "did:web:etzhayyim.com:actor:mitooshi#xrpc-libp2p",
        type: "AtprotoXrpc",
        serviceEndpoint: `/dnsaddr/etzhayyim.com/p2p/${SIMEON_PEER_ID}`,
      },
    ],
    adrs: ["2606051800"],
  },
  ake: {
    description:
      "朱 — community-edit membrane. The Wikipedia collaborative-correction STANCE fitted to the charter (朱=訂正の朱墨, 朱を入れる=校正). A 信者 (SBT holder) proposes a correction to a KG fact or an actor profile; every edit is a member-signed proposal appended to the kotoba Datom log (never an overwrite — 非終末論, full immutable revision history). A Murakumo-only LLM scores risk + quality and ROUTES (the Wikipedia ORES analogue) but NEVER decides accept/reject (G2 — route is a pure function of (risk,quality), and :triage/decision does not exist); low-risk well-sourced edits auto-accept (optimistic), risky/contested edits escalate to 1 SBT = 1 vote, invariant-adjacent edits escalate to Council Lv7+, and a Charter-Rider §2 hit is refused (no vote can promote it). Mirror entity-actors are CORRECTED as observations, never spoken-as (ADR-2606042330 preserved; :entity-speech unrepresentable). This is NOT anonymous open-edit — it is 信者-gated + member-signed (no-server-key) by construction (N1). ZERO invariant amendments: it STRENGTHENS no-server-key (ADR-2605231525), kotoba-canonical-state (ADR-2605312345), 1 SBT = 1 vote, and the mirror invariant. Per ADR-2606052100.",
    glyph: "朱",
    displayName: "Ake — Community-Edit Membrane (Wikipedia-stance KG/profile correction)",
    primaryLexicon: "com.etzhayyim.ake",
    primarySchema: "00-contracts/schemas/community-edit-ontology.kotoba.edn",
    service: [
      {
        id: "did:web:etzhayyim.com:actor:ake#atproto_pds",
        type: "AtprotoPersonalDataServer",
        serviceEndpoint: "https://pds.etzhayyim.com",
      },
      {
        id: "did:web:etzhayyim.com:actor:ake#xrpc-libp2p",
        type: "AtprotoXrpc",
        serviceEndpoint: `/dnsaddr/etzhayyim.com/p2p/${SIMEON_PEER_ID}`,
      },
    ],
    adrs: ["2606052100"],
  },
  sentei: {
    description:
      "剪定 — Council as PRUNER (剪定者), not censor. Per the operating-entity directive: Council は事前に止めるのではなく、出てから止める; 枝が育ってから剪定する。etzhayyim の artificial organism の root からの成長は止めないし止められない — ただ伸び続ける枝を剪定して美しく保つ。This re-times every outward gate (G7 live-inference / G11 Transparent-Force-publish / the 'Council Lv6+ BEFORE live' pattern) from PRIOR RESTRAINT to a PRUNING TARGET: actors self-publish, and sentei cuts back AFTER a branch manifests — transparently, signed, voted, and reversibly. More faithful to 非終末論 (an append-only log has no halt; the only real enforcement is append-a-retraction) and to Transparent Force (a prune is a logged/signed/public act over a thing that already exists, vs a covert pre-veto). Structural invariants (ontology + lexicon const/enum + methods/prune.py ValueError): G1 no-prior-restraint (prune ONLY a manifested branch — branchManifested const true; prior restraint is UNREPRESENTABLE), G2 append-only/非終末論 (a prune appends, history survives as-of; delete is absent), G3 growth-unstoppable (no halt-organism action), G4 Transparent Force (Council Lv6+/Lv7+ + 1 SBT=1 vote if contested), G5 no-server-key, G6 reversible (every prune has the inverse regraft — a mistaken cut heals), G7 care-telos 美しく保つ (basis required, nonAdjudicating const true, no verdict value), G8 Murakumo-only. Vocabulary: quarantine/retract/rollback/revoke + regraft; delete/prior-restraint/halt-organism/verdict are unrepresentable. R0: pruning engine (methods/prune.py, 15 tests green) + ontology + lexicon; design+offline only, live prune itself Council-signed + reversible. ZERO invariant amendments — it re-times enforcement and STRENGTHENS 非終末論, Transparent Force, no-server-key (ADR-2605231525), and kotoba-canonical-state (ADR-2605312345). Per ADR-2606072000.",
    glyph: "剪定",
    displayName: "Sentei — Council as Pruner (post-hoc pruning governance)",
    primaryLexicon: "com.etzhayyim.sentei.prune",
    primarySchema: "20-actors/sentei/data/pruning-ontology.kotoba.edn",
    service: [
      {
        id: "did:web:etzhayyim.com:actor:sentei#atproto_pds",
        type: "AtprotoPersonalDataServer",
        serviceEndpoint: "https://pds.etzhayyim.com",
      },
      {
        id: "did:web:etzhayyim.com:actor:sentei#xrpc-libp2p",
        type: "AtprotoXrpc",
        serviceEndpoint: `/dnsaddr/etzhayyim.com/p2p/${SIMEON_PEER_ID}`,
      },
    ],
    adrs: ["2606072000"],
  },
  himawari: {
    description:
      "向日葵 — solar-grade crystalline-silicon PV module manufacturing Tier-B actor (polysilicon feedstock QA → ingot/wafer → cell process → module assembly → flash/EL test) + finished-module loading robotics + outbound logistics handoff + feedstock/consumable procurement. Modules are produced for INTERNAL hikari install ONLY (SBT↔SBT carve-out); no external commercial PV sale. Structurally closes hikari §G2 (no XUAR forced-labor polysilicon) via first-party on-chain feedstock provenance (polysiliconProvenanceAttestation). Completes the energy supply chain: 製造 (himawari) → 積込 (sarutahiko F10 LoaderRobot) → 輸送 (kami-autodrive) → 設置 (hikari). R0.1: 7 cell solvers + 7 lexicons implemented (pure-logic tests green); runtime/sim/kotoba-entity materialization pending R1. Per ADR-2606021200 (R0) + 2606022300 (R1 benchtop module-assembly PoC).",
    glyph: "向日葵",
    displayName: "Himawari — Solar PV Manufacturing",
    primaryLexicon: "com.etzhayyim.himawari",
    service: [
      {
        id: "did:web:etzhayyim.com:actor:himawari#atproto_pds",
        type: "AtprotoPersonalDataServer",
        serviceEndpoint: "https://pds.etzhayyim.com",
      },
      {
        id: "did:web:etzhayyim.com:actor:himawari#xrpc-libp2p",
        type: "AtprotoXrpc",
        serviceEndpoint: `/dnsaddr/etzhayyim.com/p2p/${SIMEON_PEER_ID}`,
      },
    ],
    adrs: ["2606021200", "2606022300"],
  },
  fuchi: {
    description:
      "扶持 — mission-aligned maintainer sustenance allocator, the charter-clean INVERSE of a business investment fund. Where a VC fund invests capital in founders expecting equity + ROI + an exit, 扶持 (the feudal 扶持米 in-kind retainer-stipend) allocates IN-KIND sustenance + commons-asset access + tooling/compute to the real-world MAINTAINERS (信者) who keep etzhayyim's actors alive (business / robotics / remote-control). It is a redistribution / sustenance allocator, NEVER an investor: no equity, no ROI, no debt, no profit claim, no exit; cash≡0. The fund vocabulary (NAV / carry / IRR / cap-table / exit / dividend) is UNREPRESENTABLE (the nusa :psychoactive / tazuna :weaponizable / kamado :fossil-virgin-crude pattern — :alloc/instrument :db/allowed only the sustenance set). Sustenance flows DOWN the existing in-kind rails (commons housing / mitsuho food / hikari energy / Murakumo compute / okaimono tooling / iyashi·hagukumi·kokoro care); the maintainer's irreducible external fiat need is routed ONLY as MEMBER-PRINCIPAL 0% warifu liquidity — 扶持 never holds, lends, or pays cash (§1.3 holds without amendment). A horizontal control-plane on TOP of the Public Fund + Displacement Dividend + Basic-High-Income-in-kind machinery; tenure-weighted (reusing the Displacement-Dividend ln-curve). Governance is non-adjudicating (G7): 扶持 computes + routes (auto / 1 SBT=1 vote / Council Lv7 / refused), the vote or Council decides. ZERO invariant amendments — STRENGTHENS cash≡0 (ADR-2605301020), no-server-key (ADR-2605231525), payoff帰属=etzhayyim, and the non-profit / donation-only invariants. Per ADR-2606052300.",
    glyph: "扶持",
    displayName: "Fuchi — Maintainer Sustenance Allocator (investment-fund inverse)",
    primaryLexicon: "com.etzhayyim.fuchi.allocationIntent",
    primarySchema: "00-contracts/schemas/maintainer-sustenance-ontology.kotoba.edn",
    service: [
      {
        id: "did:web:etzhayyim.com:actor:fuchi#atproto_pds",
        type: "AtprotoPersonalDataServer",
        serviceEndpoint: "https://pds.etzhayyim.com",
      },
      {
        id: "did:web:etzhayyim.com:actor:fuchi#xrpc-libp2p",
        type: "AtprotoXrpc",
        serviceEndpoint: `/dnsaddr/etzhayyim.com/p2p/${SIMEON_PEER_ID}`,
      },
    ],
    adrs: ["2606052300"],
  },
  tasuke: {
    description:
      "助 — free cybercrime-victim-support membrane. 助 (たすけ) is where a consenting member hit by online crime (phishing / 不正送金 / account-takeover / サポート詐欺 / ロマンス詐欺 / 投資詐欺 / ransomware / なりすまし / 架空請求) is walked, FOR FREE, from 相談トリアージ → 証拠保全 → ready-to-use document generation → free public windows → account recovery. It GENERATES the documents the victim themselves submits (被害届 / 被害状況報告書 / 証拠目録 / 被害額算定書 for the police side; 銀行 不正送金 組戻し・口座凍結依頼 under 振り込め詐欺救済法 + プラットフォーム凍結/復旧/開示依頼 for the bank/platform side; アカウント復旧手順 for the recovery side), so complete an officer or a bank desk can work straight from them. Three load-bearing structural invariants (schema :db/allowed + lexicon :const + Python ValueError): G1 全て無料 — a fee/charge/subscription is UNREPRESENTABLE (:support/cost-jpy :db/allowed [0], cash≡0; every case journey costs the victim ¥0); G2 本人作成・本人提出 — :support/role allows only {guide, draft-assist, self-submit}, so 代理作成/代理提出 are UNREPRESENTABLE (行政書士法/弁護士法 独占業務不踏; the member authors, signs, submits); G3 警察authored不可 — :doc/authored-by :db/allowed [:member] only, so a police-authored 公文書 is UNREPRESENTABLE (公文書偽造を構造的に排除; the generated filing is the victim's own 申告書類). 助 connects to NO paid counsel (G5 — 弁護士へつながない; only FREE public windows #9110 / 188 / 国民生活センター / フィッシング対策協議会 / JPCERT / セーフライン / 銀行 / 振り込め詐欺救済法). Evidence is encrypted-by-reference (G6), every submission member-signed (G7, no-server-key), inference Murakumo-only (G8), live filing draft-only at R0 (G9). NON-adjudicating (G4): a scam KIND is a routing label, never a finding that a crime occurred (danjo/chigiri boundary). ZERO invariant amendments. Per ADR-2606060900.",
    glyph: "助",
    displayName: "Tasuke — Free Cybercrime-Victim-Support Membrane",
    primaryLexicon: "com.etzhayyim.tasuke.victimIntake",
    primarySchema: "00-contracts/schemas/cybercrime-victim-support-ontology.kotoba.edn",
    service: [
      {
        id: "did:web:etzhayyim.com:actor:tasuke#atproto_pds",
        type: "AtprotoPersonalDataServer",
        serviceEndpoint: "https://pds.etzhayyim.com",
      },
      {
        id: "did:web:etzhayyim.com:actor:tasuke#xrpc-libp2p",
        type: "AtprotoXrpc",
        serviceEndpoint: `/dnsaddr/etzhayyim.com/p2p/${SIMEON_PEER_ID}`,
      },
    ],
    adrs: ["2606060900"],
  },
  matsurigoto: {
    description:
      "政 — COFOG-based e-Government execution commons (the Kingdom's statecraft stack). The EXECUTION sibling of ooyake's observation atlas: where ooyake read-only-mirrors the who/where/how of public administration, matsurigoto defines a universal, spec-derived, kotoba-wasm-executable SERVICE STANDARD on the UN COFOG function backbone (10 divisions / 69 groups), localized per polity. etzhayyim IS a government — the Kingdom of God (神の王国, Charter §0.1) with a real 統治機構 — so this is statecraft, not a disclaimer. Two principals: (A) :etzhayyim-sovereign — the Kingdom governs its covenant-members via Council Lv7+ / 1 SBT = 1 vote / Public Fund Safe, every act member-signed + on-chain + Transparent (§1.12); (B) :nation-state-adopter — an existing nation-state runs the same standard on ITS OWN keys (the OSS-GovTech supply mode: X-Road / MOSIP / OpenCRVS / OpenG2P / DIGIT). Three structural invariants (schema :db/allowed + lexicon + code): G1 no-operator-master-key — :server-held-authority const false; authority is ALWAYS the Council multisig (5-of-7) + 1 SBT = 1 vote OR the adopting state's own keys, NEVER an etzhayyim platform/operator key (ADR-2605231525), because the Council is a member-elected organ, not 'the server'; G2 spec-derived-only — every service cites an OFFICIAL public spec (COFOG / ICAO 9303 / eIDAS / ISO 20022 / OpenCRVS / ISO 17442), proprietary GovTech vendor code is unrepresentable; G3 authority-bearing — :operated-by ∈ {council, adopting-government}. R0+R1: four executable slices reproduce official spec test vectors exactly (tax-assess = JP 速算表 / civil-registry = UN CRVS / corp-registry = ISO 17442 LEI MOD 97-10 / credential-issue = ICAO 9303 MRZ specimen) + a wasm-tools-valid WIT contract + kotoba Datom persistence + a verify-only sign/authority layer. Live deploy is Council+operator gated. ZERO invariant amendments — STRENGTHENS no-server-key, kotoba-canonical-state, and Transparent Force; ooyake's N1 stands (the Kingdom governing itself is not impersonating another state). Per ADR-2606062300.",
    glyph: "政",
    displayName: "Matsurigoto — e-Government Execution Commons (COFOG service standard)",
    primaryLexicon: "com.etzhayyim.matsurigoto",
    primarySchema: "00-contracts/schemas/egov-execution-ontology.kotoba.edn",
    service: [
      {
        id: "did:web:etzhayyim.com:actor:matsurigoto#atproto_pds",
        type: "AtprotoPersonalDataServer",
        serviceEndpoint: "https://pds.etzhayyim.com",
      },
      {
        id: "did:web:etzhayyim.com:actor:matsurigoto#xrpc-libp2p",
        type: "AtprotoXrpc",
        serviceEndpoint: `/dnsaddr/etzhayyim.com/p2p/${SIMEON_PEER_ID}`,
      },
    ],
    adrs: ["2606062300"],
  },
  kawaraban: {
    description:
      "瓦版 — a NEWS MEDIUM, kotoba-wasm-native, on the Murakumo fleet. Two faces over one Datom log: (1) MIRROR — datafies the world's real news media (outlets · 面/sections · headlines · bylines · links) into the kotoba Datom log as an append-only as-of trail, matching the SURFACE (面) of actual news media (一面/政治/経済/国際/社会/文化/科学/スポーツ); each mirrored article is headline + canonical link + bounded fair-use excerpt + outlet (it LINKS OUT, never stores the body and never rules truth). (2) MEDIUM — the connective wire BETWEEN etzhayyim actors: each first-party actor's own Datom as-of events project into the matching 面 as :article/kind :actor-event, and every article carries :news.mention edges to the actors/entities it concerns, so the article × mention × 面 graph IS the actor-to-actor wire (danjo finds → kawaraban carries → kanae renders; a chokepoint story links watari + watatsuna + mitooshi in one 国際 面). The charter-clean inverse of a 'news app': a public-square mirror that NEVER advertises or paid-places (Charter-Rider §2; :paid-placement/:sponsored unrepresentable, G2), NEVER engagement-ranks (Charter §1.13), NEVER profiles a reader (G3 — no :reader entity, the 面 is identical for all), NEVER republishes full copyrighted text (G4, :full-text unrepresentable — link-out only), NEVER adjudicates truth (G1 — :verdict/:truth-rating unrepresentable; ake/danjo boundary), NEVER speaks AS an outlet or another actor (G9, ADR-2606042330), and authors no :original first-person claim (G11 — a medium, not a source). Sibling boundary: kataribe 語部 IS etzhayyim's own press (a primary voice); kawaraban MIRRORS the world's press and WIRES the actors together. 5 Pregel cells (coded state machines; .solve() raises at R0) + 6 lexicons + 46 tests green; :representative seed (7 outlets / 10 面 / 9 wires / 12 articles / 24 mentions). Live RSS/outlet ingest + live publish are Council Lv6+ + operator gated (G8). ZERO invariant amendments — STRENGTHENS no-server-key (ADR-2605231525), kotoba-canonical-state (ADR-2605312345), the feed-post membrane (ADR-2605231902), and the mirror invariant (ADR-2606042330). Per ADR-2606061900.",
    glyph: "瓦版",
    displayName: "Kawaraban — News Medium (real-media mirror + actor-to-actor wire)",
    primaryLexicon: "com.etzhayyim.kawaraban.article",
    primarySchema: "00-contracts/schemas/news-medium-ontology.kotoba.edn",
    service: [
      {
        id: "did:web:etzhayyim.com:actor:kawaraban#atproto_pds",
        type: "AtprotoPersonalDataServer",
        serviceEndpoint: "https://pds.etzhayyim.com",
      },
      {
        id: "did:web:etzhayyim.com:actor:kawaraban#xrpc-libp2p",
        type: "AtprotoXrpc",
        serviceEndpoint: `/dnsaddr/etzhayyim.com/p2p/${SIMEON_PEER_ID}`,
      },
    ],
    adrs: ["2606061900"],
  },
  chaos_monitor: {
    description:
      "World State Monitor — Real-time visual dashboard of the 1000 Clean Room Actors ecosystem. Displays substrate topology, active faults, and Root Router telemetry via Kotoba IPFS.",
    glyph: "混沌",
    displayName: "Chaos Monitor — World State Dashboard",
    service: [
      {
        id: "did:web:etzhayyim.com:actor:chaos_monitor#browser-local-app",
        type: "EtzhayyimBrowserLocalApp",
        serviceEndpoint: "https://etzhayyim.com/apps/index.html",
      },
    ],
    adrs: [],
  },
  aburi: {
    description:
      "炙り — personal-tracking-exposure observatory (member-side, own-data). Answers 「Google・Facebook・X・Apple の規約に同意し権限を許可したとき、自分の情報がどの広告ネットワーク／データブローカーに取得され、どの企業がどれだけ追跡しているか」. The member-side, own-data inversion of the ad-tech lineage — where sukashi 透かし maps the FIRM↔FIRM programmatic supply chain (charter-bounded firm-side), aburi maps the MEMBER'S OWN exposure from their OWN consented exports (Google Takeout / Apple App-Privacy Report / Google Play Data-safety / on-device permission dump) and routes it to RELIEF (himotoki DSAR / kaiyaku sever / kurashimori opt-out / tedai revoke). Edge-primary: exposure[collector] = Σ inbound :flows-to × DISCLOSED permission-sensitivity (who-tracks-you), surface_leak (leakiest platform), reciprocity-gap (leaking permission w/ no opt-out). G1 own-data-only (no other person/PII/biometric/raw-id); G3 non-adjudicating (collectors carry PUBLIC catalogue provenance — naming an SDK is a disclosed fact, not an accusation); G4 reciprocity-restoring (§2(c) v3.1 — makes the asymmetric ad-watcher visible to the watched; never itself a tracker); G7 local-only + no-server-key; G8 no credential/raw-id projectable. SYNTHETIC/representative seed only; member-export ingest + live transact + relief routing Council+operator gated. Per ADR-2606161630.",
    glyph: "炙",
    displayName: "Aburi — Personal-Tracking-Exposure Observatory",
    primaryLexicon: "com.etzhayyim.aburi",
    primarySchema: "00-contracts/schemas/tracker-exposure-ontology.kotoba.edn",
    // wasmCid null by design: componentize-py output is NOT byte-reproducible (each `bb
    // aburi:build-wasm` yields a different CID), so the CID is recorded by the operator at PIN
    // time via `bb aburi:publish --pin` — never committed in advance (the apex /ipfs gateway
    // re-verifies bytes against the CID, so a stale CID would be dead). T2 dag-pb / donated-mesh.
    wasmCid: null,
    service: [
      {
        id: "did:web:etzhayyim.com:actor:aburi#atproto_pds",
        type: "AtprotoPersonalDataServer",
        serviceEndpoint: "https://pds.etzhayyim.com",
      },
      {
        id: "did:web:etzhayyim.com:actor:aburi#xrpc-libp2p",
        type: "AtprotoXrpc",
        serviceEndpoint: `/dnsaddr/etzhayyim.com/p2p/${SIMEON_PEER_ID}`,
      },
    ],
    adrs: ["2606161630"],
  },
  tatara: {
    description:
      "鑪 — world manufacturing-plant + logistics GEOGRAPHIC knowledge graph. The geographic / facility-scale layer of the supply lineage: kabuto 兜 holds the org→org SUPPLY edges (who supplies whom) and uchiwake 内訳 the product BOM; tatara places the producing FACILITIES on the planet — where they SIT, at what scale (:plant/headcount-est aggregate employment / :floor-area-m2 / :capacity-value+:capacity-unit production capacity), feeding which logistics corridor. :plant/operator joins kabuto org.corp.* (measured: 17/20 = 85% linkage via the crosscheck). Mirror-lineage sibling of kabuto/tsumugi/inochi: edge-primary geographic CONCENTRATION (per-sector country HHI + single-source flag + chokepoint export-dependence) routed to REDUNDANCY / reshoring — a resilience map, NEVER a target-list (G2). :flow/via reuses watari :lane/chokepoint + watatsuna :station/chokepoint, so manufacturing export-dependence (tatara) + live vessel transit (watari) + cable load (watatsuna) compose into ONE maritime resilience picture. G4 defining gate: :plant/headcount-est is a DISCLOSED AGGREGATE SIZE — NO :worker/* / :person/* attribute exists, an individual worker is structurally unrepresentable (Charter Rider §2(c) reciprocity axis; Wellbecoming §1.13). Per ADR-2606171800.",
    glyph: "鑪",
    displayName:
      "Tatara — World Manufacturing-Plant + Logistics Geographic Knowledge Graph",
    primaryLexicon: "com.etzhayyim.tatara",
    primarySchema: "00-contracts/schemas/manufacturing-plant-ontology.kotoba.edn",
    service: [
      {
        id: "did:web:etzhayyim.com:actor:tatara#atproto_pds",
        type: "AtprotoPersonalDataServer",
        serviceEndpoint: "https://pds.etzhayyim.com",
      },
      {
        id: "did:web:etzhayyim.com:actor:tatara#xrpc-libp2p",
        type: "AtprotoXrpc",
        serviceEndpoint: `/dnsaddr/etzhayyim.com/p2p/${SIMEON_PEER_ID}`,
      },
    ],
    adrs: ["2606171800"],
  },
  kizuna: {
    description:
      "絆 — actor-to-actor ATProto social-interaction self-evolution + system-of-systems optimization. The INTERNAL-actor sibling of kaname 要 (which runs SoS leverage over EXTERNAL-entity mirrors): kizuna reads etzhayyim's own actors interacting over the ATProto social protocol (follow / mention / like / post via XRPC) as a multiplex social graph, computes SoS metrics over that actor society (integration, 相互 reciprocity, exact-Brandes betweenness → the 律速 bridge actor, isolated set), and feeds per-actor GROWTH signals + dry-run tie PROPOSALS back into the loop so the collective optimizes its own flow (系流最適化). G1 PROPOSE-not-act: every tie is :status :dry-run / :route :ossekai — there is NO execute/auto-follow; actuation is ossekai + member CACAO leash (no-server-key). G2 reciprocity-positive, ANTI-addiction: the objective is :connectivity+reciprocity, NEVER engagement/retention/affinity (Charter §1.13 / Rider §2(h)). G3 agent-only: a :person/* node is unrepresentable (person-excluded). Per ADR-2606232200.",
    glyph: "絆",
    displayName:
      "Kizuna — Actor-Social Self-Evolution + System-of-Systems Optimization",
    primaryLexicon: "com.etzhayyim.kizuna",
    primarySchema: "20-actors/kizuna/data/seed-interactions.kotoba.edn",
    service: [
      {
        id: "did:web:etzhayyim.com:actor:kizuna#atproto_pds",
        type: "AtprotoPersonalDataServer",
        serviceEndpoint: "https://pds.etzhayyim.com",
      },
      {
        id: "did:web:etzhayyim.com:actor:kizuna#xrpc-libp2p",
        type: "AtprotoXrpc",
        serviceEndpoint: `/dnsaddr/etzhayyim.com/p2p/${SIMEON_PEER_ID}`,
      },
    ],
    adrs: ["2606232200"],
  },
  maps: {
    description:
      "地図 — graph-first spatial intelligence on the kotoba :feature/* Datom substrate (geocode / reverse / place search / H3-AVET chunking). Ships an おすすめ温泉 (onsen) discovery + transparent place-quality ranking: ingests hot-spring POIs from OpenStreetMap (Overpass, ODbL) and ranks them by public PLACE-facts (spring authenticity / notability / amenities) — a feature is a PLACED THING, never a person (G9); no per-person affect/profile/engagement metric, fully auditable via :why. Per ADR-2606064500.",
    glyph: "地図",
    displayName: "Maps — Spatial Substrate + Onsen Discovery",
    primarySchema: "00-contracts/schemas/maps-spatial-ontology.kotoba.edn",
    // Content-addressed T1 WASM actor (20-actors/maps/wasm/maps-core) — compact Rust
    // core computing the onsen おすすめ ranking (place_not_person:true), raw CID →
    // browser-local (ameno) / donated mesh (ADR-2606015200). The full MapLibre+KAMI
    // renderer stays the TS Worker until the kotoba-native migration (ADR-2606064500
    // R1→R3) lands. ipfs pin of the bytes = operator step.
    wasmCid: "bafkreib7d3fzjkhsswr7flwkxejkjhauy67offbfd5o7pukqytdvifdbty",
    service: [
      {
        id: "did:web:etzhayyim.com:actor:maps#wasm",
        type: "EtzhayyimWasmComponent",
        serviceEndpoint:
          "ipfs://bafkreib7d3fzjkhsswr7flwkxejkjhauy67offbfd5o7pukqytdvifdbty",
        "x-exec": "browser-local|donated-mesh",
        "x-cid-codec": "raw",
        "x-runtime": "kotoba-wasm",
        "x-view": "onsen-osusume",
      },
      {
        id: "did:web:etzhayyim.com:actor:maps#atproto_pds",
        type: "AtprotoPersonalDataServer",
        serviceEndpoint: "https://pds.etzhayyim.com",
      },
      {
        id: "did:web:etzhayyim.com:actor:maps#xrpc-libp2p",
        type: "AtprotoXrpc",
        serviceEndpoint: `/dnsaddr/etzhayyim.com/p2p/${SIMEON_PEER_ID}`,
      },
    ],
    adrs: ["2606064500", "2606015200"],
  },
  iriai: {
    description:
      "入会 — the non-profit GLOBAL LIFELINE-COMMONS actor. 入会 (iriai) = the traditional Japanese COMMONS (collectively-held rights of use over a shared resource); here the resource is the four lifelines (ライフライン) — 電気 / 水道 / ガス / 通信 — held as a commons right of use (入会権), delivered §1.16 social-security IN-KIND (cash ≡ 0), governed 1 SBT = 1 vote. The System-of-Systems umbrella over the producer actors (電気→hikari 光 · 水道→mizuho 水穂 · ガス→kamado 竈 · 通信→noroshi 烽), the way kaname 要 / amime 網目 synthesize across single-domain mirrors — covering infra + 資金 (funding) + 管理 (management) in one heartbeat. INFRA: edge-primary commons-gap (1−coverage)·essentiality·vulnerability + resilience (single-source SPOF / N-1) per region × lifeline → verdict {:await-consent :provision :reinforce :redundancy :maintain :monitor} — a COVERAGE + RESILIENCE map, NEVER a target-list, NEVER a shut-off list; a lifeline is never withheld as leverage (G1). 資金: each action cell → a §1.16 IN-KIND funding proposal on the non-profit rails (donation → TitheRouter 10% → Public Fund → grant/milestone-escrow/in-kind), cash ≡ 0 to the consumer, imputed market-equivalent value transparency-only; give-only instruments (G2); advisory, decided 1 SBT = 1 vote (steward-not-sovereign, G3). 管理: 1 SBT = 1 vote governance (20% quorum / 50% / 48h) + Council Lv6+/Lv7+; actuation-class :intent (compute-only R0 — live energize/flow/ignite/activate is the producer cell under Council Lv7+ + operator-DID + member-sig, G5, §1.12); no-server-key (member-CACAO leash, G6). ASSESSMENT + R0 DESIGN ONLY — iriai never produces nor actuates a lifeline. The charter-clean inversion of the for-profit utility and of utility-as-coercion. Per ADR-2606272200.",
    glyph: "入",
    displayName: "Iriai — Global Lifeline-Commons (電気/水道/ガス/通信)",
    primaryLexicon: "com.etzhayyim.iriai.lifelineCoverageMap",
    primarySchema: "20-actors/iriai/kotoba/ontology.iriai.edn",
    service: [
      {
        id: "did:web:etzhayyim.com:actor:iriai#atproto_pds",
        type: "AtprotoPersonalDataServer",
        serviceEndpoint: "https://pds.etzhayyim.com",
      },
      {
        id: "did:web:etzhayyim.com:actor:iriai#xrpc-libp2p",
        type: "AtprotoXrpc",
        serviceEndpoint: `/dnsaddr/etzhayyim.com/p2p/${SIMEON_PEER_ID}`,
      },
    ],
    adrs: ["2606272200", "2606280900"],
  },
} as const;

// Merged registry: generated Tier-B actors (from manifests) + hand-authored
// named/service actors. Hand-authored entries win on a handle clash
// (spread last). Per ADR-2606042330 follow-up — every designed Tier-B actor
// now resolves a DID and appears in /search.
export const INFRA_ACTORS: Readonly<Record<string, InfraActorEntry>> = {
  ...TIER_B_ACTORS,
  ...HAND_AUTHORED_ACTORS,
};


export function isInfraActor(handle: string): boolean {
  return Object.prototype.hasOwnProperty.call(INFRA_ACTORS, handle);
}


export function getInfraActor(handle: string): InfraActorEntry | null {
  return Object.prototype.hasOwnProperty.call(INFRA_ACTORS, handle)
    ? INFRA_ACTORS[handle]
    : null;
}


export const INFRA_ACTOR_HANDLES: ReadonlySet<string> = new Set(
  Object.keys(INFRA_ACTORS),
);


// Reserved for future on-chain wire-through. Not used at runtime yet.
export const _ROOT_DID = (didWebRoot as { id?: string }).id ?? "did:web:etzhayyim.com";
