// gftd ka — 会社経営 CLI (Company Operations Management)
//
// Query the Strategy Graph in RisingWave to surface goals, actions,
// revenue streams, risks, KPIs, and the reverse-topological execution
// order. Designed for CEO/COO daily decision-making.
//
// Subcommands:
//   gftd ka                 Dashboard (default) — entity health + top KPIs
//   gftd ka goals           Goal progress + attainment
//   gftd ka actions         Action priority (reverse-topo sorted)
//   gftd ka revenue         Revenue stream rollup + forecast
//   gftd ka burn            Cost center burn rate + reducible
//   gftd ka risks           Open risks ranked by expected loss
//   gftd ka cases           Litigation/project case load
//   gftd ka projects        Document→project classification summary
//   gftd ka topo            Full reverse-topological sort (actions → goals)
//   gftd ka snapshot        Take strategy snapshot (append to vertex_strategy_snapshot)
//   gftd ka assign          Job assignment matrix (4 members)
//   gftd ka kpi             KPI traffic-light board
//   gftd ka inbox           Kyber inbox signal/noise summary (email/docs)
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

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

func runKa(args []string) error {
	fs := flag.NewFlagSet("ka", flag.ContinueOnError)
	jsonOut := fs.Bool("json", false, "JSON output")
	dbURL := fs.String("url", "", "RisingWave PostgreSQL URL")
	envPreset := fs.String("env", "prod", "Env preset: local|prod")
	if err := fs.Parse(args); err != nil {
		return err
	}

	url := resolveKaDBURL(*dbURL, *envPreset)
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	pool, err := pgxpool.New(ctx, url)
	if err != nil {
		return fmt.Errorf("db connect: %w", err)
	}
	defer pool.Close()
	db := pool // alias for readability

	sub := "dashboard"
	if fa := fs.Args(); len(fa) > 0 {
		sub = fa[0]
	}

	switch sub {
	case "dashboard", "dash":
		return kaDashboard(ctx, db, *jsonOut)
	case "goals":
		return kaGoals(ctx, db, *jsonOut)
	case "actions":
		return kaActions(ctx, db, *jsonOut)
	case "revenue", "rev":
		return kaRevenue(ctx, db, *jsonOut)
	case "burn":
		return kaBurn(ctx, db, *jsonOut)
	case "risks":
		return kaRisks(ctx, db, *jsonOut)
	case "cases":
		return kaCases(ctx, db, *jsonOut)
	case "projects":
		return kaProjects(ctx, db, *jsonOut)
	case "topo":
		return kaTopo(ctx, db, *jsonOut)
	case "kpi":
		return kaKPI(ctx, db, *jsonOut)
	case "inbox":
		return kaInbox(ctx, db, *jsonOut)
	case "snapshot":
		return kaSnapshot(ctx, db, *jsonOut)
	case "tasks":
		return kaTasks(ctx, db, *jsonOut)
	case "assign":
		return kaAssign(ctx, db, *jsonOut)
	case "help":
		printKaUsage()
		return nil
	default:
		return fmt.Errorf("unknown ka subcommand: %s\n\nRun 'gftd ka help' for usage", sub)
	}
}

func resolveKaDBURL(explicit, env string) string {
	if explicit != "" {
		return explicit
	}
	if u := os.Getenv("GFTD_DATABASE_URL"); u != "" {
		return u
	}
	if u := os.Getenv("DATABASE_URL"); u != "" {
		return u
	}
	if env == "local" {
		return rwLocalURL
	}
	return rwProdURL
}

func printKaUsage() {
	fmt.Fprintln(os.Stderr, `gftd ka — 会社経営 CLI (Company Operations Management)

Usage:
  gftd ka [subcommand] [flags]

Subcommands:
  dashboard   Entity health + top KPIs (default)
  goals       Goal progress + attainment %
  actions     Action priority (reverse-topo sorted, effort/confidence weighted)
  revenue     Revenue stream rollup + forecast (MRR current vs target)
  burn        Cost center burn rate + reducible amount
  risks       Open risks ranked by expected_loss_jpy
  cases       Litigation/project case load + document counts
  projects    Document→project classification summary (P1-P10)
  topo        Full reverse-topological sort (Goal ← Action ← Infra)
  kpi         KPI traffic-light board (green/yellow/red)
  inbox       Kyber inbox signal/noise summary (email/calendar/docs)
  snapshot    Take and store a strategy snapshot
  assign      Job assignment matrix (4 members × streams)

Flags:
  --json      JSON output
  --url       RisingWave PostgreSQL URL (default: prod LB)
  --env       Preset: local (127.0.0.1:14566) | prod (45.32.79.245:4566)`)
}

