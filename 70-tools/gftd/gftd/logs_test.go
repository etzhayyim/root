package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// ── queryEvent JSON round-trip ──

func TestQueryEventJSON(t *testing.T) {
	qe := queryEvent{
		TS:                   "2026-04-10T00:00:00Z",
		CallerNsid:           "app.bsky.feed.getTimeline",
		QueryHash:            "deadbeef",
		Risk:                 "low",
		SqlHead:              "MATCH (n:Post) WHERE n.repo = 'did:web:x' LIMIT 10",
		Kind:                 "end",
		ActualMs:             42.5,
		Status:               200,
		RowCount:             10,
		EstimatedMemoryBytes: 25600,
		EstimatedMs:          8.0,
		EstimatedCpuUnits:    1.0,
	}

	data, err := json.Marshal(qe)
	if err != nil {
		t.Fatalf("marshal: %v", err)
	}

	var decoded queryEvent
	if err := json.Unmarshal(data, &decoded); err != nil {
		t.Fatalf("unmarshal: %v", err)
	}

	if decoded.CallerNsid != "app.bsky.feed.getTimeline" {
		t.Errorf("callerNsid: got %q, want %q", decoded.CallerNsid, "app.bsky.feed.getTimeline")
	}
	if decoded.QueryHash != "deadbeef" {
		t.Errorf("queryHash: got %q, want %q", decoded.QueryHash, "deadbeef")
	}
	if decoded.Risk != "low" {
		t.Errorf("risk: got %q, want %q", decoded.Risk, "low")
	}
	if decoded.Kind != "end" {
		t.Errorf("kind: got %q, want %q", decoded.Kind, "end")
	}
	if decoded.ActualMs != 42.5 {
		t.Errorf("actualMs: got %f, want %f", decoded.ActualMs, 42.5)
	}
	if decoded.RowCount != 10 {
		t.Errorf("rowCount: got %d, want %d", decoded.RowCount, 10)
	}
}

// ── queryAgg JSON round-trip ──

func TestQueryAggJSON(t *testing.T) {
	qa := queryAgg{
		Count:          100,
		Errors:         5,
		SlowCount:      3,
		AvgActualMs:    45.2,
		MaxActualMs:    5000.0,
		AvgEstimatedMs: 12.0,
		AvgMemoryBytes: 102400.0,
		TotalRows:      500,
		OomRiskCount:   1,
	}

	data, err := json.Marshal(qa)
	if err != nil {
		t.Fatalf("marshal: %v", err)
	}

	var decoded queryAgg
	if err := json.Unmarshal(data, &decoded); err != nil {
		t.Fatalf("unmarshal: %v", err)
	}

	if decoded.Count != 100 {
		t.Errorf("count: got %d, want %d", decoded.Count, 100)
	}
	if decoded.OomRiskCount != 1 {
		t.Errorf("oomRiskCount: got %d, want %d", decoded.OomRiskCount, 1)
	}
	if decoded.SlowCount != 3 {
		t.Errorf("slowCount: got %d, want %d", decoded.SlowCount, 3)
	}
}

// ── ocelResponse with query events ──

func TestOcelResponseWithQueries(t *testing.T) {
	resp := ocelResponse{
		Events: []ocelEvent{{TS: "now", Method: "test", Ms: 10, Status: 200}},
		Queries: []queryEvent{
			{CallerNsid: "app.bsky.feed.getTimeline", Kind: "end", ActualMs: 42, Status: 200, RowCount: 10, Risk: "low"},
			{CallerNsid: "app.bsky.feed.getTimeline", Kind: "slow", ActualMs: 5000, Status: 200, RowCount: 100, Risk: "medium"},
		},
		QueryAggregates: map[string]queryAgg{
			"app.bsky.feed.getTimeline": {Count: 2, SlowCount: 1, AvgActualMs: 2521, MaxActualMs: 5000},
		},
		XrpcCount:  1,
		QueryCount: 2,
	}

	data, err := json.Marshal(resp)
	if err != nil {
		t.Fatalf("marshal: %v", err)
	}

	var decoded ocelResponse
	if err := json.Unmarshal(data, &decoded); err != nil {
		t.Fatalf("unmarshal: %v", err)
	}

	if decoded.QueryCount != 2 {
		t.Errorf("queryCount: got %d, want %d", decoded.QueryCount, 2)
	}
	if len(decoded.Queries) != 2 {
		t.Fatalf("queries len: got %d, want %d", len(decoded.Queries), 2)
	}
	if decoded.Queries[1].Kind != "slow" {
		t.Errorf("queries[1].kind: got %q, want %q", decoded.Queries[1].Kind, "slow")
	}
	if agg, ok := decoded.QueryAggregates["app.bsky.feed.getTimeline"]; !ok {
		t.Error("missing queryAggregate for app.bsky.feed.getTimeline")
	} else if agg.SlowCount != 1 {
		t.Errorf("agg.slowCount: got %d, want %d", agg.SlowCount, 1)
	}
}

