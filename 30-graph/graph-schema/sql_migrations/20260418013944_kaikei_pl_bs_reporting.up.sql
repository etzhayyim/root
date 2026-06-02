CREATE MATERIALIZED VIEW mv_kaikei_pl_period AS
      SELECT
        owner_did,
        period_ym,
        account_type,
        SUM(amount)  AS total,
        COUNT(*)     AS entry_count,
        MAX(_seq)    AS _seq
      FROM (
        SELECT
          j.owner_did,
          j.period_ym,
          a.account_type,
          j.debit_amount  AS amount,
          j._seq
        FROM vertex_atrecord_kaikei_journal_entry j
        JOIN vertex_atrecord_kaikei_account a
          ON a.owner_did = j.owner_did
         AND a.vertex_id = j.owner_did || '|com.etzhayyim.apps.kaikei.account|'
                         || SPLIT_PART(j.debit_account_did, ':', 5)
        WHERE a.account_type = 'expense'
        UNION ALL
        SELECT
          j.owner_did,
          j.period_ym,
          a.account_type,
          j.credit_amount AS amount,
          j._seq
        FROM vertex_atrecord_kaikei_journal_entry j
        JOIN vertex_atrecord_kaikei_account a
          ON a.owner_did = j.owner_did
         AND a.vertex_id = j.owner_did || '|com.etzhayyim.apps.kaikei.account|'
                         || SPLIT_PART(j.credit_account_did, ':', 5)
        WHERE a.account_type = 'revenue'
      ) x
      GROUP BY owner_did, period_ym, account_type;

CREATE MATERIALIZED VIEW mv_kaikei_bs_delta AS
      SELECT
        owner_did,
        period_ym,
        account_type,
        SUM(net_amount) AS delta,
        COUNT(*)        AS entry_count,
        MAX(_seq)       AS _seq
      FROM (
        SELECT
          j.owner_did,
          j.period_ym,
          a.account_type,
          j.debit_amount  AS net_amount,
          j._seq
        FROM vertex_atrecord_kaikei_journal_entry j
        JOIN vertex_atrecord_kaikei_account a
          ON a.owner_did = j.owner_did
         AND a.vertex_id = j.owner_did || '|com.etzhayyim.apps.kaikei.account|'
                         || SPLIT_PART(j.debit_account_did, ':', 5)
        WHERE a.account_type IN ('asset','liability','equity')
        UNION ALL
        SELECT
          j.owner_did,
          j.period_ym,
          a.account_type,
          -j.credit_amount AS net_amount,
          j._seq
        FROM vertex_atrecord_kaikei_journal_entry j
        JOIN vertex_atrecord_kaikei_account a
          ON a.owner_did = j.owner_did
         AND a.vertex_id = j.owner_did || '|com.etzhayyim.apps.kaikei.account|'
                         || SPLIT_PART(j.credit_account_did, ':', 5)
        WHERE a.account_type = 'asset'
        UNION ALL
        SELECT
          j.owner_did,
          j.period_ym,
          a.account_type,
          j.credit_amount AS net_amount,
          j._seq
        FROM vertex_atrecord_kaikei_journal_entry j
        JOIN vertex_atrecord_kaikei_account a
          ON a.owner_did = j.owner_did
         AND a.vertex_id = j.owner_did || '|com.etzhayyim.apps.kaikei.account|'
                         || SPLIT_PART(j.credit_account_did, ':', 5)
        WHERE a.account_type IN ('liability','equity')
        UNION ALL
        SELECT
          j.owner_did,
          j.period_ym,
          a.account_type,
          -j.debit_amount AS net_amount,
          j._seq
        FROM vertex_atrecord_kaikei_journal_entry j
        JOIN vertex_atrecord_kaikei_account a
          ON a.owner_did = j.owner_did
         AND a.vertex_id = j.owner_did || '|com.etzhayyim.apps.kaikei.account|'
                         || SPLIT_PART(j.debit_account_did, ':', 5)
        WHERE a.account_type IN ('liability','equity')
      ) x
      GROUP BY owner_did, period_ym, account_type;

CREATE VIEW view_kaikei_monthly_summary AS
      SELECT
        owner_did,
        period_ym,
        account_type,
        total              AS flow_amount,
        NULL::DOUBLE PRECISION AS bs_delta,
        entry_count,
        _seq
      FROM mv_kaikei_pl_period
      UNION ALL
      SELECT
        owner_did,
        period_ym,
        account_type,
        NULL::DOUBLE PRECISION AS flow_amount,
        delta                   AS bs_delta,
        entry_count,
        _seq
      FROM mv_kaikei_bs_delta;
