// identifier-audit — ADR-0019 atproto-native identifier topology validator
// Detects violations of the 5-layer identifier model:
//   mnemonic-nanoid     : nanoid is leet substitution of actor name (high)
//   did-web-grandfathered : actor uses did:web (medium; Phase 5 opt-in migration)
//   missing-legacy      : actor has nanoid but no [[legacy_nanoids]] entry (medium)
//   handles-missing     : actor has neither handles[] nor domain field (high)
//   handles-schema-legacy : uses 'domain' without ADR-0019 'handles[]' array (low)
//   orphan-legacy       : [[legacy_nanoids]] entry without corresponding [[mitama_actors]] (low)
//
// Source of truth: 90-docs/adr/0019-atproto-native-identifier-topology.md
// Parser: inline text scan (no external TOML dependency)

package main

import (
	"bufio"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"sort"
	"strings"
)

type idActor struct {
	Name     string
	Domain   string
	Nanoid   string
	DID      string
	Handles  []string
}

type idLegacy struct {
	Actor       string
	Nanoid      string
	Handle      string
	DID         string
	MigratedAt  string // ADR-0019 Phase 5: ISO 8601 datetime when did:web → did:plc migration completed (empty = pending)
	NewDID      string // Post-migration did:plc (mirror of mitama_actors.did after Phase 5)
	DeprecateAt string
	Reason      string
}

type idViolation struct {
	RuleID   string `json:"rule_id"`
	Severity string `json:"severity"`
	Actor    string `json:"actor,omitempty"`
	Message  string `json:"message"`
	Hint     string `json:"hint,omitempty"`
}

