"""Unit coverage for the outbox-review repository (P21 ship).

DB-touching helpers monkey-patched at the import site in the
repository module — no live RW connection needed. The handlers
themselves are thin FastAPI wrappers over the repository so they
inherit correctness from the repository tests + auth pattern proven
in test_marketing_sales_nodes.py.
"""

from __future__ import annotations

import asyncio

import pytest

from lg_yatabase.outbox import repository as repo


# ─── Fixture: monkey-patch db helpers used by the repository ──────────────

@pytest.fixture()
def patched_db(monkeypatch):
	calls: dict = {"fetch": [], "fetchval": [], "execute": []}
	fetch_rows: list[dict] = []
	fetchval_value: dict = {"value": 0}
	status_after_update: dict = {"value": "queued"}

	async def fake_fetch(query, *args):
		calls["fetch"].append((query, args))
		# When the repository re-reads the row after UPDATE, return
		# the simulated post-update status.
		if "vertex_id = $1 LIMIT 1" in query:
			return [{"status": status_after_update["value"]}]
		return list(fetch_rows)

	async def fake_fetchval(query, *args):
		calls["fetchval"].append((query, args))
		return fetchval_value["value"]

	async def fake_execute(query, *args):
		calls["execute"].append((query, args))
		return "UPDATE 1"

	monkeypatch.setattr(repo, "fetch", fake_fetch)
	monkeypatch.setattr(repo, "fetchval", fake_fetchval)
	monkeypatch.setattr(repo, "execute", fake_execute)
	return calls, fetch_rows, fetchval_value, status_after_update


# ─── list_outbox ─────────────────────────────────────────────────────────

class TestListOutbox:
	def test_default_status_filter_lands_in_sql(self, patched_db):
		calls, fetch_rows, fetchval_v, _ = patched_db
		fetch_rows.append({
			"vertex_id": "marketing:i1:acme.com:t1",
			"org_did": "gftd",
			"subject": "yatabase × Acme",
			"body_text": "Hi [[PARTNER_NAME]]…",
			"kind": "marketing-outbound",
			"status": "queued-no-recipient",
		})
		fetchval_v["value"] = 1

		result = asyncio.run(repo.list_outbox(
			status="queued-no-recipient", kind=None, limit=50,
		))
		assert result["total"] == 1
		assert result["limit"] == 50
		assert len(result["rows"]) == 1
		# SQL should include status binding + inlined LIMIT.
		sql = calls["fetch"][0][0]
		assert "status = $1" in sql
		assert "LIMIT 50" in sql
		assert "$" not in sql.split("LIMIT", 1)[1].split("\n")[0]

	def test_kind_filter_added(self, patched_db):
		calls, *_ = patched_db
		asyncio.run(repo.list_outbox(status="queued-no-recipient", kind="sales-upgrade", limit=10))
		sql = calls["fetch"][0][0]
		assert "kind = $2" in sql

	def test_limit_clamped(self, patched_db):
		calls, *_ = patched_db
		asyncio.run(repo.list_outbox(status=None, kind=None, limit=10_000))
		sql = calls["fetch"][0][0]
		assert "LIMIT 200" in sql  # clamp upper bound


# ─── approve_outbox ──────────────────────────────────────────────────────

class TestApproveOutbox:
	def test_rejects_missing_vertex_id(self, patched_db):
		out = asyncio.run(repo.approve_outbox({"recipient_email": "x@y.com"}))
		assert out["ok"] is False
		assert "vertex_id" in out["message"]

	def test_rejects_bad_email(self, patched_db):
		out = asyncio.run(repo.approve_outbox({
			"vertex_id": "v1", "recipient_email": "not-an-email",
		}))
		assert out["ok"] is False
		assert "invalid recipient_email" in out["message"]

	def test_happy_path_flips_to_queued(self, patched_db):
		calls, _, _, status_after = patched_db
		status_after["value"] = "queued"
		out = asyncio.run(repo.approve_outbox({
			"vertex_id": "marketing:i1:acme.com:t1",
			"recipient_email": "ceo@acme.com",
			"recipient_name": "Jane CEO",
		}))
		assert out["ok"] is True
		assert out["status"] == "queued"
		assert "approved" in out["message"]
		# UPDATE must have been issued with the right SET clauses.
		exec_queries = [q for q, _ in calls["execute"]]
		assert any("status = 'queued'" in q and "recipient_email = $1" in q
				   for q in exec_queries)
		# And the guard clause must be present.
		assert any("status = 'queued-no-recipient'" in q for q in exec_queries)

	def test_body_override_added_when_present(self, patched_db):
		calls, _, _, status_after = patched_db
		status_after["value"] = "queued"
		out = asyncio.run(repo.approve_outbox({
			"vertex_id": "marketing:i1:acme.com:t1",
			"recipient_email": "ceo@acme.com",
			"body_text": "Hi Jane, …",
			"subject": "yatabase × Acme (edited)",
		}))
		assert out["ok"] is True
		exec_queries = [q for q, _ in calls["execute"]]
		assert any("body_text = $4" in q for q in exec_queries)
		assert any("subject = $5" in q or "subject = $4" in q or "subject = $6" in q
				   for q in exec_queries)

	def test_no_op_when_row_already_in_another_state(self, patched_db):
		_, _, _, status_after = patched_db
		status_after["value"] = "queued-no-recipient"  # unchanged after UPDATE
		out = asyncio.run(repo.approve_outbox({
			"vertex_id": "v1", "recipient_email": "x@y.com",
		}))
		# repo treats unchanged status as "unchanged" — and `ok` reflects
		# whether the final status is 'queued'.
		assert out["ok"] is False
		assert "unchanged" in out["message"]


# ─── reject_outbox ───────────────────────────────────────────────────────

class TestRejectOutbox:
	def test_rejects_missing_vertex_id(self, patched_db):
		out = asyncio.run(repo.reject_outbox({}))
		assert out["ok"] is False
		assert "vertex_id" in out["message"]

	def test_happy_path_flips_to_rejected(self, patched_db):
		calls, _, _, status_after = patched_db
		status_after["value"] = "rejected"
		out = asyncio.run(repo.reject_outbox({"vertex_id": "v1", "reason": "off-target ICP"}))
		assert out["ok"] is True
		assert out["status"] == "rejected"
		assert "off-target ICP" in out["message"]
		exec_queries = [q for q, _ in calls["execute"]]
		assert any("status = 'rejected'" in q for q in exec_queries)
		assert any(
			"status IN ('queued-no-recipient', 'queued')" in q for q in exec_queries
		)

	def test_default_reason_used_when_blank(self, patched_db):
		calls, _, _, status_after = patched_db
		status_after["value"] = "rejected"
		asyncio.run(repo.reject_outbox({"vertex_id": "v1"}))
		# Reason arg goes into args[0] of the first execute call.
		_, args = calls["execute"][0]
		assert args[0] == "rejected by reviewer"
