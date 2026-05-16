CREATE TABLE vertex_open_redsea_patrol (
    vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
    patrol_id varchar NOT NULL, operation varchar NOT NULL,
    flag varchar NOT NULL, vessel_class varchar,
    area_code varchar NOT NULL, started_at varchar NOT NULL, ended_at varchar,
    status varchar NOT NULL, created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE vertex_open_redsea_escort (
    vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
    escort_id varchar NOT NULL, protected_imo varchar NOT NULL,
    escort_patrol_vid varchar, from_waypoint varchar NOT NULL, to_waypoint varchar NOT NULL,
    started_at varchar NOT NULL, ended_at varchar, status varchar NOT NULL,
    created_at varchar, org_id varchar, user_id varchar, actor_id varchar);
