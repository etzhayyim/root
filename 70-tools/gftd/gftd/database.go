// gftd database — RisingWave schema management via Kysely.
//
// Thin wrapper over `30-graph/graph-schema/scripts/migrate.ts`, which is the
// single source of truth for RisingWave DDL (see 30-graph/graph-schema/CLAUDE.md).
// The runner handles RisingWave quirks (no pg_advisory_xact_lock,
// VARCHAR(255) rejected in bookkeeping tables) — we just resolve DATABASE_URL
// and shell out.
//
// Adding a new table:
//  1. Write DDL in 30-graph/graph-schema/migrations/000N_<name>.ts
//  2. Add Row interface to 30-graph/graph-schema/src/database.ts
//  3. gftd database migrate
package main

import (
	"context"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"

	gftddb "github.com/etzhayyim/root/70-tools/gftd/gftd/db"
)

const graphSchemaRel = "30-graph/graph-schema"

// Endpoint presets pulled from 50-infra/vultr/risingwave/deps.toml
// ([risingwave_vultr] block, lb_ip field). Per ADR-0048, primary RisingWave
// moved Linode LKE → Vultr VKE LAX on 2026-04-22.
const (
	rwLocalURL = "postgres://root@127.0.0.1:14566/dev?sslmode=disable"
	rwProdURL  = "postgres://root@45.32.79.245:4566/dev"
)

// runDatabaseUp bootstraps an empty cluster by running all pending migrations
// (Kysely migrateToLatest). Idempotent — running it against a fully migrated
// cluster is a no-op.
func runDatabaseUp(args []string) error {
	return runKyselyMigrate(args, []string{"latest"})
}

// runDatabaseMigrate is the general entry point. Passes through to the
// Kysely migrator with whatever subcommand the user supplied (latest/up/
// down/to <name>/list). Default is latest.
func runDatabaseMigrate(args []string) error {
	return runKyselyMigrate(args, []string{"latest"})
}

type databaseMigrationRow struct {
	Name      string
	Timestamp string
}

func runDatabaseRepairOrder(args []string) error {
	fs := flag.NewFlagSet("database repair-order", flag.ContinueOnError)
	var (
		envName = fs.String("env", "local", "Target environment: local or prod")
		urlFlag = fs.String("url", "", "Explicit PostgreSQL URL")
		apply   = fs.Bool("apply", false, "apply missing prefix migrations and rewrite kysely_migration timestamps")
	)
	if err := fs.Parse(args); err != nil {
		return err
	}

	databaseURL, err := resolveDatabaseURL(*urlFlag, *envName)
	if err != nil {
		return err
	}
	if err := os.Setenv("DATABASE_URL", databaseURL); err != nil {
		return err
	}

	gitRoot, err := findGitRoot(".")
	if err != nil {
		return fmt.Errorf("gftd database repair-order must be run inside the gftd monorepo: %w", err)
	}
	schemaDir := filepath.Join(gitRoot, graphSchemaRel)

	fileMigrations, err := listGraphSchemaMigrations(schemaDir)
	if err != nil {
		return err
	}
	applied, err := listAppliedKyselyMigrations()
	if err != nil {
		return err
	}
	if len(applied) == 0 {
		fmt.Println("kysely_migration is empty; nothing to repair")
		return nil
	}

	appliedByName := make(map[string]databaseMigrationRow, len(applied))
	for _, row := range applied {
		appliedByName[row.Name] = row
	}

	expectedApplied := make([]string, 0, len(applied))
	for _, name := range fileMigrations {
		if _, ok := appliedByName[name]; ok {
			expectedApplied = append(expectedApplied, name)
		}
	}

	actualApplied := make([]string, 0, len(applied))
	for _, row := range applied {
		actualApplied = append(actualApplied, row.Name)
	}

	highestAppliedIdx := -1
	for i, name := range fileMigrations {
		if _, ok := appliedByName[name]; ok {
			highestAppliedIdx = i
		}
	}

	missingPrefix := make([]string, 0)
	if highestAppliedIdx >= 0 {
		for _, name := range fileMigrations[:highestAppliedIdx] {
			if _, ok := appliedByName[name]; !ok {
				missingPrefix = append(missingPrefix, name)
			}
		}
	}

	orderMismatch := len(expectedApplied) != len(actualApplied)
	if !orderMismatch {
		for i := range expectedApplied {
			if expectedApplied[i] != actualApplied[i] {
				orderMismatch = true
				break
			}
		}
	}

	fmt.Printf("database topology check: %s\n", redactURL(databaseURL))
	fmt.Printf("  applied_count: %d\n", len(applied))
	fmt.Printf("  highest_applied: %s\n", actualApplied[len(actualApplied)-1])
	if len(missingPrefix) > 0 {
		fmt.Printf("  missing_prefix: %s\n", strings.Join(missingPrefix, ", "))
	}
	if orderMismatch {
		fmt.Printf("  timestamp_order_mismatch: yes\n")
	}
	if len(missingPrefix) == 0 && !orderMismatch {
		fmt.Println("  topology: already aligned")
		return nil
	}
	if !*apply {
		fmt.Println("  action: rerun with --apply to repair migration topology")
		return nil
	}

	for _, name := range missingPrefix {
		fmt.Printf("  direct-apply: %s\n", name)
		if err := runDirectGraphMigrationUp(schemaDir, databaseURL, name); err != nil {
			return fmt.Errorf("direct apply %s: %w", name, err)
		}
	}

	if err := rewriteKyselyMigrationOrder(fileMigrations, appliedByName, missingPrefix); err != nil {
		return err
	}

	fmt.Println("  topology: repaired")
	return nil
}

