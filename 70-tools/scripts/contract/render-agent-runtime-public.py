#!/usr/bin/env python3
"""Render public ERC-8004 runtime projections from Kubernetes manifests.

The output is intentionally redacted. It contains workload identity, image,
ports, runtime class, resource profile, and publication annotations. It never
copies env vars, secret refs, service account tokens, or private service URLs.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml


SCHEMA = "https://etzhayyim.com/schemas/k8s-runtime-public/v1.json"
RUNTIME_ANNOTATION = "etzhayyim.com/runtime-kind"
PUBLIC_URL_ANNOTATION = "etzhayyim.com/public-url"
AGENT_ANNOTATION = "etzhayyim.com/erc8004-agent"


def iter_docs(paths: list[Path]) -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []
    for path in paths:
        for doc in yaml.safe_load_all(path.read_text()):
            if isinstance(doc, dict):
                docs.append(doc)
    return docs


def pod_spec(workload: dict[str, Any]) -> dict[str, Any] | None:
    kind = workload.get("kind")
    spec = workload.get("spec") or {}
    if kind in ("Deployment", "StatefulSet"):
        return (((spec.get("template") or {}).get("spec")) or {})
    if kind == "Job":
        return (((spec.get("template") or {}).get("spec")) or {})
    if kind == "CronJob":
        return (((((spec.get("jobTemplate") or {}).get("spec") or {}).get("template") or {}).get("spec")) or {})
    return None


def public_ports(container: dict[str, Any], annotations: dict[str, str]) -> list[dict[str, Any]]:
    public_url = annotations.get(PUBLIC_URL_ANNOTATION, "")
    ports = []
    for port in container.get("ports") or []:
        name = str(port.get("name") or port.get("containerPort") or "http")
        is_public = bool(public_url) and name in ("http", "mcp")
        item = {"name": name, "public": is_public}
        if is_public:
            item["url"] = public_url
        ports.append(item)
    return ports


def first_container(workload: dict[str, Any]) -> dict[str, Any]:
    spec = pod_spec(workload) or {}
    containers = spec.get("containers") or []
    if not containers:
        raise ValueError(f"{workload.get('kind')}/{workload.get('metadata', {}).get('name')} has no containers")
    return containers[0]


def resource_profile(container: dict[str, Any]) -> dict[str, Any]:
    resources = container.get("resources") or {}
    return {
        "requests": resources.get("requests") or {},
        "limits": resources.get("limits") or {},
    }


def render(workload: dict[str, Any], cluster: str) -> dict[str, Any]:
    metadata = workload.get("metadata") or {}
    annotations = metadata.get("annotations") or {}
    namespace = metadata.get("namespace") or "default"
    if namespace == "default":
        raise ValueError(f"{workload.get('kind')}/{metadata.get('name')} uses forbidden default namespace")

    container = first_container(workload)
    runtime_kind = annotations.get(RUNTIME_ANNOTATION)
    if not runtime_kind:
        component = ((metadata.get("labels") or {}).get("app.kubernetes.io/component") or "").lower()
        if "mcp" in component:
            runtime_kind = "mcp-adapter"
        elif "langgraph" in component:
            runtime_kind = "langgraph"
        elif "holochain" in component or "happ" in component:
            runtime_kind = "holochain"
        else:
            runtime_kind = "k8s-langserver"

    command = container.get("command") or []
    args = container.get("args") or []
    task_types = annotations.get("etzhayyim.com/runtime-task-types", "")

    return {
        "schema": SCHEMA,
        "kind": "k8s-runtime",
        "cluster": cluster,
        "namespace": namespace,
        "agent": annotations.get(AGENT_ANNOTATION, ""),
        "workload": {
            "apiVersion": workload.get("apiVersion", ""),
            "kind": workload.get("kind", ""),
            "name": metadata.get("name", ""),
        },
        "image": container.get("image", ""),
        "ports": public_ports(container, annotations),
        "runtime": {
            "kind": runtime_kind,
            "command": command,
            "args": args,
            "taskTypes": [item.strip() for item in task_types.split(",") if item.strip()],
            "resourceProfile": resource_profile(container),
        },
        "redactions": ["env", "secretRef", "serviceAccountToken", "privateUrl"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cluster", required=True)
    parser.add_argument("--kind", action="append", default=["Deployment", "StatefulSet", "Job", "CronJob"])
    parser.add_argument("--out", type=Path)
    parser.add_argument("manifest", nargs="+", type=Path)
    args = parser.parse_args()

    docs = iter_docs(args.manifest)
    projections = []
    for doc in docs:
        if doc.get("kind") in set(args.kind):
            projections.append(render(doc, args.cluster))

    output: Any = projections[0] if len(projections) == 1 else projections
    data = json.dumps(output, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(data)
    else:
        sys.stdout.write(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
