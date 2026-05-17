use std::any::Any;
use std::collections::{BTreeMap, BTreeSet, HashMap};
use std::path::Path;
use std::sync::Arc;
use std::time::{Instant, SystemTime, UNIX_EPOCH};

use dashmap::DashMap;

use arrow::array::{
    ArrayRef, BinaryBuilder, BooleanBuilder, FixedSizeListBuilder, Float32Builder, Float64Builder,
    Int32Builder, Int64Builder, LargeBinaryBuilder, ListBuilder, StringBuilder,
    TimestampMicrosecondBuilder,
};
use arrow::datatypes::{DataType, Field, Schema, SchemaRef, TimeUnit};
use arrow::record_batch::RecordBatch;
use arrow_ipc::writer::StreamWriter;
use arrow_json::ArrayWriter;
use async_trait::async_trait;
use chrono::Duration as ChronoDuration;
use datafusion::catalog::Session;
use datafusion::common::DataFusionError;
use datafusion::datasource::{MemTable, TableProvider, TableType};
use datafusion::execution::context::SessionConfig;
use datafusion::execution::session_state::SessionStateBuilder;
use datafusion::logical_expr::TableProviderFilterPushDown;
use datafusion::physical_plan::ExecutionPlan;
use datafusion::prelude::*;
use futures::TryStreamExt;
use lance::Dataset;
use lance::dataset::builder::DatasetBuilder;
use lance::dataset::optimize::{CompactionMetrics, CompactionOptions, compact_files};
use lance::dataset::{ColumnAlteration, NewColumnTransform, ReadParams, UpdateBuilder};
use lance::index::vector::VectorIndexParams;
use lance::io::{ObjectStoreParams, WrappingObjectStore};
use lance_index::optimize::OptimizeOptions;
use lance_index::scalar::{InvertedIndexParams, ScalarIndexParams, ScalarIndexType};
use lance_index::vector::hnsw::builder::HnswBuildParams;
use lance_index::vector::ivf::IvfBuildParams;
use lance_index::vector::pq::PQBuildParams;
use lance_index::vector::sq::builder::SQBuildParams;
use lance_index::{DatasetIndexExt, IndexParams, IndexType};
use lance_linalg::distance::MetricType;
use lance_table::format::Index as LanceIndexMetadata;
use object_store::ObjectStore;
use object_store::aws::AmazonS3Builder;
use ocra::{ReadThroughCache, memory::InMemoryCache};
use serde::{Deserialize, Serialize};
use serde_json::{Map, Value};
use tokio::time::{Duration, sleep};

use crate::config::{ReadThroughCacheConfig, S3Config, StorageConfig};

struct LanceTable {
    dataset: Arc<Dataset>,
    schema: SchemaRef,
}

#[derive(Debug, Deserialize)]
struct PersistedCompatTable {
    schema: PersistedCompatSchema,
    rows: Vec<Map<String, Value>>,
}

#[derive(Debug, Deserialize)]
struct PersistedCompatSchema {
    fields: Vec<PersistedCompatField>,
}

#[derive(Debug, Deserialize)]
struct PersistedCompatField {
    name: String,
    #[serde(rename = "type")]
    dtype: String,
    nullable: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct RegisteredTableEntry {
    name: String,
    location: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct RegisteredNamespaceEntry {
    name: String,
    properties: BTreeMap<String, String>,
}

impl LanceTable {
    fn new(dataset: Arc<Dataset>) -> Self {
        let schema = Arc::new(dataset.schema().into());
        Self { dataset, schema }
    }
}

#[async_trait]
impl TableProvider for LanceTable {
    fn as_any(&self) -> &dyn Any {
        self
    }

    fn schema(&self) -> SchemaRef {
        self.schema.clone()
    }

    fn table_type(&self) -> TableType {
        TableType::Base
    }

    async fn scan(
        &self,
        _state: &dyn Session,
        projection: Option<&Vec<usize>>,
        _filters: &[Expr],
        limit: Option<usize>,
    ) -> datafusion::common::Result<Arc<dyn ExecutionPlan>> {
        let mut scan = self.dataset.scan();
        if let Some(projection) = projection {
            let columns: Vec<&str> = projection
                .iter()
                .map(|index| self.schema.field(*index).name().as_str())
                .collect();
            if !columns.is_empty() {
                scan.project(&columns)?;
            }
        }
        scan.limit(limit.map(|value| value as i64), None)?;
        scan.create_plan().await.map_err(DataFusionError::from)
    }

    fn supports_filters_pushdown(
        &self,
        filters: &[&Expr],
    ) -> datafusion::common::Result<Vec<TableProviderFilterPushDown>> {
        Ok(filters
            .iter()
            .map(|_| TableProviderFilterPushDown::Unsupported)
            .collect())
    }
}

#[derive(Debug, Deserialize)]
pub struct DataFrameQueryRequest {
    pub table: Option<String>,
    pub filter: Option<String>,
    pub limit: Option<usize>,
    pub offset: Option<usize>,
    pub order_by: Option<String>,
    pub sql: Option<String>,
}

#[derive(Debug, Serialize)]
pub struct DataFrameColumn {
    pub name: String,
    #[serde(rename = "type")]
    pub dtype: String,
}

#[derive(Debug, Serialize)]
pub struct DataFrameResponse {
    pub format: &'static str,
    pub table: String,
    pub limit: usize,
    pub row_count: usize,
    pub columns: Vec<DataFrameColumn>,
    pub rows: Vec<Map<String, Value>>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CreateTableMode {
    Create,
    Overwrite,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum NamespaceCreateMode {
    Create,
    ExistOk,
    Overwrite,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum NamespaceDropMode {
    Fail,
    Skip,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TableVersionInfo {
    pub version: i64,
}

#[derive(Debug)]
struct OcraStoreWrapper {
    cache_config: ReadThroughCacheConfig,
}

impl WrappingObjectStore for OcraStoreWrapper {
    fn wrap(
        &self,
        original: Arc<dyn object_store::ObjectStore>,
    ) -> Arc<dyn object_store::ObjectStore> {
        let cache = Arc::new(
            InMemoryCache::builder(self.cache_config.capacity_bytes)
                .page_size(self.cache_config.page_size_bytes)
                .build(),
        );
        Arc::new(ReadThroughCache::new(original, cache))
    }
}

pub struct TonboContext {
    session: SessionContext,
    storage: StorageConfig,
    known_tables: Arc<dashmap::DashSet<String>>,
    registered_tables: Arc<DashMap<String, String>>,
    namespaces: Arc<DashMap<String, BTreeMap<String, String>>>,
    dropped_indices: Arc<DashMap<String, BTreeSet<String>>>,
    // Per-table lock that serializes ensure_table_registered — eliminates TOCTOU race
    // that caused 10x parallel S3 opens and subsequent connection exhaustion.
    registration_locks: Arc<DashMap<String, Arc<tokio::sync::Mutex<()>>>>,
    // Cache of opened Lance datasets. Avoids re-opening from S3 on every read.
    // Invalidated by invalidate_table() on any write/delete.
    dataset_cache: Arc<DashMap<String, Arc<Dataset>>>,
    // Per-table buffered current state. Replaces the previous single global
    // Mutex<BTreeMap<>> which serialised all buffered-table operations regardless
    // of which table was being touched.
    buffered_table_states:
        Arc<DashMap<String, Arc<tokio::sync::Mutex<BufferedCurrentTableState>>>>,
    // Per-table load barrier: only one task loads a buffered table from storage
    // at a time. Others wait on the mutex instead of spin-sleeping 25 ms.
    buffered_load_barriers: Arc<DashMap<String, Arc<tokio::sync::Mutex<()>>>>,
    // Admission control for Lance S3/local write operations (merge_insert, delete,
    // append). Limits concurrent writes so Tokio workers remain available for
    // reads and health probes. Value from env TONBO_MAX_CONCURRENT_WRITES (default 2).
    write_semaphore: Arc<tokio::sync::Semaphore>,
    // Weak self-reference set immediately after Arc construction. Allows methods
    // with &self signature to spawn async tasks that hold Arc<Self>.
    self_ref: std::sync::OnceLock<std::sync::Weak<TonboContext>>,
}

pub struct TableIndexInfo {
    pub name: String,
    pub dataset_version: i64,
    pub fields: Vec<String>,
}

pub struct OptimizeTableResult {
    pub version: i64,
    pub metrics: CompactionMetrics,
}

pub struct CleanupTableResult {
    pub bytes_removed: u64,
    pub old_versions: u64,
}

pub struct TableVersionDetail {
    pub version: i64,
    pub manifest_path: String,
    pub transaction_file: Option<String>,
    pub schema_fields: usize,
    pub config: Map<String, Value>,
}

pub struct TableStats {
    pub version: i64,
    pub row_count: usize,
    pub index_count: usize,
    pub field_count: usize,
}

struct BufferedCurrentTableState {
    loaded: bool,
    loading: bool,
    version: u64,
    dirty_count: usize,
    last_flush_at: Option<Instant>,
    rows: BTreeMap<String, Map<String, Value>>,
    pending_events: Vec<Map<String, Value>>,
    /// Mutex held during a flush to prevent concurrent flushes of the same table.
    /// If another flush is already in progress, try_lock() fails and the caller
    /// returns immediately — the in-progress flush will cover the new rows.
    flush_lock: Arc<tokio::sync::Mutex<()>>,
}

impl Default for BufferedCurrentTableState {
    fn default() -> Self {
        Self {
            loaded: false,
            loading: false,
            version: 0,
            dirty_count: 0,
            last_flush_at: None,
            rows: BTreeMap::new(),
            pending_events: Vec::new(),
            flush_lock: Arc::new(tokio::sync::Mutex::new(())),
        }
    }
}

impl TonboContext {
    pub async fn open(
        storage: StorageConfig,
    ) -> Result<Arc<Self>, Box<dyn std::error::Error + Send + Sync>> {
        let session =
            SessionContext::new_with_config(SessionConfig::new().with_information_schema(true));
        let ctx = Arc::new(Self {
            session,
            storage,
            known_tables: Arc::new(dashmap::DashSet::new()),
            registered_tables: Arc::new(DashMap::new()),
            namespaces: {
                let m = DashMap::new();
                m.insert("default".to_string(), BTreeMap::new());
                Arc::new(m)
            },
            dropped_indices: Arc::new(DashMap::new()),
            registration_locks: Arc::new(DashMap::new()),
            dataset_cache: Arc::new(DashMap::new()),
            buffered_table_states: Arc::new(DashMap::new()),
            buffered_load_barriers: Arc::new(DashMap::new()),
            write_semaphore: Arc::new(tokio::sync::Semaphore::new(
                std::env::var("TONBO_MAX_CONCURRENT_WRITES")
                    .ok()
                    .and_then(|v| v.parse::<usize>().ok())
                    .unwrap_or(2),
            )),
            self_ref: std::sync::OnceLock::new(),
        });
        // Store a weak back-reference so &self methods can spawn Arc-owned tasks.
        let _ = ctx.self_ref.set(Arc::downgrade(&ctx));
        ctx.register_all_tables().await?;
        ctx.reconcile_known_table_schemas().await?;
        Ok(ctx)
    }

    /// Upgrade the stored weak reference to Arc<Self>.
    /// Returns None only in tests that construct TonboContext without Arc.
    fn arc(&self) -> Option<Arc<Self>> {
        self.self_ref.get()?.upgrade()
    }

    /// Spawn a background flush for `table_name`. Falls back to inline flush
    /// when the weak self-reference is unavailable (e.g., in unit tests).
    fn spawn_flush_or_inline(
        &self,
        table_name: String,
        force: bool,
    ) -> Option<tokio::task::JoinHandle<()>> {
        let Some(ctx) = self.arc() else {
            return None;
        };
        Some(tokio::spawn(async move {
            if let Err(error) = ctx
                .maybe_flush_buffered_current_table(&table_name, force)
                .await
            {
                tracing::warn!(
                    table = table_name,
                    error = %error,
                    "tonbo: background flush failed"
                );
            }
        }))
    }

    /// Create a fresh SessionContext that shares the same catalog as the master
    /// session. Each read query gets its own context so concurrent queries never
    /// contend on a single RwLock<SessionState>. Table registrations performed
    /// via the master session are immediately visible here because both contexts
    /// hold an Arc to the same underlying MemoryCatalogProviderList.
    fn query_session(&self) -> SessionContext {
        // new_from_existing copies the catalog_list Arc (shared) and sets
        // create_default_catalog_and_schema=false (catalog already exists).
        let state = SessionStateBuilder::new_from_existing(self.session.state()).build();
        SessionContext::new_with_state(state)
    }

    async fn register_all_tables(&self) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        if !self.storage.direct_tables.is_empty() {
            return self.register_direct_tables().await;
        }
        if self.storage.lance_uri.starts_with("s3://") {
            if self.storage.eager_table_registration {
                self.register_s3_tables().await
            } else {
                self.load_registered_namespaces_async().await?;
                self.register_registry_tables().await?;
                Ok(())
            }
        } else {
            self.register_local_tables().await
        }
    }

    async fn register_direct_tables(&self) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        for table in &self.storage.direct_tables {
            if table.uri.starts_with("s3://") {
                self.register_s3_table(&table.name, &table.uri).await?;
            } else {
                self.register_local_table(&table.name, Path::new(&table.uri))
                    .await?;
            }
        }
        Ok(())
    }

    async fn register_s3_tables(&self) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let names = self.discover_s3_table_names().await?;
        self.remember_table_names(names);
        self.load_registered_namespaces_async().await?;
        self.register_registry_tables().await?;
        Ok(())
    }

    async fn discover_s3_table_names(
        &self,
    ) -> Result<Vec<String>, Box<dyn std::error::Error + Send + Sync>> {
        let s3 = self
            .storage
            .s3
            .as_ref()
            .ok_or("s3 config required for s3:// URI")?;

        let store = AmazonS3Builder::new()
            .with_endpoint(&s3.endpoint)
            .with_region(&s3.region)
            .with_access_key_id(&s3.access_key)
            .with_secret_access_key(&s3.secret_key)
            .with_bucket_name(&s3.bucket)
            .with_virtual_hosted_style_request(s3.virtual_hosted_style)
            .build()?;

        let prefix = self
            .storage
            .lance_uri
            .strip_prefix("s3://")
            .and_then(|value| value.split_once('/'))
            .map(|(_, rest)| rest.to_string())
            .unwrap_or_default();
        let normalized_prefix = if prefix.is_empty() || prefix.ends_with('/') {
            prefix
        } else {
            format!("{prefix}/")
        };

        let list_prefix = object_store::path::Path::from(normalized_prefix.as_str());
        let listing = store.list_with_delimiter(Some(&list_prefix)).await?;
        tracing::info!(
            prefix = normalized_prefix,
            common_prefixes = listing.common_prefixes.len(),
            objects = listing.objects.len(),
            "tonbo: discovered s3 listing"
        );

        let mut names = Vec::new();
        for common_prefix in &listing.common_prefixes {
            let common_prefix_value = common_prefix.to_string();
            let dir_name = common_prefix_value
                .trim_end_matches('/')
                .rsplit('/')
                .next()
                .unwrap_or("");
            if dir_name.is_empty() {
                continue;
            }

            let versions_path = object_store::path::Path::from(format!(
                "{}/_versions",
                common_prefix_value.trim_end_matches('/')
            ));
            let has_versions = store
                .list_with_delimiter(Some(&versions_path))
                .await
                .map(|result| !result.objects.is_empty() || !result.common_prefixes.is_empty())
                .unwrap_or(false);

            if has_versions {
                let table_name = dir_name.trim_end_matches(".lance");
                names.push(table_name.to_string());
            } else {
                tracing::warn!(
                    prefix = common_prefix_value,
                    "tonbo: skipping s3 prefix without lance _versions"
                );
            }
        }

        tracing::info!(tables = names.len(), "tonbo: discovered s3 table names");
        Ok(names)
    }

    async fn register_s3_table(
        &self,
        name: &str,
        uri: &str,
    ) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        if self.session.table_exist(name)? {
            self.remember_table_name(name);
            return Ok(());
        }
        // Reuse cached dataset when available — avoids re-opening S3 objects.
        // Cache is invalidated by invalidate_table() after any write/delete.
        let dataset = if let Some(cached) = self.dataset_cache.get(name) {
            cached.clone()
        } else {
            let params = self.build_s3_store_params(true)?;
            let ds = Arc::new(
                DatasetBuilder::from_uri(uri)
                    .with_read_params(ReadParams {
                        store_options: Some(params),
                        ..Default::default()
                    })
                    .load()
                    .await?,
            );
            self.dataset_cache.insert(name.to_string(), ds.clone());
            ds
        };
        let provider = LanceTable::new(dataset);
        self.session.register_table(name, Arc::new(provider))?;
        if !is_ephemeral_table_name(name) {
            self.remember_table_name(name);
            tracing::info!(table = name, "tonbo: registered s3 table");
        }
        Ok(())
    }

    async fn register_local_tables(&self) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let root = Path::new(&self.storage.lance_uri);
        if !root.exists() {
            return Ok(());
        }

        self.load_registered_namespaces()?;

        for entry in std::fs::read_dir(root)? {
            let entry = entry?;
            let entry_path = entry.path();
            if entry_path.is_dir() {
                let name = entry_path
                    .file_name()
                    .and_then(|name| name.to_str())
                    .unwrap_or("")
                    .to_string();
                let has_lance_marker = entry_path.join("_versions").exists()
                    || entry_path.extension().is_some_and(|value| value == "lance");
                if has_lance_marker {
                    let table_name = name.trim_end_matches(".lance").to_string();
                    if let Err(error) = self.register_local_table(&table_name, &entry_path).await {
                        tracing::warn!("tonbo: skip table {table_name}: {error}");
                    }
                }
            } else if entry_path
                .file_name()
                .and_then(|name| name.to_str())
                .is_some_and(|name| name.ends_with(".table.json"))
            {
                let table_name = entry_path
                    .file_name()
                    .and_then(|name| name.to_str())
                    .unwrap_or_default()
                    .trim_end_matches(".table.json")
                    .to_string();
                if let Err(error) = self.register_local_compat_table(&table_name, &entry_path) {
                    tracing::warn!("tonbo: skip compat table {table_name}: {error}");
                }
            }
        }

        self.register_registry_tables().await?;

        Ok(())
    }

    fn load_registered_namespaces(&self) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        for entry in self.read_registered_namespace_entries()? {
            self.namespaces.insert(entry.name, entry.properties);
        }
        Ok(())
    }

