package main

import (
	"bytes"
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
	"time"

	"github.com/etzhayyim/root/70-tools/gftd/gftd/db"
	"github.com/jackc/pgx/v5/pgtype"
)

const legacyVertexOtherTable = "vertex_" + "other"

// ── World reference data (real-world totals for coverage denominator) ──

type worldDomain struct {
	Domain      string   `json:"domain"`
	App         string   `json:"app"`
	AltPrefixes []string `json:"altPrefixes,omitempty"` // additional DID host prefixes to count (e.g. "isic-a","isic-b",... or "gov-" for prefix match)
	WorldTotal  int      `json:"worldTotal"`
	Unit        string   `json:"unit"`
	Source      string   `json:"source"`
	DIDLabel    string   `json:"didLabel"`    // Sql label to count
	RecordLabel string   `json:"recordLabel"` // optional: record collection
}

var worldDomains = []worldDomain{
	{Domain: "dns", App: "dns.etzhayyim.com", WorldTotal: 350_000_000, Unit: "registered domains", Source: "Verisign Domain Name Industry Brief 2025", DIDLabel: "zone"},
	{Domain: "dns_whois_history", App: "dns.etzhayyim.com", WorldTotal: 350_000_000, Unit: "domain WHOIS snapshots (registrant/registrar history)", Source: "Verisign Domain Brief 2025", DIDLabel: "whois_snapshot"},
	{Domain: "dns_cert_history", App: "dns.etzhayyim.com", WorldTotal: 1_000_000_000, Unit: "SSL/TLS certificates issued (CT log)", Source: "CT log aggregate (crt.sh)", DIDLabel: "cert_history"},
	{Domain: "legal_entity", App: "legal-entity.etzhayyim.com", WorldTotal: 400_000_000, Unit: "legal entities", Source: "World Bank / OpenCorporates estimate", DIDLabel: "entity"},
	{Domain: "natural_person", App: "natural-person.etzhayyim.com", WorldTotal: 8_100_000_000, Unit: "natural persons", Source: "UN World Population 2025", DIDLabel: "person"},
	{Domain: "hanrei", App: "hanrei.etzhayyim.com", WorldTotal: 400_000, Unit: "court decisions (JP)", Source: "courts.go.jp published", DIDLabel: "court"},
	{Domain: "chotatsu", App: "chotatsu.etzhayyim.com", WorldTotal: 200_000, Unit: "procurement notices/yr (JP)", Source: "e-Gov 調達情報", DIDLabel: "procurement"},
	{Domain: "pachinko", App: "pachinko.etzhayyim.com", WorldTotal: 7_500, Unit: "pachinko stores (JP)", Source: "警察庁 遊技場データ 2025", DIDLabel: "store"},
	{Domain: "autorace", App: "autorace.etzhayyim.com", WorldTotal: 5, Unit: "autorace venues", Source: "JKA 公式", DIDLabel: "venue"},
	{Domain: "keirin", App: "keirin.etzhayyim.com", WorldTotal: 43, Unit: "keirin velodromes", Source: "JKA 競輪場", DIDLabel: "velodrome"},
	{Domain: "kyotei", App: "kyotei.etzhayyim.com", WorldTotal: 24, Unit: "kyotei boat race venues", Source: "BOATRACE 公式", DIDLabel: "venue"},
	{Domain: "isin", App: "isin.etzhayyim.com", WorldTotal: 20_000_000, Unit: "ISIN securities", Source: "ANNA (Association of National Numbering Agencies)", DIDLabel: "security"},
	{Domain: "gtin", App: "gtin.etzhayyim.com", WorldTotal: 1_000_000_000, Unit: "GTIN barcodes", Source: "GS1 global estimate", DIDLabel: "product"},
	{Domain: "isbn", App: "isbn.etzhayyim.com", WorldTotal: 175_000_000, Unit: "ISBN books", Source: "International ISBN Agency", DIDLabel: "book"},
	{Domain: "isbn_pd_fulltext", App: "isbn.etzhayyim.com", WorldTotal: 587_000, Unit: "public domain book fulltexts (Aozora+Gutenberg+NDL)", Source: "Aozora 17K + Gutenberg 70K + NDL 500K", DIDLabel: "book_fulltext"},
	{Domain: "cas", App: "cas.etzhayyim.com", WorldTotal: 210_000_000, Unit: "CAS substances", Source: "CAS Registry 2025", DIDLabel: "substance"},
	{Domain: "ndc", App: "ndc.etzhayyim.com", WorldTotal: 350_000, Unit: "NDC drug codes", Source: "FDA NDC Directory + WHO ATC", DIDLabel: "drug"},
	{Domain: "maps", App: "maps.etzhayyim.com", WorldTotal: 200_000_000, Unit: "addressable locations", Source: "OpenAddresses + OSM estimate", DIDLabel: "location"},
	{Domain: "jinushi", App: "jinushi.etzhayyim.com", WorldTotal: 3_500_000_000, Unit: "land parcels (global)", Source: "FAO/Cadastre aggregates", DIDLabel: "parcel"},
	{Domain: "ipaddress", App: "ipaddress.etzhayyim.com", WorldTotal: 4_294_967_296, Unit: "IPv4 addresses", Source: "IANA", DIDLabel: "ip"},
	{Domain: "anima", App: "anima.etzhayyim.com", WorldTotal: 8_700_000, Unit: "known species", Source: "IUCN Red List + Catalogue of Life", DIDLabel: "species"},
	{Domain: "blockchain", App: "blockchain.etzhayyim.com", WorldTotal: 1000, Unit: "active chains", Source: "DefiLlama / CoinGecko chain count", DIDLabel: "chain"},
	{Domain: "blockchain_address", App: "blockchain.etzhayyim.com", WorldTotal: 1_300_000_000, Unit: "blockchain addresses (BTC+ETH)", Source: "Glassnode / Etherscan 2025", DIDLabel: "address"},
	{Domain: "blockchain_transaction", App: "blockchain.etzhayyim.com", WorldTotal: 3_500_000_000, Unit: "blockchain transactions (BTC+ETH)", Source: "Blockchain.com / Etherscan 2025", DIDLabel: "transaction"},
	{Domain: "treaty", App: "treaty.etzhayyim.com", WorldTotal: 560, Unit: "multilateral treaties", Source: "UN Treaty Collection", DIDLabel: "treaty"},
	{Domain: "sovereign", App: "states.etzhayyim.com", AltPrefixes: []string{"gov-"}, WorldTotal: 195, Unit: "sovereign states", Source: "UN Member States + observers", DIDLabel: "state"},
	{Domain: "communities", App: "communities.etzhayyim.com", WorldTotal: 10_000, Unit: "intl organizations", Source: "UIA Yearbook", DIDLabel: "org"},
	{Domain: "isco", App: "isco.etzhayyim.com", WorldTotal: 436, Unit: "ISCO-08 occupations", Source: "ILO ISCO-08", DIDLabel: "occupation"},
	{Domain: "isic", App: "isic.etzhayyim.com", AltPrefixes: []string{"isic-"}, WorldTotal: 419, Unit: "ISIC Rev.4 industries", Source: "UNSD ISIC Rev.4", DIDLabel: "industry"},
	// Law & Governance
	{Domain: "hanrei_global", App: "hanrei.etzhayyim.com", WorldTotal: 50_000_000, Unit: "court decisions (global)", Source: "WorldLII + national court databases (83 jurisdictions)", DIDLabel: "decision"},
	{Domain: "bankruptcy", App: "bankruptcy.etzhayyim.com", WorldTotal: 5_000_000, Unit: "insolvency proceedings/yr (global)", Source: "World Bank Doing Business + UNCITRAL", DIDLabel: "proceeding"},
	{Domain: "legal_entity_lei", App: "legal-entity.etzhayyim.com", WorldTotal: 2_700_000, Unit: "LEI registrations", Source: "GLEIF (ISO 17442)", DIDLabel: "lei"},
	{Domain: "religious", App: "religious.etzhayyim.com", WorldTotal: 4_300, Unit: "religious legal systems", Source: "JuriGlobe + national constitutions", DIDLabel: "system"},
	{Domain: "customary", App: "customary.etzhayyim.com", WorldTotal: 1_500, Unit: "customary law systems", Source: "JuriGlobe + ethnographic surveys", DIDLabel: "system"},
	{Domain: "ethics", App: "ethics.etzhayyim.com", WorldTotal: 12_000, Unit: "professional ethics codes", Source: "IBA + IFAC + national bar associations", DIDLabel: "code"},
	{Domain: "judge", App: "judge.etzhayyim.com", WorldTotal: 200_000, Unit: "judges & magistrates (global)", Source: "CEPEJ + ABA + 最高裁判所人事 + national judicial councils", DIDLabel: "judge"},
	{Domain: "bengoshi", App: "bengoshi.etzhayyim.com", WorldTotal: 2_500_000, Unit: "licensed lawyers/attorneys (global)", Source: "IBA + ABA + 日弁連 + national bar associations", DIDLabel: "lawyer"},
	{Domain: "adr", App: "adr.etzhayyim.com", WorldTotal: 1_000_000, Unit: "ADR cases/yr (mediation+arbitration)", Source: "ICC + JCAA + AAA + UNCITRAL + national ADR centers", DIDLabel: "case"},
	{Domain: "legal_aid", App: "legal-aid.etzhayyim.com", WorldTotal: 10_000_000, Unit: "legal aid cases/yr (global)", Source: "ILAG + 法テラス + national legal aid bodies", DIDLabel: "case"},
	{Domain: "business_person", App: "business-person.etzhayyim.com", WorldTotal: 100_000_000, Unit: "public business persons (corporate officers + executives + board members, global)", Source: "corporate registries + XBRL + Wikipedia + official disclosures", DIDLabel: "bp"},
	{Domain: "rare_earth_coverage", App: "rare-earth-coverage.etzhayyim.com", WorldTotal: 350, Unit: "rare-earth supply chain segment nodes (mining/separation/magnet/policy/finance/recycling)", Source: "USGS + IEA + Adamas Intelligence + national mineral surveys", DIDLabel: "segment"},
	{Domain: "industry_standard", App: "industry-standard.etzhayyim.com", WorldTotal: 45_000, Unit: "industry standards", Source: "ISO + IEC + IEEE + national bodies", DIDLabel: "standard"},
	// Intelligence & Security
	{Domain: "malak", App: "malak.etzhayyim.com", WorldTotal: 500_000, Unit: "cybercrime indicators/yr", Source: "MITRE ATT&CK + VirusTotal + abuse.ch", DIDLabel: "indicator"},
	{Domain: "ct_monitor", App: "ct-monitor.etzhayyim.com", WorldTotal: 10_000_000_000, Unit: "CT log certificates", Source: "Google CT Log + crt.sh", DIDLabel: "cert"},
	{Domain: "sbom", App: "sbom.etzhayyim.com", WorldTotal: 50_000_000, Unit: "software packages", Source: "npm + PyPI + crates.io + Maven + NuGet", DIDLabel: "package"},
	{Domain: "supply_chain", App: "supply-chain.etzhayyim.com", WorldTotal: 100_000_000, Unit: "vendor relationships", Source: "D&B + Ecovadis estimates", DIDLabel: "vendor"},
	// Commerce & Finance
	{Domain: "issn", App: "issn.etzhayyim.com", WorldTotal: 2_500_000, Unit: "ISSN serials", Source: "ISSN International Centre", DIDLabel: "serial"},
	{Domain: "cpc", App: "cpc.etzhayyim.com", WorldTotal: 2_738, Unit: "CPC Ver.2.1 products", Source: "UNSD CPC Ver.2.1", DIDLabel: "product"},
	{Domain: "unspsc", App: "unspsc.etzhayyim.com", WorldTotal: 70_000, Unit: "UNSPSC commodities", Source: "UNSPSC v26", DIDLabel: "commodity"},
	// Spatial & Physical
	{Domain: "maps_poi", App: "maps.etzhayyim.com", WorldTotal: 500_000_000, Unit: "POIs (global)", Source: "OSM + Google Places estimate", DIDLabel: "poi"},
	{Domain: "maps_building", App: "maps.etzhayyim.com", WorldTotal: 1_500_000_000, Unit: "buildings (global)", Source: "Microsoft Building Footprints + OSM", DIDLabel: "building"},
	// Media & Content
	{Domain: "media_anime", App: "media-anime.etzhayyim.com", WorldTotal: 25_000, Unit: "anime titles", Source: "MAL + AniList + Annict", DIDLabel: "title"},
	{Domain: "media_gamers", App: "media-gamers.etzhayyim.com", WorldTotal: 900_000, Unit: "game titles", Source: "IGDB + MobyGames + Steam", DIDLabel: "game"},
	{Domain: "webpage", App: "webpage.etzhayyim.com", WorldTotal: 50_000_000_000, Unit: "web pages (indexed)", Source: "Common Crawl + Google estimate", DIDLabel: "page"},
	// Welfare & Society
	{Domain: "kaigo", App: "kaigo.etzhayyim.com", WorldTotal: 250_000, Unit: "care facilities (JP)", Source: "厚生労働省 介護サービス情報", DIDLabel: "facility"},
	{Domain: "society6", App: "society6.etzhayyim.com", WorldTotal: 195, Unit: "COFOG national systems", Source: "UN COFOG + national governance", DIDLabel: "system"},
	{Domain: "omatsuri", App: "omatsuri.etzhayyim.com", WorldTotal: 300_000, Unit: "festivals (JP)", Source: "観光庁 + 地方自治体祭事登録", DIDLabel: "festival"},
	{Domain: "joucho", App: "joucho.etzhayyim.com", WorldTotal: 8_100_000_000, Unit: "persons (joucho scoring)", Source: "UN World Population", DIDLabel: "person"},
	{Domain: "dojo", App: "dojo.etzhayyim.com", WorldTotal: 10_000, Unit: "readiness kata drills", Source: "gftd platform estimate", DIDLabel: "drill"},
	{Domain: "well_becoming", App: "well-becoming.etzhayyim.com", WorldTotal: 8_100_000_000, Unit: "persons (well-becoming)", Source: "UN World Population", DIDLabel: "person"},
	// Transport & Infrastructure
	{Domain: "railway", App: "railway.etzhayyim.com", WorldTotal: 1_370_000, Unit: "railway stations (global)", Source: "UIC + national railway databases", DIDLabel: "station"},
	{Domain: "port", App: "port.etzhayyim.com", WorldTotal: 8_500, Unit: "major ports (global)", Source: "World Port Source + UNCTAD", DIDLabel: "port"},
	{Domain: "road", App: "road.etzhayyim.com", WorldTotal: 64_000_000, Unit: "road km (global)", Source: "CIA World Factbook", DIDLabel: "segment"},
	{Domain: "vessel", App: "vessel.etzhayyim.com", WorldTotal: 105_000, Unit: "merchant vessels (IMO registered)", Source: "IMO GISIS + Lloyd's", DIDLabel: "vessel"},
	{Domain: "aircraft", App: "aircraft.etzhayyim.com", WorldTotal: 450_000, Unit: "registered aircraft (global)", Source: "ICAO + FAA + EASA", DIDLabel: "aircraft"},
	{Domain: "drone", App: "drone.etzhayyim.com", WorldTotal: 2_000_000, Unit: "registered drones (global)", Source: "FAA + EASA + national registries", DIDLabel: "drone"},
	{Domain: "vehicle", App: "vehicle.etzhayyim.com", WorldTotal: 1_500_000_000, Unit: "registered vehicles (global)", Source: "OICA + national registries", DIDLabel: "vehicle"},
	{Domain: "kuruma", App: "kuruma.etzhayyim.com", WorldTotal: 80_000, Unit: "car models (global)", Source: "car manufacturer databases", DIDLabel: "model"},
	{Domain: "car_maker", App: "kuruma.etzhayyim.com", WorldTotal: 5_000, Unit: "automotive OEMs & brands", Source: "OICA + MarkLines + brand registries", DIDLabel: "maker"},
	{Domain: "car_dealer", App: "kuruma.etzhayyim.com", WorldTotal: 500_000, Unit: "car dealerships (authorized+independent)", Source: "NADA + national dealer associations", DIDLabel: "dealer"},
	{Domain: "nirin", App: "nirin.etzhayyim.com", WorldTotal: 500_000_000, Unit: "motorcycles & bicycles (incl sharing)", Source: "OICA + national registries + bike-sharing", DIDLabel: "vehicle"},
	{Domain: "taxi", App: "taxi.etzhayyim.com", WorldTotal: 15_000_000, Unit: "taxis & ride-hail vehicles", Source: "IRU + Uber/Grab/DiDi fleet estimates", DIDLabel: "vehicle"},
	{Domain: "bus", App: "bus.etzhayyim.com", WorldTotal: 3_000_000, Unit: "buses (global fleet)", Source: "UITP + national transport authorities", DIDLabel: "vehicle"},
	{Domain: "bus_stop", App: "bus.etzhayyim.com", WorldTotal: 5_000_000, Unit: "bus stops (global)", Source: "GTFS + national transit databases", DIDLabel: "stop"},
	{Domain: "gas_station", App: "gas-station.etzhayyim.com", WorldTotal: 500_000, Unit: "gas/fuel stations (global)", Source: "IEA + national petroleum registries", DIDLabel: "station"},
	// Railway (additional)
	{Domain: "railway_vehicle", App: "railway.etzhayyim.com", WorldTotal: 1_000_000, Unit: "railway rolling stock (locomotives+coaches+wagons)", Source: "UIC + national railway operators", DIDLabel: "vehicle"},
	{Domain: "railway_route", App: "railway.etzhayyim.com", WorldTotal: 500_000, Unit: "railway routes/lines", Source: "UIC + OpenRailwayMap", DIDLabel: "route"},
	// Road Infrastructure (道路インフラ)
	{Domain: "douro_hyoushiki", App: "douro.etzhayyim.com", WorldTotal: 500_000_000, Unit: "road signs (global)", Source: "Vienna Convention + national road inventories", DIDLabel: "sign"},
	{Domain: "shingou", App: "douro.etzhayyim.com", WorldTotal: 10_000_000, Unit: "traffic signals/intersections", Source: "ITE + national traffic management", DIDLabel: "signal"},
	{Domain: "douro_hyouji", App: "douro.etzhayyim.com", WorldTotal: 1_000_000_000, Unit: "road markings (lanes/crosswalks/arrows)", Source: "national road maintenance surveys", DIDLabel: "marking"},
	{Domain: "guardrail", App: "douro.etzhayyim.com", WorldTotal: 200_000_000, Unit: "guardrails & barriers (km segments)", Source: "road safety infrastructure surveys", DIDLabel: "barrier"},
	{Domain: "gaitou", App: "douro.etzhayyim.com", WorldTotal: 300_000_000, Unit: "street lights (global)", Source: "IEA + smart city lighting reports", DIDLabel: "light"},
	{Domain: "ryoukinjo", App: "douro.etzhayyim.com", WorldTotal: 500_000, Unit: "toll gates/ETC points", Source: "IBTTA + national toll road operators", DIDLabel: "gate"},
	{Domain: "kyouryou", App: "douro.etzhayyim.com", WorldTotal: 10_000_000, Unit: "bridges (global)", Source: "ASCE + national bridge inventories (NBI)", DIDLabel: "bridge"},
	{Domain: "tunnel", App: "douro.etzhayyim.com", WorldTotal: 100_000, Unit: "road & rail tunnels", Source: "ITA + national tunnel registries", DIDLabel: "tunnel"},
	{Domain: "chuushajou", App: "chuushajou.etzhayyim.com", WorldTotal: 500_000_000, Unit: "parking spaces (global)", Source: "IPMI + national parking surveys", DIDLabel: "space"},
	// Real Estate & Property
	{Domain: "real_estate", App: "real-estate.etzhayyim.com", WorldTotal: 350_000_000, Unit: "real estate listings (global)", Source: "Zillow + Rightmove + global estimates", DIDLabel: "listing"},
	{Domain: "minpaku", App: "minpaku.etzhayyim.com", WorldTotal: 6_000_000, Unit: "vacation rentals (global)", Source: "Airbnb + Booking + 観光庁", DIDLabel: "listing"},
	{Domain: "property", App: "property.etzhayyim.com", WorldTotal: 3_500_000_000, Unit: "property parcels (global)", Source: "jinushi overlap — cadastre", DIDLabel: "parcel"},
	// Commerce & Marketplace
	{Domain: "okaimono", App: "okaimono.etzhayyim.com", WorldTotal: 30_000_000, Unit: "e-commerce merchants (global)", Source: "Shopify + Amazon + Rakuten estimates", DIDLabel: "merchant"},
	{Domain: "fleamarket", App: "fleamarket.etzhayyim.com", WorldTotal: 5_000_000, Unit: "C2C marketplace listings/day", Source: "Mercari + eBay + Craigslist estimates", DIDLabel: "listing"},
	{Domain: "commodities", App: "commodities.etzhayyim.com", WorldTotal: 5_500, Unit: "traded commodities", Source: "ICE + CME + commodity exchanges", DIDLabel: "commodity"},
	// Energy & Utilities
	{Domain: "denki", App: "denki.etzhayyim.com", WorldTotal: 60_000, Unit: "power plants (global)", Source: "Global Power Plant Database (WRI)", DIDLabel: "plant"},
	{Domain: "gas", App: "gas.etzhayyim.com", WorldTotal: 25_000, Unit: "gas facilities (global)", Source: "IEA + national energy agencies", DIDLabel: "facility"},
	{Domain: "water", App: "water.etzhayyim.com", WorldTotal: 300_000, Unit: "water utilities (global)", Source: "GWI + national water authorities", DIDLabel: "utility"},
	{Domain: "suido", App: "suido.etzhayyim.com", WorldTotal: 1_400, Unit: "water utilities (JP)", Source: "厚生労働省 水道事業体", DIDLabel: "utility"},
	{Domain: "energy", App: "energy.etzhayyim.com", WorldTotal: 5_000_000, Unit: "energy assets (global)", Source: "IRENA + IEA renewable + fossil assets", DIDLabel: "asset"},
	// IP & Intellectual Property (知的財産)
	{Domain: "patent", App: "patent.etzhayyim.com", WorldTotal: 200_000_000, Unit: "patent documents (global)", Source: "WIPO + USPTO + EPO + JPO", DIDLabel: "patent"},
	{Domain: "shohyo", App: "chizai.etzhayyim.com", WorldTotal: 70_000_000, Unit: "active trademark registrations", Source: "WIPO Madrid + national IP offices", DIDLabel: "trademark"},
	{Domain: "isho", App: "chizai.etzhayyim.com", WorldTotal: 20_000_000, Unit: "industrial design registrations", Source: "WIPO Hague + national IP offices", DIDLabel: "design"},
	{Domain: "chosakuken", App: "chizai.etzhayyim.com", WorldTotal: 100_000_000, Unit: "copyright registrations", Source: "USCO + national copyright offices", DIDLabel: "copyright"},
	{Domain: "jitsuyo_shinan", App: "chizai.etzhayyim.com", WorldTotal: 10_000_000, Unit: "utility model registrations", Source: "WIPO + JPO + CNIPA + KIPO + DPMA", DIDLabel: "utility_model"},
	{Domain: "shokubutsu_hinshu", App: "chizai.etzhayyim.com", WorldTotal: 200_000, Unit: "plant variety protections", Source: "UPOV + national PVP offices", DIDLabel: "variety"},
	{Domain: "chi_hyoji", App: "chizai.etzhayyim.com", WorldTotal: 10_000, Unit: "geographical indications", Source: "WIPO Lisbon + EU GI + national registries", DIDLabel: "gi"},
	{Domain: "eigyo_himitsu", App: "chizai.etzhayyim.com", WorldTotal: 50_000_000, Unit: "documented trade secrets", Source: "DTSA + EU Trade Secrets Directive estimates", DIDLabel: "secret"},
	// Manufacturing Process (製造プロセス)
	{Domain: "seizo_shiji", App: "seizo.etzhayyim.com", WorldTotal: 50_000_000_000, Unit: "work orders/production orders/yr", Source: "UNIDO + global manufacturing output estimates", DIDLabel: "order"},
	{Domain: "seizo_batch", App: "seizo.etzhayyim.com", WorldTotal: 10_000_000_000, Unit: "production batches/lots/yr", Source: "global manufacturing batch estimates", DIDLabel: "batch"},
	{Domain: "hinshitsu_kensa", App: "seizo.etzhayyim.com", WorldTotal: 100_000_000_000, Unit: "quality inspection records/yr", Source: "ISO 9001 + multiple inspections per batch", DIDLabel: "inspection"},
	{Domain: "bom", App: "seizo.etzhayyim.com", WorldTotal: 500_000_000, Unit: "bill of materials (unique product BOMs)", Source: "PLM/ERP industry estimates", DIDLabel: "bom"},
	{Domain: "koutei_recipe", App: "seizo.etzhayyim.com", WorldTotal: 50_000_000, Unit: "process recipes/formulations", Source: "ISA-88/ISA-95 batch control estimates", DIDLabel: "recipe"},
	{Domain: "kanagata", App: "seizo.etzhayyim.com", WorldTotal: 100_000_000, Unit: "molds/dies/jigs/tooling", Source: "ISTMA + global tooling industry", DIDLabel: "tooling"},
	{Domain: "kousei_kiroku", App: "seizo.etzhayyim.com", WorldTotal: 5_000_000_000, Unit: "calibration records/yr", Source: "ISO/IEC 17025 + metrology estimates", DIDLabel: "calibration"},
	{Domain: "koutei_step", App: "seizo.etzhayyim.com", WorldTotal: 1_000_000_000_000, Unit: "manufacturing process steps/yr", Source: "items × avg process steps", DIDLabel: "step"},
	// Pharmaceutical Process (製薬プロセス)
	{Domain: "gmp_batch", App: "seiyaku.etzhayyim.com", WorldTotal: 500_000_000, Unit: "GMP batch records/yr", Source: "FDA + EMA + PMDA cGMP manufacturing", DIDLabel: "batch"},
	{Domain: "yakuji_shinsei", App: "seiyaku.etzhayyim.com", WorldTotal: 500_000, Unit: "regulatory submissions (NDA/ANDA/MAA cumulative)", Source: "FDA + EMA + PMDA + national agencies", DIDLabel: "submission"},
	{Domain: "dmf", App: "seiyaku.etzhayyim.com", WorldTotal: 100_000, Unit: "Drug Master Files", Source: "FDA DMF + ASMF + national DMF registries", DIDLabel: "dmf"},
	{Domain: "yugai_jisho", App: "seiyaku.etzhayyim.com", WorldTotal: 20_000_000, Unit: "adverse event reports (cumulative)", Source: "FDA FAERS + EudraVigilance + VigiBase", DIDLabel: "report"},
	{Domain: "anteisei_shiken", App: "seiyaku.etzhayyim.com", WorldTotal: 5_000_000, Unit: "stability studies", Source: "ICH Q1A-Q1F guidelines + global pharma", DIDLabel: "study"},
	{Domain: "genyaku", App: "seiyaku.etzhayyim.com", WorldTotal: 10_000, Unit: "API manufacturing sources", Source: "FDA + CEP + national API registries", DIDLabel: "source"},
	// Raw Materials → Processing (原材料→加工)
	{Domain: "chukantai", App: "seizo.etzhayyim.com", WorldTotal: 5_000_000_000, Unit: "intermediate/semi-finished products/yr", Source: "UNIDO + global manufacturing value chain", DIDLabel: "intermediate"},
	{Domain: "hinshitsu_shomei", App: "seizo.etzhayyim.com", WorldTotal: 10_000_000_000, Unit: "certificates of analysis/conformance/yr", Source: "ISO 9001 + per-lot quality certification", DIDLabel: "certificate"},
	{Domain: "tsukan_shinkoku", App: "tsukan.etzhayyim.com", WorldTotal: 500_000_000, Unit: "customs declarations/yr", Source: "WCO + national customs agencies", DIDLabel: "declaration"},
	// Gambling & Racing
	{Domain: "keiba", App: "keiba.etzhayyim.com", WorldTotal: 25, Unit: "horse racing venues (JP)", Source: "JRA + NAR", DIDLabel: "venue"},
	{Domain: "casino", App: "casino.etzhayyim.com", WorldTotal: 6_500, Unit: "casinos (global)", Source: "UNLV + national gaming commissions", DIDLabel: "casino"},
	// Finance & Banking
	{Domain: "bank", App: "bank.etzhayyim.com", WorldTotal: 25_000, Unit: "banks (global)", Source: "BIS + national central banks", DIDLabel: "bank"},
	{Domain: "insurance", App: "insurance.etzhayyim.com", WorldTotal: 12_000, Unit: "insurance companies (global)", Source: "IAIS + national regulators", DIDLabel: "insurer"},
	{Domain: "securities", App: "securities.etzhayyim.com", WorldTotal: 3_000, Unit: "stock exchanges (global)", Source: "WFE + IOSCO", DIDLabel: "exchange"},
	{Domain: "loan", App: "loan.etzhayyim.com", WorldTotal: 500_000_000, Unit: "active loans (global)", Source: "World Bank + IMF credit estimates", DIDLabel: "loan"},
	// Contracts (契約)
	{Domain: "koyo_keiyaku", App: "keiyaku.etzhayyim.com", WorldTotal: 3_500_000_000, Unit: "employment contracts (global)", Source: "ILO World Employment 2025", DIDLabel: "contract"},
	{Domain: "chinshaku_keiyaku", App: "keiyaku.etzhayyim.com", WorldTotal: 1_500_000_000, Unit: "lease/rental contracts (residential+commercial)", Source: "UN-Habitat + CBRE estimates", DIDLabel: "contract"},
	{Domain: "riyo_kiyaku", App: "keiyaku.etzhayyim.com", WorldTotal: 10_000_000_000, Unit: "ToS/SaaS user agreements", Source: "user × service consent estimates", DIDLabel: "agreement"},
	{Domain: "baibai_keiyaku", App: "keiyaku.etzhayyim.com", WorldTotal: 5_000_000_000, Unit: "B2B purchase/sale contracts/yr", Source: "WTO + national trade statistics", DIDLabel: "contract"},
	{Domain: "license_keiyaku", App: "keiyaku.etzhayyim.com", WorldTotal: 500_000_000, Unit: "license agreements (software+IP+franchise)", Source: "BSA + WIPO + franchise registries", DIDLabel: "contract"},
	{Domain: "itaku_keiyaku", App: "keiyaku.etzhayyim.com", WorldTotal: 1_000_000_000, Unit: "outsourcing/service contracts", Source: "ILO non-standard employment + BPO estimates", DIDLabel: "contract"},
	{Domain: "nda", App: "keiyaku.etzhayyim.com", WorldTotal: 2_000_000_000, Unit: "NDA/confidentiality agreements", Source: "employment + deal-attached NDA estimates", DIDLabel: "contract"},
	{Domain: "konin_keiyaku", App: "keiyaku.etzhayyim.com", WorldTotal: 2_000_000_000, Unit: "marriage/partnership registrations (cumulative)", Source: "UN Demographic Yearbook", DIDLabel: "contract"},
	{Domain: "subscription", App: "keiyaku.etzhayyim.com", WorldTotal: 5_000_000_000, Unit: "subscription contracts (streaming+SaaS+telecom)", Source: "Zuora + industry reports", DIDLabel: "contract"},
	{Domain: "chotatsaku_keiyaku", App: "keiyaku.etzhayyim.com", WorldTotal: 50_000_000, Unit: "government procurement contracts/yr", Source: "OECD + WTO GPA + national registries", DIDLabel: "contract"},
	{Domain: "lease_doosan", App: "keiyaku.etzhayyim.com", WorldTotal: 500_000_000, Unit: "equipment/vehicle leases", Source: "Leaseurope + ALA + global fleet leasing", DIDLabel: "contract"},
	{Domain: "hosho_keiyaku", App: "keiyaku.etzhayyim.com", WorldTotal: 2_000_000_000, Unit: "warranty contracts (product+extended)", Source: "consumer electronics + automotive warranty estimates", DIDLabel: "contract"},
	// Government & Public
	{Domain: "cofog", App: "cofog.etzhayyim.com", WorldTotal: 6_000, Unit: "COFOG government functions", Source: "UN COFOG classification", DIDLabel: "function"},
	{Domain: "gov", App: "gov", WorldTotal: 500_000, Unit: "government agencies / ministries / public bodies (global)", Source: "CIA + national government directories + Wikidata agency/ministry targets", DIDLabel: "agency"},
	{Domain: "gov_admin_area", App: "gov", WorldTotal: 500_000, Unit: "administrative areas / municipalities / settlements in gov registry target", Source: "Wikidata administrative territorial entity + populated-place collector targets", DIDLabel: "admin_area"},
	{Domain: "government_fund", App: "fund.etzhayyim.com", WorldTotal: 25_000, Unit: "government / policy funds", Source: "national development bank + policy fund registries", DIDLabel: "fund"},
	{Domain: "investor_fund", App: "fund.etzhayyim.com", WorldTotal: 500_000, Unit: "fund investors / LP entities", Source: "Preqin + pension / endowment / SWF allocator universe", DIDLabel: "investor"},
	{Domain: "mutual_fund", App: "fund.etzhayyim.com", WorldTotal: 150_000, Unit: "mutual funds / UCITS", Source: "ICI + EFAMA + national fund registries", DIDLabel: "fund"},
	{Domain: "pension_fund", App: "fund.etzhayyim.com", WorldTotal: 350_000, Unit: "pension funds", Source: "OECD pensions + national retirement registries", DIDLabel: "fund"},
	{Domain: "private_fund", App: "fund.etzhayyim.com", WorldTotal: 300_000, Unit: "private funds", Source: "Preqin + SEC private fund filings + national PE/VC registries", DIDLabel: "fund"},
	{Domain: "public_fund", App: "public-fund.etzhayyim.com", WorldTotal: 150_000, Unit: "public funds / budgets", Source: "IMF GFS + national budgets", DIDLabel: "fund"},
	{Domain: "sovereign_fund", App: "fund.etzhayyim.com", WorldTotal: 250, Unit: "sovereign wealth / strategic funds", Source: "IFSWF + Global SWF", DIDLabel: "fund"},
	{Domain: "sanctions", App: "sanctions.etzhayyim.com", WorldTotal: 50_000, Unit: "sanctioned entities", Source: "OFAC + EU + UN sanctions lists", DIDLabel: "entity"},
	{Domain: "crypto_asset_freeze", App: "crypto-asset-freeze.etzhayyim.com", WorldTotal: 100_000, Unit: "crypto freeze incidents (cumulative LE escalations)", Source: "Chainalysis + TRM Labs + national LE bulletins", DIDLabel: "incident"},
	// Telecom & Network
	{Domain: "celler", App: "celler.etzhayyim.com", WorldTotal: 8_400_000_000, Unit: "mobile subscriptions (global)", Source: "ITU + GSMA", DIDLabel: "subscription"},
	{Domain: "telecom", App: "telecom.etzhayyim.com", WorldTotal: 4_000, Unit: "telecom operators (global)", Source: "ITU + GSMA Intelligence", DIDLabel: "operator"},
	{Domain: "phonenumber", App: "phonenumber.etzhayyim.com", WorldTotal: 15_000_000_000, Unit: "phone numbers (global)", Source: "ITU E.164 allocation", DIDLabel: "number"},
	// Food & Agriculture
	{Domain: "food", App: "food.etzhayyim.com", WorldTotal: 400_000, Unit: "food products (codex)", Source: "Codex Alimentarius + USDA FoodData", DIDLabel: "product"},
	{Domain: "farm", App: "farm.etzhayyim.com", WorldTotal: 570_000_000, Unit: "farms (global)", Source: "FAO World Census of Agriculture", DIDLabel: "farm"},
	{Domain: "oryori", App: "oryori.etzhayyim.com", WorldTotal: 5_000_000, Unit: "recipes (global)", Source: "global recipe databases estimate", DIDLabel: "recipe"},
	// Content & Media
	{Domain: "manga", App: "manga.etzhayyim.com", WorldTotal: 150_000, Unit: "manga titles", Source: "MAL + MangaUpdates + 出版DB", DIDLabel: "title"},
	{Domain: "narou", App: "narou.etzhayyim.com", WorldTotal: 1_000_000, Unit: "web novel titles (JP)", Source: "小説家になろう + カクヨム", DIDLabel: "title"},
	{Domain: "syosetsu", App: "syosetsu.etzhayyim.com", WorldTotal: 1_000_000, Unit: "light novel titles", Source: "小説家になろう + カクヨム + ebook platforms", DIDLabel: "title"},
	{Domain: "music", App: "music.etzhayyim.com", WorldTotal: 200_000_000, Unit: "music tracks", Source: "ISRC + Spotify + Apple Music", DIDLabel: "track"},
	{Domain: "douga", App: "douga.etzhayyim.com", WorldTotal: 1_000_000_000, Unit: "video content", Source: "YouTube + TikTok + NicoNico estimate", DIDLabel: "video"},
	{Domain: "drama", App: "drama.etzhayyim.com", WorldTotal: 100_000, Unit: "TV drama titles", Source: "IMDb + MyDramaList", DIDLabel: "title"},
	{Domain: "art", App: "art.etzhayyim.com", WorldTotal: 70_000_000, Unit: "artworks", Source: "Artsy + museum collection databases", DIDLabel: "artwork"},
	{Domain: "photos", App: "photos.etzhayyim.com", WorldTotal: 5_000_000_000_000, Unit: "photos (global annual)", Source: "Rise Above Research + InfoTrends", DIDLabel: "photo"},
	// Education & HR
	{Domain: "gakko", App: "gakko.etzhayyim.com", WorldTotal: 1_000_000, Unit: "schools & universities (global)", Source: "UNESCO + national education databases", DIDLabel: "school"},
	{Domain: "shigotoba", App: "shigotoba.etzhayyim.com", WorldTotal: 400_000_000, Unit: "business establishments (global)", Source: "ILO + national business registries", DIDLabel: "establishment"},
	// Security & Risk
	{Domain: "yabai", App: "yabai.etzhayyim.com", WorldTotal: 5_000_000, Unit: "risk intelligence records", Source: "FATF + AML databases + CTI feeds", DIDLabel: "record"},
	{Domain: "trust", App: "trust.etzhayyim.com", WorldTotal: 8_100_000_000, Unit: "trust-scored DIDs", Source: "UN World Population (all persons/agents)", DIDLabel: "did"},
	// Procurement & Delivery
	{Domain: "demae", App: "demae.etzhayyim.com", WorldTotal: 10_000_000, Unit: "delivery merchants (global)", Source: "UberEats + DoorDash + 出前館 estimates", DIDLabel: "merchant"},
	// Misc Domain
	{Domain: "shinshi", App: "shinshi.etzhayyim.com", WorldTotal: 10_000_000, Unit: "sensitive content items", Source: "content moderation platform estimates", DIDLabel: "item"},
	{Domain: "otoshimono", App: "otoshimono.etzhayyim.com", WorldTotal: 4_000_000, Unit: "lost items/yr (JP)", Source: "警察庁 遺失届統計", DIDLabel: "item"},
	{Domain: "tradition", App: "tradition.etzhayyim.com", WorldTotal: 50_000, Unit: "cultural traditions", Source: "UNESCO ICH + ethnographic databases", DIDLabel: "tradition"},
	{Domain: "i18n", App: "i18n.etzhayyim.com", WorldTotal: 7_168, Unit: "living languages", Source: "Ethnologue 27th edition", DIDLabel: "language"},
	{Domain: "handotai", App: "handotai.etzhayyim.com", WorldTotal: 100_000, Unit: "semiconductor products", Source: "WSTS + IC Insights", DIDLabel: "product"},
	{Domain: "pharma", App: "pharma.etzhayyim.com", WorldTotal: 350_000, Unit: "pharmaceutical products (global)", Source: "WHO Essential Medicines + FDA + EMA", DIDLabel: "product"},
	{Domain: "robot", App: "robot.etzhayyim.com", WorldTotal: 4_000_000, Unit: "industrial robots (global)", Source: "IFR World Robotics", DIDLabel: "robot"},
	{Domain: "mine", App: "mine.etzhayyim.com", WorldTotal: 35_000, Unit: "active mines (global)", Source: "S&P Global Market Intelligence", DIDLabel: "mine"},
	{Domain: "factory", App: "factory.etzhayyim.com", WorldTotal: 10_000_000, Unit: "factories (global)", Source: "UNIDO + national manufacturing surveys", DIDLabel: "factory"},
	{Domain: "warehouse", App: "warehouse.etzhayyim.com", WorldTotal: 500_000, Unit: "warehouses (global)", Source: "CBRE + JLL logistics reports", DIDLabel: "warehouse"},
	{Domain: "equipment", App: "equipment.etzhayyim.com", WorldTotal: 50_000_000, Unit: "industrial equipment assets", Source: "Ritchie Bros + IHS Markit", DIDLabel: "equipment"},
	// Buildings & Construction
	{Domain: "building_kouzoutai", App: "bim.etzhayyim.com", WorldTotal: 150_000_000_000, Unit: "structural members (columns/beams/walls/slabs/foundations)", Source: "1.5B buildings × ~100 avg structural elements", DIDLabel: "structure"},
	{Domain: "building_haikan", App: "bim.etzhayyim.com", WorldTotal: 300_000_000_000, Unit: "plumbing elements (pipes/fittings/valves/fixtures)", Source: "1.5B buildings × ~200 avg plumbing elements", DIDLabel: "pipe"},
	{Domain: "building_densen", App: "bim.etzhayyim.com", WorldTotal: 225_000_000_000, Unit: "electrical wiring (cables/circuits/panels)", Source: "1.5B buildings × ~150 avg electrical elements", DIDLabel: "wire"},
	{Domain: "building_tsushin", App: "bim.etzhayyim.com", WorldTotal: 100_000_000_000, Unit: "communication cabling (LAN/fiber/coax)", Source: "1B wired buildings × ~100 avg data cables", DIDLabel: "cable"},
	{Domain: "building_shoumei", App: "bim.etzhayyim.com", WorldTotal: 150_000_000_000, Unit: "fixtures (lights/outlets/switches)", Source: "1.5B buildings × ~100 avg fixtures", DIDLabel: "fixture"},
	{Domain: "building_kuuchou", App: "bim.etzhayyim.com", WorldTotal: 25_000_000_000, Unit: "HVAC elements (ducts/units/vents)", Source: "500M HVAC buildings × ~50 avg elements", DIDLabel: "hvac"},
	{Domain: "building_bouka", App: "bim.etzhayyim.com", WorldTotal: 30_000_000_000, Unit: "fire safety devices (sprinklers/detectors/extinguishers)", Source: "1.5B buildings × ~20 avg devices", DIDLabel: "fire_device"},
	{Domain: "building_setsubi", App: "bim.etzhayyim.com", WorldTotal: 15_000_000_000, Unit: "building equipment (boilers/elevators/pumps/generators)", Source: "1.5B buildings × ~10 avg equipment", DIDLabel: "equipment"},
	{Domain: "kenzai", App: "kenzai.etzhayyim.com", WorldTotal: 5_000_000, Unit: "construction material SKUs", Source: "JIS + ASTM + EN product catalogs", DIDLabel: "material"},
	{Domain: "kensetsu", App: "kensetsu.etzhayyim.com", WorldTotal: 10_000_000, Unit: "construction projects/yr (global)", Source: "GlobalData Construction + national permits", DIDLabel: "project"},
	// Parts & Components
	{Domain: "denshi_buhin", App: "denshi-buhin.etzhayyim.com", WorldTotal: 1_000_000_000, Unit: "electronic component part numbers", Source: "IEC + Digi-Key + Mouser + LCSC catalogs", DIDLabel: "part"},
	{Domain: "jidosha_buhin", App: "jidosha-buhin.etzhayyim.com", WorldTotal: 500_000_000, Unit: "automotive part numbers (OEM+aftermarket)", Source: "MEMA + TecDoc + OEM catalogs", DIDLabel: "part"},
	{Domain: "kikai_buhin", App: "kikai-buhin.etzhayyim.com", WorldTotal: 200_000_000, Unit: "mechanical parts (bearings/valves/pumps/fasteners)", Source: "ISO + industrial distributor catalogs", DIDLabel: "part"},
	// Materials
	{Domain: "sozai", App: "sozai.etzhayyim.com", WorldTotal: 200_000, Unit: "material grades (metals/polymers/ceramics/composites)", Source: "MatWeb + ASTM + JIS + Granta", DIDLabel: "grade"},
	// Consumer Products
	{Domain: "shohin", App: "shohin.etzhayyim.com", WorldTotal: 2_000_000_000, Unit: "consumer products (incl non-GTIN)", Source: "GS1 + non-barcoded product estimates", DIDLabel: "product"},
	{Domain: "kagu", App: "kagu.etzhayyim.com", WorldTotal: 50_000_000, Unit: "furniture product SKUs", Source: "CSIL + global furniture manufacturer catalogs", DIDLabel: "product"},
	{Domain: "apparel", App: "apparel.etzhayyim.com", WorldTotal: 100_000_000, Unit: "apparel SKUs (size×color)", Source: "Euromonitor + fashion industry estimates", DIDLabel: "sku"},
	// IoT & Network Devices
	{Domain: "iot", App: "iot.etzhayyim.com", WorldTotal: 18_000_000_000, Unit: "IoT devices (global)", Source: "IoT Analytics 2025", DIDLabel: "device"},
	{Domain: "mac_address", App: "mac.etzhayyim.com", WorldTotal: 20_000_000_000, Unit: "MAC addresses (global)", Source: "IEEE OUI registry + device estimates", DIDLabel: "mac"},
	{Domain: "ipv6", App: "ipaddress.etzhayyim.com", WorldTotal: 10_000_000_000, Unit: "IPv6 active addresses", Source: "APNIC + Google IPv6 adoption", DIDLabel: "ipv6"},
	{Domain: "ip_scan", App: "ipaddress.etzhayyim.com", WorldTotal: 4_294_967_296, Unit: "IPv4 scan results (port/service/software)", Source: "IANA IPv4 space (Shodan/Censys scale)", DIDLabel: "scan_result"},
	// Personal Identity & Credentials
	{Domain: "email", App: "gmail.etzhayyim.com", WorldTotal: 4_500_000_000, Unit: "email accounts (global)", Source: "Radicati Email Statistics 2025", DIDLabel: "account"},
	{Domain: "sns_account", App: "sns.etzhayyim.com", WorldTotal: 5_000_000_000, Unit: "social media accounts (global)", Source: "DataReportal + platform reports", DIDLabel: "account"},
	{Domain: "passport", App: "passport.etzhayyim.com", WorldTotal: 1_500_000_000, Unit: "active passports (global)", Source: "ICAO + national immigration agencies", DIDLabel: "passport"},
	{Domain: "menkyo", App: "menkyo.etzhayyim.com", WorldTotal: 1_500_000_000, Unit: "driver's licenses (global)", Source: "IRTAD + national DMV registries", DIDLabel: "license"},
	{Domain: "creditcard", App: "creditcard.etzhayyim.com", WorldTotal: 1_200_000_000, Unit: "credit cards in circulation", Source: "Nilson Report 2025", DIDLabel: "card"},
	// Financial Accounts
	{Domain: "bank_account", App: "bank.etzhayyim.com", WorldTotal: 10_000_000_000, Unit: "bank accounts (global)", Source: "World Bank Findex + BIS", DIDLabel: "account"},
	{Domain: "insurance_contract", App: "insurance.etzhayyim.com", WorldTotal: 3_000_000_000, Unit: "insurance policies (global)", Source: "Swiss Re sigma + IAIS", DIDLabel: "policy"},
	// Healthcare
	{Domain: "iryo", App: "iryo.etzhayyim.com", WorldTotal: 5_000_000_000, Unit: "medical patient records (global)", Source: "WHO + national health registries", DIDLabel: "patient"},
	// Logistics
	{Domain: "container", App: "container.etzhayyim.com", WorldTotal: 50_000_000, Unit: "shipping containers (global)", Source: "BIC + World Shipping Council", DIDLabel: "container"},
	// Space & Aerospace
	{Domain: "satellite", App: "satellite.etzhayyim.com", WorldTotal: 10_000, Unit: "active satellites", Source: "UCS Satellite Database 2025", DIDLabel: "satellite"},
	// Celestial Bodies (天体)
	{Domain: "tentai_star", App: "tentai.etzhayyim.com", WorldTotal: 1_800_000_000, Unit: "catalogued stars", Source: "ESA Gaia DR3", DIDLabel: "star"},
	{Domain: "tentai_exoplanet", App: "tentai.etzhayyim.com", WorldTotal: 5_700, Unit: "confirmed exoplanets", Source: "NASA Exoplanet Archive", DIDLabel: "exoplanet"},
	{Domain: "tentai_asteroid", App: "tentai.etzhayyim.com", WorldTotal: 1_300_000, Unit: "known asteroids", Source: "MPC (Minor Planet Center)", DIDLabel: "asteroid"},
	{Domain: "tentai_galaxy", App: "tentai.etzhayyim.com", WorldTotal: 2_000_000, Unit: "catalogued galaxies", Source: "NASA/IPAC Extragalactic Database", DIDLabel: "galaxy"},
	{Domain: "tentai_comet", App: "tentai.etzhayyim.com", WorldTotal: 4_000, Unit: "known comets", Source: "JPL Small-Body Database", DIDLabel: "comet"},
	{Domain: "tentai_moon", App: "tentai.etzhayyim.com", WorldTotal: 300, Unit: "known natural satellites", Source: "IAU + JPL Solar System Dynamics", DIDLabel: "moon"},
	// Transactions & Flow (トランザクション)
	{Domain: "invoice", App: "invoice.etzhayyim.com", WorldTotal: 500_000_000_000, Unit: "invoices/yr (global)", Source: "Billentis + Koch e-invoicing estimates", DIDLabel: "invoice"},
	{Domain: "receipt", App: "receipt.etzhayyim.com", WorldTotal: 500_000_000_000, Unit: "receipts/yr (global POS)", Source: "NRF + global POS transaction estimates", DIDLabel: "receipt"},
	{Domain: "kessai", App: "kessai.etzhayyim.com", WorldTotal: 1_000_000_000_000, Unit: "payment transactions/yr", Source: "BIS CPMI + Nilson Report", DIDLabel: "transaction"},
	{Domain: "nimotsu", App: "nimotsu.etzhayyim.com", WorldTotal: 200_000_000_000, Unit: "parcels/shipments/yr", Source: "Pitney Bowes Parcel Shipping Index 2025", DIDLabel: "parcel"},
	// Credentials & Certificates (資格・学歴)
	{Domain: "gakui", App: "gakureki.etzhayyim.com", WorldTotal: 500_000_000, Unit: "academic degrees (cumulative)", Source: "UNESCO + national education statistics", DIDLabel: "degree"},
	{Domain: "shikaku", App: "shikaku.etzhayyim.com", WorldTotal: 2_000_000_000, Unit: "professional certifications/licenses", Source: "ILO + national certification bodies", DIDLabel: "certification"},
	{Domain: "gakujutsu_ronbun", App: "ronbun.etzhayyim.com", WorldTotal: 200_000_000, Unit: "academic papers", Source: "Semantic Scholar + PubMed + Crossref", DIDLabel: "paper"},
	{Domain: "gakusei", App: "gakko.etzhayyim.com", WorldTotal: 1_500_000_000, Unit: "enrolled students (global)", Source: "UNESCO Institute for Statistics 2025", DIDLabel: "student"},
	// Administrative Records (行政記録)
	{Domain: "shussei_todoke", App: "koseki.etzhayyim.com", WorldTotal: 3_000_000_000, Unit: "birth/death certificates (cumulative active)", Source: "UN Vital Statistics + national registries", DIDLabel: "certificate"},
	{Domain: "visa", App: "visa.etzhayyim.com", WorldTotal: 200_000_000, Unit: "visas issued/yr", Source: "UNWTO + national immigration agencies", DIDLabel: "visa"},
	{Domain: "eigyo_kyoka", App: "kyoka.etzhayyim.com", WorldTotal: 500_000_000, Unit: "business licenses/permits (global)", Source: "World Bank Doing Business + national registries", DIDLabel: "license"},
	{Domain: "nozei_shinkoku", App: "zeimu.etzhayyim.com", WorldTotal: 1_000_000_000, Unit: "tax returns/yr (global)", Source: "OECD Tax Administration + national revenue agencies", DIDLabel: "return"},
	// Healthcare Details (医療詳細)
	{Domain: "shohousen", App: "iryo.etzhayyim.com", WorldTotal: 5_000_000_000, Unit: "prescriptions/yr (global)", Source: "IQVIA + WHO Essential Medicines", DIDLabel: "prescription"},
	{Domain: "rinshou_shiken", App: "iryo.etzhayyim.com", WorldTotal: 500_000, Unit: "clinical trials (registered)", Source: "ClinicalTrials.gov + WHO ICTRP", DIDLabel: "trial"},
	{Domain: "iryo_shisetsu", App: "iryo.etzhayyim.com", WorldTotal: 1_000_000, Unit: "hospitals & clinics (global)", Source: "WHO Global Health Observatory", DIDLabel: "facility"},
	{Domain: "icd_shikkan", App: "iryo.etzhayyim.com", WorldTotal: 70_000, Unit: "ICD-11 disease codes", Source: "WHO ICD-11", DIDLabel: "disease"},
	// Events (イベント)
	{Domain: "sports_shiai", App: "sports.etzhayyim.com", WorldTotal: 10_000_000, Unit: "sports matches/yr (global)", Source: "FIFA + IOC + national sports federations", DIDLabel: "match"},
	{Domain: "live_event", App: "event.etzhayyim.com", WorldTotal: 50_000_000, Unit: "live events/yr (concerts/exhibitions/conferences)", Source: "Pollstar + UFI + ICCA", DIDLabel: "event"},
	{Domain: "jiko", App: "jiko.etzhayyim.com", WorldTotal: 100_000_000, Unit: "accidents & incidents/yr", Source: "WHO + ILO + national safety agencies", DIDLabel: "incident"},
	{Domain: "saigai", App: "saigai.etzhayyim.com", WorldTotal: 1_000, Unit: "significant natural disasters/yr", Source: "EM-DAT (CRED)", DIDLabel: "disaster"},
	{Domain: "hanzai", App: "hanzai.etzhayyim.com", WorldTotal: 500_000_000, Unit: "crime reports/yr (global)", Source: "UNODC + national crime statistics", DIDLabel: "crime"},
	{Domain: "senkyo", App: "senkyo.etzhayyim.com", WorldTotal: 1_000, Unit: "elections/yr (national+regional)", Source: "IDEA + national election commissions", DIDLabel: "election"},
	// Digital Assets (デジタル資産)
	{Domain: "git_repo", App: "repo.etzhayyim.com", WorldTotal: 500_000_000, Unit: "software repositories", Source: "GitHub + GitLab + Bitbucket + SourceForge", DIDLabel: "repo"},
	{Domain: "api_endpoint", App: "api.etzhayyim.com", WorldTotal: 1_000_000_000, Unit: "public API endpoints", Source: "RapidAPI + ProgrammableWeb + OpenAPI registries", DIDLabel: "endpoint"},
	{Domain: "nft", App: "blockchain.etzhayyim.com", WorldTotal: 100_000_000, Unit: "minted NFTs", Source: "NFTScan + OpenSea + on-chain data", DIDLabel: "nft"},
	// Nature & Environment (自然・環境)
	{Domain: "kasen", App: "shizen.etzhayyim.com", WorldTotal: 250_000, Unit: "named rivers & water bodies", Source: "GRanD + HydroSHEDS + national registries", DIDLabel: "river"},
	{Domain: "hogoku", App: "shizen.etzhayyim.com", WorldTotal: 250_000, Unit: "protected areas", Source: "UNEP-WCMC WDPA", DIDLabel: "area"},
	{Domain: "kishou", App: "shizen.etzhayyim.com", WorldTotal: 100_000, Unit: "weather stations", Source: "WMO Global Observing System", DIDLabel: "station"},
	{Domain: "seitaikei", App: "shizen.etzhayyim.com", WorldTotal: 800, Unit: "terrestrial ecoregions", Source: "WWF + IUCN Global Ecosystem Typology", DIDLabel: "ecoregion"},
	// Social Organizations (社会組織)
	{Domain: "npo", App: "npo.etzhayyim.com", WorldTotal: 10_000_000, Unit: "NPOs & NGOs (global)", Source: "UIA + national NPO registries", DIDLabel: "org"},
	{Domain: "shukyo_shisetsu", App: "religious.etzhayyim.com", WorldTotal: 5_000_000, Unit: "religious institutions (temples/churches/mosques)", Source: "Pew Research + ARDA + national registries", DIDLabel: "institution"},
	{Domain: "sports_club", App: "sports.etzhayyim.com", WorldTotal: 5_000_000, Unit: "sports clubs & teams", Source: "FIFA + IOC + national sports registries", DIDLabel: "club"},
	{Domain: "toshokan", App: "toshokan.etzhayyim.com", WorldTotal: 400_000, Unit: "libraries (global)", Source: "IFLA World Report", DIDLabel: "library"},
	{Domain: "hakubutsukan", App: "hakubutsukan.etzhayyim.com", WorldTotal: 100_000, Unit: "museums & galleries (global)", Source: "ICOM + UNESCO", DIDLabel: "museum"},
	// Biology & Genomics (生物学)
	{Domain: "genome", App: "genome.etzhayyim.com", WorldTotal: 1_000_000_000, Unit: "sequenced genomes", Source: "GenBank + ENA + DDBJ + clinical genomics", DIDLabel: "genome"},
	{Domain: "tanpakushitsu", App: "genome.etzhayyim.com", WorldTotal: 200_000_000, Unit: "protein structures", Source: "AlphaFold DB + PDB + UniProt", DIDLabel: "protein"},
	// Financial Instruments (金融商品詳細)
	{Domain: "derivative", App: "derivative.etzhayyim.com", WorldTotal: 1_000_000_000, Unit: "derivatives contracts (OTC+exchange)", Source: "BIS OTC statistics + WFE", DIDLabel: "contract"},
	{Domain: "boueki_kinyu", App: "boueki.etzhayyim.com", WorldTotal: 50_000_000, Unit: "trade finance instruments/yr (LC/BG)", Source: "ICC Trade Register + ADB", DIDLabel: "instrument"},
	// Serialized Items (個品シリアル番号)
	{Domain: "sgtin", App: "serial.etzhayyim.com", WorldTotal: 1_000_000_000_000, Unit: "serialized products (SGTIN/EPC cumulative)", Source: "GS1 EPCglobal + RAIN RFID Alliance", DIDLabel: "item"},
	{Domain: "imei", App: "serial.etzhayyim.com", WorldTotal: 20_000_000_000, Unit: "mobile devices (IMEI cumulative)", Source: "GSMA IMEI Database", DIDLabel: "device"},
	{Domain: "iyakuhin_serial", App: "serial.etzhayyim.com", WorldTotal: 30_000_000_000, Unit: "serialized drug packages/yr", Source: "FDA DSCSA + EU FMD + national track-and-trace", DIDLabel: "package"},
	{Domain: "udi", App: "serial.etzhayyim.com", WorldTotal: 2_000_000_000, Unit: "medical devices (UDI)", Source: "FDA GUDID + EU Eudamed", DIDLabel: "device"},
	{Domain: "tire_serial", App: "serial.etzhayyim.com", WorldTotal: 10_000_000_000, Unit: "tires in service (DOT/RFID)", Source: "USTMA + ETRMA + global tire production", DIDLabel: "tire"},
	{Domain: "battery_passport", App: "serial.etzhayyim.com", WorldTotal: 15_000_000_000, Unit: "batteries/yr (EU Battery Passport)", Source: "EU Battery Regulation + IEA Global EV Outlook", DIDLabel: "battery"},
	{Domain: "danyaku", App: "serial.etzhayyim.com", WorldTotal: 15_000_000_000, Unit: "ammunition rounds/yr", Source: "SIPRI + national defense procurement", DIDLabel: "round"},
	{Domain: "apparel_rfid", App: "serial.etzhayyim.com", WorldTotal: 20_000_000_000, Unit: "RFID-tagged apparel items/yr", Source: "RAIN RFID Alliance + Avery Dennison", DIDLabel: "item"},
	{Domain: "shokuhin_lot", App: "serial.etzhayyim.com", WorldTotal: 1_000_000_000_000, Unit: "food lot/batch units/yr", Source: "GS1 SSCC + FSMA + EU food traceability", DIDLabel: "lot"},
	{Domain: "kokyuhin_serial", App: "serial.etzhayyim.com", WorldTotal: 500_000_000, Unit: "luxury goods (watches/bags/jewelry serial)", Source: "Fondation de la Haute Horlogerie + brand registries", DIDLabel: "item"},
	{Domain: "kouku_buhin_serial", App: "serial.etzhayyim.com", WorldTotal: 5_000_000_000, Unit: "aerospace parts (P/N+S/N)", Source: "IATA + ATA Spec 2000 + FAA PMA", DIDLabel: "part"},
	{Domain: "juki_serial", App: "serial.etzhayyim.com", WorldTotal: 1_000_000_000, Unit: "firearms (serial number cumulative)", Source: "Small Arms Survey + national registries", DIDLabel: "firearm"},
	{Domain: "solar_serial", App: "serial.etzhayyim.com", WorldTotal: 500_000_000, Unit: "installed solar panels", Source: "IRENA + IEA PVPS", DIDLabel: "panel"},
	{Domain: "megane", App: "serial.etzhayyim.com", WorldTotal: 2_000_000_000, Unit: "eyewear/contact lenses/yr", Source: "Essilor + WHO vision report", DIDLabel: "item"},
	// Gap Fill: Human & Society (人間・社会)
	{Domain: "setai", App: "setai.etzhayyim.com", WorldTotal: 2_000_000_000, Unit: "households (global)", Source: "UN Demographic Yearbook + national census", DIDLabel: "household"},
	{Domain: "life_event", App: "life-event.etzhayyim.com", WorldTotal: 5_000_000_000, Unit: "life events/yr (relocation/employment/retirement)", Source: "UN + ILO + national vital statistics", DIDLabel: "event"},
	// Gap Fill: Law & Governance (法・ガバナンス)
	{Domain: "hourei", App: "hourei.etzhayyim.com", WorldTotal: 10_000_000, Unit: "statutes & regulations (global)", Source: "N-Lex + national law databases (195 jurisdictions)", DIDLabel: "statute"},
	{Domain: "soshou_stage", App: "hanrei.etzhayyim.com", WorldTotal: 500_000_000, Unit: "litigation stages (filing→hearing→judgment)", Source: "national court statistics + CEPEJ", DIDLabel: "stage"},
	{Domain: "kisei_todoke", App: "kisei.etzhayyim.com", WorldTotal: 1_000_000_000, Unit: "regulatory filings/compliance reports/yr", Source: "OECD RIA + national regulatory agencies", DIDLabel: "filing"},
	// Gap Fill: Finance (金融)
	{Domain: "kabushiki_chumon", App: "torihiki.etzhayyim.com", WorldTotal: 100_000_000_000, Unit: "stock/futures orders/yr", Source: "WFE + national exchange statistics", DIDLabel: "order"},
	{Domain: "shinsa_process", App: "shinsa.etzhayyim.com", WorldTotal: 2_000_000_000, Unit: "underwriting/credit assessments/yr", Source: "BIS + insurance + lending industry", DIDLabel: "assessment"},
	// Gap Fill: Real Estate (不動産)
	{Domain: "fudosan_torihiki", App: "fudosan.etzhayyim.com", WorldTotal: 100_000_000, Unit: "property transactions/title transfers/yr", Source: "national land registries + RICS", DIDLabel: "transaction"},
	{Domain: "fudosan_kaisha", App: "fudosan.etzhayyim.com", WorldTotal: 5_000_000, Unit: "real estate agencies/property managers", Source: "NAR + RICS + national registries", DIDLabel: "agency"},
	{Domain: "tatemono_tenken", App: "bim.etzhayyim.com", WorldTotal: 500_000_000, Unit: "building inspections/statutory checks/yr", Source: "ICC + national building codes", DIDLabel: "inspection"},
	// Gap Fill: Transport (交通)
	{Domain: "unkou_kiroku", App: "unkou.etzhayyim.com", WorldTotal: 500_000_000, Unit: "flight/voyage/train service records/yr", Source: "ICAO + IMO + UIC statistics", DIDLabel: "service"},
	{Domain: "seibi_kiroku", App: "seibi.etzhayyim.com", WorldTotal: 5_000_000_000, Unit: "vehicle maintenance/inspection records/yr", Source: "OICA + national MOT/shaken registries", DIDLabel: "record"},
	{Domain: "koutsuu_ihan", App: "koutsuu.etzhayyim.com", WorldTotal: 500_000_000, Unit: "traffic violations/tickets/yr", Source: "IRTAD + national police statistics", DIDLabel: "violation"},
	// Gap Fill: IT & Digital (情報)
	{Domain: "data_center", App: "dc.etzhayyim.com", WorldTotal: 10_000, Unit: "data centers (global)", Source: "Cloudscene + DataCenterMap", DIDLabel: "dc"},
	{Domain: "db_schema", App: "db.etzhayyim.com", WorldTotal: 5_000_000_000, Unit: "database tables/collections (global)", Source: "DB-Engines + cloud DB instance estimates", DIDLabel: "table"},
	{Domain: "cicd_pipeline", App: "cicd.etzhayyim.com", WorldTotal: 1_000_000_000, Unit: "CI/CD pipelines", Source: "GitHub Actions + GitLab CI + Jenkins estimates", DIDLabel: "pipeline"},
	// Gap Fill: Healthcare (医療)
	{Domain: "yobou_sesshu", App: "iryo.etzhayyim.com", WorldTotal: 15_000_000_000, Unit: "vaccination records (cumulative doses)", Source: "WHO + Our World in Data", DIDLabel: "dose"},
	{Domain: "shujutsu_kiroku", App: "iryo.etzhayyim.com", WorldTotal: 300_000_000, Unit: "surgical procedures/yr", Source: "WHO + Lancet Commission on Global Surgery", DIDLabel: "procedure"},
	{Domain: "iryo_seikyu", App: "iryo.etzhayyim.com", WorldTotal: 10_000_000_000, Unit: "medical claims/receipts/yr", Source: "CMS + national health insurance systems", DIDLabel: "claim"},
	// Gap Fill: Agriculture (農業)
	{Domain: "kachiku", App: "kachiku.etzhayyim.com", WorldTotal: 30_000_000_000, Unit: "livestock individuals (poultry+swine+cattle+sheep)", Source: "FAO FAOSTAT 2025", DIDLabel: "animal"},
	{Domain: "hinshu_shushi", App: "hinshu.etzhayyim.com", WorldTotal: 500_000, Unit: "registered crop/seed varieties", Source: "UPOV + national variety registries", DIDLabel: "variety"},
	{Domain: "noukyou", App: "nougyou.etzhayyim.com", WorldTotal: 5_000_000, Unit: "agricultural cooperatives/corporations", Source: "ICA + FAO + national registries", DIDLabel: "coop"},
	{Domain: "shukaku_cycle", App: "nougyou.etzhayyim.com", WorldTotal: 5_000_000_000, Unit: "harvest/cultivation cycles/yr", Source: "FAO + farm × crop rotation", DIDLabel: "cycle"},
	{Domain: "shokuhin_anzen", App: "shokuhin-anzen.etzhayyim.com", WorldTotal: 100_000_000, Unit: "food safety inspections/yr", Source: "Codex + GFSI + national food safety agencies", DIDLabel: "inspection"},
	// Gap Fill: Energy (エネルギー)
	{Domain: "souden_infra", App: "souden.etzhayyim.com", WorldTotal: 500_000_000, Unit: "grid infrastructure (transformers/substations/smart meters)", Source: "IEA + national grid operators", DIDLabel: "asset"},
	{Domain: "energy_consumption", App: "energy.etzhayyim.com", WorldTotal: 10_000_000_000, Unit: "energy consumption/billing records/yr", Source: "IEA + national utility billing", DIDLabel: "record"},
	{Domain: "ev_charger", App: "ev.etzhayyim.com", WorldTotal: 5_000_000, Unit: "EV charging stations (global)", Source: "IEA GEVO + national EV registries", DIDLabel: "station"},
	{Domain: "carbon_credit", App: "carbon.etzhayyim.com", WorldTotal: 500_000_000, Unit: "carbon credits (tCO2e traded cumulative)", Source: "Verra + Gold Standard + EU ETS", DIDLabel: "credit"},
	// Gap Fill: Education (教育)
	{Domain: "koza", App: "gakko.etzhayyim.com", WorldTotal: 50_000_000, Unit: "courses/curricula (incl MOOCs)", Source: "Class Central + UNESCO + national education databases", DIDLabel: "course"},
	{Domain: "shiken_seiseki", App: "gakko.etzhayyim.com", WorldTotal: 5_000_000_000, Unit: "exam/grade records/yr", Source: "UNESCO + national examination boards", DIDLabel: "record"},
	// Gap Fill: Space (宇宙)
	{Domain: "uchu_mission", App: "uchu.etzhayyim.com", WorldTotal: 200, Unit: "space launches/yr", Source: "FAA AST + Space Launch Report", DIDLabel: "launch"},
	{Domain: "uchu_debris", App: "uchu.etzhayyim.com", WorldTotal: 30_000, Unit: "tracked orbital debris", Source: "US Space Surveillance Network + ESA", DIDLabel: "debris"},
	// Gap Fill: JP→Global expansion
	{Domain: "kaigo_global", App: "kaigo.etzhayyim.com", WorldTotal: 2_000_000, Unit: "elderly care facilities (global)", Source: "WHO + OECD Health at a Glance", DIDLabel: "facility"},
	{Domain: "festival_global", App: "festival.etzhayyim.com", WorldTotal: 5_000_000, Unit: "festivals & cultural events (global)", Source: "UNESCO + national tourism boards", DIDLabel: "festival"},
	{Domain: "keiba_global", App: "keiba.etzhayyim.com", WorldTotal: 500, Unit: "horse racing venues (global)", Source: "IFHA + national racing authorities", DIDLabel: "venue"},
	// Asset Lifecycle & End-of-Life (資産ライフサイクル・廃棄・リサイクル)
	{Domain: "shisan_lifecycle", App: "shisan.etzhayyim.com", WorldTotal: 50_000_000_000, Unit: "asset lifecycle records (acquire→operate→maintain→dispose)", Source: "ISO 55000 + global fixed asset estimates", DIDLabel: "record"},
	{Domain: "taiyou_nensu", App: "shisan.etzhayyim.com", WorldTotal: 100_000_000, Unit: "asset type × useful life entries", Source: "IRS Publication 946 + national tax depreciation tables", DIDLabel: "entry"},
	// Waste Collection (ごみ収集)
	{Domain: "gomi_shuushuu", App: "haikibutsu.etzhayyim.com", WorldTotal: 500_000_000, Unit: "waste collection points/bins (global)", Source: "ISWA + municipal waste management surveys", DIDLabel: "point"},
	{Domain: "gomi_route", App: "haikibutsu.etzhayyim.com", WorldTotal: 5_000_000, Unit: "waste collection routes", Source: "municipal fleet management estimates", DIDLabel: "route"},
	{Domain: "ippan_haikibutsu", App: "haikibutsu.etzhayyim.com", WorldTotal: 2_000_000_000, Unit: "MSW tons/yr (municipal solid waste)", Source: "World Bank What a Waste 2.0", DIDLabel: "ton"},
	{Domain: "sangyo_haikibutsu", App: "haikibutsu.etzhayyim.com", WorldTotal: 10_000_000_000, Unit: "industrial waste tons/yr", Source: "UNEP + national EPA statistics", DIDLabel: "ton"},
	{Domain: "kiken_haikibutsu", App: "haikibutsu.etzhayyim.com", WorldTotal: 500_000_000, Unit: "hazardous waste tons/yr (chemical/medical/radioactive)", Source: "Basel Convention + UNEP + national hazmat registries", DIDLabel: "ton"},
	{Domain: "e_waste", App: "haikibutsu.etzhayyim.com", WorldTotal: 50_000_000_000, Unit: "e-waste items/yr (WEEE individual units)", Source: "UNITAR Global E-waste Monitor 2024", DIDLabel: "item"},
	{Domain: "haiki_manifest", App: "haikibutsu.etzhayyim.com", WorldTotal: 5_000_000_000, Unit: "waste disposal manifests/yr", Source: "Basel Convention + national manifest systems", DIDLabel: "manifest"},
	// Disposal & Dumping (投棄・処分)
	{Domain: "fuhou_touki", App: "haikibutsu.etzhayyim.com", WorldTotal: 10_000_000, Unit: "illegal dumping sites/yr", Source: "UNEP + national environmental enforcement", DIDLabel: "site"},
	{Domain: "kaku_haikibutsu", App: "haikibutsu.etzhayyim.com", WorldTotal: 500_000, Unit: "nuclear waste containers/casks", Source: "IAEA + national nuclear regulators (NRC/NRA)", DIDLabel: "container"},
	// Recycling (リサイクル)
	{Domain: "recycle_shisetsu", App: "recycle.etzhayyim.com", WorldTotal: 500_000, Unit: "recycling facilities (global)", Source: "ISWA + BIR + national recycling registries", DIDLabel: "facility"},
	{Domain: "recycle_flow", App: "recycle.etzhayyim.com", WorldTotal: 1_000_000_000, Unit: "recycled material flow tons/yr", Source: "BIR + ISRI + national recycling statistics", DIDLabel: "ton"},
	{Domain: "recycle_rate", App: "recycle.etzhayyim.com", WorldTotal: 200, Unit: "national recycling rate records (195 countries × material)", Source: "OECD + World Bank + national EPA", DIDLabel: "record"},
	// Landfill & Incineration (埋立・焼却)
	{Domain: "umetatchi", App: "haikibutsu.etzhayyim.com", WorldTotal: 500_000, Unit: "landfill sites (global)", Source: "ISWA + national waste management registries", DIDLabel: "site"},
	{Domain: "shoukyaku", App: "haikibutsu.etzhayyim.com", WorldTotal: 2_000, Unit: "waste-to-energy/incineration plants", Source: "ISWA + CEWEP + national WtE registries", DIDLabel: "plant"},
	// End-of-Life Vehicles & Buildings (廃車・解体)
	{Domain: "haisha", App: "haikibutsu.etzhayyim.com", WorldTotal: 50_000_000, Unit: "end-of-life vehicles/yr (ELV)", Source: "EU ELV Directive + national scrappage statistics", DIDLabel: "vehicle"},
	{Domain: "kaitai_kouji", App: "haikibutsu.etzhayyim.com", WorldTotal: 5_000_000, Unit: "building demolition projects/yr", Source: "national construction statistics + NDA", DIDLabel: "project"},
	{Domain: "senpaku_kaitai", App: "haikibutsu.etzhayyim.com", WorldTotal: 1_000, Unit: "ship recycling/breaking/yr", Source: "Hong Kong Convention + NGO Shipbreaking Platform", DIDLabel: "vessel"},
	// Software & Apps — End-User (エンドユーザー向けアプリ・ソフトウェア)
	{Domain: "ios_app", App: "software.etzhayyim.com", WorldTotal: 2_000_000, Unit: "iOS apps (App Store)", Source: "Apple App Store + Sensor Tower", DIDLabel: "app"},
	{Domain: "android_app", App: "software.etzhayyim.com", WorldTotal: 3_500_000, Unit: "Android apps (Google Play)", Source: "Google Play + AppBrain", DIDLabel: "app"},
	{Domain: "windows_app", App: "software.etzhayyim.com", WorldTotal: 500_000, Unit: "Windows apps (Microsoft Store + MSI)", Source: "Microsoft Store + Chocolatey + winget", DIDLabel: "app"},
	{Domain: "macos_app", App: "software.etzhayyim.com", WorldTotal: 100_000, Unit: "macOS apps (Mac App Store + DMG)", Source: "Apple Mac App Store + Homebrew Cask", DIDLabel: "app"},
	{Domain: "linux_package", App: "software.etzhayyim.com", WorldTotal: 200_000, Unit: "Linux packages (apt/yum/pacman)", Source: "Debian + Fedora + Arch package counts", DIDLabel: "package"},
	{Domain: "browser_extension", App: "software.etzhayyim.com", WorldTotal: 500_000, Unit: "browser extensions (Chrome/Firefox/Edge)", Source: "Chrome Web Store + AMO + Edge Add-ons", DIDLabel: "extension"},
	{Domain: "desktop_software", App: "software.etzhayyim.com", WorldTotal: 5_000_000, Unit: "desktop software titles (non-store)", Source: "Download.com + Softpedia + industry estimates", DIDLabel: "software"},
	{Domain: "saas_service", App: "software.etzhayyim.com", WorldTotal: 30_000, Unit: "SaaS services (B2B+B2C)", Source: "G2 + Capterra + SaaSworthy", DIDLabel: "service"},
	{Domain: "game_store", App: "software.etzhayyim.com", WorldTotal: 1_000_000, Unit: "game titles (digital storefronts)", Source: "Steam + Epic + PS Store + Xbox + Nintendo eShop", DIDLabel: "game"},
	{Domain: "iap_item", App: "software.etzhayyim.com", WorldTotal: 500_000_000, Unit: "in-app purchase items/SKUs", Source: "app store IAP catalog estimates", DIDLabel: "item"},
	// Software Vendors & Publishers (ソフトウェアベンダー)
	{Domain: "sw_vendor", App: "software.etzhayyim.com", WorldTotal: 500_000, Unit: "software vendors/publishers", Source: "Gartner + IDC + app store developer accounts", DIDLabel: "vendor"},
	// Software Licensing (ソフトウェアライセンス)
	{Domain: "sw_license_key", App: "software.etzhayyim.com", WorldTotal: 10_000_000_000, Unit: "software license keys (issued cumulative)", Source: "BSA + commercial SW licensing estimates", DIDLabel: "key"},
	{Domain: "eula", App: "software.etzhayyim.com", WorldTotal: 50_000_000, Unit: "unique EULA/ToS documents", Source: "ToS;DR + app store + commercial SW", DIDLabel: "document"},
	{Domain: "sw_subscription", App: "software.etzhayyim.com", WorldTotal: 5_000_000_000, Unit: "active software subscriptions (SaaS+desktop)", Source: "Zuora + Gartner SaaS market estimates", DIDLabel: "subscription"},
	// Software Security (ソフトウェアセキュリティ)
	{Domain: "sw_patch", App: "software.etzhayyim.com", WorldTotal: 5_000_000, Unit: "security patches (CVE→fix mappings)", Source: "NVD + vendor security advisories", DIDLabel: "patch"},
	{Domain: "app_review", App: "software.etzhayyim.com", WorldTotal: 10_000_000_000, Unit: "app store reviews (all platforms cumulative)", Source: "App Store + Google Play + Steam reviews", DIDLabel: "review"},
	// Software & Development Ecosystem (ソフトウェア開発 — OSINT)
	{Domain: "git_commit", App: "repo.etzhayyim.com", WorldTotal: 10_000_000_000, Unit: "git commits (global)", Source: "GitHub + GitLab + Bitbucket commit estimates", DIDLabel: "commit"},
	{Domain: "git_issue", App: "repo.etzhayyim.com", WorldTotal: 2_000_000_000, Unit: "issues & pull requests (global)", Source: "GitHub + GitLab + Jira estimates", DIDLabel: "issue"},
	{Domain: "code_file", App: "repo.etzhayyim.com", WorldTotal: 100_000_000_000, Unit: "source code files (global)", Source: "GitHub + all VCS file count estimates", DIDLabel: "file"},
	{Domain: "code_symbol", App: "repo.etzhayyim.com", WorldTotal: 50_000_000_000, Unit: "function/class/method definitions", Source: "AST-level symbol estimates across all repos", DIDLabel: "symbol"},
	{Domain: "container_image", App: "container.etzhayyim.com", WorldTotal: 500_000_000, Unit: "container image tags (Docker/OCI)", Source: "Docker Hub + GHCR + ECR + private registries", DIDLabel: "image"},
	{Domain: "cloud_instance", App: "cloud.etzhayyim.com", WorldTotal: 500_000_000, Unit: "cloud instances (VM+container+serverless)", Source: "Gartner + Flexera State of Cloud", DIDLabel: "instance"},
	{Domain: "k8s_cluster", App: "k8s.etzhayyim.com", WorldTotal: 5_000_000, Unit: "Kubernetes clusters (global)", Source: "CNCF Survey + Datadog Container Report", DIDLabel: "cluster"},
	{Domain: "k8s_pod", App: "k8s.etzhayyim.com", WorldTotal: 500_000_000, Unit: "Kubernetes pods (running)", Source: "Datadog Container Report 2025", DIDLabel: "pod"},
	{Domain: "dev_account", App: "dev.etzhayyim.com", WorldTotal: 200_000_000, Unit: "developer accounts (GitHub/GitLab/Bitbucket)", Source: "GitHub Octoverse + GitLab + Bitbucket", DIDLabel: "account"},
	{Domain: "oss_license", App: "repo.etzhayyim.com", WorldTotal: 1_000_000_000, Unit: "OSS license applications (repo×license)", Source: "SPDX + GitHub license detection", DIDLabel: "application"},
	{Domain: "package_version", App: "sbom.etzhayyim.com", WorldTotal: 5_000_000_000, Unit: "package releases/versions (all registries)", Source: "npm + PyPI + crates.io + Maven + NuGet + RubyGems", DIDLabel: "version"},
	{Domain: "api_schema", App: "api.etzhayyim.com", WorldTotal: 1_000_000_000, Unit: "API schemas/domain models", Source: "OpenAPI + GraphQL + gRPC schema estimates", DIDLabel: "schema"},
	// Fictional Entities — Characters (キャラクター)
	{Domain: "character", App: "character.etzhayyim.com", WorldTotal: 500_000_000, Unit: "named fictional characters (all media)", Source: "MAL + AniList + IGDB + IMDb + MangaUpdates + book databases", DIDLabel: "character"},
	{Domain: "character_anime", App: "character.etzhayyim.com", WorldTotal: 500_000, Unit: "anime characters", Source: "MAL + AniList character databases", DIDLabel: "character"},
	{Domain: "character_manga", App: "character.etzhayyim.com", WorldTotal: 2_000_000, Unit: "manga characters", Source: "MAL + MangaUpdates + ComicVine", DIDLabel: "character"},
	{Domain: "character_game", App: "character.etzhayyim.com", WorldTotal: 9_000_000, Unit: "game characters", Source: "IGDB + MobyGames + VNDB", DIDLabel: "character"},
	{Domain: "character_movie", App: "character.etzhayyim.com", WorldTotal: 5_000_000, Unit: "movie characters", Source: "IMDb + TMDb", DIDLabel: "character"},
	{Domain: "character_tv", App: "character.etzhayyim.com", WorldTotal: 3_000_000, Unit: "TV/drama characters", Source: "IMDb + TMDb + MyDramaList", DIDLabel: "character"},
	{Domain: "character_book", App: "character.etzhayyim.com", WorldTotal: 500_000_000, Unit: "book/novel characters", Source: "ISBN titles × avg named characters", DIDLabel: "character"},
	// Fictional Entities — Worlds & Settings (世界観)
	{Domain: "fiction_world", App: "character.etzhayyim.com", WorldTotal: 10_000_000, Unit: "fictional universes/settings", Source: "franchise/series world-building databases", DIDLabel: "world"},
	{Domain: "fiction_location", App: "character.etzhayyim.com", WorldTotal: 50_000_000, Unit: "fictional places (cities/planets/dungeons)", Source: "wiki + fan databases across all media", DIDLabel: "location"},
	{Domain: "fiction_item", App: "character.etzhayyim.com", WorldTotal: 50_000_000, Unit: "fictional items (weapons/artifacts/tools)", Source: "game item DBs + wiki + fan databases", DIDLabel: "item"},
	// Fictional Entities — Story Structure (作品構造)
	{Domain: "episode", App: "episode.etzhayyim.com", WorldTotal: 500_000_000, Unit: "episodes/chapters (anime+manga+TV+novel)", Source: "MAL + MangaUpdates + IMDb + novel platforms", DIDLabel: "episode"},
	{Domain: "story_arc", App: "episode.etzhayyim.com", WorldTotal: 100_000_000, Unit: "story arcs/plot lines", Source: "fan wikis + structured story databases", DIDLabel: "arc"},
	{Domain: "character_relation", App: "character.etzhayyim.com", WorldTotal: 1_000_000_000, Unit: "character relationships (friend/enemy/family edges)", Source: "character graph estimates across all media", DIDLabel: "relation"},
	{Domain: "cast_mapping", App: "character.etzhayyim.com", WorldTotal: 50_000_000, Unit: "voice actor/actor ↔ character mappings", Source: "MAL + IMDb + Behind The Voice Actors", DIDLabel: "casting"},
	{Domain: "nijisousaku", App: "nijisousaku.etzhayyim.com", WorldTotal: 500_000_000, Unit: "fan works/doujinshi/fanfic", Source: "pixiv + AO3 + Comiket + fanfiction.net", DIDLabel: "work"},
	// Threat Intelligence — Actors & Organizations (脅威アクター・犯罪組織)
	{Domain: "apt_group", App: "malak.etzhayyim.com", WorldTotal: 300, Unit: "tracked APT groups", Source: "MITRE ATT&CK + CrowdStrike + Mandiant", DIDLabel: "group"},
	{Domain: "cybercrime_group", App: "malak.etzhayyim.com", WorldTotal: 5_000, Unit: "cybercrime gangs/groups", Source: "Europol IOCTA + FBI IC3 + MITRE", DIDLabel: "group"},
	{Domain: "crime_org", App: "malak.etzhayyim.com", WorldTotal: 10_000, Unit: "criminal organizations (physical)", Source: "UNODC + Europol SOCTA + national law enforcement", DIDLabel: "org"},
	{Domain: "threat_actor", App: "malak.etzhayyim.com", WorldTotal: 50_000, Unit: "identified threat actors (individuals)", Source: "FBI + Interpol + national cyber agencies", DIDLabel: "actor"},
	{Domain: "ransomware_family", App: "malak.etzhayyim.com", WorldTotal: 5_000, Unit: "ransomware families", Source: "ID Ransomware + No More Ransom + CISA", DIDLabel: "family"},
	{Domain: "malware_family", App: "malak.etzhayyim.com", WorldTotal: 1_000_000, Unit: "malware families/variants", Source: "VirusTotal + MalwareBazaar + MITRE", DIDLabel: "family"},
	{Domain: "malware_sample", App: "malak.etzhayyim.com", WorldTotal: 2_000_000_000, Unit: "malware samples (hashes)", Source: "VirusTotal + MalwareBazaar + national CERTs", DIDLabel: "sample"},
	{Domain: "cve", App: "malak.etzhayyim.com", WorldTotal: 250_000, Unit: "CVE vulnerabilities (cumulative)", Source: "MITRE CVE + NVD + CISA KEV", DIDLabel: "cve"},
	{Domain: "exploit_kit", App: "malak.etzhayyim.com", WorldTotal: 500, Unit: "exploit kits", Source: "MITRE ATT&CK + Proofpoint", DIDLabel: "kit"},
	// Threat Intelligence — Malicious Infrastructure (悪性インフラ)
	{Domain: "botnet_c2", App: "malak.etzhayyim.com", WorldTotal: 100_000, Unit: "active botnet C2 servers", Source: "Shadowserver + abuse.ch + Spamhaus", DIDLabel: "c2"},
	{Domain: "malicious_domain", App: "malak.etzhayyim.com", WorldTotal: 10_000_000, Unit: "compromised/malicious domains", Source: "Spamhaus DBL + PhishTank + URLhaus", DIDLabel: "domain"},
	{Domain: "phishing_domain", App: "malak.etzhayyim.com", WorldTotal: 5_000_000, Unit: "phishing domains/yr", Source: "APWG + PhishTank + OpenPhish", DIDLabel: "domain"},
	{Domain: "malicious_ip", App: "malak.etzhayyim.com", WorldTotal: 50_000_000, Unit: "malicious IP addresses (active)", Source: "AbuseIPDB + Spamhaus + Shodan", DIDLabel: "ip"},
	{Domain: "bulletproof_host", App: "malak.etzhayyim.com", WorldTotal: 500, Unit: "bulletproof hosting providers", Source: "Spamhaus + Brian Krebs research + abuse.ch", DIDLabel: "host"},
	{Domain: "darkweb_site", App: "malak.etzhayyim.com", WorldTotal: 100_000, Unit: "dark web .onion sites (active)", Source: "Tor Metrics + DarkOwl + Flashpoint", DIDLabel: "site"},
	{Domain: "abuse_contact", App: "malak.etzhayyim.com", WorldTotal: 500_000, Unit: "abuse contact records (ISP/hosting)", Source: "RIPE + ARIN + APNIC abuse-c", DIDLabel: "contact"},
	{Domain: "malicious_registrar", App: "malak.etzhayyim.com", WorldTotal: 5_000, Unit: "registrars with high abuse rates", Source: "Spamhaus + ICANN compliance", DIDLabel: "registrar"},
	// Threat Intelligence — Leaked & Exposed Data (漏洩データ)
	{Domain: "data_breach", App: "malak.etzhayyim.com", WorldTotal: 10_000, Unit: "major data breaches (reported)", Source: "HIBP + Privacy Rights Clearinghouse + national DPAs", DIDLabel: "breach"},
	{Domain: "leaked_credential", App: "malak.etzhayyim.com", WorldTotal: 15_000_000_000, Unit: "leaked credentials (email+password pairs)", Source: "HIBP + Dehashed + intelligence feeds", DIDLabel: "credential"},
	{Domain: "paste_leak", App: "malak.etzhayyim.com", WorldTotal: 50_000_000, Unit: "paste site entries (leaked data)", Source: "Pastebin + GitHub Gist + paste monitoring", DIDLabel: "paste"},
	// Threat Intelligence — OSINT Infrastructure (OSINT インフラ情報)
	{Domain: "whois_record", App: "malak.etzhayyim.com", WorldTotal: 350_000_000, Unit: "WHOIS registration records", Source: "ICANN WHOIS + RDAP + registrar databases", DIDLabel: "record"},
	{Domain: "dns_record", App: "malak.etzhayyim.com", WorldTotal: 5_000_000_000, Unit: "DNS records (A/AAAA/MX/NS/CNAME)", Source: "Passive DNS + Farsight DNSDB + SecurityTrails", DIDLabel: "record"},
	{Domain: "asn", App: "malak.etzhayyim.com", WorldTotal: 100_000, Unit: "Autonomous System Numbers", Source: "IANA + RIR delegations", DIDLabel: "asn"},
	{Domain: "bgp_route", App: "malak.etzhayyim.com", WorldTotal: 1_000_000, Unit: "BGP route announcements", Source: "RIPE RIS + RouteViews + BGPStream", DIDLabel: "route"},
	{Domain: "tor_node", App: "malak.etzhayyim.com", WorldTotal: 8_000, Unit: "Tor relay/exit nodes", Source: "Tor Metrics + Onionoo", DIDLabel: "node"},
	{Domain: "open_proxy", App: "malak.etzhayyim.com", WorldTotal: 10_000_000, Unit: "open proxy servers", Source: "Shodan + Censys + proxy lists", DIDLabel: "proxy"},
	{Domain: "exposed_service", App: "malak.etzhayyim.com", WorldTotal: 500_000_000, Unit: "internet-exposed services (Shodan/Censys)", Source: "Shodan + Censys + BinaryEdge", DIDLabel: "service"},
	// Threat Intelligence — Watchlists & PEP (監視リスト)
	{Domain: "pep", App: "yabai.etzhayyim.com", WorldTotal: 5_000_000, Unit: "politically exposed persons (PEP)", Source: "Dow Jones + Refinitiv + national PEP lists", DIDLabel: "person"},
	{Domain: "wanted_person", App: "yabai.etzhayyim.com", WorldTotal: 200_000, Unit: "wanted persons (international)", Source: "Interpol Red Notices + FBI + national wanted lists", DIDLabel: "person"},
	{Domain: "terror_watchlist", App: "yabai.etzhayyim.com", WorldTotal: 2_000_000, Unit: "terror watchlist entities", Source: "UN 1267 + OFAC SDN + EU terror lists", DIDLabel: "entity"},
	{Domain: "shell_company", App: "yabai.etzhayyim.com", WorldTotal: 50_000_000, Unit: "suspected shell/front companies", Source: "ICIJ + FinCEN + Pandora/Panama Papers", DIDLabel: "entity"},
	{Domain: "sex_offender", App: "yabai.etzhayyim.com", WorldTotal: 1_000_000, Unit: "registered sex offenders", Source: "NSOPW + Interpol ICSE + national registries", DIDLabel: "person"},
	// Threat Intelligence — Spam & Phishing Content (迷惑メール・迷惑電話・フィッシング)
	// spam_email: 160B/day volume は performer 単位では不要。spam_sender (500M) + spam_campaign (50M) + scam_template (1M) で performer カバー
	{Domain: "spam_campaign", App: "malak.etzhayyim.com", WorldTotal: 50_000_000, Unit: "spam campaigns (unique templates/yr)", Source: "Proofpoint + Barracuda + Cisco Talos", DIDLabel: "campaign"},
	{Domain: "spam_sender", App: "malak.etzhayyim.com", WorldTotal: 500_000_000, Unit: "spam sender addresses/domains", Source: "Spamhaus SBL + SURBL + barracuda", DIDLabel: "sender"},
	// robocall: 100B/yr volume は performer 単位では不要。robocall_number (50M) + robocall_campaign (5M) でカバー
	{Domain: "robocall_number", App: "malak.etzhayyim.com", WorldTotal: 50_000_000, Unit: "known spam phone numbers", Source: "Truecaller + Hiya + national DNC registries", DIDLabel: "number"},
	{Domain: "robocall_campaign", App: "malak.etzhayyim.com", WorldTotal: 5_000_000, Unit: "robocall/vishing campaigns/yr", Source: "FTC + Truecaller + STIR/SHAKEN analytics", DIDLabel: "campaign"},
	{Domain: "phishing_page", App: "malak.etzhayyim.com", WorldTotal: 50_000_000, Unit: "phishing pages/yr (unique URLs)", Source: "APWG + PhishTank + Google Safe Browsing", DIDLabel: "page"},
	{Domain: "phishing_kit", App: "malak.etzhayyim.com", WorldTotal: 10_000, Unit: "phishing kits (toolkits)", Source: "Group-IB + Proofpoint + PhishMe", DIDLabel: "kit"},
	{Domain: "scam_template", App: "malak.etzhayyim.com", WorldTotal: 1_000_000, Unit: "scam message templates (email/SMS/voice)", Source: "Scamwatch + FTC + Action Fraud + 国民生活センター", DIDLabel: "template"},
	// sms_spam: 20B/yr volume は performer 単位では不要。robocall_number + scam_template でカバー
	{Domain: "fraud_phone_line", App: "malak.etzhayyim.com", WorldTotal: 500_000, Unit: "fraud call center phone lines", Source: "Interpol + FBI + 警察庁 特殊詐欺対策", DIDLabel: "line"},
	// Adult Content (アダルトコンテンツ — shinshi.etzhayyim.com restricted)
	{Domain: "adult_performer", App: "shinshi.etzhayyim.com", WorldTotal: 5_000_000, Unit: "adult content performers/models", Source: "IAFD + FreeOnes + industry databases", DIDLabel: "performer"},
	{Domain: "adult_content", App: "shinshi.etzhayyim.com", WorldTotal: 500_000_000, Unit: "adult content items (video/image sets)", Source: "industry production estimates", DIDLabel: "content"},
	{Domain: "adult_studio", App: "shinshi.etzhayyim.com", WorldTotal: 50_000, Unit: "adult production studios/labels", Source: "ASACP + FSC + industry registries", DIDLabel: "studio"},
	{Domain: "escort_listing", App: "shinshi.etzhayyim.com", WorldTotal: 10_000_000, Unit: "escort/companion service listings", Source: "web scraping aggregates + platform estimates", DIDLabel: "listing"},
	{Domain: "adult_platform", App: "shinshi.etzhayyim.com", WorldTotal: 50_000, Unit: "adult content platforms/sites", Source: "SimilarWeb + Alexa adult category", DIDLabel: "platform"},
	{Domain: "adult_age_verification", App: "shinshi.etzhayyim.com", WorldTotal: 100_000_000, Unit: "age verification records", Source: "UK Online Safety Act + EU DSA + national regulations", DIDLabel: "verification"},
	// Legal Evidence (裁判証拠)
	{Domain: "saiban_shoko", App: "hanrei.etzhayyim.com", WorldTotal: 500_000_000, Unit: "court evidence items (exhibits cumulative)", Source: "national court systems + UNODC", DIDLabel: "exhibit"},
	{Domain: "digital_forensic", App: "hanrei.etzhayyim.com", WorldTotal: 50_000_000, Unit: "digital forensic evidence artifacts", Source: "NIST CFTT + law enforcement forensic labs", DIDLabel: "artifact"},
	{Domain: "chain_of_custody", App: "hanrei.etzhayyim.com", WorldTotal: 1_000_000_000, Unit: "chain of custody records", Source: "evidence × custody transfer events", DIDLabel: "record"},
	{Domain: "kantei", App: "hanrei.etzhayyim.com", WorldTotal: 10_000_000, Unit: "expert witness reports/appraisals", Source: "national court statistics + forensic labs", DIDLabel: "report"},
	{Domain: "witness_statement", App: "hanrei.etzhayyim.com", WorldTotal: 200_000_000, Unit: "witness statements/depositions", Source: "national court filing statistics", DIDLabel: "statement"},
}

