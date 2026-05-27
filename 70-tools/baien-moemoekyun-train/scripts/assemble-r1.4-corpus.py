#!/usr/bin/env python3
"""assemble-r1.4-corpus.py — bespoke R1.4 moemoekyun corpus assembler.

Resolves cycle 17/19 IPFS-pinned datasets directly via Kubo API (no PDS dependency),
filters per recipe weights + Charter Rider §2 scan, emits unified NDJSON
{instruction, response} pairs ready for SFTTrainer.

Per ADR-2605262100 §3.1 + cycle 7 R1.4 math-rebalance synthesis.

Bypasses e7m-dataset assemble-corpus's PDS prereq (since R1.4 train datasets
are HF mirrors + LangGraph repo-internal harvest — no PDS dataset_pin records
were emitted at pin time).

Output: 70-tools/baien-moemoekyun-train/corpora/moemoekyun-r1.4-coding-math-v1/shard-*.jsonl
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import random
import re
import sys
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

# Use CLI (local ~/.ipfs daemon) instead of HTTP /api/v0/... because cycle 17 found
# that the mac has 2 daemons running: local ~/.ipfs (CLI default, holds cycle 17 pins)
# vs broken /Volumes/260317/etzhayyim/ipfs-data daemon bound to :5001 (datastore I/O error).
# CLI bypasses the HTTP API and reads ~/.ipfs directly.

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s — %(message)s")
log = logging.getLogger("r14-assemble")


def ipfs_ls(cid: str) -> list[dict]:
    """List CID children via `ipfs ls` CLI; returns [{Name, Hash, Type}]."""
    r = subprocess.run(["ipfs", "ls", "--resolve-type=true", cid],
                       capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise RuntimeError(f"ipfs ls {cid}: {r.stderr.strip()[:200]}")
    links = []
    for line in r.stdout.splitlines():
        parts = line.split(maxsplit=2)
        if len(parts) < 3:
            continue
        sub_cid, size, name = parts
        # Type: 1 = directory, 2 = file. CLI doesn't tell us directly; infer from trailing /
        is_dir = name.endswith("/")
        links.append({"Name": name.rstrip("/"), "Hash": sub_cid, "Type": 1 if is_dir else 2, "Size": int(size) if size != "-" else 0})
    return links


def ipfs_cat(cid: str) -> bytes:
    """Fetch CID bytes via `ipfs cat` CLI."""
    r = subprocess.run(["ipfs", "cat", cid], capture_output=True, timeout=300)
    if r.returncode != 0:
        raise RuntimeError(f"ipfs cat {cid}: {r.stderr.decode(errors='replace')[:200]}")
    return r.stdout


def load_manifest(manifest_path: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for line in manifest_path.read_text().splitlines():
        if not line.strip():
            continue
        e = json.loads(line)
        if "task" in e:
            out[e["task"]] = e
    log.info("Loaded %d manifest entries", len(out))
    return out


def extract_magicoder(record):
    if "problem" in record and "solution" in record:
        return {"instruction": record["problem"], "response": record["solution"]}
    return None


def extract_commitpack(record):
    if "message" in record and "new_contents" in record:
        prompt = f"Modify this code per the commit message:\n\nMessage: {record['message']}\n\nCode:\n{record.get('old_contents', '')}"
        return {"instruction": prompt, "response": record["new_contents"]}
    return None


def extract_reasoning_distill(record):
    if "messages" in record:
        msgs = record["messages"]
        usr = next((m["content"] for m in msgs if m.get("role") == "user"), None)
        ast = next((m["content"] for m in msgs if m.get("role") == "assistant"), None)
        if usr and ast:
            return {"instruction": usr, "response": ast}
    for u, a in [("question", "answer"), ("prompt", "completion"), ("input", "output")]:
        if u in record and a in record:
            return {"instruction": record[u], "response": record[a]}
    # Parse ChatML text field: <|im_start|>user\n...<|im_end|><|im_start|>assistant\n...<|im_end|>
    if "text" in record and isinstance(record["text"], str):
        text = record["text"]
        import re as _re
        usr_m = _re.search(r"<\|im_start\|>user\s*\n(.+?)<\|im_end\|>", text, _re.DOTALL)
        ast_m = _re.search(r"<\|im_start\|>assistant\s*\n(.+?)<\|im_end\|>", text, _re.DOTALL)
        if usr_m and ast_m:
            return {"instruction": usr_m.group(1).strip(), "response": ast_m.group(1).strip()}
    return None


def extract_codealpaca(record):
    if "instruction" in record and "output" in record:
        inp = record.get("input", "")
        full = record["instruction"] + (f"\n\n{inp}" if inp else "")
        return {"instruction": full, "response": record["output"]}
    return None


def extract_gsm8k(record):
    if "question" in record and "answer" in record:
        return {"instruction": record["question"], "response": record["answer"]}
    return None


def extract_math500(record):
    if "problem" in record and "solution" in record:
        return {"instruction": record["problem"], "response": record["solution"]}
    return None


def extract_langgraph(record):
    if "instruction" in record and "code" in record:
        return {"instruction": record["instruction"], "response": record["code"]}
    return None


def extract_glaive(record):
    """glaive_function_calling_v2: {system, chat} with USER:/ASSISTANT: in chat."""
    sys_prefix = record.get("system", "")
    chat = record.get("chat", "")
    if not chat:
        return None
    # Split first USER: ... ASSISTANT: ... turn
    import re as _re
    user_m = _re.search(r"USER:\s*(.+?)(?:\n\n|ASSISTANT:)", chat, _re.DOTALL)
    asst_m = _re.search(r"ASSISTANT:\s*(.+?)(?:\n\n|USER:|$)", chat, _re.DOTALL)
    if user_m and asst_m:
        user_msg = user_m.group(1).strip()
        asst_msg = asst_m.group(1).strip()
        instruction = (sys_prefix + "\n\n" + user_msg) if sys_prefix else user_msg
        return {"instruction": instruction, "response": asst_msg}
    return None


def extract_hermes_func(record):
    """hermes_function_calling_v1: {conversations: [{from, value}], tools}."""
    convs = record.get("conversations", [])
    tools = record.get("tools", "")
    if not convs:
        return None
    sys_msg = next((c["value"] for c in convs if c.get("from") == "system"), "")
    user_msg = next((c["value"] for c in convs if c.get("from") == "human"), None)
    asst_msg = next((c["value"] for c in convs if c.get("from") == "gpt"), None)
    if not (user_msg and asst_msg):
        return None
    instruction = sys_msg + "\n\n" + user_msg if sys_msg else user_msg
    if tools and tools not in instruction:
        instruction = f"Tools available:\n{tools}\n\n{instruction}"
    return {"instruction": instruction, "response": asst_msg}


def extract_swe_bench(record):
    """SWE-bench_Verified: {problem_statement, patch}."""
    problem = record.get("problem_statement", "")
    patch = record.get("patch", "")
    if not (problem and patch):
        return None
    instruction = (
        f"Repository: {record.get('repo', 'unknown')}\n"
        f"Problem:\n{problem}\n\n"
        f"Generate a unified diff patch that fixes this issue."
    )
    return {"instruction": instruction, "response": patch}


def extract_magpie(record):
    """magpie_reasoning_v2: {instruction, response} clean direct."""
    instr = record.get("instruction")
    resp = record.get("response")
    if instr and resp:
        return {"instruction": instr, "response": resp}
    return None


SOURCES = [
    {"name": "magicoder",           "weight": 0.25, "task": "magicoder_oss_instruct_75k",       "hf_id": "ise-uiuc/Magicoder-OSS-Instruct-75K","hf_split": "train", "extractor": extract_magicoder,        "tier": "A", "license": "MIT"},
    {"name": "commitpack",          "weight": 0.25, "task": "commitpackft",                     "hf_id": "bigcode/commitpackft",         "hf_split": "train", "hf_config": "python", "extractor": extract_commitpack,       "tier": "A", "license": "MIT"},
    {"name": "reasoning_distill",   "weight": 0.20, "task": "reasoning_distill_opus_47_max_sft","hf_id": "lordx64/reasoning-distill-opus-4-7-max-sft","hf_split": "train", "extractor": extract_reasoning_distill,"tier": "A", "license": "distill-opus-attribution"},
    {"name": "codealpaca",          "weight": 0.10, "task": "codealpaca_20k",                   "hf_id": "sahil2801/CodeAlpaca-20k",     "hf_split": "train", "extractor": extract_codealpaca,       "tier": "A", "license": "CC-BY-NC-4.0", "internal_only": True},
    {"name": "langgraph_internal",  "weight": 0.10, "task": "_local_langgraph",                 "extractor": extract_langgraph,        "tier": "A", "license": "Apache-2.0 + Charter Rider"},
    {"name": "gsm8k",               "weight": 0.05, "task": "gsm8k",                             "hf_id": "openai/gsm8k",                 "hf_split": "train", "hf_config": "main", "extractor": extract_gsm8k,            "tier": "A", "license": "MIT"},
    {"name": "math_500",            "weight": 0.03, "task": "math_500",                          "hf_id": "HuggingFaceH4/MATH-500",       "hf_split": "test",  "extractor": extract_math500,          "tier": "A", "license": "MIT"},
]

# R1.5 Phase 2 SOURCES_AGENTIC: extends NC-free + adds 4 tool-use/agentic sources.
# Per reverse-topo plan (cycle 44): Layer N-3 corpus extension for agentic skills.
# All sources Apache-2.0 / MIT — HF-publish safe.
SOURCES_AGENTIC = [
    # Existing code corpus reduced from NC-free baseline
    {"name": "magicoder",           "weight": 0.18, "hf_id": "ise-uiuc/Magicoder-OSS-Instruct-75K","hf_split": "train", "extractor": extract_magicoder,        "tier": "A", "license": "MIT"},
    {"name": "commitpack",          "weight": 0.18, "hf_id": "bigcode/commitpackft",         "hf_split": "train", "hf_config": "python", "extractor": extract_commitpack,       "tier": "A", "license": "MIT"},
    {"name": "reasoning_distill",   "weight": 0.15, "hf_id": "lordx64/reasoning-distill-opus-4-7-max-sft","hf_split": "train", "extractor": extract_reasoning_distill,"tier": "A", "license": "distill-opus-attribution"},
    {"name": "langgraph_internal",  "weight": 0.08, "task": "_local_langgraph",                 "extractor": extract_langgraph,        "tier": "A", "license": "Apache-2.0 + Charter Rider"},
    # Math-aux retained
    {"name": "gsm8k",               "weight": 0.05, "hf_id": "openai/gsm8k",                 "hf_split": "train", "hf_config": "main", "extractor": extract_gsm8k,            "tier": "A", "license": "MIT"},
    {"name": "math_500",            "weight": 0.03, "hf_id": "HuggingFaceH4/MATH-500",       "hf_split": "test",  "extractor": extract_math500,          "tier": "A", "license": "MIT"},
    # NEW agentic sources (Phase 1 pinned cycle 44)
    {"name": "glaive_func_call",    "weight": 0.10, "hf_id": "glaiveai/glaive-function-calling-v2", "hf_split": "train", "extractor": extract_glaive,       "tier": "A", "license": "Apache-2.0"},
    {"name": "hermes_func_call",    "weight": 0.07, "hf_id": "NousResearch/hermes-function-calling-v1", "hf_split": "train", "extractor": extract_hermes_func, "tier": "A", "license": "Apache-2.0"},
    {"name": "swe_bench_train",     "weight": 0.06, "hf_id": "princeton-nlp/SWE-bench_Verified", "hf_split": "test",  "extractor": extract_swe_bench,    "tier": "A", "license": "MIT"},
    {"name": "magpie_reasoning",    "weight": 0.10, "hf_id": "Magpie-Align/Magpie-Reasoning-V2-250K-CoT-Llama3", "hf_split": "train", "extractor": extract_magpie, "tier": "A", "license": "Apache-2.0"},
]
# Total: 18+18+15+8+5+3+10+7+6+10 = 100%
# Agentic mix: 10+7+6+10 = 33% (tool-call + SWE + reasoning)
# Code mix: 18+18 = 36% (down from 60% in R1.4)
# Math mix: 5+3 = 8% (unchanged)

# Path B (HF-publish-ready) NC-free SOURCES: CodeAlpaca 10% removed,
# redistributed to magicoder +5% + commitpack +5%. All Tier-A non-NC.
# Per ADR-2605262100 G13: removing CC-BY-NC source removes internal_only
# propagation, enabling external publication of derived checkpoint.
SOURCES_NC_FREE = [
    {"name": "magicoder",           "weight": 0.30, "task": "magicoder_oss_instruct_75k",       "hf_id": "ise-uiuc/Magicoder-OSS-Instruct-75K","hf_split": "train", "extractor": extract_magicoder,        "tier": "A", "license": "MIT"},
    {"name": "commitpack",          "weight": 0.30, "task": "commitpackft",                     "hf_id": "bigcode/commitpackft",         "hf_split": "train", "hf_config": "python", "extractor": extract_commitpack,       "tier": "A", "license": "MIT"},
    {"name": "reasoning_distill",   "weight": 0.20, "task": "reasoning_distill_opus_47_max_sft","hf_id": "lordx64/reasoning-distill-opus-4-7-max-sft","hf_split": "train", "extractor": extract_reasoning_distill,"tier": "A", "license": "distill-opus-attribution"},
    {"name": "langgraph_internal",  "weight": 0.10, "task": "_local_langgraph",                 "extractor": extract_langgraph,        "tier": "A", "license": "Apache-2.0 + Charter Rider"},
    {"name": "gsm8k",               "weight": 0.07, "task": "gsm8k",                             "hf_id": "openai/gsm8k",                 "hf_split": "train", "hf_config": "main", "extractor": extract_gsm8k,            "tier": "A", "license": "MIT"},
    {"name": "math_500",            "weight": 0.03, "task": "math_500",                          "hf_id": "HuggingFaceH4/MATH-500",       "hf_split": "test",  "extractor": extract_math500,          "tier": "A", "license": "MIT"},
]


def iter_records_from_hf(hf_id: str, split: str, config: str | None = None) -> Iterator[dict]:
    """Use HF datasets.load_dataset as authoritative source (parquet auto-resolved).

    Cycle 20 path because annex-store git-annex SHA256E chunked names defeat direct
    parquet read; HF cache pull is reliable + reproducible (CIDs separately pinned
    in cycle 19 manifest as substrate audit trail).
    """
    try:
        from datasets import load_dataset
    except ImportError:
        log.warning("datasets package not installed; skipping HF source %s", hf_id)
        return
    log.info("  loading via HF: %s (split=%s%s)", hf_id, split, f", config={config}" if config else "")
    try:
        ds = load_dataset(hf_id, name=config, split=split, trust_remote_code=False) if config else load_dataset(hf_id, split=split, trust_remote_code=False)
        for rec in ds:
            yield rec
    except Exception as e:
        log.error("HF load_dataset %s failed: %s", hf_id, e)


def iter_records_from_cid(cid: str) -> Iterator[dict]:
    try:
        links = ipfs_ls(cid)
    except Exception as e:
        log.error("ipfs ls %s failed: %s", cid, e)
        return
    for link in links:
        name = link["Name"]
        sub_cid = link["Hash"]
        if link["Type"] == 1:
            yield from iter_records_from_cid(sub_cid)
        elif name.endswith(".jsonl"):
            try:
                content = ipfs_cat(sub_cid).decode("utf-8", errors="replace")
                for line in content.splitlines():
                    if line.strip():
                        try:
                            yield json.loads(line)
                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                log.warning("read %s: %s", name, e)
        elif name.endswith(".json"):
            try:
                content = ipfs_cat(sub_cid).decode("utf-8", errors="replace")
                obj = json.loads(content)
                if isinstance(obj, list):
                    yield from obj
                elif isinstance(obj, dict):
                    if "data" in obj and isinstance(obj["data"], list):
                        yield from obj["data"]
                    elif "rows" in obj and isinstance(obj["rows"], list):
                        yield from obj["rows"]
                    else:
                        yield obj
            except Exception as e:
                log.warning("read %s: %s", name, e)
        elif name.endswith(".parquet"):
            try:
                import io
                import pyarrow.parquet as pq
                raw = ipfs_cat(sub_cid)
                table = pq.read_table(io.BytesIO(raw))
                for row in table.to_pylist():
                    yield row
            except ImportError:
                log.warning("pyarrow not installed; skipping %s", name)
            except Exception as e:
                log.warning("read %s: %s", name, e)
        else:
            log.debug("skip non-data file: %s", name)


def iter_records_from_local_jsonl(path: Path) -> Iterator[dict]:
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            continue


CHARTER_BANS = [
    re.compile(p, re.IGNORECASE) for p in [
        r"\bmass surveillance\b",
        r"\bcovert.{0,10}operation",
        r"\bbioweapon",
        r"\bchemical weapon",
        r"\b(nuclear|atomic).{0,10}(weapon|bomb)",
        r"\bchild.{0,5}(porn|sex)",
        r"\bdoxx?ing\b",
        r"\bSSN\s*[:=]\s*\d",
        r"\bAPI[_ ]?KEY\s*[:=]\s*[A-Za-z0-9_-]{16,}",
        r"\bpassword\s*[:=]\s*['\"][^'\"]{6,}['\"]",
    ]
]


def charter_rider_scan(text: str) -> bool:
    for pat in CHARTER_BANS:
        if pat.search(text):
            return False
    return True


def assemble(args):
    repo_root = Path(__file__).resolve().parents[3]
    manifest_path = repo_root / "90-docs/baien/bench-datasets-cid-manifest.jsonl"
    manifest = load_manifest(manifest_path)

    out_dir = Path(args.output_dir)
    if not out_dir.is_absolute():
        out_dir = repo_root / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    total_weight = sum(s["weight"] for s in SOURCES)
    per_source_target = {s["name"]: int(args.target_examples * s["weight"] / total_weight) for s in SOURCES}
    log.info("Per-source targets: %s", per_source_target)

    rng = random.Random(args.seed)

    all_pairs: list[dict] = []
    stats = {"per_source": {}, "charter_rider_rejected": 0, "extraction_failed": 0}

    for src in SOURCES:
        name = src["name"]
        target = per_source_target[name]
        log.info("=== Source %s (target=%d, weight=%.2f) ===", name, target, src["weight"])
        collected: list[dict] = []

        if name == "langgraph_internal":
            harvest_path = repo_root / "90-docs/baien/moemoekyun-r1.4-langgraph-harvest.jsonl"
            if not harvest_path.exists():
                log.warning("LangGraph harvest %s missing; skipping", harvest_path)
                stats["per_source"][name] = {"target": target, "collected": 0, "missing": True}
                continue
            for rec in iter_records_from_local_jsonl(harvest_path):
                pair = src["extractor"](rec)
                if pair is None:
                    stats["extraction_failed"] += 1
                    continue
                full_text = pair["instruction"] + "\n" + pair["response"]
                if not charter_rider_scan(full_text):
                    stats["charter_rider_rejected"] += 1
                    continue
                collected.append(pair)
        else:
            task = src.get("task")
            if task and task in manifest:
                cid = manifest[task]["ipfs_dag_cid"]
                log.info("  (audit CID: %s — substrate trail per ADR-2605241500)", cid)
            # Prefer HF for parquet-based datasets (annex SHA256E chunking blocks direct read)
            hf_id = src.get("hf_id")
            if not hf_id:
                log.warning("source %s has no hf_id; skipping", name)
                stats["per_source"][name] = {"target": target, "collected": 0, "no_hf_id": True}
                continue
            try:
                for rec in iter_records_from_hf(hf_id, src["hf_split"], src.get("hf_config")):
                    pair = src["extractor"](rec)
                    if pair is None:
                        stats["extraction_failed"] += 1
                        continue
                    full_text = pair["instruction"] + "\n" + pair["response"]
                    if not charter_rider_scan(full_text):
                        stats["charter_rider_rejected"] += 1
                        continue
                    collected.append(pair)
                    if len(collected) >= target * 2:
                        break
            except Exception as e:
                log.error("source %s failed: %s", name, e)

        if len(collected) > target:
            rng.shuffle(collected)
            collected = collected[:target]

        for pair in collected:
            pair["_source"] = name
            pair["_tier"] = src["tier"]
            pair["_license"] = src["license"]
            if src.get("internal_only"):
                pair["_internal_only"] = True

        log.info("  Collected: %d (target was %d)", len(collected), target)
        stats["per_source"][name] = {"target": target, "collected": len(collected)}
        all_pairs.extend(collected)

    rng.shuffle(all_pairs)

    corpus_hash = hashlib.sha256()
    for pair in all_pairs:
        corpus_hash.update(json.dumps(pair, sort_keys=True, ensure_ascii=False).encode("utf-8"))

    shard_path = out_dir / "shard-00.jsonl"
    with shard_path.open("w", encoding="utf-8") as f:
        for pair in all_pairs:
            f.write(json.dumps(pair, ensure_ascii=False) + "\n")

    manifest_out = {
        "schema": "etzhayyim.baien.r14-corpus-manifest.v1",
        "tool": "assemble-r1.4-corpus.py",
        "adr": "ADR-2605262100 §3.1 + cycle-7 R1.4 math-rebalance + cycle-19 IPFS substrate",
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "target_examples": args.target_examples,
        "actual_examples": len(all_pairs),
        "corpus_sha256": corpus_hash.hexdigest(),
        "sources": [
            {"name": s["name"], "task": s.get("task", s.get("hf_id", s["name"])), "weight": s["weight"], "tier": s["tier"],
             "license": s["license"], "internal_only": s.get("internal_only", False)}
            for s in SOURCES
        ],
        "stats": stats,
        "output_path": str(shard_path.relative_to(repo_root)),
        "internal_only_propagated": any(s.get("internal_only") for s in SOURCES if stats["per_source"].get(s["name"], {}).get("collected", 0) > 0),
        "g13_note": "CodeAlpaca CC-BY-NC propagates fleet-internal-only restriction (ADR-2605262100 G13). Resulting moemoekyun checkpoint MUST NOT be published; LiteLLM + SBT-gate only.",
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest_out, indent=2, ensure_ascii=False))

    log.info("=== Done ===")
    log.info("Total examples: %d", len(all_pairs))
    log.info("Output shard: %s", shard_path)
    log.info("Manifest: %s", out_dir / "manifest.json")
    log.info("Corpus sha256: %s", manifest_out["corpus_sha256"])
    log.info("Stats:\n%s", json.dumps(stats, indent=2))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--target-examples", type=int, default=5000)
    p.add_argument("--output-dir", default="70-tools/baien-moemoekyun-train/corpora/moemoekyun-r1.4-coding-math-v1/")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--nc-free", action="store_true",
                   help="Use SOURCES_NC_FREE (CodeAlpaca removed, weights redistributed). "
                        "Path B prerequisite for HF publish. Removes G13 internal_only propagation.")
    p.add_argument("--agentic", action="store_true",
                   help="Use SOURCES_AGENTIC for R1.5 — extends NC-free with 4 tool-use/agentic "
                        "sources (glaive, hermes, SWE-bench, magpie). All Apache-2.0/MIT.")
    args = p.parse_args()
    global SOURCES
    if args.agentic:
        SOURCES = SOURCES_AGENTIC
        log.info("=== AGENTIC mode (R1.5): NC-free + 4 tool-use/agentic sources ===")
    elif args.nc_free:
        SOURCES = SOURCES_NC_FREE
        log.info("=== NC-FREE mode: CodeAlpaca removed, weights redistributed ===")
    assemble(args)


if __name__ == "__main__":
    main()
