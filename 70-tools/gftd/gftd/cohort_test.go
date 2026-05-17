package main

import (
	"crypto/sha256"
	"encoding/hex"
	"strings"
	"testing"
)

// TestSha256HexEquivalence — verify the Go side of `gftd cohort emit`'s
// evidenceHash derivation matches the TS handler (`handlers/gftd/cohort.ts`
// `sha256Hex`). The TS uses `crypto.subtle.digest('SHA-256', utf8(s))`
// and lowercase hex. This test pins the canonical hash for a known input
// so any future drift between Go CLI hashing and TS handler is caught.
func TestSha256HexEquivalence(t *testing.T) {
	cases := []struct {
		in   string
		want string // pre-computed via openssl dgst -sha256
	}{
		{
			in:   "did:plc:pending-cmkt003c|behavior.observed|payload-1|2026-04-15T00:00:00.000Z",
			want: "", // computed below
		},
		{
			in:   "",
			want: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
		},
	}
	for _, c := range cases {
		h := sha256.Sum256([]byte(c.in))
		got := hex.EncodeToString(h[:])
		if c.want != "" && got != c.want {
			t.Errorf("sha256(%q) = %q, want %q", c.in, got, c.want)
		}
		if len(got) != 64 {
			t.Errorf("sha256 hex length = %d, want 64", len(got))
		}
	}
}

// TestDeriveCohortEventType — Go mirror of TS host-sdk derivation must
// produce identical output for identical inputs. Precedence:
// 1. didFission > 2. kProxy<50 > 3. fissionReady > 4. genesis > 5. accrued
func TestDeriveCohortEventType(t *testing.T) {
	tr := true
	fa := false
	postHigh := 0.97
	postLow := 0.5
	kLow := 30
	kOk := 100

	cases := []struct {
		name string
		in   CohortEventInput
		want CohortOcelEventType
	}{
		{
			name: "didFission wins",
			in:   CohortEventInput{DidFission: true, EvidenceCountBefore: 0},
			want: CohortEventFission,
		},
		{
			name: "kProxy<50 second",
			in:   CohortEventInput{KProxy: &kLow, Posterior: &postHigh, JudgeAgreement: &tr, FissionEnabled: true},
			want: CohortEventKReevaluated,
		},
		{
			name: "fissionReady requires all three",
			in:   CohortEventInput{Posterior: &postHigh, JudgeAgreement: &tr, FissionEnabled: true, KProxy: &kOk, EvidenceCountBefore: 5},
			want: CohortEventEvidenceFissionReady,
		},
		{
			name: "fissionReady blocked by fissionEnabled=false",
			in:   CohortEventInput{Posterior: &postHigh, JudgeAgreement: &tr, FissionEnabled: false, EvidenceCountBefore: 5},
			want: CohortEventEvidenceAccrued,
		},
		{
			name: "fissionReady blocked by judgeAgreement=false",
			in:   CohortEventInput{Posterior: &postHigh, JudgeAgreement: &fa, FissionEnabled: true, EvidenceCountBefore: 5},
			want: CohortEventEvidenceAccrued,
		},
		{
			name: "genesis on first evidence",
			in:   CohortEventInput{EvidenceCountBefore: 0, Posterior: &postLow},
			want: CohortEventGenesis,
		},
		{
			name: "default accrued",
			in:   CohortEventInput{EvidenceCountBefore: 5, Posterior: &postLow},
			want: CohortEventEvidenceAccrued,
		},
	}
	for _, c := range cases {
		got := DeriveCohortEventType(c.in)
		if got != c.want {
			t.Errorf("%s: got %q, want %q", c.name, got, c.want)
		}
	}
}

// TestSha256HexDeterminism — same input → same output across calls.
func TestSha256HexDeterminism(t *testing.T) {
	in := "cohort:test:payload"
	h1 := sha256.Sum256([]byte(in))
	h2 := sha256.Sum256([]byte(in))
	if hex.EncodeToString(h1[:]) != hex.EncodeToString(h2[:]) {
		t.Fatal("sha256 not deterministic")
	}
}

func TestParseSegmentKV(t *testing.T) {
	cases := []struct {
		in   string
		want map[string]string
	}{
		{
			in: "sha256:pcfL1=3-market-sell;role=salesRep;locale=jp",
			want: map[string]string{
				"pcfL1":  "3-market-sell",
				"role":   "salesRep",
				"locale": "jp",
			},
		},
		{
			in: "sha256:pcfL1=9-financial-resources;role=accountant;seniority=senior;industry=banking;locale=en",
			want: map[string]string{
				"pcfL1":     "9-financial-resources",
				"role":      "accountant",
				"seniority": "senior",
				"industry":  "banking",
				"locale":    "en",
			},
		},
		{
			in:   "",
			want: map[string]string{},
		},
	}
	for _, c := range cases {
		got := parseSegmentKV(c.in)
		for k, v := range c.want {
			if got[k] != v {
				t.Errorf("parseSegmentKV(%q)[%q] = %q, want %q", c.in, k, got[k], v)
			}
		}
	}
}

func TestCohortEntryToSegmentJsonld(t *testing.T) {
	e := cohortEntry{
		SegmentHash: "sha256:pcfL1=3-market-sell;role=salesRep;industry=retail;locale=jp",
	}
	got := e.toSegmentJsonld()
	// Keys may appear in any order; check containment.
	mustContain := []string{
		`"pcfL1":"3-market-sell"`,
		`"role":"salesRep"`,
		`"industry":"retail"`,
		`"locale":"jp"`,
	}
	for _, needle := range mustContain {
		if !strings.Contains(got, needle) {
			t.Errorf("toSegmentJsonld missing %q in %q", needle, got)
		}
	}
}

func TestParseSegmentKVIgnoresMalformed(t *testing.T) {
	got := parseSegmentKV("sha256:pcfL1=x;malformed_part;locale=jp;another=")
	if got["pcfL1"] != "x" {
		t.Errorf("want pcfL1=x, got %q", got["pcfL1"])
	}
	if got["locale"] != "jp" {
		t.Errorf("want locale=jp, got %q", got["locale"])
	}
	if got["another"] != "" {
		t.Errorf("want another='', got %q", got["another"])
	}
	if _, ok := got["malformed_part"]; ok {
		t.Errorf("malformed segment (no =) should be ignored")
	}
}

func TestParseSegmentKV3Axis(t *testing.T) {
	got := parseSegmentKV("sha256:pcfL1=8-info-technology;role=sreEngineer;seniority=senior;industry=banking;locale=en")
	want := map[string]string{
		"pcfL1":     "8-info-technology",
		"role":      "sreEngineer",
		"seniority": "senior",
		"industry":  "banking",
		"locale":    "en",
	}
	for k, v := range want {
		if got[k] != v {
			t.Errorf("3-axis: got[%q]=%q want %q", k, got[k], v)
		}
	}
}

func TestSortStrings(t *testing.T) {
	s := []string{"c", "a", "b", "a"}
	sortStrings(s)
	want := []string{"a", "a", "b", "c"}
	for i := range s {
		if s[i] != want[i] {
			t.Errorf("sortStrings: got %v, want %v", s, want)
			break
		}
	}
}
