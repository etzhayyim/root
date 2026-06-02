# Discovery call script + qualification — open-salesforce

> Reverse-topo node 05 / 13. Back-solves 04 (POC). Each question below exists to disqualify fast if the POC gates would fail anyway. 30 minutes max. Two people on our side: AE leads, SE listens for LLM/data-residency signals. Output of the call is a filled-in **Qualification Sheet** (end of file) — not a meeting note.

## Pre-call prep (5 min)
- Pull from public: Salesforce earnings press release cycle, customer's fiscal year-end, any ISO27001 / ISMAP / SOC2 page, any "AI" press release in last 12 months.
- Guess the renewal quarter based on fiscal year-end. Write it in the sheet *before* the call; confirm or reset during the call.
- If the customer is on `<500 seats`, skip — they're not in ICP (node 13).

## Opening (2 min)
> "Thanks for the time. Short version of why we reached out: Salesforce's renewal invoice cycle is a forcing function we've seen 30-odd mid-market teams re-evaluate the CRM on, and two things we hear most often are — (1) AI features are locked behind Einstein add-ons when the company already runs its own LLM, and (2) APPI / GDPR reviews keep getting re-opened every year. We built open-salesforce on a DID-native W Protocol stack exactly for those two. I'll ask a handful of questions to see if there's a fit, and if not I'll say so before we waste a POC."

Purpose: set the frame as a mutual disqualification, not a pitch. Gets a better answer on question 1.

## Trigger qualification (5 min)
**Q1. What's your Salesforce renewal timing, and has the quote come in yet?**
- Want: T-90 to T-180 days from today. T-30 is too late for a 21-day POC + 2-round legal redline + weekend migration. T-300 is too early — urgency is fake.
- Listen for: YoY price increase %. If >10%, the case for change is pre-built.
- Red flag: "we just renewed 2 months ago" → park them for 10 months, no POC.

**Q2. How did you evaluate at last renewal? What did you look at, what killed the alternatives?**
- Reveals incumbent moats they think matter. Usually: Apex, Flow, AppExchange apps, bespoke reports.
- Our response vector: position §C.6 SOW exclusions (no Apex / Flow / Einstein forecasts port) as a **feature** — forces the customer to audit what they actually use.

## Pain qualification (8 min)
**Q3. How many seats today? How many of those are actually in the CRM weekly?**
- The gap (licensed vs. WAU) is our flat-price opening. If they have 800 licenses and 220 WAU, Salesforce per-seat is burning ¥.

**Q4. What's your AI / LLM plan? Is there a model already in procurement or production, internal or external?**
- Want: a named model / fleet / vendor (OpenAI enterprise, Anthropic, in-house GPU, Azure OpenAI, Murakumo). If yes → per-seat Murakumo gate on Day 21 is credible.
- Red flag: "we're evaluating AI" / "Einstein is fine" → no own-LLM pull, skip to data-residency; if that's also weak, disqualify.

**Q5. Where does your CRM data physically live, and has your DPO / Legal asked about that in the last 12 months?**
- Want: named regulation (APPI §22-28, GDPR Art 44, FSA, EBA, HIPAA, CJIS). The attestation artifact (POC Day 5) needs something to attest *against*.
- Bonus: EU sub, CN sub, or regulated industry (finance, healthcare, defence) → sovereignty story lands hard.

## Technical reality (8 min)
**Q6. Tell me about your Salesforce customisations — Apex, Flow, custom objects, AppExchange apps.**
- We need to know the port/drop list before the POC, not during the weekend.
- Calibration: "Acme Robotics had 3 custom objects, 7 Flow, 0 Apex — they ported the objects as `com.etzhayyim.apps.opensaas.salesforce.*` extensions; dropped the Flow in favour of our derive rule + scheduled command." Set expectation.

**Q7. Who owns a Salesforce data export? Can they produce a 10%-slice in 3 business days?**
- If the admin is a shared resource or an external partner-managed org, Day 3 of POC will slip. Surface it now.

**Q8. Do you have an in-house or partner RevOps person who can be the POC DRI and migration-weekend DRI?**
- No DRI = no POC. We do not run the customer's side.

## Decision path (5 min)
**Q9. Who signs the MSA and the SOW? Who's the veto for security / legal / procurement?**
- Map to: Exec Sponsor, DRI, Security reviewer (from POC gate §Track 2), Procurement, Counsel. If any of these five are unnamed, the POC will stall at Day 10 legal redline.

**Q10. If the POC hits all 8 gates on Day 21, what stops you from signing by Day 45?**
- The "I'll have to check" answer is disqualifying — they don't have the authority or internal mandate. Reset to: who do we need on the next call?

## Close (2 min)
If 7+ of 10 answers are green (see sheet below):
> "Based on those answers, I think there's a POC worth running. Next step: I'll send a 1-page POC Agreement derived from our MSA §§1–6 + §10, and we aim to kick off within 14 days. You'll need to name a Security reviewer and a DRI before we start Day 1."

If ≤6 green, or any red flag on Q1 / Q4 / Q5:
> "Based on those answers, I don't think a POC is the right next step this quarter. Let's reconnect in <N months, tied to their trigger>. I'll send a short note with the two or three things that, if they change, make this a good fit — so we don't waste each other's cycles."

Follow-up email within 2 hours: qualification sheet (shared, not internal), 1-page POC Agreement or the "revisit in N months" note.

## Qualification Sheet — fill during the call

| # | Question | Green | Yellow | Red | Answer |
|---|---|---|---|---|---|
| 1 | Renewal timing | T-90 to T-180 | T-180 to T-365 | <T-90 or just renewed | |
| 1b | YoY price delta | >10% | 0–10% | flat or decrease | |
| 2 | Past evaluation killers | Listed, non-Apex | Some Apex | Heavy Apex + Flow | |
| 3 | Seats / WAU ratio | WAU ≤ 40% licences | 40–70% | >70% | |
| 4 | Own-LLM plan | Named model in prod/procurement | Evaluating | None / Einstein fine | |
| 5 | Data-residency obligation | Named regulation + recent DPO ask | Residency matters, no named reg | Not asked / don't know | |
| 6 | Apex / Flow / AppExchange count | ≤3 custom objects, ≤10 Flow, 0 Apex | moderate | heavy (>5 Apex classes) | |
| 7 | 10%-slice export in 3d | Yes, admin named | Maybe, partner-managed | Unknown | |
| 8 | POC DRI named | Yes | "We'll find someone" | No | |
| 9 | Signing path mapped (5 roles) | All 5 named | 3–4 named | ≤2 | |
| 10 | Post-POC signing blockers | None or addressable | One to check | "I'll have to ask" | |

Count greens. **≥7 green AND no red on {1, 4, 5} → POC Agreement**. Otherwise → parked with explicit revisit trigger.

## What this script forces the inbound content plan (06) to deliver

- A public deep-dive on **content-addressed activity log** and **per-seat LLM** — so Q4 and Q5 have a credible URL to send after the call.
- A public **APPI + GDPR posture packet** — so Q5's "named regulation" path doesn't require a security reviewer to take our word for it.
- A public **Salesforce → open-salesforce field map** — so Q6 and Q7 prep themselves before the call.
- A public **pricing calculator** (flat vs. per-seat) — so Q3's seat/WAU ratio answer lands on a landing page the customer can forward internally without a second call.
- A 2-minute demo video of `listPipeline` + `convertLead` + derived `activity` — so Q2's "what would kill alternatives" gets a concrete counter.
