#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import os
import pathlib
import subprocess
import sys
import urllib.error
import urllib.request


def _methods_dir() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parents[1] / "methods"


def _load_actor() -> None:
    methods = _methods_dir()
    if str(methods) not in sys.path:
        sys.path.insert(0, str(methods))


def _jwt_for_sub(did: str) -> str:
    def b64(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")

    header = b64(b'{"alg":"HS256","typ":"JWT"}')
    payload = b64(json.dumps({"sub": did, "exp": 9999999999}, separators=(",", ":")).encode("utf-8"))
    return f"{header}.{payload}.hydrogen-electrolysis"


def _operator_did() -> str:
    out = subprocess.check_output(["kotoba", "whoami"], text=True)
    for line in out.splitlines():
        if line.startswith("DID"):
            return line.split(":", 1)[1].strip()
    raise RuntimeError("could not read operator DID from `kotoba whoami`")


def _token() -> str:
    token = os.environ.get("KOTOBA_TOKEN")
    if token:
        return token
    return _jwt_for_sub(_operator_did())


def _claim(pred: str, value: object) -> dict[str, str]:
    return {"pred": pred, "value": str(value)}


def _entities(datoms: list[dict[str, object]]) -> list[dict[str, object]]:
    entities: list[dict[str, object]] = []
    for row in datoms:
        entity_id = str(row.get(":db/id", ""))
        if not entity_id:
            continue
        if ":hydrogen.electrolysis/recommended-case" in row:
            entities.append(
                {
                    "id": entity_id,
                    "type": "HydrogenElectrolysisRecommendation",
                    "labelEn": "Hydrogen electrolysis low-temperature recommendation",
                    "confidence": "0.95",
                    "license": "CC0-1.0",
                    "sourceId": "hydrogen_electrolysis actor",
                    "claims": [
                        _claim("recommended-case", row[":hydrogen.electrolysis/recommended-case"]),
                        _claim("rationale", row[":hydrogen.electrolysis/rationale"]),
                    ],
                    "relations": [],
                }
            )
            continue

        name = str(row.get(":hydrogen.electrolysis/name", entity_id))
        entities.append(
            {
                "id": entity_id,
                "type": "HydrogenElectrolysisCase",
                "labelEn": name,
                "confidence": "0.95",
                "license": "CC0-1.0",
                "sourceId": "hydrogen_electrolysis actor",
                "claims": [
                    _claim("case-name", name),
                    _claim("actor", row.get(":hydrogen.electrolysis/actor", "")),
                    _claim("engine", row.get(":hydrogen.electrolysis/engine", "")),
                    _claim("electrical-kwh-per-kg-h2", row.get(":hydrogen.electrolysis/electrical-kwh-per-kg-h2", "")),
                    _claim("total-with-heat-kwh-per-kg-h2", row.get(":hydrogen.electrolysis/total-with-heat-kwh-per-kg-h2", "")),
                    _claim("hhv-electrical-efficiency-pct", row.get(":hydrogen.electrolysis/hhv-electrical-efficiency-pct", "")),
                    _claim("hhv-total-efficiency-pct", row.get(":hydrogen.electrolysis/hhv-total-efficiency-pct", "")),
                    _claim("h2-kg-per-hour", row.get(":hydrogen.electrolysis/h2-kg-per-hour", "")),
                    _claim("output-pressure-bar", row.get(":hydrogen.electrolysis/output-pressure-bar", "")),
                ],
                "relations": [],
            }
        )
    return entities


def _post_json(url: str, token: str, path: str, payload: dict[str, object]) -> dict[str, object]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url.rstrip("/") + path,
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{path} failed: HTTP {exc.code}: {detail}") from exc


def _delete_entities(url: str, token: str, entities: list[dict[str, object]]) -> int:
    total = 0
    for entity in entities:
        resp = _post_json(
            url,
            token,
            "/xrpc/com.etzhayyim.apps.kotobase.kg.delete",
            {"id": entity["id"]},
        )
        total += int(resp.get("retractedCount") or 0)
    return total


def _post_ingest_batch(url: str, token: str, entities: list[dict[str, object]]) -> dict[str, object]:
    return _post_json(
        url,
        token,
        "/xrpc/com.etzhayyim.apps.kotobase.kg.ingest_batch",
        {"entities": entities},
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8077")
    parser.add_argument("--graph", default="com.etzhayyim.hydrogen-electrolysis")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    _load_actor()
    from electrolysis import kotoba_datoms, run_comparison

    datoms = kotoba_datoms(run_comparison())
    entities = _entities(datoms)
    print(f"   prepared {len(entities)} hydrogen electrolysis KG entities -> {args.graph}")

    out = pathlib.Path(__file__).resolve().parent / "out"
    out.mkdir(parents=True, exist_ok=True)
    (out / "hydrogen-electrolysis-datoms.json").write_text(
        json.dumps(datoms, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (out / "hydrogen-electrolysis-kg-batch.json").write_text(
        json.dumps({"entities": entities}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    if args.dry_run:
        print("   DRY RUN - no writes.")
        return 0

    token = _token()
    if os.environ.get("KOTOBA_REPLACE") == "1":
        retracted = _delete_entities(args.url, token, entities)
        print(f"   retracted {retracted} existing quads for idempotent redeploy")
    resp = _post_ingest_batch(args.url, token, entities)
    print(f"   ingested {resp.get('entityCount')} entities / {resp.get('quadCount')} quads")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
