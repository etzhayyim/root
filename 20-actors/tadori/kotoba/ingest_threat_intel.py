#!/usr/bin/env python3
"""tadori threat-intel -> kotoba Datomic API.

Reads operator-staged JSONL observations (SecurityTrails/DNSDB/Recorded Future
shaped, but never fetched live here), validates the tadori gates, converts them
to Datomic tx-data EDN, and writes through:

    POST /xrpc/com.etzhayyim.apps.kotoba.datomic.transact

Live writes require an operator credential in KOTOBA_SESSION_POP or KOTOBA_TOKEN.
KOTOBA_SESSION_POP is verified with com.etzhayyim.pds.session.verify before transact.
Without a credential the command is a dry run and prints the tx_edn summary.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any

HERE = os.path.dirname(__file__)
DEFAULT_SEED = os.path.join(HERE, "seed.threat-intel.jsonl")
DEFAULT_SCHEMA = os.path.join(HERE, "schema.edn")

NSID_SESSION_VERIFY = "com.etzhayyim.pds.session.verify"
NSID_DATOMIC_TRANSACT = "com.etzhayyim.apps.kotoba.datomic.transact"
NSID_DATOMIC_DATOMS = "com.etzhayyim.apps.kotoba.datomic.datoms"

VENDOR_COMPAT = {
    "securitytrails-compatible",
    "dnsdb-compatible",
    "recordedfuture-compatible",
}
VALID_KINDS = {"intel-source", "dns-obs", "ip-obs", "indicator"}
VALID_LICENSE_TIERS = {"A", "B", "C", "D"}


class ValidationError(ValueError):
    pass


def edn_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def edn_keyword(value: str) -> str:
    token = value.strip().replace("_", "-")
    if not token:
        raise ValidationError("empty keyword value")
    if token.startswith(":"):
        return token
    return f":{token}"


def edn_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        return edn_string(value)
    raise ValidationError(f"unsupported EDN value {value!r}")


def source_lookup_ref(source_id: str) -> str:
    return f"[:tadori.source/id {edn_string(source_id)}]"


def add(datoms: list[str], entity: str, attr: str, value: Any, *, keyword: bool = False) -> None:
    if value is None:
        return
    values = value if isinstance(value, list) else [value]
    for item in values:
        if item is None:
            continue
        rendered = edn_keyword(str(item)) if keyword else edn_value(item)
        datoms.append(f"[:db/add {edn_string(entity)} :{attr} {rendered}]")


def add_raw(datoms: list[str], entity: str, attr: str, value_edn: str | None) -> None:
    if value_edn is None:
        return
    datoms.append(f"[:db/add {edn_string(entity)} :{attr} {value_edn}]")


def load_jsonl(path: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with open(path, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValidationError(f"{path}:{lineno}: JSON parse error: {exc}") from exc
            if not isinstance(rec, dict):
                raise ValidationError(f"{path}:{lineno}: expected JSON object")
            rec["_lineno"] = lineno
            records.append(rec)
    return records


def require(rec: dict[str, Any], *fields: str) -> None:
    missing = [f for f in fields if rec.get(f) in (None, "")]
    if missing:
        raise ValidationError(f"line {rec.get('_lineno')}: missing required fields: {', '.join(missing)}")


def validate_records(records: list[dict[str, Any]], *, allow_tier_d: bool, live: bool, case_id: str | None) -> None:
    source_ids: set[str] = set()
    for rec in records:
        kind = rec.get("kind")
        if kind not in VALID_KINDS:
            raise ValidationError(f"line {rec.get('_lineno')}: invalid kind {kind!r}")
        require(rec, "id")

        if kind == "intel-source":
            require(rec, "name", "vendor_family", "source_role", "license_tier")
            source_ids.add(str(rec["id"]))
            tier = str(rec["license_tier"])
            if tier not in VALID_LICENSE_TIERS:
                raise ValidationError(f"line {rec.get('_lineno')}: invalid license_tier {tier!r}")
            if tier == "D" and not allow_tier_d:
                raise ValidationError(
                    f"line {rec.get('_lineno')}: Tier-D source requires --allow-tier-d and remains non-SoR"
                )
            if str(rec["vendor_family"]) in VENDOR_COMPAT and rec.get("source_role") == "system-of-record":
                raise ValidationError(
                    f"line {rec.get('_lineno')}: vendor-compatible source cannot be system-of-record"
                )
            continue

        require(rec, "source", "collection_mode")
        if live and not (case_id or rec.get("case_id")):
            raise ValidationError(f"line {rec.get('_lineno')}: live write requires case_id")
        if rec.get("collection_mode") != "operator-staged-passive-archive":
            raise ValidationError(
                f"line {rec.get('_lineno')}: collection_mode must be operator-staged-passive-archive"
            )
        if rec.get("confidence") is not None:
            conf = int(rec["confidence"])
            if conf < 0 or conf > 1000:
                raise ValidationError(f"line {rec.get('_lineno')}: confidence must be 0..1000")

        if kind == "dns-obs":
            require(rec, "domain", "rrtype", "rrdata")
        elif kind == "ip-obs":
            require(rec, "address")
        elif kind == "indicator":
            require(rec, "indicator_type", "value", "status")

    missing_sources = [
        str(rec["source"])
        for rec in records
        if rec.get("kind") != "intel-source" and str(rec.get("source")) not in source_ids
    ]
    if missing_sources:
        raise ValidationError(f"observation references undeclared source(s): {', '.join(sorted(set(missing_sources)))}")


def record_to_datoms(rec: dict[str, Any], *, case_id: str | None) -> list[str]:
    datoms: list[str] = []
    kind = str(rec["kind"])
    entity = str(rec["id"])

    if kind == "intel-source":
        add(datoms, entity, "tadori.source/id", entity)
        add(datoms, entity, "tadori.source/name", rec.get("name"))
        add(datoms, entity, "tadori.source/vendor-family", rec.get("vendor_family"), keyword=True)
        add(datoms, entity, "tadori.source/source-role", rec.get("source_role"), keyword=True)
        add(datoms, entity, "tadori.source/license-tier", rec.get("license_tier"), keyword=True)
        add(datoms, entity, "tadori.source/dataset-cid", rec.get("dataset_cid"))
        add(datoms, entity, "tadori.source/captured-at", rec.get("captured_at"))
        add(datoms, entity, "tadori.source/notes", rec.get("notes"))
        return datoms

    add(datoms, entity, "tadori.obs/id", entity)
    add(datoms, entity, "tadori.obs/kind", kind, keyword=True)
    add_raw(datoms, entity, "tadori.obs/source", source_lookup_ref(str(rec["source"])))
    add(datoms, entity, "tadori.obs/case-id", case_id or rec.get("case_id"))
    add(datoms, entity, "tadori.obs/observed-at", rec.get("observed_at"))
    add(datoms, entity, "tadori.obs/first-seen-at", rec.get("first_seen_at"))
    add(datoms, entity, "tadori.obs/last-seen-at", rec.get("last_seen_at"))
    add(datoms, entity, "tadori.obs/confidence", rec.get("confidence"))
    add(datoms, entity, "tadori.obs/tlp", rec.get("tlp"), keyword=True)
    add(datoms, entity, "tadori.obs/evidence-cid", rec.get("evidence_cid"))
    add(datoms, entity, "tadori.obs/encrypted", rec.get("encrypted"))
    add(datoms, entity, "tadori.obs/collection-mode", rec.get("collection_mode"), keyword=True)

    if kind == "dns-obs":
        add(datoms, entity, "tadori.dns/domain", rec.get("domain"))
        add(datoms, entity, "tadori.dns/rrtype", rec.get("rrtype"), keyword=True)
        add(datoms, entity, "tadori.dns/rrdata", rec.get("rrdata"))
        add(datoms, entity, "tadori.dns/passive-pivot", rec.get("passive_pivot"), keyword=True)
    elif kind == "ip-obs":
        add(datoms, entity, "tadori.ip/address", rec.get("address"))
        add(datoms, entity, "tadori.ip/asn", rec.get("asn"))
        add(datoms, entity, "tadori.ip/prefix", rec.get("prefix"))
        add(datoms, entity, "tadori.ip/geo", rec.get("geo"))
        add(datoms, entity, "tadori.ip/hosting-class", rec.get("hosting_class"), keyword=True)
    elif kind == "indicator":
        add(datoms, entity, "tadori.indicator/id", entity)
        add(datoms, entity, "tadori.indicator/type", rec.get("indicator_type"), keyword=True)
        add(datoms, entity, "tadori.indicator/value", rec.get("value"))
        add(datoms, entity, "tadori.indicator/status", rec.get("status"), keyword=True)
        add(datoms, entity, "tadori.indicator/context", rec.get("context"))
    return datoms


def datoms_to_tx_edn(datoms: list[str]) -> str:
    if not datoms:
        return "[]"
    return "[\n  " + "\n  ".join(datoms) + "\n]"


def _post(url: str, body: dict[str, Any], token: str | None = None) -> tuple[int, dict[str, Any]]:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8") or "{}"
            return resp.status, json.loads(raw)
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8") or "{}"
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = {"error": raw}
        return exc.code, payload


def verify_session(base_url: str, pop_token: str) -> tuple[bool, dict[str, Any]]:
    status, body = _post(f"{base_url}/xrpc/{NSID_SESSION_VERIFY}", {"token": pop_token})
    return status == 200 and bool(body.get("valid")), body


def transact(base_url: str, graph: str, tx_edn: str, token: str) -> tuple[int, dict[str, Any]]:
    return _post(f"{base_url}/xrpc/{NSID_DATOMIC_TRANSACT}", {"graph": graph, "tx_edn": tx_edn}, token)


def read_datoms(base_url: str, graph: str, entity: str, attr: str, token: str) -> tuple[int, dict[str, Any]]:
    return _post(
        f"{base_url}/xrpc/{NSID_DATOMIC_DATOMS}",
        {
            "graph": graph,
            "index": ":eavt",
            "components_edn": [edn_string(entity), f":{attr}"],
            "limit": 1,
        },
        token,
    )


def readback_checks(records: list[dict[str, Any]]) -> list[tuple[str, str]]:
    checks: list[tuple[str, str]] = []
    for rec in records:
        kind = rec.get("kind")
        if kind == "intel-source":
            checks.append((str(rec["id"]), "tadori.source/id"))
        elif kind == "dns-obs":
            checks.append((str(rec["id"]), "tadori.dns/domain"))
        elif kind == "ip-obs":
            checks.append((str(rec["id"]), "tadori.ip/address"))
        elif kind == "indicator":
            checks.append((str(rec["id"]), "tadori.indicator/value"))
    return checks


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default=os.environ.get("KOTOBA_URL", "http://127.0.0.1:8077"))
    ap.add_argument("--graph", default=os.environ.get("TADORI_GRAPH", "etzhayyim/tadori/threat-intel"))
    ap.add_argument("--input", default=DEFAULT_SEED)
    ap.add_argument("--schema", default=DEFAULT_SCHEMA)
    ap.add_argument("--case-id", default=os.environ.get("TADORI_CASE_ID"))
    ap.add_argument("--schema-only", action="store_true")
    ap.add_argument("--data-only", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--verify-readback", action="store_true")
    ap.add_argument("--allow-tier-d", action="store_true")
    args = ap.parse_args()

    if args.schema_only and args.data_only:
        print("!! --schema-only and --data-only are mutually exclusive", file=sys.stderr)
        return 2

    token = os.environ.get("KOTOBA_SESSION_POP") or os.environ.get("KOTOBA_TOKEN")
    live = bool(token) and not args.dry_run

    txs: list[tuple[str, str, int]] = []
    records: list[dict[str, Any]] = []
    if not args.data_only:
        with open(args.schema, encoding="utf-8") as f:
            schema_edn = f.read()
        txs.append(("schema", schema_edn, schema_edn.count(":db/ident")))

    if not args.schema_only:
        records = load_jsonl(args.input)
        validate_records(records, allow_tier_d=args.allow_tier_d, live=live, case_id=args.case_id)
        datoms: list[str] = []
        for rec in records:
            datoms.extend(record_to_datoms(rec, case_id=args.case_id))
        txs.append(("data", datoms_to_tx_edn(datoms), len(datoms)))
        print(f"   parsed {len(records)} records -> {len(datoms)} datoms from {args.input}")

    if not live:
        print("   DRY RUN - no writes. Set KOTOBA_SESSION_POP or KOTOBA_TOKEN to transact.")
        for name, tx_edn, count in txs:
            print(f"   tx[{name}] count~{count} bytes={len(tx_edn.encode('utf-8'))}")
        return 0

    if os.environ.get("KOTOBA_SESSION_POP"):
        ok, info = verify_session(args.url, os.environ["KOTOBA_SESSION_POP"])
        if not ok:
            print(f"!! session PoP rejected: {info}", file=sys.stderr)
            return 1
        print(f"   session valid for {info.get('did', '?')}")

    for name, tx_edn, count in txs:
        print(f"--> datomic.transact {name} count~{count} graph={args.graph}")
        status, body = transact(args.url, args.graph, tx_edn, token)
        if status != 200:
            print(f"!! transact failed for {name}: {status} {body}", file=sys.stderr)
            return 1
        print(
            f"    ok tx_cid={body.get('tx_cid', '?')} commit_cid={body.get('commit_cid', '?')} "
            f"datom_count={body.get('datom_count', '?')}"
        )

    if args.verify_readback and not args.schema_only:
        checks = readback_checks(records)
        for entity, attr in checks:
            status, body = read_datoms(args.url, args.graph, entity, attr, token)
            if status != 200:
                print(f"!! readback failed for {entity} {attr}: {status} {body}", file=sys.stderr)
                return 1
            if int(body.get("datom_count", 0)) < 1:
                print(f"!! readback missing datom for {entity} {attr}: {body}", file=sys.stderr)
                return 1
        print(f"    readback ok checks={len(checks)} graph={args.graph}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ValidationError as exc:
        print(f"!! validation failed: {exc}", file=sys.stderr)
        sys.exit(1)
