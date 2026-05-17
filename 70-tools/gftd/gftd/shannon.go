package main

import (
	"bufio"
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"flag"
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
	"math"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
	"time"
)

// shIsGenerated returns true if the file path indicates auto-generated code.
// Generated code is a deterministic derivation of its source (Shannon redundancy = 0
// relative to the generator input), so including it inflates redundancy metrics with noise.
func shIsGenerated(path string) bool {
	base := filepath.Base(path)
	// Proto-generated Go
	if strings.HasSuffix(base, ".pb.go") || strings.HasSuffix(base, ".pb.gw.go") || strings.HasSuffix(base, "_grpc.pb.go") {
		return true
	}
	// Generated TypeScript / JavaScript
	if strings.HasSuffix(base, ".generated.ts") || strings.HasSuffix(base, ".generated.js") {
		return true
	}
	// gen/ directory (common convention for generated code)
	if strings.Contains(path, "/gen/") || strings.Contains(path, "/generated/") {
		return true
	}
	// WASM component glue (jco/wasm-tools output)
	if strings.HasSuffix(base, ".component.js") || strings.HasSuffix(base, ".component.wasm") {
		return true
	}
	return false
}

// --- Shannon redundancy report types ---

type shannonCheck struct {
	Name       string          `json:"name"`
	Score      float64         `json:"score"`      // 0-100 (100 = no redundancy)
	Weight     float64         `json:"weight"`
	Violations int             `json:"violations"`
	Details    string          `json:"details,omitempty"`
	Items      []shannonItem   `json:"items,omitempty"`
}

type shannonItem struct {
	Path        string  `json:"path"`
	Kind        string  `json:"kind"`
	Redundancy  float64 `json:"redundancy"` // 0.0-1.0
	DuplicateOf string  `json:"duplicate_of,omitempty"`
	Detail      string  `json:"detail,omitempty"`
}

type shannonReport struct {
	EvaluatedAt    string         `json:"evaluated_at"`
	OverallScore   float64        `json:"overall_score"`    // 0-100
	RedundancyRate float64        `json:"redundancy_rate"`  // 1 - score/100
	Checks         []shannonCheck `json:"checks"`
	Hotspots       []shannonItem  `json:"hotspots"`         // top-N worst redundancy
	ScoringModel   string         `json:"scoring_model"`
}

// --- Check weights ---

var shannonWeights = map[string]float64{
	"claude_md_duplication":   0.25,
	"code_clone_cross":        0.15,
	"collection_write_fan":    0.15,
	"wit_type_duplication":    0.10,
	"config_redundancy":       0.10,
	"dead_code_entropy":       0.10,
	"doc_code_drift":          0.10,
	"rust_duplication":        0.05,
	"stale_symbol_entropy":    0.10,
}

// --- Entry point ---

func runShannon(args []string) error {
	if len(args) == 0 {
		printShannonUsage()
		return nil
	}
	switch args[0] {
	case "scan":
		return runShannonScan(args[1:])
	case "violations":
		return runShannonViolations(args[1:])
	case "dsm":
		return runShannonDSM(args[1:])
	case "bayesnet":
		return runShannonBayesNet(args[1:])
	case "bottleneck":
		return runShannonBottleneck(args[1:])
	case "minimize":
		return runShannonMinimize(args[1:])
	case "help", "--help", "-h":
		printShannonUsage()
		return nil
	default:
		return fmt.Errorf("unknown shannon command: %s", args[0])
	}
}

func printShannonUsage() {
	fmt.Print(`gftd shannon — Shannon redundancy scoring for the entire repository

USAGE:
  gftd shannon <subcommand> [flags]

SUBCOMMANDS:
  scan          Run all redundancy checks and output full report
  violations    List redundancy violations only (no scoring)
  dsm           Dependency Structure Matrix (N×N adjacency + Cuthill-McKee reorder + cycle detection)
  bayesnet      Bayesian change-propagation network (conditional P + high-risk paths)
  bottleneck    Information bottleneck detection (fan-in × fan-out + mutual information)
  minimize      Entropy minimization proposals (merge/split/move suggestions)

FLAGS:
  --json        Output as JSON (default: human-readable)
  --top N       Number of hotspots to show (default: 15)
  --workspace-dir DIR  Workspace root (default: git root)

CHECKS:
  claude_md_duplication   CLAUDE.md inter-file rule duplication (weight: 0.25)
  code_clone_cross        Cross-project code clone detection (weight: 0.15)
  collection_write_fan    Multiple apps writing same collection (weight: 0.15)
  wit_type_duplication    Duplicate WIT type definitions (weight: 0.10)
  config_redundancy       Duplicate config values across wrangler.jsonc (weight: 0.10)
  dead_code_entropy       Zero-entropy code: empty funcs, stub handlers (weight: 0.10)
  doc_code_drift          CLAUDE.md evidence link staleness (weight: 0.10)
  rust_duplication        Rust AST near-duplicate function detection (weight: 0.05)
  stale_symbol_entropy    Stale WIT bindings + CLAUDE.md strikethrough (weight: 0.10)
`)
}

// shannonFlatRow is the Parquet-serialisable flat record for one shannon scan snapshot.
type shannonFlatRow struct {
	ScannedAt              string  `json:"scanned_at"`
	OverallScore           float64 `json:"overall_score"`
	RedundancyRate         float64 `json:"redundancy_rate"`
	ClaudeMdDuplication    float64 `json:"claude_md_duplication"`
	CodeCloneCross         float64 `json:"code_clone_cross"`
	CollectionWriteFan     float64 `json:"collection_write_fan"`
	WitTypeDuplication     float64 `json:"wit_type_duplication"`
	ConfigRedundancy       float64 `json:"config_redundancy"`
	DeadCodeEntropy        float64 `json:"dead_code_entropy"`
	DocCodeDrift           float64 `json:"doc_code_drift"`
	RustDuplication        float64 `json:"rust_duplication"`
	StaleSymbolEntropy     float64 `json:"stale_symbol_entropy"`
}

func storeShannonResults(wsRoot string, report *shannonReport) error {
	row := shannonFlatRow{
		ScannedAt:      report.EvaluatedAt,
		OverallScore:   report.OverallScore,
		RedundancyRate: report.RedundancyRate,
	}
	for _, c := range report.Checks {
		switch c.Name {
		case "claude_md_duplication":
			row.ClaudeMdDuplication = c.Score
		case "code_clone_cross":
			row.CodeCloneCross = c.Score
		case "collection_write_fan":
			row.CollectionWriteFan = c.Score
		case "wit_type_duplication":
			row.WitTypeDuplication = c.Score
		case "config_redundancy":
			row.ConfigRedundancy = c.Score
		case "dead_code_entropy":
			row.DeadCodeEntropy = c.Score
		case "doc_code_drift":
			row.DocCodeDrift = c.Score
		case "rust_duplication":
			row.RustDuplication = c.Score
		case "stale_symbol_entropy":
			row.StaleSymbolEntropy = c.Score
		}
	}
	summary := fmt.Sprintf("score=%.1f redundancy=%.2f", report.OverallScore, report.RedundancyRate)
	path, err := storeParquet(wsRoot, "shannon", summary, []shannonFlatRow{row})
	if err != nil {
		return err
	}
	fmt.Fprintf(os.Stderr, "shannon: stored %s\n", path)
	return nil
}

