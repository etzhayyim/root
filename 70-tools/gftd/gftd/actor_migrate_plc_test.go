package main

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// ── mockDidPlc: deterministic offline DID derivation ──

func TestMockDidPlc_DeterministicAndPrefix(t *testing.T) {
	cases := []string{"adr", "kami", "legal-aid", "kami-sabiotoshi", "Z9_X-Y"}
	for _, name := range cases {
		t.Run(name, func(t *testing.T) {
			a := mockDidPlc(name)
			b := mockDidPlc(name)
			if a != b {
				t.Errorf("mockDidPlc not deterministic: %q vs %q", a, b)
			}
			if !strings.HasPrefix(a, "did:plc:") {
				t.Errorf("missing did:plc: prefix: %q", a)
			}
			tail := strings.TrimPrefix(a, "did:plc:")
			if len(tail) != 24 {
				t.Errorf("did:plc tail length = %d, want 24: %q", len(tail), a)
			}
			// Tail must be lowercase alphanumeric (mock uses lowercase, padded with 'a')
			for _, r := range tail {
				if !(r >= 'a' && r <= 'z') && !(r >= '0' && r <= '9') {
					t.Errorf("invalid char in tail %q: %q", tail, r)
					break
				}
			}
		})
	}
}

func TestMockDidPlc_DifferentNamesProduceDifferentDIDs(t *testing.T) {
	a := mockDidPlc("kami")
	b := mockDidPlc("hanrei")
	if a == b {
		t.Errorf("mockDidPlc collision: %q vs %q", a, b)
	}
}

func TestMockDidPlc_LowercaseAndStripsSpecialChars(t *testing.T) {
	got := mockDidPlc("Kami-Sabiotoshi")
	if !strings.Contains(got, "kamisabiotoshi") {
		t.Errorf("expected lowercased + stripped name in DID, got %q", got)
	}
}

// ── patchActorDID: deps.toml rewrite ──

func TestPatchActorDID_ReplacesDIDAndAddsLegacyDidWeb(t *testing.T) {
	tomlBefore := `# header
[[mitama_actors]]
name = "adr"
domain = "adr.etzhayyim.com"
nanoid = "adr1m4d0"
did = "did:web:adr.etzhayyim.com"
handles = ["adr.etzhayyim.com"]
description = "ADR test"

[[mitama_actors]]
name = "kami"
did = "did:web:kami.etzhayyim.com"
description = "untouched"
`
	dir := t.TempDir()
	path := filepath.Join(dir, "deps.toml")
	if err := os.WriteFile(path, []byte(tomlBefore), 0o644); err != nil {
		t.Fatal(err)
	}
	err := patchActorDID(path, "adr", "did:plc:abc123abc123abc123abc12", "did:web:adr.etzhayyim.com")
	if err != nil {
		t.Fatalf("patchActorDID: %v", err)
	}
	updated, _ := os.ReadFile(path)
	s := string(updated)

	if !strings.Contains(s, `did = "did:plc:abc123abc123abc123abc12"`) {
		t.Errorf("did= not replaced; got:\n%s", s)
	}
	if !strings.Contains(s, `legacy_did_web = "did:web:adr.etzhayyim.com"`) {
		t.Errorf("legacy_did_web not inserted; got:\n%s", s)
	}
	// kami block must remain untouched
	if !strings.Contains(s, `[[mitama_actors]]
name = "kami"
did = "did:web:kami.etzhayyim.com"`) {
		t.Errorf("kami block was modified unexpectedly; got:\n%s", s)
	}
}

func TestPatchActorDID_NotFoundReturnsError(t *testing.T) {
	tomlBefore := `[[mitama_actors]]
name = "kami"
did = "did:web:kami.etzhayyim.com"
`
	dir := t.TempDir()
	path := filepath.Join(dir, "deps.toml")
	if err := os.WriteFile(path, []byte(tomlBefore), 0o644); err != nil {
		t.Fatal(err)
	}
	err := patchActorDID(path, "nonexistent", "did:plc:x", "did:web:x.etzhayyim.com")
	if err == nil {
		t.Errorf("expected error for unknown actor, got nil")
	}
	if !strings.Contains(err.Error(), "did field not found") {
		t.Errorf("error message: %v", err)
	}
}

func TestPatchActorDID_IdempotentSkipIfLegacyAlreadyPresent(t *testing.T) {
	tomlBefore := `[[mitama_actors]]
name = "adr"
did = "did:plc:existing"
legacy_did_web = "did:web:adr.etzhayyim.com"
description = "already migrated"
`
	dir := t.TempDir()
	path := filepath.Join(dir, "deps.toml")
	if err := os.WriteFile(path, []byte(tomlBefore), 0o644); err != nil {
		t.Fatal(err)
	}
	// Running again should NOT add a second legacy_did_web line
	err := patchActorDID(path, "adr", "did:plc:newer", "did:web:adr.etzhayyim.com")
	if err != nil {
		t.Fatalf("patchActorDID: %v", err)
	}
	updated, _ := os.ReadFile(path)
	count := strings.Count(string(updated), "legacy_did_web =")
	if count != 1 {
		t.Errorf("legacy_did_web duplicated: count=%d, content:\n%s", count, string(updated))
	}
}

// ── pickMode: human-readable labeling ──

func TestPickMode_AllCombinations(t *testing.T) {
	cases := []struct {
		apply, offline bool
		want           string
	}{
		{true, true, "offline + apply"},
		{false, true, "offline + dry-run"},
		{true, false, "apply (PDS"},
		{false, false, "dry-run (PDS"},
	}
	for _, tc := range cases {
		got := pickMode(tc.apply, tc.offline)
		if !strings.Contains(got, tc.want) {
			t.Errorf("pickMode(apply=%v, offline=%v) = %q; want substring %q", tc.apply, tc.offline, got, tc.want)
		}
	}
}
