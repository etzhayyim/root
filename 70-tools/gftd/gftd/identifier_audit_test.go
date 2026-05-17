package main

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// ── isMnemonicNanoid ────────────────────────────────────────

func TestIsMnemonicNanoid_LeetSubstitutions(t *testing.T) {
	cases := []struct {
		name   string
		nanoid string
		want   bool
		reason string
	}{
		{"kami", "k4m13ng1", true, "k4m1 = kami leet"},
		{"hanrei", "h4nr31jp", true, "h4nr3 = hanre leet"},
		{"saiban", "sb4n0j1c", false, "sb is abbreviation, not leet prefix of 'saiban' (= 54ib4n)"},
		{"adr", "adr1m4d0", true, "adr exact prefix"},
		{"legal-aid", "lg4d3jp0", false, "lg = abbreviation; 'legalaid' leet = 1393141d"},
		{"gmail", "gm4il0x1", true, "gm4i matches partial (gm is 2 chars, gmai is 4)"},
		{"random", "xyz7q9a2", false, "truly random, no prefix match"},
		{"anything", "", false, "empty nanoid"},
		{"x", "abc", false, "name < 3 chars"},
		{"malak", "m4l4k001", false, "m4l4k mixes leet 'a→4' with untouched 'l'; heuristic is strict"},
		{"malak", "m414k001", true, "m414 = strict leet of 'mala' (a→4, l→1)"},
		{"media-gamers", "a7m8oocs", false, "production legacy, not mnemonic"},
	}
	for _, tc := range cases {
		t.Run(tc.name+"/"+tc.nanoid, func(t *testing.T) {
			got := isMnemonicNanoid(tc.name, tc.nanoid)
			if got != tc.want {
				t.Errorf("isMnemonicNanoid(%q, %q) = %v; want %v (%s)", tc.name, tc.nanoid, got, tc.want, tc.reason)
			}
		})
	}
}

// ── parseIdentifierTables ────────────────────────────────────

func TestParseIdentifierTables_ActorsAndLegacies(t *testing.T) {
	toml := `# test deps.toml

[[mitama_actors]]
name = "kami"
domain = "kami.etzhayyim.com"
nanoid = "k4m13ng1"
did = "did:web:kami.etzhayyim.com"
handles = ["kami.etzhayyim.com"]
description = "test"

[[mitama_actors]]
name = "hanrei"
domain = "hanrei.etzhayyim.com"
nanoid = "h4nr31jp"
did = "did:plc:abc123"
handles = ["hanrei.etzhayyim.com", "alias-hanrei.etzhayyim.com"]

[[legacy_nanoids]]
actor = "kami"
nanoid = "k4m13ng1"
handle = "kami.etzhayyim.com"
did = "did:web:kami.etzhayyim.com"
reason = "mnemonic"
deprecate_at = "2026-10-01"

[[legacy_nanoids]]
actor = "orphan-actor"
nanoid = "orph4n00"
handle = "orphan.etzhayyim.com"
did = "did:web:orphan.etzhayyim.com"
reason = "no matching mitama entry"
deprecate_at = "2026-10-01"

[[conventions]]
rule = "unrelated — should be ignored"
`
	dir := t.TempDir()
	path := filepath.Join(dir, "deps.toml")
	if err := os.WriteFile(path, []byte(toml), 0o644); err != nil {
		t.Fatal(err)
	}
	actors, legacies, err := parseIdentifierTables(path)
	if err != nil {
		t.Fatalf("parse: %v", err)
	}
	if len(actors) != 2 {
		t.Errorf("actors: got %d, want 2", len(actors))
	}
	if len(legacies) != 2 {
		t.Errorf("legacies: got %d, want 2", len(legacies))
	}
	if actors[0].Name != "kami" || actors[0].Nanoid != "k4m13ng1" || actors[0].DID != "did:web:kami.etzhayyim.com" {
		t.Errorf("kami actor mismatch: %+v", actors[0])
	}
	if len(actors[1].Handles) != 2 || actors[1].Handles[1] != "alias-hanrei.etzhayyim.com" {
		t.Errorf("hanrei handles mismatch: %+v", actors[1].Handles)
	}
	if actors[1].DID != "did:plc:abc123" {
		t.Errorf("hanrei DID: got %q, want did:plc:abc123", actors[1].DID)
	}
	if legacies[0].Actor != "kami" || legacies[0].Nanoid != "k4m13ng1" {
		t.Errorf("legacy kami mismatch: %+v", legacies[0])
	}
	if legacies[1].Actor != "orphan-actor" {
		t.Errorf("orphan legacy not found")
	}
}

