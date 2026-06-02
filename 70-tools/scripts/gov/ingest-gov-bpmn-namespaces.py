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

DEFAULT_SOURCE = Path('/Users/junkawasaki/github/etzhayyim-root/00-contracts/bpmn/com/etzhayyim')

DIRNAME_RE = re.compile(r'^gov([A-Z][a-z][a-z])$')

# ISO 3166-1 alpha-3 → canonical short English name.
# Source: ISO short-form where common; UN names otherwise. Covers all 196
# country namespaces present under 00-contracts/bpmn/com/etzhayyim/gov*.
ISO3_TO_NAME: dict[str, str] = {
    'afg': 'Afghanistan',
    'ago': 'Angola',
    'alb': 'Albania',
    'and': 'Andorra',
    'are': 'United Arab Emirates',
    'arg': 'Argentina',
    'arm': 'Armenia',
    'atg': 'Antigua and Barbuda',
    'aus': 'Australia',
    'aut': 'Austria',
    'aze': 'Azerbaijan',
    'bdi': 'Burundi',
    'bel': 'Belgium',
    'ben': 'Benin',
    'bfa': 'Burkina Faso',
    'bgd': 'Bangladesh',
    'bgr': 'Bulgaria',
    'bhr': 'Bahrain',
    'bhs': 'the Bahamas',
    'bih': 'Bosnia and Herzegovina',
    'blr': 'Belarus',
    'blz': 'Belize',
    'bol': 'Bolivia',
    'bra': 'Brazil',
    'brb': 'Barbados',
    'brn': 'Brunei Darussalam',
    'btn': 'Bhutan',
    'bwa': 'Botswana',
    'caf': 'the Central African Republic',
    'can': 'Canada',
    'che': 'Switzerland',
    'chl': 'Chile',
    'chn': 'China',
    'civ': "Cote d'Ivoire",
    'cmr': 'Cameroon',
    'cod': 'the Democratic Republic of the Congo',
    'cog': 'the Republic of the Congo',
    'col': 'Colombia',
    'com': 'Comoros',
    'cpv': 'Cabo Verde',
    'cri': 'Costa Rica',
    'cub': 'Cuba',
    'cyp': 'Cyprus',
    'cze': 'Czechia',
    'deu': 'Germany',
    'dji': 'Djibouti',
    'dma': 'Dominica',
    'dnk': 'Denmark',
    'dom': 'the Dominican Republic',
    'dza': 'Algeria',
    'ecu': 'Ecuador',
    'egy': 'Egypt',
    'eri': 'Eritrea',
    'esp': 'Spain',
    'est': 'Estonia',
    'eth': 'Ethiopia',
    'fin': 'Finland',
    'fji': 'Fiji',
    'fra': 'France',
    'fsm': 'the Federated States of Micronesia',
    'gab': 'Gabon',
    'gbr': 'the United Kingdom',
    'geo': 'Georgia',
    'gha': 'Ghana',
    'gin': 'Guinea',
    'gmb': 'the Gambia',
    'gnb': 'Guinea-Bissau',
    'gnq': 'Equatorial Guinea',
    'grc': 'Greece',
    'grd': 'Grenada',
    'gtm': 'Guatemala',
    'guy': 'Guyana',
    'hkg': 'Hong Kong',
    'hnd': 'Honduras',
    'hrv': 'Croatia',
    'hti': 'Haiti',
    'hun': 'Hungary',
    'idn': 'Indonesia',
    'ind': 'India',
    'irl': 'Ireland',
    'irn': 'Iran',
    'irq': 'Iraq',
    'isl': 'Iceland',
    'isr': 'Israel',
    'ita': 'Italy',
    'jam': 'Jamaica',
    'jor': 'Jordan',
    'jpn': 'Japan',
    'kaz': 'Kazakhstan',
    'ken': 'Kenya',
    'kgz': 'Kyrgyzstan',
    'khm': 'Cambodia',
    'kir': 'Kiribati',
    'kna': 'Saint Kitts and Nevis',
    'kor': 'the Republic of Korea',
    'kwt': 'Kuwait',
    'lao': "the Lao People's Democratic Republic",
    'lbn': 'Lebanon',
    'lbr': 'Liberia',
    'lby': 'Libya',
    'lca': 'Saint Lucia',
    'lie': 'Liechtenstein',
    'lka': 'Sri Lanka',
    'lso': 'Lesotho',
    'ltu': 'Lithuania',
    'lux': 'Luxembourg',
    'lva': 'Latvia',
    'mar': 'Morocco',
    'mco': 'Monaco',
    'mda': 'the Republic of Moldova',
    'mdg': 'Madagascar',
    'mdv': 'Maldives',
    'mex': 'Mexico',
    'mhl': 'the Marshall Islands',
    'mkd': 'North Macedonia',
    'mli': 'Mali',
    'mlt': 'Malta',
    'mmr': 'Myanmar',
    'mne': 'Montenegro',
    'mng': 'Mongolia',
    'moz': 'Mozambique',
    'mrt': 'Mauritania',
    'mus': 'Mauritius',
    'mwi': 'Malawi',
    'mys': 'Malaysia',
    'nam': 'Namibia',
    'ner': 'the Niger',
    'nga': 'Nigeria',
    'nic': 'Nicaragua',
    'nld': 'the Netherlands',
    'nor': 'Norway',
    'npl': 'Nepal',
    'nru': 'Nauru',
    'nzl': 'New Zealand',
    'omn': 'Oman',
    'pak': 'Pakistan',
    'pan': 'Panama',
    'per': 'Peru',
    'phl': 'the Philippines',
    'plw': 'Palau',
    'png': 'Papua New Guinea',
    'pol': 'Poland',
    'prk': "the Democratic People's Republic of Korea",
    'prt': 'Portugal',
    'pry': 'Paraguay',
    'pse': 'the State of Palestine',
    'qat': 'Qatar',
    'rou': 'Romania',
    'rus': 'the Russian Federation',
    'rwa': 'Rwanda',
    'sau': 'Saudi Arabia',
    'sdn': 'the Sudan',
    'sen': 'Senegal',
    'sgp': 'Singapore',
    'slb': 'Solomon Islands',
    'sle': 'Sierra Leone',
    'slv': 'El Salvador',
    'smr': 'San Marino',
    'som': 'Somalia',
    'srb': 'Serbia',
    'ssd': 'South Sudan',
    'stp': 'Sao Tome and Principe',
    'sur': 'Suriname',
    'svk': 'Slovakia',
    'svn': 'Slovenia',
    'swe': 'Sweden',
    'swz': 'Eswatini',
    'syc': 'Seychelles',
    'syr': 'the Syrian Arab Republic',
    'tcd': 'Chad',
    'tgo': 'Togo',
    'tha': 'Thailand',
    'tjk': 'Tajikistan',
    'tkm': 'Turkmenistan',
    'tls': 'Timor-Leste',
    'ton': 'Tonga',
    'tto': 'Trinidad and Tobago',
    'tun': 'Tunisia',
    'tur': 'Turkiye',
    'tuv': 'Tuvalu',
    'tza': 'the United Republic of Tanzania',
    'uga': 'Uganda',
    'ukr': 'Ukraine',
    'ury': 'Uruguay',
    'usa': 'the United States of America',
    'uzb': 'Uzbekistan',
    'vat': 'the Holy See',
    'vct': 'Saint Vincent and the Grenadines',
    'ven': 'the Bolivarian Republic of Venezuela',
    'vnm': 'Viet Nam',
    'vut': 'Vanuatu',
    'wsm': 'Samoa',
    'yem': 'Yemen',
    'zaf': 'South Africa',
    'zmb': 'Zambia',
    'zwe': 'Zimbabwe',
}


