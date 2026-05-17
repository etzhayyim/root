package main

import (
	"path/filepath"
	"testing"
)

// --- Go AST extraction tests ---

func TestSGExtractGoAST_WRecord(t *testing.T) {
	src := []byte(`package main

import magatama "github.com/etzhayyim/root/20-actors/magatama-go"

func cmdCreateArticle(ctx *magatama.AppContext, body []byte) ([]byte, error) {
	magatama.WRecord("article", body)
	magatama.WRecordUpdate("article", "rkey1", body)
	return nil, nil
}
`)
	result := sgExtractGoAST("main.go", src)
	if len(result.Writes) != 2 {
		t.Fatalf("writes = %d, want 2: %v", len(result.Writes), result.Writes)
	}
	if result.Writes[0] != "article" || result.Writes[1] != "article" {
		t.Fatalf("writes = %v", result.Writes)
	}
	// Check per-function extraction
	if len(result.Funcs) != 1 {
		t.Fatalf("funcs = %d, want 1", len(result.Funcs))
	}
	if result.Funcs[0].Name != "cmdCreateArticle" {
		t.Fatalf("func name = %q", result.Funcs[0].Name)
	}
	if len(result.Funcs[0].Writes) != 2 {
		t.Fatalf("func writes = %d, want 2", len(result.Funcs[0].Writes))
	}
}

func TestSGExtractGoAST_GQuery(t *testing.T) {
	src := []byte(`package main

import magatama "github.com/etzhayyim/root/20-actors/magatama-go"

func qryList(ctx *magatama.AppContext, p []byte) ([]byte, error) {
	rows, _ := magatama.G("Article").Match(magatama.Eq{"status": "published"}).Return("title").Query()
	_ = rows
	return nil, nil
}
`)
	result := sgExtractGoAST("main.go", src)
	if len(result.Reads) != 1 {
		t.Fatalf("reads = %d, want 1: %v", len(result.Reads), result.Reads)
	}
	if result.Reads[0] != "sql:Article" {
		t.Fatalf("reads[0] = %q", result.Reads[0])
	}
}

func TestSGExtractGoAST_Invoke(t *testing.T) {
	src := []byte(`package main

import magatama "github.com/etzhayyim/root/20-actors/magatama-go"

func doTranslate() {
	magatama.Invoke("did:web:i18n.etzhayyim.com", "translate", nil)
}
`)
	result := sgExtractGoAST("main.go", src)
	if len(result.Calls) != 1 {
		t.Fatalf("calls = %d, want 1", len(result.Calls))
	}
	if result.Calls[0] != "did:web:i18n.etzhayyim.com#translate" {
		t.Fatalf("calls[0] = %q", result.Calls[0])
	}
}

func TestSGExtractGoAST_Commands(t *testing.T) {
	src := []byte(`package main

import magatama "github.com/etzhayyim/root/20-actors/magatama-go"

var app = magatama.NewApp(magatama.AppDef{})

func init() {
	app.Command("", "create-article", cmdCreate)
	app.Command("", "delete-article", cmdDelete)
	app.Query("", "list-articles", qryList)
	magatama.HandleWCommit(handleComAtprotoSyncSubscribeReposCommit)
	app.Serve()
}

func cmdCreate(ctx *magatama.AppContext, body []byte) ([]byte, error) { return nil, nil }
func cmdDelete(ctx *magatama.AppContext, body []byte) ([]byte, error) { return nil, nil }
func qryList(ctx *magatama.AppContext, p []byte) ([]byte, error) { return nil, nil }
func handleComAtprotoSyncSubscribeReposCommit(c magatama.ComAtprotoSyncSubscribeReposCommit) error { return nil }
func main() {}
`)
	result := sgExtractGoAST("main.go", src)
	if len(result.Commands) != 2 {
		t.Fatalf("commands = %d, want 2: %v", len(result.Commands), result.Commands)
	}
	if len(result.Queries) != 1 {
		t.Fatalf("queries = %d, want 1: %v", len(result.Queries), result.Queries)
	}
	if !result.HasServe {
		t.Fatal("expected HasServe=true")
	}
	if len(result.Handlers) != 1 || result.Handlers[0] != "handleComAtprotoSyncSubscribeReposCommit" {
		t.Fatalf("handlers = %v", result.Handlers)
	}
}

func TestSGExtractGoAST_Fallback(t *testing.T) {
	// Invalid Go that won't parse — should fall back to regex
	content := `package main
func init() {
	magatama.WRecord("fallback_kind", data)
	magatama.G("FallbackLabel").Match(nil).Query()
	app.Command("", "fallback-cmd", handler)
	app.Serve()
`
	result := sgExtractGoAST("main.go", []byte(content))
	if len(result.Writes) < 1 {
		t.Fatalf("fallback writes = %d, want >=1", len(result.Writes))
	}
	if len(result.Reads) < 1 {
		t.Fatalf("fallback reads = %d, want >=1", len(result.Reads))
	}
}

