// gftd bonsai — Bonsai Growth & Prune Model (ADR-2605080100)
//
// Full-auto growth with human post-facto pruning.
// Three operations: prune (sporulate) / block (gate) / release.
// Canopy view shows the live organism shape with Shannon η scores.
package main

import (
	"bufio"
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"strings"
	"text/tabwriter"
	"time"

	gftddb "github.com/etzhayyim/root/70-tools/gftd/gftd/db"
)

// ── types ─────────────────────────────────────────────────────────────────────

type canopyNode struct {
	ActorDID        string  `json:"actor_did"`
	ParentDID       string  `json:"parent_did"`
	GrowthType      string  `json:"growth_type"`
	EtaAtBirth      float64 `json:"eta_at_birth"`
	GrowthAgeDays   float64 `json:"growth_age_days"`
	EtaNow          float64 `json:"eta_now"`
	ChildCount      int     `json:"child_count"`
	PruneStatus     string  `json:"prune_status"`
	RegrowthBlocked bool    `json:"regrowth_blocked"`
}

type growthEvent struct {
	ActorDID      string    `json:"actor_did"`
	ParentDID     string    `json:"parent_did"`
	TriggerSignal string    `json:"trigger_signal"`
	GrowthType    string    `json:"growth_type"`
	EtaAtBirth    float64   `json:"eta_at_birth"`
	CreatedAt     time.Time `json:"created_at"`
}

type pruneIntent struct {
	ActorDID        string    `json:"actor_did"`
	Status          string    `json:"status"`
	RegrowthBlocked bool      `json:"regrowth_blocked"`
	PrunedBy        string    `json:"pruned_by"`
	PrunedAt        time.Time `json:"pruned_at"`
}

// ── entry point ───────────────────────────────────────────────────────────────

func runBonsai(args []string) error {
	if len(args) == 0 {
		printBonsaiUsage()
		return nil
	}
	switch args[0] {
	case "canopy":
		return runBonsaiCanopy(args[1:])
	case "growth":
		return runBonsaiGrowth(args[1:])
	case "prune":
		return runBonsaiPrune(args[1:])
	case "release":
		return runBonsaiRelease(args[1:])
	case "status":
		return runBonsaiStatus(args[1:])
	case "help", "--help", "-h":
		printBonsaiUsage()
		return nil
	default:
		return fmt.Errorf("unknown bonsai subcommand %q\n\nRun 'gftd bonsai help' for usage", args[0])
	}
}

// ── canopy ────────────────────────────────────────────────────────────────────

