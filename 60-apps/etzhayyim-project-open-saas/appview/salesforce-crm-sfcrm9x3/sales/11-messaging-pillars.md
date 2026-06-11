# Messaging pillars — open-salesforce

> Reverse-topo node 11 / 13. Back-solves 10 (landing) + 07 (outbound) + 05 (discovery): every pillar must survive out-of-context forwarding, map 1:1 to a landing CTA, and be quoted verbatim in an outbound beat. Four pillars. Each has: one sentence (canonical), proof anchor, disallowed phrasings, 30-word support, 100-word support, and a forbidden-claim list.

## Pillar 1 — "Your DPO signs before your CRO does."

**Canonical sentence**: open-salesforce splits PII into a federation-ready Tier-1 record and a residency-pinned Tier-3 vault, so APPI §22-28 and GDPR Art 44 reviews close in weeks, not quarters.

**Proof anchor**: posture packet PDF + `etzhayyim opensaas attest` signed JSON. Landing CTA link: **Download posture packet**.

**Disallowed phrasings**:
- ❌ "Enterprise-grade security" (say what the grade *is*).
- ❌ "GDPR-compliant" (compliance is a process, not a property — say what we enable).
- ❌ "Bank-grade encryption" (empty).
- ❌ "Your data is safe with us" (trust-me phrasing contradicts the sovereignty story).

**30-word support**: Contact records carry `emailHash: sha256:...` + `phoneHash`, never raw PII. Raw values live in per-tenant Preferences vault, unwrap key never leaves the seat's WebAuthn device. Art-17 purge is one XRPC call.

**100-word support**: Salesforce's residency story ends at "here's the data centre region." Ours goes further: every field tagged as PII (`contact.email`, `contact.phone`, `opportunity.amountJpy` at exact granularity) is split at write time — a hashed index lands in the Tier-1 AT Record (federation-ready, auditable), and the raw value lands in a per-tenant Tier-3 vault pinned to the region on your Order Form. On purge, we delete the Tier-3 row, rotate the Tier-1 hash to `sha256:deleted-<uuid>`, and write an `activity(kind=note)` attestation signed by the executing seat DID — evidence your auditor can verify offline.

**Forbidden claims**:
- Don't imply we're ISO27001 / SOC2 certified until we are; link the roadmap page.
- Don't claim "zero trust" — it's a vendor-bingo word; show the attestation artifact instead.
- Don't promise anything about third-party Murakumo fleet regions without a current signed attestation.

## Pillar 2 — "Seat = agent, not a license."

**Canonical sentence**: The seat DID *is* the AI agent identity; `kotodama.Invoke` runs under it with provenance, not under a shared platform API key, so per-seat LLM is an intrinsic capability — not a ¥6,000/seat/month add-on.

**Proof anchor**: Pillar 2 deep-dive `/docs/per-seat-llm-murakumo` + 2-min demo video of the opportunity "Summarise" action. Landing CTA link: **See how per-seat LLM works**.

