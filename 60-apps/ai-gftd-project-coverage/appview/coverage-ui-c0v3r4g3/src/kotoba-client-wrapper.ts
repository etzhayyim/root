// ADR-2606021730: RisingWave → kotoba Datom log migration for latent-entity resolution
// This adapter bridges legacy RW vertex/edge queries to kotoba-native EAVT queries.
//
// Constitutional gates: G2 (edge-primary), G6 (Murakumo-only), G14 (verified-procedure).
// Honest R0 status: fixture-mode only. Live kotoba endpoint and full LDA deferred to P2-full (ADR-2605262130).

export interface LatentEntityRow {
  vertex_id: string;
  entity_kind: string;
  canonical_label: string;
  existence_probability: number;
  k_evidence_count: number;
  viewpoint_consensus: number;
  fission_eligible: boolean;
  status: string;
  created_at: string;
}

export interface EvidenceRow {
  edge_id: string;
  src_vid: string;
  dst_vid: string;
  created_at: string;
}

export interface TopicRow {
  vertex_id: string;
  topic_index: number;
  topic_label: string;
  coherence_score: number;
  top_signal_count: number;
  entity_kind_hint: string;
}

export interface EntityStats {
  entity_kind: string;
  total: number;
  avg_probability: number;
  fission_ready_count: number;
}

// Phase 2: Implement queryLatentEntities using kotoba kqe queries (EAVT mode)
// Replaces RisingWave `vertex_latent_entity` query.
export async function queryLatentEntities(
  kotobaClient: any, // @etzhayyim/sdk KotobaClient (deferred to operator gate)
  options?: {
    entityKind?: string;
    fissionOnly?: boolean;
    limit?: number;
    offset?: number;
  }
): Promise<{ entities: LatentEntityRow[]; total: number }> {
  const limit = Math.min(options?.limit ?? 50, 200);
  const offset = options?.offset ?? 0;

  // HONEST R0: Fixture mode queries (no live kotoba endpoint)
  // Live kotoba kqe queries would be:
  // const aevt = await kotobaClient.kqe_aevt(
  //   e => e.entity === `:latent/entity`,
  //   { filters: [
  //       ...(options?.entityKind ? [{ a: `:latent/entity-kind`, v: options.entityKind }] : []),
  //     ],
  //     limit, offset
  //   }
  // );

  // Then aggregate :en/evidence edges to compute existence_probability on-read (G2 edge-primary, N1):
  // const entities = aevt.map(e => {
  //   const evidences = await kotobaClient.kqe_avet(`:en/evidence`, { a: e.entity });
  //   const existence = noisy_or_aggregate(evidences); // noisy-OR from 20-actors/tsumugi/methods/resolve.py
  //   return { ...e, existence_probability: existence };
  // });

  // For now, return fixture data (placeholder)
  const fixtureEntities: LatentEntityRow[] = [];
  return {
    entities: fixtureEntities,
    total: 0,
  };
}

// Phase 3: Implement queryEntityEvidence using kotoba kqe queries
// Replaces RisingWave `edge_entity_evidence` query.
export async function queryEntityEvidence(
  kotobaClient: any,
  entityVid: string,
  limit: number = 50
): Promise<{ evidence: EvidenceRow[]; count: number }> {
  limit = Math.min(limit, 200);

  // HONEST R0: Fixture mode
  // Live query would be:
  // const evidence = await kotobaClient.kqe_avet(
  //   `:en/evidence`,
  //   { filters: [{ dst: entityVid }], limit }
  // );
  // return { evidence, count: evidence.length };

  return { evidence: [], count: 0 };
}

// Phase 4: Implement getViewpointStats using kotoba EAVT aggregates
// Replaces RisingWave `vertex_lda_viewpoint` + `vertex_latent_entity` GROUP BY queries.
export async function getViewpointStats(
  kotobaClient: any
): Promise<{
  viewpoints: { vertex_id: string; viewpoint_kind: string; description: string; signal_vocab_size: number; active: boolean; created_at: string }[];
  entityStats: EntityStats[];
}> {
  // HONEST R0: Fixture mode
  // Live queries would:
  // 1. Fetch all :topic/* entities (viewpoints) filtered by active=true
  // 2. Aggregate :latent/* entities by :latent/entity-kind, computing avg existence + fission-ready count

  return {
    viewpoints: [],
    entityStats: [],
  };
}

// Helper: Noisy-OR aggregation (G2 edge-primary)
// Replicates deterministic logic from 20-actors/tsumugi/methods/resolve.py
function noisy_or_aggregate(evidences: { confidence: number }[]): number {
  if (evidences.length === 0) return 0;
  // Noisy-OR: 1 - ∏(1 - p_i)
  const product = evidences.reduce((acc, e) => acc * (1 - e.confidence), 1);
  return 1 - product;
}

// Factory: Create a wrapped kotoba client adapter
// (Deferred: actual @etzhayyim/sdk integration, operator-gated at G11/G14)
export function createKotobaClientAdapter(endpoint?: string): any {
  // Placeholder for operator-gated client initialization
  return {
    kqe_aevt: async () => [],
    kqe_avet: async () => [],
  };
}
