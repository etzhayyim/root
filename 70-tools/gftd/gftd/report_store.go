package main

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"
)

// rptCatalog is an Iceberg-like local Parquet catalog used by all CLI report commands.
type rptCatalog struct {
	FormatVersion int           `json:"format_version"`
	TableUUID     string        `json:"table_uuid"`
	Location      string        `json:"location"`
	Snapshots     []rptSnapshot `json:"snapshots"`
	CurrentID     int64         `json:"current_snapshot_id"`
}

// rptSnapshot represents one Parquet file in the catalog.
type rptSnapshot struct {
	SnapshotID int64  `json:"snapshot_id"`
	SnapshotMs int64  `json:"snapshot_ms"`
	Summary    string `json:"summary"`
	DataFile   string `json:"data_file"`
}

func (s *rptSnapshot) UnmarshalJSON(data []byte) error {
	type snapshotJSON struct {
		SnapshotID  int64  `json:"snapshot_id"`
		SnapshotMs  int64  `json:"snapshot_ms"`
		TimestampMs int64  `json:"timestamp_ms"`
		Summary     string `json:"summary"`
		DataFile    string `json:"data_file"`
	}
	var v snapshotJSON
	if err := json.Unmarshal(data, &v); err != nil {
		return err
	}
	s.SnapshotID = v.SnapshotID
	s.SnapshotMs = v.SnapshotMs
	if s.SnapshotMs == 0 {
		s.SnapshotMs = v.TimestampMs
	}
	s.Summary = v.Summary
	s.DataFile = v.DataFile
	return nil
}

func (s rptSnapshot) MarshalJSON() ([]byte, error) {
	type snapshotJSON struct {
		SnapshotID int64  `json:"snapshot_id"`
		SnapshotMs int64  `json:"snapshot_ms"`
		Summary    string `json:"summary"`
		DataFile   string `json:"data_file"`
	}
	return json.Marshal(snapshotJSON{
		SnapshotID: s.SnapshotID,
		SnapshotMs: s.SnapshotMs,
		Summary:    s.Summary,
		DataFile:   s.DataFile,
	})
}

// storeParquet writes rows as a ZSTD Parquet snapshot under
// <wsRoot>/80-data/<table>/snapshots/snap-<timestamp>.parquet.
// rows must be JSON-serialisable (slice of structs or maps).
// Returns the absolute path of the written file.
func storeParquet(wsRoot, table, summary string, rows any) (string, error) {
	if _, err := exec.LookPath("duckdb"); err != nil {
		return "", fmt.Errorf("duckdb not found in PATH — install: brew install duckdb")
	}

	tDir := filepath.Join(wsRoot, "80-data", table)
	snapDir := filepath.Join(tDir, "snapshots")
	if err := os.MkdirAll(snapDir, 0755); err != nil {
		return "", fmt.Errorf("mkdir %s: %w", snapDir, err)
	}

	now := time.Now().UTC()
	base := fmt.Sprintf("snap-%s", now.Format("20060102-150405"))
	tmpJSON := filepath.Join(snapDir, base+".json")
	parquetFile := filepath.Join(snapDir, base+".parquet")

	jsonBytes, err := json.Marshal(rows)
	if err != nil {
		return "", fmt.Errorf("marshal: %w", err)
	}
	if err := os.WriteFile(tmpJSON, jsonBytes, 0644); err != nil {
		return "", fmt.Errorf("write json: %w", err)
	}
	defer os.Remove(tmpJSON)

	duckSQL := fmt.Sprintf(
		`COPY (SELECT * FROM read_json_auto('%s')) TO '%s' (FORMAT PARQUET, COMPRESSION ZSTD);`,
		tmpJSON, parquetFile,
	)
	cmd := exec.Command("duckdb", "-c", duckSQL)
	cmd.Stderr = os.Stderr
	if err := cmd.Run(); err != nil {
		return "", fmt.Errorf("duckdb write: %w", err)
	}

	cat := loadRptCatalog(tDir, table)
	snapID := now.UnixMilli()
	relPath, _ := filepath.Rel(tDir, parquetFile)
	cat.Snapshots = append(cat.Snapshots, rptSnapshot{
		SnapshotID: snapID,
		SnapshotMs: snapID,
		Summary:    summary,
		DataFile:   relPath,
	})
	cat.CurrentID = snapID
	return parquetFile, saveRptCatalog(tDir, cat)
}

// queryParquet runs sql against <wsRoot>/80-data/<table>/snapshots/*.parquet.
// Use $TABLE as placeholder for the glob expression.
func queryParquet(wsRoot, table, sql string) error {
	if _, err := exec.LookPath("duckdb"); err != nil {
		return fmt.Errorf("duckdb not found in PATH — install: brew install duckdb")
	}
	glob := parquetGlob(wsRoot, table)
	sql = strings.ReplaceAll(sql, "$TABLE", fmt.Sprintf("read_parquet('%s')", glob))
	cmd := exec.Command("duckdb", "-c", sql)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	return cmd.Run()
}

// parquetGlob returns the glob pattern for all snapshots of a table.
func parquetGlob(wsRoot, table string) string {
	return filepath.Join(wsRoot, "80-data", table, "snapshots", "*.parquet")
}

// queryParquetJSON runs sql and returns the result rows as []map[string]any.
// Use $TABLE as placeholder.
func queryParquetJSON(wsRoot, table, sql string) ([]map[string]any, error) {
	if _, err := exec.LookPath("duckdb"); err != nil {
		return nil, fmt.Errorf("duckdb not found")
	}
	glob := parquetGlob(wsRoot, table)
	sql = strings.ReplaceAll(sql, "$TABLE", fmt.Sprintf("read_parquet('%s')", glob))
	cmd := exec.Command("duckdb", "-json", "-c", sql)
	out, err := cmd.Output()
	if err != nil {
		return nil, err
	}
	var rows []map[string]any
	if err := json.Unmarshal(out, &rows); err != nil {
		return nil, err
	}
	return rows, nil
}

func loadRptCatalog(tDir, table string) *rptCatalog {
	data, err := os.ReadFile(filepath.Join(tDir, "catalog.json"))
	if err != nil {
		return &rptCatalog{FormatVersion: 1, TableUUID: table + "-local-001", Location: tDir}
	}
	var cat rptCatalog
	if err := json.Unmarshal(data, &cat); err != nil {
		return &rptCatalog{FormatVersion: 1, TableUUID: table + "-local-001", Location: tDir}
	}
	return &cat
}

func saveRptCatalog(tDir string, cat *rptCatalog) error {
	data, err := json.MarshalIndent(cat, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(filepath.Join(tDir, "catalog.json"), data, 0644)
}
