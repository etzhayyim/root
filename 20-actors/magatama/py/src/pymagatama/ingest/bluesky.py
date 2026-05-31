"""Bluesky public AppView ingest for Zeebe.

Moves the former ``magatama-bsky1ngs`` Cloudflare Worker business logic into
the shared Python Zeebe worker. The edge Worker now only proxies manual XRPC
requests to the BPMN dispatcher; timer refreshes run from BPMN.
"""

from __future__ import annotations

import json
import logging
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

from pymagatama.db_sync import sync_cursor

LOG = logging.getLogger(__name__)

ACTOR_DID = "did:web:bluesky.etzhayyim.com"
DEFAULT_APPVIEW = "https://public.api.bsky.app"
DEFAULT_NANOID = "bsky1ngs"
BLOCKING_LABELS = {
    "!no-unauthenticated",
    "!no-search",
    "!hide",
    "!takedown",
    "no-unauthenticated",
}
FORBIDDEN_COLLECTIONS = {
    "chat.bsky.convo.message",
    "chat.bsky.actor.declaration",
    "app.bsky.graph.block",
    "app.bsky.graph.listitem",
    "app.bsky.graph.listblock",
}


@dataclass(frozen=True)
class OptOutVerdict:
    allow: bool
    reason: str = ""
    hit_label: str = ""


class ForbiddenCollectionError(ValueError):
    pass


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _http_json(url: str, timeout: int = 20) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _appview_url(base_url: str, path: str, params: dict[str, str]) -> str:
    base = (base_url or DEFAULT_APPVIEW).rstrip("/")
    query = urllib.parse.urlencode(params)
    return f"{base}{path}?{query}"


def get_profile(actor: str, appview: str = DEFAULT_APPVIEW) -> dict[str, Any]:
    return _http_json(_appview_url(appview, "/xrpc/app.bsky.actor.getProfile", {"actor": actor}))


def get_author_feed(actor: str, appview: str = DEFAULT_APPVIEW, limit: int = 25) -> dict[str, Any]:
    return _http_json(
        _appview_url(
            appview,
            "/xrpc/app.bsky.feed.getAuthorFeed",
            {"actor": actor, "limit": str(limit), "filter": "posts_no_replies"},
        )
    )


def evaluate_profile_opt_out(profile: dict[str, Any]) -> OptOutVerdict:
    for label in profile.get("labels") or []:
        if label.get("neg"):
            continue
        val = str(label.get("val") or "")
        if val in BLOCKING_LABELS:
            if "no-unauthenticated" in val:
                reason = "no-unauthenticated"
            elif "no-search" in val:
                reason = "no-search"
            elif val == "!takedown":
                reason = "takedown"
            else:
                reason = "labeler-verdict"
            return OptOutVerdict(False, reason, val)
    return OptOutVerdict(True)


def evaluate_post_opt_out(labels: Any) -> OptOutVerdict:
    for label in labels or []:
        val = str(label.get("val") or "")
        if val in BLOCKING_LABELS:
            return OptOutVerdict(False, "labeler-verdict", val)
    return OptOutVerdict(True)


def _parse_rkey(uri: str) -> str:
    return (uri or "").split("/")[-1]


def _extract_cid_from_uri(uri: str | None) -> str | None:
    if not uri:
        return None
    return uri.rstrip("/").split("/")[-1] or None


def map_profile(profile: dict[str, Any], opt_out_signal: str, indexed_at: str) -> dict[str, Any]:
    labels = [str(l.get("val")) for l in (profile.get("labels") or []) if l.get("val")]
    return {
        "source_did": str(profile.get("did") or ""),
        "handle": str(profile.get("handle") or ""),
        "display_name": profile.get("displayName"),
        "description": profile.get("description"),
        "avatar_cid": _extract_cid_from_uri(profile.get("avatar")),
        "banner_cid": _extract_cid_from_uri(profile.get("banner")),
        "labels": ",".join(labels) if labels else None,
        "opt_out_signal": opt_out_signal,
        "indexed_at": indexed_at,
    }