// ── PDS live query types ──

type wcSqlResp struct {
	Columns []string `json:"columns"`
	Rows    [][]any  `json:"rows"`
	OrgID   string   `json:"org_id,omitempty"`
	Cursor  string   `json:"cursor,omitempty"`
}

type wcHeartbeatAppsResp struct {
	Apps   []string `json:"apps"`
	Source string   `json:"source,omitempty"`
}

type wcDomainResult struct {
	Domain      string  `json:"domain"`
	App         string  `json:"app"`
	DIDCount    int     `json:"didCount"`
	RecordCount int     `json:"recordCount"`
	Collected   int     `json:"collected"`
	WorldTotal  int     `json:"worldTotal"`
	Unit        string  `json:"unit"`
	Coverage    float64 `json:"coverage"`
	CoverageDID float64 `json:"coverageDid"`
	CoverageRec float64 `json:"coverageRecord"`
	Gap         float64 `json:"gap"`
	Remaining   int     `json:"remaining"`
	Source      string  `json:"source"`
	DIDLabel    string  `json:"didLabel"`
	RecordLabel string  `json:"recordLabel,omitempty"`
	CountSource string  `json:"countSource,omitempty"` // graph | heartbeat | mixed | none
}

type wcWorkerResult struct {
	Nanoid      string `json:"nanoid"`
	DisplayName string `json:"displayName"`
	DID         string `json:"did"`
	DIDCount    int    `json:"didCount"`
	DeployedAt  string `json:"deployedAt,omitempty"`
}

