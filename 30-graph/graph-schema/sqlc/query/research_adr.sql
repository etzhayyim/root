-- name: AdrListFiltered :many
-- ADR frontmatter graph listing with relation counts.
-- Used by etzhayyim.research.listAdrs (mcp-adapter.ts).
SELECT
  did_path,
  adr_id,
  title,
  status,
  topic,
  authoritative,
  last_verified,
  related_count,
  supersedes_count,
  superseded_by_count,
  amends_count,
  amended_by_count
FROM public.mv_research_adr_graph
WHERE (sqlc.narg('status')::text IS NULL OR status = sqlc.narg('status')::text)
  AND (sqlc.narg('topic_substr')::text IS NULL OR topic ILIKE '%' || sqlc.narg('topic_substr')::text || '%')
  AND (sqlc.narg('title_substr')::text IS NULL OR title ILIKE '%' || sqlc.narg('title_substr')::text || '%')
  AND (sqlc.narg('authoritative_only')::boolean IS NULL
       OR sqlc.narg('authoritative_only')::boolean = FALSE
       OR authoritative = TRUE)
ORDER BY adr_id
LIMIT sqlc.arg('row_limit')::integer
OFFSET sqlc.arg('row_offset')::integer;

-- name: AdrRelationsForId :many
-- Outbound relations from one ADR (graph traversal step).
SELECT to_did, relation
FROM public.edge_research_adr_relates
WHERE from_did = sqlc.arg('from_did')::text
ORDER BY relation, to_did;
