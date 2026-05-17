// coverage_actors — Actor metadata completeness (η) analysis and autonomous healing.
// Implements: gftd coverage actors [list|eta|inspect|heal|standardize]
// Design: 90-docs/260409-shinka-coverage-healing-design.md
package main

import (
	"bytes"
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"math"
	"net/http"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"sync"
	"sync/atomic"
	"time"

	"github.com/etzhayyim/root/70-tools/gftd/gftd/db"
)

// actorCoverageRow represents a single actor's metadata completeness from the graph query layer.
type actorCoverageRow struct {
	DID               string   `json:"did"`
	Name              string   `json:"name"`
	DisplayName       string   `json:"displayName"`
	Description       string   `json:"description"`
	Runtime           string   `json:"runtime"`
	Edge              string   `json:"edge,omitempty"`
	LegacyTier        string   `json:"legacyExecutionTier,omitempty"`
	WitImports        string   `json:"witImports"`
	WitExports        string   `json:"witExports"`
	ConvoSystemPrompt string   `json:"convoSystemPrompt"`
	Capabilities      string   `json:"capabilities"`
	PerformerType     string   `json:"performerType"`
	Operator          string   `json:"operator"`
	CoverageScore     float64  `json:"coverageScore"`
	Grade             string   `json:"grade"`
	MissingFields     []string `json:"missingFields"`
	ManifestPath      string   `json:"-"`
}

// actorCoverageReport is the top-level report for coverage actors list/eta.
type actorCoverageReport struct {
	EvaluatedAt string             `json:"evaluatedAt"`
	Source      string             `json:"source"`
	TotalActors int                `json:"totalActors"`
	Eta         float64            `json:"eta"`
	Critical    int                `json:"critical"`
	Incomplete  int                `json:"incomplete"`
	Complete    int                `json:"complete"`
	Actors      []actorCoverageRow `json:"actors,omitempty"`
}

// actorHealResult holds the healing outcome for one actor.
type actorHealResult struct {
	DID             string            `json:"did"`
	Name            string            `json:"name"`
	FixedFields     []string          `json:"fixedFields"`
	GeneratedValues map[string]string `json:"-"` // field→value for write-back
	Error           string            `json:"error,omitempty"`
}

// actorHealReport is the top-level report for coverage actors heal.
type actorHealReport struct {
	EvaluatedAt string            `json:"evaluatedAt"`
	HealedCount int               `json:"healedCount"`
	DryRun      bool              `json:"dryRun"`
	Results     []actorHealResult `json:"results"`
}

type coverageAction struct {
	ActorDID       string  `json:"actorDid"`
	ActorName      string  `json:"actorName"`
	Runtime        string  `json:"runtime,omitempty"`
	Field          string  `json:"field"`
	CurrentScore   float64 `json:"currentScore"`
	NextScore      float64 `json:"nextScore"`
	EtaGain        float64 `json:"etaGain"`
	Cost           int     `json:"cost"`
	CostPerEtaGain float64 `json:"costPerEtaGain"`
}

type coveragePathReport struct {
	EvaluatedAt     string           `json:"evaluatedAt"`
	Source          string           `json:"source"`
	CurrentEta      float64          `json:"currentEta"`
	TargetEta       float64          `json:"targetEta"`
	ReachedEta      float64          `json:"reachedEta"`
	RequiredEtaGain float64          `json:"requiredEtaGain"`
	PlannedEtaGain  float64          `json:"plannedEtaGain"`
	TotalCost       int              `json:"totalCost"`
	Actions         []coverageAction `json:"actions"`
	Unreachable     bool             `json:"unreachable,omitempty"`
}

// criticalFields defines the fields checked for actor metadata completeness.
// Each field has a weight contributing to the coverage score (total 1.0).
//
// ADR-0049 §M1: `wit_imports` removed from the scoring set (WIT bindgen is
// a dead path; AT Lexicon JSON at 00-contracts/lexicons/ is the surviving
// contract). Its 0.25 share is redistributed proportionally across the
// remaining four fields. The `WitImports` JSON field on actorCoverageRow
// is retained for downstream shape compatibility but is no longer
// inspected by the scoring loop.
var criticalFields = []struct {
	Name   string
	Weight float64
}{
	{"convo_system_prompt", 0.33}, // 0.25 + 0.08 (share of retired wit_imports)
	{"capabilities", 0.27},        // 0.20 + 0.07
	{"performer_type", 0.20},      // 0.15 + 0.05
	{"operator", 0.20},            // 0.15 + 0.05
}

func runCoverageActors(args []string) error {
	if len(args) > 0 {
		switch args[0] {
		case "list":
			return runCoverageActorsList(args[1:])
		case "eta":
			return runCoverageActorsEta(args[1:])
		case "inspect":
			return runCoverageActorsInspect(args[1:])
		case "path", "plan":
			return runCoverageActorsPath(args[1:])
		case "heal":
			return runCoverageActorsHeal(args[1:])
		case "standardize":
			return runCoverageActorsStandardize(args[1:])
		case "help", "--help", "-h":
			printCoverageActorsUsage()
			return nil
		}
	}
	// Default: eta summary
	return runCoverageActorsEta(args)
}

func printCoverageActorsUsage() {
	fmt.Println(`Usage: gftd coverage actors <subcommand> [flags]

Subcommands:
  list      Show per-actor coverage scores (--grade, --limit)
  eta       Show system-wide η metric (default)
  inspect   Show missing fields for a specific actor (--did)
  path      Solve coverage improvement as a shortest-path problem
  heal      Trigger healing for worst N actors (--limit, --dry-run, --murakumo)
  standardize  Enforce standard shinka/koji/kyumei/domain-knowledge rule on actors

Flags (list):
  --grade   Filter by grade: critical, incomplete, complete
  --limit   Max actors to display (default: 20)
  --json    JSON output

Flags (heal):
  --limit       Max actors to heal (default: 10)
  --dry-run     Generate fixes but don't write to graph
  --murakumo    Use Murakumo LLM (default: true)
  --concurrency Parallel healing (default: 4)
  --json        JSON output

Flags (path):
  --target-eta  Target η to reach (default: 1.0)
  --budget      Optional max total action cost
  --limit       Max candidate actions to consider (default: all)
  --json        JSON output`)
}

var standardRuleLoops = []string{"shinka", "koji", "kyumei", "domain-knowledge"}

var standardRuleCollections = []string{
	"ai.gftd.apps.standard.shinkaEvolution",
	"ai.gftd.apps.standard.shinkaKnowledge",
}

var standardRuleDocs = []string{
	"90-docs/rules/compliance/per-did-kyumei-shinka-autonomy.md",
	"90-docs/platform/260403-live-data-kyumei-shinka-consolidated.md",
}

