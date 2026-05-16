"""keiei_apqc_isco_binding — bind keiei roles to APQC PCF L1 + ISCO-08.

Adds 5 columns to vertex_keiei_role (apqc_pcf_l1_primary, apqc_pcf_l1_set,
isco_08_unit_group, isco_08_label, isco_08_skill_level) + 2 edge tables
(edge_keiei_role_owns_apqc, edge_keiei_role_isco).

Source SSoT:
  - APQC PCF L1: deps.toml [[cohort_actors]] cohort-apqc-{1..13} (jp locale)
  - ISCO-08:     vertex_occupation (ILO ISCO-08, 393 unit groups)

ADRs: 2605101200 (this layer), 0025 (APQC/BPMN projector), 0026 (cohort lineage).
"""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260510020200_keiei_apqc_isco_binding"
down_revision = "r_20260510020100_seed_keiei_cxo"
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260510020200_keiei_apqc_isco_binding.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260510020200_keiei_apqc_isco_binding.down.sql"))
