//! `yata` — command-line frontend over the yata Rust client.
//!
//! Run `yata --help` for the full subcommand list. v0.1 ships the
//! command surface and dispatches to the underlying client; commands
//! whose backing path is not yet implemented in `yata-core` v0.1 print
//! a clear "not yet implemented" message and return exit 2.

#![deny(missing_debug_implementations)]

use clap::{Parser, Subcommand};
use yata_core::Yata;

#[derive(Parser, Debug)]
#[command(
    name = "yata",
    about = "Rust CLI for yatabase — graph DB + integrated Supabase-style storage.",
    version,
)]
struct Args {
    /// Connection string. Defaults to YATA_DSN env var.
    #[arg(short, long, env = "YATA_DSN", global = true)]
    dsn: Option<String>,

    #[command(subcommand)]
    cmd: Cmd,
}

#[derive(Subcommand, Debug)]
enum Cmd {
    /// Initialise ~/.yata/config.toml
    Init,

    /// Open an interactive shell against the configured DSN.
    Connect {
        /// Override the DSN supplied via --dsn / YATA_DSN.
        endpoint: Option<String>,
    },

    /// Inspect / migrate / introspect the schema.
    #[command(subcommand)]
    Schema(SchemaCmd),

    /// Manage materialised views.
    #[command(subcommand)]
    Mv(MvCmd),

    /// Run OWL reasoning against the tenant graph.
    Reason {
        /// One of: el / rl / ql / dl
        profile: String,
    },

    /// Validate the graph against a SHACL shape file.
    ShaclValidate {
        /// Path to a Turtle/JSON-LD shape file.
        path: String,
    },

    /// Bulk import rows from a CSV / JSONL file.
    Import {
        /// Path to a local file.
        path: String,
        /// Vertex label to insert into.
        #[arg(long)]
        label: String,
    },

    /// Run a one-shot SPARQL or SQL query and print the result.
    #[command(subcommand)]
    Export(ExportCmd),

    /// Start the embedded MCP server (yata-mcp).
    McpServe {
        /// TCP port (defaults to 8765).
        #[arg(long, default_value_t = 8765)]
        port: u16,
    },

    /// Run a built-in latency / throughput benchmark.
    Bench,
}

#[derive(Subcommand, Debug)]
enum SchemaCmd {
    /// Print the current schema.
    Show,
    /// Apply a `*.rs` schema migration file (cargo will compile it).
    Migrate {
        /// Path to a Rust file declaring vertex / edge types.
        path: String,
    },
}

#[derive(Subcommand, Debug)]
enum MvCmd {
    /// List materialised views.
    List,
    /// Tail events from a single MV.
    Tail {
        /// MV name.
        name: String,
    },
}

#[derive(Subcommand, Debug)]
enum ExportCmd {
    /// Export rows for a SPARQL query.
    Sparql {
        /// SPARQL query string.
        query: String,
        /// Output format: json / csv / tsv.
        #[arg(long, default_value = "json")]
        format: String,
    },
}

#[tokio::main]
async fn main() -> std::process::ExitCode {
    tracing_subscriber::fmt()
        .with_env_filter(tracing_subscriber::EnvFilter::from_default_env())
        .compact()
        .init();

    let args = Args::parse();
    match run(args).await {
        Ok(()) => std::process::ExitCode::SUCCESS,
        Err(e) => {
            eprintln!("yata: {e}");
            std::process::ExitCode::from(2)
        }
    }
}

async fn run(args: Args) -> yata_core::Result<()> {
    match args.cmd {
        Cmd::Init => {
            println!("[v0.1 skeleton] init: write ~/.yata/config.toml — implementation lands in v0.2");
            Ok(())
        }
        Cmd::Connect { endpoint } => {
            let dsn = endpoint.or(args.dsn).ok_or_else(|| {
                yata_core::YataError::Dsn("no DSN supplied (use --dsn or YATA_DSN)".into())
            })?;
            let _y = Yata::connect(&dsn).await?;
            println!("[v0.1 skeleton] connected to {} (interactive shell ships in v0.2)",
                _y.dsn().host);
            Ok(())
        }
        Cmd::Schema(SchemaCmd::Show)        => not_yet("schema show"),
        Cmd::Schema(SchemaCmd::Migrate{..}) => not_yet("schema migrate"),
        Cmd::Mv(MvCmd::List)                => not_yet("mv list"),
        Cmd::Mv(MvCmd::Tail{..})            => not_yet("mv tail"),
        Cmd::Reason{..}                     => not_yet("reason"),
        Cmd::ShaclValidate{..}              => not_yet("shacl validate"),
        Cmd::Import{..}                     => not_yet("import"),
        Cmd::Export(ExportCmd::Sparql{..})  => not_yet("export sparql"),
        Cmd::McpServe{..}                   => not_yet("mcp serve"),
        Cmd::Bench                          => not_yet("bench"),
    }
}

fn not_yet(name: &str) -> yata_core::Result<()> {
    Err(yata_core::YataError::NotImplemented(
        Box::leak(format!("yata {name} (v0.1 skeleton)").into_boxed_str()),
    ))
}