func runShannonScan(args []string) error {
	fs := flag.NewFlagSet("shannon scan", flag.ContinueOnError)
	workspaceDir := fs.String("workspace-dir", "", "workspace root (default: git root)")
	jsonOut := fs.Bool("json", false, "output as JSON")
	topN := fs.Int("top", 15, "number of hotspots to show")
	store := fs.Bool("store", false, "store results as Parquet snapshot in 80-data/shannon/")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	wsRoot, err := resolveShannonRoot(*workspaceDir)
	if err != nil {
		return err
	}

	checks := runAllShannonChecks(wsRoot)
	report := buildShannonReport(checks, *topN)

	if *store {
		if err := storeShannonResults(wsRoot, report); err != nil {
			fmt.Fprintf(os.Stderr, "shannon store warning: %v\n", err)
		}
	}

	if *jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(report)
	}

	printShannonText(report)
	return nil
}

func runShannonViolations(args []string) error {
	fs := flag.NewFlagSet("shannon violations", flag.ContinueOnError)
	workspaceDir := fs.String("workspace-dir", "", "workspace root (default: git root)")
	jsonOut := fs.Bool("json", false, "output as JSON")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	wsRoot, err := resolveShannonRoot(*workspaceDir)
	if err != nil {
		return err
	}

	checks := runAllShannonChecks(wsRoot)

	var allItems []shannonItem
	for _, c := range checks {
		allItems = append(allItems, c.Items...)
	}

	sort.Slice(allItems, func(i, j int) bool {
		return allItems[i].Redundancy > allItems[j].Redundancy
	})

	if *jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(allItems)
	}

	for _, item := range allItems {
		fmt.Printf("  [%.0f%%] %s: %s — %s\n", item.Redundancy*100, item.Kind, item.Path, item.Detail)
	}
	fmt.Printf("\ntotal violations: %d\n", len(allItems))
	return nil
}

func resolveShannonRoot(override string) (string, error) {
	if override != "" {
		return filepath.Abs(override)
	}
	cwd, err := os.Getwd()
	if err != nil {
		return "", fmt.Errorf("getwd: %w", err)
	}
	root, err := findGitRoot(cwd)
	if err != nil {
		return "", fmt.Errorf("detect workspace root: %w", err)
	}
	return filepath.Abs(root)
}

func runAllShannonChecks(wsRoot string) []shannonCheck {
	return []shannonCheck{
		shCheckClaudeMdDuplication(wsRoot),
		shCheckCodeCloneCross(wsRoot),
		shCheckCollectionWriteFan(wsRoot),
		shCheckWitTypeDuplication(wsRoot),
		shCheckConfigRedundancy(wsRoot),
		shCheckDeadCodeEntropy(wsRoot),
		shCheckDocCodeDrift(wsRoot),
		shCheckRustDuplication(wsRoot),
		shCheckStaleSymbolEntropy(wsRoot),
	}
}

func buildShannonReport(checks []shannonCheck, topN int) *shannonReport {
	var weightedSum float64
	var totalWeight float64
	var allItems []shannonItem

	for i := range checks {
		w := shannonWeights[checks[i].Name]
		checks[i].Weight = w
		weightedSum += checks[i].Score * w
		totalWeight += w
		allItems = append(allItems, checks[i].Items...)
	}

	overall := 0.0
	if totalWeight > 0 {
		overall = weightedSum / totalWeight
	}

	// Sort hotspots by redundancy descending
	sort.Slice(allItems, func(i, j int) bool {
		return allItems[i].Redundancy > allItems[j].Redundancy
	})
	if len(allItems) > topN {
		allItems = allItems[:topN]
	}

	var checkNames []string
	for _, c := range checks {
		checkNames = append(checkNames, fmt.Sprintf("%s(%.0f%%×%.0f)", c.Name, c.Score, c.Weight*100))
	}

	return &shannonReport{
		EvaluatedAt:    time.Now().UTC().Format(time.RFC3339),
		OverallScore:   overall,
		RedundancyRate: 1 - overall/100,
		Checks:         checks,
		Hotspots:       allItems,
		ScoringModel:   fmt.Sprintf("weighted: %s", strings.Join(checkNames, " + ")),
	}
}

func printShannonText(r *shannonReport) {
	fmt.Printf("shannon:\n")
	fmt.Printf("  evaluated_at: %s\n", r.EvaluatedAt)
	fmt.Printf("  overall_score: %.1f\n", r.OverallScore)
	fmt.Printf("  redundancy_rate: %.1f%%\n", r.RedundancyRate*100)
	fmt.Printf("  checks:\n")
	for _, c := range r.Checks {
		fmt.Printf("    %s:\n", c.Name)
		fmt.Printf("      score: %.1f (weight: %.0f%%)\n", c.Score, c.Weight*100)
		fmt.Printf("      violations: %d\n", c.Violations)
		if c.Details != "" {
			fmt.Printf("      details: %q\n", c.Details)
		}
	}
	if len(r.Hotspots) > 0 {
		fmt.Printf("  hotspots:\n")
		for _, h := range r.Hotspots {
			fmt.Printf("    - [%.0f%%] %s: %s\n", h.Redundancy*100, h.Kind, h.Path)
			if h.Detail != "" {
				fmt.Printf("            %s\n", h.Detail)
			}
		}
	}
}

// =============================================================================
// Check 1: CLAUDE.md inter-file rule duplication
// =============================================================================

// shNormLine normalizes a line for comparison: lowercase, collapse whitespace, strip markdown formatting.
func shNormLine(s string) string {
	s = strings.ToLower(s)
	s = strings.TrimSpace(s)
	// Strip markdown bold/italic
	s = strings.ReplaceAll(s, "**", "")
	s = strings.ReplaceAll(s, "*", "")
	s = strings.ReplaceAll(s, "`", "")
	// Collapse whitespace
	parts := strings.Fields(s)
	return strings.Join(parts, " ")
}

