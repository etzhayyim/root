// Fixture Rust clap app for the yorishiro source-repo extractor tests.
//
// Run:
//   python3 70-tools/etzhayyim-cli/yorishiro/scripts/extract-clap.py \
//       70-tools/etzhayyim-cli/yorishiro/fixtures/source-repo-clap \
//       --kami-id bin:clap-demo --binary clap-demo
//
// Builder-style clap. Derive-style is not handled by the v0 walker.
//
// Not a working Rust program — fixture-only.

use clap::{Arg, ArgAction, Command, value_parser};

fn build_cli() -> Command {
    Command::new("clap-demo")
        .about("Demo clap CLI used by the yorishiro source-repo fixture.")
        .long_about("Longer description of the clap demo CLI for the source-repo extractor.")
        .arg(
            Arg::new("input_path")
                .help("Source path to read."),
        )
        .arg(
            Arg::new("output_path")
                .required(false)
                .help("Output path; '-' for stdout."),
        )
        .arg(
            Arg::new("max_rows")
                .long("max-rows")
                .short('m')
                .value_parser(value_parser!(i32))
                .default_value("100")
                .help("Maximum rows to emit."),
        )
        .arg(
            Arg::new("encoding")
                .long("encoding")
                .default_value("utf-8")
                .help("Output encoding."),
        )
        .arg(
            Arg::new("verbose")
                .long("verbose")
                .short('v')
                .action(ArgAction::SetTrue)
                .help("Enable verbose logging."),
        )
}

fn main() {
    let _ = build_cli().get_matches();
}
