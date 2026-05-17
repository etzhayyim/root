// seed_domains.go — Additional domain seed data for gftd seed.
package main

import "fmt"

func fundSeeds() seedDef {
	def := seedDef{Domain: "fund", Nanoid: "fndmgmt1", DID: "did:web:fund.etzhayyim.com"}

	funds := []struct {
		id, name, fundKind, strategy, jurisdiction, domicile, managerName, sponsorName, currency string
		vintageYear                                                                              int
		aumAmount, committedCapital                                                              int64
	}{
		{"swf-norway-gpfg", "Government Pension Fund Global", "sovereign_fund", "global-diversified", "nor", "nor", "Norges Bank Investment Management", "Kingdom of Norway", "NOK", 1990, 1_700_000_000_000, 0},
		{"mutual-vanguard-total-world", "Vanguard Total World Stock Fund", "mutual_fund", "public-equity-index", "usa", "usa", "The Vanguard Group", "Vanguard", "USD", 2008, 41_000_000_000, 0},
		{"pension-cpp-investments", "CPP Investments Fund", "pension_fund", "multi-asset-pension", "can", "can", "CPP Investments", "Canada Pension Plan", "CAD", 1997, 632_000_000_000, 0},
		{"private-softbank-vision", "SoftBank Vision Fund", "private_fund", "late-stage-technology", "jpn", "jpn", "SoftBank Investment Advisers", "SoftBank Group", "USD", 2017, 0, 100_000_000_000},
		{"gov-jica-private-sector", "JICA Private Sector Investment Finance", "government_fund", "development-finance", "jpn", "jpn", "Japan International Cooperation Agency", "Government of Japan", "JPY", 1960, 320_000_000_000, 0},
	}

	managers := []struct {
		id, name, managerType, jurisdiction, domicile, regulator, currency string
		aumAmount                                                          int64
	}{
		{"mgr-nbim", "Norges Bank Investment Management", "sovereign-asset-manager", "nor", "nor", "Norwegian Ministry of Finance", "NOK", 1_700_000_000_000},
		{"mgr-vanguard", "The Vanguard Group", "mutual-fund-manager", "usa", "usa", "SEC", "USD", 10_000_000_000_000},
		{"mgr-cpp", "CPP Investments", "pension-fund-manager", "can", "can", "Office of the Superintendent of Financial Institutions", "CAD", 632_000_000_000},
		{"mgr-sbia", "SoftBank Investment Advisers", "private-fund-manager", "gbr", "gbr", "FCA", "USD", 140_000_000_000},
		{"mgr-jica", "JICA Private Sector Investment Finance", "development-finance-manager", "jpn", "jpn", "Ministry of Foreign Affairs of Japan", "JPY", 320_000_000_000},
	}

	investors := []struct {
		id, name, investorType, jurisdiction, domicile, currency string
		commitmentAmount                                         int64
	}{
		{"lp-abu-dhabi", "Mubadala Investment Company", "sovereign-lp", "are", "are", "USD", 15_000_000_000},
		{"lp-calpers", "CalPERS", "pension-lp", "usa", "usa", "USD", 5_000_000_000},
		{"lp-university-endowment", "Northbridge University Endowment", "endowment-lp", "usa", "usa", "USD", 750_000_000},
		{"lp-jbic", "Japan Bank for International Cooperation", "government-lp", "jpn", "jpn", "JPY", 120_000_000_000},
	}

	investees := []struct {
		id, name, investeeType, jurisdiction, sector, currency string
		valuationAmount, investedAmount                        int64
		ownershipPct                                           float64
	}{
		{"inv-voltgrid", "VoltGrid Storage", "climate-infrastructure", "deu", "energy-storage", "EUR", 2_300_000_000, 180_000_000, 11.5},
		{"inv-rural-health-net", "Rural Health Net", "health-services", "usa", "primary-care", "USD", 950_000_000, 90_000_000, 9.2},
		{"inv-orbit-fab", "OrbitFab Systems", "industrial-tech", "jpn", "advanced-manufacturing", "USD", 3_400_000_000, 250_000_000, 14.1},
		{"inv-gridwater", "GridWater Infra", "water-infrastructure", "ind", "water-treatment", "USD", 1_600_000_000, 110_000_000, 8.4},
	}

	metrics := []struct {
		id, fundID, metricType, metricUnit, asOfDate string
		metricValue                                  int64
	}{
		{"metric-gpfg-2026q1", "swf-norway-gpfg", "aum", "NOK", "2026-03-31", 1_700_000_000_000},
		{"metric-vanguard-2026q1", "mutual-vanguard-total-world", "aum", "USD", "2026-03-31", 41_000_000_000},
		{"metric-cpp-2026q1", "pension-cpp-investments", "aum", "CAD", "2026-03-31", 632_000_000_000},
		{"metric-vision-2026q1", "private-softbank-vision", "committed_capital", "USD", "2026-03-31", 100_000_000_000},
		{"metric-jica-2026q1", "gov-jica-private-sector", "aum", "JPY", "2026-03-31", 320_000_000_000},
	}

	commitments := []struct {
		id, fundID, investorID, currency string
		commitmentAmount, calledAmount   int64
	}{
		{"commit-001", "private-softbank-vision", "lp-abu-dhabi", "USD", 15_000_000_000, 10_500_000_000},
		{"commit-002", "private-softbank-vision", "lp-calpers", "USD", 5_000_000_000, 3_200_000_000},
		{"commit-003", "private-softbank-vision", "lp-university-endowment", "USD", 750_000_000, 420_000_000},
		{"commit-004", "gov-jica-private-sector", "lp-jbic", "JPY", 120_000_000_000, 84_000_000_000},
	}

	syntheticKinds := []struct {
		slug, title, fundKind, strategy, managerType, regulator, sponsorPrefix, currency, metricType string
		baseAUM                                                                                      int64
		baseCommitment                                                                               int64
	}{
		{"sovereign", "Strategic Reserve Fund", "sovereign_fund", "global-diversified", "sovereign-asset-manager", "National Treasury", "State Holding Authority", "USD", "aum", 18_000_000_000, 0},
		{"mutual", "Global Allocation Fund", "mutual_fund", "public-equity-index", "mutual-fund-manager", "Securities Regulator", "Retail Asset Platform", "USD", "aum", 4_500_000_000, 0},
		{"pension", "Retirement Income Fund", "pension_fund", "multi-asset-pension", "pension-fund-manager", "Pension Supervisor", "National Pension Board", "USD", "aum", 12_000_000_000, 0},
		{"private", "Growth Equity Fund", "private_fund", "late-stage-technology", "private-fund-manager", "Financial Conduct Authority", "General Partner Group", "USD", "committed_capital", 0, 3_200_000_000},
		{"government", "Development Finance Fund", "government_fund", "development-finance", "development-finance-manager", "Ministry of Finance", "Public Investment Agency", "USD", "aum", 6_200_000_000, 0},
		{"investor", "Allocator Partnership Fund", "investor_fund", "limited-partner-allocation", "allocator-platform-manager", "Financial Services Authority", "Institutional Allocator Network", "USD", "committed_capital", 0, 2_400_000_000},
	}
	jurisdictions := []string{"usa", "jpn", "can", "gbr", "deu", "fra", "sgp", "are", "aus", "nld", "swe", "ind"}
	investeeKinds := []struct {
		kind, sector, currency string
		baseValuation          int64
		baseInvested           int64
	}{
		{"energy-transition", "grid-modernization", "USD", 1_800_000_000, 140_000_000},
		{"digital-infrastructure", "cloud-network", "USD", 2_400_000_000, 175_000_000},
		{"health-services", "primary-care", "USD", 1_200_000_000, 95_000_000},
		{"industrial-tech", "advanced-manufacturing", "USD", 2_900_000_000, 210_000_000},
	}
	for i := 0; i < 24; i++ {
		spec := syntheticKinds[i%len(syntheticKinds)]
		jurisdiction := jurisdictions[i%len(jurisdictions)]
		series := i + 1
		fundID := fmt.Sprintf("%s-synthetic-%02d", spec.slug, series)
		managerID := fmt.Sprintf("mgr-%s-%02d", spec.slug, series)
		fundName := fmt.Sprintf("%s %02d", spec.title, series)
		managerName := fmt.Sprintf("%s Capital %02d", spec.title, series)
		sponsorName := fmt.Sprintf("%s %02d", spec.sponsorPrefix, series)
		vintageYear := 2002 + (series % 20)
		fundRow := struct {
			id, name, fundKind, strategy, jurisdiction, domicile, managerName, sponsorName, currency string
			vintageYear                                                                              int
			aumAmount, committedCapital                                                              int64
		}{
			id: fundID, name: fundName, fundKind: spec.fundKind, strategy: spec.strategy,
			jurisdiction: jurisdiction, domicile: jurisdiction, managerName: managerName, sponsorName: sponsorName,
			currency: spec.currency, vintageYear: vintageYear,
			aumAmount:        spec.baseAUM + int64(series)*450_000_000,
			committedCapital: spec.baseCommitment + int64(series)*210_000_000,
		}
		if spec.baseAUM == 0 {
			fundRow.aumAmount = 0
		}
		if spec.baseCommitment == 0 {
			fundRow.committedCapital = 0
		}
		funds = append(funds, fundRow)
		managers = append(managers, struct {
			id, name, managerType, jurisdiction, domicile, regulator, currency string
			aumAmount                                                          int64
		}{
			id: managerID, name: managerName, managerType: spec.managerType, jurisdiction: jurisdiction,
			domicile: jurisdiction, regulator: spec.regulator, currency: spec.currency,
			aumAmount: maxInt64(fundRow.aumAmount, fundRow.committedCapital),
		})
		assetMetric := maxInt64(fundRow.aumAmount, fundRow.committedCapital)
		metrics = append(metrics, struct {
			id, fundID, metricType, metricUnit, asOfDate string
			metricValue                                  int64
		}{
			id: fmt.Sprintf("metric-%s-2026q1", fundID), fundID: fundID, metricType: spec.metricType,
			metricUnit: spec.currency, asOfDate: "2026-03-31", metricValue: assetMetric,
		})

		investeeSpec := investeeKinds[i%len(investeeKinds)]
		investees = append(investees, struct {
			id, name, investeeType, jurisdiction, sector, currency string
			valuationAmount, investedAmount                        int64
			ownershipPct                                           float64
		}{
			id:              fmt.Sprintf("inv-%s-%02d", spec.slug, series),
			name:            fmt.Sprintf("%s Portfolio Company %02d", spec.title, series),
			investeeType:    investeeSpec.kind,
			jurisdiction:    jurisdiction,
			sector:          investeeSpec.sector,
			currency:        investeeSpec.currency,
			valuationAmount: investeeSpec.baseValuation + int64(series)*120_000_000,
			investedAmount:  investeeSpec.baseInvested + int64(series)*12_000_000,
			ownershipPct:    8.0 + float64((series%7)+1)*0.7,
		})

		investorID := fmt.Sprintf("lp-%s-%02d", spec.slug, series)
		investmentCurrency := spec.currency
		if investmentCurrency == "" {
			investmentCurrency = "USD"
		}
		investmentAmount := int64(650_000_000 + series*55_000_000)
		investors = append(investors, struct {
			id, name, investorType, jurisdiction, domicile, currency string
			commitmentAmount                                         int64
		}{
			id:               investorID,
			name:             fmt.Sprintf("%s Allocator %02d", spec.title, series),
			investorType:     fmt.Sprintf("%s-lp", spec.slug),
			jurisdiction:     jurisdiction,
			domicile:         jurisdiction,
			currency:         investmentCurrency,
			commitmentAmount: investmentAmount,
		})
		commitments = append(commitments, struct {
			id, fundID, investorID, currency string
			commitmentAmount, calledAmount   int64
		}{
			id:               fmt.Sprintf("commit-%s-%02d", spec.slug, series),
			fundID:           fundID,
			investorID:       investorID,
			currency:         investmentCurrency,
			commitmentAmount: investmentAmount,
			calledAmount:     investmentAmount * 7 / 10,
		})
	}

	fundRecs := seedCollection{Collection: "ai.gftd.apps.fund.fund"}
	for _, f := range funds {
		row := map[string]any{
			"fund_id":        f.id,
			"name":           f.name,
			"fund_kind":      f.fundKind,
			"strategy":       f.strategy,
			"jurisdiction":   f.jurisdiction,
			"domicile":       f.domicile,
			"vintage_year":   f.vintageYear,
			"manager_name":   f.managerName,
			"sponsor_name":   f.sponsorName,
			"currency":       f.currency,
			"status":         "active",
			"source_license": "public-web",
		}
		if f.aumAmount > 0 {
			row["aum_amount"] = f.aumAmount
		}
		if f.committedCapital > 0 {
			row["committed_capital"] = f.committedCapital
		}
		fundRecs.Items = append(fundRecs.Items, seedRecord{ID: f.id, Data: row})
	}

	managerRecs := seedCollection{Collection: "ai.gftd.apps.fund.manager"}
	for _, m := range managers {
		managerRecs.Items = append(managerRecs.Items, seedRecord{ID: m.id, Data: map[string]any{
			"manager_id":     m.id,
			"manager_name":   m.name,
			"manager_type":   m.managerType,
			"jurisdiction":   m.jurisdiction,
			"domicile":       m.domicile,
			"regulator":      m.regulator,
			"currency":       m.currency,
			"aum_amount":     m.aumAmount,
			"source_license": "public-web",
		}})
	}

	investorRecs := seedCollection{Collection: "ai.gftd.apps.fund.investor"}
	for _, i := range investors {
		investorRecs.Items = append(investorRecs.Items, seedRecord{ID: i.id, Data: map[string]any{
			"investor_id":       i.id,
			"investor_name":     i.name,
			"investor_type":     i.investorType,
			"jurisdiction":      i.jurisdiction,
			"domicile":          i.domicile,
			"commitment_amount": i.commitmentAmount,
			"currency":          i.currency,
			"source_license":    "public-web",
		}})
	}

	investeeRecs := seedCollection{Collection: "ai.gftd.apps.fund.investee"}
	for _, i := range investees {
		investeeRecs.Items = append(investeeRecs.Items, seedRecord{ID: i.id, Data: map[string]any{
			"investee_id":      i.id,
			"investee_name":    i.name,
			"investee_type":    i.investeeType,
			"jurisdiction":     i.jurisdiction,
			"sector":           i.sector,
			"valuation_amount": i.valuationAmount,
			"invested_amount":  i.investedAmount,
			"ownership_pct":    i.ownershipPct,
			"currency":         i.currency,
			"source_license":   "public-web",
		}})
	}

	metricRecs := seedCollection{Collection: "ai.gftd.apps.fund.metric"}
	for _, m := range metrics {
		metricRecs.Items = append(metricRecs.Items, seedRecord{ID: m.id, Data: map[string]any{
			"metric_id":      m.id,
			"fund_id":        m.fundID,
			"metric_type":    m.metricType,
			"metric_value":   m.metricValue,
			"metric_unit":    m.metricUnit,
			"as_of_date":     m.asOfDate,
			"source_license": "public-web",
		}})
	}

	commitmentRecs := seedCollection{Collection: "ai.gftd.apps.fund.commitment"}
	for _, c := range commitments {
		commitmentRecs.Items = append(commitmentRecs.Items, seedRecord{ID: c.id, Data: map[string]any{
			"commitment_id":     c.id,
			"fund_id":           c.fundID,
			"investor_id":       c.investorID,
			"commitment_amount": c.commitmentAmount,
			"called_amount":     c.calledAmount,
			"currency":          c.currency,
			"source_license":    "public-web",
		}})
	}

	def.DIDs = append(def.DIDs,
		seedDID{Path: "manager:nbim", DisplayName: "Norges Bank Investment Management", Description: "Sovereign fund manager"},
		seedDID{Path: "manager:vanguard", DisplayName: "The Vanguard Group", Description: "Mutual fund manager"},
		seedDID{Path: "manager:cpp", DisplayName: "CPP Investments", Description: "Pension fund manager"},
		seedDID{Path: "manager:sbia", DisplayName: "SoftBank Investment Advisers", Description: "Private fund manager"},
		seedDID{Path: "manager:jica", DisplayName: "JICA Private Sector Investment Finance", Description: "Government fund manager"},
	)
	def.Records = append(def.Records, fundRecs, managerRecs, investorRecs, investeeRecs, metricRecs, commitmentRecs)
	return def
}

