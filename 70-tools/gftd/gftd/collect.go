// gftd collect <domain> — Phase 1 "wall 1" public-dump collector.
//
// Reads 70-tools/gftd/gftd/collectors/<domain>.json, fetches the source URL,
// normalizes each record via the config's template mapping, and writes the
// result as a minimal vertex_repo_record row (uri/collection/rkey/repo/
// value_json). Skips PDS commit signing for speed — these are seed/bootstrap
// records, not federated writes.
//
// Coverage MV (`mv_world_coverage_live`) picks up the new rows automatically
// via `mv_world_record_per_host`.
//
// Design: 90-docs/260414-global-legal-entity-data-sources-design.md (Phase 1).
package main

import (
	"context"
	"encoding/csv"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"regexp"
	"runtime"
	"strings"
	"time"
)

type collectorConfig struct {
	Domain     string            `json:"domain"`
	AppHost    string            `json:"appHost"`
	Repo       string            `json:"repo"`
	Collection string            `json:"collection"`
	Source     collectorSource   `json:"source"`
	Rkey       string            `json:"rkey"`
	Mapping    map[string]string `json:"mapping"`
	ChunkSize  int               `json:"chunkSize"`
	Note       string            `json:"note,omitempty"`
}

type collectorSource struct {
	URL     string            `json:"url"`
	Format  string            `json:"format"`         // "json" | "csv" | "tsv" | "inline"
	Path    string            `json:"path"`           // JSONPath-ish: "$" or "$.data" (json only)
	Inline  []map[string]any  `json:"data,omitempty"` // for format="inline"
	Method  string            `json:"method,omitempty"`  // "GET" (default) | "POST"
	Body    string            `json:"body,omitempty"`    // request body (POST)
	Headers map[string]string `json:"headers,omitempty"` // additional request headers
}

func runCollect(args []string) error {
	fs := flag.NewFlagSet("collect", flag.ContinueOnError)
	configPath := fs.String("config", "", "collector config path (default: collectors/<domain>.json relative to gftd binary)")
	dryRun := fs.Bool("dry-run", false, "fetch + normalize only; do not write")
	limit := fs.Int("limit", 0, "max records to insert (0 = unlimited)")
	if err := fs.Parse(args); err != nil {
		return err
	}
	rest := fs.Args()
	if len(rest) == 0 {
		return fmt.Errorf("usage: gftd collect <domain> [--config path] [--dry-run] [--limit N]")
	}
	domain := rest[0]

	cfg, err := loadCollectorConfig(domain, *configPath)
	if err != nil {
		return err
	}
	fmt.Fprintf(os.Stderr, "collector: domain=%s repo=%s collection=%s source=%s\n",
		cfg.Domain, cfg.Repo, cfg.Collection, cfg.Source.URL)

	// Fetch + parse
	records, err := fetchAndParse(cfg)
	if err != nil {
		return fmt.Errorf("fetch: %w", err)
	}
	fmt.Fprintf(os.Stderr, "fetched: %d raw records\n", len(records))

	// Normalize
	normalized := make([]collectRecord, 0, len(records))
	for i, raw := range records {
		rkey := sanitizeRkey(applyTemplate(cfg.Rkey, raw))
		if rkey == "" {
			fmt.Fprintf(os.Stderr, "warning: record %d has empty rkey, skipping\n", i)
			continue
		}
		value := map[string]any{"$type": cfg.Collection}
		for k, tmpl := range cfg.Mapping {
			value[k] = applyTemplate(tmpl, raw)
		}
		normalized = append(normalized, collectRecord{rkey: rkey, value: value})
	}
	fmt.Fprintf(os.Stderr, "normalized: %d records\n", len(normalized))

	if *limit > 0 && len(normalized) > *limit {
		normalized = normalized[:*limit]
		fmt.Fprintf(os.Stderr, "limited to: %d\n", len(normalized))
	}

	if *dryRun {
		if len(normalized) > 0 {
			sample, _ := json.MarshalIndent(normalized[0].value, "", "  ")
			fmt.Fprintf(os.Stderr, "sample[0] rkey=%s value=%s\n", normalized[0].rkey, string(sample))
		}
		fmt.Fprintln(os.Stderr, "dry-run: no writes performed")
		return nil
	}

	// Write
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Minute)
	defer cancel()
	inserted, err := writeCollectedRecords(ctx, cfg, normalized)
	if err != nil {
		return fmt.Errorf("write: %w", err)
	}
	fmt.Fprintf(os.Stderr, "inserted: %d records into vertex_repo_record\n", inserted)
	fmt.Fprintf(os.Stderr, "coverage: SELECT collected FROM mv_world_coverage_live WHERE domain='%s'\n", cfg.Domain)
	return nil
}

