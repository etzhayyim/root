"""Optional Iceberg sink migration.

The current production graph storage path is RisingWave Hummock only. Iceberg /
Nessie sinks are disabled by default and only created when explicitly requested.
"""

from __future__ import annotations

import os

from alembic import op


revision = "r_0003_iceberg_sinks"
down_revision = "r_0002_streaming_mv"
branch_labels = None
depends_on = None


SINKS = [
    ("sink_follow_out_degree", "mv_follow_out_degree", "mv_follow_out_degree", "upsert", "src_vid", False),
    ("sink_follow_in_degree", "mv_follow_in_degree", "mv_follow_in_degree", "upsert", "dst_vid", False),
    ("sink_post_like_count", "mv_post_like_count", "mv_post_like_count", "upsert", "dst_vid", False),
    ("sink_actor_suggestions", "mv_actor_suggestions", "mv_actor_suggestions", "upsert", "vertex_id", False),
    ("sink_actor_by_did", "mv_actor_by_did", "mv_actor_by_did", "upsert", "did", False),
    ("sink_feed_timeline", "mv_feed_timeline", "mv_feed_timeline", "append-only", "post_id", True),
    ("sink_cc_domain_page_count", "mv_cc_domain_page_count", "mv_cc_domain_page_count", "upsert", "domain_did", False),
    ("sink_cc_domain_out_degree", "mv_cc_domain_out_degree", "mv_cc_domain_out_degree", "upsert", "domain_did", False),
    ("sink_cc_domain_in_degree", "mv_cc_domain_in_degree", "mv_cc_domain_in_degree", "upsert", "domain_did", False),
    ("sink_cc_domain_coverage", "mv_cc_domain_coverage", "mv_cc_domain_coverage", "upsert", "domain_did", False),
    ("sink_vertex_domain", "vertex_domain", "vertex_domain", "upsert", "vertex_id", False),
    ("sink_vertex_page", "vertex_page", "vertex_page", "upsert", "vertex_id", False),
    ("sink_vertex_actor", "vertex_actor", "vertex_actor", "upsert", "vertex_id", False),
    ("sink_vertex_profile", "vertex_profile", "vertex_profile", "upsert", "vertex_id", False),
    ("sink_edge_hosts_page", "edge_hosts_page", "edge_hosts_page", "upsert", "src_vid,dst_vid,edge_id", False),
    ("sink_edge_links_to", "edge_links_to", "edge_links_to", "upsert", "src_vid,dst_vid,edge_id", False),
    ("sink_edge_links_to_domain", "edge_links_to_domain", "edge_links_to_domain", "upsert", "src_vid,dst_vid,edge_id", False),
]


def _env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} is required for Iceberg sink migration")
    return value


def _iceberg_enabled() -> bool:
    return os.environ.get("ENABLE_ICEBERG_SINKS", "").lower() in {"1", "true", "yes", "on"}


def _lit(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _with_clause(name: str, sink_type: str, primary_key: str, force_append_only: bool) -> str:
    lines = [
        ("connector", "iceberg"),
        ("type", sink_type),
        ("primary_key", primary_key),
    ]
    if force_append_only:
        lines.append(("force_append_only", "true"))
    lines.extend(
        [
            ("catalog.type", "rest"),
            ("catalog.uri", _env("NESSIE_URI")),
            ("catalog.name", "graphar"),
            ("database.name", "graphar"),
            ("table.name", name),
            ("warehouse.path", f"s3://{_env('S3_BUCKET')}/iceberg/warehouse"),
            ("s3.endpoint", _env("S3_ENDPOINT")),
            ("s3.region", _env("S3_REGION")),
            ("s3.access.key", _env("S3_ACCESS_KEY")),
            ("s3.secret.key", _env("S3_SECRET_KEY")),
            ("s3.path.style.access", "true"),
            ("create_table_if_not_exists", "true"),
        ]
    )
    body = ",\n".join(f"  {key} = {_lit(value)}" for key, value in lines)
    return f"WITH (\n{body}\n)"


def upgrade() -> None:
    conn = op.get_bind()
    conn.exec_driver_sql("SET RW_IMPLICIT_FLUSH = true")
    if not _iceberg_enabled():
        return
    for sink_name, source_name, table_name, sink_type, primary_key, force_append_only in SINKS:
        conn.exec_driver_sql(
            f"CREATE SINK IF NOT EXISTS {sink_name} FROM {source_name}\n"
            f"{_with_clause(table_name, sink_type, primary_key, force_append_only)}"
        )
    conn.exec_driver_sql("FLUSH")


def downgrade() -> None:
    conn = op.get_bind()
    conn.exec_driver_sql("SET RW_IMPLICIT_FLUSH = true")
    if not _iceberg_enabled():
        return
    for sink_name, *_ in reversed(SINKS):
        conn.exec_driver_sql(f"DROP SINK IF EXISTS {sink_name}")
    conn.exec_driver_sql("FLUSH")
