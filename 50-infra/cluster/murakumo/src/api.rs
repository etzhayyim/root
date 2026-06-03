use reqwest::Client;
use serde::{de::DeserializeOwned, Serialize};
use std::time::Duration;

use crate::config::env_or;
use crate::models::*;

const DEFAULT_MURAKUMO_APP_ENDPOINT: &str = "https://murakumo.etzhayyim.com";

/// Shared HTTP client with configurable timeout.
pub fn http_client() -> Client {
    let timeout = connect_timeout();
    Client::builder()
        .timeout(timeout)
        .build()
        .unwrap_or_else(|_| Client::new())
}

fn connect_timeout() -> Duration {
    let raw = env_or("ETZHAYYIM_MURAKUMO_HTTP_TIMEOUT", "90s");
    parse_duration(&raw).unwrap_or(Duration::from_secs(90))
}

fn parse_duration(s: &str) -> Option<Duration> {
    let s = s.trim();
    if s.ends_with('s') {
        s.trim_end_matches('s').parse::<u64>().ok().map(Duration::from_secs)
    } else if s.ends_with('m') {
        s.trim_end_matches('m').parse::<u64>().ok().map(|m| Duration::from_secs(m * 60))
    } else {
        s.parse::<u64>().ok().map(Duration::from_secs)
    }
}

fn is_query_method(method: &str) -> bool {
    matches!(method.trim(), "GetWorkerStatus" | "GetDistillationJobStatus")
}

/// Route murakumo reads to QueryService and writes to CommandService via XRPC.
pub async fn connect_call<Req: Serialize, Resp: DeserializeOwned>(
    client: &Client,
    endpoint: &str,
    method: &str,
    req: &Req,
) -> Result<Resp, String> {
    if is_query_method(method) {
        murakumo_service_call(client, endpoint, "MurakumoQueryService", method, req).await
    } else {
        murakumo_service_call(client, endpoint, "MurakumoCommandService", method, req).await
    }
}

async fn murakumo_service_call<Req: Serialize, Resp: DeserializeOwned>(
    client: &Client,
    endpoint: &str,
    service: &str,
    method: &str,
    req: &Req,
) -> Result<Resp, String> {
    let url = format!("{}/xrpc/etzhayyim.murakumo.v1.{}/{}", endpoint, service, method);

    let resp = client
        .post(&url)
        .header("Content-Type", "application/json")
        .header("Connect-Protocol-Version", "1")
        .json(req)
        .send()
        .await
        .map_err(|e| format!("api error: method={} err={}", method, e))?;

    let status = resp.status();
    let body = resp
        .text()
        .await
        .map_err(|e| format!("read response body: {}", e))?;

    if status.as_u16() >= 400 {
        return Err(format!("HTTP {}: {}", status, body));
    }

    if body.trim().is_empty() {
        // Try to deserialize from empty JSON object for default-constructible types
        serde_json::from_str("{}").map_err(|e| format!("decode {} response from empty: {}", method, e))
    } else {
        serde_json::from_str(&body)
            .map_err(|e| format!("decode {} response: {}", method, e))
    }
}

/// Fetch the model catalog from the control plane.
pub async fn fetch_catalog(client: &Client, endpoint: &str) -> Result<CatalogResponse, String> {
    let url = format!("{}/api/models/catalog", endpoint);
    let resp = client.get(&url).send().await.map_err(|e| e.to_string())?;
    let body = resp.text().await.map_err(|e| e.to_string())?;
    serde_json::from_str(&body).map_err(|e| format!("decode catalog: {}", e))
}

/// Get a presigned upload URL for a model.
pub async fn get_upload_url(client: &Client, endpoint: &str, model_id: &str) -> Result<UploadUrlResp, String> {
    let url = format!("{}/api/models/upload", endpoint);
    let body = serde_json::json!({ "model_id": model_id });
    let resp = client.post(&url).json(&body).send().await.map_err(|e| e.to_string())?;
    let text = resp.text().await.map_err(|e| e.to_string())?;
    serde_json::from_str(&text).map_err(|e| format!("decode upload url: {}", e))
}

/// Fetch health status from the control plane.
pub async fn fetch_health(client: &Client, endpoint: &str) -> Result<(u16, String), String> {
    let url = format!("{}/health", endpoint);
    let resp = client.get(&url).send().await.map_err(|e| e.to_string())?;
    let status = resp.status().as_u16();
    let body = resp.text().await.map_err(|e| e.to_string())?;
    Ok((status, body))
}

/// Register a model in the catalog.
pub async fn register_model(client: &Client, endpoint: &str, model_id: &str, size_bytes: i64) {
    let req = serde_json::json!({
        "model_id": model_id,
        "size_bytes": size_bytes,
    });
    let _: Result<serde_json::Value, _> = connect_call(client, endpoint, "RegisterModel", &req).await;
}

/// Call an App command via XRPC.
pub async fn magatama_app_call<Req: Serialize, Resp: DeserializeOwned>(
    client: &Client,
    command: &str,
    args: &Req,
) -> Result<Resp, String> {
    let endpoint = env_or("ETZHAYYIM_MURAKUMO_APP", DEFAULT_MURAKUMO_APP_ENDPOINT);
    let url = format!(
        "{}/xrpc/etzhayyim.murakumo.v1.MurakumoCommandService/{}",
        endpoint, command
    );

    let resp = client
        .post(&url)
        .header("Content-Type", "application/json")
        .header("Connect-Protocol-Version", "1")
        .json(args)
        .send()
        .await
        .map_err(|e| format!("magatamaAppCall {}: {}", command, e))?;

    let status = resp.status();
    let body = resp.text().await.map_err(|e| e.to_string())?;

    if status.as_u16() >= 400 {
        return Err(format!("magatamaAppCall {} HTTP {}: {}", command, status, body));
    }

    if body.trim().is_empty() {
        serde_json::from_str("{}").map_err(|e| e.to_string())
    } else {
        serde_json::from_str(&body).map_err(|e| format!("magatamaAppCall {} decode: {}", command, e))
    }
}

/// Cloud distillation HTTP call.
pub async fn cloud_distill_call<Req: Serialize, Resp: DeserializeOwned>(
    client: &Client,
    endpoint: &str,
    path: &str,
    req: &Req,
) -> Result<Resp, String> {
    let url = format!("{}{}", endpoint, path);
    let resp = client
        .post(&url)
        .header("Content-Type", "application/json")
        .json(req)
        .send()
        .await
        .map_err(|e| format!("cloud distill {}: {}", path, e))?;

    let status = resp.status();
    let body = resp.text().await.map_err(|e| e.to_string())?;

    if status.as_u16() >= 400 {
        return Err(format!("cloud distill {} HTTP {}: {}", path, status, clip_for_log(&body, 200)));
    }

    if body.trim().is_empty() {
        serde_json::from_str("{}").map_err(|e| e.to_string())
    } else {
        serde_json::from_str(&body).map_err(|e| format!("cloud distill {} decode: {}", path, e))
    }
}

pub fn clip_for_log(s: &str, limit: usize) -> String {
    let s = s.trim();
    if s.len() <= limit {
        s.to_string()
    } else {
        format!("{}...(truncated)", &s[..limit])
    }
}
