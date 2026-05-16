#!/usr/bin/env python3
"""Generate corpus-to-BPMN/worker coverage for open-jpn-mynumber."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any
from xml.etree import ElementTree


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CORPUS_JSONL = PROJECT_ROOT / "data" / "ingest" / "corpus.jsonl"
TOPICS_PATH = PROJECT_ROOT / "coverage" / "topics.json"
OUT_JSON = PROJECT_ROOT / "coverage" / "coverage.json"
OUT_MD = PROJECT_ROOT / "coverage" / "coverage.md"


def load_topics() -> list[dict[str, Any]]:
    return json.loads(TOPICS_PATH.read_text(encoding="utf-8"))["topics"]


def bpmn_inventory() -> dict[str, dict[str, Any]]:
    ns = {
        "bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL",
        "camunda": "http://camunda.org/schema/1.0/bpmn",
    }
    inventory: dict[str, dict[str, Any]] = {}
    for path in sorted((PROJECT_ROOT / "bpmn").glob("*.bpmn")):
        root = ElementTree.parse(path).getroot()
        service_tasks = []
        user_tasks = []
        business_rules = []
        for task in root.findall(".//bpmn:serviceTask", ns):
            service_tasks.append({
                "id": task.attrib.get("id"),
                "name": task.attrib.get("name"),
                "topic": task.attrib.get("{http://camunda.org/schema/1.0/bpmn}topic"),
            })
        for task in root.findall(".//bpmn:userTask", ns):
            user_tasks.append({
                "id": task.attrib.get("id"),
                "name": task.attrib.get("name"),
                "formKey": task.attrib.get("{http://camunda.org/schema/1.0/bpmn}formKey"),
            })
        for task in root.findall(".//bpmn:businessRuleTask", ns):
            business_rules.append({
                "id": task.attrib.get("id"),
                "name": task.attrib.get("name"),
                "decisionRef": task.attrib.get("{http://camunda.org/schema/1.0/bpmn}decisionRef"),
            })
        inventory[path.name] = {
            "service_tasks": service_tasks,
            "user_tasks": user_tasks,
            "business_rules": business_rules,
        }
    return inventory


def worker_tasks() -> list[str]:
    source = (PROJECT_ROOT / "worker" / "python" / "open_jpn_mynumber_worker.py").read_text(encoding="utf-8")
    return sorted(set(re.findall(r'"(ai\.gftd\.apps\.openJpnMynumber\.[^"]+)"', source)))


def match_query(text: str, query: str) -> bool:
    terms = [term for term in re.split(r"\s+", query.strip()) if term]
    if not terms:
        return False
    lowered = text.casefold()
    return all(term.casefold() in lowered for term in terms)


def snippet(text: str, query: str, width: int = 180) -> str:
    lowered = text.casefold()
    positions = [lowered.find(term.casefold()) for term in re.split(r"\s+", query.strip()) if term]
    positions = [pos for pos in positions if pos >= 0]
    start = max(0, (min(positions) if positions else 0) - width // 2)
    return " ".join(text[start : start + width].split())


def load_corpus() -> list[dict[str, Any]]:
    rows = []
    with CORPUS_JSONL.open("r", encoding="utf-8") as corpus:
        for line in corpus:
            rows.append(json.loads(line))
    return rows


def query_evidence(corpus: list[dict[str, Any]], query: str, limit: int) -> tuple[int, list[dict[str, Any]]]:
    count = 0
    rows: list[dict[str, Any]] = []
    for row in corpus:
        text = row.get("text", "")
        if not match_query(text, query):
            continue
        count += 1
        if len(rows) < limit:
            rows.append({
                "chunk_id": row["chunk_id"],
                "source_url": row["source_url"],
                "path": row["path"],
                "media_type": row["media_type"],
                "cid": row.get("cid"),
                "snippet": snippet(text, query),
            })
    return count, rows


def score_topic(topic: dict[str, Any], bpmn: dict[str, Any], tasks: list[str], evidence_count: int) -> dict[str, Any]:
    expected_bpmn = set(topic["expected_bpmn"])
    expected_tasks = set(topic["expected_worker_tasks"])
    bpmn_present = sorted(expected_bpmn.intersection(bpmn))
    tasks_present = sorted(expected_tasks.intersection(tasks))
    missing_bpmn = sorted(expected_bpmn.difference(bpmn))
    missing_tasks = sorted(expected_tasks.difference(tasks))
    if not expected_bpmn and not expected_tasks:
        status = "gap" if evidence_count else "not_observed"
    elif missing_bpmn or missing_tasks:
        status = "partial"
    else:
        status = "covered" if evidence_count else "implemented_without_corpus_hit"
    return {
        "status": status,
        "bpmn_present": bpmn_present,
        "worker_tasks_present": tasks_present,
        "missing_bpmn": missing_bpmn,
        "missing_worker_tasks": missing_tasks,
    }


def build(limit: int) -> dict[str, Any]:
    corpus = load_corpus()
    topics = load_topics()
    bpmn = bpmn_inventory()
    tasks = worker_tasks()
    topic_rows = []
    for topic in topics:
        total_hits = 0
        evidence = []
        for query in topic["queries"]:
            count, rows = query_evidence(corpus, query, limit)
            total_hits += count
            if rows and len(evidence) < limit:
                evidence.append({"query": query, "hits": count, "examples": rows[: max(1, limit - len(evidence))]})
        row = {
            **topic,
            "corpus_hits": total_hits,
            "evidence": evidence,
            **score_topic(topic, bpmn, tasks, total_hits),
        }
        topic_rows.append(row)
    result = {
        "project": "open-jpn-mynumber",
        "bpmn": bpmn,
        "worker_tasks": tasks,
        "topics": topic_rows,
        "summary": {
            "covered": sum(1 for row in topic_rows if row["status"] == "covered"),
            "partial": sum(1 for row in topic_rows if row["status"] == "partial"),
            "gap": sum(1 for row in topic_rows if row["status"] == "gap"),
            "not_observed": sum(1 for row in topic_rows if row["status"] == "not_observed"),
        },
    }
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUT_MD.write_text(render_markdown(result), encoding="utf-8")
    return result


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Open Japan My Number Coverage",
        "",
        "## Summary",
        "",
        f"- Covered topics: {result['summary']['covered']}",
        f"- Partial topics: {result['summary']['partial']}",
        f"- Gap topics: {result['summary']['gap']}",
        f"- Not observed topics: {result['summary']['not_observed']}",
        "",
        "## Topic Matrix",
        "",
        "| Topic | Status | Corpus hits | BPMN | Worker tasks |",
        "| --- | --- | ---: | --- | --- |",
    ]
    for row in result["topics"]:
        bpmn = ", ".join(row["bpmn_present"] or row["expected_bpmn"] or ["-"])
        tasks = ", ".join(row["worker_tasks_present"] or row["expected_worker_tasks"] or ["-"])
        lines.append(f"| {row['title']} | `{row['status']}` | {row['corpus_hits']} | {bpmn} | {tasks} |")
    lines += ["", "## Gaps", ""]
    for row in result["topics"]:
        if row["status"] != "gap":
            continue
        lines.append(f"- `{row['id']}`: {row['title']} ({row['corpus_hits']} corpus hits)")
    lines += ["", "## Evidence Samples", ""]
    for row in result["topics"]:
        if not row["evidence"]:
            continue
        lines.append(f"### {row['title']}")
        for ev in row["evidence"][:2]:
            lines.append(f"- Query `{ev['query']}`: {ev['hits']} hits")
            for ex in ev["examples"][:2]:
                snippet = " ".join(str(ex["snippet"]).split())
                lines.append(f"  - `{ex['chunk_id']}` `{ex['cid']}`: {snippet}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-limit", type=int, default=3)
    args = parser.parse_args()
    result = build(args.evidence_limit)
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
