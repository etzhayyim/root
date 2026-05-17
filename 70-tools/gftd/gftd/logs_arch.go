package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"strings"
	"time"
)

// ── gftd logs arch — Architecture event log from git history + deploy state ──

// archLogEvent represents an architecture-level event derived from git commits.
type archLogEvent struct {
	TS      string `json:"ts"`
	SHA     string `json:"sha"`
	Author  string `json:"author"`
	Layer   string `json:"layer"`   // infra, packages, projects, docs, wit, root
	Scope   string `json:"scope"`   // specific project/package/component name
	Message string `json:"message"`
	Files   int    `json:"files"`
	Added   int    `json:"added"`
	Removed int    `json:"removed"`
}

// archLogReport is the full architecture log output.
type archLogReport struct {
	GeneratedAt string            `json:"generated_at"`
	TotalEvents int               `json:"total_events"`
	ByLayer     map[string]int    `json:"by_layer"`
	ByScope     map[string]int    `json:"by_scope"`
	Events      []archLogEvent    `json:"events"`
	DeployState []archDeployEntry `json:"deploy_state,omitempty"`
}

// archDeployEntry represents a deployed app from .deploy-state.json.
type archDeployEntry struct {
	App       string `json:"app"`
	Project   string `json:"project"`
	SHA       string `json:"sha"`
	Version   string `json:"version"`
	DeployAt  string `json:"deploy_at"`
	Source    string `json:"source"`
}

// runLogsArch implements `gftd logs arch`.
func runLogsArch(args []string) error {
	fs := flag.NewFlagSet("logs arch", flag.ContinueOnError)
	asJSON := fs.Bool("json", false, "emit JSON")
	limit := fs.Int("limit", 100, "max git commits to scan")
	hours := fs.Int("hours", 24, "lookback window (hours)")
	layer := fs.String("layer", "", "filter by layer (infra, packages, projects, docs, wit)")
	scope := fs.String("scope", "", "filter by scope (project/package name)")
	wsDir := fs.String("workspace-dir", "", "workspace root (default: git root)")
	showDeploy := fs.Bool("deploy", false, "include deploy state")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	wsRoot, err := resolveWSRoot(*wsDir)
	if err != nil {
		return err
	}

	since := time.Now().Add(-time.Duration(*hours) * time.Hour).Format("2006-01-02T15:04:05")

	events, err := extractArchEvents(wsRoot, since, *limit)
	if err != nil {
		return err
	}

	// Filter
	if *layer != "" {
		var filtered []archLogEvent
		for _, e := range events {
			if e.Layer == *layer {
				filtered = append(filtered, e)
			}
		}
		events = filtered
	}
	if *scope != "" {
		var filtered []archLogEvent
		for _, e := range events {
			if strings.Contains(strings.ToLower(e.Scope), strings.ToLower(*scope)) {
				filtered = append(filtered, e)
			}
		}
		events = filtered
	}

	// Aggregates
	byLayer := map[string]int{}
	byScope := map[string]int{}
	for _, e := range events {
		byLayer[e.Layer]++
		if e.Scope != "" {
			byScope[e.Scope]++
		}
	}

	// Deploy state
	var deploys []archDeployEntry
	if *showDeploy {
		deploys = scanDeployState(wsRoot)
	}

	report := archLogReport{
		GeneratedAt: time.Now().UTC().Format(time.RFC3339),
		TotalEvents: len(events),
		ByLayer:     byLayer,
		ByScope:     byScope,
		Events:      events,
		DeployState: deploys,
	}

	if *asJSON {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(report)
	}

	printArchLogReport(&report, *showDeploy)
	return nil
}

