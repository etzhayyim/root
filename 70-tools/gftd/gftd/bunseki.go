package main

import (
	"crypto/sha256"
	"encoding/json"
	"flag"
	"fmt"
	"math"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"
)

// ── gftd bunseki — OCEL v2 Runtime Process Mining & Analysis ──

// ── Data Model ──

// bunsekiEvent represents a single OCEL v2 event from Analytics Engine.
type bunsekiEvent struct {
	TS       string  `json:"ts"`
	Method   string  `json:"method"`
	Activity string  `json:"activity"`
	Type     string  `json:"type"`
	Auth     string  `json:"auth"`
	Colo     string  `json:"colo"`
	Country  string  `json:"country"`
	IP       string  `json:"ip"`
	UA       string  `json:"ua"`
	Ms       float64 `json:"ms"`
	Status   int     `json:"status"`
}

// bunsekiTrace represents a sequence of events grouped by session (IP+UA hash).
type bunsekiTrace struct {
	SessionID  string         `json:"session_id"`
	Events     []bunsekiEvent `json:"events"`
	Activities []string       `json:"activities"`
}

// bunsekiDFGEdge represents a transition in the Directly-Follows Graph.
type bunsekiDFGEdge struct {
	From  string  `json:"from"`
	To    string  `json:"to"`
	Count int     `json:"count"`
	AvgMs float64 `json:"avg_ms"`
	P50Ms float64 `json:"p50_ms"`
	P99Ms float64 `json:"p99_ms"`
	MaxMs float64 `json:"max_ms"`
}

// bunsekiVariant represents a unique trace pattern.
type bunsekiVariant struct {
	Pattern    string   `json:"pattern"`
	Activities []string `json:"activities"`
	Count      int      `json:"count"`
	Percentage float64  `json:"percentage"`
	AvgMs      float64  `json:"avg_ms"`
}

// bunsekiConformanceResult represents conformance checking result for an expected path.
type bunsekiConformanceResult struct {
	Name         string   `json:"name"`
	ExpectedPath []string `json:"expected_path"`
	TotalTraces  int      `json:"total_traces"`
	ConformCount int      `json:"conform_count"`
	ConformRate  float64  `json:"conform_rate"`
	Deviations   []string `json:"deviations,omitempty"`
}

// bunsekiPerfTransition represents performance metrics for a specific activity transition.
type bunsekiPerfTransition struct {
	From     string  `json:"from"`
	To       string  `json:"to"`
	Count    int     `json:"count"`
	AvgMs    float64 `json:"avg_ms"`
	P50Ms    float64 `json:"p50_ms"`
	P99Ms    float64 `json:"p99_ms"`
	MaxMs    float64 `json:"max_ms"`
	TargetMs float64 `json:"target_ms"`
	Severity string  `json:"severity"`
}

// bunsekiRecommendation represents a prioritized improvement suggestion.
type bunsekiRecommendation struct {
	Priority    int    `json:"priority"`
	Severity    string `json:"severity"`
	Category    string `json:"category"`
	Description string `json:"description"`
	StaticRef   string `json:"static_ref,omitempty"`
	Fix         string `json:"fix"`
	Impact      string `json:"impact"`
}

// bunsekiReport is the full analysis output.
type bunsekiReport struct {
	AnalyzedAt      string                     `json:"analyzed_at"`
	LookbackMinutes int                        `json:"lookback_minutes"`
	LookbackHours   int                        `json:"lookback_hours,omitempty"` // backward compatibility
	TotalEvents     int                        `json:"total_events"`
	TotalTraces     int                        `json:"total_traces"`
	DFG             []bunsekiDFGEdge           `json:"dfg"`
	Variants        []bunsekiVariant           `json:"variants"`
	Conformance     []bunsekiConformanceResult `json:"conformance"`
	Performance     []bunsekiPerfTransition    `json:"performance"`
	Recommendations []bunsekiRecommendation    `json:"recommendations"`
	Score           bunsekiScore               `json:"score"`
}

// bunsekiScore represents the overall process health score.
type bunsekiScore struct {
	DFGEfficiency        float64 `json:"dfg_efficiency"`
	VariantConcentration float64 `json:"variant_concentration"`
	ConformanceRate      float64 `json:"conformance_rate"`
	PerformanceScore     float64 `json:"performance_score"`
	Overall              float64 `json:"overall"`
	Grade                string  `json:"grade"`
}

// ── Method → Activity Mapping ──

var methodActivityMap = map[string]string{
	// Profile
	"AppBskyActorGetProfile":     "profile:resolve",
	"AppBskyActorSearchActors":   "profile:search",
	"AppBskyActorGetSuggestions": "profile:suggest",
	// Auth
	"ComAtprotoServerCreateSession":  "auth:session",
	"ComAtprotoServerRefreshSession": "auth:refresh",
	"ComAtprotoServerDeleteSession":  "auth:logout",
	// Record CRUD
	"ComAtprotoRepoCreateRecord": "record:create",
	"ComAtprotoRepoPutRecord":    "record:update",
	"ComAtprotoRepoDeleteRecord": "record:delete",
	"ComAtprotoRepoGetRecord":    "record:read",
	"ComAtprotoRepoListRecords":  "record:list",
	// Feed (read)
	"AppBskyFeedGetTimeline":     "feed:timeline",
	"AppBskyFeedGetAuthorFeed":   "feed:author",
	"AppBskyFeedGetDiscoverFeed": "feed:discover",
	"AppBskyFeedGetPostThread":   "feed:thread",
	"AppBskyFeedSearchPosts":     "feed:search",
	// Social evolution
	"AppBskyFeedLike":                      "evolution:like",
	"AppBskyFeedRepost":                    "evolution:repost",
	"AppBskyGraphFollow":                   "evolution:follow",
	"AppBskyGraphGetFollowers":             "graph:followers",
	"AppBskyGraphGetFollows":               "graph:follows",
	"AppBskyNotificationListNotifications": "notification:list",
	"AppBskyNotificationGetUnreadCount":    "notification:unread",
	// Convo
	"AiGftdConvoSendMessage":   "convo:send",
	"AiGftdConvoGetMessages":   "convo:read",
	"ChatBskyConvoSendMessage": "convo:send",
	"ChatBskyConvoGetMessages": "convo:read",
	// Deploy (detected from method patterns)
	"ComAtprotoAdminRegisterApp": "deploy:register_profile",
}

