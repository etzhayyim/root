---
id: adr-2605232000-agent-led-autonomous-deploy
title: "ADR-2605232000: Agent-led autonomous deploy — `e7m actor` + `e7m agent-token` + capability-gated authority"
status: proposed
doc_type: adr
topic: agent-led-autonomous-deploy
authoritative: true
last_verified: 2026-05-23
priority: 7.1
axis: infrastructure
weight: 0.71
priority_note: "Closes the 'how does an autonomous agent actually deploy a new actor?' gap. Defines the declarative actor.toml manifest read by `e7m actor deploy`, the Ed25519-signed scoped JWS issued by `e7m agent-token`, and the consent-capability extension (purpose=deploy-execution) that authorizes a specific agent DID to execute a specific scope of deploy actions for a bounded window. Required by every future agent-led-deploy event."
authoritative_for:
  - "actor.toml schema and stage execution model"
  - "e7m actor / e7m agent-token CLI surface"
  - "deploy-execution consent-capability purpose semantics"
  - "DEPLOY_EVENT audit emission contract"
  - "3-tier credential model for agent deploys"
depends_on:
  - adr-2605231100-karute-emr-phase1
  - adr-2605231400-karute-consent-capability-iryo-bridge
  - adr-2605231700-audit-webhook-subsystem
  - adr-2605231900-karute-deployment-topology
related:
  - 260417-claude-agent-secret-handling
supersedes: []
superseded_by: []
---

# ADR-2605232000: Agent-led autonomous deploy

**Status**: proposed
**Date**: 2026-05-23
**Deciders**: Jun Kawasaki

# Context

Two needs surfaced concurrently during the karute deployment work (ADR-2605231900):

1. **One CLI, all the deploy surface.** Currently a karute deploy requires `wrangler deploy` × 2 + `docker build` + `kubectl apply` + `cloudflared tunnel run` + `wrangler pages deploy` + `node build-bundle.mjs`. The deploy shell script (`50-infra/karute-deploy.sh`) wraps these but is per-actor — every new actor reinvents the orchestration. Move the orchestration into `e7m` so the CLI knows how to deploy any actor that declares an `actor.toml`.

2. **Autonomous agents need to deploy without typing.** A Claude / autonomous-cell / scheduled-runbook agent that adds a new actor to the ecosystem should be able to execute the deploy without (a) appearing in the chat transcript with credentials, (b) requiring human OAuth flows mid-deploy, (c) bypassing audit controls. Per the agent-secret-handling note (260417-claude-agent-secret-handling.md):

    > Don't put long-lived secrets into the transcript. Prefer short-lived + scoped tokens over long-lived roots. Make rotation a 1-liner.

But the existing primitives only cover **runtime** XRPC calls (`etzhayyim agent-token --lxm com.etzhayyim.apps.gmail.syncInbox --ttl 60`). Deploy-time authority — "this agent may run `wrangler deploy` against the `karute-did-web` Worker and `kubectl apply` against `lg-karute`" — has no formalized capability.

Both problems share a solution shape: a declarative manifest + a capability-gated executor + audit emission per step.

# Decision

## Three artifacts

### 1. `actor.toml` — declarative deployment manifest

Each actor that wants to be deployable via `e7m actor` ships a top-level `actor.toml` in its `20-actors/<name>/` directory:

```toml
[actor]
name = "karute"
did = "did:web:karute.etzhayyim.com"
nanoid = "karu7t3e"
manifest = "20-actors/karute/actor-manifest.jsonld"
primary_adr = "90-docs/adr/2605231100-karute-emr-phase1.md"

[[stages]]
name = "did-worker"
type = "cf-worker"
working_dir = "50-infra/karute-did-web"
command = ["wrangler", "deploy"]
require_cap = ["deploy.cfWorker:karute-did-web"]
on_error = "abort"
dry_run_safe = false

[[stages]]
name = "k8s-pod-apply"
type = "k8s"
command = ["kubectl", "apply", "-f", "50-infra/k8s/lg-karute/deployment.yaml"]
depends_on = ["image-build"]
require_cap = ["deploy.k8s:lg-karute"]
…
```

Stages have a typed `type` (`cf-worker` / `cf-pages` / `k8s` / `docker-build` / `cf-tunnel` / `cmd` / `smoke`), a working directory, a command vector, and a `require_cap` list of scope NSIDs needed to execute it.

`etzhayyim actor deploy` reads the manifest, runs preflight (`wrangler` / `kubectl` / `docker` / `cloudflared` on PATH), gates each stage against the supplied capability + token, and emits a `DEPLOY_EVENT` audit row per stage.

