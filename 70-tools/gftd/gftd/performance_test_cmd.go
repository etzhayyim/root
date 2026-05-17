package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"math"
	"net/http"
	"os"
	"sort"
	"strings"
	"sync"
	"time"
)

// ── Performance Test Command ──

func runPerformanceTest(args []string) error {
	if len(args) > 0 && (args[0] == "help" || args[0] == "--help" || args[0] == "-h") {
		printPerformanceTestUsage()
		return nil
	}
	if len(args) > 0 {
		switch args[0] {
		case "run":
			return runPerfTestRun(args[1:])
		case "report":
			return runPerfTestReport(args[1:])
		case "help", "--help", "-h":
			printPerformanceTestUsage()
			return nil
		default:
			return runPerfTestRun(args)
		}
	}
	return runPerfTestRun(args)
}

func printPerformanceTestUsage() {
	fmt.Print(`gftd performance-test — PDS XRPC endpoint performance measurement

USAGE:
  gftd performance-test [run] [flags]
  gftd performance-test report [flags]

COMMANDS:
  run       Execute performance tests against PDS (default)
  report    Load and display a saved JSON report

FLAGS:
  --target          PDS base URL (default: https://mod.etzhayyim.com)
  --concurrency     Concurrent requests per endpoint (default: 5)
  --duration        Test duration per endpoint in seconds (default: 10)
  --endpoints       Comma-separated endpoint filter (default: all)
  --json            Output as JSON
  --save            Save report to file (e.g. --save perf-report.json)
  --warm-up         Warm-up requests before measurement (default: 2)
  --timeout         Per-request timeout in seconds (default: 30)

ENDPOINTS:
  Timeline, DiscoverFeed, AuthorFeed, PostThread, SearchActors,
  SearchPosts, GetProfile, GetFollowers, GetFollows, GetSuggestions,
  ListNotifications, GetUnreadCount, SubscribeRepos, ListRecords,
  GetMessages, Health
`)
}

// ── Endpoint Definitions ──

type perfEndpoint struct {
	Name     string            `json:"name"`
	NSID     string            `json:"nsid"`
	Method   string            `json:"method"`
	Path     string            `json:"path"`
	Params   map[string]string `json:"params,omitempty"`
	Category string            `json:"category"`
}

var perfEndpoints = []perfEndpoint{
	// Feed
	{Name: "GetTimeline", NSID: "app.bsky.feed.getTimeline", Method: "GET", Path: "/xrpc/app.bsky.feed.getTimeline", Params: map[string]string{"limit": "25"}, Category: "feed"},
	{Name: "GetDiscoverFeed", NSID: "app.bsky.feed.getTimeline", Method: "GET", Path: "/xrpc/app.bsky.feed.getTimeline", Params: map[string]string{"limit": "25", "algorithm": "discover"}, Category: "feed"},
	{Name: "GetAuthorFeed", NSID: "app.bsky.feed.getAuthorFeed", Method: "GET", Path: "/xrpc/app.bsky.feed.getAuthorFeed", Params: map[string]string{"actor": "hoge.etzhayyim.com", "limit": "25"}, Category: "feed"},
	{Name: "GetPostThread", NSID: "app.bsky.feed.getPostThread", Method: "GET", Path: "/xrpc/app.bsky.feed.getPostThread", Params: map[string]string{"uri": "at://did:web:hoge.etzhayyim.com/app.bsky.feed.post/test"}, Category: "feed"},
	{Name: "SearchPosts", NSID: "app.bsky.feed.searchPosts", Method: "GET", Path: "/xrpc/app.bsky.feed.searchPosts", Params: map[string]string{"q": "test", "limit": "25"}, Category: "feed"},
	// Profile
	{Name: "GetProfile", NSID: "app.bsky.actor.getProfile", Method: "GET", Path: "/xrpc/app.bsky.actor.getProfile", Params: map[string]string{"actor": "hoge.etzhayyim.com"}, Category: "profile"},
	{Name: "SearchActors", NSID: "app.bsky.actor.searchActors", Method: "GET", Path: "/xrpc/app.bsky.actor.searchActors", Params: map[string]string{"q": "test", "limit": "10"}, Category: "profile"},
	{Name: "GetSuggestions", NSID: "app.bsky.actor.getSuggestions", Method: "GET", Path: "/xrpc/app.bsky.actor.getSuggestions", Params: map[string]string{"limit": "10"}, Category: "profile"},
	// Social
	{Name: "GetFollowers", NSID: "app.bsky.graph.getFollowers", Method: "GET", Path: "/xrpc/app.bsky.graph.getFollowers", Params: map[string]string{"actor": "hoge.etzhayyim.com", "limit": "25"}, Category: "social"},
	{Name: "GetFollows", NSID: "app.bsky.graph.getFollows", Method: "GET", Path: "/xrpc/app.bsky.graph.getFollows", Params: map[string]string{"actor": "hoge.etzhayyim.com", "limit": "25"}, Category: "social"},
	// Notification
	{Name: "ListNotifications", NSID: "app.bsky.notification.listNotifications", Method: "GET", Path: "/xrpc/app.bsky.notification.listNotifications", Params: map[string]string{"limit": "25"}, Category: "notification"},
	{Name: "GetUnreadCount", NSID: "app.bsky.notification.getUnreadCount", Method: "GET", Path: "/xrpc/app.bsky.notification.getUnreadCount", Category: "notification"},
	// Repo
	{Name: "ListRecords", NSID: "com.atproto.repo.listRecords", Method: "GET", Path: "/xrpc/com.atproto.repo.listRecords", Params: map[string]string{"repo": "did:web:hoge.etzhayyim.com", "collection": "app.bsky.feed.post", "limit": "25"}, Category: "repo"},
	// Infra
	{Name: "Health", NSID: "health", Method: "GET", Path: "/health", Category: "infra"},
}