// methodToActivity converts an XRPC method name (PascalCase or NSID dot-notation) to an OCEL activity type.
func methodToActivity(method string) string {
	if act, ok := methodActivityMap[method]; ok {
		return act
	}

	// Handle NSID dot-notation (e.g. "app.bsky.feed.getTimeline")
	lower := strings.ToLower(method)
	if strings.Contains(method, ".") {
		switch {
		case strings.HasPrefix(lower, "app.bsky.feed."):
			return "feed:" + nsidLastSegment(method)
		case strings.HasPrefix(lower, "app.bsky.actor."):
			return "profile:" + nsidLastSegment(method)
		case strings.HasPrefix(lower, "app.bsky.graph."):
			return "graph:" + nsidLastSegment(method)
		case strings.HasPrefix(lower, "app.bsky.notification."):
			return "notification:" + nsidLastSegment(method)
		case strings.HasPrefix(lower, "com.atproto.repo."):
			return "record:" + nsidLastSegment(method)
		case strings.HasPrefix(lower, "com.atproto.server."):
			return "auth:" + nsidLastSegment(method)
		case strings.HasPrefix(lower, "com.atproto.identity."):
			return "identity:" + nsidLastSegment(method)
		case strings.HasPrefix(lower, "com.atproto.sync."):
			return "sync:" + nsidLastSegment(method)
		case strings.HasPrefix(lower, "ai.gftd.identity."):
			return "gftd.identity:" + nsidLastSegment(method)
		case strings.HasPrefix(lower, "ai.gftd.convo."):
			return "convo:" + nsidLastSegment(method)
		case strings.HasPrefix(lower, "ai.gftd.apps."):
			return "gftd.apps:" + nsidLastSegment(method)
		case strings.HasPrefix(lower, "ai.gftd.kagami."):
			return "kagami:" + nsidLastSegment(method)
		case strings.HasPrefix(lower, "ai.gftd.pds."):
			return "pds:" + nsidLastSegment(method)
		case strings.HasPrefix(lower, "ai.gftd."):
			return "gftd:" + nsidLastSegment(method)
		case strings.HasPrefix(lower, "chat.bsky.convo."):
			return "convo:" + nsidLastSegment(method)
		default:
			return "other:" + nsidLastSegment(method)
		}
	}

	// Handle PascalCase (e.g. "AppBskyFeedGetTimeline")
	switch {
	case strings.HasPrefix(lower, "appbskyfeed"):
		return "feed:" + strings.ToLower(strings.TrimPrefix(method, "AppBskyFeed"))
	case strings.HasPrefix(lower, "appbskyactor"):
		return "profile:" + strings.ToLower(strings.TrimPrefix(method, "AppBskyActor"))
	case strings.HasPrefix(lower, "appbskygraph"):
		return "graph:" + strings.ToLower(strings.TrimPrefix(method, "AppBskyGraph"))
	case strings.HasPrefix(lower, "comatprotorepo"):
		return "record:" + strings.ToLower(strings.TrimPrefix(method, "ComAtprotoRepo"))
	case strings.HasPrefix(lower, "comatprotoserver"):
		return "auth:" + strings.ToLower(strings.TrimPrefix(method, "ComAtprotoServer"))
	case strings.HasPrefix(lower, "aigftd"):
		return "gftd:" + strings.ToLower(strings.TrimPrefix(method, "AiGftd"))
	default:
		return "other:" + method
	}
}

// nsidLastSegment extracts the last segment from an NSID (e.g. "app.bsky.feed.getTimeline" → "getTimeline").
func nsidLastSegment(nsid string) string {
	parts := strings.Split(nsid, ".")
	return parts[len(parts)-1]
}

// ── Expected Paths (Conformance Checking) ──

var expectedPaths = map[string][]string{
	"read_session":     {"auth:session", "feed:timeline"},
	"write_session":    {"auth:session", "record:create"},
	"profile_lookup":   {"profile:resolve"},
	"social_evolution": {"record:create", "evolution:like"},
	"deploy_pipeline":  {"deploy:register_profile"},
	"search_flow":      {"feed:search"},
	"convo_flow":       {"auth:session", "convo:send"},
}

// ── SLA Targets (ms) per activity category ──

var activitySLATargets = map[string]float64{
	"auth:":         50,
	"profile:":      20,
	"record:create": 100,
	"record:read":   20,
	"record:":       50,
	"feed:timeline": 100,
	"feed:discover": 500,
	"feed:thread":   500,
	"feed:search":   500,
	"feed:":         200,
	"convo:":        100,
	"evolution:":    100,
	"graph:":        100,
	"notification:": 100,
	"deploy:":       2000,
	"gftd:":         200,
}

// getTargetMs returns the SLA target latency for an activity transition.
func getTargetMs(activity string) float64 {
	// Exact match first
	if t, ok := activitySLATargets[activity]; ok {
		return t
	}
	// Prefix match
	for prefix, t := range activitySLATargets {
		if strings.HasPrefix(activity, prefix) {
			return t
		}
	}
	return 200 // default
}

// ── Command Entry Point ──

