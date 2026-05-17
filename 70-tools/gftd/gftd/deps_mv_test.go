package main

import (
	"strings"
	"testing"
)

func TestDepsMVStatements(t *testing.T) {
	stmts := depsMVStatements()
	if len(stmts) != 2 {
		t.Fatalf("expected 2 statements, got %d", len(stmts))
	}
	if !strings.Contains(stmts[0], "mv_deps_component_live") {
		t.Fatalf("missing component MV in first statement")
	}
	if !strings.Contains(stmts[0], "vertex_actor") || !strings.Contains(stmts[0], "edge_governance") {
		t.Fatalf("expected vertex_/edge_ sources in component MV")
	}
	if strings.Contains(strings.ToLower(stmts[0]), "json") || strings.Contains(strings.ToLower(stmts[1]), "json") {
		t.Fatalf("deps MV SQL must not depend on JSON sources")
	}
	if got := depsMVName(stmts[0]); got != "mv_deps_component_live" {
		t.Fatalf("unexpected mv name: %s", got)
	}
	if got := depsMVName(stmts[1]); got != "mv_deps_summary_live" {
		t.Fatalf("unexpected summary mv name: %s", got)
	}
}
