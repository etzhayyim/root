// kosei.go — gftd kosei: Project Configuration (構成) Management
//
// Manages, visualizes, and controls the execution tier (T1/T2/T3) of all
// App components across the monorepo. Supports tier promotion/demotion,
// auto-suggestion via heuristics, Parquet snapshots (DuckDB), and HTML visualization.
//
// Tier model (responsibility-based):
//
//	T1 Mitama Shared Executor  η=0.667  actor-manifest + primitives, no dedicated Worker
//	T2 App Worker              η=0.500  product Worker with own UI/UX (+ optional primitives)
//	T3 Infra Worker            η=0.910  platform infrastructure Worker (gateway/auth/graph/etc.)
//
// Data: 80-data/kosei/{config.json, snapshots/*.parquet, history/changes.parquet}
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"text/tabwriter"
	"time"
)

// ── Types ──────────────────────────────────────────────────────────────────

// koseiConfig is the canonical tier assignment store (config.json).
type koseiConfig struct {
	FormatVersion int                    `json:"format_version"`
	UpdatedAt     string                 `json:"updated_at"`
	Apps          map[string]koseiAppCfg `json:"apps"` // key = nanoid
}

// koseiAppCfg holds the tier assignment for one app.
type koseiAppCfg struct {
	Tier       string `json:"tier"`        // "T1" | "T2" | "T3"
	Notes      string `json:"notes"`       // human-readable rationale
	AssignedAt string `json:"assigned_at"` // RFC3339
	AssignedBy string `json:"assigned_by"` // "auto" | "manual"
}

// koseiAppMeta is static metadata extracted from magatama.jsonld.
type koseiAppMeta struct {
	Nanoid        string
	Name          string   // display name
	DID           string   // did:web:...
	Dir           string   // relative path from wsRoot
	PerformerType string   // "service" | "system" | ...
	UIType        string   // "appview" | "yoro" | ""
	RuntimeType   string   // "worker" | ...
	Collections   []string // subscribeRepos.collections
	Requires      []string // interfaces.requires
	GuestLang     string   // build.guestLanguage
	Description   string
}

// koseiAppState combines meta with current tier assignment.
type koseiAppState struct {
	koseiAppMeta
	Tier       string
	AssignedBy string
	AssignedAt string
	Notes      string
	Efficiency float64
}

// tierEfficiency maps tier ID to its Shannon efficiency (η).
var tierEfficiency = map[string]float64{
	"T1": 0.667,
	"T2": 0.500,
	"T3": 0.910,
}

// tierLabel returns a human-readable tier label.
func tierLabel(tier string) string {
	switch tier {
	case "T1":
		return "T1  Mitama Shared Executor"
	case "T2":
		return "T2  App Worker "
	case "T3":
		return "T3  Infra Worker"
	default:
		return "?   Unknown    "
	}
}

// tierNext returns the next-higher tier (for promote).
func tierNext(tier string) string {
	switch tier {
	case "T1":
		return "T2"
	case "T2":
		return "T3"
	default:
		return ""
	}
}

// tierPrev returns the next-lower tier (for demote).
func tierPrev(tier string) string {
	switch tier {
	case "T3":
		return "T2"
	case "T2":
		return "T1"
	default:
		return ""
	}
}

// ── Entry point ────────────────────────────────────────────────────────────

