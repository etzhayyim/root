DROP VIEW IF EXISTS view_icd10_disease;

DELETE FROM vertex_repo_record WHERE collection = 'ai.gftd.apps.icd10.disease';

DELETE FROM dim_world_domain WHERE domain = 'icd10';

DELETE FROM edge_classified_as WHERE system = 'iso4217_iso3166';
