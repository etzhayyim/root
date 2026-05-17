// Row-count helper backed by RisingWave `rw_catalog.rw_table_stats`.
// See ADR-0033: ad-hoc COUNT(*) is prohibited on tables ≥ 10M rows.
package db

import (
	"context"
	"fmt"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

// CountFromStats returns the live key count for a base table from
// `rw_catalog.rw_table_stats` (LSM compaction byproduct, O(1) meta lookup).
// Returns 0 + error if the table is not found or stats are not yet populated.
func CountFromStats(ctx context.Context, pool *pgxpool.Pool, table string) (int64, error) {
	if pool == nil {
		return 0, fmt.Errorf("nil pool")
	}
	const q = `
		SELECT s.total_key_count
		FROM rw_catalog.rw_tables t
		JOIN rw_catalog.rw_table_stats s ON t.id = s.id
		WHERE t.name = $1
	`
	var n int64
	if err := pool.QueryRow(ctx, q, pgx.QueryExecModeSimpleProtocol, table).Scan(&n); err != nil {
		return 0, fmt.Errorf("rw_table_stats %s: %w", table, err)
	}
	return n, nil
}
