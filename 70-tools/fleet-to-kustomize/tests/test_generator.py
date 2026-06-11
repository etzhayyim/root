#!/usr/bin/env python3
"""fleet-to-kustomize — generator tests (coverage loop iteration 15).

generator.py projects fleet.toml → k8s manifest dicts (372 LoC, pure stdlib:
tomllib/re/dataclasses) with zero tests. A casing or placement-resolution bug
ships wrong manifests (nodeSelector mismatch, dropped cells). These cover the
pure transforms end to end.

Run: PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/ -q
"""
import pathlib
import sys

SRC = pathlib.Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC))

from fleet_to_kustomize.generator import (  # noqa: E402
    kebab, snake, resolve_placements, Placement,
    render_namespace, render_serviceaccount, render_service, render_daemonset,
    render_root_kustomization, render_cell_kustomization,
    NAMESPACE_DEFAULT,
)


# ── casing helpers ───────────────────────────────────────────────────────────

def test_kebab_camel_to_kebab():
    assert kebab("CharterAttestationRequestCell") == "charter-attestation-request-cell"
    assert kebab("A") == "a"


def test_snake_drops_trailing_cell_suffix():
    assert snake("CharterAttestationRequestCell") == "charter_attestation_request"
    assert snake("FooBar") == "foo_bar"            # no _cell suffix → unchanged
    assert snake("PlainCell") == "plain"


# ── resolve_placements ───────────────────────────────────────────────────────

FLEET = {
    "nodes": [
        {"name": "naphtali", "hostname": "naphtali.local", "ip_lan": "192.168.1.10",
         "cells": ["AlphaCell", "BetaCell"]},
        {"name": "dan-shard", "hostname": "dan.local", "shard_index": 0, "cells": ["GammaCell"]},
        {"name": "joseph-rep", "hostname": "joseph.local", "replicas_of": ["*"], "cells": ["DeltaCell"]},
    ],
    "cells": {
        "AlphaCell": {"healthz_port": 14001, "trigger": "cron", "cron": "*/5 * * * *",
                      "listens_to": ["com.x.evt"], "adr": ["2605232100"]},
        # BetaCell intentionally absent from [cells] → defaults
    },
}


def test_resolve_placements_skips_sharded_and_replica_nodes_with_warnings():
    placements, warnings = resolve_placements(FLEET)
    names = sorted(p.cell_name for p in placements)
    assert names == ["AlphaCell", "BetaCell"]      # gamma/delta deferred
    assert any("sharded" in w for w in warnings)
    assert any("replica-of-all" in w for w in warnings)


def test_resolve_placements_merges_cell_config_and_defaults():
    placements, _ = resolve_placements(FLEET)
    by = {p.cell_name: p for p in placements}
    alpha = by["AlphaCell"]
    assert alpha.leader_node == "naphtali"
    assert alpha.leader_hostname == "naphtali.local"
    assert alpha.leader_ip == "192.168.1.10"
    assert alpha.healthz_port == 14001
    assert alpha.trigger == "cron"
    assert alpha.cron == "*/5 * * * *"
    assert alpha.listens_to == ["com.x.evt"]
    assert alpha.adr == ["2605232100"]
    # BetaCell falls back to empty defaults
    beta = by["BetaCell"]
    assert beta.healthz_port == 0
    assert beta.trigger == ""
    assert beta.cron is None
    assert beta.listens_to == []


def _placement(healthz=0):
    return Placement(
        cell_name="AlphaCell", leader_node="naphtali", leader_hostname="naphtali.local",
        leader_ip="192.168.1.10", healthz_port=healthz, trigger="cron",
        listens_to=[], cron=None, adr=[],
    )


# ── render_* manifests ───────────────────────────────────────────────────────

def test_render_namespace_shape():
    ns = render_namespace(NAMESPACE_DEFAULT)
    assert ns["kind"] == "Namespace"
    assert ns["metadata"]["name"] == NAMESPACE_DEFAULT
    assert ns["metadata"]["labels"]["etzhayyim.com/adr"] == "2605232100"


def test_render_serviceaccount_uses_kebab_name_and_labels():
    sa = render_serviceaccount(_placement(), NAMESPACE_DEFAULT)
    assert sa["kind"] == "ServiceAccount"
    assert sa["metadata"]["name"] == "alpha-cell"
    assert sa["metadata"]["labels"]["etzhayyim.com/cell-name"] == "AlphaCell"
    assert sa["metadata"]["labels"]["etzhayyim.com/leader-node"] == "naphtali"