// --- TypeScript AST extraction tests ---

func TestSGExtractTSAST_SqlLabels(t *testing.T) {
	content := `
const result = await graphQuery(` + "`" + `
  MATCH (a:Article {status: 'published'})
  OPTIONAL MATCH (a)-[:AUTHORED_BY]->(u:User)
  RETURN a, u
` + "`" + `);

await graphExec(` + "`" + `
  MERGE (p:Profile {did: $did})
  SET p.name = $name
` + "`" + `);
`
	result := sgExtractTSAST(content)
	// Should extract Article, User, Profile labels
	hasArticle := false
	hasUser := false
	hasProfile := false
	for _, r := range result.Reads {
		if r == "sql:Article" {
			hasArticle = true
		}
		if r == "sql:User" {
			hasUser = true
		}
	}
	for _, w := range result.Writes {
		if w == "sql:Profile" {
			hasProfile = true
		}
	}
	if !hasArticle {
		t.Fatal("missing sql:Article read")
	}
	if !hasUser {
		t.Fatal("missing sql:User read")
	}
	if !hasProfile {
		t.Fatal("missing sql:Profile write")
	}
}

func TestSGExtractTSAST_XRPCMethods(t *testing.T) {
	content := `
switch (method) {
  case "CreateRecord": {
    return handleCreate(req);
  }
  case "GetRecord": {
    return handleGet(req);
  }
}
`
	result := sgExtractTSAST(content)
	if len(result.Commands) < 2 {
		t.Fatalf("commands = %d, want >=2: %v", len(result.Commands), result.Commands)
	}
}

func TestSGExtractTSAST_Imports(t *testing.T) {
	content := `
import { WorkerEntrypoint } from "cloudflare:workers";
import { createKyselyDb } from "@gftd/magatama-host-sdk";

export async function handleRequest(req: Request): Promise<Response> {
  return new Response("ok");
}
`
	result := sgExtractTSAST(content)
	if len(result.Funcs) < 1 {
		t.Fatalf("funcs = %d, want >=1", len(result.Funcs))
	}
}

// --- Rust AST extraction tests ---

func TestSGExtractRustAST_Commands(t *testing.T) {
	content := `
use magatama_rs::*;

fn app() {
    let mut app = App::new(AppDef {
        id: "g00h5zto".into(),
        name: "yoro".into(),
        description: "Messenger".into(),
        agent: None,
    });

    app.command("", "send", cmd_send, &[
        CommandOption::AsAgentTool("Send a message".into()),
        CommandOption::WithCapabilityTags(vec!["messaging".into(), "w-protocol".into()]),
    ]);
    app.command("", "create-channel", cmd_create_channel, &[]);
    app.query("", "list-channels", qry_list_channels, &[]);
    app.serve();
}
`
	result := sgExtractRustAST(content)
	if len(result.Commands) < 2 {
		t.Fatalf("commands = %d, want >=2: %v", len(result.Commands), result.Commands)
	}
	if len(result.Queries) < 1 {
		t.Fatalf("queries = %d, want >=1", len(result.Queries))
	}
	if !result.HasServe {
		t.Fatal("expected HasServe=true")
	}
	// Check capability tags extracted
	hasCap := false
	for _, c := range result.Commands {
		if c == "cap:messaging" || c == "cap:w-protocol" {
			hasCap = true
		}
	}
	if !hasCap {
		t.Fatalf("missing capability tags: %v", result.Commands)
	}
}

func TestSGExtractRustAST_WRecord(t *testing.T) {
	content := `
fn cmd_save(ctx: &AppContext, body: &[u8]) -> Result<Vec<u8>, Error> {
    w_record("sensor_reading", &payload)?;
    let rows = G("SensorDevice").match_eq("id", device_id).return_all().query()?;
    Ok(vec![])
}
`
	result := sgExtractRustAST(content)
	if len(result.Writes) < 1 {
		t.Fatalf("writes = %d, want >=1: %v", len(result.Writes), result.Writes)
	}
	if result.Writes[0] != "sensor_reading" {
		t.Fatalf("writes[0] = %q", result.Writes[0])
	}
	if len(result.Reads) < 1 {
		t.Fatalf("reads = %d, want >=1: %v", len(result.Reads), result.Reads)
	}
}

