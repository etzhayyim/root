package main

import (
	"os"
	"path/filepath"
	"testing"
)

func TestShIsGenerated(t *testing.T) {
	tests := []struct {
		path string
		want bool
	}{
		{"projects/foo/wasm/comp/main.go", false},
		{"projects/foo/wasm/comp/gen/wasi/sockets/udp/udp.wit.go", true},
		{"projects/foo/wasm/comp/proto/service.pb.go", true},
		{"packages/protocol/wproto/src/lib.rs", false},
		{"packages/protocol/wproto/src/generated/types.wit.rs", true},
		{"infra/cloudflare/workers/atproto/src/handler.ts", false},
		{"projects/foo/wasm/comp/core.component.js", true},
	}
	for _, tt := range tests {
		got := shIsGenerated(tt.path)
		if got != tt.want {
			t.Errorf("shIsGenerated(%q) = %v, want %v", tt.path, got, tt.want)
		}
	}
}

func TestShNormLine(t *testing.T) {
	tests := []struct {
		input    string
		expected string
	}{
		{"  **Hello** `world`  ", "hello world"},
		{"| foo | bar |", "| foo | bar |"},
		{"  multiple   spaces   here  ", "multiple spaces here"},
	}
	for _, tt := range tests {
		got := shNormLine(tt.input)
		if got != tt.expected {
			t.Errorf("shNormLine(%q) = %q, want %q", tt.input, got, tt.expected)
		}
	}
}

func TestShNormFuncBody(t *testing.T) {
	body := `{
		// comment
		x := 1
		y := 2
		return x + y
	}`
	norm := shNormFuncBody(body)
	if norm == "" {
		t.Error("expected non-empty normalized body")
	}
	// Should not contain comment lines
	if contains(norm, "// comment") {
		t.Error("normalized body should strip comments")
	}
}

func TestShFindMatchingBrace(t *testing.T) {
	tests := []struct {
		input string
		pos   int
		want  int
	}{
		{"{}", 0, 1},
		{`{ { } }`, 0, 6},
		{`{ "}" }`, 0, 6},
		{`{ no close`, 0, -1},
	}
	for _, tt := range tests {
		got := shFindMatchingBrace(tt.input, tt.pos)
		if got != tt.want {
			t.Errorf("shFindMatchingBrace(%q, %d) = %d, want %d", tt.input, tt.pos, got, tt.want)
		}
	}
}

func TestShStripJsoncComments(t *testing.T) {
	input := []byte(`{
  // line comment
  "key": "value", /* block */
  "key2": "val//ue"
}`)
	out := shStripJsoncComments(input)
	s := string(out)
	if contains(s, "line comment") {
		t.Error("should strip line comments")
	}
	if contains(s, "block") {
		t.Error("should strip block comments")
	}
	if !contains(s, `"val//ue"`) {
		t.Error("should preserve comments inside strings")
	}
}

func TestShCap(t *testing.T) {
	if shCap(-5) != 0 {
		t.Error("shCap(-5) should be 0")
	}
	if shCap(150) != 100 {
		t.Error("shCap(150) should be 100")
	}
	if shCap(75.55) != 75.6 {
		t.Errorf("shCap(75.55) = %.1f, want 75.6", shCap(75.55))
	}
}

func TestShDeduplicateItems(t *testing.T) {
	items := []shannonItem{
		{Path: "a.go", Kind: "test", Detail: "dup"},
		{Path: "a.go", Kind: "test", Detail: "dup"},
		{Path: "b.go", Kind: "test", Detail: "other"},
	}
	result := shDeduplicateItems(items)
	if len(result) != 2 {
		t.Errorf("expected 2 items after dedup, got %d", len(result))
	}
}

func TestShExtractGoFuncHashes(t *testing.T) {
	src := []byte(`package main

func add(a, b int) int {
	return a + b
}

func sub(a, b int) int {
	return a - b
}
`)
	results := shExtractGoFuncHashes("test.go", src)
	if len(results) != 2 {
		t.Fatalf("expected 2 functions, got %d", len(results))
	}
	if results[0].name != "add" {
		t.Errorf("expected first func 'add', got %q", results[0].name)
	}
	// Different bodies should produce different hashes
	if results[0].hash == results[1].hash {
		t.Error("different functions should have different hashes")
	}
}

func TestShExtractGoFuncHashes_Identical(t *testing.T) {
	src := []byte(`package main

func foo() int {
	x := 1
	y := 2
	return x + y
}

func bar() int {
	x := 1
	y := 2
	return x + y
}
`)
	results := shExtractGoFuncHashes("test.go", src)
	if len(results) != 2 {
		t.Fatalf("expected 2 functions, got %d", len(results))
	}
	if results[0].hash != results[1].hash {
		t.Error("identical function bodies should have same hash")
	}
}

func TestShExtractRustFuncHashes(t *testing.T) {
	src := []byte(`pub fn process(data: &[u8]) -> Vec<u8> {
    let mut result = Vec::new();
    for b in data {
        result.push(b + 1);
    }
    result
}

fn helper() -> i32 {
    42
}
`)
	results := shExtractRustFuncHashes("lib.rs", src)
	if len(results) < 2 {
		t.Fatalf("expected at least 2 functions, got %d", len(results))
	}
}

