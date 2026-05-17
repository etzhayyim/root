package main

import (
	"context"
	"flag"
	"fmt"
	"os"
	"time"

	gftddb "github.com/etzhayyim/root/70-tools/gftd/gftd/db"
)

type naphthaMarketNodeSeed struct {
	vertexID, nodeCode, nodeKind, displayName, countryCode, locode, operatorDID, refineryCode, productCode, status string
	capacityTonnesDay                                                                                              int
}

type naphthaProductSeed struct {
	vertexID, productCode, productFamily, sulfurBand string
}

type naphthaCargoSeed struct {
	vertexID, cargoID, gradeCode, originVID, destinationVID, loadPort, dischargePort, vesselIMO, laycanStart, laycanEnd, status string
	quantityTonnes                                                                                                              int
}

type naphthaPriceSeed struct {
	vertexID, assessmentID, benchmarkCode, region, gradeCode, assessedAt, publisher, status string
	priceUSDTonne, spreadToBrentUSDBBL                                                      float64
}

type naphthaDemandSeed struct {
	vertexID, demandID, consumerVID, productFamily, substitutionFeedstock, effectiveFrom, effectiveTo, status string
	demandTonnesDay                                                                                           int
}

type naphthaSupplyLinkSeed struct {
	edgeID, srcVID, dstVID, relationship, gradeCode, contractType, status string
	capacityTonnesDay                                                     int
}

type naphthaCargoRouteSeed struct {
	edgeID, srcVID, dstVID, cargoVID, routeRole, eventAt, status string
}

type naphthaDerivativeSeed struct {
	edgeID, srcVID, dstVID, derivativeFamily, status string
	conversionYieldPct                               float64
}

const naphthaSeedDate = "2026-05-14"
const naphthaActorDID = "did:web:naphtha-supply.etzhayyim.com"
const naphthaOrgDID = "did:web:etzhayyim"

