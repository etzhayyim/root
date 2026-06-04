use std::collections::BTreeMap;
use std::io::Cursor;
use std::sync::Arc;
use std::time::Instant;

use arrow::datatypes::{DataType, SchemaRef};
use arrow_ipc::reader::StreamReader;
use arrow_ipc::writer::FileWriter;
use arrow_json::ArrayWriter;
use axum::body::Bytes;
use axum::extract::{MatchedPath, Path, Query, Request, State};
use axum::http::{HeaderMap, StatusCode};
use axum::middleware::{self, Next};
use axum::response::{IntoResponse, Response};
use axum::routing::{get, post};
use axum::{Json, Router};
use lance::dataset::ColumnAlteration;
use lance_index::scalar::ScalarIndexType;
use lance_linalg::distance::MetricType;
use serde::{Deserialize, Serialize};
use serde_json::{Map, Value};

use crate::context::{
    CreateTableMode, NamespaceCreateMode, NamespaceDropMode, TableIndexInfo, TableStats,
    TableVersionInfo, TonboContext,
};

#[derive(Clone)]
pub struct HttpState {
    pub ctx: Arc<TonboContext>,
}

#[derive(Serialize)]
struct ErrorResponse {
    error: String,
    code: u16,
    #[serde(skip_serializing_if = "Option::is_none")]
    detail: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    instance: Option<String>,
}

#[derive(Serialize)]
struct NamespaceListResponse {
    namespaces: Vec<String>,
    page_token: Option<String>,
}

#[derive(Serialize)]
struct NamespaceDescribeResponse {
    properties: Map<String, Value>,
}

#[derive(Serialize)]
struct CreateNamespaceResponse {
    transaction_id: Option<String>,
    properties: Option<Map<String, Value>>,
}

#[derive(Serialize)]
struct DropNamespaceResponse {
    properties: Option<Map<String, Value>>,
    transaction_id: Option<Vec<String>>,
}

#[derive(Serialize)]
struct TableListResponse {
    tables: Vec<String>,
    page_token: Option<String>,
}

#[derive(Serialize)]
struct TableDescribeResponse {
    table: String,
    namespace: Vec<String>,
    version: i64,
    location: String,
    table_uri: String,
    schema: TableSchemaResponse,
    storage_options: Map<String, Value>,
    stats: Option<Value>,
    metadata: Option<Map<String, Value>>,
    properties: Option<Value>,
    managed_versioning: bool,
}

#[derive(Serialize)]
struct TableSchemaResponse {
    fields: Vec<TableFieldResponse>,
}

#[derive(Serialize)]
struct TableFieldResponse {
    name: String,
    #[serde(rename = "type")]
    dtype: String,
    nullable: bool,
}

#[derive(Serialize)]
struct CreateTableResponse {
    transaction_id: Option<String>,
    location: String,
    version: i64,
    storage_options: Map<String, Value>,
    properties: Option<Map<String, Value>>,
}

#[derive(Serialize)]
struct CreateEmptyTableResponse {
    transaction_id: Option<String>,
    location: String,
    storage_options: Map<String, Value>,
    properties: Option<Map<String, Value>>,
}

#[derive(Serialize)]
struct RegisterTableResponse {
    transaction_id: Option<String>,
    location: String,
    properties: Option<Map<String, Value>>,
}

#[derive(Serialize)]
struct InsertIntoTableResponse {
    transaction_id: Option<String>,
}

#[derive(Serialize)]
struct MergeInsertIntoTableResponse {
    transaction_id: Option<String>,
    num_updated_rows: i64,
    num_inserted_rows: i64,
    num_deleted_rows: i64,
    version: i64,
}

#[derive(Serialize)]
struct QueryJsonResponse {
    rows: Vec<Map<String, Value>>,
}

#[derive(Serialize)]
struct DropTableResponse {
    transaction_id: Option<String>,
    id: Vec<String>,
    location: String,
    properties: Option<Map<String, Value>>,
}

#[derive(Serialize)]
struct DeregisterTableResponse {
    transaction_id: Option<String>,
    id: Vec<String>,
    location: String,
    properties: Option<Map<String, Value>>,
}

#[derive(Serialize)]
struct CountTableRowsResponse {
    count: usize,
}

#[derive(Serialize)]
struct DeleteFromTableResponse {
    transaction_id: Option<String>,
    version: i64,
}

#[derive(Serialize)]
struct ListTableVersionsResponse {
    versions: Vec<TableVersionResponse>,
    page_token: Option<String>,
}

#[derive(Serialize)]
struct TableVersionResponse {
    version: i64,
}

#[derive(Serialize)]
struct CreateTableVersionResponse {
    transaction_id: Option<String>,
    version: i64,
}

#[derive(Serialize)]
struct DescribeTableVersionResponse {
    version: i64,
    manifest_path: String,
    transaction_file: Option<String>,
    schema_fields: usize,
    config: Map<String, Value>,
}

#[derive(Serialize)]
struct DeleteTableVersionsResponse {
    transaction_id: Option<String>,
    deleted_versions: usize,
}

#[derive(Serialize)]
struct BatchCreateVersionsResponse {
    transaction_id: Option<String>,
    versions: Vec<BatchCreatedVersionResponse>,
}

#[derive(Serialize)]
struct BatchCreatedVersionResponse {
    table: String,
    version: i64,
}

#[derive(Serialize)]
struct SchemaMutationResponse {
    transaction_id: Option<String>,
    version: i64,
}

#[derive(Deserialize)]
struct LanceQueryRequest {
    filter: Option<String>,
    limit: Option<usize>,
    offset: Option<usize>,
    order_by: Option<String>,
    columns: Option<LanceColumnSelector>,
}

#[derive(Deserialize)]
#[serde(untagged)]
enum LanceColumnSelector {
    Flat(Vec<String>),
    Named { column_names: Vec<String> },
}

impl LanceColumnSelector {
    fn into_names(self) -> Vec<String> {
        match self {
            LanceColumnSelector::Flat(names) => names,
            LanceColumnSelector::Named { column_names } => column_names,
        }
    }
}

#[derive(Deserialize)]
struct MergeInsertParams {
    on: Option<String>,
    when_matched_update_all: Option<bool>,
    when_not_matched_insert_all: Option<bool>,
}

#[derive(Deserialize)]
struct MergeInsertCompatRequest {
    on: Option<Value>,
    rows: Vec<Map<String, Value>>,
}

#[derive(Deserialize)]
struct CreateTableJsonField {
    name: String,
    #[serde(
        rename = "type",
        alias = "dtype",
        alias = "data_type",
        default = "default_field_type"
    )]
    field_type: String,
    #[serde(default = "default_nullable")]
    nullable: bool,
}

fn default_field_type() -> String {
    "string".into()
}

fn default_nullable() -> bool {
    true
}

#[derive(Deserialize)]
struct LanceDeleteRequest {
    #[serde(alias = "filter")]
    predicate: String,
}

#[derive(Deserialize)]
struct LanceCountRowsRequest {
    #[serde(alias = "predicate")]
    filter: Option<String>,
}

#[derive(Deserialize, Default)]
struct CreateTableParams {
    mode: Option<String>,
}

#[derive(Deserialize)]
struct CreateTableJsonRequest {
    #[serde(alias = "columns", alias = "schema", default)]
    fields: Vec<CreateTableJsonField>,
    #[serde(default)]
    mode: Option<String>,
    #[serde(default)]
    rows: Option<Vec<Map<String, Value>>>,
}

#[derive(Deserialize)]
struct RegisterTableRequest {
    location: String,
    mode: Option<String>,
}

#[derive(Deserialize)]
struct RenameTableRequest {
    new_table_name: String,
}

#[derive(Deserialize, Default)]
struct VersionListQuery {
    descending: Option<bool>,
}

#[derive(Deserialize)]
struct RestoreTableRequest {
    version: i64,
}

#[derive(Deserialize, Default)]
struct CreateTableVersionRequest {
    version: Option<i64>,
    put_if_not_exists: Option<bool>,
    metadata: Option<BTreeMap<String, String>>,
}

#[derive(Deserialize)]
struct DescribeTableVersionRequest {
    version: i64,
}

#[derive(Deserialize, Default)]
struct DeleteTableVersionsRequest {
    version: Option<i64>,
    start_version: Option<i64>,
    end_version: Option<i64>,
    ranges: Option<Vec<VersionRangeRequest>>,
}

#[derive(Deserialize)]
struct VersionRangeRequest {
    start_version: i64,
    end_version: i64,
}

#[derive(Deserialize)]
struct BatchCreateVersionEntry {
    #[serde(default)]
    table: String,
    id: Option<Vec<String>>,
    version: Option<i64>,
    put_if_not_exists: Option<bool>,
    metadata: Option<BTreeMap<String, String>>,
}

#[derive(Deserialize, Default)]
struct BatchCreateVersionsRequest {
    tables: Option<Vec<BatchCreateVersionEntry>>,
    versions: Option<Vec<BatchCreateVersionEntry>>,
    entries: Option<Vec<BatchCreateVersionEntry>>,
}

#[derive(Serialize)]
struct RestoreTableResponse {
    transaction_id: Option<String>,
}

#[derive(Serialize)]
struct UpdateTableResponse {
    transaction_id: Option<String>,
    updated_rows: i64,
    version: i64,
    properties: Option<Value>,
}

#[derive(Serialize)]
struct ListIndexesResponse {
    indexes: Vec<IndexResponse>,
}

#[derive(Serialize)]
struct IndexResponse {
    name: String,
    fields: Vec<String>,
    dataset_version: i64,
}

#[derive(Serialize)]
struct OptimizeTableResponse {
    transaction_id: Option<String>,
    version: i64,
    fragments_removed: usize,
    fragments_added: usize,
    files_removed: usize,
    files_added: usize,
}

#[derive(Serialize)]
struct CleanupOldVersionsResponse {
    bytes_removed: u64,
    old_versions: u64,
}

#[derive(Serialize)]
struct TableStatsResponse {
    num_rows: usize,
    num_indices: usize,
    num_columns: usize,
    version: i64,
}

#[derive(Serialize)]
struct TagVersionResponse {
    version: u64,
}

#[derive(Serialize)]
struct DeclareTableResponse {
    transaction_id: Option<String>,
    location: String,
}

#[derive(Deserialize)]
struct AddColumnsRequest {
    #[serde(alias = "new_columns", alias = "fields")]
    columns: Vec<AddColumnRequest>,
}

#[derive(Deserialize)]
struct AddColumnRequest {
    name: String,
    expression: String,
}

#[derive(Deserialize)]
struct AlterColumnsRequest {
    #[serde(alias = "columns")]
    alterations: Vec<AlterColumnRequest>,
}

#[derive(Deserialize)]
struct AlterColumnRequest {
    path: String,
    rename: Option<String>,
    nullable: Option<bool>,
    #[serde(alias = "dataType", alias = "data_type")]
    data_type: Option<String>,
}

#[derive(Deserialize)]
struct DropColumnsRequest {
    columns: Vec<String>,
}

#[derive(Deserialize)]
struct UpdateTableRequest {
    updates: Value,
    #[serde(alias = "where", alias = "only_if")]
    predicate: Option<String>,
}

#[derive(Deserialize)]
struct CreateScalarIndexRequest {
    column: Option<String>,
    columns: Option<Vec<String>>,
    column_names: Option<Vec<String>>,
    index_name: Option<String>,
    #[serde(alias = "name")]
    name: Option<String>,
    index_type: Option<String>,
    #[serde(alias = "type")]
    kind: Option<String>,
    replace: Option<bool>,
}

#[derive(Deserialize)]
struct CreateIndexRequest {
    column: Option<String>,
    columns: Option<Vec<String>>,
    column_names: Option<Vec<String>>,
    index_name: Option<String>,
    #[serde(alias = "name")]
    name: Option<String>,
    index_type: Option<String>,
    #[serde(alias = "type")]
    kind: Option<String>,
    replace: Option<bool>,
    metric_type: Option<String>,
    #[serde(alias = "distance_type")]
    distance_type: Option<String>,
    num_partitions: Option<usize>,
    num_sub_vectors: Option<usize>,
    hnsw_m: Option<usize>,
    hnsw_ef_construction: Option<usize>,
}

#[derive(Deserialize, Default)]
struct OptimizeTableRequest {
    compact: Option<bool>,
    optimize_indices: Option<bool>,
    num_indices_to_merge: Option<usize>,
}

#[derive(Deserialize, Default)]
struct CleanupOldVersionsRequest {
    older_than_seconds: Option<i64>,
    delete_unverified: Option<bool>,
    error_if_tagged_old_versions: Option<bool>,
}

#[derive(Deserialize, Default)]
struct CreateNamespaceRequest {
    mode: Option<String>,
    properties: Option<BTreeMap<String, String>>,
}

#[derive(Deserialize, Default)]
struct DropNamespaceRequest {
    mode: Option<String>,
}

#[derive(Deserialize)]
struct TagRequest {
    tag: String,
}

#[derive(Deserialize)]
struct TagUpdateRequest {
    tag: String,
    version: u64,
}