// runKosei dispatches gftd kosei subcommands.
func runKosei(args []string) error {
	if len(args) == 0 {
		return runKoseiSummary(args)
	}
	switch args[0] {
	case "list":
		return runKoseiList(args[1:])
	case "show":
		return runKoseiShow(args[1:])
	case "set":
		return runKoseiSet(args[1:])
	case "promote":
		return runKoseiPromote(args[1:])
	case "demote":
		return runKoseiDemote(args[1:])
	case "suggest":
		return runKoseiSuggest(args[1:])
	case "snapshot":
		return runKoseiSnapshot(args[1:])
	case "query":
		return runKoseiQuery(args[1:])
	case "history":
		return runKoseiHistory(args[1:])
	case "diff":
		return runKoseiDiff(args[1:])
	case "kashika":
		return runKoseiKashika(args[1:])
	case "stack":
		return runKoseiStackCmd(args[1:])
	case "sbom":
		return runKoseiSBOM(args[1:])
	case "matrix":
		return runKoseiMatrix(args[1:])
	case "stats":
		return runKoseiStats(args[1:])
	case "help", "--help", "-h":
		printKoseiUsage()
		return nil
	default:
		return fmt.Errorf("unknown kosei subcommand %q. Run 'gftd kosei help'", args[0])
	}
}

func printKoseiUsage() {
	fmt.Print(`gftd kosei — Project Configuration (構成) Management

Manages execution tier assignments (T1/T2/T3) across all App components.
Tier model (responsibility-based):
  T1 Mitama Shared Executor  η=0.667  actor-manifest + primitives, no dedicated Worker
  T2 App Worker              η=0.500  product Worker with own UI/UX (+ optional primitives)
  T3 Infra Worker            η=0.910  platform infrastructure Worker (gateway/auth/graph/etc.)

SUBCOMMANDS:
  (none)             Tier distribution summary + system η
  list               List all apps with tier, efficiency, and notes
  show <nanoid>      Show detailed config for one app
  set <nanoid>       Set tier explicitly  --tier T1|T2|T3 --reason "..."
  promote <nanoid>   Promote tier: T1→T2 or T2→T3
  demote <nanoid>    Demote tier:  T3→T2 or T2→T1
  suggest            Auto-suggest tiers based on source heuristics (--apply to save)
  snapshot           Write current config to Parquet (DuckDB ZSTD)
  query [SQL]        Query Parquet snapshots via DuckDB  ($TABLE = snapshots glob)
  history            Show tier change history (Parquet)
  diff               Diff current state vs last Parquet snapshot
  kashika            Open HTML tier visualization in browser
  stack <nanoid>     Full technology stack detail for one app
  sbom  <nanoid>     SBOM: CF bindings + npm deps + WIT imports + features
  matrix             Cross-app technology matrix (Svelte/WebGPU/ONNX/FIDO2/...)
  stats              Aggregate feature adoption statistics across all apps

COMMON FLAGS:
  --workspace-dir    Git root override
  --data-dir         Data directory  (default: <workspace>/80-data/kosei)
  --json             JSON output

`)
}

// ── Summary ────────────────────────────────────────────────────────────────

func runKoseiSummary(args []string) error {
	fs := flag.NewFlagSet("kosei", flag.ContinueOnError)
	workspaceDir := fs.String("workspace-dir", "", "workspace root")
	dataDir := fs.String("data-dir", "", "data directory")
	jsonOut := fs.Bool("json", false, "JSON output")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	wsRoot, dDir, err := koseiResolveRoots(*workspaceDir, *dataDir)
	if err != nil {
		return err
	}

	states, err := koseiLoadStates(wsRoot, dDir)
	if err != nil {
		return err
	}

	if *jsonOut {
		return json.NewEncoder(os.Stdout).Encode(states)
	}

	printKoseiSummary(states)
	return nil
}

