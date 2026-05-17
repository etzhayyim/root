package main

import (
	"testing"
)

func TestResolveRank(t *testing.T) {
	tests := []struct {
		score int
		want  string
	}{
		{0, "Kyu 6"},
		{99, "Kyu 6"},
		{100, "Kyu 5"},
		{600, "Kyu 3"},
		{1500, "Kyu 1"},
		{2000, "Dan 1"},
		{5000, "Dan 3"},
		{12000, "Dan 10"},
	}
	for _, tt := range tests {
		r := resolveRank(tt.score)
		if r.Name != tt.want {
			t.Errorf("resolveRank(%d) = %s, want %s", tt.score, r.Name, tt.want)
		}
	}
}

func TestMokutekiEngagement(t *testing.T) {
	apps := []string{"a", "b", "c"}
	adj := map[string]map[string]int{
		"a": {"b": 1},
		"b": {"c": 1},
	}
	r := mokutekiEngagement(apps, adj, 5)
	if r.score <= 0 || r.score > 100 {
		t.Errorf("score out of range: %.1f", r.score)
	}
}

func TestMokutekiHypergraph(t *testing.T) {
	g := haisenGraph{
		Edges: []haisenEdge{
			{From: "a", To: "coll1", EdgeType: "writes"},
			{From: "b", To: "coll1", EdgeType: "writes"}, // multi-writer
			{From: "c", To: "coll2", EdgeType: "writes"},   // single writer
		},
	}
	r := mokutekiHypergraph(g)
	// 1 of 2 collections is multi-writer = 50% penalty
	if r.score < 40 || r.score > 60 {
		t.Errorf("expected ~50 for 1/2 multi-writer, got %.1f", r.score)
	}
}

func TestMokutekiPOMDPObservation(t *testing.T) {
	g := haisenGraph{
		Apps: []haisenApp{{Name: "a"}, {Name: "b"}, {Name: "c"}},
		Edges: []haisenEdge{
			{From: "a", To: "b", EdgeType: "invoke"},
			{From: "b", To: "c", EdgeType: "writes"},
		},
	}
	c := mokutekiPOMDPObservation(g)
	if c.Score < 0 || c.Score > 100 {
		t.Errorf("score out of range: %.1f", c.Score)
	}
}

func TestMokutekiEventSourcing(t *testing.T) {
	meta := map[string]sgMetaResult{
		"app1": {Collections: []string{"app.bsky.feed.post"}, DID: "did:web:a.etzhayyim.com"},
		"app2": {DID: "did:web:b.etzhayyim.com"},
		"app3": {Collections: []string{"ai.gftd.apps.x.item"}, DID: "did:web:c.etzhayyim.com"},
	}
	c := mokutekiEventSourcing(meta)
	// 2 of 3 have triggers
	if c.Score < 60 || c.Score > 70 {
		t.Errorf("expected ~66.7 for 2/3 reactive, got %.1f", c.Score)
	}
}

func TestMokutekiAttestation(t *testing.T) {
	meta := map[string]sgMetaResult{
		"app1": {DID: "did:web:a.etzhayyim.com", DisplayName: "App A"},
		"app2": {DID: "did:web:b.etzhayyim.com"},  // no displayName
		"app3": {DisplayName: "App C"},         // no DID
	}
	c := mokutekiAttestation(meta)
	// Only app1 is fully attested = 33.3%
	if c.Score < 30 || c.Score > 40 {
		t.Errorf("expected ~33.3 for 1/3 attested, got %.1f", c.Score)
	}
}

func TestMokutekiBar(t *testing.T) {
	bar := mokutekiBar(50)
	runes := []rune(bar)
	if len(runes) != 22 {
		t.Errorf("expected 22 runes, got %d: %q", len(runes), bar)
	}
}

func TestMokutekiNextRank(t *testing.T) {
	next := mokutekiNextRank(50)
	if next != "Kyu 5" {
		t.Errorf("expected Kyu 5, got %s", next)
	}
	pts := mokutekiPointsToNext(50)
	if pts != 50 {
		t.Errorf("expected 50 pts, got %d", pts)
	}
}

func TestMokutekiWeightedScore(t *testing.T) {
	checks := []mokutekiCheck{
		{Score: 100, Weight: 0.5},
		{Score: 0, Weight: 0.5},
	}
	score := mokutekiWeightedScore(checks)
	if score != 50 {
		t.Errorf("expected 50, got %.1f", score)
	}
}

func TestDeriveWellBeingAxes(t *testing.T) {
	a := mokutekiLayer{Score: 80}
	b := mokutekiLayer{Score: 60}
	c := mokutekiLayer{Score: 70}
	d := mokutekiLayer{Score: 90}

	axes := deriveWellBeingAxes(a, b, c, d)
	if len(axes) != 5 {
		t.Fatalf("expected 5 axes, got %d", len(axes))
	}
	for _, ax := range axes {
		if ax.Score < 0 || ax.Score > 100 {
			t.Errorf("%s score out of range: %.1f", ax.Name, ax.Score)
		}
	}
}

func TestMokutekiLayerDiagnosis(t *testing.T) {
	layers := []mokutekiLayer{
		{ID: "A", NameJP: "構造", Score: 80, Components: []mokutekiCheck{{Name: "DSM", Score: 90, Weight: 0.3}}},
		{ID: "B", NameJP: "不確実性", Score: 20, Components: []mokutekiCheck{{Name: "BayesNet", Score: 15, Weight: 0.35}}},
		{ID: "C", NameJP: "制御", Score: 70, Components: nil},
		{ID: "D", NameJP: "実装", Score: 50, Components: nil},
	}
	axes := deriveWellBeingAxes(
		mokutekiLayer{Score: 80},
		mokutekiLayer{Score: 20},
		mokutekiLayer{Score: 70},
		mokutekiLayer{Score: 50},
	)
	diag := mokutekiLayerDiagnosis(layers, axes, 500)
	if len(diag) == 0 {
		t.Error("expected diagnosis entries")
	}
	// Should flag Layer B as critical
	foundB := false
	for _, d := range diag {
		if len(d) > 0 && d[0] == '[' {
			for i := 0; i <= len(d)-7; i++ {
				if d[i:i+7] == "Layer B" {
					foundB = true
					break
				}
			}
		}
	}
	if !foundB {
		t.Error("expected Layer B diagnosis")
	}
}
