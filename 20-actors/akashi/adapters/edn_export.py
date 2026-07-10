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


def _record_cid(family: str, record: dict[str, Any]) -> str:
    payload = json.dumps(record, sort_keys=True, separators=(",", ":")).encode()
    digest = hashlib.sha256(payload).hexdigest()[:32]
    return f"cid:akashi:{family}:{digest}"


def _kebab(name: str) -> str:
    return re.sub(r"(?<!^)([A-Z])", r"-\1", name).replace("_", "-").lower()


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


__all__ = ["records_to_tx_data", "records_to_edn"]