func runBunseki(args []string) error {
	if len(args) > 0 {
		switch args[0] {
		case "arch":
			return runBunsekiArch(args[1:])
		case "scan":
			return runBunsekiScan(args[1:])
		case "dfg":
			return runBunsekiDFG(args[1:])
		case "variants":
			return runBunsekiVariants(args[1:])
		case "conformance":
			return runBunsekiConformance(args[1:])
		case "performance":
			return runBunsekiPerformance(args[1:])
		case "recommendations":
			return runBunsekiRecommendations(args[1:])
		case "help", "--help", "-h":
			printBunsekiUsage()
			return nil
		default:
			return runBunsekiScan(args)
		}
	}
	return runBunsekiScan(args)
}

func printBunsekiUsage() {
	fmt.Print(`gftd bunseki — OCEL v2 Runtime Process Mining & System Performance Analysis

USAGE:
  gftd bunseki <command> [flags]

COMMANDS:
  scan            Full analysis: DFG + Variants + Conformance + Performance → unified report (default)
  dfg             Directly-Follows Graph — activity transition frequencies + latencies
  variants        Variant Analysis — group traces by activity sequence, rank by frequency
  conformance     Conformance Checking — compare observed traces against expected paths
  performance     Performance Analysis — per-transition latency bottleneck detection
  recommendations Prioritized improvement suggestions (runtime + static cross-reference)
  arch            Design Architecture Process Mining (inter-app DFG, variants, conformance, cycles)

FLAGS:
  --json            Output as JSON
  --limit           Max events to fetch (default: 1000)
  --minutes         Lookback window in minutes (default: 3)
  --hours           Lookback window in hours (overrides --minutes)
  --object-type     Filter by object type: actor, session, deploy, app (default: all)
  --top             Top N results (default: 20)
  --workspace-dir   Workspace root for static cross-reference (default: git root)

DATA SOURCE:
  CF Analytics Engine (ocel_v2 table) → trace construction → process mining algorithms
  Fallback: PDS KV endpoint (/_pds/ocel)

ALGORITHMS:
  DFG               Count activity transitions per session trace
  Variant Analysis   Group traces by activity sequence, rank by frequency
  Conformance        Subsequence match against expected process paths
  Performance        p50/p99/max latency per activity transition pair
  Cross-Reference    Match runtime bottlenecks to static code analysis (process-mining)
`)
}

// ── Shared Flag Parsing ──

type bunsekiFlags struct {
	jsonOut      bool
	limit        int
	hours        int // compatibility override
	minutes      int
	objectType   string
	top          int
	workspaceDir string
}

func parseBunsekiFlags(name string, args []string) (bunsekiFlags, error) {
	fs := flag.NewFlagSet("bunseki "+name, flag.ContinueOnError)
	var f bunsekiFlags
	fs.BoolVar(&f.jsonOut, "json", false, "output as JSON")
	fs.IntVar(&f.limit, "limit", 1000, "max events to fetch")
	fs.IntVar(&f.minutes, "minutes", 3, "lookback window (minutes)")
	fs.IntVar(&f.hours, "hours", 0, "lookback window (hours, overrides --minutes)")
	fs.StringVar(&f.objectType, "object-type", "", "filter by object type")
	fs.IntVar(&f.top, "top", 20, "top N results")
	fs.StringVar(&f.workspaceDir, "workspace-dir", "", "workspace root")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return f, err
		}
		return f, err
	}
	if f.workspaceDir == "" {
		cwd, _ := os.Getwd()
		f.workspaceDir, _ = findGitRoot(cwd)
	}
	if f.hours > 0 {
		f.minutes = f.hours * 60
	}
	if f.minutes < 1 {
		f.minutes = 1
	}
	return f, nil
}

// ── Data Fetch ──

// resolveCFToken resolves any locally-available Cloudflare credential.
// Wrangler OAuth is included for commands that can shell out to Wrangler.
func resolveCFToken() string {
	if t := os.Getenv("CF_API_TOKEN"); t != "" {
		return t
	}
	if t := os.Getenv("CLOUDFLARE_API_TOKEN"); t != "" {
		return t
	}
	if home, err := os.UserHomeDir(); err == nil {
		// Fallback: ~/.gftd/cf_api_token
		if b, err := os.ReadFile(home + "/.gftd/cf_api_token"); err == nil {
			if t := strings.TrimSpace(string(b)); t != "" {
				return t
			}
		}
	}
	if t := resolveWranglerOAuthToken(); t != "" {
		return t
	}
	return ""
}

// resolveCFAnalyticsToken resolves a direct Cloudflare API token that can call
// the Analytics Engine SQL REST API. Wrangler OAuth is intentionally excluded:
// it works for wrangler tail/whoami, but not for direct AE SQL POST requests.
func resolveCFAnalyticsToken() string {
	if t := os.Getenv("CF_API_TOKEN"); t != "" {
		return t
	}
	if t := os.Getenv("CLOUDFLARE_API_TOKEN"); t != "" {
		return t
	}
	if home, err := os.UserHomeDir(); err == nil {
		if b, err := os.ReadFile(home + "/.gftd/cf_api_token"); err == nil {
			if t := strings.TrimSpace(string(b)); t != "" {
				return t
			}
		}
	}
	return ""
}

func resolveWranglerOAuthToken() string {
	home, err := os.UserHomeDir()
	if err != nil {
		return ""
	}
	for _, dir := range []string{
		home + "/Library/Preferences/.wrangler/config",
		home + "/.wrangler/config",
		home + "/.config/.wrangler/config",
	} {
		path := dir + "/default.toml"
		b, err := os.ReadFile(path)
		if err != nil {
			continue
		}
		for _, line := range strings.Split(string(b), "\n") {
			line = strings.TrimSpace(line)
			if !strings.HasPrefix(line, "oauth_token") {
				continue
			}
			parts := strings.SplitN(line, "=", 2)
			if len(parts) != 2 {
				continue
			}
			token := strings.TrimSpace(parts[1])
			token = strings.Trim(token, "\"")
			if token != "" {
				return token
			}
		}
	}
	return ""
}