func runBonsaiCanopy(args []string) error {
	fs := flag.NewFlagSet("bonsai canopy", flag.ExitOnError)
	jsonOut := fs.Bool("json", false, "JSON output")
	minEta := fs.Float64("min-eta", 0.0, "filter: only show actors with eta_now >= value")
	maxEta := fs.Float64("max-eta", 1.0, "filter: only show actors with eta_now <= value")
	status := fs.String("status", "", "filter by prune_status: alive|dormant|blocked")
	limit := fs.Int("limit", 100, "max rows")
	fs.Parse(args)

	ctx := context.Background()

	rows, err := gftddb.RawQuery(ctx, `
		SELECT
		  actor_did, parent_did, growth_type,
		  eta_at_birth, growth_age_days, eta_now,
		  child_count, prune_status, regrowth_blocked
		FROM mv_canopy_shape
		WHERE eta_now >= $1 AND eta_now <= $2
		ORDER BY eta_now ASC, growth_age_days DESC
		LIMIT $3
	`, *minEta, *maxEta, *limit)
	if err != nil {
		return fmt.Errorf("canopy query: %w\n\nhint: mv_canopy_shape may not exist yet — run `gftd database up` first", err)
	}

	nodes := make([]canopyNode, 0, len(rows.Rows))
	for _, r := range rows.Rows {
		n := canopyNode{
			ActorDID:        strVal(r["actor_did"]),
			ParentDID:       strVal(r["parent_did"]),
			GrowthType:      strVal(r["growth_type"]),
			EtaAtBirth:      floatVal(r["eta_at_birth"]),
			GrowthAgeDays:   floatVal(r["growth_age_days"]),
			EtaNow:          floatVal(r["eta_now"]),
			ChildCount:      intVal(r["child_count"]),
			PruneStatus:     strVal(r["prune_status"]),
			RegrowthBlocked: boolVal(r["regrowth_blocked"]),
		}
		if *status != "" && n.PruneStatus != *status {
			continue
		}
		nodes = append(nodes, n)
	}

	if *jsonOut {
		return json.NewEncoder(os.Stdout).Encode(nodes)
	}

	tw := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
	fmt.Fprintln(tw, "ACTOR_DID\tTYPE\tη_NOW\tη_BIRTH\tAGE_d\tCHILDREN\tSTATUS\tBLOCKED")
	for _, n := range nodes {
		blocked := ""
		if n.RegrowthBlocked {
			blocked = "🚫"
		}
		status := pruneStatusIcon(n.PruneStatus) + " " + n.PruneStatus
		fmt.Fprintf(tw, "%s\t%s\t%.2f\t%.2f\t%.0f\t%d\t%s\t%s\n",
			shortDID(n.ActorDID), n.GrowthType,
			n.EtaNow, n.EtaAtBirth, n.GrowthAgeDays,
			n.ChildCount, status, blocked,
		)
	}
	tw.Flush()
	fmt.Fprintf(os.Stderr, "\n%d actors  (min-eta=%.2f)\n", len(nodes), *minEta)
	return nil
}

// ── growth ────────────────────────────────────────────────────────────────────

func runBonsaiGrowth(args []string) error {
	fs := flag.NewFlagSet("bonsai growth", flag.ExitOnError)
	jsonOut := fs.Bool("json", false, "JSON output")
	limit := fs.Int("limit", 50, "max rows")
	growthType := fs.String("type", "", "filter: actor|table|mv|bpmn|udf")
	fs.Parse(args)

	ctx := context.Background()

	query := `
		SELECT actor_did, parent_did, trigger_signal, growth_type, eta_at_birth, created_at
		FROM vertex_growth_event
		ORDER BY created_at DESC
		LIMIT $1
	`
	qargs := []any{*limit}
	if *growthType != "" {
		query = `
			SELECT actor_did, parent_did, trigger_signal, growth_type, eta_at_birth, created_at
			FROM vertex_growth_event
			WHERE growth_type = $2
			ORDER BY created_at DESC
			LIMIT $1
		`
		qargs = append(qargs, *growthType)
	}

	rows, err := gftddb.RawQuery(ctx, query, qargs...)
	if err != nil {
		return fmt.Errorf("growth query: %w\n\nhint: vertex_growth_event may not exist yet", err)
	}

	events := make([]growthEvent, 0, len(rows.Rows))
	for _, r := range rows.Rows {
		events = append(events, growthEvent{
			ActorDID:      strVal(r["actor_did"]),
			ParentDID:     strVal(r["parent_did"]),
			TriggerSignal: strVal(r["trigger_signal"]),
			GrowthType:    strVal(r["growth_type"]),
			EtaAtBirth:    floatVal(r["eta_at_birth"]),
			CreatedAt:     timeVal(r["created_at"]),
		})
	}

	if *jsonOut {
		return json.NewEncoder(os.Stdout).Encode(events)
	}

	tw := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
	fmt.Fprintln(tw, "CREATED_AT\tTYPE\tη_BIRTH\tTRIGGER\tACTOR_DID\tPARENT_DID")
	for _, e := range events {
		fmt.Fprintf(tw, "%s\t%s\t%.2f\t%s\t%s\t%s\n",
			e.CreatedAt.Format("2006-01-02 15:04"),
			e.GrowthType, e.EtaAtBirth,
			e.TriggerSignal,
			shortDID(e.ActorDID), shortDID(e.ParentDID),
		)
	}
	tw.Flush()
	fmt.Fprintf(os.Stderr, "\n%d growth events\n", len(events))
	return nil
}

