package main

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"math"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"
	"time"
)

type codeQualityCheck struct {
	Name      string  `json:"name"`
	Tool      string  `json:"tool"`
	Available bool    `json:"available"`
	Score     float64 `json:"score"`
	Issues    int     `json:"issues"`
	Details   string  `json:"details,omitempty"`
	Error     string  `json:"error,omitempty"`
}

type codeQualityReport struct {
	EvaluatedAt    string             `json:"evaluated_at"`
	OverallScore   float64            `json:"overall_score"`
	AvailableTools int                `json:"available_tools"`
	SkippedTools   int                `json:"skipped_tools"`
	Checks         []codeQualityCheck `json:"checks"`
	ScoringModel   string             `json:"scoring_model"`
}

// codeQualityFlatRow is the Parquet-serialisable flat record for one code-quality snapshot.
type codeQualityFlatRow struct {
	CheckedAt       string  `json:"checked_at"`
	OverallScore    float64 `json:"overall_score"`
	AvailableTools  int     `json:"available_tools"`
	CargoMachete    float64 `json:"cargo_machete"`
	CargoDuplicates float64 `json:"cargo_duplicates"`
	GoVet           float64 `json:"go_vet"`
	GoModTidy       float64 `json:"go_mod_tidy"`
	JscpdClones     float64 `json:"jscpd_clones"`
	MagatamaLint    float64 `json:"magatama_lint"`
	FrontendLint    float64 `json:"frontend_lint"`
	PerfTest        float64 `json:"perf_test"`
	SqlInjection float64 `json:"sql_injection"`
	SqlFullScan  float64 `json:"sql_full_scan"`
	DomainCoverage  float64 `json:"domain_coverage"`
	DeadExports     float64 `json:"dead_exports"`
}

func storeCodeQualityResults(wsRoot string, report *codeQualityReport) error {
	row := codeQualityFlatRow{
		CheckedAt:      report.EvaluatedAt,
		OverallScore:   report.OverallScore,
		AvailableTools: report.AvailableTools,
	}
	for _, c := range report.Checks {
		switch c.Name {
		case "cargo_machete":
			row.CargoMachete = c.Score
		case "cargo_duplicates":
			row.CargoDuplicates = c.Score
		case "go_vet":
			row.GoVet = c.Score
		case "go_mod_tidy":
			row.GoModTidy = c.Score
		case "jscpd_clones":
			row.JscpdClones = c.Score
		case "magatama_lint":
			row.MagatamaLint = c.Score
		case "frontend_lint":
			row.FrontendLint = c.Score
		case "perf_test":
			row.PerfTest = c.Score
		case "sql_injection":
			row.SqlInjection = c.Score
		case "sql_full_scan":
			row.SqlFullScan = c.Score
		case "domain_coverage":
			row.DomainCoverage = c.Score
		case "dead_exports":
			row.DeadExports = c.Score
		}
	}
	summary := fmt.Sprintf("score=%.1f tools=%d", report.OverallScore, report.AvailableTools)
	path, err := storeParquet(wsRoot, "code-quality", summary, []codeQualityFlatRow{row})
	if err != nil {
		return err
	}
	fmt.Fprintf(os.Stderr, "code-quality: stored %s\n", path)
	return nil
}

func runCodeQuality(args []string) error {
	fs := flag.NewFlagSet("code-quality", flag.ContinueOnError)
	workspaceDir := fs.String("workspace-dir", "", "workspace root (default: git root)")
	rustDir := fs.String("rust-dir", "", "rust packages dir (default: {workspace}/20-actors/magatama)")
	goDir := fs.String("go-dir", "", "go packages dir (default: {workspace}/70-tools/gftd)")
	tsDir := fs.String("ts-dir", "", "ts packages dir (default: {workspace}/20-actors)")
	skip := fs.String("skip", "", "comma-separated list of tools to skip")
	jsonOut := fs.Bool("json", false, "output as JSON")
	store := fs.Bool("store", false, "store results as Parquet snapshot in 80-data/code-quality/")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	// Resolve workspace root
	wsRoot := *workspaceDir
	if wsRoot == "" {
		cwd, err := os.Getwd()
		if err != nil {
			return fmt.Errorf("getwd: %w", err)
		}
		wsRoot, err = findGitRoot(cwd)
		if err != nil {
			return fmt.Errorf("detect workspace root: %w", err)
		}
	}
	wsRoot, _ = filepath.Abs(wsRoot)

	rDir := *rustDir
	if rDir == "" {
		rDir = filepath.Join(wsRoot, "packages", "rust")
	}
	gDir := *goDir
	if gDir == "" {
		gDir = filepath.Join(wsRoot, "packages", "go")
	}
	tDir := *tsDir
	if tDir == "" {
		tDir = filepath.Join(wsRoot, "packages", "ts")
	}

	skipSet := make(map[string]bool)
	if *skip != "" {
		for _, s := range strings.Split(*skip, ",") {
			skipSet[strings.TrimSpace(s)] = true
		}
	}

	type checkFunc func() codeQualityCheck
	checks := []struct {
		name string
		fn   checkFunc
	}{
		{"cargo_machete", func() codeQualityCheck { return checkCargoMachete(rDir) }},
		{"cargo_duplicates", func() codeQualityCheck { return checkCargoDuplicates(rDir) }},
		{"go_vet", func() codeQualityCheck { return checkGoVet(gDir) }},
		{"go_mod_tidy", func() codeQualityCheck { return checkGoModTidy(gDir) }},
		{"jscpd_clones", func() codeQualityCheck { return checkJscpd(wsRoot, rDir, tDir) }},
		{"magatama_lint", func() codeQualityCheck { return checkMagatamaLint(wsRoot) }},
		{"frontend_lint", func() codeQualityCheck { return checkFrontendLint(wsRoot) }},
		{"perf_test", func() codeQualityCheck { return checkPerfTest(wsRoot) }},
		{"sql_injection", func() codeQualityCheck { return checkSqlInjection(wsRoot) }},
		{"sql_full_scan", func() codeQualityCheck { return checkSqlFullScan(wsRoot) }},
		{"large_table_count_star", func() codeQualityCheck { return checkLargeTableCountStar(wsRoot) }},
		{"domain_coverage", func() codeQualityCheck { return checkDomainCoverage(wsRoot) }},
		{"dead_exports", func() codeQualityCheck { return checkDeadExports(wsRoot) }},
	}

	var results []codeQualityCheck
	available := 0
	skipped := 0
	for _, c := range checks {
		if skipSet[c.name] {
			skipped++
			continue
		}
		result := c.fn()
		results = append(results, result)
		if result.Available {
			available++
		}
	}

	// Aggregate score: average of available tool scores
	var scoreSum float64
	scored := 0
	var scoredNames []string
	for _, r := range results {
		if r.Available && r.Error == "" {
			scoreSum += r.Score
			scored++
			scoredNames = append(scoredNames, r.Name)
		}
	}
	overall := 0.0
	if scored > 0 {
		overall = scoreSum / float64(scored)
	}

	report := codeQualityReport{
		EvaluatedAt:    time.Now().UTC().Format(time.RFC3339),
		OverallScore:   overall,
		AvailableTools: available,
		SkippedTools:   skipped,
		Checks:         results,
		ScoringModel:   fmt.Sprintf("average of available tool scores (%s)", strings.Join(scoredNames, " + ")),
	}

	if *store {
		if err := storeCodeQualityResults(wsRoot, &report); err != nil {
			fmt.Fprintf(os.Stderr, "code-quality store warning: %v\n", err)
		}
	}

	if *jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(report)
	}

	printCodeQualityText(&report)
	return nil
}

func printCodeQualityText(r *codeQualityReport) {
	fmt.Printf("code_quality:\n")
	fmt.Printf("  evaluated_at: %s\n", r.EvaluatedAt)
	fmt.Printf("  overall_score: %.1f\n", r.OverallScore)
	fmt.Printf("  available_tools: %d\n", r.AvailableTools)
	fmt.Printf("  skipped_tools: %d\n", r.SkippedTools)
	fmt.Printf("  checks:\n")
	for _, c := range r.Checks {
		fmt.Printf("    %s:\n", c.Name)
		if !c.Available {
			fmt.Printf("      available: false\n")
			fmt.Printf("      hint: %s\n", cqInstallHint(c.Name))
			continue
		}
		fmt.Printf("      score: %.1f\n", c.Score)
		fmt.Printf("      issues: %d\n", c.Issues)
		if c.Details != "" {
			fmt.Printf("      details: %q\n", c.Details)
		}
		if c.Error != "" {
			fmt.Printf("      error: %q\n", c.Error)
		}
	}
	fmt.Printf("  scoring_model: %q\n", r.ScoringModel)
}

func cqInstallHint(name string) string {
	switch name {
	case "cargo_machete":
		return "cargo install cargo-machete"
	case "cargo_duplicates":
		return "cargo is required (cargo tree -d)"
	case "go_vet":
		return "go is required (go vet)"
	case "go_mod_tidy":
		return "go 1.23+ required (go mod tidy -diff)"
	case "jscpd_clones":
		return "npx is required (npm install -g jscpd)"
	case "magatama_lint":
		return "no external tools required (scans projects/*/wasm/*/main.go)"
	case "frontend_lint":
		return "no external tools required (scans projects/*/svelte/src/**/*.{svelte,ts})"
	case "perf_test":
		return "npx playwright test (requires @playwright/test)"
	case "dead_exports":
		return "node + rg (ripgrep) required — runs 70-tools/scripts/lint/dead-exports.mjs"
	default:
		return ""
	}
}

// cap01 clamps a score to [0, 100].
func cqCap(score float64) float64 {
	if score < 0 {
		return 0
	}
	if score > 100 {
		return 100
	}
	return score
}

// findCargoWorkspaces returns directories containing Cargo.toml with [workspace] under rustDir.
func findCargoWorkspaces(rustDir string) []string {
	entries, err := os.ReadDir(rustDir)
	if err != nil {
		return nil
	}
	var dirs []string
	for _, e := range entries {
		if !e.IsDir() {
			continue
		}
		cargoPath := filepath.Join(rustDir, e.Name(), "Cargo.toml")
		data, err := os.ReadFile(cargoPath)
		if err != nil {
			continue
		}
		if bytes.Contains(data, []byte("[workspace]")) {
			dirs = append(dirs, filepath.Join(rustDir, e.Name()))
		}
	}
	return dirs
}

func checkCargoMachete(rustDir string) codeQualityCheck {
	check := codeQualityCheck{
		Name: "cargo_machete",
		Tool: "cargo-machete",
	}

	if _, err := exec.LookPath("cargo-machete"); err != nil {
		if _, err2 := exec.LookPath("cargo"); err2 != nil {
			check.Available = false
			return check
		}
		// cargo-machete might be a cargo subcommand
		ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
		defer cancel()
		out, err := exec.CommandContext(ctx, "cargo", "machete", "--help").CombinedOutput()
		if err != nil && !bytes.Contains(out, []byte("machete")) {
			check.Available = false
			return check
		}
	}
	check.Available = true

	workspaces := findCargoWorkspaces(rustDir)
	if len(workspaces) == 0 {
		check.Score = 100
		check.Details = "no cargo workspaces found"
		return check
	}

	totalUnused := 0
	var detailParts []string
	for _, ws := range workspaces {
		ctx, cancel := context.WithTimeout(context.Background(), 120*time.Second)
		cmd := exec.CommandContext(ctx, "cargo", "machete", "--with-metadata", "--skip-target-dir")
		cmd.Dir = ws
		out, err := cmd.CombinedOutput()
		cancel()

		wsName := filepath.Base(ws)
		if err != nil {
			// cargo-machete exits non-zero when unused deps are found
			lines := strings.Split(string(out), "\n")
			count := 0
			for _, line := range lines {
				// Unused dep lines start with \t (tab-indented crate name)
				if strings.HasPrefix(line, "\t") {
					count++
				}
			}
			totalUnused += count
			if count > 0 {
				detailParts = append(detailParts, fmt.Sprintf("%d unused in %s", count, wsName))
			}
		}
	}

	check.Issues = totalUnused
	// 3 points per unused dep (dev-deps like tempfile/tower are expected)
	check.Score = cqCap(100 - float64(totalUnused)*3)
	if len(detailParts) > 0 {
		check.Details = strings.Join(detailParts, ", ")
	}
	return check
}