func hasWranglerOAuthToken() bool {
	return resolveWranglerOAuthToken() != ""
}

func analyticsAuthRequiredError() error {
	return fmt.Errorf("auth required — set CF_API_TOKEN/CLOUDFLARE_API_TOKEN for Analytics Engine SQL (Wrangler OAuth only works for wrangler tail/whoami)")
}

// fetchBunsekiEvents retrieves OCEL v2 events from CF Analytics Engine, with PDS KV fallback.
func fetchBunsekiEvents(minutes, limit int) ([]bunsekiEvent, error) {
	cfAPIToken := resolveCFAnalyticsToken()

	accountID := "4da88288dc30d9ee257f319d3c33ecf0"

	// Try Analytics Engine first
	if cfAPIToken != "" {
		sql := fmt.Sprintf(
			`SELECT timestamp, blob1 AS method, blob2 AS type, blob3 AS auth, `+
				`blob4 AS httpMethod, blob5 AS colo, blob6 AS country, `+
				`double1 AS ms, double2 AS status, index1 `+
				`FROM ocel_v2 `+
				`WHERE blob2 = 'xrpc' `+
				`AND timestamp >= now() - INTERVAL '%d' MINUTE `+
				`ORDER BY timestamp ASC `+
				`LIMIT %d`, minutes, limit)

		rows, err := aeQuerySQL(cfAPIToken, accountID, sql)
		if err == nil {
			var events []bunsekiEvent
			for _, r := range rows {
				method := fmt.Sprint(r["method"])
				ev := bunsekiEvent{
					TS:       fmt.Sprint(r["timestamp"]),
					Method:   method,
					Activity: methodToActivity(method),
					Type:     fmt.Sprint(r["type"]),
					Auth:     fmt.Sprint(r["auth"]),
					Colo:     fmt.Sprint(r["colo"]),
					Country:  fmt.Sprint(r["country"]),
					IP:       fmt.Sprint(r["index1"]),
					UA:       "",
					Ms:       jsonFloat64(r["ms"]),
					Status:   jsonInt(r["status"]),
				}
				events = append(events, ev)
			}
			return events, nil
		}
		fmt.Fprintf(os.Stderr, "WARN: Analytics Engine failed (%v), falling back to PDS KV\n", err)
	} else if hasWranglerOAuthToken() {
		fmt.Fprintf(os.Stderr, "WARN: Wrangler OAuth detected, but Analytics Engine SQL needs CF_API_TOKEN/CLOUDFLARE_API_TOKEN; falling back to PDS KV\n")
	}

	// Fallback: PDS KV endpoint
	return fetchBunsekiFromPDS(limit)
}

// fetchBunsekiFromPDS retrieves OCEL v2 events via PDS KV endpoint.
func fetchBunsekiFromPDS(limit int) ([]bunsekiEvent, error) {
	token := resolveGFTDToken()
	if token == "" {
		return nil, analyticsAuthRequiredError()
	}
	data, err := fetchOcelFromPDS(token, resolvePDSBaseURL(), limit)
	if err != nil {
		return nil, err
	}

	var events []bunsekiEvent
	for _, e := range data.Events {
		ev := bunsekiEvent{
			TS:       e.TS,
			Method:   e.Method,
			Activity: methodToActivity(e.Method),
			Type:     e.Type,
			Auth:     e.Auth,
			Colo:     e.Colo,
			Country:  e.Country,
			IP:       e.IP,
			UA:       e.UA,
			Ms:       float64(e.Ms),
			Status:   e.Status,
		}
		events = append(events, ev)
	}
	return events, nil
}

// ── Trace Construction ──

// sessionKey creates a session identifier from auth type + time window.
// Events within the same auth context and 5-second window are grouped.
func sessionKey(auth string, ts string) string {
	// Parse timestamp and bucket into 5-second windows
	t, err := time.Parse("2006-01-02 15:04:05", ts)
	if err != nil {
		t, err = time.Parse(time.RFC3339, ts)
	}
	bucket := ""
	if err == nil {
		bucket = fmt.Sprintf("%d", t.Unix()/5)
	} else {
		bucket = ts
	}
	h := sha256.Sum256([]byte(auth + "|" + bucket))
	return fmt.Sprintf("%x", h[:8])
}

// buildTraces groups events into session-based traces using auth + time window.
func buildTraces(events []bunsekiEvent, objectType string) []bunsekiTrace {
	groups := map[string][]bunsekiEvent{}
	for _, e := range events {
		if objectType != "" && !activityMatchesObjectType(e.Activity, objectType) {
			continue
		}
		key := sessionKey(e.Auth, e.TS)
		groups[key] = append(groups[key], e)
	}

	var traces []bunsekiTrace
	for sid, evts := range groups {
		if len(evts) < 2 {
			continue // single-event sessions are not traces
		}
		var activities []string
		for _, e := range evts {
			activities = append(activities, e.Activity)
		}
		traces = append(traces, bunsekiTrace{
			SessionID:  sid,
			Events:     evts,
			Activities: activities,
		})
	}

	sort.Slice(traces, func(i, j int) bool {
		return len(traces[i].Events) > len(traces[j].Events)
	})
	return traces
}

// activityMatchesObjectType checks if an activity belongs to a given object type.
func activityMatchesObjectType(activity, objectType string) bool {
	switch objectType {
	case "actor":
		return strings.HasPrefix(activity, "profile:") || strings.HasPrefix(activity, "graph:")
	case "session":
		return strings.HasPrefix(activity, "auth:") || strings.HasPrefix(activity, "feed:") || strings.HasPrefix(activity, "record:")
	case "deploy":
		return strings.HasPrefix(activity, "deploy:")
	case "app":
		return strings.HasPrefix(activity, "gftd:") || strings.HasPrefix(activity, "deploy:")
	default:
		return true
	}
}

