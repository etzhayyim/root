// Hand-written complement to sqlc-generated files.
// Holds the process-wide pgx pool and a convenience Q(ctx) constructor.
// Kept in a separate file so `sqlc generate` never overwrites it.
package db

import (
	"context"
	"fmt"
	"net/url"
	"os"
	"strings"
	"sync"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
)

var (
	poolOnce sync.Once
	pool     *pgxpool.Pool
	poolErr  error
)

// Vultr VKE LoadBalancer per 50-infra/vultr/risingwave/deps.toml lb_ip (ADR-0048).
// Name retained for backwards compat with internal refs — this is the prod fallback
// when neither GFTD_DATABASE_URL nor DATABASE_URL is set.
const defaultLocalDatabaseURL = "postgresql://root@45.32.79.245:4566/dev?sslmode=disable"

// Pool returns a process-wide pgx pool against RisingWave.
//
// Connection string priority:
//  1. GFTD_DATABASE_URL
//  2. DATABASE_URL
//  3. built-in local port-forward DSN (127.0.0.1:14566)
//
// There is intentionally no implicit fallback to the production RisingWave
// LoadBalancer. Silent direct access to RW caused long hangs when the frontend
// was unhealthy and also bypassed the intended Hyperdrive / pgbouncer path.
func Pool(ctx context.Context) (*pgxpool.Pool, error) {
	poolOnce.Do(func() {
		dsn := os.Getenv("GFTD_DATABASE_URL")
		if dsn == "" {
			dsn = os.Getenv("DATABASE_URL")
		}
		if dsn == "" {
			dsn = defaultLocalDatabaseURL
		}
		dsn = normalizeRisingWaveDSN(dsn)
		cfg, err := pgxpool.ParseConfig(dsn)
		if err != nil {
			poolErr = fmt.Errorf("parse DATABASE_URL: %w", err)
			return
		}
		if cfg.ConnConfig.ConnectTimeout <= 0 {
			cfg.ConnConfig.ConnectTimeout = 3 * time.Second
		}
		if cfg.ConnConfig.RuntimeParams == nil {
			cfg.ConnConfig.RuntimeParams = map[string]string{}
		}
		if _, ok := cfg.ConnConfig.RuntimeParams["statement_timeout"]; !ok {
			cfg.ConnConfig.RuntimeParams["statement_timeout"] = "15000"
		}
		if _, ok := cfg.ConnConfig.RuntimeParams["idle_in_transaction_session_timeout"]; !ok {
			cfg.ConnConfig.RuntimeParams["idle_in_transaction_session_timeout"] = "5000"
		}
		if _, ok := cfg.ConnConfig.RuntimeParams["application_name"]; !ok {
			cfg.ConnConfig.RuntimeParams["application_name"] = "gftd-cli"
		}
		if cfg.MaxConns == 0 || cfg.MaxConns > 4 {
			cfg.MaxConns = 4
		}
		p, err := pgxpool.NewWithConfig(ctx, cfg)
		if err != nil {
			poolErr = fmt.Errorf("connect RisingWave: %w", err)
			return
		}
		pool = p
	})
	return pool, poolErr
}

// Q returns a *Queries handle tied to the process-wide pool.
func Q(ctx context.Context) (*Queries, error) {
	p, err := Pool(ctx)
	if err != nil {
		return nil, err
	}
	return New(p), nil
}

func normalizeRisingWaveDSN(dsn string) string {
	if strings.Contains(strings.ToLower(dsn), "sslmode=") {
		return dsn
	}
	u, err := url.Parse(dsn)
	if err != nil {
		return dsn
	}
	q := u.Query()
	q.Set("sslmode", "disable")
	u.RawQuery = q.Encode()
	return u.String()
}
