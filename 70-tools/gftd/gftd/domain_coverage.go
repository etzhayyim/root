package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"math"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
	"time"
)

type coverageDomain struct {
	Name            string  `json:"name"`
	Kind            string  `json:"kind"`
	App             string  `json:"app"`
	Nanoid          string  `json:"nanoid"`
	AuthoritySeed   int     `json:"authoritySeed"`
	AuthorityTarget int     `json:"authorityTarget"`
	RuleSeed        int     `json:"ruleSeed"`
	RuleTarget      int     `json:"ruleTarget"`
	ScopeSeed       int     `json:"scopeSeed"`
	ScopeTarget     int     `json:"scopeTarget"`
	CoverageRate    float64 `json:"coverageRate"`
	Status          string  `json:"status"`
	KyumeiFile      string  `json:"kyumeiFile,omitempty"`
	KyumeiGrade     string  `json:"kyumeiGrade,omitempty"`
	KyumeiScore     int     `json:"kyumeiScore,omitempty"`
	KyumeiCritical  int     `json:"kyumeiCritical,omitempty"`
	KyumeiHigh      int     `json:"kyumeiHigh,omitempty"`
	KyumeiMedium    int     `json:"kyumeiMedium,omitempty"`
}

type coverageReport struct {
	EvaluatedAt      string           `json:"evaluatedAt"`
	Domains          []coverageDomain `json:"domains"`
	TotalNodes       int              `json:"totalNodes"`
	TotalTargetNodes int              `json:"totalTargetNodes"`
	PlatformRate     float64          `json:"platformRate"`
}

// Authority-chain domain definitions (12 kinds)
// Seed values reflect registered sub-DIDs, extracted rules, and defined scope areas.
var authorityDomains = []coverageDomain{
	{Name: "sovereign", Kind: "sovereign", App: "states.etzhayyim.com", Nanoid: "(multi)", AuthoritySeed: 195, AuthorityTarget: 195, RuleSeed: 390, RuleTarget: 195000, ScopeSeed: 195, ScopeTarget: 195, Status: "deployed (300+ components, 195 states full coverage)"},
	{Name: "treaty", Kind: "treaty", App: "treaty.etzhayyim.com", Nanoid: "tr3aty01", AuthoritySeed: 48, AuthorityTarget: 500, RuleSeed: 85, RuleTarget: 5000, ScopeSeed: 18, ScopeTarget: 50, Status: "deployed"},
	{Name: "religious", Kind: "religious", App: "religious.etzhayyim.com", Nanoid: "r3lgus01", AuthoritySeed: 25, AuthorityTarget: 30, RuleSeed: 60, RuleTarget: 3000, ScopeSeed: 10, ScopeTarget: 10, Status: "deployed"},
	{Name: "private", Kind: "private", App: "(per-company)", Nanoid: "(dynamic)", AuthoritySeed: 0, AuthorityTarget: 0, RuleSeed: 0, RuleTarget: 0, ScopeSeed: 0, ScopeTarget: 0, Status: "dynamic (per-company ToS)"},
	{Name: "community", Kind: "community", App: "communities.etzhayyim.com", Nanoid: "2tqvrutp", AuthoritySeed: 69, AuthorityTarget: 100, RuleSeed: 35, RuleTarget: 1000, ScopeSeed: 8, ScopeTarget: 20, Status: "deployed (69 type DIDs)"},
	{Name: "customary", Kind: "customary", App: "customary.etzhayyim.com", Nanoid: "cstmry01", AuthoritySeed: 28, AuthorityTarget: 100, RuleSeed: 40, RuleTarget: 500, ScopeSeed: 12, ScopeTarget: 50, Status: "deployed"},
	{Name: "family", Kind: "family", App: "tradition.etzhayyim.com", Nanoid: "trdtn001", AuthoritySeed: 25, AuthorityTarget: 500, RuleSeed: 30, RuleTarget: 2000, ScopeSeed: 12, ScopeTarget: 100, Status: "deployed"},
	{Name: "cultural", Kind: "cultural", App: "tradition.etzhayyim.com", Nanoid: "trdtn001", AuthoritySeed: 30, AuthorityTarget: 200, RuleSeed: 24, RuleTarget: 1000, ScopeSeed: 12, ScopeTarget: 50, Status: "deployed"},
	{Name: "professional", Kind: "professional", App: "ethics.etzhayyim.com", Nanoid: "eth1cs01", AuthoritySeed: 24, AuthorityTarget: 100, RuleSeed: 48, RuleTarget: 500, ScopeSeed: 12, ScopeTarget: 30, Status: "deployed"},
	{Name: "academic", Kind: "academic", App: "ethics.etzhayyim.com", Nanoid: "eth1cs01", AuthoritySeed: 10, AuthorityTarget: 50, RuleSeed: 18, RuleTarget: 200, ScopeSeed: 5, ScopeTarget: 10, Status: "deployed"},
	{Name: "industry", Kind: "industry", App: "industry-standard.etzhayyim.com", Nanoid: "indstd01", AuthoritySeed: 42, AuthorityTarget: 200, RuleSeed: 60, RuleTarget: 3000, ScopeSeed: 15, ScopeTarget: 50, Status: "deployed"},
	{Name: "blockchain", Kind: "blockchain", App: "blockchain.etzhayyim.com", Nanoid: "blkchn01", AuthoritySeed: 30, AuthorityTarget: 100, RuleSeed: 65, RuleTarget: 5000, ScopeSeed: 20, ScopeTarget: 200, Status: "deployed"},
}