    async fn load_registered_namespaces_async(
        &self,
    ) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let entries = if self.storage.lance_uri.starts_with("s3://") {
            self.read_registered_namespace_entries_s3().await?
        } else {
            self.read_registered_namespace_entries()?
        };
        for entry in entries {
            self.namespaces.insert(entry.name, entry.properties);
        }
        Ok(())
    }

    async fn register_registry_tables(
        &self,
    ) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let entries = if self.storage.lance_uri.starts_with("s3://") {
            self.read_registered_table_entries_s3().await?
        } else {
            self.read_registered_table_entries()?
        };
        for entry in entries {
            self.registered_tables
                .insert(entry.name.clone(), entry.location.clone());
            if !self.storage.eager_table_registration {
                continue;
            }
            if entry.location.starts_with("s3://") {
                if let Err(error) = self.register_s3_table(&entry.name, &entry.location).await {
                    tracing::warn!("tonbo: skip registered s3 table {}: {}", entry.name, error);
                }
                continue;
            }

            let path = Path::new(&entry.location);
            if path.exists() {
                if path
                    .file_name()
                    .and_then(|name| name.to_str())
                    .is_some_and(|name| name.ends_with(".table.json"))
                {
                    if let Err(error) = self.register_local_compat_table(&entry.name, path) {
                        tracing::warn!(
                            "tonbo: skip registered compat table {}: {}",
                            entry.name,
                            error
                        );
                    }
                } else if let Err(error) = self.register_local_table(&entry.name, path).await {
                    tracing::warn!("tonbo: skip registered table {}: {}", entry.name, error);
                }
            }
        }
        Ok(())
    }

    async fn register_local_table(
        &self,
        name: &str,
        path: &Path,
    ) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let uri = path.to_string_lossy().to_string();
        let dataset = Arc::new(Dataset::open(&uri).await?);
        let provider = LanceTable::new(dataset);
        self.session.register_table(name, Arc::new(provider))?;
        if !is_ephemeral_table_name(name) {
            self.remember_table_name(name);
            tracing::info!(table = name, "tonbo: registered local table");
        }
        Ok(())
    }

    fn register_local_compat_table(
        &self,
        name: &str,
        path: &Path,
    ) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let raw = std::fs::read(path)?;
        let persisted: PersistedCompatTable = serde_json::from_slice(&raw)?;
        let schema = Arc::new(Schema::new(
            persisted
                .schema
                .fields
                .iter()
                .map(|field| {
                    Field::new(
                        &field.name,
                        decode_compat_data_type(&field.dtype),
                        field.nullable,
                    )
                })
                .collect::<Vec<_>>(),
        ));
        let batch = compat_rows_to_batch(schema.clone(), &persisted.rows)?;
        let provider = MemTable::try_new(schema, vec![vec![batch]])?;
        self.session.register_table(name, Arc::new(provider))?;
        if !is_ephemeral_table_name(name) {
            self.remember_table_name(name);
            tracing::info!(table = name, "tonbo: registered compat table");
        }
        Ok(())
    }

    /// Return a cached Arc<Dataset> for the named table.
    /// Opens from storage and caches on first access (idempotent).
    /// Used by the Cypher native engine to bypass DataFusion SQL.
    pub async fn get_lance_dataset(
        &self,
        name: &str,
    ) -> Result<Arc<Dataset>, Box<dyn std::error::Error + Send + Sync>> {
        if let Some(ds) = self.dataset_cache.get(name) {
            return Ok(ds.clone());
        }
        self.ensure_table_registered(name).await?;
        self.dataset_cache
            .get(name)
            .map(|r| r.clone())
            .ok_or_else(|| {
                format!("dataset '{name}' not found in cache after registration").into()
            })
    }

    pub async fn execute_sql(
        &self,
        sql: &str,
    ) -> Result<Vec<u8>, Box<dyn std::error::Error + Send + Sync>> {
        let batches = self.collect_sql(sql).await?;
        encode_ipc_stream(&batches)
    }

    pub async fn execute_query_request(
        &self,
        req: DataFrameQueryRequest,
    ) -> Result<Vec<u8>, Box<dyn std::error::Error + Send + Sync>> {
        let sql = dataframe_sql(&req)?;
        self.execute_sql(&sql).await
    }

    pub async fn execute_dataframe_query(
        &self,
        req: DataFrameQueryRequest,
    ) -> Result<DataFrameResponse, Box<dyn std::error::Error + Send + Sync>> {
        let sql = dataframe_sql(&req)?;
        let batches = self.collect_sql(&sql).await?;
        let table = req.table.unwrap_or_default();
        let limit = req.limit.unwrap_or(200);
        dataframe_from_batches(table, limit, &batches)
    }

    pub async fn invalidate_table(&self, name: &str) {
        if buffered_current_table_with_config(name, &self.storage.buffered_table_prefixes) {
            return;
        }
        let _ = self.session.deregister_table(name);
        self.dataset_cache.remove(name);
        self.remember_table_name(name);
    }

    pub async fn upsert_rows(
        &self,
        table_name: &str,
        key_column: &str,
        rows: Vec<Map<String, Value>>,
    ) -> Result<usize, Box<dyn std::error::Error + Send + Sync>> {
        self.upsert_rows_with_keys(table_name, vec![key_column.to_string()], rows)
            .await
    }

    pub async fn upsert_rows_with_keys(
        &self,
        table_name: &str,
        key_columns: Vec<String>,
        rows: Vec<Map<String, Value>>,
    ) -> Result<usize, Box<dyn std::error::Error + Send + Sync>> {
        if rows.is_empty() {
            return Ok(0);
        }

        let count = rows.len();
        let key_columns = normalize_key_columns(&rows, key_columns);
        if buffered_current_table_with_config(table_name, &self.storage.buffered_table_prefixes) {
            self.upsert_rows_buffered_current(table_name, &key_columns, rows)
                .await?;
            return Ok(count);
        }
        let _write_permit = self
            .write_semaphore
            .acquire()
            .await
            .map_err(|_| "write semaphore closed")?;
        if self.storage.lance_uri.starts_with("s3://") {
            self.upsert_rows_s3(table_name, &key_columns, rows).await?;
        } else {
            self.upsert_rows_local(table_name, &key_columns, rows)
                .await?;
        }
        self.invalidate_table(table_name).await;
        Ok(count)
    }

    async fn upsert_rows_s3(
        &self,
        table_name: &str,
        key_columns: &[String],
        rows: Vec<Map<String, Value>>,
    ) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let uri = format!(
            "{}/{}",
            self.storage.lance_uri.trim_end_matches('/'),
            table_name
        );
        let store_params = self.build_s3_store_params(false)?;
        let rows = normalize_rows_for_known_table(table_name, rows);

        let mut attempt = 0;
        loop {
            // Wrap in tokio::spawn to convert lance panics (e.g. B2 503 unwrap in
            // lance-0.20 commit.rs:101) into a JoinError rather than crashing the
            // HTTP server.  The spawned task is awaited immediately so behaviour is
            // otherwise identical.
            let ctx = self
                .arc()
                .ok_or("context dropped before write completed")?;
            let table_name_owned = table_name.to_string();
            let uri_owned = uri.to_string();
            let key_columns_owned = key_columns.to_vec();
            let rows_owned = rows.clone();
            let store_params_owned = store_params.clone();
            let result = tokio::spawn(async move {
                ctx.upsert_rows_s3_once(
                    &table_name_owned,
                    &uri_owned,
                    &key_columns_owned,
                    &rows_owned,
                    store_params_owned,
                )
                .await
            })
            .await;
            let result: Result<(), Box<dyn std::error::Error + Send + Sync>> = match result {
                Ok(inner) => inner,
                Err(join_err) => Err(format!("lance write panicked: {join_err}").into()),
            };
            match result {
                Ok(()) => return Ok(()),
                Err(error)
                    if error.downcast_ref::<lance::Error>().is_some_and(|error| {
                        is_retryable_lance_write_error(error) && attempt < 5
                    }) =>
                {
                    attempt += 1;
                    let delay_ms = 250_u64 * (1_u64 << (attempt - 1));
                    let reason = error
                        .downcast_ref::<lance::Error>()
                        .map(retryable_lance_error_reason)
                        .unwrap_or("unknown");
                    tracing::warn!(
                        table = table_name,
                        attempt,
                        delay_ms,
                        reason,
                        "tonbo: retrying lance write error"
                    );
                    sleep(Duration::from_millis(delay_ms)).await;
                }
                Err(error) if error.to_string().contains("lance write panicked") && attempt < 5 => {
                    attempt += 1;
                    let delay_ms = 250_u64 * (1_u64 << (attempt - 1));
                    tracing::warn!(
                        table = table_name,
                        attempt,
                        delay_ms,
                        reason = "panic",
                        "tonbo: retrying lance write error"
                    );
                    sleep(Duration::from_millis(delay_ms)).await;
                }
                Err(error) => return Err(error.into()),
            }
        }
    }

    async fn upsert_rows_s3_once(
        &self,
        table_name: &str,
        uri: &str,
        key_columns: &[String],
        rows: &[Map<String, Value>],
        store_params: ObjectStoreParams,
    ) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        match DatasetBuilder::from_uri(uri)
            .with_read_params(ReadParams {
                store_options: Some(store_params.clone()),
                ..Default::default()
            })
            .load()
            .await
        {
            Ok(dataset) => {
                let dataset_schema: SchemaRef = Arc::new(dataset.schema().into());
                let rows = normalize_rows_to_schema(rows, dataset_schema.as_ref());
                let batch = json_rows_to_batch(dataset_schema, &rows)?;
                if append_only_table(table_name) {
                    let params = lance::dataset::WriteParams {
                        store_params: Some(store_params),
                        ..Default::default()
                    };
                    let insert = lance::dataset::InsertBuilder::new(uri).with_params(&params);
                    insert.execute(vec![batch]).await?;
                    return Ok(());
                }
                let mut job = lance::dataset::MergeInsertBuilder::try_new(
                    Arc::new(dataset),
                    key_columns.to_vec(),
                )?;
                job.when_matched(lance::dataset::WhenMatched::UpdateAll);
                job.when_not_matched(lance::dataset::WhenNotMatched::InsertAll);
                let schema = batch.schema();
                let reader: Box<dyn arrow::record_batch::RecordBatchReader + Send> = Box::new(
                    arrow::record_batch::RecordBatchIterator::new(vec![Ok(batch)], schema),
                );
                job.try_build()?.execute_reader(reader).await?;
                Ok(())
            }
            Err(lance::Error::DatasetNotFound { .. }) | Err(lance::Error::NotFound { .. }) => {
                let schema = infer_schema_from_rows_for_table(table_name, rows);
                let batch = json_rows_to_batch(Arc::new(schema), rows)?;
                let params = lance::dataset::WriteParams {
                    store_params: Some(store_params),
                    ..Default::default()
                };
                let insert = lance::dataset::InsertBuilder::new(uri).with_params(&params);
                match insert.execute(vec![batch]).await {
                    Ok(_) => Ok(()),
                    Err(error) if is_dataset_already_exists(&error) => {
                        tracing::warn!(
                            table = table_name,
                            error = %error,
                            "tonbo: dataset create raced with existing dataset, retrying upsert"
                        );
                        let retry_params = self.build_s3_store_params(false)?;
                        Box::pin(self.upsert_rows_s3_once(
                            table_name,
                            uri,
                            key_columns,
                            rows,
                            retry_params,
                        ))
                        .await
                    }
                    Err(error) => Err(error.into()),
                }
            }
            Err(error) => Err(error.into()),
        }
    }

    async fn upsert_rows_local(
        &self,
        table_name: &str,
        key_columns: &[String],
        rows: Vec<Map<String, Value>>,
    ) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let uri = format!(
            "{}/{}",
            self.storage.lance_uri.trim_end_matches('/'),
            table_name
        );
        let rows = normalize_rows_for_known_table(table_name, rows);
        let path = Path::new(&uri);

        if path.exists() {
            let dataset = Dataset::open(&uri).await?;
            let dataset_schema: SchemaRef = Arc::new(dataset.schema().into());
            let rows = normalize_rows_to_schema(&rows, dataset_schema.as_ref());
            let batch = json_rows_to_batch(dataset_schema, &rows)?;
            if append_only_table(table_name) {
                let insert = lance::dataset::InsertBuilder::new(&*uri);
                insert.execute(vec![batch]).await?;
                return Ok(());
            }
            let mut job = lance::dataset::MergeInsertBuilder::try_new(
                Arc::new(dataset),
                key_columns.to_vec(),
            )?;
            job.when_matched(lance::dataset::WhenMatched::UpdateAll);
            job.when_not_matched(lance::dataset::WhenNotMatched::InsertAll);
            let schema = batch.schema();
            let reader: Box<dyn arrow::record_batch::RecordBatchReader + Send> = Box::new(
                arrow::record_batch::RecordBatchIterator::new(vec![Ok(batch)], schema),
            );
            job.try_build()?.execute_reader(reader).await?;
        } else {
            let schema = infer_schema_from_rows_for_table(table_name, &rows);
            let batch = json_rows_to_batch(Arc::new(schema), &rows)?;
            let insert = lance::dataset::InsertBuilder::new(&*uri);
            insert.execute(vec![batch]).await?;
        }

        Ok(())
    }

    pub async fn delete_rows(
        &self,
        table_name: &str,
        filter: &str,
    ) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        if buffered_current_table_with_config(table_name, &self.storage.buffered_table_prefixes) {
            self.maybe_flush_buffered_current_table(table_name, true)
                .await?;
            self.delete_rows_from_storage(table_name, filter).await?;
            {
                self.buffered_table_states.remove(table_name);
                self.buffered_load_barriers.remove(table_name);
            }
            self.ensure_buffered_table_loaded(table_name).await?;
            return Ok(());
        }
        self.delete_rows_from_storage(table_name, filter).await?;
        self.invalidate_table(table_name).await;
        Ok(())
    }

    async fn delete_rows_from_storage(
        &self,
        table_name: &str,
        filter: &str,
    ) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let _write_permit = self
            .write_semaphore
            .acquire()
            .await
            .map_err(|_| "write semaphore closed")?;
        let uri = format!(
            "{}/{}",
            self.storage.lance_uri.trim_end_matches('/'),
            table_name
        );
        if self.storage.lance_uri.starts_with("s3://") {
            let params = self.build_s3_store_params(false)?;
            let mut dataset = DatasetBuilder::from_uri(&uri)
                .with_read_params(ReadParams {
                    store_options: Some(params),
                    ..Default::default()
                })
                .load()
                .await?;
            dataset.delete(filter).await?;
        } else {
            let mut dataset = Dataset::open(&uri).await?;
            dataset.delete(filter).await?;
        }
        Ok(())
    }

    pub fn table_names(&self) -> Vec<String> {
        let mut names: BTreeSet<String> = self
            .known_tables
            .iter()
            .map(|r| r.key().clone())
            .collect();
        if let Some(catalog) = self.session.catalog("datafusion") {
            if let Some(schema) = catalog.schema("public") {
                names.extend(schema.table_names());
            }
        }
        names.extend(self.registered_tables.iter().map(|e| e.key().clone()));
        names.into_iter().collect()
    }

    pub async fn count_rows(
        &self,
        table: &str,
        filter: Option<&str>,
    ) -> Result<usize, Box<dyn std::error::Error + Send + Sync>> {
        let mut sql = format!("SELECT COUNT(*) AS count FROM \"{}\"", table);
        if let Some(filter) = filter {
            if !filter.trim().is_empty() {
                sql.push_str(" WHERE ");
                sql.push_str(filter);
            }
        }
        let batches = self.collect_sql(&sql).await?;
        let rows = rows_from_batches(&batches)?;
        Ok(rows
            .first()
            .and_then(|row| row.get("count"))
            .and_then(|value| value.as_u64())
            .unwrap_or_default() as usize)
    }

    pub async fn describe_table_schema(
        &self,
        table_name: &str,
    ) -> Result<SchemaRef, Box<dyn std::error::Error + Send + Sync>> {
        self.ensure_table_registered(table_name).await?;
        if let Some(catalog) = self.session.catalog("datafusion") {
            if let Some(schema) = catalog.schema("public") {
                if let Some(provider) = schema.table(table_name).await? {
                    return Ok(provider.schema());
                }
            }
        }
        let sql = format!("SELECT * FROM \"{}\" LIMIT 1", table_name.trim());
        let batches = self.collect_sql(&sql).await?;
        Ok(batches
            .first()
            .map(|batch| batch.schema())
            .unwrap_or_else(|| Arc::new(Schema::empty())))
    }

    pub async fn create_table(
        &self,
        table_name: &str,
        schema: SchemaRef,
        rows: Vec<Map<String, Value>>,
        mode: CreateTableMode,
    ) -> Result<usize, Box<dyn std::error::Error + Send + Sync>> {
        let table_name = table_name.trim();
        if table_name.is_empty() {
            return Err("table is required".into());
        }

        match mode {
            CreateTableMode::Create if self.table_exists(table_name)? => {
                return Err(format!("table already exists: {table_name}").into());
            }
            CreateTableMode::Overwrite => {}
            CreateTableMode::Create => {}
        }

        self.write_table_rows(table_name, schema, rows.clone(), true)
            .await?;
        Ok(rows.len())
    }

    pub async fn create_empty_table(
        &self,
        table_name: &str,
        schema: SchemaRef,
        mode: CreateTableMode,
    ) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        self.create_table(table_name, schema, Vec::new(), mode)
            .await?;
        Ok(())
    }

    pub async fn create_table_from_json(
        &self,
        table_name: &str,
        rows: Vec<Map<String, Value>>,
        mode: CreateTableMode,
    ) -> Result<usize, Box<dyn std::error::Error + Send + Sync>> {
        let schema = Arc::new(infer_schema_from_rows_for_table(table_name, &rows));
        self.create_table(table_name, schema, rows, mode).await
    }

    pub async fn insert_rows(
        &self,
        table_name: &str,
        rows: Vec<Map<String, Value>>,
    ) -> Result<usize, Box<dyn std::error::Error + Send + Sync>> {
        let table_name = table_name.trim();
        if table_name.is_empty() {
            return Err("table is required".into());
        }
        if rows.is_empty() {
            return Ok(0);
        }
        let count = rows.len();
        self.append_rows_to_storage(table_name, rows).await?;
        self.invalidate_table(table_name).await;
        Ok(count)
    }

    pub async fn drop_table(
        &self,
        table_name: &str,
    ) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let table_name = table_name.trim();
        if table_name.is_empty() {
            return Err("table is required".into());
        }
        if self.storage.lance_uri.starts_with("s3://") {
            return Err("drop table is not implemented for s3 storage".into());
        }

        let root = Path::new(&self.storage.lance_uri);
        let mut removed = false;
        for path in local_table_path_candidates(root, table_name) {
            if !path.exists() {
                continue;
            }
            if path.is_dir() {
                std::fs::remove_dir_all(&path)?;
            } else {
                std::fs::remove_file(&path)?;
            }
            removed = true;
        }
        let _ = self.session.deregister_table(table_name);
        self.forget_table_name(table_name);
        if !removed {
            return Err(format!("table not found: {table_name}").into());
        }
        Ok(())
    }

    pub async fn table_location(
        &self,
        table_name: &str,
    ) -> Result<String, Box<dyn std::error::Error + Send + Sync>> {
        let table_name = table_name.trim();
        if table_name.is_empty() {
            return Err("table is required".into());
        }
        if self.storage.lance_uri.starts_with("s3://") {
            if let Some(location) = self
                .registered_tables
                .get(table_name)
                .map(|r| r.value().clone())
            {
                return Ok(location);
            }
            for candidate in s3_table_uri_candidates(&self.storage.lance_uri, table_name) {
                let uri = candidate.clone();
                if DatasetBuilder::from_uri(&candidate)
                    .with_read_params(ReadParams {
                        store_options: Some(self.build_s3_store_params(true)?),
                        ..Default::default()
                    })
                    .load()
                    .await
                    .is_ok()
                {
                    return Ok(uri);
                }
            }
            return Err(format!("table not found: {table_name}").into());
        }

        let root = Path::new(&self.storage.lance_uri);
        let registered_location = self
            .registered_tables
            .get(table_name)
            .map(|r| r.value().clone());
        if let Some(location) = registered_location {
            return Ok(location);
        }
        for path in local_table_path_candidates(root, table_name) {
            if path.exists() {
                return Ok(path.to_string_lossy().to_string());
            }
        }
        Err(format!("table not found: {table_name}").into())
    }

    pub async fn register_table(
        &self,
        table_name: &str,
        location: &str,
        mode: CreateTableMode,
    ) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let table_name = table_name.trim();
        let location = location.trim();
        if table_name.is_empty() || location.is_empty() {
            return Err("table and location are required".into());
        }
        if matches!(mode, CreateTableMode::Create) && self.table_location(table_name).await.is_ok()
        {
            return Err(format!("table already exists: {table_name}").into());
        }
        if location.starts_with("s3://") {
            let _ = self.open_dataset_at(location, true).await?;
            self.persist_registered_table_entry_s3(table_name, location)
                .await?;
            let _ = self.session.deregister_table(table_name);
            self.register_s3_table(table_name, location).await?;
            return Ok(());
        }
        let path = Path::new(location);
        if !path.exists() {
            return Err(format!("location not found: {location}").into());
        }
        if self.storage.lance_uri.starts_with("s3://") {
            return Err(
                "register table is not implemented for non-s3 locations on s3-backed registry"
                    .into(),
            );
        }
        self.persist_registered_table_entry(table_name, location)?;
        let _ = self.session.deregister_table(table_name);
        if path
            .file_name()
            .and_then(|name| name.to_str())
            .is_some_and(|name| name.ends_with(".table.json"))
        {
            self.register_local_compat_table(table_name, path)?;
        } else {
            self.register_local_table(table_name, path).await?;
        }
        Ok(())
    }

    pub async fn deregister_table(
        &self,
        table_name: &str,
    ) -> Result<String, Box<dyn std::error::Error + Send + Sync>> {
        let table_name = table_name.trim();
        if table_name.is_empty() {
            return Err("table is required".into());
        }
        let location = if self.storage.lance_uri.starts_with("s3://") {
            self.remove_registered_table_entry_s3(table_name).await?
        } else {
            self.remove_registered_table_entry(table_name)?
        };
        let _ = self.session.deregister_table(table_name);
        self.forget_table_name(table_name);
        Ok(location)
    }

    pub async fn rename_table(
        &self,
        table_name: &str,
        new_table_name: &str,
    ) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let table_name = table_name.trim();
        let new_table_name = new_table_name.trim();
        if table_name.is_empty() || new_table_name.is_empty() {
            return Err("table names are required".into());
        }
        if self.table_location(new_table_name).await.is_ok() {
            return Err(format!("table already exists: {new_table_name}").into());
        }
        let registered_location = self
            .registered_tables
            .get(table_name)
            .map(|r| r.value().clone());
        if let Some(location) = registered_location {
            if self.storage.lance_uri.starts_with("s3://") {
                self.rename_registered_table_entry_s3(table_name, new_table_name, &location)
                    .await?;
            } else {
                self.rename_registered_table_entry(table_name, new_table_name, &location)?;
            }
            let _ = self.session.deregister_table(table_name);
            self.forget_table_name(table_name);
            if location.starts_with("s3://") {
                self.register_s3_table(new_table_name, &location).await?;
            } else {
                let path = Path::new(&location);
                if path
                    .file_name()
                    .and_then(|name| name.to_str())
                    .is_some_and(|name| name.ends_with(".table.json"))
                {
                    self.register_local_compat_table(new_table_name, path)?;
                } else {
                    self.register_local_table(new_table_name, path).await?;
                }
            }
            return Ok(());
        }
        if self.storage.lance_uri.starts_with("s3://") {
            let source_uri = self.table_location(table_name).await?;
            let target_uri = renamed_s3_table_uri(&source_uri, new_table_name)?;
            self.rename_s3_table_objects(&source_uri, &target_uri)
                .await?;
            let _ = self.session.deregister_table(table_name);
            self.forget_table_name(table_name);
            self.register_s3_table(new_table_name, &target_uri).await?;
            return Ok(());
        }

        let root = Path::new(&self.storage.lance_uri);
        let source = local_table_path_candidates(root, table_name)
            .into_iter()
            .find(|path| path.exists())
            .ok_or_else(|| format!("table not found: {table_name}"))?;
        let target = if source
            .file_name()
            .and_then(|name| name.to_str())
            .is_some_and(|name| name.ends_with(".table.json"))
        {
            root.join(format!("{new_table_name}.table.json"))
        } else if source
            .extension()
            .is_some_and(|extension| extension == "lance")
        {
            root.join(format!("{new_table_name}.lance"))
        } else {
            root.join(new_table_name)
        };

        std::fs::rename(&source, &target)?;
        let _ = self.session.deregister_table(table_name);
        self.forget_table_name(table_name);
        self.invalidate_table(new_table_name).await;
        Ok(())
    }

    pub async fn list_table_versions(
        &self,
        table_name: &str,
        descending: bool,
    ) -> Result<Vec<TableVersionInfo>, Box<dyn std::error::Error + Send + Sync>> {
        let table_name = table_name.trim();
        if table_name.is_empty() {
            return Err("table is required".into());
        }
        let location = self.table_location(table_name).await?;
        let dataset = self.open_dataset_at(&location, true).await?;
        let mut versions = dataset
            .versions()
            .await?
            .into_iter()
            .map(|version| TableVersionInfo {
                version: version.version as i64,
            })
            .collect::<Vec<_>>();
        if descending {
            versions.sort_by(|left, right| right.version.cmp(&left.version));
        } else {
            versions.sort_by(|left, right| left.version.cmp(&right.version));
        }
        if versions.is_empty() {
            versions.push(TableVersionInfo { version: 0 });
        }
        Ok(versions)
    }

    pub async fn restore_table_version(
        &self,
        table_name: &str,
        version: i64,
    ) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let table_name = table_name.trim();
        if table_name.is_empty() {
            return Err("table is required".into());
        }
        if version < 0 {
            return Err("version must be non-negative".into());
        }
        let location = self.table_location(table_name).await?;
        let dataset = self.open_dataset_at(&location, true).await?;
        let checked_out = dataset.checkout_version(version as u64).await?;
        let temp = ephemeral_table_name(table_name);
        self.session
            .register_table(&temp, Arc::new(LanceTable::new(Arc::new(checked_out))))?;
        let rows = self.collect_registered_table_rows(&temp).await?;
        let _ = self.session.deregister_table(&temp);
        self.forget_table_name(&temp);
        let schema = infer_schema_from_rows_for_table(table_name, &rows);
        self.write_table_rows(table_name, Arc::new(schema), rows, true)
            .await?;
        Ok(())
    }

    pub async fn create_table_version(
        &self,
        table_name: &str,
        version: Option<i64>,
        put_if_not_exists: bool,
        metadata: Option<BTreeMap<String, String>>,
    ) -> Result<i64, Box<dyn std::error::Error + Send + Sync>> {
        let table_name = table_name.trim();
        if table_name.is_empty() {
            return Err("table is required".into());
        }
        let location = self.table_location(table_name).await?;
        let dataset = self.open_dataset_at(&location, false).await?;
        if let Some(requested_version) = version {
            let exists = dataset
                .versions()
                .await?
                .into_iter()
                .any(|entry| entry.version as i64 == requested_version);
            if exists {
                if put_if_not_exists {
                    return Ok(requested_version);
                }
                return Err(format!("version already exists: {requested_version}").into());
            }
        }

        let upsert_values = metadata
            .unwrap_or_default()
            .into_iter()
            .collect::<HashMap<_, _>>();
        let mut dataset = dataset;
        dataset.update_config(upsert_values).await?;
        Ok(dataset.version().version as i64)
    }

    pub async fn describe_table_version(
        &self,
        table_name: &str,
        version: i64,
    ) -> Result<TableVersionDetail, Box<dyn std::error::Error + Send + Sync>> {
        let table_name = table_name.trim();
        if table_name.is_empty() {
            return Err("table is required".into());
        }
        if version < 0 {
            return Err("version must be non-negative".into());
        }
        let location = self.table_location(table_name).await?;
        let dataset = self.open_dataset_at(&location, true).await?;
        let checked_out = dataset.checkout_version(version as u64).await?;
        let manifest = checked_out.manifest();
        let mut config = Map::new();
        for (key, value) in &manifest.config {
            config.insert(key.clone(), Value::String(value.clone()));
        }
        Ok(TableVersionDetail {
            version,
            manifest_path: version_manifest_path(&location, version),
            transaction_file: manifest.transaction_file.clone(),
            schema_fields: manifest.schema.fields.len(),
            config,
        })
    }

    pub async fn delete_table_versions(
        &self,
        table_name: &str,
        start_version: i64,
        end_version: i64,
    ) -> Result<usize, Box<dyn std::error::Error + Send + Sync>> {
        let table_name = table_name.trim();
        if table_name.is_empty() {
            return Err("table is required".into());
        }
        let location = self.table_location(table_name).await?;
        if location.starts_with("s3://") {
            return Err("delete version records is not implemented for s3-backed tables".into());
        }
        let versions = self.list_table_versions(table_name, false).await?;
        let selected = versions
            .into_iter()
            .filter(|entry| version_in_range(entry.version, start_version, end_version))
            .collect::<Vec<_>>();
        let mut deleted = 0usize;
        for entry in selected {
            let path = std::path::PathBuf::from(version_manifest_path(&location, entry.version));
            if path.exists() {
                std::fs::remove_file(&path)?;
                deleted += 1;
            }
        }
        Ok(deleted)
    }

    pub async fn add_table_columns(
        &self,
        table_name: &str,
        columns: Vec<(String, String)>,
    ) -> Result<i64, Box<dyn std::error::Error + Send + Sync>> {
        if columns.is_empty() {
            return Err("columns are required".into());
        }
        let location = self.table_location(table_name).await?;
        let mut dataset = self.open_dataset_at(&location, false).await?;
        dataset
            .add_columns(NewColumnTransform::SqlExpressions(columns), None, None)
            .await?;
        let version = dataset.version().version as i64;
        self.invalidate_table(table_name).await;
        Ok(version)
    }

    pub async fn alter_table_columns(
        &self,
        table_name: &str,
        alterations: Vec<ColumnAlteration>,
    ) -> Result<i64, Box<dyn std::error::Error + Send + Sync>> {
        if alterations.is_empty() {
            return Err("alterations are required".into());
        }
        let location = self.table_location(table_name).await?;
        let mut dataset = self.open_dataset_at(&location, false).await?;
        dataset.alter_columns(&alterations).await?;
        let version = dataset.version().version as i64;
        self.invalidate_table(table_name).await;
        Ok(version)
    }

    pub async fn drop_table_columns(
        &self,
        table_name: &str,
        columns: Vec<String>,
    ) -> Result<i64, Box<dyn std::error::Error + Send + Sync>> {
        if columns.is_empty() {
            return Err("columns are required".into());
        }
        let location = self.table_location(table_name).await?;
        let mut dataset = self.open_dataset_at(&location, false).await?;
        let refs = columns.iter().map(String::as_str).collect::<Vec<_>>();
        dataset.drop_columns(&refs).await?;
        let version = dataset.version().version as i64;
        self.invalidate_table(table_name).await;
        Ok(version)
    }

    pub async fn update_table(
        &self,
        table_name: &str,
        updates: BTreeMap<String, String>,
        predicate: Option<String>,
    ) -> Result<(i64, u64), Box<dyn std::error::Error + Send + Sync>> {
        if updates.is_empty() {
            return Err("updates are required".into());
        }
        let location = self.table_location(table_name).await?;
        let dataset = Arc::new(self.open_dataset_at(&location, false).await?);
        let mut builder = UpdateBuilder::new(dataset);
        if let Some(predicate) = predicate
            .as_deref()
            .map(str::trim)
            .filter(|value| !value.is_empty())
        {
            builder = builder.update_where(predicate)?;
        }
        for (column, expression) in updates {
            builder = builder.set(column, &expression)?;
        }
        let result = builder.build()?.execute().await?;
        self.invalidate_table(table_name).await;
        Ok((
            result.new_dataset.version().version as i64,
            result.rows_updated,
        ))
    }

    pub async fn create_scalar_index(
        &self,
        table_name: &str,
        column: &str,
        index_name: Option<String>,
        index_type: ScalarIndexType,
        replace: bool,
    ) -> Result<i64, Box<dyn std::error::Error + Send + Sync>> {
        let location = self.table_location(table_name).await?;
        let mut dataset = self.open_dataset_at(&location, false).await?;
        let created_index_name = index_name.clone();
        match index_type {
            ScalarIndexType::Inverted => {
                let params = InvertedIndexParams::default();
                dataset
                    .create_index(&[column], IndexType::Inverted, index_name, &params, replace)
                    .await?;
            }
            _ => {
                let params = ScalarIndexParams::new(index_type);
                dataset
                    .create_index(&[column], params.index_type(), index_name, &params, replace)
                    .await?;
            }
        }
        if let Some(name) = created_index_name.as_deref() {
            self.clear_dropped_index(table_name, name);
        }
        self.invalidate_table(table_name).await;
        Ok(dataset.version().version as i64)
    }

    pub async fn create_vector_index(
        &self,
        table_name: &str,
        column: &str,
        index_name: Option<String>,
        metric_type: MetricType,
        index_kind: &str,
        num_partitions: Option<usize>,
        num_sub_vectors: Option<usize>,
        hnsw_m: Option<usize>,
        hnsw_ef_construction: Option<usize>,
        replace: bool,
    ) -> Result<i64, Box<dyn std::error::Error + Send + Sync>> {
        let location = self.table_location(table_name).await?;
        let mut dataset = self.open_dataset_at(&location, false).await?;
        let created_index_name = index_name.clone();
        let params = match index_kind.trim().to_ascii_lowercase().as_str() {
            "vector" | "ivf_pq" => VectorIndexParams::ivf_pq(
                num_partitions.unwrap_or(8),
                8,
                num_sub_vectors.unwrap_or(8),
                metric_type,
                50,
            ),
            "ivf_flat" => VectorIndexParams::ivf_flat(num_partitions.unwrap_or(8), metric_type),
            "ivf_hnsw_sq" => {
                let ivf = IvfBuildParams::new(num_partitions.unwrap_or(8));
                let hnsw = HnswBuildParams::default()
                    .num_edges(hnsw_m.unwrap_or(20))
                    .ef_construction(hnsw_ef_construction.unwrap_or(150));
                let sq = SQBuildParams::default();
                VectorIndexParams::with_ivf_hnsw_sq_params(metric_type, ivf, hnsw, sq)
            }
            "ivf_hnsw_pq" => {
                let ivf = IvfBuildParams::new(num_partitions.unwrap_or(8));
                let hnsw = HnswBuildParams::default()
                    .num_edges(hnsw_m.unwrap_or(20))
                    .ef_construction(hnsw_ef_construction.unwrap_or(150));
                let pq = PQBuildParams::new(num_sub_vectors.unwrap_or(8), 8);
                VectorIndexParams::with_ivf_hnsw_pq_params(metric_type, ivf, hnsw, pq)
            }
            other => return Err(format!("unsupported vector index type: {other}").into()),
        };
        dataset
            .create_index(&[column], IndexType::Vector, index_name, &params, replace)
            .await?;
        if let Some(name) = created_index_name.as_deref() {
            self.clear_dropped_index(table_name, name);
        }
        self.invalidate_table(table_name).await;
        Ok(dataset.version().version as i64)
    }

    pub async fn list_table_indices(
        &self,
        table_name: &str,
    ) -> Result<Vec<TableIndexInfo>, Box<dyn std::error::Error + Send + Sync>> {
        let location = self.table_location(table_name).await?;
        let dataset = self.open_dataset_at(&location, false).await?;
        let schema = dataset.schema();
        let indices = dataset.load_indices().await?;
        let dropped = self.dropped_index_names(table_name);
        indices
            .iter()
            .filter(|index| !dropped.contains(&index.name))
            .map(|index| lance_index_to_table_index(index, &schema))
            .collect()
    }

    pub async fn table_index_stats(
        &self,
        table_name: &str,
        index_name: &str,
    ) -> Result<Value, Box<dyn std::error::Error + Send + Sync>> {
        if self.index_is_dropped(table_name, index_name) {
            return Err(format!("index does not exist: {index_name}").into());
        }
        let location = self.table_location(table_name).await?;
        let dataset = self.open_dataset_at(&location, false).await?;
        Ok(serde_json::from_str(
            &dataset.index_statistics(index_name).await?,
        )?)
    }

    pub async fn drop_table_index(
        &self,
        table_name: &str,
        index_name: &str,
    ) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let existing = self.list_table_indices(table_name).await?;
        if !existing.iter().any(|index| index.name == index_name) {
            return Err(format!("index does not exist: {index_name}").into());
        }
        self.dropped_indices
            .entry(table_name.trim().to_string())
            .or_default()
            .insert(index_name.trim().to_string());
        Ok(())
    }

    pub async fn table_stats(
        &self,
        table_name: &str,
    ) -> Result<TableStats, Box<dyn std::error::Error + Send + Sync>> {
        let location = self.table_location(table_name).await?;
        let dataset = self.open_dataset_at(&location, false).await?;
        let row_count = dataset.count_rows(None).await?;
        let index_count = dataset.load_indices().await?.len();
        Ok(TableStats {
            version: dataset.version().version as i64,
            row_count,
            index_count,
            field_count: dataset.schema().fields.len(),
        })
    }

    pub async fn explain_table_query(
        &self,
        sql: &str,
        analyze: bool,
    ) -> Result<String, Box<dyn std::error::Error + Send + Sync>> {
        let prefix = if analyze {
            "EXPLAIN ANALYZE "
        } else {
            "EXPLAIN "
        };
        let explain_sql = prefix.to_string() + sql;
        match self.session.sql(&explain_sql).await {
            Ok(dataframe) => {
                let batches = dataframe.collect().await?;
                let rows = rows_from_batches(&batches)?;
                let mut lines = Vec::new();
                for row in rows {
                    if let Some((_, Value::String(text))) = row.into_iter().next() {
                        lines.push(text);
                    }
                }
                if lines.is_empty() {
                    Ok(explain_sql)
                } else {
                    Ok(lines.join("\n"))
                }
            }
            Err(_) => Ok(explain_sql),
        }
    }

    pub async fn list_table_tags(
        &self,
        table_name: &str,
    ) -> Result<
        HashMap<String, lance::dataset::refs::TagContents>,
        Box<dyn std::error::Error + Send + Sync>,
    > {
        let location = self.table_location(table_name).await?;
        let dataset = self.open_dataset_at(&location, false).await?;
        Ok(dataset.tags.list().await?)
    }

    pub async fn get_table_tag(
        &self,
        table_name: &str,
        tag: &str,
    ) -> Result<lance::dataset::refs::TagContents, Box<dyn std::error::Error + Send + Sync>> {
        let tags = self.list_table_tags(table_name).await?;
        tags.get(tag)
            .copied()
            .ok_or_else(|| format!("tag does not exist: {tag}").into())
    }

    pub async fn create_table_tag(
        &self,
        table_name: &str,
        tag: &str,
        version: i64,
    ) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let location = self.table_location(table_name).await?;
        let mut dataset = self.open_dataset_at(&location, false).await?;
        dataset.tags.create(tag, version as u64).await?;
        Ok(())
    }

    pub async fn update_table_tag(
        &self,
        table_name: &str,
        tag: &str,
        version: i64,
    ) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let location = self.table_location(table_name).await?;
        let mut dataset = self.open_dataset_at(&location, false).await?;
        match dataset.tags.update(tag, version as u64).await {
            Ok(()) => Ok(()),
            Err(_) => {
                let _ = dataset.tags.delete(tag).await;
                dataset.tags.create(tag, version as u64).await?;
                Ok(())
            }
        }
    }

    pub async fn delete_table_tag(
        &self,
        table_name: &str,
        tag: &str,
    ) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let location = self.table_location(table_name).await?;
        let mut dataset = self.open_dataset_at(&location, false).await?;
        dataset.tags.delete(tag).await?;
        Ok(())
    }

    pub async fn declare_table(
        &self,
        table_name: &str,
    ) -> Result<String, Box<dyn std::error::Error + Send + Sync>> {
        let table_name = table_name.trim();
        if table_name.is_empty() {
            return Err("table is required".into());
        }
        if self.storage.lance_uri.starts_with("s3://") {
            return Err("declare table is not implemented for s3-backed registries".into());
        }
        let root = Path::new(&self.storage.lance_uri);
        let path = root.join(format!("{table_name}.table.json"));
        if !path.exists() {
            let payload = serde_json::json!({
                "schema": { "fields": [] },
                "rows": []
            });
            std::fs::write(&path, serde_json::to_vec_pretty(&payload)?)?;
        }
        self.register_local_compat_table(table_name, &path)?;
        Ok(path.to_string_lossy().to_string())
    }

    pub async fn optimize_table(
        &self,
        table_name: &str,
        compact: bool,
        optimize_indices_enabled: bool,
        num_indices_to_merge: Option<usize>,
    ) -> Result<OptimizeTableResult, Box<dyn std::error::Error + Send + Sync>> {
        let location = self.table_location(table_name).await?;
        let mut dataset = self.open_dataset_at(&location, false).await?;
        let metrics = if compact {
            compact_files(&mut dataset, CompactionOptions::default(), None).await?
        } else {
            CompactionMetrics::default()
        };
        if optimize_indices_enabled {
            dataset
                .optimize_indices(&OptimizeOptions {
                    num_indices_to_merge: num_indices_to_merge.unwrap_or(1),
                    index_names: None,
                })
                .await?;
        }
        self.invalidate_table(table_name).await;
        Ok(OptimizeTableResult {
            version: dataset.version().version as i64,
            metrics,
        })
    }

    pub async fn cleanup_old_versions(
        &self,
        table_name: &str,
        older_than_seconds: i64,
        delete_unverified: bool,
        error_if_tagged_old_versions: bool,
    ) -> Result<CleanupTableResult, Box<dyn std::error::Error + Send + Sync>> {
        if older_than_seconds < 0 {
            return Err("older_than_seconds must be non-negative".into());
        }
        let location = self.table_location(table_name).await?;
        let dataset = self.open_dataset_at(&location, false).await?;
        let stats = dataset
            .cleanup_old_versions(
                ChronoDuration::seconds(older_than_seconds),
                Some(delete_unverified),
                Some(error_if_tagged_old_versions),
            )
            .await?;
        Ok(CleanupTableResult {
            bytes_removed: stats.bytes_removed,
            old_versions: stats.old_versions,
        })
    }

    pub fn table_exists(
        &self,
        name: &str,
    ) -> Result<bool, Box<dyn std::error::Error + Send + Sync>> {
        Ok(self.session.table_exist(name)?)
    }

    pub async fn show_tables(
        &self,
    ) -> Result<Vec<RecordBatch>, Box<dyn std::error::Error + Send + Sync>> {
        let schema = Arc::new(Schema::new(vec![Field::new(
            "table_name",
            DataType::Utf8,
            false,
        )]));
        let mut builder = StringBuilder::new();
        for table in self.table_names() {
            builder.append_value(table);
        }
        let batch = RecordBatch::try_new(schema, vec![Arc::new(builder.finish())])?;
        Ok(vec![batch])
    }

    pub fn catalog_names(&self) -> Vec<String> {
        self.session.catalog_names()
    }

    pub async fn collect_sql_pub(
        &self,
        sql: &str,
    ) -> Result<Vec<RecordBatch>, Box<dyn std::error::Error + Send + Sync>> {
        self.collect_sql(sql).await
    }

    pub async fn execute_update_sql(
        &self,
        sql: &str,
    ) -> Result<i64, Box<dyn std::error::Error + Send + Sync>> {
        let sql = sql.trim();
        let upper = sql.to_uppercase();

        if upper.starts_with("CREATE TABLE") {
            return Ok(0);
        }
        if upper.starts_with("DELETE FROM") || upper.starts_with("DELETE ") {
            return self.execute_delete_sql(sql).await;
        }
        if upper.starts_with("INSERT INTO") || upper.starts_with("INSERT ") {
            return self.execute_insert_sql(sql).await;
        }

        Err(format!("unsupported update SQL: {}", &sql[..sql.len().min(80)]).into())
    }

    async fn collect_sql(
        &self,
        sql: &str,
    ) -> Result<Vec<RecordBatch>, Box<dyn std::error::Error + Send + Sync>> {
        match self.collect_sql_once(sql).await {
            Ok(batches) => Ok(batches),
            Err(error) => {
                let Some(table_name) = sql_table_name(sql) else {
                    return Err(error);
                };
                if !is_missing_known_column_error(error.as_ref()) {
                    return Err(error);
                }
                if !self.heal_known_table_schema(&table_name).await? {
                    return Err(error);
                }
                self.collect_sql_once(sql).await
            }
        }
    }

    async fn collect_sql_once(
        &self,
        sql: &str,
    ) -> Result<Vec<RecordBatch>, Box<dyn std::error::Error + Send + Sync>> {
        if let Some(table_name) = sql_table_name(sql) {
            self.ensure_table_registered(&table_name).await?;
        }
        let _guard = crate::metrics::ActiveQueryGuard::new();
        let start = std::time::Instant::now();
        let result = async {
            let dataframe = self.query_session().sql(sql).await?;
            dataframe.collect().await.map_err(|e| Box::new(e) as Box<dyn std::error::Error + Send + Sync>)
        }
        .await;
        let elapsed = start.elapsed().as_secs_f64();
        match &result {
            Ok(_) => crate::metrics::QUERY_DURATION.with_label_values(&["sql"]).observe(elapsed),
            Err(_) => crate::metrics::QUERY_ERRORS.with_label_values(&["sql"]).inc(),
        }
        result
    }

    async fn reconcile_known_table_schemas(
        &self,
    ) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        for table_name in self.table_names() {
            if !is_startup_reconcile_table(&table_name) {
                continue;
            }
            match self.known_table_schema_needs_reconcile(&table_name).await {
                Ok(false) => continue,
                Ok(true) => {}
                Err(error) if is_storage_not_found(error.as_ref()) => {
                    tracing::warn!(
                        table = table_name,
                        error = %error,
                        "tonbo: skip startup reconcile for missing table"
                    );
                    self.forget_table_name(&table_name);
                    continue;
                }
                Err(error) => return Err(error),
            }
            tracing::warn!(table = table_name, "tonbo: reconciling known table schema");
            let _ = self.heal_known_table_schema(&table_name).await?;
        }
        Ok(())
    }

    async fn known_table_schema_needs_reconcile(
        &self,
        table_name: &str,
    ) -> Result<bool, Box<dyn std::error::Error + Send + Sync>> {
        let Some(expected) = desired_table_schema(table_name) else {
            return Ok(false);
        };
        let probe_sql = format!("SELECT * FROM \"{}\" LIMIT 1", table_name);
        let batches = self.collect_sql_once(&probe_sql).await?;
        let Some(actual) = batches.first().map(|batch| batch.schema()) else {
            return Ok(false);
        };
        Ok(schema_missing_known_columns(
            actual.as_ref(),
            expected.as_ref(),
        ))
    }

    async fn execute_delete_sql(
        &self,
        sql: &str,
    ) -> Result<i64, Box<dyn std::error::Error + Send + Sync>> {
        let upper = sql.to_uppercase();
        let from_pos = upper.find("FROM").ok_or("DELETE missing FROM")?;
        let after_from = sql[from_pos + 4..].trim();

        let (table, filter) = if let Some(where_pos) = upper[from_pos..].find("WHERE") {
            let table = sql[from_pos + 4..from_pos + where_pos]
                .trim()
                .trim_matches('"');
            let filter = sql[from_pos + where_pos + 5..].trim();
            (table.to_string(), filter.to_string())
        } else {
            let table = after_from.trim_end_matches(';').trim().trim_matches('"');
            (table.to_string(), "true".to_string())
        };

        self.delete_rows(&table, &filter).await?;
        Ok(1)
    }

    async fn execute_insert_sql(
        &self,
        sql: &str,
    ) -> Result<i64, Box<dyn std::error::Error + Send + Sync>> {
        let upper = sql.to_uppercase();
        let into_pos = upper.find("INTO").ok_or("INSERT missing INTO")?;
        let after_into = sql[into_pos + 4..].trim();
        let table_end = after_into
            .find(|value: char| value == '(' || value.is_whitespace())
            .unwrap_or(after_into.len());
        let table = after_into[..table_end].trim().trim_matches('"').to_string();

        let cols_start = after_into.find('(').ok_or("INSERT missing column list")?;
        let cols_end = after_into
            .find(')')
            .ok_or("INSERT missing column list close")?;
        let columns: Vec<String> = after_into[cols_start + 1..cols_end]
            .split(',')
            .map(|value| {
                value
                    .trim()
                    .trim_matches('"')
                    .trim_matches('\'')
                    .to_string()
            })
            .collect();

        let values_pos = upper[into_pos..]
            .find("VALUES")
            .ok_or("INSERT missing VALUES")?;
        let values_str = &sql[into_pos + values_pos + 6..];

        let mut rows: Vec<Map<String, Value>> = Vec::new();
        let mut depth = 0;
        let mut current_group = String::new();
        for ch in values_str.chars() {
            match ch {
                '(' => {
                    depth += 1;
                    if depth == 1 {
                        current_group.clear();
                        continue;
                    }
                }
                ')' => {
                    depth -= 1;
                    if depth == 0 {
                        let values = parse_sql_values(&current_group);
                        let mut row = Map::new();
                        for (index, column) in columns.iter().enumerate() {
                            if let Some(value) = values.get(index) {
                                row.insert(column.clone(), sql_value_to_json(value));
                            }
                        }
                        rows.push(row);
                        continue;
                    }
                }
                _ => {}
            }
            if depth > 0 {
                current_group.push(ch);
            }
        }

        let count = rows.len() as i64;
        if !rows.is_empty() {
            let key_columns = infer_upsert_key_columns(&columns);
            self.upsert_rows_with_keys(&table, key_columns, rows)
                .await?;
        }
        Ok(count)
    }

    async fn heal_known_table_schema(
        &self,
        table_name: &str,
    ) -> Result<bool, Box<dyn std::error::Error + Send + Sync>> {
        if desired_table_schema(table_name).is_none() {
            return Ok(false);
        }
        let select_all = format!("SELECT * FROM \"{}\"", table_name);
        let batches = self.collect_sql_once(&select_all).await?;
        let rows = normalize_rows_for_known_table(table_name, rows_from_batches(&batches)?);
        if rows.is_empty() {
            return Ok(false);
        }
        self.overwrite_rows(table_name, rows).await?;
        tracing::warn!("tonbo: healed known table schema for {}", table_name);
        Ok(true)
    }

    async fn overwrite_rows(
        &self,
        table_name: &str,
        rows: Vec<Map<String, Value>>,
    ) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        if self.storage.lance_uri.starts_with("s3://") {
            self.overwrite_rows_s3(table_name, rows).await
        } else {
            self.overwrite_rows_local(table_name, rows).await
        }
    }

    async fn overwrite_rows_s3(
        &self,
        table_name: &str,
        rows: Vec<Map<String, Value>>,
    ) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let uri = format!(
            "{}/{}",
            self.storage.lance_uri.trim_end_matches('/'),
            table_name
        );
        let rows = normalize_rows_for_known_table(table_name, rows);
        let schema = infer_schema_from_rows_for_table(table_name, &rows);
        self.write_rows_to_uri(&uri, Arc::new(schema), rows, true, true)
            .await?;
        self.invalidate_table(table_name).await;
        Ok(())
    }

    pub fn list_namespaces(&self) -> Vec<String> {
        self.namespaces
            .iter()
            .map(|e| e.key().clone())
            .collect()
    }

    pub fn namespace_exists(&self, namespace: &str) -> bool {
        self.namespaces.contains_key(namespace.trim())
    }

    pub fn describe_namespace(
        &self,
        namespace: &str,
    ) -> Result<BTreeMap<String, String>, Box<dyn std::error::Error + Send + Sync>> {
        self.namespaces
            .get(namespace.trim())
            .map(|r| r.value().clone())
            .ok_or_else(|| format!("namespace not found: {}", namespace.trim()).into())
    }

    pub async fn create_namespace(
        &self,
        namespace: &str,
        mode: NamespaceCreateMode,
        properties: BTreeMap<String, String>,
    ) -> Result<BTreeMap<String, String>, Box<dyn std::error::Error + Send + Sync>> {
        let namespace = namespace.trim();
        if namespace.is_empty() {
            return Err("namespace is required".into());
        }
        let exists = self.namespace_exists(namespace);
        match mode {
            NamespaceCreateMode::Create if exists => {
                return Err(format!("namespace already exists: {namespace}").into());
            }
            NamespaceCreateMode::ExistOk if exists => {
                return self.describe_namespace(namespace);
            }
            NamespaceCreateMode::Overwrite if namespace == "default" => {
                return Err("default namespace cannot be overwritten".into());
            }
            NamespaceCreateMode::Overwrite if exists => {
                self.namespaces.insert(namespace.to_string(), properties.clone());
            }
            _ => {
                self.namespaces.insert(namespace.to_string(), properties.clone());
            }
        }
        if self.storage.lance_uri.starts_with("s3://") {
            self.persist_namespaces_s3().await?;
        } else {
            self.persist_namespaces()?;
        }
        Ok(properties)
    }

    pub async fn drop_namespace(
        &self,
        namespace: &str,
        mode: NamespaceDropMode,
    ) -> Result<Option<BTreeMap<String, String>>, Box<dyn std::error::Error + Send + Sync>> {
        let namespace = namespace.trim();
        if namespace.is_empty() {
            return Err("namespace is required".into());
        }
        if namespace == "default" {
            return Err("default namespace cannot be dropped".into());
        }
        let outcome = match (self.namespaces.remove(namespace), mode) {
            (Some((_, properties)), _) => Ok(Some(properties)),
            (None, NamespaceDropMode::Skip) => Ok(None),
            (None, NamespaceDropMode::Fail) => {
                Err(format!("namespace not found: {namespace}").into())
            }
        };
        if outcome.is_ok() {
            if self.storage.lance_uri.starts_with("s3://") {
                self.persist_namespaces_s3().await?;
            } else {
                self.persist_namespaces()?;
            }
        }
        outcome
    }

    async fn overwrite_rows_local(
        &self,
        table_name: &str,
        rows: Vec<Map<String, Value>>,
    ) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let uri = format!(
            "{}/{}",
            self.storage.lance_uri.trim_end_matches('/'),
            table_name
        );
        let rows = normalize_rows_for_known_table(table_name, rows);
        let schema = infer_schema_from_rows_for_table(table_name, &rows);
        self.write_rows_to_uri(&uri, Arc::new(schema), rows, false, true)
            .await?;
        self.invalidate_table(table_name).await;
        Ok(())
    }

    async fn write_table_rows(
        &self,
        table_name: &str,
        schema: SchemaRef,
        rows: Vec<Map<String, Value>>,
        overwrite: bool,
    ) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let uri = format!(
            "{}/{}",
            self.storage.lance_uri.trim_end_matches('/'),
            table_name.trim()
        );
        let rows = normalize_rows_for_known_table(table_name, rows);
        self.write_rows_to_uri(
            &uri,
            schema,
            rows,
            self.storage.lance_uri.starts_with("s3://"),
            overwrite,
        )
        .await?;
        self.invalidate_table(table_name).await;
        Ok(())
    }

    async fn write_rows_to_uri(
        &self,
        uri: &str,
        schema: SchemaRef,
        rows: Vec<Map<String, Value>>,
        is_s3: bool,
        overwrite: bool,
    ) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let batch = json_rows_to_batch(schema.clone(), &rows)?;
        if !is_s3 {
            let path = Path::new(uri);
            if overwrite && path.exists() {
                if path.is_dir() {
                    std::fs::remove_dir_all(path)?;
                } else {
                    std::fs::remove_file(path)?;
                }
            }
            if batch.num_rows() == 0 {
                let reader: Box<dyn arrow::record_batch::RecordBatchReader + Send> =
                    Box::new(arrow::record_batch::RecordBatchIterator::new(
                        Vec::<arrow::error::Result<RecordBatch>>::new().into_iter(),
                        schema,
                    ));
                let params = lance::dataset::WriteParams {
                    mode: lance::dataset::WriteMode::Create,
                    ..Default::default()
                };
                Dataset::write(reader, uri, Some(params)).await?;
                return Ok(());
            }
            let insert = lance::dataset::InsertBuilder::new(uri);
            insert.execute(vec![batch]).await?;
            return Ok(());
        }

        let reader: Box<dyn arrow::record_batch::RecordBatchReader + Send> =
            if batch.num_rows() == 0 {
                Box::new(arrow::record_batch::RecordBatchIterator::new(
                    Vec::<arrow::error::Result<RecordBatch>>::new().into_iter(),
                    schema,
                ))
            } else {
                let batch_schema = batch.schema();
                Box::new(arrow::record_batch::RecordBatchIterator::new(
                    vec![Ok(batch)].into_iter(),
                    batch_schema,
                ))
            };
        let mut params = lance::dataset::WriteParams {
            mode: if overwrite && (is_s3 || Path::new(uri).exists()) {
                lance::dataset::WriteMode::Overwrite
            } else {
                lance::dataset::WriteMode::Create
            },
            ..Default::default()
        };
        if is_s3 {
            params.store_params = Some(self.build_s3_store_params(true)?);
        }
        Dataset::write(reader, uri, Some(params)).await?;
        Ok(())
    }

    fn build_s3_store_params(
        &self,
        allow_cache_wrapper: bool,
    ) -> Result<ObjectStoreParams, Box<dyn std::error::Error + Send + Sync>> {
        let s3 = self.storage.s3.as_ref().ok_or("s3 config required")?;
        Ok(build_s3_store_params(s3, allow_cache_wrapper))
    }

    fn remember_table_name(&self, name: &str) {
        let trimmed = name.trim();
        if trimmed.is_empty() {
            return;
        }
        self.known_tables.insert(trimmed.to_string());
    }

    fn remember_table_names(&self, names: Vec<String>) {
        for name in names {
            let trimmed = name.trim();
            if !trimmed.is_empty() {
                self.known_tables.insert(trimmed.to_string());
            }
        }
    }

    fn forget_table_name(&self, name: &str) {
        self.known_tables.remove(name);
        self.dropped_indices.remove(name);
    }

    fn dropped_index_names(&self, table_name: &str) -> BTreeSet<String> {
        self.dropped_indices
            .get(table_name.trim())
            .map(|r| r.value().clone())
            .unwrap_or_default()
    }

    fn clear_dropped_index(&self, table_name: &str, index_name: &str) {
        if let Some(mut indices) = self.dropped_indices.get_mut(table_name.trim()) {
            indices.remove(index_name.trim());
        }
    }

    fn index_is_dropped(&self, table_name: &str, index_name: &str) -> bool {
        self.dropped_indices
            .get(table_name.trim())
            .is_some_and(|r| r.value().contains(index_name.trim()))
    }

    fn registry_file_path(&self) -> Option<std::path::PathBuf> {
        if self.storage.lance_uri.starts_with("s3://") {
            return None;
        }
        Some(Path::new(&self.storage.lance_uri).join(".tonbo-registered-tables.json"))
    }

    fn namespace_registry_file_path(&self) -> Option<std::path::PathBuf> {
        if self.storage.lance_uri.starts_with("s3://") {
            return None;
        }
        Some(Path::new(&self.storage.lance_uri).join(".tonbo-namespaces.json"))
    }

    fn s3_registry_object_path(&self, file_name: &str) -> Option<object_store::path::Path> {
        let suffix = self.storage.lance_uri.strip_prefix("s3://")?;
        let (_, prefix) = suffix.split_once('/')?;
        let normalized = prefix.trim_matches('/');
        let path = if normalized.is_empty() {
            file_name.to_string()
        } else {
            format!("{normalized}/{file_name}")
        };
        Some(object_store::path::Path::from(path))
    }

    fn build_s3_object_store(
        &self,
    ) -> Result<Arc<dyn ObjectStore>, Box<dyn std::error::Error + Send + Sync>> {
        let s3 = self.storage.s3.as_ref().ok_or("s3 config required")?;
        let store = AmazonS3Builder::new()
            .with_endpoint(&s3.endpoint)
            .with_region(&s3.region)
            .with_access_key_id(&s3.access_key)
            .with_secret_access_key(&s3.secret_key)
            .with_bucket_name(&s3.bucket)
            .with_virtual_hosted_style_request(s3.virtual_hosted_style)
            .build()?;
        Ok(Arc::new(store))
    }

    async fn rename_s3_table_objects(
        &self,
        source_uri: &str,
        target_uri: &str,
    ) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let configured_bucket = self
            .storage
            .s3
            .as_ref()
            .ok_or("s3 config required")?
            .bucket
            .clone();
        let (source_bucket, source_path) = s3_object_path_from_uri(source_uri)?;
        let (target_bucket, target_path) = s3_object_path_from_uri(target_uri)?;
        if source_bucket != configured_bucket || target_bucket != configured_bucket {
            return Err("rename is only supported within the configured s3 bucket".into());
        }
        let store = self.build_s3_object_store()?;
        rename_object_store_prefix(store, &source_path, &target_path).await
    }

    fn read_registered_table_entries(
        &self,
    ) -> Result<Vec<RegisteredTableEntry>, Box<dyn std::error::Error + Send + Sync>> {
        let Some(path) = self.registry_file_path() else {
            return Ok(Vec::new());
        };
        if !path.exists() {
            return Ok(Vec::new());
        }
        Ok(serde_json::from_slice(&std::fs::read(path)?)?)
    }

    async fn read_registered_table_entries_s3(
        &self,
    ) -> Result<Vec<RegisteredTableEntry>, Box<dyn std::error::Error + Send + Sync>> {
        let Some(path) = self.s3_registry_object_path(".tonbo-registered-tables.json") else {
            return Ok(Vec::new());
        };
        let store = self.build_s3_object_store()?;
        let bytes = match store.get(&path).await {
            Ok(result) => result.bytes().await?,
            Err(error) if is_storage_not_found(&error) => return Ok(Vec::new()),
            Err(error) => return Err(error.into()),
        };
        Ok(serde_json::from_slice(&bytes)?)
    }

    fn write_registered_table_entries(
        &self,
        entries: &[RegisteredTableEntry],
    ) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let Some(path) = self.registry_file_path() else {
            return Err("registry persistence is not supported for s3-backed storage".into());
        };
        if let Some(parent) = path.parent() {
            std::fs::create_dir_all(parent)?;
        }
        std::fs::write(path, serde_json::to_vec_pretty(entries)?)?;
        Ok(())
    }

    async fn write_registered_table_entries_s3(
        &self,
        entries: &[RegisteredTableEntry],
    ) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let Some(path) = self.s3_registry_object_path(".tonbo-registered-tables.json") else {
            return Err("registry path is unavailable".into());
        };
        let store = self.build_s3_object_store()?;
        if entries.is_empty() {
            let _ = store.delete(&path).await;
            return Ok(());
        }
        store
            .put(&path, serde_json::to_vec_pretty(entries)?.into())
            .await?;
        Ok(())
    }

    fn read_registered_namespace_entries(
        &self,
    ) -> Result<Vec<RegisteredNamespaceEntry>, Box<dyn std::error::Error + Send + Sync>> {
        let Some(path) = self.namespace_registry_file_path() else {
            return Ok(Vec::new());
        };
        if !path.exists() {
            return Ok(Vec::new());
        }
        Ok(serde_json::from_slice(&std::fs::read(path)?)?)
    }

    async fn read_registered_namespace_entries_s3(
        &self,
    ) -> Result<Vec<RegisteredNamespaceEntry>, Box<dyn std::error::Error + Send + Sync>> {
        let Some(path) = self.s3_registry_object_path(".tonbo-namespaces.json") else {
            return Ok(Vec::new());
        };
        let store = self.build_s3_object_store()?;
        let bytes = match store.get(&path).await {
            Ok(result) => result.bytes().await?,
            Err(error) if is_storage_not_found(&error) => return Ok(Vec::new()),
            Err(error) => return Err(error.into()),
        };
        Ok(serde_json::from_slice(&bytes)?)
    }

    fn persist_namespaces(&self) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let Some(path) = self.namespace_registry_file_path() else {
            return Err("namespace persistence is not supported for s3-backed storage".into());
        };
        if let Some(parent) = path.parent() {
            std::fs::create_dir_all(parent)?;
        }
        let entries = self
            .namespaces
            .iter()
            .filter(|e| e.key().as_str() != "default")
            .map(|e| RegisteredNamespaceEntry {
                name: e.key().clone(),
                properties: e.value().clone(),
            })
            .collect::<Vec<_>>();
        std::fs::write(path, serde_json::to_vec_pretty(&entries)?)?;
        Ok(())
    }

    async fn persist_namespaces_s3(&self) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let Some(path) = self.s3_registry_object_path(".tonbo-namespaces.json") else {
            return Err("namespace registry path is unavailable".into());
        };
        let store = self.build_s3_object_store()?;
        let entries = self
            .namespaces
            .iter()
            .filter(|e| e.key().as_str() != "default")
            .map(|e| RegisteredNamespaceEntry {
                name: e.key().clone(),
                properties: e.value().clone(),
            })
            .collect::<Vec<_>>();
        if entries.is_empty() {
            let _ = store.delete(&path).await;
            return Ok(());
        }
        store
            .put(&path, serde_json::to_vec_pretty(&entries)?.into())
            .await?;
        Ok(())
    }

    fn persist_registered_table_entry(
        &self,
        name: &str,
        location: &str,
    ) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let mut entries = self.read_registered_table_entries()?;
        entries.retain(|entry| entry.name != name);
        entries.push(RegisteredTableEntry {
            name: name.to_string(),
            location: location.to_string(),
        });
        self.write_registered_table_entries(&entries)?;
        self.registered_tables.insert(name.to_string(), location.to_string());
        Ok(())
    }

    async fn persist_registered_table_entry_s3(
        &self,
        name: &str,
        location: &str,
    ) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let mut entries = self.read_registered_table_entries_s3().await?;
        entries.retain(|entry| entry.name != name);
        entries.push(RegisteredTableEntry {
            name: name.to_string(),
            location: location.to_string(),
        });
        self.write_registered_table_entries_s3(&entries).await?;
        self.registered_tables.insert(name.to_string(), location.to_string());
        Ok(())
    }

    fn remove_registered_table_entry(
        &self,
        name: &str,
    ) -> Result<String, Box<dyn std::error::Error + Send + Sync>> {
        let mut entries = self.read_registered_table_entries()?;
        let location = entries
            .iter()
            .find(|entry| entry.name == name)
            .map(|entry| entry.location.clone())
            .ok_or_else(|| format!("registered table not found: {name}"))?;
        entries.retain(|entry| entry.name != name);
        self.write_registered_table_entries(&entries)?;
        self.registered_tables.remove(name);
        Ok(location)
    }

    fn rename_registered_table_entry(
        &self,
        name: &str,
        new_name: &str,
        location: &str,
    ) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let mut entries = self.read_registered_table_entries()?;
        let entry = entries
            .iter_mut()
            .find(|entry| entry.name == name)
            .ok_or_else(|| format!("registered table not found: {name}"))?;
        entry.name = new_name.to_string();
        entry.location = location.to_string();
        self.write_registered_table_entries(&entries)?;
        self.registered_tables.remove(name);
        self.registered_tables.insert(new_name.to_string(), location.to_string());
        Ok(())
    }

    async fn remove_registered_table_entry_s3(
        &self,
        name: &str,
    ) -> Result<String, Box<dyn std::error::Error + Send + Sync>> {
        let mut entries = self.read_registered_table_entries_s3().await?;
        let location = entries
            .iter()
            .find(|entry| entry.name == name)
            .map(|entry| entry.location.clone())
            .ok_or_else(|| format!("registered table not found: {name}"))?;
        entries.retain(|entry| entry.name != name);
        self.write_registered_table_entries_s3(&entries).await?;
        self.registered_tables.remove(name);
        Ok(location)
    }

    async fn rename_registered_table_entry_s3(
        &self,
        name: &str,
        new_name: &str,
        location: &str,
    ) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let mut entries = self.read_registered_table_entries_s3().await?;
        let entry = entries
            .iter_mut()
            .find(|entry| entry.name == name)
            .ok_or_else(|| format!("registered table not found: {name}"))?;
        entry.name = new_name.to_string();
        entry.location = location.to_string();
        self.write_registered_table_entries_s3(&entries).await?;
        self.registered_tables.remove(name);
        self.registered_tables.insert(new_name.to_string(), location.to_string());
        Ok(())
    }

    async fn ensure_table_registered(
        &self,
        table_name: &str,
    ) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let table_name = table_name.trim();
        if table_name.is_empty() || self.session.table_exist(table_name)? {
            return Ok(());
        }
        if buffered_current_table_with_config(table_name, &self.storage.buffered_table_prefixes) {
            self.ensure_buffered_table_loaded(table_name).await?;
            return Ok(());
        }

        // Acquire a per-table mutex before touching the session.
        // This serialises concurrent registration attempts for the same table,
        // eliminating the TOCTOU race where N parallel requests would each open
        // the same Lance/S3 dataset independently (→ N×S3 opens, connection exhaustion).
        let lock = self
            .registration_locks
            .entry(table_name.to_string())
            .or_insert_with(|| Arc::new(tokio::sync::Mutex::new(())))
            .clone();
        let _guard = lock.lock().await;

        // Double-check: another task may have registered while we were waiting.
        if self.session.table_exist(table_name)? {
            return Ok(());
        }

        self.remember_table_name(table_name);

        if !self.storage.direct_tables.is_empty() {
            for table in &self.storage.direct_tables {
                if table.name != table_name {
                    continue;
                }
                if table.uri.starts_with("s3://") {
                    return self.register_s3_table(&table.name, &table.uri).await;
                }
                return self
                    .register_local_table(&table.name, Path::new(&table.uri))
                    .await;
            }
        }

        if self.storage.lance_uri.starts_with("s3://") {
            let uri = format!(
                "{}/{}",
                self.storage.lance_uri.trim_end_matches('/'),
                table_name
            );
            if self.register_s3_table(table_name, &uri).await.is_ok() {
                return Ok(());
            }
            let uri_lance = format!(
                "{}/{}.lance",
                self.storage.lance_uri.trim_end_matches('/'),
                table_name
            );
            return self.register_s3_table(table_name, &uri_lance).await;
        }

        let path = Path::new(&self.storage.lance_uri).join(table_name);
        if path.exists() {
            return self.register_local_table(table_name, &path).await;
        }
        let path_lance = Path::new(&self.storage.lance_uri).join(format!("{table_name}.lance"));
        if path_lance.exists() {
            return self.register_local_table(table_name, &path_lance).await;
        }
        let compat_path =
            Path::new(&self.storage.lance_uri).join(format!("{table_name}.table.json"));
        if compat_path.exists() {
            return self.register_local_compat_table(table_name, &compat_path);
        }

        Ok(())
    }

    async fn ensure_buffered_table_loaded(
        &self,
        table_name: &str,
    ) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        // Quick path: already loaded — check without acquiring the load barrier.
        // Clone the Arc out of the DashMap Ref immediately so the shard lock is
        // released before any .await — holding a Ref across .await blocks other
        // Tokio workers trying to write to the same shard.
        if let Some(state_arc) = self.buffered_table_states.get(table_name).map(|e| e.clone()) {
            if state_arc.lock().await.loaded {
                return Ok(());
            }
        }

        // Acquire the per-table load barrier so only one task loads from storage.
        // Other concurrent callers block here and then find loaded=true on re-check.
        let barrier = self
            .buffered_load_barriers
            .entry(table_name.to_string())
            .or_insert_with(|| Arc::new(tokio::sync::Mutex::new(())))
            .clone();
        let _guard = barrier.lock().await;

        // Double-check under barrier: the previous holder may have loaded.
        let state_arc = self
            .buffered_table_states
            .entry(table_name.to_string())
            .or_insert_with(|| {
                Arc::new(tokio::sync::Mutex::new(
                    BufferedCurrentTableState::default(),
                ))
            })
            .clone();
        {
            if state_arc.lock().await.loaded {
                return Ok(());
            }
        }

        let rows = self.load_rows_from_storage(table_name).await?;
        let normalized = normalize_rows_for_known_table(table_name, rows);
        let keyed = normalized
            .into_iter()
            .map(|row| (buffered_row_key(table_name, &row), row))
            .collect::<BTreeMap<_, _>>();
        let snapshot = keyed.values().cloned().collect::<Vec<_>>();

        {
            let mut state = state_arc.lock().await;
            state.loaded = true;
            state.loading = false;
            state.rows = keyed;
            state.pending_events.clear();
            state.dirty_count = 0;
            state.version = 0;
            state.last_flush_at = Some(Instant::now());
        }

        self.apply_current_buffer_to_session(table_name, &snapshot)?;
        Ok(())
    }

    async fn upsert_rows_buffered_current(
        &self,
        table_name: &str,
        _key_columns: &[String],
        rows: Vec<Map<String, Value>>,
    ) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        self.ensure_buffered_table_loaded(table_name).await?;
        let normalized = normalize_rows_for_known_table(table_name, rows);
        let should_force_flush = should_force_buffer_flush(table_name, &normalized);

        let state_arc = self
            .buffered_table_states
            .entry(table_name.to_string())
            .or_insert_with(|| {
                Arc::new(tokio::sync::Mutex::new(
                    BufferedCurrentTableState::default(),
                ))
            })
            .clone();

        {
            let mut state = state_arc.lock().await;
            for row in &normalized {
                state
                    .rows
                    .insert(buffered_row_key(table_name, row), row.clone());
                if let Some(event_table) = buffered_current_event_table(table_name) {
                    state.pending_events.push(buffered_current_event_row(
                        table_name,
                        event_table,
                        row,
                    ));
                }
            }
            state.loaded = true;
            state.version += 1;
            state.dirty_count += normalized.len();
        }
        // Session update is deferred to flush time — rebuilding the full MemTable
        // snapshot on every write is O(buffer_size) and becomes a bottleneck under
        // concurrent high-throughput ingest. Reads see the last flushed state;
        // forced flushes (should_force_flush=true) keep read-after-write for
        // tables like crawler_jobs that require immediate consistency.

        // Flush is spawned as a background task so the write response returns
        // immediately without waiting for S3. For forced flushes (e.g. a crawler
        // job reaching terminal state) we still need the flush to complete before
        // the response, so we await the join handle in that case.
        let handle = self.spawn_flush_or_inline(table_name.to_string(), should_force_flush);
        if should_force_flush {
            if let Some(handle) = handle {
                let _ = handle.await;
            } else {
                // Fallback for tests where Arc is not available.
                self.maybe_flush_buffered_current_table(table_name, true)
                    .await?;
            }
        }
        Ok(())
    }

    async fn maybe_flush_buffered_current_table(
        &self,
        table_name: &str,
        force: bool,
    ) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        if !buffered_current_table_with_config(table_name, &self.storage.buffered_table_prefixes) {
            return Ok(());
        }

        // Clone Arc immediately to release DashMap shard lock before any .await.
        let Some(state_arc) = self.buffered_table_states.get(table_name).map(|e| e.clone()) else {
            return Ok(());
        };

        // Acquire the per-table flush lock to prevent concurrent flushes.
        // If another flush is already in progress, skip — it will flush the current rows.
        let flush_lock_arc = {
            let state = state_arc.lock().await;
            state.flush_lock.clone()
        };
        let _flush_guard = match flush_lock_arc.try_lock() {
            Ok(guard) => guard,
            Err(_) => return Ok(()), // Another flush is in progress; let it handle the rows.
        };

        let (version, snapshot, pending_events, should_flush) = {
            let state = state_arc.lock().await;
            let should_flush = force
                || state.dirty_count >= self.storage.buffer_flush_rows
                || state
                    .last_flush_at
                    .is_none_or(|instant| instant.elapsed() >= Duration::from_secs(self.storage.buffer_flush_secs));
            (
                state.version,
                state.rows.values().cloned().collect::<Vec<_>>(),
                state.pending_events.clone(),
                should_flush && (state.dirty_count > 0 || !state.pending_events.is_empty()),
            )
        };

        if !should_flush {
            return Ok(());
        }

        // Retry buffered flush with exponential backoff (mirrors upsert_rows_s3 logic).
        let flush_start = std::time::Instant::now();
        let mut attempt = 0u32;
        loop {
            match self.write_current_rows_to_storage(table_name, snapshot.clone()).await {
                Ok(()) => break,
                Err(error)
                    if attempt < 4
                        && error
                            .downcast_ref::<lance::Error>()
                            .is_some_and(is_retryable_lance_write_error) =>
                {
                    attempt += 1;
                    let delay_ms = 250_u64 * (1_u64 << (attempt - 1));
                    tracing::warn!(
                        table = table_name,
                        attempt,
                        delay_ms,
                        "tonbo: retrying buffered flush"
                    );
                    tokio::time::sleep(Duration::from_millis(delay_ms)).await;
                }
                Err(error) => {
                    crate::metrics::FLUSH_TOTAL.with_label_values(&["error"]).inc();
                    return Err(format!("buffer flush current {table_name}: {error}").into());
                }
            }
        }
        crate::metrics::FLUSH_TOTAL.with_label_values(&["ok"]).inc();
        crate::metrics::FLUSH_DURATION
            .with_label_values(&[table_name])
            .observe(flush_start.elapsed().as_secs_f64());
        if let Some(event_table) = buffered_current_event_table(table_name) {
            if !pending_events.is_empty() {
                self.append_rows_to_storage(event_table, pending_events)
                    .await
                    .map_err(|error| format!("buffer flush events {event_table}: {error}"))?;
            }
        }

        {
            let mut state = state_arc.lock().await;
            if state.version == version {
                state.pending_events.clear();
                state.dirty_count = 0;
            }
            state.last_flush_at = Some(Instant::now());
        }
        // Update the DataFusion session once per flush rather than on every write.
        // This is safe: callers that need immediate read-after-write use
        // should_force_flush=true (e.g. crawler_jobs terminal state), which
        // reaches here via spawn_flush_or_inline awaited synchronously.
        self.apply_current_buffer_to_session(table_name, &snapshot)?;
        // Run auto-compact inline while flush_lock is still held.
        // This prevents compact_files from conflicting with a concurrent buffer flush —
        // any other flush attempt will try_lock() the per-table flush_lock, see it held,
        // and return immediately. The in-memory buffer keeps accepting writes throughout.
        self.maybe_auto_compact_after_flush(table_name).await;
        Ok(())
    }

    async fn maybe_auto_compact_after_flush(&self, table_name: &str) {
        let threshold = self.storage.compact_fragment_threshold;
        if threshold == 0 {
            return;
        }
        let location = match self.table_location(table_name).await {
            Ok(loc) => loc,
            Err(_) => return,
        };
        let dataset = match self.open_dataset_at(&location, false).await {
            Ok(ds) => ds,
            Err(_) => return,
        };
        let frag_count = dataset.get_fragments().len();
        if frag_count <= threshold {
            return;
        }
        tracing::info!(
            table = table_name,
            frag_count,
            threshold,
            "tonbo: auto-compact triggered"
        );
        match self.optimize_table(table_name, true, false, None).await {
            Ok(_) => tracing::info!(table = table_name, "tonbo: auto-compact complete"),
            Err(e) => tracing::warn!(table = table_name, error = %e, "tonbo: auto-compact failed"),
        }
    }

    pub async fn flush_dirty_buffered_tables(
        &self,
    ) -> Result<usize, Box<dyn std::error::Error + Send + Sync>> {
        let table_names = self
            .buffered_table_states
            .iter()
            .filter_map(|entry| {
                let state = entry.value().try_lock().ok()?;
                if state.dirty_count > 0 || !state.pending_events.is_empty() {
                    Some(entry.key().clone())
                } else {
                    None
                }
            })
            .collect::<Vec<_>>();
        let count = table_names.len();
        if count == 0 {
            return Ok(0);
        }
        if let Some(ctx) = self.arc() {
            // Flush all dirty tables in parallel — each table has its own per-table
            // mutex so cross-table contention is minimal.
            let handles: Vec<_> = table_names
                .into_iter()
                .map(|name| {
                    let ctx = ctx.clone();
                    tokio::spawn(async move {
                        ctx.maybe_flush_buffered_current_table(&name, true).await
                    })
                })
                .collect();
            for handle in handles {
                handle.await??;
            }
        } else {
            // Fallback for tests where Arc is not available.
            for table_name in table_names {
                self.maybe_flush_buffered_current_table(&table_name, true)
                    .await?;
            }
        }
        Ok(count)
    }

    fn apply_current_buffer_to_session(
        &self,
        table_name: &str,
        rows: &[Map<String, Value>],
    ) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let schema = desired_table_schema(table_name)
            .unwrap_or_else(|| Arc::new(infer_schema_from_rows_for_table(table_name, rows)));
        // Skip registration when schema is empty (inferred from zero rows on a brand-new table).
        // An empty-schema MemTable would shadow any future Lance-backed registration and make
        // `WHERE _doc_id = ?` fail until the next flush.  The table becomes visible once the
        // first real flush fires and apply_current_buffer_to_session is called with actual rows.
        if schema.fields().is_empty() {
            return Ok(());
        }
        let batch = if rows.is_empty() {
            RecordBatch::new_empty(schema.clone())
        } else {
            json_rows_to_batch(schema.clone(), rows)?
        };
        let provider = MemTable::try_new(schema, vec![vec![batch]])?;
        let _ = self.session.deregister_table(table_name);
        self.session
            .register_table(table_name, Arc::new(provider))?;
        self.remember_table_name(table_name);
        Ok(())
    }

    async fn write_current_rows_to_storage(
        &self,
        table_name: &str,
        rows: Vec<Map<String, Value>>,
    ) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let _write_permit = self
            .write_semaphore
            .acquire()
            .await
            .map_err(|_| "write semaphore closed")?;
        if self.storage.lance_uri.starts_with("s3://") {
            self.write_rows_current_s3(table_name, rows).await
        } else {
            self.write_rows_current_local(table_name, rows).await
        }
    }

    async fn write_rows_current_s3(
        &self,
        table_name: &str,
        rows: Vec<Map<String, Value>>,
    ) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let uri = format!(
            "{}/{}",
            self.storage.lance_uri.trim_end_matches('/'),
            table_name
        );
        let rows = normalize_rows_for_known_table(table_name, rows);
        let schema = infer_schema_from_rows_for_table(table_name, &rows);
        match self
            .write_rows_to_uri(&uri, Arc::new(schema.clone()), rows.clone(), true, true)
            .await
        {
            Ok(()) => Ok(()),
            Err(error) if is_storage_not_found(error.as_ref()) => {
                self.write_rows_to_uri(&uri, Arc::new(schema), rows, true, false)
                    .await
            }
            Err(error) => Err(error),
        }
    }

    async fn write_rows_current_local(
        &self,
        table_name: &str,
        rows: Vec<Map<String, Value>>,
    ) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let uri = format!(
            "{}/{}",
            self.storage.lance_uri.trim_end_matches('/'),
            table_name
        );
        let rows = normalize_rows_for_known_table(table_name, rows);
        let schema = infer_schema_from_rows_for_table(table_name, &rows);
        let existing_uri = open_local_dataset_uri(&uri).await;
        if existing_uri.is_some() {
            self.write_rows_to_uri(&uri, Arc::new(schema), rows, false, true)
                .await
        } else {
            let batch = json_rows_to_batch(Arc::new(schema), &rows)?;
            let insert = lance::dataset::InsertBuilder::new(&uri);
            insert.execute(vec![batch]).await?;
            Ok(())
        }
    }

    async fn append_rows_to_storage(
        &self,
        table_name: &str,
        rows: Vec<Map<String, Value>>,
    ) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        if rows.is_empty() {
            return Ok(());
        }
        let _write_permit = self
            .write_semaphore
            .acquire()
            .await
            .map_err(|_| "write semaphore closed")?;
        if self.storage.lance_uri.starts_with("s3://") {
            self.append_rows_s3(table_name, rows).await
        } else {
            self.append_rows_local(table_name, rows).await
        }
    }

    async fn append_rows_s3(
        &self,
        table_name: &str,
        rows: Vec<Map<String, Value>>,
    ) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let uri = format!(
            "{}/{}",
            self.storage.lance_uri.trim_end_matches('/'),
            table_name
        );
        let store_params = self.build_s3_store_params(false)?;
        let rows = normalize_rows_for_known_table(table_name, rows);
        match DatasetBuilder::from_uri(&uri)
            .with_read_params(ReadParams {
                store_options: Some(store_params.clone()),
                ..Default::default()
            })
            .load()
            .await
        {
            Ok(dataset) => {
                let dataset_schema: SchemaRef = Arc::new(dataset.schema().into());
                let rows = normalize_rows_to_schema(&rows, dataset_schema.as_ref());
                let batch = json_rows_to_batch(dataset_schema.clone(), &rows)?;
                let params = lance::dataset::WriteParams {
                    store_params: Some(store_params.clone()),
                    ..Default::default()
                };
                let insert = lance::dataset::InsertBuilder::new(&uri).with_params(&params);
                match insert.execute(vec![batch]).await {
                    Ok(_) => Ok(()),
                    Err(error) if is_dataset_already_exists(&error) => {
                        tracing::warn!(
                            table = table_name,
                            error = %error,
                            "tonbo: append_rows_s3 dataset raced, retrying"
                        );
                        let dataset = DatasetBuilder::from_uri(&uri)
                            .with_read_params(ReadParams {
                                store_options: Some(store_params.clone()),
                                ..Default::default()
                            })
                            .load()
                            .await?;
                        let retry_schema: SchemaRef = Arc::new(dataset.schema().into());
                        let retry_rows = normalize_rows_to_schema(&rows, retry_schema.as_ref());
                        let retry_batch = json_rows_to_batch(retry_schema, &retry_rows)?;
                        let retry_params = lance::dataset::WriteParams {
                            store_params: Some(store_params),
                            ..Default::default()
                        };
                        let retry_insert =
                            lance::dataset::InsertBuilder::new(&uri).with_params(&retry_params);
                        retry_insert.execute(vec![retry_batch]).await?;
                        Ok(())
                    }
                    Err(error) => Err(error.into()),
                }
            }
            Err(lance::Error::DatasetNotFound { .. }) | Err(lance::Error::NotFound { .. }) => {
                let schema = infer_schema_from_rows_for_table(table_name, &rows);
                self.append_rows_s3_create(&uri, Arc::new(schema), rows, store_params)
                    .await
            }
            Err(error) => Err(error.into()),
        }
    }

    /// Create-path for `append_rows_s3` with "Dataset already exists" race retry.
    async fn append_rows_s3_create(
        &self,
        uri: &str,
        schema: SchemaRef,
        rows: Vec<Map<String, Value>>,
        store_params: ObjectStoreParams,
    ) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let batch = json_rows_to_batch(schema, &rows)?;
        let batch_schema = batch.schema();
        let reader: Box<dyn arrow::record_batch::RecordBatchReader + Send> =
            if batch.num_rows() == 0 {
                Box::new(arrow::record_batch::RecordBatchIterator::new(
                    Vec::<arrow::error::Result<RecordBatch>>::new().into_iter(),
                    batch_schema,
                ))
            } else {
                Box::new(arrow::record_batch::RecordBatchIterator::new(
                    vec![Ok(batch)].into_iter(),
                    batch_schema,
                ))
            };
        let params = lance::dataset::WriteParams {
            mode: lance::dataset::WriteMode::Create,
            store_params: Some(store_params.clone()),
            ..Default::default()
        };
        match Dataset::write(reader, uri, Some(params)).await {
            Ok(_) => Ok(()),
            Err(error) if is_dataset_already_exists(&error) => {
                tracing::warn!(
                    uri = uri,
                    error = %error,
                    "tonbo: append_rows_s3 create raced, loading and appending"
                );
                let dataset = DatasetBuilder::from_uri(uri)
                    .with_read_params(ReadParams {
                        store_options: Some(store_params.clone()),
                        ..Default::default()
                    })
                    .load()
                    .await?;
                let dataset_schema: SchemaRef = Arc::new(dataset.schema().into());
                let retry_rows = normalize_rows_to_schema(&rows, dataset_schema.as_ref());
                let retry_batch = json_rows_to_batch(dataset_schema, &retry_rows)?;
                let retry_params = lance::dataset::WriteParams {
                    store_params: Some(store_params),
                    ..Default::default()
                };
                let retry_insert =
                    lance::dataset::InsertBuilder::new(uri).with_params(&retry_params);
                retry_insert.execute(vec![retry_batch]).await?;
                Ok(())
            }
            Err(error) => Err(error.into()),
        }
    }

    async fn append_rows_local(
        &self,
        table_name: &str,
        rows: Vec<Map<String, Value>>,
    ) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let uri = format!(
            "{}/{}",
            self.storage.lance_uri.trim_end_matches('/'),
            table_name
        );
        let mut rows = normalize_rows_for_known_table(table_name, rows);
        if let Some(existing_uri) = open_local_dataset_uri(&uri).await {
            let mut existing = self.load_rows_from_storage_local(table_name).await?;
            existing.append(&mut rows);
            let schema = infer_schema_from_rows_for_table(table_name, &existing);
            return self
                .write_rows_to_uri(&existing_uri, Arc::new(schema), existing, false, true)
                .await;
        }
        let schema = infer_schema_from_rows_for_table(table_name, &rows);
        let batch = json_rows_to_batch(Arc::new(schema), &rows)?;
        let insert = lance::dataset::InsertBuilder::new(&uri);
        match insert.execute(vec![batch]).await {
            Ok(_) => Ok(()),
            Err(error) if error.to_string().contains("Dataset already exists") => {
                let existing_uri = open_local_dataset_uri(&uri)
                    .await
                    .ok_or_else(|| "local dataset exists but could not be opened".to_string())?;
                let mut existing = self.load_rows_from_storage_local(table_name).await?;
                existing.extend(rows);
                let schema = infer_schema_from_rows_for_table(table_name, &existing);
                self.write_rows_to_uri(&existing_uri, Arc::new(schema), existing, false, true)
                    .await
            }
            Err(error) => Err(error.into()),
        }
    }

    async fn load_rows_from_storage(
        &self,
        table_name: &str,
    ) -> Result<Vec<Map<String, Value>>, Box<dyn std::error::Error + Send + Sync>> {
        if self.storage.lance_uri.starts_with("s3://") {
            self.load_rows_from_storage_s3(table_name).await
        } else {
            self.load_rows_from_storage_local(table_name).await
        }
    }

    async fn load_rows_from_storage_s3(
        &self,
        table_name: &str,
    ) -> Result<Vec<Map<String, Value>>, Box<dyn std::error::Error + Send + Sync>> {
        let temp = ephemeral_table_name(table_name);
        for uri in s3_table_uri_candidates(&self.storage.lance_uri, table_name) {
            match self.register_s3_table(&temp, &uri).await {
                Ok(()) => {
                    let rows = self.collect_registered_table_rows(&temp).await;
                    let _ = self.session.deregister_table(&temp);
                    self.forget_table_name(&temp);
                    return rows;
                }
                Err(error) => {
                    if !is_storage_not_found(error.as_ref()) {
                        return Err(error);
                    }
                }
            }
        }
        Ok(Vec::new())
    }

    async fn load_rows_from_storage_local(
        &self,
        table_name: &str,
    ) -> Result<Vec<Map<String, Value>>, Box<dyn std::error::Error + Send + Sync>> {
        let temp = ephemeral_table_name(table_name);
        let root = Path::new(&self.storage.lance_uri);
        for path in local_table_path_candidates(root, table_name) {
            if !path.exists() {
                continue;
            }
            if path
                .file_name()
                .and_then(|name| name.to_str())
                .is_some_and(|name| name.ends_with(".table.json"))
            {
                match self.register_local_compat_table(&temp, &path) {
                    Ok(()) => {
                        let rows = self.collect_registered_table_rows(&temp).await;
                        let _ = self.session.deregister_table(&temp);
                        self.forget_table_name(&temp);
                        return rows;
                    }
                    Err(error) => return Err(error),
                }
            } else if path.exists() {
                match self.register_local_table(&temp, &path).await {
                    Ok(()) => {
                        let rows = self.collect_registered_table_rows(&temp).await;
                        let _ = self.session.deregister_table(&temp);
                        self.forget_table_name(&temp);
                        return rows;
                    }
                    Err(error) => return Err(error),
                }
            }
        }
        Ok(Vec::new())
    }

    async fn collect_registered_table_rows(
        &self,
        table_name: &str,
    ) -> Result<Vec<Map<String, Value>>, Box<dyn std::error::Error + Send + Sync>> {
        let sql = format!("SELECT * FROM \"{}\"", table_name);
        let dataframe = self.session.sql(&sql).await?;
        let batches = dataframe.collect().await?;
        rows_from_batches(&batches)
    }

    async fn open_dataset_at(
        &self,
        location: &str,
        allow_cache_wrapper: bool,
    ) -> Result<Dataset, Box<dyn std::error::Error + Send + Sync>> {
        if location.starts_with("s3://") {
            let params = self.build_s3_store_params(allow_cache_wrapper)?;
            return Ok(DatasetBuilder::from_uri(location)
                .with_read_params(ReadParams {
                    store_options: Some(params),
                    ..Default::default()
                })
                .load()
                .await?);
        }
        Ok(Dataset::open(location).await?)
    }
}

