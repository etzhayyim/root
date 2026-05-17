/// Tonbo-native Cypher query engine.
///
/// Provides a Neo4j Query API v2-compatible HTTP endpoint (`POST /db/{org_id}/query/v2`)
/// that executes directly against Lance datasets without DataFusion SQL overhead:
///
/// - Layer 1 typed column predicates → Lance scanner filter expressions
/// - Layer 2 literal edge properties → direct edge table scans + AND-intersection
/// - Layer 3 BFS traversal → in-process async loop (zero RTT per hop)
/// - Response: Neo4j JSON format (Arrow IPC streaming planned as Accept header option)
///
/// # Performance advantage over cypher-server + lancedbrest path
///
/// - No SQL string generation/parsing per query
/// - No DataFusion query planning (join enumeration, optimizer)
/// - BFS: N round trips → 1 async function call
/// - No HTTP JSON marshalling for intermediate results
pub mod ast;
pub mod executor;
pub mod parser;

pub use executor::CypherEngine;

use std::collections::HashMap;
use std::sync::Arc;

use axum::extract::{Path, State};
use axum::http::StatusCode;
use axum::response::{IntoResponse, Response};
use axum::Json;
use serde::{Deserialize, Serialize};
use serde_json::Value;

use crate::http::HttpState;

// ── request / response types ──────────────────────────────────────────────────

#[derive(Debug, Deserialize)]
pub struct CypherRequest {
    pub statement: String,
    /// `parameters` may be absent, `null`, or a JSON object.
    #[serde(default, deserialize_with = "deserialize_params")]
    pub parameters: HashMap<String, Value>,
}

fn deserialize_params<'de, D>(de: D) -> Result<HashMap<String, Value>, D::Error>
where
    D: serde::Deserializer<'de>,
{
    let opt: Option<HashMap<String, Value>> = Option::deserialize(de)?;
    Ok(opt.unwrap_or_default())
}

/// Neo4j Query API v2 success response — matches Go cypher-server wire format exactly.
#[derive(Debug, Serialize)]
pub struct CypherResponse {
    pub data: CypherData,
    pub bookmarks: Vec<String>,
    pub notifications: Option<Value>,
    #[serde(skip_serializing_if = "Vec::is_empty")]
    pub errors: Vec<CypherError>,
}

#[derive(Debug, Serialize)]
pub struct CypherData {
    pub fields: Vec<String>,
    pub values: Vec<Vec<Value>>,
}

#[derive(Debug, Serialize)]
pub struct CypherError {
    pub code: String,
    pub message: String,
}

// ── HTTP handler ──────────────────────────────────────────────────────────────

/// POST /db/{org_id}/query/v2
///
/// Neo4j Query API v2 — accepts `{"statement": "MATCH ...", "parameters": {...}}`.
/// Returns HTTP 202 with Neo4j-compatible JSON body on success.
pub async fn handle_cypher_query(
    Path(org_id): Path<String>,
    State(state): State<Arc<HttpState>>,
    Json(req): Json<CypherRequest>,
) -> Response {
    // parse
    let query = match parser::parse(&req.statement) {
        Ok(q) => q,
        Err(e) => {
            return error_response(
                StatusCode::OK,
                "Neo.ClientError.Statement.SyntaxError",
                &format!("Cypher parse error: {e}"),
            );
        }
    };

    // execute
    let engine = CypherEngine::new(state.ctx.clone());
    let result = match engine.execute(&query, &org_id, &req.parameters).await {
        Ok(r) => r,
        Err(e) => {
            return error_response(
                StatusCode::OK,
                "Neo.DatabaseError.General.UnknownError",
                &e.to_string(),
            );
        }
    };

    let body = CypherResponse {
        data: CypherData {
            fields: result.fields,
            values: result.values,
        },
        bookmarks: vec![],
        notifications: None,
        errors: vec![],
    };

    (StatusCode::ACCEPTED, Json(body)).into_response()
}

fn error_response(status: StatusCode, code: &str, message: &str) -> Response {
    let body = CypherResponse {
        data: CypherData { fields: vec![], values: vec![] },
        bookmarks: vec![],
        notifications: None,
        errors: vec![CypherError {
            code: code.to_string(),
            message: message.to_string(),
        }],
    };
    (status, Json(body)).into_response()
}
