"""IVF+PQ codebook training and chunk encoding tasks for site.etzhayyim.com.

Weekly batch pipeline (Zeebe R/P7D timer):
  site.ivfPq.updateCentroids  — re-cluster wet_chunk embeddings (K-means via faiss)
  site.ivfPq.trainCodebook    — train PQ codebook on centroid residuals
  site.ivfPq.encodeChunks     — encode all wet_chunks into pq_code bytea rows

ADR-0044: Python External UDF with io_threads=100 for the search path.
Batch training here uses Zeebe Isolated tasks (single-value=False, timeout_ms=3600000).
"""

from __future__ import annotations

import base64
import json
import logging
import os
import threading
import time
from datetime import datetime, timezone
from typing import Any

from pymagatama.kotoba_datomic import get_kotoba_client

LOG = logging.getLogger("site_ivf_pq")

_OWNER_DID = "did:web:site.etzhayyim.com"
_DEFAULT_N_CENTROIDS = 256
_DEFAULT_M_SUBSPACES = 96
_DEFAULT_K_CENTROIDS = 256
_DEFAULT_DIM = 768
_DEFAULT_COLLECTION = "site.wet"
_ENCODE_BATCH = 500
_TRAIN_SAMPLE_MAX = 200_000

# ── Process-level codebook cache (shared across UDF io_thread pool) ───────────
_codebook_cache: dict[str, Any] = {}
_codebook_lock = threading.Lock()


def _get_active_codebook(collection_id: str) -> dict[str, Any] | None:
    # Return cached active codebook or load from kotoba Datom log.
    with _codebook_lock:
        if collection_id in _codebook_cache:
            return _codebook_cache[collection_id]
    row = get_kotoba_client().select_first_where(
        "vertex_pq_codebook",
        "collection_id",
        collection_id,
        columns=[
            "version_tag",
            "m_subspaces",
            "k_centroids",
            "dim",
            "subspace_dim",
            "codebook_json",
        ],
        where_conditions={"status": "active"},
        order_by=[{"column": "trained_at", "direction": "DESC"}],
    )
    # R0: select_first_where does not support order_by and where_conditions. Using q() instead.
    query_edn = """
    [:find ?version_tag ?m_subspaces ?k_centroids ?dim ?subspace_dim ?codebook_json
     :where
     [?e :vertex_pq_codebook/collection_id %s]
     [?e :vertex_pq_codebook/status "active"]
     [?e :vertex_pq_codebook/version_tag ?version_tag]
     [?e :vertex_pq_codebook/m_subspaces ?m_subspaces]
     [?e :vertex_pq_codebook/k_centroids ?k_centroids]
     [?e :vertex_pq_codebook/dim ?dim]
     [?e :vertex_pq_codebook/subspace_dim ?subspace_dim]
     [?e :vertex_pq_codebook/codebook_json ?codebook_json]
     [?e :vertex_pq_codebook/trained_at ?trained_at]
     :order-by desc ?trained_at
     :limit 1]
    """
    rows = get_kotoba_client().q(query_edn, args=[collection_id])
    if not rows:
        return None
    row = {
        "version_tag": rows[0][0],
        "m_subspaces": rows[0][1],
        "k_centroids": rows[0][2],
        "dim": rows[0][3],
        "subspace_dim": rows[0][4],
        "codebook_json": rows[0][5],
    }

    if not row:
        return None
    codebook = {
        "version_tag": row["version_tag"],
        "m": int(row["m_subspaces"]),
        "k": int(row["k_centroids"]),
        "dim": int(row["dim"]),
        "subspace_dim": int(row["subspace_dim"]),
        "centroids": json.loads(row["codebook_json"]),  # float[m][k][subspace_dim]
    }
    with _codebook_lock:
        _codebook_cache[collection_id] = codebook
    return codebook


def _invalidate_codebook_cache(collection_id: str) -> None:
    with _codebook_lock:
        _codebook_cache.pop(collection_id, None)


# ── Zeebe task: embed wet_chunk markdown rows ─────────────────────────────────

