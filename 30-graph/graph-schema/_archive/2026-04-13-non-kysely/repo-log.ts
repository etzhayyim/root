/**
 * Repo commit log + block store + consumer cursor.
 *
 * P10v2 vertex/edge naming convention (migrated 2026-04-12, migration 0004).
 *
 * Architecture:
 *   PDS createRecord → vertex_repo_commit INSERT (append-only) → return
 *   Graph Worker consumer → SELECT vertex_repo_commit WHERE seq > cursor → INSERT vertex_*
 *
 * vertex_repo_commit   = AT Protocol-compatible commit log (= queue)
 *   vertex_id          = '{repo}:seq:{seq}'
 * vertex_repo_block    = IPLD block store (CBOR content-addressed)
 *   vertex_id          = '{repo}/{cid}'
 * vertex_consumer_cursor = Graph Worker consumer offset
 *   vertex_id          = consumer_id
 *
 * NOTE: Table DDL is defined in migrations/0004_repo_log_to_vertex.ts
 * This file is for reference and type definitions only.
 */

// Type interfaces for vertex_repo_commit table
export interface VertexRepoCommitRow {
  vertexId?: string;
  seq: number;
  repo: string;
  collection: string;
  rkey: string;
  action: string;
  rev: string;
  cid?: string;
  prev?: string;
  sig?: string;
  valueJson?: string;
  tsMs?: number;
  recordCid?: string;
  createdAt?: string;
}

// Type interfaces for vertex_repo_block table
export interface VertexRepoBlockRow {
  vertexId?: string;
  cid: string;
  repo: string;
  content?: string;
  sizeBytes?: number;
  createdAt?: string;
}

// Type interfaces for vertex_consumer_cursor table
export interface VertexConsumerCursorRow {
  vertexId?: string;
  consumerId: string;
  lastSeq: number;
  updatedAt?: string;
}

/**
 * Build vertex_id for vertex_repo_commit.
 * Format: '{repo}:seq:{seq}'
 */
export function repoCommitVertexId(repo: string, seq: number): string {
  return `${repo}:seq:${seq}`;
}

/**
 * Build vertex_id for vertex_repo_block.
 * Format: '{repo}/{cid}'
 */
export function repoBlockVertexId(repo: string, cid: string): string {
  return `${repo}/${cid}`;
}
