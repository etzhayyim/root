"""
Hazelcast → kotoba Datom log bridge for Zeebe process mining data.

Connects to the Zeebe-embedded Hazelcast ringbuffer (zeebe-hazelcast-exporter
1.4.0) and writes decoded records to vertex_zeebe_* tables in kotoba Datom log for
persistent, pod-restart-resilient process monitoring.

Architecture:
  Zeebe WAL → hazelcast-exporter → IRingbuffer<byte[]> (Hazelcast :5701)
    → this bridge (asyncio background task)
    → vertex_zeebe_{process,instance,job,incident,message} (RisingWave)

The bridge tracks its ringbuffer sequence position in vertex_zeebe_seq_pos so
restarts resume from where they left off. Ringbuffer overflow (sequence behind
head) is detected and the bridge jumps to the current head.

No protoc or grpcio-tools needed: the proto wire format is parsed with a
minimal hand-written decoder that extracts exactly the fields we need.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Any

from pymagatama.kotoba_datomic import get_kotoba_client

LOG = logging.getLogger("hazelcast_bridge")

# ─── Config ───────────────────────────────────────────────────────────────────

_HZ_CLUSTER = os.environ.get("HAZELCAST_CLUSTER", "dev")
_HZ_ADDRESS = os.environ.get(
    "HAZELCAST_ADDRESS",
    "zeebe-0.zeebe-broker.mitama-udf.svc.cluster.local:5701",
)
# zeebe-hazelcast-exporter 1.4.0 names the ringbuffer after the configured
# name (default "zeebe"), NOT "zeebe-{partitionId}". Confirmed empirically:
# `get_ringbuffer('zeebe').size()` returns 10000, `zeebe-1` returns 0.
_HZ_RINGBUFFER = os.environ.get("HAZELCAST_RINGBUFFER", "zeebe")
_POLL_SEC = float(os.environ.get("HZ_BRIDGE_POLL_SEC", "2.0"))
_BATCH_SIZE = int(os.environ.get("HZ_BRIDGE_BATCH_SIZE", "200"))
_ENABLED = os.environ.get("HZ_BRIDGE_ENABLED", "1").lower() not in ("0", "false", "off")

# ─── Minimal protobuf wire-format decoder ─────────────────────────────────────

def _read_varint(data: bytes, pos: int) -> tuple[int, int]:
    result = 0
    shift = 0
    while pos < len(data):
        b = data[pos]; pos += 1
        result |= (b & 0x7F) << shift
        if not (b & 0x80):
            break
        shift += 7
    return result, pos


def _decode_fields(data: bytes) -> dict[int, list]:
    """Decode raw protobuf bytes → {field_number: [value, ...]} mapping.

    Values are int (wire type 0/1/5) or bytes (wire type 2).
    Repeated fields accumulate into the list.
    Stops silently on malformed input.
    """
    fields: dict[int, list] = {}
    pos = 0
    n = len(data)
    while pos < n:
        try:
            tag, pos = _read_varint(data, pos)
        except Exception:
            break
        field_num = tag >> 3
        wire_type = tag & 7
        try:
            if wire_type == 0:
                val, pos = _read_varint(data, pos)
            elif wire_type == 1:
                val = int.from_bytes(data[pos : pos + 8], "little")
                pos += 8
            elif wire_type == 2:
                length, pos = _read_varint(data, pos)
                val = data[pos : pos + length]
                pos += length
            elif wire_type == 5:
                val = int.from_bytes(data[pos : pos + 4], "little")
                pos += 4
            else:
                break
            fields.setdefault(field_num, []).append(val)
        except Exception:
            break
    return fields


def _s(fields: dict, num: int) -> str:
    vals = fields.get(num, [])
    if not vals:
        return ""
    v = vals[0]
    if isinstance(v, (bytes, bytearray)):
        return v.decode("utf-8", errors="replace")
    return ""


_INT64_MAX = 9223372036854775807  # 2^63 - 1
_UINT64_MAX = 18446744073709551615  # zeebe sentinel for "unset" int64 fields


def _i(fields: dict, num: int) -> int:
    vals = fields.get(num, [])
    if not vals:
        return 0
    v = vals[0]
    if not isinstance(v, int):
        return 0
    # Zeebe uses uint64_max as a sentinel for "no value". Clamp to 0 so it fits
    # in Kotoba Datom log BIGINT (signed int64, max = 2^63-1).
    if v == _UINT64_MAX or v > _INT64_MAX:
        return 0
    return int(v)


def _b(fields: dict, num: int) -> bytes:
    vals = fields.get(num, [])
    if not vals:
        return b""
    v = vals[0]
    return v if isinstance(v, (bytes, bytearray)) else b""


# type_url suffix → our vtype string
# zeebe-hazelcast-exporter wraps each record in google.protobuf.Any with type_url
# like "type.googleapis.com/exporter_protocol.ProcessRecord"
_TYPE_URL_TO_VTYPE: dict[str, str] = {
    "exporter_protocol.ProcessRecord": "PROCESS",
    "exporter_protocol.ProcessInstanceRecord": "PROCESS_INSTANCE",
    "exporter_protocol.JobRecord": "JOB",
    "exporter_protocol.IncidentRecord": "INCIDENT",
    "exporter_protocol.MessageRecord": "MESSAGE",
}


def _parse_metadata(meta_bytes: bytes) -> dict:
    """Decode RecordMetadata embedded message (field 1 of each record)."""
    f = _decode_fields(meta_bytes)
    return {
        "key": _i(f, 3),
        "timestamp_ms": _i(f, 4),
        "intent": _s(f, 6),
    }


def _decode_record(raw: bytes) -> dict | None:
    """Decode a raw Hazelcast ringbuffer item into a structured dict.

    zeebe-hazelcast-exporter 1.4.0 serialises each WAL record as a
    google.protobuf.Any message (field 1 of the top-level item).  The Any has:
      field 1: type_url (string) — e.g. "…/exporter_protocol.ProcessRecord"
      field 2: value   (bytes)  — the actual Record proto bytes

    Returns None for record types we don't track (VARIABLE, TIMER, etc.).
    """
    if not raw:
        return None

    # Unwrap google.protobuf.Any (top-level field 1)
    top = _decode_fields(raw)
    any_bytes = _b(top, 1)
    if not any_bytes:
        return None
    any_fields = _decode_fields(any_bytes)
    type_url_raw = _b(any_fields, 1)
    record_bytes = _b(any_fields, 2)
    if not type_url_raw or not record_bytes:
        return None

    # Determine vtype from type_url suffix
    type_url = type_url_raw.decode("utf-8", errors="replace")
    tname = type_url.split("/")[-1]
    vtype = _TYPE_URL_TO_VTYPE.get(tname)
    if vtype is None:
        return None  # VARIABLE, TIMER, DEPLOYMENT, etc. — not tracked

    # Decode the actual record fields
    f = _decode_fields(record_bytes)

    # Field 1 of every record type is RecordMetadata
    meta_bytes = _b(f, 1)
    if not meta_bytes:
        return None
    meta = _parse_metadata(meta_bytes)
    intent = meta["intent"]
    ts = meta["timestamp_ms"]
    key = meta["key"]

    result: dict[str, Any] = {"vtype": vtype, "intent": intent, "ts": ts, "key": key}

    if vtype == "PROCESS":
        # ProcessRecord: 2=bpmnProcessId(str), 3=version, 4=processDefinitionKey, 5=resourceName
        result["bpmn_process_id"] = _s(f, 2)
        result["version"] = _i(f, 3)
        result["process_definition_key"] = _i(f, 4)
        result["resource_name"] = _s(f, 5)

    elif vtype == "PROCESS_INSTANCE":
        # ProcessInstanceRecord: 2=bpmnProcessId(str), 3=version, 4=processDefinitionKey,
        #   5=processInstanceKey, 6=elementId(str), 7=flowScopeKey
        # We only track root-level instances (flowScopeKey == uint64_max = no parent scope).
        flow_scope_key = _i(f, 7)
        if flow_scope_key != 18446744073709551615:
            return None  # sub-element activation, skip
        result["bpmn_process_id"] = _s(f, 2)
        result["process_definition_key"] = _i(f, 4)
        result["process_instance_key"] = _i(f, 5)

    elif vtype == "JOB":
        # JobRecord: 2=type(str), 3=worker(str), 4=retries, 5=deadline,
        #   9=elementId(str), 11=bpmnProcessId(str), 13=processInstanceKey, 14=processDefinitionKey
        result["job_type"] = _s(f, 2)
        result["retries"] = _i(f, 4)
        result["error_message"] = _s(f, 6)
        result["element_id"] = _s(f, 9)
        result["bpmn_process_id"] = _s(f, 11)
        result["process_instance_key"] = _i(f, 13)
        result["process_definition_key"] = _i(f, 14)

    elif vtype == "INCIDENT":
        # IncidentRecord: 2=errorType(str), 3=errorMessage(str), 4=bpmnProcessId(str),
        #   5=processInstanceKey, 6=elementId(str), 8=jobKey, 9=processDefinitionKey
        result["error_type"] = _s(f, 2)
        result["error_message"] = _s(f, 3)
        result["bpmn_process_id"] = _s(f, 4)
        result["process_instance_key"] = _i(f, 5)
        result["element_id"] = _s(f, 6)
        result["job_key"] = _i(f, 8)
        result["process_definition_key"] = _i(f, 9)

    elif vtype == "MESSAGE":
        # MessageRecord: 2=name(str), 3=correlationKey(str)
        result["message_name"] = _s(f, 2)
        result["correlation_key"] = _s(f, 3)

    else:
        return None  # TIMER, JOB_BATCH, VARIABLE, etc. not tracked

    return result


# ─── RisingWave writers ───────────────────────────────────────────────────────

def _iso(ts_ms: int) -> str:
    """Convert epoch-ms to ISO 8601 UTC string."""
    from datetime import datetime, timezone
    return datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def _load_seq_pos(ringbuffer: str) -> int:
    """Read next_seq from vertex_zeebe_seq_pos (0 = start from tail)."""
    try:
        row = get_kotoba_client().select_first_where(
            "vertex_zeebe_seq_pos", "ringbuffer_name", ringbuffer, columns=["next_seq"]
        )
        return int(row["next_seq"]) if row else 0
    except Exception as exc:
        LOG.warning("hazelcast_bridge: failed to load seq_pos: %s", exc)
        return 0


def _save_seq_pos(ringbuffer: str, next_seq: int) -> None:
    """Persist sequence position. Uses upsert in Kotoba Datomic log."""
    try:
        now = _iso(int(time.time() * 1000))
        get_kotoba_client().insert_row(
            "vertex_zeebe_seq_pos",
            {
                "ringbuffer_name": ringbuffer,
                "next_seq": next_seq,
                "updated_at": now,
            },
        )
    except Exception as exc:
        LOG.warning("hazelcast_bridge: failed to save seq_pos=%d: %s", next_seq, exc)


def _write_record(rec: dict) -> None:
    """Write a decoded Zeebe record to the appropriate vertex_zeebe_* table."""
    try:

        vtype = rec["vtype"]
        intent = rec["intent"]
        ts = rec["ts"]
        key = rec["key"]

            if vtype == "PROCESS":
                get_kotoba_client().insert_row(
                    "vertex_zeebe_process",
                    {
                        "process_definition_key": rec["process_definition_key"],
                        "bpmn_process_id": rec["bpmn_process_id"][:500],
                        "version": rec["version"],
                        "resource_name": rec["resource_name"][:500],
                        "intent": intent[:100],
                        "event_time_ms": ts,
                    },
                )

            elif vtype == "PROCESS_INSTANCE" and rec.get("bpmn_element_type") == "PROCESS":
                # Only store root-level events (not sub-elements)
                pik = rec["process_instance_key"]
                get_kotoba_client().insert_row(
                    "vertex_zeebe_instance",
                    {
                        "process_instance_key": pik,
                        "intent": intent[:100],
                        "event_time_ms": ts,
                        "bpmn_process_id": rec["bpmn_process_id"][:500],
                        "process_definition_key": rec["process_definition_key"],
                        "bpmn_element_type": rec["bpmn_element_type"][:100],
                    },
                )

            elif vtype == "JOB":
                get_kotoba_client().insert_row(
                    "vertex_zeebe_job",
                    {
                        "job_key": key,
                        "intent": intent[:100],
                        "event_time_ms": ts,
                        "job_type": rec["job_type"][:200],
                        "process_instance_key": rec["process_instance_key"],
                        "bpmn_process_id": rec["bpmn_process_id"][:500],
                        "element_id": rec["element_id"][:200],
                        "retries": rec["retries"],
                        "error_message": rec["error_message"][:1000],
                    },
                )

            elif vtype == "INCIDENT":
                get_kotoba_client().insert_row(
                    "vertex_zeebe_incident",
                    {
                        "incident_key": key,
                        "intent": intent[:100],
                        "event_time_ms": ts,
                        "error_type": rec["error_type"][:200],
                        "error_message": rec["error_message"][:1000],
                        "bpmn_process_id": rec["bpmn_process_id"][:500],
                        "process_instance_key": rec["process_instance_key"],
                        "element_id": rec["element_id"][:200],
                        "job_key": rec["job_key"],
                    },
                )

            elif vtype == "MESSAGE":
                get_kotoba_client().insert_row(
                    "vertex_zeebe_message",
                    {
                        "message_key": key,
                        "intent": intent[:100],
                        "event_time_ms": ts,
                        "message_name": rec["message_name"][:500],
                        "correlation_key": rec["correlation_key"][:500],
                    },
                )
    except Exception as exc:
        LOG.warning("hazelcast_bridge: write error vtype=%s key=%s: %s", rec.get("vtype"), rec.get("key"), exc)


# ─── Async bridge loop ─────────────────────────────────────────────────────────

def _hz_connect(cluster: str, address: str) -> Any:
    """Blocking: create HazelcastClient. Run in thread executor."""
    import logging as _logging
    import hazelcast  # type: ignore[import-untyped]
    # Suppress verbose hazelcast INFO logs before creating client.
    _logging.getLogger("hazelcast").setLevel(_logging.WARNING)
    return hazelcast.HazelcastClient(
        cluster_name=cluster,
        cluster_members=[address],
        connection_timeout=15.0,
    )


def _hz_read_batch(
    rb: Any, start_seq: int, batch_size: int
) -> tuple[int, int, list[bytes]]:
    """Blocking: read head/tail + a batch. Run in thread executor."""
    head = rb.head_sequence()
    tail = rb.tail_sequence()
    if tail < 0 or start_seq > tail:
        return head, tail, []
    actual_start = max(start_seq, head)
    count = min(batch_size, tail - actual_start + 1)
    if count <= 0:
        return head, tail, []
    result = rb.read_many(actual_start, count, count)
    items: list[bytes] = []
    for item in result:
        if isinstance(item, (bytes, bytearray)):
            items.append(bytes(item))
    return head, tail, items


async def run_hazelcast_bridge(stop: asyncio.Event) -> None:
    """Asyncio background task: Hazelcast ringbuffer → RisingWave."""
    if not _ENABLED:
        LOG.info("hazelcast_bridge: disabled via HZ_BRIDGE_ENABLED=0")
        return

    try:
        import hazelcast  # noqa: F401 — availability check
    except ImportError:
        LOG.warning("hazelcast_bridge: hazelcast-python-client not installed — bridge disabled")
        return

    LOG.info(
        "hazelcast_bridge: connecting cluster=%s address=%s ringbuffer=%s",
        _HZ_CLUSTER, _HZ_ADDRESS, _HZ_RINGBUFFER,
    )

    loop = asyncio.get_running_loop()
    client: Any = None

    try:
        client = await loop.run_in_executor(None, _hz_connect, _HZ_CLUSTER, _HZ_ADDRESS)
    except Exception as exc:
        LOG.warning("hazelcast_bridge: connection failed: %s — bridge disabled", exc)
        return

    try:
        rb_blocking = client.get_ringbuffer(_HZ_RINGBUFFER).blocking()
    except Exception as exc:
        LOG.warning("hazelcast_bridge: failed to get ringbuffer %r: %s", _HZ_RINGBUFFER, exc)
        client.shutdown()
        return

    # Load persisted sequence position; 0 = start from current tail (skip history)
    next_seq = await loop.run_in_executor(None, _load_seq_pos, _HZ_RINGBUFFER)

    # If starting fresh (seq=0), jump to the current tail so we only process new records
    if next_seq == 0:
        try:
            tail_seq = await loop.run_in_executor(None, rb_blocking.tail_sequence)
            next_seq = max(0, tail_seq)
            LOG.info("hazelcast_bridge: fresh start, jumping to tail seq=%d", next_seq)
        except Exception:
            pass

    LOG.info("hazelcast_bridge: ready, starting at seq=%d", next_seq)
    write_total = 0
    skip_total = 0

    try:
        while not stop.is_set():
            try:
                head, tail, items = await loop.run_in_executor(
                    None, _hz_read_batch, rb_blocking, next_seq, _BATCH_SIZE
                )

                if tail < 0:
                    await asyncio.sleep(_POLL_SEC)
                    continue

                if next_seq < head:
                    skipped = head - next_seq
                    skip_total += skipped
                    LOG.warning(
                        "hazelcast_bridge: ringbuffer overflow — skipped %d records"
                        " (was at seq=%d, head now=%d, total_skipped=%d)",
                        skipped, next_seq, head, skip_total,
                    )
                    next_seq = head

                if not items:
                    await asyncio.sleep(_POLL_SEC)
                    continue

                written = 0
                for raw in items:
                    rec = _decode_record(raw)
                    if rec is not None:
                        _write_record(rec)
                        written += 1

                next_seq += len(items)
                await loop.run_in_executor(None, _save_seq_pos, _HZ_RINGBUFFER, next_seq)
                write_total += written

                if written > 0:
                    LOG.info(
                        "hazelcast_bridge: seq=%d wrote %d/%d records (total=%d)",
                        next_seq, written, len(items), write_total,
                    )

                if len(items) < _BATCH_SIZE:
                    await asyncio.sleep(_POLL_SEC)

            except asyncio.CancelledError:
                raise
            except Exception as exc:
                LOG.warning("hazelcast_bridge: loop error: %s — retrying in 5s", exc)
                await asyncio.sleep(5.0)

    finally:
        try:
            client.shutdown()
        except Exception:
            pass
        LOG.info(
            "hazelcast_bridge: stopped (seq=%d, written=%d, skipped=%d)",
            next_seq, write_total, skip_total,
        )