func shCheckClaudeMdDuplication(wsRoot string) shannonCheck {
	check := shannonCheck{Name: "claude_md_duplication"}

	// Find all CLAUDE.md files
	var claudeFiles []string
	_ = filepath.Walk(wsRoot, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return nil
		}
		if info.IsDir() {
			base := info.Name()
			if base == "node_modules" || base == ".git" || base == "target" || base == ".cargo-target" {
				return filepath.SkipDir
			}
			return nil
		}
		if info.Name() == "CLAUDE.md" {
			claudeFiles = append(claudeFiles, path)
		}
		return nil
	})

	if len(claudeFiles) < 2 {
		check.Score = 100
		check.Details = "fewer than 2 CLAUDE.md files"
		return check
	}

	// Extract significant lines (skip headers, empty, short lines)
	type claudeDoc struct {
		path  string
		lines []string // normalized significant lines
		hashes map[string]string // hash → original line
	}

	var docs []claudeDoc
	for _, f := range claudeFiles {
		content, err := os.ReadFile(f)
		if err != nil {
			continue
		}

		rel, _ := filepath.Rel(wsRoot, f)
		doc := claudeDoc{path: rel, hashes: make(map[string]string)}

		scanner := bufio.NewScanner(bytes.NewReader(content))
		inFrontmatter := false
		for scanner.Scan() {
			line := scanner.Text()
			trimmed := strings.TrimSpace(line)

			// Skip frontmatter
			if trimmed == "---" {
				inFrontmatter = !inFrontmatter
				continue
			}
			if inFrontmatter {
				continue
			}

			// Skip short lines, pure headers, empty, table separators
			if len(trimmed) < 20 {
				continue
			}
			if strings.HasPrefix(trimmed, "#") && !strings.Contains(trimmed, "—") && len(trimmed) < 60 {
				continue
			}
			if strings.HasPrefix(trimmed, "|---") || strings.HasPrefix(trimmed, "| ---") {
				continue
			}

			norm := shNormLine(trimmed)
			if len(norm) < 15 {
				continue
			}

			h := sha256.Sum256([]byte(norm))
			hash := hex.EncodeToString(h[:8])
			doc.lines = append(doc.lines, hash)
			doc.hashes[hash] = trimmed
		}
		if len(doc.lines) > 0 {
			docs = append(docs, doc)
		}
	}

	// Find root CLAUDE.md
	rootIdx := -1
	for i, d := range docs {
		if d.path == "CLAUDE.md" {
			rootIdx = i
			break
		}
	}

	// Build line→files index
	lineFiles := make(map[string][]int) // hash → doc indices
	for i, d := range docs {
		seen := make(map[string]bool)
		for _, h := range d.lines {
			if !seen[h] {
				lineFiles[h] = append(lineFiles[h], i)
				seen[h] = true
			}
		}
	}

	// Count duplicated lines (same line in 2+ files)
	totalUnique := len(lineFiles)
	duplicated := 0
	for hash, indices := range lineFiles {
		if len(indices) < 2 {
			continue
		}
		duplicated++

		// Find parent-child pair (root has everything, so only flag non-root duplication or root-child)
		for _, idx := range indices {
			if idx == rootIdx {
				continue
			}
			// This child duplicates something from another file
			dupOf := ""
			for _, other := range indices {
				if other != idx {
					dupOf = docs[other].path
					break
				}
			}
			original := ""
			if orig, ok := docs[idx].hashes[hash]; ok {
				if len(orig) > 80 {
					original = orig[:80] + "..."
				} else {
					original = orig
				}
			}
			check.Items = append(check.Items, shannonItem{
				Path:        docs[idx].path,
				Kind:        "claude_md_duplication",
				Redundancy:  1.0,
				DuplicateOf: dupOf,
				Detail:      original,
			})
		}
	}

	// Deduplicate items (same path+hash counted once)
	check.Items = shDeduplicateItems(check.Items)

	check.Violations = duplicated
	if totalUnique > 0 {
		check.Score = shCap(100 - float64(duplicated)/float64(totalUnique)*100)
	} else {
		check.Score = 100
	}
	if duplicated > 0 {
		check.Details = fmt.Sprintf("%d/%d lines duplicated across %d CLAUDE.md files", duplicated, totalUnique, len(docs))
	}
	return check
}

// shFuncSig represents a function signature + body hash for duplication detection.
type shFuncSig struct {
	path    string
	name    string
	bodyLen int
	hash    string
}

// =============================================================================
// Check 2: Cross-project code clone detection
// =============================================================================

func shCheckCodeCloneCross(wsRoot string) shannonCheck {
	check := shannonCheck{Name: "code_clone_cross"}

	var funcs []shFuncSig

	projectDirs := []string{
		filepath.Join(wsRoot, "projects"),
		filepath.Join(wsRoot, "infra", "cloudflare"),
	}

	for _, baseDir := range projectDirs {
		_ = filepath.Walk(baseDir, func(path string, info os.FileInfo, err error) error {
			if err != nil {
				return nil
			}
			if info.IsDir() {
				base := info.Name()
				if base == "node_modules" || base == ".git" || base == "target" || base == ".cargo-target" || base == "_svelte" {
					return filepath.SkipDir
				}
				return nil
			}
			if !strings.HasSuffix(path, ".go") || strings.HasSuffix(path, "_test.go") {
				return nil
			}
			if shIsGenerated(path) {
				return nil
			}
			content, err := os.ReadFile(path)
			if err != nil {
				return nil
			}
			rel, _ := filepath.Rel(wsRoot, path)
			extracted := shExtractGoFuncHashes(rel, content)
			funcs = append(funcs, extracted...)
			return nil
		})
	}

	// Also scan TypeScript files
	for _, baseDir := range projectDirs {
		_ = filepath.Walk(baseDir, func(path string, info os.FileInfo, err error) error {
			if err != nil {
				return nil
			}
			if info.IsDir() {
				base := info.Name()
				if base == "node_modules" || base == ".git" || base == "target" || base == ".cargo-target" || base == "_svelte" {
					return filepath.SkipDir
				}
				return nil
			}
			if !strings.HasSuffix(path, ".ts") || strings.HasSuffix(path, ".d.ts") || strings.HasSuffix(path, ".test.ts") {
				return nil
			}
			if shIsGenerated(path) {
				return nil
			}
			content, err := os.ReadFile(path)
			if err != nil {
				return nil
			}
			rel, _ := filepath.Rel(wsRoot, path)
			extracted := shExtractTSFuncHashes(rel, content)
			funcs = append(funcs, extracted...)
			return nil
		})
	}

	// Also scan Rust files
	for _, baseDir := range []string{
		filepath.Join(wsRoot, "packages", "server"),
		filepath.Join(wsRoot, "packages", "runtime"),
		filepath.Join(wsRoot, "packages", "kami-engine"),
	} {
		_ = filepath.Walk(baseDir, func(path string, info os.FileInfo, err error) error {
			if err != nil {
				return nil
			}
			if info.IsDir() {
				base := info.Name()
				if base == "node_modules" || base == ".git" || base == "target" || base == ".cargo-target" {
					return filepath.SkipDir
				}
				return nil
			}
			if !strings.HasSuffix(path, ".rs") || strings.Contains(path, "/tests/") {
				return nil
			}
			if shIsGenerated(path) {
				return nil
			}
			content, err := os.ReadFile(path)
			if err != nil {
				return nil
			}
			rel, _ := filepath.Rel(wsRoot, path)
			extracted := shExtractRustFuncHashes(rel, content)
			funcs = append(funcs, extracted...)
			return nil
		})
	}

	// Group by hash — same hash = duplicated function body
	hashGroup := make(map[string][]shFuncSig)
	for _, f := range funcs {
		if f.bodyLen < 5 { // ignore tiny functions
			continue
		}
		hashGroup[f.hash] = append(hashGroup[f.hash], f)
	}

	cloneGroups := 0
	cloneFuncs := 0
	for _, group := range hashGroup {
		if len(group) < 2 {
			continue
		}
		// Check cross-project: different top-level dirs
		projects := make(map[string]bool)
		for _, f := range group {
			parts := strings.SplitN(f.path, "/", 3)
			if len(parts) >= 2 {
				projects[parts[0]+"/"+parts[1]] = true
			}
		}
		if len(projects) < 2 {
			continue // same project, tolerable
		}

		cloneGroups++
		cloneFuncs += len(group)

		first := group[0]
		for _, dup := range group[1:] {
			check.Items = append(check.Items, shannonItem{
				Path:        dup.path,
				Kind:        "code_clone_cross",
				Redundancy:  1.0,
				DuplicateOf: first.path,
				Detail:      fmt.Sprintf("func %s (%d lines) identical to %s:%s", dup.name, dup.bodyLen, first.path, first.name),
			})
		}
	}

	totalFuncs := len(funcs)
	check.Violations = cloneGroups
	if totalFuncs > 0 {
		check.Score = shCap(100 - float64(cloneFuncs)/float64(totalFuncs)*100)
	} else {
		check.Score = 100
	}
	if cloneGroups > 0 {
		check.Details = fmt.Sprintf("%d cross-project clone groups (%d duplicated functions / %d total)", cloneGroups, cloneFuncs, totalFuncs)
	}
	return check
}