func checkCargoDuplicates(rustDir string) codeQualityCheck {
	check := codeQualityCheck{
		Name: "cargo_duplicates",
		Tool: "cargo tree -d",
	}

	if _, err := exec.LookPath("cargo"); err != nil {
		check.Available = false
		return check
	}
	check.Available = true

	workspaces := findCargoWorkspaces(rustDir)
	if len(workspaces) == 0 {
		check.Score = 100
		check.Details = "no cargo workspaces found"
		return check
	}

	// Match crate name lines like "crate_name v1.2.3"
	crateLineRe := regexp.MustCompile(`^([a-zA-Z0-9_-]+)\s+v`)
	dupCrates := make(map[string]bool)

	for _, ws := range workspaces {
		ctx, cancel := context.WithTimeout(context.Background(), 120*time.Second)
		cmd := exec.CommandContext(ctx, "cargo", "tree", "-d", "--workspace")
		cmd.Dir = ws
		out, err := cmd.CombinedOutput()
		cancel()

		if err != nil {
			// cargo tree -d may exit non-zero; parse output anyway
			_ = err
		}
		lines := strings.Split(string(out), "\n")
		for _, line := range lines {
			line = strings.TrimSpace(line)
			if m := crateLineRe.FindStringSubmatch(line); m != nil {
				dupCrates[m[1]] = true
			}
		}
	}

	duplicateCount := len(dupCrates)
	check.Issues = duplicateCount
	// Transitive duplicates are common and hard to control (wasmtime, arrow, etc.)
	// Use sqrt penalty: score = 100 - 10*sqrt(count)
	// 0 dupes = 100, 1 = 90, 4 = 80, 9 = 70, 16 = 60, 25 = 50, 36 = 40, 49 = 30, 64 = 20
	if duplicateCount > 0 {
		penalty := 10.0 * math.Sqrt(float64(duplicateCount))
		check.Score = cqCap(100 - penalty)
		check.Details = fmt.Sprintf("%d duplicate crates across workspaces", duplicateCount)
	} else {
		check.Score = 100
	}
	return check
}

func checkGoVet(goDir string) codeQualityCheck {
	check := codeQualityCheck{
		Name: "go_vet",
		Tool: "go vet",
	}

	if _, err := exec.LookPath("go"); err != nil {
		check.Available = false
		return check
	}
	check.Available = true

	// Find go.mod files under goDir
	goModDirs := findGoModDirs(goDir)
	if len(goModDirs) == 0 {
		check.Score = 100
		check.Details = "no go modules found"
		return check
	}

	totalIssues := 0
	for _, dir := range goModDirs {
		ctx, cancel := context.WithTimeout(context.Background(), 120*time.Second)
		cmd := exec.CommandContext(ctx, "go", "vet", "./...")
		cmd.Dir = dir
		out, err := cmd.CombinedOutput()
		cancel()

		if err != nil {
			lines := strings.Split(string(out), "\n")
			for _, line := range lines {
				line = strings.TrimSpace(line)
				if line != "" && !strings.HasPrefix(line, "#") &&
					!strings.Contains(line, "matched no packages") &&
					!strings.HasPrefix(line, "go: warning:") &&
					!strings.HasPrefix(line, "no packages") {
					totalIssues++
				}
			}
		}
	}

	check.Issues = totalIssues
	check.Score = cqCap(100 - float64(totalIssues)*10)
	if totalIssues > 0 {
		check.Details = fmt.Sprintf("%d vet issues across go modules", totalIssues)
	}
	return check
}

func checkGoModTidy(goDir string) codeQualityCheck {
	check := codeQualityCheck{
		Name: "go_mod_tidy",
		Tool: "go mod tidy -diff",
	}

	if _, err := exec.LookPath("go"); err != nil {
		check.Available = false
		return check
	}
	check.Available = true

	goModDirs := findGoModDirs(goDir)
	if len(goModDirs) == 0 {
		check.Score = 100
		check.Details = "no go modules found"
		return check
	}

	clean := 0
	dirty := 0
	var dirtyNames []string
	for _, dir := range goModDirs {
		ctx, cancel := context.WithTimeout(context.Background(), 120*time.Second)
		cmd := exec.CommandContext(ctx, "go", "mod", "tidy", "-diff")
		cmd.Dir = dir
		out, err := cmd.CombinedOutput()
		cancel()

		if err != nil || len(bytes.TrimSpace(out)) > 0 {
			dirty++
			dirtyNames = append(dirtyNames, filepath.Base(dir))
		} else {
			clean++
		}
	}

	total := clean + dirty
	if total > 0 {
		check.Score = float64(clean) / float64(total) * 100
	}
	check.Issues = dirty
	if dirty > 0 {
		check.Details = fmt.Sprintf("%d/%d modules dirty: %s", dirty, total, strings.Join(dirtyNames, ", "))
	}
	return check
}

func checkJscpd(workspaceDir, rustDir, tsDir string) codeQualityCheck {
	check := codeQualityCheck{
		Name: "jscpd_clones",
		Tool: "jscpd",
	}

	if _, err := exec.LookPath("npx"); err != nil {
		check.Available = false
		return check
	}
	check.Available = true

	// Build scan paths relative to workspace
	var scanPaths []string
	for _, candidate := range []string{
		rustDir,
		tsDir,
		filepath.Join(workspaceDir, "infra", "cloudflare", "templates"),
	} {
		if _, err := os.Stat(candidate); err == nil {
			rel, err := filepath.Rel(workspaceDir, candidate)
			if err == nil {
				scanPaths = append(scanPaths, rel)
			} else {
				scanPaths = append(scanPaths, candidate)
			}
		}
	}
	if len(scanPaths) == 0 {
		check.Score = 100
		check.Details = "no scan paths found"
		return check
	}

	cmdArgs := []string{"jscpd",
		"--min-lines", "5",
		"--min-tokens", "50",
		"--reporters", "json",
		"--ignore", "node_modules,target,.cargo-target,*.wasm",
	}
	cmdArgs = append(cmdArgs, scanPaths...)

	ctx, cancel := context.WithTimeout(context.Background(), 300*time.Second)
	defer cancel()

	cmd := exec.CommandContext(ctx, "npx", cmdArgs...)
	cmd.Dir = workspaceDir
	out, err := cmd.CombinedOutput()
	if err != nil {
		// jscpd may exit non-zero if clones found; try parsing output
		_ = err
	}

	// Parse JSON output — look for statistics.total.percentage
	clonePct := parseJscpdPercentage(out)
	if clonePct < 0 {
		check.Error = "failed to parse jscpd output"
		check.Score = 0
		return check
	}

	check.Score = cqCap(100 - clonePct)
	if clonePct > 0 {
		check.Details = fmt.Sprintf("%.1f%% code duplication detected", clonePct)
	}
	return check
}

// parseJscpdPercentage extracts the total clone percentage from jscpd JSON output.
func parseJscpdPercentage(output []byte) float64 {
	// jscpd JSON output contains statistics.total.percentage
	// Try to find JSON object in output (may have non-JSON prefix)
	idx := bytes.Index(output, []byte("{"))
	if idx < 0 {
		return -1
	}

	var parsed struct {
		Statistics struct {
			Total struct {
				Percentage    float64 `json:"percentage"`
				PercentageStr string  `json:"percentageStr"`
			} `json:"total"`
		} `json:"statistics"`
	}

	if err := json.Unmarshal(output[idx:], &parsed); err != nil {
		// Try line by line — jscpd sometimes outputs multiple JSON objects
		lines := bytes.Split(output, []byte("\n"))
		for _, line := range lines {
			line = bytes.TrimSpace(line)
			if len(line) == 0 || line[0] != '{' {
				continue
			}
			if err := json.Unmarshal(line, &parsed); err == nil && parsed.Statistics.Total.Percentage > 0 {
				return parsed.Statistics.Total.Percentage
			}
		}

		// Fallback: regex for percentage
		re := regexp.MustCompile(`"percentage"\s*:\s*([0-9.]+)`)
		m := re.FindSubmatch(output)
		if m != nil {
			if v, err := strconv.ParseFloat(string(m[1]), 64); err == nil {
				return v
			}
		}
		return -1
	}

	return parsed.Statistics.Total.Percentage
}

// findGoModDirs finds directories containing go.mod under the given root.
func findGoModDirs(root string) []string {
	var dirs []string
	_ = filepath.WalkDir(root, func(path string, d os.DirEntry, err error) error {
		if err != nil {
			return nil
		}
		if d.IsDir() {
			base := d.Name()
			if base == "node_modules" || base == "vendor" || base == ".git" || base == "target" || base == ".cargo-target" {
				return filepath.SkipDir
			}
			return nil
		}
		if d.Name() == "go.mod" {
			dirs = append(dirs, filepath.Dir(path))
		}
		return nil
	})
	return dirs
}

func printCodeQualityUsage() {
	fmt.Print(`gftd code-quality — run code quality tools and produce a unified score report

USAGE:
  gftd code-quality [flags]

FLAGS:
  --workspace-dir    workspace root (default: git root)
  --rust-dir         rust packages dir (default: {workspace}/20-actors/magatama)
  --go-dir           go packages dir (default: {workspace}/70-tools/gftd)
  --ts-dir           ts packages dir (default: {workspace}/20-actors)
  --skip             comma-separated list of tools to skip
                     (cargo_machete, cargo_duplicates, go_vet, go_mod_tidy, jscpd_clones, magatama_lint, frontend_lint, perf_test)
  --json             output as JSON instead of YAML-like text

TOOLS:
  cargo_machete      unused dependency detection (cargo-machete)
  cargo_duplicates   duplicate crate detection (cargo tree -d)
  go_vet             Go static analysis (go vet)
  go_mod_tidy        Go module tidiness (go mod tidy -diff)
  jscpd_clones       code clone detection (jscpd)
  magatama_lint      App standard compliance (legacy pattern detection in main.go)
  frontend_lint      Design E compliance (legacy data access in .svelte/.ts)
  perf_test          performance test coverage (Playwright budget assertions)
`)
}

// magatamaLintRule defines a single lint rule for App main.go files.
type magatamaLintRule struct {
	ID          string
	Severity    string // critical, high, medium, low
	Weight      float64
	Pattern     *regexp.Regexp
	Exclude     *regexp.Regexp // if line matches Exclude, skip the violation
	FileExclude *regexp.Regexp // if file content matches FileExclude, skip entire file for this rule
	FileInclude *regexp.Regexp // if set, only apply rule when file path matches
	Message     string
}

var didWebInterpolationPattern = regexp.MustCompile(`did:web:\$\{([^}]+)\}`)

func normalizeInlineExpr(expr string) string {
	return strings.Join(strings.Fields(strings.TrimSpace(expr)), "")
}

