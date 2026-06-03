#!/usr/bin/env python3
"""Generate the canonical unispsc actor registry JSON.

SoT inputs:
  20-actors/magatama/py/src/pymagatama/langgraph_graphs/unispsc_agents/c*.py

Output:
  00-contracts/actor-registry/unispsc.json

Schema (per ADR-2605212030 §D2, did:web colon-to-slash + lexicon family):
  {
    "$schema":     URL,
    "version":     "1",
    "generatedAt": ISO-8601,
    "lexicon":     "com.etzhayyim.apps.unispsc",
    "didEntity":   "did:web:etzhayyim.com",
    "totalCount":  int,
    "segments":    { "<2-digit prefix>": int, ... },
    "agents": [
      { "code", "handle", "did", "didSubdomain", "module", "title", "segment", "family", "class", "commodity" },
      ...
    ]
  }

Run from repo root:
  python3 70-tools/scripts/registry/generate-unispsc-registry.py
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
AGENTS_DIR = (
    REPO_ROOT
    / "20-actors/magatama/py/src/pymagatama/langgraph_graphs/unispsc_agents"
)
OUTPUT_PATH = REPO_ROOT / "00-contracts/actor-registry/unispsc.json"
# Slim derived artefact bundled into the did-web Worker. The full JSON is 6+ MB
# and exceeds the Worker per-script size budget; the Worker only needs the set
# of valid handles for DID validation, so we emit a codes-only TS module.
HANDLES_TS_PATH = (
    REPO_ROOT
    / "50-infra/etzhayyim-did-web/src/registry/unispsc-handles.gen.ts"
)
# Slim per-row tuple module bundled into the rw-free xrpc-adapter Worker.
# Compact `[code, title, segment]` tuples keep the bundle small enough that
# even with @etzhayyim/sdk + yoro-rw-free we stay well under the CF per-script
# limit. Phase β: replace with an IPFS-pinned CID fetched via gateway + KV cache.
ADAPTER_TS_PATH = (
    REPO_ROOT
    / "60-apps/etzhayyim-project-yoro/xrpc-adapter/src/registry/unispsc-agents.gen.ts"
)

CODE_RE = re.compile(r"^c(\d{6,12})$")
CLASS_RE = re.compile(r"\bclass\s+([A-Z][A-Za-z0-9_]*)\s*\(")


def split_segments(code: str) -> tuple[str, str, str, str]:
    """UNSPSC 8-digit code → (segment, family, class, commodity).

    Padded with the leading zero when shorter than 8 (older registry rows).
    """
    padded = code.zfill(8)
    return padded[0:2], padded[2:4], padded[4:6], padded[6:8]


def extract_title(path: Path) -> str:
    """Best-effort label from the file's first `class XxxState(...)` token.

    The unispsc_agents files are minified single-line LangGraph definitions;
    the State class name is the only stable human-facing label. We strip the
    trailing `State` suffix and CamelCase-split.
    """
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""
    m = CLASS_RE.search(content)
    if not m:
        return ""
    name = m.group(1)
    if name.endswith("State"):
        name = name[:-5]
    # CamelCase → "Camel Case"
    return re.sub(r"(?<!^)([A-Z])", r" \1", name).strip()


def main() -> int:
    if not AGENTS_DIR.is_dir():
        print(f"error: agents dir not found: {AGENTS_DIR}", file=sys.stderr)
        return 1

    agents = []
    segments: dict[str, int] = {}
    for path in sorted(AGENTS_DIR.iterdir()):
        if not path.is_file() or path.suffix != ".py":
            continue
        m = CODE_RE.match(path.stem)
        if not m:
            continue
        code = m.group(1)
        handle = f"c{code}"
        seg, fam, cls, com = split_segments(code)
        agents.append(
            {
                "code": code,
                "handle": handle,
                "did": f"did:web:etzhayyim.com:actor:{handle}",
                "didSubdomain": f"did:web:{handle}.etzhayyim.com",
                "module": f"pymagatama.langgraph_graphs.unispsc_agents.{path.stem}",
                "title": extract_title(path),
                "segment": seg,
                "family": fam,
                "class": cls,
                "commodity": com,
            }
        )
        segments[seg] = segments.get(seg, 0) + 1

    out = {
        "$schema": "https://etzhayyim.com/schemas/actor-registry/v1.json",
        "version": "1",
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "lexicon": "com.etzhayyim.apps.unispsc",
        "didEntity": "did:web:etzhayyim.com",
        "adr": ["2605212030", "2605171800"],
        "totalCount": len(agents),
        "segments": dict(sorted(segments.items())),
        "agents": agents,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(
        f"wrote {OUTPUT_PATH.relative_to(REPO_ROOT)} "
        f"({len(agents)} agents, {len(segments)} segments)"
    )

    handles = sorted(a["handle"] for a in agents)
    HANDLES_TS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with HANDLES_TS_PATH.open("w", encoding="utf-8") as f:
        f.write("// AUTOGENERATED — do not edit.\n")
        f.write(
            "// Source: 00-contracts/actor-registry/unispsc.json\n"
            "// Regenerate: python3 70-tools/scripts/registry/"
            "generate-unispsc-registry.py\n\n"
        )
        f.write(f"export const UNISPSC_TOTAL_COUNT = {len(handles)};\n")
        f.write(f'export const UNISPSC_GENERATED_AT = "{out["generatedAt"]}";\n\n')
        f.write("// Frozen Set for O(1) handle validation in the did-web Worker.\n")
        f.write("export const UNISPSC_HANDLES: ReadonlySet<string> = new Set([\n")
        for h in handles:
            f.write(f'  "{h}",\n')
        f.write("]);\n")
    print(
        f"wrote {HANDLES_TS_PATH.relative_to(REPO_ROOT)} ({len(handles)} handles)"
    )

    ADAPTER_TS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with ADAPTER_TS_PATH.open("w", encoding="utf-8") as f:
        f.write("// AUTOGENERATED — do not edit.\n")
        f.write(
            "// Source: 00-contracts/actor-registry/unispsc.json\n"
            "// Regenerate: python3 70-tools/scripts/registry/"
            "generate-unispsc-registry.py\n\n"
        )
        f.write(
            "// Compact tuple form: [code, handle, title, segment].\n"
            "// Bundled into the xrpc-adapter Worker for "
            "com.etzhayyim.apps.unispsc.listAgents.\n"
            "// Phase β migration target: IPFS CID + KV cache (see ADR-2605171800).\n\n"
        )
        f.write(
            "export type UnispscAgentRow = readonly "
            "[code: string, handle: string, title: string, segment: string];\n\n"
        )
        f.write(f"export const UNISPSC_TOTAL = {len(agents)};\n")
        f.write(f'export const UNISPSC_GENERATED_AT = "{out["generatedAt"]}";\n\n')
        f.write("export const UNISPSC_AGENTS: readonly UnispscAgentRow[] = [\n")
        for a in agents:
            # JS-escape title (defensive — class names are ASCII but
            # future titles from UNSPSC dictionary may include backslashes/quotes)
            t = a["title"].replace("\\", "\\\\").replace('"', '\\"')
            f.write(
                f'  ["{a["code"]}", "{a["handle"]}", "{t}", "{a["segment"]}"],\n'
            )
        f.write("];\n")
    print(
        f"wrote {ADAPTER_TS_PATH.relative_to(REPO_ROOT)} ({len(agents)} agents)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
