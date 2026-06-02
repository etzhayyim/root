"""Pydantic v2 request/response shapes for the yatabase auth XRPC surface."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class SignupInput(BaseModel):
    """Body of POST /xrpc/com.etzhayyim.apps.yata.signup — anonymous."""

    email: str | None = Field(default=None, max_length=320)
    name: str | None = Field(default=None, max_length=128)


class SignupOutput(BaseModel):
    ok: bool = True
    apiKey: str
    keyId: str
    orgDid: str
    tenantName: str
    awsAccessKeyId: str
    emailStatus: str = "skipped-no-email"
    welcome: str
    next: str = "First Cypher call auto-provisions your tenant schema."
    pricing: str = "Free tier: $0/month. See /docs for upgrade options."


class InviteInput(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    email: str | None = Field(default=None, max_length=320)


class InviteOutput(BaseModel):
    ok: bool = True
    apiKey: str
    keyId: str
    orgDid: str
    memberName: str


class RevokeInput(BaseModel):
    vertex_id: str = Field(min_length=1, max_length=400)


class RevokeOutput(BaseModel):
    ok: bool = True
    vertex_id: str
    status: str = "revoked"
