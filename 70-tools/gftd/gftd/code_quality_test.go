package main

import (
	"path/filepath"
	"strings"
	"testing"
)

func TestCountDidDoublePrefixViolations(t *testing.T) {
	content := strings.Join([]string{
		"const ok1 = `did:web:${appId}`;",
		"const ok2 = actor.startsWith(\"did:\") ? actor : `did:web:${actor}`;",
		"const ok3 = ensureDid(handle);",
		"const ok4 = `did:web:${nanoid}`;",
		"const bad1 = `did:web:${actor}`;",
		"const bad2 = `did:web:${handle.replace(/\\.gftd\\.ai$/, \"\")}.etzhayyim.com`;",
	}, "\n")

	got := countDidDoublePrefixViolations(content, []string{"appId", "APP_ID", "nanoid"})
	if got != 2 {
		t.Fatalf("countDidDoublePrefixViolations() = %d, want 2", got)
	}
}

func TestCheckMagatamaLintDidDoublePrefix(t *testing.T) {
	root := t.TempDir()
	mainGo := filepath.Join(root, "projects", "ai-gftd-project-demo", "wasm", "demo-app", "main.go")
	writeTestFile(t, mainGo, `package main

func main() {
	const ok = actor.startsWith("did:") ? actor : `+"`did:web:${actor}`"+`
	const bad = `+"`did:web:${subject}`"+`
	_, _ = ok, bad
}
`)

	check := checkMagatamaLint(root)
	if check.Issues != 1 {
		t.Fatalf("issues = %d, want 1", check.Issues)
	}
	if !strings.Contains(check.Details, "did-double-prefix: 1") {
		t.Fatalf("unexpected details: %s", check.Details)
	}
}

func TestCheckMagatamaLintStandardActorRuleOn60Apps(t *testing.T) {
	root := t.TempDir()
	appTS := filepath.Join(root, "60-apps", "ai-gftd-project-demo", "appview", "demo-app", "src", "app.ts")
	jsonld := filepath.Join(root, "60-apps", "ai-gftd-project-demo", "appview", "demo-app", "magatama.jsonld")
	writeTestFile(t, appTS, `export default { fetch() { return new Response("ok"); } };`)
	writeTestFile(t, jsonld, `{
  "@id": "did:web:demo.etzhayyim.com",
  "nanoid": "demo1234",
  "profile": { "displayName": "Demo" }
}`)

	check := checkMagatamaLint(root)
	if check.Issues == 0 {
		t.Fatalf("issues = %d, want > 0", check.Issues)
	}
	for _, want := range []string{
		"missing-standard-heartbeat",
		"missing-standard-kyumei-flags",
		"missing-standard-domain-knowledge",
		"missing-convo-system-prompt",
		"missing-profile-description",
		"missing-profile-capabilities",
	} {
		if !strings.Contains(check.Details, want) {
			t.Fatalf("expected %s violation, got: %s", want, check.Details)
		}
	}
}

func TestCheckMagatamaLintStandardActorRuleSatisfied(t *testing.T) {
	root := t.TempDir()
	appTS := filepath.Join(root, "60-apps", "ai-gftd-project-demo", "appview", "demo-app", "src", "app.ts")
	jsonld := filepath.Join(root, "60-apps", "ai-gftd-project-demo", "appview", "demo-app", "magatama.jsonld")
	writeTestFile(t, appTS, `
const collections = [
  "ai.gftd.apps.demo.shinkaEvolution",
  "ai.gftd.apps.demo.shinkaKnowledge",
];
function runHeartbeat() {
  return { shouldDrill: true, shouldValidate: true, shouldAnalyze: true, shouldEngage: true };
}
export default {
  fetch(request) {
    const url = new URL(request.url);
    if (url.pathname === "/_heartbeat") return new Response(JSON.stringify(runHeartbeat()));
    return new Response(JSON.stringify({ collections }));
  }
};`)
	writeTestFile(t, jsonld, `{
  "@id": "did:web:demo.etzhayyim.com",
  "nanoid": "demo1234",
  "convoSystemPrompt": "demo",
  "profile": {
    "displayName": "Demo",
    "description": "demo description",
    "capabilities": ["domain-query"]
  },
  "governance": { "classification": "internal" }
}`)

	check := checkMagatamaLint(root)
	for _, unwanted := range []string{
		"missing-standard-heartbeat",
		"missing-standard-kyumei-flags",
		"missing-standard-domain-knowledge",
		"missing-convo-system-prompt",
		"missing-profile-description",
		"missing-profile-capabilities",
	} {
		if strings.Contains(check.Details, unwanted) {
			t.Fatalf("unexpected %s violation: %s", unwanted, check.Details)
		}
	}
}

