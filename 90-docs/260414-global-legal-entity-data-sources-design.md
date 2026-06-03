# Global Legal Entity Data Sources — 194+ Country Ingestion Architecture

**Date**: 2026-04-14
**Status**: Active
**Project**: `60-apps/etzhayyim-project-legal-entity/`
**Component**: `le9k4x2m` (GLEIF LEI collector, extended to multi-source)

## Summary

GLEIF LEI (3M active) を起点に、全世界 194+ カ国の法人登記データソースを AT Protocol commit pipeline 経由で `vertex_legal_entity` に統合する。3 Phase で段階的に拡張し、最終的に ~345M 法人 records を graph に蓄積。Entity resolution (LEI ↔ 各国登記番号 ↔ Wikidata QID) で cross-border 法人グラフを構築。

## Architecture

### 3-Tier Collector Strategy

| Tier | 取得方式 | 対象 | 優先度 |
|---|---|---|---|
| **T1: API-first** | REST/SOAP API (bulk CSV/JSON) | GLEIF, UK CH, JP NTA, FR SIRENE, DK CVR 等 | Phase 1 (即時) |
| **T2: Bulk download** | 定期 CSV/XML dump → B2 staging → parse → PDS write | SEC EDGAR, AU ABR, BR CNPJ, OpenCorporates bulk | Phase 2 |
| **T3: Web scrape / aggregator** | OpenCorporates API + 個別 scraping | 途上国、小国、オフショア | Phase 3 |

### Common Ingest Path

```
[Data Source API / CSV / Scraper]
  → le9k4x2m Worker (command handler per source)
    → normalize → { $type: "com.etzhayyim.legalEntity.legalEntity", ... }
      → sdk.pds.rpc("com.atproto.repo.applyWrites", { repo, writes })
        → PDS → sign → vertex_legal_entity (RisingWave)
        → firehose emit (com.atproto.sync.subscribeRepos)
```

### DID Hierarchy (Extended)

```
did:web:legal-entity.etzhayyim.com                              — controller
did:web:legal-entity.etzhayyim.com:lei:{LEI}                    — GLEIF LEI entity
did:web:legal-entity.etzhayyim.com:{iso3}                       — jurisdiction (e.g. :jpn, :usa, :gbr)
did:web:legal-entity.etzhayyim.com:{iso3}:{reg_id}              — national registry entity
did:web:legal-entity.etzhayyim.com:industry:{isic_section}       — ISIC section
did:web:legal-entity.etzhayyim.com:bridge:wikidata:{QID}         — Wikidata bridging key
did:web:legal-entity.etzhayyim.com:bridge:opencorporates:{id}    — OpenCorporates bridging key
```

### vertex_legal_entity Schema Extension (Multi-Source)

| Column | Type | Purpose |
|---|---|---|
| `vertex_id` | VARCHAR PK | `le:{source}:{id}` (e.g. `le:gleif:XXXX`, `le:nta:1234567890123`) |
| `source` | VARCHAR | `gleif`, `nta_jpn`, `ch_gbr`, `sirene_fra`, `opencorporates`, ... |
| `source_record_id` | VARCHAR | Original record ID from source |
| `lei` | VARCHAR | LEI (if available) |
| `registration_number` | VARCHAR | National registration number |
| `wikidata_qid` | VARCHAR | Wikidata QID (bridging) |
| `opencorporates_id` | VARCHAR | OpenCorporates ID (bridging) |
| (existing columns) | ... | name, jurisdiction, country, status, entity_type, etc. |

### Entity Resolution (Phase 4)

```
vertex_legal_entity (lei=..., source="gleif")
  ←[:SAME_AS]→ vertex_legal_entity (reg_number=..., source="nta_jpn")
  ←[:SAME_AS]→ vertex_legal_entity (company_number=..., source="ch_gbr")
  ←[:LINKED_IN]→ vertex_wikidata (qid="Q...")
```

Resolution logic:
1. LEI `registeredAs` → national reg number JOIN
2. Wikidata QID bridging (SPARQL: `wdt:P1278` LEI, `wdt:P3225` CRN UK, etc.)
3. Name + Jurisdiction fuzzy match (Levenshtein + IDF)

