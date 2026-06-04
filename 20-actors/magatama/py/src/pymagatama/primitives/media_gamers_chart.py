"""
com.etzhayyim.apps.media_gamers chart analysis primitives.

Two LangServer task types backing chartFetch.bpmn + chartAnalyze.bpmn:

  mediaGamers.chart.fetchAndPersist
      Fetch weekly top-20 charts from SteamSpy (free, no auth) and optionally
      RAWG (API key from env RAWG_API_KEY).  Match titles to vertex_game_title
      via external_ids. Compute rank_delta vs previous week. Persist
      vertex_game_chart_snapshot rows + edge_game_charted_at edges.
      Returns: weekStart, source, snapshotCount.

  mediaGamers.chart.analyze
      Load current-week snapshots from DB. Build LLM context (top titles,
      rising/falling, genre distribution). Call Murakumo for Japanese insight
      text + insight_tags. Persist vertex_game_chart_analysis. Post to social
      feed via insert_social_post_record. Returns: analysisUri, socialText.

ADR-0036: domain writes direct to Hyperdrive (sync_cursor).
ADR-0056: BPMN-as-actor.
ADR-0044: Murakumo LLM via pymagatama.llm (external IO tier).
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import time
import urllib.error as _u_err
import urllib.request as _u_req
import uuid
from typing import Any

from pymagatama import llm as _llm
from pymagatama.db_sync import sync_cursor
from pymagatama.primitives.yoro_social import insert_social_post_record

_ACTOR_DID = os.getenv("MEDIA_GAMERS_ACTOR_DID", "did:web:media-gamers.etzhayyim.com")
_COLLECTION_SNAPSHOT = "com.etzhayyim.apps.media_gamers.chartSnapshot"
_COLLECTION_ANALYSIS = "com.etzhayyim.apps.media_gamers.chartAnalysis"

_STEAMSPY_TOP2W_URL = "https://steamspy.com/api.php?request=top100in2weeks"
_RAWG_GAMES_URL = "https://api.rawg.io/api/games"
_STEAMSPY_DETAILS_URL = "https://steamspy.com/api.php?request=appdetails&appid={appid}"

_HTTP_TIMEOUT = 20.0
_CHART_LIMIT = 20  # how many ranks to store per source per week


# ── helpers ───────────────────────────────────────────────────────────────────

def _now_iso() -> str:
    return (
        _dt.datetime.now(tz=_dt.UTC)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _week_start(ref: _dt.date | None = None) -> _dt.date:
    """Return the Monday of the ISO week containing ref (default: today)."""
    d = ref or _dt.date.today()
    return d - _dt.timedelta(days=d.weekday())


def _rkey(prefix: str) -> str:
    stamp = _dt.datetime.now(tz=_dt.UTC).strftime("%Y%m%d%H%M%S")
    return f"{prefix}-{stamp}-{uuid.uuid4().hex[:6]}"


def _http_get_json(url: str, headers: dict | None = None, timeout: float = _HTTP_TIMEOUT) -> Any:
    req = _u_req.Request(url, headers=headers or {"User-Agent": "etzhayyim-media-gamers/1.0"})
    try:
        with _u_req.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8", errors="replace"))
    except (_u_err.HTTPError, _u_err.URLError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"HTTP GET failed {url}: {exc}") from exc


def _vertex_id_snapshot(source: str, week: _dt.date, rank: int) -> str:
    return f"at://{_ACTOR_DID}/{_COLLECTION_SNAPSHOT}/{source}-{week}-{rank:03d}"


def _vertex_id_analysis(source: str, week: _dt.date) -> str:
    return f"at://{_ACTOR_DID}/{_COLLECTION_ANALYSIS}/{source}-{week}"


def _edge_id_charted(title_did: str, source: str, week: _dt.date) -> str:
    slug = title_did.replace("://", "__").replace("/", "_")
    return f"{slug}:{source}:{week}"


# ── SteamSpy fetch ────────────────────────────────────────────────────────────

def _fetch_steamspy_top2w() -> list[dict]:
    """Return top-100 games by 2-week player count from SteamSpy (public API).

    Response is a dict keyed by appid → {name, developer, publisher, owners,
    players_2weeks, positive, negative, price, ...}.
    We take top _CHART_LIMIT by players_2weeks descending.
    """
    raw = _http_get_json(_STEAMSPY_TOP2W_URL)
    if not isinstance(raw, dict):
        return []

    items: list[dict] = []
    for appid, data in raw.items():
        players = data.get("players_2weeks", 0) or 0
        positive = data.get("positive", 0) or 0
        negative = data.get("negative", 0) or 0
        total_reviews = positive + negative
        positive_pct = (positive / total_reviews * 100.0) if total_reviews > 0 else None
        price_usd = None
        raw_price = data.get("price") or data.get("initialprice")
        if raw_price and str(raw_price).isdigit() and int(raw_price) > 0:
            price_usd = int(raw_price) / 100.0

        items.append({
            "external_id": str(appid),
            "title_hint": (data.get("name") or "").strip()[:255],
            "players_2w": int(players),
            "score_source": positive_pct,
            "price_usd": price_usd,
            "tags": list(data.get("tags", {}).keys())[:10] if data.get("tags") else [],
            "reviews_total": total_reviews,
        })

    items.sort(key=lambda x: x["players_2w"], reverse=True)
    return items[:_CHART_LIMIT]


# ── RAWG fetch ────────────────────────────────────────────────────────────────

def _fetch_rawg_top(api_key: str, week: _dt.date) -> list[dict]:
    """Return top games from RAWG ordered by metacritic score for the past week."""
    since = (week - _dt.timedelta(days=7)).isoformat()
    until = week.isoformat()
    params = f"key={api_key}&ordering=-metacritic&page_size={_CHART_LIMIT}&dates={since},{until}"
    url = f"{_RAWG_GAMES_URL}?{params}"
    try:
        raw = _http_get_json(url, timeout=25.0)
    except RuntimeError:
        return []

    items = []
    for game in (raw.get("results") or []):
        steam_id = None
        for store in (game.get("stores") or []):
            if (store.get("store", {}) or {}).get("slug") == "steam":
                url_part = store.get("url", "")
                parts = [p for p in url_part.rstrip("/").split("/") if p.isdigit()]
                if parts:
                    steam_id = parts[-1]
        items.append({
            "external_id": str(game.get("id", "")),
            "steam_id": steam_id,
            "title_hint": (game.get("name") or "").strip()[:255],
            "players_2w": None,
            "score_source": float(game.get("metacritic") or 0) if game.get("metacritic") else None,
            "price_usd": None,
            "tags": [g["name"] for g in (game.get("genres") or [])][:10],
            "reviews_total": game.get("reviews_count") or 0,
        })
    return items


# ── title matching ────────────────────────────────────────────────────────────

def _match_title_did(external_id: str, steam_id: str | None, title_hint: str) -> str | None:
    """Try to match a chart entry to an existing vertex_game_title row.

    Strategy:
      1. external_ids column contains comma-separated 'key:value' pairs.
         Look for steam:{external_id} or steam:{steam_id}.
      2. Fuzzy: case-insensitive exact match on title_en.
    Returns vertex_id or None.
    """
    candidates = {external_id}
    if steam_id:
        candidates.add(steam_id)

    with sync_cursor() as cur:
        for cid in candidates:
            cur.execute(
                "SELECT vertex_id FROM vertex_game_title "
                "WHERE external_ids LIKE %s OR external_ids LIKE %s LIMIT 1",
                (f"%steam:{cid}%", f"%steamspy:{cid}%"),
            )
            row = cur.fetchone()
            if row:
                return row[0]

        # title-based fallback (exact, case-insensitive)
        if title_hint:
            cur.execute(
                "SELECT vertex_id FROM vertex_game_title "
                "WHERE LOWER(title_en) = %s OR LOWER(title_ja) = %s LIMIT 1",
                (title_hint.lower(), title_hint.lower()),
            )
            row = cur.fetchone()
            if row:
                return row[0]
    return None


# ── previous week rank lookup ─────────────────────────────────────────────────

def _prev_week_ranks(source: str, prev_week: _dt.date) -> dict[str, int]:
    """Return {external_id → rank} for the given source + prev_week."""
    with sync_cursor() as cur:
        cur.execute(
            "SELECT external_id, rank FROM vertex_game_chart_snapshot "
            "WHERE source = %s AND week_start = %s",
            (source, prev_week.isoformat()),
        )
        return {row[0]: row[1] for row in cur.fetchall()}


# ── Task 1: mediaGamers.chart.fetchAndPersist ─────────────────────────────────

def task_media_gamers_chart_fetch_and_persist() -> dict[str, Any]:
    """Fetch weekly charts, match titles, persist snapshots + edges.

    Returns:
        weekStart     — ISO date string (Monday of this week)
        source        — "steamspy_top2w" (primary source used)
        snapshotCount — total rows upserted into vertex_game_chart_snapshot
    """
    week = _week_start()
    prev_week = week - _dt.timedelta(days=7)
    created_at = _now_iso()
    source = "steamspy_top2w"

    # Fetch
    try:
        entries = _fetch_steamspy_top2w()
    except RuntimeError as exc:
        return {"ok": False, "error": str(exc), "weekStart": str(week), "source": source, "snapshotCount": 0}

    if not entries:
        return {"ok": True, "weekStart": str(week), "source": source, "snapshotCount": 0}

    prev_ranks = _prev_week_ranks(source, prev_week)
    snapshot_count = 0

    with sync_cursor() as cur:
        for rank, entry in enumerate(entries, start=1):
            ext_id = entry["external_id"]
            title_did = _match_title_did(ext_id, None, entry["title_hint"])

            rank_prev = prev_ranks.get(ext_id)
            rank_delta = (rank_prev - rank) if rank_prev is not None else None

            vertex_id = _vertex_id_snapshot(source, week, rank)
            metadata = {
                "tags": entry.get("tags", []),
                "reviews_total": entry.get("reviews_total", 0),
            }
            metadata_json = json.dumps(metadata, ensure_ascii=False, separators=(",", ":"))

            cur.execute(
                """
                INSERT INTO vertex_game_chart_snapshot (
                  vertex_id, owner_did, title_did, source, week_start, rank,
                  rank_prev, rank_delta, external_id, title_hint, score_source,
                  players_2w, price_usd, metadata_json, fetched_at,
                  actor_did, org_did, sensitivity_ord, created_at
                ) VALUES (
                  %s, %s, %s, %s, %s, %s,
                  %s, %s, %s, %s, %s,
                  %s, %s, %s, %s,
                  %s, %s, %s, %s
                )
                """,
                (
                    vertex_id, _ACTOR_DID, title_did, source, week.isoformat(), rank,
                    rank_prev, rank_delta, ext_id, entry["title_hint"], entry.get("score_source"),
                    entry.get("players_2w"), entry.get("price_usd"), metadata_json, created_at,
                    _ACTOR_DID, _ACTOR_DID, 1, created_at,
                ),
            )
            snapshot_count += 1

            # Edge: title → snapshot (only when matched)
            if title_did:
                edge_id = _edge_id_charted(title_did, source, week)
                cur.execute(
                    """
                    INSERT INTO edge_game_charted_at (
                      edge_id, owner_did, src_vid, dst_vid, rank, source, week_start,
                      sensitivity_ord, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        edge_id, _ACTOR_DID, title_did, vertex_id,
                        rank, source, week.isoformat(), 1, created_at,
                    ),
                )

    # Also try RAWG if API key is available (secondary source, non-blocking)
    rawg_key = os.getenv("RAWG_API_KEY", "")
    if rawg_key:
        _persist_rawg_source(rawg_key, week, prev_week, created_at)

    return {
        "ok": True,
        "weekStart": str(week),
        "source": source,
        "snapshotCount": snapshot_count,
    }