fn build_s3_store_params(s3: &S3Config, allow_cache_wrapper: bool) -> ObjectStoreParams {
    let mut storage_options = std::collections::HashMap::new();
    storage_options.insert("region".to_string(), s3.region.clone());
    storage_options.insert("access_key_id".to_string(), s3.access_key.clone());
    storage_options.insert("secret_access_key".to_string(), s3.secret_key.clone());
    storage_options.insert(
        "virtual_hosted_style_request".to_string(),
        s3.virtual_hosted_style.to_string(),
    );
    if !s3.endpoint.is_empty() {
        storage_options.insert("endpoint".to_string(), s3.endpoint.clone());
    }
    if s3.endpoint.starts_with("http://") {
        storage_options.insert("allow_http".to_string(), "true".to_string());
    }

    ObjectStoreParams {
        storage_options: Some(storage_options),
        object_store_wrapper: if allow_cache_wrapper {
            s3.read_through_cache.as_ref().map(|cache_config| {
                Arc::new(OcraStoreWrapper {
                    cache_config: cache_config.clone(),
                }) as Arc<dyn WrappingObjectStore>
            })
        } else {
            None
        },
        ..Default::default()
    }
}

fn normalize_key_columns(rows: &[Map<String, Value>], key_columns: Vec<String>) -> Vec<String> {
    let first = match rows.first() {
        Some(row) => row,
        None => return vec!["_doc_id".to_string()],
    };
    let mut out = Vec::new();
    for key in key_columns {
        let trimmed = key.trim();
        if trimmed.is_empty() || !first.contains_key(trimmed) || out.iter().any(|v| v == trimmed) {
            continue;
        }
        out.push(trimmed.to_string());
    }
    if out.is_empty() {
        if first.contains_key("_doc_id") {
            return vec!["_doc_id".to_string()];
        }
        if let Some(key) = first.keys().next() {
            return vec![key.clone()];
        }
    }
    out
}

