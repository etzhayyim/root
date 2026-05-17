// Raw query escape hatch. Used by the kagami_client.go shim during the
// incremental sqlc migration so existing call sites can run SQL directly
// against RisingWave without going through the legacy HTTP proxy.
//
// New code should prefer `sqlc`-generated typed functions instead.
package db

import (
	"context"
	"fmt"

	"github.com/jackc/pgx/v5"
)

// RawResult mirrors the legacy kagami response shape: named columns + row maps.
type RawResult struct {
	Columns []string
	Rows    []map[string]any
}

// RawQuery runs an arbitrary SQL statement against the shared RisingWave pool
// and materializes the result in (columns, []map[string]any) form.
// Returns an error if the pool cannot be opened or the statement fails to parse.
func RawQuery(ctx context.Context, sql string, args ...any) (*RawResult, error) {
	p, err := Pool(ctx)
	if err != nil {
		return nil, err
	}
	// RisingWave's extended protocol (Parse/Describe/Bind) occasionally hangs
	// on MV reads after upstream pod restarts; simple protocol is safer for
	// these ad hoc queries.
	qargs := append([]any{pgx.QueryExecModeSimpleProtocol}, args...)
	rows, err := p.Query(ctx, sql, qargs...)
	if err != nil {
		return nil, fmt.Errorf("risingwave query: %w", err)
	}
	defer rows.Close()

	fd := rows.FieldDescriptions()
	cols := make([]string, len(fd))
	for i, f := range fd {
		cols[i] = string(f.Name)
	}

	out := make([]map[string]any, 0, 16)
	for rows.Next() {
		vals, err := rows.Values()
		if err != nil {
			return nil, fmt.Errorf("risingwave scan: %w", err)
		}
		m := make(map[string]any, len(cols))
		for i, c := range cols {
			if i < len(vals) {
				m[c] = vals[i]
			}
		}
		out = append(out, m)
	}
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("risingwave rows: %w", err)
	}
	return &RawResult{Columns: cols, Rows: out}, nil
}
