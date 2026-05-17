package main

import (
	"bytes"
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"
	"time"
)

type coverageEntry struct {
	Language   string  `json:"language"`
	Directory  string  `json:"directory"`
	TestCount  int     `json:"test_count"`
	PassCount  int     `json:"pass_count"`
	FailCount  int     `json:"fail_count"`
	SkipCount  int     `json:"skip_count"`
	LineCov    float64 `json:"line_coverage_pct"`
	Available  bool    `json:"available"`
	Duration   string  `json:"duration"`
	Details    string  `json:"details,omitempty"`
	Error      string  `json:"error,omitempty"`
}

type testCoverageReport struct {
	EvaluatedAt   string          `json:"evaluated_at"`
	OverallTests  int             `json:"overall_tests"`
	OverallPass   int             `json:"overall_pass"`
	OverallFail   int             `json:"overall_fail"`
	OverallSkip   int             `json:"overall_skip"`
	OverallLineCov float64        `json:"overall_line_coverage_pct"`
	Entries       []coverageEntry `json:"entries"`
}

func runCoverage(args []string) error {
	fs := flag.NewFlagSet("coverage", flag.ContinueOnError)
	workspaceDir := fs.String("workspace-dir", "", "workspace root (default: git root)")
	lang := fs.String("lang", "", "comma-separated languages to test: rust,go,ts (default: all)")
	jsonOut := fs.Bool("json", false, "output as JSON")
	timeout := fs.Int("timeout", 600, "per-language timeout in seconds")
	covFlag := fs.Bool("coverage", true, "collect line coverage (requires cargo-llvm-cov / go cover / @vitest/coverage-v8)")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

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

	langSet := map[string]bool{"rust": true, "go": true, "ts": true}
	if *lang != "" {
		langSet = make(map[string]bool)
		for _, l := range strings.Split(*lang, ",") {
			langSet[strings.TrimSpace(l)] = true
		}
	}

	dur := time.Duration(*timeout) * time.Second
	var entries []coverageEntry

	if langSet["rust"] {
		entries = append(entries, covRust(wsRoot, dur, *covFlag)...)
	}
	if langSet["go"] {
		entries = append(entries, covGo(wsRoot, dur, *covFlag)...)
	}
	if langSet["ts"] {
		entries = append(entries, covTS(wsRoot, dur, *covFlag)...)
	}

	report := testCoverageReport{
		EvaluatedAt: time.Now().UTC().Format(time.RFC3339),
		Entries:     entries,
	}
	var covSum float64
	covCount := 0
	for _, e := range entries {
		report.OverallTests += e.TestCount
		report.OverallPass += e.PassCount
		report.OverallFail += e.FailCount
		report.OverallSkip += e.SkipCount
		if e.LineCov > 0 {
			covSum += e.LineCov
			covCount++
		}
	}
	if covCount > 0 {
		report.OverallLineCov = covSum / float64(covCount)
	}

	if *jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(report)
	}

	printCoverageText(&report)
	return nil
}

// --- Rust coverage via cargo test / cargo llvm-cov ---

func covRust(wsRoot string, timeout time.Duration, withCov bool) []coverageEntry {
	// Find Cargo workspace dirs under 20-actors, 30-graph, 40-engine
	searchDirs := []string{
		filepath.Join(wsRoot, "20-actors"),
		filepath.Join(wsRoot, "30-graph"),
		filepath.Join(wsRoot, "40-engine"),
	}
	var results []coverageEntry
	for _, searchDir := range searchDirs {
		workspaces := findCargoWorkspacesRecursive(searchDir)
		for _, ws := range workspaces {
			results = append(results, covRustWorkspace(ws, timeout, withCov))
		}
	}
	if len(results) == 0 {
		results = append(results, coverageEntry{
			Language:  "rust",
			Available: false,
			Error:     "no cargo workspaces found",
		})
	}
	return results
}

