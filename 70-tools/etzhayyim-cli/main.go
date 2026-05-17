// gftd — magatama build/deploy CLI (Cloudflare Containers)
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
	case "version", "--version", "-v":
		fmt.Printf("gftd %s\n", version)
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
	fmt.Printf(`gftd %s — magatama component build/deploy CLI (Cloudflare Containers)

USAGE:
  gftd <command> [flags]

COMMANDS:
  build              Build TinyGo WASM component → wasm-tools componentize (magatama WIT)
                     --extension: build as W Protocol extension (world: gftd:w/w-extension)
  build-server       Build magatama-server binary + Docker image (zigbuild cross-compile)
  deploy             Cloudflare Container deploy from source dir (magatama.toml + gftd.json → wrangler deploy + smoke test)
  plugin        Manage build tools (wasm-tools, tinygo adapters)
  version       Print version

Run 'gftd <command> --help' for command-specific flags.
`, version)
}

func fatalf(format string, args ...any) {
	fmt.Fprintf(os.Stderr, "gftd: "+format+"\n", args...)
	os.Exit(1)
}