---

## Data Source Catalog: 194+ Countries

### Tier G: Global / Multi-National

| ID | Source | Method | Format | Records | Endpoint | Tier |
|---|---|---|---|---|---|---|
| G1 | **GLEIF (LEI)** | REST API | JSON | 3.0M active | `api.gleif.org/api/v1/lei-records` | **T1 LIVE** |
| G2 | **OpenCorporates** | REST API (paid bulk) | JSON | 200M+ (180+ jurisdictions) | `api.opencorporates.com/v0.4/` | T2 |
| G3 | **Wikidata (corps)** | SPARQL | JSON | ~3M orgs | `query.wikidata.org/sparql` | T1 |
| G4 | **Open Ownership (BODS)** | Bulk JSON | JSON-LD | ~10M UBO records | `register.openownership.org/` | T2 |
| G5 | **DUNS (D&B)** | Commercial API | JSON | 400M+ | Paid contract | T3 |
| G6 | **ISNI** | REST API | XML | 12M+ | `isni.org/isni/` | T2 |
| G7 | **ROR** | REST API | JSON | 105K research orgs | `api.ror.org/v2/organizations` | T1 |
| G8 | **UN LOCODE** | Bulk CSV | CSV | 100K+ locations | UNECE download | T2 |
| G9 | **EU BRIS** | REST API | JSON | EU 27 cross-border | BRIS interconnection | T1 |

### Asia-Pacific (38 Countries)

| ID | Country | ISO3 | Source | Method | Format | Records | Tier |
|---|---|---|---|---|---|---|---|
| AP1 | **Japan** | JPN | 国税庁 法人番号公表サイト | REST API + CSV bulk | CSV/XML | 6.2M | **T1** |
| AP2 | Japan | JPN | EDINET (金融庁) | REST API | JSON/XBRL | 5K listed | T1 |
| AP3 | Japan | JPN | 登記情報提供サービス | Web (paid) | HTML | 3M+ | T3 |
| AP4 | **China** | CHN | 国家企業信用信息公示系統 | Web scrape | HTML | 150M+ | T3 |
| AP5 | China | CHN | Tianyancha / Qichacha | Commercial API | JSON | 200M+ | T3 |
| AP6 | **South Korea** | KOR | DART (FSS) | REST API | JSON/XML | 2.5K listed | T1 |
| AP7 | South Korea | KOR | 국세청 사업자등록 | API | JSON | 8M+ | T2 |
| AP8 | **India** | IND | MCA21 (CIN) | Web + limited API | JSON/CSV | 2.5M+ | T2 |
| AP9 | India | IND | SEBI EDGAR India | REST API | JSON | 7K listed | T1 |
| AP10 | **Australia** | AUS | ABR (ABN Lookup) | REST API (XML) | XML | 4.5M | **T1** |
| AP11 | **New Zealand** | NZL | Companies Office | REST API | JSON | 800K | T1 |
| AP12 | **Singapore** | SGP | ACRA BizFile+ | API (paid) | JSON | 500K+ | T2 |
| AP13 | **Hong Kong** | HKG | ICRIS (CR) | Web scrape | HTML | 2M+ | T3 |
| AP14 | **Taiwan** | TWN | 經濟部商業司 | Web + CSV bulk | CSV | 1.5M+ | T2 |
| AP15 | **Thailand** | THA | DBD (Commerce Ministry) | Web | HTML | 800K+ | T3 |
| AP16 | **Malaysia** | MYS | SSM (e-Info) | Web (paid) | HTML | 1.3M+ | T3 |
| AP17 | **Indonesia** | IDN | AHU Online (MoLHR) | Web | HTML | 5M+ | T3 |
| AP18 | **Philippines** | PHL | SEC Philippines | Web + CSV | CSV | 600K+ | T2 |
| AP19 | **Vietnam** | VNM | National Business Registration Portal | Web | HTML | 900K+ | T3 |
| AP20 | **Bangladesh** | BGD | RJSC | Web | HTML | 200K+ | T3 |
| AP21 | **Pakistan** | PAK | SECP eServices | Web | HTML | 100K+ | T3 |
| AP22 | **Sri Lanka** | LKA | Dept of Registrar | Web | HTML | 100K+ | T3 |
| AP23 | **Nepal** | NPL | OCR Nepal | Web | HTML | 50K+ | T3 |
| AP24 | **Cambodia** | KHM | MOC Cambodia | Web | HTML | 30K+ | T3 |
| AP25 | **Myanmar** | MMR | DICA MyCO | Web | HTML | 60K+ | T3 |
| AP26 | **Laos** | LAO | MOIC | Web | HTML | 20K+ | T3 |
| AP27 | **Mongolia** | MNG | eBarimt | Web | HTML | 50K+ | T3 |
| AP28 | **Brunei** | BRN | ROCBN | Web | HTML | 10K+ | T3 |
| AP29 | **Fiji** | FJI | Registrar of Companies | Web | HTML | 15K+ | T3 |
| AP30 | **Papua New Guinea** | PNG | IPA PNG | Web | HTML | 10K+ | T3 |
| AP31 | **Timor-Leste** | TLS | SERVE | Web | HTML | 5K+ | T3 |
| AP32 | **Samoa** | WSM | SBEC | Web | HTML | 3K+ | T3 |
| AP33 | **Tonga** | TON | Ministry of Commerce | Web | HTML | 2K+ | T3 |
| AP34 | **Vanuatu** | VUT | VFSC | Web | HTML | 10K+ (offshore) | T3 |
| AP35 | **Marshall Islands** | MHL | Trust Company | Web | HTML | 50K+ (offshore) | T3 |
| AP36 | **Palau** | PLW | Registrar | Web | HTML | 1K+ | T3 |
| AP37 | **Micronesia** | FSM | Registrar | Web | HTML | 1K+ | T3 |
| AP38 | **Kiribati** | KIR | Registrar | Web | HTML | 1K+ | T3 |