func countDidDoublePrefixViolations(content string, allowedExprs []string) int {
	allowed := make(map[string]struct{}, len(allowedExprs))
	for _, expr := range allowedExprs {
		allowed[normalizeInlineExpr(expr)] = struct{}{}
	}

	violations := 0
	matches := didWebInterpolationPattern.FindAllStringSubmatchIndex(content, -1)
	for _, match := range matches {
		if len(match) < 4 {
			continue
		}
		expr := normalizeInlineExpr(content[match[2]:match[3]])
		if expr == "" {
			continue
		}
		if _, ok := allowed[expr]; ok {
			continue
		}

		windowStart := match[0] - 120
		if windowStart < 0 {
			windowStart = 0
		}
		windowEnd := match[1] + 120
		if windowEnd > len(content) {
			windowEnd = len(content)
		}
		window := normalizeInlineExpr(content[windowStart:windowEnd])
		if strings.Contains(window, "ensureDid("+expr+")") {
			continue
		}
		if strings.Contains(window, expr+".startsWith(\"did:\")") || strings.Contains(window, expr+".startsWith('did:')") {
			continue
		}
		violations++
	}
	return violations
}

// checkMagatamaLint scans projects/*/wasm/*/main.go and src/app.ts for legacy/non-standard patterns.
func checkMagatamaLint(wsRoot string) codeQualityCheck {
	check := codeQualityCheck{
		Name: "magatama_lint",
		Tool: "magatama-lint (built-in)",
	}
	check.Available = true

	projectsDir := filepath.Join(wsRoot, "projects")
	appsDir := filepath.Join(wsRoot, "60-apps")
	hasProjectsDir := false
	if st, err := os.Stat(projectsDir); err == nil && st.IsDir() {
		hasProjectsDir = true
	}
	hasAppsDir := false
	if st, err := os.Stat(appsDir); err == nil && st.IsDir() {
		hasAppsDir = true
	}
	if !hasProjectsDir && !hasAppsDir {
		check.Score = 100
		check.Details = "no projects/ or 60-apps/ directory found"
		return check
	}

	rules := []magatamaLintRule{
		{ID: "init-schema", Severity: "critical", Weight: 3.0,
			Pattern: regexp.MustCompile(`(?i)CREATE\s+TABLE|func\s+initSchema\b`),
			Message: "DDL/initSchema abolished — yata is schemaless"},
		{ID: "sql-write", Severity: "critical", Weight: 2.0,
			Pattern: regexp.MustCompile(`Q\(""\)\.Exec\("(?:INSERT|UPDATE|DELETE|MERGE)`),
			Message: "direct SQL write — use ComAtprotoRepoCreateRecord()/ComAtprotoRepoPutRecord()"},
		{ID: "legacy-namespace", Severity: "high", Weight: 2.0,
			Pattern: regexp.MustCompile(`ai\.gftd\.messaging\.|ai\.gftd\.platform\.|ai\.gftd\.w\.`),
			Message: "deprecated lexicon namespace — use ai.gftd.apps.* or app.bsky.*"},
		{ID: "wsend-social", Severity: "high", Weight: 1.5,
			Pattern: regexp.MustCompile(`\bWSend\b`),
			Message: "WSend for social — use AppBskyFeedPostAs/ATLike/ATRepost/Follow, WRecord for data"},
		{ID: "http-client", Severity: "high", Weight: 1.5,
			Pattern: regexp.MustCompile(`http\.Client\{|http\.DefaultClient`),
			Message: "direct http.Client — use magatama.Send()"},
		{ID: "os-getenv", Severity: "high", Weight: 1.5,
			Pattern: regexp.MustCompile(`os\.Getenv\(`),
			Message: "os.Getenv — use magatama.ConfigGet()"},
		{ID: "kv-usage", Severity: "critical", Weight: 3.0,
			Pattern: regexp.MustCompile(`\bKvGet\b|\bKvPut\b`),
			Message: "KV access prohibited — use W Protocol Event Stream"},
		{ID: "dosqlexec", Severity: "critical", Weight: 3.0,
			Pattern: regexp.MustCompile(`\bDOSqlExec\b`),
			Message: "DOSqlExec prohibited — use G() for read, ComAtprotoRepoCreateRecord() for write"},
		{ID: "performer-alias", Severity: "medium", Weight: 1.0,
			Pattern: regexp.MustCompile(`performer\s+"github\.com/gftdcojp/magatama-go"`),
			Message: "stale import alias — rename performer to magatama"},
		{ID: "external-llm-default", Severity: "medium", Weight: 1.0,
			Pattern: regexp.MustCompile(`openrouter\.ai/api|api\.openai\.com`),
			Message: "external LLM default — use mod.etzhayyim.com"},
		{ID: "missing-serve", Severity: "medium", Weight: 1.0,
			Pattern: regexp.MustCompile(`magatama\.NewApp\(`),
			Message: "NewApp without app.Serve() — add app.Serve() in init()"},
		{ID: "pds-hardcode", Severity: "critical", Weight: 3.0,
			Pattern: regexp.MustCompile(`(?:appId|app_id)\s*[:=]\s*"pds"|mergeRecord\([^)]*"pds"\s*\)|sql\([^)]*"pds"\s*\)|mutate\([^)]*"pds"\s*\)`),
			Message: "appId 'pds' hardcode — use repo-derived appId (extractAppId). 'pds' is shared namespace only"},
		{ID: "raw-sql-exec", Severity: "critical", Weight: 3.0,
			Pattern: regexp.MustCompile(`SqlExec\(|SqlSuspend`),
			Message: "SqlExec/SqlSuspend prohibited — use G() builder for read, ComAtprotoRepoCreateRecord() for write"},
		{ID: "raw-sql-query", Severity: "high", Weight: 2.0,
			Pattern: regexp.MustCompile(`SqlQueryMap\(`),
			Message: "SqlQueryMap prohibited — use G().Match().Return().Query() builder"},
		{ID: "raw-sql-string", Severity: "high", Weight: 2.0,
			Pattern:     regexp.MustCompile(`"MATCH\s*\(`),
			FileExclude: regexp.MustCompile(`func (?:gqRaw|sqlQuery|dq|doQuery)\b|func safeLabel\(|sqlQueryAsync`),
			Message:     "raw Sql string literal — use G().Match() builder or Q().QueryRaw()"},
		{ID: "sql-sprintf", Severity: "critical", Weight: 3.0,
			Pattern:     regexp.MustCompile(`Sprintf\(.*(?:MATCH|MERGE|CREATE|DELETE)\s*\(`),
			Message:     "fmt.Sprintf with Sql — injection risk, use parameterized $param or G() builder",
			FileExclude: regexp.MustCompile(`func safeLabel\(`)},
		{ID: "kebab-collection", Severity: "high", Weight: 2.0,
			Pattern: regexp.MustCompile(`(?:WRecord(?:Update|Delete)?|DIDWrite|ComAtprotoRepoCreateRecord|ComAtprotoRepoPutRecord)\("[a-z]+-[a-z]|Q\("[a-z]+-[a-z]`),
			Message: "kebab-case collection/kind — use camelCase (AT Protocol standard)"},
		{ID: "kebab-command", Severity: "high", Weight: 2.0,
			Pattern: regexp.MustCompile(`\.command\("[a-z]+-[a-z]`),
			Message: "kebab-case command name — use camelCase (MCP tool name, XRPC NSID derived)"},
		{ID: "snake-collection", Severity: "info", Weight: 0.0,
			Pattern: regexp.MustCompile(`(?:ComAtprotoRepoCreateRecord|ComAtprotoRepoPutRecord|sdk\.pds\.createRecord|sdk\.pds\.dispatch)\("[a-z]+_[a-z]`),
			Message: "snake_case collection/kind — use camelCase (AT Protocol standard)"},
		{ID: "gexecraw-write", Severity: "critical", Weight: 3.0,
			Pattern: regexp.MustCompile(`GExecRaw\(.*(?:INSERT|UPDATE|DELETE|MERGE|CREATE\s+TABLE|DROP\s+TABLE)`),
			Exclude: regexp.MustCompile(`^\s*//`),
			Message: "GExecRaw write prohibited — use ComAtprotoRepoCreateRecord() for domain write, G() builder for read"},
		{ID: "gexecraw-usage", Severity: "info", Weight: 0.0,
			Pattern: regexp.MustCompile(`\bGExecRaw\(`),
			Message: "GExecRaw usage — prefer G() builder for read, ComAtprotoRepoCreateRecord()/ComAtprotoRepoPutRecord() for write"},
		{ID: "legacy-wrecord", Severity: "high", Weight: 2.0,
			Pattern: regexp.MustCompile(`\bWRecord\(|\bWUpdate\(|\bWDelete\(`),
			Message: "legacy WRecord/WUpdate/WDelete — use ComAtprotoRepoCreateRecord()/ComAtprotoRepoPutRecord()/ComAtprotoRepoDeleteRecord() (AT Protocol aligned)"},
		{ID: "legacy-d1-query", Severity: "info", Weight: 0.0,
			Pattern: regexp.MustCompile(`\bd1QueryRow\b|\bd1QueryRows\b`),
			Message: "legacy D1 query helper — use G() builder: G(\"Label\").Match(Eq{...}).Return(...).Query()"},
		{ID: "gqueryraw-usage", Severity: "info", Weight: 0.0,
			Pattern: regexp.MustCompile(`\bGQueryRaw\(`),
			Message: "GQueryRaw usage — prefer G() builder for type-safe reads"},
		{ID: "dot-collection", Severity: "high", Weight: 2.0,
			Pattern: regexp.MustCompile(`(?:ComAtprotoRepoCreateRecord|ComAtprotoRepoPutRecord|WRecord)\("[a-z]+\.[a-z]`),
			Message: "dot-separated collection (oshi.video) — use camelCase (oshiVideo)"},
		{ID: "did-double-prefix", Severity: "high", Weight: 2.0,
			Message: "did:web:${var} without startsWith(\"did:\") guard — allow only appId/nanoid or use ensureDid(var)"},
		{ID: "xrpc-usage", Severity: "info", Weight: 0.0,
			Pattern: regexp.MustCompile(`/xrpc/|xrpc\.`),
			Message: "XRPC is the sole API surface — /xrpc/{NSID} (AT Protocol native)"},
		{ID: "batch-polling", Severity: "high", Weight: 2.0,
			Pattern: regexp.MustCompile(`\bcmdEvaluateBatch\b|\bcmdTranslateToAll\b|\bcmdScanAll\b|\bcmdCrawlAll\b`),
			Message: "batch polling (Design A) prohibited — use HandleWCommit reactive pipeline (Design E)"},
		{ID: "dual-write", Severity: "high", Weight: 2.0,
			Pattern: regexp.MustCompile(`WRecord\(`),
			Message: "WRecord + AppBskyFeedPostAs in same function — Shannon redundancy. Design E: AppBskyFeedPostAs for social, WRecord for domain data (separate concerns)"},
		{ID: "domain-data-social-mix", Severity: "critical", Weight: 3.0,
			Pattern: regexp.MustCompile(`(?:AppBskyFeedPostAs|AppBskyFeedPostAs)\([^)]*(?:risk_score|cohort_person|compliance_rule|audit_log|internal_state|evolution_checkpoint|heartbeat_log|preference)`),
			Message: "domain/internal data in AppBskyFeedPostAs — Design E violation: AppBskyFeedPostAs is for public social posts only (AT Repo = always public). Use ComAtprotoRepoCreateRecord() for domain data, Preferences() for state"},
		{ID: "social-via-domain-write", Severity: "high", Weight: 2.0,
			Pattern: regexp.MustCompile(`(?:WRecord|ComAtprotoRepoCreateRecord)\([^)]*(?:"post"|"like"|"repost"|"follow")\b`),
			Message: "social action via domain write — Design E: use AppBskyFeedPost/AppBskyFeedLike/Follow for social (AT Record = federable)"},
		{ID: "fallback-impl", Severity: "high", Weight: 2.0,
			Pattern: regexp.MustCompile(`\bfunc\s+fallback[A-Z]\w+\(`),
			Exclude: regexp.MustCompile(`^\s*//`),
			Message: "fallback implementation — returns hardcoded data bypassing real data path. Use G() graph read with proper error handling instead of static fallback"},
		{ID: "stub-impl", Severity: "high", Weight: 2.0,
			Pattern: regexp.MustCompile(`\bvar\s+(?:default|sample|mock|fake|dummy|static)[A-Z]\w+\s*=\s*\[\]`),
			Exclude: regexp.MustCompile(`^\s*//`),
			Message: "stub data — hardcoded static data array used as stub response. Use G() graph read or ComAtprotoRepoCreateRecord() to persist real data"},
		// ── WIT Layer 0/1 naming compliance ──
		{ID: "legacy-wit-commit-handler", Severity: "high", Weight: 2.0,
			Pattern: regexp.MustCompile(`(?:commit-handler|HandleWCommit|HandleComAtprotoSyncSubscribeReposCommit|WCommit\b)`),
			Exclude: regexp.MustCompile(`^\s*//`),
			Message: "legacy WIT name: commit-handler/WCommit/HandleComAtprotoSyncSubscribeReposCommit — use ComAtprotoSyncSubscribeRepos (@nsid com.atproto.sync.subscribeRepos)"},
		{ID: "legacy-wit-channel", Severity: "high", Weight: 2.0,
			Pattern: regexp.MustCompile(`\bwproto/channel\b|WprotoChannelSend\b|WprotoChannelCreate\b`),
			Exclude: regexp.MustCompile(`^\s*//`),
			Message: "legacy WIT name: channel — renamed to convo (@nsid ai.gftd.convo). Use WprotoConvo* functions"},
		{ID: "legacy-wit-did-interface", Severity: "medium", Weight: 1.0,
			Pattern: regexp.MustCompile(`\bwproto/did@`),
			Exclude: regexp.MustCompile(`^\s*//`),
			Message: "legacy WIT name: did — renamed to identity (@nsid com.atproto.identity)"},
		{ID: "legacy-wit-follow-interface", Severity: "medium", Weight: 1.0,
			Pattern: regexp.MustCompile(`\bwproto/follow@`),
			Exclude: regexp.MustCompile(`^\s*//`),
			Message: "legacy WIT name: follow — renamed to social-graph (@nsid app.bsky.graph)"},
		{ID: "legacy-wit-access-control", Severity: "high", Weight: 2.0,
			Pattern: regexp.MustCompile(`\baccess-control\b`),
			Exclude: regexp.MustCompile(`^\s*//|Access-Control-`),
			Message: "legacy WIT name: access-control — renamed to governance (@nsid ai.gftd.governance)"},
		{ID: "legacy-wit-conversation", Severity: "medium", Weight: 1.0,
			Pattern: regexp.MustCompile(`\bwproto/conversation\b`),
			Exclude: regexp.MustCompile(`^\s*//`),
			Message: "legacy WIT name: conversation — merged into convo (@nsid ai.gftd.convo)"},
		{ID: "legacy-trigger-wcommit", Severity: "critical", Weight: 3.0,
			Pattern: regexp.MustCompile(`"wCommit"`),
			Message: "legacy trigger key: wCommit — renamed to subscribeRepos (@nsid com.atproto.sync.subscribeRepos)"},
		{ID: "hardcoded-repo-did", Severity: "critical", Weight: 3.0,
			Pattern: regexp.MustCompile(`repo:\s*"did:web:[a-z]+\.gftd\.ai"`),
			Message: "hardcoded repo DID in write path — use APP_DID or app-specific DID variable"},
		{ID: "vanity-did-repo", Severity: "critical", Weight: 3.0,
			Pattern:     regexp.MustCompile(`(?:const\s+actorDID|actorDID)\s*=\s*"did:web:[a-z]`),
			FileInclude: regexp.MustCompile(`src/app\.ts$`),
			Message:     "vanity domain DID as actorDID — AT Protocol: repo = nanoid DID. Use `did:web:${appNanoid}.etzhayyim.com`"},
		{ID: "vanity-did-postAs", Severity: "critical", Weight: 3.0,
			Pattern:     regexp.MustCompile(`postAs\([^,]*"did:web:[a-z][a-z0-9-]*\.gftd\.ai`),
			FileInclude: regexp.MustCompile(`src/app\.ts$`),
			Message:     "vanity domain DID in postAs() — AT Protocol: repo = nanoid DID. Use selfRepo or path-based nanoid DID from identityCreate()"},
		{ID: "vanity-did-dispatch", Severity: "critical", Weight: 3.0,
			Pattern:     regexp.MustCompile(`did:\s*"did:web:[a-z][a-z0-9-]*\.gftd\.ai"`),
			FileInclude: regexp.MustCompile(`src/app\.ts$`),
			Exclude:     regexp.MustCompile(`invoke\b|Invoke\b`),
			Message:     "vanity domain DID in dispatch payload — AT Protocol: repo = nanoid DID. Use `did:web:${appNanoid}.etzhayyim.com`"},
		{ID: "writebuffer-entries", Severity: "critical", Weight: 3.0,
			Pattern: regexp.MustCompile(`writeBuffer\.entries\(\)`),
			Message: "writeBuffer.entries() — writeBuffer is an array, use .length or spread [...writeBuffer]"},
		{ID: "raw-webassembly-instance", Severity: "high", Weight: 2.0,
			Pattern: regexp.MustCompile(`new\s+WebAssembly\.Instance\(`),
			Exclude: regexp.MustCompile(`^\s*//`),
			Message: "raw WebAssembly.Instance — use jco instantiate() for Component Model WASM (WIT import resolution)"},
		{ID: "host-sdk-import-gap", Severity: "info", Weight: 0.0,
			Pattern: regexp.MustCompile(`'ai-gftd:wrpc/(?:record|governance)'`),
			Message: "legacy host-sdk import key (w-record/w-governance) kept for backward compat — jco expects com-atproto:repo/repo and ai-gftd:governance/governance"},
		{ID: "legacy-enable-social-evolution", Severity: "high", Weight: 2.0,
			Pattern: regexp.MustCompile(`\bEnableSocialEvolution\b`),
			Message: "legacy EnableSocialEvolution — renamed to EnableShinka (ShinkaConfig)"},
		// ── TS native host-sdk helper duplication (app.ts only) ──
		{ID: "hostsdk-dup-encode", Severity: "high", Weight: 2.0,
			Pattern:     regexp.MustCompile(`^function\s+(?:out|toJsonBytes|jb)\s*\(`),
			FileInclude: regexp.MustCompile(`src/app\.ts$`),
			Message:     "local encodeJson duplicate — import { encodeJson } from \"@gftd/magatama-host-sdk\""},
		{ID: "hostsdk-dup-decode", Severity: "high", Weight: 2.0,
			Pattern:     regexp.MustCompile(`^function\s+(?:json|parseBody)\s*[<(]`),
			FileInclude: regexp.MustCompile(`src/app\.ts$`),
			Message:     "local decodeJson duplicate — import { decodeJson } from \"@gftd/magatama-host-sdk\""},
		{ID: "hostsdk-dup-str", Severity: "high", Weight: 2.0,
			Pattern:     regexp.MustCompile(`^function\s+s\(v:\s*unknown\)`),
			FileInclude: regexp.MustCompile(`src/app\.ts$`),
			Message:     "local str() duplicate — import { str } from \"@gftd/magatama-host-sdk\""},
		{ID: "hostsdk-dup-now", Severity: "medium", Weight: 1.0,
			Pattern:     regexp.MustCompile(`^function\s+(?:nowTS|nowISO_local)\s*\(`),
			FileInclude: regexp.MustCompile(`src/app\.ts$`),
			Message:     "local nowISO duplicate — import { nowISO } from \"@gftd/magatama-host-sdk\""},
		{ID: "hostsdk-dup-sql-rows", Severity: "high", Weight: 2.0,
			Pattern:     regexp.MustCompile(`^function\s+(?:sqlQueryRows|sqlRows)\s*\(`),
			FileInclude: regexp.MustCompile(`src/app\.ts$`),
			Message:     "local Sql row parser duplicate — import { parseYataRows } from \"@gftd/magatama-host-sdk\""},
		{ID: "hostsdk-dup-num", Severity: "high", Weight: 2.0,
			Pattern:     regexp.MustCompile(`^function\s+num\((?:v|value):\s*unknown\)`),
			FileInclude: regexp.MustCompile(`src/app\.ts$`),
			Message:     "local num() duplicate — import { num } from \"@gftd/magatama-host-sdk\""},
		{ID: "hostsdk-dup-firstrow", Severity: "high", Weight: 2.0,
			Pattern:     regexp.MustCompile(`^function\s+firstRow\(`),
			FileInclude: regexp.MustCompile(`src/app\.ts$`),
			Message:     "local firstRow() duplicate — import { firstRow } from \"@gftd/magatama-host-sdk\""},
		{ID: "hostsdk-raw-json-parse", Severity: "medium", Weight: 1.0,
			Pattern:     regexp.MustCompile(`JSON\.parse\(str\(body\)\s*\|\|\s*"\{\}"\)`),
			FileInclude: regexp.MustCompile(`src/app\.ts$`),
			Message:     "raw JSON.parse(str(body)) — use decodeJson(body, {}) from \"@gftd/magatama-host-sdk\""},
		{ID: "hostsdk-dup-genid", Severity: "high", Weight: 2.0,
			Pattern:     regexp.MustCompile(`^(?:function\s+genID|function\s+gid)\s*\(`),
			FileInclude: regexp.MustCompile(`src/app\.ts$`),
			Message:     "local genID/gid duplicate — import { genID } from \"@gftd/magatama-host-sdk\""},
		{ID: "hostsdk-dup-rlsdefaults", Severity: "high", Weight: 2.0,
			Pattern:     regexp.MustCompile(`^function\s+rlsDefaults\s*\(`),
			FileInclude: regexp.MustCompile(`src/app\.ts$`),
			Message:     "local rlsDefaults duplicate — import { rlsDefaults } from \"@gftd/magatama-host-sdk\""},
		{ID: "hostsdk-dup-textencoder", Severity: "medium", Weight: 1.0,
			Pattern:     regexp.MustCompile(`^const\s+enc\s*=\s*new\s+TextEncoder\b`),
			FileInclude: regexp.MustCompile(`src/app\.ts$`),
			Message:     "local TextEncoder — use encodeJson() from host-sdk (handles encoding internally)"},
		{ID: "hostsdk-silent-catch", Severity: "high", Weight: 2.0,
			Pattern:     regexp.MustCompile(`catch\s*(?:\([^)]*\))?\s*\{\s*(?://\s*(?:ignore|noop|nothing)|)\s*\}`),
			FileInclude: regexp.MustCompile(`src/app\.ts$`),
			Message:     "silent catch — add console.warn/error (feedback_no_silent_catch rule)"},
		{ID: "hostsdk-writebuffer-push", Severity: "high", Weight: 2.0,
			Pattern:     regexp.MustCompile(`writeBuffer\.push\(\{`),
			FileInclude: regexp.MustCompile(`src/app\.ts$`),
			Message:     "direct writeBuffer.push — use sdk.hostImports.appBskyFeedPostAs/recordWrite/comAtprotoIdentityCreate instead"},
		// ── TS native dead code / duplication / bug detection ──
		{ID: "hostsdk-undefined-querygraph", Severity: "critical", Weight: 3.0,
			Pattern:     regexp.MustCompile(`\bqueryGraph\s*\(`),
			FileInclude: regexp.MustCompile(`src/app\.ts$`),
			Message:     "undefined queryGraph() — import { sqlQueryAsync } from \"@gftd/magatama-host-sdk\" and call directly"},
		{ID: "string-template-bug", Severity: "critical", Weight: 3.0,
			FileInclude: regexp.MustCompile(`src/app\.ts$`),
			Message:     "template literal in regular quotes — use backticks ` instead of \" for string interpolation"},
		{ID: "duplicate-import-line", Severity: "high", Weight: 2.0,
			Pattern:     regexp.MustCompile(`(?m)^import\s+\{[^}]*\}\s+from\s+"@gftd/magatama-host-sdk"\s*;?\s*$`),
			FileInclude: regexp.MustCompile(`src/app\.ts$`),
			Message:     "multiple import lines from same module — consolidate into single import statement"},
		{ID: "command-duplicate-registration", Severity: "high", Weight: 2.0,
			Pattern:     regexp.MustCompile(`\.command\("[a-z_]+",\s*\(ctx,\s*body\)\s*=>[^)]+\)\s*,?\s*\n\s*\.command\(`),
			FileInclude: regexp.MustCompile(`src/app\.ts$`),
			Message:     "duplicate .command() registration (short name + NSID) — use NSID name only"},
		{ID: "dead-function-unreferenced", Severity: "medium", Weight: 1.5,
			FileInclude: regexp.MustCompile(`src/app\.ts$`),
			Message:     "unreferenced function — remove dead code or wire into command/pipeline"},
		// ── magatama.jsonld rules (scanned separately) ──
		{ID: "missing-governance", Severity: "high", Weight: 2.0,
			Message: "magatama.jsonld missing governance block — yoro profile cannot display governance"},
		{ID: "missing-convo-system-prompt", Severity: "high", Weight: 2.0,
			Message: "magatama.jsonld missing convoSystemPrompt — DM agent conversation disabled"},
		{ID: "missing-profile-description", Severity: "high", Weight: 2.0,
			Message: "magatama.jsonld missing profile.description — domain knowledge baseline incomplete"},
		{ID: "missing-profile-capabilities", Severity: "high", Weight: 2.0,
			Message: "magatama.jsonld missing profile.capabilities — domain capability surface incomplete"},
		{ID: "missing-embed-route", Severity: "high", Weight: 2.0,
			Message: "appview app must set embedUrl in magatama.jsonld and provide /embed Hono route"},
		{ID: "deprecated-sveltekit-framework", Severity: "info", Weight: 1.0,
			Message: "SvelteKit is deprecated — migrate to ts-native + Hono /embed route"},
		// ── serve() sync path violations (app.ts) ──
		{ID: "sync-serve-call", Severity: "critical", Weight: 3.0,
			Pattern:     regexp.MustCompile(`sdk\.app\.serve\(\)`),
			FileInclude: regexp.MustCompile(`src/app\.ts$`),
			Message:     "sync serve() call — remove. createWorkerExport() calls serveAsync() with proper await + error handling. Sync serve() uses fire-and-forget dispatch (silent fail)"},
		{ID: "missing-export-default", Severity: "critical", Weight: 3.0,
			FileInclude: regexp.MustCompile(`src/app\.ts$`),
			Message:     "missing export default createWorkerExport() — CF Worker entry point required"},
		// ── Shannon redundancy violations (appId ↔ magatama.jsonld) ──
		{ID: "hardcoded-appid", Severity: "critical", Weight: 3.0,
			Pattern:     regexp.MustCompile(`(?:const|let|var)\s+appId\s*=\s*"[^"]+"`),
			FileInclude: regexp.MustCompile(`src/app\.ts$`),
			Message:     "hardcoded appId — Shannon redundancy (entropy=0). Remove: SDK reads APP_NANOID from env (injected by gftd deploy from magatama.jsonld)"},
		{ID: "hardcoded-actor-did", Severity: "critical", Weight: 3.0,
			Pattern:     regexp.MustCompile(`(?:const|let|var)\s+actorDID\s*=\s*(?:"did:|` + "`" + `did:)`),
			FileInclude: regexp.MustCompile(`src/app\.ts$`),
			Message:     "hardcoded actorDID — derived from appId (Shannon redundancy). Use sdk.pds.selfRepo or env APP_NANOID"},
		{ID: "legacy-create-component-host-sdk", Severity: "high", Weight: 2.0,
			Pattern:     regexp.MustCompile(`function\s+createComponentHostSDK`),
			FileInclude: regexp.MustCompile(`src/app\.ts$`),
			Message:     "legacy createComponentHostSDK factory — use createWorkerExport() (no args). SDK auto-resolves appDef from deploy env vars"},
		{ID: "legacy-hardcoded-appdef", Severity: "high", Weight: 2.0,
			Pattern:     regexp.MustCompile(`appDef:\s*\{\s*id:\s*"`),
			FileInclude: regexp.MustCompile(`src/app\.ts$`),
			Message:     "hardcoded appDef in app.ts — Shannon redundancy. createDefaultHostSDK reads from env vars (magatama.jsonld → gftd deploy → env)"},
		{ID: "payload-string-collection", Severity: "critical", Weight: 3.0,
			Pattern:     regexp.MustCompile(`payload:\s*"ai\.gftd\.`),
			FileInclude: regexp.MustCompile(`src/app\.ts$`),
			Message:     "payload is bare string — use { collection: \"...\", recordJson: JSON.stringify(...) }"},
		{ID: "broken-dispatch-brace", Severity: "critical", Weight: 3.0,
			Pattern:     regexp.MustCompile(`payload:\s*\{\s*text:\s*` + "`[^`]*`" + `\);`),
			FileInclude: regexp.MustCompile(`src/app\.ts$`),
			Message:     "missing closing } in dispatch payload — payload: { text: `...` } });"},
		{ID: "non-async-await", Severity: "critical", Weight: 3.0,
			FileInclude: regexp.MustCompile(`src/app\.ts$`),
			Message:     "non-async function uses await — add async keyword. Await in sync function returns unresolved Promise"},
		// ── XRPC command short name violations (Shannon: full NSID is sole lookup key) ──
		{ID: "command-short-name", Severity: "high", Weight: 2.0,
			Pattern:     regexp.MustCompile(`\.command\(\s*"[a-zA-Z]+"\s*,`),
			FileInclude: regexp.MustCompile(`src/app\.ts$`),
			Message:     "command registered with short name — use full NSID (ai.gftd.apps.{app}.{method}). Host-SDK uses full NSID direct lookup; short names are never matched"},
		// ── autoCrud boilerplate elimination (app.ts only) ──
		{ID: "autocrud-manual-crud", Severity: "high", Weight: 2.0,
			FileInclude: regexp.MustCompile(`src/app\.ts$`),
			Message:     "manual CRUD commands (list/get/search/create) — use sdk.app.autoCrud({ domain, label }) to auto-register standard commands"},
		{ID: "autocrud-manual-heartbeat", Severity: "high", Weight: 2.0,
			Pattern:     regexp.MustCompile(`(?:export\s+(?:async\s+)?function\s+runHeartbeat|resolveHeartbeatCadence\()`),
			FileInclude: regexp.MustCompile(`src/app\.ts$`),
			Message:     "manual runHeartbeat export — SDK handles heartbeat via app.runDefaultHeartbeat(). Use sdk.app.onHeartbeat() hook for domain-specific logic only"},
		{ID: "autocrud-manual-commit-handler", Severity: "high", Weight: 2.0,
			Pattern:     regexp.MustCompile(`export\s+(?:function|async\s+function)\s+handleComAtprotoSyncSubscribeReposCommit`),
			FileInclude: regexp.MustCompile(`src/app\.ts$`),
			Message:     "exported handleComAtprotoSyncSubscribeReposCommit — SDK provides default commit handler. Only export if custom reactive logic needed"},
		{ID: "autocrud-manual-validate", Severity: "high", Weight: 2.0,
			Pattern:     regexp.MustCompile(`function\s+validateRecord\s*\(`),
			FileInclude: regexp.MustCompile(`src/app\.ts$`),
			Message:     "manual validateRecord() — autoCrud provides built-in validation via ai.gftd.apps.{domain}.validate command"},
		{ID: "autocrud-manual-utility-cmds", Severity: "high", Weight: 2.0,
			FileInclude: regexp.MustCompile(`src/app\.ts$`),
			Message:     "manual utility commands (health/describe/stats/export/summarize/ingest/audit) — autoCrud auto-registers these. Remove boilerplate"},
		{ID: "autocrud-cadence-state-global", Severity: "high", Weight: 2.0,
			Pattern:     regexp.MustCompile(`(?:const|let|var)\s+cadenceState\s*=\s*createCadenceState\(\)`),
			FileInclude: regexp.MustCompile(`src/app\.ts$`),
			Message:     "global cadenceState — SDK manages cadence state internally. Remove createCadenceState()/createInboxBuffer() globals"},
		{ID: "missing-standard-heartbeat", Severity: "critical", Weight: 3.0,
			FileInclude: regexp.MustCompile(`src/app\.ts$`),
			Message:     "missing standard heartbeat — every actor/app DID must expose /_heartbeat or runHeartbeat with cadence"},
		{ID: "missing-standard-kyumei-flags", Severity: "critical", Weight: 3.0,
			FileInclude: regexp.MustCompile(`src/app\.ts$`),
			Message:     "missing standard shinka/kyumei flags — require shouldDrill, shouldValidate, shouldAnalyze, shouldEngage"},
		{ID: "missing-standard-domain-knowledge", Severity: "high", Weight: 2.0,
			FileInclude: regexp.MustCompile(`src/app\.ts$`),
			Message:     "missing standard domain knowledge surface — require shinkaEvolution and shinkaKnowledge collection literals"},
	}

	// Collect all main.go files + infra TS files
	var files []string

	// Infra templates + host-sdk (scan for hardcoded-repo-did, writebuffer-entries, raw-webassembly-instance, host-sdk-import-gap)
	infraFiles := []string{
		filepath.Join(wsRoot, "infra", "cloudflare", "templates", "entry.ts"),
		filepath.Join(wsRoot, "packages", "runtime", "magatama", "magatama-host-sdk", "src", "index.ts"),
	}
	for _, f := range infraFiles {
		if _, err := os.Stat(f); err == nil {
			files = append(files, f)
		}
	}

	if hasProjectsDir {
		projEntries, _ := os.ReadDir(projectsDir)
		for _, pe := range projEntries {
			if !pe.IsDir() || !strings.HasPrefix(pe.Name(), "ai-gftd-project-") {
				continue
			}
			wasmDir := filepath.Join(projectsDir, pe.Name(), "wasm")
			wasmEntries, err := os.ReadDir(wasmDir)
			if err != nil {
				continue
			}
			for _, we := range wasmEntries {
				if !we.IsDir() {
					continue
				}
				mainGo := filepath.Join(wasmDir, we.Name(), "main.go")
				if _, err := os.Stat(mainGo); err == nil {
					files = append(files, mainGo)
				}
				appTS := filepath.Join(wasmDir, we.Name(), "src", "app.ts")
				if _, err := os.Stat(appTS); err == nil {
					files = append(files, appTS)
				}
				jsonld := filepath.Join(wasmDir, we.Name(), "magatama.jsonld")
				if _, err := os.Stat(jsonld); err == nil {
					files = append(files, jsonld)
				}
			}
		}
	}

	if hasAppsDir {
		entries, err := os.ReadDir(appsDir)
		if err == nil {
			for _, pe := range entries {
				if !pe.IsDir() || !strings.HasPrefix(pe.Name(), "ai-gftd-project-") {
					continue
				}
				appviewDir := filepath.Join(appsDir, pe.Name(), "appview")
				appviewEntries, err := os.ReadDir(appviewDir)
				if err != nil {
					continue
				}
				for _, ae := range appviewEntries {
					if !ae.IsDir() {
						continue
					}
					appTS := filepath.Join(appviewDir, ae.Name(), "src", "app.ts")
					if _, err := os.Stat(appTS); err == nil {
						files = append(files, appTS)
					}
					jsonld := filepath.Join(appviewDir, ae.Name(), "magatama.jsonld")
					if _, err := os.Stat(jsonld); err == nil {
						files = append(files, jsonld)
					}
				}
			}
		}
	}

	if len(files) == 0 {
		check.Score = 100
		check.Details = "no App main.go files found"
		return check
	}

	// Count violations per rule
	type violation struct {
		ruleID string
		count  int
	}
	ruleCounts := make(map[string]int)
	totalViolations := 0
	filesWithIssues := 0

	for _, f := range files {
		data, err := os.ReadFile(f)
		if err != nil {
			continue
		}
		content := string(data)
		fileHasIssue := false

		isJsonld := strings.HasSuffix(f, "magatama.jsonld")

		for _, rule := range rules {
			isScored := rule.Weight > 0

			// magatama.jsonld-only rules: skip for non-jsonld files, and vice versa
			if rule.ID == "missing-governance" || rule.ID == "missing-convo-system-prompt" || rule.ID == "missing-profile-description" || rule.ID == "missing-profile-capabilities" || rule.ID == "missing-embed-route" || rule.ID == "deprecated-sveltekit-framework" {
				if !isJsonld {
					continue
				}
				if rule.ID == "missing-governance" && !strings.Contains(content, `"governance"`) {
					ruleCounts[rule.ID]++
					totalViolations++
					if isScored {
						fileHasIssue = true
					}
				}
				if rule.ID == "missing-convo-system-prompt" && !strings.Contains(content, `"convoSystemPrompt"`) {
					ruleCounts[rule.ID]++
					totalViolations++
					if isScored {
						fileHasIssue = true
					}
				}
				if rule.ID == "missing-profile-description" {
					hasDescription := strings.Contains(content, `"description"`)
					if !hasDescription {
						ruleCounts[rule.ID]++
						totalViolations++
						if isScored {
							fileHasIssue = true
						}
					}
				}
				if rule.ID == "missing-profile-capabilities" {
					hasCapabilities := strings.Contains(content, `"capabilities"`)
					if !hasCapabilities {
						ruleCounts[rule.ID]++
						totalViolations++
						if isScored {
							fileHasIssue = true
						}
					}
				}
				if rule.ID == "missing-embed-route" {
					// Detect: uiType is "appview" (or absent, which defaults to appview)
					// and no "embedUrl" in magatama.jsonld.
					isAppview := !strings.Contains(content, `"uiType"`) || strings.Contains(content, `"uiType": "appview"`) || strings.Contains(content, `"uiType":"appview"`)
					hasEmbedUrl := strings.Contains(content, `"embedUrl"`)
					if isAppview && !hasEmbedUrl {
						ruleCounts[rule.ID]++
						totalViolations++
						if isScored {
							fileHasIssue = true
						}
					}
				}
				if rule.ID == "deprecated-sveltekit-framework" {
					// Detect: magatama.jsonld contains "framework": "sveltekit" or svelte.config.js exists
					hasSvelteKitFramework := strings.Contains(content, `"framework": "sveltekit"`) || strings.Contains(content, `"framework":"sveltekit"`)
					hasSvelteConfig := false
					jsonldDir := filepath.Dir(f)
					if _, err := os.Stat(filepath.Join(jsonldDir, "svelte.config.js")); err == nil {
						hasSvelteConfig = true
					}
					if hasSvelteKitFramework || hasSvelteConfig {
						ruleCounts[rule.ID]++
						totalViolations++
						if isScored {
							fileHasIssue = true
						}
					}
				}
				continue
			}
			// Skip non-jsonld rules for jsonld files
			if isJsonld {
				continue
			}

			// Special case: missing-serve checks for NewApp WITHOUT Serve
			if rule.ID == "missing-serve" {
				if rule.Pattern.MatchString(content) && !strings.Contains(content, "app.Serve()") {
					ruleCounts[rule.ID]++
					totalViolations++
					if isScored {
						fileHasIssue = true
					}
				}
				continue
			}
			if rule.ID == "did-double-prefix" {
				violations := countDidDoublePrefixViolations(content, []string{"appId", "APP_ID", "nanoid", "APP_NANOID", "COUNTRY_CODE"})
				if violations > 0 {
					ruleCounts[rule.ID] += violations
					totalViolations += violations
					if isScored {
						fileHasIssue = true
					}
				}
				continue
			}
			// string-template-bug: per-line scan for "...${x}..." (regular quotes with template syntax)
			// Skip lines containing backticks (template literals where "..." is inside `` and not a bug)
			if rule.ID == "string-template-bug" {
				if rule.FileInclude != nil && !rule.FileInclude.MatchString(f) {
					continue
				}
				stRe := regexp.MustCompile(`"[^"\n]*\$\{[^}\n]+\}[^"\n]*"`)
				for _, line := range strings.Split(content, "\n") {
					trimmed := strings.TrimSpace(line)
					if strings.HasPrefix(trimmed, "//") || strings.HasPrefix(trimmed, "*") {
						continue
					}
					// Skip lines with backticks — the "..." is inside a template literal, not a bug
					if strings.Contains(line, "`") {
						continue
					}
					matches := stRe.FindAllString(line, -1)
					if len(matches) > 0 {
						ruleCounts[rule.ID] += len(matches)
						totalViolations += len(matches)
						if rule.Weight > 0 {
							fileHasIssue = true
						}
					}
				}
				continue
			}
			// duplicate-import-line: count import lines from same module, flag if >1
			if rule.ID == "duplicate-import-line" {
				if rule.FileInclude != nil && !rule.FileInclude.MatchString(f) {
					continue
				}
				importCount := 0
				for _, line := range strings.Split(content, "\n") {
					if strings.Contains(line, `from "@gftd/magatama-host-sdk"`) || strings.Contains(line, `from '@gftd/magatama-host-sdk'`) {
						importCount++
					}
				}
				if importCount > 1 {
					ruleCounts[rule.ID] += importCount - 1
					totalViolations += importCount - 1
					if rule.Weight > 0 {
						fileHasIssue = true
					}
				}
				continue
			}
			// dead-function-unreferenced: detect functions defined but never called in app.ts
			if rule.ID == "dead-function-unreferenced" {
				if rule.FileInclude != nil && !rule.FileInclude.MatchString(f) {
					continue
				}
				deadCount := countDeadFunctions(content)
				if deadCount > 0 {
					ruleCounts[rule.ID] += deadCount
					totalViolations += deadCount
					if rule.Weight > 0 {
						fileHasIssue = true
					}
				}
				continue
			}
			// missing-export-default: app.ts must have export default createWorkerExport(...)
			if rule.ID == "missing-export-default" {
				if rule.FileInclude != nil && !rule.FileInclude.MatchString(f) {
					continue
				}
				if !strings.Contains(content, "export default") || !strings.Contains(content, "createWorkerExport") {
					ruleCounts[rule.ID]++
					totalViolations++
					if rule.Weight > 0 {
						fileHasIssue = true
					}
				}
				continue
			}
			// non-async-await: function (not async) containing await
			if rule.ID == "non-async-await" {
				if rule.FileInclude != nil && !rule.FileInclude.MatchString(f) {
					continue
				}
				naRe := regexp.MustCompile(`(?m)^(?:export\s+)?function\s+\w+\s*\([^)]*\)\s*(?::\s*[^{]+?)?\s*\{`)
				matches := naRe.FindAllStringIndex(content, -1)
				for _, loc := range matches {
					// Check 20 chars before match for "async "
					preStart := loc[0] - 10
					if preStart < 0 {
						preStart = 0
					}
					pre := content[preStart:loc[0]]
					if strings.Contains(pre, "async ") {
						continue
					}
					// Find matching brace
					depth := 1
					i := loc[1]
					for i < len(content) && depth > 0 {
						if content[i] == '{' {
							depth++
						} else if content[i] == '}' {
							depth--
						}
						i++
					}
					body := content[loc[1]:i]
					if strings.Contains(body, "await ") {
						ruleCounts[rule.ID]++
						totalViolations++
						if rule.Weight > 0 {
							fileHasIssue = true
						}
					}
				}
				continue
			}
			// autocrud-manual-crud: detect apps that have manual list/get/search/create when autoCrud should be used
			if rule.ID == "autocrud-manual-crud" {
				if strings.HasSuffix(f, "src/app.ts") && !strings.Contains(content, ".autoCrud(") {
					// Count manual CRUD command registrations that autoCrud would replace
					crudPatterns := regexp.MustCompile(`\.command\("[^"]*\.(?:list|get|search|create)"`)
					matches := crudPatterns.FindAllString(content, -1)
					if len(matches) >= 3 { // 3+ CRUD commands = should use autoCrud
						ruleCounts[rule.ID] += len(matches)
						totalViolations += len(matches)
						if isScored {
							fileHasIssue = true
						}
					}
				}
				continue
			}
			// autocrud-manual-utility-cmds: detect manual health/describe/stats/export/summarize/ingest/audit
			if rule.ID == "autocrud-manual-utility-cmds" {
				if strings.HasSuffix(f, "src/app.ts") && !strings.Contains(content, ".autoCrud(") {
					utilPatterns := regexp.MustCompile(`\.command\("[^"]*\.(?:health|describe|stats|export|summarize|ingest|audit)"`)
					matches := utilPatterns.FindAllString(content, -1)
					if len(matches) >= 3 { // 3+ utility commands = should use autoCrud
						ruleCounts[rule.ID] += len(matches)
						totalViolations += len(matches)
						if isScored {
							fileHasIssue = true
						}
					}
				}
				continue
			}
			if rule.ID == "missing-standard-heartbeat" {
				if strings.HasSuffix(f, "src/app.ts") && !strings.Contains(content, "/_heartbeat") && !strings.Contains(content, "runHeartbeat(") {
					ruleCounts[rule.ID]++
					totalViolations++
					if isScored {
						fileHasIssue = true
					}
				}
				continue
			}
			if rule.ID == "missing-standard-kyumei-flags" {
				if strings.HasSuffix(f, "src/app.ts") {
					missing := 0
					for _, token := range []string{"shouldDrill", "shouldValidate", "shouldAnalyze", "shouldEngage"} {
						if !strings.Contains(content, token) {
							missing++
						}
					}
					if missing > 0 {
						ruleCounts[rule.ID] += missing
						totalViolations += missing
						if isScored {
							fileHasIssue = true
						}
					}
				}
				continue
			}
			if rule.ID == "missing-standard-domain-knowledge" {
				if strings.HasSuffix(f, "src/app.ts") {
					missing := 0
					for _, token := range []string{"shinkaEvolution", "shinkaKnowledge"} {
						if !strings.Contains(content, token) {
							missing++
						}
					}
					if missing > 0 {
						ruleCounts[rule.ID] += missing
						totalViolations += missing
						if isScored {
							fileHasIssue = true
						}
					}
				}
				continue
			}
			// dual-write: WRecord + AppBskyFeedPostAs in the same function
			if rule.ID == "dual-write" {
				violations := countDualWriteViolations(content)
				if violations > 0 {
					ruleCounts[rule.ID] += violations
					totalViolations += violations
					fileHasIssue = true
				}
				continue
			}
			if rule.FileInclude != nil && !rule.FileInclude.MatchString(f) {
				// FileInclude filter: skip files that don't match
			} else if rule.FileExclude != nil && rule.FileExclude.MatchString(content) {
				// File-level exclude: file has been audited (e.g. contains safeLabel)
			} else if rule.Exclude != nil {
				// Per-line matching with exclude
				for _, line := range strings.Split(content, "\n") {
					if rule.Pattern.MatchString(line) && !rule.Exclude.MatchString(line) {
						ruleCounts[rule.ID]++
						totalViolations++
						if isScored {
							fileHasIssue = true
						}
					}
				}
			} else {
				matches := rule.Pattern.FindAllString(content, -1)
				if len(matches) > 0 {
					ruleCounts[rule.ID] += len(matches)
					totalViolations += len(matches)
					if isScored {
						fileHasIssue = true
					}
				}
			}
		}
		if fileHasIssue {
			filesWithIssues++
		}
	}

	check.Issues = totalViolations

	// Score: weighted violation penalty against total files
	// Each violation is penalized by its weight, normalized against file count
	weightedViolations := 0.0
	for _, rule := range rules {
		if cnt, ok := ruleCounts[rule.ID]; ok && cnt > 0 {
			weightedViolations += float64(cnt) * rule.Weight
		}
	}
	// Penalty: 100 * (weighted / (total_files * max_weight_per_file))
	// Use a simpler model: 100 * (1 - filesWithIssues/totalFiles)
	complianceRate := 1.0 - float64(filesWithIssues)/float64(len(files))
	check.Score = cqCap(complianceRate * 100)

	// Build details string
	var parts []string
	parts = append(parts, fmt.Sprintf("%d/%d files compliant", len(files)-filesWithIssues, len(files)))
	for _, rule := range rules {
		if cnt, ok := ruleCounts[rule.ID]; ok && cnt > 0 {
			parts = append(parts, fmt.Sprintf("%s: %d (%s)", rule.ID, cnt, rule.Severity))
		}
	}
	check.Details = strings.Join(parts, ", ")

	return check
}

