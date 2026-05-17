package main

import (
	"context"
	"testing"

	"github.com/etzhayyim/root/70-tools/gftd/gftd/db"
)

func TestIntegrationDepsMVApplyAndQuery(t *testing.T) {
	requireDomainCoverageDB(t)

	if err := runDepsMV([]string{"--apply", "--format", "text", "--timeout-sec", "30"}); err != nil {
		t.Fatalf("runDepsMV --apply failed: %v", err)
	}

	ctx := context.Background()

	summary, err := db.RawQuery(ctx, `
SELECT total_components, capability_coverage, governance_coverage, overall_score
FROM mv_deps_summary_live`)
	if err != nil {
		t.Fatalf("mv_deps_summary_live query failed: %v", err)
	}
	if len(summary.Rows) != 1 {
		t.Fatalf("mv_deps_summary_live rows = %d, want 1", len(summary.Rows))
	}
	if summary.Rows[0]["total_components"] == nil {
		t.Fatal("mv_deps_summary_live.total_components is nil")
	}

	components, err := db.RawQuery(ctx, `
SELECT component_did, capability_vertex_count, governance_edge_count, isolated
FROM mv_deps_component_live
ORDER BY component_did
LIMIT 5`)
	if err != nil {
		t.Fatalf("mv_deps_component_live query failed: %v", err)
	}
	if len(components.Rows) == 0 {
		t.Fatal("mv_deps_component_live returned no rows")
	}
	if got := parseStringLike(components.Rows[0]["component_did"]); got == "" {
		t.Fatal("first mv_deps_component_live row has empty component_did")
	}
}