fn infer_upsert_key_columns(columns: &[String]) -> Vec<String> {
    if columns.iter().any(|column| column == "_doc_id") {
        return vec!["_doc_id".to_string()];
    }

    let mut keys = Vec::new();
    for column in columns {
        if !keys.is_empty() && !looks_like_upsert_key(column) {
            break;
        }
        if looks_like_upsert_key(column) {
            keys.push(column.clone());
        }
    }
    if keys.is_empty() && !columns.is_empty() {
        keys.push(columns[0].clone());
    }
    keys
}

fn append_only_table(table_name: &str) -> bool {
    matches!(
        table_name,
        "crawler_results" | "crawler_job_events" | "crawler_job_url_events"
    )
}

fn buffered_current_table(table_name: &str) -> bool {
    matches!(table_name, "crawler_jobs" | "crawler_job_urls")
}

fn buffered_current_table_with_config(table_name: &str, prefixes: &[String]) -> bool {
    if buffered_current_table(table_name) {
        return true;
    }
    prefixes
        .iter()
        .any(|prefix| !prefix.is_empty() && table_name.starts_with(prefix.as_str()))
}

fn buffered_current_event_table(table_name: &str) -> Option<&'static str> {
    match table_name {
        "crawler_jobs" => Some("crawler_job_events"),
        "crawler_job_urls" => Some("crawler_job_url_events"),
        _ => None,
    }
}

