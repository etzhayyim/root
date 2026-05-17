// coverage_infer — Statistical entity resolution via Latent Discovery + Entity Resolution.
// Implements: gftd coverage infer [list|inspect|posterior|kdrift|discover|match|fission]
// Design: 90-docs/260416-coverage-infer-statistical-entity-resolution.md
package main

import (
	"bufio"
	"bytes"
	"context"
	"encoding/csv"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net/http"
	"os"
	"sort"
	"strings"
	"time"

	"github.com/etzhayyim/root/70-tools/gftd/gftd/db"
)

// inferCohortRow represents a cohort's posterior + evidence state from MVs.
type inferCohortRow struct {
	CohortDID          string  `json:"cohortDid"`
	EvidenceCount      int64   `json:"evidenceCount"`
	AvgPosterior       float64 `json:"avgPosterior"`
	MaxPosterior       float64 `json:"maxPosterior"`
	JudgeAgreeCount    int64   `json:"judgeAgreeCount"`
	FissionReadyCount  int64   `json:"fissionReadyCount"`
	LastEvidenceAt     string  `json:"lastEvidenceAt,omitempty"`
	DistinctSignals    int64   `json:"distinctSignals,omitempty"`
	KProxy             int64   `json:"kProxy,omitempty"`
	Grade              string  `json:"grade"`
}

// inferSummaryReport is the top-level report for coverage infer (default).
type inferSummaryReport struct {
	EvaluatedAt       string           `json:"evaluatedAt"`
	TotalCohorts      int              `json:"totalCohorts"`
	WithEvidence      int              `json:"withEvidence"`
	FissionReady      int              `json:"fissionReady"`
	KDriftWarnings    int              `json:"kDriftWarnings"`
	AvgPosterior      float64          `json:"avgPosterior"`
	Cohorts           []inferCohortRow `json:"cohorts,omitempty"`
}

// inferClusterRow represents a discovered latent cluster.
type inferClusterRow struct {
	VertexID    string `json:"vertexId"`
	ClusterID   int64  `json:"clusterId"`
	BatchID     string `json:"batchId"`
	Method      string `json:"method"`
	MemberCount int64  `json:"memberCount"`
	KAnonymity  int64  `json:"kAnonymity"`
	SegmentHash string `json:"segmentHash,omitempty"`
}

// inferMatchRow represents a cluster↔cohort match result.
type inferMatchRow struct {
	ClusterID  string  `json:"clusterId"`
	CohortDID  string  `json:"cohortDid"`
	Similarity float64 `json:"similarity"`
	Posterior  float64 `json:"posterior"`
	Status     string  `json:"status"`
}

func runCoverageInfer(args []string) error {
	if len(args) > 0 {
		switch args[0] {
		case "list":
			return runInferList(args[1:])
		case "inspect":
			return runInferInspect(args[1:])
		case "posterior":
			return runInferPosterior(args[1:])
		case "kdrift":
			return runInferKDrift(args[1:])
		case "discover":
			return runInferDiscover(args[1:])
		case "match":
			return runInferMatch(args[1:])
		case "fission":
			return runInferFission(args[1:])
		case "ingest":
			return runInferIngest(args[1:])
		case "materialize":
			return runInferMaterialize(args[1:])
		case "deps":
			return runInferDeps(args[1:])
		case "follow":
			return runInferFollow(args[1:])
		case "help", "--help", "-h":
			printInferUsage()
			return nil
		}
	}
	// Default: summary
	return runInferSummary(args)
}

func printInferUsage() {
	fmt.Println(`Usage: gftd coverage infer <subcommand> [flags]

Subcommands:
  (default)   Summary: all cohorts posterior + evidence + k-anonymity
  list        Detailed table (--grade, --json)
  inspect     Specific cohort evidence distribution (--did)
  posterior   mv_cohort_identity_posterior streaming state
  kdrift      mv_cohort_k_drift anomaly detection
  discover    Latent cluster discovery from statistical data (--input, --method)
  match       Cluster ↔ entity matching (--threshold)
  fission     Fission candidates (--dry-run)
  ingest      Ingest ILOSTAT CSV into vertex_talent_cohort (--input, --source)
  materialize Materialize clusters as actor DIDs (--batch-id)
  deps        Seed concept nodes + dependency edges (--seed-concepts, --input)
  follow      Auto-follow from dependency edges (--auto, --batch-id)

Flags (common):
  --json    JSON output

Flags (discover):
  --input   CSV/JSONL input file (required)
  --method  Clustering method: gmm (default)
  --k-min   Minimum k-anonymity per cluster (default: 50)

Flags (match):
  --threshold  Similarity threshold (default: 0.7)
  --batch-id   Filter by batch ID

Flags (fission):
  --dry-run   List candidates without executing`)
}

// runInferSummary shows a high-level summary of all cohorts.
func runInferSummary(args []string) error {
	fs := flag.NewFlagSet("coverage infer", flag.ContinueOnError)
	jsonOut := fs.Bool("json", false, "JSON output")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	// Query mv_cohort_identity_posterior
	posteriorSQL := `SELECT cohort_did, evidence_count, avg_posterior, max_posterior,
		judge_agree_count, fission_ready_count, last_evidence_at
		FROM mv_cohort_identity_posterior ORDER BY max_posterior DESC LIMIT 500`

	posteriorResp, err := db.RawQuery(ctx, posteriorSQL)
	if err != nil {
		return fmt.Errorf("mv_cohort_identity_posterior query: %w", err)
	}

	// Query mv_cohort_k_drift
	kdriftSQL := `SELECT cohort_did, distinct_signal_kinds, evidence_count, k_proxy
		FROM mv_cohort_k_drift ORDER BY k_proxy ASC LIMIT 500`

	kdriftResp, err := db.RawQuery(ctx, kdriftSQL)
	if err != nil {
		fmt.Fprintf(os.Stderr, "warn: mv_cohort_k_drift query failed (%v)\n", err)
	}

	// Build k-drift map
	kDriftMap := make(map[string]struct{ signals, kProxy int64 })
	if kdriftResp != nil {
		for _, row := range kdriftResp.Rows {
			did := anyStr(row["cohort_did"])
			kDriftMap[did] = struct{ signals, kProxy int64 }{
				signals: anyInt(row["distinct_signal_kinds"]),
				kProxy:  anyInt(row["k_proxy"]),
			}
		}
	}

	var cohorts []inferCohortRow
	var totalPosterior float64
	fissionReady := 0
	kDriftWarnings := 0

	for _, row := range posteriorResp.Rows {
		did := anyStr(row["cohort_did"])
		avgPost := anyFloat(row["avg_posterior"])
		maxPost := anyFloat(row["max_posterior"])
		evidenceCount := anyInt(row["evidence_count"])
		fissionCount := anyInt(row["fission_ready_count"])

		grade := "accreting"
		if fissionCount > 0 {
			grade = "fission-ready"
			fissionReady++
		} else if evidenceCount == 0 {
			grade = "genesis"
		}

		c := inferCohortRow{
			CohortDID:         did,
			EvidenceCount:     evidenceCount,
			AvgPosterior:      avgPost,
			MaxPosterior:      maxPost,
			JudgeAgreeCount:   anyInt(row["judge_agree_count"]),
			FissionReadyCount: fissionCount,
			LastEvidenceAt:    anyStr(row["last_evidence_at"]),
			Grade:             grade,
		}

		if kd, ok := kDriftMap[did]; ok {
			c.DistinctSignals = kd.signals
			c.KProxy = kd.kProxy
			if kd.kProxy < 50 && kd.kProxy > 0 {
				kDriftWarnings++
			}
		}

		cohorts = append(cohorts, c)
		totalPosterior += avgPost
	}

	avgPost := 0.0
	if len(cohorts) > 0 {
		avgPost = totalPosterior / float64(len(cohorts))
	}

	report := inferSummaryReport{
		EvaluatedAt:    time.Now().UTC().Format(time.RFC3339),
		TotalCohorts:   len(cohorts),
		WithEvidence:   countWithEvidence(cohorts),
		FissionReady:   fissionReady,
		KDriftWarnings: kDriftWarnings,
		AvgPosterior:   avgPost,
	}

	if *jsonOut {
		report.Cohorts = cohorts
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(report)
	}

	fmt.Println("Coverage Infer — Statistical Entity Resolution")
	fmt.Printf("  evaluated_at:    %s\n", report.EvaluatedAt)
	fmt.Printf("  total_cohorts:   %d\n", report.TotalCohorts)
	fmt.Printf("  with_evidence:   %d\n", report.WithEvidence)
	fmt.Printf("  fission_ready:   %d\n", report.FissionReady)
	fmt.Printf("  k_drift_warns:   %d\n", report.KDriftWarnings)
	fmt.Printf("  avg_posterior:   %.4f\n", report.AvgPosterior)
	fmt.Println()

	// Grades breakdown
	genesis, accreting, ready := 0, 0, 0
	for _, c := range cohorts {
		switch c.Grade {
		case "genesis":
			genesis++
		case "accreting":
			accreting++
		case "fission-ready":
			ready++
		}
	}
	fmt.Printf("  Phases:\n")
	fmt.Printf("    genesis:       %d\n", genesis)
	fmt.Printf("    accreting:     %d\n", accreting)
	fmt.Printf("    fission-ready: %d\n", ready)

	if kDriftWarnings > 0 {
		fmt.Printf("\n  WARNING: %d cohorts with k-anonymity drift (k_proxy < 50)\n", kDriftWarnings)
	}

	return nil
}