pub fn router(ctx: Arc<TonboContext>) -> Router {
    let state = Arc::new(HttpState { ctx });
    Router::new()
        .route(
            "/v1/namespace/{namespace}/create",
            post(handle_create_namespace),
        )
        .route(
            "/v1/namespace/{namespace}/list",
            get(handle_list_namespaces),
        )
        .route(
            "/v1/namespace/{namespace}/describe",
            post(handle_describe_namespace),
        )
        .route(
            "/v1/namespace/{namespace}/drop",
            post(handle_drop_namespace),
        )
        .route(
            "/v1/namespace/{namespace}/exists",
            post(handle_namespace_exists),
        )
        .route(
            "/v1/namespace/{namespace}/table/list",
            get(handle_list_tables_in_namespace),
        )
        .route(
            "/v1/namespace/{namespace}/table/list",
            post(handle_list_tables_in_namespace_post),
        )
        .route("/v1/table", get(handle_list_tables))
        .route("/v1/tables", get(handle_list_tables))
        .route("/v1/table/{table}/register", post(handle_register_table))
        .route("/v1/table/{table}/create", post(handle_create_table))
        .route("/v1/table/{table}/create/", post(handle_create_table))
        .route(
            "/v1/table/{table}/create_empty",
            post(handle_create_empty_table),
        )
        .route(
            "/v1/table/{table}/create-empty",
            post(handle_create_empty_table),
        )
        .route(
            "/v1/table/{table}/create_empty/",
            post(handle_create_empty_table),
        )
        .route(
            "/v1/table/{table}/create-empty/",
            post(handle_create_empty_table),
        )
        .route("/v1/table/{table}/declare", post(handle_declare_table))
        .route("/v1/table/{table}/declare/", post(handle_declare_table))
        .route("/v1/table/{table}/insert", post(handle_insert_rows))
        .route("/v1/table/{table}/describe", post(handle_describe_table))
        .route("/v1/table/{table}/exists", post(handle_table_exists))
        .route("/v1/table/{table}/drop", post(handle_drop_table))
        .route("/v1/table/{table}/update", post(handle_update_table))
        .route("/v1/table/{table}/optimize", post(handle_optimize_table))
        .route(
            "/v1/table/{table}/cleanup_old_versions",
            post(handle_cleanup_old_versions),
        )
        .route(
            "/v1/table/{table}/deregister",
            post(handle_deregister_table),
        )
        .route("/v1/table/{table}/restore", post(handle_restore_table))
        .route("/v1/table/{table}/rename", post(handle_rename_table))
        .route(
            "/v1/table/{table}/create_scalar_index",
            post(handle_create_scalar_index),
        )
        .route("/v1/table/{table}/create_index", post(handle_create_index))
        .route("/v1/table/{table}/index/list", get(handle_list_indexes))
        .route(
            "/v1/table/{table}/index/list",
            post(handle_list_indexes_post),
        )
        .route(
            "/v1/table/{table}/index/{index}/stats",
            get(handle_index_stats),
        )
        .route(
            "/v1/table/{table}/index/{index}/stats",
            post(handle_index_stats_post),
        )
        .route(
            "/v1/table/{table}/index/{index}/drop",
            post(handle_drop_index),
        )
        .route("/v1/table/{table}/add_columns", post(handle_add_columns))
        .route(
            "/v1/table/{table}/alter_columns",
            post(handle_alter_columns),
        )
        .route("/v1/table/{table}/drop_columns", post(handle_drop_columns))
        .route(
            "/v1/table/{table}/schema_metadata/update",
            post(handle_update_schema_metadata),
        )
        .route(
            "/v1/table/{table}/version/list",
            post(handle_list_table_versions),
        )
        .route(
            "/v1/table/{table}/version/list/",
            post(handle_list_table_versions),
        )
        .route(
            "/v1/table/{table}/version/create",
            post(handle_create_table_version),
        )
        .route(
            "/v1/table/{table}/version/create/",
            post(handle_create_table_version),
        )
        .route(
            "/v1/table/{table}/version/describe",
            post(handle_describe_table_version),
        )
        .route(
            "/v1/table/{table}/version/describe/",
            post(handle_describe_table_version),
        )
        .route(
            "/v1/table/{table}/version/delete",
            post(handle_delete_table_versions),
        )
        .route(
            "/v1/table/{table}/version/delete/",
            post(handle_delete_table_versions),
        )
        .route(
            "/v1/table/version/batch-create",
            post(handle_batch_create_table_versions),
        )
        .route("/v1/table/{table}/stats", post(handle_table_stats))
        .route("/v1/table/{table}/stats/", post(handle_table_stats))
        .route("/v1/table/{table}/explain", post(handle_explain_query))
        .route("/v1/table/{table}/explain/", post(handle_explain_query))
        .route("/v1/table/{table}/explain_plan", post(handle_explain_query))
        .route(
            "/v1/table/{table}/explain_plan/",
            post(handle_explain_query),
        )
        .route("/v1/table/{table}/analyze", post(handle_analyze_query))
        .route("/v1/table/{table}/analyze/", post(handle_analyze_query))
        .route("/v1/table/{table}/analyze_plan", post(handle_analyze_query))
        .route(
            "/v1/table/{table}/analyze_plan/",
            post(handle_analyze_query),
        )
        .route("/v1/table/{table}/query", post(handle_table_query))
        .route("/v1/table/{table}/query/", post(handle_table_query))
        .route(
            "/v1/table/{table}/merge_insert",
            post(handle_merge_insert),
        )
        .route(
            "/v1/table/{table}/merge_insert/",
            post(handle_merge_insert),
        )
        .route("/v1/table/{table}/delete", post(handle_delete))
        .route("/v1/table/{table}/delete/", post(handle_delete))
        .route("/v1/table/{table}/count_rows", post(handle_count_rows))
        .route("/v1/table/{table}/count_rows/", post(handle_count_rows))
        .route("/v1/table/{table}/insert/", post(handle_insert_rows))
        .route("/v1/table/{table}/describe/", post(handle_describe_table))
        .route("/v1/table/{table}/exists/", post(handle_table_exists))
        .route("/v1/table/{table}/update/", post(handle_update_table))
        .route("/v1/table/{table}/drop/", post(handle_drop_table))
        .route("/v1/table/{table}/tags/list", get(handle_list_tags))
        .route("/v1/table/{table}/tags/list", post(handle_list_tags))
        .route("/v1/table/{table}/tags/list/", post(handle_list_tags))
        .route(
            "/v1/table/{table}/tags/version",
            post(handle_get_tag_version),
        )
        .route(
            "/v1/table/{table}/tags/version/",
            post(handle_get_tag_version),
        )
        .route("/v1/table/{table}/tags/create", post(handle_create_tag))
        .route("/v1/table/{table}/tags/create/", post(handle_create_tag))
        .route("/v1/table/{table}/tags/delete", post(handle_delete_tag))
        .route("/v1/table/{table}/tags/delete/", post(handle_delete_tag))
        .route("/v1/table/{table}/tags/update", post(handle_update_tag))
        .route("/v1/table/{table}/tags/update/", post(handle_update_tag))
        .route(
            "/v1/transaction/{id}/alter",
            post(handle_transaction_alter),
        )
        .route(
            "/v1/transaction/{id}/describe",
            post(handle_transaction_describe),
        )
        .route("/health", get(handle_health))
        .route("/healthz", get(handle_health))
        .route("/metrics", get(handle_metrics))
        // Neo4j Query API v2 — Tonbo-native Cypher engine (no DataFusion SQL)
        .route(
            "/db/{org_id}/query/v2",
            post(crate::cypher::handle_cypher_query),
        )
        .route(
            "/db/{org_id}/query/v2/",
            post(crate::cypher::handle_cypher_query),
        )
        .with_state(state)
        .layer(middleware::from_fn(track_http_metrics))
}

async fn handle_create_namespace(
    State(state): State<Arc<HttpState>>,
    Path(namespace): Path<String>,
    Json(req): Json<CreateNamespaceRequest>,
) -> Response {
    let mode = match parse_namespace_create_mode(req.mode.as_deref()) {
        Ok(mode) => mode,
        Err(error) => return error_response(StatusCode::BAD_REQUEST, error),
    };
    let properties = req.properties.unwrap_or_default();
    match state
        .ctx
        .create_namespace(&namespace, mode, properties.clone())
        .await
    {
        Ok(properties) => (
            StatusCode::OK,
            Json(CreateNamespaceResponse {
                transaction_id: None,
                properties: Some(string_map_to_json_map(&properties)),
            }),
        )
            .into_response(),
        Err(error) => {
            let text = error.to_string();
            let status = if text.contains("already exists") {
                StatusCode::CONFLICT
            } else if text.contains("not implemented") {
                StatusCode::NOT_ACCEPTABLE
            } else {
                StatusCode::INTERNAL_SERVER_ERROR
            };
            error_response(status, text)
        }
    }
}

async fn handle_list_namespaces(
    State(state): State<Arc<HttpState>>,
    Path(namespace): Path<String>,
) -> Response {
    if !state.ctx.namespace_exists(&namespace) {
        return error_response(StatusCode::NOT_FOUND, "namespace not found");
    }
    Json(NamespaceListResponse {
        namespaces: state
            .ctx
            .list_namespaces()
            .into_iter()
            .filter(|name| name != "default")
            .collect(),
        page_token: None,
    })
    .into_response()
}

async fn handle_describe_namespace(
    State(state): State<Arc<HttpState>>,
    Path(namespace): Path<String>,
) -> Response {
    match state.ctx.describe_namespace(&namespace) {
        Ok(properties) => (
            StatusCode::OK,
            Json(NamespaceDescribeResponse {
                properties: string_map_to_json_map(&properties),
            }),
        )
            .into_response(),
        Err(error) => error_response(StatusCode::NOT_FOUND, error.to_string()),
    }
}

async fn handle_drop_namespace(
    State(state): State<Arc<HttpState>>,
    Path(namespace): Path<String>,
    Json(req): Json<DropNamespaceRequest>,
) -> Response {
    let mode = match parse_namespace_drop_mode(req.mode.as_deref()) {
        Ok(mode) => mode,
        Err(error) => return error_response(StatusCode::BAD_REQUEST, error),
    };
    match state.ctx.drop_namespace(&namespace, mode).await {
        Ok(properties) => (
            if properties.is_some() {
                StatusCode::OK
            } else {
                StatusCode::NO_CONTENT
            },
            Json(DropNamespaceResponse {
                properties: properties.map(|props| string_map_to_json_map(&props)),
                transaction_id: None,
            }),
        )
            .into_response(),
        Err(error) => {
            let text = error.to_string();
            let status = if text.contains("not found") {
                StatusCode::BAD_REQUEST
            } else if text.contains("not implemented") {
                StatusCode::NOT_ACCEPTABLE
            } else {
                StatusCode::INTERNAL_SERVER_ERROR
            };
            error_response(status, text)
        }
    }
}

async fn handle_namespace_exists(
    State(state): State<Arc<HttpState>>,
    Path(namespace): Path<String>,
) -> Response {
    if state.ctx.namespace_exists(&namespace) {
        StatusCode::OK.into_response()
    } else {
        error_response(StatusCode::NOT_FOUND, "namespace not found")
    }
}

async fn handle_list_tables_in_namespace(
    State(state): State<Arc<HttpState>>,
    Path(namespace): Path<String>,
) -> Response {
    if !state.ctx.namespace_exists(&namespace) {
        return error_response(StatusCode::NOT_FOUND, "namespace not found");
    }
    handle_list_tables(State(state)).await.into_response()
}

async fn handle_list_tables_in_namespace_post(
    State(state): State<Arc<HttpState>>,
    Path(namespace): Path<String>,
) -> Response {
    if !state.ctx.namespace_exists(&namespace) {
        return error_response(StatusCode::NOT_FOUND, "namespace not found");
    }
    handle_list_tables(State(state)).await.into_response()
}

async fn handle_list_tables(State(state): State<Arc<HttpState>>) -> Json<TableListResponse> {
    let tables = state.ctx.table_names().into_iter().collect();
    Json(TableListResponse {
        tables,
        page_token: None,
    })
}

async fn handle_register_table(
    State(state): State<Arc<HttpState>>,
    Path(table): Path<String>,
    Json(req): Json<RegisterTableRequest>,
) -> Response {
    if table.trim().is_empty() || req.location.trim().is_empty() {
        return error_response(StatusCode::BAD_REQUEST, "table and location are required");
    }
    let mode = match parse_create_mode(req.mode.as_deref()) {
        Ok(mode) => mode,
        Err(error) => return error_response(StatusCode::BAD_REQUEST, error),
    };
    match state.ctx.register_table(&table, &req.location, mode).await {
        Ok(()) => (
            StatusCode::OK,
            Json(RegisterTableResponse {
                transaction_id: None,
                location: req.location,
                properties: None,
            }),
        )
            .into_response(),
        Err(error) => {
            let text = error.to_string();
            let status = if text.contains("already exists") {
                StatusCode::CONFLICT
            } else if text.contains("not implemented") || text.contains("only supported") {
                StatusCode::NOT_ACCEPTABLE
            } else if text.contains("not found") {
                StatusCode::NOT_FOUND
            } else {
                StatusCode::INTERNAL_SERVER_ERROR
            };
            error_response(status, text)
        }
    }
}

async fn handle_create_table(
    State(state): State<Arc<HttpState>>,
    Path(table): Path<String>,
    Query(params): Query<CreateTableParams>,
    headers: HeaderMap,
    body: Bytes,
) -> Response {
    if table.trim().is_empty() {
        return error_response(StatusCode::BAD_REQUEST, "table is required");
    }
    if body.is_empty() {
        return error_response(StatusCode::BAD_REQUEST, "body with schema is required");
    }

    let (schema, rows) = if is_json_content_type(&headers) {
        match serde_json::from_slice::<CreateTableJsonRequest>(&body) {
            Ok(req) => {
                let schema = match json_fields_to_arrow_schema(&req.fields) {
                    Ok(s) => s,
                    Err(e) => return error_response(StatusCode::BAD_REQUEST, e),
                };
                (schema, req.rows.unwrap_or_default())
            }
            Err(e) => return error_response(StatusCode::BAD_REQUEST, e.to_string()),
        }
    } else {
        match decode_arrow_stream(&body) {
            Ok(decoded) => (decoded.schema, decoded.rows),
            Err(error) => return error_response(StatusCode::BAD_REQUEST, error.to_string()),
        }
    };

    let mode = match parse_create_mode(params.mode.as_deref()) {
        Ok(mode) => mode,
        Err(error) => return error_response(StatusCode::BAD_REQUEST, error),
    };

    let result = if rows.is_empty() {
        state
            .ctx
            .create_empty_table(&table, schema, mode)
            .await
            .map(|_| 0)
    } else {
        state
            .ctx
            .create_table(&table, schema, rows, mode)
            .await
    };
    match result {
        Ok(_) => {
            let location = match state.ctx.table_location(&table).await {
                Ok(location) => location,
                Err(error) => {
                    return error_response(StatusCode::INTERNAL_SERVER_ERROR, error.to_string());
                }
            };
            (
                StatusCode::OK,
                Json(CreateTableResponse {
                    transaction_id: None,
                    location,
                    version: 1,
                    storage_options: Map::new(),
                    properties: None,
                }),
            )
                .into_response()
        }
        Err(error) => {
            let status = if error.to_string().contains("already exists") {
                StatusCode::CONFLICT
            } else {
                StatusCode::INTERNAL_SERVER_ERROR
            };
            error_response(status, error.to_string())
        }
    }
}

async fn handle_create_empty_table(
    State(state): State<Arc<HttpState>>,
    Path(table): Path<String>,
    Query(params): Query<CreateTableParams>,
    body: Bytes,
) -> Response {
    if table.trim().is_empty() {
        return error_response(StatusCode::BAD_REQUEST, "table is required");
    }
    if body.is_empty() {
        return error_response(
            StatusCode::BAD_REQUEST,
            "arrow stream body with schema is required",
        );
    }
    let decoded = match decode_arrow_stream(&body) {
        Ok(decoded) => decoded,
        Err(error) => return error_response(StatusCode::BAD_REQUEST, error.to_string()),
    };
    let mode = match parse_create_mode(params.mode.as_deref()) {
        Ok(mode) => mode,
        Err(error) => return error_response(StatusCode::BAD_REQUEST, error),
    };
    match state
        .ctx
        .create_empty_table(&table, decoded.schema, mode)
        .await
    {
        Ok(()) => match state.ctx.table_location(&table).await {
            Ok(location) => (
                StatusCode::OK,
                Json(CreateEmptyTableResponse {
                    transaction_id: None,
                    location,
                    storage_options: Map::new(),
                    properties: None,
                }),
            )
                .into_response(),
            Err(error) => error_response(StatusCode::INTERNAL_SERVER_ERROR, error.to_string()),
        },
        Err(error) => {
            let status = if error.to_string().contains("already exists") {
                StatusCode::CONFLICT
            } else {
                StatusCode::INTERNAL_SERVER_ERROR
            };
            error_response(status, error.to_string())
        }
    }
}