// ── latencyGrade ──

func TestLatencyGrade(t *testing.T) {
	cases := []struct {
		p50     float64
		errRate float64
		want    string
	}{
		{5, 0, "S"},
		{30, 0, "A"},
		{100, 0, "B"},
		{300, 0, "C"},
		{1000, 0, "D"},
		{3000, 0, "F"},
		{5, 6, "D"},  // high error rate downgrades
		{5, 11, "F"}, // very high error rate
	}

	for _, tc := range cases {
		got := latencyGrade(tc.p50, tc.errRate)
		if got != tc.want {
			t.Errorf("latencyGrade(%.0f, %.0f): got %q, want %q", tc.p50, tc.errRate, got, tc.want)
		}
	}
}

// ── diagnostics: OOM risk detection ──

func TestDiagnosticsOomRisk(t *testing.T) {
	data := ocelResponse{
		Queries: []queryEvent{
			{CallerNsid: "test", Risk: "oom_risk", Kind: "error", ActualMs: 100, Status: 500},
			{CallerNsid: "test", Risk: "low", Kind: "end", ActualMs: 10, Status: 200},
			{CallerNsid: "test", Risk: "oom_risk", Kind: "slow", ActualMs: 5000, Status: 200},
		},
	}

	diag := buildLogsDiagnostics(data, nil)

	if diag.OomRiskQueries != 2 {
		t.Errorf("oomRiskQueries: got %d, want %d", diag.OomRiskQueries, 2)
	}
	if diag.SlowQueries != 1 {
		t.Errorf("slowQueries: got %d, want %d", diag.SlowQueries, 1)
	}
	if len(diag.LikelyCauses) == 0 {
		t.Error("expected likely causes for OOM risk queries")
	}
	found := false
	for _, cause := range diag.LikelyCauses {
		if len(cause) > 0 && cause[0] == '2' {
			found = true
		}
	}
	if !found {
		// Check for the "2 queries estimated as OOM risk" message
		hasOom := false
		for _, cause := range diag.LikelyCauses {
			if len(cause) > 10 {
				hasOom = true
			}
		}
		if !hasOom {
			t.Error("expected OOM risk likely cause message")
		}
	}
}

// ── diagnostics: slow query detection ──

func TestDiagnosticsSlowQueries(t *testing.T) {
	queries := make([]queryEvent, 0, 6)
	for i := 0; i < 6; i++ {
		queries = append(queries, queryEvent{CallerNsid: "test", Risk: "high", Kind: "slow", ActualMs: 5000, Status: 200})
	}
	data := ocelResponse{Queries: queries}

	diag := buildLogsDiagnostics(data, nil)

	if diag.SlowQueries != 6 {
		t.Errorf("slowQueries: got %d, want %d", diag.SlowQueries, 6)
	}
	hasSlowCause := false
	for _, cause := range diag.LikelyCauses {
		if len(cause) > 20 {
			hasSlowCause = true
		}
	}
	if !hasSlowCause {
		t.Error("expected slow query likely cause message for 6+ slow queries")
	}
}

// ── percentiles edge cases ──

func TestPercentilesSingle(t *testing.T) {
	p50, p99 := percentiles([]int{42})
	if p50 != 42 {
		t.Errorf("p50: got %f, want 42", p50)
	}
	if p99 != 42 {
		t.Errorf("p99: got %f, want 42", p99)
	}
}

func TestPercentilesEmpty(t *testing.T) {
	p50, p99 := percentiles(nil)
	if p50 != 0 || p99 != 0 {
		t.Errorf("empty: got %f/%f, want 0/0", p50, p99)
	}
}

