package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"math"
	"math/rand"
	"net/http"
	"os"
	"sort"
	"strconv"
	"strings"
	"time"
)

// ── OCEL v2 event types (mirrors PDS ocelLog output) ──

type ocelEvent struct {
	TS         string `json:"ts"`
	Method     string `json:"method"`
	Ms         int    `json:"ms"`
	Status     int    `json:"status"`
	Auth       string `json:"auth"`
	Type       string `json:"type,omitempty"`       // xrpc / access / query
	HTTPMethod string `json:"httpMethod,omitempty"` // GET / POST
	Colo       string `json:"colo,omitempty"`
	IP         string `json:"ip,omitempty"`
	UA         string `json:"ua,omitempty"`
	Country    string `json:"country,omitempty"`
	Err        string `json:"err,omitempty"`
}

// queryEvent represents a kagami query OCEL event (blob2='query') for process mining.
type queryEvent struct {
	TS                   string  `json:"ts"`
	CallerNsid           string  `json:"callerNsid"`
	QueryHash            string  `json:"queryHash"`
	Risk                 string  `json:"risk"`
	SqlHead              string  `json:"sqlHead"`
	Kind                 string  `json:"kind"` // end / slow / error / failed
	ActualMs             float64 `json:"actualMs"`
	Status               int     `json:"status"`
	RowCount             int     `json:"rowCount"`
	EstimatedMemoryBytes float64 `json:"estimatedMemoryBytes"`
	EstimatedMs          float64 `json:"estimatedMs"`
	EstimatedCpuUnits    float64 `json:"estimatedCpuUnits"`
}

type queryAgg struct {
	Count          int     `json:"count"`
	Errors         int     `json:"errors"`
	SlowCount      int     `json:"slowCount"`
	AvgActualMs    float64 `json:"avgActualMs"`
	MaxActualMs    float64 `json:"maxActualMs"`
	AvgEstimatedMs float64 `json:"avgEstimatedMs"`
	AvgMemoryBytes float64 `json:"avgMemoryBytes"`
	TotalRows      int     `json:"totalRows"`
	OomRiskCount   int     `json:"oomRiskCount"`
}

type ocelAgg struct {
	Count      int     `json:"count"`
	Errors     int     `json:"errors"`
	TotalMs    float64 `json:"totalMs"`
	MaxMs      float64 `json:"maxMs"`
	P99Samples []int   `json:"p99Samples"`
	// Analytics Engine native percentiles (preferred over P99Samples when present)
	P50Ms float64 `json:"p50Ms,omitempty"`
	P99Ms float64 `json:"p99Ms,omitempty"`
}

type ocelResponse struct {
	Events          []ocelEvent         `json:"events"`
	Access          []ocelEvent         `json:"access"`
	CLI             []ocelEvent         `json:"cli"`
	Queries         []queryEvent        `json:"queries"`
	Aggregates      map[string]ocelAgg  `json:"aggregates"`
	QueryAggregates map[string]queryAgg `json:"queryAggregates"`
	XrpcCount       int                 `json:"xrpcCount"`
	AccessCount     int                 `json:"accessCount"`
	CLICount        int                 `json:"cliCount"`
	QueryCount      int                 `json:"queryCount"`
}

func runLogs(args []string) error {
	// Subcommand routing: gftd logs arch
	if len(args) > 0 && args[0] == "arch" {
		return runLogsArch(args[1:])
	}

	fs := flag.NewFlagSet("logs", flag.ContinueOnError)
	pdsURL := fs.String("pds", defaultPDSURL, "PDS base URL")
	asJSON := fs.Bool("json", false, "emit JSON")
	limit := fs.Int("limit", 200, "max events to fetch")
	method := fs.String("method", "", "filter by XRPC method")
	errorsOnly := fs.Bool("errors", false, "show only errors (status >= 400)")
	showAccess := fs.Bool("access", false, "show access log (non-XRPC HTTP requests)")
	showXrpc := fs.Bool("xrpc", false, "show XRPC log only")
	showCLI := fs.Bool("cli", false, "show CLI command events (gftd build/deploy/etc)")
	showQuery := fs.Bool("query", false, "show query events (kagami Sql execution, process mining)")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	// Try CF Analytics Engine SQL API first (direct, fastest)
	cfAPIToken := resolveCFAnalyticsToken()

	var data ocelResponse
	accountID := "4da88288dc30d9ee257f319d3c33ecf0"

	if cfAPIToken != "" {
		// Analytics Engine SQL — direct CF API (no PDS hop)
		var err error
		data, err = fetchOcelFromAE(cfAPIToken, accountID, *limit)
		if err != nil {
			fmt.Fprintf(os.Stderr, "WARN: Analytics Engine query failed (%v), falling back to PDS KV\n", err)
			cfAPIToken = "" // fall through to PDS
		}
	} else if hasWranglerOAuthToken() {
		fmt.Fprintf(os.Stderr, "WARN: Wrangler OAuth detected, but Analytics Engine SQL needs CF_API_TOKEN/CLOUDFLARE_API_TOKEN; falling back to PDS KV\n")
	}

	if cfAPIToken == "" {
		// Fallback: PDS KV endpoint
		token := resolveGFTDToken()
		if token == "" {
			return analyticsAuthRequiredError()
		}
		var err error
		data, err = fetchOcelFromPDS(token, strings.TrimRight(*pdsURL, "/"), *limit)
		if err != nil {
			return err
		}
	}

	// Filter
	filtered := data.Events
	if *method != "" {
		var f []ocelEvent
		for _, e := range filtered {
			if strings.Contains(strings.ToLower(e.Method), strings.ToLower(*method)) {
				f = append(f, e)
			}
		}
		filtered = f
	}
	if *errorsOnly {
		var f []ocelEvent
		for _, e := range filtered {
			if e.Status >= 400 {
				f = append(f, e)
			}
		}
		filtered = f
	}

	if *asJSON {
		diagnostics := buildLogsDiagnostics(data, filtered)
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(map[string]any{
			"events":          filtered,
			"access":          data.Access,
			"cli":             data.CLI,
			"queries":         data.Queries,
			"aggregates":      data.Aggregates,
			"queryAggregates": data.QueryAggregates,
			"xrpcCount":       data.XrpcCount,
			"accessCount":     data.AccessCount,
			"cliCount":        data.CLICount,
			"queryCount":      data.QueryCount,
			"diagnostics":     diagnostics,
		})
	}

	printLogsReport(data, filtered, *showAccess, *showXrpc, *showCLI, *showQuery)
	return nil
}

