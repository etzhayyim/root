package main

import (
	"bytes"
	"context"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/etzhayyim/root/70-tools/gftd/gftd/db"
)

func TestCollectWITDomainsSummarizesPackages(t *testing.T) {
	root := t.TempDir()
	depsDir := filepath.Join(root, "packages", "contract", "wit", "deps", "sample")
	if err := os.MkdirAll(depsDir, 0o755); err != nil {
		t.Fatalf("mkdir: %v", err)
	}
	content := strings.Join([]string{
		"package sample:domain;",
		"interface reader {",
		"  read: func();",
		"}",
		"record entity { id: string }",
		"enum state { active, archived }",
	}, "\n")
	if err := os.WriteFile(filepath.Join(depsDir, "package.wit"), []byte(content), 0o644); err != nil {
		t.Fatalf("write package.wit: %v", err)
	}

	got := collectWITDomains(root)
	if len(got) != 1 {
		t.Fatalf("len = %d, want 1", len(got))
	}
	if got[0].Package != "sample" || got[0].Interfaces != 1 || got[0].Functions != 1 || got[0].Records != 1 || got[0].Enums != 1 {
		t.Fatalf("unexpected summary: %+v", got[0])
	}
}

func TestCollectKyumeiReportsPicksLatestByKind(t *testing.T) {
	root := t.TempDir()
	reportsDir := filepath.Join(root, "reports")
	if err := os.MkdirAll(reportsDir, 0o755); err != nil {
		t.Fatalf("mkdir: %v", err)
	}

	write := func(name string, score float64, grade string, severities ...string) {
		payload := map[string]any{
			"readiness_score": score,
			"readiness_grade": grade,
			"knowledge_gaps":  make([]map[string]string, 0, len(severities)),
		}
		for _, sev := range severities {
			payload["knowledge_gaps"] = append(payload["knowledge_gaps"].([]map[string]string), map[string]string{"severity": sev})
		}
		data, _ := json.Marshal(payload)
		if err := os.WriteFile(filepath.Join(reportsDir, name), data, 0o644); err != nil {
			t.Fatalf("write %s: %v", name, err)
		}
	}

	write("kyumei-domain-community-full-20260413.json", 61.4, "B", "high")
	write("kyumei-domain-community-full-20260414.json", 72.6, "A", "critical", "high", "medium")

	got := collectKyumeiReports(root)
	report, ok := got["community"]
	if !ok {
		t.Fatal("expected community report")
	}
	if report.file != "kyumei-domain-community-full-20260414.json" {
		t.Fatalf("file = %q", report.file)
	}
	if report.score != 73 || report.grade != "A" || report.critical != 1 || report.high != 1 || report.medium != 1 {
		t.Fatalf("unexpected report: %+v", report)
	}
}

func TestRunDomainCoverageJSONWithoutReconcile(t *testing.T) {
	root := t.TempDir()
	depsDir := filepath.Join(root, "packages", "contract", "wit", "deps", "sample")
	reportsDir := filepath.Join(root, "reports")
	if err := os.MkdirAll(depsDir, 0o755); err != nil {
		t.Fatalf("mkdir deps: %v", err)
	}
	if err := os.MkdirAll(reportsDir, 0o755); err != nil {
		t.Fatalf("mkdir reports: %v", err)
	}
	if err := os.WriteFile(filepath.Join(depsDir, "package.wit"), []byte("interface sample {\n  ping: func();\n}\nrecord rec { id: string }\n"), 0o644); err != nil {
		t.Fatalf("write package.wit: %v", err)
	}
	reportData := `{"readiness_score":88.2,"readiness_grade":"S","knowledge_gaps":[{"severity":"critical"}]}`
	if err := os.WriteFile(filepath.Join(reportsDir, "kyumei-domain-community-full-20260414.json"), []byte(reportData), 0o644); err != nil {
		t.Fatalf("write report: %v", err)
	}

	oldStdout := os.Stdout
	r, w, err := os.Pipe()
	if err != nil {
		t.Fatalf("pipe: %v", err)
	}
	os.Stdout = w
	defer func() { os.Stdout = oldStdout }()

	runErr := runDomainCoverage([]string{"--root", root, "--format", "json", "--no-reconcile"})
	_ = w.Close()
	if runErr != nil {
		t.Fatalf("runDomainCoverage: %v", runErr)
	}

	var buf bytes.Buffer
	if _, err := buf.ReadFrom(r); err != nil {
		t.Fatalf("read stdout: %v", err)
	}

	var decoded fullCoverageReport
	if err := json.Unmarshal(buf.Bytes(), &decoded); err != nil {
		t.Fatalf("unmarshal output: %v\n%s", err, buf.String())
	}
	if decoded.WITSummary.TotalPackages != 1 || decoded.WITSummary.TotalFunctions != 1 || decoded.WITSummary.TotalRecords != 1 {
		t.Fatalf("unexpected wit summary: %+v", decoded.WITSummary)
	}
	if decoded.LiveReadModel.Name != "mv_domain_coverage_live" || decoded.LiveReadModel.Mode != "read-only live MV" {
		t.Fatalf("unexpected live read model: %+v", decoded.LiveReadModel)
	}
	if len(decoded.AuthorityChain.Domains) == 0 {
		t.Fatal("expected authority domains")
	}
	var found bool
	for _, d := range decoded.AuthorityChain.Domains {
		if d.Kind == "community" {
			found = true
			if d.KyumeiGrade != "S" || d.KyumeiCritical != 1 {
				t.Fatalf("unexpected community kyumei data: %+v", d)
			}
		}
	}
	if !found {
		t.Fatal("expected community domain")
	}
}

