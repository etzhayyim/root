package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net/http"
	"os"
	"sort"
	"strings"
	"sync"
	"time"
)

// ── PDS QA Command ──

func runPDSQA(args []string) error {
	if len(args) > 0 {
		switch args[0] {
		case "help", "--help", "-h":
			printPDSQAUsage()
			return nil
		}
	}
	return runPDSQARun(args)
}

func printPDSQAUsage() {
	fmt.Print(`gftd pds qa — PDS API stability evaluation (health, cache, circuit breaker, yata)

USAGE:
  gftd pds qa [flags]

FLAGS:
  --target       PDS base URL (default: https://mod.etzhayyim.com)
  --rounds       Number of measurement rounds per probe (default: 5)
  --json         Output as JSON
  --save         Save report to file

PROBES:
  health          /health — PDS + yata connectivity + circuit breaker state
  cache-hit       Timeline query repeated — measures latency variance (low variance = cache effective)
  cold-query      Discover feed query — measures yata read path latency
  concurrent      6 parallel feed queries — simulates real feed load (enrichment)
  timeline        Authenticated timeline with follow-based filtering
  author-feed     Per-actor feed query
  search          Full-text post search
  profile         Actor profile resolution
  error-rate      30 requests x3 parallel — sustained load error rate
`)
}

// ── QA Probe Definitions ──

type qaProbe struct {
	Name     string `json:"name"`
	Category string `json:"category"`
}

var qaProbes = []qaProbe{
	{Name: "health", Category: "infra"},
	{Name: "cache-hit", Category: "cache"},
	{Name: "cold-query", Category: "yata"},
	{Name: "concurrent", Category: "yata"},
	{Name: "timeline", Category: "feed"},
	{Name: "author-feed", Category: "feed"},
	{Name: "search", Category: "feed"},
	{Name: "profile", Category: "profile"},
	{Name: "error-rate", Category: "stability"},
}

// ── QA Result ──

type qaResult struct {
	Probe      string  `json:"probe"`
	Category   string  `json:"category"`
	Status     string  `json:"status"` // pass / warn / fail
	LatencyMs  float64 `json:"latency_ms"`
	Detail     string  `json:"detail,omitempty"`
	Grade      string  `json:"grade"`
	Samples    int     `json:"samples,omitempty"`
	ErrorCount int     `json:"error_count,omitempty"`
	P50Ms      float64 `json:"p50_ms,omitempty"`
	P95Ms      float64 `json:"p95_ms,omitempty"`
}

type qaReport struct {
	Target   string     `json:"target"`
	TestedAt string     `json:"tested_at"`
	Rounds   int        `json:"rounds"`
	Results  []qaResult `json:"results"`
	Summary  qaSummary  `json:"summary"`
}

type qaSummary struct {
	TotalProbes  int    `json:"total_probes"`
	PassCount    int    `json:"pass_count"`
	WarnCount    int    `json:"warn_count"`
	FailCount    int    `json:"fail_count"`
	OverallGrade string `json:"overall_grade"`
	Verdict      string `json:"verdict"`
}

// ── Runner ──