func runIdentifierAudit(args []string) error {
	fs := flag.NewFlagSet("identifier-audit", flag.ExitOnError)
	outJSON := fs.Bool("json", false, "emit JSON output")
	sev := fs.String("severity", "", "filter by severity (critical|high|medium|low)")
	depsPath := fs.String("deps", "deps.toml", "path to deps.toml")
	_ = fs.Parse(args)

	actors, legacies, err := parseIdentifierTables(*depsPath)
	if err != nil {
		return err
	}

	legacyByActor := map[string]idLegacy{}
	for _, l := range legacies {
		legacyByActor[l.Actor] = l
	}
	mitamaNames := map[string]struct{}{}
	for _, m := range actors {
		mitamaNames[m.Name] = struct{}{}
	}

	var violations []idViolation
	for _, a := range actors {
		if a.Nanoid != "" && isMnemonicNanoid(a.Name, a.Nanoid) {
			violations = append(violations, idViolation{
				RuleID:   "mnemonic-nanoid",
				Severity: "high",
				Actor:    a.Name,
				Message:  fmt.Sprintf("nanoid %q appears to be leet/mnemonic of %q", a.Nanoid, a.Name),
				Hint:     "ADR-0019 R1: new actors must use TRUE random base62 or drop nanoid entirely",
			})
		}
		if strings.HasPrefix(a.DID, "did:web:") {
			violations = append(violations, idViolation{
				RuleID:   "did-web-grandfathered",
				Severity: "medium",
				Actor:    a.Name,
				Message:  fmt.Sprintf("did=%q uses did:web (domain-coupled)", a.DID),
				Hint:     "ADR-0019 Phase 5: opt-in migration to did:plc for content-addressed immutable identity",
			})
		}
		if a.Nanoid != "" {
			if _, ok := legacyByActor[a.Name]; !ok {
				violations = append(violations, idViolation{
					RuleID:   "missing-legacy",
					Severity: "medium",
					Actor:    a.Name,
					Message:  fmt.Sprintf("actor has nanoid=%q but no [[legacy_nanoids]] entry", a.Nanoid),
					Hint:     "ADR-0019 Phase 2: all mnemonic/legacy nanoids must be grandfathered",
				})
			}
		}
		if len(a.Handles) == 0 && a.Domain == "" {
			violations = append(violations, idViolation{
				RuleID:   "handles-missing",
				Severity: "high",
				Actor:    a.Name,
				Message:  "actor has neither handles[] nor domain field",
				Hint:     "ADR-0019 R4: set handles = [\"{name}.etzhayyim.com\"]",
			})
		}
		if len(a.Handles) == 0 && a.Domain != "" {
			violations = append(violations, idViolation{
				RuleID:   "handles-schema-legacy",
				Severity: "low",
				Actor:    a.Name,
				Message:  "uses legacy 'domain' field, missing ADR-0019 'handles[]' array",
				Hint:     fmt.Sprintf("add: handles = [%q]", a.Domain),
			})
		}
	}
	for _, l := range legacies {
		if _, ok := mitamaNames[l.Actor]; !ok {
			violations = append(violations, idViolation{
				RuleID:   "orphan-legacy",
				Severity: "low",
				Actor:    l.Actor,
				Message:  fmt.Sprintf("[[legacy_nanoids]] has no matching [[mitama_actors]] (nanoid=%q)", l.Nanoid),
				Hint:     "remove stale legacy_nanoids entry or restore mitama_actors entry",
			})
		}
		// ADR-0019 Phase 5 progress: legacy entry with new_did set but parent actor still uses did:web
		if l.NewDID != "" && strings.HasPrefix(l.NewDID, "did:plc:") {
			for _, a := range actors {
				if a.Name == l.Actor && strings.HasPrefix(a.DID, "did:web:") {
					violations = append(violations, idViolation{
						RuleID:   "phase5-migration-incomplete",
						Severity: "low",
						Actor:    l.Actor,
						Message:  fmt.Sprintf("legacy_nanoids.new_did=%s set but mitama_actors.did still %s", l.NewDID, a.DID),
						Hint:     "Phase 5 migration partial: update mitama_actors.did to did:plc and finalize",
					})
				}
			}
		}
	}

	if *sev != "" {
		filtered := make([]idViolation, 0, len(violations))
		for _, v := range violations {
			if v.Severity == *sev {
				filtered = append(filtered, v)
			}
		}
		violations = filtered
	}

	sevRank := map[string]int{"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
	sort.SliceStable(violations, func(i, j int) bool {
		if sevRank[violations[i].Severity] != sevRank[violations[j].Severity] {
			return sevRank[violations[i].Severity] < sevRank[violations[j].Severity]
		}
		return violations[i].Actor < violations[j].Actor
	})

	if *outJSON {
		type report struct {
			TotalActors int            `json:"total_actors"`
			LegacyCount int            `json:"legacy_nanoids_count"`
			Violations  []idViolation  `json:"violations"`
			BySeverity  map[string]int `json:"by_severity"`
			ByRule      map[string]int `json:"by_rule"`
		}
		bySev := map[string]int{}
		byRule := map[string]int{}
		for _, v := range violations {
			bySev[v.Severity]++
			byRule[v.RuleID]++
		}
		r := report{
			TotalActors: len(actors),
			LegacyCount: len(legacies),
			Violations:  violations,
			BySeverity:  bySev,
			ByRule:      byRule,
		}
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(r)
	}

	fmt.Printf("ADR-0019 Identifier Audit\n")
	fmt.Printf("=========================\n")
	fmt.Printf("mitama_actors:   %d\n", len(actors))
	fmt.Printf("legacy_nanoids:  %d\n", len(legacies))
	fmt.Printf("violations:      %d\n\n", len(violations))

	if len(violations) == 0 {
		fmt.Println("✅ No violations detected.")
		return nil
	}

	bySev := map[string]int{}
	byRule := map[string]int{}
	for _, v := range violations {
		bySev[v.Severity]++
		byRule[v.RuleID]++
	}
	fmt.Printf("By severity: critical=%d high=%d medium=%d low=%d\n",
		bySev["critical"], bySev["high"], bySev["medium"], bySev["low"])
	fmt.Printf("By rule:\n")
	rules := make([]string, 0, len(byRule))
	for r := range byRule {
		rules = append(rules, r)
	}
	sort.Strings(rules)
	for _, r := range rules {
		fmt.Printf("  %s: %d\n", r, byRule[r])
	}
	fmt.Println()

	curSev := ""
	for _, v := range violations {
		if v.Severity != curSev {
			fmt.Printf("\n── %s (%d)\n", strings.ToUpper(v.Severity), bySev[v.Severity])
			curSev = v.Severity
		}
		fmt.Printf("  [%s] %s: %s\n", v.RuleID, v.Actor, v.Message)
		if v.Hint != "" {
			fmt.Printf("        hint: %s\n", v.Hint)
		}
	}

	fmt.Printf("\nReference: 90-docs/adr/0019-atproto-native-identifier-topology.md\n")
	fmt.Printf("Migration: Phase 1 freeze → 2 grandfather (✓) → 3 DNS → 4 cleanup 2026-10-01\n")
	return nil
}

// parseIdentifierTables scans deps.toml line-by-line and extracts
// [[mitama_actors]] + [[legacy_nanoids]] entries. This avoids adding a TOML
// library dependency. Format assumed:
//
//	[[mitama_actors]]
//	name = "foo"
//	domain = "foo.etzhayyim.com"
//	nanoid = "..."
//	did = "..."
//	handles = ["a.etzhayyim.com", "b.etzhayyim.com"]
func parseIdentifierTables(path string) ([]idActor, []idLegacy, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, nil, err
	}
	defer f.Close()

	var actors []idActor
	var legacies []idLegacy

	var curActor *idActor
	var curLegacy *idLegacy
	var mode string // "actor", "legacy", or ""

	flush := func() {
		if mode == "actor" && curActor != nil && curActor.Name != "" {
			actors = append(actors, *curActor)
		}
		if mode == "legacy" && curLegacy != nil && curLegacy.Actor != "" {
			legacies = append(legacies, *curLegacy)
		}
	}

	sc := bufio.NewScanner(f)
	sc.Buffer(make([]byte, 1024*1024), 1024*1024)
	for sc.Scan() {
		line := strings.TrimSpace(sc.Text())
		if strings.HasPrefix(line, "#") || line == "" {
			continue
		}
		// Header detection
		if line == "[[mitama_actors]]" {
			flush()
			curActor = &idActor{}
			curLegacy = nil
			mode = "actor"
			continue
		}
		if line == "[[legacy_nanoids]]" {
			flush()
			curLegacy = &idLegacy{}
			curActor = nil
			mode = "legacy"
			continue
		}
		// Different header → flush and reset
		if strings.HasPrefix(line, "[") {
			flush()
			curActor = nil
			curLegacy = nil
			mode = ""
			continue
		}

		// Field assignment
		eq := strings.Index(line, "=")
		if eq < 0 {
			continue
		}
		key := strings.TrimSpace(line[:eq])
		val := strings.TrimSpace(line[eq+1:])
		val = stripInlineComment(val)

		switch mode {
		case "actor":
			if curActor == nil {
				continue
			}
			switch key {
			case "name":
				curActor.Name = unquote(val)
			case "domain":
				curActor.Domain = unquote(val)
			case "nanoid":
				curActor.Nanoid = unquote(val)
			case "did":
				curActor.DID = unquote(val)
			case "handles":
				curActor.Handles = parseStringArray(val)
			}
		case "legacy":
			if curLegacy == nil {
				continue
			}
			switch key {
			case "actor":
				curLegacy.Actor = unquote(val)
			case "nanoid":
				curLegacy.Nanoid = unquote(val)
			case "handle":
				curLegacy.Handle = unquote(val)
			case "did":
				curLegacy.DID = unquote(val)
			case "migrated_at":
				curLegacy.MigratedAt = unquote(val)
			case "new_did":
				curLegacy.NewDID = unquote(val)
			case "deprecate_at":
				curLegacy.DeprecateAt = unquote(val)
			case "reason":
				curLegacy.Reason = unquote(val)
			}
		}
	}
	flush()
	if err := sc.Err(); err != nil {
		return nil, nil, err
	}
	return actors, legacies, nil
}

