package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net/http"
	neturl "net/url"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"text/tabwriter"
	"time"
)

// kyumeiKojiReport holds per-app DID self-information gathering evaluation.
type kyumeiKojiReport struct {
	Nanoid           string          `json:"nanoid"`
	Name             string          `json:"name"`
	DID              string          `json:"did"`
	DeclaredSources  []sourceInfo    `json:"declared_sources"`
	SourceGathered   map[string]bool `json:"source_gathered,omitempty"`
	LiveRecordCounts map[string]int  `json:"live_record_counts"`
	LiveStatus       liveDataStatus  `json:"live_status"`
	DIDReadiness     []didReadiness  `json:"did_readiness,omitempty"`
	SubDIDs          []subDIDInfo    `json:"sub_dids"`
	KnowledgeGaps    []knowledgeGap  `json:"knowledge_gaps"`
	Recommendations  []string        `json:"recommendations"`
	ReadinessScore   float64         `json:"readiness_score"`
	ReadinessGrade   string          `json:"readiness_grade"`
	Error            string          `json:"error,omitempty"`
}

type liveDataStatus struct {
	StatusRecords int    `json:"status_records"`
	CompletedRuns int    `json:"completed_runs"`
	RecordsHint   int    `json:"records_hint"`
	LastStatus    string `json:"last_status,omitempty"`
}

// sourceInfo represents a declared data source in an app.
type sourceInfo struct {
	ID       string `json:"id"`
	Name     string `json:"name"`
	URL      string `json:"url"`
	Format   string `json:"format"`
	Category string `json:"category"`
}

// subDIDInfo represents a path-based sub-DID.
type subDIDInfo struct {
	Path        string `json:"path"`
	DisplayName string `json:"display_name"`
	Category    string `json:"category"`
	Records     int    `json:"records"`
	LastUpdated string `json:"last_updated,omitempty"`
}

type didReadiness struct {
	ActorDID    string         `json:"actor_did"`
	Path        string         `json:"path,omitempty"`
	Records     int            `json:"records"`
	LastUpdated string         `json:"last_updated,omitempty"`
	LiveStatus  liveDataStatus `json:"live_status"`
}

// knowledgeGap identifies missing domain knowledge.
type knowledgeGap struct {
	Area       string `json:"area"`
	Severity   string `json:"severity"`
	Detail     string `json:"detail"`
	Suggestion string `json:"suggestion"`
}

var (
	reSourceBlock    = regexp.MustCompile(`(?s)\{[^{}]*sourceUrl\s*:\s*"(https?://[^"]+)"[^{}]*\}`)
	reSourceIDDecl   = regexp.MustCompile(`sourceId\s*:\s*"([^"]+)"`)
	reSourceTypeDecl = regexp.MustCompile(`sourceType\s*:\s*"([^"]+)"`)
	reSourceURL      = regexp.MustCompile(`(?:sourceUrl|caseDbUrl|legislationUrl|gazetteUrl)\s*:\s*"(https?://[^"]+)"`)
	reSourceName     = regexp.MustCompile(`(?:name|sourceId)\s*:\s*"([^"]+)"`)
	reSourceFmt      = regexp.MustCompile(`(?:caseDbFormat|sourceType|Format)\s*:\s*"([^"]+)"`)
	reSourceCat      = regexp.MustCompile(`(?:category)\s*:\s*"([^"]+)"`)
	reDIDPathDecl    = regexp.MustCompile(`path:\s*"([^"]+)"`)
	reDisplayName    = regexp.MustCompile(`displayName:\s*"([^"]+)"`)
	reCatDecl        = regexp.MustCompile(`category:\s*"([^"]+)"`)
	reCollectionFull = regexp.MustCompile(`["']((?:ai\.gftd\.apps|app\.bsky)\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_.-]+)["']`)
)

