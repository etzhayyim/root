"""LangServer actor for legal-entity collection."""

from __future__ import annotations

import asyncio
import csv
import json
import logging
import os
import sys
from io import StringIO
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
import uvicorn


LOG = logging.getLogger("legal-entity-collector")
AGENTGATEWAY_MCP_URL = os.environ.get(
    "AGENTGATEWAY_MCP_URL",
    "http://agentgateway-mcp.mitama-udf.svc.cluster.local:8080",
)
PORT = int(os.environ.get("PORT", os.environ.get("HEALTH_PORT", "8080")))
GLEIF_API = "https://api.gleif.org/api/v1/lei-records"
SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
COLLECTION = "com.etzhayyim.apps.legalEntity.legalEntity"
COLLECTION_COMPANY_FILING = "com.etzhayyim.apps.legalEntity.companyFiling"
COLLECTION_COMPANY_FACT = "com.etzhayyim.apps.legalEntity.companyFact"
COLLECTOR_DID = "did:web:legal-entity.etzhayyim.com"
SEC_FACT_SPECS = [
    {
        "canonical": "revenue",
        "namespace": "us-gaap",
        "concepts": ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues", "SalesRevenueNet", "SalesRevenueGoodsNet"],
    },
    {"canonical": "employee_count", "namespace": "dei", "concepts": ["EntityNumberOfEmployees", "NumberOfEmployees"]},
    {"canonical": "assets", "namespace": "us-gaap", "concepts": ["Assets"]},
    {"canonical": "net_income", "namespace": "us-gaap", "concepts": ["NetIncomeLoss", "ProfitLoss"]},
]
COUNTRY_TASK_SOURCES = {
    "legalEntity.registry.collectJpn": "NTA_JPN",
    "legalEntity.registry.collectGbr": "CH_GBR",
    "legalEntity.registry.collectFra": "SIRENE_FRA",
    "legalEntity.registry.collectNor": "BRREG_NOR",
    "legalEntity.registry.collectDnk": "CVR_DNK",
    "legalEntity.registry.collectFin": "PRH_FIN",
    "legalEntity.registry.collectEst": "ARIK_EST",
    "legalEntity.registry.collectCze": "ARES_CZE",
    "legalEntity.registry.collectNzl": "MBIE_NZL",
    "legalEntity.registry.collectChe": "ZEFIX_CHE",
    "legalEntity.registry.collectNld": "KVK_NLD",
    "legalEntity.registry.collectIsr": "RASHAM_ISR",
}
TOOLS = {
    "legalEntity.gleif.fetchPages",
    "legalEntity.edgar.collectUsa",
    "legalEntity.edgar.ingestSecDisclosure",
    "legalEntity.gleif.registerDids",
    *COUNTRY_TASK_SOURCES.keys(),
}


def configure_logging() -> None:
    if LOG.handlers:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    LOG.addHandler(handler)
    LOG.setLevel(os.environ.get("LOG_LEVEL", "INFO"))


def now_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


async def fetch_gleif_page(page: int, page_size: int) -> dict[str, Any]:
    params = {
        "page[size]": str(page_size),
        "page[number]": str(page),
        "filter[entity.status]": "ACTIVE",
    }
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        res = await client.get(GLEIF_API, params=params, headers={"Accept": "application/vnd.api+json"})
    res.raise_for_status()
    return res.json()


def gleif_to_record(rec: dict[str, Any]) -> dict[str, Any]:
    attrs = rec.get("attributes") or {}
    entity = attrs.get("entity") or {}
    registration = attrs.get("registration") or {}
    legal_name = (entity.get("legalName") or {}).get("name") or ""
    legal_address = entity.get("legalAddress") or {}
    legal_form = entity.get("legalForm") or {}
    lei = attrs.get("lei") or ""
    return {
        "$type": COLLECTION,
        "name": legal_name,
        "displayName": legal_name,
        "description": f"LEI {lei} - {entity.get('jurisdiction') or ''}",
        "entityType": entity.get("category") or "",
        "registrationNumber": entity.get("registeredAs") or "",
        "jurisdiction": entity.get("jurisdiction") or "",
        "country": legal_address.get("country") or "",
        "entityStatus": entity.get("status") or "ACTIVE",
        "lei": lei,
        "industryCode": legal_form.get("id") or "",
        "incorporationDate": entity.get("creationDate") or "",
        "registrationStatus": registration.get("status") or "",
        "sourceDid": COLLECTOR_DID,
        "createdAt": now_iso(),
    }


def edgar_to_record(item: dict[str, Any]) -> dict[str, Any]:
    cik = str(item.get("cik_str") or "")
    name = str(item.get("title") or "")
    padded_cik = cik.zfill(10)
    return {
        "$type": COLLECTION,
        "name": name,
        "displayName": name,
        "description": f"edgar_usa:{cik} - US",
        "entityType": "SEC Registrant",
        "registrationNumber": padded_cik,
        "jurisdiction": "US",
        "country": "US",
        "entityStatus": "ACTIVE",
        "lei": "",
        "industryCode": "",
        "incorporationDate": "",
        "source": "edgar_usa",
        "sourceRecordId": cik,
        "sourceDid": COLLECTOR_DID,
        "createdAt": now_iso(),
    }


def clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def entity_to_record(
    *,
    name: Any,
    registration_number: Any,
    jurisdiction: Any,
    country: str,
    entity_type: Any = "",
    entity_status: Any = "ACTIVE",
    lei: Any = "",
    industry_code: Any = "",
    incorporation_date: Any = "",
    source: str,
    source_record_id: Any,
) -> dict[str, Any] | None:
    record_name = clean(name)
    record_id = clean(source_record_id or registration_number)
    reg_number = clean(registration_number)
    if not record_name or not record_id:
        return None
    return {
        "$type": COLLECTION,
        "name": record_name,
        "displayName": record_name,
        "description": f"{source.lower()}:{record_id} - {clean(jurisdiction)}",
        "entityType": clean(entity_type),
        "registrationNumber": reg_number,
        "jurisdiction": clean(jurisdiction),
        "country": country,
        "entityStatus": clean(entity_status) or "ACTIVE",
        "lei": clean(lei),
        "industryCode": clean(industry_code),
        "incorporationDate": clean(incorporation_date),
        "source": source.lower(),
        "sourceRecordId": record_id,
        "sourceDid": COLLECTOR_DID,
        "createdAt": now_iso(),
    }


def result_payload(
    source: str,
    pages: int,
    page_size: int,
    start_page: int,
    total_inserted: int,
    total_skipped: int,
    api_total: int,
    first_error: str,
    page_results: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "result": {
            "ok": not first_error,
            "source": source,
            "pagesProcessed": len(page_results),
            "pageSize": page_size,
            "startPage": start_page,
            "totalInserted": total_inserted,
            "totalSkipped": total_skipped,
            "apiTotal": api_total,
            "firstError": first_error,
            "pages": page_results,
            "ts": now_iso(),
        }
    }