// ── DFG (Directly-Follows Graph) ──

// buildDFG constructs the Directly-Follows Graph from traces.
func buildDFG(traces []bunsekiTrace) []bunsekiDFGEdge {
	type edgeKey struct{ from, to string }
	edgeData := map[edgeKey][]float64{}

	for _, trace := range traces {
		for i := 0; i < len(trace.Events)-1; i++ {
			key := edgeKey{trace.Events[i].Activity, trace.Events[i+1].Activity}
			edgeData[key] = append(edgeData[key], trace.Events[i+1].Ms)
		}
	}

	var edges []bunsekiDFGEdge
	for key, latencies := range edgeData {
		sort.Float64s(latencies)
		n := len(latencies)
		sum := 0.0
		for _, l := range latencies {
			sum += l
		}
		p50Idx := n / 2
		p99Idx := int(math.Ceil(float64(n)*0.99)) - 1
		if p99Idx >= n {
			p99Idx = n - 1
		}
		if p99Idx < 0 {
			p99Idx = 0
		}

		edges = append(edges, bunsekiDFGEdge{
			From:  key.from,
			To:    key.to,
			Count: n,
			AvgMs: sum / float64(n),
			P50Ms: latencies[p50Idx],
			P99Ms: latencies[p99Idx],
			MaxMs: latencies[n-1],
		})
	}

	sort.Slice(edges, func(i, j int) bool {
		return edges[i].Count > edges[j].Count
	})
	return edges
}

// ── Variant Analysis ──

// analyzeVariantsFromTraces groups traces by activity sequence pattern.
func analyzeVariantsFromTraces(traces []bunsekiTrace) []bunsekiVariant {
	patternCounts := map[string]*struct {
		activities []string
		count      int
		totalMs    float64
	}{}

	for _, trace := range traces {
		// Simplify: use first 8 activities max for pattern
		acts := trace.Activities
		if len(acts) > 8 {
			acts = acts[:8]
		}
		pattern := strings.Join(acts, " → ")
		if entry, ok := patternCounts[pattern]; ok {
			entry.count++
			for _, e := range trace.Events {
				entry.totalMs += e.Ms
			}
		} else {
			total := 0.0
			for _, e := range trace.Events {
				total += e.Ms
			}
			patternCounts[pattern] = &struct {
				activities []string
				count      int
				totalMs    float64
			}{activities: acts, count: 1, totalMs: total}
		}
	}

	total := len(traces)
	var variants []bunsekiVariant
	for pattern, data := range patternCounts {
		pct := 0.0
		if total > 0 {
			pct = float64(data.count) / float64(total) * 100
		}
		avgMs := 0.0
		if data.count > 0 {
			avgMs = data.totalMs / float64(data.count)
		}
		variants = append(variants, bunsekiVariant{
			Pattern:    pattern,
			Activities: data.activities,
			Count:      data.count,
			Percentage: pct,
			AvgMs:      avgMs,
		})
	}

	sort.Slice(variants, func(i, j int) bool {
		return variants[i].Count > variants[j].Count
	})
	return variants
}

// ── Conformance Checking ──

// checkConformanceFromTraces checks if traces conform to expected paths.
func checkConformanceFromTraces(traces []bunsekiTrace) []bunsekiConformanceResult {
	var results []bunsekiConformanceResult

	for name, expected := range expectedPaths {
		relevant := 0
		conformant := 0
		devMap := map[string]int{}

		for _, trace := range traces {
			// Check if trace is relevant (contains at least one activity from expected path)
			isRelevant := false
			for _, exp := range expected {
				for _, act := range trace.Activities {
					if act == exp {
						isRelevant = true
						break
					}
				}
				if isRelevant {
					break
				}
			}
			if !isRelevant {
				continue
			}
			relevant++

			// Subsequence match
			if isSubsequence(expected, trace.Activities) {
				conformant++
			} else {
				// Record deviation
				missing := findMissing(expected, trace.Activities)
				for _, m := range missing {
					devMap[m]++
				}
			}
		}

		if relevant == 0 {
			continue
		}

		rate := float64(conformant) / float64(relevant) * 100
		var deviations []string
		for dev, cnt := range devMap {
			deviations = append(deviations, fmt.Sprintf("%s missing in %d traces", dev, cnt))
		}
		sort.Strings(deviations)

		results = append(results, bunsekiConformanceResult{
			Name:         name,
			ExpectedPath: expected,
			TotalTraces:  relevant,
			ConformCount: conformant,
			ConformRate:  rate,
			Deviations:   deviations,
		})
	}

	sort.Slice(results, func(i, j int) bool {
		return results[i].ConformRate < results[j].ConformRate // worst first
	})
	return results
}

// isSubsequence checks if expected is a subsequence of actual.
func isSubsequence(expected, actual []string) bool {
	ei := 0
	for _, act := range actual {
		if ei < len(expected) && act == expected[ei] {
			ei++
		}
	}
	return ei == len(expected)
}

// findMissing returns expected activities not found in actual.
func findMissing(expected, actual []string) []string {
	actSet := map[string]bool{}
	for _, a := range actual {
		actSet[a] = true
	}
	var missing []string
	for _, e := range expected {
		if !actSet[e] {
			missing = append(missing, e)
		}
	}
	return missing
}

// ── Performance Analysis ──