// countDualWriteViolations detects functions that call both WRecord() and AppBskyFeedPostAs().
// Design E: AppBskyFeedPostAs for social (public AT Record), WRecord for domain data (internal).
// Calling both in the same function is Shannon redundancy — separate social and domain concerns.
func countDualWriteViolations(content string) int {
	// Split by Go function boundaries
	funcPattern := regexp.MustCompile(`(?m)^func\s+\w+`)
	locs := funcPattern.FindAllStringIndex(content, -1)
	if len(locs) == 0 {
		return 0
	}
	violations := 0
	wrecordRe := regexp.MustCompile(`\bmagatama\.WRecord\(`)
	atpostRe := regexp.MustCompile(`\bmagatama\.AppBskyFeedPostAs\(`)
	for i, loc := range locs {
		end := len(content)
		if i+1 < len(locs) {
			end = locs[i+1][0]
		}
		body := content[loc[0]:end]
		if wrecordRe.MatchString(body) && atpostRe.MatchString(body) {
			violations++
		}
	}
	return violations
}

// countDeadFunctions detects functions in app.ts that are defined but never referenced elsewhere.
// Excludes exported functions, command handlers wired into .command(), and standard lifecycle exports.
func countDeadFunctions(content string) int {
	// Extract all function names (both `function foo(` and `async function foo(`)
	funcDefRe := regexp.MustCompile(`(?m)^(?:async\s+)?function\s+(\w+)\s*[\(<]`)
	matches := funcDefRe.FindAllStringSubmatch(content, -1)
	if len(matches) == 0 {
		return 0
	}

	dead := 0
	for _, m := range matches {
		name := m[1]
		// Skip standard lifecycle exports
		if name == "createComponentHostSDK" || name == "runHeartbeat" ||
			name == "handleComAtprotoSyncSubscribeReposCommit" {
			continue
		}
		// Count references to this function name in the file (excluding its own definition line)
		refCount := 0
		refRe := regexp.MustCompile(`\b` + regexp.QuoteMeta(name) + `\b`)
		refMatches := refRe.FindAllStringIndex(content, -1)
		// Subtract the definition itself (at least 1 match is the definition)
		refCount = len(refMatches) - 1
		// Also subtract export statement if present (e.g. `export { name }`)
		if strings.Contains(content, "export { "+name) || strings.Contains(content, "export {"+name) {
			refCount--
		}
		if refCount <= 0 {
			dead++
		}
	}
	return dead
}

