package main

import (
	"encoding/base64"
	"os"
	"path/filepath"
	"reflect"
	"strings"
	"testing"
)

func TestLoadCloudflareTokenFileRaw(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "token.txt")
	if err := os.WriteFile(path, []byte("tok-123\n"), 0o600); err != nil {
		t.Fatalf("write token: %v", err)
	}
	if got := loadCloudflareTokenFile(path); got != "tok-123" {
		t.Fatalf("token = %q", got)
	}
}

func TestLoadCloudflareTokenFileK8sSecretJSON(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "secret.json")
	token := "tok-secret"
	payload := `{"data":{"CLOUDFLARE_API_TOKEN":"` + base64.StdEncoding.EncodeToString([]byte(token)) + `"}}`
	if err := os.WriteFile(path, []byte(payload), 0o600); err != nil {
		t.Fatalf("write secret json: %v", err)
	}
	if got := loadCloudflareTokenFile(path); got != token {
		t.Fatalf("token = %q", got)
	}
}

func TestGenerateWorkerWranglerIncludesAppBindings(t *testing.T) {
	t.Setenv("CLOUDFLARE_API_TOKEN", "")
	t.Setenv("CF_API_TOKEN", "")
	t.Setenv("GFTD_CLOUDFLARE_API_TOKEN", "")
	t.Setenv("CLOUDFLARE_API_TOKEN_FILE", "")
	t.Setenv("GFTD_CLOUDFLARE_API_TOKEN_FILE", "")
	t.Setenv("HOME", t.TempDir())

	backupPaths := defaultCloudflareTokenBackupPaths
	defaultCloudflareTokenBackupPaths = nil
	defer func() { defaultCloudflareTokenBackupPaths = backupPaths }()

	wrangler := generateWorkerWrangler("fixture-app", "store-123", nil, &magatamaJSONLD{}, "")

	for _, needle := range []string{
		`"main": "src/app.ts"`,
		`"compatibility_flags": ["nodejs_compat","nodejs_als"]`,
		`{ "binding": "YATA_R2", "bucket_name": "ai-gftd-cache" }`,
		`{ "binding": "CDN_R2", "bucket_name": "ai-gftd-cdn" }`,
		`{ "binding": "PDS_SERVICE", "service": "ai-gftd-pds-2603241700" }`,
		`{ "type": "CompiledWasm", "globs": ["**/*.wasm"] }`,
		`{ "pattern": "fixture-app.etzhayyim.com/*", "zone_name": "etzhayyim.com" }`,
	} {
		if !strings.Contains(wrangler, needle) {
			t.Fatalf("wrangler output missing %q\n%s", needle, wrangler)
		}
	}
}

func TestGenerateWorkerWranglerIncludesAssetsAndVersionVars(t *testing.T) {
	t.Setenv("CLOUDFLARE_API_TOKEN", "")
	t.Setenv("CF_API_TOKEN", "")
	t.Setenv("GFTD_CLOUDFLARE_API_TOKEN", "")
	t.Setenv("CLOUDFLARE_API_TOKEN_FILE", "")
	t.Setenv("GFTD_CLOUDFLARE_API_TOKEN_FILE", "")
	t.Setenv("HOME", t.TempDir())

	backupPaths := defaultCloudflareTokenBackupPaths
	defaultCloudflareTokenBackupPaths = nil
	defer func() { defaultCloudflareTokenBackupPaths = backupPaths }()

	meta := &appVersionMeta{
		Version:   "v20260321",
		Template:  "magatama-default",
		Source:    "unit-test",
		DeploySHA: "abc123",
		DeployAt:  "2026-03-21T01:23:45Z",
	}
	wrangler := generateWorkerWrangler("fixture-app", "store-123", meta, &magatamaJSONLD{UIType: "appview"}, "")

	for _, needle := range []string{
		`"assets": {`,
		`"directory": "./svelte/build"`,
		`"binding": "ASSETS"`,
		`"APP_VERSION": "v20260321"`,
		`"APP_TEMPLATE": "magatama-default"`,
		`"APP_SOURCE": "unit-test"`,
		`"APP_DEPLOY_SHA": "abc123"`,
		`"APP_DEPLOY_AT": "2026-03-21T01:23:45Z"`,
	} {
		if !strings.Contains(wrangler, needle) {
			t.Fatalf("wrangler output missing %q\n%s", needle, wrangler)
		}
	}
}

func TestGenerateWorkerWranglerContainsRoutes(t *testing.T) {
	wrangler := generateWorkerWrangler("fixture-app", "store-123", nil, &magatamaJSONLD{}, "")
	if !strings.Contains(wrangler, `"fixture-app.etzhayyim.com/*"`) {
		t.Fatalf("wrangler missing route pattern:\n%s", wrangler)
	}
}

func TestGenerateWorkerWranglerServiceOverrides(t *testing.T) {
	t.Setenv("GFTD_PDS_SERVICE", "custom-pds-worker")

	wrangler := generateWorkerWrangler("fixture-app", "store-123", nil, &magatamaJSONLD{}, "")
	for _, needle := range []string{
		`{ "binding": "PDS_SERVICE", "service": "custom-pds-worker" }`,
	} {
		if !strings.Contains(wrangler, needle) {
			t.Fatalf("wrangler output missing %q\n%s", needle, wrangler)
		}
	}
}

func TestStaticAssetHosts(t *testing.T) {
	cfg := &magatamaJSONLD{Nanoid: "abc123", Project: "games"}
	got := staticAssetHosts(cfg)
	want := []string{"abc123.etzhayyim.com", "games.etzhayyim.com"}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("staticAssetHosts = %#v, want %#v", got, want)
	}
}

func TestCurrentImmutableAssetKeys(t *testing.T) {
	dir := t.TempDir()
	assetDir := filepath.Join(dir, "svelte", "build", "_app", "immutable", "chunks")
	if err := os.MkdirAll(assetDir, 0o755); err != nil {
		t.Fatalf("mkdir asset dir: %v", err)
	}
	chunk := filepath.Join(assetDir, "index-abc.js")
	if err := os.WriteFile(chunk, []byte("console.log('ok')"), 0o644); err != nil {
		t.Fatalf("write chunk: %v", err)
	}
	keys, err := currentImmutableAssetKeys(&magatamaJSONLD{Nanoid: "abc123", Project: "games"}, dir)
	if err != nil {
		t.Fatalf("currentImmutableAssetKeys: %v", err)
	}
	for _, want := range []string{
		"abc123.etzhayyim.com/_app/immutable/chunks/index-abc.js",
		"games.etzhayyim.com/_app/immutable/chunks/index-abc.js",
	} {
		if _, ok := keys[want]; !ok {
			t.Fatalf("missing key %q in %#v", want, keys)
		}
	}
}

func TestStaleImmutableKeys(t *testing.T) {
	current := map[string]struct{}{
		"games.etzhayyim.com/_app/immutable/chunks/new.js": {},
	}
	recent := []string{
		"games.etzhayyim.com/_app/immutable/chunks/old.js",
		"games.etzhayyim.com/_app/immutable/chunks/new.js",
		"games.etzhayyim.com/index.html",
		"games.etzhayyim.com/_app/immutable/chunks/old.js",
	}
	got := staleImmutableKeys(recent, current)
	want := []string{"games.etzhayyim.com/_app/immutable/chunks/old.js"}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("staleImmutableKeys = %#v, want %#v", got, want)
	}
}