func runSeedNaphthaSupply(args []string) error {
	fs := flag.NewFlagSet("seed naphtha-supply", flag.ContinueOnError)
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

	products := []naphthaProductSeed{
		{"product:naphtha-light", "NAPH-L", "naphtha", "light"},
		{"product:naphtha-heavy", "NAPH-H", "naphtha", "heavy"},
		{"product:ethylene", "C2", "olefin", "polymer-grade"},
		{"product:propylene", "C3", "olefin", "polymer-grade"},
	}
	nodes := []naphthaMarketNodeSeed{
		{"naphtha-node:baytown-refinery", "BAYTOWN-NAPH", "refinery", "Baytown refinery naphtha splitter", "US", "US-HOU", "did:web:oil-refining.etzhayyim.com", "BAYTOWN", "NAPH-L", "active", 6500},
		{"naphtha-node:jamnagar-refinery", "JAMNAGAR-NAPH", "refinery", "Jamnagar refinery naphtha export", "IN", "IN-JAM", "did:web:oil-refining.etzhayyim.com", "JAMNAGAR", "NAPH-L", "active", 14000},
		{"naphtha-node:zhenhai-refinery", "ZHENHAI-NAPH", "refinery", "Zhenhai refinery naphtha stream", "CN", "CN-NGB", "did:web:oil-refining.etzhayyim.com", "ZHENHAI", "NAPH-H", "active", 7000},
		{"naphtha-node:jurong-terminal", "JURONG-NAPH", "terminal", "Jurong naphtha storage terminal", "SG", "SG-SIN", "did:web:oil-midstream.etzhayyim.com", "", "NAPH-L", "active", 9000},
		{"naphtha-node:rotterdam-terminal", "ARA-NAPH", "terminal", "ARA Rotterdam naphtha hub", "NL", "NL-RTM", "did:web:oil-midstream.etzhayyim.com", "", "NAPH-L", "active", 8500},
		{"naphtha-node:yeosu-cracker", "YEOSU-C2", "steam_cracker", "Yeosu steam cracker", "KR", "KR-YOS", "did:web:petrochem.etzhayyim.com", "", "NAPH-L", "active", 5200},
		{"naphtha-node:chiba-cracker", "CHIBA-C2", "steam_cracker", "Chiba steam cracker", "JP", "JP-CHB", "did:web:petrochem.etzhayyim.com", "", "NAPH-L", "active", 3600},
	}
	cargoes := []naphthaCargoSeed{
		{"naphtha-cargo:jamnagar-yeosu-001", "JAM-YOS-001", "NAPH-L", "naphtha-node:jamnagar-refinery", "naphtha-node:yeosu-cracker", "IN-JAM", "KR-YOS", "9321483", "2026-05-10", "2026-05-16", "in_transit", 55000},
		{"naphtha-cargo:jurong-chiba-001", "JUR-CHB-001", "NAPH-L", "naphtha-node:jurong-terminal", "naphtha-node:chiba-cracker", "SG-SIN", "JP-CHB", "9485590", "2026-05-12", "2026-05-18", "nominated", 35000},
		{"naphtha-cargo:baytown-rotterdam-001", "BAY-RTM-001", "NAPH-H", "naphtha-node:baytown-refinery", "naphtha-node:rotterdam-terminal", "US-HOU", "NL-RTM", "9753181", "2026-05-08", "2026-05-14", "loaded", 42000},
	}
	prices := []naphthaPriceSeed{
		{"naphtha-price:mopj-latest", "MOPJ-2026-05-14", "MOPJ-NAPHTHA", "Asia", "NAPH-L", "2026-05-14T00:00:00Z", "Platts", "active", 690.50, -2.50},
		{"naphtha-price:cif-nwe-latest", "CIF-NWE-2026-05-14", "CIF-NWE-NAPHTHA", "Europe", "NAPH-L", "2026-05-14T00:00:00Z", "Argus", "active", 675.25, -8.00},
		{"naphtha-price:usgc-latest", "USGC-2026-05-14", "USGC-NAPHTHA", "North America", "NAPH-H", "2026-05-14T00:00:00Z", "OPIS", "active", 650.75, -18.25},
	}
	demands := []naphthaDemandSeed{
		{"naphtha-demand:yeosu-may26", "YEOSU-2026-05", "naphtha-node:yeosu-cracker", "olefin", "LPG", "2026-05-01", "2026-05-31", "active", 5100},
		{"naphtha-demand:chiba-may26", "CHIBA-2026-05", "naphtha-node:chiba-cracker", "olefin", "ethane", "2026-05-01", "2026-05-31", "active", 3400},
	}
	supplyLinks := []naphthaSupplyLinkSeed{
		{"naphtha-supply:jamnagar-jurong", "naphtha-node:jamnagar-refinery", "naphtha-node:jurong-terminal", "supplies", "NAPH-L", "spot", "active", 6000},
		{"naphtha-supply:jurong-yeosu", "naphtha-node:jurong-terminal", "naphtha-node:yeosu-cracker", "supplies", "NAPH-L", "term", "active", 4200},
		{"naphtha-supply:jurong-chiba", "naphtha-node:jurong-terminal", "naphtha-node:chiba-cracker", "supplies", "NAPH-L", "term", "active", 2800},
		{"naphtha-supply:baytown-rotterdam", "naphtha-node:baytown-refinery", "naphtha-node:rotterdam-terminal", "exports_to", "NAPH-H", "spot", "active", 3000},
		{"naphtha-supply:zhenhai-yeosu", "naphtha-node:zhenhai-refinery", "naphtha-node:yeosu-cracker", "backhaul", "NAPH-H", "spot", "monitored", 1800},
	}
	routes := []naphthaCargoRouteSeed{
		{"naphtha-route:jamnagar-yeosu-001-load", "naphtha-node:jamnagar-refinery", "naphtha-node:yeosu-cracker", "naphtha-cargo:jamnagar-yeosu-001", "load_to_discharge", "2026-05-10T06:00:00Z", "active"},
		{"naphtha-route:jurong-chiba-001-load", "naphtha-node:jurong-terminal", "naphtha-node:chiba-cracker", "naphtha-cargo:jurong-chiba-001", "load_to_discharge", "2026-05-12T08:00:00Z", "active"},
		{"naphtha-route:baytown-rotterdam-001-load", "naphtha-node:baytown-refinery", "naphtha-node:rotterdam-terminal", "naphtha-cargo:baytown-rotterdam-001", "load_to_discharge", "2026-05-08T04:00:00Z", "active"},
	}
	derivatives := []naphthaDerivativeSeed{
		{"naphtha-derivative:yeosu-ethylene", "naphtha-node:yeosu-cracker", "product:ethylene", "ethylene", "active", 31.5},
		{"naphtha-derivative:yeosu-propylene", "naphtha-node:yeosu-cracker", "product:propylene", "propylene", "active", 15.0},
		{"naphtha-derivative:chiba-ethylene", "naphtha-node:chiba-cracker", "product:ethylene", "ethylene", "active", 30.0},
		{"naphtha-derivative:chiba-propylene", "naphtha-node:chiba-cracker", "product:propylene", "propylene", "active", 14.2},
	}

	fmt.Printf("naphtha supply seed target: %s\n", redactURL(databaseURL))
	fmt.Printf("  products=%d nodes=%d cargoes=%d prices=%d demands=%d supply_links=%d routes=%d derivatives=%d\n",
		len(products), len(nodes), len(cargoes), len(prices), len(demands), len(supplyLinks), len(routes), len(derivatives))
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

	for _, row := range products {
		if _, err := tx.Exec(ctx, `DELETE FROM vertex_product_grade WHERE vertex_id = $1`, row.vertexID); err != nil {
			return err
		}
		if _, err := tx.Exec(ctx, `
INSERT INTO vertex_product_grade (vertex_id, created_date, owner_did, repo, product_code, product_family, sulfur_band, status, collection, actor_did, org_did)
VALUES ($1, $2, $3, $3, $4, $5, $6, 'active', 'ai.gftd.apps.naphthaSupply.productGrade', $3, $7)`,
			row.vertexID, naphthaSeedDate, naphthaActorDID, row.productCode, row.productFamily, row.sulfurBand, naphthaOrgDID); err != nil {
			return err
		}
	}
	for _, row := range nodes {
		if _, err := tx.Exec(ctx, `DELETE FROM vertex_naphtha_market_node WHERE vertex_id = $1`, row.vertexID); err != nil {
			return err
		}
		if _, err := tx.Exec(ctx, `
INSERT INTO vertex_naphtha_market_node (vertex_id, created_date, owner_did, repo, node_code, node_kind, display_name, country_code, locode, operator_did, refinery_code, product_code, capacity_tonnes_day, status, collection, actor_did, org_did)
VALUES ($1, $2, $3, $3, $4, $5, $6, $7, $8, $9, NULLIF($10, ''), $11, $12, $13, 'ai.gftd.apps.naphthaSupply.marketNode', $3, $14)`,
			row.vertexID, naphthaSeedDate, naphthaActorDID, row.nodeCode, row.nodeKind, row.displayName, row.countryCode, row.locode, row.operatorDID, row.refineryCode, row.productCode, row.capacityTonnesDay, row.status, naphthaOrgDID); err != nil {
			return err
		}
	}
	for _, row := range cargoes {
		if _, err := tx.Exec(ctx, `DELETE FROM vertex_naphtha_cargo WHERE vertex_id = $1`, row.vertexID); err != nil {
			return err
		}
		if _, err := tx.Exec(ctx, `
INSERT INTO vertex_naphtha_cargo (vertex_id, created_date, owner_did, repo, cargo_id, grade_code, origin_node_vid, destination_node_vid, load_port, discharge_port, vessel_imo, quantity_tonnes, laycan_start, laycan_end, status, collection, actor_did, org_did)
VALUES ($1, $2, $3, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, 'ai.gftd.apps.naphthaSupply.cargo', $3, $15)`,
			row.vertexID, naphthaSeedDate, naphthaActorDID, row.cargoID, row.gradeCode, row.originVID, row.destinationVID, row.loadPort, row.dischargePort, row.vesselIMO, row.quantityTonnes, row.laycanStart, row.laycanEnd, row.status, naphthaOrgDID); err != nil {
			return err
		}
	}
	for _, row := range prices {
		if _, err := tx.Exec(ctx, `DELETE FROM vertex_naphtha_price_assessment WHERE vertex_id = $1`, row.vertexID); err != nil {
			return err
		}
		if _, err := tx.Exec(ctx, `
INSERT INTO vertex_naphtha_price_assessment (vertex_id, created_date, owner_did, repo, assessment_id, benchmark_code, region, grade_code, price_usd_tonne, spread_to_brent_usd_bbl, assessed_at, publisher, status, collection, actor_did, org_did)
VALUES ($1, $2, $3, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, 'ai.gftd.apps.naphthaSupply.priceAssessment', $3, $13)`,
			row.vertexID, naphthaSeedDate, naphthaActorDID, row.assessmentID, row.benchmarkCode, row.region, row.gradeCode, row.priceUSDTonne, row.spreadToBrentUSDBBL, row.assessedAt, row.publisher, row.status, naphthaOrgDID); err != nil {
			return err
		}
	}
	for _, row := range demands {
		if _, err := tx.Exec(ctx, `DELETE FROM vertex_naphtha_cracker_demand WHERE vertex_id = $1`, row.vertexID); err != nil {
			return err
		}
		if _, err := tx.Exec(ctx, `
INSERT INTO vertex_naphtha_cracker_demand (vertex_id, created_date, owner_did, repo, demand_id, consumer_node_vid, product_family, demand_tonnes_day, substitution_feedstock, effective_from, effective_to, status, collection, actor_did, org_did)
VALUES ($1, $2, $3, $3, $4, $5, $6, $7, $8, $9, $10, $11, 'ai.gftd.apps.naphthaSupply.crackerDemand', $3, $12)`,
			row.vertexID, naphthaSeedDate, naphthaActorDID, row.demandID, row.consumerVID, row.productFamily, row.demandTonnesDay, row.substitutionFeedstock, row.effectiveFrom, row.effectiveTo, row.status, naphthaOrgDID); err != nil {
			return err
		}
	}
	for _, row := range supplyLinks {
		if _, err := tx.Exec(ctx, `DELETE FROM edge_naphtha_supply_link WHERE edge_id = $1`, row.edgeID); err != nil {
			return err
		}
		if _, err := tx.Exec(ctx, `
INSERT INTO edge_naphtha_supply_link (edge_id, src_vid, dst_vid, created_date, owner_did, relationship, grade_code, capacity_tonnes_day, contract_type, status)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)`,
			row.edgeID, row.srcVID, row.dstVID, naphthaSeedDate, naphthaActorDID, row.relationship, row.gradeCode, row.capacityTonnesDay, row.contractType, row.status); err != nil {
			return err
		}
	}
	for _, row := range routes {
		if _, err := tx.Exec(ctx, `DELETE FROM edge_naphtha_cargo_route WHERE edge_id = $1`, row.edgeID); err != nil {
			return err
		}
		if _, err := tx.Exec(ctx, `
INSERT INTO edge_naphtha_cargo_route (edge_id, src_vid, dst_vid, created_date, owner_did, cargo_vid, route_role, event_at, status)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)`,
			row.edgeID, row.srcVID, row.dstVID, naphthaSeedDate, naphthaActorDID, row.cargoVID, row.routeRole, row.eventAt, row.status); err != nil {
			return err
		}
	}
	for _, row := range derivatives {
		if _, err := tx.Exec(ctx, `DELETE FROM edge_naphtha_feedstock_to_derivative WHERE edge_id = $1`, row.edgeID); err != nil {
			return err
		}
		if _, err := tx.Exec(ctx, `
INSERT INTO edge_naphtha_feedstock_to_derivative (edge_id, src_vid, dst_vid, created_date, owner_did, derivative_family, conversion_yield_pct, status)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8)`,
			row.edgeID, row.srcVID, row.dstVID, naphthaSeedDate, naphthaActorDID, row.derivativeFamily, row.conversionYieldPct, row.status); err != nil {
			return err
		}
	}
	if err := tx.Commit(ctx); err != nil {
		return err
	}

	fmt.Println("naphtha supply seed complete")
	return nil
}
