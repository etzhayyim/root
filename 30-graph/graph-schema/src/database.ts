/* eslint-disable */
/**
 * Kysely-compatible database types for the etzhayyim graph DB (RisingWave).
 *
 * GENERATED FILE - do not edit by hand.
 * Regenerate with: DATABASE_URL=... pnpm db:gen
 * Verify with:    DATABASE_URL=... pnpm db:drift
 *
 * Source: live RisingWave `information_schema.columns` via SQLAlchemy.
 * Schema SSoT is the DB itself; Alembic migrations and SQLMesh models are
 * the durable source of schema change. See `CLAUDE.md`.
 */

import type { ColumnType } from 'kysely';

// Silence unused-import warning when no generated column uses ColumnType.
type _KeepColumnType = ColumnType<never, never, never>;

// --- Row interfaces (one per table / view / MV) ---

export interface EdgeBusinessPersonRelationRow {
  edge_id?: string | null;
  src_person_id?: string | null;
  dst_person_id?: string | null;
  relation_type?: string | null;
  org_context?: string | null;
  direction?: string | null;
  strength?: string | null;
  since?: string | null;
  description?: string | null;
  source?: string | null;
  ingested_at?: string | null;
  confidence?: number | null;
  verification_status?: string | null;
}

export interface EdgeBusinessPersonSkillRow {
  edge_id?: string | null;
  person_vertex_id?: string | null;
  skill_id?: string | null;
  proficiency_level?: string | null;
  source?: string | null;
  ingested_at?: string | null;
}

