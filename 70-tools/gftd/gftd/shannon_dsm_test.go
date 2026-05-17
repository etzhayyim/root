package main

import (
	"math"
	"testing"
)

func TestShEntropy(t *testing.T) {
	// Uniform distribution over 4 items: H = log2(4) = 2.0
	counts := map[string]int{"a": 10, "b": 10, "c": 10, "d": 10}
	h := shEntropy(counts)
	if math.Abs(h-2.0) > 0.001 {
		t.Errorf("expected H≈2.0 for uniform(4), got %.4f", h)
	}

	// Single item: H = 0
	h = shEntropy(map[string]int{"a": 5})
	if h != 0 {
		t.Errorf("expected H=0 for single item, got %.4f", h)
	}

	// Empty: H = 0
	h = shEntropy(map[string]int{})
	if h != 0 {
		t.Errorf("expected H=0 for empty, got %.4f", h)
	}
}

func TestShBuildAdjacency(t *testing.T) {
	g := haisenGraph{
		Edges: []haisenEdge{
			{From: "a", To: "b", EdgeType: "invoke"},
			{From: "a", To: "c", EdgeType: "writes"},
			{From: "b", To: "c", EdgeType: "reads"},
			{From: "a", To: "b", EdgeType: "reads"}, // duplicate pair, different type
		},
	}

	apps, adj := shBuildAdjacency(g)
	if len(apps) != 3 {
		t.Errorf("expected 3 apps, got %d", len(apps))
	}
	if adj["a"]["b"] != 2 {
		t.Errorf("expected a→b count=2, got %d", adj["a"]["b"])
	}
	if adj["a"]["c"] != 1 {
		t.Errorf("expected a→c count=1, got %d", adj["a"]["c"])
	}
}

func TestDSMCuthillMcKee(t *testing.T) {
	// 5-node chain: 0-1-2-3-4
	matrix := [][]int{
		{0, 1, 0, 0, 0},
		{1, 0, 1, 0, 0},
		{0, 1, 0, 1, 0},
		{0, 0, 1, 0, 1},
		{0, 0, 0, 1, 0},
	}
	perm := dsmCuthillMcKee(matrix, 5)
	if len(perm) != 5 {
		t.Fatalf("expected perm length 5, got %d", len(perm))
	}

	// Verify it's a valid permutation
	seen := make(map[int]bool)
	for _, p := range perm {
		if p < 0 || p >= 5 {
			t.Errorf("invalid perm value: %d", p)
		}
		seen[p] = true
	}
	if len(seen) != 5 {
		t.Errorf("permutation is not a bijection")
	}
}

func TestDSMDetectCycles(t *testing.T) {
	// Triangle: a→b→c→a
	adj := map[string]map[string]int{
		"a": {"b": 1},
		"b": {"c": 1},
		"c": {"a": 1},
	}
	cycles := dsmDetectCycles([]string{"a", "b", "c"}, adj)
	if len(cycles) == 0 {
		t.Error("expected at least 1 cycle for triangle graph")
	}
	found := false
	for _, c := range cycles {
		if c.Length == 3 {
			found = true
		}
	}
	if !found {
		t.Error("expected a cycle of length 3")
	}
}

func TestDSMFindClusters(t *testing.T) {
	// Two disconnected pairs: a↔b, c↔d
	adj := map[string]map[string]int{
		"a": {"b": 1},
		"b": {"a": 1},
		"c": {"d": 1},
		"d": {"c": 1},
	}
	clusters := dsmFindClusters([]string{"a", "b", "c", "d"}, adj)
	if len(clusters) != 2 {
		t.Errorf("expected 2 clusters, got %d", len(clusters))
	}
}

func TestBuildDSMReportEmpty(t *testing.T) {
	g := haisenGraph{}
	r := buildDSMReport(g, 10, false)
	if r.Score != 100 {
		t.Errorf("expected score=100 for empty graph, got %.1f", r.Score)
	}
}
