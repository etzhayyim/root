// ADR-0033 guard: flag ad-hoc `COUNT(*) FROM <large_table>` queries in source.
// Canonical row count goes through `rw_catalog.rw_table_stats`
// (see 70-tools/gftd/gftd/db/stats.go `CountFromStats`).
package main

import (
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strings"
)

// largeTables = RisingWave tables with ≥ 10M rows as of ADR-0033 (2026-04-19).
// Keep this in sync with `rw_table_stats`; the list is intentionally small and
// manual — a table only lands here when its live key count crosses the
// ADR-0033 threshold.
var largeTables = []string{
	"edge_links_to",
	"edge_links_to_domain",
	"vertex_page",
	"vertex_legal_entity",
	"vertex_repo_record",
}

// Scan extensions considered source code for this lint.
var largeCountExts = map[string]bool{
	".go":  true,
	".ts":  true,
	".tsx": true,
	".js":  true,
	".mjs": true,
	".cjs": true,
	".mts": true,
	".py":  true,
	".rs":  true,
	".sql": true,
}

// Paths to skip — docs, archives, generated schema, the ADR itself, the stats
// helper, and the 30-graph/graph-schema/migrations tree (streaming MV
// definitions are an ADR-0033 exception).
var largeCountSkipPrefixes = []string{
	"90-docs/",
	"_archive/",
	"node_modules/",
	"30-graph/graph-schema/migrations/",
	"30-graph/graph-schema/src/database.ts",
	"70-tools/gftd/gftd/code_quality_large_count.go",
	"70-tools/gftd/gftd/db/stats.go",
}

// Per-path substrings to skip (build outputs, archives anywhere, bundled assets).
var largeCountSkipSubstrings = []string{
	"/.wrangler/",
	"/scripts/archive/",
	"/static/assets/",
	"/build/",
	"/dist/",
	"/target/",
}

func checkLargeTableCountStar(wsRoot string) codeQualityCheck {
	check := codeQualityCheck{
		Name:      "large_table_count_star",
		Tool:      "large-table-count-star (ADR-0033)",
		Available: true,
	}

	// Matches: COUNT(*)  [AS alias]  FROM  [whitespace]  <table>
	// and also cross-line form where FROM is on the next line.
	pattern := regexp.MustCompile(
		`(?is)COUNT\s*\(\s*\*\s*\)[^;]*?FROM\s+([a-zA-Z_][a-zA-Z0-9_]*)`,
	)

	tableSet := map[string]bool{}
	for _, t := range largeTables {
		tableSet[t] = true
	}

	var hits []string
	totalIssues := 0

	_ = filepath.WalkDir(wsRoot, func(path string, d os.DirEntry, err error) error {
		if err != nil {
			return nil
		}
		if d.IsDir() {
			// Skip heavy dirs early.
			base := d.Name()
			if base == "node_modules" || base == ".git" || base == "_archive" ||
				base == "target" || base == "dist" || base == "build" {
				return filepath.SkipDir
			}
			return nil
		}
		ext := strings.ToLower(filepath.Ext(path))
		if !largeCountExts[ext] {
			return nil
		}
		rel, err := filepath.Rel(wsRoot, path)
		if err != nil {
			rel = path
		}
		relSlash := filepath.ToSlash(rel)
		for _, p := range largeCountSkipPrefixes {
			if strings.HasPrefix(relSlash, p) {
				return nil
			}
		}
		for _, s := range largeCountSkipSubstrings {
			if strings.Contains("/"+relSlash, s) {
				return nil
			}
		}
		data, err := os.ReadFile(path)
		if err != nil {
			return nil
		}
		src := string(data)
		matches := pattern.FindAllStringSubmatchIndex(src, -1)
		for _, m := range matches {
			if len(m) < 4 {
				continue
			}
			table := src[m[2]:m[3]]
			if !tableSet[table] {
				continue
			}
			// Skip comment lines. Determine the start-of-line for the match and
			// inspect leading whitespace + first non-space chars.
			lineStart := strings.LastIndex(src[:m[0]], "\n") + 1
			lineText := src[lineStart:m[0]]
			trimmed := strings.TrimLeft(lineText, " \t")
			if strings.HasPrefix(trimmed, "//") || strings.HasPrefix(trimmed, "#") ||
				strings.HasPrefix(trimmed, "*") || strings.HasPrefix(trimmed, "--") {
				continue
			}
			// Compute 1-based line number of the COUNT(*) match start.
			line := 1 + strings.Count(src[:m[0]], "\n")
			totalIssues++
			hits = append(hits, fmt.Sprintf("%s:%d (%s)", relSlash, line, table))
		}
		return nil
	})

	check.Issues = totalIssues
	if totalIssues == 0 {
		check.Score = 100
		check.Details = "ADR-0033: no COUNT(*) against ≥10M-row tables"
	} else {
		score := 100 - totalIssues*20
		if score < 0 {
			score = 0
		}
		check.Score = float64(score)
		detail := strings.Join(hits, ", ")
		if len(detail) > 500 {
			detail = detail[:500] + "..."
		}
		check.Details = fmt.Sprintf("ADR-0033: %d ad-hoc COUNT(*) on large tables — %s", totalIssues, detail)
	}
	return check
}

