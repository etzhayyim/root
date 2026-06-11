//! Read `kg-projector` JSON output and bulk-insert RDF quads into the store.
//!
//! Two ingestion surfaces are exposed:
//!   - [`load_projection`] — bulk-load every record under a directory layout
//!     (`<dir>/nodes/*.json` + `<dir>/edges/*.json`). Used for K2.a cold-start
//!     and for `--kg-out` smoke tests.
//!   - [`apply_record_value`] / [`remove_node`] / [`remove_edge_by_key`] —
//!     single-record primitives consumed by K2.c (Jetstream firehose) and
//!     K3.a (snapshot bundle replay).

use std::fs;
use std::path::Path;

use anyhow::{anyhow, Context, Result};
use oxigraph::model::{GraphName, Literal, NamedNodeRef, Quad, QuadRef, Subject, SubjectRef, Term, TermRef};
use serde::Deserialize;
use serde_json::Value;

use crate::iri::{node_iri, predicate_iri, vocab_iri};
use crate::store::AppStore;

#[derive(Debug, Default)]
pub struct LoadStats {
    pub node_count: usize,
    pub edge_count: usize,
    pub triple_count: usize,
}

impl LoadStats {
    pub fn add(&mut self, other: &LoadStats) {
        self.node_count += other.node_count;
        self.edge_count += other.edge_count;
        self.triple_count += other.triple_count;
    }
}

#[derive(Debug, Deserialize)]
#[serde(tag = "$type")]
pub enum KgRecord {
    #[serde(rename = "com.etzhayyim.kg.node")]
    Node(NodeRecord),
    #[serde(rename = "com.etzhayyim.kg.edge")]
    Edge(EdgeRecord),
}

#[derive(Debug, Deserialize)]
pub struct NodeRecord {
    #[serde(rename = "nodeId")]
    pub node_id: String,
    #[serde(rename = "nodeType")]
    pub node_type: String,
    pub label: Option<String>,
    pub summary: Option<String>,
    #[serde(default)]
    pub tags: Vec<String>,
    pub source: String,
    #[serde(rename = "createdAt")]
    pub created_at: String,
}

#[derive(Debug, Deserialize)]
pub struct EdgeRecord {
    pub subject: String,
    pub predicate: String,
    pub object: Option<String>,
    pub literal: Option<String>,
    pub weight: Option<f64>,
    pub context: Option<String>,
    #[serde(rename = "createdAt")]
    pub created_at: String,
}

pub fn load_projection(app: &AppStore, out_dir: &Path) -> Result<LoadStats> {
    let mut stats = LoadStats::default();
    let mut quads: Vec<Quad> = Vec::with_capacity(16_384);

    let nodes_dir = out_dir.join("nodes");
    for entry in fs::read_dir(&nodes_dir)
        .with_context(|| format!("reading nodes dir {}", nodes_dir.display()))?
    {
        let entry = entry?;
        let path = entry.path();
        if path.extension().and_then(|s| s.to_str()) != Some("json") {
            continue;
        }
        let body = fs::read_to_string(&path)
            .with_context(|| format!("reading {}", path.display()))?;
        let rec: KgRecord = serde_json::from_str(&body)
            .with_context(|| format!("parsing {}", path.display()))?;
        match rec {
            KgRecord::Node(n) => {
                node_to_quads(&n, &mut quads);
                stats.node_count += 1;
            }
            KgRecord::Edge(_) => {
                return Err(anyhow!("edge record found in nodes/: {}", path.display()));
            }
        }
    }

    let edges_dir = out_dir.join("edges");
    for entry in fs::read_dir(&edges_dir)
        .with_context(|| format!("reading edges dir {}", edges_dir.display()))?
    {
        let entry = entry?;
        let path = entry.path();
        if path.extension().and_then(|s| s.to_str()) != Some("json") {
            continue;
        }
        let body = fs::read_to_string(&path)
            .with_context(|| format!("reading {}", path.display()))?;
        let rec: KgRecord = serde_json::from_str(&body)
            .with_context(|| format!("parsing {}", path.display()))?;
        match rec {
            KgRecord::Edge(e) => {
                edge_to_quads(&e, &mut quads);
                stats.edge_count += 1;
            }
            KgRecord::Node(_) => {
                return Err(anyhow!("node record found in edges/: {}", path.display()));
            }
        }
    }

    for q in &quads {
        app.store
            .insert(q.as_ref())
            .with_context(|| "inserting quad into store")?;
    }
    stats.triple_count = quads.len();
    Ok(stats)
}

