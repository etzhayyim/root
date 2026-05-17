// gftd monitor vote — ADR-0046 triple-witness autonomy monitoring.
//
// 3 independent monitor actors (yoro-liveness / yoro-shinka / yoro-integrity)
// attest yoro health and open corrective-action votes. 2-of-3 quorum gates
// pause / rollback / rotate-key. alert / escalate are unilateral.
//
// Phase 0 scope (this file): dry-run, list, cast, resolve.
// Production writes use each monitor's own CF Worker / goose wrapper via
// createKyselyDb(env.HYPERDRIVE) per ADR-0036; this CLI is for operator
// inspection + quorum simulation and runs via direct psql / pgx.
package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"strings"
	"text/tabwriter"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
)

const (
	yoroSubjectDID = "did:web:yoro.etzhayyim.com"

	voteActionAlert     = "alert"
	voteActionPause     = "pause"
	voteActionRollback  = "rollback"
	voteActionRotateKey = "rotate-key"
	voteActionEscalate  = "escalate"
)

// quorumRequired returns how many yea ballots an action needs.
// Unilateral actions (alert, escalate) pass on open with 0 required.
func quorumRequired(action string) int {
	switch action {
	case voteActionAlert, voteActionEscalate:
		return 0
	case voteActionPause, voteActionRollback, voteActionRotateKey:
		return 2
	default:
		return 2 // safe default: treat unknown action as quorum-required
	}
}

type monitorBallot struct {
	MonitorDID string `json:"monitor_did"`
	Decision   string `json:"decision"` // "yea" | "nay"
	SigES256   string `json:"sig_es256,omitempty"`
	Ts         string `json:"ts"`
}

type monitorVote struct {
	VertexID    string          `json:"vertex_id"`
	SubjectDID  string          `json:"subject_did"`
	Action      string          `json:"action"`
	Reason      string          `json:"reason"`
	RequestedBy string          `json:"requested_by"`
	OpenedAt    string          `json:"opened_at"`
	ClosesAt    string          `json:"closes_at"`
	Ballots     []monitorBallot `json:"ballots"`
	BallotCount int             `json:"ballot_count"`
	YeaCount    int             `json:"yea_count"`
	Resolution  string          `json:"resolution"` // "" (open) | "passed" | "failed" | "expired"
	ResolvedAt  string          `json:"resolved_at,omitempty"`
}

// runMonitorVote implements `gftd monitor vote`.
func runMonitorVote(args []string) error {
	if len(args) == 0 {
		printMonitorVoteUsage()
		return nil
	}
	sub := args[0]
	rest := args[1:]
	switch sub {
	case "dry-run":
		return runMonitorVoteDryRun(rest)
	case "list":
		return runMonitorVoteList(rest)
	case "cast":
		return runMonitorVoteCast(rest)
	case "resolve":
		return runMonitorVoteResolve(rest)
	case "-h", "--help", "help":
		printMonitorVoteUsage()
		return nil
	default:
		printMonitorVoteUsage()
		return fmt.Errorf("unknown subcommand: %s", sub)
	}
}

func printMonitorVoteUsage() {
	fmt.Fprintln(os.Stderr, `gftd monitor vote — ADR-0046 triple-witness quorum votes

Usage:
  gftd monitor vote <subcommand> [flags]

Subcommands:
  dry-run   Simulate a vote + N synthetic ballots locally (no DB write)
  list      List votes for a subject (default: did:web:yoro.etzhayyim.com)
  cast      Append a ballot (yea/nay) to an open vote
  resolve   Tally ballots on an open vote and close it (passed/failed/expired)

Actions:
  alert       unilateral (0-of-3) — informational page
  escalate    unilateral (0-of-3) — hand off to human oncall
  pause       quorum (2-of-3)     — disable yoro goose recipes
  rollback    quorum (2-of-3)     — request moderator tombstone of bad post
  rotate-key  quorum (2-of-3)     — authz.etzhayyim.com ES256 multi-key rotate

Examples:
  gftd monitor vote dry-run --subject did:web:yoro.etzhayyim.com --action pause \
      --reason flood --fake-ballots 2

  gftd monitor vote list --open

  gftd monitor vote cast --vote at://did:web:yoro.etzhayyim.com/.../<rkey> \
      --monitor did:web:yoro-shinka.etzhayyim.com --decision yea

  gftd monitor vote resolve --vote at://...`)
}

