"""Leader election for keiei replicas (Phase 4, ADR 2605101200).

When the keiei LSP runs as a multi-replica k8s Deployment, only one
replica may write append-only state (CXO-LEDGER row, mailer watermark)
at a time — otherwise we'd race the ledger seq counter and the mailer
state file. All replicas can serve reads (decide / state / listRoles).

This module provides a tiny, dependency-light abstraction:

  ``LocalLeader``    — always-leader. Used in local dev (stdio /
                       Unix socket / launchd) and unit tests.
  ``K8sLeaseLeader`` — acquires + renews a ``coordination.k8s.io/v1``
                       Lease against the in-cluster API using the
                       projected service-account token. No external
                       Python deps — just stdlib ``urllib.request`` +
                       JSON over HTTPS with the in-pod CA bundle.

Selection happens via ``get_leader()`` factory:

  * ``KUBERNETES_SERVICE_HOST`` + ``KEIEI_LEADER_ENABLED=1`` →
    ``K8sLeaseLeader`` (production).
  * Anything else → ``LocalLeader`` (local dev / tests).

The Lease shape (``coordination.k8s.io/v1``) is the same primitive
used by kube-controller-manager and friends, so cluster operators
already know how to inspect it::

    kubectl -n keiei get lease keiei-writer -o yaml

Override env knobs::

    KEIEI_LEADER_NAMESPACE   default: ``keiei``
    KEIEI_LEADER_NAME        default: ``keiei-writer``
    KEIEI_LEADER_IDENTITY    default: pod hostname (``HOSTNAME`` env)
    KEIEI_LEADER_TTL_SEC     default: ``15`` (lease duration)
    KEIEI_LEADER_RENEW_SEC   default: ``5``  (renew interval)
"""

from __future__ import annotations

import json
import os
import socket
import ssl
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------

class LeaderElection(Protocol):
    """Minimal contract every leader implementation satisfies."""

    def is_leader(self) -> bool: ...
    def identity(self) -> str: ...
    def stop(self) -> None: ...


# ---------------------------------------------------------------------------
# Local fallback — always leader.
# ---------------------------------------------------------------------------

class LocalLeader:
    """Single-process default. Used by launchd / tests / unit dev.

    The local file-based ledger already assumes a single writer
    (launchd plist is single instance), so always-leader is correct.
    """

    def __init__(self, identity: str | None = None) -> None:
        self._identity = identity or os.environ.get("HOSTNAME") or socket.gethostname() or "local"

    def is_leader(self) -> bool:
        return True

    def identity(self) -> str:
        return self._identity

    def stop(self) -> None:
        return None


# ---------------------------------------------------------------------------
# K8s Lease-based leader.
# ---------------------------------------------------------------------------

_KUBE_SA_DIR = Path("/var/run/secrets/kubernetes.io/serviceaccount")
_KUBE_TOKEN_PATH = _KUBE_SA_DIR / "token"
_KUBE_CA_PATH = _KUBE_SA_DIR / "ca.crt"


@dataclass
class _LeaseState:
    holder: str = ""
    acquire_time: float = 0.0
    renew_time: float = 0.0
    transitions: int = 0
    resource_version: str = ""
    lease_duration_sec: int = 15


