#!/usr/bin/env python3
"""For countries without desks, add a generic general_inquiry desk pointing
to their first contact (gov website / portal)."""
import json
from pathlib import Path

def main():
    root = Path(__file__).parent
    data = json.loads((root / "static-profile-data.json").read_text())
    touched = 0
    for iso3, entry in data.items():
        if entry.get("desks"):
            continue
        contacts = entry.get("contacts") or []
        if not contacts:
            continue
        # Primary website
        primary = next((c for c in contacts if c.get("kind") == "website"), contacts[0])
        entry["desks"] = [{
            "kind": "general_inquiry",
            "label": f"{entry.get('displayName', iso3.upper())} — citizen inquiry",
            "uri": primary.get("uri", ""),
        }]
        touched += 1
    (root / "static-profile-data.json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print(f"added generic desks to {touched} countries")

if __name__ == "__main__":
    main()
