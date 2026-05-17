use once_cell::sync::Lazy;
use prometheus::{
    Encoder, HistogramOpts, HistogramVec, IntCounterVec, IntGauge, Opts, Registry, TextEncoder,
};

// ── Private per-process registry ────────────────────────────────────────────

static REGISTRY: Lazy<Registry> = Lazy::new(Registry::new);

// ── HTTP ────────────────────────────────────────────────────────────────────

pub static HTTP_REQUESTS: Lazy<IntCounterVec> = Lazy::new(|| {
    let m = IntCounterVec::new(
        Opts::new(
            "tonbo_http_requests_total",
            "Total HTTP requests by method, route template, and status code",
        ),
        &["method", "route", "status"],
    )
    .unwrap();
    REGISTRY.register(Box::new(m.clone())).unwrap();
    m
});

pub static HTTP_DURATION: Lazy<HistogramVec> = Lazy::new(|| {
    let m = HistogramVec::new(
        HistogramOpts::new(
            "tonbo_http_request_duration_seconds",
            "HTTP request latency by method and route template",
        )
        .buckets(vec![
            0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0,
        ]),
        &["method", "route"],
    )
    .unwrap();
    REGISTRY.register(Box::new(m.clone())).unwrap();
    m
});

// ── Queries ─────────────────────────────────────────────────────────────────

pub static ACTIVE_QUERIES: Lazy<IntGauge> = Lazy::new(|| {
    let m = IntGauge::new(
        "tonbo_active_queries",
        "Number of DataFusion queries currently executing",
    )
    .unwrap();
    REGISTRY.register(Box::new(m.clone())).unwrap();
    m
});

pub static QUERY_DURATION: Lazy<HistogramVec> = Lazy::new(|| {
    let m = HistogramVec::new(
        HistogramOpts::new(
            "tonbo_query_duration_seconds",
            "DataFusion query execution latency",
        )
        .buckets(vec![
            0.001, 0.005, 0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0,
        ]),
        &["kind"], // "sql" | "update"
    )
    .unwrap();
    REGISTRY.register(Box::new(m.clone())).unwrap();
    m
});

pub static QUERY_ERRORS: Lazy<IntCounterVec> = Lazy::new(|| {
    let m = IntCounterVec::new(
        Opts::new("tonbo_query_errors_total", "Total query errors"),
        &["kind"],
    )
    .unwrap();
    REGISTRY.register(Box::new(m.clone())).unwrap();
    m
});

// ── Flush ────────────────────────────────────────────────────────────────────

pub static FLUSH_TOTAL: Lazy<IntCounterVec> = Lazy::new(|| {
    let m = IntCounterVec::new(
        Opts::new(
            "tonbo_flush_total",
            "Total buffered-table flush operations",
        ),
        &["result"], // "ok" | "error"
    )
    .unwrap();
    REGISTRY.register(Box::new(m.clone())).unwrap();
    m
});

pub static FLUSH_DURATION: Lazy<HistogramVec> = Lazy::new(|| {
    let m = HistogramVec::new(
        HistogramOpts::new(
            "tonbo_flush_duration_seconds",
            "Duration of a single buffered-table flush to S3",
        )
        .buckets(vec![0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0]),
        &["table"],
    )
    .unwrap();
    REGISTRY.register(Box::new(m.clone())).unwrap();
    m
});

// ── Helpers ──────────────────────────────────────────────────────────────────

/// Render all registered metrics in Prometheus text exposition format.
pub fn gather_text() -> String {
    let encoder = TextEncoder::new();
    let mf = REGISTRY.gather();
    let mut buf = Vec::new();
    encoder.encode(&mf, &mut buf).unwrap_or_default();
    String::from_utf8_lossy(&buf).into_owned()
}

/// RAII guard: increments `tonbo_active_queries` on creation, decrements on drop.
pub struct ActiveQueryGuard;

impl ActiveQueryGuard {
    pub fn new() -> Self {
        ACTIVE_QUERIES.inc();
        Self
    }
}

impl Drop for ActiveQueryGuard {
    fn drop(&mut self) {
        ACTIVE_QUERIES.dec();
    }
}
