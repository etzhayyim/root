"""Outreach + sales touchpoint templates (deterministic).

These render the message body that lands in `vertex_email_outbox` with
status='queued-no-recipient' (marketing) or status='queued' (sales).
A human reviewer fills in the recipient + approves before send. No PII
leaves this process: templates only contain placeholders for company,
domain, and `[[PARTNER_NAME]]` tokens that the reviewer fills.

Touchpoint kinds:
  - marketing-outbound (3-touch sequence per ICP segment)
  - sales-onboarding   (welcome + getting-started)
  - sales-usage-recap  (highlight what they tried in last 24h)
  - sales-upgrade      (free → starter, approaching quota)
  - sales-book-call    (escalation: book a call with nishino)

Compliance: every body ends with the unsubscribe + sender-postal-
address footer (CAN-SPAM 16 CFR 316.5 / PECR Reg 23). Reviewer can
edit but cannot remove without flagging.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ICPSegment = Literal[
    "dev-tooling-saas",
    "data-team-mid-market",
    "bsky-builders",
    "jp-saas-founders",
    "unknown",
]


@dataclass(frozen=True)
class OutreachBody:
    subject: str
    body_text: str
    body_html: str


_FOOTER_TEXT = (
    "\n\n— nishino\nyatabase.gftd.ai\n\n"
    "etzhayyim (operator) — etz hayim (corporate vendor: Gftd Japan株式会社)\n"
    "Tokyo, Japan.\n"
    "Don't want these? Reply 'stop' and we'll never email you again.\n"
)

_FOOTER_HTML = (
    '<p style="color:#888;font-size:0.85em;margin-top:32px">'
    "— nishino<br/>yatabase.gftd.ai<br/><br/>"
    "etzhayyim (operator) — etz hayim (corporate vendor: Gftd Japan株式会社)<br/>"
    "Tokyo, Japan.<br/>"
    "Don't want these? Reply 'stop' and we'll never email you again."
    "</p>"
)


def _para_html(text: str) -> str:
    return "".join(f"<p>{ln.strip()}</p>" for ln in text.strip().split("\n\n") if ln.strip())


# ---------------------------------------------------------------------------
# Marketing — 3-touch sequence per ICP segment.
# ---------------------------------------------------------------------------

def _marketing_touch_1(company: str, domain: str, segment: ICPSegment) -> OutreachBody:
    angle = {
        "dev-tooling-saas": (
            f"We noticed {company} ({domain}) builds on the dev-tooling stack — "
            "the same neighborhood as Supabase / Hasura / Neo4j users we ship to."
        ),
        "data-team-mid-market": (
            f"Mid-market data teams like {company} keep telling us the same thing: "
            "the graph DB they want is the one that drops into their existing Postgres workflow."
        ),
        "bsky-builders": (
            f"You're building on AT Protocol — and {company} hits the same wall every "
            "Bluesky-shaped app eventually hits: a graph layer that federates."
        ),
        "jp-saas-founders": (
            f"日本の SaaS スタートアップで {company} さんのような chiisaku hajimete "
            "プロダクトを伸ばしているチームに、graph DB の選択を提案させてください。"
        ),
        "unknown": (
            f"We've been watching {company} ({domain}) for a bit and wanted to "
            "open a low-pressure conversation."
        ),
    }[segment]

    body = (
        f"Hi [[PARTNER_NAME]],\n\n"
        f"{angle}\n\n"
        "yatabase.gftd.ai is a graph DB with built-in object storage, auth, and "
        "MCP. Free tier covers 1k req/day; no card. If it's useful: we share the "
        "Cypher + Storage S3-compat surface from day one.\n\n"
        "Worth a 15-min chat next week, or should I just send a 1-pager?"
    )
    return OutreachBody(
        subject=f"yatabase × {company}: graph + storage in one BaaS",
        body_text=body + _FOOTER_TEXT,
        body_html=_para_html(body) + _FOOTER_HTML,
    )


def _marketing_touch_2(company: str, domain: str, segment: ICPSegment) -> OutreachBody:
    body = (
        f"Hi [[PARTNER_NAME]] — quick nudge.\n\n"
        f"I sent a note about yatabase last week (graph DB + S3-compat storage + "
        f"MCP, free for {company}-sized teams). No worries if it isn't a fit right "
        "now, but a 1-line reply (yes / not now / never) saves me from chasing.\n\n"
        "If it's helpful: our public docs are at https://yatabase.gftd.ai/docs and "
        "you can spin up a free tenant in ~2 seconds (no card)."
    )
    return OutreachBody(
        subject=f"Re: yatabase × {company}",
        body_text=body + _FOOTER_TEXT,
        body_html=_para_html(body) + _FOOTER_HTML,
    )


def _marketing_touch_3(company: str, domain: str, segment: ICPSegment) -> OutreachBody:
    body = (
        f"Hi [[PARTNER_NAME]], last note from me — I'll stop after this.\n\n"
        f"If yatabase ever becomes relevant for {company} ({domain}), the door "
        "stays open. We publish ADRs publicly at github.com/gftdcojp/yatabase so "
        "you can audit before adopting.\n\n"
        "Wishing you and the team well. — nishino"
    )
    return OutreachBody(
        subject=f"Closing the loop — yatabase × {company}",
        body_text=body + _FOOTER_TEXT,
        body_html=_para_html(body) + _FOOTER_HTML,
    )


def marketing_touch(company: str, domain: str, segment: ICPSegment, touch: int) -> OutreachBody:
    """Return the rendered body for touch 1, 2, or 3 of a marketing sequence.

    Each call is deterministic — same input → same output. The reviewer
    then fills [[PARTNER_NAME]] and approves before send.
    """
    if touch == 1:
        return _marketing_touch_1(company, domain, segment)
    if touch == 2:
        return _marketing_touch_2(company, domain, segment)
    return _marketing_touch_3(company, domain, segment)


# ---------------------------------------------------------------------------
# Sales — per-decision template.
# ---------------------------------------------------------------------------

SalesKind = Literal[
    "sales-onboarding",
    "sales-usage-recap",
    "sales-upgrade",
    "sales-book-call",
]


def _onboarding(org_did: str, tenant_name: str | None) -> OutreachBody:
    name = tenant_name or "your team"
    body = (
        f"Hi [[PARTNER_NAME]] — welcome to yatabase.\n\n"
        f"You signed {name} up but haven't sent a request yet. Three things "
        "that take 60 seconds each:\n\n"
        "1. Try `POST /cypher` with `CREATE (n:Thing {name:'hello'})` — that's "
        "your first graph node.\n"
        "2. PUT something into `/storage/v1/object/test/<key>` — that's your "
        "first object.\n"
        "3. Hit `/mcp tools/list` from Claude Code — that's MCP wired in.\n\n"
        "If any of those error, reply to this thread and we'll triage. The "
        "free tier covers 1k req/day so the exploration is on us."
    )
    return OutreachBody(
        subject=f"yatabase: 3 quick wins for {name}",
        body_text=body + _FOOTER_TEXT,
        body_html=_para_html(body) + _FOOTER_HTML,
    )


def _usage_recap(org_did: str, metric_24h: dict[str, int]) -> OutreachBody:
    api = metric_24h.get("api_request", 0)
    storage = metric_24h.get("storage_gb_hour", 0)
    body = (
        f"Hi [[PARTNER_NAME]] — quick recap of your last 24h on yatabase:\n\n"
        f"  • api_request   {api:>6}\n"
        f"  • storage_gb_h  {storage:>6}\n\n"
        "Anything blocking? If a query / endpoint is shaped wrong for your use "
        "case, reply — we add NSIDs based on what actual users hit."
    )
    return OutreachBody(
        subject="yatabase: your last 24h",
        body_text=body + _FOOTER_TEXT,
        body_html=_para_html(body) + _FOOTER_HTML,
    )


def _upgrade(org_did: str, metric_24h: dict[str, int]) -> OutreachBody:
    api = metric_24h.get("api_request", 0)
    body = (
        f"Hi [[PARTNER_NAME]] — your team hit {api} api_request in the last 24h, "
        "and the free tier caps at 1k/day.\n\n"
        "Starter ($29/mo) lifts that to 100k/day + 10 GiB storage + priority "
        "support. Self-serve at https://yatabase.gftd.ai/studio/billing — no "
        "card friction.\n\n"
        "If the pricing doesn't fit your model, reply and I'll work out a custom "
        "shape with you (no auto-bills, no surprises)."
    )
    return OutreachBody(
        subject="yatabase: approaching the free-tier cap",
        body_text=body + _FOOTER_TEXT,
        body_html=_para_html(body) + _FOOTER_HTML,
    )


def _book_call(org_did: str) -> OutreachBody:
    body = (
        f"Hi [[PARTNER_NAME]] — your team's traction on yatabase looks like a "
        "good fit for a 20-min call to align on roadmap (and to hear what's "
        "missing).\n\n"
        "Pick any slot here: https://cal.gftd.ai/nishino — or reply with a "
        "couple of windows and I'll book it manually. JP/EN both fine."
    )
    return OutreachBody(
        subject="yatabase: worth a 20-min sync?",
        body_text=body + _FOOTER_TEXT,
        body_html=_para_html(body) + _FOOTER_HTML,
    )


def sales_touch(
    kind: SalesKind,
    org_did: str,
    *,
    tenant_name: str | None = None,
    metric_24h: dict[str, int] | None = None,
) -> OutreachBody:
    """Render the sales touchpoint body for a given decision."""
    metric_24h = metric_24h or {}
    if kind == "sales-onboarding":
        return _onboarding(org_did, tenant_name)
    if kind == "sales-usage-recap":
        return _usage_recap(org_did, metric_24h)
    if kind == "sales-upgrade":
        return _upgrade(org_did, metric_24h)
    return _book_call(org_did)


# ---------------------------------------------------------------------------
# Segment classifier (deterministic from tech_stack + signal hints).
# ---------------------------------------------------------------------------

def classify_segment(lead: dict) -> ICPSegment:
    """Map a lead row's tech_stack / signal / domain to one of the ICPs.

    Pure function over the lead's existing columns — no external lookup.
    """
    stack = (lead.get("tech_stack") or "").lower()
    signal = (lead.get("signal") or "").lower()
    domain = (lead.get("domain") or "").lower()

    if any(t in stack for t in ("supabase", "hasura", "neo4j", "prisma", "drizzle", "kysely")):
        return "dev-tooling-saas"
    if any(t in stack for t in ("snowflake", "databricks", "dbt", "airbyte", "fivetran")):
        return "data-team-mid-market"
    if "atproto" in stack or "atproto" in signal or "bluesky" in signal or "bsky.app" in domain:
        return "bsky-builders"
    if domain.endswith(".jp") or domain.endswith(".co.jp") or "japan" in signal:
        return "jp-saas-founders"
    return "unknown"
