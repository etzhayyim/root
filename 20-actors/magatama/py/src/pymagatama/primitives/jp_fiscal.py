"""JP Fiscal ingest primitives (ADR-0035 BPMN-as-actor, ADR-0056).

2 Zeebe task types for jp-fiscal.etzhayyim.com:
  jpFiscal.ingest.edinet       — EDINET v2 大量保有報告書 → vertex_jp_fiscal_beneficial_owner
  jpFiscal.ingest.egovContracts — e-GOV 省庁契約公表 CSV  → vertex_jp_fiscal_contract

Tables: vertex_jp_fiscal_beneficial_owner / vertex_jp_fiscal_contract
Owner:  did:web:jp-fiscal.etzhayyim.com
ADR:    0035 (JP tax money flow reverse topology)
"""

from __future__ import annotations

import datetime as _dt
import json
import time
import urllib.error
import urllib.request
from typing import Any

import aiohttp

from pymagatama import llm as _llm
from pymagatama.db_sync import sync_cursor


_OWNER_DID = "did:web:jp-fiscal.etzhayyim.com"
_COL_UBO = "ai.gftd.apps.jpFiscal.beneficialOwner"
_COL_CONTRACT = "ai.gftd.apps.jpFiscal.contract"
_EDINET_URL = "https://disclosure.edinet-fsa.go.jp/api/v2/documents.json"

_MINISTRY_URLS: dict[str, str] = {
    "mof":  "https://www.mof.go.jp/about/procurement/contract.csv",
    "mlit": "https://www.mlit.go.jp/about/procurement/contract.csv",
    "meti": "https://www.meti.go.jp/about/procurement/contract.csv",
    "mext": "https://www.mext.go.jp/about/procurement/contract.csv",
    "mhlw": "https://www.mhlw.go.jp/about/procurement/contract.csv",
}

_DEFAULT_MINISTRIES = list(_MINISTRY_URLS.keys())


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _today() -> str:
    return time.strftime("%Y-%m-%d", time.gmtime())


def _ubo_vid(doc_id: str) -> str:
    return f"at://{_OWNER_DID}/{_COL_UBO}/edinet-{doc_id}"


def _contract_vid(ministry: str, contract_no: str, seq: int) -> str:
    safe = (contract_no or str(seq)).replace("/", "-").replace(" ", "-")[:60]
    return f"at://{_OWNER_DID}/{_COL_CONTRACT}/{ministry}-{safe}"


def _is_dup_error(e: Exception) -> bool:
    s = str(e).lower()
    return "already exists" in s or "duplicate" in s or "unique" in s


# ---------------------------------------------------------------------------
# jpFiscal.ingest.edinet
# ---------------------------------------------------------------------------

