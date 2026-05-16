# SQLMesh Models

Put managed analytical views and materialized views here as SQLMesh models.
Alembic owns base-table DDL; SQLMesh owns rebuildable derived models.

The project config reads RisingWave connection pieces from `RISINGWAVE_*`
environment variables. Keep `DATABASE_URL` for Alembic and SQLAlchemy scripts.
