import { Kysely, sql } from "kysely";

// GFTD Ontology T-Box seed (ADR-0044 Phase 2).
//
// Populates vertex_owl_class / vertex_owl_property / edge_owl_subclass /
// edge_owl_property_domain / edge_owl_property_range + vertex_shacl_shape
// so the hourly owl_reasoner_batch BPMN (Zeebe key 2251799825517334) has
// axioms to run EL++ classification over.
//
// A-Box facts already flow via v_rdf_triple (pure VIEW, no dual-write):
//   - vertex_bpmn_process_def  → gftd:Actor rdf:type triples
//   - edge_follows             → gftd:follows triples
//   - vertex_profile           → gftd:handle triples
//
// IMPORTANT: vertex_id values use CURIE prefix format ("gftd:", "rdfs:",
// "shacl:") to match the CURIE literals emitted by v_rdf_triple.
// The streaming MVs (mv_owl_rl_type_d1, mv_owl_rl_domain) join on
//   edge_owl_subclass.from_vertex_id = v_rdf_triple.object
//   edge_owl_property_domain.from_vertex_id = v_rdf_triple.predicate
// so full-URI vertex IDs would produce zero matches.
//
// IRI convention:  https://schema.etzhayyim.com/owl#{LocalName}
// Profile:         gftd_core_v1
// Applied via:     psql (ADR-2604241342 out-of-band pattern)

const PROFILE = "gftd_core_v1";
const NS = "https://schema.etzhayyim.com/owl#";
const XSD = "http://www.w3.org/2001/XMLSchema#";
const RDFS_NS = "http://www.w3.org/2000/01/rdf-schema#";
const SOURCE = "ai.gftd.apps.owl.seedTbox";

