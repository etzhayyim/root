import { Kysely, sql } from 'kysely';

/**
 * Migration 20260416220000: Collection-domain coverage mappings
 *
 * Problem: dim_world_domain_collection has 433 entries but only 75 map to
 * actual data collections — the other 358 are placeholder bootstrap mappings.
 * mv_world_collection_coverage_live shows meaningless 0.002% coverage for most
 * domains because it sees bootstrap (1 record) instead of real data.
 *
 * Fix: Insert collection-domain mappings for the 80+ top collections that have
 * significant real data in mv_world_record_per_host_collection but are not yet
 * mapped in dim_world_domain_collection.
 *
 * Coverage improvements (representative sample):
 * | domain           | collection               | records | world_total | new_rate |
 * |------------------|--------------------------|---------|-------------|----------|
 * | bus_stop         | bus.busStop              | 1,488K  | 5,000K      | 29.8%    |
 * | shukyo_shisetsu  | religious.place          | 1,242K  | 5,000K      | 24.8%    |
 * | tentai_asteroid  | tentai.asteroid          | 1,098K  | 1,300K      | 84.5%    |
 * | media_gamers     | media_gamers.title       |   900K  |   900K      | 100.0%   |
 * | gakko            | gakko.gakko              |   695K  | 1,000K      | 69.5%    |
 * | rinshou_shiken   | iryo.rinshou             |   567K  |   500K      | 113.4%   |
 * | food             | food.food                |   564K  |   400K      | 141.0%   |
 * | iryo_shisetsu    | iryo.shisetsu            |   553K  | 1,000K      | 55.3%    |
 * | tunnel           | douro.tunnel             |   500K  |   100K      | 499.7%   |
 * | gov              | gov.entity               |   494K  |   500K      | 98.9%    |
 * | railway          | railway.station          |   467K  | 1,370K      | 34.1%    |
 * | recycle_shisetsu | recycle.shisetsu         |   436K  |   500K      | 87.2%    |
 * | character_anime  | character.anime          |   428K  |   500K      | 85.6%    |
 * | sports_club      | sports.sportsClub        |   416K  | 5,000K      | 8.3%     |
 * | umetatchi        | haikibutsu.site          |   391K  |   500K      | 78.2%    |
 * | pharma           | pharma.pharma            |   369K  |   350K      | 105.4%   |
 * | water            | water.water              |   306K  |   300K      | 102.0%   |
 * | handotai         | handotai.device          |   301K  |   100K      | 301.0%   |
 * | gas_station      | gasStation.gasStation    |   286K  |   500K      | 57.2%    |
 * | kuruma           | kuruma.model             |   205K  |    80K      | 256.5%   |
 * | manga            | manga.title              |   152K  |   150K      | 101.6%   |
 * | ev_charger       | ev.evCharger             |   151K  | 5,000K      | 3.0%     |
 * | toshokan         | toshokan.toshokan        |   142K  |   400K      | 35.6%    |
 * | fda_ndc          | fda.ndc                  |   132K  |   131K      | 100.7%   |
 * | ndc              | ndc.drug                 |   128K  |   350K      | 36.6%    |
 * | locode           | locode.location          |   116K  |   116K      | 100.0%   |
 * | vessel           | vessel.ship              |   115K  |   105K      | 109.5%   |
 * | kasen            | shizen.river             |   112K  |   250K      | 44.9%    |
 * | denki            | denki.denki              |   100K  |    60K      | 166.0%   |
 * | aircraft         | aircraft.aircraft        |    91K  |   450K      | 20.3%    |
 * | icd10            | icd10.disease            |    90K  |    90K      | 100.0%   |
 * | hakubutsukan     | hakubutsukan.hakubutsukan|    88K  |   100K      | 88.0%    |
 * | drama            | drama.title + drama.show |    79K  |   100K      | 79.0%    |
 * | sanctions        | sanctions.entity         |    71K  |    50K      | 141.4%   |
 *
 * Apply: out-of-band via psql (kysely migrator blocked by ghost 20260415140000).
 * After apply: INSERT INTO kysely_migration ...
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  // Transport: Bus
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('bus_stop', 'bus', 'ai.gftd.apps.bus.busStop', 5000000, 'bus stops (global)', 'transport')`.execute(db);

  // Culture/Religion
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('shukyo_shisetsu', 'religious', 'ai.gftd.apps.religious.place', 5000000, 'religious institutions', 'culture')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('religious', 'religious', 'ai.gftd.apps.religious.order', 4300, 'religious legal systems', 'governance')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('religious', 'religious', 'ai.gftd.apps.religious.system', 4300, 'religious legal systems', 'governance')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('shukyo_shisetsu', 'religious', 'ai.gftd.apps.religious.denomination', 5000000, 'religious institutions', 'culture')`.execute(db);

  // Space/Astronomy: Tentai
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('tentai_asteroid', 'tentai', 'ai.gftd.apps.tentai.asteroid', 1300000, 'asteroids', 'space')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('tentai_galaxy', 'tentai', 'ai.gftd.apps.tentai.galaxy', 2000000, 'galaxies', 'space')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('tentai_exoplanet', 'tentai', 'ai.gftd.apps.tentai.exoplanet', 5700, 'exoplanets', 'space')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('tentai_comet', 'tentai', 'ai.gftd.apps.tentai.comet', 4000, 'comets', 'space')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('tentai_star', 'tentai', 'ai.gftd.apps.tentai.star', 1800000000, 'catalogued stars', 'space')`.execute(db);

  // Content: Games, Anime, Manga, Drama
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('media_gamers', 'media-gamers', 'ai.gftd.apps.media_gamers.title', 900000, 'game titles', 'content')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('media_anime', 'media-anime', 'ai.gftd.apps.media_anime.title', 25000, 'anime titles', 'content')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('manga', 'manga', 'ai.gftd.apps.manga.title', 150000, 'manga titles', 'content')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('drama', 'drama', 'ai.gftd.apps.drama.title', 100000, 'TV drama titles', 'content')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('drama', 'drama', 'ai.gftd.apps.drama.show', 100000, 'TV drama titles', 'content')`.execute(db);

  // Fiction: Characters
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('character_anime', 'character', 'ai.gftd.apps.character.anime', 500000, 'anime characters', 'fiction')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('character_manga', 'character', 'ai.gftd.apps.character.manga', 2000000, 'manga characters', 'fiction')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('character_tv', 'character', 'ai.gftd.apps.character.tv', 3000000, 'TV characters', 'fiction')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('character_game', 'character', 'ai.gftd.apps.character.game', 9000000, 'game characters', 'fiction')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('character_book', 'character', 'ai.gftd.apps.character.book', 500000000, 'book characters', 'fiction')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('character', 'character', 'ai.gftd.apps.character.animated', 500000000, 'fictional characters', 'fiction')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('character', 'character', 'ai.gftd.apps.character.mythology', 500000000, 'fictional characters', 'fiction')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('character', 'character', 'ai.gftd.apps.character.comic', 500000000, 'fictional characters', 'fiction')`.execute(db);

  // Education
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('gakko', 'gakko', 'ai.gftd.apps.gakko.gakko', 1000000, 'schools & universities', 'education')`.execute(db);

  // Healthcare
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('rinshou_shiken', 'iryo', 'ai.gftd.apps.iryo.rinshou', 500000, 'clinical trials', 'healthcare')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('iryo_shisetsu', 'iryo', 'ai.gftd.apps.iryo.shisetsu', 1000000, 'hospitals & clinics', 'healthcare')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('icd_shikkan', 'iryo', 'ai.gftd.apps.iryo.shikkan', 70000, 'ICD-11 disease codes', 'healthcare')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('icd10', 'icd10.etzhayyim.com', 'ai.gftd.apps.icd10.disease', 90168, 'ICD-10-CM disease codes', 'healthcare')`.execute(db);

  // Food
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('food', 'food', 'ai.gftd.apps.food.food', 400000, 'food products', 'food')`.execute(db);

  // Transport: Roads and tunnels
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('tunnel', 'douro', 'ai.gftd.apps.douro.tunnel', 100000, 'road & rail tunnels', 'transport')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('kyouryou', 'douro', 'ai.gftd.apps.douro.bridge', 10000000, 'bridges (global)', 'transport')`.execute(db);

  // Governance
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('gov', 'gov', 'ai.gftd.apps.gov.entity', 500000, 'government agencies', 'governance')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('gov', 'gov', 'ai.gftd.apps.gov.agency', 500000, 'government agencies', 'governance')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('gov', 'gov', 'ai.gftd.apps.gov.ministry', 500000, 'government agencies', 'governance')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('sanctions', 'sanctions', 'ai.gftd.apps.sanctions.entity', 50000, 'sanctioned entities', 'governance')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('treaty', 'treaty', 'ai.gftd.apps.treaty.treaty', 560, 'multilateral treaties', 'governance')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('communities', 'communities', 'ai.gftd.apps.communities.ngo', 10000, 'intl organizations', 'governance')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('communities', 'communities', 'ai.gftd.apps.communities.organization', 10000, 'intl organizations', 'governance')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('senkyo', 'senkyo', 'ai.gftd.apps.senkyo.election', 1000, 'elections/yr', 'governance')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('ethics', 'ethics', 'ai.gftd.apps.ethics.code', 12000, 'professional ethics codes', 'governance')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('customary', 'customary', 'ai.gftd.apps.customary.system', 1500, 'customary law systems', 'governance')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('tradition', 'tradition', 'ai.gftd.apps.tradition.tradition', 50000, 'cultural traditions', 'culture')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('tradition', 'tradition', 'ai.gftd.apps.tradition.custom', 50000, 'cultural traditions', 'culture')`.execute(db);

  // Transport: Railway
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('railway', 'railway', 'ai.gftd.apps.railway.station', 1370000, 'railway stations (global)', 'transport')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('railway_route', 'railway', 'ai.gftd.apps.railway.line', 500000, 'railway routes/lines', 'transport')`.execute(db);

  // Waste
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('recycle_shisetsu', 'recycle', 'ai.gftd.apps.recycle.shisetsu', 500000, 'recycling facilities', 'waste')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('recycle_shisetsu', 'recycle', 'ai.gftd.apps.recycle.recyclingFacility', 500000, 'recycling facilities', 'waste')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('umetatchi', 'haikibutsu', 'ai.gftd.apps.haikibutsu.site', 500000, 'landfill sites', 'waste')`.execute(db);

  // Pharma / Healthcare drugs
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('pharma', 'pharma', 'ai.gftd.apps.pharma.pharma', 350000, 'pharmaceutical products', 'pharma')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('fda_ndc', 'fda', 'ai.gftd.apps.fda.ndc', 131664, 'FDA drug products', 'pharma')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('ndc', 'ndc', 'ai.gftd.apps.ndc.drug', 350000, 'NDC drug codes', 'pharma')`.execute(db);

  // Energy and environment
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('water', 'water', 'ai.gftd.apps.water.water', 300000, 'water utilities', 'energy')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('denki', 'denki', 'ai.gftd.apps.denki.denki', 60000, 'power plants', 'energy')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('gas', 'gas', 'ai.gftd.apps.gas.gas', 25000, 'gas facilities', 'energy')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('kasen', 'shizen', 'ai.gftd.apps.shizen.river', 250000, 'rivers & water bodies', 'environment')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('kasen', 'shizen', 'ai.gftd.apps.shizen.lake', 250000, 'rivers & water bodies', 'environment')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('kasen', 'shizen', 'ai.gftd.apps.shizen.canal', 250000, 'rivers & water bodies', 'environment')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('kasen', 'shizen', 'ai.gftd.apps.shizen.stream', 250000, 'rivers & water bodies', 'environment')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('kasen', 'shizen', 'ai.gftd.apps.shizen.spring', 250000, 'rivers & water bodies', 'environment')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('hogoku', 'shizen', 'ai.gftd.apps.shizen.protectedArea', 250000, 'protected areas', 'environment')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('kishou', 'shizen', 'ai.gftd.apps.shizen.weatherStation', 100000, 'weather stations', 'environment')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('seitaikei', 'shizen', 'ai.gftd.apps.shizen.ecoregion', 800, 'ecoregions', 'environment')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('mine', 'mine', 'ai.gftd.apps.mine.mine', 35000, 'active mines', 'manufacturing')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('mine', 'mine', 'ai.gftd.apps.mine.site', 35000, 'active mines', 'manufacturing')`.execute(db);

  // Manufacturing: Handotai, Kuruma
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('handotai', 'handotai', 'ai.gftd.apps.handotai.device', 100000, 'semiconductor products', 'manufacturing')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('kuruma', 'kuruma', 'ai.gftd.apps.kuruma.model', 80000, 'car models', 'transport')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('kuruma', 'kuruma', 'ai.gftd.apps.kuruma.vehicle', 80000, 'car models', 'transport')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('car_dealer', 'kuruma', 'ai.gftd.apps.carDealer.carDealer', 500000, 'car dealerships', 'transport')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('car_maker', 'kuruma', 'ai.gftd.apps.car_maker.maker', 5000, 'automotive OEMs', 'transport')`.execute(db);

  // Transport: EV, Gas stations, Aircraft, Vessels, LOCODE
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('ev_charger', 'ev', 'ai.gftd.apps.ev.evCharger', 5000000, 'EV charging stations', 'transport')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('gas_station', 'gas-station', 'ai.gftd.apps.gasStation.gasStation', 500000, 'gas/fuel stations', 'transport')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('aircraft', 'aircraft', 'ai.gftd.apps.aircraft.aircraft', 450000, 'registered aircraft', 'transport')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('vessel', 'vessel', 'ai.gftd.apps.vessel.ship', 105000, 'merchant vessels', 'transport')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('locode', 'locode.etzhayyim.com', 'ai.gftd.apps.locode.location', 116067, 'UN LOCODE locations', 'transport')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('locode', 'unece', 'ai.gftd.apps.locode.location', 116067, 'UN LOCODE locations', 'transport')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('locode', 'port', 'ai.gftd.apps.port.port', 116067, 'UN LOCODE locations', 'transport')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('satellite', 'satellite', 'ai.gftd.apps.satellite.satellite', 10000, 'active satellites', 'space')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('uchu_debris', 'uchu', 'ai.gftd.apps.uchu.debris', 30000, 'orbital debris', 'space')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('uchu_mission', 'uchu', 'ai.gftd.apps.uchu.satellite', 200, 'space launches/yr', 'space')`.execute(db);

  // Telecom
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('telecom', 'telecom', 'ai.gftd.apps.telecom.cable', 4000, 'telecom operators', 'telecom')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('telecom', 'telecom', 'ai.gftd.apps.telecom.company', 4000, 'telecom operators', 'telecom')`.execute(db);

  // Finance / Banking
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('bank', 'bank', 'ai.gftd.apps.bank.bank', 25000, 'banks (global)', 'finance')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('insurance', 'insurance', 'ai.gftd.apps.insurance.insurance', 12000, 'insurance companies', 'finance')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('securities', 'securities', 'ai.gftd.apps.securities.exchange', 3000, 'stock exchanges', 'finance')`.execute(db);

  // Culture
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('toshokan', 'toshokan', 'ai.gftd.apps.toshokan.toshokan', 400000, 'libraries', 'culture')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('hakubutsukan', 'hakubutsukan', 'ai.gftd.apps.hakubutsukan.hakubutsukan', 100000, 'museums', 'culture')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('hakubutsukan', 'hakubutsukan', 'ai.gftd.apps.hakubutsukan.museum', 100000, 'museums', 'culture')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('festival_global', 'festival', 'ai.gftd.apps.festival.festival', 5000000, 'festivals (global)', 'culture')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('sports_club', 'sports', 'ai.gftd.apps.sports.sportsClub', 5000000, 'sports clubs', 'culture')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('sports_shiai', 'sports', 'ai.gftd.apps.sports.match', 10000000, 'sports matches/yr', 'culture')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('dojo', 'dojo', 'ai.gftd.apps.dojo.dojo', 10000, 'readiness kata drills', 'culture')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('casino', 'casino', 'ai.gftd.apps.casino.casino', 6500, 'casinos (global)', 'culture')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('pachinko', 'pachinko', 'ai.gftd.apps.pachinko.hall', 7500, 'pachinko stores (JP)', 'culture')`.execute(db);

  // Disaster
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('saigai', 'saigai', 'ai.gftd.apps.saigai.disaster', 1000, 'natural disasters/yr', 'governance')`.execute(db);

  // Data center
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('data_center', 'dc', 'ai.gftd.apps.dc.dc', 10000, 'data centers', 'software')`.execute(db);

  // Industry standards
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('industry_standard', 'industry-standard', 'ai.gftd.apps.industry_standard.standard', 45000, 'industry standards', 'governance')`.execute(db);

  // Water utilities (JP)
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('suido', 'suido', 'ai.gftd.apps.suido.utility', 1400, 'water utilities (JP)', 'energy')`.execute(db);

  // Blockchain
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('blockchain', 'blockchain', 'ai.gftd.apps.blockchain.chain', 1000, 'active chains', 'blockchain')`.execute(db);

  // Intellectual Property: Copyright
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('chizai', 'chizai', 'ai.gftd.apps.chizai.chosakuken', 200000000, 'creative works/yr', 'ip')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('chizai', 'chizai', 'ai.gftd.apps.chizai.shohyo', 200000000, 'creative works/yr', 'ip')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('patent', 'patent', 'ai.gftd.apps.patent.patent', 100000000, 'patent filings/yr', 'ip')`.execute(db);

  // Legal entities
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('legal_entity', 'legal-entity', 'ai.gftd.apps.legalEntity.legalEntity', 400000000, 'legal entities worldwide', 'economy')`.execute(db);

  // Talent / Occupation
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('talent_cohort_stat', 'talent', 'ai.gftd.apps.talent.talentCohort', 600000000, 'talent cohort statistics', 'talent')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('skill_taxonomy', 'talent', 'ai.gftd.apps.recruit.skillTaxonomy', 50000, 'skill taxonomy codes', 'talent')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('occupation_code', 'talent', 'ai.gftd.apps.recruit.occupationTaxonomy', 5172, 'occupation codes', 'talent')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('job_posting', 'talent', 'ai.gftd.apps.recruit.jobPosting', 300000000, 'job postings', 'talent')`.execute(db);
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('occupation_code', 'shigotoba', 'ai.gftd.apps.shigotoba.occupation', 5172, 'occupation codes', 'talent')`.execute(db);

  // Hospitality
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('accommodation', 'hospitality', 'ai.gftd.apps.hospitality.accommodation', 700000, 'accommodation listings', 'tourism')`.execute(db);

  // Sovereign states and geopolitics
  await sql`INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('sovereign', 'states', 'govOrg', 195, 'sovereign states', 'governance')`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  // Remove all entries added in this migration
  const collections = [
    'ai.gftd.apps.bus.busStop',
    'ai.gftd.apps.religious.place',
    'ai.gftd.apps.religious.order',
    'ai.gftd.apps.religious.system',
    'ai.gftd.apps.religious.denomination',
    'ai.gftd.apps.tentai.asteroid',
    'ai.gftd.apps.tentai.galaxy',
    'ai.gftd.apps.tentai.exoplanet',
    'ai.gftd.apps.tentai.comet',
    'ai.gftd.apps.tentai.star',
    'ai.gftd.apps.media_gamers.title',
    'ai.gftd.apps.media_anime.title',
    'ai.gftd.apps.manga.title',
    'ai.gftd.apps.drama.title',
    'ai.gftd.apps.drama.show',
    'ai.gftd.apps.character.anime',
    'ai.gftd.apps.character.manga',
    'ai.gftd.apps.character.tv',
    'ai.gftd.apps.character.game',
    'ai.gftd.apps.character.book',
    'ai.gftd.apps.character.animated',
    'ai.gftd.apps.character.mythology',
    'ai.gftd.apps.character.comic',
    'ai.gftd.apps.gakko.gakko',
    'ai.gftd.apps.iryo.rinshou',
    'ai.gftd.apps.iryo.shisetsu',
    'ai.gftd.apps.iryo.shikkan',
    'ai.gftd.apps.icd10.disease',
    'ai.gftd.apps.food.food',
    'ai.gftd.apps.douro.tunnel',
    'ai.gftd.apps.douro.bridge',
    'ai.gftd.apps.gov.entity',
    'ai.gftd.apps.gov.agency',
    'ai.gftd.apps.gov.ministry',
    'ai.gftd.apps.sanctions.entity',
    'ai.gftd.apps.treaty.treaty',
    'ai.gftd.apps.communities.ngo',
    'ai.gftd.apps.communities.organization',
    'ai.gftd.apps.senkyo.election',
    'ai.gftd.apps.ethics.code',
    'ai.gftd.apps.customary.system',
    'ai.gftd.apps.tradition.tradition',
    'ai.gftd.apps.tradition.custom',
    'ai.gftd.apps.railway.station',
    'ai.gftd.apps.railway.line',
    'ai.gftd.apps.recycle.shisetsu',
    'ai.gftd.apps.recycle.recyclingFacility',
    'ai.gftd.apps.haikibutsu.site',
    'ai.gftd.apps.pharma.pharma',
    'ai.gftd.apps.fda.ndc',
    'ai.gftd.apps.ndc.drug',
    'ai.gftd.apps.water.water',
    'ai.gftd.apps.denki.denki',
    'ai.gftd.apps.gas.gas',
    'ai.gftd.apps.shizen.river',
    'ai.gftd.apps.shizen.lake',
    'ai.gftd.apps.shizen.canal',
    'ai.gftd.apps.shizen.stream',
    'ai.gftd.apps.shizen.spring',
    'ai.gftd.apps.shizen.protectedArea',
    'ai.gftd.apps.shizen.weatherStation',
    'ai.gftd.apps.shizen.ecoregion',
    'ai.gftd.apps.mine.mine',
    'ai.gftd.apps.mine.site',
    'ai.gftd.apps.handotai.device',
    'ai.gftd.apps.kuruma.model',
    'ai.gftd.apps.kuruma.vehicle',
    'ai.gftd.apps.carDealer.carDealer',
    'ai.gftd.apps.car_maker.maker',
    'ai.gftd.apps.ev.evCharger',
    'ai.gftd.apps.gasStation.gasStation',
    'ai.gftd.apps.aircraft.aircraft',
    'ai.gftd.apps.vessel.ship',
    'ai.gftd.apps.locode.location',
    'ai.gftd.apps.port.port',
    'ai.gftd.apps.satellite.satellite',
    'ai.gftd.apps.uchu.debris',
    'ai.gftd.apps.uchu.satellite',
    'ai.gftd.apps.telecom.cable',
    'ai.gftd.apps.telecom.company',
    'ai.gftd.apps.bank.bank',
    'ai.gftd.apps.insurance.insurance',
    'ai.gftd.apps.securities.exchange',
    'ai.gftd.apps.toshokan.toshokan',
    'ai.gftd.apps.hakubutsukan.hakubutsukan',
    'ai.gftd.apps.hakubutsukan.museum',
    'ai.gftd.apps.festival.festival',
    'ai.gftd.apps.sports.sportsClub',
    'ai.gftd.apps.sports.match',
    'ai.gftd.apps.dojo.dojo',
    'ai.gftd.apps.casino.casino',
    'ai.gftd.apps.pachinko.hall',
    'ai.gftd.apps.saigai.disaster',
    'ai.gftd.apps.dc.dc',
    'ai.gftd.apps.industry_standard.standard',
    'ai.gftd.apps.suido.utility',
    'ai.gftd.apps.blockchain.chain',
    'ai.gftd.apps.chizai.chosakuken',
    'ai.gftd.apps.chizai.shohyo',
    'ai.gftd.apps.patent.patent',
    'ai.gftd.apps.legalEntity.legalEntity',
    'ai.gftd.apps.talent.talentCohort',
    'ai.gftd.apps.recruit.skillTaxonomy',
    'ai.gftd.apps.recruit.occupationTaxonomy',
    'ai.gftd.apps.recruit.jobPosting',
    'ai.gftd.apps.shigotoba.occupation',
    'ai.gftd.apps.hospitality.accommodation',
    'govOrg',
  ];
  for (const collection of collections) {
    await sql`DELETE FROM dim_world_domain_collection WHERE collection = ${sql.lit(collection)}`.execute(db);
  }
}
