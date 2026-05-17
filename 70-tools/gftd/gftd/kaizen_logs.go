package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"math"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
	"time"
)

type kaizenLogsSummary struct {
	AnalyzedAt        string               `json:"analyzedAt"`
	DataSource        string               `json:"dataSource"`
	WindowLimit       int                  `json:"windowLimit"`
	EventCount        int                  `json:"eventCount"`
	TotalErrors       int                  `json:"totalErrors"`
	OverallErrorRate  float64              `json:"overallErrorRate"`
	SlowQueries       []kaizenQueryFinding `json:"slowQueries"`
	ErrorQueries      []kaizenQueryFinding `json:"errorQueries"`
	LikelyCauses      []string             `json:"likelyCauses,omitempty"`
	ReverseTopology   []logsCause          `json:"reverseTopology,omitempty"`
	RecentErrorEvents []ocelEvent          `json:"recentErrorEvents,omitempty"`
}

type kaizenQueryFinding struct {
	Method   string  `json:"method"`
	Count    int     `json:"count"`
	Errors   int     `json:"errors"`
	ErrRate  float64 `json:"errRate"`
	AvgMs    float64 `json:"avgMs"`
	P50Ms    float64 `json:"p50Ms"`
	P99Ms    float64 `json:"p99Ms"`
	MaxMs    float64 `json:"maxMs"`
	Severity string  `json:"severity"`
}

func runKaizenLogs(args []string) error {
	fs := flag.NewFlagSet("kaizen logs", flag.ContinueOnError)
	fs.SetOutput(os.Stdout)

	pdsURL := fs.String("pds", defaultPDSURL, "PDS base URL")
	limit := fs.Int("limit", 300, "max events to fetch from logs")
	top := fs.Int("top", 8, "top N slow/error queries to show")
	showEvents := fs.Int("show-events", 20, "max recent error events to show")
	p99Threshold := fs.Float64("p99-threshold", 500, "slow query threshold (ms, p99)")
	errorRateThreshold := fs.Float64("error-rate-threshold", 1.0, "error query threshold (%)")
	jsonOut := fs.Bool("json", false, "emit JSON")
	fix := fs.Bool("fix", false, "run 'gftd code exec' with kaizen prompt")
	workspaceDir := fs.String("workspace-dir", "", "workspace root for gftd code exec (default: git root)")
	fixEngine := fs.String("fix-engine", "code-exec", "fix engine: code-exec (default) | murakumo")
	pdsURLFix := fs.String("fix-pds-url", defaultPDSURL, "PDS base URL for murakumo fix engine (used only with --fix-engine murakumo)")
	simulateFailures := fs.Int("simulate-failures", 0, "with --fix-engine murakumo, force optimizeCycle retries for regression testing")
	waitMurakumo := fs.Bool("wait", false, "with --fix-engine murakumo, wait for optimize task result")
	waitTimeoutStr := fs.String("wait-timeout", "3m", "with --wait, max wait duration for murakumo task")
	waitIntervalStr := fs.String("wait-interval", "8s", "with --wait, poll interval for murakumo task result")

	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}
	if *limit < 1 {
		return fmt.Errorf("--limit must be >= 1")
	}
	if *top < 1 {
		return fmt.Errorf("--top must be >= 1")
	}
	if *showEvents < 0 {
		return fmt.Errorf("--show-events must be >= 0")
	}
	if *p99Threshold < 0 {
		return fmt.Errorf("--p99-threshold must be >= 0")
	}
	if *errorRateThreshold < 0 {
		return fmt.Errorf("--error-rate-threshold must be >= 0")
	}
	if *simulateFailures < 0 {
		return fmt.Errorf("--simulate-failures must be >= 0")
	}
	waitTimeout, err := time.ParseDuration(strings.TrimSpace(*waitTimeoutStr))
	if err != nil || waitTimeout <= 0 {
		return fmt.Errorf("--wait-timeout must be a positive duration (e.g. 3m): %q", *waitTimeoutStr)
	}
	waitInterval, err := time.ParseDuration(strings.TrimSpace(*waitIntervalStr))
	if err != nil || waitInterval <= 0 {
		return fmt.Errorf("--wait-interval must be a positive duration (e.g. 8s): %q", *waitIntervalStr)
	}

	data, source, err := loadOcelResponse(*pdsURL, *limit)
	if err != nil {
		return err
	}

	summary := buildKaizenLogsSummary(data, source, *limit, *top, *showEvents, *p99Threshold, *errorRateThreshold)
	if *jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		if err := enc.Encode(summary); err != nil {
			return err
		}
	} else {
		printKaizenLogsSummary(summary)
	}

	if !*fix {
		return nil
	}

	wsRoot, err := resolveKaizenWorkspaceDir(*workspaceDir)
	if err != nil {
		return err
	}
	prompt := buildKaizenLogsPrompt(summary)
	switch strings.ToLower(strings.TrimSpace(*fixEngine)) {
	case "murakumo":
		return runKaizenLogsFixMurakumo(summary, *pdsURLFix, *simulateFailures, *waitMurakumo, waitTimeout, waitInterval)
	case "code-exec", "codeexec", "code":
		codeArgs := []string{
			"--dir", wsRoot,
			"--message", prompt,
		}
		return runCodeExec(codeArgs)
	default:
		return fmt.Errorf("unknown --fix-engine: %s (use code-exec or murakumo)", *fixEngine)
	}
}

