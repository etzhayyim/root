package main

import (
	"bytes"
	"net/http"
	"os"
	"strings"
	"testing"
)

func TestSeedHelpersCoverAuthLoggingAndKeys(t *testing.T) {
	req, err := http.NewRequest("GET", "https://example.com", nil)
	if err != nil {
		t.Fatalf("new request: %v", err)
	}
	setWriteAuthHeaders(req, "token-123")
	if got := req.Header.Get("Authorization"); got != "Bearer token-123" {
		t.Fatalf("Authorization = %q", got)
	}

	oldStdout := os.Stdout
	r, w, err := os.Pipe()
	if err != nil {
		t.Fatalf("pipe: %v", err)
	}
	os.Stdout = w
	logSeedDIDWrite(map[string]any{
		"value": map[string]any{
			"id":           "did:web:sample.etzhayyim.com:actor:one",
			"display_name": "Actor One",
		},
	})
	_ = w.Close()
	os.Stdout = oldStdout

	var buf bytes.Buffer
	if _, err := buf.ReadFrom(r); err != nil {
		t.Fatalf("read stdout: %v", err)
	}
	if !strings.Contains(buf.String(), "did:web:sample.etzhayyim.com:actor:one") {
		t.Fatalf("unexpected log: %q", buf.String())
	}

	if got := collectionToLabelGo("ai.gftd.apps.sample.my_entry"); got != "MyEntry" {
		t.Fatalf("collectionToLabelGo = %q", got)
	}
	if got := seedStableRKey(" DID:Web:Sample.etzhayyim.com / Actor One "); got != "did-web-sample.etzhayyim.com-actor-one" {
		t.Fatalf("seedStableRKey = %q", got)
	}
}

func TestBuildSeedRegistryContainsActorDidAndCollectionData(t *testing.T) {
	registry := buildSeedRegistry()
	if len(registry) == 0 {
		t.Fatal("expected seed registry entries")
	}

	var found bool
	for _, def := range registry {
		if len(def.DIDs) > 0 && len(def.Records) > 0 {
			found = true
			if def.Domain == "" || def.Nanoid == "" || def.DID == "" {
				t.Fatalf("incomplete seed def: %+v", def)
			}
			if def.DIDs[0].Path == "" || def.DIDs[0].DisplayName == "" {
				t.Fatalf("expected DID data: %+v", def.DIDs[0])
			}
			if def.Records[0].Collection == "" || len(def.Records[0].Items) == 0 {
				t.Fatalf("expected collection items: %+v", def.Records[0])
			}
			break
		}
	}
	if !found {
		t.Fatal("expected at least one seed definition with DIDs and records")
	}
}

func TestFundSeedsProvideBroadCoverageBaseline(t *testing.T) {
	registry := buildSeedRegistry()

	var fundDef *seedDef
	for i := range registry {
		if registry[i].Domain == "fund" {
			fundDef = &registry[i]
			break
		}
	}
	if fundDef == nil {
		t.Fatal("expected fund seed definition")
	}

	collections := map[string]int{}
	for _, coll := range fundDef.Records {
		collections[coll.Collection] = len(coll.Items)
	}

	for _, collection := range []string{
		"ai.gftd.apps.fund.fund",
		"ai.gftd.apps.fund.manager",
		"ai.gftd.apps.fund.investor",
		"ai.gftd.apps.fund.investee",
		"ai.gftd.apps.fund.metric",
		"ai.gftd.apps.fund.commitment",
	} {
		if collections[collection] < 20 {
			t.Fatalf("%s has only %d seeded items", collection, collections[collection])
		}
	}

	fundKinds := map[string]bool{}
	investorTypes := map[string]bool{}
	for _, coll := range fundDef.Records {
		switch coll.Collection {
		case "ai.gftd.apps.fund.fund":
			for _, item := range coll.Items {
				kind, _ := item.Data["fund_kind"].(string)
				if kind != "" {
					fundKinds[kind] = true
				}
			}
		case "ai.gftd.apps.fund.investor":
			for _, item := range coll.Items {
				kind, _ := item.Data["investor_type"].(string)
				if kind != "" {
					investorTypes[kind] = true
				}
			}
		}
	}

	for _, kind := range []string{
		"sovereign_fund",
		"mutual_fund",
		"pension_fund",
		"private_fund",
		"government_fund",
		"investor_fund",
	} {
		if !fundKinds[kind] {
			t.Fatalf("missing seeded fund_kind %q", kind)
		}
	}
	if !investorTypes["government-lp"] || !investorTypes["sovereign-lp"] || !investorTypes["pension-lp"] {
		t.Fatalf("investor coverage missing core LP archetypes: %+v", investorTypes)
	}
}
