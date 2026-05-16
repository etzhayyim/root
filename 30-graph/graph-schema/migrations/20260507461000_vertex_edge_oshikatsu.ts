import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_oshikatsu_creator_profile (
      vertex_id VARCHAR PRIMARY KEY,
      id VARCHAR,
      creator_did VARCHAR,
      display_name VARCHAR,
      bio TEXT,
      tiers TEXT,
      subscriber_count BIGINT,
      total_earned_credits DOUBLE PRECISION,
      status VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      sensitivity_ord BIGINT,
      owner_did VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_oshikatsu_subscription_tier (
      vertex_id VARCHAR PRIMARY KEY,
      tier_id VARCHAR,
      rank BIGINT,
      name VARCHAR,
      label VARCHAR,
      price_credits DOUBLE PRECISION,
      description TEXT,
      creator_did VARCHAR,
      updated_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      sensitivity_ord BIGINT,
      owner_did VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_oshikatsu_subscription (
      vertex_id VARCHAR PRIMARY KEY,
      id VARCHAR,
      subscriber_did VARCHAR,
      creator_did VARCHAR,
      tier VARCHAR,
      price_credits DOUBLE PRECISION,
      status VARCHAR,
      started_at VARCHAR,
      expires_at VARCHAR,
      auto_renew BOOLEAN,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      sensitivity_ord BIGINT,
      owner_did VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_oshikatsu_subscription_cancel (
      vertex_id VARCHAR PRIMARY KEY,
      id VARCHAR,
      subscriber_did VARCHAR,
      creator_did VARCHAR,
      cancelled_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      sensitivity_ord BIGINT,
      owner_did VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_oshikatsu_exclusive_content (
      vertex_id VARCHAR PRIMARY KEY,
      id VARCHAR,
      creator_did VARCHAR,
      title VARCHAR,
      body TEXT,
      content_type VARCHAR,
      min_tier VARCHAR,
      media_urls TEXT,
      preview_text TEXT,
      like_count BIGINT,
      comment_count BIGINT,
      tip_total_credits DOUBLE PRECISION,
      status VARCHAR,
      published_at VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      sensitivity_ord BIGINT,
      owner_did VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_oshikatsu_tip (
      vertex_id VARCHAR PRIMARY KEY,
      id VARCHAR,
      from_did VARCHAR,
      creator_did VARCHAR,
      content_id VARCHAR,
      amount DOUBLE PRECISION,
      message TEXT,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      sensitivity_ord BIGINT,
      owner_did VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_oshikatsu_creator_tier (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR,
      dst_vid VARCHAR,
      creator_did VARCHAR,
      tier_id VARCHAR,
      relation VARCHAR,
      created_at VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_oshikatsu_subscription (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR,
      dst_vid VARCHAR,
      subscriber_did VARCHAR,
      creator_did VARCHAR,
      subscription_id VARCHAR,
      tier VARCHAR,
      relation VARCHAR,
      created_at VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_oshikatsu_content_by_creator (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR,
      dst_vid VARCHAR,
      creator_did VARCHAR,
      content_id VARCHAR,
      relation VARCHAR,
      created_at VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_oshikatsu_tip_to_creator (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR,
      dst_vid VARCHAR,
      from_did VARCHAR,
      creator_did VARCHAR,
      tip_id VARCHAR,
      amount DOUBLE PRECISION,
      relation VARCHAR,
      created_at VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_oshikatsu_tip_for_content (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR,
      dst_vid VARCHAR,
      tip_id VARCHAR,
      content_id VARCHAR,
      relation VARCHAR,
      created_at VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT
    )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS edge_oshikatsu_tip_for_content`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_oshikatsu_tip_to_creator`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_oshikatsu_content_by_creator`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_oshikatsu_subscription`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_oshikatsu_creator_tier`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_oshikatsu_tip`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_oshikatsu_exclusive_content`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_oshikatsu_subscription_cancel`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_oshikatsu_subscription`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_oshikatsu_subscription_tier`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_oshikatsu_creator_profile`.execute(db);
}