// runInferList shows per-cohort detailed table.
func runInferList(args []string) error {
	fs := flag.NewFlagSet("coverage infer list", flag.ContinueOnError)
	grade := fs.String("grade", "", "filter by grade: genesis, accreting, fission-ready")
	jsonOut := fs.Bool("json", false, "JSON output")
	limit := fs.Int("limit", 50, "max cohorts to display")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	sqlStmt := fmt.Sprintf(`SELECT cohort_did, evidence_count, avg_posterior, max_posterior,
		judge_agree_count, fission_ready_count, last_evidence_at
		FROM mv_cohort_identity_posterior ORDER BY max_posterior DESC LIMIT %d`, *limit)

	resp, err := db.RawQuery(ctx, sqlStmt)
	if err != nil {
		return fmt.Errorf("query: %w", err)
	}

	var cohorts []inferCohortRow
	for _, row := range resp.Rows {
		fissionCount := anyInt(row["fission_ready_count"])
		evidenceCount := anyInt(row["evidence_count"])
		g := "accreting"
		if fissionCount > 0 {
			g = "fission-ready"
		} else if evidenceCount == 0 {
			g = "genesis"
		}
		if *grade != "" && g != *grade {
			continue
		}
		cohorts = append(cohorts, inferCohortRow{
			CohortDID:         anyStr(row["cohort_did"]),
			EvidenceCount:     evidenceCount,
			AvgPosterior:      anyFloat(row["avg_posterior"]),
			MaxPosterior:      anyFloat(row["max_posterior"]),
			JudgeAgreeCount:   anyInt(row["judge_agree_count"]),
			FissionReadyCount: fissionCount,
			LastEvidenceAt:    anyStr(row["last_evidence_at"]),
			Grade:             g,
		})
	}

	if *jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(cohorts)
	}

	fmt.Printf("%-40s %-14s %6s %6s %5s %s\n", "COHORT_DID", "GRADE", "EVID", "MAX_P", "JUDGE", "LAST_AT")
	fmt.Printf("%-40s %-14s %6s %6s %5s %s\n",
		strings.Repeat("─", 40), strings.Repeat("─", 14), "──────", "──────", "─────", strings.Repeat("─", 20))
	for _, c := range cohorts {
		did := c.CohortDID
		if len(did) > 40 {
			did = did[:37] + "..."
		}
		fmt.Printf("%-40s %-14s %6d %6.3f %5d %s\n",
			did, c.Grade, c.EvidenceCount, c.MaxPosterior, c.JudgeAgreeCount, c.LastEvidenceAt)
	}
	return nil
}

// runInferInspect shows evidence distribution for a specific cohort.
func runInferInspect(args []string) error {
	fs := flag.NewFlagSet("coverage infer inspect", flag.ContinueOnError)
	did := fs.String("did", "", "cohort DID to inspect (required)")
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

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	// Evidence breakdown by signal_kind
	sqlStmt := fmt.Sprintf(
		`SELECT signal_kind, COUNT(*)::BIGINT AS cnt, AVG(posterior)::DOUBLE PRECISION AS avg_p,
			MAX(posterior)::DOUBLE PRECISION AS max_p,
			SUM(CASE WHEN judge_agreement THEN 1 ELSE 0 END)::BIGINT AS judge_yes
		FROM vertex_repo_record
		WHERE collection = 'ai.gftd.cohort.evidence' AND cohort_did = '%s'
		GROUP BY signal_kind ORDER BY cnt DESC LIMIT 100`,
		strings.ReplaceAll(targetDID, "'", "''"),
	)

	resp, err := db.RawQuery(ctx, sqlStmt)
	if err != nil {
		return fmt.Errorf("evidence query: %w", err)
	}

	type signalBreakdown struct {
		SignalKind    string  `json:"signalKind"`
		Count        int64   `json:"count"`
		AvgPosterior float64 `json:"avgPosterior"`
		MaxPosterior float64 `json:"maxPosterior"`
		JudgeYes     int64   `json:"judgeYes"`
	}
	var signals []signalBreakdown
	for _, row := range resp.Rows {
		signals = append(signals, signalBreakdown{
			SignalKind:    anyStr(row["signal_kind"]),
			Count:        anyInt(row["cnt"]),
			AvgPosterior: anyFloat(row["avg_p"]),
			MaxPosterior: anyFloat(row["max_p"]),
			JudgeYes:     anyInt(row["judge_yes"]),
		})
	}

	if *jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(map[string]any{
			"cohortDid": targetDID,
			"signals":   signals,
		})
	}

	fmt.Printf("Evidence distribution for %s\n\n", targetDID)
	if len(signals) == 0 {
		fmt.Println("  (no evidence found)")
		return nil
	}
	fmt.Printf("%-25s %6s %8s %8s %5s\n", "SIGNAL_KIND", "COUNT", "AVG_POST", "MAX_POST", "JUDGE")
	fmt.Printf("%-25s %6s %8s %8s %5s\n",
		strings.Repeat("─", 25), "──────", "────────", "────────", "─────")
	for _, s := range signals {
		fmt.Printf("%-25s %6d %8.4f %8.4f %5d\n",
			s.SignalKind, s.Count, s.AvgPosterior, s.MaxPosterior, s.JudgeYes)
	}
	return nil
}

// runInferPosterior shows mv_cohort_identity_posterior state.
func runInferPosterior(args []string) error {
	fs := flag.NewFlagSet("coverage infer posterior", flag.ContinueOnError)
	jsonOut := fs.Bool("json", false, "JSON output")
	limit := fs.Int("limit", 30, "max rows")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	sqlStmt := fmt.Sprintf(`SELECT cohort_did, evidence_count, avg_posterior, max_posterior,
		judge_agree_count, fission_ready_count, last_evidence_at
		FROM mv_cohort_identity_posterior ORDER BY max_posterior DESC LIMIT %d`, *limit)

	resp, err := db.RawQuery(ctx, sqlStmt)
	if err != nil {
		return fmt.Errorf("query: %w", err)
	}

	if *jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(resp.Rows)
	}

	fmt.Printf("mv_cohort_identity_posterior (%d rows)\n\n", len(resp.Rows))
	fmt.Printf("%-40s %6s %8s %8s %5s %5s\n", "COHORT_DID", "EVID", "AVG_P", "MAX_P", "JUDGE", "FISS")
	fmt.Printf("%-40s %6s %8s %8s %5s %5s\n",
		strings.Repeat("─", 40), "──────", "────────", "────────", "─────", "─────")
	for _, row := range resp.Rows {
		did := anyStr(row["cohort_did"])
		if len(did) > 40 {
			did = did[:37] + "..."
		}
		fmt.Printf("%-40s %6s %8s %8s %5s %5s\n",
			did,
			anyStr(row["evidence_count"]),
			fmtFloat(anyFloat(row["avg_posterior"]), 4),
			fmtFloat(anyFloat(row["max_posterior"]), 4),
			anyStr(row["judge_agree_count"]),
			anyStr(row["fission_ready_count"]),
		)
	}
	return nil
}

