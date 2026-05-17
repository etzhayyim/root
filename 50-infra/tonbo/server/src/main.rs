use tokio::runtime::{Builder as RuntimeBuilder, Runtime};
use tonbo::{TonboConfig, TonboServer};
use tracing_subscriber::EnvFilter;

fn build_env_filter() -> Result<EnvFilter, Box<dyn std::error::Error + Send + Sync>> {
    Ok(EnvFilter::from_default_env().add_directive("tonbo=info".parse()?))
}

async fn build_server_from_env() -> Result<TonboServer, Box<dyn std::error::Error + Send + Sync>> {
    TonboServer::from_config(TonboConfig::from_env()).await
}

fn apply_runtime_env(config: &TonboConfig) {
    unsafe {
        std::env::set_var(
            "LANCE_IO_CORE_RESERVATION",
            config.runtime.lance_io_core_reservation.to_string(),
        );
        std::env::set_var(
            "LANCE_CPU_THREADS",
            config.runtime.lance_cpu_threads.to_string(),
        );
    }
}

fn build_runtime(
    config: &TonboConfig,
) -> Result<Runtime, Box<dyn std::error::Error + Send + Sync>> {
    Ok(RuntimeBuilder::new_multi_thread()
        .enable_all()
        .worker_threads(config.runtime.tokio_worker_threads)
        .max_blocking_threads(config.runtime.tokio_max_blocking_threads)
        .thread_name("tonbo")
        .build()?)
}

fn main() -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let config = TonboConfig::from_env();
    apply_runtime_env(&config);

    tracing_subscriber::fmt()
        .with_env_filter(build_env_filter()?)
        .json()
        .init();

    tracing::info!(
        tokio_worker_threads = config.runtime.tokio_worker_threads,
        tokio_max_blocking_threads = config.runtime.tokio_max_blocking_threads,
        lance_cpu_threads = config.runtime.lance_cpu_threads,
        lance_io_core_reservation = config.runtime.lance_io_core_reservation,
        "tonbo runtime tuned"
    );

    let runtime = build_runtime(&config)?;
    runtime.block_on(async move {
        let server = TonboServer::from_config(config).await?;
        server.run().await
    })
}

#[cfg(test)]
mod tests {
    use std::env;
    use std::sync::{Mutex, OnceLock};

    use tonbo::TonboConfig;

    use super::{apply_runtime_env, build_env_filter, build_runtime, build_server_from_env};

    const ENV_KEYS: &[&str] = &[
        "TONBO_LANCE_URI",
        "NATA_LANCE_URI",
        "LISTEN_ADDR",
        "FLIGHT_SQL_ADDR",
        "TONBO_S3_ENDPOINT",
        "TONBO_S3_REGION",
        "TONBO_S3_ACCESS_KEY",
        "TONBO_S3_SECRET_KEY",
        "TONBO_S3_BUCKET",
        "TONBO_READ_THROUGH_CACHE_BYTES",
        "TONBO_READ_THROUGH_CACHE_PAGE_SIZE",
        "NATA_S3_ENDPOINT",
        "NATA_S3_REGION",
        "NATA_S3_ACCESS_KEY",
        "NATA_S3_SECRET_KEY",
        "NATA_S3_BUCKET",
        "NATA_READ_THROUGH_CACHE_BYTES",
        "NATA_READ_THROUGH_CACHE_PAGE_SIZE",
        "TOKIO_WORKER_THREADS",
        "TONBO_TOKIO_MAX_BLOCKING_THREADS",
        "LANCE_CPU_THREADS",
        "LANCE_IO_CORE_RESERVATION",
    ];

    struct EnvGuard {
        saved: Vec<(String, Option<String>)>,
    }

    fn env_lock() -> &'static Mutex<()> {
        static LOCK: OnceLock<Mutex<()>> = OnceLock::new();
        LOCK.get_or_init(|| Mutex::new(()))
    }

    impl EnvGuard {
        fn capture() -> Self {
            Self {
                saved: ENV_KEYS
                    .iter()
                    .map(|key| ((*key).to_string(), env::var(key).ok()))
                    .collect(),
            }
        }
    }

    impl Drop for EnvGuard {
        fn drop(&mut self) {
            for (key, value) in &self.saved {
                match value {
                    Some(value) => unsafe { env::set_var(key, value) },
                    None => unsafe { env::remove_var(key) },
                }
            }
        }
    }

    fn clear_env() {
        for key in ENV_KEYS {
            unsafe { env::remove_var(key) };
        }
    }

    #[test]
    fn build_env_filter_includes_tonbo_directive()
    -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let filter = build_env_filter()?;
        let rendered = filter.to_string();
        assert!(rendered.contains("tonbo=info"));
        Ok(())
    }

    #[tokio::test]
    async fn build_server_from_env_uses_mockable_env_config()
    -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let _lock = env_lock().lock().expect("env lock");
        let _guard = EnvGuard::capture();
        clear_env();
        unsafe {
            env::set_var("TONBO_LANCE_URI", "/tmp/tonbo-main-test");
            env::set_var("LISTEN_ADDR", "127.0.0.1:28084");
            env::set_var("FLIGHT_SQL_ADDR", "127.0.0.1:25050");
        }

        let server = build_server_from_env().await?;
        assert_eq!(server.config().storage.lance_uri, "/tmp/tonbo-main-test");
        assert_eq!(server.config().server.http.addr, "127.0.0.1:28084");
        assert_eq!(server.config().server.flightsql.addr, "127.0.0.1:25050");
        Ok(())
    }

    #[test]
    fn apply_runtime_env_sets_lance_tuning() {
        let _lock = env_lock().lock().expect("env lock");
        let _guard = EnvGuard::capture();
        clear_env();
        let config = TonboConfig::from_env();
        let expected_lance_cpu_threads = config.runtime.lance_cpu_threads.to_string();
        let expected_lance_io_core_reservation =
            config.runtime.lance_io_core_reservation.to_string();

        apply_runtime_env(&config);

        assert_eq!(
            env::var("LANCE_CPU_THREADS").ok().as_deref(),
            Some(expected_lance_cpu_threads.as_str())
        );
        assert_eq!(
            env::var("LANCE_IO_CORE_RESERVATION").ok().as_deref(),
            Some(expected_lance_io_core_reservation.as_str())
        );
    }

    #[test]
    fn build_runtime_uses_runtime_config() -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let _lock = env_lock().lock().expect("env lock");
        let _guard = EnvGuard::capture();
        clear_env();
        unsafe {
            env::set_var("TOKIO_WORKER_THREADS", "2");
            env::set_var("TONBO_TOKIO_MAX_BLOCKING_THREADS", "40");
        }
        let config = TonboConfig::from_env();
        let runtime = build_runtime(&config)?;
        drop(runtime);
        assert_eq!(config.runtime.tokio_worker_threads, 2);
        assert_eq!(config.runtime.tokio_max_blocking_threads, 40);
        Ok(())
    }
}
