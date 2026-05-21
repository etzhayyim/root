"""
lawfirm.cadence.* — LangServer handlers for the lead cadence-tick.

Task types:
  lawfirm.cadence.dispatchDueMails  Walk vertex_lawfirm_lead.next_action_at,
                                    fire warm-intro mail per due lead via
                                    Graph sendDraft, log outreach event,
                                    bump stage 'lead' → 'contacted'.

Wired to existing lawfirm_sales_cadence_tick BPMN (R/PT24H, deployed via
20260509010000_vertex_lawfirm_sales_cadence.ts seed).

Mail bodies live in `_working/etzhayyim-revenue/outbox/08[a-g]-*-warm-intro.eml`
on the dispatcher pod's mounted ConfigMap. Filename derived from
`vertex_lawfirm_lead.notes` field "Outreach: outbox/<file>" pattern.

ADR-0036 Hyperdrive direct.
etzhayyim_agent rule: external mail = draft-only by default; send_now=False
unless explicit override flag. CEO/COO approval gate stays in place.
"""

from __future__ import annotations

import datetime as _dt
import json
import logging
import os
import re
from pathlib import Path
from typing import Any

LOG = logging.getLogger("lawfirm.cadence")

_FIRM_DID = "did:web:lawfirm.etzhayyim.com"
_OUTBOX_DIR = os.environ.get(
    "LAWFIRM_OUTBOX_DIR",
    "/etc/etzhayyim/outbox",  # ConfigMap mount path in mitama-udf pod
)
_DISPATCHER_URL = os.environ.get(
    "BPMN_DISPATCHER_INTERNAL_URL",
    "http://bpmn-dispatcher.mitama-udf.svc.cluster.local:8080",
)


def _now_iso() -> str:
    return _dt.datetime.now(tz=_dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _today_date() -> str:
    return _dt.datetime.now(tz=_dt.UTC).strftime("%Y-%m-%d")


def _execute(sql_str: str, params: dict) -> bool:
    try:
        from sqlalchemy import text
        from pymagatama.db_alchemy import sa_rowcount
        sa_rowcount(text(sql_str), params)
        return True
    except Exception as exc:
        LOG.warning("execute failed: %s", exc)
        return False


def _query(sql_str: str, params: dict | None = None) -> list[dict]:
    try:
        from sqlalchemy import text
        from pymagatama.db_alchemy import sa_query
        return sa_query(text(sql_str), params or {})
    except Exception as exc:
        LOG.warning("query failed: %s", exc)
        return []


# ── Mail file parsing ─────────────────────────────────────────────────────────

_OUTREACH_PATH_RE = re.compile(r"Outreach:\s*(outbox/[A-Za-z0-9._/-]+\.eml)")


def _outreach_path_from_notes(notes: str) -> str | None:
    m = _OUTREACH_PATH_RE.search(notes or "")
    return m.group(1) if m else None


def _parse_eml(text: str) -> dict:
    """
    Minimal RFC822-ish parser tuned to our outbox/*.eml format.
    Returns dict with To, Cc, Subject, body, plus X-* headers.
    """
    headers: dict[str, str] = {}
    body_lines: list[str] = []
    in_body = False
    for line in text.splitlines():
        if not in_body:
            if line.strip() == "":
                in_body = True
                continue
            if ":" in line:
                k, _, v = line.partition(":")
                headers[k.strip()] = v.strip()
            continue
        body_lines.append(line)
    return {
        "to": [a.strip() for a in headers.get("To", "").split(",") if a.strip()],
        "cc": [a.strip() for a in headers.get("Cc", "").split(",") if a.strip()],
        "subject": headers.get("Subject", ""),
        "body_text": "\n".join(body_lines).strip(),
        "x_lead_id": headers.get("X-Lead-Id", ""),
        "x_cadence_step": headers.get("X-Cadence-Step", ""),
        "x_scheduled_send": headers.get("X-Scheduled-Send", ""),
    }


def _read_eml(rel_path: str) -> dict | None:
    """Read outbox/*.eml from dispatcher mount; returns parsed dict or None."""
    full = Path(_OUTBOX_DIR) / Path(rel_path).relative_to("outbox") if rel_path.startswith("outbox/") else Path(_OUTBOX_DIR) / rel_path
    try:
        return _parse_eml(full.read_text(encoding="utf-8"))
    except FileNotFoundError:
        # Fallback: also try repo-relative path during local dev
        repo_path = Path(
            "/Users/junkawasaki/github/etzhayyim/root/_working/etzhayyim-revenue"
        ) / rel_path
        try:
            return _parse_eml(repo_path.read_text(encoding="utf-8"))
        except Exception as exc:
            LOG.warning("eml not found %s: %s", rel_path, exc)
            return None
    except Exception as exc:
        LOG.warning("eml parse failed %s: %s", rel_path, exc)
        return None


# ── Graph sendDraft / sendMail dispatch ──────────────────────────────────────

def _dispatch_send_draft(parsed: dict, send_now: bool = False) -> dict:
    """
    POST to bpmn-dispatcher → microsoft.etzhayyim.com sendDraft (default) or sendMail.
    etzhayyim_agent rule: external mail defaults to send_now=False (draft only).
    """
    nsid = "ai.gftd.apps.microsoft.sendMail" if send_now else "ai.gftd.apps.microsoft.sendDraft"
    body = json.dumps({
        "to":       parsed.get("to") or [],
        "cc":       parsed.get("cc") or [],
        "subject":  parsed.get("subject") or "",
        "body_md":  parsed.get("body_text") or "",
        "send_now": bool(send_now),
    }).encode()
    secret = os.environ.get("BPMN_DISPATCHER_INTERNAL_SECRET", "")
    headers = {"Content-Type": "application/json"}
    if secret:
        headers["x-internal-trust"] = secret
    try:
        import urllib.request
        url = f"{_DISPATCHER_URL}/xrpc/{nsid}"
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=20) as resp:
            payload = resp.read()
        return {"ok": True, "via": nsid, "payload": payload[:200].decode("utf-8", errors="replace")}
    except Exception as exc:
        LOG.warning("dispatcher send failed: %s", exc)
        return {"ok": False, "via": nsid, "error": str(exc)}


