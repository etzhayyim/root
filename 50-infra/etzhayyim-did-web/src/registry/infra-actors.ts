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
export const INFRA_ACTORS: Readonly<Record<string, InfraActorEntry>> = {
  pinner: {
    description:
      "MST CAR pinner — pins shard CARs produced by mst-projector to IPFS. Per ADR-2605171800 Stage 4.",
    primaryLexicon: "app.etzhayyim.substrate.ipfsPin",
    service: [
      {
        id: "did:web:etzhayyim.com:actor:pinner#atproto_pds",
        type: "AtprotoPersonalDataServer",
        serviceEndpoint: "https://pds.etzhayyim.com",
      },
      {
        id: "did:web:etzhayyim.com:actor:pinner#xrpc-https-legacy",
        type: "AtprotoXrpc",
        serviceEndpoint: "https://pinner.etzhayyim.com",
        "x-deprecated-at": "Phase C (per ADR-2605241800)",
      },
    ],
    adrs: ["2605171800"],
  },
  esign: {
    description:
      "Document-signing actor — issues, collects, completes app.etzhayyim.esign.* envelopes. Per ADR-2605231230.",
    primaryLexicon: "app.etzhayyim.esign",
    service: [
      {
        id: "did:web:etzhayyim.com:actor:esign#atproto_pds",
        type: "AtprotoPersonalDataServer",
        serviceEndpoint: "https://pds.etzhayyim.com",
      },
      {
        id: "did:web:etzhayyim.com:actor:esign#xrpc-https-legacy",
        type: "AtprotoXrpc",
        serviceEndpoint: "https://esign.etzhayyim.com",
        "x-deprecated-at": "Phase C (per ADR-2605241800)",
      },
    ],
    adrs: ["2605231230"],
  },
  audit: {
    description:
      "Audit-event aggregator — substrate-wide app.etzhayyim.audit.event sink referenced by every actor manifest. Per ADR-2605231700 + 2605231900.",
    primaryLexicon: "app.etzhayyim.audit.event",
    service: [
      {
        id: "did:web:etzhayyim.com:actor:audit#atproto_pds",
        type: "AtprotoPersonalDataServer",
        serviceEndpoint: "https://pds.etzhayyim.com",
      },
      {
        id: "did:web:etzhayyim.com:actor:audit#xrpc-https-legacy",
        type: "AtprotoXrpc",
        serviceEndpoint: "https://audit.etzhayyim.com",
        "x-deprecated-at": "Phase C (per ADR-2605241800)",
      },
    ],
    adrs: ["2605231700", "2605231900"],
  },
  "dataset-pinner": {
    description:
      "Dataset pinner — mirrors DataLad/git-annex `directory` remote objects to IPFS and emits app.etzhayyim.substrate.datasetPin records. Per ADR-2605241500.",
    primaryLexicon: "app.etzhayyim.substrate.datasetPin",
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
      {
        id: "did:web:etzhayyim.com:actor:dataset-pinner#xrpc-https-legacy",
        type: "AtprotoXrpc",
        serviceEndpoint: "https://dataset-pinner.etzhayyim.com",
        "x-deprecated-at": "Phase C (per ADR-2605241800)",
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
      {
        id: "did:web:etzhayyim.com:actor:anchorer#xrpc-https-legacy",
        type: "AtprotoXrpc",
        serviceEndpoint: "https://anchorer.etzhayyim.com",
        "x-deprecated-at": "Phase C (per ADR-2605241800)",
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
      {
        id: "did:web:etzhayyim.com:actor:projector#xrpc-https-legacy",
        type: "AtprotoXrpc",
        serviceEndpoint: "https://projector.etzhayyim.com",
        "x-deprecated-at": "Phase C (per ADR-2605241800)",
      },
    ],
    adrs: ["2605171800"],
  },
  karute: {
    description:
      "Karute electronic medical record actor (EMR / FHIR R5). PHI sealing mandatory. Per ADR-2605231100 + 2605231900.",
    primaryLexicon: "app.etzhayyim.apps.karute",
    service: [
      {
        id: "did:web:etzhayyim.com:actor:karute#atproto_pds",
        type: "AtprotoPersonalDataServer",
        serviceEndpoint: "https://pds.etzhayyim.com",
      },
      {
        id: "did:web:etzhayyim.com:actor:karute#xrpc-https-legacy",
        type: "AtprotoXrpc",
        serviceEndpoint: "https://karute.etzhayyim.com",
        "x-deprecated-at": "Phase C (per ADR-2605241800)",
      },
    ],
    adrs: ["2605231100", "2605231900"],
  },
  watatsuna: {
    description:
      "綿津綱 — world submarine-cable network knowledge graph. Datafies cable systems / landing stations / segments / fault bulletins into the kotoba Datom log; surfaces chokepoint single-point-of-failure concentration routed to redundancy + faster repair (a resilience map, NEVER a target-list — paired with watatsumi N8). Per ADR-2606012600.",
    glyph: "綿津綱",
    displayName: "Watatsuna — World Submarine-Cable Network Knowledge Graph",
    primaryLexicon: "app.etzhayyim.cable",
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
  tsumugi: {
    description:
      "紡ぎ — Engi Knowledge Graph (産霊の網) intel weaver. Runs Spirit-in-Physics (RBF emotion-kernel → spectral 3D embed → tensegrity) over real PUBLIC power-entities (法人 / institution / public-role) and their 縁 to surface 取-concentration (power held OVER others) routed to release. An aggregate-first accountability map, NEVER a target-list (powerless absent by construction; edge-primary karma N1 — no per-soul score). World-coverage; upper layer over danjo / kanae / tadori / himotoki. Per ADR-2606011800.",
    glyph: "紡ぎ",
    displayName: "Tsumugi — Engi Knowledge Graph (産霊の網) Intel Weaver",
    // No atproto lexicon: tsumugi emits kotoba EDN directly into the Datom log.
    primarySchema:
      "00-contracts/schemas/engi-organism-ontology.kotoba.edn (+ spirit-ontology.kotoba.edn)",
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
} as const;


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
