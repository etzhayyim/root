"""Captured from Kysely migration 20260428330000_edge_person_cohort_cross_domain."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260428330000_edge_person_cohort_cross_domain"
down_revision = 'r_20260428320000_vertex_person_population_cohort'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_cohort_belief_system (\n'
         '      edge_id VARCHAR PRIMARY KEY,\n'
         '      src_vid VARCHAR,\n'
         '      dst_vid VARCHAR,\n'
         '      _seq BIGINT,\n'
         '      created_date DATE,\n'
         '      sensitivity_ord BIGINT DEFAULT 0,\n'
         '      owner_did VARCHAR,\n'
         '      adherent_fraction DOUBLE PRECISION,\n'
         '      dominance_rank INTEGER,\n'
         '      actor_did VARCHAR,\n'
         '      org_did VARCHAR,\n'
         '      at_did VARCHAR,\n'
         '      created_at VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_edge_cohort_belief_src\n'
         '    ON edge_cohort_belief_system (src_vid)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_edge_cohort_belief_dst\n'
         '    ON edge_cohort_belief_system (dst_vid)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_belief_system (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, sensitivity_ord, owner_did,\n'
         '        adherent_fraction, dominance_rank,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', 0, $4,\n"
         '        $5, $6,\n'
         '        $7, $8, null, $9\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.cohortBeliefSystem/bel-early_paleolithic-secular',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/early_paleolithic-001-100000',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.beliefSystem/secular',
                 'did:web:natural-person.gftd.ai',
                 1,
                 1,
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_belief_system (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, sensitivity_ord, owner_did,\n'
         '        adherent_fraction, dominance_rank,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', 0, $4,\n"
         '        $5, $6,\n'
         '        $7, $8, null, $9\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.cohortBeliefSystem/bel-toba_bottleneck-secular',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/toba_bottleneck-001-74000',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.beliefSystem/secular',
                 'did:web:natural-person.gftd.ai',
                 1,
                 1,
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_belief_system (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, sensitivity_ord, owner_did,\n'
         '        adherent_fraction, dominance_rank,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', 0, $4,\n"
         '        $5, $6,\n'
         '        $7, $8, null, $9\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.cohortBeliefSystem/bel-upper_paleolithic-secular',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/upper_paleolithic-001-70000',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.beliefSystem/secular',
                 'did:web:natural-person.gftd.ai',
                 1,
                 1,
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_belief_system (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, sensitivity_ord, owner_did,\n'
         '        adherent_fraction, dominance_rank,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', 0, $4,\n"
         '        $5, $6,\n'
         '        $7, $8, null, $9\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.cohortBeliefSystem/bel-neolithic-secular',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/neolithic-001-10000',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.beliefSystem/secular',
                 'did:web:natural-person.gftd.ai',
                 0.9,
                 1,
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_belief_system (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, sensitivity_ord, owner_did,\n'
         '        adherent_fraction, dominance_rank,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', 0, $4,\n"
         '        $5, $6,\n'
         '        $7, $8, null, $9\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.cohortBeliefSystem/bel-neolithic-dharma',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/neolithic-001-10000',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.beliefSystem/dharma',
                 'did:web:natural-person.gftd.ai',
                 0.05,
                 2,
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_belief_system (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, sensitivity_ord, owner_did,\n'
         '        adherent_fraction, dominance_rank,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', 0, $4,\n"
         '        $5, $6,\n'
         '        $7, $8, null, $9\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.cohortBeliefSystem/bel-bronze_age-yhwh',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/bronze_age-001-3000',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.beliefSystem/yhwh',
                 'did:web:natural-person.gftd.ai',
                 0.05,
                 2,
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_belief_system (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, sensitivity_ord, owner_did,\n'
         '        adherent_fraction, dominance_rank,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', 0, $4,\n"
         '        $5, $6,\n'
         '        $7, $8, null, $9\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.cohortBeliefSystem/bel-bronze_age-dharma',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/bronze_age-001-3000',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.beliefSystem/dharma',
                 'did:web:natural-person.gftd.ai',
                 0.15,
                 1,
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_belief_system (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, sensitivity_ord, owner_did,\n'
         '        adherent_fraction, dominance_rank,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', 0, $4,\n"
         '        $5, $6,\n'
         '        $7, $8, null, $9\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.cohortBeliefSystem/bel-bronze_age-secular',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/bronze_age-001-3000',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.beliefSystem/secular',
                 'did:web:natural-person.gftd.ai',
                 0.7,
                 3,
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_belief_system (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, sensitivity_ord, owner_did,\n'
         '        adherent_fraction, dominance_rank,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', 0, $4,\n"
         '        $5, $6,\n'
         '        $7, $8, null, $9\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.cohortBeliefSystem/bel-iron_age-yhwh',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/iron_age-001-1200',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.beliefSystem/yhwh',
                 'did:web:natural-person.gftd.ai',
                 0.1,
                 2,
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_belief_system (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, sensitivity_ord, owner_did,\n'
         '        adherent_fraction, dominance_rank,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', 0, $4,\n"
         '        $5, $6,\n'
         '        $7, $8, null, $9\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.cohortBeliefSystem/bel-iron_age-dharma',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/iron_age-001-1200',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.beliefSystem/dharma',
                 'did:web:natural-person.gftd.ai',
                 0.2,
                 1,
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_belief_system (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, sensitivity_ord, owner_did,\n'
         '        adherent_fraction, dominance_rank,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', 0, $4,\n"
         '        $5, $6,\n'
         '        $7, $8, null, $9\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.cohortBeliefSystem/bel-iron_age-confucian',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/iron_age-001-1200',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.beliefSystem/confucian',
                 'did:web:natural-person.gftd.ai',
                 0.15,
                 3,
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_belief_system (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, sensitivity_ord, owner_did,\n'
         '        adherent_fraction, dominance_rank,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', 0, $4,\n"
         '        $5, $6,\n'
         '        $7, $8, null, $9\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.cohortBeliefSystem/bel-classical-yhwh',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/classical-001-500',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.beliefSystem/yhwh',
                 'did:web:natural-person.gftd.ai',
                 0.25,
                 1,
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_belief_system (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, sensitivity_ord, owner_did,\n'
         '        adherent_fraction, dominance_rank,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', 0, $4,\n"
         '        $5, $6,\n'
         '        $7, $8, null, $9\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.cohortBeliefSystem/bel-classical-dharma',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/classical-001-500',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.beliefSystem/dharma',
                 'did:web:natural-person.gftd.ai',
                 0.25,
                 2,
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_belief_system (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, sensitivity_ord, owner_did,\n'
         '        adherent_fraction, dominance_rank,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', 0, $4,\n"
         '        $5, $6,\n'
         '        $7, $8, null, $9\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.cohortBeliefSystem/bel-classical-confucian',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/classical-001-500',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.beliefSystem/confucian',
                 'did:web:natural-person.gftd.ai',
                 0.2,
                 3,
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_belief_system (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, sensitivity_ord, owner_did,\n'
         '        adherent_fraction, dominance_rank,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', 0, $4,\n"
         '        $5, $6,\n'
         '        $7, $8, null, $9\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.cohortBeliefSystem/bel-medieval-yhwh',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/medieval-001-1000',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.beliefSystem/yhwh',
                 'did:web:natural-person.gftd.ai',
                 0.5,
                 1,
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_belief_system (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, sensitivity_ord, owner_did,\n'
         '        adherent_fraction, dominance_rank,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', 0, $4,\n"
         '        $5, $6,\n'
         '        $7, $8, null, $9\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.cohortBeliefSystem/bel-medieval-dharma',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/medieval-001-1000',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.beliefSystem/dharma',
                 'did:web:natural-person.gftd.ai',
                 0.25,
                 2,
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_belief_system (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, sensitivity_ord, owner_did,\n'
         '        adherent_fraction, dominance_rank,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', 0, $4,\n"
         '        $5, $6,\n'
         '        $7, $8, null, $9\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.cohortBeliefSystem/bel-medieval-confucian',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/medieval-001-1000',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.beliefSystem/confucian',
                 'did:web:natural-person.gftd.ai',
                 0.15,
                 3,
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_belief_system (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, sensitivity_ord, owner_did,\n'
         '        adherent_fraction, dominance_rank,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', 0, $4,\n"
         '        $5, $6,\n'
         '        $7, $8, null, $9\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.cohortBeliefSystem/bel-modern_boom-yhwh',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/modern_boom-001-1950',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.beliefSystem/yhwh',
                 'did:web:natural-person.gftd.ai',
                 0.53,
                 1,
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_belief_system (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, sensitivity_ord, owner_did,\n'
         '        adherent_fraction, dominance_rank,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', 0, $4,\n"
         '        $5, $6,\n'
         '        $7, $8, null, $9\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.cohortBeliefSystem/bel-modern_boom-dharma',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/modern_boom-001-1950',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.beliefSystem/dharma',
                 'did:web:natural-person.gftd.ai',
                 0.2,
                 2,
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_belief_system (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, sensitivity_ord, owner_did,\n'
         '        adherent_fraction, dominance_rank,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', 0, $4,\n"
         '        $5, $6,\n'
         '        $7, $8, null, $9\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.cohortBeliefSystem/bel-modern_boom-secular',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/modern_boom-001-1950',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.beliefSystem/secular',
                 'did:web:natural-person.gftd.ai',
                 0.15,
                 3,
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_belief_system (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, sensitivity_ord, owner_did,\n'
         '        adherent_fraction, dominance_rank,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', 0, $4,\n"
         '        $5, $6,\n'
         '        $7, $8, null, $9\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.cohortBeliefSystem/bel-modern_boom-confucian',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/modern_boom-001-1950',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.beliefSystem/confucian',
                 'did:web:natural-person.gftd.ai',
                 0.08,
                 4,
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_belief_system (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, sensitivity_ord, owner_did,\n'
         '        adherent_fraction, dominance_rank,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', 0, $4,\n"
         '        $5, $6,\n'
         '        $7, $8, null, $9\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.cohortBeliefSystem/bel-modern_boom-dialectical',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/modern_boom-001-1950',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.beliefSystem/dialectical-materialism',
                 'did:web:natural-person.gftd.ai',
                 0.35,
                 2,
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_belief_system (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, sensitivity_ord, owner_did,\n'
         '        adherent_fraction, dominance_rank,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', 0, $4,\n"
         '        $5, $6,\n'
         '        $7, $8, null, $9\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.cohortBeliefSystem/bel-contemporary-yhwh',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/contemporary-001-2000',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.beliefSystem/yhwh',
                 'did:web:natural-person.gftd.ai',
                 0.53,
                 1,
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_belief_system (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, sensitivity_ord, owner_did,\n'
         '        adherent_fraction, dominance_rank,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', 0, $4,\n"
         '        $5, $6,\n'
         '        $7, $8, null, $9\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.cohortBeliefSystem/bel-contemporary-dharma',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/contemporary-001-2000',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.beliefSystem/dharma',
                 'did:web:natural-person.gftd.ai',
                 0.22,
                 2,
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_belief_system (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, sensitivity_ord, owner_did,\n'
         '        adherent_fraction, dominance_rank,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', 0, $4,\n"
         '        $5, $6,\n'
         '        $7, $8, null, $9\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.cohortBeliefSystem/bel-contemporary-secular',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/contemporary-001-2000',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.beliefSystem/secular',
                 'did:web:natural-person.gftd.ai',
                 0.16,
                 3,
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_belief_system (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, sensitivity_ord, owner_did,\n'
         '        adherent_fraction, dominance_rank,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', 0, $4,\n"
         '        $5, $6,\n'
         '        $7, $8, null, $9\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.cohortBeliefSystem/bel-contemporary-dialectical',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/contemporary-001-2000',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.beliefSystem/dialectical-materialism',
                 'did:web:natural-person.gftd.ai',
                 0.1,
                 4,
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_belief_system (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, sensitivity_ord, owner_did,\n'
         '        adherent_fraction, dominance_rank,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', 0, $4,\n"
         '        $5, $6,\n'
         '        $7, $8, null, $9\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.cohortBeliefSystem/bel-contemporary-confucian',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/contemporary-001-2000',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.beliefSystem/confucian',
                 'did:web:natural-person.gftd.ai',
                 0.07,
                 5,
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_person_cohort_belief_cross AS\n'
         '    SELECT\n'
         '      c.era_label,\n'
         '      c.era_start_year,\n'
         '      c.estimated_population,\n'
         '      b.adherent_fraction,\n'
         '      b.dominance_rank,\n'
         '      b.dst_vid AS belief_vid\n'
         '    FROM vertex_person_population_cohort c\n'
         '    JOIN edge_cohort_belief_system b ON b.src_vid = c.vertex_id\n'
         "    WHERE c.region_m49 = '001'\n"
         '    ORDER BY c.era_start_year ASC, b.dominance_rank ASC\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '      INSERT INTO vertex_person_population_cohort (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord,\n'
         '        owner_did, rkey, repo,\n'
         '        era_label, era_start_year, era_end_year,\n'
         '        region_m49, region_name,\n'
         '        estimated_population, population_low, population_high,\n'
         '        life_expectancy, birth_rate, death_rate,\n'
         '        data_source, confidence_level,\n'
         '        cohort_did,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         "        $1, 1, '2026-04-28', 0,\n"
         '        $2, $3, $4,\n'
         "        'contemporary', 2000, 2025,\n"
         '        $5, $6,\n'
         '        $7, $8, $9,\n'
         '        $10, $11, $12,\n'
         "        'un_wpp_2024', 'high',\n"
         '        $13,\n'
         '        $14, $15, null, $16\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/contemporary-002-2000',
                 'did:web:natural-person.gftd.ai',
                 'contemporary-002-2000',
                 'at://did:web:natural-person.gftd.ai',
                 '002',
                 'Africa',
                 1500000000,
                 1490000000,
                 1510000000,
                 63,
                 33,
                 8,
                 'did:web:natural-person.gftd.ai:pop:contemporary-002-2000',
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_ancestor_of (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, sensitivity_ord, owner_did,\n'
         '        generation_offset, temporal_gap_years, confidence, lineage_type,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', 0, $4,\n"
         "        0, 0, 1.0, 'split',\n"
         '        $5, $6, null, $7\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.cohortAncestorOf/reg-contemporary-002',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/contemporary-001-2000',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/contemporary-002-2000',
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_person_population_cohort (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord,\n'
         '        owner_did, rkey, repo,\n'
         '        era_label, era_start_year, era_end_year,\n'
         '        region_m49, region_name,\n'
         '        estimated_population, population_low, population_high,\n'
         '        life_expectancy, birth_rate, death_rate,\n'
         '        data_source, confidence_level,\n'
         '        cohort_did,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         "        $1, 1, '2026-04-28', 0,\n"
         '        $2, $3, $4,\n'
         "        'contemporary', 2000, 2025,\n"
         '        $5, $6,\n'
         '        $7, $8, $9,\n'
         '        $10, $11, $12,\n'
         "        'un_wpp_2024', 'high',\n"
         '        $13,\n'
         '        $14, $15, null, $16\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/contemporary-019-2000',
                 'did:web:natural-person.gftd.ai',
                 'contemporary-019-2000',
                 'at://did:web:natural-person.gftd.ai',
                 '019',
                 'Americas',
                 1050000000,
                 1040000000,
                 1060000000,
                 75,
                 15,
                 7,
                 'did:web:natural-person.gftd.ai:pop:contemporary-019-2000',
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_ancestor_of (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, sensitivity_ord, owner_did,\n'
         '        generation_offset, temporal_gap_years, confidence, lineage_type,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', 0, $4,\n"
         "        0, 0, 1.0, 'split',\n"
         '        $5, $6, null, $7\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.cohortAncestorOf/reg-contemporary-019',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/contemporary-001-2000',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/contemporary-019-2000',
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_person_population_cohort (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord,\n'
         '        owner_did, rkey, repo,\n'
         '        era_label, era_start_year, era_end_year,\n'
         '        region_m49, region_name,\n'
         '        estimated_population, population_low, population_high,\n'
         '        life_expectancy, birth_rate, death_rate,\n'
         '        data_source, confidence_level,\n'
         '        cohort_did,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         "        $1, 1, '2026-04-28', 0,\n"
         '        $2, $3, $4,\n'
         "        'contemporary', 2000, 2025,\n"
         '        $5, $6,\n'
         '        $7, $8, $9,\n'
         '        $10, $11, $12,\n'
         "        'un_wpp_2024', 'high',\n"
         '        $13,\n'
         '        $14, $15, null, $16\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/contemporary-142-2000',
                 'did:web:natural-person.gftd.ai',
                 'contemporary-142-2000',
                 'at://did:web:natural-person.gftd.ai',
                 '142',
                 'Asia',
                 4800000000,
                 4790000000,
                 4810000000,
                 73,
                 17,
                 8,
                 'did:web:natural-person.gftd.ai:pop:contemporary-142-2000',
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_ancestor_of (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, sensitivity_ord, owner_did,\n'
         '        generation_offset, temporal_gap_years, confidence, lineage_type,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', 0, $4,\n"
         "        0, 0, 1.0, 'split',\n"
         '        $5, $6, null, $7\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.cohortAncestorOf/reg-contemporary-142',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/contemporary-001-2000',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/contemporary-142-2000',
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_person_population_cohort (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord,\n'
         '        owner_did, rkey, repo,\n'
         '        era_label, era_start_year, era_end_year,\n'
         '        region_m49, region_name,\n'
         '        estimated_population, population_low, population_high,\n'
         '        life_expectancy, birth_rate, death_rate,\n'
         '        data_source, confidence_level,\n'
         '        cohort_did,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         "        $1, 1, '2026-04-28', 0,\n"
         '        $2, $3, $4,\n'
         "        'contemporary', 2000, 2025,\n"
         '        $5, $6,\n'
         '        $7, $8, $9,\n'
         '        $10, $11, $12,\n'
         "        'un_wpp_2024', 'high',\n"
         '        $13,\n'
         '        $14, $15, null, $16\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/contemporary-150-2000',
                 'did:web:natural-person.gftd.ai',
                 'contemporary-150-2000',
                 'at://did:web:natural-person.gftd.ai',
                 '150',
                 'Europe',
                 740000000,
                 735000000,
                 745000000,
                 79,
                 10,
                 11,
                 'did:web:natural-person.gftd.ai:pop:contemporary-150-2000',
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_ancestor_of (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, sensitivity_ord, owner_did,\n'
         '        generation_offset, temporal_gap_years, confidence, lineage_type,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', 0, $4,\n"
         "        0, 0, 1.0, 'split',\n"
         '        $5, $6, null, $7\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.cohortAncestorOf/reg-contemporary-150',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/contemporary-001-2000',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/contemporary-150-2000',
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_person_population_cohort (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord,\n'
         '        owner_did, rkey, repo,\n'
         '        era_label, era_start_year, era_end_year,\n'
         '        region_m49, region_name,\n'
         '        estimated_population, population_low, population_high,\n'
         '        life_expectancy, birth_rate, death_rate,\n'
         '        data_source, confidence_level,\n'
         '        cohort_did,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         "        $1, 1, '2026-04-28', 0,\n"
         '        $2, $3, $4,\n'
         "        'contemporary', 2000, 2025,\n"
         '        $5, $6,\n'
         '        $7, $8, $9,\n'
         '        $10, $11, $12,\n'
         "        'un_wpp_2024', 'high',\n"
         '        $13,\n'
         '        $14, $15, null, $16\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/contemporary-009-2000',
                 'did:web:natural-person.gftd.ai',
                 'contemporary-009-2000',
                 'at://did:web:natural-person.gftd.ai',
                 '009',
                 'Oceania',
                 46000000,
                 45000000,
                 47000000,
                 78,
                 15,
                 7,
                 'did:web:natural-person.gftd.ai:pop:contemporary-009-2000',
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_ancestor_of (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, sensitivity_ord, owner_did,\n'
         '        generation_offset, temporal_gap_years, confidence, lineage_type,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', 0, $4,\n"
         "        0, 0, 1.0, 'split',\n"
         '        $5, $6, null, $7\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.cohortAncestorOf/reg-contemporary-009',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/contemporary-001-2000',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/contemporary-009-2000',
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '    INSERT INTO edge_cohort_ancestor_of (\n'
         '      edge_id, src_vid, dst_vid,\n'
         '      _seq, created_date, sensitivity_ord, owner_did,\n'
         '      generation_offset, temporal_gap_years, confidence, lineage_type,\n'
         '      actor_did, org_did, at_did, created_at\n'
         '    ) VALUES (\n'
         '      '
         "'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.cohortAncestorOf/pop-to-cohort-coordinator',\n"
         '      '
         "'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/contemporary-001-2000',\n"
         "      'did:web:natural-person.gftd.ai',\n"
         "      1, '2026-04-28', 0, 'did:web:natural-person.gftd.ai',\n"
         "      1, 0, 0.95, 'direct',\n"
         "      'did:web:natural-person.gftd.ai', 'did:web:natural-person.gftd.ai', null,\n"
         "      '2026-04-28T00:00:00Z'\n"
         '    )\n'
         '  ',
  'parameters': []}]

DOWN = [{'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_person_cohort_belief_cross', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_edge_cohort_belief_src', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_edge_cohort_belief_dst', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_cohort_belief_system', 'parameters': []},
 {'sql': '\n'
         '    DELETE FROM vertex_person_population_cohort\n'
         "    WHERE era_label = 'contemporary' AND region_m49 != '001'\n"
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    DELETE FROM edge_cohort_ancestor_of\n'
         "    WHERE edge_id LIKE '%pop-to-cohort-coordinator%'\n"
         "    OR lineage_type = 'split'\n"
         '  ',
  'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
