// actors_cc_coverage — Common Crawl DID coverage analysis against RisingWave (kagami).
//
// Queries vertex_domain, vertex_page, edge_hosts_page, edge_links_to, edge_links_to_domain
// tables to produce a coverage report of ingested Common Crawl data.
//
// Usage:
//
//	gftd actors common-crawler-coverage [--format text|json] [--top N] [--topic SLUG] [--min-pages N]
package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"net/http"
	"os"
	"sort"
	"strings"
	"time"

	"github.com/etzhayyim/root/70-tools/gftd/gftd/db"
	"github.com/jackc/pgx/v5/pgxpool"
)

// ── Types ──

// ccCoverageReport is the top-level coverage analysis output.
type ccCoverageReport struct {
	EvaluatedAt    string              `json:"evaluatedAt"`
	Summary        ccCoverageSummary   `json:"summary"`
	TopicBreakdown []ccTopicCoverage   `json:"topicBreakdown"`
	TopDomains     []ccDomainCoverage  `json:"topDomains"`
	LinkGraph      ccLinkGraphStats    `json:"linkGraph"`
	Ingestion      ccIngestionStatus   `json:"ingestion"`
	QuerySource    string              `json:"querySource"`
	Errors         []string            `json:"errors,omitempty"`
}

// ccCoverageSummary holds aggregate counts.
type ccCoverageSummary struct {
	TotalDomains      int64   `json:"totalDomains"`
	TotalPages        int64   `json:"totalPages"`
	DomainsWithPages  int64   `json:"domainsWithPages"`
	DomainsWithTopics int64   `json:"domainsWithTopics"`
	AvgPagesPerDomain float64 `json:"avgPagesPerDomain"`
	TopicCoverage     float64 `json:"topicCoverage"`
}

// ccTopicCoverage is per-topic coverage.
type ccTopicCoverage struct {
	Topic      string `json:"topic"`
	Domains    int64  `json:"domains"`
	Pages      int64  `json:"pages"`
	Percentage float64 `json:"percentage"`
}

// ccDomainCoverage is per-domain detail.
type ccDomainCoverage struct {
	Domain    string `json:"domain"`
	DID       string `json:"did"`
	Slug      string `json:"slug"`
	PageCount int64  `json:"pageCount"`
	Topics    string `json:"topics"`
	Source    string `json:"source"`
}

// ccLinkGraphStats captures edge coverage.
type ccLinkGraphStats struct {
	TotalHostsPageEdges    int64 `json:"totalHostsPageEdges"`
	TotalLinksToEdges      int64 `json:"totalLinksToEdges"`
	TotalLinksToDomainEdges int64 `json:"totalLinksToDomainEdges"`
	TotalEdges             int64 `json:"totalEdges"`
}

// ccIngestionStatus shows pipeline status.
type ccIngestionStatus struct {
	RisingWaveReachable bool   `json:"risingwaveReachable"`
	LatestCrawl        string `json:"latestCrawl,omitempty"`
	ProfileCount       int64  `json:"profileCount"`
	Phase3cChunksDone  int    `json:"phase3cChunksDone,omitempty"`
	Phase3cChunksTotal int    `json:"phase3cChunksTotal,omitempty"`
	Phase3cProgress    string `json:"phase3cProgress,omitempty"`
}

// ── Main ──

