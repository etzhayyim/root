"""Captured from Kysely migration 20260501160000_seed_owl_tbox_gftd_ontology."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260501160000_seed_owl_tbox_gftd_ontology"
down_revision = 'r_20260501150000_seed_owl_reasoner_bpmn'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '      INSERT INTO vertex_owl_class (vertex_id, class_iri, label, profile, source_nsid, '
         'created_at)\n'
         '      VALUES ($1, $2, $3, $4, $5, $6)\n'
         '    ',
  'parameters': ['gftd:Thing',
                 'https://schema.gftd.ai/owl#Thing',
                 'owl:Thing (root)',
                 'gftd_core_v1',
                 'ai.gftd.apps.owl.seedTbox',
                 '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_owl_class (vertex_id, class_iri, label, profile, source_nsid, '
         'created_at)\n'
         '      VALUES ($1, $2, $3, $4, $5, $6)\n'
         '    ',
  'parameters': ['gftd:Resource',
                 'https://schema.gftd.ai/owl#Resource',
                 'GFTD Resource',
                 'gftd_core_v1',
                 'ai.gftd.apps.owl.seedTbox',
                 '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_owl_class (vertex_id, class_iri, label, profile, source_nsid, '
         'created_at)\n'
         '      VALUES ($1, $2, $3, $4, $5, $6)\n'
         '    ',
  'parameters': ['gftd:Actor',
                 'https://schema.gftd.ai/owl#Actor',
                 'GFTD Actor',
                 'gftd_core_v1',
                 'ai.gftd.apps.owl.seedTbox',
                 '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_owl_class (vertex_id, class_iri, label, profile, source_nsid, '
         'created_at)\n'
         '      VALUES ($1, $2, $3, $4, $5, $6)\n'
         '    ',
  'parameters': ['gftd:MagatamaActor',
                 'https://schema.gftd.ai/owl#MagatamaActor',
                 'Magatama Actor (BPMN-resident)',
                 'gftd_core_v1',
                 'ai.gftd.apps.owl.seedTbox',
                 '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_owl_class (vertex_id, class_iri, label, profile, source_nsid, '
         'created_at)\n'
         '      VALUES ($1, $2, $3, $4, $5, $6)\n'
         '    ',
  'parameters': ['gftd:HumanActor',
                 'https://schema.gftd.ai/owl#HumanActor',
                 'Human Actor (natural person)',
                 'gftd_core_v1',
                 'ai.gftd.apps.owl.seedTbox',
                 '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_owl_class (vertex_id, class_iri, label, profile, source_nsid, '
         'created_at)\n'
         '      VALUES ($1, $2, $3, $4, $5, $6)\n'
         '    ',
  'parameters': ['gftd:OrgActor',
                 'https://schema.gftd.ai/owl#OrgActor',
                 'Organisation Actor',
                 'gftd_core_v1',
                 'ai.gftd.apps.owl.seedTbox',
                 '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_owl_class (vertex_id, class_iri, label, profile, source_nsid, '
         'created_at)\n'
         '      VALUES ($1, $2, $3, $4, $5, $6)\n'
         '    ',
  'parameters': ['gftd:BpmnProcess',
                 'https://schema.gftd.ai/owl#BpmnProcess',
                 'BPMN Process (Zeebe-deployed)',
                 'gftd_core_v1',
                 'ai.gftd.apps.owl.seedTbox',
                 '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_owl_class (vertex_id, class_iri, label, profile, source_nsid, '
         'created_at)\n'
         '      VALUES ($1, $2, $3, $4, $5, $6)\n'
         '    ',
  'parameters': ['gftd:KnowledgeGraph',
                 'https://schema.gftd.ai/owl#KnowledgeGraph',
                 'Knowledge Graph node',
                 'gftd_core_v1',
                 'ai.gftd.apps.owl.seedTbox',
                 '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_owl_property\n'
         '        (vertex_id, property_iri, property_type, is_functional, is_transitive,\n'
         '         is_symmetric, is_inverse_functional, profile, source_nsid, created_at)\n'
         '      VALUES (\n'
         '        $1, $2, $3,\n'
         '        $4, $5, $6, $7,\n'
         '        $8, $9, $10\n'
         '      )\n'
         '    ',
  'parameters': ['gftd:follows',
                 'https://schema.gftd.ai/owl#follows',
                 'ObjectProperty',
                 False,
                 False,
                 False,
                 False,
                 'gftd_core_v1',
                 'ai.gftd.apps.owl.seedTbox',
                 '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_owl_property\n'
         '        (vertex_id, property_iri, property_type, is_functional, is_transitive,\n'
         '         is_symmetric, is_inverse_functional, profile, source_nsid, created_at)\n'
         '      VALUES (\n'
         '        $1, $2, $3,\n'
         '        $4, $5, $6, $7,\n'
         '        $8, $9, $10\n'
         '      )\n'
         '    ',
  'parameters': ['gftd:hasBpmnProcess',
                 'https://schema.gftd.ai/owl#hasBpmnProcess',
                 'ObjectProperty',
                 False,
                 False,
                 False,
                 False,
                 'gftd_core_v1',
                 'ai.gftd.apps.owl.seedTbox',
                 '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_owl_property\n'
         '        (vertex_id, property_iri, property_type, is_functional, is_transitive,\n'
         '         is_symmetric, is_inverse_functional, profile, source_nsid, created_at)\n'
         '      VALUES (\n'
         '        $1, $2, $3,\n'
         '        $4, $5, $6, $7,\n'
         '        $8, $9, $10\n'
         '      )\n'
         '    ',
  'parameters': ['gftd:managedBy',
                 'https://schema.gftd.ai/owl#managedBy',
                 'ObjectProperty',
                 True,
                 False,
                 False,
                 False,
                 'gftd_core_v1',
                 'ai.gftd.apps.owl.seedTbox',
                 '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_owl_property\n'
         '        (vertex_id, property_iri, property_type, is_functional, is_transitive,\n'
         '         is_symmetric, is_inverse_functional, profile, source_nsid, created_at)\n'
         '      VALUES (\n'
         '        $1, $2, $3,\n'
         '        $4, $5, $6, $7,\n'
         '        $8, $9, $10\n'
         '      )\n'
         '    ',
  'parameters': ['gftd:memberOf',
                 'https://schema.gftd.ai/owl#memberOf',
                 'ObjectProperty',
                 False,
                 False,
                 False,
                 False,
                 'gftd_core_v1',
                 'ai.gftd.apps.owl.seedTbox',
                 '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_owl_property\n'
         '        (vertex_id, property_iri, property_type, is_functional, is_transitive,\n'
         '         is_symmetric, is_inverse_functional, profile, source_nsid, created_at)\n'
         '      VALUES (\n'
         '        $1, $2, $3,\n'
         '        $4, $5, $6, $7,\n'
         '        $8, $9, $10\n'
         '      )\n'
         '    ',
  'parameters': ['gftd:handle',
                 'https://schema.gftd.ai/owl#handle',
                 'DatatypeProperty',
                 False,
                 False,
                 False,
                 False,
                 'gftd_core_v1',
                 'ai.gftd.apps.owl.seedTbox',
                 '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_owl_property\n'
         '        (vertex_id, property_iri, property_type, is_functional, is_transitive,\n'
         '         is_symmetric, is_inverse_functional, profile, source_nsid, created_at)\n'
         '      VALUES (\n'
         '        $1, $2, $3,\n'
         '        $4, $5, $6, $7,\n'
         '        $8, $9, $10\n'
         '      )\n'
         '    ',
  'parameters': ['rdfs:label',
                 'http://www.w3.org/2000/01/rdf-schema#label',
                 'DatatypeProperty',
                 False,
                 False,
                 False,
                 False,
                 'gftd_core_v1',
                 'ai.gftd.apps.owl.seedTbox',
                 '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO edge_owl_subclass (from_vertex_id, to_vertex_id, axiom_type, profile, '
         'created_at)\n'
         '      VALUES ($1, $2, $3, $4, $5)\n'
         '    ',
  'parameters': ['gftd:Resource',
                 'gftd:Thing',
                 'SubClassOf',
                 'gftd_core_v1',
                 '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO edge_owl_subclass (from_vertex_id, to_vertex_id, axiom_type, profile, '
         'created_at)\n'
         '      VALUES ($1, $2, $3, $4, $5)\n'
         '    ',
  'parameters': ['gftd:Actor',
                 'gftd:Resource',
                 'SubClassOf',
                 'gftd_core_v1',
                 '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO edge_owl_subclass (from_vertex_id, to_vertex_id, axiom_type, profile, '
         'created_at)\n'
         '      VALUES ($1, $2, $3, $4, $5)\n'
         '    ',
  'parameters': ['gftd:MagatamaActor',
                 'gftd:Actor',
                 'SubClassOf',
                 'gftd_core_v1',
                 '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO edge_owl_subclass (from_vertex_id, to_vertex_id, axiom_type, profile, '
         'created_at)\n'
         '      VALUES ($1, $2, $3, $4, $5)\n'
         '    ',
  'parameters': ['gftd:HumanActor',
                 'gftd:Actor',
                 'SubClassOf',
                 'gftd_core_v1',
                 '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO edge_owl_subclass (from_vertex_id, to_vertex_id, axiom_type, profile, '
         'created_at)\n'
         '      VALUES ($1, $2, $3, $4, $5)\n'
         '    ',
  'parameters': ['gftd:OrgActor',
                 'gftd:Actor',
                 'SubClassOf',
                 'gftd_core_v1',
                 '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO edge_owl_subclass (from_vertex_id, to_vertex_id, axiom_type, profile, '
         'created_at)\n'
         '      VALUES ($1, $2, $3, $4, $5)\n'
         '    ',
  'parameters': ['gftd:BpmnProcess',
                 'gftd:Resource',
                 'SubClassOf',
                 'gftd_core_v1',
                 '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO edge_owl_subclass (from_vertex_id, to_vertex_id, axiom_type, profile, '
         'created_at)\n'
         '      VALUES ($1, $2, $3, $4, $5)\n'
         '    ',
  'parameters': ['gftd:KnowledgeGraph',
                 'gftd:Resource',
                 'SubClassOf',
                 'gftd_core_v1',
                 '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO edge_owl_property_domain (from_vertex_id, to_vertex_id, profile, '
         'created_at)\n'
         '      VALUES ($1, $2, $3, $4)\n'
         '    ',
  'parameters': ['gftd:follows', 'gftd:Actor', 'gftd_core_v1', '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO edge_owl_property_domain (from_vertex_id, to_vertex_id, profile, '
         'created_at)\n'
         '      VALUES ($1, $2, $3, $4)\n'
         '    ',
  'parameters': ['gftd:hasBpmnProcess', 'gftd:Actor', 'gftd_core_v1', '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO edge_owl_property_domain (from_vertex_id, to_vertex_id, profile, '
         'created_at)\n'
         '      VALUES ($1, $2, $3, $4)\n'
         '    ',
  'parameters': ['gftd:managedBy', 'gftd:BpmnProcess', 'gftd_core_v1', '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO edge_owl_property_domain (from_vertex_id, to_vertex_id, profile, '
         'created_at)\n'
         '      VALUES ($1, $2, $3, $4)\n'
         '    ',
  'parameters': ['gftd:memberOf', 'gftd:Actor', 'gftd_core_v1', '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO edge_owl_property_domain (from_vertex_id, to_vertex_id, profile, '
         'created_at)\n'
         '      VALUES ($1, $2, $3, $4)\n'
         '    ',
  'parameters': ['gftd:handle', 'gftd:Resource', 'gftd_core_v1', '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO edge_owl_property_domain (from_vertex_id, to_vertex_id, profile, '
         'created_at)\n'
         '      VALUES ($1, $2, $3, $4)\n'
         '    ',
  'parameters': ['rdfs:label', 'gftd:Resource', 'gftd_core_v1', '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO edge_owl_property_range (from_vertex_id, to_vertex_id, profile, '
         'created_at)\n'
         '      VALUES ($1, $2, $3, $4)\n'
         '    ',
  'parameters': ['gftd:follows', 'gftd:Actor', 'gftd_core_v1', '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO edge_owl_property_range (from_vertex_id, to_vertex_id, profile, '
         'created_at)\n'
         '      VALUES ($1, $2, $3, $4)\n'
         '    ',
  'parameters': ['gftd:hasBpmnProcess',
                 'gftd:BpmnProcess',
                 'gftd_core_v1',
                 '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO edge_owl_property_range (from_vertex_id, to_vertex_id, profile, '
         'created_at)\n'
         '      VALUES ($1, $2, $3, $4)\n'
         '    ',
  'parameters': ['gftd:managedBy', 'gftd:Actor', 'gftd_core_v1', '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO edge_owl_property_range (from_vertex_id, to_vertex_id, profile, '
         'created_at)\n'
         '      VALUES ($1, $2, $3, $4)\n'
         '    ',
  'parameters': ['gftd:memberOf', 'gftd:OrgActor', 'gftd_core_v1', '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO edge_owl_property_range (from_vertex_id, to_vertex_id, profile, '
         'created_at)\n'
         '      VALUES ($1, $2, $3, $4)\n'
         '    ',
  'parameters': ['gftd:handle', 'xsd:string', 'gftd_core_v1', '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO edge_owl_property_range (from_vertex_id, to_vertex_id, profile, '
         'created_at)\n'
         '      VALUES ($1, $2, $3, $4)\n'
         '    ',
  'parameters': ['rdfs:label', 'xsd:string', 'gftd_core_v1', '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_shacl_shape\n'
         '        (vertex_id, shape_iri, target_class, constraint_type, constraint_json,\n'
         '         severity, source_nsid, enabled, created_at)\n'
         '      VALUES (\n'
         '        $1, $2, $3,\n'
         '        $4, $5::jsonb,\n'
         '        $6, $7, true, $8\n'
         '      )\n'
         '    ',
  'parameters': ['shacl:ActorShape',
                 'https://schema.gftd.ai/owl#ActorShape',
                 'gftd:Actor',
                 'minCount',
                 '{"path":"gftd:handle","minCount":1}',
                 'Warning',
                 'ai.gftd.apps.owl.seedTbox',
                 '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_shacl_shape\n'
         '        (vertex_id, shape_iri, target_class, constraint_type, constraint_json,\n'
         '         severity, source_nsid, enabled, created_at)\n'
         '      VALUES (\n'
         '        $1, $2, $3,\n'
         '        $4, $5::jsonb,\n'
         '        $6, $7, true, $8\n'
         '      )\n'
         '    ',
  'parameters': ['shacl:BpmnProcessShape',
                 'https://schema.gftd.ai/owl#BpmnProcessShape',
                 'gftd:BpmnProcess',
                 'minCount',
                 '{"path":"gftd:managedBy","minCount":1}',
                 'Info',
                 'ai.gftd.apps.owl.seedTbox',
                 '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_shacl_shape\n'
         '        (vertex_id, shape_iri, target_class, constraint_type, constraint_json,\n'
         '         severity, source_nsid, enabled, created_at)\n'
         '      VALUES (\n'
         '        $1, $2, $3,\n'
         '        $4, $5::jsonb,\n'
         '        $6, $7, true, $8\n'
         '      )\n'
         '    ',
  'parameters': ['shacl:FollowsSymmetryShape',
                 'https://schema.gftd.ai/owl#FollowsSymmetryShape',
                 'gftd:Actor',
                 'qualifiedValueShape',
                 '{"path":"gftd:follows","qualifiedMinCount":0,"qualifiedValueShape":{"class":"gftd:Actor"}}',
                 'Info',
                 'ai.gftd.apps.owl.seedTbox',
                 '2026-05-08T00:42:53.785Z']}]

DOWN = [{'sql': 'DELETE FROM vertex_shacl_shape      WHERE source_nsid = $1',
  'parameters': ['ai.gftd.apps.owl.seedTbox']},
 {'sql': 'DELETE FROM edge_owl_property_range WHERE profile = $1', 'parameters': ['gftd_core_v1']},
 {'sql': 'DELETE FROM edge_owl_property_domain WHERE profile = $1', 'parameters': ['gftd_core_v1']},
 {'sql': 'DELETE FROM edge_owl_subclass        WHERE profile = $1', 'parameters': ['gftd_core_v1']},
 {'sql': 'DELETE FROM vertex_owl_property      WHERE profile = $1', 'parameters': ['gftd_core_v1']},
 {'sql': 'DELETE FROM vertex_owl_class         WHERE profile = $1', 'parameters': ['gftd_core_v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