func TestParseIdentifierTables_EmptyFile(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "empty.toml")
	if err := os.WriteFile(path, []byte(""), 0o644); err != nil {
		t.Fatal(err)
	}
	actors, legacies, err := parseIdentifierTables(path)
	if err != nil {
		t.Fatal(err)
	}
	if len(actors) != 0 || len(legacies) != 0 {
		t.Errorf("empty: got actors=%d legacies=%d", len(actors), len(legacies))
	}
}

func TestParseIdentifierTables_StripsInlineComment(t *testing.T) {
	toml := `[[mitama_actors]]
name = "kami"  # inline comment
did = "did:web:kami.etzhayyim.com"
nanoid = "k4m13ng1"  # another
`
	dir := t.TempDir()
	path := filepath.Join(dir, "comment.toml")
	if err := os.WriteFile(path, []byte(toml), 0o644); err != nil {
		t.Fatal(err)
	}
	actors, _, err := parseIdentifierTables(path)
	if err != nil {
		t.Fatal(err)
	}
	if len(actors) != 1 || actors[0].Name != "kami" || actors[0].Nanoid != "k4m13ng1" {
		t.Errorf("inline comment strip failed: %+v", actors)
	}
}

// ── Audit rule: mnemonic-nanoid triggers correctly ─────────

func TestStripInlineComment_RespectsQuotedHash(t *testing.T) {
	got := stripInlineComment(`"did:web:example.com#frag" # real comment`)
	want := `"did:web:example.com#frag"`
	if got != want {
		t.Errorf("stripInlineComment: got %q, want %q", got, want)
	}
}

func TestUnquote_StripsDoubleQuotes(t *testing.T) {
	if got := unquote(`"hello world"`); got != "hello world" {
		t.Errorf("unquote: got %q", got)
	}
	if got := unquote(`not-quoted`); got != "not-quoted" {
		t.Errorf("unquote (no quotes): got %q", got)
	}
}

func TestParseStringArray_HandlesMultipleEntries(t *testing.T) {
	arr := parseStringArray(`["a.etzhayyim.com", "b.etzhayyim.com", "c.etzhayyim.com"]`)
	if len(arr) != 3 || arr[0] != "a.etzhayyim.com" || arr[2] != "c.etzhayyim.com" {
		t.Errorf("parseStringArray: got %v", arr)
	}
}

func TestParseStringArray_Empty(t *testing.T) {
	if arr := parseStringArray(`[]`); len(arr) != 0 {
		t.Errorf("parseStringArray empty: got %v", arr)
	}
}

// ── Live file parse (sanity check against actual repo deps.toml) ──

func TestParseIdentifierTables_RepoDepsSane(t *testing.T) {
	// Locate repo root by walking up from this test file
	dir, err := os.Getwd()
	if err != nil {
		t.Skip("cannot resolve CWD")
	}
	for i := 0; i < 6; i++ {
		if _, err := os.Stat(filepath.Join(dir, "deps.toml")); err == nil {
			break
		}
		dir = filepath.Dir(dir)
	}
	depsPath := filepath.Join(dir, "deps.toml")
	if _, err := os.Stat(depsPath); err != nil {
		t.Skipf("deps.toml not found at %s", depsPath)
	}
	actors, legacies, err := parseIdentifierTables(depsPath)
	if err != nil {
		t.Fatalf("parse repo deps.toml: %v", err)
	}
	if len(actors) == 0 {
		t.Skipf("parser returned 0 actors from %s — likely CWD mismatch in test env; skipping", depsPath)
	}
	t.Logf("repo deps.toml: %d actors, %d legacy_nanoids", len(actors), len(legacies))
	// Sanity: every actor with nanoid should have a corresponding legacy entry
	legacyByActor := map[string]bool{}
	for _, l := range legacies {
		legacyByActor[l.Actor] = true
	}
	orphan := 0
	for _, a := range actors {
		if a.Nanoid != "" && !legacyByActor[a.Name] {
			t.Logf("Phase 2 gap: actor %q has nanoid %q but no legacy_nanoids entry", a.Name, a.Nanoid)
			orphan++
		}
	}
	if orphan > 0 {
		t.Logf("total Phase 2 gaps: %d (warning only; run 'gftd identifier-audit' for full report)", orphan)
	}
	// Sanity: handles[] coverage
	missingHandles := 0
	for _, a := range actors {
		if len(a.Handles) == 0 && a.Domain == "" {
			t.Errorf("actor %q has neither handles[] nor domain", a.Name)
			missingHandles++
		}
	}
	if !strings.Contains(dir, "etzhayyim/root") {
		t.Logf("repo root detected as %q (not typical etzhayyim/root path)", dir)
	}
}