// runInferKDrift shows k-anonymity drift detection.
func runInferKDrift(args []string) error {
	fs := flag.NewFlagSet("coverage infer kdrift", flag.ContinueOnError)
	jsonOut := fs.Bool("json", false, "JSON output")
	limit := fs.Int("limit", 30, "max rows")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	sqlStmt := fmt.Sprintf(`SELECT cohort_did, distinct_signal_kinds, evidence_count, k_proxy
		FROM mv_cohort_k_drift ORDER BY k_proxy ASC LIMIT %d`, *limit)

	resp, err := db.RawQuery(ctx, sqlStmt)
	if err != nil {
		return fmt.Errorf("query: %w", err)
	}

	if *jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(resp.Rows)
	}

	fmt.Printf("mv_cohort_k_drift (%d rows)\n\n", len(resp.Rows))
	warnings := 0
	fmt.Printf("%-40s %8s %6s %6s %s\n", "COHORT_DID", "SIGNALS", "EVID", "K_PROX", "STATUS")
	fmt.Printf("%-40s %8s %6s %6s %s\n",
		strings.Repeat("─", 40), "────────", "──────", "──────", strings.Repeat("─", 10))
	for _, row := range resp.Rows {
		did := anyStr(row["cohort_did"])
		if len(did) > 40 {
			did = did[:37] + "..."
		}
		kProxy := anyInt(row["k_proxy"])
		status := "ok"
		if kProxy < 50 && kProxy > 0 {
			status = "DRIFT"
			warnings++
		}
		fmt.Printf("%-40s %8s %6s %6d %s\n",
			did,
			anyStr(row["distinct_signal_kinds"]),
			anyStr(row["evidence_count"]),
			kProxy,
			status,
		)
	}
	if warnings > 0 {
		fmt.Printf("\n  WARNING: %d cohorts below k=50 threshold\n", warnings)
	}
	return nil
}

// runInferDiscover reads statistical data and discovers latent clusters via GMM.
func runInferDiscover(args []string) error {
	fs := flag.NewFlagSet("coverage infer discover", flag.ContinueOnError)
	inputFile := fs.String("input", "", "CSV/JSONL input file (required)")
	method := fs.String("method", "gmm", "clustering method: gmm")
	kParam := fs.Int("k", 0, "number of clusters (0 = auto-select via elbow)")
	kMin := fs.Int("k-min", 50, "minimum k-anonymity per cluster")
	seed := fs.Int64("seed", 42, "random seed for reproducibility")
	skipDB := fs.Bool("local", false, "local-only mode: skip DB writes, print results only")
	jsonOut := fs.Bool("json", false, "JSON output")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	if *inputFile == "" {
		return fmt.Errorf("--input is required")
	}

	// ── 1. Parse CSV ────────────────────────────────────────────────────────
	f, err := os.Open(*inputFile)
	if err != nil {
		return fmt.Errorf("open %s: %w", *inputFile, err)
	}
	defer f.Close()

	reader := csv.NewReader(f)
	reader.TrimLeadingSpace = true
	header, err := reader.Read()
	if err != nil {
		return fmt.Errorf("read CSV header: %w", err)
	}

	var rawRows [][]string
	for {
		record, err := reader.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			return fmt.Errorf("read CSV row %d: %w", len(rawRows)+1, err)
		}
		rawRows = append(rawRows, record)
	}

	if len(rawRows) == 0 {
		return fmt.Errorf("CSV has no data rows")
	}

	// ── 2. Convert to float64 feature matrix ────────────────────────────────
	data, numericCols, skippedCols := parseCSVToFeatures(rawRows, header)
	if len(data) == 0 || len(data[0]) == 0 {
		return fmt.Errorf("no numeric features found in CSV (columns: %v)", header)
	}

	dims := len(data[0])
	fmt.Fprintf(os.Stderr, "Parsed %d rows x %d numeric features", len(data), dims)
	if len(skippedCols) > 0 {
		fmt.Fprintf(os.Stderr, " (skipped non-numeric: %s)", strings.Join(skippedCols, ", "))
	}
	fmt.Fprintln(os.Stderr)

	// ── 3. Auto-select k if not specified ───────────────────────────────────
	k := *kParam
	if k <= 0 {
		k = AutoSelectK(data, 0, *seed)
		fmt.Fprintf(os.Stderr, "Auto-selected k=%d (elbow method)\n", k)
	}

	// ── 4. Run GMM (k-means + soft assignment) ──────────────────────────────
	result, err := RunGMM(data, GMMOptions{
		K:       k,
		MaxIter: 200,
		Seed:    *seed,
	})
	if err != nil {
		return fmt.Errorf("GMM failed: %w", err)
	}

	batchID := fmt.Sprintf("infer-%s", time.Now().UTC().Format("20060102T150405"))

	fmt.Fprintf(os.Stderr, "GMM converged in %d iterations (inertia=%.2f)\n", result.Iterations, result.Inertia)

	// ── 5. Check k-anonymity ────────────────────────────────────────────────
	kWarnings := 0
	for _, cl := range result.Clusters {
		if cl.MemberCount < *kMin {
			kWarnings++
			fmt.Fprintf(os.Stderr, "warn: cluster %d has %d members (below k-min=%d)\n",
				cl.ID, cl.MemberCount, *kMin)
		}
	}

	// ── 6. Build output rows ────────────────────────────────────────────────
	var clusters []inferClusterRow
	for _, cl := range result.Clusters {
		kAnon := int64(cl.MemberCount)
		clusters = append(clusters, inferClusterRow{
			VertexID:    fmt.Sprintf("infer-cluster:%s:%d", batchID, cl.ID),
			ClusterID:   int64(cl.ID),
			BatchID:     batchID,
			Method:      *method,
			MemberCount: int64(cl.MemberCount),
			KAnonymity:  kAnon,
		})
	}

	// ── 7. Write to DB (unless --local) ─────────────────────────────────────
	if !*skipDB {
		ctx, cancel := context.WithTimeout(context.Background(), 120*time.Second)
		defer cancel()

		// Insert input rows
		for i, row := range rawRows {
			vertexID := fmt.Sprintf("infer-input:%s:%d", batchID, i)
			featuresStr := "[" + strings.Join(row, ",") + "]"
			featureNames := "[\"" + strings.Join(header, "\",\"") + "\"]"
			clusterLabel := fmt.Sprintf("%d", result.Assignments[i])

			insertSQL := fmt.Sprintf(
				`INSERT INTO vertex_infer_input (vertex_id, source_type, source_file, features, feature_names, label, batch_id, created_date)
				 VALUES ('%s', 'csv', '%s', '%s', '%s', '%s', '%s', now())`,
				escape(vertexID), escape(*inputFile), escape(featuresStr),
				escape(featureNames), clusterLabel, batchID,
			)
			if _, err := db.RawQuery(ctx, insertSQL); err != nil {
				return fmt.Errorf("insert row %d: %w", i, err)
			}
		}

		// Insert clusters
		for _, cl := range clusters {
			centroidJSON := formatFloatSlice(result.Clusters[cl.ClusterID].Centroid)
			insertSQL := fmt.Sprintf(
				`INSERT INTO vertex_infer_cluster (vertex_id, cluster_id, batch_id, method, member_count, k_anonymity, features_avg, created_date, status)
				 VALUES ('%s', %d, '%s', '%s', %d, %d, '%s', now(), 'active')`,
				escape(cl.VertexID), cl.ClusterID, batchID, *method,
				cl.MemberCount, cl.KAnonymity, escape(centroidJSON),
			)
			if _, err := db.RawQuery(ctx, insertSQL); err != nil {
				fmt.Fprintf(os.Stderr, "warn: insert cluster %d: %v\n", cl.ClusterID, err)
			}
		}

		if _, err := db.RawQuery(ctx, "FLUSH"); err != nil {
			fmt.Fprintf(os.Stderr, "warn: FLUSH failed: %v\n", err)
		}

		fmt.Fprintf(os.Stderr, "Wrote %d input rows + %d clusters to DB (batch=%s)\n",
			len(rawRows), len(clusters), batchID)
	}

	// ── 8. Output ───────────────────────────────────────────────────────────
	if *jsonOut {
		// Build centroid details
		type clusterDetail struct {
			inferClusterRow
			Centroid []float64 `json:"centroid"`
			Variance float64   `json:"variance"`
		}
		details := make([]clusterDetail, len(clusters))
		for i, cl := range clusters {
			details[i] = clusterDetail{
				inferClusterRow: cl,
				Centroid:        result.Clusters[i].Centroid,
				Variance:        result.Clusters[i].Variance,
			}
		}
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(map[string]any{
			"batchId":       batchID,
			"method":        *method,
			"rows":          len(rawRows),
			"k":             result.K,
			"iterations":    result.Iterations,
			"inertia":       result.Inertia,
			"kMin":          *kMin,
			"kWarnings":     kWarnings,
			"numericCols":   numericCols,
			"skippedCols":   skippedCols,
			"clusters":      details,
		})
	}

	fmt.Printf("\nDiscovered %d clusters from %d rows (method=%s, k=%d, batch=%s)\n",
		len(clusters), len(rawRows), *method, result.K, batchID)
	fmt.Printf("Iterations: %d, Inertia: %.2f\n", result.Iterations, result.Inertia)
	if kWarnings > 0 {
		fmt.Printf("WARNING: %d clusters below k-min=%d\n", kWarnings, *kMin)
	}
	fmt.Printf("\n%-8s %8s %8s %10s  %s\n", "CLUSTER", "MEMBERS", "K_ANON", "VARIANCE", "CENTROID (first 5 dims)")
	fmt.Printf("%-8s %8s %8s %10s  %s\n",
		"────────", "────────", "────────", "──────────", strings.Repeat("─", 30))
	for i, cl := range clusters {
		centroid := result.Clusters[i].Centroid
		centroidStr := formatCentroidPreview(centroid, 5)
		fmt.Printf("%-8d %8d %8d %10.4f  %s\n",
			cl.ClusterID, cl.MemberCount, cl.KAnonymity,
			result.Clusters[i].Variance, centroidStr)
	}
	return nil
}