type collectRecord struct {
	rkey  string
	value map[string]any
}

func loadCollectorConfig(domain, override string) (*collectorConfig, error) {
	var path string
	if strings.TrimSpace(override) != "" {
		path = override
	} else {
		// Resolve relative to the gftd binary location so the CLI works from any cwd.
		_, thisFile, _, ok := runtime.Caller(0)
		if !ok {
			return nil, fmt.Errorf("cannot resolve collector config directory")
		}
		path = filepath.Join(filepath.Dir(thisFile), "collectors", domain+".json")
	}
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("read config %s: %w", path, err)
	}
	var cfg collectorConfig
	if err := json.Unmarshal(data, &cfg); err != nil {
		return nil, fmt.Errorf("parse config %s: %w", path, err)
	}
	if cfg.Domain == "" {
		cfg.Domain = domain
	}
	if cfg.ChunkSize <= 0 {
		cfg.ChunkSize = 100
	}
	if cfg.Source.Format == "" {
		cfg.Source.Format = "json"
	}
	if cfg.Source.Path == "" {
		cfg.Source.Path = "$"
	}
	return &cfg, nil
}

func fetchAndParse(cfg *collectorConfig) ([]map[string]any, error) {
	if strings.ToLower(cfg.Source.Format) == "inline" {
		return cfg.Source.Inline, nil
	}
	client := &http.Client{Timeout: 60 * time.Second}
	method := strings.ToUpper(cfg.Source.Method)
	if method == "" {
		method = "GET"
	}
	var bodyReader io.Reader
	if cfg.Source.Body != "" {
		bodyReader = strings.NewReader(cfg.Source.Body)
	}
	req, _ := http.NewRequest(method, cfg.Source.URL, bodyReader)
	req.Header.Set("User-Agent", "gftd-collect/1.0")
	for k, v := range cfg.Source.Headers {
		req.Header.Set(k, v)
	}
	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 400 {
		body, _ := io.ReadAll(io.LimitReader(resp.Body, 1024))
		return nil, fmt.Errorf("HTTP %d: %s", resp.StatusCode, string(body))
	}
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	switch strings.ToLower(cfg.Source.Format) {
	case "json":
		return parseJSONSource(body, cfg.Source.Path)
	case "csv":
		return parseDelimited(body, ',')
	case "tsv":
		return parseDelimited(body, '\t')
	default:
		return nil, fmt.Errorf("unsupported format: %s", cfg.Source.Format)
	}
}

func parseJSONSource(body []byte, path string) ([]map[string]any, error) {
	var root any
	if err := json.Unmarshal(body, &root); err != nil {
		return nil, fmt.Errorf("json parse: %w", err)
	}
	// Simple JSONPath: $, $.key, $.key.sub
	cur := root
	path = strings.TrimSpace(path)
	if path == "" || path == "$" {
		// use root as-is
	} else {
		path = strings.TrimPrefix(path, "$.")
		path = strings.TrimPrefix(path, "$")
		for _, part := range strings.Split(path, ".") {
			if part == "" {
				continue
			}
			m, ok := cur.(map[string]any)
			if !ok {
				return nil, fmt.Errorf("path %s: expected object at %q", path, part)
			}
			cur = m[part]
		}
	}
	arr, ok := cur.([]any)
	if !ok {
		return nil, fmt.Errorf("path %s did not yield an array (got %T)", path, cur)
	}
	out := make([]map[string]any, 0, len(arr))
	for i, elem := range arr {
		m, ok := elem.(map[string]any)
		if !ok {
			return nil, fmt.Errorf("element %d is not an object", i)
		}
		out = append(out, m)
	}
	return out, nil
}

