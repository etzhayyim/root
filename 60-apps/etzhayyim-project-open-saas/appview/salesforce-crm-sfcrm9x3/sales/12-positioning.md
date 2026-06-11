# Positioning — open-salesforce

> Reverse-topo node 12 / 13. Back-solves 11 (messaging pillars), 10 (landing), 08 (pricing), 05 (discovery). Produces the **category sentence** that precedes the four pillars, the **explicit trade-off** with Salesforce, and the **who-it's-not-for** statement. This is the one page every employee, investor, and partner memorises. Every other artifact in this funnel dies if this page is weak.

## Category (the anchor noun)

**Sovereign CRM.**

Not "open-source CRM" (that's Community SKU framing, not category). Not "CRM-as-protocol" (too abstract for a buyer). Not "DID-native CRM" (implementation, not use). Not "AI CRM" (nothing about the category is LLM-led).

**Sovereign CRM** = a CRM where **tenant identity is a DID the customer can custody**, **PII residency is verifiable on demand**, **AI is a seat-level capability not a platform SKU**, and **exit has no egress toll**.

Analogy, not parity: "sovereign cloud" (OVH, Exoscale, Sakura) is to hyperscalers what Sovereign CRM is to Salesforce. The analogy is there to make the category land in one sentence with a procurement officer who has never heard of AT Protocol.

## Positioning statement (canonical, memorise verbatim)

> **For** Japan- and EU-based mid-market sales organisations (500–5,000 seats) with a Salesforce renewal in the next 2 quarters, a documented data-residency obligation, and an own-LLM plan in production or procurement,
>
> **open-salesforce is** the Sovereign CRM — a Salesforce-equivalent (Account, Contact, Lead, Opportunity, Case, Activity) built on AT / W Protocol, where the tenant is a DID, PII is split between a federation-ready Tier-1 record and a residency-pinned Tier-3 vault, every Activity is a commit-derived record verifiable outside the CRM, and LLM invocation is a seat-level capability — not a platform add-on.
>
> **Unlike** Salesforce Sales Cloud + Einstein GPT, which charges per seat + per LLM add-on and treats residency as a datacentre-region promise, **open-salesforce** ships a flat per-tenant price, a public residency attestation command, a zero-egress exit clause, and a reconciliation-gated migration weekend.

JP:
> Salesforce 更新を 2 四半期以内に控え、データ所在地規制 (APPI §22–28、GDPR Art 44 等) に対応する義務があり、独自 LLM を本番または調達中の日本・EU 中堅企業 (500〜5,000 席) に対して、open-salesforce は "主権型 CRM" です。AT / W Protocol 上で Salesforce 相当 (Account / Contact / Lead / Opportunity / Case / Activity) を実装し、テナント = DID、PII は連合可能な Tier-1 レコードと所在地固定 Tier-3 Vault に分離、Activity は commit 由来で CRM の外でも検証可能、LLM 呼び出しは席単位の能力 (プラットフォームのアドオンではなく)。Salesforce Sales Cloud + Einstein GPT が席課金と LLM アドオン課金で、所在地を "データセンター地域の約束" として扱うのに対し、open-salesforce はテナント固定価格、公開検証コマンド、egress 無料の退出条項、照合ゲート付き移行週末を提供します。

## Trade-offs (explicit, not hidden)

Positioning without honest trade-offs is brochure copy. We give up:

- **No Apex / no Lightning App Builder / no Visualforce**. Custom logic lives in `kotodama.jsonld` derive rules (JSONLD) or WIT capability workers — a different extensibility model, not a richer one. Teams with ≥5 Apex classes or ≥20 Flows will feel this.
- **No AppExchange marketplace depth**. We have capability workers registered per tenant DID, but not a catalog with thousands of pre-built apps.
- **Einstein forecasting is not replicated 1:1**. Forecasting via Murakumo fine-tune is roadmap, not today.
- **Salesforce-native reports / dashboards are replaced with `listPipeline` + tenant-scoped SQL**. Power-report-users who live in Report Builder will need to re-learn.
- **No support for Sales Cloud CPQ (Configure-Price-Quote)**. Out of scope; partner-referred.
- **Federation is opt-in per collection**. If you want everything private, you can have that, but then you don't benefit from protocol-level interop. Be clear about what you're trading for.

In exchange:

- Tenant DID you can custody (`etzhayyim plc-migrate` migrates the plc:did to your own controller).
- Residency attestation on a command line.
- Per-seat LLM with provenance.
- Flat price, no egress fee.
- Federation-grade Activity audit.
- `convertLead` atomicity + auto-derived activities out of the box.
- SOW with reconciliation-gated migration + rollback clauses.

Positioning rule: when a prospect asks "what do you lose vs Salesforce?", an AE who lists the trade-offs above within 20 seconds **wins trust**; an AE who waffles loses the deal.

## Who it's for (and not)

**For**:
- JP mid-market (500–5,000 employees) with APPI obligations, ISMAP / SOC2 auditor, Japanese fiscal year-end 3/31 or 12/31.
- EU mid-market with GDPR Art 44 residency obligations, EU-only subsidiary structure, or EU-only seat population.
- APAC regional HQ of global brands where data cannot leave region under contract.
- Regulated industries (finance, healthcare, defence) with documented residency mandates.
- Organisations with an own-LLM plan — model named, fleet named, vendor named.

**Not for**:
- <500-employee businesses — HubSpot Sales / Zoho CRM Plus fit better on price and UX convenience; we'll refer.
- >5 Apex class / >20 Flow Salesforce customers unwilling to port — the SOW §C.6 exclusion is real, not negotiable.
- Teams that need CPQ or Einstein forecasting as must-haves today — roadmap yes, not today.
- Teams with no own-LLM plan and no residency obligation — the uplift over Salesforce is not worth the migration risk for them. Be honest; walk away.
- Teams where "we just need a CRM" is the requirement — we are not the generic CRM. Generic CRM is a race to the bottom; we chose not to run it.

## Category competitors (named, with honest win/lose)

| Competitor | Their story | We win when | They win when |
|---|---|---|---|
| Salesforce Sales Cloud Ent + Einstein GPT | "Industry-leading CRM + AI" | Residency / renewal price / own-LLM is live | Apex / Flow / CPQ / Einstein forecasting is load-bearing |
| HubSpot Sales Enterprise | "Unified platform, inbound-led" | Residency + mid-market ACV > ¥6M | Customer is SMB + marketing-led |
| SugarCRM Ent (self-host) | "Open CRM, self-hosted" | DID-native multi-tenant matters, or federation story matters | Customer just wants a box on their own VM and doesn't care about protocol interop |
| Zoho CRM Plus | "Full suite, low price" | Own-LLM + residency non-negotiable | Price is the only variable |
| Microsoft Dynamics 365 Sales | "Tight with Office 365 + Azure OpenAI" | Customer wants sovereignty vs. Microsoft lock-in | Customer is deeply Azure-native |

We do not position against Bluesky / ATmosphere ecosystem tools — they're peers in protocol, not competitors in CRM. Link them in the ecosystem page instead.

## The one-sentence elevator (for bluesky bios, LinkedIn headlines, booth cards)

> The Sovereign CRM for Japan & EU mid-market — tenant = DID, per-seat LLM, flat price, no egress fee.

## Positioning governance

- Canonical sentence changes require AE + CRO + CEO sign-off. Every external artifact (landing, pillars, outbound, SOW, case study, deck) must quote the canonical sentence verbatim.
- "Sovereign CRM" is trademarked by us for this use; we own and defend the category noun.
- Category noun drift (AE saying "open-source CRM" instead of "Sovereign CRM") is tracked in weekly call-review; misuse triggers recoaching, not discipline.
- New competitor entrants (the next "sovereign CRM" startup) will arrive — the positioning page gets a named-competitor block update within 2 weeks of first public pitch surface.

## What this positioning forces the ICP (13) to commit to

- A **concrete, numbers-anchored definition** of "mid-market" (seat band, revenue band, employee band) so SDRs build clean lists.
- A **named regulation list** (APPI §, GDPR Art, ISMAP, SOC2) so the "documented data-residency obligation" criterion is observable, not vibes.
- An **exclusion list** (SMB, Apex-heavy, no-LLM-plan, CPQ-dependent) so SDRs can disqualify in 30 seconds, not 3 calls.
- A **trigger definition** ("Salesforce renewal in the next 2 quarters") that SDRs can compute from public data (fiscal year-end) so the top of the funnel isn't chasing ghosts.
- A **named-LLM-plan signal list** (concrete procurement signals, press, job ads) so the "own-LLM plan" criterion is measurable, not aspirational.