func TestCountDualWriteViolations(t *testing.T) {
	content := `package main

func goodFunc() {
	magatama.AppBskyFeedPostAs(did, "hello", nil)
}

func badFunc() {
	magatama.WRecord("article", payload)
	magatama.AppBskyFeedPostAs("new article", nil)
}

func alsoGoodFunc() {
	magatama.WRecord("data", payload)
}
`
	got := countDualWriteViolations(content)
	if got != 1 {
		t.Fatalf("countDualWriteViolations() = %d, want 1", got)
	}
}

func TestCheckFrontendLint(t *testing.T) {
	root := t.TempDir()

	// Create a file with legacy listEnvelopes usage
	badSvelte := filepath.Join(root, "projects", "ai-gftd-project-demo", "wasm", "demo-app", "svelte", "src", "routes", "+page.svelte")
	writeTestFile(t, badSvelte, `<script lang="ts">
import { listEnvelopes, decodePayload } from '@gftdcojp/appshellv2/w';
const envelopes = await listEnvelopes(convoId, { limit: 50 });
const body = decodePayload(env);
</script>`)

	// Create a compliant file
	goodSvelte := filepath.Join(root, "projects", "ai-gftd-project-demo", "wasm", "demo-app", "svelte", "src", "routes", "profile", "+page.svelte")
	writeTestFile(t, goodSvelte, `<script lang="ts">
import { getAuthorFeed } from '@gftdcojp/appshellv2/w';
const { feed } = await getAuthorFeed(did, { limit: 50 });
</script>`)

	check := checkFrontendLint(root)
	if check.Issues < 2 {
		t.Fatalf("issues = %d, want >= 2 (listEnvelopes + decodePayload), details: %s", check.Issues, check.Details)
	}
	if !strings.Contains(check.Details, "legacy-envelope") {
		t.Fatalf("expected legacy-envelope violation, got: %s", check.Details)
	}
}

func TestCheckFrontendLintXRPC(t *testing.T) {
	root := t.TempDir()
	svelteFile := filepath.Join(root, "projects", "ai-gftd-project-demo", "wasm", "demo-app", "svelte", "src", "lib", "api.ts")
	writeTestFile(t, svelteFile, `
const url = "https://atproto.etzhayyim.com/xrpc/com.atproto.repo.getRecord";
`)
	check := checkFrontendLint(root)
	if check.Issues != 1 {
		t.Fatalf("issues = %d, want 1, details: %s", check.Issues, check.Details)
	}
	if !strings.Contains(check.Details, "xrpc-frontend") {
		t.Fatalf("expected xrpc-frontend violation, got: %s", check.Details)
	}
}

func TestCheckFrontendLintSkipsFramework(t *testing.T) {
	// Files matching FileExclude (w-service.ts, w-channel-store.svelte.ts) should be skipped
	root := t.TempDir()
	frameworkFile := filepath.Join(root, "projects", "ai-gftd-project-demo", "wasm", "demo-app", "svelte", "src", "lib", "w-service.ts")
	writeTestFile(t, frameworkFile, `
export function listEnvelopes() {}
export function decodePayload() {}
`)
	check := checkFrontendLint(root)
	if check.Issues != 0 {
		t.Fatalf("issues = %d, want 0 (framework files excluded), details: %s", check.Issues, check.Details)
	}
}

func TestCheckSqlInjectionDidDoublePrefix(t *testing.T) {
	root := t.TempDir()
	indexPath := filepath.Join(root, "packages", "server", "wproto", "src", "pds-dispatch.ts")
	writeTestFile(t, indexPath, strings.Join([]string{
		"const ok1 = actor.startsWith(\"did:\") ? actor : `did:web:${actor}`;",
		"const ok2 = `did:web:${appId}`;",
		"const ok3 = `did:web:${cl(r.rkey)}`;",
		"const bad1 = `did:web:${subject}`;",
		"const bad2 = `did:web:${handle.replace(/\\.gftd\\.ai$/, \"\")}.etzhayyim.com`;",
	}, "\n"))

	check := checkSqlInjection(root)
	if check.Issues != 2 {
		t.Fatalf("issues = %d, want 2", check.Issues)
	}
	if !strings.Contains(check.Details, "did-double-prefix: 2") {
		t.Fatalf("unexpected details: %s", check.Details)
	}
}