async def task_jp_fiscal_ingest_edinet(
    date: str | None = None,
    limit: int = 500,
) -> dict:
    """Fetch EDINET v2 大量保有報告書 list for a date and write to vertex_jp_fiscal_beneficial_owner."""
    target_date = str(date or _today())
    lim = max(1, min(int(limit or 500), 1000))

    url = f"{_EDINET_URL}?date={target_date}&type=2"
    async with aiohttp.ClientSession() as session:
        async with session.get(
            url,
            headers={"User-Agent": "jp-fiscal.etzhayyim.com/1.0 contact@gftd.co.jp"},
            timeout=aiohttp.ClientTimeout(total=30),
        ) as resp:
            if resp.status != 200:
                return {"error": f"EDINET {resp.status}", "written": 0, "date": target_date}
            raw = await resp.json(content_type=None)

    # docTypeCode 140=大量保有報告書, 350=変更報告書, 4xx=訂正
    docs = [
        d for d in (raw.get("results") or [])
        if str(d.get("docTypeCode") or "").startswith("4")
        or str(d.get("docTypeCode") or "") in ("140", "350")
    ][:lim]

    written = 0
    errors = 0
    now = _utc_now()

    for d in docs:
        doc_id = str(d.get("docID") or "").strip()
        target = str(d.get("secCode") or d.get("subjectEdinetCode") or "").strip()
        filer = str(d.get("edinetCode") or d.get("filerName") or "").strip()
        if not doc_id or not target or not filer:
            continue

        child_did = f"did:web:legal-entity.etzhayyim.com:sec:{target}"
        parent_did = f"did:web:legal-entity.etzhayyim.com:edinet:{filer}"
        evidence_url = f"https://disclosure.edinet-fsa.go.jp/PublicDoc/{doc_id}"
        vid = _ubo_vid(doc_id)
        doc_type_code = str(d.get("docTypeCode") or "")
        form_name = {
            "140": "大量保有報告書",
            "350": "変更報告書",
        }.get(doc_type_code[:3], f"訂正({doc_type_code})")

        with sync_cursor() as cur:
            try:
                cur.execute(
                    "INSERT INTO vertex_jp_fiscal_beneficial_owner "
                    "(vertex_id, created_date, sensitivity_ord, owner_did, "
                    "child_did, child_jcn, parent_did, parent_type, "
                    "evidence_kind, evidence_url, observed_at, status, "
                    "external_refs_json, pii_tier, source_id, document_id, "
                    "actor_did, org_did, created_at) "
                    "VALUES (%s,%s,%s,%s, %s,%s,%s,%s, %s,%s,%s,%s, %s,%s,%s,%s, %s,%s,%s)",
                    (
                        vid, target_date, 100, _OWNER_DID,
                        child_did, target, parent_did, "LEGAL",
                        "EDINET", evidence_url, target_date, "PENDING",
                        f'[{{"source":"EDINET","id":"{doc_id}","form":"{form_name}"}}]',
                        1, "EDINET", doc_id,
                        _OWNER_DID, "anon", now,
                    ),
                )
                written += 1
            except Exception as e:  # noqa: BLE001
                if _is_dup_error(e):
                    written += 1
                else:
                    errors += 1

    return {
        "ok": True,
        "date": target_date,
        "total": len(docs),
        "written": written,
        "errors": errors,
    }


# ---------------------------------------------------------------------------
# jpFiscal.ingest.egovContracts
# ---------------------------------------------------------------------------

async def task_jp_fiscal_ingest_egov_contracts(
    ministries: list[str] | None = None,
    limit: int = 50,
) -> dict:
    """Fetch e-GOV 省庁契約公表 CSVs and write to vertex_jp_fiscal_contract."""
    targets = list(ministries or _DEFAULT_MINISTRIES)
    lim = max(1, min(int(limit or 50), 500))
    now = _utc_now()
    today = _today()

    total_written = 0
    total_errors = 0
    ministry_results: dict[str, dict] = {}

    async with aiohttp.ClientSession() as session:
        for ministry in targets:
            url = _MINISTRY_URLS.get(ministry)
            if not url:
                ministry_results[ministry] = {"skipped": True, "reason": "unknown ministry"}
                continue

            ministry_did = f"did:web:gov.etzhayyim.com:country:jpn:{ministry}"
            written = 0
            errors = 0

            try:
                async with session.get(
                    url,
                    headers={"User-Agent": "jp-fiscal.etzhayyim.com/1.0 contact@gftd.co.jp"},
                    timeout=aiohttp.ClientTimeout(total=20),
                ) as resp:
                    if resp.status != 200:
                        ministry_results[ministry] = {"error": f"HTTP {resp.status}"}
                        continue
                    csv_text = await resp.text(encoding="utf-8", errors="replace")
            except Exception as e:  # noqa: BLE001
                ministry_results[ministry] = {"error": str(e)[:200]}
                continue

            rows = [r for r in csv_text.split("\n")[1:] if r.strip()][:lim]

            for seq, line in enumerate(rows):
                cols = line.rstrip("\r").split(",")
                contract_no = (cols[0] if len(cols) > 0 else "").strip()
                contractor_jcn = (cols[1] if len(cols) > 1 else "").strip()
                method = (cols[2] if len(cols) > 2 else "").strip() or "unknown"
                amount_raw = (cols[3] if len(cols) > 3 else "").strip()
                signed_date_raw = (cols[4] if len(cols) > 4 else "").strip()
                deliverable = (cols[5] if len(cols) > 5 else "").strip()

                if not contractor_jcn:
                    continue
                amount_jpy = int("".join(c for c in amount_raw if c.isdigit()) or "0")
                if amount_jpy == 0:
                    continue

                # Parse date — expect YYYY-MM-DD or YYYY/MM/DD; fall back to today
                signed_date = today
                if signed_date_raw:
                    cleaned = signed_date_raw.replace("/", "-")
                    if len(cleaned) >= 10:
                        signed_date = cleaned[:10]

                contractor_did = f"did:web:legal-entity.etzhayyim.com:jcn:{contractor_jcn}"
                kaikeiho_article = "29-3" if method in ("zuikei-random", "随契") else "29-1"
                vid = _contract_vid(ministry, contract_no, seq)

                with sync_cursor() as cur:
                    try:
                        cur.execute(
                            "INSERT INTO vertex_jp_fiscal_contract "
                            "(vertex_id, created_date, sensitivity_ord, owner_did, "
                            "issuer_did, contractor_did, contractor_jcn, contract_no, "
                            "method, amount_jpy, signed_date, deliverable, "
                            "kaikeiho_article, publication_url, "
                            "actor_did, org_did, created_at) "
                            "VALUES (%s,%s,%s,%s, %s,%s,%s,%s, %s,%s,%s,%s, %s,%s, %s,%s,%s)",
                            (
                                vid, today, 100, _OWNER_DID,
                                ministry_did, contractor_did, contractor_jcn, contract_no,
                                method, amount_jpy, signed_date, deliverable,
                                kaikeiho_article, url,
                                _OWNER_DID, "anon", now,
                            ),
                        )
                        written += 1
                    except Exception as e:  # noqa: BLE001
                        if _is_dup_error(e):
                            written += 1
                        else:
                            errors += 1

            ministry_results[ministry] = {"written": written, "errors": errors, "rows": len(rows)}
            total_written += written
            total_errors += errors

    return {
        "ok": True,
        "written": total_written,
        "errors": total_errors,
        "ministries": ministry_results,
    }


