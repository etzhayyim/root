#!/usr/bin/env python3
"""
3-phase psycopg2 apply for 20260514150000_tsukuru_cad_pcb_design_flow.up.sql

Phase 1: CREATE TABLE × 4
Phase 2: CREATE INDEX × 12  (1.5s settle after phase 1)
Phase 3: INSERTs + FLUSH    (1.5s settle after phase 2)

Usage:
  DATABASE_URL=REDACTED_USE_DATABASE_URL_ENV python3 \
      30-graph/graph-schema/scripts/apply-20260514-tsukuru-cad-pcb.py
"""

import os
import sys
import time
import psycopg2

URL = os.environ.get("DATABASE_URL")
if not URL:
    print("ERROR: DATABASE_URL not set", file=sys.stderr)
    sys.exit(1)

PHASE1_TABLES = [
    # vertex_tsukuru_cad_project
    """
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
  product_ref       VARCHAR,
  cad_tool          VARCHAR,
  status            VARCHAR,
  total_parts       INTEGER,
  parts_completed   INTEGER,
  assembly_step_ref VARCHAR,
  meviy_quote_id    VARCHAR,
  meviy_quote_jpy   BIGINT,
  meviy_order_id    VARCHAR,
  tsukuru_order_vid VARCHAR
)
""",
    # vertex_tsukuru_cad_part
    """
CREATE TABLE IF NOT EXISTS vertex_tsukuru_cad_part (
  vertex_id         VARCHAR PRIMARY KEY,
  _seq              BIGINT,
  sensitivity_ord   BIGINT,
  owner_did         VARCHAR,
  actor_did         VARCHAR,
  org_did           VARCHAR,
  created_at        VARCHAR,
  updated_at        VARCHAR,
  project_vid       VARCHAR NOT NULL,
  part_number       VARCHAR,
  part_name         VARCHAR,
  material          VARCHAR,
  process           VARCHAR,
  status            VARCHAR,
  step_file_ref     VARCHAR,
  tolerance_class   VARCHAR,
  surface_finish    VARCHAR,
  quantity          INTEGER,
  unit_price_jpy    BIGINT,
  meviy_part_id     VARCHAR,
  fit_check_note    VARCHAR
)
""",
    # vertex_tsukuru_pcb_project
    """
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
  product_ref         VARCHAR,
  kicad_version       VARCHAR,
  board_size_mm       VARCHAR,
  layer_count         INTEGER,
  status              VARCHAR,
  schematic_ref       VARCHAR,
  layout_ref          VARCHAR,
  gerber_ref          VARCHAR,
  bom_ref             VARCHAR,
  drc_errors          INTEGER,
  component_count     INTEGER,
  pban_quote_id       VARCHAR,
  pban_quote_jpy      BIGINT,
  pban_order_id       VARCHAR,
  quantity_ordered    INTEGER,
  assembly_vendor     VARCHAR,
  tsukuru_order_vid   VARCHAR
)
""",
    # edge_tsukuru_project_part
    """
CREATE TABLE IF NOT EXISTS edge_tsukuru_project_part (
  edge_id           VARCHAR PRIMARY KEY,
  src_vid           VARCHAR NOT NULL,
  dst_vid           VARCHAR NOT NULL,
  relation          VARCHAR,
  created_at        VARCHAR,
  owner_did         VARCHAR,
  sensitivity_ord   BIGINT
)
""",
]

