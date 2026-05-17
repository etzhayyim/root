package main

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

type oilCoverageRow struct {
	TargetKey    string  `json:"targetKey"`
	CountryCode  string  `json:"countryCode"`
	Segment      string  `json:"segment"`
	ActorDID     string  `json:"actorDid"`
	App          string  `json:"app"`
	TargetCount  int     `json:"targetCount"`
	ActualCount  int     `json:"actualCount"`
	CoverageGap  int     `json:"coverageGap"`
	Priority     int     `json:"priority"`
	CoverageRate float64 `json:"coverageRate"`
}

type oilCoverageSummary struct {
	EvaluatedAt  string                   `json:"evaluatedAt"`
	Segment      string                   `json:"segment,omitempty"`
	CountryCode  string                   `json:"countryCode,omitempty"`
	TotalTargets int                      `json:"totalTargets"`
	AvgCoverage  float64                  `json:"avgCoverage"`
	TotalGap     int                      `json:"totalGap"`
	SegmentStats []oilCoverageSegmentStat `json:"segmentStats"`
	Rows         []oilCoverageRow         `json:"rows"`
	Gaps         []oilCoverageRow         `json:"gaps"`
}

type oilCoverageSegmentStat struct {
	Segment        string  `json:"segment"`
	TargetTotal    int     `json:"targetTotal"`
	ActualTotal    int     `json:"actualTotal"`
	GapTotal       int     `json:"gapTotal"`
	AvgCoverage    float64 `json:"avgCoverage"`
	CountryTargets int     `json:"countryTargets"`
}

func runCoverageOil(args []string) error {
	fs := flag.NewFlagSet("coverage oil", flag.ContinueOnError)
	jsonOut := fs.Bool("json", false, "output as JSON")
	segment := fs.String("segment", "", "filter by segment")
	country := fs.String("country", "", "filter by country code")
	limit := fs.Int("limit", 20, "max rows for text output and gaps view")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Second)
	defer cancel()

	rows, err := queryOilCoverageRows(ctx, strings.ToLower(strings.TrimSpace(*segment)), strings.ToUpper(strings.TrimSpace(*country)), *limit)
	if err != nil {
		return err
	}
	gaps, err := queryOilCoverageGaps(ctx, strings.ToLower(strings.TrimSpace(*segment)), strings.ToUpper(strings.TrimSpace(*country)), *limit)
	if err != nil {
		return err
	}
	segmentStats, err := queryOilCoverageSegmentStats(ctx, strings.ToLower(strings.TrimSpace(*segment)), strings.ToUpper(strings.TrimSpace(*country)))
	if err != nil {
		return err
	}
	summary := buildOilCoverageSummary(rows, gaps, segmentStats, *segment, *country)

	if *jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(summary)
	}

	printOilCoverageText(summary, *limit)
	return nil
}

func queryOilCoverageRows(ctx context.Context, segment, country string, limit int) ([]oilCoverageRow, error) {
	if limit <= 0 {
		limit = 20
	}
	res, err := db.RawQuery(ctx, `
SELECT target_key, country_code, segment, actor_did, app, target_count, actual_count, coverage_gap, priority, coverage_rate
FROM mv_oil_coverage_live
WHERE ($1 = '' OR segment = $1)
  AND ($2 = '' OR country_code = $2)
ORDER BY priority ASC, coverage_gap DESC, country_code ASC, segment ASC
LIMIT $3
`, segment, country, limit)
	if err != nil {
		return nil, err
	}
	return decodeOilCoverageRows(res.Rows), nil
}

func queryOilCoverageGaps(ctx context.Context, segment, country string, limit int) ([]oilCoverageRow, error) {
	if limit <= 0 {
		limit = 20
	}
	res, err := db.RawQuery(ctx, `
SELECT target_key, country_code, segment, actor_did, app, target_count, actual_count, coverage_gap, priority, coverage_rate
FROM mv_oil_coverage_live
WHERE coverage_gap > 0
  AND ($1 = '' OR segment = $1)
  AND ($2 = '' OR country_code = $2)
ORDER BY priority ASC, coverage_gap DESC, coverage_rate ASC, country_code ASC, segment ASC
LIMIT $3
`, segment, country, limit)
	if err != nil {
		return nil, err
	}
	return decodeOilCoverageRows(res.Rows), nil
}

func queryOilCoverageSegmentStats(ctx context.Context, segment, country string) ([]oilCoverageSegmentStat, error) {
	res, err := db.RawQuery(ctx, `
SELECT
  segment,
  SUM(target_count) AS target_total,
  SUM(actual_count) AS actual_total,
  SUM(coverage_gap) AS gap_total,
  AVG(coverage_rate) AS avg_coverage,
  COUNT(*) AS country_targets
FROM mv_oil_coverage_live
WHERE ($1 = '' OR segment = $1)
  AND ($2 = '' OR country_code = $2)
GROUP BY segment
ORDER BY segment ASC
`, segment, country)
	if err != nil {
		return nil, err
	}

	out := make([]oilCoverageSegmentStat, 0, len(res.Rows))
	for _, row := range res.Rows {
		out = append(out, oilCoverageSegmentStat{
			Segment:        strings.TrimSpace(fmt.Sprint(row["segment"])),
			TargetTotal:    parseIntLike(row["target_total"]),
			ActualTotal:    parseIntLike(row["actual_total"]),
			GapTotal:       parseIntLike(row["gap_total"]),
			AvgCoverage:    parseFloatLike(row["avg_coverage"]),
			CountryTargets: parseIntLike(row["country_targets"]),
		})
	}
	return out, nil
}