func parseDelimited(body []byte, sep rune) ([]map[string]any, error) {
	r := csv.NewReader(strings.NewReader(string(body)))
	r.Comma = sep
	r.LazyQuotes = true
	r.FieldsPerRecord = -1
	records, err := r.ReadAll()
	if err != nil {
		return nil, fmt.Errorf("csv: %w", err)
	}
	if len(records) == 0 {
		return nil, nil
	}
	header := records[0]
	out := make([]map[string]any, 0, len(records)-1)
	for _, row := range records[1:] {
		m := make(map[string]any, len(header))
		for i, h := range header {
			if i < len(row) {
				m[h] = row[i]
			}
		}
		out = append(out, m)
	}
	return out, nil
}

var templateRe = regexp.MustCompile(`\{\{([^}]+)\}\}`)

// Template accessors: {{field}}, {{field[N]}}, {{field.sub}}, {{field.sub[0]}}.
// Simple dot + bracket path, no quoting / no escapes.
func applyTemplate(tmpl string, row map[string]any) string {
	return templateRe.ReplaceAllStringFunc(tmpl, func(m string) string {
		path := strings.TrimSpace(m[2 : len(m)-2])
		var cur any = row
		i := 0
		for i < len(path) {
			// Read a key up to '.' or '['.
			j := i
			for j < len(path) && path[j] != '.' && path[j] != '[' {
				j++
			}
			if j > i {
				key := path[i:j]
				mp, ok := cur.(map[string]any)
				if !ok {
					return ""
				}
				cur, ok = mp[key]
				if !ok || cur == nil {
					return ""
				}
				i = j
			}
			if i < len(path) && path[i] == '.' {
				i++
				continue
			}
			if i < len(path) && path[i] == '[' {
				// Parse [N]
				k := strings.IndexByte(path[i:], ']')
				if k < 0 {
					return ""
				}
				idx := 0
				fmt.Sscanf(path[i+1:i+k], "%d", &idx)
				arr, ok := cur.([]any)
				if !ok || idx < 0 || idx >= len(arr) {
					return ""
				}
				cur = arr[idx]
				i += k + 1
				if i < len(path) && path[i] == '.' {
					i++
				}
			}
		}
		switch x := cur.(type) {
		case string:
			return x
		case nil:
			return ""
		default:
			b, _ := json.Marshal(x)
			return strings.Trim(string(b), `"`)
		}
	})
}

