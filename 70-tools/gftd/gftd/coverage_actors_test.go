package main

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestApplyStandardRuleAddsRequiredFields(t *testing.T) {
	result := actorHealResult{
		DID:             "did:web:test.etzhayyim.com",
		Name:            "test",
		GeneratedValues: map[string]string{"convo_system_prompt": "prompt", "capabilities": `["graph.query"]`},
	}
	actor := actorCoverageRow{
		DID: "did:web:test.etzhayyim.com",
	}

	applyStandardRule(&result, actor)

	for _, field := range []string{
		"standard_rule",
		"standard_status",
		"required_loops",
		"required_collections",
		"compliance_docs",
		"heartbeat_required",
		"domain_knowledge_required",
		"convo_system_prompt",
		"capabilities",
		"performer_type",
		"operator",
	} {
		if _, ok := result.GeneratedValues[field]; !ok {
			t.Fatalf("missing generated value for %s", field)
		}
	}

	if got := result.GeneratedValues["standard_rule"]; !strings.Contains(got, "per-did-kyumei-shinka-autonomy") {
		t.Fatalf("unexpected standard_rule: %s", got)
	}
	if got := result.GeneratedValues["required_loops"]; !strings.Contains(got, "kyumei") || !strings.Contains(got, "domain-knowledge") {
		t.Fatalf("unexpected required_loops: %s", got)
	}
}

func TestWriteHealResultToLocalManifest(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "actor-manifest.jsonld")
	original := map[string]any{
		"@id":  "did:web:test.etzhayyim.com",
		"name": "test",
		"profile": map[string]any{
			"operator": "old.example",
		},
	}
	data, err := json.Marshal(original)
	if err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(path, data, 0644); err != nil {
		t.Fatal(err)
	}

	err = writeHealResultToLocalManifest(path, map[string]string{
		"convo_system_prompt":       "prompt",
		"capabilities":              `["graph.query","agent.chat"]`,
		"performer_type":            "service",
		"operator":                  "amanomibashira",
		"standard_rule":             "per-did-kyumei-shinka-autonomy@2026-04-13",
		"required_loops":            `["shinka","koji","kyumei","domain-knowledge"]`,
		"required_collections":      `["ai.gftd.apps.standard.shinkaEvolution","ai.gftd.apps.standard.shinkaKnowledge"]`,
		"compliance_docs":           `["90-docs/rules/compliance/per-did-kyumei-shinka-autonomy.md"]`,
		"heartbeat_required":        "true",
		"domain_knowledge_required": "true",
	})
	if err != nil {
		t.Fatal(err)
	}

	updatedData, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	var updated map[string]any
	if err := json.Unmarshal(updatedData, &updated); err != nil {
		t.Fatal(err)
	}

	if got := updated["convoSystemPrompt"]; got != "prompt" {
		t.Fatalf("unexpected convoSystemPrompt: %#v", got)
	}
	if got := updated["performerType"]; got != "service" {
		t.Fatalf("unexpected performerType: %#v", got)
	}
	if got := updated["standardRule"]; got == nil {
		t.Fatalf("missing standardRule")
	}
	if got := updated["heartbeatRequired"]; got != true {
		t.Fatalf("unexpected heartbeatRequired: %#v", got)
	}
	profile, _ := updated["profile"].(map[string]any)
	if got := profile["operator"]; got != "amanomibashira" {
		t.Fatalf("unexpected profile.operator: %#v", got)
	}
	caps, _ := updated["capabilities"].([]any)
	if len(caps) != 2 {
		t.Fatalf("unexpected capabilities: %#v", updated["capabilities"])
	}
}
