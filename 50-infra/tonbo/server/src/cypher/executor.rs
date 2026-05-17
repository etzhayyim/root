/// Tonbo-native Cypher executor.
///
/// Bypasses DataFusion SQL entirely: uses Lance Dataset::scan() directly with
/// Arrow filter expressions. BFS traversal runs as an in-process async loop
/// (zero network round trips per hop).
///
/// # Layer mapping (JanusGraph-on-Arrow)
///
/// Layer 1 — entity_nodes_current: typed columns (id_curie, types, label, …)
/// Layer 2 — entity_graph_edges_current obj_kind='literal': domain properties
/// Layer 3 — entity_graph_adj_current: BFS adjacency projection
use std::collections::{HashMap, HashSet};
use std::sync::Arc;

use arrow::array::{Array, Float64Array, ListArray, StringArray};
use arrow::record_batch::RecordBatch;
use futures::TryStreamExt;
use lance::Dataset;
use serde_json::{Map, Value};

use crate::context::TonboContext;

use super::ast::*;

// ── table names ───────────────────────────────────────────────────────────────

const TABLE_NODES: &str = "entity_nodes_current";
const TABLE_EDGES: &str = "entity_graph_edges_current";
const TABLE_ADJ: &str = "entity_graph_adj_current";

/// Columns that live in entity_nodes_current as typed Arrow columns.
/// Everything else is a Layer 2 literal edge property.
const NODE_TYPED_COLS: &[&str] = &[
    "_doc_id", "org_id", "user_id", "actor_id",
    "id_iri", "id_curie", "ns_prefix", "local_id",
    "types", "graph_name", "label", "description",
    "jsonld_json", "source_url",
    "created_at", "updated_at", "ingested_at",
];

fn is_node_typed_col(col: &str) -> bool {
    NODE_TYPED_COLS.contains(&col)
}

// ── result types ──────────────────────────────────────────────────────────────

#[derive(Debug, Default)]
pub struct CypherResult {
    pub fields: Vec<String>,
    pub values: Vec<Vec<Value>>,
}

// ── multi-variable row ────────────────────────────────────────────────────────

/// A single matched path row — maps variable name → NodeRow / EdgeRow.
#[derive(Debug, Default, Clone)]
struct MatchedRow {
    nodes: HashMap<String, NodeRow>,
    edges: HashMap<String, EdgeRow>,
}

// ── engine ────────────────────────────────────────────────────────────────────

pub struct CypherEngine {
    ctx: Arc<TonboContext>,
}

impl CypherEngine {
    pub fn new(ctx: Arc<TonboContext>) -> Self {
        Self { ctx }
    }