Flags:
- `--actor <name>` (default: inferred from cwd if under `20-actors/<name>/`)
- `--only <stage>` (run a single stage)
- `--skip <stage>` (repeatable)
- `--capability <path>` (JWS file; gates which stages can run)
- `--agent-token <token>` (short-lived scoped JWT for the called services)
- `--dry-run` (print actions without executing)
- `--non-interactive` (fail on missing creds; never prompt)
- `--commit-sha <sha>` (audit record value; default HEAD)

### 2. `e7m agent-token` — scoped ephemeral JWS

Mints an Ed25519-signed JWT (JWS compact form) for a single scope, default TTL 60s, max TTL 3600s. The signing key is read from macOS Keychain (`service=etzhayyim, account=DID_PRIVATE_KEY_ED25519`) or `--key-file <path>` for the agent's own private key. Claim shape:

```json
{
  "iss": "did:web:steward.etzhayyim.com",
  "sub": "did:web:claude-agent.etzhayyim.com",
  "aud": "did:web:karute-did-web.etzhayyim.com",
  "lxm": "deploy.cfWorker:karute-did-web",
  "cap": "at://did:web:steward.etzhayyim.com/com.etzhayyim.consent.capability/3lzw1",
  "iat": 1779513922,
  "exp": 1779513982,
  "jti": "<hex16>"
}
```

The audience DID is inferred from the `lxm` prefix when not supplied. Tokens are written to stdout (`--out -`) or a file (`--out path`) — never to disk by default.

### 3. Consent capability — `purpose: "deploy-execution"`

Extends `com.etzhayyim.consent.capability` (ADR-2605231400) to cover deploy authority. A Steward issues:

```json
{
  "granterDid":  "did:web:steward.etzhayyim.com",
  "granteeDid":  "did:web:claude-agent.etzhayyim.com",
  "purpose":     "deploy-execution",
  "scope": [
    "deploy.cfWorker:karute-did-web",
    "deploy.cfWorker:audit-did-web",
    "deploy.k8s:lg-karute",
    "deploy.pages:karute"
  ],
  "expiresAt":   "2026-05-24T00:00:00Z",
  "constraints": {
    "downstreamRedistribution": false,
    "auditWebhookDid": "did:web:audit.etzhayyim.com"
  },
  "signature":   { "alg": "ed25519", "value": "...", "keyId": "..." }
}
```

`e7m actor deploy` rejects any stage whose `require_cap` is not in the capability's `scope`, with a `denied` DEPLOY_EVENT logged. The capability itself is a normal PDS record and revocable via `com.etzhayyim.apps.karute.revokeConsent` (or the generic equivalent on `did:web:audit.etzhayyim.com`).

## Three-tier credential model (for agents)

Per the secret-handling note, with the new T3 deploy specialization:

| Tier | Lifetime | Storage | Agent use |
|---|---|---|---|
| **T0 device-only** | persistent | Keychain / WebAuthn | Never share with agent. |
| **T1 long-lived root** | months | 1Password vault, CF Secrets Store | Pre-provisioned env vars or `op read` pipes; agent never sees value. |
| **T2 deploy capability** | hours-to-day | PDS record (`com.etzhayyim.consent.capability`, purpose=deploy-execution) | Agent holds the JWS file; verifiable by every downstream tool that consults the granter's DID document. |
| **T3 scoped per-call token** | 60-300s | In-memory; not persisted | Minted per stage from the T2 capability via `e7m agent-token`; passed in `Authorization: Bearer` to the actual deploy tool wrapper. |

The capability is the only piece that needs human-issued explicit consent. Everything below is mintable by the agent itself.

## Audit emission

Every stage emits a structured `DEPLOY_EVENT` line to stderr:

```
DEPLOY_EVENT {"version":1,"agentDid":"did:web:claude-agent.etzhayyim.com","stewardDid":"did:web:steward.etzhayyim.com","stage":"did-worker","target":{"nsid":"deploy.cf-worker","identifier":"karute/did-worker"},"command":"wrangler deploy","commitSha":"abc123","outcome":"ok","durationMs":4321,"occurredAt":"2026-05-23T..."}
```

Phase 2 wires this to POST `https://audit.etzhayyim.com/xrpc/com.etzhayyim.audit.emitAuditEvent` so the audit subsystem (ADR-2605231700) gets it on its hash-chained timeline. The two new lexicons supporting this:

- `com.etzhayyim.deploy.agentToken` — token-issuance audit projection (jwsHash, never the token value)
- `com.etzhayyim.deploy.deployEvent` — per-stage signed audit record

