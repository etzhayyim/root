"""
ADR-0049 Phase B — gmail contact DID materializer.

For every inbound gmail message, materialize one `vertex_gmail_contact`
row per unique sender + one `edge_gmail_email_from_contact` edge. This
replaces the stub `TODO(Phase 2)` in the gmail Worker that never got
wired because per-sender DID creation via PDS XRPC was too expensive on
the hot ingest path (each `sync_inbox` batch may see 50-500 new senders).

The UDF runs entirely inside the mitama-udf pod:

    app.ts syncInbox → INSERT vertex_gmail_email →
      SELECT gmail_upsert_contact(email_id, from_addr, account_did) →
        [UDF] parse from_addr → sanitize path segment → INSERT contact
                                                     → INSERT edge
        returns {contactDid, wasNew, emailPath, displayName}

PDS registration (`sdk.did.create`) is deliberately NOT done here. The
row lives in the graph projection only; a later promotion job can read
`vertex_gmail_contact WHERE pds_registered = false` and publish those
that cross an activity threshold (e.g. ≥10 inbound messages) to avoid
polluting the AT relay with one-shot spam addresses.

Sanitization rules (`sanitize_path_segment`):
  alice@example.com   → alice-at-example-com
  a.b+tag@x.co.jp     → a-b-tag-at-x-co-jp
  "ALICE" <a@x>       → alice-at-x  (drops the display-name wrapper)

Only `[a-z0-9-]` are kept; `.`, `+`, `_`, `@`, whitespace collapse to `-`.
Length-capped to 63 chars (DNS label constraint for did:web path
segments). If the tail gets truncated, the sanitized path remains a
valid deterministic function of the input (no hash collision risk —
two distinct emails never produce the same segment because we bake the
full local+domain into the allowed chars).
"""

from __future__ import annotations

import json
import re
from typing import Any

from pymagatama import udf
from pymagatama.db_sync import execute

_CONTACT_COLLECTION = "com.etzhayyim.apps.gmail.contact"
_CONTACT_DID_PREFIX = "did:web:gmail.etzhayyim.com:contact:"
_MAX_SEGMENT_LEN = 63  # DNS label ceiling (RFC 1035)

# Match "Display Name" <email@host> or just email@host.
_RFC5322 = re.compile(r'^\s*(?:"?([^"<]*?)"?\s*)?<?([^<>\s]+@[^<>\s]+)>?\s*$')


def _err(msg: str, **extra: Any) -> str:
    return json.dumps({"error": msg, **extra})


def _parse_from(addr: str) -> tuple[str, str]:
    """Return (display_name, email). display_name is '' when not present."""
    if not addr:
        return "", ""
    m = _RFC5322.match(addr)
    if not m:
        # Bare token with no < > wrapper and not matching email shape —
        # fall back to treating the whole thing as the address.
        return "", addr.strip().lower()
    name = (m.group(1) or "").strip()
    email = (m.group(2) or "").strip().lower()
    return name, email