// runAppsKyumeiKoji evaluates an app's kyumei-koji readiness and knowledge gaps.
func runAppsKyumeiKoji(args []string) error {
	fs := flag.NewFlagSet("apps kyumei-koji", flag.ExitOnError)
	dir := fs.String("dir", "projects", "parent directory to scan")
	pdsURL := fs.String("pds", defaultPDSURL, "PDS base URL")
	nanoid := fs.String("nanoid", "", "single app nanoid (or positional arg)")
	domain := fs.String("domain", "", "app domain/host (e.g. isco or isco.etzhayyim.com); resolves to nanoid")
	seedNanoid := fs.String("seed-nanoid", "", "force seed target nanoid (overrides -domain resolution)")
	repoDID := fs.String("repo-did", "", "override primary repo DID for graph queries (did:web:...)")
	legacyLiveStatusFallback := fs.Bool("legacy-live-status-fallback", true, "enable compatibility fallback when liveData.status records miss status fields")
	jsonOut := fs.Bool("json", false, "JSON output")
	timeout := fs.Int("timeout", 15, "HTTP timeout seconds")
	maxSubDIDs := fs.Int("max-subdids", 24, "maximum number of sub-DIDs to evaluate live metrics for (0 = unlimited)")
	fast := fs.Bool("fast", false, "fast mode: skip expensive per-subDID live metrics/deep readiness")
	fs.Parse(args)

	if *nanoid == "" && fs.NArg() > 0 {
		*nanoid = fs.Arg(0)
	}
	if *nanoid == "" && strings.TrimSpace(*seedNanoid) != "" {
		*nanoid = strings.TrimSpace(*seedNanoid)
	}
	if *nanoid == "" && strings.TrimSpace(*domain) != "" {
		resolved, err := resolveNanoidForDomain(*dir, *domain)
		if err != nil {
			return err
		}
		*nanoid = resolved
	}

	if *nanoid == "" {
		return fmt.Errorf("nanoid required: gftd apps kyumei-koji -nanoid <id> | -domain <domain> | -seed-nanoid <id>  or  gftd apps <id> kyumei-koji")
	}

	httpClient := &http.Client{Timeout: time.Duration(*timeout) * time.Second}
	token := resolveGFTDToken()

	// 1. Discover app
	var app discoveredApp
	apps, err := discoverApps(*dir, *nanoid, "")
	if err != nil {
		return err
	}
	if len(apps) == 0 {
		app = discoveredApp{
			Nanoid: *nanoid,
			Name:   *nanoid,
			DID:    fmt.Sprintf("did:web:%s.etzhayyim.com", *nanoid),
		}
	} else {
		app = apps[0]
	}
	did := strings.TrimSpace(app.DID)
	if did == "" || !strings.HasPrefix(did, "did:") {
		did = fmt.Sprintf("did:web:%s.etzhayyim.com", app.Nanoid)
	}
	if strings.TrimSpace(*repoDID) != "" {
		did = strings.TrimSpace(*repoDID)
	}
	repoDIDs := repoDIDCandidates(did, app.Nanoid)
	if strings.TrimSpace(*domain) != "" {
		repoDIDs = appendRepoDIDs(repoDIDs, seedRepoDIDCandidatesForDomain(*domain)...)
	}
	repoClause := buildRepoClause("n", repoDIDs)

	fmt.Fprintf(os.Stderr, "==> Kyumei-Koji analysis for %s (%s)...\n\n", app.Name, app.Nanoid)

	report := kyumeiKojiReport{
		Nanoid:           app.Nanoid,
		Name:             app.Name,
		DID:              did,
		SourceGathered:   make(map[string]bool),
		LiveRecordCounts: make(map[string]int),
	}

	// 2. Static analysis: extract declared sources from app.ts
	appCollections := []string{}
	appNSCandidates := collectionNamespaceCandidates(app)
	appTsPath := findAppTs(app.Dir)
	if appTsPath != "" {
		content, readErr := os.ReadFile(appTsPath)
		if readErr == nil {
			src := string(content)
			report.DeclaredSources = extractDeclaredSources(src)
			report.SubDIDs = extractSubDIDDeclarations(src)
			if *maxSubDIDs > 0 && len(report.SubDIDs) > *maxSubDIDs {
				report.SubDIDs = report.SubDIDs[:*maxSubDIDs]
			}
			appCollections = extractCollectionLiterals(src, appNSCandidates)
		}
	}

	// 3. PDS live data: per-collection record counts
	collections := queryAppCollections(httpClient, *pdsURL, token, repoDIDs)
	if strings.TrimSpace(*domain) != "" {
		collections = appendCollections(collections, seedCollectionsForDomain(*domain)...)
	}
	collections = appendCollections(collections, appCollections...)
	subDIDCollections := prioritizeSubDIDCollections(*domain, collections, appCollections)
	// Per-collection counts: P10v2 has no generic `MATCH (n)` equivalent in SQL
	// (labels are per-vertex-table). Fall back to PDS REST (listRecords) directly
	// which remains the authoritative source for collection enumeration.
	_ = repoClause
	for _, col := range collections {
		report.LiveRecordCounts[col] = countCollectionRecordsByAPI(httpClient, *pdsURL, token, repoDIDs, col, 400)
	}
	liveRecordCountSum := 0
	for _, cnt := range report.LiveRecordCounts {
		liveRecordCountSum += cnt
	}
	totalRecords := liveRecordCountSum

	// 3.5. Live status records from host-level status collection (primary signal)
	report.LiveStatus = queryLiveDataStatus(httpClient, *pdsURL, token, repoDIDs, *legacyLiveStatusFallback)
	report.SourceGathered = queryGatheredSources(httpClient, *pdsURL, token, repoDIDs, *legacyLiveStatusFallback)
	if totalRecords == 0 && report.LiveStatus.RecordsHint > 0 {
		totalRecords = report.LiveStatus.RecordsHint
	}

	if !*fast {
		// Get sub-DID record counts
		for i := range report.SubDIDs {
			candidates := derivePathDidAliases([]string{did}, report.SubDIDs[i].Path)
			candidates = appendRepoDIDs(candidates, derivePathDidAliases(repoDIDs, report.SubDIDs[i].Path)...)
			if len(candidates) == 0 {
				// Legacy fallback for older nanoid-based repos.
				candidates = []string{
					fmt.Sprintf("did:web:%s.etzhayyim.com:%s", app.Nanoid, strings.ReplaceAll(report.SubDIDs[i].Path, "/", ":")),
				}
			}
			bestCnt := 0
			bestUpdated := ""
			for _, subDID := range candidates {
				cnt, lastUpdated := querySubDIDMetrics(httpClient, *pdsURL, token, subDID, subDIDCollections)
				if cnt > bestCnt {
					bestCnt = cnt
				}
				if lastUpdated > bestUpdated {
					bestUpdated = lastUpdated
				}
			}
			report.SubDIDs[i].Records = bestCnt
			report.SubDIDs[i].LastUpdated = bestUpdated
		}
		if totalRecords == 0 {
			subDIDTotal := 0
			for _, sd := range report.SubDIDs {
				subDIDTotal += sd.Records
			}
			if subDIDTotal > 0 {
				totalRecords = subDIDTotal
			}
		}
		report.DIDReadiness = buildDIDReadiness(httpClient, *pdsURL, token, repoDIDs, report.SubDIDs, subDIDCollections)
	}

	// 4. Identify knowledge gaps
	report.KnowledgeGaps = identifyKnowledgeGaps(report, totalRecords, report.SourceGathered)

	// 5. Generate recommendations
	report.Recommendations = generateKyumeiRecommendations(report)

	// 6. Readiness score
	report.ReadinessScore = computeKyumeiReadiness(report, totalRecords)
	report.ReadinessGrade = coverageGrade(report.ReadinessScore)

	if *jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(report)
	}

	printKyumeiKojiReport(report)
	return nil
}