export interface EdgeChatArtifactFromMessageRow {
  edge_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  src_vid?: string | null;
  dst_vid?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface EdgeChatInvocationFromMessageRow {
  edge_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  src_vid?: string | null;
  dst_vid?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface EdgeChatMessageInConversationRow {
  edge_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  src_vid?: string | null;
  dst_vid?: string | null;
  conv_id?: string | null;
  msg_id?: string | null;
  seq?: number | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface EdgeChatMessageRepliesToRow {
  edge_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  src_vid?: string | null;
  dst_vid?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface EdgeCohortAncestorOfRow {
  edge_id?: string | null;
  src_vid?: string | null;
  dst_vid?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | bigint | null;
  owner_did?: string | null;
  generation_offset?: number | null;
  temporal_gap_years?: number | null;
  confidence?: number | null;
  lineage_type?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
  at_did?: string | null;
  created_at?: string | null;
}

export interface EdgeCohortBeliefSystemRow {
  edge_id?: string | null;
  src_vid?: string | null;
  dst_vid?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | bigint | null;
  owner_did?: string | null;
  adherent_fraction?: number | null;
  dominance_rank?: number | null;
  actor_did?: string | null;
  org_did?: string | null;
  at_did?: string | null;
  created_at?: string | null;
}

export interface EdgeCompoundCrystalRow {
  edge_id?: string | null;
  compound_did?: string | null;
  crystal_did?: string | null;
  source?: string | null;
  created_at?: string | null;
}

export interface EdgeCompoundElementRow {
  edge_id?: string | null;
  compound_did?: string | null;
  element_sym?: string | null;
  element_did?: string | null;
  atom_count?: number | null;
  mass_pct?: number | null;
  created_at?: string | null;
}

export interface EdgeDatasetAllowedForTrainingTaskRow {
  edge_id?: string | null;
  src_vid?: string | null;
  dst_vid?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | bigint | null;
  owner_did?: string | null;
  dataset_id?: string | null;
  training_task?: string | null;
  license?: string | null;
  approved_by?: string | null;
  approved_at?: string | null;
  observed_at?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
  at_did?: string | null;
  created_at?: string | null;
}

export interface EdgeDatasetProducesVertexTypeRow {
  edge_id?: string | null;
  src_vid?: string | null;
  dst_vid?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | bigint | null;
  owner_did?: string | null;
  dataset_id?: string | null;
  target_vertex_label?: string | null;
  ingest_mode?: string | null;
  approved_by?: string | null;
  approved_at?: string | null;
  scan_budget_tib?: number | null;
  observed_at?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
  at_did?: string | null;
  created_at?: string | null;
}

export interface EdgeDomainRegistrarSupportsTldRow {
  edge_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  src_vid?: string | null;
  dst_vid?: string | null;
  registrar_slug?: string | null;
  tld?: string | null;
  verified_at?: string | null;
  handles_verification?: boolean | null;
  notes?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface EdgeDomainTldAcceptsRegulatorRow {
  edge_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  src_vid?: string | null;
  dst_vid?: string | null;
  tld?: string | null;
  regulator_slug?: string | null;
  basis?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface EdgeFamilyRelationRow {
  edge_id?: string | null;
  src_vid?: string | null;
  dst_vid?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | bigint | null;
  owner_did?: string | null;
  relation_type?: string | null;
  confidence?: number | null;
  effective_from?: string | null;
  effective_to?: string | null;
  source_app?: string | null;
  source_record_id?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface EdgeGameChartedAtRow {
  edge_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | bigint | null;
  owner_did?: string | null;
  src_vid?: string | null;
  dst_vid?: string | null;
  rank?: number | null;
  source?: string | null;
  week_start?: Date | string | null;
  created_at?: string | null;
}

export interface EdgeHfDatasetCollectionMemberRow {
  edge_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  src_vid?: string | null;
  dst_vid?: string | null;
  collection_id?: string | null;
  repo_id?: string | null;
  primary_modality?: string | null;
  training_stage?: string | null;
  rank_in_modality?: number | null;
  required_for_poc?: boolean | null;
  member_status?: string | null;
  rationale?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface EdgeHfDatasetReliabilityAboutRow {
  edge_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  src_vid?: string | null;
  dst_vid?: string | null;
  repo_id?: string | null;
  relation_kind?: string | null;
  confidence?: number | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface EdgeIntelDependencyRow {
  edge_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | bigint | null;
  owner_did?: string | null;
  src_vid?: string | null;
  dst_vid?: string | null;
  predicate?: string | null;
  dependency_kind?: string | null;
  confidence?: number | null;
  evidence_count?: number | bigint | null;
  evidence_json?: string | null;
  inference_run_id?: string | null;
  valid_from?: string | null;
  valid_to?: string | null;
  reason?: string | null;
  model_version?: string | null;
  status?: string | null;
  reviewed_by?: string | null;
  reviewed_at?: string | null;
  review_note?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface EdgeLifehackTipRecommendsProductRow {
  edge_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  src_vid?: string | null;
  dst_vid?: string | null;
  role?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface EdgeLifehackTipSolvesTopicRow {
  edge_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  src_vid?: string | null;
  dst_vid?: string | null;
  role?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface EdgeLifehackTopicRelatesToRow {
  edge_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  src_vid?: string | null;
  dst_vid?: string | null;
  role?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface EdgeLiveRoomLightingCueRow {
  edge_id?: string | null;
  _seq?: number | bigint | null;
  src_vid?: string | null;
  dst_vid?: string | null;
  start_bar?: number | bigint | null;
  created_at?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
  at_did?: string | null;
}

export interface EdgeLiveRoomTrackRow {
  edge_id?: string | null;
  _seq?: number | bigint | null;
  src_vid?: string | null;
  dst_vid?: string | null;
  position?: number | bigint | null;
  created_at?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
  at_did?: string | null;
}

export interface EdgeMalakControlsWalletRow {
  edge_id?: string | null;
  src_vid?: string | null;
  dst_vid?: string | null;
  sensitivity_ord?: number | bigint | null;
  owner_did?: string | null;
  created_date?: Date | string | null;
}

export interface EdgeMaterialElementRow {
  edge_id?: string | null;
  src_vid?: string | null;
  dst_vid?: string | null;
  weight_fraction?: number | null;
  created_at?: string | null;
  sensitivity_ord?: number | bigint | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  owner_did?: string | null;
  _seq?: number | bigint | null;
}

export interface EdgeMineralCrystalRow {
  edge_id?: string | null;
  mineral_did?: string | null;
  crystal_did?: string | null;
  source?: string | null;
  created_at?: string | null;
}

export interface EdgeMineralElementRow {
  edge_id?: string | null;
  mineral_did?: string | null;
  element_sym?: string | null;
  element_did?: string | null;
  mass_pct?: number | null;
  role?: string | null;
  created_at?: string | null;
}

export interface EdgeModelMaterialRow {
  edge_id?: string | null;
  src_vid?: string | null;
  dst_vid?: string | null;
  material_slot?: string | null;
  created_at?: string | null;
  sensitivity_ord?: number | bigint | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  owner_did?: string | null;
  _seq?: number | bigint | null;
}

export interface EdgeOtakiageItemHandoverRow {
  edge_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  src_vid?: string | null;
  dst_vid?: string | null;
  role?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface EdgeOtakiageItemOwnerRow {
  edge_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  src_vid?: string | null;
  dst_vid?: string | null;
  role?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface EdgeOtakiageItemRitualRow {
  edge_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  src_vid?: string | null;
  dst_vid?: string | null;
  role?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface EdgeOtakiageRitualCertificateRow {
  edge_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  src_vid?: string | null;
  dst_vid?: string | null;
  role?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface EdgePaperCompoundRow {
  edge_id?: string | null;
  paper_did?: string | null;
  compound_did?: string | null;
  mention_count?: number | null;
  created_at?: string | null;
}

export interface EdgePaperElementRow {
  edge_id?: string | null;
  src_vid?: string | null;
  dst_vid?: string | null;
  relation_kind?: string | null;
  created_at?: string | null;
  sensitivity_ord?: number | bigint | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  owner_did?: string | null;
  _seq?: number | bigint | null;
}

export interface EdgePaperProteinRow {
  edge_id?: string | null;
  paper_did?: string | null;
  protein_did?: string | null;
  mention_count?: number | null;
  created_at?: string | null;
}

export interface EdgePaperTaxonRow {
  edge_id?: string | null;
  src_vid?: string | null;
  dst_vid?: string | null;
  relation_kind?: string | null;
  confidence?: number | null;
  created_at?: string | null;
  sensitivity_ord?: number | bigint | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  owner_did?: string | null;
  _seq?: number | bigint | null;
}

export interface EdgeProteinElementRow {
  edge_id?: string | null;
  protein_did?: string | null;
  element_sym?: string | null;
  element_did?: string | null;
  role?: string | null;
  created_at?: string | null;
}

export interface EdgePublicDatasetCandidateForTrainingTaskRow {
  edge_id?: string | null;
  src_vid?: string | null;
  dst_vid?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | bigint | null;
  owner_did?: string | null;
  dataset_id?: string | null;
  training_task?: string | null;
  estimated_token_count?: number | bigint | null;
  estimated_image_count?: number | bigint | null;
  license_compatible?: string | null;
  pii_risk_ord?: number | bigint | null;
  review_status?: string | null;
  rationale?: string | null;
  observed_at?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
  at_did?: string | null;
  created_at?: string | null;
}

export interface EdgePublicDatasetCandidateForVertexTypeRow {
  edge_id?: string | null;
  src_vid?: string | null;
  dst_vid?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | bigint | null;
  owner_did?: string | null;
  dataset_id?: string | null;
  target_vertex_label?: string | null;
  column_mapping_json?: string | null;
  mapping_quality?: number | null;
  rationale?: string | null;
  review_status?: string | null;
  observed_at?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
  at_did?: string | null;
  created_at?: string | null;
}

export interface EdgePublicDatasetProfilesTableRow {
  edge_id?: string | null;
  src_vid?: string | null;
  dst_vid?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | bigint | null;
  owner_did?: string | null;
  profile_run_id?: string | null;
  dataset_id?: string | null;
  bytes_billed?: number | bigint | null;
  rows_scanned?: number | bigint | null;
  observed_at?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
  at_did?: string | null;
  created_at?: string | null;
}

export interface EdgeShoshaTradeCounterpartyRow {
  edge_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  src_vid?: string | null;
  dst_vid?: string | null;
  role?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface EdgeShoshaTradeHedgeRow {
  edge_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  src_vid?: string | null;
  dst_vid?: string | null;
  role?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface EdgeShoshaTradeSettlementRow {
  edge_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  src_vid?: string | null;
  dst_vid?: string | null;
  role?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface EdgeTaxonModelRow {
  edge_id?: string | null;
  src_vid?: string | null;
  dst_vid?: string | null;
  model_role?: string | null;
  confidence?: number | null;
  created_at?: string | null;
  sensitivity_ord?: number | bigint | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  owner_did?: string | null;
  _seq?: number | bigint | null;
}

export interface EdgeTrainingConsumedDatasetRow {
  edge_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  src_vid?: string | null;
  dst_vid?: string | null;
  role?: string | null;
  mix_ratio?: number | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface EdgeTrainingDistilledFromRow {
  edge_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  src_vid?: string | null;
  dst_vid?: string | null;
  teacher_kind?: string | null;
  distill_method?: string | null;
  temperature?: number | null;
  sample_count?: number | bigint | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface EdgeTrainingPromotedToRow {
  edge_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  src_vid?: string | null;
  dst_vid?: string | null;
  alias?: string | null;
  serving_target?: string | null;
  promoted_at?: string | null;
  retired_at?: string | null;
  promoted_by?: string | null;
  status?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface MvCompoundElementCoverageRow {
  element_sym?: string | null;
  compound_count?: number | bigint | null;
  first_edge_at?: string | null;
}

export interface MvCrystalCoverageRow {
  crystal_system?: string | null;
  structure_count?: number | bigint | null;
  first_at?: string | null;
}

export interface MvElementMaterialCoverageRow {
  symbol?: string | null;
  atomic_number?: number | bigint | null;
  category?: string | null;
  material_count?: number | bigint | null;
}

export interface MvGameGenreChartDominanceRow {
  genre_did?: string | null;
  source?: string | null;
  titles_in_chart?: number | bigint | null;
  avg_rank?: number | null;
  top_rank?: number | null;
  last_seen_week?: Date | string | null;
}

export interface MvGameRankTrendRow {
  title_did?: string | null;
  source?: string | null;
  weeks_charted?: number | bigint | null;
  avg_rank?: number | null;
  peak_rank?: number | null;
  best_rise?: number | null;
  worst_fall?: number | null;
  last_charted_week?: Date | string | null;
}

export interface MvHfDatasetQualityTopRow {
  collection_id?: string | null;
  primary_modality?: string | null;
  training_stage?: string | null;
  rank_in_modality?: number | null;
  repo_id?: string | null;
  license?: string | null;
  trust_score?: number | null;
  trust_tier?: string | null;
  decision?: string | null;
  commercial_use?: string | null;
  artifact_availability?: string | null;
  text_alignment?: string | null;
  hub_downloads_month?: number | bigint | null;
  hub_likes?: number | null;
  source_url?: string | null;
  observed_at?: string | null;
}

export interface MvIntelBuildingOwnerLeiRow {
  edge_id?: string | null;
  building_vid?: string | null;
  owner_vid?: string | null;
  lei?: string | null;
  owner_label?: string | null;
  confidence?: number | null;
  status?: string | null;
}

export interface MvIntelDependencyStatusRow {
  predicate?: string | null;
  status?: string | null;
  edge_count?: number | bigint | null;
  avg_confidence?: number | null;
}

export interface MvKaisyaPendingCountRow {
  human_did?: string | null;
  pending_count?: number | bigint | null;
  critical_count?: number | bigint | null;
  earliest_due_at?: Date | string | null;
  latest_task_at?: Date | string | null;
}

export interface MvKamiTileModelDensityRow {
  tile_h3?: string | null;
  model_kind?: string | null;
  instance_count?: number | bigint | null;
  model_def_count?: number | bigint | null;
  min_x?: number | null;
  max_x?: number | null;
  min_z?: number | null;
  max_z?: number | null;
}

export interface MvLegalCorpusJurisdictionCoverageRow {
  jurisdiction?: string | null;
  source_id?: string | null;
  document_count?: number | bigint | null;
  last_fetched_at?: string | null;
}

export interface MvMineralElementCompositionRow {
  mineral_did?: string | null;
  element_count?: number | bigint | null;
  first_edge_at?: string | null;
}

export interface MvNaturalPersonVitalStatsRow {
  era?: string | null;
  vital_status?: string | null;
  person_count?: number | bigint | null;
}

export interface MvOpenAdnetworkCampaignFunnelRow {
  campaign_id?: string | null;
  impressions?: number | bigint | null;
  clicks?: number | bigint | null;
  conversions?: number | bigint | null;
  ctr_pct?: number | null;
  cvr_pct?: number | null;
  total_spend_usd?: number | null;
}

export interface MvOpenAdnetworkMarketCpmRangeRow {
  unit_type?: string | null;
  unit_count?: number | bigint | null;
  min_floor_cpm?: number | null;
  avg_floor_cpm?: number | null;
  max_floor_cpm?: number | null;
}

export interface MvOpenAdnetworkPublisherDailyKpiRow {
  publisher_did?: string | null;
  date?: string | null;
  impressions?: number | bigint | null;
  clicks?: number | bigint | null;
  conversions?: number | bigint | null;
  total_revenue_usd?: number | null;
  rpm_usd?: number | null;
  ctr_pct?: number | null;
  cvr_pct?: number | null;
}

export interface MvOpenSalesActivitySummaryRow {
  opp_did?: string | null;
  kind?: string | null;
  activity_count?: number | bigint | null;
}

export interface MvOpenSalesPipelineHealthRow {
  stage?: string | null;
  opp_count?: number | bigint | null;
  total_pipeline_usd?: number | null;
  avg_probability_pct?: number | null;
  weighted_usd?: number | null;
}

export interface MvOpenSalesStageVelocityRow {
  stage?: string | null;
  opp_count?: number | bigint | null;
  avg_deal_size_usd?: number | null;
  won_count?: number | bigint | null;
  lost_count?: number | bigint | null;
}

export interface MvOpenSmartphonePatentFreeZoneRow {
  vertex_id?: string | null;
  patent_no?: string | null;
  holder_did?: string | null;
  rat?: string | null;
  expiry_date?: string | null;
  blocker_status?: string | null;
}

export interface MvPersonCohortBeliefCrossRow {
  era_label?: string | null;
  era_start_year?: number | null;
  estimated_population?: number | bigint | null;
  adherent_fraction?: number | null;
  dominance_rank?: number | null;
  belief_vid?: string | null;
}

export interface MvPersonCohortEraSummaryRow {
  era_label?: string | null;
  era_start_year?: number | null;
  era_end_year?: number | null;
  cohort_count?: number | bigint | null;
  total_population?: number | null;
  total_population_low?: number | null;
  total_population_high?: number | null;
  avg_life_expectancy?: number | null;
}

export interface MvProteinTaxonCoverageRow {
  taxon_id?: string | null;
  protein_count?: number | bigint | null;
  linked_count?: number | bigint | null;
  first_at?: string | null;
}

export interface MvPublicDatasetCatalogCoverageRow {
  provider?: string | null;
  dataset_count?: number | bigint | null;
  datasets_with_license?: number | bigint | null;
  datasets_with_terms?: number | bigint | null;
  datasets_with_recommendation?: number | bigint | null;
  datasets_approved?: number | bigint | null;
  datasets_rejected?: number | bigint | null;
  datasets_pending?: number | bigint | null;
  table_count_total?: number | null;
  last_observed_at?: string | null;
}

export interface MvPublicDatasetIngestStatusRow {
  provider?: string | null;
  ingest_mode?: string | null;
  dataset_count?: number | bigint | null;
  table_count_total?: number | null;
  datasets_approved?: number | bigint | null;
  datasets_rejected?: number | bigint | null;
  datasets_pending?: number | bigint | null;
  last_observed_at?: string | null;
}

export interface MvPublicDatasetProfileRankRow {
  dataset_id?: string | null;
  bq_project?: string | null;
  bq_dataset?: string | null;
  profile_count?: number | bigint | null;
  last_observed_at?: string | null;
  best_profile_score?: number | null;
  cheapest_refresh_cost_usd?: number | null;
  profiles_approved?: number | bigint | null;
  profiles_rejected?: number | bigint | null;
  profiles_pending?: number | bigint | null;
  profiles_allowed_for_train?: number | bigint | null;
  profiles_license_allow?: number | bigint | null;
}

export interface MvSciencePaperDomainStatsRow {
  domain?: string | null;
  year?: number | bigint | null;
  paper_count?: number | bigint | null;
  embedded_count?: number | bigint | null;
  linked_count?: number | bigint | null;
  avg_citations?: number | null;
}

export interface MvSekkeiStaleReviewsRow {
  drawing_id?: string | null;
  rev_no?: string | null;
  revised_by_did?: string | null;
  revised_at?: string | null;
}

export interface MvTaxonModelCoverageRow {
  domain_kind?: string | null;
  taxon_rank?: string | null;
  total_taxa?: number | bigint | null;
  modelled_taxa?: number | bigint | null;
  vegetation_taxa?: number | bigint | null;
  model_coverage_ratio?: number | null;
}

export interface MvTrainingSourceEligibilityRow {
  dataset_id?: string | null;
  training_task?: string | null;
  license?: string | null;
  approved_by?: string | null;
  approved_at?: string | null;
  provider?: string | null;
  bq_project?: string | null;
  bq_dataset?: string | null;
  dataset_review_status?: string | null;
  dataset_ingest_mode?: string | null;
  observed_at?: string | null;
}

export interface MvWorldCoverageLiveRow {
  domain?: string | null;
  app_host?: string | null;
  world_total?: number | bigint | null;
  unit?: string | null;
  sector?: string | null;
  did_count?: number | bigint | null;
  record_count?: number | bigint | null;
  vertex_count?: number | bigint | null;
  collected?: number | bigint | null;
  coverage_rate?: number | null;
  gap_rate?: number | null;
  remaining?: number | bigint | null;
}

export interface MvWorldVertexPerHostRow {
  app_host?: string | null;
  vertex_count?: number | null;
}

export interface VTrainingTripleRow {
  src_vid?: string | null;
  relation?: string | null;
  dst_vid?: string | null;
  created_date?: string | null;
}

export interface VertexAirQualityObservationRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | bigint | null;
  owner_did?: string | null;
  source_dataset_id?: string | null;
  state_code?: string | null;
  county_code?: string | null;
  site_num?: string | null;
  parameter_code?: string | null;
  parameter_name?: string | null;
  date_local?: string | null;
  arithmetic_mean?: number | null;
  units_of_measure?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  observation_count?: number | bigint | null;
  props?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
  at_did?: string | null;
  created_at?: string | null;
}

export interface VertexBigqueryExportArtifactRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | bigint | null;
  owner_did?: string | null;
  run_id?: string | null;
  job_id?: string | null;
  artifact_kind?: string | null;
  source_dataset_id?: string | null;
  source_table?: string | null;
  export_uri?: string | null;
  format?: string | null;
  byte_size?: number | bigint | null;
  row_count?: number | bigint | null;
  sha256?: string | null;
  license?: string | null;
  observed_at?: string | null;
  props?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
  at_did?: string | null;
  created_at?: string | null;
}

export interface VertexBigqueryIngestJobRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | bigint | null;
  owner_did?: string | null;
  job_id?: string | null;
  run_id?: string | null;
  query_kind?: string | null;
  query_hash?: string | null;
  query_text_uri?: string | null;
  bq_project?: string | null;
  bq_location?: string | null;
  statement_type?: string | null;
  destination_table?: string | null;
  maximum_bytes_billed?: number | bigint | null;
  total_bytes_processed?: number | bigint | null;
  total_bytes_billed?: number | bigint | null;
  slot_ms?: number | bigint | null;
  cache_hit?: string | null;
  dry_run?: string | null;
  status?: string | null;
  error_reason?: string | null;
  error_message?: string | null;
  started_at?: string | null;
  finished_at?: string | null;
  estimated_cost_usd?: number | null;
  observed_at?: string | null;
  props?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
  at_did?: string | null;
  created_at?: string | null;
}

export interface VertexBigqueryProfileRunRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | bigint | null;
  owner_did?: string | null;
  run_id?: string | null;
  mode?: string | null;
  bq_project?: string | null;
  provider_filter?: string | null;
  dataset_filter?: string | null;
  started_at?: string | null;
  finished_at?: string | null;
  status?: string | null;
  datasets_seen?: number | bigint | null;
  tables_seen?: number | bigint | null;
  samples_taken?: number | bigint | null;
  total_bytes_billed?: number | bigint | null;
  total_cost_usd?: number | null;
  max_bytes_billed_per_query?: number | bigint | null;
  monthly_scan_budget_tib?: number | null;
  monthly_scan_used_tib?: number | null;
  approval_note?: string | null;
  error_message?: string | null;
  props?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
  at_did?: string | null;
  created_at?: string | null;
}

export interface VertexBlockchainBlockRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | bigint | null;
  owner_did?: string | null;
  source_dataset_id?: string | null;
  chain_id?: string | null;
  block_height?: number | bigint | null;
  block_hash?: string | null;
  parent_hash?: string | null;
  block_time?: string | null;
  tx_count?: number | bigint | null;
  size_bytes?: number | bigint | null;
  difficulty?: number | null;
  reward_satoshis?: number | bigint | null;
  miner?: string | null;
  props?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
  at_did?: string | null;
  created_at?: string | null;
}

export interface VertexBlockchainTxRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | bigint | null;
  owner_did?: string | null;
  source_dataset_id?: string | null;
  chain_id?: string | null;
  tx_hash?: string | null;
  block_height?: number | bigint | null;
  block_hash?: string | null;
  block_time?: string | null;
  input_count?: number | bigint | null;
  output_count?: number | bigint | null;
  input_value_satoshis?: number | bigint | null;
  output_value_satoshis?: number | bigint | null;
  fee_satoshis?: number | bigint | null;
  is_coinbase?: string | null;
  props?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
  at_did?: string | null;
  created_at?: string | null;
}

export interface VertexBusinessPersonCareerEventRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | bigint | null;
  owner_did?: string | null;
  person_vertex_id?: string | null;
  org_name?: string | null;
  org_did?: string | null;
  title?: string | null;
  department?: string | null;
  employment_type?: string | null;
  since?: string | null;
  until?: string | null;
  country?: string | null;
  description?: string | null;
  source?: string | null;
  ingested_at?: string | null;
  props?: string | null;
  actor_did?: string | null;
}

export interface VertexBusinessPersonCertRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | bigint | null;
  owner_did?: string | null;
  person_vertex_id?: string | null;
  cert_name?: string | null;
  cert_code?: string | null;
  issuer?: string | null;
  issued_at?: string | null;
  expires_at?: string | null;
  credential_url?: string | null;
  source?: string | null;
  ingested_at?: string | null;
  props?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
}

export interface VertexBusinessPersonEduRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | bigint | null;
  owner_did?: string | null;
  person_vertex_id?: string | null;
  institution?: string | null;
  degree?: string | null;
  field_of_study?: string | null;
  start_year?: string | null;
  end_year?: string | null;
  country?: string | null;
  source?: string | null;
  ingested_at?: string | null;
  props?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
}

export interface VertexChatArtifactRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  conv_id?: string | null;
  msg_id?: string | null;
  artifact_id?: string | null;
  kind?: string | null;
  mime_type?: string | null;
  byte_size?: number | bigint | null;
  sha256?: string | null;
  b2_bucket?: string | null;
  b2_key?: string | null;
  title?: string | null;
  description?: string | null;
  prompt?: string | null;
  visibility?: string | null;
  ts_ms?: number | bigint | null;
  expires_at?: string | null;
  gc_at?: string | null;
  status?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface VertexChatCheckpointRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  thread_id?: string | null;
  checkpoint_id?: string | null;
  parent_checkpoint_id?: string | null;
  checkpoint_ns?: string | null;
  channel_versions_json?: string | null;
  channel_values_json?: string | null;
  pending_writes_json?: string | null;
  ts_ms?: number | bigint | null;
  status?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface VertexChatConversationRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  conv_id?: string | null;
  title?: string | null;
  agent_did?: string | null;
  model_hint?: string | null;
  tier_hint?: string | null;
  visibility?: string | null;
  message_count?: number | null;
  last_message_at?: string | null;
  pinned?: boolean | null;
  status?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface VertexChatMemoryRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  memory_id?: string | null;
  agent_did?: string | null;
  memory_kind?: string | null;
  content?: string | null;
  content_summary?: string | null;
  embedding?: string | null;
  embedding_model?: string | null;
  embedding_norm?: number | null;
  ivf_cluster_id?: number | null;
  importance_score?: number | null;
  decay_at?: string | null;
  last_accessed_at?: string | null;
  access_count?: number | null;
  source_conv_id?: string | null;
  source_msg_id?: string | null;
  ts_ms?: number | bigint | null;
  status?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface VertexChatMessageRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  conv_id?: string | null;
  msg_id?: string | null;
  role?: string | null;
  content?: string | null;
  tool_calls_json?: string | null;
  tool_call_id?: string | null;
  parent_msg_id?: string | null;
  ts_ms?: number | bigint | null;
  model_used?: string | null;
  prompt_tokens?: number | null;
  completion_tokens?: number | null;
  total_tokens?: number | null;
  finish_reason?: string | null;
  embedding?: string | null;
  embedding_model?: string | null;
  embedding_norm?: number | null;
  ivf_cluster_id?: number | null;
  indexed_at?: string | null;
  status?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface VertexChatSessionRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  session_id?: string | null;
  ip_hash?: string | null;
  ua_hash?: string | null;
  country?: string | null;
  first_seen_at?: string | null;
  last_seen_at?: string | null;
  message_count?: number | null;
  conversation_count?: number | null;
  rate_limit_bucket?: string | null;
  status?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface VertexChatToolInvocationRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  conv_id?: string | null;
  msg_id?: string | null;
  tool_call_id?: string | null;
  tool_name?: string | null;
  args_json?: string | null;
  result_summary?: string | null;
  result_byte_size?: number | null;
  duration_ms?: number | null;
  ts_ms?: number | bigint | null;
  side_effect_xrpc_uri?: string | null;
  side_effect_run_id?: string | null;
  error_code?: string | null;
  error_message?: string | null;
  status?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface VertexChemistryPatentRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | bigint | null;
  owner_did?: string | null;
  source_dataset_id?: string | null;
  schembl_id?: string | null;
  patent_id?: string | null;
  patent_publication_date?: string | null;
  chembl_id?: string | null;
  inchi_key?: string | null;
  smiles?: string | null;
  ipc_code?: string | null;
  cpc_code?: string | null;
  family_id?: string | null;
  props?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
  at_did?: string | null;
  created_at?: string | null;
}

export interface VertexCollectionProcedureRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | bigint | null;
  owner_did?: string | null;
  case_vid?: string | null;
  procedure_kind?: string | null;
  target?: string | null;
  court?: string | null;
  court_case_number?: string | null;
  filed_at?: string | null;
  ordered_at?: string | null;
  served_at?: string | null;
  completed_at?: string | null;
  status?: string | null;
  recovered_jpy?: number | bigint | null;
  filing_doc_r2_key?: string | null;
  order_doc_r2_key?: string | null;
  response_doc_r2_key?: string | null;
  notes?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
}

export interface VertexCompoundRow {
  vertex_id?: string | null;
  pubchem_cid?: string | null;
  iupac_name?: string | null;
  common_name?: string | null;
  molecular_formula?: string | null;
  molecular_weight?: number | null;
  smiles?: string | null;
  inchi?: string | null;
  inchi_key?: string | null;
  charge?: number | null;
  h_bond_donors?: number | null;
  h_bond_acceptors?: number | null;
  rotatable_bonds?: number | null;
  xlogp?: number | null;
  tpsa?: number | null;
  complexity?: number | null;
  phase_std?: string | null;
  kami_model_def_id?: string | null;
  created_at?: string | null;
  sensitivity_ord?: number | null;
  org_id?: string | null;
  owner_did?: string | null;
}

export interface VertexCryptoAssetFreezeIncidentRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | bigint | null;
  owner_did?: string | null;
  rkey?: string | null;
  repo?: string | null;
  did?: string | null;
  collection?: string | null;
  status?: string | null;
  incident_id?: string | null;
  source_case_id?: string | null;
  source_app?: string | null;
  wallet_addresses?: string | null;
  priority?: string | null;
  case_id?: string | null;
  chain?: string | null;
  asset_symbol?: string | null;
  amount?: number | null;
  wallet_address?: string | null;
  tx_hash?: string | null;
  authority?: string | null;
  jurisdiction?: string | null;
  reason?: string | null;
  severity?: string | null;
  freeze_status?: string | null;
  reported_at?: string | null;
  frozen_at?: string | null;
  released_at?: string | null;
  source?: string | null;
  source_url?: string | null;
  source_record_id?: string | null;
  notes?: string | null;
  evidence_json?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  created_at?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
  entity_name?: string | null;
  sdn_type?: string | null;
}

export interface VertexCrystalStructureRow {
  vertex_id?: string | null;
  source_ref_id?: string | null;
  source_kind?: string | null;
  crystal_system?: string | null;
  space_group?: string | null;
  space_group_number?: number | null;
  a_ang?: number | null;
  b_ang?: number | null;
  c_ang?: number | null;
  alpha_deg?: number | null;
  beta_deg?: number | null;
  gamma_deg?: number | null;
  z_value?: number | null;
  density_calc?: number | null;
  unit_cell_cid?: string | null;
  glb_cid?: string | null;
  cif_cid?: string | null;
  cod_id?: string | null;
  icsd_id?: string | null;
  created_at?: string | null;
  sensitivity_ord?: number | null;
  org_id?: string | null;
  owner_did?: string | null;
}

export interface VertexDomainEligibilityAdviceRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  tld?: string | null;
  jurisdiction?: string | null;
  regulator_slug?: string | null;
  actor_kind?: string | null;
  eligible?: boolean | null;
  basis?: string | null;
  policy_excerpt?: string | null;
  source_url?: string | null;
  effective_at?: string | null;
  status?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface VertexDomainLegalRegulatorRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  regulator_slug?: string | null;
  name?: string | null;
  jurisdiction?: string | null;
  kind?: string | null;
  public_register_url?: string | null;
  notes?: string | null;
  status?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface VertexDomainRegistrarRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  registrar_slug?: string | null;
  name?: string | null;
  homepage_url?: string | null;
  iana_id?: string | null;
  jp_friendly?: boolean | null;
  notes?: string | null;
  status?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface VertexDomainRegistrationRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  domain_name?: string | null;
  tld?: string | null;
  registrar_slug?: string | null;
  registrant_did?: string | null;
  registrant_name?: string | null;
  registrant_kind?: string | null;
  jurisdiction?: string | null;
  regulator_slug?: string | null;
  eligibility_evidence_url?: string | null;
  eligibility_advice_vid?: string | null;
  registered_at?: string | null;
  expires_at?: string | null;
  auto_renew?: boolean | null;
  ns_provider?: string | null;
  status?: string | null;
  notes?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface VertexDomainTldRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  tld?: string | null;
  operator?: string | null;
  restricted?: boolean | null;
  eligibility_summary?: string | null;
  eligibility_policy_url?: string | null;
  verification_required?: boolean | null;
  typical_uses?: string | null;
  notes?: string | null;
  status?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface VertexForestInventoryRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | bigint | null;
  owner_did?: string | null;
  source_dataset_id?: string | null;
  plot_id?: string | null;
  state_code?: string | null;
  county_code?: string | null;
  inventory_year?: number | null;
  latitude?: number | null;
  longitude?: number | null;
  forest_type_code?: string | null;
  stand_age_years?: number | null;
  stand_size_class?: string | null;
  ownership_group_code?: string | null;
  biomass_dry_kg?: number | null;
  carbon_dry_kg?: number | null;
  props?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
  at_did?: string | null;
  created_at?: string | null;
}

export interface VertexFundRow {
  vertex_id?: string | null;
  fund_id?: string | null;
  name?: string | null;
  fund_kind?: string | null;
  jurisdiction?: string | null;
  aum_amount?: number | null;
  source_url?: string | null;
  source_license?: string | null;
  created_date?: string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  _seq?: number | bigint | null;
}

export interface VertexGameChartAnalysisRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | bigint | null;
  owner_did?: string | null;
  week_start?: Date | string | null;
  source?: string | null;
  analysis_ja?: string | null;
  analysis_en?: string | null;
  top_genre?: string | null;
  rising_titles_json?: string | null;
  falling_titles_json?: string | null;
  new_entries_json?: string | null;
  insight_tags_json?: string | null;
  social_post_rkey?: string | null;
  model_id?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
  created_at?: string | null;
}

export interface VertexGameChartSnapshotRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | bigint | null;
  owner_did?: string | null;
  title_did?: string | null;
  source?: string | null;
  week_start?: Date | string | null;
  rank?: number | null;
  rank_prev?: number | null;
  rank_delta?: number | null;
  external_id?: string | null;
  title_hint?: string | null;
  score_source?: number | null;
  players_2w?: number | bigint | null;
  price_usd?: number | null;
  metadata_json?: string | null;
  fetched_at?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
  created_at?: string | null;
}

export interface VertexHfDatasetRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  slug?: string | null;
  org?: string | null;
  name?: string | null;
  modality?: string | null;
  license?: string | null;
  hf_url?: string | null;
  task_categories?: string | null;
  tags?: string | null;
  row_count_expected?: number | bigint | null;
  row_count_ingested?: number | bigint | null;
  last_synced_at?: string | null;
  status?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface VertexHfDatasetCollectionRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  collection_id?: string | null;
  display_name?: string | null;
  purpose?: string | null;
  selection_policy?: string | null;
  target_model_scope?: string | null;
  status?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface VertexHfDatasetRecordRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  slug?: string | null;
  record_id?: string | null;
  split?: string | null;
  lang?: string | null;
  text_for_training?: string | null;
  text_byte_size?: number | null;
  raw_json?: string | null;
  source_uri?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface VertexHfDatasetReliabilityRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  repo_id?: string | null;
  hf_dataset_vertex_id?: string | null;
  hfhub_dataset_vertex_id?: string | null;
  primary_modality?: string | null;
  training_stage?: string | null;
  recommended_role?: string | null;
  license?: string | null;
  commercial_use?: string | null;
  artifact_availability?: string | null;
  text_alignment?: string | null;
  card_quality_score?: number | null;
  license_score?: number | null;
  availability_score?: number | null;
  alignment_score?: number | null;
  curation_score?: number | null;
  contamination_risk_ord?: number | null;
  pii_risk_ord?: number | null;
  copyright_risk_ord?: number | null;
  eval_leakage_risk_ord?: number | null;
  duplicate_risk_ord?: number | null;
  hub_downloads_month?: number | bigint | null;
  hub_likes?: number | null;
  trust_score?: number | null;
  trust_tier?: string | null;
  decision?: string | null;
  rationale?: string | null;
  source_url?: string | null;
  observed_at?: string | null;
  status?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface VertexIntelEvidenceRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | bigint | null;
  owner_did?: string | null;
  evidence_id?: string | null;
  subject_vertex_id?: string | null;
  source_uri?: string | null;
  source_did?: string | null;
  extractor?: string | null;
  observed_at?: string | null;
  hash?: string | null;
  payload_json?: string | null;
  status?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
}

export interface VertexIntelInferenceRunRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | bigint | null;
  owner_did?: string | null;
  run_id?: string | null;
  trigger_kind?: string | null;
  scope_json?: string | null;
  model?: string | null;
  workflow_instance_key?: string | null;
  candidate_count?: number | bigint | null;
  active_count?: number | bigint | null;
  review_count?: number | bigint | null;
  status?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
}

export interface VertexIntelSubjectRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | bigint | null;
  owner_did?: string | null;
  subject_kind?: string | null;
  canonical_key?: string | null;
  label?: string | null;
  source_did?: string | null;
  source_vertex_id?: string | null;
  lei?: string | null;
  registration_number?: string | null;
  jurisdiction?: string | null;
  attributes_json?: string | null;
  status?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
}

export interface VertexIrCompanyRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | bigint | null;
  owner_did?: string | null;
  lei?: string | null;
  edinet_code?: string | null;
  securities_code?: string | null;
  ticker?: string | null;
  exchange?: string | null;
  company_name?: string | null;
  company_name_ja?: string | null;
  ir_url?: string | null;
  ir_rss_url?: string | null;
  ir_host?: string | null;
  ir_status?: string | null;
  ir_last_crawled_at?: string | null;
  ir_crawl_interval_hours?: number | bigint | null;
  country_code?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface VertexIrPressreleaseRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | bigint | null;
  owner_did?: string | null;
  company_vertex_id?: string | null;
  lei?: string | null;
  title?: string | null;
  url?: string | null;
  published_at?: string | null;
  body_snippet?: string | null;
  lang?: string | null;
  kind?: string | null;
  method?: string | null;
  intel_subject_vid?: string | null;
  crawled_at?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface VertexIrScraperRunRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | bigint | null;
  owner_did?: string | null;
  company_vertex_id?: string | null;
  lei?: string | null;
  ir_url?: string | null;
  ir_rss_url?: string | null;
  status?: string | null;
  method?: string | null;
  articles_found?: number | bigint | null;
  articles_inserted?: number | bigint | null;
  error_message?: string | null;
  queued_at?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface VertexKaisyaAgentRunRow {
  vertex_id?: string | null;
  agent_id?: string | null;
  process_id?: string | null;
  task_type?: string | null;
  human_did?: string | null;
  status?: string | null;
  output_summary?: string | null;
  tasks_created?: number | bigint | null;
  ran_at?: Date | string | null;
  owner_did?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  sensitivity_ord?: number | null;
  actor_id?: string | null;
  created_at?: Date | string | null;
}

export interface VertexKaisyaOrgSnapshotRow {
  vertex_id?: string | null;
  snapshot_at?: Date | string | null;
  omega?: number | null;
  eta_value?: number | null;
  u_total?: number | null;
  spirit_score?: number | null;
  wellbecoming_score?: number | null;
  feeling_score?: number | null;
  buffer_score?: number | null;
  separation_delta?: number | null;
  decisions_json?: string | null;
  actions_executed?: number | null;
  tasks_created?: number | null;
  agent_runs_24h?: number | null;
  pending_tasks?: number | null;
  at_risk_callers?: number | null;
  open_legal_cases?: number | null;
  floor_violated?: boolean | null;
  owner_did?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  sensitivity_ord?: number | null;
  created_at?: Date | string | null;
}

export interface VertexKaisyaTaskRow {
  vertex_id?: string | null;
  agent_id?: string | null;
  human_did?: string | null;
  title?: string | null;
  context_json?: string | null;
  priority?: number | null;
  status?: string | null;
  due_at?: Date | string | null;
  resolved_at?: Date | string | null;
  resolved_by?: string | null;
  resolution_note?: string | null;
  owner_did?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  sensitivity_ord?: number | null;
  actor_id?: string | null;
  created_at?: Date | string | null;
}

export interface VertexKamiMaterialDefRow {
  vertex_id?: string | null;
  material_name?: string | null;
  albedo_r?: number | null;
  albedo_g?: number | null;
  albedo_b?: number | null;
  albedo_a?: number | null;
  metallic?: number | null;
  roughness?: number | null;
  emissive_r?: number | null;
  emissive_g?: number | null;
  emissive_b?: number | null;
  opacity?: number | null;
  double_sided?: boolean | null;
  albedo_texture_uri?: string | null;
  normal_texture_uri?: string | null;
  orm_texture_uri?: string | null;
  element_did?: string | null;
  compound_formula?: string | null;
  crystal_system?: string | null;
  material_class?: string | null;
  created_at?: string | null;
  sensitivity_ord?: number | bigint | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  owner_did?: string | null;
  _seq?: number | bigint | null;
}

export interface VertexKamiModelDefRow {
  vertex_id?: string | null;
  slug?: string | null;
  model_kind?: string | null;
  lod_levels?: number | bigint | null;
  mesh_uri?: string | null;
  mesh_uri_lod1?: string | null;
  mesh_uri_lod2?: string | null;
  bbox_min_x?: number | null;
  bbox_min_y?: number | null;
  bbox_min_z?: number | null;
  bbox_max_x?: number | null;
  bbox_max_y?: number | null;
  bbox_max_z?: number | null;
  pivot_x?: number | null;
  pivot_y?: number | null;
  pivot_z?: number | null;
  material_json?: string | null;
  taxonomy_did?: string | null;
  render_kind?: string | null;
  source?: string | null;
  version?: number | bigint | null;
  status?: string | null;
  created_at?: string | null;
  sensitivity_ord?: number | bigint | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  owner_did?: string | null;
  _seq?: number | bigint | null;
}

export interface VertexKamiModelInstanceRow {
  vertex_id?: string | null;
  model_def_id?: string | null;
  tile_h3?: string | null;
  world_x?: number | null;
  world_y?: number | null;
  world_z?: number | null;
  scale_x?: number | null;
  scale_y?: number | null;
  scale_z?: number | null;
  rot_yaw?: number | null;
  rot_pitch?: number | null;
  rot_roll?: number | null;
  color_r?: number | null;
  color_g?: number | null;
  color_b?: number | null;
  spatial_vertex_id?: string | null;
  taxonomy_did?: string | null;
  annotation_json?: string | null;
  visibility_range_m?: number | null;
  created_at?: string | null;
  sensitivity_ord?: number | bigint | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  owner_did?: string | null;
  _seq?: number | bigint | null;
}

export interface VertexLifehackEnvironmentReadingRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  reading_id?: string | null;
  reporter_did?: string | null;
  location_h3?: string | null;
  humidity_pct?: number | null;
  temp_c?: number | null;
  pm25_ugm3?: number | null;
  ts_ms?: number | bigint | null;
  source?: string | null;
  status?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface VertexLifehackPostLogRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  post_id?: string | null;
  tip_id?: string | null;
  topic_id?: string | null;
  bsky_uri?: string | null;
  bsky_cid?: string | null;
  posted_at_ms?: number | bigint | null;
  engagement_score?: number | null;
  status?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface VertexLifehackProductRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  product_id?: string | null;
  name?: string | null;
  brand?: string | null;
  category?: string | null;
  source_type?: string | null;
  price_jpy_min?: number | null;
  price_jpy_max?: number | null;
  amazon_search_keyword?: string | null;
  asin?: string | null;
  pse_certified?: boolean | null;
  tsukuru_cad_model_did?: string | null;
  tsukuru_factory_did?: string | null;
  tsukuru_production_order_nsid?: string | null;
  estimated_make_cost_jpy?: number | null;
  estimated_make_time_hours?: number | null;
  notes_ja?: string | null;
  status?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface VertexLifehackTipRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  tip_id?: string | null;
  topic_id?: string | null;
  body_ja?: string | null;
  body_en?: string | null;
  effectiveness_score?: number | null;
  cost_jpy_min?: number | null;
  cost_jpy_max?: number | null;
  difficulty?: string | null;
  source_url?: string | null;
  source_authority?: string | null;
  evidence_summary?: string | null;
  llm_model?: string | null;
  status?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface VertexLifehackTopicRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  topic_id?: string | null;
  category?: string | null;
  title_ja?: string | null;
  title_en?: string | null;
  summary_ja?: string | null;
  summary_en?: string | null;
  parent_topic_id?: string | null;
  status?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface VertexLifehackUserQueryRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  query_id?: string | null;
  asker_did?: string | null;
  query_text?: string | null;
  answered_tip_ids?: string | null;
  llm_model?: string | null;
  latency_ms?: number | null;
  status?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface VertexLiveChatRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  room_slug?: string | null;
  actor_handle?: string | null;
  text?: string | null;
  kind?: string | null;
  tint_r?: number | null;
  tint_g?: number | null;
  tint_b?: number | null;
  posted_at?: number | null;
  name?: string | null;
  description?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
  at_did?: string | null;
  created_at?: string | null;
}

export interface VertexLiveLightingCueRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  room_slug?: string | null;
  fixture?: string | null;
  color_r?: number | null;
  color_g?: number | null;
  color_b?: number | null;
  intensity?: number | null;
  envelope?: string | null;
  envelope_param?: number | null;
  bars?: number | bigint | null;
  start_bar?: number | bigint | null;
  name?: string | null;
  description?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
  at_did?: string | null;
  created_at?: string | null;
}

export interface VertexLiveRoomRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  slug?: string | null;
  bpm?: number | null;
  start_at?: number | null;
  stage_preset?: string | null;
  performer_handle?: string | null;
  setlist_json?: string | null;
  lighting_json?: string | null;
  crowd_seed?: number | bigint | null;
  fans_target?: number | bigint | null;
  name?: string | null;
  description?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
  at_did?: string | null;
  created_at?: string | null;
}

export interface VertexLiveTrackRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  room_slug?: string | null;
  position?: number | bigint | null;
  title?: string | null;
  bpm?: number | null;
  length_beats?: number | bigint | null;
  dance?: string | null;
  audio?: string | null;
  cues_json?: string | null;
  name?: string | null;
  description?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
  at_did?: string | null;
  created_at?: string | null;
}

export interface VertexMalakWalletAddressRow {
  vertex_id?: string | null;
  rkey?: string | null;
  repo?: string | null;
  did?: string | null;
  chain?: string | null;
  address?: string | null;
  actor_node_id?: string | null;
  label?: string | null;
  confidence?: number | bigint | null;
  evidence?: string | null;
  linked_at?: string | null;
  sensitivity_ord?: number | bigint | null;
  owner_did?: string | null;
  created_date?: Date | string | null;
  actor_did?: string | null;
  org_did?: string | null;
}

export interface VertexMapsBuilding3dRow {
  vertex_id?: string | null;
  spatial_vertex_id?: string | null;
  tile_h3?: string | null;
  h3_resolution?: number | bigint | null;
  centroid_lat?: number | null;
  centroid_lng?: number | null;
  footprint_json?: string | null;
  height_m?: number | null;
  source?: string | null;
  mesh_uri?: string | null;
  coverage_score?: number | null;
  ingest_at?: string | null;
  created_at?: string | null;
  sensitivity_ord?: number | bigint | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  owner_did?: string | null;
  _seq?: number | bigint | null;
}

export interface VertexMapsBuildingCoverageRow {
  vertex_id?: string | null;
  tile_h3?: string | null;
  h3_resolution?: number | bigint | null;
  centroid_lat?: number | null;
  centroid_lng?: number | null;
  building_count?: number | bigint | null;
  has_sentinel?: boolean | null;
  has_mapraly?: boolean | null;
  coverage_source?: string | null;
  last_ingest_at?: string | null;
  status?: string | null;
  created_at?: string | null;
  sensitivity_ord?: number | bigint | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  owner_did?: string | null;
  _seq?: number | bigint | null;
}

export interface VertexMarineObservationRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | bigint | null;
  owner_did?: string | null;
  source_dataset_id?: string | null;
  observed_at?: string | null;
  year?: number | null;
  month?: number | null;
  day?: number | null;
  hour?: number | null;
  latitude?: number | null;
  longitude?: number | null;
  sea_surface_temp_c?: number | null;
  air_temp_c?: number | null;
  wind_direction_deg?: number | null;
  wind_speed_mps?: number | null;
  pressure_hpa?: number | null;
  platform_id?: string | null;
  callsign?: string | null;
  country_code?: string | null;
  props?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
  at_did?: string | null;
  created_at?: string | null;
}