// runCoverageActorsEta shows system-wide η metric.
func runCoverageActorsEta(args []string) error {
	fs := flag.NewFlagSet("coverage actors eta", flag.ContinueOnError)
	pdsURL := fs.String("pds", envOr("GFTD_PDS_URL", defaultPDSURL), "PDS base URL")
	jsonOut := fs.Bool("json", false, "JSON output")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	actors, err := fetchActorCoverage(*pdsURL, 0, "")
	if err != nil {
		return err
	}

	report := buildCoverageReport(actors, false)

	if *jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(report)
	}

	fmt.Println("Actor Metadata Coverage (η)")
	fmt.Printf("  evaluated_at: %s\n", report.EvaluatedAt)
	fmt.Printf("  source:       graph-sql\n")
	fmt.Printf("  total_actors: %d\n", report.TotalActors)
	fmt.Printf("  η:            %.4f\n", report.Eta)
	fmt.Println()
	fmt.Printf("  Grades:\n")
	fmt.Printf("    critical:   %d\n", report.Critical)
	fmt.Printf("    incomplete: %d\n", report.Incomplete)
	fmt.Printf("    complete:   %d\n", report.Complete)
	fmt.Println()

	// Progress bar
	pct := report.Eta * 100
	barLen := 40
	filled := int(pct / 100 * float64(barLen))
	if filled > barLen {
		filled = barLen
	}
	fmt.Printf("  [%s%s] %.1f%%\n",
		strings.Repeat("█", filled),
		strings.Repeat("░", barLen-filled),
		pct)

	if report.Critical > 0 {
		fmt.Printf("\n  ⚠ %d critical actors need immediate healing (run: gftd coverage actors heal)\n", report.Critical)
	}
	return nil
}

// runCoverageActorsList shows per-actor coverage scores.
func runCoverageActorsList(args []string) error {
	fs := flag.NewFlagSet("coverage actors list", flag.ContinueOnError)
	pdsURL := fs.String("pds", envOr("GFTD_PDS_URL", defaultPDSURL), "PDS base URL")
	grade := fs.String("grade", "", "filter by grade: critical, incomplete, complete")
	limit := fs.Int("limit", 20, "max actors to display")
	jsonOut := fs.Bool("json", false, "JSON output")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	actors, err := fetchActorCoverage(*pdsURL, *limit, *grade)
	if err != nil {
		return err
	}

	report := buildCoverageReport(actors, true)

	if *jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(report)
	}

	fmt.Printf("Actor Coverage List (η=%.4f, %d total, showing %d)\n\n",
		report.Eta, report.TotalActors, len(report.Actors))
	fmt.Printf("%-30s %-10s %6s  %s\n", "DID", "GRADE", "SCORE", "MISSING")
	fmt.Printf("%-30s %-10s %6s  %s\n",
		strings.Repeat("─", 30), strings.Repeat("─", 10), strings.Repeat("─", 6), strings.Repeat("─", 30))

	for _, a := range report.Actors {
		did := a.DID
		if len(did) > 30 {
			did = did[:27] + "..."
		}
		missing := strings.Join(a.MissingFields, ", ")
		if missing == "" {
			missing = "-"
		}
		fmt.Printf("%-30s %-10s %5.3f  %s\n", did, a.Grade, a.CoverageScore, missing)
	}
	return nil
}

// runCoverageActorsInspect shows missing fields for a specific actor.
func runCoverageActorsInspect(args []string) error {
	fs := flag.NewFlagSet("coverage actors inspect", flag.ContinueOnError)
	pdsURL := fs.String("pds", envOr("GFTD_PDS_URL", defaultPDSURL), "PDS base URL")
	did := fs.String("did", "", "actor DID to inspect (required)")
	jsonOut := fs.Bool("json", false, "JSON output")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	targetDID := *did
	if targetDID == "" && fs.NArg() > 0 {
		targetDID = fs.Arg(0)
	}
	if targetDID == "" {
		return fmt.Errorf("--did is required (or pass DID as argument)")
	}

	actors, err := fetchActorCoverageByDID(*pdsURL, targetDID)
	if err != nil || len(actors) == 0 {
		// Fallback to local manifest scan
		fmt.Fprintf(os.Stderr, "graph query failed, trying local scan...\n")
		localActors, localErr := fetchActorCoverageLocal("")
		if localErr != nil {
			return fmt.Errorf("graph-query: %v, local: %v", err, localErr)
		}
		found := false
		for _, a := range localActors {
			if a.DID == targetDID {
				actors = []actorCoverageRow{a}
				found = true
				break
			}
		}
		if !found {
			return fmt.Errorf("actor not found: %s", targetDID)
		}
	}
	actor := actors[0]

	if *jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(actor)
	}

	fmt.Printf("Actor: %s\n", actor.DID)
	fmt.Printf("Name: %s\n", actor.Name)
	fmt.Printf("DisplayName: %s\n", actor.DisplayName)
	if actor.Runtime != "" {
		fmt.Printf("Runtime: %s\n", actor.Runtime)
	}
	if actor.Edge != "" {
		fmt.Printf("Edge: %s\n", actor.Edge)
	}
	if actor.LegacyTier != "" {
		fmt.Printf("LegacyExecutionTier: %s\n", actor.LegacyTier)
	}
	fmt.Printf("Grade: %s\n", actor.Grade)
	fmt.Printf("Score: %.3f\n\n", actor.CoverageScore)

	fmt.Println("Fields:")
	for _, f := range coverageFieldsForActor(actor) {
		val := getActorField(actor, f.Name)
		status := "OK"
		if val == "" {
			status = "MISSING"
		}
		fmt.Printf("  %-25s [%.0f%%]  %s\n", f.Name, f.Weight*100, status)
		if val != "" && len(val) > 80 {
			val = val[:77] + "..."
		}
		if val != "" {
			fmt.Printf("    → %s\n", val)
		}
	}

	if len(actor.MissingFields) > 0 {
		fmt.Printf("\nMissing: %s\n", strings.Join(actor.MissingFields, ", "))
		fmt.Printf("Run: gftd coverage actors heal --did %s\n", actor.DID)
	}
	return nil
}

