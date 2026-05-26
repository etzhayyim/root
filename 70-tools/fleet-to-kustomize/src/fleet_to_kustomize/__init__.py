"""fleet-to-kustomize — project fleet.toml to k3s DaemonSet manifests.

Per ADR-2605232100. fleet.toml is the placement source-of-truth; this tool
emits the kustomize overlay that `kubectl apply -k` consumes.
"""

__version__ = "0.1.0"
