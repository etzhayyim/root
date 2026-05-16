CREATE TABLE IF NOT EXISTS vertex_flight_offer_alert (
      vertex_id          VARCHAR PRIMARY KEY,
      origin_iata        VARCHAR,
      destination_iata   VARCHAR,
      outbound_date      VARCHAR,
      currency           VARCHAR,
      previous_price     DOUBLE PRECISION,
      new_price          DOUBLE PRECISION,
      drop_pct           DOUBLE PRECISION,
      provider           VARCHAR,
      booking_url        VARCHAR,
      observed_at        VARCHAR,
      sensitivity_ord    BIGINT,
      org_id             VARCHAR,
      user_id            VARCHAR,
      actor_id           VARCHAR
    );