// extractArchEvents parses git log and classifies commits by architectural layer.
func extractArchEvents(wsRoot, since string, limit int) ([]archLogEvent, error) {
	cmd := exec.Command("git", "log",
		fmt.Sprintf("--since=%s", since),
		fmt.Sprintf("-n%d", limit),
		"--pretty=format:%H|%aI|%an|%s",
		"--stat",
	)
	cmd.Dir = wsRoot
	out, err := cmd.Output()
	if err != nil {
		return nil, fmt.Errorf("git log failed: %w", err)
	}

	var events []archLogEvent
	lines := strings.Split(string(out), "\n")
	var current *archLogEvent

	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}

		// Check if this is a commit header line (SHA|date|author|message)
		parts := strings.SplitN(line, "|", 4)
		if len(parts) == 4 && len(parts[0]) == 40 {
			if current != nil {
				events = append(events, *current)
			}
			current = &archLogEvent{
				SHA:     parts[0][:8],
				TS:      parts[1],
				Author:  parts[2],
				Message: parts[3],
			}
			continue
		}

		// Stat summary line (e.g. " 5 files changed, 100 insertions(+), 20 deletions(-)")
		if strings.Contains(line, "file") && strings.Contains(line, "changed") {
			if current != nil {
				current.Files = parseStatCount(line, "file")
				current.Added = parseStatCount(line, "insertion")
				current.Removed = parseStatCount(line, "deletion")
			}
			continue
		}

		// File path line from --stat (e.g. " infra/pulumi/index.ts | 15 +++---")
		if current != nil && strings.Contains(line, "|") {
			filePath := strings.TrimSpace(strings.SplitN(line, "|", 2)[0])
			layer, scope := classifyPath(filePath)
			if current.Layer == "" || layerPriority(layer) > layerPriority(current.Layer) {
				current.Layer = layer
			}
			if scope != "" && current.Scope == "" {
				current.Scope = scope
			}
		}
	}
	if current != nil {
		events = append(events, *current)
	}

	// Default layer for commits with no classified files
	for i := range events {
		if events[i].Layer == "" {
			events[i].Layer = "root"
		}
	}

	return events, nil
}

// classifyPath determines the architectural layer and scope from a file path.
func classifyPath(path string) (layer, scope string) {
	path = strings.TrimSpace(path)
	parts := strings.Split(path, "/")

	switch {
	case strings.HasPrefix(path, "infra/"):
		if len(parts) >= 2 {
			scope = parts[1]
		}
		return "infra", scope

	case strings.HasPrefix(path, "packages/contract/wit/"):
		if len(parts) >= 5 {
			scope = parts[3] // deps/magatama-*
		}
		return "wit", scope

	case strings.HasPrefix(path, "packages/"):
		if len(parts) >= 3 {
			scope = parts[1] + "/" + parts[2]
		}
		return "packages", scope

	case strings.HasPrefix(path, "projects/"):
		for _, p := range parts {
			if strings.HasPrefix(p, "ai-gftd-project-") {
				scope = strings.TrimPrefix(p, "ai-gftd-project-")
				break
			}
		}
		return "projects", scope

	case strings.HasPrefix(path, "docs/"):
		return "docs", ""

	default:
		return "root", ""
	}
}

// layerPriority returns priority for layer classification (higher = more specific).
func layerPriority(layer string) int {
	switch layer {
	case "wit":
		return 5
	case "infra":
		return 4
	case "packages":
		return 3
	case "projects":
		return 2
	case "docs":
		return 1
	default:
		return 0
	}
}

// parseStatCount extracts a number from git stat summary line.
func parseStatCount(line, keyword string) int {
	idx := strings.Index(line, keyword)
	if idx < 0 {
		return 0
	}
	// Walk backward from keyword to find the number
	numStr := ""
	for i := idx - 1; i >= 0; i-- {
		c := line[i]
		if c >= '0' && c <= '9' {
			numStr = string(c) + numStr
		} else if numStr != "" {
			break
		}
	}
	n := 0
	for _, c := range numStr {
		n = n*10 + int(c-'0')
	}
	return n
}

// scanDeployState reads .deploy-state.json files across the workspace.
func scanDeployState(wsRoot string) []archDeployEntry {
	var entries []archDeployEntry

	projectsDir := filepath.Join(wsRoot, "projects")
	projEntries, _ := os.ReadDir(projectsDir)
	for _, pe := range projEntries {
		if !pe.IsDir() || !strings.HasPrefix(pe.Name(), "ai-gftd-project-") {
			continue
		}
		project := strings.TrimPrefix(pe.Name(), "ai-gftd-project-")
		wasmDir := filepath.Join(projectsDir, pe.Name(), "wasm")
		wasmEntries, err := os.ReadDir(wasmDir)
		if err != nil {
			continue
		}
		for _, we := range wasmEntries {
			if !we.IsDir() {
				continue
			}
			statePath := filepath.Join(wasmDir, we.Name(), ".deploy-state.json")
			data, err := os.ReadFile(statePath)
			if err != nil {
				continue
			}
			var state struct {
				SHA      string `json:"deploy_sha"`
				Version  string `json:"version"`
				DeployAt string `json:"deploy_at"`
				Source   string `json:"source"`
			}
			if json.Unmarshal(data, &state) == nil && state.SHA != "" {
				entries = append(entries, archDeployEntry{
					App:      we.Name(),
					Project:  project,
					SHA:      state.SHA,
					Version:  state.Version,
					DeployAt: state.DeployAt,
					Source:   state.Source,
				})
			}
		}
	}

	sort.Slice(entries, func(i, j int) bool {
		return entries[i].DeployAt > entries[j].DeployAt
	})
	return entries
}