PHASE2_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_tsukuru_cad_project_id ON vertex_tsukuru_cad_project (project_id)",
    "CREATE INDEX IF NOT EXISTS idx_tsukuru_cad_project_owner ON vertex_tsukuru_cad_project (owner_did)",
    "CREATE INDEX IF NOT EXISTS idx_tsukuru_cad_project_product_ref ON vertex_tsukuru_cad_project (product_ref)",
    "CREATE INDEX IF NOT EXISTS idx_tsukuru_cad_project_status ON vertex_tsukuru_cad_project (status)",
    "CREATE INDEX IF NOT EXISTS idx_tsukuru_cad_part_project ON vertex_tsukuru_cad_part (project_vid)",
    "CREATE INDEX IF NOT EXISTS idx_tsukuru_cad_part_status ON vertex_tsukuru_cad_part (project_vid, status)",
    "CREATE INDEX IF NOT EXISTS idx_tsukuru_pcb_project_id ON vertex_tsukuru_pcb_project (project_id)",
    "CREATE INDEX IF NOT EXISTS idx_tsukuru_pcb_project_owner ON vertex_tsukuru_pcb_project (owner_did)",
    "CREATE INDEX IF NOT EXISTS idx_tsukuru_pcb_project_product_ref ON vertex_tsukuru_pcb_project (product_ref)",
    "CREATE INDEX IF NOT EXISTS idx_tsukuru_pcb_project_status ON vertex_tsukuru_pcb_project (status)",
    "CREATE INDEX IF NOT EXISTS idx_tsukuru_project_part_src ON edge_tsukuru_project_part (src_vid)",
    "CREATE INDEX IF NOT EXISTS idx_tsukuru_project_part_dst ON edge_tsukuru_project_part (dst_vid)",
]

PHASE3_INSERTS = """
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
   'anon', 'anon', '', '2026-05-14T15:00:00Z')
"""

PHASE3_INSERTS_DELETE = """
DELETE FROM vertex_mcp_tool_def WHERE vertex_id IN (
  'at://did:web:tsukuru.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-tsukuru-cadProject-create',
  'at://did:web:tsukuru.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-tsukuru-cadPart-upsert',
  'at://did:web:tsukuru.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-tsukuru-meviy-requestQuote',
  'at://did:web:tsukuru.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-tsukuru-pcbProject-create',
  'at://did:web:tsukuru.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-tsukuru-pban-requestQuote'
)
"""

PHASE3_LG_CAD = """
INSERT INTO vertex_langgraph_assistant
  (vertex_id, _seq, sensitivity_ord, owner_did, assistant_id, version, kind, factory_path,
   spec, description, created_at, checkpointer_mode)
VALUES
  ('tsukuru_cad_design_flow.v1', 0, 0, 'did:web:tsukuru.etzhayyim.com', 'tsukuru_cad_design_flow.v1', 1, 'topology', NULL,
   '{"state_keys":["projectVid","currentPartIdx","totalParts","stepFiles","toleranceErrors","meviyQuote","orderApproved","orderId","fitCheckResults","ok","error"],"entry":"project_init","edges":[{"from":"project_init","to":"part_modeling"},{"from":"part_modeling","to":"tolerance_review","condition":"allPartsModeled"},{"from":"part_modeling","to":"part_modeling","condition":"hasRemainingParts"},{"from":"tolerance_review","to":"meviy_quote","condition":"toleranceOk"},{"from":"tolerance_review","to":"part_modeling","condition":"hasToleranceErrors"},{"from":"meviy_quote","to":"order_decision"},{"from":"order_decision","to":"order_submit","condition":"approved"},{"from":"order_decision","to":"END","condition":"rejected"},{"from":"order_submit","to":"delivery_track"},{"from":"delivery_track","to":"fit_check","condition":"delivered"},{"from":"delivery_track","to":"delivery_track","condition":"inTransit"},{"from":"fit_check","to":"END"}]}',
   'CAD design flow: Fusion360 part modeling to tolerance review to Meviy quote to order to delivery to fit check',
   '2026-05-14T15:00:00Z', 'rw_vertex')
"""

PHASE3_LG_PCB = """
INSERT INTO vertex_langgraph_assistant
  (vertex_id, _seq, sensitivity_ord, owner_did, assistant_id, version, kind, factory_path,
   spec, description, created_at, checkpointer_mode)
VALUES
  ('tsukuru_pcb_design_flow.v1', 0, 0, 'did:web:tsukuru.etzhayyim.com', 'tsukuru_pcb_design_flow.v1', 1, 'topology', NULL,
   '{"state_keys":["projectVid","schematicDone","layoutDone","gerberRef","drcErrors","pbanQuote","orderApproved","orderId","assemblyStatus","testResults","ok","error"],"entry":"schematic_design","edges":[{"from":"schematic_design","to":"pcb_layout","condition":"schematicDone"},{"from":"pcb_layout","to":"drc_check","condition":"layoutDone"},{"from":"drc_check","to":"gerber_export","condition":"drcErrors==0"},{"from":"drc_check","to":"pcb_layout","condition":"drcErrors>0"},{"from":"gerber_export","to":"pban_quote"},{"from":"pban_quote","to":"order_decision"},{"from":"order_decision","to":"order_submit","condition":"approved"},{"from":"order_decision","to":"END","condition":"rejected"},{"from":"order_submit","to":"delivery_track"},{"from":"delivery_track","to":"assembly_check","condition":"pcbDelivered"},{"from":"delivery_track","to":"delivery_track","condition":"inTransit"},{"from":"assembly_check","to":"END"}]}',
   'PCB design flow: KiCad schematic to layout to DRC to Gerber to P-Ban.com quote to order to assembly to test',
   '2026-05-14T15:00:00Z', 'rw_vertex')
"""

