"""
lawfirm.tenant.* — LangServer handlers.

Task types:
  lawfirm.tenant.bootstrap   Provision sandbox/production tenant for a firm
  lawfirm.tenant.suspend     Pause tenant (pilot ended, 90-day retention)
  lawfirm.tenant.promote     Sandbox → saas-prod transition

Backs com.etzhayyim.apps.lawfirm.tenantBootstrap lexicon
(00-contracts/lexicons/com/etzhayyim/apps/lawfirm/tenantBootstrap.json).

Schema target: vertex_lawfirm_tenant + vertex_lawfirm_tenant_event +
edge_lawfirm_tenant_lead (added by 20260509150000 migration).

ADR-0036 Hyperdrive direct.
ADR-0029 depth-1 root DID per tenant (did:web:<slug>.lawfirm.etzhayyim.com).
"""

from __future__ import annotations

import datetime as _dt
import logging
import re
from typing import Any

LOG = logging.getLogger("lawfirm.tenant")

_FIRM_DID = "did:web:lawfirm.etzhayyim.com"
_SLUG_REGEX = re.compile(r"^[a-z][a-z0-9-]{1,15}$")
_VALID_REGIONS = {"vultr-lax", "vultr-mum", "vultr-tyo"}
_BUILT_OUT_REGIONS = {"vultr-lax"}  # Phase 1 only
_VALID_TIERS = {"sandbox", "saas-prod"}


