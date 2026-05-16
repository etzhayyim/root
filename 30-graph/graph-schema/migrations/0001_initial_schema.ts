import { Kysely, sql } from 'kysely';

export async function up(db: Kysely<any>): Promise<void> {
  // vertex_actor
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_actor" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "did" VARCHAR(512), "nanoid" VARCHAR(64), "handle" VARCHAR(512), "display_name" VARCHAR(1024), "avatar_cid" VARCHAR(512), "banner_cid" VARCHAR(512), "execution_tier" VARCHAR(8), "status" VARCHAR(64), "collection" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "created_at" VARCHAR(64), "name" VARCHAR(512), "project" VARCHAR(512), "performer_type" VARCHAR(64), "runtime_type" VARCHAR(64), "ui_type" VARCHAR(64), "agent_type" VARCHAR(64), "classification" VARCHAR(64), "operator" VARCHAR(256), "category" VARCHAR(128), "country" VARCHAR(8), "shinka_heartbeat" VARCHAR(512), "shinka_follow" VARCHAR(512), "kyumei_gather" VARCHAR(512), "gov_rbac" VARCHAR(512), "gov_raci" VARCHAR(512), "gov_approval" VARCHAR(512), "agent_tools" VARCHAR(512), "agent_invoke" VARCHAR(512), "capability_declare" VARCHAR(512), "social_subscribe" VARCHAR(512), "social_post" VARCHAR(512), "write_public" VARCHAR(512), "graph_query" VARCHAR(512), "ocel_event" VARCHAR(512), "bpmn_task" VARCHAR(512), "command_count" BIGINT, "query_count" BIGINT, "val" TEXT);`.compile(db));
  // vertex_actor_convo_prompt
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_actor_convo_prompt" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "actor_did" VARCHAR(512), "convo_system_prompt" TEXT);`.compile(db));
  // vertex_profile
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_profile" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "did" VARCHAR(512), "repo" VARCHAR(512), "handle" VARCHAR(512), "display_name" VARCHAR(1024), "description" VARCHAR(4096), "avatar_cid" VARCHAR(512), "banner_cid" VARCHAR(512), "sensitivity" VARCHAR(64), "props" VARCHAR(4096), "collection" VARCHAR(512), "rkey" VARCHAR(64), "created_at" VARCHAR(64));`.compile(db));
  // vertex_post
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_post" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "text" VARCHAR(8192), "embed" VARCHAR(16384), "facets" VARCHAR(8192), "langs" VARCHAR(1024), "reply_root" VARCHAR(1024), "reply_parent" VARCHAR(1024), "tags" VARCHAR(1024), "created_at" VARCHAR(64), "embedding" REAL[], "embedding_norm" DOUBLE PRECISION, "ivf_cluster_id" BIGINT);`.compile(db));
  // vertex_message
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_message" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "convo_id" VARCHAR(512), "sender_did" VARCHAR(512), "text" VARCHAR(8192), "embed" VARCHAR(16384), "embedding" REAL[], "embedding_norm" DOUBLE PRECISION, "ivf_cluster_id" BIGINT);`.compile(db));
  // vertex_app
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_app" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "did" VARCHAR(512), "nanoid" VARCHAR(64), "handle" VARCHAR(512), "display_name" VARCHAR(1024), "description" VARCHAR(4096), "status" VARCHAR(64), "collection" VARCHAR(512));`.compile(db));
  // vertex_handle
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_handle" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "did" VARCHAR(512));`.compile(db));
  // vertex_list
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_list" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "display_name" VARCHAR(1024), "description" VARCHAR(4096), "purpose" VARCHAR(256));`.compile(db));
  // vertex_convo
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_convo" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "convo_id" VARCHAR(512), "display_name" VARCHAR(1024), "status" VARCHAR(64), "branch_source_convo_id" VARCHAR(512), "branch_point_rkey" VARCHAR(64), "props" TEXT);`.compile(db));
  // vertex_governance
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_governance" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "name" VARCHAR(1024), "kind" VARCHAR(256), "standard" VARCHAR(256));`.compile(db));
  // vertex_capability
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_capability" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "name" VARCHAR(1024), "description" VARCHAR(4096), "collection" VARCHAR(512), "status" VARCHAR(64), "props" TEXT);`.compile(db));
  // vertex_actor_manifest
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_actor_manifest" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "did" VARCHAR(512), "name" VARCHAR(1024), "nanoid" VARCHAR(64), "display_name" VARCHAR(1024), "description" TEXT, "execution_tier" VARCHAR(8), "performer_type" VARCHAR(64), "capabilities_json" TEXT, "pipelines_json" TEXT, "triggers_json" TEXT, "profile_json" TEXT, "governance_json" TEXT, "collection" VARCHAR(512), "status" VARCHAR(64), "val" TEXT);`.compile(db));
  // vertex_actor_coverage
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_actor_coverage" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "did" VARCHAR(512), "collection" VARCHAR(512), "status" VARCHAR(64), "actorDid" VARCHAR(512), "actorName" VARCHAR(512), "nanoid" VARCHAR(64), "bucket" VARCHAR(64), "nodeCount" BIGINT, "latestTs" VARCHAR(64), "topCollections" TEXT, "freshnessRate" DOUBLE PRECISION, "totalNodes" BIGINT, "freshNodes" BIGINT, "snapshotTs" VARCHAR(64));`.compile(db));
  // vertex_gov_coverage_snapshot
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_gov_coverage_snapshot" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "did" VARCHAR(512), "collection" VARCHAR(512), "status" VARCHAR(64), "actorDid" VARCHAR(512), "actorPath" VARCHAR(512), "actorName" VARCHAR(512), "domainCode" VARCHAR(64), "orgTier" VARCHAR(64), "canonicalCoverage" DOUBLE PRECISION, "entityCoverage" DOUBLE PRECISION, "sourceCoverage" DOUBLE PRECISION, "documentCoverage" DOUBLE PRECISION, "knowledgeCoverage" DOUBLE PRECISION, "overallCoverage" DOUBLE PRECISION, "expectedEntityCount" BIGINT, "actualEntityCount" BIGINT, "expectedSourceTypesJson" TEXT, "coveredSourceTypesJson" TEXT, "expectedDocumentClassesJson" TEXT, "coveredDocumentClassesJson" TEXT, "discoveredDocs" BIGINT, "fetchedDocs" BIGINT, "renderedDocs" BIGINT, "ocrDocs" BIGINT, "linkedDocs" BIGINT, "snapshotTs" VARCHAR(64), "gapSummary" TEXT, "props" TEXT);`.compile(db));
  // vertex_gov_source
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_gov_source" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "did" VARCHAR(512), "collection" VARCHAR(512), "status" VARCHAR(64), "actorDid" VARCHAR(512), "actorPath" VARCHAR(512), "actorName" VARCHAR(512), "sourceType" VARCHAR(128), "sourceUrl" VARCHAR(2048), "format" VARCHAR(128), "discoveryMethod" VARCHAR(128), "coverageStage" VARCHAR(128), "lastSeenAt" VARCHAR(64), "props" TEXT);`.compile(db));
  // vertex_gov_document
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_gov_document" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "did" VARCHAR(512), "collection" VARCHAR(512), "status" VARCHAR(64), "actorDid" VARCHAR(512), "actorPath" VARCHAR(512), "actorName" VARCHAR(512), "sourceUrl" VARCHAR(2048), "docType" VARCHAR(128), "mimeType" VARCHAR(128), "title" VARCHAR(1024), "publishedAt" VARCHAR(64), "fetchedAt" VARCHAR(64), "renderStatus" VARCHAR(64), "ocrStatus" VARCHAR(64), "textStatus" VARCHAR(64), "lineageStatus" VARCHAR(64), "props" TEXT);`.compile(db));
  // vertex_gov_coverage_gap
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_gov_coverage_gap" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "did" VARCHAR(512), "collection" VARCHAR(512), "status" VARCHAR(64), "actorDid" VARCHAR(512), "actorPath" VARCHAR(512), "actorName" VARCHAR(512), "gapType" VARCHAR(128), "severity" VARCHAR(32), "nextAction" VARCHAR(256), "coverageKind" VARCHAR(64), "scoreBefore" DOUBLE PRECISION, "targetScore" DOUBLE PRECISION, "dueAt" VARCHAR(64), "props" TEXT);`.compile(db));
  // vertex_gov_org
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_gov_org" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "path" VARCHAR(512), "name" VARCHAR(512), "name_en" VARCHAR(512), "website" VARCHAR(2048), "contract" VARCHAR(512), "tags" TEXT, "domain_code" VARCHAR(64), "org_tier" VARCHAR(64), "site_domain_slug" VARCHAR(512), "site_followed" VARCHAR(16), "did_registered" VARCHAR(16), "last_ingested_at" VARCHAR(64), "last_content_hash" VARCHAR(256), "last_kyumei_at" VARCHAR(64), "last_shinka_at" VARCHAR(64), "parent_path" VARCHAR(512), "parent_did" VARCHAR(512), "municipal_type" VARCHAR(64), "governance_linked" VARCHAR(16), "contract_did" VARCHAR(512), "bpmn_registered" VARCHAR(16), "created_at" VARCHAR(64), "props" TEXT);`.compile(db));
  // vertex_governance_contract
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_governance_contract" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "contract_did" VARCHAR(512), "contract_slug" VARCHAR(256), "name" VARCHAR(512), "name_en" VARCHAR(512), "legal_basis" VARCHAR(512), "effective_date" VARCHAR(64), "url" VARCHAR(2048), "gov_level" VARCHAR(64), "cofog_code" VARCHAR(64), "country_code" VARCHAR(64), "tags" TEXT, "seeded_at" VARCHAR(64), "props" TEXT);`.compile(db));
  // vertex_shinka_evolution
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_shinka_evolution" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "did" VARCHAR(512), "collection" VARCHAR(512), "actorDid" VARCHAR(512), "actorName" VARCHAR(512), "nanoid" VARCHAR(64), "status" VARCHAR(64), "created_at" VARCHAR(64), "props" TEXT);`.compile(db));
  // vertex_shinka_knowledge
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_shinka_knowledge" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "did" VARCHAR(512), "collection" VARCHAR(512), "actorDid" VARCHAR(512), "actorName" VARCHAR(512), "nanoid" VARCHAR(64), "status" VARCHAR(64), "created_at" VARCHAR(64), "props" TEXT);`.compile(db));
  // vertex_page
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_page" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "url" VARCHAR(2048), "domain" VARCHAR(512), "title" VARCHAR(1024), "description" VARCHAR(4096), "language" VARCHAR(64), "content_type" VARCHAR(256), "status_code" VARCHAR(16), "outlink_count" BIGINT, "crawl" VARCHAR(256), "ip_address" VARCHAR(64), "og_image" VARCHAR(2048), "robots" VARCHAR(256), "content_hash" VARCHAR(256), "previous_content_hash" VARCHAR(256), "version" BIGINT, "crawled_at" VARCHAR(64));`.compile(db));
  // vertex_wet_chunk
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_wet_chunk" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "page_rkey" VARCHAR(64), "url" VARCHAR(2048), "domain" VARCHAR(512), "chunk_index" BIGINT, "total_chunks" BIGINT, "markdown" TEXT, "content_hash" VARCHAR(256), "language" VARCHAR(64), "title" VARCHAR(1024), "section" VARCHAR(1024), "token_count" BIGINT, "crawled_at" VARCHAR(64), "embedding" REAL[], "embedding_norm" DOUBLE PRECISION, "ivf_cluster_id" BIGINT);`.compile(db));
  // vertex_did
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_did" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "did" VARCHAR(512), "repo" VARCHAR(512), "label" VARCHAR(256), "doc" TEXT);`.compile(db));
  // vertex_domain
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_domain" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "domain" VARCHAR(512), "did" VARCHAR(512), "handle" VARCHAR(512), "display_name" VARCHAR(512), "topics" VARCHAR(1024), "performer_type" VARCHAR(64), "status" VARCHAR(64));`.compile(db));
  // vertex_collection_job
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_collection_job" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "source_id" VARCHAR(256), "source_name" VARCHAR(512), "source_url" VARCHAR(2048), "format" VARCHAR(64), "status" VARCHAR(64), "topics" VARCHAR(1024), "language" VARCHAR(64), "crawl_type" VARCHAR(128), "title" VARCHAR(1024));`.compile(db));
  // vertex_frontier
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_frontier" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "url" VARCHAR(2048), "domain" VARCHAR(512), "status" VARCHAR(64), "priority" BIGINT, "depth" BIGINT, "topics" VARCHAR(1024), "source" VARCHAR(256));`.compile(db));
  // vertex_screenshot
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_screenshot" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "url" VARCHAR(2048), "domain" VARCHAR(512), "blob_ref" VARCHAR(256), "format" VARCHAR(32), "width" BIGINT, "height" BIGINT, "quality" BIGINT, "file_size" BIGINT, "content_hash" VARCHAR(256), "captured_at" VARCHAR(64));`.compile(db));
  // vertex_wat
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_wat" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "url" VARCHAR(2048), "domain" VARCHAR(512), "headers" TEXT, "outlinks" TEXT, "og_title" VARCHAR(1024), "og_description" VARCHAR(4096), "og_image" VARCHAR(2048), "language" VARCHAR(64), "content_type" VARCHAR(256), "status_code" VARCHAR(16));`.compile(db));
  // vertex_ivf_centroid
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_ivf_centroid" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "collection" VARCHAR(512), "embedding" REAL[]);`.compile(db));
  // vertex_article
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_article" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "text" VARCHAR(8192), "display_name" VARCHAR(1024), "description" VARCHAR(4096), "props" TEXT, "embedding" REAL[], "embedding_norm" DOUBLE PRECISION, "ivf_cluster_id" BIGINT);`.compile(db));
  // vertex_authority_sovereign
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_authority_sovereign" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "name" VARCHAR(1024), "display_name" VARCHAR(1024), "description" VARCHAR(4096), "kind" VARCHAR(256), "authority_kind" VARCHAR(128), "tier" VARCHAR(64), "jurisdiction" VARCHAR(512), "effective_date" VARCHAR(64), "enacted_by" VARCHAR(512), "standard" VARCHAR(256), "url" VARCHAR(2048));`.compile(db));
  // vertex_authority_treaty
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_authority_treaty" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "name" VARCHAR(1024), "display_name" VARCHAR(1024), "description" VARCHAR(4096), "kind" VARCHAR(256), "authority_kind" VARCHAR(128), "tier" VARCHAR(64), "jurisdiction" VARCHAR(512), "effective_date" VARCHAR(64), "enacted_by" VARCHAR(512), "standard" VARCHAR(256), "url" VARCHAR(2048));`.compile(db));
  // vertex_authority_religious
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_authority_religious" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "name" VARCHAR(1024), "display_name" VARCHAR(1024), "description" VARCHAR(4096), "kind" VARCHAR(256), "authority_kind" VARCHAR(128), "tier" VARCHAR(64), "jurisdiction" VARCHAR(512), "source" VARCHAR(256));`.compile(db));
  // vertex_authority_customary
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_authority_customary" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "name" VARCHAR(1024), "display_name" VARCHAR(1024), "description" VARCHAR(4096), "kind" VARCHAR(256), "authority_kind" VARCHAR(128), "tier" VARCHAR(64), "jurisdiction" VARCHAR(512), "source" VARCHAR(256));`.compile(db));
  // vertex_authority_professional
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_authority_professional" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "name" VARCHAR(1024), "display_name" VARCHAR(1024), "description" VARCHAR(4096), "kind" VARCHAR(256), "authority_kind" VARCHAR(128), "tier" VARCHAR(64), "standard" VARCHAR(256), "effective_date" VARCHAR(64), "source" VARCHAR(256));`.compile(db));
  // vertex_authority_industry
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_authority_industry" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "name" VARCHAR(1024), "display_name" VARCHAR(1024), "description" VARCHAR(4096), "kind" VARCHAR(256), "authority_kind" VARCHAR(128), "tier" VARCHAR(64), "standard" VARCHAR(256), "effective_date" VARCHAR(64), "source" VARCHAR(256), "url" VARCHAR(2048));`.compile(db));
  // vertex_authority_blockchain
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_authority_blockchain" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "name" VARCHAR(1024), "display_name" VARCHAR(1024), "description" VARCHAR(4096), "kind" VARCHAR(256), "authority_kind" VARCHAR(128), "tier" VARCHAR(64), "standard" VARCHAR(256), "url" VARCHAR(2048));`.compile(db));
  // vertex_authority_community
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_authority_community" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "name" VARCHAR(1024), "display_name" VARCHAR(1024), "description" VARCHAR(4096), "kind" VARCHAR(256), "authority_kind" VARCHAR(128), "tier" VARCHAR(64), "source" VARCHAR(256));`.compile(db));
  // vertex_game_item
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_game_item" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "name" VARCHAR(1024), "display_name" VARCHAR(1024), "description" VARCHAR(4096), "item_type" VARCHAR(128), "rarity" VARCHAR(64), "level" BIGINT, "effect" VARCHAR(1024), "props" TEXT, "embedding" REAL[], "embedding_norm" DOUBLE PRECISION, "ivf_cluster_id" BIGINT);`.compile(db));
  // vertex_game_recipe
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_game_recipe" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "name" VARCHAR(1024), "display_name" VARCHAR(1024), "description" VARCHAR(4096), "recipe_inputs" TEXT, "recipe_output" VARCHAR(512), "level" BIGINT, "cooldown_ms" BIGINT);`.compile(db));
  // vertex_game_actor
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_game_actor" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "name" VARCHAR(1024), "display_name" VARCHAR(1024), "description" VARCHAR(4096), "level" BIGINT, "props" TEXT);`.compile(db));
  // vertex_game_quest
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_game_quest" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "name" VARCHAR(1024), "display_name" VARCHAR(1024), "description" VARCHAR(4096), "status" VARCHAR(64), "level" BIGINT, "props" TEXT);`.compile(db));
  // vertex_transport
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_transport" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "name" VARCHAR(1024), "display_name" VARCHAR(1024), "description" VARCHAR(4096), "category" VARCHAR(256), "code" VARCHAR(512), "manufacturer" VARCHAR(512), "model" VARCHAR(512), "lat" DOUBLE PRECISION, "lng" DOUBLE PRECISION, "geohash" VARCHAR(32), "status" VARCHAR(64), "props" TEXT);`.compile(db));
  // vertex_threat
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_threat" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "name" VARCHAR(1024), "display_name" VARCHAR(1024), "description" VARCHAR(4096), "category" VARCHAR(256), "severity" VARCHAR(64), "code" VARCHAR(512), "url" VARCHAR(2048), "source" VARCHAR(256), "props" TEXT);`.compile(db));
  // vertex_serial
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_serial" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "name" VARCHAR(1024), "display_name" VARCHAR(1024), "serial_number" VARCHAR(1024), "manufacturer" VARCHAR(512), "model" VARCHAR(512), "category" VARCHAR(256), "props" TEXT);`.compile(db));
  // vertex_medical
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_medical" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "name" VARCHAR(1024), "display_name" VARCHAR(1024), "description" VARCHAR(4096), "category" VARCHAR(256), "code" VARCHAR(512), "standard" VARCHAR(256), "effective_date" VARCHAR(64), "props" TEXT);`.compile(db));
  // vertex_software
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_software" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "name" VARCHAR(1024), "display_name" VARCHAR(1024), "description" VARCHAR(4096), "category" VARCHAR(256), "url" VARCHAR(2048), "code" VARCHAR(512), "standard" VARCHAR(256), "props" TEXT);`.compile(db));
  // vertex_waste
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_waste" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "name" VARCHAR(1024), "display_name" VARCHAR(1024), "description" VARCHAR(4096), "category" VARCHAR(256), "quantity" BIGINT, "unit" VARCHAR(64), "lat" DOUBLE PRECISION, "lng" DOUBLE PRECISION, "props" TEXT);`.compile(db));
  // vertex_building
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_building" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "name" VARCHAR(1024), "display_name" VARCHAR(1024), "description" VARCHAR(4096), "category" VARCHAR(256), "lat" DOUBLE PRECISION, "lng" DOUBLE PRECISION, "geohash" VARCHAR(32), "capacity" BIGINT, "props" TEXT);`.compile(db));
  // vertex_fiction
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_fiction" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "name" VARCHAR(1024), "display_name" VARCHAR(1024), "description" VARCHAR(4096), "category" VARCHAR(256), "props" TEXT, "embedding" REAL[], "embedding_norm" DOUBLE PRECISION, "ivf_cluster_id" BIGINT);`.compile(db));
  // vertex_contract
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_contract" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "name" VARCHAR(1024), "display_name" VARCHAR(1024), "description" VARCHAR(4096), "category" VARCHAR(256), "effective_date" VARCHAR(64), "status" VARCHAR(64), "props" TEXT);`.compile(db));
  // vertex_manufacturing
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_manufacturing" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "name" VARCHAR(1024), "display_name" VARCHAR(1024), "description" VARCHAR(4096), "category" VARCHAR(256), "code" VARCHAR(512), "quantity" BIGINT, "unit" VARCHAR(64), "status" VARCHAR(64), "props" TEXT);`.compile(db));
  // vertex_finance
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_finance" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "name" VARCHAR(1024), "display_name" VARCHAR(1024), "description" VARCHAR(4096), "category" VARCHAR(256), "code" VARCHAR(512), "currency" VARCHAR(16), "price" DOUBLE PRECISION, "status" VARCHAR(64), "props" TEXT);`.compile(db));
  // vertex_energy
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_energy" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "name" VARCHAR(1024), "display_name" VARCHAR(1024), "description" VARCHAR(4096), "category" VARCHAR(256), "capacity" BIGINT, "unit" VARCHAR(64), "lat" DOUBLE PRECISION, "lng" DOUBLE PRECISION, "props" TEXT);`.compile(db));
  // vertex_ip_rights
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_ip_rights" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "name" VARCHAR(1024), "display_name" VARCHAR(1024), "description" VARCHAR(4096), "category" VARCHAR(256), "code" VARCHAR(512), "effective_date" VARCHAR(64), "jurisdiction" VARCHAR(512), "status" VARCHAR(64), "url" VARCHAR(2048), "props" TEXT);`.compile(db));
  // vertex_space
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_space" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "name" VARCHAR(1024), "display_name" VARCHAR(1024), "description" VARCHAR(4096), "category" VARCHAR(256), "props" TEXT);`.compile(db));
  // vertex_legal
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_legal" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "name" VARCHAR(1024), "display_name" VARCHAR(1024), "description" VARCHAR(4096), "category" VARCHAR(256), "code" VARCHAR(512), "jurisdiction" VARCHAR(512), "effective_date" VARCHAR(64), "status" VARCHAR(64), "url" VARCHAR(2048), "props" TEXT);`.compile(db));
  // vertex_wellbeing
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_wellbeing" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "name" VARCHAR(1024), "display_name" VARCHAR(1024), "description" VARCHAR(4096), "category" VARCHAR(256), "level" BIGINT, "status" VARCHAR(64), "props" TEXT);`.compile(db));
  // vertex_agriculture
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_agriculture" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "name" VARCHAR(1024), "display_name" VARCHAR(1024), "description" VARCHAR(4096), "category" VARCHAR(256), "lat" DOUBLE PRECISION, "lng" DOUBLE PRECISION, "quantity" BIGINT, "unit" VARCHAR(64), "props" TEXT);`.compile(db));
  // vertex_education
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_education" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "name" VARCHAR(1024), "display_name" VARCHAR(1024), "description" VARCHAR(4096), "category" VARCHAR(256), "code" VARCHAR(512), "level" BIGINT, "status" VARCHAR(64), "props" TEXT);`.compile(db));
  // vertex_transaction
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_transaction" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "name" VARCHAR(1024), "display_name" VARCHAR(1024), "description" VARCHAR(4096), "category" VARCHAR(256), "code" VARCHAR(512), "currency" VARCHAR(16), "price" DOUBLE PRECISION, "quantity" BIGINT, "status" VARCHAR(64), "props" TEXT);`.compile(db));
  // vertex_spatial
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_spatial" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "name" VARCHAR(1024), "display_name" VARCHAR(1024), "description" VARCHAR(4096), "category" VARCHAR(256), "lat" DOUBLE PRECISION, "lng" DOUBLE PRECISION, "geohash" VARCHAR(32), "status" VARCHAR(64), "source" VARCHAR(256), "source_did" VARCHAR(512), "node_label" VARCHAR(256), "country" VARCHAR(64), "region_id" VARCHAR(256), "zone_type" VARCHAR(128), "admin_level" BIGINT, "props" TEXT);`.compile(db));
  // vertex_identity_doc
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_identity_doc" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "name" VARCHAR(1024), "display_name" VARCHAR(1024), "description" VARCHAR(4096), "category" VARCHAR(256), "code" VARCHAR(512), "jurisdiction" VARCHAR(512), "effective_date" VARCHAR(64), "status" VARCHAR(64), "props" TEXT);`.compile(db));
  // vertex_gambling
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_gambling" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "name" VARCHAR(1024), "display_name" VARCHAR(1024), "description" VARCHAR(4096), "category" VARCHAR(256), "code" VARCHAR(512), "lat" DOUBLE PRECISION, "lng" DOUBLE PRECISION, "props" TEXT);`.compile(db));
  // vertex_network
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_network" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "name" VARCHAR(1024), "display_name" VARCHAR(1024), "description" VARCHAR(4096), "category" VARCHAR(256), "code" VARCHAR(512), "props" TEXT);`.compile(db));
  // vertex_security
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_security" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "name" VARCHAR(1024), "display_name" VARCHAR(1024), "description" VARCHAR(4096), "category" VARCHAR(256), "severity" VARCHAR(64), "code" VARCHAR(512), "source" VARCHAR(256), "props" TEXT);`.compile(db));
  // vertex_commerce
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_commerce" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "name" VARCHAR(1024), "display_name" VARCHAR(1024), "description" VARCHAR(4096), "category" VARCHAR(256), "price" DOUBLE PRECISION, "currency" VARCHAR(16), "quantity" BIGINT, "props" TEXT, "embedding" REAL[], "embedding_norm" DOUBLE PRECISION, "ivf_cluster_id" BIGINT);`.compile(db));
  // vertex_media
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_media" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "name" VARCHAR(1024), "display_name" VARCHAR(1024), "description" VARCHAR(4096), "category" VARCHAR(256), "url" VARCHAR(2048), "language" VARCHAR(64), "props" TEXT);`.compile(db));
  // vertex_civic
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_civic" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "name" VARCHAR(1024), "display_name" VARCHAR(1024), "description" VARCHAR(4096), "category" VARCHAR(256), "severity" VARCHAR(64), "lat" DOUBLE PRECISION, "lng" DOUBLE PRECISION, "props" TEXT);`.compile(db));
  // vertex_logistics
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_logistics" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "name" VARCHAR(1024), "display_name" VARCHAR(1024), "description" VARCHAR(4096), "category" VARCHAR(256), "code" VARCHAR(512), "serial_number" VARCHAR(1024), "status" VARCHAR(64), "props" TEXT);`.compile(db));
  // vertex_bioscience
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_bioscience" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "name" VARCHAR(1024), "display_name" VARCHAR(1024), "description" VARCHAR(4096), "category" VARCHAR(256), "code" VARCHAR(512), "props" TEXT);`.compile(db));
  // vertex_identifier
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_identifier" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "name" VARCHAR(1024), "display_name" VARCHAR(1024), "description" VARCHAR(4096), "category" VARCHAR(256), "code" VARCHAR(512), "props" TEXT);`.compile(db));
  // vertex_gtin_product
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_gtin_product" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "product_id" VARCHAR(512), "did" VARCHAR(512), "name" VARCHAR(1024), "brand" VARCHAR(512), "model" VARCHAR(512), "gtin" VARCHAR(32), "jan" VARCHAR(32), "upc" VARCHAR(32), "ean" VARCHAR(32), "pack_size" VARCHAR(256), "category" VARCHAR(256), "status" VARCHAR(64), "repo" VARCHAR(512), "collection" VARCHAR(512), "updated_at" VARCHAR(64));`.compile(db));
  // vertex_kakaku_merchant
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_kakaku_merchant" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "merchant_id" VARCHAR(512), "did" VARCHAR(512), "name" VARCHAR(1024), "domain" VARCHAR(512), "base_currency" VARCHAR(32), "shipping_policy" VARCHAR(2048), "reputation_score" DOUBLE PRECISION, "selector_profile" VARCHAR(256), "selector_version" BIGINT, "selector_config" TEXT, "selector_rollout" DOUBLE PRECISION, "active_revision_id" VARCHAR(512), "status" VARCHAR(64), "repo" VARCHAR(512), "collection" VARCHAR(512), "created_at" VARCHAR(64), "updated_at" VARCHAR(64));`.compile(db));
  // vertex_kakaku_product
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_kakaku_product" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "product_id" VARCHAR(512), "did" VARCHAR(512), "name" VARCHAR(1024), "brand" VARCHAR(512), "model" VARCHAR(512), "jan" VARCHAR(32), "gtin" VARCHAR(32), "mpn" VARCHAR(256), "pack_size" VARCHAR(256), "category" VARCHAR(256), "global_product_id" VARCHAR(512), "global_product_did" VARCHAR(512), "canonical_gtin14" VARCHAR(32), "status" VARCHAR(64), "repo" VARCHAR(512), "collection" VARCHAR(512), "created_at" VARCHAR(64), "updated_at" VARCHAR(64));`.compile(db));
  // vertex_kakaku_offer
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_kakaku_offer" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "offer_id" VARCHAR(512), "did" VARCHAR(512), "product_id" VARCHAR(512), "product_did" VARCHAR(512), "merchant_id" VARCHAR(512), "merchant_did" VARCHAR(512), "merchant_sku" VARCHAR(512), "native_offer_id" VARCHAR(512), "price" DOUBLE PRECISION, "shipping_fee" DOUBLE PRECISION, "total_price" DOUBLE PRECISION, "currency" VARCHAR(32), "availability" VARCHAR(64), "delivery_eta" VARCHAR(256), "product_url" VARCHAR(2048), "observed_at" VARCHAR(64), "extraction_method" VARCHAR(128), "status" VARCHAR(64), "repo" VARCHAR(512), "collection" VARCHAR(512), "updated_at" VARCHAR(64));`.compile(db));
  // vertex_kakaku_price_history
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_kakaku_price_history" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "history_id" VARCHAR(512), "did" VARCHAR(512), "product_id" VARCHAR(512), "merchant_id" VARCHAR(512), "offer_id" VARCHAR(512), "price" DOUBLE PRECISION, "shipping_fee" DOUBLE PRECISION, "total_price" DOUBLE PRECISION, "currency" VARCHAR(32), "availability" VARCHAR(64), "source_url" VARCHAR(2048), "observed_at" VARCHAR(64), "status" VARCHAR(64), "repo" VARCHAR(512), "collection" VARCHAR(512), "created_at" VARCHAR(64));`.compile(db));
  // vertex_kakaku_match_candidate
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_kakaku_match_candidate" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "candidate_id" VARCHAR(512), "did" VARCHAR(512), "source_merchant_id" VARCHAR(512), "source_sku" VARCHAR(512), "source_url" VARCHAR(2048), "product_id" VARCHAR(512), "product_did" VARCHAR(512), "confidence" DOUBLE PRECISION, "reason" VARCHAR(2048), "status" VARCHAR(64), "repo" VARCHAR(512), "collection" VARCHAR(512), "created_at" VARCHAR(64));`.compile(db));
  // vertex_kakaku_selector_revision
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_kakaku_selector_revision" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "revision_id" VARCHAR(512), "did" VARCHAR(512), "merchant_id" VARCHAR(512), "selector_profile" VARCHAR(256), "selector_version" BIGINT, "selector_config" TEXT, "rollout" DOUBLE PRECISION, "is_active" VARCHAR(512), "reason" VARCHAR(2048), "status" VARCHAR(64), "repo" VARCHAR(512), "collection" VARCHAR(512), "created_at" VARCHAR(64));`.compile(db));
  // vertex_bpmn_process
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_bpmn_process" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "did" VARCHAR(512), "process_key" VARCHAR(512), "name" VARCHAR(1024), "version_tag" VARCHAR(64), "version" BIGINT, "is_executable" VARCHAR(512), "is_subprocess" VARCHAR(512), "candidate_starter_groups" VARCHAR(4096), "candidate_starter_users" VARCHAR(4096), "bpmn_xml" TEXT, "lane_json" TEXT, "execution_tier" VARCHAR(8), "status" VARCHAR(64));`.compile(db));
  // vertex_bpmn_element
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_bpmn_element" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "did" VARCHAR(512), "element_id" VARCHAR(512), "name" VARCHAR(1024), "element_type" VARCHAR(128), "process_did" VARCHAR(512), "mcp_primitive" VARCHAR(128), "camunda_type" VARCHAR(256), "camunda_expression" VARCHAR(4096), "camunda_form_ref" VARCHAR(512), "camunda_form_key" VARCHAR(512), "camunda_decision_ref" VARCHAR(512), "camunda_result_variable" VARCHAR(256), "script_format" VARCHAR(64), "script_body" TEXT, "event_type" VARCHAR(128), "timer_definition" VARCHAR(512), "timer_type" VARCHAR(32), "signal_ref" VARCHAR(512), "message_ref" VARCHAR(512), "error_ref" VARCHAR(512), "is_interrupting" VARCHAR(512), "attached_to_ref" VARCHAR(512), "multi_instance_type" VARCHAR(32), "mi_collection" VARCHAR(512), "mi_element_variable" VARCHAR(256), "mi_completion_condition" VARCHAR(4096), "loop_condition" VARCHAR(4096), "loop_maximum" BIGINT, "async_before" VARCHAR(512), "async_after" VARCHAR(512), "retry_cycle" VARCHAR(256), "extensions_json" TEXT, "listeners_json" TEXT, "io_mapping_json" TEXT, "status" VARCHAR(64));`.compile(db));
  // vertex_bpmn_flow
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_bpmn_flow" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "did" VARCHAR(512), "flow_id" VARCHAR(512), "process_id" VARCHAR(512), "source_element_id" VARCHAR(512), "target_element_id" VARCHAR(512), "flow_name" VARCHAR(512), "condition_expression" VARCHAR(4096), "created_at" VARCHAR(64));`.compile(db));
  // vertex_bpmn_instance
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_bpmn_instance" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "did" VARCHAR(512), "process_did" VARCHAR(512), "instance_key" VARCHAR(512), "instance_state" VARCHAR(32), "active_elements_json" TEXT, "variables_json" TEXT, "parent_instance_did" VARCHAR(512), "parent_element_id" VARCHAR(512), "initiator_did" VARCHAR(512), "start_time_ms" BIGINT, "end_time_ms" BIGINT, "incident_type" VARCHAR(128), "incident_message" VARCHAR(4096), "incident_element_id" VARCHAR(512));`.compile(db));
  // vertex_form_task
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_form_task" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "did" VARCHAR(512), "form_key" VARCHAR(512), "name" VARCHAR(1024), "display_name" VARCHAR(1024), "description" VARCHAR(4096), "form_type" VARCHAR(64), "schema_version" BIGINT, "components_json" TEXT, "variable_mappings_json" TEXT, "status" VARCHAR(64));`.compile(db));
  // vertex_consent
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_consent" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "did" VARCHAR(512), "name" VARCHAR(1024), "purpose" VARCHAR(256), "status" VARCHAR(64), "grantor_did" VARCHAR(512), "grantee_did" VARCHAR(512), "resource_pattern" VARCHAR(512), "max_sensitivity" BIGINT, "delegatable" VARCHAR(512), "expires_at" BIGINT, "revoked" VARCHAR(512), "props" TEXT);`.compile(db));
  // vertex_raci
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_raci" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "did" VARCHAR(512), "activity" VARCHAR(512), "raci_type" VARCHAR(1), "target_did" VARCHAR(512), "status" VARCHAR(64), "props" TEXT);`.compile(db));
  // vertex_dmn_model
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_dmn_model" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "did" VARCHAR(512), "decision_key" VARCHAR(512), "name" VARCHAR(1024), "description" VARCHAR(4096), "version" BIGINT, "decision_type" VARCHAR(64), "hit_policy" VARCHAR(32), "aggregation" VARCHAR(16), "inputs_json" TEXT, "outputs_json" TEXT, "rules_json" TEXT, "expression_text" TEXT, "expression_language" VARCHAR(64), "required_decisions_json" TEXT, "dmn_xml" TEXT, "status" VARCHAR(64));`.compile(db));
  // vertex_repo_head
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_repo_head" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "did" VARCHAR(512), "status" VARCHAR(64), "props" TEXT);`.compile(db));
  // vertex_policy
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_policy" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "did" VARCHAR(512), "name" VARCHAR(1024), "display_name" VARCHAR(1024), "description" VARCHAR(4096), "status" VARCHAR(64), "props" TEXT);`.compile(db));
  // vertex_signal_device
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_signal_device" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "did" VARCHAR(512), "display_name" VARCHAR(1024), "description" VARCHAR(4096), "status" VARCHAR(64), "props" TEXT);`.compile(db));
  // vertex_ocel_event
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_ocel_event" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "did" VARCHAR(512), "collection" VARCHAR(512), "text" VARCHAR(8192), "status" VARCHAR(64), "props" TEXT);`.compile(db));
  // vertex_w_envelope
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_w_envelope" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "did" VARCHAR(512), "text" VARCHAR(8192), "status" VARCHAR(64), "props" TEXT);`.compile(db));
  // vertex_social_action
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_social_action" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "collection" VARCHAR(512), "dst_vid" VARCHAR(512), "subject_uri" VARCHAR(1024), "subject_cid" VARCHAR(512), "created_at" VARCHAR(64));`.compile(db));
  // vertex_convo_member
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_convo_member" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "convo_id" VARCHAR(512), "text" VARCHAR(8192), "status" VARCHAR(64));`.compile(db));
  // vertex_message_props
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_message_props" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "convo_id" VARCHAR(512), "text" VARCHAR(8192), "props" TEXT);`.compile(db));
  // vertex_profile_fragment
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_profile_fragment" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "text" VARCHAR(8192), "props" TEXT);`.compile(db));
  // vertex_project_props
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_project_props" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "convo_id" VARCHAR(512), "name" VARCHAR(1024), "parent_id" VARCHAR(512), "status" VARCHAR(64), "assignee" VARCHAR(512), "props" TEXT);`.compile(db));
  // vertex_atproto_action
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_atproto_action" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "props" TEXT);`.compile(db));
  // vertex_label
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_label" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "collection" VARCHAR(512), "text" VARCHAR(8192), "props" TEXT);`.compile(db));
  // vertex_prekeys
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_prekeys" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "did" VARCHAR(512), "props" TEXT);`.compile(db));
  // vertex_push_subscription
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_push_subscription" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "did" VARCHAR(512), "props" TEXT);`.compile(db));
  // vertex_editor_project
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_editor_project" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "project_id" VARCHAR(128), "name" VARCHAR(200), "template" VARCHAR(64), "created_at" VARCHAR(64), "org_id" VARCHAR(128), "user_id" VARCHAR(512), "actor_id" VARCHAR(128));`.compile(db));
  // vertex_editor_file
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_editor_file" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "project_id" VARCHAR(128), "path" VARCHAR(1024), "blob_ref" VARCHAR(256), "sha256" VARCHAR(64), "size_bytes" BIGINT, "mime_type" VARCHAR(128), "updated_at" VARCHAR(64), "org_id" VARCHAR(128), "user_id" VARCHAR(512), "actor_id" VARCHAR(128));`.compile(db));
  // vertex_blockchain_actor
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_blockchain_actor" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "chain" VARCHAR(32), "address" VARCHAR(128), "name" VARCHAR(512), "balance" BIGINT, "total_received" BIGINT, "total_sent" BIGINT, "tx_count" BIGINT, "unconfirmed_tx_count" BIGINT, "risk_score" DOUBLE PRECISION, "source" VARCHAR(256), "observed_at" VARCHAR(64), "props" TEXT);`.compile(db));
  // vertex_dns_observation
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_dns_observation" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "domain" VARCHAR(512), "handle" VARCHAR(256), "registrar" VARCHAR(512), "registrar_handle" VARCHAR(256), "registrar_iana_id" VARCHAR(64), "nameservers" VARCHAR(2048), "registration_date" VARCHAR(64), "expiration_date" VARCHAR(64), "last_changed_date" VARCHAR(64), "dnssec" VARCHAR(512), "status" VARCHAR(512), "run_id" VARCHAR(64), "observed_at" VARCHAR(64), "props" TEXT);`.compile(db));
  // vertex_risk_signal
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_risk_signal" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "target_node_id" VARCHAR(512), "chain" VARCHAR(32), "address" VARCHAR(128), "signal_type" VARCHAR(128), "value" DOUBLE PRECISION, "currency" VARCHAR(32), "confidence" DOUBLE PRECISION, "detected_at" VARCHAR(64), "props" TEXT);`.compile(db));
  // vertex_collector_run
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_collector_run" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "run_id" VARCHAR(64), "collector" VARCHAR(128), "target" VARCHAR(512), "status" VARCHAR(64), "started_at" VARCHAR(64), "finished_at" VARCHAR(64), "props" TEXT);`.compile(db));
  // vertex_yabai_flag
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_yabai_flag" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "account_did" VARCHAR(512), "entity_vid" VARCHAR(512), "entity_type" VARCHAR(128), "flag_type" VARCHAR(128), "severity" VARCHAR(64), "confidence" DOUBLE PRECISION, "tlp" VARCHAR(32), "notes" VARCHAR(4096), "tags" VARCHAR(1024), "expires_at" VARCHAR(64), "props" TEXT);`.compile(db));
  // vertex_scan_result
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_scan_result" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "ip" VARCHAR(64), "port" BIGINT, "protocol" VARCHAR(32), "state" VARCHAR(32), "service" VARCHAR(128), "software" VARCHAR(256), "version" VARCHAR(128), "banner" VARCHAR(512), "tls_version" VARCHAR(32), "tls_cipher" VARCHAR(128), "cert_subject" VARCHAR(512), "cert_issuer" VARCHAR(256), "cert_expires" VARCHAR(64), "os_guess" VARCHAR(128), "scanner_host" VARCHAR(128), "scanned_at" VARCHAR(64), "props" TEXT);`.compile(db));
  // vertex_isekai_world_state
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_isekai_world_state" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "world_id" VARCHAR(128), "seed" BIGINT, "time_of_day" DOUBLE PRECISION, "day_count" BIGINT, "active_biome" VARCHAR(64), "player_count" BIGINT, "props" TEXT);`.compile(db));
  // vertex_isekai_chunk_data
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_isekai_chunk_data" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "world_id" VARCHAR(128), "chunk_x" BIGINT, "chunk_z" BIGINT, "edit_type" VARCHAR(32), "block_type" VARCHAR(64), "x" BIGINT, "y" BIGINT, "z" BIGINT, "props" TEXT);`.compile(db));
  // vertex_isekai_creature_roster
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_isekai_creature_roster" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "instance_id" VARCHAR(128), "species_id" BIGINT, "level" BIGINT, "hp" BIGINT, "max_hp" BIGINT, "friendship" BIGINT, "xp" BIGINT, "caught_biome" VARCHAR(64), "caught_at" VARCHAR(64), "action" VARCHAR(32), "nickname" VARCHAR(128), "moves_json" TEXT, "props" TEXT);`.compile(db));
  // vertex_isekai_inventory_item
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_isekai_inventory_item" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "item_id" VARCHAR(128), "name" VARCHAR(256), "category" VARCHAR(64), "quantity" BIGINT, "props" TEXT);`.compile(db));
  // vertex_isekai_brainrot_event
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_isekai_brainrot_event" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "event_id" VARCHAR(128), "npc" VARCHAR(64), "trigger" VARCHAR(64), "is_boss" VARCHAR(512), "shard_count" BIGINT, "type" VARCHAR(64), "reward_json" TEXT, "dialogue_json" TEXT, "props" TEXT);`.compile(db));
  // vertex_isekai_compliance_dep
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_isekai_compliance_dep" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "compliance_id" VARCHAR(128), "type" VARCHAR(64), "title" VARCHAR(512), "risk" VARCHAR(32), "status" VARCHAR(64), "mitigation" TEXT, "props" TEXT);`.compile(db));
  // vertex_isekai_game_capture
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_isekai_game_capture" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "species_id" BIGINT, "level" BIGINT, "ball_type" VARCHAR(64), "biome" VARCHAR(64), "props" TEXT);`.compile(db));
  // vertex_isekai_game_craft
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_isekai_game_craft" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "recipe_id" VARCHAR(128), "quantity" BIGINT, "props" TEXT);`.compile(db));
  // vertex_isekai_game_brainrot_encounter
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_isekai_game_brainrot_encounter" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "npc" VARCHAR(64), "is_boss" VARCHAR(512), "props" TEXT);`.compile(db));
  // vertex_business_person
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_business_person" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "person_id" VARCHAR(256), "display_name" VARCHAR(1024), "description" VARCHAR(4096), "title" VARCHAR(512), "name" VARCHAR(1024), "name_en" VARCHAR(1024), "name_ja" VARCHAR(1024), "code" VARCHAR(256), "level" VARCHAR(64), "org_name" VARCHAR(1024), "registry_id" VARCHAR(256), "registry_type" VARCHAR(128), "country" VARCHAR(8), "source" VARCHAR(256), "source_url" VARCHAR(2048), "url" VARCHAR(2048), "change_type" VARCHAR(128), "from_title" VARCHAR(512), "to_title" VARCHAR(512), "effective_date" VARCHAR(64), "since" VARCHAR(64), "until" VARCHAR(64), "filing_types" VARCHAR(512), "status" VARCHAR(64), "props" TEXT);`.compile(db));
  // vertex_natural_person
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_natural_person" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256), "did" VARCHAR(512), "cohort_hash" VARCHAR(64), "person_hash" VARCHAR(64), "name" VARCHAR(1024), "country" VARCHAR(8), "region" VARCHAR(256), "gender" VARCHAR(32), "vital_status" VARCHAR(32), "era" VARCHAR(32), "birth_year" BIGINT, "death_year" BIGINT, "death_cause_icd10" VARCHAR(32), "health_icd10" VARCHAR(256), "data_classification" VARCHAR(32), "role" VARCHAR(256), "organization" VARCHAR(1024), "source_app" VARCHAR(128), "source_record_id" VARCHAR(256), "enrichment_status" VARCHAR(32), "confidence" DOUBLE PRECISION, "source_url" VARCHAR(2048), "intel_chain_id" VARCHAR(128), "intel_estimated_count" DOUBLE PRECISION, "intel_confidence" DOUBLE PRECISION, "status" VARCHAR(64), "props" TEXT);`.compile(db));
  // vertex_mangaka
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_mangaka" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "did" VARCHAR(512), "collection" VARCHAR(512), "label" VARCHAR(256), "title" VARCHAR(512), "name" VARCHAR(512), "display_name" VARCHAR(512), "description" TEXT, "parent_rkey" VARCHAR(64), "page_number" BIGINT, "panel_number" BIGINT, "asset_type" VARCHAR(128), "mime_type" VARCHAR(128), "cid" VARCHAR(512), "status" VARCHAR(64), "created_at" VARCHAR(64), "props" TEXT);`.compile(db));
  // vertex_i18n
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_i18n" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "did" VARCHAR(512), "collection" VARCHAR(512), "label" VARCHAR(256), "source_lang" VARCHAR(16), "target_lang" VARCHAR(16), "source_text" TEXT, "target_text" TEXT, "project_id" VARCHAR(128), "node_type" VARCHAR(128), "edge_type" VARCHAR(128), "status" VARCHAR(64), "created_at" VARCHAR(64), "props" TEXT);`.compile(db));
  // vertex_media_content
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_media_content" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "did" VARCHAR(512), "collection" VARCHAR(512), "label" VARCHAR(256), "title" VARCHAR(512), "name" VARCHAR(512), "display_name" VARCHAR(512), "description" TEXT, "code" VARCHAR(256), "category" VARCHAR(256), "platform" VARCHAR(256), "region" VARCHAR(128), "publisher" VARCHAR(512), "developer" VARCHAR(512), "release_date" VARCHAR(64), "url" VARCHAR(1024), "source_url" VARCHAR(1024), "mime_type" VARCHAR(128), "cid" VARCHAR(512), "status" VARCHAR(64), "created_at" VARCHAR(64), "props" TEXT);`.compile(db));
  // vertex_scheduling
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_scheduling" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "did" VARCHAR(512), "collection" VARCHAR(512), "label" VARCHAR(256), "title" VARCHAR(512), "start_at" VARCHAR(64), "end_at" VARCHAR(64), "location" VARCHAR(512), "attendees" TEXT, "status" VARCHAR(64), "created_at" VARCHAR(64), "props" TEXT);`.compile(db));
  // vertex_sensor
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_sensor" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "did" VARCHAR(512), "collection" VARCHAR(512), "label" VARCHAR(256), "name" VARCHAR(512), "floor_number" BIGINT, "building_id" VARCHAR(256), "sensor_type" VARCHAR(128), "value" DOUBLE PRECISION, "unit" VARCHAR(64), "lat" DOUBLE PRECISION, "lng" DOUBLE PRECISION, "status" VARCHAR(64), "scanned_at" VARCHAR(64), "props" TEXT);`.compile(db));
  // vertex_joucho
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_joucho" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "did" VARCHAR(512), "collection" VARCHAR(512), "label" VARCHAR(256), "actorDid" VARCHAR(512), "actorName" VARCHAR(512), "joy" BIGINT, "calm" BIGINT, "stress" BIGINT, "gratitude" BIGINT, "focus" BIGINT, "mood" VARCHAR(64), "score" DOUBLE PRECISION, "status" VARCHAR(64), "created_at" VARCHAR(64), "props" TEXT);`.compile(db));
  // vertex_crawl_job
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_crawl_job" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "did" VARCHAR(512), "collection" VARCHAR(512), "label" VARCHAR(256), "sourceUrl" VARCHAR(1024), "format" VARCHAR(128), "jobId" VARCHAR(256), "appNsPrefix" VARCHAR(512), "recordsCreated" BIGINT, "error" TEXT, "lat" DOUBLE PRECISION, "lng" DOUBLE PRECISION, "status" VARCHAR(64), "created_at" VARCHAR(64), "completedAt" VARCHAR(64), "props" TEXT);`.compile(db));
  // vertex_gov_municipality
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_gov_municipality" ("vertex_id" VARCHAR(512) PRIMARY KEY, "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "did" VARCHAR(512), "collection" VARCHAR(512), "label" VARCHAR(256), "actorDid" VARCHAR(512), "municipality_code" VARCHAR(64), "prefecture" VARCHAR(128), "city" VARCHAR(256), "coverage_pct" DOUBLE PRECISION, "site_url" VARCHAR(1024), "status" VARCHAR(64), "created_at" VARCHAR(64), "props" TEXT);`.compile(db));
  // edge_follows
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_follows" ("edge_id" VARCHAR(512) PRIMARY KEY, "src_vid" VARCHAR(512), "dst_vid" VARCHAR(512), "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "created_at" VARCHAR(64));`.compile(db));
  // edge_follows_by_dest
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_follows_by_dest" ("edge_id" VARCHAR(512) PRIMARY KEY, "src_vid" VARCHAR(512), "dst_vid" VARCHAR(512), "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "created_at" VARCHAR(64));`.compile(db));
  // edge_likes
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_likes" ("edge_id" VARCHAR(512) PRIMARY KEY, "src_vid" VARCHAR(512), "dst_vid" VARCHAR(512), "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "subject_uri" VARCHAR(1024), "subject_cid" VARCHAR(512));`.compile(db));
  // edge_likes_by_dest
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_likes_by_dest" ("edge_id" VARCHAR(512) PRIMARY KEY, "src_vid" VARCHAR(512), "dst_vid" VARCHAR(512), "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "subject_uri" VARCHAR(1024), "subject_cid" VARCHAR(512));`.compile(db));
  // edge_reposts
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_reposts" ("edge_id" VARCHAR(512) PRIMARY KEY, "src_vid" VARCHAR(512), "dst_vid" VARCHAR(512), "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "subject_uri" VARCHAR(1024), "subject_cid" VARCHAR(512));`.compile(db));
  // edge_reposts_by_dest
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_reposts_by_dest" ("edge_id" VARCHAR(512) PRIMARY KEY, "src_vid" VARCHAR(512), "dst_vid" VARCHAR(512), "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "subject_uri" VARCHAR(1024), "subject_cid" VARCHAR(512));`.compile(db));
  // edge_blocks
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_blocks" ("edge_id" VARCHAR(512) PRIMARY KEY, "src_vid" VARCHAR(512), "dst_vid" VARCHAR(512), "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "label" VARCHAR(256));`.compile(db));
  // edge_has_author
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_has_author" ("edge_id" VARCHAR(512) PRIMARY KEY, "src_vid" VARCHAR(512), "dst_vid" VARCHAR(512), "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512));`.compile(db));
  // edge_has_author_by_dest
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_has_author_by_dest" ("edge_id" VARCHAR(512) PRIMARY KEY, "src_vid" VARCHAR(512), "dst_vid" VARCHAR(512), "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512));`.compile(db));
  // edge_reply
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_reply" ("edge_id" VARCHAR(512) PRIMARY KEY, "src_vid" VARCHAR(512), "dst_vid" VARCHAR(512), "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512));`.compile(db));
  // edge_reply_by_dest
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_reply_by_dest" ("edge_id" VARCHAR(512) PRIMARY KEY, "src_vid" VARCHAR(512), "dst_vid" VARCHAR(512), "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512));`.compile(db));
  // edge_hosts_page
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_hosts_page" ("edge_id" VARCHAR(512) PRIMARY KEY, "src_vid" VARCHAR(512), "dst_vid" VARCHAR(512), "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "label" VARCHAR(256));`.compile(db));
  // edge_links_to
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_links_to" ("edge_id" VARCHAR(512) PRIMARY KEY, "src_vid" VARCHAR(512), "dst_vid" VARCHAR(512), "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "label" VARCHAR(256), "anchor_text" VARCHAR(1024));`.compile(db));
  // edge_links_to_by_dest
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_links_to_by_dest" ("edge_id" VARCHAR(512) PRIMARY KEY, "src_vid" VARCHAR(512), "dst_vid" VARCHAR(512), "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "label" VARCHAR(256));`.compile(db));
  // edge_links_to_domain
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_links_to_domain" ("edge_id" VARCHAR(512) PRIMARY KEY, "src_vid" VARCHAR(512), "dst_vid" VARCHAR(512), "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "label" VARCHAR(256), "count" BIGINT);`.compile(db));
  // edge_chunk_of
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_chunk_of" ("edge_id" VARCHAR(512) PRIMARY KEY, "src_vid" VARCHAR(512), "dst_vid" VARCHAR(512), "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "label" VARCHAR(256), "chunk_index" BIGINT);`.compile(db));
  // edge_in_app
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_in_app" ("edge_id" VARCHAR(512) PRIMARY KEY, "src_vid" VARCHAR(512), "dst_vid" VARCHAR(512), "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "src_label" VARCHAR(256), "dst_label" VARCHAR(256));`.compile(db));
  // edge_in_project
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_in_project" ("edge_id" VARCHAR(512) PRIMARY KEY, "src_vid" VARCHAR(512), "dst_vid" VARCHAR(512), "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512));`.compile(db));
  // edge_membership
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_membership" ("edge_id" VARCHAR(512) PRIMARY KEY, "src_vid" VARCHAR(512), "dst_vid" VARCHAR(512), "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "role" VARCHAR(256));`.compile(db));
  // edge_membership_by_dest
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_membership_by_dest" ("edge_id" VARCHAR(512) PRIMARY KEY, "src_vid" VARCHAR(512), "dst_vid" VARCHAR(512), "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "role" VARCHAR(256));`.compile(db));
  // edge_list_item
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_list_item" ("edge_id" VARCHAR(512) PRIMARY KEY, "src_vid" VARCHAR(512), "dst_vid" VARCHAR(512), "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512));`.compile(db));
  // edge_list_item_by_dest
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_list_item_by_dest" ("edge_id" VARCHAR(512) PRIMARY KEY, "src_vid" VARCHAR(512), "dst_vid" VARCHAR(512), "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512));`.compile(db));
  // edge_enacts
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_enacts" ("edge_id" VARCHAR(512) PRIMARY KEY, "src_vid" VARCHAR(512), "dst_vid" VARCHAR(512), "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "label" VARCHAR(256), "effective_date" VARCHAR(64), "jurisdiction" VARCHAR(512));`.compile(db));
  // edge_supersedes
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_supersedes" ("edge_id" VARCHAR(512) PRIMARY KEY, "src_vid" VARCHAR(512), "dst_vid" VARCHAR(512), "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "label" VARCHAR(256), "effective_date" VARCHAR(64));`.compile(db));
  // edge_interprets
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_interprets" ("edge_id" VARCHAR(512) PRIMARY KEY, "src_vid" VARCHAR(512), "dst_vid" VARCHAR(512), "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "label" VARCHAR(256), "authority_kind" VARCHAR(128));`.compile(db));
  // edge_enforces
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_enforces" ("edge_id" VARCHAR(512) PRIMARY KEY, "src_vid" VARCHAR(512), "dst_vid" VARCHAR(512), "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "label" VARCHAR(256), "authority_kind" VARCHAR(128), "status" VARCHAR(64));`.compile(db));
  // edge_crafts
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_crafts" ("edge_id" VARCHAR(512) PRIMARY KEY, "src_vid" VARCHAR(512), "dst_vid" VARCHAR(512), "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "label" VARCHAR(256), "quantity" BIGINT);`.compile(db));
  // edge_owns
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_owns" ("edge_id" VARCHAR(512) PRIMARY KEY, "src_vid" VARCHAR(512), "dst_vid" VARCHAR(512), "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "label" VARCHAR(256), "quantity" BIGINT);`.compile(db));
  // edge_requires
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_requires" ("edge_id" VARCHAR(512) PRIMARY KEY, "src_vid" VARCHAR(512), "dst_vid" VARCHAR(512), "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "label" VARCHAR(256), "quantity" BIGINT, "role" VARCHAR(256));`.compile(db));
  // edge_rewards
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_rewards" ("edge_id" VARCHAR(512) PRIMARY KEY, "src_vid" VARCHAR(512), "dst_vid" VARCHAR(512), "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "label" VARCHAR(256), "quantity" BIGINT);`.compile(db));
  // edge_contains
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_contains" ("edge_id" VARCHAR(512) PRIMARY KEY, "src_vid" VARCHAR(512), "dst_vid" VARCHAR(512), "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "label" VARCHAR(256), "quantity" BIGINT);`.compile(db));
  // edge_contains_by_dest
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_contains_by_dest" ("edge_id" VARCHAR(512) PRIMARY KEY, "src_vid" VARCHAR(512), "dst_vid" VARCHAR(512), "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "label" VARCHAR(256), "quantity" BIGINT);`.compile(db));
  // edge_produces
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_produces" ("edge_id" VARCHAR(512) PRIMARY KEY, "src_vid" VARCHAR(512), "dst_vid" VARCHAR(512), "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "label" VARCHAR(256), "quantity" BIGINT, "unit" VARCHAR(64));`.compile(db));
  // edge_located_at
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_located_at" ("edge_id" VARCHAR(512) PRIMARY KEY, "src_vid" VARCHAR(512), "dst_vid" VARCHAR(512), "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "label" VARCHAR(256));`.compile(db));
  // edge_transacts
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_transacts" ("edge_id" VARCHAR(512) PRIMARY KEY, "src_vid" VARCHAR(512), "dst_vid" VARCHAR(512), "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "label" VARCHAR(256), "price" DOUBLE PRECISION, "currency" VARCHAR(16), "quantity" BIGINT);`.compile(db));
  // edge_treats
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_treats" ("edge_id" VARCHAR(512) PRIMARY KEY, "src_vid" VARCHAR(512), "dst_vid" VARCHAR(512), "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "label" VARCHAR(256), "code" VARCHAR(512));`.compile(db));
  // edge_targets
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_targets" ("edge_id" VARCHAR(512) PRIMARY KEY, "src_vid" VARCHAR(512), "dst_vid" VARCHAR(512), "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "label" VARCHAR(256), "severity" VARCHAR(64));`.compile(db));
  // edge_connects
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_connects" ("edge_id" VARCHAR(512) PRIMARY KEY, "src_vid" VARCHAR(512), "dst_vid" VARCHAR(512), "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "label" VARCHAR(256));`.compile(db));
  // edge_disposes
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_disposes" ("edge_id" VARCHAR(512) PRIMARY KEY, "src_vid" VARCHAR(512), "dst_vid" VARCHAR(512), "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "label" VARCHAR(256), "quantity" BIGINT, "unit" VARCHAR(64));`.compile(db));
  // edge_governance
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_governance" ("edge_id" VARCHAR(512) PRIMARY KEY, "src_vid" VARCHAR(512), "dst_vid" VARCHAR(512), "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "label" VARCHAR(256));`.compile(db));
  // edge_capability
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_capability" ("edge_id" VARCHAR(512) PRIMARY KEY, "src_vid" VARCHAR(512), "dst_vid" VARCHAR(512), "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "label" VARCHAR(256));`.compile(db));
  // edge_sequence_flow
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_sequence_flow" ("edge_id" VARCHAR(512) PRIMARY KEY, "src_vid" VARCHAR(512), "dst_vid" VARCHAR(512), "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "flow_id" VARCHAR(512), "process_did" VARCHAR(512), "name" VARCHAR(1024), "condition_expression" VARCHAR(4096), "is_default" VARCHAR(512), "source_element_type" VARCHAR(128), "target_element_type" VARCHAR(128));`.compile(db));
  // edge_bpmn_contains
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_bpmn_contains" ("edge_id" VARCHAR(512) PRIMARY KEY, "src_vid" VARCHAR(512), "dst_vid" VARCHAR(512), "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "label" VARCHAR(256), "lane_id" VARCHAR(512), "lane_name" VARCHAR(1024));`.compile(db));
  // edge_bpmn_assigns
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_bpmn_assigns" ("edge_id" VARCHAR(512) PRIMARY KEY, "src_vid" VARCHAR(512), "dst_vid" VARCHAR(512), "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "label" VARCHAR(256), "assignment_type" VARCHAR(64), "raci_type" VARCHAR(1));`.compile(db));
  // edge_bpmn_references
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_bpmn_references" ("edge_id" VARCHAR(512) PRIMARY KEY, "src_vid" VARCHAR(512), "dst_vid" VARCHAR(512), "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "ref_type" VARCHAR(64), "ref_key" VARCHAR(512));`.compile(db));
  // edge_bpmn_instance_of
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_bpmn_instance_of" ("edge_id" VARCHAR(512) PRIMARY KEY, "src_vid" VARCHAR(512), "dst_vid" VARCHAR(512), "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "label" VARCHAR(256), "token_state" VARCHAR(32));`.compile(db));
  // edge_controls_wallet
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_controls_wallet" ("edge_id" VARCHAR(512) PRIMARY KEY, "src_vid" VARCHAR(512), "dst_vid" VARCHAR(512), "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "confidence" DOUBLE PRECISION, "source" VARCHAR(256), "props" TEXT);`.compile(db));
  // edge_emits_risk
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_emits_risk" ("edge_id" VARCHAR(512) PRIMARY KEY, "src_vid" VARCHAR(512), "dst_vid" VARCHAR(512), "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "props" TEXT);`.compile(db));
  // edge_registered_with
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_registered_with" ("edge_id" VARCHAR(512) PRIMARY KEY, "src_vid" VARCHAR(512), "dst_vid" VARCHAR(512), "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "props" TEXT);`.compile(db));
  // edge_wallet_cluster
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_wallet_cluster" ("edge_id" VARCHAR(512) PRIMARY KEY, "src_vid" VARCHAR(512), "dst_vid" VARCHAR(512), "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "method" VARCHAR(64), "confidence" DOUBLE PRECISION, "props" TEXT);`.compile(db));
  // edge_flags
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_flags" ("edge_id" VARCHAR(512) PRIMARY KEY, "src_vid" VARCHAR(512), "dst_vid" VARCHAR(512), "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "rkey" VARCHAR(64), "repo" VARCHAR(512), "flag_type" VARCHAR(128), "severity" VARCHAR(64), "props" TEXT);`.compile(db));
  // edge_cites
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_cites" ("edge_id" VARCHAR(512) PRIMARY KEY, "src_vid" VARCHAR(512), "dst_vid" VARCHAR(512), "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "label" VARCHAR(256), "citation_type" VARCHAR(64), "paragraph" VARCHAR(256), "jurisdiction" VARCHAR(64));`.compile(db));
  // edge_has_judgment
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_has_judgment" ("edge_id" VARCHAR(512) PRIMARY KEY, "src_vid" VARCHAR(512), "dst_vid" VARCHAR(512), "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "label" VARCHAR(256), "court_level" VARCHAR(64), "judgment_date" VARCHAR(64));`.compile(db));
  // edge_filed_at
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_filed_at" ("edge_id" VARCHAR(512) PRIMARY KEY, "src_vid" VARCHAR(512), "dst_vid" VARCHAR(512), "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "label" VARCHAR(256), "filed_date" VARCHAR(64), "jurisdiction" VARCHAR(64));`.compile(db));
  // edge_presides
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_presides" ("edge_id" VARCHAR(512) PRIMARY KEY, "src_vid" VARCHAR(512), "dst_vid" VARCHAR(512), "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "label" VARCHAR(256), "assigned_date" VARCHAR(64), "role" VARCHAR(64));`.compile(db));
  // edge_maps_to_jurisdiction
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_maps_to_jurisdiction" ("edge_id" VARCHAR(512) PRIMARY KEY, "src_vid" VARCHAR(512), "dst_vid" VARCHAR(512), "_seq" BIGINT, "created_date" DATE, "sensitivity_ord" BIGINT, "owner_did" VARCHAR(512), "label" VARCHAR(256), "jurisdiction" VARCHAR(64));`.compile(db));
}

