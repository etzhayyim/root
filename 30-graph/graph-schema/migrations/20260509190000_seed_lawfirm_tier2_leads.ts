import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Seed: Tier-2 India lawfirm pilot funnel — 7 firms staggered W4-W7.
 *
 * Pre-built outreach .eml files in outbox/08[a-g]-*-warm-intro.eml.
 * On apply: lawfirm_sales_cadence_tick BPMN (R/PT24H) walks
 * vertex_lawfirm_lead.next_action_at and triggers cadence-tick auto-send
 * via gftdcojp.microsoft.sendDraft → k-bakshi Outlook.
 *
 * Funnel design rationale: tier2-lead-funnel-india.md
 *   P(0 wins) drops 30% → 5% versus top-3-only.
 *   Y1 ARR target hit-probability rises 50% → 80%.
 *
 * Idempotent INSERT...SELECT WHERE NOT EXISTS — re-applying is a no-op.
 *
 * Conversion value estimates per firm (Y1 USD if pilot lands):
 *   Khaitan / Cyril / Shardul (large)   = USD 80K (anchor: 800-1000 lawyer scale → custom pricing)
 *   AZB (large mid)                     = USD 70K
 *   JSA (mid-large)                     = USD 60K
 *   Luthra (mid)                        = USD 50K
 *   S&R (mid-small but PE-rich)         = USD 50K
 */
const NOW = "2026-05-09T00:00:00Z";
const OWNER = "did:web:lawfirm.etzhayyim.com";
const ASSIGNEE = "did:web:k-bakshi.etzhayyim.com";

type Lead = {
  leadId: string;
  targetName: string;
  targetEmail: string;
  city: string;
  firmSize: string;
  practiceArea: string;
  source: string;
  nextActionAt: string;        // W4-W7 send date IST→ISO
  conversionValueUsd: number;
  notes: string;
};

const LEADS: Lead[] = [
  {
    leadId: "khaitan-2026",
    targetName: "Khaitan & Co",
    targetEmail: "rabindra.jhunjhunwala@khaitanco.com",
    city: "Mumbai",
    firmSize: "850",
    practiceArea: "m-and-a-pe-tmt",
    source: "k-bakshi-linkedin",
    nextActionAt: "2026-05-26",
    conversionValueUsd: 80000.0,
    notes: "Tier 2 #1, target Rabindra Jhunjhunwala / Haigreve Khaitan / Sudhir Bassi. Outreach: outbox/08a-khaitan-warm-intro.eml",
  },
  {
    leadId: "azb-2026",
    targetName: "AZB & Partners",
    targetEmail: "zia.mody@azbpartners.com",
    city: "Mumbai",
    firmSize: "600",
    practiceArea: "m-and-a-banking-disputes",
    source: "cold-leiden-alumni",
    nextActionAt: "2026-06-02",
    conversionValueUsd: 70000.0,
    notes: "Tier 2 #2, target Zia Mody (managing) / Ajay Bahl. Outreach: outbox/08b-azb-warm-intro.eml",
  },
  {
    leadId: "sr-2026",
    targetName: "S&R Associates",
    targetEmail: "rajat.sethi@snrlaw.in",
    city: "Mumbai",
    firmSize: "130",
    practiceArea: "pe-capital-markets",
    source: "k-bakshi-prior-matter",
    nextActionAt: "2026-06-02",
    conversionValueUsd: 50000.0,
    notes: "Tier 2 #3, prior-matter rapport. Outreach: outbox/08c-snr-warm-intro.eml",
  },
  {
    leadId: "cyril-2026",
    targetName: "Cyril Amarchand Mangaldas",
    targetEmail: "cyril.shroff@cyrilshroff.com",
    city: "Mumbai",
    firmSize: "1000",
    practiceArea: "full-service",
    source: "cold-linkedin",
    nextActionAt: "2026-06-09",
    conversionValueUsd: 80000.0,
    notes: "Tier 2 #4, scale + brand halo. Outreach: outbox/08d-cyril-warm-intro.eml",
  },
  {
    leadId: "shardul-2026",
    targetName: "Shardul Amarchand Mangaldas",
    targetEmail: "pallavi.shroff@amsshardul.com",
    city: "Delhi",
    firmSize: "750",
    practiceArea: "competition-ip-disputes",
    source: "cold",
    nextActionAt: "2026-06-09",
    conversionValueUsd: 80000.0,
    notes: "Tier 2 #5, sister-firm to Cyril (separate decision tree). Outreach: outbox/08e-shardul-warm-intro.eml",
  },
  {
    leadId: "jsa-2026",
    targetName: "J Sagar Associates",
    targetEmail: "amit.kapur@jsalaw.com",
    city: "Delhi",
    firmSize: "400",
    practiceArea: "energy-pe-banking",
    source: "k-bakshi-linkedin",
    nextActionAt: "2026-06-16",
    conversionValueUsd: 60000.0,
    notes: "Tier 2 #6, energy + PE recurring volume. Outreach: outbox/08f-jsa-warm-intro.eml",
  },
  {
    leadId: "luthra-2026",
    targetName: "Luthra and Luthra",
    targetEmail: "rajiv.luthra@luthra.com",
    city: "Delhi",
    firmSize: "250",
    practiceArea: "pe-energy-disputes",
    source: "cold-linkedin",
    nextActionAt: "2026-06-16",
    conversionValueUsd: 50000.0,
    notes: "Tier 2 #7, post-2020 rebuild = greenfield openness. Outreach: outbox/08g-luthra-warm-intro.eml",
  },
];

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const l of LEADS) {
    const vid = `at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.lawfirm.lead/${l.leadId}`;
    await sql`
      INSERT INTO vertex_lawfirm_lead
        (vertex_id, lead_id, lead_kind, target_name, target_email,
         target_country, target_city, firm_size, practice_area, source,
         assigned_to_did, stage, next_action, next_action_at,
         conversion_value_usd, notes, created_at, owner_did)
      SELECT
        ${vid}, ${l.leadId}, 'saas_pilot', ${l.targetName}, ${l.targetEmail},
        'IN', ${l.city}, ${l.firmSize}, ${l.practiceArea}, ${l.source},
        ${ASSIGNEE}, 'lead', 'send warm intro mail (cadence)', ${l.nextActionAt},
        CAST(${l.conversionValueUsd} AS DOUBLE PRECISION), ${l.notes}, ${NOW}, ${OWNER}
      WHERE NOT EXISTS (SELECT 1 FROM vertex_lawfirm_lead WHERE vertex_id = ${vid})
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const l of LEADS) {
    const vid = `at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.lawfirm.lead/${l.leadId}`;
    await sql`DELETE FROM vertex_lawfirm_lead WHERE vertex_id = ${vid}`.execute(db);
  }
}
