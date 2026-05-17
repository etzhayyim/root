// actor migrate-to-plc — ADR-0014 Phase 5: did:web → did:plc migration client.
//
// Thin CLI that bridges to atproto.etzhayyim.com XRPC endpoint:
//   POST ai.gftd.plc.migrateActor
//   body: { "actor": "kami", "handle": "kami.etzhayyim.com" }
//   → 200 { "did": "did:plc:abcdef...", "genesisCid": "bafy...", "plcUrl": "https://plc.etzhayyim.com/did:plc:..." }
//
// PDS side (atproto.etzhayyim.com) performs:
//   1. Load rotation key from D1 signing_keys (ADR-0010 custody)
//   2. Build genesis op (rotation key + verification method + alsoKnownAs + pds service endpoint)
//   3. Sign with rotation key (ES256K)
//   4. Compute DID = did:plc:{base32(sha256(op))[:24]}
//   5. POST to plc.etzhayyim.com/{did} (self-hosted PLC directory, ADR-0014)
//   6. Return new did:plc to CLI
//
// CLI then patches deps.toml [[mitama_actors]]:
//   did = "did:plc:..."          (new canonical)
//   legacy_did_web = "did:web:..." (grace period marker, 6 months)

package main

import (
	"bytes"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net/http"
	"os"
	"regexp"
	"strings"
	"time"
)

type plcMigrateRequest struct {
	Actor  string `json:"actor"`
	Handle string `json:"handle"`
	DryRun bool   `json:"dryRun,omitempty"`
}

type plcMigrateResponse struct {
	DID        string `json:"did"`
	GenesisCID string `json:"genesisCid,omitempty"`
	PlcURL     string `json:"plcUrl,omitempty"`
	Handle     string `json:"handle"`
	LegacyDid  string `json:"legacyDid,omitempty"`
	Error      string `json:"error,omitempty"`
}

func runActorMigratePLC(args []string) error {
	fs := flag.NewFlagSet("actor migrate-to-plc", flag.ExitOnError)
	actorName := fs.String("actor", "", "actor name (must exist in deps.toml [[mitama_actors]])")
	handle := fs.String("handle", "", "handle for did:plc alsoKnownAs (default: {actor}.etzhayyim.com)")
	apply := fs.Bool("apply", false, "write changes to deps.toml (default: dry-run preview)")
	pdsURL := fs.String("pds", "https://atproto.etzhayyim.com", "PDS XRPC base URL")
	jsonOut := fs.Bool("json", false, "emit JSON response")
	depsPath := fs.String("deps", "deps.toml", "path to deps.toml")
	offline := fs.Bool("offline", false, "simulate response without calling PDS (for local testing)")
	_ = fs.Parse(args)

	if *actorName == "" {
		return fmt.Errorf("--actor required")
	}

	actors, _, err := parseIdentifierTables(*depsPath)
	if err != nil {
		return fmt.Errorf("parse %s: %w", *depsPath, err)
	}

	var target *idActor
	for i := range actors {
		if actors[i].Name == *actorName {
			target = &actors[i]
			break
		}
	}
	if target == nil {
		return fmt.Errorf("actor %q not found in %s [[mitama_actors]]", *actorName, *depsPath)
	}

	if !strings.HasPrefix(target.DID, "did:web:") {
		return fmt.Errorf("actor %q already has non-did:web identity: %s", *actorName, target.DID)
	}

	resolvedHandle := *handle
	if resolvedHandle == "" {
		if target.Domain != "" {
			resolvedHandle = target.Domain
		} else if len(target.Handles) > 0 {
			resolvedHandle = target.Handles[0]
		} else {
			resolvedHandle = *actorName + ".etzhayyim.com"
		}
	}

	// Preview
	if !*jsonOut {
		fmt.Printf("gftd actor migrate-to-plc — ADR-0014 Phase 5\n")
		fmt.Printf("=============================================\n")
		fmt.Printf("actor:       %s\n", *actorName)
		fmt.Printf("current DID: %s\n", target.DID)
		fmt.Printf("handle:      %s\n", resolvedHandle)
		fmt.Printf("PDS:         %s\n", *pdsURL)
		fmt.Printf("mode:        %s\n\n", pickMode(*apply, *offline))
	}

	// Call PDS (or mock if offline)
	var resp *plcMigrateResponse
	if *offline {
		resp = &plcMigrateResponse{
			DID:        mockDidPlc(*actorName),
			GenesisCID: "bafysimulated000000000000000000000000000",
			PlcURL:     "https://plc.etzhayyim.com/" + mockDidPlc(*actorName),
			Handle:     resolvedHandle,
			LegacyDid:  target.DID,
		}
	} else {
		resp, err = callPLCMigrate(*pdsURL, plcMigrateRequest{
			Actor:  *actorName,
			Handle: resolvedHandle,
			DryRun: !*apply,
		})
		if err != nil {
			return fmt.Errorf("PDS migrate call: %w", err)
		}
		if resp.Error != "" {
			return fmt.Errorf("PDS returned error: %s", resp.Error)
		}
	}

	if *jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(resp)
	}

	fmt.Printf("── Response\n")
	fmt.Printf("  new DID:     %s\n", resp.DID)
	fmt.Printf("  genesis CID: %s\n", resp.GenesisCID)
	fmt.Printf("  PLC URL:     %s\n", resp.PlcURL)
	fmt.Printf("  legacy DID:  %s (grandfathered 6 months)\n\n", resp.LegacyDid)

	if !*apply {
		fmt.Printf("dry-run: no changes written to deps.toml. Use --apply to update.\n")
		return nil
	}

	// Patch deps.toml: replace did + add legacy_did_web for this actor block
	if err := patchActorDID(*depsPath, *actorName, resp.DID, target.DID); err != nil {
		return fmt.Errorf("patch deps.toml [[mitama_actors]]: %w", err)
	}
	if err := patchLegacyNanoidMigration(*depsPath, *actorName, resp.DID); err != nil {
		// non-fatal: legacy_nanoids may not have entry for new actors
		fmt.Fprintf(os.Stderr, "warning: could not update [[legacy_nanoids]] for %s: %v\n", *actorName, err)
	}
	fmt.Printf("✓ deps.toml [[mitama_actors]] (%s) updated:\n", *actorName)
	fmt.Printf("    did            = %q\n", resp.DID)
	fmt.Printf("    legacy_did_web = %q\n", target.DID)
	fmt.Printf("✓ deps.toml [[legacy_nanoids]] (%s) updated:\n", *actorName)
	fmt.Printf("    new_did        = %q\n", resp.DID)
	fmt.Printf("    migrated_at    = %q (UTC)\n", time.Now().UTC().Format(time.RFC3339))
	fmt.Printf("\nNext: verify via 'gftd identifier-audit' and external PLC resolve at %s.\n", resp.PlcURL)
	return nil
}

