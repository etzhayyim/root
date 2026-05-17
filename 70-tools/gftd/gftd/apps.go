package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"net/http"
	"os"
	"sort"
	"sync"
	"text/tabwriter"
	"time"

	"github.com/etzhayyim/root/70-tools/gftd/gftd/db"
)

// appKPIStatus holds per-app KPI metrics from PDS yata graph.
type appKPIStatus struct {
	Nanoid    string  `json:"nanoid"`
	Name      string  `json:"name"`
	DID       string  `json:"did"`
	UIType    string  `json:"ui_type"`
	Posts     int     `json:"posts"`
	Likes     int     `json:"likes"`
	Reposts   int     `json:"reposts"`
	Followers int     `json:"followers"`
	Following int     `json:"following"`
	Guides    int     `json:"guides"`
	Records   int     `json:"records"`
	SubDIDs   int     `json:"sub_dids"`
	HealthOK  bool    `json:"health_ok"`
	KPIScore  float64 `json:"kpi_score"`
	Error     string  `json:"error,omitempty"`
}

// runApps dispatches `gftd apps` subcommands.
func runApps(args []string) error {
	if len(args) == 0 {
		return runAppsStatus(args)
	}
	switch args[0] {
	case "status":
		return runAppsStatus(args[1:])
	case "coverage":
		return runAppsCoverage(args[1:])
	case "kyumei-koji":
		return runAppsKyumeiKoji(args[1:])
	case "help", "--help", "-h":
		printAppsUsage()
		return nil
	default:
		// Check if first arg is a nanoid followed by a subcommand: gftd apps <nanoid> coverage
		if len(args) >= 2 {
			switch args[1] {
			case "coverage":
				return runAppsCoverage(append([]string{"-nanoid", args[0]}, args[2:]...))
			case "kyumei-koji":
				return runAppsKyumeiKoji(append([]string{"-nanoid", args[0]}, args[2:]...))
			}
		}
		return runAppsStatus(args)
	}
}

func printAppsUsage() {
	fmt.Println(`gftd apps — App KPI status, coverage evaluation, and kyumei-koji analysis

USAGE:
  gftd apps [subcommand] [flags]
  gftd apps <nanoid> coverage       Per-app domain knowledge coverage
  gftd apps <nanoid> kyumei-koji    Per-app DID self-information gathering analysis

SUBCOMMANDS:
  status (default)   Per-app KPI dashboard (posts, likes, followers, records)
  coverage           Domain knowledge coverage evaluation (requires -nanoid or positional nanoid)
  kyumei-koji        DID self-information gathering readiness (requires -nanoid or positional nanoid)

FLAGS (status):
  -dir         Parent directory to scan (default: projects)
  -pds         PDS base URL (default: https://mod.etzhayyim.com)
  -filter      Glob pattern for app names
  -nanoid      Check single app
  -sort        Sort by: kpi, posts, likes, followers, records, name (default: kpi)
  -limit       Limit output (0=all)
  -concurrency Parallel workers (default: 16)
  -timeout     HTTP timeout seconds (default: 15)
  -json        JSON output

FLAGS (coverage / kyumei-koji):
  -nanoid      App nanoid (required, or pass as positional arg)
  -domain      App domain/host for lookup (kyumei-koji only; e.g. isco or isco.etzhayyim.com)
  -seed-nanoid Force seed target nanoid (kyumei-koji only)
  -repo-did    Override repo DID for graph query (kyumei-koji only)
  -pds         PDS base URL (default: https://mod.etzhayyim.com)
  -dir         Parent directory to scan (default: projects)
  -timeout     HTTP timeout seconds (default: 15)
  -json        JSON output`)
}

