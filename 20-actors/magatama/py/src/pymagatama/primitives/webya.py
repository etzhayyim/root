"""
webya.etzhayyim.com — Zeebe task handlers (ADR-0056 + ADR-2605080200).

Task types registered under ZEEBE_WORKER_PROFILE=webya:
  webya.domain.provision          CF for SaaS Custom Hostname 発行
  webya.domain.checkAllPending    SSL ステータス一括確認 (R/PT30M BPMN)
  webya.seo.auditAllSites         週次 SEO 監査 (cron BPMN)

LangGraph-routed tasks (Zeebe 非実行 — dispatcher が直接 POST /runs):
  webya.site.generate             → assistant_id=webya_create_site
  webya.site.revise               → assistant_id=webya_revise_site

Coverage / query handlers:
  task_webya_get_site
  task_webya_list_sites
  task_webya_get_site_preview
  task_webya_coverage
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import time
import uuid
from typing import Any

from pymagatama.db_sync import sync_cursor
from pymagatama import llm

LOG = logging.getLogger(__name__)

# CF API settings (from env / K8s Secret)
_CF_API_TOKEN   = os.environ.get("CF_API_TOKEN", "")
_CF_ZONE_ID     = os.environ.get("WEBYA_CF_ZONE_ID", "")
_CF_PROXY_ORIGIN = "proxy-webya.etzhayyim.com"

ACTOR_DID = "did:web:webya.etzhayyim.com"


# ── Helpers ────────────────────────────────────────────────────────────────────

def _rq(sql_str: str, params: tuple = ()) -> list[Any]:
    try:
        with sync_cursor() as cur:
            cur.execute(sql_str, params)
            return cur.fetchall()
    except Exception as exc:
        LOG.warning("webya rq: %s", exc)
        return []


def _rx(sql_str: str, params: tuple = ()) -> None:
    with sync_cursor() as cur:
        cur.execute(sql_str, params)


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _slug_from_name(name: str) -> str:
    s = re.sub(r"[^\w\s-]", "", name.lower())
    s = re.sub(r"[\s_]+", "-", s)
    return s[:32].strip("-") or "site"


# ── task: webya.domain.provision ─────────────────────────────────────────────

async def task_webya_domain_provision(**kwargs: Any) -> dict[str, Any]:
    """CF for SaaS Custom Hostname を発行する。"""
    import httpx

    site_id = str(kwargs.get("siteId") or kwargs.get("site_id") or "")
    domain  = str(kwargs.get("domain") or "").strip().lower()

    if not site_id or not domain:
        return {"ok": False, "error": "siteId and domain are required"}

    if not _CF_API_TOKEN or not _CF_ZONE_ID:
        return {"ok": False, "error": "CF_API_TOKEN or WEBYA_CF_ZONE_ID not configured"}

    now = _now()
    domain_id = f"dom-{hashlib.sha256(f'{site_id}:{domain}'.encode()).hexdigest()[:16]}"
    vertex_id = f"at://{ACTOR_DID}/ai.gftd.apps.webya.domain/{domain_id}"

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"https://api.cloudflare.com/client/v4/zones/{_CF_ZONE_ID}/custom_hostnames",
                headers={"Authorization": f"Bearer {_CF_API_TOKEN}", "Content-Type": "application/json"},
                json={
                    "hostname": domain,
                    "ssl": {"method": "txt", "type": "dv", "settings": {"min_tls_version": "1.2"}},
                    "custom_origin_server": _CF_PROXY_ORIGIN,
                },
            )
        data = resp.json()
        if not data.get("success"):
            return {"ok": False, "error": str(data.get("errors", "CF API error"))}

        result = data["result"]
        cf_hostname_id = result["id"]
        ssl = result.get("ssl", {})
        verification = ssl.get("txt_name", ""), ssl.get("txt_value", "")
        txt_name, txt_value = verification

        _rx(
            """INSERT INTO vertex_webya_domain
               (vertex_id, domain_id, site_id, domain, cf_hostname_id,
                ssl_status, ownership_verified, dns_cname_target,
                verification_txt_name, verification_txt_value, provisioned_at)
               VALUES (%s, %s, %s, %s, %s, 'pending', FALSE, %s, %s, %s, %s)""",
            (vertex_id, domain_id, site_id, domain, cf_hostname_id,
             _CF_PROXY_ORIGIN, txt_name, txt_value, now),
        )
        _rx(
            "UPDATE vertex_webya_site SET custom_domain = %s, cf_custom_hostname_id = %s WHERE site_id = %s",
            (domain, cf_hostname_id, site_id),
        )

        LOG.info("domain.provision ok site_id=%s domain=%s cf_id=%s", site_id, domain, cf_hostname_id)
        return {
            "ok":           True,
            "cfHostnameId": cf_hostname_id,
            "cnameTarget":  _CF_PROXY_ORIGIN,
            "txtName":      txt_name,
            "txtValue":     txt_value,
            "sslStatus":    "pending",
        }

    except Exception as exc:
        LOG.error("domain.provision failed: %s", exc)
        return {"ok": False, "error": str(exc)}


# ── task: webya.domain.checkAllPending ───────────────────────────────────────

async def task_webya_domain_check_all_pending(**kwargs: Any) -> dict[str, Any]:
    """SSL pending な全ドメインを CF API で確認し status を更新。"""
    import httpx

    if not _CF_API_TOKEN or not _CF_ZONE_ID:
        return {"ok": True, "pendingCount": 0, "activatedCount": 0, "errorCount": 0,
                "error": "CF not configured"}

    rows = _rq(
        "SELECT domain_id, cf_hostname_id, domain FROM vertex_webya_domain WHERE ssl_status <> 'active' LIMIT 100",
    )
    pending_count  = len(rows)
    activated      = 0
    error_count    = 0

    async with httpx.AsyncClient(timeout=20) as client:
        for domain_id, cf_hostname_id, domain in rows:
            if not cf_hostname_id:
                continue
            try:
                resp = await client.get(
                    f"https://api.cloudflare.com/client/v4/zones/{_CF_ZONE_ID}/custom_hostnames/{cf_hostname_id}",
                    headers={"Authorization": f"Bearer {_CF_API_TOKEN}"},
                )
                data = resp.json()
                if not data.get("success"):
                    error_count += 1
                    continue
                result = data["result"]
                ssl_status = result.get("ssl", {}).get("status", "pending")
                ownership_verified = result.get("ownership_verification_http", {}).get("http_body") is not None

                _rx(
                    "UPDATE vertex_webya_domain SET ssl_status = %s, ownership_verified = %s WHERE domain_id = %s",
                    (ssl_status, ownership_verified, domain_id),
                )
                if ssl_status == "active":
                    activated += 1
                    _rx("UPDATE vertex_webya_site SET ssl_status = 'active' WHERE custom_domain = %s", (domain,))

            except Exception as exc:
                LOG.warning("checkAllPending domain_id=%s: %s", domain_id, exc)
                error_count += 1

    LOG.info("domain.checkAllPending pending=%d activated=%d errors=%d", pending_count, activated, error_count)
    return {"ok": True, "pendingCount": pending_count, "activatedCount": activated, "errorCount": error_count}


# ── task: webya.seo.auditAllSites ─────────────────────────────────────────────

async def task_webya_seo_audit_all_sites(**kwargs: Any) -> dict[str, Any]:
    """published サイトの全ページを SEO 監査し必要なら meta_description を更新。"""
    rows = _rq(
        "SELECT p.page_id, p.site_id, p.slug, p.title, p.meta_description "
        "FROM vertex_webya_page p "
        "JOIN vertex_webya_site s ON s.site_id = p.site_id "
        "WHERE s.status = 'published' AND p.status = 'published' LIMIT 500",
    )
    pages_audited = 0
    pages_updated = 0
    issues_found  = 0

    for page_id, site_id, slug, title, meta_desc in rows:
        pages_audited += 1
        issues: list[str] = []

        if not meta_desc or len(meta_desc) < 50:
            issues.append("meta_description too short")
        if not title:
            issues.append("title missing")

        if issues:
            issues_found += len(issues)
            if "meta_description too short" in issues:
                prompt = f"「{title}」ページのメタディスクリプション(60〜120文字)を日本語で生成。JSON: {{\"meta_description\": \"...\"}}"
                try:
                    result = llm.call_tier_json("fast", prompt, max_tokens=150)
                    new_meta = result.get("meta_description", "")[:120]
                    if new_meta:
                        _rx(
                            "UPDATE vertex_webya_page SET meta_description = %s, updated_at = %s WHERE page_id = %s",
                            (new_meta, _now(), page_id),
                        )
                        pages_updated += 1
                except Exception as exc:
                    LOG.warning("seo_audit page_id=%s: %s", page_id, exc)

    LOG.info("seo.auditAllSites audited=%d updated=%d issues=%d", pages_audited, pages_updated, issues_found)
    return {"ok": True, "sitesAudited": pages_audited, "pagesUpdated": pages_updated, "issuesFound": issues_found}


# ── task: webya.coverage ──────────────────────────────────────────────────────

async def task_webya_coverage(**kwargs: Any) -> dict[str, Any]:
    total_rows   = _rq("SELECT COUNT(*) FROM vertex_webya_site")
    published    = _rq("SELECT COUNT(*) FROM vertex_webya_site WHERE status = 'published'")
    generating   = _rq("SELECT COUNT(*) FROM vertex_webya_site WHERE status = 'generating'")
    ssl_pending  = _rq("SELECT COUNT(*) FROM vertex_webya_domain WHERE ssl_status <> 'active'")
    gen_queue    = _rq("SELECT COUNT(*) FROM vertex_webya_generation_job WHERE status IN ('pending', 'running')")
    by_prof      = _rq("SELECT profession_kind, status, site_count FROM mv_webya_sites_by_status")

    return {
        "ok":              True,
        "totalSites":      (total_rows[0][0] if total_rows else 0),
        "publishedSites":  (published[0][0]  if published  else 0),
        "generatingSites": (generating[0][0] if generating else 0),
        "sslPending":      (ssl_pending[0][0] if ssl_pending else 0),
        "generationQueue": (gen_queue[0][0]  if gen_queue  else 0),
        "byProfession":    [
            {"professionKind": r[0], "status": r[1], "siteCount": r[2]} for r in by_prof
        ],
    }


# ── task: webya.getSite ───────────────────────────────────────────────────────

async def task_webya_get_site(**kwargs: Any) -> dict[str, Any]:
    site_id = str(kwargs.get("siteId") or kwargs.get("site_id") or "")
    if not site_id:
        return {"ok": False, "error": "siteId required"}

    rows = _rq(
        "SELECT site_id, site_name, template_id, custom_domain, subdomain, "
        "ssl_status, status, published_at FROM vertex_webya_site WHERE site_id = %s LIMIT 1",
        (site_id,),
    )
    if not rows:
        return {"ok": False, "error": "site not found"}

    r = rows[0]
    pages = _rq("SELECT slug, title, status FROM vertex_webya_page WHERE site_id = %s", (site_id,))
    job   = _rq(
        "SELECT job_id, status FROM vertex_webya_generation_job WHERE site_id = %s ORDER BY started_at DESC LIMIT 1",
        (site_id,),
    )

    # Get profession_kind from template mapping
    tmpl = _rq("SELECT profession_kind FROM vertex_webya_template WHERE template_id = %s LIMIT 1", (r[2],))
    profession_kind = tmpl[0][0] if tmpl else ""

    return {
        "ok": True,
        "site": {
            "siteId":        r[0],
            "siteName":      r[1],
            "professionKind": profession_kind,
            "status":        r[6],
            "subdomain":     r[4],
            "customDomain":  r[3],
            "sslStatus":     r[5],
            "publishedAt":   r[7],
            "pages":         [{"slug": p[0], "title": p[1], "status": p[2]} for p in pages],
            "latestJobId":   job[0][0] if job else None,
            "latestJobStatus": job[0][1] if job else None,
        },
    }


# ── task: webya.getSitePreview ────────────────────────────────────────────────

async def task_webya_get_site_preview(**kwargs: Any) -> dict[str, Any]:
    site_id = str(kwargs.get("siteId") or kwargs.get("site_id") or "")
    slug    = str(kwargs.get("slug") or "home")

    rows = _rq(
        "SELECT slug, title, html_content, json_ld, status, updated_at "
        "FROM vertex_webya_page WHERE site_id = %s AND slug = %s LIMIT 1",
        (site_id, slug),
    )
    if not rows:
        return {"ok": False, "error": f"page not found: {slug}"}

    r = rows[0]
    return {
        "ok":          True,
        "slug":        r[0],
        "htmlContent": r[2] or "",
        "jsonLd":      r[3] or "",
        "status":      r[4],
        "updatedAt":   r[5],
    }


# ── task: webya.listSites ─────────────────────────────────────────────────────

async def task_webya_list_sites(**kwargs: Any) -> dict[str, Any]:
    profession_kind = kwargs.get("professionKind") or kwargs.get("profession_kind") or None
    status          = kwargs.get("status") or None
    limit           = int(kwargs.get("limit") or 50)
    offset          = int(kwargs.get("offset") or 0)

    # Build WHERE clause safely
    conditions = []
    params: list[Any] = []

    if profession_kind:
        # Join via template for profession_kind
        conditions.append("t.profession_kind = %s")
        params.append(profession_kind)
    if status:
        conditions.append("s.status = %s")
        params.append(status)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    join_clause = "LEFT JOIN vertex_webya_template t ON t.template_id = s.template_id" if profession_kind else ""

    rows = _rq(
        f"SELECT s.site_id, s.site_name, s.status, s.subdomain, s.custom_domain, s.published_at "
        f"FROM vertex_webya_site s {join_clause} {where} "
        f"ORDER BY s.created_at DESC LIMIT {int(limit)} OFFSET {int(offset)}",
        tuple(params),
    )
    count = _rq(
        f"SELECT COUNT(*) FROM vertex_webya_site s {join_clause} {where}",
        tuple(params),
    )

    return {
        "ok":    True,
        "sites": [
            {
                "siteId":       r[0],
                "siteName":     r[1],
                "status":       r[2],
                "subdomain":    r[3],
                "customDomain": r[4],
                "publishedAt":  r[5],
            }
            for r in rows
        ],
        "total":  count[0][0] if count else 0,
        "limit":  limit,
        "offset": offset,
    }


# ── Registration helper ───────────────────────────────────────────────────────

def register(worker: Any) -> None:
    """webya Zeebe worker にタスクハンドラを登録する。"""
    worker.task("webya.domain.provision")(task_webya_domain_provision)
    worker.task("webya.domain.checkAllPending")(task_webya_domain_check_all_pending)
    worker.task("webya.seo.auditAllSites")(task_webya_seo_audit_all_sites)
    # Query helpers (dispatcher 経由で XRPC として公開)
    worker.task("webya.coverage")(task_webya_coverage)
    worker.task("webya.getSite")(task_webya_get_site)
    worker.task("webya.getSitePreview")(task_webya_get_site_preview)
    worker.task("webya.listSites")(task_webya_list_sites)
    LOG.info("webya primitives registered (7 tasks)")
