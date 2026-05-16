ALTER TABLE "vertex_mangaka" ADD COLUMN IF NOT EXISTS "kind" VARCHAR;

ALTER TABLE "vertex_mangaka" ADD COLUMN IF NOT EXISTS "work_id" VARCHAR;

ALTER TABLE "vertex_mangaka" ADD COLUMN IF NOT EXISTS "chapter_id" VARCHAR;

ALTER TABLE "vertex_mangaka" ADD COLUMN IF NOT EXISTS "chapter_number" BIGINT;

ALTER TABLE "vertex_mangaka" ADD COLUMN IF NOT EXISTS "page_id" VARCHAR;

ALTER TABLE "vertex_mangaka" ADD COLUMN IF NOT EXISTS "panel_id" VARCHAR;

ALTER TABLE "vertex_mangaka" ADD COLUMN IF NOT EXISTS "project_id" VARCHAR;

ALTER TABLE "vertex_mangaka" ADD COLUMN IF NOT EXISTS "convo_id" VARCHAR;

ALTER TABLE "vertex_mangaka" ADD COLUMN IF NOT EXISTS "parent_project_id" VARCHAR;

ALTER TABLE "vertex_mangaka" ADD COLUMN IF NOT EXISTS "organization_id" VARCHAR;

ALTER TABLE "vertex_mangaka" ADD COLUMN IF NOT EXISTS "environment_id" VARCHAR;

ALTER TABLE "vertex_mangaka" ADD COLUMN IF NOT EXISTS "role" VARCHAR;

ALTER TABLE "vertex_mangaka" ADD COLUMN IF NOT EXISTS "content" TEXT;

ALTER TABLE "vertex_mangaka" ADD COLUMN IF NOT EXISTS "document_json" TEXT;

ALTER TABLE "vertex_mangaka" ADD COLUMN IF NOT EXISTS "members_json" TEXT;

ALTER TABLE "vertex_mangaka" ADD COLUMN IF NOT EXISTS "image_url" VARCHAR;

ALTER TABLE "vertex_mangaka" ADD COLUMN IF NOT EXISTS "model" VARCHAR;

ALTER TABLE "vertex_mangaka" ADD COLUMN IF NOT EXISTS "width" DOUBLE PRECISION;

ALTER TABLE "vertex_mangaka" ADD COLUMN IF NOT EXISTS "height" DOUBLE PRECISION;

ALTER TABLE "vertex_mangaka" ADD COLUMN IF NOT EXISTS "x" DOUBLE PRECISION;

ALTER TABLE "vertex_mangaka" ADD COLUMN IF NOT EXISTS "y" DOUBLE PRECISION;

ALTER TABLE "vertex_mangaka" ADD COLUMN IF NOT EXISTS "w" DOUBLE PRECISION;

ALTER TABLE "vertex_mangaka" ADD COLUMN IF NOT EXISTS "h" DOUBLE PRECISION;

CREATE INDEX IF NOT EXISTS idx_vertex_mangaka_repo_collection_created ON vertex_mangaka (repo, collection, created_at);

CREATE INDEX IF NOT EXISTS idx_vertex_mangaka_repo_collection_rkey ON vertex_mangaka (repo, collection, rkey);

CREATE INDEX IF NOT EXISTS idx_vertex_mangaka_repo_parent_rkey ON vertex_mangaka (repo, parent_rkey);

CREATE INDEX IF NOT EXISTS idx_vertex_mangaka_repo_work_id ON vertex_mangaka (repo, work_id);

CREATE INDEX IF NOT EXISTS idx_vertex_mangaka_repo_chapter_id ON vertex_mangaka (repo, chapter_id);

CREATE INDEX IF NOT EXISTS idx_vertex_mangaka_repo_page_id ON vertex_mangaka (repo, page_id);

CREATE INDEX IF NOT EXISTS idx_vertex_mangaka_repo_panel_id ON vertex_mangaka (repo, panel_id);

CREATE INDEX IF NOT EXISTS idx_vertex_mangaka_repo_project_id ON vertex_mangaka (repo, project_id);

CREATE INDEX IF NOT EXISTS idx_vertex_mangaka_repo_convo_id ON vertex_mangaka (repo, convo_id);

