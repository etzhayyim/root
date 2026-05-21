// Fixture clap derive-style app for Phase 2.5.4.1.
//
// Run:
//   python3 70-tools/etzhayyim-cli/yorishiro/scripts/extract-clap.py \
//       70-tools/etzhayyim-cli/yorishiro/fixtures/source-repo-clap-derive \
//       --kami-id bin:clap-derive --binary clap-derive
//
// #[derive(Parser)] struct + #[derive(Subcommand)] enum.
// Not a working Rust program — fixture-only.

use clap::{Parser, Subcommand};

#[derive(Parser, Debug)]
#[command(name = "clap-derive", about = "Demo clap derive-style CLI used by the yorishiro fixture.", version = "0.1.0")]
struct Cli {
    /// Enable verbose logging across all subcommands.
    #[arg(long, short = 'v', action = ArgAction::SetTrue)]
    verbose: bool,

    /// Path to config file.
    #[arg(long, default_value = "/etc/derive.conf")]
    config: String,

    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand, Debug)]
enum Commands {
    /// Encode an input file.
    Encode {
        /// Source path.
        input_path: String,
        /// Output bitrate (kbps).
        #[arg(long, default_value = "192")]
        bitrate: i32,
        /// Use lossless encoding.
        #[arg(long, action = ArgAction::SetTrue)]
        lossless: bool,
    },
    /// Decode an input file.
    Decode {
        /// Source path.
        input_path: String,
        /// Output path; '-' for stdout.
        output_path: Option<String>,
        /// Sample rate (Hz).
        #[arg(long, default_value = "44100")]
        sample_rate: i32,
    },
}

fn main() {
    let _ = Cli::parse();
}