async fn handle_declare_table(
    State(state): State<Arc<HttpState>>,
    Path(table): Path<String>,
) -> Response {
    if table.trim().is_empty() {
        return error_response(StatusCode::BAD_REQUEST, "table is required");
    }
    let location = match state.ctx.table_location(&table).await {
        Ok(location) => Ok(location),
        Err(_) => state.ctx.declare_table(&table).await,
    };
    match location {
        Ok(location) => (
            StatusCode::OK,
            Json(DeclareTableResponse {
                transaction_id: None,
                location,
            }),
        )
            .into_response(),
        Err(error) => error_response(StatusCode::NOT_FOUND, error.to_string()),
    }
}

async fn handle_insert_rows(
    State(state): State<Arc<HttpState>>,
    Path(table): Path<String>,
    body: Bytes,
) -> Response {
    if table.trim().is_empty() {
        return error_response(StatusCode::BAD_REQUEST, "table is required");
    }
    if body.is_empty() {
        return error_response(StatusCode::BAD_REQUEST, "arrow stream body is required");
    }
    let decoded = match decode_arrow_stream(&body) {
        Ok(decoded) => decoded,
        Err(error) => return error_response(StatusCode::BAD_REQUEST, error.to_string()),
    };
    match state.ctx.insert_rows(&table, decoded.rows).await {
        Ok(_) => (
            StatusCode::OK,
            Json(InsertIntoTableResponse {
                transaction_id: None,
            }),
        )
            .into_response(),
        Err(error) => error_response(StatusCode::INTERNAL_SERVER_ERROR, error.to_string()),
    }
}

async fn handle_describe_table(
    State(state): State<Arc<HttpState>>,
    Path(table): Path<String>,
) -> Response {
    if table.trim().is_empty() {
        return error_response(StatusCode::BAD_REQUEST, "table is required");
    }
    match state.ctx.describe_table_schema(&table).await {
        Ok(schema) => {
            let location = match state.ctx.table_location(&table).await {
                Ok(location) => location,
                Err(error) => {
                    return error_response(StatusCode::INTERNAL_SERVER_ERROR, error.to_string());
                }
            };
            (
                StatusCode::OK,
                Json(TableDescribeResponse {
                    table: table.clone(),
                    namespace: vec!["default".into()],
                    version: 1,
                    location: location.clone(),
                    table_uri: location,
                    schema: schema_to_response(schema),
                    storage_options: Map::new(),
                    stats: None,
                    metadata: None,
                    properties: None,
                    managed_versioning: false,
                }),
            )
                .into_response()
        }
        Err(error) => {
            let status = if error.to_string().contains("No table named") {
                StatusCode::NOT_FOUND
            } else {
                StatusCode::INTERNAL_SERVER_ERROR
            };
            error_response(status, error.to_string())
        }
    }
}

async fn handle_table_exists(
    State(state): State<Arc<HttpState>>,
    Path(table): Path<String>,
) -> Response {
    if table_exists(state.ctx.as_ref(), &table).await {
        StatusCode::OK.into_response()
    } else {
        error_response(StatusCode::NOT_FOUND, "table not found")
    }
}

async fn handle_drop_table(
    State(state): State<Arc<HttpState>>,
    Path(table): Path<String>,
) -> Response {
    if table.trim().is_empty() {
        return error_response(StatusCode::BAD_REQUEST, "table is required");
    }
    let location = state.ctx.table_location(&table).await.unwrap_or_default();
    match state.ctx.drop_table(&table).await {
        Ok(()) => (
            StatusCode::OK,
            Json(DropTableResponse {
                transaction_id: None,
                id: vec![table],
                location,
                properties: None,
            }),
        )
            .into_response(),
        Err(error) => {
            let text = error.to_string();
            let status = if text.contains("not found") {
                StatusCode::NOT_FOUND
            } else if text.contains("not implemented") {
                StatusCode::NOT_ACCEPTABLE
            } else {
                StatusCode::INTERNAL_SERVER_ERROR
            };
            error_response(status, text)
        }
    }
}

async fn handle_update_table(
    State(state): State<Arc<HttpState>>,
    Path(table): Path<String>,
    Json(req): Json<UpdateTableRequest>,
) -> Response {
    let updates = parse_updates_value(req.updates);
    match state
        .ctx
        .update_table(&table, updates, req.predicate)
        .await
    {
        Ok((version, updated_rows)) => (
            StatusCode::OK,
            Json(UpdateTableResponse {
                transaction_id: None,
                updated_rows: updated_rows as i64,
                version,
                properties: None,
            }),
        )
            .into_response(),
        Err(error) => error_response(StatusCode::BAD_REQUEST, error.to_string()),
    }
}

async fn handle_optimize_table(
    State(state): State<Arc<HttpState>>,
    Path(table): Path<String>,
    Json(req): Json<OptimizeTableRequest>,
) -> Response {
    match state
        .ctx
        .optimize_table(
            &table,
            req.compact.unwrap_or(true),
            req.optimize_indices.unwrap_or(true),
            req.num_indices_to_merge,
        )
        .await
    {
        Ok(result) => (
            StatusCode::OK,
            Json(OptimizeTableResponse {
                transaction_id: None,
                version: result.version,
                fragments_removed: result.metrics.fragments_removed,
                fragments_added: result.metrics.fragments_added,
                files_removed: result.metrics.files_removed,
                files_added: result.metrics.files_added,
            }),
        )
            .into_response(),
        Err(error) => error_response(StatusCode::BAD_REQUEST, error.to_string()),
    }
}

async fn handle_cleanup_old_versions(
    State(state): State<Arc<HttpState>>,
    Path(table): Path<String>,
    Json(req): Json<CleanupOldVersionsRequest>,
) -> Response {
    match state
        .ctx
        .cleanup_old_versions(
            &table,
            req.older_than_seconds.unwrap_or(0),
            req.delete_unverified.unwrap_or(false),
            req.error_if_tagged_old_versions.unwrap_or(false),
        )
        .await
    {
        Ok(result) => (
            StatusCode::OK,
            Json(CleanupOldVersionsResponse {
                bytes_removed: result.bytes_removed,
                old_versions: result.old_versions,
            }),
        )
            .into_response(),
        Err(error) => error_response(StatusCode::BAD_REQUEST, error.to_string()),
    }
}

async fn handle_deregister_table(
    State(state): State<Arc<HttpState>>,
    Path(table): Path<String>,
) -> Response {
    match state.ctx.deregister_table(&table).await {
        Ok(location) => (
            StatusCode::OK,
            Json(DeregisterTableResponse {
                transaction_id: None,
                id: vec![table],
                location,
                properties: None,
            }),
        )
            .into_response(),
        Err(error) => {
            let text = error.to_string();
            let status = if text.contains("not implemented") {
                StatusCode::NOT_ACCEPTABLE
            } else if text.contains("not found") {
                StatusCode::NOT_FOUND
            } else {
                StatusCode::INTERNAL_SERVER_ERROR
            };
            error_response(status, text)
        }
    }
}

async fn handle_restore_table(
    State(state): State<Arc<HttpState>>,
    Path(table): Path<String>,
    Json(req): Json<RestoreTableRequest>,
) -> Response {
    match state.ctx.restore_table_version(&table, req.version).await {
        Ok(()) => (
            StatusCode::OK,
            Json(RestoreTableResponse {
                transaction_id: None,
            }),
        )
            .into_response(),
        Err(error) => {
            let text = error.to_string();
            let status = if text.contains("not implemented") {
                StatusCode::NOT_ACCEPTABLE
            } else if text.contains("not found") {
                StatusCode::NOT_FOUND
            } else if text.contains("version") {
                StatusCode::BAD_REQUEST
            } else {
                StatusCode::INTERNAL_SERVER_ERROR
            };
            error_response(status, text)
        }
    }
}

async fn handle_rename_table(
    State(state): State<Arc<HttpState>>,
    Path(table): Path<String>,
    Json(req): Json<RenameTableRequest>,
) -> Response {
    if table.trim().is_empty() || req.new_table_name.trim().is_empty() {
        return error_response(StatusCode::BAD_REQUEST, "table names are required");
    }
    match state.ctx.rename_table(&table, &req.new_table_name).await {
        Ok(()) => StatusCode::OK.into_response(),
        Err(error) => {
            let text = error.to_string();
            let status = if text.contains("already exists") {
                StatusCode::CONFLICT
            } else if text.contains("not implemented") {
                StatusCode::NOT_ACCEPTABLE
            } else if text.contains("not found") {
                StatusCode::NOT_FOUND
            } else {
                StatusCode::INTERNAL_SERVER_ERROR
            };
            error_response(status, text)
        }
    }
}

async fn handle_create_scalar_index(
    State(state): State<Arc<HttpState>>,
    Path(table): Path<String>,
    Json(req): Json<CreateScalarIndexRequest>,
) -> Response {
    let column = match resolve_index_column(req.column, req.columns, req.column_names) {
        Ok(column) => column,
        Err(error) => return error_response(StatusCode::BAD_REQUEST, error),
    };
    let index_type =
        match parse_scalar_index_type(req.index_type.as_deref().or(req.kind.as_deref())) {
            Ok(index_type) => index_type,
            Err(error) => return error_response(StatusCode::BAD_REQUEST, error),
        };
    match state
        .ctx
        .create_scalar_index(
            &table,
            &column,
            req.index_name.or(req.name),
            index_type,
            req.replace.unwrap_or(false),
        )
        .await
    {
        Ok(version) => (
            StatusCode::OK,
            Json(SchemaMutationResponse {
                transaction_id: None,
                version,
            }),
        )
            .into_response(),
        Err(error) => {
            let text = error.to_string();
            let status = if text.contains("already exists") {
                StatusCode::CONFLICT
            } else if text.contains("not found") {
                StatusCode::NOT_FOUND
            } else {
                StatusCode::BAD_REQUEST
            };
            error_response(status, text)
        }
    }
}

async fn handle_create_index(
    State(state): State<Arc<HttpState>>,
    Path(table): Path<String>,
    Json(req): Json<CreateIndexRequest>,
) -> Response {
    let column = match resolve_index_column(req.column, req.columns, req.column_names) {
        Ok(column) => column,
        Err(error) => return error_response(StatusCode::BAD_REQUEST, error),
    };
    let index_type = req
        .index_type
        .clone()
        .or(req.kind.clone())
        .unwrap_or_else(|| "scalar".to_string());
    if matches!(
        index_type.trim().to_ascii_lowercase().as_str(),
        "vector" | "ivf_pq" | "ivf_flat" | "ivf_hnsw_sq" | "ivf_hnsw_pq"
    ) {
        let metric_type =
            match parse_metric_type(req.metric_type.as_deref().or(req.distance_type.as_deref())) {
                Ok(metric_type) => metric_type,
                Err(error) => return error_response(StatusCode::BAD_REQUEST, error),
            };
        match state
            .ctx
            .create_vector_index(
                &table,
                &column,
                req.index_name.or(req.name),
                metric_type,
                &index_type,
                req.num_partitions,
                req.num_sub_vectors,
                req.hnsw_m,
                req.hnsw_ef_construction,
                req.replace.unwrap_or(false),
            )
            .await
        {
            Ok(version) => {
                return (
                    StatusCode::OK,
                    Json(SchemaMutationResponse {
                        transaction_id: None,
                        version,
                    }),
                )
                    .into_response();
            }
            Err(error) => return error_response(StatusCode::BAD_REQUEST, error.to_string()),
        }
    }
    handle_create_scalar_index(
        State(state),
        Path(table),
        Json(CreateScalarIndexRequest {
            column: Some(column),
            columns: None,
            column_names: None,
            index_name: req.index_name,
            name: req.name,
            index_type: Some(index_type),
            kind: None,
            replace: req.replace,
        }),
    )
    .await
}

async fn handle_list_indexes(
    State(state): State<Arc<HttpState>>,
    Path(table): Path<String>,
) -> Response {
    match state.ctx.list_table_indices(&table).await {
        Ok(indexes) => (
            StatusCode::OK,
            Json(ListIndexesResponse {
                indexes: indexes.into_iter().map(index_to_response).collect(),
            }),
        )
            .into_response(),
        Err(error) => {
            let text = error.to_string();
            let status = if text.contains("not found") {
                StatusCode::NOT_FOUND
            } else {
                StatusCode::BAD_REQUEST
            };
            error_response(status, text)
        }
    }
}

async fn handle_list_indexes_post(
    State(state): State<Arc<HttpState>>,
    Path(table): Path<String>,
) -> Response {
    handle_list_indexes(State(state), Path(table)).await
}

async fn handle_index_stats(
    State(state): State<Arc<HttpState>>,
    Path((table, index)): Path<(String, String)>,
) -> Response {
    match state.ctx.table_index_stats(&table, &index).await {
        Ok(stats) => (StatusCode::OK, Json(stats)).into_response(),
        Err(error) => {
            let text = error.to_string();
            let status = if text.contains("not found") || text.contains("does not exist") {
                StatusCode::NOT_FOUND
            } else {
                StatusCode::BAD_REQUEST
            };
            error_response(status, text)
        }
    }
}

async fn handle_index_stats_post(
    State(state): State<Arc<HttpState>>,
    Path((table, index)): Path<(String, String)>,
) -> Response {
    handle_index_stats(State(state), Path((table, index))).await
}

async fn handle_drop_index(
    State(state): State<Arc<HttpState>>,
    Path((table, index)): Path<(String, String)>,
) -> Response {
    match state.ctx.drop_table_index(&table, &index).await {
        Ok(()) => StatusCode::OK.into_response(),
        Err(error) => {
            let text = error.to_string();
            let status = if text.contains("not found") || text.contains("does not exist") {
                StatusCode::NOT_FOUND
            } else {
                StatusCode::BAD_REQUEST
            };
            error_response(status, text)
        }
    }
}

async fn handle_add_columns(
    State(state): State<Arc<HttpState>>,
    Path(table): Path<String>,
    Json(req): Json<AddColumnsRequest>,
) -> Response {
    let columns = req
        .columns
        .into_iter()
        .map(|column| {
            let name = column.name.trim().to_string();
            let expression = column.expression.trim().to_string();
            if name.is_empty() || expression.is_empty() {
                Err("column name and expression are required")
            } else {
                Ok((name, expression))
            }
        })
        .collect::<Result<Vec<_>, _>>();
    let columns = match columns {
        Ok(columns) => columns,
        Err(error) => return error_response(StatusCode::BAD_REQUEST, error),
    };
    match state.ctx.add_table_columns(&table, columns).await {
        Ok(version) => (
            StatusCode::OK,
            Json(SchemaMutationResponse {
                transaction_id: None,
                version,
            }),
        )
            .into_response(),
        Err(error) => schema_mutation_error_response(error),
    }
}