def map_post(post: dict[str, Any], indexed_at: str) -> dict[str, Any]:
    record = post.get("record") or {}
    collection = str(record.get("$type") or "")
    if collection in FORBIDDEN_COLLECTIONS or collection != "app.bsky.feed.post":
        raise ForbiddenCollectionError(f"Forbidden collection: {collection}")

    embed = post.get("embed") or {}
    etype = str(embed.get("$type") or "")
    embed_kind = "none"
    media_cids: list[str] = []
    alt_text = None
    external_uri = None

    if "images" in etype:
        embed_kind = "images"
        alts: list[str] = []
        for img in embed.get("images") or []:
            cid = _extract_cid_from_uri(img.get("fullsize"))
            if cid:
                media_cids.append(cid)
            if img.get("alt"):
                alts.append(str(img.get("alt")))
        alt_text = "\n\n".join(alts) if alts else None
    elif "video" in etype:
        embed_kind = "video"
        video = embed.get("video") or {}
        alt_text = video.get("alt")
        cid = _extract_cid_from_uri(video.get("thumbnail"))
        if cid:
            media_cids.append(cid)
    elif "external" in etype:
        embed_kind = "external"
        external_uri = (embed.get("external") or {}).get("uri")
    elif "recordWithMedia" in etype:
        embed_kind = "recordWithMedia"
    elif "record" in etype:
        embed_kind = "record"

    labels = [str(l.get("val")) for l in (post.get("labels") or []) if l.get("val")]
    reply = record.get("reply") or {}
    author = post.get("author") or {}
    langs = record.get("langs") or []
    return {
        "source_did": str(author.get("did") or ""),
        "source_rkey": _parse_rkey(str(post.get("uri") or "")),
        "source_uri": str(post.get("uri") or ""),
        "source_cid": str(post.get("cid") or ""),
        "handle": str(author.get("handle") or ""),
        "text": str(record.get("text") or ""),
        "lang": str(langs[0]) if langs else None,
        "created_at": str(record.get("createdAt") or indexed_at),
        "indexed_at": indexed_at,
        "reply_root_uri": (reply.get("root") or {}).get("uri"),
        "reply_parent_uri": (reply.get("parent") or {}).get("uri"),
        "embed_kind": embed_kind,
        "embed_media_cids": ",".join(media_cids) if media_cids else None,
        "embed_alt_text": alt_text,
        "embed_external_uri": external_uri,
        "labels": ",".join(labels) if labels else None,
    }


def _execute(sql: str, params: tuple[Any, ...] = ()) -> int:
    with sync_cursor() as cur:
        cur.execute(sql, params)
        return int(cur.rowcount or 0)


def write_profile(rec: dict[str, Any], nanoid: str, indexed_at: str) -> int:
    rkey = rec["source_did"].replace(":", "-")
    vertex_id = f"at://{ACTOR_DID}/app.etzhayyim.apps.bluesky.profile/{rkey}"
    return _execute(
        """
        INSERT INTO vertex_bluesky_profile
          (vertex_id, rkey, repo, owner_did, source_did, handle, display_name, description,
           avatar_cid, banner_cid, labels, opt_out_signal, indexed_at,
           created_date, sensitivity_ord, actor_id)
        SELECT %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 200, %s
        WHERE NOT EXISTS (SELECT 1 FROM vertex_bluesky_profile WHERE vertex_id = %s)
        """,
        (
            vertex_id,
            rkey,
            ACTOR_DID,
            ACTOR_DID,
            rec["source_did"],
            rec["handle"],
            rec["display_name"],
            rec["description"],
            rec["avatar_cid"],
            rec["banner_cid"],
            rec["labels"],
            rec["opt_out_signal"],
            indexed_at,
            indexed_at[:10],
            f"t1:bluesky:{nanoid}",
            vertex_id,
        ),
    )


