package main

import (
	"bufio"
	"bytes"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"sync"
	"sync/atomic"
	"time"
)

// runSetProfiles scans all wasm component directories, extracts app metadata
// (nanoid, name, description) from main.go / magatama.jsonld, and calls
// ai.gftd.pds.putProfile on the active PDS endpoint to set AT Protocol profiles.
func runSetProfiles(args []string) error {
	fs := flag.NewFlagSet("set-profiles", flag.ExitOnError)
	dirFlag := fs.String("dir", "", "Parent directory containing wasm component subdirectories")
	concurrency := fs.Int("concurrency", 20, "Parallel profile-setting workers")
	dryRun := fs.Bool("dry-run", false, "Print profiles without setting them")
	pdsURL := fs.String("pds-url", defaultPDSURL, "PDS endpoint URL")
	filter := fs.String("filter", "", "Glob pattern to filter app dirs")
	fs.Parse(args)

	gitRoot, err := findGitRoot(".")
	if err != nil {
		return fmt.Errorf("cannot find git root: %w", err)
	}

	// Determine search directories
	var searchDirs []string
	if *dirFlag != "" {
		searchDirs = append(searchDirs, *dirFlag)
	} else {
		// Scan all project wasm directories
		projectsDir := filepath.Join(gitRoot, "projects")
		entries, err := os.ReadDir(projectsDir)
		if err != nil {
			return fmt.Errorf("cannot read projects: %w", err)
		}
		for _, e := range entries {
			if !e.IsDir() {
				continue
			}
			wasmDir := filepath.Join(projectsDir, e.Name(), "wasm")
			if info, err := os.Stat(wasmDir); err == nil && info.IsDir() {
				searchDirs = append(searchDirs, wasmDir)
			}
		}
	}

	// Collect all apps
	type appProfile struct {
		Nanoid      string `json:"nanoid"`
		DID         string `json:"did"`
		DisplayName string `json:"displayName"`
		Description string `json:"description"`
		SpaceName   string `json:"spaceName,omitempty"`
	}

	var profiles []appProfile

	for _, dir := range searchDirs {
		entries, err := os.ReadDir(dir)
		if err != nil {
			continue
		}
		for _, e := range entries {
			if !e.IsDir() {
				continue
			}
			appDir := filepath.Join(dir, e.Name())

			if *filter != "" {
				matched, _ := filepath.Match(*filter, e.Name())
				if !matched {
					continue
				}
			}

			p := extractAppProfile(appDir)
			if p.Nanoid == "" {
				continue
			}
			profiles = append(profiles, p)
		}
	}

	if len(profiles) == 0 {
		return fmt.Errorf("no apps found")
	}

	fmt.Fprintf(os.Stderr, "==> Found %d apps with profiles\n", len(profiles))

	if *dryRun {
		for _, p := range profiles {
			fmt.Printf("%-12s %-40s %s\n", p.Nanoid, p.DisplayName, truncate(p.Description, 60))
		}
		return nil
	}

	// Set profiles in parallel
	var (
		wg      sync.WaitGroup
		sem     = make(chan struct{}, *concurrency)
		success int64
		failed  int64
		skipped int64
	)

	client := &http.Client{Timeout: 30 * time.Second}

	for _, p := range profiles {
		wg.Add(1)
		sem <- struct{}{}
		go func(p appProfile) {
			defer wg.Done()
			defer func() { <-sem }()

			if p.DisplayName == "" && p.Description == "" {
				atomic.AddInt64(&skipped, 1)
				return
			}

			var lastErr error
			for attempt := 0; attempt < 3; attempt++ {
				lastErr = callPDSPutProfile(client, *pdsURL, p)
				if lastErr == nil {
					break
				}
				time.Sleep(time.Duration(attempt+1) * 2 * time.Second)
			}
			if lastErr != nil {
				fmt.Fprintf(os.Stderr, "  FAIL %s: %v\n", p.Nanoid, lastErr)
				atomic.AddInt64(&failed, 1)
				return
			}
			fmt.Fprintf(os.Stderr, "  OK   %s → %s\n", p.Nanoid, p.DisplayName)
			atomic.AddInt64(&success, 1)
		}(p)
	}

	wg.Wait()

	fmt.Fprintf(os.Stderr, "\n==> Profiles set: %d success, %d failed, %d skipped (total: %d)\n",
		success, failed, skipped, len(profiles))

	return nil
}

