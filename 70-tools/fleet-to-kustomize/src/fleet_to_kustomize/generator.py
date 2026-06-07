"""Core projection: fleet.toml → list of k8s manifest dicts.

Stage 2 scope (per ADR-2605232100 §Migration plan):
  - Simple "1 leader node → 1 DaemonSet with nodeSelector" pattern only.
  - Cells with `shard_index` / `replicas_of: ["*"]` semantics are skipped
    with a warning; their full handling is follow-up work.
"""

from __future__ import annotations

import re
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Pinned in the rendered manifest. Override-able by future ADR/SoT.
IMAGE_DEFAULT = "ghcr.io/etzhayyim/kotodama:main"
NAMESPACE_DEFAULT = "etzhayyim-cells"
CELL_RUNNER_MODULE = "kotodama.cell_runner_main"


def kebab(name: str) -> str:
    """CamelCase → kebab-case. CharterAttestationRequestCell → charter-attestation-request-cell."""
    return re.sub(r"(?<!^)(?=[A-Z])", "-", name).lower()


def snake(name: str) -> str:
    """CamelCase → snake_case. CharterAttestationRequestCell → charter_attestation_request_cell.

    The cell module path conventionally drops the trailing `_cell` suffix
    (40-engine/kotoba/crates/kotoba-kotodama/cells/charter_attestation_request/, no `_cell`).
    """
    s = re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
    return s[: -len("_cell")] if s.endswith("_cell") else s


@dataclass
class Placement:
    """One cell's pinned-to-node placement, resolved from fleet.toml."""

    cell_name: str
    leader_node: str
    leader_hostname: str
    leader_ip: str
    healthz_port: int
    trigger: str
    listens_to: list[str]
    cron: str | None
    adr: list[str]


def load_fleet(path: Path) -> dict[str, Any]:
    with path.open("rb") as f:
        return tomllib.load(f)


def resolve_placements(fleet: dict[str, Any]) -> tuple[list[Placement], list[str]]:
    """Walk fleet.toml and produce one Placement per (cell, leader-node) pair.

    Returns (placements, warnings). Warnings flag cells that are sharded or
    replica-of-all — those need follow-up handling outside Stage 2.
    """
    node_by_name: dict[str, dict[str, Any]] = {n["name"]: n for n in fleet.get("nodes", [])}
    cells_cfg = fleet.get("cells", {})
    placements: list[Placement] = []
    warnings: list[str] = []

    for node in fleet.get("nodes", []):
        node_name = node["name"]
        # Skip sharded / replica-of-all nodes for Stage 2.
        if "shard_index" in node:
            warnings.append(
                f"node {node_name!r} is sharded (shard_index={node['shard_index']}); "
                f"its cells {node.get('cells', [])} are Stage 2-deferred"
            )
            continue
        if node.get("replicas_of") == ["*"]:
            warnings.append(
                f"node {node_name!r} is replica-of-all; its cells "
                f"{node.get('cells', [])} are Stage 2-deferred"
            )
            continue

        for cell_name in node.get("cells", []):
            cell_cfg = cells_cfg.get(cell_name, {})
            placements.append(
                Placement(
                    cell_name=cell_name,
                    leader_node=node_name,
                    leader_hostname=node["hostname"],
                    leader_ip=node.get("ip_lan", ""),
                    healthz_port=int(
                        cell_cfg.get("healthz_port")
                        or cell_cfg.get("healthz_port_base", 0)
                    ),
                    trigger=str(cell_cfg.get("trigger", "")),
                    listens_to=list(cell_cfg.get("listens_to", []) or []),
                    cron=cell_cfg.get("cron"),
                    adr=list(cell_cfg.get("adr", []) or []),
                )
            )

    return placements, warnings


def render_namespace(ns: str) -> dict[str, Any]:
    return {
        "apiVersion": "v1",
        "kind": "Namespace",
        "metadata": {
            "name": ns,
            "labels": {
                "app.kubernetes.io/part-of": "etzhayyim-religious-corp",
                "etzhayyim.com/adr": "2605232100",
            },
        },
    }


def render_serviceaccount(p: Placement, ns: str) -> dict[str, Any]:
    return {
        "apiVersion": "v1",
        "kind": "ServiceAccount",
        "metadata": {
            "name": kebab(p.cell_name),
            "namespace": ns,
            "labels": _common_labels(p),
        },
    }


