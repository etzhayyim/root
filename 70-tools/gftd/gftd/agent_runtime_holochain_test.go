package main

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestBuildHolochainRuntimePlan(t *testing.T) {
	plan := buildHolochainRuntimePlan(holochainRuntimePlanInput{
		AgentDID:       "did:web:kami-agent.etzhayyim.com",
		HAppName:       "gftd-agent-actor-runtime",
		HAppURI:        "ipfs://bafy-happ",
		DNAHash:        "uhC0kagentactorruntime",
		RoleName:       "agent_actor_runtime",
		ZomeName:       "actor_runtime",
		ConductorImage: "ghcr.io/etzhayyim/holochain-agent-runtime:experimental",
		Cluster:        "test-cluster",
		Namespace:      "agent-runtime-holochain",
		Workload:       "holochain-agent-runtime",
	})
	if plan.RuntimeKind != "holochain" {
		t.Fatalf("runtime kind = %q", plan.RuntimeKind)
	}
	if plan.HApp.DNAHash == "" || plan.HApp.RoleName != "agent_actor_runtime" {
		t.Fatalf("missing hApp binding: %+v", plan.HApp)
	}
	if !strings.Contains(plan.Bindings.CommandFunction, "commit_actor_event") {
		t.Fatalf("command binding missing zome function: %+v", plan.Bindings)
	}
	if !isBytes32Hex(plan.Registration["artifactId"]) {
		t.Fatalf("artifactId must be bytes32 hex: %+v", plan.Registration)
	}
	for _, check := range plan.Verification.Checks {
		if !check.OK {
			t.Fatalf("smoke check failed: %+v", check)
		}
	}
}

func TestAgentRuntimeHolochainPlanCommand(t *testing.T) {
	dir := t.TempDir()
	out := filepath.Join(dir, "holochain-plan.json")
	if err := runAgentRuntimeHolochainPlan([]string{
		"--agent-did", "did:web:kami-agent.etzhayyim.com",
		"--happ-uri", "ipfs://bafy-happ",
		"--happ-sha256", "0x" + strings.Repeat("a", 64),
		"--dna-hash", "uhC0kagentactorruntime",
		"--cluster", "test-cluster",
		"--out", out,
	}); err != nil {
		t.Fatal(err)
	}
	data, err := os.ReadFile(out)
	if err != nil {
		t.Fatal(err)
	}
	var plan holochainRuntimePlan
	if err := json.Unmarshal(data, &plan); err != nil {
		t.Fatal(err)
	}
	if plan.Schema != holochainAgentRuntimePlanSchema {
		t.Fatalf("schema = %q", plan.Schema)
	}
	if plan.HApp.HAppSHA256 == "" {
		t.Fatalf("happ sha was not preserved: %+v", plan.HApp)
	}
	if plan.Conductor.Cluster != "test-cluster" {
		t.Fatalf("cluster = %q", plan.Conductor.Cluster)
	}
}

func TestAgentRuntimeHolochainPlanRejectsDefaultNamespace(t *testing.T) {
	err := runAgentRuntimeHolochainPlan([]string{
		"--agent-did", "did:web:kami-agent.etzhayyim.com",
		"--happ-uri", "ipfs://bafy-happ",
		"--dna-hash", "uhC0kagentactorruntime",
		"--namespace", "default",
	})
	if err == nil {
		t.Fatal("default namespace should be rejected")
	}
}