async fn handle_alter_columns(
    State(state): State<Arc<HttpState>>,
    Path(table): Path<String>,
    Json(req): Json<AlterColumnsRequest>,
) -> Response {
    let alterations = req
        .alterations
        .into_iter()
        .map(http_alteration_to_lance)
        .collect::<Result<Vec<_>, _>>();
    let alterations = match alterations {
        Ok(alterations) => alterations,
        Err(error) => return error_response(StatusCode::BAD_REQUEST, error),
    };
    match state.ctx.alter_table_columns(&table, alterations).await {
        Ok(version) => (
            StatusCode::OK,
            Json(SchemaMutationResponse {
                transaction_id: None,
                version,
            }),
        )
            .into_response(),
        Err(error) => schema_mutation_error_response(error),
    }
}

async fn handle_drop_columns(
    State(state): State<Arc<HttpState>>,
    Path(table): Path<String>,
    Json(req): Json<DropColumnsRequest>,
) -> Response {
    let columns = req
        .columns
        .into_iter()
        .map(|column| column.trim().to_string())
        .filter(|column| !column.is_empty())
        .collect::<Vec<_>>();
    if columns.is_empty() {
        return error_response(StatusCode::BAD_REQUEST, "columns are required");
    }
    match state.ctx.drop_table_columns(&table, columns).await {
        Ok(version) => (
            StatusCode::OK,
            Json(SchemaMutationResponse {
                transaction_id: None,
                version,
            }),
        )
            .into_response(),
        Err(error) => schema_mutation_error_response(error),
    }
}

async fn handle_update_schema_metadata(Json(metadata): Json<Map<String, Value>>) -> Response {
    (StatusCode::OK, Json(metadata)).into_response()
}

async fn handle_list_table_versions(
    State(state): State<Arc<HttpState>>,
    Path(table): Path<String>,
    Query(query): Query<VersionListQuery>,
) -> Response {
    match state
        .ctx
        .list_table_versions(&table, query.descending.unwrap_or(false))
        .await
    {
        Ok(versions) => (
            StatusCode::OK,
            Json(ListTableVersionsResponse {
                versions: versions_to_response(versions),
                page_token: None,
            }),
        )
            .into_response(),
        Err(error) => {
            let text = error.to_string();
            let status = if text.contains("not implemented") {
                StatusCode::NOT_ACCEPTABLE
            } else if text.contains("not found") {
                StatusCode::NOT_FOUND
            } else {
                StatusCode::INTERNAL_SERVER_ERROR
            };
            error_response(status, text)
        }
    }
}

async fn handle_create_table_version(
    State(state): State<Arc<HttpState>>,
    Path(table): Path<String>,
    Json(req): Json<CreateTableVersionRequest>,
) -> Response {
    match state
        .ctx
        .create_table_version(
            &table,
            req.version,
            req.put_if_not_exists.unwrap_or(false),
            req.metadata,
        )
        .await
    {
        Ok(version) => (
            StatusCode::OK,
            Json(CreateTableVersionResponse {
                transaction_id: None,
                version,
            }),
        )
            .into_response(),
        Err(error) => {
            let text = error.to_string();
            let status = if text.contains("already exists") {
                StatusCode::CONFLICT
            } else if text.contains("not found") {
                StatusCode::NOT_FOUND
            } else {
                StatusCode::BAD_REQUEST
            };
            error_response(status, text)
        }
    }
}

async fn handle_describe_table_version(
    State(state): State<Arc<HttpState>>,
    Path(table): Path<String>,
    Json(req): Json<DescribeTableVersionRequest>,
) -> Response {
    match state.ctx.describe_table_version(&table, req.version).await {
        Ok(detail) => (
            StatusCode::OK,
            Json(DescribeTableVersionResponse {
                version: detail.version,
                manifest_path: detail.manifest_path,
                transaction_file: detail.transaction_file,
                schema_fields: detail.schema_fields,
                config: detail.config,
            }),
        )
            .into_response(),
        Err(error) => {
            let text = error.to_string();
            let status = if text.contains("not found") || text.contains("does not exist") {
                StatusCode::NOT_FOUND
            } else {
                StatusCode::BAD_REQUEST
            };
            error_response(status, text)
        }
    }
}

async fn handle_delete_table_versions(
    State(state): State<Arc<HttpState>>,
    Path(table): Path<String>,
    Json(req): Json<DeleteTableVersionsRequest>,
) -> Response {
    let ranges = if let Some(version) = req.version {
        vec![(version, version)]
    } else if let Some(ranges) = req.ranges {
        ranges
            .into_iter()
            .map(|range| (range.start_version, range.end_version))
            .collect::<Vec<_>>()
    } else if let (Some(start), Some(end)) = (req.start_version, req.end_version) {
        vec![(start, end)]
    } else {
        return error_response(
            StatusCode::BAD_REQUEST,
            "version, ranges, or start_version/end_version is required",
        );
    };

    let mut deleted_versions = 0usize;
    for (start_version, end_version) in ranges {
        match state
            .ctx
            .delete_table_versions(&table, start_version, end_version)
            .await
        {
            Ok(count) => deleted_versions += count,
            Err(error) => {
                let text = error.to_string();
                let status = if text.contains("not implemented") {
                    StatusCode::NOT_ACCEPTABLE
                } else if text.contains("not found") {
                    StatusCode::NOT_FOUND
                } else {
                    StatusCode::BAD_REQUEST
                };
                return error_response(status, text);
            }
        }
    }

    (
        StatusCode::OK,
        Json(DeleteTableVersionsResponse {
            transaction_id: None,
            deleted_versions,
        }),
    )
        .into_response()
}

async fn handle_batch_create_table_versions(
    State(state): State<Arc<HttpState>>,
    Json(req): Json<BatchCreateVersionsRequest>,
) -> Response {
    let entries = req
        .entries
        .or(req.versions)
        .or(req.tables)
        .unwrap_or_default();
    if entries.is_empty() {
        return error_response(StatusCode::BAD_REQUEST, "entries are required");
    }

    let mut versions = Vec::with_capacity(entries.len());
    for entry in entries {
        let table = entry
            .id
            .as_ref()
            .and_then(|id| id.first())
            .map(|value| value.trim().to_string())
            .filter(|value| !value.is_empty())
            .unwrap_or_else(|| entry.table.trim().to_string());
        if table.is_empty() {
            return error_response(StatusCode::BAD_REQUEST, "table or id[0] is required");
        }
        match state
            .ctx
            .create_table_version(
                &table,
                entry.version,
                entry.put_if_not_exists.unwrap_or(false),
                entry.metadata,
            )
            .await
        {
            Ok(version) => versions.push(BatchCreatedVersionResponse { table, version }),
            Err(error) => {
                let text = error.to_string();
                let status = if text.contains("already exists") {
                    StatusCode::CONFLICT
                } else if text.contains("not found") {
                    StatusCode::NOT_FOUND
                } else {
                    StatusCode::BAD_REQUEST
                };
                return error_response(status, text);
            }
        }
    }

    (
        StatusCode::OK,
        Json(BatchCreateVersionsResponse {
            transaction_id: None,
            versions,
        }),
    )
        .into_response()
}

async fn handle_table_stats(
    State(state): State<Arc<HttpState>>,
    Path(table): Path<String>,
) -> Response {
    match state.ctx.table_stats(&table).await {
        Ok(stats) => (StatusCode::OK, Json(table_stats_to_response(stats))).into_response(),
        Err(error) => {
            let text = error.to_string();
            let status = if text.contains("not found") {
                StatusCode::NOT_FOUND
            } else {
                StatusCode::BAD_REQUEST
            };
            error_response(status, text)
        }
    }
}

async fn handle_explain_query(
    State(state): State<Arc<HttpState>>,
    Path(table): Path<String>,
    Json(req): Json<LanceQueryRequest>,
) -> Response {
    let sql = match build_lance_query_sql(&table, req) {
        Ok(sql) => sql,
        Err(error) => return error_response(StatusCode::BAD_REQUEST, error.to_string()),
    };
    match state.ctx.explain_table_query(&sql, false).await {
        Ok(plan) => (
            StatusCode::OK,
            [("content-type", "text/plain; charset=utf-8")],
            plan,
        )
            .into_response(),
        Err(error) => error_response(StatusCode::BAD_REQUEST, error.to_string()),
    }
}

async fn handle_analyze_query(
    State(state): State<Arc<HttpState>>,
    Path(table): Path<String>,
    Json(req): Json<LanceQueryRequest>,
) -> Response {
    let sql = match build_lance_query_sql(&table, req) {
        Ok(sql) => sql,
        Err(error) => return error_response(StatusCode::BAD_REQUEST, error.to_string()),
    };
    match state.ctx.explain_table_query(&sql, true).await {
        Ok(plan) => (
            StatusCode::OK,
            [("content-type", "text/plain; charset=utf-8")],
            plan,
        )
            .into_response(),
        Err(error) => error_response(StatusCode::BAD_REQUEST, error.to_string()),
    }
}

async fn handle_table_query(
    State(state): State<Arc<HttpState>>,
    Path(table): Path<String>,
    headers: HeaderMap,
    Json(req): Json<LanceQueryRequest>,
) -> Response {
    let want_json = wants_json(&headers);
    let sql = match build_lance_query_sql(&table, req) {
        Ok(sql) => sql,
        Err(error) => return error_response(StatusCode::BAD_REQUEST, error.to_string()),
    };
    if want_json {
        match state.ctx.collect_sql_pub(&sql).await {
            Ok(batches) => match rows_from_batches_http(&batches) {
                Ok(rows) => (StatusCode::OK, Json(QueryJsonResponse { rows })).into_response(),
                Err(error) => {
                    error_response(StatusCode::INTERNAL_SERVER_ERROR, error.to_string())
                }
            },
            Err(error) => error_response(StatusCode::INTERNAL_SERVER_ERROR, error.to_string()),
        }
    } else {
        match state.ctx.execute_sql(&sql).await {
            Ok(ipc_stream) => match encode_arrow_file(&ipc_stream) {
                Ok(ipc_file) => (
                    StatusCode::OK,
                    [("content-type", "application/vnd.apache.arrow.file")],
                    ipc_file,
                )
                    .into_response(),
                Err(error) => {
                    error_response(StatusCode::INTERNAL_SERVER_ERROR, error.to_string())
                }
            },
            Err(error) => error_response(StatusCode::INTERNAL_SERVER_ERROR, error.to_string()),
        }
    }
}

async fn handle_merge_insert(
    State(state): State<Arc<HttpState>>,
    Path(table): Path<String>,
    Query(params): Query<MergeInsertParams>,
    headers: HeaderMap,
    body: Bytes,
) -> Response {
    if table.trim().is_empty() {
        return error_response(StatusCode::BAD_REQUEST, "table is required");
    }
    if body.is_empty() {
        return error_response(StatusCode::BAD_REQUEST, "body is required");
    }
    let _ = params.when_matched_update_all.unwrap_or(true);
    let _ = params.when_not_matched_insert_all.unwrap_or(true);
    let (key_column, rows) = if is_json_content_type(&headers) {
        match serde_json::from_slice::<MergeInsertCompatRequest>(&body) {
            Ok(decoded) => {
                let key = resolve_merge_key(decoded.on.as_ref(), params.on.as_deref());
                (key, decoded.rows)
            }
            Err(error) => return error_response(StatusCode::BAD_REQUEST, error.to_string()),
        }
    } else {
        let key = params.on.as_deref().unwrap_or("_doc_id").to_string();
        match decode_arrow_stream(&body) {
            Ok(decoded) => (key, decoded.rows),
            Err(_) => match serde_json::from_slice::<MergeInsertCompatRequest>(&body) {
                Ok(decoded) => {
                    let key = resolve_merge_key(decoded.on.as_ref(), params.on.as_deref());
                    (key, decoded.rows)
                }
                Err(error) => return error_response(StatusCode::BAD_REQUEST, error.to_string()),
            },
        }
    };
    match state.ctx.upsert_rows(&table, &key_column, rows).await {
        Ok(_) => (
            StatusCode::OK,
            Json(MergeInsertIntoTableResponse {
                transaction_id: None,
                num_updated_rows: 0,
                num_inserted_rows: 0,
                num_deleted_rows: 0,
                version: 1,
            }),
        )
            .into_response(),
        Err(error) => error_response(StatusCode::INTERNAL_SERVER_ERROR, error.to_string()),
    }
}

async fn handle_delete(
    State(state): State<Arc<HttpState>>,
    Path(table): Path<String>,
    Json(req): Json<LanceDeleteRequest>,
) -> Response {
    if table.trim().is_empty() || req.predicate.trim().is_empty() {
        return error_response(StatusCode::BAD_REQUEST, "table and predicate are required");
    }
    match state.ctx.delete_rows(&table, &req.predicate).await {
        Ok(()) => (
            StatusCode::OK,
            Json(DeleteFromTableResponse {
                transaction_id: None,
                version: 1,
            }),
        )
            .into_response(),
        Err(error) => error_response(StatusCode::INTERNAL_SERVER_ERROR, error.to_string()),
    }
}

async fn handle_count_rows(
    State(state): State<Arc<HttpState>>,
    Path(table): Path<String>,
    headers: HeaderMap,
    Json(req): Json<LanceCountRowsRequest>,
) -> Response {
    if table.trim().is_empty() {
        return error_response(StatusCode::BAD_REQUEST, "table is required");
    }
    match state.ctx.count_rows(&table, req.filter.as_deref()).await {
        Ok(count) => {
            if wants_json(&headers) {
                (StatusCode::OK, Json(CountTableRowsResponse { count })).into_response()
            } else {
                (StatusCode::OK, count.to_string()).into_response()
            }
        }
        Err(error) => error_response(StatusCode::INTERNAL_SERVER_ERROR, error.to_string()),
    }
}

async fn handle_list_tags(
    State(state): State<Arc<HttpState>>,
    Path(table): Path<String>,
) -> Response {
    match state.ctx.list_table_tags(&table).await {
        Ok(tags) => (StatusCode::OK, Json(tags)).into_response(),
        Err(error) => {
            let text = error.to_string();
            let status = if text.contains("not found") {
                StatusCode::NOT_FOUND
            } else {
                StatusCode::BAD_REQUEST
            };
            error_response(status, text)
        }
    }
}