// =============================================================================
// Check 3: Collection write fan-out
// =============================================================================

func shCheckCollectionWriteFan(wsRoot string) shannonCheck {
	check := shannonCheck{Name: "collection_write_fan"}

	// Scan main.go files for WRecord/ComAtprotoRepoCreateRecord/AppBskyFeedPostAs/DIDWrite calls
	type writeInfo struct {
		collection string
		app        string
	}

	var writes []writeInfo

	projectsDir := filepath.Join(wsRoot, "projects")
	_ = filepath.Walk(projectsDir, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return nil
		}
		if info.IsDir() {
			base := info.Name()
			if base == "node_modules" || base == ".git" || base == "target" || base == ".cargo-target" || base == "_svelte" || base == "svelte" {
				return filepath.SkipDir
			}
			return nil
		}
		if info.Name() != "main.go" {
			return nil
		}
		content, err := os.ReadFile(path)
		if err != nil {
			return nil
		}

		// Extract app name from path: projects/<app>/wasm/<component>/main.go
		rel, _ := filepath.Rel(wsRoot, path)
		parts := strings.Split(rel, "/")
		appName := ""
		for i, p := range parts {
			if p == "projects" && i+1 < len(parts) {
				appName = parts[i+1]
				break
			}
		}
		if appName == "" {
			return nil
		}

		// Extract write targets
		ast := sgExtractGoAST(path, content)
		for _, w := range ast.Writes {
			writes = append(writes, writeInfo{collection: w, app: appName})
		}

		return nil
	})

	// Group by collection
	collWriters := make(map[string]map[string]bool) // collection → set of apps
	for _, w := range writes {
		if collWriters[w.collection] == nil {
			collWriters[w.collection] = make(map[string]bool)
		}
		collWriters[w.collection][w.app] = true
	}

	totalCollections := len(collWriters)
	multiWriter := 0
	for coll, apps := range collWriters {
		if len(apps) <= 1 {
			continue
		}
		multiWriter++
		appList := make([]string, 0, len(apps))
		for a := range apps {
			appList = append(appList, a)
		}
		sort.Strings(appList)

		check.Items = append(check.Items, shannonItem{
			Path:       coll,
			Kind:       "collection_write_fan",
			Redundancy: 1.0 - 1.0/float64(len(apps)),
			Detail:     fmt.Sprintf("written by %d apps: %s", len(apps), strings.Join(appList, ", ")),
		})
	}

	check.Violations = multiWriter
	if totalCollections > 0 {
		check.Score = shCap(100 - float64(multiWriter)/float64(totalCollections)*100)
	} else {
		check.Score = 100
	}
	if multiWriter > 0 {
		check.Details = fmt.Sprintf("%d/%d collections written by multiple apps", multiWriter, totalCollections)
	}
	return check
}

// =============================================================================
// Check 4: WIT type duplication
// =============================================================================

func shCheckWitTypeDuplication(wsRoot string) shannonCheck {
	check := shannonCheck{Name: "wit_type_duplication"}

	type witType struct {
		name string
		kind string // "record", "enum", "variant", "flags"
		file string
	}

	var types []witType

	witPattern := regexp.MustCompile(`^\s*(record|enum|variant|flags)\s+(\S+)\s*\{`)

	witDirs := []string{
		filepath.Join(wsRoot, "packages", "contract", "wit"),
	}
	// Also scan project wit/ dirs
	projectsDir := filepath.Join(wsRoot, "projects")
	entries, _ := os.ReadDir(projectsDir)
	for _, e := range entries {
		if e.IsDir() {
			witDir := filepath.Join(projectsDir, e.Name(), "wit")
			if _, err := os.Stat(witDir); err == nil {
				witDirs = append(witDirs, witDir)
			}
		}
	}

	for _, dir := range witDirs {
		_ = filepath.Walk(dir, func(path string, info os.FileInfo, err error) error {
			if err != nil || info.IsDir() || !strings.HasSuffix(path, ".wit") {
				return nil
			}
			content, err := os.ReadFile(path)
			if err != nil {
				return nil
			}
			rel, _ := filepath.Rel(wsRoot, path)
			scanner := bufio.NewScanner(bytes.NewReader(content))
			for scanner.Scan() {
				line := scanner.Text()
				if m := witPattern.FindStringSubmatch(line); m != nil {
					types = append(types, witType{name: m[2], kind: m[1], file: rel})
				}
			}
			return nil
		})
	}

	// Group by name+kind
	typeGroup := make(map[string][]witType)
	for _, t := range types {
		key := t.kind + ":" + t.name
		typeGroup[key] = append(typeGroup[key], t)
	}

	totalTypes := len(typeGroup)
	duplicated := 0
	for _, group := range typeGroup {
		if len(group) < 2 {
			continue
		}
		duplicated++
		first := group[0]
		for _, dup := range group[1:] {
			check.Items = append(check.Items, shannonItem{
				Path:        dup.file,
				Kind:        "wit_type_duplication",
				Redundancy:  1.0,
				DuplicateOf: first.file,
				Detail:      fmt.Sprintf("%s %s also defined in %s", dup.kind, dup.name, first.file),
			})
		}
	}

	check.Violations = duplicated
	if totalTypes > 0 {
		check.Score = shCap(100 - float64(duplicated)/float64(totalTypes)*100)
	} else {
		check.Score = 100
	}
	if duplicated > 0 {
		check.Details = fmt.Sprintf("%d/%d WIT types duplicated across files", duplicated, totalTypes)
	}
	return check
}