func maxInt64(a, b int64) int64 {
	if a > b {
		return a
	}
	return b
}

func keibaSeeds() seedDef {
	def := seedDef{Domain: "keiba", Nanoid: "k31b4jp0", DID: "did:web:keiba.etzhayyim.com"}
	venues := []struct{ id, name, nameEn, pref, typ string }{
		{"tokyo", "東京", "Tokyo", "東京", "jra"}, {"nakayama", "中山", "Nakayama", "千葉", "jra"},
		{"hanshin", "阪神", "Hanshin", "兵庫", "jra"}, {"kyoto", "京都", "Kyoto", "京都", "jra"},
		{"chukyo", "中京", "Chukyo", "愛知", "jra"}, {"kokura", "小倉", "Kokura", "福岡", "jra"},
		{"niigata", "新潟", "Niigata", "新潟", "jra"}, {"sapporo", "札幌", "Sapporo", "北海道", "jra"},
		{"hakodate", "函館", "Hakodate", "北海道", "jra"}, {"fukushima", "福島", "Fukushima", "福島", "jra"},
		{"ooi", "大井", "Oi", "東京", "nar"}, {"kawasaki", "川崎", "Kawasaki", "神奈川", "nar"},
		{"funabashi", "船橋", "Funabashi", "千葉", "nar"}, {"urawa", "浦和", "Urawa", "埼玉", "nar"},
		{"mombetsu", "門別", "Mombetsu", "北海道", "nar"}, {"morioka", "盛岡", "Morioka", "岩手", "nar"},
		{"kanazawa", "金沢", "Kanazawa", "石川", "nar"}, {"nagoya_nar", "名古屋", "Nagoya", "愛知", "nar"},
		{"sonoda", "園田", "Sonoda", "兵庫", "nar"}, {"himeji", "姫路", "Himeji", "兵庫", "nar"},
		{"kochi_nar", "高知", "Kochi", "高知", "nar"}, {"saga", "佐賀", "Saga", "佐賀", "nar"},
		{"arao", "荒尾", "Arao", "熊本", "nar"}, {"obihiro", "帯広", "Obihiro", "北海道", "nar"},
		{"mizusawa", "水沢", "Mizusawa", "岩手", "nar"},
	}
	recs := seedCollection{Collection: "ai.gftd.apps.keiba.race_track"}
	for _, v := range venues {
		def.DIDs = append(def.DIDs, seedDID{Path: "venue:" + v.id, DisplayName: v.name + "競馬場", Description: v.nameEn + " — " + v.typ})
		recs.Items = append(recs.Items, seedRecord{ID: v.id, Data: map[string]any{
			"id": v.id, "name": v.name, "name_en": v.nameEn, "prefecture": v.pref, "type": v.typ, "status": "active",
		}})
	}
	def.Records = append(def.Records, recs)
	return def
}

