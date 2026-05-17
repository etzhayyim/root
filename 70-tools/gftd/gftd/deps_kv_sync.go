// deps kv-sync — populate Cloudflare KV namespace `DEPS_REGISTRY` with
// `actor:{name}` keys serialized from deps.toml [[mitama_actors]].
//
// Used by:
//   - PDS handlers/plc/index.ts `lookupActor()` (ADR-0014 Phase 5)
//   - any Worker that needs runtime actor lookup without re-parsing deps.toml
//
// Schema per key:
//   key   = "actor:{name}"
//   value = JSON { name, did, handle, nanoid?, legacyDidWeb?, description? }
//
// Plus aggregate index:
//   key   = "actors:index"
//   value = JSON [name, name, ...] (sorted)

package main

import (
	"bytes"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"sort"
	"strings"
	"time"
)

type kvActorRecord struct {
	Name         string `json:"name"`
	DID          string `json:"did"`
	Handle       string `json:"handle"`
	Nanoid       string `json:"nanoid,omitempty"`
	LegacyDidWeb string `json:"legacyDidWeb,omitempty"`
	Description  string `json:"description,omitempty"`
}

type cfKVBulkEntry struct {
	Key   string `json:"key"`
	Value string `json:"value"`
}

type kvSyncPlanItem struct {
	Action string `json:"action"` // "put" | "delete" | "keep"
	Key    string `json:"key"`
}