async fn handle_get_tag_version(
    State(state): State<Arc<HttpState>>,
    Path(table): Path<String>,
    Json(req): Json<TagRequest>,
) -> Response {
    match state.ctx.get_table_tag(&table, &req.tag).await {
        Ok(tag) => (
            StatusCode::OK,
            Json(TagVersionResponse {
                version: tag.version,
            }),
        )
            .into_response(),
        Err(error) => {
            let text = error.to_string();
            let status = if text.contains("does not exist") || text.contains("not found") {
                StatusCode::NOT_FOUND
            } else {
                StatusCode::BAD_REQUEST
            };
            error_response(status, text)
        }
    }
}

async fn handle_create_tag(
    State(state): State<Arc<HttpState>>,
    Path(table): Path<String>,
    Json(req): Json<TagUpdateRequest>,
) -> Response {
    let version = match i64::try_from(req.version) {
        Ok(version) => version,
        Err(_) => return error_response(StatusCode::BAD_REQUEST, "version is out of range"),
    };
    match state.ctx.create_table_tag(&table, &req.tag, version).await {
        Ok(()) => StatusCode::OK.into_response(),
        Err(error) => {
            let text = error.to_string();
            let status = if text.contains("already exists") {
                StatusCode::CONFLICT
            } else if text.contains("not found") {
                StatusCode::NOT_FOUND
            } else {
                StatusCode::BAD_REQUEST
            };
            error_response(status, text)
        }
    }
}

async fn handle_delete_tag(
    State(state): State<Arc<HttpState>>,
    Path(table): Path<String>,
    Json(req): Json<TagRequest>,
) -> Response {
    match state.ctx.delete_table_tag(&table, &req.tag).await {
        Ok(()) => StatusCode::OK.into_response(),
        Err(error) => {
            let text = error.to_string();
            let status = if text.contains("does not exist") || text.contains("not found") {
                StatusCode::NOT_FOUND
            } else {
                StatusCode::BAD_REQUEST
            };
            error_response(status, text)
        }
    }
}

async fn handle_update_tag(
    State(state): State<Arc<HttpState>>,
    Path(table): Path<String>,
    Json(req): Json<TagUpdateRequest>,
) -> Response {
    let version = match i64::try_from(req.version) {
        Ok(version) => version,
        Err(_) => return error_response(StatusCode::BAD_REQUEST, "version is out of range"),
    };
    match state.ctx.update_table_tag(&table, &req.tag, version).await {
        Ok(()) => StatusCode::OK.into_response(),
        Err(error) => {
            let text = error.to_string();
            let status = if text.contains("does not exist") || text.contains("not found") {
                StatusCode::NOT_FOUND
            } else {
                StatusCode::BAD_REQUEST
            };
            error_response(status, text)
        }
    }
}

async fn handle_transaction_alter(
    Path(_id): Path<String>,
    Json(_body): Json<Value>,
) -> Response {
    (
        StatusCode::OK,
        Json(serde_json::json!({
            "status": "Succeeded",
            "properties": {}
        })),
    )
        .into_response()
}

async fn handle_transaction_describe(
    Path(_id): Path<String>,
) -> Response {
    (
        StatusCode::OK,
        Json(serde_json::json!({
            "status": "Succeeded",
            "properties": {}
        })),
    )
        .into_response()
}

async fn handle_health() -> StatusCode {
    StatusCode::OK
}

async fn handle_metrics() -> impl IntoResponse {
    (
        StatusCode::OK,
        [(axum::http::header::CONTENT_TYPE, "text/plain; version=0.0.4; charset=utf-8")],
        crate::metrics::gather_text(),
    )
}

/// Axum middleware that records per-route HTTP request counts and latencies.
async fn track_http_metrics(req: Request, next: Next) -> impl IntoResponse {
    let route = req
        .extensions()
        .get::<MatchedPath>()
        .map(|m| m.as_str().to_owned())
        .unwrap_or_else(|| req.uri().path().to_owned());
    let method = req.method().as_str().to_owned();
    let start = Instant::now();
    let response = next.run(req).await;
    let elapsed = start.elapsed().as_secs_f64();
    let status = response.status().as_u16().to_string();
    crate::metrics::HTTP_REQUESTS
        .with_label_values(&[&method, &route, &status])
        .inc();
    crate::metrics::HTTP_DURATION
        .with_label_values(&[&method, &route])
        .observe(elapsed);
    response
}

struct DecodedArrowStream {
    schema: SchemaRef,
    rows: Vec<Map<String, Value>>,
}

fn wants_json(headers: &HeaderMap) -> bool {
    if let Some(accept) = headers.get("accept").and_then(|v| v.to_str().ok()) {
        return accept.contains("application/json");
    }
    is_json_content_type(headers)
}

fn rows_from_batches_http(
    batches: &[arrow::record_batch::RecordBatch],
) -> Result<Vec<Map<String, Value>>, Box<dyn std::error::Error + Send + Sync>> {
    let total_rows: usize = batches.iter().map(|b| b.num_rows()).sum();
    let mut rows = Vec::with_capacity(total_rows);
    for batch in batches {
        // Pre-allocate the serialisation buffer: ~256 bytes per row is a reasonable
        // lower-bound that avoids most reallocation for typical columnar payloads.
        let mut bytes = Vec::with_capacity(batch.num_rows().max(1) * 256);
        {
            let mut writer = ArrayWriter::new(&mut bytes);
            writer.write(batch)?;
            writer.finish()?;
        }
        let json_rows: Vec<Map<String, Value>> = serde_json::from_slice(&bytes)?;
        rows.extend(json_rows);
    }
    Ok(rows)
}

fn build_lance_query_sql(
    table: &str,
    req: LanceQueryRequest,
) -> Result<String, Box<dyn std::error::Error + Send + Sync>> {
    let table = table.trim();
    if table.is_empty() {
        return Err("table is required".into());
    }
    let projection = if let Some(columns) = req.columns {
        let names = columns.into_names();
        if names.iter().any(|name| name.trim().is_empty()) {
            return Err("column_names must not contain empty values".into());
        }
        if names.is_empty() {
            "*".to_string()
        } else {
            names
                .iter()
                .map(|name| quote_identifier(name))
                .collect::<Vec<_>>()
                .join(", ")
        }
    } else {
        "*".to_string()
    };

    let mut sql = format!("SELECT {projection} FROM {}", quote_identifier(table));
    if let Some(filter) = req.filter {
        if !filter.trim().is_empty() {
            sql.push_str(" WHERE ");
            sql.push_str(&filter);
        }
    }
    if let Some(order_by) = req.order_by {
        if !order_by.trim().is_empty() {
            sql.push_str(" ORDER BY ");
            sql.push_str(&order_by);
        }
    }
    if let Some(limit) = req.limit {
        sql.push_str(&format!(" LIMIT {limit}"));
    }
    if let Some(offset) = req.offset {
        sql.push_str(&format!(" OFFSET {offset}"));
    }
    Ok(sql)
}

fn decode_arrow_stream(
    bytes: &[u8],
) -> Result<DecodedArrowStream, Box<dyn std::error::Error + Send + Sync>> {
    let mut reader = StreamReader::try_new(Cursor::new(bytes), None)?;
    let schema = reader.schema();
    let mut rows = Vec::new();
    while let Some(batch) = reader.next() {
        let batch = batch?;
        let mut json = Vec::new();
        {
            let mut writer = ArrayWriter::new(&mut json);
            writer.write(&batch)?;
            writer.finish()?;
        }
        rows.extend(serde_json::from_slice::<Vec<Map<String, Value>>>(&json)?);
    }
    Ok(DecodedArrowStream { schema, rows })
}

fn schema_mutation_error_response(error: Box<dyn std::error::Error + Send + Sync>) -> Response {
    let text = error.to_string();
    let status = if text.contains("not found") || text.contains("No table named") {
        StatusCode::NOT_FOUND
    } else if text.contains("already exists") {
        StatusCode::CONFLICT
    } else {
        StatusCode::BAD_REQUEST
    };
    error_response(status, text)
}

fn http_alteration_to_lance(
    alteration: AlterColumnRequest,
) -> Result<ColumnAlteration, &'static str> {
    let path = alteration.path.trim().to_string();
    if path.is_empty() {
        return Err("alteration path is required");
    }
    let mut out = ColumnAlteration::new(path);
    if let Some(rename) = alteration.rename {
        let rename = rename.trim().to_string();
        if rename.is_empty() {
            return Err("rename must not be empty");
        }
        out = out.rename(rename);
    }
    if let Some(nullable) = alteration.nullable {
        out = out.set_nullable(nullable);
    }
    if let Some(data_type) = alteration.data_type {
        out = out.cast_to(parse_lance_data_type(&data_type)?);
    }
    Ok(out)
}

fn parse_lance_data_type(spec: &str) -> Result<arrow::datatypes::DataType, &'static str> {
    match spec.trim().to_ascii_lowercase().as_str() {
        "int64" | "bigint" => Ok(DataType::Int64),
        "int32" | "integer" => Ok(DataType::Int32),
        "float64" | "double" => Ok(DataType::Float64),
        "float32" | "float" => Ok(DataType::Float32),
        "bool" | "boolean" => Ok(DataType::Boolean),
        "string" | "utf8" => Ok(DataType::Utf8),
        "largeutf8" => Ok(DataType::LargeUtf8),
        "binary" => Ok(DataType::Binary),
        "largebinary" => Ok(DataType::LargeBinary),
        "timestamp_us" | "timestamp(microsecond)" => Ok(DataType::Timestamp(
            arrow::datatypes::TimeUnit::Microsecond,
            None,
        )),
        _ => Err("unsupported data_type"),
    }
}

fn encode_arrow_file(
    stream_bytes: &[u8],
) -> Result<Vec<u8>, Box<dyn std::error::Error + Send + Sync>> {
    let mut reader = StreamReader::try_new(Cursor::new(stream_bytes), None)?;
    let schema = reader.schema();
    let mut out = Vec::new();
    {
        let mut writer = FileWriter::try_new(&mut out, &schema)?;
        while let Some(batch) = reader.next() {
            writer.write(&batch?)?;
        }
        writer.finish()?;
    }
    Ok(out)
}

fn parse_create_mode(value: Option<&str>) -> Result<CreateTableMode, String> {
    match value
        .map(|value| value.trim().to_ascii_lowercase())
        .as_deref()
        .unwrap_or("create")
    {
        "create" => Ok(CreateTableMode::Create),
        "overwrite" => Ok(CreateTableMode::Overwrite),
        other => Err(format!("unsupported create mode: {other}")),
    }
}

fn schema_to_response(schema: SchemaRef) -> TableSchemaResponse {
    TableSchemaResponse {
        fields: schema
            .fields()
            .iter()
            .map(|field| TableFieldResponse {
                name: field.name().to_string(),
                dtype: data_type_name(field.data_type()),
                nullable: field.is_nullable(),
            })
            .collect(),
    }
}

fn data_type_name(dtype: &DataType) -> String {
    match dtype {
        DataType::Utf8 => "string".into(),
        DataType::Int64 => "int64".into(),
        DataType::Int32 => "int32".into(),
        DataType::Float64 => "float64".into(),
        DataType::Float32 => "float32".into(),
        DataType::Boolean => "bool".into(),
        DataType::Binary => "binary".into(),
        DataType::LargeBinary => "largebinary".into(),
        DataType::Timestamp(_, _) => "timestamp".into(),
        DataType::List(child) => format!("list<{}>", data_type_name(child.data_type())),
        DataType::FixedSizeList(child, size) => {
            format!(
                "fixed_size_list<{size},{}>",
                data_type_name(child.data_type())
            )
        }
        _ => format!("{dtype:?}").to_ascii_lowercase(),
    }
}

fn quote_identifier(value: &str) -> String {
    format!("\"{}\"", value.trim().replace('"', "\"\""))
}

fn wants_arrow_response(headers: &HeaderMap) -> bool {
    headers
        .get("accept")
        .and_then(|v| v.to_str().ok())
        .map(|accept| {
            accept.contains("application/vnd.apache.arrow")
                || accept.contains("application/x-arrow")
        })
        .unwrap_or(false)
}

fn is_json_content_type(headers: &HeaderMap) -> bool {
    headers
        .get("content-type")
        .and_then(|v| v.to_str().ok())
        .map(|ct| ct.contains("application/json"))
        .unwrap_or(false)
}

fn resolve_merge_key(json_on: Option<&Value>, param_on: Option<&str>) -> String {
    if let Some(on) = json_on {
        match on {
            Value::String(s) if !s.trim().is_empty() => return s.clone(),
            Value::Array(arr) => {
                if let Some(first) = arr.first().and_then(|v| v.as_str()) {
                    if !first.trim().is_empty() {
                        return first.to_string();
                    }
                }
            }
            _ => {}
        }
    }
    param_on.unwrap_or("_doc_id").to_string()
}

fn parse_updates_value(v: Value) -> BTreeMap<String, String> {
    match v {
        Value::Object(map) => map
            .into_iter()
            .filter_map(|(k, v)| v.as_str().map(|s| (k, s.to_string())))
            .collect(),
        Value::Array(pairs) => pairs
            .into_iter()
            .filter_map(|pair| {
                let arr = pair.as_array()?;
                if arr.len() >= 2 {
                    Some((arr[0].as_str()?.to_string(), arr[1].as_str()?.to_string()))
                } else {
                    None
                }
            })
            .collect(),
        _ => BTreeMap::new(),
    }
}

fn json_fields_to_arrow_schema(
    fields: &[CreateTableJsonField],
) -> Result<SchemaRef, String> {
    use arrow::datatypes::Field;
    if fields.is_empty() {
        return Err("at least one field is required".into());
    }
    let arrow_fields: Vec<Field> = fields
        .iter()
        .map(|f| {
            let dtype = parse_lance_data_type(&f.field_type)
                .map_err(|e| format!("field '{}': {}", f.name, e))?;
            Ok(Field::new(&f.name, dtype, f.nullable))
        })
        .collect::<Result<Vec<_>, String>>()?;
    Ok(Arc::new(arrow::datatypes::Schema::new(arrow_fields)))
}

fn versions_to_response(versions: Vec<TableVersionInfo>) -> Vec<TableVersionResponse> {
    versions
        .into_iter()
        .map(|version| TableVersionResponse {
            version: version.version,
        })
        .collect()
}

fn index_to_response(index: TableIndexInfo) -> IndexResponse {
    IndexResponse {
        name: index.name,
        fields: index.fields,
        dataset_version: index.dataset_version,
    }
}

fn table_stats_to_response(stats: TableStats) -> TableStatsResponse {
    TableStatsResponse {
        num_rows: stats.row_count,
        num_indices: stats.index_count,
        num_columns: stats.field_count,
        version: stats.version,
    }
}

fn string_map_to_json_map(map: &BTreeMap<String, String>) -> Map<String, Value> {
    map.iter()
        .map(|(key, value)| (key.clone(), Value::String(value.clone())))
        .collect()
}

