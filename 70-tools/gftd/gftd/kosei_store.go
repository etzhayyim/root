// kosei_store.go — Parquet + DuckDB storage for gftd kosei
//
// Data layout (80-data/kosei/):
//
//	config.json                  Current tier assignments (source of truth)
//	snapshots/snap-*.parquet     Point-in-time app tier snapshots (ZSTD)
//	history/changes.parquet      Audit log of tier changes (ZSTD)
//	catalog.json                 Iceberg-like snapshot catalog
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"strings"
	"time"
)

// ── Config JSON ────────────────────────────────────────────────────────────

func koseiConfigPath(dDir string) string { return filepath.Join(dDir, "config.json") }

func koseiLoadConfig(dDir string) *koseiConfig {
	data, err := os.ReadFile(koseiConfigPath(dDir))
	if err != nil {
		return &koseiConfig{
			FormatVersion: 1,
			Apps:          make(map[string]koseiAppCfg),
		}
	}
	var cfg koseiConfig
	if json.Unmarshal(data, &cfg) != nil {
		return &koseiConfig{FormatVersion: 1, Apps: make(map[string]koseiAppCfg)}
	}
	if cfg.Apps == nil {
		cfg.Apps = make(map[string]koseiAppCfg)
	}
	return &cfg
}

func koseiSaveConfig(dDir string, cfg *koseiConfig) error {
	if err := os.MkdirAll(dDir, 0755); err != nil {
		return err
	}
	cfg.UpdatedAt = time.Now().UTC().Format(time.RFC3339)
	data, err := json.MarshalIndent(cfg, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(koseiConfigPath(dDir), data, 0644)
}

// ── Snapshot row ───────────────────────────────────────────────────────────

// koseiSnapshotRow is one app's state at snapshot time (Parquet row).
type koseiSnapshotRow struct {
	SnapshotAt    string  `json:"snapshot_at"`
	AppName       string  `json:"app_name"`
	Nanoid        string  `json:"nanoid"`
	DID           string  `json:"did"`
	Tier          string  `json:"tier"`
	Efficiency    float64 `json:"efficiency"`
	PerformerType string  `json:"performer_type"`
	UIType        string  `json:"ui_type"`
	RuntimeType   string  `json:"runtime_type"`
	AssignedBy    string  `json:"assigned_by"`
	Notes         string  `json:"notes"`
}

// ── Change history row ─────────────────────────────────────────────────────

// koseiChangeRow is one tier change event in the audit log (Parquet row).
type koseiChangeRow struct {
	ChangedAt string `json:"changed_at"`
	AppName   string `json:"app_name"`
	Nanoid    string `json:"nanoid"`
	OldTier   string `json:"old_tier"`
	NewTier   string `json:"new_tier"`
	Reason    string `json:"reason"`
	ChangedBy string `json:"changed_by"` // "manual" | "auto"
}

// ── Iceberg-like snapshot catalog ─────────────────────────────────────────

type koseiCatalog struct {
	FormatVersion int             `json:"format_version"`
	TableUUID     string          `json:"table_uuid"`
	Location      string          `json:"location"`
	Snapshots     []koseiSnapshot `json:"snapshots"`
	CurrentID     int64           `json:"current_snapshot_id"`
}

type koseiSnapshot struct {
	SnapshotID int64  `json:"snapshot_id"`
	SnapshotMs int64  `json:"snapshot_ms"`
	Summary    string `json:"summary"`
	DataFile   string `json:"data_file"`
}

func (s *koseiSnapshot) UnmarshalJSON(data []byte) error {
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

func (s koseiSnapshot) MarshalJSON() ([]byte, error) {
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

func koseiCatalogPath(dDir string) string { return filepath.Join(dDir, "catalog.json") }

func koseiLoadCatalog(dDir string) *koseiCatalog {
	data, err := os.ReadFile(koseiCatalogPath(dDir))
	if err != nil {
		return &koseiCatalog{FormatVersion: 1, TableUUID: "kosei-local-001", Location: dDir}
	}
	var cat koseiCatalog
	if json.Unmarshal(data, &cat) != nil {
		return &koseiCatalog{FormatVersion: 1, TableUUID: "kosei-local-001", Location: dDir}
	}
	return &cat
}

func koseiSaveCatalog(dDir string, cat *koseiCatalog) error {
	data, err := json.MarshalIndent(cat, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(koseiCatalogPath(dDir), data, 0644)
}

// ── Snapshot command ───────────────────────────────────────────────────────

func runKoseiSnapshot(args []string) error {
	fs := flag.NewFlagSet("kosei snapshot", flag.ContinueOnError)
	workspaceDir := fs.String("workspace-dir", "", "workspace root")
	dataDir := fs.String("data-dir", "", "data directory")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	if _, err := exec.LookPath("duckdb"); err != nil {
		return fmt.Errorf("duckdb not found in PATH — install: brew install duckdb")
	}

	wsRoot, dDir, err := koseiResolveRoots(*workspaceDir, *dataDir)
	if err != nil {
		return err
	}

	states, err := koseiLoadStates(wsRoot, dDir)
	if err != nil {
		return err
	}

	now := time.Now().UTC()
	snapAt := now.Format(time.RFC3339)
	snapName := fmt.Sprintf("snap-%s", now.Format("20060102-150405"))

	fmt.Fprintf(os.Stderr, "scanning stacks for %d apps...\n", len(states))
	var rows []koseiSnapshotRowFull
	for _, s := range states {
		appDir := filepath.Join(wsRoot, s.Dir)
		st := koseiScanStack(appDir, s.koseiAppMeta)
		rows = append(rows, koseiSnapshotRowFull{
			SnapshotAt:     snapAt,
			AppName:        s.Name,
			Nanoid:         s.Nanoid,
			DID:            s.DID,
			Tier:           s.Tier,
			Efficiency:     s.Efficiency,
			PerformerType:  s.PerformerType,
			UIType:         s.UIType,
			RuntimeType:    s.RuntimeType,
			AssignedBy:     s.AssignedBy,
			Notes:          s.Notes,
			Language:       st.Language,
			Framework:      st.Framework,
			ContentMode:    st.ContentMode,
			HasSvelte:      st.HasSvelte,
			HasWebGPU:      st.HasWebGPU,
			HasONNX:        st.HasONNX,
			HasFIDO2:       st.HasFIDO2,
			HasSignal:      st.HasSignal,
			HasWASM:        st.HasWASM,
			HasMCP:         st.HasMCP,
			HasBPMN:        st.HasBPMN,
			HasWorkersAI:   st.HasWorkersAI,
			HasBrowser:     st.HasBrowser,
			HasRisingWave:  st.HasRisingWave,
			HasYata:        st.HasYata,
			HasGraphSQL:   st.HasGraphSQL,
			HasEvolver:     st.HasEvolver,
			HasSpace:       st.HasSpace,
			HasGame:        st.HasGame,
			HasDesktop:     st.HasDesktop,
			HasSubscribe:   st.HasSubscribe,
			CollCount:      st.CollCount,
			RequireCount:   st.RequiresCount,
			ProvideCount:   st.ProvidesCount,
			R2Count:        st.R2Count,
			ServiceCount:   st.ServiceCount,
			SecretCount:    st.SecretCount,
			NPMDepCount:    len(st.NPMDeps),
			WITImportCount: len(st.WITImports),
			HasWIT:         st.HasWIT,
		})
	}

	snapshotsDir := filepath.Join(dDir, "snapshots")
	parquetPath := filepath.Join(snapshotsDir, snapName+".parquet")
	if err := koseiWriteParquet(rows, parquetPath); err != nil {
		return fmt.Errorf("write parquet: %w", err)
	}

	// Update catalog
	cat := koseiLoadCatalog(dDir)
	snapID := now.UnixMilli()
	relPath, _ := filepath.Rel(dDir, parquetPath)

	t1 := 0
	t2 := 0
	t3 := 0
	unknown := 0
	for _, r := range rows {
		switch r.Tier {
		case "T1":
			t1++
		case "T2":
			t2++
		case "T3":
			t3++
		default:
			unknown++
		}
	}

	cat.Snapshots = append(cat.Snapshots, koseiSnapshot{
		SnapshotID: snapID,
		SnapshotMs: snapID,
		Summary:    fmt.Sprintf("%s apps=%d T1=%d T2=%d T3=%d ?=%d η=%.3f", now.Format("2006-01-02 15:04"), len(rows), t1, t2, t3, unknown, koseiSystemEta(states)),
		DataFile:   relPath,
	})
	cat.CurrentID = snapID
	if err := koseiSaveCatalog(dDir, cat); err != nil {
		return fmt.Errorf("save catalog: %w", err)
	}

	fmt.Fprintf(os.Stderr, "snapshot: %s\n", relPath)
	fmt.Fprintf(os.Stderr, "apps=%d  T1=%d T2=%d T3=%d ?=%d  η=%.3f\n", len(rows), t1, t2, t3, unknown, koseiSystemEta(states))
	fmt.Fprintf(os.Stderr, "snapshots: %d total\n", len(cat.Snapshots))
	return nil
}

// koseiWriteParquet writes rows as Parquet via DuckDB (JSON intermediate).
func koseiWriteParquet[T any](rows []T, parquetPath string) error {
	tmpJSON := parquetPath[:len(parquetPath)-8] + ".json"
	defer os.Remove(tmpJSON)

	data, err := json.Marshal(rows)
	if err != nil {
		return fmt.Errorf("marshal: %w", err)
	}
	if err := os.WriteFile(tmpJSON, data, 0644); err != nil {
		return fmt.Errorf("write json: %w", err)
	}

	sql := fmt.Sprintf(
		`COPY (SELECT * FROM read_json_auto('%s')) TO '%s' (FORMAT PARQUET, COMPRESSION ZSTD);`,
		tmpJSON, parquetPath,
	)
	cmd := exec.Command("duckdb", "-c", sql)
	cmd.Stderr = os.Stderr
	return cmd.Run()
}

// ── Query command ──────────────────────────────────────────────────────────

func runKoseiQuery(args []string) error {
	fs := flag.NewFlagSet("kosei query", flag.ContinueOnError)
	workspaceDir := fs.String("workspace-dir", "", "workspace root")
	dataDir := fs.String("data-dir", "", "data directory")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	if _, err := exec.LookPath("duckdb"); err != nil {
		return fmt.Errorf("duckdb not found in PATH — install: brew install duckdb")
	}

	_, dDir, err := koseiResolveRoots(*workspaceDir, *dataDir)
	if err != nil {
		return err
	}

	snapshotsGlob := filepath.Join(dDir, "snapshots", "*.parquet")

	userSQL := strings.Join(fs.Args(), " ")
	if userSQL == "" {
		userSQL = fmt.Sprintf(`
SELECT snapshot_at, tier, count(*) AS apps, round(avg(efficiency),3) AS avg_eta
FROM read_parquet('%s')
GROUP BY snapshot_at, tier
ORDER BY snapshot_at DESC, tier`, snapshotsGlob)
	} else {
		userSQL = strings.ReplaceAll(userSQL, "$TABLE", fmt.Sprintf("read_parquet('%s')", snapshotsGlob))
		userSQL = strings.ReplaceAll(userSQL, "$HIST", fmt.Sprintf("read_parquet('%s')", filepath.Join(dDir, "history", "changes.parquet")))
	}

	cmd := exec.Command("duckdb", "-c", userSQL)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	return cmd.Run()
}

// ── History command ────────────────────────────────────────────────────────

func runKoseiHistory(args []string) error {
	fs := flag.NewFlagSet("kosei history", flag.ContinueOnError)
	workspaceDir := fs.String("workspace-dir", "", "workspace root")
	dataDir := fs.String("data-dir", "", "data directory")
	jsonOut := fs.Bool("json", false, "JSON output")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	_, dDir, err := koseiResolveRoots(*workspaceDir, *dataDir)
	if err != nil {
		return err
	}

	cat := koseiLoadCatalog(dDir)
	if *jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(cat)
	}

	if len(cat.Snapshots) == 0 {
		fmt.Println("No snapshots. Run: gftd kosei snapshot")
		return nil
	}

	fmt.Printf("kosei store: %s\n", dDir)
	fmt.Printf("snapshots: %d\n\n", len(cat.Snapshots))

	snaps := make([]koseiSnapshot, len(cat.Snapshots))
	copy(snaps, cat.Snapshots)
	sort.Slice(snaps, func(i, j int) bool { return snaps[i].SnapshotMs > snaps[j].SnapshotMs })

	for i, s := range snaps {
		ts := time.UnixMilli(s.SnapshotMs).UTC().Format("2006-01-02 15:04:05")
		cur := ""
		if s.SnapshotID == cat.CurrentID {
			cur = " ← current"
		}
		fmt.Printf("  %3d  %s  %s%s\n", i+1, ts, s.Summary, cur)
	}

	// Show change history from Parquet if duckdb available
	changesPath := filepath.Join(dDir, "history", "changes.parquet")
	if _, err := os.Stat(changesPath); err == nil {
		if _, err := exec.LookPath("duckdb"); err == nil {
			fmt.Printf("\nTier changes (latest 20):\n")
			sql := fmt.Sprintf(`SELECT changed_at, nanoid, old_tier, new_tier, reason, changed_by FROM read_parquet('%s') ORDER BY changed_at DESC LIMIT 20`, changesPath)
			cmd := exec.Command("duckdb", "-c", sql)
			cmd.Stdout = os.Stdout
			cmd.Stderr = os.Stderr
			_ = cmd.Run()
		}
	}

	return nil
}

// ── Change log (append to Parquet) ────────────────────────────────────────

// koseiAppendChange appends one change row to history/changes.parquet.
func koseiAppendChange(dDir string, row koseiChangeRow) error {
	if _, err := exec.LookPath("duckdb"); err != nil {
		// DuckDB not available — skip silently (history is optional)
		return nil
	}

	histDir := filepath.Join(dDir, "history")
	if err := os.MkdirAll(histDir, 0755); err != nil {
		return err
	}

	changesPath := filepath.Join(histDir, "changes.parquet")

	// Load existing rows, append new row, rewrite.
	var existing []koseiChangeRow
	if _, statErr := os.Stat(changesPath); statErr == nil {
		existing = koseiReadChangeHistory(changesPath)
	}
	existing = append(existing, row)

	return koseiWriteParquet(existing, changesPath)
}

// koseiReadChangeHistory reads all change rows from history Parquet via DuckDB.
func koseiReadChangeHistory(parquetPath string) []koseiChangeRow {
	sql := fmt.Sprintf(`SELECT changed_at, app_name, nanoid, old_tier, new_tier, reason, changed_by FROM read_parquet('%s') ORDER BY changed_at`, parquetPath)
	out, err := exec.Command("duckdb", "-json", "-c", sql).Output()
	if err != nil {
		return nil
	}
	var rows []koseiChangeRow
	json.Unmarshal(out, &rows)
	return rows
}

// koseiReadLatestSnapshot reads nanoid→tier from a snapshot Parquet file.
func koseiReadLatestSnapshot(parquetPath string) (map[string]string, error) {
	result := make(map[string]string)
	if _, err := exec.LookPath("duckdb"); err != nil {
		return result, nil
	}
	sql := fmt.Sprintf(`SELECT nanoid, tier FROM read_parquet('%s') ORDER BY snapshot_at DESC`, parquetPath)
	out, err := exec.Command("duckdb", "-json", "-c", sql).Output()
	if err != nil {
		return result, fmt.Errorf("duckdb: %w", err)
	}
	var rows []struct {
		Nanoid string `json:"nanoid"`
		Tier   string `json:"tier"`
	}
	if err := json.Unmarshal(out, &rows); err != nil {
		return result, err
	}
	for _, r := range rows {
		if _, seen := result[r.Nanoid]; !seen {
			result[r.Nanoid] = r.Tier
		}
	}
	return result, nil
}
