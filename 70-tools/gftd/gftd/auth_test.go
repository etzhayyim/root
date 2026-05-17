package main

import (
	"bytes"
	"encoding/base64"
	"encoding/json"
	"io"
	"os"
	"strings"
	"testing"
)

func testJWTWithSub(sub string) string {
	header := base64.RawURLEncoding.EncodeToString([]byte(`{"alg":"HS256","typ":"JWT"}`))
	payload, _ := json.Marshal(map[string]string{"sub": sub})
	body := base64.RawURLEncoding.EncodeToString(payload)
	return header + "." + body + ".sig"
}

func TestQueryControlledDIDs_RequiresDatabaseURL(t *testing.T) {
	token := testJWTWithSub("did:web:auth.etzhayyim.com:user:test123")

	// Isolate from local ~/.gftd auth state.
	t.Setenv("HOME", t.TempDir())
	t.Setenv("GFTD_TOKEN", "")
	t.Setenv("GFTD_DATABASE_URL", "")
	t.Setenv("DATABASE_URL", "")

	_, err := queryControlledDIDs(token)
	if err == nil {
		t.Fatal("expected database URL error")
	}
	if !strings.Contains(err.Error(), "database URL is required") {
		t.Fatalf("unexpected error: %v", err)
	}
}

func TestPrintWorldCoverageText_IncludesAuthStatus(t *testing.T) {
	report := &worldCoverageReport{
		EvaluatedAt: "2026-04-02T08:30:00Z",
		PDS:         defaultPDSURL,
		Auth: wcAuthStatus{
			Mode:      "authenticated (anon scope)",
			OrgID:     "anon",
			ActiveDID: "did:web:auth.etzhayyim.com:user:test123",
		},
		Summary: wcSummary{
			TotalApps:     0,
			TotalDIDs:     1,
			TotalProfiles: 1,
			WorldCoverage: 0,
		},
	}

	oldStdout := os.Stdout
	r, w, err := os.Pipe()
	if err != nil {
		t.Fatalf("pipe: %v", err)
	}
	os.Stdout = w
	printWorldCoverageText(report, 0)
	_ = w.Close()
	os.Stdout = oldStdout

	var buf bytes.Buffer
	if _, err := io.Copy(&buf, r); err != nil {
		t.Fatalf("read stdout: %v", err)
	}
	out := buf.String()
	if !strings.Contains(out, "Auth:         authenticated (anon scope) / org:anon / did:did:web:auth.etzhayyim.com:user:test123") {
		t.Fatalf("auth status line missing from output:\n%s", out)
	}
}
