"""Runtime-env Alembic replacement for news intel UDF registration."""

from __future__ import annotations

import os

from alembic import op


revision = "r_20260424170000_news_intel_udf"
down_revision = "r_20260424164100_seed_open_transit_bpmn_actors"
branch_labels = None
depends_on = None


def _link() -> str:
    host = os.environ.get("RW_UDF_SERVER_HOST", "udf-cluster.mitama-udf.svc.cluster.local:8815")
    return host if host.startswith("http") else f"http://{host}"


def _lit(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def upgrade() -> None:
    conn = op.get_bind()
    conn.exec_driver_sql("SET RW_IMPLICIT_FLUSH = true")
    conn.exec_driver_sql("DROP FUNCTION IF EXISTS news_source_credibility(varchar, boolean, boolean)")
    conn.exec_driver_sql(
        "DROP FUNCTION IF EXISTS news_intel_priority(int, int, int, double precision, double precision)"
    )
    link = _lit(_link())
    conn.exec_driver_sql(
        "CREATE FUNCTION news_source_credibility(source_type varchar, primary_source boolean, official_source boolean) "
        f"RETURNS double precision AS 'news_source_credibility' USING LINK {link}"
    )
    conn.exec_driver_sql(
        "CREATE FUNCTION news_intel_priority(evidence_count int, official_count int, corroborated_count int, "
        f"recency_hours double precision, impact double precision) RETURNS double precision AS 'news_intel_priority' USING LINK {link}"
    )
    conn.exec_driver_sql("FLUSH")


def downgrade() -> None:
    conn = op.get_bind()
    conn.exec_driver_sql("SET RW_IMPLICIT_FLUSH = true")
    conn.exec_driver_sql(
        "DROP FUNCTION IF EXISTS news_intel_priority(int, int, int, double precision, double precision)"
    )
    conn.exec_driver_sql("DROP FUNCTION IF EXISTS news_source_credibility(varchar, boolean, boolean)")
    conn.exec_driver_sql("FLUSH")
