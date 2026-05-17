package main

import (
	"strings"
	"testing"
)

func TestBuildDomainIngestLocalArgs(t *testing.T) {
	got := buildDomainIngestLocalArgs("/repo/70-tools/scripts/ingest-domain-data.ts", "gtin", 500, true, true)
	want := []string{
		"tsx",
		"/repo/70-tools/scripts/ingest-domain-data.ts",
		"--domain", "gtin",
		"--limit", "500",
		"--dry-run",
		"--skip-llm",
	}
	if strings.Join(got, " ") != strings.Join(want, " ") {
		t.Fatalf("args = %#v, want %#v", got, want)
	}
}

func TestRunDomainIngestRejectsUnknownSubcommand(t *testing.T) {
	err := runDomainIngest([]string{"unknown-subcommand"})
	if err == nil {
		t.Fatal("expected error")
	}
	if !strings.Contains(err.Error(), "unknown domain-ingest subcommand") {
		t.Fatalf("unexpected error: %v", err)
	}
}