func TestSGExtractRustAST_Functions(t *testing.T) {
	content := `
pub async fn handle_commit(commit: WCommit) -> Result<(), Error> {
    Ok(())
}

fn helper() -> String {
    "test".into()
}
`
	result := sgExtractRustAST(content)
	if len(result.Funcs) < 2 {
		t.Fatalf("funcs = %d, want >=2: %v", len(result.Funcs), result.Funcs)
	}
}

// --- Layer 1: WIT + magatama.jsonld parsing tests ---

func TestSGParseWIT(t *testing.T) {
	root := t.TempDir()
	witPath := filepath.Join(root, "wit", "world.wit")
	writeTestFile(t, witPath, `package gftd:warehouse-wh2cn7gd;

world component {
  include magatama:runtime/magatama-component@1.0.0;

  // Contract import
  import magatama:contract/agreement@1.0.0;
  import magatama:div/materiel@1.0.0;

  // Capability export
  export gftd:warehouse/registry@1.0.0;
}
`)

	meta := sgParseWIT(witPath)
	if meta.WITPackage != "gftd:warehouse-wh2cn7gd" {
		t.Fatalf("package = %q", meta.WITPackage)
	}
	if len(meta.WITImports) != 2 {
		t.Fatalf("imports = %d, want 2: %v", len(meta.WITImports), meta.WITImports)
	}
	if len(meta.WITExports) != 1 {
		t.Fatalf("exports = %d, want 1: %v", len(meta.WITExports), meta.WITExports)
	}
	if len(meta.WITInclude) != 1 {
		t.Fatalf("include = %d, want 1: %v", len(meta.WITInclude), meta.WITInclude)
	}
}

func TestSGParseJSONLD(t *testing.T) {
	root := t.TempDir()
	jPath := filepath.Join(root, "magatama.jsonld")
	writeTestFile(t, jPath, `{
  "@context": "https://etzhayyim.com/ns/magatama/v1",
  "@id": "did:web:warehouse.etzhayyim.com",
  "performerType": "service",
  "name": "warehouse",
  "nanoid": "wh2cn7gd",
  "runtimeType": "worker",
  "uiType": "appview",
  "triggers": {
    "subscribeRepos": {
      "collections": [
        "app.bsky.feed.post",
        "ai.gftd.apps.warehouse.warehouse"
      ]
    }
  },
  "profile": {
    "displayName": "Warehouse Manager",
    "description": "Warehouse management agent"
  },
  "build": {
    "guestLanguage": "go"
  }
}`)

	meta := sgParseJSONLD(jPath)
	if meta.DID != "did:web:warehouse.etzhayyim.com" {
		t.Fatalf("did = %q", meta.DID)
	}
	if meta.PerformerType != "service" {
		t.Fatalf("performerType = %q", meta.PerformerType)
	}
	if meta.NanoID != "wh2cn7gd" {
		t.Fatalf("nanoid = %q", meta.NanoID)
	}
	if len(meta.Collections) != 2 {
		t.Fatalf("collections = %d, want 2", len(meta.Collections))
	}
	if meta.GuestLanguage != "go" {
		t.Fatalf("guestLanguage = %q", meta.GuestLanguage)
	}
	if meta.DisplayName != "Warehouse Manager" {
		t.Fatalf("displayName = %q", meta.DisplayName)
	}
}

// --- Hybrid 3-layer integration test ---