// runAppsStatus queries PDS for per-app social metrics and KPI scores.
func runAppsStatus(args []string) error {
	fs := flag.NewFlagSet("apps status", flag.ExitOnError)
	dir := fs.String("dir", "projects", "parent directory to scan")
	pdsURL := fs.String("pds", defaultPDSURL, "PDS base URL")
	filter := fs.String("filter", "", "glob pattern")
	nanoid := fs.String("nanoid", "", "single app nanoid")
	sortBy := fs.String("sort", "kpi", "sort by: kpi, posts, likes, followers, records, name")
	limit := fs.Int("limit", 0, "limit output (0=all)")
	concurrency := fs.Int("concurrency", 16, "parallel workers")
	timeout := fs.Int("timeout", 15, "HTTP timeout seconds")
	jsonOut := fs.Bool("json", false, "JSON output")
	fs.Parse(args)

	httpClient := &http.Client{Timeout: time.Duration(*timeout) * time.Second}

	apps, err := discoverApps(*dir, *nanoid, *filter)
	if err != nil {
		return err
	}
	if len(apps) == 0 {
		fmt.Fprintln(os.Stderr, "No apps found")
		return nil
	}

	fmt.Fprintf(os.Stderr, "==> Querying KPI for %d apps...\n\n", len(apps))

	results := make([]appKPIStatus, len(apps))
	var wg sync.WaitGroup
	sem := make(chan struct{}, *concurrency)

	for i, app := range apps {
		wg.Add(1)
		go func(idx int, a discoveredApp) {
			defer wg.Done()
			sem <- struct{}{}
			defer func() { <-sem }()
			results[idx] = queryAppKPI(httpClient, a, *pdsURL)
		}(i, app)
	}
	wg.Wait()

	// Sort
	sortAppsResults(results, *sortBy)

	// Limit
	if *limit > 0 && *limit < len(results) {
		results = results[:*limit]
	}

	if *jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(results)
	}

	printAppsTable(results)
	return nil
}

// queryAppKPI fetches social metrics for a single app from PDS graph + health endpoint.
func queryAppKPI(client *http.Client, app discoveredApp, pdsURL string) appKPIStatus {
	s := appKPIStatus{
		Nanoid: app.Nanoid,
		Name:   app.Name,
		DID:    fmt.Sprintf("did:web:%s.etzhayyim.com", app.Nanoid),
		UIType: app.UIType,
	}

	// 1. Health check
	base := "https://" + app.Nanoid + ".etzhayyim.com"
	resp, err := client.Get(base + "/health")
	if err == nil {
		s.HealthOK = resp.StatusCode == 200
		resp.Body.Close()
	}

	// 2. Query RisingWave directly for social metrics.
	did := s.DID
	// vertex_post is not present in P10v2 (posts live in edge tables only);
	// Post/Like/Repost counts against the repo would require `vertex_profile_fragment`
	// joins that the current schema does not support. Report 0 and let KPI
	// scoring reflect the absent data signal.
	s.Posts = 0
	s.Likes = 0
	s.Reposts = 0
	s.Records = 0
	stats := readActorSocialStats(did)
	repoStats := readActorRepoStats(did)

	// Followers: exact DID count + path-subDID descendants.
	s.Followers = stats.Followers + repoStats.DescendantFollowers

	// Following: exact DID count + path-subDID descendants.
	s.Following = stats.Following + repoStats.DescendantFollowing

	// Exact post count also comes from the actor social MV.
	s.Posts = stats.Posts

	// Sub-DIDs (path-based child DIDs)
	s.SubDIDs = repoStats.DescendantSubDIDs

	// KPI score: weighted composite
	s.KPIScore = computeKPI(s)

	return s
}

// rwCountInt runs a COUNT(*) SQL statement against RisingWave and returns the
// single-row integer result. Returns 0 on any error (connection, parse, empty).
func rwCountInt(sql string, args ...any) int {
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	p, err := db.Pool(ctx)
	if err != nil {
		return 0
	}
	var cnt int64
	if err := p.QueryRow(ctx, sql, args...).Scan(&cnt); err != nil {
		return 0
	}
	return int(cnt)
}

