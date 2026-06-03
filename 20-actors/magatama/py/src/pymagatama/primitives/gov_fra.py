"""FRA Government states actor primitives.

This module moves the `did:web:fra-state.etzhayyim.com` app actor off its
dedicated Cloudflare Worker path. The public edge keeps only XRPC/MCP
facade duties; these functions run as Zeebe jobs in Kubernetes and write
the same graph-visible state the Worker previously wrote via host-sdk.
"""

from __future__ import annotations

import asyncio
import datetime as _dt
import hashlib
import hmac
import json
import os
import re
import time
import urllib.error as _u_err
import urllib.request as _u_req
from typing import Any

from pymagatama.db_sync import sync_cursor


PRIMARY_DID = "did:web:fra-state.etzhayyim.com"
DOMAIN_CODE = "fra"
SITE_NANOID = "w3bpg001"
SITE_GOV_TOPIC_DID = "did:web:site.etzhayyim.com:topic:government"
PDS_BASE = os.environ.get("PDS_URL", "https://atproto.etzhayyim.com")
PDS_SERVICE_AUTH_TOKEN = os.environ.get("PDS_SERVICE_AUTH_TOKEN", "").strip()
PDS_SERVICE_AUTH_MINT_URL = os.environ.get(
    "PDS_SERVICE_AUTH_MINT_URL",
    f"{PDS_BASE}/_internal/mint-pds-bearer",
).strip()
PDS_SERVICE_AUTH_MINT_SECRET = os.environ.get("PDS_SERVICE_AUTH_MINT_SECRET", "").strip()
PDS_LEGACY_INTERNAL_TRUST = os.environ.get("PDS_LEGACY_INTERNAL_TRUST", "0") == "1"
try:
    PDS_SERVICE_AUTH_TTL_SEC = int(os.environ.get("PDS_SERVICE_AUTH_TTL_SEC", "600"))
except ValueError:
    PDS_SERVICE_AUTH_TTL_SEC = 600
PDS_SERVICE_AUTH_TTL_SEC = max(30, min(600, PDS_SERVICE_AUTH_TTL_SEC))
_PDS_SERVICE_AUTH_CACHE: dict[str, dict[str, Any]] = {}

_MINISTRY_NDJSON = """\
{"path":"premier-ministre","name":"Premier ministre","nameEn":"Prime Minister's Office","website":"https://www.gouvernement.fr/","contract":"Constitution 1958 Art. 21","tags":["cofog:01","executive","prime-minister"],"orgTier":"ministry"}
{"path":"mdef","name":"Ministère des Armées","nameEn":"Ministry of the Armed Forces","website":"https://www.defense.gouv.fr/","contract":"Constitution 1958 Art. 15","tags":["cofog:02","defence","military"],"orgTier":"ministry"}
{"path":"mae","name":"Ministère de l'Europe et des Affaires étrangères","nameEn":"Ministry for Europe and Foreign Affairs","website":"https://www.diplomatie.gouv.fr/","contract":"Constitution 1958 Art. 52","tags":["cofog:01.2","foreign-affairs","diplomacy","europe"],"orgTier":"ministry"}
{"path":"mfin","name":"Ministère de l'Économie et des Finances","nameEn":"Ministry of Economy and Finance","website":"https://www.economie.gouv.fr/","contract":"Constitution 1958 Art. 34","tags":["cofog:01.1","finance","economy","taxation"],"orgTier":"ministry"}
{"path":"mjust","name":"Ministère de la Justice","nameEn":"Ministry of Justice","website":"https://www.justice.gouv.fr/","contract":"Constitution 1958 Art. 64","tags":["cofog:03","justice","courts"],"orgTier":"ministry"}
{"path":"mint","name":"Ministère de l'Intérieur et des Outre-mer","nameEn":"Ministry of the Interior","website":"https://www.interieur.gouv.fr/","contract":"Constitution 1958 Art. 72","tags":["cofog:03","interior","police","prefectures"],"orgTier":"ministry"}
{"path":"msante","name":"Ministère de la Santé et de la Prévention","nameEn":"Ministry of Health","website":"https://sante.gouv.fr/","contract":"Constitution 1958 Art. 34","tags":["cofog:07","health"],"orgTier":"ministry"}
{"path":"mesr","name":"Ministère de l'Enseignement supérieur et de la Recherche","nameEn":"Ministry of Higher Education and Research","website":"https://www.enseignementsup-recherche.gouv.fr/","contract":"Constitution 1958 Art. 34","tags":["cofog:09","higher-education","research"],"orgTier":"ministry"}
{"path":"men","name":"Ministère de l'Éducation nationale","nameEn":"Ministry of National Education","website":"https://www.education.gouv.fr/","contract":"Constitution 1958 Art. 34","tags":["cofog:09","education"],"orgTier":"ministry"}
{"path":"mtravail","name":"Ministère du Travail, de la Santé et des Solidarités","nameEn":"Ministry of Labour","website":"https://www.travail-emploi.gouv.fr/","contract":"Constitution 1958 Art. 34","tags":["cofog:04","labour","employment"],"orgTier":"ministry"}
{"path":"mtr","name":"Ministère de la Transition écologique","nameEn":"Ministry of Ecological Transition","website":"https://www.ecologie.gouv.fr/","contract":"Constitution 1958 Art. 34","tags":["cofog:05","environment","transport","energy"],"orgTier":"ministry"}
{"path":"magri","name":"Ministère de l'Agriculture","nameEn":"Ministry of Agriculture","website":"https://agriculture.gouv.fr/","contract":"Constitution 1958 Art. 34","tags":["cofog:04.2","agriculture","food"],"orgTier":"ministry"}
{"path":"mcc","name":"Ministère de la Culture","nameEn":"Ministry of Culture","website":"https://www.culture.gouv.fr/","contract":"Constitution 1958 Art. 34","tags":["cofog:08","culture","heritage"],"orgTier":"ministry"}
{"path":"assemblee-nationale","name":"Assemblée nationale","nameEn":"National Assembly","website":"https://www.assemblee-nationale.fr/","contract":"Constitution 1958 Art. 24","tags":["cofog:01","legislature","lower-house"],"orgTier":"agency"}
{"path":"senat","name":"Sénat","nameEn":"Senate","website":"https://www.senat.fr/","contract":"Constitution 1958 Art. 24","tags":["cofog:01","legislature","upper-house"],"orgTier":"agency"}
{"path":"conseil-constitutionnel","name":"Conseil constitutionnel","nameEn":"Constitutional Council","website":"https://www.conseil-constitutionnel.fr/","contract":"Constitution 1958 Art. 56-63","tags":["cofog:03","judiciary","constitutional-council"],"orgTier":"agency"}
"""

