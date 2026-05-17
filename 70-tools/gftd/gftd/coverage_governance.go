package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"
)

type coverageGovernanceSummary struct {
	EvaluatedAt     string                      `json:"evaluatedAt"`
	WorkspaceRoot   string                      `json:"workspaceRoot"`
	TotalComponents int                         `json:"totalComponents"`
	AverageScore    float64                     `json:"averageScore"`
	MedianScore     float64                     `json:"medianScore"`
	MinScore        float64                     `json:"minScore"`
	MaxScore        float64                     `json:"maxScore"`
	Verdicts        map[string]int              `json:"verdicts"`
	TopFindings     []coverageGovernanceFinding `json:"topFindings,omitempty"`
	Components      []coverageGovernanceEntry   `json:"components,omitempty"`
}

type coverageGovernanceFinding struct {
	Code    string `json:"code"`
	Count   int    `json:"count"`
	Example string `json:"example,omitempty"`
}

type coverageGovernanceEntry struct {
	Component string  `json:"component"`
	Score     float64 `json:"score"`
	Verdict   string  `json:"verdict"`
	Runtime   string  `json:"runtime"`
}

func runCoverageGovernance(args []string) error {
	fs := flag.NewFlagSet("coverage governance", flag.ContinueOnError)
	rootDir := fs.String("root", "", "repo root (default: git root)")
	jsonOut := fs.Bool("json", false, "output as JSON")
	showComponents := fs.Bool("components", false, "include per-component entries")
	limit := fs.Int("limit", 20, "show top N weakest components in text output")
	kaizen := fs.Bool("kaizen", false, "launch codex to improve weakest governance WIT components")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	root := *rootDir
	if root == "" {
		cwd, _ := os.Getwd()
		var err error
		root, err = findGitRoot(cwd)
		if err != nil {
			root = cwd
		}
	}
	root, _ = filepath.Abs(root)

	report, detailed, err := buildCoverageGovernanceSummary(root, *showComponents || *kaizen || !*jsonOut)
	if err != nil {
		return err
	}

	if *jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(report)
	}

	printCoverageGovernanceText(report, *limit)
	if *kaizen {
		return runCoverageGovernanceKaizen(root, detailed)
	}
	return nil
}

func buildCoverageGovernanceSummary(root string, includeDetailed bool) (*coverageGovernanceSummary, []*depsGovernanceWITReport, error) {
	componentDirs, err := findGovernanceCoverageComponents(root)
	if err != nil {
		return nil, nil, err
	}
	reports := make([]*depsGovernanceWITReport, 0, len(componentDirs))
	scores := make([]float64, 0, len(componentDirs))
	verdicts := map[string]int{}
	findingCounts := map[string]int{}
	findingExamples := map[string]string{}
	entries := make([]coverageGovernanceEntry, 0, len(componentDirs))

	for _, dir := range componentDirs {
		r, err := evaluateGovernanceWIT(dir)
		if err != nil {
			return nil, nil, err
		}
		reports = append(reports, r)
		scores = append(scores, r.Score)
		verdicts[r.Verdict]++
		for _, f := range r.Findings {
			findingCounts[f.Code]++
			if findingExamples[f.Code] == "" {
				findingExamples[f.Code] = relComponentPath(root, dir)
			}
		}
		if includeDetailed {
			entries = append(entries, coverageGovernanceEntry{
				Component: relComponentPath(root, dir),
				Score:     r.Score,
				Verdict:   r.Verdict,
				Runtime:   r.Implementation.Runtime,
			})
		}
	}

	sort.Float64s(scores)
	var avg, median, minScore, maxScore float64
	if len(scores) > 0 {
		for _, s := range scores {
			avg += s
		}
		avg /= float64(len(scores))
		minScore = scores[0]
		maxScore = scores[len(scores)-1]
		median = scores[len(scores)/2]
		if len(scores)%2 == 0 {
			median = (scores[len(scores)/2-1] + scores[len(scores)/2]) / 2
		}
	}

	var topFindings []coverageGovernanceFinding
	for code, count := range findingCounts {
		topFindings = append(topFindings, coverageGovernanceFinding{
			Code:    code,
			Count:   count,
			Example: findingExamples[code],
		})
	}
	sort.Slice(topFindings, func(i, j int) bool {
		if topFindings[i].Count == topFindings[j].Count {
			return topFindings[i].Code < topFindings[j].Code
		}
		return topFindings[i].Count > topFindings[j].Count
	})
	if len(topFindings) > 10 {
		topFindings = topFindings[:10]
	}

	if includeDetailed {
		sort.Slice(entries, func(i, j int) bool {
			if entries[i].Score == entries[j].Score {
				return entries[i].Component < entries[j].Component
			}
			return entries[i].Score < entries[j].Score
		})
	}

	summary := &coverageGovernanceSummary{
		EvaluatedAt:     time.Now().UTC().Format(time.RFC3339),
		WorkspaceRoot:   root,
		TotalComponents: len(componentDirs),
		AverageScore:    round1(avg),
		MedianScore:     round1(median),
		MinScore:        round1(minScore),
		MaxScore:        round1(maxScore),
		Verdicts:        verdicts,
		TopFindings:     topFindings,
	}
	if includeDetailed {
		summary.Components = entries
	}
	return summary, reports, nil
}