func covRustWorkspace(wsDir string, timeout time.Duration, withCov bool) coverageEntry {
	relDir := wsDir
	if gitRoot, err := findGitRoot(wsDir); err == nil {
		if rel, err := filepath.Rel(gitRoot, wsDir); err == nil {
			relDir = rel
		}
	}

	entry := coverageEntry{
		Language:  "rust",
		Directory: relDir,
	}

	if _, err := exec.LookPath("cargo"); err != nil {
		entry.Available = false
		entry.Error = "cargo not found"
		return entry
	}
	entry.Available = true

	start := time.Now()

	// Try cargo llvm-cov for coverage, fallback to cargo test
	if withCov {
		if covEntry, ok := covRustLlvmCov(wsDir, timeout, relDir); ok {
			covEntry.Duration = time.Since(start).Truncate(time.Millisecond).String()
			return covEntry
		}
	}

	// Try JSON format first (nightly), fallback to text parsing (stable)
	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()

	cmd := exec.CommandContext(ctx, "cargo", "test", "--workspace", "--", "--format=json", "-Z", "unstable-options")
	cmd.Dir = wsDir
	cmd.Env = append(os.Environ(), "RUSTC_WRAPPER=")
	out, err := cmd.CombinedOutput()

	// If -Z unstable-options fails (stable compiler), fallback to text output
	if err != nil && bytes.Contains(out, []byte("the option `Z` is only accepted on the nightly")) {
		ctx2, cancel2 := context.WithTimeout(context.Background(), timeout)
		defer cancel2()
		cmd2 := exec.CommandContext(ctx2, "cargo", "test", "--workspace")
		cmd2.Dir = wsDir
		cmd2.Env = append(os.Environ(), "RUSTC_WRAPPER=")
		out, err = cmd2.CombinedOutput()

		entry.Duration = time.Since(start).Truncate(time.Millisecond).String()
		parseRustTestText(out, &entry)

		if err != nil && entry.FailCount == 0 && entry.PassCount == 0 {
			entry.Error = truncateStr(string(out), 500)
		}
		return entry
	}

	entry.Duration = time.Since(start).Truncate(time.Millisecond).String()
	parseRustTestJSON(out, &entry)

	if err != nil && entry.FailCount == 0 && entry.PassCount == 0 {
		entry.Error = truncateStr(string(out), 500)
	}

	return entry
}

func covRustLlvmCov(wsDir string, timeout time.Duration, relDir string) (coverageEntry, bool) {
	entry := coverageEntry{
		Language:  "rust",
		Directory: relDir,
		Available: true,
	}

	// Check if cargo-llvm-cov is available
	checkCtx, checkCancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer checkCancel()
	if err := exec.CommandContext(checkCtx, "cargo", "llvm-cov", "--help").Run(); err != nil {
		return entry, false
	}

	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()

	cmd := exec.CommandContext(ctx, "cargo", "llvm-cov", "--workspace", "--json")
	cmd.Dir = wsDir
	cmd.Env = append(os.Environ(), "RUSTC_WRAPPER=")
	out, err := cmd.CombinedOutput()

	if err != nil {
		// llvm-cov failed, fallback
		return entry, false
	}

	// Parse llvm-cov JSON output for line coverage
	var covData struct {
		Data []struct {
			Totals struct {
				Lines struct {
					Count   int     `json:"count"`
					Covered int     `json:"covered"`
					Percent float64 `json:"percent"`
				} `json:"lines"`
			} `json:"totals"`
		} `json:"data"`
	}
	if err := json.Unmarshal(out, &covData); err == nil && len(covData.Data) > 0 {
		entry.LineCov = covData.Data[0].Totals.Lines.Percent
	}

	// Also run cargo test to get counts (use text output for stable compiler compat)
	testCtx, testCancel := context.WithTimeout(context.Background(), timeout)
	defer testCancel()
	testCmd := exec.CommandContext(testCtx, "cargo", "test", "--workspace")
	testCmd.Dir = wsDir
	testCmd.Env = append(os.Environ(), "RUSTC_WRAPPER=")
	testOut, _ := testCmd.CombinedOutput()
	parseRustTestText(testOut, &entry)

	return entry, true
}