// ── Subcommand implementations ────────────────────────────────────────

func kaDashboard(ctx context.Context, db *pgxpool.Pool, jsonOut bool) error {
	w := tabwriter.NewWriter(os.Stdout, 0, 4, 2, ' ', 0)
	defer w.Flush()

	fmt.Fprintf(w, "═══════════════════════════════════════════════\n")
	fmt.Fprintf(w, " gftd ka — 経営ダッシュボード  %s\n", time.Now().Format("2006-01-02 15:04"))
	fmt.Fprintf(w, "═══════════════════════════════════════════════\n\n")

	// Entity health
	rows, err := db.Query(ctx, `SELECT entity_code, legal_name, status FROM vertex_business_entity ORDER BY entity_code`)
	if err != nil {
		return fmt.Errorf("entities: %w", err)
	}
	defer rows.Close()
	fmt.Fprintf(w, "【法人】\n")
	fmt.Fprintf(w, "  Code\tName\tStatus\n")
	for rows.Next() {
		var code, name, status string
		rows.Scan(&code, &name, &status)
		icon := statusIcon(status)
		fmt.Fprintf(w, "  %s\t%s\t%s %s\n", code, name, icon, status)
	}

	// Goals
	fmt.Fprintf(w, "\n【目標 (Goals)】\n")
	rows2, _ := db.Query(ctx, `SELECT goal_code, display_name, status, attainment_bps, target_date FROM vertex_goal ORDER BY attainment_bps DESC`)
	defer rows2.Close()
	fmt.Fprintf(w, "  Code\tGoal\tStatus\tProgress\tDeadline\n")
	for rows2.Next() {
		var code, name, status, date string
		var att int64
		rows2.Scan(&code, &name, &status, &att, &date)
		bar := progressBar(int(att), 10000)
		fmt.Fprintf(w, "  %s\t%s\t%s\t%s %.1f%%\t%s\n", code, name, statusIcon(status), bar, float64(att)/100.0, date)
	}

	// KPI traffic lights
	fmt.Fprintf(w, "\n【KPI】\n")
	rows3, _ := db.Query(ctx, `SELECT kpi_code, display_name, current_value, target_value, threshold_red, threshold_green, unit, direction FROM vertex_kpi ORDER BY kpi_code`)
	defer rows3.Close()
	fmt.Fprintf(w, "  KPI\tCurrent\tTarget\tLight\n")
	for rows3.Next() {
		var code, name, unit, dir string
		var cur, tgt, red, green int64
		rows3.Scan(&code, &name, &cur, &tgt, &red, &green, &unit, &dir)
		light := trafficLight(cur, red, green, dir)
		fmt.Fprintf(w, "  %s\t%s\t%s\t%s\n", name, fmtVal(cur, unit), fmtVal(tgt, unit), light)
	}

	// Revenue summary
	fmt.Fprintf(w, "\n【収益 (Revenue Streams)】\n")
	rows4, _ := db.Query(ctx, `SELECT stream_code, display_name, status, current_mrr_jpy, target_mrr_jpy FROM vertex_revenue_stream WHERE target_mrr_jpy > 0 ORDER BY target_mrr_jpy DESC LIMIT 10`)
	defer rows4.Close()
	fmt.Fprintf(w, "  Stream\tStatus\tMRR Now\tMRR Target\n")
	for rows4.Next() {
		var code, name, status string
		var cur, tgt int64
		rows4.Scan(&code, &name, &status, &cur, &tgt)
		fmt.Fprintf(w, "  %s\t%s\t¥%s\t¥%s\n", name, statusIcon(status), fmtJPY(cur), fmtJPY(tgt))
	}

	// Top risks
	fmt.Fprintf(w, "\n【リスク (Top 5)】\n")
	rows5, _ := db.Query(ctx, `SELECT risk_code, display_name, severity, expected_loss_jpy FROM vertex_risk WHERE status IN ('open','mitigating') ORDER BY expected_loss_jpy DESC LIMIT 5`)
	defer rows5.Close()
	fmt.Fprintf(w, "  Risk\tSeverity\tExpected Loss\n")
	for rows5.Next() {
		var code, name, sev string
		var loss int64
		rows5.Scan(&code, &name, &sev, &loss)
		fmt.Fprintf(w, "  %s\t%s\t¥%s\n", name, sevIcon(sev), fmtJPY(loss))
	}

	// Top actions
	fmt.Fprintf(w, "\n【次アクション (Top 5 by priority)】\n")
	rows6, _ := db.Query(ctx, `SELECT action_code, display_name, phase, priority, effort_days FROM vertex_action WHERE status = 'planned' ORDER BY priority DESC, effort_days ASC LIMIT 5`)
	defer rows6.Close()
	fmt.Fprintf(w, "  Action\tPhase\tPriority\tEffort\n")
	for rows6.Next() {
		var code, name, phase string
		var prio, effort int64
		rows6.Scan(&code, &name, &phase, &prio, &effort)
		fmt.Fprintf(w, "  %s\t%s\tP%d\t%dd\n", name, phase, prio, effort)
	}

	return nil
}

