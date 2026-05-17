package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"
	"time"

	"github.com/etzhayyim/root/70-tools/gftd/gftd/db"
)

// didRegistrationStatus holds the result of checking a DID's registration completeness.
type didRegistrationStatus struct {
	Nanoid      string
	DID         string
	DisplayName string
	Description string

	// Profile
	HasProfile    bool
	ProfileName   string
	ProfileDesc   string
	ProfileSensit string

	// App
	HasApp       bool
	AppPerformer string
	AppDeployAt  string

	// Tools (ActorCapability)
	ToolCount int
	ToolNames []string

	// Governance (GovernanceManifest)
	HasGovernance bool
	GovPolicies   int

	// Graph (connections)
	FollowCount   int
	FollowerCount int
	DepsCount     int

	// DIDs (path-based)
	PathDIDCount int

	// Errors
	Errors []string
}

func runMonitorDID(args []string) error {
	// Extract positional arg before flag parsing (Go flag stops at first non-flag)
	var positional string
	var flagArgs []string
	for _, a := range args {
		if strings.HasPrefix(a, "-") {
			flagArgs = append(flagArgs, a)
		} else if positional == "" {
			positional = a
		}
	}

	fs := flag.NewFlagSet("monitor did", flag.ExitOnError)
	nanoid := fs.String("nanoid", "", "nanoid to check (required)")
	did := fs.String("did", "", "full DID to check (alternative to nanoid)")
	pdsURL := fs.String("pds", "", "PDS base URL (default: https://mod.etzhayyim.com)")
	jsonOut := fs.Bool("json", false, "JSON output")
	fs.Parse(flagArgs)

	if *nanoid == "" && *did == "" && positional != "" {
		if strings.HasPrefix(positional, "did:") {
			*did = positional
		} else {
			*nanoid = positional
		}
	}

	if *nanoid == "" && *did == "" {
		fmt.Fprintln(os.Stderr, "Usage: gftd monitor did <nanoid|did> [--json]")
		fmt.Fprintln(os.Stderr, "  gftd monitor did g0vhti01")
		fmt.Fprintln(os.Stderr, "  gftd monitor did did:web:g0vhti01.etzhayyim.com")
		return nil
	}

	targetDID := *did
	targetNanoid := *nanoid
	autoDIDFromNanoid := targetDID == "" && targetNanoid != ""
	if targetDID == "" {
		targetDID = "did:web:" + targetNanoid + ".etzhayyim.com"
	}
	if targetNanoid == "" {
		// Extract nanoid from DID: did:web:xxx.etzhayyim.com -> xxx
		parts := strings.Split(targetDID, ":")
		if len(parts) >= 3 {
			host := parts[2]
			targetNanoid = strings.TrimSuffix(host, ".etzhayyim.com")
		}
	}

	base := defaultPDSURL
	if *pdsURL != "" {
		base = *pdsURL
	} else if env := os.Getenv("GFTD_PDS_URL"); env != "" {
		base = env
	}

	token := resolveGFTDToken()
	if token == "" {
		return fmt.Errorf("not authenticated. Run 'gftd auth login' first")
	}
	client := &http.Client{Timeout: 45 * time.Second}

	// Resolve canonical DID from graph when only nanoid was given.
	// Example: uqpel6i6 -> did:web:maps.etzhayyim.com (not did:web:uqpel6i6.etzhayyim.com)
	if autoDIDFromNanoid {
		if resolved := resolveCanonicalDIDByNanoid(client, base, token, targetNanoid); resolved != "" {
			targetDID = resolved
		}
	}

	status := didRegistrationStatus{
		Nanoid: targetNanoid,
		DID:    targetDID,
	}

	// 1. Profile + social stats via XRPC (same as yoro)
	if err := queryProfileXRPC(client, base, targetDID, &status); err != nil {
		if fbErr := queryProfileFromGraph(client, base, token, targetDID, &status); fbErr != nil {
			status.Errors = append(status.Errors, "profile: "+err.Error())
		}
	}

	// 2. App meta via /_app/meta
	queryAppMeta(client, targetNanoid, &status)

	// 3. Tools (ActorCapability) via Sql
	queryTools(client, base, token, targetNanoid, targetDID, &status)

	// 4. Governance via Sql
	queryGovernance(client, base, token, targetNanoid, targetDID, &status)

	// 5. Deps via Sql
	queryDeps(client, base, token, targetNanoid, &status)

	// 6. Path-based DIDs via Sql
	queryPathDIDs(client, base, token, targetDID, &status)

	if *jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(status)
	}

	printDIDStatus(status)
	return nil
}

