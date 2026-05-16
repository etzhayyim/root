/**
 * Historical Kysely config stub — no longer consumed.
 *
 * This file used to reference an imaginary `defineConfig` + `kysely-cli`, but
 * Kysely ships no CLI. Canonical migrations now run through Alembic and
 * SQLAlchemy (`pnpm db:migrate`). Kept throwing so any stale tooling that
 * imports it fails loud rather than silently picking up a phantom connection
 * string.
 */
throw new Error(
  'kysely.config.ts is no longer used. Run migrations via Alembic: ' +
    '`DATABASE_URL=... pnpm db:migrate`.',
);
export {};