func TestRunDomainCoverageStrictReturnsErrorWhenReconcileFails(t *testing.T) {
	oldRawQuery := rawQuery
	t.Cleanup(func() { rawQuery = oldRawQuery })
	rawQuery = func(_ context.Context, _ string, _ ...any) (*db.RawResult, error) {
		return nil, context.DeadlineExceeded
	}

	err := runDomainCoverage([]string{"--strict"})
	if err == nil {
		t.Fatal("expected strict reconciliation error")
	}
	if !strings.Contains(err.Error(), "live reconciliation required (--strict)") {
		t.Fatalf("unexpected error: %v", err)
	}
}

func TestCoverageHelpersParseValues(t *testing.T) {
	if got := coverageBar(0.5, 4); got != "[██░░]" {
		t.Fatalf("coverageBar = %q", got)
	}
	if got := parseStringLike([]byte("abc")); got != "abc" {
		t.Fatalf("parseStringLike bytes = %q", got)
	}
	if got := parseStringLike(42); got != "42" {
		t.Fatalf("parseStringLike fmt = %q", got)
	}
	if got := parseFloatLike("3.5"); got != 3.5 {
		t.Fatalf("parseFloatLike string = %v", got)
	}
	if got := parseFloatLike([]byte("7")); got != 7 {
		t.Fatalf("parseFloatLike bytes = %v", got)
	}
}

func TestCollectCoverageReconciliationKagamiUsesLiveMV(t *testing.T) {
	oldRawQuery := rawQuery
	t.Cleanup(func() { rawQuery = oldRawQuery })

	rawQuery = func(_ context.Context, sql string, args ...any) (*db.RawResult, error) {
		if !strings.Contains(sql, "FROM mv_domain_coverage_live") {
			t.Fatalf("unexpected SQL: %s", sql)
		}
		if len(args) != 2 || args[0] != "community" || args[1] != "industry" {
			t.Fatalf("unexpected args: %#v", args)
		}
		return &db.RawResult{
			Rows: []map[string]any{
				{
					"kind":                 "industry",
					"authority_rate":       "0.40",
					"live_coverage_did":    0.55,
					"live_coverage_record": []byte("0.60"),
					"delta_did":            -0.15,
					"delta_record":         -0.20,
				},
				{
					"kind":                 "community",
					"authority_rate":       "0.56",
					"live_coverage_did":    0.70,
					"live_coverage_record": "0.80",
					"delta_did":            "-0.14",
					"delta_record":         "-0.24",
				},
			},
		}, nil
	}

	recon, err := collectCoverageReconciliationKagami(kagamiConfig{}, []coverageDomain{
		{Kind: "private"},
		{Kind: "community"},
		{Kind: "industry"},
	})
	if err != nil {
		t.Fatalf("collectCoverageReconciliationKagami: %v", err)
	}
	if len(recon) != 2 {
		t.Fatalf("len = %d, want 2", len(recon))
	}
	if recon[0].Kind != "community" || recon[0].LiveCountSource != "risingwave:mv_domain_coverage_live" {
		t.Fatalf("unexpected first row: %+v", recon[0])
	}
	if recon[1].Kind != "industry" || recon[1].LiveCoverageRec != 0.60 {
		t.Fatalf("unexpected second row: %+v", recon[1])
	}
}
