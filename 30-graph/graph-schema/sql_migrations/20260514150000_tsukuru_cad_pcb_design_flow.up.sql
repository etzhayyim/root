-- tsukuru: CAD/PCB design project schema + LangGraph design-flow topologies
-- Supports open-robo (and any hardware project) on tsukuru.etzhayyim.com
--
-- Tables:
--   vertex_tsukuru_cad_project  — one row per hardware design project
--   vertex_tsukuru_cad_part     — one row per CAD part within a project
--   vertex_tsukuru_pcb_project  — one row per PCB design project
--   edge_tsukuru_project_part   — CAD project → part membership
--
-- LangGraph topologies (INSERT into existing vertex_langgraph_assistant/node):
--   tsukuru_cad_design_flow.v1  — Fusion360 design → Meviy quote → order
--   tsukuru_pcb_design_flow.v1  — KiCad design → P-Ban.com quote → assembly

-- ─── vertex_tsukuru_cad_project ──────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS vertex_tsukuru_cad_project (
  vertex_id         VARCHAR PRIMARY KEY,
  _seq              BIGINT,
  sensitivity_ord   BIGINT,
  owner_did         VARCHAR,
  actor_did         VARCHAR,
  org_did           VARCHAR,
  created_at        VARCHAR,
  updated_at        VARCHAR,
  project_id        VARCHAR NOT NULL,
  project_name      VARCHAR,
  product_ref       VARCHAR,    -- e.g. "etzhayyim-project-open-robo"
  cad_tool          VARCHAR,    -- fusion360 | onshape | freecad
  status            VARCHAR,    -- draft | modeling | tolerance_review | ready_to_order | ordered | delivered
  total_parts       INTEGER,
  parts_completed   INTEGER,
  assembly_step_ref VARCHAR,    -- blob CID of top-level assembly STEP
  meviy_quote_id    VARCHAR,
  meviy_quote_jpy   BIGINT,
  meviy_order_id    VARCHAR,
  tsukuru_order_vid VARCHAR     -- FK → vertex_tsukuru_production_order
);

CREATE INDEX IF NOT EXISTS idx_tsukuru_cad_project_id
  ON vertex_tsukuru_cad_project (project_id);
CREATE INDEX IF NOT EXISTS idx_tsukuru_cad_project_owner
  ON vertex_tsukuru_cad_project (owner_did);
CREATE INDEX IF NOT EXISTS idx_tsukuru_cad_project_product_ref
  ON vertex_tsukuru_cad_project (product_ref);
CREATE INDEX IF NOT EXISTS idx_tsukuru_cad_project_status
  ON vertex_tsukuru_cad_project (status);

-- ─── vertex_tsukuru_cad_part ─────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS vertex_tsukuru_cad_part (
  vertex_id         VARCHAR PRIMARY KEY,
  _seq              BIGINT,
  sensitivity_ord   BIGINT,
  owner_did         VARCHAR,
  actor_did         VARCHAR,
  org_did           VARCHAR,
  created_at        VARCHAR,
  updated_at        VARCHAR,
  project_vid       VARCHAR NOT NULL,  -- FK → vertex_tsukuru_cad_project
  part_number       VARCHAR,           -- e.g. "01-001"
  part_name         VARCHAR,           -- e.g. "Bottom_Plate"
  material          VARCHAR,           -- AL6061 | SUS304 | TPU95A | PA12
  process           VARCHAR,           -- cnc_milling | laser_cut | fdm_print | sls_print
  status            VARCHAR,           -- not_started | modeling | done | quoted | ordered | delivered | fit_ok | fit_ng
  step_file_ref     VARCHAR,           -- blob CID of individual part STEP
  tolerance_class   VARCHAR,           -- standard | h7 | h6
  surface_finish    VARCHAR,           -- anodize_black | anodize_silver | raw
  quantity          INTEGER,
  unit_price_jpy    BIGINT,
  meviy_part_id     VARCHAR,
  fit_check_note    VARCHAR
);

CREATE INDEX IF NOT EXISTS idx_tsukuru_cad_part_project
  ON vertex_tsukuru_cad_part (project_vid);
CREATE INDEX IF NOT EXISTS idx_tsukuru_cad_part_status
  ON vertex_tsukuru_cad_part (project_vid, status);

