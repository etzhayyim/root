# Local LLM Agent Daemon Runbook

This runbook starts the active-inference supervisor on a local machine. The
daemon keeps the loop resident; the local LLM is only called as a planner.
Real-world effects remain proposals until BPMN gates, scoped capabilities,
policy refs, budgets, and payload-hash checks pass. Per-action human approval
is not part of the autonomous runtime path; the runtime contract is scoped
autonomous authority plus receipted effects.

## Runtime Model

```text
launchd / shell
  -> pymagatama.agent_daemon_main
  -> local LLM HTTP endpoint
  -> agent_active_inference_tick BPMN when Zeebe mode is enabled
```

## Local LLM

Default provider is Ollama:

```bash
ollama serve
ollama pull qwen3:14b
```

Override with environment variables:

```bash
export LOCAL_LLM_PROVIDER=ollama
export LOCAL_LLM_ENDPOINT=http://127.0.0.1:11434/api/chat
export LOCAL_LLM_MODEL=qwen3:14b
```

## Dry Run

Dry run calls the local LLM and logs the BPMN variables without starting Zeebe.

```bash
cd 20-actors/magatama/py
PYTHONPATH=src \
AGENT_DAEMON_MODE=dry-run \
AGENT_AUTONOMOUS_EFFECTS=0 \
python3 -m pymagatama.agent_daemon_main --once
```

## Zeebe Mode

Zeebe mode starts `agent_active_inference_tick` every interval. For local dev,
keep a port-forward to the in-cluster gateway alive:

```bash
ops/local-agent/install-zeebe-port-forward.sh
ops/local-agent/agent-loop-preflight.sh
```

Deploy the agent BPMNs directly to the forwarded gateway when the graph watcher
has not deployed them yet:

```bash
ops/local-agent/deploy-agent-bpmn.sh
```

```bash
cd 20-actors/magatama/py
PYTHONPATH=src \
ZEEBE_GATEWAY=127.0.0.1:26500 \
AGENT_DAEMON_MODE=zeebe \
AGENT_TICK_INTERVAL_SEC=300 \
AGENT_AUTONOMOUS_EFFECTS=0 \
python3 -m pymagatama.agent_daemon_main
```

If `ZEEBE_GATEWAY` is missing, the daemon falls back to dry-run.

## Autonomous Effects

Set `AGENT_AUTONOMOUS_EFFECTS=1` to make the daemon start
`agent_realworld_autonomous_dispatch` for each LLM-produced
`realWorldEffectProposals[]` item that contains an `autonomousAuthorityRef` and
`policyRef`.

`autonomousAuthorityRef` is treated as a predelegated `authority_ref`, not a
live human approval request. Inline `policy` may further narrow it with
`allowedChannels`, `allowedEffectClasses`, `allowedRecipientDomains`,
`maxPayloadBytes`, `budgetRef`, `expiresAt`, and `signatureRef`. High-risk
channels/classes must provide `specificPredelegation: true`; otherwise the
dispatch plan returns `specific_predelegation_required` and stays blocked.

```bash
cd 20-actors/magatama/py
PYTHONPATH=src \
ZEEBE_GATEWAY=127.0.0.1:26500 \
AGENT_DAEMON_MODE=zeebe \
AGENT_AUTONOMOUS_EFFECTS=1 \
AGENT_DEFAULT_POLICY_REF=policy://agent/autonomous-email-v1 \
python3 -m pymagatama.agent_daemon_main
```

The proposal object shape expected from the local LLM:

```json
{
  "channel": "email",
  "effectClass": "private_send",
  "targetRef": "mailto:ops@example.com",
  "autonomousAuthorityRef": "capability://agent/email/outbound/low-risk",
  "policyRef": "policy://agent/autonomous-email-v1",
  "policy": {
    "authorityRef": "capability://agent/email/outbound/low-risk",
    "policyRef": "policy://agent/autonomous-email-v1",
    "allowedChannels": ["email"],
    "allowedEffectClasses": ["private_send"],
    "allowedRecipientDomains": ["example.com"],
    "signatureRef": "sig://authority/kami-agent-email-low-risk",
    "expiresAt": "2026-12-31T23:59:59Z"
  },
  "payload": {
    "to": "ops@example.com",
    "subject": "Ping",
    "text": "hello"
  }
}
```

For email, `from` may be omitted. `agent.planRealWorldDispatch` derives it as
`{agent-id}@etzhayyim.com`; for example `did:web:kami-agent.etzhayyim.com` becomes
`kami-agent@etzhayyim.com`. This relies on the Resend-verified `etzhayyim.com` sender
domain behind `mailer.sendEmail`.

Smoke-test the planner without sending:

```bash
cd 20-actors/magatama/py
PYTHONPATH=src \
python3 -m pymagatama.agent_email_smoke \
  --agent-did did:web:kami-agent.etzhayyim.com \
  --to ops@example.com
```

To actually call Resend through the Python mailer handler, add `--live` and
ensure `RESEND_API_KEY` or `SS_RESEND_API_KEY` is present in the worker
environment.

After a channel worker returns a receipt, `agent.buildDispatchReceiptObservation`
converts it into a `vertex_agent_observation` row. The next active-inference
tick can therefore see external action results as world observations.

Inline policy can be carried on each proposal:

```json
{
  "policy": {
    "allowedChannels": ["email"],
    "allowedRecipientDomains": ["etzhayyim.com", "example.com"],
    "maxPayloadBytes": 10000
  }
}
```

The daemon suppresses duplicate dispatch proposals within the running process.
The BPMN path also writes `vertex_agent_dispatch_ledger` keyed by
`dispatchPlanId` and sends only when that insert is new.

