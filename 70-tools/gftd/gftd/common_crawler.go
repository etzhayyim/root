package main

import (
	"flag"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"
)

// runCommonCrawler handles `gftd common-crawler` subcommands.
//
// Orchestrates Common Crawl pipeline: download → graph → intel.
// Canonical writes belong to `gftd domain-ingest common-crawl`.
// Python scripts in CC_DATA_DIR/scripts/ do the heavy lifting.
// XRPC interface: ai.gftd.apps.commonCrawler.* (common-crawl.etzhayyim.com)
func runCommonCrawler(args []string) error {
	if len(args) == 0 {
		return ccUsage()
	}

	switch args[0] {
	case "download":
		return ccDownload(args[1:])
	case "graph":
		return ccGraph(args[1:])
	case "intel":
		return ccIntel(args[1:])
	case "inject":
		fmt.Fprintln(os.Stderr, "warning: 'gftd common-crawler inject' is deprecated; use 'gftd domain-ingest common-crawl' instead")
		return runDomainIngestCommonCrawl(args[1:])
	case "monitor":
		return ccMonitor()
	case "status":
		return ccMonitor()
	case "purge":
		return ccPurge(args[1:])
	case "list-crawls":
		return ccListCrawls(args[1:])
	case "help", "--help", "-h":
		return ccUsage()
	default:
		return fmt.Errorf("unknown common-crawler subcommand: %s\n\nRun 'gftd common-crawler help' for usage", args[0])
	}
}

// ── Config ──

const (
	ccDefaultDataDir = "/Volumes/251220/CC/2603"
	ccVenvPython     = ".venv/bin/python3"
	ccScriptsDir     = "scripts"
)

func ccDataDir() string {
	if v := os.Getenv("CC_DATA_DIR"); v != "" {
		return v
	}
	return ccDefaultDataDir
}

func ccPython() string {
	return filepath.Join(ccDataDir(), ccVenvPython)
}

func ccScript(name string) string {
	return filepath.Join(ccDataDir(), ccScriptsDir, name)
}

// ccProjectScript resolves a script from the monorepo project directory,
// falling back to CC_DATA_DIR/scripts/ if the project copy doesn't exist.
func ccProjectScript(name string) string {
	// Try monorepo project scripts first
	repoRoot, _ := findGitRoot(".")
	if repoRoot != "" {
		candidates := []string{
			filepath.Join(repoRoot, "60-apps", "ai-gftd-project-common-crawl", "scripts", name),
			// backward-compat legacy layout
			filepath.Join(repoRoot, "projects", "ai-gftd-project-common-crawl", "scripts", name),
		}
		for _, projectPath := range candidates {
			if _, err := os.Stat(projectPath); err == nil {
				return projectPath
			}
		}
	}
	// Fallback to CC_DATA_DIR/scripts/
	return ccScript(name)
}

// ── download ──

func ccDownload(args []string) error {
	fs := flag.NewFlagSet("common-crawler download", flag.ExitOnError)
	workers := fs.Int("workers", 4, "parallel download workers")
	watOnly := fs.Bool("wat-only", false, "download WAT only (skip WET filter)")
	wetOnly := fs.Bool("wet-only", false, "process WET only (skip WAT download)")
	resume := fs.Bool("resume", true, "resume from saved state")
	crawl := fs.String("crawl", "CC-MAIN-2026-12", "Common Crawl crawl ID (e.g., CC-MAIN-2026-12)")
	formats := fs.String("format", "wat,wet", "file formats to download: wat, wet, warc (comma-separated)")
	domains := fs.String("domains", "", "domain filter file (one domain per line). Empty = use default authority list")
	rangeStart := fs.Int("range-start", 0, "start index in path list (for parallel sharding)")
	rangeEnd := fs.Int("range-end", 0, "end index in path list (0 = all)")
	fs.Parse(args)

	pyArgs := []string{ccScript("download_all.py")}
	if *watOnly {
		pyArgs = append(pyArgs, "--wat-only")
	}
	if *wetOnly {
		pyArgs = append(pyArgs, "--wet-only")
	}
	if *resume {
		pyArgs = append(pyArgs, "--resume")
	}
	pyArgs = append(pyArgs, "--workers", fmt.Sprintf("%d", *workers))

	env := os.Environ()
	env = append(env, fmt.Sprintf("CC_CRAWL_ID=%s", *crawl))
	env = append(env, fmt.Sprintf("CC_FORMATS=%s", *formats))
	if *domains != "" {
		env = append(env, fmt.Sprintf("CC_DOMAINS_FILE=%s", *domains))
	}
	if *rangeStart > 0 {
		env = append(env, fmt.Sprintf("CC_RANGE_START=%d", *rangeStart))
	}
	if *rangeEnd > 0 {
		env = append(env, fmt.Sprintf("CC_RANGE_END=%d", *rangeEnd))
	}

	fmt.Printf("▶ common-crawler download: %s format=%s workers=%d\n", *crawl, *formats, *workers)
	if *domains != "" {
		fmt.Printf("  domain filter: %s\n", *domains)
	}
	if *rangeStart > 0 || *rangeEnd > 0 {
		fmt.Printf("  range: [%d, %d)\n", *rangeStart, *rangeEnd)
	}
	return ccExecWithEnv(pyArgs, env)
}