func kaGoals(ctx context.Context, db *pgxpool.Pool, jsonOut bool) error {
	rows, _ := db.Query(ctx, `SELECT goal_code, display_name, goal_type, status, attainment_bps, target_date, target_value_jpy FROM vertex_goal ORDER BY attainment_bps DESC`)
	defer rows.Close()
	if jsonOut {
		return rowsToJSON(rows)
	}
	w := tabwriter.NewWriter(os.Stdout, 0, 4, 2, ' ', 0)
	defer w.Flush()
	fmt.Fprintf(w, "Goal\tType\tStatus\tProgress\tTarget Date\tTarget ¥\n")
	for rows.Next() {
		var code, name, typ, status, date string
		var att, tgt int64
		rows.Scan(&code, &name, &typ, &status, &att, &date, &tgt)
		fmt.Fprintf(w, "%s\t%s\t%s %s\t%s %.1f%%\t%s\t¥%s\n", name, typ, statusIcon(status), status, progressBar(int(att), 10000), float64(att)/100.0, date, fmtJPY(tgt))
	}
	return nil
}

func kaActions(ctx context.Context, db *pgxpool.Pool, jsonOut bool) error {
	rows, _ := db.Query(ctx, `SELECT action_code, display_name, status, phase, topo_level, priority, effort_days, confidence_bps FROM vertex_action ORDER BY topo_level ASC, priority DESC`)
	defer rows.Close()
	if jsonOut {
		return rowsToJSON(rows)
	}
	w := tabwriter.NewWriter(os.Stdout, 0, 4, 2, ' ', 0)
	defer w.Flush()
	fmt.Fprintf(w, "Action\tPhase\tTopo\tPriority\tEffort\tConf\n")
	for rows.Next() {
		var code, name, status, phase string
		var topo, prio, effort, conf int64
		rows.Scan(&code, &name, &status, &phase, &topo, &prio, &effort, &conf)
		fmt.Fprintf(w, "%s\t%s\tL%d\tP%d\t%dd\t%.0f%%\n", name, phase, topo, prio, effort, float64(conf)/100.0)
	}
	return nil
}

func kaRevenue(ctx context.Context, db *pgxpool.Pool, jsonOut bool) error {
	rows, _ := db.Query(ctx, `SELECT stream_code, display_name, status, current_mrr_jpy, target_mrr_jpy, gross_margin_bps, entity_id FROM vertex_revenue_stream ORDER BY target_mrr_jpy DESC`)
	defer rows.Close()
	if jsonOut {
		return rowsToJSON(rows)
	}
	w := tabwriter.NewWriter(os.Stdout, 0, 4, 2, ' ', 0)
	defer w.Flush()
	fmt.Fprintf(w, "Stream\tStatus\tMRR Now\tMRR Target\tMargin\tEntity\n")
	for rows.Next() {
		var code, name, status, entity string
		var cur, tgt, margin int64
		rows.Scan(&code, &name, &status, &cur, &tgt, &margin, &entity)
		fmt.Fprintf(w, "%s\t%s %s\t¥%s\t¥%s\t%.0f%%\t%s\n", name, statusIcon(status), status, fmtJPY(cur), fmtJPY(tgt), float64(margin)/100.0, entity)
	}
	return nil
}

