package main

import (
	"bytes"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
	"time"
)

type kaizenReport struct {
	EvaluatedAt string            `json:"evaluated_at"`
	TotalApps   int               `json:"total_apps"`
	AvgScore    float64           `json:"avg_domain_score"`
	Grades      map[string]int    `json:"grades"`
	Gaps        []kaizenGap       `json:"gaps"`
	Apps        []domainAppReport `json:"apps,omitempty"`
}

type kaizenGap struct {
	Feature string `json:"feature"`
	Count   int    `json:"count"`
	Impact  string `json:"impact"`
}

func runKaizen(args []string) error {
	if len(args) > 0 {
		switch args[0] {
		case "logs":
			return runKaizenLogs(args[1:])
		case "help", "--help", "-h":
			printKaizenUsage()
			return nil
		}
	}

	fs := flag.NewFlagSet("kaizen", flag.ContinueOnError)
	workspaceDir := fs.String("workspace-dir", "", "workspace root (default: git root)")
	jsonOut := fs.Bool("json", false, "output as JSON")
	autoFix := fs.Bool("fix", false, "run codex kaizen agent to fix gaps (codex exec sh)")
	filterGrade := fs.String("grade", "", "filter: only show apps with this grade (S/A/B/C/D)")
	limitN := fs.Int("limit", 0, "limit output to N apps (0=all)")
	showApps := fs.Bool("apps", false, "show per-app details")
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
			return err
		}
		wsRoot, err = findGitRoot(cwd)
		if err != nil {
			return fmt.Errorf("detect workspace root: %w", err)
		}
	}
	wsRoot, _ = filepath.Abs(wsRoot)

	// Single walk: collect all domain app reports (shared with code-quality)
	allApps := collectAndScoreDomainApps(wsRoot)
	check := checkDomainCoverage(wsRoot)

	// Aggregate stats from full set
	gradeCount := map[string]int{}
	totalApps := len(allApps)
	totalScore := 0
	for _, a := range allApps {
		gradeCount[a.Grade]++
		totalScore += a.DomainScore
	}

	// Filter + sort for display
	apps := allApps
	if *filterGrade != "" {
		apps = nil
		for _, a := range allApps {
			if a.Grade == *filterGrade {
				apps = append(apps, a)
			}
		}
	}
	sort.Slice(apps, func(i, j int) bool { return apps[i].DomainScore < apps[j].DomainScore })
	if *limitN > 0 && len(apps) > *limitN {
		apps = apps[:*limitN]
	}

	// Aggregate gaps from display set
	gapCounts := map[string]int{}
	for _, a := range apps {
		for _, m := range a.Missing {
			gapCounts[m]++
		}
	}
	gapImpact := map[string]string{
		"graph_labels":     "Domain graph model not designed — using generic Record label",
		"collection_kinds": "AT Protocol collections not domain-specific — using generic record kind",
		"custom_commands":  "No domain-specific commands — only template CRUD",
		"governance":       "Governance is template copy — no domain-specific RACI/compliance",
		"business_rules":   "Insufficient business logic — fewer than 5 conditional branches",
	}
	var gaps []kaizenGap
	for feat, count := range gapCounts {
		gaps = append(gaps, kaizenGap{Feature: feat, Count: count, Impact: gapImpact[feat]})
	}
	sort.Slice(gaps, func(i, j int) bool { return gaps[i].Count > gaps[j].Count })

	report := kaizenReport{
		EvaluatedAt: time.Now().UTC().Format(time.RFC3339),
		TotalApps:   totalApps,
		AvgScore:    float64(totalScore) / float64(max(totalApps, 1)),
		Grades:      gradeCount,
		Gaps:        gaps,
	}
	if *showApps {
		report.Apps = apps
	}

	if *jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(report)
	}

	// Text output
	fmt.Printf("gftd kaizen — Domain Coverage Analysis\n\n")
	fmt.Printf("  Evaluated: %s\n", report.EvaluatedAt)
	fmt.Printf("  Apps:      %d\n", report.TotalApps)
	fmt.Printf("  Avg Score: %.1f / 100\n", report.AvgScore)
	fmt.Printf("  code-quality domain_coverage: %.1f\n\n", check.Score)

	fmt.Printf("  Grade Distribution:\n")
	for _, g := range []string{"S", "A", "B", "C", "D"} {
		c := gradeCount[g]
		pct := float64(c) / float64(max(totalApps, 1)) * 100
		bar := strings.Repeat("█", c/10)
		fmt.Printf("    %s: %5d (%5.1f%%)  %s\n", g, c, pct, bar)
	}

	fmt.Printf("\n  Top Gaps:\n")
	for _, g := range gaps {
		fmt.Printf("    %-20s %4d apps  %s\n", g.Feature, g.Count, g.Impact)
	}

	if *showApps && len(apps) > 0 {
		fmt.Printf("\n  Apps (worst first):\n")
		fmt.Printf("    %5s %5s %-22s %-40s %s\n", "Score", "Grade", "Project", "App", "Missing")
		for _, a := range apps {
			missing := strings.Join(a.Missing, ", ")
			fmt.Printf("    %5d %5s %-22s %-40s %s\n", a.DomainScore, a.Grade, a.Project, a.App[:min(len(a.App), 40)], missing)
		}
	}

	// Auto-fix via codex
	if *autoFix {
		return runKaizenAgent(wsRoot, gaps, apps)
	}

	return nil
}