func printLogsReport(data ocelResponse, events []ocelEvent, showAccess bool, showXrpc bool, showCLI bool, showQuery bool) {
	fmt.Println()
	fmt.Println("╔══════════════════════════════════════════════════════════════════════════════════╗")
	fmt.Println("║                    GFTD OCEL v2 Event Log                                      ║")
	fmt.Printf("║                    %s                                     ║\n", time.Now().Format("2006-01-02 15:04:05"))
	fmt.Println("╠══════════════════════════════════════════════════════════════════════════════════╣")
	fmt.Println()

	// ── Aggregates table (per-method SLA) ──
	if len(data.Aggregates) > 0 {
		type aggRow struct {
			Method  string
			Count   int
			Errors  int
			ErrRate float64
			AvgMs   float64
			MaxMs   float64
			P50Ms   float64
			P99Ms   float64
			Grade   string
		}

		var rows []aggRow
		for m, a := range data.Aggregates {
			avg := 0.0
			if a.Count > 0 {
				avg = a.TotalMs / float64(a.Count)
			}
			errRate := 0.0
			if a.Count > 0 {
				errRate = float64(a.Errors) / float64(a.Count) * 100
			}
			var p50, p99 float64
			if a.P50Ms > 0 || a.P99Ms > 0 {
				// Analytics Engine native percentiles
				p50, p99 = a.P50Ms, a.P99Ms
			} else {
				p50, p99 = percentiles(a.P99Samples)
			}
			grade := latencyGrade(p50, errRate)
			rows = append(rows, aggRow{m, a.Count, a.Errors, errRate, avg, a.MaxMs, p50, p99, grade})
		}
		sort.Slice(rows, func(i, j int) bool { return rows[i].Count > rows[j].Count })

		fmt.Println("  NSID Aggregates (rolling 1h):")
		fmt.Println("  ┌─────────────────────────────────────────┬───────┬───────┬────────┬────────┬────────┬────────┬───────┐")
		fmt.Println("  │ Method                                  │ Count │ Errs  │ Err%   │ p50    │ p99    │ Max    │ Grade │")
		fmt.Println("  ├─────────────────────────────────────────┼───────┼───────┼────────┼────────┼────────┼────────┼───────┤")
		for _, r := range rows {
			m := r.Method
			if len(m) > 39 {
				m = m[:39]
			}
			errMark := fmt.Sprintf("%.1f%%", r.ErrRate)
			if r.ErrRate > 5 {
				errMark = fmt.Sprintf("%.1f%% !", r.ErrRate)
			}
			fmt.Printf("  │ %-39s │ %5d │ %5d │ %6s │ %4.0fms │ %4.0fms │ %4.0fms │   %s   │\n",
				m, r.Count, r.Errors, errMark, r.P50Ms, r.P99Ms, r.MaxMs, r.Grade)
		}
		fmt.Println("  └─────────────────────────────────────────┴───────┴───────┴────────┴────────┴────────┴────────┴───────┘")

		// Summary
		totalReqs := 0
		totalErrs := 0
		for _, r := range rows {
			totalReqs += r.Count
			totalErrs += r.Errors
		}
		overallErrRate := 0.0
		if totalReqs > 0 {
			overallErrRate = float64(totalErrs) / float64(totalReqs) * 100
		}
		fmt.Printf("  Total: %d requests, %d errors (%.2f%% error rate)\n", totalReqs, totalErrs, overallErrRate)
		fmt.Println()

		// SLA compliance check
		fmt.Println("  p99 SLA Compliance:")
		type nsidTarget struct {
			method string
			tier   string
			p99    float64
		}
		targets := []nsidTarget{
			{"ComAtprotoRepoCreateRecord", "interactive", 100},
			{"ComAtprotoRepoGetRecord", "instant", 20},
			{"AppBskyFeedGetTimeline", "interactive", 100},
			{"AppBskyFeedGetAuthorFeed", "interactive", 100},
			{"AppBskyFeedGetDiscoverFeed", "tolerable", 500},
			{"AppBskyFeedGetPostThread", "tolerable", 500},
			{"AppBskyFeedSearchPosts", "tolerable", 500},
			{"AppBskyActorGetProfile", "instant", 20},
			{"AppBskyActorSearchActors", "tolerable", 500},
			{"AppBskyGraphGetFollowers", "interactive", 100},
			{"AppBskyGraphGetFollows", "interactive", 100},
			{"AppBskyNotificationListNotifications", "interactive", 100},
			{"AiGftdConvoSendMessage", "interactive", 100},
		}
		met := 0
		gap := 0
		for _, t := range targets {
			a, ok := data.Aggregates[t.method]
			if !ok {
				continue
			}
			p99 := a.P99Ms
			if p99 == 0 {
				_, p99 = percentiles(a.P99Samples)
			}
			status := "OK"
			if p99 > t.p99 {
				status = "GAP"
				gap++
			} else {
				met++
			}
			if status == "GAP" {
				m := t.method
				if len(m) > 35 {
					m = m[:35]
				}
				fmt.Printf("    [GAP] %-35s p99=%4.0fms > target %4.0fms (%s)\n", m, p99, t.p99, t.tier)
			}
		}
		if gap == 0 && met > 0 {
			fmt.Printf("    All %d monitored NSIDs within p99 target\n", met)
		} else if met+gap > 0 {
			fmt.Printf("    %d/%d NSIDs within target, %d gaps\n", met, met+gap, gap)
		}
		fmt.Println()
	}

	// ── Recent events ──
	fmt.Printf("  Recent XRPC Events (%d of %d total):\n", len(events), data.XrpcCount)
	if len(events) > 50 {
		events = events[:50]
	}
	fmt.Println("  ┌─────────────────────┬─────────────────────────────────────────┬───────┬────────┬────────┐")
	fmt.Println("  │ Timestamp           │ Method                                  │ Status│ Latency│ Auth   │")
	fmt.Println("  ├─────────────────────┼─────────────────────────────────────────┼───────┼────────┼────────┤")
	for _, e := range events {
		ts := e.TS
		if len(ts) > 19 {
			ts = ts[:19]
		}
		m := e.Method
		if len(m) > 39 {
			m = m[:39]
		}
		statusMark := fmt.Sprintf("%d", e.Status)
		if e.Status >= 500 {
			statusMark = fmt.Sprintf("%d !!", e.Status)
		} else if e.Status >= 400 {
			statusMark = fmt.Sprintf("%d !", e.Status)
		}
		fmt.Printf("  │ %s │ %-39s │ %-5s │ %4dms │ %-6s │\n",
			ts, m, statusMark, e.Ms, e.Auth)
	}
	fmt.Println("  └─────────────────────┴─────────────────────────────────────────┴───────┴────────┴────────┘")
	fmt.Println()

	// ── Error breakdown ──
	errCount := 0
	errMethods := map[string]int{}
	for _, e := range data.Events {
		if e.Status >= 400 {
			errCount++
			errMethods[e.Method]++
		}
	}
	if errCount > 0 {
		fmt.Printf("  Errors: %d total\n", errCount)
		type errEntry struct {
			method string
			count  int
		}
		var errs []errEntry
		for m, c := range errMethods {
			errs = append(errs, errEntry{m, c})
		}
		sort.Slice(errs, func(i, j int) bool { return errs[i].count > errs[j].count })
		for _, e := range errs {
			if e.count > 0 {
				fmt.Printf("    %-40s %d errors\n", e.method, e.count)
			}
		}
		fmt.Println()
	}

	// ── Access log ──
	if showAccess || (!showXrpc && len(data.Access) > 0) {
		accessEvents := data.Access
		if len(accessEvents) > 30 {
			accessEvents = accessEvents[:30]
		}
		fmt.Printf("  Access Log (%d of %d total):\n", len(accessEvents), data.AccessCount)
		fmt.Println("  ┌─────────────────────┬──────┬──────────────────────────────┬───────┬────────┬──────┬─────────┐")
		fmt.Println("  │ Timestamp           │ Verb │ Path                         │ Status│ Latency│ Colo │ Country │")
		fmt.Println("  ├─────────────────────┼──────┼──────────────────────────────┼───────┼────────┼──────┼─────────┤")
		for _, e := range accessEvents {
			ts := e.TS
			if len(ts) > 19 {
				ts = ts[:19]
			}
			path := e.Method
			if len(path) > 28 {
				path = path[:28]
			}
			verb := e.HTTPMethod
			if verb == "" {
				verb = "GET"
			}
			colo := e.Colo
			if len(colo) > 4 {
				colo = colo[:4]
			}
			country := e.Country
			if len(country) > 5 {
				country = country[:5]
			}
			fmt.Printf("  │ %s │ %-4s │ %-28s │ %5d │ %4dms │ %-4s │ %-7s │\n",
				ts, verb, path, e.Status, e.Ms, colo, country)
		}
		fmt.Println("  └─────────────────────┴──────┴──────────────────────────────┴───────┴────────┴──────┴─────────┘")
		fmt.Println()

		// Access log stats
		statusCounts := map[int]int{}
		for _, e := range data.Access {
			bucket := e.Status / 100 * 100
			statusCounts[bucket]++
		}
		if len(statusCounts) > 0 {
			fmt.Print("  HTTP Status: ")
			codes := []int{}
			for c := range statusCounts {
				codes = append(codes, c)
			}
			sort.Ints(codes)
			for _, c := range codes {
				fmt.Printf("%dxx=%d  ", c/100, statusCounts[c])
			}
			fmt.Println()

			// Geo distribution
			geoCounts := map[string]int{}
			for _, e := range data.Access {
				if e.Country != "" {
					geoCounts[e.Country]++
				}
			}
			if len(geoCounts) > 0 {
				fmt.Print("  Geo: ")
				type gc struct {
					c string
					n int
				}
				var gcs []gc
				for c, n := range geoCounts {
					gcs = append(gcs, gc{c, n})
				}
				sort.Slice(gcs, func(i, j int) bool { return gcs[i].n > gcs[j].n })
				for i, g := range gcs {
					if i > 5 {
						fmt.Printf("+%d more", len(gcs)-5)
						break
					}
					fmt.Printf("%s=%d  ", g.c, g.n)
				}
				fmt.Println()
			}

			// Colo distribution
			coloCounts := map[string]int{}
			for _, e := range data.Access {
				if e.Colo != "" {
					coloCounts[e.Colo]++
				}
			}
			if len(coloCounts) > 0 {
				fmt.Print("  Edge PoP: ")
				type cc struct {
					c string
					n int
				}
				var ccs []cc
				for c, n := range coloCounts {
					ccs = append(ccs, cc{c, n})
				}
				sort.Slice(ccs, func(i, j int) bool { return ccs[i].n > ccs[j].n })
				for i, g := range ccs {
					if i > 8 {
						fmt.Printf("+%d more", len(ccs)-8)
						break
					}
					fmt.Printf("%s=%d  ", g.c, g.n)
				}
				fmt.Println()
			}
			fmt.Println()
		}
	}

	// ── CLI events ──
	if showCLI || (!showXrpc && !showAccess && len(data.CLI) > 0) {
		cliEvents := data.CLI
		if len(cliEvents) > 30 {
			cliEvents = cliEvents[:30]
		}
		fmt.Printf("  CLI Events (%d of %d total):\n", len(cliEvents), data.CLICount)
		fmt.Println("  ┌─────────────────────┬──────────────────────────────┬────────┬──────────┬───────────────────┐")
		fmt.Println("  │ Timestamp           │ Command                      │ Status │ Duration │ Host              │")
		fmt.Println("  ├─────────────────────┼──────────────────────────────┼────────┼──────────┼───────────────────┤")
		for _, e := range cliEvents {
			ts := e.TS
			if len(ts) > 19 {
				ts = ts[:19]
			}
			m := e.Method
			if len(m) > 28 {
				m = m[:28]
			}
			statusMark := "OK"
			if e.Status >= 1 {
				statusMark = "ERR"
			}
			host := e.Colo
			if len(host) > 17 {
				host = host[:17]
			}
			fmt.Printf("  │ %s │ %-28s │ %-6s │ %6dms │ %-17s │\n",
				ts, m, statusMark, e.Ms, host)
		}
		fmt.Println("  └─────────────────────┴──────────────────────────────┴────────┴──────────┴───────────────────┘")
		fmt.Println()
	}

	// ── Query events (process mining) ──
	if showQuery || (!showXrpc && !showAccess && !showCLI && len(data.Queries) > 0) {
		// Query aggregates table (per-caller NSID)
		if len(data.QueryAggregates) > 0 {
			type qaRow struct {
				Caller       string
				Count        int
				Errors       int
				SlowCount    int
				AvgActualMs  float64
				MaxActualMs  float64
				AvgEstMs     float64
				AvgMemMB     float64
				OomRiskCount int
				Grade        string
			}
			var qaRows []qaRow
			for caller, qa := range data.QueryAggregates {
				memMB := qa.AvgMemoryBytes / (1024 * 1024)
				grade := "S"
				switch {
				case qa.OomRiskCount > 0:
					grade = "F"
				case qa.AvgActualMs > 3000:
					grade = "D"
				case qa.AvgActualMs > 1000:
					grade = "C"
				case qa.AvgActualMs > 200:
					grade = "B"
				case qa.AvgActualMs > 50:
					grade = "A"
				}
				qaRows = append(qaRows, qaRow{caller, qa.Count, qa.Errors, qa.SlowCount, qa.AvgActualMs, qa.MaxActualMs, qa.AvgEstimatedMs, memMB, qa.OomRiskCount, grade})
			}
			sort.Slice(qaRows, func(i, j int) bool { return qaRows[i].Count > qaRows[j].Count })

			fmt.Println("  Query Process Mining (per-caller NSID):")
			fmt.Println("  ┌─────────────────────────────────────────┬───────┬──────┬──────┬─────────┬─────────┬─────────┬────────┬─────┬───────┐")
			fmt.Println("  │ Caller NSID                             │ Count │ Errs │ Slow │ Avg(ms) │ Max(ms) │ Est(ms) │ Mem MB │ OOM │ Grade │")
			fmt.Println("  ├─────────────────────────────────────────┼───────┼──────┼──────┼─────────┼─────────┼─────────┼────────┼─────┼───────┤")
			for _, r := range qaRows {
				c := r.Caller
				if len(c) > 39 {
					c = c[:39]
				}
				fmt.Printf("  │ %-39s │ %5d │ %4d │ %4d │ %5.0fms │ %5.0fms │ %5.0fms │ %4.1fMB │ %3d │   %s   │\n",
					c, r.Count, r.Errors, r.SlowCount, r.AvgActualMs, r.MaxActualMs, r.AvgEstMs, r.AvgMemMB, r.OomRiskCount, r.Grade)
			}
			fmt.Println("  └─────────────────────────────────────────┴───────┴──────┴──────┴─────────┴─────────┴─────────┴────────┴─────┴───────┘")
			fmt.Println()

			// OOM risk summary
			totalOom := 0
			totalSlow := 0
			for _, r := range qaRows {
				totalOom += r.OomRiskCount
				totalSlow += r.SlowCount
			}
			if totalOom > 0 {
				fmt.Printf("  !! OOM Risk: %d queries exceeded memory budget (2GB)\n", totalOom)
			}
			if totalSlow > 0 {
				fmt.Printf("  !! Slow: %d queries exceeded 3s threshold\n", totalSlow)
			}
			fmt.Println()
		}

		// Recent query events
		queryEvents := data.Queries
		if len(queryEvents) > 30 {
			queryEvents = queryEvents[:30]
		}
		if len(queryEvents) > 0 {
			fmt.Printf("  Recent Query Events (%d of %d total):\n", len(queryEvents), data.QueryCount)
			fmt.Println("  ┌─────────────────────┬──────────────────────────────┬──────┬─────────┬─────────┬───────┬────────┬──────────────────────────────────────────┐")
			fmt.Println("  │ Timestamp           │ Caller                       │ Kind │ Act(ms) │ Est(ms) │ Rows  │ Risk   │ Sql                                   │")
			fmt.Println("  ├─────────────────────┼──────────────────────────────┼──────┼─────────┼─────────┼───────┼────────┼──────────────────────────────────────────┤")
			for _, q := range queryEvents {
				ts := q.TS
				if len(ts) > 19 {
					ts = ts[:19]
				}
				caller := q.CallerNsid
				if len(caller) > 28 {
					caller = caller[:28]
				}
				cyHead := q.SqlHead
				if len(cyHead) > 38 {
					cyHead = cyHead[:38]
				}
				risk := q.Risk
				if len(risk) > 6 {
					risk = risk[:6]
				}
				fmt.Printf("  │ %s │ %-28s │ %-4s │ %5.0fms │ %5.0fms │ %5d │ %-6s │ %-40s │\n",
					ts, caller, q.Kind, q.ActualMs, q.EstimatedMs, q.RowCount, risk, cyHead)
			}
			fmt.Println("  └─────────────────────┴──────────────────────────────┴──────┴─────────┴─────────┴───────┴────────┴──────────────────────────────────────────┘")
			fmt.Println()
		}
	}

	fmt.Printf("  Summary: %d XRPC events, %d access events, %d CLI events, %d query events\n", data.XrpcCount, data.AccessCount, data.CLICount, data.QueryCount)
	diagnostics := buildLogsDiagnostics(data, events)
	if len(diagnostics.LikelyCauses) > 0 {
		fmt.Println("  Likely Causes:")
		for _, cause := range diagnostics.LikelyCauses {
			fmt.Printf("    - %s\n", cause)
		}
	}
	fmt.Println()
	fmt.Println("╚══════════════════════════════════════════════════════════════════════════════════╝")
}

