package main

import "testing"

func TestBuildKaizenLogsSummaryUsesAggregateCountsAndErrors(t *testing.T) {
	data := ocelResponse{
		Events: []ocelEvent{
			{Method: "com.atproto.repo.createRecord", Ms: 24, Status: 500},
			{Method: "com.atproto.repo.createRecord", Ms: 1200, Status: 200},
		},
		Aggregates: map[string]ocelAgg{
			"com.atproto.repo.createRecord": {
				Count:   2,
				Errors:  1,
				TotalMs: 1224,
				MaxMs:   1200,
				P50Ms:   24,
				P99Ms:   1200,
			},
		},
	}

	summary := buildKaizenLogsSummary(data, "analytics_engine", 2, 5, 5, 500, 1)

	if summary.TotalErrors != 1 {
		t.Fatalf("totalErrors: got %d, want 1", summary.TotalErrors)
	}
	if summary.OverallErrorRate != 50 {
		t.Fatalf("overallErrorRate: got %v, want 50", summary.OverallErrorRate)
	}
	if len(summary.SlowQueries) != 1 {
		t.Fatalf("slowQueries len: got %d, want 1", len(summary.SlowQueries))
	}
	if len(summary.ErrorQueries) != 1 {
		t.Fatalf("errorQueries len: got %d, want 1", len(summary.ErrorQueries))
	}
	if summary.ErrorQueries[0].Method != "com.atproto.repo.createRecord" {
		t.Fatalf("errorQueries[0].Method: got %q", summary.ErrorQueries[0].Method)
	}
}

func TestBuildKaizenLogsSummaryFallsBackToEventErrorsAndReverseTopology(t *testing.T) {
	data := ocelResponse{
		Events: []ocelEvent{
			{Method: "ai.gftd.kagami.sql", Ms: 20000, Status: 504},
			{Method: "ai.gftd.kagami.sql", Ms: 415, Status: 502},
			{Method: "ai.gftd.kagami.sql", Ms: 0, Status: 410},
			{Method: "ai.gftd.pds.getEntityGraph", Ms: 1, Status: 501},
		},
		Aggregates: map[string]ocelAgg{
			"ai.gftd.kagami.sql": {Count: 3, Errors: 0, MaxMs: 20000, P99Ms: 20000},
		},
	}

	summary := buildKaizenLogsSummary(data, "analytics_engine", 4, 5, 5, 500, 1)

	if summary.TotalErrors != 4 {
		t.Fatalf("totalErrors: got %d, want 4", summary.TotalErrors)
	}
	if len(summary.SlowQueries) == 0 {
		t.Fatal("slowQueries: expected event-derived slow query")
	}
	if len(summary.ReverseTopology) == 0 {
		t.Fatal("reverseTopology: expected graph-query root cause")
	}
	if summary.ReverseTopology[0].Key != "graph-query" {
		t.Fatalf("reverseTopology[0].Key: got %q, want graph-query", summary.ReverseTopology[0].Key)
	}
	if len(summary.LikelyCauses) == 0 {
		t.Fatal("likelyCauses: expected reverse-topology summary")
	}
}