func resolveNanoidForDomain(dir, rawDomain string) (string, error) {
	targetDomain := normalizeDomainLookup(rawDomain)
	if targetDomain == "" {
		return "", fmt.Errorf("invalid domain: %q", rawDomain)
	}
	seedNanoid, hasSeed := seedNanoidForDomain(targetDomain)

	targetHost := targetDomain
	for _, wd := range worldDomains {
		if normalizeDomainLookup(wd.Domain) == targetDomain {
			host := normalizeDomainLookup(strings.TrimSuffix(wd.App, ".etzhayyim.com"))
			if host != "" {
				targetHost = host
				break
			}
		}
	}

	apps, err := discoverApps(dir, "", "")
	if err != nil {
		return "", err
	}
	if len(apps) == 0 {
		return "", fmt.Errorf("no apps found under %s", dir)
	}

	bestNanoid := ""
	bestScore := -1
	for _, app := range apps {
		host := normalizeDomainLookup(appHostFromDID(app.DID))
		score := 0
		if host != "" && host == targetHost {
			score = 100
		} else if normalizeDomainLookup(app.Nanoid) == targetHost {
			score = 95
		} else {
			dirName := normalizeDomainLookup(filepath.Base(filepath.Dir(app.Dir)))
			if dirName == targetDomain || strings.Contains(dirName, targetDomain) {
				score = 80
			}
			fullPath := strings.ToLower(filepath.ToSlash(app.Dir))
			if strings.Contains(fullPath, "/ai-gftd-project-"+targetHost+"/") || strings.Contains(fullPath, "/ai-gftd-project-"+targetDomain+"/") {
				if score < 88 {
					score = 88
				}
			}
			leaf := normalizeDomainLookup(filepath.Base(app.Dir))
			if leaf == targetDomain || strings.Contains(leaf, targetDomain) {
				if score < 75 {
					score = 75
				}
			}
		}

		if score > bestScore {
			bestScore = score
			bestNanoid = app.Nanoid
		}
	}

	if bestScore > 0 && bestNanoid != "" {
		return bestNanoid, nil
	}
	if hasSeed && seedNanoid != "" {
		return seedNanoid, nil
	}
	return "", fmt.Errorf("app not found for domain: %s", rawDomain)
}

func seedNanoidForDomain(domain string) (string, bool) {
	norm := normalizeDomainLookup(domain)
	for _, def := range buildSeedRegistry() {
		if normalizeDomainLookup(def.Domain) == norm {
			return def.Nanoid, true
		}
	}
	return "", false
}

func seedRepoDIDCandidatesForDomain(domain string) []string {
	norm := normalizeDomainLookup(domain)
	for _, def := range buildSeedRegistry() {
		if normalizeDomainLookup(def.Domain) != norm {
			continue
		}
		out := []string{}
		if strings.TrimSpace(def.DID) != "" {
			out = append(out, strings.TrimSpace(def.DID))
		}
		if strings.TrimSpace(def.Nanoid) != "" {
			out = append(out, fmt.Sprintf("did:web:%s.etzhayyim.com", strings.TrimSpace(def.Nanoid)))
		}
		return out
	}
	return nil
}

func seedCollectionsForDomain(domain string) []string {
	norm := normalizeDomainLookup(domain)
	for _, def := range buildSeedRegistry() {
		if normalizeDomainLookup(def.Domain) != norm {
			continue
		}
		out := make([]string, 0, len(def.Records))
		for _, r := range def.Records {
			if strings.TrimSpace(r.Collection) != "" {
				out = append(out, strings.TrimSpace(r.Collection))
			}
		}
		return out
	}
	return nil
}

func normalizeDomainLookup(v string) string {
	s := strings.TrimSpace(strings.ToLower(v))
	s = strings.TrimPrefix(s, "did:web:")
	s = strings.TrimPrefix(s, "https://")
	s = strings.TrimPrefix(s, "http://")
	if i := strings.Index(s, "/"); i >= 0 {
		s = s[:i]
	}
	if i := strings.Index(s, ":"); i >= 0 {
		s = s[:i]
	}
	s = strings.TrimSuffix(s, ".etzhayyim.com")
	s = strings.TrimSuffix(s, ".gftd")
	s = strings.Trim(s, ".")
	return s
}

func appHostFromDID(did string) string {
	s := strings.TrimSpace(did)
	if !strings.HasPrefix(s, "did:web:") {
		return ""
	}
	s = strings.TrimPrefix(s, "did:web:")
	if i := strings.Index(s, ":"); i >= 0 {
		s = s[:i]
	}
	return s
}

// findAppTs locates the app.ts file from a discovered app directory.
func findAppTs(dir string) string {
	// Try standard path: {dir}/src/app.ts
	candidate := filepath.Join(dir, "src", "app.ts")
	if _, err := os.Stat(candidate); err == nil {
		return candidate
	}
	// Walk up looking for src/app.ts
	return ""
}

// extractDeclaredSources extracts data source declarations from app.ts content.
func extractDeclaredSources(content string) []sourceInfo {
	var sources []sourceInfo
	seen := map[string]bool{}

	// Prefer structured declaredSources object literals (sourceId-aware)
	for _, block := range reSourceBlock.FindAllString(content, -1) {
		urlMatch := reSourceURL.FindStringSubmatch(block)
		if len(urlMatch) < 2 {
			continue
		}
		url := urlMatch[1]
		if seen[url] {
			continue
		}
		seen[url] = true

		src := sourceInfo{URL: url}
		if m := reSourceIDDecl.FindStringSubmatch(block); len(m) > 1 {
			src.ID = strings.TrimSpace(m[1])
		}
		if m := reSourceName.FindStringSubmatch(block); len(m) > 1 {
			src.Name = strings.TrimSpace(m[1])
		}
		if m := reSourceTypeDecl.FindStringSubmatch(block); len(m) > 1 {
			src.Format = strings.TrimSpace(m[1])
		}
		if src.Name == "" {
			parts := strings.Split(url, "/")
			if len(parts) >= 3 {
				src.Name = parts[2]
			}
		}
		if src.ID == "" {
			src.ID = normalizeSourceID(src.Name, src.URL)
		}
		if src.Format == "" {
			src.Format = "browser_automation"
		}
		src.Category = "external"
		sources = append(sources, src)
	}

	// Fallback: generic URL scan
	urlMatches := reSourceURL.FindAllStringSubmatch(content, -1)
	for _, m := range urlMatches {
		url := m[1]
		if seen[url] {
			continue
		}
		seen[url] = true

		src := sourceInfo{URL: url}

		// Infer name from URL
		if strings.Contains(url, "courts.go.jp") {
			src.Name = "裁判所 (courts.go.jp)"
			src.Category = "court"
			src.Format = "browser_automation"
		} else if strings.Contains(url, "elaws.e-gov.go.jp") || strings.Contains(url, "laws.e-gov.go.jp") {
			src.Name = "e-Gov法令検索"
			src.Category = "legislation"
			src.Format = "api"
		} else if strings.Contains(url, "kanpou.npb.go.jp") {
			src.Name = "官報"
			src.Category = "gazette"
			src.Format = "browser_automation"
		} else if strings.Contains(url, "wikidata.org") {
			src.Name = "Wikidata"
			src.Category = "knowledge_graph"
			src.Format = "sparql"
		} else {
			// Generic: extract hostname
			parts := strings.Split(url, "/")
			if len(parts) >= 3 {
				src.Name = parts[2]
			}
			src.Category = "external"
			src.Format = "browser_automation"
		}

		src.ID = normalizeSourceID(src.Name, src.URL)
		sources = append(sources, src)
	}

	return sources
}

