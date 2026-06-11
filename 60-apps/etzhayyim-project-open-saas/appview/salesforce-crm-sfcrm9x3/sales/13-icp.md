# ICP — open-salesforce Ideal Customer Profile

> Reverse-topo node 13 / 13 — root. Back-solves 12 (positioning), 07 (outbound), 05 (discovery). The ICP is deliberately narrow: narrow ICP makes outbound cheap and discovery fast. Every criterion below is observable from public data or answerable in one discovery question — no "cultural fit" vibes.

## Canonical ICP sentence

> JP- or EU-headquartered mid-market sales organisations (500–5,000 employees, ¥5B–¥200B annual revenue) on Salesforce Sales Cloud Enterprise, with (a) a renewal quote due in the next 2 quarters, (b) a documented data-residency obligation (APPI §22–28, GDPR Art 44, ISMAP, FSA, EBA, HIPAA, CJIS, or equivalent), and (c) a named-LLM plan in production or procurement.

## Firmographic bands (hard filters)

| Dimension | Include | Exclude | Why |
|---|---|---|---|
| Headcount | 500–5,000 | <500 or >5,000 | <500: Zoho / HubSpot fit better on price + convenience, we refer. >5,000: Enterprise SKU with bespoke motion, different team. |
| Annual revenue | ¥5B–¥200B (or USD 35M–1.5B equivalent) | Outside | Matches seat band; >¥200B crosses into Enterprise motion. |
| Sales seats | 22–450 | Outside | The flat ¥3.6M Sovereign plan wins cleanly; below 22 seats Salesforce is cheaper. |
| HQ country | JPN, 27 EU states + UK, CH, NO + APAC regional HQ of a JP/EU parent | US-HQ without JP/EU presence | Sovereignty narrative is load-bearing in JP + EU; US-first procurement prioritises AppExchange depth. |
| Industry | Manufacturing, finance, insurance, healthcare, logistics, regulated SaaS, professional services with regulated clients | Pure SMB retail, pure consumer brands without data obligation | Residency mandate correlates with industry. |
| CRM today | Salesforce Sales Cloud Enterprise (or Unlimited) | HubSpot / Zoho / Dynamics / no CRM / home-grown | "Renewal trigger" requires a renewal. |

## Triggers (the SDR ranks leads by trigger count — 0 trigger = drop)

1. **Salesforce renewal quarter in [+0, +2 quarters] from today.** Computed from public fiscal year-end. Evidence: annual report, press release, stock filing.
2. **YoY Salesforce list-price increase ≥10% (FY26Q1 wave).** Public pricing + discount cycle leaks from RevOps slack groups, AE board notes.
3. **Named own-LLM plan in the last 12 months.** Press release mentioning "GPU cluster", "Azure OpenAI regional deployment", "in-house LLM", "fine-tuned Llama", or a procurement RFP public posting. Job ads for "ML Platform Engineer — internal LLM" count.
4. **Documented residency incident or obligation.** APPI §24 breach notice, GDPR Art 28 audit finding, ISMAP renewal filing, FSA IT supervision guidance, an EU subsidiary launch requiring EU-only CRM data.
5. **Einstein GPT renewal or decline.** AE LinkedIn posts, slack leaks, or vendor board minutes indicate the customer is evaluating Einstein GPT as a line item.
6. **Executive turnover at VP Sales / CRO / CIO in the last 9 months.** New executive = willingness to re-evaluate stack.

**Scoring**: 3+ triggers → Tier A (enter Sequence A immediately). 2 triggers → Tier B (enter Sequence A or B based on which signals). 1 trigger → Tier C (nurture only, watch for second trigger). 0 triggers → drop.

## Named regulation list (the "documented obligation" is observable, not a feeling)

| Region | Named regulation / standard | What SDR looks for |
|---|---|---|
| JPN | APPI §22–28 (sensitive info) + §30 (deletion) | Privacy policy citing APPI sections, DPO name in IR docs |
| JPN | ISMAP / ISMAP-LIU (gov + gov-adjacent) | ISMAP registration number public |
| JPN | FSA IT supervision guideline (financial) | FSA-issued guidance references, bank or insurance license |
| EU | GDPR Art 44–49 (transfer) + Art 17 (erasure) | DPO on staff, SCC template published, Art 30 register |
| EU | NIS2 (critical sector) | NIS2 sector designation (energy, finance, transport, health) |
| EU | DORA (financial resilience, 2025–) | DORA program named in annual report |
| Global | HIPAA (US-adj healthcare) | BAA references |
| Global | CJIS / FedRAMP-equivalent (defence/regulated) | Gov contracts awarded, cleared staff press |
| Industry | SOC 2 Type II + ISO 27001 | Certificates posted, renewal dates |

SDR qualifier: "Is there a named regulation your CRM is audited against every year?" → Yes + can name it = green. "We follow best practices" = red.