-- ─── vertex_tsukuru_pcb_project ──────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS vertex_tsukuru_pcb_project (
  vertex_id           VARCHAR PRIMARY KEY,
  _seq                BIGINT,
  sensitivity_ord     BIGINT,
  owner_did           VARCHAR,
  actor_did           VARCHAR,
  org_did             VARCHAR,
  created_at          VARCHAR,
  updated_at          VARCHAR,
  project_id          VARCHAR NOT NULL,
  pcb_name            VARCHAR,
  product_ref         VARCHAR,           -- e.g. "etzhayyim-project-open-robo"
  kicad_version       VARCHAR,           -- "8.0"
  board_size_mm       VARCHAR,           -- "85x65"
  layer_count         INTEGER,
  status              VARCHAR,           -- schematic | layout | drc_pass | gerber_ready | quoted | ordered | assembled | tested
  schematic_ref       VARCHAR,           -- blob CID of .kicad_sch
  layout_ref          VARCHAR,           -- blob CID of .kicad_pcb
  gerber_ref          VARCHAR,           -- blob CID of Gerber ZIP
  bom_ref             VARCHAR,           -- blob CID of BOM CSV
  drc_errors          INTEGER,
  component_count     INTEGER,
  pban_quote_id       VARCHAR,
  pban_quote_jpy      BIGINT,
  pban_order_id       VARCHAR,
  quantity_ordered    INTEGER,
  assembly_vendor     VARCHAR,           -- e.g. "sanwa-automation"
  tsukuru_order_vid   VARCHAR            -- FK → vertex_tsukuru_production_order
);

CREATE INDEX IF NOT EXISTS idx_tsukuru_pcb_project_id
  ON vertex_tsukuru_pcb_project (project_id);
CREATE INDEX IF NOT EXISTS idx_tsukuru_pcb_project_owner
  ON vertex_tsukuru_pcb_project (owner_did);
CREATE INDEX IF NOT EXISTS idx_tsukuru_pcb_project_product_ref
  ON vertex_tsukuru_pcb_project (product_ref);
CREATE INDEX IF NOT EXISTS idx_tsukuru_pcb_project_status
  ON vertex_tsukuru_pcb_project (status);

-- ─── edge_tsukuru_project_part ───────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS edge_tsukuru_project_part (
  edge_id           VARCHAR PRIMARY KEY,
  src_vid           VARCHAR NOT NULL,   -- vertex_tsukuru_cad_project
  dst_vid           VARCHAR NOT NULL,   -- vertex_tsukuru_cad_part
  relation          VARCHAR,
  created_at        VARCHAR,
  owner_did         VARCHAR,
  sensitivity_ord   BIGINT
);

CREATE INDEX IF NOT EXISTS idx_tsukuru_project_part_src
  ON edge_tsukuru_project_part (src_vid);
CREATE INDEX IF NOT EXISTS idx_tsukuru_project_part_dst
  ON edge_tsukuru_project_part (dst_vid);

-- ─── MCP tool definitions ─────────────────────────────────────────────────────

INSERT INTO vertex_mcp_tool_def
  (vertex_id, _seq, sensitivity_ord, nsid, actor_did, actor_host, lexicon_type,
   description, input_schema, output_schema, visibility, version, enabled,
   source_path, org_id, user_id, actor_id, created_at)
