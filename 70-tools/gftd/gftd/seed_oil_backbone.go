package main

import (
	"context"
	"flag"
	"fmt"
	"os"
	"time"

	gftddb "github.com/etzhayyim/root/70-tools/gftd/gftd/db"
)

type oilCompanySeed struct {
	vertexID, name, companyType, hqCountry string
}

type oilBasinSeed struct {
	vertexID, basinCode, basinName, countryCode, basinType string
}

type oilFieldSeed struct {
	vertexID, fieldCode, basinCode, fieldType, operatorDID, countryCode string
}

type oilPipelineSeed struct {
	vertexID, pipelineCode, commodity, operatorDID, status string
	capacityBPD                                            int
	lengthKM                                               float64
}

type oilTerminalSeed struct {
	vertexID, terminalCode, terminalType, locode, operatorDID, status string
	storageCapacity                                                   int
}

type oilRefinerySeed struct {
	vertexID, refineryCode, operatorDID, countryCode, status string
	throughputBPD                                            int
	complexityIndex                                          float64
}

type oilBenchmarkSeed struct {
	vertexID, benchmarkCode, region, commodity, publisher string
}

type oilCrudeSeed struct {
	vertexID, gradeCode, benchmarkLink string
	apiGravity, sulfurPct              float64
}

type oilProductSeed struct {
	vertexID, productCode, productFamily, sulfurBand string
}

type oilCargoSeed struct {
	vertexID, cargoID, commodity, gradeCode, loadPort, dischargePort, laycan, status string
	quantity                                                                         int
}

type oilTradeSeed struct {
	vertexID, tradeID, traderDID, counterpartyDID, commodity, gradeCode, benchmarkCode, countryCode, unit, priceBasis, deliveryWindow, status string
	volume                                                                                                                                    int
}

type oilOfftakeContractSeed struct {
	vertexID, contractID, sellerDID, buyerDID, commodity, benchmarkCode, unit, deliveryTerm, countryCode, status string
	volume                                                                                                       int
}

type oilProductTerminalSeed struct {
	vertexID, terminalCode, locode, countryCode, operatorDID, productFamily, status string
	storageCapacity                                                                 int
}

type oilWholesaleHubSeed struct {
	vertexID, hubCode, countryCode, operatorDID, hubType, productFamily, status string
	throughputBPD                                                               int
}

type oilCoverageTargetSeed struct {
	targetKey, countryCode, segment, actorDID, app string
	targetCount, priority                          int
}

type oilEdgeSeed struct {
	edgeID, srcVID, dstVID, label, role string
}

const oilSeedDate = "2026-04-13"