// ── graph ──

func ccGraph(args []string) error {
	fs := flag.NewFlagSet("common-crawler graph", flag.ExitOnError)
	source := fs.String("source", "full", "WAT source: full or filtered")
	batchSize := fs.Int("batch-size", 5000, "Sql batch size (pages per file)")
	output := fs.String("output", "sql", "output format: sql, jsonl, parquet")
	domainFilter := fs.String("domain", "", "filter by internet domain pattern (e.g., *.go.jp)")
	crawl := fs.String("crawl", "CC-MAIN-2026-12", "crawl ID")
	fs.Parse(args)

	pyArgs := []string{
		ccProjectScript("phase3_wat_to_sql.py"),
		"--source", *source,
		"--batch-size", fmt.Sprintf("%d", *batchSize),
	}
	if strings.TrimSpace(*domainFilter) != "" {
		pyArgs = append(pyArgs, "--domain", strings.TrimSpace(*domainFilter))
	}

	env := os.Environ()
	env = append(env, fmt.Sprintf("CC_OUTPUT_FORMAT=%s", *output))
	env = append(env, fmt.Sprintf("CC_CRAWL_ID=%s", *crawl))
	if *domainFilter != "" {
		env = append(env, fmt.Sprintf("CC_DOMAIN_FILTER=%s", *domainFilter))
	}

	fmt.Printf("▶ common-crawler graph: %s → DID property graph (source=%s, format=%s)\n", *crawl, *source, *output)
	return ccExecWithEnv(pyArgs, env)
}

// ── intel ──

func ccIntel(args []string) error {
	fs := flag.NewFlagSet("common-crawler intel", flag.ExitOnError)
	limit := fs.Int("limit", 0, "max domains to process (0=all)")
	resume := fs.Bool("resume", false, "resume from saved state")
	model := fs.String("model", "qwen3.5-9b", "Murakumo model for intelligence extraction")
	minPages := fs.Int("min-pages", 0, "only process domains with >= N pages in crawl")
	domainFilter := fs.String("domain", "", "domain pattern filter (e.g., *.gov, *.go.jp)")
	output := fs.String("output", "jsonl", "output format: jsonl, sql, parquet")
	concurrency := fs.Int("concurrency", 1, "parallel LLM calls (careful: fleet capacity)")
	fs.Parse(args)

	pyArgs := []string{ccScript("phase4_intel_extract.py")}
	if *limit > 0 {
		pyArgs = append(pyArgs, "--limit", fmt.Sprintf("%d", *limit))
	}
	if *resume {
		pyArgs = append(pyArgs, "--resume")
	}

	env := os.Environ()
	env = append(env, fmt.Sprintf("MURAKUMO_MODEL=%s", *model))
	if *minPages > 0 {
		env = append(env, fmt.Sprintf("CC_MIN_PAGES=%d", *minPages))
	}
	if *domainFilter != "" {
		env = append(env, fmt.Sprintf("CC_DOMAIN_FILTER=%s", *domainFilter))
	}
	env = append(env, fmt.Sprintf("CC_OUTPUT_FORMAT=%s", *output))
	env = append(env, fmt.Sprintf("CC_CONCURRENCY=%d", *concurrency))

	fmt.Printf("▶ common-crawler intel: %s (limit=%d, min-pages=%d, format=%s)\n", *model, *limit, *minPages, *output)
	return ccExecWithEnv(pyArgs, env)
}

// ── inject ──

// ── list-crawls ──

func ccListCrawls(args []string) error {
	fs := flag.NewFlagSet("common-crawler list-crawls", flag.ExitOnError)
	year := fs.Int("year", 0, "filter by year (e.g., 2026)")
	json := fs.Bool("json", false, "JSON output")
	fs.Parse(args)

	pyArgs := []string{ccScript("list_crawls.py")}
	if *year > 0 {
		pyArgs = append(pyArgs, "--year", fmt.Sprintf("%d", *year))
	}
	if *json {
		pyArgs = append(pyArgs, "--json")
	}

	fmt.Println("▶ common-crawler list-crawls: querying index.commoncrawl.org")
	return ccExec(pyArgs)
}