VALUES
  ('at://did:web:tsukuru.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-tsukuru-cadProject-create',
   0, 0, 'com.etzhayyim.apps.tsukuru.cadProject.create',
   'did:web:tsukuru.etzhayyim.com', 'tsukuru.etzhayyim.com', 'procedure',
   'Create a new CAD design project on tsukuru, linked to a hardware product.',
   '{"type":"object","required":["projectName","productRef","cadTool","totalParts"],"properties":{"projectName":{"type":"string"},"productRef":{"type":"string"},"cadTool":{"type":"string","enum":["fusion360","onshape","freecad"]},"totalParts":{"type":"integer"}}}',
   '{"type":"object","properties":{"projectVid":{"type":"string"},"projectId":{"type":"string"}}}',
   'internal', 1, TRUE,
   '00-contracts/lexicons/com/etzhayyim/apps/tsukuru/cadProject/create.json',
   'anon', 'anon', '', '2026-05-14T15:00:00Z'),

  ('at://did:web:tsukuru.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-tsukuru-cadPart-upsert',
   0, 0, 'com.etzhayyim.apps.tsukuru.cadPart.upsert',
   'did:web:tsukuru.etzhayyim.com', 'tsukuru.etzhayyim.com', 'procedure',
   'Upsert a CAD part record within a project (create or update status/step_file_ref).',
   '{"type":"object","required":["projectVid","partNumber","partName"],"properties":{"projectVid":{"type":"string"},"partNumber":{"type":"string"},"partName":{"type":"string"},"material":{"type":"string"},"process":{"type":"string"},"status":{"type":"string"},"stepFileRef":{"type":"string"},"quantity":{"type":"integer"}}}',
   '{"type":"object","properties":{"partVid":{"type":"string"}}}',
   'internal', 1, TRUE,
   '00-contracts/lexicons/com/etzhayyim/apps/tsukuru/cadPart/upsert.json',
   'anon', 'anon', '', '2026-05-14T15:00:00Z'),

  ('at://did:web:tsukuru.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-tsukuru-meviy-requestQuote',
   0, 0, 'com.etzhayyim.apps.tsukuru.meviy.requestQuote',
   'did:web:tsukuru.etzhayyim.com', 'tsukuru.etzhayyim.com', 'procedure',
   'Submit STEP files to Misumi Meviy for automatic machining quote.',
   '{"type":"object","required":["projectVid"],"properties":{"projectVid":{"type":"string"},"partVids":{"type":"array","items":{"type":"string"}}}}',
   '{"type":"object","properties":{"quoteId":{"type":"string"},"totalJpy":{"type":"integer"},"lineItems":{"type":"array"},"leadDays":{"type":"integer"}}}',
   'internal', 1, TRUE,
   '00-contracts/lexicons/com/etzhayyim/apps/tsukuru/meviy/requestQuote.json',
   'anon', 'anon', '', '2026-05-14T15:00:00Z'),

  ('at://did:web:tsukuru.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-tsukuru-pcbProject-create',
   0, 0, 'com.etzhayyim.apps.tsukuru.pcbProject.create',
   'did:web:tsukuru.etzhayyim.com', 'tsukuru.etzhayyim.com', 'procedure',
   'Create a new PCB design project on tsukuru.',
   '{"type":"object","required":["pcbName","productRef"],"properties":{"pcbName":{"type":"string"},"productRef":{"type":"string"},"kicadVersion":{"type":"string"},"boardSizeMm":{"type":"string"},"layerCount":{"type":"integer"}}}',
   '{"type":"object","properties":{"projectVid":{"type":"string"},"projectId":{"type":"string"}}}',
   'internal', 1, TRUE,
   '00-contracts/lexicons/com/etzhayyim/apps/tsukuru/pcbProject/create.json',
   'anon', 'anon', '', '2026-05-14T15:00:00Z'),

  ('at://did:web:tsukuru.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-tsukuru-pban-requestQuote',
   0, 0, 'com.etzhayyim.apps.tsukuru.pban.requestQuote',
   'did:web:tsukuru.etzhayyim.com', 'tsukuru.etzhayyim.com', 'procedure',
   'Submit Gerber ZIP to P-Ban.com for PCB fabrication + assembly quote.',
   '{"type":"object","required":["projectVid","gerberRef"],"properties":{"projectVid":{"type":"string"},"gerberRef":{"type":"string"},"quantity":{"type":"integer"},"needsAssembly":{"type":"boolean"}}}',
   '{"type":"object","properties":{"quoteId":{"type":"string"},"pcbJpy":{"type":"integer"},"assemblyJpy":{"type":"integer"},"totalJpy":{"type":"integer"},"leadDays":{"type":"integer"}}}',
   'internal', 1, TRUE,
   '00-contracts/lexicons/com/etzhayyim/apps/tsukuru/pban/requestQuote.json',
   'anon', 'anon', '', '2026-05-14T15:00:00Z');

FLUSH;

-- ─── LangGraph topology: tsukuru_cad_design_flow.v1 ─────────────────────────