// runCoverageActorsHeal triggers healing for the worst N actors via Murakumo LLM.
func runCoverageActorsHeal(args []string) error {
	fs := flag.NewFlagSet("coverage actors heal", flag.ContinueOnError)
	pdsURL := fs.String("pds", envOr("GFTD_PDS_URL", defaultPDSURL), "PDS base URL")
	limit := fs.Int("limit", 10, "max actors to heal per cycle")
	dryRun := fs.Bool("dry-run", false, "generate fixes but don't write")
	useMurakumo := fs.Bool("murakumo", true, "use Murakumo LLM")
	murakumoURL := fs.String("murakumo-url", envOr("GFTD_MURAKUMO", murakumoEndpoint), "Murakumo API base URL")
	model := fs.String("model", envOr("GFTD_SHINKA_MODEL", "qwen3-30b-a3b"), "LLM model")
	concurrency := fs.Int("concurrency", 4, "parallel healing")
	filterDID := fs.String("did", "", "heal specific actor DID only")
	jsonOut := fs.Bool("json", false, "JSON output")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	// Fetch actors needing healing
	var actors []actorCoverageRow
	var err error
	if *filterDID != "" {
		// Single actor mode
		actors, err = fetchActorCoverageByDID(*pdsURL, *filterDID)
	} else {
		actors, err = fetchActorCoverage(*pdsURL, *limit, "")
	}
	if err != nil {
		return err
	}

	// Filter to actors with missing fields
	var needsHealing []actorCoverageRow
	for _, a := range actors {
		if len(a.MissingFields) > 0 {
			needsHealing = append(needsHealing, a)
		}
	}
	if len(needsHealing) > *limit {
		needsHealing = needsHealing[:*limit]
	}

	if len(needsHealing) == 0 {
		fmt.Println("All actors complete — no healing needed (η=1.0)")
		return nil
	}

	// Select LLM backend
	var llmGenerate func(prompt string) (string, error)
	if *useMurakumo {
		apiKey := envOr("MURAKUMO_API_KEY", murakumoAPIKey)
		if err := checkMurakumo(*murakumoURL, apiKey); err != nil {
			fmt.Fprintf(os.Stderr, "warn: murakumo not ready (%v), using deterministic fallback\n", err)
			llmGenerate = nil
		} else {
			llmGenerate = func(prompt string) (string, error) {
				return murakumoGenerate(*murakumoURL, apiKey, *model, prompt)
			}
			fmt.Fprintf(os.Stderr, "Healing %d actors via Murakumo (%s) model=%s\n", len(needsHealing), *murakumoURL, *model)
		}
	} else {
		fmt.Fprintf(os.Stderr, "Healing %d actors via deterministic fallback (Murakumo disabled)\n", len(needsHealing))
		llmGenerate = nil
	}

	// Process actors in parallel
	results := make([]actorHealResult, len(needsHealing))
	var healedCount int64
	var wg sync.WaitGroup
	sem := make(chan struct{}, *concurrency)

	for i, actor := range needsHealing {
		wg.Add(1)
		sem <- struct{}{}
		go func(idx int, a actorCoverageRow) {
			defer wg.Done()
			defer func() { <-sem }()

			result := healActor(llmGenerate, a)
			results[idx] = result

			if !*dryRun && result.Error == "" && len(result.FixedFields) > 0 {
				if err := writeHealResult(*pdsURL, a, result); err != nil {
					result.Error = err.Error()
				}
			}

			n := atomic.AddInt64(&healedCount, 1)
			if !*jsonOut {
				fmt.Fprintf(os.Stderr, "\r[%d/%d] %s — fixed: %s",
					n, len(needsHealing), a.Name, strings.Join(result.FixedFields, ", "))
			}
		}(i, actor)
	}
	wg.Wait()

	if !*jsonOut {
		fmt.Fprintln(os.Stderr)
	}

	report := actorHealReport{
		EvaluatedAt: time.Now().UTC().Format(time.RFC3339),
		DryRun:      *dryRun,
		Results:     results,
	}
	for _, r := range results {
		if r.Error == "" && len(r.FixedFields) > 0 {
			report.HealedCount++
		}
	}

	if *jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(report)
	}

	fmt.Printf("\nHealing complete: %d/%d actors healed\n", report.HealedCount, len(needsHealing))
	if *dryRun {
		fmt.Println("(dry-run — nothing written)")
	}
	for _, r := range results {
		if r.Error != "" {
			fmt.Printf("  ERROR %s: %s\n", r.DID, r.Error)
		} else if len(r.FixedFields) > 0 {
			fmt.Printf("  OK    %s: %s\n", r.DID, strings.Join(r.FixedFields, ", "))
		}
	}
	return nil
}

func runCoverageActorsStandardize(args []string) error {
	fs := flag.NewFlagSet("coverage actors standardize", flag.ContinueOnError)
	pdsURL := fs.String("pds", envOr("GFTD_PDS_URL", defaultPDSURL), "PDS base URL")
	limit := fs.Int("limit", 0, "max actors to standardize (0=all)")
	dryRun := fs.Bool("dry-run", false, "generate fixes but don't write")
	registerLive := fs.Bool("register-live", false, "re-register updated actor manifests to PDS via ai.gftd.actor.registerManifest")
	useMurakumo := fs.Bool("murakumo", true, "use Murakumo LLM for missing metadata")
	murakumoURL := fs.String("murakumo-url", envOr("GFTD_MURAKUMO", murakumoEndpoint), "Murakumo API base URL")
	model := fs.String("model", envOr("GFTD_SHINKA_MODEL", "qwen3-30b-a3b"), "LLM model")
	concurrency := fs.Int("concurrency", 4, "parallel standardization")
	filterDID := fs.String("did", "", "standardize specific actor DID only")
	jsonOut := fs.Bool("json", false, "JSON output")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	var actors []actorCoverageRow
	var err error
	if *filterDID != "" {
		actors, err = fetchActorCoverageByDID(*pdsURL, *filterDID)
	} else {
		actors, err = fetchActorCoverage(*pdsURL, *limit, "")
	}
	if err != nil {
		return err
	}
	if len(actors) == 0 {
		fmt.Println("No actors found to standardize.")
		return nil
	}

	var llmGenerate func(prompt string) (string, error)
	if *useMurakumo {
		apiKey := envOr("MURAKUMO_API_KEY", murakumoAPIKey)
		if err := checkMurakumo(*murakumoURL, apiKey); err != nil {
			fmt.Fprintf(os.Stderr, "warn: murakumo not ready (%v), using deterministic fallback\n", err)
			llmGenerate = nil
		} else {
			llmGenerate = func(prompt string) (string, error) {
				return murakumoGenerate(*murakumoURL, apiKey, *model, prompt)
			}
		}
	} else {
		llmGenerate = nil
	}
	if *registerLive && !*dryRun && resolveGFTDToken() == "" {
		return fmt.Errorf("--register-live requires auth token — run: gftd auth login")
	}

	results := make([]actorHealResult, len(actors))
	var standardized int64
	var wg sync.WaitGroup
	sem := make(chan struct{}, *concurrency)

	for i, actor := range actors {
		wg.Add(1)
		sem <- struct{}{}
		go func(idx int, a actorCoverageRow) {
			defer wg.Done()
			defer func() { <-sem }()

			result := healActor(llmGenerate, a)
			applyStandardRule(&result, a)
			results[idx] = result

			if !*dryRun && result.Error == "" && len(result.FixedFields) > 0 {
				if err := writeHealResult(*pdsURL, a, result); err != nil {
					result.Error = err.Error()
					results[idx] = result
				} else if *registerLive {
					if manifestPath, err := resolveActorManifestPath(a); err != nil {
						result.Error = err.Error()
						results[idx] = result
					} else if manifestPath != "" {
						if err := registerActorManifest(*pdsURL, manifestPath); err != nil {
							result.Error = err.Error()
							results[idx] = result
						}
					}
				}
			}

			n := atomic.AddInt64(&standardized, 1)
			if !*jsonOut {
				fmt.Fprintf(os.Stderr, "\r[%d/%d] %s — standardized: %s",
					n, len(actors), a.Name, strings.Join(result.FixedFields, ", "))
			}
		}(i, actor)
	}
	wg.Wait()

	if !*jsonOut {
		fmt.Fprintln(os.Stderr)
	}

	report := actorHealReport{
		EvaluatedAt: time.Now().UTC().Format(time.RFC3339),
		DryRun:      *dryRun,
		Results:     results,
	}
	for _, r := range results {
		if r.Error == "" && len(r.FixedFields) > 0 {
			report.HealedCount++
		}
	}

	if *jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(report)
	}

	fmt.Printf("\nStandardization complete: %d/%d actors updated\n", report.HealedCount, len(actors))
	if *dryRun {
		fmt.Println("(dry-run — nothing written)")
	}
	for _, r := range results {
		if r.Error != "" {
			fmt.Printf("  ERROR %s: %s\n", r.DID, r.Error)
		} else {
			fmt.Printf("  OK    %s: %s\n", r.DID, strings.Join(r.FixedFields, ", "))
		}
	}
	return nil
}