### Europe (50 Countries)

| ID | Country | ISO3 | Source | Method | Format | Records | Tier |
|---|---|---|---|---|---|---|---|
| EU1 | **United Kingdom** | GBR | Companies House | REST API + bulk | JSON/CSV | 5M+ | **T1** |
| EU2 | **France** | FRA | INSEE SIRENE | Bulk CSV (open) | CSV | 12M+ SIREN | **T1** |
| EU3 | France | FRA | RNE (Registre National des Entreprises) | API | JSON | 12M+ | T1 |
| EU4 | **Germany** | DEU | Handelsregister (common register) | Web + XML | XML | 4M+ | T2 |
| EU5 | Germany | DEU | Unternehmensregister | SOAP/XML | XML | 4M+ | T2 |
| EU6 | **Italy** | ITA | Registro Imprese (InfoCamere) | API (paid) | JSON | 6M+ | T2 |
| EU7 | **Spain** | ESP | Registro Mercantil Central | Web | HTML | 3.5M+ | T3 |
| EU8 | **Netherlands** | NLD | KVK (Handelsregister) | REST API | JSON | 2.5M+ | **T1** |
| EU9 | **Belgium** | BEL | KBO/BCE (Crossroads Bank) | Bulk CSV (open) | CSV | 3M+ | **T1** |
| EU10 | **Switzerland** | CHE | Zefix (FOSC) | REST API | JSON | 700K+ | **T1** |
| EU11 | **Austria** | AUT | Firmenbuch (Justiz) | Web | HTML | 500K+ | T3 |
| EU12 | **Sweden** | SWE | Bolagsverket | API (paid) | JSON | 1.2M+ | T2 |
| EU13 | **Norway** | NOR | Bronnøysund Register | REST API (free) | JSON | 1M+ | **T1** |
| EU14 | **Denmark** | DNK | CVR (Virk.dk) | REST API (free) | JSON | 800K+ | **T1** |
| EU15 | **Finland** | FIN | PRH (YTJ) | REST API | JSON | 600K+ | **T1** |
| EU16 | **Ireland** | IRL | CRO | REST API | JSON | 300K+ | T1 |
| EU17 | **Portugal** | PRT | Portal da Empresa | Web | HTML | 1.5M+ | T3 |
| EU18 | **Poland** | POL | KRS (National Court Register) | REST API | JSON | 500K+ | T1 |
| EU19 | **Czech Republic** | CZE | ARES (MF) | REST API | XML/JSON | 3M+ | **T1** |
| EU20 | **Hungary** | HUN | e-Cegjegyzek | Web | HTML | 700K+ | T3 |
| EU21 | **Romania** | ROU | ONRC (e-Portal) | Web | HTML | 1M+ | T3 |
| EU22 | **Bulgaria** | BGR | Commercial Register (TR) | REST API | JSON | 400K+ | T1 |
| EU23 | **Croatia** | HRV | Sudski Registar | Web | HTML | 300K+ | T3 |
| EU24 | **Slovakia** | SVK | ORSR | REST API | JSON | 300K+ | T1 |
| EU25 | **Slovenia** | SVN | AJPES (ePRS) | REST API | JSON | 200K+ | T1 |
| EU26 | **Lithuania** | LTU | Registru Centras | REST API | JSON | 200K+ | T1 |
| EU27 | **Latvia** | LVA | UR (Lursoft) | API (paid) | JSON | 200K+ | T2 |
| EU28 | **Estonia** | EST | e-Business Register | REST API (free) | JSON | 300K+ | **T1** |
| EU29 | **Luxembourg** | LUX | RCSL (LBR) | REST API | JSON | 150K+ | T1 |
| EU30 | **Malta** | MLT | MBR | Web | HTML | 70K+ | T3 |
| EU31 | **Cyprus** | CYP | DRCOR | Web | HTML | 300K+ | T3 |
| EU32 | **Greece** | GRC | GEMI | Web | HTML | 700K+ | T3 |
| EU33 | **Serbia** | SRB | APR | REST API | JSON | 400K+ | T1 |
| EU34 | **North Macedonia** | MKD | CRM | Web | HTML | 80K+ | T3 |
| EU35 | **Bosnia** | BIH | Court Registry | Web | HTML | 60K+ | T3 |
| EU36 | **Montenegro** | MNE | CRPS | Web | HTML | 30K+ | T3 |
| EU37 | **Albania** | ALB | QKR (NBC) | Web | HTML | 100K+ | T3 |
| EU38 | **Kosovo** | XKX | KBRA | Web | HTML | 50K+ | T3 |
| EU39 | **Iceland** | ISL | RSK (Skatturinn) | REST API | JSON | 50K+ | T1 |
| EU40 | **Liechtenstein** | LIE | Handelsregister | Web | HTML | 40K+ | T3 |
| EU41 | **Monaco** | MCO | RCI Monaco | Web | HTML | 5K+ | T3 |
| EU42 | **San Marino** | SMR | Registro Societa | Web | HTML | 5K+ | T3 |
| EU43 | **Andorra** | AND | Registre de Societats | Web | HTML | 8K+ | T3 |
| EU44 | **Moldova** | MDA | ASP | Web | HTML | 100K+ | T3 |
| EU45 | **Ukraine** | UKR | USR (Opendatabot) | REST API | JSON | 1.5M+ | T1 |
| EU46 | **Belarus** | BLR | EGR | Web | HTML | 200K+ | T3 |
| EU47 | **Georgia** | GEO | NAPR | REST API | JSON | 200K+ | T1 |
| EU48 | **Armenia** | ARM | e-Register | Web | HTML | 50K+ | T3 |
| EU49 | **Azerbaijan** | AZE | Taxes Ministry | Web | HTML | 100K+ | T3 |
| EU50 | **Turkey** | TUR | MERSIS (TOBB) | Web | HTML | 2M+ | T3 |