func kaBurn(ctx context.Context, db *pgxpool.Pool, jsonOut bool) error {
	rows, _ := db.Query(ctx, `SELECT center_code, display_name, category, monthly_burn_jpy, reducible_bps, entity_id FROM vertex_cost_center ORDER BY monthly_burn_jpy DESC`)
	defer rows.Close()
	if jsonOut {
		return rowsToJSON(rows)
	}
	w := tabwriter.NewWriter(os.Stdout, 0, 4, 2, ' ', 0)
	defer w.Flush()
	fmt.Fprintf(w, "Cost Center\tCategory\tBurn/月\tReducible\tEntity\n")
	var totalBurn int64
	for rows.Next() {
		var code, name, cat, entity string
		var burn, red int64
		rows.Scan(&code, &name, &cat, &burn, &red, &entity)
		totalBurn += burn
		fmt.Fprintf(w, "%s\t%s\t¥%s\t%.0f%%\t%s\n", name, cat, fmtJPY(burn), float64(red)/100.0, entity)
	}
	fmt.Fprintf(w, "\nTotal burn: ¥%s/月\n", fmtJPY(totalBurn))
	return nil
}

func kaRisks(ctx context.Context, db *pgxpool.Pool, jsonOut bool) error {
	rows, _ := db.Query(ctx, `SELECT risk_code, display_name, risk_type, severity, probability_bps, impact_jpy, expected_loss_jpy, status FROM vertex_risk WHERE status IN ('open','mitigating') ORDER BY expected_loss_jpy DESC`)
	defer rows.Close()
	if jsonOut {
		return rowsToJSON(rows)
	}
	w := tabwriter.NewWriter(os.Stdout, 0, 4, 2, ' ', 0)
	defer w.Flush()
	fmt.Fprintf(w, "Risk\tType\tSeverity\tProb\tImpact\tE[Loss]\tStatus\n")
	for rows.Next() {
		var code, name, typ, sev, status string
		var prob, impact, loss int64
		rows.Scan(&code, &name, &typ, &sev, &prob, &impact, &loss, &status)
		fmt.Fprintf(w, "%s\t%s\t%s %s\t%.0f%%\t¥%s\t¥%s\t%s\n", name, typ, sevIcon(sev), sev, float64(prob)/100.0, fmtJPY(impact), fmtJPY(loss), status)
	}
	return nil
}

func kaCases(ctx context.Context, db *pgxpool.Pool, jsonOut bool) error {
	rows, _ := db.Query(ctx, `SELECT case_code, display_name, case_type, status, counterparty, estimated_impact_jpy, document_count FROM vertex_business_case WHERE status != 'closed' ORDER BY estimated_impact_jpy DESC`)
	defer rows.Close()
	if jsonOut {
		return rowsToJSON(rows)
	}
	w := tabwriter.NewWriter(os.Stdout, 0, 4, 2, ' ', 0)
	defer w.Flush()
	fmt.Fprintf(w, "Case\tType\tStatus\tCounterparty\tImpact\tDocs\n")
	for rows.Next() {
		var code, name, typ, status string
		var party *string
		var impact, docs int64
		rows.Scan(&code, &name, &typ, &status, &party, &impact, &docs)
		p := "-"
		if party != nil {
			p = *party
		}
		fmt.Fprintf(w, "%s\t%s\t%s\t%s\t¥%s\t%d\n", name, typ, status, p, fmtJPY(impact), docs)
	}
	return nil
}