// ── monitor ──

func ccMonitor() error {
	dataDir := ccDataDir()

	fmt.Println("═══ Common Crawl Pipeline Monitor ═══")
	fmt.Printf("Data dir: %s\n", dataDir)
	fmt.Printf("Time:     %s\n\n", time.Now().Format("2006-01-02 15:04:05"))

	fmt.Println("── Download ──")
	ccShowLogTail(filepath.Join(dataDir, ccScriptsDir, "download.log"), 2)
	ccShowDiskUsage(filepath.Join(dataDir, "wat-full"))
	ccShowFileCount(filepath.Join(dataDir, "wat-full"), "*.gz")

	fmt.Println("\n── Filtered ──")
	ccShowDiskUsage(filepath.Join(dataDir, "filtered/wat"))
	ccShowDiskUsage(filepath.Join(dataDir, "filtered/wet"))

	fmt.Println("\n── DID Property Graph ──")
	ccShowLogTail(filepath.Join(dataDir, ccScriptsDir, "phase3v2.log"), 2)
	ccShowFileCount(filepath.Join(dataDir, "graph"), "did_batch_*.sql")
	ccShowDiskUsage(filepath.Join(dataDir, "graph"))

	fmt.Println("\n── Intelligence Extraction ──")
	ccShowLogTail(filepath.Join(dataDir, ccScriptsDir, "phase4v3.log"), 2)

	fmt.Println("\n── State ──")
	for _, sf := range []string{".download_state.json", ".phase4v3_state.json"} {
		path := filepath.Join(dataDir, ccScriptsDir, sf)
		if info, err := os.Stat(path); err == nil {
			fmt.Printf("  %s: %s (%.0f KB)\n", sf, info.ModTime().Format("15:04:05"), float64(info.Size())/1024)
		}
	}

	fmt.Println("\n── Processes ──")
	ccCheckProcess("download_all.py")
	ccCheckProcess("phase3_did_property_graph.py")
	ccCheckProcess("phase4_intel_extract.py")

	return nil
}

// ── purge ──

func ccPurge(args []string) error {
	fs := flag.NewFlagSet("common-crawler purge", flag.ExitOnError)
	phase := fs.String("phase", "", "purge state: download, graph, intel, all")
	fs.Parse(args)

	if *phase == "" {
		return fmt.Errorf("--phase required: download, graph, intel, all")
	}

	dataDir := ccDataDir()
	scriptsDir := filepath.Join(dataDir, ccScriptsDir)

	phaseFiles := map[string][]string{
		"download": {filepath.Join(scriptsDir, ".download_state.json")},
		"graph":    {filepath.Join(scriptsDir, ".phase3v2_state.json")},
		"intel": {
			filepath.Join(scriptsDir, ".phase4v3_state.json"),
			filepath.Join(dataDir, "graph", "domain_intel.jsonl.gz"),
			filepath.Join(dataDir, "graph", "knowledge_graph.sql"),
		},
	}

	var files []string
	if *phase == "all" {
		for _, fs := range phaseFiles {
			files = append(files, fs...)
		}
	} else if fs, ok := phaseFiles[*phase]; ok {
		files = fs
	} else {
		return fmt.Errorf("unknown phase: %s (use: download, graph, intel, all)", *phase)
	}

	for _, f := range files {
		if err := os.Remove(f); err == nil {
			fmt.Printf("  removed: %s\n", filepath.Base(f))
		}
	}
	fmt.Printf("Purged state for phase: %s\n", *phase)
	return nil
}

// ── Helpers ──

func ccExec(pyArgs []string) error {
	return ccExecWithEnv(pyArgs, nil)
}

func ccExecWithEnv(pyArgs []string, env []string) error {
	python := ccPython()
	if _, err := os.Stat(python); err != nil {
		return fmt.Errorf("venv python not found at %s\nRun: python3 -m venv %s/.venv && %s/.venv/bin/pip install warcio requests httpx", python, ccDataDir(), ccDataDir())
	}

	cmd := exec.Command(python, pyArgs...)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	if env != nil {
		cmd.Env = env
	}
	return cmd.Run()
}

func ccShowLogTail(path string, n int) {
	data, err := os.ReadFile(path)
	if err != nil {
		fmt.Printf("  (no log: %s)\n", filepath.Base(path))
		return
	}
	lines := strings.Split(strings.TrimSpace(string(data)), "\n")
	start := max(len(lines)-n, 0)
	for _, line := range lines[start:] {
		fmt.Printf("  %s\n", line)
	}
}

