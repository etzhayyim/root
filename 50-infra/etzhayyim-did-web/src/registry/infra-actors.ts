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
