package main

// Tests for actor.toml parsing + stage gating.

import (
	"strings"
	"testing"
)

const sampleActorTOML = `
[actor]
name = "test"
did = "did:web:test.example"
nanoid = "test1234"

[[stages]]
name = "did-worker"
description = "Cloudflare Worker"
type = "cf-worker"
working_dir = "50-infra/test-did-web"
command = ["wrangler", "deploy"]
require_cap = ["deploy.cfWorker:test-did-web"]
on_error = "abort"
dry_run_safe = false

[[stages]]
name = "k8s-pod"
type = "k8s"
command = ["kubectl", "apply", "-f", "deployment.yaml"]
depends_on = ["did-worker"]
require_cap = ["deploy.k8s:lg-test"]

[stages.env]
KUBECONFIG = "/tmp/kubeconfig"

[[stages]]
name = "smoke"
type = "smoke"
command = ["bash", "-c", "curl -fsS https://test.example/healthz"]
on_error = "continue"
dry_run_safe = true
`

func TestParseActorTOML_Basic(t *testing.T) {
	m, err := parseActorTOML([]byte(sampleActorTOML))
	if err != nil {
		t.Fatalf("parse: %v", err)
	}
	if m.Actor.Name != "test" {
		t.Errorf("actor.name: %q", m.Actor.Name)
	}
	if m.Actor.Did != "did:web:test.example" {
		t.Errorf("actor.did: %q", m.Actor.Did)
	}
	if len(m.Stages) != 3 {
		t.Fatalf("want 3 stages, got %d", len(m.Stages))
	}
	if m.Stages[0].Name != "did-worker" {
		t.Errorf("stage[0].name: %q", m.Stages[0].Name)
	}
	if len(m.Stages[0].Command) != 2 || m.Stages[0].Command[0] != "wrangler" {
		t.Errorf("stage[0].command: %v", m.Stages[0].Command)
	}
	if len(m.Stages[0].RequireCap) != 1 || m.Stages[0].RequireCap[0] != "deploy.cfWorker:test-did-web" {
		t.Errorf("stage[0].require_cap: %v", m.Stages[0].RequireCap)
	}
	// k8s stage has env
	if m.Stages[1].Env["KUBECONFIG"] != "/tmp/kubeconfig" {
		t.Errorf("stage[1].env.KUBECONFIG: %q", m.Stages[1].Env["KUBECONFIG"])
	}
	// smoke stage
	if m.Stages[2].OnError != "continue" || !m.Stages[2].DryRunSafe {
		t.Errorf("stage[2] flags: on_error=%q dry_run_safe=%v", m.Stages[2].OnError, m.Stages[2].DryRunSafe)
	}
}

func TestStageGate_NoCapability(t *testing.T) {
	st := &actorStage{Name: "x", RequireCap: []string{"deploy.k8s:lg-test"}}
	err := stageGate(st, nil, "")
	if err == nil {
		t.Fatal("expected gate to deny with no capability + no token")
	}
	if !strings.Contains(err.Error(), "requires capability") {
		t.Errorf("err: %q", err.Error())
	}
}

func TestStageGate_NoRequireCap(t *testing.T) {
	st := &actorStage{Name: "x", RequireCap: nil}
	if err := stageGate(st, nil, ""); err != nil {
		t.Fatalf("expected unrestricted stage to pass, got %v", err)
	}
}

func TestStageGate_CapabilityWithScope(t *testing.T) {
	st := &actorStage{Name: "x", RequireCap: []string{"deploy.k8s:lg-test"}}
	cap := &capability{Purpose: "deploy-execution", Scope: []string{"deploy.k8s:lg-test", "deploy.pages:test"}}
	if err := stageGate(st, cap, ""); err != nil {
		t.Fatalf("expected pass with matching scope, got %v", err)
	}
}

func TestStageGate_CapabilityMissingScope(t *testing.T) {
	st := &actorStage{Name: "x", RequireCap: []string{"deploy.k8s:lg-test"}}
	cap := &capability{Purpose: "deploy-execution", Scope: []string{"deploy.cfWorker:other"}}
	err := stageGate(st, cap, "")
	if err == nil {
		t.Fatal("expected deny with non-overlapping scope")
	}
	if !strings.Contains(err.Error(), "lacks scope") {
		t.Errorf("err: %q", err.Error())
	}
}

func TestStageGate_CapabilityMultipleRequiredAllMatch(t *testing.T) {
	st := &actorStage{Name: "x", RequireCap: []string{"deploy.docker:lg-test", "deploy.ghcr:lg-test"}}
	cap := &capability{Purpose: "deploy-execution", Scope: []string{"deploy.docker:lg-test", "deploy.ghcr:lg-test", "deploy.k8s:lg-test"}}
	if err := stageGate(st, cap, ""); err != nil {
		t.Fatalf("expected pass when all required scopes present, got %v", err)
	}
}

func TestStageGate_CapabilityPartialMatch(t *testing.T) {
	st := &actorStage{Name: "x", RequireCap: []string{"deploy.docker:lg-test", "deploy.k8s:lg-test"}}
	cap := &capability{Purpose: "deploy-execution", Scope: []string{"deploy.docker:lg-test"}}
	err := stageGate(st, cap, "")
	if err == nil {
		t.Fatal("expected deny — only 1 of 2 required scopes present")
	}
}

func TestFilterStagesByName(t *testing.T) {
	stages := []actorStage{
		{Name: "a"}, {Name: "b"}, {Name: "c"},
	}
	out := filterStagesByName(stages, "b")
	if len(out) != 1 || out[0].Name != "b" {
		t.Errorf("got %v", out)
	}
	if len(filterStagesByName(stages, "missing")) != 0 {
		t.Error("expected empty for missing")
	}
}

func TestRemoveStages(t *testing.T) {
	stages := []actorStage{
		{Name: "a"}, {Name: "b"}, {Name: "c"},
	}
	out := removeStages(stages, []string{"b"})
	if len(out) != 2 || out[0].Name != "a" || out[1].Name != "c" {
		t.Errorf("got %v", out)
	}
}

func TestSanitizeCommand_DropsTokens(t *testing.T) {
	cmd := []string{"wrangler", "deploy", "--token", "abc123secret"}
	out := sanitizeCommand(cmd)
	if strings.Contains(out, "abc123secret") {
		t.Errorf("token leaked: %q", out)
	}
	if !strings.Contains(out, "***") {
		t.Errorf("expected redaction marker, got %q", out)
	}
}

func TestSplitTopLevelCommas(t *testing.T) {
	cases := []struct {
		in   string
		want int
	}{
		{`"a", "b", "c"`, 3},
		{`"a"`, 1},
		{``, 1}, // empty string still produces one empty element
	}
	for _, c := range cases {
		got := splitTopLevelCommas(c.in)
		if len(got) != c.want {
			t.Errorf("splitTopLevelCommas(%q): got %d parts, want %d", c.in, len(got), c.want)
		}
	}
}
