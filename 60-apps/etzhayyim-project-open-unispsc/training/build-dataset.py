#!/usr/bin/env python3
"""Build LoRA training dataset from existing UNSPSC commodity components.

Reads all commodity component directories, extracts the 4 files,
and creates JSONL training data for mlx-lm LoRA fine-tuning.
"""
import json
import os
import glob
import random

WASM_DIR = os.path.join(os.path.dirname(__file__), "..", "wasm")
OUTPUT_DIR = os.path.dirname(__file__)

SYSTEM_PROMPT = """You are a UNSPSC commodity component generator for the App platform.
Given a UNSPSC commodity code, name, segment, family, class, and nanoid, generate 4 files:
1. wit/package.wit — commodity-specific WIT interface with domain-appropriate doc comments
2. wit/world.wit — WIT world with contract import + capability export
3. kotodama.jsonld — component configuration
4. main.go — TinyGo implementation using kotodama-go SDK

CRITICAL rules for main.go:
- Use `kotodama.NewApp(kotodama.AppDef{...})` pattern
- Use `app.Command(name, handler, ...options)` for command registration
- Use `kotodama.HandleWCommit(handleWCommit)` and `app.Serve()` in init()
- Use `kotodama.Q("")` for DDL, `kotodama.Q("table")` for queries
- Use `kotodama.G("Label")` for Cypher graph operations
- Use `kotodama.WSend()` for W Protocol publishing
- Include RLS columns: org_id, user_id, actor_id in all tables
- Schema tables: unispsc_specs, unispsc_procurements, unispsc_suppliers, unispsc_standards, unispsc_risks
- Import: `kotodama "github.com/etzhayyim/root/40-engine/kotoba/crates/kotoba-kotodama-go"`
- Commands: get-spec, search-variants, get-concordance, evaluate-supplier, generate-rfp, record-procurement, get-standards, assess-risk, get-contract-info
- func main() {} must be empty"""


def read_file(path):
    try:
        with open(path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return None


def extract_commodity_info(dirname):
    """Extract code, name from directory name like etzhayyim-wasm-unispsc-43211501-mainframe-computers-mc51r8p3"""
    parts = dirname.replace("etzhayyim-wasm-unispsc-", "").split("-")
    if len(parts) < 3:
        return None
    code = parts[0]
    if not code.isdigit() or len(code) != 8:
        return None
    nanoid = parts[-1]
    name_parts = parts[1:-1]
    name = " ".join(name_parts).replace("-", " ").title()
    return {"code": code, "name": name, "nanoid": nanoid}


def build_user_prompt(info, main_go):
    """Build user prompt from commodity info."""
    # Extract segment/family/class from the main.go const block
    segment = family = class_code = ""
    for line in main_go.split("\n"):
        line = line.strip()
        if line.startswith("segmentCode"):
            segment = line.split('"')[1] if '"' in line else ""
        elif line.startswith("familyCode"):
            family = line.split('"')[1] if '"' in line else ""
        elif line.startswith("classCode"):
            class_code = line.split('"')[1] if '"' in line else ""

    return f"""Generate UNSPSC commodity component files:
- Code: {info['code']}
- Name: {info['name']}
- Segment: {segment}
- Family: {family}
- Class: {class_code}
- nanoid: {info['nanoid']}

Output a JSON object with keys: package_wit, world_wit, kotodama_jsonld, main_go"""


def build_training_example(wasm_dir, dirname):
    """Build one training example from a commodity directory."""
    info = extract_commodity_info(dirname)
    if not info:
        return None

    base = os.path.join(wasm_dir, dirname)
    main_go = read_file(os.path.join(base, "main.go"))
    package_wit = read_file(os.path.join(base, "wit", "package.wit"))
    world_wit = read_file(os.path.join(base, "wit", "world.wit"))
    kotodama_jsonld = read_file(os.path.join(base, "kotodama.jsonld"))

    if not all([main_go, package_wit, world_wit, kotodama_jsonld]):
        return None

    user_prompt = build_user_prompt(info, main_go)

    response = json.dumps({
        "package_wit": package_wit,
        "world_wit": world_wit,
        "kotodama_jsonld": kotodama_jsonld,
        "main_go": main_go,
    }, ensure_ascii=False)

    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
            {"role": "assistant", "content": response},
        ]
    }


def load_generated_examples(gen_dir):
    """Load validated generated components from a distillation output directory.

    Each subdirectory is named by commodity code and contains:
    main.go, package.wit, world.wit, kotodama.jsonld
    """
    examples = []
    if not os.path.isdir(gen_dir):
        return examples

    for code_dir in sorted(os.listdir(gen_dir)):
        base = os.path.join(gen_dir, code_dir)
        if not os.path.isdir(base):
            continue

        main_go = read_file(os.path.join(base, "main.go"))
        package_wit = read_file(os.path.join(base, "package.wit"))
        world_wit = read_file(os.path.join(base, "world.wit"))
        kotodama_jsonld = read_file(os.path.join(base, "kotodama.jsonld"))

        if not all([main_go, package_wit, world_wit, kotodama_jsonld]):
            continue

        # Extract info from main.go const block
        info = {"code": code_dir, "name": code_dir, "nanoid": code_dir[:8]}
        user_prompt = build_user_prompt(info, main_go)

        response = json.dumps({
            "package_wit": package_wit,
            "world_wit": world_wit,
            "kotodama_jsonld": kotodama_jsonld,
            "main_go": main_go,
        }, ensure_ascii=False)

        examples.append({
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
                {"role": "assistant", "content": response},
            ]
        })
        print(f"  GEN: {code_dir}")

    return examples


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Build LoRA training dataset from UNSPSC components")
    parser.add_argument("--from-generated", type=str, default="",
                        help="Path to validated generated components directory (distillation output)")
    parser.add_argument("--output-dir", type=str, default=OUTPUT_DIR,
                        help="Output directory for train.jsonl/valid.jsonl")
    args = parser.parse_args()

    wasm_dir = os.path.abspath(WASM_DIR)
    examples = []

    # Load existing local examples
    for dirname in sorted(os.listdir(wasm_dir)):
        if not dirname.startswith("etzhayyim-wasm-unispsc-"):
            continue
        if "-seg-" in dirname:
            continue  # skip segment coordinators

        example = build_training_example(wasm_dir, dirname)
        if example:
            examples.append(example)
            print(f"  OK: {dirname}")
        else:
            print(f"  SKIP: {dirname}")

    print(f"\nLocal examples: {len(examples)}")

    # Load generated examples from distillation output
    if args.from_generated:
        gen_examples = load_generated_examples(args.from_generated)
        examples.extend(gen_examples)
        print(f"Generated examples: {len(gen_examples)}")

    print(f"Total examples: {len(examples)}")

    if len(examples) < 2:
        print("Not enough examples for train/valid split")
        return

    # Shuffle and split 80/20
    random.seed(42)
    random.shuffle(examples)
    split = max(1, len(examples) - max(1, len(examples) // 5))
    train = examples[:split]
    valid = examples[split:]

    # Write JSONL
    out_dir = args.output_dir
    os.makedirs(out_dir, exist_ok=True)
    train_path = os.path.join(out_dir, "train.jsonl")
    valid_path = os.path.join(out_dir, "valid.jsonl")

    for path, data in [(train_path, train), (valid_path, valid)]:
        with open(path, "w") as f:
            for ex in data:
                f.write(json.dumps(ex, ensure_ascii=False) + "\n")
        print(f"Wrote {path} ({len(data)} examples)")


if __name__ == "__main__":
    main()