export async function up(db: Kysely<unknown>): Promise<void> {
  const now = new Date().toISOString();

  // ── Classes ──────────────────────────────────────────────────────────────
  // vertex_id uses CURIE prefix so mv_owl_rl_type_d1 can join on
  // v_rdf_triple.object (which emits "gftd:Actor" etc.)
  const classes = [
    { vid: "gftd:Thing",          iri: `${NS}Thing`,          label: "owl:Thing (root)" },
    { vid: "gftd:Resource",       iri: `${NS}Resource`,       label: "GFTD Resource" },
    { vid: "gftd:Actor",          iri: `${NS}Actor`,          label: "GFTD Actor" },
    { vid: "gftd:MagatamaActor",  iri: `${NS}MagatamaActor`,  label: "Magatama Actor (BPMN-resident)" },
    { vid: "gftd:HumanActor",     iri: `${NS}HumanActor`,     label: "Human Actor (natural person)" },
    { vid: "gftd:OrgActor",       iri: `${NS}OrgActor`,       label: "Organisation Actor" },
    { vid: "gftd:BpmnProcess",    iri: `${NS}BpmnProcess`,    label: "BPMN Process (Zeebe-deployed)" },
    { vid: "gftd:KnowledgeGraph", iri: `${NS}KnowledgeGraph`, label: "Knowledge Graph node" },
  ];

  for (const c of classes) {
    await sql`
      INSERT INTO vertex_owl_class (vertex_id, class_iri, label, profile, source_nsid, created_at)
      VALUES (${c.vid}, ${c.iri}, ${c.label}, ${PROFILE}, ${SOURCE}, ${now})
    `.execute(db);
  }

  // ── Object properties ─────────────────────────────────────────────────────
  // vertex_id CURIE matches v_rdf_triple.predicate literals
  // ("gftd:follows", "gftd:handle", "rdfs:label", …)
  const objProps = [
    { vid: "gftd:follows",        iri: `${NS}follows`,        functional: false, transitive: false, symmetric: false, inv_functional: false },
    { vid: "gftd:hasBpmnProcess", iri: `${NS}hasBpmnProcess`, functional: false, transitive: false, symmetric: false, inv_functional: false },
    { vid: "gftd:managedBy",      iri: `${NS}managedBy`,      functional: true,  transitive: false, symmetric: false, inv_functional: false },
    { vid: "gftd:memberOf",       iri: `${NS}memberOf`,       functional: false, transitive: false, symmetric: false, inv_functional: false },
  ];
  const dataProps = [
    { vid: "gftd:handle",  iri: `${NS}handle`,         functional: false, transitive: false, symmetric: false, inv_functional: false },
    { vid: "rdfs:label",   iri: `${RDFS_NS}label`,     functional: false, transitive: false, symmetric: false, inv_functional: false },
  ];

  for (const p of objProps) {
    await sql`
      INSERT INTO vertex_owl_property
        (vertex_id, property_iri, property_type, is_functional, is_transitive,
         is_symmetric, is_inverse_functional, profile, source_nsid, created_at)
      VALUES (
        ${p.vid}, ${p.iri}, ${"ObjectProperty"},
        ${p.functional}, ${p.transitive}, ${p.symmetric}, ${p.inv_functional},
        ${PROFILE}, ${SOURCE}, ${now}
      )
    `.execute(db);
  }
  for (const p of dataProps) {
    await sql`
      INSERT INTO vertex_owl_property
        (vertex_id, property_iri, property_type, is_functional, is_transitive,
         is_symmetric, is_inverse_functional, profile, source_nsid, created_at)
      VALUES (
        ${p.vid}, ${p.iri}, ${"DatatypeProperty"},
        ${p.functional}, ${p.transitive}, ${p.symmetric}, ${p.inv_functional},
        ${PROFILE}, ${SOURCE}, ${now}
      )
    `.execute(db);
  }

  // ── Subclass axioms (edge_owl_subclass) ──────────────────────────────────
  // from_vertex_id rdfs:subClassOf to_vertex_id  (CURIEs, matches A-Box)
  const subclasses: [string, string][] = [
    ["gftd:Resource",       "gftd:Thing"],
    ["gftd:Actor",          "gftd:Resource"],
    ["gftd:MagatamaActor",  "gftd:Actor"],
    ["gftd:HumanActor",     "gftd:Actor"],
    ["gftd:OrgActor",       "gftd:Actor"],
    ["gftd:BpmnProcess",    "gftd:Resource"],
    ["gftd:KnowledgeGraph", "gftd:Resource"],
  ];

  for (const [from, to] of subclasses) {
    await sql`
      INSERT INTO edge_owl_subclass (from_vertex_id, to_vertex_id, axiom_type, profile, created_at)
      VALUES (${from}, ${to}, ${"SubClassOf"}, ${PROFILE}, ${now})
    `.execute(db);
  }

  // ── Property domain (edge_owl_property_domain) ───────────────────────────
  // from_vertex_id (property CURIE) → to_vertex_id (domain class CURIE)
  const domains: [string, string][] = [
    ["gftd:follows",        "gftd:Actor"],
    ["gftd:hasBpmnProcess", "gftd:Actor"],
    ["gftd:managedBy",      "gftd:BpmnProcess"],
    ["gftd:memberOf",       "gftd:Actor"],
    ["gftd:handle",         "gftd:Resource"],
    ["rdfs:label",          "gftd:Resource"],
  ];

  for (const [prop, cls] of domains) {
    await sql`
      INSERT INTO edge_owl_property_domain (from_vertex_id, to_vertex_id, profile, created_at)
      VALUES (${prop}, ${cls}, ${PROFILE}, ${now})
    `.execute(db);
  }

  // ── Property range (edge_owl_property_range) ─────────────────────────────
  // from_vertex_id (property CURIE) → to_vertex_id (range class CURIE or xsd:*)
  const ranges: [string, string][] = [
    ["gftd:follows",        "gftd:Actor"],
    ["gftd:hasBpmnProcess", "gftd:BpmnProcess"],
    ["gftd:managedBy",      "gftd:Actor"],
    ["gftd:memberOf",       "gftd:OrgActor"],
    ["gftd:handle",         "xsd:string"],
    ["rdfs:label",          "xsd:string"],
  ];

  for (const [prop, range] of ranges) {
    await sql`
      INSERT INTO edge_owl_property_range (from_vertex_id, to_vertex_id, profile, created_at)
      VALUES (${prop}, ${range}, ${PROFILE}, ${now})
    `.execute(db);
  }

  // ── SHACL Shapes ─────────────────────────────────────────────────────────
  const shapes = [
    {
      vid:             "shacl:ActorShape",
      shape_iri:       `${NS}ActorShape`,
      target_class:    "gftd:Actor",
      constraint_type: "minCount",
      constraint_json: JSON.stringify({ path: "gftd:handle", minCount: 1 }),
      severity:        "Warning",
    },
    {
      vid:             "shacl:BpmnProcessShape",
      shape_iri:       `${NS}BpmnProcessShape`,
      target_class:    "gftd:BpmnProcess",
      constraint_type: "minCount",
      constraint_json: JSON.stringify({ path: "gftd:managedBy", minCount: 1 }),
      severity:        "Info",
    },
    {
      vid:             "shacl:FollowsSymmetryShape",
      shape_iri:       `${NS}FollowsSymmetryShape`,
      target_class:    "gftd:Actor",
      constraint_type: "qualifiedValueShape",
      constraint_json: JSON.stringify({
        path: "gftd:follows",
        qualifiedMinCount: 0,
        qualifiedValueShape: { class: "gftd:Actor" },
      }),
      severity:        "Info",
    },
  ];

  for (const s of shapes) {
    await sql`
      INSERT INTO vertex_shacl_shape
        (vertex_id, shape_iri, target_class, constraint_type, constraint_json,
         severity, source_nsid, enabled, created_at)
      VALUES (
        ${s.vid}, ${s.shape_iri}, ${s.target_class},
        ${s.constraint_type}, ${s.constraint_json}::jsonb,
        ${s.severity}, ${SOURCE}, true, ${now}
      )
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DELETE FROM vertex_shacl_shape      WHERE source_nsid = ${SOURCE}`.execute(db);
  await sql`DELETE FROM edge_owl_property_range WHERE profile = ${PROFILE}`.execute(db);
  await sql`DELETE FROM edge_owl_property_domain WHERE profile = ${PROFILE}`.execute(db);
  await sql`DELETE FROM edge_owl_subclass        WHERE profile = ${PROFILE}`.execute(db);
  await sql`DELETE FROM vertex_owl_property      WHERE profile = ${PROFILE}`.execute(db);
  await sql`DELETE FROM vertex_owl_class         WHERE profile = ${PROFILE}`.execute(db);
}
