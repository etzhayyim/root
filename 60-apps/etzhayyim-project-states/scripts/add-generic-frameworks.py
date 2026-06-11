#!/usr/bin/env python3
"""Add generic complianceFrameworks for countries that lack the rich 46-country list.
Uses a placeholder "<Country> Constitution" entry so the gov tab has at least 1 framework shown.
"""
import json
from pathlib import Path

def main():
    root = Path(__file__).parent
    data = json.loads((root / "static-profile-data.json").read_text())
    touched = 0
    for iso, entry in data.items():
        if entry.get("complianceFrameworks"):
            continue
        name = entry.get("displayName") or iso.upper()
        entry["complianceFrameworks"] = [
            f"{name} — National Constitution / Basic Law",
            "Access-to-information statute (where enacted)",
            "Administrative procedure legislation",
        ]
        touched += 1
    (root / "static-profile-data.json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print(f"added generic frameworks to {touched} countries")

if __name__ == "__main__":
    main()
