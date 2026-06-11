# lima-k3s — etzhayyim K3s HA dry-run

Stand up a 3-node K3s embedded-etcd HA cluster as Lima VMs on a single
Mac mini for the M1 milestone of ADR-2605191346.

ADR: [`90-docs/adr/2605191346-etzhayyim-vultr-free-murakumo-control-plane.md`](../../../90-docs/adr/2605191346-etzhayyim-vultr-free-murakumo-control-plane.md)

## Why this scaffolding

ADR-2605191346 ("etzhayyim is Vultr-free") makes the Murakumo Mac-mini
fleet the only Tier-1 substrate. For HA stateful workloads (geth-private,
atproto-pds, langserver pods) we still want K8s — but the control plane
must live **on the fleet**, not on Vultr / EKS / GKE.

The cheapest path to validate the topology before committing to bare-metal
Mac mini cluster build-out is **three Lima VMs on one Mac mini**:

- exactly the same K3s embedded-etcd HA shape as the eventual 3-physical-Mac-mini
  cluster
- one Mac mini's worth of resources (12 GiB RAM + 90 GiB sparse disk)
- can be torn down and re-created in minutes
- exercises the same kubectl / kubeconfig / cloudflared paths as production

If this scaffolding works, the migration to 3 physical Mac minis is just
"use `--name=k3s-server-0X` on three hosts instead of one".

## Files

| file | role |
|---|---|
| `lima-k3s-server.yaml` | Lima template — Ubuntu 24.04, 2 vCPU / 4 GiB RAM / 30 GiB disk, K3s installer staged |
| `bring-up.sh` | idempotent automation: 3 Lima VMs → K3s server (cluster-init + 2 joins) → kubeconfig export |
| `verify.sh` | 5 gates: cluster-info, 3 Ready nodes, 3 etcd members, default StorageClass, cross-VM pod networking |
| `teardown.sh` | clean removal of all three VMs and kubeconfig |
| `kubeconfig` | (generated) exported kubeconfig pointing at VM 1's IP |

## Prereqs

| | install |
|---|---|
| **Lima** ≥ 2.0 | `brew install lima` |
| **socket_vmnet** | `brew install socket_vmnet && sudo brew services start socket_vmnet` (needed for VM-to-VM networking on macOS) |
| **kubectl** | `brew install kubectl` |
| **jq** | `brew install jq` |
| **RAM** | ~12 GB free |
| **Disk** | ~90 GB free (sparse qcow2) |

If you skip `socket_vmnet` Lima falls back to slirp NAT and the
3 VMs can't see each other — bring-up.sh checks for this and exits early.

## Bring-up

```sh
cd 50-infra/k8s/lima-k3s
./bring-up.sh
```

Expected output (last lines):

```
✅ K3s HA dry-run cluster is up.
   kubeconfig:   /…/lima-k3s/kubeconfig
   API server:   https://192.168.105.X:6443
   token:        etzhayyim-k3s-dryrun-2026
```

`bring-up.sh` is idempotent: re-running after a partial failure resumes
from the right step.

## Verify

```sh
./verify.sh
```

Passes when:

1. ✅ API server reachable from host kubeconfig
2. ✅ All 3 nodes show `Ready`
3. ✅ All 3 are etcd members (HA quorum)
4. ✅ Default StorageClass is `local-path` (k3s built-in)
5. ✅ Pods on different VMs can speak TCP to each other (flannel CNI works)

`verify.sh` cleans up the test namespace on exit.

## Quick smoke from the host

```sh
export KUBECONFIG=$(pwd)/kubeconfig

kubectl get nodes -o wide
# NAME             STATUS   ROLES                       AGE   VERSION
# k3s-server-01    Ready    control-plane,etcd,master   3m    v1.31.x+k3s1
# k3s-server-02    Ready    control-plane,etcd,master   2m    v1.31.x+k3s1
# k3s-server-03    Ready    control-plane,etcd,master   1m    v1.31.x+k3s1

kubectl get pods -A
# kube-system    coredns-…             Running
# kube-system    local-path-provisioner-…  Running
# kube-system    metrics-server-…      Running
# kube-system    traefik-…             Running

kubectl get sc
# NAME                 PROVISIONER             RECLAIMPOLICY   …
# local-path (default) rancher.io/local-path   Delete
```

## Teardown

```sh
./teardown.sh
```

All three VMs are stopped and deleted, and the kubeconfig is removed.

## Going from dry-run to production (M1 → M2)

Spreading across 3 physical Mac minis is mechanical:

1. On each Mac mini, install Lima + socket_vmnet + kubectl
2. Adjust `bring-up.sh`:
   - Set `VMS=(k3s-server-0X)` to **one** VM per Mac mini (not three on one host)
   - Run bring-up.sh on Mac mini 01 first (it picks up `cluster-init`)
   - Then on 02 and 03 with `FIRST_IP=<mac01.lan.ip>` env exported (small refactor of the script — currently it discovers IP via `vm_ip` for an in-host neighbour; for cross-host we pass it in)
3. Front the cluster with Cloudflare Tunnel:
   - `cloudflared tunnel create etzhayyim-k3s`
   - point `*.etzhayyim.com` ingresses at `https://k8s-01.local:6443` via tunnel config

When the bare-metal topology is validated, this directory's Lima
template moves to `_archive` and a `bare-metal/` sibling takes over.

## Limitations of dry-run

- **One host = one failure domain.** True HA only after 3 physical hosts.
- **socket_vmnet performance.** ~1 Gbit/s between VMs on a Mac mini — fine
  for control-plane chatter, may be tight under heavy pod-to-pod traffic.
- **Lima VM IP not stable across `limactl stop/start`.** Bring-up.sh
  re-exports kubeconfig each run; consumers should `KUBECONFIG=…` not
  assume a fixed address.

## Troubleshooting

| symptom | likely cause | fix |
|---|---|---|
| `bring-up.sh` aborts: "socket_vmnet not found" | brew install missing | `brew install socket_vmnet && sudo brew services start socket_vmnet` |
| node stays NotReady | flannel CNI can't reach across VMs | check socket_vmnet service status |
| `verify.sh` cross-VM TCP fails | iptables / firewall on host blocking lima bridge | `sudo pfctl -d` (temporarily, dev only) |
| `kubectl` complains "x509 cert is for 127.0.0.1" | kubeconfig wasn't rewritten | re-run `bring-up.sh`; or manually `sed -i '' "s|127.0.0.1|<vm-ip>|" kubeconfig` |

## License

Apache-2.0.
