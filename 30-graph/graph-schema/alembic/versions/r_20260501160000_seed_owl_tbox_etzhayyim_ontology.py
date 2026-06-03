"""Captured from Kysely migration 20260501160000_seed_owl_tbox_etzhayyim_ontology."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260501160000_seed_owl_tbox_etzhayyim_ontology"
down_revision = 'r_20260501150000_seed_owl_reasoner_bpmn'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '      INSERT INTO vertex_owl_class (vertex_id, class_iri, label, profile, source_nsid, '
         'created_at)\n'
         '      VALUES ($1, $2, $3, $4, $5, $6)\n'
         '    ',
  'parameters': ['etzhayyim:Thing',
                 'https://schema.etzhayyim.com/owl#Thing',
                 'owl:Thing (root)',
                 'etzhayyim_core_v1',
                 'com.etzhayyim.apps.owl.seedTbox',
                 '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_owl_class (vertex_id, class_iri, label, profile, source_nsid, '
         'created_at)\n'
         '      VALUES ($1, $2, $3, $4, $5, $6)\n'
         '    ',
  'parameters': ['etzhayyim:Resource',
                 'https://schema.etzhayyim.com/owl#Resource',
                 'etzhayyim Resource',
                 'etzhayyim_core_v1',
                 'com.etzhayyim.apps.owl.seedTbox',
                 '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_owl_class (vertex_id, class_iri, label, profile, source_nsid, '
         'created_at)\n'
         '      VALUES ($1, $2, $3, $4, $5, $6)\n'
         '    ',
  'parameters': ['etzhayyim:Actor',
                 'https://schema.etzhayyim.com/owl#Actor',
                 'etzhayyim Actor',
                 'etzhayyim_core_v1',
                 'com.etzhayyim.apps.owl.seedTbox',
                 '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_owl_class (vertex_id, class_iri, label, profile, source_nsid, '
         'created_at)\n'
         '      VALUES ($1, $2, $3, $4, $5, $6)\n'
         '    ',
  'parameters': ['etzhayyim:MagatamaActor',
                 'https://schema.etzhayyim.com/owl#MagatamaActor',
                 'Magatama Actor (BPMN-resident)',
                 'etzhayyim_core_v1',
                 'com.etzhayyim.apps.owl.seedTbox',
                 '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_owl_class (vertex_id, class_iri, label, profile, source_nsid, '
         'created_at)\n'
         '      VALUES ($1, $2, $3, $4, $5, $6)\n'
         '    ',
  'parameters': ['etzhayyim:HumanActor',
                 'https://schema.etzhayyim.com/owl#HumanActor',
                 'Human Actor (natural person)',
                 'etzhayyim_core_v1',
                 'com.etzhayyim.apps.owl.seedTbox',
                 '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_owl_class (vertex_id, class_iri, label, profile, source_nsid, '
         'created_at)\n'
         '      VALUES ($1, $2, $3, $4, $5, $6)\n'
         '    ',
  'parameters': ['etzhayyim:OrgActor',
                 'https://schema.etzhayyim.com/owl#OrgActor',
                 'Organisation Actor',
                 'etzhayyim_core_v1',
                 'com.etzhayyim.apps.owl.seedTbox',
                 '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_owl_class (vertex_id, class_iri, label, profile, source_nsid, '
         'created_at)\n'
         '      VALUES ($1, $2, $3, $4, $5, $6)\n'
         '    ',
  'parameters': ['etzhayyim:BpmnProcess',
                 'https://schema.etzhayyim.com/owl#BpmnProcess',
                 'BPMN Process (Zeebe-deployed)',
                 'etzhayyim_core_v1',
                 'com.etzhayyim.apps.owl.seedTbox',
                 '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_owl_class (vertex_id, class_iri, label, profile, source_nsid, '
         'created_at)\n'
         '      VALUES ($1, $2, $3, $4, $5, $6)\n'
         '    ',
  'parameters': ['etzhayyim:KnowledgeGraph',
                 'https://schema.etzhayyim.com/owl#KnowledgeGraph',
                 'Knowledge Graph node',
                 'etzhayyim_core_v1',
                 'com.etzhayyim.apps.owl.seedTbox',
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
  'parameters': ['etzhayyim:follows',
                 'https://schema.etzhayyim.com/owl#follows',
                 'ObjectProperty',
                 False,
                 False,
                 False,
                 False,
                 'etzhayyim_core_v1',
                 'com.etzhayyim.apps.owl.seedTbox',
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
  'parameters': ['etzhayyim:hasBpmnProcess',
                 'https://schema.etzhayyim.com/owl#hasBpmnProcess',
                 'ObjectProperty',
                 False,
                 False,
                 False,
                 False,
                 'etzhayyim_core_v1',
                 'com.etzhayyim.apps.owl.seedTbox',
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
  'parameters': ['etzhayyim:managedBy',
                 'https://schema.etzhayyim.com/owl#managedBy',
                 'ObjectProperty',
                 True,
                 False,
                 False,
                 False,
                 'etzhayyim_core_v1',
                 'com.etzhayyim.apps.owl.seedTbox',
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
  'parameters': ['etzhayyim:memberOf',
                 'https://schema.etzhayyim.com/owl#memberOf',
                 'ObjectProperty',
                 False,
                 False,
                 False,
                 False,
                 'etzhayyim_core_v1',
                 'com.etzhayyim.apps.owl.seedTbox',
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
  'parameters': ['etzhayyim:handle',
                 'https://schema.etzhayyim.com/owl#handle',
                 'DatatypeProperty',
                 False,
                 False,
                 False,
                 False,
                 'etzhayyim_core_v1',
                 'com.etzhayyim.apps.owl.seedTbox',
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
                 'etzhayyim_core_v1',
                 'com.etzhayyim.apps.owl.seedTbox',
                 '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO edge_owl_subclass (from_vertex_id, to_vertex_id, axiom_type, profile, '
         'created_at)\n'
         '      VALUES ($1, $2, $3, $4, $5)\n'
         '    ',
  'parameters': ['etzhayyim:Resource',
                 'etzhayyim:Thing',
                 'SubClassOf',
                 'etzhayyim_core_v1',
                 '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO edge_owl_subclass (from_vertex_id, to_vertex_id, axiom_type, profile, '
         'created_at)\n'
         '      VALUES ($1, $2, $3, $4, $5)\n'
         '    ',
  'parameters': ['etzhayyim:Actor',
                 'etzhayyim:Resource',
                 'SubClassOf',
                 'etzhayyim_core_v1',
                 '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO edge_owl_subclass (from_vertex_id, to_vertex_id, axiom_type, profile, '
         'created_at)\n'
         '      VALUES ($1, $2, $3, $4, $5)\n'
         '    ',
  'parameters': ['etzhayyim:MagatamaActor',
                 'etzhayyim:Actor',
                 'SubClassOf',
                 'etzhayyim_core_v1',
                 '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO edge_owl_subclass (from_vertex_id, to_vertex_id, axiom_type, profile, '
         'created_at)\n'
         '      VALUES ($1, $2, $3, $4, $5)\n'
         '    ',
  'parameters': ['etzhayyim:HumanActor',
                 'etzhayyim:Actor',
                 'SubClassOf',
                 'etzhayyim_core_v1',
                 '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO edge_owl_subclass (from_vertex_id, to_vertex_id, axiom_type, profile, '
         'created_at)\n'
         '      VALUES ($1, $2, $3, $4, $5)\n'
         '    ',
  'parameters': ['etzhayyim:OrgActor',
                 'etzhayyim:Actor',
                 'SubClassOf',
                 'etzhayyim_core_v1',
                 '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO edge_owl_subclass (from_vertex_id, to_vertex_id, axiom_type, profile, '
         'created_at)\n'
         '      VALUES ($1, $2, $3, $4, $5)\n'
         '    ',
  'parameters': ['etzhayyim:BpmnProcess',
                 'etzhayyim:Resource',
                 'SubClassOf',
                 'etzhayyim_core_v1',
                 '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO edge_owl_subclass (from_vertex_id, to_vertex_id, axiom_type, profile, '
         'created_at)\n'
         '      VALUES ($1, $2, $3, $4, $5)\n'
         '    ',
  'parameters': ['etzhayyim:KnowledgeGraph',
                 'etzhayyim:Resource',
                 'SubClassOf',
                 'etzhayyim_core_v1',
                 '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO edge_owl_property_domain (from_vertex_id, to_vertex_id, profile, '
         'created_at)\n'
         '      VALUES ($1, $2, $3, $4)\n'
         '    ',
  'parameters': ['etzhayyim:follows', 'etzhayyim:Actor', 'etzhayyim_core_v1', '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO edge_owl_property_domain (from_vertex_id, to_vertex_id, profile, '
         'created_at)\n'
         '      VALUES ($1, $2, $3, $4)\n'
         '    ',
  'parameters': ['etzhayyim:hasBpmnProcess', 'etzhayyim:Actor', 'etzhayyim_core_v1', '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO edge_owl_property_domain (from_vertex_id, to_vertex_id, profile, '
         'created_at)\n'
         '      VALUES ($1, $2, $3, $4)\n'
         '    ',
  'parameters': ['etzhayyim:managedBy', 'etzhayyim:BpmnProcess', 'etzhayyim_core_v1', '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO edge_owl_property_domain (from_vertex_id, to_vertex_id, profile, '
         'created_at)\n'
         '      VALUES ($1, $2, $3, $4)\n'
         '    ',
  'parameters': ['etzhayyim:memberOf', 'etzhayyim:Actor', 'etzhayyim_core_v1', '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO edge_owl_property_domain (from_vertex_id, to_vertex_id, profile, '
         'created_at)\n'
         '      VALUES ($1, $2, $3, $4)\n'
         '    ',
  'parameters': ['etzhayyim:handle', 'etzhayyim:Resource', 'etzhayyim_core_v1', '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO edge_owl_property_domain (from_vertex_id, to_vertex_id, profile, '
         'created_at)\n'
         '      VALUES ($1, $2, $3, $4)\n'
         '    ',
  'parameters': ['rdfs:label', 'etzhayyim:Resource', 'etzhayyim_core_v1', '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO edge_owl_property_range (from_vertex_id, to_vertex_id, profile, '
         'created_at)\n'
         '      VALUES ($1, $2, $3, $4)\n'
         '    ',
  'parameters': ['etzhayyim:follows', 'etzhayyim:Actor', 'etzhayyim_core_v1', '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO edge_owl_property_range (from_vertex_id, to_vertex_id, profile, '
         'created_at)\n'
         '      VALUES ($1, $2, $3, $4)\n'
         '    ',
  'parameters': ['etzhayyim:hasBpmnProcess',
                 'etzhayyim:BpmnProcess',
                 'etzhayyim_core_v1',
                 '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO edge_owl_property_range (from_vertex_id, to_vertex_id, profile, '
         'created_at)\n'
         '      VALUES ($1, $2, $3, $4)\n'
         '    ',
  'parameters': ['etzhayyim:managedBy', 'etzhayyim:Actor', 'etzhayyim_core_v1', '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO edge_owl_property_range (from_vertex_id, to_vertex_id, profile, '
         'created_at)\n'
         '      VALUES ($1, $2, $3, $4)\n'
         '    ',
  'parameters': ['etzhayyim:memberOf', 'etzhayyim:OrgActor', 'etzhayyim_core_v1', '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO edge_owl_property_range (from_vertex_id, to_vertex_id, profile, '
         'created_at)\n'
         '      VALUES ($1, $2, $3, $4)\n'
         '    ',
  'parameters': ['etzhayyim:handle', 'xsd:string', 'etzhayyim_core_v1', '2026-05-08T00:42:53.785Z']},
 {'sql': '\n'
         '      INSERT INTO edge_owl_property_range (from_vertex_id, to_vertex_id, profile, '
         'created_at)\n'
         '      VALUES ($1, $2, $3, $4)\n'
         '    ',
  'parameters': ['rdfs:label', 'xsd:string', 'etzhayyim_core_v1', '2026-05-08T00:42:53.785Z']},
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
                 'https://schema.etzhayyim.com/owl#ActorShape',
                 'etzhayyim:Actor',
                 'minCount',
                 '{"path":"etzhayyim:handle","minCount":1}',
                 'Warning',
                 'com.etzhayyim.apps.owl.seedTbox',
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
                 'https://schema.etzhayyim.com/owl#BpmnProcessShape',
                 'etzhayyim:BpmnProcess',
                 'minCount',
                 '{"path":"etzhayyim:managedBy","minCount":1}',
                 'Info',
                 'com.etzhayyim.apps.owl.seedTbox',
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
                 'https://schema.etzhayyim.com/owl#FollowsSymmetryShape',
                 'etzhayyim:Actor',
                 'qualifiedValueShape',
                 '{"path":"etzhayyim:follows","qualifiedMinCount":0,"qualifiedValueShape":{"class":"etzhayyim:Actor"}}',
                 'Info',
                 'com.etzhayyim.apps.owl.seedTbox',
                 '2026-05-08T00:42:53.785Z']}]

DOWN = [{'sql': 'DELETE FROM vertex_shacl_shape      WHERE source_nsid = $1',
  'parameters': ['com.etzhayyim.apps.owl.seedTbox']},
 {'sql': 'DELETE FROM edge_owl_property_range WHERE profile = $1', 'parameters': ['etzhayyim_core_v1']},
 {'sql': 'DELETE FROM edge_owl_property_domain WHERE profile = $1', 'parameters': ['etzhayyim_core_v1']},
 {'sql': 'DELETE FROM edge_owl_subclass        WHERE profile = $1', 'parameters': ['etzhayyim_core_v1']},
 {'sql': 'DELETE FROM vertex_owl_property      WHERE profile = $1', 'parameters': ['etzhayyim_core_v1']},
 {'sql': 'DELETE FROM vertex_owl_class         WHERE profile = $1', 'parameters': ['etzhayyim_core_v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