type logsDiagnostics struct {
	LikelyCauses        []string       `json:"likelyCauses,omitempty"`
	ErrorMethods        map[string]int `json:"errorMethods,omitempty"`
	Access404Paths      map[string]int `json:"access404Paths,omitempty"`
	BlockedGraphQueries int            `json:"blockedGraphQueries,omitempty"`
	LegacyInternal404s  int            `json:"legacyInternal404s,omitempty"`
	OomRiskQueries      int            `json:"oomRiskQueries,omitempty"`
	SlowQueries         int            `json:"slowQueries,omitempty"`
	ReverseTopology     []logsCause    `json:"reverseTopology,omitempty"`
}

type logsCause struct {
	Key        string   `json:"key"`
	Category   string   `json:"category"`
	Severity   string   `json:"severity"`
	Score      int      `json:"score"`
	RootCause  string   `json:"rootCause"`
	Action     string   `json:"action"`
	Symptoms   []string `json:"symptoms,omitempty"`
	Dependents []string `json:"dependents,omitempty"`
	Evidence   []string `json:"evidence,omitempty"`
}

func buildLogsDiagnostics(data ocelResponse, events []ocelEvent) logsDiagnostics {
	out := logsDiagnostics{
		ErrorMethods:   map[string]int{},
		Access404Paths: map[string]int{},
	}

	for _, e := range events {
		if e.Status >= 400 {
			out.ErrorMethods[e.Method]++
		}
		if e.Method == "ai.gftd.kagami.sql" && (e.Status == 401 || e.Status == 403) {
			out.BlockedGraphQueries++
		}
	}

	legacy404 := 0
	for _, e := range data.Access {
		if e.Status != 404 {
			continue
		}
		out.Access404Paths[e.Method]++
		if strings.HasPrefix(e.Method, "/internal/") || strings.HasPrefix(e.Method, "/_internal/") {
			legacy404++
		}
	}
	out.LegacyInternal404s = legacy404

	if out.BlockedGraphQueries >= 5 {
		out.LikelyCauses = append(out.LikelyCauses, "ai.gftd.kagami.sql is policy-blocked (401/403). Use allowed read paths or proper org-scoped auth.")
	}
	if out.LegacyInternal404s >= 5 {
		out.LikelyCauses = append(out.LikelyCauses, "Legacy internal endpoints (/internal/*, /_internal/*) are being called and returning 404. Migrate callers to supported XRPC routes.")
	}

	// Query process mining diagnostics
	for _, q := range data.Queries {
		if q.Risk == "oom_risk" {
			out.OomRiskQueries++
		}
		if q.Kind == "slow" {
			out.SlowQueries++
		}
	}
	if out.OomRiskQueries > 0 {
		out.LikelyCauses = append(out.LikelyCauses, fmt.Sprintf("%d queries estimated as OOM risk (>2GB memory). Check vertex_actor_ext TEXT column projections, missing bloom filter WHERE, or unbounded JOINs.", out.OomRiskQueries))
	}
	if out.SlowQueries >= 5 {
		out.LikelyCauses = append(out.LikelyCauses, fmt.Sprintf("%d slow queries (>3s). Check for full table scans, non-selective WHERE, or RisingWave CN memory pressure.", out.SlowQueries))
	}
	out.ReverseTopology = buildReverseTopologyDiagnostics(data)
	for _, cause := range out.ReverseTopology {
		line := fmt.Sprintf("[%s] %s -> %s", strings.ToUpper(cause.Severity), cause.RootCause, cause.Action)
		if len(cause.Dependents) > 0 {
			line += fmt.Sprintf(" (dependents: %s)", strings.Join(cause.Dependents, ", "))
		}
		out.LikelyCauses = append(out.LikelyCauses, line)
	}

	return out
}