/// Apply a single parsed kg.node / kg.edge JSON value to the store. Returns
/// the number of triples inserted. Idempotent: a re-applied node first
/// retracts its old triples (matched by nodeId IRI) so updates land cleanly;
/// edges are append-only here, callers wanting "update" semantics should
/// remove the matching edge first via [`remove_edge_by_key`].
pub fn apply_record_value(app: &AppStore, value: &Value) -> Result<ApplyOutcome> {
    let rec: KgRecord = serde_json::from_value(value.clone())
        .context("parsing $type-tagged kg record")?;

    match rec {
        KgRecord::Node(node) => {
            remove_node(app, &node.node_id)?;
            let mut quads = Vec::with_capacity(8);
            node_to_quads(&node, &mut quads);
            for q in &quads {
                app.store.insert(q.as_ref())?;
            }
            Ok(ApplyOutcome::Node {
                node_id: node.node_id,
                triples: quads.len(),
            })
        }
        KgRecord::Edge(edge) => {
            // Edges aren't keyed by themselves; the projector emits one rkey
            // per (subject, predicate, object|literal). Caller may dedupe
            // ahead of time. Insert as-is.
            let mut quads = Vec::with_capacity(1);
            edge_to_quads(&edge, &mut quads);
            for q in &quads {
                app.store.insert(q.as_ref())?;
            }
            Ok(ApplyOutcome::Edge {
                subject: edge.subject,
                predicate: edge.predicate,
                triples: quads.len(),
            })
        }
    }
}

#[derive(Debug)]
pub enum ApplyOutcome {
    Node { node_id: String, triples: usize },
    Edge {
        subject: String,
        predicate: String,
        triples: usize,
    },
}

/// Retract only the node's *metadata* triples (those with `etzv:*`
/// predicates: nodeType / label / summary / tag / source / createdAt).
/// Edge triples emanating from the same subject (`etzp:*`) are kept;
/// otherwise re-applying a node would wipe its outgoing edges every
/// time the snapshot bundle interleaves node and edge records.
pub fn remove_node(app: &AppStore, node_id: &str) -> Result<usize> {
    let subject_iri = node_iri(node_id);
    let subject_ref: SubjectRef = SubjectRef::NamedNode(subject_iri.as_ref());
    let to_remove: Vec<Quad> = app
        .store
        .quads_for_pattern(Some(subject_ref), None, None, None)
        .filter_map(|q| q.ok())
        .filter(|q| q.predicate.as_str().starts_with(crate::iri::VOCAB_PREFIX))
        .collect();
    for q in &to_remove {
        app.store.remove(q.as_ref())?;
    }
    Ok(to_remove.len())
}

/// Retract a specific edge triple keyed by (subject, predicate, object|literal).
/// Returns the number of triples removed (0 or 1 in normal use).
pub fn remove_edge_by_key(
    app: &AppStore,
    subject: &str,
    predicate: &str,
    object_or_literal: Either<&str, &str>,
) -> Result<usize> {
    let subject_iri = node_iri(subject);
    let predicate_iri_v = predicate_iri(predicate);
    let object_term: Term = match object_or_literal {
        Either::Left(obj) => Term::NamedNode(node_iri(obj)),
        Either::Right(lit) => Term::Literal(Literal::new_simple_literal(lit)),
    };
    let q = Quad::new(
        subject_iri,
        predicate_iri_v,
        object_term,
        GraphName::DefaultGraph,
    );
    let removed = app.store.remove(q.as_ref())?;
    Ok(if removed { 1 } else { 0 })
}

/// Tiny stand-in for `Either` so callers don't pull in a crate.
#[derive(Debug)]
pub enum Either<L, R> {
    Left(L),
    Right(R),
}

pub(crate) fn node_to_quads(rec: &NodeRecord, out: &mut Vec<Quad>) {
    let subject = node_iri(&rec.node_id);

    out.push(Quad::new(
        subject.clone(),
        vocab_iri("nodeType"),
        Literal::new_simple_literal(&rec.node_type),
        GraphName::DefaultGraph,
    ));
    if let Some(label) = &rec.label {
        out.push(Quad::new(
            subject.clone(),
            vocab_iri("label"),
            Literal::new_simple_literal(label),
            GraphName::DefaultGraph,
        ));
    }
    if let Some(summary) = &rec.summary {
        out.push(Quad::new(
            subject.clone(),
            vocab_iri("summary"),
            Literal::new_simple_literal(summary),
            GraphName::DefaultGraph,
        ));
    }
    for tag in &rec.tags {
        out.push(Quad::new(
            subject.clone(),
            vocab_iri("tag"),
            Literal::new_simple_literal(tag),
            GraphName::DefaultGraph,
        ));
    }
    out.push(Quad::new(
        subject.clone(),
        vocab_iri("source"),
        Literal::new_simple_literal(&rec.source),
        GraphName::DefaultGraph,
    ));
    out.push(Quad::new(
        subject,
        vocab_iri("createdAt"),
        Literal::new_simple_literal(&rec.created_at),
        GraphName::DefaultGraph,
    ));
}