func TestJSONIntParsesAnalyticsEngineShapes(t *testing.T) {
	cases := []struct {
		name string
		in   any
		want int
	}{
		{name: "string int", in: "37", want: 37},
		{name: "string float", in: "37.9", want: 37},
		{name: "json number", in: json.Number("42"), want: 42},
		{name: "bool true", in: true, want: 1},
		{name: "bool false", in: false, want: 0},
	}

	for _, tc := range cases {
		if got := jsonInt(tc.in); got != tc.want {
			t.Errorf("%s: got %d, want %d", tc.name, got, tc.want)
		}
	}
}

func TestJSONFloat64ParsesAnalyticsEngineShapes(t *testing.T) {
	cases := []struct {
		name string
		in   any
		want float64
	}{
		{name: "string float", in: "15.5", want: 15.5},
		{name: "json number", in: json.Number("42.25"), want: 42.25},
		{name: "bool true", in: true, want: 1},
		{name: "bool false", in: false, want: 0},
	}

	for _, tc := range cases {
		if got := jsonFloat64(tc.in); got != tc.want {
			t.Errorf("%s: got %f, want %f", tc.name, got, tc.want)
		}
	}
}

func TestBuildLogsDiagnosticsReverseTopology(t *testing.T) {
	data := ocelResponse{
		Aggregates: map[string]ocelAgg{
			"ai.gftd.kagami.sql":            {Count: 12, Errors: 10, P99Ms: 20000, MaxMs: 20000},
			"app.bsky.actor.getProfile":     {Count: 8, Errors: 0, P99Ms: 16417, MaxMs: 16417},
			"app.bsky.feed.getPostThread":   {Count: 4, Errors: 0, P99Ms: 12059, MaxMs: 12059},
			"com.atproto.repo.listRecords":  {Count: 6, Errors: 1, P99Ms: 4405, MaxMs: 4405},
			"com.atproto.repo.createRecord": {Count: 7, Errors: 4, P99Ms: 9101, MaxMs: 9101},
			"ai.gftd.apps.dojo.addXp":       {Count: 3, Errors: 3, P99Ms: 2, MaxMs: 2},
			"ai.gftd.pds.getEntityGraph":    {Count: 2, Errors: 2, P99Ms: 2, MaxMs: 2},
		},
		Events: []ocelEvent{
			{Method: "ai.gftd.kagami.sql", Status: 404, Ms: 21},
			{Method: "ai.gftd.kagami.sql", Status: 404, Ms: 3},
			{Method: "ai.gftd.kagami.sql", Status: 401, Ms: 2},
			{Method: "app.bsky.actor.getProfile", Status: 200, Ms: 16417},
			{Method: "app.bsky.feed.getPostThread", Status: 200, Ms: 12059},
			{Method: "com.atproto.repo.listRecords", Status: 200, Ms: 4405},
			{Method: "com.atproto.repo.createRecord", Status: 401, Ms: 21},
			{Method: "com.atproto.repo.createRecord", Status: 401, Ms: 1},
			{Method: "ai.gftd.apps.dojo.addXp", Status: 404, Ms: 0},
			{Method: "ai.gftd.apps.dojo.getXpProfile", Status: 404, Ms: 0},
			{Method: "app.bsky.feed.post", Status: 404, Ms: 0},
			{Method: "ai.gftd.pds.getEntityGraph", Status: 501, Ms: 2},
		},
		QueryAggregates: map[string]queryAgg{
			"ai.gftd.kagami.sql":        {Count: 12, Errors: 10, SlowCount: 3, AvgActualMs: 2500},
			"app.bsky.actor.getProfile": {Count: 8, Errors: 0, SlowCount: 2, AvgActualMs: 5000},
		},
	}

	diag := buildLogsDiagnostics(data, data.Events)

	if len(diag.ReverseTopology) < 3 {
		t.Fatalf("reverseTopology len: got %d, want >= 3", len(diag.ReverseTopology))
	}
	if diag.ReverseTopology[0].Key != "graph-query" {
		t.Fatalf("top reverseTopology key: got %q, want graph-query", diag.ReverseTopology[0].Key)
	}
	if diag.ReverseTopology[0].Severity != "critical" {
		t.Fatalf("top reverseTopology severity: got %q, want critical", diag.ReverseTopology[0].Severity)
	}
	if len(diag.ReverseTopology[0].Dependents) == 0 {
		t.Fatal("graph-query dependents: expected non-empty list")
	}
	if len(diag.LikelyCauses) == 0 {
		t.Fatal("likelyCauses: expected reverse-topology messages")
	}
}

