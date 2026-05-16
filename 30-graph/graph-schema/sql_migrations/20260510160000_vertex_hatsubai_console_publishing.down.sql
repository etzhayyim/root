-- Down: drop hatsubai console-publishing schema.

DROP MATERIALIZED VIEW IF EXISTS mv_hatsubai_release_calendar;
DROP MATERIALIZED VIEW IF EXISTS mv_hatsubai_partner_devkit_utilization;
DROP MATERIALIZED VIEW IF EXISTS mv_hatsubai_title_age_rating_coverage;
DROP MATERIALIZED VIEW IF EXISTS mv_hatsubai_title_trc_open_failures;
DROP MATERIALIZED VIEW IF EXISTS mv_hatsubai_title_cert_status_latest;

DROP TABLE IF EXISTS edge_hatsubai_rating_required_for_listing;
DROP TABLE IF EXISTS edge_hatsubai_localized_into;
DROP TABLE IF EXISTS edge_hatsubai_publisher_publishes;
DROP TABLE IF EXISTS edge_hatsubai_submission_for_build;
DROP TABLE IF EXISTS edge_hatsubai_build_of_title;
DROP TABLE IF EXISTS edge_hatsubai_title_targets_platform;
DROP TABLE IF EXISTS edge_hatsubai_partner_devkit_holds;

DROP TABLE IF EXISTS vertex_hatsubai_store_asset;
DROP TABLE IF EXISTS vertex_hatsubai_store_listing;
DROP TABLE IF EXISTS vertex_hatsubai_age_rating;
DROP TABLE IF EXISTS vertex_hatsubai_cert_submission;
DROP TABLE IF EXISTS vertex_hatsubai_trc_check;
DROP TABLE IF EXISTS vertex_hatsubai_title_build;
DROP TABLE IF EXISTS vertex_hatsubai_title;
DROP TABLE IF EXISTS vertex_hatsubai_sdk_version;
DROP TABLE IF EXISTS vertex_hatsubai_devkit;
DROP TABLE IF EXISTS vertex_hatsubai_partner_account;
DROP TABLE IF EXISTS vertex_hatsubai_platform;

FLUSH;