fn should_force_buffer_flush(table_name: &str, rows: &[Map<String, Value>]) -> bool {
    match table_name {
        "crawler_jobs" => rows.iter().any(|row| {
            row.get("status")
                .and_then(Value::as_str)
                .is_some_and(|status| matches!(status, "completed" | "failed" | "cancelled"))
        }),
        "crawler_job_urls" => rows.iter().any(|row| {
            row.get("status")
                .and_then(Value::as_str)
                .is_some_and(|status| matches!(status, "visited" | "failed" | "skipped"))
        }),
        _ => false,
    }
}

fn buffered_row_key(table_name: &str, row: &Map<String, Value>) -> String {
    match table_name {
        "crawler_jobs" => row
            .get("_doc_id")
            .or_else(|| row.get("job_id"))
            .and_then(Value::as_str)
            .unwrap_or("")
            .to_string(),
        "crawler_job_urls" => row
            .get("_doc_id")
            .or_else(|| row.get("url_hash"))
            .and_then(Value::as_str)
            .unwrap_or("")
            .to_string(),
        _ => row
            .get("_doc_id")
            .and_then(Value::as_str)
            .unwrap_or("")
            .to_string(),
    }
}

fn buffered_current_event_row(
    table_name: &str,
    event_table: &str,
    row: &Map<String, Value>,
) -> Map<String, Value> {
    match table_name {
        "crawler_job_urls" => buffered_frontier_event_row(event_table, row),
        _ => buffered_job_event_row(table_name, event_table, row),
    }
}