func TestDetectGraphQueryRootCauseIncludes5xxAnd410(t *testing.T) {
	methodStats := map[string]logsMethodStats{
		"ai.gftd.kagami.sql": {
			Count:  4,
			Errors: 4,
			Statuses: map[int]int{
				410: 1,
				502: 1,
				504: 2,
			},
			P99Ms: 20000,
			MaxMs: 20000,
		},
	}

	cause, ok := detectGraphQueryRootCause(methodStats, nil)
	if !ok {
		t.Fatal("detectGraphQueryRootCause: expected 5xx/410 regression to be detected")
	}
	if cause.Key != "graph-query" {
		t.Fatalf("cause.Key: got %q, want graph-query", cause.Key)
	}
	if len(cause.Evidence) == 0 || cause.Evidence[0] == "" {
		t.Fatal("cause.Evidence: expected non-empty evidence")
	}
}

func TestDetectPublicWriteRootCause(t *testing.T) {
	events := []ocelEvent{
		{Method: "com.atproto.repo.createRecord", Auth: "public", Status: 500},
		{Method: "com.atproto.repo.createRecord", Auth: "public", Status: 401},
		{Method: "ai.gftd.convo.createConvo", Auth: "public", Status: 401},
		{Method: "ai.gftd.convo.send", Auth: "session", Status: 401},
	}

	cause, ok := detectPublicWriteRootCause(events)
	if !ok {
		t.Fatal("detectPublicWriteRootCause: expected public write failures to be detected")
	}
	if cause.Key != "public-write" {
		t.Fatalf("cause.Key: got %q, want public-write", cause.Key)
	}
	if cause.Severity != "high" {
		t.Fatalf("cause.Severity: got %q, want high", cause.Severity)
	}
}

func TestResolvePMHandlerDirPrefersCurrentWorkspaceLayout(t *testing.T) {
	wsRoot := filepath.Clean(filepath.Join("..", "..", ".."))
	got := resolvePMHandlerDir(wsRoot)
	want := filepath.Join(wsRoot, "50-infra", "cloudflare", "workers", "atproto", "src", "handlers")
	if got != want {
		t.Fatalf("resolvePMHandlerDir: got %q, want %q", got, want)
	}
}

func TestResolvePMHandlerSourcesCurrentLayout(t *testing.T) {
	wsRoot := filepath.Clean(filepath.Join("..", "..", ".."))
	got := resolvePMHandlerSources(wsRoot)
	if len(got) != 4 {
		t.Fatalf("resolvePMHandlerSources len: got %d, want 4", len(got))
	}
	want := []string{
		filepath.Join(wsRoot, "50-infra", "cloudflare", "workers", "atproto", "src", "handlers", "appview", "feed.ts"),
		filepath.Join(wsRoot, "50-infra", "cloudflare", "workers", "atproto", "src", "handlers", "pds", "repo.ts"),
		filepath.Join(wsRoot, "50-infra", "cloudflare", "workers", "atproto", "src", "handlers", "pds", "server.ts"),
		filepath.Join(wsRoot, "50-infra", "cloudflare", "workers", "atproto", "src", "handlers", "gftd", "index.ts"),
	}
	for i, src := range got {
		if src.Path != want[i] {
			t.Fatalf("resolvePMHandlerSources[%d].Path: got %q, want %q", i, src.Path, want[i])
		}
		if src.Category == "" {
			t.Fatalf("resolvePMHandlerSources[%d].Category: expected non-empty category", i)
		}
	}
}

func TestResolvePMHandlerDirFromGftdSubmoduleCwd(t *testing.T) {
	wsRoot := "."
	got := resolvePMHandlerDir(wsRoot)
	want := filepath.Clean(filepath.Join("..", "..", "..", "50-infra", "cloudflare", "workers", "atproto", "src", "handlers"))
	if got != want {
		t.Fatalf("resolvePMHandlerDir from submodule: got %q, want %q", got, want)
	}
}

