package main

import (
	"testing"
)

func TestMinimizeMergeProposal(t *testing.T) {
	// Two apps in same project with high mutual coupling
	g := haisenGraph{
		Apps: []haisenApp{
			{Name: "a", Project: "proj1"},
			{Name: "b", Project: "proj1"},
			{Name: "c", Project: "proj2"},
		},
		Edges: []haisenEdge{
			{From: "a", To: "b", EdgeType: "invoke"},
			{From: "a", To: "b", EdgeType: "writes"},
			{From: "b", To: "a", EdgeType: "invoke"},
			{From: "b", To: "a", EdgeType: "reads"},
			{From: "a", To: "c", EdgeType: "reads"},
		},
	}

	report := buildMinimizeReport(g, 10, 2.0)

	mergeFound := false
	for _, p := range report.Proposals {
		if p.Action == "merge" {
			mergeFound = true
			if p.Reduction <= 0 {
				t.Error("merge proposal should have positive reduction")
			}
		}
	}
	if !mergeFound {
		t.Error("expected a merge proposal for tightly-coupled same-project apps")
	}
}

func TestMinimizeSplitProposal(t *testing.T) {
	// One app with non-uniform outbound targets (skewed distribution).
	// Split at median separates high-count from low-count, reducing entropy.
	g := haisenGraph{
		Apps: []haisenApp{
			{Name: "god"},
			{Name: "a"}, {Name: "b"}, {Name: "c"}, {Name: "d"}, {Name: "e"},
		},
		Edges: []haisenEdge{
			{From: "god", To: "a", EdgeType: "invoke"},
			{From: "god", To: "a", EdgeType: "invoke"},
			{From: "god", To: "a", EdgeType: "invoke"},
			{From: "god", To: "a", EdgeType: "invoke"},
			{From: "god", To: "a", EdgeType: "invoke"},
			{From: "god", To: "b", EdgeType: "writes"},
			{From: "god", To: "b", EdgeType: "writes"},
			{From: "god", To: "b", EdgeType: "writes"},
			{From: "god", To: "c", EdgeType: "reads"},
			{From: "god", To: "d", EdgeType: "subscribe"},
			{From: "god", To: "e", EdgeType: "reads"},
		},
	}

	report := buildMinimizeReport(g, 10, 1.5)

	splitFound := false
	for _, p := range report.Proposals {
		if p.Action == "split" {
			splitFound = true
		}
	}
	if !splitFound {
		t.Error("expected a split proposal for high-entropy god module")
	}
}

func TestMinimizeMoveProposal(t *testing.T) {
	// App in proj1 but 80% of edges go to proj2
	g := haisenGraph{
		Apps: []haisenApp{
			{Name: "misplaced", Project: "proj1"},
			{Name: "x", Project: "proj2"},
			{Name: "y", Project: "proj2"},
			{Name: "z", Project: "proj2"},
			{Name: "w", Project: "proj2"},
		},
		Edges: []haisenEdge{
			{From: "misplaced", To: "x", EdgeType: "invoke"},
			{From: "misplaced", To: "y", EdgeType: "invoke"},
			{From: "misplaced", To: "z", EdgeType: "writes"},
			{From: "misplaced", To: "w", EdgeType: "reads"},
		},
	}

	report := buildMinimizeReport(g, 10, 2.0)

	moveFound := false
	for _, p := range report.Proposals {
		if p.Action == "move" {
			moveFound = true
			if len(p.Targets) != 1 || p.Targets[0] != "misplaced" {
				t.Errorf("expected move target=misplaced, got %v", p.Targets)
			}
		}
	}
	if !moveFound {
		t.Error("expected a move proposal for misplaced app")
	}
}

func TestMinimizeEmpty(t *testing.T) {
	g := haisenGraph{}
	r := buildMinimizeReport(g, 10, 2.0)
	if r.Score != 100 {
		t.Errorf("expected score=100 for empty graph, got %.1f", r.Score)
	}
}

func TestMinimizeScoreRange(t *testing.T) {
	g := haisenGraph{
		Apps: []haisenApp{
			{Name: "a", Project: "p1"},
			{Name: "b", Project: "p1"},
			{Name: "c", Project: "p2"},
		},
		Edges: []haisenEdge{
			{From: "a", To: "b", EdgeType: "invoke"},
			{From: "a", To: "c", EdgeType: "reads"},
		},
	}
	r := buildMinimizeReport(g, 10, 2.0)
	if r.Score < 0 || r.Score > 100 {
		t.Errorf("score out of range: %.1f", r.Score)
	}
}