type wcSummary struct {
	TotalApps               int     `json:"totalApps"`
	TotalDIDs               int     `json:"totalDIDs"`
	TotalRecords            int     `json:"totalRecords"`
	TotalProfiles           int     `json:"totalProfiles"`
	ProfilesLinkedActor     int     `json:"profilesLinkedActor,omitempty"`
	ProfilesLinkedDID       int     `json:"profilesLinkedDid,omitempty"`
	ProfilesFullyLinked     int     `json:"profilesFullyLinked,omitempty"`
	RecordByRepoTotal       int     `json:"recordByRepoTotal,omitempty"`
	RecordByCollectionTotal int     `json:"recordByCollectionTotal,omitempty"`
	WorldCoverage           float64 `json:"worldCoverage"`
	WorldCoverageDID        float64 `json:"worldCoverageDid"`
	WorldCoverageRecord     float64 `json:"worldCoverageRecord"`
	WorldCoverageOverall    float64 `json:"worldCoverageOverall"`
	RecentRecords           int     `json:"recentRecords,omitempty"`
	RecentSince             string  `json:"recentSince,omitempty"`
}

type wcAnomaly struct {
	Domain     string `json:"domain"`
	Collected  int    `json:"collected"`
	WorldTotal int    `json:"worldTotal"`
	Kind       string `json:"kind"`
	Detail     string `json:"detail,omitempty"`
}