// runKyselyMigrate parses shared flags (--env, --url), resolves DATABASE_URL,
// and execs `node --loader=ts-node/esm scripts/migrate.ts <migratorArgs...>`
// inside 30-graph/graph-schema. Any positional args left after flag parsing
// override the default migratorArgs (so `gftd database migrate to 0005_foo`
// becomes `scripts/migrate.ts to 0005_foo`).
func runKyselyMigrate(args []string, defaultMigratorArgs []string) error {
	fs := flag.NewFlagSet("database", flag.ContinueOnError)
	var (
		envName = fs.String("env", "local", "Target environment: local (localhost:4566) or prod (graph.etzhayyim.com LB)")
		urlFlag = fs.String("url", "", "Explicit PostgreSQL URL (overrides --env and $DATABASE_URL)")
	)
	fs.Usage = func() {
		fmt.Fprintf(os.Stderr, `gftd database — RisingWave schema management (Kysely SSoT)

USAGE:
  gftd database up                          Bootstrap: migrate to latest
  gftd database migrate [subcommand]        Incremental migration
  gftd database status                      Show applied vs pending

MIGRATE SUBCOMMANDS (pass-through to Kysely Migrator):
  latest                (default) apply all pending migrations
  up                    apply next single migration
  down                  revert last applied migration
  to <name>             migrate to specific migration (e.g. 0005_vertex_gitrepo)
  list                  show migration state (applied / pending)

FLAGS:
  --env local|prod      Resolve DATABASE_URL from deps.toml preset (default: local)
  --url <postgres-url>  Override URL explicitly

REPAIR:
  gftd database repair-order [--env prod] [--apply]
                        Detect and repair out-of-order applied migrations / timestamp drift

ENVIRONMENT:
  DATABASE_URL          Used if set and --url is not given (highest precedence after --url)

SSoT: 30-graph/graph-schema/migrations/*.ts
Runner: 30-graph/graph-schema/scripts/migrate.ts
`)
	}
	if err := fs.Parse(args); err != nil {
		return err
	}

	databaseURL, err := resolveDatabaseURL(*urlFlag, *envName)
	if err != nil {
		return err
	}

	migratorArgs := fs.Args()
	if len(migratorArgs) == 0 {
		migratorArgs = defaultMigratorArgs
	}
	if err := validateMigratorArgs(migratorArgs); err != nil {
		return err
	}

	gitRoot, err := findGitRoot(".")
	if err != nil {
		return fmt.Errorf("gftd database must be run inside the gftd monorepo: %w", err)
	}
	schemaDir := filepath.Join(gitRoot, graphSchemaRel)
	if _, err := os.Stat(filepath.Join(schemaDir, "scripts", "migrate.ts")); err != nil {
		return fmt.Errorf("kysely migrate runner not found at %s/scripts/migrate.ts: %w", graphSchemaRel, err)
	}

	nodeArgs := append([]string{"--loader=ts-node/esm", "scripts/migrate.ts"}, migratorArgs...)
	env := append(os.Environ(), "DATABASE_URL="+databaseURL)

	fmt.Fprintf(os.Stderr, "gftd database: %s → %s\n", migratorArgs[0], redactURL(databaseURL))
	return runCmdEnv(schemaDir, env, "node", nodeArgs...)
}

// resolveDatabaseURL picks the PostgreSQL URL in this precedence:
//  1. --url flag (explicit)
//  2. $DATABASE_URL env var
//  3. --env preset (local → localhost, prod → LB IP from deps.toml)
func resolveDatabaseURL(urlFlag, envName string) (string, error) {
	if urlFlag != "" {
		return urlFlag, nil
	}
	if v := os.Getenv("DATABASE_URL"); v != "" {
		return v, nil
	}
	switch envName {
	case "local":
		return rwLocalURL, nil
	case "prod":
		return rwProdURL, nil
	default:
		return "", fmt.Errorf("unknown --env %q (want: local, prod) — or pass --url / $DATABASE_URL", envName)
	}
}

// validateMigratorArgs sanity-checks positional args before we hand them to
// the TS runner (which also validates, but failing fast here yields a
// clearer error than a node stacktrace).
func validateMigratorArgs(args []string) error {
	if len(args) == 0 {
		return nil
	}
	switch args[0] {
	case "latest", "up", "down", "list":
		if len(args) > 1 {
			return fmt.Errorf("%q takes no arguments, got %v", args[0], args[1:])
		}
		return nil
	case "to":
		if len(args) < 2 {
			return fmt.Errorf("'to' requires a migration name (e.g. 'to 0005_vertex_gitrepo')")
		}
		return nil
	default:
		return fmt.Errorf("unknown migrator subcommand %q (want: latest, up, down, to <name>, list)", args[0])
	}
}