// parseCSVToFeatures converts CSV rows to float64 feature vectors,
// skipping non-numeric columns.
func parseCSVToFeatures(rows [][]string, header []string) ([][]float64, []string, []string) {
	if len(rows) == 0 {
		return nil, nil, nil
	}

	cols := len(header)
	// Detect which columns are numeric by scanning first 10 rows
	isNumeric := make([]bool, cols)
	scanRows := rows
	if len(scanRows) > 10 {
		scanRows = scanRows[:10]
	}
	for c := 0; c < cols; c++ {
		allNumeric := true
		for _, row := range scanRows {
			if c >= len(row) {
				continue
			}
			v := strings.TrimSpace(row[c])
			if v == "" || v == "NA" || v == "N/A" || v == "-" {
				continue // skip missing
			}
			var f float64
			if _, err := fmt.Sscanf(v, "%f", &f); err != nil {
				allNumeric = false
				break
			}
		}
		isNumeric[c] = allNumeric
	}

	var numericCols, skippedCols []string
	numericIdx := make([]int, 0)
	for c := 0; c < cols; c++ {
		if isNumeric[c] {
			numericCols = append(numericCols, header[c])
			numericIdx = append(numericIdx, c)
		} else {
			skippedCols = append(skippedCols, header[c])
		}
	}

	data := make([][]float64, 0, len(rows))
	for _, row := range rows {
		vec := make([]float64, len(numericIdx))
		valid := false
		for i, c := range numericIdx {
			if c < len(row) {
				v := strings.TrimSpace(row[c])
				var f float64
				if _, err := fmt.Sscanf(v, "%f", &f); err == nil {
					vec[i] = f
					valid = true
				}
			}
		}
		if valid {
			data = append(data, vec)
		}
	}

	return data, numericCols, skippedCols
}

func escape(s string) string {
	return strings.ReplaceAll(s, "'", "''")
}

func formatFloatSlice(v []float64) string {
	parts := make([]string, len(v))
	for i, f := range v {
		parts[i] = fmt.Sprintf("%.6f", f)
	}
	return "[" + strings.Join(parts, ",") + "]"
}

func formatCentroidPreview(centroid []float64, maxDims int) string {
	n := len(centroid)
	if n > maxDims {
		n = maxDims
	}
	parts := make([]string, n)
	for i := 0; i < n; i++ {
		parts[i] = fmt.Sprintf("%.2f", centroid[i])
	}
	s := "[" + strings.Join(parts, ", ")
	if len(centroid) > maxDims {
		s += fmt.Sprintf(", ...+%d", len(centroid)-maxDims)
	}
	s += "]"
	return s
}

// runInferMatch matches discovered clusters against existing cohort actors.
func runInferMatch(args []string) error {
	fs := flag.NewFlagSet("coverage infer match", flag.ContinueOnError)
	threshold := fs.Float64("threshold", 0.7, "similarity threshold")
	batchID := fs.String("batch-id", "", "filter by batch ID (latest if empty)")
	jsonOut := fs.Bool("json", false, "JSON output")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	ctx, cancel := context.WithTimeout(context.Background(), 60*time.Second)
	defer cancel()

	// Find latest batch if not specified
	batch := *batchID
	if batch == "" {
		latestSQL := `SELECT batch_id FROM vertex_infer_cluster ORDER BY created_date DESC LIMIT 1`
		resp, err := db.RawQuery(ctx, latestSQL)
		if err != nil || len(resp.Rows) == 0 {
			return fmt.Errorf("no clusters found. Run 'gftd coverage infer discover' first")
		}
		batch = anyStr(resp.Rows[0]["batch_id"])
	}

	// Fetch clusters
	clusterSQL := fmt.Sprintf(
		`SELECT vertex_id, cluster_id, member_count, features_avg, segment_hash
		 FROM vertex_infer_cluster WHERE batch_id = '%s' AND status = 'active' LIMIT 100`,
		strings.ReplaceAll(batch, "'", "''"),
	)
	clusterResp, err := db.RawQuery(ctx, clusterSQL)
	if err != nil {
		return fmt.Errorf("cluster query: %w", err)
	}

	// Fetch cohort actors
	cohortSQL := `SELECT cohort_did, segment_hash, k_anonymity FROM vertex_cohort_actor
		WHERE status = 'active' LIMIT 1000`
	cohortResp, err := db.RawQuery(ctx, cohortSQL)
	if err != nil {
		return fmt.Errorf("cohort query: %w", err)
	}

	var matches []inferMatchRow
	matchCount := 0

	for _, cl := range clusterResp.Rows {
		clusterID := anyStr(cl["vertex_id"])
		clSegHash := anyStr(cl["segment_hash"])

		for _, co := range cohortResp.Rows {
			cohortDID := anyStr(co["cohort_did"])
			coSegHash := anyStr(co["segment_hash"])

			// Segment hash exact match = 1.0 similarity
			similarity := 0.0
			if clSegHash != "" && coSegHash != "" && clSegHash == coSegHash {
				similarity = 1.0
			}

			if similarity >= *threshold {
				matchVertexID := fmt.Sprintf("infer-match:%s:%s:%d", batch, cohortDID, matchCount)
				m := inferMatchRow{
					ClusterID:  clusterID,
					CohortDID:  cohortDID,
					Similarity: similarity,
					Posterior:  similarity, // Initial posterior = similarity as prior
					Status:     "candidate",
				}
				matches = append(matches, m)

				insertSQL := fmt.Sprintf(
					`INSERT INTO vertex_infer_match (vertex_id, cluster_id, cohort_did, similarity, posterior, match_method, batch_id, created_date, status)
					 VALUES ('%s', '%s', '%s', %f, %f, 'segment_hash', '%s', now(), 'candidate')`,
					matchVertexID,
					strings.ReplaceAll(clusterID, "'", "''"),
					strings.ReplaceAll(cohortDID, "'", "''"),
					similarity, similarity, batch,
				)
				if _, err := db.RawQuery(ctx, insertSQL); err != nil {
					fmt.Fprintf(os.Stderr, "warn: insert match: %v\n", err)
				}
				matchCount++
			}
		}
	}

	if _, err := db.RawQuery(ctx, "FLUSH"); err != nil {
		fmt.Fprintf(os.Stderr, "warn: FLUSH failed: %v\n", err)
	}

	if *jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(map[string]any{
			"batchId":   batch,
			"threshold": *threshold,
			"matches":   matches,
		})
	}

	fmt.Printf("Match results (batch=%s, threshold=%.2f)\n\n", batch, *threshold)
	if len(matches) == 0 {
		fmt.Println("  (no matches found above threshold)")
		return nil
	}
	fmt.Printf("%-35s %-35s %8s %8s %s\n", "CLUSTER", "COHORT_DID", "SIMILAR", "POST", "STATUS")
	fmt.Printf("%-35s %-35s %8s %8s %s\n",
		strings.Repeat("─", 35), strings.Repeat("─", 35), "────────", "────────", strings.Repeat("─", 10))
	for _, m := range matches {
		cl := m.ClusterID
		if len(cl) > 35 {
			cl = cl[:32] + "..."
		}
		co := m.CohortDID
		if len(co) > 35 {
			co = co[:32] + "..."
		}
		fmt.Printf("%-35s %-35s %8.4f %8.4f %s\n", cl, co, m.Similarity, m.Posterior, m.Status)
	}
	return nil
}

