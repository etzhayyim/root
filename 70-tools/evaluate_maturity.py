#!/usr/bin/env python3
"""
Maturity Evaluation Script for Clean Room Actors.
Analyzes the codebase of all 600 actors to determine their implementation depth.

Metrics:
- Endpoints: Number of `@app.route` decorators in main.py.
- Entities: Number of `entity` declarations in the .kotoba schema.
- LOC: Lines of Code in main.py.

Maturity Levels:
- L1 (Scaffolded): 1 Endpoint, 1 Entity, < 50 LOC.
- L2 (Basic): 2-5 Endpoints, 2-5 Entities, 50-150 LOC.
- L3 (Advanced): >5 Endpoints, >5 Entities, >150 LOC.
- L4 (Production Ready): Extensive validation, comprehensive schema.
"""

import os
import re
import sys

ACTORS_DIR = "20-actors"

def evaluate_maturity():
    if not os.path.exists(ACTORS_DIR):
        print(f"Error: {ACTORS_DIR} not found.")
        sys.exit(1)

    actor_dirs = sorted([d for d in os.listdir(ACTORS_DIR) if d.endswith("-compat")])

    levels = {"L1 (Scaffolded)": 0, "L2 (Basic Implementation)": 0, "L3 (Advanced)": 0, "L4 (Production)": 0}
    standouts = []

    for actor in actor_dirs:
        actor_path = os.path.join(ACTORS_DIR, actor)
        platform = actor.replace("-compat", "")

        main_py_path = os.path.join(actor_path, "src", "main.py")
        schema_path = os.path.join(actor_path, "schema", f"{platform}.kotoba")

        endpoints = 0
        loc = 0
        entities = 0

        # Analyze main.py
        if os.path.exists(main_py_path):
            with open(main_py_path, "r") as f:
                content = f.read()
                loc = len(content.splitlines())
                endpoints = len(re.findall(r"@app\.route", content))

        # Analyze schema
        if os.path.exists(schema_path):
            with open(schema_path, "r") as f:
                schema_content = f.read()
                entities = len(re.findall(r"entity\s+\w+\s*\{", schema_content))

        # Determine Level
        level = "L1 (Scaffolded)"
        if endpoints > 5 or entities > 5 or loc > 150:
            level = "L3 (Advanced)"
        elif endpoints > 1 or entities > 1 or loc >= 50:
            level = "L2 (Basic Implementation)"

        levels[level] += 1

        if level in ["L2 (Basic Implementation)", "L3 (Advanced)", "L4 (Production)"]:
            standouts.append({"actor": actor, "level": level, "endpoints": endpoints, "entities": entities, "loc": loc})

    print("="*50)
    print("ACTOR MATURITY EVALUATION REPORT (600 APIs)")
    print("="*50)
    print(f"Total Actors Evaluated: {len(actor_dirs)}\n")

    print("DISTRIBUTION BY MATURITY LEVEL:")
    for lvl, count in levels.items():
        percentage = (count / len(actor_dirs)) * 100 if len(actor_dirs) > 0 else 0
        print(f"  {lvl:<25}: {count:>4} ({percentage:>5.1f}%)")

    print("\n" + "-"*50)
    print("STANDOUT IMPLEMENTATIONS (Above L1):")
    for s in standouts:
        print(f" - {s['actor']:<20} | {s['level']:<25} | Endpoints: {s['endpoints']}, Entities: {s['entities']}, LOC: {s['loc']}")

if __name__ == "__main__":
    evaluate_maturity()
