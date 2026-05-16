DROP MATERIALIZED VIEW IF EXISTS mv_air_crew_fatigue_risk;

DROP INDEX IF EXISTS idx_air_crew_duty_time_crew_date;

DROP INDEX IF EXISTS idx_air_crew_pairing_carrier_id;

DROP INDEX IF EXISTS idx_air_crew_roster_crew_date;

DROP TABLE IF EXISTS edge_air_crew_roster_has_pairing;

DROP TABLE IF EXISTS vertex_air_crew_qualification;

DROP TABLE IF EXISTS vertex_air_crew_duty_time;

DROP TABLE IF EXISTS vertex_air_crew_pairing;

DROP TABLE IF EXISTS vertex_air_crew_roster;