func runCoverageActorsPath(args []string) error {
	fs := flag.NewFlagSet("coverage actors path", flag.ContinueOnError)
	pdsURL := fs.String("pds", envOr("GFTD_PDS_URL", defaultPDSURL), "PDS base URL")
	targetEta := fs.Float64("target-eta", 1.0, "target η to reach")
	budget := fs.Int("budget", 0, "optional max total action cost")
	limit := fs.Int("limit", 0, "max candidate actions to consider (0=all)")
	jsonOut := fs.Bool("json", false, "JSON output")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	actors, err := fetchActorCoverage(*pdsURL, 0, "")
	if err != nil {
		return err
	}
	report := buildCoverageReport(actors, false)
	path := solveCoveragePath(actors, report.Eta, *targetEta, *budget, *limit)

	if *jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(path)
	}

	fmt.Println("Actor Coverage Path")
	fmt.Printf("  current_eta:   %.4f\n", path.CurrentEta)
	fmt.Printf("  target_eta:    %.4f\n", path.TargetEta)
	fmt.Printf("  reached_eta:   %.4f\n", path.ReachedEta)
	fmt.Printf("  required_gain: %.4f\n", path.RequiredEtaGain)
	fmt.Printf("  planned_gain:  %.4f\n", path.PlannedEtaGain)
	fmt.Printf("  total_cost:    %d\n", path.TotalCost)
	if path.Unreachable {
		fmt.Printf("  status:        target unreachable with current candidates\n")
	} else {
		fmt.Printf("  status:        path found\n")
	}
	fmt.Println()
	if len(path.Actions) == 0 {
		fmt.Println("No actions needed.")
		return nil
	}

	fmt.Printf("%-3s %-24s %-16s %-20s %-8s %-6s %s\n", "#", "ACTOR", "RUNTIME", "FIELD", "ETA+", "COST", "DETAIL")
	for i, a := range path.Actions {
		fmt.Printf("%-3d %-24s %-16s %-20s %-8.4f %-6d %.3f -> %.3f\n",
			i+1, truncStr(a.ActorName, 24), a.Runtime, a.Field, a.EtaGain, a.Cost, a.CurrentScore, a.NextScore)
	}
	return nil
}

// fetchActorCoverage queries the graph query layer for actors sorted by coverage score ascending.
// Uses lightweight columns (no large text blobs) to avoid RisingWave OOM.
// Paginates in batches of 200 to stay within memory limits.
func fetchActorCoverage(pdsURL string, limit int, gradeFilter string) ([]actorCoverageRow, error) {
	// Try graph query first, fallback to local manifest scan on OOM/error.
	actors, err := fetchActorCoverageKagami(pdsURL, gradeFilter)
	if err != nil {
		fmt.Fprintf(os.Stderr, "graph query failed (%v), falling back to local manifest scan...\n", err)
		actors, err = fetchActorCoverageLocal(gradeFilter)
		if err != nil {
			return nil, err
		}
	}

	// Sort by coverage score ascending (worst first)
	sort.Slice(actors, func(i, j int) bool {
		return actors[i].CoverageScore < actors[j].CoverageScore
	})

	if limit > 0 && len(actors) > limit {
		actors = actors[:limit]
	}

	return actors, nil
}

// fetchActorCoverageKagami queries RisingWave directly for actor metadata.
func fetchActorCoverageKagami(pdsURL string, gradeFilter string) ([]actorCoverageRow, error) {
	_ = pdsURL
	ctx, cancel := context.WithTimeout(context.Background(), 90*time.Second)
	defer cancel()

	// Step 1: Query ActorConvoPrompt for convo_system_prompt presence.
	hasPrompt := make(map[string]bool)
	promptSQL := `SELECT actor_did AS did FROM vertex_actor_convo_prompt WHERE convo_system_prompt IS NOT NULL AND convo_system_prompt <> '' LIMIT 2000`
	if promptResp, err := db.RawQuery(ctx, promptSQL); err != nil {
		fmt.Fprintf(os.Stderr, "warn: ActorConvoPrompt query failed (%v), will mark convo_system_prompt as missing\n", err)
	} else {
		for _, row := range promptResp.Rows {
			if d := anyStr(row["did"]); d != "" {
				hasPrompt[d] = true
			}
		}
	}

	// Step 2: Fetch Actor short metadata fields.
	var allActors []actorCoverageRow
	batchSize := 200
	for offset := 0; ; offset += batchSize {
		sqlStmt := fmt.Sprintf(
			`SELECT did, name, display_name, execution_tier AS legacy_execution_tier, 'k8s-langserver' AS runtime, 'sveltekit-proxy' AS edge, agent_tools::varchar AS wit_imports, capability_declare::varchar AS capabilities, performer_type, operator FROM vertex_actor WHERE did IS NOT NULL ORDER BY did OFFSET %d LIMIT %d`,
			offset, batchSize,
		)

		resp, err := db.RawQuery(ctx, sqlStmt)
		if err != nil {
			return nil, fmt.Errorf("risingwave query (offset %d): %w", offset, err)
		}
		if len(resp.Rows) == 0 {
			break
		}

		for _, row := range resp.Rows {
			did := anyStr(row["did"])
			if hasPrompt[did] {
				row["convo_system_prompt"] = "Y"
			}
			a := parseActorCoverageRow(row)
			if gradeFilter != "" && a.Grade != gradeFilter {
				continue
			}
			allActors = append(allActors, a)
		}

		if len(resp.Rows) < batchSize {
			break
		}
	}

	return allActors, nil
}

