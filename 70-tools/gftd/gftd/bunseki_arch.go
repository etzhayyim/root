package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"math"
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"strings"
	"time"
)

// ── gftd bunseki arch — Design Architecture Process Mining ──
//
// Treats the repo's design architecture as a process model:
//   - Inter-app data flow DFG (invoke/writes/reads/subscribe edges)
//   - Architecture variant analysis (performer types, integration patterns)
//   - Design conformance checking (Design E, WIT capability, naming)
//   - Build/deploy cycle performance (git commit → deploy latency)
//   - Architectural health score

// ── Data Model ──

// archDFGEdge represents a data flow transition between apps.
type archDFGEdge struct {
	From     string `json:"from"`
	To       string `json:"to"`
	EdgeType string `json:"edge_type"` // invoke, writes, reads, subscribe
	Count    int    `json:"count"`
	Label    string `json:"label,omitempty"`
}

// archVariant represents an app architecture pattern.
type archVariant struct {
	Pattern string   `json:"pattern"`
	Apps    []string `json:"apps"`
	Count   int      `json:"count"`
	Pct     float64  `json:"pct"`
}

// archConformance represents a design principle conformance check result.
type archConformance struct {
	Rule        string   `json:"rule"`
	Description string   `json:"description"`
	Total       int      `json:"total"`
	Conformant  int      `json:"conformant"`
	Rate        float64  `json:"rate"`
	Violations  []string `json:"violations,omitempty"`
}

// archCyclePerf represents build/deploy cycle performance for a project.
type archCyclePerf struct {
	Project      string  `json:"project"`
	CommitCount  int     `json:"commit_count"`
	DeployCount  int     `json:"deploy_count"`
	AvgCycleHrs  float64 `json:"avg_cycle_hrs,omitempty"`
	LastCommit   string  `json:"last_commit,omitempty"`
	LastDeploy   string  `json:"last_deploy,omitempty"`
	Drift        string  `json:"drift"` // "deployed", "pending", "no_deploy"
}

// archScore represents the architectural health score.
type archScore struct {
	DataFlowScore    float64 `json:"data_flow_score"`
	VariantScore     float64 `json:"variant_score"`
	ConformanceScore float64 `json:"conformance_score"`
	CycleScore       float64 `json:"cycle_score"`
	Overall          float64 `json:"overall"`
	Grade            string  `json:"grade"`
}

// archReport is the full architecture process mining output.
type archReport struct {
	GeneratedAt  string            `json:"generated_at"`
	TotalApps    int               `json:"total_apps"`
	TotalEdges   int               `json:"total_edges"`
	TotalProjects int              `json:"total_projects"`
	DFG          []archDFGEdge     `json:"dfg"`
	Variants     []archVariant     `json:"variants"`
	Conformance  []archConformance `json:"conformance"`
	CyclePerf    []archCyclePerf   `json:"cycle_perf"`
	Score        archScore         `json:"score"`
}

// ── Entry Points ──

// runBunsekiArch dispatches bunseki arch subcommands.
func runBunsekiArch(args []string) error {
	if len(args) > 0 {
		switch args[0] {
		case "scan":
			return runBunsekiArchScan(args[1:])
		case "dfg":
			return runBunsekiArchDFG(args[1:])
		case "variants":
			return runBunsekiArchVariants(args[1:])
		case "conformance":
			return runBunsekiArchConformance(args[1:])
		case "cycles":
			return runBunsekiArchCycles(args[1:])
		case "help", "--help", "-h":
			printBunsekiArchUsage()
			return nil
		default:
			return runBunsekiArchScan(args)
		}
	}
	return runBunsekiArchScan(args)
}

func printBunsekiArchUsage() {
	fmt.Print(`gftd bunseki arch — Design Architecture Process Mining

USAGE:
  gftd bunseki arch <command> [flags]

COMMANDS:
  scan          Full architecture analysis: DFG + Variants + Conformance + Cycles → unified report (default)
  dfg           Inter-app data flow graph (invoke/writes/reads/subscribe edges)
  variants      Architecture pattern analysis (performer types, integration patterns)
  conformance   Design principle compliance (Design E, WIT capability, naming)
  cycles        Build/deploy cycle performance per project

FLAGS:
  --json            Output as JSON
  --top             Top N results (default: 30)
  --workspace-dir   Workspace root (default: git root)
  --project         Filter by project name

DATA SOURCE:
  magatama.jsonld + source-graph AST + haisen edges + git log + .deploy-state.json

ALGORITHMS:
  DFG               Inter-app data flow transitions (reuses haisen scan)
  Variant Analysis   Group apps by architecture pattern (performer × runtime × integration)
  Conformance        Check against Design E, WIT capability export, NSID naming, etc.
  Cycle Perf         Git commit → deploy latency per project
  Score              25% data_flow + 25% variant + 25% conformance + 25% cycle
`)
}

