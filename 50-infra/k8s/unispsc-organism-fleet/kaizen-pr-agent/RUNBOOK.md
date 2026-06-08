# kaizen-pr-agent — Wave-4 enablement runbook

The self-evolution loop's **actuator**. Drains the observer's proposal queue →
applies structured patches → opens PRs / issues on `github.com/etzhayyim/root`.
Wave-4 (real PRs) **approved 2026-06-08** (Council Lv7+ unanimity, founder 1/1).

## Topology

```
levi (Mac mini):
  kaizen-observer  Deployment → /var/lib/etzhayyim/kaizen-proposals/observer.ndjson (hostPath)
  kaizen-pr-agent  Deployment ← same hostPath → PR/issue on etzhayyim/root
joseph / issachar / dan: UnispscOrganismFleetCell DaemonSets (~18,342 organisms)
```

The pr-agent is **co-located on levi** because the proposal queue is a node-local
hostPath the observer writes (multi-node read is Wave 5).

## Preconditions (operator)

1. **Cluster up + reachable.** The Murakumo k3s control plane must be running and
   your `kubectl` context must point at it. As of 2026-06-08 the fleet nodes are
   reachable over Tailscale (`tailscale status` → levi/joseph/issachar/dan up) but
   the **k3s API (6443) was not serving and no fleet kubeconfig is on `jacob`** —
   bring k3s up and fetch its kubeconfig before applying.
2. **Image has git + gh.** `ghcr.io/etzhayyim/kotodama:main` MUST ship `git` and
   `gh` on PATH (the actuator clones, branches, and runs `gh pr/issue create`).
   Verify: `kubectl run --rm -it tmp --image=ghcr.io/etzhayyim/kotodama:main -- sh -c 'git --version && gh --version'`.
   If absent, rebuild the image with them first.

## Enable

```bash
# 1. Apply the fleet (creates/updates kaizen-pr-agent alongside observer + shards)
kubectl apply -k 50-infra/k8s/unispsc-organism-fleet/

# 2. Provision the GitHub token Secret (NEVER commit it). Least-privilege,
#    short-lived, fine-grained PAT scoped to etzhayyim/root:
#      contents:write + pull_requests:write + issues:write
kubectl create secret generic kaizen-pr-agent-gh \
  -n etzhayyim-organism \
  --from-literal=token="$GH_PR_AGENT_TOKEN"

# 3. Restart so the pod picks up the Secret (optional auth is read at startup)
kubectl rollout restart deploy/kaizen-pr-agent -n etzhayyim-organism
```

## Verify

```bash
kubectl get pods -n etzhayyim-organism -l app.kubernetes.io/name=kaizen-pr-agent
kubectl logs -n etzhayyim-organism deploy/kaizen-pr-agent -f
#   "kaizen-pr-agent resident loop start: ... dry_run=False"
#   "pr-agent drain: consumed=N ..."   (N>0 once the observer has emitted proposals)
```

## Fail-safe behavior

- **No Secret yet** → `_verify_gh_auth` fails → each cycle is logged + skipped, the
  daemon stays up. No push, no crash. (Safe to apply the Deployment before the token.)
- **Stuck proposal** (non-applicable patch) → quarantined to
  `<stem>.needs-human.ndjson`; the queue keeps draining (consume_all liveness).
- **issue-only proposal** → `gh issue create`, drained (no branch/patch).

## Rollback

```bash
# Pause without deleting: scale to zero
kubectl scale deploy/kaizen-pr-agent -n etzhayyim-organism --replicas=0
# Or revert to observe-only (no actuator): set DRY_RUN back to "true"
kubectl set env deploy/kaizen-pr-agent -n etzhayyim-organism KAIZEN_PR_AGENT_DRY_RUN=true
# Or remove the token to halt pushes immediately
kubectl delete secret kaizen-pr-agent-gh -n etzhayyim-organism
```

## no-server-key (ADR-2605231525)

The token is operator-injected, short-lived, least-privilege — NOT a platform
master key. Rotate per `cell_key_rotation_period_days` (90). The Secret is never
committed (the `gh-secret.example.yaml` is a placeholder template only and is NOT
in the kustomization resource list).