// ── Measurement ──

type perfSample struct {
	Latency    time.Duration `json:"-"`
	LatencyMs  float64       `json:"latency_ms"`
	StatusCode int           `json:"status_code"`
	Error      string        `json:"error,omitempty"`
}

type perfResult struct {
	Endpoint    string  `json:"endpoint"`
	NSID        string  `json:"nsid"`
	Category    string  `json:"category"`
	Requests    int     `json:"requests"`
	Successes   int     `json:"successes"`
	Failures    int     `json:"failures"`
	P50Ms       float64 `json:"p50_ms"`
	P95Ms       float64 `json:"p95_ms"`
	P99Ms       float64 `json:"p99_ms"`
	MinMs       float64 `json:"min_ms"`
	MaxMs       float64 `json:"max_ms"`
	MeanMs      float64 `json:"mean_ms"`
	StddevMs    float64 `json:"stddev_ms"`
	RPSMeasured float64 `json:"rps_measured"`
	ErrorRate   float64 `json:"error_rate"`
	Grade       string  `json:"grade"`
}

type perfReport struct {
	Target      string       `json:"target"`
	TestedAt    string       `json:"tested_at"`
	Concurrency int          `json:"concurrency"`
	DurationS   int          `json:"duration_s"`
	Results     []perfResult `json:"results"`
	Summary     perfSummary  `json:"summary"`
}

type perfSummary struct {
	TotalEndpoints int     `json:"total_endpoints"`
	HealthyCount   int     `json:"healthy_count"`
	SlowCount      int     `json:"slow_count"`
	FailedCount    int     `json:"failed_count"`
	OverallGrade   string  `json:"overall_grade"`
	OverallP50Ms   float64 `json:"overall_p50_ms"`
}

