DROP MATERIALIZED VIEW IF EXISTS mv_vertex_yotei_event_count;

DROP MATERIALIZED VIEW IF EXISTS mv_vertex_yotei_booking_count;

DROP MATERIALIZED VIEW IF EXISTS mv_vertex_vin_shipment_volume_count;

DROP MATERIALIZED VIEW IF EXISTS mv_vertex_vin_vehicle_count;

DROP MATERIALIZED VIEW IF EXISTS mv_vertex_livecam_anomaly_count;

DROP MATERIALIZED VIEW IF EXISTS mv_vertex_livecam_detection_event_count;

DROP TABLE IF EXISTS vertex_yotei_booking;

DROP TABLE IF EXISTS vertex_yotei_event;

DROP TABLE IF EXISTS vertex_yotei_availability;

DROP TABLE IF EXISTS vertex_yotei_calendar;

DROP TABLE IF EXISTS vertex_vin_cohort_registration;

DROP TABLE IF EXISTS vertex_vin_shipment_volume;

DROP TABLE IF EXISTS vertex_vin_production_line;

DROP TABLE IF EXISTS vertex_vin_production_plant;

DROP TABLE IF EXISTS vertex_vin_vehicle_type;

DROP TABLE IF EXISTS vertex_vin_wmi_code;

DROP TABLE IF EXISTS vertex_vin_manufacturer;

DROP TABLE IF EXISTS vertex_vin_jurisdiction_registry;

DROP TABLE IF EXISTS vertex_vin_license_plate;

DROP TABLE IF EXISTS vertex_vin_vehicle;

DROP TABLE IF EXISTS vertex_livecam_summary;

DROP TABLE IF EXISTS vertex_livecam_anomaly;

DROP TABLE IF EXISTS vertex_livecam_detection_event;

DROP TABLE IF EXISTS vertex_livecam_vehicle_cohort;

DROP TABLE IF EXISTS vertex_livecam_person_cohort;

DROP TABLE IF EXISTS vertex_livecam_zone;

DROP TABLE IF EXISTS vertex_livecam_camera;
