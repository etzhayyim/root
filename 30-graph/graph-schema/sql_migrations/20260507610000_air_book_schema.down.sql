DROP MATERIALIZED VIEW IF EXISTS mv_air_booking_by_route;

DROP INDEX IF EXISTS idx_air_book_pnr_carrier_dep;

DROP INDEX IF EXISTS idx_air_book_ticket_no;

DROP INDEX IF EXISTS idx_air_book_pnr_id;

DROP TABLE IF EXISTS edge_air_pnr_has_ancillary;

DROP TABLE IF EXISTS edge_air_pnr_has_ticket;

DROP TABLE IF EXISTS vertex_air_book_bsp_settlement;

DROP TABLE IF EXISTS vertex_air_book_ancillary;

DROP TABLE IF EXISTS vertex_air_book_ticket;

DROP TABLE IF EXISTS vertex_air_book_pnr;
