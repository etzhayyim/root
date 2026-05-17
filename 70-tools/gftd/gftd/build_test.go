package main

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestValidateMagatamaGovernanceImportRequiresGovernance(t *testing.T) {
	dir := t.TempDir()
	writeTestFile(t, filepath.Join(dir, "magatama.jsonld"), `{"@context":"https://etzhayyim.com/ns/magatama/v1","name":"test","nanoid":"t3st","component":{"path":"./app.wasm"}}`)
	writeTestFile(t, filepath.Join(dir, "wit", "world.wit"), "package gftd:test;\n\nworld component {\n  import wasi:http/outgoing-handler@0.2.0;\n}\n")

	err := validateMagatamaGovernanceImport(dir)
	if err == nil {
		t.Fatal("expected governance import validation error")
	}
	if !strings.Contains(err.Error(), "magatama:agent/governance@1.0.0") {
		t.Fatalf("unexpected error: %v", err)
	}
}

func TestValidateMagatamaGovernanceImportAcceptsDirectImport(t *testing.T) {
	dir := t.TempDir()
	writeTestFile(t, filepath.Join(dir, "magatama.jsonld"), `{"@context":"https://etzhayyim.com/ns/magatama/v1","name":"test","nanoid":"t3st","component":{"path":"./app.wasm"}}`)
	writeTestFile(t, filepath.Join(dir, "wit", "world.wit"), "package gftd:test;\n\nworld component {\n  import magatama:agent/governance@1.0.0;\n}\n")

	if err := validateMagatamaGovernanceImport(dir); err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
}

func TestValidateMagatamaGovernanceImportAcceptsMagatamaWorldInclude(t *testing.T) {
	dir := t.TempDir()
	writeTestFile(t, filepath.Join(dir, "magatama.jsonld"), `{"@context":"https://etzhayyim.com/ns/magatama/v1","name":"test","nanoid":"t3st","component":{"path":"./app.wasm"}}`)
	writeTestFile(t, filepath.Join(dir, "wit", "world.wit"), "package gftd:test;\n\nworld component {\n  include magatama:runtime/magatama-component@1.0.0;\n}\n")

	if err := validateMagatamaGovernanceImport(dir); err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
}

func TestValidateMagatamaGovernanceImportSkipsNonApp(t *testing.T) {
	dir := t.TempDir()
	writeTestFile(t, filepath.Join(dir, "wit", "world.wit"), "package gftd:test;\n\nworld component {}\n")

	if err := validateMagatamaGovernanceImport(dir); err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
}

func TestValidateMagatamaGovernanceImportMissingWorldIsIgnored(t *testing.T) {
	dir := t.TempDir()
	writeTestFile(t, filepath.Join(dir, "magatama.jsonld"), `{"@context":"https://etzhayyim.com/ns/magatama/v1","name":"test","nanoid":"t3st","component":{"path":"./app.wasm"}}`)

	if err := validateMagatamaGovernanceImport(dir); err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
}

func TestValidateMagatamaGovernanceImportReadError(t *testing.T) {
	dir := t.TempDir()
	writeTestFile(t, filepath.Join(dir, "magatama.jsonld"), `{"@context":"https://etzhayyim.com/ns/magatama/v1","name":"test","nanoid":"t3st","component":{"path":"./app.wasm"}}`)
	worldDir := filepath.Join(dir, "wit", "world.wit")
	if err := os.MkdirAll(worldDir, 0o755); err != nil {
		t.Fatalf("mkdir %s: %v", worldDir, err)
	}

	err := validateMagatamaGovernanceImport(dir)
	if err == nil || !strings.Contains(err.Error(), "read app world.wit") {
		t.Fatalf("unexpected error: %v", err)
	}
}


func TestFindGitRoot(t *testing.T) {
	root := t.TempDir()
	writeTestFile(t, filepath.Join(root, ".git", "keep"), "")
	nested := filepath.Join(root, "a", "b")
	if err := os.MkdirAll(nested, 0o755); err != nil {
		t.Fatalf("mkdir nested: %v", err)
	}

	got, err := findGitRoot(nested)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if got != root {
		t.Fatalf("got %q want %q", got, root)
	}
}