func runDepsKVSync(args []string) error {
	fs := flag.NewFlagSet("deps kv-sync", flag.ExitOnError)
	apply := fs.Bool("apply", false, "PUT keys to Cloudflare KV (default: dry-run)")
	jsonOut := fs.Bool("json", false, "emit JSON plan")
	noCF := fs.Bool("no-cf", false, "skip Cloudflare API (print desired KV bulk payload only, offline mode)")
	diff := fs.Bool("diff", false, "fetch existing KV state and report add/update/delete plan vs deps.toml")
	depsPath := fs.String("deps", "deps.toml", "path to deps.toml")
	accountID := fs.String("account-id", "", "Cloudflare account id (CF_ACCOUNT_ID env fallback)")
	namespaceID := fs.String("namespace-id", "", "KV namespace id for DEPS_REGISTRY (CF_DEPS_REGISTRY_KV_ID env fallback)")
	_ = fs.Parse(args)

	actors, _, err := parseIdentifierTables(*depsPath)
	if err != nil {
		return fmt.Errorf("parse %s: %w", *depsPath, err)
	}
	if len(actors) == 0 {
		return fmt.Errorf("no [[mitama_actors]] in %s", *depsPath)
	}

	desired := buildKVActorRecords(actors)

	if *noCF {
		if *jsonOut {
			enc := json.NewEncoder(os.Stdout)
			enc.SetIndent("", "  ")
			return enc.Encode(map[string]any{
				"mode":          "offline",
				"actors":        len(actors),
				"desired_count": len(desired),
				"desired":       desired,
			})
		}
		fmt.Printf("gftd deps kv-sync — offline (no Cloudflare API)\n")
		fmt.Printf("================================================\n")
		fmt.Printf("actors:        %d\n", len(actors))
		fmt.Printf("desired KV keys: %d  (%d actors + 1 actors:index)\n\n", len(desired), len(actors))
		for _, e := range desired[:min(15, len(desired))] {
			val := e.Value
			if len(val) > 80 {
				val = val[:80] + "…"
			}
			fmt.Printf("  PUT  %-28s  %s\n", e.Key, val)
		}
		if len(desired) > 15 {
			fmt.Printf("  ... (%d more)\n", len(desired)-15)
		}
		return nil
	}

	// Resolve CF credentials
	token, _ := resolveCloudflareToken()
	if token == "" {
		return fmt.Errorf("no Cloudflare API token (CLOUDFLARE_API_TOKEN, CF_API_TOKEN, or wrangler OAuth)")
	}
	acct := *accountID
	if acct == "" {
		acct = strings.TrimSpace(os.Getenv("CF_ACCOUNT_ID"))
	}
	if acct == "" {
		return fmt.Errorf("--account-id required (or set CF_ACCOUNT_ID)")
	}
	ns := *namespaceID
	if ns == "" {
		ns = strings.TrimSpace(os.Getenv("CF_DEPS_REGISTRY_KV_ID"))
	}
	if ns == "" {
		return fmt.Errorf("--namespace-id required (or set CF_DEPS_REGISTRY_KV_ID)")
	}

	// --diff: fetch existing KV state and report add/update/delete plan
	if *diff {
		existing, err := cfKVList(token, acct, ns)
		if err != nil {
			return fmt.Errorf("list KV: %w", err)
		}
		plan := diffKVRecords(desired, existing)
		actionCount := map[string]int{}
		for _, p := range plan {
			actionCount[p.Action]++
		}
		if *jsonOut {
			enc := json.NewEncoder(os.Stdout)
			enc.SetIndent("", "  ")
			return enc.Encode(map[string]any{
				"account":     acct,
				"namespace":   ns,
				"existing":    len(existing),
				"desired":     len(desired),
				"by_action":   actionCount,
				"plan":        plan,
			})
		}
		fmt.Printf("gftd deps kv-sync --diff\n")
		fmt.Printf("=========================\n")
		fmt.Printf("account:  %s\n", acct)
		fmt.Printf("KV ns:    %s\n", ns)
		fmt.Printf("existing: %d keys  desired: %d\n", len(existing), len(desired))
		fmt.Printf("plan: add=%d update=%d delete=%d keep=%d\n\n",
			actionCount["add"], actionCount["update"], actionCount["delete"], actionCount["keep"])
		for _, p := range plan {
			if p.Action == "keep" {
				continue
			}
			fmt.Printf("  %-6s  %s\n", strings.ToUpper(p.Action), p.Key)
		}
		return nil
	}

	if !*apply {
		// Dry-run: print plan
		fmt.Printf("gftd deps kv-sync — dry-run\n")
		fmt.Printf("===========================\n")
		fmt.Printf("account: %s\n", acct)
		fmt.Printf("KV ns:   %s\n", ns)
		fmt.Printf("actors:  %d\n", len(actors))
		fmt.Printf("desired: %d KV keys (would PUT)\n", len(desired))
		fmt.Printf("\nUse --apply to execute, or --diff to see existing-vs-desired plan.\n")
		return nil
	}

	// Apply: bulk PUT
	fmt.Printf("Applying KV bulk PUT (%d keys)...\n", len(desired))
	if err := cfKVBulkPut(token, acct, ns, desired); err != nil {
		return fmt.Errorf("bulk PUT: %w", err)
	}
	fmt.Printf("✓ DEPS_REGISTRY KV synced: %d keys\n", len(desired))
	return nil
}

// cfKVList — list keys (paginated) under a KV namespace, matching the actor: + actors: prefixes.
func cfKVList(token, accountID, namespaceID string) (map[string]bool, error) {
	out := map[string]bool{}
	cursor := ""
	for {
		u := fmt.Sprintf(
			"https://api.cloudflare.com/client/v4/accounts/%s/storage/kv/namespaces/%s/keys?limit=1000",
			url.PathEscape(accountID), url.PathEscape(namespaceID),
		)
		if cursor != "" {
			u += "&cursor=" + url.QueryEscape(cursor)
		}
		req, _ := http.NewRequest(http.MethodGet, u, nil)
		req.Header.Set("Authorization", "Bearer "+token)
		client := &http.Client{Timeout: 30 * time.Second}
		resp, err := client.Do(req)
		if err != nil {
			return nil, err
		}
		var body struct {
			Success    bool `json:"success"`
			Result     []struct {
				Name string `json:"name"`
			} `json:"result"`
			ResultInfo struct {
				Cursor string `json:"cursor"`
			} `json:"result_info"`
		}
		if err := json.NewDecoder(resp.Body).Decode(&body); err != nil {
			resp.Body.Close()
			return nil, err
		}
		resp.Body.Close()
		for _, k := range body.Result {
			if strings.HasPrefix(k.Name, "actor:") || strings.HasPrefix(k.Name, "actors:") {
				out[k.Name] = true
			}
		}
		if body.ResultInfo.Cursor == "" {
			break
		}
		cursor = body.ResultInfo.Cursor
	}
	return out, nil
}