// redactURL strips the password from a postgres URL for logging.
// postgres://user:pass@host:port/db → postgres://user@host:port/db
func redactURL(url string) string {
	// Walk: find "://", then find "@" after it, then look for ":" between.
	schemeEnd := -1
	for i := 0; i+2 < len(url); i++ {
		if url[i] == ':' && url[i+1] == '/' && url[i+2] == '/' {
			schemeEnd = i + 3
			break
		}
	}
	if schemeEnd < 0 {
		return url
	}
	at := -1
	for i := schemeEnd; i < len(url); i++ {
		if url[i] == '@' {
			at = i
			break
		}
	}
	if at < 0 {
		return url
	}
	colon := -1
	for i := schemeEnd; i < at; i++ {
		if url[i] == ':' {
			colon = i
			break
		}
	}
	if colon < 0 {
		return url
	}
	return url[:colon] + url[at:]
}

func listGraphSchemaMigrations(schemaDir string) ([]string, error) {
	entries, err := os.ReadDir(filepath.Join(schemaDir, "migrations"))
	if err != nil {
		return nil, err
	}
	names := make([]string, 0, len(entries))
	for _, entry := range entries {
		if entry.IsDir() || !strings.HasSuffix(entry.Name(), ".ts") {
			continue
		}
		names = append(names, strings.TrimSuffix(entry.Name(), ".ts"))
	}
	sort.Strings(names)
	return names, nil
}

func listAppliedKyselyMigrations() ([]databaseMigrationRow, error) {
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	if _, err := gftddb.RawQuery(ctx, `SET RW_IMPLICIT_FLUSH = true`); err != nil {
		return nil, err
	}
	if _, err := gftddb.RawQuery(ctx, `FLUSH`); err != nil {
		return nil, err
	}
	res, err := gftddb.RawQuery(ctx, `SELECT name, timestamp FROM kysely_migration ORDER BY timestamp, name`)
	if err != nil {
		return nil, err
	}
	rows := make([]databaseMigrationRow, 0, len(res.Rows))
	for _, row := range res.Rows {
		rows = append(rows, databaseMigrationRow{
			Name:      strings.TrimSpace(fmt.Sprint(row["name"])),
			Timestamp: strings.TrimSpace(fmt.Sprint(row["timestamp"])),
		})
	}
	return rows, nil
}

func runDirectGraphMigrationUp(schemaDir, databaseURL, migrationName string) error {
	script := fmt.Sprintf(`import { Kysely, PostgresDialect } from 'kysely';
import pg from 'pg';
import * as migration from './migrations/%s.ts';
const { Pool } = pg;
const db = new Kysely({ dialect: new PostgresDialect({ pool: new Pool({ connectionString: %q, max: 2 }) }) });
try {
  await migration.up(db);
} finally {
  await db.destroy();
}`, migrationName, databaseURL)
	return runCmdEnv(schemaDir, append(os.Environ(), "DATABASE_URL="+databaseURL), "pnpm", "exec", "node", "--loader", "ts-node/esm", "--input-type=module", "-e", script)
}

func rewriteKyselyMigrationOrder(fileMigrations []string, appliedByName map[string]databaseMigrationRow, newlyApplied []string) error {
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	pool, err := gftddb.Pool(ctx)
	if err != nil {
		return err
	}
	if _, err := pool.Exec(ctx, `SET RW_IMPLICIT_FLUSH = true`); err != nil {
		return err
	}
	tx, err := pool.Begin(ctx)
	if err != nil {
		return err
	}
	defer tx.Rollback(ctx)

	newlyAppliedSet := make(map[string]bool, len(newlyApplied))
	for _, name := range newlyApplied {
		newlyAppliedSet[name] = true
		if _, ok := appliedByName[name]; !ok {
			appliedByName[name] = databaseMigrationRow{Name: name}
		}
	}

	baseTime := time.Date(2026, 4, 13, 0, 0, 0, 0, time.UTC)
	if row, ok := appliedByName[fileMigrations[0]]; ok {
		if ts, err := time.Parse(time.RFC3339, row.Timestamp); err == nil {
			baseTime = ts
		}
	}

	index := 0
	for _, name := range fileMigrations {
		if _, ok := appliedByName[name]; !ok {
			continue
		}
		ts := baseTime.Add(time.Duration(index) * time.Second).Format(time.RFC3339)
		if newlyAppliedSet[name] {
			if _, err := tx.Exec(ctx, `INSERT INTO kysely_migration ("name", "timestamp") VALUES ($1, $2)`, name, ts); err != nil {
				return err
			}
		} else {
			if _, err := tx.Exec(ctx, `UPDATE kysely_migration SET "timestamp" = $2 WHERE "name" = $1`, name, ts); err != nil {
				return err
			}
		}
		index++
	}
	if err := tx.Commit(ctx); err != nil {
		return err
	}
	_, err = pool.Exec(ctx, `FLUSH`)
	return err
}