// collectWITDomains scans projects for domain WIT packages and returns coverage info
func collectWITDomains(rootDir string) []witDomainCoverage {
	var results []witDomainCoverage
	witDepsDir := filepath.Join(rootDir, "packages", "contract", "wit", "deps")
	entries, err := os.ReadDir(witDepsDir)
	if err != nil {
		return results
	}
	for _, e := range entries {
		if !e.IsDir() {
			continue
		}
		pkgWit := filepath.Join(witDepsDir, e.Name(), "package.wit")
		data, err := os.ReadFile(pkgWit)
		if err != nil {
			continue
		}
		content := string(data)
		interfaces := strings.Count(content, "interface ")
		funcs := strings.Count(content, ": func(")
		records := strings.Count(content, "record ")
		enums := strings.Count(content, "enum ")
		results = append(results, witDomainCoverage{
			Package:    e.Name(),
			Interfaces: interfaces,
			Functions:  funcs,
			Records:    records,
			Enums:      enums,
		})
	}
	return results
}

type witDomainCoverage struct {
	Package    string `json:"package"`
	Interfaces int    `json:"interfaces"`
	Functions  int    `json:"functions"`
	Records    int    `json:"records"`
	Enums      int    `json:"enums"`
}

type fullCoverageReport struct {
	AuthorityModel coverageModel       `json:"authorityModel"`
	LiveReadModel  coverageModel       `json:"liveReadModel"`
	AuthorityChain coverageReport      `json:"authorityChain"`
	WITDomains     []witDomainCoverage `json:"witDomains"`
	WITSummary     witSummary          `json:"witSummary"`
	Reconciliation []coverageDiff      `json:"reconciliation,omitempty"`
	ReconcileError string              `json:"reconcileError,omitempty"`
}

type coverageModel struct {
	Name      string `json:"name"`
	Mode      string `json:"mode"`
	Ownership string `json:"ownership"`
}

type witSummary struct {
	TotalPackages   int `json:"totalPackages"`
	TotalInterfaces int `json:"totalInterfaces"`
	TotalFunctions  int `json:"totalFunctions"`
	TotalRecords    int `json:"totalRecords"`
	TotalEnums      int `json:"totalEnums"`
}

type coverageDiff struct {
	Kind            string  `json:"kind"`
	AuthorityRate   float64 `json:"authorityRate"`
	LiveCoverageDid float64 `json:"liveCoverageDid"`
	LiveCoverageRec float64 `json:"liveCoverageRecord"`
	DeltaDid        float64 `json:"deltaDid"`
	DeltaRecord     float64 `json:"deltaRecord"`
	LiveCountSource string  `json:"liveCountSource,omitempty"`
}

type kyumeiDomainReport struct {
	file     string
	grade    string
	score    int
	critical int
	high     int
	medium   int
}

type kyumeiDomainFile struct {
	ReadinessScore float64 `json:"readiness_score"`
	ReadinessGrade string  `json:"readiness_grade"`
	KnowledgeGaps  []struct {
		Severity string `json:"severity"`
	} `json:"knowledge_gaps"`
}