def write_post(rec: dict[str, Any], nanoid: str, indexed_at: str) -> int:
    rkey = f"{rec['source_did'].replace(':', '-')}-{rec['source_rkey']}"
    vertex_id = f"at://{ACTOR_DID}/app.etzhayyim.apps.bluesky.post/{rkey}"
    return _execute(
        """
        INSERT INTO vertex_bluesky_post
          (vertex_id, rkey, repo, owner_did, source_did, source_rkey, source_uri, source_cid,
           handle, text, lang, created_at, indexed_at,
           reply_root_uri, reply_parent_uri, embed_kind, embed_media_cids, embed_alt_text,
           embed_external_uri, labels, created_date, sensitivity_ord, actor_id)
        SELECT %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 200, %s
        WHERE NOT EXISTS (SELECT 1 FROM vertex_bluesky_post WHERE vertex_id = %s)
        """,
        (
            vertex_id,
            rkey,
            ACTOR_DID,
            ACTOR_DID,
            rec["source_did"],
            rec["source_rkey"],
            rec["source_uri"],
            rec["source_cid"],
            rec["handle"],
            rec["text"],
            rec["lang"],
            rec["created_at"],
            indexed_at,
            rec["reply_root_uri"],
            rec["reply_parent_uri"],
            rec["embed_kind"],
            rec["embed_media_cids"],
            rec["embed_alt_text"],
            rec["embed_external_uri"],
            rec["labels"],
            indexed_at[:10],
            f"t1:bluesky:{nanoid}",
            vertex_id,
        ),
    )


def write_opt_out(did: str, handle: str | None, reason: str, hit_label: str, nanoid: str, indexed_at: str) -> int:
    rkey = did.replace(":", "-")
    vertex_id = f"at://{ACTOR_DID}/app.etzhayyim.apps.bluesky.optOut/{rkey}"
    note = f"hit label: {hit_label}" if hit_label else None
    return _execute(
        """
        INSERT INTO vertex_bluesky_opt_out
          (vertex_id, rkey, repo, owner_did, source_did, handle, reason, note,
           detected_at, created_date, sensitivity_ord, actor_id)
        SELECT %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 200, %s
        WHERE NOT EXISTS (SELECT 1 FROM vertex_bluesky_opt_out WHERE vertex_id = %s)
        """,
        (
            vertex_id,
            rkey,
            ACTOR_DID,
            ACTOR_DID,
            did,
            handle,
            reason,
            note,
            indexed_at,
            indexed_at[:10],
            f"t1:bluesky:{nanoid}",
            vertex_id,
        ),
    )


def cascade_tombstones(source_did: str, fresh_rkeys: set[str], nanoid: str, indexed_at: str) -> dict[str, Any]:
    if not fresh_rkeys:
        return {"purged": 0, "existingCount": 0, "toPurgeList": []}
    with sync_cursor() as cur:
        cur.execute(
            """
            SELECT source_rkey, created_at
            FROM vertex_bluesky_post
            WHERE source_did = %s
            ORDER BY created_at DESC
            LIMIT 25
            """,
            (source_did,),
        )
        existing = cur.fetchall() or []

    to_purge = [str(row[0]) for row in existing if str(row[0]) not in fresh_rkeys]
    for rkey in to_purge:
        vertex_id = f"at://{ACTOR_DID}/app.etzhayyim.apps.bluesky.post/{source_did.replace(':', '-')}-{rkey}"
        _execute("DELETE FROM vertex_bluesky_post WHERE vertex_id = %s", (vertex_id,))
        tomb_rkey = f"{source_did.replace(':', '-')}-{rkey}-{int(time.time() * 1000)}"
        tomb_vid = f"at://{ACTOR_DID}/app.etzhayyim.apps.bluesky.tombstone/{tomb_rkey}"
        _execute(
            """
            INSERT INTO vertex_bluesky_tombstone
              (vertex_id, rkey, repo, owner_did, source_did, source_rkey, source_collection,
               event_kind, detected_at, cascade_completed_at,
               created_date, sensitivity_ord, actor_id)
            SELECT %s, %s, %s, %s, %s, %s, 'app.bsky.feed.post', 'delete', %s, %s, %s, 200, %s
            WHERE NOT EXISTS (SELECT 1 FROM vertex_bluesky_tombstone WHERE vertex_id = %s)
            """,
            (
                tomb_vid,
                tomb_rkey,
                ACTOR_DID,
                ACTOR_DID,
                source_did,
                rkey,
                indexed_at,
                indexed_at,
                indexed_at[:10],
                f"t1:bluesky:{nanoid}",
                tomb_vid,
            ),
        )
    return {"purged": len(to_purge), "existingCount": len(existing), "toPurgeList": to_purge}


