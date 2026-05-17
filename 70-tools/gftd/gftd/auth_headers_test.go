package main

import (
	"net/http"
	"testing"
)

func TestResolveOrgHint_FromEnv(t *testing.T) {
	t.Setenv("GFTD_ORG_ID", "org-from-env")
	t.Setenv("HOME", t.TempDir())
	if got := resolveOrgHint(); got != "org-from-env" {
		t.Fatalf("resolveOrgHint=%q, want org-from-env", got)
	}
}

func TestSetAuthHeaders_SetsOrgFromEnv(t *testing.T) {
	t.Setenv("GFTD_ORG_ID", "org-from-env")
	t.Setenv("GFTD_TOKEN", "token-123")
	t.Setenv("HOME", t.TempDir())

	req, _ := http.NewRequest(http.MethodPost, "https://atproto.etzhayyim.com/xrpc/ai.gftd.kagami.sql", nil)
	setAuthHeaders(req)

	if got := req.Header.Get("Authorization"); got != "Bearer token-123" {
		t.Fatalf("Authorization=%q, want Bearer token-123", got)
	}
	if got := req.Header.Get("X-Gftd-Org-Id"); got != "org-from-env" {
		t.Fatalf("X-Gftd-Org-Id=%q, want org-from-env", got)
	}
}
