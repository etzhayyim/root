package main

import (
	"context"
	"flag"
	"fmt"
	"os"
	"strings"
	"time"

	"github.com/etzhayyim/root/70-tools/gftd/gftd/db"
)

func runDepsMV(args []string) error {
	fs := flag.NewFlagSet("deps mv", flag.ContinueOnError)
	apply := fs.Bool("apply", false, "apply the generated DDL to RisingWave")
	format := fs.String("format", "sql", "output format: sql or text")
	timeoutSec := fs.Int("timeout-sec", 20, "database timeout in seconds when --apply is set")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}
	if *timeoutSec <= 0 {
		return fmt.Errorf("--timeout-sec must be greater than 0")
	}

	statements := depsMVStatements()
	switch strings.ToLower(strings.TrimSpace(*format)) {
	case "sql":
		if err := printDepsMVSQL(os.Stdout, statements); err != nil {
			return err
		}
	case "text":
		fmt.Printf("deps_mv:\n")
		fmt.Printf("  views: %d\n", len(statements))
		fmt.Printf("  generated_from: risingwave vertex_* / edge_* tables only\n")
		for _, stmt := range statements {
			fmt.Printf("  - %s\n", depsMVName(stmt))
		}
	default:
		return fmt.Errorf("unknown --format: %s", *format)
	}

	if !*apply {
		return nil
	}

	ctx, cancel := context.WithTimeout(context.Background(), time.Duration(*timeoutSec)*time.Second)
	defer cancel()
	pool, err := db.Pool(ctx)
	if err != nil {
		return err
	}
	for _, stmt := range statements {
		if _, err := pool.Exec(ctx, stmt); err != nil {
			return fmt.Errorf("apply %s: %w", depsMVName(stmt), err)
		}
	}
	fmt.Fprintf(os.Stderr, "applied %d deps materialized view(s)\n", len(statements))
	return nil
}

func printDepsMVSQL(w *os.File, statements []string) error {
	if _, err := fmt.Fprintln(w, "-- gftd deps mv"); err != nil {
		return err
	}
	if _, err := fmt.Fprintln(w, "-- Generated from RisingWave vertex_/edge_ tables. No JSON snapshot dependency."); err != nil {
		return err
	}
	for _, stmt := range statements {
		if _, err := fmt.Fprintln(w); err != nil {
			return err
		}
		if _, err := fmt.Fprintf(w, "%s;\n", stmt); err != nil {
			return err
		}
	}
	return nil
}