### Americas (35 Countries)

| ID | Country | ISO3 | Source | Method | Format | Records | Tier |
|---|---|---|---|---|---|---|---|
| AM1 | **United States** | USA | SEC EDGAR (CIK) | REST API | JSON | 10K+ listed | **T1** |
| AM2 | US | USA | Delaware Division of Corps | Bulk CSV | CSV | 1.8M | T2 |
| AM3 | US | USA | 50 State SOS (aggregate) | OpenCorporates | JSON | 30M+ | T2 |
| AM4 | US | USA | FinCEN BOI | API (restricted) | JSON | ~30M | T3 |
| AM5 | **Canada** | CAN | Corporations Canada (ISED) | REST API | JSON | 500K federal | **T1** |
| AM6 | Canada | CAN | Provinces (ON, QC, BC, AB) | Various | Various | 3M+ | T2 |
| AM7 | **Mexico** | MEX | SAT (RFC lookup) | Web | HTML | 5M+ | T3 |
| AM8 | **Brazil** | BRA | Receita Federal (CNPJ) | Bulk CSV (open) | CSV | 55M+ | **T1** |
| AM9 | **Argentina** | ARG | AFIP / IGJ | Web | HTML | 1M+ | T3 |
| AM10 | **Colombia** | COL | RUES (Confecamaras) | REST API | JSON | 2M+ | T2 |
| AM11 | **Chile** | CHL | SII / Registro de Empresas | Web | HTML | 1M+ | T3 |
| AM12 | **Peru** | PER | SUNAT (RUC) | Web | HTML | 2M+ | T3 |
| AM13 | **Ecuador** | ECU | SRI / Superintendencia | Web | HTML | 500K+ | T3 |
| AM14 | **Venezuela** | VEN | SENIAT | Web | HTML | 500K+ | T3 |
| AM15 | **Uruguay** | URY | DGI | Web | HTML | 200K+ | T3 |
| AM16 | **Paraguay** | PRY | SET | Web | HTML | 100K+ | T3 |
| AM17 | **Bolivia** | BOL | SEPREC (Fundempresa) | Web | HTML | 300K+ | T3 |
| AM18 | **Panama** | PAN | Registro Publico | Web | HTML | 400K+ (offshore) | T3 |
| AM19 | **Costa Rica** | CRI | Registro Nacional | Web | HTML | 200K+ | T3 |
| AM20 | **Guatemala** | GTM | Registro Mercantil | Web | HTML | 100K+ | T3 |
| AM21 | **Honduras** | HND | IP Registry | Web | HTML | 50K+ | T3 |
| AM22 | **El Salvador** | SLV | CNR | Web | HTML | 50K+ | T3 |
| AM23 | **Nicaragua** | NIC | Registro Publico | Web | HTML | 30K+ | T3 |
| AM24 | **Dominican Republic** | DOM | DGII / Camara de Comercio | Web | HTML | 200K+ | T3 |
| AM25 | **Jamaica** | JAM | Companies Office | Web | HTML | 80K+ | T3 |
| AM26 | **Trinidad & Tobago** | TTO | Companies Registry | Web | HTML | 50K+ | T3 |
| AM27 | **Bahamas** | BHS | Registrar General | Web | HTML | 100K+ (offshore) | T3 |
| AM28 | **Barbados** | BRB | CAD | Web | HTML | 30K+ | T3 |
| AM29 | **Cayman Islands** | CYM | CIMA | Web | HTML | 120K+ (offshore) | T3 |
| AM30 | **BVI** | VGB | FSC BVI | Web | HTML | 400K+ (offshore) | T3 |
| AM31 | **Bermuda** | BMU | Registrar of Companies | Web | HTML | 15K+ | T3 |
| AM32 | **Curacao** | CUW | Chamber of Commerce | Web | HTML | 10K+ | T3 |
| AM33 | **Belize** | BLZ | IFS Belize | Web | HTML | 50K+ (offshore) | T3 |
| AM34 | **Haiti** | HTI | MCI | Web | HTML | 10K+ | T3 |
| AM35 | **Cuba** | CUB | MINCEX | N/A | N/A | Restricted | T3 |

