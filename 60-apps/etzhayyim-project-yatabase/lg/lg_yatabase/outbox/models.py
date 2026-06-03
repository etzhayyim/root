"""Pydantic v2 shapes for the yatabase outbox-review XRPC surface.

vertex_email_outbox rows produced by the marketing/sales graphs land
at status='queued-no-recipient'. Operators (admin-gated) flip them to
'queued' (after filling recipient + reviewing body) or 'rejected'.

Kept narrow on purpose — every action is human-in-the-loop, no batch
auto-approve.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

OutboxStatus = Literal[
    "queued-no-recipient",
    "queued",
    "queued-escalation",
    "sent",
    "failed",
    "rejected",
]


class OutboxListInput(BaseModel):
    status: str | None = Field(default="queued-no-recipient", max_length=64)
    kind: str | None = Field(default=None, max_length=64)
    limit: int = Field(default=50, ge=1, le=200)


class OutboxRow(BaseModel):
    vertex_id: str
    org_did: str | None = None
    recipient_email: str | None = None
    recipient_name: str | None = None
    subject: str | None = None
    body_text: str | None = None
    body_html: str | None = None
    kind: str | None = None
    status: str | None = None
    scheduled_at: str | None = None
    sent_at: str | None = None
    retry_count: int | None = None
    last_error: str | None = None
    created_at: str | None = None


class OutboxListOutput(BaseModel):
    rows: list[OutboxRow]
    total: int
    offset: int = 0
    limit: int


class OutboxApproveInput(BaseModel):
    vertex_id: str = Field(min_length=1, max_length=400)
    recipient_email: str = Field(min_length=3, max_length=320)
    recipient_name: str = Field(default="", max_length=200)
    # The reviewer may edit the body before approval (e.g. filling
    # [[PARTNER_NAME]] tokens). When omitted, server keeps the
    # graph-generated body verbatim.
    body_text: str | None = Field(default=None, max_length=32768)
    body_html: str | None = Field(default=None, max_length=32768)
    subject: str | None = Field(default=None, max_length=512)


class OutboxRejectInput(BaseModel):
    vertex_id: str = Field(min_length=1, max_length=400)
    reason: str = Field(default="", max_length=512)


class OutboxMutationOutput(BaseModel):
    ok: bool
    vertex_id: str
    status: str
    message: str = ""