// printArchLogReport renders the architecture event log as a terminal table.
func printArchLogReport(r *archLogReport, showDeploy bool) {
	fmt.Println()
	fmt.Println("╔══════════════════════════════════════════════════════════════════════════════════╗")
	fmt.Println("║                    GFTD Architecture Event Log                                  ║")
	fmt.Printf("║                    %s                                     ║\n", time.Now().Format("2006-01-02 15:04:05"))
	fmt.Println("╠══════════════════════════════════════════════════════════════════════════════════╣")
	fmt.Println()

	// Layer breakdown
	fmt.Printf("  Total: %d commits\n", r.TotalEvents)
	fmt.Print("  Layers: ")
	type layerCount struct{ l string; n int }
	var lcs []layerCount
	for l, n := range r.ByLayer {
		lcs = append(lcs, layerCount{l, n})
	}
	sort.Slice(lcs, func(i, j int) bool { return lcs[i].n > lcs[j].n })
	for _, lc := range lcs {
		fmt.Printf("%s=%d  ", lc.l, lc.n)
	}
	fmt.Println()

	// Top scopes
	if len(r.ByScope) > 0 {
		fmt.Print("  Top scopes: ")
		type scopeCount struct{ s string; n int }
		var scs []scopeCount
		for s, n := range r.ByScope {
			scs = append(scs, scopeCount{s, n})
		}
		sort.Slice(scs, func(i, j int) bool { return scs[i].n > scs[j].n })
		shown := 0
		for _, sc := range scs {
			if shown >= 10 {
				fmt.Printf("+%d more", len(scs)-10)
				break
			}
			fmt.Printf("%s=%d  ", sc.s, sc.n)
			shown++
		}
		fmt.Println()
	}
	fmt.Println()

	// Event table
	events := r.Events
	if len(events) > 50 {
		events = events[:50]
	}
	fmt.Println("  ┌──────────┬──────────┬────────────┬───────────────┬──────────────────────────────────────────┐")
	fmt.Println("  │ SHA      │ Layer    │ Scope      │ Files +/-     │ Message                                  │")
	fmt.Println("  ├──────────┼──────────┼────────────┼───────────────┼──────────────────────────────────────────┤")
	for _, e := range events {
		layer := e.Layer
		if len(layer) > 8 {
			layer = layer[:8]
		}
		scope := e.Scope
		if len(scope) > 10 {
			scope = scope[:10]
		}
		msg := e.Message
		if len(msg) > 40 {
			msg = msg[:37] + "..."
		}
		churn := fmt.Sprintf("%d +%d -%d", e.Files, e.Added, e.Removed)
		fmt.Printf("  │ %s │ %-8s │ %-10s │ %-13s │ %-40s │\n",
			e.SHA, layer, scope, churn, msg)
	}
	fmt.Println("  └──────────┴──────────┴────────────┴───────────────┴──────────────────────────────────────────┘")
	fmt.Println()

	// Deploy state
	if showDeploy && len(r.DeployState) > 0 {
		deploys := r.DeployState
		if len(deploys) > 30 {
			deploys = deploys[:30]
		}
		fmt.Printf("  Deploy State (%d apps):\n", len(r.DeployState))
		fmt.Println("  ┌───────────────────────────┬────────────────┬──────────┬─────────┬─────────────────────┐")
		fmt.Println("  │ App                       │ Project        │ SHA      │ Source  │ Deployed At         │")
		fmt.Println("  ├───────────────────────────┼────────────────┼──────────┼─────────┼─────────────────────┤")
		for _, d := range deploys {
			app := d.App
			if len(app) > 25 {
				app = app[:25]
			}
			proj := d.Project
			if len(proj) > 14 {
				proj = proj[:14]
			}
			sha := d.SHA
			if len(sha) > 8 {
				sha = sha[:8]
			}
			src := d.Source
			if len(src) > 7 {
				src = src[:7]
			}
			deployAt := d.DeployAt
			if len(deployAt) > 19 {
				deployAt = deployAt[:19]
			}
			fmt.Printf("  │ %-25s │ %-14s │ %s │ %-7s │ %s │\n",
				app, proj, sha, src, deployAt)
		}
		fmt.Println("  └───────────────────────────┴────────────────┴──────────┴─────────┴─────────────────────┘")
		fmt.Println()
	}

	fmt.Println("╚══════════════════════════════════════════════════════════════════════════════════╝")
}