fn buffered_job_event_row(
    table_name: &str,
    event_table: &str,
    row: &Map<String, Value>,
) -> Map<String, Value> {
    let mut event = Map::new();
    let event_id = format!(
        "{}:{}:{}",
        table_name,
        row.get("job_id").and_then(Value::as_str).unwrap_or(""),
        now_unix_micros()
    );
    event.insert("_doc_id".into(), Value::String(event_id.clone()));
    event.insert("event_id".into(), Value::String(event_id));
    event.insert("event_table".into(), Value::String(event_table.to_string()));
    for key in [
        "org_id",
        "user_id",
        "actor_id",
        "job_id",
        "url",
        "seed_urls",
        "status",
        "fail_reason",
        "terminal_reason",
        "started_at",
        "updated_at",
        "user_agent",
    ] {
        if let Some(value) = row.get(key).cloned() {
            event.insert(key.to_string(), value);
        }
    }
    for key in [
        "depth",
        "max_pages",
        "max_domains",
        "pages_found",
        "frontier_enqueued",
        "frontier_done",
        "frontier_failed",
        "render",
        "follow_ext",
    ] {
        if let Some(value) = row.get(key).cloned() {
            event.insert(key.to_string(), value);
        }
    }
    event.insert(
        "event_kind".into(),
        row.get("status")
            .cloned()
            .unwrap_or_else(|| Value::String("snapshot".into())),
    );
    event.insert("event_at".into(), Value::String(now_rfc3339()));
    normalize_rows_for_known_table("crawler_job_events", vec![event])
        .into_iter()
        .next()
        .unwrap_or_default()
}

fn buffered_frontier_event_row(event_table: &str, row: &Map<String, Value>) -> Map<String, Value> {
    let mut event = Map::new();
    let event_id = format!(
        "crawler_job_urls:{}:{}",
        row.get("_doc_id")
            .or_else(|| row.get("url_hash"))
            .and_then(Value::as_str)
            .unwrap_or(""),
        now_unix_micros()
    );
    event.insert("_doc_id".into(), Value::String(event_id.clone()));
    event.insert("event_id".into(), Value::String(event_id));
    event.insert("event_table".into(), Value::String(event_table.to_string()));
    event.insert(
        "event_kind".into(),
        row.get("status")
            .cloned()
            .unwrap_or_else(|| Value::String("snapshot".into())),
    );
    event.insert("event_at".into(), Value::String(now_rfc3339()));
    for key in [
        "url_hash",
        "url",
        "host",
        "status",
        "discovered_by",
        "last_error",
        "worker_id",
        "job_id",
        "lease_token",
    ] {
        if let Some(value) = row.get(key).cloned() {
            event.insert(key.to_string(), value);
        }
    }
    for key in [
        "depth_remaining",
        "priority",
        "attempts",
        "leased_until",
        "visited_at",
    ] {
        if let Some(value) = row.get(key).cloned() {
            event.insert(key.to_string(), value);
        }
    }
    normalize_rows_for_known_table("crawler_job_url_events", vec![event])
        .into_iter()
        .next()
        .unwrap_or_default()
}

fn now_unix_micros() -> u128 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|value| value.as_micros())
        .unwrap_or_default()
}

fn now_rfc3339() -> String {
    now_unix_micros().to_string()
}

fn ephemeral_table_name(table_name: &str) -> String {
    format!("__tonbo_load_{}_{}", table_name, now_unix_micros())
}

fn is_ephemeral_table_name(table_name: &str) -> bool {
    table_name.starts_with("__tonbo_load_")
}

fn s3_table_uri_candidates(base_uri: &str, table_name: &str) -> [String; 2] {
    [
        format!("{}/{}", base_uri.trim_end_matches('/'), table_name),
        format!("{}/{}.lance", base_uri.trim_end_matches('/'), table_name),
    ]
}

fn lance_index_to_table_index(
    index: &LanceIndexMetadata,
    schema: &lance::datatypes::Schema,
) -> Result<TableIndexInfo, Box<dyn std::error::Error + Send + Sync>> {
    let fields = index
        .fields
        .iter()
        .map(|field_id| {
            schema
                .field_by_id(*field_id)
                .map(|field| field.name.clone())
                .ok_or_else(|| format!("index field id not found in schema: {field_id}"))
        })
        .collect::<Result<Vec<_>, _>>()?;
    Ok(TableIndexInfo {
        name: index.name.clone(),
        dataset_version: index.dataset_version as i64,
        fields,
    })
}

fn renamed_s3_table_uri(
    source_uri: &str,
    new_table_name: &str,
) -> Result<String, Box<dyn std::error::Error + Send + Sync>> {
    let (prefix, _) = source_uri
        .rsplit_once('/')
        .ok_or("invalid s3 table uri for rename")?;
    if source_uri.ends_with(".lance") {
        Ok(format!("{prefix}/{new_table_name}.lance"))
    } else if source_uri.ends_with(".table.json") {
        Ok(format!("{prefix}/{new_table_name}.table.json"))
    } else {
        Ok(format!("{prefix}/{new_table_name}"))
    }
}

fn s3_object_path_from_uri(
    uri: &str,
) -> Result<(String, object_store::path::Path), Box<dyn std::error::Error + Send + Sync>> {
    let suffix = uri.strip_prefix("s3://").ok_or("invalid s3 uri")?;
    let (bucket, key) = suffix.split_once('/').ok_or("invalid s3 uri")?;
    let key = key.trim_matches('/');
    if key.is_empty() {
        return Err("invalid s3 uri".into());
    }
    Ok((
        bucket.to_string(),
        object_store::path::Path::from(key.to_string()),
    ))
}

async fn rename_object_store_prefix(
    store: Arc<dyn ObjectStore>,
    source_prefix: &object_store::path::Path,
    target_prefix: &object_store::path::Path,
) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let target_objects = store
        .list(Some(target_prefix))
        .try_collect::<Vec<_>>()
        .await?;
    if !target_objects.is_empty() {
        return Err(format!("table already exists at {target_prefix}").into());
    }

    let source_objects = store
        .list(Some(source_prefix))
        .try_collect::<Vec<_>>()
        .await?;
    if source_objects.is_empty() {
        return Err(format!("table not found at {source_prefix}").into());
    }

    for object in source_objects {
        let relative = object
            .location
            .prefix_match(source_prefix)
            .ok_or("object path is outside source prefix")?
            .map(|part| part.as_ref().to_string())
            .collect::<Vec<_>>();
        let target_location = if relative.is_empty() {
            target_prefix.clone()
        } else {
            object_store::path::Path::from(format!("{}/{}", target_prefix, relative.join("/")))
        };
        store.rename(&object.location, &target_location).await?;
    }
    Ok(())
}

fn local_table_path_candidates(root: &Path, table_name: &str) -> [std::path::PathBuf; 3] {
    [
        root.join(table_name),
        root.join(format!("{table_name}.lance")),
        root.join(format!("{table_name}.table.json")),
    ]
}

fn version_manifest_path(location: &str, version: i64) -> String {
    format!(
        "{}/_versions/{}.manifest",
        location.trim_end_matches('/'),
        version
    )
}

fn version_in_range(version: i64, start_version: i64, end_version: i64) -> bool {
    if start_version == 0 && end_version == -1 {
        return true;
    }
    if end_version >= 0 {
        return version >= start_version && version <= end_version;
    }
    version >= start_version
}

async fn open_local_dataset_uri(uri: &str) -> Option<String> {
    if Dataset::open(uri).await.is_ok() {
        return Some(uri.to_string());
    }
    let lance_uri = format!("{uri}.lance");
    if Dataset::open(&lance_uri).await.is_ok() {
        return Some(lance_uri);
    }
    None
}

fn is_storage_not_found(error: &(dyn std::error::Error + Send + Sync)) -> bool {
    error.to_string().contains("DatasetNotFound")
        || error.to_string().contains("not found")
        || error.to_string().contains("NotFound")
}

fn is_dataset_already_exists<E: std::fmt::Display + ?Sized>(error: &E) -> bool {
    error.to_string().contains("Dataset already exists")
}

fn looks_like_upsert_key(column: &str) -> bool {
    matches!(
        column,
        "alias" | "data_type" | "server_name" | "tag" | "user_id" | "version"
    ) || column.ends_with("_id")
        || column.ends_with("_name")
}

fn decode_compat_data_type(spec: &str) -> DataType {
    match spec {
        "int64" => DataType::Int64,
        "int32" => DataType::Int32,
        "float64" => DataType::Float64,
        "float32" => DataType::Float32,
        "bool" => DataType::Boolean,
        "binary" => DataType::Binary,
        "largebinary" => DataType::LargeBinary,
        "timestamp_us" => DataType::Timestamp(TimeUnit::Microsecond, None),
        _ if spec.starts_with("list:float32") => {
            DataType::List(Arc::new(Field::new("item", DataType::Float32, true)))
        }
        _ if spec.starts_with("fsl:") && spec.ends_with(":float32") => {
            let len = spec
                .split(':')
                .nth(1)
                .and_then(|value| value.parse::<i32>().ok())
                .unwrap_or(1);
            DataType::FixedSizeList(Arc::new(Field::new("item", DataType::Float32, true)), len)
        }
        _ => DataType::Utf8,
    }
}

fn compat_rows_to_batch(
    schema: SchemaRef,
    rows: &[Map<String, Value>],
) -> Result<RecordBatch, Box<dyn std::error::Error + Send + Sync>> {
    let columns = schema
        .fields()
        .iter()
        .map(|field| compat_build_array(field.as_ref(), rows))
        .collect::<Result<Vec<_>, _>>()?;
    Ok(RecordBatch::try_new(schema, columns)?)
}

fn compat_build_array(
    field: &Field,
    rows: &[Map<String, Value>],
) -> Result<ArrayRef, Box<dyn std::error::Error + Send + Sync>> {
    match field.data_type() {
        DataType::Utf8 => {
            let mut builder = StringBuilder::new();
            for row in rows {
                match row.get(field.name()) {
                    Some(Value::String(value)) => builder.append_value(value),
                    Some(Value::Null) | None => builder.append_null(),
                    Some(value) => builder.append_value(value.to_string()),
                }
            }
            Ok(Arc::new(builder.finish()))
        }
        DataType::Int64 => {
            let mut builder = Int64Builder::new();
            for row in rows {
                compat_append_number(row.get(field.name()), &mut builder, |value| value as i64)?;
            }
            Ok(Arc::new(builder.finish()))
        }
        DataType::Int32 => {
            let mut builder = Int32Builder::new();
            for row in rows {
                compat_append_number(row.get(field.name()), &mut builder, |value| value as i32)?;
            }
            Ok(Arc::new(builder.finish()))
        }
        DataType::Float64 => {
            let mut builder = Float64Builder::new();
            for row in rows {
                compat_append_number(row.get(field.name()), &mut builder, |value| value)?;
            }
            Ok(Arc::new(builder.finish()))
        }
        DataType::Float32 => {
            let mut builder = Float32Builder::new();
            for row in rows {
                compat_append_number(row.get(field.name()), &mut builder, |value| value as f32)?;
            }
            Ok(Arc::new(builder.finish()))
        }
        DataType::Boolean => {
            let mut builder = BooleanBuilder::new();
            for row in rows {
                match row.get(field.name()) {
                    Some(Value::Bool(value)) => builder.append_value(*value),
                    Some(Value::Null) | None => builder.append_null(),
                    Some(_) => builder.append_null(),
                }
            }
            Ok(Arc::new(builder.finish()))
        }
        DataType::Binary => {
            let mut builder = BinaryBuilder::new();
            for row in rows {
                match row.get(field.name()) {
                    Some(Value::String(value)) => builder.append_value(value.as_bytes()),
                    Some(Value::Null) | None => builder.append_null(),
                    Some(value) => builder.append_value(value.to_string().as_bytes()),
                }
            }
            Ok(Arc::new(builder.finish()))
        }
        DataType::LargeBinary => {
            let mut builder = LargeBinaryBuilder::new();
            for row in rows {
                match row.get(field.name()) {
                    Some(Value::String(value)) => builder.append_value(value.as_bytes()),
                    Some(Value::Null) | None => builder.append_null(),
                    Some(value) => builder.append_value(value.to_string().as_bytes()),
                }
            }
            Ok(Arc::new(builder.finish()))
        }
        DataType::Timestamp(TimeUnit::Microsecond, _) => {
            let mut builder = TimestampMicrosecondBuilder::new();
            for row in rows {
                match row.get(field.name()) {
                    Some(Value::Number(value)) => match value.as_i64() {
                        Some(ts) => builder.append_value(ts),
                        None => builder.append_null(),
                    },
                    Some(Value::Null) | None => builder.append_null(),
                    Some(_) => builder.append_null(),
                }
            }
            Ok(Arc::new(builder.finish()))
        }
        DataType::List(child) if matches!(child.data_type(), DataType::Float32) => {
            let mut builder = ListBuilder::new(Float32Builder::new());
            for row in rows {
                match row.get(field.name()) {
                    Some(Value::Array(values)) => {
                        for value in values {
                            match value.as_f64() {
                                Some(v) => builder.values().append_value(v as f32),
                                None => builder.values().append_null(),
                            }
                        }
                        builder.append(true);
                    }
                    Some(Value::Null) | None => builder.append(false),
                    Some(_) => builder.append(false),
                }
            }
            Ok(Arc::new(builder.finish()))
        }
        DataType::FixedSizeList(child, _) if matches!(child.data_type(), DataType::Float32) => {
            let list_size = match field.data_type() {
                DataType::FixedSizeList(_, len) => *len as usize,
                _ => 0,
            };
            let mut builder = FixedSizeListBuilder::new(Float32Builder::new(), list_size as i32);
            for row in rows {
                match row.get(field.name()) {
                    Some(Value::Array(values)) => {
                        for index in 0..list_size {
                            match values.get(index).and_then(Value::as_f64) {
                                Some(value) => builder.values().append_value(value as f32),
                                None => builder.values().append_null(),
                            }
                        }
                        builder.append(true);
                    }
                    Some(Value::Null) | None => {
                        for _ in 0..list_size {
                            builder.values().append_null();
                        }
                        builder.append(false);
                    }
                    Some(_) => {
                        for _ in 0..list_size {
                            builder.values().append_null();
                        }
                        builder.append(false);
                    }
                }
            }
            Ok(Arc::new(builder.finish()))
        }
        _ => {
            let mut builder = StringBuilder::new();
            for row in rows {
                match row.get(field.name()) {
                    Some(Value::String(value)) => builder.append_value(value),
                    Some(Value::Null) | None => builder.append_null(),
                    Some(value) => builder.append_value(value.to_string()),
                }
            }
            Ok(Arc::new(builder.finish()))
        }
    }
}

trait ArrayBuilderNumber<T> {
    fn append_numeric(&mut self, value: T);
    fn append_null_value(&mut self);
}

impl ArrayBuilderNumber<i64> for Int64Builder {
    fn append_numeric(&mut self, value: i64) {
        self.append_value(value);
    }

    fn append_null_value(&mut self) {
        self.append_null();
    }
}

impl ArrayBuilderNumber<i32> for Int32Builder {
    fn append_numeric(&mut self, value: i32) {
        self.append_value(value);
    }

    fn append_null_value(&mut self) {
        self.append_null();
    }
}

impl ArrayBuilderNumber<f64> for Float64Builder {
    fn append_numeric(&mut self, value: f64) {
        self.append_value(value);
    }

    fn append_null_value(&mut self) {
        self.append_null();
    }
}

impl ArrayBuilderNumber<f32> for Float32Builder {
    fn append_numeric(&mut self, value: f32) {
        self.append_value(value);
    }

    fn append_null_value(&mut self) {
        self.append_null();
    }
}

fn compat_append_number<T, F>(
    value: Option<&Value>,
    builder: &mut impl ArrayBuilderNumber<T>,
    cast: F,
) -> Result<(), Box<dyn std::error::Error + Send + Sync>>
where
    F: Fn(f64) -> T,
{
    match value {
        Some(Value::Number(number)) => match number.as_f64() {
            Some(value) => builder.append_numeric(cast(value)),
            None => builder.append_null_value(),
        },
        Some(Value::Null) | None => builder.append_null_value(),
        Some(_) => builder.append_null_value(),
    }
    Ok(())
}

#[cfg_attr(not(test), allow(dead_code))]
fn infer_schema_from_rows(rows: &[Map<String, Value>]) -> Schema {
    infer_schema_from_rows_for_table("", rows)
}

fn is_retryable_lance_write_error(error: &lance::Error) -> bool {
    match error {
        lance::Error::CommitConflict { .. } => true,
        lance::Error::IO { source, .. }
        | lance::Error::NotSupported { source, .. }
        | lance::Error::InvalidInput { source, .. }
        | lance::Error::Wrapped { error: source, .. } => {
            is_retryable_storage_error_text(&source.to_string())
        }
        _ => false,
    }
}

fn is_retryable_storage_error_text(text: &str) -> bool {
    let text = text.to_ascii_lowercase();
    text.contains("http status server error (503")
        || text.contains("service unavailable")
        || text.contains("operation timeout")
        || text.contains("connection reset by peer")
        || text.contains("temporarily unavailable")
        || text.contains("generic s3 error")
}

fn retryable_lance_error_reason(error: &lance::Error) -> &'static str {
    match error {
        lance::Error::CommitConflict { .. } => "commit-conflict",
        lance::Error::IO { .. } => "io",
        lance::Error::NotSupported { .. } => "not-supported",
        lance::Error::InvalidInput { .. } => "invalid-input",
        lance::Error::Wrapped { .. } => "wrapped",
        _ => "other",
    }
}

fn infer_schema_from_rows_for_table(table_name: &str, rows: &[Map<String, Value>]) -> Schema {
    if let Some(schema) = desired_table_schema(table_name) {
        return schema.as_ref().clone();
    }
    let mut fields: BTreeMap<String, DataType> = BTreeMap::new();
    for row in rows {
        for (name, value) in row {
            let next = infer_data_type(value);
            fields
                .entry(name.clone())
                .and_modify(|current| *current = merge_data_types(current, &next))
                .or_insert(next);
        }
    }
    Schema::new(
        fields
            .into_iter()
            .map(|(name, dtype)| Field::new(name, dtype, true))
            .collect::<Vec<_>>(),
    )
}