// runActorsCCCoverage implements `gftd actors common-crawler-coverage`.
func runActorsCCCoverage(args []string) error {
	fs := flag.NewFlagSet("actors common-crawler-coverage", flag.ContinueOnError)
	format := fs.String("format", "text", "output format: text or json")
	graphURL := fs.String("graph", "https://graph.etzhayyim.com", "graph Worker base URL (RisingWave HTTP)")
	top := fs.Int("top", 30, "number of top domains to show")
	topic := fs.String("topic", "", "filter by topic slug (e.g., government, technology)")
	minPages := fs.Int("min-pages", 0, "only show domains with >= N pages")

	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	_ = graphURL

	report := ccCoverageReport{
		EvaluatedAt: time.Now().UTC().Format(time.RFC3339),
		QuerySource: "risingwave direct (pgx)",
	}

	ctx, cancel := context.WithTimeout(context.Background(), 60*time.Second)
	defer cancel()
	pool, err := db.Pool(ctx)
	if err != nil {
		report.Errors = append(report.Errors, fmt.Sprintf("pool: %v", err))
		report.Ingestion.RisingWaveReachable = false
	} else {
		report.Ingestion.RisingWaveReachable = true
	}

	// 1. Total domain count
	if pool != nil {
		var n int64
		if err := pool.QueryRow(ctx, `SELECT COUNT(*)::bigint FROM vertex_domain`).Scan(&n); err != nil {
			report.Errors = append(report.Errors, fmt.Sprintf("domain count: %v", err))
		} else {
			report.Summary.TotalDomains = n
		}
	}

	// 2. Total page count — ADR-0033: rw_table_stats (vertex_page ≈ 985M rows)
	if pool != nil {
		if n, err := db.CountFromStats(ctx, pool, "vertex_page"); err != nil {
			report.Errors = append(report.Errors, fmt.Sprintf("page count: %v", err))
		} else {
			report.Summary.TotalPages = n
		}
	}

	// 3. Avg pages per domain
	if report.Summary.TotalDomains > 0 {
		report.Summary.AvgPagesPerDomain = float64(report.Summary.TotalPages) / float64(report.Summary.TotalDomains)
	}

	// 4. Domains with topics
	if pool != nil {
		var n int64
		if err := pool.QueryRow(ctx, `SELECT COUNT(*)::bigint FROM vertex_domain WHERE topics IS NOT NULL AND topics <> '' AND topics <> '[]'`).Scan(&n); err != nil {
			report.Errors = append(report.Errors, fmt.Sprintf("topic domain count: %v", err))
		} else {
			report.Summary.DomainsWithTopics = n
		}
	}
	if report.Summary.TotalDomains > 0 {
		report.Summary.TopicCoverage = float64(report.Summary.DomainsWithTopics) / float64(report.Summary.TotalDomains)
	}

	// 5. Domains with pages (page_count > 0) — aggregate via edge_hosts_page
	if pool != nil {
		var n int64
		if err := pool.QueryRow(ctx, `SELECT COUNT(DISTINCT src_vid)::bigint FROM edge_hosts_page`).Scan(&n); err != nil {
			report.Errors = append(report.Errors, fmt.Sprintf("domains with pages: %v", err))
		} else {
			report.Summary.DomainsWithPages = n
		}
	}

	// 6. Topic breakdown — group domains by topics field
	if pool != nil {
		rows, qerr := pool.Query(ctx, `SELECT topics, COUNT(*)::bigint AS cnt FROM vertex_domain WHERE topics IS NOT NULL AND topics <> '' AND topics <> '[]' GROUP BY topics LIMIT 100`)
		if qerr != nil {
			report.Errors = append(report.Errors, fmt.Sprintf("topic breakdown: %v", qerr))
		} else {
			topicMap := map[string]int64{}
			for rows.Next() {
				var topicsRaw string
				var cnt int64
				if err := rows.Scan(&topicsRaw, &cnt); err != nil {
					continue
				}
				for _, t := range parseTopicList(topicsRaw) {
					if *topic != "" && t != *topic {
						continue
					}
					topicMap[t] += cnt
				}
			}
			rows.Close()
			for t, c := range topicMap {
				pct := float64(0)
				if report.Summary.TotalDomains > 0 {
					pct = float64(c) / float64(report.Summary.TotalDomains) * 100
				}
				report.TopicBreakdown = append(report.TopicBreakdown, ccTopicCoverage{
					Topic: t, Domains: c, Percentage: pct,
				})
			}
			sort.Slice(report.TopicBreakdown, func(i, j int) bool {
				return report.TopicBreakdown[i].Domains > report.TopicBreakdown[j].Domains
			})
		}
	}

	// 7. Link graph edge counts
	report.LinkGraph = ccQueryLinkGraph(ctx, pool, &report)

	// 8. Top domains by page_count
	if pool != nil {
		whereClause := ""
		if *minPages > 0 {
			whereClause = fmt.Sprintf(" WHERE page_count >= %d", *minPages)
		}
		queryLimit := *top
		if *topic != "" {
			queryLimit = min(*top*20, 2000)
		}
		topSQL := fmt.Sprintf(`SELECT domain, did, slug, page_count, topics, source FROM vertex_domain%s ORDER BY page_count DESC NULLS LAST LIMIT %d`, whereClause, queryLimit)
		rows, qerr := pool.Query(ctx, topSQL)
		if qerr != nil {
			report.Errors = append(report.Errors, fmt.Sprintf("top domains: %v", qerr))
		} else {
			for rows.Next() {
				var d ccDomainCoverage
				var pc *int64
				var domain, did, slug, topics, source *string
				if err := rows.Scan(&domain, &did, &slug, &pc, &topics, &source); err != nil {
					continue
				}
				if domain != nil {
					d.Domain = *domain
				}
				if did != nil {
					d.DID = *did
				}
				if slug != nil {
					d.Slug = *slug
				}
				if pc != nil {
					d.PageCount = *pc
				}
				if topics != nil {
					d.Topics = *topics
				}
				if source != nil {
					d.Source = *source
				}
				if *topic != "" {
					matched := false
					for _, t := range parseTopicList(d.Topics) {
						if t == *topic {
							matched = true
							break
						}
					}
					if !matched {
						continue
					}
				}
				report.TopDomains = append(report.TopDomains, d)
				if len(report.TopDomains) >= *top {
					break
				}
			}
			rows.Close()
		}
	}

	// 9. Latest crawl info
	if pool != nil {
		var crawl *string
		if err := pool.QueryRow(ctx, `SELECT crawl FROM vertex_page WHERE crawl IS NOT NULL AND crawl <> '' LIMIT 1`).Scan(&crawl); err == nil && crawl != nil {
			report.Ingestion.LatestCrawl = *crawl
		}
	}

	// 10. Profile count (vertex_actor scoped to site.etzhayyim.com)
	if pool != nil {
		var n int64
		if err := pool.QueryRow(ctx, `SELECT COUNT(*)::bigint FROM vertex_actor WHERE repo LIKE 'did:web:site.etzhayyim.com:%'`).Scan(&n); err == nil {
			report.Ingestion.ProfileCount = n
		}
	}

	// 11. Phase 3c ingestion progress (local state file)
	ccLoadPhase3cProgress(&report)

	// ── Output ──
	if *format == "json" {
		data, _ := json.MarshalIndent(report, "", "  ")
		fmt.Println(string(data))
		return nil
	}

	ccPrintTextReport(report, *top)
	return nil
}