func printKaizenUsage() {
	fmt.Print(`gftd kaizen — kaizen entrypoint

USAGE:
  gftd kaizen [flags]
  gftd kaizen logs [flags]

MODES:
  (default)       Domain coverage analysis + optional codex-based fixes
  logs            Analyze gftd logs for query speed/errors and optionally run gftd code exec

EXAMPLES:
  gftd kaizen --apps --limit 20
  gftd kaizen logs --limit 300 --top 8
  gftd kaizen logs --fix --workspace-dir .
  gftd kaizen logs --fix --fix-engine murakumo --wait
`)
}

// runKaizenAgent launches codex exec sh to fix domain coverage gaps.
func runKaizenAgent(wsRoot string, gaps []kaizenGap, apps []domainAppReport) error {
	var sb strings.Builder
	sb.WriteString("You are a kaizen agent improving domain coverage for App implementations.\n\n")
	sb.WriteString("CRITICAL RULES:\n")
	sb.WriteString("- Do NOT create git worktrees. Work directly in the current directory.\n")
	sb.WriteString("- Each app needs DOMAIN-SPECIFIC logic, not template copies.\n")
	sb.WriteString("- Read each app's CLAUDE.md, magatama.jsonld, and existing app.ts to understand its domain.\n")
	sb.WriteString("- Design domain-specific Sql graph labels (not generic 'Record').\n")
	sb.WriteString("- Design domain-specific collection kinds (not generic 'record').\n")
	sb.WriteString("- Design domain-specific commands based on actual business operations.\n")
	sb.WriteString("- Design domain-specific governance (RACI roles, compliance frameworks).\n")
	sb.WriteString("- Add real business rules with conditional logic.\n\n")

	sb.WriteString("EVALUATION CRITERIA (gftd kaizen scoring):\n")
	sb.WriteString("- Graph labels: +10 pts per unique domain label (max 30)\n")
	sb.WriteString("- Collection kinds: +10 pts per unique domain kind (max 20)\n")
	sb.WriteString("- Custom commands: +5 pts per non-template command (max 15)\n")
	sb.WriteString("- Business rules: +1 pt per if/switch/transform (max 15)\n")
	sb.WriteString("- Data structures: +3 pts per interface/array/map (max 10)\n")
	sb.WriteString("- Governance: +5 pts if unique (not default template)\n")
	sb.WriteString("- DID paths: +3 pts per comAtprotoIdentityCreate path (max 5)\n")
	sb.WriteString("- Score >= 70 = S-grade\n\n")

	sb.WriteString("TOP GAPS:\n")
	for _, g := range gaps {
		if g.Count > 50 {
			sb.WriteString(fmt.Sprintf("  %s: %d apps (%s)\n", g.Feature, g.Count, g.Impact))
		}
	}

	// Include worst apps for context
	sb.WriteString("\nWORST 20 APPS (fix these first):\n")
	limit := 20
	if len(apps) < limit {
		limit = len(apps)
	}
	for i := 0; i < limit; i++ {
		a := apps[i]
		sb.WriteString(fmt.Sprintf("  score=%d project=%s app=%s missing=[%s]\n",
			a.DomainScore, a.Project, a.App, strings.Join(a.Missing, ",")))
	}

	sb.WriteString("\nProcess each app:\n")
	sb.WriteString("1. Read projects/ai-gftd-project-{project}/CLAUDE.md for domain context\n")
	sb.WriteString("2. Read the app's magatama.jsonld for identity/collections\n")
	sb.WriteString("3. Read the app's src/app.ts current implementation\n")
	sb.WriteString("4. Design domain-specific graph labels, collection kinds, commands\n")
	sb.WriteString("5. Update src/app.ts with domain logic\n")
	sb.WriteString("6. Update magatama.jsonld governance with domain-specific RACI\n")
	sb.WriteString("7. Verify with: gftd kaizen --apps --limit 5\n")

	return runCodexPrompt(wsRoot, "gftd-kaizen", sb.String(),
		"Fix the worst 20 apps listed above. Do NOT create worktrees.")
}

func runCodexPrompt(wsRoot, promptName, prompt, trailingInstruction string) error {
	promptFile := filepath.Join(os.TempDir(), promptName+"-prompt.txt")
	if err := os.WriteFile(promptFile, []byte(prompt), 0o644); err != nil {
		return fmt.Errorf("write prompt: %w", err)
	}

	fmt.Fprintf(os.Stderr, "==> launching codex agent via codex exec sh\n")
	fmt.Fprintf(os.Stderr, "==> prompt: %s\n", promptFile)

	// Check for codex
	codexPath, err := exec.LookPath("codex")
	if err != nil {
		return fmt.Errorf("codex not found in PATH — install: npm i -g @anthropic-ai/codex")
	}
	_ = codexPath

	// Detect if ANTHROPIC_API_KEY is set for codex
	reAnthropic := regexp.MustCompile(`^sk-ant-`)
	apiKey := os.Getenv("ANTHROPIC_API_KEY")
	if apiKey == "" || !reAnthropic.MatchString(apiKey) {
		fmt.Fprintf(os.Stderr, "warning: ANTHROPIC_API_KEY not set or invalid — codex may fail\n")
	}

	fullPrompt := prompt + "\n\n---\n" + trailingInstruction + "\n"
	cmd := exec.Command("codex", "exec", "-")
	cmd.Dir = wsRoot
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	cmd.Stdin = bytes.NewBufferString(fullPrompt)

	return cmd.Run()
}