def _persist_rawg_source(api_key: str, week: _dt.date, prev_week: _dt.date, created_at: str) -> None:
    source = "rawg_top"
    try:
        entries = _fetch_rawg_top(api_key, week)
    except Exception:  # noqa: BLE001
        return
    if not entries:
        return
    prev_ranks = _prev_week_ranks(source, prev_week)
    with sync_cursor() as cur:
        for rank, entry in enumerate(entries, start=1):
            ext_id = entry["external_id"]
            steam_id = entry.get("steam_id")
            title_did = _match_title_did(ext_id, steam_id, entry["title_hint"])
            rank_prev = prev_ranks.get(ext_id)
            rank_delta = (rank_prev - rank) if rank_prev is not None else None
            vertex_id = _vertex_id_snapshot(source, week, rank)
            metadata = {"tags": entry.get("tags", []), "reviews_total": entry.get("reviews_total", 0)}
            cur.execute(
                """
                INSERT INTO vertex_game_chart_snapshot (
                  vertex_id, owner_did, title_did, source, week_start, rank,
                  rank_prev, rank_delta, external_id, title_hint, score_source,
                  players_2w, price_usd, metadata_json, fetched_at,
                  actor_did, org_did, sensitivity_ord, created_at
                ) VALUES (
                  %s, %s, %s, %s, %s, %s,
                  %s, %s, %s, %s, %s,
                  %s, %s, %s, %s,
                  %s, %s, %s, %s
                )
                """,
                (
                    vertex_id, _ACTOR_DID, title_did, source, week.isoformat(), rank,
                    rank_prev, rank_delta, ext_id, entry["title_hint"], entry.get("score_source"),
                    None, None,
                    json.dumps(metadata, ensure_ascii=False, separators=(",", ":")),
                    created_at, _ACTOR_DID, _ACTOR_DID, 1, created_at,
                ),
            )
            if title_did:
                cur.execute(
                    """
                    INSERT INTO edge_game_charted_at (
                      edge_id, owner_did, src_vid, dst_vid, rank, source, week_start,
                      sensitivity_ord, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        _edge_id_charted(title_did, source, week),
                        _ACTOR_DID, title_did, vertex_id,
                        rank, source, week.isoformat(), 1, created_at,
                    ),
                )


# ── Task 2: mediaGamers.chart.analyze ────────────────────────────────────────

_ANALYSIS_SYSTEM = (
    "You are a game industry analyst writing for media-gamers.etzhayyim.com.\n"
    "Output ONLY valid JSON, no prose, no code fences.\n"
    "Schema: {\n"
    '  "analysis_ja": string (≤280 chars, Japanese, for AT Protocol social post),\n'
    '  "analysis_en": string (≤400 chars, English summary),\n'
    '  "top_genre": string (most common genre in top 10),\n'
    '  "insight_tags": [string] (2-5 short English tags like "indie-surge", "sequel-effect",\n'
    '    "seasonal", "early-access-peak", "jrpg-week", "battle-royale-resurgence")\n'
    "}"
)


def task_media_gamers_chart_analyze(
    weekStart: str = "",
    source: str = "steamspy_top2w",
) -> dict[str, Any]:
    """LLM-analyze current-week chart data and persist vertex_game_chart_analysis.

    Reads vertex_game_chart_snapshot for weekStart × source, joins with
    vertex_game_title for genre info via edge_game_has_genre, builds LLM
    context, generates analysis_ja + insight_tags, persists, and posts to
    the media-gamers AT social feed.

    Returns:
        analysisUri — vertex_id of vertex_game_chart_analysis
        socialText  — Japanese post text used for social feed
    """
    # Resolve weekStart
    if weekStart:
        try:
            week = _dt.date.fromisoformat(weekStart)
        except ValueError:
            week = _week_start()
    else:
        week = _week_start()

    created_at = _now_iso()
    vertex_id = _vertex_id_analysis(source, week)

    # ── Load snapshot rows for this week + source ──────────────────────────
    with sync_cursor() as cur:
        cur.execute(
            """
            SELECT s.rank, s.rank_delta, s.rank_prev, s.title_hint,
                   s.players_2w, s.score_source, s.external_id,
                   s.title_did, s.metadata_json
            FROM vertex_game_chart_snapshot s
            WHERE s.source = %s AND s.week_start = %s
            ORDER BY s.rank ASC
            LIMIT {int(_CHART_LIMIT)}
            """.replace("{int(_CHART_LIMIT)}", str(_CHART_LIMIT)),
            (source, week.isoformat()),
        )
        rows = cur.fetchall()

    if not rows:
        return {
            "ok": False,
            "error": f"no snapshots for {source} week {week}",
            "analysisUri": vertex_id,
            "socialText": "",
        }

    # ── Genre lookup for matched titles ───────────────────────────────────
    matched_dids = [r[7] for r in rows if r[7]]
    genre_map: dict[str, str] = {}
    if matched_dids:
        placeholders = ",".join(["%s"] * len(matched_dids))
        with sync_cursor() as cur:
            cur.execute(
                f"""
                SELECT g.src_vid, genre.name
                FROM edge_game_has_genre g
                JOIN vertex_game_genre genre ON genre.vertex_id = g.dst_vid
                WHERE g.src_vid IN ({placeholders}) AND g.is_primary = true
                LIMIT {int(len(matched_dids) * 2)}
                """,
                matched_dids,
            )
            for r in cur.fetchall():
                genre_map[r[0]] = r[1]

    # ── Build context for LLM ─────────────────────────────────────────────
    rising: list[dict] = []
    falling: list[dict] = []
    new_entries: list[dict] = []
    genre_counts: dict[str, int] = {}

    top_lines: list[str] = []
    for r in rows:
        rank, rank_delta, rank_prev, title_hint, players_2w, score, ext_id, title_did, meta_json = r
        genre = genre_map.get(title_did or "", "Unknown")
        genre_counts[genre] = genre_counts.get(genre, 0) + 1

        delta_str = ""
        if rank_delta is not None:
            if rank_delta > 0:
                delta_str = f"↑{rank_delta}"
                rising.append({"title_hint": title_hint, "rank": rank, "rank_delta": rank_delta, "title_did": title_did})
            elif rank_delta < 0:
                delta_str = f"↓{abs(rank_delta)}"
                falling.append({"title_hint": title_hint, "rank": rank, "rank_delta": rank_delta, "title_did": title_did})
        if rank_prev is None:
            new_entries.append({"title_hint": title_hint, "rank": rank, "title_did": title_did})

        players_str = f"{players_2w:,}" if players_2w else "N/A"
        top_lines.append(f"#{rank} {title_hint} [{genre}] players={players_str} {delta_str}")

    top_genre = max(genre_counts, key=lambda k: genre_counts[k]) if genre_counts else "Unknown"
    context = (
        f"Week: {week} | Source: {source}\n"
        f"Top {len(rows)} games:\n"
        + "\n".join(top_lines[:15])
        + f"\n\nRising: {[r['title_hint'] for r in rising[:3]]}"
        + f"\nFalling: {[f['title_hint'] for f in falling[:3]]}"
        + f"\nNew entries: {[n['title_hint'] for n in new_entries[:3]]}"
        + f"\nTop genre: {top_genre}"
    )

    # ── LLM call ──────────────────────────────────────────────────────────
    llm_result: dict = {}
    model_id = "unknown"
    try:
        resp = _llm.call_tier_json(
            "fast",
            system=_ANALYSIS_SYSTEM,
            user=f"Analyze this weekly game chart:\n\n{context}",
            max_tokens=600,
            temperature=0.5,
        )
        if resp.get("ok") and isinstance(resp.get("data"), dict):
            llm_result = resp["data"]
            model_id = resp.get("model_id", "unknown")
    except Exception:  # noqa: BLE001
        pass

    analysis_ja = (llm_result.get("analysis_ja") or
                   f"今週のゲームチャート({source}): {top_lines[0] if top_lines else ''}ほか{len(rows)}作品をランクイン。")[:280]
    analysis_en = (llm_result.get("analysis_en") or
                   f"Weekly chart ({source}, {week}): {top_genre} leads with {len(rows)} titles tracked.")[:400]
    insight_tags = llm_result.get("insight_tags") or []
    if not isinstance(insight_tags, list):
        insight_tags = []

    # ── Persist vertex_game_chart_analysis ────────────────────────────────
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_game_chart_analysis (
              vertex_id, owner_did, week_start, source,
              analysis_ja, analysis_en, top_genre,
              rising_titles_json, falling_titles_json, new_entries_json,
              insight_tags_json, model_id,
              actor_did, org_did, sensitivity_ord, created_at
            ) VALUES (
              %s, %s, %s, %s,
              %s, %s, %s,
              %s, %s, %s,
              %s, %s,
              %s, %s, %s, %s
            )
            """,
            (
                vertex_id, _ACTOR_DID, week.isoformat(), source,
                analysis_ja, analysis_en, top_genre,
                json.dumps(rising[:5], ensure_ascii=False),
                json.dumps(falling[:5], ensure_ascii=False),
                json.dumps(new_entries[:5], ensure_ascii=False),
                json.dumps(insight_tags[:5], ensure_ascii=False),
                model_id,
                _ACTOR_DID, _ACTOR_DID, 1, created_at,
            ),
        )

    # ── Social post ───────────────────────────────────────────────────────
    social_rkey = _rkey("chart")
    try:
        insert_social_post_record(
            repo=_ACTOR_DID,
            rkey=social_rkey,
            text=analysis_ja,
            langs=["ja"],
        )
        # Update social_post_rkey in analysis row
        with sync_cursor() as cur:
            cur.execute(
                "UPDATE vertex_game_chart_analysis SET social_post_rkey = %s WHERE vertex_id = %s",
                (social_rkey, vertex_id),
            )
    except Exception:  # noqa: BLE001
        pass

    return {
        "ok": True,
        "analysisUri": vertex_id,
        "socialText": analysis_ja,
        "weekStart": str(week),
        "source": source,
        "topGenre": top_genre,
        "insightTags": insight_tags,
    }


# ── LangServer registration ──────────────────────────────────────────────────────

def register(worker: Any, *, timeout_ms: int) -> None:
    """Wire media-gamers chart primitives onto the shared LangServer worker."""

    def t(name: str, fn: Any, *, timeout: int | None = None) -> None:
        worker.task(
            task_type=name,
            single_value=False,
            timeout_ms=timeout if timeout is not None else timeout_ms,
        )(fn)

    # fetchAndPersist may be slow on SteamSpy (rate limits) — give 5min
    t("mediaGamers.chart.fetchAndPersist", task_media_gamers_chart_fetch_and_persist, timeout=300_000)
    # analyze includes LLM call — give 3min
    t("mediaGamers.chart.analyze", task_media_gamers_chart_analyze, timeout=180_000)


__all__ = [
    "register",
    "task_media_gamers_chart_fetch_and_persist",
    "task_media_gamers_chart_analyze",
]