// analyzePerformanceFromTraces computes per-transition latency metrics.
func analyzePerformanceFromTraces(traces []bunsekiTrace) []bunsekiPerfTransition {
	type edgeKey struct{ from, to string }
	data := map[edgeKey][]float64{}

	for _, trace := range traces {
		for i := 0; i < len(trace.Events)-1; i++ {
			key := edgeKey{trace.Events[i].Activity, trace.Events[i+1].Activity}
			data[key] = append(data[key], trace.Events[i+1].Ms)
		}
	}

	var results []bunsekiPerfTransition
	for key, latencies := range data {
		if len(latencies) < 3 {
			continue // need enough samples
		}
		sort.Float64s(latencies)
		n := len(latencies)
		sum := 0.0
		for _, l := range latencies {
			sum += l
		}
		p50 := latencies[n/2]
		p99Idx := int(math.Ceil(float64(n)*0.99)) - 1
		if p99Idx >= n {
			p99Idx = n - 1
		}
		if p99Idx < 0 {
			p99Idx = 0
		}
		p99 := latencies[p99Idx]
		maxMs := latencies[n-1]

		target := getTargetMs(key.to)
		severity := ""
		if p99 > target*3 {
			severity = "critical"
		} else if p99 > target*1.5 {
			severity = "high"
		} else if p99 > target {
			severity = "medium"
		}

		results = append(results, bunsekiPerfTransition{
			From:     key.from,
			To:       key.to,
			Count:    n,
			AvgMs:    sum / float64(n),
			P50Ms:    p50,
			P99Ms:    p99,
			MaxMs:    maxMs,
			TargetMs: target,
			Severity: severity,
		})
	}

	// Sort: critical first, then by p99 descending
	sort.Slice(results, func(i, j int) bool {
		sevOrder := map[string]int{"critical": 0, "high": 1, "medium": 2, "": 3}
		si, sj := sevOrder[results[i].Severity], sevOrder[results[j].Severity]
		if si != sj {
			return si < sj
		}
		return results[i].P99Ms > results[j].P99Ms
	})
	return results
}

// ── Cross-Reference (Runtime + Static) ──

// crossReferenceStatic matches runtime performance bottlenecks to static code analysis results.
func crossReferenceStatic(perfResults []bunsekiPerfTransition, wsRoot string) []bunsekiRecommendation {
	var recommendations []bunsekiRecommendation
	priority := 0

	// Get static bottlenecks
	handlerDir := filepath.Join(wsRoot, "packages", "server", "wproto", "src")
	handlerFiles := []string{
		"pds-handlers-feed.ts",
		"pds-handlers-repo.ts",
		"pds-handlers-infra.ts",
		"pds-handlers-gftd.ts",
	}

	var staticBottlenecks []pmBottleneck
	for _, fname := range handlerFiles {
		fpath := filepath.Join(handlerDir, fname)
		data, err := os.ReadFile(fpath)
		if err != nil {
			continue
		}
		analyses := analyzeHandlerFile(pmHandlerSource{Path: fpath}, string(data))
		for _, a := range analyses {
			staticBottlenecks = append(staticBottlenecks, a.Bottlenecks...)
		}
	}

	// Match runtime bottlenecks to static issues
	for _, perf := range perfResults {
		if perf.Severity == "" {
			continue
		}

		priority++
		rec := bunsekiRecommendation{
			Priority: priority,
			Severity: perf.Severity,
			Category: "performance",
			Description: fmt.Sprintf("%s → %s transition p99=%.0fms (target: %.0fms, %d samples)",
				perf.From, perf.To, perf.P99Ms, perf.TargetMs, perf.Count),
			Impact: fmt.Sprintf("Affects %d transitions, avg=%.0fms", perf.Count, perf.AvgMs),
		}

		// Try to match with static analysis
		for _, sb := range staticBottlenecks {
			nsid := sb.NSID
			activity := methodToActivity(sb.Handler)
			if activity == perf.To || strings.Contains(nsid, activityToMethodFragment(perf.To)) {
				rec.StaticRef = fmt.Sprintf("[%s] %s (%s:%d)", sb.Severity, sb.Message, sb.File, sb.Line)
				rec.Fix = sb.Fix
				break
			}
		}

		if rec.Fix == "" {
			rec.Fix = fmt.Sprintf("Investigate %s handler — p99 %.0fms exceeds %.0fms target", perf.To, perf.P99Ms, perf.TargetMs)
		}

		recommendations = append(recommendations, rec)

		if priority >= 10 {
			break
		}
	}

	// Add conformance-based recommendations would come from the caller
	return recommendations
}

// activityToMethodFragment converts an activity back to a method name fragment for matching.
func activityToMethodFragment(activity string) string {
	parts := strings.SplitN(activity, ":", 2)
	if len(parts) != 2 {
		return activity
	}
	switch parts[0] {
	case "feed":
		return "Feed"
	case "profile":
		return "Actor"
	case "record":
		return "Repo"
	case "auth":
		return "Server"
	case "graph":
		return "Graph"
	case "convo":
		return "Convo"
	case "notification":
		return "Notification"
	default:
		return parts[1]
	}
}

// ── Scoring ──

// computeBunsekiScoreFromData calculates the overall process health score.
func computeBunsekiScoreFromData(
	dfg []bunsekiDFGEdge,
	variants []bunsekiVariant,
	conformance []bunsekiConformanceResult,
	performance []bunsekiPerfTransition,
	totalEvents int,
) bunsekiScore {
	// DFG efficiency: fewer unique transitions relative to events = simpler = better
	dfgScore := 100.0
	if totalEvents > 0 && len(dfg) > 0 {
		ratio := float64(len(dfg)) / float64(totalEvents)
		dfgScore = math.Max(0, 100-ratio*1000) // penalize high transition diversity
	}

	// Variant concentration: top-3 variants covering >80% = predictable = good
	variantScore := 0.0
	if len(variants) > 0 {
		top3Pct := 0.0
		for i := 0; i < len(variants) && i < 3; i++ {
			top3Pct += variants[i].Percentage
		}
		variantScore = top3Pct // 0-100
		if variantScore > 100 {
			variantScore = 100
		}
	}

	// Conformance rate: average across all checked paths
	conformScore := 100.0
	if len(conformance) > 0 {
		sum := 0.0
		for _, c := range conformance {
			sum += c.ConformRate
		}
		conformScore = sum / float64(len(conformance))
	}

	// Performance: percentage of transitions within SLA
	perfScore := 100.0
	if len(performance) > 0 {
		withinSLA := 0
		for _, p := range performance {
			if p.Severity == "" {
				withinSLA++
			}
		}
		perfScore = float64(withinSLA) / float64(len(performance)) * 100
	}

	overall := dfgScore*0.25 + variantScore*0.25 + conformScore*0.25 + perfScore*0.25
	grade := bunsekiGrade(overall)

	return bunsekiScore{
		DFGEfficiency:        dfgScore,
		VariantConcentration: variantScore,
		ConformanceRate:      conformScore,
		PerformanceScore:     perfScore,
		Overall:              overall,
		Grade:                grade,
	}
}

