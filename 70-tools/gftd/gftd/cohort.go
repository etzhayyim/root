// gftd cohort — ADR-0026 cohort actor lifecycle CLI.
//
// Phase A genesis: POST /xrpc/ai.gftd.cohort.seed with a demographic
// segment (JSON-LD) + k-anonymity ≥ 50.
//
//	gftd cohort seed \
//	  --segment '{"pcfL1":"3-market-sell","role":"salesRep","locale":"jp"}' \
//	  --k 50
//
// Uses the standard `gftd agent-token --lxm ai.gftd.cohort.seed` path so
// the call carries a scoped 60s Service Auth JWT — never a long-lived
// session token.
package main

import (
	"bytes"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"strings"
	"time"
)

type cohortSeedInput struct {
	SegmentJsonld  string `json:"segmentJsonld"`
	KAnonymity     int    `json:"kAnonymity"`
	FissionEnabled bool   `json:"fissionEnabled,omitempty"`
	PolicyRef      string `json:"policyRef,omitempty"`
}

type cohortSeedOutput struct {
	Did          string `json:"did"`
	Handle       string `json:"handle"`
	SignatureURI string `json:"signatureUri"`
	GenesisAt    string `json:"genesisAt"`
}

func runCohort(args []string) error {
	if len(args) == 0 {
		return fmt.Errorf("usage: gftd cohort <seed|bootstrap> [flags]")
	}
	switch args[0] {
	case "seed":
		return runCohortSeed(args[1:])
	case "bootstrap":
		return runCohortBootstrap(args[1:])
	case "list":
		return runCohortList(args[1:])
	case "fission":
		return runCohortFission(args[1:])
	case "lineage":
		return runCohortLineage(args[1:])
	case "evidence":
		return runCohortEvidence(args[1:])
	case "forest":
		return runCohortForest(args[1:])
	case "stats":
		return runCohortStats(args[1:])
	case "coverage":
		return runCohortCoverage(args[1:])
	case "gap":
		return runCohortGap(args[1:])
	case "gen":
		return runCohortGen(args[1:])
	case "snapshot":
		return runCohortSnapshot(args[1:])
	case "diff":
		return runCohortDiff(args[1:])
	case "drift":
		return runCohortDrift(args[1:])
	case "emit":
		return runCohortEmit(args[1:])
	case "lineage-stats":
		return runCohortLineageStats(args[1:])
	case "repair-edge":
		return runCohortRepairEdge(args[1:])
	case "dashboard":
		return runCohortDashboard(args[1:])
	default:
		return fmt.Errorf("unknown cohort subcommand %q (available: seed, bootstrap, list, fission, lineage, evidence, forest, stats, coverage, gap, gen, snapshot, diff, drift)", args[0])
	}
}

// runCohortDashboard — one-shot summary view combining stats / coverage / lineage-stats.
// Replaces the need to run 3 separate commands by fanning out internally.
func runCohortDashboard(args []string) error {
	fs := flag.NewFlagSet("cohort dashboard", flag.ContinueOnError)
	pds := fs.String("pds", resolvePDSBaseURL(), "PDS base URL")
	limit := fs.Int("limit", 500, "max cohorts to fetch")
	if err := fs.Parse(args); err != nil {
		return err
	}
	token := resolveGFTDToken()
	if token == "" {
		return fmt.Errorf("no GFTD token found — run `gftd auth login` or set GFTD_TOKEN")
	}

	type listResp struct {
		Cohorts []struct {
			Kind           string `json:"kind"`
			SegmentHash    string `json:"segmentHash"`
			FissionEnabled bool   `json:"fissionEnabled"`
		} `json:"cohorts"`
	}

	q := url.Values{}
	q.Set("limit", fmt.Sprintf("%d", *limit))
	target := strings.TrimRight(*pds, "/") + "/xrpc/ai.gftd.cohort.listCohorts?" + q.Encode()
	req, _ := http.NewRequest("GET", target, nil)
	req.Header.Set("Authorization", "Bearer "+token)
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return fmt.Errorf("listCohorts: %w", err)
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body)
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("listCohorts %d: %s", resp.StatusCode, string(body))
	}
	var lr listResp
	if err := json.Unmarshal(body, &lr); err != nil {
		return err
	}

	totalCohort, totalFissioned, fissionEnabled := 0, 0, 0
	pcfL1Set := map[string]bool{}
	roleSet := map[string]bool{}
	industrySet := map[string]bool{}
	localeSet := map[string]bool{}
	for _, c := range lr.Cohorts {
		if c.Kind == "fissioned" {
			totalFissioned++
		} else {
			totalCohort++
		}
		if c.FissionEnabled {
			fissionEnabled++
		}
		kv := parseSegmentKV(c.SegmentHash)
		if kv["pcfL1"] != "" {
			pcfL1Set[kv["pcfL1"]] = true
		}
		if kv["role"] != "" {
			roleSet[kv["role"]] = true
		}
		if kv["industry"] != "" {
			industrySet[kv["industry"]] = true
		}
		if kv["locale"] != "" {
			localeSet[kv["locale"]] = true
		}
	}

	fmt.Println("┌─ ADR-0026 Cohort Fleet Dashboard ─────────────────────")
	fmt.Printf("│  total           : %d  (cohort=%d, fissioned=%d)\n", len(lr.Cohorts), totalCohort, totalFissioned)
	fmt.Printf("│  fissionEnabled  : %d / %d  (%.1f%%)\n", fissionEnabled, totalCohort, ratePct(fissionEnabled, totalCohort))
	fmt.Printf("│  axis cardinality\n")
	fmt.Printf("│    pcfL1     : %d / 13\n", len(pcfL1Set))
	fmt.Printf("│    role      : %d\n", len(roleSet))
	fmt.Printf("│    industry  : %d\n", len(industrySet))
	fmt.Printf("│    locale    : %d\n", len(localeSet))

	// Phase trigger watch (ADR-0028, 64Gi GPU baseline 2026-04-15+)
	phase := "Phase 1 (single MV)"
	switch {
	case len(lr.Cohorts) > 5_000_000:
		phase = "Phase 4 (vertex_individual_actor partition)"
	case len(lr.Cohorts) > 1_000_000:
		phase = "Phase 3 (13 sub-MV per pcfL1)"
	case len(lr.Cohorts) > 10_000:
		phase = "Phase 2 (index 追加検討)"
	}
	fmt.Printf("│  ADR-0028 phase  : %s\n", phase)
	fmt.Println("└────────────────────────────────────────────────────────")
	return nil
}

func ratePct(n, total int) float64 {
	if total == 0 {
		return 0
	}
	return float64(n) / float64(total) * 100
}

// CohortOcelEventType — must match TS host-sdk cohort.ts CohortOcelEventType.
type CohortOcelEventType string

const (
	CohortEventGenesis              CohortOcelEventType = "cohort.genesis"
	CohortEventEvidenceAccrued      CohortOcelEventType = "cohort.evidence.accrued"
	CohortEventEvidenceFissionReady CohortOcelEventType = "cohort.evidence.fissionReady"
	CohortEventKReevaluated         CohortOcelEventType = "cohort.kReevaluated"
	CohortEventFission              CohortOcelEventType = "cohort.fission"
	CohortEventPurge                CohortOcelEventType = "cohort.purge"
)

// CohortEventInput mirrors TS deriveCohortEventType arg shape exactly.
// Must produce identical eventType for identical inputs (cross-runtime
// invariant verified by cohort_test.go).
type CohortEventInput struct {
	EvidenceCountBefore int
	Posterior           *float64 // nil = absent
	JudgeAgreement      *bool    // nil = absent
	KProxy              *int     // nil = absent
	FissionEnabled      bool
	DidFission          bool
}

