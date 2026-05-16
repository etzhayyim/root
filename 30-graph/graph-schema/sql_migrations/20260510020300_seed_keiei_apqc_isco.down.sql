-- Reverse seed of 20260510020300_seed_keiei_apqc_isco.up.sql.
-- Removes the APQC + ISCO edges. The vertex_keiei_role rows are *not*
-- deleted because the prior seed migration (20260510020100) owns those
-- rows; this seed only re-inserts to fill new columns.

DELETE FROM edge_keiei_role_isco       WHERE owner_did = 'did:web:etz-hayim';
DELETE FROM edge_keiei_role_owns_apqc  WHERE owner_did = 'did:web:etz-hayim';

FLUSH;