func bunsekiGrade(score float64) string {
	switch {
	case score >= 90:
		return "S"
	case score >= 80:
		return "A"
	case score >= 70:
		return "B"
	case score >= 50:
		return "C"
	case score >= 30:
		return "D"
	default:
		return "F"
	}
}

// ── Subcommand Implementations ──

func runBunsekiScan(args []string) error {
	f, err := parseBunsekiFlags("scan", args)
	if err != nil {
		return nil
	}

	events, err := fetchBunsekiEvents(f.minutes, f.limit)
	if err != nil {
		return err
	}
	if len(events) == 0 {
		fmt.Println("No OCEL v2 events found in the specified time window.")
		return nil
	}

	traces := buildTraces(events, f.objectType)
	dfg := buildDFG(traces)
	variants := analyzeVariantsFromTraces(traces)
	conformance := checkConformanceFromTraces(traces)
	performance := analyzePerformanceFromTraces(traces)
	recommendations := crossReferenceStatic(performance, f.workspaceDir)
	score := computeBunsekiScoreFromData(dfg, variants, conformance, performance, len(events))

	// Truncate to --top
	if len(dfg) > f.top {
		dfg = dfg[:f.top]
	}
	if len(variants) > f.top {
		variants = variants[:f.top]
	}

	report := bunsekiReport{
		AnalyzedAt:      time.Now().UTC().Format(time.RFC3339),
		LookbackMinutes: f.minutes,
		LookbackHours:   f.minutes / 60,
		TotalEvents:     len(events),
		TotalTraces:     len(traces),
		DFG:             dfg,
		Variants:        variants,
		Conformance:     conformance,
		Performance:     performance,
		Recommendations: recommendations,
		Score:           score,
	}

	if f.jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(report)
	}

	printBunsekiReport(&report)
	return nil
}

func runBunsekiDFG(args []string) error {
	f, err := parseBunsekiFlags("dfg", args)
	if err != nil {
		return nil
	}

	events, err := fetchBunsekiEvents(f.minutes, f.limit)
	if err != nil {
		return err
	}

	traces := buildTraces(events, f.objectType)
	dfg := buildDFG(traces)
	if len(dfg) > f.top {
		dfg = dfg[:f.top]
	}

	if f.jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(dfg)
	}

	printDFGTable(dfg)
	return nil
}

func runBunsekiVariants(args []string) error {
	f, err := parseBunsekiFlags("variants", args)
	if err != nil {
		return nil
	}

	events, err := fetchBunsekiEvents(f.minutes, f.limit)
	if err != nil {
		return err
	}

	traces := buildTraces(events, f.objectType)
	variants := analyzeVariantsFromTraces(traces)
	if len(variants) > f.top {
		variants = variants[:f.top]
	}

	if f.jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(variants)
	}

	printVariantsTable(variants)
	return nil
}

func runBunsekiConformance(args []string) error {
	f, err := parseBunsekiFlags("conformance", args)
	if err != nil {
		return nil
	}

	events, err := fetchBunsekiEvents(f.minutes, f.limit)
	if err != nil {
		return err
	}

	traces := buildTraces(events, f.objectType)
	conformance := checkConformanceFromTraces(traces)

	if f.jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(conformance)
	}

	printConformanceTable(conformance)
	return nil
}

func runBunsekiPerformance(args []string) error {
	f, err := parseBunsekiFlags("performance", args)
	if err != nil {
		return nil
	}

	events, err := fetchBunsekiEvents(f.minutes, f.limit)
	if err != nil {
		return err
	}

	traces := buildTraces(events, f.objectType)
	performance := analyzePerformanceFromTraces(traces)

	if f.jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(performance)
	}

	printPerformanceTable(performance, f.top)
	return nil
}

func runBunsekiRecommendations(args []string) error {
	f, err := parseBunsekiFlags("recommendations", args)
	if err != nil {
		return nil
	}

	events, err := fetchBunsekiEvents(f.minutes, f.limit)
	if err != nil {
		return err
	}

	traces := buildTraces(events, f.objectType)
	performance := analyzePerformanceFromTraces(traces)
	recommendations := crossReferenceStatic(performance, f.workspaceDir)

	if f.jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(recommendations)
	}

	printRecommendations(recommendations)
	return nil
}

// ── Output Formatting ──

