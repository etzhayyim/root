"""Runtime-env Alembic replacement for external UDF registration."""

from __future__ import annotations

import os

from alembic import op


revision = "r_20260421170000_udf_external_python_fix_and_classify_t3"
down_revision = "r_20260421160000_udf_classify_t1"
branch_labels = None
depends_on = None


def _link() -> str:
    host = os.environ.get("RW_UDF_SERVER_HOST", "risingwave-udf.risingwave.svc:8815")
    return host if host.startswith("http") else f"http://{host}"


def _lit(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def upgrade() -> None:
    conn = op.get_bind()
    conn.exec_driver_sql("SET RW_IMPLICIT_FLUSH = true")
    for statement in [
        "DROP FUNCTION IF EXISTS cosine_similarity(double precision[], double precision[])",
        "DROP FUNCTION IF EXISTS posterior_update(double precision, double precision)",
        "DROP FUNCTION IF EXISTS segment_hash(jsonb)",
        "DROP FUNCTION IF EXISTS gmm_fit(double precision[], int)",
        "DROP FUNCTION IF EXISTS classify_t3(varchar, varchar, varchar)",
    ]:
        conn.exec_driver_sql(statement)
    link = _lit(_link())
    conn.exec_driver_sql(
        "CREATE FUNCTION cosine_similarity(a double precision[], b double precision[]) "
        f"RETURNS double precision AS 'cosine_similarity' USING LINK {link}"
    )
    conn.exec_driver_sql(
        "CREATE FUNCTION posterior_update(prior double precision, likelihood double precision) "
        f"RETURNS double precision AS 'posterior_update' USING LINK {link}"
    )
    conn.exec_driver_sql(
        "CREATE FUNCTION segment_hash(features_json jsonb) "
        f"RETURNS varchar AS 'segment_hash' USING LINK {link}"
    )
    conn.exec_driver_sql(
        "CREATE FUNCTION gmm_fit(features double precision[], k int) "
        f"RETURNS jsonb AS 'gmm_fit' USING LINK {link}"
    )
    conn.exec_driver_sql(
        "CREATE FUNCTION classify_t3(subject varchar, from_addr varchar, body_preview varchar) "
        f"RETURNS varchar AS 'classify_t3' USING LINK {link}"
    )
    conn.exec_driver_sql("FLUSH")


def downgrade() -> None:
    conn = op.get_bind()
    conn.exec_driver_sql("SET RW_IMPLICIT_FLUSH = true")
    conn.exec_driver_sql("DROP FUNCTION IF EXISTS classify_t3(varchar, varchar, varchar)")
    conn.exec_driver_sql("DROP FUNCTION IF EXISTS gmm_fit(double precision[], int)")
    conn.exec_driver_sql("DROP FUNCTION IF EXISTS segment_hash(jsonb)")
    conn.exec_driver_sql("DROP FUNCTION IF EXISTS posterior_update(double precision, double precision)")
    conn.exec_driver_sql("DROP FUNCTION IF EXISTS cosine_similarity(double precision[], double precision[])")
    conn.exec_driver_sql("FLUSH")