// ── Flag Parsing ──

type bunsekiArchFlags struct {
	jsonOut      bool
	top          int
	workspaceDir string
	project      string
}

func parseBunsekiArchFlags(name string, args []string) (bunsekiArchFlags, error) {
	fs := flag.NewFlagSet("bunseki arch "+name, flag.ContinueOnError)
	var f bunsekiArchFlags
	fs.BoolVar(&f.jsonOut, "json", false, "output as JSON")
	fs.IntVar(&f.top, "top", 30, "top N results")
	fs.StringVar(&f.workspaceDir, "workspace-dir", "", "workspace root")
	fs.StringVar(&f.project, "project", "", "filter by project name")
	if err := fs.Parse(args); err != nil {
		return f, err
	}
	if f.workspaceDir == "" {
		cwd, _ := os.Getwd()
		f.workspaceDir, _ = findGitRoot(cwd)
	}
	return f, nil
}

// ── Data Extraction ──

// buildArchDFG extracts inter-app data flow edges from haisen scan.
func buildArchDFG(wsRoot string) ([]archDFGEdge, []haisenApp) {
	graph := haisenScanWorkspace(wsRoot, false)

	// Aggregate edges by (from_project, to_target, type)
	type edgeKey struct{ from, to, edgeType string }
	agg := map[edgeKey]int{}
	labels := map[edgeKey]string{}

	projectOf := map[string]string{}
	for _, app := range graph.Apps {
		projectOf[app.Nanoid] = app.Project
		if projectOf[app.Nanoid] == "" {
			projectOf[app.Nanoid] = app.Name
		}
	}

	for _, e := range graph.Edges {
		fromProj := projectOf[e.From]
		if fromProj == "" {
			fromProj = e.From
		}
		key := edgeKey{fromProj, e.To, e.EdgeType}
		agg[key]++
		if labels[key] == "" {
			labels[key] = e.Label
		}
	}

	var edges []archDFGEdge
	for key, count := range agg {
		edges = append(edges, archDFGEdge{
			From:     key.from,
			To:       key.to,
			EdgeType: key.edgeType,
			Count:    count,
			Label:    labels[edgeKey{key.from, key.to, key.edgeType}],
		})
	}

	sort.Slice(edges, func(i, j int) bool {
		return edges[i].Count > edges[j].Count
	})
	return edges, graph.Apps
}

// analyzeArchVariants groups apps by architecture pattern.
func analyzeArchVariants(apps []haisenApp) []archVariant {
	patternApps := map[string][]string{}

	for _, app := range apps {
		rt := app.RuntimeType
		if rt == "" {
			rt = "ts-native"
		}
		pt := app.PerformerType
		if pt == "" {
			pt = "unknown"
		}
		ui := app.UIType
		if ui == "" {
			ui = "appview"
		}

		// Integration pattern
		integration := "standalone"
		if len(app.Collections) > 0 {
			integration = "subscribed"
		}

		pattern := fmt.Sprintf("%s × %s × %s × %s", rt, pt, ui, integration)
		name := app.Name
		if name == "" {
			name = app.Nanoid
		}
		patternApps[pattern] = append(patternApps[pattern], name)
	}

	total := len(apps)
	var variants []archVariant
	for pattern, appNames := range patternApps {
		pct := 0.0
		if total > 0 {
			pct = float64(len(appNames)) / float64(total) * 100
		}
		sort.Strings(appNames)
		variants = append(variants, archVariant{
			Pattern: pattern,
			Apps:    appNames,
			Count:   len(appNames),
			Pct:     pct,
		})
	}

	sort.Slice(variants, func(i, j int) bool {
		return variants[i].Count > variants[j].Count
	})
	return variants
}