func sovereignSeeds() seedDef {
	def := seedDef{Domain: "sovereign", Nanoid: "st4t3s01", DID: "did:web:states.etzhayyim.com"}
	states := []struct{ iso3, name, region string }{
		// East Asia (5)
		{"jpn", "Japan", "east_asia"}, {"chn", "China", "east_asia"}, {"kor", "South Korea", "east_asia"},
		{"prk", "North Korea", "east_asia"}, {"mng", "Mongolia", "east_asia"},
		// Southeast Asia (11)
		{"idn", "Indonesia", "southeast_asia"}, {"tha", "Thailand", "southeast_asia"}, {"sgp", "Singapore", "southeast_asia"},
		{"mys", "Malaysia", "southeast_asia"}, {"phl", "Philippines", "southeast_asia"}, {"vnm", "Vietnam", "southeast_asia"},
		{"mmr", "Myanmar", "southeast_asia"}, {"khm", "Cambodia", "southeast_asia"}, {"lao", "Laos", "southeast_asia"},
		{"brn", "Brunei", "southeast_asia"}, {"tls", "Timor-Leste", "southeast_asia"},
		// South Asia (8)
		{"ind", "India", "south_asia"}, {"pak", "Pakistan", "south_asia"}, {"bgd", "Bangladesh", "south_asia"},
		{"lka", "Sri Lanka", "south_asia"}, {"npl", "Nepal", "south_asia"}, {"btn", "Bhutan", "south_asia"},
		{"mdv", "Maldives", "south_asia"}, {"afg", "Afghanistan", "south_asia"},
		// Central Asia (5)
		{"kaz", "Kazakhstan", "central_asia"}, {"uzb", "Uzbekistan", "central_asia"}, {"tkm", "Turkmenistan", "central_asia"},
		{"kgz", "Kyrgyzstan", "central_asia"}, {"tjk", "Tajikistan", "central_asia"},
		// Western Asia / Middle East (18)
		{"tur", "Turkey", "western_asia"}, {"sau", "Saudi Arabia", "western_asia"}, {"are", "UAE", "western_asia"},
		{"isr", "Israel", "western_asia"}, {"irn", "Iran", "western_asia"}, {"irq", "Iraq", "western_asia"},
		{"jor", "Jordan", "western_asia"}, {"lbn", "Lebanon", "western_asia"}, {"syr", "Syria", "western_asia"},
		{"yem", "Yemen", "western_asia"}, {"omn", "Oman", "western_asia"}, {"kwt", "Kuwait", "western_asia"},
		{"qat", "Qatar", "western_asia"}, {"bhr", "Bahrain", "western_asia"}, {"pse", "Palestine", "western_asia"},
		{"cyp", "Cyprus", "western_asia"}, {"geo", "Georgia", "western_asia"}, {"arm", "Armenia", "western_asia"},
		// Caucasus
		{"aze", "Azerbaijan", "western_asia"},
		// Western Europe (12)
		{"gbr", "United Kingdom", "western_europe"}, {"fra", "France", "western_europe"}, {"deu", "Germany", "western_europe"},
		{"che", "Switzerland", "western_europe"}, {"nld", "Netherlands", "western_europe"}, {"bel", "Belgium", "western_europe"},
		{"aut", "Austria", "western_europe"}, {"irl", "Ireland", "western_europe"}, {"lux", "Luxembourg", "western_europe"},
		{"mco", "Monaco", "western_europe"}, {"lie", "Liechtenstein", "western_europe"}, {"and", "Andorra", "western_europe"},
		// Northern Europe (8)
		{"swe", "Sweden", "northern_europe"}, {"nor", "Norway", "northern_europe"}, {"fin", "Finland", "northern_europe"},
		{"dnk", "Denmark", "northern_europe"}, {"isl", "Iceland", "northern_europe"}, {"est", "Estonia", "northern_europe"},
		{"lva", "Latvia", "northern_europe"}, {"ltu", "Lithuania", "northern_europe"},
		// Southern Europe (11)
		{"ita", "Italy", "southern_europe"}, {"esp", "Spain", "southern_europe"}, {"prt", "Portugal", "southern_europe"},
		{"grc", "Greece", "southern_europe"}, {"hrv", "Croatia", "southern_europe"}, {"svn", "Slovenia", "southern_europe"},
		{"mlt", "Malta", "southern_europe"}, {"smr", "San Marino", "southern_europe"}, {"vat", "Vatican City", "southern_europe"},
		{"mne", "Montenegro", "southern_europe"}, {"mkd", "North Macedonia", "southern_europe"},
		// Eastern Europe (11)
		{"pol", "Poland", "eastern_europe"}, {"rou", "Romania", "eastern_europe"}, {"hun", "Hungary", "eastern_europe"},
		{"cze", "Czech Republic", "eastern_europe"}, {"svk", "Slovakia", "eastern_europe"}, {"ukr", "Ukraine", "eastern_europe"},
		{"blr", "Belarus", "eastern_europe"}, {"bgr", "Bulgaria", "eastern_europe"}, {"srb", "Serbia", "eastern_europe"},
		{"bih", "Bosnia and Herzegovina", "eastern_europe"}, {"alb", "Albania", "eastern_europe"},
		// Russia
		{"rus", "Russia", "eastern_europe"},
		// North America (3)
		{"usa", "United States", "north_america"}, {"can", "Canada", "north_america"}, {"mex", "Mexico", "north_america"},
		// Central America (7)
		{"gtm", "Guatemala", "central_america"}, {"hnd", "Honduras", "central_america"}, {"slv", "El Salvador", "central_america"},
		{"nic", "Nicaragua", "central_america"}, {"cri", "Costa Rica", "central_america"}, {"pan", "Panama", "central_america"},
		{"blz", "Belize", "central_america"},
		// Caribbean (13)
		{"cub", "Cuba", "caribbean"}, {"dom", "Dominican Republic", "caribbean"}, {"hti", "Haiti", "caribbean"},
		{"jam", "Jamaica", "caribbean"}, {"bhs", "Bahamas", "caribbean"}, {"brb", "Barbados", "caribbean"},
		{"atg", "Antigua and Barbuda", "caribbean"}, {"dma", "Dominica", "caribbean"}, {"grd", "Grenada", "caribbean"},
		{"lca", "Saint Lucia", "caribbean"}, {"vct", "Saint Vincent and the Grenadines", "caribbean"},
		{"kna", "Saint Kitts and Nevis", "caribbean"}, {"tto", "Trinidad and Tobago", "caribbean"},
		// South America (12)
		{"bra", "Brazil", "south_america"}, {"arg", "Argentina", "south_america"}, {"col", "Colombia", "south_america"},
		{"chl", "Chile", "south_america"}, {"per", "Peru", "south_america"}, {"ven", "Venezuela", "south_america"},
		{"ecu", "Ecuador", "south_america"}, {"bol", "Bolivia", "south_america"}, {"pry", "Paraguay", "south_america"},
		{"ury", "Uruguay", "south_america"}, {"guy", "Guyana", "south_america"}, {"sur", "Suriname", "south_america"},
		// Oceania (14)
		{"aus", "Australia", "oceania"}, {"nzl", "New Zealand", "oceania"}, {"fji", "Fiji", "oceania"},
		{"png", "Papua New Guinea", "oceania"}, {"slb", "Solomon Islands", "oceania"}, {"vut", "Vanuatu", "oceania"},
		{"wsm", "Samoa", "oceania"}, {"ton", "Tonga", "oceania"}, {"kir", "Kiribati", "oceania"},
		{"fsm", "Micronesia", "oceania"}, {"mhl", "Marshall Islands", "oceania"}, {"plw", "Palau", "oceania"},
		{"tuv", "Tuvalu", "oceania"}, {"nru", "Nauru", "oceania"},
		// Northern Africa (7)
		{"egy", "Egypt", "northern_africa"}, {"dza", "Algeria", "northern_africa"}, {"mar", "Morocco", "northern_africa"},
		{"tun", "Tunisia", "northern_africa"}, {"lby", "Libya", "northern_africa"}, {"sdn", "Sudan", "northern_africa"},
		{"ssd", "South Sudan", "northern_africa"},
		// West Africa (16)
		{"nga", "Nigeria", "west_africa"}, {"gha", "Ghana", "west_africa"}, {"civ", "Côte d'Ivoire", "west_africa"},
		{"sen", "Senegal", "west_africa"}, {"mli", "Mali", "west_africa"}, {"bfa", "Burkina Faso", "west_africa"},
		{"ner", "Niger", "west_africa"}, {"gin", "Guinea", "west_africa"}, {"sle", "Sierra Leone", "west_africa"},
		{"lbr", "Liberia", "west_africa"}, {"tgo", "Togo", "west_africa"}, {"ben", "Benin", "west_africa"},
		{"gmb", "Gambia", "west_africa"}, {"gnb", "Guinea-Bissau", "west_africa"}, {"cpv", "Cabo Verde", "west_africa"},
		{"mrt", "Mauritania", "west_africa"},
		// East Africa (11)
		{"ken", "Kenya", "east_africa"}, {"eth", "Ethiopia", "east_africa"}, {"tza", "Tanzania", "east_africa"},
		{"uga", "Uganda", "east_africa"}, {"rwa", "Rwanda", "east_africa"}, {"bdi", "Burundi", "east_africa"},
		{"som", "Somalia", "east_africa"}, {"eri", "Eritrea", "east_africa"}, {"dji", "Djibouti", "east_africa"},
		{"com", "Comoros", "east_africa"}, {"syc", "Seychelles", "east_africa"},
		// Central Africa (8)
		{"cod", "DR Congo", "central_africa"}, {"cog", "Republic of the Congo", "central_africa"},
		{"cmr", "Cameroon", "central_africa"}, {"gab", "Gabon", "central_africa"}, {"gnq", "Equatorial Guinea", "central_africa"},
		{"caf", "Central African Republic", "central_africa"}, {"tcd", "Chad", "central_africa"},
		{"stp", "São Tomé and Príncipe", "central_africa"},
		// Southern Africa (10)
		{"zaf", "South Africa", "southern_africa"}, {"ago", "Angola", "southern_africa"}, {"moz", "Mozambique", "southern_africa"},
		{"zmb", "Zambia", "southern_africa"}, {"zwe", "Zimbabwe", "southern_africa"}, {"bwa", "Botswana", "southern_africa"},
		{"nam", "Namibia", "southern_africa"}, {"mwi", "Malawi", "southern_africa"}, {"lso", "Lesotho", "southern_africa"},
		{"swz", "Eswatini", "southern_africa"},
		// Island Africa (1)
		{"mdg", "Madagascar", "east_africa"},
		// Disputed / Observer (2)
		{"twn", "Taiwan", "east_asia"}, {"xkx", "Kosovo", "eastern_europe"},
		// 195 sovereign states: 193 UN members + Vatican + Palestine + Taiwan + Kosovo observers/disputed
	}
	recs := seedCollection{Collection: "ai.gftd.apps.states.sovereign"}
	for _, s := range states {
		def.DIDs = append(def.DIDs, seedDID{Path: "state:" + s.iso3, DisplayName: s.name, Description: s.region})
		recs.Items = append(recs.Items, seedRecord{ID: s.iso3, Data: map[string]any{
			"id": s.iso3, "iso3": s.iso3, "name": s.name, "region": s.region, "status": "active",
			"kind": "sovereign", "authority_kind": "sovereign", "tier": "sovereign",
			"jurisdiction": s.iso3, "sensitivity_ord": 0,
		}})
	}
	def.Records = append(def.Records, recs)
	return def
}