# ---------------------------------------------------------------------------
# DSL scraper (runScrapers) — ported from CF Worker app.ts runScraper batch
# ---------------------------------------------------------------------------

_RATE_MS = 1500  # per-host politeness delay ms


def _now_iso() -> str:
    return (
        _dt.datetime.now(tz=_dt.UTC)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _polite_fetch_sync(url: str, ua: str | None = None) -> str:
    """Rate-limited sync HTTP GET. Returns text capped at 60 KB."""
    time.sleep(_RATE_MS / 1000.0)
    headers = {"User-Agent": ua} if ua else {}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read(65_536).decode("utf-8", errors="replace")
    except urllib.error.URLError as exc:
        raise RuntimeError(f"fetch {url} failed: {exc}") from exc


def _load_dsls(only: str | None = None) -> list[dict[str, Any]]:
    q = (
        "SELECT d.vertex_id AS dsl_vid, s.source_url, s.ministry_did, s.ua, s.rate_ms,"
        " s.content_type, d.target_table, d.target_columns, d.extract_hints,"
        " d.edge_emit, d.llm_model, d.max_rows_per_run, d.prompt_override"
        " FROM vertex_scraper_dsl d"
        " JOIN vertex_scraper_source s ON s.vertex_id = d.source_vid"
    )
    with sync_cursor() as cur:
        if only:
            cur.execute(q + " WHERE d.vertex_id = %s AND s.status = 'active'", (only,))
        else:
            cur.execute(q + " WHERE s.status = 'active' AND d.dsl_kind = 'schema-first'"
                        + f" LIMIT {50}")
        col_names = [c[0] for c in cur.description]
        return [dict(zip(col_names, row)) for row in (cur.fetchall() or [])]


def _record_scraper_run(
    dsl_vid: str, status: str,
    extracted: int, emitted: int, edges: int,
    err_summary: str | None = None,
) -> None:
    run_id = f"run-{int(time.time() * 1000)}-{dsl_vid[-8:]}"
    now = _now_iso()
    with sync_cursor() as cur:
        cur.execute(
            "INSERT INTO vertex_scraper_run"
            " (vertex_id, dsl_vid, started_at, finished_at, status,"
            "  extracted_rows, emitted_records, emitted_edges, error_summary,"
            "  created_date, sensitivity_ord, owner_did, created_at)"
            " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (
                run_id, dsl_vid, now, now, status,
                extracted, emitted, edges, err_summary,
                _today(), 100, _OWNER_DID, now,
            ),
        )