// =============================================================================
// Check 5: Config redundancy (wrangler.jsonc)
// =============================================================================

func shCheckConfigRedundancy(wsRoot string) shannonCheck {
	check := shannonCheck{Name: "config_redundancy"}

	type configEntry struct {
		key   string
		value string
		file  string
	}

	var entries []configEntry

	_ = filepath.Walk(wsRoot, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return nil
		}
		if info.IsDir() {
			base := info.Name()
			if base == "node_modules" || base == ".git" || base == "target" || base == ".cargo-target" {
				return filepath.SkipDir
			}
			return nil
		}
		if info.Name() != "wrangler.jsonc" && info.Name() != "wrangler.json" {
			return nil
		}
		content, err := os.ReadFile(path)
		if err != nil {
			return nil
		}
		rel, _ := filepath.Rel(wsRoot, path)

		// Strip JSONC comments for parsing
		cleaned := shStripJsoncComments(content)

		var parsed map[string]interface{}
		if err := json.Unmarshal(cleaned, &parsed); err != nil {
			return nil
		}

		// Extract vars (exclude deploy-injected vars — deterministic output of gftd deploy)
		if vars, ok := parsed["vars"].(map[string]interface{}); ok {
			for k, v := range vars {
				if shIsDeployInjectedVar(k) {
					continue
				}
				entries = append(entries, configEntry{
					key:   k,
					value: fmt.Sprintf("%v", v),
					file:  rel,
				})
			}
		}

		return nil
	})

	// Group by key+value
	kvGroup := make(map[string][]configEntry)
	for _, e := range entries {
		key := e.key + "=" + e.value
		kvGroup[key] = append(kvGroup[key], e)
	}

	totalEntries := len(kvGroup)
	redundant := 0
	for _, group := range kvGroup {
		if len(group) < 3 { // 2 is common (dev/prod), 3+ is redundant
			continue
		}
		redundant++
		files := make([]string, len(group))
		for i, g := range group {
			files[i] = g.file
		}
		check.Items = append(check.Items, shannonItem{
			Path:       group[0].key,
			Kind:       "config_redundancy",
			Redundancy: 1.0 - 1.0/float64(len(group)),
			Detail:     fmt.Sprintf("%s=%s in %d files", group[0].key, group[0].value, len(group)),
		})
	}

	check.Violations = redundant
	if totalEntries > 0 {
		check.Score = shCap(100 - float64(redundant)/float64(totalEntries)*100)
	} else {
		check.Score = 100
	}
	if redundant > 0 {
		check.Details = fmt.Sprintf("%d/%d config key=value pairs appear in 3+ files", redundant, totalEntries)
	}
	return check
}

// =============================================================================
// Check 6: Dead code entropy (empty funcs, stubs, TODO-only bodies)
// =============================================================================

func shCheckDeadCodeEntropy(wsRoot string) shannonCheck {
	check := shannonCheck{Name: "dead_code_entropy"}

	totalFuncs := 0
	deadFuncs := 0

	scanDirs := []string{
		filepath.Join(wsRoot, "projects"),
		filepath.Join(wsRoot, "infra", "cloudflare"),
		filepath.Join(wsRoot, "packages", "server"),
		filepath.Join(wsRoot, "packages", "runtime"),
	}

	for _, dir := range scanDirs {
		_ = filepath.Walk(dir, func(path string, info os.FileInfo, err error) error {
			if err != nil {
				return nil
			}
			if info.IsDir() {
				base := info.Name()
				if base == "node_modules" || base == ".git" || base == "target" || base == ".cargo-target" || base == "_svelte" {
					return filepath.SkipDir
				}
				return nil
			}

			if shIsGenerated(path) {
				return nil
			}

			rel, _ := filepath.Rel(wsRoot, path)

			switch {
			case strings.HasSuffix(path, ".go") && !strings.HasSuffix(path, "_test.go"):
				t, d, items := shScanGoDeadFuncs(path, content(path), rel)
				totalFuncs += t
				deadFuncs += d
				check.Items = append(check.Items, items...)
			case strings.HasSuffix(path, ".rs") && !strings.Contains(path, "/tests/"):
				t, d, items := shScanRustDeadFuncs(path, rel)
				totalFuncs += t
				deadFuncs += d
				check.Items = append(check.Items, items...)
			case strings.HasSuffix(path, ".ts") && !strings.HasSuffix(path, ".d.ts") && !strings.HasSuffix(path, ".test.ts"):
				t, d, items := shScanTSDeadFuncs(path, rel)
				totalFuncs += t
				deadFuncs += d
				check.Items = append(check.Items, items...)
			}

			return nil
		})
	}

	check.Violations = deadFuncs
	if totalFuncs > 0 {
		check.Score = shCap(100 - float64(deadFuncs)/float64(totalFuncs)*100)
	} else {
		check.Score = 100
	}
	if deadFuncs > 0 {
		check.Details = fmt.Sprintf("%d/%d functions are dead (empty/stub/TODO-only)", deadFuncs, totalFuncs)
	}
	return check
}

func content(path string) []byte {
	b, _ := os.ReadFile(path)
	return b
}

func shScanGoDeadFuncs(path string, src []byte, relPath string) (total, dead int, items []shannonItem) {
	fset := token.NewFileSet()
	f, err := parser.ParseFile(fset, path, src, parser.ParseComments)
	if err != nil {
		return
	}

	for _, decl := range f.Decls {
		fn, ok := decl.(*ast.FuncDecl)
		if !ok || fn.Body == nil {
			continue
		}
		total++

		if len(fn.Body.List) == 0 {
			dead++
			items = append(items, shannonItem{
				Path:       relPath,
				Kind:       "dead_code_entropy",
				Redundancy: 1.0,
				Detail:     fmt.Sprintf("func %s: empty body", fn.Name.Name),
			})
			continue
		}

		// Check if body is only comments/TODO/panic
		bodyText := string(src[fn.Body.Pos()-1 : fn.Body.End()-1])
		stripped := shStripCommentsGo(bodyText)
		stripped = strings.TrimSpace(stripped)
		stripped = strings.Trim(stripped, "{}")
		stripped = strings.TrimSpace(stripped)
		if stripped == "" || strings.HasPrefix(stripped, "panic(") || strings.HasPrefix(stripped, "// TODO") {
			dead++
			items = append(items, shannonItem{
				Path:       relPath,
				Kind:       "dead_code_entropy",
				Redundancy: 0.9,
				Detail:     fmt.Sprintf("func %s: stub (panic/TODO only)", fn.Name.Name),
			})
		}
	}
	return
}