func buildReverseTopologyDiagnostics(data ocelResponse) []logsCause {
	methodStats := collectMethodStats(data)
	causes := make([]logsCause, 0, 6)

	if cause, ok := detectGraphQueryRootCause(methodStats, data.QueryAggregates); ok {
		causes = append(causes, cause)
	}
	if cause, ok := detectWriteAuthRootCause(methodStats); ok {
		causes = append(causes, cause)
	}
	if cause, ok := detectPublicWriteRootCause(data.Events); ok {
		causes = append(causes, cause)
	}
	if cause, ok := detectUnsupportedRouteRootCause(methodStats); ok {
		causes = append(causes, cause)
	}
	if cause, ok := detectEntityGraphRootCause(methodStats); ok {
		causes = append(causes, cause)
	}

	sort.Slice(causes, func(i, j int) bool {
		if causes[i].Score == causes[j].Score {
			return causes[i].Key < causes[j].Key
		}
		return causes[i].Score > causes[j].Score
	})
	return causes
}

type logsMethodStats struct {
	Count    int
	Errors   int
	Statuses map[int]int
	P99Ms    float64
	MaxMs    float64
}

func collectMethodStats(data ocelResponse) map[string]logsMethodStats {
	stats := map[string]logsMethodStats{}
	for method, agg := range data.Aggregates {
		p99 := agg.P99Ms
		if p99 == 0 {
			_, p99 = percentiles(agg.P99Samples)
		}
		entry := logsMethodStats{
			Count:    agg.Count,
			Errors:   agg.Errors,
			Statuses: map[int]int{},
			P99Ms:    p99,
			MaxMs:    agg.MaxMs,
		}
		stats[method] = entry
	}
	for _, event := range data.Events {
		entry := stats[event.Method]
		if entry.Statuses == nil {
			entry.Statuses = map[int]int{}
		}
		if entry.Count == 0 {
			entry.Count = 1
		}
		if event.Status >= 400 && entry.Errors == 0 {
			entry.Errors = 1
		}
		entry.Statuses[event.Status]++
		if float64(event.Ms) > entry.MaxMs {
			entry.MaxMs = float64(event.Ms)
		}
		if float64(event.Ms) > entry.P99Ms {
			entry.P99Ms = float64(event.Ms)
		}
		stats[event.Method] = entry
	}
	return stats
}