func findGovernanceCoverageComponents(root string) ([]string, error) {
	var dirs []string
	err := filepath.WalkDir(filepath.Join(root, "projects"), func(path string, d os.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if d.IsDir() {
			return nil
		}
		if d.Name() != "world.wit" || filepath.Base(filepath.Dir(path)) != "wit" {
			return nil
		}
		componentDir := filepath.Dir(filepath.Dir(path))
		if isGovernanceCoverageTarget(componentDir) {
			dirs = append(dirs, componentDir)
		}
		return nil
	})
	sort.Strings(dirs)
	return dirs, err
}

func isGovernanceCoverageTarget(componentDir string) bool {
	if _, err := os.Stat(filepath.Join(componentDir, "magatama.jsonld")); err == nil {
		return true
	}
	if _, err := os.Stat(filepath.Join(componentDir, "src", "app.ts")); err == nil {
		return true
	}
	if _, err := os.Stat(filepath.Join(componentDir, "main.go")); err == nil {
		return true
	}
	return false
}

func relComponentPath(root, dir string) string {
	if rel, err := filepath.Rel(root, dir); err == nil {
		return rel
	}
	return dir
}

func printCoverageGovernanceText(report *coverageGovernanceSummary, limit int) {
	fmt.Printf("coverage_governance:\n")
	fmt.Printf("  workspace_root: %s\n", report.WorkspaceRoot)
	fmt.Printf("  evaluated_at: %s\n", report.EvaluatedAt)
	fmt.Printf("  total_components: %d\n", report.TotalComponents)
	fmt.Printf("  average_score: %.1f\n", report.AverageScore)
	fmt.Printf("  median_score: %.1f\n", report.MedianScore)
	fmt.Printf("  min_score: %.1f\n", report.MinScore)
	fmt.Printf("  max_score: %.1f\n", report.MaxScore)
	fmt.Printf("  verdicts:\n")
	for _, key := range sortedMapKeys(report.Verdicts) {
		fmt.Printf("    %s: %d\n", key, report.Verdicts[key])
	}
	if len(report.TopFindings) > 0 {
		fmt.Printf("  top_findings:\n")
		for _, f := range report.TopFindings {
			fmt.Printf("    - %s: %d", f.Code, f.Count)
			if f.Example != "" {
				fmt.Printf(" (example: %s)", f.Example)
			}
			fmt.Printf("\n")
		}
	}
	if len(report.Components) > 0 {
		fmt.Printf("  weakest_components:\n")
		maxN := limit
		if maxN <= 0 || maxN > len(report.Components) {
			maxN = len(report.Components)
		}
		for i := 0; i < maxN; i++ {
			c := report.Components[i]
			fmt.Printf("    - score=%.1f verdict=%s runtime=%s component=%s\n", c.Score, c.Verdict, c.Runtime, c.Component)
		}
	}
}

func runCoverageGovernanceKaizen(root string, reports []*depsGovernanceWITReport) error {
	sort.Slice(reports, func(i, j int) bool {
		if reports[i].Score == reports[j].Score {
			return reports[i].ComponentDir < reports[j].ComponentDir
		}
		return reports[i].Score < reports[j].Score
	})

	var sb strings.Builder
	sb.WriteString("You are a kaizen agent improving governance WIT coverage for App components.\n\n")
	sb.WriteString("CRITICAL RULES:\n")
	sb.WriteString("- Do NOT create git worktrees. Work directly in the current repository.\n")
	sb.WriteString("- Preserve each app's domain behavior; only improve governance/WIT alignment.\n")
	sb.WriteString("- Prefer explicit command-level governance instead of relying only on SDK defaults.\n")
	sb.WriteString("- Keep WIT imports aligned with the authoritative Magatama runtime governance surface.\n")
	sb.WriteString("- Update magatama.jsonld governance only with domain-specific roles/frameworks, not generic template copies.\n\n")
	sb.WriteString("TARGET COMMAND:\n")
	sb.WriteString("- Verify with `gftd coverage governance --limit 20`\n")
	sb.WriteString("- Per component verify with `gftd deps governance-wit --component-dir <component>`\n\n")

	sb.WriteString("WEAKEST COMPONENTS TO FIX FIRST:\n")
	limit := 20
	if len(reports) < limit {
		limit = len(reports)
	}
	for i := 0; i < limit; i++ {
		r := reports[i]
		sb.WriteString(fmt.Sprintf("- score=%.1f verdict=%s component=%s\n", r.Score, r.Verdict, relComponentPath(root, r.ComponentDir)))
		for _, f := range r.Findings {
			sb.WriteString(fmt.Sprintf("  finding[%s] %s: %s\n", f.Severity, f.Code, f.Message))
		}
	}

	sb.WriteString("\nFIX STRATEGY:\n")
	sb.WriteString("1. Read the component's wit/world.wit, src/app.ts or main.go, and magatama.jsonld.\n")
	sb.WriteString("2. Add missing governance-related WIT imports where appropriate.\n")
	sb.WriteString("3. Add explicit command-level RACI / approval / traceability metadata for high-value commands.\n")
	sb.WriteString("4. Replace default governance template blocks with domain-specific governance.\n")
	sb.WriteString("5. Re-run governance coverage commands and continue until the weakest components improve.\n")

	return runCodexPrompt(root, "gftd-coverage-governance", sb.String(),
		"Fix the weakest governance WIT components listed above. Do NOT create worktrees.")
}

func sortedMapKeys(m map[string]int) []string {
	keys := make([]string, 0, len(m))
	for k := range m {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	return keys
}
