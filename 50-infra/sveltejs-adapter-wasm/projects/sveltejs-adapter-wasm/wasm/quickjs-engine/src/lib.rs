#[allow(warnings)]
mod bindings;

use bindings::exports::etzhayyim::svelte_adapter::js_runtime::Guest;

struct Component;

impl Guest for Component {
    fn evaluate(_code: String, request_json: String) -> String {
        // Scaffold SSR response - parse URL from request JSON manually
        // Full JS evaluation (Boa/QuickJS) will be implemented in a follow-up
        let url = extract_url(&request_json);
        format!(
            r#"{{"status":200,"headers":{{"content-type":"text/html; charset=utf-8"}},"body":"<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n  <meta charset=\"utf-8\">\n  <title>SvelteKit SSR</title>\n</head>\n<body>\n  <div id=\"svelte\">\n    <h1>SvelteKit SSR via wasmCloud</h1>\n    <p>Route: {url}</p>\n    <p>Rendered by: Rust QuickJS engine (wRPC)</p>\n  </div>\n</body>\n</html>"}}"#
        )
    }
}

fn extract_url(json: &str) -> &str {
    // Simple manual JSON extraction to avoid serde dependency for now
    if let Some(start) = json.find("\"url\":\"") {
        let rest = &json[start + 7..];
        if let Some(end) = rest.find('"') {
            return &rest[..end];
        }
    }
    "/"
}

bindings::export!(Component with_types_in bindings);