func TestFindGitRootNotFound(t *testing.T) {
	_, err := findGitRoot(t.TempDir())
	if err == nil || !strings.Contains(err.Error(), "no .git root found") {
		t.Fatalf("unexpected error: %v", err)
	}
}

func TestDetectWITVersionAndValidate(t *testing.T) {
	dir := t.TempDir()
	writeTestFile(t, filepath.Join(dir, "world.wit"), "package magatama:runtime@1.2.3;\n")

	got, err := detectWITVersion(dir)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if got != "1.2.3" {
		t.Fatalf("got %q", got)
	}
	if err := validateWITVersion(dir); err != nil {
		t.Fatalf("validateWITVersion: %v", err)
	}
}

func TestDetectWITVersionErrors(t *testing.T) {
	t.Run("missing package", func(t *testing.T) {
		dir := t.TempDir()
		writeTestFile(t, filepath.Join(dir, "world.wit"), "package gftd:test;\n")
		_, err := detectWITVersion(dir)
		if err == nil || !strings.Contains(err.Error(), "cannot find 'package magatama:runtime@...'") {
			t.Fatalf("unexpected error: %v", err)
		}
	})

	t.Run("empty version", func(t *testing.T) {
		dir := t.TempDir()
		writeTestFile(t, filepath.Join(dir, "world.wit"), "package magatama:runtime@;\n")
		_, err := detectWITVersion(dir)
		if err == nil || !strings.Contains(err.Error(), "empty version") {
			t.Fatalf("unexpected error: %v", err)
		}
	})
}

func TestValidateNoCORSHeaders(t *testing.T) {
	dir := t.TempDir()
	writeTestFile(t, filepath.Join(dir, "main.go"), `package main
func main() {
	_ = "Access-Control-Allow-Origin"
}
`)

	err := validateNoCORSHeaders(dir)
	if err == nil || !strings.Contains(err.Error(), "cors guard") {
		t.Fatalf("unexpected error: %v", err)
	}
}

func TestValidateNoCORSHeadersWithoutMainGo(t *testing.T) {
	if err := validateNoCORSHeaders(t.TempDir()); err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
}

func TestRunBuildAllowsTSNativeWorkerWithoutComponentWasm(t *testing.T) {
	root := t.TempDir()
	writeTestFile(t, filepath.Join(root, ".git", "keep"), "")
	writeTestFile(t, filepath.Join(root, "packages", "contract", "wit", "world.wit"), "package magatama:runtime@1.0.0;\n")

	compDir := filepath.Join(root, "component")
	writeTestFile(t, filepath.Join(compDir, "magatama.jsonld"), `{
  "@context":"https://etzhayyim.com/ns/magatama/v1",
  "name":"test-worker",
  "nanoid":"t3stw0rk",
  "runtimeType":"worker",
  "performerType":"service",
  "component": {},
  "profile":{
    "displayName":"Test Worker",
    "description":"Worker app for build test",
    "capabilities":["query"]
  },
  "governance":{"classification":"internal","raci":"responsible"},
  "convoSystemPrompt":"test prompt",
  "triggers":{"subscribeRepos":{"collections":["app.bsky.feed.post"]}}
}`)
	writeTestFile(t, filepath.Join(compDir, "wit", "world.wit"), `package gftd:test;

world component {
  import magatama:agent/governance@1.0.0;
}
`)
	writeTestFile(t, filepath.Join(compDir, "src", "app.ts"), `import { createWorkerExport } from "@gftd/magatama-host-sdk";
export default createWorkerExport();
`)

	cwd, err := os.Getwd()
	if err != nil {
		t.Fatalf("getwd: %v", err)
	}
	if err := os.Chdir(root); err != nil {
		t.Fatalf("chdir root: %v", err)
	}
	t.Cleanup(func() {
		_ = os.Chdir(cwd)
	})

	if err := runBuild([]string{"--dir", compDir, "--deps-score=false", "--no-svelte", "--no-lint"}); err != nil {
		t.Fatalf("runBuild returned error for TS Native worker without component.wasm: %v", err)
	}
}


func writeTestFile(t *testing.T, path, contents string) {
	t.Helper()
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		t.Fatalf("mkdir %s: %v", path, err)
	}
	if err := os.WriteFile(path, []byte(contents), 0o644); err != nil {
		t.Fatalf("write %s: %v", path, err)
	}
}