// frontendLintRule defines a lint rule for frontend (.svelte/.ts) files.
type frontendLintRule struct {
	ID          string
	Severity    string
	Weight      float64
	Pattern     *regexp.Regexp
	Exclude     *regexp.Regexp
	FileExclude *regexp.Regexp
	Message     string
}

// checkFrontendLint scans projects/*/svelte/ and packages/ts/ for legacy data access patterns.
// Design D mandate: all data/posts/process management through W Protocol only.
func checkFrontendLint(wsRoot string) codeQualityCheck {
	check := codeQualityCheck{
		Name: "frontend_lint",
		Tool: "frontend-lint (built-in)",
	}
	check.Available = true

	rules := []frontendLintRule{
		{ID: "legacy-envelope", Severity: "critical", Weight: 3.0,
			Pattern:     regexp.MustCompile(`\blistEnvelopes\s*\(|\bdecodePayload\s*\(`),
			FileExclude: regexp.MustCompile(`(?:w-service\.ts|w-channel-store\.svelte\.ts|index\.ts)$`),
			Message:     "legacy channel envelope access — use getAuthorFeed/getTimeline/getDiscoverFeed (W Protocol)"},
		{ID: "direct-app-fetch", Severity: "high", Weight: 2.0,
			Pattern: regexp.MustCompile(`fetch\s*\(\s*` + "`" + `https://\$\{[^}]*\}\.gftd\.ai/api/`),
			Message: "direct app host API fetch — route through mod.etzhayyim.com (Data Gateway Consolidation)"},
		{ID: "wsend-frontend", Severity: "high", Weight: 2.0,
			Pattern:     regexp.MustCompile(`\bWSend\s*\(|\bwPublish\s*\(`),
			FileExclude: regexp.MustCompile(`(?:w-service\.ts|w-channel-store\.svelte\.ts|host/)$`),
			Message:     "WSend/wPublish in frontend — use AppBskyFeedPostAs/getAuthorFeed for social, WRecord for data"},
		{ID: "channel-data-access", Severity: "high", Weight: 2.0,
			Pattern:     regexp.MustCompile(`\blistEnvelopes\s*\(\s*(?:ch\.|channel)`),
			FileExclude: regexp.MustCompile(`(?:w-service\.ts|w-channel-store\.svelte\.ts)$`),
			Message:     "channel-based data access — use getAuthorFeed/getPostThread (Bluesky feed model)"},
		{ID: "xrpc-frontend", Severity: "info", Weight: 0.0,
			Pattern: regexp.MustCompile(`/xrpc/`),
			Message: "XRPC is the sole API surface — /xrpc/{NSID} (AT Protocol native) via mod.etzhayyim.com"},
		{ID: "legacy-chat-store", Severity: "medium", Weight: 1.0,
			Pattern:     regexp.MustCompile(`from\s+['"].*chat-store['"]|import.*chat-store`),
			FileExclude: regexp.MustCompile(`chat-store\.ts$`),
			Message:     "legacy chat-store import — use @gftdcojp/appshellv2/w"},
		{ID: "legacy-at-import", Severity: "medium", Weight: 1.0,
			Pattern: regexp.MustCompile(`from\s+['"]@gftdcojp/appshellv2/at['"]`),
			Message: "deprecated @gftdcojp/appshellv2/at — use @gftdcojp/appshellv2/w"},
		{ID: "wproto-reexport", Severity: "high", Weight: 2.0,
			Pattern:     regexp.MustCompile(`from\s+['"](?:\.\./w/w-service|\.\/w-service)(?:\.js)?['"]`),
			FileExclude: regexp.MustCompile(`(?:index\.ts|w/index\.ts)$`),
			Message:     "w-service re-export import — use @gftd/wproto/service directly"},
		{ID: "silent-catch", Severity: "high", Weight: 2.0,
			Pattern: regexp.MustCompile(`\.catch\(\s*\(\)\s*=>\s*\[\]`),
			Message: "silent .catch(() => []) swallows graph errors — use catchWarn helper to log fallback source"},
		{ID: "stub-fallback-chain", Severity: "medium", Weight: 1.0,
			Pattern: regexp.MustCompile(`\|\|\s*didToHandle\(|\.displayName\s*\|\|\s*['"]`),
			Message: "displayName fallback chain masks missing profile data — log profileSource for observability"},
		// ── WIT Layer 0/1 naming compliance (TS/Svelte) ──
		{ID: "legacy-wit-commit-handler-ts", Severity: "high", Weight: 2.0,
			Pattern:     regexp.MustCompile(`commit-handler-handle-commit|["']commit-handler["']`),
			FileExclude: regexp.MustCompile(`\.test\.ts$`),
			Message:     "legacy dispatch key: commit-handler — renamed to subscribe-repos (@nsid com.atproto.sync.subscribeRepos)"},
		{ID: "legacy-dispatch-channel", Severity: "high", Weight: 2.0,
			Pattern:     regexp.MustCompile(`["']channel-(?:create-channel|create-dm|send|list-envelopes|get-thread|search|get-unread|mark-read|update-presence)["']`),
			FileExclude: regexp.MustCompile(`\.test\.ts$`),
			Message:     "legacy dispatch key: channel-* — renamed to convo-* (@nsid ai.gftd.convo)"},
		{ID: "legacy-dispatch-did", Severity: "medium", Weight: 1.0,
			Pattern:     regexp.MustCompile(`["']did-(?:create|resolve|update|deactivate|rotate-key|write|update-record|delete-record)["']`),
			FileExclude: regexp.MustCompile(`\.test\.ts$`),
			Message:     "legacy dispatch key: did-* — renamed to identity-* (@nsid com.atproto.identity)"},
		{ID: "legacy-dispatch-follow", Severity: "medium", Weight: 1.0,
			Pattern:     regexp.MustCompile(`["']follow-(?:follow|unfollow|set-muted|react|unreact|pull-feed|ack-feed|leaderboard|approve|reject)["']`),
			FileExclude: regexp.MustCompile(`\.test\.ts$`),
			Message:     "legacy dispatch key: follow-* — renamed to social-graph-* (@nsid app.bsky.graph)"},
		{ID: "legacy-dispatch-access-control", Severity: "high", Weight: 2.0,
			Pattern:     regexp.MustCompile(`["']access-control-`),
			FileExclude: regexp.MustCompile(`\.test\.ts$`),
			Message:     "legacy dispatch key: access-control-* — renamed to governance-* (@nsid ai.gftd.governance)"},
	}

	// Collect frontend files: projects/*/svelte/src/**/*.{svelte,ts}
	var files []string
	projectsDir := filepath.Join(wsRoot, "projects")
	projEntries, _ := os.ReadDir(projectsDir)
	for _, pe := range projEntries {
		if !pe.IsDir() || !strings.HasPrefix(pe.Name(), "ai-gftd-project-") {
			continue
		}
		wasmDir := filepath.Join(projectsDir, pe.Name(), "wasm")
		wasmEntries, err := os.ReadDir(wasmDir)
		if err != nil {
			continue
		}
		for _, we := range wasmEntries {
			if !we.IsDir() {
				continue
			}
			svelteDir := filepath.Join(wasmDir, we.Name(), "svelte", "src")
			collectFrontendFiles(svelteDir, &files)
		}
	}
	// Also scan appshellv2 internal components for re-export imports
	appshellSrc := filepath.Join(wsRoot, "packages", "svelte", "appshellv2", "src", "lib")
	collectFrontendFiles(appshellSrc, &files)
	// Scan PDS/wproto TS source for silent-catch and fallback patterns
	pdsSrc := filepath.Join(wsRoot, "packages", "server", "wproto", "src")
	collectFrontendFiles(pdsSrc, &files)

	if len(files) == 0 {
		check.Score = 100
		check.Details = "no frontend files found"
		return check
	}

	ruleCounts := make(map[string]int)
	totalViolations := 0
	filesWithIssues := 0

	for _, f := range files {
		data, err := os.ReadFile(f)
		if err != nil {
			continue
		}
		content := string(data)
		fileHasIssue := false

		for _, rule := range rules {
			if rule.FileExclude != nil {
				if rule.FileExclude.MatchString(f) {
					continue
				}
			}
			if rule.Exclude != nil {
				for _, line := range strings.Split(content, "\n") {
					if rule.Pattern.MatchString(line) && !rule.Exclude.MatchString(line) {
						ruleCounts[rule.ID]++
						totalViolations++
						fileHasIssue = true
					}
				}
			} else {
				matches := rule.Pattern.FindAllString(content, -1)
				if len(matches) > 0 {
					ruleCounts[rule.ID] += len(matches)
					totalViolations += len(matches)
					fileHasIssue = true
				}
			}
		}
		if fileHasIssue {
			filesWithIssues++
		}
	}

	check.Issues = totalViolations
	complianceRate := 1.0 - float64(filesWithIssues)/float64(len(files))
	check.Score = cqCap(complianceRate * 100)

	var parts []string
	parts = append(parts, fmt.Sprintf("%d/%d files compliant", len(files)-filesWithIssues, len(files)))
	for _, rule := range rules {
		if cnt, ok := ruleCounts[rule.ID]; ok && cnt > 0 {
			parts = append(parts, fmt.Sprintf("%s: %d (%s)", rule.ID, cnt, rule.Severity))
		}
	}
	check.Details = strings.Join(parts, ", ")
	return check
}