# ── Task: lawfirm.cadence.dispatchDueMails ────────────────────────────────────

async def task_cadence_dispatch_due_mails(
    horizon_days: int = 0,
    max_dispatches: int = 20,
    send_now: bool = False,
) -> dict:
    """
    Walk leads where stage='lead' AND next_action_at <= today + horizon_days.
    For each, find the .eml via notes-embedded path, dispatch via Graph
    sendDraft (draft mode by default), log outreach_event, bump stage='contacted'.

    Idempotent on (lead_id, cadence_step) — re-run safe via vertex_lawfirm_outreach_event check.
    """
    today = _today_date()
    cutoff = today  # extend with horizon_days if needed at SQL level

    rows = _query(
        "SELECT lead_id, target_name, target_email, notes, next_action_at "
        "FROM vertex_lawfirm_lead "
        "WHERE stage = 'lead' "
        "  AND next_action_at IS NOT NULL "
        "  AND next_action_at <= :cutoff "
        "ORDER BY next_action_at ASC "
        "LIMIT :limit",
        {"cutoff": cutoff, "limit": max(1, int(max_dispatches))},
    )

    dispatched: list[dict] = []
    skipped: list[dict] = []
    for r in rows:
        lead_id = r.get("lead_id") or ""
        notes = r.get("notes") or ""
        eml_rel = _outreach_path_from_notes(notes)
        if not eml_rel:
            skipped.append({"lead_id": lead_id, "reason": "no_outreach_path"})
            continue

        # Idempotency: skip if T+0 warm-intro event already exists for this lead
        existing = _query(
            "SELECT vertex_id FROM vertex_lawfirm_outreach_event "
            "WHERE lead_id = :lid AND event_kind = 'warm_intro_sent'",
            {"lid": lead_id},
        )
        if existing:
            skipped.append({"lead_id": lead_id, "reason": "already_sent"})
            continue

        parsed = _read_eml(eml_rel)
        if not parsed or not parsed.get("to"):
            skipped.append({"lead_id": lead_id, "reason": "eml_unreadable"})
            continue

        result = _dispatch_send_draft(parsed, send_now=send_now)

        ev_uri = (
            f"at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.lawfirm.outreachEvent/"
            f"{lead_id}-warm-intro-{_dt.datetime.now(tz=_dt.UTC).strftime('%Y%m%d%H%M%S')}"
        )
        _execute(
            "INSERT INTO vertex_lawfirm_outreach_event "
            "(vertex_id, lead_id, event_kind, channel, direction, "
            " subject, body_preview, asset_uri, occurred_at, actor_did, "
            " created_at, sensitivity_ord, owner_did) "
            "VALUES (:vid, :lid, 'warm_intro_sent', 'email', 'outbound', "
            " :subj, :preview, :asset, :now, :actor, :now, 200, :owner)",
            {
                "vid": ev_uri,
                "lid": lead_id,
                "subj": parsed.get("subject", "")[:300],
                "preview": (parsed.get("body_text") or "")[:500],
                "asset": eml_rel,
                "now": _now_iso(),
                "actor": _FIRM_DID,
                "owner": _FIRM_DID,
            },
        )

        # Bump stage lead → contacted, set last_touch_at
        _execute(
            "UPDATE vertex_lawfirm_lead "
            "SET stage = 'contacted', last_touch_at = :now "
            "WHERE lead_id = :lid AND stage = 'lead'",
            {"now": _now_iso(), "lid": lead_id},
        )

        dispatched.append({
            "lead_id":      lead_id,
            "target_name":  r.get("target_name"),
            "target_email": r.get("target_email"),
            "asset":        eml_rel,
            "send_result":  result,
            "send_now":     bool(send_now),
        })

    LOG.info(
        "cadence dispatch tick: %d dispatched, %d skipped (cutoff=%s, send_now=%s)",
        len(dispatched), len(skipped), cutoff, send_now,
    )
    return {
        "ok": True,
        "cutoff_date": cutoff,
        "dispatched_count": len(dispatched),
        "skipped_count": len(skipped),
        "dispatched": dispatched,
        "skipped": skipped,
    }


