DELETE FROM vertex_repo_record
    WHERE collection = 'ai.gftd.apps.hs.commodity';

UPDATE dim_world_domain SET world_total = 6708 WHERE domain = 'hs';