func runPerfTestRun(args []string) error {
	fs := flag.NewFlagSet("performance-test run", flag.ContinueOnError)
	target := fs.String("target", defaultPDSURL, "PDS base URL")
	concurrency := fs.Int("concurrency", 5, "concurrent requests per endpoint")
	duration := fs.Int("duration", 10, "test duration per endpoint (seconds)")
	endpoints := fs.String("endpoints", "", "comma-separated endpoint filter")
	jsonOut := fs.Bool("json", false, "output as JSON")
	savePath := fs.String("save", "", "save report to file")
	warmUp := fs.Int("warm-up", 2, "warm-up requests before measurement")
	timeout := fs.Int("timeout", 30, "per-request timeout (seconds)")

	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	token := resolveGFTDToken()
	client := &http.Client{Timeout: time.Duration(*timeout) * time.Second}

	// Filter endpoints
	selected := perfEndpoints
	if *endpoints != "" {
		filterSet := make(map[string]bool)
		for _, e := range strings.Split(*endpoints, ",") {
			filterSet[strings.TrimSpace(e)] = true
		}
		var filtered []perfEndpoint
		for _, ep := range perfEndpoints {
			if filterSet[ep.Name] || filterSet[ep.Category] {
				filtered = append(filtered, ep)
			}
		}
		selected = filtered
	}

	if !*jsonOut {
		fmt.Printf("performance-test: target=%s concurrency=%d duration=%ds endpoints=%d\n\n", *target, *concurrency, *duration, len(selected))
	}

	var results []perfResult
	for i, ep := range selected {
		if !*jsonOut {
			fmt.Printf("[%d/%d] %s (%s) ... ", i+1, len(selected), ep.Name, ep.NSID)
		}

		// Build URL
		url := *target + ep.Path
		if len(ep.Params) > 0 {
			parts := make([]string, 0, len(ep.Params))
			for k, v := range ep.Params {
				parts = append(parts, k+"="+v)
			}
			url += "?" + strings.Join(parts, "&")
		}

		// Warm-up
		for w := 0; w < *warmUp; w++ {
			doRequest(client, ep.Method, url, token)
		}

		// Measure
		samples := measureEndpoint(client, ep.Method, url, token, *concurrency, time.Duration(*duration)*time.Second)
		result := computeResult(ep, samples)
		results = append(results, result)

		if !*jsonOut {
			fmt.Printf("p50=%.1fms p95=%.1fms p99=%.1fms rps=%.1f grade=%s\n",
				result.P50Ms, result.P95Ms, result.P99Ms, result.RPSMeasured, result.Grade)
		}
	}

	// Summary
	summary := computeSummary(results)
	report := perfReport{
		Target:      *target,
		TestedAt:    time.Now().UTC().Format(time.RFC3339),
		Concurrency: *concurrency,
		DurationS:   *duration,
		Results:     results,
		Summary:     summary,
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
	fmt.Printf("\n── Summary ──\n")
	fmt.Printf("  overall_grade: %s\n", summary.OverallGrade)
	fmt.Printf("  overall_p50:   %.1fms\n", summary.OverallP50Ms)
	fmt.Printf("  healthy:       %d/%d\n", summary.HealthyCount, summary.TotalEndpoints)
	fmt.Printf("  slow (>500ms): %d\n", summary.SlowCount)
	fmt.Printf("  failed:        %d\n", summary.FailedCount)

	// Slow endpoints
	var slow []perfResult
	for _, r := range results {
		if r.P50Ms > 500 {
			slow = append(slow, r)
		}
	}
	if len(slow) > 0 {
		fmt.Printf("\n── Slow Endpoints (p50 > 500ms) ──\n")
		for _, r := range slow {
			fmt.Printf("  %-25s p50=%7.1fms p95=%7.1fms grade=%s\n", r.Endpoint, r.P50Ms, r.P95Ms, r.Grade)
		}
	}

	return nil
}

func runPerfTestReport(args []string) error {
	fs := flag.NewFlagSet("performance-test report", flag.ContinueOnError)
	filePath := fs.String("file", "", "report JSON file to load")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}
	if *filePath == "" && fs.NArg() > 0 {
		*filePath = fs.Arg(0)
	}
	if *filePath == "" {
		return fmt.Errorf("usage: gftd performance-test report <file.json>")
	}
	data, err := os.ReadFile(*filePath)
	if err != nil {
		return fmt.Errorf("read: %w", err)
	}
	var report perfReport
	if err := json.Unmarshal(data, &report); err != nil {
		return fmt.Errorf("parse: %w", err)
	}

	fmt.Printf("Performance Report: %s (%s)\n", report.Target, report.TestedAt)
	fmt.Printf("  concurrency=%d duration=%ds\n\n", report.Concurrency, report.DurationS)

	fmt.Printf("%-25s %8s %8s %8s %8s %6s %6s\n", "ENDPOINT", "P50", "P95", "P99", "MEAN", "RPS", "GRADE")
	fmt.Printf("%s\n", strings.Repeat("─", 80))
	for _, r := range report.Results {
		fmt.Printf("%-25s %7.1fms %7.1fms %7.1fms %7.1fms %6.1f %6s\n",
			r.Endpoint, r.P50Ms, r.P95Ms, r.P99Ms, r.MeanMs, r.RPSMeasured, r.Grade)
	}
	fmt.Printf("\nOverall: %s (p50=%.1fms, healthy=%d/%d)\n",
		report.Summary.OverallGrade, report.Summary.OverallP50Ms,
		report.Summary.HealthyCount, report.Summary.TotalEndpoints)
	return nil
}

// ── HTTP + Measurement Helpers ──