func TestSGHybridScan(t *testing.T) {
	root := t.TempDir()
	appDir := filepath.Join(root, "projects", "ai-gftd-project-news", "wasm", "news-app-n001")

	// Layer 1: magatama.jsonld
	writeTestFile(t, filepath.Join(appDir, "magatama.jsonld"), `{
  "@id": "did:web:news.etzhayyim.com",
  "performerType": "service",
  "name": "news",
  "nanoid": "n001",
  "triggers": {
    "subscribeRepos": {
      "collections": ["app.bsky.feed.post", "ai.gftd.apps.news.article"]
    }
  },
  "profile": {"displayName": "News Agent", "description": "News"}
}`)

	// Layer 1: world.wit
	writeTestFile(t, filepath.Join(appDir, "wit", "world.wit"), `package gftd:news-n001;

world component {
  include magatama:runtime/magatama-component@1.0.0;
  import magatama:contract/agreement@1.0.0;
  export gftd:news/feed@1.0.0;
}
`)

	// Layer 2 + 3: main.go with both AST-extractable calls and @gftd: annotations
	writeTestFile(t, filepath.Join(appDir, "main.go"), `package main

import magatama "github.com/etzhayyim/root/20-actors/magatama-go"

// @gftd:authority sovereign/jpn, treaty/wto
// @gftd:sensitivity confidential
// @gftd:owner did:web:news.etzhayyim.com

var app = magatama.NewApp(magatama.AppDef{})

func init() {
	app.Command("", "publish", cmdPublish)
	magatama.HandleWCommit(handleComAtprotoSyncSubscribeReposCommit)
	app.Serve()
}

func cmdPublish(ctx *magatama.AppContext, body []byte) ([]byte, error) {
	// @gftd:calls did:web:i18n.etzhayyim.com#translate
	magatama.WRecord("translated_article", body)
	magatama.Invoke("did:web:i18n.etzhayyim.com", "translate", nil)
	return nil, nil
}

func handleComAtprotoSyncSubscribeReposCommit(c magatama.ComAtprotoSyncSubscribeReposCommit) error {
	rows, _ := magatama.G("Article").Match(magatama.Eq{}).Return("*").Query()
	_ = rows
	return nil
}

func main() {}
`)

	graph := sgScanWorkspace(root)

	// Verify 3-layer metrics
	if graph.ExtractionMode != "hybrid" {
		t.Fatalf("extraction_mode = %q, want hybrid", graph.ExtractionMode)
	}
	if graph.MetaResolved < 1 {
		t.Fatalf("meta_resolved = %d, want >=1", graph.MetaResolved)
	}
	if graph.ASTExtracted < 1 {
		t.Fatalf("ast_extracted = %d, want >=1", graph.ASTExtracted)
	}
	if graph.Annotated < 1 {
		t.Fatalf("annotated = %d, want >=1", graph.Annotated)
	}

	// Verify merged node has data from all 3 layers
	var fileNode *sgSourceNode
	for i := range graph.Nodes {
		if graph.Nodes[i].FuncName == "" && graph.Nodes[i].Kind == "go" {
			fileNode = &graph.Nodes[i]
			break
		}
	}
	if fileNode == nil {
		t.Fatal("no file-level Go node found")
	}

	// Layer 1: DID from magatama.jsonld
	if fileNode.AppDID != "did:web:news.etzhayyim.com" {
		t.Fatalf("app_did = %q (Layer 1 merge failed)", fileNode.AppDID)
	}

	// Layer 1: WIT imports merged
	hasContractImport := false
	for _, imp := range fileNode.Imports {
		if imp == "magatama:contract/agreement@1.0.0" {
			hasContractImport = true
		}
	}
	if !hasContractImport {
		t.Fatalf("missing WIT import merge (Layer 1): imports = %v", fileNode.Imports)
	}

	// Layer 3: @gftd: annotations
	if fileNode.Sensitivity != "confidential" {
		t.Fatalf("sensitivity = %q (Layer 3 annotation failed)", fileNode.Sensitivity)
	}
	if len(fileNode.Authorities) < 2 {
		t.Fatalf("authorities = %d (Layer 3 annotation failed)", len(fileNode.Authorities))
	}

	// Check function-level node has AST + annotation merge
	var publishNode *sgSourceNode
	for i := range graph.Nodes {
		if graph.Nodes[i].FuncName == "cmdPublish" {
			publishNode = &graph.Nodes[i]
			break
		}
	}
	if publishNode == nil {
		t.Fatal("cmdPublish node not found")
	}

	// Layer 2: AST-extracted WRecord write
	hasWrite := false
	for _, w := range publishNode.Writes {
		if w == "translated_article" {
			hasWrite = true
		}
	}
	if !hasWrite {
		t.Fatalf("missing AST-extracted write (Layer 2): writes = %v", publishNode.Writes)
	}

	// Layer 2: AST-extracted Invoke call
	hasInvoke := false
	for _, c := range publishNode.Calls {
		if c == "did:web:i18n.etzhayyim.com#translate" {
			hasInvoke = true
		}
	}
	if !hasInvoke {
		t.Fatalf("missing AST-extracted invoke (Layer 2): calls = %v", publishNode.Calls)
	}

	// Score should be >0 since all 3 layers contributed
	report := sgDetectViolations(root, &graph)
	if report.Score.ASTCoverage <= 0 {
		t.Fatalf("ast_coverage = %f, want >0", report.Score.ASTCoverage)
	}
	if report.Score.AnnotationCoverage <= 0 {
		t.Fatalf("annotation_coverage = %f, want >0", report.Score.AnnotationCoverage)
	}
}

func TestSGDedup(t *testing.T) {
	input := []string{"a", "b", "a", "c", "b"}
	got := sgDedup(input)
	if len(got) != 3 {
		t.Fatalf("dedup = %v, want 3 unique", got)
	}
}

func TestSGMergeStrings(t *testing.T) {
	a := []string{"x", "y"}
	b := []string{"y", "z"}
	got := sgMergeStrings(a, b)
	if len(got) != 3 {
		t.Fatalf("merge = %v, want [x,y,z]", got)
	}
}