// extractAppProfile reads nanoid/name/description from magatama.jsonld and main.go.
func extractAppProfile(dir string) struct {
	Nanoid      string `json:"nanoid"`
	DID         string `json:"did"`
	DisplayName string `json:"displayName"`
	Description string `json:"description"`
	SpaceName   string `json:"spaceName,omitempty"`
} {
	type result = struct {
		Nanoid      string `json:"nanoid"`
		DID         string `json:"did"`
		DisplayName string `json:"displayName"`
		Description string `json:"description"`
		SpaceName   string `json:"spaceName,omitempty"`
	}

	var r result

	// Try magatama.jsonld first
	cfg, _ := readMagatamaJSONLD(dir)
	if cfg != nil {
		r.Nanoid = cfg.Nanoid
		if strings.HasPrefix(strings.TrimSpace(cfg.ID), "did:web:") {
			r.DID = strings.TrimSpace(cfg.ID)
		}
		if cfg.Profile != nil {
			if strings.TrimSpace(cfg.Profile.DisplayName) != "" {
				r.DisplayName = strings.TrimSpace(cfg.Profile.DisplayName)
			}
			if strings.TrimSpace(cfg.Profile.Description) != "" {
				r.Description = strings.TrimSpace(cfg.Profile.Description)
			}
		}
		if cfg.Space != nil {
			r.SpaceName = cfg.Space.Name
			if strings.TrimSpace(r.Description) == "" {
				r.Description = cfg.Space.Description
			}
		}
	}

	// Extract from main.go (has more detailed Name/Description)
	goName, goDesc := extractNameDescFromMainGo(dir)
	if goName != "" {
		r.DisplayName = goName
	}
	if goDesc != "" {
		r.Description = goDesc
	}

	// Fallback display name
	if r.DisplayName == "" && r.SpaceName != "" {
		r.DisplayName = r.SpaceName
	}
	if r.DisplayName == "" && cfg != nil {
		r.DisplayName = cfg.Name
	}

	// Nanoid fallback
	if r.Nanoid == "" {
		r.Nanoid = extractNanoidFromAppTS(dir)
	}

	if r.DID == "" && r.Nanoid != "" {
		r.DID = "did:web:" + r.Nanoid + ".etzhayyim.com"
	}

	return r
}

var (
	goNameRe = regexp.MustCompile(`Name:\s*"([^"]*)"`)
	goDescRe = regexp.MustCompile(`Description:\s*"([^"]*)"`)
)

func extractNameDescFromMainGo(dir string) (name, desc string) {
	f, err := os.Open(filepath.Join(dir, "main.go"))
	if err != nil {
		return "", ""
	}
	defer f.Close()

	scanner := bufio.NewScanner(f)
	buf := make([]byte, 0, 64*1024)
	scanner.Buffer(buf, 256*1024)
	for scanner.Scan() {
		line := scanner.Text()
		if m := goNameRe.FindStringSubmatch(line); len(m) == 2 && name == "" {
			name = m[1]
		}
		if m := goDescRe.FindStringSubmatch(line); len(m) == 2 && desc == "" {
			desc = m[1]
		}
		if name != "" && desc != "" {
			break
		}
	}
	return name, desc
}

func callPDSPutProfile(client *http.Client, pdsURL string, p struct {
	Nanoid      string `json:"nanoid"`
	DID         string `json:"did"`
	DisplayName string `json:"displayName"`
	Description string `json:"description"`
	SpaceName   string `json:"spaceName,omitempty"`
}) error {
	body := map[string]any{
		"repo":        p.DID,
		"displayName": p.DisplayName,
		"description": p.Description,
		"$type":       "app.bsky.actor.profile",
	}
	bodyJSON, _ := json.Marshal(body)

	// XRPC path — PDS GftdPutProfile handler calls comAtprotoRepoCreateRecord(env, repo, "app.bsky.actor.profile", body)
	url := strings.TrimRight(pdsURL, "/") + "/xrpc/ai.gftd.pds.putProfile"
	req, err := http.NewRequest("POST", url, bytes.NewReader(bodyJSON))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")

	// Resolve auth token: Clerk JWT > internal token
	token := resolveGFTDToken()
	if token != "" {
		req.Header.Set("Authorization", "Bearer "+token)
	}

	resp, err := client.Do(req)
	if err != nil {
		return fmt.Errorf("HTTP error: %w", err)
	}
	defer resp.Body.Close()
	respBody, _ := io.ReadAll(resp.Body)

	if resp.StatusCode >= 300 {
		return fmt.Errorf("HTTP %d: %s", resp.StatusCode, string(respBody))
	}

	return nil
}

func truncate(s string, max int) string {
	if len(s) <= max {
		return s
	}
	return s[:max-3] + "..."
}
