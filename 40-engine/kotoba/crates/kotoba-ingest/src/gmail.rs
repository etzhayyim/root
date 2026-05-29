//! Gmail REST API client — OAuth2 refresh token flow.
//!
//! Required env vars:
//!   KOTOBA_GMAIL_CLIENT_ID
//!   KOTOBA_GMAIL_CLIENT_SECRET
//!   KOTOBA_GMAIL_REFRESH_TOKEN

use anyhow::{anyhow, Context, Result};
use base64::{Engine as _, engine::general_purpose::URL_SAFE_NO_PAD as B64URL};
use serde::Deserialize;

const TOKEN_URL: &str  = "https://oauth2.googleapis.com/token";
const GMAIL_BASE: &str = "https://gmail.googleapis.com/gmail/v1/users/me";

pub struct GmailClient {
    client_id:     String,
    client_secret: String,
    refresh_token: String,
    access_token:  String,
    http:          reqwest::Client,
}

#[derive(Deserialize)]
struct TokenResponse {
    access_token: String,
}

#[derive(Deserialize)]
struct MessageStub {
    id:        String,
    #[serde(rename = "threadId")]
    thread_id: String,
}

#[derive(Deserialize)]
struct RawMessageResponse {
    raw:       String,
    #[serde(rename = "threadId")]
    thread_id: String,
}

#[derive(Deserialize)]
struct HistoryResponse {
    history:            Option<Vec<HistoryRecord>>,
    #[serde(rename = "historyId")]
    history_id:         String,
}

#[derive(Deserialize)]
struct HistoryRecord {
    #[serde(rename = "messagesAdded", default)]
    messages_added: Vec<HistoryMessageAdded>,
}

#[derive(Deserialize)]
struct HistoryMessageAdded {
    message: MessageStub,
}

impl GmailClient {
    /// Build from environment variables.
    pub fn from_env() -> Result<Self> {
        let client_id     = std::env::var("KOTOBA_GMAIL_CLIENT_ID")
            .context("KOTOBA_GMAIL_CLIENT_ID not set")?;
        let client_secret = std::env::var("KOTOBA_GMAIL_CLIENT_SECRET")
            .context("KOTOBA_GMAIL_CLIENT_SECRET not set")?;
        let refresh_token = std::env::var("KOTOBA_GMAIL_REFRESH_TOKEN")
            .context("KOTOBA_GMAIL_REFRESH_TOKEN not set")?;
        Ok(Self {
            client_id,
            client_secret,
            refresh_token,
            access_token: String::new(),
            http: reqwest::Client::new(),
        })
    }

    /// Exchange the refresh token for a new access token.
    pub async fn refresh(&mut self) -> Result<()> {
        let resp: TokenResponse = self.http
            .post(TOKEN_URL)
            .form(&[
                ("grant_type",    "refresh_token"),
                ("client_id",     self.client_id.as_str()),
                ("client_secret", self.client_secret.as_str()),
                ("refresh_token", self.refresh_token.as_str()),
            ])
            .send().await?.error_for_status()?.json().await?;
        self.access_token = resp.access_token;
        Ok(())
    }

    /// Fetch the current inbox historyId from the Gmail profile endpoint.
    pub async fn profile_history_id(&mut self) -> Result<u64> {
        let url = format!("{GMAIL_BASE}/profile");
        let resp: serde_json::Value = self.http.get(&url)
            .bearer_auth(&self.access_token)
            .send().await?.error_for_status()?.json().await?;
        resp["historyId"].as_str()
            .and_then(|s| s.parse().ok())
            .ok_or_else(|| anyhow!("historyId not found in Gmail profile response"))
    }

    /// Return `(new_stubs, latest_history_id)` since `start_history_id`.
    /// Each stub is `(message_id, thread_id)`.
    pub async fn list_history(
        &mut self,
        start_history_id: u64,
    ) -> Result<(Vec<(String, String)>, u64)> {
        let url = format!("{GMAIL_BASE}/history");
        let resp = self.http.get(&url)
            .bearer_auth(&self.access_token)
            .query(&[
                ("startHistoryId", start_history_id.to_string()),
                ("historyTypes",   "messageAdded".to_string()),
            ])
            .send().await?;

        // 404 means historyId has expired — return empty; caller must full-sync
        if resp.status() == reqwest::StatusCode::NOT_FOUND {
            tracing::warn!(start_history_id, "Gmail historyId expired; skipping delta");
            return Ok((vec![], start_history_id));
        }
        let h: HistoryResponse = resp.error_for_status()?.json().await?;
        let new_id = h.history_id.parse::<u64>().unwrap_or(start_history_id);

        let stubs = h.history
            .unwrap_or_default()
            .into_iter()
            .flat_map(|r| r.messages_added)
            .map(|m| (m.message.id, m.message.thread_id))
            .collect();
        Ok((stubs, new_id))
    }