def render_service(p: Placement, ns: str) -> dict[str, Any]:
    name = kebab(p.cell_name)
    ports = [
        # The cell-runner process serves /healthz on 13000 reflecting
        # overall runner + cells.toml registry state. Probed by k8s.
        {
            "name": "runner-healthz",
            "port": 13000,
            "targetPort": "runner-healthz",
            "protocol": "TCP",
        },
    ]
    if p.healthz_port > 0:
        # Per-cell subprocess healthz (declared in fleet.toml). May
        # 404 until the cell finishes init — not used by k8s probes
        # in Stage 2 (per-cell readiness gating is Stage 4+ work).
        # Cells with healthz_port_base (dynamic per-instance ports)
        # don't get a stable Service endpoint here.
        ports.append(
            {
                "name": "cell-healthz",
                "port": p.healthz_port,
                "targetPort": "cell-healthz",
                "protocol": "TCP",
            }
        )
    return {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {"name": name, "namespace": ns, "labels": _common_labels(p)},
        "spec": {
            "type": "ClusterIP",
            "selector": {"app.kubernetes.io/name": name},
            "ports": ports,
        },
    }


def render_daemonset(
    p: Placement,
    ns: str,
    image: str,
    target_hostname: str | None,
    repo_hostpath: str | None,
) -> dict[str, Any]:
    """Emit a DaemonSet pinned to the leader hostname.

    `target_hostname` overrides the nodeSelector for single-node validation
    (e.g. local orbstack); production uses the leader Mac mini hostname.

    `repo_hostpath` (orbstack-only) mounts the host repo at `/repo` so
    cell_runner_main.py can resolve `50-infra/murakumo/fleet.toml` from a
    well-known location. Pre-Stage-3 production deploys will replace this
    with a ConfigMap mount; pre-Stage-6 cell_runner_main.py needs a
    `FLEET_TOML` env knob.
    """
    name = kebab(p.cell_name)
    # Although k3s registers the node's NAME as the bare tribe ("naphtali"),
    # the `kubernetes.io/hostname` LABEL on each node is set to the macOS
    # `.local` form (e.g. "naphtalinomac-mini.local"). Use leader_hostname
    # so nodeSelector matches the label, not the NAME. Verified 2026-05-23
    # against the live naphtali k3s cluster (`kubectl get nodes --show-labels`).
    selected_host = target_hostname or p.leader_hostname

    pod_spec: dict[str, Any] = {
        "serviceAccountName": name,
        "nodeSelector": {"kubernetes.io/hostname": selected_host},
        "imagePullSecrets": [{"name": "ghcr-pull"}],
        "containers": [
            {
                "name": "cell",
                "image": image,
                "imagePullPolicy": "Always",
                "command": [
                    "python",
                    "-m",
                    CELL_RUNNER_MODULE,
                    "--node",
                    p.leader_node,
                    "--cell-only",
                    p.cell_name,
                ],
                "env": [
                    {"name": "ETZ_SUBSTRATE", "value": "kotoba-datomic"},
                    {
                        "name": "ETZ_CHECKPOINTER_SOCKET",
                        "value": "/run/etzhayyim/checkpointer.sock",
                    },
                    {"name": "ETZ_CELL_NAME", "value": p.cell_name},
                    # cell_runner_main.py defaults log_dir to ~/.etzhayyim/log
                    # which is read-only under readOnlyRootFilesystem=true.
                    # Redirect into the writable emptyDir at /tmp.
                    {"name": "ETZHAYYIM_LOG_DIR", "value": "/tmp/etzhayyim/log"},
                    # cell-runner /healthz defaults to 127.0.0.1 bind which is
                    # unreachable from the kubelet. ADR-2605232100 enables
                    # 0.0.0.0 bind inside Pods.
                    {"name": "ETZ_HEALTHZ_BIND", "value": "0.0.0.0"},
                ],
                "ports": (
                    [
                        {
                            "name": "runner-healthz",
                            "containerPort": 13000,
                            "protocol": "TCP",
                        },
                    ]
                    + (
                        [
                            {
                                "name": "cell-healthz",
                                "containerPort": p.healthz_port,
                                "protocol": "TCP",
                            }
                        ]
                        if p.healthz_port > 0
                        else []
                    )
                ),
                # Stage 2 (per ADR-2605232100 §Migration plan): probe the
                # runner's overall /healthz on 13000. Per-cell readiness
                # gating (using p.healthz_port) is Stage 4+ work — it
                # requires every cell.py to expose a working /healthz, which
                # is not yet uniformly true across the 15-cell catalog.
                "livenessProbe": _runner_probe(30, 30, 5),
                "readinessProbe": _runner_probe(15, 10, 3),
                "resources": {
                    "requests": {"cpu": "50m", "memory": "128Mi"},
                    "limits": {"cpu": "500m", "memory": "512Mi"},
                },
                "securityContext": {
                    "allowPrivilegeEscalation": False,
                    "readOnlyRootFilesystem": True,
                    "capabilities": {"drop": ["ALL"]},
                },
                "volumeMounts": [
                    {"name": "tmp", "mountPath": "/tmp"},
                ],
            },
        ],
        "volumes": [{"name": "tmp", "emptyDir": {"sizeLimit": "128Mi"}}],
    }

    # Orbstack hostPath repo mount — see docstring caveat.
    if repo_hostpath:
        container = pod_spec["containers"][0]
        container["env"].append({"name": "FLEET_TOML", "value": "/repo/50-infra/murakumo/fleet.toml"})
        container["env"].append({"name": "ETZ_REPO", "value": "/repo"})
        container["volumeMounts"].append({"name": "repo", "mountPath": "/repo", "readOnly": True})
        pod_spec["volumes"].append(
            {"name": "repo", "hostPath": {"path": repo_hostpath, "type": "Directory"}},
        )
    else:
        # Production: ConfigMap-mounted fleet.toml. Cell modules ship in
        # the image. Per ADR-2605232100 §Migration plan, this replaces the
        # orbstack hostPath pattern for the mac mini fleet.
        container = pod_spec["containers"][0]
        container["env"].append(
            {"name": "FLEET_TOML", "value": "/etc/etzhayyim/fleet.toml"}
        )
        container["volumeMounts"].append(
            {"name": "fleet-config", "mountPath": "/etc/etzhayyim", "readOnly": True}
        )
        pod_spec["volumes"].append(
            {
                "name": "fleet-config",
                "configMap": {"name": "fleet-config", "items": [{"key": "fleet.toml", "path": "fleet.toml"}]},
            }
        )

    return {
        "apiVersion": "apps/v1",
        "kind": "DaemonSet",
        "metadata": {
            "name": name,
            "namespace": ns,
            "labels": _common_labels(p),
            "annotations": {
                "etzhayyim.com/leader-node": p.leader_node,
                "etzhayyim.com/leader-hostname": p.leader_hostname,
                "etzhayyim.com/trigger": p.trigger,
                "etzhayyim.com/healthz-port": str(p.healthz_port),
                **(
                    {"etzhayyim.com/listens-to": ",".join(p.listens_to)}
                    if p.listens_to
                    else {}
                ),
                **({"etzhayyim.com/cron": p.cron} if p.cron else {}),
                **({"etzhayyim.com/adr": ",".join(p.adr)} if p.adr else {}),
            },
        },
        "spec": {
            "selector": {"matchLabels": {"app.kubernetes.io/name": name}},
            "template": {"metadata": {"labels": _common_labels(p)}, "spec": pod_spec},
        },
    }


