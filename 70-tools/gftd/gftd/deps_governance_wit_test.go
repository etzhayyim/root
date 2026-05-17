package main

import (
	"os"
	"path/filepath"
	"testing"
)

func TestEvaluateGovernanceWITTSApp(t *testing.T) {
	dir := t.TempDir()
	if err := os.MkdirAll(filepath.Join(dir, "wit"), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.MkdirAll(filepath.Join(dir, "src"), 0o755); err != nil {
		t.Fatal(err)
	}
	world := `package magatama:runtime@1.0.0;

world magatama-component {
    include magatama:runtime/magatama-component@1.0.0;
    import magatama:identity/capability@1.0.0;
    import magatama:agent/governance@1.0.0;
    import magatama:governance/raci@1.0.0;
    import magatama:governance/rbac@1.0.0;
    import magatama:governance/governance@1.0.0;
    import magatama:governance/traceability@1.0.0;
}`
	app := `const app = new App({ id: "demo", name: "Demo" })
  .command("create_demo", handler,
    responsible(AssigneeKind.OrgRole, "operator"),
    requireApproval(DecisionClass.B, 1, "medium"),
    withBPMNTask("task-1"),
  )
  .build()
`
	manifest := `{
  "governance": {
    "raci": "accountable",
    "classification": "restricted",
    "complianceFrameworks": ["NIST-CSF"],
    "roles": [{"role": "owner", "did": "did:web:demo.etzhayyim.com"}]
  }
}`
	if err := os.WriteFile(filepath.Join(dir, "wit", "world.wit"), []byte(world), 0o644); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(dir, "src", "app.ts"), []byte(app), 0o644); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(dir, "magatama.jsonld"), []byte(manifest), 0o644); err != nil {
		t.Fatal(err)
	}

	report, err := evaluateGovernanceWIT(dir)
	if err != nil {
		t.Fatalf("evaluateGovernanceWIT: %v", err)
	}
	if report.Verdict != "suitable" {
		t.Fatalf("verdict = %s, want suitable", report.Verdict)
	}
	if report.Score < 90 {
		t.Fatalf("score = %.1f, want >= 90", report.Score)
	}
	if report.Implementation.ExplicitGovernedCount != 1 {
		t.Fatalf("explicit governed count = %d, want 1", report.Implementation.ExplicitGovernedCount)
	}
}

func TestEvaluateGovernanceWITMissingGovernanceImport(t *testing.T) {
	dir := t.TempDir()
	if err := os.MkdirAll(filepath.Join(dir, "wit"), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.MkdirAll(filepath.Join(dir, "src"), 0o755); err != nil {
		t.Fatal(err)
	}
	world := `package magatama:runtime@1.0.0;
world magatama-component {
    import magatama:core/log@1.0.0;
}`
	app := `const app = new App({ id: "demo", name: "Demo" }).command("list_demo", handler).build()`
	manifest := `{"governance":{"raci":"responsible","classification":"internal","complianceFrameworks":[]}}`
	if err := os.WriteFile(filepath.Join(dir, "wit", "world.wit"), []byte(world), 0o644); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(dir, "src", "app.ts"), []byte(app), 0o644); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(dir, "magatama.jsonld"), []byte(manifest), 0o644); err != nil {
		t.Fatal(err)
	}

	report, err := evaluateGovernanceWIT(dir)
	if err != nil {
		t.Fatalf("evaluateGovernanceWIT: %v", err)
	}
	if report.World.HasGovernance {
		t.Fatal("expected governance import to be absent")
	}
	if report.Verdict != "not-suitable" {
		t.Fatalf("verdict = %s, want not-suitable", report.Verdict)
	}
	if len(report.Findings) == 0 || report.Findings[0].Severity != "critical" {
		t.Fatalf("expected critical finding, got %+v", report.Findings)
	}
}

func TestEvaluateGovernanceWITRuntimeIncludeCountsAsGovernance(t *testing.T) {
	dir := t.TempDir()
	if err := os.MkdirAll(filepath.Join(dir, "wit"), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.MkdirAll(filepath.Join(dir, "src"), 0o755); err != nil {
		t.Fatal(err)
	}
	world := `package gftd:test;

world component {
    include magatama:runtime/magatama-component@1.0.0;
    export gftd:test/provider@1.0.0;
}`
	app := `const app = new App({ id: "demo", name: "Demo" }).command("list_demo", handler).build()`
	manifest := `{"governance":{"raci":"accountable","classification":"restricted","complianceFrameworks":["NIST-CSF"]}}`
	if err := os.WriteFile(filepath.Join(dir, "wit", "world.wit"), []byte(world), 0o644); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(dir, "src", "app.ts"), []byte(app), 0o644); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(dir, "magatama.jsonld"), []byte(manifest), 0o644); err != nil {
		t.Fatal(err)
	}

	report, err := evaluateGovernanceWIT(dir)
	if err != nil {
		t.Fatalf("evaluateGovernanceWIT: %v", err)
	}
	if !report.World.HasRuntimeInclude || !report.World.HasGovernance {
		t.Fatalf("runtime include should satisfy governance imports: %+v", report.World)
	}
	for _, f := range report.Findings {
		if f.Code == "wit_governance_missing" || f.Code == "wit_import_recommended" {
			t.Fatalf("unexpected WIT finding with runtime include: %+v", f)
		}
	}
}
