use std::pin::Pin;
use std::sync::Arc;
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::SystemTime;

use arrow::ipc::writer::IpcWriteOptions;
use arrow_flight::encode::FlightDataEncoderBuilder;
use arrow_flight::flight_service_server::FlightService;
use arrow_flight::sql::server::{FlightSqlService, PeekableFlightDataStream};
use arrow_flight::sql::{
    Any, CommandStatementQuery, CommandStatementUpdate, SqlInfo, TicketStatementQuery,
};
use arrow_flight::{
    FlightDescriptor, FlightEndpoint, FlightInfo, HandshakeRequest, HandshakeResponse, Ticket,
};
use arrow::record_batch::RecordBatch;
use dashmap::DashMap;
use futures::TryStreamExt;
use futures::stream;
use prost::Message;
use tonic::{Request, Response, Status, Streaming};

use crate::context::TonboContext;

/// Marker prefix for tickets that reference the result cache.
/// First two bytes are 0xFF 0xFF — not valid UTF-8 SQL start, so detection
/// is unambiguous. Followed by 8 bytes of u64 ticket ID (big-endian).
/// Total new-format ticket size: 10 bytes.
const TICKET_MARKER: [u8; 2] = [0xFF, 0xFF];
/// Cached results are evicted after this many seconds.
const TICKET_TTL_SECS: u64 = 30;

struct CachedResult {
    batches: Vec<RecordBatch>,
    created_secs: u64,
}

pub struct TonboFlightSqlService {
    ctx: Arc<TonboContext>,
    /// Monotonically increasing ticket ID generator. No collision risk within a
    /// single process lifetime; tickets from prior process instances would have
    /// different IDs and fall back to the SQL re-execution path.
    ticket_seq: AtomicU64,
    /// One-shot cache: results are removed on DoGet. Stale entries are evicted
    /// lazily on each insert to bound memory usage.
    result_cache: Arc<DashMap<u64, CachedResult>>,
}

impl TonboFlightSqlService {
    pub fn new(ctx: Arc<TonboContext>) -> Self {
        Self {
            ctx,
            ticket_seq: AtomicU64::new(1),
            result_cache: Arc::new(DashMap::new()),
        }
    }

    fn next_ticket_id(&self) -> u64 {
        self.ticket_seq.fetch_add(1, Ordering::Relaxed)
    }

    fn now_secs() -> u64 {
        SystemTime::now()
            .duration_since(SystemTime::UNIX_EPOCH)
            .unwrap_or_default()
            .as_secs()
    }

    /// Evict cache entries older than TICKET_TTL_SECS.
    /// Called on every insert to prevent unbounded growth under sustained load.
    fn evict_stale(&self) {
        let threshold = Self::now_secs().saturating_sub(TICKET_TTL_SECS);
        self.result_cache
            .retain(|_, v| v.created_secs >= threshold);
    }

    /// Encode a ticket ID into the wire format understood by `decode_ticket`.
    fn encode_ticket(id: u64) -> Vec<u8> {
        let mut bytes = Vec::with_capacity(10);
        bytes.extend_from_slice(&TICKET_MARKER);
        bytes.extend_from_slice(&id.to_be_bytes());
        bytes
    }

    /// Decode a ticket. Returns `Some(id)` for new-format tickets, `None` for
    /// legacy SQL-bytes tickets (transparent fallback to SQL re-execution).
    fn decode_ticket(handle: &[u8]) -> Option<u64> {
        if handle.len() == 10 && handle[0] == TICKET_MARKER[0] && handle[1] == TICKET_MARKER[1] {
            let id_bytes: [u8; 8] = handle[2..10].try_into().ok()?;
            Some(u64::from_be_bytes(id_bytes))
        } else {
            None
        }
    }

    async fn execute_statement_update(&self, sql: &str) -> Result<i64, Status> {
        self.ctx
            .execute_update_sql(sql)
            .await
            .map_err(|error| Status::internal(format!("execute update: {error}")))
    }
}

#[tonic::async_trait]
impl FlightSqlService for TonboFlightSqlService {
    type FlightService = TonboFlightSqlService;

    async fn do_handshake(
        &self,
        _request: Request<Streaming<HandshakeRequest>>,
    ) -> Result<
        Response<Pin<Box<dyn futures::Stream<Item = Result<HandshakeResponse, Status>> + Send>>>,
        Status,
    > {
        let result = HandshakeResponse {
            protocol_version: 0,
            payload: Default::default(),
        };
        let output = stream::once(async { Ok(result) });
        Ok(Response::new(Box::pin(output)))
    }