def _common_labels(p: Placement) -> dict[str, str]:
    return {
        "app.kubernetes.io/name": kebab(p.cell_name),
        "app.kubernetes.io/component": "religious-corp-cell",
        "app.kubernetes.io/part-of": "etzhayyim-religious-corp",
        "etzhayyim.com/cell-name": p.cell_name,
        "etzhayyim.com/leader-node": p.leader_node,
    }


def _runner_probe(initial: int, period: int, timeout: int) -> dict[str, Any]:
    """Probe the cell-runner's overall /healthz on port 13000.

    Reflects "runner process alive + cells.toml registry loaded" (Stage 2
    Pod-level readiness criterion). Independent of individual cell
    subprocess init status.
    """
    return {
        "httpGet": {"path": "/healthz", "port": "runner-healthz"},
        "initialDelaySeconds": initial,
        "periodSeconds": period,
        "timeoutSeconds": timeout,
        "failureThreshold": 3,
    }


def render_root_kustomization(cell_names: list[str], ns: str) -> dict[str, Any]:
    return {
        "apiVersion": "kustomize.config.k8s.io/v1beta1",
        "kind": "Kustomization",
        "namespace": ns,
        "resources": ["namespace.yaml"] + [f"cells/{kebab(c)}" for c in cell_names],
    }


def render_cell_kustomization(p: Placement, ns: str) -> dict[str, Any]:
    return {
        "apiVersion": "kustomize.config.k8s.io/v1beta1",
        "kind": "Kustomization",
        "namespace": ns,
        "resources": ["serviceaccount.yaml", "daemonset.yaml", "service.yaml"],
    }