func printKoseiSummary(states []koseiAppState) {
	counts := map[string]int{"T1": 0, "T2": 0, "T3": 0, "?": 0}
	for _, s := range states {
		if _, ok := counts[s.Tier]; ok {
			counts[s.Tier]++
		} else {
			counts["?"]++
		}
	}

	total := len(states)
	systemEta := koseiSystemEta(states)

	fmt.Printf("gftd kosei — Project Configuration (構成)\n")
	fmt.Printf("Apps: %d  |  System η: %.3f\n\n", total, systemEta)

	maxBar := 40
	for _, tier := range []string{"T1", "T2", "T3", "?"} {
		n := counts[tier]
		pct := 0.0
		if total > 0 {
			pct = float64(n) / float64(total) * 100
		}
		bar := int(pct / 100 * float64(maxBar))
		barStr := strings.Repeat("█", bar) + strings.Repeat("░", maxBar-bar)
		eta := tierEfficiency[tier]
		etaStr := ""
		if eta > 0 {
			etaStr = fmt.Sprintf("η=%.3f", eta)
		}
		label := tierLabel(tier)
		fmt.Printf("  %s  %s  %4d apps  %5.1f%%  %s\n", label, barStr, n, pct, etaStr)
	}

	fmt.Printf("\nRun 'gftd kosei list' to see all apps.\n")
	fmt.Printf("Run 'gftd kosei suggest --apply' to auto-assign missing tiers.\n")
}

// koseiSystemEta computes weighted average η across all apps.
func koseiSystemEta(states []koseiAppState) float64 {
	if len(states) == 0 {
		return 0
	}
	total := 0.0
	for _, s := range states {
		if s.Efficiency > 0 {
			total += s.Efficiency
		}
	}
	return total / float64(len(states))
}

// ── List ───────────────────────────────────────────────────────────────────

func runKoseiList(args []string) error {
	fs := flag.NewFlagSet("kosei list", flag.ContinueOnError)
	workspaceDir := fs.String("workspace-dir", "", "workspace root")
	dataDir := fs.String("data-dir", "", "data directory")
	filterTier := fs.String("tier", "", "filter by tier: T1, T2, T3")
	sortBy := fs.String("sort", "name", "sort by: name, tier, eta")
	jsonOut := fs.Bool("json", false, "JSON output")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	wsRoot, dDir, err := koseiResolveRoots(*workspaceDir, *dataDir)
	if err != nil {
		return err
	}

	states, err := koseiLoadStates(wsRoot, dDir)
	if err != nil {
		return err
	}

	if *filterTier != "" {
		ft := strings.ToUpper(*filterTier)
		var filtered []koseiAppState
		for _, s := range states {
			if s.Tier == ft {
				filtered = append(filtered, s)
			}
		}
		states = filtered
	}

	koseiSortStates(states, *sortBy)

	if *jsonOut {
		return json.NewEncoder(os.Stdout).Encode(states)
	}

	w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
	fmt.Fprintln(w, "NANOID\tNAME\tTIER\tη\tBY\tNOTES")
	fmt.Fprintln(w, "──────\t────\t────\t─\t──\t─────")
	for _, s := range states {
		etaStr := "—"
		if s.Efficiency > 0 {
			etaStr = fmt.Sprintf("%.3f", s.Efficiency)
		}
		notes := s.Notes
		if len(notes) > 40 {
			notes = notes[:37] + "..."
		}
		fmt.Fprintf(w, "%s\t%s\t%s\t%s\t%s\t%s\n",
			s.Nanoid, truncStr(s.Name, 28), s.Tier, etaStr, s.AssignedBy, notes)
	}
	w.Flush()
	fmt.Printf("\n%d apps shown\n", len(states))
	return nil
}

// ── Show ───────────────────────────────────────────────────────────────────