## macOS launchd

Use `ops/local-agent/com.etzhayyim.agent-daemon.plist.example` as the template.
The plist calls the `magatama-agent-daemon` console script directly and the
CLI loads `ops/local-agent/agent-daemon.env`.

The dedicated local Zeebe worker uses the `magatama-agent-zeebe-worker` console
script directly through the `ops/local-agent/com.etzhayyim.agent-zeebe-worker.plist.example`
template. The shell scripts remain as compatibility wrappers, but launchd does
not depend on them.

Install in dry-run mode first:

```bash
ops/local-agent/install-launchd-agent.sh
```

Logs:

```bash
tail -f /tmp/com.etzhayyim.agent-daemon.out.log /tmp/com.etzhayyim.agent-daemon.err.log
```

Live organism status:

```bash
AGENT_DAEMON_ENV_FILE=ops/local-agent/agent-daemon.env \
  20-actors/magatama/py/.venv/bin/magatama-agent-status
```

The status command reads launchd state plus Kotoba/Datomic homeostasis, outcome,
learning, real-world effect, and dispatch ledger rows. It reports the current
organism state (`active`, `repairing`, `degraded`, `critical`, or `unknown`)
and a bounded score for quick operator checks.

Read-only WebUI:

```bash
AGENT_DAEMON_ENV_FILE=ops/local-agent/agent-daemon.env \
  20-actors/magatama/py/.venv/bin/magatama-agent-status-web
```

Open `http://127.0.0.1:8765`. The WebUI is intentionally read-only in this
phase. It polls `/api/status` and renders organism state, homeostasis,
outcome, learning priors, launchd processes, observations, real-world effects,
and dispatch ledger counts from the same status surface as the CLI.
Use `ops/local-agent/com.etzhayyim.agent-status-web.plist.example` when the WebUI
should stay resident under launchd.

ERC-8004 local registration draft:

```bash
AGENT_DAEMON_ENV_FILE=ops/local-agent/agent-daemon.env \
  20-actors/magatama/py/.venv/bin/magatama-agent-erc8004 \
  --upsert-profile \
  --out 90-docs/proof/kami-agent-erc8004-registration.local.json
```

This renders a public ERC-8004-compatible agent registration document from the
same organism status surface and upserts `vertex_agent_economy_profile` with
the current `erc8004_agent_id`.

ERC-8004 IPFS publication and chain registration:

```bash
AGENT_DAEMON_ENV_FILE=ops/local-agent/agent-daemon.env \
  20-actors/magatama/py/.venv/bin/magatama-agent-erc8004 \
  --agent-did did:web:kami-agent.etzhayyim.com \
  --out 90-docs/proof/kami-agent-erc8004-registration.local.json \
  --publish-ipfs \
  --submit-chain \
  --no-dry-run \
  --publish-proof-out 90-docs/proof/kami-agent-erc8004-publish-attempt.local.json
```

The command publishes the generated registration JSON to `https://ipfs.etzhayyim.com`
and then calls `etzhayyim agent-runtime register`, which submits
`etzhayyimAgentRegistry.registerAgent(...)` on chain `260425`. It fails closed before
IPFS/chain writes when the registration still contains unsafe placeholders such
as a zero `rootIdentity.address`.

Required local secrets and identity values:

```bash
security find-generic-password -s etzhayyim.cloudflare -a IPFS_HMAC -w
security find-generic-password -s etzhayyim.private-chain -a SEALER_PRIV -w
```

`ops/local-agent/agent-daemon.env` must contain a real
`AGENT_ERC725_ROOT_ADDRESS`, `AGENT_ERC725_ROOT_DID`, and any policy CIDs that
should be part of the public registration. After the transaction returns an
agent token id, set `AGENT_ERC8004_AGENT_ID` and restart the status WebUI so
`/api/status` reports the on-chain identity.

Switch to the full loop by editing `ops/local-agent/agent-daemon.env`:

```bash
AGENT_DAEMON_MODE=zeebe
AGENT_AUTONOMOUS_EFFECTS=1
ZEEBE_GATEWAY=127.0.0.1:26500
```

Then restart:

```bash
launchctl stop com.etzhayyim.agent-daemon
launchctl start com.etzhayyim.agent-daemon
```

Stop and remove the LaunchAgent:

```bash
ops/local-agent/uninstall-launchd-agent.sh
ops/local-agent/uninstall-zeebe-port-forward.sh
```

## Autonomous Effect Boundary

The daemon does not call mail, fax, browser, phone, print-mail, robotics, or
public-post surfaces directly. It emits:

- `observations`
- `candidateActions`
- `realWorldEffectProposals`
- `viability`

Effectful dispatch continues through `vertex_agent_realworld_effect`,
`agent.planRealWorldDispatch`, scoped `capability://...` authority refs,
payload hashes, rate/budget policy, and channel-specific BPMN workers.

Supported autonomous bridge targets in this phase:

| Channel | Task type | Receipt |
|---|---|---|
| Email | `mailer.sendEmail` | `messageId` |
| Fax | `fax.send` | `txId` |
| Print-mail | `insatsu.printMailJob.createPrintMailJob` | `jobId` |

Phone, robotics, browser form submission, public posting, audio, video, and
image publishing stay blocked until their channel workers expose bounded
capability contracts and receipts.

The BPMN process that performs the first live path is
`agent_realworld_autonomous_dispatch`. In Phase A it can reach
`mailer.sendEmail`; other channels stop at the dispatch-plan blocker/audit path.
