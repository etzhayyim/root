-- Reverse seed of 20260510020100_seed_keiei_cxo.up.sql
-- Removes the keiei controller's seeded rows, leaves the schema intact.

DELETE FROM edge_keiei_reports_to       WHERE owner_did = 'did:web:etz-hayim';
DELETE FROM edge_keiei_role_has_profile WHERE owner_did = 'did:web:etz-hayim';
DELETE FROM edge_keiei_agent_acts_as    WHERE owner_did = 'did:web:etz-hayim';
DELETE FROM vertex_keiei_profile        WHERE actor_did = 'did:web:keiei.gftd.ai';
DELETE FROM vertex_keiei_agent          WHERE actor_did = 'did:web:keiei.gftd.ai';
DELETE FROM vertex_keiei_role           WHERE actor_did = 'did:web:keiei.gftd.ai';

FLUSH;