### Middle East & North Africa (22 Countries)

| ID | Country | ISO3 | Source | Method | Format | Records | Tier |
|---|---|---|---|---|---|---|---|
| ME1 | **UAE** | ARE | DED / DIFC / ADGM | REST API (partial) | JSON | 600K+ | T2 |
| ME2 | **Saudi Arabia** | SAU | MC (Wazarat al-Tijara) | Web | HTML | 1M+ | T3 |
| ME3 | **Israel** | ISR | Companies Registrar | REST API | JSON | 600K+ | **T1** |
| ME4 | **Qatar** | QAT | MOEC | Web | HTML | 50K+ | T3 |
| ME5 | **Kuwait** | KWT | MOCI | Web | HTML | 100K+ | T3 |
| ME6 | **Bahrain** | BHR | MOICT (Sijilat) | Web | HTML | 80K+ | T3 |
| ME7 | **Oman** | OMN | MOCI | Web | HTML | 100K+ | T3 |
| ME8 | **Jordan** | JOR | CCD | Web | HTML | 100K+ | T3 |
| ME9 | **Lebanon** | LBN | CR Beirut | Web | HTML | 50K+ | T3 |
| ME10 | **Egypt** | EGY | GAFI / IDA | Web | HTML | 500K+ | T3 |
| ME11 | **Morocco** | MAR | OMPIC | Web | HTML | 400K+ | T3 |
| ME12 | **Tunisia** | TUN | RNE Tunisia | Web | HTML | 200K+ | T3 |
| ME13 | **Algeria** | DZA | CNRC | Web | HTML | 200K+ | T3 |
| ME14 | **Libya** | LBY | Ministry of Economy | N/A | N/A | Restricted | T3 |
| ME15 | **Iraq** | IRQ | Companies Registrar | Web | HTML | 50K+ | T3 |
| ME16 | **Iran** | IRN | IRSOG | Web (Farsi) | HTML | 500K+ | T3 |
| ME17 | **Syria** | SYR | N/A | N/A | N/A | Restricted | T3 |
| ME18 | **Yemen** | YEM | N/A | N/A | N/A | Restricted | T3 |
| ME19 | **Palestine** | PSE | Companies Controller | Web | HTML | 10K+ | T3 |
| ME20 | **Sudan** | SDN | RSCR | Web | HTML | 20K+ | T3 |
| ME21 | **Mauritania** | MRT | GUICHET | Web | HTML | 5K+ | T3 |
| ME22 | **Djibouti** | DJI | ODPIC | Web | HTML | 2K+ | T3 |