func iscoSeeds() seedDef {
	def := seedDef{Domain: "isco", Nanoid: "pba7d22f", DID: "did:web:isco.etzhayyim.com"}
	// ISCO-08 major groups (10) + sub-major groups (43) = seed top-level
	groups := []struct{ code, name string }{
		{"0", "Armed Forces Occupations"}, {"1", "Managers"}, {"2", "Professionals"},
		{"3", "Technicians and Associate Professionals"}, {"4", "Clerical Support Workers"},
		{"5", "Service and Sales Workers"}, {"6", "Skilled Agricultural Workers"},
		{"7", "Craft and Related Trades Workers"}, {"8", "Plant and Machine Operators"},
		{"9", "Elementary Occupations"},
		// Sub-major
		{"11", "Chief Executives/Legislators"}, {"12", "Administrative Managers"},
		{"13", "Production/Services Managers"}, {"14", "Hospitality/Retail Managers"},
		{"21", "Science/Engineering Professionals"}, {"22", "Health Professionals"},
		{"23", "Teaching Professionals"}, {"24", "Business/Admin Professionals"},
		{"25", "ICT Professionals"}, {"26", "Legal/Social/Cultural Professionals"},
		{"31", "Science/Engineering Technicians"}, {"32", "Health Associate Professionals"},
		{"33", "Business/Admin Associate Professionals"}, {"34", "Legal/Social Associates"},
		{"35", "ICT Technicians"}, {"41", "General Office Clerks"},
		{"42", "Customer Services Clerks"}, {"43", "Numerical Recording Clerks"},
		{"44", "Other Clerical Support"}, {"51", "Personal Services Workers"},
		{"52", "Sales Workers"}, {"53", "Personal Care Workers"},
		{"54", "Protective Services Workers"}, {"61", "Market-Oriented Agriculture"},
		{"62", "Forestry/Fishery Workers"}, {"63", "Subsistence Agriculture"},
		{"71", "Building Trades Workers"}, {"72", "Metal/Machinery Trades"},
		{"73", "Handicraft/Printing Workers"}, {"74", "Electrical/Electronic Trades"},
		{"75", "Food Processing Workers"}, {"81", "Stationary Plant Operators"},
		{"82", "Assemblers"}, {"83", "Drivers/Mobile Operators"},
		{"91", "Cleaners/Helpers"}, {"92", "Agricultural Labourers"},
		{"93", "Mining/Construction Labourers"}, {"94", "Food Preparation Assistants"},
		{"95", "Street Services Workers"}, {"96", "Refuse Workers"},
	}
	recs := seedCollection{Collection: "ai.gftd.apps.isco.professional_code"}
	for _, g := range groups {
		def.DIDs = append(def.DIDs, seedDID{Path: "occupation:" + g.code, DisplayName: g.name, Description: "ISCO-08 " + g.code})
		recs.Items = append(recs.Items, seedRecord{ID: g.code, Data: map[string]any{
			"id": g.code, "code": g.code, "name": g.name, "level": len(g.code), "status": "active",
		}})
	}
	def.Records = append(def.Records, recs)
	return def
}

func isicSeeds() seedDef {
	def := seedDef{Domain: "isic", Nanoid: "1s1c5c0a", DID: "did:web:isic.etzhayyim.com"}
	sections := []struct{ code, name string }{
		{"A", "Agriculture, forestry and fishing"}, {"B", "Mining and quarrying"},
		{"C", "Manufacturing"}, {"D", "Electricity, gas, steam"},
		{"E", "Water supply; sewerage"}, {"F", "Construction"},
		{"G", "Wholesale and retail trade"}, {"H", "Transportation and storage"},
		{"I", "Accommodation and food"}, {"J", "Information and communication"},
		{"K", "Financial and insurance"}, {"L", "Real estate"},
		{"M", "Professional, scientific"}, {"N", "Administrative and support"},
		{"O", "Public administration"}, {"P", "Education"},
		{"Q", "Human health and social"}, {"R", "Arts, entertainment"},
		{"S", "Other service activities"}, {"T", "Household activities"},
		{"U", "Extraterritorial organizations"},
	}
	recs := seedCollection{Collection: "ai.gftd.apps.isic.industry_standard"}
	for _, s := range sections {
		def.DIDs = append(def.DIDs, seedDID{Path: "section:" + s.code, DisplayName: s.name, Description: "ISIC Rev.4 Section " + s.code})
		recs.Items = append(recs.Items, seedRecord{ID: s.code, Data: map[string]any{
			"id": s.code, "code": s.code, "name": s.name, "level": "section", "status": "active",
		}})
	}
	def.Records = append(def.Records, recs)
	return def
}

func treatySeeds() seedDef {
	def := seedDef{Domain: "treaty", Nanoid: "tr3aty01", DID: "did:web:treaty.etzhayyim.com"}
	treaties := []struct{ id, name, year string }{
		{"un_charter", "Charter of the United Nations", "1945"},
		{"udhr", "Universal Declaration of Human Rights", "1948"},
		{"geneva_1949", "Geneva Conventions", "1949"},
		{"iccpr", "International Covenant on Civil and Political Rights", "1966"},
		{"icescr", "International Covenant on Economic, Social and Cultural Rights", "1966"},
		{"vienna_treaties", "Vienna Convention on the Law of Treaties", "1969"},
		{"unclos", "UN Convention on the Law of the Sea", "1982"},
		{"paris_climate", "Paris Agreement", "2015"},
		{"rome_statute", "Rome Statute of the ICC", "1998"},
		{"wto_marrakesh", "Marrakesh Agreement (WTO)", "1994"},
	}
	recs := seedCollection{Collection: "ai.gftd.apps.treaty.treaty"}
	for _, t := range treaties {
		def.DIDs = append(def.DIDs, seedDID{Path: "treaty:" + t.id, DisplayName: t.name, Description: t.year})
		recs.Items = append(recs.Items, seedRecord{ID: t.id, Data: map[string]any{
			"id": t.id, "name": t.name, "year": t.year, "status": "in_force",
			"kind": "treaty", "authority_kind": "treaty", "tier": "treaty",
			"jurisdiction": "international", "sensitivity_ord": 0,
		}})
	}
	def.Records = append(def.Records, recs)
	return def
}

func blockchainSeeds() seedDef {
	def := seedDef{Domain: "blockchain", Nanoid: "bl0ckch1", DID: "did:web:blockchain.etzhayyim.com"}
	chains := []struct{ id, name, consensus string }{
		{"bitcoin", "Bitcoin", "pow"}, {"ethereum", "Ethereum", "pos"},
		{"solana", "Solana", "pos"}, {"cardano", "Cardano", "pos"},
		{"polkadot", "Polkadot", "npos"}, {"avalanche", "Avalanche", "pos"},
		{"cosmos", "Cosmos", "pos"}, {"near", "NEAR Protocol", "pos"},
		{"algorand", "Algorand", "ppos"}, {"tezos", "Tezos", "lpos"},
	}
	recs := seedCollection{Collection: "ai.gftd.apps.blockchain.blockchain_protocol"}
	for _, c := range chains {
		def.DIDs = append(def.DIDs, seedDID{Path: "chain:" + c.id, DisplayName: c.name, Description: c.consensus})
		recs.Items = append(recs.Items, seedRecord{ID: c.id, Data: map[string]any{
			"id": c.id, "name": c.name, "consensus": c.consensus, "status": "active",
			"kind": "blockchain", "authority_kind": "blockchain", "tier": "blockchain",
			"sensitivity_ord": 0,
		}})
	}
	def.Records = append(def.Records, recs)
	return def
}

func religiousSeeds() seedDef {
	def := seedDef{Domain: "religious", Nanoid: "r3lgus01", DID: "did:web:religious.etzhayyim.com"}
	systems := []struct{ id, name, family string }{
		{"canon_catholic", "Catholic Canon Law", "christian"},
		{"canon_orthodox", "Orthodox Canon Law", "christian"},
		{"canon_anglican", "Anglican Canon Law", "christian"},
		{"canon_lutheran", "Lutheran Church Order", "christian"},
		{"canon_reformed", "Reformed Church Order", "christian"},
		{"canon_maronite", "Maronite Canon Law", "christian"},
		{"canon_coptic", "Coptic Canon Tradition", "christian"},
		{"canon_syriac", "Syriac Canon Tradition", "christian"},
		{"canon_melkite", "Melkite Canon Tradition", "christian"},
		{"canon_ethiopian", "Ethiopian Orthodox Canon", "christian"},
		{"sharia_sunni", "Sunni Sharia", "islamic"},
		{"sharia_shia", "Shia Fiqh", "islamic"},
		{"fiqh_hanafi", "Hanafi Fiqh", "islamic"},
		{"fiqh_maliki", "Maliki Fiqh", "islamic"},
		{"fiqh_shafii", "Shafii Fiqh", "islamic"},
		{"fiqh_hanbali", "Hanbali Fiqh", "islamic"},
		{"fiqh_jafari", "Jafari Fiqh", "islamic"},
		{"fiqh_zaydi", "Zaydi Fiqh", "islamic"},
		{"fiqh_ibadi", "Ibadi Fiqh", "islamic"},
		{"siyar_islamic", "Islamic Siyar", "islamic"},
		{"halakha", "Jewish Halakha", "jewish"},
		{"torah_law", "Torah Law", "jewish"},
		{"talmudic_law", "Talmudic Law", "jewish"},
		{"mishneh_torah", "Mishneh Torah", "jewish"},
		{"shulchan_aruch", "Shulchan Aruch", "jewish"},
		{"rabbinic_responsa", "Rabbinic Responsa", "jewish"},
		{"beit_din_practice", "Beit Din Practice", "jewish"},
		{"noahide_law", "Noahide Law", "jewish"},
		{"dharmashastra", "Hindu Dharmashastra", "hindu"},
		{"manusmriti", "Manusmriti Tradition", "hindu"},
		{"yajnavalkya_smriti", "Yajnavalkya Smriti", "hindu"},
		{"narada_smriti", "Narada Smriti", "hindu"},
		{"mitakshara", "Mitakshara School", "hindu"},
		{"dayabhaga", "Dayabhaga School", "hindu"},
		{"arthashastra_norms", "Arthashastra Norms", "hindu"},
		{"agama_hindu", "Hindu Agama Codes", "hindu"},
		{"vinaya", "Buddhist Vinaya", "buddhist"},
		{"theravada_vinaya", "Theravada Vinaya", "buddhist"},
		{"mahayana_vinaya", "Mahayana Vinaya", "buddhist"},
		{"mulasarvastivada_vinaya", "Mulasarvastivada Vinaya", "buddhist"},
		{"upasaka_precepts", "Buddhist Lay Precepts", "buddhist"},
		{"jain_agama", "Jain Agama", "jain"},
		{"jain_digambara", "Digambara Conduct Code", "jain"},
		{"jain_svetambara", "Svetambara Conduct Code", "jain"},
		{"sikh_rehat", "Sikh Rehat Maryada", "sikh"},
		{"tankhah_code", "Sikh Tankhah Code", "sikh"},
		{"khalsa_rahit", "Khalsa Rahit", "sikh"},
		{"shinto_norito", "Shinto Ritual Law", "shinto"},
		{"shinto_jingi", "Jingi Institution Norms", "shinto"},
		{"taoist_precepts", "Taoist Precepts", "taoist"},
		{"confucian_li", "Confucian Li Norms", "confucian"},
		{"zoroastrian_dadestan", "Zoroastrian Dadestan", "zoroastrian"},
		{"baha_i_law", "Bahai Administrative Law", "bahai"},
		{"tenrikyo_oyasama", "Tenrikyo Conduct Norms", "tenrikyo"},
		{"caodai_rites", "Cao Dai Ritual Norms", "caodai"},
	}
	recs := seedCollection{Collection: "ai.gftd.apps.religious.religious_tradition"}
	for _, s := range systems {
		def.DIDs = append(def.DIDs, seedDID{Path: "system:" + s.id, DisplayName: s.name, Description: s.family})
		recs.Items = append(recs.Items, seedRecord{ID: s.id, Data: map[string]any{
			"id": s.id, "name": s.name, "family": s.family, "status": "active",
			"kind": "religious", "authority_kind": "religious", "tier": "religious",
			"sensitivity_ord": 0,
		}})
	}
	def.Records = append(def.Records, recs)
	return def
}