// collectFrontendFiles walks a directory and collects .svelte and .ts files.
func collectFrontendFiles(dir string, files *[]string) {
	_ = filepath.WalkDir(dir, func(path string, d os.DirEntry, err error) error {
		if err != nil {
			return nil
		}
		if d.IsDir() {
			base := d.Name()
			if base == "node_modules" || base == ".svelte-kit" || base == "build" {
				return filepath.SkipDir
			}
			return nil
		}
		ext := filepath.Ext(d.Name())
		if ext == ".svelte" || ext == ".ts" {
			// Skip .d.ts type definition files
			if strings.HasSuffix(d.Name(), ".d.ts") {
				return nil
			}
			*files = append(*files, path)
		}
		return nil
	})
}

// checkSqlInjection checks PDS index.ts for raw string interpolation in Sql queries.
func checkSqlInjection(wsRoot string) codeQualityCheck {
	check := codeQualityCheck{
		Name: "sql_injection",
		Tool: "sql-injection-lint (built-in)",
	}
	check.Available = true

	pdsIndex := filepath.Join(wsRoot, "packages", "server", "wproto", "src", "pds-dispatch.ts")
	data, err := os.ReadFile(pdsIndex)
	if err != nil {
		check.Score = 100
		check.Details = "PDS index.ts not found (skipped)"
		return check
	}
	content := string(data)

	type sqlRule struct {
		id      string
		pattern *regexp.Regexp
		message string
	}
	rules := []sqlRule{
		{"esc-interpolation", regexp.MustCompile(`\$\{esc\(`), "Sql string interpolation via esc() — use $param parameterized query"},
		{"template-sql", regexp.MustCompile(`"\$\{[^}]+\}"`), "template literal in Sql string position — use $param"},
		{"list-agents-query", regexp.MustCompile(`list-agents`), "list-agents named query — removed, use SearchActors"},
		{"did-double-prefix", nil, "did:web:${var} without startsWith(\"did:\") guard — allow only appId/nanoid/cl(r.rkey) or use ensureDid(var)"},
	}

	totalIssues := 0
	var parts []string
	for _, rule := range rules {
		var matches int
		if rule.id == "did-double-prefix" {
			matches = countDidDoublePrefixViolations(content, []string{"appId", "APP_ID", "nanoid", "cl(r.rkey)"})
		} else {
			matches = len(rule.pattern.FindAllString(content, -1))
		}
		if matches > 0 {
			totalIssues += matches
			parts = append(parts, fmt.Sprintf("%s: %d", rule.id, matches))
		}
	}

	check.Issues = totalIssues
	if totalIssues == 0 {
		check.Score = 100
		check.Details = "PDS index.ts: no Sql injection patterns found"
	} else {
		check.Score = 0
		check.Details = "PDS index.ts: " + strings.Join(parts, ", ")
	}
	return check
}