PHASE3_NODES_CAD = [
    ("tsukuru_cad_design_flow.v1:project_init", "tsukuru_cad_design_flow.v1", "project_init", "mcp_tool",
     "mcp://com.etzhayyim.apps.tsukuru.cadProject.create",
     '{"input_keys":["productRef","projectName","cadTool","totalParts"],"result_key":"projectVid","args":{"name":"com.etzhayyim.apps.tsukuru.cadProject.create"}}'),
    ("tsukuru_cad_design_flow.v1:part_modeling", "tsukuru_cad_design_flow.v1", "part_modeling", "mcp_tool",
     "mcp://com.etzhayyim.apps.tsukuru.cadPart.upsert",
     '{"input_keys":["projectVid","currentPartIdx","stepFiles"],"result_key":"partVid","args":{"name":"com.etzhayyim.apps.tsukuru.cadPart.upsert"},"loop_var":"currentPartIdx","loop_max":"totalParts"}'),
    ("tsukuru_cad_design_flow.v1:tolerance_review", "tsukuru_cad_design_flow.v1", "tolerance_review", "mcp_tool",
     "mcp://com.etzhayyim.tools.sql.query",
     '{"input_keys":["projectVid"],"result_key":"toleranceErrors","args":{"name":"com.etzhayyim.tools.sql.query","sql":"SELECT part_number, tolerance_class, fit_check_note FROM vertex_tsukuru_cad_part WHERE project_vid = %(project_vid)s AND tolerance_class NOT IN (\'standard\',\'h7\',\'h6\') LIMIT 50"}}'),
    ("tsukuru_cad_design_flow.v1:meviy_quote", "tsukuru_cad_design_flow.v1", "meviy_quote", "mcp_tool",
     "mcp://com.etzhayyim.apps.tsukuru.meviy.requestQuote",
     '{"input_keys":["projectVid"],"result_key":"meviyQuote","args":{"name":"com.etzhayyim.apps.tsukuru.meviy.requestQuote"}}'),
    ("tsukuru_cad_design_flow.v1:order_decision", "tsukuru_cad_design_flow.v1", "order_decision", "human_review",
     '',
     '{"prompt":"Meviy quote ready. Review line items and approve or reject the order.","input_keys":["meviyQuote"],"result_key":"orderApproved","timeout_hours":48}'),
    ("tsukuru_cad_design_flow.v1:order_submit", "tsukuru_cad_design_flow.v1", "order_submit", "mcp_tool",
     "mcp://com.etzhayyim.apps.tsukuru.productionOrder.create",
     '{"input_keys":["projectVid","meviyQuote"],"result_key":"orderId","args":{"name":"com.etzhayyim.apps.tsukuru.productionOrder.create","fulfillmentMode":"mto","vendorDid":"did:web:misumi-meviy.tsukuru.etzhayyim.com"}}'),
    ("tsukuru_cad_design_flow.v1:delivery_track", "tsukuru_cad_design_flow.v1", "delivery_track", "mcp_tool",
     "mcp://com.etzhayyim.tools.sql.query",
     '{"input_keys":["orderId"],"result_key":"deliveryStatus","args":{"name":"com.etzhayyim.tools.sql.query","sql":"SELECT status FROM vertex_tsukuru_production_order WHERE vertex_id = %(order_id)s LIMIT 1"}}'),
    ("tsukuru_cad_design_flow.v1:fit_check", "tsukuru_cad_design_flow.v1", "fit_check", "human_review",
     '',
     '{"prompt":"Parts delivered. Perform physical fit check for each part. Record pass/fail per part.","input_keys":["projectVid"],"result_key":"fitCheckResults","timeout_hours":72}'),
]