func customarySeeds() seedDef {
	def := seedDef{Domain: "customary", Nanoid: "cst0m4ry", DID: "did:web:customary.etzhayyim.com"}
	systems := []struct{ id, name, region string }{
		{"adat_indonesia", "Adat (Indonesia)", "southeast_asia"},
		{"aboriginal_aus", "Aboriginal Customary Law", "oceania"},
		{"maori_tikanga", "Tikanga Māori", "oceania"},
		{"ubuntu_southern_africa", "Ubuntu Law", "sub_saharan_africa"},
		{"gacaca_rwanda", "Gacaca Courts", "sub_saharan_africa"},
		{"xeer_somali", "Xeer (Somali)", "east_africa"},
		{"panchayat_india", "Panchayat System", "south_asia"},
		{"jirga_pashtun", "Jirga (Pashtun)", "south_asia"},
		{"roma_kris", "Romani Kris", "europe"},
		{"indigenous_americas", "Indigenous American Law", "americas"},
	}
	recs := seedCollection{Collection: "ai.gftd.apps.customary.customary_norm"}
	for _, s := range systems {
		def.DIDs = append(def.DIDs, seedDID{Path: "system:" + s.id, DisplayName: s.name, Description: s.region})
		recs.Items = append(recs.Items, seedRecord{ID: s.id, Data: map[string]any{
			"id": s.id, "name": s.name, "region": s.region, "status": "active",
			"kind": "customary", "authority_kind": "customary", "tier": "customary",
			"jurisdiction": s.region, "sensitivity_ord": 0,
		}})
	}
	def.Records = append(def.Records, recs)
	return def
}

func communityAuthoritySeeds() seedDef {
	def := seedDef{Domain: "community", Nanoid: "2tqvrutp", DID: "did:web:communities.etzhayyim.com"}
	orgs := []struct{ id, name, description string }{
		{"linux_foundation", "Linux Foundation", "Open source governance community"},
		{"wikipedia", "Wikipedia Community", "Volunteer knowledge commons"},
		{"apache", "Apache Software Foundation", "Foundation-led software community"},
		{"cncf", "Cloud Native Computing Foundation", "Cloud native ecosystem community"},
		{"stack_overflow", "Stack Overflow", "Developer question and answer community"},
	}
	recs := seedCollection{Collection: "ai.gftd.apps.communities.org"}
	for _, org := range orgs {
		def.DIDs = append(def.DIDs, seedDID{Path: "community:" + org.id, DisplayName: org.name, Description: org.description})
		recs.Items = append(recs.Items, seedRecord{ID: org.id, Data: map[string]any{
			"id":              org.id,
			"name":            org.name,
			"description":     org.description,
			"status":          "active",
			"kind":            "community",
			"authority_kind":  "community",
			"tier":            "community",
			"sensitivity_ord": 0,
		}})
	}
	def.Records = append(def.Records, recs)
	return def
}

func familyAuthoritySeeds() seedDef {
	def := seedDef{Domain: "family", Nanoid: "trdtn001", DID: "did:web:tradition.etzhayyim.com"}
	systems := []struct{ id, name, region string }{
		{"ie_stem_family", "Stem Family", "japan"},
		{"nuclear_family", "Nuclear Family", "global"},
		{"extended_family", "Extended Family", "global"},
		{"clan_lineage", "Clan Lineage", "east_asia"},
		{"filial_piety", "Filial Piety", "east_asia"},
	}
	recs := seedCollection{Collection: "ai.gftd.apps.tradition.tradition"}
	for _, system := range systems {
		def.DIDs = append(def.DIDs, seedDID{Path: "family:" + system.id, DisplayName: system.name, Description: system.region})
		recs.Items = append(recs.Items, seedRecord{ID: system.id, Data: map[string]any{
			"id":              system.id,
			"name":            system.name,
			"description":     system.region,
			"status":          "active",
			"kind":            "family",
			"authority_kind":  "family",
			"tier":            "family",
			"jurisdiction":    system.region,
			"sensitivity_ord": 0,
		}})
	}
	def.Records = append(def.Records, recs)
	return def
}

func culturalAuthoritySeeds() seedDef {
	def := seedDef{Domain: "cultural", Nanoid: "trdtn001", DID: "did:web:tradition.etzhayyim.com"}
	practices := []struct{ id, name, region string }{
		{"tea_ceremony", "Tea Ceremony", "japan"},
		{"ikebana", "Ikebana", "japan"},
		{"ubuntu", "Ubuntu", "southern_africa"},
		{"hanami", "Hanami", "japan"},
		{"diwali", "Diwali", "south_asia"},
	}
	recs := seedCollection{Collection: "ai.gftd.apps.tradition.tradition"}
	for _, practice := range practices {
		def.DIDs = append(def.DIDs, seedDID{Path: "culture:" + practice.id, DisplayName: practice.name, Description: practice.region})
		recs.Items = append(recs.Items, seedRecord{ID: practice.id, Data: map[string]any{
			"id":              practice.id,
			"name":            practice.name,
			"description":     practice.region,
			"status":          "active",
			"kind":            "cultural",
			"authority_kind":  "cultural",
			"tier":            "cultural",
			"jurisdiction":    practice.region,
			"sensitivity_ord": 0,
		}})
	}
	def.Records = append(def.Records, recs)
	return def
}

func professionalAuthoritySeeds() seedDef {
	def := seedDef{Domain: "professional", Nanoid: "eth1cs01", DID: "did:web:ethics.etzhayyim.com"}
	codes := []struct{ id, name, profession string }{
		{"ieee", "IEEE Code of Ethics", "engineering"},
		{"ama", "AMA Code of Medical Ethics", "medicine"},
		{"aba", "ABA Model Rules", "legal"},
		{"cfa", "CFA Standards of Practice", "finance"},
		{"icn", "ICN Code of Ethics for Nurses", "nursing"},
	}
	recs := seedCollection{Collection: "ai.gftd.apps.ethics.code"}
	for _, code := range codes {
		def.DIDs = append(def.DIDs, seedDID{Path: "profession:" + code.id, DisplayName: code.name, Description: code.profession})
		recs.Items = append(recs.Items, seedRecord{ID: code.id, Data: map[string]any{
			"id":              code.id,
			"name":            code.name,
			"description":     code.profession,
			"status":          "active",
			"kind":            "professional",
			"authority_kind":  "professional",
			"tier":            "professional",
			"jurisdiction":    code.profession,
			"sensitivity_ord": 0,
		}})
	}
	def.Records = append(def.Records, recs)
	return def
}

func academicAuthoritySeeds() seedDef {
	def := seedDef{Domain: "academic", Nanoid: "eth1cs01", DID: "did:web:ethics.etzhayyim.com"}
	norms := []struct{ id, name, field string }{
		{"apa_ethics", "APA Ethics Code", "psychology"},
		{"mla_style", "MLA Style", "humanities"},
		{"chicago_manual", "Chicago Manual of Style", "publishing"},
		{"research_integrity", "Research Integrity Norms", "science"},
		{"peer_review", "Peer Review Practice", "scholarship"},
	}
	recs := seedCollection{Collection: "ai.gftd.apps.ethics.code"}
	for _, norm := range norms {
		def.DIDs = append(def.DIDs, seedDID{Path: "academic:" + norm.id, DisplayName: norm.name, Description: norm.field})
		recs.Items = append(recs.Items, seedRecord{ID: norm.id, Data: map[string]any{
			"id":              norm.id,
			"name":            norm.name,
			"description":     norm.field,
			"status":          "active",
			"kind":            "academic",
			"authority_kind":  "academic",
			"tier":            "academic",
			"jurisdiction":    norm.field,
			"sensitivity_ord": 0,
		}})
	}
	def.Records = append(def.Records, recs)
	return def
}

