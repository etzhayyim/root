#!/usr/bin/env python3
"""Validate AT Protocol Lexicon v1 JSON files in 00-contracts/lexicons/.

Per AT Protocol spec + religious-corp constraints:
- lexicon == 1
- id is a valid NSID (lowercase reverse-domain + identifier)
- defs.main.type is one of: record / procedure / query / subscription / token
- No `type: "number"` (use integer with implied units)
- No inline `items: {type: "object", ...}` (use {type: "ref", ref: "#typeName"})
- All format values are valid: did / at-uri / cid / datetime / handle / nsid / uri

Run:
    python 70-tools/scripts/validate-lexicons.py

    # specific dir:
    python 70-tools/scripts/validate-lexicons.py --root 00-contracts/lexicons/com/etzhayyim/
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any


VALID_DEF_TYPES = {"record", "procedure", "query", "subscription", "token", "string", "object"}
VALID_FORMATS = {"did", "at-uri", "cid", "datetime", "handle", "nsid", "uri", "language"}


def validate_lexicon(path: Path) -> list[str]:
    """Return list of validation errors for a single lexicon JSON file."""
    errors = []

    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        return [f"invalid JSON: {e}"]

    if data.get("lexicon") != 1:
        errors.append(f"lexicon != 1 (got {data.get('lexicon')})")

    nsid = data.get("id", "")
    if not _is_valid_nsid(nsid):
        errors.append(f"invalid NSID: {nsid!r}")

    defs = data.get("defs", {})
    if not isinstance(defs, dict):
        errors.append("defs is not a dict")
        return errors

    if "main" not in defs:
        errors.append("missing defs.main")
        return errors

    main_type = defs["main"].get("type")
    if main_type not in VALID_DEF_TYPES:
        errors.append(f"defs.main.type {main_type!r} not in {VALID_DEF_TYPES}")

    # Walk all defs for forbidden patterns
    for def_name, def_value in defs.items():
        _walk_def(def_name, def_value, errors)

    return errors


def _is_valid_nsid(nsid: str) -> bool:
    """AT Protocol NSID format: reverse-domain + identifier, e.g. com.etzhayyim.shinka.tick"""
    if not nsid:
        return False
    parts = nsid.split(".")
    if len(parts) < 3:
        return False
    for part in parts:
        if not part:
            return False
        if not part.replace("-", "").replace("_", "").isalnum():
            return False
    return True


def _walk_def(name: str, value: Any, errors: list[str], path: str = "") -> None:
    """Recursively check for forbidden patterns."""
    if isinstance(value, dict):
        # Check for type: "number"
        if value.get("type") == "number":
            errors.append(f"{path}: type='number' (use integer with implied units)")

        # Check for inline items: {type: "object"}
        items = value.get("items")
        if isinstance(items, dict) and items.get("type") == "object":
            errors.append(f"{path}.items: inline type='object' (use ref to def)")

        # Check format values (must be string)
        if "format" in value:
            fmt = value["format"]
            if isinstance(fmt, str) and fmt not in VALID_FORMATS:
                errors.append(f"{path}: invalid format {fmt!r}")

        for k, v in value.items():
            _walk_def(k, v, errors, f"{path}.{k}" if path else k)
    elif isinstance(value, list):
        for i, item in enumerate(value):
            _walk_def(name, item, errors, f"{path}[{i}]")


def main():
    parser = argparse.ArgumentParser(description="Validate AT Protocol Lexicon JSON files")
    parser.add_argument(
        "--root",
        default="00-contracts/lexicons",
        help="Lexicon root directory (default: 00-contracts/lexicons). Used when --files is empty.",
    )
    parser.add_argument(
        "--files",
        nargs="*",
        default=None,
        help="Explicit list of Lexicon JSON files to validate (overrides --root walk). "
             "Use with lefthook {staged_files} to only validate files in current commit.",
    )
    parser.add_argument(
        "--exit-on-error",
        action="store_true",
        help="Exit with non-zero status if any errors found",
    )
    args = parser.parse_args()

    if args.files:
        # Explicit file list mode (lefthook staged-only path)
        files = []
        for f in args.files:
            p = Path(f)
            if not p.exists():
                continue
            if p.suffix != ".json":
                continue
            if p.name.startswith("_"):
                continue
            # Only validate files actually inside a lexicon root
            if "00-contracts/lexicons/" not in str(p):
                continue
            files.append(p)
        files = sorted(files)
        if not files:
            # No staged Lexicon files — nothing to validate, exit clean
            print("[validate-lexicons] no staged Lexicon files in commit; skipping.")
            sys.exit(0)
    else:
        # Root walk mode (manual invocation)
        root = Path(args.root)
        if not root.exists():
            print(f"error: root not found: {root}", file=sys.stderr)
            sys.exit(2)
        files = sorted(root.rglob("*.json"))
        # Skip _manifest.json and other registry files
        files = [f for f in files if not f.name.startswith("_")]

    total_errors = 0
    error_categories = {}

    for path in files:
        errors = validate_lexicon(path)
        if errors:
            # When --files mode used, root may not be set; print absolute-from-repo path
            try:
                rel = path.relative_to(root) if not args.files else path
            except (ValueError, NameError):
                rel = path
            print(f"\n{rel}:")
            for err in errors:
                print(f"  - {err}")
                # Categorize error
                if "type='number'" in err:
                    error_categories["type='number'"] = error_categories.get("type='number'", 0) + 1
                elif "inline type='object'" in err:
                    error_categories["inline type='object'"] = error_categories.get("inline type='object'", 0) + 1
                elif "invalid format" in err:
                    error_categories["invalid format"] = error_categories.get("invalid format", 0) + 1
                elif "invalid NSID" in err:
                    error_categories["invalid NSID"] = error_categories.get("invalid NSID", 0) + 1
                elif "lexicon !=" in err:
                    error_categories["lexicon != 1"] = error_categories.get("lexicon != 1", 0) + 1
                else:
                    error_categories["other"] = error_categories.get("other", 0) + 1
            total_errors += len(errors)

    print(f"\n{len(files)} lexicons validated, {total_errors} errors found")

    if error_categories:
        print("\nError breakdown:")
        for category, count in sorted(error_categories.items(), key=lambda x: -x[1]):
            print(f"  {category}: {count}")

    if total_errors > 0 and args.exit_on_error:
        sys.exit(1)


if __name__ == "__main__":
    main()