// ── Link graph queries (RisingWave direct) ──

func ccQueryLinkGraph(ctx context.Context, pool *pgxpool.Pool, report *ccCoverageReport) ccLinkGraphStats {
	var stats ccLinkGraphStats
	if pool == nil {
		return stats
	}
	// ADR-0033: rw_table_stats (edge_links_to ≈ 4.84B, edge_links_to_domain ≈ 2.33B)
	if n, err := db.CountFromStats(ctx, pool, "edge_hosts_page"); err != nil {
		report.Errors = append(report.Errors, fmt.Sprintf("edge hosts_page: %v", err))
	} else {
		stats.TotalHostsPageEdges = n
	}
	if n, err := db.CountFromStats(ctx, pool, "edge_links_to"); err != nil {
		report.Errors = append(report.Errors, fmt.Sprintf("edge links_to: %v", err))
	} else {
		stats.TotalLinksToEdges = n
	}
	if n, err := db.CountFromStats(ctx, pool, "edge_links_to_domain"); err != nil {
		report.Errors = append(report.Errors, fmt.Sprintf("edge links_to_domain: %v", err))
	} else {
		stats.TotalLinksToDomainEdges = n
	}
	stats.TotalEdges = stats.TotalHostsPageEdges + stats.TotalLinksToEdges + stats.TotalLinksToDomainEdges
	return stats
}