// checkArchConformance checks design principle compliance across all apps.
func checkArchConformance(wsRoot string, apps []haisenApp) []archConformance {
	appMeta := sgScanAppMeta(wsRoot)
	var results []archConformance

	// Rule 1: WIT capability export — world.wit must have capability export
	{
		total := 0
		conformant := 0
		var violations []string
		for relPath, meta := range appMeta {
			if meta.NanoID == "" {
				continue
			}
			total++
			if len(meta.WITExports) > 0 {
				conformant++
			} else {
				violations = append(violations, fmt.Sprintf("%s (%s): no WIT capability export", meta.Name, relPath))
			}
		}
		rate := 0.0
		if total > 0 {
			rate = float64(conformant) / float64(total) * 100
		}
		sort.Strings(violations)
		if len(violations) > 10 {
			violations = violations[:10]
		}
		results = append(results, archConformance{
			Rule:        "wit_capability_export",
			Description: "world.wit must have contract import + capability export",
			Total:       total,
			Conformant:  conformant,
			Rate:        rate,
			Violations:  violations,
		})
	}

	// Rule 2: magatama.jsonld governance — must have governance block
	{
		total := 0
		conformant := 0
		var violations []string
		for relPath, meta := range appMeta {
			if meta.NanoID == "" {
				continue
			}
			total++
			jPath := filepath.Join(wsRoot, relPath, "magatama.jsonld")
			data, err := os.ReadFile(jPath)
			if err != nil {
				violations = append(violations, fmt.Sprintf("%s: magatama.jsonld missing", meta.Name))
				continue
			}
			if strings.Contains(string(data), "\"governance\"") {
				conformant++
			} else {
				violations = append(violations, fmt.Sprintf("%s: missing governance block", meta.Name))
			}
		}
		rate := 0.0
		if total > 0 {
			rate = float64(conformant) / float64(total) * 100
		}
		sort.Strings(violations)
		if len(violations) > 10 {
			violations = violations[:10]
		}
		results = append(results, archConformance{
			Rule:        "governance_block",
			Description: "magatama.jsonld must have governance block for yoro profile display",
			Total:       total,
			Conformant:  conformant,
			Rate:        rate,
			Violations:  violations,
		})
	}

	// Rule 3: convoSystemPrompt — must have DM agent system prompt
	{
		total := 0
		conformant := 0
		var violations []string
		for relPath, meta := range appMeta {
			if meta.NanoID == "" {
				continue
			}
			total++
			jPath := filepath.Join(wsRoot, relPath, "magatama.jsonld")
			data, err := os.ReadFile(jPath)
			if err != nil {
				continue
			}
			if strings.Contains(string(data), "\"convoSystemPrompt\"") {
				conformant++
			} else {
				violations = append(violations, fmt.Sprintf("%s: missing convoSystemPrompt", meta.Name))
			}
		}
		rate := 0.0
		if total > 0 {
			rate = float64(conformant) / float64(total) * 100
		}
		sort.Strings(violations)
		if len(violations) > 10 {
			violations = violations[:10]
		}
		results = append(results, archConformance{
			Rule:        "convo_system_prompt",
			Description: "magatama.jsonld must have convoSystemPrompt for DM agent",
			Total:       total,
			Conformant:  conformant,
			Rate:        rate,
			Violations:  violations,
		})
	}

	// Rule 4: TS Native entry — app.ts must export default createWorkerExport()
	{
		total := 0
		conformant := 0
		var violations []string
		for relPath, meta := range appMeta {
			if meta.NanoID == "" {
				continue
			}
			appTS := filepath.Join(wsRoot, relPath, "src", "app.ts")
			data, err := os.ReadFile(appTS)
			if err != nil {
				continue
			}
			total++
			content := string(data)
			if strings.Contains(content, "createWorkerExport") && strings.Contains(content, "export default") {
				conformant++
			} else {
				violations = append(violations, fmt.Sprintf("%s: missing export default createWorkerExport()", meta.Name))
			}
		}
		rate := 0.0
		if total > 0 {
			rate = float64(conformant) / float64(total) * 100
		}
		sort.Strings(violations)
		if len(violations) > 10 {
			violations = violations[:10]
		}
		results = append(results, archConformance{
			Rule:        "ts_native_entry",
			Description: "app.ts must export default createWorkerExport()",
			Total:       total,
			Conformant:  conformant,
			Rate:        rate,
			Violations:  violations,
		})
	}

	// Rule 5: Alpha-start naming — DID paths must start with alpha character
	{
		total := 0
		conformant := 0
		var violations []string
		for _, app := range apps {
			if app.DID == "" {
				continue
			}
			total++
			// Check DID path segment (after did:web:)
			didParts := strings.Split(app.DID, ":")
			if len(didParts) >= 3 {
				host := didParts[2]
				namePart := strings.Split(host, ".")[0]
				if len(namePart) > 0 && namePart[0] >= 'a' && namePart[0] <= 'z' {
					conformant++
				} else {
					violations = append(violations, fmt.Sprintf("%s: DID path '%s' does not start with alpha", app.Name, namePart))
				}
			}
		}
		rate := 0.0
		if total > 0 {
			rate = float64(conformant) / float64(total) * 100
		}
		results = append(results, archConformance{
			Rule:        "alpha_start_naming",
			Description: "DID path must start with alpha character",
			Total:       total,
			Conformant:  conformant,
			Rate:        rate,
			Violations:  violations,
		})
	}

	// Rule 6: Design E — no domain data in AppBskyFeedPost (domain → ComAtprotoRepoCreateRecord)
	{
		total := 0
		conformant := 0
		var violations []string
		for relPath, meta := range appMeta {
			if meta.NanoID == "" {
				continue
			}
			appTS := filepath.Join(wsRoot, relPath, "src", "app.ts")
			data, err := os.ReadFile(appTS)
			if err != nil {
				continue
			}
			total++
			content := string(data)
			// Check if domain data is written via social post
			hasFeedPost := strings.Contains(content, "AppBskyFeedPost") || strings.Contains(content, "feedPost")
			hasDomainWrite := strings.Contains(content, "ComAtprotoRepoCreateRecord") || strings.Contains(content, "createRecord")
			if hasFeedPost && !hasDomainWrite {
				violations = append(violations, fmt.Sprintf("%s: uses AppBskyFeedPost without ComAtprotoRepoCreateRecord (Design E violation)", meta.Name))
			} else {
				conformant++
			}
		}
		rate := 0.0
		if total > 0 {
			rate = float64(conformant) / float64(total) * 100
		}
		sort.Strings(violations)
		if len(violations) > 10 {
			violations = violations[:10]
		}
		results = append(results, archConformance{
			Rule:        "design_e_write_separation",
			Description: "Domain data via ComAtprotoRepoCreateRecord, social via AppBskyFeedPost",
			Total:       total,
			Conformant:  conformant,
			Rate:        rate,
			Violations:  violations,
		})
	}

	sort.Slice(results, func(i, j int) bool {
		return results[i].Rate < results[j].Rate // worst first
	})
	return results
}