func industryAuthoritySeeds() seedDef {
	def := seedDef{Domain: "industry", Nanoid: "indstd01", DID: "did:web:industry-standard.etzhayyim.com"}
	standards := []struct{ id, name, sector string }{
		{"iso_9001", "ISO 9001", "quality"},
		{"iso_27001", "ISO 27001", "security"},
		{"iso_14001", "ISO 14001", "environment"},
		{"pci_dss", "PCI DSS", "payments"},
		{"soc2", "SOC 2", "service_assurance"},
	}
	recs := seedCollection{Collection: "ai.gftd.apps.industrystandard.standard"}
	for _, standard := range standards {
		def.DIDs = append(def.DIDs, seedDID{Path: "standard:" + standard.id, DisplayName: standard.name, Description: standard.sector})
		recs.Items = append(recs.Items, seedRecord{ID: standard.id, Data: map[string]any{
			"id":              standard.id,
			"name":            standard.name,
			"description":     standard.sector,
			"status":          "active",
			"kind":            "industry",
			"authority_kind":  "industry",
			"tier":            "industry",
			"jurisdiction":    standard.sector,
			"sensitivity_ord": 0,
		}})
	}
	def.Records = append(def.Records, recs)
	return def
}

func suidoSeeds() seedDef {
	def := seedDef{Domain: "suido", Nanoid: "su1d0jp0", DID: "did:web:suido.etzhayyim.com"}
	// Top 20 water utilities in Japan
	utilities := []struct{ id, name, pref string }{
		{"tokyo", "東京都水道局", "東京"}, {"osaka", "大阪市水道局", "大阪"},
		{"yokohama", "横浜市水道局", "神奈川"}, {"nagoya", "名古屋市上下水道局", "愛知"},
		{"sapporo", "札幌市水道局", "北海道"}, {"fukuoka", "福岡市水道局", "福岡"},
		{"kobe", "神戸市水道局", "兵庫"}, {"kyoto", "京都市上下水道局", "京都"},
		{"kawasaki", "川崎市上下水道局", "神奈川"}, {"saitama", "さいたま市水道局", "埼玉"},
		{"hiroshima", "広島市水道局", "広島"}, {"sendai", "仙台市水道局", "宮城"},
		{"chiba", "千葉県水道局", "千葉"}, {"kitakyushu", "北九州市上下水道局", "福岡"},
		{"niigata", "新潟市水道局", "新潟"}, {"hamamatsu", "浜松市上下水道部", "静岡"},
		{"kumamoto", "熊本市上下水道局", "熊本"}, {"okayama", "岡山市水道局", "岡山"},
		{"shizuoka", "静岡市上下水道局", "静岡"}, {"sagamihara", "相模原市水道局", "神奈川"},
	}
	recs := seedCollection{Collection: "ai.gftd.apps.suido.water_utility"}
	for _, u := range utilities {
		def.DIDs = append(def.DIDs, seedDID{Path: "utility:" + u.id, DisplayName: u.name, Description: u.pref})
		recs.Items = append(recs.Items, seedRecord{ID: u.id, Data: map[string]any{
			"id": u.id, "name": u.name, "prefecture": u.pref, "status": "active",
		}})
	}
	def.Records = append(def.Records, recs)
	return def
}

