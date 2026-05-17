use std::env;

#[derive(Debug, Clone)]
pub struct TonboConfig {
    pub storage: StorageConfig,
    pub server: ServerConfig,
    pub runtime: RuntimeConfig,
}

#[derive(Debug, Clone)]
pub struct StorageConfig {
    pub lance_uri: String,
    pub s3: Option<S3Config>,
    pub direct_tables: Vec<DirectTableConfig>,
    pub eager_table_registration: bool,
    /// Table name prefixes that use the in-memory buffer + async B2 flush path.
    /// Comma-separated via TONBO_BUFFERED_TABLE_PREFIXES env var.
    /// Tables whose name starts with any of these prefixes bypass synchronous Lance/B2
    /// writes and instead accumulate in RAM, flushing every TONBO_BUFFER_FLUSH_SECS
    /// seconds or when TONBO_BUFFER_FLUSH_ROWS dirty rows have accumulated.
    pub buffered_table_prefixes: Vec<String>,
    /// Flush after this many dirty rows (default 25).
    pub buffer_flush_rows: usize,
    /// Flush after this many seconds since last flush (default 2).
    pub buffer_flush_secs: u64,
    /// Trigger a background compaction after a flush when the Lance fragment count for a
    /// buffered table exceeds this value. 0 = disabled. Recommended: 100.
    pub compact_fragment_threshold: usize,
}