func parseRustTestJSON(out []byte, entry *coverageEntry) {
	// cargo test --format=json outputs one JSON object per line
	// { "type": "test", "event": "ok", "name": "..." }
	// { "type": "suite", "event": "ok", "passed": N, "failed": N, "ignored": N }
	for _, line := range bytes.Split(out, []byte("\n")) {
		line = bytes.TrimSpace(line)
		if len(line) == 0 || line[0] != '{' {
			continue
		}
		var obj map[string]interface{}
		if err := json.Unmarshal(line, &obj); err != nil {
			continue
		}
		typ, _ := obj["type"].(string)
		event, _ := obj["event"].(string)
		if typ == "suite" && (event == "ok" || event == "failed") {
			if p, ok := obj["passed"].(float64); ok {
				entry.PassCount += int(p)
			}
			if f, ok := obj["failed"].(float64); ok {
				entry.FailCount += int(f)
			}
			if ig, ok := obj["ignored"].(float64); ok {
				entry.SkipCount += int(ig)
			}
		}
	}
	entry.TestCount = entry.PassCount + entry.FailCount + entry.SkipCount
}

// rustTestSummaryRe matches "test result: ok. 3 passed; 0 failed; 1 ignored; ..."
var rustTestSummaryRe = regexp.MustCompile(`test result: \w+\.\s+(\d+) passed;\s+(\d+) failed;\s+(\d+) ignored;`)

func parseRustTestText(out []byte, entry *coverageEntry) {
	for _, line := range bytes.Split(out, []byte("\n")) {
		m := rustTestSummaryRe.FindSubmatch(line)
		if m == nil {
			continue
		}
		p, _ := strconv.Atoi(string(m[1]))
		f, _ := strconv.Atoi(string(m[2]))
		ig, _ := strconv.Atoi(string(m[3]))
		entry.PassCount += p
		entry.FailCount += f
		entry.SkipCount += ig
	}
	entry.TestCount = entry.PassCount + entry.FailCount + entry.SkipCount
}

// --- Go coverage via go test -cover ---

func covGo(wsRoot string, timeout time.Duration, withCov bool) []coverageEntry {
	// Find go.mod files
	goModDirs := findGoTestModDirs(wsRoot)
	if len(goModDirs) == 0 {
		return []coverageEntry{{
			Language:  "go",
			Available: false,
			Error:     "no go.mod found",
		}}
	}

	var results []coverageEntry
	for _, dir := range goModDirs {
		results = append(results, covGoModule(dir, timeout, withCov))
	}
	return results
}

func covGoModule(modDir string, timeout time.Duration, withCov bool) coverageEntry {
	relDir := modDir
	if gitRoot, err := findGitRoot(modDir); err == nil {
		if rel, err := filepath.Rel(gitRoot, modDir); err == nil {
			relDir = rel
		}
	}

	entry := coverageEntry{
		Language:  "go",
		Directory: relDir,
	}

	if _, err := exec.LookPath("go"); err != nil {
		entry.Available = false
		entry.Error = "go not found"
		return entry
	}
	entry.Available = true

	start := time.Now()
	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()

	goArgs := []string{"test", "-json"}
	if withCov {
		goArgs = append(goArgs, "-coverprofile=coverage.out", "-covermode=atomic")
	}
	goArgs = append(goArgs, "./...")

	cmd := exec.CommandContext(ctx, "go", goArgs...)
	cmd.Dir = modDir
	out, err := cmd.CombinedOutput()

	entry.Duration = time.Since(start).Truncate(time.Millisecond).String()

	parseGoTestJSON(out, &entry)

	// Parse coverage from go tool cover
	if withCov {
		covFile := filepath.Join(modDir, "coverage.out")
		if _, statErr := os.Stat(covFile); statErr == nil {
			entry.LineCov = parseGoCoverageFile(covFile)
			os.Remove(covFile)
		}
	}

	if err != nil && entry.FailCount == 0 && entry.PassCount == 0 {
		entry.Error = truncateStr(string(out), 500)
	}

	return entry
}

