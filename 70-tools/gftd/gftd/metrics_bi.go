// metrics_bi — Business Intelligence metrics collection from CF Analytics, Stripe, and graph.
// Fetches access/revenue/platform data and writes MetricsBi vertices to kagami graph.
package main

import (
	"bytes"
	"context"
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

const cfAccountID = "4da88288dc30d9ee257f319d3c33ecf0"

// biMetrics holds all collected BI data for a single snapshot.
type biMetrics struct {
	Timestamp string `json:"timestamp"`

	// CF Analytics
	XrpcRequests1h  int            `json:"xrpcRequests1h"`
	XrpcErrors1h    int            `json:"xrpcErrors1h"`
	XrpcErrorRate   float64        `json:"xrpcErrorRate"`
	AccessRequests  int            `json:"accessRequests"`
	UniqueCountries int            `json:"uniqueCountries"`
	UniqueColos     int            `json:"uniqueColos"`
	TopMethods      []biMethodStat `json:"topMethods"`
	TopCountries    []biCountStat  `json:"topCountries"`
	TopColos        []biCountStat  `json:"topColos"`
	StatusBuckets   map[string]int `json:"statusBuckets"`

	// Graph platform
	TotalActors   int64 `json:"totalActors"`
	TotalDIDs     int64 `json:"totalDIDs"`
	TotalRecords  int64 `json:"totalRecords"`
	TotalProfiles int64 `json:"totalProfiles"`
	TotalApps     int64 `json:"totalApps"`
	TotalPosts    int64 `json:"totalPosts"`
	TotalEdges    int64 `json:"totalEdges"`

	// Stripe
	StripeBalance       int64  `json:"stripeBalance"`
	StripeCurrency      string `json:"stripeCurrency"`
	StripeCharges24h    int    `json:"stripeCharges24h"`
	StripeRevenue24h    int64  `json:"stripeRevenue24h"`
	StripeSubscriptions int    `json:"stripeSubscriptions"`
}

type biMethodStat struct {
	Method string  `json:"method"`
	Count  int     `json:"count"`
	Errors int     `json:"errors"`
	P50Ms  float64 `json:"p50Ms"`
	P99Ms  float64 `json:"p99Ms"`
}

type biCountStat struct {
	Name  string `json:"name"`
	Count int    `json:"count"`
}

func runMetrics(args []string) error {
	fs := flag.NewFlagSet("metrics", flag.ContinueOnError)
	subCmd := "bi"
	if len(args) > 0 && args[0] == "bi" {
		args = args[1:]
	}
	_ = subCmd

	pdsURL := fs.String("pds", defaultPDSURL, "PDS base URL")
	asJSON := fs.Bool("json", false, "emit JSON")
	dryRun := fs.Bool("dry-run", false, "collect only, do not write vertices")
	writeGraph := fs.Bool("write", defaultMetricsBiWriteEnabled(), "write MetricsBi vertex to graph")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	now := time.Now().UTC()
	metrics := biMetrics{
		Timestamp:     now.Format(time.RFC3339),
		StatusBuckets: map[string]int{},
	}

	// ── 1. CF Analytics Engine ──
	cfToken := resolveCFAnalyticsToken()
	if cfToken != "" {
		fmt.Fprintf(os.Stderr, "Fetching Cloudflare Analytics...\n")
		if err := fetchCFAnalytics(cfToken, &metrics); err != nil {
			fmt.Fprintf(os.Stderr, "WARN: CF Analytics: %v\n", err)
		}
	} else if hasWranglerOAuthToken() {
		fmt.Fprintf(os.Stderr, "WARN: Wrangler OAuth detected, but Analytics Engine SQL needs CF_API_TOKEN/CLOUDFLARE_API_TOKEN\n")
	} else {
		fmt.Fprintf(os.Stderr, "WARN: No CF token (set CF_API_TOKEN/CLOUDFLARE_API_TOKEN)\n")
	}

	// ── 2. Graph platform summary ──
	fmt.Fprintf(os.Stderr, "Fetching graph platform summary...\n")
	if err := fetchGraphSummary(&metrics); err != nil {
		fmt.Fprintf(os.Stderr, "WARN: Graph summary: %v\n", err)
	}

	// ── 3. Stripe ──
	stripeKey := os.Getenv("STRIPE_SECRET_KEY")
	if stripeKey != "" {
		fmt.Fprintf(os.Stderr, "Fetching Stripe data...\n")
		if err := fetchStripeMetrics(stripeKey, &metrics); err != nil {
			fmt.Fprintf(os.Stderr, "WARN: Stripe: %v\n", err)
		}
	} else {
		fmt.Fprintf(os.Stderr, "WARN: No STRIPE_SECRET_KEY set\n")
	}

	// ── 4. Write MetricsBi vertex to graph ──
	if *writeGraph && !*dryRun {
		fmt.Fprintf(os.Stderr, "Writing MetricsBi vertex to graph...\n")
		if err := writeMetricsBiVertex(*pdsURL, &metrics); err != nil {
			fmt.Fprintf(os.Stderr, "WARN: Write vertex: %v\n", err)
		}
	} else if !*dryRun && !*writeGraph {
		fmt.Fprintf(os.Stderr, "Skipping MetricsBi vertex write (no graph write credential detected; pass --write to force)\n")
	}

	// ── Output ──
	if *asJSON {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(metrics)
	}

	printBIReport(&metrics)
	return nil
}

func defaultMetricsBiWriteEnabled() bool {
	if strings.TrimSpace(resolveGFTDToken()) != "" {
		return true
	}
	if strings.TrimSpace(os.Getenv("DATABASE_URL")) != "" {
		return true
	}
	if strings.TrimSpace(os.Getenv("GFTD_DATABASE_URL")) != "" {
		return true
	}
	return false
}

// ── CF Analytics Engine queries ──

func fetchCFAnalytics(cfToken string, m *biMetrics) error {
	// XRPC aggregates (1h)
	aggSQL := `SELECT blob1 AS method, count() AS count, sum(double2>=400) AS errors,
		quantileWeighted(0.50)(double1,1) AS p50Ms, quantileWeighted(0.99)(double1,1) AS p99Ms
		FROM ocel_v2 WHERE blob2='xrpc'
		AND timestamp >= now() - INTERVAL '1' HOUR
		GROUP BY blob1 ORDER BY count DESC LIMIT 30`
	aggRows, err := aeQuerySQL(cfToken, cfAccountID, aggSQL)
	if err != nil {
		return fmt.Errorf("xrpc agg: %w", err)
	}
	totalReqs := 0
	totalErrs := 0
	for _, r := range aggRows {
		cnt := jsonInt(r["count"])
		errs := jsonInt(r["errors"])
		totalReqs += cnt
		totalErrs += errs
		m.TopMethods = append(m.TopMethods, biMethodStat{
			Method: fmt.Sprint(r["method"]),
			Count:  cnt,
			Errors: errs,
			P50Ms:  jsonFloat64(r["p50Ms"]),
			P99Ms:  jsonFloat64(r["p99Ms"]),
		})
	}
	m.XrpcRequests1h = totalReqs
	m.XrpcErrors1h = totalErrs
	if totalReqs > 0 {
		m.XrpcErrorRate = float64(totalErrs) / float64(totalReqs) * 100
	}

	// Access log stats (1h): country, colo, status buckets
	accessSQL := `SELECT blob6 AS country, blob5 AS colo, double2 AS status
		FROM ocel_v2 WHERE blob2='access'
		AND timestamp >= now() - INTERVAL '1' HOUR
		LIMIT 5000`
	accessRows, err := aeQuerySQL(cfToken, cfAccountID, accessSQL)
	if err != nil {
		return fmt.Errorf("access: %w", err)
	}
	m.AccessRequests = len(accessRows)
	countryCounts := map[string]int{}
	coloCounts := map[string]int{}
	for _, r := range accessRows {
		c := fmt.Sprint(r["country"])
		if c != "" && c != "<nil>" {
			countryCounts[c]++
		}
		co := fmt.Sprint(r["colo"])
		if co != "" && co != "<nil>" {
			coloCounts[co]++
		}
		status := jsonInt(r["status"])
		bucket := fmt.Sprintf("%dxx", status/100)
		m.StatusBuckets[bucket]++
	}
	m.UniqueCountries = len(countryCounts)
	m.UniqueColos = len(coloCounts)
	m.TopCountries = sortCountStats(countryCounts, 10)
	m.TopColos = sortCountStats(coloCounts, 10)

	return nil
}

func sortCountStats(m map[string]int, limit int) []biCountStat {
	var stats []biCountStat
	for k, v := range m {
		stats = append(stats, biCountStat{k, v})
	}
	sort.Slice(stats, func(i, j int) bool { return stats[i].Count > stats[j].Count })
	if len(stats) > limit {
		stats = stats[:limit]
	}
	return stats
}

// ── Graph platform summary ──

func fetchGraphSummary(m *biMetrics) error {
	ctx, cancel := context.WithTimeout(context.Background(), 60*time.Second)
	defer cancel()
	q, err := db.Q(ctx)
	if err != nil {
		return err
	}

	if n, err := q.CountActors(ctx); err == nil {
		m.TotalActors = n
	}
	if n, err := q.CountDids(ctx); err == nil {
		m.TotalDIDs = n
	}
	if n, err := q.CountPosts(ctx); err == nil {
		m.TotalPosts = n
	}
	if n, err := q.CountProfiles(ctx); err == nil {
		m.TotalProfiles = n
	}
	if n, err := q.CountApps(ctx); err == nil {
		m.TotalApps = n
	}

	m.TotalRecords = m.TotalActors + m.TotalDIDs + m.TotalPosts + m.TotalProfiles + m.TotalApps
	return nil
}

// ── Stripe API ──

func fetchStripeMetrics(apiKey string, m *biMetrics) error {
	client := &http.Client{Timeout: 15 * time.Second}

	// Balance
	balReq, _ := http.NewRequest("GET", "https://api.stripe.com/v1/balance", nil)
	balReq.SetBasicAuth(apiKey, "")
	balResp, err := client.Do(balReq)
	if err != nil {
		return fmt.Errorf("balance: %w", err)
	}
	defer balResp.Body.Close()
	balBody, _ := io.ReadAll(balResp.Body)
	if balResp.StatusCode == 200 {
		var bal struct {
			Available []struct {
				Amount   int64  `json:"amount"`
				Currency string `json:"currency"`
			} `json:"available"`
		}
		if json.Unmarshal(balBody, &bal) == nil && len(bal.Available) > 0 {
			m.StripeBalance = bal.Available[0].Amount
			m.StripeCurrency = bal.Available[0].Currency
		}
	}

	// Charges (last 24h)
	since := time.Now().Add(-24 * time.Hour).Unix()
	chargeURL := fmt.Sprintf("https://api.stripe.com/v1/charges?created[gte]=%d&limit=100", since)
	chargeReq, _ := http.NewRequest("GET", chargeURL, nil)
	chargeReq.SetBasicAuth(apiKey, "")
	chargeResp, err := client.Do(chargeReq)
	if err != nil {
		return fmt.Errorf("charges: %w", err)
	}
	defer chargeResp.Body.Close()
	chargeBody, _ := io.ReadAll(chargeResp.Body)
	if chargeResp.StatusCode == 200 {
		var charges struct {
			Data []struct {
				Amount int64 `json:"amount"`
				Paid   bool  `json:"paid"`
			} `json:"data"`
		}
		if json.Unmarshal(chargeBody, &charges) == nil {
			m.StripeCharges24h = len(charges.Data)
			for _, ch := range charges.Data {
				if ch.Paid {
					m.StripeRevenue24h += ch.Amount
				}
			}
		}
	}

	// Active subscriptions count
	subReq, _ := http.NewRequest("GET", "https://api.stripe.com/v1/subscriptions?status=active&limit=1", nil)
	subReq.SetBasicAuth(apiKey, "")
	subResp, err := client.Do(subReq)
	if err != nil {
		return fmt.Errorf("subscriptions: %w", err)
	}
	defer subResp.Body.Close()
	subBody, _ := io.ReadAll(subResp.Body)
	if subResp.StatusCode == 200 {
		var subs struct {
			Data    []any `json:"data"`
			HasMore bool  `json:"has_more"`
		}
		if json.Unmarshal(subBody, &subs) == nil {
			// Use total_count if available, otherwise count data
			var subCount struct {
				TotalCount int `json:"total_count"`
			}
			if json.Unmarshal(subBody, &subCount) == nil && subCount.TotalCount > 0 {
				m.StripeSubscriptions = subCount.TotalCount
			} else {
				m.StripeSubscriptions = len(subs.Data)
			}
		}
	}

	return nil
}

// ── Write MetricsBi vertex to graph via Sql MERGE ──

func writeMetricsBiVertex(pdsURL string, m *biMetrics) error {
	client := &http.Client{Timeout: 15 * time.Second}
	token := resolveGFTDToken()

	rkey := "bi-" + time.Now().UTC().Format("20060102-150405")
	vertexID := "metrics:bi:" + rkey

	payload, err := buildMetricsBiWritePayload(m, vertexID, rkey)
	if err != nil {
		return err
	}

	url := strings.TrimRight(pdsURL, "/") + "/xrpc/ai.gftd.kagami.sql"
	req, err := http.NewRequest("POST", url, bytes.NewReader(payload))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	if token != "" {
		req.Header.Set("Authorization", "Bearer "+token)
	}
	setAuthHeaders(req)

	resp, err := client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 400 {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("graph.query HTTP %d: %s", resp.StatusCode, truncStr(string(body), 200))
	}
	fmt.Fprintf(os.Stderr, "  Wrote MetricsBi vertex: %s\n", vertexID)
	return nil
}

func buildMetricsBiWritePayload(m *biMetrics, vertexID, rkey string) ([]byte, error) {
	valJSON, err := json.Marshal(m)
	if err != nil {
		return nil, err
	}
	return json.Marshal(map[string]any{
		"statement": `MERGE (n:MetricsBi {vertex_id: $vertex_id}) SET n.rkey = $rkey, n.repo = $repo, n.collection = $collection, n.owner_did = $owner_did, n.app_id = $app_id, n.visibility = $visibility, n.sensitivity_ord = $sensitivity_ord, n.val = $val`,
		"parameters": map[string]any{
			"vertex_id":       vertexID,
			"rkey":            rkey,
			"repo":            "did:web:mod.etzhayyim.com",
			"collection":      "ai.gftd.metrics.bi",
			"owner_did":       "did:web:mod.etzhayyim.com",
			"app_id":          "metrics",
			"visibility":      "internal",
			"sensitivity_ord": 0,
			"val":             string(valJSON),
		},
	})
}

// ── Terminal report ──

func printBIReport(m *biMetrics) {
	fmt.Println()
	fmt.Println("╔══════════════════════════════════════════════════════════════════════════════════╗")
	fmt.Println("║                    GFTD Business Intelligence                                   ║")
	fmt.Printf("║                    %s                                     ║\n", m.Timestamp[:19])
	fmt.Println("╠══════════════════════════════════════════════════════════════════════════════════╣")
	fmt.Println()

	// ── Traffic (CF Analytics) ──
	fmt.Println("  ── Traffic (rolling 1h) ─────────────────────────────────────────────")
	fmt.Printf("  XRPC Requests:    %d\n", m.XrpcRequests1h)
	fmt.Printf("  XRPC Errors:      %d (%.2f%%)\n", m.XrpcErrors1h, m.XrpcErrorRate)
	fmt.Printf("  Access Requests:  %d\n", m.AccessRequests)
	fmt.Printf("  Countries:        %d\n", m.UniqueCountries)
	fmt.Printf("  Edge PoPs:        %d\n", m.UniqueColos)
	fmt.Println()

	if len(m.StatusBuckets) > 0 {
		fmt.Print("  HTTP Status: ")
		keys := make([]string, 0, len(m.StatusBuckets))
		for k := range m.StatusBuckets {
			keys = append(keys, k)
		}
		sort.Strings(keys)
		for _, k := range keys {
			fmt.Printf("%s=%d  ", k, m.StatusBuckets[k])
		}
		fmt.Println()
		fmt.Println()
	}

	if len(m.TopCountries) > 0 {
		fmt.Print("  Top Geo: ")
		for i, c := range m.TopCountries {
			if i >= 8 {
				break
			}
			fmt.Printf("%s=%d  ", c.Name, c.Count)
		}
		fmt.Println()
	}
	if len(m.TopColos) > 0 {
		fmt.Print("  Top PoP: ")
		for i, c := range m.TopColos {
			if i >= 8 {
				break
			}
			fmt.Printf("%s=%d  ", c.Name, c.Count)
		}
		fmt.Println()
	}
	fmt.Println()

	// ── Top Methods ──
	if len(m.TopMethods) > 0 {
		fmt.Println("  ── Top XRPC Methods ─────────────────────────────────────────────")
		fmt.Println("  ┌─────────────────────────────────────────┬───────┬───────┬────────┬────────┐")
		fmt.Println("  │ Method                                  │ Count │ Errs  │ p50    │ p99    │")
		fmt.Println("  ├─────────────────────────────────────────┼───────┼───────┼────────┼────────┤")
		limit := 15
		if len(m.TopMethods) < limit {
			limit = len(m.TopMethods)
		}
		for _, s := range m.TopMethods[:limit] {
			method := s.Method
			if len(method) > 39 {
				method = method[:39]
			}
			fmt.Printf("  │ %-39s │ %5d │ %5d │ %4.0fms │ %4.0fms │\n",
				method, s.Count, s.Errors, s.P50Ms, s.P99Ms)
		}
		fmt.Println("  └─────────────────────────────────────────┴───────┴───────┴────────┴────────┘")
		fmt.Println()
	}

	// ── Platform (Graph) ──
	fmt.Println("  ── Platform (Graph) ─────────────────────────────────────────────")
	fmt.Printf("  Actors:           %d\n", m.TotalActors)
	fmt.Printf("  DIDs:             %d\n", m.TotalDIDs)
	fmt.Printf("  Profiles:         %d\n", m.TotalProfiles)
	fmt.Printf("  Apps:             %d\n", m.TotalApps)
	fmt.Printf("  Posts:            %d\n", m.TotalPosts)
	fmt.Printf("  Records (sum):    %d\n", m.TotalRecords)
	fmt.Println()

	// ── Revenue (Stripe) ──
	fmt.Println("  ── Revenue (Stripe) ─────────────────────────────────────────────")
	if m.StripeCurrency != "" {
		fmt.Printf("  Balance:          %s %s\n", formatCurrency(m.StripeBalance), strings.ToUpper(m.StripeCurrency))
		fmt.Printf("  Charges (24h):    %d\n", m.StripeCharges24h)
		fmt.Printf("  Revenue (24h):    %s %s\n", formatCurrency(m.StripeRevenue24h), strings.ToUpper(m.StripeCurrency))
		fmt.Printf("  Subscriptions:    %d\n", m.StripeSubscriptions)
	} else {
		fmt.Println("  (no STRIPE_SECRET_KEY)")
	}
	fmt.Println()

	fmt.Println("╚══════════════════════════════════════════════════════════════════════════════════╝")
}

func formatCurrency(amount int64) string {
	major := amount / 100
	minor := amount % 100
	if minor < 0 {
		minor = -minor
	}
	return fmt.Sprintf("%d.%02d", major, minor)
}
