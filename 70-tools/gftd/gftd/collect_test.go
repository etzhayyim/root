package main

import (
	"context"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/etzhayyim/root/70-tools/gftd/gftd/db"
	"github.com/jackc/pgx/v5/pgxpool"
)

func TestLoadCollectorConfigDefaultsAndOverride(t *testing.T) {
	dir := t.TempDir()
	cfgPath := filepath.Join(dir, "demo.json")
	raw := `{"repo":"did:web:demo.etzhayyim.com","collection":"ai.gftd.apps.demo.entry","source":{"url":"https://example.com/data.json"}}`
	if err := os.WriteFile(cfgPath, []byte(raw), 0o644); err != nil {
		t.Fatalf("write config: %v", err)
	}

	cfg, err := loadCollectorConfig("demo", cfgPath)
	if err != nil {
		t.Fatalf("loadCollectorConfig: %v", err)
	}
	if cfg.Domain != "demo" || cfg.ChunkSize != 100 || cfg.Source.Format != "json" || cfg.Source.Path != "$" {
		t.Fatalf("unexpected config: %+v", cfg)
	}
}

func TestParseJSONSourceAndDelimitedAndTemplate(t *testing.T) {
	jsonBody := []byte(`{"data":[{"id":"a1","meta":{"rank":2}}]}`)
	rows, err := parseJSONSource(jsonBody, "$.data")
	if err != nil {
		t.Fatalf("parseJSONSource: %v", err)
	}
	if len(rows) != 1 || rows[0]["id"] != "a1" {
		t.Fatalf("unexpected rows: %#v", rows)
	}

	csvRows, err := parseDelimited([]byte("id,name\n1,Alice\n2,Bob\n"), ',')
	if err != nil {
		t.Fatalf("parseDelimited csv: %v", err)
	}
	if len(csvRows) != 2 || csvRows[1]["name"] != "Bob" {
		t.Fatalf("unexpected csv rows: %#v", csvRows)
	}

	got := applyTemplate("{{id}}-{{meta}}-{{missing}}", rows[0])
	if got != `a1-{"rank":2}-` {
		t.Fatalf("applyTemplate = %q", got)
	}
}

func TestFetchAndParseInlineAndSQLQuote(t *testing.T) {
	cfg := &collectorConfig{
		Source: collectorSource{
			Format: "inline",
			Inline: []map[string]any{{"id": "1", "name": "Alpha"}},
		},
	}
	rows, err := fetchAndParse(cfg)
	if err != nil {
		t.Fatalf("fetchAndParse inline: %v", err)
	}
	if len(rows) != 1 || rows[0]["name"] != "Alpha" {
		t.Fatalf("unexpected inline rows: %#v", rows)
	}
	if got := sqlQuote("O'Reilly"); got != "'O''Reilly'" {
		t.Fatalf("sqlQuote = %q", got)
	}

	value, _ := json.Marshal(rows[0])
	if string(value) == "" {
		t.Fatal("expected json output")
	}
}

func TestWriteCollectedRecordsDedupesAndBuildsInsert(t *testing.T) {
	oldRawQuery := rawQuery
	oldDBPool := dbPool
	t.Cleanup(func() {
		rawQuery = oldRawQuery
		dbPool = oldDBPool
	})

	dbPool = func(context.Context) (*pgxpool.Pool, error) {
		return &pgxpool.Pool{}, nil
	}

	var queries []string
	rawQuery = func(_ context.Context, sql string, args ...any) (*db.RawResult, error) {
		queries = append(queries, sql)
		if strings.HasPrefix(sql, "SELECT rkey FROM vertex_repo_record") {
			return &db.RawResult{Rows: []map[string]any{{"rkey": "existing"}}}, nil
		}
		if strings.HasPrefix(sql, "INSERT INTO vertex_repo_record") {
			if !strings.Contains(sql, "fresh") || strings.Contains(sql, "existing") {
				t.Fatalf("unexpected insert SQL: %s", sql)
			}
			if !strings.Contains(sql, "did:web:demo.etzhayyim.com") || !strings.Contains(sql, "ai.gftd.apps.demo.entry") {
				t.Fatalf("missing repo/collection in insert SQL: %s", sql)
			}
			return &db.RawResult{}, nil
		}
		t.Fatalf("unexpected SQL: %s", sql)
		return nil, nil
	}

	inserted, err := writeCollectedRecords(context.Background(), &collectorConfig{
		Repo:       "did:web:demo.etzhayyim.com",
		Collection: "ai.gftd.apps.demo.entry",
		ChunkSize:  10,
	}, []collectRecord{
		{rkey: "existing", value: map[string]any{"id": "existing"}},
		{rkey: "fresh", value: map[string]any{"id": "fresh"}},
	})
	if err != nil {
		t.Fatalf("writeCollectedRecords: %v", err)
	}
	if inserted != 1 {
		t.Fatalf("inserted = %d, want 1", inserted)
	}
	if len(queries) != 2 {
		t.Fatalf("query count = %d, want 2", len(queries))
	}
}