func loadOcelResponse(pdsURL string, limit int) (ocelResponse, string, error) {
	cfAPIToken := resolveCFAnalyticsToken()
	accountID := "4da88288dc30d9ee257f319d3c33ecf0"
	if cfAPIToken != "" {
		data, err := fetchOcelFromAE(cfAPIToken, accountID, limit)
		if err == nil {
			return data, "analytics_engine", nil
		}
		fmt.Fprintf(os.Stderr, "WARN: Analytics Engine query failed (%v), falling back to PDS KV\n", err)
	} else if hasWranglerOAuthToken() {
		fmt.Fprintf(os.Stderr, "WARN: Wrangler OAuth detected, but Analytics Engine SQL needs CF_API_TOKEN/CLOUDFLARE_API_TOKEN; falling back to PDS KV\n")
	}

	token := resolveGFTDToken()
	if token == "" {
		return ocelResponse{}, "", analyticsAuthRequiredError()
	}
	data, err := fetchOcelFromPDS(token, strings.TrimRight(pdsURL, "/"), limit)
	if err != nil {
		return ocelResponse{}, "", err
	}
	return data, "pds_fallback", nil
}

func buildKaizenLogsSummary(data ocelResponse, source string, limit, top, showEvents int, p99Threshold, errorRateThreshold float64) kaizenLogsSummary {
	aggs := data.Aggregates
	if len(aggs) == 0 {
		aggs = aggregateFromEvents(data.Events)
	}
	methodStats := collectMethodStats(data)

	totalErrors, totalReq := deriveKaizenTotals(data, aggs)
	findings := make([]kaizenQueryFinding, 0, len(methodStats))
	for method, stat := range methodStats {
		if stat.Count <= 0 {
			continue
		}
		a := aggs[method]
		avgMs := 0.0
		if a.Count > 0 {
			avgMs = a.TotalMs / float64(a.Count)
		}
		if avgMs == 0 && stat.Count > 0 {
			avgMs = stat.MaxMs
		}
		p50 := a.P50Ms
		p99 := a.P99Ms
		if p50 == 0 && p99 == 0 {
			p50, p99 = percentiles(a.P99Samples)
		}
		if p99 == 0 {
			p99 = stat.P99Ms
		}
		maxMs := a.MaxMs
		if maxMs == 0 {
			maxMs = stat.MaxMs
		}
		errors := a.Errors
		if errors == 0 && stat.Errors > 0 {
			errors = stat.Errors
		}
		errRate := float64(errors) / float64(stat.Count) * 100
		findings = append(findings, kaizenQueryFinding{
			Method:   method,
			Count:    stat.Count,
			Errors:   errors,
			ErrRate:  round2f(errRate),
			AvgMs:    round2f(avgMs),
			P50Ms:    round2f(p50),
			P99Ms:    round2f(p99),
			MaxMs:    round2f(maxMs),
			Severity: classifySeverity(p99, errRate),
		})
	}

	sort.Slice(findings, func(i, j int) bool {
		if findings[i].P99Ms == findings[j].P99Ms {
			return findings[i].ErrRate > findings[j].ErrRate
		}
		return findings[i].P99Ms > findings[j].P99Ms
	})
	slow := make([]kaizenQueryFinding, 0, top)
	for _, f := range findings {
		if f.P99Ms >= p99Threshold {
			slow = append(slow, f)
			if len(slow) >= top {
				break
			}
		}
	}

	sort.Slice(findings, func(i, j int) bool {
		if findings[i].ErrRate == findings[j].ErrRate {
			return findings[i].Errors > findings[j].Errors
		}
		return findings[i].ErrRate > findings[j].ErrRate
	})
	errRows := make([]kaizenQueryFinding, 0, top)
	for _, f := range findings {
		if f.ErrRate >= errorRateThreshold || f.Errors > 0 {
			errRows = append(errRows, f)
			if len(errRows) >= top {
				break
			}
		}
	}

	recentErrs := make([]ocelEvent, 0, showEvents)
	for _, e := range data.Events {
		if e.Status >= 400 {
			recentErrs = append(recentErrs, e)
			if len(recentErrs) >= showEvents {
				break
			}
		}
	}

	overallErrRate := 0.0
	if totalReq > 0 {
		overallErrRate = float64(totalErrors) / float64(totalReq) * 100
	}
	diag := buildLogsDiagnostics(data, data.Events)
	return kaizenLogsSummary{
		AnalyzedAt:        time.Now().UTC().Format(time.RFC3339),
		DataSource:        source,
		WindowLimit:       limit,
		EventCount:        len(data.Events),
		TotalErrors:       totalErrors,
		OverallErrorRate:  round2f(overallErrRate),
		SlowQueries:       slow,
		ErrorQueries:      errRows,
		LikelyCauses:      diag.LikelyCauses,
		ReverseTopology:   diag.ReverseTopology,
		RecentErrorEvents: recentErrs,
	}
}