// analyzeArchCycles measures build/deploy cycle times per project.
func analyzeArchCycles(wsRoot string) []archCyclePerf {
	// Get recent commits per project
	projectCommits := map[string][]string{}
	cmd := exec.Command("git", "log", "--since=7 days ago", "-n500", "--pretty=format:%aI|%s", "--name-only")
	cmd.Dir = wsRoot
	out, _ := cmd.Output()

	var currentTS, currentMsg string
	for _, line := range strings.Split(string(out), "\n") {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}
		parts := strings.SplitN(line, "|", 2)
		if len(parts) == 2 && len(parts[0]) > 10 && (parts[0][4] == '-') {
			currentTS = parts[0]
			currentMsg = parts[1]
			_ = currentMsg
			continue
		}
		// File path
		if strings.HasPrefix(line, "projects/ai-gftd-project-") {
			pathParts := strings.Split(line, "/")
			if len(pathParts) >= 2 {
				for _, p := range pathParts {
					if strings.HasPrefix(p, "ai-gftd-project-") {
						proj := strings.TrimPrefix(p, "ai-gftd-project-")
						projectCommits[proj] = append(projectCommits[proj], currentTS)
						break
					}
				}
			}
		}
	}

	// Get deploy state
	deploys := scanDeployState(wsRoot)
	deployByProject := map[string]archDeployEntry{}
	deployCounts := map[string]int{}
	for _, d := range deploys {
		deployCounts[d.Project]++
		if _, ok := deployByProject[d.Project]; !ok {
			deployByProject[d.Project] = d // most recent
		}
	}

	// Build results
	allProjects := map[string]bool{}
	for p := range projectCommits {
		allProjects[p] = true
	}
	for p := range deployByProject {
		allProjects[p] = true
	}

	var results []archCyclePerf
	for proj := range allProjects {
		commits := projectCommits[proj]
		deploy, hasD := deployByProject[proj]

		cp := archCyclePerf{
			Project:     proj,
			CommitCount: len(commits),
			DeployCount: deployCounts[proj],
		}

		if len(commits) > 0 {
			cp.LastCommit = commits[0]
		}
		if hasD {
			cp.LastDeploy = deploy.DeployAt
		}

		// Drift detection
		if !hasD {
			cp.Drift = "no_deploy"
		} else if len(commits) > 0 {
			commitTime, err1 := time.Parse(time.RFC3339, commits[0])
			deployTime, err2 := time.Parse(time.RFC3339, deploy.DeployAt)
			if err1 == nil && err2 == nil {
				if commitTime.After(deployTime) {
					cp.Drift = "pending"
					cp.AvgCycleHrs = time.Since(commitTime).Hours()
				} else {
					cp.Drift = "deployed"
					cp.AvgCycleHrs = deployTime.Sub(commitTime).Hours()
				}
			} else {
				cp.Drift = "deployed"
			}
		} else {
			cp.Drift = "deployed"
		}

		results = append(results, cp)
	}

	sort.Slice(results, func(i, j int) bool {
		driftOrder := map[string]int{"pending": 0, "no_deploy": 1, "deployed": 2}
		di, dj := driftOrder[results[i].Drift], driftOrder[results[j].Drift]
		if di != dj {
			return di < dj
		}
		return results[i].CommitCount > results[j].CommitCount
	})
	return results
}

