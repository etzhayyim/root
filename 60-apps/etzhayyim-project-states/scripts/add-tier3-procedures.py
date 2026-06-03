#!/usr/bin/env python3
"""Add standard procedures (Access to Info / Passport / Tax) + 1 doc template
to tier-3 countries (those with only minimal static data) so every country
gets at least 3 procedure entries visible in the yoro gov tab.
"""
import json
from pathlib import Path

# Countries that already have rich procedures in static data — skip
RICH = {
    "jpn","usa","gbr","deu","fra","ita","can","esp","kor","aus","bra","ind","mex","zaf",
    "rus","chn","idn","sau","tur","arg","che","nld","bel","swe","nor","fin","dnk","pol",
    "grc","prt","aut","irl","isr","sgp","tha","vnm","phl","mys","nzl","chl","col","per",
    "nga","ken","egy","mar",
    "bgd","lka",  # extra set in iter11 extend
}

def standard_procs(iso3: str, name: str) -> list:
    iso = iso3.lower()
    return [
        {
            "id": f"{iso}.access_info",
            "title": "Access to Public Information / Right to Know",
            "authority": f"{name} — each public authority",
            "basis": "Constitutional or administrative access-to-information provision",
        },
        {
            "id": f"{iso}.passport",
            "title": "Passport Application / Renewal",
            "authority": f"{name} — passport authority",
            "basis": "Immigration / nationality law",
        },
        {
            "id": f"{iso}.civil_registration",
            "title": "Civil Registration — birth / marriage / death",
            "authority": f"{name} — civil registry office",
            "basis": "Civil registration statute",
        },
    ]

def standard_doc(iso3: str, name: str) -> list:
    return [
        {
            "id": f"{iso3}.access_info_request.v1",
            "title": "Request for access to public information — template",
            "authority": name,
            "basis": "Access-to-information statute",
        },
    ]

def main():
    root = Path(__file__).parent
    data = json.loads((root / "static-profile-data.json").read_text())
    touched = []
    for iso3, entry in data.items():
        if iso3 in RICH:
            continue
        if entry.get("procedures"):  # already has procedures
            continue
        name = entry.get("displayName") or iso3.upper()
        entry["procedures"] = standard_procs(iso3, name)
        entry["documentTemplates"] = entry.get("documentTemplates", []) + standard_doc(iso3, name)
        touched.append(iso3)
    (root / "static-profile-data.json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print(f"added standard procs/docs to {len(touched)} countries")

if __name__ == "__main__":
    main()