func normalizeSourceID(name, url string) string {
	raw := strings.TrimSpace(strings.ToLower(name))
	raw = strings.ReplaceAll(raw, " ", "_")
	if raw != "" && !strings.Contains(raw, ".") {
		return raw
	}
	if u := strings.TrimSpace(url); u != "" {
		if parsed, err := neturl.Parse(u); err == nil && parsed.Hostname() != "" {
			return strings.ToLower(parsed.Hostname())
		}
	}
	return raw
}

// extractSubDIDDeclarations extracts path-based DID declarations from app.ts.
func extractSubDIDDeclarations(content string) []subDIDInfo {
	var dids []subDIDInfo
	seen := map[string]bool{}

	pathMatches := reDIDPathDecl.FindAllStringSubmatch(content, -1)
	nameMatches := reDisplayName.FindAllStringSubmatch(content, -1)
	catMatches := reCatDecl.FindAllStringSubmatch(content, -1)

	for i, m := range pathMatches {
		path := m[1]
		if seen[path] {
			continue
		}
		seen[path] = true

		info := subDIDInfo{Path: path}
		if i < len(nameMatches) {
			info.DisplayName = nameMatches[i][1]
		}
		if i < len(catMatches) {
			info.Category = catMatches[i][1]
		}
		dids = append(dids, info)
	}

	return dids
}

func collectionNamespaceCandidates(app discoveredApp) []string {
	seen := map[string]bool{}
	out := make([]string, 0, 4)
	add := func(ns string) {
		ns = normalizeDomainLookup(ns)
		if ns == "" || seen[ns] {
			return
		}
		seen[ns] = true
		out = append(out, ns)
	}
	add(appHostFromDID(app.DID))
	add(app.Nanoid)
	add(app.Name)
	add(filepath.Base(filepath.Dir(app.Dir)))
	return out
}

func extractCollectionLiterals(content string, appNSCandidates []string) []string {
	matches := reCollectionFull.FindAllStringSubmatch(content, -1)
	seen := map[string]bool{}
	out := make([]string, 0, len(matches))
	prefixes := make([]string, 0, len(appNSCandidates))
	for _, ns := range appNSCandidates {
		if ns == "" {
			continue
		}
		prefixes = append(prefixes, "ai.gftd.apps."+ns+".")
	}
	for _, m := range matches {
		if len(m) < 2 {
			continue
		}
		col := strings.TrimSpace(m[1])
		if col == "" || seen[col] {
			continue
		}
		if len(prefixes) > 0 {
			ok := false
			for _, pfx := range prefixes {
				if strings.HasPrefix(col, pfx) {
					ok = true
					break
				}
			}
			if !ok {
				continue
			}
		}
		seen[col] = true
		out = append(out, col)
	}
	return out
}

// queryAppCollections returns an empty list — P10v2 collapses collection
// enumeration into per-vertex tables, so a generic "list collections for
// these repos" query no longer has a SQL equivalent. Callers fall back to
// PDS listRecords enumeration for known collections.
func queryAppCollections(_ *http.Client, _, _ string, _ []string) []string {
	return nil
}

// legacyParseCollections retained so the downstream result parser below
// still compiles — dead code kept as a comment-sized stub.
func legacyParseCollections(_ []byte) []string {
	var collections []string
	// legacy body removed during kagami → RisingWave direct migration.
	// The historical column/object parse path is intentionally gone.
	{
		row := map[string]any{}
		if col, ok := row["col"].(string); ok && col != "" {
			if strings.HasPrefix(col, "ai.gftd.apps.") || strings.HasPrefix(col, "app.bsky.") {
				collections = append(collections, col)
			}
		}
	}
	return collections
}

// identifyKnowledgeGaps finds areas where domain knowledge is missing.
func identifyKnowledgeGaps(r kyumeiKojiReport, totalRecords int, gathered map[string]bool) []knowledgeGap {
	var gaps []knowledgeGap

	// Gap: no data sources declared
	if len(r.DeclaredSources) == 0 {
		gaps = append(gaps, knowledgeGap{
			Area:       "data_sources",
			Severity:   "critical",
			Detail:     "No external data sources declared in app.ts",
			Suggestion: "declare-sources: Add sourceUrl/caseDbUrl constants for each 1次ソース",
		})
	}

	// Gap: no sub-DIDs
	if len(r.SubDIDs) == 0 {
		gaps = append(gaps, knowledgeGap{
			Area:       "sub_dids",
			Severity:   "high",
			Detail:     "No path-based sub-DIDs declared (Multi-DID)",
			Suggestion: "declare-sources: Create comAtprotoIdentityCreate() for domain entities",
		})
	}

	// Gap: no live records
	if totalRecords == 0 {
		gaps = append(gaps, knowledgeGap{
			Area:       "live_data",
			Severity:   "critical",
			Detail:     "No domain records in PDS graph",
			Suggestion: "gather: Run seed/collection commands to populate initial data",
		})
	} else if totalRecords < 10 {
		gaps = append(gaps, knowledgeGap{
			Area:       "live_data",
			Severity:   "medium",
			Detail:     fmt.Sprintf("Only %d domain records — minimal data", totalRecords),
			Suggestion: "gather: Run collection jobs to increase coverage",
		})
	}

	// Gap: sub-DIDs with 0 records
	for _, sd := range r.SubDIDs {
		if sd.Records == 0 {
			gaps = append(gaps, knowledgeGap{
				Area:       "sub_did_empty",
				Severity:   "medium",
				Detail:     fmt.Sprintf("Sub-DID %s has 0 records", sd.Path),
				Suggestion: fmt.Sprintf("gather: Collect data for %s (%s)", sd.DisplayName, sd.Path),
			})
		}
	}

	// Gap: declared sources with no corresponding collection
	for _, src := range r.DeclaredSources {
		srcID := normalizeSourceID(src.ID, src.URL)
		hasData := gathered[srcID]
		if !hasData && srcID == "" {
			hasData = gathered[strings.ToLower(strings.TrimSpace(src.URL))]
		}
		if !hasData && len(gathered) > 0 {
			gaps = append(gaps, knowledgeGap{
				Area:       "source_ungathered",
				Severity:   "medium",
				Detail:     fmt.Sprintf("Source %s (%s) declared but no matching records found", src.Name, src.URL),
				Suggestion: fmt.Sprintf("gather: Create collection job for %s", src.Name),
			})
		}
	}

	return gaps
}

