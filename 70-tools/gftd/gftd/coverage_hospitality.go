package main

// `gftd hospitality coverage` — reads mv_hospitality_actor_coverage +
// mv_hospitality_ownership_depth from RisingWave and prints a coverage report.
// ADR-0028 Phase 1. Uses Hyperdrive direct via db.RawQuery() per
// 70-tools/gftd/CLAUDE.md read-path convention.

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"strings"
	"text/tabwriter"
	"time"

	"github.com/etzhayyim/root/70-tools/gftd/gftd/db"
)

type hospitalityCoverageRow struct {
	Kind     string `json:"kind"`
	ActorCnt int    `json:"actorCount"`
}

type hospitalityDepthRow struct {
	ParentDid      string `json:"parentDid"`
	DirectChildren int    `json:"directChildren"`
}

type hospitalityTierRow struct {
	Tier     string `json:"tier"`
	Kind     string `json:"kind"`
	ActorCnt int    `json:"actorCount"`
}

type hospitalityCoverageReport struct {
	EvaluatedAt string                   `json:"evaluatedAt"`
	Total       int                      `json:"total"`
	ByKind      []hospitalityCoverageRow `json:"byKind"`
	ByTier      []hospitalityTierRow     `json:"byTier"`
	TopParents  []hospitalityDepthRow    `json:"topParents"`
}

func runHospitalityCoverage(ctx context.Context, args []string) error {
	fs := flag.NewFlagSet("hospitality coverage", flag.ContinueOnError)
	region := fs.String("region", "", "Reserved for future region filter (MV currently scopes by kind only)")
	format := fs.String("format", "table", "Output: table|json")
	limit := fs.Int("top-parents", 20, "Top-N parents by direct_children")
	if err := fs.Parse(args); err != nil {
		return err
	}
	_ = region

	byKind, err := queryHospitalityCoverageKinds(ctx)
	if err != nil {
		return err
	}
	byTier, err := queryHospitalityTierCoverage(ctx)
	if err != nil {
		return err
	}
	top, err := queryHospitalityOwnershipDepth(ctx, *limit)
	if err != nil {
		return err
	}

	total := 0
	for _, r := range byKind {
		total += r.ActorCnt
	}

	report := hospitalityCoverageReport{
		EvaluatedAt: time.Now().UTC().Format(time.RFC3339),
		Total:       total,
		ByKind:      byKind,
		ByTier:      byTier,
		TopParents:  top,
	}

	if *format == "json" {
		b, _ := json.MarshalIndent(report, "", "  ")
		fmt.Println(string(b))
		return nil
	}

	w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
	fmt.Fprintln(w, "kind\tactor_cnt")
	for _, r := range byKind {
		fmt.Fprintf(w, "%s\t%d\n", r.Kind, r.ActorCnt)
	}
	fmt.Fprintln(w, strings.Repeat("-", 32))
	fmt.Fprintf(w, "TOTAL\t%d\n", total)
	w.Flush()

	fmt.Println()
	wt := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
	fmt.Fprintln(wt, "tier\tkind\tactor_cnt")
	for _, r := range byTier {
		fmt.Fprintf(wt, "%s\t%s\t%d\n", r.Tier, r.Kind, r.ActorCnt)
	}
	wt.Flush()

	fmt.Println()
	w2 := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
	fmt.Fprintln(w2, "parent\tdirect_children")
	for _, r := range top {
		fmt.Fprintf(w2, "%s\t%d\n", r.ParentDid, r.DirectChildren)
	}
	w2.Flush()
	return nil
}

func queryHospitalityCoverageKinds(ctx context.Context) ([]hospitalityCoverageRow, error) {
	res, err := db.RawQuery(ctx, `
SELECT kind, actor_cnt
FROM mv_hospitality_actor_coverage
ORDER BY actor_cnt DESC
`)
	if err != nil {
		return nil, fmt.Errorf("mv_hospitality_actor_coverage: %w", err)
	}
	out := make([]hospitalityCoverageRow, 0, len(res.Rows))
	for _, row := range res.Rows {
		out = append(out, hospitalityCoverageRow{
			Kind:     strings.TrimSpace(fmt.Sprint(row["kind"])),
			ActorCnt: parseIntLike(row["actor_cnt"]),
		})
	}
	return out, nil
}

func queryHospitalityTierCoverage(ctx context.Context) ([]hospitalityTierRow, error) {
	res, err := db.RawQuery(ctx, `
SELECT tier, kind, actor_cnt
FROM mv_hospitality_tier_coverage
ORDER BY tier ASC, actor_cnt DESC
`)
	if err != nil {
		return nil, fmt.Errorf("mv_hospitality_tier_coverage: %w", err)
	}
	out := make([]hospitalityTierRow, 0, len(res.Rows))
	for _, row := range res.Rows {
		out = append(out, hospitalityTierRow{
			Tier:     strings.TrimSpace(fmt.Sprint(row["tier"])),
			Kind:     strings.TrimSpace(fmt.Sprint(row["kind"])),
			ActorCnt: parseIntLike(row["actor_cnt"]),
		})
	}
	return out, nil
}

func queryHospitalityOwnershipDepth(ctx context.Context, limit int) ([]hospitalityDepthRow, error) {
	if limit <= 0 {
		limit = 20
	}
	res, err := db.RawQuery(ctx, `
SELECT parent_did, direct_children
FROM mv_hospitality_ownership_depth
ORDER BY direct_children DESC
LIMIT $1
`, limit)
	if err != nil {
		return nil, fmt.Errorf("mv_hospitality_ownership_depth: %w", err)
	}
	out := make([]hospitalityDepthRow, 0, len(res.Rows))
	for _, row := range res.Rows {
		out = append(out, hospitalityDepthRow{
			ParentDid:      strings.TrimSpace(fmt.Sprint(row["parent_did"])),
			DirectChildren: parseIntLike(row["direct_children"]),
		})
	}
	return out, nil
}