def task_site_ivf_pq_embed_markdown(
    domain: str = "",
    batch_size: int = 200,
) -> dict[str, Any]:
    """Embed vertex_wet_chunk.markdown rows that have embedding IS NULL.

    Uses embed_texts_768() (sentence-transformers BAAI/bge-m3, 768-dim).
    Iterates through all unembedded rows in batch_size increments until done.
    Prerequisite for site.ivfPq.updateCentroids.
    """
    import math

    from pymagatama.primitives.vector_embedding import embed_texts_768

    if not domain:
        domain = _DEFAULT_COLLECTION

    total_embedded = 0

    while True:
        with sync_cursor() as cur:
            cur.execute(
                f"""
                SELECT vertex_id, markdown
                FROM vertex_wet_chunk
                WHERE embedding IS NULL
                  AND markdown IS NOT NULL AND markdown != ''
                LIMIT {int(batch_size)}
                """,
            )
            rows = cur.fetchall()

        if not rows:
            break

        vids = [r[0] for r in rows]
        texts = [str(r[1]) for r in rows]

        embeddings = embed_texts_768(texts)

        with sync_cursor() as cur:
            for vid, emb in zip(vids, embeddings):
                norm = math.sqrt(sum(v * v for v in emb))
                cur.execute(
                    "UPDATE vertex_wet_chunk SET embedding = %s, embedding_norm = %s WHERE vertex_id = %s",
                    (emb, float(norm), vid),
                )

        total_embedded += len(rows)
        LOG.info("embed_markdown domain=%s embedded_so_far=%d", domain, total_embedded)

    LOG.info("embed_markdown complete domain=%s total=%d", domain, total_embedded)
    return {
        "ok": True,
        "domain": domain,
        "total_embedded": total_embedded,
    }


# ── Zeebe task: update IVF centroids ──────────────────────────────────────────