// generateKyumeiRecommendations produces actionable next steps.
func generateKyumeiRecommendations(r kyumeiKojiReport) []string {
	var recs []string

	criticalGaps := 0
	for _, g := range r.KnowledgeGaps {
		if g.Severity == "critical" {
			criticalGaps++
		}
	}

	if criticalGaps > 0 {
		recs = append(recs, fmt.Sprintf("CRITICAL: %d critical knowledge gaps — address before production", criticalGaps))
	}

	if len(r.DeclaredSources) > 0 && len(r.LiveRecordCounts) == 0 {
		recs = append(recs, "Phase 1 (declare-sources): Sources declared. Run collection jobs to gather data")
	}

	if len(r.SubDIDs) > 0 {
		emptyDIDs := 0
		for _, sd := range r.SubDIDs {
			if sd.Records == 0 {
				emptyDIDs++
			}
		}
		if emptyDIDs > 0 {
			recs = append(recs, fmt.Sprintf("Phase 2 (gather): %d/%d sub-DIDs have 0 records", emptyDIDs, len(r.SubDIDs)))
		}
	}

	totalRecords := 0
	for _, c := range r.LiveRecordCounts {
		totalRecords += c
	}
	if totalRecords > 0 {
		recs = append(recs, "Phase 3 (validate): Cross-reference gathered facts against existing records")
		recs = append(recs, "Phase 4 (integrate): Merge validated facts into domain graph")
	}

	if len(recs) == 0 {
		recs = append(recs, "All kyumei-koji phases complete — domain knowledge is well-covered")
	}

	return recs
}

// computeKyumeiReadiness scores how ready an app is for kyumei-koji.
func computeKyumeiReadiness(r kyumeiKojiReport, totalRecords int) float64 {
	score := 0.0

	// 30%: declared sources
	srcScore := float64(min(len(r.DeclaredSources)*15, 100))
	score += 0.30 * srcScore

	// 25%: live data
	score += 0.25 * tierScore(totalRecords, 1, 10, 100)

	// 20%: sub-DID utilization
	if len(r.SubDIDs) > 0 {
		active := 0
		for _, sd := range r.SubDIDs {
			if sd.Records > 0 {
				active++
			}
		}
		score += 0.20 * (float64(active) / float64(len(r.SubDIDs)) * 100)
	}

	// 15%: knowledge gap severity
	criticalGaps := 0
	for _, g := range r.KnowledgeGaps {
		if g.Severity == "critical" {
			criticalGaps++
		}
	}
	if criticalGaps == 0 {
		score += 0.15 * 100
	} else {
		score += 0.15 * float64(max(0, 100-criticalGaps*30))
	}

	// 10%: collection/status diversity (prefer status records, fallback to collection count)
	diversity := len(r.LiveRecordCounts)
	if r.LiveStatus.StatusRecords > 0 {
		diversity = max(diversity, 1)
	}
	score += 0.10 * tierScore(diversity, 1, 3, 6)

	return score
}

func queryLiveDataStatus(client *http.Client, pdsURL, token string, repoDIDs []string, _ bool) liveDataStatus {
	// Generic `(n)` Sql has no direct SQL equivalent in P10v2; rely on PDS
	// listRecords for the single collection we care about.
	status := liveDataStatus{}
	rows := listCollectionRecords(client, pdsURL, token, repoDIDs, "ai.gftd.liveData.status", 500)
	status.StatusRecords = len(rows)
	for i, row := range rows {
		st := strings.ToLower(strings.TrimSpace(strVal(row["status"])))
		if i == 0 && st != "" {
			status.LastStatus = st
		}
		if st == "completed" {
			status.CompletedRuns++
			status.RecordsHint += parseIntLike(row["recordsCreated"])
		}
	}
	return status
}

func queryGatheredSources(client *http.Client, pdsURL, token string, repoDIDs []string, _ bool) map[string]bool {
	out := make(map[string]bool)
	// PDS listRecords is the single source after the Sql path was archived.
	for _, row := range listCollectionRecords(client, pdsURL, token, repoDIDs, "ai.gftd.liveData.status", 500) {
		st := strings.ToLower(strings.TrimSpace(strVal(row["status"])))
		if st != "completed" && st != "" {
			continue
		}
		id := normalizeSourceID(strVal(row["sourceId"]), strVal(row["sourceUrl"]))
		if id != "" {
			out[id] = true
		}
		urlKey := strings.ToLower(strings.TrimSpace(strVal(row["sourceUrl"])))
		if urlKey != "" {
			out[urlKey] = true
		}
	}
	return out
}

type listRecordEntry struct {
	URI   string
	Value map[string]interface{}
}

func listCollectionRecords(client *http.Client, pdsURL, token string, repoDIDs []string, collection string, limit int) []map[string]interface{} {
	seen := map[string]bool{}
	out := make([]map[string]interface{}, 0, limit)
	for _, repo := range repoDIDs {
		if repo == "" {
			continue
		}
		entries := listCollectionRecordEntriesForRepo(client, pdsURL, token, repo, collection, limit)
		for _, rec := range entries {
			if rec.URI != "" && seen[rec.URI] {
				continue
			}
			if rec.URI != "" {
				seen[rec.URI] = true
			}
			out = append(out, rec.Value)
			if len(out) >= limit {
				break
			}
		}
		if len(out) >= limit {
			break
		}
	}
	return out
}