func detectGraphQueryRootCause(methodStats map[string]logsMethodStats, queryAgg map[string]queryAgg) (logsCause, bool) {
	graph := methodStats["ai.gftd.kagami.sql"]
	if graph.Count == 0 {
		return logsCause{}, false
	}
	graph404 := graph.Statuses[404]
	graphBlocked := graph.Statuses[401] + graph.Statuses[403]
	graphGone := graph.Statuses[410]
	graphUpstream := 0
	for status, count := range graph.Statuses {
		if status >= 500 {
			graphUpstream += count
		}
	}
	if graph404 == 0 && graphBlocked == 0 && graphGone == 0 && graphUpstream == 0 && graph.P99Ms < 1500 {
		return logsCause{}, false
	}

	dependents := []string{}
	for _, method := range []string{
		"app.bsky.actor.getProfile",
		"app.bsky.feed.getPostThread",
		"com.atproto.repo.listRecords",
		"ai.gftd.mcp.message",
	} {
		stat := methodStats[method]
		qAgg := queryAgg[method]
		if stat.Count == 0 && qAgg.Count == 0 {
			continue
		}
		if stat.P99Ms >= 3000 || qAgg.Errors > 0 || qAgg.SlowCount > 0 {
			dependents = append(dependents, method)
		}
	}
	evidence := []string{
		fmt.Sprintf("ai.gftd.kagami.sql count=%d 404=%d 401/403=%d 410=%d 5xx=%d p99=%.0fms", graph.Count, graph404, graphBlocked, graphGone, graphUpstream, graph.P99Ms),
	}
	if qa, ok := queryAgg["ai.gftd.kagami.sql"]; ok && qa.Count > 0 {
		evidence = append(evidence, fmt.Sprintf("query aggregates count=%d errors=%d slow=%d avgActualMs=%.0f", qa.Count, qa.Errors, qa.SlowCount, qa.AvgActualMs))
	}
	return logsCause{
		Key:        "graph-query",
		Category:   "dependency",
		Severity:   severityFromScore(95),
		Score:      95,
		RootCause:  "Graph read path is unstable, deprecated, or upstream-failing at ai.gftd.kagami.sql",
		Action:     "Migrate callers to supported Kysely-backed reads or restore the permitted kagami route before tuning downstream handlers",
		Dependents: dependents,
		Evidence:   evidence,
		Symptoms:   []string{"404/410/5xx on ai.gftd.kagami.sql", "high p99 on graph-backed read APIs"},
	}, true
}

func detectWriteAuthRootCause(methodStats map[string]logsMethodStats) (logsCause, bool) {
	authFailures := 0
	evidence := []string{}
	symptoms := []string{}
	for _, method := range []string{
		"com.atproto.repo.createRecord",
		"ai.gftd.convo.createConvo",
		"ai.gftd.convo.send",
		"app.bsky.feed.like",
		"app.bsky.feed.repost",
		"com.atproto.server.getSession",
		"com.atproto.server.getServiceAuth",
	} {
		stat := methodStats[method]
		count := stat.Statuses[401] + stat.Statuses[403]
		if count == 0 {
			continue
		}
		authFailures += count
		evidence = append(evidence, fmt.Sprintf("%s auth failures=%d", method, count))
		symptoms = append(symptoms, method)
	}
	if authFailures < 3 {
		return logsCause{}, false
	}
	return logsCause{
		Key:       "write-auth",
		Category:  "auth",
		Severity:  severityFromScore(90),
		Score:     90,
		RootCause: "Write/admin calls are being issued without a valid session or scope",
		Action:    "Fix caller auth propagation for repo/convo mutations before retrying writes; current failures are not server-side latency regressions",
		Symptoms:  symptoms,
		Evidence:  evidence,
	}, true
}

