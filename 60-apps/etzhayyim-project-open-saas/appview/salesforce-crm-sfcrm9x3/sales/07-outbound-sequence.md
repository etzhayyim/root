# Outbound sequence — open-salesforce

> Reverse-topo node 07 / 13. Back-solves 06 (inbound content): every beat links to a concrete pillar URL; sequence cadence is pegged to the target's Salesforce renewal quarter (T-180 → T-90); every landing form becomes a `createLead({source: "outbound"|"event"|"referral"})` write. No "hope you're well"; no "circling back".

## Target list construction (pre-send)

1. **Seed**: 2,500 accounts — Japan mid-market (500–5,000 employees) + EU mid-market with APAC / JP presence.
2. **Renewal quarter inference**: public fiscal year-end → renewal = FYE + 0..3 months. Bucket each account into a renewal quarter.
3. **Priority filter** (green on all three → Tier A, green on two → Tier B, else drop):
   - Salesforce customer (public, press, Marketplace, job ads mentioning "Apex / Flow").
   - Named LLM or sovereignty press in last 12m (own-GPU, Azure OpenAI regional, APPI certification).
   - Renewal quarter ∈ next 2 quarters.
4. **Contact roles** per account: VP Sales / CRO (economic), RevOps lead (champion), CISO / DPO (Security gate), Head of IT Procurement (motion blocker).

## Sequence A — "Renewal quarter approaching" (Tier A, T-180 to T-120)

**Audience**: VP Sales + RevOps lead, cc nobody.
**Total beats**: 5 emails + 2 LinkedIn + 1 voicemail over 18 business days.

### Beat A1 (Day 0 — email, VP Sales)

Subject: Acme's Salesforce renewal — the two levers most of your peers pulled this year

Body (JP or EN, localised):
> `<FirstName>`,
>
> Your FY`<NN>` closes `<Month>`, so the Salesforce quote usually lands on your desk around `<Month+0..3>`. Two things came up 30-odd times in the last 12 months of renewal re-evaluations we've been close to:
>
> 1. **Einstein GPT is billed separately**, but your team already has an LLM in production (`<named model from press>`).
> 2. **APPI / GDPR residency reviews** are being re-opened per-tenant, so the "trust us, US-EU Data Privacy Framework covers it" answer from the Salesforce AE is no longer enough.
>
> We built open-salesforce on AT / W Protocol specifically for those two — tenant = DID, PII split between Tier-1 hashed indices and a Tier-3 residency-pinned vault, per-seat LLM invocation instead of a platform-wide add-on.
>
> One artifact that's worth more than any call: `https://salesforce.opensaas.etzhayyim.com/docs/posture-appi-gdpr`. Forward to your DPO; it's the packet most Security teams want before they'll sit at the table.
>
> Worth 20 minutes?
> — `<AE>`

### Beat A2 (Day 3 — LinkedIn connect + note, RevOps lead)

> `<FirstName>`, I sent a note to `<VP Sales>` on the Salesforce renewal. Not looking to spam — if you're the RevOps owner and Einstein/residency aren't on the table this cycle, tell me and I'll stop. If they are, here's the 3-min read: `<pillar-2 URL>`.

### Beat A3 (Day 5 — email, VP Sales, reply-on-thread)

Subject (reuse A1 thread).

> Two data points since Monday:
>
> - A RevOps peer in `<industry>` cut their CRM TCO 38% over 3 years after migrating off Sales Cloud Enterprise. Their renewal quarter was `<quarter>` — so the clock that matters is your quote-arrival date, not contract-end date.
> - `convertLead` in open-salesforce writes the Account + Contact + Opportunity atomically in one commit, then auto-derives a conversion Activity. 90-second screen capture: `<pillar-4 video URL>`.
>
> If you'd rather see the TCO before talking, our calculator takes ~2 minutes: `<pillar-5 URL>`. It'll also tell you which of your current Salesforce add-ons map to zero-cost open-salesforce features.

### Beat A4 (Day 8 — LinkedIn comment on recent post, VP Sales)

No pitch. Genuine comment on their most recent public post related to sales efficiency / AI / Japan SaaS. Sets the fourth email up.

### Beat A5 (Day 10 — email, RevOps lead, new thread)

Subject: Field map: your Salesforce objects → open-salesforce lexicons

