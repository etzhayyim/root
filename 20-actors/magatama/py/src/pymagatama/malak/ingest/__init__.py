"""malak.surveillance ingest — international LEA public-data ingestion (Phase 0 dry-run only).

Formerly `mehikari.ingest` — merged into malak namespace 2026-05-13 to align
with malak.gftd.ai (Cybercrime Intelligence Platform) and to support
international scope beyond JPN.

CRITICAL: until external counsel sign-off (see _working/malak/surveillance/COMPLIANCE-MEMO.md
blocker items B1-B5), only `--mode dry-run` is permitted. `--mode apply`
requires `--legal-approved-token <UUID>` validated against an out-of-band
signature record.

Design doc: _working/malak/surveillance/ingest/SCRAPE-DESIGN.md
"""