func listCollectionRecordEntriesForRepo(client *http.Client, pdsURL, token, repoDID, collection string, limit int) []listRecordEntry {
	out := make([]listRecordEntry, 0, limit)
	if repoDID == "" || collection == "" || limit <= 0 {
		return out
	}
	cursor := ""
	for page := 0; page < 5 && len(out) < limit; page++ {
		base := strings.TrimRight(pdsURL, "/") + "/xrpc/com.atproto.repo.listRecords"
		q := neturl.Values{}
		q.Set("repo", repoDID)
		q.Set("collection", collection)
		q.Set("limit", "50")
		if cursor != "" {
			q.Set("cursor", cursor)
		}
		req, err := http.NewRequest("GET", base+"?"+q.Encode(), nil)
		if err != nil {
			break
		}
		if token != "" {
			req.Header.Set("Authorization", "Bearer "+token)
		}
		resp, err := client.Do(req)
		if err != nil {
			break
		}
		var payload struct {
			Cursor  string `json:"cursor"`
			Records []struct {
				URI   string                 `json:"uri"`
				Value map[string]interface{} `json:"value"`
			} `json:"records"`
		}
		body, _ := io.ReadAll(resp.Body)
		resp.Body.Close()
		if resp.StatusCode >= 400 || json.Unmarshal(body, &payload) != nil {
			break
		}
		for _, rec := range payload.Records {
			out = append(out, listRecordEntry{URI: rec.URI, Value: rec.Value})
			if len(out) >= limit {
				break
			}
		}
		if payload.Cursor == "" || len(payload.Records) == 0 || payload.Cursor == cursor {
			break
		}
		cursor = payload.Cursor
	}
	return out
}

func buildDIDReadiness(client *http.Client, pdsURL, token string, primaryRepoDIDs []string, subDIDs []subDIDInfo, appCollections []string) []didReadiness {
	out := make([]didReadiness, 0, len(subDIDs)+1)
	primaryDid := pickCanonicalDid(primaryRepoDIDs)
	primaryRecords, primaryUpdated := querySubDIDMetrics(client, pdsURL, token, primaryDid, appCollections)
	out = append(out, didReadiness{
		ActorDID:    primaryDid,
		Records:     primaryRecords,
		LastUpdated: primaryUpdated,
		LiveStatus:  queryActorLiveStatus(client, pdsURL, token, primaryRepoDIDs, primaryRepoDIDs),
	})
	for _, sd := range subDIDs {
		actorCandidates := derivePathDidAliases(primaryRepoDIDs, sd.Path)
		actorDid := pickCanonicalDid(actorCandidates)
		out = append(out, didReadiness{
			ActorDID:    actorDid,
			Path:        sd.Path,
			Records:     sd.Records,
			LastUpdated: sd.LastUpdated,
			LiveStatus:  queryActorLiveStatus(client, pdsURL, token, primaryRepoDIDs, actorCandidates),
		})
	}
	return out
}

func queryActorLiveStatus(client *http.Client, pdsURL, token string, primaryRepoDIDs, actorDidCandidates []string) liveDataStatus {
	entries := []listRecordEntry{}
	actorSet := map[string]bool{}
	for _, d := range actorDidCandidates {
		d = strings.TrimSpace(d)
		if d != "" {
			actorSet[d] = true
		}
	}
	for actorDid := range actorSet {
		entries = append(entries, listCollectionRecordEntriesForRepo(client, pdsURL, token, actorDid, "ai.gftd.liveData.status", 200)...)
	}
	for _, primaryRepoDID := range primaryRepoDIDs {
		for _, rec := range listCollectionRecordEntriesForRepo(client, pdsURL, token, primaryRepoDID, "ai.gftd.liveData.status", 500) {
			recActor := strings.TrimSpace(strVal(rec.Value["actorDid"]))
			if recActor != "" && actorSet[recActor] {
				entries = append(entries, rec)
			}
		}
	}
	if len(entries) > 1 {
		uniq := make([]listRecordEntry, 0, len(entries))
		seen := map[string]bool{}
		for _, rec := range entries {
			if rec.URI != "" {
				if seen[rec.URI] {
					continue
				}
				seen[rec.URI] = true
			}
			uniq = append(uniq, rec)
		}
		entries = uniq
	}
	status := liveDataStatus{}
	if len(entries) == 0 {
		return status
	}
	status.StatusRecords = len(entries)
	for i, rec := range entries {
		st := strings.ToLower(strings.TrimSpace(strVal(rec.Value["status"])))
		if i == 0 && st != "" {
			status.LastStatus = st
		}
		if st == "completed" {
			status.CompletedRuns++
			status.RecordsHint += parseIntLike(rec.Value["recordsCreated"])
		}
	}
	return status
}

func pickCanonicalDid(candidates []string) string {
	for _, d := range candidates {
		d = strings.TrimSpace(d)
		if d == "" {
			continue
		}
		m := regexp.MustCompile(`^did:web:([a-z0-9]{8})\.gftd\.ai(?::|$)`).FindStringSubmatch(d)
		if len(m) == 0 {
			return strings.TrimSpace(d)
		}
	}
	for _, d := range candidates {
		if strings.TrimSpace(d) != "" {
			return strings.TrimSpace(d)
		}
	}
	return ""
}

func derivePathDidAliases(baseDIDs []string, path string) []string {
	normalizedPath := strings.ReplaceAll(strings.Trim(path, "/"), "/", ":")
	if normalizedPath == "" {
		return nil
	}
	seen := map[string]bool{}
	out := make([]string, 0, len(baseDIDs))
	for _, base := range baseDIDs {
		base = strings.TrimSpace(base)
		if base == "" {
			continue
		}
		host := strings.TrimPrefix(base, "did:web:")
		if idx := strings.Index(host, ":"); idx >= 0 {
			host = host[:idx]
		}
		if host == "" {
			continue
		}
		d := "did:web:" + host + ":" + normalizedPath
		if !seen[d] {
			seen[d] = true
			out = append(out, d)
		}
	}
	return out
}


func strVal(v interface{}) string {
	if v == nil {
		return ""
	}
	switch t := v.(type) {
	case string:
		return t
	case float64:
		return fmt.Sprintf("%.0f", t)
	default:
		return fmt.Sprintf("%v", t)
	}
}

func querySubDIDMetrics(client *http.Client, pdsURL, token, subDID string, appCollections []string) (int, string) {
	if len(appCollections) > 0 {
		total := 0
		last := ""
		for _, col := range appCollections {
			count, updated := querySubDIDCollectionCount(client, pdsURL, token, subDID, col)
			if count == 0 && strings.TrimSpace(token) != "" {
				// Some tokens can observe sparse/empty listRecords on public repos.
				// Fall back to anonymous read before marking sub-DID as empty.
				count2, updated2 := querySubDIDCollectionCount(client, pdsURL, "", subDID, col)
				if count2 > count {
					count = count2
				}
				if updated2 > updated {
					updated = updated2
				}
			}
			total += count
			if updated > last {
				last = updated
			}
		}
		if total > 0 {
			return total, normalizeTimeLike(last)
		}
	}
	// Sql fallback archived; nothing to count for unknown collections.
	_ = client
	_ = pdsURL
	_ = token
	_ = subDID
	return 0, ""
}