### Sub-Saharan Africa (49 Countries)

| ID | Country | ISO3 | Source | Method | Format | Records | Tier |
|---|---|---|---|---|---|---|---|
| AF1 | **South Africa** | ZAF | CIPC | REST API | JSON | 3M+ | **T1** |
| AF2 | **Nigeria** | NGA | CAC Nigeria | Web + API | JSON | 3M+ | T2 |
| AF3 | **Kenya** | KEN | eCitizen BRS | Web | HTML | 500K+ | T3 |
| AF4 | **Ghana** | GHA | Registrar General | Web | HTML | 300K+ | T3 |
| AF5 | **Ethiopia** | ETH | Ministry of Trade | Web | HTML | 100K+ | T3 |
| AF6 | **Tanzania** | TZA | BRELA | Web | HTML | 200K+ | T3 |
| AF7 | **Uganda** | UGA | URSB | Web | HTML | 100K+ | T3 |
| AF8 | **Rwanda** | RWA | RDB | REST API | JSON | 100K+ | T2 |
| AF9 | **Senegal** | SEN | APIX | Web | HTML | 50K+ | T3 |
| AF10 | **Cote d'Ivoire** | CIV | CEPICI | Web | HTML | 100K+ | T3 |
| AF11 | **Cameroon** | CMR | CFCE | Web | HTML | 50K+ | T3 |
| AF12 | **DR Congo** | COD | GUICHET | Web | HTML | 30K+ | T3 |
| AF13 | **Angola** | AGO | GUUE | Web | HTML | 50K+ | T3 |
| AF14 | **Mozambique** | MOZ | CRE | Web | HTML | 30K+ | T3 |
| AF15 | **Zimbabwe** | ZWE | CR Zimbabwe | Web | HTML | 100K+ | T3 |
| AF16 | **Zambia** | ZMB | PACRA | Web | HTML | 100K+ | T3 |
| AF17 | **Botswana** | BWA | CIPA | Web | HTML | 50K+ | T3 |
| AF18 | **Namibia** | NAM | BIPA | Web | HTML | 30K+ | T3 |
| AF19 | **Madagascar** | MDG | EDBM | Web | HTML | 20K+ | T3 |
| AF20 | **Mauritius** | MUS | CBRD | REST API | JSON | 150K+ (offshore) | T2 |
| AF21 | **Seychelles** | SYC | FSA Seychelles | Web | HTML | 200K+ (offshore) | T3 |
| AF22 | **Mali** | MLI | API-Mali | Web | HTML | 30K+ | T3 |
| AF23 | **Burkina Faso** | BFA | CEFORE | Web | HTML | 20K+ | T3 |
| AF24 | **Niger** | NER | CNIP | Web | HTML | 10K+ | T3 |
| AF25 | **Chad** | TCD | ANIE | Web | HTML | 5K+ | T3 |
| AF26 | **Guinea** | GIN | APIP | Web | HTML | 15K+ | T3 |
| AF27 | **Sierra Leone** | SLE | OARG | Web | HTML | 10K+ | T3 |
| AF28 | **Liberia** | LBR | LBR | Web | HTML | 20K+ (offshore) | T3 |
| AF29 | **Togo** | TGO | CFE Togo | Web | HTML | 10K+ | T3 |
| AF30 | **Benin** | BEN | APIEx | Web | HTML | 15K+ | T3 |
| AF31 | **Gabon** | GAB | ANPI | Web | HTML | 10K+ | T3 |
| AF32 | **Equatorial Guinea** | GNQ | Ministry | Web | HTML | 3K+ | T3 |
| AF33 | **Central African Rep.** | CAF | GUICHET | Web | HTML | 3K+ | T3 |
| AF34 | **Congo Republic** | COG | CFE | Web | HTML | 10K+ | T3 |
| AF35 | **Burundi** | BDI | API Burundi | Web | HTML | 5K+ | T3 |
| AF36 | **Malawi** | MWI | RG Malawi | Web | HTML | 20K+ | T3 |
| AF37 | **Lesotho** | LSO | CR Lesotho | Web | HTML | 5K+ | T3 |
| AF38 | **Eswatini** | SWZ | RSTP | Web | HTML | 5K+ | T3 |
| AF39 | **Comoros** | COM | ANPI | Web | HTML | 2K+ | T3 |
| AF40 | **Cabo Verde** | CPV | Casa do Cidadao | Web | HTML | 5K+ | T3 |
| AF41 | **Sao Tome & Principe** | STP | Ministry | Web | HTML | 1K+ | T3 |
| AF42 | **Gambia** | GMB | GIEPA | Web | HTML | 5K+ | T3 |
| AF43 | **Guinea-Bissau** | GNB | Ministry | Web | HTML | 2K+ | T3 |
| AF44 | **Eritrea** | ERI | Ministry | N/A | N/A | Restricted | T3 |
| AF45 | **Somalia** | SOM | Ministry | N/A | N/A | Restricted | T3 |
| AF46 | **South Sudan** | SSD | Ministry | N/A | N/A | Restricted | T3 |
| AF47 | **Western Sahara** | ESH | N/A | N/A | N/A | Disputed | T3 |
| AF48 | **Reunion/Mayotte** | REU | INSEE SIRENE (FR) | Same as FR | CSV | Included in FR | T1 |
| AF49 | **Mauritius offshore** | MUS | GBC1/GBC2 | FSC API | JSON | 20K+ | T2 |

