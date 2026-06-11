---
id: adr-2605102100-runpod-declarative-ansible
title: "RunPod pods declarative via Ansible (no tfstate, no Pulumi)"
status: accepted
doc_type: adr
topic: gpu-infrastructure
authoritative: true
last_verified: 2026-05-10
authoritative_for:
  - RunPod pod provisioning convention (manifest + role + reconcile)
  - Secret resolution path for RunPod env vars
  - Pod naming → manifest → API state SSoT chain
depends_on:
  - adr-2605010000
  - adr-2605092345-runpod-l40s-fp8-multimodal-model-design
related:
  - wellbecoming-karma-lean-proofs
  - 60-apps/etzhayyim-project-comfyui/ansible/        # earlier L40S precedent
supersedes: []
superseded_by: []
---

# Goal

Replace the manual web-UI / `runpodctl` provisioning of RunPod pods
with a declarative source-of-truth flow that fits the existing repo
patterns. Specifically: each pod has one YAML manifest, one
`ansible-playbook` invocation reconciles the pod to that manifest,
and secrets stay in 1Password.

# Scope

In scope:

- **Pod** resource — create, lookup-by-name, terminate, wait-for-RUNNING.
- **Network volume** *reference* (not creation) — manifests can pin an
  existing `networkVolumeId`; volume creation is a one-off web UI step
  for now and out of scope here.
- **Env vars** for the pod, including 1Password-resolved secrets.

Out of scope (deferred to follow-up ADRs if the need crystallizes):

- Network volume / Container Registry creation.
- Endpoint / Serverless deploys.
- Cross-pod resource graphs (e.g. one volume → many pods); the current
  pattern is "one manifest = one pod, one volume id at most".

# Executive Summary

| Layer | Decision |
|---|---|
| Tool | **Ansible** (`ansible-core ≥ 2.16`) |
| Why not Terraform | No reliable RunPod provider; `tfstate` puts the API key at risk of plaintext leak |
| Why not Pulumi | Adds a new toolchain to the repo; ROI low for a 2-pod fleet today |
| Manifest format | YAML in `50-infra/runpod/ansible/host_vars/<host>.yaml` |
| Reconcile transport | RunPod GraphQL via `ansible.builtin.uri`, run from `localhost` |
| State | RunPod's own API (no local state file, no `tfstate`) |
| Secrets | `op://...` URIs in manifests, resolved at apply-time via the local `op` CLI; never written to disk; tasks that touch secret values use `no_log: true` |
| Idempotency | Lookup by `runpod_pod_name` first; create only if missing; terminate only if found |
| Drift detection | Best-effort via `--check` + `myself.pods` diff. Strong drift is out of scope; pods are short-lived |

# Decision

## 1. Directory layout

```
50-infra/runpod/ansible/
├── ansible.cfg                       transport=local, no SSH
├── inventory.yaml                    one logical host per pod
├── group_vars/all.yaml               api endpoint, op:// API key lookup
├── host_vars/                        per-pod manifests (the SSoT)
│   ├── h100_training.yaml
│   └── six_thousand_ada_inference.yaml
├── roles/runpod_pod/
│   ├── defaults/main.yaml            spec/env defaults
│   └── tasks/
│       ├── main.yaml                 dispatch + lookup
│       ├── create.yaml               podFindAndDeployOnDemand
│       ├── terminate.yaml            podTerminate
│       └── wait_running.yaml         poll until desiredStatus=RUNNING
├── playbooks/
│   ├── apply.yaml                    runpod_pod_state=present
│   └── destroy.yaml                  runpod_pod_state=absent
└── README.md
```

## 2. Manifest contract

Required keys in `host_vars/<host>.yaml`:

- `runpod_pod_name`     — string, unique-per-account
- `runpod_pod_spec`     — dict matching `PodFindAndDeployOnDemandInput`
  (gpuTypeId, gpuCount, imageName, ports, volumeInGb,
  containerDiskInGb, optional networkVolumeId, optional
  regionPreference, etc.)
- `runpod_pod_env`      — dict, values may be plain strings or `op://...`
  references

Optional metadata (for `deps.toml` cross-references and audit):

- `runpod_purpose`      — `training-only` / `inference-only` / `mixed`
- `runpod_disposition`  — `ad_hoc` / `always_on` / `legacy`
- `runpod_adr_link`     — id of the ADR that justifies the pod's existence

## 3. Reconcile semantics

`apply.yaml` walks the limited host set and for each one runs the
`runpod_pod` role with `runpod_pod_state=present`:

1. Validate manifest shape (`assert`).
2. `myself.pods` GraphQL query → match by `runpod_pod_name`.
3. If found: pin its id+status as facts and skip create.
4. If not found: resolve `op://` env values, call
   `podFindAndDeployOnDemand`, register the new id.
5. `wait_running.yaml` polls `pod(id)` until `desiredStatus=RUNNING`
   or the timeout (`runpod_wait_timeout_seconds`, default 600 s).
6. Surface `runpod_pod_id`, `runpod_pod_status`, `runpod_pod_proxy_url`
   as ansible facts.

`destroy.yaml` does the inverse: lookup by name → if found, call
`podTerminate`; if not found, no-op exit.

## 4. Secret handling

- The single RunPod API key is read once via the local `op` CLI in
  `group_vars/all.yaml`. URI uses the **vault id**, not the vault
  name — `op read` rejects CJK characters in secret references and
  the vault is named `etzhayyim Japan株式会社`. The vault id
  `dk3qlcuqumtoml2oaxrs5mwiji` is exposed as `op_vault_id` so every
  manifest can build URIs like
  `op://dk3qlcuqumtoml2oaxrs5mwiji/etzhayyim.runpod/RUNPOD_API_KEY/password`.