func querySubDIDCollectionCount(client *http.Client, pdsURL, token, subDID, collection string) (int, string) {
	base := strings.TrimRight(pdsURL, "/") + "/xrpc/com.atproto.repo.listRecords"
	cursor := ""
	total := 0
	last := ""
	for page := 0; page < 8; page++ {
		q := neturl.Values{}
		q.Set("repo", subDID)
		q.Set("collection", collection)
		q.Set("limit", "50")
		if cursor != "" {
			q.Set("cursor", cursor)
		}
		var (
			resp *http.Response
			err  error
			body []byte
		)
		for attempt := 0; attempt < 3; attempt++ {
			req, reqErr := http.NewRequest("GET", base+"?"+q.Encode(), nil)
			if reqErr != nil {
				err = reqErr
				break
			}
			if token != "" {
				req.Header.Set("Authorization", "Bearer "+token)
			}
			resp, err = client.Do(req)
			if err != nil {
				time.Sleep(time.Duration(attempt+1) * 250 * time.Millisecond)
				continue
			}
			body, _ = io.ReadAll(resp.Body)
			resp.Body.Close()
			if (resp.StatusCode == http.StatusUnauthorized || resp.StatusCode == http.StatusForbidden) && token != "" {
				// Token may be stale in env; fall back to anonymous listRecords for public repos.
				req2, reqErr2 := http.NewRequest("GET", base+"?"+q.Encode(), nil)
				if reqErr2 == nil {
					resp2, err2 := client.Do(req2)
					if err2 == nil {
						body2, _ := io.ReadAll(resp2.Body)
						resp2.Body.Close()
						resp = resp2
						body = body2
					}
				}
			}
			if resp.StatusCode == http.StatusTooManyRequests || strings.Contains(string(body), "1015") {
				time.Sleep(time.Duration(attempt+1) * time.Second)
				continue
			}
			break
		}
		var payload struct {
			Cursor  string `json:"cursor"`
			Records []struct {
				Value map[string]interface{} `json:"value"`
			} `json:"records"`
		}
		if err != nil || resp == nil || resp.StatusCode >= 400 || json.Unmarshal(body, &payload) != nil {
			break
		}
		total += len(payload.Records)
		for _, rec := range payload.Records {
			updated := strVal(rec.Value["updatedAt"])
			if updated == "" {
				updated = strVal(rec.Value["createdAt"])
			}
			if updated > last {
				last = updated
			}
		}
		if payload.Cursor == "" || len(payload.Records) == 0 || payload.Cursor == cursor {
			break
		}
		cursor = payload.Cursor
	}
	return total, last
}

func parseIntLike(v interface{}) int {
	switch t := v.(type) {
	case nil:
		return 0
	case int:
		return t
	case int64:
		return int(t)
	case float64:
		return int(t)
	case string:
		var n int64
		if _, err := fmt.Sscanf(strings.TrimSpace(t), "%d", &n); err == nil {
			return int(n)
		}
		return 0
	default:
		var n int64
		if _, err := fmt.Sscanf(fmt.Sprintf("%v", t), "%d", &n); err == nil {
			return int(n)
		}
		return 0
	}
}

func normalizeTimeLike(raw string) string {
	s := strings.TrimSpace(raw)
	if s == "" {
		return ""
	}
	if len(s) >= 10 && strings.Contains(s, "T") {
		return s
	}
	var epoch int64
	if _, err := fmt.Sscanf(s, "%d", &epoch); err != nil || epoch <= 0 {
		return s
	}
	// Heuristic: 13+ digits => milliseconds
	if epoch > 9_999_999_999 {
		return time.UnixMilli(epoch).UTC().Format(time.RFC3339)
	}
	return time.Unix(epoch, 0).UTC().Format(time.RFC3339)
}

func repoDIDCandidates(primaryDID, nanoid string) []string {
	seen := map[string]bool{}
	out := make([]string, 0, 2)
	add := func(d string) {
		d = strings.TrimSpace(d)
		if d == "" || seen[d] {
			return
		}
		seen[d] = true
		out = append(out, d)
	}
	add(primaryDID)
	if nanoid != "" {
		add(fmt.Sprintf("did:web:%s.etzhayyim.com", nanoid))
	}
	return out
}

func appendRepoDIDs(base []string, extra ...string) []string {
	seen := map[string]bool{}
	out := make([]string, 0, len(base)+len(extra))
	for _, d := range base {
		d = strings.TrimSpace(d)
		if d == "" || seen[d] {
			continue
		}
		seen[d] = true
		out = append(out, d)
	}
	for _, d := range extra {
		d = strings.TrimSpace(d)
		if d == "" || seen[d] {
			continue
		}
		seen[d] = true
		out = append(out, d)
	}
	return out
}

func appendCollections(base []string, extra ...string) []string {
	seen := map[string]bool{}
	out := make([]string, 0, len(base)+len(extra))
	for _, c := range base {
		c = strings.TrimSpace(c)
		if c == "" || seen[c] {
			continue
		}
		seen[c] = true
		out = append(out, c)
	}
	for _, c := range extra {
		c = strings.TrimSpace(c)
		if c == "" || seen[c] {
			continue
		}
		seen[c] = true
		out = append(out, c)
	}
	return out
}

func prioritizeSubDIDCollections(domain string, collections, appCollections []string) []string {
	// Sub-DID checks should be lightweight to avoid listRecords throttling (1015).
	norm := normalizeDomainLookup(domain)
	preferred := []string{}
	switch norm {
	case "treaty":
		preferred = append(preferred, "ai.gftd.apps.treaty.treatyBody")
	case "sovereign", "states":
		preferred = append(preferred, "ai.gftd.apps.states.sovereign")
	case "blockchain":
		preferred = append(preferred, "ai.gftd.apps.blockchain.chain")
	case "religious":
		preferred = append(preferred, "ai.gftd.apps.religious.system")
	case "customary":
		preferred = append(preferred, "ai.gftd.apps.customary.rule")
	}
	if len(preferred) > 0 {
		return appendCollections(preferred)
	}
	for _, c := range appCollections {
		c = strings.TrimSpace(c)
		if strings.HasPrefix(c, "ai.gftd.apps.") {
			preferred = append(preferred, c)
		}
	}
	if len(preferred) == 0 {
		preferred = append(preferred, collections...)
	}
	merged := appendCollections(preferred)
	if len(merged) > 6 {
		merged = merged[:6]
	}
	return merged
}