## Reference flow — full agent-led karute deploy

```bash
# (Once, per Steward) — establish T1 + T2 root
op signin
export CLOUDFLARE_API_TOKEN=$(op read 'op://Dev/cf-api-token/credential')
export GITHUB_PAT=$(op read 'op://Dev/ghcr-pat/credential')
export ETZ_STEWARD_DID=did:web:steward.etzhayyim.com

# Issue T2 deploy capability (good for 24h, scoped to karute resources)
e7m capability issue \
  --granter "$ETZ_STEWARD_DID" \
  --grantee did:web:claude-agent.etzhayyim.com \
  --purpose deploy-execution \
  --scope deploy.cfWorker:karute-did-web,deploy.cfWorker:audit-did-web,deploy.docker:lg-karute,deploy.k8s:lg-karute,deploy.pages:karute \
  --ttl 86400 \
  --audit did:web:audit.etzhayyim.com \
  --out ~/.etzhayyim/cap-karute-deploy.jws

# (Agent now has the capability JWS — everything below runs without human input)

# Per-stage T3 token + execution
export ETZ_AGENT_DID=did:web:claude-agent.etzhayyim.com

for STAGE in did-worker audit-worker image-build k8s-pod-apply k8s-pod-rollout cf-tunnel-ensure pages-build pages-deploy lexicon-bundle smoke; do
  TOKEN=$(e7m agent-token \
    --lxm "deploy.${STAGE}" \
    --ttl 300 \
    --capability "$(jq -r .capabilityUri ~/.etzhayyim/cap-karute-deploy.json)")
  e7m actor deploy \
    --actor karute --only "$STAGE" \
    --capability ~/.etzhayyim/cap-karute-deploy.jws \
    --agent-token "$TOKEN" \
    --non-interactive
done
```

The agent's local invocations of `wrangler` / `kubectl` / `docker` / `cloudflared` use the pre-provisioned T1 env vars (`CLOUDFLARE_API_TOKEN` / `GITHUB_PAT` / k8s context); the T2 capability + T3 token authorize the deploy at the **etzhayyim governance layer** (audit + revocation), separate from the cloud-provider auth.

## What this ADR does NOT change

- The encryption envelope (ADR-2605181100), the substrate boundary (ADR-2605172000), the charter (ADR-2605192100). Deploy authority composes with — does not bypass — them.
- The PHI guard hook (ADR-2605231100) still applies to source code being deployed. An agent that attempts to ship plaintext PHI fails at commit time, not at deploy time.
- The consent capability primitive (ADR-2605231400). `deploy-execution` is a new enum value; the record shape, signature semantics, and revocation flow are unchanged.

# Consequences

## 正の効果

- **One declarative manifest per actor.** Adding a new actor requires writing `actor.toml`; the deploy orchestrator is shared and battle-tested.
- **Agents can deploy without human-in-the-loop credentials.** The Steward issues one T2 capability; the agent mints T3 tokens per stage. Human is not required for individual stages.
- **Every deploy step has a signed, verifiable audit trail.** `DEPLOY_EVENT` correlates the agent DID, Steward DID, capability URI, commit SHA, and outcome — a regulator or licensure board can subpoena the timeline.
- **Capability is revocable.** Steward revokes via `revokeConsent`; agent immediately loses authority for all future stages. Already-committed deploys are not unwound, but new deploys fail closed.
- **Composes with existing primitives.** No new lexicon families; `deploy-execution` is one enum value on `com.etzhayyim.consent.capability`.
- **Stage-scope minimum privilege.** An agent authorized for `deploy.cfWorker:karute-did-web` cannot run `kubectl apply`. Per-stage capability fanout is fine-grained.
- **Dry-run is free and safe.** `--dry-run` prints the planned commands and emits `outcome="dry-run"` events without executing anything.

## 負の効果 / コスト

- **Capability JWS-verify is structural in v1.** `e7m actor deploy` parses the JWS and decodes the payload but does NOT yet verify the Ed25519 signature against the granter's DID document. Phase 2 adds the verification step. Until then, a forged JWS file can pass the gate — mitigated by the agent's runtime environment being trusted by the operator (T1 creds are still required for the actual cloud-provider call).
- **Audit emission is stderr-only in v1.** Phase 2 wires to `https://audit.etzhayyim.com/xrpc/...` once the aggregator is implemented. Until then, the parent process / CI logger / journalctl must capture stderr.
- **T1 cloud-provider creds are still long-lived.** The agent runs `wrangler deploy` which uses the human-owned Cloudflare API token. Per-stage scoping at the cloud-provider layer (CF Workers API tokens scoped to specific Workers) is a follow-up; today we rely on the etzhayyim capability layer being the audit point and CF auth being the access point.
- **No supply-chain proof.** The agent could in principle build a malicious image and run `docker push`. Mitigation: ghcr.io image signing (cosign) + capability scope that names the image SHA — both deferred.
- **`actor.toml` is a parallel manifest to `actor-manifest.jsonld`.** The former is operational (deploy-time); the latter is constitutional (runtime — actor capabilities, pipelines, governance). They reference each other but are independent files. Drift risk acknowledged.