func detectPublicWriteRootCause(events []ocelEvent) (logsCause, bool) {
	publicWriteFailures := map[string]int{}
	for _, event := range events {
		if !strings.EqualFold(event.Auth, "public") || event.Status < 400 {
			continue
		}
		switch event.Method {
		case "com.atproto.repo.createRecord",
			"ai.gftd.convo.createConvo",
			"ai.gftd.convo.send",
			"app.bsky.feed.post",
			"app.bsky.feed.like",
			"app.bsky.feed.repost":
			publicWriteFailures[event.Method]++
		}
	}
	total := 0
	evidence := make([]string, 0, len(publicWriteFailures))
	symptoms := make([]string, 0, len(publicWriteFailures))
	for method, count := range publicWriteFailures {
		total += count
		evidence = append(evidence, fmt.Sprintf("%s public write failures=%d", method, count))
		symptoms = append(symptoms, method)
	}
	if total < 3 {
		return logsCause{}, false
	}
	sort.Strings(evidence)
	sort.Strings(symptoms)
	return logsCause{
		Key:       "public-write",
		Category:  "auth",
		Severity:  severityFromScore(88),
		Score:     88,
		RootCause: "Write mutations are reaching backend handlers without session/service auth",
		Action:    "Reject unauthenticated write intents at the caller boundary and require session/service auth before invoking repo or convo mutations",
		Symptoms:  symptoms,
		Evidence:  evidence,
	}, true
}

func detectUnsupportedRouteRootCause(methodStats map[string]logsMethodStats) (logsCause, bool) {
	total404 := 0
	evidence := []string{}
	symptoms := []string{}
	for method, stat := range methodStats {
		if stat.Statuses[404] == 0 {
			continue
		}
		if strings.HasPrefix(method, "ai.gftd.apps.dojo.") || strings.HasPrefix(method, "ai.gftd.convo.") || method == "app.bsky.feed.post" || method == "app.bsky.feed.postAs" || method == "ai.gftd.graph.batchInsert" {
			total404 += stat.Statuses[404]
			evidence = append(evidence, fmt.Sprintf("%s 404=%d", method, stat.Statuses[404]))
			symptoms = append(symptoms, method)
		}
	}
	if total404 < 3 {
		return logsCause{}, false
	}
	return logsCause{
		Key:       "unsupported-route",
		Category:  "routing",
		Severity:  severityFromScore(80),
		Score:     80,
		RootCause: "Clients are calling NSIDs that are missing, legacy, or not mounted in this deployment",
		Action:    "Update client routing/feature flags to supported NSIDs and treat these 404s as contract drift, not backend bottlenecks",
		Symptoms:  symptoms,
		Evidence:  evidence,
	}, true
}

func detectEntityGraphRootCause(methodStats map[string]logsMethodStats) (logsCause, bool) {
	stat := methodStats["ai.gftd.pds.getEntityGraph"]
	deprecated := stat.Statuses[410]
	notPorted := stat.Statuses[501]
	slowSuccess := stat.P99Ms >= 30_000
	if deprecated == 0 && notPorted == 0 && !slowSuccess {
		return logsCause{}, false
	}
	evidence := []string{}
	symptoms := []string{}
	if deprecated > 0 {
		evidence = append(evidence, fmt.Sprintf("ai.gftd.pds.getEntityGraph 410=%d", deprecated))
		symptoms = append(symptoms, "410 on ai.gftd.pds.getEntityGraph")
	}
	if notPorted > 0 {
		evidence = append(evidence, fmt.Sprintf("ai.gftd.pds.getEntityGraph 501=%d", notPorted))
		symptoms = append(symptoms, "501 on ai.gftd.pds.getEntityGraph")
	}
	if slowSuccess {
		evidence = append(evidence, fmt.Sprintf("ai.gftd.pds.getEntityGraph p99=%.0fms", stat.P99Ms))
		symptoms = append(symptoms, "extreme latency on ai.gftd.pds.getEntityGraph")
	}
	return logsCause{
		Key:       "entity-graph",
		Category:  "feature-gap",
		Severity:  severityFromScore(70),
		Score:     70,
		RootCause: "ai.gftd.pds.getEntityGraph callers are still reaching deprecated or unbounded traversal paths",
		Action:    "Keep clients on knowledgeGraph mode only, remove any SQL-mode fallback from deployed UI, and finish the Kysely traversal port before re-enabling wider graph fetches",
		Symptoms:  symptoms,
		Evidence:  evidence,
	}, true
}

func severityFromScore(score int) string {
	switch {
	case score >= 90:
		return "critical"
	case score >= 75:
		return "high"
	default:
		return "medium"
	}
}

func percentiles(samples []int) (p50, p99 float64) {
	if len(samples) == 0 {
		return 0, 0
	}
	sorted := make([]int, len(samples))
	copy(sorted, samples)
	sort.Ints(sorted)
	p50 = float64(sorted[len(sorted)/2])
	idx99 := int(math.Ceil(float64(len(sorted))*0.99)) - 1
	if idx99 < 0 {
		idx99 = 0
	}
	if idx99 >= len(sorted) {
		idx99 = len(sorted) - 1
	}
	p99 = float64(sorted[idx99])
	return
}

// ── Analytics Engine SQL queries ──