INSERT INTO vertex_langgraph_assistant
  (vertex_id, _seq, sensitivity_ord, assistant_id, version, kind, factory_path,
   spec, description, created_at, checkpointer_mode, authored_by)
VALUES
  ('tsukuru_cad_design_flow.v1', 0, 0, 'tsukuru_cad_design_flow.v1', 1, 'topology', NULL,
   '{"state_keys":["projectVid","currentPartIdx","totalParts","stepFiles","toleranceErrors","meviyQuote","orderApproved","orderId","fitCheckResults","ok","error"],"entry":"project_init","edges":[{"from":"project_init","to":"part_modeling"},{"from":"part_modeling","to":"tolerance_review","condition":"allPartsModeled"},{"from":"part_modeling","to":"part_modeling","condition":"hasRemainingParts"},{"from":"tolerance_review","to":"meviy_quote","condition":"toleranceOk"},{"from":"tolerance_review","to":"part_modeling","condition":"hasToleranceErrors"},{"from":"meviy_quote","to":"order_decision"},{"from":"order_decision","to":"order_submit","condition":"approved"},{"from":"order_decision","to":"END","condition":"rejected"},{"from":"order_submit","to":"delivery_track"},{"from":"delivery_track","to":"fit_check","condition":"delivered"},{"from":"delivery_track","to":"delivery_track","condition":"inTransit"},{"from":"fit_check","to":"END"}]}',
   'CAD design flow: Fusion360 part modeling → tolerance review → Meviy quote → order → delivery → fit check',
   '2026-05-14T15:00:00Z', 'rw_vertex', 'did:web:tsukuru.etzhayyim.com');

INSERT INTO vertex_langgraph_assistant_node
  (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at)
VALUES
  ('tsukuru_cad_design_flow.v1:project_init', 0, 0, 'tsukuru_cad_design_flow.v1',
   'project_init', 'mcp_tool', 'mcp://com.etzhayyim.apps.tsukuru.cadProject.create',
   '{"input_keys":["productRef","projectName","cadTool","totalParts"],"result_key":"projectVid","args":{"name":"com.etzhayyim.apps.tsukuru.cadProject.create"}}',
   '2026-05-14T15:00:00Z'),

  ('tsukuru_cad_design_flow.v1:part_modeling', 0, 0, 'tsukuru_cad_design_flow.v1',
   'part_modeling', 'mcp_tool', 'mcp://com.etzhayyim.apps.tsukuru.cadPart.upsert',
   '{"input_keys":["projectVid","currentPartIdx","stepFiles"],"result_key":"partVid","args":{"name":"com.etzhayyim.apps.tsukuru.cadPart.upsert"},"loop_var":"currentPartIdx","loop_max":"totalParts"}',
   '2026-05-14T15:00:00Z'),

  ('tsukuru_cad_design_flow.v1:tolerance_review', 0, 0, 'tsukuru_cad_design_flow.v1',
   'tolerance_review', 'mcp_tool', 'mcp://com.etzhayyim.tools.sql.query',
   '{"input_keys":["projectVid"],"result_key":"toleranceErrors","args":{"name":"com.etzhayyim.tools.sql.query","sql":"SELECT part_number, tolerance_class, fit_check_note FROM vertex_tsukuru_cad_part WHERE project_vid = %(project_vid)s AND (tolerance_class NOT IN (''standard'',''h7'',''h6'') OR fit_check_note IS NOT NULL) LIMIT 50"}}',
   '2026-05-14T15:00:00Z'),

  ('tsukuru_cad_design_flow.v1:meviy_quote', 0, 0, 'tsukuru_cad_design_flow.v1',
   'meviy_quote', 'mcp_tool', 'mcp://com.etzhayyim.apps.tsukuru.meviy.requestQuote',
   '{"input_keys":["projectVid"],"result_key":"meviyQuote","args":{"name":"com.etzhayyim.apps.tsukuru.meviy.requestQuote"}}',
   '2026-05-14T15:00:00Z'),

  ('tsukuru_cad_design_flow.v1:order_decision', 0, 0, 'tsukuru_cad_design_flow.v1',
   'order_decision', 'human_review', NULL,
   '{"prompt":"Meviy quote ready. Review line items and approve or reject the order.","input_keys":["meviyQuote"],"result_key":"orderApproved","timeout_hours":48}',
   '2026-05-14T15:00:00Z'),

  ('tsukuru_cad_design_flow.v1:order_submit', 0, 0, 'tsukuru_cad_design_flow.v1',
   'order_submit', 'mcp_tool', 'mcp://com.etzhayyim.apps.tsukuru.productionOrder.create',
   '{"input_keys":["projectVid","meviyQuote"],"result_key":"orderId","args":{"name":"com.etzhayyim.apps.tsukuru.productionOrder.create","fulfillmentMode":"mto","vendorDid":"did:web:misumi-meviy.tsukuru.etzhayyim.com"}}',
   '2026-05-14T15:00:00Z'),

  ('tsukuru_cad_design_flow.v1:delivery_track', 0, 0, 'tsukuru_cad_design_flow.v1',
   'delivery_track', 'mcp_tool', 'mcp://com.etzhayyim.tools.sql.query',
   '{"input_keys":["orderId"],"result_key":"deliveryStatus","args":{"name":"com.etzhayyim.tools.sql.query","sql":"SELECT value_json::jsonb ->> ''status'' AS status, value_json::jsonb ->> ''trackingNumber'' AS tracking FROM vertex_tsukuru_production_order WHERE vertex_id = %(order_id)s LIMIT 1"}}',
   '2026-05-14T15:00:00Z'),

  ('tsukuru_cad_design_flow.v1:fit_check', 0, 0, 'tsukuru_cad_design_flow.v1',
   'fit_check', 'human_review', NULL,
   '{"prompt":"Parts delivered. Perform physical fit check for each part (bearing press-fit, shaft clearance, track tension). Record pass/fail per part.","input_keys":["projectVid"],"result_key":"fitCheckResults","timeout_hours":72}',
   '2026-05-14T15:00:00Z');

