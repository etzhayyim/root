---
id: adr-2605173100-gitguardian-incident-response
title: "ADR-2605173100: GitGuardian Kotoba/Datomic credential-leak incident response — full remediation 2026-05-17"
status: active
doc_type: adr
topic: gitguardian-incident-response
authoritative: true
last_verified: 2026-05-17
priority: 8.5
axis: security
weight: 0.85
priority_note: "Security incident response — high priority. Documents the discovered RW network/auth posture, the multi-layer remediation, and the defense-in-depth pattern adopted afterwards. Required reading before touching RW infra or 1Password vault entries."
authoritative_for:
  - GitGuardian 2026-05-17 incident response narrative
  - Kotoba/Datomic network exposure decision (ClusterIP, no public LB)
  - Kotoba/Datomic root user authentication enforcement
  - CF Tunnel + Hyperdrive private-origin pattern for upstream DBs
  - 1Password custody for the rotated RW root password
  - lefthook secret-scan hook regex
  - filter-repo policy
depends_on:
  - adr-2605172000-etzhayyim-kotoba-substrate
related: []
supersedes: []
superseded_by: []
---

# ADR-2605173100: GitGuardian Kotoba/Datomic credential-leak incident response

**Status**: active
**Date**: 2026-05-17
**Deciders**: Jun Kawasaki

# Context

On 2026-05-17 GitGuardian flagged a PostgreSQL URI exposed in the
public `etzhayyim/root` repository:

```
postgresql://root:REDACTED_EXAMPLE_PASSWORD@45.32.79.245:4566/dev # EXAMPLE
```

The leak originated in seeded kotodama Python framework content. ~50 worker
`*_worker_main.py` files contained the URI as the **fallback** in
`os.getenv("DATABASE_URL", "<full-DSN>")` — meaning the URI was always
the runtime value unless an env var overrode it.

The leak surfaced four security-posture issues, only one of which we
expected:

## What we expected (the GitGuardian alert)

- A real password in source → must scrub HEAD + history + rotate.

## What we discovered while remediating

1. **Kotoba/Datomic root user had no password enforcement.** Testing in-cluster
   with empty / leaked / bogus passwords all returned the same
   `SELECT 1 → 1` result. The chart's `kotoba` Secret had
   `root-password = ""` (helm chart default for v0.2.49). The 32-char
   string `rw_66a4…` in source was a **placeholder, not a real password**.

2. **The Kotoba/Datomic LoadBalancer was wide-open to the public internet.**
   `kubectl get svc kotoba -o jsonpath='{.spec.loadBalancerSourceRanges}'`
   returned empty. The external IP `45.32.79.245:4566` was reachable from
   anywhere with no authentication required.