// fetchActorCoverageLocal scans local actor-manifest.jsonld files for coverage analysis.
func fetchActorCoverageLocal(gradeFilter string) ([]actorCoverageRow, error) {
	root, err := findGitRoot(".")
	if err != nil {
		return nil, err
	}

	// Scan 20-actors/*/actor-manifest.jsonld
	pattern := filepath.Join(root, "20-actors", "*", "actor-manifest.jsonld")
	matches, _ := filepath.Glob(pattern)

	var actors []actorCoverageRow
	for _, m := range matches {
		data, err := os.ReadFile(m)
		if err != nil {
			continue
		}
		var manifest struct {
			ID                string   `json:"@id"`
			Name              string   `json:"name"`
			DisplayName       string   `json:"displayName"`
			Description       string   `json:"description"`
			Runtime           string   `json:"runtime"`
			Edge              string   `json:"edge"`
			LegacyTier        string   `json:"legacyExecutionTier"`
			WitImports        []string `json:"witImports"`
			WitExports        []string `json:"witExports"`
			PerformerType     string   `json:"performerType"`
			Capabilities      []string `json:"capabilities"`
			ConvoSystemPrompt string   `json:"convoSystemPrompt"`
			Profile           struct {
				Operator string `json:"operator"`
			} `json:"profile"`
		}
		if err := json.Unmarshal(data, &manifest); err != nil || manifest.Name == "" {
			continue
		}

		row := map[string]any{
			"did":                   manifest.ID,
			"name":                  manifest.Name,
			"display_name":          manifest.DisplayName,
			"runtime":               manifest.Runtime,
			"edge":                  manifest.Edge,
			"legacy_execution_tier": manifest.LegacyTier,
		}
		if manifest.PerformerType != "" {
			row["performer_type"] = manifest.PerformerType
		}
		if len(manifest.WitImports) > 0 {
			b, _ := json.Marshal(manifest.WitImports)
			row["wit_imports"] = string(b)
		}
		if len(manifest.WitExports) > 0 {
			b, _ := json.Marshal(manifest.WitExports)
			row["wit_exports"] = string(b)
		}
		if len(manifest.Capabilities) > 0 {
			b, _ := json.Marshal(manifest.Capabilities)
			row["capabilities"] = string(b)
		}
		if manifest.ConvoSystemPrompt != "" {
			row["convo_system_prompt"] = manifest.ConvoSystemPrompt
		}
		if manifest.Profile.Operator != "" {
			row["operator"] = manifest.Profile.Operator
		}

		// Check for WIT world.wit in same directory
		dir := filepath.Dir(m)
		witPath := filepath.Join(dir, "wit", "world.wit")
		if _, statErr := os.Stat(witPath); statErr == nil && row["wit_imports"] == nil {
			row["wit_imports"] = "Y"
		}

		a := parseActorCoverageRow(row)
		a.ManifestPath = m
		if gradeFilter != "" && a.Grade != gradeFilter {
			continue
		}
		actors = append(actors, a)
	}

	fmt.Fprintf(os.Stderr, "local scan: found %d actors from actor-manifest.jsonld\n", len(actors))
	return actors, nil
}

// fetchActorCoverageByDID fetches a single actor's coverage by DID.
func fetchActorCoverageByDID(pdsURL string, did string) ([]actorCoverageRow, error) {
	_ = pdsURL
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	stmt := `SELECT did, name, display_name, classification AS description, execution_tier AS legacy_execution_tier, 'k8s-langserver' AS runtime, 'sveltekit-proxy' AS edge, agent_tools::varchar AS wit_imports, agent_invoke::varchar AS wit_exports, capability_declare::varchar AS capabilities, performer_type, operator FROM vertex_actor WHERE did = $1 LIMIT 1`
	resp, err := db.RawQuery(ctx, stmt, did)
	if err != nil {
		return nil, fmt.Errorf("risingwave query: %w", err)
	}

	// Check convo_system_prompt from split table.
	promptStmt := `SELECT actor_did AS did FROM vertex_actor_convo_prompt WHERE actor_did = $1 AND convo_system_prompt IS NOT NULL AND convo_system_prompt <> '' LIMIT 1`
	promptResp, _ := db.RawQuery(ctx, promptStmt, did)
	hasPrompt := promptResp != nil && len(promptResp.Rows) > 0

	var actors []actorCoverageRow
	for _, row := range resp.Rows {
		if hasPrompt {
			row["convo_system_prompt"] = "Y"
		}
		actors = append(actors, parseActorCoverageRow(row))
	}
	return actors, nil
}

// parseActorCoverageRow converts a graph query row to actorCoverageRow with score/grade.
func parseActorCoverageRow(row map[string]any) actorCoverageRow {
	a := actorCoverageRow{
		DID:               anyStr(row["did"]),
		Name:              anyStr(row["name"]),
		DisplayName:       anyStr(row["display_name"]),
		Description:       anyStr(row["description"]),
		Runtime:           actorCoverageRuntime(row),
		Edge:              anyStr(firstNonNil(row, "edge", "Edge")),
		LegacyTier:        anyStr(firstNonNil(row, "legacy_execution_tier", "legacyExecutionTier", "execution_tier", "executionTier")),
		WitImports:        anyStr(row["wit_imports"]),
		WitExports:        anyStr(row["wit_exports"]),
		ConvoSystemPrompt: anyStr(row["convo_system_prompt"]),
		Capabilities:      anyStr(row["capabilities"]),
		PerformerType:     anyStr(row["performer_type"]),
		Operator:          anyStr(row["operator"]),
	}

	// Calculate coverage score and missing fields.
	// Normalize by applicable field weights so migrated actors can still reach 1.0
	// when WIT imports are intentionally not required.
	fields := coverageFieldsForActor(a)
	var score float64
	var totalWeight float64
	for _, f := range fields {
		totalWeight += f.Weight
		val := getActorField(a, f.Name)
		if val != "" && val != "[]" && val != "null" {
			score += f.Weight
		} else {
			a.MissingFields = append(a.MissingFields, f.Name)
		}
	}
	if totalWeight > 0 {
		a.CoverageScore = score / totalWeight
	}

	// Grade assignment
	switch {
	case len(a.MissingFields) >= 3:
		a.Grade = "critical"
	case len(a.MissingFields) >= 1:
		a.Grade = "incomplete"
	default:
		a.Grade = "complete"
	}

	return a
}