def ingest_actor(actor: str, appview: str = DEFAULT_APPVIEW, nanoid: str = DEFAULT_NANOID) -> dict[str, Any]:
    if not actor:
        return {"ok": False, "error": "actor required"}
    indexed_at = now_iso()
    try:
        profile = get_profile(actor, appview)
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "actor": actor, "error": f"getProfile failed: {e}"}

    verdict = evaluate_profile_opt_out(profile)
    if not verdict.allow:
        write_opt_out(
            str(profile.get("did") or actor),
            profile.get("handle"),
            verdict.reason or "labeler-verdict",
            verdict.hit_label,
            nanoid,
            indexed_at,
        )
        return {
            "ok": True,
            "actor": profile.get("did"),
            "optOut": True,
            "reason": verdict.reason,
            "label": verdict.hit_label,
        }

    write_profile(map_profile(profile, "none", indexed_at), nanoid, indexed_at)

    try:
        feed = get_author_feed(actor, appview, 25)
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "actor": profile.get("did"), "error": f"getAuthorFeed failed: {e}"}

    ingested = 0
    skipped_opt_out = 0
    skipped_forbidden = 0
    fresh_rkeys: set[str] = set()

    for item in feed.get("feed") or []:
        post = item.get("post") or {}
        post_author = post.get("author") or {}
        p_verdict = evaluate_post_opt_out(post.get("labels"))
        if not p_verdict.allow:
            skipped_opt_out += 1
            continue
        try:
            rec = map_post(post, indexed_at)
            ingested += write_post(rec, nanoid, indexed_at)
            if post_author.get("did") == profile.get("did"):
                fresh_rkeys.add(rec["source_rkey"])
        except ForbiddenCollectionError:
            skipped_forbidden += 1

    tombstone = cascade_tombstones(str(profile.get("did") or actor), fresh_rkeys, nanoid, indexed_at)
    return {
        "ok": True,
        "actor": profile.get("did"),
        "handle": profile.get("handle"),
        "ingested": ingested,
        "tombstoned": tombstone["purged"],
        "skippedOptOut": skipped_opt_out,
        "skippedForbidden": skipped_forbidden,
    }


def stale_actor_dids(batch_size: int) -> list[str]:
    with sync_cursor() as cur:
        cur.execute(
            """
            SELECT source_did, MAX(indexed_at) AS last_indexed
            FROM vertex_bluesky_post
            WHERE source_did NOT IN (SELECT source_did FROM vertex_bluesky_opt_out)
            GROUP BY source_did
            ORDER BY last_indexed ASC
            LIMIT %s
            """,
            (int(batch_size),),
        )
        return [str(row[0]) for row in (cur.fetchall() or []) if row[0]]


def refresh_stalest(
    batch_size: int = 10,
    appview: str = DEFAULT_APPVIEW,
    nanoid: str = DEFAULT_NANOID,
) -> dict[str, Any]:
    actors = stale_actor_dids(max(1, int(batch_size or 10)))
    results: list[dict[str, Any]] = []
    errors = 0
    ingested = 0
    tombstoned = 0
    for actor in actors:
        result = ingest_actor(actor, appview=appview, nanoid=nanoid)
        results.append(result)
        if not result.get("ok"):
            errors += 1
        ingested += int(result.get("ingested") or 0)
        tombstoned += int(result.get("tombstoned") or 0)
    return {
        "ok": errors == 0,
        "actorsRead": len(actors),
        "ingested": ingested,
        "tombstoned": tombstoned,
        "errorCount": errors,
        "results": results[:20],
    }