3. **Vultr VKE-managed LoadBalancers reject K8s-level firewall config.**
   `spec.loadBalancerSourceRanges` is silently ignored. The Vultr API
   refuses direct PATCH on VKE-attached LBs ("`Load Balancer is part of
   a VKE Cluster. You can only view Metrics.`").

4. **CF Hyperdrive was the only external consumer.** A leaked private IP
   for an open-access DB had no documented production caller — but CF
   Hyperdrive bindings (`HYPERDRIVE_VULTR`) were configured to use it.

# Decision

Layered defense, executed during the incident:

## Layer 1 — HEAD scrub

| Action | etzhayyim |
|---|---|
| sed-replace DSN + password literal | ✅ commit `23e499b5` |
| Strip leaked host IP `45.32.79.245` | ✅ |
| Remove compiled binary embedding the credential | ✅ |
| Files affected | 76 |

## Layer 2 — Git history rewrite (`git filter-repo`)

| Action | etzhayyim |
|---|---|
| `git filter-repo --replace-text` | ✅ 67 commits |
| Force-push to `origin` | ✅ all 3 branches |
| Backup tag | `backup/pre-filter-repo-20260517-211628` |

Replacements applied:

```
REDACTED_EXAMPLE_PASSWORD → REDACTED
45.32.79.245                         → <rw-host>
regex:postgres(ql)?://USER:PW@HOST/(dev|prod) → REDACTED_USE_DATABASE_URL_ENV
```

## Layer 3 — Pre-commit secret-scan

Added `lefthook.yml` `secret-scan` hook with regex covering:

```
postgres(ql)?://[^@]*:[^@]+@                — DSN with embedded password
sk_(live|test)_[A-Za-z0-9]{16,}             — Stripe-style secret keys
rw_[a-f0-9]{32}                              — Kotoba/Datomic password format
AWS_SECRET_ACCESS_KEY=[A-Za-z0-9/+]{16,}    — AWS env keys
github_pat_[A-Za-z0-9_]{20,}                — GitHub PATs (new format)
ghp_/ghs_/gho_/ghr_                          — GitHub PAT short prefixes
-----BEGIN [A-Z ]*PRIVATE KEY-----           — PEM private keys
```

Exclusions (whitelist tokens for documented examples):
`REDACTED`, `<rw-host>`, `example`, `fixture`, `placeholder`,
`EXAMPLE_`, `DUMMY_`, `XXXX`, `<your-`, `<insert-`, `/test/`, `_test.`,
`.test.`, `/tests/`, `.example`, `.sample`.

Commit: `da059d91`.

## Layer 4 — Network exposure removal

K8s Service `kotoba` patched LoadBalancer → ClusterIP at 21:55 JST.

Effects:
- Vultr LB id `63490c84-0b1b-4cd1-a9f8-991cf54a8c68` released by VKE CCM
- External IP `45.32.79.245` released to Vultr's pool (no longer points at our cluster)
- ClusterIP `10.100.13.171:4566` retained for in-cluster traffic
- External reachability confirmed broken (`/dev/tcp/45.32.79.245/4566` BLOCKED ✅)
- Intra-cluster confirmed working (`SELECT NOW()` from in-cluster Job → OK ✅)

Pre-patch Service spec backed up to `/tmp/kotoba-svc-backup-20260517-215515.yaml`.

## Layer 5 — Authentication enforcement

Discovery: empty `kotoba` Secret `root-password` meant no auth was
required. The chart doesn't wire the Secret into the Kotoba/Datomic
frontend's auth check; it's just a default placeholder.

Action: ran `ALTER USER root WITH PASSWORD '<32-char-from-op>'`
in-cluster via a one-shot Job, with the password sourced from a
staging Secret that was deleted at the end of the Job. The 32-char
password lives in 1Password (item `Kotoba/Datomic root (rotated 2026-05-17)`,
id `kudkk66526jk3ft4iasbezf6uy`).

Post-ALTER verification:

| Test | Expected | Actual |
|---|---|---|
| New PW + `SELECT 1` | OK | ✅ row returned |
| Empty PW | reject | ✅ `fe_sendauth: no password supplied` |
| Bogus PW (random) | reject | ✅ `ERROR: Invalid password` |
| Old "placeholder" test PW from discovery phase | reject | ✅ Invalid password |

Note: ALTER USER state is persisted in RW metastore (Postgres). Helm
chart upgrades won't reset it (the chart Secret remains empty, but
RW's metastore has the real password). If helm chart upgrade ever
explicitly runs an ALTER, this needs re-checking.

## Layer 6 — Private CF Tunnel for legitimate consumers

To keep CF Hyperdrive functional after ClusterIP-ifying RW:

```
CF Worker → Hyperdrive → CF Tunnel `kotoba-private` (id a17cdf9d-…)
        → cloudflared (in cluster, 2 replicas)
        → tcp://kotoba.kotoba.svc.cluster.local:4566 (ClusterIP)
        → Kotoba/Datomic frontend (auth-enforced)
```

Artifacts:

- CF Tunnel `kotoba-private` (id `a17cdf9d-7b9d-4cf4-a482-66129bc2a43d`)
- CF DNS CNAME `kotoba-private` (private origin)
- K8s Secret `kotoba/cloudflared-kotoba-private-credentials`
- K8s ConfigMap `kotoba/cloudflared-kotoba-private-config`
- K8s Deployment `kotoba/cloudflared-kotoba-private` (2 replicas, image `cloudflare/cloudflared:2025.4.0`)
- IaC committed at `50-infra/vultr/kotoba/private-tunnel/` (commit `684edcc9`)

Hyperdrive binding update (final step) is **pending user action in CF
Dashboard** — the CF API token in Keychain (`cloudflare:API_TOKEN`)
lacks Hyperdrive scope. README in `private-tunnel/` documents both
the dashboard path and the API-token-with-Hyperdrive-scope alternative.

## Layer 7 — Runbook for future rotations

`50-infra/vultr/kotoba/rotate-password.sh` (commit `a523b012`,
amended at `684edcc9` to reference the 1Password "compromised" item):

- Pre-flight: `op` auth check, `VULTR_API_KEY` from Keychain, kubeconfig from Vultr API
- Step 1: `op item create --generate-password='letters,digits,symbols,32'` → 1Password
- Step 2: K8s Secret update (currently a placeholder — see Layer 5 note about helm)
- Step 3: Rolling restart (when applicable for future helm-wired auth)
- Step 4: in-cluster smoke test Job
- `--dry-run` mode supported

## Layer 8 — Vultr Cloud Firewall script (defense in depth — not applied)

`50-infra/vultr/kotoba-firewall-restrict.sh` (commit `143421d5`) creates
a Vultr firewall group attachable to VKE node instances. **Not applied
in the final design** because ClusterIP (Layer 4) eliminated the public
IP entirely — Vultr firewall on nodes would be redundant for RW.

Kept as a template for similar lockdowns of other infrastructure.

# Consequences

## 正の効果

- **Public RW exposure eliminated.** No external IP points at the
  Kotoba/Datomic cluster.
- **Root user authentication enforced.** Empty / bogus / leaked
  passwords all rejected. The 32-char 1Password-managed credential is
  the only path.
- **Hyperdrive continues to work** (after dashboard reconfig) via
  private CF Tunnel — no public origin needed.
- **Pre-commit guardrail.** Future commits with credential-shaped
  strings are blocked by the secret-scan hook before reaching
  `origin/main`.
- **History clean (etzhayyim).** A snapshot of `etzhayyim/root` at any
  commit no longer contains the leaked credential.
- **Defense in depth.** Even if any one layer fails, the others
  (auth, network isolation, pre-commit) catch the attack.

## 負の効果 / コスト

- **Public IP released.** `45.32.79.245` is now in Vultr's pool and
  may be re-assigned to other Vultr customers. Anything in the wild
  configured with that exact IP gets directed to whoever Vultr assigns
  it to. Documentation referencing the old IP needs to clarify the
  IP is **historical only** and must not be redialed.
- **Existing clones of the repo retain the credential** (even after
  filter-repo on `origin`). The rotation-then-IP-restriction
  combination is what makes the leak useless, not the history rewrite.
- **Helm chart upgrades** could trigger reconcile of the `kotoba`
  Secret to empty `root-password` again. The actual auth state lives
  in RW metastore (Postgres), but a chart upgrade with explicit
  password-reset might overwrite. Need helm values override for
  long-term correctness (TODO).
- **Hyperdrive setup requires manual dashboard action.** API token
  scope expansion would let us automate; tracked.
- **Legacy-prefix npm scopes, NSIDs, and DIDs unchanged.** Those are
  Class D items (deferred cutover, scheduled with Step 8 in repo-root
  `CLAUDE.md`); they don't reference secrets. No remediation needed for
  this incident.

## Out of scope

- Other secret patterns not in our regex (e.g., specific cloud-provider
  formats we haven't seen yet)
- RW user audit (`kaisya_app`, `postgres`, `rw_admin`, `rwadmin` —
  these other roles need their own password review; the chart only
  manages `root`)
- Migration of kotodama Python framework off RW per ADR-2605172000
  (etzhayyim is kotoba; the ~50 worker `*_main.py` files referencing
  RW need a substrate-rule audit)

## Timeline (2026-05-17, JST)

| Time | Event |
|---|---|
| ~20:30 | GitGuardian alert reaches user |
| ~20:50 | etzhayyim HEAD sed-scrub committed (`23e499b5`) |
| 21:16 | etzhayyim `git filter-repo` backup tag created |
| ~21:18 | etzhayyim filter-repo + force-push complete |
| 21:35 | Lefthook secret-scan hook committed |
| 21:45 | First `op` password generation (initial PW, later archived) |
| 21:50 | Second `op` password generation (canonical, `kudkk66526jk3ft4iasbezf6uy`) |
| 21:51 | Discovery: RW root has no auth enforcement |
| 21:55 | K8s Service patched LoadBalancer → ClusterIP |
| 21:57 | `ALTER USER root WITH PASSWORD` run; empty PW now rejected |
| 22:00 | CF Tunnel `kotoba-private` created; cloudflared deployed (2/2) |
| 22:01 | Private CNAME for `kotoba-private` published |
| 22:05 | IaC manifests + ADR committed |

## Lessons learned

1. **A `os.getenv(VAR, default)` fallback is not "a placeholder" — it
   IS the production value when the env var isn't set.** Treat all
   such defaults as committed credentials.
2. **Chart default Secrets are not auth wiring.** Empty `root-password`
   meant "no auth", not "set this externally". Audit before relying.
3. **Some cloud LBs ignore K8s firewall directives.**
   `loadBalancerSourceRanges` works on AWS / GCP / Azure but not on
   some smaller providers including Vultr VKE. Verify per-provider.
4. **Defense in depth is not over-engineering.** This incident had
   network exposure AND no auth AND a leaked credential — each layer
   independently masked a fault. Layering all of them is the only
   reason post-incident posture is acceptable.

# Alternatives Considered

## A. Just rotate the leaked password

Generate new PW in 1Password, apply via K8s Secret, restart RW. Done.

却下理由: discovery showed RW had NO password enforcement — rotating
a password that wasn't being checked is meaningless. The actual problems
were (a) wide-open network and (b) no auth wiring. Layer 5 (ALTER USER)
is what made auth real; rotation alone would have left the system open.

## B. Vultr Cloud Firewall on node instances

Attach a Vultr firewall group to the 3 VKE node instances. Allowlist
specific source IPs for port 30453 (NodePort backing the LB).

却下理由: Vultr firewall is allowlist-only and the rules conflict with
internal cluster traffic patterns (any allowed external port also affects
internal). ClusterIP (no public IP at all) is cleaner. The firewall
script is kept as a template (Layer 8) for cases where ClusterIP isn't
acceptable.

## C. K8s NetworkPolicy

Restrict ingress at the K8s layer via Cilium CNI's NetworkPolicy.

却下理由: NetworkPolicy controls intra-cluster pod-to-pod traffic. It
doesn't affect the LoadBalancer external IP → NodePort → Service path.
Cilium can do this via CiliumNetworkPolicy + L7 but adds complexity.
ClusterIP achieves the same outcome by structurally removing the path.

## D. Keep LB, add ALL CF egress CIDRs to `loadBalancerSourceRanges`

Allow Hyperdrive (from CF edges) by listing CF's published egress
ranges in `loadBalancerSourceRanges`.

却下理由: (1) Vultr VKE ignores `loadBalancerSourceRanges`. (2) CF's
egress range is large and changes; maintaining the list is brittle.
(3) Even if it worked, leaked credentials would still grant root from
any CF Worker (since CF is a multi-tenant network — any CF customer
could potentially route through their workers). CF Tunnel + Hyperdrive
specifically binds the connection to OUR account's tunnel, much
narrower.

## E. Defer RW auth-enable until helm values can be properly overridden

Just lock the network; leave RW open within the cluster.

却下理由: defense in depth. Future intra-cluster supply-chain
compromise (e.g., a single misconfigured pod gaining lateral access)
would have full root SELECT without auth. ALTER USER took 2 minutes;
deferring it has no upside.

# References

- ADR-2605172000 — etzhayyim/root kotoba substrate (the workers
  containing the leak should arguably not live in etzhayyim/root)
- Cloudflare Hyperdrive over Tunnel:
  https://developers.cloudflare.com/hyperdrive/configuration/connect-to-private-database/
- Kotoba/Datomic user management:
  https://docs.kotoba.com/sql/commands/sql-alter-user
- 1Password CLI item-create:
  https://developer.1password.com/docs/cli/item-create/
- Pre-incident state references:
  - `50-infra/vultr/kotoba/deploy.sh` — original deploy with `HYPERDRIVE_VULTR` mention
  - `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/llm.py` — one of ~50 worker files with the leaked default
- Post-incident commit chain:
  - `23e499b5` HEAD scrub
  - `da059d91` secret-scan hook
  - `143421d5` Vultr firewall script (not applied; template)
  - `a523b012` 1Password rotation runbook
  - `684edcc9` CF Tunnel IaC + Hyperdrive runbook
  - `git filter-repo` rewrite on etzhayyim (backup tag `backup/pre-filter-repo-20260517-211628`)