type wcAuthStatus struct {
	Mode      string `json:"mode"`
	OrgID     string `json:"orgId,omitempty"`
	ActiveDID string `json:"activeDid,omitempty"`
}

type worldCoverageReport struct {
	EvaluatedAt string           `json:"evaluatedAt"`
	PDS         string           `json:"pds"`
	Summary     wcSummary        `json:"summary"`
	Auth        wcAuthStatus     `json:"auth"`
	Domains     []wcDomainResult `json:"domains"`
	TopWorkers  []wcWorkerResult `json:"topWorkers,omitempty"`
	Anomalies   []wcAnomaly      `json:"anomalies,omitempty"`
}

type profileTopologyCounts struct {
	Total       int
	LinkedActor int
	LinkedDID   int
	LinkedBoth  int
}

// ── Entry point ──

func runWorldCoverage(args []string) error {
	fs := flag.NewFlagSet("coverage", flag.ContinueOnError)
	pdsURL := fs.String("pds", defaultPDSURL, "PDS base URL")
	orgOverride := fs.String("org", "", "override auth org scope (sends X-Gftd-Org-Id)")
	worldData := fs.String("world-data", "", "path to world domain totals JSON (default: <repo>/config/world_domains.json if exists)")
	strict := fs.Bool("strict", false, "strict mode: disable heartbeat/local fallback (graph data only)")
	since := fs.String("since", "", "recent records window (RFC3339, YYYY-MM-DD, or duration like 24h)")
	jsonOut := fs.Bool("json", false, "output as JSON")
	topN := fs.Int("top", 30, "show top N workers by DID count")
	domain := fs.String("domain", "", "filter by domain (e.g. dns, hanrei)")
	offline := fs.Bool("offline", false, "offline mode (local manifest scan only, no PDS query)")
	rootDir := fs.String("root", "", "repo root (default: git root)")

	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	// Resolve root
	root := *rootDir
	if root == "" {
		cwd, _ := os.Getwd()
		var err error
		root, err = findGitRoot(cwd)
		if err != nil {
			root = cwd
		}
	}
	root, _ = filepath.Abs(root)
	domains := loadWorldDomains(root, *worldData)
	requestedDomain := strings.TrimSpace(*domain)
	domainScope := domains
	if requestedDomain != "" {
		filtered := make([]worldDomain, 0, 1)
		for _, wd := range domains {
			if wd.Domain == requestedDomain {
				filtered = append(filtered, wd)
				break
			}
		}
		if len(filtered) > 0 {
			domainScope = filtered
		}
	}
	sinceAt, sinceISO, hasSince, sinceErr := resolveSinceTime(*since)
	if sinceErr != nil {
		return sinceErr
	}

	report := worldCoverageReport{
		EvaluatedAt: time.Now().UTC().Format(time.RFC3339),
		PDS:         *pdsURL,
		Auth: wcAuthStatus{
			Mode: "unauthenticated",
		},
	}

	if *offline {
		return runOfflineCoverage(root, &report, *domain, *jsonOut)
	}

	client := &http.Client{Timeout: 30 * time.Second}

	// ── kagami SQL via graph.etzhayyim.com (primary path) ──
	{
		kagamiEP := os.Getenv("KAGAMI_ENDPOINT")
		if kagamiEP == "" {
			kagamiEP = "https://graph.etzhayyim.com"
		}
		kcfg := kagamiConfig{Endpoint: kagamiEP}
		kagamiErr := runKagamiCoverage(client, kcfg, root, &report, domainScope, domains, requestedDomain, hasSince, sinceISO, sinceAt, *jsonOut, *topN)
		if kagamiErr == nil {
			return nil
		}
		fmt.Fprintf(os.Stderr, "warning: kagami query via PDS failed: %v\n", kagamiErr)
	}
	queryOrgID := ""
	localApps := scanLocalApps(root)

	queryPDSRequest := func(reqBody map[string]any) (*wcSqlResp, error) {
		payload, _ := json.Marshal(reqBody)

		queryBase := func(base string) (*wcSqlResp, error) {
			// Primary: ai.gftd.kagami.sql (auth required)
			endpoints := []string{
				"/xrpc/ai.gftd.kagami.sql",
			}
			var lastErr error
			for _, ep := range endpoints {
				for attempt := 0; attempt < 3; attempt++ {
					req, _ := http.NewRequest("POST", strings.TrimRight(base, "/")+ep, bytes.NewReader(payload))
					req.Header.Set("Content-Type", "application/json")
					setCoverageAuthHeaders(req, *orgOverride)
					resp, err := client.Do(req)
					if err != nil {
						lastErr = fmt.Errorf("PDS unreachable: %w", err)
						if attempt < 2 {
							time.Sleep(time.Duration(attempt+1) * 250 * time.Millisecond)
						}
						continue
					}
					body, _ := io.ReadAll(resp.Body)
					resp.Body.Close()
					if resp.StatusCode == 429 {
						lastErr = fmt.Errorf("PDS %d: %s", resp.StatusCode, truncStr(string(body), 200))
						if attempt < 2 {
							time.Sleep(time.Duration(attempt+1) * 300 * time.Millisecond)
						}
						continue
					}
					if resp.StatusCode == 404 {
						lastErr = fmt.Errorf("PDS %d: %s", resp.StatusCode, truncStr(string(body), 200))
						break
					}
					if resp.StatusCode == 401 || resp.StatusCode == 403 {
						return nil, fmt.Errorf("PDS auth required (%d) — run 'gftd auth login' first", resp.StatusCode)
					}
					if resp.StatusCode != 200 {
						lastErr = fmt.Errorf("PDS %d: %s", resp.StatusCode, truncStr(string(body), 200))
						break
					}
					var result wcSqlResp
					if err := json.Unmarshal(body, &result); err != nil {
						return nil, fmt.Errorf("parse: %w", err)
					}
					if queryOrgID == "" && strings.TrimSpace(result.OrgID) != "" {
						queryOrgID = strings.TrimSpace(result.OrgID)
					}
					return &result, nil
				}
			}
			return nil, lastErr
		}

		result, err := queryBase(*pdsURL)
		if err == nil {
			return result, nil
		}
		if strings.Contains(err.Error(), "auth required") {
			return nil, err
		}
		if fb, useFallback := fallbackPDSBase(*pdsURL); useFallback {
			fallbackResult, fallbackErr := queryBase(fb)
			if fallbackErr == nil {
				return fallbackResult, nil
			}
			return nil, fmt.Errorf("%v; fallback failed: %v", err, fallbackErr)
		}
		return nil, err
	}

	queryPDS := func(sql string) (*wcSqlResp, error) {
		return queryPDSRequest(map[string]any{"statement": sql, "timeoutMs": 20000})
	}

	queryPDSAppsKeyset := func(pageSize int, maxRows int) (*wcSqlResp, error) {
		if pageSize <= 0 {
			pageSize = 200
		}
		if maxRows <= 0 {
			maxRows = pageSize
		}
		out := &wcSqlResp{
			Columns: []string{"a.nanoid", "a.display_name", "a.did", "a.deploy_at"},
			Rows:    make([][]any, 0, pageSize),
		}
		cursor := ""
		const maxPages = 100
		for page := 0; page < maxPages; page++ {
			stmt := "MATCH (a:App) RETURN a.nanoid, a.display_name, a.did, a.deploy_at ORDER BY a.nanoid LIMIT $limit"
			params := map[string]any{"limit": pageSize}
			if cursor != "" {
				stmt = "MATCH (a:App) WHERE a.nanoid > $cursor RETURN a.nanoid, a.display_name, a.did, a.deploy_at ORDER BY a.nanoid LIMIT $limit"
				params["cursor"] = cursor
			}
			result, err := queryPDSRequest(map[string]any{
				"statement": stmt,
				"params":    params,
				"timeoutMs": 30000,
				"maxRows":   pageSize,
			})
			if err != nil {
				if page == 0 {
					return nil, err
				}
				return out, nil
			}
			if result == nil || len(result.Rows) == 0 {
				break
			}
			if out.OrgID == "" && strings.TrimSpace(result.OrgID) != "" {
				out.OrgID = strings.TrimSpace(result.OrgID)
			}
			out.Rows = append(out.Rows, result.Rows...)
			if len(out.Rows) >= maxRows {
				out.Rows = out.Rows[:maxRows]
				break
			}
			last := result.Rows[len(result.Rows)-1]
			if len(last) == 0 {
				break
			}
			next := strings.TrimSpace(fmt.Sprint(last[0]))
			if next == "" || next == cursor {
				break
			}
			cursor = next
			if len(result.Rows) < pageSize {
				break
			}
		}
		return out, nil
	}

	// Guard against repeated auth/policy-denied graph queries.
	var queryBlockedErr error
	markQueryBlocked := func(err error) {
		if err == nil {
			return
		}
		if queryBlockedErr == nil {
			queryBlockedErr = err
		}
		if strings.Contains(strings.ToLower(err.Error()), "auth required") {
			if report.Auth.Mode == "authenticated" {
				report.Auth.Mode = "authenticated (graph query restricted)"
			} else {
				report.Auth.Mode = "restricted"
			}
		}
	}
	queryPDSGuarded := func(sql string) (*wcSqlResp, error) {
		if queryBlockedErr != nil {
			return nil, queryBlockedErr
		}
		result, err := queryPDS(sql)
		if err != nil {
			markQueryBlocked(err)
			return nil, err
		}
		return result, nil
	}
	if token := resolveGFTDToken(); token != "" {
		report.Auth.Mode = "authenticated"
	}
	if did := resolveActiveDID(); did != "" {
		report.Auth.ActiveDID = did
	}

	// ── Query 1: App list ──
	appResult := appRowsFromLocal(localApps)
	if *strict {
		var err error
		appResult, err = queryPDSAppsKeyset(200, 1500)
		if err != nil {
			fmt.Fprintf(os.Stderr, "warning: app query failed: %v\n", err)
			appResult = appRowsFromLocal(localApps)
		}
	}
	if (appResult == nil || len(appResult.Rows) == 0) && len(localApps) > 0 {
		appResult = appRowsFromLocal(localApps)
	}

	qctx, qcancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer qcancel()
	qq, qerr := db.Q(qctx)
	if qerr != nil {
		qq = nil
	}

	// ── Query 2: App count ──
	appCountResult := (*wcSqlResp)(nil)
	if qq != nil {
		if cnt, err := qq.CountApps(qctx); err == nil {
			appCountResult = &wcSqlResp{Rows: [][]any{{cnt}}}
		}
	}

	// ── Query 3: Profile count ──
	profileCountResult := (*wcSqlResp)(nil)
	profileTopo := profileTopologyCounts{}
	if requestedDomain == "" && qq != nil {
		profileTopo = queryProfileTopologyCounts(qctx)
		if profileTopo.Total > 0 {
			profileCountResult = &wcSqlResp{Rows: [][]any{{profileTopo.Total}}}
		}
	}

	// ── Query 3a: Record count ──
	recordCountResult := (*wcSqlResp)(nil)
	recordByRepoResult := (*wcSqlResp)(nil)
	recordByCollectionResult := (*wcSqlResp)(nil)
	if requestedDomain == "" {
		if res, err := db.RawQuery(qctx, fmt.Sprintf(`
			SELECT COUNT(*)::bigint AS cnt
			FROM %s
			WHERE collection IS NOT NULL
		`, legacyVertexOtherTable)); err == nil {
			recordCountResult = &wcSqlResp{Rows: make([][]any, 0, len(res.Rows))}
			for _, row := range res.Rows {
				recordCountResult.Rows = append(recordCountResult.Rows, []any{row["cnt"]})
			}
		}
		if res, err := db.RawQuery(qctx, fmt.Sprintf(`
			SELECT repo, COUNT(*)::bigint AS cnt
			FROM %s
			WHERE collection IS NOT NULL AND repo IS NOT NULL
			GROUP BY repo
			LIMIT 20000
		`, legacyVertexOtherTable)); err == nil {
			recordByRepoResult = &wcSqlResp{Rows: make([][]any, 0, len(res.Rows))}
			for _, row := range res.Rows {
				recordByRepoResult.Rows = append(recordByRepoResult.Rows, []any{row["repo"], row["cnt"]})
			}
		}
		if res, err := db.RawQuery(qctx, fmt.Sprintf(`
			SELECT collection, COUNT(*)::bigint AS cnt
			FROM %s
			WHERE collection IS NOT NULL
			GROUP BY collection
			LIMIT 10000
		`, legacyVertexOtherTable)); err == nil {
			recordByCollectionResult = &wcSqlResp{Rows: make([][]any, 0, len(res.Rows))}
			for _, row := range res.Rows {
				recordByCollectionResult.Rows = append(recordByCollectionResult.Rows, []any{row["collection"], row["cnt"]})
			}
		}
	} else {
		recordByRepoResult = &wcSqlResp{Rows: make([][]any, 0, len(domainScope))}
		sum := 0
		for _, wd := range domainScope {
			host := normalizeDomainLookup(strings.TrimSuffix(wd.App, ".etzhayyim.com"))
			if host == "" {
				continue
			}
			res, err := db.RawQuery(qctx, fmt.Sprintf(`
				SELECT COUNT(*)::bigint AS cnt
				FROM %s
				WHERE collection IS NOT NULL
				  AND repo LIKE $1
			`, legacyVertexOtherTable), fmt.Sprintf("did:web:%s.etzhayyim.com%%", host))
			if err != nil || len(res.Rows) == 0 {
				continue
			}
			cnt := toInt([]any{res.Rows[0]["cnt"]}, 0)
			sum += cnt
			recordByRepoResult.Rows = append(recordByRepoResult.Rows, []any{
				fmt.Sprintf("did:web:%s.etzhayyim.com", host),
				cnt,
			})
		}
		recordCountResult = &wcSqlResp{Rows: [][]any{{sum}}}
	}

	// ── Query 4: DID list/count ──
	didResult := (*wcSqlResp)(nil)
	didCountByDomain := map[string]int{}
	if requestedDomain == "" && qq != nil {
		// Global mode: keep list-based behavior for downstream analysis.
		if raw, err := db.RawQuery(qctx, `
			SELECT did
			FROM vertex_did
			WHERE did IS NOT NULL
			ORDER BY did
		`); err == nil {
			didResult = &wcSqlResp{Rows: make([][]any, 0, len(raw.Rows))}
			for _, row := range raw.Rows {
				didResult.Rows = append(didResult.Rows, []any{parseStringLike(row["did"])})
			}
		}
	} else {
		// Domain mode: avoid full DID scans and use domain-bounded count queries.
		for _, wd := range domainScope {
			host := normalizeDomainLookup(strings.TrimSuffix(wd.App, ".etzhayyim.com"))
			if host == "" {
				continue
			}
			res, err := db.RawQuery(qctx, `
				SELECT COUNT(*)::bigint AS cnt
				FROM vertex_did
				WHERE did LIKE $1
			`, fmt.Sprintf("did:web:%s.etzhayyim.com%%", host))
			if err != nil || len(res.Rows) == 0 {
				continue
			}
			didCountByDomain[wd.Domain] += toInt([]any{res.Rows[0]["cnt"]}, 0)
		}
		didResult = &wcSqlResp{Rows: [][]any{}}
	}

	// Combine into legacy vars for compatibility
	appDIDResult := appResult
	totalResult := (*wcSqlResp)(nil)
	domainDIDResult := didResult

	// Build synthetic total from separate counts
	appCount := 0
	if appCountResult != nil && len(appCountResult.Rows) > 0 {
		appCount = toInt(appCountResult.Rows[0], 0)
	}
	if appCount == 0 && appDIDResult != nil && len(appDIDResult.Rows) > 0 {
		appCount = len(appDIDResult.Rows)
	}
	profileCount := 0
	if profileCountResult != nil && len(profileCountResult.Rows) > 0 {
		profileCount = toInt(profileCountResult.Rows[0], 0)
	}
	didCount := 0
	if requestedDomain != "" {
		didCount = sumCountMap(didCountByDomain)
	} else if didResult != nil {
		didCount = len(didResult.Rows)
	}
	recordCount := 0
	if recordCountResult != nil && len(recordCountResult.Rows) > 0 {
		recordCount = toInt(recordCountResult.Rows[0], 0)
	}
	_ = totalResult

	heartbeatApps := []string{}
	if !*strict {
		heartbeatSource := ""
		heartbeatErr := error(nil)
		heartbeatApps, heartbeatSource, heartbeatErr = queryHeartbeatApps(client, *pdsURL, *orgOverride)
		fallbackApplied := false
		appCount, appDIDResult, fallbackApplied = applyHeartbeatAppFallback(appCount, appDIDResult, heartbeatApps)
		if fallbackApplied {
			fmt.Fprintf(os.Stderr, "info: app count fallback from %q (%d apps)\n", heartbeatSource, appCount)
		}
		if heartbeatErr != nil && appCount == 0 {
			fmt.Fprintf(os.Stderr, "warning: heartbeat app fallback failed: %v\n", heartbeatErr)
		}
		if requestedDomain == "" {
			didCount, profileCount = applyCoverageSummaryFallback(didCount, profileCount, appDIDResult)
		}
	}

	if hasSince {
		report.Summary.RecentSince = sinceISO
		if recentResult, err := queryPDSGuarded(buildRecentRecordCountStatement(sinceAt, sinceISO)); err == nil && recentResult != nil && len(recentResult.Rows) > 0 {
			report.Summary.RecentRecords = toInt(recentResult.Rows[0], 0)
		} else if err != nil {
			fmt.Fprintf(os.Stderr, "warning: recent record query failed: %v\n", err)
		}
	}
	if queryBlockedErr != nil {
		fmt.Fprintf(os.Stderr, "warning: graph queries blocked; suppressing repeated retries: %v\n", queryBlockedErr)
	}

	if queryOrgID != "" {
		report.Auth.OrgID = queryOrgID
		if queryOrgID == "anon" && report.Auth.Mode == "authenticated" {
			if inferred := inferOrgFromActiveDID(report.Auth.ActiveDID); inferred != "" {
				report.Auth.OrgID = inferred
			} else {
				report.Auth.Mode = "authenticated (anon scope)"
			}
		}
	}
	if report.Auth.OrgID == "" && strings.TrimSpace(*orgOverride) != "" {
		report.Auth.OrgID = strings.TrimSpace(*orgOverride)
	}

	// Parse totals from separate queries
	report.Summary.TotalApps = appCount
	report.Summary.TotalDIDs = didCount
	report.Summary.TotalRecords = recordCount
	report.Summary.TotalProfiles = profileCount
	report.Summary.ProfilesLinkedActor = profileTopo.LinkedActor
	report.Summary.ProfilesLinkedDID = profileTopo.LinkedDID
	report.Summary.ProfilesFullyLinked = profileTopo.LinkedBoth

	// Parse top workers (columns: nanoid, display_name, did, deploy_at)
	if appDIDResult != nil {
		for _, row := range appDIDResult.Rows {
			if len(row) < 3 {
				continue
			}
			w := wcWorkerResult{
				Nanoid:      toStr(row[0]),
				DisplayName: toStr(row[1]),
				DID:         toStr(row[2]),
			}
			if len(row) > 3 {
				w.DeployedAt = toStr(row[3])
			}
			report.TopWorkers = append(report.TopWorkers, w)
		}
	}

	// Count DIDs per domain by parsing did:web:{app}.etzhayyim.com prefixes
	didByDomain := map[string]int{}
	if domainDIDResult != nil {
		for _, row := range domainDIDResult.Rows {
			if len(row) < 1 {
				continue
			}
			did := toStr(row[0])
			// Extract app from did:web:{app}.etzhayyim.com or did:web:{nanoid}.etzhayyim.com:{path}
			domainKey := extractDomainFromDID(did)
			if domainKey != "" {
				didByDomain[domainKey]++
			}
		}
	}
	for k, v := range didCountByDomain {
		if v > didByDomain[k] {
			didByDomain[k] = v
		}
	}
	graphDIDByDomain := cloneCountMap(didByDomain)
	recordByDomain := buildRecordDomainCounts(recordByRepoResult)
	recordByRepoDomain := cloneCountMap(recordByDomain)
	recordByCollectionDomain := buildCollectionDomainCounts(recordByCollectionResult, domains)
	recordByRepoTotal := sumCountMap(recordByDomain)
	recordByCollectionTotal := sumCountMap(recordByCollectionDomain)
	report.Summary.RecordByRepoTotal = recordByRepoTotal
	report.Summary.RecordByCollectionTotal = recordByCollectionTotal
	for k, v := range recordByCollectionDomain {
		recordByDomain[k] += v
	}
	// Prefer repo/listRecords counts when available (stable read-after-write source of truth).
	hostScope := map[string]bool{}
	if requestedDomain == "" {
		for host, cnt := range recordByRepoDomain {
			if cnt > 0 {
				hostScope[normalizeDomainLookup(host)] = true
			}
		}
	} else {
		for _, wd := range domainScope {
			hostScope[normalizeDomainLookup(strings.TrimSuffix(wd.App, ".etzhayyim.com"))] = true
		}
	}
	listRecordByDomain := map[string]int{}
	listDidByDomain := map[string]int{}
	authToken := resolveGFTDToken()
	if authToken != "" && len(hostScope) > 0 && requestedDomain == "" {
		listRecordByDomain, listDidByDomain = buildListRecordsDomainCounts(client, *pdsURL, authToken, domainScope, hostScope)
	}
	if len(listRecordByDomain) > 0 {
		report.Summary.RecordByRepoTotal = sumCountMap(listRecordByDomain)
	}

	// Also count from local magatama.jsonld scan for apps not yet in graph
	heartbeatDomainCounts := map[string]int{}
	if !*strict {
		heartbeatDomainCounts = buildHeartbeatDomainCounts(heartbeatApps, localApps)
		if len(heartbeatDomainCounts) > 0 {
			if len(didByDomain) == 0 {
				didByDomain = heartbeatDomainCounts
				fmt.Fprintf(os.Stderr, "info: domain DID fallback from heartbeat/local map (%d domain keys)\n", len(didByDomain))
			} else {
				merged := 0
				for k, v := range heartbeatDomainCounts {
					if didByDomain[k] <= 0 {
						didByDomain[k] = v
						merged++
					}
				}
				if merged > 0 {
					fmt.Fprintf(os.Stderr, "info: domain DID fallback merge from heartbeat/local map (+%d domain keys)\n", merged)
				}
			}
		}
	}
	if len(hostScope) == 0 {
		for _, wd := range domainScope {
			include := false
			for prefix, cnt := range didByDomain {
				if cnt > 0 && matchesDomain(prefix, wd) {
					include = true
					break
				}
			}
			if !include {
				for prefix, cnt := range heartbeatDomainCounts {
					if cnt > 0 && matchesDomain(prefix, wd) {
						include = true
						break
					}
				}
			}
			if include {
				host := normalizeDomainLookup(strings.TrimSuffix(wd.App, ".etzhayyim.com"))
				if host != "" {
					hostScope[host] = true
				}
			}
		}
	}
	for prefix, cnt := range didByDomain {
		if cnt <= 0 {
			continue
		}
		host := normalizeDomainLookup(prefix)
		if host != "" {
			hostScope[host] = true
		}
	}
	for prefix, cnt := range heartbeatDomainCounts {
		if cnt <= 0 {
			continue
		}
		host := normalizeDomainLookup(prefix)
		if host != "" {
			hostScope[host] = true
		}
	}
	if len(listRecordByDomain) == 0 && authToken != "" && len(hostScope) > 0 && requestedDomain == "" {
		listRecordByDomain, listDidByDomain = buildListRecordsDomainCounts(client, *pdsURL, authToken, domainScope, hostScope)
	}
	if len(listRecordByDomain) > 0 && report.Summary.TotalRecords == 0 {
		report.Summary.TotalRecords = sumCountMap(listRecordByDomain)
	}

	// Build domain results
	totalWorldTarget := 0
	totalWorldCoveredDid := 0
	totalWorldCoveredRecord := 0
	anomalies := make([]wcAnomaly, 0)
	for _, wd := range domains {
		if *domain != "" && wd.Domain != *domain {
			continue
		}
		dr := wcDomainResult{
			Domain:      wd.Domain,
			App:         wd.App,
			WorldTotal:  wd.WorldTotal,
			Unit:        wd.Unit,
			Source:      wd.Source,
			DIDLabel:    wd.DIDLabel,
			RecordLabel: wd.RecordLabel,
		}

		// Try to find DID count from PDS query
		// Match by app host prefix in DID
		graphDomainDid := 0
		for prefix, count := range didByDomain {
			if matchesDomain(prefix, wd) {
				dr.DIDCount += count
			}
		}
		if v := listDidByDomain[wd.Domain]; v > dr.DIDCount {
			dr.DIDCount = v
		}
		for prefix, count := range graphDIDByDomain {
			if matchesDomain(prefix, wd) {
				graphDomainDid += count
			}
		}
		if v := listRecordByDomain[wd.Domain]; v > 0 {
			dr.RecordCount = v
		} else {
			for prefix, count := range recordByDomain {
				if matchesDomain(prefix, wd) {
					dr.RecordCount += count
				}
			}
		}
		heartbeatDomainDid := 0
		for prefix, count := range heartbeatDomainCounts {
			if matchesDomain(prefix, wd) {
				heartbeatDomainDid += count
			}
		}
		dr.Collected = effectiveCollectedCount(dr.DIDCount, dr.RecordCount)
		dr.CountSource = inferCountSource(graphDomainDid, dr.RecordCount, heartbeatDomainDid)

		// Fallback: query dedicated vertex tables directly when DID-based count is 0.
		// Some domains (e.g. legal_entity_lei) have records written directly to their
		// vertex table bypassing vertex_did, so the DID prefix scan finds nothing.
		if dr.Collected == 0 {
			cnt, source, err := vertexTableFallbackCount(wd.Domain)
			if err != nil {
				fmt.Fprintf(os.Stderr, "warning: %s vertex table fallback query failed: %v\n", wd.Domain, err)
			} else if cnt > 0 {
				dr.RecordCount = int(cnt)
				dr.Collected = int(cnt)
				dr.CountSource = source
				fmt.Fprintf(os.Stderr, "info: %s fallback → %s = %d\n", wd.Domain, source, cnt)
			}
		}

		// Also check top workers for record counts
		for _, w := range report.TopWorkers {
			if matchesWorkerDomain(w, wd) {
				dr.Collected = max(dr.Collected, w.DIDCount)
			}
		}

		if wd.WorldTotal > 0 {
			dr.CoverageDID = float64(dr.DIDCount) / float64(wd.WorldTotal)
			dr.CoverageRec = float64(dr.RecordCount) / float64(wd.WorldTotal)
			dr.Coverage = float64(dr.Collected) / float64(wd.WorldTotal)
			if dr.Coverage > 1.0 {
				dr.Coverage = 1.0
			}
			if dr.CoverageDID > 1.0 {
				dr.CoverageDID = 1.0
			}
			if dr.CoverageRec > 1.0 {
				dr.CoverageRec = 1.0
			}
			dr.Gap = 1.0 - dr.Coverage
			dr.Remaining = wd.WorldTotal - dr.Collected
			if dr.Remaining < 0 {
				dr.Remaining = 0
			}
			if dr.Collected > wd.WorldTotal {
				anomalies = append(anomalies, wcAnomaly{
					Domain:     wd.Domain,
					Collected:  dr.Collected,
					WorldTotal: wd.WorldTotal,
					Kind:       "coverage_overflow",
					Detail:     "collected exceeds world total denominator",
				})
			}
		}
		report.Domains = append(report.Domains, dr)

		totalWorldTarget += wd.WorldTotal
		totalWorldCoveredDid += minInt(dr.DIDCount, wd.WorldTotal)
		totalWorldCoveredRecord += minInt(dr.RecordCount, wd.WorldTotal)
	}

	if totalWorldTarget > 0 {
		report.Summary.WorldCoverageDID = float64(totalWorldCoveredDid) / float64(totalWorldTarget)
		report.Summary.WorldCoverageRecord = float64(totalWorldCoveredRecord) / float64(totalWorldTarget)
		report.Summary.WorldCoverageOverall = 0.7*report.Summary.WorldCoverageDID + 0.3*report.Summary.WorldCoverageRecord
		report.Summary.WorldCoverage = report.Summary.WorldCoverageOverall
	}
	report.Anomalies = anomalies

	// Trim top workers to topN
	if len(report.TopWorkers) > *topN {
		report.TopWorkers = report.TopWorkers[:*topN]
	}

	if *jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(report)
	}

	printWorldCoverageText(&report, *topN)
	return nil
}