func runPDSQARun(args []string) error {
	fs := flag.NewFlagSet("pds qa", flag.ContinueOnError)
	target := fs.String("target", defaultPDSURL, "PDS base URL")
	rounds := fs.Int("rounds", 5, "measurement rounds per probe")
	jsonOut := fs.Bool("json", false, "output as JSON")
	savePath := fs.String("save", "", "save report to file")

	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	token := resolveGFTDToken()
	client := &http.Client{Timeout: 15 * time.Second}
	base := strings.TrimRight(*target, "/")

	if !*jsonOut {
		fmt.Printf("pds qa: target=%s rounds=%d\n\n", base, *rounds)
	}

	var results []qaResult
	for i, probe := range qaProbes {
		if !*jsonOut {
			fmt.Printf("[%d/%d] %-15s ... ", i+1, len(qaProbes), probe.Name)
		}

		var r qaResult
		switch probe.Name {
		case "health":
			r = probeHealth(client, base)
		case "cache-hit":
			r = probeCacheHit(client, base, token, *rounds)
		case "cold-query":
			r = probeColdQuery(client, base, token, *rounds)
		case "concurrent":
			r = probeConcurrent(client, base, token)
		case "timeline":
			r = probeEndpoint(client, base, token, *rounds, "timeline",
				"/xrpc/app.bsky.feed.getTimeline?limit=25", "feed")
		case "author-feed":
			r = probeEndpoint(client, base, token, *rounds, "author-feed",
				"/xrpc/app.bsky.feed.getAuthorFeed?actor=hoge.etzhayyim.com&limit=25", "feed")
		case "search":
			r = probeEndpoint(client, base, token, *rounds, "search",
				"/xrpc/app.bsky.feed.searchPosts?q=test&limit=10", "feed")
		case "profile":
			r = probeEndpoint(client, base, token, *rounds, "profile",
				"/xrpc/app.bsky.actor.getProfile?actor=hoge.etzhayyim.com", "profile")
		case "error-rate":
			r = probeErrorRate(client, base, token)
		}
		r.Probe = probe.Name
		r.Category = probe.Category
		results = append(results, r)

		if !*jsonOut {
			fmt.Printf("%-5s %7.1fms grade=%s %s\n", r.Status, r.LatencyMs, r.Grade, r.Detail)
		}
	}

	summary := computeQASummary(results)
	report := qaReport{
		Target:   base,
		TestedAt: time.Now().UTC().Format(time.RFC3339),
		Rounds:   *rounds,
		Results:  results,
		Summary:  summary,
	}

	if *savePath != "" {
		f, err := os.Create(*savePath)
		if err != nil {
			return fmt.Errorf("save: %w", err)
		}
		defer f.Close()
		enc := json.NewEncoder(f)
		enc.SetIndent("", "  ")
		if err := enc.Encode(report); err != nil {
			return fmt.Errorf("save: %w", err)
		}
		if !*jsonOut {
			fmt.Printf("\nReport saved to %s\n", *savePath)
		}
	}

	if *jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(report)
	}

	// Text summary
	fmt.Printf("\n── PDS QA Summary ──\n")
	fmt.Printf("  grade:   %s\n", summary.OverallGrade)
	fmt.Printf("  verdict: %s\n", summary.Verdict)
	fmt.Printf("  pass:    %d/%d\n", summary.PassCount, summary.TotalProbes)
	if summary.WarnCount > 0 {
		fmt.Printf("  warn:    %d\n", summary.WarnCount)
	}
	if summary.FailCount > 0 {
		fmt.Printf("  fail:    %d\n", summary.FailCount)
	}

	return nil
}

// ── Probe: Health ──

type healthResponse struct {
	Status  string `json:"status"`
	Yata    string `json:"yata"`
	Circuit string `json:"circuit"`
}

func probeHealth(client *http.Client, base string) qaResult {
	start := time.Now()
	resp, err := client.Get(base + "/health")
	elapsed := float64(time.Since(start).Microseconds()) / 1000.0
	if err != nil {
		return qaResult{Status: "fail", LatencyMs: elapsed, Detail: err.Error(), Grade: "F"}
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body)

	var h healthResponse
	json.Unmarshal(body, &h)

	if resp.StatusCode >= 500 || h.Status == "" {
		return qaResult{Status: "fail", LatencyMs: elapsed, Detail: fmt.Sprintf("HTTP %d", resp.StatusCode), Grade: "F"}
	}

	detail := fmt.Sprintf("yata=%s circuit=%s", h.Yata, h.Circuit)
	if h.Yata != "ok" {
		return qaResult{Status: "fail", LatencyMs: elapsed, Detail: detail, Grade: "F"}
	}
	if h.Circuit == "open" {
		return qaResult{Status: "warn", LatencyMs: elapsed, Detail: detail, Grade: "C"}
	}
	if resp.StatusCode == 503 {
		return qaResult{Status: "warn", LatencyMs: elapsed, Detail: fmt.Sprintf("HTTP 503 degraded — %s", detail), Grade: "D"}
	}
	return qaResult{Status: "pass", LatencyMs: elapsed, Detail: detail, Grade: gradeQALatency(elapsed)}
}

// ── Probe: Cache Hit ──

func probeCacheHit(client *http.Client, base, token string, rounds int) qaResult {
	url := base + "/xrpc/app.bsky.feed.getTimeline?limit=10"

	// Warm up (populate cache in whichever isolate we hit)
	doQARequest(client, url, token)
	time.Sleep(100 * time.Millisecond)

	// Measure repeated requests — low variance + low latency = cache/stability effective
	var latencies []float64
	for i := 0; i < rounds+2; i++ {
		s := doQARequest(client, url, token)
		latencies = append(latencies, s.latencyMs)
	}

	sort.Float64s(latencies)
	p50 := qaPercentile(latencies, 0.50)
	p95 := qaPercentile(latencies, 0.95)
	minMs := latencies[0]
	maxMs := latencies[len(latencies)-1]
	variance := maxMs - minMs

	// Grade by p50 latency (consistent fast response = stable)
	grade := gradeQALatency(p50)
	status := "pass"
	if p50 > 2000 {
		status = "warn"
	}
	if variance > p50*2 && variance > 1000 {
		status = "warn"
	}

	detail := fmt.Sprintf("p50=%.1fms p95=%.1fms min=%.1fms max=%.1fms variance=%.1fms", p50, p95, minMs, maxMs, variance)

	return qaResult{
		Status: status, LatencyMs: p50, Detail: detail, Grade: grade,
		Samples: len(latencies), P50Ms: p50, P95Ms: p95,
	}
}

