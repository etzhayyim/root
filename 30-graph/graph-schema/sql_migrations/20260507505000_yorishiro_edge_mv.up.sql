INSERT INTO edge_yorishiro_nuro_offer_claim (
      edge_id, src_vid, dst_vid, relation, provider, job_id, owner_did, actor_id, created_at
    )
    SELECT
      'edge:nuro:offer-claim:' || o.campaign_code || ':' || j.job_id,
      o.vertex_id,
      j.vertex_id,
      'CLAIMS_OFFER',
      j.provider,
      j.job_id,
      coalesce(j.owner_did, o.owner_did),
      j.actor_id,
      j.created_at
    FROM vertex_yorishiroNuro_offer o
    JOIN vertex_yorishiroNuro_claimJob j ON j.campaign_code = o.campaign_code
    ON CONFLICT (edge_id) DO NOTHING;

INSERT INTO edge_yorishiro_nuro_claim_receipt (
      edge_id, src_vid, dst_vid, relation, provider, job_id, owner_did, actor_id, created_at
    )
    SELECT
      'edge:nuro:claim-receipt:' || j.job_id || ':' || r.receipt_id,
      j.vertex_id,
      r.vertex_id,
      'PRODUCED_RECEIPT',
      j.provider,
      j.job_id,
      coalesce(r.owner_did, j.owner_did),
      r.actor_id,
      r.created_at
    FROM vertex_yorishiroNuro_claimJob j
    JOIN vertex_yorishiroNuro_claimReceipt r ON r.job_id = j.job_id
    ON CONFLICT (edge_id) DO NOTHING;

INSERT INTO edge_yorishiro_enaiyo_draft_docx_blob (
      edge_id, src_vid, dst_vid, relation, provider, job_id, owner_did, actor_id, created_at
    )
    SELECT
      'edge:enaiyo:draft-docx:' || d.draft_id || ':' || b.job_id,
      d.vertex_id,
      b.vertex_id,
      'RENDERED_DOCX',
      NULL,
      b.job_id,
      coalesce(b.owner_did, d.owner_did),
      b.actor_id,
      b.created_at
    FROM vertex_yorishiroEnaiyo_draftNaiyo d
    JOIN vertex_yorishiroEnaiyo_docxBlob b ON b.draft_id = d.draft_id
    ON CONFLICT (edge_id) DO NOTHING;

INSERT INTO edge_yorishiro_enaiyo_draft_submit_job (
      edge_id, src_vid, dst_vid, relation, provider, job_id, owner_did, actor_id, created_at
    )
    SELECT
      'edge:enaiyo:draft-submit:' || d.draft_id || ':' || s.job_id,
      d.vertex_id,
      s.vertex_id,
      'SUBMITTED_BY_JOB',
      s.provider,
      s.job_id,
      coalesce(s.owner_did, d.owner_did),
      s.actor_id,
      s.created_at
    FROM vertex_yorishiroEnaiyo_draftNaiyo d
    JOIN vertex_yorishiroEnaiyo_submitJob s ON s.draft_id = d.draft_id
    ON CONFLICT (edge_id) DO NOTHING;

INSERT INTO edge_yorishiro_enaiyo_submit_receipt (
      edge_id, src_vid, dst_vid, relation, provider, job_id, owner_did, actor_id, created_at
    )
    SELECT
      'edge:enaiyo:submit-receipt:' || s.job_id || ':' || r.receipt_id,
      s.vertex_id,
      r.vertex_id,
      'PRODUCED_RECEIPT',
      s.provider,
      s.job_id,
      coalesce(r.owner_did, s.owner_did),
      r.actor_id,
      r.created_at
    FROM vertex_yorishiroEnaiyo_submitJob s
    JOIN vertex_yorishiroEnaiyo_receipt r ON r.job_id = s.job_id
    ON CONFLICT (edge_id) DO NOTHING;