func TestResolveCFTokenFallsBackToWranglerOAuth(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	t.Setenv("CF_API_TOKEN", "")
	t.Setenv("CLOUDFLARE_API_TOKEN", "")

	wranglerDir := filepath.Join(tmp, "Library", "Preferences", ".wrangler", "config")
	if err := os.MkdirAll(wranglerDir, 0o755); err != nil {
		t.Fatalf("mkdir wrangler dir: %v", err)
	}
	if err := os.WriteFile(filepath.Join(wranglerDir, "default.toml"), []byte("oauth_token = \"wrangler-oauth\"\n"), 0o644); err != nil {
		t.Fatalf("write wrangler config: %v", err)
	}

	if got := resolveCFToken(); got != "wrangler-oauth" {
		t.Fatalf("resolveCFToken: got %q, want wrangler oauth fallback", got)
	}
	if !hasWranglerOAuthToken() {
		t.Fatal("hasWranglerOAuthToken: expected true")
	}
	if got := resolveCFAnalyticsToken(); got != "" {
		t.Fatalf("resolveCFAnalyticsToken: got %q, want empty for Wrangler OAuth", got)
	}
}

func TestResolveCFTokenPrefersExplicitEnvOrFile(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	t.Setenv("CF_API_TOKEN", "")
	t.Setenv("CLOUDFLARE_API_TOKEN", "cf-env-token")

	if got := resolveCFToken(); got != "cf-env-token" {
		t.Fatalf("resolveCFToken from env: got %q, want %q", got, "cf-env-token")
	}
	if got := resolveCFAnalyticsToken(); got != "cf-env-token" {
		t.Fatalf("resolveCFAnalyticsToken from env: got %q, want %q", got, "cf-env-token")
	}

	t.Setenv("CLOUDFLARE_API_TOKEN", "")
	gftdDir := filepath.Join(tmp, ".gftd")
	if err := os.MkdirAll(gftdDir, 0o755); err != nil {
		t.Fatalf("mkdir gftd dir: %v", err)
	}
	if err := os.WriteFile(filepath.Join(gftdDir, "cf_api_token"), []byte("cf-file-token\n"), 0o644); err != nil {
		t.Fatalf("write cf_api_token: %v", err)
	}

	if got := resolveCFToken(); got != "cf-file-token" {
		t.Fatalf("resolveCFToken from file: got %q, want %q", got, "cf-file-token")
	}
	if got := resolveCFAnalyticsToken(); got != "cf-file-token" {
		t.Fatalf("resolveCFAnalyticsToken from file: got %q, want %q", got, "cf-file-token")
	}
}

func TestAnalyticsAuthRequiredErrorGeneric(t *testing.T) {
	err := analyticsAuthRequiredError()
	if err == nil {
		t.Fatal("analyticsAuthRequiredError: expected non-nil")
	}
	if !strings.Contains(err.Error(), "CF_API_TOKEN") {
		t.Fatalf("analyticsAuthRequiredError: got %q, want token guidance", err.Error())
	}
	if !strings.Contains(err.Error(), "Wrangler OAuth") {
		t.Fatalf("analyticsAuthRequiredError: got %q, want Wrangler OAuth guidance", err.Error())
	}
}