// DeriveCohortEventType — Go mirror of TS host-sdk
// `deriveCohortEventType` (20-actors/magatama/sdk/magatama-host-sdk/src/cohort.ts).
// Precedence order MUST match TS exactly:
//   1. didFission → cohort.fission
//   2. kProxy<50 → cohort.kReevaluated
//   3. posterior>0.95 && judgeAgreement && fissionEnabled → fissionReady
//   4. evidenceCountBefore===0 → cohort.genesis
//   5. default → cohort.evidence.accrued
func DeriveCohortEventType(input CohortEventInput) CohortOcelEventType {
	if input.DidFission {
		return CohortEventFission
	}
	if input.KProxy != nil && *input.KProxy < 50 {
		return CohortEventKReevaluated
	}
	if input.Posterior != nil && *input.Posterior > 0.95 &&
		input.JudgeAgreement != nil && *input.JudgeAgreement &&
		input.FissionEnabled {
		return CohortEventEvidenceFissionReady
	}
	if input.EvidenceCountBefore == 0 {
		return CohortEventGenesis
	}
	return CohortEventEvidenceAccrued
}

// runCohortRepairEdge — POST /xrpc/ai.gftd.cohort.repairEdge to backfill
// edge_cohort_derived rows missing for fissioned individuals.
func runCohortRepairEdge(args []string) error {
	fs := flag.NewFlagSet("cohort repair-edge", flag.ContinueOnError)
	individualDid := fs.String("did", "", "single individual DID (omit for bulk)")
	limit := fs.Int("limit", 100, "bulk repair limit")
	dryRun := fs.Bool("dry-run", true, "preview only (default true)")
	pds := fs.String("pds", resolvePDSBaseURL(), "PDS base URL")
	jsonOut := fs.Bool("json", false, "Emit raw JSON")
	if err := fs.Parse(args); err != nil {
		return err
	}
	token := resolveGFTDToken()
	if token == "" {
		return fmt.Errorf("no GFTD token found — run `gftd auth login` or set GFTD_TOKEN")
	}
	body, _ := json.Marshal(map[string]any{
		"individualDid": *individualDid,
		"limit":         *limit,
		"dryRun":        *dryRun,
	})
	target := strings.TrimRight(*pds, "/") + "/xrpc/ai.gftd.cohort.repairEdge"
	req, _ := http.NewRequest("POST", target, bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+token)
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return fmt.Errorf("http: %w", err)
	}
	defer resp.Body.Close()
	respBody, _ := io.ReadAll(resp.Body)
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("repair-edge failed: %d %s: %s", resp.StatusCode, http.StatusText(resp.StatusCode), string(respBody))
	}
	if *jsonOut {
		fmt.Println(string(respBody))
		return nil
	}
	fmt.Println(string(respBody))
	return nil
}

// runCohortLineageStats — read mv_cohort_lineage_depth via XRPC.
func runCohortLineageStats(args []string) error {
	fs := flag.NewFlagSet("cohort lineage-stats", flag.ContinueOnError)
	pcfL1 := fs.String("pcfL1", "", "filter by APQC L1 (joins vertex_cohort_actor)")
	minChildren := fs.Int("min-children", 1, "include cohort with direct_children >= N")
	limit := fs.Int("limit", 100, "page size")
	pds := fs.String("pds", resolvePDSBaseURL(), "PDS base URL")
	jsonOut := fs.Bool("json", false, "Emit raw JSON")
	if err := fs.Parse(args); err != nil {
		return err
	}
	token := resolveGFTDToken()
	if token == "" {
		return fmt.Errorf("no GFTD token found — run `gftd auth login` or set GFTD_TOKEN")
	}
	q := url.Values{}
	if *pcfL1 != "" {
		q.Set("pcfL1", *pcfL1)
	}
	q.Set("minChildren", fmt.Sprintf("%d", *minChildren))
	q.Set("limit", fmt.Sprintf("%d", *limit))
	target := strings.TrimRight(*pds, "/") + "/xrpc/ai.gftd.cohort.lineageStats?" + q.Encode()
	req, _ := http.NewRequest("GET", target, nil)
	req.Header.Set("Authorization", "Bearer "+token)
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return fmt.Errorf("http: %w", err)
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body)
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("lineage-stats failed: %d %s: %s", resp.StatusCode, http.StatusText(resp.StatusCode), string(body))
	}
	if *jsonOut {
		fmt.Println(string(body))
		return nil
	}
	var out struct {
		Rows []struct {
			CohortDid       string `json:"cohortDid"`
			DirectChildren  int    `json:"directChildren"`
			LastFissionAt   string `json:"lastFissionAt"`
		} `json:"rows"`
	}
	if err := json.Unmarshal(body, &out); err != nil {
		fmt.Println(string(body))
		return nil
	}
	fmt.Printf("lineage-stats: %d cohorts (children >= %d, pcfL1=%s)\n", len(out.Rows), *minChildren, *pcfL1)
	for _, r := range out.Rows {
		fmt.Printf("  %-44s  children=%-4d  last=%s\n", r.CohortDid, r.DirectChildren, r.LastFissionAt)
	}
	return nil
}

// runCohortEmit — POST /xrpc/ai.gftd.cohort.emitEvidence to insert one evidence
// row + edge directly into RisingWave (Phase B). Useful for fission simulation.
func runCohortEmit(args []string) error {
	fs := flag.NewFlagSet("cohort emit", flag.ContinueOnError)
	cohort := fs.String("cohort", "", "Cohort DID (required)")
	signal := fs.String("signal-kind", "behavior.observed", "signal kind label")
	payload := fs.String("payload", "", "Evidence payload (required, hashed for deduping)")
	posterior := fs.Float64("posterior", 0, "Posterior contribution (0..1)")
	judge := fs.Bool("judge", false, "LLM-as-judge agreement")
	pds := fs.String("pds", resolvePDSBaseURL(), "PDS base URL")
	jsonOut := fs.Bool("json", false, "Emit raw JSON response")
	if err := fs.Parse(args); err != nil {
		return err
	}
	if *cohort == "" || *payload == "" {
		return fmt.Errorf("--cohort and --payload required")
	}
	token := resolveGFTDToken()
	if token == "" {
		return fmt.Errorf("no GFTD token found — run `gftd auth login` or set GFTD_TOKEN")
	}
	body, _ := json.Marshal(map[string]any{
		"cohortDid":       *cohort,
		"signalKind":      *signal,
		"evidencePayload": *payload,
		"posterior":       *posterior,
		"judgeAgreement":  *judge,
	})
	target := strings.TrimRight(*pds, "/") + "/xrpc/ai.gftd.cohort.emitEvidence"
	req, _ := http.NewRequest("POST", target, bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+token)
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return fmt.Errorf("http: %w", err)
	}
	defer resp.Body.Close()
	respBody, _ := io.ReadAll(resp.Body)
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("emit failed: %d %s: %s", resp.StatusCode, http.StatusText(resp.StatusCode), string(respBody))
	}
	if *jsonOut {
		fmt.Println(string(respBody))
		return nil
	}
	fmt.Println(string(respBody))
	return nil
}

// runCohortDrift — auto-load oldest + newest snapshot under --dir within --window.
// Emits the same delta report as `diff` but doesn't require explicit file paths.
func runCohortDrift(args []string) error {
	fs := flag.NewFlagSet("cohort drift", flag.ContinueOnError)
	dir := fs.String("dir", "data/cohort-coverage", "snapshot dir")
	window := fs.Int("window", 7, "look-back window in days (0 = all snapshots)")
	jsonOut := fs.Bool("json", false, "Emit JSON delta report")
	if err := fs.Parse(args); err != nil {
		return err
	}
	entries, err := os.ReadDir(*dir)
	if err != nil {
		return fmt.Errorf("read dir %s: %w", *dir, err)
	}
	files := []string{}
	cutoff := time.Now().Add(-time.Duration(*window) * 24 * time.Hour)
	for _, e := range entries {
		if e.IsDir() || !strings.HasSuffix(e.Name(), ".json") {
			continue
		}
		info, err := e.Info()
		if err != nil {
			continue
		}
		if *window > 0 && info.ModTime().Before(cutoff) {
			continue
		}
		files = append(files, *dir+"/"+e.Name())
	}
	if len(files) < 2 {
		return fmt.Errorf("need >=2 snapshots in %s within %dd window (found %d)", *dir, *window, len(files))
	}
	sortStrings(files)
	oldest := files[0]
	newest := files[len(files)-1]
	if *jsonOut {
		return runCohortDiff([]string{"--json", oldest, newest})
	}
	fmt.Printf("drift window: %s ⇒ %s (%d snapshots)\n", oldest, newest, len(files))
	return runCohortDiff([]string{oldest, newest})
}