fn parse_scalar_index_type(value: Option<&str>) -> Result<ScalarIndexType, &'static str> {
    match value
        .map(|value| value.trim().to_ascii_lowercase())
        .as_deref()
        .unwrap_or("scalar")
    {
        "scalar" | "btree" => Ok(ScalarIndexType::BTree),
        "bitmap" => Ok(ScalarIndexType::Bitmap),
        "label_list" | "labellist" => Ok(ScalarIndexType::LabelList),
        "inverted" | "fts" | "full_text" => Ok(ScalarIndexType::Inverted),
        _ => Err("unsupported scalar index type"),
    }
}

fn parse_metric_type(value: Option<&str>) -> Result<MetricType, &'static str> {
    match value
        .map(|value| value.trim().to_ascii_lowercase())
        .as_deref()
        .unwrap_or("l2")
    {
        "l2" => Ok(MetricType::L2),
        "cosine" => Ok(MetricType::Cosine),
        "dot" | "dotproduct" | "dot_product" => Ok(MetricType::Dot),
        "hamming" => Ok(MetricType::Hamming),
        _ => Err("unsupported metric type"),
    }
}

fn resolve_index_column(
    column: Option<String>,
    columns: Option<Vec<String>>,
    column_names: Option<Vec<String>>,
) -> Result<String, &'static str> {
    if let Some(column) = column {
        let column = column.trim().to_string();
        if !column.is_empty() {
            return Ok(column);
        }
    }
    let candidates = columns.or(column_names).unwrap_or_default();
    if candidates.len() != 1 {
        return Err("exactly one column is required");
    }
    let column = candidates[0].trim().to_string();
    if column.is_empty() {
        return Err("column is required");
    }
    Ok(column)
}

fn parse_namespace_create_mode(value: Option<&str>) -> Result<NamespaceCreateMode, String> {
    match value
        .map(|value| value.trim().to_ascii_lowercase())
        .as_deref()
        .unwrap_or("create")
    {
        "create" => Ok(NamespaceCreateMode::Create),
        "existok" | "exist_ok" => Ok(NamespaceCreateMode::ExistOk),
        "overwrite" => Ok(NamespaceCreateMode::Overwrite),
        other => Err(format!("unsupported namespace create mode: {other}")),
    }
}

fn parse_namespace_drop_mode(value: Option<&str>) -> Result<NamespaceDropMode, String> {
    match value
        .map(|value| value.trim().to_ascii_lowercase())
        .as_deref()
        .unwrap_or("fail")
    {
        "fail" => Ok(NamespaceDropMode::Fail),
        "skip" => Ok(NamespaceDropMode::Skip),
        other => Err(format!("unsupported namespace drop mode: {other}")),
    }
}

fn error_response(status: StatusCode, detail: impl ToString) -> Response {
    let detail_str = detail.to_string();
    (
        status,
        Json(ErrorResponse {
            error: detail_str.clone(),
            code: status.as_u16(),
            detail: if detail_str.is_empty() {
                None
            } else {
                Some(detail_str)
            },
            instance: None,
        }),
    )
        .into_response()
}

async fn table_exists(ctx: &TonboContext, table: &str) -> bool {
    if ctx.table_exists(table).ok().unwrap_or(false) {
        return true;
    }
    ctx.describe_table_schema(table).await.is_ok()
}

#[cfg(test)]
mod tests {
    use std::sync::Arc;

    use arrow::array::{FixedSizeListArray, Float32Array, Int64Array, StringArray};
    use arrow::datatypes::{DataType, Field, Schema};
    use arrow::record_batch::RecordBatch;
    use axum::body::{Body, to_bytes};
    use axum::http::{Request, StatusCode};
    use serde_json::{json, Value};
    use tempfile::tempdir;
    use tower::util::ServiceExt;

    use super::router;
    use crate::config::StorageConfig;
    use crate::context::TonboContext;

    async fn test_router()
    -> Result<(tempfile::TempDir, axum::Router), Box<dyn std::error::Error + Send + Sync>> {
        let dir = tempdir()?;
        let ctx = TonboContext::open(StorageConfig {
            lance_uri: dir.path().to_string_lossy().to_string(),
            s3: None,
            direct_tables: Vec::new(),
            eager_table_registration: true, ..Default::default()
        })
        .await?;
        ctx.execute_update_sql(
            "INSERT INTO people (_doc_id, name, age) VALUES ('p1', 'Alice', 30), ('p2', 'Bob', 41)",
        )
        .await?;
        Ok((dir, router(ctx)))
    }

