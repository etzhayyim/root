package main

import (
	"fmt"
	"testing"
)

func TestBottleneckDetection(t *testing.T) {
	// Hub topology: "hub" receives from a,b,c and sends to d,e,f
	g := haisenGraph{
		Apps: []haisenApp{
			{Name: "a"}, {Name: "b"}, {Name: "c"},
			{Name: "hub"},
			{Name: "d"}, {Name: "e"}, {Name: "f"},
		},
		Edges: []haisenEdge{
			{From: "a", To: "hub", EdgeType: "invoke"},
			{From: "b", To: "hub", EdgeType: "invoke"},
			{From: "c", To: "hub", EdgeType: "writes"},
			{From: "hub", To: "d", EdgeType: "invoke"},
			{From: "hub", To: "e", EdgeType: "writes"},
			{From: "hub", To: "f", EdgeType: "reads"},
		},
	}

	report := buildBottleneckReport(g, 10, 1)

	if report.TotalApps != 7 {
		t.Errorf("expected 7 apps, got %d", report.TotalApps)
	}

	// "hub" should be the top bottleneck
	if len(report.Bottlenecks) == 0 {
		t.Fatal("expected at least 1 bottleneck")
	}
	if report.Bottlenecks[0].App != "hub" {
		t.Errorf("expected hub as top bottleneck, got %s", report.Bottlenecks[0].App)
	}
	if report.Bottlenecks[0].FanIn != 3 {
		t.Errorf("expected hub fan_in=3, got %d", report.Bottlenecks[0].FanIn)
	}
	if report.Bottlenecks[0].FanOut != 3 {
		t.Errorf("expected hub fan_out=3, got %d", report.Bottlenecks[0].FanOut)
	}
}

func TestBottleneckSeverity(t *testing.T) {
	// Create a node with high fan-in and fan-out
	edges := []haisenEdge{}
	for i := 0; i < 6; i++ {
		edges = append(edges, haisenEdge{
			From:     fmt.Sprintf("in%d", i),
			To:       "center",
			EdgeType: "invoke",
		})
		edges = append(edges, haisenEdge{
			From:     "center",
			To:       fmt.Sprintf("out%d", i),
			EdgeType: "invoke",
		})
	}

	g := haisenGraph{Edges: edges}
	report := buildBottleneckReport(g, 10, 1)

	// "center" should be critical
	found := false
	for _, b := range report.Bottlenecks {
		if b.App == "center" {
			found = true
			if b.Severity != "critical" {
				t.Errorf("expected critical severity for center (fan_in=%d, fan_out=%d, score=%.2f), got %s",
					b.FanIn, b.FanOut, b.BottleneckScore, b.Severity)
			}
		}
	}
	if !found {
		t.Error("expected center in bottlenecks")
	}
}

func TestBottleneckMutualInfo(t *testing.T) {
	g := haisenGraph{
		Edges: []haisenEdge{
			{From: "a", To: "hub", EdgeType: "invoke"},
			{From: "b", To: "hub", EdgeType: "writes"},
			{From: "hub", To: "c", EdgeType: "reads"},
			{From: "hub", To: "d", EdgeType: "subscribe"},
		},
	}
	report := buildBottleneckReport(g, 10, 1)

	for _, b := range report.Bottlenecks {
		if b.App == "hub" {
			if b.MutualInfo < 0 {
				t.Errorf("expected non-negative MI, got %.4f", b.MutualInfo)
			}
		}
	}
}

func TestBottleneckEmpty(t *testing.T) {
	g := haisenGraph{}
	r := buildBottleneckReport(g, 10, 2)
	if r.Score != 100 {
		t.Errorf("expected score=100 for empty graph, got %.1f", r.Score)
	}
}
