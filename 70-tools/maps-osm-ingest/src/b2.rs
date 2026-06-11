//! Backblaze B2 native API v3 client (download + existence check).
//!
//! Only the operations needed by the PBF cache are implemented:
//!   - `authorize` — POST /b2api/v3/b2_authorize_account
//!   - `exists`    — POST /b2api/v3/b2_list_file_names (1 result)
//!   - `download`  — GET  /b2api/v3/b2_download_file_by_name
//!
//! Upload is intentionally not implemented here; PBF files are 800MB–2.4GB and
//! require B2 Large File (multipart) upload.  A human operator uploads the PBF
//! to B2 once; the tool cache-hits from then on.
//!
//! B2 v3 auth response shape (verified 2026-05-08):
//! ```json
//! { "apiInfo": { "storageApi": { "apiUrl": "...", "downloadUrl": "...",
//!                                "bucketId": "...", "bucketName": "..." } },
//!   "authorizationToken": "..." }
//! ```
//! This differs from the v2 flat shape; we deserialize the nested form.

use anyhow::{bail, Context, Result};
use base64::Engine as _;
use bytes::Bytes;
use serde::Deserialize;
use sha1::{Digest, Sha1};
use tracing::info;

// ── auth response (B2 native API v3) ─────────────────────────────────────────

#[derive(Deserialize)]
struct AuthResponse {
    #[serde(rename = "authorizationToken")]
    authorization_token: String,
    #[serde(rename = "apiInfo")]
    api_info: ApiInfo,
}

#[derive(Deserialize)]
struct ApiInfo {
    #[serde(rename = "storageApi")]
    storage_api: StorageApi,
}

#[derive(Deserialize)]
struct StorageApi {
    #[serde(rename = "apiUrl")]
    api_url: String,
    #[serde(rename = "downloadUrl")]
    download_url: String,
    /// Non-empty only when the application key is bucket-scoped.
    #[serde(rename = "bucketId", default)]
    bucket_id: String,
    /// Non-empty only when the application key is bucket-scoped.
    #[serde(rename = "bucketName", default)]
    bucket_name: String,
}

// ── list-file-names response (minimal) ───────────────────────────────────────

#[derive(Deserialize)]
struct ListFileNamesResponse {
    files: Vec<serde_json::Value>,
}

// ── upload-url response ───────────────────────────────────────────────────────

#[allow(dead_code)]
#[derive(Deserialize)]
struct UploadUrlResponse {
    #[serde(rename = "uploadUrl")]
    upload_url: String,
    #[serde(rename = "authorizationToken")]
    authorization_token: String,
}

// ── public client ─────────────────────────────────────────────────────────────

pub struct B2Client {
    http: reqwest::Client,
    auth_token: String,
    api_url: String,
    download_url: String,
    bucket_id: String,
    pub bucket_name: String,
}

impl B2Client {
    /// Authorize via POST /b2api/v3/b2_authorize_account.
    ///
    /// `key_id`  – B2 application key ID
    /// `app_key` – B2 application key
    /// `bucket_name` – bucket name (required when key_id is account-master and
    ///   `allowed.bucketName` is empty; bucket-scoped keys fill it from the
    ///   auth response automatically).
    pub async fn authorize(key_id: &str, app_key: &str, bucket_name: &str) -> Result<Self> {
        let http = reqwest::Client::builder()
            .timeout(std::time::Duration::from_secs(30))
            .build()
            .context("build reqwest client")?;

        // Basic auth = base64("{key_id}:{app_key}")
        let creds = base64::engine::general_purpose::STANDARD
            .encode(format!("{key_id}:{app_key}"));

        let resp = http
            .post("https://api.backblazeb2.com/b2api/v3/b2_authorize_account")
            .header("Authorization", format!("Basic {creds}"))
            .send()
            .await
            .context("b2_authorize_account request")?;

        if !resp.status().is_success() {
            let status = resp.status();
            let body = resp.text().await.unwrap_or_default();
            bail!("b2_authorize_account HTTP {status}: {body}");
        }

        let auth: AuthResponse = resp.json().await.context("parse auth response")?;
        let sa = auth.api_info.storage_api;

        // Prefer bucket_name from auth response (bucket-scoped key); fall back
        // to the caller-supplied name (account-master key).
        let effective_bucket_name = if sa.bucket_name.is_empty() {
            bucket_name.to_string()
        } else {
            sa.bucket_name.clone()
        };

        if effective_bucket_name.is_empty() {
            bail!("b2_authorize_account: bucket name is empty and --b2-bucket-name not set");
        }

        info!(
            api_url = %sa.api_url,
            download_url = %sa.download_url,
            bucket_name = %effective_bucket_name,
            "B2 authorized"
        );

        Ok(Self {
            http,
            auth_token: auth.authorization_token,
            api_url: sa.api_url,
            download_url: sa.download_url,
            bucket_id: sa.bucket_id,
            bucket_name: effective_bucket_name,
        })
    }

    /// Return true if `key` exists in the bucket (one-file list check).
    pub async fn exists(&self, key: &str) -> Result<bool> {
        let url = format!("{}/b2api/v3/b2_list_file_names", self.api_url);
        let body = serde_json::json!({
            "bucketId": self.bucket_id,
            "prefix": key,
            "maxFileCount": 1,
        });

        let resp = self
            .http
            .post(&url)
            .header("Authorization", &self.auth_token)
            .json(&body)
            .send()
            .await
            .context("b2_list_file_names request")?;

        if !resp.status().is_success() {
            let status = resp.status();
            let text = resp.text().await.unwrap_or_default();
            bail!("b2_list_file_names HTTP {status}: {text}");
        }

        let list: ListFileNamesResponse = resp.json().await.context("parse list response")?;
        // A file exists if at least one entry has a fileName that starts with our key
        let found = list.files.iter().any(|f| {
            f.get("fileName")
                .and_then(|v| v.as_str())
                .map(|n| n == key)
                .unwrap_or(false)
        });
        Ok(found)
    }