    #[tokio::test]
    async fn health_route_returns_ok() -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let (_dir, app) = test_router().await?;
        let response = app
            .oneshot(Request::builder().uri("/health").body(Body::empty())?)
            .await?;
        assert_eq!(response.status(), StatusCode::OK);
        Ok(())
    }

    #[tokio::test]
    async fn transaction_routes_work() -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let (_dir, app) = test_router().await?;

        let alter = Request::builder()
            .method("POST")
            .uri("/v1/transaction/tx1/alter")
            .header("content-type", "application/json")
            .body(Body::from(json!({"actions": []}).to_string()))?;
        let alter_response = app.clone().oneshot(alter).await?;
        assert_eq!(alter_response.status(), StatusCode::OK);
        let alter_body: Value =
            serde_json::from_slice(&to_bytes(alter_response.into_body(), usize::MAX).await?)?;
        assert_eq!(alter_body["status"], "Succeeded");
        assert!(alter_body["properties"].is_object());

        let describe = Request::builder()
            .method("POST")
            .uri("/v1/transaction/tx1/describe")
            .body(Body::empty())?;
        let desc_response = app.clone().oneshot(describe).await?;
        assert_eq!(desc_response.status(), StatusCode::OK);
        let desc_body: Value =
            serde_json::from_slice(&to_bytes(desc_response.into_body(), usize::MAX).await?)?;
        assert_eq!(desc_body["status"], "Succeeded");
        assert!(desc_body["properties"].is_object());

        Ok(())
    }

    #[tokio::test]
    async fn error_response_matches_official_format() -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let (_dir, app) = test_router().await?;

        let bad_request = Request::builder()
            .method("POST")
            .uri("/v1/table/people/delete")
            .header("content-type", "application/json")
            .body(Body::from(json!({"predicate": ""}).to_string()))?;
        let response = app.clone().oneshot(bad_request).await?;
        assert_eq!(response.status(), StatusCode::BAD_REQUEST);
        let body: Value =
            serde_json::from_slice(&to_bytes(response.into_body(), usize::MAX).await?)?;
        assert!(body["error"].is_string(), "error field should be string");
        assert!(body["code"].is_number(), "code field should be number");
        assert_eq!(body["code"], 400);
        assert!(body.get("type").is_none(), "old 'type' field should not exist");
        assert!(body.get("title").is_none(), "old 'title' field should not exist");
        assert!(body.get("status").is_none(), "old 'status' field should not exist");

        Ok(())
    }

    #[tokio::test]
    async fn list_tables_returns_string_array() -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let (_dir, app) = test_router().await?;

        let response = app
            .clone()
            .oneshot(Request::builder().uri("/v1/table").body(Body::empty())?)
            .await?;
        assert_eq!(response.status(), StatusCode::OK);
        let body: Value =
            serde_json::from_slice(&to_bytes(response.into_body(), usize::MAX).await?)?;
        let tables = body["tables"].as_array().expect("tables should be array");
        for t in tables {
            assert!(t.is_string(), "each table should be a plain string, got: {}", t);
        }

        Ok(())
    }

    #[tokio::test]
    async fn namespace_and_table_metadata_routes_match_spec_basics()
    -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let (_dir, app) = test_router().await?;

        let create_namespace = app
            .clone()
            .oneshot(
                Request::builder()
                    .method("POST")
                    .uri("/v1/namespace/research/create")
                    .header("content-type", "application/json")
                    .body(Body::from(
                        json!({ "mode": "create", "properties": { "owner": "etzhayyim" } }).to_string(),
                    ))?,
            )
            .await?;
        assert_eq!(create_namespace.status(), StatusCode::OK);

        let namespace_exists = app
            .clone()
            .oneshot(
                Request::builder()
                    .method("POST")
                    .uri("/v1/namespace/default/exists")
                    .body(Body::empty())?,
            )
            .await?;
        assert_eq!(namespace_exists.status(), StatusCode::OK);

        let created_namespace_exists = app
            .clone()
            .oneshot(
                Request::builder()
                    .method("POST")
                    .uri("/v1/namespace/research/exists")
                    .body(Body::empty())?,
            )
            .await?;
        assert_eq!(created_namespace_exists.status(), StatusCode::OK);

        let namespace_describe = app
            .clone()
            .oneshot(
                Request::builder()
                    .method("POST")
                    .uri("/v1/namespace/research/describe")
                    .body(Body::from("{}"))?,
            )
            .await?;
        assert_eq!(namespace_describe.status(), StatusCode::OK);

        let tables = app
            .clone()
            .oneshot(
                Request::builder()
                    .uri("/v1/namespace/default/table/list")
                    .body(Body::empty())?,
            )
            .await?;
        assert_eq!(tables.status(), StatusCode::OK);

        let all_tables = app
            .clone()
            .oneshot(Request::builder().uri("/v1/table").body(Body::empty())?)
            .await?;
        assert_eq!(all_tables.status(), StatusCode::OK);

        let table_exists = app
            .clone()
            .oneshot(
                Request::builder()
                    .method("POST")
                    .uri("/v1/table/people/exists")
                    .body(Body::from("{}"))?,
            )
            .await?;
        assert_eq!(table_exists.status(), StatusCode::OK);

        let unsupported = app
            .clone()
            .oneshot(
                Request::builder()
                    .method("POST")
                    .uri("/v1/table/people/register")
                    .header("content-type", "application/json")
                    .body(Body::from(
                        json!({"location":"file:///tmp/people"}).to_string(),
                    ))?,
            )
            .await?;
        assert_eq!(unsupported.status(), StatusCode::CONFLICT);

        let drop_namespace = app
            .clone()
            .oneshot(
                Request::builder()
                    .method("POST")
                    .uri("/v1/namespace/research/drop")
                    .header("content-type", "application/json")
                    .body(Body::from(json!({ "mode": "fail" }).to_string()))?,
            )
            .await?;
        assert_eq!(drop_namespace.status(), StatusCode::OK);
        Ok(())
    }

    #[tokio::test]
    async fn query_route_returns_arrow_file() -> Result<(), Box<dyn std::error::Error + Send + Sync>>
    {
        let (_dir, app) = test_router().await?;

        let arrow_query = Request::builder()
            .method("POST")
            .uri("/v1/table/people/query")
            .header("content-type", "application/json")
            .header("accept", "application/vnd.apache.arrow.file")
            .body(Body::from(
                json!({
                    "filter": "age >= 30",
                    "limit": 10,
                    "order_by": "_doc_id ASC",
                    "columns": { "column_names": ["_doc_id", "name"] }
                })
                .to_string(),
            ))?;
        let response = app.clone().oneshot(arrow_query).await?;
        assert_eq!(response.status(), StatusCode::OK);
        assert_eq!(
            response.headers().get("content-type").unwrap(),
            "application/vnd.apache.arrow.file"
        );

        let json_query = Request::builder()
            .method("POST")
            .uri("/v1/table/people/query/")
            .header("content-type", "application/json")
            .header("accept", "application/json")
            .body(Body::from(
                json!({
                    "filter": "age >= 30",
                    "limit": 10,
                    "order_by": "_doc_id ASC",
                    "columns": ["_doc_id", "name"]
                })
                .to_string(),
            ))?;
        let response = app.clone().oneshot(json_query).await?;
        assert_eq!(response.status(), StatusCode::OK);
        assert_eq!(
            response.headers().get("content-type").unwrap(),
            "application/json"
        );
        let body = axum::body::to_bytes(response.into_body(), usize::MAX).await?;
        let parsed: Value = serde_json::from_slice(&body)?;
        assert!(parsed.get("rows").unwrap().is_array());

        Ok(())
    }

    #[tokio::test]
    async fn mutation_routes_work() -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let (_dir, app) = test_router().await?;

        let create = Request::builder()
            .method("POST")
            .uri("/v1/table/books/create?mode=overwrite")
            .header("content-type", "application/vnd.apache.arrow.stream")
            .body(Body::from(arrow_rows(vec![("b1", "Book A", 10)])?))?;
        let create_response = app.clone().oneshot(create).await?;
        assert_eq!(create_response.status(), StatusCode::OK);

        let insert = Request::builder()
            .method("POST")
            .uri("/v1/table/books/insert")
            .header("content-type", "application/vnd.apache.arrow.stream")
            .body(Body::from(arrow_rows(vec![("b2", "Book B", 20)])?))?;
        let insert_response = app.clone().oneshot(insert).await?;
        assert_eq!(insert_response.status(), StatusCode::OK);

        let merge = Request::builder()
            .method("POST")
            .uri("/v1/table/books/merge_insert?on=_doc_id")
            .header("content-type", "application/vnd.apache.arrow.stream")
            .body(Body::from(arrow_rows(vec![("b2", "Book B2", 30)])?))?;
        let merge_response = app.clone().oneshot(merge).await?;
        assert_eq!(merge_response.status(), StatusCode::OK);

        let merge_json = Request::builder()
            .method("POST")
            .uri("/v1/table/books/merge_insert")
            .header("content-type", "application/json")
            .body(Body::from(
                json!({
                    "on": "_doc_id",
                    "rows": [
                        {"_doc_id": "b2", "name": "Book B3", "age": 40}
                    ]
                })
                .to_string(),
            ))?;
        let merge_json_response = app.clone().oneshot(merge_json).await?;
        assert_eq!(merge_json_response.status(), StatusCode::OK);

        let merge_json_array_on = Request::builder()
            .method("POST")
            .uri("/v1/table/books/merge_insert/")
            .header("content-type", "application/json")
            .body(Body::from(
                json!({
                    "on": ["_doc_id"],
                    "rows": [
                        {"_doc_id": "b2", "name": "Book B4", "age": 50}
                    ]
                })
                .to_string(),
            ))?;
        let merge_json_array_response = app.clone().oneshot(merge_json_array_on).await?;
        assert_eq!(merge_json_array_response.status(), StatusCode::OK);

        let count = Request::builder()
            .method("POST")
            .uri("/v1/table/books/count_rows")
            .header("content-type", "application/json")
            .body(Body::from(json!({}).to_string()))?;
        let count_response = app.clone().oneshot(count).await?;
        assert_eq!(count_response.status(), StatusCode::OK);
        let payload: serde_json::Value =
            serde_json::from_slice(&to_bytes(count_response.into_body(), usize::MAX).await?)?;
        assert_eq!(payload["count"], 2);

        let delete = Request::builder()
            .method("POST")
            .uri("/v1/table/books/delete")
            .header("content-type", "application/json")
            .body(Body::from(
                json!({ "predicate": "_doc_id = 'b1'" }).to_string(),
            ))?;
        let delete_response = app.clone().oneshot(delete).await?;
        assert_eq!(delete_response.status(), StatusCode::OK);

        let drop_response = app
            .clone()
            .oneshot(
                Request::builder()
                    .method("POST")
                    .uri("/v1/table/books/drop")
                    .body(Body::empty())?,
            )
            .await?;
        assert_eq!(drop_response.status(), StatusCode::OK);
        Ok(())
    }

    #[tokio::test]
    async fn json_create_table_works() -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let (_dir, app) = test_router().await?;

        let create = Request::builder()
            .method("POST")
            .uri("/v1/table/json_books/create/?mode=overwrite")
            .header("content-type", "application/json")
            .body(Body::from(
                json!({
                    "fields": [
                        {"name": "_doc_id", "type": "string", "nullable": false},
                        {"name": "title", "type": "string"},
                        {"name": "pages", "type": "int64"}
                    ]
                })
                .to_string(),
            ))?;
        let response = app.clone().oneshot(create).await?;
        assert_eq!(response.status(), StatusCode::OK);
        let payload: Value =
            serde_json::from_slice(&to_bytes(response.into_body(), usize::MAX).await?)?;
        assert!(payload["location"].as_str().is_some());

        let exists = Request::builder()
            .method("POST")
            .uri("/v1/table/json_books/exists/")
            .header("content-type", "application/json")
            .body(Body::from("{}"))?;
        let exists_response = app.clone().oneshot(exists).await?;
        assert_eq!(exists_response.status(), StatusCode::OK);

        let describe = Request::builder()
            .method("POST")
            .uri("/v1/table/json_books/describe/")
            .body(Body::empty())?;
        let describe_response = app.clone().oneshot(describe).await?;
        assert_eq!(describe_response.status(), StatusCode::OK);
        let schema: Value =
            serde_json::from_slice(&to_bytes(describe_response.into_body(), usize::MAX).await?)?;
        let fields = schema["schema"]["fields"].as_array().expect(
            &format!("describe response has no schema.fields: {}", serde_json::to_string_pretty(&schema).unwrap()),
        );
        assert_eq!(fields.len(), 3);

        let merge = Request::builder()
            .method("POST")
            .uri("/v1/table/json_books/merge_insert/")
            .header("content-type", "application/json")
            .body(Body::from(
                json!({
                    "on": "_doc_id",
                    "rows": [{"_doc_id": "jb1", "title": "JSON Book", "pages": 100}]
                })
                .to_string(),
            ))?;
        let merge_response = app.clone().oneshot(merge).await?;
        assert_eq!(merge_response.status(), StatusCode::OK);

        let count = Request::builder()
            .method("POST")
            .uri("/v1/table/json_books/count_rows/")
            .header("content-type", "application/json")
            .body(Body::from("{}"))?;
        let count_response = app.clone().oneshot(count).await?;
        assert_eq!(count_response.status(), StatusCode::OK);
        let count_payload: Value =
            serde_json::from_slice(&to_bytes(count_response.into_body(), usize::MAX).await?)?;
        assert_eq!(count_payload["count"], 1);

        let drop = Request::builder()
            .method("POST")
            .uri("/v1/table/json_books/drop/")
            .body(Body::empty())?;
        let drop_response = app.clone().oneshot(drop).await?;
        assert_eq!(drop_response.status(), StatusCode::OK);

        Ok(())
    }

    #[tokio::test]
    async fn register_and_deregister_routes_work()
    -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let (_dir, app) = test_router().await?;

        let create = Request::builder()
            .method("POST")
            .uri("/v1/table/source_books/create?mode=overwrite")
            .header("content-type", "application/vnd.apache.arrow.stream")
            .body(Body::from(arrow_rows(vec![("s1", "Source", 1)])?))?;
        let create_response = app.clone().oneshot(create).await?;
        assert_eq!(create_response.status(), StatusCode::OK);
        let create_payload: serde_json::Value =
            serde_json::from_slice(&to_bytes(create_response.into_body(), usize::MAX).await?)?;
        let location = create_payload["location"].as_str().unwrap().to_string();

        let register = Request::builder()
            .method("POST")
            .uri("/v1/table/aliased_books/register")
            .header("content-type", "application/json")
            .body(Body::from(
                json!({ "location": location, "mode": "create" }).to_string(),
            ))?;
        let register_response = app.clone().oneshot(register).await?;
        assert_eq!(register_response.status(), StatusCode::OK);

        let describe = app
            .clone()
            .oneshot(
                Request::builder()
                    .method("POST")
                    .uri("/v1/table/aliased_books/describe")
                    .body(Body::from("{}"))?,
            )
            .await?;
        assert_eq!(describe.status(), StatusCode::OK);

        let deregister = app
            .clone()
            .oneshot(
                Request::builder()
                    .method("POST")
                    .uri("/v1/table/aliased_books/deregister")
                    .body(Body::from("{}"))?,
            )
            .await?;
        assert_eq!(deregister.status(), StatusCode::OK);
        Ok(())
    }

    #[tokio::test]
    async fn restore_route_restores_previous_version()
    -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let (dir, app) = test_router().await?;
        let table_uri = dir.path().join("restore_books");
        let table_uri = table_uri.to_string_lossy().to_string();
        let batch1 = arrow_batch(vec![("r1", "First", 1)])?;
        let batch2 = arrow_batch(vec![("r2", "Second", 2)])?;
        let schema1 = batch1.schema();
        let reader1 =
            arrow::record_batch::RecordBatchIterator::new(vec![Ok(batch1)].into_iter(), schema1);
        let mut dataset = lance::Dataset::write(reader1, &table_uri, None).await?;
        let schema2 = batch2.schema();
        let reader2 =
            arrow::record_batch::RecordBatchIterator::new(vec![Ok(batch2)].into_iter(), schema2);
        dataset.append(reader2, None).await?;

        let versions = app
            .clone()
            .oneshot(
                Request::builder()
                    .method("POST")
                    .uri("/v1/table/restore_books/version/list?descending=false")
                    .body(Body::empty())?,
            )
            .await?;
        assert_eq!(versions.status(), StatusCode::OK);
        let versions_payload: serde_json::Value =
            serde_json::from_slice(&to_bytes(versions.into_body(), usize::MAX).await?)?;
        let restore_version = versions_payload["versions"][0]["version"].as_i64().unwrap();

        let restore = Request::builder()
            .method("POST")
            .uri("/v1/table/restore_books/restore")
            .header("content-type", "application/json")
            .body(Body::from(
                json!({ "version": restore_version }).to_string(),
            ))?;
        let restore_response = app.clone().oneshot(restore).await?;
        assert_eq!(restore_response.status(), StatusCode::OK);

        let count = Request::builder()
            .method("POST")
            .uri("/v1/table/restore_books/count_rows")
            .header("content-type", "application/json")
            .body(Body::from(json!({}).to_string()))?;
        let count_response = app.clone().oneshot(count).await?;
        assert_eq!(count_response.status(), StatusCode::OK);
        let payload: serde_json::Value =
            serde_json::from_slice(&to_bytes(count_response.into_body(), usize::MAX).await?)?;
        assert_eq!(payload["count"], 1);
        Ok(())
    }

    #[tokio::test]
    async fn schema_evolution_routes_mutate_table_schema()
    -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let (_dir, app) = test_router().await?;

        let add_columns = Request::builder()
            .method("POST")
            .uri("/v1/table/people/add_columns")
            .header("content-type", "application/json")
            .body(Body::from(
                json!({
                    "columns": [
                        { "name": "age_plus", "expression": "age + 1" }
                    ]
                })
                .to_string(),
            ))?;
        let add_columns_response = app.clone().oneshot(add_columns).await?;
        assert_eq!(add_columns_response.status(), StatusCode::OK);

        let alter_columns = Request::builder()
            .method("POST")
            .uri("/v1/table/people/alter_columns")
            .header("content-type", "application/json")
            .body(Body::from(
                json!({
                    "alterations": [
                        { "path": "age_plus", "rename": "age_next", "data_type": "int64" }
                    ]
                })
                .to_string(),
            ))?;
        let alter_columns_response = app.clone().oneshot(alter_columns).await?;
        assert_eq!(alter_columns_response.status(), StatusCode::OK);

        let describe_after_alter = app
            .clone()
            .oneshot(
                Request::builder()
                    .method("POST")
                    .uri("/v1/table/people/describe")
                    .body(Body::from("{}"))?,
            )
            .await?;
        assert_eq!(describe_after_alter.status(), StatusCode::OK);
        let describe_after_alter_payload: serde_json::Value =
            serde_json::from_slice(&to_bytes(describe_after_alter.into_body(), usize::MAX).await?)?;
        let field_names = describe_after_alter_payload["schema"]["fields"]
            .as_array()
            .unwrap()
            .iter()
            .filter_map(|field| field["name"].as_str())
            .collect::<Vec<_>>();
        assert!(field_names.contains(&"age_next"));

        let drop_columns = Request::builder()
            .method("POST")
            .uri("/v1/table/people/drop_columns")
            .header("content-type", "application/json")
            .body(Body::from(json!({ "columns": ["age_next"] }).to_string()))?;
        let drop_columns_response = app.clone().oneshot(drop_columns).await?;
        assert_eq!(drop_columns_response.status(), StatusCode::OK);

        let describe_after_drop = app
            .clone()
            .oneshot(
                Request::builder()
                    .method("POST")
                    .uri("/v1/table/people/describe")
                    .body(Body::from("{}"))?,
            )
            .await?;
        assert_eq!(describe_after_drop.status(), StatusCode::OK);
        let describe_after_drop_payload: serde_json::Value =
            serde_json::from_slice(&to_bytes(describe_after_drop.into_body(), usize::MAX).await?)?;
        let field_names = describe_after_drop_payload["schema"]["fields"]
            .as_array()
            .unwrap()
            .iter()
            .filter_map(|field| field["name"].as_str())
            .collect::<Vec<_>>();
        assert!(!field_names.contains(&"age_next"));
        Ok(())
    }

    #[tokio::test]
    async fn update_and_scalar_index_routes_work()
    -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let (_dir, app) = test_router().await?;

        let update = Request::builder()
            .method("POST")
            .uri("/v1/table/people/update")
            .header("content-type", "application/json")
            .body(Body::from(
                json!({
                    "updates": { "age": "age + 1" },
                    "predicate": "_doc_id = 'p1'"
                })
                .to_string(),
            ))?;
        let update_response = app.clone().oneshot(update).await?;
        assert_eq!(update_response.status(), StatusCode::OK);

        let query = Request::builder()
            .method("POST")
            .uri("/v1/table/people/query")
            .header("content-type", "application/json")
            .body(Body::from(
                json!({
                    "filter": "_doc_id = 'p1'",
                    "columns": { "column_names": ["age"] }
                })
                .to_string(),
            ))?;
        let query_response = app.clone().oneshot(query).await?;
        assert_eq!(query_response.status(), StatusCode::OK);

        let create_index = Request::builder()
            .method("POST")
            .uri("/v1/table/people/create_scalar_index")
            .header("content-type", "application/json")
            .body(Body::from(
                json!({
                    "columns": ["age"],
                    "name": "age_idx",
                    "type": "btree"
                })
                .to_string(),
            ))?;
        let create_index_response = app.clone().oneshot(create_index).await?;
        assert_eq!(create_index_response.status(), StatusCode::OK);

        let list_indexes = app
            .clone()
            .oneshot(
                Request::builder()
                    .uri("/v1/table/people/index/list")
                    .body(Body::empty())?,
            )
            .await?;
        assert_eq!(list_indexes.status(), StatusCode::OK);
        let list_indexes_payload: serde_json::Value =
            serde_json::from_slice(&to_bytes(list_indexes.into_body(), usize::MAX).await?)?;
        assert_eq!(list_indexes_payload["indexes"][0]["name"], "age_idx");

        let stats = app
            .clone()
            .oneshot(
                Request::builder()
                    .uri("/v1/table/people/index/age_idx/stats")
                    .body(Body::empty())?,
            )
            .await?;
        assert_eq!(stats.status(), StatusCode::OK);
        let stats_payload: serde_json::Value =
            serde_json::from_slice(&to_bytes(stats.into_body(), usize::MAX).await?)?;
        assert!(stats_payload.is_object());
        Ok(())
    }

    #[tokio::test]
    async fn optimize_cleanup_and_vector_index_routes_work()
    -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let (dir, app) = test_router().await?;

        let optimize = Request::builder()
            .method("POST")
            .uri("/v1/table/people/optimize")
            .header("content-type", "application/json")
            .body(Body::from(
                json!({ "compact": true, "optimize_indices": false }).to_string(),
            ))?;
        let optimize_response = app.clone().oneshot(optimize).await?;
        assert_eq!(optimize_response.status(), StatusCode::OK);

        let cleanup = Request::builder()
            .method("POST")
            .uri("/v1/table/people/cleanup_old_versions")
            .header("content-type", "application/json")
            .body(Body::from(
                json!({ "older_than_seconds": 0, "delete_unverified": false }).to_string(),
            ))?;
        let cleanup_response = app.clone().oneshot(cleanup).await?;
        assert_eq!(cleanup_response.status(), StatusCode::OK);

        let vector_create = Request::builder()
            .method("POST")
            .uri("/v1/table/embeddings/create?mode=overwrite")
            .header("content-type", "application/vnd.apache.arrow.stream")
            .body(Body::from(arrow_vector_rows()?))?;
        let vector_create_response = app.clone().oneshot(vector_create).await?;
        assert_eq!(vector_create_response.status(), StatusCode::OK);

        let vector_index = Request::builder()
            .method("POST")
            .uri("/v1/table/embeddings/create_index")
            .header("content-type", "application/json")
            .body(Body::from(
                json!({
                    "column_names": ["vector"],
                    "name": "vector_idx",
                    "type": "ivf_hnsw_sq",
                    "distance_type": "l2",
                    "num_partitions": 2,
                    "hnsw_m": 8,
                    "hnsw_ef_construction": 50
                })
                .to_string(),
            ))?;
        let vector_index_response = app.clone().oneshot(vector_index).await?;
        assert_eq!(vector_index_response.status(), StatusCode::OK);

        let stats = app
            .clone()
            .oneshot(
                Request::builder()
                    .uri("/v1/table/embeddings/index/vector_idx/stats")
                    .body(Body::empty())?,
            )
            .await?;
        assert_eq!(stats.status(), StatusCode::OK);

        let list_indexes_post = app
            .clone()
            .oneshot(
                Request::builder()
                    .method("POST")
                    .uri("/v1/table/embeddings/index/list")
                    .body(Body::from("{}"))?,
            )
            .await?;
        assert_eq!(list_indexes_post.status(), StatusCode::OK);

        let stats_post = app
            .clone()
            .oneshot(
                Request::builder()
                    .method("POST")
                    .uri("/v1/table/embeddings/index/vector_idx/stats")
                    .body(Body::from("{}"))?,
            )
            .await?;
        assert_eq!(stats_post.status(), StatusCode::OK);

        let drop_index = app
            .clone()
            .oneshot(
                Request::builder()
                    .method("POST")
                    .uri("/v1/table/embeddings/index/vector_idx/drop")
                    .body(Body::from("{}"))?,
            )
            .await?;
        assert_eq!(drop_index.status(), StatusCode::OK);

        let dropped_stats = app
            .clone()
            .oneshot(
                Request::builder()
                    .method("POST")
                    .uri("/v1/table/embeddings/index/vector_idx/stats")
                    .body(Body::from("{}"))?,
            )
            .await?;
        assert_eq!(dropped_stats.status(), StatusCode::NOT_FOUND);
        let _ = dir;
        Ok(())
    }

    #[tokio::test]
    async fn stats_explain_and_declare_routes_work()
    -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let (_dir, app) = test_router().await?;

        let create_empty = Request::builder()
            .method("POST")
            .uri("/v1/table/empty_people/create-empty/?mode=overwrite")
            .header("content-type", "application/vnd.apache.arrow.stream")
            .body(Body::from(arrow_rows(vec![])?))?;
        let create_empty_response = app.clone().oneshot(create_empty).await?;
        assert_eq!(create_empty_response.status(), StatusCode::OK);

        let declare = Request::builder()
            .method("POST")
            .uri("/v1/table/empty_people/declare")
            .body(Body::empty())?;
        let declare_response = app.clone().oneshot(declare).await?;
        assert_eq!(declare_response.status(), StatusCode::OK);
        let declare_payload: serde_json::Value =
            serde_json::from_slice(&to_bytes(declare_response.into_body(), usize::MAX).await?)?;
        assert!(
            declare_payload["location"]
                .as_str()
                .unwrap_or_default()
                .contains("empty_people")
        );

        let stats = Request::builder()
            .method("POST")
            .uri("/v1/table/people/stats/")
            .body(Body::from("{}"))?;
        let stats_response = app.clone().oneshot(stats).await?;
        assert_eq!(stats_response.status(), StatusCode::OK);
        let stats_payload: serde_json::Value =
            serde_json::from_slice(&to_bytes(stats_response.into_body(), usize::MAX).await?)?;
        assert!(stats_payload["num_rows"].as_u64().unwrap_or_default() > 0);

        let explain = Request::builder()
            .method("POST")
            .uri("/v1/table/people/explain_plan/")
            .header("content-type", "application/json")
            .body(Body::from(
                json!({
                    "filter": "age >= 30",
                    "limit": 1
                })
                .to_string(),
            ))?;
        let explain_response = app.clone().oneshot(explain).await?;
        assert_eq!(explain_response.status(), StatusCode::OK);
        let explain_body = String::from_utf8(
            to_bytes(explain_response.into_body(), usize::MAX)
                .await?
                .to_vec(),
        )?;
        assert!(!explain_body.trim().is_empty());

        let analyze = Request::builder()
            .method("POST")
            .uri("/v1/table/people/analyze_plan/")
            .header("content-type", "application/json")
            .body(Body::from(
                json!({
                    "filter": "age >= 30",
                    "limit": 1
                })
                .to_string(),
            ))?;
        let analyze_response = app.clone().oneshot(analyze).await?;
        assert_eq!(analyze_response.status(), StatusCode::OK);
        let analyze_body = String::from_utf8(
            to_bytes(analyze_response.into_body(), usize::MAX)
                .await?
                .to_vec(),
        )?;
        assert!(!analyze_body.trim().is_empty());

        let create_version = Request::builder()
            .method("POST")
            .uri("/v1/table/people/version/create/")
            .header("content-type", "application/json")
            .body(Body::from(
                json!({
                    "put_if_not_exists": true,
                    "metadata": { "source": "test" }
                })
                .to_string(),
            ))?;
        let create_version_response = app.clone().oneshot(create_version).await?;
        assert_eq!(create_version_response.status(), StatusCode::OK);
        let create_version_payload: serde_json::Value = serde_json::from_slice(
            &to_bytes(create_version_response.into_body(), usize::MAX).await?,
        )?;
        let created_version = create_version_payload["version"]
            .as_i64()
            .expect("created version");

        let describe_version = Request::builder()
            .method("POST")
            .uri("/v1/table/people/version/describe/")
            .header("content-type", "application/json")
            .body(Body::from(
                json!({ "version": created_version }).to_string(),
            ))?;
        let describe_version_response = app.clone().oneshot(describe_version).await?;
        assert_eq!(describe_version_response.status(), StatusCode::OK);

        let batch_create = Request::builder()
            .method("POST")
            .uri("/v1/table/version/batch-create")
            .header("content-type", "application/json")
            .body(Body::from(
                json!({
                    "entries": [
                        { "id": ["people"], "put_if_not_exists": true }
                    ]
                })
                .to_string(),
            ))?;
        let batch_create_response = app.clone().oneshot(batch_create).await?;
        assert_eq!(batch_create_response.status(), StatusCode::OK);

        let delete_version = Request::builder()
            .method("POST")
            .uri("/v1/table/people/version/delete/")
            .header("content-type", "application/json")
            .body(Body::from(
                json!({
                    "ranges": [
                        { "start_version": created_version, "end_version": created_version }
                    ]
                })
                .to_string(),
            ))?;
        let delete_version_response = app.clone().oneshot(delete_version).await?;
        assert_eq!(delete_version_response.status(), StatusCode::OK);
        Ok(())
    }

    #[tokio::test]
    async fn table_version_routes_work() -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let (_dir, app) = test_router().await?;

        let create_version = Request::builder()
            .method("POST")
            .uri("/v1/table/people/version/create")
            .header("content-type", "application/json")
            .body(Body::from(
                json!({
                    "metadata": {
                        "label": "snapshot"
                    }
                })
                .to_string(),
            ))?;
        let create_version_response = app.clone().oneshot(create_version).await?;
        assert_eq!(create_version_response.status(), StatusCode::OK);
        let create_version_payload: serde_json::Value = serde_json::from_slice(
            &to_bytes(create_version_response.into_body(), usize::MAX).await?,
        )?;
        let created_version = create_version_payload["version"]
            .as_i64()
            .expect("created version");

        let describe_version = Request::builder()
            .method("POST")
            .uri("/v1/table/people/version/describe")
            .header("content-type", "application/json")
            .body(Body::from(
                json!({
                    "version": created_version
                })
                .to_string(),
            ))?;
        let describe_version_response = app.clone().oneshot(describe_version).await?;
        assert_eq!(describe_version_response.status(), StatusCode::OK);
        let describe_version_payload: serde_json::Value = serde_json::from_slice(
            &to_bytes(describe_version_response.into_body(), usize::MAX).await?,
        )?;
        assert_eq!(
            describe_version_payload["version"].as_i64(),
            Some(created_version)
        );

        let batch_create = Request::builder()
            .method("POST")
            .uri("/v1/table/version/batch-create")
            .header("content-type", "application/json")
            .body(Body::from(
                json!({
                    "entries": [
                        { "table": "people", "metadata": { "batch": "one" } },
                        { "table": "people", "metadata": { "batch": "two" } }
                    ]
                })
                .to_string(),
            ))?;
        let batch_create_response = app.clone().oneshot(batch_create).await?;
        assert_eq!(batch_create_response.status(), StatusCode::OK);
        let batch_create_payload: serde_json::Value = serde_json::from_slice(
            &to_bytes(batch_create_response.into_body(), usize::MAX).await?,
        )?;
        assert_eq!(
            batch_create_payload["versions"]
                .as_array()
                .map(|versions| versions.len()),
            Some(2)
        );

        let delete_version = Request::builder()
            .method("POST")
            .uri("/v1/table/people/version/delete")
            .header("content-type", "application/json")
            .body(Body::from(
                json!({
                    "version": created_version
                })
                .to_string(),
            ))?;
        let delete_version_response = app.clone().oneshot(delete_version).await?;
        assert_eq!(delete_version_response.status(), StatusCode::OK);
        let delete_version_payload: serde_json::Value = serde_json::from_slice(
            &to_bytes(delete_version_response.into_body(), usize::MAX).await?,
        )?;
        assert_eq!(delete_version_payload["deleted_versions"].as_u64(), Some(1));

        Ok(())
    }

    #[tokio::test]
    async fn tag_routes_work() -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let (_dir, app) = test_router().await?;

        let create = Request::builder()
            .method("POST")
            .uri("/v1/table/tag_books/create?mode=overwrite")
            .header("content-type", "application/vnd.apache.arrow.stream")
            .body(Body::from(arrow_rows(vec![("t1", "Tag Book", 1)])?))?;
        let create_response = app.clone().oneshot(create).await?;
        assert_eq!(create_response.status(), StatusCode::OK);

        let create_tag = Request::builder()
            .method("POST")
            .uri("/v1/table/tag_books/tags/create/")
            .header("content-type", "application/json")
            .body(Body::from(json!({ "tag": "v1", "version": 1 }).to_string()))?;
        let create_tag_response = app.clone().oneshot(create_tag).await?;
        assert_eq!(create_tag_response.status(), StatusCode::OK);

        let list_tags = Request::builder()
            .method("POST")
            .uri("/v1/table/tag_books/tags/list/")
            .body(Body::from("{}"))?;
        let list_tags_response = app.clone().oneshot(list_tags).await?;
        assert_eq!(list_tags_response.status(), StatusCode::OK);
        let list_tags_payload: serde_json::Value =
            serde_json::from_slice(&to_bytes(list_tags_response.into_body(), usize::MAX).await?)?;
        assert_eq!(list_tags_payload["v1"]["version"], 1);

        let insert = Request::builder()
            .method("POST")
            .uri("/v1/table/tag_books/insert")
            .header("content-type", "application/vnd.apache.arrow.stream")
            .body(Body::from(arrow_rows(vec![("t2", "Tag Book 2", 2)])?))?;
        let insert_response = app.clone().oneshot(insert).await?;
        assert_eq!(insert_response.status(), StatusCode::OK);

        let versions = Request::builder()
            .method("POST")
            .uri("/v1/table/tag_books/version/list/")
            .header("content-type", "application/json")
            .body(Body::from("{}"))?;
        let versions_response = app.clone().oneshot(versions).await?;
        assert_eq!(versions_response.status(), StatusCode::OK);
        let versions_payload: serde_json::Value =
            serde_json::from_slice(&to_bytes(versions_response.into_body(), usize::MAX).await?)?;
        let latest_version = versions_payload["versions"]
            .as_array()
            .and_then(|versions| {
                versions
                    .iter()
                    .filter_map(|version| version["version"].as_i64())
                    .max()
            })
            .expect("latest version");

        let update_tag = Request::builder()
            .method("POST")
            .uri("/v1/table/tag_books/tags/update/")
            .header("content-type", "application/json")
            .body(Body::from(
                json!({ "tag": "v1", "version": latest_version }).to_string(),
            ))?;
        let update_tag_response = app.clone().oneshot(update_tag).await?;
        assert_eq!(update_tag_response.status(), StatusCode::OK);

        let get_tag = Request::builder()
            .method("POST")
            .uri("/v1/table/tag_books/tags/version/")
            .header("content-type", "application/json")
            .body(Body::from(json!({ "tag": "v1" }).to_string()))?;
        let get_tag_response = app.clone().oneshot(get_tag).await?;
        assert_eq!(get_tag_response.status(), StatusCode::OK);
        let get_tag_payload: serde_json::Value =
            serde_json::from_slice(&to_bytes(get_tag_response.into_body(), usize::MAX).await?)?;
        assert_eq!(get_tag_payload["version"].as_i64(), Some(latest_version));

        let delete_tag = Request::builder()
            .method("POST")
            .uri("/v1/table/tag_books/tags/delete/")
            .header("content-type", "application/json")
            .body(Body::from(json!({ "tag": "v1" }).to_string()))?;
        let delete_tag_response = app.clone().oneshot(delete_tag).await?;
        assert_eq!(delete_tag_response.status(), StatusCode::OK);
        Ok(())
    }

    fn arrow_rows(
        rows: Vec<(&str, &str, i64)>,
    ) -> Result<Vec<u8>, Box<dyn std::error::Error + Send + Sync>> {
        let batch = arrow_batch(rows)?;
        let schema = batch.schema();
        let mut out = Vec::new();
        {
            let mut writer = arrow_ipc::writer::StreamWriter::try_new(&mut out, &schema)?;
            writer.write(&batch)?;
            writer.finish()?;
        }
        Ok(out)
    }

    fn arrow_vector_rows() -> Result<Vec<u8>, Box<dyn std::error::Error + Send + Sync>> {
        let schema = Arc::new(Schema::new(vec![
            Field::new("_doc_id", DataType::Utf8, false),
            Field::new(
                "vector",
                DataType::FixedSizeList(Arc::new(Field::new("item", DataType::Float32, true)), 2),
                false,
            ),
        ]));
        let ids = Arc::new(StringArray::from(vec!["v1", "v2", "v3", "v4"]));
        let values = Arc::new(Float32Array::from(vec![
            1.0, 0.0, 0.9, 0.1, 0.0, 1.0, 0.1, 0.9,
        ]));
        let vectors = Arc::new(FixedSizeListArray::try_new(
            Arc::new(Field::new("item", DataType::Float32, true)),
            2,
            values,
            None,
        )?);
        let batch = RecordBatch::try_new(schema.clone(), vec![ids, vectors])?;
        let mut out = Vec::new();
        {
            let mut writer = arrow_ipc::writer::StreamWriter::try_new(&mut out, &schema)?;
            writer.write(&batch)?;
            writer.finish()?;
        }
        Ok(out)
    }

    fn arrow_batch(
        rows: Vec<(&str, &str, i64)>,
    ) -> Result<RecordBatch, Box<dyn std::error::Error + Send + Sync>> {
        let schema = Arc::new(Schema::new(vec![
            Field::new("_doc_id", DataType::Utf8, false),
            Field::new("name", DataType::Utf8, true),
            Field::new("age", DataType::Int64, true),
        ]));
        Ok(RecordBatch::try_new(
            schema.clone(),
            vec![
                Arc::new(StringArray::from(
                    rows.iter()
                        .map(|(doc_id, _, _)| *doc_id)
                        .collect::<Vec<_>>(),
                )),
                Arc::new(StringArray::from(
                    rows.iter().map(|(_, name, _)| *name).collect::<Vec<_>>(),
                )),
                Arc::new(Int64Array::from(
                    rows.iter().map(|(_, _, age)| *age).collect::<Vec<_>>(),
                )),
            ],
        )?)
    }
}
