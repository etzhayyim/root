-- Reverse of 20260510020200_keiei_apqc_isco_binding.up.sql

DROP TABLE IF EXISTS edge_keiei_role_isco;
DROP TABLE IF EXISTS edge_keiei_role_owns_apqc;

ALTER TABLE vertex_keiei_role DROP COLUMN IF EXISTS isco_08_skill_level;
ALTER TABLE vertex_keiei_role DROP COLUMN IF EXISTS isco_08_label;
ALTER TABLE vertex_keiei_role DROP COLUMN IF EXISTS isco_08_unit_group;
ALTER TABLE vertex_keiei_role DROP COLUMN IF EXISTS apqc_pcf_l1_set;
ALTER TABLE vertex_keiei_role DROP COLUMN IF EXISTS apqc_pcf_l1_primary;

FLUSH;