> `<FirstName>`,
>
> This one's for you, not your VP. Our interactive field map — paste your Salesforce object-field list client-side, get back a dry-run `map.jsonl` ready for `etzhayyim opensaas migrate`: `<pillar-4 URL>`.
>
> Two things it'll surface in under 5 minutes:
> - which custom objects port cleanly (extend `com.etzhayyim.apps.opensaas.salesforce.*`),
> - which Flow / Apex doesn't, and what the `derive` rule replacement looks like.
>
> If the map shows >10% drop, I'll tell you it's not a fit this year.

### Beat A6 (Day 12 — voicemail + email, VP Sales)

90-second VM: named regulation ("APPI §22-28" / "GDPR Art 44"), named renewal month, one sentence on per-seat LLM, closer is "reply to my last email or I'll stop".

Follow-up email within 10 min: "Left you a VM. Short version: `<one-line recap>`. Reply with a 'not this year' and I'll close the loop."

### Beat A7 (Day 15 — email, CISO / DPO, new thread)

Subject: Pre-reading for `<VP Sales>` / `<RevOps>`'s CRM renewal decision

> `<FirstName>`,
>
> If your Sales team re-opens the CRM residency question this quarter (renewal quarter is `<quarter>`), they'll need a Processor/Controller matrix, a sub-processor list, and a working Art-17 cascade demo.
>
> Here's ours: `<pillar-3 URL>`. It's 14 pages; skim the matrix on page 4 and the purge rehearsal on page 9. Zero ask — I'd rather you disqualify us now than at week 10 of a POC.

### Beat A8 (Day 18 — breakup email, VP Sales)

> `<FirstName>`,
>
> I'll stop reaching out on this cycle. If the Salesforce quote comes in above `<YoY threshold from press>%` and you want a second option, the two numbers worth knowing are: flat ¥`<pricing>` / year for unlimited seats and a reconciliation-gated migration weekend with a written rollback clause.
>
> I'll revisit around `<renewal quarter - 2 months>` next year. Good luck with the quote.

## Sequence B — "LLM-led" (Tier A/B where own-LLM signal is strongest)

Same cadence, different beats. Openers reference their named model in production and how `kotodama.Invoke` from inside the CRM UI lets the seat DID call that model directly. Beat 2 links Pillar 2 video; Beat 5 links the `atproto.etzhayyim.com` post "per-seat LLM auth is the seat DID, not an API key".

## Sequence C — "Security-led" (Tier A in regulated industry)

Addressed to CISO / DPO first, not VP Sales. Opener is the posture packet link; beat 3 is the purge rehearsal video; beat 5 pivots to "ping your VP Sales if residency is on the agenda this cycle."

## Write-backs into the CRM

Every outbound message is logged as an `com.etzhayyim.apps.opensaas.salesforce.activity` record with:
- `kind=email` or `call`,
- `direction=outbound`,
- `source=manual-ui` (since it's pre-lead),
- `leadDid=<null until landing page form fires `createLead`>`.

When the landing page `createLead` fires, the sequence logger emits the backlog of outbound activities as `activity` records attached to the new `leadDid` — so the RevOps dashboard shows the full 18-day touch history from day one.

## Reply handlers (human-in-the-loop, LLM-drafted)

| Reply pattern | LLM draft anchor | Human review |
|---|---|---|
| "Not now / we just renewed" | Parse FYE → revisit date; update `lead.status=unqualified`, schedule a calendar reminder at revisit date | Yes, before send |
| "Send more info" | Send Pillar 3 + calculator link; move to `lead.status=qualifying` | Auto-send |
| "Who's your reference?" | Send node 01 case study; move to `lead.status=qualified`, book a discovery | Yes, before send |
| "Security wants to talk first" | Forward to Pillar 3 + offer Security-only call; status=qualifying | Auto-send |
| "Pricing?" | Calculator URL first, then AE call only if the calc output >¥`<threshold>` | Auto-send for URL, human for call |

LLM prompt includes the account's renewal quarter, named regulation, and named LLM — so replies aren't generic.

## What this sequence forces pricing (08) to commit to

- A **flat number** the calculator can display without auth — per-seat ambiguity destroys the calculator's conversion.
- A **3-year ACV commitment** price, because the "38% TCO" claim in Beat A3 needs a defensible TCO basis.
- A **migration fee separate from platform fee**, because Beat A5's map tool outputs ≈ customer's own migration estimate and the platform fee must not flex with it.
- A **reference-customer discount** mechanism, because Beat A8's breakup line ("flat ¥`<pricing>`") only lands if the number is believable — and the way it becomes believable is that early customers get a clear, named discount.
- A **no-egress-fee commit** at term end, because Beats A1 and A7 both link the posture packet and a sovereignty story is hollow without exit rights.