func collectKyumeiReports(rootDir string) map[string]kyumeiDomainReport {
	results := map[string]kyumeiDomainReport{}
	pattern := filepath.Join(rootDir, "reports", "kyumei-domain-*-full-*.json")
	files, err := filepath.Glob(pattern)
	if err != nil {
		return results
	}
	sort.Strings(files)
	latestByKind := map[string]string{}
	for _, f := range files {
		base := filepath.Base(f)
		kind := strings.TrimPrefix(base, "kyumei-domain-")
		if idx := strings.Index(kind, "-full-"); idx > 0 {
			kind = kind[:idx]
		} else {
			continue
		}
		latestByKind[kind] = f
	}

	for kind, file := range latestByKind {
		data, err := os.ReadFile(file)
		if err != nil {
			continue
		}
		var parsed kyumeiDomainFile
		if err := json.Unmarshal(data, &parsed); err != nil {
			continue
		}
		summary := kyumeiDomainReport{
			file:  filepath.Base(file),
			grade: parsed.ReadinessGrade,
			score: int(math.Round(parsed.ReadinessScore)),
		}
		for _, gap := range parsed.KnowledgeGaps {
			switch strings.ToLower(strings.TrimSpace(gap.Severity)) {
			case "critical":
				summary.critical++
			case "high":
				summary.high++
			case "medium":
				summary.medium++
			}
		}
		results[kind] = summary
	}
	return results
}