    pub async fn execute(
        &self,
        q: &Query,
        org_id: &str,
        params: &HashMap<String, Value>,
    ) -> Result<CypherResult, Box<dyn std::error::Error + Send + Sync>> {
        let m = q.r#match.as_ref().ok_or("missing MATCH clause")?;
        if m.patterns.is_empty() {
            return Ok(CypherResult::default());
        }
        // single pattern only (first); multiple patterns unsupported for now
        let pat = &m.patterns[0];

        // ── 1. resolve start node set ────────────────────────────────────
        let mut rows = self
            .resolve_start_rows(&pat.start, q.r#where.as_ref(), org_id, params)
            .await?;

        // ── 2. traverse edge steps ───────────────────────────────────────
        let mut src_var = pat.start.variable.clone();
        for step in &pat.steps {
            rows = self
                .exec_step_rows(step, rows, &src_var, q.r#where.as_ref(), org_id, params)
                .await?;
            src_var = step.end.variable.clone();
        }

        // ── 3. collect literal props needed for RETURN / ORDER BY ─────────
        let lit_props = self
            .fetch_lit_props(
                q.r#return.as_ref(),
                q.order_by.as_ref(),
                &rows,
                org_id,
            )
            .await?;

        // ── 4. build result ───────────────────────────────────────────────
        let result = build_result(
            q.r#return.as_ref(),
            q.order_by.as_ref(),
            &rows,
            &lit_props,
            q.skip as usize,
            q.limit as usize,
        );
        Ok(result)
    }

    // ── node resolution (shared: start + end nodes) ───────────────────────────

    /// Resolve nodes with label filters, inline props, typed WHERE predicates,
    /// and literal predicate AND-intersection applied.
    /// `candidate_ids`: None = no ID constraint (start node scan);
    ///                  Some = constrain to these IDs (end node after edge step).
    async fn resolve_nodes(
        &self,
        np: &NodePattern,
        candidate_ids: Option<&HashSet<String>>,
        where_clause: Option<&WhereClause>,
        org_id: &str,
        params: &HashMap<String, Value>,
    ) -> Result<Vec<NodeRow>, Box<dyn std::error::Error + Send + Sync>> {
        let var = &np.variable;

        // collect WHERE predicates scoped to this variable
        let preds: Vec<&Predicate> = where_clause
            .map(|w| {
                w.predicates
                    .iter()
                    .filter(|p| p.variable.is_empty() || &p.variable == var)
                    .collect()
            })
            .unwrap_or_default();

        // split: typed column predicates vs literal edge predicates
        let (typed_preds, lit_preds): (Vec<&&Predicate>, Vec<&&Predicate>) =
            preds.iter().partition(|p| {
                p.op == "HAS_LABEL" || is_node_typed_col(&p.property)
            });

        // ── Layer 1: node table filter ───────────────────────────────────
        let mut filter_parts: Vec<String> = vec![format!("org_id = '{}'", sql_esc(org_id))];

        // candidate_ids constraint (end node)
        if let Some(ids) = candidate_ids {
            if ids.is_empty() {
                return Ok(vec![]);
            }
            filter_parts.push(format!(
                "id_curie IN ({})",
                ids_to_in_list(&ids.iter().cloned().collect::<Vec<_>>())
            ));
        }

        // label filters from node pattern
        for lbl in &np.labels {
            filter_parts.push(types_like_filter(lbl));
        }

        // inline props
        for (k, v) in &np.props {
            if is_node_typed_col(k) {
                if let Some(cond) = scalar_cond(k, "=", v) {
                    filter_parts.push(cond);
                }
            }
        }

        // typed WHERE predicates
        for p in &typed_preds {
            if p.op == "HAS_LABEL" {
                if let PredicateValue::Str(lbl) = &p.value {
                    filter_parts.push(types_like_filter(lbl));
                }
            } else if let Some(resolved) = p.value.resolve(params) {
                if let Some(cond) = scalar_cond(&p.property, &p.op, &resolved) {
                    filter_parts.push(cond);
                }
            }
        }

        // ── Layer 2: literal edge AND-intersection ───────────────────────
        let lit_id_sets = self
            .resolve_literal_preds(&lit_preds, org_id, params)
            .await?;

        let mut node_id_filter: Option<HashSet<String>> = None;
        for id_set in lit_id_sets {
            node_id_filter = Some(match node_id_filter {
                None => id_set,
                Some(existing) => existing.intersection(&id_set).cloned().collect(),
            });
        }

        // if literal preds returned empty intersection, short-circuit
        if let Some(ref ids) = node_id_filter {
            if ids.is_empty() {
                return Ok(vec![]);
            }
        }

        // add id_curie IN (...) filter if we have a literal pred intersection
        if let Some(ref ids) = node_id_filter {
            // intersect with candidate_ids already applied above; just append
            filter_parts.push(format!(
                "id_curie IN ({})",
                ids_to_in_list(&ids.iter().cloned().collect::<Vec<_>>())
            ));
        }

        let filter = filter_parts.join(" AND ");
        self.scan_nodes(org_id, &filter).await
    }

    /// Resolve start nodes → Vec<MatchedRow>, one per start node.
    async fn resolve_start_rows(
        &self,
        np: &NodePattern,
        where_clause: Option<&WhereClause>,
        org_id: &str,
        params: &HashMap<String, Value>,
    ) -> Result<Vec<MatchedRow>, Box<dyn std::error::Error + Send + Sync>> {
        let nodes = self
            .resolve_nodes(np, None, where_clause, org_id, params)
            .await?;
        let var = np.variable.clone();
        Ok(nodes
            .into_iter()
            .map(|n| {
                let mut row = MatchedRow::default();
                row.nodes.insert(var.clone(), n);
                row
            })
            .collect())
    }

    // ── step execution ────────────────────────────────────────────────────────

    async fn exec_step_rows(
        &self,
        step: &PathStep,
        src_rows: Vec<MatchedRow>,
        src_var: &str,
        where_clause: Option<&WhereClause>,
        org_id: &str,
        params: &HashMap<String, Value>,
    ) -> Result<Vec<MatchedRow>, Box<dyn std::error::Error + Send + Sync>> {
        let rel = &step.rel;
        let end_np = &step.end;

        // variable-length (BFS)
        if rel.max_hops != 1 || rel.min_hops != 1 {
            return self
                .exec_bfs_step_rows(step, src_rows, src_var, where_clause, org_id, params)
                .await;
        }

        // collect unique src node IDs from current rows
        let src_ids: Vec<String> = src_rows
            .iter()
            .filter_map(|row| row.nodes.get(src_var))
            .map(|n| n.id_curie.clone())
            .collect::<HashSet<_>>()
            .into_iter()
            .collect();

        if src_ids.is_empty() {
            return Ok(vec![]);
        }

        // query edge table
        let (src_col, _dst_col) = match rel.direction.as_str() {
            "in" => ("dst_id", "src_id"),
            _ => ("src_id", "dst_id"),
        };

        let in_list = ids_to_in_list(&src_ids);
        let mut edge_filter_parts = vec![
            format!("org_id = '{}'", sql_esc(org_id)),
            format!("{} IN ({})", src_col, in_list),
            "obj_kind = 'node'".to_string(),
            "(valid_to IS NULL OR valid_to = '')".to_string(),
        ];

        // multi-type OR filter (fix: single pass, no pop+push bug)
        if !rel.types.is_empty() {
            if rel.types.len() == 1 {
                edge_filter_parts.push(format!(
                    "predicate_curie = '{}'",
                    sql_esc(&rel.types[0])
                ));
            } else {
                let type_list = rel
                    .types
                    .iter()
                    .map(|t| format!("'{}'", sql_esc(t)))
                    .collect::<Vec<_>>()
                    .join(", ");
                edge_filter_parts.push(format!("predicate_curie IN ({})", type_list));
            }
        }

        let edge_filter = edge_filter_parts.join(" AND ");
        let ds_edges = self.ctx.get_lance_dataset(TABLE_EDGES).await?;
        let edge_cols = &[
            "src_id", "dst_id", "predicate_curie", "predicate_label",
            "weight", "props_json", "valid_from", "valid_to",
        ];
        let edge_batches = scan_dataset(&ds_edges, &edge_filter, edge_cols).await?;
        let edges: Vec<EdgeRow> = batches_to_edge_rows(&edge_batches);

        // build src_id → Vec<EdgeRow> map
        let mut src_to_edges: HashMap<String, Vec<EdgeRow>> = HashMap::new();
        for edge in edges {
            let key = if rel.direction.as_str() == "in" {
                edge.dst_id.clone()
            } else {
                edge.src_id.clone()
            };
            src_to_edges.entry(key).or_default().push(edge);
        }

        // collect candidate end-node IDs
        let candidate_ids: HashSet<String> = src_to_edges
            .values()
            .flat_map(|evec| evec.iter().map(|e| {
                if rel.direction.as_str() == "in" {
                    e.src_id.clone()
                } else {
                    e.dst_id.clone()
                }
            }))
            .collect();

        if candidate_ids.is_empty() {
            return Ok(vec![]);
        }

        // resolve end nodes with WHERE applied
        let end_nodes = self
            .resolve_nodes(end_np, Some(&candidate_ids), where_clause, org_id, params)
            .await?;

        // build end_id → NodeRow map
        let end_node_map: HashMap<String, NodeRow> = end_nodes
            .into_iter()
            .map(|n| (n.id_curie.clone(), n))
            .collect();

        let end_var = end_np.variable.clone();

        // expand: src_row × matching_edge × matching_end_node → new MatchedRow
        let mut result_rows: Vec<MatchedRow> = Vec::new();
        for src_row in &src_rows {
            let src_node = match src_row.nodes.get(src_var) {
                Some(n) => n,
                None => continue,
            };
            let src_id = &src_node.id_curie;
            let matching_edges = match src_to_edges.get(src_id) {
                Some(evec) => evec,
                None => continue,
            };
            for edge in matching_edges {
                let end_id = if rel.direction.as_str() == "in" {
                    &edge.src_id
                } else {
                    &edge.dst_id
                };
                if let Some(end_node) = end_node_map.get(end_id) {
                    let mut new_row = src_row.clone();
                    new_row.nodes.insert(end_var.clone(), end_node.clone());
                    if !rel.variable.is_empty() {
                        new_row.edges.insert(rel.variable.clone(), edge.clone());
                    }
                    result_rows.push(new_row);
                }
            }
        }

        Ok(result_rows)
    }

    async fn exec_bfs_step_rows(
        &self,
        step: &PathStep,
        src_rows: Vec<MatchedRow>,
        src_var: &str,
        where_clause: Option<&WhereClause>,
        org_id: &str,
        params: &HashMap<String, Value>,
    ) -> Result<Vec<MatchedRow>, Box<dyn std::error::Error + Send + Sync>> {
        let rel = &step.rel;
        let min_hops = rel.min_hops.max(1) as usize;
        let max_hops = if rel.max_hops < 0 { 10usize } else { rel.max_hops as usize };

        let mut frontier: HashSet<String> = src_rows
            .iter()
            .filter_map(|row| row.nodes.get(src_var))
            .map(|n| n.id_curie.clone())
            .collect();
        let mut visited: HashSet<String> = frontier.clone();
        let mut result_ids: HashSet<String> = HashSet::new();

        let adj_col = match rel.direction.as_str() {
            "in" => "in_ids",
            _ => "out_ids",
        };

        let ds_adj = self.ctx.get_lance_dataset(TABLE_ADJ).await?;

        for depth in 1..=max_hops {
            if frontier.is_empty() {
                break;
            }
            let in_list = ids_to_in_list(&frontier.iter().cloned().collect::<Vec<_>>());
            let filter = format!(
                "org_id = '{}' AND node_id IN ({})",
                sql_esc(org_id),
                in_list
            );
            let batches = scan_dataset(&ds_adj, &filter, &["node_id", adj_col]).await?;

            let mut next_frontier = HashSet::new();
            for batch in &batches {
                let list_col = batch.column_by_name(adj_col);
                if let Some(col) = list_col {
                    if let Some(list_arr) = col.as_any().downcast_ref::<ListArray>() {
                        for i in 0..list_arr.len() {
                            if list_arr.is_null(i) {
                                continue;
                            }
                            let inner = list_arr.value(i);
                            if let Some(str_arr) = inner.as_any().downcast_ref::<StringArray>() {
                                for j in 0..str_arr.len() {
                                    if !str_arr.is_null(j) {
                                        let id = str_arr.value(j).to_string();
                                        if !visited.contains(&id) {
                                            visited.insert(id.clone());
                                            next_frontier.insert(id.clone());
                                        }
                                        if depth >= min_hops {
                                            result_ids.insert(id);
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            frontier = next_frontier;
        }

        if result_ids.is_empty() {
            return Ok(vec![]);
        }

        // resolve end nodes with WHERE applied
        let end_nodes = self
            .resolve_nodes(&step.end, Some(&result_ids), where_clause, org_id, params)
            .await?;

        if end_nodes.is_empty() {
            return Ok(vec![]);
        }

        let end_var = step.end.variable.clone();

        // BFS doesn't track individual paths — cartesian product of src_rows × end_nodes
        let mut result_rows: Vec<MatchedRow> = Vec::new();
        for src_row in &src_rows {
            for end_node in &end_nodes {
                let mut new_row = src_row.clone();
                new_row.nodes.insert(end_var.clone(), end_node.clone());
                result_rows.push(new_row);
            }
        }

        Ok(result_rows)
    }

    // ── helpers ───────────────────────────────────────────────────────────────

    async fn scan_nodes(
        &self,
        _org_id: &str,
        filter: &str,
    ) -> Result<Vec<NodeRow>, Box<dyn std::error::Error + Send + Sync>> {
        let ds = self.ctx.get_lance_dataset(TABLE_NODES).await?;
        let cols = &[
            "id_curie", "id_iri", "types", "label", "description",
            "graph_name", "source_url", "created_at", "updated_at",
        ];
        let batches = scan_dataset(&ds, filter, cols).await?;
        Ok(batches_to_node_rows(&batches))
    }

    /// Layer 2: for each literal predicate, query the edge table and return src_id sets.
    /// Batched: single scan with OR groups per predicate to avoid N serial scans.
    async fn resolve_literal_preds(
        &self,
        preds: &[&&Predicate],
        org_id: &str,
        params: &HashMap<String, Value>,
    ) -> Result<Vec<HashSet<String>>, Box<dyn std::error::Error + Send + Sync>> {
        if preds.is_empty() {
            return Ok(vec![]);
        }

        // Build OR groups: (predicate_curie = 'p1' AND lit_value ...) OR ...
        let mut or_groups: Vec<String> = Vec::new();
        // Track which predicates appear in which order for result grouping
        let mut pred_keys: Vec<String> = Vec::new();

        for pred in preds {
            let resolved = match pred.value.resolve(params) {
                Some(v) => v,
                None => continue,
            };
            let value_cond = match lit_value_cond(&pred.op, &resolved) {
                Some(c) => c,
                None => continue,
            };
            or_groups.push(format!(
                "(predicate_curie = '{}' AND {})",
                sql_esc(&pred.property),
                value_cond
            ));
            pred_keys.push(pred.property.clone());
        }

        if or_groups.is_empty() {
            return Ok(vec![]);
        }

        let filter = format!(
            "org_id = '{}' AND obj_kind = 'literal' AND (valid_to IS NULL OR valid_to = '') AND ({})",
            sql_esc(org_id),
            or_groups.join(" OR ")
        );

        let ds = self.ctx.get_lance_dataset(TABLE_EDGES).await?;
        let batches = scan_dataset(&ds, &filter, &["src_id", "predicate_curie"]).await?;

        // Group src_ids by predicate_curie in memory
        let mut pred_to_ids: HashMap<String, HashSet<String>> = HashMap::new();
        for batch in &batches {
            let src_col = batch.column_by_name("src_id");
            let pred_col = batch.column_by_name("predicate_curie");
            if let (Some(src), Some(pred_arr)) = (src_col, pred_col) {
                if let (Some(src_arr), Some(pred_str_arr)) = (
                    src.as_any().downcast_ref::<StringArray>(),
                    pred_arr.as_any().downcast_ref::<StringArray>(),
                ) {
                    for i in 0..src_arr.len() {
                        if !src_arr.is_null(i) && !pred_str_arr.is_null(i) {
                            pred_to_ids
                                .entry(pred_str_arr.value(i).to_string())
                                .or_default()
                                .insert(src_arr.value(i).to_string());
                        }
                    }
                }
            }
        }

        // Return sets in the same order as pred_keys (one set per predicate)
        let sets: Vec<HashSet<String>> = pred_keys
            .iter()
            .map(|k| pred_to_ids.remove(k).unwrap_or_default())
            .collect();

        Ok(sets)
    }

    /// Bulk-fetch literal properties for RETURN / ORDER BY items.
    /// Single batched scan: predicate_curie IN (...) AND src_id IN (...).
    /// Returns map[node_id → map[prop_name → lit_value]].
    async fn fetch_lit_props(
        &self,
        ret: Option<&ReturnClause>,
        ob: Option<&OrderByClause>,
        rows: &[MatchedRow],
        org_id: &str,
    ) -> Result<LitPropMap, Box<dyn std::error::Error + Send + Sync>> {
        // Collect all (variable, property) pairs that need literal props
        let mut var_props: HashMap<String, HashSet<String>> = HashMap::new();

        if let Some(r) = ret {
            for item in &r.items {
                if !item.property.is_empty() && !is_node_typed_col(&item.property) {
                    var_props
                        .entry(item.variable.clone())
                        .or_default()
                        .insert(item.property.clone());
                }
            }
        }
        if let Some(o) = ob {
            for item in &o.items {
                if !item.property.is_empty() && !is_node_typed_col(&item.property) {
                    var_props
                        .entry(item.variable.clone())
                        .or_default()
                        .insert(item.property.clone());
                }
            }
        }

        if var_props.is_empty() || rows.is_empty() {
            return Ok(HashMap::new());
        }

        // Collect all domain props and all node IDs across all variables
        let mut all_props: HashSet<String> = HashSet::new();
        for props in var_props.values() {
            all_props.extend(props.iter().cloned());
        }

        let mut all_node_ids: HashSet<String> = HashSet::new();
        for row in rows {
            for node in row.nodes.values() {
                all_node_ids.insert(node.id_curie.clone());
            }
        }

        if all_props.is_empty() || all_node_ids.is_empty() {
            return Ok(HashMap::new());
        }

        let prop_in_list = all_props
            .iter()
            .map(|p| format!("'{}'", sql_esc(p)))
            .collect::<Vec<_>>()
            .join(", ");
        let node_in_list = ids_to_in_list(&all_node_ids.iter().cloned().collect::<Vec<_>>());

        let filter = format!(
            "org_id = '{}' AND predicate_curie IN ({}) AND obj_kind = 'literal' AND (valid_to IS NULL OR valid_to = '') AND src_id IN ({})",
            sql_esc(org_id),
            prop_in_list,
            node_in_list
        );

        let ds = self.ctx.get_lance_dataset(TABLE_EDGES).await?;
        let batches = scan_dataset(&ds, &filter, &["src_id", "predicate_curie", "lit_value"]).await?;

        let mut lit_props: LitPropMap = HashMap::new();
        for batch in &batches {
            let src_col = batch.column_by_name("src_id");
            let pred_col = batch.column_by_name("predicate_curie");
            let val_col = batch.column_by_name("lit_value");
            if let (Some(src), Some(pred_arr), Some(val)) = (src_col, pred_col, val_col) {
                if let (Some(src_arr), Some(pred_str_arr), Some(val_arr)) = (
                    src.as_any().downcast_ref::<StringArray>(),
                    pred_arr.as_any().downcast_ref::<StringArray>(),
                    val.as_any().downcast_ref::<StringArray>(),
                ) {
                    for i in 0..src_arr.len() {
                        if !src_arr.is_null(i) && !pred_str_arr.is_null(i) && !val_arr.is_null(i) {
                            lit_props
                                .entry(src_arr.value(i).to_string())
                                .or_default()
                                .insert(
                                    pred_str_arr.value(i).to_string(),
                                    val_arr.value(i).to_string(),
                                );
                        }
                    }
                }
            }
        }

        Ok(lit_props)
    }
}

// ── TonboContext extension ────────────────────────────────────────────────────
// (implemented in context.rs via get_lance_dataset — this trait just documents usage)

// ── result building ───────────────────────────────────────────────────────────

type LitPropMap = HashMap<String, HashMap<String, String>>;

fn build_result(
    ret: Option<&ReturnClause>,
    ob: Option<&OrderByClause>,
    rows: &[MatchedRow],
    lit_props: &LitPropMap,
    skip: usize,
    limit: usize,
) -> CypherResult {
    let items: Vec<&ReturnItem> = ret
        .map(|r| r.items.iter().collect())
        .unwrap_or_default();

    if items.is_empty() {
        return CypherResult::default();
    }

    // field names
    let fields: Vec<String> = items
        .iter()
        .map(|item| {
            if !item.alias.is_empty() {
                item.alias.clone()
            } else if !item.property.is_empty() {
                format!("{}.{}", item.variable, item.property)
            } else {
                item.variable.clone()
            }
        })
        .collect();

    let empty_node_props: HashMap<String, String> = HashMap::new();

    // collect rows
    let mut result_rows: Vec<(Vec<Value>, SortKey)> = rows
        .iter()
        .map(|matched_row| {
            let sort_key = sort_key_for_row(matched_row, lit_props, ob);

            let vals: Vec<Value> = items
                .iter()
                .map(|item| {
                    // edge variable reference (r.property)
                    if let Some(edge) = matched_row.edges.get(&item.variable) {
                        if item.property.is_empty() {
                            return Value::Null; // RETURN r whole-object not supported
                        }
                        return edge.to_map()
                            .get(item.property.as_str())
                            .cloned()
                            .unwrap_or(Value::Null);
                    }

                    // node variable reference
                    let node = match matched_row.nodes.get(&item.variable) {
                        Some(n) => n,
                        None => return Value::Null,
                    };
                    let node_map = node.to_map();
                    let node_lit = lit_props
                        .get(&node.id_curie)
                        .unwrap_or(&empty_node_props);

                    if item.property.is_empty() {
                        // RETURN n — Neo4j v2 wire format: {elementId, labels, properties}
                        node.to_neo4j_element(&node_map, node_lit)
                    } else if is_node_typed_col(&item.property) {
                        node_map
                            .get(&item.property)
                            .cloned()
                            .unwrap_or(Value::Null)
                    } else {
                        node_lit
                            .get(&item.property)
                            .map(|s| Value::String(s.clone()))
                            .unwrap_or(Value::Null)
                    }
                })
                .collect();

            (vals, sort_key)
        })
        .collect();

    // sort
    if ob.is_some() {
        result_rows.sort_by(|(_, a), (_, b)| compare_sort_keys(a, b));
    }

    // skip / limit
    let start = skip.min(result_rows.len());
    let end = if limit > 0 {
        (start + limit).min(result_rows.len())
    } else {
        result_rows.len()
    };
    let values: Vec<Vec<Value>> = result_rows[start..end]
        .iter()
        .map(|(vals, _)| vals.clone())
        .collect();

    CypherResult { fields, values }
}

#[derive(Debug, Default)]
struct SortKey {
    keys: Vec<SortKeyPart>,
}

#[derive(Debug)]
enum SortKeyPart {
    Null,
    Num(f64),
    Str(String),
}

fn sort_key_for_row(
    row: &MatchedRow,
    lit_props: &LitPropMap,
    ob: Option<&OrderByClause>,
) -> SortKey {
    let items = match ob {
        None => return SortKey::default(),
        Some(o) => &o.items,
    };
    let empty: HashMap<String, String> = HashMap::new();
    let keys = items
        .iter()
        .map(|item| {
            let node = match row.nodes.get(&item.variable) {
                Some(n) => n,
                None => return SortKeyPart::Null,
            };
            let node_lit = lit_props.get(&node.id_curie).unwrap_or(&empty);
            let raw = if is_node_typed_col(&item.property) {
                node.to_map()
                    .get(&item.property)
                    .and_then(|v| v.as_str().map(|s| s.to_string()))
            } else {
                node_lit.get(&item.property).cloned()
            };
            match raw {
                None => SortKeyPart::Null,
                Some(s) => {
                    if let Ok(f) = s.parse::<f64>() {
                        SortKeyPart::Num(f)
                    } else {
                        SortKeyPart::Str(s)
                    }
                }
            }
        })
        .collect();
    SortKey { keys }
}

fn compare_sort_keys(a: &SortKey, b: &SortKey) -> std::cmp::Ordering {
    use std::cmp::Ordering;
    for (ak, bk) in a.keys.iter().zip(b.keys.iter()) {
        let ord = match (ak, bk) {
            (SortKeyPart::Null, SortKeyPart::Null) => Ordering::Equal,
            (SortKeyPart::Null, _) => Ordering::Less,
            (_, SortKeyPart::Null) => Ordering::Greater,
            (SortKeyPart::Num(a), SortKeyPart::Num(b)) => a.partial_cmp(b).unwrap_or(Ordering::Equal),
            (SortKeyPart::Str(a), SortKeyPart::Str(b)) => a.cmp(b),
            (SortKeyPart::Num(a), SortKeyPart::Str(b)) => {
                b.parse::<f64>().map(|bv| a.partial_cmp(&bv).unwrap_or(Ordering::Equal)).unwrap_or_else(|_| Ordering::Less)
            }
            (SortKeyPart::Str(a), SortKeyPart::Num(b)) => {
                a.parse::<f64>().map(|av| av.partial_cmp(b).unwrap_or(Ordering::Equal)).unwrap_or_else(|_| Ordering::Greater)
            }
        };
        if ord != std::cmp::Ordering::Equal {
            return ord;
        }
    }
    std::cmp::Ordering::Equal
}

// ── node / edge row types ─────────────────────────────────────────────────────

#[derive(Debug, Default, Clone)]
pub struct NodeRow {
    pub id_curie: String,
    pub id_iri: String,
    pub types: String,   // raw JSON string: '["Label1","Label2"]'
    pub label: String,
    pub description: String,
    pub graph_name: String,
    pub source_url: String,
    pub created_at: String,
    pub updated_at: String,
}

impl NodeRow {
    pub fn to_map(&self) -> Map<String, Value> {
        let mut m = Map::new();
        m.insert("id_curie".into(), Value::String(self.id_curie.clone()));
        m.insert("id_iri".into(), Value::String(self.id_iri.clone()));
        m.insert("label".into(), Value::String(self.label.clone()));
        m.insert("description".into(), Value::String(self.description.clone()));
        m.insert("graph_name".into(), Value::String(self.graph_name.clone()));
        m.insert("source_url".into(), Value::String(self.source_url.clone()));
        m.insert("created_at".into(), Value::String(self.created_at.clone()));
        m.insert("updated_at".into(), Value::String(self.updated_at.clone()));
        // parse types JSON string → array
        let types_val: Value = serde_json::from_str(&self.types)
            .unwrap_or(Value::Array(vec![]));
        m.insert("types".into(), types_val);
        m
    }

    /// Convert to Neo4j Query API v2 node element wire format.
    /// Matches Go cypher-server `toNodeElement()` in result.go.
    pub fn to_neo4j_element(
        &self,
        node_map: &Map<String, Value>,
        lit: &HashMap<String, String>,
    ) -> Value {
        let mut props = Map::new();
        for key in &[
            "label", "description", "id_iri", "graph_name",
            "source_url", "created_at", "updated_at", "ns_prefix", "local_id",
        ] {
            if let Some(v) = node_map.get(*key) {
                props.insert((*key).to_string(), v.clone());
            }
        }
        // merge domain literal props
        for (k, v) in lit {
            props.insert(k.clone(), Value::String(v.clone()));
        }
        let labels = node_map
            .get("types")
            .cloned()
            .unwrap_or(Value::Array(vec![]));
        let mut m = Map::new();
        m.insert("elementId".into(), Value::String(self.id_curie.clone()));
        m.insert("labels".into(), labels);
        m.insert("properties".into(), Value::Object(props));
        Value::Object(m)
    }
}

#[derive(Debug, Default, Clone)]
pub struct EdgeRow {
    pub src_id: String,
    pub dst_id: String,
    pub predicate_curie: String,
    pub predicate_label: String,
    pub weight: f64,
    pub props_json: String,
    pub valid_from: String,
    pub valid_to: String,
}

impl EdgeRow {
    pub fn to_map(&self) -> Map<String, Value> {
        let mut m = Map::new();
        m.insert("src_id".into(), Value::String(self.src_id.clone()));
        m.insert("dst_id".into(), Value::String(self.dst_id.clone()));
        m.insert("predicate_curie".into(), Value::String(self.predicate_curie.clone()));
        m.insert("weight".into(), serde_json::json!(self.weight));
        m
    }
}

// ── Lance scan helper ─────────────────────────────────────────────────────────

async fn scan_dataset(
    ds: &Arc<Dataset>,
    filter: &str,
    columns: &[&str],
) -> Result<Vec<RecordBatch>, Box<dyn std::error::Error + Send + Sync>> {
    let mut scanner = ds.scan();
    if !filter.is_empty() {
        scanner.filter(filter)?;
    }
    if !columns.is_empty() {
        scanner.project(columns)?;
    }
    let batches: Vec<RecordBatch> = scanner
        .try_into_stream()
        .await?
        .try_collect()
        .await?;
    Ok(batches)
}

// ── batch → row converters ────────────────────────────────────────────────────

fn batches_to_node_rows(batches: &[RecordBatch]) -> Vec<NodeRow> {
    let mut rows = Vec::new();
    for batch in batches {
        let len = batch.num_rows();
        for i in 0..len {
            let mut row = NodeRow::default();
            macro_rules! get_str {
                ($field:expr, $col:expr) => {
                    if let Some(col) = batch.column_by_name($col) {
                        if let Some(arr) = col.as_any().downcast_ref::<StringArray>() {
                            if !arr.is_null(i) {
                                $field = arr.value(i).to_string();
                            }
                        }
                    }
                };
            }
            get_str!(row.id_curie, "id_curie");
            get_str!(row.id_iri, "id_iri");
            get_str!(row.types, "types");
            get_str!(row.label, "label");
            get_str!(row.description, "description");
            get_str!(row.graph_name, "graph_name");
            get_str!(row.source_url, "source_url");
            get_str!(row.created_at, "created_at");
            get_str!(row.updated_at, "updated_at");
            if !row.id_curie.is_empty() {
                rows.push(row);
            }
        }
    }
    rows
}

fn batches_to_edge_rows(batches: &[RecordBatch]) -> Vec<EdgeRow> {
    let mut rows = Vec::new();
    for batch in batches {
        let len = batch.num_rows();
        for i in 0..len {
            let mut row = EdgeRow::default();
            macro_rules! get_str {
                ($field:expr, $col:expr) => {
                    if let Some(col) = batch.column_by_name($col) {
                        if let Some(arr) = col.as_any().downcast_ref::<StringArray>() {
                            if !arr.is_null(i) {
                                $field = arr.value(i).to_string();
                            }
                        }
                    }
                };
            }
            get_str!(row.src_id, "src_id");
            get_str!(row.dst_id, "dst_id");
            get_str!(row.predicate_curie, "predicate_curie");
            get_str!(row.predicate_label, "predicate_label");
            get_str!(row.props_json, "props_json");
            get_str!(row.valid_from, "valid_from");
            get_str!(row.valid_to, "valid_to");
            if let Some(col) = batch.column_by_name("weight") {
                if let Some(arr) = col.as_any().downcast_ref::<Float64Array>() {
                    if !arr.is_null(i) {
                        row.weight = arr.value(i);
                    }
                }
            }
            if !row.src_id.is_empty() {
                rows.push(row);
            }
        }
    }
    rows
}

// ── SQL helpers ───────────────────────────────────────────────────────────────

fn sql_esc(s: &str) -> String {
    s.replace('\'', "''")
}

fn ids_to_in_list(ids: &[String]) -> String {
    ids.iter()
        .map(|id| format!("'{}'", sql_esc(id)))
        .collect::<Vec<_>>()
        .join(", ")
}

/// Word-boundary-safe types LIKE filter: prevents false positives where one
/// label is a substring of another (e.g. "Case" vs "LegalCase").
fn types_like_filter(label: &str) -> String {
    let l = sql_esc(label);
    format!(
        r#"(types = '["{l}"]' OR types LIKE '["{l}",%' OR types LIKE '%,"{l}"]' OR types LIKE '%,"{l}",%')"#,
        l = l
    )
}

fn scalar_cond(col: &str, op: &str, val: &Value) -> Option<String> {
    let rhs = match val {
        Value::String(s) => format!("'{}'", sql_esc(s)),
        Value::Number(n) => n.to_string(),
        Value::Bool(b) => b.to_string(),
        _ => return None,
    };
    Some(format!("{col} {op} {rhs}"))
}

fn lit_value_cond(op: &str, val: &Value) -> Option<String> {
    match op {
        "=" | "<>" | "CONTAINS" | "STARTS WITH" | "ENDS WITH" => {
            let rhs = match val {
                Value::String(s) => format!("'{}'", sql_esc(s)),
                Value::Number(n) => format!("'{}'", n),
                _ => return None,
            };
            match op {
                "=" => Some(format!("lit_value = {rhs}")),
                "<>" => Some(format!("lit_value <> {rhs}")),
                "CONTAINS" => Some(format!("lit_value LIKE '%{}%'", val.as_str().unwrap_or("").replace('\'', "''"))),
                "STARTS WITH" => Some(format!("lit_value LIKE '{}%'", val.as_str().unwrap_or("").replace('\'', "''"))),
                "ENDS WITH" => Some(format!("lit_value LIKE '%{}'", val.as_str().unwrap_or("").replace('\'', "''"))),
                _ => None,
            }
        }
        ">" | "<" | ">=" | "<=" => {
            let rhs = match val {
                Value::Number(n) => n.to_string(),
                Value::String(s) => format!("'{}'", sql_esc(s)),
                _ => return None,
            };
            match val {
                Value::Number(_) => Some(format!("CAST(lit_value AS DOUBLE) {op} {rhs}")),
                _ => Some(format!("lit_value {op} {rhs}")),
            }
        }
        "IN" => {
            if let Value::Array(items) = val {
                let list: Vec<String> = items
                    .iter()
                    .filter_map(|v| match v {
                        Value::String(s) => Some(format!("'{}'", sql_esc(s))),
                        Value::Number(n) => Some(n.to_string()),
                        _ => None,
                    })
                    .collect();
                if list.is_empty() {
                    return None;
                }
                Some(format!("lit_value IN ({})", list.join(", ")))
            } else {
                None
            }
        }
        _ => None,
    }
}