func kaProjects(ctx context.Context, db *pgxpool.Pool, jsonOut bool) error {
	rows, _ := db.Query(ctx, `SELECT bc.case_code, bc.display_name, COUNT(ip.src_vid) AS docs FROM vertex_business_case bc LEFT JOIN edge_in_project ip ON ip.dst_vid = bc.vertex_id WHERE bc.case_code LIKE 'P%' GROUP BY bc.case_code, bc.display_name ORDER BY docs DESC`)
	defer rows.Close()
	if jsonOut {
		return rowsToJSON(rows)
	}
	w := tabwriter.NewWriter(os.Stdout, 0, 4, 2, ' ', 0)
	defer w.Flush()
	fmt.Fprintf(w, "Project\tDescription\tDocs\n")
	for rows.Next() {
		var code, name string
		var docs int64
		rows.Scan(&code, &name, &docs)
		fmt.Fprintf(w, "%s\t%s\t%d\n", code, name, docs)
	}
	return nil
}

func kaTopo(ctx context.Context, db *pgxpool.Pool, jsonOut bool) error {
	// Print goals, then L1 actions (topo_level=1), L2, L3 with deps
	w := tabwriter.NewWriter(os.Stdout, 0, 4, 2, ' ', 0)
	defer w.Flush()

	fmt.Fprintf(w, "═══ Reverse Topological Sort (Goal ← Action ← Infra) ═══\n\n")

	// Goals
	fmt.Fprintf(w, "L0 GOALS:\n")
	rows, _ := db.Query(ctx, `SELECT goal_code, display_name, status, attainment_bps FROM vertex_goal ORDER BY goal_code`)
	defer rows.Close()
	for rows.Next() {
		var code, name, status string
		var att int64
		rows.Scan(&code, &name, &status, &att)
		fmt.Fprintf(w, "  🎯 %s — %s (%s, %.1f%%)\n", code, name, status, float64(att)/100.0)
	}

	// Actions by topo_level
	for level := int64(1); level <= 3; level++ {
		fmt.Fprintf(w, "\nL%d ACTIONS:\n", level)
		rows2, _ := db.Query(ctx, `SELECT action_code, display_name, phase, priority, effort_days FROM vertex_action WHERE topo_level = $1 ORDER BY priority DESC`, level)
		for rows2.Next() {
			var code, name, phase string
			var prio, effort int64
			rows2.Scan(&code, &name, &phase, &prio, &effort)
			indent := strings.Repeat("  ", int(level))
			fmt.Fprintf(w, "%s→ %s — %s [%s, P%d, %dd]\n", indent, code, name, phase, prio, effort)

			// Show deps
			deps, _ := db.Query(ctx, `SELECT dst_vid, dep_type FROM edge_depends_on WHERE src_vid = $1`, "action:"+code)
			for deps.Next() {
				var dep, dt string
				deps.Scan(&dep, &dt)
				fmt.Fprintf(w, "%s    ← depends: %s (%s)\n", indent, dep, dt)
			}
			deps.Close()
		}
		rows2.Close()
	}

	// Infra
	fmt.Fprintf(w, "\nINFRA:\n")
	rows3, _ := db.Query(ctx, `SELECT capability_code, display_name, status FROM vertex_infra_capability ORDER BY status DESC, capability_code`)
	defer rows3.Close()
	for rows3.Next() {
		var code, name, status string
		rows3.Scan(&code, &name, &status)
		icon := "⬜"
		if status == "deployed" {
			icon = "✅"
		} else if status == "built" {
			icon = "🔧"
		}
		fmt.Fprintf(w, "  %s %s — %s\n", icon, code, name)
	}

	return nil
}

func kaKPI(ctx context.Context, db *pgxpool.Pool, jsonOut bool) error {
	rows, _ := db.Query(ctx, `SELECT kpi_code, display_name, unit, direction, current_value, target_value, threshold_red, threshold_green FROM vertex_kpi ORDER BY kpi_code`)
	defer rows.Close()
	if jsonOut {
		return rowsToJSON(rows)
	}
	w := tabwriter.NewWriter(os.Stdout, 0, 4, 2, ' ', 0)
	defer w.Flush()
	fmt.Fprintf(w, "KPI\tCurrent\tTarget\tLight\tDirection\n")
	for rows.Next() {
		var code, name, unit, dir string
		var cur, tgt, red, green int64
		rows.Scan(&code, &name, &unit, &dir, &cur, &tgt, &red, &green)
		light := trafficLight(cur, red, green, dir)
		fmt.Fprintf(w, "%s\t%s\t%s\t%s\t%s\n", name, fmtVal(cur, unit), fmtVal(tgt, unit), light, dir)
	}
	return nil
}