// ── Text output ──

func ccPrintTextReport(report ccCoverageReport, top int) {
	fmt.Println("╔══════════════════════════════════════════════════════════════════════════╗")
	fmt.Println("║         gftd actors common-crawler-coverage — CC DID Analysis           ║")
	fmt.Println("╠══════════════════════════════════════════════════════════════════════════╣")
	fmt.Println()

	// Ingestion status
	reachable := "OFFLINE"
	if report.Ingestion.RisingWaveReachable {
		reachable = "ONLINE"
	}
	fmt.Printf("  RisingWave: %s", reachable)
	if report.Ingestion.LatestCrawl != "" {
		fmt.Printf("  |  Crawl: %s", report.Ingestion.LatestCrawl)
	}
	if report.Ingestion.ProfileCount > 0 {
		fmt.Printf("  |  Profiles: %s", fmtInt64(report.Ingestion.ProfileCount))
	}
	fmt.Println()
	if report.Ingestion.Phase3cProgress != "" {
		fmt.Printf("  Phase 3c:  %s (%d/%d chunks)\n",
			report.Ingestion.Phase3cProgress,
			report.Ingestion.Phase3cChunksDone,
			report.Ingestion.Phase3cChunksTotal)
	}
	fmt.Println()

	// Summary
	fmt.Println("  Summary")
	fmt.Println("  ──────────────────────────────────────────────────────────────────────")
	fmt.Printf("  Domains:          %s\n", fmtInt64(report.Summary.TotalDomains))
	fmt.Printf("  Pages:            %s\n", fmtInt64(report.Summary.TotalPages))
	fmt.Printf("  Domains w/ Pages: %s\n", fmtInt64(report.Summary.DomainsWithPages))
	fmt.Printf("  Avg Pages/Domain: %.1f\n", report.Summary.AvgPagesPerDomain)
	fmt.Printf("  Topic Coverage:   %.1f%% (%s / %s domains classified)\n",
		report.Summary.TopicCoverage*100,
		fmtInt64(report.Summary.DomainsWithTopics),
		fmtInt64(report.Summary.TotalDomains))
	fmt.Println()

	// Topic breakdown
	if len(report.TopicBreakdown) > 0 {
		fmt.Println("  Topic Breakdown")
		fmt.Println("  ──────────────────────────────────────────────────────────────────────")
		fmt.Printf("  %-20s %10s %8s  %s\n", "TOPIC", "DOMAINS", "PCT", "BAR")
		fmt.Println("  ──────────────────────────────────────────────────────────────────────")
		for _, t := range report.TopicBreakdown {
			bar := coverageBar(t.Percentage/100, 20)
			fmt.Printf("  %-20s %10s %7.1f%%  %s\n",
				t.Topic, fmtInt64(t.Domains), t.Percentage, bar)
		}
		fmt.Println()
	}

	// Link graph
	fmt.Println("  Link Graph (Edges)")
	fmt.Println("  ──────────────────────────────────────────────────────────────────────")
	fmt.Printf("  HOSTS_PAGE:       %s\n", fmtInt64(report.LinkGraph.TotalHostsPageEdges))
	fmt.Printf("  LINKS_TO:         %s\n", fmtInt64(report.LinkGraph.TotalLinksToEdges))
	fmt.Printf("  LINKS_TO_DOMAIN:  %s\n", fmtInt64(report.LinkGraph.TotalLinksToDomainEdges))
	fmt.Printf("  Total Edges:      %s\n", fmtInt64(report.LinkGraph.TotalEdges))
	fmt.Println()

	// Top domains
	if len(report.TopDomains) > 0 {
		fmt.Printf("  Top %d Domains (by page count)\n", min(top, len(report.TopDomains)))
		fmt.Println("  ──────────────────────────────────────────────────────────────────────")
		fmt.Printf("  %-4s %-35s %10s  %-20s %s\n", "#", "DOMAIN", "PAGES", "TOPIC", "SOURCE")
		fmt.Println("  ──────────────────────────────────────────────────────────────────────")
		for i, d := range report.TopDomains {
			if i >= top {
				break
			}
			topicStr := d.Topics
			if len(topicStr) > 20 {
				topicStr = topicStr[:17] + "..."
			}
			domainStr := d.Domain
			if len(domainStr) > 35 {
				domainStr = domainStr[:32] + "..."
			}
			fmt.Printf("  %-4d %-35s %10s  %-20s %s\n",
				i+1, domainStr, fmtInt64(d.PageCount), topicStr, d.Source)
		}
		fmt.Println()
	}

	// Errors
	if len(report.Errors) > 0 {
		fmt.Println("  Errors")
		fmt.Println("  ──────────────────────────────────────────────────────────────────────")
		for _, e := range report.Errors {
			fmt.Printf("  ! %s\n", e)
		}
		fmt.Println()
	}

	fmt.Println("╚══════════════════════════════════════════════════════════════════════════╝")
}

