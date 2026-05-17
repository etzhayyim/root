package main

import (
	"flag"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
)

// runDomainIngest handles `gftd domain-ingest` subcommands.
//
// Separates canonical write paths from Common Crawl acquisition:
// - common-crawler: acquire / transform / export
// - domain-ingest: normalize / enrich / write into PDS
func runDomainIngest(args []string) error {
	if len(args) == 0 {
		return runDomainIngestLocal(nil)
	}

	switch args[0] {
	case "local":
		return runDomainIngestLocal(args[1:])
	case "common-crawl", "cc":
		return runDomainIngestCommonCrawl(args[1:])
	case "help", "--help", "-h":
		return domainIngestUsage()
	default:
		// Backward-compatible shorthand: `gftd domain-ingest --domain gtin`
		if len(args) > 0 && len(args[0]) > 0 && args[0][0] == '-' {
			return runDomainIngestLocal(args)
		}
		return fmt.Errorf("unknown domain-ingest subcommand: %s\n\nRun 'gftd domain-ingest help' for usage", args[0])
	}
}

func runDomainIngestLocal(args []string) error {
	fs := flag.NewFlagSet("domain-ingest local", flag.ExitOnError)
	domain := fs.String("domain", "", "domain filter (e.g., hanrei, gtin, blockchain)")
	limit := fs.Int("limit", 10000, "max records per source")
	dryRun := fs.Bool("dry-run", false, "validate and count without PDS writes")
	skipLLM := fs.Bool("skip-llm", false, "skip Murakumo enrichment queueing")
	fs.Parse(args)

	script, err := resolveDomainIngestScript()
	if err != nil {
		return err
	}

	cmdArgs := buildDomainIngestLocalArgs(script, *domain, *limit, *dryRun, *skipLLM)
	fmt.Printf("▶ domain-ingest local: script=%s limit=%d dry-run=%v\n", filepath.Base(script), *limit, *dryRun)
	if *domain != "" {
		fmt.Printf("  domain filter: %s\n", *domain)
	}
	return execDomainIngestNode(cmdArgs)
}

func runDomainIngestCommonCrawl(args []string) error {
	fs := flag.NewFlagSet("domain-ingest common-crawl", flag.ExitOnError)
	dryRun := fs.Bool("dry-run", false, "validate only, no PDS writes")
	batchSize := fs.Int("batch-size", 200, "records per PDS applyWrites batch")
	source := fs.String("source", "intel", "data source: intel (domain_intel.jsonl.gz) or graph (did_batch_*.sql)")
	pds := fs.String("pds", "https://atproto.etzhayyim.com", "PDS URL")
	fs.Parse(args)

	pyArgs := []string{ccProjectScript("phase5_inject.py")}
	if *dryRun {
		pyArgs = append(pyArgs, "--dry-run")
	}
	pyArgs = append(pyArgs, "--batch-size", fmt.Sprintf("%d", *batchSize))
	pyArgs = append(pyArgs, "--source", *source)

	env := os.Environ()
	env = append(env, fmt.Sprintf("PDS_URL=%s", *pds))

	fmt.Printf("▶ domain-ingest common-crawl: source=%s batch=%d dry-run=%v\n", *source, *batchSize, *dryRun)
	return ccExecWithEnv(pyArgs, env)
}

func resolveDomainIngestScript() (string, error) {
	repoRoot, err := findGitRoot(".")
	if err != nil {
		return "", fmt.Errorf("find git root: %w", err)
	}
	script := filepath.Join(repoRoot, "70-tools", "scripts", "ingest-domain-data.ts")
	if _, err := os.Stat(script); err != nil {
		return "", fmt.Errorf("domain ingest script not found: %s", script)
	}
	return script, nil
}

func buildDomainIngestLocalArgs(script, domain string, limit int, dryRun, skipLLM bool) []string {
	args := []string{"tsx", script}
	if domain != "" {
		args = append(args, "--domain", domain)
	}
	if limit > 0 {
		args = append(args, "--limit", fmt.Sprintf("%d", limit))
	}
	if dryRun {
		args = append(args, "--dry-run")
	}
	if skipLLM {
		args = append(args, "--skip-llm")
	}
	return args
}

func execDomainIngestNode(args []string) error {
	if _, err := exec.LookPath("npx"); err != nil {
		return fmt.Errorf("npx not found in PATH")
	}
	cmd := exec.Command("npx", args...)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	cmd.Env = os.Environ()
	return cmd.Run()
}

func domainIngestUsage() error {
	fmt.Print(`gftd domain-ingest — Canonical domain write path (normalize → enrich → PDS write)

USAGE:
  gftd domain-ingest [local] [flags]
  gftd domain-ingest common-crawl [flags]

SUBCOMMANDS:
  local         Ingest domain datasets from /Volumes/251220/domain-data via scripts/ingest-domain-data.ts
                --domain slug     domain filter (e.g., gtin, hanrei)
                --limit N         records per source (default: 10000)
                --dry-run         validate/count only
                --skip-llm        skip Murakumo enrichment queue

  common-crawl  Import Common Crawl exports into PDS
                --source src      intel or graph (default: intel)
                --batch-size N    applyWrites batch size (default: 200)
                --pds url         PDS URL (default: https://atproto.etzhayyim.com)
                --dry-run         validate only

BOUNDARY:
  common-crawler   acquisition / graph extraction / intel generation
  domain-ingest    normalization / enrichment / canonical writes
  coverage domain  live read-only reconciliation from mv_domain_coverage_live

EXAMPLES:
  gftd domain-ingest --domain gtin --limit 500 --dry-run
  gftd domain-ingest local --domain hanrei --skip-llm
  gftd domain-ingest common-crawl --source intel --dry-run
`)
	return nil
}