---

## Phase Roadmap

### Phase 1: T1 API-First (13 Sources, ~95M records)

Immediate implementation. Each source gets a `collect{Iso3}` command in `le9k4x2m`.

| Priority | Source | ISO3 | Est. Records | Lexicon |
|---|---|---|---|---|
| P0 | GLEIF (full) | Global | 3.0M | `collectGlobal` (existing) |
| P1 | JP NTA | JPN | 6.2M | `collectJpn` |
| P2 | UK Companies House | GBR | 5.0M | `collectGbr` |
| P3 | FR SIRENE | FRA | 12.0M | `collectFra` |
| P4 | BR CNPJ | BRA | 55.0M | `collectBra` |
| P5 | NO Bronnøysund | NOR | 1.0M | `collectNor` |
| P6 | DK CVR | DNK | 0.8M | `collectDnk` |
| P7 | FI PRH | FIN | 0.6M | `collectFin` |
| P8 | EE e-Business | EST | 0.3M | `collectEst` |
| P9 | BE KBO | BEL | 3.0M | `collectBel` |
| P10 | CZ ARES | CZE | 3.0M | `collectCze` |
| P11 | NZ Companies Office | NZL | 0.8M | `collectNzl` |
| P12 | AU ABR | AUS | 4.5M | `collectAus` |