FLUSH;

-- ─── LangGraph topology: tsukuru_pcb_design_flow.v1 ─────────────────────────

INSERT INTO vertex_langgraph_assistant
  (vertex_id, _seq, sensitivity_ord, assistant_id, version, kind, factory_path,
   spec, description, created_at, checkpointer_mode, authored_by)
VALUES
  ('tsukuru_pcb_design_flow.v1', 0, 0, 'tsukuru_pcb_design_flow.v1', 1, 'topology', NULL,
   '{"state_keys":["projectVid","schematicDone","layoutDone","gerberRef","drcErrors","pbanQuote","orderApproved","orderId","assemblyStatus","testResults","ok","error"],"entry":"schematic_design","edges":[{"from":"schematic_design","to":"pcb_layout","condition":"schematicDone"},{"from":"pcb_layout","to":"drc_check","condition":"layoutDone"},{"from":"drc_check","to":"gerber_export","condition":"drcErrors==0"},{"from":"drc_check","to":"pcb_layout","condition":"drcErrors>0"},{"from":"gerber_export","to":"pban_quote"},{"from":"pban_quote","to":"order_decision"},{"from":"order_decision","to":"order_submit","condition":"approved"},{"from":"order_decision","to":"END","condition":"rejected"},{"from":"order_submit","to":"delivery_track"},{"from":"delivery_track","to":"assembly_check","condition":"pcbDelivered"},{"from":"delivery_track","to":"delivery_track","condition":"inTransit"},{"from":"assembly_check","to":"END"}]}',
   'PCB design flow: KiCad schematic → layout → DRC → Gerber → P-Ban.com quote → order → assembly → test',
   '2026-05-14T15:00:00Z', 'rw_vertex', 'did:web:tsukuru.etzhayyim.com');

INSERT INTO vertex_langgraph_assistant_node
  (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at)