export interface VertexMineralRow {
  vertex_id?: string | null;
  ima_symbol?: string | null;
  mineral_name?: string | null;
  chemical_formula?: string | null;
  crystal_system?: string | null;
  crystal_class?: string | null;
  space_group?: string | null;
  hardness_min?: number | null;
  hardness_max?: number | null;
  density_min?: number | null;
  density_max?: number | null;
  luster?: string | null;
  color_common?: string | null;
  streak?: string | null;
  cleavage?: string | null;
  ima_number?: string | null;
  discovery_year?: number | bigint | null;
  element_dids_json?: string | null;
  kami_model_def_id?: string | null;
  taxon_did?: string | null;
  created_at?: string | null;
  sensitivity_ord?: number | bigint | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  owner_did?: string | null;
  _seq?: number | bigint | null;
}

export interface VertexNaturalPersonBirthEventRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | bigint | null;
  owner_did?: string | null;
  rkey?: string | null;
  repo?: string | null;
  person_did?: string | null;
  person_hash?: string | null;
  birth_year?: string | null;
  birth_country?: string | null;
  birth_region?: string | null;
  birth_municipality?: string | null;
  parent_a_did?: string | null;
  parent_b_did?: string | null;
  parent_a_hash?: string | null;
  parent_b_hash?: string | null;
  registration_source?: string | null;
  registration_id?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface VertexNaturalPersonDemographicStatRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | bigint | null;
  owner_did?: string | null;
  rkey?: string | null;
  repo?: string | null;
  source_id?: string | null;
  stat_type?: string | null;
  country?: string | null;
  region?: string | null;
  age_min?: string | null;
  age_max?: string | null;
  gender?: string | null;
  income_decile?: string | null;
  education_isced?: string | null;
  occupation_isco?: string | null;
  employment_status?: string | null;
  marital_status?: string | null;
  household_size?: string | null;
  housing_tenure?: string | null;
  urban_rural?: string | null;
  health_icd10?: string | null;
  disability_type?: string | null;
  migration_status?: string | null;
  vital_status?: string | null;
  era?: string | null;
  population_count?: number | bigint | null;
  population_share?: number | null;
  data_year?: number | bigint | null;
  data_currency?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface VertexNaturalPersonEventAttendeeRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | bigint | null;
  owner_did?: string | null;
  rkey?: string | null;
  repo?: string | null;
  attendee_hash?: string | null;
  person_did?: string | null;
  name?: string | null;
  title?: string | null;
  company?: string | null;
  country?: string | null;
  biography?: string | null;
  person_id?: string | null;
  booth?: string | null;
  event_name?: string | null;
  event_year?: number | bigint | null;
  source_id?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface VertexNaturalPersonIdDocumentRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | bigint | null;
  owner_did?: string | null;
  rkey?: string | null;
  repo?: string | null;
  person_hash?: string | null;
  doc_type?: string | null;
  doc_number_hash?: string | null;
  issue_country?: string | null;
  issue_year?: string | null;
  expiry_year?: string | null;
  approval_count?: number | bigint | null;
  approval_class?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface VertexNaturalPersonPersonRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | bigint | null;
  owner_did?: string | null;
  rkey?: string | null;
  repo?: string | null;
  person_hash?: string | null;
  cohort_did?: string | null;
  person_did?: string | null;
  name?: string | null;
  country?: string | null;
  birth_year?: string | null;
  gender?: string | null;
  org_id_owner?: string | null;
  registration_method?: string | null;
  registered_by?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface VertexOpenAdnetworkAdUnitRow {
  vertex_id?: string | null;
  unit_id?: string | null;
  publisher_did?: string | null;
  unit_type?: string | null;
  size?: string | null;
  placement?: string | null;
  floor_cpm_usd?: number | null;
  active_campaign_count?: number | null;
  status?: string | null;
  created_at?: string | null;
  sensitivity_ord?: number | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
}

