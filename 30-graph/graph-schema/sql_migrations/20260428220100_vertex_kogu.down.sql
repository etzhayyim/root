DROP INDEX IF EXISTS idx_kogu_inspection_tool;

DROP TABLE IF EXISTS vertex_kogu_inspection;

DROP INDEX IF EXISTS idx_kogu_checkout_status;

DROP INDEX IF EXISTS idx_kogu_checkout_borrower;

DROP INDEX IF EXISTS idx_kogu_checkout_tool;

DROP TABLE IF EXISTS vertex_kogu_checkout;

DROP INDEX IF EXISTS idx_kogu_calibration_tool;

DROP TABLE IF EXISTS vertex_kogu_calibration;

DROP INDEX IF EXISTS idx_kogu_item_calibration;

DROP INDEX IF EXISTS idx_kogu_item_status;

DROP INDEX IF EXISTS idx_kogu_item_custodian;

DROP TABLE IF EXISTS vertex_kogu_item;

FLUSH;