// ── Scoring ──

// computeArchScore calculates the overall architecture health score.
func computeArchScore(
	dfg []archDFGEdge,
	variants []archVariant,
	conformance []archConformance,
	cycles []archCyclePerf,
	totalApps int,
) archScore {
	// Data flow: connected apps / total = better (penalize orphans)
	dfgScore := 100.0
	if totalApps > 0 {
		connected := map[string]bool{}
		for _, e := range dfg {
			connected[e.From] = true
		}
		ratio := float64(len(connected)) / float64(totalApps)
		dfgScore = math.Min(100, ratio*100)
	}

	// Variant concentration: top-3 patterns covering majority = simpler architecture
	variantScore := 0.0
	if len(variants) > 0 {
		top3Pct := 0.0
		for i := 0; i < len(variants) && i < 3; i++ {
			top3Pct += variants[i].Pct
		}
		variantScore = math.Min(100, top3Pct)
	}

	// Conformance: average across all rules
	conformScore := 100.0
	if len(conformance) > 0 {
		sum := 0.0
		for _, c := range conformance {
			sum += c.Rate
		}
		conformScore = sum / float64(len(conformance))
	}

	// Cycle: percentage of projects that are "deployed" (not drifting)
	cycleScore := 100.0
	if len(cycles) > 0 {
		deployed := 0
		for _, c := range cycles {
			if c.Drift == "deployed" {
				deployed++
			}
		}
		cycleScore = float64(deployed) / float64(len(cycles)) * 100
	}

	overall := dfgScore*0.25 + variantScore*0.25 + conformScore*0.25 + cycleScore*0.25
	return archScore{
		DataFlowScore:    dfgScore,
		VariantScore:     variantScore,
		ConformanceScore: conformScore,
		CycleScore:       cycleScore,
		Overall:          overall,
		Grade:            bunsekiGrade(overall),
	}
}

// ── Subcommand Implementations ──

