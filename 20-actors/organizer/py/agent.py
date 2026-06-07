#!/usr/bin/env python3
"""organizer — kotoba-native auto-organize file commons langgraph actor (kotoba WASM cell).

ADR-2606072400 (Phase A of the substrate remediation wave, ADR-2606071800). Replaces the legacy
RisingWave-backed Worker with content-addressed, vault-isolated items on the kotoba Datom log.
Handlers over one kotoba EAVT graph:

  ingest_item    blob → content-addressed dedup (G4) → encrypted, member-signed item (G5/G6)
  classify       deterministic category/labels (rule-first, Murakumo fallback; G7) — owner-only (G2)
  apply_rules    classification → organize-rule → collection assignment (auto-organize)
  read_item      vault-isolation guard (G3) — cross-vault read refused

Hard invariants encoded so they are structurally unrepresentable, not policy:
  - content-addressed dedup (G4): itemId derives from the Blake3 of content; uploading identical
    content returns the existing item (no redundant storage, no re-upload leak).
  - vault-isolation (G3): an item belongs to exactly one vault DID; a read from another vault is
    refused.
  - no-mining (G2): classification emits category/labels for the OWNER; there is no profile / ad
    / cross-vault field — the function cannot produce one.
  - no-server-key (G6): only a member signature finalizes an upload; a server signature refused.

Classification is Murakumo-only when the rule layer is unsure (G7). R1 computes items +
classifications + collection assignments; encrypted blob storage is downstream.
"""
from __future__ import annotations

from typing import TypedDict

try:
    from kotoba import datalog, llm  # type: ignore
except ImportError:  # local dev fallback
    datalog = llm = None  # type: ignore


# --------------------------------------------------------------------------- #
# content addressing + dedup (G4)
# --------------------------------------------------------------------------- #
def content_item_id(blake3_hex: str) -> str:
    """Content-addressed item id. Identical content → identical id → dedup (G4)."""
    return f"cid.{blake3_hex[:16]}"


class Item(TypedDict, total=False):
    itemId: str
    vaultDid: str
    blake3: str
    blobRef: str
    filename: str
    contentType: str
    sizeBytes: int
    postedBy: str


def ingest_item(vault_did: str, blake3_hex: str, blob_ref: str, filename: str,
                content_type: str, size_bytes: int, posted_by: str,
                existing_items: list) -> dict:
    """Ingest an upload. If content with the same Blake3 already exists IN THIS VAULT, return the
    existing item flagged deduped (G4) — no new storage. Otherwise stage a new, unsigned item
    (member finalizes via authorize_upload, G6). Blob is referenced as an encrypted envelope (G5)."""
    item_id = content_item_id(blake3_hex)
    for it in existing_items:
        if it.get("vaultDid") == vault_did and it.get("blake3") == blake3_hex:
            return {"state": "deduped", "item": it, "deduped": True}
    return {
        "state": "staged",
        "deduped": False,
        "item": {
            "itemId": item_id,
            "vaultDid": vault_did,
            "blake3": blake3_hex,
            "blobRef": blob_ref,        # encrypted envelope ref (G5)
            "filename": filename,
            "contentType": content_type,
            "sizeBytes": int(size_bytes),
            "postedBy": posted_by,
            "postedSig": None,           # G6: unsigned until member authorizes
        },
    }


def authorize_upload(staged: dict, signature: dict) -> dict:
    """Finalize a staged upload. ONLY a member-origin signature finalizes (G6 no-server-key)."""
    if staged.get("state") != "staged":
        return {**staged, "refused": True, "reason": "upload is not in :staged state"}
    if signature.get("origin") != "member":
        return {**staged, "refused": True,
                "reason": "only a member passkey/wallet signature finalizes upload (G6 no-server-key)"}
    item = {**staged["item"], "postedSig": signature.get("ref")}
    return {"state": "stored", "item": item}


# --------------------------------------------------------------------------- #
# classification (G2 owner-only, G7 Murakumo fallback)
# --------------------------------------------------------------------------- #
# Deterministic rule layer: content-type / extension → category. Owner-facing only.
_TYPE_CATEGORY = {
    "application/pdf": "document",
    "text/plain": "document",
    "image/jpeg": "image",
    "image/png": "image",
    "video/mp4": "media",
    "audio/mpeg": "media",
    "application/zip": "archive",
}
_EXT_CATEGORY = {
    "pdf": "document", "txt": "document", "doc": "document", "docx": "document",
    "jpg": "image", "jpeg": "image", "png": "image", "heic": "image",
    "mp4": "media", "mov": "media", "mp3": "media",
    "zip": "archive", "tar": "archive", "gz": "archive",
}


def classify(item: dict) -> dict:
    """Classify an item for the OWNER's organization (G2). Rule layer first (content-type, then
    extension); Murakumo only when the rule layer is unsure (G7). Returns category/labels/source
    scoped to the item's vault (G3) — NEVER a profile or ad signal."""
    ct = (item.get("contentType") or "").lower()
    category = _TYPE_CATEGORY.get(ct)
    source = "rule"
    if category is None:
        ext = (item.get("filename", "").rsplit(".", 1)[-1] or "").lower()
        category = _EXT_CATEGORY.get(ext)
    if category is None:
        # Murakumo-only fallback (G7); deterministic 'unknown' when host absent.
        category = _murakumo_category(item) if llm is not None else "unknown"
        source = "murakumo" if llm is not None else "rule"
    labels = [category]
    if "receipt" in item.get("filename", "").lower() or "invoice" in item.get("filename", "").lower():
        labels.append("receipt")
    return {
        "itemId": item["itemId"],
        "vaultDid": item["vaultDid"],   # G3: classification stays in the item's vault
        "category": category,
        "labels": labels,
        "confidence": 1.0 if source == "rule" else 0.7,
        "source": source,
    }


def _murakumo_category(item: dict) -> str:
    try:
        out = llm.infer(  # type: ignore[union-attr]
            model="gemma3:4b",
            prompt=f"One-word file category for filename {item.get('filename','')!r} "
            f"type {item.get('contentType','')!r}: document|image|media|archive|other",
        )
        return str(out).strip().split()[0].lower() or "other"
    except Exception:
        return "unknown"


# --------------------------------------------------------------------------- #
# auto-organize rules → collection
# --------------------------------------------------------------------------- #
def apply_rules(classification: dict, rules: list) -> dict | None:
    """Match the first organize-rule whose condition fits the classification and return its
    collection assignment (auto-organize core). A rule is
    {condition: {category|label: value}, collection: id, priority: int}. Returns None if no rule
    fits (the item stays uncollected — no forced bucketing)."""
    cat = classification.get("category")
    labels = set(classification.get("labels", []))
    for r in sorted(rules, key=lambda r: -int(r.get("priority", 0))):
        cond = r.get("condition", {})
        if "category" in cond and cond["category"] != cat:
            continue
        if "label" in cond and cond["label"] not in labels:
            continue
        return {
            "itemId": classification["itemId"],
            "vaultDid": classification["vaultDid"],
            "collection": r["collection"],
            "ruleMatched": r.get("id", ""),
        }
    return None


# --------------------------------------------------------------------------- #
# vault isolation (G3)
# --------------------------------------------------------------------------- #
def read_item(item: dict, requester_vault_did: str) -> dict:
    """Read an item only if the requester owns its vault (G3 own-data-only). A cross-vault read is
    refused — there is no global/admin read path."""
    if item.get("vaultDid") != requester_vault_did:
        return {"state": "refused", "reason": "cross-vault read refused — own-data-only (G3)"}
    return {"state": "ok", "item": item}
