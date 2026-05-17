package main

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestSGParseFile_GoAnnotations(t *testing.T) {
	root := t.TempDir()
	mainGo := filepath.Join(root, "projects", "ai-gftd-project-news", "wasm", "news-app", "main.go")
	writeTestFile(t, mainGo, `package main

// @gftd:import com-atproto:repo/repo@1.0.0
// @gftd:import magatama:contract/agreement@1.0.0
// @gftd:authority sovereign/jpn, treaty/wto
// @gftd:sensitivity confidential
// @gftd:rule no-batch-polling, no-dual-write
// @gftd:owner did:web:news.etzhayyim.com
// @gftd:ref docs/260324-news-wrpc-stream-reactive-design.md

func (app *App) handleArticle(commit wCommit) {
	// @gftd:calls did:web:i18n.etzhayyim.com#translate
	// @gftd:writes ai.gftd.apps.news.translated_article
	magatama.AppBskyFeedPostAs(did, text, opts)
}

func (app *App) readLatest() {
	// @gftd:reads ai.gftd.apps.news.article
}
`)

	rel := "projects/ai-gftd-project-news/wasm/news-app/main.go"
	nodes := sgParseFile(mainGo, rel, "go")
	if len(nodes) == 0 {
		t.Fatal("expected nodes, got 0")
	}

	// File-level node
	fileNode := nodes[0]
	if fileNode.FuncName != "" {
		t.Fatalf("expected file-level node, got func %q", fileNode.FuncName)
	}
	if len(fileNode.Imports) != 2 {
		t.Fatalf("imports = %d, want 2", len(fileNode.Imports))
	}
	if fileNode.Imports[0] != "com-atproto:repo/repo@1.0.0" {
		t.Fatalf("imports[0] = %q", fileNode.Imports[0])
	}
	if len(fileNode.Authorities) != 2 {
		t.Fatalf("authorities = %d, want 2", len(fileNode.Authorities))
	}
	if fileNode.Sensitivity != "confidential" {
		t.Fatalf("sensitivity = %q, want confidential", fileNode.Sensitivity)
	}
	if len(fileNode.Rules) != 2 {
		t.Fatalf("rules = %d, want 2", len(fileNode.Rules))
	}
	if fileNode.Owner != "did:web:news.etzhayyim.com" {
		t.Fatalf("owner = %q", fileNode.Owner)
	}

	// Function-level nodes
	var handleNode, readNode *sgSourceNode
	for i := range nodes {
		if nodes[i].FuncName == "handleArticle" {
			handleNode = &nodes[i]
		}
		if nodes[i].FuncName == "readLatest" {
			readNode = &nodes[i]
		}
	}

	if handleNode == nil {
		t.Fatal("handleArticle node not found")
	}
	if len(handleNode.Calls) != 1 || handleNode.Calls[0] != "did:web:i18n.etzhayyim.com#translate" {
		t.Fatalf("calls = %v", handleNode.Calls)
	}
	if len(handleNode.Writes) != 1 || handleNode.Writes[0] != "ai.gftd.apps.news.translated_article" {
		t.Fatalf("writes = %v", handleNode.Writes)
	}

	if readNode == nil {
		t.Fatal("readLatest node not found")
	}
	if len(readNode.Reads) != 1 || readNode.Reads[0] != "ai.gftd.apps.news.article" {
		t.Fatalf("reads = %v", readNode.Reads)
	}
}

func TestSGParseFile_RustAnnotations(t *testing.T) {
	root := t.TempDir()
	libRs := filepath.Join(root, "src", "lib.rs")
	writeTestFile(t, libRs, `// @gftd:import magatama:trust/trust-score@1.0.0
// @gftd:visibility internal

pub fn verify_trust(did: &str) -> TrustLevel {
	// @gftd:reads trust_score
}
`)
	nodes := sgParseFile(libRs, "src/lib.rs", "rust")
	if len(nodes) < 2 {
		t.Fatalf("expected >=2 nodes, got %d", len(nodes))
	}
	found := false
	for _, n := range nodes {
		if n.FuncName == "verify_trust" {
			found = true
			if len(n.Reads) != 1 || n.Reads[0] != "trust_score" {
				t.Fatalf("reads = %v", n.Reads)
			}
		}
	}
	if !found {
		t.Fatal("verify_trust not found")
	}
}