func deriveKaizenTotals(data ocelResponse, aggs map[string]ocelAgg) (totalErrors, totalReq int) {
	if len(data.Events) > 0 {
		for _, e := range data.Events {
			totalReq++
			if e.Status >= 400 {
				totalErrors++
			}
		}
		return totalErrors, totalReq
	}
	for _, a := range aggs {
		totalReq += a.Count
		totalErrors += a.Errors
	}
	return totalErrors, totalReq
}

func printKaizenLogsSummary(s kaizenLogsSummary) {
	fmt.Println("gftd kaizen logs — Query速度/エラー分析")
	fmt.Printf("  analyzed_at: %s\n", s.AnalyzedAt)
	fmt.Printf("  source:      %s\n", s.DataSource)
	fmt.Printf("  limit:       %d\n", s.WindowLimit)
	fmt.Printf("  events:      %d\n", s.EventCount)
	fmt.Printf("  errors:      %d (%.2f%%)\n\n", s.TotalErrors, s.OverallErrorRate)

	fmt.Println("  Slow Queries:")
	fmt.Println("    p99(ms)   err%   count  method")
	if len(s.SlowQueries) == 0 {
		fmt.Println("    (none above threshold)")
	}
	for _, q := range s.SlowQueries {
		fmt.Printf("    %7.0f  %5.2f  %6d  %s\n", q.P99Ms, q.ErrRate, q.Count, q.Method)
	}

	fmt.Println("\n  Error Queries:")
	fmt.Println("    err%     errs  count  method")
	if len(s.ErrorQueries) == 0 {
		fmt.Println("    (none)")
	}
	for _, q := range s.ErrorQueries {
		fmt.Printf("    %6.2f  %6d  %6d  %s\n", q.ErrRate, q.Errors, q.Count, q.Method)
	}

	if len(s.RecentErrorEvents) > 0 {
		fmt.Println("\n  Recent Error Events:")
		fmt.Println("    ts                   status  ms   method")
		for _, e := range s.RecentErrorEvents {
			ts := e.TS
			if len(ts) > 19 {
				ts = ts[:19]
			}
			fmt.Printf("    %-19s  %6d  %3d  %s\n", ts, e.Status, e.Ms, e.Method)
		}
	}

	if len(s.ReverseTopology) > 0 {
		fmt.Println("\n  Reverse Topology:")
		fmt.Println("    severity  key              root_cause")
		for _, cause := range s.ReverseTopology {
			fmt.Printf("    %-8s  %-15s  %s\n", cause.Severity, cause.Key, cause.RootCause)
		}
	}
}

