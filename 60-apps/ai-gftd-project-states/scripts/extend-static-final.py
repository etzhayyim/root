#!/usr/bin/env python3
"""Final 15 sovereign states to reach 100% coverage of seed_domains.sovereignSeeds()."""
import json
from pathlib import Path

FINAL = {
    "and": ("Principality of Andorra", "Andorra la Vella", "AD", "https://www.govern.ad/"),
    "atg": ("Antigua and Barbuda", "Saint John's", "AG", "https://ab.gov.ag/"),
    "brb": ("Barbados", "Bridgetown", "BB", "https://gisbarbados.gov.bb/"),
    "dma": ("Commonwealth of Dominica", "Roseau", "DM", "https://dominica.gov.dm/"),
    "grd": ("Grenada", "Saint George's", "GD", "https://gov.gd/"),
    "kna": ("Federation of Saint Kitts and Nevis", "Basseterre", "KN", "https://www.gov.kn/"),
    "lby": ("State of Libya", "Tripoli", "LY", "https://www.pm.gov.ly/"),
    "lie": ("Principality of Liechtenstein", "Vaduz", "LI", "https://www.liechtenstein.li/"),
    "mhl": ("Republic of the Marshall Islands", "Majuro", "MH", "https://rmigovernment.org/"),
    "mlt": ("Republic of Malta", "Valletta", "MT", "https://www.gov.mt/"),
    "mne": ("Montenegro", "Podgorica", "ME", "https://www.gov.me/"),
    "nru": ("Republic of Nauru", "Yaren District", "NR", "https://www.naurugov.nr/"),
    "smr": ("Most Serene Republic of San Marino", "San Marino", "SM", "https://www.sanmarino.sm/"),
    "vat": ("Vatican City State / Holy See", "Vatican City", "VA", "https://www.vatican.va/"),
    "vct": ("Saint Vincent and the Grenadines", "Kingstown", "VC", "https://www.gov.vc/"),
}

def build(entry):
    name, capital, country, website = entry
    return {
        "displayName": name,
        "addresses": [{"kind": "headquarters", "label": f"Capital: {capital}", "addressLocality": capital, "country": country}],
        "contacts": [{"kind": "website", "uri": website, "label": f"{name} — official portal"}],
        "desks": [{"kind": "general_inquiry", "label": f"{name} — citizen inquiry", "uri": website}],
        "procedures": [
            {"id": f"{next(iter([name[:3].lower()]))}.access_info", "title": "Access to Public Information", "authority": name},
            {"id": f"{next(iter([name[:3].lower()]))}.passport", "title": "Passport Application / Renewal", "authority": f"{name} — passport authority"},
        ],
        "documentTemplates": [
            {"id": f"{country.lower()}.access_info.v1", "title": "Access to public information request — template", "authority": name},
        ],
    }

def main():
    root = Path(__file__).parent
    data = json.loads((root / "static-profile-data.json").read_text())
    before = len(data)
    added = []
    for iso, entry in FINAL.items():
        if iso in data: continue
        data[iso] = build(entry)
        added.append(iso)
    (root / "static-profile-data.json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print(f"added {len(added)} countries, total {before} -> {len(data)}")

if __name__ == "__main__":
    main()
