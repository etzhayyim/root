"""scrape_police_stations.py — Phase 0 skeleton (DRY-RUN by default).

Per-prefecture parsers are intentionally NOT implemented. Each prefecture's
HP layout differs; mis-parsing is worse than missing data. Implement parsers
incrementally after Kunal review of the pilot prefecture (神奈川).

Usage (dry-run):
    python -m pymagatama.malak.surveillance.ingest.scrape_police_stations \
        --mode dry-run \
        --prefectural-police-path prefectural-police:kanagawa

Usage (live, post-legal-clearance):
    python -m pymagatama.malak.surveillance.ingest.scrape_police_stations \
        --mode apply --legal-approved-token <UUID> \
        --prefectural-police-path prefectural-police:kanagawa
"""

from __future__ import annotations

import argparse
import csv
import logging
import pathlib
from typing import Optional

from . import _common

logger = logging.getLogger(__name__)


def load_prefectural_urls(csv_path: str) -> list[dict]:
    p = pathlib.Path(csv_path)
    if not p.exists():
        logger.warning("prefectural-police-urls.csv not found at %s; returning empty list", p)
        return []
    with p.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def scrape_one_prefecture(
    path: str,
    base_url: str,
    index_path: str,
    policy: _common.FetchPolicy,
    audit_log_dir: str,
) -> list[_common.PoliceStationRow]:
    parser = _common.get_station_parser(path)
    if parser is None:
        logger.warning("no parser registered for %s; skipping (Phase 0 stub)", path)
        _common.emit_audit({"event": "skip_no_parser", "target": path}, audit_log_dir)
        return []
    client = _common.RateLimitedClient(base_url, policy)
    _common.emit_audit({"event": "scrape_start", "target": path, "base_url": base_url}, audit_log_dir)
    html = client.get(index_path).text
    _common.assert_no_pii(html, f"{path} index page")
    rows = parser(html, base_url)
    for r in rows:
        # Each row's stringified fields must not contain PII patterns
        full_text = " ".join(str(getattr(r, k, "") or "") for k in r.__dataclass_fields__)
        _common.assert_no_pii(full_text, f"{path} row {r.path}")
    _common.emit_audit({"event": "scrape_end", "target": path, "rows": len(rows)}, audit_log_dir)
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description="malak.surveillance police station scraper (Phase 0 skeleton)")
    ap.add_argument("--mode", choices=["dry-run", "preview", "apply"], default="dry-run")
    ap.add_argument("--legal-approved-token", default=None)
    ap.add_argument(
        "--prefectural-police-path",
        default=None,
        help="path like 'prefectural-police:kanagawa'; if omitted, all 47",
    )
    ap.add_argument("--urls-csv", default="_working/malak/surveillance/ingest/prefectural-police-urls.csv")
    ap.add_argument("--out-dir", default="_working/malak/surveillance/ingest/out")
    ap.add_argument("--audit-log-dir", default="_working/malak/surveillance/ingest/audit")
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    policy = _common.FetchPolicy(
        mode=args.mode,
        apply_token=args.legal_approved_token,
    )
    _common.assert_dry_run_or_approved(policy)

    targets = load_prefectural_urls(args.urls_csv)
    if args.prefectural_police_path:
        targets = [t for t in targets if t.get("path") == args.prefectural_police_path]
    if not targets:
        logger.error("no targets matched; check --prefectural-police-path / --urls-csv")
        return 1

    all_rows: list[_common.PoliceStationRow] = []
    for t in targets:
        try:
            rows = scrape_one_prefecture(
                t["path"],
                t["base_url"],
                t.get("station_index", "/"),
                policy,
                args.audit_log_dir,
            )
            all_rows.extend(rows)
        except _common.RobotsViolationError as e:
            logger.error("robots violation for %s: %s; skipping prefecture", t["path"], e)
            _common.emit_audit({"event": "robots_violation", "target": t["path"], "error": str(e)}, args.audit_log_dir)
        except _common.PIIDetectedError as e:
            logger.error("PII detected for %s: %s; ABORTING entire run", t["path"], e)
            _common.emit_audit({"event": "pii_detected_abort", "target": t["path"], "error": str(e)}, args.audit_log_dir)
            return 2
        except _common.OutsideBusinessHoursError as e:
            logger.error("outside business hours: %s; aborting", e)
            _common.emit_audit({"event": "outside_business_hours_abort", "error": str(e)}, args.audit_log_dir)
            return 3

    out_path = f"{args.out_dir}/police_stations.ndjson"
    _common.emit_dry_run_json(all_rows, out_path)

    if args.mode == "apply":
        logger.error(
            "apply mode dry-run path complete; actual INSERT not implemented in Phase 0"
        )
        return 4

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