export interface VertexOpenAdnetworkAdvertiserRow {
  vertex_id?: string | null;
  advertiser_id?: string | null;
  brand_name?: string | null;
  domain?: string | null;
  industry_category?: string | null;
  monthly_budget_usd?: number | null;
  payment_method?: string | null;
  status?: string | null;
  created_at?: string | null;
  sensitivity_ord?: number | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
}

export interface VertexOpenAdnetworkCampaignRow {
  vertex_id?: string | null;
  campaign_id?: string | null;
  advertiser_did?: string | null;
  name?: string | null;
  objective?: string | null;
  budget_daily_usd?: number | null;
  bid_strategy?: string | null;
  bid_floor_usd?: number | null;
  targeting_json?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  status?: string | null;
  created_at?: string | null;
  sensitivity_ord?: number | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
}

export interface VertexOpenAdnetworkClickRow {
  vertex_id?: string | null;
  click_id?: string | null;
  imp_id?: string | null;
  unit_id?: string | null;
  campaign_id?: string | null;
  cpc_usd?: number | null;
  country_iso2?: string | null;
  ts_ms?: number | bigint | null;
  created_at?: string | null;
  sensitivity_ord?: number | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
}

export interface VertexOpenAdnetworkConversionRow {
  vertex_id?: string | null;
  conv_id?: string | null;
  click_id?: string | null;
  campaign_id?: string | null;
  conv_type?: string | null;
  conv_value_usd?: number | null;
  ts_ms?: number | bigint | null;
  created_at?: string | null;
  sensitivity_ord?: number | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
}

