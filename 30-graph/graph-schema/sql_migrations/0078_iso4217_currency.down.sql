DROP VIEW IF EXISTS view_iso4217_currency;

DELETE FROM vertex_repo_record WHERE collection = 'ai.gftd.apps.iso4217.currency';

DELETE FROM dim_world_domain WHERE domain = 'iso4217';