// ── prune ─────────────────────────────────────────────────────────────────────

func runBonsaiPrune(args []string) error {
	fs := flag.NewFlagSet("bonsai prune", flag.ExitOnError)
	preview := fs.Bool("preview", false, "show cascade preview without executing")
	cascade := fs.Bool("cascade", false, "sporulate dependent actors/tables/bpmn/udf")
	block := fs.Bool("block", false, "close anastomosis gate (prevent regrowth)")
	skipEta := fs.Float64("skip-eta", 0.6, "cascade: skip dependents with eta_now >= this value")
	jsonOut := fs.Bool("json", false, "JSON output")
	yes := fs.Bool("yes", false, "skip confirmation prompt")
	fs.Parse(args)

	if fs.NArg() == 0 {
		return fmt.Errorf("usage: gftd bonsai prune <actor_did> [--preview] [--cascade] [--block]")
	}
	actorDID := fs.Arg(0)

	ctx := context.Background()

	// Build cascade list
	targets, err := buildCascadeTargets(ctx, actorDID, *cascade, *skipEta)
	if err != nil {
		return err
	}

	if *jsonOut {
		return json.NewEncoder(os.Stdout).Encode(map[string]any{
			"actor_did": actorDID,
			"targets":   targets,
			"block":     *block,
			"preview":   *preview,
		})
	}

	// Always show preview
	fmt.Printf("will sporulate:\n")
	for _, t := range targets {
		skipped := ""
		if t["skip"] == true {
			skipped = "  (skip: η≥" + fmt.Sprintf("%.2f", *skipEta) + ")"
		}
		fmt.Printf("  %-8s  %-52s  η=%.2f  age=%.0fd%s\n",
			t["growth_type"], shortDID(fmt.Sprint(t["actor_did"])),
			floatAny(t["eta_now"]), floatAny(t["growth_age_days"]), skipped)
	}
	if *block {
		fmt.Printf("\nanastomosis gate: CLOSE (regrowth blocked)\n")
	}
	fmt.Println()

	if *preview {
		fmt.Println("(preview only — no changes made)")
		return nil
	}

	// Confirm
	if !*yes {
		fmt.Printf("confirm sporulate %d target(s)? [y/N] ", countActive(targets))
		reader := bufio.NewReader(os.Stdin)
		line, _ := reader.ReadString('\n')
		if strings.TrimSpace(strings.ToLower(line)) != "y" {
			fmt.Println("aborted")
			return nil
		}
	}

	// Execute: INSERT into vertex_prune_intent
	prunedBy := envOr("GFTD_AGENT_DID", "did:web:gftd-cli.local")
	now := time.Now().UTC()
	for _, t := range targets {
		if t["skip"] == true {
			continue
		}
		did := fmt.Sprint(t["actor_did"])
		status := "dormant"
		if *block {
			status = "blocked"
		}
		_, err := gftddb.RawQuery(ctx, `
			INSERT INTO vertex_prune_intent
			  (actor_did, status, regrowth_blocked, pruned_by, pruned_at)
			VALUES ($1, $2, $3, $4, $5)
		`, did, status, *block, prunedBy, now)
		if err != nil {
			fmt.Fprintf(os.Stderr, "warn: failed to prune %s: %v\n", shortDID(did), err)
			continue
		}
		fmt.Printf("  ✓ sporulated  %s\n", shortDID(did))
	}

	if *block {
		fmt.Printf("\nanastomosis gate closed for %s\n", shortDID(actorDID))
	}
	return nil
}

// ── release ───────────────────────────────────────────────────────────────────

