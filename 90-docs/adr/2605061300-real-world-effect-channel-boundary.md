---
id: adr-2605061300-real-world-effect-channel-boundary
title: "Real-world effect channel boundary for autonomous agents"
status: active
doc_type: adr
topic: real-world-effect-channels
authoritative: true
last_verified: 2026-05-06
authoritative_for:
  - real-world effect channel boundary
  - email web fax phone media print-mail agent action policy
  - autonomous agent dispatch gating
  - non-human-intervention delegated authority model
  - active inference action proposal effect classes
priority: 9.0
axis: gate
weight: 0.90
priority_note: "CRITICAL — governs actions that can affect external people, organizations, accounts, websites, physical mail, or public media surfaces"
depends_on:
  - adr-2605061200-agi-active-inference-artificial-organism-architecture
  - adr-2604291800-well-becoming-spirit-objective-function
  - adr-2604291800-well-becoming-formal-model
  - adr-2604251215-etzhayyim-agent-authority-bounds
  - adr-2604252100-robotics-product-manufacturing-package
related:
  - active-inference-agent-organism-design
  - adr-0062
  - adr-0088-comfyui-image-generation-gateway
  - adr-2604300135-hume-distillation-artifact-persistence
  - adr-2604291630
  - adr-2604301200-web4-contract-did-autonomous-agent-economy
supersedes: []
superseded_by: []
---

# Context

Active-inference agents need action channels that can affect the real world:

- email sending
- web operation and form submission
- fax
- phone / voice calls
- document creation and signing workflows
- image creation
- audio / speech generation
- video generation
- public posting / publishing
- print and postal mail
- robotics / physical dispatch

These channels differ from internal graph writes. They can create legal,
commercial, reputational, financial, physical, or social consequences outside
the repo. They therefore require a common effect boundary.

Existing repo surfaces already cover parts of this:

- `com.etzhayyim.apps.mailer.*` for mailer
- `com.etzhayyim.apps.fax.*` for fax
- `com.etzhayyim.apps.browser.*` for browser sessions
- `com.etzhayyim.apps.docs.*` for document sync
- `com.etzhayyim.apps.insatsu.printMailJob.*` for print-mail
- `comfyui.etzhayyim.com` / image-generation gateway
- `robotics.*` mission, simulation, authority, telemetry contracts

The missing piece is a single policy that says when an autonomous agent may use
these surfaces and what must be recorded before and after dispatch.

# Decision

Adopt **real-world effect channels** as a first-class action class under
`vertex_agent_action_proposal`.

An action becomes a real-world effect when it crosses any of these boundaries:

| Boundary | Examples |
|---|---|
| External person or organization | email, fax, phone, postal mail, public reply |
| External account or website | browser login, web form submit, purchase, booking |
| Public or semi-public media | image/video/audio publish, social post, file share |
| Legal / commercial artifact | invoice, quote, signed PDF, notice, claim, contract |
| Physical world | print-mail, robotics, shipping, manufacturing dispatch |

Internal generation is not automatically an effect. Drafting a document,
rendering an image, or generating audio is an artifact action. Sending,
publishing, submitting, calling, printing, mailing, or dispatching it is the
effectful action.

## Effect Classes

All real-world actions MUST declare one `effect_class`:

| Class | Meaning | Default gate |
|---|---|---|
| `draft_only` | Creates internal artifact only | audit |
| `private_send` | Sends to known recipient | delegated authority |
| `public_publish` | Publishes or posts externally | policy + predelegated high-risk authority |
| `account_operation` | Uses external account / website | scoped credential + session audit |
| `legal_commercial` | invoice, notice, claim, contract, quote | specific predelegated authority |
| `financial_commitment` | payment, purchase, reservation, ad spend | budget policy + specific authority |
| `physical_dispatch` | print-mail, robotics, shipment, manufacturing | simulation/quote + specific authority + receipt |
| `emergency_or_safety` | safety-critical external action | pre-authorized runbook only |

## Common Dispatch Contract

Every real-world effect must follow this state machine:

```text
draft
  -> classified
  -> policy_checked
  -> authority_bound
  -> dispatched
  -> receipt_recorded
  -> observed
```

Failed or blocked transitions:

```text
draft -> rejected
classified -> authority_missing
policy_checked -> blocked
authority_bound -> expired
dispatched -> failed
```

The dispatch record MUST include:

- agent DID
- requester / principal DID
- channel
- effect class
- target recipient / endpoint / account / partner
- payload hash
- human-readable summary
- delegated authority reference
- budget / quote reference when applicable
- dispatch receipt
- post-dispatch observation plan

## Channel Mapping

| Channel | Existing or target surface | Required pre-dispatch gate |
|---|---|---|
| Email | `com.etzhayyim.apps.mailer.sendEmail` | recipient binding, payload hash, delegated authority |
| Gmail ingest / reply | `com.etzhayyim.apps.gmail.*` / Gmail connector | thread context, reply payload hash, delegated mailbox authority |
| Web operation | `com.etzhayyim.apps.browser.openSession` / browser worker | credential scope, domain allowlist, form-submit authority |
| Fax | `com.etzhayyim.apps.fax.composeAndSend` / `send` | rendered PDF hash, recipient number binding, delegated authority |
| Phone / voice call | `com.etzhayyim.apps.phone.*` (target namespace) | caller identity, script, recording/consent policy, delegated authority |
| Document creation | `com.etzhayyim.apps.docs.*` | artifact only unless shared/sent/signed |
| Image generation | `comfyui.etzhayyim.com` / image gateway | artifact only unless published/sent/printed |
| Audio / speech generation | `com.etzhayyim.apps.voice.*` (target namespace) | artifact only unless played/called/published |
| Video generation | `com.etzhayyim.apps.video.*` (target namespace) | artifact only unless published/sent/ad-used |
| Public post | AT Protocol / PDS dispatch | actor policy, moderation, high-risk delegated authority |
| Print-mail | `com.etzhayyim.apps.insatsu.printMailJob.*` | quote, destination validation, PDF hash, delegated authority |
| Robotics | `com.etzhayyim.apps.robotics.*` | simulation, safety envelope, delegated authority, telemetry sink |

Target namespaces may be added incrementally. The boundary applies before the
namespace exists.

## Delegated Authority Rules

The default rule is:

```text
effect_class != draft_only -> delegated_authority_required
```

This ADR assumes resident organisms may run without human intervention.
Therefore dispatch authorization is not modeled as a live human approval step.
It is modeled as a prior, signed, machine-checkable authority boundary.

Delegated authority may allow dispatch only when all are true:

1. The agent has a signed authority policy for the channel.
2. The target is allowlisted or previously bound.
3. The payload falls below risk thresholds.
4. Budget and rate limits are within policy.
5. Mokuteki / Well-Becoming hard floors pass.
6. The channel can produce a receipt.

If any required condition is missing, the selected action is not "ask a human".
The selected action is `blocked` or `repair`, with a receipt explaining the
missing authority, identity, budget, policy, or observability prerequisite.

High-risk classes are blocked unless covered by a specific predelegated policy:

- first contact to a new external recipient
- legal/commercial notices
- financial commitments
- purchases, bookings, ad spend, or subscription changes
- phone calls to external parties
- fax or postal mail to government, court, bank, employer, school, medical, or
  legal recipients
- public media that uses a real person's name, likeness, voice, or private data
- any action involving minors, medical, legal, immigration, employment, debt,
  tax, or law-enforcement contexts
- safety-critical robotics or physical dispatch

The predelegated policy must name the channel, effect class, allowed targets or
target-binding rule, budget/rate envelope, payload constraints, receipt
requirements, post-dispatch observation plan, and expiry. Broad "all external
actions allowed" policies are invalid.

## Prohibited Patterns

- Sending externally without an action proposal row.
- Dispatching without payload hash and receipt plan.
- Treating generated media as harmless after it is published, sent, printed, or
  used in advertising.
