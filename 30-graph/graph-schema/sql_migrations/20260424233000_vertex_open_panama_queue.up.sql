CREATE TABLE vertex_open_panama_anchorage_queue (
    vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
    queue_id varchar NOT NULL, imo varchar NOT NULL, anchorage_zone varchar NOT NULL,
    arrived_at varchar NOT NULL, queued_position int, departed_at varchar,
    dwell_hours double precision, status varchar NOT NULL,
    created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE vertex_open_panama_priority (
    vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
    assignment_id varchar NOT NULL, imo varchar NOT NULL,
    priority_class varchar NOT NULL, reason varchar, assigned_slot_date varchar NOT NULL,
    require_broadcast boolean, assigned_at varchar NOT NULL, status varchar NOT NULL,
    created_at varchar, org_id varchar, user_id varchar, actor_id varchar);