func doRequest(client *http.Client, method, url, token string) perfSample {
	start := time.Now()
	req, err := http.NewRequest(method, url, nil)
	if err != nil {
		return perfSample{Error: err.Error(), LatencyMs: -1}
	}
	if token != "" {
		req.Header.Set("Authorization", "Bearer "+token)
	}
	req.Header.Set("Accept", "application/json")

	resp, err := client.Do(req)
	elapsed := time.Since(start)
	if err != nil {
		return perfSample{Latency: elapsed, LatencyMs: float64(elapsed.Microseconds()) / 1000.0, Error: err.Error()}
	}
	resp.Body.Close()
	return perfSample{
		Latency:    elapsed,
		LatencyMs:  float64(elapsed.Microseconds()) / 1000.0,
		StatusCode: resp.StatusCode,
	}
}

func measureEndpoint(client *http.Client, method, url, token string, concurrency int, duration time.Duration) []perfSample {
	var mu sync.Mutex
	var samples []perfSample

	deadline := time.Now().Add(duration)
	var wg sync.WaitGroup
	for c := 0; c < concurrency; c++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for time.Now().Before(deadline) {
				s := doRequest(client, method, url, token)
				mu.Lock()
				samples = append(samples, s)
				mu.Unlock()
			}
		}()
	}
	wg.Wait()
	return samples
}

func computeResult(ep perfEndpoint, samples []perfSample) perfResult {
	r := perfResult{
		Endpoint: ep.Name,
		NSID:     ep.NSID,
		Category: ep.Category,
		Requests: len(samples),
	}

	var latencies []float64
	for _, s := range samples {
		if s.Error != "" || s.StatusCode >= 500 {
			r.Failures++
		} else {
			r.Successes++
		}
		if s.LatencyMs > 0 {
			latencies = append(latencies, s.LatencyMs)
		}
	}

	if len(latencies) == 0 {
		r.Grade = "F"
		r.ErrorRate = 1.0
		return r
	}

	sort.Float64s(latencies)
	r.MinMs = latencies[0]
	r.MaxMs = latencies[len(latencies)-1]
	r.P50Ms = percentile(latencies, 0.50)
	r.P95Ms = percentile(latencies, 0.95)
	r.P99Ms = percentile(latencies, 0.99)

	var sum float64
	for _, l := range latencies {
		sum += l
	}
	r.MeanMs = sum / float64(len(latencies))

	var sqDiffSum float64
	for _, l := range latencies {
		diff := l - r.MeanMs
		sqDiffSum += diff * diff
	}
	r.StddevMs = math.Sqrt(sqDiffSum / float64(len(latencies)))

	if r.Requests > 0 {
		r.ErrorRate = float64(r.Failures) / float64(r.Requests)
	}

	// RPS from total samples / elapsed (approximate)
	if len(latencies) > 1 {
		totalMs := r.MeanMs * float64(len(latencies))
		r.RPSMeasured = float64(len(latencies)) / (totalMs / 1000.0)
	}

	r.Grade = gradeLatency(r.P50Ms, r.ErrorRate)
	return r
}

func percentile(sorted []float64, p float64) float64 {
	if len(sorted) == 0 {
		return 0
	}
	idx := int(float64(len(sorted)-1) * p)
	if idx >= len(sorted) {
		idx = len(sorted) - 1
	}
	return sorted[idx]
}

func gradeLatency(p50Ms, errorRate float64) string {
	if errorRate > 0.1 {
		return "F"
	}
	switch {
	case p50Ms < 20:
		return "S"
	case p50Ms < 50:
		return "A"
	case p50Ms < 200:
		return "B"
	case p50Ms < 500:
		return "C"
	case p50Ms < 2000:
		return "D"
	default:
		return "F"
	}
}

func computeSummary(results []perfResult) perfSummary {
	s := perfSummary{TotalEndpoints: len(results)}
	var allP50 []float64
	for _, r := range results {
		allP50 = append(allP50, r.P50Ms)
		switch {
		case r.Grade == "F":
			s.FailedCount++
		case r.P50Ms > 500:
			s.SlowCount++
		default:
			s.HealthyCount++
		}
	}
	if len(allP50) > 0 {
		sort.Float64s(allP50)
		s.OverallP50Ms = percentile(allP50, 0.50)
	}

	// Overall grade from median p50
	healthy := float64(s.HealthyCount) / float64(s.TotalEndpoints)
	switch {
	case healthy >= 0.95 && s.OverallP50Ms < 20:
		s.OverallGrade = "S"
	case healthy >= 0.9 && s.OverallP50Ms < 100:
		s.OverallGrade = "A"
	case healthy >= 0.7 && s.OverallP50Ms < 300:
		s.OverallGrade = "B"
	case healthy >= 0.5:
		s.OverallGrade = "C"
	case healthy >= 0.3:
		s.OverallGrade = "D"
	default:
		s.OverallGrade = "F"
	}
	return s
}