def dirname_to_iso3(dirname: str) -> str | None:
    m = DIRNAME_RE.match(dirname)
    if not m:
        return None
    return m.group(1).lower()


def country_name(iso3: str) -> str:
    return ISO3_TO_NAME.get(iso3, iso3.upper())


def emit_agency_record(iso3: str, created_at: str) -> dict[str, Any]:
    name = f'Government of {country_name(iso3)}'
    return {
        'name': name,
        'jurisdiction': iso3,
        'branch': 'executive',
        'level': 'national',
        'agencyDid': f'did:web:etzhayyim.com:gov:{iso3}',
        'createdAt': created_at,
        'updatedAt': created_at,
    }


def ingest_namespaces(source: Path, created_at: str) -> list[dict[str, Any]]:
    records = []
    for child in sorted(source.iterdir()):
        if not child.is_dir():
            continue
        iso3 = dirname_to_iso3(child.name)
        if iso3 is None:
            continue
        records.append(emit_agency_record(iso3, created_at))
    return records


def main():
    parser = argparse.ArgumentParser(
        description='Walk BPMN gov<ISO3> namespaces and emit com.etzhayyim.gov.agency NDJSON.'
    )
    parser.add_argument('--source', type=Path, default=DEFAULT_SOURCE)
    parser.add_argument('--out', type=Path, default=None)
    args = parser.parse_args()

    now_utc = dt.datetime.now(dt.timezone.utc)
    created_at = now_utc.strftime('%Y-%m-%dT%H:%M:%SZ')

    records = ingest_namespaces(args.source, created_at)

    output_lines = [json.dumps(rec, separators=(',', ':'), ensure_ascii=False) for rec in records]

    if args.out is None:
        for line in output_lines:
            print(line)
        print(f'# Ingested {len(records)} country namespaces from {args.source}', file=sys.stderr)
    else:
        if args.out.is_dir() or str(args.out).endswith('/'):
            timestamp = now_utc.strftime('%Y%m%dT%H%M%SZ')
            out_file = args.out / f'ingest-gov-bpmn-namespaces-{timestamp}.ndjson'
        else:
            out_file = args.out
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, 'w') as f:
            for line in output_lines:
                f.write(line + '\n')
        print(f'Wrote {len(records)} records to {out_file}', file=sys.stderr)


if __name__ == '__main__':
    main()