**Disallowed phrasings**:
- ❌ "AI-powered CRM" (empty).
- ❌ "Bring your own model" (doesn't capture the seat-DID provenance story).
- ❌ "Einstein GPT alternative" (anchors us to the competitor; instead: "without the Einstein GPT line item").
- ❌ "GenAI-first" (bingo word).

**30-word support**: Seat `did:web:<tenant>.opensaas.etzhayyim.com:seat:<role>-<nn>` invokes Murakumo (or your own LLM) directly. Every invocation emits an `activity(kind=note, source=derived-convo)` with `actorDid=<seat>`. Swap fleets with one `ConfigPut`.

**100-word support**: Einstein GPT is a line item because Salesforce's data model has no way to attribute an LLM invocation to the individual seat that triggered it — so they bill at the tenant plan tier. In open-salesforce, every XRPC call carries the seat DID, `kotodama.Invoke` carries it forward to Murakumo (or any HTTP-invocable fleet you bind), and the fleet's response is tied back to the calling seat in the `activity` record with a signed convo URI. Provenance, cost attribution, and audit are the same object. Swapping Murakumo for Azure OpenAI, Anthropic, or your in-house GPU is `ConfigPut fleet=<didOrUrl>`.

**Forbidden claims**:
- Don't claim we're "faster than Einstein" without current benchmarks.
- Don't promise fine-tuning until the Murakumo fleet exposes it in the relevant tier.
- Don't call per-seat LLM "free" — the Murakumo fleet has its own cost; it's just not a Salesforce-style per-seat uplift.

## Pillar 3 — "Every activity is a commit, not a screenshot."

**Canonical sentence**: `activity` records aren't typed by a user; they're derived by the PDS commit pipeline from stage-changes, status-changes, and conversions — every row is cryptographically tied to the commit that caused it and is verifiable outside the CRM.

**Proof anchor**: a real record at `/at/democo.opensaas.etzhayyim.com/com.etzhayyim.apps.opensaas.salesforce.activity/act-demo-conv-001`. Landing CTA link: **See a real record**.

**Disallowed phrasings**:
- ❌ "Immutable ledger" (blockchainy; just say content-addressed).
- ❌ "Tamper-proof audit trail" (marketing word; explain that the commit DAG is signed).
- ❌ "Single source of truth" (empty).
- ❌ "Forensic-grade" (don't over-promise forensics).

**30-word support**: Stage changes on `opportunity`, status changes on `case`, and `convertLead` atomic commits each auto-emit `activity` via `kotodama.jsonld` derive rules. Every activity row's source commit is AT-URI-addressable.

**100-word support**: Salesforce `FieldHistory` is a row in a mutable table; a DBA with write access can rewrite it. W Protocol commits sign, chain, and content-address each write — so the `activity(kind=stage-change)` row that claims "VP Sales moved opp-4829 from negotiation to closed-won at 14:02" can be verified by fetching the source commit at `/at/<tenant>/com.etzhayyim.apps.opensaas.salesforce.opportunity/opp-4829` and comparing the signed commit CID. This is what "federation-grade audit" actually means — an auditor, a regulator, or a successor CRM can read the evidence without our CRM being online.

**Forbidden claims**:
- Don't claim the audit trail is legally admissible in `<jurisdiction>` without counsel sign-off.
- Don't compare to blockchain CRMs; we're not that category.
- Don't imply activity records are immutable against operator-initiated purge — GDPR Art 17 *requires* deletion; our story is that deletion is also signed.

## Pillar 4 — "Flat price. No Einstein. No egress fee."

**Canonical sentence**: ¥3,600,000 / year flat for unlimited seats on Sovereign; ¥7,200,000 on Sovereign Plus; no per-seat, no LLM add-on, no egress fee at any tier.

**Proof anchor**: public pricing page + TCO calculator. Landing CTA link: **Run the TCO calculator**.

**Disallowed phrasings**:
- ❌ "Starting at ¥3.6M" (flat means flat; "starting at" undermines Pillar 4's entire premise).
- ❌ "Contact us for pricing" on Sovereign / Sovereign Plus (only valid on Enterprise SKU).
- ❌ "Affordable" / "cost-effective" / "save thousands" (vague).
- ❌ "No hidden fees" (cue-phrase that signals hidden fees).

**30-word support**: Sovereign ¥3.6M covers up to 20M records, 1 region, Murakumo `m2`. Sovereign Plus ¥7.2M: 60M records, 3 regions, `m4`. Published soft caps. No per-API-call or per-row metering.

**100-word support**: The flat number is defensible because every variable cost (records, regions, integrations, LLM tier) has a published soft cap and a published uplift — no hidden metering dressed as "fair use". The egress-free guarantee matters because sovereignty without exit is hostage marketing: on termination, we deliver a full repo archive in AT Protocol JSON and Iceberg Parquet within 30 days, at no fee. The migration, integration, and hyper-care lines are one-time or term-bounded and priced separately — customers have told us that the separation is the thing that makes their CFO nod.

**Forbidden claims**:
- Don't claim "cheaper than Salesforce" without referencing the calculator output at the prospect's seat count.
- Don't promise price holds after term; our Order Form renewal caps are CPI+3%.
- Don't compare to Zoho on price; we don't compete there (pricing node 08).

## Copy discipline — cross-cutting

| Rule | Reason |
|---|---|
| Every pillar sentence must survive out-of-context forwarding | Beat A7 (CISO) and Beat A5 (RevOps) route pillars sideways |
| Logo blocks only appear after Order Form §logo rights opt-in | "No-logo-lying" rule from landing (node 10) |
| Every public claim links to either a file on our domain or a command the prospect can run | Demo (node 09) proved "artifact, not slide" |
| JP + EN canonical sentences must mean the same thing | Discovery (node 05) qualification spans JP + EU buyers |
| Number in a pillar must match number in calculator, SOW, and Order Form | Pricing (node 08) internal consistency |

## What this forces the positioning (12) to commit to

- A **category sentence** that precedes all four pillars — because pillars are *within* a category, and we can't let the buyer miscategorise us (e.g. "blockchain CRM", "Salesforce managed service", "AI CRM").
- A **competitive frame** that makes the trade-off with Salesforce explicit (what we give up for what we give) rather than hand-waving "better in every dimension".
- A **who-it's-not-for** statement so Pillar 4 "no Zoho compete" and SOW §C.6 "no Apex" land as deliberate choices, not gaps.
- A **permanent anchor noun** for the category so the four pillars resolve to a single identity in buyer memory — otherwise pillars compete with each other.