func parseGoTestJSON(out []byte, entry *coverageEntry) {
	// go test -json outputs one JSON per line:
	// {"Action":"pass","Test":"TestFoo",...}
	// {"Action":"fail","Test":"TestBar",...}
	// {"Action":"skip","Test":"TestBaz",...}
	for _, line := range bytes.Split(out, []byte("\n")) {
		line = bytes.TrimSpace(line)
		if len(line) == 0 || line[0] != '{' {
			continue
		}
		var obj map[string]interface{}
		if err := json.Unmarshal(line, &obj); err != nil {
			continue
		}
		action, _ := obj["Action"].(string)
		// Only count events that have a "Test" field (not package-level)
		if _, hasTest := obj["Test"]; !hasTest {
			continue
		}
		switch action {
		case "pass":
			entry.PassCount++
		case "fail":
			entry.FailCount++
		case "skip":
			entry.SkipCount++
		}
	}
	entry.TestCount = entry.PassCount + entry.FailCount + entry.SkipCount
}

func parseGoCoverageFile(path string) float64 {
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	cmd := exec.CommandContext(ctx, "go", "tool", "cover", "-func="+path)
	out, err := cmd.CombinedOutput()
	if err != nil {
		return 0
	}

	// Last line: "total:   (statements)  XX.X%"
	lines := strings.Split(strings.TrimSpace(string(out)), "\n")
	if len(lines) == 0 {
		return 0
	}
	last := lines[len(lines)-1]
	re := regexp.MustCompile(`(\d+\.\d+)%`)
	m := re.FindStringSubmatch(last)
	if len(m) < 2 {
		return 0
	}
	v, err := strconv.ParseFloat(m[1], 64)
	if err != nil {
		return 0
	}
	return v
}

// --- TypeScript coverage via vitest / npx vitest ---

func covTS(wsRoot string, timeout time.Duration, withCov bool) []coverageEntry {
	// Find directories with vitest/jest test configs
	tsDirs := findTSTestDirs(wsRoot)
	if len(tsDirs) == 0 {
		return []coverageEntry{{
			Language:  "ts",
			Available: false,
			Error:     "no vitest/jest test directories found",
		}}
	}

	var results []coverageEntry
	for _, dir := range tsDirs {
		results = append(results, covTSDir(dir, timeout, withCov))
	}
	return results
}

func covTSDir(dir string, timeout time.Duration, withCov bool) coverageEntry {
	relDir := dir
	if gitRoot, err := findGitRoot(dir); err == nil {
		if rel, err := filepath.Rel(gitRoot, dir); err == nil {
			relDir = rel
		}
	}

	entry := coverageEntry{
		Language:  "ts",
		Directory: relDir,
	}

	// Determine test runner: vitest preferred
	runner := detectTSRunner(dir)
	if runner == "" {
		entry.Available = false
		entry.Error = "no vitest/jest found"
		return entry
	}
	entry.Available = true

	start := time.Now()
	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()

	var cmd *exec.Cmd
	switch runner {
	case "vitest":
		args := []string{"vitest", "run", "--reporter=json"}
		if withCov {
			args = append(args, "--coverage", "--coverage.reporter=json")
		}
		cmd = exec.CommandContext(ctx, "npx", args...)
	case "jest":
		args := []string{"jest", "--json"}
		if withCov {
			args = append(args, "--coverage", "--testCoverageReporters=json-summary")
		}
		cmd = exec.CommandContext(ctx, "npx", args...)
	case "playwright":
		args := []string{"playwright", "test", "--reporter=json"}
		cmd = exec.CommandContext(ctx, "npx", args...)
	}

	cmd.Dir = dir
	out, err := cmd.CombinedOutput()

	entry.Duration = time.Since(start).Truncate(time.Millisecond).String()

	switch runner {
	case "vitest":
		parseVitestJSON(out, &entry)
		if withCov {
			// vitest writes coverage to coverage/coverage-final.json
			covPath := filepath.Join(dir, "coverage", "coverage-summary.json")
			if _, statErr := os.Stat(covPath); statErr == nil {
				entry.LineCov = parseIstanbulSummary(covPath)
			}
		}
	case "jest":
		parseJestJSON(out, &entry)
		if withCov {
			covPath := filepath.Join(dir, "coverage", "coverage-summary.json")
			if _, statErr := os.Stat(covPath); statErr == nil {
				entry.LineCov = parseIstanbulSummary(covPath)
			}
		}
	case "playwright":
		parsePlaywrightJSON(out, &entry)
	}

	if err != nil && entry.FailCount == 0 && entry.PassCount == 0 {
		entry.Error = truncateStr(string(out), 500)
	}

	return entry
}