func cpcSeeds() seedDef {
	// UN CPC Ver.2.1 — Central Product Classification (UNSD, authoritative hierarchy).
	// 10 Sections + 71 Divisions seeded. Groups (305) / Classes (1 167) / Subclasses
	// (2 738) are deferred to follow-up ingestion passes.
	def := seedDef{Domain: "cpc", Nanoid: "cpc5c0v2", DID: "did:web:cpc.etzhayyim.com"}
	sections := []struct{ code, name string }{
		{"0", "Agriculture, forestry and fishery products"},
		{"1", "Ores and minerals; electricity, gas and water"},
		{"2", "Food products, beverages and tobacco; textiles, apparel and leather products"},
		{"3", "Other transportable goods, except metal products, machinery and equipment"},
		{"4", "Metal products, machinery and equipment"},
		{"5", "Constructions and construction services"},
		{"6", "Distributive trade services; accommodation, food and beverage serving services; transport services; and electricity, gas and water distribution services"},
		{"7", "Financial and related services; real estate services; and rental and leasing services"},
		{"8", "Business and production services"},
		{"9", "Community, social and personal services"},
	}
	divisions := []struct{ code, section, name string }{
		// Section 0 — Agriculture, forestry and fishery products (4)
		{"01", "0", "Products of agriculture, horticulture and market gardening"},
		{"02", "0", "Live animals and animal products (excluding meat)"},
		{"03", "0", "Forestry and logging products"},
		{"04", "0", "Fish and other fishing products"},
		// Section 1 — Ores and minerals; electricity, gas and water (8)
		{"11", "1", "Coal and lignite; peat"},
		{"12", "1", "Crude petroleum and natural gas"},
		{"13", "1", "Uranium and thorium ores"},
		{"14", "1", "Metal ores"},
		{"15", "1", "Stone, sand and clay"},
		{"16", "1", "Other minerals"},
		{"17", "1", "Electricity, town gas, steam and hot water"},
		{"18", "1", "Water"},
		// Section 2 — Food, beverages, tobacco; textiles, apparel, leather (9)
		{"21", "2", "Meat, fish, fruit, vegetables, oils and fats"},
		{"22", "2", "Dairy products and egg products"},
		{"23", "2", "Grain mill products, starches and starch products; other food products"},
		{"24", "2", "Beverages"},
		{"25", "2", "Tobacco products"},
		{"26", "2", "Yarn and thread; woven and tufted textile fabrics"},
		{"27", "2", "Textile articles other than apparel"},
		{"28", "2", "Knitted or crocheted fabrics; wearing apparel"},
		{"29", "2", "Leather and leather products; footwear"},
		// Section 3 — Other transportable goods (9)
		{"31", "3", "Products of wood, cork, straw and plaiting materials"},
		{"32", "3", "Pulp, paper and paper products; printed matter and related articles"},
		{"33", "3", "Coke oven products; refined petroleum products; nuclear fuel"},
		{"34", "3", "Basic chemicals"},
		{"35", "3", "Other chemical products; man-made fibres"},
		{"36", "3", "Rubber and plastics products"},
		{"37", "3", "Glass and glass products and other non-metallic products n.e.c."},
		{"38", "3", "Furniture; other transportable goods n.e.c."},
		{"39", "3", "Wastes or scraps"},
		// Section 4 — Metal products, machinery and equipment (9)
		{"41", "4", "Basic metals"},
		{"42", "4", "Fabricated metal products, except machinery and equipment"},
		{"43", "4", "General-purpose machinery"},
		{"44", "4", "Special-purpose machinery"},
		{"45", "4", "Office, accounting and computing machinery"},
		{"46", "4", "Electrical machinery and apparatus"},
		{"47", "4", "Radio, television and communication equipment and apparatus"},
		{"48", "4", "Medical appliances, precision and optical instruments, watches and clocks"},
		{"49", "4", "Transport equipment"},
		// Section 5 — Constructions and construction services (2)
		{"53", "5", "Constructions"},
		{"54", "5", "Construction services"},
		// Section 6 — Distributive trade; transport; utility distribution (9)
		{"61", "6", "Wholesale trade services, except of motor vehicles and motorcycles"},
		{"62", "6", "Retail trade services, except of motor vehicles and motorcycles"},
		{"63", "6", "Sale, maintenance and repair services of motor vehicles and motorcycles"},
		{"64", "6", "Accommodation, food and beverage serving services"},
		{"65", "6", "Passenger transport services"},
		{"66", "6", "Freight transport services"},
		{"67", "6", "Supporting transport services"},
		{"68", "6", "Postal and courier services"},
		{"69", "6", "Electricity, gas and water distribution services (on own account)"},
		// Section 7 — Financial; real estate; rental/leasing (3)
		{"71", "7", "Financial and related services"},
		{"72", "7", "Real estate services"},
		{"73", "7", "Leasing or rental services without operator"},
		// Section 8 — Business and production services (9)
		{"81", "8", "Research and development services"},
		{"82", "8", "Legal and accounting services"},
		{"83", "8", "Other professional, scientific and technical services"},
		{"84", "8", "Telecommunications, broadcasting and information supply services"},
		{"85", "8", "Support services"},
		{"86", "8", "Agriculture, mining and manufacturing related services"},
		{"87", "8", "Maintenance, repair and installation (except construction) services"},
		{"88", "8", "Manufacturing services on physical inputs owned by others"},
		{"89", "8", "Other manufacturing services; publishing, printing and reproduction services; materials recovery services"},
		// Section 9 — Community, social and personal services (9)
		{"91", "9", "Public administration and other services provided to the community as a whole"},
		{"92", "9", "Education services"},
		{"93", "9", "Human health and social care services"},
		{"94", "9", "Sewage and waste collection, treatment and disposal services"},
		{"95", "9", "Services of membership organizations"},
		{"96", "9", "Recreational, cultural and sporting services"},
		{"97", "9", "Other services"},
		{"98", "9", "Domestic services"},
		{"99", "9", "Services provided by extraterritorial organizations and bodies"},
	}
	recs := seedCollection{Collection: "ai.gftd.apps.cpc.commodity_item"}
	for _, s := range sections {
		def.DIDs = append(def.DIDs, seedDID{Path: "section:" + s.code, DisplayName: s.name, Description: "CPC Ver.2.1 Section " + s.code})
		recs.Items = append(recs.Items, seedRecord{ID: s.code, Data: map[string]any{
			"id": s.code, "code": s.code, "name": s.name, "level": "section", "status": "active",
		}})
	}
	for _, d := range divisions {
		def.DIDs = append(def.DIDs, seedDID{
			Path:        "division:" + d.code,
			DisplayName: d.name,
			Description: fmt.Sprintf("CPC Ver.2.1 Division %s (Section %s)", d.code, d.section),
		})
		recs.Items = append(recs.Items, seedRecord{ID: d.code, Data: map[string]any{
			"id":      d.code,
			"code":    d.code,
			"name":    d.name,
			"level":   "division",
			"section": d.section,
			"parent":  d.section,
			"status":  "active",
		}})
	}
	// Subclasses (5-digit) — codes are UN CPC Ver.2.1 canonical; names carried
	// over from archived component implementations and may need UNSD-master
	// refinement on a later pass.
	subclasses := []struct{ code, name, section, division, group, class string }{
		{"01111", "Wheat", "0", "01", "011", "0111"},
		{"01112", "Maize Corn", "0", "01", "011", "0111"},
		{"01113", "Rice Paddy", "0", "01", "011", "0111"},
		{"01114", "Barley", "0", "01", "011", "0111"},
		{"01115", "Rye", "0", "01", "011", "0111"},
		{"01116", "Oats", "0", "01", "011", "0111"},
		{"01119", "Other Cereals n.e.c.", "0", "01", "011", "0111"},
		{"01211", "Potatoes", "0", "01", "012", "0121"},
		{"01212", "Sweet Potatoes", "0", "01", "012", "0121"},
		{"01311", "Beans Green", "0", "01", "013", "0131"},
		{"01312", "Peas Green", "0", "01", "013", "0131"},
		{"01411", "Soya Beans", "0", "01", "014", "0141"},
		{"01412", "Groundnuts", "0", "01", "014", "0141"},
		{"01511", "Coconuts", "0", "01", "015", "0151"},
		{"01611", "Oil Palm Fruit", "0", "01", "016", "0161"},
		{"01711", "Coffee Not Roasted", "0", "01", "017", "0171"},
		{"01712", "Tea", "0", "01", "017", "0171"},
		{"01811", "Sugar Cane", "0", "01", "018", "0181"},
		{"01911", "Tobacco Unmanufactured", "0", "01", "019", "0191"},
		{"02111", "Cattle Live", "0", "02", "021", "0211"},
		{"02112", "Sheep Live", "0", "02", "021", "0211"},
		{"02113", "Swine Live", "0", "02", "021", "0211"},
		{"02114", "Poultry Live", "0", "02", "021", "0211"},
		{"02211", "Raw Milk From Cattle", "0", "02", "022", "0221"},
		{"02311", "Hen Eggs In Shell", "0", "02", "023", "0231"},
		{"02411", "Honey Natural", "0", "02", "024", "0241"},
		{"03111", "Logs Coniferous", "0", "03", "031", "0311"},
		{"03112", "Logs Non Coniferous", "0", "03", "031", "0311"},
		{"03211", "Fuel Wood", "0", "03", "032", "0321"},
		{"04111", "Fish Live", "0", "04", "041", "0411"},
		{"04121", "Fish Fresh Or Chilled", "0", "04", "041", "0412"},
		{"04211", "Crustaceans", "0", "04", "042", "0421"},
		{"11010", "Coal", "1", "11", "110", "1101"},
		{"11020", "Lignite", "1", "11", "110", "1102"},
		{"11030", "Peat", "1", "11", "110", "1103"},
		{"12011", "Crude Petroleum", "1", "12", "120", "1201"},
		{"12021", "Natural Gas, Liquefied Or Gaseous", "1", "12", "120", "1202"},
		{"13010", "Uranium And Thorium Ores", "1", "13", "130", "1301"},
		{"14110", "Iron Ores", "1", "14", "141", "1411"},
		{"14210", "Copper Ores", "1", "14", "142", "1421"},
		{"14310", "Nickel Ores", "1", "14", "143", "1431"},
		{"14410", "Aluminium Ores", "1", "14", "144", "1441"},
		{"14510", "Precious Metal Ores", "1", "14", "145", "1451"},
		{"14610", "Lead, Zinc And Tin Ores", "1", "14", "146", "1461"},
		{"17100", "Electric Power Supply", "1", "17", "171", "1710"},
		{"17200", "Gas Supply", "1", "17", "172", "1720"},
		{"17300", "Steam And Air Conditioning Supply", "1", "17", "173", "1730"},
		{"18000", "Water Supply", "1", "18", "180", "1800"},
		{"21111", "Meat Of Mammals, Fresh Or Chilled", "2", "21", "211", "2111"},
		{"32111", "Newsprint", "3", "32", "321", "3211"},
		{"34111", "Industrial Gas", "3", "34", "341", "3411"},
		{"35410", "Glues And Prepared Admixtures", "3", "35", "354", "3541"},
		{"41111", "Basic Iron And Steel", "4", "41", "411", "4111"},
		{"44111", "Internal Combustion Engines", "4", "44", "441", "4411"},
		{"54111", "General Construction Services Of Residential Buildings", "5", "54", "541", "5411"},
		{"61184", "Wholesale Trade Services Of Computers And Software", "6", "61", "611", "6118"},
		{"62111", "Food Retail Services", "6", "62", "621", "6211"},
		{"63110", "Hotel Lodging Services", "6", "63", "631", "6311"},
		{"63210", "Meal Serving Services", "6", "63", "632", "6321"},
		{"64112", "Railway Freight Transport Services", "6", "64", "641", "6411"},
		{"64211", "Scheduled Air Passenger Transport", "6", "64", "642", "6421"},
		{"71110", "Central Banking Services", "7", "71", "711", "7111"},
		{"71211", "Deposit Services", "7", "71", "712", "7121"},
		{"71311", "Life Insurance Services", "7", "71", "713", "7131"},
		{"71411", "Pension Funding Services", "7", "71", "714", "7141"},
		{"71511", "Financial Leasing Services", "7", "71", "715", "7151"},
		{"71611", "Digital Payment Services", "7", "71", "716", "7161"},
		{"71621", "Cryptocurrency Exchange Services", "7", "71", "716", "7162"},
		{"71631", "Blockchain-Based Financial Services", "7", "71", "716", "7163"},
		{"72111", "Residential Real Estate Rental Services", "7", "72", "721", "7211"},
		{"82111", "Legal Advisory And Representation Services", "8", "82", "821", "8211"},
		{"82211", "Financial Auditing Services", "8", "82", "822", "8221"},
		{"82311", "Business And Management Consultancy Services", "8", "82", "823", "8231"},
		{"83111", "Management Consulting Services", "8", "83", "831", "8311"},
		{"83131", "IT Consulting Services", "8", "83", "831", "8313"},
		{"83141", "Information Security Services", "8", "83", "831", "8314"},
		{"83151", "Cloud Hosting Services (IaaS)", "8", "83", "831", "8315"},
		{"83152", "Cloud Platform Services (PaaS)", "8", "83", "831", "8315"},
		{"83153", "Cloud Software Services (SaaS)", "8", "83", "831", "8315"},
		{"83154", "Cloud Application Hosting Services", "8", "83", "831", "8315"},
		{"83161", "IT Infrastructure Provisioning Services", "8", "83", "831", "8316"},
		{"83162", "AI Inference Services", "8", "83", "831", "8316"},
		{"83163", "Natural Language Processing Services", "8", "83", "831", "8316"},
		{"83164", "Computer Vision Services", "8", "83", "831", "8316"},
		{"83171", "Data-As-A-Product Services", "8", "83", "831", "8317"},
		{"83172", "Data Analytics Services", "8", "83", "831", "8317"},
		{"83173", "Big Data Processing Services", "8", "83", "831", "8317"},
		{"83181", "Network Management Services", "8", "83", "831", "8318"},
		{"83211", "Architectural Services", "8", "83", "832", "8321"},
		{"83311", "Engineering Services", "8", "83", "833", "8331"},
		{"83990", "Compliance Services", "8", "83", "839", "8399"},
	}
	for _, sc := range subclasses {
		def.DIDs = append(def.DIDs, seedDID{
			Path:        "subclass:" + sc.code,
			DisplayName: sc.name,
			Description: fmt.Sprintf("CPC Ver.2.1 Subclass %s (Division %s)", sc.code, sc.division),
		})
		recs.Items = append(recs.Items, seedRecord{ID: sc.code, Data: map[string]any{
			"id":       sc.code,
			"code":     sc.code,
			"name":     sc.name,
			"level":    "subclass",
			"section":  sc.section,
			"division": sc.division,
			"group":    sc.group,
			"class":    sc.class,
			"parent":   sc.class,
			"status":   "active",
		}})
	}
	def.Records = append(def.Records, recs)
	return def
}

func commoditiesSeeds() seedDef {
	def := seedDef{Domain: "commodities", Nanoid: "cmdty001", DID: "did:web:commodities.etzhayyim.com"}
	items := []struct{ id, name, category string }{
		{"crude_oil", "Crude Oil (WTI)", "energy"}, {"brent", "Brent Crude", "energy"},
		{"natural_gas", "Natural Gas", "energy"}, {"gold", "Gold", "precious_metals"},
		{"silver", "Silver", "precious_metals"}, {"copper", "Copper", "base_metals"},
		{"aluminum", "Aluminum", "base_metals"}, {"wheat", "Wheat", "agriculture"},
		{"corn", "Corn", "agriculture"}, {"soybeans", "Soybeans", "agriculture"},
	}
	recs := seedCollection{Collection: "ai.gftd.apps.commodities.commodity_item"}
	for _, c := range items {
		def.DIDs = append(def.DIDs, seedDID{Path: "commodity:" + c.id, DisplayName: c.name, Description: c.category})
		recs.Items = append(recs.Items, seedRecord{ID: c.id, Data: map[string]any{
			"id": c.id, "name": c.name, "category": c.category, "status": "active",
		}})
	}
	def.Records = append(def.Records, recs)
	return def
}

func cofogSeeds() seedDef {
	def := seedDef{Domain: "cofog", Nanoid: "c0f0g001", DID: "did:web:cofog.etzhayyim.com"}
	functions := []struct{ code, name string }{
		{"01", "General public services"}, {"02", "Defence"},
		{"03", "Public order and safety"}, {"04", "Economic affairs"},
		{"05", "Environmental protection"}, {"06", "Housing and community amenities"},
		{"07", "Health"}, {"08", "Recreation, culture and religion"},
		{"09", "Education"}, {"10", "Social protection"},
	}
	recs := seedCollection{Collection: "ai.gftd.apps.cofog.governance_policy"}
	for _, f := range functions {
		def.DIDs = append(def.DIDs, seedDID{Path: "function:" + f.code, DisplayName: f.name, Description: "COFOG " + f.code})
		recs.Items = append(recs.Items, seedRecord{ID: f.code, Data: map[string]any{
			"id": f.code, "code": f.code, "name": f.name, "level": 1, "status": "active",
		}})
	}
	def.Records = append(def.Records, recs)
	return def
}