// runInferFission lists fission candidates (posterior > 0.95 + judge agreement).
func runInferFission(args []string) error {
	fs := flag.NewFlagSet("coverage infer fission", flag.ContinueOnError)
	dryRun := fs.Bool("dry-run", true, "list candidates without executing")
	jsonOut := fs.Bool("json", false, "JSON output")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	sqlStmt := `SELECT cohort_did, max_posterior, fission_ready_count, evidence_count
		FROM mv_cohort_identity_posterior
		WHERE max_posterior > 0.95 AND fission_ready_count >= 1
		ORDER BY max_posterior DESC LIMIT 100`

	resp, err := db.RawQuery(ctx, sqlStmt)
	if err != nil {
		return fmt.Errorf("fission query: %w", err)
	}

	if *jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(map[string]any{
			"dryRun":     *dryRun,
			"candidates": resp.Rows,
		})
	}

	fmt.Printf("Fission candidates (dry-run=%v)\n\n", *dryRun)
	if len(resp.Rows) == 0 {
		fmt.Println("  (no fission-ready cohorts)")
		return nil
	}
	fmt.Printf("%-40s %8s %6s %6s\n", "COHORT_DID", "MAX_POST", "FISS_R", "EVID")
	fmt.Printf("%-40s %8s %6s %6s\n",
		strings.Repeat("─", 40), "────────", "──────", "──────")
	for _, row := range resp.Rows {
		did := anyStr(row["cohort_did"])
		if len(did) > 40 {
			did = did[:37] + "..."
		}
		fmt.Printf("%-40s %8s %6s %6s\n",
			did, fmtFloat(anyFloat(row["max_posterior"]), 4),
			anyStr(row["fission_ready_count"]),
			anyStr(row["evidence_count"]),
		)
	}

	if !*dryRun {
		fmt.Println("\n  Fission execution requires: gftd cohort fission --did <cohort_did>")
		fmt.Println("  (delegated to existing cohort fission pipeline)")
	}
	return nil
}

// Helpers

func countWithEvidence(cohorts []inferCohortRow) int {
	n := 0
	for _, c := range cohorts {
		if c.EvidenceCount > 0 {
			n++
		}
	}
	return n
}

func anyInt(v any) int64 {
	if v == nil {
		return 0
	}
	switch x := v.(type) {
	case int64:
		return x
	case float64:
		return int64(x)
	case json.Number:
		n, _ := x.Int64()
		return n
	case string:
		var n int64
		fmt.Sscanf(x, "%d", &n)
		return n
	default:
		return 0
	}
}

func anyFloat(v any) float64 {
	if v == nil {
		return 0
	}
	switch x := v.(type) {
	case float64:
		return x
	case int64:
		return float64(x)
	case json.Number:
		f, _ := x.Float64()
		return f
	case string:
		var f float64
		fmt.Sscanf(x, "%f", &f)
		return f
	default:
		return 0
	}
}

func fmtFloat(f float64, prec int) string {
	return fmt.Sprintf("%.*f", prec, f)
}

// runInferIngest ingests ILOSTAT SDMX CSV into vertex_talent_cohort.
// Expected CSV format: DATAFLOW,REF_AREA,FREQ,MEASURE,SEX,OCU,TIME_PERIOD,OBS_VALUE,...
func runInferIngest(args []string) error {
	fs := flag.NewFlagSet("coverage infer ingest", flag.ContinueOnError)
	inputFile := fs.String("input", "", "ILOSTAT SDMX CSV file (required)")
	source := fs.String("source", "ilostat", "data source label")
	dryRun := fs.Bool("dry-run", false, "parse and validate only, skip DB writes")
	jsonOut := fs.Bool("json", false, "JSON output")
	batchSize := fs.Int("batch-size", 100, "rows per request (XRPC sink) or per progress tick (direct SQL)")
	xrpcSink := fs.Bool("xrpc-sink", true, "POST rows to ai.gftd.apps.coverage.inferIngest via BPMN-as-actor (ADR-0056). Uses generic.db.bulkInsert: single multi-row INSERT, 10/10 row reliability confirmed. Set false to fall back to legacy direct-INSERT path.")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	if *inputFile == "" {
		// Auto-download from ILOSTAT if no file specified
		return fmt.Errorf("--input is required.\n\nTo download ILOSTAT data:\n  curl -sL 'https://sdmx.ilo.org/rest/data/ILO,DF_EMP_2EMP_SEX_OCU_NB,1.0/all?startPeriod=2020&endPeriod=2024&dimensionAtObservation=AllDimensions' \\\n    -H 'Accept: application/vnd.sdmx.data+csv' -o ilostat_emp_ocu.csv")
	}

	f, err := os.Open(*inputFile)
	if err != nil {
		return fmt.Errorf("open %s: %w", *inputFile, err)
	}
	defer f.Close()

	reader := csv.NewReader(f)
	reader.LazyQuotes = true
	header, err := reader.Read()
	if err != nil {
		return fmt.Errorf("read header: %w", err)
	}

	// Map column names to indices
	colIdx := make(map[string]int)
	for i, h := range header {
		colIdx[strings.TrimSpace(h)] = i
	}

	// Support both ILOSTAT SDMX format and generic CSV format
	// ILOSTAT: REF_AREA, SEX, OCU, TIME_PERIOD, OBS_VALUE
	// Generic: country, sex, isco_code, time_period, size_thousands
	colAliases := map[string][]string{
		"REF_AREA":    {"REF_AREA", "country", "geo", "COUNTRY"},
		"SEX":         {"SEX", "sex"},
		"OCU":         {"OCU", "isco_code", "isco", "ISCO08"},
		"TIME_PERIOD": {"TIME_PERIOD", "time_period", "year", "YEAR"},
		"OBS_VALUE":   {"OBS_VALUE", "size_thousands", "value", "VALUE"},
	}
	resolvedCol := make(map[string]int)
	for canonical, aliases := range colAliases {
		for _, alias := range aliases {
			if idx, ok := colIdx[alias]; ok {
				resolvedCol[canonical] = idx
				break
			}
		}
	}
	for _, r := range []string{"REF_AREA", "SEX", "OCU", "TIME_PERIOD", "OBS_VALUE"} {
		if _, ok := resolvedCol[r]; !ok {
			return fmt.Errorf("missing required column: %s (tried aliases: %v, found: %v)", r, colAliases[r], header)
		}
	}
	colIdx = resolvedCol

	var rows []talentRow
	lineNum := 1
	skipped := 0
	for {
		record, err := reader.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			lineNum++
			skipped++
			continue
		}
		lineNum++

		country := record[colIdx["REF_AREA"]]
		sex := record[colIdx["SEX"]]
		ocu := record[colIdx["OCU"]]
		timePeriod := record[colIdx["TIME_PERIOD"]]
		obsValueStr := strings.TrimSpace(record[colIdx["OBS_VALUE"]])

		// Skip TOTAL aggregates and empty values
		if ocu == "OCU_ISCO08_TOTAL" || obsValueStr == "" {
			skipped++
			continue
		}

		var obsValue float64
		if _, err := fmt.Sscanf(obsValueStr, "%f", &obsValue); err != nil {
			skipped++
			continue
		}

		// Normalize ISCO code: OCU_ISCO08_1 → 1, OCU_ISCO08_96 → 96
		iscoCode := strings.TrimPrefix(ocu, "OCU_ISCO08_")
		if iscoCode == ocu {
			iscoCode = ocu // Keep original if no prefix
		}

		// Normalize sex: SEX_T → T, SEX_M → M, SEX_F → F
		sexNorm := strings.TrimPrefix(sex, "SEX_")

		rows = append(rows, talentRow{
			Country:    country,
			Sex:        sexNorm,
			ISCOCode:   iscoCode,
			TimePeriod: timePeriod,
			SizeK:      obsValue,
		})
	}

	fmt.Fprintf(os.Stderr, "Parsed %d rows (%d skipped) from %s\n", len(rows), skipped, *inputFile)

	// Stats
	countries := make(map[string]bool)
	iscoCodes := make(map[string]bool)
	periods := make(map[string]bool)
	for _, r := range rows {
		countries[r.Country] = true
		iscoCodes[r.ISCOCode] = true
		periods[r.TimePeriod] = true
	}
	fmt.Fprintf(os.Stderr, "  countries: %d, ISCO codes: %d, periods: %v\n",
		len(countries), len(iscoCodes), sortedKeys(periods))

	if *dryRun {
		fmt.Fprintf(os.Stderr, "  (dry-run: skipping DB writes)\n")
		if *jsonOut {
			enc := json.NewEncoder(os.Stdout)
			enc.SetIndent("", "  ")
			return enc.Encode(map[string]any{
				"source":    *source,
				"rows":      len(rows),
				"countries": len(countries),
				"iscoCodes": sortedKeys(iscoCodes),
				"periods":   sortedKeys(periods),
				"sample":    rows[:min10(10, len(rows))],
			})
		}
		return nil
	}

	// Write path: ADR-0056 BPMN actor (default) or legacy direct SQL.
	ctx, cancel := context.WithTimeout(context.Background(), 300*time.Second)
	defer cancel()

	var inserted, errCount int
	if *xrpcSink {
		inserted, errCount = ingestViaXRPC(ctx, *source, rows, *batchSize)
	} else {
		fmt.Fprintf(os.Stderr, "warn: --xrpc-sink=false uses the legacy direct-INSERT path (deprecated; the BPMN actor `ai.gftd.apps.coverage.inferIngest` is the canonical sink under ADR-0056)\n")
		inserted, errCount = ingestViaDirectSQL(ctx, *source, rows)
	}

	fmt.Fprintf(os.Stderr, "Ingested %d rows into vertex_talent_cohort (%d errors)\n", inserted, errCount)

	if *jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(map[string]any{
			"source":    *source,
			"inserted":  inserted,
			"errors":    errCount,
			"countries": len(countries),
			"iscoCodes": sortedKeys(iscoCodes),
			"periods":   sortedKeys(periods),
		})
	}

	fmt.Printf("\nILOSTAT Ingest Complete\n")
	fmt.Printf("  source:     %s\n", *source)
	fmt.Printf("  inserted:   %d\n", inserted)
	fmt.Printf("  errors:     %d\n", errCount)
	fmt.Printf("  countries:  %d\n", len(countries))
	fmt.Printf("  ISCO codes: %v\n", sortedKeys(iscoCodes))
	fmt.Printf("  periods:    %v\n", sortedKeys(periods))
	return nil
}