export interface VertexOpenAdnetworkImpressionRow {
  vertex_id?: string | null;
  imp_id?: string | null;
  unit_id?: string | null;
  campaign_id?: string | null;
  cpm_usd?: number | null;
  viewable?: boolean | null;
  user_cohort?: string | null;
  country_iso2?: string | null;
  ts_ms?: number | bigint | null;
  created_at?: string | null;
  sensitivity_ord?: number | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
}

export interface VertexOpenAdnetworkPublisherRow {
  vertex_id?: string | null;
  publisher_id?: string | null;
  domain?: string | null;
  owner_did?: string | null;
  revenue_share_pct?: number | null;
  floor_cpm_usd?: number | null;
  content_category?: string | null;
  ad_policy?: string | null;
  status?: string | null;
  created_at?: string | null;
  sensitivity_ord?: number | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
}

export interface VertexOpenAdnetworkRevenueSnapshotRow {
  vertex_id?: string | null;
  snap_id?: string | null;
  publisher_did?: string | null;
  date?: string | null;
  impressions?: number | bigint | null;
  clicks?: number | bigint | null;
  conversions?: number | bigint | null;
  total_revenue_usd?: number | null;
  rpm_usd?: number | null;
  ctr_pct?: number | null;
  cvr_pct?: number | null;
  ai_insight?: string | null;
  created_at?: string | null;
  sensitivity_ord?: number | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
}

export interface VertexOpenSalesAccountRow {
  vertex_id?: string | null;
  account_id?: string | null;
  company_name?: string | null;
  domain?: string | null;
  industry?: string | null;
  employee_count?: number | null;
  arr_usd?: number | null;
  tier?: string | null;
  status?: string | null;
  created_at?: string | null;
  owner_did?: string | null;
  sensitivity_ord?: number | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
}

export interface VertexOpenSalesActivityRow {
  vertex_id?: string | null;
  activity_id?: string | null;
  opp_did?: string | null;
  contact_did?: string | null;
  kind?: string | null;
  summary?: string | null;
  outcome?: string | null;
  logged_by?: string | null;
  logged_at?: string | null;
  created_at?: string | null;
  sensitivity_ord?: number | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
}

export interface VertexOpenSalesContactRow {
  vertex_id?: string | null;
  contact_id?: string | null;
  full_name?: string | null;
  email?: string | null;
  phone?: string | null;
  account_did?: string | null;
  role?: string | null;
  linkedin_url?: string | null;
  status?: string | null;
  created_at?: string | null;
  owner_did?: string | null;
  sensitivity_ord?: number | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
}

export interface VertexOpenSalesForecastRow {
  vertex_id?: string | null;
  forecast_id?: string | null;
  period?: string | null;
  pipeline_usd?: number | null;
  weighted_usd?: number | null;
  closed_usd?: number | null;
  ai_forecast_usd?: number | null;
  confidence_pct?: number | null;
  notes?: string | null;
  created_at?: string | null;
  sensitivity_ord?: number | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
}

export interface VertexOpenSalesLeadRow {
  vertex_id?: string | null;
  lead_id?: string | null;
  full_name?: string | null;
  email?: string | null;
  company?: string | null;
  source?: string | null;
  lead_score?: number | null;
  status?: string | null;
  assigned_did?: string | null;
  notes?: string | null;
  created_at?: string | null;
  owner_did?: string | null;
  sensitivity_ord?: number | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
}

export interface VertexOpenSalesOpportunityRow {
  vertex_id?: string | null;
  opp_id?: string | null;
  account_did?: string | null;
  title?: string | null;
  stage?: string | null;
  probability_pct?: number | null;
  amount_usd?: number | null;
  close_date?: string | null;
  owner_did?: string | null;
  lost_reason?: string | null;
  status?: string | null;
  created_at?: string | null;
  sensitivity_ord?: number | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
}

export interface VertexOpenSalesQuoteRow {
  vertex_id?: string | null;
  quote_id?: string | null;
  opp_did?: string | null;
  total_usd?: number | null;
  currency?: string | null;
  valid_until?: string | null;
  status?: string | null;
  line_items_json?: string | null;
  llm_summary?: string | null;
  created_at?: string | null;
  sensitivity_ord?: number | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
}

export interface VertexOpenSmartphoneBomRow {
  vertex_id?: string | null;
  bom_id?: string | null;
  design_name?: string | null;
  version?: string | null;
  soc_did?: string | null;
  modem_did?: string | null;
  os_did?: string | null;
  ems_facility_did?: string | null;
  target_price_usd?: number | null;
  open_score_pct?: number | null;
  key_closed_risks?: string | null;
  recommendations?: string | null;
  scored_at?: string | null;
  status?: string | null;
  created_at?: string | null;
  owner_did?: string | null;
  sensitivity_ord?: number | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
}

export interface VertexOpenSmartphoneBomLineRow {
  vertex_id?: string | null;
  line_id?: string | null;
  bom_did?: string | null;
  component_type?: string | null;
  vendor_name?: string | null;
  part_number?: string | null;
  unit_cost_usd?: number | null;
  open_source?: boolean | null;
  license?: string | null;
  patent_did?: string | null;
  alternative_count?: number | null;
  created_at?: string | null;
  owner_did?: string | null;
  sensitivity_ord?: number | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
}

export interface VertexOpenSmartphoneBomSourcerRow {
  vertex_id?: string | null;
  bom_line_did?: string | null;
  alt_vendor?: string | null;
  alt_part_number?: string | null;
  alt_unit_cost_usd?: number | null;
  open_source?: boolean | null;
  availability?: string | null;
  lead_time_weeks?: number | null;
  notes?: string | null;
  created_at?: string | null;
  owner_did?: string | null;
  sensitivity_ord?: number | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
}

export interface VertexOpenSmartphoneEmsComplianceRow {
  vertex_id?: string | null;
  facility_did?: string | null;
  issue_type?: string | null;
  severity?: string | null;
  description?: string | null;
  detected_at?: string | null;
  resolved_at?: string | null;
  status?: string | null;
  created_at?: string | null;
  owner_did?: string | null;
  sensitivity_ord?: number | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
}

export interface VertexOpenSmartphoneEmsFacilityRow {
  vertex_id?: string | null;
  facility_id?: string | null;
  operator_name?: string | null;
  operator_lei?: string | null;
  location_iso3?: string | null;
  city?: string | null;
  facility_type?: string | null;
  monthly_capacity_units?: number | null;
  certifications?: string | null;
  rba_audit_status?: string | null;
  conflict_mineral_compliant?: boolean | null;
  status?: string | null;
  created_at?: string | null;
  owner_did?: string | null;
  sensitivity_ord?: number | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
}

export interface VertexOpenSmartphoneEmsOrderRow {
  vertex_id?: string | null;
  order_id?: string | null;
  facility_did?: string | null;
  bom_did?: string | null;
  quantity_units?: number | null;
  target_unit_cost_usd?: number | null;
  delivery_quarter?: string | null;
  quality_standard?: string | null;
  order_status?: string | null;
  created_at?: string | null;
  owner_did?: string | null;
  sensitivity_ord?: number | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
}

export interface VertexOpenSmartphoneModemSepDepRow {
  vertex_id?: string | null;
  modem_did?: string | null;
  patent_no?: string | null;
  holder_did?: string | null;
  rat?: string | null;
  frand_declared?: boolean | null;
  pool_id?: string | null;
  expiry_date?: string | null;
  blocker_status?: string | null;
  severity?: string | null;
  created_at?: string | null;
  owner_did?: string | null;
  sensitivity_ord?: number | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
}

export interface VertexOpenSmartphoneModemSpecRow {
  vertex_id?: string | null;
  modem_id?: string | null;
  chip_name?: string | null;
  rat_support?: string | null;
  baseband_chip?: string | null;
  open_source_fw?: boolean | null;
  fw_license?: string | null;
  max_dl_mbps?: number | null;
  max_ul_mbps?: number | null;
  release_year?: number | null;
  status?: string | null;
  created_at?: string | null;
  owner_did?: string | null;
  sensitivity_ord?: number | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
}

export interface VertexOpenSmartphoneModemTypeApprovalRow {
  vertex_id?: string | null;
  modem_did?: string | null;
  authority?: string | null;
  certificate_no?: string | null;
  jurisdiction_iso3?: string | null;
  approved_at?: string | null;
  expiry_date?: string | null;
  rat_approved?: string | null;
  status?: string | null;
  created_at?: string | null;
  owner_did?: string | null;
  sensitivity_ord?: number | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
}

export interface VertexOpenSmartphoneOsBuildRow {
  vertex_id?: string | null;
  build_id?: string | null;
  os_name?: string | null;
  os_base?: string | null;
  version?: string | null;
  kernel_version?: string | null;
  soc_support?: string | null;
  open_blobs_pct?: number | null;
  verified_boot?: boolean | null;
  build_url?: string | null;
  release_date?: string | null;
  status?: string | null;
  created_at?: string | null;
  owner_did?: string | null;
  sensitivity_ord?: number | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
  cve_vendor_tag?: string | null;
}

export interface VertexOpenSmartphoneOsHalDriverRow {
  vertex_id?: string | null;
  driver_id?: string | null;
  os_did?: string | null;
  soc_did?: string | null;
  sensor_did?: string | null;
  driver_type?: string | null;
  upstream_status?: string | null;
  vendor_blobs_required?: boolean | null;
  license?: string | null;
  version?: string | null;
  status?: string | null;
  created_at?: string | null;
  owner_did?: string | null;
  sensitivity_ord?: number | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
}

export interface VertexOpenSmartphoneOsOtaRow {
  vertex_id?: string | null;
  ota_id?: string | null;
  os_did?: string | null;
  from_version?: string | null;
  to_version?: string | null;
  release_notes_url?: string | null;
  patch_level?: string | null;
  cve_fixes?: string | null;
  ota_size_mb?: number | null;
  signed?: boolean | null;
  release_date?: string | null;
  status?: string | null;
  created_at?: string | null;
  owner_did?: string | null;
  sensitivity_ord?: number | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
}

export interface VertexOpenSmartphonePatentDepRow {
  vertex_id?: string | null;
  dep_id?: string | null;
  component_type?: string | null;
  component_did?: string | null;
  patent_no?: string | null;
  holder_did?: string | null;
  standard?: string | null;
  dependency_type?: string | null;
  status?: string | null;
  created_at?: string | null;
  owner_did?: string | null;
  sensitivity_ord?: number | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
}

export interface VertexOpenSmartphonePatentPoolRow {
  vertex_id?: string | null;
  pool_id?: string | null;
  pool_name?: string | null;
  administrator?: string | null;
  standards_covered?: string | null;
  member_count?: number | null;
  license_fee_usd_per_unit?: number | null;
  frand_compliant?: boolean | null;
  url?: string | null;
  status?: string | null;
  created_at?: string | null;
  owner_did?: string | null;
  sensitivity_ord?: number | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
}

export interface VertexOpenSmartphonePatentSepRow {
  vertex_id?: string | null;
  patent_no?: string | null;
  holder_did?: string | null;
  cpc_codes?: string | null;
  rat?: string | null;
  frand_declared?: boolean | null;
  pool_id?: string | null;
  priority_date?: string | null;
  expiry_date?: string | null;
  jurisdiction_iso3?: string | null;
  blocker_status?: string | null;
  created_at?: string | null;
  owner_did?: string | null;
  sensitivity_ord?: number | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
  standard?: string | null;
}

export interface VertexOpenSmartphoneSensorCalibrationRow {
  vertex_id?: string | null;
  sensor_did?: string | null;
  calibration_type?: string | null;
  standard_ref?: string | null;
  calibrated_at?: string | null;
  valid_until?: string | null;
  calibrated_by?: string | null;
  pass?: boolean | null;
  status?: string | null;
  created_at?: string | null;
  owner_did?: string | null;
  sensitivity_ord?: number | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
}

export interface VertexOpenSmartphoneSensorDriverRow {
  vertex_id?: string | null;
  sensor_type?: string | null;
  driver_name?: string | null;
  kernel_version?: string | null;
  mainlined?: boolean | null;
  os_build_did?: string | null;
  created_at?: string | null;
  owner_did?: string | null;
  sensitivity_ord?: number | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
}

export interface VertexOpenSmartphoneSensorModuleRow {
  vertex_id?: string | null;
  sensor_id?: string | null;
  sensor_type?: string | null;
  vendor?: string | null;
  model?: string | null;
  interface_type?: string | null;
  open_driver?: boolean | null;
  mainline_kernel_status?: string | null;
  pixel_count_mp?: number | null;
  status?: string | null;
  created_at?: string | null;
  owner_did?: string | null;
  sensitivity_ord?: number | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
}

export interface VertexOpenSmartphoneSocDesignRow {
  vertex_id?: string | null;
  chip_id?: string | null;
  chip_name?: string | null;
  isa?: string | null;
  process_node_nm?: number | null;
  die_area_mm2?: number | null;
  transistor_count_b?: number | null;
  open_source_rtl?: boolean | null;
  rtl_license?: string | null;
  fab_did?: string | null;
  tape_out_date?: string | null;
  status?: string | null;
  created_at?: string | null;
  owner_did?: string | null;
  sensitivity_ord?: number | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
}

export interface VertexOpenSmartphoneSocExportFlagRow {
  vertex_id?: string | null;
  chip_did?: string | null;
  flag_type?: string | null;
  entity_list_entry?: string | null;
  jurisdiction?: string | null;
  flagged_at?: string | null;
  severity?: string | null;
  status?: string | null;
  created_at?: string | null;
  owner_did?: string | null;
  sensitivity_ord?: number | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
}

export interface VertexOpenSmartphoneSocFabOrderRow {
  vertex_id?: string | null;
  order_id?: string | null;
  chip_did?: string | null;
  fab_did?: string | null;
  process_node_nm?: number | null;
  wafer_qty?: number | null;
  delivery_estimate?: string | null;
  price_usd_k?: number | null;
  order_status?: string | null;
  created_at?: string | null;
  owner_did?: string | null;
  sensitivity_ord?: number | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
}

export interface VertexOtakiageCertificateRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  certificate_id?: string | null;
  ritual_uri?: string | null;
  matsuri_uri?: string | null;
  item_uris?: string | null;
  item_count?: number | null;
  donor_dids?: string | null;
  issued_at?: string | null;
  issuer_did?: string | null;
  issuer_name?: string | null;
  display_text?: string | null;
  category_breakdown?: string | null;
  photo_blob_key?: string | null;
  certificate_json?: string | null;
  anchor_token_id?: string | null;
  version?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  anchor_chain?: string | null;
  anchor_contract?: string | null;
  anchor_status?: string | null;
  anchor_tx_hash?: string | null;
  anchor_block_number?: number | bigint | null;
  anchored_at?: string | null;
  content_hash?: string | null;
  failure_reason?: string | null;
}

export interface VertexOtakiageConversationRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  thread_id?: string | null;
  caller_did?: string | null;
  title?: string | null;
  turn_count?: number | null;
  last_intent?: string | null;
  last_message_at?: string | null;
  state?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface VertexOtakiageConversationTurnRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  turn_id?: string | null;
  thread_id?: string | null;
  thread_uri?: string | null;
  caller_did?: string | null;
  turn_index?: number | null;
  user_message?: string | null;
  agent_reply?: string | null;
  intent?: string | null;
  actions_json?: string | null;
  llm_calls?: number | null;
  latency_ms?: number | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface VertexOtakiageHandoverRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  handover_id?: string | null;
  item_uri?: string | null;
  reuse_request_uri?: string | null;
  donor_did?: string | null;
  recipient_did?: string | null;
  handover_at?: string | null;
  handover_photo_blob_key?: string | null;
  gratitude_text?: string | null;
  social_announce_uri?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface VertexOtakiageItemRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  item_id?: string | null;
  category?: string | null;
  title?: string | null;
  story_text?: string | null;
  photo_blob_keys?: string | null;
  h3_cell?: string | null;
  h3_res?: number | null;
  lat?: number | null;
  lng?: number | null;
  weight_kg_class?: string | null;
  mode?: string | null;
  state?: string | null;
  donor_did?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface VertexOtakiageMatsuriRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  matsuri_id?: string | null;
  name?: string | null;
  category_scope?: string | null;
  scheduled_date?: Date | string | null;
  capacity?: number | null;
  registered_count?: number | null;
  location_h3?: string | null;
  description?: string | null;
  state?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface VertexOtakiageReuseRequestRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  request_id?: string | null;
  item_uri?: string | null;
  requester_did?: string | null;
  message?: string | null;
  h3_cell?: string | null;
  lat?: number | null;
  lng?: number | null;
  distance_km?: number | null;
  preferred_handover_date?: Date | string | null;
  state?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface VertexOtakiageRitualRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  ritual_id?: string | null;
  matsuri_uri?: string | null;
  item_uris?: string | null;
  item_count?: number | null;
  ceremony_date?: string | null;
  ceremony_photo_blob_key?: string | null;
  certificate_uri?: string | null;
  state?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface VertexPeriodicElementRow {
  vertex_id?: string | null;
  atomic_number?: number | bigint | null;
  symbol?: string | null;
  element_name_en?: string | null;
  element_name_ja?: string | null;
  atomic_mass?: number | null;
  electronegativity?: number | null;
  atomic_radius_pm?: number | null;
  covalent_radius_pm?: number | null;
  van_der_waals_r_pm?: number | null;
  melting_point_k?: number | null;
  boiling_point_k?: number | null;
  density_gcc?: number | null;
  electron_config?: string | null;
  period?: number | bigint | null;
  group_number?: number | bigint | null;
  block?: string | null;
  category?: string | null;
  cas_number?: string | null;
  kami_sphere_r_pm?: number | null;
  kami_color_r?: number | null;
  kami_color_g?: number | null;
  kami_color_b?: number | null;
  created_at?: string | null;
  sensitivity_ord?: number | bigint | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  owner_did?: string | null;
  _seq?: number | bigint | null;
}

export interface VertexPersonPopulationCohortRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | bigint | null;
  owner_did?: string | null;
  rkey?: string | null;
  repo?: string | null;
  era_label?: string | null;
  era_start_year?: number | null;
  era_end_year?: number | null;
  region_m49?: string | null;
  region_name?: string | null;
  subregion_m49?: string | null;
  estimated_population?: number | bigint | null;
  population_low?: number | bigint | null;
  population_high?: number | bigint | null;
  birth_rate?: number | null;
  death_rate?: number | null;
  life_expectancy?: number | null;
  infant_mortality_rate?: number | null;
  data_source?: string | null;
  confidence_level?: string | null;
  cohort_did?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
  at_did?: string | null;
  created_at?: string | null;
}

export interface VertexProteinRow {
  vertex_id?: string | null;
  uniprot_id?: string | null;
  entry_name?: string | null;
  protein_name?: string | null;
  gene_name?: string | null;
  organism?: string | null;
  taxon_id?: string | null;
  sequence_length?: number | null;
  molecular_weight?: number | null;
  subcell_location?: string | null;
  function_text?: string | null;
  pfam_ids_json?: string | null;
  go_ids_json?: string | null;
  pdb_ids_json?: string | null;
  embed_cid?: string | null;
  kg_linked?: number | null;
  created_at?: string | null;
  sensitivity_ord?: number | null;
  org_id?: string | null;
  owner_did?: string | null;
}

export interface VertexPublicDatasetCatalogRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | bigint | null;
  owner_did?: string | null;
  dataset_id?: string | null;
  provider?: string | null;
  bq_project?: string | null;
  bq_dataset?: string | null;
  description?: string | null;
  homepage_url?: string | null;
  marketplace_url?: string | null;
  license?: string | null;
  terms_url?: string | null;
  last_modified_at?: string | null;
  table_count?: number | bigint | null;
  total_size_bytes_estimate?: number | bigint | null;
  pii_tier_guess?: number | bigint | null;
  allowed_for_train_guess?: string | null;
  allowed_for_embedding_guess?: string | null;
  recommended_ingest_mode?: string | null;
  candidate_vertex_targets_json?: string | null;
  candidate_edge_targets_json?: string | null;
  review_status?: string | null;
  review_note?: string | null;
  observed_at?: string | null;
  props?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
  at_did?: string | null;
  created_at?: string | null;
}

export interface VertexPublicDatasetProfileRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | bigint | null;
  owner_did?: string | null;
  profile_run_id?: string | null;
  table_vertex_id?: string | null;
  dataset_id?: string | null;
  bq_project?: string | null;
  bq_dataset?: string | null;
  bq_table?: string | null;
  columns_profiled_json?: string | null;
  key_candidate_json?: string | null;
  null_rate_json?: string | null;
  distinct_estimate_json?: string | null;
  top_values_json?: string | null;
  text_columns_json?: string | null;
  language_distribution_json?: string | null;
  text_length_stats_json?: string | null;
  timestamp_range_json?: string | null;
  geo_coverage_json?: string | null;
  pii_signal_json?: string | null;
  license_decision?: string | null;
  allowed_for_train?: string | null;
  allowed_for_embedding?: string | null;
  dedupe_strategy?: string | null;
  delta_strategy?: string | null;
  recommended_risingwave_tables_json?: string | null;
  recommended_edges_json?: string | null;
  recommended_ingest_mode?: string | null;
  estimated_monthly_refresh_scan_tib?: number | null;
  estimated_monthly_refresh_cost_usd?: number | null;
  profile_artifact_uri?: string | null;
  profile_hash?: string | null;
  bytes_billed?: number | bigint | null;
  profile_score?: number | null;
  review_status?: string | null;
  review_note?: string | null;
  observed_at?: string | null;
  props?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
  at_did?: string | null;
  created_at?: string | null;
}

export interface VertexPublicDatasetSampleRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | bigint | null;
  owner_did?: string | null;
  table_vertex_id?: string | null;
  dataset_id?: string | null;
  run_id?: string | null;
  job_id?: string | null;
  query_hash?: string | null;
  query_text_uri?: string | null;
  sample_rows_uri?: string | null;
  sample_format?: string | null;
  sample_row_count?: number | bigint | null;
  sample_byte_size?: number | bigint | null;
  sample_hash?: string | null;
  bytes_billed?: number | bigint | null;
  observed_at?: string | null;
  props?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
  at_did?: string | null;
  created_at?: string | null;
}

export interface VertexPublicDatasetTableRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | bigint | null;
  owner_did?: string | null;
  dataset_vertex_id?: string | null;
  dataset_id?: string | null;
  bq_project?: string | null;
  bq_dataset?: string | null;
  bq_table?: string | null;
  description?: string | null;
  table_kind?: string | null;
  schema_json?: string | null;
  partitioning_json?: string | null;
  clustering_json?: string | null;
  row_count_estimate?: number | bigint | null;
  size_bytes_estimate?: number | bigint | null;
  last_modified_at?: string | null;
  estimated_full_scan_cost_usd?: number | null;
  estimated_delta_scan_cost_usd?: number | null;
  review_status?: string | null;
  observed_at?: string | null;
  props?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
  at_did?: string | null;
  created_at?: string | null;
}

export interface VertexQaPostRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | bigint | null;
  owner_did?: string | null;
  source_dataset_id?: string | null;
  community?: string | null;
  post_type?: string | null;
  post_id?: string | null;
  parent_post_id?: string | null;
  accepted_answer_id?: string | null;
  title?: string | null;
  body_text_uri?: string | null;
  body_text_sha256?: string | null;
  body_byte_size?: number | bigint | null;
  score?: number | bigint | null;
  view_count?: number | bigint | null;
  answer_count?: number | bigint | null;
  comment_count?: number | bigint | null;
  favorite_count?: number | bigint | null;
  tags?: string | null;
  owner_user_id?: string | null;
  posted_at?: string | null;
  last_activity_at?: string | null;
  last_edit_at?: string | null;
  language?: string | null;
  license?: string | null;
  props?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
  at_did?: string | null;
  created_at?: string | null;
}

export interface VertexRareEarthCoverageRow {
  vertex_id?: string | null;
  mineral?: string | null;
  symbol?: string | null;
  source?: string | null;
  created_at?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  _seq?: number | bigint | null;
}

export interface VertexRecapDownloadRow {
  vertex_id?: string | null;
  rkey?: string | null;
  owner_did?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
  at_did?: string | null;
  source_url?: string | null;
  platform?: string | null;
  title?: string | null;
  uploader?: string | null;
  duration_sec?: number | null;
  upload_date?: string | null;
  format_id?: string | null;
  format_note?: string | null;
  blob_key?: string | null;
  blob_size_bytes?: number | bigint | null;
  thumbnail_url?: string | null;
  status?: string | null;
  scope?: string | null;
  error_msg?: string | null;
  created_at?: string | null;
  license?: string | null;
}

export interface VertexScientificPaperRow {
  vertex_id?: string | null;
  doi?: string | null;
  arxiv_id?: string | null;
  pmid?: string | null;
  title?: string | null;
  abstract_text?: string | null;
  journal?: string | null;
  venue?: string | null;
  published_at?: string | null;
  year?: number | bigint | null;
  citation_count?: number | bigint | null;
  domain?: string | null;
  subdomain?: string | null;
  embedding_norm?: number | null;
  ivf_cluster_id?: number | bigint | null;
  source?: string | null;
  status?: string | null;
  created_at?: string | null;
  sensitivity_ord?: number | bigint | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  owner_did?: string | null;
  _seq?: number | bigint | null;
}

export interface VertexScientificTaxonRow {
  vertex_id?: string | null;
  taxon_rank?: string | null;
  scientific_name?: string | null;
  common_name_ja?: string | null;
  common_name_en?: string | null;
  taxon_code?: string | null;
  parent_taxon_did?: string | null;
  domain_kind?: string | null;
  kami_model_def_id?: string | null;
  kami_canopy_shape?: string | null;
  render_profile_json?: string | null;
  description?: string | null;
  source?: string | null;
  created_at?: string | null;
  sensitivity_ord?: number | bigint | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  owner_did?: string | null;
  _seq?: number | bigint | null;
}

export interface VertexSekkeiApprovalRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  drawing_id?: string | null;
  rev_no?: string | null;
  approver_did?: string | null;
  approver_role?: string | null;
  decision?: string | null;
  decided_at?: string | null;
  conditions?: string | null;
  rejection_reason?: string | null;
  signature_ref?: string | null;
  notes?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
}

export interface VertexSekkeiBomLineRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  bom_line_id?: string | null;
  parent_drawing_id?: string | null;
  parent_rev_no?: string | null;
  child_item_code?: string | null;
  child_drawing_id?: string | null;
  child_item_name?: string | null;
  quantity?: number | null;
  unit?: string | null;
  level?: number | null;
  item_type?: string | null;
  supplier_did?: string | null;
  notes?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
}

export interface VertexSekkeiDrawingRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  drawing_id?: string | null;
  title?: string | null;
  drawing_type?: string | null;
  owner_did_drawing?: string | null;
  project_code?: string | null;
  assembly_code?: string | null;
  current_rev_no?: string | null;
  status?: string | null;
  cad_file_ref?: string | null;
  pdf_file_ref?: string | null;
  linked_actor_did?: string | null;
  tsukuru_manufacturer_did?: string | null;
  notes?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
}

export interface VertexSekkeiReleaseRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  drawing_id?: string | null;
  rev_no?: string | null;
  release_type?: string | null;
  released_by_did?: string | null;
  released_at?: string | null;
  target_product_code?: string | null;
  effective_date?: string | null;
  obsoletes_drawing_id?: string | null;
  distribution_list?: string | null;
  notes?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
}

export interface VertexSekkeiRevisionRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  drawing_id?: string | null;
  rev_no?: string | null;
  previous_rev_no?: string | null;
  revision_reason?: string | null;
  change_description?: string | null;
  revised_by_did?: string | null;
  revised_at?: string | null;
  cad_file_ref?: string | null;
  pdf_file_ref?: string | null;
  status?: string | null;
  affected_bom_lines?: string | null;
  notes?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
}

export interface VertexShoshaConsumerCursorRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  consumer_id?: string | null;
  upstream_did?: string | null;
  collection_prefix?: string | null;
  last_seq?: number | bigint | null;
  last_ts_ms?: number | bigint | null;
  last_seen_at?: string | null;
  records_seen?: number | bigint | null;
  reactions_emitted?: number | bigint | null;
  status?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface VertexShoshaCounterpartyRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  name?: string | null;
  name_normalized?: string | null;
  country?: string | null;
  legal_entity_id?: string | null;
  risk_band?: string | null;
  credit_limit_usd?: number | null;
  sanction_status?: string | null;
  sanction_flags?: string | null;
  last_reviewed_at?: string | null;
  status?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface VertexShoshaExposureSnapshotRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  as_of_ts_ms?: number | bigint | null;
  group_by?: string | null;
  group_key?: string | null;
  gross_long?: number | null;
  gross_short?: number | null;
  net?: number | null;
  hedged?: number | null;
  unhedged?: number | null;
  currency?: string | null;
  counterparty_top1?: string | null;
  counterparty_top1_pct?: number | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface VertexShoshaHedgeRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  hedge_id?: string | null;
  instrument?: string | null;
  commodity?: string | null;
  ref_trade_id?: string | null;
  direction?: string | null;
  notional?: number | null;
  currency?: string | null;
  strike?: number | null;
  expiry_date?: Date | string | null;
  broker?: string | null;
  target_hedge_ratio?: number | null;
  current_exposure?: number | null;
  rationale?: string | null;
  status?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface VertexShoshaIntelRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  source?: string | null;
  symbol?: string | null;
  category?: string | null;
  value?: number | null;
  unit?: string | null;
  ts_ms?: number | bigint | null;
  raw_json?: string | null;
  status?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface VertexShoshaMarketViewRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  commodity?: string | null;
  as_of_date?: Date | string | null;
  direction?: string | null;
  confidence?: number | null;
  price_target?: number | null;
  price_currency?: string | null;
  price_unit?: string | null;
  rationale?: string | null;
  intel_count_used?: number | null;
  llm_model?: string | null;
  status?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface VertexShoshaReactionRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  reaction_id?: string | null;
  upstream_did?: string | null;
  upstream_collection?: string | null;
  upstream_seq?: number | bigint | null;
  upstream_rkey?: string | null;
  upstream_record_vid?: string | null;
  reaction_type?: string | null;
  commodity?: string | null;
  direction?: string | null;
  target_action?: string | null;
  rationale?: string | null;
  confidence?: number | null;
  llm_model?: string | null;
  status?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface VertexShoshaSettlementRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  settlement_id?: string | null;
  ref_trade_id?: string | null;
  currency?: string | null;
  amount?: number | null;
  amount_usd?: number | null;
  method?: string | null;
  bank_ref?: string | null;
  value_date?: Date | string | null;
  counterparty_name?: string | null;
  counterparty_vid?: string | null;
  pnl_realized?: number | null;
  remarks?: string | null;
  status?: string | null;
  settled_at?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface VertexShoshaTradeRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  trade_id?: string | null;
  side?: string | null;
  commodity?: string | null;
  quantity?: number | null;
  unit?: string | null;
  price?: number | null;
  currency?: string | null;
  amount_usd?: number | null;
  counterparty_name?: string | null;
  counterparty_vid?: string | null;
  desk?: string | null;
  delivery_date?: Date | string | null;
  delivery_location?: string | null;
  rationale?: string | null;
  comply_ok?: boolean | null;
  comply_flags?: string | null;
  approval_state?: string | null;
  approver?: string | null;
  approved_at?: string | null;
  status?: string | null;
  pnl_realized?: number | null;
  pnl_unrealized?: number | null;
  pnl_marked_at?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface VertexSyntheticPatientRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | bigint | null;
  owner_did?: string | null;
  source_dataset_id?: string | null;
  person_id?: string | null;
  gender_concept_id?: number | bigint | null;
  year_of_birth?: number | null;
  month_of_birth?: number | null;
  race_concept_id?: number | bigint | null;
  ethnicity_concept_id?: number | bigint | null;
  location_id?: string | null;
  provider_id?: string | null;
  care_site_id?: string | null;
  condition_concept_id?: number | bigint | null;
  drug_concept_id?: number | bigint | null;
  visit_concept_id?: number | bigint | null;
  condition_start_date?: string | null;
  props?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
  at_did?: string | null;
  created_at?: string | null;
}

export interface VertexTargetEvidenceRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | bigint | null;
  owner_did?: string | null;
  source_dataset_id?: string | null;
  evidence_id?: string | null;
  target_id?: string | null;
  disease_id?: string | null;
  datatype_id?: string | null;
  datasource_id?: string | null;
  score?: number | null;
  evidence_origin?: string | null;
  literature_pmids?: string | null;
  release_year?: number | null;
  props?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
  at_did?: string | null;
  created_at?: string | null;
}

export interface VertexTaxiTripRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | bigint | null;
  owner_did?: string | null;
  source_dataset_id?: string | null;
  city?: string | null;
  vendor?: string | null;
  pickup_datetime?: string | null;
  dropoff_datetime?: string | null;
  passenger_count?: number | bigint | null;
  trip_distance_m?: number | bigint | null;
  pickup_latitude?: number | null;
  pickup_longitude?: number | null;
  dropoff_latitude?: number | null;
  dropoff_longitude?: number | null;
  fare_amount_minor?: number | bigint | null;
  tip_amount_minor?: number | bigint | null;
  total_amount_minor?: number | bigint | null;
  currency?: string | null;
  payment_type?: string | null;
  trip_id?: string | null;
  props?: string | null;
  actor_did?: string | null;
  org_did?: string | null;
  at_did?: string | null;
  created_at?: string | null;
}

export interface VertexTrainingCheckpointRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  checkpoint_id?: string | null;
  run_id?: string | null;
  step?: number | bigint | null;
  epoch?: number | null;
  train_loss?: number | null;
  eval_loss?: number | null;
  learning_rate?: number | null;
  weight_b2_uri?: string | null;
  weight_byte_size?: number | bigint | null;
  weight_sha256?: string | null;
  adapter_kind?: string | null;
  adapter_rank?: number | null;
  is_final?: boolean | null;
  tokenizer_b2_uri?: string | null;
  training_args_b2_uri?: string | null;
  status?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface VertexTrainingDatasetSnapshotRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  snapshot_id?: string | null;
  dataset_name?: string | null;
  label?: string | null;
  b2_prefix?: string | null;
  shard_count?: number | bigint | null;
  row_count?: number | bigint | null;
  byte_size?: number | bigint | null;
  content_hash?: string | null;
  hf_repo_id?: string | null;
  hf_revision?: string | null;
  source_view?: string | null;
  filter_expr?: string | null;
  status?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface VertexTrainingEvalRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  eval_id?: string | null;
  checkpoint_id?: string | null;
  run_id?: string | null;
  bench_name?: string | null;
  eval_dataset_snapshot_id?: string | null;
  metrics_json?: string | null;
  primary_metric?: string | null;
  primary_score?: number | null;
  sample_count?: number | bigint | null;
  duration_seconds?: number | null;
  eval_runner?: string | null;
  status?: string | null;
  evaluated_at?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface VertexTrainingRunRow {
  vertex_id?: string | null;
  _seq?: number | bigint | null;
  created_date?: Date | string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  run_id?: string | null;
  kind?: string | null;
  base_model?: string | null;
  base_model_revision?: string | null;
  dataset_snapshot_id?: string | null;
  teacher_run_id?: string | null;
  teacher_actor_did?: string | null;
  hyperparams_json?: string | null;
  gpu_target?: string | null;
  gpu_count?: number | null;
  seed?: number | bigint | null;
  total_steps?: number | bigint | null;
  completed_steps?: number | bigint | null;
  status?: string | null;
  started_at?: string | null;
  ended_at?: string | null;
  failure_reason?: string | null;
  triggered_by?: string | null;
  bpmn_process_instance_key?: string | null;
  created_at?: string | null;
  org_id?: string | null;
  user_id?: string | null;
  actor_id?: string | null;
}

export interface VertexTrainingShardRow {
  vertex_id?: string | null;
  dataset_name?: string | null;
  label?: string | null;
  shard_index?: number | bigint | null;
  row_count?: number | bigint | null;
  b2_key?: string | null;
  status?: string | null;
  created_date?: string | null;
  sensitivity_ord?: number | null;
  owner_did?: string | null;
  _seq?: number | bigint | null;
}

export interface ViewOpenSmartphoneOcel2ExportRow {
  event_sort_key?: number | bigint | null;
  event_id?: string | null;
  event_activity?: string | null;
  event_timestamp?: string | null;
  event_resource?: string | null;
  event_object_type?: string | null;
  omap_json?: string | null;
  vmap_json?: string | null;
  status?: string | null;
  duration_ms?: number | bigint | null;
}

export interface ViewOpenSmartphoneReadinessScorecardRow {
  bom_id?: string | null;
  design_name?: string | null;
  open_score?: number | null;
  soc_export_status?: string | null;
  soc_eccn?: string | null;
  export_severity?: string | null;
  type_approval_count?: number | bigint | null;
  approved_jurisdictions?: string | null;
  sep_5gnr_blockers?: number | bigint | null;
  sep_bt_blockers?: number | bigint | null;
  sep_5gnr_pool_covered?: number | bigint | null;
  alt_sources_available?: number | bigint | null;
  hal_upstream_count?: number | bigint | null;
  hal_blob_count?: number | bigint | null;
  latest_patch_level?: string | null;
  ems_open_issues?: number | bigint | null;
}

export interface ViewOpenSmartphoneV02DepGraphRow {
  node_type?: string | null;
  node_id?: string | null;
  node_label?: string | null;
  parent_id?: string | null;
  relationship?: string | null;
  detail_1?: string | null;
  detail_2?: string | null;
}

export interface ViewOpenSmartphoneWeightedScoreRow {
  bom_id?: string | null;
  design_name?: string | null;
  total_lines?: number | bigint | null;
  open_lines?: number | bigint | null;
  raw_pct?: number | null;
  weighted_pct?: number | null;
  soc_lines?: number | bigint | null;
  modem_lines?: number | bigint | null;
  os_lines?: number | bigint | null;
  sensor_lines?: number | bigint | null;
  ems_lines?: number | bigint | null;
  patent_lines?: number | bigint | null;
}

export interface ViewWorldCoverageLiveRow {
  domain?: string | null;
  app_host?: string | null;
  world_total?: number | bigint | null;
  unit?: string | null;
  sector?: string | null;
  did_count?: number | bigint | null;
  record_count?: number | bigint | null;
  vertex_count?: number | bigint | null;
  collected?: number | bigint | null;
  coverage_rate?: number | null;
  gap_rate?: number | null;
  remaining?: number | bigint | null;
}

// --- Database interface (table name -> Row type) ---

