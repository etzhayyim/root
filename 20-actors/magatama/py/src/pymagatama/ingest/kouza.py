"""Kouza read-only account aggregation handlers for BPMN + Zeebe."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import time
import uuid
from typing import Any

from pymagatama.db_sync import sync_cursor

NS = "ai.gftd.apps.kouza"
ACTOR = "did:web:kouza.gftd.ai"
READ_SCOPES = {"accounts.read", "transactions.read", "documents.read", "balances.read"}


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _str(value: Any) -> str:
    return "" if value is None else str(value)


def _int(value: Any, label: str = "value") -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{label} must be an integer")


def _hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()[:16]


def _require_did(value: Any, label: str) -> str:
    text = _str(value)
    if not text.startswith("did:"):
        raise ValueError(f"{label} must be a DID")
    return text


def _require_ref(value: Any, label: str) -> str:
    text = _str(value)
    if not text:
        raise ValueError(f"{label} required")
    return text


def _record_did(owner_did: str, collection: str, rkey: str) -> str:
    return f"{owner_did}|{collection}|{rkey}"


def _next_seq(table: str) -> int:
    with sync_cursor() as cur:
        cur.execute(f"SELECT COALESCE(MAX(_seq), 0) + 1 AS seq FROM {table}")
        row = cur.fetchone()
        return int(row[0] if row else 1)


def _execute(sql: str, params: tuple[Any, ...] = ()) -> int:
    with sync_cursor() as cur:
        cur.execute(sql, params)
        return int(cur.rowcount or 0)


def _fetch_all(sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with sync_cursor() as cur:
        cur.execute(sql, params)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in (cur.fetchall() or [])]


def _scopes(scopes: Any) -> list[str]:
    if not isinstance(scopes, list) or not scopes:
        raise ValueError("scopes required")
    out = []
    for scope in scopes:
        text = _str(scope)
        if text not in READ_SCOPES:
            raise ValueError(f"scope not allowed: {text}")
        out.append(text)
    return sorted(set(out))


def register_connection(ownerDid: str = "", institutionName: str = "", institutionKind: str = "", providerKey: str = "", scopes: Any = None, credentialVaultRef: str = "", consentExpiresAt: str = "", **_: Any) -> dict[str, Any]:
    owner = _require_did(ownerDid, "ownerDid")
    if not institutionName or not institutionKind or not providerKey:
        return {"error": "institutionName, institutionKind, providerKey required"}
    allowed = _scopes(scopes)
    rkey = f"conn-{_hash({'ownerDid': owner, 'institutionName': institutionName, 'institutionKind': institutionKind, 'providerKey': providerKey})}"
    did = _record_did(owner, f"{NS}.institutionConnection", rkey)
    seq = _next_seq("vertex_atrecord_kouza_institution_connection")
    now = now_iso()
    _execute(
        """INSERT INTO vertex_atrecord_kouza_institution_connection
        (vertex_id, _seq, owner_did, rkey, institution_name, institution_kind, provider_key,
         credential_vault_ref, scopes_json, consent_expires_at, status, created_at, updated_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'active',%s,%s)
        ON CONFLICT (vertex_id) DO UPDATE SET credential_vault_ref=EXCLUDED.credential_vault_ref,
        scopes_json=EXCLUDED.scopes_json, consent_expires_at=EXCLUDED.consent_expires_at, status='active', updated_at=EXCLUDED.updated_at""",
        (did, seq, owner, rkey, institutionName, institutionKind, providerKey, credentialVaultRef or None, json.dumps(allowed), consentExpiresAt or None, now, now),
    )
    return {"connectionDid": did, "status": "active"}


def create_financial_account(ownerDid: str = "", connectionDid: str = "", externalAccountIdHash: str = "", maskedAccountNumber: str = "", displayName: str = "", accountKind: str = "checking", currency: str = "JPY", currentBalanceMinor: Any = None, balanceAsOf: str = "", kaikeiAccountDid: str = "", status: str = "active", **_: Any) -> dict[str, Any]:
    did = _ensure_financial_account(locals())
    return {"financialAccountDid": did}


def _ensure_financial_account(input: dict[str, Any]) -> str:
    owner = _require_did(input.get("ownerDid"), "ownerDid")
    connection = _require_ref(input.get("connectionDid"), "connectionDid")
    external_hash = _str(input.get("externalAccountIdHash")) or _hash({"connectionDid": connection, "maskedAccountNumber": input.get("maskedAccountNumber"), "displayName": input.get("displayName"), "accountKind": input.get("accountKind"), "currency": input.get("currency")})
    rkey = f"acct-{external_hash}"
    did = _record_did(owner, f"{NS}.financialAccount", rkey)
    now = now_iso()
    _execute(
        """INSERT INTO vertex_atrecord_kouza_financial_account
        (vertex_id, _seq, owner_did, rkey, connection_did, external_account_id_hash, masked_account_number,
         display_name, account_kind, currency, current_balance_minor, balance_as_of, kaikei_account_did, status, created_at, updated_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (vertex_id) DO UPDATE SET masked_account_number=COALESCE(EXCLUDED.masked_account_number, vertex_atrecord_kouza_financial_account.masked_account_number),
        display_name=COALESCE(EXCLUDED.display_name, vertex_atrecord_kouza_financial_account.display_name),
        current_balance_minor=COALESCE(EXCLUDED.current_balance_minor, vertex_atrecord_kouza_financial_account.current_balance_minor),
        balance_as_of=COALESCE(EXCLUDED.balance_as_of, vertex_atrecord_kouza_financial_account.balance_as_of),
        kaikei_account_did=COALESCE(EXCLUDED.kaikei_account_did, vertex_atrecord_kouza_financial_account.kaikei_account_did),
        status=EXCLUDED.status, updated_at=EXCLUDED.updated_at""",
        (did, _next_seq("vertex_atrecord_kouza_financial_account"), owner, rkey, connection, external_hash, input.get("maskedAccountNumber") or None, input.get("displayName") or None, input.get("accountKind") or "checking", input.get("currency") or "JPY", input.get("currentBalanceMinor"), input.get("balanceAsOf") or None, input.get("kaikeiAccountDid") or None, input.get("status") or "active", now, now),
    )
    return did


def sync_connection(ownerDid: str = "", connectionDid: str = "", **_: Any) -> dict[str, Any]:
    owner = ownerDid if _str(ownerDid).startswith("did:") else ACTOR
    connection = _require_ref(connectionDid, "connectionDid")
    sync = _create_sync_run(owner, connection, "succeeded", {"accounts": 0, "txns": 0, "docs": 0})
    return {"syncRunDid": sync, "status": "succeeded", "accountsImported": 0, "transactionsImported": 0, "documentsImported": 0}


def _create_sync_run(owner: str, connection: str, status: str, counts: dict[str, int], error: str = "") -> str:
    rkey = f"sync-{uuid.uuid4().hex[:14]}"
    did = _record_did(owner, f"{NS}.syncRun", rkey)
    now = now_iso()
    _execute(
        """INSERT INTO vertex_atrecord_kouza_sync_run
        (vertex_id, _seq, owner_did, rkey, connection_did, adapter_key, started_at, finished_at,
         accounts_imported, transactions_imported, documents_imported, status, error_message, created_at)
        VALUES (%s,%s,%s,%s,%s,'manual-statement',%s,%s,%s,%s,%s,%s,%s,%s)""",
        (did, _next_seq("vertex_atrecord_kouza_sync_run"), owner, rkey, connection, now, now, counts.get("accounts", 0), counts.get("txns", 0), counts.get("docs", 0), status, error or None, now),
    )
    _execute("UPDATE vertex_atrecord_kouza_institution_connection SET last_sync_run_did=%s, updated_at=%s WHERE vertex_id=%s", (did, now, connection))
    return did


def import_statement(ownerDid: str = "", connectionDid: str = "", financialAccountDid: str = "", rows: Any = None, **_: Any) -> dict[str, Any]:
    owner = _require_did(ownerDid, "ownerDid")
    connection = _require_ref(connectionDid, "connectionDid")
    account = _require_ref(financialAccountDid, "financialAccountDid")
    if not isinstance(rows, list) or not rows:
        return {"error": "rows required"}
    imported = skipped = derived = 0
    for raw in rows:
        row = dict(raw or {})
        posted = _require_ref(row.get("postedAt"), "postedAt")
        amount = _int(row.get("amountMinor"), "amountMinor")
        currency = _str(row.get("currency")) or "JPY"
        external_id = _str(row.get("externalTxnId")) or _hash({"financialAccountDid": account, **row})
        rkey = f"txn-{_hash({'financialAccountDid': account, 'externalTxnId': external_id})}"
        did = _record_did(owner, f"{NS}.externalTransaction", rkey)
        inserted = _execute(
            """INSERT INTO vertex_atrecord_kouza_external_transaction
            (vertex_id, _seq, owner_did, rkey, financial_account_did, external_txn_id, posted_at, value_at,
             amount_minor, currency, counterparty_name, description, category_hint, document_did, accounting_status, created_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NULL,'pending',%s)
            ON CONFLICT (vertex_id) DO NOTHING""",
            (did, _next_seq("vertex_atrecord_kouza_external_transaction"), owner, rkey, account, external_id, posted, row.get("valueAt") or None, amount, currency, row.get("counterpartyName") or None, row.get("description") or None, row.get("categoryHint") or None, now_iso()),
        )
        if inserted == 0:
            skipped += 1
            continue
        imported += 1
        if _derive_kaikei(owner, account, {**row, "externalTxnId": external_id, "postedAt": posted, "amountMinor": amount, "currency": currency}, did):
            derived += 1
    sync = _create_sync_run(owner, connection, "succeeded", {"accounts": 0, "txns": imported, "docs": 0})
    return {"syncRunDid": sync, "imported": imported, "skipped": skipped, "kaikeiDerived": derived}


def import_statement_csv(csvText: str = "", **kwargs: Any) -> dict[str, Any]:
    if not csvText.strip():
        return {"error": "csvText required"}
    reader = csv.DictReader(io.StringIO(csvText.lstrip("\ufeff")))
    rows = [dict(row) for row in reader]
    return import_statement(rows=rows, **kwargs)


def _derive_kaikei(owner: str, account_did: str, row: dict[str, Any], external_did: str) -> str | None:
    if row.get("currency") != "JPY":
        return None
    acct = _fetch_all("SELECT kaikei_account_did FROM vertex_atrecord_kouza_financial_account WHERE vertex_id=%s AND owner_did=%s LIMIT 1", (account_did, owner))
    bank_did = (acct[0] or {}).get("kaikei_account_did") if acct else None
    if not bank_did:
        return None
    bank_txn_id = _str(row.get("externalTxnId")) or _hash(row)
    rkey = f"kouza-{_hash({'financialAccountDid': account_did, 'bankTxnId': bank_txn_id})}"
    did = _record_did(owner, "ai.gftd.apps.kaikei.bankTransaction", rkey)
    _execute(
        """INSERT INTO vertex_atrecord_kaikei_bank_transaction
        (vertex_id, _seq, owner_did, bank_did, bank_txn_id, posted_at, amount, counterparty_name, reconcile_status, created_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'pending',%s) ON CONFLICT (vertex_id) DO NOTHING""",
        (did, _next_seq("vertex_atrecord_kaikei_bank_transaction"), owner, bank_did, bank_txn_id, row["postedAt"], row["amountMinor"], row.get("counterpartyName") or row.get("description") or None, now_iso()),
    )
    _execute("UPDATE vertex_atrecord_kouza_external_transaction SET kaikei_bank_transaction_did=%s, accounting_status='derived' WHERE vertex_id=%s", (did, external_did))
    return did


def attach_document(ownerDid: str = "", financialAccountDid: str = "", documentKind: str = "", vaultCid: str = "", contentHash: str = "", issuedAt: str = "", title: str = "", periodFrom: str = "", periodTo: str = "", mimeType: str = "", **_: Any) -> dict[str, Any]:
    owner = _require_did(ownerDid, "ownerDid")
    account = _require_ref(financialAccountDid, "financialAccountDid")
    if not documentKind or not vaultCid or not contentHash or not issuedAt:
        return {"error": "documentKind, vaultCid, contentHash, issuedAt required"}
    rkey = f"doc-{_hash({'financialAccountDid': account, 'documentKind': documentKind, 'contentHash': contentHash})}"
    did = _record_did(owner, f"{NS}.accountDocument", rkey)
    _execute(
        """INSERT INTO vertex_atrecord_kouza_account_document
        (vertex_id, _seq, owner_did, rkey, financial_account_did, document_kind, title, period_from, period_to,
         issued_at, vault_cid, content_hash, mime_type, created_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (vertex_id) DO NOTHING""",
        (did, _next_seq("vertex_atrecord_kouza_account_document"), owner, rkey, account, documentKind, title or None, periodFrom or None, periodTo or None, issuedAt, vaultCid, contentHash, mimeType or None, now_iso()),
    )
    return {"documentDid": did}


def map_kaikei_account(financialAccountDid: str = "", kaikeiAccountDid: str = "", **_: Any) -> dict[str, Any]:
    account = _require_ref(financialAccountDid, "financialAccountDid")
    kaikei = _require_ref(kaikeiAccountDid, "kaikeiAccountDid")
    updated = _execute("UPDATE vertex_atrecord_kouza_financial_account SET kaikei_account_did=%s, updated_at=%s WHERE vertex_id=%s", (kaikei, now_iso(), account))
    return {"ok": updated > 0}


def list_accounts(ownerDid: str = "", limit: Any = 50, **_: Any) -> dict[str, Any]:
    owner = _require_did(ownerDid, "ownerDid")
    n = max(1, min(_int(limit, "limit"), 200))
    rows = _fetch_all(
        """SELECT vertex_id, connection_did, masked_account_number, display_name, account_kind, currency,
        current_balance_minor, balance_as_of, kaikei_account_did, status, _seq AS cursor
        FROM vertex_atrecord_kouza_financial_account WHERE owner_did=%s ORDER BY _seq DESC LIMIT %s""",
        (owner, n),
    )
    return {"accounts": rows, "cursor": rows[-1]["cursor"] if rows else None}


def list_transactions(financialAccountDid: str = "", limit: Any = 100, **_: Any) -> dict[str, Any]:
    account = _require_ref(financialAccountDid, "financialAccountDid")
    n = max(1, min(_int(limit, "limit"), 500))
    rows = _fetch_all(
        """SELECT vertex_id, external_txn_id, posted_at, value_at, amount_minor, currency,
        counterparty_name, description, category_hint, document_did, kaikei_bank_transaction_did,
        accounting_status, _seq AS cursor
        FROM vertex_atrecord_kouza_external_transaction
        WHERE financial_account_did=%s ORDER BY posted_at DESC, _seq DESC LIMIT %s""",
        (account, n),
    )
    return {"transactions": rows, "cursor": rows[-1]["cursor"] if rows else None}