func runKoseiShow(args []string) error {
	target, flagArgs := koseiExtractTarget(args)

	fs := flag.NewFlagSet("kosei show", flag.ContinueOnError)
	workspaceDir := fs.String("workspace-dir", "", "workspace root")
	dataDir := fs.String("data-dir", "", "data directory")
	jsonOut := fs.Bool("json", false, "JSON output")
	if err := fs.Parse(flagArgs); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	if target == "" {
		return fmt.Errorf("usage: gftd kosei show <nanoid>")
	}

	wsRoot, dDir, err := koseiResolveRoots(*workspaceDir, *dataDir)
	if err != nil {
		return err
	}

	states, err := koseiLoadStates(wsRoot, dDir)
	if err != nil {
		return err
	}

	var found *koseiAppState
	for i := range states {
		if states[i].Nanoid == target || states[i].Name == target {
			found = &states[i]
			break
		}
	}
	if found == nil {
		return fmt.Errorf("app %q not found", target)
	}

	if *jsonOut {
		return json.NewEncoder(os.Stdout).Encode(found)
	}

	fmt.Printf("App:           %s  (%s)\n", found.Name, found.Nanoid)
	fmt.Printf("DID:           %s\n", found.DID)
	fmt.Printf("Dir:           %s\n", found.Dir)
	fmt.Printf("Tier:          %s  (η=%.3f)\n", found.Tier, found.Efficiency)
	fmt.Printf("Assigned by:   %s  at %s\n", found.AssignedBy, found.AssignedAt)
	fmt.Printf("Notes:         %s\n", found.Notes)
	fmt.Printf("PerformerType: %s\n", found.PerformerType)
	fmt.Printf("UIType:        %s\n", found.UIType)
	fmt.Printf("RuntimeType:   %s\n", found.RuntimeType)
	if len(found.Collections) > 0 {
		fmt.Printf("Collections:   %s\n", strings.Join(found.Collections, ", "))
	}
	if len(found.Requires) > 0 {
		fmt.Printf("Requires:      %s\n", strings.Join(found.Requires, ", "))
	}
	return nil
}

// ── Set / Promote / Demote ─────────────────────────────────────────────────

func runKoseiSet(args []string) error {
	// Extract nanoid (first non-flag arg) before flag.Parse stops at it.
	target, flagArgs := koseiExtractTarget(args)

	fs := flag.NewFlagSet("kosei set", flag.ContinueOnError)
	workspaceDir := fs.String("workspace-dir", "", "workspace root")
	dataDir := fs.String("data-dir", "", "data directory")
	tier := fs.String("tier", "", "tier: T1, T2, T3")
	reason := fs.String("reason", "", "rationale for change")
	if err := fs.Parse(flagArgs); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	if target == "" || *tier == "" {
		return fmt.Errorf("usage: gftd kosei set <nanoid> --tier T1|T2|T3 [--reason \"...\"]")
	}

	newTier := strings.ToUpper(*tier)
	if newTier != "T1" && newTier != "T2" && newTier != "T3" {
		return fmt.Errorf("invalid tier %q: must be T1, T2, or T3", *tier)
	}

	return koseiChangeTier(target, newTier, *reason, "manual", *workspaceDir, *dataDir)
}

func runKoseiPromote(args []string) error {
	target, flagArgs := koseiExtractTarget(args)

	fs := flag.NewFlagSet("kosei promote", flag.ContinueOnError)
	workspaceDir := fs.String("workspace-dir", "", "workspace root")
	dataDir := fs.String("data-dir", "", "data directory")
	reason := fs.String("reason", "", "rationale")
	if err := fs.Parse(flagArgs); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	if target == "" {
		return fmt.Errorf("usage: gftd kosei promote <nanoid> [--reason \"...\"]")
	}

	wsRoot, dDir, err := koseiResolveRoots(*workspaceDir, *dataDir)
	if err != nil {
		return err
	}

	cfg := koseiLoadConfig(dDir)
	app, ok := cfg.Apps[target]
	if !ok {
		app = koseiAppCfg{Tier: "T1"}
	}

	next := tierNext(app.Tier)
	if next == "" {
		return fmt.Errorf("app %q is already at T3 (highest tier)", target)
	}

	_ = wsRoot
	return koseiChangeTier(target, next, *reason, "manual", *workspaceDir, *dataDir)
}

