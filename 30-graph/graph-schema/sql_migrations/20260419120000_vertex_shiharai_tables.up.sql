CREATE TABLE IF NOT EXISTS vertex_shiharai_biller (
      vertex_id          VARCHAR PRIMARY KEY,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      rkey               VARCHAR,
      repo               VARCHAR,
      biller_handle      VARCHAR,
      display_name       VARCHAR,
      country            VARCHAR,
      site_url           VARCHAR,
      pay_url            VARCHAR,
      recurring_url      VARCHAR,
      adapter            VARCHAR,
      auth_kind          VARCHAR,
      keychain_service   VARCHAR,
      capabilities       VARCHAR,
      notes              VARCHAR,
      created_at         VARCHAR,
      org_id             VARCHAR,
      user_id            VARCHAR,
      actor_id           VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_shiharai_bill (
      vertex_id          VARCHAR PRIMARY KEY,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      rkey               VARCHAR,
      repo               VARCHAR,
      bill_id            VARCHAR,
      issuer             VARCHAR,
      biller_handle      VARCHAR,
      amount_jpy         BIGINT,
      currency           VARCHAR,
      due_date           VARCHAR,
      customer_number    VARCHAR,
      invoice_number     VARCHAR,
      pay_url            VARCHAR,
      method             VARCHAR,
      source_email_id    VARCHAR,
      state              VARCHAR,
      extracted_at       VARCHAR,
      paid_at            VARCHAR,
      cancelled_at       VARCHAR,
      created_at         VARCHAR,
      org_id             VARCHAR,
      user_id            VARCHAR,
      actor_id           VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_shiharai_payment (
      vertex_id          VARCHAR PRIMARY KEY,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      rkey               VARCHAR,
      repo               VARCHAR,
      payment_id         VARCHAR,
      bill_id            VARCHAR,
      biller_handle      VARCHAR,
      amount_jpy         BIGINT,
      method             VARCHAR,
      result_tx_id       VARCHAR,
      page_snapshot_cid  VARCHAR,
      approved_by_did    VARCHAR,
      approval_token_hash VARCHAR,
      committed_at       VARCHAR,
      created_at         VARCHAR,
      org_id             VARCHAR,
      user_id            VARCHAR,
      actor_id           VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_shiharai_recurring (
      vertex_id          VARCHAR PRIMARY KEY,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      rkey               VARCHAR,
      repo               VARCHAR,
      recurring_id       VARCHAR,
      biller_handle      VARCHAR,
      customer_number    VARCHAR,
      pay_method         VARCHAR,
      state              VARCHAR,
      registered_at      VARCHAR,
      cancelled_at       VARCHAR,
      created_at         VARCHAR,
      org_id             VARCHAR,
      user_id            VARCHAR,
      actor_id           VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_shiharai_job (
      vertex_id          VARCHAR PRIMARY KEY,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      rkey               VARCHAR,
      repo               VARCHAR,
      job_id             VARCHAR,
      bill_id            VARCHAR,
      biller_handle      VARCHAR,
      method             VARCHAR,
      pay_url            VARCHAR,
      state              VARCHAR,
      require_confirm    VARCHAR,
      daemon_id          VARCHAR,
      enqueued_at        VARCHAR,
      dispatched_at      VARCHAR,
      started_at         VARCHAR,
      finished_at        VARCHAR,
      expires_at         VARCHAR,
      last_error         VARCHAR,
      page_snapshot_cid  VARCHAR,
      result_tx_id       VARCHAR,
      created_at         VARCHAR,
      org_id             VARCHAR,
      user_id            VARCHAR,
      actor_id           VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_shiharai_job_result (
      vertex_id          VARCHAR PRIMARY KEY,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      rkey               VARCHAR,
      repo               VARCHAR,
      job_id             VARCHAR,
      outcome            VARCHAR,
      page_snapshot_cid  VARCHAR,
      result_tx_id       VARCHAR,
      error_message      VARCHAR,
      reported_at        VARCHAR,
      created_at         VARCHAR,
      org_id             VARCHAR,
      user_id            VARCHAR,
      actor_id           VARCHAR
    );

CREATE TABLE IF NOT EXISTS edge_shiharai_bill_for_biller (
      edge_id            VARCHAR PRIMARY KEY,
      src_vid            VARCHAR,
      dst_vid            VARCHAR,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      bill_id            VARCHAR,
      biller_handle      VARCHAR,
      created_at         VARCHAR
    );

CREATE TABLE IF NOT EXISTS edge_shiharai_payment_settles_bill (
      edge_id            VARCHAR PRIMARY KEY,
      src_vid            VARCHAR,
      dst_vid            VARCHAR,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      payment_id         VARCHAR,
      bill_id            VARCHAR,
      created_at         VARCHAR
    );

CREATE TABLE IF NOT EXISTS edge_shiharai_job_processes_bill (
      edge_id            VARCHAR PRIMARY KEY,
      src_vid            VARCHAR,
      dst_vid            VARCHAR,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      job_id             VARCHAR,
      bill_id            VARCHAR,
      created_at         VARCHAR
    );

CREATE TABLE IF NOT EXISTS edge_shiharai_result_reports_job (
      edge_id            VARCHAR PRIMARY KEY,
      src_vid            VARCHAR,
      dst_vid            VARCHAR,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      job_id             VARCHAR,
      outcome            VARCHAR,
      created_at         VARCHAR
    );

CREATE TABLE IF NOT EXISTS edge_shiharai_recurring_for_biller (
      edge_id            VARCHAR PRIMARY KEY,
      src_vid            VARCHAR,
      dst_vid            VARCHAR,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      recurring_id       VARCHAR,
      biller_handle      VARCHAR,
      created_at         VARCHAR
    );

CREATE TABLE IF NOT EXISTS edge_shiharai_bill_from_email (
      edge_id            VARCHAR PRIMARY KEY,
      src_vid            VARCHAR,
      dst_vid            VARCHAR,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      bill_id            VARCHAR,
      source_email_id    VARCHAR,
      created_at         VARCHAR
    );