_STATE_NDJSON = """\
{"path":"region:auvergne-rhone-alpes","name":"Auvergne-Rhône-Alpes","nameEn":"Auvergne-Rhône-Alpes","website":"https://www.auvergnerhonealpes.fr/","contract":"CGCT Art. L4111-1","tags":["cofog:01","region","l5"],"orgTier":"state"}
{"path":"region:bourgogne-franche-comte","name":"Bourgogne-Franche-Comté","nameEn":"Bourgogne-Franche-Comté","website":"https://www.bourgognefranchecomte.fr/","contract":"CGCT Art. L4111-1","tags":["cofog:01","region","l5"],"orgTier":"state"}
{"path":"region:bretagne","name":"Bretagne","nameEn":"Brittany","website":"https://www.bretagne.bzh/","contract":"CGCT Art. L4111-1","tags":["cofog:01","region","l5"],"orgTier":"state"}
{"path":"region:centre-val-de-loire","name":"Centre-Val de Loire","nameEn":"Centre-Val de Loire","website":"https://www.centre-valdeloire.fr/","contract":"CGCT Art. L4111-1","tags":["cofog:01","region","l5"],"orgTier":"state"}
{"path":"region:corse","name":"Corse","nameEn":"Corsica","website":"https://www.isula.corsica/","contract":"CGCT Art. L4421-1 (special statute)","tags":["cofog:01","region","l5","special-statute"],"orgTier":"state"}
{"path":"region:grand-est","name":"Grand Est","nameEn":"Grand Est","website":"https://www.grandest.fr/","contract":"CGCT Art. L4111-1","tags":["cofog:01","region","l5"],"orgTier":"state"}
{"path":"region:hauts-de-france","name":"Hauts-de-France","nameEn":"Hauts-de-France","website":"https://www.hautsdefrance.fr/","contract":"CGCT Art. L4111-1","tags":["cofog:01","region","l5"],"orgTier":"state"}
{"path":"region:ile-de-france","name":"Île-de-France","nameEn":"Île-de-France","website":"https://www.iledefrance.fr/","contract":"CGCT Art. L4111-1","tags":["cofog:01","region","l5","capital-region"],"orgTier":"state"}
{"path":"region:normandie","name":"Normandie","nameEn":"Normandy","website":"https://www.normandie.fr/","contract":"CGCT Art. L4111-1","tags":["cofog:01","region","l5"],"orgTier":"state"}
{"path":"region:nouvelle-aquitaine","name":"Nouvelle-Aquitaine","nameEn":"Nouvelle-Aquitaine","website":"https://www.nouvelle-aquitaine.fr/","contract":"CGCT Art. L4111-1","tags":["cofog:01","region","l5","largest-region"],"orgTier":"state"}
{"path":"region:occitanie","name":"Occitanie","nameEn":"Occitanie","website":"https://www.laregion.fr/","contract":"CGCT Art. L4111-1","tags":["cofog:01","region","l5"],"orgTier":"state"}
{"path":"region:pays-de-la-loire","name":"Pays de la Loire","nameEn":"Pays de la Loire","website":"https://www.paysdelaloire.fr/","contract":"CGCT Art. L4111-1","tags":["cofog:01","region","l5"],"orgTier":"state"}
{"path":"region:provence-alpes-cote-dazur","name":"Provence-Alpes-Côte d'Azur","nameEn":"Provence-Alpes-Côte d'Azur","website":"https://www.maregionsud.fr/","contract":"CGCT Art. L4111-1","tags":["cofog:01","region","l5"],"orgTier":"state"}
{"path":"region:guadeloupe","name":"Guadeloupe","nameEn":"Guadeloupe","website":"https://www.regionguadeloupe.fr/","contract":"CGCT Art. L4111-1","tags":["cofog:01","region","l5","overseas"],"orgTier":"state"}
{"path":"region:martinique","name":"Martinique","nameEn":"Martinique","website":"https://www.collectivitedemartinique.mq/","contract":"CGCT Art. L7211-1 (CTU)","tags":["cofog:01","region","l5","overseas"],"orgTier":"state"}
{"path":"region:guyane","name":"Guyane","nameEn":"French Guiana","website":"https://www.ctguyane.fr/","contract":"CGCT Art. L7111-1 (CTU)","tags":["cofog:01","region","l5","overseas"],"orgTier":"state"}
{"path":"region:la-reunion","name":"La Réunion","nameEn":"Réunion","website":"https://www.regionreunion.com/","contract":"CGCT Art. L4111-1","tags":["cofog:01","region","l5","overseas"],"orgTier":"state"}
{"path":"region:mayotte","name":"Mayotte","nameEn":"Mayotte","website":"https://www.conseil-mayotte.fr/","contract":"CGCT Art. L3511-1","tags":["cofog:01","region","l5","overseas"],"orgTier":"state"}
"""


