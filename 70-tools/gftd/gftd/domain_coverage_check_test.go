package main

import (
	"os"
	"path/filepath"
	"testing"
)

func TestCollectAndScoreDomainAppsExtractsDomainSignals(t *testing.T) {
	root := t.TempDir()
	appDir := filepath.Join(root, "60-apps", "ai-gftd-project-sample", "appview", "sample-ui", "src")
	if err := os.MkdirAll(appDir, 0o755); err != nil {
		t.Fatalf("mkdir: %v", err)
	}
	appTS := `
interface DomainRow { id: string }
const kinds = ["ai.gftd.apps.sample.entry", "ai.gftd.apps.sample.report"]
const rows = [{ id: "1" }].map((row) => row)
function cmdCustomSync() {}
function cmd_list_standard() {}
if (rows.length > 0) { console.log(rows[0]) }
switch ("a") { case "a": break }
Graph("Company")
comAtprotoIdentityCreate("/xrpc/com.atproto.identity.create")
const writerDID = "did:web:sample.etzhayyim.com"
const source = "https://api.example.com/feed.json"
`
	if err := os.WriteFile(filepath.Join(appDir, "app.ts"), []byte(appTS), 0o644); err != nil {
		t.Fatalf("write app.ts: %v", err)
	}
	jsonld := `{"nanoid":"smpl1234","governance":{"classification":"restricted","raci":"accountable"}}`
	if err := os.WriteFile(filepath.Join(filepath.Dir(appDir), "magatama.jsonld"), []byte(jsonld), 0o644); err != nil {
		t.Fatalf("write magatama.jsonld: %v", err)
	}

	got := collectAndScoreDomainApps(root)
	if len(got) != 1 {
		t.Fatalf("len = %d, want 1", len(got))
	}
	app := got[0]
	if app.Project != "sample" || app.Nanoid != "smpl1234" {
		t.Fatalf("unexpected app identity: %+v", app)
	}
	if len(app.SqlLabels) != 1 || app.SqlLabels[0] != "Company" {
		t.Fatalf("labels = %#v", app.SqlLabels)
	}
	if len(app.CollectionKinds) != 2 {
		t.Fatalf("collection kinds = %#v", app.CollectionKinds)
	}
	if len(app.CustomCommands) != 1 || app.TemplateCmds != 1 {
		t.Fatalf("commands = %#v template=%d", app.CustomCommands, app.TemplateCmds)
	}
	if !app.GovernanceUniq || !app.HasWriterEntity || len(app.DIDPaths) != 1 {
		t.Fatalf("expected governance/writer/did paths: %+v", app)
	}
	if app.DomainScore <= 0 || len(app.Missing) != 0 {
		t.Fatalf("unexpected score or missing fields: %+v", app)
	}
}