- Web form submission through browser automation without domain and credential
  scope.
- Phone calls without declared caller identity and authority-bound script.
- Fax or print-mail without rendered document hash.
- Reusing delegated authority for a changed payload hash outside its policy.
- Bypassing robotics safety gateway through generic browser or API tools.
- Using real-world effect channels to evade platform moderation, consent,
  legal process, or identity policy.

## Data Model Additions

Add a narrow table for dispatch gating:

```text
vertex_agent_realworld_effect
```

Minimum columns:

| Column | Type | Notes |
|---|---|---|
| `vertex_id` | VARCHAR PRIMARY KEY | effect row |
| `action_proposal_id` | VARCHAR | link to `vertex_agent_action_proposal` |
| `agent_did` | VARCHAR | actor |
| `principal_did` | VARCHAR | authority holder / requester |
| `channel` | VARCHAR | `email`, `web`, `fax`, `phone`, `document`, `image`, `audio`, `video`, `print-mail`, `robotics` |
| `effect_class` | VARCHAR | class from this ADR |
| `target_ref_hash` | VARCHAR | hashed recipient / endpoint where sensitive |
| `payload_hash` | VARCHAR | immutable payload digest |
| `summary` | VARCHAR | human-readable summary |
| `authority_ref` | VARCHAR | signed delegated authority policy |
| `budget_ref` | VARCHAR | quote / lease / budget |
| `dispatch_state` | VARCHAR | state machine value |
| `dispatch_receipt_ref` | VARCHAR | provider receipt |
| `observation_plan_json` | VARCHAR | expected post-dispatch observation |
| `created_at` | VARCHAR | ISO timestamp |
| `updated_at` | VARCHAR | ISO timestamp |

`vertex_agent_action_proposal.action_kind` gains:

- `realworld-email`
- `realworld-web`
- `realworld-fax`
- `realworld-phone`
- `realworld-document`
- `realworld-image`
- `realworld-audio`
- `realworld-video`
- `realworld-print-mail`
- `realworld-robotics`

## Active Inference Integration

Expected free energy scoring must add an external-effect penalty:

```text
G = risk
  + ambiguity
  - epistemic_value
  + viability_penalty
  + external_effect_penalty
```

`external_effect_penalty` increases with:

- new recipient / new website / new phone number
- public visibility
- legal/commercial/financial consequence
- irreversible physical dispatch
- use of likeness, voice, identity, private data, or regulated context
- missing receipt or weak post-dispatch observability

The selected action may still be "bind authority", "repair policy", or
"blocked" rather than "dispatch".

## Consequences

- All external effects are auditable through one boundary even if the underlying
  channel implementations differ.
- Existing channel contracts remain reusable. This ADR adds the common gate,
  not a replacement mailer/fax/browser/print system.
- Media generation is correctly separated from media publication.
- Active-inference agents can reason about real-world action cost and risk
  without being allowed to directly act.
- High-impact channels become compatible with homeostasis: budget, error rate,
  and failed dispatches can push the agent into `conserve`, `repair`, or
  `halted`.

# Alternatives Considered

- **Per-channel policies only**: rejected. It repeats authority binding,
  payload hash, and receipt logic across mailer, fax, browser, phone, media,
  and print-mail.
- **Treat all tools as equal actions**: rejected. Internal graph writes and
  external dispatch have different risk profiles.
- **Require live human approval for every external action**: rejected. This
  conflicts with resident artificial-organism operation. Human intent must be
  represented as prior delegated authority, not an online dispatch dependency.
- **Let LLM decide dispatch directly**: rejected. LLMs may draft and classify;
  dispatch is a policy-gated state transition.

# References

- ADR-2605061200 — AGI / artificial organism architecture
- `90-docs/260506-active-inference-agent-organism-design.md`
- ADR-0062 — Insatsu Cloud Print Mail Network
- ADR-0088 — ComfyUI Image Generation Gateway
- ADR-2604252100 — Robotics control adapters and safety boundary
- ADR-2604301200 — Contract-DID autonomous agent economy