func parseVitestJSON(out []byte, entry *coverageEntry) {
	// vitest --reporter=json outputs: { "testResults": [...], "numPassedTests": N, ... }
	// The JSON may be preceded by non-JSON lines; find the JSON block
	jsonData := extractJSON(out)
	if jsonData == nil {
		return
	}

	var result struct {
		NumPassedTests  int `json:"numPassedTests"`
		NumFailedTests  int `json:"numFailedTests"`
		NumPendingTests int `json:"numPendingTests"`
		NumTotalTests   int `json:"numTotalTests"`
	}
	if err := json.Unmarshal(jsonData, &result); err != nil {
		return
	}
	entry.TestCount = result.NumTotalTests
	entry.PassCount = result.NumPassedTests
	entry.FailCount = result.NumFailedTests
	entry.SkipCount = result.NumPendingTests
}

func parseJestJSON(out []byte, entry *coverageEntry) {
	jsonData := extractJSON(out)
	if jsonData == nil {
		return
	}

	var result struct {
		NumPassedTests  int `json:"numPassedTests"`
		NumFailedTests  int `json:"numFailedTests"`
		NumPendingTests int `json:"numPendingTests"`
		NumTotalTests   int `json:"numTotalTests"`
	}
	if err := json.Unmarshal(jsonData, &result); err != nil {
		return
	}
	entry.TestCount = result.NumTotalTests
	entry.PassCount = result.NumPassedTests
	entry.FailCount = result.NumFailedTests
	entry.SkipCount = result.NumPendingTests
}

func parsePlaywrightJSON(out []byte, entry *coverageEntry) {
	// Playwright --reporter=json outputs:
	// { "suites": [...], "stats": { "expected": N, "unexpected": N, "skipped": N } }
	jsonData := extractJSON(out)
	if jsonData == nil {
		// Fallback: count "passed"/"failed"/"skipped" from text output
		entry.PassCount = bytes.Count(out, []byte("passed"))
		entry.FailCount = bytes.Count(out, []byte("failed"))
		entry.TestCount = entry.PassCount + entry.FailCount
		return
	}

	var result struct {
		Stats struct {
			Expected   int `json:"expected"`
			Unexpected int `json:"unexpected"`
			Skipped    int `json:"skipped"`
			Flaky      int `json:"flaky"`
		} `json:"stats"`
	}
	if err := json.Unmarshal(jsonData, &result); err != nil {
		return
	}
	entry.PassCount = result.Stats.Expected + result.Stats.Flaky
	entry.FailCount = result.Stats.Unexpected
	entry.SkipCount = result.Stats.Skipped
	entry.TestCount = entry.PassCount + entry.FailCount + entry.SkipCount
}

func parseIstanbulSummary(path string) float64 {
	data, err := os.ReadFile(path)
	if err != nil {
		return 0
	}
	var summary map[string]json.RawMessage
	if err := json.Unmarshal(data, &summary); err != nil {
		return 0
	}
	totalRaw, ok := summary["total"]
	if !ok {
		return 0
	}
	var total struct {
		Lines struct {
			Pct float64 `json:"pct"`
		} `json:"lines"`
	}
	if err := json.Unmarshal(totalRaw, &total); err != nil {
		return 0
	}
	return total.Lines.Pct
}

// --- helpers ---

func findCargoWorkspacesRecursive(dir string) []string {
	var results []string
	filepath.Walk(dir, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return nil
		}
		if info.Name() == "Cargo.toml" && !info.IsDir() {
			data, err := os.ReadFile(path)
			if err != nil {
				return nil
			}
			if bytes.Contains(data, []byte("[workspace]")) {
				results = append(results, filepath.Dir(path))
				return filepath.SkipDir
			}
		}
		// Skip target dirs and hidden dirs
		if info.IsDir() && (info.Name() == "target" || info.Name() == ".cargo-target" || strings.HasPrefix(info.Name(), ".")) {
			return filepath.SkipDir
		}
		return nil
	})
	return results
}

