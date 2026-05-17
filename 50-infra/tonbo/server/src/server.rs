use std::sync::Arc;

use arrow_flight::flight_service_server::FlightServiceServer;
use axum::Router;
use tokio::signal;
use tokio::time::{Duration, interval, sleep};
use tonic::transport::Server as TonicServer;

use crate::config::TonboConfig;
use crate::context::TonboContext;
use crate::flightsql::TonboFlightSqlService;
use crate::http;

pub struct TonboServer {
    config: TonboConfig,
    ctx: Arc<TonboContext>,
}

impl TonboServer {
    pub async fn from_config(
        config: TonboConfig,
    ) -> Result<Self, Box<dyn std::error::Error + Send + Sync>> {
        let ctx = TonboContext::open(config.storage.clone()).await?;
        Ok(Self { config, ctx })
    }

    pub async fn run(self) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let grpc_addr = self.flightsql_addr()?;
        let http_listener = tokio::net::TcpListener::bind(self.http_addr()?).await?;
        let flush_ctx = self.ctx.clone();
        let flush_task = tokio::spawn(async move {
            let mut ticker = interval(Duration::from_secs(2));
            ticker.set_missed_tick_behavior(tokio::time::MissedTickBehavior::Skip);
            loop {
                ticker.tick().await;
                // jitter: spread flushes across 0-500ms to avoid thundering herd
                let jitter_ms = (std::time::SystemTime::now()
                    .duration_since(std::time::SystemTime::UNIX_EPOCH)
                    .unwrap_or_default()
                    .subsec_nanos() % 500) as u64;
                sleep(Duration::from_millis(jitter_ms)).await;
                if let Err(error) = flush_ctx.flush_dirty_buffered_tables().await {
                    tracing::warn!("tonbo: buffered flush tick failed: {error}");
                }
            }
        });

        let flight = self.flightsql_service();
        let grpc_server = TonicServer::builder()
            .add_service(FlightServiceServer::new(flight))
            .serve_with_shutdown(grpc_addr, shutdown_signal());

        let http_server = axum::serve(http_listener, self.http_router())
            .with_graceful_shutdown(shutdown_signal());

        tracing::info!(
            http_addr = %self.config.server.http.addr,
            flightsql_addr = %self.config.server.flightsql.addr,
            lance_uri = %self.config.storage.lance_uri,
            "tonbo server starting"
        );

        tokio::select! {
            result = http_server => {
                flush_task.abort();
                if let Err(error) = result {
                    tracing::error!("http server error: {error}");
                }
            }
            result = grpc_server => {
                flush_task.abort();
                if let Err(error) = result {
                    tracing::error!("grpc server error: {error}");
                }
            }
        }

        Ok(())
    }

    pub fn http_addr(&self) -> Result<std::net::SocketAddr, std::net::AddrParseError> {
        self.config.server.http.addr.parse()
    }

    pub fn flightsql_addr(&self) -> Result<std::net::SocketAddr, std::net::AddrParseError> {
        self.config.server.flightsql.addr.parse()
    }

    pub fn http_router(&self) -> Router {
        http::router(self.ctx.clone())
    }

    pub fn flightsql_service(&self) -> TonboFlightSqlService {
        TonboFlightSqlService::new(self.ctx.clone())
    }

    pub fn config(&self) -> &TonboConfig {
        &self.config
    }
}

async fn shutdown_signal() {
    let _ = signal::ctrl_c().await;
}

#[cfg(test)]
mod tests {
    use crate::config::{ListenConfig, RuntimeConfig, ServerConfig, StorageConfig, TonboConfig};

    use super::TonboServer;

    #[tokio::test]
    async fn from_config_exposes_parsed_addresses()
    -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let server = TonboServer::from_config(TonboConfig {
            storage: StorageConfig {
                lance_uri: "/tmp/tonbo-server-test".into(),
                s3: None,
                direct_tables: Vec::new(),
                eager_table_registration: true, ..Default::default()
            },
            server: ServerConfig {
                http: ListenConfig {
                    addr: "127.0.0.1:18084".into(),
                },
                flightsql: ListenConfig {
                    addr: "127.0.0.1:15050".into(),
                },
            },
            runtime: RuntimeConfig {
                tokio_worker_threads: 2,
                tokio_max_blocking_threads: 32,
                lance_cpu_threads: 1,
                lance_io_core_reservation: 1,
            },
        })
        .await?;

        assert_eq!(server.http_addr()?.to_string(), "127.0.0.1:18084");
        assert_eq!(server.flightsql_addr()?.to_string(), "127.0.0.1:15050");
        let _router = server.http_router();
        let _flight = server.flightsql_service();
        Ok(())
    }

    #[tokio::test]
    async fn invalid_addresses_are_rejected() -> Result<(), Box<dyn std::error::Error + Send + Sync>>
    {
        let server = TonboServer::from_config(TonboConfig {
            storage: StorageConfig {
                lance_uri: "/tmp/tonbo-server-test-invalid".into(),
                s3: None,
                direct_tables: Vec::new(),
                eager_table_registration: true, ..Default::default()
            },
            server: ServerConfig {
                http: ListenConfig {
                    addr: "not-an-addr".into(),
                },
                flightsql: ListenConfig {
                    addr: "also-not-an-addr".into(),
                },
            },
            runtime: RuntimeConfig {
                tokio_worker_threads: 2,
                tokio_max_blocking_threads: 32,
                lance_cpu_threads: 1,
                lance_io_core_reservation: 1,
            },
        })
        .await?;

        assert!(server.http_addr().is_err());
        assert!(server.flightsql_addr().is_err());
        Ok(())
    }
}