func kaInbox(ctx context.Context, db *pgxpool.Pool, jsonOut bool) error {
	w := tabwriter.NewWriter(os.Stdout, 0, 4, 2, ' ', 0)
	defer w.Flush()

	// Email health
	var total, unread, noise, signal int64
	db.QueryRow(ctx, `SELECT total_30d, unread_30d, noise_30d, signal_30d FROM mv_inbox_health LIMIT 1`).Scan(&total, &unread, &noise, &signal)
	fmt.Fprintf(w, "【Email (30d)】\n  Total: %d / Unread: %d / Noise: %d / Signal: %d\n\n", total, unread, noise, signal)

	// Dept signals
	fmt.Fprintf(w, "【Kyber Dept Signals】\n")
	rows, _ := db.Query(ctx, `SELECT dept_code, signal_class, email_count, event_count, total_count FROM mv_kyber_dept_signals ORDER BY total_count DESC`)
	defer rows.Close()
	fmt.Fprintf(w, "  Dept\tClass\tEmail\tEvent\tTotal\n")
	for rows.Next() {
		var dept, cls string
		var email, event, total int64
		rows.Scan(&dept, &cls, &email, &event, &total)
		fmt.Fprintf(w, "  %s\t%s\t%d\t%d\t%d\n", dept, cls, email, event, total)
	}

	// Doc dedup
	var rowCount, dedup, logMB, physMB int64
	db.QueryRow(ctx, `SELECT row_count, dedup_hits, (logical_bytes/1024/1024)::BIGINT, (physical_bytes/1024/1024)::BIGINT FROM mv_blob_dedup_stats LIMIT 1`).Scan(&rowCount, &dedup, &logMB, &physMB)
	fmt.Fprintf(w, "\n【R2 Blob】\n  Docs: %d / Dedup: %d / Logical: %dMB / Physical: %dMB\n", rowCount, dedup, logMB, physMB)

	return nil
}

func kaSnapshot(ctx context.Context, db *pgxpool.Pool, jsonOut bool) error {
	now := time.Now().UTC().Format(time.RFC3339)
	today := now[:10]

	// Gather metrics
	var totalDocs, openRisks, openCases int64
	db.QueryRow(ctx, `SELECT COUNT(*) FROM vertex_office_document WHERE status = 'active'`).Scan(&totalDocs)
	db.QueryRow(ctx, `SELECT COUNT(*) FROM vertex_risk WHERE status IN ('open','mitigating')`).Scan(&openRisks)
	db.QueryRow(ctx, `SELECT COUNT(*) FROM vertex_business_case WHERE status != 'closed'`).Scan(&openCases)

	var totalRevenue, totalBurn int64
	db.QueryRow(ctx, `SELECT COALESCE(SUM(current_mrr_jpy), 0) FROM vertex_revenue_stream`).Scan(&totalRevenue)
	db.QueryRow(ctx, `SELECT COALESCE(SUM(monthly_burn_jpy), 0) FROM vertex_cost_center`).Scan(&totalBurn)

	vid := fmt.Sprintf("snap:%s", now)
	_, err := db.Exec(ctx,
		`INSERT INTO vertex_strategy_snapshot (vertex_id, owner_did, sensitivity_ord, created_date, snapshot_at, entity_code, total_documents, active_users, monthly_revenue_jpy, monthly_burn_jpy, net_margin_jpy, open_risks, open_cases, profit_months, generator) VALUES ($1, $2, 1, $3, $4, 'GJ', $5, 3, $6, $7, $8, $9, $10, 0, 'gftd-ka-cli')`,
		vid, "did:web:etzhayyim:ceo:j.kawasaki", today, now, totalDocs, totalRevenue, totalBurn, totalRevenue-totalBurn, openRisks, openCases)
	if err != nil {
		return fmt.Errorf("snapshot insert: %w", err)
	}
	fmt.Printf("✓ snapshot saved: %s (docs=%d rev=¥%s burn=¥%s net=¥%s risks=%d cases=%d)\n",
		vid, totalDocs, fmtJPY(totalRevenue), fmtJPY(totalBurn), fmtJPY(totalRevenue-totalBurn), openRisks, openCases)
	return nil
}

