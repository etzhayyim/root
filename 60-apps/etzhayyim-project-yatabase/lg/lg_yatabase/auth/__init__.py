"""Yatabase auth surface — vertex_api_key INSERTs + tenant DID minting.

The yatabase CF Worker forwards `/xrpc/com.etzhayyim.apps.yata.{signup,invite,
revoke}` to this module. Per ADR-2605111200 the Worker no longer writes
to RisingWave directly; this pod owns vertex_api_key + vertex_org_plan
writes.

Mirrors the BMC module layout (`lg_yatabase/bmc/`):

  __init__.py    — this docstring
  db.py          — re-exports the shared asyncpg pool from bmc.db
  models.py      — Pydantic v2 request/response shapes
  repository.py  — INSERT-only writers (record-log semantics)
  handlers.py    — FastAPI router registering the XRPC routes
"""