// ---------------------------------------------------------------------------
// dry-run: fully local simulation, no DB write.
// ---------------------------------------------------------------------------

func runMonitorVoteDryRun(args []string) error {
	fs := flag.NewFlagSet("monitor vote dry-run", flag.ExitOnError)
	subject := fs.String("subject", yoroSubjectDID, "subject DID to vote on")
	action := fs.String("action", "", "action: alert|escalate|pause|rollback|rotate-key")
	reason := fs.String("reason", "", "fault class: stale|drift|loop|byzantine|pii-leak|flood|...")
	requestedBy := fs.String("requested-by", "did:web:yoro-liveness.etzhayyim.com", "monitor DID opening the vote")
	fakeBallots := fs.Int("fake-ballots", 2, "number of synthetic yea ballots to inject")
	fakeDecision := fs.String("fake-decision", "yea", "synthetic ballot decision: yea|nay|mixed")
	jsonOut := fs.Bool("json", false, "JSON output")
	fs.Parse(args)

	if *action == "" || *reason == "" {
		return fmt.Errorf("--action and --reason are required")
	}

	now := time.Now().UTC()
	closes := now.Add(closesAfter(*action))
	rkey := fmt.Sprintf("%d", now.UnixNano())
	vertexID := fmt.Sprintf("at://%s/ai.gftd.apps.yoro_gov.vote/%s", *subject, rkey)

	// Candidate peers. In real flow these are the other 2 monitor DIDs.
	peers := []string{
		"did:web:yoro-liveness.etzhayyim.com",
		"did:web:yoro-shinka.etzhayyim.com",
		"did:web:yoro-integrity.etzhayyim.com",
	}

	vote := monitorVote{
		VertexID:    vertexID,
		SubjectDID:  *subject,
		Action:      *action,
		Reason:      *reason,
		RequestedBy: *requestedBy,
		OpenedAt:    now.Format(time.RFC3339),
		ClosesAt:    closes.Format(time.RFC3339),
	}

	// Unilateral actions self-pass on open.
	if quorumRequired(*action) == 0 {
		vote.Resolution = "passed"
		vote.ResolvedAt = now.Format(time.RFC3339)
	}

	// Inject synthetic ballots from peers other than the opener.
	injected := 0
	for _, peer := range peers {
		if injected >= *fakeBallots {
			break
		}
		if peer == *requestedBy {
			continue
		}
		decision := *fakeDecision
		if decision == "mixed" {
			if injected%2 == 0 {
				decision = "yea"
			} else {
				decision = "nay"
			}
		}
		vote.Ballots = append(vote.Ballots, monitorBallot{
			MonitorDID: peer,
			Decision:   decision,
			SigES256:   "dryrun-unsigned",
			Ts:         now.Add(time.Duration(injected+1) * time.Second).Format(time.RFC3339),
		})
		injected++
	}
	vote.BallotCount = len(vote.Ballots)
	for _, b := range vote.Ballots {
		if b.Decision == "yea" {
			vote.YeaCount++
		}
	}

	// Tally against quorum (if not already self-passed).
	if vote.Resolution == "" {
		if vote.YeaCount >= quorumRequired(*action) {
			vote.Resolution = "passed"
			vote.ResolvedAt = now.Format(time.RFC3339)
		}
		// else: leave open; real monitors would tally on the next tick.
	}

	if *jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(vote)
	}
	printVote(vote)
	fmt.Fprintf(os.Stderr, "\n-- dry-run: no database write --\n")
	return nil
}

// closesAfter returns the per-action default vote window.
func closesAfter(action string) time.Duration {
	switch action {
	case voteActionAlert, voteActionEscalate:
		return 15 * time.Minute
	case voteActionPause, voteActionRollback:
		return 1 * time.Hour
	case voteActionRotateKey:
		return 24 * time.Hour
	default:
		return 1 * time.Hour
	}
}