func buildKaizenLogsPrompt(s kaizenLogsSummary) string {
	var b strings.Builder
	b.WriteString("ログ由来の性能/障害 kaizen を実施してください。\n")
	b.WriteString("目的: 遅い query と高エラー率メソッドの原因をコードから特定し、改善案と必要なら修正を行う。\n\n")
	b.WriteString("観測サマリ:\n")
	b.WriteString(fmt.Sprintf("- analyzed_at: %s\n", s.AnalyzedAt))
	b.WriteString(fmt.Sprintf("- source: %s\n", s.DataSource))
	b.WriteString(fmt.Sprintf("- total_events: %d\n", s.EventCount))
	b.WriteString(fmt.Sprintf("- total_errors: %d (%.2f%%)\n", s.TotalErrors, s.OverallErrorRate))

	b.WriteString("\n遅い query (p99上位):\n")
	for _, q := range s.SlowQueries {
		b.WriteString(fmt.Sprintf("- %s: p99=%.0fms p50=%.0fms avg=%.0fms errRate=%.2f%% count=%d\n",
			q.Method, q.P99Ms, q.P50Ms, q.AvgMs, q.ErrRate, q.Count))
	}

	b.WriteString("\nエラー query (errRate上位):\n")
	for _, q := range s.ErrorQueries {
		b.WriteString(fmt.Sprintf("- %s: errRate=%.2f%% errors=%d/%d p99=%.0fms\n",
			q.Method, q.ErrRate, q.Errors, q.Count, q.P99Ms))
	}

	if len(s.RecentErrorEvents) > 0 {
		b.WriteString("\n最近のエラーイベント:\n")
		for _, e := range s.RecentErrorEvents {
			b.WriteString(fmt.Sprintf("- ts=%s status=%d ms=%d method=%s auth=%s err=%s\n",
				e.TS, e.Status, e.Ms, e.Method, e.Auth, e.Err))
		}
	}

	if len(s.ReverseTopology) > 0 {
		b.WriteString("\n逆トポロジーソート済みの根因候補:\n")
		for _, cause := range s.ReverseTopology {
			b.WriteString(fmt.Sprintf("- [%s] %s: %s / action=%s\n",
				strings.ToUpper(cause.Severity), cause.Key, cause.RootCause, cause.Action))
		}
	}

	b.WriteString("\nやってほしいこと:\n")
	b.WriteString("1. 上記メソッド実装を特定し、遅延/失敗の主要因を列挙。\n")
	b.WriteString("2. すぐ効く改善を優先して実装 (N+1削減、不要I/O削減、キャッシュ、validation、error handling)。\n")
	b.WriteString("3. 変更点、想定改善効果、追加テストをまとめる。\n")
	b.WriteString("4. 実行可能な検証コマンドを提示する。\n")
	return b.String()
}