func decodeOilCoverageRows(rows []map[string]interface{}) []oilCoverageRow {
	out := make([]oilCoverageRow, 0, len(rows))
	for _, row := range rows {
		out = append(out, oilCoverageRow{
			TargetKey:    strings.TrimSpace(fmt.Sprint(row["target_key"])),
			CountryCode:  strings.TrimSpace(fmt.Sprint(row["country_code"])),
			Segment:      strings.TrimSpace(fmt.Sprint(row["segment"])),
			ActorDID:     strings.TrimSpace(fmt.Sprint(row["actor_did"])),
			App:          strings.TrimSpace(fmt.Sprint(row["app"])),
			TargetCount:  parseIntLike(row["target_count"]),
			ActualCount:  parseIntLike(row["actual_count"]),
			CoverageGap:  parseIntLike(row["coverage_gap"]),
			Priority:     parseIntLike(row["priority"]),
			CoverageRate: parseFloatLike(row["coverage_rate"]),
		})
	}
	return out
}

func buildOilCoverageSummary(rows, gaps []oilCoverageRow, segmentStats []oilCoverageSegmentStat, segment, country string) oilCoverageSummary {
	summary := oilCoverageSummary{
		EvaluatedAt:  time.Now().UTC().Format(time.RFC3339),
		Segment:      segment,
		CountryCode:  strings.ToUpper(country),
		SegmentStats: segmentStats,
		Rows:         rows,
		Gaps:         gaps,
	}
	if len(rows) == 0 {
		return summary
	}
	var sumCoverage float64
	for _, row := range rows {
		sumCoverage += row.CoverageRate
		summary.TotalGap += row.CoverageGap
	}
	summary.TotalTargets = len(rows)
	summary.AvgCoverage = sumCoverage / float64(len(rows))
	return summary
}

func printOilCoverageText(summary oilCoverageSummary, limit int) {
	fmt.Printf("oil_coverage:\n")
	fmt.Printf("  evaluated_at: %s\n", summary.EvaluatedAt)
	if summary.Segment != "" {
		fmt.Printf("  segment: %s\n", summary.Segment)
	}
	if summary.CountryCode != "" {
		fmt.Printf("  country_code: %s\n", summary.CountryCode)
	}
	fmt.Printf("  total_targets: %d\n", summary.TotalTargets)
	fmt.Printf("  avg_coverage: %.1f%%\n", summary.AvgCoverage*100)
	fmt.Printf("  total_gap: %d\n", summary.TotalGap)

	if len(summary.SegmentStats) > 0 {
		fmt.Printf("\nsegment_summary:\n")
		w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
		fmt.Fprintln(w, "SEGMENT\tCOUNTRIES\tTARGET\tACTUAL\tGAP\tAVG_COVERAGE")
		for _, row := range summary.SegmentStats {
			fmt.Fprintf(w, "%s\t%d\t%d\t%d\t%d\t%.1f%%\n",
				row.Segment,
				row.CountryTargets,
				row.TargetTotal,
				row.ActualTotal,
				row.GapTotal,
				row.AvgCoverage*100,
			)
		}
		_ = w.Flush()
	}

	if len(summary.Rows) > 0 {
		fmt.Printf("\ncoverage_live:\n")
		w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
		fmt.Fprintln(w, "COUNTRY\tSEGMENT\tACTOR\tTARGET\tACTUAL\tGAP\tCOVERAGE")
		for _, row := range summary.Rows {
			fmt.Fprintf(w, "%s\t%s\t%s\t%d\t%d\t%d\t%.1f%%\n",
				row.CountryCode,
				row.Segment,
				row.ActorDID,
				row.TargetCount,
				row.ActualCount,
				row.CoverageGap,
				row.CoverageRate*100,
			)
		}
		_ = w.Flush()
	}

	if len(summary.Gaps) > 0 {
		if limit > 0 && len(summary.Gaps) > limit {
			summary.Gaps = summary.Gaps[:limit]
		}
		fmt.Printf("\npriority_gaps:\n")
		w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
		fmt.Fprintln(w, "COUNTRY\tSEGMENT\tACTOR\tTARGET\tACTUAL\tGAP\tCOVERAGE")
		for _, row := range summary.Gaps {
			fmt.Fprintf(w, "%s\t%s\t%s\t%d\t%d\t%d\t%.1f%%\n",
				row.CountryCode,
				row.Segment,
				row.ActorDID,
				row.TargetCount,
				row.ActualCount,
				row.CoverageGap,
				row.CoverageRate*100,
			)
		}
		_ = w.Flush()
	}
}
