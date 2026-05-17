package main

import (
	"testing"
)

func TestBayesNetCouplingStrength(t *testing.T) {
	g := haisenGraph{
		Edges: []haisenEdge{
			{From: "a", To: "b", EdgeType: "invoke"},
			{From: "a", To: "b", EdgeType: "invoke"},
			{From: "b", To: "c", EdgeType: "reads"},
		},
	}
	report := buildBayesNetReport(g, 5, 6)

	if report.TotalApps != 3 {
		t.Errorf("expected 3 apps, got %d", report.TotalApps)
	}
	if report.TotalEdges != 2 {
		t.Errorf("expected 2 edges (deduplicated by pair), got %d", report.TotalEdges)
	}

	// a→b should have higher conditional than b→c (invoke > reads)
	var abCond, bcCond float64
	for _, e := range report.Edges {
		if e.From == "a" && e.To == "b" {
			abCond = e.Conditional
		}
		if e.From == "b" && e.To == "c" {
			bcCond = e.Conditional
		}
	}
	if abCond <= bcCond {
		t.Errorf("expected a→b conditional (%.3f) > b→c conditional (%.3f)", abCond, bcCond)
	}
}

func TestBayesNetHighRiskPaths(t *testing.T) {
	// Chain: a→b→c with strong coupling
	g := haisenGraph{
		Edges: []haisenEdge{
			{From: "a", To: "b", EdgeType: "invoke"},
			{From: "b", To: "c", EdgeType: "invoke"},
		},
	}
	report := buildBayesNetReport(g, 10, 6)

	// Should find path a→b→c
	found := false
	for _, p := range report.HighRiskPaths {
		if len(p.Nodes) == 3 && p.Nodes[0] == "a" && p.Nodes[1] == "b" && p.Nodes[2] == "c" {
			found = true
			if p.Probability <= 0 {
				t.Error("path probability should be > 0")
			}
		}
	}
	if !found {
		t.Error("expected to find path a→b→c in high-risk paths")
	}
}

func TestBayesNetEmpty(t *testing.T) {
	g := haisenGraph{}
	r := buildBayesNetReport(g, 5, 6)
	if r.Score != 100 {
		t.Errorf("expected score=100 for empty graph, got %.1f", r.Score)
	}
}

func TestBayesPriorityQueue(t *testing.T) {
	// Verify heap interface works
	pq := &bayesPQ{}
	pq.Push(&bayesPQItem{app: "a", negLogP: 2.0})
	pq.Push(&bayesPQItem{app: "b", negLogP: 1.0})
	pq.Push(&bayesPQItem{app: "c", negLogP: 3.0})

	if pq.Len() != 3 {
		t.Errorf("expected 3 items, got %d", pq.Len())
	}
}