func runKaizenLogsFixMurakumo(s kaizenLogsSummary, pdsURL string, simulateFailures int, wait bool, waitTimeout, waitInterval time.Duration) error {
	fmt.Fprintf(os.Stderr, "==> kaizen logs fix-engine=murakumo\n")
	repoRoot, err := findGitRoot(".")
	if err != nil {
		return err
	}
	resolvedToken, err := ensurePDSToken(repoRoot, "")
	if err != nil {
		return err
	}

	scorePayload := `{"minRows":50,"sampleRows":64,"maxLabels":0}`
	scoreResp, err := callMurakumoNSID(repoRoot, strings.TrimSpace(pdsURL), resolvedToken, "ai.gftd.murakumo.scoreDataQuality", scorePayload)
	if err != nil {
		return fmt.Errorf("murakumo scoreDataQuality failed: %w", err)
	}
	fmt.Println(scoreResp)

	ingestCount := 10
	trainCount := 4
	samplesPer := 200
	evalLimit := 20

	maxP99 := 0.0
	for _, q := range s.SlowQueries {
		if q.P99Ms > maxP99 {
			maxP99 = q.P99Ms
		}
	}
	if maxP99 >= 10000 {
		trainCount = 8
		ingestCount = 20
		samplesPer = 256
	}
	if s.TotalErrors >= 20 {
		evalLimit = 40
	}

	optPayload := map[string]any{
		"ingestStart": 0,
		"ingestCount": ingestCount,
		"trainStart":  0,
		"trainCount":  trainCount,
		"samplesPer":  samplesPer,
		"evalLimit":   evalLimit,
	}
	if simulateFailures > 0 {
		optPayload["simulateFailures"] = simulateFailures
	}
	raw, _ := json.Marshal(optPayload)
	optResp, err := callMurakumoNSID(repoRoot, strings.TrimSpace(pdsURL), resolvedToken, "ai.gftd.murakumo.optimizeCycle", string(raw))
	if err != nil {
		return fmt.Errorf("murakumo optimizeCycle failed: %w", err)
	}
	fmt.Println(optResp)

	notes := []string{
		"murakumo scoreDataQuality + optimizeCycle submitted from gftd kaizen logs",
		"maxP99Ms=" + strconv.FormatFloat(maxP99, 'f', 0, 64),
		"totalErrors=" + strconv.Itoa(s.TotalErrors),
		"optimizePayload=" + string(raw),
	}
	fmt.Fprintf(os.Stderr, "==> murakumo fix submitted: %s\n", strings.Join(notes, " | "))
	if !wait {
		return nil
	}

	var optRun struct {
		RunID  string `json:"runId"`
		Status string `json:"status"`
		TaskID string `json:"taskId"`
	}
	if err := json.Unmarshal([]byte(optResp), &optRun); err != nil {
		return fmt.Errorf("parse optimizeCycle response: %w", err)
	}
	if strings.TrimSpace(optRun.TaskID) == "" {
		return fmt.Errorf("optimizeCycle response missing taskId: %s", strings.TrimSpace(optResp))
	}
	if strings.EqualFold(strings.TrimSpace(optRun.Status), "completed") {
		fmt.Fprintf(os.Stderr, "==> murakumo optimize already completed (control-plane) taskId=%s\n", optRun.TaskID)
		return nil
	}
	fmt.Fprintf(os.Stderr, "==> waiting murakumo task result taskId=%s timeout=%s interval=%s\n", optRun.TaskID, waitTimeout.String(), waitInterval.String())

	resultBody, err := waitMurakumoTaskResult(repoRoot, strings.TrimSpace(pdsURL), resolvedToken, optRun.TaskID, waitTimeout, waitInterval)
	if err != nil {
		return err
	}
	fmt.Println(resultBody)
	fmt.Fprintf(os.Stderr, "==> murakumo task completed taskId=%s\n", optRun.TaskID)
	return nil
}