func ccShowDiskUsage(path string) {
	out, err := exec.Command("du", "-sh", path).CombinedOutput()
	if err != nil {
		fmt.Printf("  %s: (empty)\n", filepath.Base(path))
		return
	}
	fmt.Printf("  %s", string(out))
}

func ccShowFileCount(dir, pattern string) {
	matches, _ := filepath.Glob(filepath.Join(dir, "**", pattern))
	if len(matches) == 0 {
		matches, _ = filepath.Glob(filepath.Join(dir, pattern))
	}
	fmt.Printf("  files (%s): %d\n", pattern, len(matches))
}

func ccCheckProcess(name string) {
	out, err := exec.Command("pgrep", "-f", name).CombinedOutput()
	if err != nil || strings.TrimSpace(string(out)) == "" {
		fmt.Printf("  %s: not running\n", name)
	} else {
		pids := strings.TrimSpace(string(out))
		fmt.Printf("  %s: running (PID %s)\n", name, strings.Split(pids, "\n")[0])
	}
}

func ccUsage() error {
	fmt.Print(`gftd common-crawler — Common Crawl acquisition pipeline (download → graph → intel)

USAGE:
  gftd common-crawler <subcommand> [flags]

SUBCOMMANDS:
  download      Download WET/WAT/WARC from Common Crawl
                --crawl ID        crawl ID (default: CC-MAIN-2026-12)
                --format fmt      file formats: wat,wet,warc (default: wat,wet)
                --domains file    domain filter file (default: authority list)
                --workers N       parallel workers (default: 4)
                --range-start N   shard start index
                --range-end N     shard end index
                --wat-only        WAT only shorthand
                --wet-only        WET only shorthand
                --resume          resume from state (default: true)

  graph         WAT → DID property graph
                --crawl ID        crawl ID
                --source src      full or filtered (default: full)
                --domain pat      domain pattern filter (e.g., *.go.jp)
                --output fmt      sql, jsonl, parquet (default: sql)
                --batch-size N    pages per file (default: 5000)

  intel         Murakumo intelligence extraction → knowledge graph
                --model name      LLM model (default: qwen3.5-9b)
                --limit N         max domains (0=all)
                --min-pages N     only domains with >= N pages
                --domain pat      domain pattern filter
                --output fmt      jsonl, sql, parquet (default: jsonl)
                --concurrency N   parallel LLM calls (default: 1)
                --resume          resume from state

  inject        Deprecated alias for 'gftd domain-ingest common-crawl'

  list-crawls   List available Common Crawl archives
                --year N          filter by year
                --json            JSON output

  monitor       Pipeline status dashboard
  status        Alias for monitor
  purge         Clean state (--phase download|graph|intel|all)

ENVIRONMENT:
  CC_DATA_DIR       data directory (default: /Volumes/251220/CC/2603)
  CC_CRAWL_ID       crawl ID override
  MURAKUMO_URL      fleet URL (default: https://murakumo.etzhayyim.com)
  MURAKUMO_MODEL    LLM model override
  MURAKUMO_API_KEY  fleet API key

XRPC (common-crawl.etzhayyim.com):
  ai.gftd.apps.commonCrawler.startDownload   — start/resume download job
  ai.gftd.apps.commonCrawler.startGraph      — start graph generation
  ai.gftd.apps.commonCrawler.startIntel      — start intelligence extraction
  ai.gftd.apps.commonCrawler.startInject     — start DID injection
  ai.gftd.apps.commonCrawler.getStatus       — pipeline status
  ai.gftd.apps.commonCrawler.listCrawls      — available CC archives
  ai.gftd.apps.commonCrawler.getDomainIntel  — get extracted intel for domain

BOUNDARY:
  common-crawler   acquisition / graph extraction / intel generation
  domain-ingest    normalization / enrichment / canonical writes to PDS
  coverage domain  live reconciliation from mv_domain_coverage_live

EXAMPLES:
  gftd common-crawler download --crawl CC-MAIN-2026-12 --workers 8
  gftd common-crawler download --domains my-domains.txt --format wat
  gftd common-crawler download --range-start 0 --range-end 50000
  gftd common-crawler graph --domain "*.go.jp" --output jsonl
  gftd common-crawler intel --limit 5000 --min-pages 100 --resume
  gftd common-crawler intel --model qwen3.5-9b --domain "*.gov"
  gftd domain-ingest common-crawl --dry-run
  gftd common-crawler list-crawls --year 2026
  gftd common-crawler status
`)
	return nil
}