// ── Probe: Cold Query ──

func probeColdQuery(client *http.Client, base, token string, rounds int) qaResult {
	url := base + "/xrpc/app.bsky.feed.getTimeline?limit=25&algorithm=discover"
	var latencies []float64
	var errors int

	for i := 0; i < rounds; i++ {
		s := doQARequest(client, url, token)
		if s.err != "" || s.statusCode >= 500 {
			errors++
		}
		latencies = append(latencies, s.latencyMs)
	}

	sort.Float64s(latencies)
	p50 := qaPercentile(latencies, 0.50)
	p95 := qaPercentile(latencies, 0.95)

	status := "pass"
	if errors > 0 {
		status = "fail"
	} else if p50 > 500 {
		status = "warn"
	}

	return qaResult{
		Status: status, LatencyMs: p50, Grade: gradeQALatency(p50),
		Detail:  fmt.Sprintf("p50=%.1fms p95=%.1fms errors=%d/%d", p50, p95, errors, rounds),
		Samples: rounds, P50Ms: p50, P95Ms: p95, ErrorCount: errors,
	}
}

// ── Probe: Concurrent (6 parallel queries like real feed enrichment) ──

func probeConcurrent(client *http.Client, base, token string) qaResult {
	urls := []string{
		base + "/xrpc/app.bsky.feed.getTimeline?limit=25",
		base + "/xrpc/app.bsky.actor.getProfile?actor=hoge.etzhayyim.com",
		base + "/xrpc/app.bsky.actor.searchActors?q=test&limit=5",
		base + "/xrpc/app.bsky.feed.searchPosts?q=test&limit=5",
		base + "/xrpc/app.bsky.actor.getSuggestions?limit=5",
		base + "/health",
	}

	start := time.Now()
	var mu sync.Mutex
	var wg sync.WaitGroup
	var maxMs float64
	var errors int

	for _, u := range urls {
		wg.Add(1)
		go func(url string) {
			defer wg.Done()
			s := doQARequest(client, url, token)
			mu.Lock()
			if s.latencyMs > maxMs {
				maxMs = s.latencyMs
			}
			if s.err != "" || s.statusCode >= 500 {
				errors++
			}
			mu.Unlock()
		}(u)
	}
	wg.Wait()
	totalMs := float64(time.Since(start).Microseconds()) / 1000.0

	status := "pass"
	if errors > 0 {
		status = "fail"
	} else if totalMs > 1000 {
		status = "warn"
	}

	return qaResult{
		Status: status, LatencyMs: totalMs, Grade: gradeQALatency(totalMs),
		Detail:  fmt.Sprintf("wall=%.1fms max_single=%.1fms parallel=6 errors=%d", totalMs, maxMs, errors),
		Samples: len(urls), ErrorCount: errors,
	}
}

// ── Probe: Generic Endpoint ──

func probeEndpoint(client *http.Client, base, token string, rounds int, name, path, category string) qaResult {
	url := base + path
	var latencies []float64
	var errors int

	for i := 0; i < rounds; i++ {
		s := doQARequest(client, url, token)
		if s.err != "" || s.statusCode >= 500 {
			errors++
		}
		latencies = append(latencies, s.latencyMs)
	}

	sort.Float64s(latencies)
	p50 := qaPercentile(latencies, 0.50)
	p95 := qaPercentile(latencies, 0.95)

	status := "pass"
	if errors > 0 {
		status = "fail"
	} else if p50 > 500 {
		status = "warn"
	}

	return qaResult{
		Status: status, LatencyMs: p50, Grade: gradeQALatency(p50),
		Detail:  fmt.Sprintf("p50=%.1fms p95=%.1fms errors=%d/%d", p50, p95, errors, rounds),
		Samples: rounds, P50Ms: p50, P95Ms: p95, ErrorCount: errors,
	}
}