func printBunsekiReport(r *bunsekiReport) {
	fmt.Println()
	fmt.Println("╔══════════════════════════════════════════════════════════════════════════════════╗")
	fmt.Println("║                    GFTD Bunseki — Process Mining Analysis                       ║")
	fmt.Printf("║                    %s                                     ║\n", time.Now().Format("2006-01-02 15:04:05"))
	fmt.Println("╠══════════════════════════════════════════════════════════════════════════════════╣")
	fmt.Printf("  Events: %d | Traces: %d | Lookback: %dm\n\n", r.TotalEvents, r.TotalTraces, r.LookbackMinutes)

	// DFG
	if len(r.DFG) > 0 {
		printDFGTable(r.DFG)
		fmt.Println()
	}

	// Variants
	if len(r.Variants) > 0 {
		printVariantsTable(r.Variants)
		fmt.Println()
	}

	// Performance Bottlenecks
	bottleneckCount := 0
	for _, p := range r.Performance {
		if p.Severity != "" {
			bottleneckCount++
		}
	}
	if bottleneckCount > 0 {
		fmt.Println("  Performance Bottlenecks:")
		for _, p := range r.Performance {
			if p.Severity == "" {
				continue
			}
			sev := strings.ToUpper(p.Severity)
			fmt.Printf("    [%s] %-25s → %-25s p99=%.0fms (target: %.0fms)\n",
				sev, p.From, p.To, p.P99Ms, p.TargetMs)
		}
		fmt.Println()
	}

	// Conformance
	if len(r.Conformance) > 0 {
		printConformanceTable(r.Conformance)
		fmt.Println()
	}

	// Recommendations
	if len(r.Recommendations) > 0 {
		printRecommendations(r.Recommendations)
		fmt.Println()
	}

	// Score
	fmt.Printf("  Score: %.0f (%s)\n", r.Score.Overall, r.Score.Grade)
	fmt.Printf("    DFG Efficiency:        %.0f\n", r.Score.DFGEfficiency)
	fmt.Printf("    Variant Concentration: %.0f\n", r.Score.VariantConcentration)
	fmt.Printf("    Conformance Rate:      %.0f\n", r.Score.ConformanceRate)
	fmt.Printf("    Performance Score:     %.0f\n", r.Score.PerformanceScore)
	fmt.Println()
	fmt.Println("╚══════════════════════════════════════════════════════════════════════════════════╝")
}

func printDFGTable(dfg []bunsekiDFGEdge) {
	fmt.Println("  DFG (Directly-Follows Graph):")
	fmt.Println("  ┌──────────────────────────┬──────────────────────────┬───────┬────────┬────────┬────────┐")
	fmt.Println("  │ From                     │ To                       │ Count │ Avg ms │ p99 ms │ Max ms │")
	fmt.Println("  ├──────────────────────────┼──────────────────────────┼───────┼────────┼────────┼────────┤")
	for _, e := range dfg {
		from := e.From
		if len(from) > 24 {
			from = from[:24]
		}
		to := e.To
		if len(to) > 24 {
			to = to[:24]
		}
		fmt.Printf("  │ %-24s │ %-24s │ %5d │ %4.0fms │ %4.0fms │ %4.0fms │\n",
			from, to, e.Count, e.AvgMs, e.P99Ms, e.MaxMs)
	}
	fmt.Println("  └──────────────────────────┴──────────────────────────┴───────┴────────┴────────┴────────┘")
}

func printVariantsTable(variants []bunsekiVariant) {
	fmt.Println("  Variants (trace patterns):")
	fmt.Println("  ┌───┬──────────────────────────────────────────────────────────────┬───────┬───────┬────────┐")
	fmt.Println("  │ # │ Trace Pattern                                               │ Count │    %  │ Avg ms │")
	fmt.Println("  ├───┼──────────────────────────────────────────────────────────────┼───────┼───────┼────────┤")
	for i, v := range variants {
		pattern := v.Pattern
		if len(pattern) > 60 {
			pattern = pattern[:57] + "..."
		}
		fmt.Printf("  │%2d │ %-60s │ %5d │ %4.1f%% │ %4.0fms │\n",
			i+1, pattern, v.Count, v.Percentage, v.AvgMs)
	}
	fmt.Println("  └───┴──────────────────────────────────────────────────────────────┴───────┴───────┴────────┘")
}

func printConformanceTable(conformance []bunsekiConformanceResult) {
	fmt.Println("  Conformance:")
	for _, c := range conformance {
		status := "OK"
		if c.ConformRate < 90 {
			status = "GAP"
		}
		fmt.Printf("    [%s] %-20s %.1f%% conformant (%d/%d traces)\n",
			status, c.Name, c.ConformRate, c.ConformCount, c.TotalTraces)
		for _, d := range c.Deviations {
			fmt.Printf("         deviation: %s\n", d)
		}
	}
}

func printPerformanceTable(perf []bunsekiPerfTransition, top int) {
	fmt.Println("  Performance (transition latency):")
	fmt.Println("  ┌──────────────────────────┬──────────────────────────┬───────┬────────┬────────┬────────┬────────┬──────────┐")
	fmt.Println("  │ From                     │ To                       │ Count │ p50 ms │ p99 ms │ Max ms │ Target │ Severity │")
	fmt.Println("  ├──────────────────────────┼──────────────────────────┼───────┼────────┼────────┼────────┼────────┼──────────┤")
	shown := 0
	for _, p := range perf {
		if shown >= top {
			break
		}
		from := p.From
		if len(from) > 24 {
			from = from[:24]
		}
		to := p.To
		if len(to) > 24 {
			to = to[:24]
		}
		sev := p.Severity
		if sev == "" {
			sev = "ok"
		}
		fmt.Printf("  │ %-24s │ %-24s │ %5d │ %4.0fms │ %4.0fms │ %4.0fms │ %4.0fms │ %-8s │\n",
			from, to, p.Count, p.P50Ms, p.P99Ms, p.MaxMs, p.TargetMs, sev)
		shown++
	}
	fmt.Println("  └──────────────────────────┴──────────────────────────┴───────┴────────┴────────┴────────┴────────┴──────────┘")
}

func printRecommendations(recs []bunsekiRecommendation) {
	fmt.Println("  Recommendations:")
	for _, r := range recs {
		sev := strings.ToUpper(r.Severity)
		fmt.Printf("    %d. [%s] %s\n", r.Priority, sev, r.Description)
		if r.StaticRef != "" {
			fmt.Printf("       Static: %s\n", r.StaticRef)
		}
		fmt.Printf("       Fix: %s\n", r.Fix)
		fmt.Printf("       Impact: %s\n", r.Impact)
	}
}
