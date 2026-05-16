"""Baseline from the live RisingWave schema on 2026-05-08.

This revision intentionally contains no DDL. The historical Kysely migration
archive was converted to Alembic for lineage, but the production RisingWave
cluster is the baseline source of truth from this point onward.
"""

from __future__ import annotations


revision = "live_risingwave_20260508"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