// rwQueryRows runs a SQL statement against RisingWave and returns the result
// as [][]any (column positions preserved). Replacement for the archived
// `sqlQuery` helper. Accepts positional `$1,$2,...` parameters.
func rwQueryRows(sql string, args ...any) ([][]any, error) {
	ctx, cancel := context.WithTimeout(context.Background(), 60*time.Second)
	defer cancel()
	res, err := db.RawQuery(ctx, sql, args...)
	if err != nil {
		return nil, err
	}
	rows := make([][]any, 0, len(res.Rows))
	for _, m := range res.Rows {
		row := make([]any, len(res.Columns))
		for i, c := range res.Columns {
			row[i] = m[c]
		}
		rows = append(rows, row)
	}
	return rows, nil
}

// queryProfileXRPC uses the public XRPC getProfile endpoint (same as yoro).
func queryProfileXRPC(client *http.Client, base, did string, s *didRegistrationStatus) error {
	url := base + "/xrpc/app.bsky.actor.getProfile?actor=" + did
	resp, err := client.Get(url)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body)
	if resp.StatusCode != 200 {
		return fmt.Errorf("HTTP %d", resp.StatusCode)
	}
	var profile struct {
		DID            string `json:"did"`
		Handle         string `json:"handle"`
		DisplayName    string `json:"displayName"`
		Description    string `json:"description"`
		FollowersCount int    `json:"followersCount"`
		FollowsCount   int    `json:"followsCount"`
		PostsCount     int    `json:"postsCount"`
		Sensitivity    string `json:"sensitivity"`
	}
	if json.Unmarshal(body, &profile) != nil {
		return fmt.Errorf("invalid profile response")
	}
	// Profile exists if displayName is not just the handle default
	s.HasProfile = profile.DisplayName != "" && profile.DisplayName != profile.Handle
	s.ProfileName = profile.DisplayName
	s.ProfileDesc = profile.Description
	s.ProfileSensit = profile.Sensitivity
	s.FollowCount = profile.FollowsCount
	s.FollowerCount = profile.FollowersCount
	return nil
}

func resolveCanonicalDIDByNanoid(client *http.Client, base, token, nanoid string) string {
	_ = client
	_ = base
	_ = token
	if strings.TrimSpace(nanoid) == "" {
		return ""
	}
	queries := []string{
		`SELECT did FROM vertex_actor_manifest WHERE nanoid = $1 LIMIT 1`,
		`SELECT did FROM vertex_app WHERE nanoid = $1 LIMIT 1`,
	}
	for _, q := range queries {
		rows, err := rwQueryRows(q, nanoid)
		if err != nil || len(rows) == 0 || len(rows[0]) == 0 {
			continue
		}
		did := strings.TrimSpace(fmt.Sprint(rows[0][0]))
		if strings.HasPrefix(did, "did:") {
			return did
		}
	}
	return ""
}

func queryProfileFromGraph(client *http.Client, base, token, did string, s *didRegistrationStatus) error {
	_ = client
	_ = base
	_ = token
	rows, err := rwQueryRows(
		`SELECT display_name, description, sensitivity, handle, NULL::varchar AS val FROM vertex_profile WHERE repo = $1 LIMIT 1`,
		did)
	if err != nil {
		return err
	}
	if len(rows) == 0 {
		return fmt.Errorf("not found")
	}
	row := rows[0]
	get := func(i int) string {
		if i < 0 || i >= len(row) {
			return ""
		}
		v := strings.TrimSpace(fmt.Sprint(row[i]))
		if v == "<nil>" {
			return ""
		}
		return v
	}
	displayName := get(0)
	description := get(1)
	sensitivity := get(2)
	handle := get(3)
	if val := get(4); val != "" {
		var obj map[string]any
		if json.Unmarshal([]byte(val), &obj) == nil {
			if displayName == "" {
				displayName = strings.TrimSpace(fmt.Sprint(obj["displayName"]))
			}
			if description == "" {
				description = strings.TrimSpace(fmt.Sprint(obj["description"]))
			}
			if sensitivity == "" {
				sensitivity = strings.TrimSpace(fmt.Sprint(obj["sensitivity"]))
			}
		}
	}
	s.HasProfile = displayName != "" && displayName != handle
	s.ProfileName = displayName
	s.ProfileDesc = description
	s.ProfileSensit = sensitivity
	return nil
}

