package main

import (
	"strings"
	"testing"
)

func TestDidWebDocumentURL(t *testing.T) {
	tests := []struct {
		name string
		did  string
		want string
	}{
		{
			name: "root did",
			did:  "did:web:tnt4ib0d.etzhayyim.com",
			want: "https://tnt4ib0d.etzhayyim.com/.well-known/did.json",
		},
		{
			name: "path did",
			did:  "did:web:example.com:users:alice",
			want: "https://example.com/users/alice/did.json",
		},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			got, err := didWebDocumentURL(tc.did)
			if err != nil {
				t.Fatalf("didWebDocumentURL() error = %v", err)
			}
			if got != tc.want {
				t.Fatalf("didWebDocumentURL() = %q, want %q", got, tc.want)
			}
		})
	}
}

func TestDidWebNanoid(t *testing.T) {
	tests := []struct {
		name   string
		did    string
		want   string
		wantOK bool
	}{
		{
			name:   "gftd host",
			did:    "did:web:tnt4ib0d.etzhayyim.com",
			want:   "tnt4ib0d",
			wantOK: true,
		},
		{
			name:   "non gftd host",
			did:    "did:web:example.com",
			want:   "",
			wantOK: false,
		},
		{
			name:   "path did not accepted for nanoid",
			did:    "did:web:tnt4ib0d.etzhayyim.com:users:alice",
			want:   "",
			wantOK: false,
		},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			got, ok := didWebNanoid(tc.did)
			if ok != tc.wantOK {
				t.Fatalf("didWebNanoid() ok = %v, want %v", ok, tc.wantOK)
			}
			if got != tc.want {
				t.Fatalf("didWebNanoid() = %q, want %q", got, tc.want)
			}
		})
	}
}

func TestCompactSnippet(t *testing.T) {
	got := compactSnippet("line1\nline2\r\nline3", 12)
	if got != "line1 lin..." {
		t.Fatalf("compactSnippet() = %q, want %q", got, "line1 lin...")
	}
}

func TestDidToSlug(t *testing.T) {
	got := didToSlug("did:web:tnt4ib0d.etzhayyim.com")
	if got != "did-web-tnt4ib0d-gftd-ai" {
		t.Fatalf("didToSlug() = %q", got)
	}
}

func TestBuildDidDocumentTemplate(t *testing.T) {
	did := "did:web:tnt4ib0d.etzhayyim.com"
	doc := buildDidDocumentTemplate(did)
	id, _ := doc["id"].(string)
	if id != did {
		t.Fatalf("template id = %q, want %q", id, did)
	}
	vm, ok := doc["verificationMethod"].([]map[string]any)
	if !ok || len(vm) == 0 {
		t.Fatalf("verificationMethod missing")
	}
}

func TestBuildActorRecommendations(t *testing.T) {
	recs := buildActorRecommendations("did:web:tnt4ib0d.etzhayyim.com", []hinshitsuFleetFinding{
		{Severity: "critical", Category: "did_document"},
		{Severity: "high", Category: "verification"},
		{Severity: "medium", Category: "citations"},
		{Severity: "medium", Category: "citations"}, // dedupe check
	})
	if len(recs) < 3 {
		t.Fatalf("expected >=3 recommendations, got %d (%v)", len(recs), recs)
	}
	foundDidDoc := false
	foundVerification := false
	foundCitation := false
	for _, r := range recs {
		if containsAll(r, "did.json", "tnt4ib0d") {
			foundDidDoc = true
		}
		if containsAll(r, "verificationMethod", "publicKey") {
			foundVerification = true
		}
		if containsAll(r, "出典", "URL") {
			foundCitation = true
		}
	}
	if !foundDidDoc {
		t.Fatalf("did doc recommendation missing: %v", recs)
	}
	if !foundVerification {
		t.Fatalf("verification recommendation missing: %v", recs)
	}
	if !foundCitation {
		t.Fatalf("citation recommendation missing: %v", recs)
	}
}

func TestActorActionPriority(t *testing.T) {
	tests := []struct {
		name     string
		score    float64
		minScore float64
		findings []hinshitsuFleetFinding
		want     string
	}{
		{
			name:     "above threshold",
			score:    10.5,
			minScore: 10,
			findings: nil,
			want:     "P3",
		},
		{
			name:     "critical finding",
			score:    5.5,
			minScore: 10,
			findings: []hinshitsuFleetFinding{{Severity: "critical", Category: "did_document"}},
			want:     "P0",
		},
		{
			name:     "high finding",
			score:    8.5,
			minScore: 10,
			findings: []hinshitsuFleetFinding{{Severity: "high", Category: "verification"}},
			want:     "P1",
		},
		{
			name:     "medium only",
			score:    9.2,
			minScore: 10,
			findings: []hinshitsuFleetFinding{{Severity: "medium", Category: "citations"}},
			want:     "P2",
		},
	}
	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			got := actorActionPriority(tc.score, tc.minScore, tc.findings)
			if got != tc.want {
				t.Fatalf("actorActionPriority()=%s want=%s", got, tc.want)
			}
		})
	}
}

func containsAll(s string, terms ...string) bool {
	for _, term := range terms {
		if !strings.Contains(s, term) {
			return false
		}
	}
	return true
}