export interface Database {
  edge_business_person_relation: EdgeBusinessPersonRelationRow;
  edge_business_person_skill: EdgeBusinessPersonSkillRow;
  edge_chat_artifact_from_message: EdgeChatArtifactFromMessageRow;
  edge_chat_invocation_from_message: EdgeChatInvocationFromMessageRow;
  edge_chat_message_in_conversation: EdgeChatMessageInConversationRow;
  edge_chat_message_replies_to: EdgeChatMessageRepliesToRow;
  edge_cohort_ancestor_of: EdgeCohortAncestorOfRow;
  edge_cohort_belief_system: EdgeCohortBeliefSystemRow;
  edge_compound_crystal: EdgeCompoundCrystalRow;
  edge_compound_element: EdgeCompoundElementRow;
  edge_dataset_allowed_for_training_task: EdgeDatasetAllowedForTrainingTaskRow;
  edge_dataset_produces_vertex_type: EdgeDatasetProducesVertexTypeRow;
  edge_domain_registrar_supports_tld: EdgeDomainRegistrarSupportsTldRow;
  edge_domain_tld_accepts_regulator: EdgeDomainTldAcceptsRegulatorRow;
  edge_family_relation: EdgeFamilyRelationRow;
  edge_game_charted_at: EdgeGameChartedAtRow;
  edge_hf_dataset_collection_member: EdgeHfDatasetCollectionMemberRow;
  edge_hf_dataset_reliability_about: EdgeHfDatasetReliabilityAboutRow;
  edge_intel_dependency: EdgeIntelDependencyRow;
  edge_lifehack_tip_recommends_product: EdgeLifehackTipRecommendsProductRow;
  edge_lifehack_tip_solves_topic: EdgeLifehackTipSolvesTopicRow;
  edge_lifehack_topic_relates_to: EdgeLifehackTopicRelatesToRow;
  edge_live_room_lighting_cue: EdgeLiveRoomLightingCueRow;
  edge_live_room_track: EdgeLiveRoomTrackRow;
  edge_material_element: EdgeMaterialElementRow;
  edge_mineral_crystal: EdgeMineralCrystalRow;
  edge_mineral_element: EdgeMineralElementRow;
  edge_model_material: EdgeModelMaterialRow;
  edge_otakiage_item_handover: EdgeOtakiageItemHandoverRow;
  edge_otakiage_item_owner: EdgeOtakiageItemOwnerRow;
  edge_otakiage_item_ritual: EdgeOtakiageItemRitualRow;
  edge_otakiage_ritual_certificate: EdgeOtakiageRitualCertificateRow;
  edge_paper_compound: EdgePaperCompoundRow;
  edge_paper_element: EdgePaperElementRow;
  edge_paper_protein: EdgePaperProteinRow;
  edge_paper_taxon: EdgePaperTaxonRow;
  edge_protein_element: EdgeProteinElementRow;
  edge_public_dataset_candidate_for_training_task: EdgePublicDatasetCandidateForTrainingTaskRow;
  edge_public_dataset_candidate_for_vertex_type: EdgePublicDatasetCandidateForVertexTypeRow;
  edge_public_dataset_profiles_table: EdgePublicDatasetProfilesTableRow;
  edge_shosha_trade_counterparty: EdgeShoshaTradeCounterpartyRow;
  edge_shosha_trade_hedge: EdgeShoshaTradeHedgeRow;
  edge_shosha_trade_settlement: EdgeShoshaTradeSettlementRow;
  edge_taxon_model: EdgeTaxonModelRow;
  edge_training_consumed_dataset: EdgeTrainingConsumedDatasetRow;
  edge_training_distilled_from: EdgeTrainingDistilledFromRow;
  edge_training_promoted_to: EdgeTrainingPromotedToRow;
  mv_compound_element_coverage: MvCompoundElementCoverageRow;
  mv_crystal_coverage: MvCrystalCoverageRow;
  mv_element_material_coverage: MvElementMaterialCoverageRow;
  mv_game_genre_chart_dominance: MvGameGenreChartDominanceRow;
  mv_game_rank_trend: MvGameRankTrendRow;
  mv_hf_dataset_quality_top: MvHfDatasetQualityTopRow;
  mv_intel_building_owner_lei: MvIntelBuildingOwnerLeiRow;
  mv_intel_dependency_status: MvIntelDependencyStatusRow;
  mv_kaisya_pending_count: MvKaisyaPendingCountRow;
  mv_kami_tile_model_density: MvKamiTileModelDensityRow;
  mv_legal_corpus_jurisdiction_coverage: MvLegalCorpusJurisdictionCoverageRow;
  mv_mineral_element_composition: MvMineralElementCompositionRow;
  mv_natural_person_vital_stats: MvNaturalPersonVitalStatsRow;
  mv_open_adnetwork_campaign_funnel: MvOpenAdnetworkCampaignFunnelRow;
  mv_open_adnetwork_market_cpm_range: MvOpenAdnetworkMarketCpmRangeRow;
  mv_open_adnetwork_publisher_daily_kpi: MvOpenAdnetworkPublisherDailyKpiRow;
  mv_open_sales_activity_summary: MvOpenSalesActivitySummaryRow;
  mv_open_sales_pipeline_health: MvOpenSalesPipelineHealthRow;
  mv_open_sales_stage_velocity: MvOpenSalesStageVelocityRow;
  mv_open_smartphone_patent_free_zone: MvOpenSmartphonePatentFreeZoneRow;
  mv_person_cohort_belief_cross: MvPersonCohortBeliefCrossRow;
  mv_person_cohort_era_summary: MvPersonCohortEraSummaryRow;
  mv_protein_taxon_coverage: MvProteinTaxonCoverageRow;
  mv_public_dataset_catalog_coverage: MvPublicDatasetCatalogCoverageRow;
  mv_public_dataset_ingest_status: MvPublicDatasetIngestStatusRow;
  mv_public_dataset_profile_rank: MvPublicDatasetProfileRankRow;
  mv_science_paper_domain_stats: MvSciencePaperDomainStatsRow;
  mv_sekkei_stale_reviews: MvSekkeiStaleReviewsRow;
  mv_taxon_model_coverage: MvTaxonModelCoverageRow;
  mv_training_source_eligibility: MvTrainingSourceEligibilityRow;
  mv_world_coverage_live: MvWorldCoverageLiveRow;
  mv_world_vertex_per_host: MvWorldVertexPerHostRow;
  v_training_triple: VTrainingTripleRow;
  vertex_air_quality_observation: VertexAirQualityObservationRow;
  vertex_bigquery_export_artifact: VertexBigqueryExportArtifactRow;
  vertex_bigquery_ingest_job: VertexBigqueryIngestJobRow;
  vertex_bigquery_profile_run: VertexBigqueryProfileRunRow;
  vertex_blockchain_block: VertexBlockchainBlockRow;
  vertex_blockchain_tx: VertexBlockchainTxRow;
  vertex_business_person_career_event: VertexBusinessPersonCareerEventRow;
  vertex_business_person_cert: VertexBusinessPersonCertRow;
  vertex_business_person_edu: VertexBusinessPersonEduRow;
  vertex_chat_artifact: VertexChatArtifactRow;
  vertex_chat_checkpoint: VertexChatCheckpointRow;
  vertex_chat_conversation: VertexChatConversationRow;
  vertex_chat_memory: VertexChatMemoryRow;
  vertex_chat_message: VertexChatMessageRow;
  vertex_chat_session: VertexChatSessionRow;
  vertex_chat_tool_invocation: VertexChatToolInvocationRow;
  vertex_chemistry_patent: VertexChemistryPatentRow;
  vertex_collection_procedure: VertexCollectionProcedureRow;
  vertex_compound: VertexCompoundRow;
  vertex_crypto_asset_freeze_incident: VertexCryptoAssetFreezeIncidentRow;
  vertex_crystal_structure: VertexCrystalStructureRow;
  vertex_domain_eligibility_advice: VertexDomainEligibilityAdviceRow;
  vertex_domain_legal_regulator: VertexDomainLegalRegulatorRow;
  vertex_domain_registrar: VertexDomainRegistrarRow;
  vertex_domain_registration: VertexDomainRegistrationRow;
  vertex_domain_tld: VertexDomainTldRow;
  vertex_forest_inventory: VertexForestInventoryRow;
  vertex_fund: VertexFundRow;
  vertex_game_chart_analysis: VertexGameChartAnalysisRow;
  vertex_game_chart_snapshot: VertexGameChartSnapshotRow;
  vertex_hf_dataset: VertexHfDatasetRow;
  vertex_hf_dataset_collection: VertexHfDatasetCollectionRow;
  vertex_hf_dataset_record: VertexHfDatasetRecordRow;
  vertex_hf_dataset_reliability: VertexHfDatasetReliabilityRow;
  vertex_intel_evidence: VertexIntelEvidenceRow;
  vertex_intel_inference_run: VertexIntelInferenceRunRow;
  vertex_intel_subject: VertexIntelSubjectRow;
  vertex_ir_company: VertexIrCompanyRow;
  vertex_ir_pressrelease: VertexIrPressreleaseRow;
  vertex_ir_scraper_run: VertexIrScraperRunRow;
  vertex_kaisya_agent_run: VertexKaisyaAgentRunRow;
  vertex_kaisya_org_snapshot: VertexKaisyaOrgSnapshotRow;
  vertex_kaisya_task: VertexKaisyaTaskRow;
  vertex_kami_material_def: VertexKamiMaterialDefRow;
  vertex_kami_model_def: VertexKamiModelDefRow;
  vertex_kami_model_instance: VertexKamiModelInstanceRow;
  vertex_lifehack_environment_reading: VertexLifehackEnvironmentReadingRow;
  vertex_lifehack_post_log: VertexLifehackPostLogRow;
  vertex_lifehack_product: VertexLifehackProductRow;
  vertex_lifehack_tip: VertexLifehackTipRow;
  vertex_lifehack_topic: VertexLifehackTopicRow;
  vertex_lifehack_user_query: VertexLifehackUserQueryRow;
  vertex_live_chat: VertexLiveChatRow;
  vertex_live_lighting_cue: VertexLiveLightingCueRow;
  vertex_live_room: VertexLiveRoomRow;
  vertex_live_track: VertexLiveTrackRow;
  vertex_maps_building_3d: VertexMapsBuilding3dRow;
  vertex_maps_building_coverage: VertexMapsBuildingCoverageRow;
  vertex_marine_observation: VertexMarineObservationRow;
  vertex_mineral: VertexMineralRow;
  vertex_natural_person_birth_event: VertexNaturalPersonBirthEventRow;
  vertex_natural_person_demographic_stat: VertexNaturalPersonDemographicStatRow;
  vertex_natural_person_event_attendee: VertexNaturalPersonEventAttendeeRow;
  vertex_natural_person_id_document: VertexNaturalPersonIdDocumentRow;
  vertex_natural_person_person: VertexNaturalPersonPersonRow;
  vertex_open_adnetwork_ad_unit: VertexOpenAdnetworkAdUnitRow;
  vertex_open_adnetwork_advertiser: VertexOpenAdnetworkAdvertiserRow;
  vertex_open_adnetwork_campaign: VertexOpenAdnetworkCampaignRow;
  vertex_open_adnetwork_click: VertexOpenAdnetworkClickRow;
  vertex_open_adnetwork_conversion: VertexOpenAdnetworkConversionRow;
  vertex_open_adnetwork_impression: VertexOpenAdnetworkImpressionRow;
  vertex_open_adnetwork_publisher: VertexOpenAdnetworkPublisherRow;
  vertex_open_adnetwork_revenue_snapshot: VertexOpenAdnetworkRevenueSnapshotRow;
  vertex_open_sales_account: VertexOpenSalesAccountRow;
  vertex_open_sales_activity: VertexOpenSalesActivityRow;
  vertex_open_sales_contact: VertexOpenSalesContactRow;
  vertex_open_sales_forecast: VertexOpenSalesForecastRow;
  vertex_open_sales_lead: VertexOpenSalesLeadRow;
  vertex_open_sales_opportunity: VertexOpenSalesOpportunityRow;
  vertex_open_sales_quote: VertexOpenSalesQuoteRow;
  vertex_open_smartphone_bom: VertexOpenSmartphoneBomRow;
  vertex_open_smartphone_bom_line: VertexOpenSmartphoneBomLineRow;
  vertex_open_smartphone_bom_sourcer: VertexOpenSmartphoneBomSourcerRow;
  vertex_open_smartphone_ems_compliance: VertexOpenSmartphoneEmsComplianceRow;
  vertex_open_smartphone_ems_facility: VertexOpenSmartphoneEmsFacilityRow;
  vertex_open_smartphone_ems_order: VertexOpenSmartphoneEmsOrderRow;
  vertex_open_smartphone_modem_sep_dep: VertexOpenSmartphoneModemSepDepRow;
  vertex_open_smartphone_modem_spec: VertexOpenSmartphoneModemSpecRow;
  vertex_open_smartphone_modem_type_approval: VertexOpenSmartphoneModemTypeApprovalRow;
  vertex_open_smartphone_os_build: VertexOpenSmartphoneOsBuildRow;
  vertex_open_smartphone_os_hal_driver: VertexOpenSmartphoneOsHalDriverRow;
  vertex_open_smartphone_os_ota: VertexOpenSmartphoneOsOtaRow;
  vertex_open_smartphone_patent_dep: VertexOpenSmartphonePatentDepRow;
  vertex_open_smartphone_patent_pool: VertexOpenSmartphonePatentPoolRow;
  vertex_open_smartphone_patent_sep: VertexOpenSmartphonePatentSepRow;
  vertex_open_smartphone_sensor_calibration: VertexOpenSmartphoneSensorCalibrationRow;
  vertex_open_smartphone_sensor_driver: VertexOpenSmartphoneSensorDriverRow;
  vertex_open_smartphone_sensor_module: VertexOpenSmartphoneSensorModuleRow;
  vertex_open_smartphone_soc_design: VertexOpenSmartphoneSocDesignRow;
  vertex_open_smartphone_soc_export_flag: VertexOpenSmartphoneSocExportFlagRow;
  vertex_open_smartphone_soc_fab_order: VertexOpenSmartphoneSocFabOrderRow;
  vertex_otakiage_certificate: VertexOtakiageCertificateRow;
  vertex_otakiage_conversation: VertexOtakiageConversationRow;
  vertex_otakiage_conversation_turn: VertexOtakiageConversationTurnRow;
  vertex_otakiage_handover: VertexOtakiageHandoverRow;
  vertex_otakiage_item: VertexOtakiageItemRow;
  vertex_otakiage_matsuri: VertexOtakiageMatsuriRow;
  vertex_otakiage_reuse_request: VertexOtakiageReuseRequestRow;
  vertex_otakiage_ritual: VertexOtakiageRitualRow;
  vertex_periodic_element: VertexPeriodicElementRow;
  vertex_person_population_cohort: VertexPersonPopulationCohortRow;
  vertex_protein: VertexProteinRow;
  vertex_public_dataset_catalog: VertexPublicDatasetCatalogRow;
  vertex_public_dataset_profile: VertexPublicDatasetProfileRow;
  vertex_public_dataset_sample: VertexPublicDatasetSampleRow;
  vertex_public_dataset_table: VertexPublicDatasetTableRow;
  vertex_qa_post: VertexQaPostRow;
  vertex_rare_earth_coverage: VertexRareEarthCoverageRow;
  vertex_recap_download: VertexRecapDownloadRow;
  vertex_scientific_paper: VertexScientificPaperRow;
  vertex_scientific_taxon: VertexScientificTaxonRow;
  vertex_sekkei_approval: VertexSekkeiApprovalRow;
  vertex_sekkei_bom_line: VertexSekkeiBomLineRow;
  vertex_sekkei_drawing: VertexSekkeiDrawingRow;
  vertex_sekkei_release: VertexSekkeiReleaseRow;
  vertex_sekkei_revision: VertexSekkeiRevisionRow;
  vertex_shosha_consumer_cursor: VertexShoshaConsumerCursorRow;
  vertex_shosha_counterparty: VertexShoshaCounterpartyRow;
  vertex_shosha_exposure_snapshot: VertexShoshaExposureSnapshotRow;
  vertex_shosha_hedge: VertexShoshaHedgeRow;
  vertex_shosha_intel: VertexShoshaIntelRow;
  vertex_shosha_market_view: VertexShoshaMarketViewRow;
  vertex_shosha_reaction: VertexShoshaReactionRow;
  vertex_shosha_settlement: VertexShoshaSettlementRow;
  vertex_shosha_trade: VertexShoshaTradeRow;
  vertex_synthetic_patient: VertexSyntheticPatientRow;
  vertex_target_evidence: VertexTargetEvidenceRow;
  vertex_taxi_trip: VertexTaxiTripRow;
  vertex_training_checkpoint: VertexTrainingCheckpointRow;
  vertex_training_dataset_snapshot: VertexTrainingDatasetSnapshotRow;
  vertex_training_eval: VertexTrainingEvalRow;
  vertex_training_run: VertexTrainingRunRow;
  vertex_training_shard: VertexTrainingShardRow;
  view_open_smartphone_ocel2_export: ViewOpenSmartphoneOcel2ExportRow;
  view_open_smartphone_readiness_scorecard: ViewOpenSmartphoneReadinessScorecardRow;
  view_open_smartphone_v02_dep_graph: ViewOpenSmartphoneV02DepGraphRow;
  view_open_smartphone_weighted_score: ViewOpenSmartphoneWeightedScoreRow;
  view_world_coverage_live: ViewWorldCoverageLiveRow;
}