def _utc_now_iso() -> str:
    return _dt.datetime.now(tz=_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _url_to_domain_slug(url: str) -> str:
    try:
        host = re.sub(r"^https?://", "", url).split("/", 1)[0]
        host = re.sub(r"^(www|web)\.", "", host)
        return host.replace(".", "-")
    except Exception:
        return ""


def _load_seed_orgs() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for blob in (_MINISTRY_NDJSON, _STATE_NDJSON):
        for line in blob.splitlines():
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _vertex_id(path: str) -> str:
    return f"at://{PRIMARY_DID}/com.etzhayyim.apps.states.govOrg/{path}"


def _repo_rkey(prefix: str, key: str) -> str:
    stamp = _dt.datetime.now(tz=_dt.UTC).strftime("%Y%m%d%H%M%S%f")
    safe = re.sub(r"[^a-zA-Z0-9._~-]+", "-", key).strip("-")[:80] or "record"
    return f"{prefix}-{safe}-{stamp}"


def _http_post_json(url: str, payload: dict[str, Any], headers: dict[str, str], timeout: float = 30.0) -> dict[str, Any]:
    body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    merged_headers = {
        "User-Agent": "etzhayyim-pymagatama-gov-afg/0.1",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    merged_headers.update(headers)
    req = _u_req.Request(url, data=body, headers=merged_headers, method="POST")
    try:
        with _u_req.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            status = int(resp.status)
    except _u_err.HTTPError as e:
        raw = e.read()
        status = int(e.code)
    except Exception as e:  # noqa: BLE001
        return {"status": -1, "body": {"error": f"transport: {e}"}}
    try:
        parsed: Any = json.loads(raw.decode("utf-8"))
    except Exception:
        parsed = {"raw": raw.decode("utf-8", errors="replace")[:500]}
    return {"status": status, "body": parsed}


def _mint_pds_service_auth(lxm: str) -> str:
    cached = _PDS_SERVICE_AUTH_CACHE.get(lxm)
    now = int(time.time())
    if cached and int(cached.get("expiresAt", 0)) > now + 30:
        token = str(cached.get("token") or "")
        if token:
            return token
    if not PDS_SERVICE_AUTH_MINT_URL or not PDS_SERVICE_AUTH_MINT_SECRET:
        return ""
    payload = {"lxm": lxm, "ttlSeconds": PDS_SERVICE_AUTH_TTL_SEC}
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    sig = hmac.new(PDS_SERVICE_AUTH_MINT_SECRET.encode("utf-8"), body, hashlib.sha256).hexdigest()
    req = _u_req.Request(
        PDS_SERVICE_AUTH_MINT_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "x-bpmn-auth": sig,
        },
        method="POST",
    )
    try:
        with _u_req.urlopen(req, timeout=10.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return ""
    token = str(data.get("token") or "")
    expires_at = int(data.get("expiresAt") or (now + PDS_SERVICE_AUTH_TTL_SEC))
    if token:
        _PDS_SERVICE_AUTH_CACHE[lxm] = {"token": token, "expiresAt": expires_at}
    return token


async def _pds_xrpc(lxm: str, payload: dict[str, Any]) -> dict[str, Any]:
    token = await asyncio.to_thread(_mint_pds_service_auth, lxm)
    bearer = token or PDS_SERVICE_AUTH_TOKEN
    headers: dict[str, str] = {}
    if bearer:
        headers["Authorization"] = f"Bearer {bearer}"
    elif PDS_LEGACY_INTERNAL_TRUST:
        headers["x-magatama-verified"] = "true"
    else:
        return {"status": 401, "body": {"error": "PDS service auth unavailable"}}
    return await asyncio.to_thread(_http_post_json, f"{PDS_BASE}/xrpc/{lxm}", payload, headers)


def _insert_repo_record(repo: str, collection: str, rkey: str, record: dict[str, Any]) -> str:
    created_at = str(record.get("createdAt") or _utc_now_iso())
    uri = f"at://{repo}/{collection}/{rkey}"
    if collection != "app.bsky.feed.post":
        value_json = json.dumps(record, separators=(",", ":"), ensure_ascii=False)
        if collection == "actorManifest":
            path = str(record.get("path") or rkey)
            params = {
                "vertex_id": uri,
                "record_key": rkey,
                "record_kind": collection,
                "path": path,
                "country": str(record.get("country") or DOMAIN_CODE),
                "display_name": str(record.get("displayName") or ""),
                "description": str(record.get("description") or ""),
                "performer_type": str(record.get("performerType") or ""),
                "agent_type": str(record.get("agentType") or ""),
                "is_bot": bool(record.get("isBot") or False),
                "value_json": value_json,
                "indexed_at": created_at,
                "created_at": created_at,
                "updated_at": str(record.get("updated_at") or created_at),
                "actor_did": repo,
                "org_did": repo,
                "owner_did": PRIMARY_DID,
                "sensitivity_ord": 2,
            }
            with sync_cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO vertex_gov_actor_manifest
                      (vertex_id,record_key,record_kind,path,country,display_name,description,performer_type,agent_type,is_bot,value_json,indexed_at,created_at,updated_at,actor_did,org_did,owner_did,sensitivity_ord)
                    VALUES (%(vertex_id)s,%(record_key)s,%(record_kind)s,%(path)s,%(country)s,%(display_name)s,%(description)s,%(performer_type)s,%(agent_type)s,%(is_bot)s,%(value_json)s,%(indexed_at)s,%(created_at)s,%(updated_at)s,%(actor_did)s,%(org_did)s,%(owner_did)s,%(sensitivity_ord)s)
                    ON CONFLICT (vertex_id) DO UPDATE SET
                      display_name = EXCLUDED.display_name,
                      description = EXCLUDED.description,
                      value_json = EXCLUDED.value_json,
                      indexed_at = EXCLUDED.indexed_at,
                      updated_at = EXCLUDED.updated_at
                    """,
                    params,
                )
            return uri
        if collection == "com.etzhayyim.apps.states.govOrgSiteDep":
            path = str(record.get("path") or "")
            site_did = str(record.get("siteDid") or "")
            params = {
                "edge_id": uri,
                "record_key": rkey,
                "from_vertex_id": _vertex_id(path) if path else repo,
                "to_vertex_id": site_did,
                "path": path,
                "site_nanoid": str(record.get("siteNanoid") or ""),
                "site_topic_did": str(record.get("siteTopicDid") or ""),
                "site_did": site_did,
                "value_json": value_json,
                "indexed_at": created_at,
                "created_at": created_at,
                "updated_at": str(record.get("updated_at") or created_at),
                "actor_did": repo,
                "org_did": str(record.get("orgId") or "anon"),
                "owner_did": repo,
                "sensitivity_ord": 2,
            }
            with sync_cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO edge_gov_org_site_dependency
                      (edge_id,record_key,from_vertex_id,to_vertex_id,path,site_nanoid,site_topic_did,site_did,value_json,indexed_at,created_at,updated_at,actor_did,org_did,owner_did,sensitivity_ord)
                    VALUES (%(edge_id)s,%(record_key)s,%(from_vertex_id)s,%(to_vertex_id)s,%(path)s,%(site_nanoid)s,%(site_topic_did)s,%(site_did)s,%(value_json)s,%(indexed_at)s,%(created_at)s,%(updated_at)s,%(actor_did)s,%(org_did)s,%(owner_did)s,%(sensitivity_ord)s)
                    ON CONFLICT (edge_id) DO UPDATE SET
                      value_json = EXCLUDED.value_json,
                      indexed_at = EXCLUDED.indexed_at,
                      updated_at = EXCLUDED.updated_at,
                      site_did = EXCLUDED.site_did,
                      to_vertex_id = EXCLUDED.to_vertex_id
                    """,
                    params,
                )
            return uri
        raise ValueError(f"unsupported gov collection: {collection!r}")
    params = {
        "vertex_id": uri,
        "record_kind": collection,
        "record_key": rkey,
        "label": "GovRecord",
        "status": "active",
        "value_json": json.dumps(record, separators=(",", ":"), ensure_ascii=False),
        "indexed_at": created_at,
        "created_at": created_at,
        "updated_at": str(record.get("updated_at") or record.get("updatedAt") or created_at),
        "org_id": str(record.get("orgId") or "anon"),
        "user_id": str(record.get("userId") or "anon"),
        "actor_id": str(record.get("actorId") or repo),
        "actor_did": repo,
        "org_did": str(record.get("orgDid") or "anon"),
        "owner_did": repo,
        "sensitivity_ord": 2,
    }
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_gov_record (
              vertex_id, record_kind, record_key, label, status, value_json,
              indexed_at, created_at, updated_at, org_id, user_id, actor_id,
              actor_did, org_did, owner_did, sensitivity_ord
            )
            VALUES (
              %(vertex_id)s, %(record_kind)s, %(record_key)s, %(label)s, %(status)s,
              %(value_json)s, %(indexed_at)s, %(created_at)s, %(updated_at)s,
              %(org_id)s, %(user_id)s, %(actor_id)s, %(actor_did)s, %(org_did)s,
              %(owner_did)s, %(sensitivity_ord)s
            )
            ON CONFLICT (vertex_id) DO UPDATE SET
              value_json = EXCLUDED.value_json,
              indexed_at = EXCLUDED.indexed_at,
              updated_at = EXCLUDED.updated_at,
              status = EXCLUDED.status
            """,
            params,
        )
    return uri


def _upsert_gov_org(row: dict[str, Any]) -> None:
    now = _utc_now_iso()
    path = str(row["path"])
    params = {
        "vertex_id": _vertex_id(path),
        "sensitivity_ord": 1,
        "owner_did": PRIMARY_DID,
        "path": path,
        "name": str(row.get("name") or ""),
        "name_en": str(row.get("nameEn") or row.get("name_en") or ""),
        "website": str(row.get("website") or ""),
        "contract": str(row.get("contract") or ""),
        "tags": json.dumps(row.get("tags") or [], separators=(",", ":"), ensure_ascii=False),
        "domain_code": DOMAIN_CODE,
        "org_tier": str(row.get("orgTier") or row.get("org_tier") or ""),
        "site_domain_slug": str(row.get("site_domain_slug") or _url_to_domain_slug(str(row.get("website") or ""))),
        "site_followed": str(row.get("site_followed") or "false"),
        "did_registered": str(row.get("did_registered") or "false"),
        "last_ingested_at": str(row.get("last_ingested_at") or ""),
        "last_content_hash": str(row.get("last_content_hash") or ""),
        "last_kyumei_at": str(row.get("last_kyumei_at") or ""),
        "last_shinka_at": str(row.get("last_shinka_at") or ""),
        "created_at": str(row.get("created_at") or now),
        "props": json.dumps(row.get("props") or {}, separators=(",", ":"), ensure_ascii=False),
    }
    with sync_cursor() as cur:
        cur.execute("DELETE FROM vertex_gov_org WHERE vertex_id = %(vertex_id)s", params)
        cur.execute(
            """
            INSERT INTO vertex_gov_org (
              vertex_id, sensitivity_ord, owner_did, path, name, name_en,
              website, contract, tags, domain_code, org_tier, site_domain_slug,
              site_followed, did_registered, last_ingested_at, last_content_hash,
              last_kyumei_at, last_shinka_at, created_at, props
            )
            VALUES (
              %(vertex_id)s, %(sensitivity_ord)s, %(owner_did)s, %(path)s,
              %(name)s, %(name_en)s, %(website)s, %(contract)s, %(tags)s,
              %(domain_code)s, %(org_tier)s, %(site_domain_slug)s,
              %(site_followed)s, %(did_registered)s, %(last_ingested_at)s,
              %(last_content_hash)s, %(last_kyumei_at)s, %(last_shinka_at)s,
              %(created_at)s, %(props)s
            )
            """,
            params,
        )


def _direct_fetch_hash(url: str, timeout: int = 10) -> tuple[str, str]:
    """Fetch url and return (md5_content_hash, text_snippet). Returns ('', '') on failure."""
    if not url or not url.startswith("http"):
        return "", ""
    try:
        req = _u_req.Request(url, headers={"User-Agent": "GovBot/1.0"})
        with _u_req.urlopen(req, timeout=timeout) as resp:
            body = resp.read(65536)
        content_hash = hashlib.md5(body).hexdigest()
        text = re.sub(r"<[^>]+>", " ", body.decode("utf-8", errors="replace"))
        text = re.sub(r"\s+", " ", text).strip()[:300]
        return content_hash, text
    except Exception:
        return "", ""


def _update_gov_org_fields(path: str, fields: dict[str, str]) -> None:
    allowed = {
        "site_followed",
        "did_registered",
        "last_ingested_at",
        "last_content_hash",
        "last_kyumei_at",
        "last_shinka_at",
    }
    updates = {k: str(v) for k, v in fields.items() if k in allowed}
    if not path or not updates:
        return
    set_sql = ", ".join(f"{key} = %({key})s" for key in updates)
    params: dict[str, Any] = {
        "domain_code": DOMAIN_CODE,
        "owner_did": PRIMARY_DID,
        "path": path,
        **updates,
    }
    with sync_cursor() as cur:
        cur.execute(
            (
                f"UPDATE vertex_gov_org SET {set_sql} "
                "WHERE domain_code = %(domain_code)s AND owner_did = %(owner_did)s AND path = %(path)s"
            ),
            params,
        )


def _get_org(path: str) -> dict[str, Any] | None:
    with sync_cursor() as cur:
        cur.execute(
            """
            SELECT path, name, name_en, website, contract, tags, org_tier,
                   site_domain_slug, site_followed, did_registered,
                   last_ingested_at, last_content_hash, last_kyumei_at,
                   last_shinka_at, created_at
              FROM vertex_gov_org
             WHERE domain_code = %s AND owner_did = %s AND path = %s
             LIMIT 1
            """,
            (DOMAIN_CODE, PRIMARY_DID, path),
        )
        row = cur.fetchone()
    if not row:
        return None
    keys = [
        "path", "name", "name_en", "website", "contract", "tags", "org_tier",
        "site_domain_slug", "site_followed", "did_registered",
        "last_ingested_at", "last_content_hash", "last_kyumei_at",
        "last_shinka_at", "created_at",
    ]
    return dict(zip(keys, row))


def task_gov_fra_seed_orgs(limit: int = 30) -> dict[str, Any]:
    limit = max(1, min(int(limit or 30), 100))
    with sync_cursor() as cur:
        cur.execute(
            (
                "SELECT path FROM vertex_gov_org "
                "WHERE domain_code = %s AND owner_did = %s AND name_en != '' LIMIT 10000"
            ),
            (DOMAIN_CODE, PRIMARY_DID),
        )
        existing = {str(r[0]) for r in cur.fetchall()}
    pending = [row for row in _load_seed_orgs() if row["path"] not in existing]
    written = 0
    for row in pending[:limit]:
        _upsert_gov_org(row)
        written += 1
    return {"ok": True, "seeded": written, "remaining": max(0, len(pending) - written)}


def task_gov_fra_resolve_org_path(path: str = "") -> dict[str, Any]:
    path = str(path or "").strip()
    if not path:
        return {"error": "missing path"}
    row = _get_org(path)
    if not row:
        return {"error": f"not found: {path}"}
    return {
        "did": f"{PRIMARY_DID}:{path}",
        "name": str(row.get("name") or ""),
        "nameEn": str(row.get("name_en") or ""),
        "website": str(row.get("website") or ""),
    }


def task_gov_fra_list_orgs(orgTier: str = "", offset: int = 0, limit: int = 50) -> dict[str, Any]:
    org_tier = str(orgTier or "").strip()
    offset = max(0, int(offset or 0))
    limit = max(1, min(int(limit or 50), 100))
    params: list[Any] = [DOMAIN_CODE, PRIMARY_DID]
    where = "domain_code = %s AND owner_did = %s AND name_en != ''"
    if org_tier:
        where += " AND org_tier = %s"
        params.append(org_tier)
    with sync_cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM vertex_gov_org WHERE {where}", tuple(params))
        total = int((cur.fetchone() or [0])[0] or 0)
        cur.execute(
            f"""
            SELECT path, name, name_en, website, did_registered
              FROM vertex_gov_org
             WHERE {where}
             ORDER BY path
             LIMIT {limit} OFFSET {offset}
            """,
            tuple(params),
        )
        rows = cur.fetchall()
    return {
        "orgs": [
            {
                "path": str(r[0] or ""),
                "did": f"{PRIMARY_DID}:{str(r[0] or '')}",
                "name": str(r[1] or ""),
                "nameEn": str(r[2] or ""),
                "website": str(r[3] or ""),
                "didRegistered": str(r[4] or "") == "true",
            }
            for r in rows
        ],
        "total": total,
    }


async def task_gov_fra_register_dids(limit: int = 10) -> dict[str, Any]:
    limit = max(1, min(int(limit or 10), 50))
    with sync_cursor() as cur:
        cur.execute(
            f"""
            SELECT path, name, name_en, website, contract, tags, org_tier,
                   site_domain_slug, site_followed, last_ingested_at,
                   last_content_hash, last_kyumei_at, last_shinka_at, created_at
              FROM vertex_gov_org
             WHERE domain_code = %s AND owner_did = %s AND name_en != '' AND did_registered != 'true'
             ORDER BY path
             LIMIT {limit}
            """,
            (DOMAIN_CODE, PRIMARY_DID),
        )
        rows = cur.fetchall()
    registered: list[str] = []
    pds_results: list[dict[str, Any]] = []
    for r in rows:
        row = {
            "path": str(r[0] or ""),
            "name": str(r[1] or ""),
            "name_en": str(r[2] or ""),
            "website": str(r[3] or ""),
            "contract": str(r[4] or ""),
            "tags": json.loads(str(r[5] or "[]")),
            "org_tier": str(r[6] or ""),
            "site_domain_slug": str(r[7] or ""),
            "site_followed": str(r[8] or "false"),
            "last_ingested_at": str(r[9] or ""),
            "last_content_hash": str(r[10] or ""),
            "last_kyumei_at": str(r[11] or ""),
            "last_shinka_at": str(r[12] or ""),
            "created_at": str(r[13] or _utc_now_iso()),
            "did_registered": "true",
        }
        path = row["path"]
        org_did = f"{PRIMARY_DID}:{path}"
        display_name = f"{row['name']} ({row['name_en']})"
        description = (
            "[AI Agent - unofficial, not affiliated with the real organization] "
            f"{row['name_en']}"
        )
        pds_results.append(
            {
                "path": path,
                "identity": await _pds_xrpc(
                    "com.atproto.identity.create",
                    {
                        "path": path,
                        "documentJson": json.dumps(
                            {
                                "displayName": display_name,
                                "description": f"{description} - {row['website']}",
                            },
                            separators=(",", ":"),
                            ensure_ascii=False,
                        ),
                    },
                ),
            }
        )
        _insert_repo_record(
            org_did,
            "actorManifest",
            _repo_rkey("actor", path),
            {
                "$type": "actorManifest",
                "displayName": display_name,
                "description": description,
                "performerType": "service",
                "isBot": True,
                "agentType": "autonomous",
                "country": DOMAIN_CODE,
                "path": path,
                "createdAt": _utc_now_iso(),
            },
        )
        pds_results[-1]["post"] = await _pds_xrpc(
            "app.bsky.feed.post",
            {"did": org_did, "text": f"{row['name_en']} registered.\n{org_did}"},
        )
        _insert_repo_record(
            org_did,
            "app.bsky.feed.post",
            _repo_rkey("registered", path),
            {
                "$type": "app.bsky.feed.post",
                "text": f"{row['name_en']} registered.\n{org_did}",
                "createdAt": _utc_now_iso(),
            },
        )
        _upsert_gov_org(row)
        registered.append(org_did)
    pds_ok = sum(
        1
        for result in pds_results
        if int(result.get("identity", {}).get("status") or 0) in range(200, 300)
    )
    return {"ok": True, "registered": len(registered), "dids": registered, "pdsIdentityOk": pds_ok}


async def task_gov_fra_follow_site_deps(limit: int = 15) -> dict[str, Any]:
    limit = max(1, min(int(limit or 15), 50))
    followed = 0
    with sync_cursor() as cur:
        cur.execute(
            f"""
            SELECT path, name, name_en, website, contract, tags, org_tier,
                   site_domain_slug, did_registered, last_ingested_at,
                   last_content_hash, last_kyumei_at, last_shinka_at, created_at
              FROM vertex_gov_org
             WHERE domain_code = %s
               AND owner_did = %s
               AND site_followed != 'true'
               AND site_domain_slug != ''
             ORDER BY path
             LIMIT {limit}
            """,
            (DOMAIN_CODE, PRIMARY_DID),
        )
        rows = cur.fetchall()
    for r in rows:
        path = str(r[0] or "")
        slug = str(r[7] or "")
        await _pds_xrpc("app.bsky.graph.follow", {"did": f"did:web:site.etzhayyim.com:{slug}"})
        row = {
            "path": path,
            "name": str(r[1] or ""),
            "name_en": str(r[2] or ""),
            "website": str(r[3] or ""),
            "contract": str(r[4] or ""),
            "tags": json.loads(str(r[5] or "[]")),
            "org_tier": str(r[6] or ""),
            "site_domain_slug": slug,
            "site_followed": "true",
            "did_registered": str(r[8] or "false"),
            "last_ingested_at": str(r[9] or ""),
            "last_content_hash": str(r[10] or ""),
            "last_kyumei_at": str(r[11] or ""),
            "last_shinka_at": str(r[12] or ""),
            "created_at": str(r[13] or _utc_now_iso()),
        }
        _insert_repo_record(
            f"{PRIMARY_DID}:{path}",
            "com.etzhayyim.apps.states.govOrgSiteDep",
            _repo_rkey("site-dep", path),
            {
                "$type": "com.etzhayyim.apps.states.govOrgSiteDep",
                "path": path,
                "siteNanoid": SITE_NANOID,
                "siteTopicDid": SITE_GOV_TOPIC_DID,
                "siteDid": f"did:web:site.etzhayyim.com:{slug}",
                "updated_at": _utc_now_iso(),
            },
        )
        _upsert_gov_org(row)
        followed += 1
    return {"ok": True, "followed": followed}


async def task_gov_fra_sync_wet_updates(limit: int = 10, postUpdates: bool = True) -> dict[str, Any]:
    limit = max(1, min(int(limit or 10), 50))
    cutoff = (_dt.datetime.now(tz=_dt.UTC) - _dt.timedelta(days=7)).replace(microsecond=0)
    cutoff_iso = cutoff.isoformat().replace("+00:00", "Z")
    with sync_cursor() as cur:
        cur.execute(
            f"""
            SELECT path, name_en, website, site_domain_slug, last_content_hash
              FROM vertex_gov_org
             WHERE domain_code = %s
               AND owner_did = %s
               AND site_domain_slug != ''
               AND (
                 last_ingested_at = ''
                 OR last_ingested_at IS NULL
                 OR last_ingested_at < %s
               )
             ORDER BY last_ingested_at ASC
             LIMIT {limit}
            """,
            (DOMAIN_CODE, PRIMARY_DID, cutoff_iso),
        )
        rows = cur.fetchall()
    checked = 0
    updated = 0
    posted = 0
    now = _utc_now_iso()
    for r in rows:
        path = str(r[0] or "")
        name_en = str(r[1] or "")
        website = str(r[2] or "")
        slug = str(r[3] or "")
        last_hash = str(r[4] or "")
        if not path or not slug:
            continue
        checked += 1
        with sync_cursor() as cur:
            cur.execute(
                """
                SELECT markdown, content_hash
                  FROM vertex_wet_chunk
                 WHERE domain = %s
                 ORDER BY crawled_at DESC
                 LIMIT 1
                """,
                (slug,),
            )
            wet = cur.fetchone()
        if not wet:
            fetch_hash, fetch_text = _direct_fetch_hash(website)
            if fetch_hash:
                fields: dict[str, str] = {"last_ingested_at": now, "last_content_hash": fetch_hash}
                _update_gov_org_fields(path, fields)
                if fetch_hash != last_hash:
                    updated += 1
                    text = f"{name_en} - official site updated\n{fetch_text[:200]}..."
                    org_did = f"{PRIMARY_DID}:{path}"
                    if postUpdates:
                        result = await _pds_xrpc("app.bsky.feed.post", {"did": org_did, "text": text})
                        if int(result.get("status") or 0) in range(200, 300):
                            posted += 1
                    _insert_repo_record(
                        org_did,
                        "app.bsky.feed.post",
                        _repo_rkey("wet-update", path),
                        {"$type": "app.bsky.feed.post", "text": text, "createdAt": now},
                    )
            else:
                _update_gov_org_fields(path, {"last_ingested_at": now})
            continue
        markdown = str(wet[0] or "")
        content_hash = str(wet[1] or "")
        fields = {"last_ingested_at": now}
        if content_hash:
            fields["last_content_hash"] = content_hash
        _update_gov_org_fields(path, fields)
        if content_hash and content_hash != last_hash:
            updated += 1
            summary = re.sub(r"\s+", " ", markdown)[:200]
            text = f"{name_en} - official site updated\n{summary}..."
            org_did = f"{PRIMARY_DID}:{path}"
            if postUpdates:
                result = await _pds_xrpc("app.bsky.feed.post", {"did": org_did, "text": text})
                if int(result.get("status") or 0) in range(200, 300):
                    posted += 1
            _insert_repo_record(
                org_did,
                "app.bsky.feed.post",
                _repo_rkey("wet-update", path),
                {
                    "$type": "app.bsky.feed.post",
                    "text": text,
                    "createdAt": now,
                },
            )
    return {"ok": True, "checked": checked, "updated": updated, "posted": posted}


async def task_gov_fra_shinka(limit: int = 1, postUpdates: bool = True) -> dict[str, Any]:
    limit = max(1, min(int(limit or 1), 5))
    with sync_cursor() as cur:
        cur.execute(
            f"""
            SELECT path, name_en
              FROM vertex_gov_org
             WHERE domain_code = %s
               AND owner_did = %s
               AND did_registered = 'true'
             ORDER BY last_shinka_at ASC
             LIMIT {limit}
            """,
            (DOMAIN_CODE, PRIMARY_DID),
        )
        rows = cur.fetchall()
    posted = 0
    now = _utc_now_iso()
    for r in rows:
        path = str(r[0] or "")
        name_en = str(r[1] or "")
        if not path:
            continue
        org_did = f"{PRIMARY_DID}:{path}"
        text = f"{name_en} - government organization update"
        if postUpdates:
            result = await _pds_xrpc("app.bsky.feed.post", {"did": org_did, "text": text})
            if int(result.get("status") or 0) in range(200, 300):
                posted += 1
        _insert_repo_record(
            org_did,
            "app.bsky.feed.post",
            _repo_rkey("shinka", path),
            {
                "$type": "app.bsky.feed.post",
                "text": text,
                "createdAt": now,
            },
        )
        _update_gov_org_fields(path, {"last_shinka_at": now})
    return {"ok": True, "posted": posted, "touched": len(rows)}


async def task_gov_fra_heartbeat_tick(
    seedLimit: int = 30,
    registerLimit: int = 10,
    followLimit: int = 15,
    ingestLimit: int = 5,
    shinkaLimit: int = 1,
) -> dict[str, Any]:
    seed = await asyncio.to_thread(task_gov_fra_seed_orgs, seedLimit)
    register = await task_gov_fra_register_dids(registerLimit)
    follow = await task_gov_fra_follow_site_deps(followLimit)
    ingest = await task_gov_fra_sync_wet_updates(ingestLimit)
    shinka = await task_gov_fra_shinka(shinkaLimit)
    return {
        "ok": True,
        "seeded": seed.get("seeded", 0),
        "registered": register.get("registered", 0),
        "followed": follow.get("followed", 0),
        "wetUpdated": ingest.get("updated", 0),
        "shinkaPosted": shinka.get("posted", 0),
    }


def register(worker: Any, *, timeout_ms: int) -> None:
    worker.task(
        task_type="xrpc.com.etzhayyim.govFra.seedOrgs",
        single_value=False,
        timeout_ms=timeout_ms,
    )(task_gov_fra_seed_orgs)
    worker.task(
        task_type="xrpc.com.etzhayyim.govFra.registerDIDs",
        single_value=False,
        timeout_ms=timeout_ms,
    )(task_gov_fra_register_dids)
    worker.task(
        task_type="xrpc.com.etzhayyim.govFra.followSiteDeps",
        single_value=False,
        timeout_ms=timeout_ms,
    )(task_gov_fra_follow_site_deps)
    worker.task(
        task_type="xrpc.com.etzhayyim.govFra.resolveOrgPath",
        single_value=False,
        timeout_ms=timeout_ms,
    )(task_gov_fra_resolve_org_path)
    worker.task(
        task_type="xrpc.com.etzhayyim.govFra.listOrgs",
        single_value=False,
        timeout_ms=timeout_ms,
    )(task_gov_fra_list_orgs)
    worker.task(
        task_type="xrpc.com.etzhayyim.govFra.syncWetUpdates",
        single_value=False,
        timeout_ms=timeout_ms,
    )(task_gov_fra_sync_wet_updates)
    worker.task(
        task_type="xrpc.com.etzhayyim.govFra.shinka",
        single_value=False,
        timeout_ms=timeout_ms,
    )(task_gov_fra_shinka)
    worker.task(
        task_type="xrpc.com.etzhayyim.govFra.heartbeatTick",
        single_value=False,
        timeout_ms=timeout_ms,
    )(task_gov_fra_heartbeat_tick)