// ---------------------------------------------------------------------------
// list: query vertex_yoro_monitor_vote.
// ---------------------------------------------------------------------------

func runMonitorVoteList(args []string) error {
	fs := flag.NewFlagSet("monitor vote list", flag.ExitOnError)
	subject := fs.String("subject", yoroSubjectDID, "subject DID filter")
	openOnly := fs.Bool("open", false, "list only open votes (resolution IS NULL)")
	limit := fs.Int("limit", 50, "max rows")
	dbURL := fs.String("url", "", "RisingWave PostgreSQL URL")
	envPreset := fs.String("env", "prod", "Env preset: local|prod")
	jsonOut := fs.Bool("json", false, "JSON output")
	fs.Parse(args)

	url := resolveKaDBURL(*dbURL, *envPreset)
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	pool, err := pgxpool.New(ctx, url)
	if err != nil {
		return fmt.Errorf("db connect: %w", err)
	}
	defer pool.Close()

	q := `SELECT vertex_id, subject_did, action, reason, requested_by,
	         opened_at, closes_at, ballots_json, ballot_count, yea_count,
	         resolution, resolved_at
	     FROM vertex_yoro_monitor_vote
	     WHERE subject_did = $1`
	params := []any{*subject}
	if *openOnly {
		q += " AND resolution IS NULL"
	}
	q += " ORDER BY opened_at DESC LIMIT $2"
	params = append(params, *limit)

	rows, err := pool.Query(ctx, q, params...)
	if err != nil {
		return fmt.Errorf("query: %w", err)
	}
	defer rows.Close()

	var out []monitorVote
	for rows.Next() {
		var v monitorVote
		var ballotsJSON, resolution, resolvedAt *string
		if err := rows.Scan(&v.VertexID, &v.SubjectDID, &v.Action, &v.Reason, &v.RequestedBy,
			&v.OpenedAt, &v.ClosesAt, &ballotsJSON, &v.BallotCount, &v.YeaCount,
			&resolution, &resolvedAt); err != nil {
			return fmt.Errorf("scan: %w", err)
		}
		if ballotsJSON != nil && *ballotsJSON != "" {
			_ = json.Unmarshal([]byte(*ballotsJSON), &v.Ballots)
		}
		if resolution != nil {
			v.Resolution = *resolution
		}
		if resolvedAt != nil {
			v.ResolvedAt = *resolvedAt
		}
		out = append(out, v)
	}

	if *jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(out)
	}
	if len(out) == 0 {
		fmt.Fprintln(os.Stderr, "(no votes)")
		return nil
	}
	w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
	fmt.Fprintln(w, "Opened\tAction\tReason\tBallots\tYea\tResolution\tRequestedBy")
	fmt.Fprintln(w, "------\t------\t------\t-------\t---\t----------\t-----------")
	for _, v := range out {
		res := v.Resolution
		if res == "" {
			res = "open"
		}
		fmt.Fprintf(w, "%s\t%s\t%s\t%d/%d\t%d\t%s\t%s\n",
			shortTs(v.OpenedAt), v.Action, v.Reason, v.BallotCount, quorumRequired(v.Action),
			v.YeaCount, res, shortDID(v.RequestedBy))
	}
	return w.Flush()
}

// ---------------------------------------------------------------------------
// cast: append a ballot to an open vote.
// ---------------------------------------------------------------------------

