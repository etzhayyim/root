// Tests for `gftd authn revoke` — ADR-2604240914 Y2 (RFC 7009).

package main

import (
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"net/url"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"testing"
)

// captureServer records every POST /oauth/revoke request it receives.
type captureServer struct {
	srv  *httptest.Server
	mu   sync.Mutex
	reqs []revokeCall
}

type revokeCall struct {
	Token         string
	TokenTypeHint string
}

func newCaptureServer(status int) *captureServer {
	cs := &captureServer{}
	cs.srv = httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost || r.URL.Path != "/oauth/revoke" {
			http.Error(w, "not found", http.StatusNotFound)
			return
		}
		body, _ := io.ReadAll(r.Body)
		_ = r.Body.Close()
		vals, _ := url.ParseQuery(string(body))
		cs.mu.Lock()
		cs.reqs = append(cs.reqs, revokeCall{
			Token:         vals.Get("token"),
			TokenTypeHint: vals.Get("token_type_hint"),
		})
		cs.mu.Unlock()
		w.WriteHeader(status)
	}))
	return cs
}

func writeTokenStore(t *testing.T, home string, ts tokenStore) {
	t.Helper()
	if err := os.MkdirAll(filepath.Join(home, ".gftd"), 0o700); err != nil {
		t.Fatalf("mkdir: %v", err)
	}
	data, _ := json.MarshalIndent(ts, "", "  ")
	if err := os.WriteFile(filepath.Join(home, ".gftd", "auth.json"), data, 0o600); err != nil {
		t.Fatalf("write auth.json: %v", err)
	}
}

func TestAuthRevoke_FromLocalStoreSendsBothTokensAndClears(t *testing.T) {
	home := t.TempDir()
	t.Setenv("HOME", home)
	t.Setenv("GFTD_TOKEN", "")

	cs := newCaptureServer(http.StatusOK)
	defer cs.srv.Close()

	writeTokenStore(t, home, tokenStore{
		AccessToken:  "ACCESS-JWT",
		RefreshToken: "REFRESH-JWT",
		Sub:          "did:web:alice.etzhayyim.com",
	})

	if err := runAuthRevoke([]string{"--pds", cs.srv.URL, "-q"}); err != nil {
		t.Fatalf("runAuthRevoke: %v", err)
	}

	if len(cs.reqs) != 2 {
		t.Fatalf("expected 2 revoke calls, got %d", len(cs.reqs))
	}
	var sawAccess, sawRefresh bool
	for _, r := range cs.reqs {
		switch r.Token {
		case "ACCESS-JWT":
			sawAccess = true
			if r.TokenTypeHint != "access_token" {
				t.Errorf("access token_type_hint = %q, want access_token", r.TokenTypeHint)
			}
		case "REFRESH-JWT":
			sawRefresh = true
			if r.TokenTypeHint != "refresh_token" {
				t.Errorf("refresh token_type_hint = %q, want refresh_token", r.TokenTypeHint)
			}
		default:
			t.Errorf("unexpected token: %q", r.Token)
		}
	}
	if !sawAccess || !sawRefresh {
		t.Errorf("missing revoke call — access=%v refresh=%v", sawAccess, sawRefresh)
	}

	// Local store must be gone.
	if _, err := os.Stat(filepath.Join(home, ".gftd", "auth.json")); !os.IsNotExist(err) {
		t.Errorf("expected auth.json to be removed, stat err = %v", err)
	}
}

func TestAuthRevoke_ExplicitTokenDoesNotTouchLocalStore(t *testing.T) {
	home := t.TempDir()
	t.Setenv("HOME", home)
	t.Setenv("GFTD_TOKEN", "")

	cs := newCaptureServer(http.StatusOK)
	defer cs.srv.Close()

	writeTokenStore(t, home, tokenStore{
		AccessToken:  "LOCAL-ACCESS",
		RefreshToken: "LOCAL-REFRESH",
	})

	if err := runAuthRevoke([]string{"--pds", cs.srv.URL, "--token", "EXTERNAL-JWT", "-q"}); err != nil {
		t.Fatalf("runAuthRevoke: %v", err)
	}

	if len(cs.reqs) != 1 {
		t.Fatalf("expected 1 revoke call, got %d", len(cs.reqs))
	}
	if cs.reqs[0].Token != "EXTERNAL-JWT" {
		t.Errorf("token = %q, want EXTERNAL-JWT", cs.reqs[0].Token)
	}
	// Local store must be untouched.
	if _, err := os.Stat(filepath.Join(home, ".gftd", "auth.json")); err != nil {
		t.Errorf("expected auth.json to survive --token mode, got %v", err)
	}
}

func TestAuthRevoke_KeepLocalFlag(t *testing.T) {
	home := t.TempDir()
	t.Setenv("HOME", home)
	t.Setenv("GFTD_TOKEN", "")

	cs := newCaptureServer(http.StatusOK)
	defer cs.srv.Close()

	writeTokenStore(t, home, tokenStore{AccessToken: "ACCESS-JWT"})

	if err := runAuthRevoke([]string{"--pds", cs.srv.URL, "--keep-local", "-q"}); err != nil {
		t.Fatalf("runAuthRevoke: %v", err)
	}
	if _, err := os.Stat(filepath.Join(home, ".gftd", "auth.json")); err != nil {
		t.Errorf("expected auth.json to survive --keep-local, got %v", err)
	}
}

func TestAuthRevoke_NonOKResponseReturnsError(t *testing.T) {
	home := t.TempDir()
	t.Setenv("HOME", home)
	t.Setenv("GFTD_TOKEN", "")

	cs := newCaptureServer(http.StatusInternalServerError)
	defer cs.srv.Close()

	writeTokenStore(t, home, tokenStore{AccessToken: "ACCESS-JWT"})

	err := runAuthRevoke([]string{"--pds", cs.srv.URL, "-q"})
	if err == nil {
		t.Fatal("expected error on 500 response, got nil")
	}
	if !strings.Contains(err.Error(), "revoke calls failed") {
		t.Errorf("unexpected error: %v", err)
	}
	// Local store should still exist (we don't clear on failure).
	if _, err := os.Stat(filepath.Join(home, ".gftd", "auth.json")); err != nil {
		t.Errorf("expected auth.json preserved on failure, got %v", err)
	}
}

func TestAuthRevoke_RejectsApiKeyOnlyStore(t *testing.T) {
	home := t.TempDir()
	t.Setenv("HOME", home)
	t.Setenv("GFTD_TOKEN", "")

	cs := newCaptureServer(http.StatusOK)
	defer cs.srv.Close()

	writeTokenStore(t, home, tokenStore{APIKey: "sk_live_abc"})

	err := runAuthRevoke([]string{"--pds", cs.srv.URL, "-q"})
	if err == nil {
		t.Fatal("expected error when store has only api_key")
	}
	if !strings.Contains(err.Error(), "revoke-api-key") {
		t.Errorf("unexpected error (should mention revoke-api-key): %v", err)
	}
	if len(cs.reqs) != 0 {
		t.Errorf("expected no revoke calls, got %d", len(cs.reqs))
	}
}