func runDomainCoverage(args []string) error {
	fs := flag.NewFlagSet("domain-coverage", flag.ContinueOnError)
	format := fs.String("format", "text", "output format: text or json")
	rootDir := fs.String("root", ".", "repo root directory")
	pdsURL := fs.String("pds", defaultPDSURL, "PDS base URL used for live reconciliation snapshot")
	noReconcile := fs.Bool("no-reconcile", false, "skip live world-coverage reconciliation snapshot")
	strict := fs.Bool("strict", false, "fail if live reconciliation cannot be loaded")

	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	// Build authority-chain coverage
	report := coverageReport{
		EvaluatedAt: time.Now().UTC().Format(time.RFC3339),
	}
	kyumeiByKind := collectKyumeiReports(*rootDir)
	totalSeed := 0
	totalTarget := 0
	for i := range authorityDomains {
		d := &authorityDomains[i]
		seed := d.AuthoritySeed + d.RuleSeed + d.ScopeSeed
		target := d.AuthorityTarget + d.RuleTarget + d.ScopeTarget
		if target > 0 {
			d.CoverageRate = float64(seed) / float64(target)
		}
		if k, ok := kyumeiByKind[d.Kind]; ok {
			d.KyumeiFile = k.file
			d.KyumeiGrade = k.grade
			d.KyumeiScore = k.score
			d.KyumeiCritical = k.critical
			d.KyumeiHigh = k.high
			d.KyumeiMedium = k.medium
		}
		totalSeed += seed
		totalTarget += target
		report.Domains = append(report.Domains, *d)
	}
	report.TotalNodes = totalSeed
	report.TotalTargetNodes = totalTarget
	if totalTarget > 0 {
		report.PlatformRate = float64(totalSeed) / float64(totalTarget)
	}

	// Collect WIT domain info
	witDomains := collectWITDomains(*rootDir)
	var summary witSummary
	summary.TotalPackages = len(witDomains)
	for _, w := range witDomains {
		summary.TotalInterfaces += w.Interfaces
		summary.TotalFunctions += w.Functions
		summary.TotalRecords += w.Records
		summary.TotalEnums += w.Enums
	}

	full := fullCoverageReport{
		AuthorityModel: coverageModel{
			Name:      "authority-chain static targets",
			Mode:      "static",
			Ownership: "domain-ingest/control-plane",
		},
		LiveReadModel: coverageModel{
			Name:      "mv_domain_coverage_live",
			Mode:      "read-only live MV",
			Ownership: "coverage/observability",
		},
		AuthorityChain: report,
		WITDomains:     witDomains,
		WITSummary:     summary,
	}
	if !*noReconcile {
		kcfg := kagamiConfig{Endpoint: *pdsURL}
		if rec, err := collectCoverageReconciliationKagami(kcfg, report.Domains); err == nil {
			full.Reconciliation = rec
		} else {
			if *strict {
				return fmt.Errorf("live reconciliation required (--strict): %w", err)
			}
			full.ReconcileError = err.Error()
		}
	}

	if *format == "json" {
		data, _ := json.MarshalIndent(full, "", "  ")
		fmt.Println(string(data))
		return nil
	}

	// Text output
	fmt.Println("╔══════════════════════════════════════════════════════════════════════════╗")
	fmt.Println("║               gftd domain-coverage — Authority-Chain Compliance         ║")
	fmt.Println("╠══════════════════════════════════════════════════════════════════════════╣")
	fmt.Println()

	fmt.Println("  Authority-Chain Graph Coverage")
	fmt.Println("  ──────────────────────────────────────────────────────────────────────")
	fmt.Printf("  %-14s %-28s %6s %6s %6s %8s  %s\n", "KIND", "APP", "AUTH", "RULES", "SCOPE", "RATE", "STATUS")
	fmt.Println("  ──────────────────────────────────────────────────────────────────────")
	for _, d := range report.Domains {
		bar := coverageBar(d.CoverageRate, 10)
		rateStr := "N/A"
		if d.AuthorityTarget+d.RuleTarget+d.ScopeTarget > 0 {
			rateStr = fmt.Sprintf("%5.1f%%", d.CoverageRate*100)
		}
		fmt.Printf("  %-14s %-28s %3d/%-3d %3d/%-5d %2d/%-3d %8s %s %s\n",
			d.Kind, d.App,
			d.AuthoritySeed, d.AuthorityTarget,
			d.RuleSeed, d.RuleTarget,
			d.ScopeSeed, d.ScopeTarget,
			rateStr, bar, d.Status)
	}
	fmt.Println("  ──────────────────────────────────────────────────────────────────────")
	fmt.Printf("  TOTAL: %d / %d nodes  |  Platform Rate: %.2f%%\n", report.TotalNodes, report.TotalTargetNodes, report.PlatformRate*100)
	fmt.Println()

	if len(full.Reconciliation) > 0 {
		fmt.Printf("  Reconciliation (authority-chain vs coverage --strict @ %s)\n", *pdsURL)
		fmt.Println("  ──────────────────────────────────────────────────────────────────────")
		fmt.Printf("  %-14s %8s %8s %8s %8s %8s\n", "KIND", "AUTH", "LIVE-DID", "LIVE-REC", "ΔDID", "ΔREC")
		fmt.Println("  ──────────────────────────────────────────────────────────────────────")
		for _, r := range full.Reconciliation {
			fmt.Printf("  %-14s %7.1f%% %7.1f%% %7.1f%% %7.1f%% %7.1f%%\n",
				r.Kind, r.AuthorityRate*100, r.LiveCoverageDid*100, r.LiveCoverageRec*100, r.DeltaDid*100, r.DeltaRecord*100)
		}
		fmt.Println("  ──────────────────────────────────────────────────────────────────────")
		fmt.Println()
	} else if full.ReconcileError != "" {
		fmt.Printf("  Reconciliation skipped: %s\n\n", full.ReconcileError)
	}

	fmt.Println("  Kyumei Readiness Hints (latest full reports)")
	fmt.Println("  ──────────────────────────────────────────────────────────────────────")
	fmt.Printf("  %-14s %5s %5s %4s %4s %4s  %s\n", "KIND", "GRADE", "SCORE", "CRI", "HIGH", "MED", "REPORT")
	fmt.Println("  ──────────────────────────────────────────────────────────────────────")
	for _, d := range report.Domains {
		if d.KyumeiFile == "" {
			continue
		}
		fmt.Printf("  %-14s %5s %5d %4d %4d %4d  %s\n",
			d.Kind, d.KyumeiGrade, d.KyumeiScore, d.KyumeiCritical, d.KyumeiHigh, d.KyumeiMedium, d.KyumeiFile)
	}
	fmt.Println("  ──────────────────────────────────────────────────────────────────────")

	next := make([]coverageDomain, 0, len(report.Domains))
	for _, d := range report.Domains {
		if d.KyumeiFile != "" {
			next = append(next, d)
		}
	}
	sort.Slice(next, func(i, j int) bool {
		if next[i].KyumeiCritical != next[j].KyumeiCritical {
			return next[i].KyumeiCritical > next[j].KyumeiCritical
		}
		if next[i].KyumeiHigh != next[j].KyumeiHigh {
			return next[i].KyumeiHigh > next[j].KyumeiHigh
		}
		return next[i].KyumeiScore < next[j].KyumeiScore
	})
	if len(next) > 0 {
		fmt.Printf("  NEXT STEP: %s (critical=%d, high=%d, score=%d)\n",
			next[0].Kind, next[0].KyumeiCritical, next[0].KyumeiHigh, next[0].KyumeiScore)
	}
	fmt.Println()

	fmt.Println("  WIT Domain Packages (magatama:*@1.0.0)")
	fmt.Println("  ──────────────────────────────────────────────────────────────────────")
	fmt.Printf("  %-30s %5s %5s %5s %5s\n", "PACKAGE", "IFACE", "FUNCS", "RECS", "ENUMS")
	fmt.Println("  ──────────────────────────────────────────────────────────────────────")
	for _, w := range witDomains {
		fmt.Printf("  %-30s %5d %5d %5d %5d\n", w.Package, w.Interfaces, w.Functions, w.Records, w.Enums)
	}
	fmt.Println("  ──────────────────────────────────────────────────────────────────────")
	fmt.Printf("  TOTAL: %d packages | %d interfaces | %d functions | %d records | %d enums\n",
		summary.TotalPackages, summary.TotalInterfaces, summary.TotalFunctions, summary.TotalRecords, summary.TotalEnums)

	fmt.Println()
	fmt.Println("╚══════════════════════════════════════════════════════════════════════════╝")

	return nil
}