// ── Offline mode: local manifest scan only ──

type localApp struct {
	project string
	nanoid  string
	app     string
	did     string
}

func runOfflineCoverage(root string, report *worldCoverageReport, domainFilter string, jsonOut bool) error {
	apps := scanLocalApps(root)
	report.Summary.TotalApps = len(apps)
	report.PDS = "(offline)"

	// Count apps per domain
	appsByDomain := map[string]int{}
	for _, a := range apps {
		appsByDomain[a.project]++
	}

	// Domain → project name alias (when world domain name differs from project dir name)
	domainProjectAlias := map[string]string{
		"sovereign": "states",
	}

	for _, wd := range worldDomains {
		if domainFilter != "" && wd.Domain != domainFilter {
			continue
		}
		didCount := appsByDomain[wd.Domain]
		if alias, ok := domainProjectAlias[wd.Domain]; ok {
			didCount += appsByDomain[alias]
		}
		dr := wcDomainResult{
			Domain:      wd.Domain,
			App:         wd.App,
			DIDCount:    didCount,
			WorldTotal:  wd.WorldTotal,
			Unit:        wd.Unit,
			Source:      wd.Source,
			DIDLabel:    wd.DIDLabel,
			RecordLabel: wd.RecordLabel,
		}
		if wd.WorldTotal > 0 {
			dr.Coverage = float64(dr.DIDCount) / float64(wd.WorldTotal)
			if dr.Coverage > 1.0 {
				dr.Coverage = 1.0
			}
			dr.Gap = 1.0 - dr.Coverage
			dr.Remaining = wd.WorldTotal - dr.DIDCount
			if dr.Remaining < 0 {
				dr.Remaining = 0
			}
		}
		report.Domains = append(report.Domains, dr)
	}

	if jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(report)
	}

	printWorldCoverageText(report, 0)
	return nil
}

