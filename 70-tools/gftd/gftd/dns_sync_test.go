package main

import (
	"strings"
	"testing"
)

// ── buildDesiredDNSRecords: TXT + CNAME record generation ──

func TestBuildDesiredDNSRecords_TXTForEachActor(t *testing.T) {
	actors := []idActor{
		{Name: "kami", Domain: "kami.etzhayyim.com", DID: "did:web:kami.etzhayyim.com"},
		{Name: "hanrei", Domain: "hanrei.etzhayyim.com", DID: "did:plc:abc123"},
	}
	recs := buildDesiredDNSRecords(actors, nil, true, false, "etzhayyim.com")
	if len(recs) != 2 {
		t.Fatalf("expected 2 TXT records, got %d", len(recs))
	}
	for _, r := range recs {
		if r.Type != "TXT" {
			t.Errorf("expected TXT, got %s", r.Type)
		}
		if !strings.HasPrefix(r.Name, "_atproto.") {
			t.Errorf("TXT record name missing _atproto prefix: %s", r.Name)
		}
		if !strings.Contains(r.Content, "did=") {
			t.Errorf("TXT content missing did=: %q", r.Content)
		}
		if r.Comment != dnsSyncTXTComment {
			t.Errorf("comment missing prefix: %q", r.Comment)
		}
	}
}

func TestBuildDesiredDNSRecords_CNAMEForLegacyNanoids(t *testing.T) {
	actors := []idActor{
		{Name: "kami", Domain: "kami.etzhayyim.com", DID: "did:web:kami.etzhayyim.com"},
	}
	legacies := []idLegacy{
		{Actor: "kami", Nanoid: "k4m13ng1", Handle: "kami.etzhayyim.com", DID: "did:web:kami.etzhayyim.com"},
		{Actor: "hanrei", Nanoid: "h4nr31jp", Handle: "hanrei.etzhayyim.com", DID: "did:web:hanrei.etzhayyim.com"},
	}
	// TXT disabled, nanoid CNAMEs only
	recs := buildDesiredDNSRecords(actors, legacies, false, true, "etzhayyim.com")
	if len(recs) != 2 {
		t.Fatalf("expected 2 CNAME records, got %d", len(recs))
	}
	for _, r := range recs {
		if r.Type != "CNAME" {
			t.Errorf("expected CNAME, got %s", r.Type)
		}
		if !strings.HasSuffix(r.Name, ".etzhayyim.com") {
			t.Errorf("name not *.etzhayyim.com: %s", r.Name)
		}
		if !r.Proxied {
			t.Errorf("CNAME should be proxied: %s", r.Name)
		}
		if r.Comment != dnsSyncCNAMEComment {
			t.Errorf("comment wrong: %q", r.Comment)
		}
	}
}

func TestBuildDesiredDNSRecords_FilterByZone(t *testing.T) {
	actors := []idActor{
		{Name: "in-zone", Domain: "a.etzhayyim.com", DID: "did:web:a.etzhayyim.com"},
		{Name: "out-of-zone", Domain: "b.example.com", DID: "did:web:b.example.com"},
	}
	recs := buildDesiredDNSRecords(actors, nil, true, false, "etzhayyim.com")
	if len(recs) != 1 {
		t.Fatalf("expected 1 record (in-zone only), got %d", len(recs))
	}
	if recs[0].Name != "_atproto.a.etzhayyim.com" {
		t.Errorf("filter failed: %+v", recs[0])
	}
}

func TestBuildDesiredDNSRecords_DeterministicSort(t *testing.T) {
	actors := []idActor{
		{Name: "z-actor", Domain: "zeta.etzhayyim.com", DID: "did:web:zeta.etzhayyim.com"},
		{Name: "a-actor", Domain: "alpha.etzhayyim.com", DID: "did:web:alpha.etzhayyim.com"},
		{Name: "m-actor", Domain: "mid.etzhayyim.com", DID: "did:web:mid.etzhayyim.com"},
	}
	recs := buildDesiredDNSRecords(actors, nil, true, false, "etzhayyim.com")
	if len(recs) != 3 {
		t.Fatalf("got %d", len(recs))
	}
	// Sorted alphabetically by name
	if !(recs[0].Name < recs[1].Name && recs[1].Name < recs[2].Name) {
		t.Errorf("not sorted: %s %s %s", recs[0].Name, recs[1].Name, recs[2].Name)
	}
}

// ── diffDNSRecords: plan action classification ──

func TestDiffDNSRecords_CreateNew(t *testing.T) {
	desired := []cfDNSRecord{
		{Type: "TXT", Name: "_atproto.new.etzhayyim.com", Content: `"did=did:web:new.etzhayyim.com"`, Comment: dnsSyncTXTComment},
	}
	existing := []cfDNSRecord{}
	plan := diffDNSRecords(desired, existing)
	if len(plan) != 1 || plan[0].Action != "create" {
		t.Errorf("expected 1 create, got %+v", plan)
	}
}

func TestDiffDNSRecords_KeepUnchanged(t *testing.T) {
	rec := cfDNSRecord{
		Type: "TXT", Name: "_atproto.k.etzhayyim.com", Content: `"did=did:web:k"`,
		Comment: dnsSyncTXTComment, ID: "existing-id-123",
	}
	plan := diffDNSRecords([]cfDNSRecord{rec}, []cfDNSRecord{rec})
	if len(plan) != 1 || plan[0].Action != "keep" {
		t.Errorf("expected 1 keep, got %+v", plan)
	}
}