func coverageBar(rate float64, width int) string {
	filled := int(rate * float64(width))
	if filled > width {
		filled = width
	}
	return "[" + strings.Repeat("█", filled) + strings.Repeat("░", width-filled) + "]"
}

// collectCoverageReconciliationKagami queries RisingWave (direct pgx) for live DID/record counts
// per authority-chain domain kind. The `kagamiConfig` arg is retained for call-site compatibility
// but is unused — all reads go through the shared pgx pool in the db package.
func collectCoverageReconciliationKagami(cfg kagamiConfig, domains []coverageDomain) ([]coverageDiff, error) {
	_ = cfg
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	kinds := make([]string, 0, len(domains))
	for _, d := range domains {
		if strings.TrimSpace(d.Kind) == "" || d.Kind == "private" {
			continue
		}
		kinds = append(kinds, d.Kind)
	}
	if len(kinds) == 0 {
		return nil, nil
	}

	placeholders := make([]string, 0, len(kinds))
	args := make([]any, 0, len(kinds))
	for i, kind := range kinds {
		placeholders = append(placeholders, fmt.Sprintf("$%d", i+1))
		args = append(args, kind)
	}

	stmt := fmt.Sprintf(`
SELECT
  kind,
  authority_rate,
  live_coverage_did,
  live_coverage_record,
  delta_did,
  delta_record
FROM mv_domain_coverage_live
WHERE kind IN (%s)
ORDER BY kind`, strings.Join(placeholders, ", "))
	resp, err := rawQuery(ctx, stmt, args...)
	if err != nil {
		return nil, fmt.Errorf("mv_domain_coverage_live: %w", err)
	}

	recon := make([]coverageDiff, 0, len(resp.Rows))
	for _, row := range resp.Rows {
		kind := strings.TrimSpace(parseStringLike(row["kind"]))
		if kind == "" {
			continue
		}
		recon = append(recon, coverageDiff{
			Kind:            kind,
			AuthorityRate:   parseFloatLike(row["authority_rate"]),
			LiveCoverageDid: parseFloatLike(row["live_coverage_did"]),
			LiveCoverageRec: parseFloatLike(row["live_coverage_record"]),
			DeltaDid:        parseFloatLike(row["delta_did"]),
			DeltaRecord:     parseFloatLike(row["delta_record"]),
			LiveCountSource: "risingwave:mv_domain_coverage_live",
		})
	}
	sort.Slice(recon, func(i, j int) bool {
		return recon[i].Kind < recon[j].Kind
	})
	return recon, nil
}

func parseStringLike(v any) string {
	switch t := v.(type) {
	case nil:
		return ""
	case string:
		return t
	case []byte:
		return string(t)
	default:
		return fmt.Sprintf("%v", t)
	}
}

func parseFloatLike(v any) float64 {
	switch t := v.(type) {
	case nil:
		return 0
	case float64:
		return t
	case float32:
		return float64(t)
	case int:
		return float64(t)
	case int32:
		return float64(t)
	case int64:
		return float64(t)
	case uint:
		return float64(t)
	case uint32:
		return float64(t)
	case uint64:
		return float64(t)
	case string:
		n, _ := strconv.ParseFloat(strings.TrimSpace(t), 64)
		return n
	case []byte:
		n, _ := strconv.ParseFloat(strings.TrimSpace(string(t)), 64)
		return n
	default:
		n, _ := strconv.ParseFloat(strings.TrimSpace(fmt.Sprintf("%v", t)), 64)
		return n
	}
}
