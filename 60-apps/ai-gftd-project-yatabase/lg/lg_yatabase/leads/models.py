"""Pydantic v2 shapes for the yatabase lead-CRM XRPC surface.

Field names mirror src/leads.ts so the Worker forwarder can pass the
parsed body through verbatim.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


OutreachStatus = Literal["new", "drafted", "approved", "dismissed", "sent", "replied", "bounced", "dead"]


class LeadIngestInput(BaseModel):
    company: str = Field(min_length=1, max_length=200)
    domain: str = Field(min_length=1, max_length=200)
    contact_name: str | None = Field(default=None, max_length=200)
    contact_email: str | None = Field(default=None, max_length=320)
    source: str | None = Field(default="manual", max_length=64)
    source_url: str | None = Field(default=None, max_length=1024)
    signal: str | None = Field(default=None, max_length=1024)
    tech_stack: list[str] | None = None
    employees: str | None = Field(default=None, max_length=64)
    fit_score: float | None = Field(default=0, ge=0, le=100)
    reasoning: str | None = Field(default=None, max_length=2048)
    notes: str | None = Field(default=None, max_length=2048)
    force: bool = False


class LeadIngestOutput(BaseModel):
    ok: bool = True
    vertex_id: str
    domain: str
    outreach_status: str
    message: str = ""


class SetOutreachStatusInput(BaseModel):
    vertex_id: str
    status: Literal["approved", "dismissed", "sent", "replied", "bounced", "dead"]


class SetContactEmailInput(BaseModel):
    vertex_id: str
    email: str = Field(max_length=320)


class SetEnrichmentInput(BaseModel):
    vertex_id: str
    contact_email: str | None = Field(default=None, max_length=320)
    tech_stack: list[str] | None = None


class MarkDraftedInput(BaseModel):
    vertex_id: str
    outbox_id: str = Field(max_length=400)