func actorCoverageRuntime(row map[string]any) string {
	runtime := anyStr(firstNonNil(row, "runtime", "Runtime"))
	if runtime != "" {
		return runtime
	}
	if legacy := anyStr(firstNonNil(row, "legacy_execution_tier", "legacyExecutionTier", "execution_tier", "executionTier")); legacy != "" {
		return "legacy-" + legacy
	}
	return ""
}

// coverageFieldsForActor returns the scoring fields for one actor.
//
// ADR-0049 §M1: previously this function conditionally included
// `wit_imports` for legacy actor classes via `actorRequiresWITImports`. WIT
// bindgen is now a dead path, so every actor (all tiers) uses the same
// four-field set defined on `criticalFields`.
func coverageFieldsForActor(_ actorCoverageRow) []struct {
	Name   string
	Weight float64
} {
	return criticalFields
}

// actorRequiresWITImports is retained as a stub returning false so
// pre-ADR-0049 call sites in healActor + fallbackCapabilities keep
// compiling while their WIT branches become unreachable dead code.
// Remove once those call sites are deleted in a follow-up cleanup PR.
func actorRequiresWITImports(_ actorCoverageRow) bool {
	return false
}

// getActorField returns the field value by name from an actorCoverageRow.
func getActorField(a actorCoverageRow, field string) string {
	switch field {
	case "wit_imports":
		return a.WitImports
	case "wit_exports":
		return a.WitExports
	case "convo_system_prompt":
		return a.ConvoSystemPrompt
	case "capabilities":
		return a.Capabilities
	case "performer_type":
		return a.PerformerType
	case "operator":
		return a.Operator
	default:
		return ""
	}
}

// buildCoverageReport aggregates actor coverage into a report.
func buildCoverageReport(actors []actorCoverageRow, includeActors bool) actorCoverageReport {
	report := actorCoverageReport{
		EvaluatedAt: time.Now().UTC().Format(time.RFC3339),
		Source:      "graph-sql",
	}

	// Count all actors (need total for η, not just filtered)
	var totalScore float64
	for _, a := range actors {
		totalScore += a.CoverageScore
		switch a.Grade {
		case "critical":
			report.Critical++
		case "incomplete":
			report.Incomplete++
		case "complete":
			report.Complete++
		}
	}

	report.TotalActors = len(actors)
	if report.TotalActors > 0 {
		report.Eta = totalScore / float64(report.TotalActors)
	}

	if includeActors {
		report.Actors = actors
	}

	return report
}

func solveCoveragePath(actors []actorCoverageRow, currentEta, targetEta float64, budget, limit int) coveragePathReport {
	path := coveragePathReport{
		EvaluatedAt:     time.Now().UTC().Format(time.RFC3339),
		Source:          "coverage_actors",
		CurrentEta:      currentEta,
		TargetEta:       targetEta,
		ReachedEta:      currentEta,
		RequiredEtaGain: maxFloat(0, targetEta-currentEta),
	}
	if targetEta <= currentEta {
		return path
	}

	actions := enumerateCoverageActions(actors)
	if len(actions) == 0 {
		path.Unreachable = true
		return path
	}
	sort.Slice(actions, func(i, j int) bool {
		if actions[i].CostPerEtaGain != actions[j].CostPerEtaGain {
			return actions[i].CostPerEtaGain < actions[j].CostPerEtaGain
		}
		return actions[i].EtaGain > actions[j].EtaGain
	})
	if limit > 0 && len(actions) > limit {
		actions = actions[:limit]
	}

	const etaScale = 10000
	requiredUnits := int(math.Ceil(path.RequiredEtaGain * etaScale))
	maxGainUnits := 0
	gainUnits := make([]int, len(actions))
	for i, a := range actions {
		u := int(math.Round(a.EtaGain * etaScale))
		if u < 1 {
			u = 1
		}
		gainUnits[i] = u
		maxGainUnits += u
	}
	if requiredUnits > maxGainUnits {
		requiredUnits = maxGainUnits
		path.Unreachable = true
	}

	const infCost = int(^uint(0) >> 1)
	dp := make([]int, maxGainUnits+1)
	prevGain := make([]int, maxGainUnits+1)
	prevAction := make([]int, maxGainUnits+1)
	for i := range dp {
		dp[i] = infCost
		prevGain[i] = -1
		prevAction[i] = -1
	}
	dp[0] = 0
	for i, action := range actions {
		g := gainUnits[i]
		for gain := maxGainUnits - g; gain >= 0; gain-- {
			if dp[gain] == infCost {
				continue
			}
			nextGain := gain + g
			nextCost := dp[gain] + action.Cost
			if nextCost < dp[nextGain] {
				dp[nextGain] = nextCost
				prevGain[nextGain] = gain
				prevAction[nextGain] = i
			}
		}
	}

	bestGain := -1
	bestCost := infCost
	for gain := requiredUnits; gain <= maxGainUnits; gain++ {
		if dp[gain] == infCost {
			continue
		}
		if budget > 0 && dp[gain] > budget {
			continue
		}
		if dp[gain] < bestCost {
			bestCost = dp[gain]
			bestGain = gain
		}
	}
	if bestGain < 0 {
		path.Unreachable = true
		bestGain = 0
		bestCost = 0
		if budget > 0 {
			for gain := 0; gain <= maxGainUnits; gain++ {
				if dp[gain] != infCost && dp[gain] <= budget && gain > bestGain {
					bestGain = gain
					bestCost = dp[gain]
				}
			}
		}
	}

	for gain := bestGain; gain > 0; {
		actionIdx := prevAction[gain]
		if actionIdx < 0 {
			break
		}
		path.Actions = append(path.Actions, actions[actionIdx])
		gain = prevGain[gain]
	}
	for i, j := 0, len(path.Actions)-1; i < j; i, j = i+1, j-1 {
		path.Actions[i], path.Actions[j] = path.Actions[j], path.Actions[i]
	}
	path.TotalCost = bestCost
	for _, a := range path.Actions {
		path.PlannedEtaGain += a.EtaGain
	}
	path.ReachedEta = minFloat(1.0, path.CurrentEta+path.PlannedEtaGain)
	return path
}