func TestShExtractTSFuncHashes(t *testing.T) {
	src := []byte(`export async function handleRequest(req: Request): Promise<Response> {
    const url = new URL(req.url);
    return new Response(url.pathname);
}

function helper(): string {
    return "hello";
}
`)
	results := shExtractTSFuncHashes("handler.ts", src)
	if len(results) < 2 {
		t.Fatalf("expected at least 2 functions, got %d", len(results))
	}
}

func TestShCheckClaudeMdDuplication(t *testing.T) {
	tmp := t.TempDir()

	// Create root CLAUDE.md
	os.WriteFile(filepath.Join(tmp, "CLAUDE.md"), []byte(`# Root
This is a very important rule that must be followed at all times in every situation
`), 0644)

	// Create child CLAUDE.md with duplicated content
	os.MkdirAll(filepath.Join(tmp, "child"), 0755)
	os.WriteFile(filepath.Join(tmp, "child", "CLAUDE.md"), []byte(`# Child
This is a very important rule that must be followed at all times in every situation
Some unique child content that is not in the root at all and is long enough
`), 0644)

	check := shCheckClaudeMdDuplication(tmp)
	if check.Violations == 0 {
		t.Error("expected violations for duplicated CLAUDE.md content")
	}
	if check.Score >= 100 {
		t.Error("score should be less than 100 with duplicates")
	}
}

func TestShCheckDeadCodeEntropy_Go(t *testing.T) {
	tmp := t.TempDir()

	// Create a Go file with an empty function
	projectDir := filepath.Join(tmp, "projects", "test", "wasm", "comp")
	os.MkdirAll(projectDir, 0755)
	os.WriteFile(filepath.Join(projectDir, "main.go"), []byte(`package main

func liveFunc() int {
	return 42
}

func deadFunc() {
}

func stubFunc() {
	panic("not implemented")
}
`), 0644)

	check := shCheckDeadCodeEntropy(tmp)
	if check.Violations < 2 {
		t.Errorf("expected at least 2 dead functions, got %d", check.Violations)
	}
}

func TestShCheckWitTypeDuplication(t *testing.T) {
	tmp := t.TempDir()

	// Create WIT files with duplicate type
	witDir1 := filepath.Join(tmp, "packages", "contract", "wit")
	os.MkdirAll(witDir1, 0755)
	os.WriteFile(filepath.Join(witDir1, "types.wit"), []byte(`
record my-config {
    name: string,
}
enum my-status {
    active,
    inactive,
}
`), 0644)

	// Duplicate in project
	projWit := filepath.Join(tmp, "projects", "test-app", "wit")
	os.MkdirAll(projWit, 0755)
	os.WriteFile(filepath.Join(projWit, "types.wit"), []byte(`
record my-config {
    name: string,
    extra: string,
}
`), 0644)

	check := shCheckWitTypeDuplication(tmp)
	if check.Violations < 1 {
		t.Errorf("expected at least 1 duplicated WIT type, got %d", check.Violations)
	}
}

func TestShCheckConfigRedundancy(t *testing.T) {
	tmp := t.TempDir()

	config := `{
  "vars": {
    "ENVIRONMENT": "production",
    "SHARED_KEY": "abc123"
  }
}`
	// Create 4 identical wrangler.jsonc files (threshold is 3+)
	for _, dir := range []string{"a", "b", "c", "d"} {
		d := filepath.Join(tmp, "projects", dir)
		os.MkdirAll(d, 0755)
		os.WriteFile(filepath.Join(d, "wrangler.jsonc"), []byte(config), 0644)
	}

	check := shCheckConfigRedundancy(tmp)
	if check.Violations < 1 {
		t.Errorf("expected config redundancy violations, got %d", check.Violations)
	}
}

func TestBuildShannonReport(t *testing.T) {
	checks := []shannonCheck{
		{Name: "claude_md_duplication", Score: 80, Violations: 5},
		{Name: "code_clone_cross", Score: 90, Violations: 2},
		{Name: "collection_write_fan", Score: 100, Violations: 0},
		{Name: "wit_type_duplication", Score: 95, Violations: 1},
		{Name: "config_redundancy", Score: 100, Violations: 0},
		{Name: "dead_code_entropy", Score: 85, Violations: 3},
		{Name: "doc_code_drift", Score: 100, Violations: 0},
		{Name: "rust_duplication", Score: 92, Violations: 1},
	}

	report := buildShannonReport(checks, 10)

	if report.OverallScore <= 0 || report.OverallScore > 100 {
		t.Errorf("overall score out of range: %.1f", report.OverallScore)
	}
	if report.RedundancyRate < 0 || report.RedundancyRate > 1 {
		t.Errorf("redundancy rate out of range: %.3f", report.RedundancyRate)
	}
	if len(report.Checks) != 8 {
		t.Errorf("expected 8 checks, got %d", len(report.Checks))
	}
	// Verify weights are assigned
	for _, c := range report.Checks {
		if c.Weight <= 0 {
			t.Errorf("check %s has no weight", c.Name)
		}
	}
}

func contains(s, substr string) bool {
	return len(s) >= len(substr) && (s == substr || len(s) > 0 && containsHelper(s, substr))
}

func containsHelper(s, substr string) bool {
	for i := 0; i <= len(s)-len(substr); i++ {
		if s[i:i+len(substr)] == substr {
			return true
		}
	}
	return false
}