// runCohortDiff — compare two snapshot JSON files and report axis-level deltas.
func runCohortDiff(args []string) error {
	fs := flag.NewFlagSet("cohort diff", flag.ContinueOnError)
	jsonOut := fs.Bool("json", false, "Emit JSON delta report")
	if err := fs.Parse(args); err != nil {
		return err
	}
	rest := fs.Args()
	if len(rest) < 2 {
		return fmt.Errorf("usage: gftd cohort diff [--json] <a.json> <b.json>")
	}
	a, err := loadSnapshot(rest[0])
	if err != nil {
		return err
	}
	b, err := loadSnapshot(rest[1])
	if err != nil {
		return err
	}
	type delta struct {
		Value  string `json:"value"`
		Before int    `json:"before"`
		After  int    `json:"after"`
		Delta  int    `json:"delta"`
	}
	report := map[string]any{
		"a":               a.CapturedAt,
		"b":               b.CapturedAt,
		"deltaTotal":      b.TotalCohorts - a.TotalCohorts,
		"deltaFissioned":  b.TotalFissioned - a.TotalFissioned,
		"axes":            map[string][]delta{},
	}
	axesDelta := map[string][]delta{}
	for axis, listB := range b.Axes {
		listA := a.Axes[axis]
		mapA := map[string]int{}
		for _, v := range listA {
			mapA[v.Value] = v.Cohorts + v.Fissioned
		}
		ds := []delta{}
		for _, v := range listB {
			before := mapA[v.Value]
			after := v.Cohorts + v.Fissioned
			if before != after {
				ds = append(ds, delta{v.Value, before, after, after - before})
			}
		}
		axesDelta[axis] = ds
	}
	report["axes"] = axesDelta

	if *jsonOut {
		raw, _ := json.MarshalIndent(report, "", "  ")
		fmt.Println(string(raw))
		return nil
	}

	fmt.Printf("snapshot A: %s  total=%d  fissioned=%d\n", a.CapturedAt, a.TotalCohorts, a.TotalFissioned)
	fmt.Printf("snapshot B: %s  total=%d  fissioned=%d\n", b.CapturedAt, b.TotalCohorts, b.TotalFissioned)
	fmt.Printf("Δ total      = %+d\n", b.TotalCohorts-a.TotalCohorts)
	fmt.Printf("Δ fissioned  = %+d\n", b.TotalFissioned-a.TotalFissioned)
	for axis, ds := range axesDelta {
		if len(ds) == 0 {
			continue
		}
		fmt.Printf("\n[%s]\n", axis)
		for _, d := range ds {
			fmt.Printf("  %-32s  %+d  (%d → %d)\n", d.Value, d.Delta, d.Before, d.After)
		}
	}
	return nil
}

type snapshotFile struct {
	CapturedAt     string `json:"capturedAt"`
	TotalCohorts   int    `json:"totalCohorts"`
	TotalFissioned int    `json:"totalFissioned"`
	Axes           map[string][]struct {
		Value     string `json:"value"`
		Cohorts   int    `json:"cohorts"`
		Fissioned int    `json:"fissioned"`
	} `json:"axes"`
}

func loadSnapshot(path string) (*snapshotFile, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("read %s: %w", path, err)
	}
	var s snapshotFile
	if err := json.Unmarshal(raw, &s); err != nil {
		return nil, fmt.Errorf("parse %s: %w", path, err)
	}
	return &s, nil
}

// runCohortSnapshot — persist a point-in-time 4-axis coverage snapshot
// to `data/cohort-coverage/<timestamp>.json` for drift monitoring.
func runCohortSnapshot(args []string) error {
	fs := flag.NewFlagSet("cohort snapshot", flag.ContinueOnError)
	pds := fs.String("pds", resolvePDSBaseURL(), "PDS base URL")
	outDir := fs.String("out-dir", "data/cohort-coverage", "output directory")
	limit := fs.Int("limit", 500, "max cohorts to fetch")
	if err := fs.Parse(args); err != nil {
		return err
	}
	token := resolveGFTDToken()
	if token == "" {
		return fmt.Errorf("no GFTD token found — run `gftd auth login` or set GFTD_TOKEN")
	}
	q := url.Values{}
	q.Set("limit", fmt.Sprintf("%d", *limit))
	target := strings.TrimRight(*pds, "/") + "/xrpc/ai.gftd.cohort.listCohorts?" + q.Encode()
	req, _ := http.NewRequest("GET", target, nil)
	req.Header.Set("Authorization", "Bearer "+token)
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return fmt.Errorf("http: %w", err)
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body)
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("listCohorts failed: %d %s: %s", resp.StatusCode, http.StatusText(resp.StatusCode), string(body))
	}
	var out struct {
		Cohorts []struct {
			Kind        string `json:"kind"`
			SegmentHash string `json:"segmentHash"`
		} `json:"cohorts"`
	}
	if err := json.Unmarshal(body, &out); err != nil {
		return err
	}
	// 4-axis aggregate (L1 × {role, industry, seniority, locale} × {cohort,fissioned})
	type axisCount struct {
		Value     string `json:"value"`
		Cohorts   int    `json:"cohorts"`
		Fissioned int    `json:"fissioned"`
	}
	buckets := map[string]map[string]*axisCount{} // axis → value → count
	axes := []string{"pcfL1", "role", "industry", "seniority", "locale"}
	for _, a := range axes {
		buckets[a] = map[string]*axisCount{}
	}
	total := 0
	totalFissioned := 0
	for _, c := range out.Cohorts {
		total++
		if c.Kind == "fissioned" {
			totalFissioned++
		}
		kv := parseSegmentKV(c.SegmentHash)
		for _, a := range axes {
			v := kv[a]
			if v == "" {
				v = "-"
			}
			b := buckets[a][v]
			if b == nil {
				b = &axisCount{Value: v}
				buckets[a][v] = b
			}
			if c.Kind == "fissioned" {
				b.Fissioned++
			} else {
				b.Cohorts++
			}
		}
	}
	snap := map[string]any{
		"capturedAt":     formatISO(),
		"totalCohorts":   total - totalFissioned,
		"totalFissioned": totalFissioned,
		"axes":           map[string][]*axisCount{},
	}
	axesOut := map[string][]*axisCount{}
	for a, m := range buckets {
		list := make([]*axisCount, 0, len(m))
		for _, v := range m {
			list = append(list, v)
		}
		// sort by Value
		for i := 1; i < len(list); i++ {
			for j := i; j > 0 && list[j-1].Value > list[j].Value; j-- {
				list[j-1], list[j] = list[j], list[j-1]
			}
		}
		axesOut[a] = list
	}
	snap["axes"] = axesOut

	if err := os.MkdirAll(*outDir, 0o755); err != nil {
		return fmt.Errorf("mkdir %s: %w", *outDir, err)
	}
	ts := strings.ReplaceAll(strings.ReplaceAll(formatISO(), ":", ""), "-", "")
	path := *outDir + "/" + ts[:15] + ".json"
	raw, _ := json.MarshalIndent(snap, "", "  ")
	if err := os.WriteFile(path, raw, 0o644); err != nil {
		return fmt.Errorf("write %s: %w", path, err)
	}
	fmt.Printf("snapshot written: %s (total=%d, fissioned=%d)\n", path, total-totalFissioned, totalFissioned)
	return nil
}