PHASE3_NODES_PCB = [
    ("tsukuru_pcb_design_flow.v1:schematic_design", "tsukuru_pcb_design_flow.v1", "schematic_design", "mcp_tool",
     "mcp://com.etzhayyim.apps.tsukuru.pcbProject.create",
     '{"input_keys":["productRef","pcbName","kicadVersion","boardSizeMm","layerCount"],"result_key":"projectVid","args":{"name":"com.etzhayyim.apps.tsukuru.pcbProject.create"}}'),
    ("tsukuru_pcb_design_flow.v1:pcb_layout", "tsukuru_pcb_design_flow.v1", "pcb_layout", "human_review",
     '',
     '{"prompt":"Complete PCB layout in KiCad. Upload .kicad_pcb blob and confirm layout is done.","input_keys":["projectVid"],"result_key":"layoutDone","timeout_hours":168}'),
    ("tsukuru_pcb_design_flow.v1:drc_check", "tsukuru_pcb_design_flow.v1", "drc_check", "mcp_tool",
     "mcp://com.etzhayyim.tools.sql.query",
     '{"input_keys":["projectVid"],"result_key":"drcErrors","args":{"name":"com.etzhayyim.tools.sql.query","sql":"SELECT drc_errors FROM vertex_tsukuru_pcb_project WHERE vertex_id = %(project_vid)s LIMIT 1"}}'),
    ("tsukuru_pcb_design_flow.v1:gerber_export", "tsukuru_pcb_design_flow.v1", "gerber_export", "human_review",
     '',
     '{"prompt":"Export Gerber files from KiCad. Upload Gerber ZIP and confirm.","input_keys":["projectVid"],"result_key":"gerberRef","timeout_hours":24}'),
    ("tsukuru_pcb_design_flow.v1:pban_quote", "tsukuru_pcb_design_flow.v1", "pban_quote", "mcp_tool",
     "mcp://com.etzhayyim.apps.tsukuru.pban.requestQuote",
     '{"input_keys":["projectVid","gerberRef"],"result_key":"pbanQuote","args":{"name":"com.etzhayyim.apps.tsukuru.pban.requestQuote","quantity":10,"needsAssembly":true}}'),
    ("tsukuru_pcb_design_flow.v1:order_decision", "tsukuru_pcb_design_flow.v1", "order_decision", "human_review",
     '',
     '{"prompt":"P-Ban.com PCB quote ready. Review fabrication and assembly cost and approve or reject.","input_keys":["pbanQuote"],"result_key":"orderApproved","timeout_hours":48}'),
    ("tsukuru_pcb_design_flow.v1:order_submit", "tsukuru_pcb_design_flow.v1", "order_submit", "mcp_tool",
     "mcp://com.etzhayyim.apps.tsukuru.productionOrder.create",
     '{"input_keys":["projectVid","pbanQuote"],"result_key":"orderId","args":{"name":"com.etzhayyim.apps.tsukuru.productionOrder.create","fulfillmentMode":"mto","vendorDid":"did:web:pban-com.tsukuru.etzhayyim.com"}}'),
    ("tsukuru_pcb_design_flow.v1:delivery_track", "tsukuru_pcb_design_flow.v1", "delivery_track", "mcp_tool",
     "mcp://com.etzhayyim.tools.sql.query",
     '{"input_keys":["orderId"],"result_key":"deliveryStatus","args":{"name":"com.etzhayyim.tools.sql.query","sql":"SELECT status FROM vertex_tsukuru_production_order WHERE vertex_id = %(order_id)s LIMIT 1"}}'),
    ("tsukuru_pcb_design_flow.v1:assembly_check", "tsukuru_pcb_design_flow.v1", "assembly_check", "human_review",
     '',
     '{"prompt":"PCB received. Perform continuity test and power-on check. Record pass/fail.","input_keys":["projectVid"],"result_key":"testResults","timeout_hours":72}'),
]


def run(conn, sql: str, label: str = ""):
    with conn.cursor() as cur:
        cur.execute(sql)
    print(f"  OK {label}")