// ── Probe: Error Rate (sustained load) ──

func probeErrorRate(client *http.Client, base, token string) qaResult {
	url := base + "/xrpc/app.bsky.feed.getTimeline?limit=10"
	total := 30
	var errors int
	var latencies []float64

	var mu sync.Mutex
	var wg sync.WaitGroup
	for i := 0; i < 3; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for j := 0; j < total/3; j++ {
				s := doQARequest(client, url, token)
				mu.Lock()
				latencies = append(latencies, s.latencyMs)
				if s.err != "" || s.statusCode >= 500 {
					errors++
				}
				mu.Unlock()
			}
		}()
	}
	wg.Wait()

	sort.Float64s(latencies)
	p50 := qaPercentile(latencies, 0.50)
	errorRate := 0.0
	if total > 0 {
		errorRate = float64(errors) / float64(total) * 100
	}

	status := "pass"
	grade := "S"
	if errorRate > 10 {
		status = "fail"
		grade = "F"
	} else if errorRate > 1 {
		status = "warn"
		grade = "C"
	} else {
		grade = gradeQALatency(p50)
	}

	return qaResult{
		Status: status, LatencyMs: p50, Grade: grade,
		Detail:     fmt.Sprintf("error_rate=%.1f%% errors=%d/%d p50=%.1fms", errorRate, errors, total, p50),
		Samples:    total,
		ErrorCount: errors,
		P50Ms:      p50,
	}
}

// ── HTTP Helper ──

type qaHTTPResult struct {
	latencyMs  float64
	statusCode int
	err        string
	body       []byte
}

func doQARequest(client *http.Client, url, token string) qaHTTPResult {
	start := time.Now()
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return qaHTTPResult{err: err.Error(), latencyMs: -1}
	}
	if token != "" {
		req.Header.Set("Authorization", "Bearer "+token)
	}
	req.Header.Set("Accept", "application/json")

	resp, err := client.Do(req)
	elapsed := float64(time.Since(start).Microseconds()) / 1000.0
	if err != nil {
		return qaHTTPResult{latencyMs: elapsed, err: err.Error()}
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body)
	return qaHTTPResult{latencyMs: elapsed, statusCode: resp.StatusCode, body: body}
}

// ── Scoring ──

func gradeQALatency(ms float64) string {
	switch {
	case ms < 20:
		return "S"
	case ms < 50:
		return "A"
	case ms < 200:
		return "B"
	case ms < 500:
		return "C"
	case ms < 2000:
		return "D"
	default:
		return "F"
	}
}

func qaPercentile(sorted []float64, p float64) float64 {
	if len(sorted) == 0 {
		return 0
	}
	idx := int(float64(len(sorted)-1) * p)
	if idx >= len(sorted) {
		idx = len(sorted) - 1
	}
	return sorted[idx]
}

func computeQASummary(results []qaResult) qaSummary {
	s := qaSummary{TotalProbes: len(results)}

	gradeScore := map[string]int{"S": 6, "A": 5, "B": 4, "C": 3, "D": 2, "F": 1}
	totalScore := 0

	for _, r := range results {
		switch r.Status {
		case "pass":
			s.PassCount++
		case "warn":
			s.WarnCount++
		case "fail":
			s.FailCount++
		}
		totalScore += gradeScore[r.Grade]
	}

	avg := 0.0
	if len(results) > 0 {
		avg = float64(totalScore) / float64(len(results))
	}
	switch {
	case s.FailCount > 0 && avg < 2:
		s.OverallGrade = "F"
	case s.FailCount >= 3:
		s.OverallGrade = "F"
	case s.FailCount > 0:
		s.OverallGrade = "D"
	case avg >= 5.5:
		s.OverallGrade = "S"
	case avg >= 4.5:
		s.OverallGrade = "A"
	case avg >= 3.5:
		s.OverallGrade = "B"
	case avg >= 2.5:
		s.OverallGrade = "C"
	default:
		s.OverallGrade = "D"
	}

	switch s.OverallGrade {
	case "S":
		s.Verdict = "Excellent — yata responsive, low latency, no errors"
	case "A":
		s.Verdict = "Good — minor latency variance, stable"
	case "B":
		s.Verdict = "Acceptable — some slow queries, check yata cold start"
	case "C":
		s.Verdict = "Degraded — high latency, yata may be cold starting"
	case "D":
		s.Verdict = "Poor — yata slow or warming up, high latency across probes"
	case "F":
		s.Verdict = "Critical — PDS or yata unreachable, errors detected"
	}

	return s
}