func runBonsaiRelease(args []string) error {
	fs := flag.NewFlagSet("bonsai release", flag.ExitOnError)
	jsonOut := fs.Bool("json", false, "JSON output")
	yes := fs.Bool("yes", false, "skip confirmation prompt")
	fs.Parse(args)

	if fs.NArg() == 0 {
		return fmt.Errorf("usage: gftd bonsai release <actor_did>")
	}
	actorDID := fs.Arg(0)

	if !*yes {
		fmt.Printf("release anastomosis gate for %s? PoNF may trigger regrowth. [y/N] ", shortDID(actorDID))
		reader := bufio.NewReader(os.Stdin)
		line, _ := reader.ReadString('\n')
		if strings.TrimSpace(strings.ToLower(line)) != "y" {
			fmt.Println("aborted")
			return nil
		}
	}

	ctx := context.Background()
	_, err := gftddb.RawQuery(ctx, `
		UPDATE vertex_prune_intent
		SET regrowth_blocked = false, status = 'dormant'
		WHERE actor_did = $1
	`, actorDID)
	if err != nil {
		return fmt.Errorf("release: %w", err)
	}

	if *jsonOut {
		return json.NewEncoder(os.Stdout).Encode(map[string]any{
			"actor_did": actorDID,
			"released":  true,
		})
	}
	fmt.Printf("✓ released  %s\n  anastomosis gate open — PoNF may trigger regrowth\n", shortDID(actorDID))
	return nil
}

// ── status ────────────────────────────────────────────────────────────────────

func runBonsaiStatus(args []string) error {
	fs := flag.NewFlagSet("bonsai status", flag.ExitOnError)
	jsonOut := fs.Bool("json", false, "JSON output")
	fs.Parse(args)

	ctx := context.Background()

	res, err := gftddb.RawQuery(ctx, `
		SELECT
		  prune_status,
		  COUNT(*)           AS count,
		  AVG(eta_now)       AS avg_eta,
		  MIN(eta_now)       AS min_eta,
		  MAX(eta_now)       AS max_eta
		FROM mv_canopy_shape
		GROUP BY prune_status
		ORDER BY prune_status
	`)
	if err != nil {
		return fmt.Errorf("status query: %w\n\nhint: mv_canopy_shape may not exist yet", err)
	}

	growth, err := gftddb.RawQuery(ctx, `
		SELECT COUNT(*) AS total, MAX(created_at) AS last_growth
		FROM vertex_growth_event
	`)
	if err != nil {
		return fmt.Errorf("growth count query: %w", err)
	}

	if *jsonOut {
		out := map[string]any{
			"canopy": res.Rows,
			"growth": growth.Rows,
		}
		return json.NewEncoder(os.Stdout).Encode(out)
	}

	fmt.Println("=== Bonsai Status ===")
	tw := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
	fmt.Fprintln(tw, "STATUS\tCOUNT\tAVG_η\tMIN_η\tMAX_η")
	for _, r := range res.Rows {
		fmt.Fprintf(tw, "%s %s\t%v\t%.2f\t%.2f\t%.2f\n",
			pruneStatusIcon(strVal(r["prune_status"])), strVal(r["prune_status"]),
			r["count"],
			floatAny(r["avg_eta"]), floatAny(r["min_eta"]), floatAny(r["max_eta"]),
		)
	}
	tw.Flush()

	if len(growth.Rows) > 0 {
		fmt.Printf("\ngrowth events total: %v  last: %v\n",
			growth.Rows[0]["total"], growth.Rows[0]["last_growth"])
	}
	return nil
}

// ── helpers ───────────────────────────────────────────────────────────────────