// writeCollectedRecords bulk-inserts minimal vertex_repo_record rows. Skips
// rows whose rkey already exists under (repo, collection) to keep the command
// idempotent across reruns.
func writeCollectedRecords(ctx context.Context, cfg *collectorConfig, records []collectRecord) (int, error) {
	pool, err := dbPool(ctx)
	if err != nil {
		return 0, err
	}
	if len(records) == 0 {
		return 0, nil
	}

	_ = pool // not directly used; writes go through db.RawQuery for Simple Protocol consistency.

	// Pre-fetch existing rkeys for this (repo, collection) so we skip duplicates.
	existing := map[string]struct{}{}
	{
		// db.RawQuery uses Simple Protocol (works around RisingWave Extended Protocol hangs).
		q := fmt.Sprintf(
			`SELECT rkey FROM vertex_repo_record WHERE repo = %s AND collection = %s`,
			sqlQuote(cfg.Repo), sqlQuote(cfg.Collection))
		res, err := rawQuery(ctx, q)
		if err != nil {
			return 0, fmt.Errorf("existing rkeys: %w", err)
		}
		for _, r := range res.Rows {
			if k, ok := r["rkey"].(string); ok {
				existing[k] = struct{}{}
			}
		}
	}

	inserted := 0

	// Bulk INSERT in chunks of cfg.ChunkSize — Simple Protocol `VALUES (...),(...),...`
	// outperforms per-row INSERTs roughly 100× on RisingWave for large seed loads.
	// RisingWave supports basic INSERT … VALUES but not all PG ON CONFLICT paths,
	// so dedup is handled in-memory via the `existing` set above.
	pending := make([]collectRecord, 0, cfg.ChunkSize)
	flush := func() error {
		if len(pending) == 0 {
			return nil
		}
		nowISO := time.Now().UTC().Format(time.RFC3339)
		nowMs := time.Now().UnixMilli()
		valuesSQL := make([]string, 0, len(pending))
		for _, rec := range pending {
			valueJSON, _ := json.Marshal(rec.value)
			uri := "at://" + cfg.Repo + "/" + cfg.Collection + "/" + rec.rkey
			valuesSQL = append(valuesSQL, fmt.Sprintf(
				"(%s, '', %s, %s, %s, '', %s, %s, NULL, %d, %s)",
				sqlQuote(uri), sqlQuote(cfg.Collection), sqlQuote(rec.rkey), sqlQuote(cfg.Repo),
				sqlQuote(string(valueJSON)), sqlQuote(nowISO), nowMs, sqlQuote(nowISO)))
		}
		q := "INSERT INTO vertex_repo_record (uri, cid, collection, rkey, repo, repo_rev, value_json, indexed_at, takedown_ref, ts_ms, created_at) VALUES " +
			strings.Join(valuesSQL, ", ")
		if _, err := rawQuery(ctx, q); err != nil {
			return fmt.Errorf("bulk insert (%d rows): %w", len(pending), err)
		}
		inserted += len(pending)
		pending = pending[:0]
		return nil
	}

	for _, rec := range records {
		if _, ok := existing[rec.rkey]; ok {
			continue
		}
		pending = append(pending, rec)
		if len(pending) >= cfg.ChunkSize {
			if err := flush(); err != nil {
				return inserted, err
			}
			if inserted%(cfg.ChunkSize*10) == 0 || inserted >= len(records)-cfg.ChunkSize {
				fmt.Fprintf(os.Stderr, "  inserted %d (batch of %d)...\n", inserted, cfg.ChunkSize)
			}
		}
	}
	if err := flush(); err != nil {
		return inserted, err
	}
	return inserted, nil
}

// sanitizeRkey maps an arbitrary string to the AT Protocol rkey character set
// (ALPHA / DIGIT / "-" / "_" / "." / ":" / "~"). Everything else collapses to
// "-"; the result is trimmed and truncated to 512 chars to respect Lex RFC.
func sanitizeRkey(s string) string {
	if s == "" {
		return ""
	}
	b := make([]byte, 0, len(s))
	lastDash := false
	for i := 0; i < len(s); i++ {
		c := s[i]
		ok := (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9') ||
			c == '-' || c == '_' || c == '.' || c == ':' || c == '~'
		if ok {
			b = append(b, c)
			lastDash = c == '-'
		} else if !lastDash && len(b) > 0 {
			b = append(b, '-')
			lastDash = true
		}
	}
	// Trim leading/trailing '-'
	out := strings.Trim(string(b), "-")
	if len(out) > 512 {
		out = out[:512]
	}
	return out
}

// sqlQuote returns a single-quoted SQL literal with embedded apostrophes doubled.
// Used by collect.go's Simple-Protocol INSERT path; inputs are all internally
// generated or source-derived text fields, never user-provided identifiers.
func sqlQuote(s string) string {
	return "'" + strings.ReplaceAll(s, "'", "''") + "'"
}