func runKoseiDemote(args []string) error {
	target, flagArgs := koseiExtractTarget(args)

	fs := flag.NewFlagSet("kosei demote", flag.ContinueOnError)
	workspaceDir := fs.String("workspace-dir", "", "workspace root")
	dataDir := fs.String("data-dir", "", "data directory")
	reason := fs.String("reason", "", "rationale")
	if err := fs.Parse(flagArgs); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	if target == "" {
		return fmt.Errorf("usage: gftd kosei demote <nanoid> [--reason \"...\"]")
	}

	wsRoot, dDir, err := koseiResolveRoots(*workspaceDir, *dataDir)
	if err != nil {
		return err
	}

	cfg := koseiLoadConfig(dDir)
	app, ok := cfg.Apps[target]
	if !ok {
		app = koseiAppCfg{Tier: "T1"}
	}

	prev := tierPrev(app.Tier)
	if prev == "" {
		return fmt.Errorf("app %q is already at T1 (lowest tier)", target)
	}

	_ = wsRoot
	return koseiChangeTier(target, prev, *reason, "manual", *workspaceDir, *dataDir)
}

// koseiChangeTier applies a tier change, writes config.json, and logs the change.
func koseiChangeTier(nanoid, newTier, reason, by, workspaceDirFlag, dataDirFlag string) error {
	wsRoot, dDir, err := koseiResolveRoots(workspaceDirFlag, dataDirFlag)
	if err != nil {
		return err
	}
	_ = wsRoot

	cfg := koseiLoadConfig(dDir)
	if cfg.Apps == nil {
		cfg.Apps = make(map[string]koseiAppCfg)
	}

	old := cfg.Apps[nanoid]
	oldTier := old.Tier
	if oldTier == "" {
		oldTier = "?"
	}

	now := time.Now().UTC().Format(time.RFC3339)
	cfg.Apps[nanoid] = koseiAppCfg{
		Tier:       newTier,
		Notes:      reason,
		AssignedAt: now,
		AssignedBy: by,
	}
	cfg.UpdatedAt = now

	if err := koseiSaveConfig(dDir, cfg); err != nil {
		return fmt.Errorf("save config: %w", err)
	}

	// Append to change history Parquet.
	if err := koseiAppendChange(dDir, koseiChangeRow{
		ChangedAt: now,
		AppName:   nanoid,
		Nanoid:    nanoid,
		OldTier:   oldTier,
		NewTier:   newTier,
		Reason:    reason,
		ChangedBy: by,
	}); err != nil {
		fmt.Fprintf(os.Stderr, "warn: change history write failed: %v\n", err)
	}

	fmt.Printf("✓  %s: %s → %s  (by %s)\n", nanoid, oldTier, newTier, by)
	return nil
}

// ── Diff ───────────────────────────────────────────────────────────────────