impl Default for StorageConfig {
    fn default() -> Self {
        Self {
            lance_uri: String::new(),
            s3: None,
            direct_tables: Vec::new(),
            eager_table_registration: false,
            buffered_table_prefixes: Vec::new(),
            buffer_flush_rows: 25,
            buffer_flush_secs: 2,
            compact_fragment_threshold: 0,
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DirectTableConfig {
    pub name: String,
    pub uri: String,
}

#[derive(Debug, Clone)]
pub struct ServerConfig {
    pub http: ListenConfig,
    pub flightsql: ListenConfig,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RuntimeConfig {
    pub tokio_worker_threads: usize,
    pub tokio_max_blocking_threads: usize,
    pub lance_cpu_threads: usize,
    pub lance_io_core_reservation: usize,
}

#[derive(Debug, Clone)]
pub struct ListenConfig {
    pub addr: String,
}

#[derive(Debug, Clone)]
pub struct S3Config {
    pub endpoint: String,
    pub region: String,
    pub access_key: String,
    pub secret_key: String,
    pub bucket: String,
    pub virtual_hosted_style: bool,
    pub read_through_cache: Option<ReadThroughCacheConfig>,
}

#[derive(Debug, Clone)]
pub struct ReadThroughCacheConfig {
    pub capacity_bytes: usize,
    pub page_size_bytes: usize,
}

impl TonboConfig {
    pub fn from_env() -> Self {
        let lance_uri = env_string(&["TONBO_LANCE_URI", "NATA_LANCE_URI"])
            .unwrap_or_else(|| "/data/tonbo".to_string());
        let http_addr = env::var("LISTEN_ADDR").unwrap_or_else(|_| "0.0.0.0:8084".to_string());
        let flightsql_addr =
            env::var("FLIGHT_SQL_ADDR").unwrap_or_else(|_| "0.0.0.0:50050".to_string());

        Self {
            storage: StorageConfig {
                lance_uri,
                s3: s3_config_from_env(),
                direct_tables: direct_tables_from_env(),
                eager_table_registration: env_bool(&[
                    "TONBO_EAGER_TABLE_REGISTRATION",
                    "NATA_EAGER_TABLE_REGISTRATION",
                ])
                .unwrap_or(true),
                buffered_table_prefixes: env::var("TONBO_BUFFERED_TABLE_PREFIXES")
                    .unwrap_or_default()
                    .split(',')
                    .filter(|s| !s.trim().is_empty())
                    .map(|s| s.trim().to_string())
                    .collect(),
                buffer_flush_rows: env_usize("TONBO_BUFFER_FLUSH_ROWS").unwrap_or(25),
                buffer_flush_secs: env_usize("TONBO_BUFFER_FLUSH_SECS")
                    .unwrap_or(2)
                    .try_into()
                    .unwrap_or(2),
                compact_fragment_threshold: env_usize("TONBO_COMPACT_FRAGMENT_THRESHOLD").unwrap_or(0),
            },
            server: ServerConfig {
                http: ListenConfig { addr: http_addr },
                flightsql: ListenConfig {
                    addr: flightsql_addr,
                },
            },
            runtime: runtime_config_from_env(),
        }
    }
}

fn runtime_config_from_env() -> RuntimeConfig {
    let parallelism = std::thread::available_parallelism()
        .map(|value| value.get())
        .unwrap_or(2)
        .max(1);
    let lance_io_core_reservation = env_usize("LANCE_IO_CORE_RESERVATION")
        .unwrap_or_else(|| if parallelism <= 2 { 1 } else { 2 })
        .min(parallelism)
        .max(1);
    let lance_cpu_threads = env_usize("LANCE_CPU_THREADS")
        .unwrap_or_else(|| parallelism.saturating_sub(lance_io_core_reservation).max(1));
    let tokio_worker_threads = env_usize("TOKIO_WORKER_THREADS").unwrap_or(parallelism.max(1));
    let tokio_max_blocking_threads =
        env_usize("TONBO_TOKIO_MAX_BLOCKING_THREADS").unwrap_or((parallelism * 8).max(32));

    RuntimeConfig {
        tokio_worker_threads,
        tokio_max_blocking_threads,
        lance_cpu_threads: lance_cpu_threads.max(1),
        lance_io_core_reservation,
    }
}

fn env_usize(key: &str) -> Option<usize> {
    env::var(key)
        .ok()
        .and_then(|value| value.trim().parse::<usize>().ok())
        .filter(|value| *value > 0)
}

fn env_string(keys: &[&str]) -> Option<String> {
    keys.iter().find_map(|key| {
        env::var(key)
            .ok()
            .map(|value| value.trim().to_string())
            .filter(|value| !value.is_empty())
    })
}

fn env_bool(keys: &[&str]) -> Option<bool> {
    env_string(keys).and_then(|value| match value.to_ascii_lowercase().as_str() {
        "1" | "true" | "yes" | "on" => Some(true),
        "0" | "false" | "no" | "off" => Some(false),
        _ => None,
    })
}

fn env_usize_any(keys: &[&str]) -> Option<usize> {
    env_string(keys).and_then(|value| value.parse::<usize>().ok())
}

fn s3_config_from_env() -> Option<S3Config> {
    let endpoint = env_string(&[
        "TONBO_S3_ENDPOINT",
        "S3_ENDPOINT",
        "AWS_ENDPOINT_URL",
        "AWS_ENDPOINT",
        "NATA_S3_ENDPOINT",
    ])?;
    let access_key = env_string(&[
        "TONBO_S3_ACCESS_KEY",
        "S3_ACCESS_KEY",
        "AWS_ACCESS_KEY_ID",
        "NATA_S3_ACCESS_KEY",
    ])?;
    let secret_key = env_string(&[
        "TONBO_S3_SECRET_KEY",
        "S3_SECRET_KEY",
        "AWS_SECRET_ACCESS_KEY",
        "NATA_S3_SECRET_KEY",
    ])?;
    let bucket = env_string(&[
        "TONBO_S3_BUCKET",
        "S3_BUCKET",
        "AWS_BUCKET_NAME",
        "NATA_S3_BUCKET",
    ])?;
    let region = env_string(&[
        "TONBO_S3_REGION",
        "S3_REGION",
        "AWS_REGION",
        "AWS_DEFAULT_REGION",
        "NATA_S3_REGION",
    ])
    .unwrap_or_else(|| "us-west-004".to_string());
    let virtual_hosted_style = env_bool(&[
        "TONBO_S3_VIRTUAL_HOSTED_STYLE",
        "S3_VIRTUAL_HOSTED_STYLE",
        "AWS_VIRTUAL_HOSTED_STYLE_REQUEST",
        "NATA_S3_VIRTUAL_HOSTED_STYLE",
    ])
    .unwrap_or_else(|| !endpoint.contains(".backblazeb2.com"));
    let capacity_bytes = env_usize_any(&[
        "TONBO_READ_THROUGH_CACHE_BYTES",
        "NATA_READ_THROUGH_CACHE_BYTES",
    ])
    .unwrap_or(512 * 1024 * 1024);
    let page_size_bytes = env_usize_any(&[
        "TONBO_READ_THROUGH_CACHE_PAGE_SIZE",
        "NATA_READ_THROUGH_CACHE_PAGE_SIZE",
    ])
    .unwrap_or(256 * 1024);
    let read_through_cache = if capacity_bytes == 0 {
        None
    } else {
        Some(ReadThroughCacheConfig {
            capacity_bytes,
            page_size_bytes,
        })
    };

    Some(S3Config {
        endpoint,
        region,
        access_key,
        secret_key,
        bucket,
        virtual_hosted_style,
        read_through_cache,
    })
}

fn direct_tables_from_env() -> Vec<DirectTableConfig> {
    env_string(&["TONBO_LANCE_DIRECT_TABLES", "NATA_LANCE_DIRECT_TABLES"])
        .map(|value| {
            value
                .split(',')
                .filter_map(|entry| {
                    let trimmed = entry.trim();
                    let (name, uri) = trimmed.split_once('=')?;
                    let name = name.trim();
                    let uri = uri.trim();
                    if name.is_empty() || uri.is_empty() {
                        return None;
                    }
                    Some(DirectTableConfig {
                        name: name.to_string(),
                        uri: uri.to_string(),
                    })
                })
                .collect()
        })
        .unwrap_or_default()
}

#[cfg(test)]
mod tests {
    use std::sync::{Mutex, OnceLock};

    use super::*;

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
        "TONBO_S3_VIRTUAL_HOSTED_STYLE",
        "TONBO_READ_THROUGH_CACHE_BYTES",
        "TONBO_READ_THROUGH_CACHE_PAGE_SIZE",
        "TONBO_LANCE_DIRECT_TABLES",
        "S3_ENDPOINT",
        "S3_REGION",
        "S3_ACCESS_KEY",
        "S3_SECRET_KEY",
        "S3_BUCKET",
        "S3_VIRTUAL_HOSTED_STYLE",
        "AWS_ENDPOINT",
        "AWS_ENDPOINT_URL",
        "AWS_REGION",
        "AWS_DEFAULT_REGION",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_BUCKET_NAME",
        "AWS_VIRTUAL_HOSTED_STYLE_REQUEST",
        "NATA_S3_ENDPOINT",
        "NATA_S3_REGION",
        "NATA_S3_ACCESS_KEY",
        "NATA_S3_SECRET_KEY",
        "NATA_S3_BUCKET",
        "NATA_S3_VIRTUAL_HOSTED_STYLE",
        "NATA_READ_THROUGH_CACHE_BYTES",
        "NATA_READ_THROUGH_CACHE_PAGE_SIZE",
        "NATA_LANCE_DIRECT_TABLES",
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
    fn from_env_uses_defaults_without_s3() {
        let _lock = env_lock().lock().expect("env lock");
        let _guard = EnvGuard::capture();
        clear_env();

        let config = TonboConfig::from_env();
        assert_eq!(config.storage.lance_uri, "/data/tonbo");
        assert_eq!(config.server.http.addr, "0.0.0.0:8084");
        assert_eq!(config.server.flightsql.addr, "0.0.0.0:50050");
        assert!(config.storage.s3.is_none());
        assert!(config.storage.direct_tables.is_empty());
        assert!(config.runtime.tokio_worker_threads >= 1);
        assert!(config.runtime.tokio_max_blocking_threads >= 32);
        assert!(config.runtime.lance_cpu_threads >= 1);
        assert!(config.runtime.lance_io_core_reservation >= 1);
    }

    #[test]
    fn from_env_reads_all_overrides() {
        let _lock = env_lock().lock().expect("env lock");
        let _guard = EnvGuard::capture();
        clear_env();

        unsafe {
            env::set_var("TONBO_LANCE_URI", "/tmp/tonbo");
            env::set_var("LISTEN_ADDR", "127.0.0.1:18084");
            env::set_var("FLIGHT_SQL_ADDR", "127.0.0.1:15050");
            env::set_var("TONBO_S3_ENDPOINT", "http://localhost:9000");
            env::set_var("TONBO_S3_REGION", "local");
            env::set_var("TONBO_S3_ACCESS_KEY", "access");
            env::set_var("TONBO_S3_SECRET_KEY", "secret");
            env::set_var("TONBO_S3_BUCKET", "bucket");
            env::set_var("TONBO_S3_VIRTUAL_HOSTED_STYLE", "false");
            env::set_var("TONBO_READ_THROUGH_CACHE_BYTES", "1024");
            env::set_var("TONBO_READ_THROUGH_CACHE_PAGE_SIZE", "128");
            env::set_var(
                "TONBO_LANCE_DIRECT_TABLES",
                "people=s3://bucket/data/people.lance,events=s3://bucket/data/events",
            );
            env::set_var("TOKIO_WORKER_THREADS", "3");
            env::set_var("TONBO_TOKIO_MAX_BLOCKING_THREADS", "48");
            env::set_var("LANCE_CPU_THREADS", "2");
            env::set_var("LANCE_IO_CORE_RESERVATION", "1");
        }

        let config = TonboConfig::from_env();
        let s3 = config.storage.s3.expect("s3 config");
        assert_eq!(config.storage.lance_uri, "/tmp/tonbo");
        assert_eq!(config.server.http.addr, "127.0.0.1:18084");
        assert_eq!(config.server.flightsql.addr, "127.0.0.1:15050");
        assert_eq!(s3.endpoint, "http://localhost:9000");
        assert_eq!(s3.region, "local");
        assert_eq!(s3.bucket, "bucket");
        assert!(!s3.virtual_hosted_style);
        assert_eq!(
            config.runtime,
            RuntimeConfig {
                tokio_worker_threads: 3,
                tokio_max_blocking_threads: 48,
                lance_cpu_threads: 2,
                lance_io_core_reservation: 1,
            }
        );
        let cache = s3.read_through_cache.expect("cache config");
        assert_eq!(cache.capacity_bytes, 1024);
        assert_eq!(cache.page_size_bytes, 128);
        assert_eq!(
            config.storage.direct_tables,
            vec![
                DirectTableConfig {
                    name: "people".into(),
                    uri: "s3://bucket/data/people.lance".into()
                },
                DirectTableConfig {
                    name: "events".into(),
                    uri: "s3://bucket/data/events".into()
                }
            ]
        );
    }

    #[test]
    fn from_env_disables_read_through_cache_when_zero() {
        let _lock = env_lock().lock().expect("env lock");
        let _guard = EnvGuard::capture();
        clear_env();

        unsafe {
            env::set_var("TONBO_S3_ENDPOINT", "http://localhost:9000");
            env::set_var("TONBO_S3_REGION", "local");
            env::set_var("TONBO_S3_ACCESS_KEY", "access");
            env::set_var("TONBO_S3_SECRET_KEY", "secret");
            env::set_var("TONBO_S3_BUCKET", "bucket");
            env::set_var("TONBO_READ_THROUGH_CACHE_BYTES", "0");
        }

        let config = TonboConfig::from_env();
        assert!(config.storage.s3.expect("s3").read_through_cache.is_none());
    }

    #[test]
    fn from_env_defaults_to_path_style_for_backblaze() {
        let _lock = env_lock().lock().expect("env lock");
        let _guard = EnvGuard::capture();
        clear_env();

        unsafe {
            env::set_var(
                "TONBO_S3_ENDPOINT",
                "https://s3.us-west-004.backblazeb2.com",
            );
            env::set_var("TONBO_S3_REGION", "us-west-004");
            env::set_var("TONBO_S3_ACCESS_KEY", "access");
            env::set_var("TONBO_S3_SECRET_KEY", "secret");
            env::set_var("TONBO_S3_BUCKET", "bucket");
        }

        let config = TonboConfig::from_env();
        assert!(!config.storage.s3.expect("s3").virtual_hosted_style);
    }

    #[test]
    fn from_env_chooses_safe_lance_defaults_on_small_hosts() {
        let _lock = env_lock().lock().expect("env lock");
        let _guard = EnvGuard::capture();
        clear_env();

        let config = TonboConfig::from_env();
        assert!(config.runtime.lance_io_core_reservation <= 2);
        assert!(config.runtime.lance_cpu_threads >= 1);
    }
}
