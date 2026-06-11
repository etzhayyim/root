# ollama-fleet

K8s manifest that runs Ollama on every Murakumo Mac-mini node and
exposes a single ClusterIP service so `lg-ameno` (and any future
in-cluster langserver) can dial it via a stable DNS name.

ADR-2605191257 + ADR-2605191346 + ADR-2605182312.

## Files

| file | role |
|---|---|
| `daemonset.yaml` | Namespace + ServiceAccount + PVC + DaemonSet (one pod per murakumo-host node) + ClusterIP Service |

## Apply

```sh
export KUBECONFIG=$(realpath ../lima-k3s/kubeconfig)
kubectl apply -f daemonset.yaml
kubectl -n etzhayyim-langserver rollout status ds/ollama
```

Then on each Mac-mini node (or via the local-path PVC if running in
the Lima dry-run), pull a model:

```sh
kubectl -n etzhayyim-langserver exec ds/ollama -- ollama pull gemma3:4b
kubectl -n etzhayyim-langserver exec ds/ollama -- ollama list
```

## Verify from lg-ameno

`lg-ameno`'s default env points at:

    LOCAL_LLM_ENDPOINT=http://ollama.etzhayyim-langserver.svc.cluster.local:11434/api/chat

After both manifests are applied:

```sh
kubectl -n etzhayyim-langserver port-forward svc/lg-ameno 12481:8080 &
curl http://127.0.0.1:12481/workerInfo
# expect: { …, "ollamaReachable": true, "ollamaModelInstalled": true, … }
```

## Native macOS alternative (no DaemonSet)

If you'd rather run Ollama natively on each Mac-mini (no K8s
indirection), the operationally simpler path is:

```sh
brew install ollama
ollama serve &
ollama pull gemma3:4b
```

Then override the lg-ameno env at deploy time:

```sh
kubectl -n etzhayyim-langserver set env deploy/lg-ameno \
  LOCAL_LLM_ENDPOINT=http://<mac-mini-lan-ip>:11434/api/chat
```

Trade-off: native install is faster to bring up and matches the
Path A / Path B daemon's local pattern, but you lose the K8s
service-discovery story and have to maintain per-host model state by
hand.

## Why DaemonSet over Deployment

The Ollama API is per-host-affine: each pod owns a local model cache
and a GPU/CPU context. A single Deployment with N replicas would
scatter requests across pods that don't share weights and would force
a model pull on every fresh replica. DaemonSet + node-affine
`lg-ameno` scheduling keeps decode latency tight and model cache hit
rate at 100% per node.

## Limitations

- The `ollama/ollama:0.5.4` image does NOT include any pre-pulled
  models. First request after pod start = first-pull latency
  (~30-60s for Gemma 3:4b). Mitigate via a `lifecycle.postStart` hook
  in a follow-up PR if it becomes painful.
- DaemonSet on virtual-kubelet (Mac-native nodes) depends on
  murakumo-agent's ability to translate "DaemonSet pod" into a native
  process spec. If that's missing, fall back to the native macOS
  install path above.

## License

Apache-2.0.