INSERT INTO edge_yorishiro_enaiyo_batch_draft (
      edge_id, src_vid, dst_vid, relation, provider, job_id, owner_did, actor_id, created_at
    )
    SELECT
      'edge:enaiyo:batch-draft:' || b.batch_id || ':' || d.draft_id,
      b.vertex_id,
      d.vertex_id,
      'INCLUDES_DRAFT',
      b.provider,
      b.batch_id,
      coalesce(b.owner_did, d.owner_did),
      b.actor_id,
      b.created_at
    FROM vertex_yorishiroEnaiyo_batchJob b
    JOIN LATERAL jsonb_array_elements_text(coalesce(nullif(b.draft_ids, '')::jsonb, '[]'::jsonb)) draft_id(value) ON TRUE
    JOIN vertex_yorishiroEnaiyo_draftNaiyo d ON d.draft_id = draft_id.value
    ON CONFLICT (edge_id) DO NOTHING;

INSERT INTO edge_yorishiro_flyio_job_provider (
      edge_id, src_vid, dst_vid, relation, provider, job_id, owner_did, actor_id, created_at
    )
    SELECT
      'edge:flyio:provider:' || job_id,
      vertex_id,
      provider,
      'RUNS_BROWSER_SESSION',
      provider,
      job_id,
      owner_did,
      actor_id,
      created_at
    FROM vertex_yorishiroFlyio_cancellationJob
    WHERE provider IS NOT NULL AND provider <> ''
    ON CONFLICT (edge_id) DO NOTHING;

INSERT INTO edge_yorishiro_flyio_job_provider (
      edge_id, src_vid, dst_vid, relation, provider, job_id, owner_did, actor_id, created_at
    )
    SELECT
      'edge:flyio:provider:' || job_id,
      vertex_id,
      provider,
      'RUNS_BROWSER_SESSION',
      provider,
      job_id,
      owner_did,
      actor_id,
      created_at
    FROM vertex_yorishiroFlyio_appDeleteJob
    WHERE provider IS NOT NULL AND provider <> ''
    ON CONFLICT (edge_id) DO NOTHING;

INSERT INTO edge_yorishiro_flyio_job_provider (
      edge_id, src_vid, dst_vid, relation, provider, job_id, owner_did, actor_id, created_at
    )
    SELECT
      'edge:flyio:provider:' || job_id,
      vertex_id,
      provider,
      'RUNS_BROWSER_SESSION',
      provider,
      job_id,
      owner_did,
      actor_id,
      created_at
    FROM vertex_yorishiroFlyio_orgDeleteJob
    WHERE provider IS NOT NULL AND provider <> ''
    ON CONFLICT (edge_id) DO NOTHING;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_yorishiro_nuro_claim_flow AS
    SELECT
      j.job_id,
      j.campaign_code,
      j.status,
      j.created_at,
      r.receipt_number,
      r.submitted_at,
      r.amount_jpy,
      o.title AS offer_title,
      o.window_open,
      o.window_close
    FROM vertex_yorishiroNuro_claimJob j
    LEFT JOIN vertex_yorishiroNuro_claimReceipt r ON r.job_id = j.job_id
    LEFT JOIN vertex_yorishiroNuro_offer o ON o.campaign_code = j.campaign_code;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_yorishiro_enaiyo_submission_flow AS
    SELECT
      d.draft_id,
      d.status AS draft_status,
      s.job_id,
      s.status AS submit_status,
      r.receipt_number,
      r.submitted_at,
      b.blob_key AS docx_blob_key,
      d.created_at
    FROM vertex_yorishiroEnaiyo_draftNaiyo d
    LEFT JOIN vertex_yorishiroEnaiyo_submitJob s ON s.draft_id = d.draft_id
    LEFT JOIN vertex_yorishiroEnaiyo_receipt r ON r.job_id = s.job_id
    LEFT JOIN vertex_yorishiroEnaiyo_docxBlob b ON b.draft_id = d.draft_id;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_yorishiro_flyio_job_status AS
    SELECT 'cancellation' AS job_kind, phase AS action, status, count(*) AS job_count, max(created_at) AS latest_created_at
    FROM vertex_yorishiroFlyio_cancellationJob
    GROUP BY phase, status
    UNION ALL
    SELECT 'app_delete' AS job_kind, 'deleteApp' AS action, status, count(*) AS job_count, max(created_at) AS latest_created_at
    FROM vertex_yorishiroFlyio_appDeleteJob
    GROUP BY status
    UNION ALL
    SELECT 'org_delete' AS job_kind, 'deleteOrg' AS action, status, count(*) AS job_count, max(created_at) AS latest_created_at
    FROM vertex_yorishiroFlyio_orgDeleteJob
    GROUP BY status;
