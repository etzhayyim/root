#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# License Rider: see /CHARTER-RIDER.md

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any


def parse_path(path: str) -> tuple[str, str]:
    """Parse path like 'country:jpn:moj' or 'country:jpn:cabinet-office' -> (jurisdiction, slug)."""
    parts = path.split(':')
    if len(parts) < 3:
        raise ValueError(f"Invalid path format: {path}")
    jurisdiction = parts[1]
    slug = ':'.join(parts[2:])
    return jurisdiction, slug


def clean_name(display_name: str) -> str:
    """Drop the (JP) suffix from displayName."""
    return display_name.replace(' (JP)', '').strip()


def emit_agency_record(
    name: str,
    jurisdiction: str,
    slug: str,
    created_at: str,
) -> dict[str, Any]:
    """Build a single com.etzhayyim.gov.agency record."""
    return {
        'name': name,
        'jurisdiction': jurisdiction,
        'branch': 'executive',
        'level': 'national',
        'agencyDid': f'did:web:etzhayyim.com:gov:{jurisdiction}:{slug}',
        'createdAt': created_at,
        'updatedAt': created_at,
    }


def ingest_roster(roster_path: Path, created_at: str) -> list[dict[str, Any]]:
    """Read actor-manifest.jsonld and emit agency records."""
    with open(roster_path, 'r') as f:
        data = json.load(f)

    records = []
    for actor in data.get('actors', []):
        display_name = actor.get('displayName', '')
        path = actor.get('path', '')

        if not display_name or not path:
            continue

        jurisdiction, slug = parse_path(path)
        name = clean_name(display_name)

        record = emit_agency_record(name, jurisdiction, slug, created_at)
        records.append(record)

    return records


def main():
    parser = argparse.ArgumentParser(
        description='Ingest Japanese ministries roster to com.etzhayyim.gov.agency Lexicon.'
    )
    parser.add_argument(
        '--roster',
        type=Path,
        default=Path('/Users/junkawasaki/github/etzhayyim-root/60-apps/etzhayyim-project-gov/scaffold/actor-manifest.jsonld'),
        help='Path to actor-manifest.jsonld',
    )
    parser.add_argument(
        '--out',
        type=Path,
        default=None,
        help='Output path (file or directory). If directory, writes timestamped file.',
    )
    args = parser.parse_args()

    now_utc = dt.datetime.now(dt.timezone.utc)
    created_at = now_utc.strftime('%Y-%m-%dT%H:%M:%SZ')

    records = ingest_roster(args.roster, created_at)

    output_lines = [json.dumps(rec, separators=(',', ':')) for rec in records]

    if args.out is None:
        for line in output_lines:
            print(line)
        print(f'\n# Ingested {len(records)} Japanese government agencies', file=__import__('sys').stderr)
    else:
        if args.out.is_dir() or (not args.out.exists() and str(args.out).endswith('/')):
            timestamp = now_utc.strftime('%Y%m%dT%H%M%SZ')
            out_file = args.out / f'ingest-gov-jpn-ministries-{timestamp}.ndjson'
        else:
            out_file = args.out

        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, 'w') as f:
            for line in output_lines:
                f.write(line + '\n')

        print(f'Wrote {len(records)} records to {out_file}', file=__import__('sys').stderr)


if __name__ == '__main__':
    main()