func callMurakumoNSID(repoRoot, pdsURL, token, nsid, payload string) (string, error) {
	nsidName := strings.TrimSpace(nsid)
	if nsidName == "" {
		return "", fmt.Errorf("murakumo nsid is empty")
	}
	body := strings.TrimSpace(payload)
	if body == "" {
		body = "{}"
	}
	if !json.Valid([]byte(body)) {
		return "", fmt.Errorf("payload is not valid JSON")
	}
	baseURL := strings.TrimRight(strings.TrimSpace(pdsURL), "/")
	if baseURL == "" {
		return "", fmt.Errorf("pds url is empty")
	}

	if strings.HasPrefix(nsidName, "ai.gftd.murakumo.") {
		meta, ok, err := lookupNSIDMeta(repoRoot, nsidName)
		if err != nil {
			return "", err
		}
		if !ok {
			return "", fmt.Errorf("nsid not found in registry: %s", nsidName)
		}
		service := "MurakumoCommandService"
		if strings.EqualFold(meta.Category, "query") {
			service = "MurakumoQueryService"
		}
		url := fmt.Sprintf("%s/xrpc/gftd.murakumo.v1.%s/%s", baseURL, service, meta.Method)
		respBody, svcErr := postXrpcJSON(url, body, token, true)
		if svcErr == nil {
			return respBody, nil
		}
		legacyURL := baseURL + "/xrpc/" + nsidName
		legacyBody, legacyErr := postXrpcJSON(legacyURL, body, token, false)
		if legacyErr == nil {
			return legacyBody, nil
		}
		return "", fmt.Errorf("murakumo xrpc failed: service route error: %v; legacy route error: %v", svcErr, legacyErr)
	}

	url := baseURL + "/xrpc/" + nsidName
	return postXrpcJSON(url, body, token, false)
}

func waitMurakumoTaskResult(repoRoot, pdsURL, token, taskID string, timeout, interval time.Duration) (string, error) {
	deadline := time.Now().Add(timeout)
	attempt := 0
	nextSleep := interval
	payload := fmt.Sprintf(`{"taskId":%q}`, taskID)
	for {
		attempt++
		respBody, err := callMurakumoNSID(repoRoot, pdsURL, token, "gftd.murakumo.v1.MurakumoQueryService/GetTaskResult", payload)
		if err == nil {
			return respBody, nil
		}

		errMsg := err.Error()
		if strings.Contains(errMsg, "HTTP 404") {
			if time.Now().After(deadline) {
				return "", fmt.Errorf("murakumo task result timeout after %s (still not found)", timeout.String())
			}
			time.Sleep(nextSleep)
			continue
		}
		if strings.Contains(errMsg, "HTTP 429") {
			if time.Now().After(deadline) {
				return "", fmt.Errorf("murakumo task result timeout after %s (rate limited)", timeout.String())
			}
			if attempt%3 == 0 {
				fmt.Fprintf(os.Stderr, "==> wait murakumo task: rate limited (attempt=%d), backing off %s\n", attempt, nextSleep.String())
			}
			time.Sleep(nextSleep)
			nextSleep *= 2
			if nextSleep > 45*time.Second {
				nextSleep = 45 * time.Second
			}
			continue
		}
		return "", fmt.Errorf("murakumo task result failed: %w", err)
	}
}

func resolveKaizenWorkspaceDir(dir string) (string, error) {
	if strings.TrimSpace(dir) != "" {
		return filepath.Abs(dir)
	}
	cwd, err := os.Getwd()
	if err != nil {
		return "", err
	}
	root, err := findGitRoot(cwd)
	if err != nil {
		return "", fmt.Errorf("detect workspace root: %w", err)
	}
	return filepath.Abs(root)
}

func aggregateFromEvents(events []ocelEvent) map[string]ocelAgg {
	out := map[string]ocelAgg{}
	for _, e := range events {
		a := out[e.Method]
		a.Count++
		if e.Status >= 400 {
			a.Errors++
		}
		a.TotalMs += float64(e.Ms)
		if float64(e.Ms) > a.MaxMs {
			a.MaxMs = float64(e.Ms)
		}
		a.P99Samples = append(a.P99Samples, e.Ms)
		out[e.Method] = a
	}
	return out
}

func classifySeverity(p99, errRate float64) string {
	switch {
	case errRate >= 10 || p99 >= 2000:
		return "critical"
	case errRate >= 5 || p99 >= 1000:
		return "high"
	case errRate >= 1 || p99 >= 500:
		return "medium"
	default:
		return "low"
	}
}

func round2f(v float64) float64 {
	return math.Round(v*100) / 100
}
