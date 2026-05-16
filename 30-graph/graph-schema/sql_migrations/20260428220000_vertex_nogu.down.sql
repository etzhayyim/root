DROP INDEX IF EXISTS idx_nogu_disposal_item;

DROP TABLE IF EXISTS vertex_nogu_disposal;

DROP INDEX IF EXISTS idx_nogu_lease_status;

DROP INDEX IF EXISTS idx_nogu_lease_lessee;

DROP INDEX IF EXISTS idx_nogu_lease_item;

DROP TABLE IF EXISTS vertex_nogu_lease;

DROP INDEX IF EXISTS idx_nogu_maintenance_status;

DROP INDEX IF EXISTS idx_nogu_maintenance_item;

DROP TABLE IF EXISTS vertex_nogu_maintenance;

DROP INDEX IF EXISTS idx_nogu_inspection_item;

DROP TABLE IF EXISTS vertex_nogu_inspection;

DROP INDEX IF EXISTS idx_nogu_item_inspection;

DROP INDEX IF EXISTS idx_nogu_item_status;

DROP INDEX IF EXISTS idx_nogu_item_owner;

DROP TABLE IF EXISTS vertex_nogu_item;

FLUSH;
