import os

replacements = [
    ("RisingWave", "Kotoba/Datomic"),
    ("risingwave", "kotoba"),
    ("RW_URL", "KOTOBA_URL"),
]

def replace_in_file(filepath, replacements):
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            
        new_content = content
        for old, new in replacements:
            new_content = new_content.replace(old, new)
            
        if new_content != content:
            with open(filepath, 'w') as f:
                f.write(new_content)
            print(f"Updated {filepath}")
    except Exception as e:
        print(f"Error processing {filepath}: {e}")

toml_files = [
    "50-infra/etzhayyim-did-web/wrangler.toml",
    "50-infra/murakumo/fleet.toml",
    "50-infra/vultr/geth-private/deps.toml",
    "70-tools/maps-osm-ingest/Cargo.toml",
    "30-graph/deps.toml",
    "90-docs/deps.toml",
    "60-apps/etzhayyim-project-patent/magatama.toml",
    "60-apps/etzhayyim-project-ma/magatama.toml",
    "60-apps/etzhayyim-project-common-crawl/deps.toml",
    "deps.toml"
]

for filepath in toml_files:
    if os.path.exists(filepath):
        replace_in_file(filepath, replacements)

print("Done fixing TOMLs.")
