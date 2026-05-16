/**
 * @gftd/graph-schema — generated DB types for the GFTD graph DB (RisingWave).
 *
 * Single source of truth for database schema definitions.
 * Migration: Kysely migration runtime → SQLAlchemy/Alembic/SQLMesh (2026-05-07)
 */

// Re-export Kysely database types
export type { Database } from './database.js';
export * from './database.js';
export type { StrictDatabase, ForbiddenLegacyTables } from './database-strict.js';

// Helper functions for table resolution
export {
  resolveVertexTable,
  resolveEdgeTable,
  getAllVertexTables,
  getAllEdgeTables,
} from './helpers.js';

export {
  listOilCoverageLive,
  listOilCoverageGaps,
  getOilCoverageSummary,
} from './oil-coverage.js';

export {
  listLatestNaphthaPrices,
  listNaphthaCargoFlows,
  listNaphthaCountryBalance,
  listNaphthaMarketNodes,
  listNaphthaSupplyChainTrace,
  type NaphthaTraceFilters,
} from './naphtha-supply-chain.js';

export {
  computeDependencyTopologyOrder,
  type ComputeDependencyTopologyOptions,
  type DependencyTopologyEdge,
  type DependencyTopologyNode,
  type DependencyTopologyOrderRow,
} from './dependency-topology.js';

// ADR-0040 vertex DID tier policy
export {
  getVertexTier,
  listVertexTier,
  VERTEX_TIER_A,
  VERTEX_TIER_B,
  VERTEX_TIER_C,
  VERTEX_TIER_TOTAL,
  type VertexTier,
} from './vertex-tier.gen.js';
