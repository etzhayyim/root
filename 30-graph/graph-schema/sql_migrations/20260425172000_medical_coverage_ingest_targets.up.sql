DELETE FROM dim_world_domain_collection
    WHERE (domain = 'gakujutsu_ronbun' AND collection = 'ai.gftd.apps.iryo.pubmedPaper')
       OR (domain = 'rinshou_shiken'   AND collection = 'ai.gftd.apps.iryo.rinshou')
       OR (domain = 'iryo_shisetsu'    AND collection = 'ai.gftd.apps.iryo.shisetsu')
       OR (domain = 'dsm_shikkan'      AND collection = 'ai.gftd.apps.iryo.dsmCategory');

INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES
      ('gakujutsu_ronbun', 'iryo', 'ai.gftd.apps.iryo.pubmedPaper', 200000000, 'academic papers indexed by PubMed/Semantic Scholar/Crossref', 'healthcare'),
      ('rinshou_shiken',   'iryo', 'ai.gftd.apps.iryo.rinshou',        500000, 'registered clinical trials', 'healthcare'),
      ('iryo_shisetsu',    'iryo', 'ai.gftd.apps.iryo.shisetsu',      1000000, 'hospitals and clinics', 'healthcare'),
      ('dsm_shikkan',      'iryo', 'ai.gftd.apps.iryo.dsmCategory',        21, 'DSM public category-level taxonomy rows', 'healthcare');

DELETE FROM dim_world_domain
    WHERE domain = 'dsm_shikkan';

INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('dsm_shikkan', 'iryo', 21, 'DSM public category-level taxonomy rows', 'healthcare');