def test_render_service_adds_cell_port_only_when_healthz_set():
    svc0 = render_service(_placement(0), NAMESPACE_DEFAULT)
    names0 = [p["name"] for p in svc0["spec"]["ports"]]
    assert names0 == ["runner-healthz"]            # always; no cell port
    svc1 = render_service(_placement(14001), NAMESPACE_DEFAULT)
    ports1 = {p["name"]: p["port"] for p in svc1["spec"]["ports"]}
    assert ports1 == {"runner-healthz": 13000, "cell-healthz": 14001}
    assert svc1["spec"]["selector"]["app.kubernetes.io/name"] == "alpha-cell"


def test_render_daemonset_nodeselector_default_and_override():
    ds = render_daemonset(_placement(), NAMESPACE_DEFAULT, "img:1", None, None)
    spec = ds["spec"]["template"]["spec"]
    assert spec["nodeSelector"]["kubernetes.io/hostname"] == "naphtali.local"  # leader_hostname
    # explicit target_hostname overrides (single-node / orbstack validation)
    ds2 = render_daemonset(_placement(), NAMESPACE_DEFAULT, "img:1", "orbstack.local", None)
    assert ds2["spec"]["template"]["spec"]["nodeSelector"]["kubernetes.io/hostname"] == "orbstack.local"


def test_render_daemonset_security_and_command():
    ds = render_daemonset(_placement(14001), NAMESPACE_DEFAULT, "ghcr.io/x:main", None, None)
    c = ds["spec"]["template"]["spec"]["containers"][0]
    assert c["image"] == "ghcr.io/x:main"
    assert c["command"][:3] == ["python", "-m", "kotodama.cell_runner_main"]
    assert "--cell-only" in c["command"] and "AlphaCell" in c["command"]
    assert c["securityContext"]["readOnlyRootFilesystem"] is True
    assert c["securityContext"]["capabilities"]["drop"] == ["ALL"]
    # healthz_port set → a cell-healthz containerPort is appended
    cport_names = [p["name"] for p in c["ports"]]
    assert cport_names == ["runner-healthz", "cell-healthz"]


def test_render_daemonset_repo_hostpath_vs_configmap_fleet_source():
    # orbstack: hostPath repo mount → FLEET_TOML points at /repo/...
    ds = render_daemonset(_placement(), NAMESPACE_DEFAULT, "img:1", None, "/host/repo")
    spec = ds["spec"]["template"]["spec"]
    assert "repo" in [v["name"] for v in spec["volumes"]]
    c = spec["containers"][0]
    fleet = next(e for e in c["env"] if e["name"] == "FLEET_TOML")
    assert fleet["value"] == "/repo/50-infra/murakumo/fleet.toml"
    assert any(e["name"] == "ETZ_REPO" for e in c["env"])

    # production: ConfigMap-mounted fleet.toml → /etc/etzhayyim, fleet-config volume mount
    ds0 = render_daemonset(_placement(), NAMESPACE_DEFAULT, "img:1", None, None)
    c0 = ds0["spec"]["template"]["spec"]["containers"][0]
    fleet0 = next(e for e in c0["env"] if e["name"] == "FLEET_TOML")
    assert fleet0["value"] == "/etc/etzhayyim/fleet.toml"
    assert any(m["name"] == "fleet-config" for m in c0["volumeMounts"])
    assert all(e["name"] != "ETZ_REPO" for e in c0["env"])


# ── kustomization assembly ───────────────────────────────────────────────────

def test_root_kustomization_lists_namespace_then_kebab_cells():
    k = render_root_kustomization(["AlphaCell", "BetaCell"], NAMESPACE_DEFAULT)
    assert k["resources"] == ["namespace.yaml", "cells/alpha-cell", "cells/beta-cell"]
    assert k["namespace"] == NAMESPACE_DEFAULT


def test_cell_kustomization_lists_the_three_manifests():
    k = render_cell_kustomization(_placement(), NAMESPACE_DEFAULT)
    assert k["resources"] == ["serviceaccount.yaml", "daemonset.yaml", "service.yaml"]