fn desired_table_schema(table_name: &str) -> Option<SchemaRef> {
    let schema = match table_name {
        "crawler_pages" => Schema::new(vec![
            Field::new("_doc_id", DataType::Utf8, false),
            Field::new("doc_id", DataType::Utf8, true),
            Field::new("result_id", DataType::Utf8, true),
            Field::new("job_id", DataType::Utf8, true),
            Field::new("url", DataType::Utf8, true),
            Field::new("domain", DataType::Utf8, true),
            Field::new("title", DataType::Utf8, true),
            Field::new("snippet", DataType::Utf8, true),
            Field::new("text_content", DataType::Utf8, true),
            Field::new("language", DataType::Utf8, true),
            Field::new("status", DataType::Int64, true),
            Field::new("size_bytes", DataType::Int64, true),
            Field::new("link_count", DataType::Int64, true),
            Field::new("primary_image", DataType::Utf8, true),
            Field::new("primary_image_cdn", DataType::Utf8, true),
            Field::new("indexed_at", DataType::Utf8, true),
            Field::new("seed_category", DataType::Utf8, true),
            Field::new("metadata_json", DataType::Utf8, true),
            Field::new("ogp_json", DataType::Utf8, true),
        ]),
        "crawler_jobs" => Schema::new(vec![
            Field::new("_doc_id", DataType::Utf8, false),
            Field::new("org_id", DataType::Utf8, true),
            Field::new("user_id", DataType::Utf8, true),
            Field::new("actor_id", DataType::Utf8, true),
            Field::new("job_id", DataType::Utf8, true),
            Field::new("url", DataType::Utf8, true),
            Field::new("seed_urls", DataType::Utf8, true),
            Field::new("depth", DataType::Int64, true),
            Field::new("max_pages", DataType::Int64, true),
            Field::new("max_domains", DataType::Int64, true),
            Field::new("status", DataType::Utf8, true),
            Field::new("fail_reason", DataType::Utf8, true),
            Field::new("terminal_reason", DataType::Utf8, true),
            Field::new("pages_found", DataType::Int64, true),
            Field::new("frontier_enqueued", DataType::Int64, true),
            Field::new("frontier_done", DataType::Int64, true),
            Field::new("frontier_failed", DataType::Int64, true),
            Field::new("started_at", DataType::Utf8, true),
            Field::new("updated_at", DataType::Utf8, true),
            Field::new("user_agent", DataType::Utf8, true),
            Field::new("render", DataType::Int64, true),
            Field::new("follow_ext", DataType::Int64, true),
        ]),
        "crawler_job_events" => Schema::new(vec![
            Field::new("_doc_id", DataType::Utf8, false),
            Field::new("event_id", DataType::Utf8, true),
            Field::new("event_table", DataType::Utf8, true),
            Field::new("event_kind", DataType::Utf8, true),
            Field::new("event_at", DataType::Utf8, true),
            Field::new("org_id", DataType::Utf8, true),
            Field::new("user_id", DataType::Utf8, true),
            Field::new("actor_id", DataType::Utf8, true),
            Field::new("job_id", DataType::Utf8, true),
            Field::new("url", DataType::Utf8, true),
            Field::new("seed_urls", DataType::Utf8, true),
            Field::new("depth", DataType::Int64, true),
            Field::new("max_pages", DataType::Int64, true),
            Field::new("max_domains", DataType::Int64, true),
            Field::new("status", DataType::Utf8, true),
            Field::new("fail_reason", DataType::Utf8, true),
            Field::new("terminal_reason", DataType::Utf8, true),
            Field::new("pages_found", DataType::Int64, true),
            Field::new("frontier_enqueued", DataType::Int64, true),
            Field::new("frontier_done", DataType::Int64, true),
            Field::new("frontier_failed", DataType::Int64, true),
            Field::new("started_at", DataType::Utf8, true),
            Field::new("updated_at", DataType::Utf8, true),
            Field::new("user_agent", DataType::Utf8, true),
            Field::new("render", DataType::Int64, true),
            Field::new("follow_ext", DataType::Int64, true),
        ]),
        "crawler_results" => Schema::new(vec![
            Field::new("_doc_id", DataType::Utf8, true),
            Field::new("actor_id", DataType::Utf8, true),
            Field::new("content_hash", DataType::Utf8, true),
            Field::new("crawled_at", DataType::Utf8, true),
            Field::new("duplicate_of", DataType::Utf8, true),
            Field::new("duplicate_type", DataType::Utf8, true),
            Field::new("http_status", DataType::Int64, true),
            Field::new("image_urls_json", DataType::Utf8, true),
            Field::new("is_duplicate", DataType::Int64, true),
            Field::new("job_id", DataType::Utf8, true),
            Field::new("link_count", DataType::Int64, true),
            Field::new("metadata_json", DataType::Utf8, true),
            Field::new("org_id", DataType::Utf8, true),
            Field::new("primary_image", DataType::Utf8, true),
            Field::new("result_id", DataType::Utf8, true),
            Field::new("seed_category", DataType::Utf8, true),
            Field::new("seed_region", DataType::Utf8, true),
            Field::new("seed_source", DataType::Utf8, true),
            Field::new("sim_hash", DataType::Utf8, true),
            Field::new("size_bytes", DataType::Int64, true),
            Field::new("text_content", DataType::Utf8, true),
            Field::new("title", DataType::Utf8, true),
            Field::new("url", DataType::Utf8, true),
            Field::new("user_id", DataType::Utf8, true),
        ]),
        "crawler_job_urls" => Schema::new(vec![
            Field::new("_doc_id", DataType::Utf8, false),
            Field::new("url_hash", DataType::Utf8, true),
            Field::new("url", DataType::Utf8, true),
            Field::new("host", DataType::Utf8, true),
            Field::new("depth_remaining", DataType::Int64, true),
            Field::new("status", DataType::Utf8, true),
            Field::new("priority", DataType::Int64, true),
            Field::new("discovered_by", DataType::Utf8, true),
            Field::new("discovered_at", DataType::Utf8, true),
            Field::new("last_error", DataType::Utf8, true),
            Field::new("attempts", DataType::Int64, true),
            Field::new("leased_until", DataType::Int64, true),
            Field::new("worker_id", DataType::Utf8, true),
            Field::new("job_id", DataType::Utf8, true),
            Field::new("visited_at", DataType::Int64, true),
            Field::new("lease_token", DataType::Utf8, true),
        ]),
        "crawler_job_url_events" => Schema::new(vec![
            Field::new("_doc_id", DataType::Utf8, false),
            Field::new("event_id", DataType::Utf8, true),
            Field::new("event_table", DataType::Utf8, true),
            Field::new("event_kind", DataType::Utf8, true),
            Field::new("event_at", DataType::Utf8, true),
            Field::new("url_hash", DataType::Utf8, true),
            Field::new("url", DataType::Utf8, true),
            Field::new("host", DataType::Utf8, true),
            Field::new("depth_remaining", DataType::Int64, true),
            Field::new("status", DataType::Utf8, true),
            Field::new("priority", DataType::Int64, true),
            Field::new("discovered_by", DataType::Utf8, true),
            Field::new("last_error", DataType::Utf8, true),
            Field::new("attempts", DataType::Int64, true),
            Field::new("leased_until", DataType::Int64, true),
            Field::new("worker_id", DataType::Utf8, true),
            Field::new("job_id", DataType::Utf8, true),
            Field::new("visited_at", DataType::Int64, true),
            Field::new("lease_token", DataType::Utf8, true),
        ]),
        "messaging_rooms" => Schema::new(vec![
            Field::new("_doc_id", DataType::Utf8, false),
            Field::new("id", DataType::Utf8, true),
            Field::new("name", DataType::Utf8, true),
            Field::new("topic", DataType::Utf8, true),
            Field::new("creator_nanoid", DataType::Utf8, true),
            Field::new("visibility", DataType::Utf8, true),
            Field::new("room_type", DataType::Utf8, true),
            Field::new("encrypted", DataType::Int64, true),
            Field::new("archived", DataType::Int64, true),
            Field::new("mls_group_id", DataType::Utf8, true),
            Field::new("mls_cipher_suite", DataType::Utf8, true),
            Field::new("mls_epoch", DataType::Int64, true),
            Field::new("mls_tree_size", DataType::Int64, true),
            Field::new("org_id", DataType::Utf8, true),
            Field::new("user_id", DataType::Utf8, true),
            Field::new("actor_id", DataType::Utf8, true),
            Field::new("created_at", DataType::Utf8, true),
            Field::new("updated_at", DataType::Utf8, true),
        ]),
        "messaging_events" => Schema::new(vec![
            Field::new("_doc_id", DataType::Utf8, false),
            Field::new("id", DataType::Utf8, true),
            Field::new("room_id", DataType::Utf8, true),
            Field::new("sender", DataType::Utf8, true),
            Field::new("event_kind", DataType::Utf8, true),
            Field::new("state_key", DataType::Utf8, true),
            Field::new("content_json", DataType::Utf8, true),
            Field::new("parent_ids", DataType::Utf8, true),
            Field::new("mls_epoch", DataType::Int64, true),
            Field::new("redacted_by", DataType::Utf8, true),
            Field::new("org_id", DataType::Utf8, true),
            Field::new("user_id", DataType::Utf8, true),
            Field::new("actor_id", DataType::Utf8, true),
            Field::new("timestamp", DataType::Utf8, true),
        ]),
        "messaging_room_timeline_current" => Schema::new(vec![
            Field::new("_doc_id", DataType::Utf8, false),
            Field::new("room_id", DataType::Utf8, true),
            Field::new("id", DataType::Utf8, true),
            Field::new("seq_in_room", DataType::Int64, true),
            Field::new("sender", DataType::Utf8, true),
            Field::new("event_kind", DataType::Utf8, true),
            Field::new("state_key", DataType::Utf8, true),
            Field::new("content_json", DataType::Utf8, true),
            Field::new("parent_ids", DataType::Utf8, true),
            Field::new("mls_epoch", DataType::Int64, true),
            Field::new("redacted_by", DataType::Utf8, true),
            Field::new("org_id", DataType::Utf8, true),
            Field::new("user_id", DataType::Utf8, true),
            Field::new("actor_id", DataType::Utf8, true),
            Field::new("timestamp", DataType::Utf8, true),
            Field::new("created_at", DataType::Utf8, true),
            Field::new("updated_at", DataType::Utf8, true),
        ]),
        "shinshi_blobs" => Schema::new(vec![
            Field::new("_doc_id", DataType::Utf8, false),
            Field::new("blob_key", DataType::Utf8, true),
            Field::new("content_type", DataType::Utf8, true),
            Field::new("data_b64", DataType::Utf8, true),
            Field::new("size", DataType::Int64, true),
            Field::new("cid", DataType::Utf8, true),
            Field::new("s3_key", DataType::Utf8, true),
            Field::new("visibility", DataType::Utf8, true),
            Field::new("org_id", DataType::Utf8, true),
            Field::new("user_id", DataType::Utf8, true),
            Field::new("actor_id", DataType::Utf8, true),
        ]),
        "shinshi_models" => Schema::new(vec![
            Field::new("_doc_id", DataType::Utf8, false),
            Field::new("model_id", DataType::Utf8, true),
            Field::new("name", DataType::Utf8, true),
            Field::new("description", DataType::Utf8, true),
            Field::new("tags_json", DataType::Utf8, true),
            Field::new("profile_image_url", DataType::Utf8, true),
            Field::new("base_prompt", DataType::Utf8, true),
            Field::new("negative_prompt", DataType::Utf8, true),
            Field::new("style", DataType::Utf8, true),
            Field::new("created_at", DataType::Utf8, true),
            Field::new("updated_at", DataType::Utf8, true),
            Field::new("status", DataType::Utf8, true),
            Field::new("image_count", DataType::Int64, true),
            Field::new("ai_model_id", DataType::Utf8, true),
            Field::new("age", DataType::Utf8, true),
            Field::new("appearance", DataType::Utf8, true),
            Field::new("character", DataType::Utf8, true),
            Field::new("keywords", DataType::Utf8, true),
            Field::new("owner_id", DataType::Utf8, true),
            Field::new("org_id", DataType::Utf8, true),
            Field::new("user_id", DataType::Utf8, true),
            Field::new("actor_id", DataType::Utf8, true),
        ]),
        "shinshi_image_posts" => Schema::new(vec![
            Field::new("_doc_id", DataType::Utf8, false),
            Field::new("post_id", DataType::Utf8, true),
            Field::new("category", DataType::Utf8, true),
            Field::new("category_slug", DataType::Utf8, true),
            Field::new("title", DataType::Utf8, true),
            Field::new("prompt", DataType::Utf8, true),
            Field::new("negative_prompt", DataType::Utf8, true),
            Field::new("model", DataType::Utf8, true),
            Field::new("image_url", DataType::Utf8, true),
            Field::new("content_type", DataType::Utf8, true),
            Field::new("width", DataType::Int64, true),
            Field::new("height", DataType::Int64, true),
            Field::new("num_steps", DataType::Int64, true),
            Field::new("guidance_scale", DataType::Utf8, true),
            Field::new("seed", DataType::Int64, true),
            Field::new("model_id", DataType::Utf8, true),
            Field::new("created_at", DataType::Utf8, true),
            Field::new("source", DataType::Utf8, true),
            Field::new("cdn_path", DataType::Utf8, true),
            Field::new("generation_notes", DataType::Utf8, true),
            Field::new("keyword", DataType::Utf8, true),
            Field::new("tags_json", DataType::Utf8, true),
            Field::new("file_name", DataType::Utf8, true),
            Field::new("search_text", DataType::Utf8, true),
            Field::new("reactions_json", DataType::Utf8, true),
            Field::new("reaction_score", DataType::Int64, true),
            Field::new("org_id", DataType::Utf8, true),
            Field::new("user_id", DataType::Utf8, true),
            Field::new("actor_id", DataType::Utf8, true),
        ]),
        _ => return None,
    };
    Some(Arc::new(schema))
}

fn is_startup_reconcile_table(table_name: &str) -> bool {
    matches!(
        table_name,
        "messaging_rooms" | "messaging_events" | "messaging_room_timeline_current"
    )
}

fn schema_missing_known_columns(actual: &Schema, expected: &Schema) -> bool {
    expected
        .fields()
        .iter()
        .any(|field| actual.field_with_name(field.name()).is_err())
}

fn normalize_rows_for_known_table(
    table_name: &str,
    rows: Vec<Map<String, Value>>,
) -> Vec<Map<String, Value>> {
    let expected = match desired_table_schema(table_name) {
        Some(schema) => schema,
        None => return rows,
    };
    rows.into_iter()
        .map(|mut row| {
            if !row.contains_key("_doc_id") {
                if let Some(doc_id) = row
                    .get("doc_id")
                    .cloned()
                    .or_else(|| row.get("result_id").cloned())
                {
                    row.insert("_doc_id".into(), doc_id);
                }
            }
            expected
                .fields()
                .iter()
                .filter_map(|field| {
                    row.get(field.name())
                        .cloned()
                        .or_else(|| missing_known_column_default(table_name, field.name(), &row))
                        .map(|value| {
                            (
                                field.name().to_string(),
                                coerce_json_value(&value, field.data_type()),
                            )
                        })
                })
                .collect()
        })
        .collect()
}

fn normalize_rows_to_schema(
    rows: &[Map<String, Value>],
    schema: &Schema,
) -> Vec<Map<String, Value>> {
    rows.iter()
        .map(|row| {
            schema
                .fields()
                .iter()
                .filter_map(|field| {
                    row.get(field.name()).cloned().map(|value| {
                        (
                            field.name().to_string(),
                            coerce_json_value(&value, field.data_type()),
                        )
                    })
                })
                .collect()
        })
        .collect()
}

fn missing_known_column_default(
    table_name: &str,
    column: &str,
    row: &Map<String, Value>,
) -> Option<Value> {
    match (table_name, column) {
        ("crawler_pages", "doc_id") => row.get("_doc_id").cloned(),
        ("crawler_results", "_doc_id") => row.get("result_id").cloned(),
        ("crawler_job_urls", "_doc_id") => row
            .get("job_id")
            .and_then(Value::as_str)
            .zip(row.get("url_hash").and_then(Value::as_str))
            .map(|(job_id, url_hash)| Value::String(format!("{job_id}:{url_hash}"))),
        ("messaging_rooms", "_doc_id") => row.get("id").cloned(),
        ("messaging_rooms", "created_at") | ("messaging_rooms", "updated_at") => Some(
            row.get("updated_at")
                .cloned()
                .or_else(|| row.get("created_at").cloned())
                .unwrap_or_else(|| Value::String(String::new())),
        ),
        ("messaging_events", "_doc_id") => row.get("id").cloned(),
        ("messaging_events", "timestamp") => Some(
            row.get("timestamp")
                .cloned()
                .unwrap_or_else(|| Value::String(String::new())),
        ),
        ("messaging_room_timeline_current", "_doc_id") => row
            .get("room_id")
            .and_then(Value::as_str)
            .zip(row.get("id").and_then(Value::as_str))
            .map(|(room_id, id)| Value::String(format!("{room_id}:{id}"))),
        ("messaging_room_timeline_current", "timestamp")
        | ("messaging_room_timeline_current", "created_at")
        | ("messaging_room_timeline_current", "updated_at") => Some(
            row.get(column)
                .cloned()
                .or_else(|| row.get("timestamp").cloned())
                .unwrap_or_else(|| Value::String(String::new())),
        ),
        _ => None,
    }
}

fn coerce_json_value(value: &Value, dtype: &DataType) -> Value {
    match dtype {
        DataType::Utf8 => match value {
            Value::Null => Value::Null,
            Value::String(_) => value.clone(),
            _ => Value::String(match value {
                Value::Bool(v) => v.to_string(),
                Value::Number(v) => v.to_string(),
                _ => value.to_string(),
            }),
        },
        DataType::Int64 => match value {
            Value::Number(number) => number
                .as_i64()
                .map(|v| Value::Number(v.into()))
                .unwrap_or(Value::Null),
            Value::String(text) => text
                .trim()
                .parse::<i64>()
                .map(|v| Value::Number(v.into()))
                .unwrap_or(Value::Null),
            Value::Bool(v) => Value::Number((*v as i64).into()),
            _ => Value::Null,
        },
        _ => value.clone(),
    }
}

fn infer_data_type(value: &Value) -> DataType {
    match value {
        Value::Null => DataType::Null,
        Value::Bool(_) => DataType::Boolean,
        Value::Number(number) if number.as_i64().is_some() => DataType::Int64,
        Value::Number(_) => DataType::Float64,
        Value::Array(values) => {
            if values.iter().all(|value| value.as_f64().is_some()) {
                DataType::List(Arc::new(Field::new("item", DataType::Float32, true)))
            } else {
                DataType::Utf8
            }
        }
        _ => DataType::Utf8,
    }
}

fn merge_data_types(current: &DataType, next: &DataType) -> DataType {
    match (current, next) {
        (DataType::Null, dtype) | (dtype, DataType::Null) => dtype.clone(),
        (left, right) if left == right => left.clone(),
        (DataType::Int64, DataType::Float64) | (DataType::Float64, DataType::Int64) => {
            DataType::Float64
        }
        (DataType::Int32, DataType::Int64) | (DataType::Int64, DataType::Int32) => DataType::Int64,
        (DataType::Int32, DataType::Float64) | (DataType::Float64, DataType::Int32) => {
            DataType::Float64
        }
        (DataType::List(left), DataType::List(right)) if left.data_type() == right.data_type() => {
            DataType::List(left.clone())
        }
        _ => DataType::Utf8,
    }
}

fn json_rows_to_batch(
    schema: SchemaRef,
    rows: &[Map<String, Value>],
) -> Result<RecordBatch, Box<dyn std::error::Error + Send + Sync>> {
    compat_rows_to_batch(schema, rows)
}

fn encode_ipc_stream(
    batches: &[RecordBatch],
) -> Result<Vec<u8>, Box<dyn std::error::Error + Send + Sync>> {
    let mut out = Vec::new();
    let schema = batches
        .first()
        .map(|batch| batch.schema())
        .unwrap_or_else(|| Arc::new(Schema::empty()));
    let mut writer = StreamWriter::try_new(&mut out, &schema)?;
    for batch in batches {
        writer.write(batch)?;
    }
    writer.finish()?;
    Ok(out)
}