async def get_json(url: str, *, params: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> Any:
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        res = await client.get(url, params=params, headers=headers or {"Accept": "application/json"})
    res.raise_for_status()
    return res.json()


async def post_json(url: str, payload: dict[str, Any], *, headers: dict[str, str] | None = None) -> Any:
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        res = await client.post(url, json=payload, headers=headers or {"Accept": "application/json"})
    res.raise_for_status()
    return res.json()


async def get_text(url: str, *, params: dict[str, Any] | None = None) -> str:
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        res = await client.get(url, params=params)
    res.raise_for_status()
    return res.text


def collect_records(items: list[Any], mapper: Any) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for item in items:
        if isinstance(item, dict):
            record = mapper(item)
            if record:
                records.append(record)
    return records


async def commit_entities(source: str, page: int, records: list[dict[str, Any]]) -> dict[str, Any]:
    url = os.environ.get(
        "LEGAL_ENTITY_COMMIT_ENTITIES_URL",
        "https://legal-entity.etzhayyim.com/xrpc/com.etzhayyim.apps.legalEntity.commitEntities",
    )
    async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
        res = await client.post(url, json={"source": source, "page": page, "records": records})
    if res.status_code >= 400:
        raise RuntimeError(f"commitEntities {res.status_code}: {res.text[:500]}")
    return res.json()


async def fetch_sec_tickers() -> dict[str, Any]:
    headers = {
        "Accept": "application/json",
        "User-Agent": "etzhayyim-legal-entity/1.0 legal-entity@etzhayyim.com",
    }
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        res = await client.get(SEC_TICKERS_URL, headers=headers)
    res.raise_for_status()
    return res.json()


def normalize_cik(value: Any) -> str:
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    return digits.zfill(10) if digits else ""


def to_float_or_none(value: Any) -> float | int | None:
    if isinstance(value, (int, float)):
        return value
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


async def resolve_sec_cik(ticker: str, cik: str) -> tuple[str, str]:
    normalized = normalize_cik(cik)
    if normalized:
        return normalized, ticker.upper()
    symbol = clean(ticker).upper()
    if not symbol:
        raise ValueError("ticker or cik required")
    data = await fetch_sec_tickers()
    for item in data.values():
        if isinstance(item, dict) and clean(item.get("ticker")).upper() == symbol:
            return normalize_cik(item.get("cik_str")), symbol
    raise ValueError(f"SEC ticker not found: {symbol}")


async def fetch_sec_json(url: str) -> dict[str, Any]:
    headers = {
        "Accept": "application/json",
        "User-Agent": "etzhayyim-legal-entity/1.0 legal-entity@etzhayyim.com",
    }
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        res = await client.get(url, headers=headers)
    res.raise_for_status()
    return res.json()


def pick_fact_units(concept_node: dict[str, Any]) -> list[dict[str, Any]]:
    units = concept_node.get("units") if isinstance(concept_node, dict) else {}
    if not isinstance(units, dict):
        return []
    preferred = ["USD", "pure", "shares"]
    ordered_units = [unit for unit in preferred if unit in units] + [unit for unit in units if unit not in preferred]
    rows: list[dict[str, Any]] = []
    for unit in ordered_units:
        values = units.get(unit) or []
        if isinstance(values, list):
            rows.extend({"unit": unit, **value} for value in values if isinstance(value, dict))
    return rows


def build_recent_filing_records(submissions: dict[str, Any], company_did: str, cik: str, filing_limit: int) -> list[dict[str, Any]]:
    recent = ((submissions.get("filings") or {}).get("recent") or {}) if isinstance(submissions, dict) else {}
    allowed_forms = {"10-K", "10-Q", "20-F", "40-F", "6-K", "8-K"}
    records: list[dict[str, Any]] = []
    forms = recent.get("form") or []
    for index in range(len(forms)):
        filing_type = clean(forms[index])
        if filing_type not in allowed_forms:
            continue
        accession_no = clean((recent.get("accessionNumber") or [])[index] if index < len(recent.get("accessionNumber") or []) else "")
        if not accession_no:
            continue
        accession_compact = accession_no.replace("-", "")
        filing_date = clean((recent.get("filingDate") or [])[index] if index < len(recent.get("filingDate") or []) else "")
        period_end = clean((recent.get("reportDate") or [])[index] if index < len(recent.get("reportDate") or []) else "")
        primary_document = clean((recent.get("primaryDocument") or [])[index] if index < len(recent.get("primaryDocument") or []) else "")
        filing_url = (
            f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_compact}/{primary_document}"
            if primary_document
            else f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_compact}/"
        )
        issuer_tickers = submissions.get("tickers") if isinstance(submissions.get("tickers"), list) else []
        issuer_exchanges = submissions.get("exchanges") if isinstance(submissions.get("exchanges"), list) else []
        records.append(
            {
                "$type": COLLECTION_COMPANY_FILING,
                "companyDid": company_did,
                "filingSource": "sec_edgar",
                "filingType": filing_type,
                "filingDate": filing_date,
                "periodStart": "",
                "periodEnd": period_end,
                "fiscalYear": int(period_end[:4]) if len(period_end) >= 4 and period_end[:4].isdigit() else None,
                "fiscalQuarter": max(1, min(4, (int(period_end[5:7]) + 2) // 3)) if filing_type == "10-Q" and len(period_end) >= 7 and period_end[5:7].isdigit() else None,
                "accessionNo": accession_no,
                "filingUrl": filing_url,
                "issuerName": clean(submissions.get("name")),
                "issuerTicker": clean(issuer_tickers[0] if issuer_tickers else ""),
                "issuerExchange": clean(issuer_exchanges[0] if issuer_exchanges else ""),
                "country": "US",
                "language": "en",
                "sourceLicense": "public-domain",
                "props": json.dumps({"secPrimaryDocDescription": clean((recent.get("primaryDocDescription") or [])[index] if index < len(recent.get("primaryDocDescription") or []) else "")}),
                "createdAt": now_iso(),
            }
        )
        if len(records) >= filing_limit:
            break
    return records


def build_company_fact_records(company_facts: dict[str, Any], company_did: str, cik: str, facts_limit: int) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    facts = company_facts.get("facts") or {}
    for spec in SEC_FACT_SPECS:
        namespace = spec["namespace"]
        ns_root = facts.get(namespace) if isinstance(facts, dict) else {}
        if not isinstance(ns_root, dict):
            continue
        for concept_name in spec["concepts"]:
            concept = ns_root.get(concept_name)
            if not isinstance(concept, dict):
                continue
            values = [row for row in pick_fact_units(concept) if row.get("val") is not None]
            values.sort(key=lambda row: clean(row.get("end") or row.get("fy")), reverse=True)
            for value in values:
                accession_no = clean(value.get("accn"))
                accession_compact = accession_no.replace("-", "")
                end = clean(value.get("end"))
                val = value.get("val")
                records.append(
                    {
                        "$type": COLLECTION_COMPANY_FACT,
                        "companyDid": company_did,
                        "filingDid": f"filing:edgar:{cik}:{accession_compact}" if accession_compact else "",
                        "factNamespace": namespace,
                        "factName": spec["canonical"],
                        "factValueNum": to_float_or_none(val),
                        "factValueText": "" if isinstance(val, (int, float)) else clean(val),
                        "unit": clean(value.get("unit")),
                        "currency": "USD" if clean(value.get("unit")).upper() == "USD" else "",
                        "periodStart": clean(value.get("start")),
                        "periodEnd": end,
                        "asOfDate": end or clean(value.get("frame")),
                        "fiscalYear": int(value.get("fy")) if clean(value.get("fy")).isdigit() else int(end[:4]) if len(end) >= 4 and end[:4].isdigit() else None,
                        "fiscalQuarter": int(clean(value.get("fp"))[1]) if clean(value.get("fp")) in {"Q1", "Q2", "Q3", "Q4"} else None,
                        "sourceUrl": f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_compact}/" if accession_compact else "https://data.sec.gov/api/xbrl/companyfacts/",
                        "sourceMethod": "sec_companyfacts",
                        "confidence": 0.95,
                        "createdAt": now_iso(),
                    }
                )
                if len(records) >= facts_limit:
                    return records
            break
    return records


async def commit_sec_disclosure(cik: str, ticker: str, company_did: str, filings: list[dict[str, Any]], facts: list[dict[str, Any]]) -> dict[str, Any]:
    url = os.environ.get(
        "LEGAL_ENTITY_COMMIT_SEC_DISCLOSURE_URL",
        "https://legal-entity.etzhayyim.com/xrpc/com.etzhayyim.apps.legalEntity.commitSecDisclosure",
    )
    payload = {"source": "SEC_EDGAR", "cik": cik, "ticker": ticker, "companyDid": company_did, "filings": filings, "facts": facts}
    async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
        res = await client.post(url, json=payload)
    if res.status_code >= 400:
        raise RuntimeError(f"commitSecDisclosure {res.status_code}: {res.text[:500]}")
    return res.json()


def gleif_to_did(rec: dict[str, Any]) -> dict[str, Any] | None:
    attrs = rec.get("attributes") or {}
    entity = attrs.get("entity") or {}
    lei = attrs.get("lei") or ""
    legal_name = ((entity.get("legalName") or {}).get("name") or "").strip()
    if not lei or not legal_name:
        return None
    jurisdiction = entity.get("jurisdiction") or ""
    return {
        "path": f"lei:{lei}",
        "doc": {
            "displayName": legal_name,
            "description": f"LEI {lei} - {jurisdiction}",
        },
    }


async def commit_entity_dids(source: str, page: int, dids: list[dict[str, Any]]) -> dict[str, Any]:
    url = os.environ.get(
        "LEGAL_ENTITY_COMMIT_ENTITY_DIDS_URL",
        "https://legal-entity.etzhayyim.com/xrpc/com.etzhayyim.apps.legalEntity.commitEntityDids",
    )
    async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
        res = await client.post(url, json={"source": source, "page": page, "dids": dids})
    if res.status_code >= 400:
        raise RuntimeError(f"commitEntityDids {res.status_code}: {res.text[:500]}")
    return res.json()


async def fetch_country_registry_page(
    task_type: str,
    page: int,
    page_size: int,
    variables: dict[str, Any],
) -> tuple[list[dict[str, Any]], int]:
    if task_type == "legalEntity.registry.collectJpn":
        params: dict[str, Any] = {
            "id": os.environ.get("NTA_APPLICATION_ID", "etzhayyim-legal-entity"),
            "type": "12",
            "from": clean(variables.get("from") or "2015-10-05"),
            "to": clean(variables.get("to") or now_iso()[:10]),
            "divide": page,
        }
        if variables.get("kind"):
            params["kind"] = clean(variables.get("kind"))
        if variables.get("prefecture"):
            params["address"] = clean(variables.get("prefecture"))
        text = await get_text("https://api.houjin-bangou.nta.go.jp/4/diff", params=params)
        rows = list(csv.reader(StringIO(text)))
        records: list[dict[str, Any]] = []
        for cols in rows[1:]:
            if len(cols) < 9 or len(records) >= page_size:
                continue
            record = entity_to_record(
                name=cols[6],
                registration_number=cols[1],
                jurisdiction=f"JP-{clean(cols[7])}",
                country="JP",
                entity_type=cols[5] if len(cols) > 5 else "",
                entity_status="ACTIVE",
                incorporation_date=cols[4] if len(cols) > 4 else "",
                source="NTA_JPN",
                source_record_id=cols[1],
            )
            if record:
                records.append(record)
        return records, len(records)

    if task_type == "legalEntity.registry.collectGbr":
        params = {
            "company_status": clean(variables.get("companyStatus") or "active"),
            "size": page_size,
            "start_index": int(variables.get("startIndex") or 0) + page * page_size,
        }
        if variables.get("companyType"):
            params["company_type"] = clean(variables.get("companyType"))
        if variables.get("incorporatedFrom"):
            params["incorporated_from"] = clean(variables.get("incorporatedFrom"))
        data = await get_json("https://api.company-information.service.gov.uk/advanced-search/companies", params=params)
        records = collect_records(data.get("items") or [], lambda item: entity_to_record(
            name=item.get("company_name"),
            registration_number=item.get("company_number"),
            jurisdiction="GB",
            country="GB",
            entity_type=item.get("company_type"),
            entity_status=item.get("company_status") or "active",
            industry_code=(item.get("sic_codes") or [""])[0],
            incorporation_date=item.get("date_of_creation"),
            source="CH_GBR",
            source_record_id=item.get("company_number"),
        ))
        return records, int(data.get("total_results") or 0)

    if task_type == "legalEntity.registry.collectFra":
        cursor = clean(variables.get("cursor"))
        params = {"nombre": page_size}
        if cursor and page == int(variables.get("startPage") or 0):
            params["curseur"] = cursor
        elif not cursor:
            params["debut"] = page * page_size
        filters: list[str] = []
        if variables.get("activesOnly") is not False:
            filters.append("etatAdministratifUniteLegale:A")
        if variables.get("departement"):
            filters.append(f"codePostalEtablissement:{clean(variables.get('departement'))}*")
        if filters:
            params["q"] = " AND ".join(filters)
        data = await get_json("https://api.insee.fr/entreprises/sirene/V3.11/siren", params=params)
        records = collect_records(data.get("unitesLegales") or [], lambda item: entity_to_record(
            name=((item.get("periodesUniteLegale") or [{}])[0]).get("denominationUniteLegale") or item.get("siren"),
            registration_number=item.get("siren"),
            jurisdiction="FR",
            country="FR",
            entity_type=((item.get("periodesUniteLegale") or [{}])[0]).get("categorieJuridiqueUniteLegale"),
            entity_status="ACTIVE" if ((item.get("periodesUniteLegale") or [{}])[0]).get("etatAdministratifUniteLegale") == "A" else "INACTIVE",
            industry_code=((item.get("periodesUniteLegale") or [{}])[0]).get("activitePrincipaleUniteLegale"),
            incorporation_date=item.get("dateCreationUniteLegale"),
            source="SIRENE_FRA",
            source_record_id=item.get("siren"),
        ))
        return records, int((data.get("header") or {}).get("total") or 0)

    if task_type == "legalEntity.registry.collectNor":
        params = {"size": page_size, "page": page}
        if variables.get("organisasjonsform"):
            params["organisasjonsform"] = clean(variables.get("organisasjonsform"))
        data = await get_json("https://data.brreg.no/enhetsregisteret/api/enheter", params=params)
        records = collect_records(((data.get("_embedded") or {}).get("enheter") or []), lambda item: entity_to_record(
            name=item.get("navn"),
            registration_number=item.get("organisasjonsnummer"),
            jurisdiction=f"NO-{clean((item.get('forretningsadresse') or {}).get('kommunenummer'))}",
            country="NO",
            entity_type=(item.get("organisasjonsform") or {}).get("kode"),
            entity_status="ACTIVE" if item.get("registreringsdatoEnhetsregisteret") else "INACTIVE",
            industry_code=(item.get("naeringskode1") or {}).get("kode"),
            incorporation_date=item.get("stiftelsesdato") or item.get("registreringsdatoEnhetsregisteret"),
            source="BRREG_NOR",
            source_record_id=item.get("organisasjonsnummer"),
        ))
        return records, int((data.get("page") or {}).get("totalElements") or 0)

    if task_type == "legalEntity.registry.collectDnk":
        data = await get_json("https://cvrapi.dk/api", params={"country": "dk", "format": "json"})
        records = collect_records([data], lambda item: entity_to_record(
            name=item.get("name"),
            registration_number=item.get("vat"),
            jurisdiction="DK",
            country="DK",
            entity_type=item.get("companydesc") or variables.get("virksomhedsform"),
            entity_status="ACTIVE" if item.get("status") == "NORMAL" else item.get("status") or "ACTIVE",
            industry_code=item.get("industrycode"),
            incorporation_date=item.get("startdate"),
            source="CVR_DNK",
            source_record_id=item.get("vat"),
        ))
        return records, len(records)

    if task_type == "legalEntity.registry.collectFin":
        params = {"totalResults": "true", "maxResults": page_size, "resultsFrom": page * page_size}
        if variables.get("companyForm"):
            params["companyForm"] = clean(variables.get("companyForm"))
        data = await get_json("https://avoindata.prh.fi/bis/v1", params=params)
        records = collect_records(data.get("results") or [], lambda item: entity_to_record(
            name=item.get("name"),
            registration_number=item.get("businessId"),
            jurisdiction="FI",
            country="FI",
            entity_type=item.get("companyForm"),
            entity_status="ACTIVE" if item.get("registrationDate") else "INACTIVE",
            industry_code=item.get("businessLine"),
            incorporation_date=item.get("registrationDate"),
            source="PRH_FIN",
            source_record_id=item.get("businessId"),
        ))
        return records, int(data.get("totalResults") or 0)

    if task_type == "legalEntity.registry.collectEst":
        data = await get_json("https://avaandmed.rik.ee/andmed/ARIREGISTER/ettevotjad", params={"limit": page_size, "offset": page * page_size})
        items = data if isinstance(data, list) else data.get("data") or []
        records = collect_records(items, lambda item: entity_to_record(
            name=item.get("nimi") or item.get("arinimi"),
            registration_number=item.get("ariregistri_kood") or item.get("registrikood"),
            jurisdiction="EE",
            country="EE",
            entity_type=item.get("oiguslik_vorm") or variables.get("legalForm"),
            entity_status="ACTIVE" if item.get("staatus") == "R" else item.get("staatus") or "ACTIVE",
            industry_code=item.get("emtak_kood"),
            incorporation_date=item.get("registreerimise_kpv"),
            source="ARIK_EST",
            source_record_id=item.get("ariregistri_kood") or item.get("registrikood"),
        ))
        return records, len(records)

    if task_type == "legalEntity.registry.collectCze":
        data = await post_json(
            "https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty/vyhledat",
            {"start": page * page_size, "pocet": page_size, "obpiPlatnostOd": "2000-01-01"},
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        records = collect_records(data.get("ekonomickeSubjekty") or [], lambda item: entity_to_record(
            name=item.get("obchodniJmeno"),
            registration_number=item.get("ico"),
            jurisdiction="CZ",
            country="CZ",
            entity_type=item.get("pravniForma") or variables.get("pravniForma"),
            entity_status="ACTIVE",
            industry_code=(item.get("czNace") or [""])[0],
            incorporation_date=item.get("datumVzniku"),
            source="ARES_CZE",
            source_record_id=item.get("ico"),
        ))
        return records, int(data.get("pocetCelkem") or 0)

    if task_type == "legalEntity.registry.collectNzl":
        data = await get_json("https://api.business.govt.nz/gateway/nzbn/v5/entities", params={
            "page-size": page_size,
            "page-number": page,
            "entity-status": clean(variables.get("entityStatus") or "Registered"),
            "search-type": "all",
        })
        records = collect_records(data.get("items") or [], lambda item: entity_to_record(
            name=item.get("entityName"),
            registration_number=item.get("nzbn"),
            jurisdiction="NZ",
            country="NZ",
            entity_type=item.get("entityTypeDescription") or variables.get("entityType"),
            entity_status=item.get("entityStatusDescription") or "Registered",
            industry_code=item.get("industryClassificationCode"),
            incorporation_date=item.get("registrationDate"),
            source="MBIE_NZL",
            source_record_id=item.get("nzbn"),
        ))
        return records, int(data.get("totalRecords") or 0)

    if task_type == "legalEntity.registry.collectChe":
        data = await post_json("https://www.zefix.admin.ch/ZefixREST/api/v1/company/search", {
            "offset": page * page_size,
            "maxEntries": page_size,
            "activeOnly": variables.get("activeOnly") is not False,
            **({"registryOffice": clean(variables.get("canton"))} if variables.get("canton") else {}),
        }, headers={"Content-Type": "application/json", "Accept": "application/json"})
        records = collect_records(data if isinstance(data, list) else [], lambda item: entity_to_record(
            name=item.get("name"),
            registration_number=item.get("uid") or item.get("chid"),
            jurisdiction=f"CH-{clean(item.get('canton'))}",
            country="CH",
            entity_type=item.get("legalFormId") or variables.get("legalForm"),
            entity_status=item.get("status") or "ACTIVE",
            industry_code=clean(item.get("purpose"))[:10],
            incorporation_date=item.get("registrationDate"),
            source="ZEFIX_CHE",
            source_record_id=item.get("uid") or item.get("chid"),
        ))
        return records, len(records)

    if task_type == "legalEntity.registry.collectNld":
        data = await get_json("https://api.kvk.nl/api/v1/zoeken", params={"pagina": page + 1, "resultatenPerPagina": page_size})
        records = collect_records(data.get("resultaten") or [], lambda item: entity_to_record(
            name=item.get("handelsnaam"),
            registration_number=item.get("kvkNummer"),
            jurisdiction="NL",
            country="NL",
            entity_type=item.get("type"),
            entity_status="ACTIVE",
            industry_code=((item.get("sbiActiviteiten") or [{}])[0]).get("sbiCode"),
            source="KVK_NLD",
            source_record_id=item.get("kvkNummer"),
        ))
        return records, int(data.get("totaal") or 0)

    if task_type == "legalEntity.registry.collectIsr":
        data = await get_json("https://data.gov.il/api/3/action/datastore_search", params={
            "resource_id": "f004176c-b85f-4542-8901-7b3176f9a054",
            "limit": page_size,
            "offset": page * page_size,
        })
        result = data.get("result") or {}
        records = collect_records(result.get("records") or [], lambda item: entity_to_record(
            name=item.get("company_name") or item.get("company_name_eng"),
            registration_number=item.get("company_number"),
            jurisdiction="IL",
            country="IL",
            entity_type=item.get("company_type") or variables.get("companyType"),
            entity_status="ACTIVE" if item.get("company_status") == "active" else item.get("company_status") or variables.get("status") or "ACTIVE",
            incorporation_date=item.get("incorporation_date"),
            source="RASHAM_ISR",
            source_record_id=item.get("company_number"),
        ))
        return records, int(result.get("total") or 0)

    raise ValueError(f"unknown country registry task type: {task_type}")


async def collect_country_registry(task_type: str, **variables: Any) -> dict[str, Any]:
    source = COUNTRY_TASK_SOURCES[task_type]
    pages = max(1, min(int(variables.get("pages") or 5), 50))
    default_page_size = 500 if task_type == "legalEntity.registry.collectJpn" else 100
    page_size_max = 1000 if task_type in {"legalEntity.registry.collectFra", "legalEntity.registry.collectDnk"} else default_page_size
    page_size = max(1, min(int(variables.get("pageSize") or default_page_size), page_size_max))
    start_page = int(variables.get("startPage") or 0)
    if task_type == "legalEntity.registry.collectJpn":
        start_page = max(1, start_page or 1)
    total_inserted = 0
    total_skipped = 0
    api_total = 0
    first_error = ""
    page_results: list[dict[str, Any]] = []
    for page in range(start_page, start_page + pages):
        try:
            records, page_total = await fetch_country_registry_page(task_type, page, page_size, variables)
            api_total = page_total or api_total
            if not records:
                break
            commit = await commit_entities(source, page, records)
            total_inserted += int(commit.get("inserted") or 0)
            total_skipped += int(commit.get("skipped") or 0)
            if not first_error and commit.get("firstError"):
                first_error = str(commit.get("firstError"))[:300]
            page_results.append({"page": page, "ok": bool(commit.get("ok")), "submitted": len(records), "inserted": commit.get("inserted"), "skipped": commit.get("skipped")})
        except Exception as exc:  # noqa: BLE001
            LOG.exception("country registry page failed task=%s page=%s", task_type, page)
            first_error = first_error or str(exc)[:300]
            page_results.append({"page": page, "ok": False, "error": str(exc)})
            break
    return result_payload(source, pages, page_size, start_page, total_inserted, total_skipped, api_total, first_error, page_results)


async def fetch_pages(pages: int = 5, pageSize: int = 200, startPage: int = 1, **_: Any) -> dict[str, Any]:
    pages = max(1, min(int(pages or 5), 50))
    page_size = max(1, min(int(pageSize or 200), 200))
    start_page = max(1, int(startPage or 1))
    total_inserted = 0
    total_skipped = 0
    api_total = 0
    first_error = ""
    results: list[dict[str, Any]] = []
    for page in range(start_page, start_page + pages):
        try:
            data = await fetch_gleif_page(page, page_size)
            api_total = int(((data.get("meta") or {}).get("pagination") or {}).get("total") or api_total or 0)
            records = [gleif_to_record(item) for item in data.get("data") or []]
            if not records:
                break
            commit = await commit_entities("GLEIF", page, records)
            total_inserted += int(commit.get("inserted") or 0)
            total_skipped += int(commit.get("skipped") or 0)
            results.append({"page": page, "ok": bool(commit.get("ok")), "inserted": commit.get("inserted"), "skipped": commit.get("skipped")})
        except Exception as exc:  # noqa: BLE001
            LOG.exception("GLEIF page failed page=%s", page)
            if not first_error:
                first_error = str(exc)[:300]
            results.append({"page": page, "ok": False, "error": str(exc)})
            break
    return {"result": {"ok": not first_error, "source": "GLEIF", "pagesProcessed": len(results), "pageSize": page_size, "startPage": start_page, "totalInserted": total_inserted, "totalSkipped": total_skipped, "apiTotal": api_total, "firstError": first_error, "pages": results, "ts": now_iso()}}


async def collect_usa(pages: int = 5, pageSize: int = 100, startPage: int = 0, **_: Any) -> dict[str, Any]:
    pages = max(1, min(int(pages or 5), 50))
    page_size = max(1, min(int(pageSize or 100), 100))
    start_page = max(0, int(startPage or 0))
    total_inserted = 0
    total_skipped = 0
    api_total = 0
    first_error = ""
    results: list[dict[str, Any]] = []
    try:
        data = await fetch_sec_tickers()
        entries = list(data.values())
        api_total = len(entries)
        offset = start_page * page_size
        end = min(offset + pages * page_size, len(entries))
        records = [edgar_to_record(item) for item in entries[offset:end] if isinstance(item, dict)]
        for index in range(0, len(records), 200):
            chunk = records[index : index + 200]
            page = start_page + (index // page_size)
            commit = await commit_entities("EDGAR_USA", page, chunk)
            total_inserted += int(commit.get("inserted") or 0)
            total_skipped += int(commit.get("skipped") or 0)
            if not first_error and commit.get("firstError"):
                first_error = str(commit.get("firstError"))[:300]
            results.append({"page": page, "ok": bool(commit.get("ok")), "submitted": len(chunk), "inserted": commit.get("inserted"), "skipped": commit.get("skipped")})
    except Exception as exc:  # noqa: BLE001
        LOG.exception("EDGAR USA collection failed")
        first_error = str(exc)[:300]
    return {"result": {"ok": not first_error, "source": "EDGAR_USA", "pagesProcessed": len(results), "pageSize": page_size, "startPage": start_page, "totalInserted": total_inserted, "totalSkipped": total_skipped, "apiTotal": api_total, "firstError": first_error, "pages": results, "ts": now_iso()}}


async def ingest_sec_disclosure(ticker: str = "", cik: str = "", filingLimit: int = 20, factsLimit: int = 50, **_: Any) -> dict[str, Any]:
    filing_limit = max(1, min(int(filingLimit or 20), 100))
    facts_limit = max(1, min(int(factsLimit or 50), 200))
    first_error = ""
    commit: dict[str, Any] = {}
    normalized_cik = ""
    normalized_ticker = clean(ticker).upper()
    company_did = ""
    filings: list[dict[str, Any]] = []
    facts: list[dict[str, Any]] = []
    try:
        normalized_cik, normalized_ticker = await resolve_sec_cik(normalized_ticker, cik)
        submissions = await fetch_sec_json(f"https://data.sec.gov/submissions/CIK{normalized_cik}.json")
        company_facts = await fetch_sec_json(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{normalized_cik}.json")
        company_did = f"le:edgar_usa:{normalized_cik}"
        filings = build_recent_filing_records(submissions, company_did, normalized_cik, filing_limit)
        facts = build_company_fact_records(company_facts, company_did, normalized_cik, facts_limit)
        if not normalized_ticker:
            tickers = submissions.get("tickers") if isinstance(submissions.get("tickers"), list) else []
            normalized_ticker = clean(tickers[0] if tickers else "")
        commit = await commit_sec_disclosure(normalized_cik, normalized_ticker, company_did, filings, facts)
        if commit.get("firstError"):
            first_error = clean(commit.get("firstError"))[:300]
    except Exception as exc:  # noqa: BLE001
        LOG.exception("SEC disclosure ingest failed ticker=%s cik=%s", ticker, cik)
        first_error = str(exc)[:300]
    return {"result": {"ok": not first_error, "source": "SEC_EDGAR", "cik": normalized_cik, "ticker": normalized_ticker, "companyDid": company_did, "filingsBuilt": len(filings), "factsBuilt": len(facts), "filingsInserted": commit.get("filingsInserted", 0), "factsInserted": commit.get("factsInserted", 0), "filingsSkipped": commit.get("filingsSkipped", 0), "factsSkipped": commit.get("factsSkipped", 0), "firstError": first_error, "ts": now_iso()}}


async def register_dids(pages: int = 1, pageSize: int = 200, startPage: int = 1, **_: Any) -> dict[str, Any]:
    pages = max(1, min(int(pages or 1), 50))
    page_size = max(1, min(int(pageSize or 200), 200))
    start_page = max(1, int(startPage or 1))
    total_registered = 0
    total_skipped = 0
    total_errors = 0
    api_total = 0
    first_error = ""
    results: list[dict[str, Any]] = []
    for page in range(start_page, start_page + pages):
        try:
            data = await fetch_gleif_page(page, page_size)
            api_total = int(((data.get("meta") or {}).get("pagination") or {}).get("total") or api_total or 0)
            dids = [did for item in data.get("data") or [] if (did := gleif_to_did(item))]
            if not dids:
                break
            commit = await commit_entity_dids("GLEIF", page, dids)
            total_registered += int(commit.get("totalRegistered") or 0)
            total_skipped += int(commit.get("totalSkipped") or 0)
            total_errors += int(commit.get("totalErrors") or 0)
            if not first_error and commit.get("firstError"):
                first_error = str(commit.get("firstError"))[:300]
            results.append({"page": page, "ok": bool(commit.get("ok")), "submitted": len(dids), "registered": commit.get("totalRegistered"), "skipped": commit.get("totalSkipped"), "errors": commit.get("totalErrors")})
        except Exception as exc:  # noqa: BLE001
            LOG.exception("GLEIF DID page failed page=%s", page)
            total_errors += 1
            if not first_error:
                first_error = str(exc)[:300]
            results.append({"page": page, "ok": False, "error": str(exc)})
            break
    return {"result": {"ok": not first_error and total_errors == 0, "source": "GLEIF", "pagesProcessed": len(results), "pageSize": page_size, "startPage": start_page, "totalRegistered": total_registered, "totalSkipped": total_skipped, "totalErrors": total_errors, "apiTotal": api_total, "firstError": first_error, "pages": results, "ts": now_iso()}}


app = FastAPI(title="legal-entity-collector-actor", version="1.0.0")


@app.get("/healthz")
async def healthz() -> dict[str, Any]:
    return {"ok": True, "runtimeKind": "k8s-langserver", "agentGatewayMcpUrl": AGENTGATEWAY_MCP_URL, "tools": sorted(TOOLS)}


@app.get("/tools")
async def tools() -> dict[str, Any]:
    return {"tools": [{"name": name, "runtime": "langserver"} for name in sorted(TOOLS)]}


async def _invoke_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if name == "legalEntity.gleif.fetchPages":
        return await fetch_pages(**arguments)
    if name == "legalEntity.edgar.collectUsa":
        return await collect_usa(**arguments)
    if name == "legalEntity.edgar.ingestSecDisclosure":
        return await ingest_sec_disclosure(**arguments)
    if name == "legalEntity.gleif.registerDids":
        return await register_dids(**arguments)
    if name in COUNTRY_TASK_SOURCES:
        return await collect_country_registry(name, **arguments)
    raise HTTPException(status_code=404, detail=f"unknown tool: {name}")


@app.post("/invoke")
async def invoke(payload: dict[str, Any]) -> dict[str, Any]:
    name = str(payload.get("name") or payload.get("tool") or "")
    arguments = payload.get("arguments") or payload.get("input") or {}
    if not isinstance(arguments, dict):
        raise HTTPException(status_code=400, detail="arguments must be an object")
    return {"ok": True, "name": name, "result": await _invoke_tool(name, arguments)}


@app.post("/runs")
async def runs(payload: dict[str, Any]) -> dict[str, Any]:
    assistant_id = str(payload.get("assistant_id") or "")
    arguments = payload.get("input") or payload.get("arguments") or {}
    if not isinstance(arguments, dict):
        raise HTTPException(status_code=400, detail="input must be an object")
    return {"status": "completed", "assistant_id": assistant_id, "output": await _invoke_tool(assistant_id, arguments)}


if __name__ == "__main__":
    configure_logging()
    LOG.info("legal-entity-collector starting, runtime=k8s-langserver, agentgateway_mcp_url=%s", AGENTGATEWAY_MCP_URL)
    uvicorn.run(app, host="0.0.0.0", port=PORT)