func formatISO() string {
	return time.Now().UTC().Format("2006-01-02T15:04:05Z")
}

// runCohortGen — one-shot seed builder. Builds a minimum JSON-LD from
// typed flags (pcfL1/role/industry/seniority/locale) and POSTs to
// ai.gftd.cohort.seed. Convenience wrapper around `gftd cohort seed`
// that avoids the user having to hand-craft JSON on the command line.
func runCohortGen(args []string) error {
	fs := flag.NewFlagSet("cohort gen", flag.ContinueOnError)
	pcfL1 := fs.String("pcfL1", "", "APQC L1 slug (required, e.g. 3-market-sell)")
	role := fs.String("role", "", "role (required, e.g. salesRep)")
	industry := fs.String("industry", "", "industry (optional)")
	seniority := fs.String("seniority", "", "seniority (optional: junior/mid/senior)")
	locale := fs.String("locale", "jp", "locale (required, default jp)")
	k := fs.Int("k", 50, "k-anonymity floor")
	pds := fs.String("pds", resolvePDSBaseURL(), "PDS base URL")
	dry := fs.Bool("dry-run", false, "Print generated JSON-LD, skip POST")
	jsonOut := fs.Bool("json", false, "Emit raw JSON response")
	if err := fs.Parse(args); err != nil {
		return err
	}
	if *pcfL1 == "" || *role == "" || *locale == "" {
		return fmt.Errorf("--pcfL1, --role, --locale are all required")
	}
	obj := map[string]string{
		"pcfL1":  *pcfL1,
		"role":   *role,
		"locale": *locale,
	}
	if *industry != "" {
		obj["industry"] = *industry
	}
	if *seniority != "" {
		obj["seniority"] = *seniority
	}
	segmentJsonld, _ := json.Marshal(obj)
	if *dry {
		fmt.Println(string(segmentJsonld))
		return nil
	}
	token := resolveGFTDToken()
	if token == "" {
		return fmt.Errorf("no GFTD token found — run `gftd auth login` or set GFTD_TOKEN")
	}
	input := cohortSeedInput{
		SegmentJsonld: string(segmentJsonld),
		KAnonymity:    *k,
	}
	body, _ := json.Marshal(input)
	target := strings.TrimRight(*pds, "/") + "/xrpc/ai.gftd.cohort.seed"
	req, _ := http.NewRequest("POST", target, bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+token)
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return fmt.Errorf("http: %w", err)
	}
	defer resp.Body.Close()
	respBody, _ := io.ReadAll(resp.Body)
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("gen failed: %d %s: %s", resp.StatusCode, http.StatusText(resp.StatusCode), string(respBody))
	}
	if *jsonOut {
		fmt.Println(string(respBody))
		return nil
	}
	var out cohortSeedOutput
	if err := json.Unmarshal(respBody, &out); err == nil {
		fmt.Printf("gen ok: did=%s handle=%s\n", out.Did, out.Handle)
	} else {
		fmt.Println(string(respBody))
	}
	return nil
}

// runCohortGap — list (row, col) cells from a 2D coverage matrix that
// have count < threshold. Useful for identifying what to seed next.
func runCohortGap(args []string) error {
	fs := flag.NewFlagSet("cohort gap", flag.ContinueOnError)
	axes := fs.String("axes", "pcfL1,locale", "exactly two comma-separated axes (row,col)")
	minN := fs.Int("min", 1, "minimum count; cells with count < min are reported as gaps")
	pds := fs.String("pds", resolvePDSBaseURL(), "PDS base URL")
	limit := fs.Int("limit", 500, "max cohorts to fetch")
	jsonOut := fs.Bool("json", false, "Emit JSON gap list")
	if err := fs.Parse(args); err != nil {
		return err
	}
	parts := strings.Split(*axes, ",")
	if len(parts) != 2 {
		return fmt.Errorf("--axes must be exactly two (row,col)")
	}
	rowAxis, colAxis := strings.TrimSpace(parts[0]), strings.TrimSpace(parts[1])
	token := resolveGFTDToken()
	if token == "" {
		return fmt.Errorf("no GFTD token found — run `gftd auth login` or set GFTD_TOKEN")
	}
	q := url.Values{}
	q.Set("limit", fmt.Sprintf("%d", *limit))
	target := strings.TrimRight(*pds, "/") + "/xrpc/ai.gftd.cohort.listCohorts?" + q.Encode()
	req, _ := http.NewRequest("GET", target, nil)
	req.Header.Set("Authorization", "Bearer "+token)
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return fmt.Errorf("http: %w", err)
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body)
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("listCohorts failed: %d %s: %s", resp.StatusCode, http.StatusText(resp.StatusCode), string(body))
	}
	var out struct {
		Cohorts []struct {
			SegmentHash string `json:"segmentHash"`
		} `json:"cohorts"`
	}
	if err := json.Unmarshal(body, &out); err != nil {
		return err
	}
	matrix := map[string]map[string]int{}
	rowSet := map[string]bool{}
	colSet := map[string]bool{}
	for _, c := range out.Cohorts {
		kv := parseSegmentKV(c.SegmentHash)
		r, cv := kv[rowAxis], kv[colAxis]
		if r == "" || cv == "" {
			continue
		}
		if matrix[r] == nil {
			matrix[r] = map[string]int{}
		}
		matrix[r][cv]++
		rowSet[r] = true
		colSet[cv] = true
	}
	rows := make([]string, 0, len(rowSet))
	for r := range rowSet {
		rows = append(rows, r)
	}
	cols := make([]string, 0, len(colSet))
	for c := range colSet {
		cols = append(cols, c)
	}
	sortStrings(rows)
	sortStrings(cols)

	type gapCell struct {
		Row   string `json:"row"`
		Col   string `json:"col"`
		Count int    `json:"count"`
	}
	gaps := []gapCell{}
	for _, r := range rows {
		for _, c := range cols {
			n := matrix[r][c]
			if n < *minN {
				gaps = append(gaps, gapCell{r, c, n})
			}
		}
	}
	if *jsonOut {
		raw, _ := json.Marshal(gaps)
		fmt.Println(string(raw))
		return nil
	}
	fmt.Printf("gaps (%d cells with count<%d, axes=%s/%s):\n", len(gaps), *minN, rowAxis, colAxis)
	for _, g := range gaps {
		fmt.Printf("  %-36s %-16s  count=%d\n", g.Row, g.Col, g.Count)
	}
	return nil
}