fn dataframe_sql(
    req: &DataFrameQueryRequest,
) -> Result<String, Box<dyn std::error::Error + Send + Sync>> {
    if let Some(sql) = &req.sql {
        return Ok(sql.clone());
    }

    let table = req.table.as_deref().ok_or("table or sql is required")?;
    let mut sql = format!("SELECT * FROM \"{table}\"");
    if let Some(filter) = &req.filter {
        if !filter.trim().is_empty() {
            sql.push_str(" WHERE ");
            sql.push_str(filter);
        }
    }
    if let Some(order_by) = &req.order_by {
        if !order_by.trim().is_empty() {
            sql.push_str(" ORDER BY ");
            sql.push_str(order_by);
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

fn dataframe_from_batches(
    table: String,
    limit: usize,
    batches: &[RecordBatch],
) -> Result<DataFrameResponse, Box<dyn std::error::Error + Send + Sync>> {
    let schema = batches
        .first()
        .map(|batch| batch.schema())
        .unwrap_or_else(|| Arc::new(Schema::empty()));

    let columns = schema
        .fields()
        .iter()
        .map(|field| DataFrameColumn {
            name: field.name().to_string(),
            dtype: format!("{:?}", field.data_type()),
        })
        .collect::<Vec<_>>();

    let rows = rows_from_batches(batches)?;

    Ok(DataFrameResponse {
        format: "nata.dataframe.v1",
        table,
        limit,
        row_count: rows.len(),
        columns,
        rows,
    })
}

fn rows_from_batches(
    batches: &[RecordBatch],
) -> Result<Vec<Map<String, Value>>, Box<dyn std::error::Error + Send + Sync>> {
    let mut rows = Vec::new();
    for batch in batches {
        let mut bytes = Vec::new();
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

fn sql_table_name(sql: &str) -> Option<String> {
    let upper = sql.to_uppercase();
    let from_pos = upper.find("FROM")?;
    let after_from = sql[from_pos + 4..].trim_start();
    let table = after_from
        .split_whitespace()
        .next()?
        .trim()
        .trim_end_matches(',')
        .trim_matches('"')
        .trim_matches('`');
    if table.is_empty() {
        None
    } else {
        Some(table.to_string())
    }
}

fn is_missing_known_column_error(error: &(dyn std::error::Error + Send + Sync)) -> bool {
    error.to_string().contains("No field named")
}

fn parse_sql_values(input: &str) -> Vec<String> {
    let mut out = Vec::new();
    let mut current = String::new();
    let mut in_string = false;
    let mut quote = '\0';
    for ch in input.chars() {
        match ch {
            '\'' | '"' => {
                if in_string && ch == quote {
                    in_string = false;
                } else if !in_string {
                    in_string = true;
                    quote = ch;
                } else {
                    current.push(ch);
                }
            }
            ',' if !in_string => {
                out.push(current.trim().to_string());
                current.clear();
            }
            _ => current.push(ch),
        }
    }
    if !current.trim().is_empty() {
        out.push(current.trim().to_string());
    }
    out
}

fn sql_value_to_json(value: &str) -> Value {
    let trimmed = value.trim().trim_end_matches(';');
    if trimmed.eq_ignore_ascii_case("null") {
        Value::Null
    } else if trimmed.eq_ignore_ascii_case("true") {
        Value::Bool(true)
    } else if trimmed.eq_ignore_ascii_case("false") {
        Value::Bool(false)
    } else if let Ok(parsed) = trimmed.parse::<i64>() {
        Value::Number(parsed.into())
    } else if let Ok(parsed) = trimmed.parse::<f64>() {
        serde_json::Number::from_f64(parsed)
            .map(Value::Number)
            .unwrap_or(Value::Null)
    } else {
        Value::String(trimmed.trim_matches('"').trim_matches('\'').to_string())
    }
}

#[cfg(test)]
mod tests {
    use std::env;
    use std::sync::Arc;

    use super::*;
    use object_store::ObjectStore;
    use object_store::memory::InMemory;
    use object_store::path::Path as ObjectPath;
    use std::fs;
    use tempfile::tempdir;

    use crate::config::StorageConfig;

    fn row(entries: &[(&str, Value)]) -> Map<String, Value> {
        entries
            .iter()
            .map(|(key, value)| ((*key).to_string(), value.clone()))
            .collect()
    }

    async fn open_test_context()
    -> Result<(tempfile::TempDir, Arc<TonboContext>), Box<dyn std::error::Error + Send + Sync>>
    {
        let dir = tempdir()?;
        let ctx = TonboContext::open(test_storage_config(dir.path())).await?;
        Ok((dir, ctx))
    }

    fn test_storage_config(path: &Path) -> StorageConfig {
        StorageConfig {
            lance_uri: path.to_string_lossy().to_string(),
            s3: None,
            direct_tables: Vec::new(),
            eager_table_registration: true,
            compact_fragment_threshold: 0,
            ..Default::default()
        }
    }

    #[test]
    fn infer_schema_merges_all_rows() {
        let rows = vec![
            row(&[
                ("_doc_id", Value::String("a".into())),
                ("count", Value::Number(1.into())),
            ]),
            row(&[
                ("_doc_id", Value::String("b".into())),
                (
                    "score",
                    serde_json::Number::from_f64(1.5)
                        .map(Value::Number)
                        .unwrap(),
                ),
            ]),
        ];

        let schema = infer_schema_from_rows(&rows);
        assert!(schema.field_with_name("_doc_id").is_ok());
        assert!(schema.field_with_name("count").is_ok());
        assert!(schema.field_with_name("score").is_ok());
    }

    #[test]
    fn known_crawler_pages_schema_is_fixed() {
        let rows = vec![row(&[
            ("_doc_id", Value::String("doc-1".into())),
            ("status", Value::String("200".into())),
            ("title", Value::String("Example".into())),
        ])];

        let schema = infer_schema_from_rows_for_table("crawler_pages", &rows);

        assert_eq!(
            schema.field_with_name("status").unwrap().data_type(),
            &DataType::Int64
        );
        assert!(schema.field_with_name("primary_image_cdn").is_ok());
    }

    #[test]
    fn normalize_rows_for_known_table_fills_doc_id_and_casts_types() {
        let rows = normalize_rows_for_known_table(
            "crawler_pages",
            vec![row(&[
                ("_doc_id", Value::String("doc-1".into())),
                ("status", Value::String("200".into())),
                ("size_bytes", Value::String("42".into())),
            ])],
        );

        assert_eq!(rows[0]["doc_id"], Value::String("doc-1".into()));
        assert_eq!(rows[0]["status"], Value::Number(200.into()));
        assert_eq!(rows[0]["size_bytes"], Value::Number(42.into()));
    }

    #[test]
    fn normalize_crawler_results_drops_non_dataset_columns() {
        let rows = normalize_rows_for_known_table(
            "crawler_results",
            vec![row(&[
                ("_doc_id", Value::String("r-1".into())),
                ("org_id", Value::String("anon".into())),
                ("user_id", Value::String("anon".into())),
                ("ogp_json", Value::String("{\"title\":\"x\"}".into())),
                ("http_status", Value::String("200".into())),
            ])],
        );

        assert!(!rows[0].contains_key("ogp_json"));
        assert_eq!(rows[0]["org_id"], Value::String("anon".into()));
        assert_eq!(rows[0]["user_id"], Value::String("anon".into()));
        assert_eq!(rows[0]["http_status"], Value::Number(200.into()));
    }

    #[test]
    fn normalize_crawler_jobs_drops_completed_at() {
        let rows = normalize_rows_for_known_table(
            "crawler_jobs",
            vec![row(&[
                ("_doc_id", Value::String("job-1".into())),
                ("job_id", Value::String("job-1".into())),
                ("status", Value::String("completed".into())),
                ("completed_at", Value::String("2026-03-12T14:00:00Z".into())),
            ])],
        );

        assert!(!rows[0].contains_key("completed_at"));
        assert_eq!(rows[0]["job_id"], Value::String("job-1".into()));
        assert_eq!(rows[0]["status"], Value::String("completed".into()));
    }

    #[test]
    fn crawler_results_is_append_only() {
        assert!(append_only_table("crawler_results"));
        assert!(!append_only_table("crawler_pages"));
    }

    #[test]
    fn retryable_storage_error_text_accepts_b2_503() {
        assert!(is_retryable_storage_error_text(
            "Generic S3 error: HTTP status server error (503) for url (...)"
        ));
        assert!(is_retryable_storage_error_text("service unavailable"));
        assert!(!is_retryable_storage_error_text("bucket not found"));
    }

    #[test]
    fn known_matrix_event_schema_is_fixed() {
        let rows = vec![row(&[
            ("id", Value::String("evt-1".into())),
            ("room_id", Value::String("room-1".into())),
            ("event_kind", Value::String("message".into())),
        ])];

        let schema = infer_schema_from_rows_for_table("messaging_events", &rows);

        assert!(schema.field_with_name("timestamp").is_ok());
        assert!(schema.field_with_name("actor_id").is_ok());
    }

    #[test]
    fn normalize_matrix_rows_fill_known_defaults() {
        let rooms = normalize_rows_for_known_table(
            "messaging_rooms",
            vec![row(&[
                ("id", Value::String("room-1".into())),
                ("name", Value::String("General".into())),
            ])],
        );
        assert_eq!(rooms[0]["_doc_id"], Value::String("room-1".into()));
        assert_eq!(rooms[0]["updated_at"], Value::String(String::new()));

        let events = normalize_rows_for_known_table(
            "messaging_events",
            vec![row(&[
                ("id", Value::String("evt-1".into())),
                ("room_id", Value::String("room-1".into())),
            ])],
        );
        assert_eq!(events[0]["_doc_id"], Value::String("evt-1".into()));
        assert_eq!(events[0]["timestamp"], Value::String(String::new()));
    }

    #[test]
    fn startup_reconcile_only_targets_known_matrix_tables() {
        assert!(is_startup_reconcile_table("messaging_events"));
        assert!(is_startup_reconcile_table("messaging_rooms"));
        assert!(!is_startup_reconcile_table("crawler_pages"));
    }

    #[test]
    fn dataset_already_exists_detection_matches_lance_error_text() {
        let error = std::io::Error::other("Dataset already exists: s3://bucket/table");
        assert!(is_dataset_already_exists(&error));
    }

    #[test]
    fn schema_missing_known_columns_detects_missing_timestamp() {
        let actual = Schema::new(vec![
            Field::new("_doc_id", DataType::Utf8, false),
            Field::new("id", DataType::Utf8, true),
            Field::new("room_id", DataType::Utf8, true),
        ]);
        let expected = desired_table_schema("messaging_events").unwrap();
        assert!(schema_missing_known_columns(&actual, expected.as_ref()));
    }

    #[test]
    fn parse_sql_values_keeps_strings_intact() {
        let values = parse_sql_values("1, 'hello, world', true, 3.14");
        assert_eq!(values, vec!["1", "hello, world", "true", "3.14"]);
    }

    #[tokio::test]
    async fn local_lance_roundtrip_via_dataframe_and_delete()
    -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let (_dir, ctx) = open_test_context().await?;
        ctx.upsert_rows(
            "people",
            "_doc_id",
            vec![
                row(&[
                    ("_doc_id", Value::String("p1".into())),
                    ("name", Value::String("Alice".into())),
                    ("age", Value::Number(30.into())),
                ]),
                row(&[
                    ("_doc_id", Value::String("p2".into())),
                    ("name", Value::String("Bob".into())),
                    ("age", Value::Number(41.into())),
                ]),
            ],
        )
        .await?;

        let frame = ctx
            .execute_dataframe_query(DataFrameQueryRequest {
                table: Some("people".into()),
                filter: Some("age >= 30".into()),
                limit: Some(10),
                offset: None,
                order_by: Some("_doc_id ASC".into()),
                sql: None,
            })
            .await?;
        assert_eq!(frame.row_count, 2);
        assert_eq!(frame.rows[0]["name"], Value::String("Alice".into()));

        ctx.delete_rows("people", "_doc_id = 'p2'").await?;
        let after_delete = ctx
            .execute_dataframe_query(DataFrameQueryRequest {
                table: Some("people".into()),
                filter: None,
                limit: Some(10),
                offset: None,
                order_by: Some("_doc_id ASC".into()),
                sql: None,
            })
            .await?;
        assert_eq!(after_delete.row_count, 1);
        assert_eq!(after_delete.rows[0]["_doc_id"], Value::String("p1".into()));
        Ok(())
    }

    #[tokio::test]
    async fn crawler_jobs_buffered_current_persists_and_appends_events()
    -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let dir = tempdir()?;
        let ctx = TonboContext::open(test_storage_config(dir.path())).await?;

        ctx.upsert_rows_with_keys(
            "crawler_jobs",
            vec!["_doc_id".to_string()],
            vec![row(&[
                ("_doc_id", Value::String("job-1".into())),
                ("job_id", Value::String("job-1".into())),
                ("status", Value::String("pending".into())),
                ("updated_at", Value::String("2026-03-13T01:00:00Z".into())),
            ])],
        )
        .await?;

        ctx.upsert_rows_with_keys(
            "crawler_jobs",
            vec!["_doc_id".to_string()],
            vec![row(&[
                ("_doc_id", Value::String("job-1".into())),
                ("job_id", Value::String("job-1".into())),
                ("status", Value::String("completed".into())),
                ("updated_at", Value::String("2026-03-13T01:00:02Z".into())),
            ])],
        )
        .await?;

        let jobs = ctx
            .collect_sql_pub("SELECT status FROM \"crawler_jobs\" WHERE job_id = 'job-1'")
            .await?;
        let job_rows = rows_from_batches(&jobs)?;
        assert_eq!(job_rows.len(), 1);
        assert_eq!(job_rows[0]["status"], Value::String("completed".into()));

        let events = ctx
            .collect_sql_pub("SELECT event_kind FROM \"crawler_job_events\" WHERE job_id = 'job-1'")
            .await?;
        let event_rows = rows_from_batches(&events)?;
        assert_eq!(event_rows.len(), 2);

        drop(ctx);

        let reopened = TonboContext::open(test_storage_config(dir.path())).await?;
        let reopened_jobs = reopened
            .collect_sql_pub("SELECT status FROM \"crawler_jobs\" WHERE job_id = 'job-1'")
            .await?;
        let reopened_rows = rows_from_batches(&reopened_jobs)?;
        assert_eq!(reopened_rows.len(), 1);
        assert_eq!(
            reopened_rows[0]["status"],
            Value::String("completed".into())
        );
        Ok(())
    }

    #[tokio::test]
    async fn crawler_job_urls_buffered_current_persists_and_appends_events()
    -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let dir = tempdir()?;
        let ctx = TonboContext::open(test_storage_config(dir.path())).await?;

        ctx.upsert_rows_with_keys(
            "crawler_job_urls",
            vec!["_doc_id".to_string()],
            vec![row(&[
                ("_doc_id", Value::String("job-1:url-1".into())),
                ("job_id", Value::String("job-1".into())),
                ("url_hash", Value::String("url-1".into())),
                ("url", Value::String("https://example.com/".into())),
                ("status", Value::String("queued".into())),
                ("leased_until", Value::Number(0.into())),
                ("attempts", Value::Number(0.into())),
            ])],
        )
        .await?;

        ctx.upsert_rows_with_keys(
            "crawler_job_urls",
            vec!["_doc_id".to_string()],
            vec![row(&[
                ("_doc_id", Value::String("job-1:url-1".into())),
                ("job_id", Value::String("job-1".into())),
                ("url_hash", Value::String("url-1".into())),
                ("url", Value::String("https://example.com/".into())),
                ("status", Value::String("visited".into())),
                ("leased_until", Value::Number(123_i64.into())),
                ("visited_at", Value::Number(456_i64.into())),
                ("attempts", Value::Number(1.into())),
            ])],
        )
        .await?;

        let urls = ctx
            .collect_sql_pub(
                "SELECT status, attempts FROM \"crawler_job_urls\" WHERE job_id = 'job-1'",
            )
            .await?;
        let url_rows = rows_from_batches(&urls)?;
        assert_eq!(url_rows.len(), 1);
        assert_eq!(url_rows[0]["status"], Value::String("visited".into()));
        assert_eq!(url_rows[0]["attempts"], Value::Number(1.into()));

        let events = ctx
            .collect_sql_pub(
                "SELECT event_kind FROM \"crawler_job_url_events\" WHERE job_id = 'job-1'",
            )
            .await?;
        let event_rows = rows_from_batches(&events)?;
        assert_eq!(event_rows.len(), 2);

        drop(ctx);

        let reopened = TonboContext::open(test_storage_config(dir.path())).await?;
        let reopened_urls = reopened
            .collect_sql_pub("SELECT status FROM \"crawler_job_urls\" WHERE job_id = 'job-1'")
            .await?;
        let reopened_rows = rows_from_batches(&reopened_urls)?;
        assert_eq!(reopened_rows.len(), 1);
        assert_eq!(reopened_rows[0]["status"], Value::String("visited".into()));
        Ok(())
    }

    #[tokio::test]
    async fn buffered_current_query_does_not_force_flush_until_background_tick()
    -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let dir = tempdir()?;
        let ctx = TonboContext::open(test_storage_config(dir.path())).await?;

        ctx.upsert_rows_with_keys(
            "crawler_job_urls",
            vec!["_doc_id".to_string()],
            vec![row(&[
                ("_doc_id", Value::String("job-1:url-1".into())),
                ("job_id", Value::String("job-1".into())),
                ("url_hash", Value::String("url-1".into())),
                ("url", Value::String("https://example.com/".into())),
                ("status", Value::String("queued".into())),
                ("leased_until", Value::Number(0.into())),
                ("attempts", Value::Number(0.into())),
            ])],
        )
        .await?;

        let query_rows = rows_from_batches(
            &ctx.collect_sql_pub("SELECT status FROM \"crawler_job_urls\" WHERE job_id = 'job-1'")
                .await?,
        )?;
        assert_eq!(query_rows.len(), 1);
        assert_eq!(query_rows[0]["status"], Value::String("queued".into()));

        {
            let state_arc = ctx
                .buffered_table_states
                .get("crawler_job_urls")
                .map(|e| e.clone())
                .expect("buffered state entry");
            let state = state_arc.lock().await;
            assert_eq!(state.dirty_count, 1);
            assert_eq!(state.pending_events.len(), 1);
        }

        let stored_before = ctx.load_rows_from_storage("crawler_job_urls").await?;
        assert!(stored_before.is_empty());

        assert_eq!(ctx.flush_dirty_buffered_tables().await?, 1);

        let stored_after = ctx.load_rows_from_storage("crawler_job_urls").await?;
        assert_eq!(stored_after.len(), 1);

        {
            let state_arc = ctx
                .buffered_table_states
                .get("crawler_job_urls")
                .map(|e| e.clone())
                .expect("buffered state entry");
            let state = state_arc.lock().await;
            assert_eq!(state.dirty_count, 0);
            assert!(state.pending_events.is_empty());
        }

        Ok(())
    }

    #[tokio::test]
    async fn execute_update_sql_supports_insert_and_delete()
    -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let (_dir, ctx) = open_test_context().await?;
        let inserted = ctx
            .execute_update_sql(
                "INSERT INTO people (_doc_id, name, age) VALUES ('p1', 'Alice', 30), ('p2', 'Bob', 41)",
            )
            .await?;
        assert_eq!(inserted, 2);

        let rows = ctx
            .execute_dataframe_query(DataFrameQueryRequest {
                table: Some("people".into()),
                filter: None,
                limit: Some(10),
                offset: None,
                order_by: Some("_doc_id ASC".into()),
                sql: None,
            })
            .await?;
        assert_eq!(rows.row_count, 2);

        let deleted = ctx
            .execute_update_sql("DELETE FROM people WHERE _doc_id = 'p1'")
            .await?;
        assert_eq!(deleted, 1);

        let after_delete = ctx
            .execute_dataframe_query(DataFrameQueryRequest {
                table: Some("people".into()),
                filter: None,
                limit: Some(10),
                offset: None,
                order_by: Some("_doc_id ASC".into()),
                sql: None,
            })
            .await?;
        assert_eq!(after_delete.row_count, 1);
        Ok(())
    }

    #[test]
    fn infer_upsert_key_columns_prefers_keyish_prefix() {
        assert_eq!(
            infer_upsert_key_columns(&[
                "server_name".into(),
                "key_id".into(),
                "public_key_base64".into(),
                "valid_until_ts".into(),
            ]),
            vec!["server_name".to_string(), "key_id".to_string()]
        );
        assert_eq!(
            infer_upsert_key_columns(
                &["room_id".into(), "member_id".into(), "power_level".into(),]
            ),
            vec!["room_id".to_string(), "member_id".to_string()]
        );
    }

    #[tokio::test]
    async fn execute_update_sql_upserts_without_doc_id()
    -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let (_dir, ctx) = open_test_context().await?;
        ctx.execute_update_sql(
            "INSERT INTO messaging_matrix_federation_keys (server_name, key_id, public_key_base64, valid_until_ts, fetched_at) VALUES ('matrix.etzhayyim.com', 'ed25519:a', 'key-v1', 1, 10)",
        )
        .await?;
        ctx.execute_update_sql(
            "INSERT OR REPLACE INTO messaging_matrix_federation_keys (server_name, key_id, public_key_base64, valid_until_ts, fetched_at) VALUES ('matrix.etzhayyim.com', 'ed25519:a', 'key-v2', 2, 20)",
        )
        .await?;

        let rows = ctx
            .execute_dataframe_query(DataFrameQueryRequest {
                table: Some("messaging_matrix_federation_keys".into()),
                filter: Some("server_name = 'matrix.etzhayyim.com'".into()),
                limit: Some(10),
                offset: None,
                order_by: Some("key_id ASC".into()),
                sql: None,
            })
            .await?;
        assert_eq!(rows.row_count, 1);
        assert_eq!(
            rows.rows[0]["public_key_base64"],
            Value::String("key-v2".into())
        );
        Ok(())
    }

    #[tokio::test]
    async fn execute_sql_returns_arrow_ipc_stream()
    -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let (_dir, ctx) = open_test_context().await?;
        ctx.execute_update_sql(
            "INSERT INTO people (_doc_id, name, age) VALUES ('p1', 'Alice', 30)",
        )
        .await?;

        let bytes = ctx.execute_sql("SELECT * FROM \"people\"").await?;
        assert!(!bytes.is_empty());
        Ok(())
    }

    #[tokio::test]
    async fn dataframe_query_sql_passthrough_works()
    -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let (_dir, ctx) = open_test_context().await?;
        ctx.execute_update_sql(
            "INSERT INTO people (_doc_id, name, age) VALUES ('p1', 'Alice', 30), ('p2', 'Bob', 41)",
        )
        .await?;

        let rows = ctx
            .execute_dataframe_query(DataFrameQueryRequest {
                table: None,
                filter: None,
                limit: None,
                offset: None,
                order_by: None,
                sql: Some("SELECT name FROM \"people\" WHERE age >= 40 ORDER BY _doc_id".into()),
            })
            .await?;
        assert_eq!(rows.row_count, 1);
        assert_eq!(rows.rows[0]["name"], Value::String("Bob".into()));
        Ok(())
    }

    #[tokio::test]
    async fn local_compat_table_is_registered()
    -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let dir = tempdir()?;
        let compat = serde_json::json!({
            "schema": {
                "fields": [
                    { "name": "_doc_id", "type": "utf8", "nullable": false },
                    { "name": "name", "type": "utf8", "nullable": true },
                    { "name": "age", "type": "int64", "nullable": true }
                ]
            },
            "rows": [
                { "_doc_id": "p1", "name": "Alice", "age": 30 },
                { "_doc_id": "p2", "name": "Bob", "age": 41 }
            ]
        });
        fs::write(
            dir.path().join("people.table.json"),
            serde_json::to_vec(&compat)?,
        )?;

        let ctx = TonboContext::open(StorageConfig {
            lance_uri: dir.path().to_string_lossy().to_string(),
            s3: None,
            direct_tables: Vec::new(),
            eager_table_registration: true, ..Default::default()
        })
        .await?;

        assert!(ctx.table_names().contains(&"people".to_string()));
        let rows = ctx
            .execute_dataframe_query(DataFrameQueryRequest {
                table: Some("people".into()),
                filter: Some("age >= 30".into()),
                limit: Some(10),
                offset: None,
                order_by: Some("_doc_id ASC".into()),
                sql: None,
            })
            .await?;
        assert_eq!(rows.row_count, 2);
        Ok(())
    }

    #[tokio::test]
    async fn unsupported_update_sql_returns_error()
    -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let (_dir, ctx) = open_test_context().await?;
        let err = ctx
            .execute_update_sql("UPDATE people SET name = 'Alice' WHERE _doc_id = 'p1'")
            .await
            .expect_err("unsupported sql should fail");
        assert!(err.to_string().contains("unsupported update SQL"));
        Ok(())
    }

    #[test]
    fn build_s3_store_params_sets_expected_flags() {
        let params = super::build_s3_store_params(
            &crate::config::S3Config {
                endpoint: "http://localhost:9000".into(),
                region: "local".into(),
                access_key: "access".into(),
                secret_key: "secret".into(),
                bucket: "bucket".into(),
                virtual_hosted_style: false,
                read_through_cache: Some(crate::config::ReadThroughCacheConfig {
                    capacity_bytes: 1024,
                    page_size_bytes: 128,
                }),
            },
            true,
        );

        let opts = params.storage_options.expect("storage options");
        assert_eq!(opts.get("region").map(String::as_str), Some("local"));
        assert_eq!(
            opts.get("virtual_hosted_style_request").map(String::as_str),
            Some("false")
        );
        assert_eq!(opts.get("allow_http").map(String::as_str), Some("true"));
        assert!(params.object_store_wrapper.is_some());
    }

    #[test]
    fn build_s3_store_params_without_cache_has_no_wrapper() {
        let params = super::build_s3_store_params(
            &crate::config::S3Config {
                endpoint: "https://example.invalid".into(),
                region: "test".into(),
                access_key: "access".into(),
                secret_key: "secret".into(),
                bucket: "bucket".into(),
                virtual_hosted_style: true,
                read_through_cache: None,
            },
            false,
        );
        assert!(params.object_store_wrapper.is_none());
    }

    #[tokio::test]
    async fn s3_uri_without_s3_config_is_rejected() {
        let result = TonboContext::open(StorageConfig {
            lance_uri: "s3://bucket/data".into(),
            s3: None,
            direct_tables: Vec::new(),
            eager_table_registration: true, ..Default::default()
        })
        .await;
        let err = match result {
            Ok(_) => panic!("s3 config should be required"),
            Err(err) => err,
        };
        assert!(err.to_string().contains("s3 config required"));
    }

    #[tokio::test]
    async fn ocra_wrapper_wraps_object_store_and_preserves_reads()
    -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let wrapper = OcraStoreWrapper {
            cache_config: crate::config::ReadThroughCacheConfig {
                capacity_bytes: 1024,
                page_size_bytes: 128,
            },
        };
        let store: Arc<dyn object_store::ObjectStore> = Arc::new(InMemory::new());
        let wrapped = wrapper.wrap(store.clone());
        let path = ObjectPath::from("people/p1.json");
        let payload = vec![b'a'; 256];

        store
            .put(&path, object_store::PutPayload::from(payload.clone()))
            .await?;
        let bytes = wrapped.get(&path).await?.bytes().await?;
        assert_eq!(bytes.as_ref(), payload.as_slice());
        Ok(())
    }

    #[tokio::test]
    async fn rename_object_store_prefix_moves_nested_objects()
    -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let store: Arc<dyn object_store::ObjectStore> = Arc::new(InMemory::new());
        let source_manifest = ObjectPath::from("root/books/_versions/1.manifest");
        let source_data = ObjectPath::from("root/books/data/part-1.lance");

        store
            .put(
                &source_manifest,
                object_store::PutPayload::from(br#"{"version":1}"#.to_vec()),
            )
            .await?;
        store
            .put(
                &source_data,
                object_store::PutPayload::from(b"payload".to_vec()),
            )
            .await?;

        rename_object_store_prefix(
            store.clone(),
            &ObjectPath::from("root/books"),
            &ObjectPath::from("root/renamed_books"),
        )
        .await?;

        let renamed_manifest = ObjectPath::from("root/renamed_books/_versions/1.manifest");
        let renamed_data = ObjectPath::from("root/renamed_books/data/part-1.lance");
        assert!(store.head(&renamed_manifest).await.is_ok());
        assert!(store.head(&renamed_data).await.is_ok());
        assert!(store.head(&source_manifest).await.is_err());
        assert!(store.head(&source_data).await.is_err());
        Ok(())
    }

    #[tokio::test]
    async fn direct_local_table_registration_skips_listing()
    -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let dir = tempdir()?;
        let dataset_dir = dir.path().join("people");
        let base = StorageConfig {
            lance_uri: dir.path().to_string_lossy().to_string(),
            s3: None,
            direct_tables: Vec::new(),
            eager_table_registration: true, ..Default::default()
        };
        let ctx = TonboContext::open(base.clone()).await?;
        ctx.upsert_rows(
            "people",
            "_doc_id",
            vec![row(&[
                ("_doc_id", Value::String("p1".into())),
                ("name", Value::String("Alice".into())),
            ])],
        )
        .await?;

        let direct = TonboContext::open(StorageConfig {
            lance_uri: "/unused".into(),
            s3: None,
            direct_tables: vec![crate::config::DirectTableConfig {
                name: "people".into(),
                uri: dataset_dir.to_string_lossy().to_string(),
            }],
            eager_table_registration: true, ..Default::default()
        })
        .await?;
        assert!(direct.table_names().contains(&"people".to_string()));
        Ok(())
    }

    #[tokio::test]
    async fn s3_context_exposes_registered_tables_when_b2_env_is_present()
    -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let endpoint = match env::var("NATA_S3_ENDPOINT") {
            Ok(value) if !value.trim().is_empty() => value,
            _ => return Ok(()),
        };
        let region = match env::var("NATA_S3_REGION") {
            Ok(value) if !value.trim().is_empty() => value,
            _ => return Ok(()),
        };
        let access_key = match env::var("NATA_S3_ACCESS_KEY") {
            Ok(value) if !value.trim().is_empty() => value,
            _ => return Ok(()),
        };
        let secret_key = match env::var("NATA_S3_SECRET_KEY") {
            Ok(value) if !value.trim().is_empty() => value,
            _ => return Ok(()),
        };
        let bucket = match env::var("NATA_S3_BUCKET") {
            Ok(value) if !value.trim().is_empty() => value,
            _ => return Ok(()),
        };
        let lance_uri = match env::var("NATA_LANCE_URI") {
            Ok(value) if !value.trim().is_empty() => value,
            _ => return Ok(()),
        };

        let ctx = TonboContext::open(StorageConfig {
            lance_uri,
            s3: Some(crate::config::S3Config {
                endpoint,
                region,
                access_key,
                secret_key,
                bucket,
                virtual_hosted_style: true,
                read_through_cache: None,
            }),
            direct_tables: Vec::new(),
            eager_table_registration: true, ..Default::default()
        })
        .await?;

        let tables = ctx.table_names();
        assert!(
            !tables.is_empty(),
            "expected registered tables, catalogs={:?}",
            ctx.catalog_names()
        );
        assert!(
            ctx.table_exists("crawler_pages")?,
            "crawler_pages missing from {:?}",
            tables
        );

        let show_tables = ctx.show_tables().await?;
        assert!(
            !show_tables.is_empty(),
            "SHOW TABLES should return at least one batch"
        );

        let rows = ctx
            .execute_dataframe_query(DataFrameQueryRequest {
                table: Some("crawler_pages".into()),
                filter: None,
                limit: Some(1),
                offset: None,
                order_by: None,
                sql: None,
            })
            .await?;
        assert!(rows.row_count <= 1);
        Ok(())
    }
}
