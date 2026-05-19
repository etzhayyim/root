//! Read-only SPARQL 1.1 Protocol endpoint. K2.a scope:
//!   - GET  /sparql?query=<urlencoded>
//!   - POST /sparql  (Content-Type: application/sparql-query OR
//!                                  application/x-www-form-urlencoded with `query=` field)
//!   - GET  /healthz
//!
//! Update operations are rejected with 403. The store's only legitimate
//! mutation path is loading from kg-projector / firehose at startup.

use std::net::SocketAddr;
use std::sync::Arc;

use anyhow::Result;
use axum::{
    extract::{Query, State},
    http::{header, HeaderMap, HeaderValue, StatusCode},
    response::{IntoResponse, Response},
    routing::get,
    Router,
};
use oxigraph::sparql::results::QueryResultsFormat;
use oxigraph::sparql::QueryResults;
use serde::Deserialize;

use crate::store::AppStore;

#[derive(Debug, Deserialize)]
pub struct SparqlQueryParams {
    query: Option<String>,
}

pub async fn serve(app: Arc<AppStore>, listen: SocketAddr) -> Result<()> {
    let router = Router::new()
        .route("/sparql", get(get_sparql).post(post_sparql))
        .route("/healthz", get(healthz))
        .with_state(app);

    let listener = tokio::net::TcpListener::bind(listen).await?;
    tracing::info!(addr = %listen, "kg-appview listening");
    axum::serve(listener, router).await?;
    Ok(())
}

async fn healthz() -> &'static str {
    "ok\n"
}

async fn get_sparql(
    State(app): State<Arc<AppStore>>,
    Query(params): Query<SparqlQueryParams>,
    headers: HeaderMap,
) -> Response {
    let Some(query) = params.query else {
        return (StatusCode::BAD_REQUEST, "missing query parameter\n").into_response();
    };
    execute_sparql(&app, &query, &headers)
}

async fn post_sparql(
    State(app): State<Arc<AppStore>>,
    headers: HeaderMap,
    body: String,
) -> Response {
    let content_type = headers
        .get(header::CONTENT_TYPE)
        .and_then(|v| v.to_str().ok())
        .unwrap_or("");

    let query = if content_type.starts_with("application/sparql-query") {
        body
    } else if content_type.starts_with("application/x-www-form-urlencoded") {
        match form_decode_query(&body) {
            Some(q) => q,
            None => return (StatusCode::BAD_REQUEST, "missing query field\n").into_response(),
        }
    } else {
        return (
            StatusCode::UNSUPPORTED_MEDIA_TYPE,
            "Content-Type must be application/sparql-query or application/x-www-form-urlencoded\n",
        )
            .into_response();
    };
    execute_sparql(&app, &query, &headers)
}

fn form_decode_query(body: &str) -> Option<String> {
    for pair in body.split('&') {
        if let Some(value) = pair.strip_prefix("query=") {
            return percent_encoding::percent_decode_str(value)
                .decode_utf8()
                .ok()
                .map(|s| s.into_owned());
        }
    }
    None
}

fn execute_sparql(app: &AppStore, query: &str, headers: &HeaderMap) -> Response {
    if looks_like_update(query) {
        return (StatusCode::FORBIDDEN, "SPARQL UPDATE not allowed\n").into_response();
    }

    let results = match app.store.query(query) {
        Ok(r) => r,
        Err(err) => {
            return (StatusCode::BAD_REQUEST, format!("query error: {err}\n")).into_response();
        }
    };

    let accept = headers
        .get(header::ACCEPT)
        .and_then(|v| v.to_str().ok())
        .unwrap_or("");

    match results {
        QueryResults::Solutions(_) | QueryResults::Boolean(_) => {
            let format = if accept.contains("text/csv") {
                QueryResultsFormat::Csv
            } else if accept.contains("application/sparql-results+xml")
                || accept.contains("application/xml")
            {
                QueryResultsFormat::Xml
            } else {
                QueryResultsFormat::Json
            };
            let mut buf = Vec::new();
            if let Err(err) = results.write(&mut buf, format) {
                return (
                    StatusCode::INTERNAL_SERVER_ERROR,
                    format!("write error: {err}\n"),
                )
                    .into_response();
            }
            let ct = match format {
                QueryResultsFormat::Json => "application/sparql-results+json; charset=utf-8",
                QueryResultsFormat::Xml => "application/sparql-results+xml; charset=utf-8",
                QueryResultsFormat::Csv => "text/csv; charset=utf-8",
                _ => "application/sparql-results+json; charset=utf-8",
            };
            (
                StatusCode::OK,
                [(header::CONTENT_TYPE, HeaderValue::from_static(ct))],
                buf,
            )
                .into_response()
        }
        QueryResults::Graph(_triples) => (
            StatusCode::NOT_IMPLEMENTED,
            "CONSTRUCT / DESCRIBE not yet supported in K2.a — use SELECT or ASK\n",
        )
            .into_response(),
    }
}

fn looks_like_update(query: &str) -> bool {
    let lower = query.trim_start().to_lowercase();
    const UPDATE_KEYWORDS: &[&str] = &[
        "insert ", "delete ", "load ", "clear ", "create ", "drop ", "copy ", "move ", "add ",
    ];
    UPDATE_KEYWORDS.iter().any(|kw| lower.starts_with(kw))
}