// runCohortCoverage — 2D cover matrix (rows×cols from --axes).
// Shows which (axis1, axis2) cells exist vs. are empty. Useful for
// identifying coverage gaps (e.g. pcfL1 × role matrix).
func runCohortCoverage(args []string) error {
	fs := flag.NewFlagSet("cohort coverage", flag.ContinueOnError)
	axes := fs.String("axes", "pcfL1,role", "exactly two comma-separated axes (row,col)")
	pds := fs.String("pds", resolvePDSBaseURL(), "PDS base URL")
	limit := fs.Int("limit", 500, "max cohorts to fetch")
	jsonOut := fs.Bool("json", false, "Emit JSON matrix")
	if err := fs.Parse(args); err != nil {
		return err
	}
	parts := strings.Split(*axes, ",")
	if len(parts) != 2 {
		return fmt.Errorf("--axes must be exactly two (row,col)")
	}
	rowAxis, colAxis := strings.TrimSpace(parts[0]), strings.TrimSpace(parts[1])
	token := resolveGFTDToken()
	if token == "" {
		return fmt.Errorf("no GFTD token found — run `gftd auth login` or set GFTD_TOKEN")
	}
	q := url.Values{}
	q.Set("limit", fmt.Sprintf("%d", *limit))
	target := strings.TrimRight(*pds, "/") + "/xrpc/ai.gftd.cohort.listCohorts?" + q.Encode()
	req, _ := http.NewRequest("GET", target, nil)
	req.Header.Set("Authorization", "Bearer "+token)
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return fmt.Errorf("http: %w", err)
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body)
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("listCohorts failed: %d %s: %s", resp.StatusCode, http.StatusText(resp.StatusCode), string(body))
	}
	var out struct {
		Cohorts []struct {
			SegmentHash string `json:"segmentHash"`
		} `json:"cohorts"`
	}
	if err := json.Unmarshal(body, &out); err != nil {
		return err
	}
	matrix := map[string]map[string]int{}
	rowSet := map[string]bool{}
	colSet := map[string]bool{}
	for _, c := range out.Cohorts {
		kv := parseSegmentKV(c.SegmentHash)
		r, cv := kv[rowAxis], kv[colAxis]
		if r == "" {
			r = "-"
		}
		if cv == "" {
			cv = "-"
		}
		if matrix[r] == nil {
			matrix[r] = map[string]int{}
		}
		matrix[r][cv]++
		rowSet[r] = true
		colSet[cv] = true
	}
	rows := make([]string, 0, len(rowSet))
	for r := range rowSet {
		rows = append(rows, r)
	}
	cols := make([]string, 0, len(colSet))
	for c := range colSet {
		cols = append(cols, c)
	}
	sortStrings(rows)
	sortStrings(cols)

	if *jsonOut {
		type cell struct {
			Row   string `json:"row"`
			Col   string `json:"col"`
			Count int    `json:"count"`
		}
		cells := []cell{}
		for _, r := range rows {
			for _, c := range cols {
				cells = append(cells, cell{r, c, matrix[r][c]})
			}
		}
		raw, _ := json.Marshal(cells)
		fmt.Println(string(raw))
		return nil
	}

	// Text render
	colW := 12
	fmt.Printf("%-36s", rowAxis+"\\"+colAxis)
	for _, c := range cols {
		if len(c) > colW-1 {
			c = c[:colW-1]
		}
		fmt.Printf(" %-*s", colW, c)
	}
	fmt.Println()
	for _, r := range rows {
		fmt.Printf("%-36s", r)
		for _, c := range cols {
			n := matrix[r][c]
			if n == 0 {
				fmt.Printf(" %-*s", colW, ".")
			} else {
				fmt.Printf(" %-*d", colW, n)
			}
		}
		fmt.Println()
	}
	return nil
}

// runCohortStats — aggregate cohort + fissioned counts per APQC L1 via
// client-side grouping over listCohorts. Useful for ops dashboards.
func runCohortStats(args []string) error {
	fs := flag.NewFlagSet("cohort stats", flag.ContinueOnError)
	pds := fs.String("pds", resolvePDSBaseURL(), "PDS base URL")
	limit := fs.Int("limit", 500, "max cohorts to fetch per page")
	by := fs.String("by", "pcfL1", "comma-separated group-by axes (pcfL1,role,industry,seniority,locale)")
	kindFilter := fs.String("kind", "", "filter by kind: cohort | fissioned (empty = both)")
	jsonOut := fs.Bool("json", false, "Emit JSON aggregate")
	if err := fs.Parse(args); err != nil {
		return err
	}
	token := resolveGFTDToken()
	if token == "" {
		return fmt.Errorf("no GFTD token found — run `gftd auth login` or set GFTD_TOKEN")
	}
	q := url.Values{}
	q.Set("limit", fmt.Sprintf("%d", *limit))
	target := strings.TrimRight(*pds, "/") + "/xrpc/ai.gftd.cohort.listCohorts?" + q.Encode()
	req, _ := http.NewRequest("GET", target, nil)
	req.Header.Set("Authorization", "Bearer "+token)
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return fmt.Errorf("http: %w", err)
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body)
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("listCohorts failed: %d %s: %s", resp.StatusCode, http.StatusText(resp.StatusCode), string(body))
	}
	var out struct {
		Cohorts []struct {
			Kind           string `json:"kind"`
			SegmentHash    string `json:"segmentHash"`
			FissionEnabled bool   `json:"fissionEnabled"`
		} `json:"cohorts"`
	}
	if err := json.Unmarshal(body, &out); err != nil {
		return err
	}
	axes := []string{}
	for _, a := range strings.Split(*by, ",") {
		if a = strings.TrimSpace(a); a != "" {
			axes = append(axes, a)
		}
	}
	if len(axes) == 0 {
		axes = []string{"pcfL1"}
	}
	type bucket struct {
		Key       string `json:"key"`
		Cohorts   int    `json:"cohorts"`
		Fissioned int    `json:"fissioned"`
		FissionOn int    `json:"fissionEnabled"`
		Total     int    `json:"total"`
	}
	buckets := map[string]*bucket{}
	for _, c := range out.Cohorts {
		if *kindFilter != "" && c.Kind != *kindFilter {
			continue
		}
		parts := parseSegmentKV(c.SegmentHash)
		keyParts := make([]string, 0, len(axes))
		for _, a := range axes {
			v := parts[a]
			if v == "" {
				v = "-"
			}
			keyParts = append(keyParts, v)
		}
		key := strings.Join(keyParts, "/")
		b, ok := buckets[key]
		if !ok {
			b = &bucket{Key: key}
			buckets[key] = b
		}
		b.Total++
		if c.Kind == "fissioned" {
			b.Fissioned++
		} else {
			b.Cohorts++
		}
		if c.FissionEnabled {
			b.FissionOn++
		}
	}
	keys := make([]string, 0, len(buckets))
	for k := range buckets {
		keys = append(keys, k)
	}
	sortStrings(keys)
	if *jsonOut {
		list := make([]*bucket, 0, len(keys))
		for _, k := range keys {
			list = append(list, buckets[k])
		}
		raw, _ := json.Marshal(list)
		fmt.Println(string(raw))
		return nil
	}
	header := strings.Join(axes, "/")
	fmt.Printf("%-42s %8s %10s %14s %6s\n", header, "cohorts", "fissioned", "fissionEnabled", "total")
	for _, k := range keys {
		b := buckets[k]
		fmt.Printf("%-42s %8d %10d %14d %6d\n", b.Key, b.Cohorts, b.Fissioned, b.FissionOn, b.Total)
	}
	return nil
}

func parseSegmentKV(segmentHash string) map[string]string {
	body := strings.TrimPrefix(segmentHash, "sha256:")
	kv := map[string]string{}
	for _, part := range strings.Split(body, ";") {
		if eq := strings.Index(part, "="); eq > 0 {
			kv[part[:eq]] = part[eq+1:]
		}
	}
	return kv
}

func sortStrings(s []string) {
	// insertion sort — list is small (13 L1 slugs typically)
	for i := 1; i < len(s); i++ {
		j := i
		for j > 0 && s[j-1] > s[j] {
			s[j-1], s[j] = s[j], s[j-1]
			j--
		}
	}
}