    /// Fetch one message as raw RFC 2822 bytes plus its thread_id.
    pub async fn get_raw_message(&mut self, message_id: &str) -> Result<(Vec<u8>, String)> {
        let url = format!("{GMAIL_BASE}/messages/{message_id}");
        let resp: RawMessageResponse = self.http.get(&url)
            .bearer_auth(&self.access_token)
            .query(&[("format", "raw")])
            .send().await?.error_for_status()?.json().await?;
        let raw = B64URL.decode(&resp.raw)
            .context("base64url decode of Gmail raw message failed")?;
        Ok((raw, resp.thread_id))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // The Gmail wire contract is encoded entirely in the `#[serde(rename)]` /
    // `default` attributes on these private structs. The async methods that consume
    // them can't be unit-tested without live OAuth, so these tests pin the exact JSON
    // field mapping — a renamed/dropped field (or a broken rename) fails here instead
    // of silently yielding empty deltas at runtime.

    #[test]
    fn token_response_extracts_access_token() {
        let v: TokenResponse =
            serde_json::from_str(r#"{"access_token":"ya29.abc","expires_in":3599}"#).unwrap();
        assert_eq!(v.access_token, "ya29.abc");
    }

    #[test]
    fn message_stub_maps_camelcase_thread_id() {
        let v: MessageStub =
            serde_json::from_str(r#"{"id":"18f","threadId":"t42"}"#).unwrap();
        assert_eq!(v.id, "18f");
        assert_eq!(v.thread_id, "t42");
    }

    #[test]
    fn raw_message_response_maps_thread_id() {
        let v: RawMessageResponse =
            serde_json::from_str(r#"{"raw":"aGk","threadId":"t7","id":"m1"}"#).unwrap();
        assert_eq!(v.raw, "aGk");
        assert_eq!(v.thread_id, "t7");
    }

    #[test]
    fn history_response_flattens_messages_added_into_stubs() {
        // Mirrors the stub-extraction in `list_history` without any HTTP.
        let json = r#"{
            "historyId": "9001",
            "history": [
                {"id":"h1","messagesAdded":[
                    {"message":{"id":"m1","threadId":"t1"}},
                    {"message":{"id":"m2","threadId":"t2"}}
                ]},
                {"id":"h2","messagesAdded":[
                    {"message":{"id":"m3","threadId":"t1"}}
                ]}
            ]
        }"#;
        let h: HistoryResponse = serde_json::from_str(json).unwrap();
        assert_eq!(h.history_id.parse::<u64>().unwrap(), 9001);
        let stubs: Vec<(String, String)> = h.history
            .unwrap_or_default()
            .into_iter()
            .flat_map(|r| r.messages_added)
            .map(|m| (m.message.id, m.message.thread_id))
            .collect();
        assert_eq!(stubs, vec![
            ("m1".into(), "t1".into()),
            ("m2".into(), "t2".into()),
            ("m3".into(), "t1".into()),
        ]);
    }

    #[test]
    fn history_response_handles_empty_delta() {
        // Gmail returns no `history` key when there are no changes since startHistoryId.
        let h: HistoryResponse =
            serde_json::from_str(r#"{"historyId":"9100"}"#).unwrap();
        assert!(h.history.is_none());
        assert_eq!(h.history.unwrap_or_default().len(), 0);
    }

    #[test]
    fn history_record_defaults_messages_added_when_absent() {
        // A history record can carry only label changes — `messagesAdded` then absent.
        let r: HistoryRecord = serde_json::from_str(r#"{"id":"h9"}"#).unwrap();
        assert!(r.messages_added.is_empty());
    }

    #[test]
    fn raw_decode_uses_url_safe_no_pad_alphabet() {
        // Gmail `format=raw` returns web-safe base64 (`-`/`_`, no padding). Bytes
        // 0xFB 0xFF encode to "-_8" under URL_SAFE_NO_PAD; the standard alphabet
        // would produce "+/" and fail here — guarding the chosen engine.
        let bytes = [0xFBu8, 0xFF];
        let encoded = B64URL.encode(bytes);
        assert_eq!(encoded, "-_8");
        assert_eq!(B64URL.decode(&encoded).unwrap(), bytes);
    }

    #[test]
    fn raw_decode_round_trips_rfc2822_message() {
        let msg = b"From: a@example.com\r\nSubject: hi\r\n\r\nbody";
        let encoded = B64URL.encode(msg);
        assert_eq!(B64URL.decode(&encoded).unwrap(), msg);
    }
}
