/// OpenAI-compatible HTTP inference engine.
///
/// Works with any OpenAI-compatible endpoint: Ollama, vLLM, Vultr A16, LiteLLM.
///
/// Environment variables:
///   KOTOBA_INFERENCE_URL     — base URL (e.g. http://localhost:11434 for Ollama)
///   KOTOBA_INFERENCE_MODEL   — model name (default: gemma4:e4b)
///   KOTOBA_INFERENCE_API_KEY — optional Bearer token (LiteLLM / vLLM / OpenAI)
///
/// Wire format: POST /v1/chat/completions (OpenAI chat completions API).
///
/// Only compiled when the `http-inference` feature is enabled.
#[cfg(feature = "http-inference")]
mod inner {
    use anyhow::{anyhow, Result};

    /// Synchronous HTTP inference engine backed by reqwest + tokio block_in_place.
    #[derive(Clone)]
    pub struct HttpInferEngine {
        base_url: String,
        model: String,
        api_key: Option<String>,
        client: reqwest::Client,
    }

    impl HttpInferEngine {
        /// Construct from environment variables.
        ///
        /// Requires `KOTOBA_INFERENCE_URL`.
        /// `KOTOBA_INFERENCE_MODEL` defaults to `"gemma4:e4b"`.
        /// `KOTOBA_INFERENCE_API_KEY` is optional; when present, sent as
        /// `Authorization: Bearer ...` (required for LiteLLM master-key auth).
        pub fn from_env() -> Result<Self> {
            let base_url = std::env::var("KOTOBA_INFERENCE_URL")
                .map_err(|_| anyhow!("KOTOBA_INFERENCE_URL not set"))?;
            let model = std::env::var("KOTOBA_INFERENCE_MODEL")
                .unwrap_or_else(|_| "gemma4:e4b".to_string());
            let api_key = std::env::var("KOTOBA_INFERENCE_API_KEY").ok();
            let client = reqwest::Client::builder()
                .timeout(std::time::Duration::from_secs(120))
                .build()?;
            Ok(Self {
                base_url: base_url.trim_end_matches('/').to_string(),
                model,
                api_key,
                client,
            })
        }

        /// Synchronous generate — blocks the current tokio worker thread.
        ///
        /// Safe to call from `Arc<dyn Fn>` InferenceFn closures that run inside
        /// a `tokio::task::spawn_blocking` or a multi-threaded runtime.
        pub fn generate(&self, prompt: &str, max_tokens: usize) -> Result<String> {
            let engine = self.clone();
            let prompt = prompt.to_string();
            tokio::task::block_in_place(|| {
                tokio::runtime::Handle::current()
                    .block_on(engine.generate_async(&prompt, max_tokens))
            })
        }

        async fn generate_async(&self, prompt: &str, max_tokens: usize) -> Result<String> {
            let url = format!("{}/v1/chat/completions", self.base_url);
            let body = build_chat_request_body(&self.model, prompt, max_tokens);
            let mut req = self
                .client
                .post(&url)
                .header("Content-Type", "application/json")
                .json(&body);
            if let Some(key) = &self.api_key {
                req = req.bearer_auth(key);
            }
            let resp = req.send().await?.error_for_status()?;

            let json: serde_json::Value = resp.json().await?;
            parse_chat_response(&json)
        }
    }

    /// Build the OpenAI `/v1/chat/completions` request body for a single-turn prompt.
    /// Extracted from `generate_async` so the wire shape is unit-testable without HTTP.
    fn build_chat_request_body(model: &str, prompt: &str, max_tokens: usize) -> serde_json::Value {
        serde_json::json!({
            "model": model,
            "messages": [{ "role": "user", "content": prompt }],
            "max_tokens": max_tokens,
            "stream": false,
        })
    }

    /// Extract the assistant message text from an OpenAI chat-completions response,
    /// erroring if the expected `choices[0].message.content` path is absent.
    fn parse_chat_response(json: &serde_json::Value) -> Result<String> {
        json["choices"][0]["message"]["content"]
            .as_str()
            .ok_or_else(|| anyhow!("missing choices[0].message.content in response"))
            .map(|s| s.to_string())
    }

    #[cfg(test)]
    mod tests {
        use super::*;

        #[test]
        fn request_body_matches_openai_chat_shape() {
            let body = build_chat_request_body("gemma4:e4b", "hello", 256);
            assert_eq!(body["model"], "gemma4:e4b");
            assert_eq!(body["messages"][0]["role"], "user");
            assert_eq!(body["messages"][0]["content"], "hello");
            assert_eq!(body["max_tokens"], 256);
            // Non-streaming is required: the sync engine reads a single JSON body.
            assert_eq!(body["stream"], false);
        }

        #[test]
        fn parse_response_extracts_assistant_content() {
            let json = serde_json::json!({
                "choices": [{ "message": { "role": "assistant", "content": "hi there" } }]
            });
            assert_eq!(parse_chat_response(&json).unwrap(), "hi there");
        }

        #[test]
        fn parse_response_errors_on_missing_content() {
            // An error/empty payload must surface as Err, not a silent empty string.
            let json = serde_json::json!({ "error": { "message": "model not found" } });
            assert!(parse_chat_response(&json).is_err());
        }
    }
}

#[cfg(feature = "http-inference")]
pub use inner::HttpInferEngine;