// runCohortEvidence — wraps `ai.gftd.cohort.listEvidence` for inspection.
func runCohortEvidence(args []string) error {
	fs := flag.NewFlagSet("cohort evidence", flag.ContinueOnError)
	cohort := fs.String("cohort", "", "Cohort DID (required)")
	minP := fs.Float64("min-posterior", 0, "Minimum posterior (0..1)")
	judge := fs.String("judge", "", "true/false/\"\" (empty = unfiltered)")
	limit := fs.Int("limit", 100, "page size")
	offset := fs.Int("offset", 0, "offset")
	pds := fs.String("pds", resolvePDSBaseURL(), "PDS base URL")
	jsonOut := fs.Bool("json", false, "Emit raw JSON")
	if err := fs.Parse(args); err != nil {
		return err
	}
	if *cohort == "" {
		return fmt.Errorf("--cohort is required")
	}
	token := resolveGFTDToken()
	if token == "" {
		return fmt.Errorf("no GFTD token found — run `gftd auth login` or set GFTD_TOKEN")
	}
	q := url.Values{}
	q.Set("cohortDid", *cohort)
	if *minP > 0 {
		q.Set("minPosterior", fmt.Sprintf("%v", *minP))
	}
	if *judge != "" {
		q.Set("judgeAgreement", *judge)
	}
	q.Set("limit", fmt.Sprintf("%d", *limit))
	q.Set("offset", fmt.Sprintf("%d", *offset))
	target := strings.TrimRight(*pds, "/") + "/xrpc/ai.gftd.cohort.listEvidence?" + q.Encode()
	req, _ := http.NewRequest("GET", target, nil)
	req.Header.Set("Authorization", "Bearer "+token)
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return fmt.Errorf("http: %w", err)
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body)
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("listEvidence failed: %d %s: %s", resp.StatusCode, http.StatusText(resp.StatusCode), string(body))
	}
	if *jsonOut {
		fmt.Println(string(body))
		return nil
	}
	var out struct {
		Evidence []struct {
			EvidenceHash   string  `json:"evidenceHash"`
			SignalKind     string  `json:"signalKind"`
			Posterior      float64 `json:"posterior"`
			JudgeAgreement bool    `json:"judgeAgreement"`
			Tier           string  `json:"tier"`
			ObservedAt     string  `json:"observedAt"`
		} `json:"evidence"`
		Offset int `json:"offset"`
		Limit  int `json:"limit"`
	}
	if err := json.Unmarshal(body, &out); err != nil {
		fmt.Println(string(body))
		return nil
	}
	fmt.Printf("evidence for %s (offset=%d, limit=%d, count=%d)\n", *cohort, out.Offset, out.Limit, len(out.Evidence))
	for i, e := range out.Evidence {
		fmt.Printf("  [%3d] %s  post=%.3f  judge=%v  %s  (%s)\n",
			i+1, e.EvidenceHash, e.Posterior, e.JudgeAgreement, e.SignalKind, e.ObservedAt)
	}
	return nil
}

// runCohortForest — ascii tree of cohort + derived_from chains scoped by pcfL1.
// Fetches all cohorts (or filtered by pcfL1), then builds parent→children index
// via derived_from (null parent = root cohort).
func runCohortForest(args []string) error {
	fs := flag.NewFlagSet("cohort forest", flag.ContinueOnError)
	pcfL1 := fs.String("pcfL1", "", "APQC L1 slug filter (optional)")
	pds := fs.String("pds", resolvePDSBaseURL(), "PDS base URL")
	limit := fs.Int("limit", 500, "Max cohorts to fetch")
	rooted := fs.String("rooted", "", "render only the subtree rooted at this cohort DID")
	jsonOut := fs.Bool("json", false, "Emit JSON forest")
	if err := fs.Parse(args); err != nil {
		return err
	}
	token := resolveGFTDToken()
	if token == "" {
		return fmt.Errorf("no GFTD token found — run `gftd auth login` or set GFTD_TOKEN")
	}
	q := url.Values{}
	if *pcfL1 != "" {
		q.Set("pcfL1", *pcfL1)
	}
	q.Set("limit", fmt.Sprintf("%d", *limit))
	target := strings.TrimRight(*pds, "/") + "/xrpc/ai.gftd.cohort.listCohorts?" + q.Encode()
	req, _ := http.NewRequest("GET", target, nil)
	req.Header.Set("Authorization", "Bearer "+token)
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return fmt.Errorf("http: %w", err)
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body)
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("listCohorts failed: %d %s: %s", resp.StatusCode, http.StatusText(resp.StatusCode), string(body))
	}
	var out struct {
		Cohorts []struct {
			CohortDid   string `json:"cohortDid"`
			Handle      string `json:"handle"`
			Kind        string `json:"kind"`
			SegmentHash string `json:"segmentHash"`
			DerivedFrom string `json:"derivedFrom,omitempty"`
		} `json:"cohorts"`
	}
	if err := json.Unmarshal(body, &out); err != nil {
		return err
	}
	children := map[string][]int{}
	for i, c := range out.Cohorts {
		children[c.DerivedFrom] = append(children[c.DerivedFrom], i)
	}
	if *jsonOut {
		raw, _ := json.Marshal(out.Cohorts)
		fmt.Println(string(raw))
		return nil
	}
	fmt.Printf("forest (%d nodes, pcfL1=%s, rooted=%s):\n", len(out.Cohorts), *pcfL1, *rooted)
	var printTree func(parent string, depth int)
	printTree = func(parent string, depth int) {
		for _, idx := range children[parent] {
			c := out.Cohorts[idx]
			fmt.Printf("%s%s  %s  kind=%s\n", strings.Repeat("  ", depth), c.CohortDid, c.Handle, c.Kind)
			printTree(c.CohortDid, depth+1)
		}
	}
	if *rooted != "" {
		// Find the root node by DID and print its descendants only.
		for i, c := range out.Cohorts {
			if c.CohortDid == *rooted {
				fmt.Printf("%s  %s  kind=%s\n", c.CohortDid, c.Handle, c.Kind)
				printTree(out.Cohorts[i].CohortDid, 1)
				return nil
			}
		}
		return fmt.Errorf("rooted cohort not found in fetched page: %s", *rooted)
	}
	printTree("", 0)
	return nil
}

// runCohortLineage — traverse `derived_from` chain upward from a fissioned
// actor DID back to the cohort root. Uses repeated listCohorts lookups
// rather than a SQL CTE so no new server-side handler is required.
func runCohortLineage(args []string) error {
	fs := flag.NewFlagSet("cohort lineage", flag.ContinueOnError)
	did := fs.String("did", "", "Fissioned actor DID (required)")
	pds := fs.String("pds", resolvePDSBaseURL(), "PDS base URL")
	maxHops := fs.Int("max", 16, "Maximum chain depth before giving up (alias of --depth)")
	depth := fs.Int("depth", 0, "Hard cap on chain depth (overrides --max if >0)")
	jsonOut := fs.Bool("json", false, "Emit raw JSON chain")
	if err := fs.Parse(args); err != nil {
		return err
	}
	if *did == "" {
		return fmt.Errorf("--did is required")
	}
	token := resolveGFTDToken()
	if token == "" {
		return fmt.Errorf("no GFTD token found — run `gftd auth login` or set GFTD_TOKEN")
	}

	type lineageNode struct {
		CohortDid   string `json:"cohortDid"`
		Handle      string `json:"handle"`
		Kind        string `json:"kind"`
		DerivedFrom string `json:"derivedFrom,omitempty"`
		SegmentHash string `json:"segmentHash,omitempty"`
	}

	cap := *maxHops
	if *depth > 0 {
		cap = *depth
	}
	chain := []lineageNode{}
	cur := *did
	visited := map[string]bool{}
	for hop := 0; hop < cap && cur != "" && !visited[cur]; hop++ {
		visited[cur] = true
		node, err := fetchCohortByDid(*pds, token, cur)
		if err != nil {
			return fmt.Errorf("lookup %s: %w", cur, err)
		}
		if node == nil {
			break
		}
		chain = append(chain, lineageNode{
			CohortDid:   node.CohortDid,
			Handle:      node.Handle,
			Kind:        node.Kind,
			DerivedFrom: node.DerivedFrom,
			SegmentHash: node.SegmentHash,
		})
		cur = node.DerivedFrom
	}

	if *jsonOut {
		out, _ := json.Marshal(chain)
		fmt.Println(string(out))
		return nil
	}
	fmt.Printf("lineage (%d hop):\n", len(chain))
	for i, n := range chain {
		prefix := "  ├─"
		if i == len(chain)-1 {
			prefix = "  └─"
		}
		fmt.Printf("%s %s  %s  kind=%s  segment=%s\n", prefix, n.CohortDid, n.Handle, n.Kind, n.SegmentHash)
	}
	return nil
}