// patchLegacyNanoidMigration — add `migrated_at` + `new_did` fields to the
// [[legacy_nanoids]] entry matching `actor`. Idempotent: skips if already set.
func patchLegacyNanoidMigration(path, actor, newDID string) error {
	data, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	lines := strings.Split(string(data), "\n")
	migratedAt := time.Now().UTC().Format(time.RFC3339)

	// Two-pass: 1) locate [start, end) of matching block; 2) patch
	blockStart, blockEnd := -1, -1
	curStart := -1
	curActorMatch := false
	finalize := func(end int) {
		if curStart >= 0 && curActorMatch && blockStart < 0 {
			blockStart = curStart
			blockEnd = end
		}
	}
	actorRe := regexp.MustCompile(`^actor\s*=\s*"([^"]+)"`)

	for i := 0; i < len(lines); i++ {
		line := strings.TrimSpace(lines[i])
		// Section header → flush previous + maybe start new
		if strings.HasPrefix(line, "[") {
			finalize(i)
			if line == "[[legacy_nanoids]]" {
				curStart = i
				curActorMatch = false
			} else {
				curStart = -1
			}
			continue
		}
		if curStart >= 0 && !curActorMatch {
			if m := actorRe.FindStringSubmatch(line); m != nil {
				curActorMatch = m[1] == actor
			}
		}
	}
	finalize(len(lines))

	if blockStart < 0 {
		return fmt.Errorf("actor %q not found in [[legacy_nanoids]]", actor)
	}
	return finishLegacyPatch(path, lines, blockStart, blockEnd, newDID, migratedAt)
}