    async fn get_flight_info_statement(
        &self,
        query: CommandStatementQuery,
        _request: Request<FlightDescriptor>,
    ) -> Result<Response<FlightInfo>, Status> {
        let sql = query.query.trim().to_string();
        if sql.is_empty() {
            return Err(Status::invalid_argument("empty SQL"));
        }

        // Execute the query once here. The results are cached so that
        // do_get_statement can serve them without re-executing.
        // Previously, both phases ran collect_sql_pub independently, causing
        // every Flight SQL read to hit B2 and DataFusion twice.
        let batches = self
            .ctx
            .collect_sql_pub(&sql)
            .await
            .map_err(|error| Status::internal(format!("query error: {error}")))?;

        let schema = if batches.is_empty() {
            Arc::new(arrow::datatypes::Schema::empty())
        } else {
            batches[0].schema()
        };

        let ticket_id = self.next_ticket_id();
        self.result_cache.insert(
            ticket_id,
            CachedResult {
                batches,
                created_secs: Self::now_secs(),
            },
        );
        self.evict_stale();

        let ticket_bytes = Self::encode_ticket(ticket_id);

        let ticket_query = TicketStatementQuery {
            statement_handle: ticket_bytes.into(),
        };
        let mut ticket_bytes_wire = Vec::new();
        let any = Any::pack(&ticket_query)
            .map_err(|error| Status::internal(format!("pack ticket: {error}")))?;
        any.encode(&mut ticket_bytes_wire)
            .map_err(|error| Status::internal(format!("encode ticket: {error}")))?;

        let endpoint = FlightEndpoint::new().with_ticket(Ticket::new(ticket_bytes_wire));
        let info = FlightInfo::new()
            .try_with_schema(&schema)
            .map_err(|error| Status::internal(format!("schema encode: {error}")))?
            .with_endpoint(endpoint);

        Ok(Response::new(info))
    }

    async fn do_get_statement(
        &self,
        ticket: TicketStatementQuery,
        _request: Request<Ticket>,
    ) -> Result<Response<<Self as FlightService>::DoGetStream>, Status> {
        let handle = ticket.statement_handle.as_ref();

        // New-format ticket: look up cached results from get_flight_info_statement.
        // The entry is removed (one-shot consumption) to bound memory usage.
        let batches = if let Some(ticket_id) = Self::decode_ticket(handle) {
            match self.result_cache.remove(&ticket_id) {
                Some((_, cached)) => cached.batches,
                None => {
                    // Cache miss: ticket expired or from a prior process instance.
                    // Return not_found so the client knows to retry.
                    return Err(Status::not_found(format!(
                        "flight ticket {ticket_id} not found or expired; retry the query"
                    )));
                }
            }
        } else {
            // Legacy path: ticket is the raw SQL bytes (e.g., direct test calls,
            // or clients constructed with the pre-cache ticket format).
            // Fall back to re-executing the query so behaviour is unchanged.
            let sql = String::from_utf8(handle.to_vec())
                .map_err(|error| Status::internal(format!("invalid utf8: {error}")))?;
            self.ctx
                .collect_sql_pub(&sql)
                .await
                .map_err(|error| Status::internal(format!("query error: {error}")))?
        };

        let schema = if batches.is_empty() {
            Arc::new(arrow::datatypes::Schema::empty())
        } else {
            batches[0].schema()
        };
        let batch_stream = futures::stream::iter(batches.into_iter().map(Ok));
        let flight_data_stream = FlightDataEncoderBuilder::new()
            .with_schema(schema)
            .with_options(IpcWriteOptions::default())
            .build(batch_stream)
            .map_err(|error| Status::internal(format!("encode error: {error}")));

        Ok(Response::new(Box::pin(flight_data_stream)))
    }

    async fn do_put_statement_update(
        &self,
        ticket: CommandStatementUpdate,
        _request: Request<PeekableFlightDataStream>,
    ) -> Result<i64, Status> {
        let sql = ticket.query.trim().to_string();
        self.execute_statement_update(&sql).await
    }

    async fn register_sql_info(&self, _id: i32, _result: &SqlInfo) {}
}

#[cfg(test)]
mod tests {
    use std::sync::Arc;

    use arrow_flight::FlightData;
    use arrow_flight::FlightDescriptor;
    use arrow_flight::sql::server::FlightSqlService;
    use arrow_flight::sql::{CommandStatementQuery, TicketStatementQuery};
    use futures::StreamExt;
    use tempfile::tempdir;
    use tonic::Request;

    use super::TonboFlightSqlService;
    use crate::config::StorageConfig;
    use crate::context::TonboContext;