## Rollout

1. **This commit** — ADR + 2 new lexicons (`com.etzhayyim.deploy.agentToken`, `com.etzhayyim.deploy.deployEvent`) + `purpose=deploy-execution` enum value on consent capability + 2 e7m subcommands (`actor`, `agent-token`) + karute `actor.toml`. End-to-end dry-run smoke (`etzhayyim actor deploy --actor karute --dry-run --only pages-build` → DEPLOY_EVENT emitted) verified.
2. **Phase 2** — Capability JWS Ed25519 verification + audit emission HTTP POST to `https://audit.etzhayyim.com/xrpc/com.etzhayyim.audit.emitAuditEvent`. Phase 2 also adds `e7m capability issue / revoke / list` subcommands so capability management is in-CLI.
3. **Phase 3** — Per-stage T1 cloud-provider creds (CF Workers API tokens scoped to a single Worker; GitHub PATs scoped to a single repo). Cosign + image-SHA scoping for `deploy.docker:` scopes.
4. **Phase 4** — Failure-mode test rig (revoked capability mid-deploy / expired token mid-stage / forged JWS detection).

# Alternatives Considered

## A. Shell-script-only orchestration

Keep `50-infra/karute-deploy.sh` per-actor and don't introduce e7m subcommands. Rejected because (i) every new actor reinvents the script, (ii) no audit emission unless explicitly added, (iii) capability gating is awkward in bash.

## B. Existing CI (GitHub Actions / similar)

Use GHA to deploy. Rejected because (i) introduces a non-substrate trust point — GitHub holds the deploy authority, (ii) per-step capability check would require a sidecar process anyway, (iii) `actor.toml` + `e7m actor` works equally from a developer laptop, a CI runner, and an autonomous-agent process — single code path.

## C. Service-account model (long-lived agent credentials)

Issue the agent its own long-lived Cloudflare API token + k8s ServiceAccount. Rejected as the primary model because (i) loses revocation granularity (revoking is across-the-board), (ii) the agent's authority becomes equal to the Steward's at the cloud-provider layer, (iii) audit trail rests on the cloud-provider's logs rather than the etzhayyim substrate. Service-account credentials remain available as the T1 layer; capability + agent-token sit ON TOP of them to provide the etzhayyim-governance layer.

## D. Container-image autonomous deploy bot

Stand up a long-running deploy daemon that watches a queue and dispatches builds. Rejected for v1 because (i) over-engineered for current scale, (ii) the daemon itself becomes a target for compromise, (iii) `e7m actor deploy --non-interactive` invoked from any process (CI / cron / agent loop) covers the same ground with less infrastructure.

## E. Per-stage capability JWT (no separate scoped token)

Have the capability JWS itself be the per-call authorization. Rejected because (i) capability lifetime is hours-to-days (too long for per-call auth — leaked = entire window is compromised), (ii) capability is a record stored in a PDS; tokens are in-memory ephemerals — different lifecycle is correct, (iii) splitting capability (long-lived authority claim) from token (short-lived per-call assertion) is the standard pattern (UCAN, OAuth2, JWT-based STS).

# References

- ADR-2605231100 [karute EMR Phase 1](./2605231100-karute-emr-phase1.md)
- ADR-2605231400 [karute consent capability + iryo billing bridge](./2605231400-karute-consent-capability-iryo-bridge.md)
- ADR-2605231700 [audit webhook subsystem](./2605231700-audit-webhook-subsystem.md)
- ADR-2605231900 [karute deployment topology](./2605231900-karute-deployment-topology.md)
- [260417-claude-agent-secret-handling.md](../260417-claude-agent-secret-handling.md) — 4-tier secret model
- W3C DID Core 1.0 — https://www.w3.org/TR/did-1.0/
- IETF JWT (RFC 7519) — https://datatracker.ietf.org/doc/html/rfc7519
- IETF JOSE Ed25519 (RFC 8037) — https://datatracker.ietf.org/doc/html/rfc8037
- UCAN spec — https://ucan.xyz/ (capability-with-scope predecessor)
