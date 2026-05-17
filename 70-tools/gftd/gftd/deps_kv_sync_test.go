package main

import (
	"encoding/json"
	"strings"
	"testing"
)

func TestBuildKVActorRecords_OneEntryPerActorPlusIndex(t *testing.T) {
	actors := []idActor{
		{Name: "kami", DID: "did:web:kami.etzhayyim.com", Domain: "kami.etzhayyim.com", Nanoid: "k4m13ng1"},
		{Name: "adr", DID: "did:plc:abc123", Domain: "adr.etzhayyim.com", Nanoid: "adr1m4d0"},
	}
	out := buildKVActorRecords(actors)
	if len(out) != 3 {
		t.Fatalf("expected 3 entries (2 actors + 1 index), got %d", len(out))
	}

	// Sorted alphabetically by name → adr first
	if out[0].Key != "actor:adr" {
		t.Errorf("expected first key actor:adr, got %s", out[0].Key)
	}
	if out[1].Key != "actor:kami" {
		t.Errorf("expected second key actor:kami, got %s", out[1].Key)
	}
	if out[2].Key != "actors:index" {
		t.Errorf("expected last key actors:index, got %s", out[2].Key)
	}
}

func TestBuildKVActorRecords_PreservesDIDAndHandle(t *testing.T) {
	actors := []idActor{
		{Name: "adr", DID: "did:plc:abc123", Domain: "adr.etzhayyim.com", Nanoid: "adr1m4d0"},
	}
	out := buildKVActorRecords(actors)
	var rec kvActorRecord
	if err := json.Unmarshal([]byte(out[0].Value), &rec); err != nil {
		t.Fatalf("decode: %v", err)
	}
	if rec.Name != "adr" || rec.DID != "did:plc:abc123" || rec.Handle != "adr.etzhayyim.com" || rec.Nanoid != "adr1m4d0" {
		t.Errorf("record fields mismatch: %+v", rec)
	}
}

func TestBuildKVActorRecords_HandleFallbackToHandlesArray(t *testing.T) {
	actors := []idActor{
		{Name: "kami", DID: "did:web:kami.etzhayyim.com", Handles: []string{"kami.etzhayyim.com", "alt-kami.etzhayyim.com"}},
	}
	out := buildKVActorRecords(actors)
	var rec kvActorRecord
	json.Unmarshal([]byte(out[0].Value), &rec)
	if rec.Handle != "kami.etzhayyim.com" {
		t.Errorf("expected handle from Handles[0], got %q", rec.Handle)
	}
}

func TestBuildKVActorRecords_ActorsIndexHasAllNames(t *testing.T) {
	actors := []idActor{
		{Name: "z-last", DID: "did:web:z.etzhayyim.com", Domain: "z.etzhayyim.com"},
		{Name: "a-first", DID: "did:web:a.etzhayyim.com", Domain: "a.etzhayyim.com"},
		{Name: "m-mid", DID: "did:web:m.etzhayyim.com", Domain: "m.etzhayyim.com"},
	}
	out := buildKVActorRecords(actors)
	indexEntry := out[len(out)-1]
	if indexEntry.Key != "actors:index" {
		t.Fatalf("last entry must be actors:index, got %s", indexEntry.Key)
	}
	var names []string
	if err := json.Unmarshal([]byte(indexEntry.Value), &names); err != nil {
		t.Fatalf("index JSON decode: %v", err)
	}
	if len(names) != 3 {
		t.Errorf("expected 3 names in index, got %d", len(names))
	}
	// Sorted: a-first, m-mid, z-last
	if names[0] != "a-first" || names[2] != "z-last" {
		t.Errorf("index not sorted: %v", names)
	}
}

func TestBuildKVActorRecords_DeterministicOrder(t *testing.T) {
	actors := []idActor{
		{Name: "kami", DID: "did:web:kami", Domain: "kami.etzhayyim.com"},
		{Name: "adr", DID: "did:web:adr", Domain: "adr.etzhayyim.com"},
	}
	out1 := buildKVActorRecords(actors)
	// Reverse input → must produce same output
	reversed := []idActor{actors[1], actors[0]}
	out2 := buildKVActorRecords(reversed)
	for i := range out1 {
		if out1[i].Key != out2[i].Key || out1[i].Value != out2[i].Value {
			t.Errorf("deterministic violated at %d", i)
		}
	}
}

func TestDiffKVRecords_AddUpdateDeleteKeep(t *testing.T) {
	desired := []cfKVBulkEntry{
		{Key: "actor:adr", Value: `{"name":"adr"}`},
		{Key: "actor:kami", Value: `{"name":"kami"}`},
		{Key: "actors:index", Value: `["adr","kami"]`},
	}
	existing := map[string]bool{
		"actor:kami":   true, // → update
		"actor:orphan": true, // → delete
		"actors:index": true, // → update
	}
	plan := diffKVRecords(desired, existing)
	counts := map[string]int{}
	for _, p := range plan {
		counts[p.Action]++
	}
	if counts["add"] != 1 || counts["update"] != 2 || counts["delete"] != 1 {
		t.Errorf("expected add=1 update=2 delete=1, got %+v", counts)
	}
	// Orphan delete should be present
	found := false
	for _, p := range plan {
		if p.Action == "delete" && p.Key == "actor:orphan" {
			found = true
		}
	}
	if !found {
		t.Errorf("expected actor:orphan delete in plan, got %+v", plan)
	}
}

func TestDiffKVRecords_AllAddWhenEmpty(t *testing.T) {
	desired := []cfKVBulkEntry{
		{Key: "actor:a", Value: "{}"},
		{Key: "actors:index", Value: "[]"},
	}
	plan := diffKVRecords(desired, map[string]bool{})
	if len(plan) != 2 {
		t.Fatalf("expected 2 plan items, got %d", len(plan))
	}
	for _, p := range plan {
		if p.Action != "add" {
			t.Errorf("expected add, got %s for %s", p.Action, p.Key)
		}
	}
}

func TestKvActorRecord_OmitEmptyOptionalFields(t *testing.T) {
	rec := kvActorRecord{Name: "x", DID: "did:plc:y", Handle: "x.etzhayyim.com"}
	body, _ := json.Marshal(rec)
	s := string(body)
	if strings.Contains(s, "nanoid") || strings.Contains(s, "legacyDidWeb") || strings.Contains(s, "description") {
		t.Errorf("optional fields should omit when empty, got %s", s)
	}
}