func findGoTestModDirs(wsRoot string) []string {
	var results []string
	candidates := []string{
		filepath.Join(wsRoot, "packages", "cmd", "gftd"),
	}
	for _, dir := range candidates {
		goMod := filepath.Join(dir, "go.mod")
		if _, err := os.Stat(goMod); err == nil {
			results = append(results, dir)
		}
	}
	return results
}

func findTSTestDirs(wsRoot string) []string {
	var results []string
	candidates := []string{
		filepath.Join(wsRoot, "infra", "cloudflare", "workers", "pds"),
		filepath.Join(wsRoot, "packages", "svelte", "appshellv2"),
		filepath.Join(wsRoot, "packages", "runtime", "magatama", "magatama-host-sdk"),
		filepath.Join(wsRoot, "packages", "graph", "kagami"),
		filepath.Join(wsRoot, "packages", "graph", "kagami-provider"),
		filepath.Join(wsRoot, "packages", "graph", "kagami-provider-unified"),
		filepath.Join(wsRoot, "packages", "graph", "kagami-provider-col-projection"),
		filepath.Join(wsRoot, "packages", "graph", "kagami-provider-client-write"),
		filepath.Join(wsRoot, "packages", "graph", "kagami-provider-cas-direct"),
	}
	for _, dir := range candidates {
		if detectTSRunner(dir) != "" {
			results = append(results, dir)
		}
	}
	// Playwright E2E tests require running services — skip by default.
	// Use --lang ts-e2e to include them explicitly.
	return results
}

func detectTSRunner(dir string) string {
	// Check package.json for vitest/jest
	// vitest > jest priority. Playwright E2E is excluded from unit coverage.
	pkgPath := filepath.Join(dir, "package.json")
	data, err := os.ReadFile(pkgPath)
	if err != nil {
		return ""
	}
	if bytes.Contains(data, []byte("vitest")) {
		return "vitest"
	}
	if bytes.Contains(data, []byte("jest")) {
		return "jest"
	}
	return ""
}

func extractJSON(out []byte) []byte {
	// Find the first '{' that starts a valid JSON object.
	// Skip braces inside JSON strings to handle large outputs correctly.
	for i := 0; i < len(out); i++ {
		if out[i] == '{' {
			depth := 0
			inString := false
			escaped := false
			for j := i; j < len(out); j++ {
				ch := out[j]
				if escaped {
					escaped = false
					continue
				}
				if ch == '\\' && inString {
					escaped = true
					continue
				}
				if ch == '"' {
					inString = !inString
					continue
				}
				if inString {
					continue
				}
				switch ch {
				case '{':
					depth++
				case '}':
					depth--
					if depth == 0 {
						return out[i : j+1]
					}
				}
			}
		}
	}
	return nil
}

func truncateStr(s string, maxLen int) string {
	if len(s) <= maxLen {
		return s
	}
	return s[:maxLen] + "..."
}

func printCoverageText(r *testCoverageReport) {
	fmt.Printf("coverage:\n")
	fmt.Printf("  evaluated_at: %s\n", r.EvaluatedAt)
	fmt.Printf("  overall:\n")
	fmt.Printf("    tests: %d (pass: %d, fail: %d, skip: %d)\n",
		r.OverallTests, r.OverallPass, r.OverallFail, r.OverallSkip)
	if r.OverallLineCov > 0 {
		fmt.Printf("    line_coverage: %.1f%%\n", r.OverallLineCov)
	}
	fmt.Printf("  entries:\n")
	for _, e := range r.Entries {
		fmt.Printf("    %s (%s):\n", e.Language, e.Directory)
		if !e.Available {
			fmt.Printf("      available: false\n")
			if e.Error != "" {
				fmt.Printf("      error: %q\n", e.Error)
			}
			continue
		}
		fmt.Printf("      tests: %d (pass: %d, fail: %d, skip: %d)\n",
			e.TestCount, e.PassCount, e.FailCount, e.SkipCount)
		if e.LineCov > 0 {
			fmt.Printf("      line_coverage: %.1f%%\n", e.LineCov)
		}
		if e.Duration != "" {
			fmt.Printf("      duration: %s\n", e.Duration)
		}
		if e.Error != "" {
			fmt.Printf("      error: %q\n", e.Error)
		}
	}
}