// talentRow is the canonical ILOSTAT cohort row shape (matches the
// `ai.gftd.apps.coverage.inferIngest` lexicon input). JSON tags double as
// XRPC payload keys.
type talentRow struct {
	Country    string  `json:"country"`
	Sex        string  `json:"sex"`
	ISCOCode   string  `json:"iscoCode"`
	TimePeriod string  `json:"timePeriod"`
	SizeK      float64 `json:"sizeThousands"`
}

// ingestViaXRPC POSTs rows in batches to ai.gftd.apps.coverage.inferIngest
// (BPMN-as-actor sink, ADR-0056). PDS pipethroughs to dispatcher.etzhayyim.com
// with the internal-trust header on our behalf, so the CLI just needs the
// usual `gftd authn signin` Bearer token.
func ingestViaXRPC(ctx context.Context, source string, rows []talentRow, batchSize int) (int, int) {
	if batchSize <= 0 {
		batchSize = 100
	}
	endpoint := strings.TrimRight(resolvePDSBaseURL(), "/") + "/xrpc/ai.gftd.apps.coverage.inferIngest"
	inserted, errCount := 0, 0
	for start := 0; start < len(rows); start += batchSize {
		end := start + batchSize
		if end > len(rows) {
			end = len(rows)
		}
		payload := map[string]any{"source": source, "rows": rows[start:end]}
		body, _ := json.Marshal(payload)

		req, err := http.NewRequestWithContext(ctx, "POST", endpoint, bytes.NewReader(body))
		if err != nil {
			errCount += end - start
			fmt.Fprintf(os.Stderr, "warn: build request: %v\n", err)
			continue
		}
		req.Header.Set("Content-Type", "application/json")
		req.Header.Set("Accept", "application/json")
		setAuthHeaders(req)

		resp, err := http.DefaultClient.Do(req)
		if err != nil {
			errCount += end - start
			fmt.Fprintf(os.Stderr, "warn: batch %d-%d POST failed: %v\n", start, end, err)
			continue
		}
		respBody, _ := io.ReadAll(resp.Body)
		resp.Body.Close()

		if resp.StatusCode < 200 || resp.StatusCode >= 300 {
			errCount += end - start
			if errCount <= 3*batchSize {
				fmt.Fprintf(os.Stderr, "warn: batch %d-%d HTTP %s: %s\n", start, end, resp.Status, truncate(string(respBody), 200))
			}
			continue
		}

		// BPMN multi-instance writes each loop's `inserted` back to the
		// same parent-scope variable (last-write-wins), so the count in
		// `variables.inserted` undercounts. HTTP 2xx == all rows in this
		// batch were submitted; we trust that. (Per-row failures show up
		// in dispatcher logs, not here.)
		inserted += end - start

		if inserted%500 < batchSize {
			fmt.Fprintf(os.Stderr, "  ... %d/%d inserted\n", inserted, len(rows))
		}
	}
	return inserted, errCount
}

// ingestViaDirectSQL is the legacy path. Kept behind --xrpc-sink=false until
// downstream automation finishes migrating; the BPMN sink is the canonical
// write path under ADR-0056.
func ingestViaDirectSQL(ctx context.Context, source string, rows []talentRow) (int, int) {
	inserted, errCount := 0, 0
	for i := 0; i < len(rows); i++ {
		r := rows[i]
		vertexID := fmt.Sprintf("talent-cohort:%s:%s:%s:%s:%s",
			source, r.Country, r.ISCOCode, r.Sex, r.TimePeriod)
		insertSQL := fmt.Sprintf(
			`INSERT INTO vertex_talent_cohort (vertex_id, label, source, isco_code, country, sex, time_period, size_thousands, created_date)
			 VALUES ('%s', 'TalentCohort', '%s', '%s', '%s', '%s', '%s', %f, now())`,
			escape(vertexID), escape(source),
			escape(r.ISCOCode), escape(r.Country), escape(r.Sex),
			escape(r.TimePeriod), r.SizeK,
		)
		if _, err := db.RawQuery(ctx, insertSQL); err != nil {
			errCount++
			if errCount <= 3 {
				fmt.Fprintf(os.Stderr, "warn: insert %s: %v\n", vertexID, err)
			}
			continue
		}
		inserted++
		if inserted%500 == 0 {
			fmt.Fprintf(os.Stderr, "  ... %d/%d inserted\n", inserted, len(rows))
		}
	}
	if _, err := db.RawQuery(ctx, "FLUSH"); err != nil {
		fmt.Fprintf(os.Stderr, "warn: FLUSH failed: %v\n", err)
	}
	return inserted, errCount
}

func sortedKeys(m map[string]bool) []string {
	keys := make([]string, 0, len(m))
	for k := range m {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	return keys
}

func min10(a, b int) int {
	if a < b {
		return a
	}
	return b
}

// ── materialize ─────────────────────────────────────────────────────────────

// runInferMaterialize converts discovered clusters into actor DIDs.
func runInferMaterialize(args []string) error {
	fs := flag.NewFlagSet("coverage infer materialize", flag.ContinueOnError)
	batchID := fs.String("batch-id", "", "batch ID from discover (latest if empty)")
	dryRun := fs.Bool("dry-run", false, "preview only")
	jsonOut := fs.Bool("json", false, "JSON output")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	ctx, cancel := context.WithTimeout(context.Background(), 120*time.Second)
	defer cancel()

	batch := *batchID
	if batch == "" {
		resp, err := db.RawQuery(ctx, `SELECT batch_id FROM vertex_infer_cluster ORDER BY created_date DESC LIMIT 1`)
		if err != nil || len(resp.Rows) == 0 {
			return fmt.Errorf("no clusters found. Run 'gftd coverage infer discover' first")
		}
		batch = anyStr(resp.Rows[0]["batch_id"])
	}

	clusterSQL := fmt.Sprintf(
		`SELECT vertex_id, cluster_id, method, member_count, k_anonymity, features_avg
		 FROM vertex_infer_cluster WHERE batch_id = '%s' AND status = 'active' LIMIT 100`,
		escape(batch))

	resp, err := db.RawQuery(ctx, clusterSQL)
	if err != nil {
		return fmt.Errorf("cluster query: %w", err)
	}

	type materialized struct {
		ClusterID int64  `json:"clusterId"`
		DID       string `json:"did"`
		Handle    string `json:"handle"`
		Members   int64  `json:"members"`
	}
	var results []materialized

	for _, row := range resp.Rows {
		cid := anyInt(row["cluster_id"])
		did := fmt.Sprintf("did:web:infer.etzhayyim.com:cluster:%s:%d", batch, cid)
		handle := fmt.Sprintf("cluster-%d.infer.etzhayyim.com", cid)
		members := anyInt(row["member_count"])

		results = append(results, materialized{
			ClusterID: cid, DID: did, Handle: handle, Members: members,
		})

		if !*dryRun {
			actorSQL := fmt.Sprintf(
				`INSERT INTO vertex_actor (vertex_id, did, name, display_name, performer_type, operator, created_date)
				 VALUES ('%s', '%s', 'infer-cluster-%d', 'Statistical Cluster %d (%d members)', 'service', 'amanomibashira', now())`,
				escape(did), escape(did), cid, cid, members)
			if _, err := db.RawQuery(ctx, actorSQL); err != nil {
				fmt.Fprintf(os.Stderr, "warn: actor %s: %v\n", did, err)
			}
		}
	}

	if !*dryRun {
		db.RawQuery(ctx, "FLUSH")
	}

	if *jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(map[string]any{"batchId": batch, "dryRun": *dryRun, "actors": results})
	}

	fmt.Printf("Materialized %d clusters as actor DIDs (batch=%s, dry-run=%v)\n\n", len(results), batch, *dryRun)
	fmt.Printf("%-4s %-50s %8s\n", "ID", "DID", "MEMBERS")
	fmt.Printf("%-4s %-50s %8s\n", "────", strings.Repeat("─", 50), "────────")
	for _, r := range results {
		fmt.Printf("%-4d %-50s %8d\n", r.ClusterID, r.DID, r.Members)
	}
	return nil
}

