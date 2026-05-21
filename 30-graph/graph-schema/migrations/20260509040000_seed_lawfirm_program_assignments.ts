import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Seed lawfirm.etzhayyim.com program assignments + RACI for tanaka + nishino.
 *
 * Per `gtm-funnel-individual-corporate.md` §0 + `india-lawfirm-llp-plan.md`:
 *   chikada    25% — eng-deploy (CF Worker, demo tenant, Stripe webhook)
 *   tanaka     30% — eng-review (BPMN review, code quality, audit)
 *   nishino    25% — eng-infra (RW MV, consent UI, multi-tenant scope)
 *   k-bakshi   50% — domain lead (per CEO D1 approval iter 9)
 *   a-nakamura 30% — operations
 *
 * Locks tanaka/nishino RACI on key lawfirm.* task NSIDs.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  // ── Assignments (vertex_etzhayyim_assignment) ────────────────────────────
  await sql`
    INSERT INTO vertex_etzhayyim_assignment
      (vertex_id, person_did, role_id, project_id, allocation_pct,
       start_date, status, created_at, owner_did)
    VALUES
      (
        'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.etzhayyim.assignment/chikada-lawfirm-2026',
        'did:web:t-chikada.etzhayyim.com', 'eng-deploy', 'lawfirm-india-program',
        25, '2026-05-08', 'active', now()::varchar, 'did:web:etzhayyim.etzhayyim.com'
      ),
      (
        'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.etzhayyim.assignment/tanaka-lawfirm-2026',
        'did:web:f-tanaka.etzhayyim.com', 'eng-review', 'lawfirm-india-program',
        30, '2026-05-08', 'active', now()::varchar, 'did:web:etzhayyim.etzhayyim.com'
      ),
      (
        'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.etzhayyim.assignment/nishino-lawfirm-2026',
        'did:web:y-nishino.etzhayyim.com', 'eng-infra', 'lawfirm-india-program',
        25, '2026-05-08', 'active', now()::varchar, 'did:web:etzhayyim.etzhayyim.com'
      ),
      (
        'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.etzhayyim.assignment/kbakshi-lawfirm-2026',
        'did:web:k-bakshi.etzhayyim.com', 'clo-lead', 'lawfirm-india-program',
        50, '2026-05-08', 'active', now()::varchar, 'did:web:etzhayyim.etzhayyim.com'
      ),
      (
        'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.etzhayyim.assignment/anakamura-lawfirm-2026',
        'did:web:a-nakamura.etzhayyim.com', 'coo-ops', 'lawfirm-india-program',
        30, '2026-05-08', 'active', now()::varchar, 'did:web:etzhayyim.etzhayyim.com'
      )
  `.execute(db);

  // ── RACI (vertex_etzhayyim_raci) — tanaka/nishino on lawfirm task NSIDs ──
  await sql`
    INSERT INTO vertex_etzhayyim_raci
      (vertex_id, task_nsid, person_did, raci_role, context,
       effective_date, created_at, owner_did)
    VALUES
      -- tanaka (eng-review): R on code review across BPMN + Stripe + esign
      (
        'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.etzhayyim.raci/tanaka-bpmn-review',
        'ai.gftd.apps.lawfirm.engagementClose',
        'did:web:f-tanaka.etzhayyim.com', 'R',
        'BPMN review for the 4-step engagement close pipeline; ensures audit emit + RACI + Spirit floor',
        '2026-05-08', now()::varchar, 'did:web:etzhayyim.etzhayyim.com'
      ),
      (
        'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.etzhayyim.raci/tanaka-stripe-review',
        'ai.gftd.apps.lawfirm.stripeWebhook',
        'did:web:f-tanaka.etzhayyim.com', 'R',
        'Stripe webhook signature verify + idempotency review; PCI scope none (Stripe hosted)',
        '2026-05-08', now()::varchar, 'did:web:etzhayyim.etzhayyim.com'
      ),
      (
        'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.etzhayyim.raci/tanaka-esign-review',
        'ai.gftd.apps.lawfirm.eSignRequest',
        'did:web:f-tanaka.etzhayyim.com', 'R',
        'DocuSign envelope template + recipient routing review',
        '2026-05-08', now()::varchar, 'did:web:etzhayyim.etzhayyim.com'
      ),
      -- nishino (eng-infra): R on RW MV + consent UI + tenant scoping
      (
        'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.etzhayyim.raci/nishino-mv-revenue',
        'mv_lawfirm_revenue_monthly',
        'did:web:y-nishino.etzhayyim.com', 'R',
        'Revenue MV maintenance, freshness SLA <100ms, schema evolution',
        '2026-05-08', now()::varchar, 'did:web:etzhayyim.etzhayyim.com'
      ),
      (
        'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.etzhayyim.raci/nishino-consent-ui',
        'ai.gftd.apps.lawfirm.dpdpConsent',
        'did:web:y-nishino.etzhayyim.com', 'R',
        'DPDP Act 2023 consent UI infra; cascade-purge wiring',
        '2026-05-08', now()::varchar, 'did:web:etzhayyim.etzhayyim.com'
      ),
      (
        'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.etzhayyim.raci/nishino-tenant-scope',
        'lawfirm.tenant_id_scoping',
        'did:web:y-nishino.etzhayyim.com', 'R',
        'Multi-tenant query scope helper, prevents cross-tenant data leak',
        '2026-05-08', now()::varchar, 'did:web:etzhayyim.etzhayyim.com'
      ),
      -- chikada (eng-deploy): R on demo tenant + MS Graph webhook
      (
        'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.etzhayyim.raci/chikada-demo-tenant',
        'lawfirm.demo_tenant_provisioning',
        'did:web:t-chikada.etzhayyim.com', 'R',
        'Demo tenant subdomain + RW namespace + DNS for pilot logos',
        '2026-05-08', now()::varchar, 'did:web:etzhayyim.etzhayyim.com'
      ),
      (
        'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.etzhayyim.raci/chikada-msgraph-webhook',
        'ai.gftd.apps.lawfirm.mailReplyWebhook',
        'did:web:t-chikada.etzhayyim.com', 'R',
        'MS Graph subscription validation + webhook receiver CF Worker route',
        '2026-05-08', now()::varchar, 'did:web:etzhayyim.etzhayyim.com'
      ),
      -- k-bakshi (CLO + advocate): A on all client-facing
      (
        'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.etzhayyim.raci/kbakshi-engagement-close-A',
        'ai.gftd.apps.lawfirm.engagementClose',
        'did:web:k-bakshi.etzhayyim.com', 'A',
        'Final professional responsibility for client engagement; BCI Rule 36 compliance',
        '2026-05-08', now()::varchar, 'did:web:etzhayyim.etzhayyim.com'
      ),
      (
        'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.etzhayyim.raci/kbakshi-pwc-A',
        'ai.gftd.apps.lawfirm.pwcClearanceRequest',
        'did:web:k-bakshi.etzhayyim.com', 'A',
        'PwC clearance request submission + matter unlock authority',
        '2026-05-08', now()::varchar, 'did:web:etzhayyim.etzhayyim.com'
      ),
      -- a-nakamura (COO): A on operations + sales
      (
        'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.etzhayyim.raci/anakamura-pipeline-A',
        'ai.gftd.apps.lawfirm.pipelineTransition',
        'did:web:a-nakamura.etzhayyim.com', 'A',
        'Pipeline stage transition authority + weekly KPI reporting',
        '2026-05-08', now()::varchar, 'did:web:etzhayyim.etzhayyim.com'
      ),
      (
        'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.etzhayyim.raci/anakamura-marketing-A',
        'ai.gftd.apps.lawfirm.marketingDispatch',
        'did:web:a-nakamura.etzhayyim.com', 'A',
        'Marketing tick + ad-hoc dispatch authority; brand guardrail review',
        '2026-05-08', now()::varchar, 'did:web:etzhayyim.etzhayyim.com'
      ),
      -- CEO j-kawasaki: A on PwC clearance final + budget
      (
        'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.etzhayyim.raci/jkawasaki-pwc-final-A',
        'ai.gftd.apps.lawfirm.pwcClearanceRequest',
        'did:web:j-kawasaki.etzhayyim.com', 'A',
        'PwC clearance final HITL approval (per CEO D4 decision)',
        '2026-05-08', now()::varchar, 'did:web:etzhayyim.etzhayyim.com'
      )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DELETE FROM vertex_etzhayyim_raci WHERE context LIKE '%lawfirm%' OR context LIKE '%pwc%' OR context LIKE '%pipeline stage%'`.execute(db);
  await sql`DELETE FROM vertex_etzhayyim_assignment WHERE project_id = 'lawfirm-india-program'`.execute(db);
}