CREATE INDEX IF NOT EXISTS idx_vertex_record_attribute_record_vid_name ON vertex_record_attribute (record_vid, name);

CREATE INDEX IF NOT EXISTS idx_vertex_record_attribute_name_value_text ON vertex_record_attribute (name, value_text);

CREATE INDEX IF NOT EXISTS idx_vertex_record_attribute_name_value_num ON vertex_record_attribute (name, value_num);

CREATE INDEX IF NOT EXISTS idx_edge_contains_src_vid ON edge_contains (src_vid);

CREATE INDEX IF NOT EXISTS idx_edge_in_project_src_vid ON edge_in_project (src_vid);

CREATE INDEX IF NOT EXISTS idx_edge_membership_src_vid ON edge_membership (src_vid);

CREATE VIEW IF NOT EXISTS view_mangaka_record_flat AS
    WITH attr AS (
      SELECT
        record_vid,
        MAX(CASE WHEN name = 'id' THEN value_text END) AS id,
        MAX(CASE WHEN name = 'workId' THEN COALESCE(value_text, CAST(value_num AS VARCHAR), value_bool, value_ts) END) AS work_id,
        MAX(CASE WHEN name = 'chapterId' THEN COALESCE(value_text, CAST(value_num AS VARCHAR), value_bool, value_ts) END) AS chapter_id,
        MAX(CASE WHEN name = 'pageId' THEN COALESCE(value_text, CAST(value_num AS VARCHAR), value_bool, value_ts) END) AS page_id,
        MAX(CASE WHEN name = 'panelId' THEN COALESCE(value_text, CAST(value_num AS VARCHAR), value_bool, value_ts) END) AS panel_id,
        MAX(CASE WHEN name = 'projectId' THEN COALESCE(value_text, CAST(value_num AS VARCHAR), value_bool, value_ts) END) AS project_id,
        MAX(CASE WHEN name = 'convoId' THEN COALESCE(value_text, CAST(value_num AS VARCHAR), value_bool, value_ts) END) AS convo_id,
        MAX(CASE WHEN name = 'parentProjectId' THEN COALESCE(value_text, CAST(value_num AS VARCHAR), value_bool, value_ts) END) AS parent_project_id,
        MAX(CASE WHEN name = 'organizationId' THEN COALESCE(value_text, CAST(value_num AS VARCHAR), value_bool, value_ts) END) AS organization_id,
        MAX(CASE WHEN name = 'environmentId' THEN COALESCE(value_text, CAST(value_num AS VARCHAR), value_bool, value_ts) END) AS environment_id,
        MAX(CASE WHEN name = 'document' THEN value_text END) AS document_json,
        MAX(CASE WHEN name = 'project' THEN value_text END) AS project_json,
        MAX(CASE WHEN name = 'content' THEN value_text END) AS content,
        MAX(CASE WHEN name = 'imageUrl' THEN value_text END) AS image_url,
        MAX(CASE WHEN name = 'model' THEN value_text END) AS model,
        MAX(CASE WHEN name = 'members' THEN value_text END) AS members_json,
        MAX(CASE WHEN name = 'displayName' THEN value_text END) AS display_name,
        MAX(CASE WHEN name = 'name' THEN value_text END) AS name,
        MAX(CASE WHEN name = 'title' THEN value_text END) AS title,
        MAX(CASE WHEN name = 'description' THEN value_text END) AS description,
        MAX(CASE WHEN name = 'role' THEN value_text END) AS role,
        MAX(CASE WHEN name = 'pageNum' THEN CAST(value_num AS BIGINT) END) AS page_number,
        MAX(CASE WHEN name = 'chapterNum' THEN CAST(value_num AS BIGINT) END) AS chapter_number,
        MAX(CASE WHEN name = 'order' THEN CAST(value_num AS BIGINT) END) AS panel_number,
        MAX(CASE WHEN name = 'assetType' THEN value_text END) AS asset_type,
        MAX(CASE WHEN name = 'mimeType' THEN value_text END) AS mime_type,
        MAX(CASE WHEN name = 'width' THEN value_num END) AS width,
        MAX(CASE WHEN name = 'height' THEN value_num END) AS height,
        MAX(CASE WHEN name = 'x' THEN value_num END) AS x,
        MAX(CASE WHEN name = 'y' THEN value_num END) AS y,
        MAX(CASE WHEN name = 'w' THEN value_num END) AS w,
        MAX(CASE WHEN name = 'h' THEN value_num END) AS h
      FROM vertex_record_attribute
      GROUP BY record_vid
    )
    SELECT
      vm.vertex_id,
      vm._seq,
      vm.created_date,
      vm.sensitivity_ord,
      vm.owner_did,
      vm.rkey,
      vm.repo,
      vm.did,
      vm.collection,
      vm.label,
      COALESCE(vm.kind, split_part(vm.collection, '.', array_length(string_to_array(vm.collection, '.'), 1)), '') AS kind,
      COALESCE(vm.title, attr.title) AS title,
      COALESCE(vm.name, attr.name, vm.title, attr.title) AS name,
      COALESCE(vm.display_name, attr.display_name, vm.name, attr.name, vm.title, attr.title) AS display_name,
      COALESCE(vm.description, attr.description) AS description,
      vm.parent_rkey,
      COALESCE(vm.work_id, attr.work_id) AS work_id,
      COALESCE(vm.chapter_id, attr.chapter_id) AS chapter_id,
      COALESCE(vm.chapter_number, attr.chapter_number) AS chapter_number,
      COALESCE(vm.page_id, attr.page_id) AS page_id,
      COALESCE(vm.page_number, attr.page_number) AS page_number,
      COALESCE(vm.panel_id, attr.panel_id) AS panel_id,
      COALESCE(vm.panel_number, attr.panel_number) AS panel_number,
      COALESCE(vm.project_id, attr.project_id, vm.convo_id, attr.convo_id) AS project_id,
      COALESCE(vm.convo_id, attr.convo_id, vm.project_id, attr.project_id) AS convo_id,
      COALESCE(vm.parent_project_id, attr.parent_project_id) AS parent_project_id,
      COALESCE(vm.organization_id, attr.organization_id) AS organization_id,
      COALESCE(vm.environment_id, attr.environment_id) AS environment_id,
      COALESCE(vm.role, attr.role) AS role,
      COALESCE(vm.asset_type, attr.asset_type) AS asset_type,
      COALESCE(vm.mime_type, attr.mime_type) AS mime_type,
      vm.cid,
      vm.status,
      vm.created_at,
      COALESCE(vm.content, attr.content) AS content,
      COALESCE(vm.document_json, attr.document_json) AS document,
      attr.project_json AS project,
      COALESCE(vm.members_json, attr.members_json) AS members_json,
      COALESCE(vm.image_url, attr.image_url) AS image_url,
      COALESCE(vm.model, attr.model) AS model,
      COALESCE(vm.x, attr.x) AS x,
      COALESCE(vm.y, attr.y) AS y,
      COALESCE(vm.w, attr.w) AS w,
      COALESCE(vm.h, attr.h) AS h,
      COALESCE(vm.width, attr.width) AS width,
      COALESCE(vm.height, attr.height) AS height,
      COALESCE(attr.id, vm.rkey) AS id
    FROM vertex_mangaka vm
    LEFT JOIN attr ON attr.record_vid = vm.vertex_id;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_vertex_mangaka_count AS
    SELECT
      COALESCE(repo, '') AS repo,
      COALESCE(collection, '') AS collection,
      COALESCE(kind, split_part(collection, '.', array_length(string_to_array(collection, '.'), 1)), '') AS kind,
      COUNT(*)::bigint AS cnt
    FROM vertex_mangaka
    GROUP BY 1, 2, 3;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_mangaka_children_by_parent AS
    SELECT
      src_vid AS parent_vid,
      COALESCE(label, '') AS child_label,
      COUNT(*)::bigint AS cnt
    FROM edge_contains
    GROUP BY 1, 2;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_mangaka_members_by_project AS
    SELECT
      src_vid AS project_vid,
      COUNT(*)::bigint AS cnt
    FROM edge_membership
    GROUP BY 1;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_mangaka_generated_image_by_panel AS
    SELECT
      src_vid AS panel_vid,
      COUNT(*)::bigint AS cnt
    FROM edge_contains
    WHERE COALESCE(label, '') = 'generatedImage'
    GROUP BY 1;