func finishLegacyPatch(path string, lines []string, blockStart, blockEnd int, newDID, migratedAt string) error {
	hasNewDid := false
	hasMigratedAt := false
	insertPoint := -1
	for i := blockStart + 1; i < blockEnd; i++ {
		t := strings.TrimSpace(lines[i])
		if strings.HasPrefix(t, "new_did") {
			hasNewDid = true
		}
		if strings.HasPrefix(t, "migrated_at") {
			hasMigratedAt = true
		}
		// Insert after did= line (canonical position before reason/deprecate_at)
		if strings.HasPrefix(t, "did ") || strings.HasPrefix(t, "did=") {
			insertPoint = i + 1
		}
	}
	if hasNewDid && hasMigratedAt {
		return nil // idempotent
	}
	if insertPoint < 0 {
		insertPoint = blockEnd // append at end of block
	}
	insertions := []string{}
	if !hasNewDid {
		insertions = append(insertions, fmt.Sprintf(`new_did = "%s"`, newDID))
	}
	if !hasMigratedAt {
		insertions = append(insertions, fmt.Sprintf(`migrated_at = "%s"`, migratedAt))
	}
	lines = append(lines[:insertPoint], append(insertions, lines[insertPoint:]...)...)
	return os.WriteFile(path, []byte(strings.Join(lines, "\n")), 0o644)
}

func pickMode(apply, offline bool) string {
	switch {
	case offline && apply:
		return "offline + apply (mock response, writes deps.toml)"
	case offline:
		return "offline + dry-run (mock response, no write)"
	case apply:
		return "apply (PDS call, writes deps.toml)"
	default:
		return "dry-run (PDS call, no write)"
	}
}

func mockDidPlc(actor string) string {
	// Deterministic mock for offline testing (not cryptographic)
	clean := regexp.MustCompile(`[^a-z0-9]`).ReplaceAllString(strings.ToLower(actor), "")
	padded := (clean + "aaaaaaaaaaaaaaaaaaaaaaaaaa")[:24]
	return "did:plc:" + padded
}

func callPLCMigrate(pdsURL string, reqBody plcMigrateRequest) (*plcMigrateResponse, error) {
	body, _ := json.Marshal(reqBody)
	u := strings.TrimRight(pdsURL, "/") + "/xrpc/ai.gftd.plc.migrateActor"
	req, _ := http.NewRequest(http.MethodPost, u, bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	// Auth via resolveGFTDToken if available
	if token := resolveGFTDToken(); token != "" {
		req.Header.Set("Authorization", "Bearer "+token)
	}
	client := &http.Client{Timeout: 30 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	raw, _ := io.ReadAll(resp.Body)
	if resp.StatusCode >= 400 {
		return nil, fmt.Errorf("pds %d: %s", resp.StatusCode, string(raw))
	}
	var out plcMigrateResponse
	if err := json.Unmarshal(raw, &out); err != nil {
		return nil, fmt.Errorf("decode: %w", err)
	}
	return &out, nil
}

// resolveGFTDToken is provided by auth.go (shared helper).

// patchActorDID — find [[mitama_actors]] block matching actor and rewrite
// did + insert legacy_did_web. Preserves all other fields / order / formatting.
func patchActorDID(path, actor, newDID, oldDID string) error {
	data, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	lines := strings.Split(string(data), "\n")

	blockStart := -1
	nameMatch := false
	for i := 0; i < len(lines); i++ {
		line := strings.TrimSpace(lines[i])
		if line == "[[mitama_actors]]" {
			blockStart = i
			nameMatch = false
			continue
		}
		if blockStart >= 0 {
			if strings.HasPrefix(line, "[") {
				if nameMatch {
					break // should have done its work in block body
				}
				blockStart = -1
				continue
			}
			if m := regexp.MustCompile(`^name\s*=\s*"([^"]+)"`).FindStringSubmatch(line); m != nil {
				nameMatch = m[1] == actor
			}
			if nameMatch {
				if strings.HasPrefix(line, "did ") || strings.HasPrefix(line, "did=") || strings.HasPrefix(line, "did\t") {
					// Replace `did = "..."` with new did
					lines[i] = fmt.Sprintf(`did = "%s"`, newDID)
					// Insert legacy_did_web on next line (if not already present in block)
					hasLegacy := false
					for j := blockStart; j < len(lines); j++ {
						t := strings.TrimSpace(lines[j])
						if strings.HasPrefix(t, "[") && j != blockStart {
							break
						}
						if strings.HasPrefix(t, "legacy_did_web") {
							hasLegacy = true
							break
						}
					}
					if !hasLegacy {
						legacyLine := fmt.Sprintf(`legacy_did_web = "%s"`, oldDID)
						lines = append(lines[:i+1], append([]string{legacyLine}, lines[i+1:]...)...)
					}
					return os.WriteFile(path, []byte(strings.Join(lines, "\n")), 0o644)
				}
			}
		}
	}
	return fmt.Errorf("actor %q did field not found", actor)
}