var (
	shRustFnRe    = regexp.MustCompile(`(?m)^(?:\s*(?:pub(?:\(crate\))?\s+)?(?:async\s+)?fn\s+(\w+))`)
	shRustEmptyRe = regexp.MustCompile(`(?m)fn\s+\w+[^{]*\{\s*\}`)
	shRustStubRe  = regexp.MustCompile(`(?m)fn\s+\w+[^{]*\{\s*(?:todo!\(\)|unimplemented!\(\)|panic!\()\s*\}`)
	shTSFnRe      = regexp.MustCompile(`(?m)^(?:export\s+)?(?:async\s+)?function\s+(\w+)`)
	shTSEmptyRe   = regexp.MustCompile(`(?m)function\s+\w+[^{]*\{\s*\}`)
	shTSStubRe    = regexp.MustCompile(`(?m)function\s+\w+[^{]*\{\s*(?:throw|// TODO|/\* TODO)\s`)
)

func shScanRustDeadFuncs(path, relPath string) (total, dead int, items []shannonItem) {
	src, err := os.ReadFile(path)
	if err != nil {
		return
	}
	s := string(src)

	total = len(shRustFnRe.FindAllString(s, -1))
	emptyCount := len(shRustEmptyRe.FindAllString(s, -1))
	stubCount := len(shRustStubRe.FindAllString(s, -1))
	dead = emptyCount + stubCount

	if emptyCount > 0 {
		items = append(items, shannonItem{
			Path:       relPath,
			Kind:       "dead_code_entropy",
			Redundancy: 1.0,
			Detail:     fmt.Sprintf("%d empty fn bodies", emptyCount),
		})
	}
	if stubCount > 0 {
		items = append(items, shannonItem{
			Path:       relPath,
			Kind:       "dead_code_entropy",
			Redundancy: 0.9,
			Detail:     fmt.Sprintf("%d stub fn (todo!/unimplemented!/panic!)", stubCount),
		})
	}
	return
}

func shScanTSDeadFuncs(path, relPath string) (total, dead int, items []shannonItem) {
	src, err := os.ReadFile(path)
	if err != nil {
		return
	}
	s := string(src)

	total = len(shTSFnRe.FindAllString(s, -1))
	emptyCount := len(shTSEmptyRe.FindAllString(s, -1))
	stubCount := len(shTSStubRe.FindAllString(s, -1))
	dead = emptyCount + stubCount

	if emptyCount > 0 {
		items = append(items, shannonItem{
			Path:       relPath,
			Kind:       "dead_code_entropy",
			Redundancy: 1.0,
			Detail:     fmt.Sprintf("%d empty function bodies", emptyCount),
		})
	}
	if stubCount > 0 {
		items = append(items, shannonItem{
			Path:       relPath,
			Kind:       "dead_code_entropy",
			Redundancy: 0.9,
			Detail:     fmt.Sprintf("%d stub functions (throw/TODO)", stubCount),
		})
	}
	return
}

// =============================================================================
// Check 7: Document-code drift (CLAUDE.md evidence link verification)
// =============================================================================

var shEvidenceRe = regexp.MustCompile(`evidence:\s*` + "`" + `([^` + "`" + `]+)` + "`")
var shStatusTagRe = regexp.MustCompile(`\[(PRODUCTION|IMPLEMENTED)\]`)

func shCheckDocCodeDrift(wsRoot string) shannonCheck {
	check := shannonCheck{Name: "doc_code_drift"}

	totalClaims := 0
	staleClaims := 0

	_ = filepath.Walk(wsRoot, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return nil
		}
		if info.IsDir() {
			base := info.Name()
			if base == "node_modules" || base == ".git" || base == "target" || base == ".cargo-target" {
				return filepath.SkipDir
			}
			return nil
		}
		if info.Name() != "CLAUDE.md" {
			return nil
		}

		src, err := os.ReadFile(path)
		if err != nil {
			return nil
		}
		rel, _ := filepath.Rel(wsRoot, path)
		lines := strings.Split(string(src), "\n")

		for _, line := range lines {
			if !shStatusTagRe.MatchString(line) {
				continue
			}

			// Check evidence links on this and following lines
			matches := shEvidenceRe.FindAllStringSubmatch(line, -1)
			for _, m := range matches {
				totalClaims++
				evidencePath := m[1]
				// Parse "file:Lnnn" or "file:line"
				filePart := evidencePath
				if idx := strings.LastIndex(filePart, ":"); idx > 0 {
					filePart = filePart[:idx]
				}
				// Also handle (funcName) suffix
				if idx := strings.Index(filePart, " ("); idx > 0 {
					filePart = filePart[:idx]
				}

				fullPath := filepath.Join(wsRoot, filePart)
				if _, err := os.Stat(fullPath); err != nil {
					staleClaims++
					check.Items = append(check.Items, shannonItem{
						Path:       rel,
						Kind:       "doc_code_drift",
						Redundancy: 1.0,
						Detail:     fmt.Sprintf("evidence file missing: %s", evidencePath),
					})
				}
			}
		}
		return nil
	})

	check.Violations = staleClaims
	if totalClaims > 0 {
		check.Score = shCap(100 - float64(staleClaims)/float64(totalClaims)*100)
	} else {
		check.Score = 100
		check.Details = "no [PRODUCTION]/[IMPLEMENTED] evidence links found"
	}
	if staleClaims > 0 {
		check.Details = fmt.Sprintf("%d/%d evidence links are stale (file missing)", staleClaims, totalClaims)
	}
	return check
}

// =============================================================================
// Check 8: Rust near-duplicate function detection (AST-level)
// =============================================================================

func shCheckRustDuplication(wsRoot string) shannonCheck {
	check := shannonCheck{Name: "rust_duplication"}

	var funcs []shFuncSig

	rustDirs := []string{
		filepath.Join(wsRoot, "packages", "server"),
		filepath.Join(wsRoot, "packages", "runtime"),
		filepath.Join(wsRoot, "packages", "kami-engine"),
	}

	for _, dir := range rustDirs {
		_ = filepath.Walk(dir, func(path string, info os.FileInfo, err error) error {
			if err != nil {
				return nil
			}
			if info.IsDir() {
				base := info.Name()
				if base == "target" || base == ".cargo-target" || base == ".git" {
					return filepath.SkipDir
				}
				return nil
			}
			if !strings.HasSuffix(path, ".rs") || strings.Contains(path, "/tests/") {
				return nil
			}
			if shIsGenerated(path) {
				return nil
			}
			content, err := os.ReadFile(path)
			if err != nil {
				return nil
			}
			rel, _ := filepath.Rel(wsRoot, path)
			extracted := shExtractRustFuncHashes(rel, content)
			funcs = append(funcs, extracted...)
			return nil
		})
	}

	// Group by hash
	hashGroup := make(map[string][]shFuncSig)
	for _, f := range funcs {
		if f.bodyLen < 5 {
			continue
		}
		hashGroup[f.hash] = append(hashGroup[f.hash], f)
	}

	totalFuncs := len(funcs)
	dupGroups := 0
	dupFuncs := 0

	for _, group := range hashGroup {
		if len(group) < 2 {
			continue
		}
		dupGroups++
		dupFuncs += len(group)

		first := group[0]
		for _, dup := range group[1:] {
			check.Items = append(check.Items, shannonItem{
				Path:        dup.path,
				Kind:        "rust_duplication",
				Redundancy:  1.0,
				DuplicateOf: first.path,
				Detail:      fmt.Sprintf("fn %s (%d lines) identical to %s::%s", dup.name, dup.bodyLen, first.path, first.name),
			})
		}
	}

	check.Violations = dupGroups
	if totalFuncs > 0 {
		check.Score = shCap(100 - float64(dupFuncs)/float64(totalFuncs)*100)
	} else {
		check.Score = 100
	}
	if dupGroups > 0 {
		check.Details = fmt.Sprintf("%d duplicate groups (%d funcs / %d total) in Rust codebase", dupGroups, dupFuncs, totalFuncs)
	}
	return check
}

