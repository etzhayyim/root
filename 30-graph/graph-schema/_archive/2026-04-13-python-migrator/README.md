# Archived: `apply-migrations.py` Python migrator

**Archived**: 2026-04-13.

## Why archived

- Two parallel tools were applying the same migrations: this Python script
  (extracting `` sql`...` `` literals out of `migrations/*.ts` with regex +
  psycopg2) and a broken `db:migrate` npm script that pointed at a non-existent
  `node_modules/kysely/dist/kysely-cli.js`.
- The Python path bypassed the Kysely `Migrator`, so it could not track which
  migrations had been applied, could not run `down`, and silently ignored any
  non-`` sql`…` `` template code in a migration.
- Per the 2026-04-13 Cypher archive directive and the `as any` blocker
  cleanup, the whole schema tool-chain is TypeScript — keeping a Python
  runner around forces a second tool-chain with no marginal benefit.

## Replacement

`scripts/migrate.ts` — runs migrations via Kysely's `Migrator` +
`FileMigrationProvider`, supports `latest` / `up` / `down` / `to` / `list`,
tracks applied migrations in `kysely_migration` / `kysely_migration_lock`,
and reads `DATABASE_URL` from the environment.

```bash
DATABASE_URL=postgres://user:pass@host:port/db pnpm db:migrate
DATABASE_URL=... pnpm db:migrate:list
DATABASE_URL=... pnpm db:migrate:down
```

## Resurrecting (don't)

If you ever need the Python path back, run:

```bash
python3 _archive/2026-04-13-python-migrator/apply-migrations.py --drop-all
```

…but please don't. If you hit a migration the Kysely runner cannot express,
extend `scripts/migrate.ts` instead of forking a second runner.
