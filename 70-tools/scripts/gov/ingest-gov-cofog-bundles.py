#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# License Rider: see /CHARTER-RIDER.md

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path
from typing import Any


COUNTRY_MAP = {
    'jp': 'jpn',
    'us': 'usa',
    'uk': 'gbr',
    'de': 'deu',
    'fr': 'fra',
    'cn': 'chn',
    'kr': 'kor',
    'il': 'isr',
    'in': 'ind',
    'br': 'bra',
    'ru': 'rus',
    'it': 'ita',
    'es': 'esp',
    'nl': 'nld',
    'ca': 'can',
    'au': 'aus',
    'mx': 'mex',
    'za': 'zaf',
    'sg': 'sgp',
    'tw': 'twn',
    'pl': 'pol',
    'tr': 'tur',
}


def extract_cofog_code(bundle_name: str) -> str:
    match = re.search(r'cofog-(\d{4}|\d{2}-\d)', bundle_name)
    if not match:
        return ""
    code = match.group(1)
    if '-' in code:
        return code.replace('-', '.')
    else:
        return f"{code[0:2]}.{code[2:4]}"


def extract_jurisdiction(bundle_name: str) -> str:
    match = re.search(r'-([a-z]{2})-', bundle_name)
    if match:
        country_code = match.group(1)
        return COUNTRY_MAP.get(country_code, country_code)
    return "un"


def extract_name(bundle_name: str, magatama_data: dict[str, Any]) -> str:
    if 'profile' in magatama_data and 'displayName' in magatama_data['profile']:
        return magatama_data['profile']['displayName']
    if 'name' in magatama_data:
        return magatama_data['name']
    suffix = bundle_name
    if suffix.startswith('etzhayyim-performer-sys-etzhayyim-actors-pba7d22f-svc-'):
        suffix = suffix[len('etzhayyim-performer-sys-etzhayyim-actors-pba7d22f-svc-'):]
    suffix = re.sub(r'-[a-z0-9]{8}$', '', suffix)
    return ' '.join(word.capitalize() for word in suffix.replace('-', ' ').split())


def emit_agency_record(
    name: str,
    jurisdiction: str,
    cofog: str,
    created_at: str,
) -> dict[str, Any]:
    level = "international" if jurisdiction == "un" else "national"
    cofog_slug = cofog.replace('.', '.') if cofog else ""
    agency_did = f'did:web:etzhayyim.com:gov:{jurisdiction}:cofog-{cofog_slug}' if cofog else None

    record = {
        'name': name,
        'jurisdiction': jurisdiction,
        'branch': 'executive',
        'level': level,
        'createdAt': created_at,
        'updatedAt': created_at,
    }

    if cofog:
        record['cofog'] = cofog
    if agency_did:
        record['agencyDid'] = agency_did

    return record


def process_bundle(bundle_dir: Path, created_at: str) -> dict[str, Any] | None:
    magatama_path = bundle_dir / 'magatama.jsonld'
    if not magatama_path.exists():
        return None

    try:
        with open(magatama_path, 'r') as f:
            magatama_data = json.load(f)
    except (json.JSONDecodeError, IOError):
        return None

    bundle_name = bundle_dir.name
    cofog = extract_cofog_code(bundle_name)
    jurisdiction = extract_jurisdiction(bundle_name)
    name = extract_name(bundle_name, magatama_data)

    record = emit_agency_record(name, jurisdiction, cofog, created_at)
    return record


def ingest_bundles(source_dir: Path, created_at: str) -> list[dict[str, Any]]:
    records = []
    for bundle_dir in sorted(source_dir.iterdir()):
        if bundle_dir.is_dir():
            record = process_bundle(bundle_dir, created_at)
            if record:
                records.append(record)
    return records


def main():
    parser = argparse.ArgumentParser(
        description='Ingest COFOG bundles to com.etzhayyim.gov.agency Lexicon.'
    )
    parser.add_argument(
        '--source',
        type=Path,
        default=Path('/Users/junkawasaki/github/etzhayyim-root/60-apps/etzhayyim-project-cofog/appview'),
        help='Path to COFOG appview bundles directory',
    )
    parser.add_argument(
        '--out',
        type=str,
        default=None,
        help='Output path (file or directory). If directory, writes timestamped file.',
    )
    args = parser.parse_args()

    if not args.source.is_dir():
        print(f"Error: source directory not found: {args.source}", file=sys.stderr)
        sys.exit(1)

    now_utc = dt.datetime.now(dt.timezone.utc)
    created_at = now_utc.strftime('%Y-%m-%dT%H:%M:%SZ')

    records = ingest_bundles(args.source, created_at)

    output_lines = [json.dumps(rec, separators=(',', ':'), sort_keys=True) for rec in records]

    if args.out is None:
        for line in output_lines:
            print(line)
        print(f'# Ingested {len(records)} COFOG agency records', file=sys.stderr)
    else:
        out_path = Path(args.out)
        if out_path.is_dir() or str(args.out).endswith('/'):
            timestamp = now_utc.strftime('%Y%m%dT%H%M%SZ')
            out_file = out_path / f'ingest-gov-cofog-bundles-{timestamp}.ndjson'
        else:
            out_file = out_path

        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, 'w') as f:
            for line in output_lines:
                f.write(line + '\n')

        print(f'Wrote {len(records)} records to {out_file}', file=sys.stderr)


if __name__ == '__main__':
    main()