// =============================================================================
// Helpers
// =============================================================================

func shCap(score float64) float64 {
	if score < 0 {
		return 0
	}
	if score > 100 {
		return 100
	}
	return math.Round(score*10) / 10
}

// shExtractGoFuncHashes extracts function name + normalized body hash from Go source.
func shExtractGoFuncHashes(relPath string, src []byte) []shFuncSig {
	fset := token.NewFileSet()
	f, err := parser.ParseFile(fset, relPath, src, 0)
	if err != nil {
		return nil
	}

	var results []shFuncSig
	for _, decl := range f.Decls {
		fn, ok := decl.(*ast.FuncDecl)
		if !ok || fn.Body == nil {
			continue
		}

		start := fn.Body.Pos()
		end := fn.Body.End()
		if int(start) >= len(src) || int(end) > len(src) {
			continue
		}

		body := string(src[start-1 : end-1])
		norm := shNormFuncBody(body)
		lines := strings.Count(norm, "\n") + 1
		h := sha256.Sum256([]byte(norm))
		hash := hex.EncodeToString(h[:12])

		results = append(results, shFuncSig{
			path:    relPath,
			name:    fn.Name.Name,
			bodyLen: lines,
			hash:    hash,
		})
	}
	return results
}

// shNormFuncBody normalizes a function body for comparison.
func shNormFuncBody(body string) string {
	lines := strings.Split(body, "\n")
	var normalized []string
	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "//") {
			continue
		}
		// Collapse whitespace
		parts := strings.Fields(line)
		normalized = append(normalized, strings.Join(parts, " "))
	}
	return strings.Join(normalized, "\n")
}

// shExtractRustFuncHashes extracts function bodies from Rust via regex-based extraction.
func shExtractRustFuncHashes(relPath string, src []byte) []shFuncSig {
	s := string(src)
	fnStarts := shRustFnRe.FindAllStringIndex(s, -1)
	fnNames := shRustFnRe.FindAllStringSubmatch(s, -1)

	var results []shFuncSig
	for i, loc := range fnStarts {
		name := fnNames[i][1]
		braceIdx := strings.Index(s[loc[0]:], "{")
		if braceIdx < 0 {
			continue
		}
		bodyStart := loc[0] + braceIdx
		bodyEnd := shFindMatchingBrace(s, bodyStart)
		if bodyEnd < 0 {
			continue
		}

		body := s[bodyStart : bodyEnd+1]
		norm := shNormFuncBody(body)
		lines := strings.Count(norm, "\n") + 1
		h := sha256.Sum256([]byte(norm))
		hash := hex.EncodeToString(h[:12])

		results = append(results, shFuncSig{
			path:    relPath,
			name:    name,
			bodyLen: lines,
			hash:    hash,
		})
	}
	return results
}

// shExtractTSFuncHashes extracts function bodies from TypeScript source.
func shExtractTSFuncHashes(relPath string, src []byte) []shFuncSig {
	s := string(src)
	fnStarts := shTSFnRe.FindAllStringIndex(s, -1)
	fnNames := shTSFnRe.FindAllStringSubmatch(s, -1)

	var results []shFuncSig
	for i, loc := range fnStarts {
		name := fnNames[i][1]
		braceIdx := strings.Index(s[loc[0]:], "{")
		if braceIdx < 0 {
			continue
		}
		bodyStart := loc[0] + braceIdx
		bodyEnd := shFindMatchingBrace(s, bodyStart)
		if bodyEnd < 0 {
			continue
		}

		body := s[bodyStart : bodyEnd+1]
		norm := shNormFuncBody(body)
		lines := strings.Count(norm, "\n") + 1
		h := sha256.Sum256([]byte(norm))
		hash := hex.EncodeToString(h[:12])

		results = append(results, shFuncSig{
			path:    relPath,
			name:    name,
			bodyLen: lines,
			hash:    hash,
		})
	}
	return results
}

// shFindMatchingBrace finds the closing brace that matches the opening brace at pos.
func shFindMatchingBrace(s string, pos int) int {
	if pos >= len(s) || s[pos] != '{' {
		return -1
	}
	depth := 0
	inString := false
	escape := false
	for i := pos; i < len(s); i++ {
		ch := s[i]
		if escape {
			escape = false
			continue
		}
		if ch == '\\' {
			escape = true
			continue
		}
		if ch == '"' || ch == '\'' {
			inString = !inString
			continue
		}
		if inString {
			continue
		}
		if ch == '{' {
			depth++
		} else if ch == '}' {
			depth--
			if depth == 0 {
				return i
			}
		}
	}
	return -1
}

// shStripJsoncComments strips // and /* */ comments from JSONC content.
func shStripJsoncComments(input []byte) []byte {
	var out bytes.Buffer
	inString := false
	escape := false
	i := 0
	for i < len(input) {
		ch := input[i]
		if escape {
			out.WriteByte(ch)
			escape = false
			i++
			continue
		}
		if inString {
			if ch == '\\' {
				escape = true
			} else if ch == '"' {
				inString = false
			}
			out.WriteByte(ch)
			i++
			continue
		}
		if ch == '"' {
			inString = true
			out.WriteByte(ch)
			i++
			continue
		}
		if ch == '/' && i+1 < len(input) {
			if input[i+1] == '/' {
				// Line comment
				for i < len(input) && input[i] != '\n' {
					i++
				}
				continue
			}
			if input[i+1] == '*' {
				// Block comment
				i += 2
				for i+1 < len(input) && !(input[i] == '*' && input[i+1] == '/') {
					i++
				}
				i += 2
				continue
			}
		}
		out.WriteByte(ch)
		i++
	}
	return out.Bytes()
}

// shStripCommentsGo strips // comments from Go source for dead-code analysis.
func shStripCommentsGo(s string) string {
	lines := strings.Split(s, "\n")
	var result []string
	for _, line := range lines {
		trimmed := strings.TrimSpace(line)
		if strings.HasPrefix(trimmed, "//") {
			continue
		}
		if idx := strings.Index(trimmed, "//"); idx > 0 {
			trimmed = trimmed[:idx]
		}
		result = append(result, trimmed)
	}
	return strings.Join(result, "\n")
}

