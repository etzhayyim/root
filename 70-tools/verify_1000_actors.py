#!/usr/bin/env python3
"""
Mass Verification Script for 1000 Clean Room Actors.
Performs a dry-run startup test:
1. Validates directory structure and required files.
2. Compiles the `src/main.py` into an AST to verify Python syntax (Simulated WASM compile phase).
"""

import os
import ast
import sys

ACTORS_DIR = "20-actors"

def verify_all():
    print("Starting Mass Verification for Clean Room Actors...")

    if not os.path.exists(ACTORS_DIR):
        print(f"Error: {ACTORS_DIR} not found.")
        sys.exit(1)

    actor_dirs = sorted([d for d in os.listdir(ACTORS_DIR) if d.endswith("-compat")])
    total_actors = len(actor_dirs)

    print(f"Found {total_actors} actor directories.")

    success_count = 0
    failure_count = 0
    failures = []

    for actor in actor_dirs:
        actor_path = os.path.join(ACTORS_DIR, actor)
        platform = actor.replace("-compat", "")

        # 1. Check required files
        req_files = [
            "README.md",
            "deps.toml",
            f"schema/{platform}.kotoba",
            "src/main.py"
        ]

        missing = []
        for req in req_files:
            if not os.path.exists(os.path.join(actor_path, req)):
                missing.append(req)

        if missing:
            failures.append(f"[{actor}] Missing files: {', '.join(missing)}")
            failure_count += 1
            continue

        # 2. Syntax Check (AST compilation simulates WASM load phase)
        main_py_path = os.path.join(actor_path, "src", "main.py")
        try:
            with open(main_py_path, "r") as f:
                source_code = f.read()
            ast.parse(source_code, filename=main_py_path)
            success_count += 1
        except SyntaxError as e:
            failures.append(f"[{actor}] Syntax Error in main.py: {e}")
            failure_count += 1
        except Exception as e:
            failures.append(f"[{actor}] Unexpected Error reading main.py: {e}")
            failure_count += 1

    print("\n" + "="*40)
    print("VERIFICATION REPORT")
    print("="*40)
    print(f"Total Evaluated: {total_actors}")
    print(f"Successful:      {success_count}")
    print(f"Failed:          {failure_count}")

    if failures:
        print("\nFailures Detail:")
        for f in failures[:10]: # Print up to 10 failures
            print(f" - {f}")
        if len(failures) > 10:
            print(f" ... and {len(failures) - 10} more.")
        sys.exit(1)
    else:
        print("\nAll systems GO. Syntax and structural integrity confirmed for all APIs.")
        sys.exit(0)

if __name__ == "__main__":
    verify_all()
