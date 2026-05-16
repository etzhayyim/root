DROP MATERIALIZED VIEW IF EXISTS mv_vertex_stripe_authorization_count;

DROP MATERIALIZED VIEW IF EXISTS mv_vertex_stripe_issued_card_count;

DROP MATERIALIZED VIEW IF EXISTS mv_vertex_stripe_cardholder_count;

DROP MATERIALIZED VIEW IF EXISTS mv_vertex_shigotoba_company_profile_count;

DROP MATERIALIZED VIEW IF EXISTS mv_vertex_shigotoba_job_posting_count;

DROP TABLE IF EXISTS edge_stripe_cardholder_card;

DROP TABLE IF EXISTS vertex_stripe_spending_limit;

DROP TABLE IF EXISTS vertex_stripe_card_credit_consumption;

DROP TABLE IF EXISTS vertex_stripe_card_credit_allocation;

DROP TABLE IF EXISTS vertex_stripe_authorization;

DROP TABLE IF EXISTS vertex_stripe_issued_card;

DROP TABLE IF EXISTS vertex_stripe_cardholder;

DROP TABLE IF EXISTS edge_shigotoba_posting_company;

DROP TABLE IF EXISTS vertex_shigotoba_company_profile;

DROP TABLE IF EXISTS vertex_shigotoba_job_posting;

DROP TABLE IF EXISTS vertex_auth_account;
