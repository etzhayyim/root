package main

import (
	"context"
	"os"
	"strings"
	"testing"

	"github.com/etzhayyim/root/70-tools/gftd/gftd/db"
)

func requireDomainCoverageDB(t *testing.T) {
	t.Helper()
	dsn := strings.TrimSpace(getenvAny("GFTD_DATABASE_URL", "DATABASE_URL"))
	if dsn == "" {
		t.Skip("integration DB not configured")
	}
}

func getenvAny(keys ...string) string {
	for _, k := range keys {
		if v := strings.TrimSpace(os.Getenv(k)); v != "" {
			return v
		}
	}
	return ""
}

func TestIntegrationDomainCoverageMVExistsAndReturnsRows(t *testing.T) {
	requireDomainCoverageDB(t)

	ctx := context.Background()
	resp, err := db.RawQuery(ctx, `
SELECT kind, authority_rate, live_coverage_record
FROM mv_domain_coverage_live
ORDER BY kind
LIMIT 5`)
	if err != nil {
		t.Fatalf("mv_domain_coverage_live query failed: %v", err)
	}
	if len(resp.Rows) == 0 {
		t.Fatal("mv_domain_coverage_live returned no rows")
	}
	if got := parseStringLike(resp.Rows[0]["kind"]); got == "" {
		t.Fatal("first mv_domain_coverage_live row has empty kind")
	}
}

func TestIntegrationDomainCoverageReconciliationUsesMV(t *testing.T) {
	requireDomainCoverageDB(t)

	domains := make([]coverageDomain, 0, len(authorityDomains))
	for _, d := range authorityDomains {
		if d.Kind == "private" {
			continue
		}
		seed := d.AuthoritySeed + d.RuleSeed + d.ScopeSeed
		target := d.AuthorityTarget + d.RuleTarget + d.ScopeTarget
		if target > 0 {
			d.CoverageRate = float64(seed) / float64(target)
		}
		domains = append(domains, d)
	}

	recon, err := collectCoverageReconciliationKagami(kagamiConfig{}, domains)
	if err != nil {
		t.Fatalf("collectCoverageReconciliationKagami failed: %v", err)
	}
	if len(recon) == 0 {
		t.Fatal("expected reconciliation rows")
	}
	found := false
	for _, row := range recon {
		if row.LiveCountSource != "risingwave:mv_domain_coverage_live" {
			t.Fatalf("unexpected live count source for %s: %s", row.Kind, row.LiveCountSource)
		}
		if row.Kind == "community" {
			found = true
		}
	}
	if !found {
		t.Fatal("expected community reconciliation row")
	}
}

func TestIntegrationActorSocialMVsReturnRows(t *testing.T) {
	requireDomainCoverageDB(t)

	ctx := context.Background()
	resp, err := db.RawQuery(ctx, `
SELECT actor_did, follower_count, following_count, post_count
FROM mv_actor_social_stats
ORDER BY post_count DESC
LIMIT 5`)
	if err != nil {
		t.Fatalf("mv_actor_social_stats query failed: %v", err)
	}
	if len(resp.Rows) == 0 {
		t.Fatal("mv_actor_social_stats returned no rows")
	}

	resp2, err := db.RawQuery(ctx, `
SELECT actor_did, descendant_subdid_count, repo_record_count
FROM mv_actor_repo_stats
ORDER BY repo_record_count DESC
LIMIT 5`)
	if err != nil {
		t.Fatalf("mv_actor_repo_stats query failed: %v", err)
	}
	if len(resp2.Rows) == 0 {
		t.Fatal("mv_actor_repo_stats returned no rows")
	}
}