func scanLocalApps(root string) []localApp {
	var apps []localApp
	projDir := filepath.Join(root, "projects")
	entries, err := os.ReadDir(projDir)
	if err != nil {
		return apps
	}
	for _, e := range entries {
		if !e.IsDir() || !strings.HasPrefix(e.Name(), "ai-gftd-project-") {
			continue
		}
		project := strings.TrimPrefix(e.Name(), "ai-gftd-project-")

		// Find magatama.jsonld in wasm subdirs
		wasmDir := filepath.Join(projDir, e.Name(), "wasm")
		wasmEntries, err := os.ReadDir(wasmDir)
		if err != nil {
			continue
		}
		for _, we := range wasmEntries {
			if !we.IsDir() {
				continue
			}
			mPath := filepath.Join(wasmDir, we.Name(), "magatama.jsonld")
			data, err := os.ReadFile(mPath)
			if err != nil {
				continue
			}
			var m struct {
				ID      string `json:"@id"`
				Nanoid  string `json:"nanoid"`
				Project string `json:"project"`
			}
			if json.Unmarshal(data, &m) == nil {
				apps = append(apps, localApp{
					project: firstNonEmpty(m.Project, project),
					nanoid:  m.Nanoid,
					did:     m.ID,
					app:     we.Name(),
				})
			}
		}
	}
	return apps
}

