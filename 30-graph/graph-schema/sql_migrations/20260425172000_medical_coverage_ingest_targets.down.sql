DELETE FROM dim_world_domain_collection
    WHERE (domain = 'gakujutsu_ronbun' AND collection = 'com.etzhayyim.apps.iryo.pubmedPaper')
       OR (domain = 'rinshou_shiken'   AND collection = 'com.etzhayyim.apps.iryo.rinshou')
       OR (domain = 'iryo_shisetsu'    AND collection = 'com.etzhayyim.apps.iryo.shisetsu')
       OR (domain = 'dsm_shikkan'      AND collection = 'com.etzhayyim.apps.iryo.dsmCategory');

DELETE FROM dim_world_domain WHERE domain = 'dsm_shikkan';
