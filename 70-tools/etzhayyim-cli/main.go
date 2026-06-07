// etzhayyim — kotodama build/deploy CLI (Cloudflare Containers)
package main

import (
	"fmt"
	"os"
	"path/filepath"
)

const version = "0.2.0"

func main() {
	if len(os.Args) < 2 {
		printUsage()
		os.Exit(1)
	}

	var err error
	switch os.Args[1] {
	case "build":
		err = runBuild(os.Args[2:])
	case "build-server":
		err = runBuildServer(os.Args[2:])
	case "deploy":
		err = runDeploy(os.Args[2:])
	case "plugin":
		err = runPlugin(os.Args[2:])
	case "bench":
		err = runBench(os.Args[2:])
	case "baien":
		err = runBaien(os.Args[2:])
	case "actor":
		err = runActor(os.Args[2:])
	case "agent-token":
		err = runAgentToken(os.Args[2:])
	case "capability":
		err = runCapability(os.Args[2:])
	case "kuni-umi":
		err = runKuniUmi(os.Args[2:])
	case "version", "--version", "-v":
		fmt.Printf("etzhayyim %s\n", version)
	case "help", "--help", "-h":
		printUsage()
	default:
		fatalf("unknown command: %s\n\nRun '%s help' for usage.", os.Args[1], filepath.Base(os.Args[0]))
	}
	if err != nil {
		fatalf("%v", err)
	}
}

func printUsage() {
	fmt.Printf(`etzhayyim %s — kotodama component build/deploy CLI (Cloudflare Containers)

USAGE:
  etzhayyim <command> [flags]

COMMANDS:
  build              Build TinyGo WASM component → wasm-tools componentize (kotodama WIT)
                     --extension: build as W Protocol extension (world: etzhayyim:w/w-extension)
  build-server       Build kotodama-server binary + Docker image (zigbuild cross-compile)
  deploy             Cloudflare Container deploy from source dir (kotodama.toml + etzhayyim.json → wrangler deploy + smoke test)
  plugin        Manage build tools (wasm-tools, tinygo adapters)
  bench         Dispatch baien benches (micro / core4 / distill / rope-extend / list) — see 'etzhayyim bench help'
  baien         Ad-hoc baien inference (prompt) — see 'etzhayyim baien help'
  actor         Declarative actor deploy from actor.toml (--only <stage>, --non-interactive) — see 'etzhayyim actor help'
                Per ADR-2605232000.
  agent-token   Mint a scoped ephemeral JWT (Ed25519, default TTL 60s) for agent-led XRPC/deploy steps.
                Per ADR-2605232000.
  capability    Consent capability lifecycle (issue / verify / revoke / list) — see 'etzhayyim capability help'.
                Per ADR-2605231400 + ADR-2605232000.
  kuni-umi      6-phase robotic-deployment flow (define-site / submit-survey / propose-plan /
                record-progress / commission / audit-event) — see 'etzhayyim kuni-umi help'.
                Per ADR-2605201400.
  version       Print version

Run 'etzhayyim <command> --help' for command-specific flags.
`, version)
}

func fatalf(format string, args ...any) {
	fmt.Fprintf(os.Stderr, "etzhayyim: "+format+"\n", args...)
	os.Exit(1)
}