def _run_single_dsl(dsl: dict[str, Any]) -> dict[str, Any]:
    try:
        raw = _polite_fetch_sync(dsl["source_url"], dsl.get("ua"))
        if len(raw) > 60_000:
            raw = raw[:60_000]

        target_cols: list[str] = json.loads(dsl["target_columns"])
        hints: dict[str, str] = json.loads(dsl["extract_hints"])
        max_rows = int(dsl.get("max_rows_per_run") or 200)

        sys_prompt = dsl.get("prompt_override") or (
            f"Extract structured rows from the following {dsl['content_type']} document. "
            'Return JSON {"rows": [...]} where each row has these typed fields:\n'
            + "\n".join(f"  - {c}: {hints.get(c, '(no hint)')}" for c in target_cols)
            + "\nDrop rows missing required identifiers."
              " Numeric amounts in Japanese Yen as integers."
        )

        result = _llm.call_tier_json("structured", sys_prompt, raw,
                                     max_tokens=4096, temperature=0.1)
        if not result.get("ok"):
            raise RuntimeError(f"LLM failed: {result.get('error', 'unknown')}")

        rows: list[dict] = (result.get("data") or {}).get("rows", [])[:max_rows]

        emitted = 0
        for row in rows:
            cols = [c for c in target_cols if row.get(c) is not None]
            if not cols:
                continue
            col_str = ", ".join(cols)
            val_str = ", ".join(["%s"] * len(cols))
            try:
                with sync_cursor() as cur:
                    cur.execute(
                        f"INSERT INTO {dsl['target_table']} ({col_str}) VALUES ({val_str})",
                        [row[c] for c in cols],
                    )
                emitted += 1
            except Exception as e:  # noqa: BLE001
                print(f"[jp_fiscal dsl insert] {dsl['target_table']}: {e!s:.200}")

        _record_scraper_run(dsl["dsl_vid"], "success" if emitted > 0 else "partial",
                             len(rows), emitted, 0)
        return {"extracted": len(rows), "emitted": emitted, "error": None}

    except Exception as e:  # noqa: BLE001
        msg = str(e)[:300]
        print(f"[jp_fiscal dsl] {dsl.get('dsl_vid', '?')}: {msg}")
        try:
            _record_scraper_run(dsl["dsl_vid"], "failed", 0, 0, 0, msg)
        except Exception:  # noqa: BLE001
            pass
        return {"extracted": 0, "emitted": 0, "error": msg}


def task_jp_fiscal_run_scrapers(dsl_vid: str = "") -> dict[str, Any]:
    """Zeebe: run all active schema-first DSL scrapers (or a single one by dsl_vid)."""
    only = dsl_vid or None
    dsls = _load_dsls(only)
    total_emitted = 0
    errors: list[str] = []
    for dsl in dsls:
        r = _run_single_dsl(dsl)
        total_emitted += r["emitted"]
        if r["error"]:
            errors.append(f"{dsl['dsl_vid']}: {r['error']}")
    return {"ran": len(dsls), "emitted": total_emitted, "errors": errors}


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def register(worker: Any, *, timeout_ms: int) -> None:
    """Wire jp_fiscal primitives onto the shared LangServer worker."""

    def t(name: str, fn: Any, *, timeout: int | None = None) -> None:
        worker.task(
            task_type=name,
            single_value=False,
            timeout_ms=timeout if timeout is not None else timeout_ms,
        )(fn)

    t("jpFiscal.ingest.edinet",        task_jp_fiscal_ingest_edinet,         timeout=120_000)
    t("jpFiscal.ingest.egovContracts", task_jp_fiscal_ingest_egov_contracts,  timeout=180_000)
    t("jpFiscal.run.scrapers",         task_jp_fiscal_run_scrapers,           timeout=600_000)


__all__ = [
    "register",
    "task_jp_fiscal_ingest_edinet",
    "task_jp_fiscal_ingest_egov_contracts",
    "task_jp_fiscal_run_scrapers",
]