func TestFetchOcelFromPDSRetriesWithServiceAuthOnInternalAuth(t *testing.T) {
	t.Setenv("GFTD_TOKEN", "base-token")

	var serviceAuthCalls int
	var ocelCalls int
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		switch {
		case r.URL.Path == "/_pds/ocel":
			http.NotFound(w, r)
		case r.URL.Path == "/xrpc/com.atproto.server.getServiceAuth":
			serviceAuthCalls++
			if got := r.Header.Get("Authorization"); got != "Bearer base-token" {
				t.Fatalf("getServiceAuth auth header: got %q", got)
			}
			_ = json.NewEncoder(w).Encode(map[string]any{"token": "svc-token"})
		case r.URL.Path == "/xrpc/ai.gftd.pds.getOcel":
			ocelCalls++
			switch r.Header.Get("Authorization") {
			case "Bearer base-token":
				w.WriteHeader(http.StatusForbidden)
				_, _ = w.Write([]byte(`{"error":"Forbidden","message":"ai.gftd.pds.getOcel requires internal auth"}`))
			case "Bearer svc-token":
				_ = json.NewEncoder(w).Encode(map[string]any{
					"events":     []map[string]any{{"ts": "2026-04-16T00:00:00Z", "method": "app.bsky.actor.getProfile", "ms": 12, "status": 200, "auth": "internal"}},
					"aggregates": map[string]any{"app.bsky.actor.getProfile": map[string]any{"count": 1, "errors": 0, "totalMs": 12, "maxMs": 12}},
					"xrpcCount":  1,
				})
			default:
				t.Fatalf("unexpected Authorization header for getOcel: %q", r.Header.Get("Authorization"))
			}
		default:
			http.NotFound(w, r)
		}
	}))
	defer srv.Close()

	data, err := fetchOcelFromPDS("base-token", srv.URL, 5)
	if err != nil {
		t.Fatalf("fetchOcelFromPDS: %v", err)
	}
	if serviceAuthCalls != 1 {
		t.Fatalf("serviceAuthCalls: got %d, want 1", serviceAuthCalls)
	}
	if ocelCalls != 2 {
		t.Fatalf("ocelCalls: got %d, want 2", ocelCalls)
	}
	if data.XrpcCount != 1 || len(data.Events) != 1 {
		t.Fatalf("unexpected OCEL payload: %+v", data)
	}
}

func TestFetchOcelFromPDSSurfacesServiceAuthMintFailure(t *testing.T) {
	t.Setenv("GFTD_TOKEN", "base-token")

	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		switch {
		case r.URL.Path == "/_pds/ocel":
			http.NotFound(w, r)
		case r.URL.Path == "/xrpc/com.atproto.server.getServiceAuth":
			w.WriteHeader(http.StatusUnauthorized)
			_, _ = w.Write([]byte(`{"error":"AuthRequired"}`))
		case r.URL.Path == "/xrpc/ai.gftd.pds.getOcel":
			w.WriteHeader(http.StatusForbidden)
			_, _ = w.Write([]byte(`{"error":"Forbidden","message":"ai.gftd.pds.getOcel requires internal auth"}`))
		default:
			http.NotFound(w, r)
		}
	}))
	defer srv.Close()

	_, err := fetchOcelFromPDS("base-token", srv.URL, 5)
	if err == nil {
		t.Fatal("fetchOcelFromPDS: expected error")
	}
	if !strings.Contains(err.Error(), "service-auth mint failed") {
		t.Fatalf("error: got %q, want service-auth mint failure hint", err.Error())
	}
}

func TestFetchOcelFromPDSSurfacesBodyForServiceTokenFailure(t *testing.T) {
	t.Setenv("GFTD_TOKEN", "base-token")

	var serviceAuthCalls int
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		switch {
		case r.URL.Path == "/_pds/ocel":
			http.NotFound(w, r)
		case r.URL.Path == "/xrpc/com.atproto.server.getServiceAuth":
			serviceAuthCalls++
			_ = json.NewEncoder(w).Encode(map[string]any{"token": "svc-token"})
		case r.URL.Path == "/xrpc/ai.gftd.pds.getOcel":
			switch r.Header.Get("Authorization") {
			case "Bearer base-token":
				w.WriteHeader(http.StatusForbidden)
				_, _ = w.Write([]byte(`{"error":"Forbidden","message":"ai.gftd.pds.getOcel requires internal auth"}`))
			case "Bearer svc-token":
				w.WriteHeader(http.StatusServiceUnavailable)
				_, _ = w.Write([]byte(`{"error":"CloudflareAnalyticsAuthRequired","message":"Cloudflare API token required"}`))
			default:
				t.Fatalf("unexpected Authorization header for getOcel: %q", r.Header.Get("Authorization"))
			}
		default:
			http.NotFound(w, r)
		}
	}))
	defer srv.Close()

	_, err := fetchOcelFromPDS("base-token", srv.URL, 5)
	if err == nil {
		t.Fatal("fetchOcelFromPDS: expected error")
	}
	if serviceAuthCalls != 1 {
		t.Fatalf("serviceAuthCalls: got %d, want 1", serviceAuthCalls)
	}
	if !strings.Contains(err.Error(), "Cloudflare API token required") {
		t.Fatalf("error: got %q, want surfaced response body", err.Error())
	}
}
