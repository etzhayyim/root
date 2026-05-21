"""Shared durable state helpers for ingest workers.

The canonical domain facts stay in source-specific vertex/edge tables. This
module only writes the cross-domain orchestration spine documented in
`90-docs/260425-ingest-orchestration-zeebe-python-k8s-mcp-design.md`.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any

from pymagatama.db_sync import sync_cursor
from pymagatama.db_sync import _validate_sql_guard

INGEST_ACTOR_DID = "did:web:ingest.etzhayyim.com"


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _slug(value: str) -> str:
    out = []
    for ch in value.lower():
        if ch.isalnum():
            out.append(ch)
        else:
            out.append("-")
    return "-".join(part for part in "".join(out).split("-") if part)[:160] or "unknown"


def stable_run_id(ingest_family: str, source_id: str, mode: str, input_json: str = "") -> str:
    payload = "|".join((ingest_family, source_id, mode, input_json or "", now_iso()))
    digest = hashlib.blake2b(payload.encode("utf-8"), digest_size=6).hexdigest()
    return f"{_slug(ingest_family)}-{_slug(source_id)}-{_slug(mode)}-{digest}"


def run_vertex_id(run_id: str) -> str:
    return f"at://{INGEST_ACTOR_DID}/ai.gftd.apps.ingest.run/{_slug(run_id)}"


def cursor_vertex_id(ingest_family: str, source_id: str, shard_key: str) -> str:
    slug = _slug(f"{ingest_family}-{source_id}-{shard_key}")
    return f"at://{INGEST_ACTOR_DID}/ai.gftd.apps.ingest.cursor/{slug}"


def artifact_vertex_id(run_id: str, artifact_kind: str, uri: str) -> str:
    digest = hashlib.blake2b(uri.encode("utf-8"), digest_size=6).hexdigest()
    slug = _slug(f"{run_id}-{artifact_kind}-{digest}")
    return f"at://{INGEST_ACTOR_DID}/ai.gftd.apps.ingest.artifact/{slug}"


def _psql_enabled() -> bool:
    """Religious-corp port: always False — RW path disabled per ADR-2605172000.

    Per gate (a) §1 P4 of `/90-docs/2605211949-gate-a-execution-checklist.md`,
    the psql/_psql_exec fallback is removed. All ingest persistence falls back
    to the non-psql code paths (BeliefStore + local SQLite via ingest spine).
    Vendor pymagatama keeps the RW branch on its repo.
    """
    return False


def _sql_string(value: str) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def _sql_value(value: Any, *, date_value: bool = False, bigint: bool = False) -> str:
    if value is None:
        if bigint:
            return "CAST(NULL AS BIGINT)"
        if date_value:
            return "CAST(NULL AS DATE)"
        return "NULL"
    if date_value:
        if isinstance(value, date):
            value = value.isoformat()
        return f"DATE {_sql_string(str(value))}"
    if bigint:
        return f"CAST({int(value)} AS BIGINT)"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, int):
        return str(value)
    return _sql_string(str(value))


def _psql_exec(sql: str, *, ignore_duplicate: bool = False, flush: bool = False) -> None:
    _validate_sql_guard(sql)
    env = {**os.environ, "PGCONNECT_TIMEOUT": os.environ.get("PGCONNECT_TIMEOUT", "10")}
    timeout_sec = int(os.environ.get("RW_PSQL_TIMEOUT_SEC", "240"))
    allow_flush = os.environ.get("RW_ALLOW_FLUSH", "0").lower() in ("1", "true", "on", "yes")
    command_sql = f"{sql.rstrip().rstrip(';')}; FLUSH;" if flush and allow_flush else sql
    proc = subprocess.run(
        ["psql", os.environ["RW_URL"], "-v", "ON_ERROR_STOP=1", "-Atc", command_sql],
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout_sec,
        check=False,
    )
    if proc.returncode == 0:
        return
    msg = f"{proc.stderr}\n{proc.stdout}".lower()
    if ignore_duplicate and ("duplicate" in msg or "primary key" in msg or "already exists" in msg):
        return
    raise RuntimeError((proc.stderr or proc.stdout or "psql failed").strip())


def _insert_or_ignore(cur: Any, sql: str, params: tuple[Any, ...]) -> None:
    try:
        cur.execute(sql, params)
    except Exception as e:  # noqa: BLE001
        message = str(e).lower()
        if "duplicate" in message or "primary key" in message or "already exists" in message:
            return
        raise


@dataclass(frozen=True)
class IngestRun:
    ingest_family: str
    source_id: str
    mode: str = "delta"
    run_id: str = ""
    status: str = "planned"
    zeebe_process_instance_key: str | None = None
    bpmn_process_id: str | None = None
    requested_by: str | None = None
    input_json: str | None = None

    def with_run_id(self) -> "IngestRun":
        if self.run_id:
            return self
        return IngestRun(
            ingest_family=self.ingest_family,
            source_id=self.source_id,
            mode=self.mode,
            run_id=stable_run_id(self.ingest_family, self.source_id, self.mode, self.input_json or ""),
            status=self.status,
            zeebe_process_instance_key=self.zeebe_process_instance_key,
            bpmn_process_id=self.bpmn_process_id,
            requested_by=self.requested_by,
            input_json=self.input_json,
        )


@dataclass(frozen=True)
class IngestArtifact:
    run_id: str
    artifact_kind: str
    source_id: str
    uri: str
    sha256: str | None = None
    byte_size: int | None = None
    record_count: int | None = None
    props: dict[str, Any] | None = None


def upsert_run(run: IngestRun) -> str:
    """Create a run row if missing, then update mutable progress fields."""
    run = run.with_run_id()
    vid = run_vertex_id(run.run_id)
    now = now_iso()
    if _psql_enabled():
        _psql_exec(
            """
            INSERT INTO vertex_ingest_run (
              vertex_id, _seq, created_date, sensitivity_ord, owner_did,
              run_id, ingest_family, source_id, mode, status,
              zeebe_process_instance_key, bpmn_process_id, started_at,
              requested_by, input_json, created_at, updated_at
            ) VALUES (
              {vertex_id}, CAST(NULL AS BIGINT), {created_date}, CAST(0 AS BIGINT), {owner_did},
              {run_id}, {ingest_family}, {source_id}, {mode}, {status},
              {zeebe_process_instance_key}, {bpmn_process_id}, {started_at},
              {requested_by}, {input_json}, {created_at}, {updated_at}
            )
            """.format(
                vertex_id=_sql_value(vid),
                created_date=_sql_value(today(), date_value=True),
                owner_did=_sql_value(INGEST_ACTOR_DID),
                run_id=_sql_value(run.run_id),
                ingest_family=_sql_value(run.ingest_family),
                source_id=_sql_value(run.source_id),
                mode=_sql_value(run.mode),
                status=_sql_value(run.status),
                zeebe_process_instance_key=_sql_value(run.zeebe_process_instance_key),
                bpmn_process_id=_sql_value(run.bpmn_process_id),
                started_at=_sql_value(now),
                requested_by=_sql_value(run.requested_by),
                input_json=_sql_value(run.input_json),
                created_at=_sql_value(now),
                updated_at=_sql_value(now),
            ),
            ignore_duplicate=True,
        )
        _psql_exec(
            """
            UPDATE vertex_ingest_run
               SET status = {status},
                   zeebe_process_instance_key = COALESCE({zeebe_process_instance_key}, zeebe_process_instance_key),
                   bpmn_process_id = COALESCE({bpmn_process_id}, bpmn_process_id),
                   requested_by = COALESCE({requested_by}, requested_by),
                   input_json = COALESCE({input_json}, input_json),
                   updated_at = {updated_at}
             WHERE vertex_id = {vertex_id}
            """.format(
                status=_sql_value(run.status),
                zeebe_process_instance_key=_sql_value(run.zeebe_process_instance_key),
                bpmn_process_id=_sql_value(run.bpmn_process_id),
                requested_by=_sql_value(run.requested_by),
                input_json=_sql_value(run.input_json),
                updated_at=_sql_value(now),
                vertex_id=_sql_value(vid),
            ),
            flush=True,
        )
        return vid
    with sync_cursor() as cur:
        _insert_or_ignore(
            cur,
            """
            INSERT INTO vertex_ingest_run (
              vertex_id, _seq, created_date, sensitivity_ord, owner_did,
              run_id, ingest_family, source_id, mode, status,
              zeebe_process_instance_key, bpmn_process_id, started_at,
              requested_by, input_json, created_at, updated_at
            )
            VALUES (
              %s, CAST(NULL AS BIGINT), CAST(%s AS DATE), CAST(0 AS BIGINT), %s,
              %s, %s, %s, %s, %s,
              %s, %s, %s,
              %s, %s, %s, %s
            )
            """,
            (
                vid,
                today(),
                INGEST_ACTOR_DID,
                run.run_id,
                run.ingest_family,
                run.source_id,
                run.mode,
                run.status,
                run.zeebe_process_instance_key,
                run.bpmn_process_id,
                now,
                run.requested_by,
                run.input_json,
                now,
                now,
            ),
        )
        cur.execute(
            """
            UPDATE vertex_ingest_run
               SET status = %s,
                   zeebe_process_instance_key = COALESCE(%s, zeebe_process_instance_key),
                   bpmn_process_id = COALESCE(%s, bpmn_process_id),
                   requested_by = COALESCE(%s, requested_by),
                   input_json = COALESCE(%s, input_json),
                   updated_at = %s
             WHERE vertex_id = %s
            """,
            (
                run.status,
                run.zeebe_process_instance_key,
                run.bpmn_process_id,
                run.requested_by,
                run.input_json,
                now,
                vid,
            ),
        )
    return vid


def mark_run_finished(
    run_id: str,
    *,
    status: str,
    records_read: int | None = None,
    records_written: int | None = None,
    records_skipped: int | None = None,
    error_count: int | None = None,
    last_error: str | None = None,
    output: dict[str, Any] | None = None,
) -> None:
    vid = run_vertex_id(run_id)
    if _psql_enabled():
        _psql_exec(
            """
            UPDATE vertex_ingest_run
               SET status = {status},
                   finished_at = {finished_at},
                   records_read = COALESCE({records_read}, records_read),
                   records_written = COALESCE({records_written}, records_written),
                   records_skipped = COALESCE({records_skipped}, records_skipped),
                   error_count = COALESCE({error_count}, error_count),
                   last_error = COALESCE({last_error}, last_error),
                   output_json = COALESCE({output_json}, output_json),
                   updated_at = {updated_at}
             WHERE vertex_id = {vertex_id}
            """.format(
                status=_sql_value(status),
                finished_at=_sql_value(now_iso()),
                records_read=_sql_value(records_read, bigint=True),
                records_written=_sql_value(records_written, bigint=True),
                records_skipped=_sql_value(records_skipped, bigint=True),
                error_count=_sql_value(error_count, bigint=True),
                last_error=_sql_value(last_error),
                output_json=_sql_value(
                    json.dumps(output, sort_keys=True, separators=(",", ":"))
                    if output is not None
                    else None
                ),
                updated_at=_sql_value(now_iso()),
                vertex_id=_sql_value(vid),
            ),
            flush=True,
        )
        return
    with sync_cursor() as cur:
        cur.execute(
            """
            UPDATE vertex_ingest_run
               SET status = %s,
                   finished_at = %s,
                   records_read = COALESCE(%s, records_read),
                   records_written = COALESCE(%s, records_written),
                   records_skipped = COALESCE(%s, records_skipped),
                   error_count = COALESCE(%s, error_count),
                   last_error = COALESCE(%s, last_error),
                   output_json = COALESCE(%s, output_json),
                   updated_at = %s
             WHERE vertex_id = %s
            """,
            (
                status,
                now_iso(),
                records_read,
                records_written,
                records_skipped,
                error_count,
                last_error,
                json.dumps(output, sort_keys=True, separators=(",", ":")) if output is not None else None,
                now_iso(),
                vid,
            ),
        )


def upsert_cursor(
    *,
    ingest_family: str,
    source_id: str,
    shard_key: str,
    cursor_value: str | None = None,
    high_watermark: str | None = None,
    content_hash: str | None = None,
    locked_by_run_id: str | None = None,
    lock_expires_at: str | None = None,
    status: str | None = None,
    last_error: str | None = None,
) -> str:
    vid = cursor_vertex_id(ingest_family, source_id, shard_key)
    now = now_iso()
    cursor_hash = (
        hashlib.sha256(cursor_value.encode("utf-8")).hexdigest()
        if cursor_value is not None
        else None
    )
    if _psql_enabled():
        _psql_exec(
            """
            INSERT INTO vertex_ingest_cursor (
              vertex_id, _seq, created_date, sensitivity_ord, owner_did,
              ingest_family, source_id, shard_key, cursor_value, cursor_hash,
              high_watermark, content_hash, updated_at, locked_by_run_id,
              lock_expires_at, status, fail_count, last_error
            ) VALUES (
              {vertex_id}, CAST(NULL AS BIGINT), {created_date}, CAST(0 AS BIGINT), {owner_did},
              {ingest_family}, {source_id}, {shard_key}, {cursor_value}, {cursor_hash},
              {high_watermark}, {content_hash}, {updated_at}, {locked_by_run_id},
              {lock_expires_at}, {status}, CAST(0 AS BIGINT), {last_error}
            )
            """.format(
                vertex_id=_sql_value(vid),
                created_date=_sql_value(today(), date_value=True),
                owner_did=_sql_value(INGEST_ACTOR_DID),
                ingest_family=_sql_value(ingest_family),
                source_id=_sql_value(source_id),
                shard_key=_sql_value(shard_key),
                cursor_value=_sql_value(cursor_value),
                cursor_hash=_sql_value(cursor_hash),
                high_watermark=_sql_value(high_watermark),
                content_hash=_sql_value(content_hash),
                updated_at=_sql_value(now),
                locked_by_run_id=_sql_value(locked_by_run_id),
                lock_expires_at=_sql_value(lock_expires_at),
                status=_sql_value(status),
                last_error=_sql_value(last_error),
            ),
            ignore_duplicate=True,
        )
        _psql_exec(
            """
            UPDATE vertex_ingest_cursor
               SET cursor_value = COALESCE({cursor_value}, cursor_value),
                   cursor_hash = COALESCE({cursor_hash}, cursor_hash),
                   high_watermark = COALESCE({high_watermark}, high_watermark),
                   content_hash = COALESCE({content_hash}, content_hash),
                   updated_at = {updated_at},
                   locked_by_run_id = COALESCE({locked_by_run_id}, locked_by_run_id),
                   lock_expires_at = COALESCE({lock_expires_at}, lock_expires_at),
                   status = COALESCE({status}, status),
                   last_error = COALESCE({last_error}, last_error)
             WHERE vertex_id = {vertex_id}
            """.format(
                cursor_value=_sql_value(cursor_value),
                cursor_hash=_sql_value(cursor_hash),
                high_watermark=_sql_value(high_watermark),
                content_hash=_sql_value(content_hash),
                updated_at=_sql_value(now),
                locked_by_run_id=_sql_value(locked_by_run_id),
                lock_expires_at=_sql_value(lock_expires_at),
                status=_sql_value(status),
                last_error=_sql_value(last_error),
                vertex_id=_sql_value(vid),
            ),
            flush=True,
        )
        return vid
    with sync_cursor() as cur:
        _insert_or_ignore(
            cur,
            """
            INSERT INTO vertex_ingest_cursor (
              vertex_id, _seq, created_date, sensitivity_ord, owner_did,
              ingest_family, source_id, shard_key, cursor_value, cursor_hash,
              high_watermark, content_hash, updated_at, locked_by_run_id,
              lock_expires_at, status, fail_count, last_error
            )
            VALUES (
              %s, CAST(NULL AS BIGINT), CAST(%s AS DATE), CAST(0 AS BIGINT), %s,
              %s, %s, %s, %s, %s,
              %s, %s, %s, %s,
              %s, %s, CAST(0 AS BIGINT), %s
            )
            """,
            (
                vid,
                today(),
                INGEST_ACTOR_DID,
                ingest_family,
                source_id,
                shard_key,
                cursor_value,
                cursor_hash,
                high_watermark,
                content_hash,
                now,
                locked_by_run_id,
                lock_expires_at,
                status,
                last_error,
            ),
        )
        cur.execute(
            """
            UPDATE vertex_ingest_cursor
               SET cursor_value = COALESCE(%s, cursor_value),
                   cursor_hash = COALESCE(%s, cursor_hash),
                   high_watermark = COALESCE(%s, high_watermark),
                   content_hash = COALESCE(%s, content_hash),
                   updated_at = %s,
                   locked_by_run_id = COALESCE(%s, locked_by_run_id),
                   lock_expires_at = COALESCE(%s, lock_expires_at),
                   status = COALESCE(%s, status),
                   last_error = COALESCE(%s, last_error)
             WHERE vertex_id = %s
            """,
            (
                cursor_value,
                cursor_hash,
                high_watermark,
                content_hash,
                now,
                locked_by_run_id,
                lock_expires_at,
                status,
                last_error,
                vid,
            ),
        )
    return vid


def upsert_artifact(artifact: IngestArtifact) -> str:
    vid = artifact_vertex_id(artifact.run_id, artifact.artifact_kind, artifact.uri)
    now = now_iso()
    props = json.dumps(artifact.props, sort_keys=True, separators=(",", ":")) if artifact.props else None
    if _psql_enabled():
        _psql_exec(
            """
            INSERT INTO vertex_ingest_artifact (
              vertex_id, _seq, created_date, sensitivity_ord, owner_did,
              run_id, artifact_kind, source_id, uri, sha256,
              byte_size, record_count, created_at, props
            ) VALUES (
              {vertex_id}, CAST(NULL AS BIGINT), {created_date}, CAST(0 AS BIGINT), {owner_did},
              {run_id}, {artifact_kind}, {source_id}, {uri}, {sha256},
              {byte_size}, {record_count}, {created_at}, {props}
            )
            """.format(
                vertex_id=_sql_value(vid),
                created_date=_sql_value(today(), date_value=True),
                owner_did=_sql_value(INGEST_ACTOR_DID),
                run_id=_sql_value(artifact.run_id),
                artifact_kind=_sql_value(artifact.artifact_kind),
                source_id=_sql_value(artifact.source_id),
                uri=_sql_value(artifact.uri),
                sha256=_sql_value(artifact.sha256),
                byte_size=_sql_value(artifact.byte_size, bigint=True),
                record_count=_sql_value(artifact.record_count, bigint=True),
                created_at=_sql_value(now),
                props=_sql_value(props),
            ),
            ignore_duplicate=True,
            flush=True,
        )
        return vid
    with sync_cursor() as cur:
        _insert_or_ignore(
            cur,
            """
            INSERT INTO vertex_ingest_artifact (
              vertex_id, _seq, created_date, sensitivity_ord, owner_did,
              run_id, artifact_kind, source_id, uri, sha256,
              byte_size, record_count, created_at, props
            )
            VALUES (
              %s, CAST(NULL AS BIGINT), CAST(%s AS DATE), CAST(0 AS BIGINT), %s,
              %s, %s, %s, %s, %s,
              %s, %s, %s, %s
            )
            """,
            (
                vid,
                today(),
                INGEST_ACTOR_DID,
                artifact.run_id,
                artifact.artifact_kind,
                artifact.source_id,
                artifact.uri,
                artifact.sha256,
                artifact.byte_size,
                artifact.record_count,
                now,
                props,
            ),
        )
    return vid
