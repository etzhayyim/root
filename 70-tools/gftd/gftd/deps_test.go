package main

import (
	"bytes"
	"encoding/json"
	"io"
	"math"
	"net/http"
	"net/http/httptest"
	"os"
	"strings"
	"testing"
)

func TestParseDepsUISummaryParsesOptionalBadges(t *testing.T) {
	html := `
<div>
  <span>575 domain deps</span>
  <span>12 isolated (2.1%)</span>
  <span>governance coverage 78.5%</span>
  <span>explicit RACI coverage: 0.64</span>
</div>`

	got := parseDepsUISummary(html)
	if !got.HasIsolated {
		t.Fatal("expected isolated badge to be detected")
	}
	if got.IsolatedCount != 12 {
		t.Fatalf("isolated count = %d, want 12", got.IsolatedCount)
	}
	if diff := math.Abs(got.IsolatedRate - 0.021); diff > 0.0001 {
		t.Fatalf("isolated rate = %.4f, want 0.0210", got.IsolatedRate)
	}
	if !got.HasGovernanceCoverage {
		t.Fatal("expected governance coverage badge to be detected")
	}
	if diff := math.Abs(got.GovernanceCoverage - 0.785); diff > 0.0001 {
		t.Fatalf("governance coverage = %.4f, want 0.7850", got.GovernanceCoverage)
	}
	if !got.HasRACICoverage {
		t.Fatal("expected RACI coverage badge to be detected")
	}
	if diff := math.Abs(got.RACICoverage - 0.64); diff > 0.0001 {
		t.Fatalf("raci coverage = %.4f, want 0.6400", got.RACICoverage)
	}
}

func TestFormatDepsScoreSummaryIncludesOptionalMetrics(t *testing.T) {
	report := &depsScoreReport{
		UnresolvedCount:           3,
		GovernanceUnresolvedCount: 1,
		LinkCoverageRate:          0.6523,
		IsolatedCount:             4,
		IsolatedRate:              0.0123,
		GovernanceCoverage:        0.7812,
		RACICoverage:              0.6434,
		IsolationPenalty:          7.5,
		UnadaptedPenalty:          16.0,
		Scoring: depsScoring{
			BuildLinkerScore:         71.2,
			RuntimeLinkerScore:       63.4,
			DoDAFV2Score:             59.1,
			NISTCSFV2Score:           68.8,
			AppWITDefinitionScore:    82.4,
			AppWITDefinitionCoverage: 0.9211,
		},
	}

	got := formatDepsScoreSummary(report)
	for _, want := range []string{
		"build=71.2",
		"runtime=63.4",
		"isolated=4",
		"isolated-rate=0.0123",
		"governance-coverage=0.7812",
		"raci-coverage=0.6434",
		"isolation-penalty=7.5",
		"unadapted-penalty=16.0",
	} {
		if !strings.Contains(got, want) {
			t.Fatalf("summary %q missing %q", got, want)
		}
	}
}

func TestPrintDepsScoreTextIncludesOptionalMetrics(t *testing.T) {
	report := &depsScoreReport{
		SourceURL:                 "https://deps.etzhayyim.com/",
		EvaluatedAt:               "2026-03-20T00:00:00Z",
		TotalLinks:                10,
		ResolvedCount:             8,
		UnresolvedCount:           2,
		LinkCoverageRate:          0.8,
		UnresolvedRate:            0.2,
		GovernanceUnresolvedCount: 1,
		IsolatedCount:             4,
		IsolatedRate:              0.0123,
		GovernanceCoverage:        0.7812,
		RACICoverage:              0.6434,
		IsolationPenalty:          7.5,
		UnadaptedPenalty:          16.0,
		Scoring: depsScoring{
			Model:                    "test model",
			OverallScore:             71.2,
			BuildLinkerScore:         71.2,
			RuntimeLinkerScore:       63.4,
			DoDAFV2Score:             59.1,
			NISTCSFV2Score:           68.8,
			AppWITDefinitionScore:    82.4,
			AppWITDefinitionCoverage: 0.9211,
			BuildLinkerFactors: depsStageScoreFactors{
				IsolatedRate:       0.0123,
				GovernanceCoverage: 0.7812,
				RACICoverage:       0.6434,
			},
			RuntimeLinkerFactors: depsStageScoreFactors{
				LinkCoverage: 0.8,
			},
		},
	}

	oldStdout := os.Stdout
	r, w, err := os.Pipe()
	if err != nil {
		t.Fatalf("pipe: %v", err)
	}
	os.Stdout = w
	printDepsScoreText(report)
	w.Close()
	os.Stdout = oldStdout

	var buf bytes.Buffer
	if _, err := io.Copy(&buf, r); err != nil {
		t.Fatalf("read stdout: %v", err)
	}
	out := buf.String()
	for _, want := range []string{
		"isolated_count: 4",
		"isolated_rate: 0.0123",
		"governance_coverage: 0.7812",
		"raci_coverage: 0.6434",
		"isolation_penalty: 7.5",
		"unadapted_penalty: 16.0",
	} {
		if !strings.Contains(out, want) {
			t.Fatalf("output %q missing %q", out, want)
		}
	}
}

func TestTriggerDepsManualRefresh(t *testing.T) {
	var got map[string]any
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			t.Fatalf("method = %s, want POST", r.Method)
		}
		if r.URL.Path != "/api/hooks/component" {
			t.Fatalf("path = %s, want /api/hooks/component", r.URL.Path)
		}
		if ct := r.Header.Get("Content-Type"); ct != "application/json" {
			t.Fatalf("content-type = %s, want application/json", ct)
		}
		if err := json.NewDecoder(r.Body).Decode(&got); err != nil {
			t.Fatalf("decode body: %v", err)
		}
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusAccepted)
		_, _ = w.Write([]byte(`{"status":"accepted","event":"manual_refresh"}`))
	}))
	defer srv.Close()

	res, err := triggerDepsManualRefresh(srv.Client(), srv.URL+"/", "manual_refresh", "deps")
	if err != nil {
		t.Fatalf("triggerDepsManualRefresh: %v", err)
	}
	if !res.Triggered {
		t.Fatal("expected Triggered=true")
	}
	if res.Status != "accepted" {
		t.Fatalf("status = %s, want accepted", res.Status)
	}
	if got["schema"] != "gftd:wproto/hook-envelope@v1" {
		t.Fatalf("schema = %v", got["schema"])
	}
	if got["event"] != "manual_refresh" {
		t.Fatalf("event = %v", got["event"])
	}
	app, ok := got["app"].(map[string]any)
	if !ok {
		t.Fatalf("app payload type = %T", got["app"])
	}
	if app["app_id"] != "deps" {
		t.Fatalf("app_id = %v", app["app_id"])
	}
}
