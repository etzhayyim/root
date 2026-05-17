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

// --- Iceberg-like catalog ---

type mokutekiCatalog struct {
	FormatVersion int                   `json:"format_version"`
	TableUUID     string                `json:"table_uuid"`
	Location      string                `json:"location"`
	Schema        mokutekiIcebergSchema `json:"schema"`
	Snapshots     []mokutekiSnapshot    `json:"snapshots"`
	CurrentID     int64                 `json:"current_snapshot_id"`
}

type mokutekiIcebergSchema struct {
	Type   string                `json:"type"`
	Fields []mokutekiSchemaField `json:"fields"`
}

type mokutekiSchemaField struct {
	ID       int    `json:"id"`
	Name     string `json:"name"`
	Type     string `json:"type"`
	Required bool   `json:"required"`
}

type mokutekiSnapshot struct {
	SnapshotID int64  `json:"snapshot_id"`
	SnapshotMs int64  `json:"snapshot_ms"`
	Summary    string `json:"summary"`
	DataFile   string `json:"data_file"`
}

func (s *mokutekiSnapshot) UnmarshalJSON(data []byte) error {
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

func (s mokutekiSnapshot) MarshalJSON() ([]byte, error) {
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

// mokutekiFlatRow is the flattened row for Parquet storage.
type mokutekiFlatRow struct {
	EvaluatedAt         string  `json:"evaluated_at"`
	TotalApps           int     `json:"total_apps"`
	TotalEdges          int     `json:"total_edges"`
	TotalScore          int     `json:"total_score"`
	MaxScore            int     `json:"max_score"`
	RankName            string  `json:"rank_name"`
	LayerAScore         float64 `json:"layer_a_score"`
	LayerBScore         float64 `json:"layer_b_score"`
	LayerCScore         float64 `json:"layer_c_score"`
	LayerDScore         float64 `json:"layer_d_score"`
	Engagement          float64 `json:"engagement"`
	Competence          float64 `json:"competence"`
	Contribution        float64 `json:"contribution"`
	Growth              float64 `json:"growth"`
	Resilience          float64 `json:"resilience"`
	DSMBandwidth        float64 `json:"dsm_bandwidth"`
	GraphConnectivity   float64 `json:"graph_connectivity"`
	ShannonRedundancy   float64 `json:"shannon_redundancy"`
	HypergraphCoupling  float64 `json:"hypergraph_coupling"`
	TypeSystem          float64 `json:"type_system"`
	BayesNetPropagation float64 `json:"bayesnet_propagation"`
	CausalDAG           float64 `json:"causal_dag"`
	InfoBottleneck      float64 `json:"info_bottleneck"`
	StateSpaceDiversity float64 `json:"state_space_diversity"`
	POMDPObservation    float64 `json:"pomdp_observation"`
	ConstraintOpt       float64 `json:"constraint_opt"`
	MPCLookahead        float64 `json:"mpc_lookahead"`
	BanditSensing       float64 `json:"bandit_sensing"`
	EventSourcing       float64 `json:"event_sourcing"`
	ImmutableLog        float64 `json:"immutable_log"`
	PolicyAsCode        float64 `json:"policy_as_code"`
	TypedSchema         float64 `json:"typed_schema"`
	Attestation         float64 `json:"attestation"`
}

var mokutekiParquetSchema = mokutekiIcebergSchema{
	Type: "struct",
	Fields: []mokutekiSchemaField{
		{1, "evaluated_at", "string", true}, {2, "total_apps", "int", true},
		{3, "total_edges", "int", true}, {4, "total_score", "int", true},
		{5, "max_score", "int", true}, {6, "rank_name", "string", true},
		{7, "layer_a_score", "double", true}, {8, "layer_b_score", "double", true},
		{9, "layer_c_score", "double", true}, {10, "layer_d_score", "double", true},
		{11, "engagement", "double", true}, {12, "competence", "double", true},
		{13, "contribution", "double", true}, {14, "growth", "double", true},
		{15, "resilience", "double", true},
	},
}

func flattenMokutekiReport(r *mokutekiReport) mokutekiFlatRow {
	row := mokutekiFlatRow{
		EvaluatedAt: r.GeneratedAt, TotalApps: r.TotalApps, TotalEdges: r.TotalEdges,
		TotalScore: r.TotalScore, MaxScore: r.MaxScore, RankName: r.Rank.Name,
	}
	for _, l := range r.Layers {
		switch l.ID {
		case "A":
			row.LayerAScore = l.Score
			for _, c := range l.Components {
				switch {
				case strings.Contains(c.Name, "DSM"):
					row.DSMBandwidth = c.Score
				case strings.Contains(c.Name, "graph"):
					row.GraphConnectivity = c.Score
				case strings.Contains(c.Name, "Shannon"):
					row.ShannonRedundancy = c.Score
				case strings.Contains(c.Name, "Hypergraph"):
					row.HypergraphCoupling = c.Score
				case strings.Contains(c.Name, "type"):
					row.TypeSystem = c.Score
				}
			}
		case "B":
			row.LayerBScore = l.Score
			for _, c := range l.Components {
				switch {
				case strings.Contains(c.Name, "BayesNet"):
					row.BayesNetPropagation = c.Score
				case strings.Contains(c.Name, "Causal"):
					row.CausalDAG = c.Score
				case strings.Contains(c.Name, "bottleneck"):
					row.InfoBottleneck = c.Score
				case strings.Contains(c.Name, "State"):
					row.StateSpaceDiversity = c.Score
				}
			}
		case "C":
			row.LayerCScore = l.Score
			for _, c := range l.Components {
				switch {
				case strings.Contains(c.Name, "POMDP"):
					row.POMDPObservation = c.Score
				case strings.Contains(c.Name, "Constraint"):
					row.ConstraintOpt = c.Score
				case strings.Contains(c.Name, "MPC"):
					row.MPCLookahead = c.Score
				case strings.Contains(c.Name, "Bandit"):
					row.BanditSensing = c.Score
				}
			}
		case "D":
			row.LayerDScore = l.Score
			for _, c := range l.Components {
				switch {
				case strings.Contains(c.Name, "Event"):
					row.EventSourcing = c.Score
				case strings.Contains(c.Name, "Immutable"):
					row.ImmutableLog = c.Score
				case strings.Contains(c.Name, "Policy"):
					row.PolicyAsCode = c.Score
				case strings.Contains(c.Name, "Typed"):
					row.TypedSchema = c.Score
				case strings.Contains(c.Name, "Attestation"):
					row.Attestation = c.Score
				}
			}
		}
	}
	for _, a := range r.Axes {
		switch {
		case strings.Contains(a.Name, "Engagement"):
			row.Engagement = a.Score
		case strings.Contains(a.Name, "Competence"):
			row.Competence = a.Score
		case strings.Contains(a.Name, "Contribution"):
			row.Contribution = a.Score
		case strings.Contains(a.Name, "Growth"):
			row.Growth = a.Score
		case strings.Contains(a.Name, "Resilience"):
			row.Resilience = a.Score
		}
	}
	return row
}

// --- Store ---

func runMokutekiStore(args []string) error {
	fs := flag.NewFlagSet("mokuteki store", flag.ContinueOnError)
	workspaceDir := fs.String("workspace-dir", "", "workspace root (default: git root)")
	dataDir := fs.String("data-dir", "", "data directory (default: <workspace>/80-data/mokuteki)")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}
	if _, err := exec.LookPath("duckdb"); err != nil {
		return fmt.Errorf("duckdb not found in PATH — install: brew install duckdb")
	}
	wsRoot, err := resolveShannonRoot(*workspaceDir)
	if err != nil {
		return err
	}
	dDir := *dataDir
	if dDir == "" {
		dDir = filepath.Join(wsRoot, "80-data", "mokuteki")
	}
	snapshotsDir := filepath.Join(dDir, "snapshots")
	if err := os.MkdirAll(snapshotsDir, 0755); err != nil {
		return fmt.Errorf("mkdir: %w", err)
	}

	fmt.Fprintf(os.Stderr, "evaluating mokuteki...\n")
	report := buildMokutekiReport(wsRoot)
	row := flattenMokutekiReport(report)

	now := time.Now().UTC()
	snapName := fmt.Sprintf("snap-%s", now.Format("20060102-150405"))
	tmpJSON := filepath.Join(snapshotsDir, snapName+".json")
	parquetFile := filepath.Join(snapshotsDir, snapName+".parquet")

	jsonBytes, err := json.Marshal([]mokutekiFlatRow{row})
	if err != nil {
		return fmt.Errorf("marshal: %w", err)
	}
	if err := os.WriteFile(tmpJSON, jsonBytes, 0644); err != nil {
		return fmt.Errorf("write json: %w", err)
	}

	sql := fmt.Sprintf(
		`COPY (SELECT * FROM read_json_auto('%s')) TO '%s' (FORMAT PARQUET, COMPRESSION ZSTD);`,
		tmpJSON, parquetFile,
	)
	cmd := exec.Command("duckdb", "-c", sql)
	cmd.Stderr = os.Stderr
	if err := cmd.Run(); err != nil {
		return fmt.Errorf("duckdb parquet write: %w", err)
	}
	os.Remove(tmpJSON)

	catalog := loadOrCreateCatalog(dDir)
	snapID := now.UnixMilli()
	relPath, _ := filepath.Rel(dDir, parquetFile)
	catalog.Snapshots = append(catalog.Snapshots, mokutekiSnapshot{
		SnapshotID: snapID, SnapshotMs: snapID,
		Summary:  fmt.Sprintf("%s score=%d rank=%s apps=%d", now.Format("2006-01-02 15:04"), report.TotalScore, report.Rank.Name, report.TotalApps),
		DataFile: relPath,
	})
	catalog.CurrentID = snapID
	if err := saveCatalog(dDir, catalog); err != nil {
		return fmt.Errorf("save catalog: %w", err)
	}

	fmt.Fprintf(os.Stderr, "stored: %s (score=%d, rank=%s)\n", relPath, report.TotalScore, report.Rank.Name)
	fmt.Fprintf(os.Stderr, "snapshots: %d total\n", len(catalog.Snapshots))
	return nil
}

// --- Query ---

func runMokutekiQuery(args []string) error {
	fs := flag.NewFlagSet("mokuteki query", flag.ContinueOnError)
	workspaceDir := fs.String("workspace-dir", "", "workspace root (default: git root)")
	dataDir := fs.String("data-dir", "", "data directory (default: <workspace>/80-data/mokuteki)")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}
	if _, err := exec.LookPath("duckdb"); err != nil {
		return fmt.Errorf("duckdb not found in PATH — install: brew install duckdb")
	}
	wsRoot, err := resolveShannonRoot(*workspaceDir)
	if err != nil {
		return err
	}
	dDir := *dataDir
	if dDir == "" {
		dDir = filepath.Join(wsRoot, "80-data", "mokuteki")
	}
	snapshotsGlob := filepath.Join(dDir, "snapshots", "*.parquet")

	userSQL := strings.Join(fs.Args(), " ")
	if userSQL == "" {
		userSQL = fmt.Sprintf(`
SELECT evaluated_at, total_score, rank_name, total_apps,
  round(layer_a_score,1) AS "A:構造",
  round(layer_b_score,1) AS "B:不確実性",
  round(layer_c_score,1) AS "C:制御",
  round(layer_d_score,1) AS "D:実装",
  round(engagement,1) AS "参与",
  round(competence,1) AS "能力",
  round(contribution,1) AS "貢献",
  round(growth,1) AS "成長",
  round(resilience,1) AS "回復"
FROM read_parquet('%s')
ORDER BY evaluated_at DESC LIMIT 20`, snapshotsGlob)
	} else {
		userSQL = strings.ReplaceAll(userSQL, "$TABLE", fmt.Sprintf("read_parquet('%s')", snapshotsGlob))
	}

	cmd := exec.Command("duckdb", "-c", userSQL)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	return cmd.Run()
}

