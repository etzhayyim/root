//! `yata-mcp` — Model Context Protocol server bridge.
//!
//! Wraps a [`Yata`] handle as an MCP server so LangGraph / Claude
//! Desktop / Cursor can call yatabase operations as native tools.
//!
//! Default tool set published by `MCPServer::new(y).serve(...)`:
//!
//! | tool                     | parameters                            | result                       |
//! |--------------------------|---------------------------------------|------------------------------|
//! | `query.sql`              | `{ sql: string }`                     | `{ rows: array }`            |
//! | `query.sparql`           | `{ query: string }`                   | `{ rows: array }`            |
//! | `vertex.insert`          | `{ label: string, value: object }`    | `{ ok: bool, vertex_id: string }` |
//! | `mv.subscribe`           | `{ name: string }`                    | `{ subscription_id: string }`     |
//! | `reason.run`             | `{ profile: "el" \| "rl" \| ... }`    | `{ triples_inferred: number }`    |
//!
//! v0.1 publishes the public surface only; the rmcp-backed server
//! implementation is wired in v0.3 once the underlying `Yata::query` /
//! `Yata::insert` paths are real (see `yata-core` v0.2).

#![cfg_attr(docsrs, feature(doc_cfg))]
#![deny(missing_debug_implementations)]
#![warn(missing_docs)]

use yata_core::{Yata, YataError, Result};

/// Optional configuration passed to [`McpServer::serve`].
#[derive(Debug, Clone)]
pub struct ServeConfig {
    /// TCP port to bind on. Defaults to `8765`.
    pub port: u16,
    /// HTTP host to bind on. Defaults to `127.0.0.1`.
    pub host: String,
    /// Optional Bearer token required from inbound clients. When `None`
    /// the server is open (intended for `localhost` / Claude Desktop).
    pub auth_bearer: Option<String>,
}

impl Default for ServeConfig {
    fn default() -> Self {
        Self {
            port: 8765,
            host: "127.0.0.1".to_string(),
            auth_bearer: None,
        }
    }
}

/// MCP server wrapping a [`Yata`] client.
#[derive(Debug, Clone)]
pub struct McpServer {
    yata: Yata,
}

impl McpServer {
    /// Construct a server. The server holds its own `Yata` handle (clone
    /// of the caller's) so connection lifetime is independent.
    pub fn new(yata: Yata) -> Self {
        Self { yata }
    }

    /// Start the MCP server. v0.1 returns `NotImplemented`; v0.3 wires
    /// the rmcp Streamable HTTP transport.
    pub async fn serve(self, _cfg: ServeConfig) -> Result<()> {
        let _ = self.yata; // suppress unused warning
        Err(YataError::NotImplemented(
            "yata-mcp::McpServer::serve is a v0.1 skeleton; rmcp wiring lives in 0.3",
        ))
    }
}
