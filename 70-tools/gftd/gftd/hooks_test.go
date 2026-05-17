package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"testing"
)

func TestBuildHookEnvelopeBasic(t *testing.T) {
	dir := t.TempDir()
	writeTestFile(t, filepath.Join(dir, "magatama.jsonld"), `{"@context":"https://etzhayyim.com/ns/magatama/v1","name":"demo","nanoid":"d3m0","project":"demo-app"}`)

	cfg := &magatamaJSONLD{Name: "demo", Nanoid: "d3m0", Project: "demo-app", Build: &buildConfig{WITWorld: "magatama:runtime/magatama-component"}}
	env, err := buildHookEnvelope(cfg, dir, hookOptions{
		Event:      "post_build",
		CachePurge: planCachePurge(cfg, dir, ""),
	})
	if err != nil {
		t.Fatalf("buildHookEnvelope: %v", err)
	}

	if env.App.AppID != "d3m0" {
		t.Fatalf("AppID = %q", env.App.AppID)
	}
	if env.Cache.Status != "planned" {
		t.Fatalf("cache status = %q", env.Cache.Status)
	}
}

func TestRunConfiguredHooksPostsJSONEnvelope(t *testing.T) {
	dir := t.TempDir()

	var got hookEnvelope
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			t.Fatalf("unexpected method %s", r.Method)
		}
		if err := json.NewDecoder(r.Body).Decode(&got); err != nil {
			t.Fatalf("decode body: %v", err)
		}
		w.WriteHeader(http.StatusAccepted)
	}))
	defer srv.Close()

	cfg := &magatamaJSONLD{
		Name:        "demo",
		Nanoid:      "abc123",
		RuntimeType: "worker",
		Hooks: []gftdHook{
			{
				Name:   "deps",
				Kind:   "http",
				URL:    srv.URL,
				Events: []string{"post_build"},
			},
		},
	}

	if err := runConfiguredHooks(cfg, dir, hookOptions{
		Event:      "post_build",
		CachePurge: planCachePurge(cfg, dir, ""),
	}); err != nil {
		t.Fatalf("runConfiguredHooks: %v", err)
	}

	if got.Event != "post_build" {
		t.Fatalf("event = %q", got.Event)
	}
	if got.App.Nanoid != "abc123" {
		t.Fatalf("nanoid = %q", got.App.Nanoid)
	}
	if got.Cache.Status != "planned" {
		t.Fatalf("cache status = %q", got.Cache.Status)
	}
}

func TestPlanCachePurgeIncludesAppviewURLs(t *testing.T) {
	dir := t.TempDir()
	writeTestFile(t, filepath.Join(dir, "magatama.jsonld"), `{"@context":"https://etzhayyim.com/ns/magatama/v1","name":"demo","nanoid":"d3m0","project":"demo-app","uiType":"appview"}`)

	cfg := &magatamaJSONLD{Name: "demo", Nanoid: "d3m0", Project: "demo-app", UIType: "appview"}
	plan := planCachePurge(cfg, dir, "https://demo-app.etzhayyim.com/health")

	if plan.Status != "planned" {
		t.Fatalf("status = %q", plan.Status)
	}
	expected := map[string]bool{
		"https://d3m0.etzhayyim.com/":           false,
		"https://demo-app.etzhayyim.com/health": false,
	}
	for _, u := range plan.URLs {
		if _, ok := expected[u]; ok {
			expected[u] = true
		}
	}
	for u, ok := range expected {
		if !ok {
			t.Fatalf("missing purge url %s in %#v", u, plan.URLs)
		}
	}
}

func TestDispatchHTTPHookUsesAuthEnv(t *testing.T) {
	old := os.Getenv("HOOK_TOKEN")
	t.Cleanup(func() {
		_ = os.Setenv("HOOK_TOKEN", old)
	})
	_ = os.Setenv("HOOK_TOKEN", "secret-token")

	sawAuth := ""
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		sawAuth = r.Header.Get("Authorization")
		w.WriteHeader(http.StatusOK)
	}))
	defer srv.Close()

	err := dispatchHTTPHook(gftdHook{
		Name:       "deps",
		URL:        srv.URL,
		AuthEnv:    "HOOK_TOKEN",
		AuthScheme: "Bearer",
	}, &hookEnvelope{Schema: "x"})
	if err != nil {
		t.Fatalf("dispatchHTTPHook: %v", err)
	}
	if sawAuth != "Bearer secret-token" {
		t.Fatalf("authorization = %q", sawAuth)
	}
}