func buildCascadeTargets(ctx context.Context, rootDID string, cascade bool, skipEta float64) ([]map[string]any, error) {
	rows, err := gftddb.RawQuery(ctx, `
		SELECT actor_did, growth_type, eta_now, growth_age_days
		FROM mv_canopy_shape
		WHERE actor_did = $1
	`, rootDID)
	if err != nil {
		return nil, fmt.Errorf("target lookup: %w", err)
	}
	if len(rows.Rows) == 0 {
		return nil, fmt.Errorf("actor not found in canopy: %s", rootDID)
	}

	targets := []map[string]any{rows.Rows[0]}

	if !cascade {
		return targets, nil
	}

	// Walk dependency tree
	deps, err := gftddb.RawQuery(ctx, `
		SELECT actor_did, growth_type, eta_now, growth_age_days
		FROM mv_canopy_shape
		WHERE parent_did = $1 AND prune_status = 'alive'
		ORDER BY eta_now ASC
	`, rootDID)
	if err != nil {
		return nil, fmt.Errorf("cascade lookup: %w", err)
	}

	for _, d := range deps.Rows {
		if floatAny(d["eta_now"]) >= skipEta {
			d["skip"] = true
		}
		targets = append(targets, d)
	}
	return targets, nil
}

func countActive(targets []map[string]any) int {
	n := 0
	for _, t := range targets {
		if t["skip"] != true {
			n++
		}
	}
	return n
}

// strVal and shortDID are defined in apps_kyumei_koji.go and monitor_vote.go respectively.

func pruneStatusIcon(s string) string {
	switch s {
	case "alive":
		return "🌿"
	case "dormant":
		return "💤"
	case "blocked":
		return "🚫"
	default:
		return "❓"
	}
}

func floatVal(v any) float64 {
	switch x := v.(type) {
	case float64:
		return x
	case float32:
		return float64(x)
	case int64:
		return float64(x)
	case int:
		return float64(x)
	}
	return 0
}

func floatAny(v any) float64 { return floatVal(v) }

func intVal(v any) int {
	switch x := v.(type) {
	case int64:
		return int(x)
	case int:
		return x
	case float64:
		return int(x)
	}
	return 0
}

func boolVal(v any) bool {
	switch x := v.(type) {
	case bool:
		return x
	case string:
		return x == "true" || x == "t" || x == "1"
	}
	return false
}

func timeVal(v any) time.Time {
	switch x := v.(type) {
	case time.Time:
		return x
	case string:
		t, _ := time.Parse(time.RFC3339, x)
		return t
	}
	return time.Time{}
}

func printBonsaiUsage() {
	fmt.Print(`gftd bonsai — Bonsai Growth & Prune Model (ADR-2605080100)

Full-auto growth (PoNF-gated), human post-facto pruning.

SUBCOMMANDS:
  canopy    Show live organism shape (mv_canopy_shape)
            --min-eta 0.0  --max-eta 1.0  --status alive|dormant|blocked
            --limit 100    --json

  growth    Show recent growth events (vertex_growth_event)
            --type actor|table|mv|bpmn|udf  --limit 50  --json

  prune     Sporulate an actor (and optionally its dependents)
            gftd bonsai prune <actor_did> [flags]
            --preview          show cascade without executing
            --cascade          include dependent actors/tables/bpmn/udf
            --skip-eta 0.6     skip cascade targets with η ≥ value (default: 0.6)
            --block            close anastomosis gate (prevent regrowth)
            --yes              skip confirmation prompt
            --json

  release   Open anastomosis gate — allow PoNF to trigger regrowth
            gftd bonsai release <actor_did> [--yes] [--json]

  status    Canopy summary (counts / avg η by prune_status + growth total)
            --json

EXAMPLES:
  gftd bonsai canopy --min-eta 0.0 --max-eta 0.5   # show weak branches
  gftd bonsai canopy --status dormant               # show dormant actors
  gftd bonsai growth --type actor --limit 20        # recent actor births
  gftd bonsai prune did:web:foo.etzhayyim.com --preview   # dry-run cascade preview
  gftd bonsai prune did:web:foo.etzhayyim.com --cascade --block --yes
  gftd bonsai release did:web:foo.etzhayyim.com           # re-open gate

PRUNING RULES (ADR-2605080100):
  prune = sporulation, NOT hard delete
  cascade skips η ≥ 0.6 dependents by default (healthy branches are safe)
  dormant actors hard-delete after 90 days (invariants.bonsai.dormancy_ttl_days)
  humans never run DROP TABLE or DELETE directly
`)
}
