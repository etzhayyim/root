CREATE TABLE vertex_open_panama_toll_payment (
    vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
    payment_id varchar NOT NULL, transit_vid varchar, imo varchar NOT NULL,
    base_toll_usd double precision NOT NULL, auction_premium_usd double precision,
    total_toll_usd double precision NOT NULL, paid_at varchar NOT NULL, status varchar NOT NULL,
    created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE vertex_open_panama_auction (
    vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
    auction_id varchar NOT NULL, slot_date varchar NOT NULL, lane varchar NOT NULL,
    winning_bid_usd double precision NOT NULL, bidder_imo varchar, bid_count int,
    closed_at varchar NOT NULL, status varchar NOT NULL,
    created_at varchar, org_id varchar, user_id varchar, actor_id varchar);