func loadWorldDomains(root, explicitPath string) []worldDomain {
	path := strings.TrimSpace(explicitPath)
	if path == "" {
		candidate := filepath.Join(root, "config", "world_domains.json")
		if _, err := os.Stat(candidate); err == nil {
			path = candidate
		}
	}
	if path == "" {
		return worldDomains
	}
	data, err := os.ReadFile(path)
	if err != nil {
		fmt.Fprintf(os.Stderr, "warning: world-data read failed (%s): %v\n", path, err)
		return worldDomains
	}
	var parsed []worldDomain
	if err := json.Unmarshal(data, &parsed); err != nil || len(parsed) == 0 {
		fmt.Fprintf(os.Stderr, "warning: world-data parse failed (%s): %v\n", path, err)
		return worldDomains
	}
	fmt.Fprintf(os.Stderr, "info: loaded world domains from %s (%d entries)\n", path, len(parsed))
	return parsed
}

func resolveSinceTime(raw string) (time.Time, string, bool, error) {
	s := strings.TrimSpace(raw)
	if s == "" {
		return time.Time{}, "", false, nil
	}
	now := time.Now().UTC()
	if d, err := time.ParseDuration(s); err == nil {
		t := now.Add(-d)
		return t, t.Format(time.RFC3339), true, nil
	}
	layouts := []string{time.RFC3339, "2006-01-02"}
	for _, layout := range layouts {
		if t, err := time.Parse(layout, s); err == nil {
			return t.UTC(), t.UTC().Format(time.RFC3339), true, nil
		}
	}
	return time.Time{}, "", false, fmt.Errorf("invalid --since value: %q (use RFC3339, YYYY-MM-DD, or duration like 24h)", raw)
}

func buildRecentRecordCountStatement(sinceAt time.Time, sinceISO string) string {
	isoEsc := strings.ReplaceAll(sinceISO, `"`, `\"`)
	ms := sinceAt.UnixMilli()
	return fmt.Sprintf(
		`MATCH (n) WHERE n.collection IS NOT NULL AND ((n.createdAt IS NOT NULL AND n.createdAt >= "%s") OR (n.updatedAt IS NOT NULL AND n.updatedAt >= "%s") OR (n.created_at IS NOT NULL AND n.created_at >= "%s") OR (n.updated_at IS NOT NULL AND n.updated_at >= "%s") OR (n.createdAtMs IS NOT NULL AND n.createdAtMs >= %d) OR (n.updatedAtMs IS NOT NULL AND n.updatedAtMs >= %d)) RETURN count(n) AS cnt LIMIT 1`,
		isoEsc, isoEsc, isoEsc, isoEsc, ms, ms,
	)
}

func cloneCountMap(in map[string]int) map[string]int {
	out := make(map[string]int, len(in))
	for k, v := range in {
		out[k] = v
	}
	return out
}

func sumCountMap(in map[string]int) int {
	total := 0
	for _, v := range in {
		if v > 0 {
			total += v
		}
	}
	return total
}

func minInt(a, b int) int {
	if a < b {
		return a
	}
	return b
}

func inferCountSource(graphDidCount, graphRecordCount, heartbeatDidCount int) string {
	graph := graphDidCount > 0 || graphRecordCount > 0
	heartbeat := heartbeatDidCount > 0
	switch {
	case graph && heartbeat:
		return "mixed"
	case graph:
		return "graph"
	case heartbeat:
		return "heartbeat"
	default:
		return "none"
	}
}

func buildCollectionDomainCounts(recordByCollectionResult *wcSqlResp, domains []worldDomain) map[string]int {
	out := map[string]int{}
	if recordByCollectionResult == nil {
		return out
	}
	for _, row := range recordByCollectionResult.Rows {
		if len(row) < 2 {
			continue
		}
		col := strings.ToLower(strings.TrimSpace(toStr(row[0])))
		if col == "" {
			continue
		}
		cnt := toInt(row, 1)
		if cnt <= 0 {
			continue
		}
		bestDomain := ""
		bestScore := 0
		for _, wd := range domains {
			score := 0
			domainKey := strings.ToLower(wd.Domain)
			appHost := strings.ToLower(strings.TrimSuffix(wd.App, ".etzhayyim.com"))
			didLabel := strings.ToLower(wd.DIDLabel)
			recLabel := strings.ToLower(wd.RecordLabel)
			if strings.Contains(col, domainKey) {
				score += 4
			}
			if appHost != "" && strings.Contains(col, appHost) {
				score += 3
			}
			if didLabel != "" && strings.Contains(col, didLabel) {
				score++
			}
			if recLabel != "" && strings.Contains(col, recLabel) {
				score += 2
			}
			for _, alt := range wd.AltPrefixes {
				alt = strings.ToLower(strings.TrimSuffix(alt, "-"))
				if alt != "" && strings.Contains(col, alt) {
					score += 2
					break
				}
			}
			if score > bestScore {
				bestScore = score
				bestDomain = wd.Domain
			}
		}
		if bestScore > 0 && bestDomain != "" {
			out[bestDomain] += cnt
		}
	}
	return out
}

// ── Domain matching helpers ──

func extractDomainFromDID(did string) string {
	// did:web:dns.etzhayyim.com:zone:example_com → "dns"
	// did:web:scndu0rf.etzhayyim.com:zone:foo → "scndu0rf" (nanoid)
	if !strings.HasPrefix(did, "did:web:") {
		return ""
	}
	rest := strings.TrimPrefix(did, "did:web:")
	host := strings.Split(rest, ":")[0]
	host = strings.TrimSuffix(host, ".etzhayyim.com")
	return host
}

func matchesDomain(prefix string, wd worldDomain) bool {
	appHost := strings.TrimSuffix(wd.App, ".etzhayyim.com")
	if prefix == appHost {
		return true
	}
	// Check AltPrefixes — supports exact match or prefix match (trailing "-")
	for _, alt := range wd.AltPrefixes {
		if strings.HasSuffix(alt, "-") {
			// Prefix match: "gov-" matches "gov-jpn", "gov-usa", etc.
			if strings.HasPrefix(prefix, alt) {
				return true
			}
		} else if prefix == alt {
			return true
		}
	}
	// Also match nanoid-style
	return strings.Contains(wd.App, prefix)
}

func matchesWorkerDomain(w wcWorkerResult, wd worldDomain) bool {
	appHost := strings.TrimSuffix(wd.App, ".etzhayyim.com")
	if strings.Contains(w.DID, appHost+".etzhayyim.com") {
		return true
	}
	if strings.Contains(w.DisplayName, wd.Domain) {
		return true
	}
	return false
}

func firstNonEmpty(vals ...string) string {
	for _, v := range vals {
		if v != "" {
			return v
		}
	}
	return ""
}

func toStr(v any) string {
	if v == nil {
		return ""
	}
	return fmt.Sprintf("%v", v)
}

func toFloat(row []any, fallback float64) float64 {
	if len(row) == 0 || row[0] == nil {
		return fallback
	}
	switch v := row[0].(type) {
	case float64:
		return v
	case float32:
		return float64(v)
	case int:
		return float64(v)
	case int64:
		return float64(v)
	case int32:
		return float64(v)
	case json.Number:
		f, err := v.Float64()
		if err != nil {
			return fallback
		}
		return f
	default:
		var f float64
		if n, err := fmt.Sscanf(fmt.Sprint(v), "%f", &f); n == 1 && err == nil {
			return f
		}
		return fallback
	}
}

func toInt(row []any, idx int) int {
	if idx >= len(row) || row[idx] == nil {
		return 0
	}
	switch v := row[idx].(type) {
	case float64:
		return int(v)
	case int:
		return v
	case int64:
		return int(v)
	case int32:
		return int(v)
	case json.Number:
		n, _ := v.Int64()
		return int(n)
	case pgtype.Numeric:
		if f, err := v.Float64Value(); err == nil && f.Valid {
			return int(f.Float64)
		}
		return 0
	default:
		// Try string → int as last resort
		s := fmt.Sprint(v)
		if n, err := fmt.Sscanf(s, "%d", new(int)); n == 1 && err == nil {
			var i int
			fmt.Sscanf(s, "%d", &i)
			return i
		}
		return 0
	}
}

func truncStr(s string, maxLen int) string {
	if len(s) <= maxLen {
		return s
	}
	return s[:maxLen] + "..."
}

func setCoverageAuthHeaders(req *http.Request, orgOverride string) {
	setAuthHeaders(req)
	if org := strings.TrimSpace(orgOverride); org != "" {
		req.Header.Set("X-Gftd-Org-Id", org)
	}
}

func queryHeartbeatApps(client *http.Client, pdsURL, orgOverride string) ([]string, string, error) {
	tryFetch := func(base string) ([]string, string, error) {
		req, _ := http.NewRequest("POST", strings.TrimRight(base, "/")+"/xrpc/ai.gftd.pds.listHeartbeatApps", bytes.NewReader([]byte(`{}`)))
		req.Header.Set("Content-Type", "application/json")
		setCoverageAuthHeaders(req, orgOverride)

		resp, err := client.Do(req)
		if err != nil {
			return nil, "", fmt.Errorf("heartbeat list unreachable: %w", err)
		}
		body, _ := io.ReadAll(resp.Body)
		resp.Body.Close()
		if resp.StatusCode != 200 {
			return nil, "", fmt.Errorf("heartbeat list %d: %s", resp.StatusCode, truncStr(string(body), 200))
		}
		var parsed wcHeartbeatAppsResp
		if err := json.Unmarshal(body, &parsed); err != nil {
			return nil, "", fmt.Errorf("heartbeat list parse: %w", err)
		}
		if parsed.Source == "" {
			parsed.Source = "unknown"
		}
		return parsed.Apps, parsed.Source, nil
	}

	apps, source, err := tryFetch(pdsURL)
	if err == nil {
		return apps, source, nil
	}
	if fb, useFallback := fallbackPDSBase(pdsURL); useFallback {
		fallbackApps, fallbackSource, fbErr := tryFetch(fb)
		if fbErr == nil {
			if fallbackSource == "" || fallbackSource == "unknown" {
				fallbackSource = "fallback:pds"
			} else {
				fallbackSource = "fallback:pds:" + fallbackSource
			}
			return fallbackApps, fallbackSource, nil
		}
		return nil, "", fmt.Errorf("%v; fallback failed: %v", err, fbErr)
	}
	return nil, "", err
}

func applyHeartbeatAppFallback(appCount int, appResult *wcSqlResp, heartbeatApps []string) (int, *wcSqlResp, bool) {
	if appCount > 0 || len(heartbeatApps) == 0 {
		return appCount, appResult, false
	}
	seen := map[string]struct{}{}
	cleaned := make([]string, 0, len(heartbeatApps))
	for _, app := range heartbeatApps {
		app = strings.TrimSpace(app)
		if app == "" {
			continue
		}
		if _, exists := seen[app]; exists {
			continue
		}
		seen[app] = struct{}{}
		cleaned = append(cleaned, app)
	}
	if len(cleaned) == 0 {
		return appCount, appResult, false
	}
	appCount = len(cleaned)
	if appResult == nil || len(appResult.Rows) == 0 {
		appResult = &wcSqlResp{
			Columns: []string{"nanoid", "display_name", "did", "deploy_at"},
			Rows:    make([][]any, 0, len(cleaned)),
		}
		for _, app := range cleaned {
			appResult.Rows = append(appResult.Rows, []any{app, app, "did:web:" + app + ".etzhayyim.com", ""})
		}
	}
	return appCount, appResult, true
}

func applyCoverageSummaryFallback(didCount, profileCount int, appResult *wcSqlResp) (int, int) {
	if appResult == nil || len(appResult.Rows) == 0 {
		return didCount, profileCount
	}
	minCount := len(appResult.Rows)
	if didCount < minCount {
		didCount = minCount
	}
	if profileCount < minCount {
		profileCount = minCount
	}
	return didCount, profileCount
}

func appRowsFromLocal(localApps []localApp) *wcSqlResp {
	if len(localApps) == 0 {
		return nil
	}
	out := &wcSqlResp{
		Columns: []string{"nanoid", "display_name", "did", "deploy_at"},
		Rows:    make([][]any, 0, len(localApps)),
	}
	for _, la := range localApps {
		name := strings.TrimSpace(la.project)
		if name == "" {
			name = strings.TrimSpace(la.app)
		}
		out.Rows = append(out.Rows, []any{la.nanoid, name, la.did, ""})
	}
	return out
}

func buildRecordDomainCounts(recordByRepoResult *wcSqlResp) map[string]int {
	out := map[string]int{}
	if recordByRepoResult == nil {
		return out
	}
	for _, row := range recordByRepoResult.Rows {
		if len(row) < 2 {
			continue
		}
		repo := toStr(row[0])
		if repo == "" {
			continue
		}
		domainKey := extractDomainFromDID(repo)
		if domainKey == "" {
			continue
		}
		out[domainKey] += toInt(row, 1)
	}
	return out
}

func buildListRecordsDomainCounts(client *http.Client, pdsURL, token string, domains []worldDomain, hostScope map[string]bool) (map[string]int, map[string]int) {
	recordByDomain := map[string]int{}
	didByDomain := map[string]int{}
	if client == nil {
		return recordByDomain, didByDomain
	}
	hostToDomains := map[string][]worldDomain{}
	for _, wd := range domains {
		host := normalizeDomainLookup(strings.TrimSuffix(wd.App, ".etzhayyim.com"))
		if host == "" {
			continue
		}
		hostToDomains[host] = append(hostToDomains[host], wd)
	}
	if len(hostScope) > 0 {
		for host := range hostScope {
			host = normalizeDomainLookup(host)
			if host == "" || len(hostToDomains[host]) > 0 {
				continue
			}
			for _, wd := range domains {
				if matchesDomain(host, wd) {
					hostToDomains[host] = append(hostToDomains[host], wd)
				}
			}
		}
	}

	seenDomainURI := map[string]map[string]bool{}
	seenDomainEntity := map[string]map[string]bool{}
	seenDomainActor := map[string]map[string]bool{}
	for host, doms := range hostToDomains {
		if len(hostScope) > 0 && !hostScope[host] {
			continue
		}
		repo := "did:web:" + host + ".etzhayyim.com"
		for _, wd := range doms {
			if seenDomainURI[wd.Domain] == nil {
				seenDomainURI[wd.Domain] = map[string]bool{}
			}
			if seenDomainEntity[wd.Domain] == nil {
				seenDomainEntity[wd.Domain] = map[string]bool{}
			}
			if seenDomainActor[wd.Domain] == nil {
				seenDomainActor[wd.Domain] = map[string]bool{}
			}
			for _, col := range candidateCollectionsForDomain(wd, host) {
				entries := listCollectionRecordEntriesForRepo(client, pdsURL, token, repo, col, 500)
				for _, rec := range entries {
					uri := strings.TrimSpace(rec.URI)
					if uri == "" || seenDomainURI[wd.Domain][uri] {
						continue
					}
					seenDomainURI[wd.Domain][uri] = true
					entityKey := listRecordEntityKey(rec, uri)
					if !seenDomainEntity[wd.Domain][entityKey] {
						seenDomainEntity[wd.Domain][entityKey] = true
						recordByDomain[wd.Domain]++
					}
					actor := strings.TrimSpace(strVal(rec.Value["actorDid"]))
					if actor == "" {
						actor = atURIRepo(uri)
					}
					if actor == "" {
						actor = repo
					}
					if actor != "" && !seenDomainActor[wd.Domain][actor] {
						seenDomainActor[wd.Domain][actor] = true
						didByDomain[wd.Domain]++
					}
				}
			}
		}
	}
	return recordByDomain, didByDomain
}

func listRecordEntityKey(rec listRecordEntry, fallback string) string {
	if rec.Value != nil {
		candidates := []string{
			strVal(rec.Value["canonicalEntityId"]),
			strVal(rec.Value["canonical_entity_id"]),
			strVal(rec.Value["id"]),
			strVal(rec.Value["entityId"]),
			strVal(rec.Value["entity_id"]),
			strVal(rec.Value["code"]),
		}
		for _, c := range candidates {
			c = strings.TrimSpace(c)
			if c != "" {
				return c
			}
		}
	}
	return strings.TrimSpace(fallback)
}

func candidateCollectionsForDomain(wd worldDomain, hostHints ...string) []string {
	hosts := []string{normalizeDomainLookup(strings.TrimSuffix(wd.App, ".etzhayyim.com"))}
	for _, h := range hostHints {
		if nh := normalizeDomainLookup(h); nh != "" {
			hosts = append(hosts, nh)
		}
	}
	cands := []string{}
	for _, host := range hosts {
		if host == "" {
			continue
		}
		cands = append(cands, "ai.gftd.apps."+host+"."+strings.ToLower(strings.TrimSpace(wd.Domain)))
		if wd.DIDLabel != "" {
			cands = append(cands, "ai.gftd.apps."+host+"."+strings.ToLower(strings.TrimSpace(wd.DIDLabel)))
		}
		if wd.RecordLabel != "" {
			cands = append(cands, "ai.gftd.apps."+host+"."+strings.ToLower(strings.TrimSpace(wd.RecordLabel)))
		}
	}
	seen := map[string]bool{}
	out := make([]string, 0, len(cands))
	for _, c := range cands {
		c = strings.TrimSpace(strings.ToLower(c))
		if c == "" || seen[c] {
			continue
		}
		seen[c] = true
		out = append(out, c)
	}
	return out
}