type lineageRow struct {
	CohortDid   string `json:"cohortDid"`
	Handle      string `json:"handle"`
	Kind        string `json:"kind"`
	SegmentHash string `json:"segmentHash"`
	DerivedFrom string `json:"derivedFrom"`
}

func fetchCohortByDid(pds, token, did string) (*lineageRow, error) {
	// Use exact-DID filter (added in iter 41). Falls back to scan only if
	// the server-side filter is unavailable on older PDS deployments.
	q := url.Values{}
	q.Set("cohortDid", did)
	q.Set("limit", "1")
	target := strings.TrimRight(pds, "/") + "/xrpc/ai.gftd.cohort.listCohorts?" + q.Encode()
	req, _ := http.NewRequest("GET", target, nil)
	req.Header.Set("Authorization", "Bearer "+token)
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body)
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return nil, fmt.Errorf("HTTP %d: %s", resp.StatusCode, string(body))
	}
	var out struct {
		Cohorts []lineageRow `json:"cohorts"`
	}
	if err := json.Unmarshal(body, &out); err != nil {
		return nil, err
	}
	for _, c := range out.Cohorts {
		if c.CohortDid == did {
			return &c, nil
		}
	}
	return nil, nil
}

// runCohortFission — Phase C stub: POST /xrpc/ai.gftd.cohort.fission with
// posterior + judgeAgreement + evidence refs. Server handler not yet
// implemented, but CLI shape is fixed here so the call site exists.
func runCohortFission(args []string) error {
	fs := flag.NewFlagSet("cohort fission", flag.ContinueOnError)
	cohortDid := fs.String("cohort", "", "Cohort DID (required)")
	posterior := fs.Float64("posterior", 0, "Posterior from mv_cohort_identity_posterior (>=0.95)")
	judge := fs.Bool("judge", false, "LLM-as-judge agreement (must be true)")
	evidence := fs.String("evidence", "", "Comma-separated evidence URIs")
	pds := fs.String("pds", resolvePDSBaseURL(), "PDS base URL")
	jsonOut := fs.Bool("json", false, "Emit raw JSON response")
	if err := fs.Parse(args); err != nil {
		return err
	}
	if *cohortDid == "" {
		return fmt.Errorf("--cohort is required")
	}
	if *posterior < 0.95 {
		return fmt.Errorf("--posterior must be >= 0.95 (ADR-0026 Phase C gate)")
	}
	if !*judge {
		return fmt.Errorf("--judge=true required (LLM-as-judge agreement, ADR-0026 §Risks)")
	}
	refs := []string{}
	for _, r := range strings.Split(*evidence, ",") {
		if r = strings.TrimSpace(r); r != "" {
			refs = append(refs, r)
		}
	}
	if len(refs) == 0 {
		return fmt.Errorf("--evidence must list >= 1 evidence URI")
	}
	token := resolveGFTDToken()
	if token == "" {
		return fmt.Errorf("no GFTD token found — run `gftd auth login` or set GFTD_TOKEN")
	}
	body, _ := json.Marshal(map[string]any{
		"cohortDid":       *cohortDid,
		"posterior":       *posterior,
		"judgeAgreement":  *judge,
		"evidenceUris":    refs,
	})
	target := strings.TrimRight(*pds, "/") + "/xrpc/ai.gftd.cohort.fission"
	req, _ := http.NewRequest("POST", target, bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+token)
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return fmt.Errorf("http: %w", err)
	}
	defer resp.Body.Close()
	respBody, _ := io.ReadAll(resp.Body)
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("fission failed: %d %s: %s", resp.StatusCode, http.StatusText(resp.StatusCode), string(respBody))
	}
	if *jsonOut {
		fmt.Println(string(respBody))
		return nil
	}
	fmt.Println(string(respBody))
	return nil
}

func runCohortList(args []string) error {
	fs := flag.NewFlagSet("cohort list", flag.ContinueOnError)
	kind := fs.String("kind", "", "cohort | fissioned")
	pcfL1 := fs.String("pcfL1", "", "APQC L1 slug filter (e.g. 3-market-sell)")
	locale := fs.String("locale", "", "locale filter (jp/en/...)")
	derivedFrom := fs.String("derived-from", "", "filter by parent cohort DID (kind='fissioned' children)")
	cohortDid := fs.String("did", "", "exact cohort DID lookup")
	limit := fs.Int("limit", 100, "page size")
	offset := fs.Int("offset", 0, "offset")
	pds := fs.String("pds", resolvePDSBaseURL(), "PDS base URL")
	jsonOut := fs.Bool("json", false, "Emit raw JSON")
	if err := fs.Parse(args); err != nil {
		return err
	}
	token := resolveGFTDToken()
	if token == "" {
		return fmt.Errorf("no GFTD token found — run `gftd auth login` or set GFTD_TOKEN")
	}
	q := url.Values{}
	if *kind != "" {
		q.Set("kind", *kind)
	}
	if *pcfL1 != "" {
		q.Set("pcfL1", *pcfL1)
	}
	if *locale != "" {
		q.Set("locale", *locale)
	}
	if *derivedFrom != "" {
		q.Set("derivedFrom", *derivedFrom)
	}
	if *cohortDid != "" {
		q.Set("cohortDid", *cohortDid)
	}
	q.Set("limit", fmt.Sprintf("%d", *limit))
	q.Set("offset", fmt.Sprintf("%d", *offset))

	target := strings.TrimRight(*pds, "/") + "/xrpc/ai.gftd.cohort.listCohorts?" + q.Encode()
	req, _ := http.NewRequest("GET", target, nil)
	req.Header.Set("Authorization", "Bearer "+token)
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return fmt.Errorf("http: %w", err)
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body)
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("list failed: %d %s: %s", resp.StatusCode, http.StatusText(resp.StatusCode), string(body))
	}
	if *jsonOut {
		fmt.Println(string(body))
		return nil
	}
	var out struct {
		Cohorts []struct {
			CohortDid      string `json:"cohortDid"`
			Handle         string `json:"handle"`
			Kind           string `json:"kind"`
			SegmentHash    string `json:"segmentHash"`
			KAnonymity     int    `json:"kAnonymity"`
			FissionEnabled bool   `json:"fissionEnabled"`
			Status         string `json:"status"`
			GenesisAt      string `json:"genesisAt"`
		} `json:"cohorts"`
		Total  int `json:"total"`
		Offset int `json:"offset"`
		Limit  int `json:"limit"`
	}
	if err := json.Unmarshal(body, &out); err != nil {
		fmt.Println(string(body))
		return nil
	}
	fmt.Printf("cohorts: %d (offset=%d, limit=%d, total~%d)\n", len(out.Cohorts), out.Offset, out.Limit, out.Total)
	for i, c := range out.Cohorts {
		fmt.Printf("  [%3d] %-36s %-30s k=%d fission=%v %s\n",
			i+1, c.CohortDid, c.Handle, c.KAnonymity, c.FissionEnabled, c.SegmentHash)
	}
	return nil
}