class K8sLeaseLeader:
    """Acquire + renew a coordination.k8s.io/v1 Lease.

    Background thread polls the lease every ``renew_sec``. When the
    incumbent's ``renewTime`` is older than ``lease_duration_sec``, we
    try to acquire by PUT'ing a new Lease body with our identity. On
    success we own the lease and renew on every tick; on failure we
    remain follower and try again next tick.

    Thread-safe ``is_leader()`` for callers (ledger writer + mailer).
    """

    def __init__(
        self,
        *,
        namespace: str,
        name: str,
        identity: str,
        lease_duration_sec: int = 15,
        renew_sec: int = 5,
        api_host: str | None = None,
        api_port: str | None = None,
        token_path: Path = _KUBE_TOKEN_PATH,
        ca_path: Path = _KUBE_CA_PATH,
        http_timeout_sec: float = 5.0,
    ) -> None:
        self._namespace = namespace
        self._name = name
        self._identity = identity
        self._lease_duration_sec = lease_duration_sec
        self._renew_sec = max(1, min(renew_sec, lease_duration_sec - 1))
        self._token_path = token_path
        self._ca_path = ca_path
        self._http_timeout_sec = http_timeout_sec

        host = api_host or os.environ.get("KUBERNETES_SERVICE_HOST", "kubernetes.default.svc")
        port = api_port or os.environ.get("KUBERNETES_SERVICE_PORT_HTTPS", "443")
        self._base_url = f"https://{host}:{port}/apis/coordination.k8s.io/v1/namespaces/{namespace}/leases"

        self._lock = threading.Lock()
        self._state = _LeaseState(lease_duration_sec=lease_duration_sec)
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    # ---- public ------------------------------------------------------------

    def identity(self) -> str:
        return self._identity

    def is_leader(self) -> bool:
        with self._lock:
            if self._state.holder != self._identity:
                return False
            # Lease has not been renewed within its duration → we lost it.
            if time.time() - self._state.renew_time > self._lease_duration_sec:
                return False
            return True

    def start(self) -> "K8sLeaseLeader":
        if self._thread is not None:
            return self
        self._stop_event.clear()
        t = threading.Thread(
            target=self._renew_loop, name="keiei-leader", daemon=True,
        )
        self._thread = t
        t.start()
        return self

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=self._lease_duration_sec)
            self._thread = None

    # ---- internals ---------------------------------------------------------

    def _renew_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._tick()
            except Exception:                                       # noqa: BLE001
                # Never let an exception kill the background thread —
                # we'd lose the leader gate silently.
                pass
            self._stop_event.wait(self._renew_sec)

    def _tick(self) -> None:
        lease = self._read_lease()
        now = time.time()
        if lease is None:
            self._create_lease()
            return

        spec = (lease or {}).get("spec") or {}
        holder = spec.get("holderIdentity") or ""
        renew_str = spec.get("renewTime") or ""
        duration = int(spec.get("leaseDurationSeconds") or self._lease_duration_sec)
        renew_ts = _parse_rfc3339(renew_str)

        # If we're the holder, just renew.
        if holder == self._identity:
            new_lease = dict(lease)
            new_lease["spec"] = dict(spec, **{
                "holderIdentity": self._identity,
                "renewTime": _now_rfc3339(),
                "leaseDurationSeconds": self._lease_duration_sec,
            })
            ok = self._update_lease(new_lease, lease.get("metadata", {}).get("resourceVersion", ""))
            if ok:
                with self._lock:
                    self._state.holder = self._identity
                    self._state.renew_time = now
                    self._state.lease_duration_sec = self._lease_duration_sec
            return

        # Someone else holds it but the lease is stale → contest it.
        if now - renew_ts > duration:
            new_lease = dict(lease)
            new_lease["spec"] = dict(spec, **{
                "holderIdentity": self._identity,
                "acquireTime": _now_rfc3339(),
                "renewTime": _now_rfc3339(),
                "leaseDurationSeconds": self._lease_duration_sec,
                "leaseTransitions": int(spec.get("leaseTransitions") or 0) + 1,
            })
            ok = self._update_lease(new_lease, lease.get("metadata", {}).get("resourceVersion", ""))
            if ok:
                with self._lock:
                    self._state.holder = self._identity
                    self._state.acquire_time = now
                    self._state.renew_time = now
                    self._state.transitions += 1
                    self._state.lease_duration_sec = self._lease_duration_sec
            return

        # Fresh foreign holder → remain follower.
        with self._lock:
            self._state.holder = holder
            self._state.renew_time = renew_ts

    # ---- HTTP --------------------------------------------------------------

    def _read_token(self) -> str:
        try:
            return self._token_path.read_text().strip()
        except OSError:
            return ""

    def _ssl_context(self) -> ssl.SSLContext:
        ctx = ssl.create_default_context(cafile=str(self._ca_path) if self._ca_path.exists() else None)
        return ctx

    def _request(self, method: str, url: str, body: dict | None = None) -> tuple[int, dict | None]:
        data = None if body is None else json.dumps(body).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self._read_token()}",
            "Accept": "application/json",
        }
        if data is not None:
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=self._http_timeout_sec,
                                        context=self._ssl_context()) as r:
                raw = r.read().decode("utf-8")
                return r.status, (json.loads(raw) if raw else None)
        except urllib.error.HTTPError as e:
            try:
                err_body = e.read().decode("utf-8")
                err_json = json.loads(err_body) if err_body else None
            except Exception:                                       # noqa: BLE001
                err_json = None
            return e.code, err_json
        except (urllib.error.URLError, TimeoutError, ssl.SSLError):
            return 0, None

    def _read_lease(self) -> dict | None:
        status, body = self._request("GET", f"{self._base_url}/{self._name}")
        if status == 200 and isinstance(body, dict):
            return body
        return None

    def _create_lease(self) -> bool:
        body = {
            "apiVersion": "coordination.k8s.io/v1",
            "kind": "Lease",
            "metadata": {"name": self._name, "namespace": self._namespace},
            "spec": {
                "holderIdentity": self._identity,
                "acquireTime": _now_rfc3339(),
                "renewTime": _now_rfc3339(),
                "leaseDurationSeconds": self._lease_duration_sec,
                "leaseTransitions": 1,
            },
        }
        status, _ = self._request("POST", self._base_url, body)
        if status in (200, 201):
            with self._lock:
                now = time.time()
                self._state.holder = self._identity
                self._state.acquire_time = now
                self._state.renew_time = now
                self._state.transitions = 1
            return True
        return False

    def _update_lease(self, lease: dict, resource_version: str) -> bool:
        # Ensure metadata.resourceVersion is set so the API rejects on conflict.
        meta = dict(lease.get("metadata") or {})
        if resource_version:
            meta["resourceVersion"] = resource_version
        lease = dict(lease, metadata=meta)
        status, _ = self._request("PUT", f"{self._base_url}/{self._name}", lease)
        return status == 200