func telecomSeeds() seedDef {
	def := seedDef{Domain: "telecom", Nanoid: "t3l3c0m1", DID: "did:web:telecom.etzhayyim.com"}
	operators := []struct{ id, name, country string }{
		{"ntt_docomo", "NTT docomo", "jpn"}, {"kddi_au", "KDDI au", "jpn"},
		{"softbank_mobile", "SoftBank", "jpn"}, {"rakuten_mobile", "Rakuten Mobile", "jpn"},
		{"att", "AT&T", "usa"}, {"verizon", "Verizon", "usa"},
		{"tmobile", "T-Mobile", "usa"}, {"china_mobile", "China Mobile", "chn"},
		{"vodafone", "Vodafone", "gbr"}, {"deutsche_telekom", "Deutsche Telekom", "deu"},
	}
	recs := seedCollection{Collection: "ai.gftd.apps.telecom.telecom_carrier"}
	for _, o := range operators {
		def.DIDs = append(def.DIDs, seedDID{Path: "operator:" + o.id, DisplayName: o.name, Description: o.country})
		recs.Items = append(recs.Items, seedRecord{ID: o.id, Data: map[string]any{
			"id": o.id, "name": o.name, "country": o.country, "status": "active",
		}})
	}
	def.Records = append(def.Records, recs)
	return def
}

func society6Seeds() seedDef {
	def := seedDef{Domain: "society6", Nanoid: "s0c1ty06", DID: "did:web:society6.etzhayyim.com"}
	// COFOG × Well-Becoming: top 10 national systems as seed
	recs := seedCollection{Collection: "ai.gftd.apps.society6.well_becoming"}
	for _, s := range []struct{ iso3, name string }{
		{"jpn", "Japan"}, {"usa", "United States"}, {"gbr", "United Kingdom"},
		{"deu", "Germany"}, {"fra", "France"}, {"swe", "Sweden"},
		{"nor", "Norway"}, {"fin", "Finland"}, {"dnk", "Denmark"}, {"che", "Switzerland"},
	} {
		def.DIDs = append(def.DIDs, seedDID{Path: "system:" + s.iso3, DisplayName: s.name + " Well-Becoming", Description: "Kyu/Dan scoring system"})
		recs.Items = append(recs.Items, seedRecord{ID: s.iso3, Data: map[string]any{
			"id": s.iso3, "iso3": s.iso3, "name": s.name,
			"model": "well_becoming", "status": "active",
		}})
	}
	def.Records = append(def.Records, recs)
	return def
}

func casinoSeeds() seedDef {
	def := seedDef{Domain: "casino", Nanoid: "c4s1n001", DID: "did:web:casino.etzhayyim.com"}
	casinos := []struct{ id, name, location string }{
		{"marina_bay_sands", "Marina Bay Sands", "Singapore"},
		{"bellagio", "Bellagio", "Las Vegas, USA"},
		{"venetian_macao", "The Venetian Macao", "Macau"},
		{"city_of_dreams", "City of Dreams", "Macau"},
		{"monte_carlo", "Casino de Monte-Carlo", "Monaco"},
		{"crown_melbourne", "Crown Melbourne", "Australia"},
		{"okada_manila", "Okada Manila", "Philippines"},
		{"wynn_palace", "Wynn Palace", "Macau"},
		{"solaire", "Solaire Resort", "Philippines"},
		{"resorts_world", "Resorts World Sentosa", "Singapore"},
	}
	recs := seedCollection{Collection: "ai.gftd.apps.casino.casino_venue"}
	for _, c := range casinos {
		def.DIDs = append(def.DIDs, seedDID{Path: "casino:" + c.id, DisplayName: c.name, Description: c.location})
		recs.Items = append(recs.Items, seedRecord{ID: c.id, Data: map[string]any{
			"id": c.id, "name": c.name, "location": c.location, "status": "active",
		}})
	}
	def.Records = append(def.Records, recs)
	return def
}

func pachinkoSeeds() seedDef {
	def := seedDef{Domain: "pachinko", Nanoid: "p4ch1nk0", DID: "did:web:pachinko.etzhayyim.com"}
	// Top 10 pachinko chains
	chains := []struct {
		id, name string
		stores   int
	}{
		{"maruhan", "マルハン", 310}, {"dynam", "ダイナム", 400},
		{"gaia", "ガイア", 120}, {"keioh", "京楽", 80},
		{"suncity", "サンシティ", 60}, {"daiichi", "第一興商", 45},
		{"pworld", "パラダイス", 35}, {"jumbo", "ジャンボ", 30},
		{"nikkyu", "日邦", 25}, {"taiyo", "太陽", 20},
	}
	recs := seedCollection{Collection: "ai.gftd.apps.pachinko.pachinko_store"}
	for _, c := range chains {
		def.DIDs = append(def.DIDs, seedDID{Path: "chain:" + c.id, DisplayName: c.name, Description: fmt.Sprintf("%d stores", c.stores)})
		recs.Items = append(recs.Items, seedRecord{ID: c.id, Data: map[string]any{
			"id": c.id, "name": c.name, "store_count": c.stores, "status": "active",
		}})
	}
	def.Records = append(def.Records, recs)
	return def
}

func i18nSeeds() seedDef {
	def := seedDef{Domain: "i18n", Nanoid: "i18n0001", DID: "did:web:i18n.etzhayyim.com"}
	langs := []struct{ code, name, family string }{
		{"en", "English", "indo_european"}, {"zh", "Chinese", "sino_tibetan"},
		{"hi", "Hindi", "indo_european"}, {"es", "Spanish", "indo_european"},
		{"ar", "Arabic", "afro_asiatic"}, {"bn", "Bengali", "indo_european"},
		{"pt", "Portuguese", "indo_european"}, {"ru", "Russian", "indo_european"},
		{"ja", "Japanese", "japonic"}, {"de", "German", "indo_european"},
		{"fr", "French", "indo_european"}, {"ko", "Korean", "koreanic"},
		{"vi", "Vietnamese", "austroasiatic"}, {"it", "Italian", "indo_european"},
		{"tr", "Turkish", "turkic"}, {"th", "Thai", "kra_dai"},
		{"pl", "Polish", "indo_european"}, {"nl", "Dutch", "indo_european"},
		{"id", "Indonesian", "austronesian"}, {"sv", "Swedish", "indo_european"},
	}
	recs := seedCollection{Collection: "ai.gftd.apps.i18n.language"}
	for _, l := range langs {
		def.DIDs = append(def.DIDs, seedDID{Path: "language:" + l.code, DisplayName: l.name, Description: l.family})
		recs.Items = append(recs.Items, seedRecord{ID: l.code, Data: map[string]any{
			"id": l.code, "code": l.code, "name": l.name, "family": l.family, "status": "active",
		}})
	}
	def.Records = append(def.Records, recs)
	return def
}

func govSeeds() seedDef {
	def := seedDef{Domain: "gov", Nanoid: "g0v9a1cy", DID: "did:web:gov.etzhayyim.com"}
	agencies := []struct {
		id, name, country string
	}{
		{"jpn_moj", "Ministry of Justice (JP)", "jpn"},
		{"jpn_meti", "METI (JP)", "jpn"},
		{"jpn_mof", "Ministry of Finance (JP)", "jpn"},
		{"usa_doj", "Department of Justice (US)", "usa"},
		{"usa_treasury", "Department of the Treasury (US)", "usa"},
		{"deu_bmi", "Federal Ministry of the Interior (DE)", "deu"},
		{"fra_interieur", "Ministere de l Interieur (FR)", "fra"},
		{"gbr_home_office", "Home Office (UK)", "gbr"},
		{"can_justice", "Department of Justice (CA)", "can"},
		{"aus_home_affairs", "Department of Home Affairs (AU)", "aus"},
	}
	recs := seedCollection{Collection: "ai.gftd.apps.gov.legal_entity"}
	for _, a := range agencies {
		def.DIDs = append(def.DIDs, seedDID{
			Path:        "agency:" + a.id,
			DisplayName: a.name,
			Description: a.country,
		})
		recs.Items = append(recs.Items, seedRecord{ID: a.id, Data: map[string]any{
			"id": a.id, "name": a.name, "country": a.country, "status": "active",
		}})
	}
	def.Records = append(def.Records, recs)
	return def
}

func shinsaSeeds() seedDef {
	def := seedDef{Domain: "shinsa_process", Nanoid: "sh1n54pr", DID: "did:web:shinsa.etzhayyim.com"}
	recs := seedCollection{Collection: "ai.gftd.apps.shinsa.regulatory_filing"}
	categories := []struct {
		key, name string
	}{
		{"finance", "Loan Underwriting"},
		{"insurance", "Insurance Underwriting"},
		{"permit", "Business License Review"},
		{"immigration", "Visa Screening"},
		{"tax", "Tax Audit Screening"},
		{"pharma", "Drug Application Assessment"},
		{"infrastructure", "Construction Permit Review"},
		{"environment", "Environmental Impact Screening"},
		{"welfare", "Benefit Eligibility Assessment"},
		{"procurement", "Public Procurement Bid Review"},
		{"education", "School Grant Screening"},
		{"energy", "Energy Subsidy Assessment"},
	}
	jurisdictions := []string{
		"jpn", "usa", "deu", "fra", "gbr", "can", "aus", "kor", "sgp", "ind", "idn", "are",
		"ita", "esp", "nld", "swe", "nor", "fin", "dnk", "che", "aut", "bel", "irl", "nzl",
		"bra", "mex", "tur", "sau", "zaf", "arg",
	}
	stages := []string{"intake", "primary", "secondary", "final", "appeal", "audit", "fraud", "closure"}
	for _, c := range categories {
		for _, j := range jurisdictions {
			for _, s := range stages {
				id := fmt.Sprintf("%s_%s_%s", c.key, j, s)
				name := fmt.Sprintf("%s (%s %s)", c.name, j, s)
				def.DIDs = append(def.DIDs, seedDID{
					Path:        "assessment:" + id,
					DisplayName: name,
					Description: c.key,
				})
				recs.Items = append(recs.Items, seedRecord{ID: id, Data: map[string]any{
					"id": id, "name": name, "category": c.key, "jurisdiction": j, "stage": s, "status": "active",
				}})
			}
		}
	}
	def.Records = append(def.Records, recs)
	return def
}