- Per-pod env values that start with `op://` are resolved inside the
  role's `create.yaml` under `no_log: true`, never echoed to console
  or written to disk.
- The role intentionally does NOT cache secrets; every run re-reads
  from `op`. If the operator's 1Password session has expired, the
  apply fails before touching RunPod.

### 1Password entry inventory (verified 2026-05-10)

The H100 training manifest's env block depends on a fixed set of op
entries. Existing (read OK via vault-id URI):

- `etzhayyim.runpod/RUNPOD_API_KEY` (control plane)
- `etzhayyim.hf/HF_TOKEN`
- `etzhayyim.b2/ACCESS_KEY_ID`, `etzhayyim.b2/SECRET_ACCESS_KEY`,
  `etzhayyim.b2/ENDPOINT_URL`, `etzhayyim.b2/REGION` (S3-compat — matches
  `training_export.py` env-var convention)

Missing — must be created before first H100 apply:

- `etzhayyim.runpod-training/AUTH_TOKEN` — bearer the H100 pod's
  `kotodama.training_http_server` expects on `/train/run` and
  `/train/status/*`. Distinct from `RUNPOD_API_KEY`. Single
  `password` field, value = random 32-byte hex shared with the pod.

The H100 manifest's env-var names match what training_run.py /
training_export.py / training_http_server.py actually consume, so
the manifest stays the SSoT for both 1Password references AND the
pod's runtime configuration.

## 5. Pod naming → API state SSoT chain

```
host_vars/h100_training.yaml          (manifest, in repo, version-controlled)
        ↓ runpod_pod_name = "etzhayyim-h100-train"
RunPod GraphQL myself.pods            (live state, queried per apply)
        ↓ id = "mcax1y64ihgw4u"
deps.toml [invariants.runpod_pods]    (audit table, hand-updated when a pod is provisioned)
```

The repo-side SSoT is the manifest. The id assigned by RunPod is a
secondary artifact recorded in `deps.toml` for cost / topology
visibility.

# Comparison

|  | Ansible (this ADR) | Pulumi runpod-native | Terraform 3rd-party |
|---|---|---|---|
| RunPod-aware abstraction | No (URI module) | Yes (Pod / NetworkVolume / Endpoint) | Limited (Pod only on most providers) |
| State | None — API is state | Pulumi backend (Cloud or S3) | tfstate |
| Secret leak risk in state | None | Configurable | High (tfstate plaintext) |
| Repo precedent | L40S Ansible (`60-apps/etzhayyim-project-comfyui/ansible/`) | None | Vultr Terraform |
| New toolchain | None | Yes | Mostly no |
| Drift detection | Weak | Strong | Strong |
| Resource graph | None | Strong | Strong |
| Bus factor of provider | Self (we own the URI calls) | Public RunPod org repo | Single-maintainer GitHub repos |

For our current 2-pod fleet, Ansible's "no state, no toolchain" wins
on security (no key in tfstate) and onboarding (anyone with `op`
auth can apply). The cost is no real drift detection — acceptable
because:

- The ad-hoc training pod has a very short lifetime (provision →
  train → terminate within hours).
- The always-on 6000 Ada has manual-only operational changes; a
  weekly `apply --check` is sufficient drift surveillance.

If the fleet grows past ~5 pods or we need cross-pod resource
graphs (one volume serving many pods, etc.), revisit and migrate to
Pulumi.

# Exceptions

- **Volume / Endpoint creation** are out of scope. If/when needed,
  add `roles/runpod_volume/` and `roles/runpod_endpoint/` siblings
  with the same idempotency-by-name pattern.
- **Pod resize** is not supported — manifest changes that conflict
  with a live pod's spec require a manual destroy + apply. The
  `myself.pods` lookup explicitly does not diff spec fields.
- **Multi-account RunPod** is not supported; a single
  `RUNPOD_API_KEY` is assumed.

# Status

Implemented 2026-05-10:

- Role `runpod_pod` with create / terminate / wait_running tasks.
- `apply.yaml` / `destroy.yaml` playbooks.
- Two manifests: `h100_training` (Baien-MX step 6 trigger,
  ADR 2605092345 + 2605101000) and `six_thousand_ada_inference`
  (ADR-2605010000).
- Pod audit table at `deps.toml [invariants.runpod_pods]`
  cross-references each manifest to its assigned pod id and
  current `status` (`not_provisioned` | `running` | `terminated`).

`ansible-playbook --syntax-check` passes for both playbooks. End-to-
end apply against live RunPod is gated on:

1. The operator's `op` session being authenticated to the
   `etzhayyim Japan株式会社` vault (vault id
   `dk3qlcuqumtoml2oaxrs5mwiji`).
2. `op://dk3qlcuqumtoml2oaxrs5mwiji/etzhayyim.runpod-training/AUTH_TOKEN/password`
   existing — **still missing as of session-close 2026-05-10**.
   Create as a `Password`-category item with a single `password`
   field set to `openssl rand -hex 32` output, shared between the
   manifest and the H100 pod's `kotodama.training_http_server`
   bearer check. This is the only remaining gate before
   `ansible-playbook --limit h100_training playbooks/apply.yaml`
   can run end-to-end and unblock Baien-MX step 6.

After a successful apply, copy the assigned pod id into
`deps.toml [invariants.runpod_pods.h100_training].pod_id` and flip
`status = "running"` so the audit table stays current.

# References

- wellbecoming-karma-lean-proofs
- 60-apps/etzhayyim-project-comfyui/ansible/ (L40S Ansible precedent)
- ADR 2605010000 (6000 Ada unified pod)
- ADR 2605092345 (H100 training pod)
- ADR 2605101000 (Baien-MX, the immediate consumer of declarative H100 provisioning)
- RunPod GraphQL: https://docs.runpod.io/api-reference (official API)