func kaTasks(ctx context.Context, db *pgxpool.Pool, jsonOut bool) error {
	w := tabwriter.NewWriter(os.Stdout, 0, 4, 2, ' ', 0)
	defer w.Flush()

	fmt.Fprintf(w, "═══ Human Computing Task Queue ═══\n\n")

	// Per-person summary
	fmt.Fprintf(w, "【タスク概要 (per person)】\n")
	rows, _ := db.Query(ctx, `SELECT assignee_role, assignee_did, pending_count, in_progress_count, completed_count, highest_priority, nearest_deadline FROM mv_human_task_queue ORDER BY pending_count DESC`)
	fmt.Fprintf(w, "  Role\tPending\tIn Progress\tDone\tMax P\tNearest Deadline\n")
	for rows.Next() {
		var role, did string
		var pending, inprog, done, maxP int64
		var deadline *string
		rows.Scan(&role, &did, &pending, &inprog, &done, &maxP, &deadline)
		dl := "-"
		if deadline != nil {
			dl = *deadline
		}
		fmt.Fprintf(w, "  %s\t%d\t%d\t%d\tP%d\t%s\n", role, pending, inprog, done, maxP, dl)
	}
	rows.Close()

	// Pending tasks
	fmt.Fprintf(w, "\n【Pending Tasks】\n")
	rows2, _ := db.Query(ctx, `SELECT task_code, title, assignee_role, priority, deadline, estimated_minutes, blocking_action, task_type FROM vertex_human_task WHERE status = 'pending' ORDER BY priority DESC, deadline ASC`)
	fmt.Fprintf(w, "  Task\tAssignee\tP\tDeadline\tMin\tBlocks\tType\n")
	for rows2.Next() {
		var code, title, role, ttype string
		var prio, mins int64
		var deadline, blocking *string
		rows2.Scan(&code, &title, &role, &prio, &deadline, &mins, &blocking, &ttype)
		dl := "-"
		if deadline != nil {
			dl = (*deadline)[:10]
		}
		bl := "-"
		if blocking != nil {
			bl = *blocking
		}
		fmt.Fprintf(w, "  %s\t%s\tP%d\t%s\t%dm\t%s\t%s\n", title, role, prio, dl, mins, bl, ttype)
	}
	rows2.Close()

	// Blocked actions
	fmt.Fprintf(w, "\n【Blocked Actions (waiting on human tasks)】\n")
	rows3, _ := db.Query(ctx, `SELECT action_code, action_name, task_title, assignee_role, task_status, deadline FROM mv_blocked_actions ORDER BY deadline ASC NULLS LAST`)
	fmt.Fprintf(w, "  Action\tBlocking Task\tAssignee\tTask Status\tDeadline\n")
	for rows3.Next() {
		var action, actionName, task, role, status string
		var deadline *string
		rows3.Scan(&action, &actionName, &task, &role, &status, &deadline)
		dl := "-"
		if deadline != nil {
			dl = (*deadline)[:10]
		}
		fmt.Fprintf(w, "  %s\t%s\t%s\t%s\t%s\n", actionName, task, role, status, dl)
	}
	rows3.Close()

	// Agent activity
	fmt.Fprintf(w, "\n【AI Agent Activity (recent)】\n")
	rows4, _ := db.Query(ctx, `SELECT agent_did, action_type, total_actions, success_count, last_action_at FROM mv_agent_activity_summary ORDER BY total_actions DESC`)
	fmt.Fprintf(w, "  Agent\tAction Type\tTotal\tSuccess\tLast\n")
	for rows4.Next() {
		var agent, atype string
		var total, success int64
		var last *string
		rows4.Scan(&agent, &atype, &total, &success, &last)
		l := "-"
		if last != nil {
			l = (*last)[:19]
		}
		name := strings.TrimPrefix(agent, "did:web:")
		fmt.Fprintf(w, "  %s\t%s\t%d\t%d\t%s\n", name, atype, total, success, l)
	}
	rows4.Close()

	return nil
}