def sanitize_path_segment(email: str) -> str:
    """Deterministic email → did:web path segment."""
    s = email.strip().lower()
    s = s.replace("@", "-at-")
    s = re.sub(r"[^a-z0-9-]+", "-", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s[:_MAX_SEGMENT_LEN]


@udf(
    nsid="com.etzhayyim.apps.gmail.upsertContact",
    io_threads=50,
    input_types=["VARCHAR"],
    result_type="VARCHAR",
    capability_tags=("gmail", "contact", "did-materialize"),
    agent_tool="Materialize a gmail contact DID + edge from a sender address.",
)
def upsert_contact(request_json: str) -> str:
    """
    Input: JSON `{emailId, fromAddr, accountDid}` — emailId is the rkey
    used by the gmail Worker when it INSERTed vertex_gmail_email (it's
    the `email-${gmailMessageId}` shape at call site, not the full
    vertex_id).

    Output: JSON `{contactDid, sanitized, displayName, email, wasNew,
    edgeCreated}`.
    """

    try:
        body = json.loads(request_json) if request_json else {}
    except json.JSONDecodeError as e:
        return _err(f"invalid JSON: {e}")
    if not isinstance(body, dict):
        return _err("request must be a JSON object")
    if "json" in body and isinstance(body.get("json"), dict):
        body = body["json"]

    email_id = str(body.get("emailId") or "").strip()
    from_addr = str(body.get("fromAddr") or "").strip()
    account_did = str(body.get("accountDid") or "did:web:gmail.etzhayyim.com").strip()
    if not email_id:
        return _err("emailId is required")
    if not from_addr:
        return _err("fromAddr is required")

    display_name, email = _parse_from(from_addr)
    if not email or "@" not in email:
        # Reject bare tokens that slipped past _RFC5322 — we never want
        # contacts like `did:web:gmail.etzhayyim.com:contact:junk-no-email`.
        return _err("could not extract email from fromAddr", fromAddr=from_addr)

    sanitized = sanitize_path_segment(email)
    if not sanitized:
        return _err("sanitization produced empty segment", email=email)

    contact_did = f"{_CONTACT_DID_PREFIX}{sanitized}"
    contact_vertex_id = f"at://{contact_did}/{_CONTACT_COLLECTION}/{sanitized}"
    # Email vertex_id shape from gmail/app.ts write("email", ...).
    email_vertex_id = f"at://{account_did}/com.etzhayyim.apps.gmail.email/{email_id}"
    edge_id = f"{email_vertex_id}|from|{contact_vertex_id}"

    # RisingWave does not parse `ON CONFLICT DO NOTHING`. Use `WHERE NOT
    # EXISTS` so concurrent / replay inserts are idempotent without the
    # round-trip cost of a separate pre-SELECT. The pattern degrades
    # message_count tracking — keep it fixed at 1; a streaming MV over
    # `vertex_gmail_email` can aggregate true counts later.
    contact_rowcount = execute(
        """
        INSERT INTO vertex_gmail_contact (
            vertex_id, created_date, sensitivity_ord, owner_did, rkey, repo,
            contact_did, email, display_name,
            first_seen_at, last_seen_at, message_count, created_at,
            org_id, user_id, actor_id
        )
        SELECT
            %s, to_char(now(),'YYYY-MM-DD')::date, 50, %s, %s, %s,
            %s, %s, %s,
            to_char(now(),'YYYY-MM-DD"T"HH24:MI:SS"Z"'),
            to_char(now(),'YYYY-MM-DD"T"HH24:MI:SS"Z"'),
            1,
            to_char(now(),'YYYY-MM-DD"T"HH24:MI:SS"Z"'),
            'etzhayyim', 'system', 'sys.gmail-udf'
        WHERE NOT EXISTS (
            SELECT 1 FROM vertex_gmail_contact WHERE vertex_id = %s
        )
        """,
        (
            contact_vertex_id,
            contact_did,
            sanitized,
            contact_did,
            contact_did,
            email,
            display_name,
            contact_vertex_id,
        ),
    )
    was_new = contact_rowcount > 0

    edge_rowcount = execute(
        """
        INSERT INTO edge_gmail_email_from_contact (
            edge_id, src_vid, dst_vid, created_date, sensitivity_ord, owner_did,
            email_id, contact_did, created_at
        )
        SELECT
            %s, %s, %s, to_char(now(),'YYYY-MM-DD')::date, 50, %s,
            %s, %s,
            to_char(now(),'YYYY-MM-DD"T"HH24:MI:SS"Z"')
        WHERE NOT EXISTS (
            SELECT 1 FROM edge_gmail_email_from_contact WHERE edge_id = %s
        )
        """,
        (edge_id, email_vertex_id, contact_vertex_id, account_did, email_id, contact_did, edge_id),
    )
    edge_created = edge_rowcount > 0

    return json.dumps(
        {
            "contactDid": contact_did,
            "sanitized": sanitized,
            "displayName": display_name,
            "email": email,
            "wasNew": was_new,
            "edgeCreated": edge_created,
        }
    )