## Named-LLM-plan signal list (the "own-LLM plan" is measurable)

| Signal | Weight | Evidence source |
|---|---|---|
| In-house GPU cluster announced (press, board filing) | 3 | Financial Times, Nikkei, press release |
| Azure OpenAI regional deployment public | 3 | Azure customer reference, Microsoft case study |
| Anthropic / OpenAI enterprise contract public | 3 | Vendor customer page, press release |
| Murakumo (etzhayyim internal) customer | 5 | Our own records |
| Internal fine-tuned model product launched externally | 2 | Product page referencing their own LLM |
| Job ads for "ML Platform", "LLM Ops", "GenAI Engineer" >3 openings | 2 | LinkedIn, Indeed, local job boards |
| RFP public for LLM vendor | 3 | Gov procurement portals, IR-filed RFP |
| CTO public statement on "own AI strategy" in the last 12m | 1 | Conference talk, interview |

Weight sum ≥5 → Q4 of discovery is green. <5 → yellow; reset to green only after the AE gets a named counterparty on the call.

## Exclusion list (disqualify in 30 seconds)

- Headcount <500 or >5,000 (size band mismatch).
- No Salesforce today (no renewal trigger).
- Salesforce renewal <90 days or >540 days from today (urgency mismatch).
- ≥5 Apex classes + ≥20 Flows + CPQ + Einstein forecasting all load-bearing (our §C.6 SOW exclusion eats the deal).
- No own-LLM plan and no residency obligation (value prop collapses; send to Zoho/HubSpot).
- US-HQ only, no JP/EU presence (sovereignty narrative weak; route to partner).
- Recent CRM switch (<24 months ago, not Salesforce) → they just did this, they won't redo.

## Ideal target list composition (FY26 launch cohort, 1,000 accounts)

- 600 JP mid-market (FYE 3/31 biased to Sequence A in Q1–Q2): ~180 manufacturing, 150 financial services, 90 logistics, 80 healthcare, 60 regulated SaaS, 40 professional services.
- 300 EU mid-market (FYE 12/31 biased to Sequence A in Q3–Q4): ~100 financial services, 80 manufacturing, 60 healthcare, 40 energy/utilities (NIS2/DORA), 20 regulated SaaS.
- 100 APAC regional HQ of JP/EU parents: mixed industry.

ACV assumption mix: 60% Sovereign ¥3.6M, 30% Sovereign Plus ¥7.2M, 10% Enterprise ¥14.4M+. Expected year-1 ARR if 3% net conversion at avg ¥6M migration + ¥6M ACV = ~180 accounts, ~¥1.1B pipeline, ~¥180M booked ARR.

## Persona targets inside the account (4 roles)

| Role | Title patterns | Primary concern | Our hook |
|---|---|---|---|
| **Economic buyer** | VP Sales, CRO, Head of Commercial, 営業本部長 | Renewal quote, TCO, team productivity | Pillar 4 (flat price) |
| **Champion** | RevOps Lead, Head of Sales Operations, Salesforce Admin, 営業企画 | Flow tech debt, audit trail, data model | Pillar 3 (commit-derived audit) + Pillar 4 |
| **Security / Legal veto** | CISO, DPO, 情報セキュリティ責任者 | APPI / GDPR attestation, residency | Pillar 1 (DPO signs first) |
| **Technology veto** | CTO, Head of AI, 技術本部長 | Own-LLM strategy, lock-in | Pillar 2 (seat = agent) |

Sequence design (node 07) maps each persona to a specific beat; this ICP page is where the mapping is defined.

## ICP governance

- Quarterly review: did the closed-won cohort match the ICP? If 40%+ of wins are outside ICP, widen it. If <10% of contacted-in-ICP converted, tighten or fix messaging.
- New trigger proposals need CRO sign-off before SDRs act on them.
- "ICP drift" (AE chasing off-ICP deals because the month is short) is surfaced in weekly pipeline review; off-ICP deals are flagged but not killed — some win, some teach us to widen.
- ICP page is public-facing: posted at `https://salesforce.opensaas.etzhayyim.com/about/ideal-customer` so prospects self-select. Self-disqualification is a feature, not a bug.

---

## Funnel closed

This is the root of the reverse-topo DAG. With ICP defined:
- Positioning (12) has a buyer identity to position *to*.
- Messaging (11) pillars have a buyer to land with.
- Landing (10), demo (09), pricing (08), outbound (07), content (06), discovery (05) all derive their copy, their numbers, and their filters from this ICP.
- POC (04), SOW (03), onboarding (02), and the closed-won reference (01) all serve this buyer specifically.

If the ICP is wrong, every artifact above is wrong. If the ICP is right and every artifact back-solves from the closed-won case, the funnel is mechanical.
