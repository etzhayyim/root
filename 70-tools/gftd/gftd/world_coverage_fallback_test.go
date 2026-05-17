package main

import (
	"net/http"
	"strings"
	"testing"
)

func TestApplyHeartbeatAppFallback_AppliesWhenGraphEmpty(t *testing.T) {
	count, apps, applied := applyHeartbeatAppFallback(0, nil, []string{"a1", "a1", "  ", "b2"})
	if !applied {
		t.Fatal("expected fallback to apply")
	}
	if count != 2 {
		t.Fatalf("count=%d, want 2", count)
	}
	if apps == nil {
		t.Fatal("expected synthesized app rows")
	}
	if len(apps.Rows) != 2 {
		t.Fatalf("rows=%d, want 2", len(apps.Rows))
	}
	if got := toStr(apps.Rows[0][2]); got != "did:web:a1.etzhayyim.com" {
		t.Fatalf("did=%q, want did:web:a1.etzhayyim.com", got)
	}
}

func TestApplyHeartbeatAppFallback_SkipsWhenGraphHasApps(t *testing.T) {
	existing := &wcSqlResp{Rows: [][]any{{"x", "X", "did:web:x.etzhayyim.com"}}}
	count, apps, applied := applyHeartbeatAppFallback(3, existing, []string{"a1", "b2"})
	if applied {
		t.Fatal("expected fallback not to apply")
	}
	if count != 3 {
		t.Fatalf("count=%d, want 3", count)
	}
	if apps != existing {
		t.Fatal("expected existing app rows to be preserved")
	}
}

func TestApplyCoverageSummaryFallback_FromAppRows(t *testing.T) {
	apps := &wcSqlResp{Rows: [][]any{{"a1"}, {"b2"}, {"c3"}}}
	dids, profiles := applyCoverageSummaryFallback(0, 0, apps)
	if dids != 3 || profiles != 3 {
		t.Fatalf("dids=%d profiles=%d, want 3/3", dids, profiles)
	}
}

func TestApplyCoverageSummaryFallback_PreservesExistingCounts(t *testing.T) {
	apps := &wcSqlResp{Rows: [][]any{{"a1"}, {"b2"}}}
	dids, profiles := applyCoverageSummaryFallback(5, 7, apps)
	if dids != 5 || profiles != 7 {
		t.Fatalf("dids=%d profiles=%d, want 5/7", dids, profiles)
	}
}

func TestApplyCoverageSummaryFallback_UsesAppRowsAsFloor(t *testing.T) {
	apps := &wcSqlResp{Rows: [][]any{{"a1"}, {"b2"}, {"c3"}}}
	dids, profiles := applyCoverageSummaryFallback(2, 1, apps)
	if dids != 3 || profiles != 3 {
		t.Fatalf("dids=%d profiles=%d, want 3/3", dids, profiles)
	}
}

func TestBuildHeartbeatDomainCounts_MapsNanoidToLocalDomain(t *testing.T) {
	heartbeat := []string{"n1", "n2", "n3"}
	local := []localApp{
		{project: "dns", nanoid: "n1", did: "did:web:dns.etzhayyim.com", app: "dns.etzhayyim.com"},
		{project: "autorace", nanoid: "n2", did: "did:web:autorace.etzhayyim.com", app: "autorace.etzhayyim.com"},
	}
	counts := buildHeartbeatDomainCounts(heartbeat, local)
	if counts["dns"] == 0 {
		t.Fatalf("dns count=%d, want >0", counts["dns"])
	}
	if counts["autorace"] == 0 {
		t.Fatalf("autorace count=%d, want >0", counts["autorace"])
	}
}

func TestSetCoverageAuthHeaders_OrgOverrideWins(t *testing.T) {
	t.Setenv("GFTD_ORG_ID", "env-org")
	t.Setenv("GFTD_TOKEN", "tok")
	t.Setenv("HOME", t.TempDir())

	req, _ := http.NewRequest(http.MethodPost, "https://atproto.etzhayyim.com/xrpc/ai.gftd.kagami.sql", nil)
	setCoverageAuthHeaders(req, "cli-org")

	if got := req.Header.Get("X-Gftd-Org-Id"); got != "cli-org" {
		t.Fatalf("X-Gftd-Org-Id=%q, want cli-org", got)
	}
}

func TestBuildRecordDomainCounts_AggregatesByDidHost(t *testing.T) {
	resp := &wcSqlResp{
		Rows: [][]any{
			{"did:web:dns.etzhayyim.com:zone:example", 3},
			{"did:web:dns.etzhayyim.com:zone:example2", 2},
			{"did:web:autorace.etzhayyim.com:venue:kawaguchi", 1},
		},
	}
	got := buildRecordDomainCounts(resp)
	if got["dns"] != 5 {
		t.Fatalf("dns recordCount=%d, want 5", got["dns"])
	}
	if got["autorace"] != 1 {
		t.Fatalf("autorace recordCount=%d, want 1", got["autorace"])
	}
}

func TestEffectiveCollectedCount_UsesLargerOfDidOrRecord(t *testing.T) {
	if got := effectiveCollectedCount(3, 7); got != 7 {
		t.Fatalf("effectiveCollectedCount(3,7)=%d, want 7", got)
	}
	if got := effectiveCollectedCount(9, 2); got != 9 {
		t.Fatalf("effectiveCollectedCount(9,2)=%d, want 9", got)
	}
}

func TestInferCountSource(t *testing.T) {
	if got := inferCountSource(1, 0, 0); got != "graph" {
		t.Fatalf("inferCountSource graph=%q, want graph", got)
	}
	if got := inferCountSource(0, 0, 2); got != "heartbeat" {
		t.Fatalf("inferCountSource heartbeat=%q, want heartbeat", got)
	}
	if got := inferCountSource(1, 0, 2); got != "mixed" {
		t.Fatalf("inferCountSource mixed=%q, want mixed", got)
	}
}

func TestBuildCollectionDomainCounts_AssignsBestDomain(t *testing.T) {
	resp := &wcSqlResp{
		Rows: [][]any{
			{"ai.gftd.apps.autorace.venue", 4},
			{"ai.gftd.apps.dns.zone", 7},
		},
	}
	domains := []worldDomain{
		{Domain: "autorace", App: "autorace.etzhayyim.com", DIDLabel: "venue"},
		{Domain: "dns", App: "dns.etzhayyim.com", DIDLabel: "zone"},
	}
	got := buildCollectionDomainCounts(resp, domains)
	if got["autorace"] != 4 {
		t.Fatalf("autorace=%d, want 4", got["autorace"])
	}
	if got["dns"] != 7 {
		t.Fatalf("dns=%d, want 7", got["dns"])
	}
}

func TestResolveSinceTime_Duration(t *testing.T) {
	_, iso, ok, err := resolveSinceTime("24h")
	if err != nil || !ok {
		t.Fatalf("resolveSinceTime err=%v ok=%v, want ok", err, ok)
	}
	if !strings.Contains(iso, "T") {
		t.Fatalf("since iso=%q not RFC3339-like", iso)
	}
}