VALUES
  ('tsukuru_pcb_design_flow.v1:schematic_design', 0, 0, 'tsukuru_pcb_design_flow.v1',
   'schematic_design', 'mcp_tool', 'mcp://com.etzhayyim.apps.tsukuru.pcbProject.create',
   '{"input_keys":["productRef","pcbName","kicadVersion","boardSizeMm","layerCount"],"result_key":"projectVid","args":{"name":"com.etzhayyim.apps.tsukuru.pcbProject.create"}}',
   '2026-05-14T15:00:00Z'),

  ('tsukuru_pcb_design_flow.v1:pcb_layout', 0, 0, 'tsukuru_pcb_design_flow.v1',
   'pcb_layout', 'human_review', NULL,
   '{"prompt":"Complete PCB layout in KiCad. Upload .kicad_pcb blob and confirm layout is done.","input_keys":["projectVid"],"result_key":"layoutDone","timeout_hours":168}',
   '2026-05-14T15:00:00Z'),

  ('tsukuru_pcb_design_flow.v1:drc_check', 0, 0, 'tsukuru_pcb_design_flow.v1',
   'drc_check', 'mcp_tool', 'mcp://com.etzhayyim.tools.sql.query',
   '{"input_keys":["projectVid"],"result_key":"drcErrors","args":{"name":"com.etzhayyim.tools.sql.query","sql":"SELECT drc_errors FROM vertex_tsukuru_pcb_project WHERE vertex_id = %(project_vid)s LIMIT 1"}}',
   '2026-05-14T15:00:00Z'),

  ('tsukuru_pcb_design_flow.v1:gerber_export', 0, 0, 'tsukuru_pcb_design_flow.v1',
   'gerber_export', 'human_review', NULL,
   '{"prompt":"Export Gerber files from KiCad (File → Fabrication Outputs → Gerbers). Upload Gerber ZIP and confirm.","input_keys":["projectVid"],"result_key":"gerberRef","timeout_hours":24}',
   '2026-05-14T15:00:00Z'),

  ('tsukuru_pcb_design_flow.v1:pban_quote', 0, 0, 'tsukuru_pcb_design_flow.v1',
   'pban_quote', 'mcp_tool', 'mcp://com.etzhayyim.apps.tsukuru.pban.requestQuote',
   '{"input_keys":["projectVid","gerberRef"],"result_key":"pbanQuote","args":{"name":"com.etzhayyim.apps.tsukuru.pban.requestQuote","quantity":10,"needsAssembly":true}}',
   '2026-05-14T15:00:00Z'),

  ('tsukuru_pcb_design_flow.v1:order_decision', 0, 0, 'tsukuru_pcb_design_flow.v1',
   'order_decision', 'human_review', NULL,
   '{"prompt":"P-Ban.com PCB quote ready. Review fabrication + assembly cost and approve or reject.","input_keys":["pbanQuote"],"result_key":"orderApproved","timeout_hours":48}',
   '2026-05-14T15:00:00Z'),

  ('tsukuru_pcb_design_flow.v1:order_submit', 0, 0, 'tsukuru_pcb_design_flow.v1',
   'order_submit', 'mcp_tool', 'mcp://com.etzhayyim.apps.tsukuru.productionOrder.create',
   '{"input_keys":["projectVid","pbanQuote"],"result_key":"orderId","args":{"name":"com.etzhayyim.apps.tsukuru.productionOrder.create","fulfillmentMode":"mto","vendorDid":"did:web:pban-com.tsukuru.etzhayyim.com"}}',
   '2026-05-14T15:00:00Z'),

  ('tsukuru_pcb_design_flow.v1:delivery_track', 0, 0, 'tsukuru_pcb_design_flow.v1',
   'delivery_track', 'mcp_tool', 'mcp://com.etzhayyim.tools.sql.query',
   '{"input_keys":["orderId"],"result_key":"deliveryStatus","args":{"name":"com.etzhayyim.tools.sql.query","sql":"SELECT value_json::jsonb ->> ''status'' AS status FROM vertex_tsukuru_production_order WHERE vertex_id = %(order_id)s LIMIT 1"}}',
   '2026-05-14T15:00:00Z'),

  ('tsukuru_pcb_design_flow.v1:assembly_check', 0, 0, 'tsukuru_pcb_design_flow.v1',
   'assembly_check', 'human_review', NULL,
   '{"prompt":"PCB received. Perform continuity test and power-on check. Record pass/fail, voltages, and any rework needed.","input_keys":["projectVid"],"result_key":"testResults","timeout_hours":72}',
   '2026-05-14T15:00:00Z');

FLUSH;