// --- History ---

func runMokutekiHistory(args []string) error {
	fs := flag.NewFlagSet("mokuteki history", flag.ContinueOnError)
	workspaceDir := fs.String("workspace-dir", "", "workspace root (default: git root)")
	dataDir := fs.String("data-dir", "", "data directory (default: <workspace>/80-data/mokuteki)")
	jsonOut := fs.Bool("json", false, "output as JSON")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}
	wsRoot, err := resolveShannonRoot(*workspaceDir)
	if err != nil {
		return err
	}
	dDir := *dataDir
	if dDir == "" {
		dDir = filepath.Join(wsRoot, "80-data", "mokuteki")
	}
	catalog := loadOrCreateCatalog(dDir)
	if *jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(catalog)
	}
	if len(catalog.Snapshots) == 0 {
		fmt.Println("no snapshots. Run: gftd mokuteki store")
		return nil
	}
	fmt.Printf("mokuteki store: %s\n", dDir)
	fmt.Printf("snapshots: %d\n\n", len(catalog.Snapshots))
	snaps := make([]mokutekiSnapshot, len(catalog.Snapshots))
	copy(snaps, catalog.Snapshots)
	sort.Slice(snaps, func(i, j int) bool { return snaps[i].SnapshotMs > snaps[j].SnapshotMs })
	for i, s := range snaps {
		ts := time.UnixMilli(s.SnapshotMs).UTC().Format("2006-01-02 15:04:05")
		cur := ""
		if s.SnapshotID == catalog.CurrentID {
			cur = " ← current"
		}
		fmt.Printf("  %3d  %s  %s%s\n", i+1, ts, s.Summary, cur)
	}
	return nil
}

// --- Catalog helpers ---

func catalogPath(dDir string) string {
	return filepath.Join(dDir, "catalog.json")
}

func loadOrCreateCatalog(dDir string) *mokutekiCatalog {
	data, err := os.ReadFile(catalogPath(dDir))
	if err != nil {
		return &mokutekiCatalog{FormatVersion: 1, TableUUID: "mokuteki-local-001", Location: dDir, Schema: mokutekiParquetSchema}
	}
	var cat mokutekiCatalog
	if err := json.Unmarshal(data, &cat); err != nil {
		return &mokutekiCatalog{FormatVersion: 1, TableUUID: "mokuteki-local-001", Location: dDir, Schema: mokutekiParquetSchema}
	}
	return &cat
}

func saveCatalog(dDir string, cat *mokutekiCatalog) error {
	data, err := json.MarshalIndent(cat, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(catalogPath(dDir), data, 0644)
}