func TestSGParseFile_TSAnnotations(t *testing.T) {
	root := t.TempDir()
	indexTs := filepath.Join(root, "src", "index.ts")
	writeTestFile(t, indexTs, `// @gftd:import magatama:browser/automation@1.0.0
// @gftd:contract service-agreement/oshi-runway

export async function renderVideo(params: RenderParams) {
	// @gftd:calls did:web:murakumo.etzhayyim.com#inference
}
`)
	nodes := sgParseFile(indexTs, "src/index.ts", "ts")
	if len(nodes) < 2 {
		t.Fatalf("expected >=2 nodes, got %d", len(nodes))
	}
	found := false
	for _, n := range nodes {
		if n.FuncName == "renderVideo" {
			found = true
			if len(n.Calls) != 1 || n.Calls[0] != "did:web:murakumo.etzhayyim.com#inference" {
				t.Fatalf("calls = %v", n.Calls)
			}
		}
	}
	if !found {
		t.Fatal("renderVideo not found")
	}
}

func TestSGInferAppDID(t *testing.T) {
	tests := []struct {
		path string
		want string
	}{
		{"projects/ai-gftd-project-news/wasm/news-app/main.go", "did:web:news.etzhayyim.com"},
		{"projects/ai-gftd-project-oshi/wasm/oshi-vibes/src/lib.rs", "did:web:oshi.etzhayyim.com"},
		{"20-actors/magatama/src/lib.rs", ""},
	}
	for _, tt := range tests {
		got := sgInferAppDID(tt.path)
		if got != tt.want {
			t.Errorf("sgInferAppDID(%q) = %q, want %q", tt.path, got, tt.want)
		}
	}
}

func TestSGViolations_NoDualWrite(t *testing.T) {
	root := t.TempDir()
	mainGo := filepath.Join(root, "projects", "ai-gftd-project-demo", "wasm", "demo-app", "main.go")
	writeTestFile(t, mainGo, `package main

func handle() {
	// @gftd:rule no-dual-write
	// @gftd:writes collection_a
	// @gftd:writes collection_b
}
`)
	graph := sgScanWorkspace(root)
	report := sgDetectViolations(root, &graph)

	found := false
	for _, v := range report.Violations {
		if v.Rule == "rule-no-dual-write" {
			found = true
		}
	}
	if !found {
		t.Fatal("expected rule-no-dual-write violation")
	}
}

func TestSGViolations_DeadSupersedes(t *testing.T) {
	root := t.TempDir()
	mainGo := filepath.Join(root, "projects", "ai-gftd-project-demo", "wasm", "demo-app", "main.go")
	writeTestFile(t, mainGo, `package main
// @gftd:supersedes 20-actors/magatama/dead-file.rs
`)
	graph := sgScanWorkspace(root)
	report := sgDetectViolations(root, &graph)

	found := false
	for _, v := range report.Violations {
		if v.Rule == "dead-supersedes" {
			found = true
		}
	}
	if !found {
		t.Fatal("expected dead-supersedes violation")
	}
}

func TestSGViolations_ShannonRedundancy(t *testing.T) {
	root := t.TempDir()
	// Two apps writing to same collection
	app1 := filepath.Join(root, "projects", "ai-gftd-project-news", "wasm", "news-app", "main.go")
	writeTestFile(t, app1, `package main
func write1() {
	// @gftd:writes shared_collection
}
`)
	app2 := filepath.Join(root, "projects", "ai-gftd-project-handotai", "wasm", "handotai-app", "main.go")
	writeTestFile(t, app2, `package main
func write2() {
	// @gftd:writes shared_collection
}
`)

	graph := sgScanWorkspace(root)
	report := sgDetectViolations(root, &graph)

	found := false
	for _, v := range report.Violations {
		if v.Rule == "shannon-redundancy" {
			found = true
			if !strings.Contains(v.Detail, "shared_collection") {
				t.Fatalf("unexpected detail: %s", v.Detail)
			}
		}
	}
	if !found {
		t.Fatal("expected shannon-redundancy violation")
	}
}

func TestSGViolations_DeadRef(t *testing.T) {
	root := t.TempDir()
	mainGo := filepath.Join(root, "projects", "ai-gftd-project-demo", "wasm", "demo-app", "main.go")
	writeTestFile(t, mainGo, `package main
// @gftd:ref docs/nonexistent-design.md
`)
	graph := sgScanWorkspace(root)
	report := sgDetectViolations(root, &graph)

	found := false
	for _, v := range report.Violations {
		if v.Rule == "dead-ref" {
			found = true
		}
	}
	if !found {
		t.Fatal("expected dead-ref violation")
	}
}