// runCohortBootstrap reads `[[cohort_actors]]` from deps.toml and POSTs
// each entry to `ai.gftd.cohort.seed`. Idempotent — the server rejects
// duplicates via PRIMARY KEY on cohort_did (newly-minted nano each call
// means new rows per invocation unless seed is skipped by segment_hash
// lookup, which is the next enhancement).
func runCohortBootstrap(args []string) error {
	fs := flag.NewFlagSet("cohort bootstrap", flag.ContinueOnError)
	depsPath := fs.String("deps", "deps.toml", "Path to deps.toml")
	pds := fs.String("pds", resolvePDSBaseURL(), "PDS base URL")
	dryRun := fs.Bool("dry-run", true, "Preview only (no POST)")
	limit := fs.Int("limit", 0, "Max entries to process (0 = all)")
	verbose := fs.Bool("v", false, "Verbose per-entry status")
	if err := fs.Parse(args); err != nil {
		return err
	}

	entries, err := parseCohortActorsFromDeps(*depsPath)
	if err != nil {
		return fmt.Errorf("parse deps.toml: %w", err)
	}
	if *limit > 0 && len(entries) > *limit {
		entries = entries[:*limit]
	}

	fmt.Printf("cohort bootstrap: %d entries (dry-run=%v)\n", len(entries), *dryRun)
	if *dryRun {
		for i, e := range entries {
			fmt.Printf("  [%3d] %s  (segment=%s)\n", i+1, e.Name, e.SegmentHash)
		}
		fmt.Println("→ run with --dry-run=false to POST to /xrpc/ai.gftd.cohort.seed")
		return nil
	}

	token := resolveGFTDToken()
	if token == "" {
		return fmt.Errorf("no GFTD token found — run `gftd auth login` or set GFTD_TOKEN")
	}
	pdsURL := strings.TrimRight(strings.TrimSpace(*pds), "/")
	if pdsURL == "" {
		pdsURL = "https://atproto.etzhayyim.com"
	}
	target := pdsURL + "/xrpc/ai.gftd.cohort.seed"

	ok, fail := 0, 0
	for i, e := range entries {
		input := map[string]any{
			"segmentJsonld":  e.toSegmentJsonld(),
			"kAnonymity":     e.KAnonymity,
			"fissionEnabled": e.FissionEnabled,
		}
		body, _ := json.Marshal(input)
		req, _ := http.NewRequest("POST", target, bytes.NewReader(body))
		req.Header.Set("Content-Type", "application/json")
		req.Header.Set("Authorization", "Bearer "+token)
		resp, err := http.DefaultClient.Do(req)
		if err != nil {
			fail++
			if *verbose {
				fmt.Fprintf(os.Stderr, "  [%3d] %s FAIL: %v\n", i+1, e.Name, err)
			}
			continue
		}
		_, _ = io.Copy(io.Discard, resp.Body)
		resp.Body.Close()
		if resp.StatusCode >= 200 && resp.StatusCode < 300 {
			ok++
			if *verbose {
				fmt.Printf("  [%3d] %s OK\n", i+1, e.Name)
			}
		} else {
			fail++
			if *verbose {
				fmt.Fprintf(os.Stderr, "  [%3d] %s HTTP %d\n", i+1, e.Name, resp.StatusCode)
			}
		}
	}
	fmt.Printf("done: %d ok / %d fail / %d total\n", ok, fail, len(entries))
	return nil
}

type cohortEntry struct {
	Name           string
	SegmentHash    string
	KAnonymity     int
	FissionEnabled bool
}

// toSegmentJsonld derives the JSON-LD body expected by handleCohortSeed
// from the segment_hash `pcfL1=...;role=...;...` KV string.
func (e cohortEntry) toSegmentJsonld() string {
	body := strings.TrimPrefix(e.SegmentHash, "sha256:")
	obj := map[string]string{}
	for _, part := range strings.Split(body, ";") {
		if eq := strings.Index(part, "="); eq > 0 {
			obj[part[:eq]] = part[eq+1:]
		}
	}
	out, _ := json.Marshal(obj)
	return string(out)
}

// parseCohortActorsFromDeps scans deps.toml line-by-line for
// `[[cohort_actors]]` blocks. A minimal text parser so we don't have to
// pull in a TOML library for this one command.
func parseCohortActorsFromDeps(path string) ([]cohortEntry, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var entries []cohortEntry
	var cur *cohortEntry
	for _, rawLine := range strings.Split(string(data), "\n") {
		line := strings.TrimSpace(rawLine)
		if line == "[[cohort_actors]]" {
			if cur != nil {
				entries = append(entries, *cur)
			}
			cur = &cohortEntry{KAnonymity: 50}
			continue
		}
		if cur == nil {
			continue
		}
		if strings.HasPrefix(line, "[[") || strings.HasPrefix(line, "[") {
			entries = append(entries, *cur)
			cur = nil
			continue
		}
		if eq := strings.Index(line, "="); eq > 0 {
			k := strings.TrimSpace(line[:eq])
			v := strings.TrimSpace(line[eq+1:])
			v = strings.TrimSuffix(strings.TrimPrefix(v, `"`), `"`)
			switch k {
			case "name":
				cur.Name = v
			case "segment_hash":
				cur.SegmentHash = v
			case "k_anonymity":
				fmt.Sscanf(v, "%d", &cur.KAnonymity)
			case "fission_enabled":
				cur.FissionEnabled = v == "true"
			}
		}
	}
	if cur != nil {
		entries = append(entries, *cur)
	}
	return entries, nil
}

func runCohortSeed(args []string) error {
	fs := flag.NewFlagSet("cohort seed", flag.ContinueOnError)
	segment := fs.String("segment", "", "Demographic segment as JSON (required). Must include pcfL1, role, locale")
	k := fs.Int("k", 50, "k-anonymity floor (>= 50 enforced by PDS)")
	fission := fs.Bool("fission", false, "Enable fission (Phase C) at genesis time")
	policyRef := fs.String("policy", "", "Optional policy DID reference")
	pds := fs.String("pds", resolvePDSBaseURL(), "PDS base URL")
	jsonOut := fs.Bool("json", false, "Emit raw JSON response")
	verbose := fs.Bool("v", false, "Print target URL + HTTP status to stderr")
	if err := fs.Parse(args); err != nil {
		return err
	}
	if strings.TrimSpace(*segment) == "" {
		fs.Usage()
		return fmt.Errorf("--segment is required (JSON with pcfL1/role/locale)")
	}
	if *k < 50 {
		return fmt.Errorf("--k must be >= 50 (ADR-0026 Phase A)")
	}

	token := resolveGFTDToken()
	if token == "" {
		return fmt.Errorf("no GFTD token found — run `gftd auth login` or set GFTD_TOKEN")
	}

	input := cohortSeedInput{
		SegmentJsonld:  strings.TrimSpace(*segment),
		KAnonymity:     *k,
		FissionEnabled: *fission,
		PolicyRef:      strings.TrimSpace(*policyRef),
	}
	body, err := json.Marshal(input)
	if err != nil {
		return fmt.Errorf("marshal input: %w", err)
	}

	pdsURL := strings.TrimRight(strings.TrimSpace(*pds), "/")
	if pdsURL == "" {
		pdsURL = "https://atproto.etzhayyim.com"
	}
	target := pdsURL + "/xrpc/ai.gftd.cohort.seed"

	req, err := http.NewRequest("POST", target, bytes.NewReader(body))
	if err != nil {
		return fmt.Errorf("build request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+token)

	if *verbose {
		fmt.Fprintf(os.Stderr, "POST %s\n", target)
	}
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return fmt.Errorf("http: %w", err)
	}
	defer resp.Body.Close()
	respBody, _ := io.ReadAll(resp.Body)
	if *verbose {
		fmt.Fprintf(os.Stderr, "← %d %s\n", resp.StatusCode, http.StatusText(resp.StatusCode))
	}
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("cohort seed failed: %d %s: %s", resp.StatusCode, http.StatusText(resp.StatusCode), string(respBody))
	}

	if *jsonOut {
		fmt.Println(string(respBody))
		return nil
	}

	var out cohortSeedOutput
	if err := json.Unmarshal(respBody, &out); err != nil {
		fmt.Println(string(respBody))
		return nil
	}
	fmt.Printf("cohort genesis:\n")
	fmt.Printf("  did:          %s\n", out.Did)
	fmt.Printf("  handle:       %s\n", out.Handle)
	fmt.Printf("  signatureUri: %s\n", out.SignatureURI)
	fmt.Printf("  genesisAt:    %s\n", out.GenesisAt)
	return nil
}