func effectiveCollectedCount(didCount, recordCount int) int {
	if recordCount > didCount {
		return recordCount
	}
	return didCount
}

// vertexTableFallbackCount returns record count for domains whose rows live in
// a dedicated vertex table rather than vertex_did / vertex_other.
//
// ADR-0033: unfiltered counts on ≥10M row tables go through rw_table_stats.
// Filtered counts (e.g. status='ACTIVE') still execute a scan and require an
// index on the filter column to avoid tripping meta backpressure.
func vertexTableFallbackCount(domain string) (int64, string, error) {
	switch domain {
	case "legal_entity":
		ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
		defer cancel()
		pool, err := db.Pool(ctx)
		if err != nil {
			return 0, "", err
		}
		n, err := db.CountFromStats(ctx, pool, "vertex_legal_entity")
		if err != nil {
			return 0, "", err
		}
		return n, "vertex_table_stats", nil
	case "legal_entity_lei":
		// Filtered count; needs index on status to stay under meta backpressure.
		ctx, cancel := context.WithTimeout(context.Background(), 60*time.Second)
		defer cancel()
		res, err := db.RawQuery(ctx, "SELECT COUNT(*)::bigint AS cnt FROM vertex_legal_entity WHERE status = 'ACTIVE'")
		if err != nil {
			return 0, "", err
		}
		if len(res.Rows) == 0 {
			return 0, "vertex_table_direct", nil
		}
		return int64(toInt([]any{res.Rows[0]["cnt"]}, 0)), "vertex_table_direct", nil
	default:
		return 0, "", nil
	}
}

func buildHeartbeatDomainCounts(heartbeatApps []string, localApps []localApp) map[string]int {
	if len(heartbeatApps) == 0 || len(localApps) == 0 {
		return map[string]int{}
	}
	localByNanoid := map[string]localApp{}
	for _, la := range localApps {
		if strings.TrimSpace(la.nanoid) == "" {
			continue
		}
		localByNanoid[la.nanoid] = la
	}
	counts := map[string]int{}
	seenDomainApp := map[string]struct{}{}
	for _, nanoid := range heartbeatApps {
		la, ok := localByNanoid[nanoid]
		if !ok {
			continue
		}
		candidates := []string{
			strings.TrimSpace(la.project),
			extractDomainFromDID(la.did),
			strings.TrimSuffix(strings.TrimSpace(la.app), ".etzhayyim.com"),
		}
		for _, c := range candidates {
			if c == "" {
				continue
			}
			key := c + "|" + nanoid
			if _, exists := seenDomainApp[key]; exists {
				continue
			}
			seenDomainApp[key] = struct{}{}
			counts[c]++
		}
	}
	return counts
}

func inferOrgFromActiveDID(activeDID string) string {
	did := strings.TrimSpace(activeDID)
	if did == "" {
		return ""
	}
	if m := regexp.MustCompile(`^did:web:([^.]+)\.gftd\.ai$`).FindStringSubmatch(did); len(m) == 2 {
		return m[1]
	}
	if m := regexp.MustCompile(`^did:web:gftd\.ai:org:([a-zA-Z0-9._:-]+)$`).FindStringSubmatch(did); len(m) == 2 {
		return m[1]
	}
	if m := regexp.MustCompile(`^did:web:auth\.gftd\.ai:user:([a-zA-Z0-9._:-]+)$`).FindStringSubmatch(did); len(m) == 2 {
		return "user:" + m[1]
	}
	return ""
}

func queryProfileTopologyCounts(ctx context.Context) profileTopologyCounts {
	// Preferred source: materialized summary view.
	if res, err := db.RawQuery(ctx, `
		SELECT total_profiles, linked_actor_profiles, linked_did_profiles, fully_linked_profiles
		FROM mv_profile_identity_summary
		LIMIT 1
	`); err == nil && len(res.Rows) > 0 {
		row := res.Rows[0]
		return profileTopologyCounts{
			Total:       toInt([]any{row["total_profiles"]}, 0),
			LinkedActor: toInt([]any{row["linked_actor_profiles"]}, 0),
			LinkedDID:   toInt([]any{row["linked_did_profiles"]}, 0),
			LinkedBoth:  toInt([]any{row["fully_linked_profiles"]}, 0),
		}
	}

	// Fallback: derive directly from base tables.
	if res, err := db.RawQuery(ctx, `
		SELECT
		  COUNT(*)::bigint AS total_profiles,
		  SUM(CASE WHEN a.vertex_id IS NOT NULL THEN 1 ELSE 0 END)::bigint AS linked_actor_profiles,
		  SUM(CASE WHEN d.vertex_id IS NOT NULL THEN 1 ELSE 0 END)::bigint AS linked_did_profiles,
		  SUM(CASE WHEN a.vertex_id IS NOT NULL AND d.vertex_id IS NOT NULL THEN 1 ELSE 0 END)::bigint AS fully_linked_profiles
		FROM vertex_profile p
		LEFT JOIN vertex_actor a ON a.did = p.did
		LEFT JOIN vertex_did d ON d.did = p.did
	`); err == nil && len(res.Rows) > 0 {
		row := res.Rows[0]
		return profileTopologyCounts{
			Total:       toInt([]any{row["total_profiles"]}, 0),
			LinkedActor: toInt([]any{row["linked_actor_profiles"]}, 0),
			LinkedDID:   toInt([]any{row["linked_did_profiles"]}, 0),
			LinkedBoth:  toInt([]any{row["fully_linked_profiles"]}, 0),
		}
	}

	return profileTopologyCounts{}
}

// ── Text output ──

func printWorldCoverageText(r *worldCoverageReport, topN int) {
	fmt.Println("╔════════════════════════════════════════════════════════════════════════════════════════════════════════════╗")
	fmt.Println("║                              gftd coverage — World Coverage Analysis                                      ║")
	fmt.Println("╠════════════════════════════════════════════════════════════════════════════════════════════════════════════╣")
	fmt.Println()
	fmt.Printf("  PDS:          %s\n", r.PDS)
	fmt.Printf("  Evaluated:    %s\n", r.EvaluatedAt)
	if r.Auth.Mode != "" {
		authLine := r.Auth.Mode
		if r.Auth.OrgID != "" {
			authLine += " / org:" + r.Auth.OrgID
		}
		if r.Auth.ActiveDID != "" {
			authLine += " / did:" + r.Auth.ActiveDID
		}
		fmt.Printf("  Auth:         %s\n", authLine)
	}
	fmt.Println()
	fmt.Println("  Platform Summary")
	fmt.Println("  ────────────────────────────────────────────────")
	fmt.Printf("  Apps:             %d\n", r.Summary.TotalApps)
	fmt.Printf("  DIDs:             %d\n", r.Summary.TotalDIDs)
	fmt.Printf("  Records:          %d\n", r.Summary.TotalRecords)
	fmt.Printf("  Profiles:         %d\n", r.Summary.TotalProfiles)
	if r.Summary.TotalProfiles > 0 {
		fmt.Printf("  Profile Links:    actor=%d did=%d both=%d\n",
			r.Summary.ProfilesLinkedActor,
			r.Summary.ProfilesLinkedDID,
			r.Summary.ProfilesFullyLinked,
		)
	}
	if r.Summary.RecordByRepoTotal > 0 || r.Summary.RecordByCollectionTotal > 0 {
		fmt.Printf("  Record Sources: repo=%d, collection=%d\n", r.Summary.RecordByRepoTotal, r.Summary.RecordByCollectionTotal)
	}
	fmt.Println()

	// Sort domains by coverage descending
	sorted := make([]wcDomainResult, len(r.Domains))
	copy(sorted, r.Domains)
	sort.Slice(sorted, func(i, j int) bool {
		return sorted[i].Coverage > sorted[j].Coverage
	})

	fmt.Println("  Domain Coverage vs. World (with Gap Analysis)")
	fmt.Println("  ────────────────────────────────────────────────────────────────────────────────────────────────────────")
	fmt.Printf("  %-16s %10s %14s %10s %10s %14s  %s\n", "DOMAIN", "COLLECTED", "WORLD TOTAL", "COVERAGE", "GAP", "REMAINING", "BAR")
	fmt.Println("  ────────────────────────────────────────────────────────────────────────────────────────────────────────")
	for _, d := range sorted {
		covStr := "—"
		gapStr := "—"
		remStr := "—"
		if d.WorldTotal > 0 {
			covStr = formatCovPct(d.Coverage)
			gapStr = formatGapPct(d.Gap)
			remStr = formatNum(d.Remaining)
		}
		bar := coverageBarWC(d.Coverage, 15)
		fmt.Printf("  %-16s %10s %14s %10s %10s %14s  %s\n",
			d.Domain,
			formatNum(d.Collected),
			formatNum(d.WorldTotal),
			covStr,
			gapStr,
			remStr,
			bar)
	}
	fmt.Println("  ────────────────────────────────────────────────────────────────────────────────────────────────────────")
	overall := r.Summary.WorldCoverageOverall
	if overall == 0 && r.Summary.WorldCoverage > 0 {
		overall = r.Summary.WorldCoverage
	}
	fmt.Printf("  World Coverage Rate: %s  |  World Gap: %s\n", formatCovPct(overall), formatGapPct(1.0-overall))
	fmt.Printf("  World DID Coverage:  %s  |  World Record Coverage: %s\n", formatCovPct(r.Summary.WorldCoverageDID), formatCovPct(r.Summary.WorldCoverageRecord))
	if r.Summary.RecentSince != "" {
		fmt.Printf("  Recent Records (%s+): %s\n", r.Summary.RecentSince, formatNum(r.Summary.RecentRecords))
	}
	if len(r.Anomalies) > 0 {
		fmt.Printf("  Anomalies: %d (coverage_overflow)\n", len(r.Anomalies))
	}
	fmt.Println()

	// Gap summary by tier
	fmt.Println("  Gap Tier Summary")
	fmt.Println("  ────────────────────────────────────────────────────────────────────")
	tier50 := 0   // coverage >= 50%
	tier10 := 0   // 10-50%
	tier1 := 0    // 1-10%
	tier01 := 0   // 0.01-1%
	tierZero := 0 // < 0.01%
	totalRemaining := 0
	for _, d := range sorted {
		totalRemaining += d.Remaining
		pct := d.Coverage * 100
		switch {
		case pct >= 50:
			tier50++
		case pct >= 10:
			tier10++
		case pct >= 1:
			tier1++
		case pct >= 0.01:
			tier01++
		default:
			tierZero++
		}
	}
	fmt.Printf("  >= 50%%  (near complete):  %2d domains\n", tier50)
	fmt.Printf("  10-50%% (strong start):    %2d domains\n", tier10)
	fmt.Printf("   1-10%% (early stage):     %2d domains\n", tier1)
	fmt.Printf("  <1%%    (seed only):       %2d domains\n", tier01+tierZero)
	fmt.Printf("  Total remaining entities: %s\n", formatNum(totalRemaining))
	fmt.Println()

	// Top workers
	if topN > 0 && len(r.TopWorkers) > 0 {
		fmt.Println("  Top Workers by DID Count")
		fmt.Println("  ────────────────────────────────────────────────────────────────────────────────────────────────────────")
		fmt.Printf("  %-12s %-30s %-42s %6s\n", "NANOID", "NAME", "DID", "DIDs")
		fmt.Println("  ────────────────────────────────────────────────────────────────────────────────────────────────────────")
		shown := 0
		for _, w := range r.TopWorkers {
			if shown >= topN {
				break
			}
			name := w.DisplayName
			if len(name) > 30 {
				name = name[:27] + "..."
			}
			did := w.DID
			if len(did) > 42 {
				did = did[:39] + "..."
			}
			fmt.Printf("  %-12s %-30s %-42s %6d\n", w.Nanoid, name, did, w.DIDCount)
			shown++
		}
		fmt.Println("  ────────────────────────────────────────────────────────────────────────────────────────────────────────")
		fmt.Println()
	}

	fmt.Println("╚════════════════════════════════════════════════════════════════════════════════════════════════════════════╝")
}

func coverageBarWC(rate float64, width int) string {
	filled := int(rate * float64(width))
	if filled > width {
		filled = width
	}
	if filled < 0 {
		filled = 0
	}
	return "[" + strings.Repeat("█", filled) + strings.Repeat("░", width-filled) + "]"
}

func formatNum(n int) string {
	if n == 0 {
		return "0"
	}
	s := fmt.Sprintf("%d", n)
	if n < 1000 {
		return s
	}
	// Add commas
	var parts []string
	for i := len(s); i > 0; i -= 3 {
		start := i - 3
		if start < 0 {
			start = 0
		}
		parts = append([]string{s[start:i]}, parts...)
	}
	return strings.Join(parts, ",")
}

func formatCovPct(rate float64) string {
	pct := rate * 100
	if pct < 0.001 && pct > 0 {
		return fmt.Sprintf("%.2e%%", pct)
	}
	if pct < 0.01 {
		return fmt.Sprintf("%.4f%%", pct)
	}
	if pct < 1 {
		return fmt.Sprintf("%.3f%%", pct)
	}
	if pct >= 100 {
		return "100.0%"
	}
	return fmt.Sprintf("%.1f%%", pct)
}

func formatGapPct(rate float64) string {
	pct := rate * 100
	if pct <= 0 {
		return "0.0%"
	}
	if pct >= 99.99 {
		return "~100%"
	}
	if pct >= 99 {
		return fmt.Sprintf("%.1f%%", pct)
	}
	return fmt.Sprintf("%.1f%%", pct)
}

// ── graph.etzhayyim.com direct coverage mode ──

// runKagamiCoverage queries RisingWave GraphAr tables via graph.etzhayyim.com, bypassing PDS XRPC.
// Returns nil on success (report printed/encoded), non-nil to signal fallback to PDS.
func runKagamiCoverage(
	client *http.Client,
	cfg kagamiConfig,
	root string,
	report *worldCoverageReport,
	domainScope []worldDomain,
	allDomains []worldDomain,
	requestedDomain string,
	hasSince bool, sinceISO string, sinceAt time.Time,
	jsonOut bool,
	topN int,
) error {
	report.PDS = cfg.Endpoint
	_ = client // kagami HTTP client no longer used; kept for signature compatibility

	qctx, qcancel := context.WithTimeout(context.Background(), 60*time.Second)
	defer qcancel()
	qq, qerr := db.Q(qctx)
	if qerr != nil {
		return fmt.Errorf("risingwave: %w", qerr)
	}

	// Query 1: App count
	appCount64, err := qq.CountApps(qctx)
	if err != nil {
		return fmt.Errorf("count apps: %w", err)
	}
	appCount := int(appCount64)

	// Query 2: App list (for top workers)
	appListRows, err := qq.ListApps(qctx)
	if err != nil {
		fmt.Fprintf(os.Stderr, "warning: list apps: %v\n", err)
	}

	// Query 3: Profile count
	profileCount := 0
	profileTopo := profileTopologyCounts{}
	if requestedDomain == "" {
		profileTopo = queryProfileTopologyCounts(qctx)
		profileCount = profileTopo.Total
	}

	// Query 4: Coverage via migration 0025 `mv_world_coverage_live`.
	// The MV pre-joins dim_world_domain (405) × dim_app_host_alias (183) ×
	// vertex_profile / vertex_repo_record / dedicated vertex_* tables, producing
	// per-domain {did_count, record_count, vertex_count, collected} with
	// collected = GREATEST(did, record, vertex) to avoid triple-counting the
	// same entity. Single SQL read, no per-domain fallback needed.
	//
	// SSoT: 30-graph/graph-schema/migrations/0025_world_coverage_live_mv.ts
	type mvCoverageRow struct {
		didCount     int
		recordCount  int
		vertexCount  int
		collected    int
		coverageRate float64
	}
	mvByDomain := map[string]mvCoverageRow{}
	{
		res, err := db.RawQuery(qctx, `SELECT domain, did_count, record_count, vertex_count, collected, coverage_rate FROM mv_world_coverage_live`)
		if err != nil {
			fmt.Fprintf(os.Stderr, "warning: mv_world_coverage_live query failed: %v\n", err)
		} else {
			for _, row := range res.Rows {
				dom, _ := row["domain"].(string)
				if dom == "" {
					continue
				}
				mvByDomain[dom] = mvCoverageRow{
					didCount:     toInt([]any{row["did_count"]}, 0),
					recordCount:  toInt([]any{row["record_count"]}, 0),
					vertexCount:  toInt([]any{row["vertex_count"]}, 0),
					collected:    toInt([]any{row["collected"]}, 0),
					coverageRate: toFloat([]any{row["coverage_rate"]}, 0),
				}
			}
		}
	}
	didByDomain := map[string]int{}
	recordByDomain := map[string]int{}
	for dom, r := range mvByDomain {
		didByDomain[dom] = r.didCount
		recordByDomain[dom] = r.recordCount
	}

	// Query 5/6: Total record & DID counts
	// Use mv_world_coverage_live domain aggregates as the primary source of truth.
	// Profile fragments can be empty even when domain records are populated.
	totalRecords := 0
	totalDIDs := 0
	for _, v := range recordByDomain {
		totalRecords += v
	}
	for _, v := range didByDomain {
		totalDIDs += v
	}

	// Query 7: Recent records (if --since) — deferred until sqlc query is added
	_ = hasSince
	_ = sinceISO
	_ = sinceAt

	// Populate report summary
	report.Summary.TotalApps = appCount
	report.Summary.TotalDIDs = totalDIDs
	report.Summary.TotalRecords = totalRecords
	report.Summary.TotalProfiles = profileCount
	report.Summary.ProfilesLinkedActor = profileTopo.LinkedActor
	report.Summary.ProfilesLinkedDID = profileTopo.LinkedDID
	report.Summary.ProfilesFullyLinked = profileTopo.LinkedBoth

	// Top workers from app list
	for _, row := range appListRows {
		vid := row.VertexID.String
		did := row.Repo.String
		if did == "" {
			did = vid
		}
		w := wcWorkerResult{
			Nanoid:      vid,
			DisplayName: vid,
			DID:         did,
		}
		report.TopWorkers = append(report.TopWorkers, w)
	}

	// Build domain results
	totalWorldTarget := 0
	totalWorldCoveredDid := 0
	totalWorldCoveredRecord := 0
	anomalies := make([]wcAnomaly, 0)
	for _, wd := range allDomains {
		if requestedDomain != "" && wd.Domain != requestedDomain {
			continue
		}
		dr := wcDomainResult{
			Domain:      wd.Domain,
			App:         wd.App,
			WorldTotal:  wd.WorldTotal,
			Unit:        wd.Unit,
			Source:      wd.Source,
			DIDLabel:    wd.DIDLabel,
			RecordLabel: wd.RecordLabel,
		}

		if mv, ok := mvByDomain[wd.Domain]; ok {
			dr.DIDCount = mv.didCount
			dr.RecordCount = mv.recordCount
			dr.Collected = mv.collected // GREATEST(did, record, vertex) from MV
			dr.CountSource = "risingwave:mv_world_coverage_live"
		} else {
			dr.DIDCount = didByDomain[wd.Domain]
			dr.RecordCount = recordByDomain[wd.Domain]
			dr.Collected = effectiveCollectedCount(dr.DIDCount, dr.RecordCount)
			dr.CountSource = "risingwave:empty"
		}

		if wd.WorldTotal > 0 {
			dr.CoverageDID = float64(dr.DIDCount) / float64(wd.WorldTotal)
			dr.CoverageRec = float64(dr.RecordCount) / float64(wd.WorldTotal)
			dr.Coverage = float64(dr.Collected) / float64(wd.WorldTotal)
			if dr.Coverage > 1.0 {
				dr.Coverage = 1.0
			}
			if dr.CoverageDID > 1.0 {
				dr.CoverageDID = 1.0
			}
			if dr.CoverageRec > 1.0 {
				dr.CoverageRec = 1.0
			}
			dr.Gap = 1.0 - dr.Coverage
			dr.Remaining = wd.WorldTotal - dr.Collected
			if dr.Remaining < 0 {
				dr.Remaining = 0
			}
			if dr.Collected > wd.WorldTotal {
				anomalies = append(anomalies, wcAnomaly{
					Domain:     wd.Domain,
					Collected:  dr.Collected,
					WorldTotal: wd.WorldTotal,
					Kind:       "coverage_overflow",
					Detail:     "collected exceeds world total denominator",
				})
			}
		}
		report.Domains = append(report.Domains, dr)
		totalWorldTarget += wd.WorldTotal
		totalWorldCoveredDid += minInt(dr.DIDCount, wd.WorldTotal)
		totalWorldCoveredRecord += minInt(dr.RecordCount, wd.WorldTotal)
	}

	if totalWorldTarget > 0 {
		report.Summary.WorldCoverageDID = float64(totalWorldCoveredDid) / float64(totalWorldTarget)
		report.Summary.WorldCoverageRecord = float64(totalWorldCoveredRecord) / float64(totalWorldTarget)
		report.Summary.WorldCoverageOverall = 0.7*report.Summary.WorldCoverageDID + 0.3*report.Summary.WorldCoverageRecord
		report.Summary.WorldCoverage = report.Summary.WorldCoverageOverall
	}
	report.Anomalies = anomalies

	if len(report.TopWorkers) > topN {
		report.TopWorkers = report.TopWorkers[:topN]
	}

	if jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(report)
	}

	printWorldCoverageText(report, topN)
	return nil
}