func enumerateCoverageActions(actors []actorCoverageRow) []coverageAction {
	totalActors := len(actors)
	if totalActors == 0 {
		return nil
	}
	actions := make([]coverageAction, 0)
	for _, actor := range actors {
		fields := coverageFieldsForActor(actor)
		totalWeight := 0.0
		weights := make(map[string]float64, len(fields))
		for _, f := range fields {
			totalWeight += f.Weight
			weights[f.Name] = f.Weight
		}
		if totalWeight == 0 {
			continue
		}
		for _, field := range actor.MissingFields {
			weight, ok := weights[field]
			if !ok {
				continue
			}
			current := actor.CoverageScore
			next := minFloat(1.0, current+weight/totalWeight)
			gain := (next - current) / float64(totalActors)
			cost := coverageFieldCost(field)
			actions = append(actions, coverageAction{
				ActorDID:       actor.DID,
				ActorName:      actor.Name,
				Runtime:        actor.Runtime,
				Field:          field,
				CurrentScore:   current,
				NextScore:      next,
				EtaGain:        gain,
				Cost:           cost,
				CostPerEtaGain: float64(cost) / gain,
			})
		}
	}
	return actions
}

func coverageFieldCost(field string) int {
	switch field {
	case "operator", "performer_type":
		return 1
	case "wit_imports":
		return 2
	case "convo_system_prompt":
		return 3
	case "capabilities":
		return 4
	default:
		return 3
	}
}

func minFloat(a, b float64) float64 {
	if a < b {
		return a
	}
	return b
}

func maxFloat(a, b float64) float64 {
	if a > b {
		return a
	}
	return b
}

// healActor generates fixes for missing fields using Murakumo LLM.
func healActor(llmGenerate func(string) (string, error), actor actorCoverageRow) actorHealResult {
	result := actorHealResult{
		DID:             actor.DID,
		Name:            actor.Name,
		GeneratedValues: make(map[string]string),
	}

	for _, field := range actor.MissingFields {
		var fix string
		var err error

		switch field {
		case "convo_system_prompt":
			fix, err = healConvoPrompt(llmGenerate, actor)
		case "wit_imports":
			if actorRequiresWITImports(actor) {
				fix, err = healWitImports(actor)
			}
		case "capabilities":
			fix, err = healCapabilities(llmGenerate, actor)
		case "performer_type":
			fix = "service"
		case "operator":
			fix = "amanomibashira"
		}

		if err != nil {
			result.Error = fmt.Sprintf("%s: %v", field, err)
			return result
		}
		if fix != "" {
			result.FixedFields = append(result.FixedFields, field)
			result.GeneratedValues[field] = fix
		}
	}

	return result
}

func applyStandardRule(result *actorHealResult, actor actorCoverageRow) {
	addStandardField := func(field, value string) {
		if value == "" {
			return
		}
		if result.GeneratedValues == nil {
			result.GeneratedValues = make(map[string]string)
		}
		result.GeneratedValues[field] = value
		for _, existing := range result.FixedFields {
			if existing == field {
				return
			}
		}
		result.FixedFields = append(result.FixedFields, field)
	}

	addStandardField("standard_rule", "per-did-kyumei-shinka-autonomy@2026-04-13")
	addStandardField("standard_status", "required")
	addStandardField("required_loops", coverageToJSON(standardRuleLoops))
	addStandardField("required_collections", coverageToJSON(standardRuleCollections))
	addStandardField("compliance_docs", coverageToJSON(standardRuleDocs))
	addStandardField("heartbeat_required", "true")
	addStandardField("domain_knowledge_required", "true")

	if actor.ConvoSystemPrompt == "" {
		addStandardField("convo_system_prompt", result.GeneratedValues["convo_system_prompt"])
	}
	if actor.Capabilities == "" {
		addStandardField("capabilities", result.GeneratedValues["capabilities"])
	}
	if actor.PerformerType == "" {
		addStandardField("performer_type", "service")
	}
	if actor.Operator == "" {
		addStandardField("operator", "amanomibashira")
	}
}

// healConvoPrompt generates a convo system prompt via LLM.
func healConvoPrompt(llmGenerate func(string) (string, error), actor actorCoverageRow) (string, error) {
	if llmGenerate == nil {
		return fallbackConvoPrompt(actor), nil
	}
	prompt := fmt.Sprintf(`Generate a concise system prompt (2-4 sentences, Japanese) for an AI actor on etzhayyim.com platform.

Actor: %s
DisplayName: %s
Description: %s

The prompt should:
1. Define the actor's role and expertise
2. Specify how it should respond to DM conversations
3. Be written in Japanese

Output ONLY the system prompt text, no JSON, no markdown fences.`, actor.Name, actor.DisplayName, actor.Description)

	resp, err := llmGenerate(prompt)
	if err != nil {
		return fallbackConvoPrompt(actor), nil
	}
	return strings.TrimSpace(resp), nil
}

// healWitImports returns default WIT imports based on actor metadata.
func healWitImports(actor actorCoverageRow) (string, error) {
	imports := []string{
		"magatama:governance/governance",
		"magatama:identity/capability",
		"magatama:agent/agent",
	}
	return coverageToJSON(imports), nil
}

// healCapabilities generates capabilities via LLM.
func healCapabilities(llmGenerate func(string) (string, error), actor actorCoverageRow) (string, error) {
	if llmGenerate == nil {
		return fallbackCapabilities(actor), nil
	}
	prompt := fmt.Sprintf(`List the MCP capabilities for an AI actor. Output ONLY a JSON array of capability strings.

Actor: %s
DisplayName: %s
Description: %s

Available capabilities: graph.query, graph.write, agent.chat, agent.invoke, browser.fetch, derive:social

Example: ["graph.query", "graph.write", "agent.chat"]

Output ONLY the JSON array:`, actor.Name, actor.DisplayName, actor.Description)

	resp, err := llmGenerate(prompt)
	if err != nil {
		return fallbackCapabilities(actor), nil
	}

	// Extract JSON array
	resp = strings.TrimSpace(resp)
	start := strings.Index(resp, "[")
	end := strings.LastIndex(resp, "]")
	if start >= 0 && end > start {
		return resp[start : end+1], nil
	}
	// Fallback
	return fallbackCapabilities(actor), nil
}

func fallbackConvoPrompt(actor actorCoverageRow) string {
	name := strings.TrimSpace(actor.DisplayName)
	if name == "" {
		name = strings.TrimSpace(actor.Name)
	}
	desc := strings.TrimSpace(actor.Description)
	if desc == "" {
		desc = "対象領域の情報を整理し、必要な文脈を短く返す"
	}
	return fmt.Sprintf("%s の担当エージェントです。%s。問い合わせには事実関係、依存関係、次の確認ポイントを簡潔に整理して日本語で答えてください。", name, desc)
}

func fallbackCapabilities(actor actorCoverageRow) string {
	base := []string{"graph.query", "agent.chat", "derive:social"}
	if actorRequiresWITImports(actor) {
		base = append(base, "graph.write")
	}
	return coverageToJSON(base)
}

