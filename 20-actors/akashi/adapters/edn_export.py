"""EDN tx-data exporter for akashi fixture records.

The exporter emits Datomic/DataScript-shaped tx maps. It is intentionally pure:
the caller decides whether to write the EDN into git, DataLad/git-annex, or a
future kotoba-git/kotoba-rad store.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any


def records_to_tx_data(records: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten validated akashi record families into tx-data maps."""
    tx: list[dict[str, Any]] = []
    dbid = -1
    for family in sorted(records):
        value = records[family]
        items = value if isinstance(value, list) else [value]
        for record in items:
            cid = _record_cid(family, record)
            entity: dict[str, Any] = {
                "db/id": dbid,
                "akashi.record/family": family,
                "akashi.record/cid": cid,
            }
            for key, child in sorted(record.items()):
                entity[f"akashi.{family}/{_kebab(key)}"] = child
            tx.append(entity)
            dbid -= 1
    return tx


def records_to_edn(records: dict[str, Any]) -> str:
    """Return deterministic EDN vector text for Datomic/DataScript import."""
    return _edn(records_to_tx_data(records)) + "\n"


def records_to_datomic_bundle(records: dict[str, Any]) -> dict[str, Any]:
    """Return a Datomic import bundle with schema and scalar tx ops.

    The DataScript/kotoba tx-data keeps source-shaped vectors and range maps.
    Datomic import is stricter: every emitted value is scalar, range maps are
    flattened into sub-attributes, and repeated scalar values are emitted as
    separate [:db/add ...] ops with :db.cardinality/many schema.
    """
    ops: list[list[Any]] = []
    attr_values: dict[str, list[Any]] = {}
    dbid = -1
    for family in sorted(records):
        value = records[family]
        items = value if isinstance(value, list) else [value]
        for record in items:
            cid = _record_cid(family, record)
            for attr, child in (
                ("akashi.record/family", family),
                ("akashi.record/cid", cid),
            ):
                _add_op(ops, attr_values, dbid, attr, child)
            for key, child in sorted(record.items()):
                attr = f"akashi.{family}/{_kebab(key)}"
                _emit_datomic_value(ops, attr_values, dbid, attr, child)
            dbid -= 1
    return {"akashi.datomic/schema": _schema(attr_values), "akashi.datomic/tx-data": ops}


def records_to_datomic_edn(records: dict[str, Any]) -> str:
    return _edn(records_to_datomic_bundle(records)) + "\n"


def _record_cid(family: str, record: dict[str, Any]) -> str:
    payload = json.dumps(record, sort_keys=True, separators=(",", ":")).encode()
    digest = hashlib.sha256(payload).hexdigest()[:32]
    return f"cid:akashi:{family}:{digest}"


def _kebab(name: str) -> str:
    return re.sub(r"(?<!^)([A-Z])", r"-\1", name).replace("_", "-").lower()


def _emit_datomic_value(
    ops: list[list[Any]],
    attr_values: dict[str, list[Any]],
    dbid: int,
    attr: str,
    value: Any,
) -> None:
    if _scalar(value):
        _add_op(ops, attr_values, dbid, attr, value)
    elif isinstance(value, list) and all(_scalar(v) for v in value):
        for item in value:
            _add_op(ops, attr_values, dbid, attr, item)
    elif isinstance(value, dict) and all(_scalar(v) for v in value.values()):
        for key, child in sorted(value.items()):
            _add_op(ops, attr_values, dbid, f"{attr}-{_kebab(str(key))}", child)
    else:
        _add_op(
            ops,
            attr_values,
            dbid,
            f"{attr}-json",
            json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        )


def _add_op(
    ops: list[list[Any]],
    attr_values: dict[str, list[Any]],
    dbid: int,
    attr: str,
    value: Any,
) -> None:
    ops.append(["db/add", dbid, attr, value])
    attr_values.setdefault(attr, []).append(value)


def _schema(attr_values: dict[str, list[Any]]) -> list[dict[str, Any]]:
    out = []
    for attr in sorted(attr_values):
        values = attr_values[attr]
        out.append(
            {
                "db/ident": attr,
                "db/valueType": _value_type(values),
                "db/cardinality": (
                    "db.cardinality/many"
                    if _cardinality_many(attr, values)
                    else "db.cardinality/one"
                ),
                **({"db/unique": "db.unique/identity"} if attr == "akashi.record/cid" else {}),
            }
        )
    return out


def _cardinality_many(attr: str, values: list[Any]) -> bool:
    per_entity_repeated = attr.endswith("/evidence-cids") or attr.endswith("/method-note-cids")
    return per_entity_repeated or attr.endswith("/region-summary") or attr.endswith("/source-cids")


def _value_type(values: list[Any]) -> str:
    sample = next((v for v in values if v is not None), "")
    if isinstance(sample, bool):
        return "db.type/boolean"
    if isinstance(sample, int) and not isinstance(sample, bool):
        return "db.type/long"
    return "db.type/string"


def _scalar(value: Any) -> bool:
    return value is None or isinstance(value, (str, int, bool))


def _edn(value: Any) -> str:
    if value is None:
        return "nil"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, str):
        if "/" in value and re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", value):
            return ":" + value
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list):
        return "[" + " ".join(_edn(v) for v in value) + "]"
    if isinstance(value, dict):
        parts: list[str] = []
        for key in sorted(value):
            parts.append(_edn_key(key))
            parts.append(_edn(value[key]))
        return "{" + " ".join(parts) + "}"
    raise TypeError(f"unsupported EDN value: {type(value)!r}")


def _edn_key(key: str) -> str:
    return ":" + key if "/" in key else json.dumps(key)


__all__ = [
    "records_to_tx_data",
    "records_to_edn",
    "records_to_datomic_bundle",
    "records_to_datomic_edn",
]