    async fn seed_context()
    -> Result<(tempfile::TempDir, Arc<TonboContext>), Box<dyn std::error::Error + Send + Sync>>
    {
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
        Ok((dir, ctx))
    }

    #[tokio::test]
    async fn flightsql_statement_query_returns_ticket_and_stream()
    -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let (_dir, ctx) = seed_context().await?;
        let service = TonboFlightSqlService::new(ctx);
        let sql = "SELECT name FROM \"people\" ORDER BY _doc_id".to_string();

        let info = <TonboFlightSqlService as FlightSqlService>::get_flight_info_statement(
            &service,
            CommandStatementQuery {
                query: sql.clone(),
                transaction_id: None,
            },
            Request::new(FlightDescriptor::new_cmd(Vec::<u8>::new())),
        )
        .await?
        .into_inner();
        assert_eq!(info.endpoint.len(), 1);
        let ticket_endpoint = info.endpoint[0].ticket.as_ref().expect("ticket");

        // Decode the TicketStatementQuery from the endpoint to get the handle.
        use prost::Message as _;
        use arrow_flight::sql::Any;
        let any = Any::decode(ticket_endpoint.ticket.as_ref())?;
        let tq = any.unpack::<TicketStatementQuery>()?.expect("TicketStatementQuery");

        // Use the ticket from get_flight_info_statement — cache hit path.
        let response = <TonboFlightSqlService as FlightSqlService>::do_get_statement(
            &service,
            tq,
            Request::new(arrow_flight::Ticket::new(Vec::<u8>::new())),
        )
        .await?;
        let messages: Vec<Result<FlightData, tonic::Status>> =
            response.into_inner().collect().await;
        assert!(messages.iter().any(|item| item.is_ok()));
        Ok(())
    }

    #[tokio::test]
    async fn flightsql_legacy_ticket_re_executes_sql()
    -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let (_dir, ctx) = seed_context().await?;
        let service = TonboFlightSqlService::new(ctx);
        let sql = "SELECT name FROM \"people\" ORDER BY _doc_id".to_string();

        // Legacy path: pass raw SQL bytes as the ticket handle (no get_flight_info_statement).
        let response = <TonboFlightSqlService as FlightSqlService>::do_get_statement(
            &service,
            TicketStatementQuery {
                statement_handle: sql.into_bytes().into(),
            },
            Request::new(arrow_flight::Ticket::new(Vec::<u8>::new())),
        )
        .await?;
        let messages: Vec<Result<FlightData, tonic::Status>> =
            response.into_inner().collect().await;
        assert!(messages.iter().any(|item| item.is_ok()));
        Ok(())
    }

    #[tokio::test]
    async fn flightsql_rejects_empty_statement()
    -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let (_dir, ctx) = seed_context().await?;
        let service = TonboFlightSqlService::new(ctx);

        let result = <TonboFlightSqlService as FlightSqlService>::get_flight_info_statement(
            &service,
            CommandStatementQuery {
                query: "   ".into(),
                transaction_id: None,
            },
            Request::new(FlightDescriptor::new_cmd(Vec::<u8>::new())),
        )
        .await;
        assert!(result.is_err());
        Ok(())
    }

    #[tokio::test]
    async fn flightsql_update_executes_insert()
    -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let (_dir, ctx) = seed_context().await?;
        let service = TonboFlightSqlService::new(ctx.clone());

        let updated = service
            .execute_statement_update(
                "INSERT INTO people (_doc_id, name, age) VALUES ('p3', 'Cara', 27)",
            )
            .await?;
        assert_eq!(updated, 1);

        let rows = ctx
            .execute_dataframe_query(crate::context::DataFrameQueryRequest {
                table: Some("people".into()),
                filter: Some("_doc_id = 'p3'".into()),
                limit: Some(10),
                offset: None,
                order_by: None,
                sql: None,
            })
            .await?;
        assert_eq!(rows.row_count, 1);
        Ok(())
    }

    #[tokio::test]
    async fn flightsql_expired_ticket_returns_not_found()
    -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let (_dir, ctx) = seed_context().await?;
        let service = TonboFlightSqlService::new(ctx);

        // Manually construct a new-format ticket with a non-existent ID.
        let bogus_id: u64 = 999_999_999;
        let handle = TonboFlightSqlService::encode_ticket(bogus_id);

        let result = <TonboFlightSqlService as FlightSqlService>::do_get_statement(
            &service,
            TicketStatementQuery {
                statement_handle: handle.into(),
            },
            Request::new(arrow_flight::Ticket::new(Vec::<u8>::new())),
        )
        .await;
        assert!(result.is_err(), "expected error for unknown ticket");
        Ok(())
    }
}