// diffKVRecords — compare desired entries against existing keys.
// Returns plan items: add (key not in KV), update (key exists, value differs — but we
// always treat as update without fetching values to avoid 92-roundtrip cost), delete
// (key in KV but not desired), keep (would only be set if we also fetched values).
//
// Approximation: every desired key with existing presence is reported as "update"
// (forcing PUT). Real keep/update split requires per-key value fetch (KV GET),
// which is expensive. The bulk PUT is idempotent so over-counting is safe.
func diffKVRecords(desired []cfKVBulkEntry, existing map[string]bool) []kvSyncPlanItem {
	desiredSet := make(map[string]bool, len(desired))
	plan := make([]kvSyncPlanItem, 0, len(desired))
	for _, e := range desired {
		desiredSet[e.Key] = true
		if existing[e.Key] {
			plan = append(plan, kvSyncPlanItem{Action: "update", Key: e.Key})
		} else {
			plan = append(plan, kvSyncPlanItem{Action: "add", Key: e.Key})
		}
	}
	// Orphan keys in KV but no longer in desired
	orphans := make([]string, 0)
	for k := range existing {
		if !desiredSet[k] {
			orphans = append(orphans, k)
		}
	}
	sort.Strings(orphans)
	for _, k := range orphans {
		plan = append(plan, kvSyncPlanItem{Action: "delete", Key: k})
	}
	return plan
}

// buildKVActorRecords — convert mitama_actors → KV bulk entries.
// Includes per-actor "actor:{name}" + aggregate "actors:index".
func buildKVActorRecords(actors []idActor) []cfKVBulkEntry {
	sorted := append([]idActor(nil), actors...)
	sort.Slice(sorted, func(i, j int) bool { return sorted[i].Name < sorted[j].Name })

	out := make([]cfKVBulkEntry, 0, len(sorted)+1)
	names := make([]string, 0, len(sorted))
	for _, a := range sorted {
		handle := a.Domain
		if handle == "" && len(a.Handles) > 0 {
			handle = a.Handles[0]
		}
		rec := kvActorRecord{
			Name:   a.Name,
			DID:    a.DID,
			Handle: handle,
			Nanoid: a.Nanoid,
		}
		body, err := json.Marshal(rec)
		if err != nil {
			continue
		}
		out = append(out, cfKVBulkEntry{Key: "actor:" + a.Name, Value: string(body)})
		names = append(names, a.Name)
	}
	idxBody, _ := json.Marshal(names)
	out = append(out, cfKVBulkEntry{Key: "actors:index", Value: string(idxBody)})
	return out
}

// cfKVBulkPut — POST /accounts/{acct}/storage/kv/namespaces/{ns}/bulk
// Cloudflare bulk PUT supports up to 10,000 entries per request, 100 MB body.
func cfKVBulkPut(token, accountID, namespaceID string, entries []cfKVBulkEntry) error {
	body, _ := json.Marshal(entries)
	u := fmt.Sprintf(
		"https://api.cloudflare.com/client/v4/accounts/%s/storage/kv/namespaces/%s/bulk",
		url.PathEscape(accountID), url.PathEscape(namespaceID),
	)
	req, _ := http.NewRequest(http.MethodPut, u, bytes.NewReader(body))
	req.Header.Set("Authorization", "Bearer "+token)
	req.Header.Set("Content-Type", "application/json")
	client := &http.Client{Timeout: 60 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	respBody, _ := io.ReadAll(resp.Body)
	if resp.StatusCode >= 400 {
		return fmt.Errorf("cf api %d: %s", resp.StatusCode, string(respBody))
	}
	return nil
}

// (uses min from dodaf.go)
