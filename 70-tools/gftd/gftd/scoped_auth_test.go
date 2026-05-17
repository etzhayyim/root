package main

import (
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"net/url"
	"testing"
)

func TestNsidFromURLPath(t *testing.T) {
	cases := map[string]string{
		"https://atproto.etzhayyim.com/xrpc/com.atproto.repo.applyWrites":        "com.atproto.repo.applyWrites",
		"https://atproto.etzhayyim.com/xrpc/ai.gftd.kagami.sql?foo=bar":  "ai.gftd.kagami.sql",
		"https://atproto.etzhayyim.com/xrpc/ai.gftd.actor.list/":                 "ai.gftd.actor.list",
		"https://atproto.etzhayyim.com/health":                                   "",
		"https://atproto.etzhayyim.com/":                                         "",
	}
	for raw, want := range cases {
		u, err := url.Parse(raw)
		if err != nil {
			t.Fatalf("parse %q: %v", raw, err)
		}
		if got := nsidFromURLPath(u); got != want {
			t.Errorf("nsidFromURLPath(%q)=%q, want %q", raw, got, want)
		}
	}
	if got := nsidFromURLPath(nil); got != "" {
		t.Errorf("nsidFromURLPath(nil)=%q, want empty", got)
	}
}

func TestScopedAuthKillSwitch(t *testing.T) {
	for _, v := range []string{"off", "0", "false", "OFF", "False"} {
		t.Setenv("GFTD_SCOPED_AUTH", v)
		if scopedAuthEnabled() {
			t.Errorf("GFTD_SCOPED_AUTH=%q should disable", v)
		}
	}
	for _, v := range []string{"", "on", "1", "true"} {
		t.Setenv("GFTD_SCOPED_AUTH", v)
		if !scopedAuthEnabled() {
			t.Errorf("GFTD_SCOPED_AUTH=%q should enable", v)
		}
	}
}

func TestMintScopedJWT_ShortCircuits(t *testing.T) {
	if got := mintScopedJWT("", "ai.gftd.foo.bar"); got != "" {
		t.Errorf("empty baseToken: got %q, want empty", got)
	}
	if got := mintScopedJWT("tok", ""); got != "" {
		t.Errorf("empty nsid: got %q, want empty", got)
	}
	if got := mintScopedJWT("tok", serviceAuthNSID); got != "" {
		t.Errorf("getServiceAuth bootstrap nsid: got %q, want empty (no recursion)", got)
	}
}

func TestSetAuthHeaders_UsesScopedJWT(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/xrpc/com.atproto.server.getServiceAuth" {
			http.Error(w, "unexpected path", 404)
			return
		}
		var body map[string]any
		b, _ := io.ReadAll(r.Body)
		_ = json.Unmarshal(b, &body)
		if body["lxm"] != "ai.gftd.kagami.sql" {
			http.Error(w, "lxm mismatch", 400)
			return
		}
		if r.Header.Get("Authorization") != "Bearer base-token" {
			http.Error(w, "base token missing", 401)
			return
		}
		_ = json.NewEncoder(w).Encode(map[string]string{"token": "scoped-jwt-xyz"})
	}))
	defer srv.Close()

	t.Setenv("GFTD_PDS_URL", srv.URL)
	t.Setenv("GFTD_TOKEN", "base-token")
	t.Setenv("GFTD_SCOPED_AUTH", "on")
	t.Setenv("HOME", t.TempDir())
	scopedJWTMu.Lock()
	scopedJWTCache = map[string]scopedJWTEntry{}
	scopedJWTMu.Unlock()

	req, _ := http.NewRequest(http.MethodPost, srv.URL+"/xrpc/ai.gftd.kagami.sql", nil)
	setAuthHeaders(req)

	if got := req.Header.Get("Authorization"); got != "Bearer scoped-jwt-xyz" {
		t.Fatalf("Authorization=%q, want Bearer scoped-jwt-xyz (scoped JWT)", got)
	}
}

func TestSetAuthHeaders_FallsBackOnMintFailure(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		http.Error(w, "upstream down", 503)
	}))
	defer srv.Close()

	t.Setenv("GFTD_PDS_URL", srv.URL)
	t.Setenv("GFTD_TOKEN", "base-token")
	t.Setenv("GFTD_SCOPED_AUTH", "on")
	t.Setenv("HOME", t.TempDir())
	scopedJWTMu.Lock()
	scopedJWTCache = map[string]scopedJWTEntry{}
	scopedJWTMu.Unlock()

	req, _ := http.NewRequest(http.MethodPost, srv.URL+"/xrpc/ai.gftd.kagami.sql", nil)
	setAuthHeaders(req)

	if got := req.Header.Get("Authorization"); got != "Bearer base-token" {
		t.Fatalf("Authorization=%q, want fallback to Bearer base-token", got)
	}
}

func TestSetAuthHeaders_KillSwitchSkipsMint(t *testing.T) {
	// Mint endpoint would succeed, but kill switch must prevent the call.
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		t.Errorf("mint endpoint should not be called when GFTD_SCOPED_AUTH=off")
		_ = json.NewEncoder(w).Encode(map[string]string{"token": "should-not-appear"})
	}))
	defer srv.Close()

	t.Setenv("GFTD_PDS_URL", srv.URL)
	t.Setenv("GFTD_TOKEN", "base-token")
	t.Setenv("GFTD_SCOPED_AUTH", "off")
	t.Setenv("HOME", t.TempDir())
	scopedJWTMu.Lock()
	scopedJWTCache = map[string]scopedJWTEntry{}
	scopedJWTMu.Unlock()

	req, _ := http.NewRequest(http.MethodPost, srv.URL+"/xrpc/ai.gftd.kagami.sql", nil)
	setAuthHeaders(req)

	if got := req.Header.Get("Authorization"); got != "Bearer base-token" {
		t.Fatalf("Authorization=%q, want Bearer base-token (kill switch)", got)
	}
}

func TestSetAuthHeaders_NonXrpcURLSkipsMint(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		t.Errorf("mint endpoint should not be called for non-XRPC URLs")
	}))
	defer srv.Close()

	t.Setenv("GFTD_PDS_URL", srv.URL)
	t.Setenv("GFTD_TOKEN", "base-token")
	t.Setenv("GFTD_SCOPED_AUTH", "on")
	t.Setenv("HOME", t.TempDir())

	req, _ := http.NewRequest(http.MethodGet, srv.URL+"/health", nil)
	setAuthHeaders(req)

	if got := req.Header.Get("Authorization"); got != "Bearer base-token" {
		t.Fatalf("Authorization=%q, want Bearer base-token for non-XRPC path", got)
	}
}