// computeKPI calculates a weighted KPI score (0-100).
func computeKPI(s appKPIStatus) float64 {
	// Scoring weights:
	//   Posts:     30% (engagement output)
	//   Likes:     20% (engagement received)
	//   Followers: 20% (audience)
	//   Records:   15% (domain data)
	//   SubDIDs:   10% (multi-DID utilization)
	//   Health:     5% (operational)
	score := 0.0

	// Posts: 0=0, 1-9=30, 10-49=60, 50+=100
	score += 0.30 * tierScore(s.Posts, 1, 10, 50)

	// Likes: 0=0, 1-4=30, 5-19=60, 20+=100
	score += 0.20 * tierScore(s.Likes, 1, 5, 20)

	// Followers: 0=0, 1-4=30, 5-19=60, 20+=100
	score += 0.20 * tierScore(s.Followers, 1, 5, 20)

	// Records: 0=0, 1-9=30, 10-99=60, 100+=100
	score += 0.15 * tierScore(s.Records, 1, 10, 100)

	// SubDIDs: 0=0, 1=50, 2+=100
	score += 0.10 * tierScore(s.SubDIDs, 1, 2, 5)

	// Health: binary
	if s.HealthOK {
		score += 0.05 * 100
	}

	return score
}

func tierScore(val, t1, t2, t3 int) float64 {
	if val >= t3 {
		return 100
	}
	if val >= t2 {
		return 60
	}
	if val >= t1 {
		return 30
	}
	return 0
}

func sortAppsResults(results []appKPIStatus, sortBy string) {
	sort.Slice(results, func(i, j int) bool {
		switch sortBy {
		case "posts":
			return results[i].Posts > results[j].Posts
		case "likes":
			return results[i].Likes > results[j].Likes
		case "followers":
			return results[i].Followers > results[j].Followers
		case "records":
			return results[i].Records > results[j].Records
		case "name":
			return results[i].Name < results[j].Name
		default: // kpi
			return results[i].KPIScore > results[j].KPIScore
		}
	})
}

func printAppsTable(results []appKPIStatus) {
	w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)

	totalPosts := 0
	totalLikes := 0
	totalFollowers := 0
	totalRecords := 0
	healthy := 0
	for _, r := range results {
		totalPosts += r.Posts
		totalLikes += r.Likes
		totalFollowers += r.Followers
		totalRecords += r.Records
		if r.HealthOK {
			healthy++
		}
	}

	fmt.Fprintf(w, "\nApp KPI Dashboard (%d apps)\n\n", len(results))
	fmt.Fprintln(w, "KPI\tNanoid\tName\tHealth\tPosts\tLikes\tReposts\tFollowers\tFollowing\tRecords\tSubDIDs")
	fmt.Fprintln(w, "---\t--------\t--------------------\t------\t-----\t-----\t-------\t---------\t---------\t-------\t-------")

	for _, r := range results {
		health := "✗"
		if r.HealthOK {
			health = "✓"
		}

		grade := kpiGrade(r.KPIScore)

		fmt.Fprintf(w, "%s\t%s\t%s\t%s\t%d\t%d\t%d\t%d\t%d\t%d\t%d\n",
			grade,
			r.Nanoid,
			truncateStr(r.Name, 20),
			health,
			r.Posts,
			r.Likes,
			r.Reposts,
			r.Followers,
			r.Following,
			r.Records,
			r.SubDIDs,
		)
	}

	fmt.Fprintln(w)
	fmt.Fprintf(w, "Totals: %d posts, %d likes, %d followers, %d records, %d/%d healthy\n",
		totalPosts, totalLikes, totalFollowers, totalRecords, healthy, len(results))
	w.Flush()
}

func kpiGrade(score float64) string {
	switch {
	case score >= 80:
		return "S"
	case score >= 60:
		return "A"
	case score >= 40:
		return "B"
	case score >= 20:
		return "C"
	default:
		return "D"
	}
}
