"""Captured from Kysely migration 20260430220000_vertex_arms_conflict_falklands."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260430220000_vertex_arms_conflict_falklands"
down_revision = 'r_20260430216400_seed_maps_collection_bpmn_actors'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_arms_conflict (\n'
         '      vertex_id             varchar PRIMARY KEY,\n'
         '      _seq                  bigint,\n'
         '      created_date          date,\n'
         '      sensitivity_ord       int,\n'
         '      owner_did             varchar,\n'
         '      canonical_name        varchar NOT NULL,\n'
         '      alternate_names       varchar,\n'
         '      conflict_kind         varchar NOT NULL,\n'
         '      start_at              varchar,\n'
         '      end_at                varchar,\n'
         '      status                varchar NOT NULL,\n'
         '      primary_location_code varchar,\n'
         '      sovereignty_issue     varchar,\n'
         '      summary               varchar,\n'
         '      source_uri            varchar,\n'
         '      created_at            varchar,\n'
         '      org_id                varchar,\n'
         '      user_id               varchar,\n'
         '      actor_id              varchar,\n'
         '      actor_did             varchar,\n'
         '      org_did               varchar\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_arms_conflict_dates ON vertex_arms_conflict (start_at, '
         'end_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_arms_conflict_location ON vertex_arms_conflict '
         '(primary_location_code)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_arms_transfer (\n'
         '      vertex_id                  varchar PRIMARY KEY,\n'
         '      _seq                       bigint,\n'
         '      created_date               date,\n'
         '      sensitivity_ord            int,\n'
         '      owner_did                  varchar,\n'
         '      transfer_kind              varchar NOT NULL,\n'
         '      supplier_actor_vid         varchar NOT NULL,\n'
         '      supplier_country_iso3      varchar NOT NULL,\n'
         '      recipient_actor_vid        varchar NOT NULL,\n'
         '      recipient_country_iso3     varchar NOT NULL,\n'
         '      equipment_name             varchar NOT NULL,\n'
         '      equipment_type             varchar NOT NULL,\n'
         '      weapon_family              varchar,\n'
         '      quantity_ordered           int,\n'
         '      quantity_delivered         int,\n'
         '      quantity_missiles_delivered int,\n'
         '      contract_at                varchar,\n'
         '      delivery_start_at          varchar,\n'
         '      delivery_end_at            varchar,\n'
         '      status                     varchar NOT NULL,\n'
         '      compliance_frame           varchar,\n'
         '      source_uri                 varchar,\n'
         '      notes                      varchar,\n'
         '      created_at                 varchar,\n'
         '      org_id                     varchar,\n'
         '      user_id                    varchar,\n'
         '      actor_id                   varchar,\n'
         '      actor_did                  varchar,\n'
         '      org_did                    varchar\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_arms_transfer_supplier_recipient ON vertex_arms_transfer '
         '(supplier_country_iso3, recipient_country_iso3)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_arms_transfer_equipment ON vertex_arms_transfer '
         '(weapon_family, equipment_type)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_arms_transfer_dates ON vertex_arms_transfer '
         '(delivery_start_at, delivery_end_at)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_arms_conflict_event (\n'
         '      vertex_id          varchar PRIMARY KEY,\n'
         '      _seq               bigint,\n'
         '      created_date       date,\n'
         '      sensitivity_ord    int,\n'
         '      owner_did          varchar,\n'
         '      conflict_vid       varchar NOT NULL,\n'
         '      occurred_at        varchar NOT NULL,\n'
         '      event_kind         varchar NOT NULL,\n'
         '      title              varchar NOT NULL,\n'
         '      primary_actor_vid  varchar,\n'
         '      opposing_actor_vid varchar,\n'
         '      location_code      varchar,\n'
         '      weapon_system      varchar,\n'
         '      outcome            varchar,\n'
         '      impact             varchar,\n'
         '      source_uri         varchar,\n'
         '      created_at         varchar,\n'
         '      org_id             varchar,\n'
         '      user_id            varchar,\n'
         '      actor_id           varchar,\n'
         '      actor_did          varchar,\n'
         '      org_did            varchar\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_arms_conflict_event_conflict_time ON '
         'vertex_arms_conflict_event (conflict_vid, occurred_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_arms_conflict_event_kind ON vertex_arms_conflict_event '
         '(event_kind, occurred_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_arms_conflict_event_actor ON vertex_arms_conflict_event '
         '(primary_actor_vid)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_arms_conflict_actor (\n'
         '      src              varchar NOT NULL,\n'
         '      dst              varchar NOT NULL,\n'
         '      rel              varchar NOT NULL,\n'
         '      side             varchar,\n'
         '      country_iso3     varchar,\n'
         '      note             varchar,\n'
         '      created_at       varchar,\n'
         '      owner_did         varchar,\n'
         '      sensitivity_ord  int,\n'
         '      org_id           varchar,\n'
         '      user_id          varchar,\n'
         '      actor_id         varchar,\n'
         '      actor_did        varchar,\n'
         '      org_did          varchar,\n'
         '      PRIMARY KEY (src, dst, rel)\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_arms_conflict_actor_dst ON edge_arms_conflict_actor (dst)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_arms_transfer_to_conflict (\n'
         '      src              varchar NOT NULL,\n'
         '      dst              varchar NOT NULL,\n'
         '      rel              varchar NOT NULL,\n'
         '      dependency_kind  varchar,\n'
         '      created_at       varchar,\n'
         '      owner_did         varchar,\n'
         '      sensitivity_ord  int,\n'
         '      org_id           varchar,\n'
         '      user_id          varchar,\n'
         '      actor_id         varchar,\n'
         '      actor_did        varchar,\n'
         '      org_did          varchar,\n'
         '      PRIMARY KEY (src, dst, rel)\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_arms_event_dependency (\n'
         '      src              varchar NOT NULL,\n'
         '      dst              varchar NOT NULL,\n'
         '      rel              varchar NOT NULL,\n'
         '      dependency_kind  varchar,\n'
         '      created_at       varchar,\n'
         '      owner_did         varchar,\n'
         '      sensitivity_ord  int,\n'
         '      org_id           varchar,\n'
         '      user_id          varchar,\n'
         '      actor_id         varchar,\n'
         '      actor_did        varchar,\n'
         '      org_did          varchar,\n'
         '      PRIMARY KEY (src, dst, rel)\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_arms_event_dependency_dst ON edge_arms_event_dependency '
         '(dst)',
  'parameters': []},
 {'sql': '\n'
         '    INSERT INTO vertex_arms_conflict (\n'
         '      vertex_id, _seq, created_date, sensitivity_ord, owner_did,\n'
         '      canonical_name, alternate_names, conflict_kind, start_at, end_at, status,\n'
         '      primary_location_code, sovereignty_issue, summary, source_uri,\n'
         '      created_at, org_id, user_id, actor_id, actor_did, org_did\n'
         '    )\n'
         '    SELECT\n'
         "      $1, NULL, CAST('2026-04-30' AS date), 1, $2,\n"
         "      'Falklands/Malvinas War 1982',\n"
         "      'Falkland Islands War; Malvinas War; South Atlantic War',\n"
         "      'interstate_territorial_war',\n"
         "      '1982-04-02',\n"
         "      '1982-06-14',\n"
         "      'ended',\n"
         "      'FK',\n"
         "      'United Kingdom sovereignty vs Argentina claim over Falkland Islands, South "
         "Georgia and South Sandwich Islands',\n"
         "      'Short undeclared 1982 war between Argentina and the United Kingdom. The "
         'arms-transfer dependency of interest is France-to-Argentina Super Etendard aircraft and '
         "AM39 Exocet missiles delivered before the war, followed by a wartime embargo.',\n"
         "      'https://www.iwm.org.uk/history/cold-war/falklands-conflict',\n"
         '      $3, $4, $5, $6, $7, $8\n'
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_arms_conflict WHERE vertex_id = $9)\n'
         '  ',
  'parameters': ['arms:conflict:falklands-malvinas-1982',
                 'did:web:arms.gftd.ai',
                 '2026-04-30T22:00:00+09:00',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'sys.schema.seed.arms.falklands',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'arms:conflict:falklands-malvinas-1982']},
 {'sql': '\n'
         '      INSERT INTO edge_arms_conflict_actor (\n'
         '        src, dst, rel, side, country_iso3, note, created_at,\n'
         '        owner_did, sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, $5, $6, $7,\n'
         '        $8, 1, $9, $10, $11, $12, $13\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM edge_arms_conflict_actor\n'
         '        WHERE src = $14 AND dst = $15 AND rel = $16\n'
         '      )\n'
         '    ',
  'parameters': ['arms:conflict:falklands-malvinas-1982',
                 'did:web:uqpel6i6.gftd.ai:geo:iso3166-1:gb',
                 'belligerent',
                 'united-kingdom',
                 'GBR',
                 'United Kingdom task force retook the Falkland Islands and South Georgia.',
                 '2026-04-30T22:00:00+09:00',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'sys.schema.seed.arms.falklands',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'arms:conflict:falklands-malvinas-1982',
                 'did:web:uqpel6i6.gftd.ai:geo:iso3166-1:gb',
                 'belligerent']},
 {'sql': '\n'
         '      INSERT INTO edge_arms_conflict_actor (\n'
         '        src, dst, rel, side, country_iso3, note, created_at,\n'
         '        owner_did, sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, $5, $6, $7,\n'
         '        $8, 1, $9, $10, $11, $12, $13\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM edge_arms_conflict_actor\n'
         '        WHERE src = $14 AND dst = $15 AND rel = $16\n'
         '      )\n'
         '    ',
  'parameters': ['arms:conflict:falklands-malvinas-1982',
                 'did:web:uqpel6i6.gftd.ai:geo:iso3166-1:ar',
                 'belligerent',
                 'argentina',
                 'ARG',
                 'Argentina invaded and occupied the islands, then surrendered on 1982-06-14.',
                 '2026-04-30T22:00:00+09:00',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'sys.schema.seed.arms.falklands',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'arms:conflict:falklands-malvinas-1982',
                 'did:web:uqpel6i6.gftd.ai:geo:iso3166-1:ar',
                 'belligerent']},
 {'sql': '\n'
         '      INSERT INTO edge_arms_conflict_actor (\n'
         '        src, dst, rel, side, country_iso3, note, created_at,\n'
         '        owner_did, sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, $5, $6, $7,\n'
         '        $8, 1, $9, $10, $11, $12, $13\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM edge_arms_conflict_actor\n'
         '        WHERE src = $14 AND dst = $15 AND rel = $16\n'
         '      )\n'
         '    ',
  'parameters': ['arms:conflict:falklands-malvinas-1982',
                 'did:web:uqpel6i6.gftd.ai:geo:iso3166-1:fr',
                 'supplier_then_embargoing_state',
                 'third-party-supplier',
                 'FRA',
                 'France supplied Super Etendard aircraft and AM39 Exocet missiles before the war, '
                 'then imposed an embargo during the conflict.',
                 '2026-04-30T22:00:00+09:00',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'sys.schema.seed.arms.falklands',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'arms:conflict:falklands-malvinas-1982',
                 'did:web:uqpel6i6.gftd.ai:geo:iso3166-1:fr',
                 'supplier_then_embargoing_state']},
 {'sql': '\n'
         '      INSERT INTO vertex_arms_transfer (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord, owner_did,\n'
         '        transfer_kind, supplier_actor_vid, supplier_country_iso3, recipient_actor_vid,\n'
         '        recipient_country_iso3, equipment_name, equipment_type, weapon_family,\n'
         '        quantity_ordered, quantity_delivered, quantity_missiles_delivered,\n'
         '        contract_at, delivery_start_at, delivery_end_at, status, compliance_frame,\n'
         '        source_uri, notes, created_at, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         "        $1, NULL, CAST('2026-04-30' AS date), 1, $2,\n"
         '        $3, $4, $5, $6,\n'
         '        $7, $8, $9, $10,\n'
         '        CAST($11 AS integer), CAST($12 AS integer), CAST($13 AS integer),\n'
         '        $14, $15, $16, $17, $18,\n'
         '        $19, $20, $21, $22, $23, $24, $25, $26\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_arms_transfer WHERE vertex_id = $27)\n'
         '    ',
  'parameters': ['arms:transfer:fra-arg-super-etendard-exocet-1981',
                 'did:web:arms.gftd.ai',
                 'prewar_export',
                 'did:web:uqpel6i6.gftd.ai:geo:iso3166-1:fr',
                 'FRA',
                 'did:web:uqpel6i6.gftd.ai:geo:iso3166-1:ar',
                 'ARG',
                 'Dassault-Breguet Super Etendard + AM39 Exocet',
                 'strike_aircraft_and_anti_ship_missile',
                 'Exocet',
                 14,
                 5,
                 5,
                 '1979',
                 '1981-08',
                 '1981-11',
                 'delivered_prewar_first_batch',
                 'prewar_contract_later_embargoed',
                 'https://www.usni.org/magazines/proceedings/1983/may/malvinas-campaign',
                 'USNI reports five aircraft and five missiles shipped from France to Argentina '
                 'between August and November 1981.',
                 '2026-04-30T22:00:00+09:00',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'sys.schema.seed.arms.falklands',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'arms:transfer:fra-arg-super-etendard-exocet-1981']},
 {'sql': '\n'
         '      INSERT INTO edge_arms_transfer_to_conflict (\n'
         '        src, dst, rel, dependency_kind, created_at,\n'
         '        owner_did, sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         "        $1, $2, 'transfer_context_for', $3, $4,\n"
         '        $5, 1, $6, $7, $8, $9, $10\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM edge_arms_transfer_to_conflict\n'
         "        WHERE src = $11 AND dst = $12 AND rel = 'transfer_context_for'\n"
         '      )\n'
         '    ',
  'parameters': ['arms:transfer:fra-arg-super-etendard-exocet-1981',
                 'arms:conflict:falklands-malvinas-1982',
                 'prewar_export',
                 '2026-04-30T22:00:00+09:00',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'sys.schema.seed.arms.falklands',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'arms:transfer:fra-arg-super-etendard-exocet-1981',
                 'arms:conflict:falklands-malvinas-1982']},
 {'sql': '\n'
         '      INSERT INTO vertex_arms_transfer (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord, owner_did,\n'
         '        transfer_kind, supplier_actor_vid, supplier_country_iso3, recipient_actor_vid,\n'
         '        recipient_country_iso3, equipment_name, equipment_type, weapon_family,\n'
         '        quantity_ordered, quantity_delivered, quantity_missiles_delivered,\n'
         '        contract_at, delivery_start_at, delivery_end_at, status, compliance_frame,\n'
         '        source_uri, notes, created_at, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         "        $1, NULL, CAST('2026-04-30' AS date), 1, $2,\n"
         '        $3, $4, $5, $6,\n'
         '        $7, $8, $9, $10,\n'
         '        CAST($11 AS integer), CAST($12 AS integer), CAST($13 AS integer),\n'
         '        $14, $15, $16, $17, $18,\n'
         '        $19, $20, $21, $22, $23, $24, $25, $26\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_arms_transfer WHERE vertex_id = $27)\n'
         '    ',
  'parameters': ['arms:transfer:fra-arg-arms-embargo-1982',
                 'did:web:arms.gftd.ai',
                 'wartime_embargo',
                 'did:web:uqpel6i6.gftd.ai:geo:iso3166-1:fr',
                 'FRA',
                 'did:web:uqpel6i6.gftd.ai:geo:iso3166-1:ar',
                 'ARG',
                 'Further Super Etendard and Exocet deliveries',
                 'arms_embargo',
                 'Exocet',
                 9,
                 0,
                 0,
                 '1979',
                 '1982-04',
                 '1982-08',
                 'halted_during_conflict',
                 'solidarity_embargo_after_invasion',
                 'https://www.upi.com/Archives/1982/11/20/French-resume-shipping-exocet-missiles-to-Argentina/8561406616400/',
                 'UPI reported France had imposed an arms-shipment embargo in solidarity with '
                 'Britain, later lifting it for old prewar contracts.',
                 '2026-04-30T22:00:00+09:00',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'sys.schema.seed.arms.falklands',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'arms:transfer:fra-arg-arms-embargo-1982']},
 {'sql': '\n'
         '      INSERT INTO edge_arms_transfer_to_conflict (\n'
         '        src, dst, rel, dependency_kind, created_at,\n'
         '        owner_did, sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         "        $1, $2, 'transfer_context_for', $3, $4,\n"
         '        $5, 1, $6, $7, $8, $9, $10\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM edge_arms_transfer_to_conflict\n'
         "        WHERE src = $11 AND dst = $12 AND rel = 'transfer_context_for'\n"
         '      )\n'
         '    ',
  'parameters': ['arms:transfer:fra-arg-arms-embargo-1982',
                 'arms:conflict:falklands-malvinas-1982',
                 'wartime_embargo',
                 '2026-04-30T22:00:00+09:00',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'sys.schema.seed.arms.falklands',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'arms:transfer:fra-arg-arms-embargo-1982',
                 'arms:conflict:falklands-malvinas-1982']},
 {'sql': '\n'
         '      INSERT INTO vertex_arms_conflict_event (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord, owner_did, conflict_vid,\n'
         '        occurred_at, event_kind, title, primary_actor_vid, opposing_actor_vid,\n'
         '        location_code, weapon_system, outcome, impact, source_uri,\n'
         '        created_at, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         "        $1, NULL, CAST('2026-04-30' AS date), 1, $2, $3,\n"
         '        $4, $5, $6, $7, $8,\n'
         '        $9, $10, $11, $12, $13,\n'
         '        $14, $15, $16, $17, $18, $19\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_arms_conflict_event WHERE vertex_id = $20)\n'
         '    ',
  'parameters': ['arms:event:falklands-1833-british-control',
                 'did:web:arms.gftd.ai',
                 'arms:conflict:falklands-malvinas-1982',
                 '1833',
                 'background_sovereignty_dispute',
                 'Britain reasserts control over the Falkland Islands',
                 'did:web:uqpel6i6.gftd.ai:geo:iso3166-1:gb',
                 'did:web:uqpel6i6.gftd.ai:geo:iso3166-1:ar',
                 'FK',
                 '',
                 'long_running_sovereignty_dispute',
                 'Argentina maintained a sovereignty claim; Britain rejected it.',
                 'https://www.britannica.com/event/Falkland-Islands-War',
                 '2026-04-30T22:00:00+09:00',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'sys.schema.seed.arms.falklands',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'arms:event:falklands-1833-british-control']},
 {'sql': '\n'
         '      INSERT INTO vertex_arms_conflict_event (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord, owner_did, conflict_vid,\n'
         '        occurred_at, event_kind, title, primary_actor_vid, opposing_actor_vid,\n'
         '        location_code, weapon_system, outcome, impact, source_uri,\n'
         '        created_at, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         "        $1, NULL, CAST('2026-04-30' AS date), 1, $2, $3,\n"
         '        $4, $5, $6, $7, $8,\n'
         '        $9, $10, $11, $12, $13,\n'
         '        $14, $15, $16, $17, $18, $19\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_arms_conflict_event WHERE vertex_id = $20)\n'
         '    ',
  'parameters': ['arms:event:falklands-1976-south-sandwich-presence',
                 'did:web:arms.gftd.ai',
                 'arms:conflict:falklands-malvinas-1982',
                 '1976',
                 'background_presence',
                 'Argentina establishes an unauthorized presence in the South Sandwich Islands',
                 'did:web:uqpel6i6.gftd.ai:geo:iso3166-1:ar',
                 'did:web:uqpel6i6.gftd.ai:geo:iso3166-1:gb',
                 'GS',
                 '',
                 'unopposed_presence',
                 'Prewar friction over associated South Atlantic dependencies increased.',
                 'https://www.iwm.org.uk/history/cold-war/falklands-conflict',
                 '2026-04-30T22:00:00+09:00',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'sys.schema.seed.arms.falklands',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'arms:event:falklands-1976-south-sandwich-presence']},
 {'sql': '\n'
         '      INSERT INTO vertex_arms_conflict_event (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord, owner_did, conflict_vid,\n'
         '        occurred_at, event_kind, title, primary_actor_vid, opposing_actor_vid,\n'
         '        location_code, weapon_system, outcome, impact, source_uri,\n'
         '        created_at, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         "        $1, NULL, CAST('2026-04-30' AS date), 1, $2, $3,\n"
         '        $4, $5, $6, $7, $8,\n'
         '        $9, $10, $11, $12, $13,\n'
         '        $14, $15, $16, $17, $18, $19\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_arms_conflict_event WHERE vertex_id = $20)\n'
         '    ',
  'parameters': ['arms:event:falklands-1981-france-delivery',
                 'did:web:arms.gftd.ai',
                 'arms:conflict:falklands-malvinas-1982',
                 '1981-11',
                 'arms_delivery',
                 'France delivers first Super Etendard and Exocet batch to Argentina',
                 'did:web:uqpel6i6.gftd.ai:geo:iso3166-1:fr',
                 '',
                 'AR',
                 'Super Etendard; AM39 Exocet',
                 'argentine_naval_air_strike_capability',
                 'Argentina entered the conflict with a small but high-leverage anti-ship missile '
                 'capability.',
                 'https://www.usni.org/magazines/proceedings/1983/may/malvinas-campaign',
                 '2026-04-30T22:00:00+09:00',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'sys.schema.seed.arms.falklands',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'arms:event:falklands-1981-france-delivery']},
 {'sql': '\n'
         '      INSERT INTO vertex_arms_conflict_event (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord, owner_did, conflict_vid,\n'
         '        occurred_at, event_kind, title, primary_actor_vid, opposing_actor_vid,\n'
         '        location_code, weapon_system, outcome, impact, source_uri,\n'
         '        created_at, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         "        $1, NULL, CAST('2026-04-30' AS date), 1, $2, $3,\n"
         '        $4, $5, $6, $7, $8,\n'
         '        $9, $10, $11, $12, $13,\n'
         '        $14, $15, $16, $17, $18, $19\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_arms_conflict_event WHERE vertex_id = $20)\n'
         '    ',
  'parameters': ['arms:event:falklands-1982-03-19-south-georgia',
                 'did:web:arms.gftd.ai',
                 'arms:conflict:falklands-malvinas-1982',
                 '1982-03-19',
                 'trigger_dispute',
                 'South Georgia flag incident accelerates crisis timetable',
                 'did:web:uqpel6i6.gftd.ai:geo:iso3166-1:ar',
                 'did:web:uqpel6i6.gftd.ai:geo:iso3166-1:gb',
                 'GS',
                 '',
                 'naval_mobilization',
                 'The incident shortened the timetable before the Argentine invasion.',
                 'https://www.britannica.com/event/Falkland-Islands-War',
                 '2026-04-30T22:00:00+09:00',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'sys.schema.seed.arms.falklands',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'arms:event:falklands-1982-03-19-south-georgia']},
 {'sql': '\n'
         '      INSERT INTO vertex_arms_conflict_event (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord, owner_did, conflict_vid,\n'
         '        occurred_at, event_kind, title, primary_actor_vid, opposing_actor_vid,\n'
         '        location_code, weapon_system, outcome, impact, source_uri,\n'
         '        created_at, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         "        $1, NULL, CAST('2026-04-30' AS date), 1, $2, $3,\n"
         '        $4, $5, $6, $7, $8,\n'
         '        $9, $10, $11, $12, $13,\n'
         '        $14, $15, $16, $17, $18, $19\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_arms_conflict_event WHERE vertex_id = $20)\n'
         '    ',
  'parameters': ['arms:event:falklands-1982-04-02-invasion',
                 'did:web:arms.gftd.ai',
                 'arms:conflict:falklands-malvinas-1982',
                 '1982-04-02',
                 'invasion',
                 'Argentina invades the Falkland Islands',
                 'did:web:uqpel6i6.gftd.ai:geo:iso3166-1:ar',
                 'did:web:uqpel6i6.gftd.ai:geo:iso3166-1:gb',
                 'FK',
                 'amphibious_force',
                 'argentine_occupation',
                 'The invasion started the 74-day war.',
                 'https://www.iwm.org.uk/history/cold-war/falklands-conflict',
                 '2026-04-30T22:00:00+09:00',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'sys.schema.seed.arms.falklands',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'arms:event:falklands-1982-04-02-invasion']},
 {'sql': '\n'
         '      INSERT INTO vertex_arms_conflict_event (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord, owner_did, conflict_vid,\n'
         '        occurred_at, event_kind, title, primary_actor_vid, opposing_actor_vid,\n'
         '        location_code, weapon_system, outcome, impact, source_uri,\n'
         '        created_at, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         "        $1, NULL, CAST('2026-04-30' AS date), 1, $2, $3,\n"
         '        $4, $5, $6, $7, $8,\n'
         '        $9, $10, $11, $12, $13,\n'
         '        $14, $15, $16, $17, $18, $19\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_arms_conflict_event WHERE vertex_id = $20)\n'
         '    ',
  'parameters': ['arms:event:falklands-1982-04-03-south-georgia',
                 'did:web:arms.gftd.ai',
                 'arms:conflict:falklands-malvinas-1982',
                 '1982-04-03',
                 'occupation_expands',
                 'Argentina occupies South Georgia',
                 'did:web:uqpel6i6.gftd.ai:geo:iso3166-1:ar',
                 'did:web:uqpel6i6.gftd.ai:geo:iso3166-1:gb',
                 'GS',
                 'naval_infantry',
                 'argentine_occupation',
                 'The conflict extended to associated South Atlantic dependencies.',
                 'https://www.iwm.org.uk/history/cold-war/falklands-conflict',
                 '2026-04-30T22:00:00+09:00',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'sys.schema.seed.arms.falklands',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'arms:event:falklands-1982-04-03-south-georgia']},
 {'sql': '\n'
         '      INSERT INTO vertex_arms_conflict_event (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord, owner_did, conflict_vid,\n'
         '        occurred_at, event_kind, title, primary_actor_vid, opposing_actor_vid,\n'
         '        location_code, weapon_system, outcome, impact, source_uri,\n'
         '        created_at, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         "        $1, NULL, CAST('2026-04-30' AS date), 1, $2, $3,\n"
         '        $4, $5, $6, $7, $8,\n'
         '        $9, $10, $11, $12, $13,\n'
         '        $14, $15, $16, $17, $18, $19\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_arms_conflict_event WHERE vertex_id = $20)\n'
         '    ',
  'parameters': ['arms:event:falklands-1982-04-05-task-force',
                 'did:web:arms.gftd.ai',
                 'arms:conflict:falklands-malvinas-1982',
                 '1982-04-05',
                 'task_force_deployment',
                 'British carrier task force sails south',
                 'did:web:uqpel6i6.gftd.ai:geo:iso3166-1:gb',
                 'did:web:uqpel6i6.gftd.ai:geo:iso3166-1:ar',
                 'GB',
                 'naval_task_force',
                 'operation_corporate',
                 'Britain committed naval, air, and ground forces to retake the islands.',
                 'https://www.britannica.com/event/Falkland-Islands-War',
                 '2026-04-30T22:00:00+09:00',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'sys.schema.seed.arms.falklands',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'arms:event:falklands-1982-04-05-task-force']},
 {'sql': '\n'
         '      INSERT INTO vertex_arms_conflict_event (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord, owner_did, conflict_vid,\n'
         '        occurred_at, event_kind, title, primary_actor_vid, opposing_actor_vid,\n'
         '        location_code, weapon_system, outcome, impact, source_uri,\n'
         '        created_at, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         "        $1, NULL, CAST('2026-04-30' AS date), 1, $2, $3,\n"
         '        $4, $5, $6, $7, $8,\n'
         '        $9, $10, $11, $12, $13,\n'
         '        $14, $15, $16, $17, $18, $19\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_arms_conflict_event WHERE vertex_id = $20)\n'
         '    ',
  'parameters': ['arms:event:falklands-1982-04-france-embargo',
                 'did:web:arms.gftd.ai',
                 'arms:conflict:falklands-malvinas-1982',
                 '1982-04',
                 'export_control',
                 'France halts further arms shipments to Argentina during conflict',
                 'did:web:uqpel6i6.gftd.ai:geo:iso3166-1:fr',
                 '',
                 'FR',
                 'Super Etendard; AM39 Exocet',
                 'remaining_deliveries_halted',
                 'Argentina fought with only the already delivered first batch of the French '
                 'aircraft-missile system.',
                 'https://www.upi.com/Archives/1982/11/20/French-resume-shipping-exocet-missiles-to-Argentina/8561406616400/',
                 '2026-04-30T22:00:00+09:00',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'sys.schema.seed.arms.falklands',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'arms:event:falklands-1982-04-france-embargo']},
 {'sql': '\n'
         '      INSERT INTO vertex_arms_conflict_event (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord, owner_did, conflict_vid,\n'
         '        occurred_at, event_kind, title, primary_actor_vid, opposing_actor_vid,\n'
         '        location_code, weapon_system, outcome, impact, source_uri,\n'
         '        created_at, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         "        $1, NULL, CAST('2026-04-30' AS date), 1, $2, $3,\n"
         '        $4, $5, $6, $7, $8,\n'
         '        $9, $10, $11, $12, $13,\n'
         '        $14, $15, $16, $17, $18, $19\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_arms_conflict_event WHERE vertex_id = $20)\n'
         '    ',
  'parameters': ['arms:event:falklands-1982-04-25-south-georgia-retaken',
                 'did:web:arms.gftd.ai',
                 'arms:conflict:falklands-malvinas-1982',
                 '1982-04-25',
                 'recapture',
                 'Operation Paraquet returns South Georgia to British control',
                 'did:web:uqpel6i6.gftd.ai:geo:iso3166-1:gb',
                 'did:web:uqpel6i6.gftd.ai:geo:iso3166-1:ar',
                 'GS',
                 'naval_task_force',
                 'british_control_restored',
                 'Argentine forces in South Georgia surrendered before the main Falklands land '
                 'campaign.',
                 'https://www.iwm.org.uk/history/cold-war/falklands-conflict',
                 '2026-04-30T22:00:00+09:00',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'sys.schema.seed.arms.falklands',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'arms:event:falklands-1982-04-25-south-georgia-retaken']},
 {'sql': '\n'
         '      INSERT INTO vertex_arms_conflict_event (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord, owner_did, conflict_vid,\n'
         '        occurred_at, event_kind, title, primary_actor_vid, opposing_actor_vid,\n'
         '        location_code, weapon_system, outcome, impact, source_uri,\n'
         '        created_at, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         "        $1, NULL, CAST('2026-04-30' AS date), 1, $2, $3,\n"
         '        $4, $5, $6, $7, $8,\n'
         '        $9, $10, $11, $12, $13,\n'
         '        $14, $15, $16, $17, $18, $19\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_arms_conflict_event WHERE vertex_id = $20)\n'
         '    ',
  'parameters': ['arms:event:falklands-1982-04-30-exclusion-zone',
                 'did:web:arms.gftd.ai',
                 'arms:conflict:falklands-malvinas-1982',
                 '1982-04-30',
                 'maritime_exclusion_zone',
                 'Britain imposes a 200-mile Total Exclusion Zone',
                 'did:web:uqpel6i6.gftd.ai:geo:iso3166-1:gb',
                 'did:web:uqpel6i6.gftd.ai:geo:iso3166-1:ar',
                 'FK',
                 'naval_blockade',
                 'exclusion_zone_active',
                 'The maritime and air operating environment around the islands changed.',
                 'https://www.iwm.org.uk/history/cold-war/falklands-conflict',
                 '2026-04-30T22:00:00+09:00',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'sys.schema.seed.arms.falklands',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'arms:event:falklands-1982-04-30-exclusion-zone']},
 {'sql': '\n'
         '      INSERT INTO vertex_arms_conflict_event (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord, owner_did, conflict_vid,\n'
         '        occurred_at, event_kind, title, primary_actor_vid, opposing_actor_vid,\n'
         '        location_code, weapon_system, outcome, impact, source_uri,\n'
         '        created_at, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         "        $1, NULL, CAST('2026-04-30' AS date), 1, $2, $3,\n"
         '        $4, $5, $6, $7, $8,\n'
         '        $9, $10, $11, $12, $13,\n'
         '        $14, $15, $16, $17, $18, $19\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_arms_conflict_event WHERE vertex_id = $20)\n'
         '    ',
  'parameters': ['arms:event:falklands-1982-05-02-belgrano',
                 'did:web:arms.gftd.ai',
                 'arms:conflict:falklands-malvinas-1982',
                 '1982-05-02',
                 'naval_sinking',
                 'HMS Conqueror sinks ARA General Belgrano',
                 'did:web:uqpel6i6.gftd.ai:geo:iso3166-1:gb',
                 'did:web:uqpel6i6.gftd.ai:geo:iso3166-1:ar',
                 'FK',
                 'submarine_torpedo',
                 'argentine_cruiser_sunk',
                 'More than 300 Argentine crew were lost and naval escalation sharpened.',
                 'https://www.iwm.org.uk/history/cold-war/falklands-conflict',
                 '2026-04-30T22:00:00+09:00',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'sys.schema.seed.arms.falklands',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'arms:event:falklands-1982-05-02-belgrano']},
 {'sql': '\n'
         '      INSERT INTO vertex_arms_conflict_event (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord, owner_did, conflict_vid,\n'
         '        occurred_at, event_kind, title, primary_actor_vid, opposing_actor_vid,\n'
         '        location_code, weapon_system, outcome, impact, source_uri,\n'
         '        created_at, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         "        $1, NULL, CAST('2026-04-30' AS date), 1, $2, $3,\n"
         '        $4, $5, $6, $7, $8,\n'
         '        $9, $10, $11, $12, $13,\n'
         '        $14, $15, $16, $17, $18, $19\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_arms_conflict_event WHERE vertex_id = $20)\n'
         '    ',
  'parameters': ['arms:event:falklands-1982-05-04-sheffield-exocet',
                 'did:web:arms.gftd.ai',
                 'arms:conflict:falklands-malvinas-1982',
                 '1982-05-04',
                 'missile_strike',
                 'AM39 Exocet strike destroys HMS Sheffield',
                 'did:web:uqpel6i6.gftd.ai:geo:iso3166-1:ar',
                 'did:web:uqpel6i6.gftd.ai:geo:iso3166-1:gb',
                 'FK',
                 'Super Etendard; AM39 Exocet',
                 'hms_sheffield_destroyed',
                 'The French-origin aircraft-missile dependency became operationally decisive; 20 '
                 'were killed.',
                 'https://www.iwm.org.uk/history/cold-war/falklands-conflict',
                 '2026-04-30T22:00:00+09:00',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'sys.schema.seed.arms.falklands',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'arms:event:falklands-1982-05-04-sheffield-exocet']},
 {'sql': '\n'
         '      INSERT INTO vertex_arms_conflict_event (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord, owner_did, conflict_vid,\n'
         '        occurred_at, event_kind, title, primary_actor_vid, opposing_actor_vid,\n'
         '        location_code, weapon_system, outcome, impact, source_uri,\n'
         '        created_at, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         "        $1, NULL, CAST('2026-04-30' AS date), 1, $2, $3,\n"
         '        $4, $5, $6, $7, $8,\n'
         '        $9, $10, $11, $12, $13,\n'
         '        $14, $15, $16, $17, $18, $19\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_arms_conflict_event WHERE vertex_id = $20)\n'
         '    ',
  'parameters': ['arms:event:falklands-1982-05-21-san-carlos',
                 'did:web:arms.gftd.ai',
                 'arms:conflict:falklands-malvinas-1982',
                 '1982-05-21',
                 'amphibious_landing',
                 'British troops land at San Carlos and Ajax Bay',
                 'did:web:uqpel6i6.gftd.ai:geo:iso3166-1:gb',
                 'did:web:uqpel6i6.gftd.ai:geo:iso3166-1:ar',
                 'FK',
                 'amphibious_landing_force',
                 'bridgehead_established',
                 'The land campaign on East Falkland began.',
                 'https://www.iwm.org.uk/history/cold-war/falklands-conflict',
                 '2026-04-30T22:00:00+09:00',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'sys.schema.seed.arms.falklands',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'arms:event:falklands-1982-05-21-san-carlos']},
 {'sql': '\n'
         '      INSERT INTO vertex_arms_conflict_event (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord, owner_did, conflict_vid,\n'
         '        occurred_at, event_kind, title, primary_actor_vid, opposing_actor_vid,\n'
         '        location_code, weapon_system, outcome, impact, source_uri,\n'
         '        created_at, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         "        $1, NULL, CAST('2026-04-30' AS date), 1, $2, $3,\n"
         '        $4, $5, $6, $7, $8,\n'
         '        $9, $10, $11, $12, $13,\n'
         '        $14, $15, $16, $17, $18, $19\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_arms_conflict_event WHERE vertex_id = $20)\n'
         '    ',
  'parameters': ['arms:event:falklands-1982-05-25-atlantic-conveyor-exocet',
                 'did:web:arms.gftd.ai',
                 'arms:conflict:falklands-malvinas-1982',
                 '1982-05-25',
                 'missile_strike',
                 'Exocet strike hits SS Atlantic Conveyor',
                 'did:web:uqpel6i6.gftd.ai:geo:iso3166-1:ar',
                 'did:web:uqpel6i6.gftd.ai:geo:iso3166-1:gb',
                 'FK',
                 'Super Etendard; AM39 Exocet',
                 'atlantic_conveyor_lost',
                 'Loss of transport and helicopter capacity affected the British advance.',
                 'https://www.iwm.org.uk/history/cold-war/falklands-conflict',
                 '2026-04-30T22:00:00+09:00',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'sys.schema.seed.arms.falklands',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'arms:event:falklands-1982-05-25-atlantic-conveyor-exocet']},
 {'sql': '\n'
         '      INSERT INTO vertex_arms_conflict_event (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord, owner_did, conflict_vid,\n'
         '        occurred_at, event_kind, title, primary_actor_vid, opposing_actor_vid,\n'
         '        location_code, weapon_system, outcome, impact, source_uri,\n'
         '        created_at, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         "        $1, NULL, CAST('2026-04-30' AS date), 1, $2, $3,\n"
         '        $4, $5, $6, $7, $8,\n'
         '        $9, $10, $11, $12, $13,\n'
         '        $14, $15, $16, $17, $18, $19\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_arms_conflict_event WHERE vertex_id = $20)\n'
         '    ',
  'parameters': ['arms:event:falklands-1982-05-29-goose-green',
                 'did:web:arms.gftd.ai',
                 'arms:conflict:falklands-malvinas-1982',
                 '1982-05-29',
                 'land_battle',
                 'British forces take Goose Green',
                 'did:web:uqpel6i6.gftd.ai:geo:iso3166-1:gb',
                 'did:web:uqpel6i6.gftd.ai:geo:iso3166-1:ar',
                 'FK',
                 'infantry',
                 'british_capture',
                 'First settlement captured by British ground forces.',
                 'https://www.iwm.org.uk/history/cold-war/falklands-conflict',
                 '2026-04-30T22:00:00+09:00',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'sys.schema.seed.arms.falklands',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'arms:event:falklands-1982-05-29-goose-green']},
 {'sql': '\n'
         '      INSERT INTO vertex_arms_conflict_event (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord, owner_did, conflict_vid,\n'
         '        occurred_at, event_kind, title, primary_actor_vid, opposing_actor_vid,\n'
         '        location_code, weapon_system, outcome, impact, source_uri,\n'
         '        created_at, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         "        $1, NULL, CAST('2026-04-30' AS date), 1, $2, $3,\n"
         '        $4, $5, $6, $7, $8,\n'
         '        $9, $10, $11, $12, $13,\n'
         '        $14, $15, $16, $17, $18, $19\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_arms_conflict_event WHERE vertex_id = $20)\n'
         '    ',
  'parameters': ['arms:event:falklands-1982-06-14-surrender',
                 'did:web:arms.gftd.ai',
                 'arms:conflict:falklands-malvinas-1982',
                 '1982-06-14',
                 'surrender',
                 'Argentine forces surrender in the Falkland Islands',
                 'did:web:uqpel6i6.gftd.ai:geo:iso3166-1:ar',
                 'did:web:uqpel6i6.gftd.ai:geo:iso3166-1:gb',
                 'FK',
                 '',
                 'british_control_restored',
                 'The 74-day war ended with the Falklands back under British control.',
                 'https://www.iwm.org.uk/history/cold-war/falklands-conflict',
                 '2026-04-30T22:00:00+09:00',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'sys.schema.seed.arms.falklands',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'arms:event:falklands-1982-06-14-surrender']},
 {'sql': '\n'
         '      INSERT INTO edge_arms_event_dependency (\n'
         '        src, dst, rel, dependency_kind, created_at,\n'
         '        owner_did, sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         "        $1, $2, 'precedes_enables_or_constrains', $3, $4,\n"
         '        $5, 1, $6, $7, $8, $9, $10\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM edge_arms_event_dependency\n'
         "        WHERE src = $11 AND dst = $12 AND rel = 'precedes_enables_or_constrains'\n"
         '      )\n'
         '    ',
  'parameters': ['arms:event:falklands-1833-british-control',
                 'arms:event:falklands-1982-04-02-invasion',
                 'sovereignty_claim_background',
                 '2026-04-30T22:00:00+09:00',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'sys.schema.seed.arms.falklands',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'arms:event:falklands-1833-british-control',
                 'arms:event:falklands-1982-04-02-invasion']},
 {'sql': '\n'
         '      INSERT INTO edge_arms_event_dependency (\n'
         '        src, dst, rel, dependency_kind, created_at,\n'
         '        owner_did, sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         "        $1, $2, 'precedes_enables_or_constrains', $3, $4,\n"
         '        $5, 1, $6, $7, $8, $9, $10\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM edge_arms_event_dependency\n'
         "        WHERE src = $11 AND dst = $12 AND rel = 'precedes_enables_or_constrains'\n"
         '      )\n'
         '    ',
  'parameters': ['arms:event:falklands-1976-south-sandwich-presence',
                 'arms:event:falklands-1982-04-03-south-georgia',
                 'dependency_dispute_background',
                 '2026-04-30T22:00:00+09:00',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'sys.schema.seed.arms.falklands',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'arms:event:falklands-1976-south-sandwich-presence',
                 'arms:event:falklands-1982-04-03-south-georgia']},
 {'sql': '\n'
         '      INSERT INTO edge_arms_event_dependency (\n'
         '        src, dst, rel, dependency_kind, created_at,\n'
         '        owner_did, sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         "        $1, $2, 'precedes_enables_or_constrains', $3, $4,\n"
         '        $5, 1, $6, $7, $8, $9, $10\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM edge_arms_event_dependency\n'
         "        WHERE src = $11 AND dst = $12 AND rel = 'precedes_enables_or_constrains'\n"
         '      )\n'
         '    ',
  'parameters': ['arms:event:falklands-1981-france-delivery',
                 'arms:event:falklands-1982-05-04-sheffield-exocet',
                 'weapon_system_enabled',
                 '2026-04-30T22:00:00+09:00',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'sys.schema.seed.arms.falklands',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'arms:event:falklands-1981-france-delivery',
                 'arms:event:falklands-1982-05-04-sheffield-exocet']},
 {'sql': '\n'
         '      INSERT INTO edge_arms_event_dependency (\n'
         '        src, dst, rel, dependency_kind, created_at,\n'
         '        owner_did, sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         "        $1, $2, 'precedes_enables_or_constrains', $3, $4,\n"
         '        $5, 1, $6, $7, $8, $9, $10\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM edge_arms_event_dependency\n'
         "        WHERE src = $11 AND dst = $12 AND rel = 'precedes_enables_or_constrains'\n"
         '      )\n'
         '    ',
  'parameters': ['arms:event:falklands-1981-france-delivery',
                 'arms:event:falklands-1982-05-25-atlantic-conveyor-exocet',
                 'weapon_system_enabled',
                 '2026-04-30T22:00:00+09:00',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'sys.schema.seed.arms.falklands',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'arms:event:falklands-1981-france-delivery',
                 'arms:event:falklands-1982-05-25-atlantic-conveyor-exocet']},
 {'sql': '\n'
         '      INSERT INTO edge_arms_event_dependency (\n'
         '        src, dst, rel, dependency_kind, created_at,\n'
         '        owner_did, sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         "        $1, $2, 'precedes_enables_or_constrains', $3, $4,\n"
         '        $5, 1, $6, $7, $8, $9, $10\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM edge_arms_event_dependency\n'
         "        WHERE src = $11 AND dst = $12 AND rel = 'precedes_enables_or_constrains'\n"
         '      )\n'
         '    ',
  'parameters': ['arms:event:falklands-1982-03-19-south-georgia',
                 'arms:event:falklands-1982-04-02-invasion',
                 'crisis_accelerator',
                 '2026-04-30T22:00:00+09:00',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'sys.schema.seed.arms.falklands',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'arms:event:falklands-1982-03-19-south-georgia',
                 'arms:event:falklands-1982-04-02-invasion']},
 {'sql': '\n'
         '      INSERT INTO edge_arms_event_dependency (\n'
         '        src, dst, rel, dependency_kind, created_at,\n'
         '        owner_did, sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         "        $1, $2, 'precedes_enables_or_constrains', $3, $4,\n"
         '        $5, 1, $6, $7, $8, $9, $10\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM edge_arms_event_dependency\n'
         "        WHERE src = $11 AND dst = $12 AND rel = 'precedes_enables_or_constrains'\n"
         '      )\n'
         '    ',
  'parameters': ['arms:event:falklands-1982-04-02-invasion',
                 'arms:event:falklands-1982-04-05-task-force',
                 'military_response',
                 '2026-04-30T22:00:00+09:00',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'sys.schema.seed.arms.falklands',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'arms:event:falklands-1982-04-02-invasion',
                 'arms:event:falklands-1982-04-05-task-force']},
 {'sql': '\n'
         '      INSERT INTO edge_arms_event_dependency (\n'
         '        src, dst, rel, dependency_kind, created_at,\n'
         '        owner_did, sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         "        $1, $2, 'precedes_enables_or_constrains', $3, $4,\n"
         '        $5, 1, $6, $7, $8, $9, $10\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM edge_arms_event_dependency\n'
         "        WHERE src = $11 AND dst = $12 AND rel = 'precedes_enables_or_constrains'\n"
         '      )\n'
         '    ',
  'parameters': ['arms:event:falklands-1982-04-05-task-force',
                 'arms:event:falklands-1982-04-30-exclusion-zone',
                 'operational_precondition',
                 '2026-04-30T22:00:00+09:00',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'sys.schema.seed.arms.falklands',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'arms:event:falklands-1982-04-05-task-force',
                 'arms:event:falklands-1982-04-30-exclusion-zone']},
 {'sql': '\n'
         '      INSERT INTO edge_arms_event_dependency (\n'
         '        src, dst, rel, dependency_kind, created_at,\n'
         '        owner_did, sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         "        $1, $2, 'precedes_enables_or_constrains', $3, $4,\n"
         '        $5, 1, $6, $7, $8, $9, $10\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM edge_arms_event_dependency\n'
         "        WHERE src = $11 AND dst = $12 AND rel = 'precedes_enables_or_constrains'\n"
         '      )\n'
         '    ',
  'parameters': ['arms:event:falklands-1982-04-30-exclusion-zone',
                 'arms:event:falklands-1982-05-02-belgrano',
                 'operational_context',
                 '2026-04-30T22:00:00+09:00',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'sys.schema.seed.arms.falklands',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'arms:event:falklands-1982-04-30-exclusion-zone',
                 'arms:event:falklands-1982-05-02-belgrano']},
 {'sql': '\n'
         '      INSERT INTO edge_arms_event_dependency (\n'
         '        src, dst, rel, dependency_kind, created_at,\n'
         '        owner_did, sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         "        $1, $2, 'precedes_enables_or_constrains', $3, $4,\n"
         '        $5, 1, $6, $7, $8, $9, $10\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM edge_arms_event_dependency\n'
         "        WHERE src = $11 AND dst = $12 AND rel = 'precedes_enables_or_constrains'\n"
         '      )\n'
         '    ',
  'parameters': ['arms:event:falklands-1982-05-04-sheffield-exocet',
                 'arms:event:falklands-1982-05-21-san-carlos',
                 'threat_environment',
                 '2026-04-30T22:00:00+09:00',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'sys.schema.seed.arms.falklands',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'arms:event:falklands-1982-05-04-sheffield-exocet',
                 'arms:event:falklands-1982-05-21-san-carlos']},
 {'sql': '\n'
         '      INSERT INTO edge_arms_event_dependency (\n'
         '        src, dst, rel, dependency_kind, created_at,\n'
         '        owner_did, sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         "        $1, $2, 'precedes_enables_or_constrains', $3, $4,\n"
         '        $5, 1, $6, $7, $8, $9, $10\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM edge_arms_event_dependency\n'
         "        WHERE src = $11 AND dst = $12 AND rel = 'precedes_enables_or_constrains'\n"
         '      )\n'
         '    ',
  'parameters': ['arms:event:falklands-1982-05-21-san-carlos',
                 'arms:event:falklands-1982-05-29-goose-green',
                 'campaign_sequence',
                 '2026-04-30T22:00:00+09:00',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'sys.schema.seed.arms.falklands',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'arms:event:falklands-1982-05-21-san-carlos',
                 'arms:event:falklands-1982-05-29-goose-green']},
 {'sql': '\n'
         '      INSERT INTO edge_arms_event_dependency (\n'
         '        src, dst, rel, dependency_kind, created_at,\n'
         '        owner_did, sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         "        $1, $2, 'precedes_enables_or_constrains', $3, $4,\n"
         '        $5, 1, $6, $7, $8, $9, $10\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM edge_arms_event_dependency\n'
         "        WHERE src = $11 AND dst = $12 AND rel = 'precedes_enables_or_constrains'\n"
         '      )\n'
         '    ',
  'parameters': ['arms:event:falklands-1982-05-25-atlantic-conveyor-exocet',
                 'arms:event:falklands-1982-06-14-surrender',
                 'logistics_constraint',
                 '2026-04-30T22:00:00+09:00',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'sys.schema.seed.arms.falklands',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'arms:event:falklands-1982-05-25-atlantic-conveyor-exocet',
                 'arms:event:falklands-1982-06-14-surrender']},
 {'sql': '\n'
         '      INSERT INTO edge_arms_event_dependency (\n'
         '        src, dst, rel, dependency_kind, created_at,\n'
         '        owner_did, sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         "        $1, $2, 'precedes_enables_or_constrains', $3, $4,\n"
         '        $5, 1, $6, $7, $8, $9, $10\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM edge_arms_event_dependency\n'
         "        WHERE src = $11 AND dst = $12 AND rel = 'precedes_enables_or_constrains'\n"
         '      )\n'
         '    ',
  'parameters': ['arms:event:falklands-1982-05-29-goose-green',
                 'arms:event:falklands-1982-06-14-surrender',
                 'campaign_sequence',
                 '2026-04-30T22:00:00+09:00',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'sys.schema.seed.arms.falklands',
                 'did:web:arms.gftd.ai',
                 'did:web:arms.gftd.ai',
                 'arms:event:falklands-1982-05-29-goose-green',
                 'arms:event:falklands-1982-06-14-surrender']},
 {'sql': 'FLUSH', 'parameters': []}]

DOWN = [{'sql': 'DROP TABLE IF EXISTS edge_arms_event_dependency', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_arms_transfer_to_conflict', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_arms_conflict_actor', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_arms_conflict_event', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_arms_transfer', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_arms_conflict', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