// ── deps ────────────────────────────────────────────────────────────────────

var conceptSeeds = []struct {
	Slug, Category, DisplayName, Era, Origin string
}{
	// Ideological
	{"communism", "ideological", "Communism", "modern", "DEU"},
	{"liberalism", "ideological", "Liberalism", "modern", "GBR"},
	{"fascism", "ideological", "Fascism", "modern", "ITA"},
	{"socialism", "ideological", "Socialism", "modern", "FRA"},
	{"capitalism", "economic", "Capitalism", "modern", "GBR"},
	{"neoliberalism", "economic", "Neoliberalism", "modern", "USA"},
	{"mercantilism", "economic", "Mercantilism", "classical", "GBR"},
	// Philosophical
	{"confucianism", "philosophical", "Confucianism", "classical", "CHN"},
	{"taoism", "philosophical", "Taoism", "classical", "CHN"},
	{"stoicism", "philosophical", "Stoicism", "classical", "GRC"},
	{"existentialism", "philosophical", "Existentialism", "modern", "FRA"},
	{"utilitarianism", "philosophical", "Utilitarianism", "modern", "GBR"},
	{"pragmatism", "philosophical", "Pragmatism", "modern", "USA"},
	// Religious
	{"buddhism", "religious", "Buddhism", "classical", "IND"},
	{"islam", "religious", "Islam", "medieval", "SAU"},
	{"christianity", "religious", "Christianity", "classical", "ISR"},
	{"hinduism", "religious", "Hinduism", "classical", "IND"},
	{"shintoism", "religious", "Shintoism", "classical", "JPN"},
	{"judaism", "religious", "Judaism", "classical", "ISR"},
	{"wahhabism", "religious", "Wahhabism", "modern", "SAU"},
	{"orthodoxy", "religious", "Eastern Orthodoxy", "medieval", "GRC"},
	// Political
	{"stalinism", "political", "Stalinism", "modern", "RUS"},
	{"maoism", "political", "Maoism", "modern", "CHN"},
	{"democracy", "political", "Democracy", "classical", "GRC"},
	{"monarchy", "political", "Monarchy", "classical", ""},
	{"authoritarianism", "political", "Authoritarianism", "modern", ""},
	{"theocracy", "political", "Theocracy", "classical", ""},
	{"federalism", "political", "Federalism", "modern", "USA"},
	{"juche", "political", "Juche", "modern", "PRK"},
	// Sport
	{"olympics", "sport", "Olympic Movement", "modern", "GRC"},
	{"fifa", "sport", "FIFA Football", "modern", "FRA"},
	{"cricket", "sport", "Cricket (ICC)", "modern", "GBR"},
	{"baseball", "sport", "Baseball (WBSC)", "modern", "USA"},
	{"martial_arts", "sport", "Martial Arts", "classical", "CHN"},
	// Community
	{"cooperative", "community", "Cooperative Movement", "modern", "GBR"},
	{"ngo", "community", "NGO Sector", "modern", ""},
	{"labor_union", "community", "Labor Union Movement", "modern", "GBR"},
	{"civil_society", "community", "Civil Society", "modern", ""},
	// Education
	{"compulsory_education", "education", "Compulsory Education", "modern", "DEU"},
	{"university_system", "education", "University System", "medieval", "ITA"},
	{"vocational_training", "education", "Vocational Training", "modern", "DEU"},
	{"stem_education", "education", "STEM Education", "modern", "USA"},
	// Cultural
	{"secularism", "cultural", "Secularism", "modern", "FRA"},
	{"collectivism", "cultural", "Collectivism", "classical", ""},
	{"individualism", "cultural", "Individualism", "modern", "USA"},
	// History (historical periods / movements)
	{"sengoku_period", "history", "Sengoku Period (Warring States)", "medieval", "JPN"},
	{"industrial_revolution", "history", "Industrial Revolution", "modern", "GBR"},
	{"cold_war", "history", "Cold War", "modern", "USA"},
	{"colonialism", "history", "Colonialism", "modern", "GBR"},
	{"enlightenment", "history", "Enlightenment", "classical", "FRA"},
	{"scientific_revolution", "history", "Scientific Revolution", "classical", "GBR"},
	{"reformation", "history", "Protestant Reformation", "medieval", "DEU"},
	{"meiji_restoration", "history", "Meiji Restoration", "modern", "JPN"},
	{"french_revolution", "history", "French Revolution", "modern", "FRA"},
	{"opium_war", "history", "Opium Wars", "modern", "CHN"},
	// Language (linguistic spheres)
	{"han_script", "language", "Han Script Sphere (漢字圏)", "classical", "CHN"},
	{"arabic_script", "language", "Arabic Script Sphere", "medieval", "SAU"},
	{"latin_script", "language", "Latin Script Sphere", "classical", "ITA"},
	{"cyrillic_script", "language", "Cyrillic Script Sphere", "medieval", "RUS"},
	{"devanagari_script", "language", "Devanagari Script Sphere", "classical", "IND"},
	{"hangul", "language", "Hangul Script", "medieval", "KOR"},
	{"kana_script", "language", "Kana Script (仮名)", "medieval", "JPN"},
	// Art (art movements)
	{"renaissance", "art", "Renaissance Art", "medieval", "ITA"},
	{"impressionism", "art", "Impressionism", "modern", "FRA"},
	{"ukiyoe", "art", "Ukiyo-e (浮世絵)", "medieval", "JPN"},
	{"bauhaus", "art", "Bauhaus", "modern", "DEU"},
	{"baroque", "art", "Baroque Art", "classical", "ITA"},
	{"romanticism", "art", "Romanticism", "modern", "DEU"},
	{"pop_art", "art", "Pop Art", "modern", "USA"},
	// Literature (literary traditions)
	{"shakespeare", "literature", "Shakespearean Canon", "classical", "GBR"},
	{"russian_novel", "literature", "Russian Novel Tradition", "modern", "RUS"},
	{"japanese_literature", "literature", "Japanese Literary Tradition", "classical", "JPN"},
	{"tang_poetry", "literature", "Tang Dynasty Poetry", "classical", "CHN"},
	{"modernist_lit", "literature", "Modernist Literature", "modern", "GBR"},
	{"beat_generation", "literature", "Beat Generation", "modern", "USA"},
	// Science / thought (science-thought movements)
	{"newtonian_physics", "science", "Newtonian Physics", "classical", "GBR"},
	{"darwinism", "science", "Darwinian Evolution", "modern", "GBR"},
	{"relativity", "science", "Einsteinian Relativity", "modern", "DEU"},
	{"quantum_theory", "science", "Quantum Theory", "modern", "DEU"},
	{"cybernetics", "science", "Cybernetics", "modern", "USA"},
	{"ai_thought", "science", "Artificial Intelligence Paradigm", "modern", "USA"},
	{"information_theory", "science", "Information Theory (Shannon)", "modern", "USA"},
	// Architecture (architectural traditions)
	{"gothic", "architecture", "Gothic Architecture", "medieval", "FRA"},
	{"modernism_arch", "architecture", "Modernist Architecture", "modern", "DEU"},
	{"wafu", "architecture", "Wafu (Japanese Traditional)", "classical", "JPN"},
	{"classical_arch", "architecture", "Greco-Roman Classical", "classical", "GRC"},
	{"islamic_arch", "architecture", "Islamic Architecture", "medieval", "SAU"},
	{"brutalism", "architecture", "Brutalism", "modern", "GBR"},
	// Music (musical traditions)
	{"western_classical", "music", "Western Classical Music", "classical", "DEU"},
	{"gagaku", "music", "Gagaku (雅楽)", "classical", "JPN"},
	{"rock_music", "music", "Rock Music", "modern", "USA"},
	{"kpop", "music", "K-Pop", "modern", "KOR"},
	{"jazz", "music", "Jazz", "modern", "USA"},
	{"hip_hop", "music", "Hip-Hop", "modern", "USA"},
	{"indian_classical", "music", "Indian Classical Music", "classical", "IND"},
	// Cuisine (culinary traditions)
	{"mediterranean_cuisine", "cuisine", "Mediterranean Cuisine", "classical", "ITA"},
	{"washoku", "cuisine", "Washoku (和食)", "classical", "JPN"},
	{"chinese_cuisine", "cuisine", "Chinese Cuisine", "classical", "CHN"},
	{"french_cuisine", "cuisine", "French Haute Cuisine", "classical", "FRA"},
	{"indian_cuisine", "cuisine", "Indian Cuisine", "classical", "IND"},
	{"middle_eastern_cuisine", "cuisine", "Middle Eastern Cuisine", "classical", "SAU"},
	{"mexican_cuisine", "cuisine", "Mexican Cuisine", "classical", "MEX"},
}