func TestDiffDNSRecords_UpdateOnContentChange(t *testing.T) {
	existing := cfDNSRecord{
		Type: "TXT", Name: "_atproto.k.etzhayyim.com", Content: `"did=did:web:OLD"`,
		Comment: dnsSyncTXTComment, ID: "rec-id-1",
	}
	desired := cfDNSRecord{
		Type: "TXT", Name: "_atproto.k.etzhayyim.com", Content: `"did=did:plc:NEW"`,
		Comment: dnsSyncTXTComment,
	}
	plan := diffDNSRecords([]cfDNSRecord{desired}, []cfDNSRecord{existing})
	if len(plan) != 1 || plan[0].Action != "update" {
		t.Errorf("expected update, got %+v", plan)
	}
	if plan[0].Record.ID != "rec-id-1" {
		t.Errorf("update should carry existing ID, got %q", plan[0].Record.ID)
	}
}

func TestDiffDNSRecords_DeleteOrphan(t *testing.T) {
	existing := cfDNSRecord{
		Type: "CNAME", Name: "stale.etzhayyim.com", Content: "old.etzhayyim.com",
		Comment: dnsSyncCNAMEComment, ID: "rec-id-stale",
	}
	plan := diffDNSRecords([]cfDNSRecord{}, []cfDNSRecord{existing})
	if len(plan) != 1 || plan[0].Action != "delete" {
		t.Errorf("expected 1 delete, got %+v", plan)
	}
}

// ── emitRoutingMapTS: routing-gateway map generation ──

func TestEmitRoutingMapTS_StructureAndDeterministic(t *testing.T) {
	legacies := []idLegacy{
		{Actor: "kami", Nanoid: "k4m13ng1", Handle: "kami.etzhayyim.com", DID: "did:web:kami.etzhayyim.com"},
		{Actor: "adr", Nanoid: "adr1m4d0", Handle: "adr.etzhayyim.com", DID: "did:web:adr.etzhayyim.com"},
		{Actor: "saiban", Nanoid: "sb4n0j1c", Handle: "saiban.etzhayyim.com", DID: "did:web:saiban.etzhayyim.com"},
	}
	ts := emitRoutingMapTS(legacies)
	for _, want := range []string{
		"export const LEGACY_NANOID_MAP",
		"export const PHASE4_DEPRECATE_AT",
		`"adr1m4d0": "adr.etzhayyim.com"`,
		`"k4m13ng1": "kami.etzhayyim.com"`,
		`"sb4n0j1c": "saiban.etzhayyim.com"`,
		"DO NOT EDIT BY HAND",
		"2026-10-01T00:00:00Z",
	} {
		if !strings.Contains(ts, want) {
			t.Errorf("emit missing %q in:\n%s", want, ts)
		}
	}
	idxAdr := strings.Index(ts, "adr1m4d0")
	idxKami := strings.Index(ts, "k4m13ng1")
	idxSai := strings.Index(ts, "sb4n0j1c")
	if !(idxAdr < idxKami && idxKami < idxSai) {
		t.Errorf("not sorted: adr=%d kami=%d saiban=%d", idxAdr, idxKami, idxSai)
	}
	shuffled := []idLegacy{legacies[2], legacies[0], legacies[1]}
	ts2 := emitRoutingMapTS(shuffled)
	if ts != ts2 {
		t.Errorf("emit not deterministic; outputs differ")
	}
}

func TestEmitRoutingMapTS_HandlesEmptyAndQuoted(t *testing.T) {
	ts := emitRoutingMapTS(nil)
	if !strings.Contains(ts, "Record<string, string>") {
		t.Errorf("empty input should still emit type signature")
	}
	if !strings.Contains(ts, "PHASE4_DEPRECATE_AT") {
		t.Errorf("missing footer constant")
	}
}

func TestDiffDNSRecords_MixedActions(t *testing.T) {
	existing := []cfDNSRecord{
		{Type: "TXT", Name: "_atproto.kept.etzhayyim.com", Content: "same", Comment: dnsSyncTXTComment, ID: "id-1"},
		{Type: "TXT", Name: "_atproto.updated.etzhayyim.com", Content: "old-val", Comment: dnsSyncTXTComment, ID: "id-2"},
		{Type: "CNAME", Name: "orphan.etzhayyim.com", Content: "some.etzhayyim.com", Comment: dnsSyncCNAMEComment, ID: "id-3"},
	}
	desired := []cfDNSRecord{
		{Type: "TXT", Name: "_atproto.kept.etzhayyim.com", Content: "same", Comment: dnsSyncTXTComment},
		{Type: "TXT", Name: "_atproto.updated.etzhayyim.com", Content: "new-val", Comment: dnsSyncTXTComment},
		{Type: "TXT", Name: "_atproto.fresh.etzhayyim.com", Content: "hi", Comment: dnsSyncTXTComment},
	}
	plan := diffDNSRecords(desired, existing)
	actionCount := map[string]int{}
	for _, p := range plan {
		actionCount[p.Action]++
	}
	if actionCount["keep"] != 1 || actionCount["update"] != 1 ||
		actionCount["create"] != 1 || actionCount["delete"] != 1 {
		t.Errorf("expected keep=1 update=1 create=1 delete=1, got %+v", actionCount)
	}
}