// queryAppMeta checks /_app/meta for app registration.
func queryAppMeta(client *http.Client, nanoid string, s *didRegistrationStatus) {
	url := "https://" + nanoid + ".etzhayyim.com/_app/meta"
	resp, err := client.Get(url)
	if err != nil {
		s.Errors = append(s.Errors, "meta: "+err.Error())
		return
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body)
	if resp.StatusCode != 200 {
		return
	}
	var meta struct {
		Nanoid    string `json:"nanoid"`
		Name      string `json:"name"`
		UI        string `json:"ui"`
		Version   string `json:"version"`
		DeployAt  string `json:"deploy_at"`
		DeploySHA string `json:"deploy_sha"`
	}
	if json.Unmarshal(body, &meta) == nil && meta.Nanoid != "" {
		s.HasApp = true
		if s.DisplayName == "" {
			s.DisplayName = meta.Name
		}
		s.AppDeployAt = meta.DeployAt
	}
}

func queryTools(client *http.Client, base, token, nanoid, did string, s *didRegistrationStatus) {
	_ = client
	_ = base
	_ = token
	queries := []struct {
		sql  string
		args []any
	}{
		{`SELECT name FROM vertex_capability WHERE did = $1 OR repo = $1 LIMIT 50`, []any{did}},
		{`SELECT name FROM vertex_capability WHERE repo LIKE '%' || $1 || '%' LIMIT 50`, []any{nanoid}},
	}
	var lastErr error
	for _, q := range queries {
		rows, err := rwQueryRows(q.sql, q.args...)
		if err != nil {
			lastErr = err
			continue
		}
		seen := map[string]struct{}{}
		for _, row := range rows {
			if len(row) == 0 {
				continue
			}
			name := strings.TrimSpace(fmt.Sprint(row[0]))
			if name == "" || name == "<nil>" {
				continue
			}
			if _, ok := seen[name]; ok {
				continue
			}
			seen[name] = struct{}{}
			s.ToolNames = append(s.ToolNames, name)
		}
		s.ToolCount = len(s.ToolNames)
		if len(s.ToolNames) > 0 {
			return
		}
	}
	if lastErr != nil {
		s.Errors = append(s.Errors, "tools: "+lastErr.Error())
	}
}

func queryGovernance(client *http.Client, base, token, nanoid, did string, s *didRegistrationStatus) {
	_ = client
	_ = base
	_ = token
	queries := []struct {
		sql  string
		args []any
	}{
		{`SELECT name FROM vertex_governance WHERE repo = $1 OR did = $1 LIMIT 50`, []any{did}},
		{`SELECT name FROM vertex_governance WHERE repo LIKE '%' || $1 || '%' LIMIT 50`, []any{nanoid}},
	}
	var lastErr error
	for _, q := range queries {
		rows, err := rwQueryRows(q.sql, q.args...)
		if err != nil {
			lastErr = err
			continue
		}
		names := map[string]struct{}{}
		for _, row := range rows {
			if len(row) == 0 {
				continue
			}
			name := strings.TrimSpace(fmt.Sprint(row[0]))
			if name == "" || name == "<nil>" {
				continue
			}
			names[name] = struct{}{}
		}
		if len(names) > 0 {
			s.HasGovernance = true
			s.GovPolicies = len(names)
			return
		}
	}
	if lastErr != nil {
		s.Errors = append(s.Errors, "governance: "+lastErr.Error())
	}
}

func queryFollows(client *http.Client, base, token, did string, s *didRegistrationStatus) {
	_ = client
	_ = base
	_ = token
	stats := readActorSocialStats(did)
	s.FollowCount = stats.Following
	s.FollowerCount = stats.Followers
}

func queryDeps(client *http.Client, base, token, nanoid string, s *didRegistrationStatus) {
	_ = client
	_ = base
	_ = token
	// edge_depends_on is not present in P10v2; dep count is best-effort 0.
	_ = nanoid
	s.DepsCount = 0
}

