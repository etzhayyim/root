package main

import (
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

func runLint(args []string) error {
	fs := flag.NewFlagSet("lint", flag.ContinueOnError)
	fs.SetOutput(os.Stdout)
	root := fs.String("root", "", "repo root (default: git root)")
	if err := fs.Parse(args); err != nil {
		return err
	}

	rest := fs.Args()
	target := "all"
	if len(rest) > 0 {
		target = rest[0]
	}

	wd, _ := os.Getwd()
	wsRoot := wd
	if *root != "" {
		wsRoot = *root
	} else if gr, err := findGitRoot(wd); err == nil {
		wsRoot = gr
	}
	if abs, err := filepath.Abs(wsRoot); err == nil {
		wsRoot = abs
	}

	switch strings.ToLower(target) {
	case "all":
		// Guard against newly introduced non-canonical command method names.
		if err := runLintTarget(wsRoot, "nsid-regression"); err != nil {
			return err
		}
		// Block deprecated PDS/graph NSIDs.
		if err := runLintTarget(wsRoot, "legacy-pds-nsid"); err != nil {
			return err
		}
		// Prevent error swallowing patterns that hide real failures.
		if err := runLintTarget(wsRoot, "silent-catch"); err != nil {
			return err
		}
		// Keep source identifiers in camelCase on TS/TSX surfaces.
		if err := runLintTarget(wsRoot, "ts-camel"); err != nil {
			return err
		}
		// Enforce JSON/JSON-LD naming for graph/query interoperability.
		if err := runLintTarget(wsRoot, "json-sql"); err != nil {
			return err
		}
		// Keep deps metadata in sync with the working tree, excluding .depsignore paths.
		return runLintTarget(wsRoot, "deps-drift")
	case "silent-catch", "silent-catch-update", "nsid-regression", "legacy-pds-nsid", "ts-camel", "ts-camel-update", "json-sql", "json-sql-update", "deps-drift":
		return runLintTarget(wsRoot, strings.ToLower(target))
	case "help", "--help", "-h":
		printLintUsage()
		return nil
	default:
		return fmt.Errorf("unknown lint target: %s", target)
	}
}

func runLintTarget(wsRoot, target string) error {
	switch target {
	case "nsid-regression":
		fmt.Fprintf(os.Stderr, "==> lint target: nsid-regression\n")
		return runCmd(wsRoot, "node", "70-tools/scripts/lint/nsid-regression-guard.mjs")
	case "legacy-pds-nsid":
		fmt.Fprintf(os.Stderr, "==> lint target: legacy-pds-nsid\n")
		return runCmd(wsRoot, "node", "70-tools/scripts/lint/no-legacy-pds-nsid.mjs")
	case "silent-catch":
		fmt.Fprintf(os.Stderr, "==> lint target: silent-catch\n")
		return runCmd(wsRoot, "node", "70-tools/scripts/lint/no-silent-catch.mjs")
	case "silent-catch-update":
		fmt.Fprintf(os.Stderr, "==> lint target: silent-catch-update\n")
		return runCmd(wsRoot, "node", "70-tools/scripts/lint/no-silent-catch.mjs", "--update-baseline")
	case "ts-camel":
		fmt.Fprintf(os.Stderr, "==> lint target: ts-camel\n")
		return runCmd(wsRoot, "node", "70-tools/scripts/lint/ts-camelcase.mjs")
	case "ts-camel-update":
		fmt.Fprintf(os.Stderr, "==> lint target: ts-camel-update\n")
		return runCmd(wsRoot, "node", "70-tools/scripts/lint/ts-camelcase.mjs", "--update-baseline")
	case "json-sql":
		fmt.Fprintf(os.Stderr, "==> lint target: json-sql\n")
		return runCmd(wsRoot, "node", "70-tools/scripts/lint/json-sql-case.mjs")
	case "json-sql-update":
		fmt.Fprintf(os.Stderr, "==> lint target: json-sql-update\n")
		return runCmd(wsRoot, "node", "70-tools/scripts/lint/json-sql-case.mjs", "--update-baseline")
	case "deps-drift":
		fmt.Fprintf(os.Stderr, "==> lint target: deps-drift\n")
		return runCmd(filepath.Join(wsRoot, "70-tools", "gftd", "gftd"), "go", "run", ".", "deps", "drift", "--limit", "20")
	default:
		return fmt.Errorf("unknown lint target: %s", target)
	}
}

func printLintUsage() {
	fmt.Println(`Usage: gftd lint [target] [--root <dir>]

Targets:
  all                  run nsid-regression + legacy-pds-nsid + silent-catch + ts-camel + json-sql + deps-drift
  nsid-regression      fail on new non-NSID command names vs baseline CSV
  legacy-pds-nsid      fail on deprecated PDS/graph NSIDs
  silent-catch         run silent catch lint
  ts-camel             enforce camelCase identifiers in TS/TSX (Rust is out of scope)
  json-sql          enforce camelCase keys / PascalCase labels in JSON+JSON-LD
  deps-drift           compare repo paths vs deps.toml declarations with .depsignore applied
  silent-catch-update  update silent-catch lint baseline
  ts-camel-update      update ts-camel lint baseline
  json-sql-update   update json-sql lint baseline`)
}