// shDeduplicateItems removes duplicate items by path+kind+detail.
func shDeduplicateItems(items []shannonItem) []shannonItem {
	seen := make(map[string]bool)
	var result []shannonItem
	for _, item := range items {
		key := item.Path + "|" + item.Kind + "|" + item.Detail
		if seen[key] {
			continue
		}
		seen[key] = true
		result = append(result, item)
	}
	return result
}

// shIsDeployInjectedVar returns true for Worker vars that are deterministically
// injected by `gftd deploy` and should not count as config redundancy.
func shIsDeployInjectedVar(key string) bool {
	switch key {
	case "APP_TEMPLATE", "APP_SOURCE", "APP_VERSION",
		"APP_DEPLOY_SHA", "APP_DEPLOY_AT", "WASM_HASH":
		return true
	}
	return false
}

// --- stale_symbol_entropy check ---
// Detects stale WIT bindings (wasmimport referencing non-existent WIT interfaces),
// CLAUDE.md strikethrough (~~removed~~) remnants, and prohibited symbol usage in code.
// Score = 100 - (violations / totalChecked * 100), clamped to [0, 100].

func shCheckStaleSymbolEntropy(wsRoot string) shannonCheck {
	var items []shannonItem
	totalChecked := 0

	// --- Sub-check 1: (removed — Go guest wasmimport check, Path B eliminated) ---

	// --- Sub-check 2: CLAUDE.md strikethrough remnants ---
	strikethroughRe := regexp.MustCompile(`~~.+~~`)
	err := filepath.Walk(wsRoot, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return nil
		}
		if info.IsDir() {
			base := filepath.Base(path)
			if base == "node_modules" || base == ".git" || base == "build" || base == ".cargo-target" {
				return filepath.SkipDir
			}
			return nil
		}
		if filepath.Base(path) != "CLAUDE.md" {
			return nil
		}
		rel, _ := filepath.Rel(wsRoot, path)
		f, err := os.Open(path)
		if err != nil {
			return nil
		}
		defer f.Close()
		scanner := bufio.NewScanner(f)
		lineNum := 0
		for scanner.Scan() {
			lineNum++
			line := scanner.Text()
			totalChecked++
			if strikethroughRe.MatchString(line) {
				// Skip lines that are behavioral rules (contain "禁止" or "PROHIBITED")
				if strings.Contains(line, "禁止") || strings.Contains(line, "PROHIBITED") {
					continue
				}
				items = append(items, shannonItem{
					Path:       rel + ":" + fmt.Sprintf("%d", lineNum),
					Kind:       "claude-md-strikethrough",
					Redundancy: 0.8,
					Detail:     "strikethrough in CLAUDE.md — delete (git has history)",
				})
			}
		}
		return nil
	})
	if err != nil {
		// non-fatal
	}

	// --- Sub-check 3: Prohibited symbol usage in Go/TS source ---
	prohibitedPatterns := []struct {
		re   *regexp.Regexp
		kind string
		msg  string
	}{
		{regexp.MustCompile(`\bDOSqlExec\b`), "prohibited-api", "DOSqlExec — use G() or ComAtprotoRepoCreateRecord"},
		{regexp.MustCompile(`\bSqlExec\s*\(`), "prohibited-api", "SqlExec() — use G() builder"},
		{regexp.MustCompile(`\bSqlQueryMap\s*\(`), "prohibited-api", "SqlQueryMap() — use G() builder"},
		{regexp.MustCompile(`\bappId:\s*"pds"`), "prohibited-magic", `appId: "pds" — use repo-derived appId`},
	}
	err = filepath.Walk(wsRoot, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return nil
		}
		if info.IsDir() {
			base := filepath.Base(path)
			if base == "node_modules" || base == ".git" || base == "build" || base == ".cargo-target" || base == "_svelte" {
				return filepath.SkipDir
			}
			return nil
		}
		ext := filepath.Ext(path)
		if ext != ".go" && ext != ".ts" {
			return nil
		}
		// Skip generated code, test files, and the linter itself
		if shIsGenerated(path) {
			return nil
		}
		if strings.Contains(path, "code_quality.go") || strings.Contains(path, "shannon.go") {
			return nil
		}
		if strings.HasSuffix(path, "_test.go") || strings.HasSuffix(path, ".test.ts") || strings.HasSuffix(path, ".spec.ts") {
			return nil
		}
		data, err := os.ReadFile(path)
		if err != nil {
			return nil
		}
		rel, _ := filepath.Rel(wsRoot, path)
		lines := bytes.Split(data, []byte("\n"))
		for lineIdx, line := range lines {
			for _, pp := range prohibitedPatterns {
				if pp.re.Match(line) {
					totalChecked++
					items = append(items, shannonItem{
						Path:       rel + ":" + fmt.Sprintf("%d", lineIdx+1),
						Kind:       pp.kind,
						Redundancy: 1.0,
						Detail:     pp.msg,
					})
				}
			}
		}
		return nil
	})
	if err != nil {
		// non-fatal
	}

	items = shDeduplicateItems(items)

	score := 100.0
	if totalChecked > 0 {
		score = 100.0 * (1.0 - float64(len(items))/float64(totalChecked))
	}

	return shannonCheck{
		Name:       "stale_symbol_entropy",
		Score:      shCap(score),
		Violations: len(items),
		Items:      items,
		Details:    fmt.Sprintf("checked %d symbols/lines, found %d stale/prohibited", totalChecked, len(items)),
	}
}

// shCollectWITInterfaces reads all package.wit files under packages/contract/wit/deps/
// and returns a set of "package:name/interface" keys.
func shCollectWITInterfaces(wsRoot string) map[string]bool {
	result := make(map[string]bool)
	witDepsDir := filepath.Join(wsRoot, "packages", "contract", "wit", "deps")

	packageRe := regexp.MustCompile(`^package\s+([\w:-]+)@`)
	interfaceRe := regexp.MustCompile(`^interface\s+([\w-]+)\s*\{`)

	filepath.Walk(witDepsDir, func(path string, info os.FileInfo, err error) error {
		if err != nil || info.IsDir() {
			return nil
		}
		if filepath.Base(path) != "package.wit" {
			return nil
		}
		data, err := os.ReadFile(path)
		if err != nil {
			return nil
		}
		var pkgName string
		for _, line := range strings.Split(string(data), "\n") {
			line = strings.TrimSpace(line)
			if m := packageRe.FindStringSubmatch(line); m != nil {
				pkgName = m[1]
			}
			if m := interfaceRe.FindStringSubmatch(line); m != nil && pkgName != "" {
				result[pkgName+"/"+m[1]] = true
			}
		}
		return nil
	})

	return result
}

// Ensure math import is used
var _ = math.Round