func fetchOcelFromAE(apiToken, accountID string, limit int) (ocelResponse, error) {
	cols := "timestamp,blob1 AS method,blob2 AS type,blob3 AS auth,blob4 AS httpMethod,blob5 AS colo,blob6 AS country,blob7 AS ip,blob8 AS ua,double1 AS ms,double2 AS status"

	// Query events columns: blob1=callerNsid, blob2='query', blob3=queryHash, blob4=risk, blob5=sqlHead, blob6=kind
	// doubles: d1=actualMs, d2=status, d3=rowCount, d4=estMemory, d5=estMs, d6=estCpu
	queryCols := "timestamp,blob1 AS callerNsid,blob3 AS queryHash,blob4 AS risk,blob5 AS sqlHead,blob6 AS kind,double1 AS actualMs,double2 AS status,double3 AS rowCount,double4 AS estMemory,double5 AS estMs,double6 AS estCpu"
	recentXrpc := fmt.Sprintf("(SELECT timestamp, blob1, double1, double2 FROM ocel_v2 WHERE blob2='xrpc' ORDER BY timestamp DESC LIMIT %d)", limit)
	recentQuery := fmt.Sprintf("(SELECT timestamp, blob1, blob4, blob6, double1, double2, double4, double5 FROM ocel_v2 WHERE blob2='query' ORDER BY timestamp DESC LIMIT %d)", limit)

	queries := []string{
		fmt.Sprintf("SELECT %s FROM ocel_v2 WHERE blob2='xrpc' ORDER BY timestamp DESC LIMIT %d", cols, limit),
		fmt.Sprintf("SELECT %s FROM ocel_v2 WHERE blob2='access' ORDER BY timestamp DESC LIMIT %d", cols, limit),
		fmt.Sprintf("SELECT blob1 AS method, count() AS count, sum(double2>=400) AS errors, avg(double1) AS avgMs, max(double1) AS maxMs, quantileWeighted(0.50)(double1,1) AS p50Ms, quantileWeighted(0.99)(double1,1) AS p99Ms FROM %s GROUP BY blob1 ORDER BY count DESC LIMIT 50", recentXrpc),
		fmt.Sprintf("SELECT %s FROM ocel_v2 WHERE blob2='cli' ORDER BY timestamp DESC LIMIT %d", cols, limit),
		fmt.Sprintf("SELECT %s FROM ocel_v2 WHERE blob2='query' ORDER BY timestamp DESC LIMIT %d", queryCols, limit),
		// Query aggregates per caller NSID
		fmt.Sprintf("SELECT blob1 AS callerNsid, count() AS count, sum(double2>=400) AS errors, sum(blob6='slow') AS slowCount, avg(double1) AS avgActualMs, max(double1) AS maxActualMs, avg(double5) AS avgEstMs, avg(double4) AS avgMemory, sum(blob4='oom_risk') AS oomRiskCount FROM %s GROUP BY blob1 ORDER BY count DESC LIMIT 50", recentQuery),
	}

	results := make([][]map[string]any, 6)
	for i, sql := range queries {
		rows, err := aeQuerySQL(apiToken, accountID, sql)
		if err != nil {
			return ocelResponse{}, fmt.Errorf("AE query %d: %w", i, err)
		}
		results[i] = rows
	}

	mapEvent := func(r map[string]any) ocelEvent {
		return ocelEvent{
			TS:         fmt.Sprint(r["timestamp"]),
			Method:     fmt.Sprint(r["method"]),
			Ms:         jsonInt(r["ms"]),
			Status:     jsonInt(r["status"]),
			Auth:       fmt.Sprint(r["auth"]),
			Type:       fmt.Sprint(r["type"]),
			HTTPMethod: fmt.Sprint(r["httpMethod"]),
			Colo:       fmt.Sprint(r["colo"]),
			Country:    fmt.Sprint(r["country"]),
			IP:         fmt.Sprint(r["ip"]),
			UA:         fmt.Sprint(r["ua"]),
		}
	}

	var events, access, cli []ocelEvent
	for _, r := range results[0] {
		events = append(events, mapEvent(r))
	}
	for _, r := range results[1] {
		access = append(access, mapEvent(r))
	}
	for _, r := range results[3] {
		cli = append(cli, mapEvent(r))
	}

	agg := map[string]ocelAgg{}
	for _, r := range results[2] {
		m := fmt.Sprint(r["method"])
		agg[m] = ocelAgg{
			Count:   jsonInt(r["count"]),
			Errors:  jsonInt(r["errors"]),
			TotalMs: jsonFloat64(r["avgMs"]) * float64(jsonInt(r["count"])),
			MaxMs:   jsonFloat64(r["maxMs"]),
			P50Ms:   jsonFloat64(r["p50Ms"]),
			P99Ms:   jsonFloat64(r["p99Ms"]),
		}
	}

	// Query events (blob2='query')
	var queryEvents []queryEvent
	for _, r := range results[4] {
		queryEvents = append(queryEvents, queryEvent{
			TS:                   fmt.Sprint(r["timestamp"]),
			CallerNsid:           fmt.Sprint(r["callerNsid"]),
			QueryHash:            fmt.Sprint(r["queryHash"]),
			Risk:                 fmt.Sprint(r["risk"]),
			SqlHead:              fmt.Sprint(r["sqlHead"]),
			Kind:                 fmt.Sprint(r["kind"]),
			ActualMs:             jsonFloat64(r["actualMs"]),
			Status:               jsonInt(r["status"]),
			RowCount:             jsonInt(r["rowCount"]),
			EstimatedMemoryBytes: jsonFloat64(r["estMemory"]),
			EstimatedMs:          jsonFloat64(r["estMs"]),
			EstimatedCpuUnits:    jsonFloat64(r["estCpu"]),
		})
	}

	// Query aggregates per caller NSID
	qAggMap := map[string]queryAgg{}
	for _, r := range results[5] {
		caller := fmt.Sprint(r["callerNsid"])
		qAggMap[caller] = queryAgg{
			Count:          jsonInt(r["count"]),
			Errors:         jsonInt(r["errors"]),
			SlowCount:      jsonInt(r["slowCount"]),
			AvgActualMs:    jsonFloat64(r["avgActualMs"]),
			MaxActualMs:    jsonFloat64(r["maxActualMs"]),
			AvgEstimatedMs: jsonFloat64(r["avgEstMs"]),
			AvgMemoryBytes: jsonFloat64(r["avgMemory"]),
			OomRiskCount:   jsonInt(r["oomRiskCount"]),
		}
	}

	return ocelResponse{
		Events:          events,
		Access:          access,
		CLI:             cli,
		Queries:         queryEvents,
		Aggregates:      agg,
		QueryAggregates: qAggMap,
		XrpcCount:       len(events),
		AccessCount:     len(access),
		CLICount:        len(cli),
		QueryCount:      len(queryEvents),
	}, nil
}

func fetchOcelFromPDS(token, pdsURL string, limit int) (ocelResponse, error) {
	endpoints := []string{
		fmt.Sprintf("%s/_pds/ocel?limit=%d", pdsURL, limit),
		fmt.Sprintf("%s/xrpc/ai.gftd.pds.getOcel?limit=%d", pdsURL, limit),
	}
	var lastErr error
	internalToken := ""
	internalTokenAttempted := false
	for _, endpoint := range endpoints {
		tokens := []string{token}
		if internalToken != "" {
			tokens = append(tokens, internalToken)
		}
		for i := 0; i < len(tokens); i++ {
			req, err := http.NewRequest("GET", endpoint, nil)
			if err != nil {
				lastErr = err
				break
			}
			req.Header.Set("Authorization", "Bearer "+tokens[i])
			req.Header.Set("User-Agent", "gftd-logs/1.0")
			resp, err := http.DefaultClient.Do(req)
			if err != nil {
				lastErr = fmt.Errorf("PDS unreachable: %w", err)
				break
			}
			body, _ := io.ReadAll(resp.Body)
			resp.Body.Close()
			if resp.StatusCode == 404 {
				lastErr = fmt.Errorf("PDS endpoint not found: %s", endpoint)
				break
			}
			if resp.StatusCode == 403 && strings.Contains(strings.ToLower(string(body)), "requires internal auth") && !internalTokenAttempted {
				internalTokenAttempted = true
				minted, mintErr := mintServiceAuthToken(pdsURL, "ai.gftd.pds.getOcel")
				if mintErr != nil {
					lastErr = fmt.Errorf("PDS returned 403 at %s and service-auth mint failed: %w", endpoint, mintErr)
					break
				}
				internalToken = minted
				tokens = append(tokens, internalToken)
				continue
			}
			if resp.StatusCode != 200 {
				msg := truncStr(strings.TrimSpace(string(body)), 240)
				if msg != "" {
					lastErr = fmt.Errorf("PDS returned %d at %s: %s", resp.StatusCode, endpoint, msg)
				} else {
					lastErr = fmt.Errorf("PDS returned %d at %s", resp.StatusCode, endpoint)
				}
				break
			}
			var data ocelResponse
			if err := json.Unmarshal(body, &data); err != nil {
				lastErr = fmt.Errorf("parse error at %s: %w", endpoint, err)
				break
			}
			return data, nil
		}
	}
	if lastErr == nil {
		lastErr = fmt.Errorf("PDS OCEL fetch failed")
	}
	return ocelResponse{}, lastErr
}