// checkSqlFullScan detects Sql queries in PDS handlers that lack promoted column filters,
// causing full label scans on R2 SQL. Promoted columns (SQL pushdown eligible): rkey, repo, did,
// collection, updated_at, status, nanoid, visibility, region, vertex_type, project_id, etc.
// A full scan occurs when WHERE uses only non-promoted columns or only time-range without identity.
func checkSqlFullScan(wsRoot string) codeQualityCheck {
	check := codeQualityCheck{
		Name:      "sql_full_scan",
		Tool:      "sql-full-scan-lint (built-in)",
		Available: true,
	}

	pdsDir := filepath.Join(wsRoot, "infra", "cloudflare", "workers", "pds", "src")
	handlerFiles := []string{
		"pds-handlers-feed.ts",
		"pds-handlers-gftd.ts",
		"pds-handlers-repo.ts",
		"pds-handlers-infra.ts",
		"pds-actor.ts",
		"pds-actor-tools.ts",
	}

	// Promoted columns that provide SQL pushdown (identity/key filters).
	// Time-range alone (updated_at/updatedAt) is NOT sufficient — must pair with identity.
	identityFilterRe := regexp.MustCompile(`\w\.\b(?:rkey|repo|did|nanoid|vertex_id|edge_id|collection|owner_did|ownerDid|app_id|visibility|status|region|vertex_type|project_id|src_vid|dst_vid|src_label|dst_label|updated_at|updatedAt)\b\s*(?:=|IN\s*\[|IS\s+NOT\s+NULL|STARTS\s+WITH|<>|!=)`)
	// Match MATCH queries in template literals
	matchQueryRe := regexp.MustCompile("MATCH\\s*\\(\\w+:\\w+\\)")

	totalIssues := 0
	var parts []string

	for _, fname := range handlerFiles {
		data, err := os.ReadFile(filepath.Join(pdsDir, fname))
		if err != nil {
			continue
		}
		lines := strings.Split(string(data), "\n")
		for i, line := range lines {
			if !matchQueryRe.MatchString(line) {
				continue
			}
			// Skip comment lines
			trimmed := strings.TrimSpace(line)
			if strings.HasPrefix(trimmed, "//") || strings.HasPrefix(trimmed, "*") {
				continue
			}
			// For multi-line queries, check next line for identity filter
			if i+1 < len(lines) && identityFilterRe.MatchString(lines[i+1]) {
				continue
			}
			// Skip if line has an identity-promoting WHERE filter
			if identityFilterRe.MatchString(line) {
				continue
			}
			// Skip Sql property match syntax {nanoid: "..."} (promoted inline)
			if strings.Contains(line, "{nanoid:") || strings.Contains(line, "{rkey:") || strings.Contains(line, "{did:") {
				continue
			}
			// Skip lines using variable indirection that contains promoted filters
			// (e.g. ${filter}, ${conditions}, multiDidFilter("r.repo", ...))
			if strings.Contains(line, "${filter}") || strings.Contains(line, "${conditions") || strings.Contains(line, "multiDidFilter") {
				continue
			}
			// Skip aggregation-only queries (count/sum with LIMIT 1)
			if strings.Contains(line, "count(") && strings.Contains(line, "LIMIT 1") {
				continue
			}
			// This query has no promoted identity filter — full scan
			totalIssues++
			parts = append(parts, fmt.Sprintf("%s:%d", fname, i+1))
		}
	}

	check.Issues = totalIssues
	if totalIssues == 0 {
		check.Score = 100
		check.Details = "PDS handlers: no Sql full scan queries found"
	} else {
		check.Score = float64(max(0, 100-totalIssues*5))
		detail := strings.Join(parts, ", ")
		if len(detail) > 500 {
			detail = detail[:500] + "..."
		}
		check.Details = fmt.Sprintf("PDS handlers: %d full scan queries — %s", totalIssues, detail)
	}
	return check
}