def main():
    print(f"Connecting to RisingWave...")
    conn = psycopg2.connect(URL)
    conn.autocommit = True

    # Phase 1: tables
    print("\n── Phase 1: CREATE TABLE × 4 ──────────────────────────────────────")
    for stmt in PHASE1_TABLES:
        name = [l.strip() for l in stmt.splitlines() if l.strip().upper().startswith("CREATE")][0]
        run(conn, stmt, name[:60])
    run(conn, "FLUSH", "FLUSH")

    print("  [settle 1.5s]")
    time.sleep(1.5)

    # Phase 2: indexes
    print("\n── Phase 2: CREATE INDEX × 12 ─────────────────────────────────────")
    for stmt in PHASE2_INDEXES:
        idx_name = stmt.split("idx_")[1].split(" ")[0]
        run(conn, stmt, f"idx_{idx_name}")
    run(conn, "FLUSH", "FLUSH")

    print("  [settle 1.5s]")
    time.sleep(1.5)

    # Phase 3: MCP tool defs
    print("\n── Phase 3: INSERT vertex_mcp_tool_def × 5 ────────────────────────")
    run(conn, PHASE3_INSERTS_DELETE, "delete 5 mcp_tool_defs")
    run(conn, "FLUSH", "FLUSH")
    time.sleep(0.5)
    run(conn, PHASE3_INSERTS, "5 mcp_tool_defs")
    run(conn, "FLUSH", "FLUSH")

    # Phase 3: LangGraph assistants
    print("\n── Phase 3: INSERT vertex_langgraph_assistant × 2 ─────────────────")
    run(conn,
        "DELETE FROM vertex_langgraph_assistant WHERE vertex_id IN ('tsukuru_cad_design_flow.v1','tsukuru_pcb_design_flow.v1')",
        "delete 2 assistants")
    run(conn, "FLUSH", "FLUSH")
    time.sleep(0.5)
    run(conn, PHASE3_LG_CAD, "tsukuru_cad_design_flow.v1")
    run(conn, PHASE3_LG_PCB, "tsukuru_pcb_design_flow.v1")
    run(conn, "FLUSH", "FLUSH")

    # Phase 3: LangGraph nodes
    print("\n── Phase 3: INSERT vertex_langgraph_assistant_node × 17 ───────────")
    node_vids = [row[0] for row in PHASE3_NODES_CAD + PHASE3_NODES_PCB]
    placeholders = ",".join(["%s"] * len(node_vids))
    with conn.cursor() as cur:
        cur.execute(f"DELETE FROM vertex_langgraph_assistant_node WHERE vertex_id IN ({placeholders})", node_vids)
    print(f"  OK delete {len(node_vids)} nodes")
    run(conn, "FLUSH", "FLUSH")
    time.sleep(0.5)
    node_sql = """
INSERT INTO vertex_langgraph_assistant_node
  (vertex_id, _seq, sensitivity_ord, owner_did, assistant_id, node_id, kind, ref, config, created_at)
VALUES (%s, 0, 0, 'did:web:tsukuru.etzhayyim.com', %s, %s, %s, %s, %s, '2026-05-14T15:00:00Z')
"""
    for row in PHASE3_NODES_CAD + PHASE3_NODES_PCB:
        vid, asst_id, node_id, kind, ref, config = row
        with conn.cursor() as cur:
            cur.execute(node_sql, (vid, asst_id, node_id, kind, ref, config))
        print(f"  OK {vid}")
    run(conn, "FLUSH", "FLUSH")

    # Register in kysely_migration
    print("\n── Registering in kysely_migration ────────────────────────────────")
    run(conn,
        "DELETE FROM kysely_migration WHERE name = '20260514150000_tsukuru_cad_pcb_design_flow'",
        "delete kysely_migration entry")
    run(conn, "FLUSH", "FLUSH")
    time.sleep(0.5)
    reg_sql = """
INSERT INTO kysely_migration (name, timestamp)
VALUES ('20260514150000_tsukuru_cad_pcb_design_flow', '2026-05-14T15:00:00.000Z')
"""
    run(conn, reg_sql, "kysely_migration entry")
    run(conn, "FLUSH", "FLUSH")

    conn.close()
    print("\n✅ Migration 20260514150000_tsukuru_cad_pcb_design_flow applied successfully.")


if __name__ == "__main__":
    main()
