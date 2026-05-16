"""Captured from Kysely migration 20260416220000_collection_domain_coverage_mappings."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260416220000_collection_domain_coverage_mappings"
down_revision = 'r_20260416210000_belief_system_emotion_graph'
branch_labels = None
depends_on = None

UP = [{'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('bus_stop', 'bus', 'ai.gftd.apps.bus.busStop', 5000000, 'bus stops "
         "(global)', 'transport')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('shukyo_shisetsu', 'religious', 'ai.gftd.apps.religious.place', 5000000, "
         "'religious institutions', 'culture')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('religious', 'religious', 'ai.gftd.apps.religious.order', 4300, 'religious "
         "legal systems', 'governance')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('religious', 'religious', 'ai.gftd.apps.religious.system', 4300, 'religious "
         "legal systems', 'governance')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('shukyo_shisetsu', 'religious', 'ai.gftd.apps.religious.denomination', "
         "5000000, 'religious institutions', 'culture')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('tentai_asteroid', 'tentai', 'ai.gftd.apps.tentai.asteroid', 1300000, "
         "'asteroids', 'space')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('tentai_galaxy', 'tentai', 'ai.gftd.apps.tentai.galaxy', 2000000, "
         "'galaxies', 'space')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('tentai_exoplanet', 'tentai', 'ai.gftd.apps.tentai.exoplanet', 5700, "
         "'exoplanets', 'space')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('tentai_comet', 'tentai', 'ai.gftd.apps.tentai.comet', 4000, 'comets', "
         "'space')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('tentai_star', 'tentai', 'ai.gftd.apps.tentai.star', 1800000000, 'catalogued "
         "stars', 'space')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('media_gamers', 'media-gamers', 'ai.gftd.apps.media_gamers.title', 900000, "
         "'game titles', 'content')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('media_anime', 'media-anime', 'ai.gftd.apps.media_anime.title', 25000, "
         "'anime titles', 'content')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('manga', 'manga', 'ai.gftd.apps.manga.title', 150000, 'manga titles', "
         "'content')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('drama', 'drama', 'ai.gftd.apps.drama.title', 100000, 'TV drama titles', "
         "'content')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('drama', 'drama', 'ai.gftd.apps.drama.show', 100000, 'TV drama titles', "
         "'content')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('character_anime', 'character', 'ai.gftd.apps.character.anime', 500000, "
         "'anime characters', 'fiction')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('character_manga', 'character', 'ai.gftd.apps.character.manga', 2000000, "
         "'manga characters', 'fiction')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('character_tv', 'character', 'ai.gftd.apps.character.tv', 3000000, 'TV "
         "characters', 'fiction')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('character_game', 'character', 'ai.gftd.apps.character.game', 9000000, 'game "
         "characters', 'fiction')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('character_book', 'character', 'ai.gftd.apps.character.book', 500000000, "
         "'book characters', 'fiction')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('character', 'character', 'ai.gftd.apps.character.animated', 500000000, "
         "'fictional characters', 'fiction')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('character', 'character', 'ai.gftd.apps.character.mythology', 500000000, "
         "'fictional characters', 'fiction')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('character', 'character', 'ai.gftd.apps.character.comic', 500000000, "
         "'fictional characters', 'fiction')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('gakko', 'gakko', 'ai.gftd.apps.gakko.gakko', 1000000, 'schools & "
         "universities', 'education')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('rinshou_shiken', 'iryo', 'ai.gftd.apps.iryo.rinshou', 500000, 'clinical "
         "trials', 'healthcare')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('iryo_shisetsu', 'iryo', 'ai.gftd.apps.iryo.shisetsu', 1000000, 'hospitals & "
         "clinics', 'healthcare')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('icd_shikkan', 'iryo', 'ai.gftd.apps.iryo.shikkan', 70000, 'ICD-11 disease "
         "codes', 'healthcare')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('icd10', 'icd10.gftd.ai', 'ai.gftd.apps.icd10.disease', 90168, 'ICD-10-CM "
         "disease codes', 'healthcare')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('food', 'food', 'ai.gftd.apps.food.food', 400000, 'food products', 'food')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('tunnel', 'douro', 'ai.gftd.apps.douro.tunnel', 100000, 'road & rail "
         "tunnels', 'transport')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('kyouryou', 'douro', 'ai.gftd.apps.douro.bridge', 10000000, 'bridges "
         "(global)', 'transport')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('gov', 'gov', 'ai.gftd.apps.gov.entity', 500000, 'government agencies', "
         "'governance')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('gov', 'gov', 'ai.gftd.apps.gov.agency', 500000, 'government agencies', "
         "'governance')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('gov', 'gov', 'ai.gftd.apps.gov.ministry', 500000, 'government agencies', "
         "'governance')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('sanctions', 'sanctions', 'ai.gftd.apps.sanctions.entity', 50000, "
         "'sanctioned entities', 'governance')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('treaty', 'treaty', 'ai.gftd.apps.treaty.treaty', 560, 'multilateral "
         "treaties', 'governance')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('communities', 'communities', 'ai.gftd.apps.communities.ngo', 10000, 'intl "
         "organizations', 'governance')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('communities', 'communities', 'ai.gftd.apps.communities.organization', "
         "10000, 'intl organizations', 'governance')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('senkyo', 'senkyo', 'ai.gftd.apps.senkyo.election', 1000, 'elections/yr', "
         "'governance')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('ethics', 'ethics', 'ai.gftd.apps.ethics.code', 12000, 'professional ethics "
         "codes', 'governance')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('customary', 'customary', 'ai.gftd.apps.customary.system', 1500, 'customary "
         "law systems', 'governance')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('tradition', 'tradition', 'ai.gftd.apps.tradition.tradition', 50000, "
         "'cultural traditions', 'culture')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('tradition', 'tradition', 'ai.gftd.apps.tradition.custom', 50000, 'cultural "
         "traditions', 'culture')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('railway', 'railway', 'ai.gftd.apps.railway.station', 1370000, 'railway "
         "stations (global)', 'transport')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('railway_route', 'railway', 'ai.gftd.apps.railway.line', 500000, 'railway "
         "routes/lines', 'transport')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('recycle_shisetsu', 'recycle', 'ai.gftd.apps.recycle.shisetsu', 500000, "
         "'recycling facilities', 'waste')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('recycle_shisetsu', 'recycle', 'ai.gftd.apps.recycle.recyclingFacility', "
         "500000, 'recycling facilities', 'waste')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('umetatchi', 'haikibutsu', 'ai.gftd.apps.haikibutsu.site', 500000, 'landfill "
         "sites', 'waste')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('pharma', 'pharma', 'ai.gftd.apps.pharma.pharma', 350000, 'pharmaceutical "
         "products', 'pharma')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('fda_ndc', 'fda', 'ai.gftd.apps.fda.ndc', 131664, 'FDA drug products', "
         "'pharma')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('ndc', 'ndc', 'ai.gftd.apps.ndc.drug', 350000, 'NDC drug codes', 'pharma')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('water', 'water', 'ai.gftd.apps.water.water', 300000, 'water utilities', "
         "'energy')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('denki', 'denki', 'ai.gftd.apps.denki.denki', 60000, 'power plants', "
         "'energy')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('gas', 'gas', 'ai.gftd.apps.gas.gas', 25000, 'gas facilities', 'energy')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('kasen', 'shizen', 'ai.gftd.apps.shizen.river', 250000, 'rivers & water "
         "bodies', 'environment')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('kasen', 'shizen', 'ai.gftd.apps.shizen.lake', 250000, 'rivers & water "
         "bodies', 'environment')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('kasen', 'shizen', 'ai.gftd.apps.shizen.canal', 250000, 'rivers & water "
         "bodies', 'environment')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('kasen', 'shizen', 'ai.gftd.apps.shizen.stream', 250000, 'rivers & water "
         "bodies', 'environment')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('kasen', 'shizen', 'ai.gftd.apps.shizen.spring', 250000, 'rivers & water "
         "bodies', 'environment')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('hogoku', 'shizen', 'ai.gftd.apps.shizen.protectedArea', 250000, 'protected "
         "areas', 'environment')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('kishou', 'shizen', 'ai.gftd.apps.shizen.weatherStation', 100000, 'weather "
         "stations', 'environment')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('seitaikei', 'shizen', 'ai.gftd.apps.shizen.ecoregion', 800, 'ecoregions', "
         "'environment')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('mine', 'mine', 'ai.gftd.apps.mine.mine', 35000, 'active mines', "
         "'manufacturing')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('mine', 'mine', 'ai.gftd.apps.mine.site', 35000, 'active mines', "
         "'manufacturing')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('handotai', 'handotai', 'ai.gftd.apps.handotai.device', 100000, "
         "'semiconductor products', 'manufacturing')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('kuruma', 'kuruma', 'ai.gftd.apps.kuruma.model', 80000, 'car models', "
         "'transport')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('kuruma', 'kuruma', 'ai.gftd.apps.kuruma.vehicle', 80000, 'car models', "
         "'transport')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('car_dealer', 'kuruma', 'ai.gftd.apps.carDealer.carDealer', 500000, 'car "
         "dealerships', 'transport')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('car_maker', 'kuruma', 'ai.gftd.apps.car_maker.maker', 5000, 'automotive "
         "OEMs', 'transport')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('ev_charger', 'ev', 'ai.gftd.apps.ev.evCharger', 5000000, 'EV charging "
         "stations', 'transport')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('gas_station', 'gas-station', 'ai.gftd.apps.gasStation.gasStation', 500000, "
         "'gas/fuel stations', 'transport')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('aircraft', 'aircraft', 'ai.gftd.apps.aircraft.aircraft', 450000, "
         "'registered aircraft', 'transport')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('vessel', 'vessel', 'ai.gftd.apps.vessel.ship', 105000, 'merchant vessels', "
         "'transport')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('locode', 'locode.gftd.ai', 'ai.gftd.apps.locode.location', 116067, 'UN "
         "LOCODE locations', 'transport')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('locode', 'unece', 'ai.gftd.apps.locode.location', 116067, 'UN LOCODE "
         "locations', 'transport')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('locode', 'port', 'ai.gftd.apps.port.port', 116067, 'UN LOCODE locations', "
         "'transport')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('satellite', 'satellite', 'ai.gftd.apps.satellite.satellite', 10000, 'active "
         "satellites', 'space')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('uchu_debris', 'uchu', 'ai.gftd.apps.uchu.debris', 30000, 'orbital debris', "
         "'space')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('uchu_mission', 'uchu', 'ai.gftd.apps.uchu.satellite', 200, 'space "
         "launches/yr', 'space')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('telecom', 'telecom', 'ai.gftd.apps.telecom.cable', 4000, 'telecom "
         "operators', 'telecom')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('telecom', 'telecom', 'ai.gftd.apps.telecom.company', 4000, 'telecom "
         "operators', 'telecom')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('bank', 'bank', 'ai.gftd.apps.bank.bank', 25000, 'banks (global)', "
         "'finance')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('insurance', 'insurance', 'ai.gftd.apps.insurance.insurance', 12000, "
         "'insurance companies', 'finance')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('securities', 'securities', 'ai.gftd.apps.securities.exchange', 3000, 'stock "
         "exchanges', 'finance')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('toshokan', 'toshokan', 'ai.gftd.apps.toshokan.toshokan', 400000, "
         "'libraries', 'culture')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('hakubutsukan', 'hakubutsukan', 'ai.gftd.apps.hakubutsukan.hakubutsukan', "
         "100000, 'museums', 'culture')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('hakubutsukan', 'hakubutsukan', 'ai.gftd.apps.hakubutsukan.museum', 100000, "
         "'museums', 'culture')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('festival_global', 'festival', 'ai.gftd.apps.festival.festival', 5000000, "
         "'festivals (global)', 'culture')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('sports_club', 'sports', 'ai.gftd.apps.sports.sportsClub', 5000000, 'sports "
         "clubs', 'culture')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('sports_shiai', 'sports', 'ai.gftd.apps.sports.match', 10000000, 'sports "
         "matches/yr', 'culture')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('dojo', 'dojo', 'ai.gftd.apps.dojo.dojo', 10000, 'readiness kata drills', "
         "'culture')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('casino', 'casino', 'ai.gftd.apps.casino.casino', 6500, 'casinos (global)', "
         "'culture')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('pachinko', 'pachinko', 'ai.gftd.apps.pachinko.hall', 7500, 'pachinko stores "
         "(JP)', 'culture')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('saigai', 'saigai', 'ai.gftd.apps.saigai.disaster', 1000, 'natural "
         "disasters/yr', 'governance')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('data_center', 'dc', 'ai.gftd.apps.dc.dc', 10000, 'data centers', "
         "'software')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('industry_standard', 'industry-standard', "
         "'ai.gftd.apps.industry_standard.standard', 45000, 'industry standards', 'governance')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('suido', 'suido', 'ai.gftd.apps.suido.utility', 1400, 'water utilities "
         "(JP)', 'energy')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('blockchain', 'blockchain', 'ai.gftd.apps.blockchain.chain', 1000, 'active "
         "chains', 'blockchain')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('chizai', 'chizai', 'ai.gftd.apps.chizai.chosakuken', 200000000, 'creative "
         "works/yr', 'ip')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('chizai', 'chizai', 'ai.gftd.apps.chizai.shohyo', 200000000, 'creative "
         "works/yr', 'ip')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('patent', 'patent', 'ai.gftd.apps.patent.patent', 100000000, 'patent "
         "filings/yr', 'ip')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('legal_entity', 'legal-entity', 'ai.gftd.apps.legalEntity.legalEntity', "
         "400000000, 'legal entities worldwide', 'economy')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('talent_cohort_stat', 'talent', 'ai.gftd.apps.talent.talentCohort', "
         "600000000, 'talent cohort statistics', 'talent')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('skill_taxonomy', 'talent', 'ai.gftd.apps.recruit.skillTaxonomy', 50000, "
         "'skill taxonomy codes', 'talent')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('occupation_code', 'talent', 'ai.gftd.apps.recruit.occupationTaxonomy', "
         "5172, 'occupation codes', 'talent')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('job_posting', 'talent', 'ai.gftd.apps.recruit.jobPosting', 300000000, 'job "
         "postings', 'talent')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('occupation_code', 'shigotoba', 'ai.gftd.apps.shigotoba.occupation', 5172, "
         "'occupation codes', 'talent')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('accommodation', 'hospitality', 'ai.gftd.apps.hospitality.accommodation', "
         "700000, 'accommodation listings', 'tourism')",
  'parameters': []},
 {'sql': 'INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, '
         'unit, sector)\n'
         "    VALUES ('sovereign', 'states', 'govOrg', 195, 'sovereign states', 'governance')",
  'parameters': []}]

DOWN = [{'sql': "DELETE FROM dim_world_domain_collection WHERE collection = 'ai.gftd.apps.bus.busStop'",
  'parameters': []},
 {'sql': 'DELETE FROM dim_world_domain_collection WHERE collection = '
         "'ai.gftd.apps.religious.place'",
  'parameters': []},
 {'sql': 'DELETE FROM dim_world_domain_collection WHERE collection = '
         "'ai.gftd.apps.religious.order'",
  'parameters': []},
 {'sql': 'DELETE FROM dim_world_domain_collection WHERE collection = '
         "'ai.gftd.apps.religious.system'",
  'parameters': []},
 {'sql': 'DELETE FROM dim_world_domain_collection WHERE collection = '
         "'ai.gftd.apps.religious.denomination'",
  'parameters': []},
 {'sql': 'DELETE FROM dim_world_domain_collection WHERE collection = '
         "'ai.gftd.apps.tentai.asteroid'",
  'parameters': []},
 {'sql': "DELETE FROM dim_world_domain_collection WHERE collection = 'ai.gftd.apps.tentai.galaxy'",
  'parameters': []},
 {'sql': 'DELETE FROM dim_world_domain_collection WHERE collection = '
         "'ai.gftd.apps.tentai.exoplanet'",
  'parameters': []},
 {'sql': "DELETE FROM dim_world_domain_collection WHERE collection = 'ai.gftd.apps.tentai.comet'",
  'parameters': []},
 {'sql': "DELETE FROM dim_world_domain_collection WHERE collection = 'ai.gftd.apps.tentai.star'",
  'parameters': []},
 {'sql': 'DELETE FROM dim_world_domain_collection WHERE collection = '
         "'ai.gftd.apps.media_gamers.title'",
  'parameters': []},
 {'sql': 'DELETE FROM dim_world_domain_collection WHERE collection = '
         "'ai.gftd.apps.media_anime.title'",
  'parameters': []},
 {'sql': "DELETE FROM dim_world_domain_collection WHERE collection = 'ai.gftd.apps.manga.title'",
  'parameters': []},
 {'sql': "DELETE FROM dim_world_domain_collection WHERE collection = 'ai.gftd.apps.drama.title'",
  'parameters': []},
 {'sql': "DELETE FROM dim_world_domain_collection WHERE collection = 'ai.gftd.apps.drama.show'",
  'parameters': []},
 {'sql': 'DELETE FROM dim_world_domain_collection WHERE collection = '
         "'ai.gftd.apps.character.anime'",
  'parameters': []},
 {'sql': 'DELETE FROM dim_world_domain_collection WHERE collection = '
         "'ai.gftd.apps.character.manga'",
  'parameters': []},
 {'sql': "DELETE FROM dim_world_domain_collection WHERE collection = 'ai.gftd.apps.character.tv'",
  'parameters': []},
 {'sql': "DELETE FROM dim_world_domain_collection WHERE collection = 'ai.gftd.apps.character.game'",
  'parameters': []},
 {'sql': "DELETE FROM dim_world_domain_collection WHERE collection = 'ai.gftd.apps.character.book'",
  'parameters': []},
 {'sql': 'DELETE FROM dim_world_domain_collection WHERE collection = '
         "'ai.gftd.apps.character.animated'",
  'parameters': []},
 {'sql': 'DELETE FROM dim_world_domain_collection WHERE collection = '
         "'ai.gftd.apps.character.mythology'",
  'parameters': []},
 {'sql': 'DELETE FROM dim_world_domain_collection WHERE collection = '
         "'ai.gftd.apps.character.comic'",
  'parameters': []},
 {'sql': "DELETE FROM dim_world_domain_collection WHERE collection = 'ai.gftd.apps.gakko.gakko'",
  'parameters': []},
 {'sql': "DELETE FROM dim_world_domain_collection WHERE collection = 'ai.gftd.apps.iryo.rinshou'",
  'parameters': []},
 {'sql': "DELETE FROM dim_world_domain_collection WHERE collection = 'ai.gftd.apps.iryo.shisetsu'",
  'parameters': []},
 {'sql': "DELETE FROM dim_world_domain_collection WHERE collection = 'ai.gftd.apps.iryo.shikkan'",
  'parameters': []},
 {'sql': "DELETE FROM dim_world_domain_collection WHERE collection = 'ai.gftd.apps.icd10.disease'",
  'parameters': []},
 {'sql': "DELETE FROM dim_world_domain_collection WHERE collection = 'ai.gftd.apps.food.food'",
  'parameters': []},
 {'sql': "DELETE FROM dim_world_domain_collection WHERE collection = 'ai.gftd.apps.douro.tunnel'",
  'parameters': []},
 {'sql': "DELETE FROM dim_world_domain_collection WHERE collection = 'ai.gftd.apps.douro.bridge'",
  'parameters': []},
 {'sql': "DELETE FROM dim_world_domain_collection WHERE collection = 'ai.gftd.apps.gov.entity'",
  'parameters': []},
 {'sql': "DELETE FROM dim_world_domain_collection WHERE collection = 'ai.gftd.apps.gov.agency'",
  'parameters': []},
 {'sql': "DELETE FROM dim_world_domain_collection WHERE collection = 'ai.gftd.apps.gov.ministry'",
  'parameters': []},
 {'sql': 'DELETE FROM dim_world_domain_collection WHERE collection = '
         "'ai.gftd.apps.sanctions.entity'",
  'parameters': []},
 {'sql': "DELETE FROM dim_world_domain_collection WHERE collection = 'ai.gftd.apps.treaty.treaty'",
  'parameters': []},
 {'sql': 'DELETE FROM dim_world_domain_collection WHERE collection = '
         "'ai.gftd.apps.communities.ngo'",
  'parameters': []},
 {'sql': 'DELETE FROM dim_world_domain_collection WHERE collection = '
         "'ai.gftd.apps.communities.organization'",
  'parameters': []},
 {'sql': 'DELETE FROM dim_world_domain_collection WHERE collection = '
         "'ai.gftd.apps.senkyo.election'",
  'parameters': []},
 {'sql': "DELETE FROM dim_world_domain_collection WHERE collection = 'ai.gftd.apps.ethics.code'",
  'parameters': []},
 {'sql': 'DELETE FROM dim_world_domain_collection WHERE collection = '
         "'ai.gftd.apps.customary.system'",
  'parameters': []},
 {'sql': 'DELETE FROM dim_world_domain_collection WHERE collection = '
         "'ai.gftd.apps.tradition.tradition'",
  'parameters': []},
 {'sql': 'DELETE FROM dim_world_domain_collection WHERE collection = '
         "'ai.gftd.apps.tradition.custom'",
  'parameters': []},
 {'sql': 'DELETE FROM dim_world_domain_collection WHERE collection = '
         "'ai.gftd.apps.railway.station'",
  'parameters': []},
 {'sql': "DELETE FROM dim_world_domain_collection WHERE collection = 'ai.gftd.apps.railway.line'",
  'parameters': []},
 {'sql': 'DELETE FROM dim_world_domain_collection WHERE collection = '
         "'ai.gftd.apps.recycle.shisetsu'",
  'parameters': []},
 {'sql': 'DELETE FROM dim_world_domain_collection WHERE collection = '
         "'ai.gftd.apps.recycle.recyclingFacility'",
  'parameters': []},
 {'sql': 'DELETE FROM dim_world_domain_collection WHERE collection = '
         "'ai.gftd.apps.haikibutsu.site'",
  'parameters': []},
 {'sql': "DELETE FROM dim_world_domain_collection WHERE collection = 'ai.gftd.apps.pharma.pharma'",
  'parameters': []},
 {'sql': "DELETE FROM dim_world_domain_collection WHERE collection = 'ai.gftd.apps.fda.ndc'",
  'parameters': []},
 {'sql': "DELETE FROM dim_world_domain_collection WHERE collection = 'ai.gftd.apps.ndc.drug'",
  'parameters': []},
 {'sql': "DELETE FROM dim_world_domain_collection WHERE collection = 'ai.gftd.apps.water.water'",
  'parameters': []},
 {'sql': "DELETE FROM dim_world_domain_collection WHERE collection = 'ai.gftd.apps.denki.denki'",
  'parameters': []},
 {'sql': "DELETE FROM dim_world_domain_collection WHERE collection = 'ai.gftd.apps.gas.gas'",
  'parameters': []},
 {'sql': "DELETE FROM dim_world_domain_collection WHERE collection = 'ai.gftd.apps.shizen.river'",
  'parameters': []},
 {'sql': "DELETE FROM dim_world_domain_collection WHERE collection = 'ai.gftd.apps.shizen.lake'",
  'parameters': []},
 {'sql': "DELETE FROM dim_world_domain_collection WHERE collection = 'ai.gftd.apps.shizen.canal'",
  'parameters': []},
 {'sql': "DELETE FROM dim_world_domain_collection WHERE collection = 'ai.gftd.apps.shizen.stream'",
  'parameters': []},
 {'sql': "DELETE FROM dim_world_domain_collection WHERE collection = 'ai.gftd.apps.shizen.spring'",
  'parameters': []},
 {'sql': 'DELETE FROM dim_world_domain_collection WHERE collection = '
         "'ai.gftd.apps.shizen.protectedArea'",
  'parameters': []},
 {'sql': 'DELETE FROM dim_world_domain_collection WHERE collection = '
         "'ai.gftd.apps.shizen.weatherStation'",
  'parameters': []},
 {'sql': 'DELETE FROM dim_world_domain_collection WHERE collection = '
         "'ai.gftd.apps.shizen.ecoregion'",
  'parameters': []},
 {'sql': "DELETE FROM dim_world_domain_collection WHERE collection = 'ai.gftd.apps.mine.mine'",
  'parameters': []},
 {'sql': "DELETE FROM dim_world_domain_collection WHERE collection = 'ai.gftd.apps.mine.site'",
  'parameters': []},
 {'sql': 'DELETE FROM dim_world_domain_collection WHERE collection = '
         "'ai.gftd.apps.handotai.device'",
  'parameters': []},
 {'sql': "DELETE FROM dim_world_domain_collection WHERE collection = 'ai.gftd.apps.kuruma.model'",
  'parameters': []},
 {'sql': "DELETE FROM dim_world_domain_collection WHERE collection = 'ai.gftd.apps.kuruma.vehicle'",
  'parameters': []},
 {'sql': 'DELETE FROM dim_world_domain_collection WHERE collection = '
         "'ai.gftd.apps.carDealer.carDealer'",
  'parameters': []},
 {'sql': 'DELETE FROM dim_world_domain_collection WHERE collection = '
         "'ai.gftd.apps.car_maker.maker'",
  'parameters': []},
 {'sql': "DELETE FROM dim_world_domain_collection WHERE collection = 'ai.gftd.apps.ev.evCharger'",
  'parameters': []},
 {'sql': 'DELETE FROM dim_world_domain_collection WHERE collection = '
         "'ai.gftd.apps.gasStation.gasStation'",
  'parameters': []},
 {'sql': 'DELETE FROM dim_world_domain_collection WHERE collection = '
         "'ai.gftd.apps.aircraft.aircraft'",
  'parameters': []},
 {'sql': "DELETE FROM dim_world_domain_collection WHERE collection = 'ai.gftd.apps.vessel.ship'",
  'parameters': []},
 {'sql': 'DELETE FROM dim_world_domain_collection WHERE collection = '
         "'ai.gftd.apps.locode.location'",
  'parameters': []},
 {'sql': "DELETE FROM dim_world_domain_collection WHERE collection = 'ai.gftd.apps.port.port'",
  'parameters': []},
 {'sql': 'DELETE FROM dim_world_domain_collection WHERE collection = '
         "'ai.gftd.apps.satellite.satellite'",
  'parameters': []},
 {'sql': "DELETE FROM dim_world_domain_collection WHERE collection = 'ai.gftd.apps.uchu.debris'",
  'parameters': []},
 {'sql': "DELETE FROM dim_world_domain_collection WHERE collection = 'ai.gftd.apps.uchu.satellite'",
  'parameters': []},
 {'sql': "DELETE FROM dim_world_domain_collection WHERE collection = 'ai.gftd.apps.telecom.cable'",
  'parameters': []},
 {'sql': 'DELETE FROM dim_world_domain_collection WHERE collection = '
         "'ai.gftd.apps.telecom.company'",
  'parameters': []},
 {'sql': "DELETE FROM dim_world_domain_collection WHERE collection = 'ai.gftd.apps.bank.bank'",
  'parameters': []},
 {'sql': 'DELETE FROM dim_world_domain_collection WHERE collection = '
         "'ai.gftd.apps.insurance.insurance'",
  'parameters': []},
 {'sql': 'DELETE FROM dim_world_domain_collection WHERE collection = '
         "'ai.gftd.apps.securities.exchange'",
  'parameters': []},
 {'sql': 'DELETE FROM dim_world_domain_collection WHERE collection = '
         "'ai.gftd.apps.toshokan.toshokan'",
  'parameters': []},
 {'sql': 'DELETE FROM dim_world_domain_collection WHERE collection = '
         "'ai.gftd.apps.hakubutsukan.hakubutsukan'",
  'parameters': []},
 {'sql': 'DELETE FROM dim_world_domain_collection WHERE collection = '
         "'ai.gftd.apps.hakubutsukan.museum'",
  'parameters': []},
 {'sql': 'DELETE FROM dim_world_domain_collection WHERE collection = '
         "'ai.gftd.apps.festival.festival'",
  'parameters': []},
 {'sql': 'DELETE FROM dim_world_domain_collection WHERE collection = '
         "'ai.gftd.apps.sports.sportsClub'",
  'parameters': []},
 {'sql': "DELETE FROM dim_world_domain_collection WHERE collection = 'ai.gftd.apps.sports.match'",
  'parameters': []},
 {'sql': "DELETE FROM dim_world_domain_collection WHERE collection = 'ai.gftd.apps.dojo.dojo'",
  'parameters': []},
 {'sql': "DELETE FROM dim_world_domain_collection WHERE collection = 'ai.gftd.apps.casino.casino'",
  'parameters': []},
 {'sql': "DELETE FROM dim_world_domain_collection WHERE collection = 'ai.gftd.apps.pachinko.hall'",
  'parameters': []},
 {'sql': 'DELETE FROM dim_world_domain_collection WHERE collection = '
         "'ai.gftd.apps.saigai.disaster'",
  'parameters': []},
 {'sql': "DELETE FROM dim_world_domain_collection WHERE collection = 'ai.gftd.apps.dc.dc'",
  'parameters': []},
 {'sql': 'DELETE FROM dim_world_domain_collection WHERE collection = '
         "'ai.gftd.apps.industry_standard.standard'",
  'parameters': []},
 {'sql': "DELETE FROM dim_world_domain_collection WHERE collection = 'ai.gftd.apps.suido.utility'",
  'parameters': []},
 {'sql': 'DELETE FROM dim_world_domain_collection WHERE collection = '
         "'ai.gftd.apps.blockchain.chain'",
  'parameters': []},
 {'sql': 'DELETE FROM dim_world_domain_collection WHERE collection = '
         "'ai.gftd.apps.chizai.chosakuken'",
  'parameters': []},
 {'sql': "DELETE FROM dim_world_domain_collection WHERE collection = 'ai.gftd.apps.chizai.shohyo'",
  'parameters': []},
 {'sql': "DELETE FROM dim_world_domain_collection WHERE collection = 'ai.gftd.apps.patent.patent'",
  'parameters': []},
 {'sql': 'DELETE FROM dim_world_domain_collection WHERE collection = '
         "'ai.gftd.apps.legalEntity.legalEntity'",
  'parameters': []},
 {'sql': 'DELETE FROM dim_world_domain_collection WHERE collection = '
         "'ai.gftd.apps.talent.talentCohort'",
  'parameters': []},
 {'sql': 'DELETE FROM dim_world_domain_collection WHERE collection = '
         "'ai.gftd.apps.recruit.skillTaxonomy'",
  'parameters': []},
 {'sql': 'DELETE FROM dim_world_domain_collection WHERE collection = '
         "'ai.gftd.apps.recruit.occupationTaxonomy'",
  'parameters': []},
 {'sql': 'DELETE FROM dim_world_domain_collection WHERE collection = '
         "'ai.gftd.apps.recruit.jobPosting'",
  'parameters': []},
 {'sql': 'DELETE FROM dim_world_domain_collection WHERE collection = '
         "'ai.gftd.apps.shigotoba.occupation'",
  'parameters': []},
 {'sql': 'DELETE FROM dim_world_domain_collection WHERE collection = '
         "'ai.gftd.apps.hospitality.accommodation'",
  'parameters': []},
 {'sql': "DELETE FROM dim_world_domain_collection WHERE collection = 'govOrg'", 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
