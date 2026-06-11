"""evidence.py — 助 (tasuke) evidence preservation: chain-of-custody, PII-by-reference.

A cybercrime victim's evidence (screenshots, email headers, chat logs, transaction records) is
exactly the kind of 要配慮 / identifying material the charter says must live ENCRYPTED (G6,
ADR-2605181100). So this module never stores the plaintext. For each item it records:

  - kind          ∈ ontology :evidence-kinds
  - envelope-ref  the com.etzhayyim.encrypted.* CID where the ciphertext lives (G6)
  - sha256        a chain-of-custody integrity hash, so the victim can later prove the item is
                  byte-for-byte unchanged since capture (the thing a court/officer cares about)
  - captured-at   when it was preserved

`preserve(...)` REFUSES (raises) any attempt to attach a plaintext PII blob — the only
representable form is the encrypted-envelope ref + the hash. That is the G6 invariant in code.

Stdlib only (hashlib).
"""

from __future__ import annotations

import hashlib
from typing import Any

EVIDENCE_KINDS = (
    "url", "email-header", "screenshot", "chat-log", "transaction-record", "wallet-address",
    "phone-number", "account-id", "file-hash", "audio", "other",
)

# field names that would smuggle plaintext PII into the clear record — refused (G6).
_PLAINTEXT_PII_FIELDS = (":evidence/plaintext", ":evidence/raw", ":evidence/pii", "plaintext", "raw-bytes")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _kw(v: Any) -> str:
    return str(v or "").lstrip(":").split("/")[-1].lower()


def preserve(item: dict) -> dict:
    """Preserve one evidence item as an encrypted-by-reference, hash-anchored record.

    `item` carries :evidence/kind, :evidence/envelope-ref (the ciphertext CID), and EITHER an
    :evidence/sha256 (already computed client-side) or :evidence/bytes (raw bytes to hash here
    and then discard — they are never stored). Raises on a G6 violation or an unknown kind.
    """
    for f in _PLAINTEXT_PII_FIELDS:
        if f in item:
            raise ValueError(
                f"G6: plaintext PII field {f!r} is unrepresentable — evidence lives encrypted "
                "(com.etzhayyim.encrypted.*); store an envelope-ref + a hash only"
            )
    kind = _kw(item.get(":evidence/kind", ""))
    if kind not in EVIDENCE_KINDS:
        raise ValueError(f"unknown evidence kind {kind!r} (allowed: {EVIDENCE_KINDS})")
    ref = str(item.get(":evidence/envelope-ref", "")).strip()
    if not ref:
        raise ValueError("G6: an evidence item needs an encrypted envelope-ref (the ciphertext CID)")

    digest = str(item.get(":evidence/sha256", "")).strip()
    if not digest:
        raw = item.get(":evidence/bytes")
        if raw is None:
            raise ValueError("evidence needs either :evidence/sha256 or :evidence/bytes to hash")
        if isinstance(raw, str):
            raw = raw.encode("utf-8")
        digest = sha256_hex(raw)   # hash then discard the bytes (never stored)

    return {
        ":evidence/id": item.get(":evidence/id", "?"),
        ":evidence/case": item.get(":evidence/case", "?"),
        ":evidence/kind": ":" + kind,
        ":evidence/envelope-ref": ref,
        ":evidence/sha256": digest,
        ":evidence/captured-at": int(item.get(":evidence/captured-at", 0) or 0),
    }


def index(items: list[dict]) -> list[dict]:
    """Preserve a batch → the 証拠目録 (evidence index) rows, in capture order."""
    rows = [preserve(it) for it in items]
    return sorted(rows, key=lambda r: int(r.get(":evidence/captured-at", 0)))


def custody_intact(record: dict, current_bytes: bytes) -> bool:
    """Verify an item's chain of custody: does the current ciphertext still match the recorded hash?"""
    return sha256_hex(current_bytes) == record.get(":evidence/sha256", "")