func runKoseiDiff(args []string) error {
	fs := flag.NewFlagSet("kosei diff", flag.ContinueOnError)
	workspaceDir := fs.String("workspace-dir", "", "workspace root")
	dataDir := fs.String("data-dir", "", "data directory")
	jsonOut := fs.Bool("json", false, "JSON output")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	wsRoot, dDir, err := koseiResolveRoots(*workspaceDir, *dataDir)
	if err != nil {
		return err
	}

	// Current state
	current, err := koseiLoadStates(wsRoot, dDir)
	if err != nil {
		return err
	}
	currentMap := make(map[string]string)
	for _, s := range current {
		currentMap[s.Nanoid] = s.Tier
	}

	// Last snapshot from Parquet
	snapshotsGlob := filepath.Join(dDir, "snapshots", "*.parquet")
	matches, _ := filepath.Glob(snapshotsGlob)
	if len(matches) == 0 {
		fmt.Println("No snapshots found. Run 'gftd kosei snapshot' first.")
		return nil
	}

	type diffEntry struct {
		Nanoid   string `json:"nanoid"`
		OldTier  string `json:"old_tier"`
		NewTier  string `json:"new_tier"`
		Action   string `json:"action"`
	}

	// Read latest snapshot
	latestSnap := matches[len(matches)-1]
	snapData, err := koseiReadLatestSnapshot(latestSnap)
	if err != nil {
		return fmt.Errorf("read snapshot: %w", err)
	}

	var diffs []diffEntry
	seen := make(map[string]bool)
	for nanoid, snapTier := range snapData {
		seen[nanoid] = true
		curTier, ok := currentMap[nanoid]
		if !ok {
			curTier = "?"
		}
		if curTier != snapTier {
			action := "changed"
			if snapTier == "?" || snapTier == "" {
				action = "added"
			} else if curTier == "?" || curTier == "" {
				action = "removed"
			}
			diffs = append(diffs, diffEntry{Nanoid: nanoid, OldTier: snapTier, NewTier: curTier, Action: action})
		}
	}
	// New apps not in snapshot
	for nanoid, curTier := range currentMap {
		if !seen[nanoid] {
			diffs = append(diffs, diffEntry{Nanoid: nanoid, OldTier: "?", NewTier: curTier, Action: "new"})
		}
	}

	sort.Slice(diffs, func(i, j int) bool { return diffs[i].Nanoid < diffs[j].Nanoid })

	if *jsonOut {
		return json.NewEncoder(os.Stdout).Encode(diffs)
	}

	if len(diffs) == 0 {
		fmt.Println("No tier changes since last snapshot.")
		return nil
	}

	fmt.Printf("Tier changes since last snapshot (%s):\n\n", filepath.Base(latestSnap))
	w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
	fmt.Fprintln(w, "NANOID\tACTION\tOLD\t→\tNEW")
	for _, d := range diffs {
		fmt.Fprintf(w, "%s\t%s\t%s\t→\t%s\n", d.Nanoid, d.Action, d.OldTier, d.NewTier)
	}
	w.Flush()
	fmt.Printf("\n%d change(s)\n", len(diffs))
	return nil
}

// ── Scan helpers ───────────────────────────────────────────────────────────

// koseiScanApps discovers all App metadata from the workspace.
func koseiScanApps(wsRoot string) []koseiAppMeta {
	var apps []koseiAppMeta
	projectsDir := filepath.Join(wsRoot, "60-apps")

	projEntries, err := os.ReadDir(projectsDir)
	if err != nil {
		// Fallback: try cwd-relative
		projectsDir = filepath.Join(".", "60-apps")
		projEntries, err = os.ReadDir(projectsDir)
		if err != nil {
			return apps
		}
	}

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
			appDir := filepath.Join(wasmDir, we.Name())
			jPath := filepath.Join(appDir, "magatama.jsonld")
			if _, err := os.Stat(jPath); err != nil {
				continue
			}
			meta := koseiParseJSONLD(jPath)
			if meta.Nanoid == "" {
				continue
			}
			rel, _ := filepath.Rel(wsRoot, appDir)
			meta.Dir = rel
			apps = append(apps, meta)
		}
	}

	sort.Slice(apps, func(i, j int) bool { return apps[i].Nanoid < apps[j].Nanoid })
	return apps
}