// writeHealResult writes healing fixes back through the graph write path via PDS XRPC.
func writeHealResult(pdsURL string, actor actorCoverageRow, result actorHealResult) error {
	// Build SET clause from fixed fields
	sets := make(map[string]string)
	for _, field := range result.FixedFields {
		switch field {
		case "convo_system_prompt":
			if v, ok := result.GeneratedValues["convo_system_prompt"]; ok && v != "" {
				sets["convo_system_prompt"] = v
			}
		case "wit_imports":
			imports := []string{"magatama:governance/governance", "magatama:identity/capability", "magatama:agent/agent"}
			sets["wit_imports"] = coverageToJSON(imports)
			exports := []string{fmt.Sprintf("gftd:%s/service", actor.Name)}
			sets["wit_exports"] = coverageToJSON(exports)
		case "capabilities":
			if v, ok := result.GeneratedValues["capabilities"]; ok && v != "" {
				sets["capabilities"] = v
			} else {
				sets["capabilities"] = `["graph.query","graph.write","agent.chat"]`
			}
		case "performer_type":
			if v, ok := result.GeneratedValues["performer_type"]; ok && v != "" {
				sets["performer_type"] = v
			} else {
				sets["performer_type"] = "service"
			}
		case "operator":
			if v, ok := result.GeneratedValues["operator"]; ok && v != "" {
				sets["operator"] = v
			} else {
				sets["operator"] = "amanomibashira"
			}
		case "standard_rule", "standard_status", "required_loops", "required_collections", "compliance_docs", "heartbeat_required", "domain_knowledge_required":
			if v, ok := result.GeneratedValues[field]; ok && v != "" {
				sets[field] = v
			}
		}
	}

	if len(sets) == 0 {
		return nil
	}

	if manifestPath, err := resolveActorManifestPath(actor); err == nil && manifestPath != "" {
		return writeHealResultToLocalManifest(manifestPath, sets)
	}

	client := &http.Client{Timeout: 30 * time.Second}

	// convo_system_prompt: direct SQL UPSERT into vertex_actor_convo_prompt is
	// not supported on RisingWave (streaming DB, no OLTP merge). Per the
	// Write-Only Derived Architecture rule (root CLAUDE.md), writes must go
	// through PDS XRPC — leave the field in `sets` so the XRPC call below
	// picks it up with the other Actor fields.

	// Write remaining fields to Actor table via PDS XRPC.
	if len(sets) == 0 {
		return nil
	}
	payload := map[string]any{
		"did":    actor.DID,
		"fields": sets,
	}
	body, _ := json.Marshal(payload)
	req, err := http.NewRequest("POST", pdsURL+"/xrpc/ai.gftd.governance.updateActorFields", bytes.NewReader(body))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	setAuthHeaders(req)

	resp, err := client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode >= 400 {
		b, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("PDS %d: %s", resp.StatusCode, truncStr(string(b), 200))
	}
	return nil
}

func resolveActorManifestPath(actor actorCoverageRow) (string, error) {
	if strings.TrimSpace(actor.ManifestPath) != "" {
		return actor.ManifestPath, nil
	}

	root, err := findGitRoot(".")
	if err != nil {
		return "", err
	}
	pattern := filepath.Join(root, "20-actors", "*", "actor-manifest.jsonld")
	matches, err := filepath.Glob(pattern)
	if err != nil {
		return "", err
	}
	for _, m := range matches {
		data, err := os.ReadFile(m)
		if err != nil {
			continue
		}
		var manifest struct {
			ID string `json:"@id"`
		}
		if err := json.Unmarshal(data, &manifest); err != nil {
			continue
		}
		if manifest.ID == actor.DID {
			return m, nil
		}
	}
	return "", nil
}

func writeHealResultToLocalManifest(path string, sets map[string]string) error {
	data, err := os.ReadFile(path)
	if err != nil {
		return err
	}

	var manifest map[string]any
	if err := json.Unmarshal(data, &manifest); err != nil {
		return err
	}

	for field, value := range sets {
		switch field {
		case "convo_system_prompt":
			manifest["convoSystemPrompt"] = value
		case "wit_imports":
			manifest["witImports"] = parseJSONStringArray(value)
		case "wit_exports":
			manifest["witExports"] = parseJSONStringArray(value)
		case "capabilities":
			manifest["capabilities"] = parseJSONStringArray(value)
		case "performer_type":
			manifest["performerType"] = value
		case "operator":
			profile := nestedObject(manifest, "profile")
			profile["operator"] = value
			manifest["profile"] = profile
		case "standard_rule":
			manifest["standardRule"] = value
		case "standard_status":
			manifest["standardStatus"] = value
		case "required_loops":
			manifest["requiredLoops"] = parseJSONStringArray(value)
		case "required_collections":
			manifest["requiredCollections"] = parseJSONStringArray(value)
		case "compliance_docs":
			manifest["complianceDocs"] = parseJSONStringArray(value)
		case "heartbeat_required":
			manifest["heartbeatRequired"] = parseJSONBool(value)
		case "domain_knowledge_required":
			manifest["domainKnowledgeRequired"] = parseJSONBool(value)
		default:
			manifest[field] = value
		}
	}

	updated, err := json.MarshalIndent(manifest, "", "  ")
	if err != nil {
		return err
	}
	updated = append(updated, '\n')
	return os.WriteFile(path, updated, 0644)
}

func nestedObject(root map[string]any, key string) map[string]any {
	if v, ok := root[key]; ok {
		if obj, ok := v.(map[string]any); ok {
			return obj
		}
	}
	return map[string]any{}
}

func parseJSONStringArray(raw string) []string {
	var out []string
	if err := json.Unmarshal([]byte(raw), &out); err == nil {
		return out
	}
	if raw == "" {
		return nil
	}
	return []string{raw}
}

func parseJSONBool(raw string) bool {
	return strings.EqualFold(strings.TrimSpace(raw), "true")
}

func registerActorManifest(pdsURL string, manifestPath string) error {
	data, err := os.ReadFile(manifestPath)
	if err != nil {
		return err
	}
	req, err := http.NewRequest("POST", strings.TrimRight(pdsURL, "/")+"/xrpc/ai.gftd.actor.registerManifest", bytes.NewReader(data))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	setAuthHeaders(req)

	client := &http.Client{Timeout: 30 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 400 {
		b, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("registerManifest %d: %s", resp.StatusCode, truncStr(string(b), 200))
	}
	return nil
}

// coverageToJSON marshals a value to a JSON string.
func coverageToJSON(v any) string {
	b, _ := json.Marshal(v)
	return string(b)
}
