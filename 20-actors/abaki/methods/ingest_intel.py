import json
import os
from pathlib import Path

def fetch_from_intel():
    """
    Mock integration with the `intel` actor's OSINT pipeline.
    In a real implementation, this would call intel.etzhayyim.com/xrpc/etzhayyim.intel.v1.QueryEntityGraph
    or subscribe to its datom log to find monopolistic indicators (M&A, patents, licensing changes).
    """
    print("[intel OSINT] Querying intel graph for Chokepoint/Monopoly indicators...")

    # Simulated response from the intel actor based on OSINT crawling
    return [
        {
            "id": "entity:compute:megacorp_a",
            "name": "MegaCorp AI Compute",
            "domain": "compute",
            "intel_findings": [
                "Acquired 3 major open-source AI startups this quarter (M&A consolidation).",
                "Changed licensing of core model infrastructure from open to proprietary closed-source.",
                "Increased API pricing by 400% after achieving 70% market share."
            ],
            "traits": {
                "closed_source_models": True,
                "proprietary_hardware_lockin": True,
                "pricing_power_abuse": True
            },
            "beneficial_owners": ["individual:tech_baron_x"]
        },
        {
            "id": "entity:biology:agri_monopoly_b",
            "name": "GlobalSeeds Inc.",
            "domain": "biology",
            "intel_findings": [
                "Sued 50+ independent farmers for accidental cross-pollination of patented traits.",
                "Lobbied successfully to ban seed-saving practices in 3 new jurisdictions."
            ],
            "traits": {
                "f1_hybrid_lockin": True,
                "gene_patents": True,
                "lawsuits_against_farmers": True
            },
            "beneficial_owners": ["individual:agri_baron_y", "vc:fund_z"]
        }
    ]

def ingest_to_abaki(intel_data):
    """
    Merges intel OSINT findings into abaki's primary seed data.
    """
    base_dir = Path(__file__).parent.paren
    data_file = base_dir / "data" / "seed.json"

    print(f"[abaki Ingest] Merging {len(intel_data)} OSINT intelligence records into abaki dataset...")

    existing_data = {"entities": []}
    if data_file.exists():
        with open(data_file, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)

    existing_entities = {e["id"]: e for e in existing_data["entities"]}

    for record in intel_data:
        entity_id = record["id"]
        if entity_id in existing_entities:
            # Update traits and findings
            existing_entities[entity_id]["traits"].update(record["traits"])
            existing_entities[entity_id]["intel_findings"] = record.get("intel_findings", [])
        else:
            existing_entities[entity_id] = record

    updated_data = {"entities": list(existing_entities.values())}

    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(updated_data, f, indent=2, ensure_ascii=False)

    print(f"✅ Successfully updated abaki dataset at {data_file}")

def main():
    print("=== abaki OSINT Ingestion Pipeline (intel -> abaki) ===")
    intel_data = fetch_from_intel()
    ingest_to_abaki(intel_data)
    print("=======================================================")

if __name__ == "__main__":
    main()