func runBunsekiArchScan(args []string) error {
	f, err := parseBunsekiArchFlags("scan", args)
	if err != nil {
		return nil
	}

	dfg, apps := buildArchDFG(f.workspaceDir)
	variants := analyzeArchVariants(apps)
	conformance := checkArchConformance(f.workspaceDir, apps)
	cycles := analyzeArchCycles(f.workspaceDir)

	// Filter by project
	if f.project != "" {
		var filteredApps []haisenApp
		for _, a := range apps {
			if strings.Contains(strings.ToLower(a.Project), strings.ToLower(f.project)) {
				filteredApps = append(filteredApps, a)
			}
		}
		var filteredCycles []archCyclePerf
		for _, c := range cycles {
			if strings.Contains(strings.ToLower(c.Project), strings.ToLower(f.project)) {
				filteredCycles = append(filteredCycles, c)
			}
		}
		cycles = filteredCycles
	}

	// Collect unique projects
	projects := map[string]bool{}
	for _, a := range apps {
		if a.Project != "" {
			projects[a.Project] = true
		}
	}

	score := computeArchScore(dfg, variants, conformance, cycles, len(apps))

	if len(dfg) > f.top {
		dfg = dfg[:f.top]
	}
	if len(variants) > f.top {
		variants = variants[:f.top]
	}
	if len(cycles) > f.top {
		cycles = cycles[:f.top]
	}

	report := archReport{
		GeneratedAt:   time.Now().UTC().Format(time.RFC3339),
		TotalApps:     len(apps),
		TotalEdges:    len(dfg),
		TotalProjects: len(projects),
		DFG:           dfg,
		Variants:      variants,
		Conformance:   conformance,
		CyclePerf:     cycles,
		Score:         score,
	}

	if f.jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(report)
	}

	printArchReport(&report)
	return nil
}

func runBunsekiArchDFG(args []string) error {
	f, err := parseBunsekiArchFlags("dfg", args)
	if err != nil {
		return nil
	}

	dfg, _ := buildArchDFG(f.workspaceDir)
	if len(dfg) > f.top {
		dfg = dfg[:f.top]
	}

	if f.jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(dfg)
	}

	printArchDFGTable(dfg)
	return nil
}

func runBunsekiArchVariants(args []string) error {
	f, err := parseBunsekiArchFlags("variants", args)
	if err != nil {
		return nil
	}

	_, apps := buildArchDFG(f.workspaceDir)
	variants := analyzeArchVariants(apps)
	if len(variants) > f.top {
		variants = variants[:f.top]
	}

	if f.jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(variants)
	}

	printArchVariantsTable(variants)
	return nil
}

func runBunsekiArchConformance(args []string) error {
	f, err := parseBunsekiArchFlags("conformance", args)
	if err != nil {
		return nil
	}

	_, apps := buildArchDFG(f.workspaceDir)
	conformance := checkArchConformance(f.workspaceDir, apps)

	if f.jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(conformance)
	}

	printArchConformanceTable(conformance)
	return nil
}

func runBunsekiArchCycles(args []string) error {
	f, err := parseBunsekiArchFlags("cycles", args)
	if err != nil {
		return nil
	}

	cycles := analyzeArchCycles(f.workspaceDir)

	if f.project != "" {
		var filtered []archCyclePerf
		for _, c := range cycles {
			if strings.Contains(strings.ToLower(c.Project), strings.ToLower(f.project)) {
				filtered = append(filtered, c)
			}
		}
		cycles = filtered
	}

	if len(cycles) > f.top {
		cycles = cycles[:f.top]
	}

	if f.jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(cycles)
	}

	printArchCyclesTable(cycles)
	return nil
}

// ── Output Formatting ──

func printArchReport(r *archReport) {
	fmt.Println()
	fmt.Println("╔══════════════════════════════════════════════════════════════════════════════════╗")
	fmt.Println("║              GFTD Bunseki Arch — Design Architecture Process Mining             ║")
	fmt.Printf("║              %s                                              ║\n", time.Now().Format("2006-01-02 15:04:05"))
	fmt.Println("╠══════════════════════════════════════════════════════════════════════════════════╣")
	fmt.Printf("  Apps: %d | Edges: %d | Projects: %d\n\n", r.TotalApps, r.TotalEdges, r.TotalProjects)

	// DFG
	if len(r.DFG) > 0 {
		printArchDFGTable(r.DFG)
		fmt.Println()
	}

	// Variants
	if len(r.Variants) > 0 {
		printArchVariantsTable(r.Variants)
		fmt.Println()
	}

	// Conformance
	if len(r.Conformance) > 0 {
		printArchConformanceTable(r.Conformance)
		fmt.Println()
	}

	// Cycles (show only drifting)
	pendingCount := 0
	for _, c := range r.CyclePerf {
		if c.Drift == "pending" {
			pendingCount++
		}
	}
	if pendingCount > 0 {
		fmt.Printf("  Deploy Drift (%d projects pending):\n", pendingCount)
		for _, c := range r.CyclePerf {
			if c.Drift != "pending" {
				continue
			}
			fmt.Printf("    [PENDING] %-20s %d commits since last deploy (%.1fh ago)\n",
				c.Project, c.CommitCount, c.AvgCycleHrs)
		}
		fmt.Println()
	}

	// Score
	fmt.Printf("  Score: %.0f (%s)\n", r.Score.Overall, r.Score.Grade)
	fmt.Printf("    Data Flow:    %.0f  (connected apps / total)\n", r.Score.DataFlowScore)
	fmt.Printf("    Variant:      %.0f  (top-3 pattern concentration)\n", r.Score.VariantScore)
	fmt.Printf("    Conformance:  %.0f  (avg design rule compliance)\n", r.Score.ConformanceScore)
	fmt.Printf("    Cycle:        %.0f  (deployed / total projects)\n", r.Score.CycleScore)
	fmt.Println()
	fmt.Println("╚══════════════════════════════════════════════════════════════════════════════════╝")
}

