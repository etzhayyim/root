//! Read `kg-projector` JSON output and bulk-insert RDF quads into the store.

use std::fs;
use std::path::Path;

use anyhow::{anyhow, Context, Result};
use oxigraph::model::{GraphName, Literal, Quad};
use serde::Deserialize;

use crate::iri::{node_iri, predicate_iri, vocab_iri};
use crate::store::AppStore;

#[derive(Debug, Default)]
pub struct LoadStats {
    pub node_count: usize,
    pub edge_count: usize,
    pub triple_count: usize,
}

#[derive(Debug, Deserialize)]
#[serde(tag = "$type")]
enum KgRecord {
    #[serde(rename = "app.etzhayyim.kg.node")]
    Node(NodeRecord),
    #[serde(rename = "app.etzhayyim.kg.edge")]
    Edge(EdgeRecord),
}

#[derive(Debug, Deserialize)]
struct NodeRecord {
    #[serde(rename = "nodeId")]
    node_id: String,
    #[serde(rename = "nodeType")]
    node_type: String,
    label: Option<String>,
    summary: Option<String>,
    #[serde(default)]
    tags: Vec<String>,
    source: String,
    #[serde(rename = "createdAt")]
    created_at: String,
}

#[derive(Debug, Deserialize)]
struct EdgeRecord {
    subject: String,
    predicate: String,
    object: Option<String>,
    literal: Option<String>,
    weight: Option<f64>,
    context: Option<String>,
    #[serde(rename = "createdAt")]
    created_at: String,
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

fn node_to_quads(rec: &NodeRecord, out: &mut Vec<Quad>) {
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

fn edge_to_quads(rec: &EdgeRecord, out: &mut Vec<Quad>) {
    // K2.a stores every edge as a single triple in the default graph.
    // Edge metadata (weight, context, createdAt) is dropped here because
    // it cannot be attached to a triple without reification, and K2.a
    // does not need it for the smoke queries the SPARQL endpoint serves.
    // K2.b will add `etz:assertedBy` provenance via RDF-star or reification.
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
