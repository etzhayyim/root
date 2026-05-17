// dns-sync — ADR-0013 Phase 3 tool: sync deps.toml [[mitama_actors]]
// + [[legacy_nanoids]] to Cloudflare DNS records.
//
// Records managed per actor:
//   {handle}.etzhayyim.com                A     → CF Worker anycast (default handled by wildcard)
//   _atproto.{handle}.etzhayyim.com       TXT   "did={did}"                 (AT Protocol handle verification)
//   {legacy_nanoid}.etzhayyim.com         CNAME {handle}.etzhayyim.com            (Phase 3 grace, 2026-10-01 削除予定)
//
// Only records matching the gftd-managed comment prefix are affected; manual
// records are preserved. Use --dry-run (default) to preview diff.

package main

import (
	"bufio"
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

const (
	dnsSyncCommentPrefix = "gftd:adr-0013:"
	dnsSyncTXTComment    = dnsSyncCommentPrefix + "atproto-verify"
	dnsSyncCNAMEComment  = dnsSyncCommentPrefix + "legacy-nanoid"
)

type cfZone struct {
	ID   string `json:"id"`
	Name string `json:"name"`
}

type cfDNSRecord struct {
	ID      string `json:"id,omitempty"`
	Type    string `json:"type"`
	Name    string `json:"name"`
	Content string `json:"content"`
	TTL     int    `json:"ttl,omitempty"`
	Proxied bool   `json:"proxied,omitempty"`
	Comment string `json:"comment,omitempty"`
}

type dnsSyncPlanItem struct {
	Action   string       `json:"action"` // "create" | "update" | "delete" | "keep"
	Record   cfDNSRecord  `json:"record"`
	Existing *cfDNSRecord `json:"existing,omitempty"`
	Reason   string       `json:"reason,omitempty"`
}

func runDNSSync(args []string) error {
	fs := flag.NewFlagSet("dns-sync", flag.ExitOnError)
	apply := fs.Bool("apply", false, "apply changes (default: dry-run)")
	jsonOut := fs.Bool("json", false, "emit JSON plan")
	zoneName := fs.String("zone-name", "etzhayyim.com", "Cloudflare zone name")
	depsPath := fs.String("deps", "deps.toml", "path to deps.toml")
	includeNanoid := fs.Bool("include-nanoid", true, "include legacy nanoid CNAMEs (Phase 3 grace)")
	includeTXT := fs.Bool("include-txt", true, "include _atproto TXT verification records")
	noCF := fs.Bool("no-cf", false, "skip Cloudflare API (print desired records only, offline mode)")
	emitMap := fs.String("emit-routing-map", "", "write routing-gateway TS map to PATH (50-infra/cloudflare/workers/routing-gateway/src/legacy-nanoid-map.ts) and exit. Also emits yoro mirror to 60-apps/ai-gftd-project-yoro/.../svelte/src/lib/server/legacy-nanoid-map.ts unless --no-yoro-mirror is set")
	noYoroMirror := fs.Bool("no-yoro-mirror", false, "skip emitting yoro mirror legacy-nanoid-map.ts when --emit-routing-map is used")
	yoroMirrorPath := fs.String("yoro-mirror-path", "60-apps/ai-gftd-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/lib/server/legacy-nanoid-map.ts", "yoro mirror output path (relative to cwd)")
	emitBindings := fs.String("populate-bindings", "", "patch wrangler.jsonc at PATH with WORKER_{HANDLE} Service Bindings (90 entries from [[mitama_actors]]) and exit")
	_ = fs.Parse(args)

	actors, legacies, err := parseIdentifierTables(*depsPath)
	if err != nil {
		return fmt.Errorf("parse %s: %w", *depsPath, err)
	}
	if len(actors) == 0 {
		return fmt.Errorf("no [[mitama_actors]] in %s", *depsPath)
	}

	// --emit-routing-map: short-circuit (deps.toml → routing-gateway TS map)
	if *emitMap != "" {
		ts := emitRoutingMapTS(legacies)
		if err := os.WriteFile(*emitMap, []byte(ts), 0o644); err != nil {
			return fmt.Errorf("write %s: %w", *emitMap, err)
		}
		fmt.Printf("✓ routing-gateway map written: %s (%d entries)\n", *emitMap, len(legacies))
		if !*noYoroMirror {
			yoroTS := emitYoroMirrorTS(legacies)
			if err := os.WriteFile(*yoroMirrorPath, []byte(yoroTS), 0o644); err != nil {
				return fmt.Errorf("write yoro mirror %s: %w", *yoroMirrorPath, err)
			}
			fmt.Printf("✓ yoro mirror written:        %s (%d entries)\n", *yoroMirrorPath, len(legacies))
		}
		return nil
	}

	// --populate-bindings: short-circuit (deps.toml → wrangler.jsonc Service Bindings)
	if *emitBindings != "" {
		patched, count, err := patchWranglerBindings(*emitBindings, actors)
		if err != nil {
			return fmt.Errorf("patch %s: %w", *emitBindings, err)
		}
		if err := os.WriteFile(*emitBindings, []byte(patched), 0o644); err != nil {
			return fmt.Errorf("write %s: %w", *emitBindings, err)
		}
		fmt.Printf("✓ wrangler.jsonc bindings updated: %s (%d Service Bindings)\n", *emitBindings, count)
		return nil
	}

	// Build desired record set from deps.toml
	desired := buildDesiredDNSRecords(actors, legacies, *includeTXT, *includeNanoid, *zoneName)

	// Offline mode: print desired records without CF API call
	if *noCF {
		if *jsonOut {
			// `actors` here = the count of actors that produce a DNS
			// record in this zone (i.e. handle ends with `.<zone>`).
			// Cross-zone handles (e.g. junkawasaki.com) and path-DID
			// shaped handles (e.g. jpn-state.etzhayyim.com:sashiosae) are
			// legitimately skipped by buildDesiredDNSRecords; reporting
			// the raw deps.toml count would make the CI invariant
			// `TXT == ACTORS` falsely fail.
			actorsInZone := 0
			for _, a := range actors {
				h := a.Domain
				if h == "" && len(a.Handles) > 0 {
					h = a.Handles[0]
				}
				if h != "" && strings.HasSuffix(h, "."+*zoneName) {
					actorsInZone++
				}
			}
			enc := json.NewEncoder(os.Stdout)
			enc.SetIndent("", "  ")
			return enc.Encode(map[string]any{
				"zone":            *zoneName,
				"mode":            "offline",
				"actors":          actorsInZone,
				"actors_total":    len(actors),
				"actors_in_zone":  actorsInZone,
				"actors_excluded": len(actors) - actorsInZone,
				"legacy":          len(legacies),
				"desired_count":   len(desired),
				"desired":         desired,
			})
		}
		fmt.Printf("gftd dns-sync — offline mode (no Cloudflare API)\n")
		fmt.Printf("================================================\n")
		fmt.Printf("zone:    %s\n", *zoneName)
		fmt.Printf("actors:  %d  legacy: %d  desired: %d\n\n", len(actors), len(legacies), len(desired))
		byType := map[string]int{}
		for _, r := range desired {
			byType[r.Type]++
		}
		fmt.Printf("Records by type: TXT=%d CNAME=%d A=%d\n\n", byType["TXT"], byType["CNAME"], byType["A"])
		for _, r := range desired {
			fmt.Printf("  %-6s  %-45s  %s\n", r.Type, r.Name, r.Content)
		}
		return nil
	}

	// Resolve CF credentials + zone
	token, tokenSrc := resolveCloudflareToken()
	if token == "" {
		return fmt.Errorf("no Cloudflare API token (CLOUDFLARE_API_TOKEN, CF_API_TOKEN, or wrangler OAuth)")
	}
	zoneID, err := dnsSyncResolveZone(token, *zoneName)
	if err != nil {
		return fmt.Errorf("resolve zone: %w", err)
	}

	// Fetch existing managed records
	existing, err := dnsSyncListManagedRecords(token, zoneID)
	if err != nil {
		return fmt.Errorf("list records: %w", err)
	}

	plan := diffDNSRecords(desired, existing)

	if *jsonOut {
		type report struct {
			Zone      string            `json:"zone"`
			TokenFrom string            `json:"token_from"`
			Actions   map[string]int    `json:"actions"`
			Plan      []dnsSyncPlanItem `json:"plan"`
			Apply     bool              `json:"apply"`
		}
		actions := map[string]int{}
		for _, p := range plan {
			actions[p.Action]++
		}
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(report{Zone: *zoneName, TokenFrom: tokenSrc, Actions: actions, Plan: plan, Apply: *apply})
	}

	// Text output
	fmt.Printf("gftd dns-sync — ADR-0013 Phase 3\n")
	fmt.Printf("=================================\n")
	fmt.Printf("zone:         %s (id=%s)\n", *zoneName, zoneID)
	fmt.Printf("token from:   %s\n", tokenSrc)
	fmt.Printf("actors:       %d\n", len(actors))
	fmt.Printf("legacy:       %d\n", len(legacies))
	fmt.Printf("desired recs: %d  existing managed: %d\n", len(desired), len(existing))
	fmt.Println()

	actions := map[string]int{}
	for _, p := range plan {
		actions[p.Action]++
	}
	fmt.Printf("plan: create=%d update=%d delete=%d keep=%d\n\n",
		actions["create"], actions["update"], actions["delete"], actions["keep"])

	// Group & print
	for _, kind := range []string{"create", "update", "delete"} {
		items := []dnsSyncPlanItem{}
		for _, p := range plan {
			if p.Action == kind {
				items = append(items, p)
			}
		}
		if len(items) == 0 {
			continue
		}
		fmt.Printf("── %s (%d)\n", strings.ToUpper(kind), len(items))
		for _, p := range items {
			fmt.Printf("  %-6s  %-40s  %s  %s\n", p.Record.Type, p.Record.Name, p.Record.Content, p.Reason)
		}
		fmt.Println()
	}

	if !*apply {
		fmt.Printf("dry-run: no changes applied. Use --apply to execute.\n")
		return nil
	}

	// Apply
	fmt.Printf("Applying %d changes...\n", actions["create"]+actions["update"]+actions["delete"])
	applied, failed := 0, 0
	for _, p := range plan {
		if p.Action == "keep" {
			continue
		}
		if err := dnsSyncApplyOne(token, zoneID, p); err != nil {
			fmt.Fprintf(os.Stderr, "  FAIL %s %s %s: %v\n", p.Action, p.Record.Type, p.Record.Name, err)
			failed++
			continue
		}
		fmt.Printf("  OK   %s %s %s\n", p.Action, p.Record.Type, p.Record.Name)
		applied++
		time.Sleep(50 * time.Millisecond) // gentle pacing vs CF rate limit
	}
	fmt.Printf("\napplied=%d failed=%d\n", applied, failed)
	if failed > 0 {
		return fmt.Errorf("%d operations failed", failed)
	}
	return nil
}

func buildDesiredDNSRecords(actors []idActor, legacies []idLegacy, includeTXT, includeNanoid bool, zoneName string) []cfDNSRecord {
	var recs []cfDNSRecord
	legacyByNanoid := map[string]idLegacy{}
	for _, l := range legacies {
		legacyByNanoid[l.Nanoid] = l
	}

	for _, a := range actors {
		handle := a.Domain
		if handle == "" && len(a.Handles) > 0 {
			handle = a.Handles[0]
		}
		if handle == "" || !strings.HasSuffix(handle, "."+zoneName) {
			continue
		}
		// _atproto TXT for handle verification
		if includeTXT && a.DID != "" {
			recs = append(recs, cfDNSRecord{
				Type:    "TXT",
				Name:    "_atproto." + handle,
				Content: fmt.Sprintf(`"did=%s"`, a.DID),
				TTL:     3600,
				Comment: dnsSyncTXTComment,
			})
		}
	}

	// Legacy nanoid CNAMEs for Phase 3 grace
	if includeNanoid {
		for _, l := range legacies {
			if l.Handle == "" || !strings.HasSuffix(l.Handle, "."+zoneName) {
				continue
			}
			name := l.Nanoid + "." + zoneName
			recs = append(recs, cfDNSRecord{
				Type:    "CNAME",
				Name:    name,
				Content: l.Handle,
				TTL:     3600,
				Proxied: true,
				Comment: dnsSyncCNAMEComment,
			})
		}
	}

	// Sort for stable diff
	sort.Slice(recs, func(i, j int) bool {
		if recs[i].Name != recs[j].Name {
			return recs[i].Name < recs[j].Name
		}
		return recs[i].Type < recs[j].Type
	})
	return recs
}

func diffDNSRecords(desired, existing []cfDNSRecord) []dnsSyncPlanItem {
	type key struct{ name, recType string }
	existingMap := map[key]cfDNSRecord{}
	for _, r := range existing {
		existingMap[key{r.Name, r.Type}] = r
	}

	var plan []dnsSyncPlanItem
	seen := map[key]bool{}

	for _, d := range desired {
		k := key{d.Name, d.Type}
		seen[k] = true
		if e, ok := existingMap[k]; ok {
			if e.Content == d.Content && e.Comment == d.Comment {
				plan = append(plan, dnsSyncPlanItem{Action: "keep", Record: d, Existing: &e})
			} else {
				d.ID = e.ID
				plan = append(plan, dnsSyncPlanItem{
					Action:   "update",
					Record:   d,
					Existing: &e,
					Reason:   fmt.Sprintf("content %q → %q", e.Content, d.Content),
				})
			}
		} else {
			plan = append(plan, dnsSyncPlanItem{Action: "create", Record: d, Reason: "missing"})
		}
	}

	// Records managed by gftd but no longer desired → delete
	for k, e := range existingMap {
		if seen[k] {
			continue
		}
		plan = append(plan, dnsSyncPlanItem{
			Action:   "delete",
			Record:   e,
			Existing: &e,
			Reason:   "orphan (not in deps.toml)",
		})
	}

	return plan
}

// ── Cloudflare API helpers ────────────────────────────────────

func dnsSyncResolveZone(token, zoneName string) (string, error) {
	u := "https://api.cloudflare.com/client/v4/zones?name=" + url.QueryEscape(zoneName)
	req, _ := http.NewRequest(http.MethodGet, u, nil)
	req.Header.Set("Authorization", "Bearer "+token)
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()
	var body struct {
		Success bool     `json:"success"`
		Result  []cfZone `json:"result"`
		Errors  []any    `json:"errors"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&body); err != nil {
		return "", err
	}
	if !body.Success || len(body.Result) == 0 {
		return "", fmt.Errorf("zone %q not found (errors=%v)", zoneName, body.Errors)
	}
	return body.Result[0].ID, nil
}

func dnsSyncListManagedRecords(token, zoneID string) ([]cfDNSRecord, error) {
	var all []cfDNSRecord
	page := 1
	for {
		u := fmt.Sprintf("https://api.cloudflare.com/client/v4/zones/%s/dns_records?per_page=1000&page=%d", zoneID, page)
		req, _ := http.NewRequest(http.MethodGet, u, nil)
		req.Header.Set("Authorization", "Bearer "+token)
		resp, err := http.DefaultClient.Do(req)
		if err != nil {
			return nil, err
		}
		var body struct {
			Success    bool          `json:"success"`
			Result     []cfDNSRecord `json:"result"`
			ResultInfo struct {
				Page       int `json:"page"`
				TotalPages int `json:"total_pages"`
			} `json:"result_info"`
		}
		if err := json.NewDecoder(resp.Body).Decode(&body); err != nil {
			resp.Body.Close()
			return nil, err
		}
		resp.Body.Close()
		for _, r := range body.Result {
			if strings.HasPrefix(r.Comment, dnsSyncCommentPrefix) {
				all = append(all, r)
			}
		}
		if body.ResultInfo.Page >= body.ResultInfo.TotalPages {
			break
		}
		page++
	}
	return all, nil
}

func dnsSyncApplyOne(token, zoneID string, p dnsSyncPlanItem) error {
	client := &http.Client{Timeout: 15 * time.Second}
	switch p.Action {
	case "create":
		body, _ := json.Marshal(p.Record)
		req, _ := http.NewRequest(http.MethodPost,
			fmt.Sprintf("https://api.cloudflare.com/client/v4/zones/%s/dns_records", zoneID),
			strings.NewReader(string(body)))
		req.Header.Set("Authorization", "Bearer "+token)
		req.Header.Set("Content-Type", "application/json")
		return dnsSyncDoRequest(client, req)
	case "update":
		body, _ := json.Marshal(p.Record)
		req, _ := http.NewRequest(http.MethodPatch,
			fmt.Sprintf("https://api.cloudflare.com/client/v4/zones/%s/dns_records/%s", zoneID, p.Record.ID),
			strings.NewReader(string(body)))
		req.Header.Set("Authorization", "Bearer "+token)
		req.Header.Set("Content-Type", "application/json")
		return dnsSyncDoRequest(client, req)
	case "delete":
		req, _ := http.NewRequest(http.MethodDelete,
			fmt.Sprintf("https://api.cloudflare.com/client/v4/zones/%s/dns_records/%s", zoneID, p.Record.ID),
			nil)
		req.Header.Set("Authorization", "Bearer "+token)
		return dnsSyncDoRequest(client, req)
	}
	return nil
}

func dnsSyncDoRequest(client *http.Client, req *http.Request) error {
	resp, err := client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 400 {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("cf api %d: %s", resp.StatusCode, string(body))
	}
	return nil
}

// emitRoutingMapTS — generate `legacy-nanoid-map.ts` content for routing-gateway.
// Sorted alphabetically by nanoid for deterministic output (CI diff stability).
func emitRoutingMapTS(legacies []idLegacy) string {
	sort.Slice(legacies, func(i, j int) bool { return legacies[i].Nanoid < legacies[j].Nanoid })
	var b strings.Builder
	b.WriteString("// legacy-nanoid-map.ts — Phase 3 grace period mapping table.\n")
	b.WriteString("//\n")
	b.WriteString("// Auto-generated by `gftd dns-sync --emit-routing-map`. DO NOT EDIT BY HAND.\n")
	b.WriteString("// Source: deps.toml [[legacy_nanoids]]\n")
	b.WriteString("// Phase 4 cutover (2026-10-01, ADR-0021): this file is renamed to\n")
	b.WriteString("// legacy-nanoid-map.archived.ts and the import in worker.ts is removed.\n\n")
	b.WriteString("export const LEGACY_NANOID_MAP: Record<string, string> = {\n")
	for _, l := range legacies {
		// Quote keys conservatively (some nanoids may start with a digit)
		b.WriteString(fmt.Sprintf("  %q: %q,\n", l.Nanoid, l.Handle))
	}
	b.WriteString("}\n\n")
	b.WriteString("/**\n")
	b.WriteString(" * Phase 4 deprecation window: when current time exceeds this, every legacy\n")
	b.WriteString(" * lookup logs a high-severity warning. Intended to fire alarms in CF Analytics.\n")
	b.WriteString(" */\n")
	b.WriteString("export const PHASE4_DEPRECATE_AT = new Date('2026-10-01T00:00:00Z')\n")
	return b.String()
}

// emitYoroMirrorTS — generate the yoro-side mirror of legacy-nanoid-map.ts.
// Used by /profile/[handle]/+page.server.ts to 301 redirect
// /profile/{nanoid}.etzhayyim.com → /profile/{handle}.etzhayyim.com during the Phase 3 grace.
// Includes a resolveLegacyHandle() helper that the routing-gateway primary copy
// does not need (routing-gateway operates at the DNS label level).
func emitYoroMirrorTS(legacies []idLegacy) string {
	sort.Slice(legacies, func(i, j int) bool { return legacies[i].Nanoid < legacies[j].Nanoid })
	var b strings.Builder
	b.WriteString("// legacy-nanoid-map.ts — Phase 3 grace period mapping table (yoro mirror).\n")
	b.WriteString("//\n")
	b.WriteString("// MIRROR OF: 50-infra/cloudflare/workers/routing-gateway/src/legacy-nanoid-map.ts\n")
	b.WriteString("// Both files are auto-generated from deps.toml [[legacy_nanoids]] by\n")
	b.WriteString("// `gftd dns-sync --emit-routing-map`. Keep in sync until Phase 4 cutover\n")
	b.WriteString("// (2026-10-01, ADR-0021).\n")
	b.WriteString("//\n")
	b.WriteString("// Used by: routes/profile/[handle]/+page.server.ts to 301 redirect\n")
	b.WriteString("// /profile/{nanoid}.etzhayyim.com → /profile/{handle}.etzhayyim.com\n\n")
	b.WriteString("export const LEGACY_NANOID_MAP: Record<string, string> = {\n")
	for _, l := range legacies {
		b.WriteString(fmt.Sprintf("  %q: %q,\n", l.Nanoid, l.Handle))
	}
	b.WriteString("};\n\n")
	b.WriteString("/**\n")
	b.WriteString(" * Resolve `{nanoid}.etzhayyim.com` to canonical handle, or null if not a legacy nanoid.\n")
	b.WriteString(" * Used by /profile/[handle] SSR redirect.\n")
	b.WriteString(" */\n")
	b.WriteString("export function resolveLegacyHandle(handle: string): string | null {\n")
	b.WriteString("  const match = handle.match(/^([a-z0-9-]+)\\.gftd\\.ai$/i);\n")
	b.WriteString("  if (!match) return null;\n")
	b.WriteString("  const nanoid = match[1].toLowerCase();\n")
	b.WriteString("  return LEGACY_NANOID_MAP[nanoid] ?? null;\n")
	b.WriteString("}\n")
	return b.String()
}

// patchWranglerBindings — replace the `services` array in wrangler.jsonc with
// the canonical 90+2 Service Bindings (PDS_WORKER + PLC_DIRECTORY + per-actor).
//
// JSONC (JSON-with-comments) is patched by scanning the services array start/end
// markers while skipping strings/comments. Full JSONC parsing is out of scope. If no
// `services` block exists, one is inserted before the closing brace of the root
// object.
func patchWranglerBindings(path string, actors []idActor) (string, int, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return "", 0, err
	}
	src := string(data)

	sortedActors := append([]idActor(nil), actors...)
	sort.Slice(sortedActors, func(i, j int) bool { return sortedActors[i].Name < sortedActors[j].Name })

	var sb strings.Builder
	sb.WriteString("\"services\": [\n")
	sb.WriteString("    { \"binding\": \"PDS_WORKER\",    \"service\": \"ai-gftd-pds-2603241700\" },\n")
	sb.WriteString("    { \"binding\": \"PLC_DIRECTORY\", \"service\": \"ai-gftd-plc-directory\" }")
	emitted := 2
	for _, a := range sortedActors {
		handle := a.Domain
		if handle == "" && len(a.Handles) > 0 {
			handle = a.Handles[0]
		}
		if handle == "" {
			continue
		}
		label := strings.Split(handle, ".")[0]
		bindingName := "WORKER_" + strings.ToUpper(strings.ReplaceAll(label, "-", "_"))
		serviceName := "ai-gftd-actor-" + label
		sb.WriteString(",\n")
		fmt.Fprintf(&sb, "    { \"binding\": %q, \"service\": %q }", bindingName, serviceName)
		emitted++
	}
	sb.WriteString("\n  ]")

	var patched string
	if start, end, ok := findServicesArrayRange(src); ok {
		patched = src[:start] + sb.String() + src[end:]
	} else {
		lastBrace := strings.LastIndex(src, "}")
		if lastBrace < 0 {
			return "", 0, fmt.Errorf("wrangler.jsonc: no closing brace found")
		}
		insertion := ",\n  " + sb.String() + "\n"
		patched = src[:lastBrace] + insertion + src[lastBrace:]
	}
	return patched, emitted, nil
}

func findServicesArrayRange(src string) (int, int, bool) {
	key := `"services"`
	keyStart := strings.Index(src, key)
	if keyStart < 0 {
		return 0, 0, false
	}
	i := keyStart + len(key)
	for i < len(src) && (src[i] == ' ' || src[i] == '\t' || src[i] == '\r' || src[i] == '\n') {
		i++
	}
	if i >= len(src) || src[i] != ':' {
		return 0, 0, false
	}
	i++
	for i < len(src) && (src[i] == ' ' || src[i] == '\t' || src[i] == '\r' || src[i] == '\n') {
		i++
	}
	if i >= len(src) || src[i] != '[' {
		return 0, 0, false
	}
	depth := 0
	inString := false
	inLineComment := false
	inBlockComment := false
	escaped := false
	for j := i; j < len(src); j++ {
		c := src[j]
		next := byte(0)
		if j+1 < len(src) {
			next = src[j+1]
		}
		if inLineComment {
			if c == '\n' {
				inLineComment = false
			}
			continue
		}
		if inBlockComment {
			if c == '*' && next == '/' {
				inBlockComment = false
				j++
			}
			continue
		}
		if inString {
			if escaped {
				escaped = false
			} else if c == '\\' {
				escaped = true
			} else if c == '"' {
				inString = false
			}
			continue
		}
		if c == '/' && next == '/' {
			inLineComment = true
			j++
			continue
		}
		if c == '/' && next == '*' {
			inBlockComment = true
			j++
			continue
		}
		if c == '"' {
			inString = true
			continue
		}
		if c == '[' {
			depth++
		} else if c == ']' {
			depth--
			if depth == 0 {
				return keyStart, j + 1, true
			}
		}
	}
	return 0, 0, false
}

// Stub for linter (matches resolveCloudflareToken signature in deploy.go)
var _ = bufio.NewReader