# ── Task: lawfirm.cadence.dispatchFollowUps ───────────────────────────────────

# Cadence step → (template path, lookback_days, prior_event_kind, post_stage)
# T+5d: warm-intro sent ≥ 5d ago + no reply → light follow-up draft
# T+12d: light follow-up sent ≥ 7d ago (cumulative ~12d from initial) → soft release + stage='lost'
_FOLLOWUP_STEPS = [
    {
        "step":          "T+5d-light-followup",
        "template":      "outbox/templates/cadence-touch2-d5-light-followup.eml",
        "prior_kind":    "warm_intro_sent",
        "lookback_days": 5,
        "next_kind":     "followup_5d_sent",
        "set_stage":     None,           # no stage change, just touch
    },
    {
        "step":          "T+12d-soft-release",
        "template":      "outbox/templates/cadence-touch3-d12-soft-release.eml",
        "prior_kind":    "followup_5d_sent",
        "lookback_days": 7,
        "next_kind":     "soft_release_sent",
        "set_stage":     "lost",         # close loop after final touch
    },
]


async def task_cadence_dispatch_follow_ups(
    max_dispatches: int = 20,
    send_now: bool = False,
) -> dict:
    """
    Walk vertex_lawfirm_outreach_event for `prior_kind` rows whose
    occurred_at < now - lookback_days, where no `next_kind` row exists yet
    AND the lead has no inbound reply event AND lead.stage='contacted'.

    For each, render template with {{lead_id, partner_first_name, partner_email,
    firm_short_name}} substitutions, dispatch via Graph sendDraft (default
    send_now=False), record next_kind event, optionally bump lead.stage.
    """
    dispatched: list[dict] = []
    skipped: list[dict] = []

    for cfg in _FOLLOWUP_STEPS:
        rows = _query(
            """
            SELECT l.lead_id, l.target_name, l.target_email, l.notes, l.stage
            FROM vertex_lawfirm_lead l
            JOIN vertex_lawfirm_outreach_event prior
              ON prior.lead_id = l.lead_id
             AND prior.event_kind = :prior_kind
             AND CAST(prior.occurred_at AS timestamptz) < now() - (:lookback || ' days')::interval
            WHERE l.stage = 'contacted'
              AND NOT EXISTS (
                SELECT 1 FROM vertex_lawfirm_outreach_event nxt
                WHERE nxt.lead_id = l.lead_id AND nxt.event_kind = :next_kind
              )
              AND NOT EXISTS (
                SELECT 1 FROM vertex_lawfirm_outreach_event reply
                WHERE reply.lead_id = l.lead_id
                  AND reply.event_kind = 'reply_received'
                  AND reply.direction = 'inbound'
              )
            ORDER BY prior.occurred_at ASC
            LIMIT :limit
            """,
            {
                "prior_kind": cfg["prior_kind"],
                "next_kind":  cfg["next_kind"],
                "lookback":   str(cfg["lookback_days"]),
                "limit":      max(1, int(max_dispatches)),
            },
        )

        if not rows:
            continue

        template = _read_eml(cfg["template"])
        if not template:
            skipped.append({"step": cfg["step"], "reason": "template_unreadable"})
            continue

        for r in rows:
            lead_id = r.get("lead_id") or ""
            partner_email = r.get("target_email") or ""
            firm_full = r.get("target_name") or ""
            partner_first = (partner_email.split("@", 1)[0].split(".")[0] or "there").title()
            firm_short = firm_full.split(" ")[0] if firm_full else "your firm"

            substituted = {
                "to":        [partner_email] if partner_email else [],
                "cc":        [],
                "subject":   (template.get("subject") or "")
                              .replace("{{lead_id}}", lead_id)
                              .replace("{{partner_first_name}}", partner_first)
                              .replace("{{firm_short_name}}", firm_short),
                "body_text": (template.get("body_text") or "")
                              .replace("{{lead_id}}", lead_id)
                              .replace("{{partner_email}}", partner_email)
                              .replace("{{partner_first_name}}", partner_first)
                              .replace("{{firm_short_name}}", firm_short),
            }

            result = _dispatch_send_draft(substituted, send_now=send_now)

            ev_uri = (
                f"at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.lawfirm.outreachEvent/"
                f"{lead_id}-{cfg['next_kind']}-"
                f"{_dt.datetime.now(tz=_dt.UTC).strftime('%Y%m%d%H%M%S')}"
            )
            _execute(
                "INSERT INTO vertex_lawfirm_outreach_event "
                "(vertex_id, lead_id, event_kind, channel, direction, "
                " subject, body_preview, asset_uri, occurred_at, actor_did, "
                " created_at, sensitivity_ord, owner_did) "
                "VALUES (:vid, :lid, :kind, 'email', 'outbound', "
                " :subj, :preview, :asset, :now, :actor, :now, 200, :owner)",
                {
                    "vid": ev_uri, "lid": lead_id, "kind": cfg["next_kind"],
                    "subj": substituted["subject"][:300],
                    "preview": substituted["body_text"][:500],
                    "asset": cfg["template"],
                    "now": _now_iso(), "actor": _FIRM_DID, "owner": _FIRM_DID,
                },
            )

            if cfg.get("set_stage"):
                _execute(
                    "UPDATE vertex_lawfirm_lead SET stage = :stage, last_touch_at = :now "
                    "WHERE lead_id = :lid",
                    {"stage": cfg["set_stage"], "now": _now_iso(), "lid": lead_id},
                )
            else:
                _execute(
                    "UPDATE vertex_lawfirm_lead SET last_touch_at = :now WHERE lead_id = :lid",
                    {"now": _now_iso(), "lid": lead_id},
                )

            dispatched.append({
                "lead_id":     lead_id,
                "step":        cfg["step"],
                "next_kind":   cfg["next_kind"],
                "stage_after": cfg.get("set_stage") or r.get("stage") or "",
                "send_result": result,
                "send_now":    bool(send_now),
            })

    LOG.info(
        "follow-up dispatch tick: %d dispatched, %d skipped (send_now=%s)",
        len(dispatched), len(skipped), send_now,
    )
    return {
        "ok": True,
        "dispatched_count": len(dispatched),
        "skipped_count": len(skipped),
        "dispatched": dispatched,
        "skipped": skipped,
    }


# ── LangServer registration ─────────────────────────────────────────────────────

def register(app: Any, timeout_ms: int = 90_000) -> None:
    from pymagatama.langserver_compat import LangServerWorker
    if not isinstance(app, LangServerWorker):
        return

    @app.task(task_type="lawfirm.cadence.dispatchDueMails",
              timeout_ms=timeout_ms, max_jobs_to_activate=2)
    async def _dispatch(horizon_days: int = 0,
                        max_dispatches: int = 20,
                        send_now: bool = False) -> dict:
        return await task_cadence_dispatch_due_mails(
            horizon_days=horizon_days,
            max_dispatches=max_dispatches,
            send_now=send_now,
        )

    @app.task(task_type="lawfirm.cadence.dispatchFollowUps",
              timeout_ms=timeout_ms, max_jobs_to_activate=2)
    async def _followup(max_dispatches: int = 20, send_now: bool = False) -> dict:
        return await task_cadence_dispatch_follow_ups(
            max_dispatches=max_dispatches, send_now=send_now,
        )

    LOG.info(
        "Registered tasks: lawfirm.cadence.{dispatchDueMails,dispatchFollowUps}"
    )