func runMonitorVoteCast(args []string) error {
	fs := flag.NewFlagSet("monitor vote cast", flag.ExitOnError)
	voteID := fs.String("vote", "", "vote vertex_id (required)")
	monitor := fs.String("monitor", "", "monitor DID casting the ballot (required)")
	decision := fs.String("decision", "", "yea|nay (required)")
	sig := fs.String("sig", "", "ES256 signature (mandatory in prod; empty for local manual ops)")
	dbURL := fs.String("url", "", "RisingWave PostgreSQL URL")
	envPreset := fs.String("env", "prod", "Env preset: local|prod")
	jsonOut := fs.Bool("json", false, "JSON output")
	fs.Parse(args)

	if *voteID == "" || *monitor == "" || (*decision != "yea" && *decision != "nay") {
		return fmt.Errorf("--vote, --monitor, and --decision (yea|nay) are required")
	}

	url := resolveKaDBURL(*dbURL, *envPreset)
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	pool, err := pgxpool.New(ctx, url)
	if err != nil {
		return fmt.Errorf("db connect: %w", err)
	}
	defer pool.Close()

	// Fetch current row.
	var ballotsJSON *string
	var action, resolution string
	err = pool.QueryRow(ctx,
		`SELECT action, COALESCE(resolution,'') AS resolution, ballots_json
		 FROM vertex_yoro_monitor_vote WHERE vertex_id = $1`, *voteID).
		Scan(&action, &resolution, &ballotsJSON)
	if err != nil {
		return fmt.Errorf("vote not found: %w", err)
	}
	if resolution != "" {
		return fmt.Errorf("vote already resolved: %s", resolution)
	}

	var ballots []monitorBallot
	if ballotsJSON != nil && *ballotsJSON != "" {
		_ = json.Unmarshal([]byte(*ballotsJSON), &ballots)
	}
	for _, b := range ballots {
		if b.MonitorDID == *monitor {
			return fmt.Errorf("monitor %s has already cast a ballot on this vote", *monitor)
		}
	}
	now := time.Now().UTC().Format(time.RFC3339)
	ballots = append(ballots, monitorBallot{
		MonitorDID: *monitor, Decision: *decision, SigES256: *sig, Ts: now,
	})
	yea := 0
	for _, b := range ballots {
		if b.Decision == "yea" {
			yea++
		}
	}
	newJSON, _ := json.Marshal(ballots)

	resolutionVal := ""
	resolvedAt := ""
	if yea >= quorumRequired(action) {
		resolutionVal = "passed"
		resolvedAt = now
	}

	_, err = pool.Exec(ctx,
		`UPDATE vertex_yoro_monitor_vote
		   SET ballots_json = $1, ballot_count = $2, yea_count = $3,
		       resolution = NULLIF($4, ''), resolved_at = NULLIF($5, '')
		 WHERE vertex_id = $6`,
		string(newJSON), len(ballots), yea, resolutionVal, resolvedAt, *voteID)
	if err != nil {
		return fmt.Errorf("update: %w", err)
	}

	result := map[string]any{
		"vote":        *voteID,
		"action":      action,
		"ballots":     len(ballots),
		"yea":         yea,
		"required":    quorumRequired(action),
		"resolution":  resolutionVal,
		"resolved_at": resolvedAt,
	}
	if *jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(result)
	}
	fmt.Fprintf(os.Stderr, "✓ ballot cast by %s: decision=%s tally=%d/%d (need %d) resolution=%s\n",
		shortDID(*monitor), *decision, yea, len(ballots), quorumRequired(action),
		emptyAs(resolutionVal, "open"))
	return nil
}

// ---------------------------------------------------------------------------
// resolve: tally an open vote, set resolution=passed|failed|expired.
// ---------------------------------------------------------------------------