// ── Helpers ──

// parseTopicList extracts topic slugs from a JSON array string or comma-separated list.
func parseTopicList(raw string) []string {
	raw = strings.TrimSpace(raw)
	if raw == "" || raw == "[]" {
		return nil
	}
	// Try JSON array
	if strings.HasPrefix(raw, "[") {
		var arr []string
		if err := json.Unmarshal([]byte(raw), &arr); err == nil {
			return arr
		}
	}
	// Comma-separated fallback
	parts := strings.Split(raw, ",")
	var result []string
	for _, p := range parts {
		p = strings.TrimSpace(p)
		p = strings.Trim(p, `"'`)
		if p != "" {
			result = append(result, p)
		}
	}
	return result
}

// anyStr converts an any value to string.
func anyStr(v any) string {
	if v == nil {
		return ""
	}
	return fmt.Sprintf("%v", v)
}

// queryGraphSql is archived. All actors_cc_coverage queries now run
// directly against RisingWave via pgx. Retained as a stub so any lingering
// callers compile; returns an error on every invocation.
func queryGraphSql(_ *http.Client, _ any, _ string) (any, error) {
	return nil, fmt.Errorf("queryGraphSql is archived; use db.RawQuery instead")
}

// ccLoadPhase3cProgress reads local Phase 3c state file for ingestion progress.
func ccLoadPhase3cProgress(report *ccCoverageReport) {
	stateFile := os.Getenv("CC_DATA_DIR")
	if stateFile == "" {
		stateFile = "/Volumes/251220/CC/2603"
	}
	stateFile += "/scripts/.phase3c_state.json"

	data, err := os.ReadFile(stateFile)
	if err != nil {
		return
	}
	var state struct {
		ChunksDone []string       `json:"chunks_done"`
		Totals     map[string]int `json:"totals"`
	}
	if err := json.Unmarshal(data, &state); err != nil {
		return
	}
	report.Ingestion.Phase3cChunksDone = len(state.ChunksDone)
	report.Ingestion.Phase3cChunksTotal = 8451 // 84510 files / 10 per chunk
	if report.Ingestion.Phase3cChunksTotal > 0 {
		pct := float64(len(state.ChunksDone)) / float64(report.Ingestion.Phase3cChunksTotal) * 100
		report.Ingestion.Phase3cProgress = fmt.Sprintf("%.1f%%", pct)
	}
}

// fmtInt64 formats an int64 with thousands separators.
func fmtInt64(n int64) string {
	if n == 0 {
		return "0"
	}
	sign := ""
	if n < 0 {
		sign = "-"
		n = -n
	}
	s := fmt.Sprintf("%d", n)
	// Insert commas from right
	var result strings.Builder
	for i, c := range s {
		if i > 0 && (len(s)-i)%3 == 0 {
			result.WriteByte(',')
		}
		result.WriteRune(c)
	}
	return sign + result.String()
}