func countCollectionRecordsByAPI(client *http.Client, pdsURL, token string, repoDIDs []string, collection string, limit int) int {
	if collection == "" || limit <= 0 {
		return 0
	}
	seen := map[string]bool{}
	total := 0
	for _, repo := range repoDIDs {
		if strings.TrimSpace(repo) == "" {
			continue
		}
		entries := listCollectionRecordEntriesForRepo(client, pdsURL, token, repo, collection, limit)
		for _, e := range entries {
			if e.URI != "" {
				if seen[e.URI] {
					continue
				}
				seen[e.URI] = true
			}
			total++
			if total >= limit {
				return total
			}
		}
	}
	if total == 0 && strings.TrimSpace(token) != "" {
		// Retry once without auth to avoid token-scoped visibility issues.
		return countCollectionRecordsByAPI(client, pdsURL, "", repoDIDs, collection, limit)
	}
	return total
}

func buildRepoClause(varName string, repoDIDs []string) string {
	if len(repoDIDs) == 0 {
		return "false"
	}
	parts := make([]string, 0, len(repoDIDs)*2)
	for _, did := range repoDIDs {
		escaped := strings.ReplaceAll(strings.ReplaceAll(did, `\`, `\\`), `"`, `\"`)
		parts = append(parts, fmt.Sprintf(`%s.repo = "%s"`, varName, escaped))
		parts = append(parts, fmt.Sprintf(`%s.repo STARTS WITH "%s:"`, varName, escaped))
	}
	return "(" + strings.Join(parts, " OR ") + ")"
}

func printKyumeiKojiReport(r kyumeiKojiReport) {
	w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)

	fmt.Fprintf(w, "Kyumei-Koji (究明工事) Report: %s (%s)\n", r.Name, r.Nanoid)
	fmt.Fprintf(w, "DID: %s\n", r.DID)
	fmt.Fprintf(w, "Readiness: %s (%.1f / 100)\n\n", r.ReadinessGrade, r.ReadinessScore)

	// Declared sources
	fmt.Fprintf(w, "Declared Sources (%d):\n", len(r.DeclaredSources))
	if len(r.DeclaredSources) > 0 {
		fmt.Fprintln(w, "  Name\tCategory\tFormat\tURL")
		fmt.Fprintln(w, "  ----\t--------\t------\t---")
		for _, s := range r.DeclaredSources {
			fmt.Fprintf(w, "  %s\t%s\t%s\t%s\n", s.Name, s.Category, s.Format, truncateStr(s.URL, 50))
		}
	}
	fmt.Fprintln(w)

	// Sub-DIDs
	fmt.Fprintf(w, "Sub-DIDs (%d):\n", len(r.SubDIDs))
	if len(r.SubDIDs) > 0 {
		fmt.Fprintln(w, "  Path\tDisplay Name\tCategory\tRecords\tLast Updated")
		fmt.Fprintln(w, "  ----\t------------\t--------\t-------\t------------")
		for _, d := range r.SubDIDs {
			fmt.Fprintf(w, "  %s\t%s\t%s\t%d\t%s\n", d.Path, d.DisplayName, d.Category, d.Records, d.LastUpdated)
		}
	}
	fmt.Fprintln(w)

	// DID readiness
	if len(r.DIDReadiness) > 0 {
		fmt.Fprintf(w, "DID Readiness (%d):\n", len(r.DIDReadiness))
		fmt.Fprintln(w, "  Actor DID\tPath\tRecords\tStatusRecords\tCompletedRuns\tRecordsHint\tLastStatus")
		fmt.Fprintln(w, "  ---------\t----\t-------\t-------------\t-------------\t-----------\t----------")
		for _, d := range r.DIDReadiness {
			fmt.Fprintf(
				w,
				"  %s\t%s\t%d\t%d\t%d\t%d\t%s\n",
				truncateStr(d.ActorDID, 64),
				d.Path,
				d.Records,
				d.LiveStatus.StatusRecords,
				d.LiveStatus.CompletedRuns,
				d.LiveStatus.RecordsHint,
				d.LiveStatus.LastStatus,
			)
		}
		fmt.Fprintln(w)
	}

	// Live record counts
	if len(r.LiveRecordCounts) > 0 {
		fmt.Fprintln(w, "Live Record Counts:")
		for col, cnt := range r.LiveRecordCounts {
			fmt.Fprintf(w, "  %s\t%d\n", col, cnt)
		}
		fmt.Fprintln(w)
	}
	if r.LiveStatus.StatusRecords > 0 {
		fmt.Fprintln(w, "Live Status (ai.gftd.liveData.status):")
		fmt.Fprintf(w, "  status_records\t%d\n", r.LiveStatus.StatusRecords)
		fmt.Fprintf(w, "  completed_runs\t%d\n", r.LiveStatus.CompletedRuns)
		fmt.Fprintf(w, "  records_hint\t%d\n", r.LiveStatus.RecordsHint)
		if r.LiveStatus.LastStatus != "" {
			fmt.Fprintf(w, "  last_status\t%s\n", r.LiveStatus.LastStatus)
		}
		fmt.Fprintln(w)
	}

	// Knowledge gaps
	if len(r.KnowledgeGaps) > 0 {
		fmt.Fprintf(w, "Knowledge Gaps (%d):\n", len(r.KnowledgeGaps))
		fmt.Fprintln(w, "  Severity\tArea\tDetail")
		fmt.Fprintln(w, "  --------\t----\t------")
		for _, g := range r.KnowledgeGaps {
			fmt.Fprintf(w, "  %s\t%s\t%s\n", g.Severity, g.Area, g.Detail)
			fmt.Fprintf(w, "  \t\t→ %s\n", g.Suggestion)
		}
		fmt.Fprintln(w)
	}

	// Recommendations
	if len(r.Recommendations) > 0 {
		fmt.Fprintln(w, "Recommendations:")
		for _, rec := range r.Recommendations {
			fmt.Fprintf(w, "  • %s\n", rec)
		}
		fmt.Fprintln(w)
	}

	w.Flush()
}