func printArchDFGTable(dfg []archDFGEdge) {
	fmt.Println("  Inter-App Data Flow (DFG):")
	fmt.Println("  ┌────────────────────────┬────────────────────────────────┬───────────┬───────┐")
	fmt.Println("  │ From (project)         │ To (target)                    │ Type      │ Count │")
	fmt.Println("  ├────────────────────────┼────────────────────────────────┼───────────┼───────┤")
	for _, e := range dfg {
		from := e.From
		if len(from) > 22 {
			from = from[:22]
		}
		to := e.To
		if len(to) > 30 {
			to = to[:30]
		}
		fmt.Printf("  │ %-22s │ %-30s │ %-9s │ %5d │\n",
			from, to, e.EdgeType, e.Count)
	}
	fmt.Println("  └────────────────────────┴────────────────────────────────┴───────────┴───────┘")
}

func printArchVariantsTable(variants []archVariant) {
	fmt.Println("  Architecture Variants:")
	fmt.Println("  ┌───┬──────────────────────────────────────────────────────────┬───────┬───────┐")
	fmt.Println("  │ # │ Pattern (runtime × performer × UI × integration)        │ Count │    %  │")
	fmt.Println("  ├───┼──────────────────────────────────────────────────────────┼───────┼───────┤")
	for i, v := range variants {
		pattern := v.Pattern
		if len(pattern) > 56 {
			pattern = pattern[:53] + "..."
		}
		fmt.Printf("  │%2d │ %-56s │ %5d │ %4.1f%% │\n",
			i+1, pattern, v.Count, v.Pct)
	}
	fmt.Println("  └───┴──────────────────────────────────────────────────────────┴───────┴───────┘")
}

func printArchConformanceTable(conformance []archConformance) {
	fmt.Println("  Design Conformance:")
	for _, c := range conformance {
		status := "OK"
		if c.Rate < 90 {
			status = "GAP"
		}
		if c.Rate < 50 {
			status = "CRIT"
		}
		fmt.Printf("    [%4s] %-30s %.1f%% (%d/%d)\n",
			status, c.Rule, c.Rate, c.Conformant, c.Total)
		for _, v := range c.Violations {
			fmt.Printf("           %s\n", v)
		}
	}
}

func printArchCyclesTable(cycles []archCyclePerf) {
	fmt.Println("  Build/Deploy Cycles:")
	fmt.Println("  ┌─────────────────────────┬─────────┬─────────┬──────────┬──────────┐")
	fmt.Println("  │ Project                 │ Commits │ Deploys │ Cycle hr │ Drift    │")
	fmt.Println("  ├─────────────────────────┼─────────┼─────────┼──────────┼──────────┤")
	for _, c := range cycles {
		proj := c.Project
		if len(proj) > 23 {
			proj = proj[:23]
		}
		cycleStr := "-"
		if c.AvgCycleHrs > 0 {
			cycleStr = fmt.Sprintf("%.1f", c.AvgCycleHrs)
		}
		fmt.Printf("  │ %-23s │ %7d │ %7d │ %8s │ %-8s │\n",
			proj, c.CommitCount, c.DeployCount, cycleStr, c.Drift)
	}
	fmt.Println("  └─────────────────────────┴─────────┴─────────┴──────────┴──────────┘")
}