func mintServiceAuthToken(pdsURL, lxm string) (string, error) {
	baseToken := resolveGFTDToken()
	if baseToken == "" {
		return "", fmt.Errorf("no GFTD token found for service-auth mint")
	}
	pdsURL = strings.TrimRight(strings.TrimSpace(pdsURL), "/")
	if pdsURL == "" {
		pdsURL = resolvePDSBaseURL()
	}
	audience := "did:web:atproto.etzhayyim.com"
	if u, err := http.NewRequest("GET", pdsURL, nil); err == nil && u.URL.Hostname() != "" {
		audience = "did:web:" + u.URL.Hostname()
	}
	body, err := json.Marshal(map[string]any{
		"aud": audience,
		"lxm": lxm,
		"exp": time.Now().Unix() + 60,
	})
	if err != nil {
		return "", err
	}
	req, err := http.NewRequest("POST", pdsURL+"/xrpc/com.atproto.server.getServiceAuth", strings.NewReader(string(body)))
	if err != nil {
		return "", err
	}
	req.Header.Set("Authorization", "Bearer "+baseToken)
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("User-Agent", "gftd-logs/1.0")
	if did := resolveActiveDID(); did != "" {
		req.Header.Set("X-Active-DID", did)
	}
	if org := resolveOrgHint(); org != "" {
		req.Header.Set("X-Gftd-Org-Id", org)
	}
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return "", fmt.Errorf("getServiceAuth request failed: %w", err)
	}
	defer resp.Body.Close()
	raw, _ := io.ReadAll(resp.Body)
	if resp.StatusCode >= 400 {
		return "", fmt.Errorf("getServiceAuth HTTP %d: %s", resp.StatusCode, truncStr(string(raw), 240))
	}
	var out struct {
		Token string `json:"token"`
	}
	if err := json.Unmarshal(raw, &out); err != nil {
		return "", fmt.Errorf("getServiceAuth parse response: %w", err)
	}
	if strings.TrimSpace(out.Token) == "" {
		return "", fmt.Errorf("getServiceAuth returned empty token")
	}
	return out.Token, nil
}

func aeQuerySQL(apiToken, accountID, sql string) ([]map[string]any, error) {
	url := fmt.Sprintf("https://api.cloudflare.com/client/v4/accounts/%s/analytics_engine/sql", accountID)
	client := &http.Client{Timeout: 15 * time.Second}
	var lastErr error
	for attempt := 0; attempt < 4; attempt++ {
		req, err := http.NewRequest("POST", url, strings.NewReader(sql))
		if err != nil {
			return nil, err
		}
		req.Header.Set("Authorization", "Bearer "+apiToken)
		req.Header.Set("Content-Type", "text/plain")
		req.Header.Set("User-Agent", "gftd-logs/1.0")

		resp, err := client.Do(req)
		if err != nil {
			lastErr = err
		} else {
			body, readErr := io.ReadAll(resp.Body)
			resp.Body.Close()
			if readErr != nil {
				lastErr = readErr
			} else if resp.StatusCode == http.StatusOK {
				var result struct {
					Data []map[string]any `json:"data"`
					Meta json.RawMessage  `json:"meta"`
				}
				if err := json.Unmarshal(body, &result); err != nil {
					snippet := string(body)
					if len(snippet) > 200 {
						snippet = snippet[:200]
					}
					return nil, fmt.Errorf("AE parse: %w (body=%s)", err, snippet)
				}
				return result.Data, nil
			} else {
				msg := string(body)
				if len(msg) > 200 {
					msg = msg[:200]
				}
				lastErr = fmt.Errorf("AE SQL %d: %s", resp.StatusCode, msg)
				if !shouldRetryAEStatus(resp.StatusCode) || attempt == 3 {
					return nil, lastErr
				}
				time.Sleep(aeRetryDelay(resp.Header.Get("Retry-After"), attempt))
				continue
			}
		}
		if attempt == 3 {
			break
		}
		time.Sleep(aeRetryDelay("", attempt))
	}
	return nil, lastErr
}

func shouldRetryAEStatus(status int) bool {
	return status == http.StatusTooManyRequests || status >= 500
}

func aeRetryDelay(retryAfter string, attempt int) time.Duration {
	if secs, err := strconv.Atoi(strings.TrimSpace(retryAfter)); err == nil && secs > 0 {
		return time.Duration(secs) * time.Second
	}
	base := 400 * time.Millisecond
	maxJitter := 250 * time.Millisecond
	return time.Duration(1<<attempt)*base + time.Duration(rand.Int63n(int64(maxJitter)))
}

func jsonInt(v any) int {
	switch t := v.(type) {
	case float64:
		return int(t)
	case int:
		return t
	case int64:
		return int(t)
	case json.Number:
		n, _ := t.Int64()
		return int(n)
	case string:
		if strings.EqualFold(t, "true") {
			return 1
		}
		if strings.EqualFold(t, "false") || strings.TrimSpace(t) == "" {
			return 0
		}
		if n, err := strconv.ParseInt(t, 10, 64); err == nil {
			return int(n)
		}
		if f, err := strconv.ParseFloat(t, 64); err == nil {
			return int(f)
		}
	case bool:
		if t {
			return 1
		}
		return 0
	}
	return 0
}

func jsonFloat64(v any) float64 {
	switch t := v.(type) {
	case float64:
		return t
	case int:
		return float64(t)
	case int64:
		return float64(t)
	case json.Number:
		f, _ := t.Float64()
		return f
	case string:
		if strings.TrimSpace(t) == "" {
			return 0
		}
		f, _ := strconv.ParseFloat(t, 64)
		return f
	case bool:
		if t {
			return 1
		}
		return 0
	}
	return 0
}

func latencyGrade(p50Ms, errRate float64) string {
	if errRate > 10 {
		return "F"
	}
	if errRate > 5 {
		return "D"
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