def _now_iso() -> str:
    return _dt.datetime.now(tz=_dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


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


def _enc_field(plaintext: str) -> str:
    """App-layer field encryption placeholder.
    Production: signal:v1: prefix + AES-GCM. Day-0: prefix-marker only."""
    if not plaintext:
        return ""
    return f"signal:v1:{plaintext}"


# ── Task: lawfirm.tenant.bootstrap ────────────────────────────────────────────

async def task_lawfirm_tenant_bootstrap(
    slug: str = "",
    legal_name: str = "",
    country: str = "",
    data_region: str = "vultr-lax",
    tier: str = "sandbox",
    pilot_lead_id: str = "",
    admin_email: str = "",
    consent_regions: list[str] | None = None,
) -> dict:
    if not slug or not _SLUG_REGEX.match(slug):
        return {"ok": False, "error": "InvalidSlug",
                "detail": "slug must match ^[a-z][a-z0-9-]{1,15}$"}
    if not legal_name:
        return {"ok": False, "error": "InvalidInput", "detail": "legal_name required"}
    if data_region not in _VALID_REGIONS:
        return {"ok": False, "error": "InvalidRegion", "detail": f"data_region must be one of {sorted(_VALID_REGIONS)}"}
    if data_region not in _BUILT_OUT_REGIONS:
        return {"ok": False, "error": "RegionUnavailable",
                "detail": f"{data_region} not built out (Phase 1 = vultr-lax only)"}
    if tier not in _VALID_TIERS:
        return {"ok": False, "error": "InvalidTier", "detail": f"tier must be one of {sorted(_VALID_TIERS)}"}
    if tier == "sandbox" and not pilot_lead_id:
        return {"ok": False, "error": "PilotLeadMissing",
                "detail": "tier=sandbox requires pilot_lead_id"}

    # Idempotency check: existing (slug, tier) pair
    tenant_id = f"{tier.replace('saas-', '')}-{slug}" if tier == "sandbox" else f"prod-{slug}"
    vertex_id = f"at://did:web:lawfirm.etzhayyim.com/com.etzhayyim.apps.lawfirm.tenant/{tenant_id}"
    existing = _query(
        "SELECT vertex_id, status, tier FROM vertex_lawfirm_tenant WHERE slug = :slug AND tier = :tier",
        {"slug": slug, "tier": tier},
    )
    if existing:
        row = existing[0]
        return {
            "ok": True,
            "status": "already_exists",
            "tenantDid": _tenant_did(slug, tier),
            "pdsUrl": _pds_url(slug, tier),
            "xrpcEndpoint": "https://lawfirm.etzhayyim.com",
            "kpiDashboardUrl": f"https://kpi-lawfirm.etzhayyim.com/{slug}",
            "tenant_id": tenant_id,
            "vertex_id": row["vertex_id"],
            "existing_status": row.get("status"),
        }

    # Different (slug, tier=other) collision check
    other_tier = _query(
        "SELECT tier, legal_name, country FROM vertex_lawfirm_tenant WHERE slug = :slug",
        {"slug": slug},
    )
    if other_tier:
        for r in other_tier:
            if r.get("legal_name") != legal_name or r.get("country") != country:
                return {"ok": False, "error": "SlugTaken",
                        "detail": f"slug '{slug}' already used by different firm"}

    tenant_did = _tenant_did(slug, tier)
    pds_url = _pds_url(slug, tier)
    kpi_url = f"https://kpi-lawfirm.etzhayyim.com/{slug}"
    now = _now_iso()
    consent_str = ",".join(consent_regions or []) if consent_regions else ""

    if not _execute(
        "INSERT INTO vertex_lawfirm_tenant "
        "(vertex_id, tenant_id, slug, tenant_did, legal_name, country, "
        " data_region, tier, status, pilot_lead_id, admin_email_ct, consent_regions, "
        " pds_url, xrpc_endpoint, kpi_dashboard_url, "
        " provisioned_at, created_at, sensitivity_ord, owner_did) "
        "VALUES (:vid, :tid, :slug, :did, :legal, :country, "
        " :region, :tier, 'active', :lead, :admin, :consent, "
        " :pds, 'https://lawfirm.etzhayyim.com', :kpi, "
        " :now, :now, 200, :owner)",
        {
            "vid": vertex_id, "tid": tenant_id, "slug": slug, "did": tenant_did,
            "legal": legal_name, "country": country, "region": data_region, "tier": tier,
            "lead": pilot_lead_id or None,
            "admin": _enc_field(admin_email),
            "consent": consent_str,
            "pds": pds_url, "kpi": kpi_url,
            "now": now, "owner": _FIRM_DID,
        },
    ):
        return {"ok": False, "error": "PersistFailed"}

    # Audit event
    event_vid = f"at://did:web:lawfirm.etzhayyim.com/com.etzhayyim.apps.lawfirm.tenantEvent/{tenant_id}-provisioned-{now}"
    _execute(
        "INSERT INTO vertex_lawfirm_tenant_event "
        "(vertex_id, tenant_id, event_kind, from_status, to_status, "
        " from_tier, to_tier, reason, actor_did, occurred_at, "
        " created_at, sensitivity_ord, owner_did) "
        "VALUES (:vid, :tid, 'provisioned', NULL, 'active', "
        " NULL, :tier, 'tenantBootstrap procedure', :actor, :now, "
        " :now, 200, :owner)",
        {
            "vid": event_vid, "tid": tenant_id, "tier": tier,
            "actor": _FIRM_DID, "now": now, "owner": _FIRM_DID,
        },
    )

    # tenant ↔ lead edge (sandbox tier only)
    if tier == "sandbox" and pilot_lead_id:
        lead_vid = f"at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.lawfirm.lead/{pilot_lead_id}"
        edge_id = f"edge:tenant:{tenant_id}:for-lead:{pilot_lead_id}"
        _execute(
            "INSERT INTO edge_lawfirm_tenant_lead "
            "(edge_id, src_vid, dst_vid, tenant_id, lead_id, rel_kind, "
            " created_at, sensitivity_ord, owner_did) "
            "VALUES (:eid, :src, :dst, :tid, :lead, 'sandbox_for_lead', "
            " :now, 200, :owner)",
            {
                "eid": edge_id, "src": vertex_id, "dst": lead_vid,
                "tid": tenant_id, "lead": pilot_lead_id, "now": now, "owner": _FIRM_DID,
            },
        )

    LOG.info(
        "tenant provisioned slug=%s tier=%s did=%s lead=%s",
        slug, tier, tenant_did, pilot_lead_id or "-",
    )
    return {
        "ok": True,
        "status": "created",
        "tenantDid": tenant_did,
        "pdsUrl": pds_url,
        "xrpcEndpoint": "https://lawfirm.etzhayyim.com",
        "kpiDashboardUrl": kpi_url,
        "tenant_id": tenant_id,
        "vertex_id": vertex_id,
    }


def _tenant_did(slug: str, tier: str) -> str:
    if tier == "sandbox":
        return f"did:web:{slug}.sandbox.lawfirm.etzhayyim.com"
    return f"did:web:{slug}.lawfirm.etzhayyim.com"


def _pds_url(slug: str, tier: str) -> str:
    if tier == "sandbox":
        return f"https://{slug}.sandbox.lawfirm.etzhayyim.com"
    return f"https://{slug}.lawfirm.etzhayyim.com"


# ── Task: lawfirm.tenant.suspend (pilot end, 90-day retention) ────────────────

async def task_lawfirm_tenant_suspend(
    slug: str = "",
    reason: str = "pilot-end",
) -> dict:
    if not slug:
        return {"ok": False, "error": "slug required"}

    rows = _query(
        "SELECT vertex_id, tenant_id, status FROM vertex_lawfirm_tenant WHERE slug = :slug",
        {"slug": slug},
    )
    if not rows:
        return {"ok": False, "error": "TenantNotFound"}

    now = _now_iso()
    suspended = 0
    for row in rows:
        if row.get("status") == "suspended":
            continue
        if _execute(
            "UPDATE vertex_lawfirm_tenant SET status = 'suspended', suspended_at = :now "
            "WHERE vertex_id = :vid",
            {"now": now, "vid": row["vertex_id"]},
        ):
            event_vid = f"at://did:web:lawfirm.etzhayyim.com/com.etzhayyim.apps.lawfirm.tenantEvent/{row['tenant_id']}-suspended-{now}"
            _execute(
                "INSERT INTO vertex_lawfirm_tenant_event "
                "(vertex_id, tenant_id, event_kind, from_status, to_status, "
                " reason, actor_did, occurred_at, created_at, sensitivity_ord, owner_did) "
                "VALUES (:vid, :tid, 'suspended', :from, 'suspended', "
                " :reason, :actor, :now, :now, 200, :owner)",
                {
                    "vid": event_vid, "tid": row["tenant_id"],
                    "from": row.get("status"), "reason": reason,
                    "actor": _FIRM_DID, "now": now, "owner": _FIRM_DID,
                },
            )
            suspended += 1

    return {"ok": True, "suspended_count": suspended}


# ── Task: lawfirm.tenant.promote (sandbox → saas-prod) ────────────────────────

async def task_lawfirm_tenant_promote(
    slug: str = "",
    monthly_rate_usd: float = 5000.0,
) -> dict:
    if not slug:
        return {"ok": False, "error": "slug required"}

    sandbox = _query(
        "SELECT vertex_id, tenant_id, country, data_region "
        "FROM vertex_lawfirm_tenant WHERE slug = :slug AND tier = 'sandbox' AND status = 'active'",
        {"slug": slug},
    )
    if not sandbox:
        return {"ok": False, "error": "ActiveSandboxNotFound"}

    # Provision saas-prod tier reusing the same firm metadata
    src = sandbox[0]
    legal_rows = _query(
        "SELECT legal_name, admin_email_ct, consent_regions, pilot_lead_id "
        "FROM vertex_lawfirm_tenant WHERE vertex_id = :vid",
        {"vid": src["vertex_id"]},
    )
    if not legal_rows:
        return {"ok": False, "error": "PromotionMetadataMissing"}
    meta = legal_rows[0]

    # Bootstrap the prod tier (idempotent)
    prod_result = await task_lawfirm_tenant_bootstrap(
        slug=slug,
        legal_name=meta["legal_name"],
        country=src.get("country", ""),
        data_region=src.get("data_region", "vultr-lax"),
        tier="saas-prod",
        pilot_lead_id="",
        admin_email="",  # already encrypted in source row, do not re-encrypt
        consent_regions=(meta.get("consent_regions") or "").split(",") if meta.get("consent_regions") else None,
    )
    if not prod_result.get("ok"):
        return prod_result

    # Audit promotion
    now = _now_iso()
    event_vid = f"at://did:web:lawfirm.etzhayyim.com/com.etzhayyim.apps.lawfirm.tenantEvent/{src['tenant_id']}-promoted-{now}"
    _execute(
        "INSERT INTO vertex_lawfirm_tenant_event "
        "(vertex_id, tenant_id, event_kind, from_status, to_status, "
        " from_tier, to_tier, reason, actor_did, occurred_at, "
        " created_at, sensitivity_ord, owner_did) "
        "VALUES (:vid, :tid, 'promoted', 'active', 'active', "
        " 'sandbox', 'saas-prod', :reason, :actor, :now, "
        " :now, 200, :owner)",
        {
            "vid": event_vid, "tid": src["tenant_id"],
            "reason": f"pilot conversion at USD {monthly_rate_usd}/mo",
            "actor": _FIRM_DID, "now": now, "owner": _FIRM_DID,
        },
    )

    return {
        "ok": True,
        "status": "promoted",
        "sandbox_tenant_id": src["tenant_id"],
        "prod_tenant_id": prod_result.get("tenant_id"),
        "prod_did": prod_result.get("tenantDid"),
        "monthly_rate_usd": monthly_rate_usd,
    }


# ── LangServer registration ─────────────────────────────────────────────────────

def register(app: Any, timeout_ms: int = 60_000) -> None:
    from pymagatama.langserver_compat import LangServerWorker
    if not isinstance(app, LangServerWorker):
        return

    @app.task(task_type="lawfirm.tenant.bootstrap",
              timeout_ms=timeout_ms, max_jobs_to_activate=4)
    async def _bootstrap(slug: str = "", legal_name: str = "",
                         country: str = "", data_region: str = "vultr-lax",
                         tier: str = "sandbox", pilot_lead_id: str = "",
                         admin_email: str = "",
                         consent_regions: list[str] | None = None) -> dict:
        return await task_lawfirm_tenant_bootstrap(
            slug=slug, legal_name=legal_name, country=country,
            data_region=data_region, tier=tier,
            pilot_lead_id=pilot_lead_id, admin_email=admin_email,
            consent_regions=consent_regions,
        )

    @app.task(task_type="lawfirm.tenant.suspend",
              timeout_ms=timeout_ms, max_jobs_to_activate=4)
    async def _suspend(slug: str = "", reason: str = "pilot-end") -> dict:
        return await task_lawfirm_tenant_suspend(slug=slug, reason=reason)

    @app.task(task_type="lawfirm.tenant.promote",
              timeout_ms=timeout_ms, max_jobs_to_activate=2)
    async def _promote(slug: str = "", monthly_rate_usd: float = 5000.0) -> dict:
        return await task_lawfirm_tenant_promote(
            slug=slug, monthly_rate_usd=monthly_rate_usd,
        )

    LOG.info("Registered tasks: lawfirm.tenant.{bootstrap,suspend,promote}")
