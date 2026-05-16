"""SES Phase 3 — Kubernetes CronJob entrypoint (ADR-2605120000).

Runs every 15 minutes; reads new SES-related emails from configured
Outlook/Exchange mailboxes via Microsoft Graph API and pipes each message
through the LangGraph ses_ingest pipeline with source_kind='email_cron'.

Required env vars:
  AZURE_TENANT_ID      Azure AD tenant ID
  AZURE_CLIENT_ID      Azure app-registration client ID
  AZURE_CLIENT_SECRET  Azure app-registration client secret
  SES_ACTOR_DID        DID of the ses actor (default: did:web:ses.gftd.ai)
  RW_URL               RisingWave asyncpg URL (same as ses-langgraph)

Optional env vars:
  SES_MAILBOXES        Comma-separated list of UPNs to pull
                       (default: j.kawasaki@gftd.co.jp,agent@gftd.co.jp)
  SES_ORG_DID          Org DID (default: did:erc725:gftd:260425:anon)
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
_log = logging.getLogger("ses-cron")

_DEFAULT_MAILBOXES = "j.kawasaki@gftd.co.jp,agent@gftd.co.jp"


def _require(key: str) -> str:
    val = os.environ.get(key, "").strip()
    if not val:
        _log.error("Required env var %s is not set", key)
        sys.exit(1)
    return val


async def main() -> None:
    tenant_id = _require("AZURE_TENANT_ID")
    client_id = _require("AZURE_CLIENT_ID")
    client_secret = _require("AZURE_CLIENT_SECRET")
    actor_did = os.environ.get("SES_ACTOR_DID", "did:web:ses.gftd.ai").strip()
    org_did = os.environ.get("SES_ORG_DID", "did:erc725:gftd:260425:anon").strip()
    mailboxes_raw = os.environ.get("SES_MAILBOXES", _DEFAULT_MAILBOXES)
    mailboxes = [m.strip() for m in mailboxes_raw.split(",") if m.strip()]

    if not mailboxes:
        _log.error("SES_MAILBOXES is empty after parsing")
        sys.exit(1)

    from pymagatama.ses.graph import build_graph
    from pymagatama.ses.outlook_pull import run_outlook_pull

    graph = build_graph()
    _log.info("ses-cron start | mailboxes=%s actor_did=%s", mailboxes, actor_did)

    results = []
    for mailbox in mailboxes:
        _log.info("Pulling mailbox=%s", mailbox)
        try:
            result = await run_outlook_pull(
                graph,
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret,
                mailbox_upn=mailbox,
                actor_did=actor_did,
                org_did=org_did,
            )
        except Exception as exc:
            _log.error("run_outlook_pull failed for mailbox=%s: %s", mailbox, exc)
            result = {"ok": False, "error": str(exc)}
        results.append({"mailbox": mailbox, **result})
        _log.info("result mailbox=%s: %s", mailbox, json.dumps(result))

    ok = all(r.get("ok") for r in results)
    total_processed = sum(r.get("processed", 0) for r in results)
    _log.info(
        "ses-cron done | ok=%s total_processed=%d results=%s",
        ok, total_processed, json.dumps(results),
    )
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    asyncio.run(main())
