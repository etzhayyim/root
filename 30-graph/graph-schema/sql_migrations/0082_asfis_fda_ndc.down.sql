DROP VIEW IF EXISTS view_asfis_species;

DROP VIEW IF EXISTS view_fda_ndc;

DELETE FROM vertex_repo_record WHERE collection = 'ai.gftd.apps.asfis.species';

DELETE FROM vertex_repo_record WHERE collection = 'ai.gftd.apps.fda.ndc';

DELETE FROM dim_world_domain WHERE domain IN ('asfis','fda_ndc');

DELETE FROM edge_classified_as WHERE system = 'atc_ndc';