func runMonitorVoteResolve(args []string) error {
	fs := flag.NewFlagSet("monitor vote resolve", flag.ExitOnError)
	voteID := fs.String("vote", "", "vote vertex_id (required)")
	dbURL := fs.String("url", "", "RisingWave PostgreSQL URL")
	envPreset := fs.String("env", "prod", "Env preset: local|prod")
	jsonOut := fs.Bool("json", false, "JSON output")
	fs.Parse(args)

	if *voteID == "" {
		return fmt.Errorf("--vote is required")
	}

	url := resolveKaDBURL(*dbURL, *envPreset)
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	pool, err := pgxpool.New(ctx, url)
	if err != nil {
		return fmt.Errorf("db connect: %w", err)
	}
	defer pool.Close()

	var action, closesAt string
	var ballotsJSON, existing *string
	err = pool.QueryRow(ctx,
		`SELECT action, closes_at, COALESCE(resolution,'') AS resolution, ballots_json
		 FROM vertex_yoro_monitor_vote WHERE vertex_id = $1`, *voteID).
		Scan(&action, &closesAt, &existing, &ballotsJSON)
	if err != nil {
		return fmt.Errorf("vote not found: %w", err)
	}
	if existing != nil && *existing != "" {
		return fmt.Errorf("vote already resolved: %s", *existing)
	}

	var ballots []monitorBallot
	if ballotsJSON != nil && *ballotsJSON != "" {
		_ = json.Unmarshal([]byte(*ballotsJSON), &ballots)
	}
	yea := 0
	for _, b := range ballots {
		if b.Decision == "yea" {
			yea++
		}
	}
	now := time.Now().UTC()
	nowStr := now.Format(time.RFC3339)

	expired := false
	if t, err := time.Parse(time.RFC3339, closesAt); err == nil && now.After(t) {
		expired = true
	}

	resolution := ""
	switch {
	case yea >= quorumRequired(action):
		resolution = "passed"
	case expired:
		resolution = "expired"
	default:
		// Still open and not expired — no-op.
		fmt.Fprintf(os.Stderr, "vote still open: %d yea / need %d (closes_at=%s)\n",
			yea, quorumRequired(action), closesAt)
		return nil
	}

	_, err = pool.Exec(ctx,
		`UPDATE vertex_yoro_monitor_vote SET resolution = $1, resolved_at = $2
		 WHERE vertex_id = $3`, resolution, nowStr, *voteID)
	if err != nil {
		return fmt.Errorf("update: %w", err)
	}

	result := map[string]any{
		"vote":        *voteID,
		"action":      action,
		"yea":         yea,
		"required":    quorumRequired(action),
		"resolution":  resolution,
		"resolved_at": nowStr,
	}
	if *jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(result)
	}
	fmt.Fprintf(os.Stderr, "✓ resolved %s: %s (%d yea / required %d)\n",
		shortTs(nowStr), resolution, yea, quorumRequired(action))
	return nil
}

// ---------------------------------------------------------------------------
// Helpers.
// ---------------------------------------------------------------------------

func printVote(v monitorVote) {
	fmt.Printf("vote_id:      %s\n", v.VertexID)
	fmt.Printf("subject:      %s\n", v.SubjectDID)
	fmt.Printf("action:       %s (quorum required: %d yea)\n", v.Action, quorumRequired(v.Action))
	fmt.Printf("reason:       %s\n", v.Reason)
	fmt.Printf("requested_by: %s\n", v.RequestedBy)
	fmt.Printf("opened_at:    %s\n", v.OpenedAt)
	fmt.Printf("closes_at:    %s\n", v.ClosesAt)
	fmt.Printf("ballots:      %d (yea=%d)\n", v.BallotCount, v.YeaCount)
	for _, b := range v.Ballots {
		fmt.Printf("  - %s %s (sig=%s, ts=%s)\n", shortDID(b.MonitorDID), b.Decision, shortSig(b.SigES256), b.Ts)
	}
	res := v.Resolution
	if res == "" {
		res = "open"
	}
	fmt.Printf("resolution:   %s", res)
	if v.ResolvedAt != "" {
		fmt.Printf(" (at %s)", v.ResolvedAt)
	}
	fmt.Println()
}

func shortDID(did string) string {
	// did:web:yoro-liveness.etzhayyim.com → yoro-liveness
	s := strings.TrimPrefix(did, "did:web:")
	s = strings.TrimSuffix(s, ".etzhayyim.com")
	return s
}

func shortTs(ts string) string {
	if t, err := time.Parse(time.RFC3339, ts); err == nil {
		return t.Format("01-02 15:04")
	}
	return ts
}

func shortSig(sig string) string {
	if len(sig) > 12 {
		return sig[:12] + "…"
	}
	return sig
}

func emptyAs(s, fallback string) string {
	if s == "" {
		return fallback
	}
	return s
}