    /// Download `key` from the bucket.  Returns `None` on 404.
    ///
    /// For large files (PBFs) the caller should stream to disk rather than
    /// holding the full body in memory.  We return `Bytes` here for
    /// simplicity; the PBF cache check at job startup handles the allocation.
    pub async fn download(&self, key: &str) -> Result<Option<Bytes>> {
        // Percent-encode colons in the key (e.g. did:web: → did%3Aweb%3A)
        let encoded_key = percent_encode_key(key);
        let url = format!(
            "{}/b2api/v3/b2_download_file_by_name?bucketName={}&fileName={}",
            self.download_url,
            self.bucket_name,
            encoded_key
        );

        let resp = self
            .http
            .get(&url)
            .header("Authorization", &self.auth_token)
            .timeout(std::time::Duration::from_secs(60 * 60 * 4)) // 4h for large files
            .send()
            .await
            .context("b2_download_file_by_name request")?;

        if resp.status() == reqwest::StatusCode::NOT_FOUND {
            return Ok(None);
        }

        if !resp.status().is_success() {
            let status = resp.status();
            let text = resp.text().await.unwrap_or_default();
            bail!("b2_download_file_by_name HTTP {status}: {text}");
        }

        let bytes = resp.bytes().await.context("read download body")?;
        info!(key, bytes = bytes.len(), "B2 download complete");
        Ok(Some(bytes))
    }

    /// Upload `data` to `key`.  Computes SHA-1 and URL-encodes the key.
    ///
    /// NOTE: For files > 5 GB use `b2_start_large_file` / multipart instead.
    /// This method uses the single-shot upload path (max 5 GB per B2 docs).
    #[allow(dead_code)]
    pub async fn upload(&self, key: &str, data: &[u8], content_type: &str) -> Result<()> {
        // Step 1: get upload URL
        let get_url = format!("{}/b2api/v3/b2_get_upload_url", self.api_url);
        let body = serde_json::json!({ "bucketId": self.bucket_id });
        let resp = self
            .http
            .post(&get_url)
            .header("Authorization", &self.auth_token)
            .json(&body)
            .send()
            .await
            .context("b2_get_upload_url")?;

        if !resp.status().is_success() {
            let status = resp.status();
            let text = resp.text().await.unwrap_or_default();
            bail!("b2_get_upload_url HTTP {status}: {text}");
        }

        let upload_info: UploadUrlResponse = resp.json().await.context("parse upload url")?;

        // Step 2: compute SHA-1
        let mut hasher = Sha1::new();
        hasher.update(data);
        let sha1_hex = hex::encode(hasher.finalize());

        // Step 3: upload
        let encoded_key = percent_encode_key(key);
        let upload_resp = self
            .http
            .post(&upload_info.upload_url)
            .header("Authorization", &upload_info.authorization_token)
            .header("X-Bz-File-Name", &encoded_key)
            .header("Content-Type", content_type)
            .header("Content-Length", data.len().to_string())
            .header("X-Bz-Content-Sha1", &sha1_hex)
            .body(data.to_vec())
            .send()
            .await
            .context("b2 upload")?;

        if !upload_resp.status().is_success() {
            let status = upload_resp.status();
            let text = upload_resp.text().await.unwrap_or_default();
            bail!("b2 upload HTTP {status}: {text}");
        }

        info!(key, bytes = data.len(), "B2 upload complete");
        Ok(())
    }
}

/// Percent-encode characters that are not safe in B2 `X-Bz-File-Name` /
/// `fileName=` query params.  Slashes are kept literal (path separators).
/// The main culprit in our keys is `:` from `did:web:...`.
fn percent_encode_key(key: &str) -> String {
    let mut out = String::with_capacity(key.len() + 16);
    for c in key.chars() {
        match c {
            // Safe: unreserved chars + slash (path separator)
            'A'..='Z' | 'a'..='z' | '0'..='9' | '-' | '_' | '.' | '~' | '/' => out.push(c),
            // Percent-encode everything else
            c => {
                let mut buf = [0u8; 4];
                let encoded = c.encode_utf8(&mut buf);
                for byte in encoded.bytes() {
                    out.push('%');
                    out.push_str(&format!("{byte:02X}"));
                }
            }
        }
    }
    out
}

/// Compute SHA-256 hex digest of a byte slice.
pub fn sha256_hex(data: &[u8]) -> String {
    use sha2::Digest as _;
    let digest = sha2::Sha256::digest(data);
    hex::encode(digest)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_percent_encode_key_colons() {
        let key = "maps/osm-pbf/did:web:maps.etzhayyim.com:planet/2026-05-08/planet.osm.pbf";
        let enc = percent_encode_key(key);
        assert!(enc.contains("%3A"), "colons should be encoded");
        assert!(enc.contains('/'), "slashes should be preserved");
        assert!(enc.contains("maps/osm-pbf/did%3Aweb%3Amaps.etzhayyim.com%3Aplanet"));
    }

    #[test]
    fn test_sha256_hex_stable() {
        let h = sha256_hex(b"hello");
        assert_eq!(h.len(), 64);
    }
}