// koseiParseJSONLD extracts kosei metadata from a magatama.jsonld file.
func koseiParseJSONLD(path string) koseiAppMeta {
	var meta koseiAppMeta
	data, err := os.ReadFile(path)
	if err != nil {
		return meta
	}
	var jld struct {
		ID            string `json:"@id"`
		Name          string `json:"name"`
		Nanoid        string `json:"nanoid"`
		PerformerType string `json:"performerType"`
		UIType        string `json:"uiType"`
		RuntimeType   string `json:"runtimeType"`
		Profile       *struct {
			DisplayName string `json:"displayName"`
			Description string `json:"description"`
		} `json:"profile"`
		Triggers *struct {
			SubscribeRepos *struct {
				Collections []string `json:"collections"`
			} `json:"subscribeRepos"`
		} `json:"triggers"`
		Interfaces *struct {
			Requires []interface{} `json:"requires"`
		} `json:"interfaces"`
		Build *struct {
			GuestLanguage string `json:"guestLanguage"`
		} `json:"build"`
	}
	if err := json.Unmarshal(data, &jld); err != nil {
		return meta
	}

	meta.DID = jld.ID
	meta.Nanoid = jld.Nanoid
	meta.Name = jld.Name
	meta.PerformerType = jld.PerformerType
	meta.UIType = jld.UIType
	meta.RuntimeType = jld.RuntimeType
	if jld.Profile != nil {
		if jld.Profile.DisplayName != "" {
			meta.Name = jld.Profile.DisplayName
		}
		meta.Description = jld.Profile.Description
	}
	if jld.Triggers != nil && jld.Triggers.SubscribeRepos != nil {
		meta.Collections = jld.Triggers.SubscribeRepos.Collections
	}
	if jld.Interfaces != nil {
		for _, r := range jld.Interfaces.Requires {
			if s, ok := r.(string); ok {
				meta.Requires = append(meta.Requires, s)
			}
		}
	}
	if jld.Build != nil {
		meta.GuestLang = jld.Build.GuestLanguage
	}
	return meta
}

// koseiLoadStates merges scanned app metadata with config tier assignments.
func koseiLoadStates(wsRoot, dDir string) ([]koseiAppState, error) {
	apps := koseiScanApps(wsRoot)
	cfg := koseiLoadConfig(dDir)

	var states []koseiAppState
	for _, app := range apps {
		s := koseiAppState{koseiAppMeta: app}
		if c, ok := cfg.Apps[app.Nanoid]; ok {
			s.Tier = c.Tier
			s.AssignedBy = c.AssignedBy
			s.AssignedAt = c.AssignedAt
			s.Notes = c.Notes
		} else {
			s.Tier = "?"
			s.AssignedBy = "—"
		}
		s.Efficiency = tierEfficiency[s.Tier]
		states = append(states, s)
	}
	return states, nil
}

// ── Sort helpers ───────────────────────────────────────────────────────────

func koseiSortStates(states []koseiAppState, by string) {
	switch by {
	case "tier":
		sort.Slice(states, func(i, j int) bool {
			if states[i].Tier == states[j].Tier {
				return states[i].Nanoid < states[j].Nanoid
			}
			return states[i].Tier < states[j].Tier
		})
	case "eta":
		sort.Slice(states, func(i, j int) bool {
			if states[i].Efficiency == states[j].Efficiency {
				return states[i].Nanoid < states[j].Nanoid
			}
			return states[i].Efficiency > states[j].Efficiency
		})
	default: // name
		sort.Slice(states, func(i, j int) bool { return states[i].Nanoid < states[j].Nanoid })
	}
}

// ── Root resolution ────────────────────────────────────────────────────────

func koseiResolveRoots(workspaceDirFlag, dataDirFlag string) (wsRoot, dDir string, err error) {
	wsRoot, err = resolveShannonRoot(workspaceDirFlag)
	if err != nil {
		return
	}
	dDir = dataDirFlag
	if dDir == "" {
		dDir = filepath.Join(wsRoot, "80-data", "kosei")
	}
	if err = os.MkdirAll(filepath.Join(dDir, "snapshots"), 0755); err != nil {
		return
	}
	if err = os.MkdirAll(filepath.Join(dDir, "history"), 0755); err != nil {
		return
	}
	return
}

// ── Misc helpers ───────────────────────────────────────────────────────────
// (truncStr is defined in world_coverage.go and shared across the package)

// koseiExtractTarget extracts the first non-flag argument as the target nanoid
// and returns the remaining args for flag.Parse.
// This is needed because Go's flag package stops parsing at the first non-flag arg.
func koseiExtractTarget(args []string) (target string, rest []string) {
	for i, a := range args {
		if !strings.HasPrefix(a, "-") && target == "" {
			target = a
		} else {
			_ = i
			rest = append(rest, a)
		}
	}
	return
}
