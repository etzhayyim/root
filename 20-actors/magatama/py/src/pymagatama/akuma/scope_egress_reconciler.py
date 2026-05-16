"""Akuma scope-egress NetworkPolicy reconciler (ADR-2605151400).

Reads currently-active red team scope contracts from RisingWave
(``vertex_akuma_scope`` WHERE status='active' AND now BETWEEN
valid_from_ms AND valid_until_ms) and rewrites the
``akuma-probe-scope-allow`` NetworkPolicy egress so that probe pods
can reach only IPs/CIDRs covered by an active scope.

Runs as a Kubernetes CronJob every 60 seconds (see
``50-infra/k8s/akuma-langserver/scope-egress-reconciler.yaml``). On
revocation (status flip or window expiry) the WHERE clause stops
returning that scope, so its egress rule disappears on the next tick.

Forbidden:
- Direct edits to ``akuma-probe-scope-allow`` by hand
  (annotation ``do-not-edit-by-hand: "true"`` on the resource).
- Mounting akuma LangServer write credentials inside the
  ``akuma-probe`` namespace.

Apply path: this module is idempotent and exits 0 on success, non-zero
on any failure. Failed runs leave the previous policy untouched.
"""

from __future__ import annotations

import ipaddress
import logging
import os
import socket
import sys
import time
from typing import Any

import psycopg
from kubernetes import client, config


LOG = logging.getLogger("akuma.scope_egress_reconciler")

NS = os.environ.get("AKUMA_PROBE_NAMESPACE", "akuma-probe")
NP_NAME = os.environ.get("AKUMA_NETWORKPOLICY_NAME", "akuma-probe-scope-allow")
RW_URL = os.environ["RW_URL"]


def _load_active_scopes() -> list[dict[str, Any]]:
    now_ms = int(time.time() * 1000)
    sql = (
        "SELECT scope_id, target_kind, targets, excluded_targets, allowed_ports "
        "FROM vertex_akuma_scope "
        "WHERE status = 'active' "
        "  AND %s BETWEEN valid_from_ms AND valid_until_ms"
    )
    with psycopg.connect(RW_URL) as conn, conn.cursor() as cur:
        cur.execute(sql, (now_ms,))
        cols = [c.name for c in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


def _parse_csv(s: str | None) -> list[str]:
    if not s:
        return []
    return [t.strip() for t in s.split(",") if t.strip()]


def _resolve_to_cidrs(target: str, kind: str) -> list[str]:
    """Resolve a scope target to one or more CIDRs.

    ``ip``       -> ``<ip>/32`` or ``<ip>/128``
    ``cidr``     -> as-is
    ``hostname`` -> DNS A/AAAA at reconcile time, each as ``/32`` or ``/128``
    ``url``      -> hostname extracted, then DNS like above

    Resolution failures return ``[]`` (target gets no egress allow until
    DNS recovers; the next tick retries).
    """
    if kind == "cidr":
        try:
            ipaddress.ip_network(target, strict=False)
            return [target]
        except ValueError:
            LOG.warning("invalid cidr %r in scope, skipping", target)
            return []

    if kind == "ip":
        try:
            ip = ipaddress.ip_address(target)
            return [f"{ip}/{32 if ip.version == 4 else 128}"]
        except ValueError:
            LOG.warning("invalid ip %r in scope, skipping", target)
            return []

    if kind in ("hostname", "url"):
        host = target
        if kind == "url":
            from urllib.parse import urlparse
            host = urlparse(target).hostname or ""
        if not host:
            return []
        try:
            infos = socket.getaddrinfo(host, None)
        except OSError as exc:
            LOG.warning("dns lookup failed for %r: %s", host, exc)
            return []
        cidrs: list[str] = []
        seen: set[str] = set()
        for info in infos:
            addr = info[4][0]
            try:
                ip = ipaddress.ip_address(addr)
            except ValueError:
                continue
            cidr = f"{ip}/{32 if ip.version == 4 else 128}"
            if cidr in seen:
                continue
            seen.add(cidr)
            cidrs.append(cidr)
        return cidrs

    LOG.warning("unknown target_kind %r for %r", kind, target)
    return []


def _build_egress_rules(scopes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rules: list[dict[str, Any]] = []
    for scope in scopes:
        kind = scope["target_kind"]
        excluded = set(_parse_csv(scope.get("excluded_targets")))
        ports_raw = _parse_csv(scope.get("allowed_ports"))
        ports: list[dict[str, Any]] = []
        for p in ports_raw:
            try:
                ports.append({"protocol": "TCP", "port": int(p)})
            except ValueError:
                LOG.warning(
                    "scope %s allowed_ports has non-int %r, skipping",
                    scope["scope_id"],
                    p,
                )
        for target in _parse_csv(scope.get("targets")):
            if target in excluded:
                continue
            for cidr in _resolve_to_cidrs(target, kind):
                rule: dict[str, Any] = {"to": [{"ipBlock": {"cidr": cidr}}]}
                if ports:
                    rule["ports"] = ports
                rules.append(rule)
    return rules


def _patch_networkpolicy(rules: list[dict[str, Any]]) -> None:
    try:
        config.load_incluster_config()
    except config.ConfigException:
        config.load_kube_config()
    api = client.NetworkingV1Api()

    body = {
        "spec": {
            "podSelector": {"matchLabels": {"role": "probe-runner"}},
            "policyTypes": ["Egress"],
            "egress": rules,
        }
    }
    api.patch_namespaced_network_policy(name=NP_NAME, namespace=NS, body=body)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    try:
        scopes = _load_active_scopes()
        LOG.info("loaded %d active scope(s)", len(scopes))
        rules = _build_egress_rules(scopes)
        LOG.info("built %d egress rule(s)", len(rules))
        _patch_networkpolicy(rules)
        LOG.info("patched networkpolicy %s/%s", NS, NP_NAME)
        return 0
    except Exception:  # noqa: BLE001
        LOG.exception("reconcile failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