export async function down(db: Kysely<any>): Promise<void> {
  await db.schema.dropTable('vertex_actor').ifExists().execute();
  await db.schema.dropTable('vertex_actor_convo_prompt').ifExists().execute();
  await db.schema.dropTable('vertex_profile').ifExists().execute();
  await db.schema.dropTable('vertex_post').ifExists().execute();
  await db.schema.dropTable('vertex_message').ifExists().execute();
  await db.schema.dropTable('vertex_app').ifExists().execute();
  await db.schema.dropTable('vertex_handle').ifExists().execute();
  await db.schema.dropTable('vertex_list').ifExists().execute();
  await db.schema.dropTable('vertex_convo').ifExists().execute();
  await db.schema.dropTable('vertex_governance').ifExists().execute();
  await db.schema.dropTable('vertex_capability').ifExists().execute();
  await db.schema.dropTable('vertex_actor_manifest').ifExists().execute();
  await db.schema.dropTable('vertex_actor_coverage').ifExists().execute();
  await db.schema.dropTable('vertex_gov_coverage_snapshot').ifExists().execute();
  await db.schema.dropTable('vertex_gov_source').ifExists().execute();
  await db.schema.dropTable('vertex_gov_document').ifExists().execute();
  await db.schema.dropTable('vertex_gov_coverage_gap').ifExists().execute();
  await db.schema.dropTable('vertex_gov_org').ifExists().execute();
  await db.schema.dropTable('vertex_governance_contract').ifExists().execute();
  await db.schema.dropTable('vertex_shinka_evolution').ifExists().execute();
  await db.schema.dropTable('vertex_shinka_knowledge').ifExists().execute();
  await db.schema.dropTable('vertex_page').ifExists().execute();
  await db.schema.dropTable('vertex_wet_chunk').ifExists().execute();
  await db.schema.dropTable('vertex_did').ifExists().execute();
  await db.schema.dropTable('vertex_domain').ifExists().execute();
  await db.schema.dropTable('vertex_collection_job').ifExists().execute();
  await db.schema.dropTable('vertex_frontier').ifExists().execute();
  await db.schema.dropTable('vertex_screenshot').ifExists().execute();
  await db.schema.dropTable('vertex_wat').ifExists().execute();
  await db.schema.dropTable('vertex_ivf_centroid').ifExists().execute();
  await db.schema.dropTable('vertex_article').ifExists().execute();
  await db.schema.dropTable('vertex_authority_sovereign').ifExists().execute();
  await db.schema.dropTable('vertex_authority_treaty').ifExists().execute();
  await db.schema.dropTable('vertex_authority_religious').ifExists().execute();
  await db.schema.dropTable('vertex_authority_customary').ifExists().execute();
  await db.schema.dropTable('vertex_authority_professional').ifExists().execute();
  await db.schema.dropTable('vertex_authority_industry').ifExists().execute();
  await db.schema.dropTable('vertex_authority_blockchain').ifExists().execute();
  await db.schema.dropTable('vertex_authority_community').ifExists().execute();
  await db.schema.dropTable('vertex_game_item').ifExists().execute();
  await db.schema.dropTable('vertex_game_recipe').ifExists().execute();
  await db.schema.dropTable('vertex_game_actor').ifExists().execute();
  await db.schema.dropTable('vertex_game_quest').ifExists().execute();
  await db.schema.dropTable('vertex_transport').ifExists().execute();
  await db.schema.dropTable('vertex_threat').ifExists().execute();
  await db.schema.dropTable('vertex_serial').ifExists().execute();
  await db.schema.dropTable('vertex_medical').ifExists().execute();
  await db.schema.dropTable('vertex_software').ifExists().execute();
  await db.schema.dropTable('vertex_waste').ifExists().execute();
  await db.schema.dropTable('vertex_building').ifExists().execute();
  await db.schema.dropTable('vertex_fiction').ifExists().execute();
  await db.schema.dropTable('vertex_contract').ifExists().execute();
  await db.schema.dropTable('vertex_manufacturing').ifExists().execute();
  await db.schema.dropTable('vertex_finance').ifExists().execute();
  await db.schema.dropTable('vertex_energy').ifExists().execute();
  await db.schema.dropTable('vertex_ip_rights').ifExists().execute();
  await db.schema.dropTable('vertex_space').ifExists().execute();
  await db.schema.dropTable('vertex_legal').ifExists().execute();
  await db.schema.dropTable('vertex_wellbeing').ifExists().execute();
  await db.schema.dropTable('vertex_agriculture').ifExists().execute();
  await db.schema.dropTable('vertex_education').ifExists().execute();
  await db.schema.dropTable('vertex_transaction').ifExists().execute();
  await db.schema.dropTable('vertex_spatial').ifExists().execute();
  await db.schema.dropTable('vertex_identity_doc').ifExists().execute();
  await db.schema.dropTable('vertex_gambling').ifExists().execute();
  await db.schema.dropTable('vertex_network').ifExists().execute();
  await db.schema.dropTable('vertex_security').ifExists().execute();
  await db.schema.dropTable('vertex_commerce').ifExists().execute();
  await db.schema.dropTable('vertex_media').ifExists().execute();
  await db.schema.dropTable('vertex_civic').ifExists().execute();
  await db.schema.dropTable('vertex_logistics').ifExists().execute();
  await db.schema.dropTable('vertex_bioscience').ifExists().execute();
  await db.schema.dropTable('vertex_identifier').ifExists().execute();
  await db.schema.dropTable('vertex_gtin_product').ifExists().execute();
  await db.schema.dropTable('vertex_kakaku_merchant').ifExists().execute();
  await db.schema.dropTable('vertex_kakaku_product').ifExists().execute();
  await db.schema.dropTable('vertex_kakaku_offer').ifExists().execute();
  await db.schema.dropTable('vertex_kakaku_price_history').ifExists().execute();
  await db.schema.dropTable('vertex_kakaku_match_candidate').ifExists().execute();
  await db.schema.dropTable('vertex_kakaku_selector_revision').ifExists().execute();
  await db.schema.dropTable('vertex_bpmn_process').ifExists().execute();
  await db.schema.dropTable('vertex_bpmn_element').ifExists().execute();
  await db.schema.dropTable('vertex_bpmn_flow').ifExists().execute();
  await db.schema.dropTable('vertex_bpmn_instance').ifExists().execute();
  await db.schema.dropTable('vertex_form_task').ifExists().execute();
  await db.schema.dropTable('vertex_consent').ifExists().execute();
  await db.schema.dropTable('vertex_raci').ifExists().execute();
  await db.schema.dropTable('vertex_dmn_model').ifExists().execute();
  await db.schema.dropTable('vertex_repo_head').ifExists().execute();
  await db.schema.dropTable('vertex_policy').ifExists().execute();
  await db.schema.dropTable('vertex_signal_device').ifExists().execute();
  await db.schema.dropTable('vertex_ocel_event').ifExists().execute();
  await db.schema.dropTable('vertex_w_envelope').ifExists().execute();
  await db.schema.dropTable('vertex_social_action').ifExists().execute();
  await db.schema.dropTable('vertex_convo_member').ifExists().execute();
  await db.schema.dropTable('vertex_message_props').ifExists().execute();
  await db.schema.dropTable('vertex_profile_fragment').ifExists().execute();
  await db.schema.dropTable('vertex_project_props').ifExists().execute();
  await db.schema.dropTable('vertex_atproto_action').ifExists().execute();
  await db.schema.dropTable('vertex_label').ifExists().execute();
  await db.schema.dropTable('vertex_prekeys').ifExists().execute();
  await db.schema.dropTable('vertex_push_subscription').ifExists().execute();
  await db.schema.dropTable('vertex_editor_project').ifExists().execute();
  await db.schema.dropTable('vertex_editor_file').ifExists().execute();
  await db.schema.dropTable('vertex_blockchain_actor').ifExists().execute();
  await db.schema.dropTable('vertex_dns_observation').ifExists().execute();
  await db.schema.dropTable('vertex_risk_signal').ifExists().execute();
  await db.schema.dropTable('vertex_collector_run').ifExists().execute();
  await db.schema.dropTable('vertex_yabai_flag').ifExists().execute();
  await db.schema.dropTable('vertex_scan_result').ifExists().execute();
  await db.schema.dropTable('vertex_isekai_world_state').ifExists().execute();
  await db.schema.dropTable('vertex_isekai_chunk_data').ifExists().execute();
  await db.schema.dropTable('vertex_isekai_creature_roster').ifExists().execute();
  await db.schema.dropTable('vertex_isekai_inventory_item').ifExists().execute();
  await db.schema.dropTable('vertex_isekai_brainrot_event').ifExists().execute();
  await db.schema.dropTable('vertex_isekai_compliance_dep').ifExists().execute();
  await db.schema.dropTable('vertex_isekai_game_capture').ifExists().execute();
  await db.schema.dropTable('vertex_isekai_game_craft').ifExists().execute();
  await db.schema.dropTable('vertex_isekai_game_brainrot_encounter').ifExists().execute();
  await db.schema.dropTable('vertex_business_person').ifExists().execute();
  await db.schema.dropTable('vertex_natural_person').ifExists().execute();
  await db.schema.dropTable('vertex_mangaka').ifExists().execute();
  await db.schema.dropTable('vertex_i18n').ifExists().execute();
  await db.schema.dropTable('vertex_media_content').ifExists().execute();
  await db.schema.dropTable('vertex_scheduling').ifExists().execute();
  await db.schema.dropTable('vertex_sensor').ifExists().execute();
  await db.schema.dropTable('vertex_joucho').ifExists().execute();
  await db.schema.dropTable('vertex_crawl_job').ifExists().execute();
  await db.schema.dropTable('vertex_gov_municipality').ifExists().execute();
  await db.schema.dropTable('edge_follows').ifExists().execute();
  await db.schema.dropTable('edge_follows_by_dest').ifExists().execute();
  await db.schema.dropTable('edge_likes').ifExists().execute();
  await db.schema.dropTable('edge_likes_by_dest').ifExists().execute();
  await db.schema.dropTable('edge_reposts').ifExists().execute();
  await db.schema.dropTable('edge_reposts_by_dest').ifExists().execute();
  await db.schema.dropTable('edge_blocks').ifExists().execute();
  await db.schema.dropTable('edge_has_author').ifExists().execute();
  await db.schema.dropTable('edge_has_author_by_dest').ifExists().execute();
  await db.schema.dropTable('edge_reply').ifExists().execute();
  await db.schema.dropTable('edge_reply_by_dest').ifExists().execute();
  await db.schema.dropTable('edge_hosts_page').ifExists().execute();
  await db.schema.dropTable('edge_links_to').ifExists().execute();
  await db.schema.dropTable('edge_links_to_by_dest').ifExists().execute();
  await db.schema.dropTable('edge_links_to_domain').ifExists().execute();
  await db.schema.dropTable('edge_chunk_of').ifExists().execute();
  await db.schema.dropTable('edge_in_app').ifExists().execute();
  await db.schema.dropTable('edge_in_project').ifExists().execute();
  await db.schema.dropTable('edge_membership').ifExists().execute();
  await db.schema.dropTable('edge_membership_by_dest').ifExists().execute();
  await db.schema.dropTable('edge_list_item').ifExists().execute();
  await db.schema.dropTable('edge_list_item_by_dest').ifExists().execute();
  await db.schema.dropTable('edge_enacts').ifExists().execute();
  await db.schema.dropTable('edge_supersedes').ifExists().execute();
  await db.schema.dropTable('edge_interprets').ifExists().execute();
  await db.schema.dropTable('edge_enforces').ifExists().execute();
  await db.schema.dropTable('edge_crafts').ifExists().execute();
  await db.schema.dropTable('edge_owns').ifExists().execute();
  await db.schema.dropTable('edge_requires').ifExists().execute();
  await db.schema.dropTable('edge_rewards').ifExists().execute();
  await db.schema.dropTable('edge_contains').ifExists().execute();
  await db.schema.dropTable('edge_contains_by_dest').ifExists().execute();
  await db.schema.dropTable('edge_produces').ifExists().execute();
  await db.schema.dropTable('edge_located_at').ifExists().execute();
  await db.schema.dropTable('edge_transacts').ifExists().execute();
  await db.schema.dropTable('edge_treats').ifExists().execute();
  await db.schema.dropTable('edge_targets').ifExists().execute();
  await db.schema.dropTable('edge_connects').ifExists().execute();
  await db.schema.dropTable('edge_disposes').ifExists().execute();
  await db.schema.dropTable('edge_governance').ifExists().execute();
  await db.schema.dropTable('edge_capability').ifExists().execute();
  await db.schema.dropTable('edge_sequence_flow').ifExists().execute();
  await db.schema.dropTable('edge_bpmn_contains').ifExists().execute();
  await db.schema.dropTable('edge_bpmn_assigns').ifExists().execute();
  await db.schema.dropTable('edge_bpmn_references').ifExists().execute();
  await db.schema.dropTable('edge_bpmn_instance_of').ifExists().execute();
  await db.schema.dropTable('edge_controls_wallet').ifExists().execute();
  await db.schema.dropTable('edge_emits_risk').ifExists().execute();
  await db.schema.dropTable('edge_registered_with').ifExists().execute();
  await db.schema.dropTable('edge_wallet_cluster').ifExists().execute();
  await db.schema.dropTable('edge_flags').ifExists().execute();
  await db.schema.dropTable('edge_cites').ifExists().execute();
  await db.schema.dropTable('edge_has_judgment').ifExists().execute();
  await db.schema.dropTable('edge_filed_at').ifExists().execute();
  await db.schema.dropTable('edge_presides').ifExists().execute();
  await db.schema.dropTable('edge_maps_to_jurisdiction').ifExists().execute();
}