func kaAssign(ctx context.Context, db *pgxpool.Pool, jsonOut bool) error {
	w := tabwriter.NewWriter(os.Stdout, 0, 4, 2, ' ', 0)
	defer w.Flush()

	fmt.Fprintf(w, "═══ Job Assignment Matrix (4人 × Streams) ═══\n\n")
	fmt.Fprintf(w, "Member\tRole\tPrimary Stream\tSecondary\tWeek 1-2 Action\n")
	fmt.Fprintf(w, "j.kawasaki\tProduct+Sales\tagent-match-sales\tyoro ad\tjk-6 SES委譲 + jk-2 GCC LOI\n")
	fmt.Fprintf(w, "a.nakamura\tOps+India\tagent-match engine\tTelnyx India\tan-1 SES inbox + an-2 DLT\n")
	fmt.Fprintf(w, "a.oda\tPlatform+LLM\tLLM usage\tyoro platform\tao-1 kyber deploy + ao-3 Arabic LLM\n")
	fmt.Fprintf(w, "gjcelaw\tLegal+Compliance\tlitigation\tGCC entity\tgc-1 鈴木和解 + gc-3 DMCC\n")

	// Meeting load
	fmt.Fprintf(w, "\n【会議負荷 (±14d)】\n")
	rows, _ := db.Query(ctx, `SELECT attendee_vid, meeting_count, total_hours FROM mv_calendar_meeting_load WHERE attendee_vid LIKE 'actor:%etzhayyim' ORDER BY total_hours DESC`)
	defer rows.Close()
	fmt.Fprintf(w, "  Attendee\tMeetings\tHours\n")
	for rows.Next() {
		var vid string
		var cnt int64
		var hrs float64
		rows.Scan(&vid, &cnt, &hrs)
		name := strings.TrimPrefix(vid, "actor:")
		fmt.Fprintf(w, "  %s\t%d\t%.1fh\n", name, cnt, hrs)
	}

	return nil
}

// ── Helpers ────────────────────────────────────────────────────────

func statusIcon(s string) string {
	switch s {
	case "active", "on_track", "deployed":
		return "🟢"
	case "ramping", "in_progress", "built", "planned":
		return "🟡"
	case "at_risk":
		return "🔴"
	case "divesting", "dormant":
		return "⚪"
	case "dissolved":
		return "⚫"
	default:
		return "⬜"
	}
}

func sevIcon(s string) string {
	switch s {
	case "critical":
		return "🔴"
	case "high":
		return "🟠"
	case "medium":
		return "🟡"
	default:
		return "🟢"
	}
}

func progressBar(val, max int) string {
	filled := val * 10 / max
	if filled > 10 {
		filled = 10
	}
	return "[" + strings.Repeat("█", filled) + strings.Repeat("░", 10-filled) + "]"
}

func trafficLight(cur, red, green int64, dir string) string {
	if dir == "down" {
		// For costs: lower is better
		if cur <= green {
			return "🟢"
		}
		if cur >= red {
			return "🔴"
		}
		return "🟡"
	}
	// For revenue/counts: higher is better
	if cur >= green {
		return "🟢"
	}
	if cur <= red {
		return "🔴"
	}
	return "🟡"
}

func fmtJPY(v int64) string {
	if v == 0 {
		return "0"
	}
	s := fmt.Sprintf("%d", v)
	if v < 0 {
		s = fmt.Sprintf("%d", -v)
	}
	// Insert commas
	n := len(s)
	if n <= 3 {
		if v < 0 {
			return "-" + s
		}
		return s
	}
	var parts []string
	for n > 0 {
		end := n
		start := n - 3
		if start < 0 {
			start = 0
		}
		parts = append([]string{s[start:end]}, parts...)
		n = start
	}
	result := strings.Join(parts, ",")
	if v < 0 {
		return "-" + result
	}
	return result
}

func fmtVal(v int64, unit string) string {
	switch unit {
	case "jpy":
		return "¥" + fmtJPY(v)
	default:
		return fmtJPY(v)
	}
}

func rowsToJSON(rows pgx.Rows) error {
	descs := rows.FieldDescriptions()
	var result []map[string]interface{}
	for rows.Next() {
		vals, err := rows.Values()
		if err != nil {
			continue
		}
		row := make(map[string]interface{})
		for i, d := range descs {
			row[string(d.Name)] = vals[i]
		}
		result = append(result, row)
	}
	enc := json.NewEncoder(os.Stdout)
	enc.SetIndent("", "  ")
	return enc.Encode(result)
}