#### Common Collector Pattern

```ts
sdk.app.command("com.etzhayyim.legalEntity.collect{Iso3}", async (input) => {
  // 1. Fetch from national API (paginated)
  const resp = await sdk.net.fetch(API_URL, { params });
  // 2. Normalize to common LegalEntity schema
  const records = normalizeSource(resp.data, "{iso3}", "{source_id}");
  // 3. Batch write to PDS (applyWrites, 200/batch)
  await batchWritePDS(records);
  // 4. Register path-based DIDs for jurisdiction
  await sdk.did.create("{iso3}", { displayName: "..." });
});
```

### Phase 2: T2 Bulk Download (15 Sources, ~50M records)

B2 staging + cron parse pipeline.

```
[Cron: daily/weekly]
  -> Download bulk CSV/XML -> R2 bucket (le-staging/)
    -> scheduled Worker -> stream parse -> normalize -> applyWrites
      -> PDS -> vertex_legal_entity
```

Targets: SEC EDGAR, DE Handelsregister, IT InfoCamere, SE Bolagsverket, SG ACRA, IN MCA21, TW Commerce, KR DART, CO RUES, UAE DED, NG CAC, RW RDB, MU CBRD, PH SEC, Wikidata SPARQL bulk.

### Phase 3: T3 OpenCorporates + Scraping (160+ Countries, ~200M records)

OpenCorporates paid bulk API for 180+ jurisdictions. Individual scrapers for high-ROI countries (CN, HK, MX, etc.).

```
[OpenCorporates API (paid bulk)]
  -> jurisdiction filter per country
    -> normalize -> applyWrites -> PDS -> vertex_legal_entity

[Individual Scrapers (CN, HK, etc.)]
  -> BrowserRendering / Playwright -> parse -> normalize -> applyWrites
```

### Phase 4: Entity Resolution & Cross-Border Graph

Build bridging edges between records from different sources.

1. LEI `registeredAs` -> national reg number JOIN
2. Wikidata QID bridging (SPARQL properties: P1278 LEI, P3225 UK CRN, P1320 OpenCorporates, etc.)
3. Name + Jurisdiction fuzzy match (Levenshtein + TF-IDF)
4. `[:SAME_AS]` edge generation between matched `vertex_legal_entity` records

---

## Estimated Scale

| Phase | Sources | Est. Total Records |
|---|---|---|
| Phase 1 (T1 API) | 13 | ~95M |
| Phase 2 (T2 Bulk) | 15 | ~50M |
| Phase 3 (T3 OC+Scrape) | 160+ | ~200M |
| **Total** | **194+** | **~345M** |

## References

- Existing GLEIF ingest: `70-tools/scripts/gleif-bulk-ingest.mjs`
- Legal entity project: `60-apps/etzhayyim-project-legal-entity/CLAUDE.md`
- Lexicons: `00-contracts/lexicons/com/etzhayyim/apps/legalEntity/`
- Graph schema: `30-graph/graph-schema/src/database.ts` (`VertexLegalEntityRow`)
- PDS typed vertex: `50-infra/cloudflare/workers/atproto/src/core.ts` (`buildTypedVertex("LegalEntity", ...)`)