func queryPathDIDs(client *http.Client, base, token, did string, s *didRegistrationStatus) {
	_ = client
	_ = base
	_ = token
	if rows, err := rwQueryRows(`SELECT COUNT(*)::bigint FROM vertex_diddocument WHERE controller = $1`, did); err == nil && len(rows) > 0 && len(rows[0]) > 0 {
		s.PathDIDCount = int(toInt64FromAny(rows[0][0]))
	}
}

func printDIDStatus(s didRegistrationStatus) {
	check := func(ok bool) string {
		if ok {
			return "✓"
		}
		return "✗"
	}
	countCheck := func(n int) string {
		if n > 0 {
			return fmt.Sprintf("✓ %d", n)
		}
		return "✗ 0"
	}

	fmt.Printf("\n  DID Registration Monitor\n")
	fmt.Printf("  ========================\n\n")
	fmt.Printf("  Nanoid:  %s\n", s.Nanoid)
	fmt.Printf("  DID:     %s\n\n", s.DID)

	// Profile
	fmt.Printf("  %-20s %s\n", "Profile", check(s.HasProfile))
	if s.HasProfile {
		fmt.Printf("    %-18s %s\n", "displayName", displayOrMissing(s.ProfileName))
		fmt.Printf("    %-18s %s\n", "description", truncateStrMon(displayOrMissing(s.ProfileDesc), 60))
		if s.ProfileSensit != "" {
			fmt.Printf("    %-18s %s\n", "sensitivity", s.ProfileSensit)
		}
	}

	// App
	fmt.Printf("  %-20s %s\n", "App", check(s.HasApp))
	if s.HasApp {
		fmt.Printf("    %-18s %s\n", "displayName", displayOrMissing(s.DisplayName))
		fmt.Printf("    %-18s %s\n", "performerType", displayOrMissing(s.AppPerformer))
		if s.AppDeployAt != "" {
			fmt.Printf("    %-18s %s\n", "deploy_at", s.AppDeployAt)
		}
	}

	// Tools
	fmt.Printf("  %-20s %s\n", "Tools", countCheck(s.ToolCount))
	if s.ToolCount > 0 {
		limit := s.ToolCount
		if limit > 10 {
			limit = 10
		}
		for _, name := range s.ToolNames[:limit] {
			fmt.Printf("    - %s\n", name)
		}
		if s.ToolCount > 10 {
			fmt.Printf("    ... +%d more\n", s.ToolCount-10)
		}
	}

	// Governance
	fmt.Printf("  %-20s %s\n", "Governance", check(s.HasGovernance))
	if s.HasGovernance {
		fmt.Printf("    %-18s %d policies\n", "count", s.GovPolicies)
	}

	// Graph
	fmt.Printf("  %-20s %s\n", "Follows", countCheck(s.FollowCount))
	fmt.Printf("  %-20s %s\n", "Followers", countCheck(s.FollowerCount))
	fmt.Printf("  %-20s %s\n", "Deps", countCheck(s.DepsCount))
	fmt.Printf("  %-20s %s\n", "Path DIDs", countCheck(s.PathDIDCount))

	// Summary
	total := 7
	passed := 0
	if s.HasProfile {
		passed++
	}
	if s.HasApp {
		passed++
	}
	if s.ToolCount > 0 {
		passed++
	}
	if s.HasGovernance {
		passed++
	}
	if s.FollowCount > 0 {
		passed++
	}
	if s.FollowerCount > 0 {
		passed++
	}
	if s.DepsCount > 0 {
		passed++
	}

	fmt.Printf("\n  Score: %d/%d", passed, total)
	if passed == total {
		fmt.Printf(" (complete)\n")
	} else {
		fmt.Printf(" (%d missing)\n", total-passed)
	}

	// Diagnosis
	if !s.HasProfile && s.HasApp {
		fmt.Printf("\n  Diagnosis: /_app/meta OK but Profile missing in graph.\n")
		fmt.Printf("  → yata Container index likely empty (Container restart wiped Lance).\n")
		fmt.Printf("  → Fix: redeploy with `gftd deploy` to re-register profile.\n")
		fmt.Printf("  → If still empty: yata index rebuild from KV is needed.\n")
	}

	if len(s.Errors) > 0 {
		fmt.Printf("\n  Errors:\n")
		for _, e := range s.Errors {
			fmt.Printf("    ! %s\n", e)
		}
	}
	fmt.Println()
}

func displayOrMissing(s string) string {
	if s == "" {
		return "(empty)"
	}
	return s
}