// runInferDeps seeds concept nodes and/or creates dependency edges.
func runInferDeps(args []string) error {
	fs := flag.NewFlagSet("coverage infer deps", flag.ContinueOnError)
	seedConcepts := fs.Bool("seed-concepts", false, "seed built-in concept nodes")
	inputFile := fs.String("input", "", "JSONL file with dependency edges")
	dryRun := fs.Bool("dry-run", false, "preview only")
	jsonOut := fs.Bool("json", false, "JSON output")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	if !*seedConcepts && *inputFile == "" {
		return fmt.Errorf("use --seed-concepts and/or --input <deps.jsonl>")
	}

	ctx, cancel := context.WithTimeout(context.Background(), 180*time.Second)
	defer cancel()

	// Seed concept nodes
	if *seedConcepts {
		seeded := 0
		for _, c := range conceptSeeds {
			vid := fmt.Sprintf("did:web:infer.etzhayyim.com:concept:%s", c.Slug)
			if *dryRun {
				fmt.Printf("  [dry-run] concept: %s (%s) — %s\n", c.Slug, c.Category, c.DisplayName)
				seeded++
				continue
			}
			insertSQL := fmt.Sprintf(
				`INSERT INTO vertex_infer_concept (vertex_id, slug, category, display_name, era, origin_country, created_date)
				 VALUES ('%s', '%s', '%s', '%s', '%s', '%s', now())`,
				escape(vid), escape(c.Slug), escape(c.Category),
				escape(c.DisplayName), escape(c.Era), escape(c.Origin))
			if _, err := db.RawQuery(ctx, insertSQL); err != nil {
				fmt.Fprintf(os.Stderr, "warn: concept %s: %v\n", c.Slug, err)
			} else {
				seeded++
			}
		}
		if !*dryRun {
			db.RawQuery(ctx, "FLUSH")
		}
		fmt.Fprintf(os.Stderr, "Seeded %d concept nodes (dry-run=%v)\n", seeded, *dryRun)
	}

	// Load and insert dependency edges
	if *inputFile != "" {
		f, err := os.Open(*inputFile)
		if err != nil {
			return fmt.Errorf("open %s: %w", *inputFile, err)
		}
		defer f.Close()

		type depEdge struct {
			From     string  `json:"from"`
			To       string  `json:"to"`
			Label    string  `json:"label"`
			Strength float64 `json:"strength"`
			Role     string  `json:"role"`
		}

		scanner := bufio.NewScanner(f)
		edgeCount := 0
		errCount := 0

		for scanner.Scan() {
			line := strings.TrimSpace(scanner.Text())
			if line == "" || line[0] == '#' {
				continue
			}
			var dep depEdge
			if err := json.Unmarshal([]byte(line), &dep); err != nil {
				fmt.Fprintf(os.Stderr, "warn: parse line: %v\n", err)
				errCount++
				continue
			}

			// Resolve DIDs
			srcDID := resolveEntityDID(dep.From)
			dstDID := resolveEntityDID(dep.To)
			edgeID := fmt.Sprintf("dep:%s:%s:%s", dep.From, dep.To, dep.Label)

			if *dryRun {
				fmt.Printf("  [dry-run] %s -[%s:%.2f]-> %s\n", srcDID, dep.Label, dep.Strength, dstDID)
				edgeCount++
				continue
			}

			insertSQL := fmt.Sprintf(
				`INSERT INTO edge_requires (edge_id, src_vid, dst_vid, label, quantity, role, created_date)
				 VALUES ('%s', '%s', '%s', '%s', %f, '%s', now())`,
				escape(edgeID), escape(srcDID), escape(dstDID),
				escape(dep.Label), dep.Strength, escape(dep.Role))
			if _, err := db.RawQuery(ctx, insertSQL); err != nil {
				fmt.Fprintf(os.Stderr, "warn: edge %s→%s: %v\n", dep.From, dep.To, err)
				errCount++
			} else {
				edgeCount++
			}
		}

		if !*dryRun {
			db.RawQuery(ctx, "FLUSH")
		}
		fmt.Fprintf(os.Stderr, "Created %d dependency edges (%d errors, dry-run=%v)\n", edgeCount, errCount, *dryRun)
	}

	if *jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(map[string]any{"status": "ok"})
	}
	return nil
}

// resolveEntityDID maps a country code or concept slug to a DID.
func resolveEntityDID(name string) string {
	// ISO 3166 country code (2-3 uppercase letters)
	if len(name) >= 2 && len(name) <= 3 && name == strings.ToUpper(name) {
		return fmt.Sprintf("did:web:infer.etzhayyim.com:country:%s", strings.ToLower(name))
	}
	// Concept slug
	return fmt.Sprintf("did:web:infer.etzhayyim.com:concept:%s", strings.ToLower(name))
}

// ── follow ──────────────────────────────────────────────────────────────────

// runInferFollow creates follow edges from dependency relationships.
func runInferFollow(args []string) error {
	fs := flag.NewFlagSet("coverage infer follow", flag.ContinueOnError)
	auto := fs.Bool("auto", false, "auto-follow deps with strength > 0.7")
	threshold := fs.Float64("threshold", 0.7, "minimum strength for auto-follow")
	dryRun := fs.Bool("dry-run", false, "preview only")
	jsonOut := fs.Bool("json", false, "JSON output")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	if !*auto {
		return fmt.Errorf("use --auto to create follow edges from deps (strength > threshold)")
	}

	ctx, cancel := context.WithTimeout(context.Background(), 120*time.Second)
	defer cancel()

	// Query edge_requires with strength above threshold
	sqlStmt := fmt.Sprintf(
		`SELECT edge_id, src_vid, dst_vid, label, quantity FROM edge_requires
		 WHERE quantity >= %f ORDER BY quantity DESC LIMIT 1000`, *threshold)

	resp, err := db.RawQuery(ctx, sqlStmt)
	if err != nil {
		return fmt.Errorf("query deps: %w", err)
	}

	type followResult struct {
		SrcDID   string  `json:"srcDid"`
		DstDID   string  `json:"dstDid"`
		Label    string  `json:"label"`
		Strength float64 `json:"strength"`
	}
	var follows []followResult
	errCount := 0

	for _, row := range resp.Rows {
		src := anyStr(row["src_vid"])
		dst := anyStr(row["dst_vid"])
		label := anyStr(row["label"])
		strength := anyFloat(row["quantity"])

		if *dryRun {
			fmt.Printf("  [dry-run] follow: %s → %s (%s, %.2f)\n", src, dst, label, strength)
			follows = append(follows, followResult{src, dst, label, strength})
			continue
		}

		edgeID := fmt.Sprintf("follow:%s:%s", src, dst)
		insertSQL := fmt.Sprintf(
			`INSERT INTO edge_follows (edge_id, src_vid, dst_vid, created_date)
			 VALUES ('%s', '%s', '%s', now())`,
			escape(edgeID), escape(src), escape(dst))
		if _, err := db.RawQuery(ctx, insertSQL); err != nil {
			fmt.Fprintf(os.Stderr, "warn: follow %s→%s: %v\n", src, dst, err)
			errCount++
		} else {
			follows = append(follows, followResult{src, dst, label, strength})
		}
	}

	if !*dryRun {
		db.RawQuery(ctx, "FLUSH")
	}

	if *jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(map[string]any{
			"dryRun":    *dryRun,
			"threshold": *threshold,
			"follows":   follows,
			"errors":    errCount,
		})
	}

	fmt.Printf("Created %d follow edges from deps (threshold=%.2f, errors=%d, dry-run=%v)\n\n",
		len(follows), *threshold, errCount, *dryRun)
	if len(follows) > 0 {
		fmt.Printf("%-45s %-45s %-14s %6s\n", "FROM", "TO", "LABEL", "STR")
		fmt.Printf("%-45s %-45s %-14s %6s\n",
			strings.Repeat("─", 45), strings.Repeat("─", 45), strings.Repeat("─", 14), "──────")
		for _, f := range follows {
			src := f.SrcDID
			if len(src) > 45 {
				src = src[:42] + "..."
			}
			dst := f.DstDID
			if len(dst) > 45 {
				dst = dst[:42] + "..."
			}
			fmt.Printf("%-45s %-45s %-14s %6.2f\n", src, dst, f.Label, f.Strength)
		}
	}
	return nil
}
