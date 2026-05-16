DELETE FROM dim_world_domain_collection
    WHERE (domain = 'gakujutsu_ronbun' AND collection = 'ai.gftd.apps.iryo.pubmedPaper')
       OR (domain = 'rinshou_shiken'   AND collection = 'ai.gftd.apps.iryo.rinshou')
       OR (domain = 'iryo_shisetsu'    AND collection = 'ai.gftd.apps.iryo.shisetsu')
       OR (domain = 'dsm_shikkan'      AND collection = 'ai.gftd.apps.iryo.dsmCategory');

DELETE FROM dim_world_domain WHERE domain = 'dsm_shikkan';