func runSeedOilBackbone(args []string) error {
	fs := flag.NewFlagSet("seed oil-backbone", flag.ContinueOnError)
	envName := fs.String("env", "local", "Target environment: local or prod")
	urlFlag := fs.String("url", "", "Explicit PostgreSQL URL")
	dryRun := fs.Bool("dry-run", false, "print planned writes without executing")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	databaseURL, err := resolveDatabaseURL(*urlFlag, *envName)
	if err != nil {
		return err
	}
	if err := os.Setenv("DATABASE_URL", databaseURL); err != nil {
		return err
	}

	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Minute)
	defer cancel()

	companies := []oilCompanySeed{
		{"oilco:aramco", "Saudi Aramco", "noc", "SA"},
		{"oilco:exxonmobil", "ExxonMobil", "ioc", "US"},
		{"oilco:rosneft", "Rosneft", "noc", "RU"},
		{"oilco:adnoc", "ADNOC", "noc", "AE"},
		{"oilco:enterprise", "Enterprise Products", "midstream", "US"},
		{"oilco:vopak", "Vopak", "terminal", "SG"},
		{"oilco:vitol", "Vitol", "trader", "CH"},
	}
	basins := []oilBasinSeed{
		{"basin:ghawar", "GHWR", "Ghawar", "SA", "onshore"},
		{"basin:permian", "PRMN", "Permian", "US", "onshore"},
		{"basin:west-siberia", "WSIB", "West Siberia", "RU", "onshore"},
		{"basin:upper-zakum", "UZKM", "Upper Zakum", "AE", "offshore"},
	}
	fields := []oilFieldSeed{
		{"field:ain-dar", "AINDAR", "GHWR", "crude", "did:web:oil-upstream.etzhayyim.com", "SA"},
		{"field:midland-core", "MIDLAND", "PRMN", "crude", "did:web:oil-upstream.etzhayyim.com", "US"},
		{"field:prirazlomnoye", "PRIRAZ", "WSIB", "crude", "did:web:oil-upstream.etzhayyim.com", "RU"},
		{"field:upper-zakum-main", "UZMAIN", "UZKM", "crude", "did:web:oil-upstream.etzhayyim.com", "AE"},
	}
	pipelines := []oilPipelineSeed{
		{"pipe:east-west-sa", "EWSP", "crude", "did:web:oil-midstream.etzhayyim.com", "active", 5000000, 1200},
		{"pipe:permian-gulf", "PGX", "crude", "did:web:oil-midstream.etzhayyim.com", "active", 900000, 900},
		{"pipe:espo", "ESPO", "crude", "did:web:oil-midstream.etzhayyim.com", "active", 1600000, 4857},
		{"pipe:habshan-fujairah", "HOF", "crude", "did:web:oil-midstream.etzhayyim.com", "active", 1500000, 380},
	}
	terminals := []oilTerminalSeed{
		{"terminal:ras-tanura", "RASTAN", "export", "SA-DMM", "did:web:oil-midstream.etzhayyim.com", "active", 6500000},
		{"terminal:houston-ec", "HOU-EC", "export", "US-HOU", "did:web:oil-midstream.etzhayyim.com", "active", 4200000},
		{"terminal:kozmino", "KOZMIN", "export", "RU-VVO", "did:web:oil-midstream.etzhayyim.com", "active", 1000000},
		{"terminal:fujairah", "FUJAIR", "export", "AE-JEA", "did:web:oil-midstream.etzhayyim.com", "active", 7000000},
		{"terminal:jurong", "JURONG", "storage", "SG-SIN", "did:web:oil-midstream.etzhayyim.com", "active", 9500000},
	}
	refineries := []oilRefinerySeed{
		{"refinery:baytown", "BAYTOWN", "did:web:oil-refining.etzhayyim.com", "US", "active", 610000, 12.5},
		{"refinery:jamnagar", "JAMNAGAR", "did:web:oil-refining.etzhayyim.com", "IN", "active", 1240000, 21.1},
		{"refinery:zhenhai", "ZHENHAI", "did:web:oil-refining.etzhayyim.com", "CN", "active", 460000, 14.2},
	}
	benchmarks := []oilBenchmarkSeed{
		{"benchmark:brent", "BRENT", "Europe", "crude", "ICE"},
		{"benchmark:dubai", "DUBAI", "Middle East", "crude", "Platts"},
		{"benchmark:wti", "WTI", "North America", "crude", "CME"},
	}
	crudes := []oilCrudeSeed{
		{"crude:arab-light", "ARABL", "DUBAI", 33.4, 1.8},
		{"crude:wti-midland", "WTIMID", "WTI", 40.5, 0.2},
		{"crude:espo", "ESPO", "DUBAI", 34.8, 0.6},
	}
	products := []oilProductSeed{
		{"product:gasoil-10ppm", "GO10", "diesel", "10ppm"},
		{"product:gasoline-rbob", "RBOB", "gasoline", "low-sulfur"},
		{"product:jet-a1", "JETA1", "jet", "aviation"},
	}
	cargoes := []oilCargoSeed{
		{"cargo:adnoc-jet-001", "ADNOCJET001", "crude", "ARABL", "AE-JEA", "IN-JAM", "2026-04", "active", 2000000},
		{"cargo:permian-asia-001", "PERMIAN001", "crude", "WTIMID", "US-HOU", "SG-SIN", "2026-04", "active", 1800000},
		{"cargo:jurong-gasoil-001", "JURONGGO001", "product", "GO10", "SG-SIN", "JP-KWS", "2026-04", "active", 1200000},
		{"cargo:piraeus-diesel-001", "PIRAEUS001", "product", "GO10", "GR-PIR", "DE-HAM", "2026-04", "active", 950000},
	}
	trades := []oilTradeSeed{
		{"trade:vitol-brent-001", "VITOL-BRENT-001", "did:web:oil-trading.etzhayyim.com", "did:web:oil-refining.etzhayyim.com", "crude", "ARABL", "BRENT", "CH", "bbl", "dated-brent-plus", "2026-Q2", "active", 1000000},
		{"trade:trafi-wti-001", "TRAFI-WTI-001", "did:web:oil-trading.etzhayyim.com", "did:web:oil-distribution.etzhayyim.com", "crude", "WTIMID", "WTI", "SG", "bbl", "wti-houston-plus", "2026-Q2", "active", 850000},
		{"trade:adnoc-dubai-001", "ADNOC-DUBAI-001", "did:web:oil-trading.etzhayyim.com", "did:web:oil-refining.etzhayyim.com", "crude", "ARABL", "DUBAI", "AE", "bbl", "dubai-osp", "2026-Q2", "active", 1200000},
		{"trade:bp-brent-uk-001", "BP-BRENT-UK-001", "did:web:oil-trading.etzhayyim.com", "did:web:oil-distribution.etzhayyim.com", "crude", "ESPO", "BRENT", "GB", "bbl", "bfoet-minus", "2026-Q2", "active", 700000},
	}
	offtakes := []oilOfftakeContractSeed{
		{"offtake:aramco-jamnagar", "ARAMCO-JAM-001", "did:web:oil-trading.etzhayyim.com", "did:web:oil-refining.etzhayyim.com", "crude", "DUBAI", "bbl", "CIF West India", "AE", "active", 2400000},
		{"offtake:permian-japan", "PERMIAN-JP-001", "did:web:oil-trading.etzhayyim.com", "did:web:oil-distribution.etzhayyim.com", "crude", "WTI", "bbl", "FOB USGC", "US", "active", 1600000},
		{"offtake:espo-germany", "ESPO-DE-001", "did:web:oil-trading.etzhayyim.com", "did:web:oil-distribution.etzhayyim.com", "crude", "BRENT", "bbl", "DES Europe", "GB", "active", 900000},
	}
	productTerminals := []oilProductTerminalSeed{
		{"product-terminal:new-york-harbor", "NYH", "US-NYC", "US", "did:web:oil-distribution.etzhayyim.com", "gasoline", "active", 2800000},
		{"product-terminal:ningbo-products", "NBO-P", "CN-NGB", "CN", "did:web:oil-distribution.etzhayyim.com", "diesel", "active", 2400000},
		{"product-terminal:kawasaki-fuels", "KWSK-F", "JP-KWS", "JP", "did:web:oil-distribution.etzhayyim.com", "jet", "active", 1800000},
		{"product-terminal:ara-rotterdam", "ARA", "DE-HAM", "DE", "did:web:oil-distribution.etzhayyim.com", "diesel", "active", 3200000},
	}
	wholesaleHubs := []oilWholesaleHubSeed{
		{"wh-hub:usgc", "USGC", "US", "did:web:oil-distribution.etzhayyim.com", "rack", "gasoline", "active", 950000},
		{"wh-hub:east-china", "ECN", "CN", "did:web:oil-distribution.etzhayyim.com", "import", "diesel", "active", 820000},
		{"wh-hub:kanto", "KANTO", "JP", "did:web:oil-distribution.etzhayyim.com", "airport", "jet", "active", 410000},
		{"wh-hub:ara", "ARA", "DE", "did:web:oil-distribution.etzhayyim.com", "seaborne", "diesel", "active", 780000},
	}
	targets := []oilCoverageTargetSeed{
		{"SA:upstream", "SA", "upstream", "did:web:oil-upstream.etzhayyim.com", "oil-upstream.etzhayyim.com", 25, 1},
		{"US:upstream", "US", "upstream", "did:web:oil-upstream.etzhayyim.com", "oil-upstream.etzhayyim.com", 40, 1},
		{"RU:upstream", "RU", "upstream", "did:web:oil-upstream.etzhayyim.com", "oil-upstream.etzhayyim.com", 25, 1},
		{"AE:upstream", "AE", "upstream", "did:web:oil-upstream.etzhayyim.com", "oil-upstream.etzhayyim.com", 15, 1},
		{"US:midstream", "US", "midstream", "did:web:oil-midstream.etzhayyim.com", "oil-midstream.etzhayyim.com", 30, 1},
		{"AE:midstream", "AE", "midstream", "did:web:oil-midstream.etzhayyim.com", "oil-midstream.etzhayyim.com", 12, 1},
		{"SG:midstream", "SG", "midstream", "did:web:oil-midstream.etzhayyim.com", "oil-midstream.etzhayyim.com", 10, 1},
		{"US:refining", "US", "refining", "did:web:oil-refining.etzhayyim.com", "oil-refining.etzhayyim.com", 25, 1},
		{"CN:refining", "CN", "refining", "did:web:oil-refining.etzhayyim.com", "oil-refining.etzhayyim.com", 20, 1},
		{"IN:refining", "IN", "refining", "did:web:oil-refining.etzhayyim.com", "oil-refining.etzhayyim.com", 12, 1},
		{"CH:trading", "CH", "trading", "did:web:oil-trading.etzhayyim.com", "oil-trading.etzhayyim.com", 10, 1},
		{"SG:trading", "SG", "trading", "did:web:oil-trading.etzhayyim.com", "oil-trading.etzhayyim.com", 10, 1},
		{"AE:trading", "AE", "trading", "did:web:oil-trading.etzhayyim.com", "oil-trading.etzhayyim.com", 8, 1},
		{"GB:trading", "GB", "trading", "did:web:oil-trading.etzhayyim.com", "oil-trading.etzhayyim.com", 8, 1},
		{"GR:shipping", "GR", "shipping", "did:web:oil-shipping.etzhayyim.com", "oil-shipping.etzhayyim.com", 15, 1},
		{"SG:shipping", "SG", "shipping", "did:web:oil-shipping.etzhayyim.com", "oil-shipping.etzhayyim.com", 12, 1},
		{"AE:shipping", "AE", "shipping", "did:web:oil-shipping.etzhayyim.com", "oil-shipping.etzhayyim.com", 12, 1},
		{"US:distribution", "US", "distribution", "did:web:oil-distribution.etzhayyim.com", "oil-distribution.etzhayyim.com", 20, 1},
		{"CN:distribution", "CN", "distribution", "did:web:oil-distribution.etzhayyim.com", "oil-distribution.etzhayyim.com", 20, 1},
		{"JP:distribution", "JP", "distribution", "did:web:oil-distribution.etzhayyim.com", "oil-distribution.etzhayyim.com", 10, 1},
		{"DE:distribution", "DE", "distribution", "did:web:oil-distribution.etzhayyim.com", "oil-distribution.etzhayyim.com", 10, 1},
	}
	operates := []oilEdgeSeed{
		{"operates:aramco-ain-dar", "oilco:aramco", "field:ain-dar", "operates", "operator"},
		{"operates:exxon-permian", "oilco:exxonmobil", "field:midland-core", "operates", "operator"},
		{"operates:rosneft-priraz", "oilco:rosneft", "field:prirazlomnoye", "operates", "operator"},
		{"operates:adnoc-zakum", "oilco:adnoc", "field:upper-zakum-main", "operates", "operator"},
		{"operates:enterprise-pgx", "oilco:enterprise", "pipe:permian-gulf", "operates", "operator"},
		{"operates:vopak-jurong", "oilco:vopak", "terminal:jurong", "operates", "operator"},
	}
	feeds := []struct {
		edgeID, srcVID, dstVID, label, commodity, unit string
		capacity                                       int
	}{
		{"feeds:ain-dar-east-west", "field:ain-dar", "pipe:east-west-sa", "feeds", "crude", "bpd", 5000000},
		{"feeds:permian-pgx", "field:midland-core", "pipe:permian-gulf", "feeds", "crude", "bpd", 900000},
		{"feeds:priraz-espo", "field:prirazlomnoye", "pipe:espo", "feeds", "crude", "bpd", 1600000},
		{"feeds:zakum-hof", "field:upper-zakum-main", "pipe:habshan-fujairah", "feeds", "crude", "bpd", 1500000},
	}
	flows := []struct {
		edgeID, srcVID, dstVID, label, commodity, unit, timeBucket string
		volume                                                     int
	}{
		{"flows:east-west-ras-tanura", "pipe:east-west-sa", "terminal:ras-tanura", "flowsTo", "crude", "bpd", "2026-04", 5000000},
		{"flows:pgx-houston", "pipe:permian-gulf", "terminal:houston-ec", "flowsTo", "crude", "bpd", "2026-04", 900000},
		{"flows:espo-kozmino", "pipe:espo", "terminal:kozmino", "flowsTo", "crude", "bpd", "2026-04", 1600000},
		{"flows:hof-fujairah", "pipe:habshan-fujairah", "terminal:fujairah", "flowsTo", "crude", "bpd", "2026-04", 1500000},
		{"flows:fujairah-jamnagar", "terminal:fujairah", "refinery:jamnagar", "flowsTo", "crude", "bpd", "2026-04", 650000},
		{"flows:houston-baytown", "terminal:houston-ec", "refinery:baytown", "flowsTo", "crude", "bpd", "2026-04", 550000},
		{"flows:jurong-zhenhai", "terminal:jurong", "refinery:zhenhai", "flowsTo", "crude", "bpd", "2026-04", 300000},
	}
	pricedAgainst := []struct {
		edgeID, srcVID, dstVID, label, basis string
	}{
		{"priced:vitol-brent-001", "trade:vitol-brent-001", "benchmark:brent", "pricedAgainst", "dated-brent-plus"},
		{"priced:trafi-wti-001", "trade:trafi-wti-001", "benchmark:wti", "pricedAgainst", "wti-houston-plus"},
		{"priced:adnoc-dubai-001", "trade:adnoc-dubai-001", "benchmark:dubai", "pricedAgainst", "dubai-osp"},
		{"priced:bp-brent-uk-001", "trade:bp-brent-uk-001", "benchmark:brent", "pricedAgainst", "bfoet-minus"},
	}
	constrainedBy := []struct {
		edgeID, srcVID, dstVID, label, severity, status string
	}{
		{"constraint:trade-fujairah", "trade:adnoc-dubai-001", "terminal:fujairah", "constrainedBy", "medium", "open"},
		{"constraint:trade-jurong", "trade:trafi-wti-001", "terminal:jurong", "constrainedBy", "medium", "open"},
		{"constraint:dist-ara", "product-terminal:ara-rotterdam", "wh-hub:ara", "constrainedBy", "low", "monitored"},
	}

	fmt.Printf("oil backbone seed target: %s\n", redactURL(databaseURL))
	fmt.Printf("  companies=%d basins=%d fields=%d pipelines=%d terminals=%d refineries=%d cargoes=%d trades=%d product_terminals=%d\n",
		len(companies), len(basins), len(fields), len(pipelines), len(terminals), len(refineries), len(cargoes), len(trades), len(productTerminals))
	if *dryRun {
		return nil
	}

	pool, err := gftddb.Pool(ctx)
	if err != nil {
		return err
	}

	tx, err := pool.Begin(ctx)
	if err != nil {
		return err
	}
	defer tx.Rollback(ctx)

	for _, row := range companies {
		if _, err := tx.Exec(ctx, `DELETE FROM vertex_oil_company WHERE vertex_id = $1`, row.vertexID); err != nil {
			return err
		}
		if _, err := tx.Exec(ctx, `
INSERT INTO vertex_oil_company (vertex_id, created_date, owner_did, did, repo, name, company_type, hq_country, sanctions_status, status, collection)
VALUES ($1, $2, 'did:web:oil-coverage.etzhayyim.com', 'did:web:oil-coverage.etzhayyim.com', 'did:web:oil-coverage.etzhayyim.com', $3, $4, $5, 'clear', 'active', 'ai.gftd.apps.oil.coverage.company')`,
			row.vertexID, oilSeedDate, row.name, row.companyType, row.hqCountry); err != nil {
			return err
		}
	}
	for _, row := range basins {
		if _, err := tx.Exec(ctx, `DELETE FROM vertex_oil_basin WHERE vertex_id = $1`, row.vertexID); err != nil {
			return err
		}
		if _, err := tx.Exec(ctx, `
INSERT INTO vertex_oil_basin (vertex_id, created_date, owner_did, repo, basin_code, basin_name, country_code, basin_type, status, collection)
VALUES ($1, $2, 'did:web:oil-upstream.etzhayyim.com', 'did:web:oil-upstream.etzhayyim.com', $3, $4, $5, $6, 'active', 'ai.gftd.apps.oilUpstream.basin')`,
			row.vertexID, oilSeedDate, row.basinCode, row.basinName, row.countryCode, row.basinType); err != nil {
			return err
		}
	}
	for _, row := range fields {
		if _, err := tx.Exec(ctx, `DELETE FROM vertex_oil_field WHERE vertex_id = $1`, row.vertexID); err != nil {
			return err
		}
		if _, err := tx.Exec(ctx, `
INSERT INTO vertex_oil_field (vertex_id, created_date, owner_did, repo, field_code, basin_code, field_type, operator_did, country_code, status, collection)
VALUES ($1, $2, 'did:web:oil-upstream.etzhayyim.com', 'did:web:oil-upstream.etzhayyim.com', $3, $4, $5, $6, $7, 'active', 'ai.gftd.apps.oilUpstream.field')`,
			row.vertexID, oilSeedDate, row.fieldCode, row.basinCode, row.fieldType, row.operatorDID, row.countryCode); err != nil {
			return err
		}
	}
	for _, row := range pipelines {
		if _, err := tx.Exec(ctx, `DELETE FROM vertex_oil_pipeline WHERE vertex_id = $1`, row.vertexID); err != nil {
			return err
		}
		if _, err := tx.Exec(ctx, `
INSERT INTO vertex_oil_pipeline (vertex_id, created_date, owner_did, repo, pipeline_code, commodity, operator_did, capacity_bpd, length_km, status, collection)
VALUES ($1, $2, 'did:web:oil-midstream.etzhayyim.com', 'did:web:oil-midstream.etzhayyim.com', $3, $4, $5, $6, $7, $8, 'ai.gftd.apps.oilMidstream.pipeline')`,
			row.vertexID, oilSeedDate, row.pipelineCode, row.commodity, row.operatorDID, row.capacityBPD, row.lengthKM, row.status); err != nil {
			return err
		}
	}
	for _, row := range terminals {
		if _, err := tx.Exec(ctx, `DELETE FROM vertex_oil_terminal WHERE vertex_id = $1`, row.vertexID); err != nil {
			return err
		}
		if _, err := tx.Exec(ctx, `
INSERT INTO vertex_oil_terminal (vertex_id, created_date, owner_did, repo, terminal_code, terminal_type, locode, operator_did, storage_capacity, status, collection)
VALUES ($1, $2, 'did:web:oil-midstream.etzhayyim.com', 'did:web:oil-midstream.etzhayyim.com', $3, $4, $5, $6, $7, $8, 'ai.gftd.apps.oilMidstream.terminal')`,
			row.vertexID, oilSeedDate, row.terminalCode, row.terminalType, row.locode, row.operatorDID, row.storageCapacity, row.status); err != nil {
			return err
		}
	}
	for _, row := range refineries {
		if _, err := tx.Exec(ctx, `DELETE FROM vertex_refinery WHERE vertex_id = $1`, row.vertexID); err != nil {
			return err
		}
		if _, err := tx.Exec(ctx, `
INSERT INTO vertex_refinery (vertex_id, created_date, owner_did, repo, refinery_code, operator_did, throughput_bpd, complexity_index, country_code, status, collection)
VALUES ($1, $2, 'did:web:oil-refining.etzhayyim.com', 'did:web:oil-refining.etzhayyim.com', $3, $4, $5, $6, $7, $8, 'ai.gftd.apps.oilRefining.refinery')`,
			row.vertexID, oilSeedDate, row.refineryCode, row.operatorDID, row.throughputBPD, row.complexityIndex, row.countryCode, row.status); err != nil {
			return err
		}
	}
	for _, row := range benchmarks {
		if _, err := tx.Exec(ctx, `DELETE FROM vertex_pricing_benchmark WHERE vertex_id = $1`, row.vertexID); err != nil {
			return err
		}
		if _, err := tx.Exec(ctx, `
INSERT INTO vertex_pricing_benchmark (vertex_id, created_date, owner_did, repo, benchmark_code, region, commodity, publisher, status, collection)
VALUES ($1, $2, 'did:web:oil-coverage.etzhayyim.com', 'did:web:oil-coverage.etzhayyim.com', $3, $4, $5, $6, 'active', 'ai.gftd.apps.oil.coverage.benchmark')`,
			row.vertexID, oilSeedDate, row.benchmarkCode, row.region, row.commodity, row.publisher); err != nil {
			return err
		}
	}
	for _, row := range crudes {
		if _, err := tx.Exec(ctx, `DELETE FROM vertex_crude_grade WHERE vertex_id = $1`, row.vertexID); err != nil {
			return err
		}
		if _, err := tx.Exec(ctx, `
INSERT INTO vertex_crude_grade (vertex_id, created_date, owner_did, repo, grade_code, api_gravity, sulfur_pct, benchmark_link, status, collection)
VALUES ($1, $2, 'did:web:oil-coverage.etzhayyim.com', 'did:web:oil-coverage.etzhayyim.com', $3, $4, $5, $6, 'active', 'ai.gftd.apps.oil.coverage.crudeGrade')`,
			row.vertexID, oilSeedDate, row.gradeCode, row.apiGravity, row.sulfurPct, row.benchmarkLink); err != nil {
			return err
		}
	}
	for _, row := range products {
		if _, err := tx.Exec(ctx, `DELETE FROM vertex_product_grade WHERE vertex_id = $1`, row.vertexID); err != nil {
			return err
		}
		if _, err := tx.Exec(ctx, `
INSERT INTO vertex_product_grade (vertex_id, created_date, owner_did, repo, product_code, product_family, sulfur_band, status, collection)
VALUES ($1, $2, 'did:web:oil-coverage.etzhayyim.com', 'did:web:oil-coverage.etzhayyim.com', $3, $4, $5, 'active', 'ai.gftd.apps.oil.coverage.productGrade')`,
			row.vertexID, oilSeedDate, row.productCode, row.productFamily, row.sulfurBand); err != nil {
			return err
		}
	}
	for _, row := range cargoes {
		if _, err := tx.Exec(ctx, `DELETE FROM vertex_oil_cargo WHERE vertex_id = $1`, row.vertexID); err != nil {
			return err
		}
		if _, err := tx.Exec(ctx, `
INSERT INTO vertex_oil_cargo (vertex_id, created_date, owner_did, repo, cargo_id, commodity, grade_code, quantity, load_port, discharge_port, laycan, status, collection)
VALUES ($1, $2, 'did:web:oil-shipping.etzhayyim.com', 'did:web:oil-shipping.etzhayyim.com', $3, $4, $5, $6, $7, $8, $9, $10, 'ai.gftd.apps.oilShipping.cargo')`,
			row.vertexID, oilSeedDate, row.cargoID, row.commodity, row.gradeCode, row.quantity, row.loadPort, row.dischargePort, row.laycan, row.status); err != nil {
			return err
		}
	}
	for _, row := range trades {
		if _, err := tx.Exec(ctx, `DELETE FROM vertex_oil_trade WHERE vertex_id = $1`, row.vertexID); err != nil {
			return err
		}
		if _, err := tx.Exec(ctx, `
INSERT INTO vertex_oil_trade (vertex_id, created_date, owner_did, repo, trade_id, trader_did, counterparty_did, commodity, grade_code, benchmark_code, country_code, volume, unit, price_basis, delivery_window, status, collection)
VALUES ($1, $2, 'did:web:oil-trading.etzhayyim.com', 'did:web:oil-trading.etzhayyim.com', $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, 'ai.gftd.apps.oilTrading.trade')`,
			row.vertexID, oilSeedDate, row.tradeID, row.traderDID, row.counterpartyDID, row.commodity, row.gradeCode, row.benchmarkCode, row.countryCode, row.volume, row.unit, row.priceBasis, row.deliveryWindow, row.status); err != nil {
			return err
		}
	}
	for _, row := range offtakes {
		if _, err := tx.Exec(ctx, `DELETE FROM vertex_offtake_contract WHERE vertex_id = $1`, row.vertexID); err != nil {
			return err
		}
		if _, err := tx.Exec(ctx, `
INSERT INTO vertex_offtake_contract (vertex_id, created_date, owner_did, repo, contract_id, seller_did, buyer_did, commodity, benchmark_code, volume, unit, delivery_term, country_code, status, collection)
VALUES ($1, $2, 'did:web:oil-trading.etzhayyim.com', 'did:web:oil-trading.etzhayyim.com', $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, 'ai.gftd.apps.oilTrading.offtakeContract')`,
			row.vertexID, oilSeedDate, row.contractID, row.sellerDID, row.buyerDID, row.commodity, row.benchmarkCode, row.volume, row.unit, row.deliveryTerm, row.countryCode, row.status); err != nil {
			return err
		}
	}
	for _, row := range productTerminals {
		if _, err := tx.Exec(ctx, `DELETE FROM vertex_product_terminal WHERE vertex_id = $1`, row.vertexID); err != nil {
			return err
		}
		if _, err := tx.Exec(ctx, `
INSERT INTO vertex_product_terminal (vertex_id, created_date, owner_did, repo, terminal_code, locode, country_code, operator_did, product_family, storage_capacity, status, collection)
VALUES ($1, $2, 'did:web:oil-distribution.etzhayyim.com', 'did:web:oil-distribution.etzhayyim.com', $3, $4, $5, $6, $7, $8, $9, 'ai.gftd.apps.oilDistribution.productTerminal')`,
			row.vertexID, oilSeedDate, row.terminalCode, row.locode, row.countryCode, row.operatorDID, row.productFamily, row.storageCapacity, row.status); err != nil {
			return err
		}
	}
	for _, row := range wholesaleHubs {
		if _, err := tx.Exec(ctx, `DELETE FROM vertex_wholesale_hub WHERE vertex_id = $1`, row.vertexID); err != nil {
			return err
		}
		if _, err := tx.Exec(ctx, `
INSERT INTO vertex_wholesale_hub (vertex_id, created_date, owner_did, repo, hub_code, country_code, operator_did, hub_type, product_family, throughput_bpd, status, collection)
VALUES ($1, $2, 'did:web:oil-distribution.etzhayyim.com', 'did:web:oil-distribution.etzhayyim.com', $3, $4, $5, $6, $7, $8, $9, 'ai.gftd.apps.oilDistribution.wholesaleHub')`,
			row.vertexID, oilSeedDate, row.hubCode, row.countryCode, row.operatorDID, row.hubType, row.productFamily, row.throughputBPD, row.status); err != nil {
			return err
		}
	}
	if _, err := tx.Exec(ctx, `DELETE FROM dim_oil_coverage_target`); err != nil {
		return err
	}
	for _, row := range targets {
		if _, err := tx.Exec(ctx, `
INSERT INTO dim_oil_coverage_target (target_key, country_code, segment, actor_did, app, target_count, priority)
VALUES ($1, $2, $3, $4, $5, $6, $7)`,
			row.targetKey, row.countryCode, row.segment, row.actorDID, row.app, row.targetCount, row.priority); err != nil {
			return err
		}
	}
	for _, row := range operates {
		if _, err := tx.Exec(ctx, `DELETE FROM edge_operates WHERE edge_id = $1`, row.edgeID); err != nil {
			return err
		}
		if _, err := tx.Exec(ctx, `
INSERT INTO edge_operates (edge_id, src_vid, dst_vid, label, source_did, created_date, owner_did)
VALUES ($1, $2, $3, $4, 'did:web:oil-coverage.etzhayyim.com', $5, 'did:web:oil-coverage.etzhayyim.com')`,
			row.edgeID, row.srcVID, row.dstVID, row.label, oilSeedDate); err != nil {
			return err
		}
	}
	for _, row := range feeds {
		if _, err := tx.Exec(ctx, `DELETE FROM edge_feeds WHERE edge_id = $1`, row.edgeID); err != nil {
			return err
		}
		if _, err := tx.Exec(ctx, `
INSERT INTO edge_feeds (edge_id, src_vid, dst_vid, created_date, owner_did, label, commodity, capacity, unit)
VALUES ($1, $2, $3, $4, 'did:web:oil-upstream.etzhayyim.com', $5, $6, $7, $8)`,
			row.edgeID, row.srcVID, row.dstVID, oilSeedDate, row.label, row.commodity, row.capacity, row.unit); err != nil {
			return err
		}
	}
	for _, row := range flows {
		if _, err := tx.Exec(ctx, `DELETE FROM edge_flows_to WHERE edge_id = $1`, row.edgeID); err != nil {
			return err
		}
		if _, err := tx.Exec(ctx, `
INSERT INTO edge_flows_to (edge_id, src_vid, dst_vid, created_date, owner_did, label, commodity, volume, unit, time_bucket)
VALUES ($1, $2, $3, $4, 'did:web:oil-midstream.etzhayyim.com', $5, $6, $7, $8, $9)`,
			row.edgeID, row.srcVID, row.dstVID, oilSeedDate, row.label, row.commodity, row.volume, row.unit, row.timeBucket); err != nil {
			return err
		}
	}
	for _, row := range pricedAgainst {
		if _, err := tx.Exec(ctx, `DELETE FROM edge_priced_against WHERE edge_id = $1`, row.edgeID); err != nil {
			return err
		}
		if _, err := tx.Exec(ctx, `
INSERT INTO edge_priced_against (edge_id, src_vid, dst_vid, created_date, owner_did, label, basis)
VALUES ($1, $2, $3, $4, 'did:web:oil-trading.etzhayyim.com', $5, $6)`,
			row.edgeID, row.srcVID, row.dstVID, oilSeedDate, row.label, row.basis); err != nil {
			return err
		}
	}
	for _, row := range constrainedBy {
		if _, err := tx.Exec(ctx, `DELETE FROM edge_constrained_by WHERE edge_id = $1`, row.edgeID); err != nil {
			return err
		}
		if _, err := tx.Exec(ctx, `
INSERT INTO edge_constrained_by (edge_id, src_vid, dst_vid, created_date, owner_did, label, severity, status)
VALUES ($1, $2, $3, $4, 'did:web:oil-distribution.etzhayyim.com', $5, $6, $7)`,
			row.edgeID, row.srcVID, row.dstVID, oilSeedDate, row.label, row.severity, row.status); err != nil {
			return err
		}
	}
	if err := tx.Commit(ctx); err != nil {
		return err
	}

	fmt.Println("oil backbone seed complete")
	return nil
}