func depsMVStatements() []string {
	return []string{
		strings.TrimSpace(`
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_deps_component_live AS
WITH components AS (
  SELECT did AS component_did FROM vertex_actor WHERE did IS NOT NULL
  UNION
  SELECT did AS component_did FROM vertex_actor_manifest WHERE did IS NOT NULL
  UNION
  SELECT did AS component_did FROM vertex_capability WHERE did IS NOT NULL
  UNION
  SELECT did AS component_did FROM vertex_raci WHERE did IS NOT NULL
  UNION
  SELECT repo AS component_did FROM vertex_did WHERE repo LIKE 'did:%'
  UNION
  SELECT src_vid AS component_did FROM edge_capability WHERE src_vid LIKE 'did:%'
  UNION
  SELECT dst_vid AS component_did FROM edge_capability WHERE dst_vid LIKE 'did:%'
  UNION
  SELECT src_vid AS component_did FROM edge_governance WHERE src_vid LIKE 'did:%'
  UNION
  SELECT dst_vid AS component_did FROM edge_governance WHERE dst_vid LIKE 'did:%'
  UNION
  SELECT src_vid AS component_did FROM edge_requires WHERE src_vid LIKE 'did:%'
  UNION
  SELECT dst_vid AS component_did FROM edge_requires WHERE dst_vid LIKE 'did:%'
  UNION
  SELECT src_vid AS component_did FROM edge_in_app WHERE src_vid LIKE 'did:%'
  UNION
  SELECT dst_vid AS component_did FROM edge_in_app WHERE dst_vid LIKE 'did:%'
  UNION
  SELECT src_vid AS component_did FROM edge_in_project WHERE src_vid LIKE 'did:%'
  UNION
  SELECT dst_vid AS component_did FROM edge_in_project WHERE dst_vid LIKE 'did:%'
),
actor_meta AS (
  SELECT
    did AS component_did,
    MAX(COALESCE(display_name, name, handle)) AS component_name,
    MAX(COALESCE(project, '')) AS project,
    MAX(COALESCE(nanoid, '')) AS nanoid
  FROM vertex_actor
  WHERE did IS NOT NULL
  GROUP BY did
),
manifest_meta AS (
  SELECT
    did AS component_did,
    MAX(COALESCE(display_name, name)) AS component_name,
    MAX(COALESCE(nanoid, '')) AS nanoid
  FROM vertex_actor_manifest
  WHERE did IS NOT NULL
  GROUP BY did
),
capability_vertex_counts AS (
  SELECT did AS component_did, COUNT(*)::bigint AS capability_vertex_count
  FROM vertex_capability
  WHERE did IS NOT NULL
  GROUP BY did
),
capability_edge_counts AS (
  SELECT component_did, COUNT(*)::bigint AS capability_edge_count
  FROM (
    SELECT src_vid AS component_did FROM edge_capability WHERE src_vid LIKE 'did:%'
    UNION ALL
    SELECT dst_vid AS component_did FROM edge_capability WHERE dst_vid LIKE 'did:%'
  ) s
  GROUP BY component_did
),
raci_counts AS (
  SELECT did AS component_did, COUNT(*)::bigint AS raci_count
  FROM vertex_raci
  WHERE did IS NOT NULL
  GROUP BY did
),
governance_vertex_counts AS (
  SELECT component_did, SUM(governance_vertex_count)::bigint AS governance_vertex_count
  FROM (
    SELECT repo AS component_did, COUNT(*)::bigint AS governance_vertex_count
    FROM vertex_governance
    WHERE repo LIKE 'did:%'
    GROUP BY repo
    UNION ALL
    SELECT repo AS component_did, COUNT(*)::bigint AS governance_vertex_count
    FROM vertex_governance_contract
    WHERE repo LIKE 'did:%'
    GROUP BY repo
  ) s
  GROUP BY component_did
),
governance_edge_counts AS (
  SELECT component_did, COUNT(*)::bigint AS governance_edge_count
  FROM (
    SELECT src_vid AS component_did FROM edge_governance WHERE src_vid LIKE 'did:%'
    UNION ALL
    SELECT dst_vid AS component_did FROM edge_governance WHERE dst_vid LIKE 'did:%'
  ) s
  GROUP BY component_did
),
dependency_edge_counts AS (
  SELECT component_did, COUNT(*)::bigint AS dependency_edge_count
  FROM (
    SELECT src_vid AS component_did FROM edge_requires WHERE src_vid LIKE 'did:%'
    UNION ALL
    SELECT dst_vid AS component_did FROM edge_requires WHERE dst_vid LIKE 'did:%'
  ) s
  GROUP BY component_did
),
resource_flow_counts AS (
  SELECT component_did, COUNT(*)::bigint AS resource_flow_count
  FROM (
    SELECT src_vid AS component_did FROM edge_in_app WHERE src_vid LIKE 'did:%'
    UNION ALL
    SELECT dst_vid AS component_did FROM edge_in_app WHERE dst_vid LIKE 'did:%'
    UNION ALL
    SELECT src_vid AS component_did FROM edge_in_project WHERE src_vid LIKE 'did:%'
    UNION ALL
    SELECT dst_vid AS component_did FROM edge_in_project WHERE dst_vid LIKE 'did:%'
  ) s
  GROUP BY component_did
)
SELECT
  c.component_did,
  COALESCE(a.component_name, m.component_name, c.component_did) AS component_name,
  COALESCE(a.project, '') AS project,
  COALESCE(a.nanoid, m.nanoid, '') AS nanoid,
  COALESCE(cv.capability_vertex_count, 0) AS capability_vertex_count,
  COALESCE(ce.capability_edge_count, 0) AS capability_edge_count,
  COALESCE(r.raci_count, 0) AS raci_count,
  COALESCE(gv.governance_vertex_count, 0) AS governance_vertex_count,
  COALESCE(ge.governance_edge_count, 0) AS governance_edge_count,
  COALESCE(dep.dependency_edge_count, 0) AS dependency_edge_count,
  COALESCE(flow.resource_flow_count, 0) AS resource_flow_count,
  CASE
    WHEN COALESCE(cv.capability_vertex_count, 0)
       + COALESCE(ce.capability_edge_count, 0)
       + COALESCE(r.raci_count, 0)
       + COALESCE(gv.governance_vertex_count, 0)
       + COALESCE(ge.governance_edge_count, 0)
       + COALESCE(dep.dependency_edge_count, 0)
       + COALESCE(flow.resource_flow_count, 0) = 0
    THEN true
    ELSE false
  END AS isolated
FROM components c
LEFT JOIN actor_meta a ON a.component_did = c.component_did
LEFT JOIN manifest_meta m ON m.component_did = c.component_did
LEFT JOIN capability_vertex_counts cv ON cv.component_did = c.component_did
LEFT JOIN capability_edge_counts ce ON ce.component_did = c.component_did
LEFT JOIN raci_counts r ON r.component_did = c.component_did
LEFT JOIN governance_vertex_counts gv ON gv.component_did = c.component_did
LEFT JOIN governance_edge_counts ge ON ge.component_did = c.component_did
LEFT JOIN dependency_edge_counts dep ON dep.component_did = c.component_did
LEFT JOIN resource_flow_counts flow ON flow.component_did = c.component_did`),
		strings.TrimSpace(`
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_deps_summary_live AS
SELECT
  COUNT(*)::bigint AS total_components,
  SUM(CASE WHEN capability_vertex_count + capability_edge_count > 0 THEN 1 ELSE 0 END)::bigint AS capability_ready_components,
  SUM(CASE WHEN governance_vertex_count + governance_edge_count > 0 THEN 1 ELSE 0 END)::bigint AS governance_ready_components,
  SUM(CASE WHEN raci_count > 0 THEN 1 ELSE 0 END)::bigint AS raci_ready_components,
  SUM(CASE WHEN dependency_edge_count > 0 THEN 1 ELSE 0 END)::bigint AS dependency_ready_components,
  SUM(CASE WHEN resource_flow_count > 0 THEN 1 ELSE 0 END)::bigint AS resource_flow_ready_components,
  SUM(CASE WHEN isolated THEN 1 ELSE 0 END)::bigint AS isolated_components,
  ROUND(
    100.0 * SUM(CASE WHEN capability_vertex_count + capability_edge_count > 0 THEN 1 ELSE 0 END)
    / NULLIF(COUNT(*), 0),
    1
  ) AS capability_coverage,
  ROUND(
    100.0 * SUM(CASE WHEN governance_vertex_count + governance_edge_count > 0 THEN 1 ELSE 0 END)
    / NULLIF(COUNT(*), 0),
    1
  ) AS governance_coverage,
  ROUND(
    100.0 * SUM(CASE WHEN raci_count > 0 THEN 1 ELSE 0 END)
    / NULLIF(COUNT(*), 0),
    1
  ) AS raci_coverage,
  ROUND(
    100.0 * SUM(CASE WHEN dependency_edge_count > 0 THEN 1 ELSE 0 END)
    / NULLIF(COUNT(*), 0),
    1
  ) AS dependency_coverage,
  ROUND(
    100.0 * SUM(CASE WHEN resource_flow_count > 0 THEN 1 ELSE 0 END)
    / NULLIF(COUNT(*), 0),
    1
  ) AS resource_flow_coverage,
  ROUND(
    GREATEST(
      0,
      (
        (
          100.0 * SUM(CASE WHEN capability_vertex_count + capability_edge_count > 0 THEN 1 ELSE 0 END)
          / NULLIF(COUNT(*), 0)
        ) +
        (
          100.0 * SUM(CASE WHEN governance_vertex_count + governance_edge_count > 0 THEN 1 ELSE 0 END)
          / NULLIF(COUNT(*), 0)
        ) +
        (
          100.0 * SUM(CASE WHEN raci_count > 0 THEN 1 ELSE 0 END)
          / NULLIF(COUNT(*), 0)
        ) +
        (
          100.0 * SUM(CASE WHEN dependency_edge_count > 0 THEN 1 ELSE 0 END)
          / NULLIF(COUNT(*), 0)
        ) +
        (
          100.0 * SUM(CASE WHEN resource_flow_count > 0 THEN 1 ELSE 0 END)
          / NULLIF(COUNT(*), 0)
        )
      ) / 5.0 -
      (
        100.0 * SUM(CASE WHEN isolated THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0)
      ) * 0.2
    ),
    1
  ) AS overall_score
FROM mv_deps_component_live`),
	}
}

func depsMVName(stmt string) string {
	fields := strings.Fields(stmt)
	for i := 0; i < len(fields)-1; i++ {
		if strings.EqualFold(fields[i], "VIEW") {
			name := fields[i+1]
			name = strings.Trim(name, `"`)
			if strings.EqualFold(name, "IF") && i+4 < len(fields) {
				return strings.Trim(fields[i+4], `"`)
			}
			return name
		}
	}
	return "unknown_view"
}