func TestSGSqlGeneration(t *testing.T) {
	root := t.TempDir()
	mainGo := filepath.Join(root, "projects", "ai-gftd-project-news", "wasm", "news-app", "main.go")
	writeTestFile(t, mainGo, `package main
// @gftd:import com-atproto:repo/repo@1.0.0
// @gftd:owner did:web:news.etzhayyim.com

func handle() {
	// @gftd:calls did:web:i18n.etzhayyim.com#translate
	// @gftd:writes ai.gftd.apps.news.article
}
`)

	graph := sgScanWorkspace(root)
	stmts := sgGenerateSql(&graph)

	if len(stmts) == 0 {
		t.Fatal("expected sql statements")
	}

	// Check for MERGE Source, IMPORTS, INVOKES, WRITES_TO
	hasSource := false
	hasImports := false
	hasInvokes := false
	hasWrites := false
	for _, s := range stmts {
		if strings.Contains(s, "MERGE (s:Source") {
			hasSource = true
		}
		if strings.Contains(s, "[:IMPORTS]") {
			hasImports = true
		}
		if strings.Contains(s, "[:INVOKES") {
			hasInvokes = true
		}
		if strings.Contains(s, "[:WRITES_TO]") {
			hasWrites = true
		}
	}
	if !hasSource {
		t.Fatal("missing Source MERGE")
	}
	if !hasImports {
		t.Fatal("missing IMPORTS edge")
	}
	if !hasInvokes {
		t.Fatal("missing INVOKES edge")
	}
	if !hasWrites {
		t.Fatal("missing WRITES_TO edge")
	}
}

func TestSGDotGeneration(t *testing.T) {
	root := t.TempDir()
	mainGo := filepath.Join(root, "projects", "ai-gftd-project-news", "wasm", "news-app", "main.go")
	writeTestFile(t, mainGo, `package main
// @gftd:owner did:web:news.etzhayyim.com

func handle() {
	// @gftd:calls did:web:i18n.etzhayyim.com#translate
}
`)

	graph := sgScanWorkspace(root)
	dot := sgGenerateDot(&graph)

	if !strings.Contains(dot, "digraph source_graph") {
		t.Fatal("missing digraph header")
	}
	if !strings.Contains(dot, "calls") {
		t.Fatal("missing calls edge")
	}
}

func TestSGScanWorkspace_EmptyDir(t *testing.T) {
	root := t.TempDir()
	graph := sgScanWorkspace(root)
	if graph.TotalFiles != 0 {
		t.Fatalf("total_files = %d, want 0", graph.TotalFiles)
	}
}

func TestSGScore_NoAnnotations(t *testing.T) {
	root := t.TempDir()
	// Create a main.go without annotations
	mainGo := filepath.Join(root, "projects", "ai-gftd-project-demo", "wasm", "demo-app", "main.go")
	writeTestFile(t, mainGo, `package main
func main() {}
`)
	graph := sgScanWorkspace(root)
	report := sgDetectViolations(root, &graph)

	// 0 annotated out of 1 file → annotation_coverage = 0
	if report.Score.AnnotationCoverage != 0 {
		t.Fatalf("annotation_coverage = %f, want 0", report.Score.AnnotationCoverage)
	}
}

func TestSGScanJSON(t *testing.T) {
	root := t.TempDir()
	mainGo := filepath.Join(root, "projects", "ai-gftd-project-news", "wasm", "news-app", "main.go")
	writeTestFile(t, mainGo, `package main
// @gftd:import com-atproto:repo/repo@1.0.0
`)
	graph := sgScanWorkspace(root)
	data, err := json.Marshal(graph)
	if err != nil {
		t.Fatal(err)
	}
	var parsed sgGraph
	if err := json.Unmarshal(data, &parsed); err != nil {
		t.Fatal(err)
	}
	if parsed.Annotated != 1 {
		t.Fatalf("annotated = %d, want 1", parsed.Annotated)
	}
}

func TestSGViolations_ValidRef(t *testing.T) {
	root := t.TempDir()
	// Create the referenced doc
	docPath := filepath.Join(root, "docs", "existing-design.md")
	writeTestFile(t, docPath, "# Design\n")

	mainGo := filepath.Join(root, "projects", "ai-gftd-project-demo", "wasm", "demo-app", "main.go")
	writeTestFile(t, mainGo, `package main
// @gftd:ref docs/existing-design.md
`)
	graph := sgScanWorkspace(root)
	report := sgDetectViolations(root, &graph)

	for _, v := range report.Violations {
		if v.Rule == "dead-ref" {
			t.Fatal("should not have dead-ref for existing doc")
		}
	}
	if report.Score.ReferenceIntegrity != 1.0 {
		t.Fatalf("reference_integrity = %f, want 1.0", report.Score.ReferenceIntegrity)
	}
}

// writeTestFile is defined in build_test.go — reuse via package-level.
// If running standalone, ensure build_test.go is in the test binary.
func init() {
	// Ensure temp dirs work
	_ = os.TempDir()
}
