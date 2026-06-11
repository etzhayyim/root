#!/usr/bin/env sh
set -eu

DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"

kubectl apply --dry-run=client -f "$DIR/deployment.yaml" >/dev/null
kubectl apply --dry-run=client -f "$DIR/job-smoke.yaml" >/dev/null
(cd "$DIR" && python3 -m unittest test_k8s_manifests.py)

echo "intel-dependency-worker k8s dry-run job test ok"