func stripInlineComment(s string) string {
	// Strip # comment not inside a string
	inStr := false
	for i, c := range s {
		if c == '"' {
			inStr = !inStr
		}
		if c == '#' && !inStr {
			return strings.TrimSpace(s[:i])
		}
	}
	return s
}

func unquote(s string) string {
	s = strings.TrimSpace(s)
	if len(s) >= 2 && s[0] == '"' && s[len(s)-1] == '"' {
		return s[1 : len(s)-1]
	}
	return s
}

func parseStringArray(s string) []string {
	s = strings.TrimSpace(s)
	s = strings.TrimPrefix(s, "[")
	s = strings.TrimSuffix(s, "]")
	parts := strings.Split(s, ",")
	var out []string
	for _, p := range parts {
		p = strings.TrimSpace(p)
		if p == "" {
			continue
		}
		out = append(out, unquote(p))
	}
	return out
}

// isMnemonicNanoid detects leet/mnemonic substitution of name in nanoid.
// Heuristic: nanoid starts with first 3+ chars of (leet-substituted) name.
func isMnemonicNanoid(name, nanoid string) bool {
	if len(nanoid) < 3 {
		return false
	}
	nameClean := strings.ReplaceAll(strings.ReplaceAll(name, "-", ""), "_", "")
	if len(nameClean) < 3 {
		return false
	}
	if nanoid == name || nanoid == nameClean {
		return true
	}
	leet := strings.NewReplacer("a", "4", "e", "3", "i", "1", "o", "0", "s", "5", "l", "1").Replace(nameClean)
	maxLen := len(nameClean)
	if maxLen > 8 {
		maxLen = 8
	}
	for n := 3; n <= maxLen; n++ {
		if strings.HasPrefix(nanoid, nameClean[:n]) || strings.HasPrefix(nanoid, leet[:n]) {
			return true
		}
	}
	return false
}
