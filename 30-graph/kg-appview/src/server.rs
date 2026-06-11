//! Read-only SPARQL 1.1 Protocol endpoint + ATProto XRPC facade.
//!
//! Routes:
//!   - GET   /sparql?query=<urlencoded>[&format=<fmt>]
//!   - POST  /sparql  (Content-Type: application/sparql-query OR
//!                                   application/x-www-form-urlencoded with `query=` field)
//!   - GET   /xrpc/com.etzhayyim.kg.query?query=<urlencoded>[&format=<fmt>]
//!           (read-only XRPC facade defined by the lexicon of the same id)
//!   - GET   /healthz
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
use oxigraph::io::{RdfFormat, RdfSerializer};
use oxigraph::sparql::results::QueryResultsFormat;
use oxigraph::sparql::QueryResults;
use serde::Deserialize;

use crate::store::AppStore;

#[derive(Debug, Deserialize)]
pub struct SparqlQueryParams {
    query: Option<String>,
    /// Optional response-format override. Accepted values:
    ///   SELECT / ASK    json (default), xml, csv
    ///   CONSTRUCT/DESCRIBE  turtle (default), ntriples, rdfxml
    format: Option<String>,
}

pub async fn serve(app: Arc<AppStore>, listen: SocketAddr) -> Result<()> {
    let router = Router::new()
        .route("/sparql", get(get_sparql).post(post_sparql))
        .route("/xrpc/com.etzhayyim.kg.query", get(get_sparql))
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
    execute_sparql(&app, &query, params.format.as_deref(), &headers)
}

async fn post_sparql(
    State(app): State<Arc<AppStore>>,
    Query(params): Query<SparqlQueryParams>,
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
    execute_sparql(&app, &query, params.format.as_deref(), &headers)
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

fn execute_sparql(
    app: &AppStore,
    query: &str,
    format_param: Option<&str>,
    headers: &HeaderMap,
) -> Response {
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
            let format = pick_solution_format(format_param, accept);
            let mut buf = Vec::new();
            if let Err(err) = results.write(&mut buf, format) {
                return (
                    StatusCode::INTERNAL_SERVER_ERROR,
                    format!("write error: {err}\n"),
                )
                    .into_response();
            }
            let ct = solution_content_type(format);
            (
                StatusCode::OK,
                [(header::CONTENT_TYPE, HeaderValue::from_static(ct))],
                buf,
            )
                .into_response()
        }
        QueryResults::Graph(triples) => {
            let format = pick_graph_format(format_param, accept);
            let mut buf = Vec::new();
            let mut serializer = RdfSerializer::from_format(format).for_writer(&mut buf);
            for triple in triples {
                let t = match triple {
                    Ok(t) => t,
                    Err(err) => {
                        return (
                            StatusCode::INTERNAL_SERVER_ERROR,
                            format!("graph iter error: {err}\n"),
                        )
                            .into_response();
                    }
                };
                if let Err(err) = serializer.serialize_triple(t.as_ref()) {
                    return (
                        StatusCode::INTERNAL_SERVER_ERROR,
                        format!("serializer error: {err}\n"),
                    )
                        .into_response();
                }
            }
            if let Err(err) = serializer.finish() {
                return (
                    StatusCode::INTERNAL_SERVER_ERROR,
                    format!("serializer finish error: {err}\n"),
                )
                    .into_response();
            }
            let ct = graph_content_type(format);
            (
                StatusCode::OK,
                [(header::CONTENT_TYPE, HeaderValue::from_static(ct))],
                buf,
            )
                .into_response()
        }
    }
}

fn pick_solution_format(format_param: Option<&str>, accept: &str) -> QueryResultsFormat {
    if let Some(fmt) = format_param {
        match fmt.to_ascii_lowercase().as_str() {
            "json" => return QueryResultsFormat::Json,
            "xml" => return QueryResultsFormat::Xml,
            "csv" => return QueryResultsFormat::Csv,
            _ => {} // fall through to Accept negotiation
        }
    }
    if accept.contains("text/csv") {
        QueryResultsFormat::Csv
    } else if accept.contains("application/sparql-results+xml") || accept.contains("application/xml") {
        QueryResultsFormat::Xml
    } else {
        QueryResultsFormat::Json
    }
}

fn solution_content_type(format: QueryResultsFormat) -> &'static str {
    match format {
        QueryResultsFormat::Json => "application/sparql-results+json; charset=utf-8",
        QueryResultsFormat::Xml => "application/sparql-results+xml; charset=utf-8",
        QueryResultsFormat::Csv => "text/csv; charset=utf-8",
        _ => "application/sparql-results+json; charset=utf-8",
    }
}

fn pick_graph_format(format_param: Option<&str>, accept: &str) -> RdfFormat {
    if let Some(fmt) = format_param {
        match fmt.to_ascii_lowercase().as_str() {
            "turtle" | "ttl" => return RdfFormat::Turtle,
            "ntriples" | "nt" => return RdfFormat::NTriples,
            "rdfxml" | "xml" => return RdfFormat::RdfXml,
            _ => {} // fall through
        }
    }
    if accept.contains("application/n-triples") {
        RdfFormat::NTriples
    } else if accept.contains("application/rdf+xml") {
        RdfFormat::RdfXml
    } else {
        RdfFormat::Turtle
    }
}

fn graph_content_type(format: RdfFormat) -> &'static str {
    match format {
        RdfFormat::Turtle => "text/turtle; charset=utf-8",
        RdfFormat::NTriples => "application/n-triples; charset=utf-8",
        RdfFormat::RdfXml => "application/rdf+xml; charset=utf-8",
        _ => "text/turtle; charset=utf-8",
    }
}

fn looks_like_update(query: &str) -> bool {
    let lower = query.trim_start().to_lowercase();
    const UPDATE_KEYWORDS: &[&str] = &[
        "insert ", "delete ", "load ", "clear ", "create ", "drop ", "copy ", "move ", "add ",
    ];
    UPDATE_KEYWORDS.iter().any(|kw| lower.starts_with(kw))
}