// checkPerfTest verifies that performance test specs exist for key user flows.
// Checks for Playwright performance test files with budget assertions.
func checkPerfTest(wsRoot string) codeQualityCheck {
	check := codeQualityCheck{
		Name:      "perf_test",
		Tool:      "perf-test-coverage (built-in)",
		Available: true,
	}

	type perfTarget struct {
		project string
		dir     string
		pattern string
	}
	targets := []perfTarget{
		{"yoro", filepath.Join(wsRoot, "projects", "ai-gftd-project-yoro", "wasm", "yoro-ui-g00h5zto", "svelte", "tests"), "profile-performance"},
	}

	var found, missing int
	var details []string
	for _, t := range targets {
		var hasPerf bool
		_ = filepath.WalkDir(t.dir, func(path string, d os.DirEntry, err error) error {
			if err != nil || d.IsDir() {
				return nil
			}
			if strings.Contains(d.Name(), t.pattern) && strings.HasSuffix(d.Name(), ".spec.ts") {
				// Verify it contains budget assertions (toBeLessThan)
				data, readErr := os.ReadFile(path)
				if readErr == nil && bytes.Contains(data, []byte("toBeLessThan")) {
					hasPerf = true
				}
			}
			return nil
		})
		if hasPerf {
			found++
			details = append(details, fmt.Sprintf("%s: perf test found", t.project))
		} else {
			missing++
			details = append(details, fmt.Sprintf("%s: perf test MISSING", t.project))
		}
	}

	check.Issues = missing
	if len(targets) > 0 {
		check.Score = cqCap(float64(found) / float64(len(targets)) * 100)
	} else {
		check.Score = 100
	}
	check.Details = strings.Join(details, ", ")
	return check
}

// checkDeadExports runs dead-exports.mjs and scores based on dead export count.
// Score: 100 - (dead * 5), clamped to [0, 100]. 5 pts per dead export.
func checkDeadExports(wsRoot string) codeQualityCheck {
	check := codeQualityCheck{
		Name: "dead_exports",
		Tool: "dead-exports.mjs (node + rg)",
	}

	// Requires node and rg
	if _, err := exec.LookPath("node"); err != nil {
		check.Available = false
		return check
	}
	if _, err := exec.LookPath("rg"); err != nil {
		check.Available = false
		return check
	}
	check.Available = true

	scriptPath := filepath.Join(wsRoot, "70-tools", "scripts", "lint", "dead-exports.mjs")
	if _, err := os.Stat(scriptPath); err != nil {
		check.Score = 100
		check.Details = "dead-exports.mjs not found (skip)"
		return check
	}

	ctx, cancel := context.WithTimeout(context.Background(), 120*time.Second)
	defer cancel()
	cmd := exec.CommandContext(ctx, "node", scriptPath, "--json", "--warn-only")
	cmd.Dir = wsRoot
	out, err := cmd.Output()
	if err != nil {
		// Script itself may exit non-zero if dead exports found; that's OK in --warn-only mode.
		// Use combined output for error reporting.
		var exitErr *exec.ExitError
		if !errors.As(err, &exitErr) {
			check.Error = err.Error()
			return check
		}
		// exitErr: dead exports found — parse JSON from stdout
	}

	type deadResult struct {
		Dead  []struct{ File, Name string } `json:"dead"`
		Total int                           `json:"total"`
	}
	var result deadResult
	if jsonErr := json.Unmarshal(out, &result); jsonErr != nil {
		check.Error = fmt.Sprintf("failed to parse dead-exports output: %v", jsonErr)
		return check
	}

	check.Issues = result.Total
	// 5 pts penalty per dead export
	check.Score = cqCap(100 - float64(result.Total)*5)
	if result.Total > 0 {
		// Summarise by file
		byFile := make(map[string]int)
		for _, d := range result.Dead {
			byFile[d.File]++
		}
		var parts []string
		for f, n := range byFile {
			parts = append(parts, fmt.Sprintf("%d in %s", n, filepath.Base(filepath.Dir(f))))
		}
		check.Details = strings.Join(parts, ", ")
	}
	return check
}
