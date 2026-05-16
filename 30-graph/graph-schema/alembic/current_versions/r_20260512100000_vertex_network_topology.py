"""vertex_network_topology — LAN scan results as graph data.

4 vertex tables + 4 edge tables + 3 streaming MVs supporting the
`run_lan_topology` LangGraph in `pymagatama.lan_topology`. The Python
actor is the single writer; it serializes a full scan as one
vertex_network_scan + N interfaces + M hosts + K segments, then writes
the edges that close the (scan)-[:observed]->(iface)-[:in]->(segment)
<-[:in]-(host) topology.

Vertices:

* `vertex_network_scan`       — one row per scan invocation
* `vertex_network_interface`  — one row per (scan, iface) IPv4 NIC
* `vertex_network_host`       — one row per (scan, iface, ip) ARP-observed peer
* `vertex_network_segment`    — one row per (scan, subnet, gateway_mac)
                                — N rows on a single subnet = dual-router split L2

Edges (GraphAr-native, CSR via idx on src_vid):

* `edge_scan_observed_interface`  — scan -> iface
* `edge_interface_in_segment`     — iface -> segment
* `edge_host_in_segment`          — host -> segment
* `edge_segment_has_gateway`      — segment -> host (the gateway host row)

Materialized views (cardinality-bounded, MV-safe):

* `mv_network_segment_summary`        — passthrough rollup
* `mv_network_split_l2_detection`     — per (scan, subnet) → is_split_l2 flag
* `mv_network_ip_collision`           — per (scan, ip) → is_collision flag
"""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260512100000_vertex_network_topology"
down_revision = "r_20260512000000_bmc_lean_iteration"
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(
        op.get_bind(),
        _read("20260512100000_vertex_network_topology.up.sql"),
    )


def downgrade() -> None:
    execute_sql_text(
        op.get_bind(),
        _read("20260512100000_vertex_network_topology.down.sql"),
    )