def task_site_ivf_pq_update_centroids(
    domain: str = "",
    n_centroids: int = _DEFAULT_N_CENTROIDS,
    sample_limit: int = _TRAIN_SAMPLE_MAX,
) -> dict[str, Any]:
    """Re-cluster wet_chunk embeddings using faiss K-means.

    Reads vertex_wet_chunk WHERE domain=domain AND embedding IS NOT NULL,
    runs faiss.Kmeans (d=768, k=n_centroids), then upserts vertex_ivf_centroid rows.
    """
    try:
        import faiss  # type: ignore[import]
        import numpy as np  # type: ignore[import]
    except ImportError:
        return {"ok": False, "error": "faiss-cpu not installed"}

    if not domain:
        domain = _DEFAULT_COLLECTION

    LOG.info("ivfPq.updateCentroids domain=%s n_centroids=%d", domain, n_centroids)

    # Load embeddings (no domain filter — vertex_wet_chunk.domain stores per-URL hostnames)
    with sync_cursor() as cur:
        cur.execute(
            f"""
            SELECT vertex_id, embedding
            FROM vertex_wet_chunk
            WHERE embedding IS NOT NULL
            LIMIT {int(sample_limit)}
            """,
        )
        rows = cur.fetchall()

    if not rows:
        return {"ok": False, "error": "no embedded chunks found", "domain": domain}

    vids = [r[0] for r in rows]
    embeddings = np.array([r[1] for r in rows], dtype=np.float32)
    n_vecs = embeddings.shape[0]
    n_centroids = min(n_centroids, n_vecs)

    LOG.info("training K-means n=%d k=%d", n_vecs, n_centroids)
    kmeans = faiss.Kmeans(d=int(_DEFAULT_DIM), k=n_centroids, niter=20, verbose=False)
    kmeans.train(embeddings)
    centroids = kmeans.centroids  # (k, d)

    # Assign cluster IDs back to vertex_wet_chunk
    _, assignments = kmeans.index.search(embeddings, 1)
    assignments = assignments.flatten()

    # Upsert centroids into vertex_ivf_centroid
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with sync_cursor() as cur:
        for i, vec in enumerate(centroids):
            centroid_id = f"at://{_OWNER_DID}/com.etzhayyim.apps.site.ivfCentroid/{domain}-{i}"
            cur.execute(
                """
                INSERT INTO vertex_ivf_centroid (vertex_id, rkey, collection, embedding, actor_did, org_did)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (centroid_id, str(i), domain, list(vec.astype(float)), _OWNER_DID, _OWNER_DID),
            )

    # Batch-update ivf_cluster_id on vertex_wet_chunk
    with sync_cursor() as cur:
        for vid, cluster_id in zip(vids, assignments.tolist()):
            cur.execute(
                "UPDATE vertex_wet_chunk SET ivf_cluster_id = %s WHERE vertex_id = %s",
                (int(cluster_id), vid),
            )

    LOG.info("centroids written: %d, chunks assigned: %d", len(centroids), len(vids))
    return {
        "ok": True,
        "domain": domain,
        "n_centroids": len(centroids),
        "n_chunks_assigned": len(vids),
    }


# ── Zeebe task: train PQ codebook ─────────────────────────────────────────────

def task_site_ivf_pq_train_codebook(
    domain: str = "",
    version_tag: str = "",
    m_subspaces: int = _DEFAULT_M_SUBSPACES,
    k_centroids: int = _DEFAULT_K_CENTROIDS,
    sample_limit: int = _TRAIN_SAMPLE_MAX,
) -> dict[str, Any]:
    """Train a PQ codebook on embedding residuals for the given domain.

    Steps:
    1. Load embeddings + ivf_cluster_id from vertex_wet_chunk.
    2. Compute residuals (embedding minus nearest centroid).
    3. Split each residual into m_subspaces subvectors of dim subspace_dim.
    4. K-means each subspace → k_centroids cluster centres.
    5. Persist to vertex_pq_codebook (status='active'), mark previous 'superseded'.
    """
    try:
        import faiss  # type: ignore[import]
        import numpy as np  # type: ignore[import]
    except ImportError:
        return {"ok": False, "error": "faiss-cpu not installed"}

    if not domain:
        domain = _DEFAULT_COLLECTION
    if not version_tag:
        version_tag = time.strftime("%Y%m%d%H%M", time.gmtime())

    subspace_dim = _DEFAULT_DIM // m_subspaces  # 768 // 96 = 8

    LOG.info("trainCodebook domain=%s version=%s m=%d k=%d", domain, version_tag, m_subspaces, k_centroids)

    # Load centroids
    with sync_cursor() as cur:
        cur.execute(
            "SELECT rkey, embedding FROM vertex_ivf_centroid WHERE collection = %s",
            (domain,),
        )
        centroid_rows = cur.fetchall()
    if not centroid_rows:
        return {"ok": False, "error": "no centroids found — run updateCentroids first"}

    centroid_map = {int(r[0]): np.array(r[1], dtype=np.float32) for r in centroid_rows}

    # Load embeddings (no domain filter — vertex_wet_chunk.domain stores per-URL hostnames)
    with sync_cursor() as cur:
        cur.execute(
            f"""
            SELECT embedding, ivf_cluster_id
            FROM vertex_wet_chunk
            WHERE embedding IS NOT NULL AND ivf_cluster_id IS NOT NULL
            LIMIT {int(sample_limit)}
            """,
        )
        rows = cur.fetchall()

    if not rows:
        return {"ok": False, "error": "no embedded+assigned chunks"}

    embeddings = np.array([r[0] for r in rows], dtype=np.float32)
    cluster_ids = [int(r[1]) for r in rows]

    # Compute residuals
    residuals = embeddings.copy()
    for i, cid in enumerate(cluster_ids):
        if cid in centroid_map:
            residuals[i] -= centroid_map[cid]

    # Train PQ subspace codebooks
    all_centroids: list[list[list[float]]] = []
    for sub in range(m_subspaces):
        start = sub * subspace_dim
        end = start + subspace_dim
        sub_vecs = residuals[:, start:end].copy()
        kmeans = faiss.Kmeans(d=subspace_dim, k=k_centroids, niter=15, verbose=False)
        kmeans.train(sub_vecs)
        all_centroids.append(kmeans.centroids.tolist())

    # Persist codebook
    codebook_json = json.dumps(all_centroids)
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    collection_id = domain
    vertex_id = f"at://{_OWNER_DID}/com.etzhayyim.apps.site.pqCodebook/{domain}-{version_tag}"

    with sync_cursor() as cur:
        # Mark previous active as superseded
        cur.execute(
            "UPDATE vertex_pq_codebook SET status = 'superseded' WHERE collection_id = %s AND status = 'active'",
            (collection_id,),
        )
        cur.execute(
            """
            INSERT INTO vertex_pq_codebook
              (vertex_id, owner_did, rkey, collection_id, version_tag,
               m_subspaces, k_centroids, dim, subspace_dim,
               n_train_vectors, codebook_json, trained_at, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'active')
            """,
            (
                vertex_id, _OWNER_DID, version_tag, collection_id, version_tag,
                m_subspaces, k_centroids, _DEFAULT_DIM, subspace_dim,
                len(rows), codebook_json, now,
            ),
        )

    _invalidate_codebook_cache(collection_id)
    LOG.info("codebook trained and persisted: %s", vertex_id)
    return {
        "ok": True,
        "domain": domain,
        "version_tag": version_tag,
        "vertex_id": vertex_id,
        "n_train_vectors": len(rows),
        "m_subspaces": m_subspaces,
        "k_centroids": k_centroids,
    }


# ── Zeebe task: encode chunks ──────────────────────────────────────────────────

def task_site_ivf_pq_encode_chunks(
    domain: str = "",
    batch_size: int = _ENCODE_BATCH,
) -> dict[str, Any]:
    """Encode all wet_chunks that lack a current PQ code into vertex_wet_chunk_pq.

    Uses ADC-compatible encoding: for each chunk, subtract centroid residual,
    then assign nearest PQ centroid per subspace. Result stored as base64(96 bytes).
    """
    try:
        import numpy as np  # type: ignore[import]
    except ImportError:
        return {"ok": False, "error": "numpy not installed"}

    if not domain:
        domain = _DEFAULT_COLLECTION

    codebook = _get_active_codebook(domain)
    if not codebook:
        return {"ok": False, "error": "no active codebook — run trainCodebook first"}

    version_tag = codebook["version_tag"]
    m: int = codebook["m"]
    subspace_dim: int = codebook["subspace_dim"]
    cb_np = [np.array(codebook["centroids"][s], dtype=np.float32) for s in range(m)]

    # Load IVF centroids
    with sync_cursor() as cur:
        cur.execute(
            "SELECT rkey, embedding FROM vertex_ivf_centroid WHERE collection = %s",
            (domain,),
        )
        centroid_rows = cur.fetchall()
    centroid_map = {int(r[0]): np.array(r[1], dtype=np.float32) for r in centroid_rows}

    # Find chunks not yet encoded with this codebook version (no domain filter)
    with sync_cursor() as cur:
        cur.execute(
            f"""
            SELECT w.vertex_id, w.embedding, w.ivf_cluster_id
            FROM vertex_wet_chunk w
            WHERE w.embedding IS NOT NULL
              AND w.ivf_cluster_id IS NOT NULL
              AND NOT EXISTS (
                SELECT 1 FROM vertex_wet_chunk_pq p
                WHERE p.chunk_vertex_id = w.vertex_id
                  AND p.codebook_version = %s
              )
            LIMIT {int(batch_size)}
            """,
            (version_tag,),
        )
        rows = cur.fetchall()

    if not rows:
        return {"ok": True, "domain": domain, "encoded": 0, "message": "up to date"}

    encoded = 0
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with sync_cursor() as cur:
        for vid, emb_list, cluster_id in rows:
            emb = np.array(emb_list, dtype=np.float32)
            cid = int(cluster_id)
            if cid in centroid_map:
                residual = emb - centroid_map[cid]
            else:
                residual = emb

            # Encode: find nearest PQ centroid per subspace
            code_bytes = bytearray(m)
            for s in range(m):
                start = s * subspace_dim
                end = start + subspace_dim
                sub_vec = residual[start:end]
                dists = np.sum((cb_np[s] - sub_vec) ** 2, axis=1)
                code_bytes[s] = int(np.argmin(dists)) & 0xFF

            pq_code_b64 = base64.b64encode(bytes(code_bytes)).decode()
            pq_id = f"pq:{vid}:{version_tag}"
            cur.execute(
                """
                INSERT INTO vertex_wet_chunk_pq
                  (pq_id, chunk_vertex_id, ivf_cluster_id, codebook_version, domain, pq_code, encoded_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (pq_id, vid, cid, version_tag, domain, pq_code_b64, now),
            )
            encoded += 1

    LOG.info("encodeChunks domain=%s version=%s encoded=%d", domain, version_tag, encoded)
    return {
        "ok": True,
        "domain": domain,
        "version_tag": version_tag,
        "encoded": encoded,
        "remaining": None,
    }


# ── Synchronous ADC search (called by searchSemantic handler) ─────────────────

def ivf_pq_search_sync(
    query_vec: list[float],
    domain: str,
    top_k: int = 10,
    n_probe: int = 8,
) -> list[dict[str, Any]]:
    """ADC-based IVF+PQ search. Returns top_k hits with url, markdown_preview, score.

    Called synchronously from the site.searchSemantic XRPC handler.
    Codebook is process-level cached (threading.Lock protected).
    """
    try:
        import numpy as np  # type: ignore[import]
    except ImportError:
        return []

    codebook = _get_active_codebook(domain)
    if not codebook:
        return []

    version_tag = codebook["version_tag"]
    m: int = codebook["m"]
    k: int = codebook["k"]
    subspace_dim: int = codebook["subspace_dim"]
    cb_np = [np.array(codebook["centroids"][s], dtype=np.float32) for s in range(m)]

    q = np.array(query_vec, dtype=np.float32)

    # 1. Find nearest n_probe IVF centroids
    with sync_cursor() as cur:
        cur.execute(
            "SELECT rkey, embedding FROM vertex_ivf_centroid WHERE collection = %s",
            (domain,),
        )
        centroid_rows = cur.fetchall()
    if not centroid_rows:
        return []

    centroid_ids = [int(r[0]) for r in centroid_rows]
    centroid_vecs = np.array([r[1] for r in centroid_rows], dtype=np.float32)
    dists = np.sum((centroid_vecs - q) ** 2, axis=1)
    probe_idx = np.argsort(dists)[:n_probe]
    probe_cluster_ids = [centroid_ids[i] for i in probe_idx]

    # 2. Pre-compute ADC distance table: dist_table[m][k]
    dist_table = np.zeros((m, k), dtype=np.float32)
    for s in range(m):
        start = s * subspace_dim
        end = start + subspace_dim
        q_sub = q[start:end]
        diff = cb_np[s] - q_sub
        dist_table[s] = np.sum(diff ** 2, axis=1)

    # 3. Load PQ codes for probe clusters
    placeholders = ",".join(["%s"] * len(probe_cluster_ids))
    with sync_cursor() as cur:
        cur.execute(
            f"""
            SELECT p.pq_id, p.chunk_vertex_id, p.pq_code
            FROM vertex_wet_chunk_pq p
            WHERE p.ivf_cluster_id IN ({placeholders})
              AND p.codebook_version = %s
            LIMIT 2000
            """,
            probe_cluster_ids + [version_tag],
        )
        pq_rows = cur.fetchall()

    if not pq_rows:
        return []

    # 4. Score each PQ code via ADC lookup
    scored: list[tuple[float, str]] = []
    for _pq_id, vid, pq_code_b64 in pq_rows:
        code_bytes = base64.b64decode(pq_code_b64)
        score = 0.0
        for s, byte_val in enumerate(code_bytes[:m]):
            score += float(dist_table[s, byte_val])
        scored.append((score, vid))

    # Lower ADC score = closer (it approximates squared distance)
    scored.sort(key=lambda x: x[0])
    top_vids = [vid for _, vid in scored[:top_k]]

    # 5. Fetch markdown + url for top hits
    if not top_vids:
        return []
    placeholders2 = ",".join(["%s"] * len(top_vids))
    with sync_cursor() as cur:
        cur.execute(
            f"""
            SELECT vertex_id, url, domain, markdown, title, ivf_cluster_id
            FROM vertex_wet_chunk
            WHERE vertex_id IN ({placeholders2})
            """,
            top_vids,
        )
        chunk_rows = cur.fetchall()

    vid_to_score = {vid: score for score, vid in scored[:top_k]}
    hits = []
    for vertex_id, url, dom, markdown, title, cluster_id in chunk_rows:
        preview = (markdown or "")[:400]
        hits.append({
            "chunkVertexId": vertex_id,
            "domain": dom,
            "url": url or "",
            "title": title or "",
            "markdownPreview": preview,
            "score": round(float(vid_to_score.get(vertex_id, 9999.0)), 6),
            "clusterId": cluster_id,
        })
    hits.sort(key=lambda h: h["score"])
    return hits


# ── Zeebe worker registration ──────────────────────────────────────────────────

def register(worker: Any, *, timeout_ms: int) -> None:
    worker.task(
        task_type="site.ivfPq.embedMarkdown",
        single_value=False,
        timeout_ms=max(timeout_ms, 7_200_000),
    )(task_site_ivf_pq_embed_markdown)
    worker.task(
        task_type="site.ivfPq.updateCentroids",
        single_value=False,
        timeout_ms=max(timeout_ms, 3_600_000),
    )(task_site_ivf_pq_update_centroids)
    worker.task(
        task_type="site.ivfPq.trainCodebook",
        single_value=False,
        timeout_ms=max(timeout_ms, 3_600_000),
    )(task_site_ivf_pq_train_codebook)
    worker.task(
        task_type="site.ivfPq.encodeChunks",
        single_value=False,
        timeout_ms=max(timeout_ms, 1_800_000),
    )(task_site_ivf_pq_encode_chunks)