pub(crate) fn edge_to_quads(rec: &EdgeRecord, out: &mut Vec<Quad>) {
    // K2.a stores every edge as a single triple in the default graph.
    // Edge metadata (weight, context, createdAt) is dropped because it
    // cannot be attached to a triple without reification, and the smoke
    // queries don't need it. K2+ that needs provenance can layer RDF-star
    // on top.
    let _ = rec.weight;
    let _ = rec.context;
    let _ = rec.created_at;

    let subject = node_iri(&rec.subject);
    let predicate = predicate_iri(&rec.predicate);

    if let Some(obj) = &rec.object {
        out.push(Quad::new(
            subject,
            predicate,
            node_iri(obj),
            GraphName::DefaultGraph,
        ));
    } else if let Some(lit) = &rec.literal {
        out.push(Quad::new(
            subject,
            predicate,
            Literal::new_simple_literal(lit),
            GraphName::DefaultGraph,
        ));
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn new_store() -> AppStore {
        AppStore::new().expect("memory store")
    }

    #[test]
    fn apply_node_then_query_back() {
        let app = new_store();
        let value = serde_json::json!({
            "$type": "com.etzhayyim.kg.node",
            "nodeId": "urn:adr:2605190900-kg-as-lexicon-ipld-oxigraph-appview",
            "nodeType": "adr",
            "label": "ADR-2605190900",
            "tags": ["status:proposed"],
            "source": "adr-frontmatter",
            "createdAt": "2026-05-19T00:00:00.000Z"
        });
        let outcome = apply_record_value(&app, &value).expect("apply");
        match outcome {
            ApplyOutcome::Node { triples, .. } => {
                assert!(triples >= 4, "expected at least 4 triples, got {triples}");
            }
            _ => panic!("expected Node outcome"),
        }
        let results = app
            .store
            .query("SELECT (COUNT(*) AS ?c) WHERE { ?s ?p ?o }")
            .expect("query");
        // Smoke check: store has triples now.
        match results {
            oxigraph::sparql::QueryResults::Solutions(mut it) => {
                let row = it.next().expect("row").expect("solution");
                let c = row.get("c").expect("c binding");
                let term_string = c.to_string();
                assert!(term_string.contains('5') || term_string.contains('6'),
                    "expected 5 or 6 triples, got {term_string}");
            }
            _ => panic!("expected solutions"),
        }
    }

    #[test]
    fn apply_edge_creates_one_triple() {
        let app = new_store();
        let value = serde_json::json!({
            "$type": "com.etzhayyim.kg.edge",
            "subject": "urn:adr:2605190900-x",
            "predicate": "depends_on",
            "object": "urn:adr:2605172000-y",
            "createdAt": "2026-05-19T00:00:00.000Z"
        });
        let outcome = apply_record_value(&app, &value).expect("apply");
        match outcome {
            ApplyOutcome::Edge { triples, .. } => assert_eq!(triples, 1),
            _ => panic!("expected Edge outcome"),
        }
    }

    #[test]
    fn applying_node_twice_does_not_double_triples() {
        let app = new_store();
        let value = serde_json::json!({
            "$type": "com.etzhayyim.kg.node",
            "nodeId": "urn:adr:test",
            "nodeType": "adr",
            "source": "adr-frontmatter",
            "createdAt": "2026-05-19T00:00:00.000Z"
        });
        let _ = apply_record_value(&app, &value).expect("first apply");
        let _ = apply_record_value(&app, &value).expect("second apply");
        let results = app
            .store
            .query("SELECT (COUNT(*) AS ?c) WHERE { ?s ?p ?o }")
            .expect("query");
        if let oxigraph::sparql::QueryResults::Solutions(mut it) = results {
            let row = it.next().unwrap().unwrap();
            let c = row.get("c").unwrap().to_string();
            // Should be exactly 3 triples (nodeType + source + createdAt),
            // not 6 — i.e. the second apply replaced rather than appended.
            assert!(c.contains("\"3\""), "expected 3 triples, got {c}");
        }
    }
}

// Silence unused import warnings — kept available for K2+ helpers that
// will reach into these types.
#[allow(dead_code)]
fn _silence_unused() {
    let _ = std::marker::PhantomData::<(NamedNodeRef<'_>, QuadRef<'_>, TermRef<'_>, Subject)>;
}