# ---------------------------------------------------------------------------
# RFC3339 helpers — kept minimal, no external dep.
# ---------------------------------------------------------------------------

def _now_rfc3339() -> str:
    # k8s expects nanosecond-precision RFC3339; second precision is accepted.
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _parse_rfc3339(s: str) -> float:
    if not s:
        return 0.0
    try:
        # Strip fractional seconds + trailing Z if present.
        clean = s.replace("Z", "")
        if "." in clean:
            head, _ = clean.split(".", 1)
            clean = head
        return time.mktime(time.strptime(clean, "%Y-%m-%dT%H:%M:%S"))
    except ValueError:
        return 0.0


# ---------------------------------------------------------------------------
# Factory + process-wide singleton (lazy).
# ---------------------------------------------------------------------------

_LEADER_SINGLETON: LeaderElection | None = None
_LEADER_LOCK = threading.Lock()


def _build_leader() -> LeaderElection:
    in_cluster = bool(os.environ.get("KUBERNETES_SERVICE_HOST"))
    enabled = os.environ.get("KEIEI_LEADER_ENABLED", "0") == "1"
    if not (in_cluster and enabled):
        return LocalLeader()

    namespace = os.environ.get("KEIEI_LEADER_NAMESPACE", "keiei")
    name = os.environ.get("KEIEI_LEADER_NAME", "keiei-writer")
    identity = (
        os.environ.get("KEIEI_LEADER_IDENTITY")
        or os.environ.get("HOSTNAME")
        or socket.gethostname()
        or "keiei-pod"
    )
    ttl = int(os.environ.get("KEIEI_LEADER_TTL_SEC", "15"))
    renew = int(os.environ.get("KEIEI_LEADER_RENEW_SEC", "5"))
    leader = K8sLeaseLeader(
        namespace=namespace, name=name, identity=identity,
        lease_duration_sec=ttl, renew_sec=renew,
    )
    leader.start()
    return leader


def get_leader() -> LeaderElection:
    """Return the process-wide leader (lazy, cached)."""
    global _LEADER_SINGLETON
    if _LEADER_SINGLETON is not None:
        return _LEADER_SINGLETON
    with _LEADER_LOCK:
        if _LEADER_SINGLETON is None:
            _LEADER_SINGLETON = _build_leader()
    return _LEADER_SINGLETON


def reset_leader_for_tests() -> None:
    """Clear singleton — only for unit-test isolation."""
    global _LEADER_SINGLETON
    with _LEADER_LOCK:
        if _LEADER_SINGLETON is not None:
            _LEADER_SINGLETON.stop()
        _LEADER_SINGLETON = None


def set_leader_for_tests(leader: LeaderElection) -> None:
    """Inject a custom leader (e.g. a stub). Only for tests."""
    global _LEADER_SINGLETON
    with _LEADER_LOCK:
        _LEADER_SINGLETON = leader
