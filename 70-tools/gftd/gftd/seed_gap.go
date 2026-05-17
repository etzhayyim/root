// seed_gap.go — Gap coverage seed data for 178 apps.
// Generated — provides seedDef per app for gftd coverage gap filling.
package main

func AircraftGapSeeds() seedDef {
	def := seedDef{Domain: "aircraft", Nanoid: "ac7mv2xp", DID: "did:web:aircraft.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "aircraft:b737", DisplayName: "Boeing 737", Description: "Narrow-body commercial aircraft"})
	def.DIDs = append(def.DIDs, seedDID{Path: "aircraft:a320", DisplayName: "Airbus A320", Description: "Single-aisle commercial aircraft"})
	def.DIDs = append(def.DIDs, seedDID{Path: "aircraft:b777", DisplayName: "Boeing 777", Description: "Wide-body twin-engine aircraft"})
	def.DIDs = append(def.DIDs, seedDID{Path: "aircraft:a380", DisplayName: "Airbus A380", Description: "Double-deck wide-body aircraft"})
	def.DIDs = append(def.DIDs, seedDID{Path: "aircraft:b787", DisplayName: "Boeing 787 Dreamliner", Description: "Long-haul wide-body"})
	def.DIDs = append(def.DIDs, seedDID{Path: "aircraft:a350", DisplayName: "Airbus A350 XWB", Description: "Wide-body twin-engine"})
	def.DIDs = append(def.DIDs, seedDID{Path: "aircraft:c919", DisplayName: "COMAC C919", Description: "Chinese narrow-body"})
	def.DIDs = append(def.DIDs, seedDID{Path: "aircraft:e195", DisplayName: "Embraer E195", Description: "Regional jet"})
	recsaircraft := seedCollection{Collection: "ai.gftd.apps.aircraft.aircraft"}
	recsaircraft.Items = append(recsaircraft.Items, seedRecord{ID: "b737", Data: map[string]any{"id": "b737", "name": "Boeing 737", "description": "Narrow-body commercial aircraft", "status": "active"}})
	recsaircraft.Items = append(recsaircraft.Items, seedRecord{ID: "a320", Data: map[string]any{"id": "a320", "name": "Airbus A320", "description": "Single-aisle commercial aircraft", "status": "active"}})
	recsaircraft.Items = append(recsaircraft.Items, seedRecord{ID: "b777", Data: map[string]any{"id": "b777", "name": "Boeing 777", "description": "Wide-body twin-engine aircraft", "status": "active"}})
	recsaircraft.Items = append(recsaircraft.Items, seedRecord{ID: "a380", Data: map[string]any{"id": "a380", "name": "Airbus A380", "description": "Double-deck wide-body aircraft", "status": "active"}})
	recsaircraft.Items = append(recsaircraft.Items, seedRecord{ID: "b787", Data: map[string]any{"id": "b787", "name": "Boeing 787 Dreamliner", "description": "Long-haul wide-body", "status": "active"}})
	recsaircraft.Items = append(recsaircraft.Items, seedRecord{ID: "a350", Data: map[string]any{"id": "a350", "name": "Airbus A350 XWB", "description": "Wide-body twin-engine", "status": "active"}})
	recsaircraft.Items = append(recsaircraft.Items, seedRecord{ID: "c919", Data: map[string]any{"id": "c919", "name": "COMAC C919", "description": "Chinese narrow-body", "status": "active"}})
	recsaircraft.Items = append(recsaircraft.Items, seedRecord{ID: "e195", Data: map[string]any{"id": "e195", "name": "Embraer E195", "description": "Regional jet", "status": "active"}})
	def.Records = append(def.Records, recsaircraft)
	return def
}

func AnimaGapSeeds() seedDef {
	def := seedDef{Domain: "anima", Nanoid: "czj1f6yv", DID: "did:web:anima.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "species:canis_lupus", DisplayName: "オオカミ (Gray Wolf)", Description: "Mammalia Carnivora"})
	def.DIDs = append(def.DIDs, seedDID{Path: "species:panthera_tigris", DisplayName: "トラ (Tiger)", Description: "Mammalia Carnivora"})
	def.DIDs = append(def.DIDs, seedDID{Path: "species:elephas_maximus", DisplayName: "アジアゾウ (Asian Elephant)", Description: "Mammalia Proboscidea"})
	def.DIDs = append(def.DIDs, seedDID{Path: "species:tursiops", DisplayName: "バンドウイルカ (Bottlenose Dolphin)", Description: "Mammalia Cetacea"})
	def.DIDs = append(def.DIDs, seedDID{Path: "species:corvus", DisplayName: "カラス (Crow)", Description: "Aves Passeriformes"})
	def.DIDs = append(def.DIDs, seedDID{Path: "species:apis_mellifera", DisplayName: "ミツバチ (Honey Bee)", Description: "Insecta Hymenoptera"})
	def.DIDs = append(def.DIDs, seedDID{Path: "species:octopus_vulgaris", DisplayName: "マダコ (Common Octopus)", Description: "Cephalopoda"})
	recsspecies := seedCollection{Collection: "ai.gftd.apps.anima.species"}
	recsspecies.Items = append(recsspecies.Items, seedRecord{ID: "canis_lupus", Data: map[string]any{"id": "canis_lupus", "name": "オオカミ (Gray Wolf)", "description": "Mammalia Carnivora", "status": "active"}})
	recsspecies.Items = append(recsspecies.Items, seedRecord{ID: "panthera_tigris", Data: map[string]any{"id": "panthera_tigris", "name": "トラ (Tiger)", "description": "Mammalia Carnivora", "status": "active"}})
	recsspecies.Items = append(recsspecies.Items, seedRecord{ID: "elephas_maximus", Data: map[string]any{"id": "elephas_maximus", "name": "アジアゾウ (Asian Elephant)", "description": "Mammalia Proboscidea", "status": "active"}})
	recsspecies.Items = append(recsspecies.Items, seedRecord{ID: "tursiops", Data: map[string]any{"id": "tursiops", "name": "バンドウイルカ (Bottlenose Dolphin)", "description": "Mammalia Cetacea", "status": "active"}})
	recsspecies.Items = append(recsspecies.Items, seedRecord{ID: "corvus", Data: map[string]any{"id": "corvus", "name": "カラス (Crow)", "description": "Aves Passeriformes", "status": "active"}})
	recsspecies.Items = append(recsspecies.Items, seedRecord{ID: "apis_mellifera", Data: map[string]any{"id": "apis_mellifera", "name": "ミツバチ (Honey Bee)", "description": "Insecta Hymenoptera", "status": "active"}})
	recsspecies.Items = append(recsspecies.Items, seedRecord{ID: "octopus_vulgaris", Data: map[string]any{"id": "octopus_vulgaris", "name": "マダコ (Common Octopus)", "description": "Cephalopoda", "status": "active"}})
	def.Records = append(def.Records, recsspecies)
	return def
}

func ApiGapSeeds() seedDef {
	def := seedDef{Domain: "api", Nanoid: "ap1sv01", DID: "did:web:api.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "endpoint:rest_users", DisplayName: "REST /users", Description: "User management API"})
	def.DIDs = append(def.DIDs, seedDID{Path: "endpoint:graphql", DisplayName: "GraphQL /graphql", Description: "Query API"})
	def.DIDs = append(def.DIDs, seedDID{Path: "endpoint:websocket", DisplayName: "WebSocket /ws", Description: "Real-time streaming"})
	def.DIDs = append(def.DIDs, seedDID{Path: "schema:openapi_v3", DisplayName: "OpenAPI 3.0", Description: "API specification format"})
	def.DIDs = append(def.DIDs, seedDID{Path: "schema:asyncapi", DisplayName: "AsyncAPI 2.0", Description: "Event-driven API spec"})
	def.DIDs = append(def.DIDs, seedDID{Path: "endpoint:grpc_service", DisplayName: "gRPC Service", Description: "Binary RPC protocol"})
	recsendpoint := seedCollection{Collection: "ai.gftd.apps.api.endpoint"}
	recsendpoint.Items = append(recsendpoint.Items, seedRecord{ID: "rest_users", Data: map[string]any{"id": "rest_users", "name": "REST /users", "description": "User management API", "status": "active"}})
	recsendpoint.Items = append(recsendpoint.Items, seedRecord{ID: "graphql", Data: map[string]any{"id": "graphql", "name": "GraphQL /graphql", "description": "Query API", "status": "active"}})
	recsendpoint.Items = append(recsendpoint.Items, seedRecord{ID: "websocket", Data: map[string]any{"id": "websocket", "name": "WebSocket /ws", "description": "Real-time streaming", "status": "active"}})
	recsendpoint.Items = append(recsendpoint.Items, seedRecord{ID: "grpc_service", Data: map[string]any{"id": "grpc_service", "name": "gRPC Service", "description": "Binary RPC protocol", "status": "active"}})
	def.Records = append(def.Records, recsendpoint)
	recsschema := seedCollection{Collection: "ai.gftd.apps.api.schema"}
	recsschema.Items = append(recsschema.Items, seedRecord{ID: "openapi_v3", Data: map[string]any{"id": "openapi_v3", "name": "OpenAPI 3.0", "description": "API specification format", "status": "active"}})
	recsschema.Items = append(recsschema.Items, seedRecord{ID: "asyncapi", Data: map[string]any{"id": "asyncapi", "name": "AsyncAPI 2.0", "description": "Event-driven API spec", "status": "active"}})
	def.Records = append(def.Records, recsschema)
	return def
}

func ApparelGapSeeds() seedDef {
	def := seedDef{Domain: "apparel", Nanoid: "ap4rl01", DID: "did:web:apparel.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "sku:tshirt_m", DisplayName: "T-Shirt M", Description: "Cotton basic tee"})
	def.DIDs = append(def.DIDs, seedDID{Path: "sku:denim_32", DisplayName: "Denim Jeans 32", Description: "Straight fit denim"})
	def.DIDs = append(def.DIDs, seedDID{Path: "sku:sneaker_26", DisplayName: "Sneaker 26cm", Description: "Running shoe"})
	def.DIDs = append(def.DIDs, seedDID{Path: "sku:hoodie_l", DisplayName: "Hoodie L", Description: "Pullover hoodie"})
	def.DIDs = append(def.DIDs, seedDID{Path: "sku:dress_s", DisplayName: "Dress S", Description: "Summer dress"})
	def.DIDs = append(def.DIDs, seedDID{Path: "sku:jacket_m", DisplayName: "Jacket M", Description: "Down jacket"})
	recssku := seedCollection{Collection: "ai.gftd.apps.apparel.sku"}
	recssku.Items = append(recssku.Items, seedRecord{ID: "tshirt_m", Data: map[string]any{"id": "tshirt_m", "name": "T-Shirt M", "description": "Cotton basic tee", "status": "active"}})
	recssku.Items = append(recssku.Items, seedRecord{ID: "denim_32", Data: map[string]any{"id": "denim_32", "name": "Denim Jeans 32", "description": "Straight fit denim", "status": "active"}})
	recssku.Items = append(recssku.Items, seedRecord{ID: "sneaker_26", Data: map[string]any{"id": "sneaker_26", "name": "Sneaker 26cm", "description": "Running shoe", "status": "active"}})
	recssku.Items = append(recssku.Items, seedRecord{ID: "hoodie_l", Data: map[string]any{"id": "hoodie_l", "name": "Hoodie L", "description": "Pullover hoodie", "status": "active"}})
	recssku.Items = append(recssku.Items, seedRecord{ID: "dress_s", Data: map[string]any{"id": "dress_s", "name": "Dress S", "description": "Summer dress", "status": "active"}})
	recssku.Items = append(recssku.Items, seedRecord{ID: "jacket_m", Data: map[string]any{"id": "jacket_m", "name": "Jacket M", "description": "Down jacket", "status": "active"}})
	def.Records = append(def.Records, recssku)
	return def
}

func ArtGapSeeds() seedDef {
	def := seedDef{Domain: "art", Nanoid: "ar7nk3vp", DID: "did:web:art.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "artwork:mona_lisa", DisplayName: "Mona Lisa", Description: "Leonardo da Vinci, 1503"})
	def.DIDs = append(def.DIDs, seedDID{Path: "artwork:starry_night", DisplayName: "The Starry Night", Description: "Vincent van Gogh, 1889"})
	def.DIDs = append(def.DIDs, seedDID{Path: "artwork:great_wave", DisplayName: "神奈川沖浪裏", Description: "Katsushika Hokusai, 1831"})
	def.DIDs = append(def.DIDs, seedDID{Path: "artwork:guernica", DisplayName: "Guernica", Description: "Pablo Picasso, 1937"})
	def.DIDs = append(def.DIDs, seedDID{Path: "artwork:girl_pearl", DisplayName: "Girl with a Pearl Earring", Description: "Johannes Vermeer, 1665"})
	def.DIDs = append(def.DIDs, seedDID{Path: "artwork:persistence", DisplayName: "The Persistence of Memory", Description: "Salvador Dalí, 1931"})
	recsartwork := seedCollection{Collection: "ai.gftd.apps.art.artwork"}
	recsartwork.Items = append(recsartwork.Items, seedRecord{ID: "mona_lisa", Data: map[string]any{"id": "mona_lisa", "name": "Mona Lisa", "description": "Leonardo da Vinci, 1503", "status": "active"}})
	recsartwork.Items = append(recsartwork.Items, seedRecord{ID: "starry_night", Data: map[string]any{"id": "starry_night", "name": "The Starry Night", "description": "Vincent van Gogh, 1889", "status": "active"}})
	recsartwork.Items = append(recsartwork.Items, seedRecord{ID: "great_wave", Data: map[string]any{"id": "great_wave", "name": "神奈川沖浪裏", "description": "Katsushika Hokusai, 1831", "status": "active"}})
	recsartwork.Items = append(recsartwork.Items, seedRecord{ID: "guernica", Data: map[string]any{"id": "guernica", "name": "Guernica", "description": "Pablo Picasso, 1937", "status": "active"}})
	recsartwork.Items = append(recsartwork.Items, seedRecord{ID: "girl_pearl", Data: map[string]any{"id": "girl_pearl", "name": "Girl with a Pearl Earring", "description": "Johannes Vermeer, 1665", "status": "active"}})
	recsartwork.Items = append(recsartwork.Items, seedRecord{ID: "persistence", Data: map[string]any{"id": "persistence", "name": "The Persistence of Memory", "description": "Salvador Dalí, 1931", "status": "active"}})
	def.Records = append(def.Records, recsartwork)
	return def
}

func BankGapSeeds() seedDef {
	def := seedDef{Domain: "bank", Nanoid: "bn3kf8yz", DID: "did:web:bank.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "bank:mufg", DisplayName: "三菱UFJ銀行", Description: "MUFG Bank, Japan"})
	def.DIDs = append(def.DIDs, seedDID{Path: "bank:smbc", DisplayName: "三井住友銀行", Description: "SMBC, Japan"})
	def.DIDs = append(def.DIDs, seedDID{Path: "bank:mizuho", DisplayName: "みずほ銀行", Description: "Mizuho Bank, Japan"})
	def.DIDs = append(def.DIDs, seedDID{Path: "bank:jpmorgan", DisplayName: "JPMorgan Chase", Description: "USA"})
	def.DIDs = append(def.DIDs, seedDID{Path: "bank:hsbc", DisplayName: "HSBC", Description: "United Kingdom"})
	def.DIDs = append(def.DIDs, seedDID{Path: "bank:icbc", DisplayName: "中国工商銀行", Description: "ICBC, China"})
	def.DIDs = append(def.DIDs, seedDID{Path: "bank:bnp", DisplayName: "BNP Paribas", Description: "France"})
	def.DIDs = append(def.DIDs, seedDID{Path: "account:savings_std", DisplayName: "普通預金", Description: "Standard savings account"})
	recsbank := seedCollection{Collection: "ai.gftd.apps.bank.bank"}
	recsbank.Items = append(recsbank.Items, seedRecord{ID: "mufg", Data: map[string]any{"id": "mufg", "name": "三菱UFJ銀行", "description": "MUFG Bank, Japan", "status": "active"}})
	recsbank.Items = append(recsbank.Items, seedRecord{ID: "smbc", Data: map[string]any{"id": "smbc", "name": "三井住友銀行", "description": "SMBC, Japan", "status": "active"}})
	recsbank.Items = append(recsbank.Items, seedRecord{ID: "mizuho", Data: map[string]any{"id": "mizuho", "name": "みずほ銀行", "description": "Mizuho Bank, Japan", "status": "active"}})
	recsbank.Items = append(recsbank.Items, seedRecord{ID: "jpmorgan", Data: map[string]any{"id": "jpmorgan", "name": "JPMorgan Chase", "description": "USA", "status": "active"}})
	recsbank.Items = append(recsbank.Items, seedRecord{ID: "hsbc", Data: map[string]any{"id": "hsbc", "name": "HSBC", "description": "United Kingdom", "status": "active"}})
	recsbank.Items = append(recsbank.Items, seedRecord{ID: "icbc", Data: map[string]any{"id": "icbc", "name": "中国工商銀行", "description": "ICBC, China", "status": "active"}})
	recsbank.Items = append(recsbank.Items, seedRecord{ID: "bnp", Data: map[string]any{"id": "bnp", "name": "BNP Paribas", "description": "France", "status": "active"}})
	def.Records = append(def.Records, recsbank)
	recsaccount := seedCollection{Collection: "ai.gftd.apps.bank.account"}
	recsaccount.Items = append(recsaccount.Items, seedRecord{ID: "savings_std", Data: map[string]any{"id": "savings_std", "name": "普通預金", "description": "Standard savings account", "status": "active"}})
	def.Records = append(def.Records, recsaccount)
	return def
}

func BankruptcyGapSeeds() seedDef {
	def := seedDef{Domain: "bankruptcy", Nanoid: "b4nkrpt0", DID: "did:web:bankruptcy.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "proceeding:ch7_liq", DisplayName: "Chapter 7 Liquidation", Description: "US bankruptcy liquidation"})
	def.DIDs = append(def.DIDs, seedDID{Path: "proceeding:ch11_reorg", DisplayName: "Chapter 11 Reorganization", Description: "US corporate reorganization"})
	def.DIDs = append(def.DIDs, seedDID{Path: "proceeding:minji_saisei", DisplayName: "民事再生", Description: "Japan civil rehabilitation"})
	def.DIDs = append(def.DIDs, seedDID{Path: "proceeding:kaisha_kosei", DisplayName: "会社更生", Description: "Japan corporate reorganization"})
	def.DIDs = append(def.DIDs, seedDID{Path: "proceeding:hasan", DisplayName: "破産", Description: "Japan bankruptcy"})
	def.DIDs = append(def.DIDs, seedDID{Path: "proceeding:insolvency_uk", DisplayName: "UK Insolvency", Description: "UK insolvency proceeding"})
	recsproceeding := seedCollection{Collection: "ai.gftd.apps.bankruptcy.proceeding"}
	recsproceeding.Items = append(recsproceeding.Items, seedRecord{ID: "ch7_liq", Data: map[string]any{"id": "ch7_liq", "name": "Chapter 7 Liquidation", "description": "US bankruptcy liquidation", "status": "active"}})
	recsproceeding.Items = append(recsproceeding.Items, seedRecord{ID: "ch11_reorg", Data: map[string]any{"id": "ch11_reorg", "name": "Chapter 11 Reorganization", "description": "US corporate reorganization", "status": "active"}})
	recsproceeding.Items = append(recsproceeding.Items, seedRecord{ID: "minji_saisei", Data: map[string]any{"id": "minji_saisei", "name": "民事再生", "description": "Japan civil rehabilitation", "status": "active"}})
	recsproceeding.Items = append(recsproceeding.Items, seedRecord{ID: "kaisha_kosei", Data: map[string]any{"id": "kaisha_kosei", "name": "会社更生", "description": "Japan corporate reorganization", "status": "active"}})
	recsproceeding.Items = append(recsproceeding.Items, seedRecord{ID: "hasan", Data: map[string]any{"id": "hasan", "name": "破産", "description": "Japan bankruptcy", "status": "active"}})
	recsproceeding.Items = append(recsproceeding.Items, seedRecord{ID: "insolvency_uk", Data: map[string]any{"id": "insolvency_uk", "name": "UK Insolvency", "description": "UK insolvency proceeding", "status": "active"}})
	def.Records = append(def.Records, recsproceeding)
	return def
}

func BimGapSeeds() seedDef {
	def := seedDef{Domain: "bim", Nanoid: "bm4ld01", DID: "did:web:bim.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "pipe:hvac_main_01", DisplayName: "空調主配管01", Description: "Main HVAC piping"})
	def.DIDs = append(def.DIDs, seedDID{Path: "wire:power_floor3", DisplayName: "電力幹線3F", Description: "3F power trunk cable"})
	def.DIDs = append(def.DIDs, seedDID{Path: "structure:beam_b1", DisplayName: "梁B1", Description: "Main structural beam"})
	def.DIDs = append(def.DIDs, seedDID{Path: "hvac:ahu_01", DisplayName: "空調機AHU-01", Description: "Air handling unit"})
	def.DIDs = append(def.DIDs, seedDID{Path: "equipment:elv_01", DisplayName: "エレベータ01", Description: "Passenger elevator"})
	def.DIDs = append(def.DIDs, seedDID{Path: "fixture:led_panel_01", DisplayName: "LEDパネル照明01", Description: "Ceiling LED panel"})
	def.DIDs = append(def.DIDs, seedDID{Path: "cable:lan_floor5", DisplayName: "LAN配線5F", Description: "5F LAN cabling"})
	def.DIDs = append(def.DIDs, seedDID{Path: "fire_device:sprinkler_01", DisplayName: "スプリンクラー01", Description: "Fire sprinkler head"})
	def.DIDs = append(def.DIDs, seedDID{Path: "inspection:annual_2025", DisplayName: "2025年度定期点検", Description: "Annual building inspection"})
	recspipe := seedCollection{Collection: "ai.gftd.apps.bim.pipe"}
	recspipe.Items = append(recspipe.Items, seedRecord{ID: "hvac_main_01", Data: map[string]any{"id": "hvac_main_01", "name": "空調主配管01", "description": "Main HVAC piping", "status": "active"}})
	def.Records = append(def.Records, recspipe)
	recswire := seedCollection{Collection: "ai.gftd.apps.bim.wire"}
	recswire.Items = append(recswire.Items, seedRecord{ID: "power_floor3", Data: map[string]any{"id": "power_floor3", "name": "電力幹線3F", "description": "3F power trunk cable", "status": "active"}})
	def.Records = append(def.Records, recswire)
	recsstructure := seedCollection{Collection: "ai.gftd.apps.bim.structure"}
	recsstructure.Items = append(recsstructure.Items, seedRecord{ID: "beam_b1", Data: map[string]any{"id": "beam_b1", "name": "梁B1", "description": "Main structural beam", "status": "active"}})
	def.Records = append(def.Records, recsstructure)
	recshvac := seedCollection{Collection: "ai.gftd.apps.bim.hvac"}
	recshvac.Items = append(recshvac.Items, seedRecord{ID: "ahu_01", Data: map[string]any{"id": "ahu_01", "name": "空調機AHU-01", "description": "Air handling unit", "status": "active"}})
	def.Records = append(def.Records, recshvac)
	recsequipment := seedCollection{Collection: "ai.gftd.apps.bim.equipment"}
	recsequipment.Items = append(recsequipment.Items, seedRecord{ID: "elv_01", Data: map[string]any{"id": "elv_01", "name": "エレベータ01", "description": "Passenger elevator", "status": "active"}})
	def.Records = append(def.Records, recsequipment)
	recsfixture := seedCollection{Collection: "ai.gftd.apps.bim.fixture"}
	recsfixture.Items = append(recsfixture.Items, seedRecord{ID: "led_panel_01", Data: map[string]any{"id": "led_panel_01", "name": "LEDパネル照明01", "description": "Ceiling LED panel", "status": "active"}})
	def.Records = append(def.Records, recsfixture)
	recscable := seedCollection{Collection: "ai.gftd.apps.bim.cable"}
	recscable.Items = append(recscable.Items, seedRecord{ID: "lan_floor5", Data: map[string]any{"id": "lan_floor5", "name": "LAN配線5F", "description": "5F LAN cabling", "status": "active"}})
	def.Records = append(def.Records, recscable)
	recsfire_device := seedCollection{Collection: "ai.gftd.apps.bim.fire_device"}
	recsfire_device.Items = append(recsfire_device.Items, seedRecord{ID: "sprinkler_01", Data: map[string]any{"id": "sprinkler_01", "name": "スプリンクラー01", "description": "Fire sprinkler head", "status": "active"}})
	def.Records = append(def.Records, recsfire_device)
	recsinspection := seedCollection{Collection: "ai.gftd.apps.bim.inspection"}
	recsinspection.Items = append(recsinspection.Items, seedRecord{ID: "annual_2025", Data: map[string]any{"id": "annual_2025", "name": "2025年度定期点検", "description": "Annual building inspection", "status": "active"}})
	def.Records = append(def.Records, recsinspection)
	return def
}

func BouekiGapSeeds() seedDef {
	def := seedDef{Domain: "boueki", Nanoid: "boue537e", DID: "did:web:boueki.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "instrument:lc_import", DisplayName: "輸入信用状", Description: "Import letter of credit"})
	def.DIDs = append(def.DIDs, seedDID{Path: "instrument:lc_export", DisplayName: "輸出信用状", Description: "Export letter of credit"})
	def.DIDs = append(def.DIDs, seedDID{Path: "instrument:bill_lading", DisplayName: "船荷証券", Description: "Bill of lading"})
	def.DIDs = append(def.DIDs, seedDID{Path: "instrument:insurance_cargo", DisplayName: "貨物保険", Description: "Cargo insurance"})
	def.DIDs = append(def.DIDs, seedDID{Path: "instrument:standby_lc", DisplayName: "スタンバイLC", Description: "Standby letter of credit"})
	def.DIDs = append(def.DIDs, seedDID{Path: "instrument:factoring", DisplayName: "ファクタリング", Description: "Trade factoring"})
	recsinstrument := seedCollection{Collection: "ai.gftd.apps.boueki.instrument"}
	recsinstrument.Items = append(recsinstrument.Items, seedRecord{ID: "lc_import", Data: map[string]any{"id": "lc_import", "name": "輸入信用状", "description": "Import letter of credit", "status": "active"}})
	recsinstrument.Items = append(recsinstrument.Items, seedRecord{ID: "lc_export", Data: map[string]any{"id": "lc_export", "name": "輸出信用状", "description": "Export letter of credit", "status": "active"}})
	recsinstrument.Items = append(recsinstrument.Items, seedRecord{ID: "bill_lading", Data: map[string]any{"id": "bill_lading", "name": "船荷証券", "description": "Bill of lading", "status": "active"}})
	recsinstrument.Items = append(recsinstrument.Items, seedRecord{ID: "insurance_cargo", Data: map[string]any{"id": "insurance_cargo", "name": "貨物保険", "description": "Cargo insurance", "status": "active"}})
	recsinstrument.Items = append(recsinstrument.Items, seedRecord{ID: "standby_lc", Data: map[string]any{"id": "standby_lc", "name": "スタンバイLC", "description": "Standby letter of credit", "status": "active"}})
	recsinstrument.Items = append(recsinstrument.Items, seedRecord{ID: "factoring", Data: map[string]any{"id": "factoring", "name": "ファクタリング", "description": "Trade factoring", "status": "active"}})
	def.Records = append(def.Records, recsinstrument)
	return def
}

func BusGapSeeds() seedDef {
	def := seedDef{Domain: "bus", Nanoid: "bs4rt01", DID: "did:web:bus.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "stop:shinjuku_west", DisplayName: "新宿駅西口", Description: "Shinjuku Station West Exit"})
	def.DIDs = append(def.DIDs, seedDID{Path: "stop:shibuya_markc", DisplayName: "渋谷マークシティ", Description: "Shibuya Mark City"})
	def.DIDs = append(def.DIDs, seedDID{Path: "stop:tokyo_yaesu", DisplayName: "東京駅八重洲口", Description: "Tokyo Station Yaesu"})
	def.DIDs = append(def.DIDs, seedDID{Path: "vehicle:hino_selega", DisplayName: "日野セレガ", Description: "Highway express bus"})
	def.DIDs = append(def.DIDs, seedDID{Path: "vehicle:isuzu_erga", DisplayName: "いすゞエルガ", Description: "City route bus"})
	def.DIDs = append(def.DIDs, seedDID{Path: "stop:osaka_umeda", DisplayName: "大阪梅田", Description: "Osaka Umeda terminal"})
	recsstop := seedCollection{Collection: "ai.gftd.apps.bus.stop"}
	recsstop.Items = append(recsstop.Items, seedRecord{ID: "shinjuku_west", Data: map[string]any{"id": "shinjuku_west", "name": "新宿駅西口", "description": "Shinjuku Station West Exit", "status": "active"}})
	recsstop.Items = append(recsstop.Items, seedRecord{ID: "shibuya_markc", Data: map[string]any{"id": "shibuya_markc", "name": "渋谷マークシティ", "description": "Shibuya Mark City", "status": "active"}})
	recsstop.Items = append(recsstop.Items, seedRecord{ID: "tokyo_yaesu", Data: map[string]any{"id": "tokyo_yaesu", "name": "東京駅八重洲口", "description": "Tokyo Station Yaesu", "status": "active"}})
	recsstop.Items = append(recsstop.Items, seedRecord{ID: "osaka_umeda", Data: map[string]any{"id": "osaka_umeda", "name": "大阪梅田", "description": "Osaka Umeda terminal", "status": "active"}})
	def.Records = append(def.Records, recsstop)
	recsvehicle := seedCollection{Collection: "ai.gftd.apps.bus.vehicle"}
	recsvehicle.Items = append(recsvehicle.Items, seedRecord{ID: "hino_selega", Data: map[string]any{"id": "hino_selega", "name": "日野セレガ", "description": "Highway express bus", "status": "active"}})
	recsvehicle.Items = append(recsvehicle.Items, seedRecord{ID: "isuzu_erga", Data: map[string]any{"id": "isuzu_erga", "name": "いすゞエルガ", "description": "City route bus", "status": "active"}})
	def.Records = append(def.Records, recsvehicle)
	return def
}

func CarbonGapSeeds() seedDef {
	def := seedDef{Domain: "carbon", Nanoid: "cb4rn01", DID: "did:web:carbon.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "credit:vcs_001", DisplayName: "VCS Forest Carbon", Description: "Verified Carbon Standard"})
	def.DIDs = append(def.DIDs, seedDID{Path: "credit:gold_std", DisplayName: "Gold Standard CER", Description: "Gold Standard certified"})
	def.DIDs = append(def.DIDs, seedDID{Path: "credit:cdm_solar", DisplayName: "CDM Solar Project", Description: "Clean Development Mechanism"})
	def.DIDs = append(def.DIDs, seedDID{Path: "credit:redd_amazon", DisplayName: "REDD+ Amazon", Description: "Reduced deforestation"})
	def.DIDs = append(def.DIDs, seedDID{Path: "credit:jcm_asia", DisplayName: "JCM Asia", Description: "Japan Joint Crediting Mechanism"})
	def.DIDs = append(def.DIDs, seedDID{Path: "credit:eu_ets", DisplayName: "EU ETS Allowance", Description: "EU Emissions Trading"})
	recscredit := seedCollection{Collection: "ai.gftd.apps.carbon.credit"}
	recscredit.Items = append(recscredit.Items, seedRecord{ID: "vcs_001", Data: map[string]any{"id": "vcs_001", "name": "VCS Forest Carbon", "description": "Verified Carbon Standard", "status": "active"}})
	recscredit.Items = append(recscredit.Items, seedRecord{ID: "gold_std", Data: map[string]any{"id": "gold_std", "name": "Gold Standard CER", "description": "Gold Standard certified", "status": "active"}})
	recscredit.Items = append(recscredit.Items, seedRecord{ID: "cdm_solar", Data: map[string]any{"id": "cdm_solar", "name": "CDM Solar Project", "description": "Clean Development Mechanism", "status": "active"}})
	recscredit.Items = append(recscredit.Items, seedRecord{ID: "redd_amazon", Data: map[string]any{"id": "redd_amazon", "name": "REDD+ Amazon", "description": "Reduced deforestation", "status": "active"}})
	recscredit.Items = append(recscredit.Items, seedRecord{ID: "jcm_asia", Data: map[string]any{"id": "jcm_asia", "name": "JCM Asia", "description": "Japan Joint Crediting Mechanism", "status": "active"}})
	recscredit.Items = append(recscredit.Items, seedRecord{ID: "eu_ets", Data: map[string]any{"id": "eu_ets", "name": "EU ETS Allowance", "description": "EU Emissions Trading", "status": "active"}})
	def.Records = append(def.Records, recscredit)
	return def
}

func CasGapSeeds() seedDef {
	def := seedDef{Domain: "cas", Nanoid: "cs4r7n2k", DID: "did:web:cas.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "substance:water", DisplayName: "Water (H2O)", Description: "CAS 7732-18-5"})
	def.DIDs = append(def.DIDs, seedDID{Path: "substance:ethanol", DisplayName: "Ethanol", Description: "CAS 64-17-5"})
	def.DIDs = append(def.DIDs, seedDID{Path: "substance:nacl", DisplayName: "Sodium Chloride", Description: "CAS 7647-14-5"})
	def.DIDs = append(def.DIDs, seedDID{Path: "substance:glucose", DisplayName: "Glucose", Description: "CAS 50-99-7"})
	def.DIDs = append(def.DIDs, seedDID{Path: "substance:caffeine", DisplayName: "Caffeine", Description: "CAS 58-08-2"})
	def.DIDs = append(def.DIDs, seedDID{Path: "substance:aspirin", DisplayName: "Acetylsalicylic Acid", Description: "CAS 50-78-2"})
	recssubstance := seedCollection{Collection: "ai.gftd.apps.cas.substance"}
	recssubstance.Items = append(recssubstance.Items, seedRecord{ID: "water", Data: map[string]any{"id": "water", "name": "Water (H2O)", "description": "CAS 7732-18-5", "status": "active"}})
	recssubstance.Items = append(recssubstance.Items, seedRecord{ID: "ethanol", Data: map[string]any{"id": "ethanol", "name": "Ethanol", "description": "CAS 64-17-5", "status": "active"}})
	recssubstance.Items = append(recssubstance.Items, seedRecord{ID: "nacl", Data: map[string]any{"id": "nacl", "name": "Sodium Chloride", "description": "CAS 7647-14-5", "status": "active"}})
	recssubstance.Items = append(recssubstance.Items, seedRecord{ID: "glucose", Data: map[string]any{"id": "glucose", "name": "Glucose", "description": "CAS 50-99-7", "status": "active"}})
	recssubstance.Items = append(recssubstance.Items, seedRecord{ID: "caffeine", Data: map[string]any{"id": "caffeine", "name": "Caffeine", "description": "CAS 58-08-2", "status": "active"}})
	recssubstance.Items = append(recssubstance.Items, seedRecord{ID: "aspirin", Data: map[string]any{"id": "aspirin", "name": "Acetylsalicylic Acid", "description": "CAS 50-78-2", "status": "active"}})
	def.Records = append(def.Records, recssubstance)
	return def
}

func CellerGapSeeds() seedDef {
	def := seedDef{Domain: "celler", Nanoid: "oilt0wta", DID: "did:web:celler.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "subscription:basic_jp", DisplayName: "Basic JP", Description: "Japan domestic calling plan"})
	def.DIDs = append(def.DIDs, seedDID{Path: "subscription:global_roam", DisplayName: "Global Roaming", Description: "International roaming plan"})
	def.DIDs = append(def.DIDs, seedDID{Path: "subscription:esim_data", DisplayName: "eSIM Data Only", Description: "Data-only eSIM plan"})
	def.DIDs = append(def.DIDs, seedDID{Path: "subscription:sip_trunk", DisplayName: "SIP Trunk", Description: "Enterprise SIP trunking"})
	def.DIDs = append(def.DIDs, seedDID{Path: "subscription:starlink", DisplayName: "Starlink Voice", Description: "Satellite voice plan"})
	recssubscription := seedCollection{Collection: "ai.gftd.apps.celler.subscription"}
	recssubscription.Items = append(recssubscription.Items, seedRecord{ID: "basic_jp", Data: map[string]any{"id": "basic_jp", "name": "Basic JP", "description": "Japan domestic calling plan", "status": "active"}})
	recssubscription.Items = append(recssubscription.Items, seedRecord{ID: "global_roam", Data: map[string]any{"id": "global_roam", "name": "Global Roaming", "description": "International roaming plan", "status": "active"}})
	recssubscription.Items = append(recssubscription.Items, seedRecord{ID: "esim_data", Data: map[string]any{"id": "esim_data", "name": "eSIM Data Only", "description": "Data-only eSIM plan", "status": "active"}})
	recssubscription.Items = append(recssubscription.Items, seedRecord{ID: "sip_trunk", Data: map[string]any{"id": "sip_trunk", "name": "SIP Trunk", "description": "Enterprise SIP trunking", "status": "active"}})
	recssubscription.Items = append(recssubscription.Items, seedRecord{ID: "starlink", Data: map[string]any{"id": "starlink", "name": "Starlink Voice", "description": "Satellite voice plan", "status": "active"}})
	def.Records = append(def.Records, recssubscription)
	return def
}

func CharacterGapSeeds() seedDef {
	def := seedDef{Domain: "character", Nanoid: "ch4r4k01", DID: "did:web:character.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "character:goku", DisplayName: "孫悟空", Description: "Dragon Ball protagonist"})
	def.DIDs = append(def.DIDs, seedDID{Path: "character:luffy", DisplayName: "モンキー・D・ルフィ", Description: "One Piece protagonist"})
	def.DIDs = append(def.DIDs, seedDID{Path: "character:naruto", DisplayName: "うずまきナルト", Description: "Naruto protagonist"})
	def.DIDs = append(def.DIDs, seedDID{Path: "character:pikachu", DisplayName: "ピカチュウ", Description: "Pokémon mascot"})
	def.DIDs = append(def.DIDs, seedDID{Path: "character:mario", DisplayName: "マリオ", Description: "Nintendo mascot"})
	def.DIDs = append(def.DIDs, seedDID{Path: "character:saber", DisplayName: "セイバー", Description: "Fate/stay night"})
	def.DIDs = append(def.DIDs, seedDID{Path: "casting:goku_va", DisplayName: "野沢雅子 → 孫悟空", Description: "Voice actor casting"})
	def.DIDs = append(def.DIDs, seedDID{Path: "relation:goku_vegeta", DisplayName: "悟空 ↔ ベジータ", Description: "Rival relationship"})
	def.DIDs = append(def.DIDs, seedDID{Path: "world:dragon_ball", DisplayName: "ドラゴンボール世界", Description: "Dragon Ball universe"})
	def.DIDs = append(def.DIDs, seedDID{Path: "item:dragon_ball_4star", DisplayName: "四星球", Description: "Four-Star Dragon Ball"})
	def.DIDs = append(def.DIDs, seedDID{Path: "location:kamehouse", DisplayName: "カメハウス", Description: "Kame House"})
	recscharacter := seedCollection{Collection: "ai.gftd.apps.character.character"}
	recscharacter.Items = append(recscharacter.Items, seedRecord{ID: "goku", Data: map[string]any{"id": "goku", "name": "孫悟空", "description": "Dragon Ball protagonist", "status": "active"}})
	recscharacter.Items = append(recscharacter.Items, seedRecord{ID: "luffy", Data: map[string]any{"id": "luffy", "name": "モンキー・D・ルフィ", "description": "One Piece protagonist", "status": "active"}})
	recscharacter.Items = append(recscharacter.Items, seedRecord{ID: "naruto", Data: map[string]any{"id": "naruto", "name": "うずまきナルト", "description": "Naruto protagonist", "status": "active"}})
	recscharacter.Items = append(recscharacter.Items, seedRecord{ID: "pikachu", Data: map[string]any{"id": "pikachu", "name": "ピカチュウ", "description": "Pokémon mascot", "status": "active"}})
	recscharacter.Items = append(recscharacter.Items, seedRecord{ID: "mario", Data: map[string]any{"id": "mario", "name": "マリオ", "description": "Nintendo mascot", "status": "active"}})
	recscharacter.Items = append(recscharacter.Items, seedRecord{ID: "saber", Data: map[string]any{"id": "saber", "name": "セイバー", "description": "Fate/stay night", "status": "active"}})
	def.Records = append(def.Records, recscharacter)
	recscasting := seedCollection{Collection: "ai.gftd.apps.character.casting"}
	recscasting.Items = append(recscasting.Items, seedRecord{ID: "goku_va", Data: map[string]any{"id": "goku_va", "name": "野沢雅子 → 孫悟空", "description": "Voice actor casting", "status": "active"}})
	def.Records = append(def.Records, recscasting)
	recsrelation := seedCollection{Collection: "ai.gftd.apps.character.relation"}
	recsrelation.Items = append(recsrelation.Items, seedRecord{ID: "goku_vegeta", Data: map[string]any{"id": "goku_vegeta", "name": "悟空 ↔ ベジータ", "description": "Rival relationship", "status": "active"}})
	def.Records = append(def.Records, recsrelation)
	recsworld := seedCollection{Collection: "ai.gftd.apps.character.world"}
	recsworld.Items = append(recsworld.Items, seedRecord{ID: "dragon_ball", Data: map[string]any{"id": "dragon_ball", "name": "ドラゴンボール世界", "description": "Dragon Ball universe", "status": "active"}})
	def.Records = append(def.Records, recsworld)
	recsitem := seedCollection{Collection: "ai.gftd.apps.character.item"}
	recsitem.Items = append(recsitem.Items, seedRecord{ID: "dragon_ball_4star", Data: map[string]any{"id": "dragon_ball_4star", "name": "四星球", "description": "Four-Star Dragon Ball", "status": "active"}})
	def.Records = append(def.Records, recsitem)
	recslocation := seedCollection{Collection: "ai.gftd.apps.character.location"}
	recslocation.Items = append(recslocation.Items, seedRecord{ID: "kamehouse", Data: map[string]any{"id": "kamehouse", "name": "カメハウス", "description": "Kame House", "status": "active"}})
	def.Records = append(def.Records, recslocation)
	return def
}

func ChizaiGapSeeds() seedDef {
	def := seedDef{Domain: "chizai", Nanoid: "chz4ig01", DID: "did:web:chizai.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "trademark:apple_logo", DisplayName: "Apple Logo", Description: "US trademark"})
	def.DIDs = append(def.DIDs, seedDID{Path: "copyright:mickey_mouse", DisplayName: "Mickey Mouse", Description: "Disney copyright"})
	def.DIDs = append(def.DIDs, seedDID{Path: "design:iphone_shape", DisplayName: "iPhone Industrial Design", Description: "Apple design patent"})
	def.DIDs = append(def.DIDs, seedDID{Path: "utility_model:jp_um001", DisplayName: "実用新案JP001", Description: "Japan utility model"})
	def.DIDs = append(def.DIDs, seedDID{Path: "gi:champagne", DisplayName: "Champagne", Description: "French geographical indication"})
	def.DIDs = append(def.DIDs, seedDID{Path: "secret:coca_cola", DisplayName: "Coca-Cola Recipe", Description: "Trade secret"})
	def.DIDs = append(def.DIDs, seedDID{Path: "variety:shine_muscat", DisplayName: "シャインマスカット", Description: "Plant variety right"})
	recstrademark := seedCollection{Collection: "ai.gftd.apps.chizai.trademark"}
	recstrademark.Items = append(recstrademark.Items, seedRecord{ID: "apple_logo", Data: map[string]any{"id": "apple_logo", "name": "Apple Logo", "description": "US trademark", "status": "active"}})
	def.Records = append(def.Records, recstrademark)
	recscopyright := seedCollection{Collection: "ai.gftd.apps.chizai.copyright"}
	recscopyright.Items = append(recscopyright.Items, seedRecord{ID: "mickey_mouse", Data: map[string]any{"id": "mickey_mouse", "name": "Mickey Mouse", "description": "Disney copyright", "status": "active"}})
	def.Records = append(def.Records, recscopyright)
	recsdesign := seedCollection{Collection: "ai.gftd.apps.chizai.design"}
	recsdesign.Items = append(recsdesign.Items, seedRecord{ID: "iphone_shape", Data: map[string]any{"id": "iphone_shape", "name": "iPhone Industrial Design", "description": "Apple design patent", "status": "active"}})
	def.Records = append(def.Records, recsdesign)
	recsutility_model := seedCollection{Collection: "ai.gftd.apps.chizai.utility_model"}
	recsutility_model.Items = append(recsutility_model.Items, seedRecord{ID: "jp_um001", Data: map[string]any{"id": "jp_um001", "name": "実用新案JP001", "description": "Japan utility model", "status": "active"}})
	def.Records = append(def.Records, recsutility_model)
	recsgi := seedCollection{Collection: "ai.gftd.apps.chizai.gi"}
	recsgi.Items = append(recsgi.Items, seedRecord{ID: "champagne", Data: map[string]any{"id": "champagne", "name": "Champagne", "description": "French geographical indication", "status": "active"}})
	def.Records = append(def.Records, recsgi)
	recssecret := seedCollection{Collection: "ai.gftd.apps.chizai.secret"}
	recssecret.Items = append(recssecret.Items, seedRecord{ID: "coca_cola", Data: map[string]any{"id": "coca_cola", "name": "Coca-Cola Recipe", "description": "Trade secret", "status": "active"}})
	def.Records = append(def.Records, recssecret)
	recsvariety := seedCollection{Collection: "ai.gftd.apps.chizai.variety"}
	recsvariety.Items = append(recsvariety.Items, seedRecord{ID: "shine_muscat", Data: map[string]any{"id": "shine_muscat", "name": "シャインマスカット", "description": "Plant variety right", "status": "active"}})
	def.Records = append(def.Records, recsvariety)
	return def
}

func ChotatsuGapSeeds() seedDef {
	def := seedDef{Domain: "chotatsu", Nanoid: "chotbf32", DID: "did:web:chotatsu.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "procurement:mlit_road", DisplayName: "国交省道路整備", Description: "MLIT road construction"})
	def.DIDs = append(def.DIDs, seedDID{Path: "procurement:mod_defense", DisplayName: "防衛省装備調達", Description: "MOD equipment procurement"})
	def.DIDs = append(def.DIDs, seedDID{Path: "procurement:mext_it", DisplayName: "文科省IT調達", Description: "MEXT IT procurement"})
	def.DIDs = append(def.DIDs, seedDID{Path: "procurement:mhlw_medical", DisplayName: "厚労省医療機器", Description: "MHLW medical equipment"})
	def.DIDs = append(def.DIDs, seedDID{Path: "procurement:tokyo_infra", DisplayName: "東京都インフラ整備", Description: "Tokyo Metropolitan infrastructure"})
	recsprocurement := seedCollection{Collection: "ai.gftd.apps.chotatsu.procurement"}
	recsprocurement.Items = append(recsprocurement.Items, seedRecord{ID: "mlit_road", Data: map[string]any{"id": "mlit_road", "name": "国交省道路整備", "description": "MLIT road construction", "status": "active"}})
	recsprocurement.Items = append(recsprocurement.Items, seedRecord{ID: "mod_defense", Data: map[string]any{"id": "mod_defense", "name": "防衛省装備調達", "description": "MOD equipment procurement", "status": "active"}})
	recsprocurement.Items = append(recsprocurement.Items, seedRecord{ID: "mext_it", Data: map[string]any{"id": "mext_it", "name": "文科省IT調達", "description": "MEXT IT procurement", "status": "active"}})
	recsprocurement.Items = append(recsprocurement.Items, seedRecord{ID: "mhlw_medical", Data: map[string]any{"id": "mhlw_medical", "name": "厚労省医療機器", "description": "MHLW medical equipment", "status": "active"}})
	recsprocurement.Items = append(recsprocurement.Items, seedRecord{ID: "tokyo_infra", Data: map[string]any{"id": "tokyo_infra", "name": "東京都インフラ整備", "description": "Tokyo Metropolitan infrastructure", "status": "active"}})
	def.Records = append(def.Records, recsprocurement)
	return def
}

func ChuushajouGapSeeds() seedDef {
	def := seedDef{Domain: "chuushajou", Nanoid: "ch4sh01", DID: "did:web:chuushajou.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "space:times_shinjuku", DisplayName: "タイムズ新宿", Description: "Times Shinjuku parking"})
	def.DIDs = append(def.DIDs, seedDID{Path: "space:npc_ginza", DisplayName: "NPC銀座", Description: "NPC Ginza parking"})
	def.DIDs = append(def.DIDs, seedDID{Path: "space:akippa_shibuya", DisplayName: "akippa渋谷", Description: "akippa Shibuya"})
	def.DIDs = append(def.DIDs, seedDID{Path: "space:park24_tokyo", DisplayName: "Park24東京駅前", Description: "Park24 Tokyo Station"})
	def.DIDs = append(def.DIDs, seedDID{Path: "space:repark_ikebukuro", DisplayName: "リパーク池袋", Description: "Repark Ikebukuro"})
	recsspace := seedCollection{Collection: "ai.gftd.apps.chuushajou.space"}
	recsspace.Items = append(recsspace.Items, seedRecord{ID: "times_shinjuku", Data: map[string]any{"id": "times_shinjuku", "name": "タイムズ新宿", "description": "Times Shinjuku parking", "status": "active"}})
	recsspace.Items = append(recsspace.Items, seedRecord{ID: "npc_ginza", Data: map[string]any{"id": "npc_ginza", "name": "NPC銀座", "description": "NPC Ginza parking", "status": "active"}})
	recsspace.Items = append(recsspace.Items, seedRecord{ID: "akippa_shibuya", Data: map[string]any{"id": "akippa_shibuya", "name": "akippa渋谷", "description": "akippa Shibuya", "status": "active"}})
	recsspace.Items = append(recsspace.Items, seedRecord{ID: "park24_tokyo", Data: map[string]any{"id": "park24_tokyo", "name": "Park24東京駅前", "description": "Park24 Tokyo Station", "status": "active"}})
	recsspace.Items = append(recsspace.Items, seedRecord{ID: "repark_ikebukuro", Data: map[string]any{"id": "repark_ikebukuro", "name": "リパーク池袋", "description": "Repark Ikebukuro", "status": "active"}})
	def.Records = append(def.Records, recsspace)
	return def
}

func CicdGapSeeds() seedDef {
	def := seedDef{Domain: "cicd", Nanoid: "cicd436b", DID: "did:web:cicd.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "pipeline:github_actions", DisplayName: "GitHub Actions", Description: "CI/CD pipeline"})
	def.DIDs = append(def.DIDs, seedDID{Path: "pipeline:gitlab_ci", DisplayName: "GitLab CI", Description: "CI/CD pipeline"})
	def.DIDs = append(def.DIDs, seedDID{Path: "pipeline:jenkins", DisplayName: "Jenkins Pipeline", Description: "CI/CD pipeline"})
	def.DIDs = append(def.DIDs, seedDID{Path: "pipeline:circleci", DisplayName: "CircleCI", Description: "CI/CD pipeline"})
	def.DIDs = append(def.DIDs, seedDID{Path: "pipeline:argocd", DisplayName: "Argo CD", Description: "GitOps CD"})
	recspipeline := seedCollection{Collection: "ai.gftd.apps.cicd.pipeline"}
	recspipeline.Items = append(recspipeline.Items, seedRecord{ID: "github_actions", Data: map[string]any{"id": "github_actions", "name": "GitHub Actions", "description": "CI/CD pipeline", "status": "active"}})
	recspipeline.Items = append(recspipeline.Items, seedRecord{ID: "gitlab_ci", Data: map[string]any{"id": "gitlab_ci", "name": "GitLab CI", "description": "CI/CD pipeline", "status": "active"}})
	recspipeline.Items = append(recspipeline.Items, seedRecord{ID: "jenkins", Data: map[string]any{"id": "jenkins", "name": "Jenkins Pipeline", "description": "CI/CD pipeline", "status": "active"}})
	recspipeline.Items = append(recspipeline.Items, seedRecord{ID: "circleci", Data: map[string]any{"id": "circleci", "name": "CircleCI", "description": "CI/CD pipeline", "status": "active"}})
	recspipeline.Items = append(recspipeline.Items, seedRecord{ID: "argocd", Data: map[string]any{"id": "argocd", "name": "Argo CD", "description": "GitOps CD", "status": "active"}})
	def.Records = append(def.Records, recspipeline)
	return def
}

func CloudGapSeeds() seedDef {
	def := seedDef{Domain: "cloud", Nanoid: "clou218f", DID: "did:web:cloud.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "instance:aws_ec2", DisplayName: "AWS EC2", Description: "Amazon cloud compute"})
	def.DIDs = append(def.DIDs, seedDID{Path: "instance:gcp_gce", DisplayName: "GCP Compute Engine", Description: "Google cloud compute"})
	def.DIDs = append(def.DIDs, seedDID{Path: "instance:azure_vm", DisplayName: "Azure VM", Description: "Microsoft cloud compute"})
	def.DIDs = append(def.DIDs, seedDID{Path: "instance:cf_workers", DisplayName: "Cloudflare Workers", Description: "Edge compute"})
	def.DIDs = append(def.DIDs, seedDID{Path: "instance:alibaba_ecs", DisplayName: "Alibaba Cloud ECS", Description: "China cloud compute"})
	recsinstance := seedCollection{Collection: "ai.gftd.apps.cloud.instance"}
	recsinstance.Items = append(recsinstance.Items, seedRecord{ID: "aws_ec2", Data: map[string]any{"id": "aws_ec2", "name": "AWS EC2", "description": "Amazon cloud compute", "status": "active"}})
	recsinstance.Items = append(recsinstance.Items, seedRecord{ID: "gcp_gce", Data: map[string]any{"id": "gcp_gce", "name": "GCP Compute Engine", "description": "Google cloud compute", "status": "active"}})
	recsinstance.Items = append(recsinstance.Items, seedRecord{ID: "azure_vm", Data: map[string]any{"id": "azure_vm", "name": "Azure VM", "description": "Microsoft cloud compute", "status": "active"}})
	recsinstance.Items = append(recsinstance.Items, seedRecord{ID: "cf_workers", Data: map[string]any{"id": "cf_workers", "name": "Cloudflare Workers", "description": "Edge compute", "status": "active"}})
	recsinstance.Items = append(recsinstance.Items, seedRecord{ID: "alibaba_ecs", Data: map[string]any{"id": "alibaba_ecs", "name": "Alibaba Cloud ECS", "description": "China cloud compute", "status": "active"}})
	def.Records = append(def.Records, recsinstance)
	return def
}

func CommunitiesGapSeeds() seedDef {
	def := seedDef{Domain: "communities", Nanoid: "2tqvrutp", DID: "did:web:communities.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "org:oss_linux", DisplayName: "Linux Foundation", Description: "Open source community"})
	def.DIDs = append(def.DIDs, seedDID{Path: "org:wikipedia", DisplayName: "Wikipedia Community", Description: "Free encyclopedia editors"})
	def.DIDs = append(def.DIDs, seedDID{Path: "org:stack_overflow", DisplayName: "Stack Overflow", Description: "Developer Q&A community"})
	def.DIDs = append(def.DIDs, seedDID{Path: "org:cncf", DisplayName: "CNCF", Description: "Cloud Native Computing Foundation"})
	def.DIDs = append(def.DIDs, seedDID{Path: "org:apache", DisplayName: "Apache Foundation", Description: "Open source software"})
	recsorg := seedCollection{Collection: "ai.gftd.apps.communities.org"}
	recsorg.Items = append(recsorg.Items, seedRecord{ID: "oss_linux", Data: map[string]any{"id": "oss_linux", "name": "Linux Foundation", "description": "Open source community", "status": "active"}})
	recsorg.Items = append(recsorg.Items, seedRecord{ID: "wikipedia", Data: map[string]any{"id": "wikipedia", "name": "Wikipedia Community", "description": "Free encyclopedia editors", "status": "active"}})
	recsorg.Items = append(recsorg.Items, seedRecord{ID: "stack_overflow", Data: map[string]any{"id": "stack_overflow", "name": "Stack Overflow", "description": "Developer Q&A community", "status": "active"}})
	recsorg.Items = append(recsorg.Items, seedRecord{ID: "cncf", Data: map[string]any{"id": "cncf", "name": "CNCF", "description": "Cloud Native Computing Foundation", "status": "active"}})
	recsorg.Items = append(recsorg.Items, seedRecord{ID: "apache", Data: map[string]any{"id": "apache", "name": "Apache Foundation", "description": "Open source software", "status": "active"}})
	def.Records = append(def.Records, recsorg)
	return def
}

func ContainerGapSeeds() seedDef {
	def := seedDef{Domain: "container", Nanoid: "cn4tn01", DID: "did:web:container.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "image:nginx", DisplayName: "nginx:alpine", Description: "Web server image"})
	def.DIDs = append(def.DIDs, seedDID{Path: "image:postgres", DisplayName: "postgres:16", Description: "Database image"})
	def.DIDs = append(def.DIDs, seedDID{Path: "image:redis", DisplayName: "redis:7", Description: "Cache image"})
	def.DIDs = append(def.DIDs, seedDID{Path: "image:node", DisplayName: "node:22-slim", Description: "Node.js runtime"})
	def.DIDs = append(def.DIDs, seedDID{Path: "container:docker", DisplayName: "Docker Engine", Description: "Container runtime"})
	def.DIDs = append(def.DIDs, seedDID{Path: "container:containerd", DisplayName: "containerd", Description: "Container runtime"})
	recsimage := seedCollection{Collection: "ai.gftd.apps.container.image"}
	recsimage.Items = append(recsimage.Items, seedRecord{ID: "nginx", Data: map[string]any{"id": "nginx", "name": "nginx:alpine", "description": "Web server image", "status": "active"}})
	recsimage.Items = append(recsimage.Items, seedRecord{ID: "postgres", Data: map[string]any{"id": "postgres", "name": "postgres:16", "description": "Database image", "status": "active"}})
	recsimage.Items = append(recsimage.Items, seedRecord{ID: "redis", Data: map[string]any{"id": "redis", "name": "redis:7", "description": "Cache image", "status": "active"}})
	recsimage.Items = append(recsimage.Items, seedRecord{ID: "node", Data: map[string]any{"id": "node", "name": "node:22-slim", "description": "Node.js runtime", "status": "active"}})
	def.Records = append(def.Records, recsimage)
	recscontainer := seedCollection{Collection: "ai.gftd.apps.container.container"}
	recscontainer.Items = append(recscontainer.Items, seedRecord{ID: "docker", Data: map[string]any{"id": "docker", "name": "Docker Engine", "description": "Container runtime", "status": "active"}})
	recscontainer.Items = append(recscontainer.Items, seedRecord{ID: "containerd", Data: map[string]any{"id": "containerd", "name": "containerd", "description": "Container runtime", "status": "active"}})
	def.Records = append(def.Records, recscontainer)
	return def
}

func CreditcardGapSeeds() seedDef {
	def := seedDef{Domain: "creditcard", Nanoid: "cc4rd01", DID: "did:web:creditcard.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "card:visa_gold", DisplayName: "Visa Gold", Description: "Visa gold credit card"})
	def.DIDs = append(def.DIDs, seedDID{Path: "card:mastercard_plat", DisplayName: "Mastercard Platinum", Description: "MC platinum card"})
	def.DIDs = append(def.DIDs, seedDID{Path: "card:amex_green", DisplayName: "American Express Green", Description: "Amex charge card"})
	def.DIDs = append(def.DIDs, seedDID{Path: "card:jcb_gold", DisplayName: "JCB Gold", Description: "JCB gold card"})
	def.DIDs = append(def.DIDs, seedDID{Path: "card:diners_prem", DisplayName: "Diners Club Premium", Description: "Diners premium card"})
	recscard := seedCollection{Collection: "ai.gftd.apps.creditcard.card"}
	recscard.Items = append(recscard.Items, seedRecord{ID: "visa_gold", Data: map[string]any{"id": "visa_gold", "name": "Visa Gold", "description": "Visa gold credit card", "status": "active"}})
	recscard.Items = append(recscard.Items, seedRecord{ID: "mastercard_plat", Data: map[string]any{"id": "mastercard_plat", "name": "Mastercard Platinum", "description": "MC platinum card", "status": "active"}})
	recscard.Items = append(recscard.Items, seedRecord{ID: "amex_green", Data: map[string]any{"id": "amex_green", "name": "American Express Green", "description": "Amex charge card", "status": "active"}})
	recscard.Items = append(recscard.Items, seedRecord{ID: "jcb_gold", Data: map[string]any{"id": "jcb_gold", "name": "JCB Gold", "description": "JCB gold card", "status": "active"}})
	recscard.Items = append(recscard.Items, seedRecord{ID: "diners_prem", Data: map[string]any{"id": "diners_prem", "name": "Diners Club Premium", "description": "Diners premium card", "status": "active"}})
	def.Records = append(def.Records, recscard)
	return def
}

func CtMonitorGapSeeds() seedDef {
	def := seedDef{Domain: "ct-monitor", Nanoid: "ctm0n1t0", DID: "did:web:ct-monitor.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "cert:letsencrypt", DisplayName: "Let's Encrypt Root", Description: "ISRG Root X1"})
	def.DIDs = append(def.DIDs, seedDID{Path: "cert:digicert_global", DisplayName: "DigiCert Global Root", Description: "DigiCert G2"})
	def.DIDs = append(def.DIDs, seedDID{Path: "cert:comodo", DisplayName: "Comodo RSA", Description: "Sectigo root"})
	def.DIDs = append(def.DIDs, seedDID{Path: "cert:google_trust", DisplayName: "Google Trust Services", Description: "GTS Root R1"})
	def.DIDs = append(def.DIDs, seedDID{Path: "cert:amazon_root", DisplayName: "Amazon Root CA", Description: "Amazon Trust Services"})
	recscert := seedCollection{Collection: "ai.gftd.apps.ctmonitor.cert"}
	recscert.Items = append(recscert.Items, seedRecord{ID: "letsencrypt", Data: map[string]any{"id": "letsencrypt", "name": "Let's Encrypt Root", "description": "ISRG Root X1", "status": "active"}})
	recscert.Items = append(recscert.Items, seedRecord{ID: "digicert_global", Data: map[string]any{"id": "digicert_global", "name": "DigiCert Global Root", "description": "DigiCert G2", "status": "active"}})
	recscert.Items = append(recscert.Items, seedRecord{ID: "comodo", Data: map[string]any{"id": "comodo", "name": "Comodo RSA", "description": "Sectigo root", "status": "active"}})
	recscert.Items = append(recscert.Items, seedRecord{ID: "google_trust", Data: map[string]any{"id": "google_trust", "name": "Google Trust Services", "description": "GTS Root R1", "status": "active"}})
	recscert.Items = append(recscert.Items, seedRecord{ID: "amazon_root", Data: map[string]any{"id": "amazon_root", "name": "Amazon Root CA", "description": "Amazon Trust Services", "status": "active"}})
	def.Records = append(def.Records, recscert)
	return def
}

func DbGapSeeds() seedDef {
	def := seedDef{Domain: "db", Nanoid: "g0vintladb01", DID: "did:web:db.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "table:db_schema_001", DisplayName: "Db Schema", Description: "db table"})
	recstable := seedCollection{Collection: "ai.gftd.apps.db.table"}
	recstable.Items = append(recstable.Items, seedRecord{ID: "db_schema_001", Data: map[string]any{"id": "db_schema_001", "name": "Db Schema", "description": "db table", "status": "active"}})
	def.Records = append(def.Records, recstable)
	return def
}

func DcGapSeeds() seedDef {
	def := seedDef{Domain: "dc", Nanoid: "dc4t5c01", DID: "did:web:dc.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "dc:equinix_ty1", DisplayName: "Equinix TY1", Description: "Tokyo data center"})
	def.DIDs = append(def.DIDs, seedDID{Path: "dc:aws_apne1", DisplayName: "AWS ap-northeast-1", Description: "Tokyo region"})
	def.DIDs = append(def.DIDs, seedDID{Path: "dc:ntt_otemachi", DisplayName: "NTT大手町", Description: "NTT Otemachi DC"})
	def.DIDs = append(def.DIDs, seedDID{Path: "dc:google_tw", DisplayName: "Google Taiwan", Description: "Changhua County DC"})
	def.DIDs = append(def.DIDs, seedDID{Path: "dc:microsoft_jp", DisplayName: "Microsoft Japan East", Description: "Saitama DC"})
	def.DIDs = append(def.DIDs, seedDID{Path: "dc:sakura_ishikari", DisplayName: "さくら石狩", Description: "Sakura Ishikari DC"})
	recsdc := seedCollection{Collection: "ai.gftd.apps.dc.dc"}
	recsdc.Items = append(recsdc.Items, seedRecord{ID: "equinix_ty1", Data: map[string]any{"id": "equinix_ty1", "name": "Equinix TY1", "description": "Tokyo data center", "status": "active"}})
	recsdc.Items = append(recsdc.Items, seedRecord{ID: "aws_apne1", Data: map[string]any{"id": "aws_apne1", "name": "AWS ap-northeast-1", "description": "Tokyo region", "status": "active"}})
	recsdc.Items = append(recsdc.Items, seedRecord{ID: "ntt_otemachi", Data: map[string]any{"id": "ntt_otemachi", "name": "NTT大手町", "description": "NTT Otemachi DC", "status": "active"}})
	recsdc.Items = append(recsdc.Items, seedRecord{ID: "google_tw", Data: map[string]any{"id": "google_tw", "name": "Google Taiwan", "description": "Changhua County DC", "status": "active"}})
	recsdc.Items = append(recsdc.Items, seedRecord{ID: "microsoft_jp", Data: map[string]any{"id": "microsoft_jp", "name": "Microsoft Japan East", "description": "Saitama DC", "status": "active"}})
	recsdc.Items = append(recsdc.Items, seedRecord{ID: "sakura_ishikari", Data: map[string]any{"id": "sakura_ishikari", "name": "さくら石狩", "description": "Sakura Ishikari DC", "status": "active"}})
	def.Records = append(def.Records, recsdc)
	return def
}

func DemaeGapSeeds() seedDef {
	def := seedDef{Domain: "demae", Nanoid: "d3ma3x7q", DID: "did:web:demae.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "merchant:ubereats_tokyo", DisplayName: "Uber Eats 東京", Description: "Food delivery"})
	def.DIDs = append(def.DIDs, seedDID{Path: "merchant:demaecan", DisplayName: "出前館", Description: "Japan delivery platform"})
	def.DIDs = append(def.DIDs, seedDID{Path: "merchant:menu_jp", DisplayName: "menu", Description: "Food delivery app"})
	def.DIDs = append(def.DIDs, seedDID{Path: "merchant:wolt_jp", DisplayName: "Wolt Japan", Description: "Delivery platform"})
	def.DIDs = append(def.DIDs, seedDID{Path: "merchant:doordash", DisplayName: "DoorDash", Description: "US delivery platform"})
	recsmerchant := seedCollection{Collection: "ai.gftd.apps.demae.merchant"}
	recsmerchant.Items = append(recsmerchant.Items, seedRecord{ID: "ubereats_tokyo", Data: map[string]any{"id": "ubereats_tokyo", "name": "Uber Eats 東京", "description": "Food delivery", "status": "active"}})
	recsmerchant.Items = append(recsmerchant.Items, seedRecord{ID: "demaecan", Data: map[string]any{"id": "demaecan", "name": "出前館", "description": "Japan delivery platform", "status": "active"}})
	recsmerchant.Items = append(recsmerchant.Items, seedRecord{ID: "menu_jp", Data: map[string]any{"id": "menu_jp", "name": "menu", "description": "Food delivery app", "status": "active"}})
	recsmerchant.Items = append(recsmerchant.Items, seedRecord{ID: "wolt_jp", Data: map[string]any{"id": "wolt_jp", "name": "Wolt Japan", "description": "Delivery platform", "status": "active"}})
	recsmerchant.Items = append(recsmerchant.Items, seedRecord{ID: "doordash", Data: map[string]any{"id": "doordash", "name": "DoorDash", "description": "US delivery platform", "status": "active"}})
	def.Records = append(def.Records, recsmerchant)
	return def
}

func DenkiGapSeeds() seedDef {
	def := seedDef{Domain: "denki", Nanoid: "dk3n7k8p", DID: "did:web:denki.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "plant:tepco_kashiwazaki", DisplayName: "東電柏崎刈羽", Description: "Nuclear power plant"})
	def.DIDs = append(def.DIDs, seedDID{Path: "plant:kansai_ohi", DisplayName: "関電大飯", Description: "Nuclear power plant"})
	def.DIDs = append(def.DIDs, seedDID{Path: "plant:jpower_isogo", DisplayName: "J-POWER磯子", Description: "Coal thermal plant"})
	def.DIDs = append(def.DIDs, seedDID{Path: "plant:mega_solar_hokkaido", DisplayName: "北海道メガソーラー", Description: "Solar farm"})
	def.DIDs = append(def.DIDs, seedDID{Path: "plant:wind_akita", DisplayName: "秋田洋上風力", Description: "Offshore wind farm"})
	def.DIDs = append(def.DIDs, seedDID{Path: "plant:tepco_futtsu", DisplayName: "東電富津", Description: "LNG thermal plant"})
	recsplant := seedCollection{Collection: "ai.gftd.apps.denki.plant"}
	recsplant.Items = append(recsplant.Items, seedRecord{ID: "tepco_kashiwazaki", Data: map[string]any{"id": "tepco_kashiwazaki", "name": "東電柏崎刈羽", "description": "Nuclear power plant", "status": "active"}})
	recsplant.Items = append(recsplant.Items, seedRecord{ID: "kansai_ohi", Data: map[string]any{"id": "kansai_ohi", "name": "関電大飯", "description": "Nuclear power plant", "status": "active"}})
	recsplant.Items = append(recsplant.Items, seedRecord{ID: "jpower_isogo", Data: map[string]any{"id": "jpower_isogo", "name": "J-POWER磯子", "description": "Coal thermal plant", "status": "active"}})
	recsplant.Items = append(recsplant.Items, seedRecord{ID: "mega_solar_hokkaido", Data: map[string]any{"id": "mega_solar_hokkaido", "name": "北海道メガソーラー", "description": "Solar farm", "status": "active"}})
	recsplant.Items = append(recsplant.Items, seedRecord{ID: "wind_akita", Data: map[string]any{"id": "wind_akita", "name": "秋田洋上風力", "description": "Offshore wind farm", "status": "active"}})
	recsplant.Items = append(recsplant.Items, seedRecord{ID: "tepco_futtsu", Data: map[string]any{"id": "tepco_futtsu", "name": "東電富津", "description": "LNG thermal plant", "status": "active"}})
	def.Records = append(def.Records, recsplant)
	return def
}

func DenshiBuhinGapSeeds() seedDef {
	def := seedDef{Domain: "denshi-buhin", Nanoid: "densa7f4", DID: "did:web:denshi-buhin.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "part:mlcc_murata", DisplayName: "村田MLCC", Description: "Multilayer ceramic capacitor"})
	def.DIDs = append(def.DIDs, seedDID{Path: "part:nand_kioxia", DisplayName: "キオクシアNAND", Description: "3D NAND flash"})
	def.DIDs = append(def.DIDs, seedDID{Path: "part:mcu_renesas", DisplayName: "ルネサスMCU", Description: "Microcontroller"})
	def.DIDs = append(def.DIDs, seedDID{Path: "part:igbt_mitsubishi", DisplayName: "三菱IGBT", Description: "Power semiconductor"})
	def.DIDs = append(def.DIDs, seedDID{Path: "part:sensor_sony", DisplayName: "ソニーCMOS", Description: "Image sensor"})
	def.DIDs = append(def.DIDs, seedDID{Path: "part:connector_jst", DisplayName: "JST connector", Description: "Board connector"})
	recspart := seedCollection{Collection: "ai.gftd.apps.denshibuhin.part"}
	recspart.Items = append(recspart.Items, seedRecord{ID: "mlcc_murata", Data: map[string]any{"id": "mlcc_murata", "name": "村田MLCC", "description": "Multilayer ceramic capacitor", "status": "active"}})
	recspart.Items = append(recspart.Items, seedRecord{ID: "nand_kioxia", Data: map[string]any{"id": "nand_kioxia", "name": "キオクシアNAND", "description": "3D NAND flash", "status": "active"}})
	recspart.Items = append(recspart.Items, seedRecord{ID: "mcu_renesas", Data: map[string]any{"id": "mcu_renesas", "name": "ルネサスMCU", "description": "Microcontroller", "status": "active"}})
	recspart.Items = append(recspart.Items, seedRecord{ID: "igbt_mitsubishi", Data: map[string]any{"id": "igbt_mitsubishi", "name": "三菱IGBT", "description": "Power semiconductor", "status": "active"}})
	recspart.Items = append(recspart.Items, seedRecord{ID: "sensor_sony", Data: map[string]any{"id": "sensor_sony", "name": "ソニーCMOS", "description": "Image sensor", "status": "active"}})
	recspart.Items = append(recspart.Items, seedRecord{ID: "connector_jst", Data: map[string]any{"id": "connector_jst", "name": "JST connector", "description": "Board connector", "status": "active"}})
	def.Records = append(def.Records, recspart)
	return def
}

func DerivativeGapSeeds() seedDef {
	def := seedDef{Domain: "derivative", Nanoid: "dv4tv01", DID: "did:web:derivative.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "contract:nikkei_future", DisplayName: "日経225先物", Description: "Nikkei futures"})
	def.DIDs = append(def.DIDs, seedDID{Path: "contract:sp500_option", DisplayName: "S&P 500 Option", Description: "Index option"})
	def.DIDs = append(def.DIDs, seedDID{Path: "contract:fx_usdjpy", DisplayName: "USD/JPY Forward", Description: "FX forward"})
	def.DIDs = append(def.DIDs, seedDID{Path: "contract:irs_jpy", DisplayName: "JPY IRS", Description: "Interest rate swap"})
	def.DIDs = append(def.DIDs, seedDID{Path: "contract:cds_corp", DisplayName: "Corporate CDS", Description: "Credit default swap"})
	recscontract := seedCollection{Collection: "ai.gftd.apps.derivative.contract"}
	recscontract.Items = append(recscontract.Items, seedRecord{ID: "nikkei_future", Data: map[string]any{"id": "nikkei_future", "name": "日経225先物", "description": "Nikkei futures", "status": "active"}})
	recscontract.Items = append(recscontract.Items, seedRecord{ID: "sp500_option", Data: map[string]any{"id": "sp500_option", "name": "S&P 500 Option", "description": "Index option", "status": "active"}})
	recscontract.Items = append(recscontract.Items, seedRecord{ID: "fx_usdjpy", Data: map[string]any{"id": "fx_usdjpy", "name": "USD/JPY Forward", "description": "FX forward", "status": "active"}})
	recscontract.Items = append(recscontract.Items, seedRecord{ID: "irs_jpy", Data: map[string]any{"id": "irs_jpy", "name": "JPY IRS", "description": "Interest rate swap", "status": "active"}})
	recscontract.Items = append(recscontract.Items, seedRecord{ID: "cds_corp", Data: map[string]any{"id": "cds_corp", "name": "Corporate CDS", "description": "Credit default swap", "status": "active"}})
	def.Records = append(def.Records, recscontract)
	return def
}

func DevGapSeeds() seedDef {
	def := seedDef{Domain: "dev", Nanoid: "dev4070", DID: "did:web:dev.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "account:github_org", DisplayName: "GitHub Organization", Description: "Developer account"})
	def.DIDs = append(def.DIDs, seedDID{Path: "account:npm_scope", DisplayName: "npm @scope", Description: "Package registry account"})
	def.DIDs = append(def.DIDs, seedDID{Path: "account:docker_hub", DisplayName: "Docker Hub", Description: "Container registry"})
	def.DIDs = append(def.DIDs, seedDID{Path: "account:pypi_org", DisplayName: "PyPI Organization", Description: "Python package index"})
	def.DIDs = append(def.DIDs, seedDID{Path: "account:crates_io", DisplayName: "crates.io", Description: "Rust package registry"})
	recsaccount := seedCollection{Collection: "ai.gftd.apps.dev.account"}
	recsaccount.Items = append(recsaccount.Items, seedRecord{ID: "github_org", Data: map[string]any{"id": "github_org", "name": "GitHub Organization", "description": "Developer account", "status": "active"}})
	recsaccount.Items = append(recsaccount.Items, seedRecord{ID: "npm_scope", Data: map[string]any{"id": "npm_scope", "name": "npm @scope", "description": "Package registry account", "status": "active"}})
	recsaccount.Items = append(recsaccount.Items, seedRecord{ID: "docker_hub", Data: map[string]any{"id": "docker_hub", "name": "Docker Hub", "description": "Container registry", "status": "active"}})
	recsaccount.Items = append(recsaccount.Items, seedRecord{ID: "pypi_org", Data: map[string]any{"id": "pypi_org", "name": "PyPI Organization", "description": "Python package index", "status": "active"}})
	recsaccount.Items = append(recsaccount.Items, seedRecord{ID: "crates_io", Data: map[string]any{"id": "crates_io", "name": "crates.io", "description": "Rust package registry", "status": "active"}})
	def.Records = append(def.Records, recsaccount)
	return def
}

func DnsGapSeeds() seedDef {
	def := seedDef{Domain: "dns", Nanoid: "scndu0rf", DID: "did:web:dns.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "zone:example_com", DisplayName: "example.com", Description: "DNS zone"})
	def.DIDs = append(def.DIDs, seedDID{Path: "zone:gftd_ai", DisplayName: "etzhayyim.com", Description: "Platform DNS zone"})
	def.DIDs = append(def.DIDs, seedDID{Path: "cert_history:le_2024", DisplayName: "Let's Encrypt 2024", Description: "CT log entry"})
	def.DIDs = append(def.DIDs, seedDID{Path: "whois_snapshot:example_2024", DisplayName: "example.com WHOIS", Description: "WHOIS snapshot"})
	recszone := seedCollection{Collection: "ai.gftd.apps.dns.zone"}
	recszone.Items = append(recszone.Items, seedRecord{ID: "example_com", Data: map[string]any{"id": "example_com", "name": "example.com", "description": "DNS zone", "status": "active"}})
	recszone.Items = append(recszone.Items, seedRecord{ID: "gftd_ai", Data: map[string]any{"id": "gftd_ai", "name": "etzhayyim.com", "description": "Platform DNS zone", "status": "active"}})
	def.Records = append(def.Records, recszone)
	recscert_history := seedCollection{Collection: "ai.gftd.apps.dns.cert_history"}
	recscert_history.Items = append(recscert_history.Items, seedRecord{ID: "le_2024", Data: map[string]any{"id": "le_2024", "name": "Let's Encrypt 2024", "description": "CT log entry", "status": "active"}})
	def.Records = append(def.Records, recscert_history)
	recswhois_snapshot := seedCollection{Collection: "ai.gftd.apps.dns.whois_snapshot"}
	recswhois_snapshot.Items = append(recswhois_snapshot.Items, seedRecord{ID: "example_2024", Data: map[string]any{"id": "example_2024", "name": "example.com WHOIS", "description": "WHOIS snapshot", "status": "active"}})
	def.Records = append(def.Records, recswhois_snapshot)
	return def
}

func DojoGapSeeds() seedDef {
	def := seedDef{Domain: "dojo", Nanoid: "d0j0k4t4", DID: "did:web:dojo.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "drill:incident_response", DisplayName: "Incident Response Drill", Description: "Security readiness"})
	def.DIDs = append(def.DIDs, seedDID{Path: "drill:disaster_recovery", DisplayName: "Disaster Recovery", Description: "DR failover test"})
	def.DIDs = append(def.DIDs, seedDID{Path: "drill:load_test", DisplayName: "Load Test Kata", Description: "Performance readiness"})
	def.DIDs = append(def.DIDs, seedDID{Path: "drill:deploy_rollback", DisplayName: "Deploy Rollback", Description: "Deployment readiness"})
	def.DIDs = append(def.DIDs, seedDID{Path: "drill:data_breach", DisplayName: "Data Breach Response", Description: "Privacy incident drill"})
	recsdrill := seedCollection{Collection: "ai.gftd.apps.dojo.drill"}
	recsdrill.Items = append(recsdrill.Items, seedRecord{ID: "incident_response", Data: map[string]any{"id": "incident_response", "name": "Incident Response Drill", "description": "Security readiness", "status": "active"}})
	recsdrill.Items = append(recsdrill.Items, seedRecord{ID: "disaster_recovery", Data: map[string]any{"id": "disaster_recovery", "name": "Disaster Recovery", "description": "DR failover test", "status": "active"}})
	recsdrill.Items = append(recsdrill.Items, seedRecord{ID: "load_test", Data: map[string]any{"id": "load_test", "name": "Load Test Kata", "description": "Performance readiness", "status": "active"}})
	recsdrill.Items = append(recsdrill.Items, seedRecord{ID: "deploy_rollback", Data: map[string]any{"id": "deploy_rollback", "name": "Deploy Rollback", "description": "Deployment readiness", "status": "active"}})
	recsdrill.Items = append(recsdrill.Items, seedRecord{ID: "data_breach", Data: map[string]any{"id": "data_breach", "name": "Data Breach Response", "description": "Privacy incident drill", "status": "active"}})
	def.Records = append(def.Records, recsdrill)
	return def
}

func DouroGapSeeds() seedDef {
	def := seedDef{Domain: "douro", Nanoid: "dr4rd01", DID: "did:web:douro.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "bridge:akashi", DisplayName: "明石海峡大橋", Description: "Akashi Kaikyo Bridge"})
	def.DIDs = append(def.DIDs, seedDID{Path: "bridge:rainbow", DisplayName: "レインボーブリッジ", Description: "Rainbow Bridge, Tokyo"})
	def.DIDs = append(def.DIDs, seedDID{Path: "tunnel:kan_etsu", DisplayName: "関越トンネル", Description: "Kan-Etsu Tunnel"})
	def.DIDs = append(def.DIDs, seedDID{Path: "sign:speed_limit_60", DisplayName: "速度制限60", Description: "60 km/h speed limit sign"})
	def.DIDs = append(def.DIDs, seedDID{Path: "signal:shibuya_scramble", DisplayName: "渋谷スクランブル信号", Description: "Shibuya Scramble crossing"})
	def.DIDs = append(def.DIDs, seedDID{Path: "light:led_street_01", DisplayName: "LED街灯01", Description: "LED street light"})
	def.DIDs = append(def.DIDs, seedDID{Path: "barrier:guardrail_01", DisplayName: "ガードレール01", Description: "Highway guardrail"})
	def.DIDs = append(def.DIDs, seedDID{Path: "marking:crosswalk_01", DisplayName: "横断歩道01", Description: "Crosswalk marking"})
	def.DIDs = append(def.DIDs, seedDID{Path: "gate:tomei_tokyo", DisplayName: "東名東京料金所", Description: "Tomei Expressway toll gate"})
	recsbridge := seedCollection{Collection: "ai.gftd.apps.douro.bridge"}
	recsbridge.Items = append(recsbridge.Items, seedRecord{ID: "akashi", Data: map[string]any{"id": "akashi", "name": "明石海峡大橋", "description": "Akashi Kaikyo Bridge", "status": "active"}})
	recsbridge.Items = append(recsbridge.Items, seedRecord{ID: "rainbow", Data: map[string]any{"id": "rainbow", "name": "レインボーブリッジ", "description": "Rainbow Bridge, Tokyo", "status": "active"}})
	def.Records = append(def.Records, recsbridge)
	recstunnel := seedCollection{Collection: "ai.gftd.apps.douro.tunnel"}
	recstunnel.Items = append(recstunnel.Items, seedRecord{ID: "kan_etsu", Data: map[string]any{"id": "kan_etsu", "name": "関越トンネル", "description": "Kan-Etsu Tunnel", "status": "active"}})
	def.Records = append(def.Records, recstunnel)
	recssign := seedCollection{Collection: "ai.gftd.apps.douro.sign"}
	recssign.Items = append(recssign.Items, seedRecord{ID: "speed_limit_60", Data: map[string]any{"id": "speed_limit_60", "name": "速度制限60", "description": "60 km/h speed limit sign", "status": "active"}})
	def.Records = append(def.Records, recssign)
	recssignal := seedCollection{Collection: "ai.gftd.apps.douro.signal"}
	recssignal.Items = append(recssignal.Items, seedRecord{ID: "shibuya_scramble", Data: map[string]any{"id": "shibuya_scramble", "name": "渋谷スクランブル信号", "description": "Shibuya Scramble crossing", "status": "active"}})
	def.Records = append(def.Records, recssignal)
	recslight := seedCollection{Collection: "ai.gftd.apps.douro.light"}
	recslight.Items = append(recslight.Items, seedRecord{ID: "led_street_01", Data: map[string]any{"id": "led_street_01", "name": "LED街灯01", "description": "LED street light", "status": "active"}})
	def.Records = append(def.Records, recslight)
	recsbarrier := seedCollection{Collection: "ai.gftd.apps.douro.barrier"}
	recsbarrier.Items = append(recsbarrier.Items, seedRecord{ID: "guardrail_01", Data: map[string]any{"id": "guardrail_01", "name": "ガードレール01", "description": "Highway guardrail", "status": "active"}})
	def.Records = append(def.Records, recsbarrier)
	recsmarking := seedCollection{Collection: "ai.gftd.apps.douro.marking"}
	recsmarking.Items = append(recsmarking.Items, seedRecord{ID: "crosswalk_01", Data: map[string]any{"id": "crosswalk_01", "name": "横断歩道01", "description": "Crosswalk marking", "status": "active"}})
	def.Records = append(def.Records, recsmarking)
	recsgate := seedCollection{Collection: "ai.gftd.apps.douro.gate"}
	recsgate.Items = append(recsgate.Items, seedRecord{ID: "tomei_tokyo", Data: map[string]any{"id": "tomei_tokyo", "name": "東名東京料金所", "description": "Tomei Expressway toll gate", "status": "active"}})
	def.Records = append(def.Records, recsgate)
	return def
}

func DroneGapSeeds() seedDef {
	def := seedDef{Domain: "drone", Nanoid: "dr0n3x8k", DID: "did:web:drone.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "drone:dji_mavic3", DisplayName: "DJI Mavic 3", Description: "Consumer drone"})
	def.DIDs = append(def.DIDs, seedDID{Path: "drone:dji_matrice", DisplayName: "DJI Matrice 350", Description: "Enterprise drone"})
	def.DIDs = append(def.DIDs, seedDID{Path: "drone:skydio_x10", DisplayName: "Skydio X10", Description: "Autonomous drone"})
	def.DIDs = append(def.DIDs, seedDID{Path: "drone:parrot_anafi", DisplayName: "Parrot ANAFI", Description: "Compact drone"})
	def.DIDs = append(def.DIDs, seedDID{Path: "drone:autel_evo2", DisplayName: "Autel EVO II", Description: "8K camera drone"})
	recsdrone := seedCollection{Collection: "ai.gftd.apps.drone.drone"}
	recsdrone.Items = append(recsdrone.Items, seedRecord{ID: "dji_mavic3", Data: map[string]any{"id": "dji_mavic3", "name": "DJI Mavic 3", "description": "Consumer drone", "status": "active"}})
	recsdrone.Items = append(recsdrone.Items, seedRecord{ID: "dji_matrice", Data: map[string]any{"id": "dji_matrice", "name": "DJI Matrice 350", "description": "Enterprise drone", "status": "active"}})
	recsdrone.Items = append(recsdrone.Items, seedRecord{ID: "skydio_x10", Data: map[string]any{"id": "skydio_x10", "name": "Skydio X10", "description": "Autonomous drone", "status": "active"}})
	recsdrone.Items = append(recsdrone.Items, seedRecord{ID: "parrot_anafi", Data: map[string]any{"id": "parrot_anafi", "name": "Parrot ANAFI", "description": "Compact drone", "status": "active"}})
	recsdrone.Items = append(recsdrone.Items, seedRecord{ID: "autel_evo2", Data: map[string]any{"id": "autel_evo2", "name": "Autel EVO II", "description": "8K camera drone", "status": "active"}})
	def.Records = append(def.Records, recsdrone)
	return def
}

func EnergyGapSeeds() seedDef {
	def := seedDef{Domain: "energy", Nanoid: "en4kw9hc", DID: "did:web:energy.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "asset:solar_sahara", DisplayName: "Sahara Solar Farm", Description: "Large-scale solar"})
	def.DIDs = append(def.DIDs, seedDID{Path: "asset:wind_north_sea", DisplayName: "North Sea Wind Farm", Description: "Offshore wind"})
	def.DIDs = append(def.DIDs, seedDID{Path: "asset:hydro_three_gorges", DisplayName: "Three Gorges Dam", Description: "Hydroelectric"})
	def.DIDs = append(def.DIDs, seedDID{Path: "asset:nuclear_hinkley", DisplayName: "Hinkley Point C", Description: "Nuclear power"})
	def.DIDs = append(def.DIDs, seedDID{Path: "asset:geothermal_iceland", DisplayName: "Hellisheiði", Description: "Geothermal plant"})
	def.DIDs = append(def.DIDs, seedDID{Path: "record:consumption_jp_2024", DisplayName: "Japan 2024 Consumption", Description: "Annual energy data"})
	recsasset := seedCollection{Collection: "ai.gftd.apps.energy.asset"}
	recsasset.Items = append(recsasset.Items, seedRecord{ID: "solar_sahara", Data: map[string]any{"id": "solar_sahara", "name": "Sahara Solar Farm", "description": "Large-scale solar", "status": "active"}})
	recsasset.Items = append(recsasset.Items, seedRecord{ID: "wind_north_sea", Data: map[string]any{"id": "wind_north_sea", "name": "North Sea Wind Farm", "description": "Offshore wind", "status": "active"}})
	recsasset.Items = append(recsasset.Items, seedRecord{ID: "hydro_three_gorges", Data: map[string]any{"id": "hydro_three_gorges", "name": "Three Gorges Dam", "description": "Hydroelectric", "status": "active"}})
	recsasset.Items = append(recsasset.Items, seedRecord{ID: "nuclear_hinkley", Data: map[string]any{"id": "nuclear_hinkley", "name": "Hinkley Point C", "description": "Nuclear power", "status": "active"}})
	recsasset.Items = append(recsasset.Items, seedRecord{ID: "geothermal_iceland", Data: map[string]any{"id": "geothermal_iceland", "name": "Hellisheiði", "description": "Geothermal plant", "status": "active"}})
	def.Records = append(def.Records, recsasset)
	recsrecord := seedCollection{Collection: "ai.gftd.apps.energy.record"}
	recsrecord.Items = append(recsrecord.Items, seedRecord{ID: "consumption_jp_2024", Data: map[string]any{"id": "consumption_jp_2024", "name": "Japan 2024 Consumption", "description": "Annual energy data", "status": "active"}})
	def.Records = append(def.Records, recsrecord)
	return def
}

func EpisodeGapSeeds() seedDef {
	def := seedDef{Domain: "episode", Nanoid: "ep4sd01", DID: "did:web:episode.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "episode:onepiece_1", DisplayName: "One Piece EP1", Description: "Romance Dawn"})
	def.DIDs = append(def.DIDs, seedDID{Path: "episode:demon_slayer_1", DisplayName: "鬼滅の刃 EP1", Description: "Cruelty"})
	def.DIDs = append(def.DIDs, seedDID{Path: "arc:wano", DisplayName: "ワノ国編", Description: "One Piece Wano arc"})
	def.DIDs = append(def.DIDs, seedDID{Path: "episode:jjk_1", DisplayName: "呪術廻戦 EP1", Description: "Ryomen Sukuna"})
	def.DIDs = append(def.DIDs, seedDID{Path: "episode:spy_family_1", DisplayName: "SPY×FAMILY EP1", Description: "Operation Strix"})
	recsepisode := seedCollection{Collection: "ai.gftd.apps.episode.episode"}
	recsepisode.Items = append(recsepisode.Items, seedRecord{ID: "onepiece_1", Data: map[string]any{"id": "onepiece_1", "name": "One Piece EP1", "description": "Romance Dawn", "status": "active"}})
	recsepisode.Items = append(recsepisode.Items, seedRecord{ID: "demon_slayer_1", Data: map[string]any{"id": "demon_slayer_1", "name": "鬼滅の刃 EP1", "description": "Cruelty", "status": "active"}})
	recsepisode.Items = append(recsepisode.Items, seedRecord{ID: "jjk_1", Data: map[string]any{"id": "jjk_1", "name": "呪術廻戦 EP1", "description": "Ryomen Sukuna", "status": "active"}})
	recsepisode.Items = append(recsepisode.Items, seedRecord{ID: "spy_family_1", Data: map[string]any{"id": "spy_family_1", "name": "SPY×FAMILY EP1", "description": "Operation Strix", "status": "active"}})
	def.Records = append(def.Records, recsepisode)
	recsarc := seedCollection{Collection: "ai.gftd.apps.episode.arc"}
	recsarc.Items = append(recsarc.Items, seedRecord{ID: "wano", Data: map[string]any{"id": "wano", "name": "ワノ国編", "description": "One Piece Wano arc", "status": "active"}})
	def.Records = append(def.Records, recsarc)
	return def
}

func EquipmentGapSeeds() seedDef {
	def := seedDef{Domain: "equipment", Nanoid: "eq6mt9yl", DID: "did:web:equipment.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "equipment:excavator_cat", DisplayName: "CAT 320 Excavator", Description: "Hydraulic excavator"})
	def.DIDs = append(def.DIDs, seedDID{Path: "equipment:crane_liebherr", DisplayName: "Liebherr LTM 1300", Description: "Mobile crane"})
	def.DIDs = append(def.DIDs, seedDID{Path: "equipment:forklift_toyota", DisplayName: "Toyota 8FG25", Description: "Forklift"})
	def.DIDs = append(def.DIDs, seedDID{Path: "equipment:compressor_atlas", DisplayName: "Atlas Copco GA37", Description: "Air compressor"})
	def.DIDs = append(def.DIDs, seedDID{Path: "equipment:generator_cat", DisplayName: "CAT C15 Generator", Description: "Diesel generator"})
	recsequipment := seedCollection{Collection: "ai.gftd.apps.equipment.equipment"}
	recsequipment.Items = append(recsequipment.Items, seedRecord{ID: "excavator_cat", Data: map[string]any{"id": "excavator_cat", "name": "CAT 320 Excavator", "description": "Hydraulic excavator", "status": "active"}})
	recsequipment.Items = append(recsequipment.Items, seedRecord{ID: "crane_liebherr", Data: map[string]any{"id": "crane_liebherr", "name": "Liebherr LTM 1300", "description": "Mobile crane", "status": "active"}})
	recsequipment.Items = append(recsequipment.Items, seedRecord{ID: "forklift_toyota", Data: map[string]any{"id": "forklift_toyota", "name": "Toyota 8FG25", "description": "Forklift", "status": "active"}})
	recsequipment.Items = append(recsequipment.Items, seedRecord{ID: "compressor_atlas", Data: map[string]any{"id": "compressor_atlas", "name": "Atlas Copco GA37", "description": "Air compressor", "status": "active"}})
	recsequipment.Items = append(recsequipment.Items, seedRecord{ID: "generator_cat", Data: map[string]any{"id": "generator_cat", "name": "CAT C15 Generator", "description": "Diesel generator", "status": "active"}})
	def.Records = append(def.Records, recsequipment)
	return def
}

func EthicsGapSeeds() seedDef {
	def := seedDef{Domain: "ethics", Nanoid: "eth1cs01", DID: "did:web:ethics.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "code:ieee_ethics", DisplayName: "IEEE Code of Ethics", Description: "Engineering ethics"})
	def.DIDs = append(def.DIDs, seedDID{Path: "code:ama_medical", DisplayName: "AMA Code of Medical Ethics", Description: "Medical ethics"})
	def.DIDs = append(def.DIDs, seedDID{Path: "code:aba_legal", DisplayName: "ABA Model Rules", Description: "Legal professional ethics"})
	def.DIDs = append(def.DIDs, seedDID{Path: "code:acm_computing", DisplayName: "ACM Code of Ethics", Description: "Computing ethics"})
	def.DIDs = append(def.DIDs, seedDID{Path: "code:cfa_standards", DisplayName: "CFA Standards", Description: "Financial ethics"})
	recscode := seedCollection{Collection: "ai.gftd.apps.ethics.code"}
	recscode.Items = append(recscode.Items, seedRecord{ID: "ieee_ethics", Data: map[string]any{"id": "ieee_ethics", "name": "IEEE Code of Ethics", "description": "Engineering ethics", "status": "active"}})
	recscode.Items = append(recscode.Items, seedRecord{ID: "ama_medical", Data: map[string]any{"id": "ama_medical", "name": "AMA Code of Medical Ethics", "description": "Medical ethics", "status": "active"}})
	recscode.Items = append(recscode.Items, seedRecord{ID: "aba_legal", Data: map[string]any{"id": "aba_legal", "name": "ABA Model Rules", "description": "Legal professional ethics", "status": "active"}})
	recscode.Items = append(recscode.Items, seedRecord{ID: "acm_computing", Data: map[string]any{"id": "acm_computing", "name": "ACM Code of Ethics", "description": "Computing ethics", "status": "active"}})
	recscode.Items = append(recscode.Items, seedRecord{ID: "cfa_standards", Data: map[string]any{"id": "cfa_standards", "name": "CFA Standards", "description": "Financial ethics", "status": "active"}})
	def.Records = append(def.Records, recscode)
	return def
}

func EvGapSeeds() seedDef {
	def := seedDef{Domain: "ev", Nanoid: "fw4dinae", DID: "did:web:ev.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "station:tesla_sc_tokyo", DisplayName: "Tesla SC東京", Description: "Tesla Supercharger"})
	def.DIDs = append(def.DIDs, seedDID{Path: "station:chademo_osaka", DisplayName: "CHAdeMO大阪駅", Description: "CHAdeMO quick charger"})
	def.DIDs = append(def.DIDs, seedDID{Path: "station:eneosev_yokohama", DisplayName: "ENEOS EV横浜", Description: "ENEOS EV station"})
	def.DIDs = append(def.DIDs, seedDID{Path: "station:ionity_berlin", DisplayName: "IONITY Berlin", Description: "European fast charger"})
	def.DIDs = append(def.DIDs, seedDID{Path: "station:chargepoint_sf", DisplayName: "ChargePoint SF", Description: "US charging station"})
	recsstation := seedCollection{Collection: "ai.gftd.apps.ev.station"}
	recsstation.Items = append(recsstation.Items, seedRecord{ID: "tesla_sc_tokyo", Data: map[string]any{"id": "tesla_sc_tokyo", "name": "Tesla SC東京", "description": "Tesla Supercharger", "status": "active"}})
	recsstation.Items = append(recsstation.Items, seedRecord{ID: "chademo_osaka", Data: map[string]any{"id": "chademo_osaka", "name": "CHAdeMO大阪駅", "description": "CHAdeMO quick charger", "status": "active"}})
	recsstation.Items = append(recsstation.Items, seedRecord{ID: "eneosev_yokohama", Data: map[string]any{"id": "eneosev_yokohama", "name": "ENEOS EV横浜", "description": "ENEOS EV station", "status": "active"}})
	recsstation.Items = append(recsstation.Items, seedRecord{ID: "ionity_berlin", Data: map[string]any{"id": "ionity_berlin", "name": "IONITY Berlin", "description": "European fast charger", "status": "active"}})
	recsstation.Items = append(recsstation.Items, seedRecord{ID: "chargepoint_sf", Data: map[string]any{"id": "chargepoint_sf", "name": "ChargePoint SF", "description": "US charging station", "status": "active"}})
	def.Records = append(def.Records, recsstation)
	return def
}

func EventGapSeeds() seedDef {
	def := seedDef{Domain: "event", Nanoid: "evena966", DID: "did:web:event.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "event:tokyo_marathon", DisplayName: "東京マラソン", Description: "Annual marathon event"})
	def.DIDs = append(def.DIDs, seedDID{Path: "event:comiket", DisplayName: "コミケ", Description: "Comic Market"})
	def.DIDs = append(def.DIDs, seedDID{Path: "event:ces_2025", DisplayName: "CES 2025", Description: "Consumer Electronics Show"})
	def.DIDs = append(def.DIDs, seedDID{Path: "event:olympics_2028", DisplayName: "LA Olympics 2028", Description: "Summer Olympics"})
	def.DIDs = append(def.DIDs, seedDID{Path: "event:fuji_rock", DisplayName: "フジロック", Description: "Music festival"})
	recsevent := seedCollection{Collection: "ai.gftd.apps.event.event"}
	recsevent.Items = append(recsevent.Items, seedRecord{ID: "tokyo_marathon", Data: map[string]any{"id": "tokyo_marathon", "name": "東京マラソン", "description": "Annual marathon event", "status": "active"}})
	recsevent.Items = append(recsevent.Items, seedRecord{ID: "comiket", Data: map[string]any{"id": "comiket", "name": "コミケ", "description": "Comic Market", "status": "active"}})
	recsevent.Items = append(recsevent.Items, seedRecord{ID: "ces_2025", Data: map[string]any{"id": "ces_2025", "name": "CES 2025", "description": "Consumer Electronics Show", "status": "active"}})
	recsevent.Items = append(recsevent.Items, seedRecord{ID: "olympics_2028", Data: map[string]any{"id": "olympics_2028", "name": "LA Olympics 2028", "description": "Summer Olympics", "status": "active"}})
	recsevent.Items = append(recsevent.Items, seedRecord{ID: "fuji_rock", Data: map[string]any{"id": "fuji_rock", "name": "フジロック", "description": "Music festival", "status": "active"}})
	def.Records = append(def.Records, recsevent)
	return def
}

func FactoryGapSeeds() seedDef {
	def := seedDef{Domain: "factory", Nanoid: "fc9wt5hj", DID: "did:web:factory.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "factory:toyota_motomachi", DisplayName: "トヨタ元町工場", Description: "Toyota Motomachi plant"})
	def.DIDs = append(def.DIDs, seedDID{Path: "factory:tsmc_fab18", DisplayName: "TSMC Fab 18", Description: "Semiconductor fab"})
	def.DIDs = append(def.DIDs, seedDID{Path: "factory:samsung_pyeongtaek", DisplayName: "Samsung Pyeongtaek", Description: "Memory fab"})
	def.DIDs = append(def.DIDs, seedDID{Path: "factory:tesla_giga_berlin", DisplayName: "Tesla Giga Berlin", Description: "EV factory"})
	def.DIDs = append(def.DIDs, seedDID{Path: "factory:foxconn_shenzhen", DisplayName: "Foxconn Shenzhen", Description: "Electronics assembly"})
	recsfactory := seedCollection{Collection: "ai.gftd.apps.factory.factory"}
	recsfactory.Items = append(recsfactory.Items, seedRecord{ID: "toyota_motomachi", Data: map[string]any{"id": "toyota_motomachi", "name": "トヨタ元町工場", "description": "Toyota Motomachi plant", "status": "active"}})
	recsfactory.Items = append(recsfactory.Items, seedRecord{ID: "tsmc_fab18", Data: map[string]any{"id": "tsmc_fab18", "name": "TSMC Fab 18", "description": "Semiconductor fab", "status": "active"}})
	recsfactory.Items = append(recsfactory.Items, seedRecord{ID: "samsung_pyeongtaek", Data: map[string]any{"id": "samsung_pyeongtaek", "name": "Samsung Pyeongtaek", "description": "Memory fab", "status": "active"}})
	recsfactory.Items = append(recsfactory.Items, seedRecord{ID: "tesla_giga_berlin", Data: map[string]any{"id": "tesla_giga_berlin", "name": "Tesla Giga Berlin", "description": "EV factory", "status": "active"}})
	recsfactory.Items = append(recsfactory.Items, seedRecord{ID: "foxconn_shenzhen", Data: map[string]any{"id": "foxconn_shenzhen", "name": "Foxconn Shenzhen", "description": "Electronics assembly", "status": "active"}})
	def.Records = append(def.Records, recsfactory)
	return def
}

func FarmGapSeeds() seedDef {
	def := seedDef{Domain: "farm", Nanoid: "fm8kv4xt", DID: "did:web:farm.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "farm:hokkaido_dairy", DisplayName: "北海道酪農場", Description: "Hokkaido dairy farm"})
	def.DIDs = append(def.DIDs, seedDID{Path: "farm:niigata_rice", DisplayName: "新潟コシヒカリ農場", Description: "Niigata rice paddy"})
	def.DIDs = append(def.DIDs, seedDID{Path: "farm:shizuoka_tea", DisplayName: "静岡茶農園", Description: "Shizuoka tea plantation"})
	def.DIDs = append(def.DIDs, seedDID{Path: "farm:napa_vineyard", DisplayName: "Napa Valley Vineyard", Description: "California winery"})
	def.DIDs = append(def.DIDs, seedDID{Path: "farm:dutch_tulip", DisplayName: "Dutch Tulip Farm", Description: "Netherlands floriculture"})
	recsfarm := seedCollection{Collection: "ai.gftd.apps.farm.farm"}
	recsfarm.Items = append(recsfarm.Items, seedRecord{ID: "hokkaido_dairy", Data: map[string]any{"id": "hokkaido_dairy", "name": "北海道酪農場", "description": "Hokkaido dairy farm", "status": "active"}})
	recsfarm.Items = append(recsfarm.Items, seedRecord{ID: "niigata_rice", Data: map[string]any{"id": "niigata_rice", "name": "新潟コシヒカリ農場", "description": "Niigata rice paddy", "status": "active"}})
	recsfarm.Items = append(recsfarm.Items, seedRecord{ID: "shizuoka_tea", Data: map[string]any{"id": "shizuoka_tea", "name": "静岡茶農園", "description": "Shizuoka tea plantation", "status": "active"}})
	recsfarm.Items = append(recsfarm.Items, seedRecord{ID: "napa_vineyard", Data: map[string]any{"id": "napa_vineyard", "name": "Napa Valley Vineyard", "description": "California winery", "status": "active"}})
	recsfarm.Items = append(recsfarm.Items, seedRecord{ID: "dutch_tulip", Data: map[string]any{"id": "dutch_tulip", "name": "Dutch Tulip Farm", "description": "Netherlands floriculture", "status": "active"}})
	def.Records = append(def.Records, recsfarm)
	return def
}

func FestivalGapSeeds() seedDef {
	def := seedDef{Domain: "festival", Nanoid: "fest2047", DID: "did:web:festival.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "festival:gion_matsuri", DisplayName: "祇園祭", Description: "Kyoto, July"})
	def.DIDs = append(def.DIDs, seedDID{Path: "festival:carnival_rio", DisplayName: "Rio Carnival", Description: "Rio de Janeiro, February"})
	def.DIDs = append(def.DIDs, seedDID{Path: "festival:oktoberfest", DisplayName: "Oktoberfest", Description: "Munich, September"})
	def.DIDs = append(def.DIDs, seedDID{Path: "festival:diwali", DisplayName: "Diwali", Description: "India, October/November"})
	def.DIDs = append(def.DIDs, seedDID{Path: "festival:songkran", DisplayName: "Songkran", Description: "Thailand, April"})
	def.DIDs = append(def.DIDs, seedDID{Path: "festival:hanami", DisplayName: "花見", Description: "Japan, March/April"})
	recsfestival := seedCollection{Collection: "ai.gftd.apps.festival.festival"}
	recsfestival.Items = append(recsfestival.Items, seedRecord{ID: "gion_matsuri", Data: map[string]any{"id": "gion_matsuri", "name": "祇園祭", "description": "Kyoto, July", "status": "active"}})
	recsfestival.Items = append(recsfestival.Items, seedRecord{ID: "carnival_rio", Data: map[string]any{"id": "carnival_rio", "name": "Rio Carnival", "description": "Rio de Janeiro, February", "status": "active"}})
	recsfestival.Items = append(recsfestival.Items, seedRecord{ID: "oktoberfest", Data: map[string]any{"id": "oktoberfest", "name": "Oktoberfest", "description": "Munich, September", "status": "active"}})
	recsfestival.Items = append(recsfestival.Items, seedRecord{ID: "diwali", Data: map[string]any{"id": "diwali", "name": "Diwali", "description": "India, October/November", "status": "active"}})
	recsfestival.Items = append(recsfestival.Items, seedRecord{ID: "songkran", Data: map[string]any{"id": "songkran", "name": "Songkran", "description": "Thailand, April", "status": "active"}})
	recsfestival.Items = append(recsfestival.Items, seedRecord{ID: "hanami", Data: map[string]any{"id": "hanami", "name": "花見", "description": "Japan, March/April", "status": "active"}})
	def.Records = append(def.Records, recsfestival)
	return def
}

func FleamarketGapSeeds() seedDef {
	def := seedDef{Domain: "fleamarket", Nanoid: "k6p4x2n9", DID: "did:web:fleamarket.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "listing:vintage_camera", DisplayName: "Vintage Camera", Description: "Film camera listing"})
	def.DIDs = append(def.DIDs, seedDID{Path: "listing:vinyl_record", DisplayName: "Vinyl Record Collection", Description: "LP records"})
	def.DIDs = append(def.DIDs, seedDID{Path: "listing:antique_clock", DisplayName: "Antique Clock", Description: "Mechanical clock"})
	def.DIDs = append(def.DIDs, seedDID{Path: "listing:kimono_silk", DisplayName: "正絹着物", Description: "Silk kimono"})
	def.DIDs = append(def.DIDs, seedDID{Path: "listing:retro_game", DisplayName: "Retro Game Console", Description: "Classic gaming"})
	recslisting := seedCollection{Collection: "ai.gftd.apps.fleamarket.listing"}
	recslisting.Items = append(recslisting.Items, seedRecord{ID: "vintage_camera", Data: map[string]any{"id": "vintage_camera", "name": "Vintage Camera", "description": "Film camera listing", "status": "active"}})
	recslisting.Items = append(recslisting.Items, seedRecord{ID: "vinyl_record", Data: map[string]any{"id": "vinyl_record", "name": "Vinyl Record Collection", "description": "LP records", "status": "active"}})
	recslisting.Items = append(recslisting.Items, seedRecord{ID: "antique_clock", Data: map[string]any{"id": "antique_clock", "name": "Antique Clock", "description": "Mechanical clock", "status": "active"}})
	recslisting.Items = append(recslisting.Items, seedRecord{ID: "kimono_silk", Data: map[string]any{"id": "kimono_silk", "name": "正絹着物", "description": "Silk kimono", "status": "active"}})
	recslisting.Items = append(recslisting.Items, seedRecord{ID: "retro_game", Data: map[string]any{"id": "retro_game", "name": "Retro Game Console", "description": "Classic gaming", "status": "active"}})
	def.Records = append(def.Records, recslisting)
	return def
}

func FoodGapSeeds() seedDef {
	def := seedDef{Domain: "food", Nanoid: "fd7o8d3n", DID: "did:web:food.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "product:rice_koshihikari", DisplayName: "コシヒカリ", Description: "Japanese premium rice"})
	def.DIDs = append(def.DIDs, seedDID{Path: "product:wagyu_a5", DisplayName: "A5和牛", Description: "Japanese Wagyu beef"})
	def.DIDs = append(def.DIDs, seedDID{Path: "product:olive_oil_ev", DisplayName: "Extra Virgin Olive Oil", Description: "Italian EVOO"})
	def.DIDs = append(def.DIDs, seedDID{Path: "product:matcha_uji", DisplayName: "宇治抹茶", Description: "Uji matcha powder"})
	def.DIDs = append(def.DIDs, seedDID{Path: "product:parmigiano", DisplayName: "Parmigiano Reggiano", Description: "Italian cheese DOP"})
	def.DIDs = append(def.DIDs, seedDID{Path: "product:soy_sauce_kikkoman", DisplayName: "キッコーマン醤油", Description: "Soy sauce"})
	def.DIDs = append(def.DIDs, seedDID{Path: "product:baguette", DisplayName: "French Baguette", Description: "Traditional bread"})
	recsproduct := seedCollection{Collection: "ai.gftd.apps.food.product"}
	recsproduct.Items = append(recsproduct.Items, seedRecord{ID: "rice_koshihikari", Data: map[string]any{"id": "rice_koshihikari", "name": "コシヒカリ", "description": "Japanese premium rice", "status": "active"}})
	recsproduct.Items = append(recsproduct.Items, seedRecord{ID: "wagyu_a5", Data: map[string]any{"id": "wagyu_a5", "name": "A5和牛", "description": "Japanese Wagyu beef", "status": "active"}})
	recsproduct.Items = append(recsproduct.Items, seedRecord{ID: "olive_oil_ev", Data: map[string]any{"id": "olive_oil_ev", "name": "Extra Virgin Olive Oil", "description": "Italian EVOO", "status": "active"}})
	recsproduct.Items = append(recsproduct.Items, seedRecord{ID: "matcha_uji", Data: map[string]any{"id": "matcha_uji", "name": "宇治抹茶", "description": "Uji matcha powder", "status": "active"}})
	recsproduct.Items = append(recsproduct.Items, seedRecord{ID: "parmigiano", Data: map[string]any{"id": "parmigiano", "name": "Parmigiano Reggiano", "description": "Italian cheese DOP", "status": "active"}})
	recsproduct.Items = append(recsproduct.Items, seedRecord{ID: "soy_sauce_kikkoman", Data: map[string]any{"id": "soy_sauce_kikkoman", "name": "キッコーマン醤油", "description": "Soy sauce", "status": "active"}})
	recsproduct.Items = append(recsproduct.Items, seedRecord{ID: "baguette", Data: map[string]any{"id": "baguette", "name": "French Baguette", "description": "Traditional bread", "status": "active"}})
	def.Records = append(def.Records, recsproduct)
	return def
}

func FudosanGapSeeds() seedDef {
	def := seedDef{Domain: "fudosan", Nanoid: "fd4sn01", DID: "did:web:fudosan.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "agency:mitsui_re", DisplayName: "三井不動産リアルティ", Description: "Mitsui Fudosan Realty"})
	def.DIDs = append(def.DIDs, seedDID{Path: "agency:sumitomo_re", DisplayName: "住友不動産販売", Description: "Sumitomo Realty Sales"})
	def.DIDs = append(def.DIDs, seedDID{Path: "agency:tokyu_livable", DisplayName: "東急リバブル", Description: "Tokyu Livable"})
	def.DIDs = append(def.DIDs, seedDID{Path: "transaction:mansion_minato", DisplayName: "港区マンション売買", Description: "Minato-ku condo sale"})
	def.DIDs = append(def.DIDs, seedDID{Path: "agency:nomura_re", DisplayName: "野村不動産", Description: "Nomura Real Estate"})
	recsagency := seedCollection{Collection: "ai.gftd.apps.fudosan.agency"}
	recsagency.Items = append(recsagency.Items, seedRecord{ID: "mitsui_re", Data: map[string]any{"id": "mitsui_re", "name": "三井不動産リアルティ", "description": "Mitsui Fudosan Realty", "status": "active"}})
	recsagency.Items = append(recsagency.Items, seedRecord{ID: "sumitomo_re", Data: map[string]any{"id": "sumitomo_re", "name": "住友不動産販売", "description": "Sumitomo Realty Sales", "status": "active"}})
	recsagency.Items = append(recsagency.Items, seedRecord{ID: "tokyu_livable", Data: map[string]any{"id": "tokyu_livable", "name": "東急リバブル", "description": "Tokyu Livable", "status": "active"}})
	recsagency.Items = append(recsagency.Items, seedRecord{ID: "nomura_re", Data: map[string]any{"id": "nomura_re", "name": "野村不動産", "description": "Nomura Real Estate", "status": "active"}})
	def.Records = append(def.Records, recsagency)
	recstransaction := seedCollection{Collection: "ai.gftd.apps.fudosan.transaction"}
	recstransaction.Items = append(recstransaction.Items, seedRecord{ID: "mansion_minato", Data: map[string]any{"id": "mansion_minato", "name": "港区マンション売買", "description": "Minato-ku condo sale", "status": "active"}})
	def.Records = append(def.Records, recstransaction)
	return def
}

func GakurekiGapSeeds() seedDef {
	def := seedDef{Domain: "gakureki", Nanoid: "gakub5d6", DID: "did:web:gakureki.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "degree:bachelor_cs", DisplayName: "学士(情報科学)", Description: "Bachelor of CS"})
	def.DIDs = append(def.DIDs, seedDID{Path: "degree:master_eng", DisplayName: "修士(工学)", Description: "Master of Engineering"})
	def.DIDs = append(def.DIDs, seedDID{Path: "degree:phd_med", DisplayName: "博士(医学)", Description: "PhD Medicine"})
	def.DIDs = append(def.DIDs, seedDID{Path: "degree:mba", DisplayName: "MBA", Description: "Master of Business Administration"})
	def.DIDs = append(def.DIDs, seedDID{Path: "degree:jd", DisplayName: "法務博士", Description: "Juris Doctor"})
	recsdegree := seedCollection{Collection: "ai.gftd.apps.gakureki.degree"}
	recsdegree.Items = append(recsdegree.Items, seedRecord{ID: "bachelor_cs", Data: map[string]any{"id": "bachelor_cs", "name": "学士(情報科学)", "description": "Bachelor of CS", "status": "active"}})
	recsdegree.Items = append(recsdegree.Items, seedRecord{ID: "master_eng", Data: map[string]any{"id": "master_eng", "name": "修士(工学)", "description": "Master of Engineering", "status": "active"}})
	recsdegree.Items = append(recsdegree.Items, seedRecord{ID: "phd_med", Data: map[string]any{"id": "phd_med", "name": "博士(医学)", "description": "PhD Medicine", "status": "active"}})
	recsdegree.Items = append(recsdegree.Items, seedRecord{ID: "mba", Data: map[string]any{"id": "mba", "name": "MBA", "description": "Master of Business Administration", "status": "active"}})
	recsdegree.Items = append(recsdegree.Items, seedRecord{ID: "jd", Data: map[string]any{"id": "jd", "name": "法務博士", "description": "Juris Doctor", "status": "active"}})
	def.Records = append(def.Records, recsdegree)
	return def
}

func GasGapSeeds() seedDef {
	def := seedDef{Domain: "gas", Nanoid: "gs5a6s1m", DID: "did:web:gas.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "facility:tokyo_gas_main", DisplayName: "東京ガス根岸LNG", Description: "Negishi LNG terminal"})
	def.DIDs = append(def.DIDs, seedDID{Path: "facility:osaka_gas_senboku", DisplayName: "大阪ガス泉北", Description: "Senboku LNG terminal"})
	def.DIDs = append(def.DIDs, seedDID{Path: "facility:toho_gas_chita", DisplayName: "東邦ガス知多", Description: "Chita LNG terminal"})
	def.DIDs = append(def.DIDs, seedDID{Path: "facility:saibu_gas", DisplayName: "西部ガス", Description: "Saibu Gas facility"})
	def.DIDs = append(def.DIDs, seedDID{Path: "facility:shizuoka_gas", DisplayName: "静岡ガス", Description: "Shizuoka Gas facility"})
	recsfacility := seedCollection{Collection: "ai.gftd.apps.gas.facility"}
	recsfacility.Items = append(recsfacility.Items, seedRecord{ID: "tokyo_gas_main", Data: map[string]any{"id": "tokyo_gas_main", "name": "東京ガス根岸LNG", "description": "Negishi LNG terminal", "status": "active"}})
	recsfacility.Items = append(recsfacility.Items, seedRecord{ID: "osaka_gas_senboku", Data: map[string]any{"id": "osaka_gas_senboku", "name": "大阪ガス泉北", "description": "Senboku LNG terminal", "status": "active"}})
	recsfacility.Items = append(recsfacility.Items, seedRecord{ID: "toho_gas_chita", Data: map[string]any{"id": "toho_gas_chita", "name": "東邦ガス知多", "description": "Chita LNG terminal", "status": "active"}})
	recsfacility.Items = append(recsfacility.Items, seedRecord{ID: "saibu_gas", Data: map[string]any{"id": "saibu_gas", "name": "西部ガス", "description": "Saibu Gas facility", "status": "active"}})
	recsfacility.Items = append(recsfacility.Items, seedRecord{ID: "shizuoka_gas", Data: map[string]any{"id": "shizuoka_gas", "name": "静岡ガス", "description": "Shizuoka Gas facility", "status": "active"}})
	def.Records = append(def.Records, recsfacility)
	return def
}

func GasStationGapSeeds() seedDef {
	def := seedDef{Domain: "gas-station", Nanoid: "gs4tn01", DID: "did:web:gas-station.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "station:eneos_shinjuku", DisplayName: "ENEOS新宿", Description: "ENEOS gas station"})
	def.DIDs = append(def.DIDs, seedDID{Path: "station:shell_roppongi", DisplayName: "Shell六本木", Description: "Shell station"})
	def.DIDs = append(def.DIDs, seedDID{Path: "station:idemitsu_shibuya", DisplayName: "出光渋谷", Description: "Idemitsu station"})
	def.DIDs = append(def.DIDs, seedDID{Path: "station:cosmo_ikebukuro", DisplayName: "コスモ池袋", Description: "Cosmo Oil station"})
	def.DIDs = append(def.DIDs, seedDID{Path: "station:apollo_ueno", DisplayName: "apollostation上野", Description: "Apollo station"})
	recsstation := seedCollection{Collection: "ai.gftd.apps.gasstation.station"}
	recsstation.Items = append(recsstation.Items, seedRecord{ID: "eneos_shinjuku", Data: map[string]any{"id": "eneos_shinjuku", "name": "ENEOS新宿", "description": "ENEOS gas station", "status": "active"}})
	recsstation.Items = append(recsstation.Items, seedRecord{ID: "shell_roppongi", Data: map[string]any{"id": "shell_roppongi", "name": "Shell六本木", "description": "Shell station", "status": "active"}})
	recsstation.Items = append(recsstation.Items, seedRecord{ID: "idemitsu_shibuya", Data: map[string]any{"id": "idemitsu_shibuya", "name": "出光渋谷", "description": "Idemitsu station", "status": "active"}})
	recsstation.Items = append(recsstation.Items, seedRecord{ID: "cosmo_ikebukuro", Data: map[string]any{"id": "cosmo_ikebukuro", "name": "コスモ池袋", "description": "Cosmo Oil station", "status": "active"}})
	recsstation.Items = append(recsstation.Items, seedRecord{ID: "apollo_ueno", Data: map[string]any{"id": "apollo_ueno", "name": "apollostation上野", "description": "Apollo station", "status": "active"}})
	def.Records = append(def.Records, recsstation)
	return def
}

func GenomeGapSeeds() seedDef {
	def := seedDef{Domain: "genome", Nanoid: "gn4me01", DID: "did:web:genome.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "genome:human_grch38", DisplayName: "Human GRCh38", Description: "Human reference genome"})
	def.DIDs = append(def.DIDs, seedDID{Path: "genome:mouse_grcm39", DisplayName: "Mouse GRCm39", Description: "Mouse reference genome"})
	def.DIDs = append(def.DIDs, seedDID{Path: "genome:rice_irgsp", DisplayName: "Rice IRGSP-1.0", Description: "Oryza sativa genome"})
	def.DIDs = append(def.DIDs, seedDID{Path: "protein:p53_human", DisplayName: "TP53 Human", Description: "Tumor suppressor protein"})
	def.DIDs = append(def.DIDs, seedDID{Path: "genome:ecoli_k12", DisplayName: "E. coli K-12", Description: "Bacterial reference genome"})
	recsgenome := seedCollection{Collection: "ai.gftd.apps.genome.genome"}
	recsgenome.Items = append(recsgenome.Items, seedRecord{ID: "human_grch38", Data: map[string]any{"id": "human_grch38", "name": "Human GRCh38", "description": "Human reference genome", "status": "active"}})
	recsgenome.Items = append(recsgenome.Items, seedRecord{ID: "mouse_grcm39", Data: map[string]any{"id": "mouse_grcm39", "name": "Mouse GRCm39", "description": "Mouse reference genome", "status": "active"}})
	recsgenome.Items = append(recsgenome.Items, seedRecord{ID: "rice_irgsp", Data: map[string]any{"id": "rice_irgsp", "name": "Rice IRGSP-1.0", "description": "Oryza sativa genome", "status": "active"}})
	recsgenome.Items = append(recsgenome.Items, seedRecord{ID: "ecoli_k12", Data: map[string]any{"id": "ecoli_k12", "name": "E. coli K-12", "description": "Bacterial reference genome", "status": "active"}})
	def.Records = append(def.Records, recsgenome)
	recsprotein := seedCollection{Collection: "ai.gftd.apps.genome.protein"}
	recsprotein.Items = append(recsprotein.Items, seedRecord{ID: "p53_human", Data: map[string]any{"id": "p53_human", "name": "TP53 Human", "description": "Tumor suppressor protein", "status": "active"}})
	def.Records = append(def.Records, recsprotein)
	return def
}

func GovGapSeeds() seedDef {
	def := seedDef{Domain: "gov", Nanoid: "gv7ps2m1", DID: "did:web:gov.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "agency:mof_jp", DisplayName: "財務省", Description: "Ministry of Finance Japan"})
	def.DIDs = append(def.DIDs, seedDID{Path: "agency:meti_jp", DisplayName: "経済産業省", Description: "METI Japan"})
	def.DIDs = append(def.DIDs, seedDID{Path: "agency:mhlw_jp", DisplayName: "厚生労働省", Description: "MHLW Japan"})
	def.DIDs = append(def.DIDs, seedDID{Path: "agency:mlit_jp", DisplayName: "国土交通省", Description: "MLIT Japan"})
	def.DIDs = append(def.DIDs, seedDID{Path: "agency:irs_us", DisplayName: "IRS", Description: "US Internal Revenue Service"})
	def.DIDs = append(def.DIDs, seedDID{Path: "agency:hmrc_uk", DisplayName: "HMRC", Description: "UK tax authority"})
	recsagency := seedCollection{Collection: "ai.gftd.apps.gov.legal_entity"}
	recsagency.Items = append(recsagency.Items, seedRecord{ID: "mof_jp", Data: map[string]any{"id": "mof_jp", "name": "財務省", "description": "Ministry of Finance Japan", "status": "active"}})
	recsagency.Items = append(recsagency.Items, seedRecord{ID: "meti_jp", Data: map[string]any{"id": "meti_jp", "name": "経済産業省", "description": "METI Japan", "status": "active"}})
	recsagency.Items = append(recsagency.Items, seedRecord{ID: "mhlw_jp", Data: map[string]any{"id": "mhlw_jp", "name": "厚生労働省", "description": "MHLW Japan", "status": "active"}})
	recsagency.Items = append(recsagency.Items, seedRecord{ID: "mlit_jp", Data: map[string]any{"id": "mlit_jp", "name": "国土交通省", "description": "MLIT Japan", "status": "active"}})
	recsagency.Items = append(recsagency.Items, seedRecord{ID: "irs_us", Data: map[string]any{"id": "irs_us", "name": "IRS", "description": "US Internal Revenue Service", "status": "active"}})
	recsagency.Items = append(recsagency.Items, seedRecord{ID: "hmrc_uk", Data: map[string]any{"id": "hmrc_uk", "name": "HMRC", "description": "UK tax authority", "status": "active"}})
	def.Records = append(def.Records, recsagency)
	return def
}

func GtinGapSeeds() seedDef {
	def := seedDef{Domain: "gtin", Nanoid: "gt1n4k7m", DID: "did:web:gtin.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "product:coca_cola_500", DisplayName: "コカ・コーラ 500ml", Description: "4902102139496"})
	def.DIDs = append(def.DIDs, seedDID{Path: "product:pocky_choco", DisplayName: "ポッキーチョコレート", Description: "4902777394008"})
	def.DIDs = append(def.DIDs, seedDID{Path: "product:cup_noodle", DisplayName: "カップヌードル", Description: "4902105002100"})
	def.DIDs = append(def.DIDs, seedDID{Path: "product:iphone_15", DisplayName: "iPhone 15", Description: "0194253396062"})
	def.DIDs = append(def.DIDs, seedDID{Path: "product:kitkat_mini", DisplayName: "キットカット ミニ", Description: "4902201178945"})
	recsproduct := seedCollection{Collection: "ai.gftd.apps.gtin.product"}
	recsproduct.Items = append(recsproduct.Items, seedRecord{ID: "coca_cola_500", Data: map[string]any{"id": "coca_cola_500", "name": "コカ・コーラ 500ml", "description": "4902102139496", "status": "active"}})
	recsproduct.Items = append(recsproduct.Items, seedRecord{ID: "pocky_choco", Data: map[string]any{"id": "pocky_choco", "name": "ポッキーチョコレート", "description": "4902777394008", "status": "active"}})
	recsproduct.Items = append(recsproduct.Items, seedRecord{ID: "cup_noodle", Data: map[string]any{"id": "cup_noodle", "name": "カップヌードル", "description": "4902105002100", "status": "active"}})
	recsproduct.Items = append(recsproduct.Items, seedRecord{ID: "iphone_15", Data: map[string]any{"id": "iphone_15", "name": "iPhone 15", "description": "0194253396062", "status": "active"}})
	recsproduct.Items = append(recsproduct.Items, seedRecord{ID: "kitkat_mini", Data: map[string]any{"id": "kitkat_mini", "name": "キットカット ミニ", "description": "4902201178945", "status": "active"}})
	def.Records = append(def.Records, recsproduct)
	return def
}

func HaikibutsuGapSeeds() seedDef {
	def := seedDef{Domain: "haikibutsu", Nanoid: "hkbt5u01", DID: "did:web:haikibutsu.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "manifest:tokyo_ind_001", DisplayName: "東京産廃マニフェスト001", Description: "Industrial waste manifest"})
	def.DIDs = append(def.DIDs, seedDID{Path: "route:setagaya_burnable", DisplayName: "世田谷区可燃ゴミ", Description: "Burnable waste route"})
	def.DIDs = append(def.DIDs, seedDID{Path: "point:shibuya_st_recycle", DisplayName: "渋谷駅リサイクルステーション", Description: "Recycling collection point"})
	def.DIDs = append(def.DIDs, seedDID{Path: "plant:koto_incineration", DisplayName: "江東清掃工場", Description: "Waste incineration plant"})
	def.DIDs = append(def.DIDs, seedDID{Path: "site:illegal_dump_01", DisplayName: "不法投棄サイト01", Description: "Illegal dump site"})
	def.DIDs = append(def.DIDs, seedDID{Path: "vehicle:waste_truck_01", DisplayName: "収集車01", Description: "Waste collection vehicle"})
	def.DIDs = append(def.DIDs, seedDID{Path: "ton:industrial_2024", DisplayName: "2024年度産業廃棄物", Description: "Annual industrial waste"})
	def.DIDs = append(def.DIDs, seedDID{Path: "container:nuclear_dry_01", DisplayName: "乾式キャスク01", Description: "Nuclear dry cask"})
	def.DIDs = append(def.DIDs, seedDID{Path: "site:landfill_chiba", DisplayName: "千葉最終処分場", Description: "Chiba landfill site"})
	def.DIDs = append(def.DIDs, seedDID{Path: "vessel:ship_recycle_01", DisplayName: "船舶解体01", Description: "Ship recycling"})
	def.DIDs = append(def.DIDs, seedDID{Path: "project:demolition_01", DisplayName: "解体工事01", Description: "Demolition project"})
	recsmanifest := seedCollection{Collection: "ai.gftd.apps.haikibutsu.manifest"}
	recsmanifest.Items = append(recsmanifest.Items, seedRecord{ID: "tokyo_ind_001", Data: map[string]any{"id": "tokyo_ind_001", "name": "東京産廃マニフェスト001", "description": "Industrial waste manifest", "status": "active"}})
	def.Records = append(def.Records, recsmanifest)
	recsroute := seedCollection{Collection: "ai.gftd.apps.haikibutsu.route"}
	recsroute.Items = append(recsroute.Items, seedRecord{ID: "setagaya_burnable", Data: map[string]any{"id": "setagaya_burnable", "name": "世田谷区可燃ゴミ", "description": "Burnable waste route", "status": "active"}})
	def.Records = append(def.Records, recsroute)
	recspoint := seedCollection{Collection: "ai.gftd.apps.haikibutsu.point"}
	recspoint.Items = append(recspoint.Items, seedRecord{ID: "shibuya_st_recycle", Data: map[string]any{"id": "shibuya_st_recycle", "name": "渋谷駅リサイクルステーション", "description": "Recycling collection point", "status": "active"}})
	def.Records = append(def.Records, recspoint)
	recsplant := seedCollection{Collection: "ai.gftd.apps.haikibutsu.plant"}
	recsplant.Items = append(recsplant.Items, seedRecord{ID: "koto_incineration", Data: map[string]any{"id": "koto_incineration", "name": "江東清掃工場", "description": "Waste incineration plant", "status": "active"}})
	def.Records = append(def.Records, recsplant)
	recssite := seedCollection{Collection: "ai.gftd.apps.haikibutsu.site"}
	recssite.Items = append(recssite.Items, seedRecord{ID: "illegal_dump_01", Data: map[string]any{"id": "illegal_dump_01", "name": "不法投棄サイト01", "description": "Illegal dump site", "status": "active"}})
	recssite.Items = append(recssite.Items, seedRecord{ID: "landfill_chiba", Data: map[string]any{"id": "landfill_chiba", "name": "千葉最終処分場", "description": "Chiba landfill site", "status": "active"}})
	def.Records = append(def.Records, recssite)
	recsvehicle := seedCollection{Collection: "ai.gftd.apps.haikibutsu.vehicle"}
	recsvehicle.Items = append(recsvehicle.Items, seedRecord{ID: "waste_truck_01", Data: map[string]any{"id": "waste_truck_01", "name": "収集車01", "description": "Waste collection vehicle", "status": "active"}})
	def.Records = append(def.Records, recsvehicle)
	recston := seedCollection{Collection: "ai.gftd.apps.haikibutsu.ton"}
	recston.Items = append(recston.Items, seedRecord{ID: "industrial_2024", Data: map[string]any{"id": "industrial_2024", "name": "2024年度産業廃棄物", "description": "Annual industrial waste", "status": "active"}})
	def.Records = append(def.Records, recston)
	recscontainer := seedCollection{Collection: "ai.gftd.apps.haikibutsu.container"}
	recscontainer.Items = append(recscontainer.Items, seedRecord{ID: "nuclear_dry_01", Data: map[string]any{"id": "nuclear_dry_01", "name": "乾式キャスク01", "description": "Nuclear dry cask", "status": "active"}})
	def.Records = append(def.Records, recscontainer)
	recsvessel := seedCollection{Collection: "ai.gftd.apps.haikibutsu.vessel"}
	recsvessel.Items = append(recsvessel.Items, seedRecord{ID: "ship_recycle_01", Data: map[string]any{"id": "ship_recycle_01", "name": "船舶解体01", "description": "Ship recycling", "status": "active"}})
	def.Records = append(def.Records, recsvessel)
	recsproject := seedCollection{Collection: "ai.gftd.apps.haikibutsu.project"}
	recsproject.Items = append(recsproject.Items, seedRecord{ID: "demolition_01", Data: map[string]any{"id": "demolition_01", "name": "解体工事01", "description": "Demolition project", "status": "active"}})
	def.Records = append(def.Records, recsproject)
	return def
}

func HakubutsukanGapSeeds() seedDef {
	def := seedDef{Domain: "hakubutsukan", Nanoid: "hk4bt01", DID: "did:web:hakubutsukan.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "museum:tokyo_national", DisplayName: "東京国立博物館", Description: "Tokyo National Museum"})
	def.DIDs = append(def.DIDs, seedDID{Path: "museum:louvre", DisplayName: "Louvre Museum", Description: "Paris, France"})
	def.DIDs = append(def.DIDs, seedDID{Path: "museum:british", DisplayName: "British Museum", Description: "London, UK"})
	def.DIDs = append(def.DIDs, seedDID{Path: "museum:smithsonian", DisplayName: "Smithsonian", Description: "Washington DC, USA"})
	def.DIDs = append(def.DIDs, seedDID{Path: "museum:故宮", DisplayName: "National Palace Museum", Description: "Taipei, Taiwan"})
	def.DIDs = append(def.DIDs, seedDID{Path: "museum:hermitage", DisplayName: "Hermitage Museum", Description: "Saint Petersburg, Russia"})
	recsmuseum := seedCollection{Collection: "ai.gftd.apps.hakubutsukan.museum"}
	recsmuseum.Items = append(recsmuseum.Items, seedRecord{ID: "tokyo_national", Data: map[string]any{"id": "tokyo_national", "name": "東京国立博物館", "description": "Tokyo National Museum", "status": "active"}})
	recsmuseum.Items = append(recsmuseum.Items, seedRecord{ID: "louvre", Data: map[string]any{"id": "louvre", "name": "Louvre Museum", "description": "Paris, France", "status": "active"}})
	recsmuseum.Items = append(recsmuseum.Items, seedRecord{ID: "british", Data: map[string]any{"id": "british", "name": "British Museum", "description": "London, UK", "status": "active"}})
	recsmuseum.Items = append(recsmuseum.Items, seedRecord{ID: "smithsonian", Data: map[string]any{"id": "smithsonian", "name": "Smithsonian", "description": "Washington DC, USA", "status": "active"}})
	recsmuseum.Items = append(recsmuseum.Items, seedRecord{ID: "故宮", Data: map[string]any{"id": "故宮", "name": "National Palace Museum", "description": "Taipei, Taiwan", "status": "active"}})
	recsmuseum.Items = append(recsmuseum.Items, seedRecord{ID: "hermitage", Data: map[string]any{"id": "hermitage", "name": "Hermitage Museum", "description": "Saint Petersburg, Russia", "status": "active"}})
	def.Records = append(def.Records, recsmuseum)
	return def
}

func HanzaiGapSeeds() seedDef {
	def := seedDef{Domain: "hanzai", Nanoid: "hz4ai01", DID: "did:web:hanzai.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "crime:fraud", DisplayName: "詐欺", Description: "Fraud"})
	def.DIDs = append(def.DIDs, seedDID{Path: "crime:theft", DisplayName: "窃盗", Description: "Theft"})
	def.DIDs = append(def.DIDs, seedDID{Path: "crime:assault", DisplayName: "暴行", Description: "Assault"})
	def.DIDs = append(def.DIDs, seedDID{Path: "crime:dui", DisplayName: "飲酒運転", Description: "Driving under influence"})
	def.DIDs = append(def.DIDs, seedDID{Path: "crime:cybercrime", DisplayName: "サイバー犯罪", Description: "Cybercrime"})
	recscrime := seedCollection{Collection: "ai.gftd.apps.hanzai.crime"}
	recscrime.Items = append(recscrime.Items, seedRecord{ID: "fraud", Data: map[string]any{"id": "fraud", "name": "詐欺", "description": "Fraud", "status": "active"}})
	recscrime.Items = append(recscrime.Items, seedRecord{ID: "theft", Data: map[string]any{"id": "theft", "name": "窃盗", "description": "Theft", "status": "active"}})
	recscrime.Items = append(recscrime.Items, seedRecord{ID: "assault", Data: map[string]any{"id": "assault", "name": "暴行", "description": "Assault", "status": "active"}})
	recscrime.Items = append(recscrime.Items, seedRecord{ID: "dui", Data: map[string]any{"id": "dui", "name": "飲酒運転", "description": "Driving under influence", "status": "active"}})
	recscrime.Items = append(recscrime.Items, seedRecord{ID: "cybercrime", Data: map[string]any{"id": "cybercrime", "name": "サイバー犯罪", "description": "Cybercrime", "status": "active"}})
	def.Records = append(def.Records, recscrime)
	return def
}

func HinshuGapSeeds() seedDef {
	def := seedDef{Domain: "hinshu", Nanoid: "hins0801", DID: "did:web:hinshu.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "variety:koshihikari", DisplayName: "コシヒカリ", Description: "Rice cultivar"})
	def.DIDs = append(def.DIDs, seedDID{Path: "variety:fuji_apple", DisplayName: "ふじ", Description: "Apple cultivar"})
	def.DIDs = append(def.DIDs, seedDID{Path: "variety:shine_muscat", DisplayName: "シャインマスカット", Description: "Grape cultivar"})
	def.DIDs = append(def.DIDs, seedDID{Path: "variety:tochiotome", DisplayName: "とちおとめ", Description: "Strawberry cultivar"})
	def.DIDs = append(def.DIDs, seedDID{Path: "variety:yubari_melon", DisplayName: "夕張メロン", Description: "Melon cultivar"})
	recsvariety := seedCollection{Collection: "ai.gftd.apps.hinshu.variety"}
	recsvariety.Items = append(recsvariety.Items, seedRecord{ID: "koshihikari", Data: map[string]any{"id": "koshihikari", "name": "コシヒカリ", "description": "Rice cultivar", "status": "active"}})
	recsvariety.Items = append(recsvariety.Items, seedRecord{ID: "fuji_apple", Data: map[string]any{"id": "fuji_apple", "name": "ふじ", "description": "Apple cultivar", "status": "active"}})
	recsvariety.Items = append(recsvariety.Items, seedRecord{ID: "shine_muscat", Data: map[string]any{"id": "shine_muscat", "name": "シャインマスカット", "description": "Grape cultivar", "status": "active"}})
	recsvariety.Items = append(recsvariety.Items, seedRecord{ID: "tochiotome", Data: map[string]any{"id": "tochiotome", "name": "とちおとめ", "description": "Strawberry cultivar", "status": "active"}})
	recsvariety.Items = append(recsvariety.Items, seedRecord{ID: "yubari_melon", Data: map[string]any{"id": "yubari_melon", "name": "夕張メロン", "description": "Melon cultivar", "status": "active"}})
	def.Records = append(def.Records, recsvariety)
	return def
}

func HoureiGapSeeds() seedDef {
	def := seedDef{Domain: "hourei", Nanoid: "hr4ei01", DID: "did:web:hourei.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "statute:kenpo", DisplayName: "日本国憲法", Description: "Constitution of Japan"})
	def.DIDs = append(def.DIDs, seedDID{Path: "statute:minpo", DisplayName: "民法", Description: "Civil Code of Japan"})
	def.DIDs = append(def.DIDs, seedDID{Path: "statute:keiho", DisplayName: "刑法", Description: "Penal Code of Japan"})
	def.DIDs = append(def.DIDs, seedDID{Path: "statute:shoho", DisplayName: "商法", Description: "Commercial Code of Japan"})
	def.DIDs = append(def.DIDs, seedDID{Path: "statute:kaishaho", DisplayName: "会社法", Description: "Companies Act of Japan"})
	def.DIDs = append(def.DIDs, seedDID{Path: "statute:usc_title26", DisplayName: "US Internal Revenue Code", Description: "US tax law"})
	recsstatute := seedCollection{Collection: "ai.gftd.apps.hourei.statute"}
	recsstatute.Items = append(recsstatute.Items, seedRecord{ID: "kenpo", Data: map[string]any{"id": "kenpo", "name": "日本国憲法", "description": "Constitution of Japan", "status": "active"}})
	recsstatute.Items = append(recsstatute.Items, seedRecord{ID: "minpo", Data: map[string]any{"id": "minpo", "name": "民法", "description": "Civil Code of Japan", "status": "active"}})
	recsstatute.Items = append(recsstatute.Items, seedRecord{ID: "keiho", Data: map[string]any{"id": "keiho", "name": "刑法", "description": "Penal Code of Japan", "status": "active"}})
	recsstatute.Items = append(recsstatute.Items, seedRecord{ID: "shoho", Data: map[string]any{"id": "shoho", "name": "商法", "description": "Commercial Code of Japan", "status": "active"}})
	recsstatute.Items = append(recsstatute.Items, seedRecord{ID: "kaishaho", Data: map[string]any{"id": "kaishaho", "name": "会社法", "description": "Companies Act of Japan", "status": "active"}})
	recsstatute.Items = append(recsstatute.Items, seedRecord{ID: "usc_title26", Data: map[string]any{"id": "usc_title26", "name": "US Internal Revenue Code", "description": "US tax law", "status": "active"}})
	def.Records = append(def.Records, recsstatute)
	return def
}

func IndustryStandardGapSeeds() seedDef {
	def := seedDef{Domain: "industry-standard", Nanoid: "indstd01", DID: "did:web:industry-standard.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "standard:iso_9001", DisplayName: "ISO 9001", Description: "Quality management"})
	def.DIDs = append(def.DIDs, seedDID{Path: "standard:iso_27001", DisplayName: "ISO 27001", Description: "Information security"})
	def.DIDs = append(def.DIDs, seedDID{Path: "standard:iso_14001", DisplayName: "ISO 14001", Description: "Environmental management"})
	def.DIDs = append(def.DIDs, seedDID{Path: "standard:pci_dss", DisplayName: "PCI DSS v4.0", Description: "Payment card security"})
	def.DIDs = append(def.DIDs, seedDID{Path: "standard:soc2", DisplayName: "SOC 2 Type II", Description: "Service organization controls"})
	recsstandard := seedCollection{Collection: "ai.gftd.apps.industrystandard.standard"}
	recsstandard.Items = append(recsstandard.Items, seedRecord{ID: "iso_9001", Data: map[string]any{"id": "iso_9001", "name": "ISO 9001", "description": "Quality management", "status": "active"}})
	recsstandard.Items = append(recsstandard.Items, seedRecord{ID: "iso_27001", Data: map[string]any{"id": "iso_27001", "name": "ISO 27001", "description": "Information security", "status": "active"}})
	recsstandard.Items = append(recsstandard.Items, seedRecord{ID: "iso_14001", Data: map[string]any{"id": "iso_14001", "name": "ISO 14001", "description": "Environmental management", "status": "active"}})
	recsstandard.Items = append(recsstandard.Items, seedRecord{ID: "pci_dss", Data: map[string]any{"id": "pci_dss", "name": "PCI DSS v4.0", "description": "Payment card security", "status": "active"}})
	recsstandard.Items = append(recsstandard.Items, seedRecord{ID: "soc2", Data: map[string]any{"id": "soc2", "name": "SOC 2 Type II", "description": "Service organization controls", "status": "active"}})
	def.Records = append(def.Records, recsstandard)
	return def
}

func InsuranceGapSeeds() seedDef {
	def := seedDef{Domain: "insurance", Nanoid: "in2rl7bg", DID: "did:web:insurance.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "insurer:tokio_marine", DisplayName: "東京海上日動", Description: "Tokio Marine Japan"})
	def.DIDs = append(def.DIDs, seedDID{Path: "insurer:sompo", DisplayName: "損保ジャパン", Description: "Sompo Japan"})
	def.DIDs = append(def.DIDs, seedDID{Path: "insurer:mitsui_sumitomo", DisplayName: "三井住友海上", Description: "MS&AD Japan"})
	def.DIDs = append(def.DIDs, seedDID{Path: "insurer:allianz", DisplayName: "Allianz", Description: "Germany"})
	def.DIDs = append(def.DIDs, seedDID{Path: "insurer:axa", DisplayName: "AXA", Description: "France"})
	def.DIDs = append(def.DIDs, seedDID{Path: "insurer:zurich", DisplayName: "Zurich Insurance", Description: "Switzerland"})
	def.DIDs = append(def.DIDs, seedDID{Path: "insurer:lloyds", DisplayName: "Lloyd's of London", Description: "UK"})
	def.DIDs = append(def.DIDs, seedDID{Path: "policy:auto_std", DisplayName: "自動車保険", Description: "Standard auto insurance"})
	recsinsurer := seedCollection{Collection: "ai.gftd.apps.insurance.insurer"}
	recsinsurer.Items = append(recsinsurer.Items, seedRecord{ID: "tokio_marine", Data: map[string]any{"id": "tokio_marine", "name": "東京海上日動", "description": "Tokio Marine Japan", "status": "active"}})
	recsinsurer.Items = append(recsinsurer.Items, seedRecord{ID: "sompo", Data: map[string]any{"id": "sompo", "name": "損保ジャパン", "description": "Sompo Japan", "status": "active"}})
	recsinsurer.Items = append(recsinsurer.Items, seedRecord{ID: "mitsui_sumitomo", Data: map[string]any{"id": "mitsui_sumitomo", "name": "三井住友海上", "description": "MS&AD Japan", "status": "active"}})
	recsinsurer.Items = append(recsinsurer.Items, seedRecord{ID: "allianz", Data: map[string]any{"id": "allianz", "name": "Allianz", "description": "Germany", "status": "active"}})
	recsinsurer.Items = append(recsinsurer.Items, seedRecord{ID: "axa", Data: map[string]any{"id": "axa", "name": "AXA", "description": "France", "status": "active"}})
	recsinsurer.Items = append(recsinsurer.Items, seedRecord{ID: "zurich", Data: map[string]any{"id": "zurich", "name": "Zurich Insurance", "description": "Switzerland", "status": "active"}})
	recsinsurer.Items = append(recsinsurer.Items, seedRecord{ID: "lloyds", Data: map[string]any{"id": "lloyds", "name": "Lloyd's of London", "description": "UK", "status": "active"}})
	def.Records = append(def.Records, recsinsurer)
	recspolicy := seedCollection{Collection: "ai.gftd.apps.insurance.policy"}
	recspolicy.Items = append(recspolicy.Items, seedRecord{ID: "auto_std", Data: map[string]any{"id": "auto_std", "name": "自動車保険", "description": "Standard auto insurance", "status": "active"}})
	def.Records = append(def.Records, recspolicy)
	return def
}

func InvoiceGapSeeds() seedDef {
	def := seedDef{Domain: "invoice", Nanoid: "iv4ce01", DID: "did:web:invoice.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "invoice:inv_001", DisplayName: "請求書001", Description: "Standard invoice"})
	def.DIDs = append(def.DIDs, seedDID{Path: "invoice:inv_credit", DisplayName: "クレジットノート", Description: "Credit note"})
	def.DIDs = append(def.DIDs, seedDID{Path: "invoice:inv_proforma", DisplayName: "プロフォーマ請求書", Description: "Proforma invoice"})
	def.DIDs = append(def.DIDs, seedDID{Path: "invoice:inv_recurring", DisplayName: "定期請求書", Description: "Recurring invoice"})
	def.DIDs = append(def.DIDs, seedDID{Path: "invoice:inv_einvoice", DisplayName: "電子インボイス", Description: "e-Invoice (JP qualified)"})
	recsinvoice := seedCollection{Collection: "ai.gftd.apps.invoice.invoice"}
	recsinvoice.Items = append(recsinvoice.Items, seedRecord{ID: "inv_001", Data: map[string]any{"id": "inv_001", "name": "請求書001", "description": "Standard invoice", "status": "active"}})
	recsinvoice.Items = append(recsinvoice.Items, seedRecord{ID: "inv_credit", Data: map[string]any{"id": "inv_credit", "name": "クレジットノート", "description": "Credit note", "status": "active"}})
	recsinvoice.Items = append(recsinvoice.Items, seedRecord{ID: "inv_proforma", Data: map[string]any{"id": "inv_proforma", "name": "プロフォーマ請求書", "description": "Proforma invoice", "status": "active"}})
	recsinvoice.Items = append(recsinvoice.Items, seedRecord{ID: "inv_recurring", Data: map[string]any{"id": "inv_recurring", "name": "定期請求書", "description": "Recurring invoice", "status": "active"}})
	recsinvoice.Items = append(recsinvoice.Items, seedRecord{ID: "inv_einvoice", Data: map[string]any{"id": "inv_einvoice", "name": "電子インボイス", "description": "e-Invoice (JP qualified)", "status": "active"}})
	def.Records = append(def.Records, recsinvoice)
	return def
}

func IotGapSeeds() seedDef {
	def := seedDef{Domain: "iot", Nanoid: "iot3c0a", DID: "did:web:iot.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "device:temp_sensor", DisplayName: "Temperature Sensor", Description: "IoT temperature probe"})
	def.DIDs = append(def.DIDs, seedDID{Path: "device:smart_meter", DisplayName: "Smart Meter", Description: "Electric smart meter"})
	def.DIDs = append(def.DIDs, seedDID{Path: "device:security_cam", DisplayName: "Security Camera", Description: "IP surveillance camera"})
	def.DIDs = append(def.DIDs, seedDID{Path: "device:hvac_ctrl", DisplayName: "HVAC Controller", Description: "Building automation"})
	def.DIDs = append(def.DIDs, seedDID{Path: "device:water_sensor", DisplayName: "Water Level Sensor", Description: "Flood monitoring"})
	recsdevice := seedCollection{Collection: "ai.gftd.apps.iot.device"}
	recsdevice.Items = append(recsdevice.Items, seedRecord{ID: "temp_sensor", Data: map[string]any{"id": "temp_sensor", "name": "Temperature Sensor", "description": "IoT temperature probe", "status": "active"}})
	recsdevice.Items = append(recsdevice.Items, seedRecord{ID: "smart_meter", Data: map[string]any{"id": "smart_meter", "name": "Smart Meter", "description": "Electric smart meter", "status": "active"}})
	recsdevice.Items = append(recsdevice.Items, seedRecord{ID: "security_cam", Data: map[string]any{"id": "security_cam", "name": "Security Camera", "description": "IP surveillance camera", "status": "active"}})
	recsdevice.Items = append(recsdevice.Items, seedRecord{ID: "hvac_ctrl", Data: map[string]any{"id": "hvac_ctrl", "name": "HVAC Controller", "description": "Building automation", "status": "active"}})
	recsdevice.Items = append(recsdevice.Items, seedRecord{ID: "water_sensor", Data: map[string]any{"id": "water_sensor", "name": "Water Level Sensor", "description": "Flood monitoring", "status": "active"}})
	def.Records = append(def.Records, recsdevice)
	return def
}

func IpaddressGapSeeds() seedDef {
	def := seedDef{Domain: "ipaddress", Nanoid: "n7w1p4d0", DID: "did:web:ipaddress.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "ip:cloudflare_1111", DisplayName: "1.1.1.1", Description: "Cloudflare DNS resolver"})
	def.DIDs = append(def.DIDs, seedDID{Path: "ip:google_8888", DisplayName: "8.8.8.8", Description: "Google DNS resolver"})
	def.DIDs = append(def.DIDs, seedDID{Path: "ipv6:google_dns", DisplayName: "2001:4860:4860::8888", Description: "Google DNS IPv6"})
	def.DIDs = append(def.DIDs, seedDID{Path: "scan_result:port_scan_01", DisplayName: "Port Scan Result 01", Description: "Nmap scan result"})
	recsip := seedCollection{Collection: "ai.gftd.apps.ipaddress.ip"}
	recsip.Items = append(recsip.Items, seedRecord{ID: "cloudflare_1111", Data: map[string]any{"id": "cloudflare_1111", "name": "1.1.1.1", "description": "Cloudflare DNS resolver", "status": "active"}})
	recsip.Items = append(recsip.Items, seedRecord{ID: "google_8888", Data: map[string]any{"id": "google_8888", "name": "8.8.8.8", "description": "Google DNS resolver", "status": "active"}})
	def.Records = append(def.Records, recsip)
	recsipv6 := seedCollection{Collection: "ai.gftd.apps.ipaddress.ipv6"}
	recsipv6.Items = append(recsipv6.Items, seedRecord{ID: "google_dns", Data: map[string]any{"id": "google_dns", "name": "2001:4860:4860::8888", "description": "Google DNS IPv6", "status": "active"}})
	def.Records = append(def.Records, recsipv6)
	recsscan_result := seedCollection{Collection: "ai.gftd.apps.ipaddress.scan_result"}
	recsscan_result.Items = append(recsscan_result.Items, seedRecord{ID: "port_scan_01", Data: map[string]any{"id": "port_scan_01", "name": "Port Scan Result 01", "description": "Nmap scan result", "status": "active"}})
	def.Records = append(def.Records, recsscan_result)
	return def
}

func IryoGapSeeds() seedDef {
	def := seedDef{Domain: "iryo", Nanoid: "ir4md01", DID: "did:web:iryo.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "facility:tokyo_univ_hosp", DisplayName: "東京大学医学部附属病院", Description: "Tokyo University Hospital"})
	def.DIDs = append(def.DIDs, seedDID{Path: "facility:keio_hosp", DisplayName: "慶應義塾大学病院", Description: "Keio University Hospital"})
	def.DIDs = append(def.DIDs, seedDID{Path: "disease:icd_j06", DisplayName: "急性上気道感染症", Description: "ICD J06 Acute URI"})
	def.DIDs = append(def.DIDs, seedDID{Path: "disease:icd_e11", DisplayName: "2型糖尿病", Description: "ICD E11 Type 2 DM"})
	def.DIDs = append(def.DIDs, seedDID{Path: "trial:covid_vaccine_01", DisplayName: "COVID-19ワクチン治験", Description: "Vaccine clinical trial"})
	def.DIDs = append(def.DIDs, seedDID{Path: "claim:iryo_seikyu_001", DisplayName: "医療費請求001", Description: "Medical claim"})
	def.DIDs = append(def.DIDs, seedDID{Path: "prescription:rx_001", DisplayName: "処方箋001", Description: "Prescription"})
	def.DIDs = append(def.DIDs, seedDID{Path: "dose:flu_vaccine_2024", DisplayName: "インフルエンザワクチン2024", Description: "Flu vaccine dose"})
	recsfacility := seedCollection{Collection: "ai.gftd.apps.iryo.facility"}
	recsfacility.Items = append(recsfacility.Items, seedRecord{ID: "tokyo_univ_hosp", Data: map[string]any{"id": "tokyo_univ_hosp", "name": "東京大学医学部附属病院", "description": "Tokyo University Hospital", "status": "active"}})
	recsfacility.Items = append(recsfacility.Items, seedRecord{ID: "keio_hosp", Data: map[string]any{"id": "keio_hosp", "name": "慶應義塾大学病院", "description": "Keio University Hospital", "status": "active"}})
	def.Records = append(def.Records, recsfacility)
	recsdisease := seedCollection{Collection: "ai.gftd.apps.iryo.disease"}
	recsdisease.Items = append(recsdisease.Items, seedRecord{ID: "icd_j06", Data: map[string]any{"id": "icd_j06", "name": "急性上気道感染症", "description": "ICD J06 Acute URI", "status": "active"}})
	recsdisease.Items = append(recsdisease.Items, seedRecord{ID: "icd_e11", Data: map[string]any{"id": "icd_e11", "name": "2型糖尿病", "description": "ICD E11 Type 2 DM", "status": "active"}})
	def.Records = append(def.Records, recsdisease)
	recstrial := seedCollection{Collection: "ai.gftd.apps.iryo.trial"}
	recstrial.Items = append(recstrial.Items, seedRecord{ID: "covid_vaccine_01", Data: map[string]any{"id": "covid_vaccine_01", "name": "COVID-19ワクチン治験", "description": "Vaccine clinical trial", "status": "active"}})
	def.Records = append(def.Records, recstrial)
	recsclaim := seedCollection{Collection: "ai.gftd.apps.iryo.claim"}
	recsclaim.Items = append(recsclaim.Items, seedRecord{ID: "iryo_seikyu_001", Data: map[string]any{"id": "iryo_seikyu_001", "name": "医療費請求001", "description": "Medical claim", "status": "active"}})
	def.Records = append(def.Records, recsclaim)
	recsprescription := seedCollection{Collection: "ai.gftd.apps.iryo.prescription"}
	recsprescription.Items = append(recsprescription.Items, seedRecord{ID: "rx_001", Data: map[string]any{"id": "rx_001", "name": "処方箋001", "description": "Prescription", "status": "active"}})
	def.Records = append(def.Records, recsprescription)
	recsdose := seedCollection{Collection: "ai.gftd.apps.iryo.dose"}
	recsdose.Items = append(recsdose.Items, seedRecord{ID: "flu_vaccine_2024", Data: map[string]any{"id": "flu_vaccine_2024", "name": "インフルエンザワクチン2024", "description": "Flu vaccine dose", "status": "active"}})
	def.Records = append(def.Records, recsdose)
	return def
}

func IsbnGapSeeds() seedDef {
	def := seedDef{Domain: "isbn", Nanoid: "bn7k2m4x", DID: "did:web:isbn.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "book:harry_potter_1", DisplayName: "Harry Potter and the Philosopher's Stone", Description: "978-0-7475-3269-9"})
	def.DIDs = append(def.DIDs, seedDID{Path: "book:1q84", DisplayName: "1Q84", Description: "978-4-10-353432-4"})
	def.DIDs = append(def.DIDs, seedDID{Path: "book:sapiens", DisplayName: "Sapiens", Description: "978-0-06-231609-7"})
	def.DIDs = append(def.DIDs, seedDID{Path: "book:genshi_monogatari", DisplayName: "源氏物語", Description: "978-4-00-301001-6"})
	def.DIDs = append(def.DIDs, seedDID{Path: "book:art_of_war", DisplayName: "孫子兵法", Description: "978-0-19-501476-1"})
	recsbook := seedCollection{Collection: "ai.gftd.apps.isbn.book"}
	recsbook.Items = append(recsbook.Items, seedRecord{ID: "harry_potter_1", Data: map[string]any{"id": "harry_potter_1", "name": "Harry Potter and the Philosopher's Stone", "description": "978-0-7475-3269-9", "status": "active"}})
	recsbook.Items = append(recsbook.Items, seedRecord{ID: "1q84", Data: map[string]any{"id": "1q84", "name": "1Q84", "description": "978-4-10-353432-4", "status": "active"}})
	recsbook.Items = append(recsbook.Items, seedRecord{ID: "sapiens", Data: map[string]any{"id": "sapiens", "name": "Sapiens", "description": "978-0-06-231609-7", "status": "active"}})
	recsbook.Items = append(recsbook.Items, seedRecord{ID: "genshi_monogatari", Data: map[string]any{"id": "genshi_monogatari", "name": "源氏物語", "description": "978-4-00-301001-6", "status": "active"}})
	recsbook.Items = append(recsbook.Items, seedRecord{ID: "art_of_war", Data: map[string]any{"id": "art_of_war", "name": "孫子兵法", "description": "978-0-19-501476-1", "status": "active"}})
	def.Records = append(def.Records, recsbook)
	return def
}

func IsinGapSeeds() seedDef {
	def := seedDef{Domain: "isin", Nanoid: "is1n8k2x", DID: "did:web:isin.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "security:toyota_7203", DisplayName: "Toyota Motor (7203.T)", Description: "JP3633400001"})
	def.DIDs = append(def.DIDs, seedDID{Path: "security:apple_aapl", DisplayName: "Apple Inc (AAPL)", Description: "US0378331005"})
	def.DIDs = append(def.DIDs, seedDID{Path: "security:us_treasury_10y", DisplayName: "US Treasury 10Y", Description: "US912810TM53"})
	def.DIDs = append(def.DIDs, seedDID{Path: "security:sony_6758", DisplayName: "Sony Group (6758.T)", Description: "JP3435000009"})
	def.DIDs = append(def.DIDs, seedDID{Path: "security:nestle", DisplayName: "Nestlé SA", Description: "CH0038863350"})
	recssecurity := seedCollection{Collection: "ai.gftd.apps.isin.security"}
	recssecurity.Items = append(recssecurity.Items, seedRecord{ID: "toyota_7203", Data: map[string]any{"id": "toyota_7203", "name": "Toyota Motor (7203.T)", "description": "JP3633400001", "status": "active"}})
	recssecurity.Items = append(recssecurity.Items, seedRecord{ID: "apple_aapl", Data: map[string]any{"id": "apple_aapl", "name": "Apple Inc (AAPL)", "description": "US0378331005", "status": "active"}})
	recssecurity.Items = append(recssecurity.Items, seedRecord{ID: "us_treasury_10y", Data: map[string]any{"id": "us_treasury_10y", "name": "US Treasury 10Y", "description": "US912810TM53", "status": "active"}})
	recssecurity.Items = append(recssecurity.Items, seedRecord{ID: "sony_6758", Data: map[string]any{"id": "sony_6758", "name": "Sony Group (6758.T)", "description": "JP3435000009", "status": "active"}})
	recssecurity.Items = append(recssecurity.Items, seedRecord{ID: "nestle", Data: map[string]any{"id": "nestle", "name": "Nestlé SA", "description": "CH0038863350", "status": "active"}})
	def.Records = append(def.Records, recssecurity)
	return def
}

func IssnGapSeeds() seedDef {
	def := seedDef{Domain: "issn", Nanoid: "sn3k8m2v", DID: "did:web:issn.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "serial:nature", DisplayName: "Nature", Description: "ISSN 0028-0836"})
	def.DIDs = append(def.DIDs, seedDID{Path: "serial:science", DisplayName: "Science", Description: "ISSN 0036-8075"})
	def.DIDs = append(def.DIDs, seedDID{Path: "serial:lancet", DisplayName: "The Lancet", Description: "ISSN 0140-6736"})
	def.DIDs = append(def.DIDs, seedDID{Path: "serial:nikkei", DisplayName: "日本経済新聞", Description: "ISSN 0029-0181"})
	def.DIDs = append(def.DIDs, seedDID{Path: "serial:ieee_spectrum", DisplayName: "IEEE Spectrum", Description: "ISSN 0018-9235"})
	recsserial := seedCollection{Collection: "ai.gftd.apps.issn.serial"}
	recsserial.Items = append(recsserial.Items, seedRecord{ID: "nature", Data: map[string]any{"id": "nature", "name": "Nature", "description": "ISSN 0028-0836", "status": "active"}})
	recsserial.Items = append(recsserial.Items, seedRecord{ID: "science", Data: map[string]any{"id": "science", "name": "Science", "description": "ISSN 0036-8075", "status": "active"}})
	recsserial.Items = append(recsserial.Items, seedRecord{ID: "lancet", Data: map[string]any{"id": "lancet", "name": "The Lancet", "description": "ISSN 0140-6736", "status": "active"}})
	recsserial.Items = append(recsserial.Items, seedRecord{ID: "nikkei", Data: map[string]any{"id": "nikkei", "name": "日本経済新聞", "description": "ISSN 0029-0181", "status": "active"}})
	recsserial.Items = append(recsserial.Items, seedRecord{ID: "ieee_spectrum", Data: map[string]any{"id": "ieee_spectrum", "name": "IEEE Spectrum", "description": "ISSN 0018-9235", "status": "active"}})
	def.Records = append(def.Records, recsserial)
	return def
}

func JidoshaBuhinGapSeeds() seedDef {
	def := seedDef{Domain: "jidosha-buhin", Nanoid: "jido1363", DID: "did:web:jidosha-buhin.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "part:aisin_at", DisplayName: "アイシンAT", Description: "Automatic transmission"})
	def.DIDs = append(def.DIDs, seedDID{Path: "part:denso_injector", DisplayName: "デンソーインジェクタ", Description: "Fuel injector"})
	def.DIDs = append(def.DIDs, seedDID{Path: "part:nsk_bearing", DisplayName: "NSKベアリング", Description: "Wheel bearing"})
	def.DIDs = append(def.DIDs, seedDID{Path: "part:bridgestone_tire", DisplayName: "ブリヂストンタイヤ", Description: "Passenger tire"})
	def.DIDs = append(def.DIDs, seedDID{Path: "part:bosch_brake", DisplayName: "Bosch ABS", Description: "Anti-lock brake system"})
	recspart := seedCollection{Collection: "ai.gftd.apps.jidoshabuhin.part"}
	recspart.Items = append(recspart.Items, seedRecord{ID: "aisin_at", Data: map[string]any{"id": "aisin_at", "name": "アイシンAT", "description": "Automatic transmission", "status": "active"}})
	recspart.Items = append(recspart.Items, seedRecord{ID: "denso_injector", Data: map[string]any{"id": "denso_injector", "name": "デンソーインジェクタ", "description": "Fuel injector", "status": "active"}})
	recspart.Items = append(recspart.Items, seedRecord{ID: "nsk_bearing", Data: map[string]any{"id": "nsk_bearing", "name": "NSKベアリング", "description": "Wheel bearing", "status": "active"}})
	recspart.Items = append(recspart.Items, seedRecord{ID: "bridgestone_tire", Data: map[string]any{"id": "bridgestone_tire", "name": "ブリヂストンタイヤ", "description": "Passenger tire", "status": "active"}})
	recspart.Items = append(recspart.Items, seedRecord{ID: "bosch_brake", Data: map[string]any{"id": "bosch_brake", "name": "Bosch ABS", "description": "Anti-lock brake system", "status": "active"}})
	def.Records = append(def.Records, recspart)
	return def
}

func JikoGapSeeds() seedDef {
	def := seedDef{Domain: "jiko", Nanoid: "jk4ko01", DID: "did:web:jiko.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "incident:traffic_01", DisplayName: "交通事故01", Description: "Traffic accident"})
	def.DIDs = append(def.DIDs, seedDID{Path: "incident:fire_01", DisplayName: "火災事故01", Description: "Building fire"})
	def.DIDs = append(def.DIDs, seedDID{Path: "incident:industrial_01", DisplayName: "労働災害01", Description: "Industrial accident"})
	def.DIDs = append(def.DIDs, seedDID{Path: "incident:food_poison_01", DisplayName: "食中毒01", Description: "Food poisoning incident"})
	def.DIDs = append(def.DIDs, seedDID{Path: "incident:chemical_spill", DisplayName: "化学物質漏洩", Description: "Chemical spill"})
	recsincident := seedCollection{Collection: "ai.gftd.apps.jiko.incident"}
	recsincident.Items = append(recsincident.Items, seedRecord{ID: "traffic_01", Data: map[string]any{"id": "traffic_01", "name": "交通事故01", "description": "Traffic accident", "status": "active"}})
	recsincident.Items = append(recsincident.Items, seedRecord{ID: "fire_01", Data: map[string]any{"id": "fire_01", "name": "火災事故01", "description": "Building fire", "status": "active"}})
	recsincident.Items = append(recsincident.Items, seedRecord{ID: "industrial_01", Data: map[string]any{"id": "industrial_01", "name": "労働災害01", "description": "Industrial accident", "status": "active"}})
	recsincident.Items = append(recsincident.Items, seedRecord{ID: "food_poison_01", Data: map[string]any{"id": "food_poison_01", "name": "食中毒01", "description": "Food poisoning incident", "status": "active"}})
	recsincident.Items = append(recsincident.Items, seedRecord{ID: "chemical_spill", Data: map[string]any{"id": "chemical_spill", "name": "化学物質漏洩", "description": "Chemical spill", "status": "active"}})
	def.Records = append(def.Records, recsincident)
	return def
}

func JinushiGapSeeds() seedDef {
	def := seedDef{Domain: "jinushi", Nanoid: "ln5qr8tw", DID: "did:web:jinushi.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "parcel:minato_1_1", DisplayName: "港区1-1", Description: "Minato-ku, Tokyo parcel"})
	def.DIDs = append(def.DIDs, seedDID{Path: "parcel:chuo_ginza", DisplayName: "中央区銀座4丁目", Description: "Ginza, Tokyo parcel"})
	def.DIDs = append(def.DIDs, seedDID{Path: "parcel:shibuya_1", DisplayName: "渋谷区渋谷1丁目", Description: "Shibuya parcel"})
	def.DIDs = append(def.DIDs, seedDID{Path: "parcel:chiyoda_marunouchi", DisplayName: "千代田区丸の内1丁目", Description: "Marunouchi parcel"})
	def.DIDs = append(def.DIDs, seedDID{Path: "parcel:osaka_umeda", DisplayName: "大阪市北区梅田", Description: "Umeda, Osaka parcel"})
	recsparcel := seedCollection{Collection: "ai.gftd.apps.jinushi.parcel"}
	recsparcel.Items = append(recsparcel.Items, seedRecord{ID: "minato_1_1", Data: map[string]any{"id": "minato_1_1", "name": "港区1-1", "description": "Minato-ku, Tokyo parcel", "status": "active"}})
	recsparcel.Items = append(recsparcel.Items, seedRecord{ID: "chuo_ginza", Data: map[string]any{"id": "chuo_ginza", "name": "中央区銀座4丁目", "description": "Ginza, Tokyo parcel", "status": "active"}})
	recsparcel.Items = append(recsparcel.Items, seedRecord{ID: "shibuya_1", Data: map[string]any{"id": "shibuya_1", "name": "渋谷区渋谷1丁目", "description": "Shibuya parcel", "status": "active"}})
	recsparcel.Items = append(recsparcel.Items, seedRecord{ID: "chiyoda_marunouchi", Data: map[string]any{"id": "chiyoda_marunouchi", "name": "千代田区丸の内1丁目", "description": "Marunouchi parcel", "status": "active"}})
	recsparcel.Items = append(recsparcel.Items, seedRecord{ID: "osaka_umeda", Data: map[string]any{"id": "osaka_umeda", "name": "大阪市北区梅田", "description": "Umeda, Osaka parcel", "status": "active"}})
	def.Records = append(def.Records, recsparcel)
	return def
}

func JouchoGapSeeds() seedDef {
	def := seedDef{Domain: "joucho", Nanoid: "erp6xu1c", DID: "did:web:joucho.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "person:sample_001", DisplayName: "情緒スコア001", Description: "Emotional wellness score sample"})
	def.DIDs = append(def.DIDs, seedDID{Path: "person:sample_002", DisplayName: "情緒スコア002", Description: "Mindfulness assessment"})
	def.DIDs = append(def.DIDs, seedDID{Path: "person:sample_003", DisplayName: "情緒スコア003", Description: "Stress resilience score"})
	def.DIDs = append(def.DIDs, seedDID{Path: "person:sample_004", DisplayName: "情緒スコア004", Description: "Social wellbeing index"})
	def.DIDs = append(def.DIDs, seedDID{Path: "person:sample_005", DisplayName: "情緒スコア005", Description: "Life satisfaction score"})
	recsperson := seedCollection{Collection: "ai.gftd.apps.joucho.person"}
	recsperson.Items = append(recsperson.Items, seedRecord{ID: "sample_001", Data: map[string]any{"id": "sample_001", "name": "情緒スコア001", "description": "Emotional wellness score sample", "status": "active"}})
	recsperson.Items = append(recsperson.Items, seedRecord{ID: "sample_002", Data: map[string]any{"id": "sample_002", "name": "情緒スコア002", "description": "Mindfulness assessment", "status": "active"}})
	recsperson.Items = append(recsperson.Items, seedRecord{ID: "sample_003", Data: map[string]any{"id": "sample_003", "name": "情緒スコア003", "description": "Stress resilience score", "status": "active"}})
	recsperson.Items = append(recsperson.Items, seedRecord{ID: "sample_004", Data: map[string]any{"id": "sample_004", "name": "情緒スコア004", "description": "Social wellbeing index", "status": "active"}})
	recsperson.Items = append(recsperson.Items, seedRecord{ID: "sample_005", Data: map[string]any{"id": "sample_005", "name": "情緒スコア005", "description": "Life satisfaction score", "status": "active"}})
	def.Records = append(def.Records, recsperson)
	return def
}

func K8sGapSeeds() seedDef {
	def := seedDef{Domain: "k8s", Nanoid: "ks4cl01", DID: "did:web:k8s.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "cluster:prod_apne1", DisplayName: "Production ap-northeast-1", Description: "Production K8s cluster"})
	def.DIDs = append(def.DIDs, seedDID{Path: "cluster:staging", DisplayName: "Staging Cluster", Description: "Staging K8s cluster"})
	def.DIDs = append(def.DIDs, seedDID{Path: "pod:nginx_ingress", DisplayName: "nginx-ingress", Description: "Ingress controller pod"})
	def.DIDs = append(def.DIDs, seedDID{Path: "pod:coredns", DisplayName: "CoreDNS", Description: "DNS pod"})
	def.DIDs = append(def.DIDs, seedDID{Path: "pod:prometheus", DisplayName: "Prometheus", Description: "Monitoring pod"})
	recscluster := seedCollection{Collection: "ai.gftd.apps.k8s.cluster"}
	recscluster.Items = append(recscluster.Items, seedRecord{ID: "prod_apne1", Data: map[string]any{"id": "prod_apne1", "name": "Production ap-northeast-1", "description": "Production K8s cluster", "status": "active"}})
	recscluster.Items = append(recscluster.Items, seedRecord{ID: "staging", Data: map[string]any{"id": "staging", "name": "Staging Cluster", "description": "Staging K8s cluster", "status": "active"}})
	def.Records = append(def.Records, recscluster)
	recspod := seedCollection{Collection: "ai.gftd.apps.k8s.pod"}
	recspod.Items = append(recspod.Items, seedRecord{ID: "nginx_ingress", Data: map[string]any{"id": "nginx_ingress", "name": "nginx-ingress", "description": "Ingress controller pod", "status": "active"}})
	recspod.Items = append(recspod.Items, seedRecord{ID: "coredns", Data: map[string]any{"id": "coredns", "name": "CoreDNS", "description": "DNS pod", "status": "active"}})
	recspod.Items = append(recspod.Items, seedRecord{ID: "prometheus", Data: map[string]any{"id": "prometheus", "name": "Prometheus", "description": "Monitoring pod", "status": "active"}})
	def.Records = append(def.Records, recspod)
	return def
}

func KachikuGapSeeds() seedDef {
	def := seedDef{Domain: "kachiku", Nanoid: "kachfe1b", DID: "did:web:kachiku.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "animal:wagyu_kuroge", DisplayName: "黒毛和牛", Description: "Japanese Black cattle"})
	def.DIDs = append(def.DIDs, seedDID{Path: "animal:holstein", DisplayName: "ホルスタイン", Description: "Holstein dairy cow"})
	def.DIDs = append(def.DIDs, seedDID{Path: "animal:berkshire", DisplayName: "バークシャー豚", Description: "Berkshire pig"})
	def.DIDs = append(def.DIDs, seedDID{Path: "animal:nagoya_cochin", DisplayName: "名古屋コーチン", Description: "Nagoya Cochin chicken"})
	def.DIDs = append(def.DIDs, seedDID{Path: "animal:suffolk", DisplayName: "サフォーク羊", Description: "Suffolk sheep"})
	recsanimal := seedCollection{Collection: "ai.gftd.apps.kachiku.animal"}
	recsanimal.Items = append(recsanimal.Items, seedRecord{ID: "wagyu_kuroge", Data: map[string]any{"id": "wagyu_kuroge", "name": "黒毛和牛", "description": "Japanese Black cattle", "status": "active"}})
	recsanimal.Items = append(recsanimal.Items, seedRecord{ID: "holstein", Data: map[string]any{"id": "holstein", "name": "ホルスタイン", "description": "Holstein dairy cow", "status": "active"}})
	recsanimal.Items = append(recsanimal.Items, seedRecord{ID: "berkshire", Data: map[string]any{"id": "berkshire", "name": "バークシャー豚", "description": "Berkshire pig", "status": "active"}})
	recsanimal.Items = append(recsanimal.Items, seedRecord{ID: "nagoya_cochin", Data: map[string]any{"id": "nagoya_cochin", "name": "名古屋コーチン", "description": "Nagoya Cochin chicken", "status": "active"}})
	recsanimal.Items = append(recsanimal.Items, seedRecord{ID: "suffolk", Data: map[string]any{"id": "suffolk", "name": "サフォーク羊", "description": "Suffolk sheep", "status": "active"}})
	def.Records = append(def.Records, recsanimal)
	return def
}

func KaguGapSeeds() seedDef {
	def := seedDef{Domain: "kagu", Nanoid: "kg4gu01", DID: "did:web:kagu.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "product:sofa_3seat", DisplayName: "3人掛けソファ", Description: "3-seater sofa"})
	def.DIDs = append(def.DIDs, seedDID{Path: "product:dining_table", DisplayName: "ダイニングテーブル", Description: "Dining table"})
	def.DIDs = append(def.DIDs, seedDID{Path: "product:office_chair", DisplayName: "オフィスチェア", Description: "Ergonomic office chair"})
	def.DIDs = append(def.DIDs, seedDID{Path: "product:bookshelf", DisplayName: "本棚", Description: "5-tier bookshelf"})
	def.DIDs = append(def.DIDs, seedDID{Path: "product:bed_queen", DisplayName: "クイーンベッド", Description: "Queen-size bed frame"})
	recsproduct := seedCollection{Collection: "ai.gftd.apps.kagu.product"}
	recsproduct.Items = append(recsproduct.Items, seedRecord{ID: "sofa_3seat", Data: map[string]any{"id": "sofa_3seat", "name": "3人掛けソファ", "description": "3-seater sofa", "status": "active"}})
	recsproduct.Items = append(recsproduct.Items, seedRecord{ID: "dining_table", Data: map[string]any{"id": "dining_table", "name": "ダイニングテーブル", "description": "Dining table", "status": "active"}})
	recsproduct.Items = append(recsproduct.Items, seedRecord{ID: "office_chair", Data: map[string]any{"id": "office_chair", "name": "オフィスチェア", "description": "Ergonomic office chair", "status": "active"}})
	recsproduct.Items = append(recsproduct.Items, seedRecord{ID: "bookshelf", Data: map[string]any{"id": "bookshelf", "name": "本棚", "description": "5-tier bookshelf", "status": "active"}})
	recsproduct.Items = append(recsproduct.Items, seedRecord{ID: "bed_queen", Data: map[string]any{"id": "bed_queen", "name": "クイーンベッド", "description": "Queen-size bed frame", "status": "active"}})
	def.Records = append(def.Records, recsproduct)
	return def
}

func KaigoGapSeeds() seedDef {
	def := seedDef{Domain: "kaigo", Nanoid: "kg8r2m5n", DID: "did:web:kaigo.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "facility:tokuyo_tokyo", DisplayName: "特養東京01", Description: "Special nursing home Tokyo"})
	def.DIDs = append(def.DIDs, seedDID{Path: "facility:rouken_osaka", DisplayName: "老健大阪01", Description: "Health facility Osaka"})
	def.DIDs = append(def.DIDs, seedDID{Path: "facility:group_home_kobe", DisplayName: "グループホーム神戸", Description: "Group home Kobe"})
	def.DIDs = append(def.DIDs, seedDID{Path: "facility:dayservice_yokohama", DisplayName: "デイサービス横浜", Description: "Day service Yokohama"})
	def.DIDs = append(def.DIDs, seedDID{Path: "facility:home_care_sapporo", DisplayName: "訪問介護札幌", Description: "Home care Sapporo"})
	recsfacility := seedCollection{Collection: "ai.gftd.apps.kaigo.facility"}
	recsfacility.Items = append(recsfacility.Items, seedRecord{ID: "tokuyo_tokyo", Data: map[string]any{"id": "tokuyo_tokyo", "name": "特養東京01", "description": "Special nursing home Tokyo", "status": "active"}})
	recsfacility.Items = append(recsfacility.Items, seedRecord{ID: "rouken_osaka", Data: map[string]any{"id": "rouken_osaka", "name": "老健大阪01", "description": "Health facility Osaka", "status": "active"}})
	recsfacility.Items = append(recsfacility.Items, seedRecord{ID: "group_home_kobe", Data: map[string]any{"id": "group_home_kobe", "name": "グループホーム神戸", "description": "Group home Kobe", "status": "active"}})
	recsfacility.Items = append(recsfacility.Items, seedRecord{ID: "dayservice_yokohama", Data: map[string]any{"id": "dayservice_yokohama", "name": "デイサービス横浜", "description": "Day service Yokohama", "status": "active"}})
	recsfacility.Items = append(recsfacility.Items, seedRecord{ID: "home_care_sapporo", Data: map[string]any{"id": "home_care_sapporo", "name": "訪問介護札幌", "description": "Home care Sapporo", "status": "active"}})
	def.Records = append(def.Records, recsfacility)
	return def
}

func KeiyakuGapSeeds() seedDef {
	def := seedDef{Domain: "keiyaku", Nanoid: "ky4ku01", DID: "did:web:keiyaku.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "contract:nda_001", DisplayName: "秘密保持契約001", Description: "NDA"})
	def.DIDs = append(def.DIDs, seedDID{Path: "contract:employment_001", DisplayName: "雇用契約001", Description: "Employment contract"})
	def.DIDs = append(def.DIDs, seedDID{Path: "contract:lease_001", DisplayName: "賃貸借契約001", Description: "Lease agreement"})
	def.DIDs = append(def.DIDs, seedDID{Path: "contract:service_001", DisplayName: "業務委託契約001", Description: "Service agreement"})
	def.DIDs = append(def.DIDs, seedDID{Path: "contract:subscription_001", DisplayName: "サブスクリプション契約001", Description: "Subscription"})
	def.DIDs = append(def.DIDs, seedDID{Path: "contract:license_001", DisplayName: "ライセンス契約001", Description: "License agreement"})
	def.DIDs = append(def.DIDs, seedDID{Path: "agreement:terms_001", DisplayName: "利用規約001", Description: "Terms of service"})
	recscontract := seedCollection{Collection: "ai.gftd.apps.keiyaku.contract"}
	recscontract.Items = append(recscontract.Items, seedRecord{ID: "nda_001", Data: map[string]any{"id": "nda_001", "name": "秘密保持契約001", "description": "NDA", "status": "active"}})
	recscontract.Items = append(recscontract.Items, seedRecord{ID: "employment_001", Data: map[string]any{"id": "employment_001", "name": "雇用契約001", "description": "Employment contract", "status": "active"}})
	recscontract.Items = append(recscontract.Items, seedRecord{ID: "lease_001", Data: map[string]any{"id": "lease_001", "name": "賃貸借契約001", "description": "Lease agreement", "status": "active"}})
	recscontract.Items = append(recscontract.Items, seedRecord{ID: "service_001", Data: map[string]any{"id": "service_001", "name": "業務委託契約001", "description": "Service agreement", "status": "active"}})
	recscontract.Items = append(recscontract.Items, seedRecord{ID: "subscription_001", Data: map[string]any{"id": "subscription_001", "name": "サブスクリプション契約001", "description": "Subscription", "status": "active"}})
	recscontract.Items = append(recscontract.Items, seedRecord{ID: "license_001", Data: map[string]any{"id": "license_001", "name": "ライセンス契約001", "description": "License agreement", "status": "active"}})
	def.Records = append(def.Records, recscontract)
	recsagreement := seedCollection{Collection: "ai.gftd.apps.keiyaku.agreement"}
	recsagreement.Items = append(recsagreement.Items, seedRecord{ID: "terms_001", Data: map[string]any{"id": "terms_001", "name": "利用規約001", "description": "Terms of service", "status": "active"}})
	def.Records = append(def.Records, recsagreement)
	return def
}

func KensetsuGapSeeds() seedDef {
	def := seedDef{Domain: "kensetsu", Nanoid: "kn4st01", DID: "did:web:kensetsu.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "project:tokyo_skytree", DisplayName: "東京スカイツリー", Description: "634m broadcasting tower"})
	def.DIDs = append(def.DIDs, seedDID{Path: "project:linear_chuo", DisplayName: "リニア中央新幹線", Description: "Maglev Shinkansen"})
	def.DIDs = append(def.DIDs, seedDID{Path: "project:osaka_expo2025", DisplayName: "大阪万博2025", Description: "Expo 2025 Osaka"})
	def.DIDs = append(def.DIDs, seedDID{Path: "project:crossrail", DisplayName: "Crossrail (Elizabeth Line)", Description: "London rail project"})
	def.DIDs = append(def.DIDs, seedDID{Path: "project:neom", DisplayName: "NEOM", Description: "Saudi Arabia megaproject"})
	recsproject := seedCollection{Collection: "ai.gftd.apps.kensetsu.project"}
	recsproject.Items = append(recsproject.Items, seedRecord{ID: "tokyo_skytree", Data: map[string]any{"id": "tokyo_skytree", "name": "東京スカイツリー", "description": "634m broadcasting tower", "status": "active"}})
	recsproject.Items = append(recsproject.Items, seedRecord{ID: "linear_chuo", Data: map[string]any{"id": "linear_chuo", "name": "リニア中央新幹線", "description": "Maglev Shinkansen", "status": "active"}})
	recsproject.Items = append(recsproject.Items, seedRecord{ID: "osaka_expo2025", Data: map[string]any{"id": "osaka_expo2025", "name": "大阪万博2025", "description": "Expo 2025 Osaka", "status": "active"}})
	recsproject.Items = append(recsproject.Items, seedRecord{ID: "crossrail", Data: map[string]any{"id": "crossrail", "name": "Crossrail (Elizabeth Line)", "description": "London rail project", "status": "active"}})
	recsproject.Items = append(recsproject.Items, seedRecord{ID: "neom", Data: map[string]any{"id": "neom", "name": "NEOM", "description": "Saudi Arabia megaproject", "status": "active"}})
	def.Records = append(def.Records, recsproject)
	return def
}

func KenzaiGapSeeds() seedDef {
	def := seedDef{Domain: "kenzai", Nanoid: "kz4ai01", DID: "did:web:kenzai.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "material:concrete_c30", DisplayName: "コンクリートC30", Description: "Ready-mix concrete"})
	def.DIDs = append(def.DIDs, seedDID{Path: "material:rebar_d13", DisplayName: "鉄筋D13", Description: "Deformed rebar 13mm"})
	def.DIDs = append(def.DIDs, seedDID{Path: "material:plywood_12", DisplayName: "合板12mm", Description: "Structural plywood"})
	def.DIDs = append(def.DIDs, seedDID{Path: "material:insulation_glass", DisplayName: "グラスウール", Description: "Glass wool insulation"})
	def.DIDs = append(def.DIDs, seedDID{Path: "material:steel_h200", DisplayName: "H鋼200", Description: "H-beam steel 200mm"})
	recsmaterial := seedCollection{Collection: "ai.gftd.apps.kenzai.material"}
	recsmaterial.Items = append(recsmaterial.Items, seedRecord{ID: "concrete_c30", Data: map[string]any{"id": "concrete_c30", "name": "コンクリートC30", "description": "Ready-mix concrete", "status": "active"}})
	recsmaterial.Items = append(recsmaterial.Items, seedRecord{ID: "rebar_d13", Data: map[string]any{"id": "rebar_d13", "name": "鉄筋D13", "description": "Deformed rebar 13mm", "status": "active"}})
	recsmaterial.Items = append(recsmaterial.Items, seedRecord{ID: "plywood_12", Data: map[string]any{"id": "plywood_12", "name": "合板12mm", "description": "Structural plywood", "status": "active"}})
	recsmaterial.Items = append(recsmaterial.Items, seedRecord{ID: "insulation_glass", Data: map[string]any{"id": "insulation_glass", "name": "グラスウール", "description": "Glass wool insulation", "status": "active"}})
	recsmaterial.Items = append(recsmaterial.Items, seedRecord{ID: "steel_h200", Data: map[string]any{"id": "steel_h200", "name": "H鋼200", "description": "H-beam steel 200mm", "status": "active"}})
	def.Records = append(def.Records, recsmaterial)
	return def
}

func KessaiGapSeeds() seedDef {
	def := seedDef{Domain: "kessai", Nanoid: "ks4ai01", DID: "did:web:kessai.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "transaction:paypay_001", DisplayName: "PayPay決済001", Description: "QR code payment"})
	def.DIDs = append(def.DIDs, seedDID{Path: "transaction:suica_001", DisplayName: "Suica決済001", Description: "IC card payment"})
	def.DIDs = append(def.DIDs, seedDID{Path: "transaction:visa_touch", DisplayName: "Visaタッチ001", Description: "Contactless payment"})
	def.DIDs = append(def.DIDs, seedDID{Path: "transaction:bank_transfer", DisplayName: "銀行振込001", Description: "Bank transfer"})
	def.DIDs = append(def.DIDs, seedDID{Path: "transaction:conv_001", DisplayName: "コンビニ決済001", Description: "Convenience store payment"})
	recstransaction := seedCollection{Collection: "ai.gftd.apps.kessai.transaction"}
	recstransaction.Items = append(recstransaction.Items, seedRecord{ID: "paypay_001", Data: map[string]any{"id": "paypay_001", "name": "PayPay決済001", "description": "QR code payment", "status": "active"}})
	recstransaction.Items = append(recstransaction.Items, seedRecord{ID: "suica_001", Data: map[string]any{"id": "suica_001", "name": "Suica決済001", "description": "IC card payment", "status": "active"}})
	recstransaction.Items = append(recstransaction.Items, seedRecord{ID: "visa_touch", Data: map[string]any{"id": "visa_touch", "name": "Visaタッチ001", "description": "Contactless payment", "status": "active"}})
	recstransaction.Items = append(recstransaction.Items, seedRecord{ID: "bank_transfer", Data: map[string]any{"id": "bank_transfer", "name": "銀行振込001", "description": "Bank transfer", "status": "active"}})
	recstransaction.Items = append(recstransaction.Items, seedRecord{ID: "conv_001", Data: map[string]any{"id": "conv_001", "name": "コンビニ決済001", "description": "Convenience store payment", "status": "active"}})
	def.Records = append(def.Records, recstransaction)
	return def
}

func KikaiBuhinGapSeeds() seedDef {
	def := seedDef{Domain: "kikai-buhin", Nanoid: "kikaf5d2", DID: "did:web:kikai-buhin.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "part:nsk_bearing", DisplayName: "NSKベアリング", Description: "Ball bearing"})
	def.DIDs = append(def.DIDs, seedDID{Path: "part:thk_linear", DisplayName: "THKリニアガイド", Description: "Linear guide"})
	def.DIDs = append(def.DIDs, seedDID{Path: "part:smc_cylinder", DisplayName: "SMCシリンダ", Description: "Pneumatic cylinder"})
	def.DIDs = append(def.DIDs, seedDID{Path: "part:harmonic_drive", DisplayName: "ハーモニックドライブ", Description: "Harmonic drive"})
	def.DIDs = append(def.DIDs, seedDID{Path: "part:fanuc_servo", DisplayName: "ファナックサーボ", Description: "Servo motor"})
	recspart := seedCollection{Collection: "ai.gftd.apps.kikaibuhin.part"}
	recspart.Items = append(recspart.Items, seedRecord{ID: "nsk_bearing", Data: map[string]any{"id": "nsk_bearing", "name": "NSKベアリング", "description": "Ball bearing", "status": "active"}})
	recspart.Items = append(recspart.Items, seedRecord{ID: "thk_linear", Data: map[string]any{"id": "thk_linear", "name": "THKリニアガイド", "description": "Linear guide", "status": "active"}})
	recspart.Items = append(recspart.Items, seedRecord{ID: "smc_cylinder", Data: map[string]any{"id": "smc_cylinder", "name": "SMCシリンダ", "description": "Pneumatic cylinder", "status": "active"}})
	recspart.Items = append(recspart.Items, seedRecord{ID: "harmonic_drive", Data: map[string]any{"id": "harmonic_drive", "name": "ハーモニックドライブ", "description": "Harmonic drive", "status": "active"}})
	recspart.Items = append(recspart.Items, seedRecord{ID: "fanuc_servo", Data: map[string]any{"id": "fanuc_servo", "name": "ファナックサーボ", "description": "Servo motor", "status": "active"}})
	def.Records = append(def.Records, recspart)
	return def
}

func KiseiGapSeeds() seedDef {
	def := seedDef{Domain: "kisei", Nanoid: "kisef8c9", DID: "did:web:kisei.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "filing:fsa_annual", DisplayName: "金融庁有価証券報告書", Description: "FSA annual report"})
	def.DIDs = append(def.DIDs, seedDID{Path: "filing:sec_10k", DisplayName: "SEC 10-K", Description: "US annual filing"})
	def.DIDs = append(def.DIDs, seedDID{Path: "filing:pmda_nda", DisplayName: "PMDA新薬承認申請", Description: "Drug approval filing"})
	def.DIDs = append(def.DIDs, seedDID{Path: "filing:fcc_license", DisplayName: "FCC License", Description: "Telecom license filing"})
	def.DIDs = append(def.DIDs, seedDID{Path: "filing:ema_marketing", DisplayName: "EMA Marketing Auth", Description: "EU drug authorization"})
	recsfiling := seedCollection{Collection: "ai.gftd.apps.kisei.filing"}
	recsfiling.Items = append(recsfiling.Items, seedRecord{ID: "fsa_annual", Data: map[string]any{"id": "fsa_annual", "name": "金融庁有価証券報告書", "description": "FSA annual report", "status": "active"}})
	recsfiling.Items = append(recsfiling.Items, seedRecord{ID: "sec_10k", Data: map[string]any{"id": "sec_10k", "name": "SEC 10-K", "description": "US annual filing", "status": "active"}})
	recsfiling.Items = append(recsfiling.Items, seedRecord{ID: "pmda_nda", Data: map[string]any{"id": "pmda_nda", "name": "PMDA新薬承認申請", "description": "Drug approval filing", "status": "active"}})
	recsfiling.Items = append(recsfiling.Items, seedRecord{ID: "fcc_license", Data: map[string]any{"id": "fcc_license", "name": "FCC License", "description": "Telecom license filing", "status": "active"}})
	recsfiling.Items = append(recsfiling.Items, seedRecord{ID: "ema_marketing", Data: map[string]any{"id": "ema_marketing", "name": "EMA Marketing Auth", "description": "EU drug authorization", "status": "active"}})
	def.Records = append(def.Records, recsfiling)
	return def
}

func KosekiGapSeeds() seedDef {
	def := seedDef{Domain: "koseki", Nanoid: "kose772a", DID: "did:web:koseki.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "certificate:birth_001", DisplayName: "出生届001", Description: "Birth certificate"})
	def.DIDs = append(def.DIDs, seedDID{Path: "certificate:marriage_001", DisplayName: "婚姻届001", Description: "Marriage certificate"})
	def.DIDs = append(def.DIDs, seedDID{Path: "certificate:death_001", DisplayName: "死亡届001", Description: "Death certificate"})
	def.DIDs = append(def.DIDs, seedDID{Path: "certificate:divorce_001", DisplayName: "離婚届001", Description: "Divorce certificate"})
	def.DIDs = append(def.DIDs, seedDID{Path: "certificate:adoption_001", DisplayName: "養子縁組届001", Description: "Adoption certificate"})
	recscertificate := seedCollection{Collection: "ai.gftd.apps.koseki.certificate"}
	recscertificate.Items = append(recscertificate.Items, seedRecord{ID: "birth_001", Data: map[string]any{"id": "birth_001", "name": "出生届001", "description": "Birth certificate", "status": "active"}})
	recscertificate.Items = append(recscertificate.Items, seedRecord{ID: "marriage_001", Data: map[string]any{"id": "marriage_001", "name": "婚姻届001", "description": "Marriage certificate", "status": "active"}})
	recscertificate.Items = append(recscertificate.Items, seedRecord{ID: "death_001", Data: map[string]any{"id": "death_001", "name": "死亡届001", "description": "Death certificate", "status": "active"}})
	recscertificate.Items = append(recscertificate.Items, seedRecord{ID: "divorce_001", Data: map[string]any{"id": "divorce_001", "name": "離婚届001", "description": "Divorce certificate", "status": "active"}})
	recscertificate.Items = append(recscertificate.Items, seedRecord{ID: "adoption_001", Data: map[string]any{"id": "adoption_001", "name": "養子縁組届001", "description": "Adoption certificate", "status": "active"}})
	def.Records = append(def.Records, recscertificate)
	return def
}

func KoutsuuGapSeeds() seedDef {
	def := seedDef{Domain: "koutsuu", Nanoid: "kout04d8", DID: "did:web:koutsuu.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "violation:speed_001", DisplayName: "速度超過001", Description: "Speeding violation"})
	def.DIDs = append(def.DIDs, seedDID{Path: "violation:signal_001", DisplayName: "信号無視001", Description: "Red light violation"})
	def.DIDs = append(def.DIDs, seedDID{Path: "violation:parking_001", DisplayName: "駐車違反001", Description: "Parking violation"})
	def.DIDs = append(def.DIDs, seedDID{Path: "violation:dui_001", DisplayName: "飲酒運転001", Description: "DUI violation"})
	def.DIDs = append(def.DIDs, seedDID{Path: "violation:seatbelt_001", DisplayName: "シートベルト不装着001", Description: "Seatbelt violation"})
	recsviolation := seedCollection{Collection: "ai.gftd.apps.koutsuu.violation"}
	recsviolation.Items = append(recsviolation.Items, seedRecord{ID: "speed_001", Data: map[string]any{"id": "speed_001", "name": "速度超過001", "description": "Speeding violation", "status": "active"}})
	recsviolation.Items = append(recsviolation.Items, seedRecord{ID: "signal_001", Data: map[string]any{"id": "signal_001", "name": "信号無視001", "description": "Red light violation", "status": "active"}})
	recsviolation.Items = append(recsviolation.Items, seedRecord{ID: "parking_001", Data: map[string]any{"id": "parking_001", "name": "駐車違反001", "description": "Parking violation", "status": "active"}})
	recsviolation.Items = append(recsviolation.Items, seedRecord{ID: "dui_001", Data: map[string]any{"id": "dui_001", "name": "飲酒運転001", "description": "DUI violation", "status": "active"}})
	recsviolation.Items = append(recsviolation.Items, seedRecord{ID: "seatbelt_001", Data: map[string]any{"id": "seatbelt_001", "name": "シートベルト不装着001", "description": "Seatbelt violation", "status": "active"}})
	def.Records = append(def.Records, recsviolation)
	return def
}

func KurumaGapSeeds() seedDef {
	def := seedDef{Domain: "kuruma", Nanoid: "qewr7sl0", DID: "did:web:kuruma.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "model:toyota_corolla", DisplayName: "トヨタ カローラ", Description: "Toyota Corolla sedan"})
	def.DIDs = append(def.DIDs, seedDID{Path: "model:honda_civic", DisplayName: "ホンダ シビック", Description: "Honda Civic sedan"})
	def.DIDs = append(def.DIDs, seedDID{Path: "model:nissan_leaf", DisplayName: "日産 リーフ", Description: "Nissan Leaf EV"})
	def.DIDs = append(def.DIDs, seedDID{Path: "maker:toyota", DisplayName: "トヨタ自動車", Description: "Toyota Motor Corporation"})
	def.DIDs = append(def.DIDs, seedDID{Path: "maker:honda", DisplayName: "本田技研工業", Description: "Honda Motor Co"})
	def.DIDs = append(def.DIDs, seedDID{Path: "dealer:toyota_tokyo", DisplayName: "トヨタ東京販売", Description: "Toyota dealer Tokyo"})
	recsmodel := seedCollection{Collection: "ai.gftd.apps.kuruma.model"}
	recsmodel.Items = append(recsmodel.Items, seedRecord{ID: "toyota_corolla", Data: map[string]any{"id": "toyota_corolla", "name": "トヨタ カローラ", "description": "Toyota Corolla sedan", "status": "active"}})
	recsmodel.Items = append(recsmodel.Items, seedRecord{ID: "honda_civic", Data: map[string]any{"id": "honda_civic", "name": "ホンダ シビック", "description": "Honda Civic sedan", "status": "active"}})
	recsmodel.Items = append(recsmodel.Items, seedRecord{ID: "nissan_leaf", Data: map[string]any{"id": "nissan_leaf", "name": "日産 リーフ", "description": "Nissan Leaf EV", "status": "active"}})
	def.Records = append(def.Records, recsmodel)
	recsmaker := seedCollection{Collection: "ai.gftd.apps.kuruma.maker"}
	recsmaker.Items = append(recsmaker.Items, seedRecord{ID: "toyota", Data: map[string]any{"id": "toyota", "name": "トヨタ自動車", "description": "Toyota Motor Corporation", "status": "active"}})
	recsmaker.Items = append(recsmaker.Items, seedRecord{ID: "honda", Data: map[string]any{"id": "honda", "name": "本田技研工業", "description": "Honda Motor Co", "status": "active"}})
	def.Records = append(def.Records, recsmaker)
	recsdealer := seedCollection{Collection: "ai.gftd.apps.kuruma.dealer"}
	recsdealer.Items = append(recsdealer.Items, seedRecord{ID: "toyota_tokyo", Data: map[string]any{"id": "toyota_tokyo", "name": "トヨタ東京販売", "description": "Toyota dealer Tokyo", "status": "active"}})
	def.Records = append(def.Records, recsdealer)
	return def
}

func KyokaGapSeeds() seedDef {
	def := seedDef{Domain: "kyoka", Nanoid: "kyok5671", DID: "did:web:kyoka.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "license:inshokugyou", DisplayName: "飲食業営業許可", Description: "Restaurant business license"})
	def.DIDs = append(def.DIDs, seedDID{Path: "license:kensetsugyou", DisplayName: "建設業許可", Description: "Construction business license"})
	def.DIDs = append(def.DIDs, seedDID{Path: "license:takushii", DisplayName: "タクシー事業許可", Description: "Taxi business license"})
	def.DIDs = append(def.DIDs, seedDID{Path: "license:iyakuhin", DisplayName: "医薬品製造販売許可", Description: "Pharmaceutical license"})
	def.DIDs = append(def.DIDs, seedDID{Path: "license:sanpai", DisplayName: "産業廃棄物収集運搬許可", Description: "Waste collection license"})
	recslicense := seedCollection{Collection: "ai.gftd.apps.kyoka.license"}
	recslicense.Items = append(recslicense.Items, seedRecord{ID: "inshokugyou", Data: map[string]any{"id": "inshokugyou", "name": "飲食業営業許可", "description": "Restaurant business license", "status": "active"}})
	recslicense.Items = append(recslicense.Items, seedRecord{ID: "kensetsugyou", Data: map[string]any{"id": "kensetsugyou", "name": "建設業許可", "description": "Construction business license", "status": "active"}})
	recslicense.Items = append(recslicense.Items, seedRecord{ID: "takushii", Data: map[string]any{"id": "takushii", "name": "タクシー事業許可", "description": "Taxi business license", "status": "active"}})
	recslicense.Items = append(recslicense.Items, seedRecord{ID: "iyakuhin", Data: map[string]any{"id": "iyakuhin", "name": "医薬品製造販売許可", "description": "Pharmaceutical license", "status": "active"}})
	recslicense.Items = append(recslicense.Items, seedRecord{ID: "sanpai", Data: map[string]any{"id": "sanpai", "name": "産業廃棄物収集運搬許可", "description": "Waste collection license", "status": "active"}})
	def.Records = append(def.Records, recslicense)
	return def
}

func LegalEntityGapSeeds() seedDef {
	def := seedDef{Domain: "legal-entity", Nanoid: "le01corp0", DID: "did:web:legal-entity.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "entity:toyota_lei", DisplayName: "Toyota Motor Corp", Description: "LEI 549300LMDOGTYKHN1539"})
	def.DIDs = append(def.DIDs, seedDID{Path: "entity:softbank_lei", DisplayName: "SoftBank Group", Description: "LEI 5493003HJX5AKHY01N21"})
	def.DIDs = append(def.DIDs, seedDID{Path: "entity:sony_lei", DisplayName: "Sony Group Corp", Description: "LEI 529900R5WX9N2OI2N910"})
	def.DIDs = append(def.DIDs, seedDID{Path: "lei:jpmorgan", DisplayName: "JPMorgan Chase", Description: "LEI 8I5DZWZKVSZI1NUHU748"})
	def.DIDs = append(def.DIDs, seedDID{Path: "entity:apple_lei", DisplayName: "Apple Inc", Description: "LEI HWUPKR0MPOU8FGXBT394"})
	recsentity := seedCollection{Collection: "ai.gftd.apps.legalentity.entity"}
	recsentity.Items = append(recsentity.Items, seedRecord{ID: "toyota_lei", Data: map[string]any{"id": "toyota_lei", "name": "Toyota Motor Corp", "description": "LEI 549300LMDOGTYKHN1539", "status": "active"}})
	recsentity.Items = append(recsentity.Items, seedRecord{ID: "softbank_lei", Data: map[string]any{"id": "softbank_lei", "name": "SoftBank Group", "description": "LEI 5493003HJX5AKHY01N21", "status": "active"}})
	recsentity.Items = append(recsentity.Items, seedRecord{ID: "sony_lei", Data: map[string]any{"id": "sony_lei", "name": "Sony Group Corp", "description": "LEI 529900R5WX9N2OI2N910", "status": "active"}})
	recsentity.Items = append(recsentity.Items, seedRecord{ID: "apple_lei", Data: map[string]any{"id": "apple_lei", "name": "Apple Inc", "description": "LEI HWUPKR0MPOU8FGXBT394", "status": "active"}})
	def.Records = append(def.Records, recsentity)
	recslei := seedCollection{Collection: "ai.gftd.apps.legalentity.lei"}
	recslei.Items = append(recslei.Items, seedRecord{ID: "jpmorgan", Data: map[string]any{"id": "jpmorgan", "name": "JPMorgan Chase", "description": "LEI 8I5DZWZKVSZI1NUHU748", "status": "active"}})
	def.Records = append(def.Records, recslei)
	return def
}

func LifeEventGapSeeds() seedDef {
	def := seedDef{Domain: "life-event", Nanoid: "life3f74", DID: "did:web:life-event.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "event:birth", DisplayName: "誕生", Description: "Birth"})
	def.DIDs = append(def.DIDs, seedDID{Path: "event:enrollment", DisplayName: "入学", Description: "School enrollment"})
	def.DIDs = append(def.DIDs, seedDID{Path: "event:graduation", DisplayName: "卒業", Description: "Graduation"})
	def.DIDs = append(def.DIDs, seedDID{Path: "event:employment", DisplayName: "就職", Description: "Employment"})
	def.DIDs = append(def.DIDs, seedDID{Path: "event:marriage", DisplayName: "結婚", Description: "Marriage"})
	def.DIDs = append(def.DIDs, seedDID{Path: "event:retirement", DisplayName: "退職", Description: "Retirement"})
	recsevent := seedCollection{Collection: "ai.gftd.apps.lifeevent.event"}
	recsevent.Items = append(recsevent.Items, seedRecord{ID: "birth", Data: map[string]any{"id": "birth", "name": "誕生", "description": "Birth", "status": "active"}})
	recsevent.Items = append(recsevent.Items, seedRecord{ID: "enrollment", Data: map[string]any{"id": "enrollment", "name": "入学", "description": "School enrollment", "status": "active"}})
	recsevent.Items = append(recsevent.Items, seedRecord{ID: "graduation", Data: map[string]any{"id": "graduation", "name": "卒業", "description": "Graduation", "status": "active"}})
	recsevent.Items = append(recsevent.Items, seedRecord{ID: "employment", Data: map[string]any{"id": "employment", "name": "就職", "description": "Employment", "status": "active"}})
	recsevent.Items = append(recsevent.Items, seedRecord{ID: "marriage", Data: map[string]any{"id": "marriage", "name": "結婚", "description": "Marriage", "status": "active"}})
	recsevent.Items = append(recsevent.Items, seedRecord{ID: "retirement", Data: map[string]any{"id": "retirement", "name": "退職", "description": "Retirement", "status": "active"}})
	def.Records = append(def.Records, recsevent)
	return def
}

func LoanGapSeeds() seedDef {
	def := seedDef{Domain: "loan", Nanoid: "lo4hs8rw", DID: "did:web:loan.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "loan:mortgage_35y", DisplayName: "住宅ローン35年固定", Description: "35-year fixed mortgage"})
	def.DIDs = append(def.DIDs, seedDID{Path: "loan:car_loan", DisplayName: "自動車ローン", Description: "Auto loan"})
	def.DIDs = append(def.DIDs, seedDID{Path: "loan:student_loan", DisplayName: "奨学金", Description: "Student loan"})
	def.DIDs = append(def.DIDs, seedDID{Path: "loan:business_loan", DisplayName: "事業融資", Description: "Business loan"})
	def.DIDs = append(def.DIDs, seedDID{Path: "loan:personal_loan", DisplayName: "カードローン", Description: "Personal loan"})
	recsloan := seedCollection{Collection: "ai.gftd.apps.loan.loan"}
	recsloan.Items = append(recsloan.Items, seedRecord{ID: "mortgage_35y", Data: map[string]any{"id": "mortgage_35y", "name": "住宅ローン35年固定", "description": "35-year fixed mortgage", "status": "active"}})
	recsloan.Items = append(recsloan.Items, seedRecord{ID: "car_loan", Data: map[string]any{"id": "car_loan", "name": "自動車ローン", "description": "Auto loan", "status": "active"}})
	recsloan.Items = append(recsloan.Items, seedRecord{ID: "student_loan", Data: map[string]any{"id": "student_loan", "name": "奨学金", "description": "Student loan", "status": "active"}})
	recsloan.Items = append(recsloan.Items, seedRecord{ID: "business_loan", Data: map[string]any{"id": "business_loan", "name": "事業融資", "description": "Business loan", "status": "active"}})
	recsloan.Items = append(recsloan.Items, seedRecord{ID: "personal_loan", Data: map[string]any{"id": "personal_loan", "name": "カードローン", "description": "Personal loan", "status": "active"}})
	def.Records = append(def.Records, recsloan)
	return def
}

func MacGapSeeds() seedDef {
	def := seedDef{Domain: "mac", Nanoid: "mac82c7", DID: "did:web:mac.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "mac:apple_oui", DisplayName: "Apple OUI", Description: "MAC prefix AC:DE:48"})
	def.DIDs = append(def.DIDs, seedDID{Path: "mac:intel_oui", DisplayName: "Intel OUI", Description: "MAC prefix 00:1B:21"})
	def.DIDs = append(def.DIDs, seedDID{Path: "mac:cisco_oui", DisplayName: "Cisco OUI", Description: "MAC prefix 00:1A:A1"})
	def.DIDs = append(def.DIDs, seedDID{Path: "mac:samsung_oui", DisplayName: "Samsung OUI", Description: "MAC prefix 00:07:AB"})
	def.DIDs = append(def.DIDs, seedDID{Path: "mac:huawei_oui", DisplayName: "Huawei OUI", Description: "MAC prefix 00:E0:FC"})
	recsmac := seedCollection{Collection: "ai.gftd.apps.mac.mac"}
	recsmac.Items = append(recsmac.Items, seedRecord{ID: "apple_oui", Data: map[string]any{"id": "apple_oui", "name": "Apple OUI", "description": "MAC prefix AC:DE:48", "status": "active"}})
	recsmac.Items = append(recsmac.Items, seedRecord{ID: "intel_oui", Data: map[string]any{"id": "intel_oui", "name": "Intel OUI", "description": "MAC prefix 00:1B:21", "status": "active"}})
	recsmac.Items = append(recsmac.Items, seedRecord{ID: "cisco_oui", Data: map[string]any{"id": "cisco_oui", "name": "Cisco OUI", "description": "MAC prefix 00:1A:A1", "status": "active"}})
	recsmac.Items = append(recsmac.Items, seedRecord{ID: "samsung_oui", Data: map[string]any{"id": "samsung_oui", "name": "Samsung OUI", "description": "MAC prefix 00:07:AB", "status": "active"}})
	recsmac.Items = append(recsmac.Items, seedRecord{ID: "huawei_oui", Data: map[string]any{"id": "huawei_oui", "name": "Huawei OUI", "description": "MAC prefix 00:E0:FC", "status": "active"}})
	def.Records = append(def.Records, recsmac)
	return def
}

func MapsGapSeeds() seedDef {
	def := seedDef{Domain: "maps", Nanoid: "uqpel6i6", DID: "did:web:maps.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "location:tokyo_tower", DisplayName: "東京タワー", Description: "35.6586N, 139.7454E"})
	def.DIDs = append(def.DIDs, seedDID{Path: "building:tokyo_skytree", DisplayName: "東京スカイツリー", Description: "634m broadcasting tower"})
	def.DIDs = append(def.DIDs, seedDID{Path: "poi:shibuya_crossing", DisplayName: "渋谷スクランブル交差点", Description: "Famous intersection"})
	def.DIDs = append(def.DIDs, seedDID{Path: "location:mt_fuji", DisplayName: "富士山", Description: "3776m, highest peak in Japan"})
	def.DIDs = append(def.DIDs, seedDID{Path: "poi:fushimi_inari", DisplayName: "伏見稲荷大社", Description: "Kyoto shrine"})
	recslocation := seedCollection{Collection: "ai.gftd.apps.maps.location"}
	recslocation.Items = append(recslocation.Items, seedRecord{ID: "tokyo_tower", Data: map[string]any{"id": "tokyo_tower", "name": "東京タワー", "description": "35.6586N, 139.7454E", "status": "active"}})
	recslocation.Items = append(recslocation.Items, seedRecord{ID: "mt_fuji", Data: map[string]any{"id": "mt_fuji", "name": "富士山", "description": "3776m, highest peak in Japan", "status": "active"}})
	def.Records = append(def.Records, recslocation)
	recsbuilding := seedCollection{Collection: "ai.gftd.apps.maps.building"}
	recsbuilding.Items = append(recsbuilding.Items, seedRecord{ID: "tokyo_skytree", Data: map[string]any{"id": "tokyo_skytree", "name": "東京スカイツリー", "description": "634m broadcasting tower", "status": "active"}})
	def.Records = append(def.Records, recsbuilding)
	recspoi := seedCollection{Collection: "ai.gftd.apps.maps.poi"}
	recspoi.Items = append(recspoi.Items, seedRecord{ID: "shibuya_crossing", Data: map[string]any{"id": "shibuya_crossing", "name": "渋谷スクランブル交差点", "description": "Famous intersection", "status": "active"}})
	recspoi.Items = append(recspoi.Items, seedRecord{ID: "fushimi_inari", Data: map[string]any{"id": "fushimi_inari", "name": "伏見稲荷大社", "description": "Kyoto shrine", "status": "active"}})
	def.Records = append(def.Records, recspoi)
	return def
}

func MediaAnimeGapSeeds() seedDef {
	def := seedDef{Domain: "media-anime", Nanoid: "pd3juk85", DID: "did:web:media-anime.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "title:demon_slayer", DisplayName: "鬼滅の刃", Description: "Kimetsu no Yaiba"})
	def.DIDs = append(def.DIDs, seedDID{Path: "title:jjk", DisplayName: "呪術廻戦", Description: "Jujutsu Kaisen"})
	def.DIDs = append(def.DIDs, seedDID{Path: "title:spy_family", DisplayName: "SPY×FAMILY", Description: "SPY x FAMILY"})
	def.DIDs = append(def.DIDs, seedDID{Path: "title:one_piece", DisplayName: "ONE PIECE", Description: "One Piece"})
	def.DIDs = append(def.DIDs, seedDID{Path: "title:chainsaw_man", DisplayName: "チェンソーマン", Description: "Chainsaw Man"})
	recstitle := seedCollection{Collection: "ai.gftd.apps.mediaanime.title"}
	recstitle.Items = append(recstitle.Items, seedRecord{ID: "demon_slayer", Data: map[string]any{"id": "demon_slayer", "name": "鬼滅の刃", "description": "Kimetsu no Yaiba", "status": "active"}})
	recstitle.Items = append(recstitle.Items, seedRecord{ID: "jjk", Data: map[string]any{"id": "jjk", "name": "呪術廻戦", "description": "Jujutsu Kaisen", "status": "active"}})
	recstitle.Items = append(recstitle.Items, seedRecord{ID: "spy_family", Data: map[string]any{"id": "spy_family", "name": "SPY×FAMILY", "description": "SPY x FAMILY", "status": "active"}})
	recstitle.Items = append(recstitle.Items, seedRecord{ID: "one_piece", Data: map[string]any{"id": "one_piece", "name": "ONE PIECE", "description": "One Piece", "status": "active"}})
	recstitle.Items = append(recstitle.Items, seedRecord{ID: "chainsaw_man", Data: map[string]any{"id": "chainsaw_man", "name": "チェンソーマン", "description": "Chainsaw Man", "status": "active"}})
	def.Records = append(def.Records, recstitle)
	return def
}

func MediaGamersGapSeeds() seedDef {
	def := seedDef{Domain: "media-gamers", Nanoid: "media656", DID: "did:web:media-gamers.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "game:zelda_totk", DisplayName: "ゼルダの伝説 TotK", Description: "Tears of the Kingdom"})
	def.DIDs = append(def.DIDs, seedDID{Path: "game:ff16", DisplayName: "FINAL FANTASY XVI", Description: "Final Fantasy 16"})
	def.DIDs = append(def.DIDs, seedDID{Path: "game:elden_ring", DisplayName: "ELDEN RING", Description: "Elden Ring"})
	def.DIDs = append(def.DIDs, seedDID{Path: "game:persona5", DisplayName: "ペルソナ5", Description: "Persona 5 Royal"})
	def.DIDs = append(def.DIDs, seedDID{Path: "game:mh_wilds", DisplayName: "モンスターハンター ワイルズ", Description: "Monster Hunter Wilds"})
	recsgame := seedCollection{Collection: "ai.gftd.apps.mediagamers.game"}
	recsgame.Items = append(recsgame.Items, seedRecord{ID: "zelda_totk", Data: map[string]any{"id": "zelda_totk", "name": "ゼルダの伝説 TotK", "description": "Tears of the Kingdom", "status": "active"}})
	recsgame.Items = append(recsgame.Items, seedRecord{ID: "ff16", Data: map[string]any{"id": "ff16", "name": "FINAL FANTASY XVI", "description": "Final Fantasy 16", "status": "active"}})
	recsgame.Items = append(recsgame.Items, seedRecord{ID: "elden_ring", Data: map[string]any{"id": "elden_ring", "name": "ELDEN RING", "description": "Elden Ring", "status": "active"}})
	recsgame.Items = append(recsgame.Items, seedRecord{ID: "persona5", Data: map[string]any{"id": "persona5", "name": "ペルソナ5", "description": "Persona 5 Royal", "status": "active"}})
	recsgame.Items = append(recsgame.Items, seedRecord{ID: "mh_wilds", Data: map[string]any{"id": "mh_wilds", "name": "モンスターハンター ワイルズ", "description": "Monster Hunter Wilds", "status": "active"}})
	def.Records = append(def.Records, recsgame)
	return def
}

func MenkyoGapSeeds() seedDef {
	def := seedDef{Domain: "menkyo", Nanoid: "mk4yo01", DID: "did:web:menkyo.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "license:futsu_unten", DisplayName: "普通自動車免許", Description: "Standard driver license"})
	def.DIDs = append(def.DIDs, seedDID{Path: "license:oogata", DisplayName: "大型自動車免許", Description: "Heavy vehicle license"})
	def.DIDs = append(def.DIDs, seedDID{Path: "license:nirin", DisplayName: "普通二輪免許", Description: "Motorcycle license"})
	def.DIDs = append(def.DIDs, seedDID{Path: "license:ishi", DisplayName: "医師免許", Description: "Medical doctor license"})
	def.DIDs = append(def.DIDs, seedDID{Path: "license:bengoshi", DisplayName: "弁護士資格", Description: "Bar admission"})
	recslicense := seedCollection{Collection: "ai.gftd.apps.menkyo.license"}
	recslicense.Items = append(recslicense.Items, seedRecord{ID: "futsu_unten", Data: map[string]any{"id": "futsu_unten", "name": "普通自動車免許", "description": "Standard driver license", "status": "active"}})
	recslicense.Items = append(recslicense.Items, seedRecord{ID: "oogata", Data: map[string]any{"id": "oogata", "name": "大型自動車免許", "description": "Heavy vehicle license", "status": "active"}})
	recslicense.Items = append(recslicense.Items, seedRecord{ID: "nirin", Data: map[string]any{"id": "nirin", "name": "普通二輪免許", "description": "Motorcycle license", "status": "active"}})
	recslicense.Items = append(recslicense.Items, seedRecord{ID: "ishi", Data: map[string]any{"id": "ishi", "name": "医師免許", "description": "Medical doctor license", "status": "active"}})
	recslicense.Items = append(recslicense.Items, seedRecord{ID: "bengoshi", Data: map[string]any{"id": "bengoshi", "name": "弁護士資格", "description": "Bar admission", "status": "active"}})
	def.Records = append(def.Records, recslicense)
	return def
}

func MineGapSeeds() seedDef {
	def := seedDef{Domain: "mine", Nanoid: "mn3rp6wz", DID: "did:web:mine.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "mine:pilbara_iron", DisplayName: "Pilbara Iron Ore Mine", Description: "Australia, iron ore"})
	def.DIDs = append(def.DIDs, seedDID{Path: "mine:escondida_copper", DisplayName: "Escondida Copper Mine", Description: "Chile, copper"})
	def.DIDs = append(def.DIDs, seedDID{Path: "mine:muruntau_gold", DisplayName: "Muruntau Gold Mine", Description: "Uzbekistan, gold"})
	def.DIDs = append(def.DIDs, seedDID{Path: "mine:jwaneng_diamond", DisplayName: "Jwaneng Diamond Mine", Description: "Botswana, diamond"})
	def.DIDs = append(def.DIDs, seedDID{Path: "mine:sumitomo_besshi", DisplayName: "住友別子銅山", Description: "Japan historic copper mine"})
	recsmine := seedCollection{Collection: "ai.gftd.apps.mine.mine"}
	recsmine.Items = append(recsmine.Items, seedRecord{ID: "pilbara_iron", Data: map[string]any{"id": "pilbara_iron", "name": "Pilbara Iron Ore Mine", "description": "Australia, iron ore", "status": "active"}})
	recsmine.Items = append(recsmine.Items, seedRecord{ID: "escondida_copper", Data: map[string]any{"id": "escondida_copper", "name": "Escondida Copper Mine", "description": "Chile, copper", "status": "active"}})
	recsmine.Items = append(recsmine.Items, seedRecord{ID: "muruntau_gold", Data: map[string]any{"id": "muruntau_gold", "name": "Muruntau Gold Mine", "description": "Uzbekistan, gold", "status": "active"}})
	recsmine.Items = append(recsmine.Items, seedRecord{ID: "jwaneng_diamond", Data: map[string]any{"id": "jwaneng_diamond", "name": "Jwaneng Diamond Mine", "description": "Botswana, diamond", "status": "active"}})
	recsmine.Items = append(recsmine.Items, seedRecord{ID: "sumitomo_besshi", Data: map[string]any{"id": "sumitomo_besshi", "name": "住友別子銅山", "description": "Japan historic copper mine", "status": "active"}})
	def.Records = append(def.Records, recsmine)
	return def
}

func MinpakuGapSeeds() seedDef {
	def := seedDef{Domain: "minpaku", Nanoid: "mp7k9x2w", DID: "did:web:minpaku.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "listing:shibuya_apt", DisplayName: "渋谷アパートメント", Description: "Shibuya vacation rental"})
	def.DIDs = append(def.DIDs, seedDID{Path: "listing:kyoto_machiya", DisplayName: "京都町家", Description: "Kyoto traditional house"})
	def.DIDs = append(def.DIDs, seedDID{Path: "listing:hakone_onsen", DisplayName: "箱根温泉宿", Description: "Hakone hot spring rental"})
	def.DIDs = append(def.DIDs, seedDID{Path: "listing:okinawa_villa", DisplayName: "沖縄ヴィラ", Description: "Okinawa beach villa"})
	def.DIDs = append(def.DIDs, seedDID{Path: "listing:niseko_chalet", DisplayName: "ニセコシャレー", Description: "Niseko ski chalet"})
	recslisting := seedCollection{Collection: "ai.gftd.apps.minpaku.listing"}
	recslisting.Items = append(recslisting.Items, seedRecord{ID: "shibuya_apt", Data: map[string]any{"id": "shibuya_apt", "name": "渋谷アパートメント", "description": "Shibuya vacation rental", "status": "active"}})
	recslisting.Items = append(recslisting.Items, seedRecord{ID: "kyoto_machiya", Data: map[string]any{"id": "kyoto_machiya", "name": "京都町家", "description": "Kyoto traditional house", "status": "active"}})
	recslisting.Items = append(recslisting.Items, seedRecord{ID: "hakone_onsen", Data: map[string]any{"id": "hakone_onsen", "name": "箱根温泉宿", "description": "Hakone hot spring rental", "status": "active"}})
	recslisting.Items = append(recslisting.Items, seedRecord{ID: "okinawa_villa", Data: map[string]any{"id": "okinawa_villa", "name": "沖縄ヴィラ", "description": "Okinawa beach villa", "status": "active"}})
	recslisting.Items = append(recslisting.Items, seedRecord{ID: "niseko_chalet", Data: map[string]any{"id": "niseko_chalet", "name": "ニセコシャレー", "description": "Niseko ski chalet", "status": "active"}})
	def.Records = append(def.Records, recslisting)
	return def
}

func NaturalPersonGapSeeds() seedDef {
	def := seedDef{Domain: "natural-person", Nanoid: "np01priv8", DID: "did:web:natural-person.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "person:natural_person_001", DisplayName: "Natural Person", Description: "natural-person person"})
	recsperson := seedCollection{Collection: "ai.gftd.apps.naturalperson.person"}
	recsperson.Items = append(recsperson.Items, seedRecord{ID: "natural_person_001", Data: map[string]any{"id": "natural_person_001", "name": "Natural Person", "description": "natural-person person", "status": "active"}})
	def.Records = append(def.Records, recsperson)
	return def
}

func NdcGapSeeds() seedDef {
	def := seedDef{Domain: "ndc", Nanoid: "nd7c3k9m", DID: "did:web:ndc.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "drug:aspirin", DisplayName: "アスピリン", Description: "ATC B01AC06, antipyretic analgesic"})
	def.DIDs = append(def.DIDs, seedDID{Path: "drug:metformin", DisplayName: "メトホルミン", Description: "ATC A10BA02, antidiabetic"})
	def.DIDs = append(def.DIDs, seedDID{Path: "drug:atorvastatin", DisplayName: "アトルバスタチン", Description: "ATC C10AA05, statin"})
	def.DIDs = append(def.DIDs, seedDID{Path: "drug:omeprazole", DisplayName: "オメプラゾール", Description: "ATC A02BC01, PPI"})
	def.DIDs = append(def.DIDs, seedDID{Path: "drug:amoxicillin", DisplayName: "アモキシシリン", Description: "ATC J01CA04, antibiotic"})
	recsdrug := seedCollection{Collection: "ai.gftd.apps.ndc.drug"}
	recsdrug.Items = append(recsdrug.Items, seedRecord{ID: "aspirin", Data: map[string]any{"id": "aspirin", "name": "アスピリン", "description": "ATC B01AC06, antipyretic analgesic", "status": "active"}})
	recsdrug.Items = append(recsdrug.Items, seedRecord{ID: "metformin", Data: map[string]any{"id": "metformin", "name": "メトホルミン", "description": "ATC A10BA02, antidiabetic", "status": "active"}})
	recsdrug.Items = append(recsdrug.Items, seedRecord{ID: "atorvastatin", Data: map[string]any{"id": "atorvastatin", "name": "アトルバスタチン", "description": "ATC C10AA05, statin", "status": "active"}})
	recsdrug.Items = append(recsdrug.Items, seedRecord{ID: "omeprazole", Data: map[string]any{"id": "omeprazole", "name": "オメプラゾール", "description": "ATC A02BC01, PPI", "status": "active"}})
	recsdrug.Items = append(recsdrug.Items, seedRecord{ID: "amoxicillin", Data: map[string]any{"id": "amoxicillin", "name": "アモキシシリン", "description": "ATC J01CA04, antibiotic", "status": "active"}})
	def.Records = append(def.Records, recsdrug)
	return def
}

func NijisousakuGapSeeds() seedDef {
	def := seedDef{Domain: "nijisousaku", Nanoid: "nj4sk01", DID: "did:web:nijisousaku.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "work:doujin_001", DisplayName: "同人誌001", Description: "Fan-created manga"})
	def.DIDs = append(def.DIDs, seedDID{Path: "work:cosplay_001", DisplayName: "コスプレ作品001", Description: "Cosplay creation"})
	def.DIDs = append(def.DIDs, seedDID{Path: "work:fanfic_001", DisplayName: "二次小説001", Description: "Fan fiction"})
	def.DIDs = append(def.DIDs, seedDID{Path: "work:mmd_001", DisplayName: "MMD作品001", Description: "MikuMikuDance creation"})
	def.DIDs = append(def.DIDs, seedDID{Path: "work:fanart_001", DisplayName: "ファンアート001", Description: "Fan illustration"})
	recswork := seedCollection{Collection: "ai.gftd.apps.nijisousaku.work"}
	recswork.Items = append(recswork.Items, seedRecord{ID: "doujin_001", Data: map[string]any{"id": "doujin_001", "name": "同人誌001", "description": "Fan-created manga", "status": "active"}})
	recswork.Items = append(recswork.Items, seedRecord{ID: "cosplay_001", Data: map[string]any{"id": "cosplay_001", "name": "コスプレ作品001", "description": "Cosplay creation", "status": "active"}})
	recswork.Items = append(recswork.Items, seedRecord{ID: "fanfic_001", Data: map[string]any{"id": "fanfic_001", "name": "二次小説001", "description": "Fan fiction", "status": "active"}})
	recswork.Items = append(recswork.Items, seedRecord{ID: "mmd_001", Data: map[string]any{"id": "mmd_001", "name": "MMD作品001", "description": "MikuMikuDance creation", "status": "active"}})
	recswork.Items = append(recswork.Items, seedRecord{ID: "fanart_001", Data: map[string]any{"id": "fanart_001", "name": "ファンアート001", "description": "Fan illustration", "status": "active"}})
	def.Records = append(def.Records, recswork)
	return def
}

func NimotsuGapSeeds() seedDef {
	def := seedDef{Domain: "nimotsu", Nanoid: "nm4ts01", DID: "did:web:nimotsu.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "parcel:yamato_001", DisplayName: "ヤマト宅急便001", Description: "Yamato parcel delivery"})
	def.DIDs = append(def.DIDs, seedDID{Path: "parcel:sagawa_001", DisplayName: "佐川急便001", Description: "Sagawa express delivery"})
	def.DIDs = append(def.DIDs, seedDID{Path: "parcel:jppost_001", DisplayName: "ゆうパック001", Description: "Japan Post parcel"})
	def.DIDs = append(def.DIDs, seedDID{Path: "parcel:fedex_001", DisplayName: "FedEx International", Description: "International express"})
	def.DIDs = append(def.DIDs, seedDID{Path: "parcel:dhl_001", DisplayName: "DHL Express", Description: "International courier"})
	recsparcel := seedCollection{Collection: "ai.gftd.apps.nimotsu.parcel"}
	recsparcel.Items = append(recsparcel.Items, seedRecord{ID: "yamato_001", Data: map[string]any{"id": "yamato_001", "name": "ヤマト宅急便001", "description": "Yamato parcel delivery", "status": "active"}})
	recsparcel.Items = append(recsparcel.Items, seedRecord{ID: "sagawa_001", Data: map[string]any{"id": "sagawa_001", "name": "佐川急便001", "description": "Sagawa express delivery", "status": "active"}})
	recsparcel.Items = append(recsparcel.Items, seedRecord{ID: "jppost_001", Data: map[string]any{"id": "jppost_001", "name": "ゆうパック001", "description": "Japan Post parcel", "status": "active"}})
	recsparcel.Items = append(recsparcel.Items, seedRecord{ID: "fedex_001", Data: map[string]any{"id": "fedex_001", "name": "FedEx International", "description": "International express", "status": "active"}})
	recsparcel.Items = append(recsparcel.Items, seedRecord{ID: "dhl_001", Data: map[string]any{"id": "dhl_001", "name": "DHL Express", "description": "International courier", "status": "active"}})
	def.Records = append(def.Records, recsparcel)
	return def
}

func NirinGapSeeds() seedDef {
	def := seedDef{Domain: "nirin", Nanoid: "nr4in01", DID: "did:web:nirin.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "vehicle:honda_cbr", DisplayName: "Honda CBR250RR", Description: "Sport motorcycle"})
	def.DIDs = append(def.DIDs, seedDID{Path: "vehicle:yamaha_mt", DisplayName: "Yamaha MT-07", Description: "Naked motorcycle"})
	def.DIDs = append(def.DIDs, seedDID{Path: "vehicle:kawasaki_ninja", DisplayName: "Kawasaki Ninja 400", Description: "Sport motorcycle"})
	def.DIDs = append(def.DIDs, seedDID{Path: "vehicle:suzuki_gsx", DisplayName: "Suzuki GSX-R750", Description: "Supersport"})
	def.DIDs = append(def.DIDs, seedDID{Path: "vehicle:honda_supercub", DisplayName: "Honda Super Cub", Description: "Commuter motorcycle"})
	recsvehicle := seedCollection{Collection: "ai.gftd.apps.nirin.vehicle"}
	recsvehicle.Items = append(recsvehicle.Items, seedRecord{ID: "honda_cbr", Data: map[string]any{"id": "honda_cbr", "name": "Honda CBR250RR", "description": "Sport motorcycle", "status": "active"}})
	recsvehicle.Items = append(recsvehicle.Items, seedRecord{ID: "yamaha_mt", Data: map[string]any{"id": "yamaha_mt", "name": "Yamaha MT-07", "description": "Naked motorcycle", "status": "active"}})
	recsvehicle.Items = append(recsvehicle.Items, seedRecord{ID: "kawasaki_ninja", Data: map[string]any{"id": "kawasaki_ninja", "name": "Kawasaki Ninja 400", "description": "Sport motorcycle", "status": "active"}})
	recsvehicle.Items = append(recsvehicle.Items, seedRecord{ID: "suzuki_gsx", Data: map[string]any{"id": "suzuki_gsx", "name": "Suzuki GSX-R750", "description": "Supersport", "status": "active"}})
	recsvehicle.Items = append(recsvehicle.Items, seedRecord{ID: "honda_supercub", Data: map[string]any{"id": "honda_supercub", "name": "Honda Super Cub", "description": "Commuter motorcycle", "status": "active"}})
	def.Records = append(def.Records, recsvehicle)
	return def
}

func NougyouGapSeeds() seedDef {
	def := seedDef{Domain: "nougyou", Nanoid: "ng4yu01", DID: "did:web:nougyou.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "coop:ja_hokkaido", DisplayName: "JA北海道", Description: "Hokkaido agricultural coop"})
	def.DIDs = append(def.DIDs, seedDID{Path: "coop:ja_niigata", DisplayName: "JA新潟", Description: "Niigata agricultural coop"})
	def.DIDs = append(def.DIDs, seedDID{Path: "cycle:rice_niigata_2024", DisplayName: "新潟コシヒカリ2024", Description: "Rice harvest cycle"})
	def.DIDs = append(def.DIDs, seedDID{Path: "coop:ja_shizuoka", DisplayName: "JA静岡", Description: "Shizuoka agricultural coop"})
	def.DIDs = append(def.DIDs, seedDID{Path: "coop:ja_kagoshima", DisplayName: "JA鹿児島", Description: "Kagoshima agricultural coop"})
	recscoop := seedCollection{Collection: "ai.gftd.apps.nougyou.coop"}
	recscoop.Items = append(recscoop.Items, seedRecord{ID: "ja_hokkaido", Data: map[string]any{"id": "ja_hokkaido", "name": "JA北海道", "description": "Hokkaido agricultural coop", "status": "active"}})
	recscoop.Items = append(recscoop.Items, seedRecord{ID: "ja_niigata", Data: map[string]any{"id": "ja_niigata", "name": "JA新潟", "description": "Niigata agricultural coop", "status": "active"}})
	recscoop.Items = append(recscoop.Items, seedRecord{ID: "ja_shizuoka", Data: map[string]any{"id": "ja_shizuoka", "name": "JA静岡", "description": "Shizuoka agricultural coop", "status": "active"}})
	recscoop.Items = append(recscoop.Items, seedRecord{ID: "ja_kagoshima", Data: map[string]any{"id": "ja_kagoshima", "name": "JA鹿児島", "description": "Kagoshima agricultural coop", "status": "active"}})
	def.Records = append(def.Records, recscoop)
	recscycle := seedCollection{Collection: "ai.gftd.apps.nougyou.cycle"}
	recscycle.Items = append(recscycle.Items, seedRecord{ID: "rice_niigata_2024", Data: map[string]any{"id": "rice_niigata_2024", "name": "新潟コシヒカリ2024", "description": "Rice harvest cycle", "status": "active"}})
	def.Records = append(def.Records, recscycle)
	return def
}

func NpoGapSeeds() seedDef {
	def := seedDef{Domain: "npo", Nanoid: "np4or01", DID: "did:web:npo.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "org:msf", DisplayName: "国境なき医師団", Description: "Doctors Without Borders"})
	def.DIDs = append(def.DIDs, seedDID{Path: "org:wwf", DisplayName: "世界自然保護基金", Description: "WWF"})
	def.DIDs = append(def.DIDs, seedDID{Path: "org:redcross_jp", DisplayName: "日本赤十字社", Description: "Japanese Red Cross"})
	def.DIDs = append(def.DIDs, seedDID{Path: "org:unicef", DisplayName: "UNICEF", Description: "United Nations Children's Fund"})
	def.DIDs = append(def.DIDs, seedDID{Path: "org:greenpeace", DisplayName: "グリーンピース", Description: "Greenpeace"})
	recsorg := seedCollection{Collection: "ai.gftd.apps.npo.org"}
	recsorg.Items = append(recsorg.Items, seedRecord{ID: "msf", Data: map[string]any{"id": "msf", "name": "国境なき医師団", "description": "Doctors Without Borders", "status": "active"}})
	recsorg.Items = append(recsorg.Items, seedRecord{ID: "wwf", Data: map[string]any{"id": "wwf", "name": "世界自然保護基金", "description": "WWF", "status": "active"}})
	recsorg.Items = append(recsorg.Items, seedRecord{ID: "redcross_jp", Data: map[string]any{"id": "redcross_jp", "name": "日本赤十字社", "description": "Japanese Red Cross", "status": "active"}})
	recsorg.Items = append(recsorg.Items, seedRecord{ID: "unicef", Data: map[string]any{"id": "unicef", "name": "UNICEF", "description": "United Nations Children's Fund", "status": "active"}})
	recsorg.Items = append(recsorg.Items, seedRecord{ID: "greenpeace", Data: map[string]any{"id": "greenpeace", "name": "グリーンピース", "description": "Greenpeace", "status": "active"}})
	def.Records = append(def.Records, recsorg)
	return def
}

func OmatsuriGapSeeds() seedDef {
	def := seedDef{Domain: "omatsuri", Nanoid: "mt5r1f8k", DID: "did:web:omatsuri.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "festival:yoga_retreat", DisplayName: "ヨガリトリート", Description: "Wellness yoga retreat"})
	def.DIDs = append(def.DIDs, seedDID{Path: "festival:forest_bathing", DisplayName: "森林浴イベント", Description: "Shinrin-yoku event"})
	def.DIDs = append(def.DIDs, seedDID{Path: "festival:onsen_fest", DisplayName: "温泉フェスティバル", Description: "Hot spring wellness festival"})
	def.DIDs = append(def.DIDs, seedDID{Path: "festival:meditation", DisplayName: "瞑想会", Description: "Meditation gathering"})
	def.DIDs = append(def.DIDs, seedDID{Path: "festival:zen_retreat", DisplayName: "禅リトリート", Description: "Zen retreat event"})
	recsfestival := seedCollection{Collection: "ai.gftd.apps.omatsuri.festival"}
	recsfestival.Items = append(recsfestival.Items, seedRecord{ID: "yoga_retreat", Data: map[string]any{"id": "yoga_retreat", "name": "ヨガリトリート", "description": "Wellness yoga retreat", "status": "active"}})
	recsfestival.Items = append(recsfestival.Items, seedRecord{ID: "forest_bathing", Data: map[string]any{"id": "forest_bathing", "name": "森林浴イベント", "description": "Shinrin-yoku event", "status": "active"}})
	recsfestival.Items = append(recsfestival.Items, seedRecord{ID: "onsen_fest", Data: map[string]any{"id": "onsen_fest", "name": "温泉フェスティバル", "description": "Hot spring wellness festival", "status": "active"}})
	recsfestival.Items = append(recsfestival.Items, seedRecord{ID: "meditation", Data: map[string]any{"id": "meditation", "name": "瞑想会", "description": "Meditation gathering", "status": "active"}})
	recsfestival.Items = append(recsfestival.Items, seedRecord{ID: "zen_retreat", Data: map[string]any{"id": "zen_retreat", "name": "禅リトリート", "description": "Zen retreat event", "status": "active"}})
	def.Records = append(def.Records, recsfestival)
	return def
}

func OtoshimonoGapSeeds() seedDef {
	def := seedDef{Domain: "otoshimono", Nanoid: "ot0sh1m0", DID: "did:web:otoshimono.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "item:wallet_tokyo", DisplayName: "財布（東京駅）", Description: "Lost wallet at Tokyo Station"})
	def.DIDs = append(def.DIDs, seedDID{Path: "item:umbrella_shibuya", DisplayName: "傘（渋谷駅）", Description: "Lost umbrella at Shibuya"})
	def.DIDs = append(def.DIDs, seedDID{Path: "item:phone_shinjuku", DisplayName: "スマートフォン（新宿駅）", Description: "Lost phone at Shinjuku"})
	def.DIDs = append(def.DIDs, seedDID{Path: "item:key_ikebukuro", DisplayName: "鍵（池袋駅）", Description: "Lost keys at Ikebukuro"})
	def.DIDs = append(def.DIDs, seedDID{Path: "item:bag_ueno", DisplayName: "カバン（上野駅）", Description: "Lost bag at Ueno Station"})
	recsitem := seedCollection{Collection: "ai.gftd.apps.otoshimono.item"}
	recsitem.Items = append(recsitem.Items, seedRecord{ID: "wallet_tokyo", Data: map[string]any{"id": "wallet_tokyo", "name": "財布（東京駅）", "description": "Lost wallet at Tokyo Station", "status": "active"}})
	recsitem.Items = append(recsitem.Items, seedRecord{ID: "umbrella_shibuya", Data: map[string]any{"id": "umbrella_shibuya", "name": "傘（渋谷駅）", "description": "Lost umbrella at Shibuya", "status": "active"}})
	recsitem.Items = append(recsitem.Items, seedRecord{ID: "phone_shinjuku", Data: map[string]any{"id": "phone_shinjuku", "name": "スマートフォン（新宿駅）", "description": "Lost phone at Shinjuku", "status": "active"}})
	recsitem.Items = append(recsitem.Items, seedRecord{ID: "key_ikebukuro", Data: map[string]any{"id": "key_ikebukuro", "name": "鍵（池袋駅）", "description": "Lost keys at Ikebukuro", "status": "active"}})
	recsitem.Items = append(recsitem.Items, seedRecord{ID: "bag_ueno", Data: map[string]any{"id": "bag_ueno", "name": "カバン（上野駅）", "description": "Lost bag at Ueno Station", "status": "active"}})
	def.Records = append(def.Records, recsitem)
	return def
}

func PassportGapSeeds() seedDef {
	def := seedDef{Domain: "passport", Nanoid: "pp4rt01", DID: "did:web:passport.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "passport:jpn_type", DisplayName: "日本国パスポート", Description: "Japanese passport"})
	def.DIDs = append(def.DIDs, seedDID{Path: "passport:usa_type", DisplayName: "US Passport", Description: "US passport"})
	def.DIDs = append(def.DIDs, seedDID{Path: "passport:gbr_type", DisplayName: "British Passport", Description: "UK passport"})
	def.DIDs = append(def.DIDs, seedDID{Path: "passport:deu_type", DisplayName: "German Passport", Description: "German passport"})
	def.DIDs = append(def.DIDs, seedDID{Path: "passport:sgp_type", DisplayName: "Singapore Passport", Description: "Singapore passport"})
	recspassport := seedCollection{Collection: "ai.gftd.apps.passport.passport"}
	recspassport.Items = append(recspassport.Items, seedRecord{ID: "jpn_type", Data: map[string]any{"id": "jpn_type", "name": "日本国パスポート", "description": "Japanese passport", "status": "active"}})
	recspassport.Items = append(recspassport.Items, seedRecord{ID: "usa_type", Data: map[string]any{"id": "usa_type", "name": "US Passport", "description": "US passport", "status": "active"}})
	recspassport.Items = append(recspassport.Items, seedRecord{ID: "gbr_type", Data: map[string]any{"id": "gbr_type", "name": "British Passport", "description": "UK passport", "status": "active"}})
	recspassport.Items = append(recspassport.Items, seedRecord{ID: "deu_type", Data: map[string]any{"id": "deu_type", "name": "German Passport", "description": "German passport", "status": "active"}})
	recspassport.Items = append(recspassport.Items, seedRecord{ID: "sgp_type", Data: map[string]any{"id": "sgp_type", "name": "Singapore Passport", "description": "Singapore passport", "status": "active"}})
	def.Records = append(def.Records, recspassport)
	return def
}

func PatentGapSeeds() seedDef {
	def := seedDef{Domain: "patent", Nanoid: "pa9wk4jf", DID: "did:web:patent.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "patent:us_smartphone", DisplayName: "US Smartphone Patent", Description: "US design patent"})
	def.DIDs = append(def.DIDs, seedDID{Path: "patent:jp_battery", DisplayName: "リチウム電池特許", Description: "JP battery patent"})
	def.DIDs = append(def.DIDs, seedDID{Path: "patent:ep_pharma", DisplayName: "EU Pharmaceutical Patent", Description: "EP drug patent"})
	def.DIDs = append(def.DIDs, seedDID{Path: "patent:cn_5g", DisplayName: "5G Standard Patent", Description: "CN telecom patent"})
	def.DIDs = append(def.DIDs, seedDID{Path: "patent:kr_display", DisplayName: "OLED Display Patent", Description: "KR display patent"})
	recspatent := seedCollection{Collection: "ai.gftd.apps.patent.patent"}
	recspatent.Items = append(recspatent.Items, seedRecord{ID: "us_smartphone", Data: map[string]any{"id": "us_smartphone", "name": "US Smartphone Patent", "description": "US design patent", "status": "active"}})
	recspatent.Items = append(recspatent.Items, seedRecord{ID: "jp_battery", Data: map[string]any{"id": "jp_battery", "name": "リチウム電池特許", "description": "JP battery patent", "status": "active"}})
	recspatent.Items = append(recspatent.Items, seedRecord{ID: "ep_pharma", Data: map[string]any{"id": "ep_pharma", "name": "EU Pharmaceutical Patent", "description": "EP drug patent", "status": "active"}})
	recspatent.Items = append(recspatent.Items, seedRecord{ID: "cn_5g", Data: map[string]any{"id": "cn_5g", "name": "5G Standard Patent", "description": "CN telecom patent", "status": "active"}})
	recspatent.Items = append(recspatent.Items, seedRecord{ID: "kr_display", Data: map[string]any{"id": "kr_display", "name": "OLED Display Patent", "description": "KR display patent", "status": "active"}})
	def.Records = append(def.Records, recspatent)
	return def
}

func PharmaGapSeeds() seedDef {
	def := seedDef{Domain: "pharma", Nanoid: "f0963b54", DID: "did:web:pharma.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "product:tylenol", DisplayName: "Tylenol", Description: "Acetaminophen OTC"})
	def.DIDs = append(def.DIDs, seedDID{Path: "product:lipitor", DisplayName: "Lipitor", Description: "Atorvastatin brand"})
	def.DIDs = append(def.DIDs, seedDID{Path: "product:humira", DisplayName: "Humira", Description: "Adalimumab biologic"})
	def.DIDs = append(def.DIDs, seedDID{Path: "product:keytruda", DisplayName: "Keytruda", Description: "Pembrolizumab immunotherapy"})
	def.DIDs = append(def.DIDs, seedDID{Path: "product:ozempic", DisplayName: "Ozempic", Description: "Semaglutide GLP-1"})
	recsproduct := seedCollection{Collection: "ai.gftd.apps.pharma.product"}
	recsproduct.Items = append(recsproduct.Items, seedRecord{ID: "tylenol", Data: map[string]any{"id": "tylenol", "name": "Tylenol", "description": "Acetaminophen OTC", "status": "active"}})
	recsproduct.Items = append(recsproduct.Items, seedRecord{ID: "lipitor", Data: map[string]any{"id": "lipitor", "name": "Lipitor", "description": "Atorvastatin brand", "status": "active"}})
	recsproduct.Items = append(recsproduct.Items, seedRecord{ID: "humira", Data: map[string]any{"id": "humira", "name": "Humira", "description": "Adalimumab biologic", "status": "active"}})
	recsproduct.Items = append(recsproduct.Items, seedRecord{ID: "keytruda", Data: map[string]any{"id": "keytruda", "name": "Keytruda", "description": "Pembrolizumab immunotherapy", "status": "active"}})
	recsproduct.Items = append(recsproduct.Items, seedRecord{ID: "ozempic", Data: map[string]any{"id": "ozempic", "name": "Ozempic", "description": "Semaglutide GLP-1", "status": "active"}})
	def.Records = append(def.Records, recsproduct)
	return def
}

func PhonenumberGapSeeds() seedDef {
	def := seedDef{Domain: "phonenumber", Nanoid: "pn6xt3hw", DID: "did:web:phonenumber.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "number:jp_110", DisplayName: "110", Description: "Japan police emergency"})
	def.DIDs = append(def.DIDs, seedDID{Path: "number:jp_119", DisplayName: "119", Description: "Japan fire/ambulance"})
	def.DIDs = append(def.DIDs, seedDID{Path: "number:us_911", DisplayName: "911", Description: "US emergency"})
	def.DIDs = append(def.DIDs, seedDID{Path: "number:uk_999", DisplayName: "999", Description: "UK emergency"})
	def.DIDs = append(def.DIDs, seedDID{Path: "number:eu_112", DisplayName: "112", Description: "EU emergency"})
	recsnumber := seedCollection{Collection: "ai.gftd.apps.phonenumber.number"}
	recsnumber.Items = append(recsnumber.Items, seedRecord{ID: "jp_110", Data: map[string]any{"id": "jp_110", "name": "110", "description": "Japan police emergency", "status": "active"}})
	recsnumber.Items = append(recsnumber.Items, seedRecord{ID: "jp_119", Data: map[string]any{"id": "jp_119", "name": "119", "description": "Japan fire/ambulance", "status": "active"}})
	recsnumber.Items = append(recsnumber.Items, seedRecord{ID: "us_911", Data: map[string]any{"id": "us_911", "name": "911", "description": "US emergency", "status": "active"}})
	recsnumber.Items = append(recsnumber.Items, seedRecord{ID: "uk_999", Data: map[string]any{"id": "uk_999", "name": "999", "description": "UK emergency", "status": "active"}})
	recsnumber.Items = append(recsnumber.Items, seedRecord{ID: "eu_112", Data: map[string]any{"id": "eu_112", "name": "112", "description": "EU emergency", "status": "active"}})
	def.Records = append(def.Records, recsnumber)
	return def
}

func PhotosGapSeeds() seedDef {
	def := seedDef{Domain: "photos", Nanoid: "krtjlccu", DID: "did:web:photos.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "photo:landscape_01", DisplayName: "Landscape Photo 01", Description: "Mountain landscape"})
	def.DIDs = append(def.DIDs, seedDID{Path: "photo:portrait_01", DisplayName: "Portrait Photo 01", Description: "Studio portrait"})
	def.DIDs = append(def.DIDs, seedDID{Path: "photo:aerial_01", DisplayName: "Aerial Photo 01", Description: "Drone aerial shot"})
	def.DIDs = append(def.DIDs, seedDID{Path: "photo:macro_01", DisplayName: "Macro Photo 01", Description: "Macro flower shot"})
	def.DIDs = append(def.DIDs, seedDID{Path: "photo:street_01", DisplayName: "Street Photo 01", Description: "Urban street photography"})
	recsphoto := seedCollection{Collection: "ai.gftd.apps.photos.photo"}
	recsphoto.Items = append(recsphoto.Items, seedRecord{ID: "landscape_01", Data: map[string]any{"id": "landscape_01", "name": "Landscape Photo 01", "description": "Mountain landscape", "status": "active"}})
	recsphoto.Items = append(recsphoto.Items, seedRecord{ID: "portrait_01", Data: map[string]any{"id": "portrait_01", "name": "Portrait Photo 01", "description": "Studio portrait", "status": "active"}})
	recsphoto.Items = append(recsphoto.Items, seedRecord{ID: "aerial_01", Data: map[string]any{"id": "aerial_01", "name": "Aerial Photo 01", "description": "Drone aerial shot", "status": "active"}})
	recsphoto.Items = append(recsphoto.Items, seedRecord{ID: "macro_01", Data: map[string]any{"id": "macro_01", "name": "Macro Photo 01", "description": "Macro flower shot", "status": "active"}})
	recsphoto.Items = append(recsphoto.Items, seedRecord{ID: "street_01", Data: map[string]any{"id": "street_01", "name": "Street Photo 01", "description": "Urban street photography", "status": "active"}})
	def.Records = append(def.Records, recsphoto)
	return def
}

func PortGapSeeds() seedDef {
	def := seedDef{Domain: "port", Nanoid: "pr8xn5jv", DID: "did:web:port.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "port:shanghai", DisplayName: "上海港", Description: "Port of Shanghai, China"})
	def.DIDs = append(def.DIDs, seedDID{Path: "port:singapore", DisplayName: "シンガポール港", Description: "Port of Singapore"})
	def.DIDs = append(def.DIDs, seedDID{Path: "port:rotterdam", DisplayName: "ロッテルダム港", Description: "Port of Rotterdam, Netherlands"})
	def.DIDs = append(def.DIDs, seedDID{Path: "port:shenzhen", DisplayName: "深圳港", Description: "Port of Shenzhen, China"})
	def.DIDs = append(def.DIDs, seedDID{Path: "port:busan", DisplayName: "釜山港", Description: "Port of Busan, South Korea"})
	def.DIDs = append(def.DIDs, seedDID{Path: "port:tokyo", DisplayName: "東京港", Description: "Port of Tokyo, Japan"})
	def.DIDs = append(def.DIDs, seedDID{Path: "port:los_angeles", DisplayName: "ロサンゼルス港", Description: "Port of Los Angeles, USA"})
	def.DIDs = append(def.DIDs, seedDID{Path: "port:hamburg", DisplayName: "ハンブルク港", Description: "Port of Hamburg, Germany"})
	recsport := seedCollection{Collection: "ai.gftd.apps.port.port"}
	recsport.Items = append(recsport.Items, seedRecord{ID: "shanghai", Data: map[string]any{"id": "shanghai", "name": "上海港", "description": "Port of Shanghai, China", "status": "active"}})
	recsport.Items = append(recsport.Items, seedRecord{ID: "singapore", Data: map[string]any{"id": "singapore", "name": "シンガポール港", "description": "Port of Singapore", "status": "active"}})
	recsport.Items = append(recsport.Items, seedRecord{ID: "rotterdam", Data: map[string]any{"id": "rotterdam", "name": "ロッテルダム港", "description": "Port of Rotterdam, Netherlands", "status": "active"}})
	recsport.Items = append(recsport.Items, seedRecord{ID: "shenzhen", Data: map[string]any{"id": "shenzhen", "name": "深圳港", "description": "Port of Shenzhen, China", "status": "active"}})
	recsport.Items = append(recsport.Items, seedRecord{ID: "busan", Data: map[string]any{"id": "busan", "name": "釜山港", "description": "Port of Busan, South Korea", "status": "active"}})
	recsport.Items = append(recsport.Items, seedRecord{ID: "tokyo", Data: map[string]any{"id": "tokyo", "name": "東京港", "description": "Port of Tokyo, Japan", "status": "active"}})
	recsport.Items = append(recsport.Items, seedRecord{ID: "los_angeles", Data: map[string]any{"id": "los_angeles", "name": "ロサンゼルス港", "description": "Port of Los Angeles, USA", "status": "active"}})
	recsport.Items = append(recsport.Items, seedRecord{ID: "hamburg", Data: map[string]any{"id": "hamburg", "name": "ハンブルク港", "description": "Port of Hamburg, Germany", "status": "active"}})
	def.Records = append(def.Records, recsport)
	return def
}

func PropertyGapSeeds() seedDef {
	def := seedDef{Domain: "property", Nanoid: "pt6rl2mv", DID: "did:web:property.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "parcel:manhattan_5th", DisplayName: "5th Ave Manhattan", Description: "Manhattan real estate"})
	def.DIDs = append(def.DIDs, seedDID{Path: "parcel:ginza_4chome", DisplayName: "銀座4丁目", Description: "Ginza prime property"})
	def.DIDs = append(def.DIDs, seedDID{Path: "parcel:mayfair_london", DisplayName: "Mayfair London", Description: "London prime property"})
	def.DIDs = append(def.DIDs, seedDID{Path: "parcel:omotesando", DisplayName: "表参道", Description: "Omotesando property"})
	def.DIDs = append(def.DIDs, seedDID{Path: "parcel:beverly_hills", DisplayName: "Beverly Hills", Description: "LA prime property"})
	recsparcel := seedCollection{Collection: "ai.gftd.apps.property.parcel"}
	recsparcel.Items = append(recsparcel.Items, seedRecord{ID: "manhattan_5th", Data: map[string]any{"id": "manhattan_5th", "name": "5th Ave Manhattan", "description": "Manhattan real estate", "status": "active"}})
	recsparcel.Items = append(recsparcel.Items, seedRecord{ID: "ginza_4chome", Data: map[string]any{"id": "ginza_4chome", "name": "銀座4丁目", "description": "Ginza prime property", "status": "active"}})
	recsparcel.Items = append(recsparcel.Items, seedRecord{ID: "mayfair_london", Data: map[string]any{"id": "mayfair_london", "name": "Mayfair London", "description": "London prime property", "status": "active"}})
	recsparcel.Items = append(recsparcel.Items, seedRecord{ID: "omotesando", Data: map[string]any{"id": "omotesando", "name": "表参道", "description": "Omotesando property", "status": "active"}})
	recsparcel.Items = append(recsparcel.Items, seedRecord{ID: "beverly_hills", Data: map[string]any{"id": "beverly_hills", "name": "Beverly Hills", "description": "LA prime property", "status": "active"}})
	def.Records = append(def.Records, recsparcel)
	return def
}

func RailwayGapSeeds() seedDef {
	def := seedDef{Domain: "railway", Nanoid: "rw6ts3mk", DID: "did:web:railway.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "station:tokyo", DisplayName: "東京駅", Description: "Tokyo Station, JR East"})
	def.DIDs = append(def.DIDs, seedDID{Path: "station:shinjuku", DisplayName: "新宿駅", Description: "Shinjuku Station, world busiest"})
	def.DIDs = append(def.DIDs, seedDID{Path: "station:shibuya", DisplayName: "渋谷駅", Description: "Shibuya Station"})
	def.DIDs = append(def.DIDs, seedDID{Path: "station:osaka_umeda", DisplayName: "大阪梅田駅", Description: "Osaka Umeda Station"})
	def.DIDs = append(def.DIDs, seedDID{Path: "station:grand_central", DisplayName: "Grand Central Terminal", Description: "New York, USA"})
	def.DIDs = append(def.DIDs, seedDID{Path: "station:kings_cross", DisplayName: "King's Cross", Description: "London, UK"})
	def.DIDs = append(def.DIDs, seedDID{Path: "route:tokaido_shinkansen", DisplayName: "東海道新幹線", Description: "Tokaido Shinkansen line"})
	def.DIDs = append(def.DIDs, seedDID{Path: "route:yamanote", DisplayName: "山手線", Description: "Yamanote Line loop"})
	def.DIDs = append(def.DIDs, seedDID{Path: "vehicle:n700s", DisplayName: "N700S", Description: "Tokaido Shinkansen train"})
	recsstation := seedCollection{Collection: "ai.gftd.apps.railway.station"}
	recsstation.Items = append(recsstation.Items, seedRecord{ID: "tokyo", Data: map[string]any{"id": "tokyo", "name": "東京駅", "description": "Tokyo Station, JR East", "status": "active"}})
	recsstation.Items = append(recsstation.Items, seedRecord{ID: "shinjuku", Data: map[string]any{"id": "shinjuku", "name": "新宿駅", "description": "Shinjuku Station, world busiest", "status": "active"}})
	recsstation.Items = append(recsstation.Items, seedRecord{ID: "shibuya", Data: map[string]any{"id": "shibuya", "name": "渋谷駅", "description": "Shibuya Station", "status": "active"}})
	recsstation.Items = append(recsstation.Items, seedRecord{ID: "osaka_umeda", Data: map[string]any{"id": "osaka_umeda", "name": "大阪梅田駅", "description": "Osaka Umeda Station", "status": "active"}})
	recsstation.Items = append(recsstation.Items, seedRecord{ID: "grand_central", Data: map[string]any{"id": "grand_central", "name": "Grand Central Terminal", "description": "New York, USA", "status": "active"}})
	recsstation.Items = append(recsstation.Items, seedRecord{ID: "kings_cross", Data: map[string]any{"id": "kings_cross", "name": "King's Cross", "description": "London, UK", "status": "active"}})
	def.Records = append(def.Records, recsstation)
	recsroute := seedCollection{Collection: "ai.gftd.apps.railway.route"}
	recsroute.Items = append(recsroute.Items, seedRecord{ID: "tokaido_shinkansen", Data: map[string]any{"id": "tokaido_shinkansen", "name": "東海道新幹線", "description": "Tokaido Shinkansen line", "status": "active"}})
	recsroute.Items = append(recsroute.Items, seedRecord{ID: "yamanote", Data: map[string]any{"id": "yamanote", "name": "山手線", "description": "Yamanote Line loop", "status": "active"}})
	def.Records = append(def.Records, recsroute)
	recsvehicle := seedCollection{Collection: "ai.gftd.apps.railway.vehicle"}
	recsvehicle.Items = append(recsvehicle.Items, seedRecord{ID: "n700s", Data: map[string]any{"id": "n700s", "name": "N700S", "description": "Tokaido Shinkansen train", "status": "active"}})
	def.Records = append(def.Records, recsvehicle)
	return def
}

func ReceiptGapSeeds() seedDef {
	def := seedDef{Domain: "receipt", Nanoid: "rc4pt01", DID: "did:web:receipt.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "receipt:receipt_001", DisplayName: "Receipt", Description: "receipt receipt"})
	recsreceipt := seedCollection{Collection: "ai.gftd.apps.receipt.receipt"}
	recsreceipt.Items = append(recsreceipt.Items, seedRecord{ID: "receipt_001", Data: map[string]any{"id": "receipt_001", "name": "Receipt", "description": "receipt receipt", "status": "active"}})
	def.Records = append(def.Records, recsreceipt)
	return def
}

func RecycleGapSeeds() seedDef {
	def := seedDef{Domain: "recycle", Nanoid: "rcycl4t1", DID: "did:web:recycle.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "facility:pet_recycle_tokyo", DisplayName: "PETリサイクル東京", Description: "PET bottle recycling"})
	def.DIDs = append(def.DIDs, seedDID{Path: "facility:metal_recycle_osaka", DisplayName: "金属リサイクル大阪", Description: "Metal recycling"})
	def.DIDs = append(def.DIDs, seedDID{Path: "ton:pet_2024", DisplayName: "PETボトル2024年度", Description: "Annual PET recycling volume"})
	def.DIDs = append(def.DIDs, seedDID{Path: "record:recycle_rate_jp_2024", DisplayName: "リサイクル率2024", Description: "Japan 2024 recycle rate"})
	recsfacility := seedCollection{Collection: "ai.gftd.apps.recycle.facility"}
	recsfacility.Items = append(recsfacility.Items, seedRecord{ID: "pet_recycle_tokyo", Data: map[string]any{"id": "pet_recycle_tokyo", "name": "PETリサイクル東京", "description": "PET bottle recycling", "status": "active"}})
	recsfacility.Items = append(recsfacility.Items, seedRecord{ID: "metal_recycle_osaka", Data: map[string]any{"id": "metal_recycle_osaka", "name": "金属リサイクル大阪", "description": "Metal recycling", "status": "active"}})
	def.Records = append(def.Records, recsfacility)
	recston := seedCollection{Collection: "ai.gftd.apps.recycle.ton"}
	recston.Items = append(recston.Items, seedRecord{ID: "pet_2024", Data: map[string]any{"id": "pet_2024", "name": "PETボトル2024年度", "description": "Annual PET recycling volume", "status": "active"}})
	def.Records = append(def.Records, recston)
	recsrecord := seedCollection{Collection: "ai.gftd.apps.recycle.record"}
	recsrecord.Items = append(recsrecord.Items, seedRecord{ID: "recycle_rate_jp_2024", Data: map[string]any{"id": "recycle_rate_jp_2024", "name": "リサイクル率2024", "description": "Japan 2024 recycle rate", "status": "active"}})
	def.Records = append(def.Records, recsrecord)
	return def
}

func RepoGapSeeds() seedDef {
	def := seedDef{Domain: "repo", Nanoid: "r3p0s3rv", DID: "did:web:repo.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "repo:linux_kernel", DisplayName: "Linux Kernel", Description: "torvalds/linux"})
	def.DIDs = append(def.DIDs, seedDID{Path: "repo:kubernetes", DisplayName: "Kubernetes", Description: "kubernetes/kubernetes"})
	def.DIDs = append(def.DIDs, seedDID{Path: "file:main_go", DisplayName: "main.go", Description: "Go entry point"})
	def.DIDs = append(def.DIDs, seedDID{Path: "commit:abc1234", DisplayName: "Initial commit", Description: "First commit"})
	def.DIDs = append(def.DIDs, seedDID{Path: "issue:bug_001", DisplayName: "Bug Report 001", Description: "Critical bug"})
	recsrepo := seedCollection{Collection: "ai.gftd.apps.repo.repo"}
	recsrepo.Items = append(recsrepo.Items, seedRecord{ID: "linux_kernel", Data: map[string]any{"id": "linux_kernel", "name": "Linux Kernel", "description": "torvalds/linux", "status": "active"}})
	recsrepo.Items = append(recsrepo.Items, seedRecord{ID: "kubernetes", Data: map[string]any{"id": "kubernetes", "name": "Kubernetes", "description": "kubernetes/kubernetes", "status": "active"}})
	def.Records = append(def.Records, recsrepo)
	recsfile := seedCollection{Collection: "ai.gftd.apps.repo.file"}
	recsfile.Items = append(recsfile.Items, seedRecord{ID: "main_go", Data: map[string]any{"id": "main_go", "name": "main.go", "description": "Go entry point", "status": "active"}})
	def.Records = append(def.Records, recsfile)
	recscommit := seedCollection{Collection: "ai.gftd.apps.repo.commit"}
	recscommit.Items = append(recscommit.Items, seedRecord{ID: "abc1234", Data: map[string]any{"id": "abc1234", "name": "Initial commit", "description": "First commit", "status": "active"}})
	def.Records = append(def.Records, recscommit)
	recsissue := seedCollection{Collection: "ai.gftd.apps.repo.issue"}
	recsissue.Items = append(recsissue.Items, seedRecord{ID: "bug_001", Data: map[string]any{"id": "bug_001", "name": "Bug Report 001", "description": "Critical bug", "status": "active"}})
	def.Records = append(def.Records, recsissue)
	return def
}

func RoadGapSeeds() seedDef {
	def := seedDef{Domain: "road", Nanoid: "rd2xk7gs", DID: "did:web:road.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "segment:tomei_01", DisplayName: "東名高速01", Description: "Tomei Expressway segment"})
	def.DIDs = append(def.DIDs, seedDID{Path: "segment:meishin_01", DisplayName: "名神高速01", Description: "Meishin Expressway segment"})
	def.DIDs = append(def.DIDs, seedDID{Path: "segment:chuo_01", DisplayName: "中央道01", Description: "Chuo Expressway segment"})
	def.DIDs = append(def.DIDs, seedDID{Path: "segment:route66_01", DisplayName: "Route 66 Segment", Description: "US historic highway"})
	def.DIDs = append(def.DIDs, seedDID{Path: "segment:autobahn_a1", DisplayName: "Autobahn A1", Description: "German highway"})
	recssegment := seedCollection{Collection: "ai.gftd.apps.road.segment"}
	recssegment.Items = append(recssegment.Items, seedRecord{ID: "tomei_01", Data: map[string]any{"id": "tomei_01", "name": "東名高速01", "description": "Tomei Expressway segment", "status": "active"}})
	recssegment.Items = append(recssegment.Items, seedRecord{ID: "meishin_01", Data: map[string]any{"id": "meishin_01", "name": "名神高速01", "description": "Meishin Expressway segment", "status": "active"}})
	recssegment.Items = append(recssegment.Items, seedRecord{ID: "chuo_01", Data: map[string]any{"id": "chuo_01", "name": "中央道01", "description": "Chuo Expressway segment", "status": "active"}})
	recssegment.Items = append(recssegment.Items, seedRecord{ID: "route66_01", Data: map[string]any{"id": "route66_01", "name": "Route 66 Segment", "description": "US historic highway", "status": "active"}})
	recssegment.Items = append(recssegment.Items, seedRecord{ID: "autobahn_a1", Data: map[string]any{"id": "autobahn_a1", "name": "Autobahn A1", "description": "German highway", "status": "active"}})
	def.Records = append(def.Records, recssegment)
	return def
}

func RonbunGapSeeds() seedDef {
	def := seedDef{Domain: "ronbun", Nanoid: "ronb5da3", DID: "did:web:ronbun.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "paper:attention_2017", DisplayName: "Attention Is All You Need", Description: "Vaswani et al., 2017"})
	def.DIDs = append(def.DIDs, seedDID{Path: "paper:bert_2018", DisplayName: "BERT", Description: "Devlin et al., 2018"})
	def.DIDs = append(def.DIDs, seedDID{Path: "paper:alphafold", DisplayName: "AlphaFold", Description: "Jumper et al., 2021"})
	def.DIDs = append(def.DIDs, seedDID{Path: "paper:gpt4", DisplayName: "GPT-4 Technical Report", Description: "OpenAI, 2023"})
	def.DIDs = append(def.DIDs, seedDID{Path: "paper:diffusion", DisplayName: "Denoising Diffusion Models", Description: "Ho et al., 2020"})
	recspaper := seedCollection{Collection: "ai.gftd.apps.ronbun.paper"}
	recspaper.Items = append(recspaper.Items, seedRecord{ID: "attention_2017", Data: map[string]any{"id": "attention_2017", "name": "Attention Is All You Need", "description": "Vaswani et al., 2017", "status": "active"}})
	recspaper.Items = append(recspaper.Items, seedRecord{ID: "bert_2018", Data: map[string]any{"id": "bert_2018", "name": "BERT", "description": "Devlin et al., 2018", "status": "active"}})
	recspaper.Items = append(recspaper.Items, seedRecord{ID: "alphafold", Data: map[string]any{"id": "alphafold", "name": "AlphaFold", "description": "Jumper et al., 2021", "status": "active"}})
	recspaper.Items = append(recspaper.Items, seedRecord{ID: "gpt4", Data: map[string]any{"id": "gpt4", "name": "GPT-4 Technical Report", "description": "OpenAI, 2023", "status": "active"}})
	recspaper.Items = append(recspaper.Items, seedRecord{ID: "diffusion", Data: map[string]any{"id": "diffusion", "name": "Denoising Diffusion Models", "description": "Ho et al., 2020", "status": "active"}})
	def.Records = append(def.Records, recspaper)
	return def
}

func SaigaiGapSeeds() seedDef {
	def := seedDef{Domain: "saigai", Nanoid: "sg4id1s1", DID: "did:web:saigai.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "disaster:earthquake", DisplayName: "地震", Description: "Earthquake"})
	def.DIDs = append(def.DIDs, seedDID{Path: "disaster:tsunami", DisplayName: "津波", Description: "Tsunami"})
	def.DIDs = append(def.DIDs, seedDID{Path: "disaster:typhoon", DisplayName: "台風", Description: "Typhoon"})
	def.DIDs = append(def.DIDs, seedDID{Path: "disaster:flood", DisplayName: "洪水", Description: "Flood"})
	def.DIDs = append(def.DIDs, seedDID{Path: "disaster:volcanic", DisplayName: "火山噴火", Description: "Volcanic eruption"})
	def.DIDs = append(def.DIDs, seedDID{Path: "disaster:landslide", DisplayName: "土砂崩れ", Description: "Landslide"})
	def.DIDs = append(def.DIDs, seedDID{Path: "disaster:wildfire", DisplayName: "山火事", Description: "Wildfire"})
	recsdisaster := seedCollection{Collection: "ai.gftd.apps.saigai.disaster"}
	recsdisaster.Items = append(recsdisaster.Items, seedRecord{ID: "earthquake", Data: map[string]any{"id": "earthquake", "name": "地震", "description": "Earthquake", "status": "active"}})
	recsdisaster.Items = append(recsdisaster.Items, seedRecord{ID: "tsunami", Data: map[string]any{"id": "tsunami", "name": "津波", "description": "Tsunami", "status": "active"}})
	recsdisaster.Items = append(recsdisaster.Items, seedRecord{ID: "typhoon", Data: map[string]any{"id": "typhoon", "name": "台風", "description": "Typhoon", "status": "active"}})
	recsdisaster.Items = append(recsdisaster.Items, seedRecord{ID: "flood", Data: map[string]any{"id": "flood", "name": "洪水", "description": "Flood", "status": "active"}})
	recsdisaster.Items = append(recsdisaster.Items, seedRecord{ID: "volcanic", Data: map[string]any{"id": "volcanic", "name": "火山噴火", "description": "Volcanic eruption", "status": "active"}})
	recsdisaster.Items = append(recsdisaster.Items, seedRecord{ID: "landslide", Data: map[string]any{"id": "landslide", "name": "土砂崩れ", "description": "Landslide", "status": "active"}})
	recsdisaster.Items = append(recsdisaster.Items, seedRecord{ID: "wildfire", Data: map[string]any{"id": "wildfire", "name": "山火事", "description": "Wildfire", "status": "active"}})
	def.Records = append(def.Records, recsdisaster)
	return def
}

func SanctionsGapSeeds() seedDef {
	def := seedDef{Domain: "sanctions", Nanoid: "sn4c8t1x", DID: "did:web:sanctions.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "entity:ofac_sdn_001", DisplayName: "OFAC SDN Entity 001", Description: "US sanctions list"})
	def.DIDs = append(def.DIDs, seedDID{Path: "entity:eu_sanctions_001", DisplayName: "EU Sanctions Entity 001", Description: "EU restrictive measures"})
	def.DIDs = append(def.DIDs, seedDID{Path: "entity:un_sanctions_001", DisplayName: "UN Sanctions Entity 001", Description: "UN Security Council"})
	def.DIDs = append(def.DIDs, seedDID{Path: "entity:jp_mof_sanctions", DisplayName: "財務省制裁リスト", Description: "Japan MOF sanctions"})
	def.DIDs = append(def.DIDs, seedDID{Path: "entity:uk_sanctions_001", DisplayName: "UK Sanctions Entity 001", Description: "UK OFSI list"})
	recsentity := seedCollection{Collection: "ai.gftd.apps.sanctions.entity"}
	recsentity.Items = append(recsentity.Items, seedRecord{ID: "ofac_sdn_001", Data: map[string]any{"id": "ofac_sdn_001", "name": "OFAC SDN Entity 001", "description": "US sanctions list", "status": "active"}})
	recsentity.Items = append(recsentity.Items, seedRecord{ID: "eu_sanctions_001", Data: map[string]any{"id": "eu_sanctions_001", "name": "EU Sanctions Entity 001", "description": "EU restrictive measures", "status": "active"}})
	recsentity.Items = append(recsentity.Items, seedRecord{ID: "un_sanctions_001", Data: map[string]any{"id": "un_sanctions_001", "name": "UN Sanctions Entity 001", "description": "UN Security Council", "status": "active"}})
	recsentity.Items = append(recsentity.Items, seedRecord{ID: "jp_mof_sanctions", Data: map[string]any{"id": "jp_mof_sanctions", "name": "財務省制裁リスト", "description": "Japan MOF sanctions", "status": "active"}})
	recsentity.Items = append(recsentity.Items, seedRecord{ID: "uk_sanctions_001", Data: map[string]any{"id": "uk_sanctions_001", "name": "UK Sanctions Entity 001", "description": "UK OFSI list", "status": "active"}})
	def.Records = append(def.Records, recsentity)
	return def
}

func SatelliteGapSeeds() seedDef {
	def := seedDef{Domain: "satellite", Nanoid: "stlt3k01", DID: "did:web:satellite.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "satellite:iss", DisplayName: "International Space Station", Description: "LEO, crewed station"})
	def.DIDs = append(def.DIDs, seedDID{Path: "satellite:starlink_001", DisplayName: "Starlink-001", Description: "SpaceX LEO broadband"})
	def.DIDs = append(def.DIDs, seedDID{Path: "satellite:gps_iif1", DisplayName: "GPS IIF-1", Description: "US navigation satellite"})
	def.DIDs = append(def.DIDs, seedDID{Path: "satellite:himawari9", DisplayName: "ひまわり9号", Description: "Japan weather satellite"})
	def.DIDs = append(def.DIDs, seedDID{Path: "satellite:sentinel_2a", DisplayName: "Sentinel-2A", Description: "ESA Earth observation"})
	def.DIDs = append(def.DIDs, seedDID{Path: "satellite:oneweb_001", DisplayName: "OneWeb-001", Description: "LEO broadband"})
	def.DIDs = append(def.DIDs, seedDID{Path: "satellite:beidou_3m1", DisplayName: "BeiDou-3 M1", Description: "China navigation"})
	def.DIDs = append(def.DIDs, seedDID{Path: "satellite:michibiki_01", DisplayName: "みちびき1号", Description: "Japan QZSS"})
	recssatellite := seedCollection{Collection: "ai.gftd.apps.satellite.satellite"}
	recssatellite.Items = append(recssatellite.Items, seedRecord{ID: "iss", Data: map[string]any{"id": "iss", "name": "International Space Station", "description": "LEO, crewed station", "status": "active"}})
	recssatellite.Items = append(recssatellite.Items, seedRecord{ID: "starlink_001", Data: map[string]any{"id": "starlink_001", "name": "Starlink-001", "description": "SpaceX LEO broadband", "status": "active"}})
	recssatellite.Items = append(recssatellite.Items, seedRecord{ID: "gps_iif1", Data: map[string]any{"id": "gps_iif1", "name": "GPS IIF-1", "description": "US navigation satellite", "status": "active"}})
	recssatellite.Items = append(recssatellite.Items, seedRecord{ID: "himawari9", Data: map[string]any{"id": "himawari9", "name": "ひまわり9号", "description": "Japan weather satellite", "status": "active"}})
	recssatellite.Items = append(recssatellite.Items, seedRecord{ID: "sentinel_2a", Data: map[string]any{"id": "sentinel_2a", "name": "Sentinel-2A", "description": "ESA Earth observation", "status": "active"}})
	recssatellite.Items = append(recssatellite.Items, seedRecord{ID: "oneweb_001", Data: map[string]any{"id": "oneweb_001", "name": "OneWeb-001", "description": "LEO broadband", "status": "active"}})
	recssatellite.Items = append(recssatellite.Items, seedRecord{ID: "beidou_3m1", Data: map[string]any{"id": "beidou_3m1", "name": "BeiDou-3 M1", "description": "China navigation", "status": "active"}})
	recssatellite.Items = append(recssatellite.Items, seedRecord{ID: "michibiki_01", Data: map[string]any{"id": "michibiki_01", "name": "みちびき1号", "description": "Japan QZSS", "status": "active"}})
	def.Records = append(def.Records, recssatellite)
	return def
}

func SbomGapSeeds() seedDef {
	def := seedDef{Domain: "sbom", Nanoid: "sb0m001x", DID: "did:web:sbom.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "package:openssl_3", DisplayName: "OpenSSL 3.x", Description: "Crypto library"})
	def.DIDs = append(def.DIDs, seedDID{Path: "package:log4j_2", DisplayName: "Log4j 2.x", Description: "Java logging"})
	def.DIDs = append(def.DIDs, seedDID{Path: "package:curl_8", DisplayName: "curl 8.x", Description: "HTTP client"})
	def.DIDs = append(def.DIDs, seedDID{Path: "version:openssl_3_1_4", DisplayName: "OpenSSL 3.1.4", Description: "Security patch"})
	def.DIDs = append(def.DIDs, seedDID{Path: "package:zlib_1", DisplayName: "zlib 1.3", Description: "Compression library"})
	recspackage := seedCollection{Collection: "ai.gftd.apps.sbom.package"}
	recspackage.Items = append(recspackage.Items, seedRecord{ID: "openssl_3", Data: map[string]any{"id": "openssl_3", "name": "OpenSSL 3.x", "description": "Crypto library", "status": "active"}})
	recspackage.Items = append(recspackage.Items, seedRecord{ID: "log4j_2", Data: map[string]any{"id": "log4j_2", "name": "Log4j 2.x", "description": "Java logging", "status": "active"}})
	recspackage.Items = append(recspackage.Items, seedRecord{ID: "curl_8", Data: map[string]any{"id": "curl_8", "name": "curl 8.x", "description": "HTTP client", "status": "active"}})
	recspackage.Items = append(recspackage.Items, seedRecord{ID: "zlib_1", Data: map[string]any{"id": "zlib_1", "name": "zlib 1.3", "description": "Compression library", "status": "active"}})
	def.Records = append(def.Records, recspackage)
	recsversion := seedCollection{Collection: "ai.gftd.apps.sbom.version"}
	recsversion.Items = append(recsversion.Items, seedRecord{ID: "openssl_3_1_4", Data: map[string]any{"id": "openssl_3_1_4", "name": "OpenSSL 3.1.4", "description": "Security patch", "status": "active"}})
	def.Records = append(def.Records, recsversion)
	return def
}

func SecuritiesGapSeeds() seedDef {
	def := seedDef{Domain: "securities", Nanoid: "sc3hn6yd", DID: "did:web:securities.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "exchange:tse", DisplayName: "東京証券取引所", Description: "Tokyo Stock Exchange"})
	def.DIDs = append(def.DIDs, seedDID{Path: "exchange:nyse", DisplayName: "NYSE", Description: "New York Stock Exchange"})
	def.DIDs = append(def.DIDs, seedDID{Path: "exchange:nasdaq", DisplayName: "NASDAQ", Description: "NASDAQ"})
	def.DIDs = append(def.DIDs, seedDID{Path: "exchange:lse", DisplayName: "LSE", Description: "London Stock Exchange"})
	def.DIDs = append(def.DIDs, seedDID{Path: "exchange:hkex", DisplayName: "HKEX", Description: "Hong Kong Exchanges"})
	def.DIDs = append(def.DIDs, seedDID{Path: "exchange:sse", DisplayName: "SSE", Description: "Shanghai Stock Exchange"})
	def.DIDs = append(def.DIDs, seedDID{Path: "exchange:euronext", DisplayName: "Euronext", Description: "European exchange"})
	recsexchange := seedCollection{Collection: "ai.gftd.apps.securities.exchange"}
	recsexchange.Items = append(recsexchange.Items, seedRecord{ID: "tse", Data: map[string]any{"id": "tse", "name": "東京証券取引所", "description": "Tokyo Stock Exchange", "status": "active"}})
	recsexchange.Items = append(recsexchange.Items, seedRecord{ID: "nyse", Data: map[string]any{"id": "nyse", "name": "NYSE", "description": "New York Stock Exchange", "status": "active"}})
	recsexchange.Items = append(recsexchange.Items, seedRecord{ID: "nasdaq", Data: map[string]any{"id": "nasdaq", "name": "NASDAQ", "description": "NASDAQ", "status": "active"}})
	recsexchange.Items = append(recsexchange.Items, seedRecord{ID: "lse", Data: map[string]any{"id": "lse", "name": "LSE", "description": "London Stock Exchange", "status": "active"}})
	recsexchange.Items = append(recsexchange.Items, seedRecord{ID: "hkex", Data: map[string]any{"id": "hkex", "name": "HKEX", "description": "Hong Kong Exchanges", "status": "active"}})
	recsexchange.Items = append(recsexchange.Items, seedRecord{ID: "sse", Data: map[string]any{"id": "sse", "name": "SSE", "description": "Shanghai Stock Exchange", "status": "active"}})
	recsexchange.Items = append(recsexchange.Items, seedRecord{ID: "euronext", Data: map[string]any{"id": "euronext", "name": "Euronext", "description": "European exchange", "status": "active"}})
	def.Records = append(def.Records, recsexchange)
	return def
}

func SeibiGapSeeds() seedDef {
	def := seedDef{Domain: "seibi", Nanoid: "seibf1ea", DID: "did:web:seibi.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "record:shaken_001", DisplayName: "車検記録001", Description: "Vehicle inspection record"})
	def.DIDs = append(def.DIDs, seedDID{Path: "record:oil_change_001", DisplayName: "オイル交換001", Description: "Oil change record"})
	def.DIDs = append(def.DIDs, seedDID{Path: "record:tire_rotation", DisplayName: "タイヤローテーション", Description: "Tire rotation record"})
	def.DIDs = append(def.DIDs, seedDID{Path: "record:brake_pad", DisplayName: "ブレーキパッド交換", Description: "Brake pad replacement"})
	def.DIDs = append(def.DIDs, seedDID{Path: "record:12month_check", DisplayName: "12ヶ月点検", Description: "12-month inspection"})
	recsrecord := seedCollection{Collection: "ai.gftd.apps.seibi.record"}
	recsrecord.Items = append(recsrecord.Items, seedRecord{ID: "shaken_001", Data: map[string]any{"id": "shaken_001", "name": "車検記録001", "description": "Vehicle inspection record", "status": "active"}})
	recsrecord.Items = append(recsrecord.Items, seedRecord{ID: "oil_change_001", Data: map[string]any{"id": "oil_change_001", "name": "オイル交換001", "description": "Oil change record", "status": "active"}})
	recsrecord.Items = append(recsrecord.Items, seedRecord{ID: "tire_rotation", Data: map[string]any{"id": "tire_rotation", "name": "タイヤローテーション", "description": "Tire rotation record", "status": "active"}})
	recsrecord.Items = append(recsrecord.Items, seedRecord{ID: "brake_pad", Data: map[string]any{"id": "brake_pad", "name": "ブレーキパッド交換", "description": "Brake pad replacement", "status": "active"}})
	recsrecord.Items = append(recsrecord.Items, seedRecord{ID: "12month_check", Data: map[string]any{"id": "12month_check", "name": "12ヶ月点検", "description": "12-month inspection", "status": "active"}})
	def.Records = append(def.Records, recsrecord)
	return def
}

func SeiyakuGapSeeds() seedDef {
	def := seedDef{Domain: "seiyaku", Nanoid: "syk4ph01", DID: "did:web:seiyaku.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "study:stability_001", DisplayName: "安定性試験001", Description: "Stability study"})
	def.DIDs = append(def.DIDs, seedDID{Path: "dmf:dmf_001", DisplayName: "DMF登録001", Description: "Drug Master File"})
	def.DIDs = append(def.DIDs, seedDID{Path: "batch:gmp_batch_001", DisplayName: "GMP製造バッチ001", Description: "GMP manufacturing batch"})
	def.DIDs = append(def.DIDs, seedDID{Path: "source:api_001", DisplayName: "原薬001", Description: "Active pharmaceutical ingredient"})
	def.DIDs = append(def.DIDs, seedDID{Path: "submission:nda_001", DisplayName: "新薬申請001", Description: "New drug application"})
	def.DIDs = append(def.DIDs, seedDID{Path: "report:adverse_001", DisplayName: "有害事象報告001", Description: "Adverse event report"})
	recsstudy := seedCollection{Collection: "ai.gftd.apps.seiyaku.study"}
	recsstudy.Items = append(recsstudy.Items, seedRecord{ID: "stability_001", Data: map[string]any{"id": "stability_001", "name": "安定性試験001", "description": "Stability study", "status": "active"}})
	def.Records = append(def.Records, recsstudy)
	recsdmf := seedCollection{Collection: "ai.gftd.apps.seiyaku.dmf"}
	recsdmf.Items = append(recsdmf.Items, seedRecord{ID: "dmf_001", Data: map[string]any{"id": "dmf_001", "name": "DMF登録001", "description": "Drug Master File", "status": "active"}})
	def.Records = append(def.Records, recsdmf)
	recsbatch := seedCollection{Collection: "ai.gftd.apps.seiyaku.batch"}
	recsbatch.Items = append(recsbatch.Items, seedRecord{ID: "gmp_batch_001", Data: map[string]any{"id": "gmp_batch_001", "name": "GMP製造バッチ001", "description": "GMP manufacturing batch", "status": "active"}})
	def.Records = append(def.Records, recsbatch)
	recssource := seedCollection{Collection: "ai.gftd.apps.seiyaku.source"}
	recssource.Items = append(recssource.Items, seedRecord{ID: "api_001", Data: map[string]any{"id": "api_001", "name": "原薬001", "description": "Active pharmaceutical ingredient", "status": "active"}})
	def.Records = append(def.Records, recssource)
	recssubmission := seedCollection{Collection: "ai.gftd.apps.seiyaku.submission"}
	recssubmission.Items = append(recssubmission.Items, seedRecord{ID: "nda_001", Data: map[string]any{"id": "nda_001", "name": "新薬申請001", "description": "New drug application", "status": "active"}})
	def.Records = append(def.Records, recssubmission)
	recsreport := seedCollection{Collection: "ai.gftd.apps.seiyaku.report"}
	recsreport.Items = append(recsreport.Items, seedRecord{ID: "adverse_001", Data: map[string]any{"id": "adverse_001", "name": "有害事象報告001", "description": "Adverse event report", "status": "active"}})
	def.Records = append(def.Records, recsreport)
	return def
}

func SeizoGapSeeds() seedDef {
	def := seedDef{Domain: "seizo", Nanoid: "sz4mk01", DID: "did:web:seizo.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "batch:lot_001", DisplayName: "製造ロット001", Description: "Manufacturing batch"})
	def.DIDs = append(def.DIDs, seedDID{Path: "bom:product_001", DisplayName: "BOM001", Description: "Bill of materials"})
	def.DIDs = append(def.DIDs, seedDID{Path: "inspection:qc_001", DisplayName: "品質検査001", Description: "Quality inspection"})
	def.DIDs = append(def.DIDs, seedDID{Path: "certificate:iso_cert", DisplayName: "ISO認証", Description: "Quality certificate"})
	def.DIDs = append(def.DIDs, seedDID{Path: "order:work_order_001", DisplayName: "製造指示001", Description: "Manufacturing order"})
	def.DIDs = append(def.DIDs, seedDID{Path: "step:assembly_001", DisplayName: "組立工程001", Description: "Assembly process step"})
	def.DIDs = append(def.DIDs, seedDID{Path: "recipe:process_001", DisplayName: "工程レシピ001", Description: "Process recipe"})
	def.DIDs = append(def.DIDs, seedDID{Path: "calibration:gauge_001", DisplayName: "校正記録001", Description: "Gauge calibration"})
	def.DIDs = append(def.DIDs, seedDID{Path: "tooling:mold_001", DisplayName: "金型001", Description: "Injection mold"})
	def.DIDs = append(def.DIDs, seedDID{Path: "intermediate:part_001", DisplayName: "中間体001", Description: "Intermediate product"})
	recsbatch := seedCollection{Collection: "ai.gftd.apps.seizo.batch"}
	recsbatch.Items = append(recsbatch.Items, seedRecord{ID: "lot_001", Data: map[string]any{"id": "lot_001", "name": "製造ロット001", "description": "Manufacturing batch", "status": "active"}})
	def.Records = append(def.Records, recsbatch)
	recsbom := seedCollection{Collection: "ai.gftd.apps.seizo.bom"}
	recsbom.Items = append(recsbom.Items, seedRecord{ID: "product_001", Data: map[string]any{"id": "product_001", "name": "BOM001", "description": "Bill of materials", "status": "active"}})
	def.Records = append(def.Records, recsbom)
	recsinspection := seedCollection{Collection: "ai.gftd.apps.seizo.inspection"}
	recsinspection.Items = append(recsinspection.Items, seedRecord{ID: "qc_001", Data: map[string]any{"id": "qc_001", "name": "品質検査001", "description": "Quality inspection", "status": "active"}})
	def.Records = append(def.Records, recsinspection)
	recscertificate := seedCollection{Collection: "ai.gftd.apps.seizo.certificate"}
	recscertificate.Items = append(recscertificate.Items, seedRecord{ID: "iso_cert", Data: map[string]any{"id": "iso_cert", "name": "ISO認証", "description": "Quality certificate", "status": "active"}})
	def.Records = append(def.Records, recscertificate)
	recsorder := seedCollection{Collection: "ai.gftd.apps.seizo.order"}
	recsorder.Items = append(recsorder.Items, seedRecord{ID: "work_order_001", Data: map[string]any{"id": "work_order_001", "name": "製造指示001", "description": "Manufacturing order", "status": "active"}})
	def.Records = append(def.Records, recsorder)
	recsstep := seedCollection{Collection: "ai.gftd.apps.seizo.step"}
	recsstep.Items = append(recsstep.Items, seedRecord{ID: "assembly_001", Data: map[string]any{"id": "assembly_001", "name": "組立工程001", "description": "Assembly process step", "status": "active"}})
	def.Records = append(def.Records, recsstep)
	recsrecipe := seedCollection{Collection: "ai.gftd.apps.seizo.recipe"}
	recsrecipe.Items = append(recsrecipe.Items, seedRecord{ID: "process_001", Data: map[string]any{"id": "process_001", "name": "工程レシピ001", "description": "Process recipe", "status": "active"}})
	def.Records = append(def.Records, recsrecipe)
	recscalibration := seedCollection{Collection: "ai.gftd.apps.seizo.calibration"}
	recscalibration.Items = append(recscalibration.Items, seedRecord{ID: "gauge_001", Data: map[string]any{"id": "gauge_001", "name": "校正記録001", "description": "Gauge calibration", "status": "active"}})
	def.Records = append(def.Records, recscalibration)
	recstooling := seedCollection{Collection: "ai.gftd.apps.seizo.tooling"}
	recstooling.Items = append(recstooling.Items, seedRecord{ID: "mold_001", Data: map[string]any{"id": "mold_001", "name": "金型001", "description": "Injection mold", "status": "active"}})
	def.Records = append(def.Records, recstooling)
	recsintermediate := seedCollection{Collection: "ai.gftd.apps.seizo.intermediate"}
	recsintermediate.Items = append(recsintermediate.Items, seedRecord{ID: "part_001", Data: map[string]any{"id": "part_001", "name": "中間体001", "description": "Intermediate product", "status": "active"}})
	def.Records = append(def.Records, recsintermediate)
	return def
}

func SenkyoGapSeeds() seedDef {
	def := seedDef{Domain: "senkyo", Nanoid: "snky0e01", DID: "did:web:senkyo.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "election:shugiin_2024", DisplayName: "第50回衆議院選挙", Description: "2024 House of Representatives"})
	def.DIDs = append(def.DIDs, seedDID{Path: "election:sangiin_2025", DisplayName: "第27回参議院選挙", Description: "2025 House of Councillors"})
	def.DIDs = append(def.DIDs, seedDID{Path: "election:us_pres_2024", DisplayName: "2024 US Presidential", Description: "US presidential election"})
	def.DIDs = append(def.DIDs, seedDID{Path: "election:eu_parl_2024", DisplayName: "2024 EU Parliament", Description: "EU parliamentary election"})
	def.DIDs = append(def.DIDs, seedDID{Path: "election:tokyo_gov_2024", DisplayName: "2024東京都知事選", Description: "Tokyo gubernatorial"})
	recselection := seedCollection{Collection: "ai.gftd.apps.senkyo.election"}
	recselection.Items = append(recselection.Items, seedRecord{ID: "shugiin_2024", Data: map[string]any{"id": "shugiin_2024", "name": "第50回衆議院選挙", "description": "2024 House of Representatives", "status": "active"}})
	recselection.Items = append(recselection.Items, seedRecord{ID: "sangiin_2025", Data: map[string]any{"id": "sangiin_2025", "name": "第27回参議院選挙", "description": "2025 House of Councillors", "status": "active"}})
	recselection.Items = append(recselection.Items, seedRecord{ID: "us_pres_2024", Data: map[string]any{"id": "us_pres_2024", "name": "2024 US Presidential", "description": "US presidential election", "status": "active"}})
	recselection.Items = append(recselection.Items, seedRecord{ID: "eu_parl_2024", Data: map[string]any{"id": "eu_parl_2024", "name": "2024 EU Parliament", "description": "EU parliamentary election", "status": "active"}})
	recselection.Items = append(recselection.Items, seedRecord{ID: "tokyo_gov_2024", Data: map[string]any{"id": "tokyo_gov_2024", "name": "2024東京都知事選", "description": "Tokyo gubernatorial", "status": "active"}})
	def.Records = append(def.Records, recselection)
	return def
}

func SerialGapSeeds() seedDef {
	def := seedDef{Domain: "serial", Nanoid: "sr1l4k01", DID: "did:web:serial.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "item:sgtin_001", DisplayName: "SGTIN001", Description: "Serialized GTIN item"})
	def.DIDs = append(def.DIDs, seedDID{Path: "device:imei_001", DisplayName: "IMEI001", Description: "Mobile device IMEI"})
	def.DIDs = append(def.DIDs, seedDID{Path: "device:udi_001", DisplayName: "UDI001", Description: "Medical device UDI"})
	def.DIDs = append(def.DIDs, seedDID{Path: "lot:food_lot_001", DisplayName: "食品ロット001", Description: "Food lot number"})
	def.DIDs = append(def.DIDs, seedDID{Path: "battery:ev_battery_001", DisplayName: "EVバッテリー001", Description: "EV battery passport"})
	def.DIDs = append(def.DIDs, seedDID{Path: "firearm:jp_gun_001", DisplayName: "銃砲登録001", Description: "Firearm registration"})
	def.DIDs = append(def.DIDs, seedDID{Path: "panel:solar_001", DisplayName: "ソーラーパネル001", Description: "Solar panel serial"})
	def.DIDs = append(def.DIDs, seedDID{Path: "tire:tire_serial_001", DisplayName: "タイヤ001", Description: "Tire serial number"})
	def.DIDs = append(def.DIDs, seedDID{Path: "package:pharma_001", DisplayName: "医薬品シリアル001", Description: "Pharma serialization"})
	def.DIDs = append(def.DIDs, seedDID{Path: "part:aircraft_part_001", DisplayName: "航空部品001", Description: "Aircraft part serial"})
	def.DIDs = append(def.DIDs, seedDID{Path: "round:ammo_001", DisplayName: "弾薬ロット001", Description: "Ammunition lot"})
	def.DIDs = append(def.DIDs, seedDID{Path: "item:glasses_001", DisplayName: "メガネ001", Description: "Eyewear serial"})
	def.DIDs = append(def.DIDs, seedDID{Path: "item:luxury_001", DisplayName: "高級品001", Description: "Luxury item serial"})
	recsitem := seedCollection{Collection: "ai.gftd.apps.serial.item"}
	recsitem.Items = append(recsitem.Items, seedRecord{ID: "sgtin_001", Data: map[string]any{"id": "sgtin_001", "name": "SGTIN001", "description": "Serialized GTIN item", "status": "active"}})
	recsitem.Items = append(recsitem.Items, seedRecord{ID: "glasses_001", Data: map[string]any{"id": "glasses_001", "name": "メガネ001", "description": "Eyewear serial", "status": "active"}})
	recsitem.Items = append(recsitem.Items, seedRecord{ID: "luxury_001", Data: map[string]any{"id": "luxury_001", "name": "高級品001", "description": "Luxury item serial", "status": "active"}})
	def.Records = append(def.Records, recsitem)
	recsdevice := seedCollection{Collection: "ai.gftd.apps.serial.device"}
	recsdevice.Items = append(recsdevice.Items, seedRecord{ID: "imei_001", Data: map[string]any{"id": "imei_001", "name": "IMEI001", "description": "Mobile device IMEI", "status": "active"}})
	recsdevice.Items = append(recsdevice.Items, seedRecord{ID: "udi_001", Data: map[string]any{"id": "udi_001", "name": "UDI001", "description": "Medical device UDI", "status": "active"}})
	def.Records = append(def.Records, recsdevice)
	recslot := seedCollection{Collection: "ai.gftd.apps.serial.lot"}
	recslot.Items = append(recslot.Items, seedRecord{ID: "food_lot_001", Data: map[string]any{"id": "food_lot_001", "name": "食品ロット001", "description": "Food lot number", "status": "active"}})
	def.Records = append(def.Records, recslot)
	recsbattery := seedCollection{Collection: "ai.gftd.apps.serial.battery"}
	recsbattery.Items = append(recsbattery.Items, seedRecord{ID: "ev_battery_001", Data: map[string]any{"id": "ev_battery_001", "name": "EVバッテリー001", "description": "EV battery passport", "status": "active"}})
	def.Records = append(def.Records, recsbattery)
	recsfirearm := seedCollection{Collection: "ai.gftd.apps.serial.firearm"}
	recsfirearm.Items = append(recsfirearm.Items, seedRecord{ID: "jp_gun_001", Data: map[string]any{"id": "jp_gun_001", "name": "銃砲登録001", "description": "Firearm registration", "status": "active"}})
	def.Records = append(def.Records, recsfirearm)
	recspanel := seedCollection{Collection: "ai.gftd.apps.serial.panel"}
	recspanel.Items = append(recspanel.Items, seedRecord{ID: "solar_001", Data: map[string]any{"id": "solar_001", "name": "ソーラーパネル001", "description": "Solar panel serial", "status": "active"}})
	def.Records = append(def.Records, recspanel)
	recstire := seedCollection{Collection: "ai.gftd.apps.serial.tire"}
	recstire.Items = append(recstire.Items, seedRecord{ID: "tire_serial_001", Data: map[string]any{"id": "tire_serial_001", "name": "タイヤ001", "description": "Tire serial number", "status": "active"}})
	def.Records = append(def.Records, recstire)
	recspackage := seedCollection{Collection: "ai.gftd.apps.serial.package"}
	recspackage.Items = append(recspackage.Items, seedRecord{ID: "pharma_001", Data: map[string]any{"id": "pharma_001", "name": "医薬品シリアル001", "description": "Pharma serialization", "status": "active"}})
	def.Records = append(def.Records, recspackage)
	recspart := seedCollection{Collection: "ai.gftd.apps.serial.part"}
	recspart.Items = append(recspart.Items, seedRecord{ID: "aircraft_part_001", Data: map[string]any{"id": "aircraft_part_001", "name": "航空部品001", "description": "Aircraft part serial", "status": "active"}})
	def.Records = append(def.Records, recspart)
	recsround := seedCollection{Collection: "ai.gftd.apps.serial.round"}
	recsround.Items = append(recsround.Items, seedRecord{ID: "ammo_001", Data: map[string]any{"id": "ammo_001", "name": "弾薬ロット001", "description": "Ammunition lot", "status": "active"}})
	def.Records = append(def.Records, recsround)
	return def
}

func SetaiGapSeeds() seedDef {
	def := seedDef{Domain: "setai", Nanoid: "st4ai01", DID: "did:web:setai.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "household:single_tokyo", DisplayName: "単身世帯東京", Description: "Single household Tokyo"})
	def.DIDs = append(def.DIDs, seedDID{Path: "household:family_osaka", DisplayName: "家族世帯大阪", Description: "Family household Osaka"})
	def.DIDs = append(def.DIDs, seedDID{Path: "household:elderly_rural", DisplayName: "高齢者世帯地方", Description: "Elderly household rural"})
	def.DIDs = append(def.DIDs, seedDID{Path: "household:dual_income", DisplayName: "共働き世帯", Description: "Dual-income household"})
	def.DIDs = append(def.DIDs, seedDID{Path: "household:single_parent", DisplayName: "ひとり親世帯", Description: "Single-parent household"})
	recshousehold := seedCollection{Collection: "ai.gftd.apps.setai.household"}
	recshousehold.Items = append(recshousehold.Items, seedRecord{ID: "single_tokyo", Data: map[string]any{"id": "single_tokyo", "name": "単身世帯東京", "description": "Single household Tokyo", "status": "active"}})
	recshousehold.Items = append(recshousehold.Items, seedRecord{ID: "family_osaka", Data: map[string]any{"id": "family_osaka", "name": "家族世帯大阪", "description": "Family household Osaka", "status": "active"}})
	recshousehold.Items = append(recshousehold.Items, seedRecord{ID: "elderly_rural", Data: map[string]any{"id": "elderly_rural", "name": "高齢者世帯地方", "description": "Elderly household rural", "status": "active"}})
	recshousehold.Items = append(recshousehold.Items, seedRecord{ID: "dual_income", Data: map[string]any{"id": "dual_income", "name": "共働き世帯", "description": "Dual-income household", "status": "active"}})
	recshousehold.Items = append(recshousehold.Items, seedRecord{ID: "single_parent", Data: map[string]any{"id": "single_parent", "name": "ひとり親世帯", "description": "Single-parent household", "status": "active"}})
	def.Records = append(def.Records, recshousehold)
	return def
}

func ShikakuGapSeeds() seedDef {
	def := seedDef{Domain: "shikaku", Nanoid: "sh1k4k0q", DID: "did:web:shikaku.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "certification:ipa_fe", DisplayName: "基本情報技術者", Description: "IPA FE certification"})
	def.DIDs = append(def.DIDs, seedDID{Path: "certification:ipa_ap", DisplayName: "応用情報技術者", Description: "IPA AP certification"})
	def.DIDs = append(def.DIDs, seedDID{Path: "certification:aws_saa", DisplayName: "AWS SAA", Description: "AWS Solutions Architect"})
	def.DIDs = append(def.DIDs, seedDID{Path: "certification:cpa_jp", DisplayName: "公認会計士", Description: "CPA Japan"})
	def.DIDs = append(def.DIDs, seedDID{Path: "certification:takkenshi", DisplayName: "宅建士", Description: "Real estate broker"})
	recscertification := seedCollection{Collection: "ai.gftd.apps.shikaku.certification"}
	recscertification.Items = append(recscertification.Items, seedRecord{ID: "ipa_fe", Data: map[string]any{"id": "ipa_fe", "name": "基本情報技術者", "description": "IPA FE certification", "status": "active"}})
	recscertification.Items = append(recscertification.Items, seedRecord{ID: "ipa_ap", Data: map[string]any{"id": "ipa_ap", "name": "応用情報技術者", "description": "IPA AP certification", "status": "active"}})
	recscertification.Items = append(recscertification.Items, seedRecord{ID: "aws_saa", Data: map[string]any{"id": "aws_saa", "name": "AWS SAA", "description": "AWS Solutions Architect", "status": "active"}})
	recscertification.Items = append(recscertification.Items, seedRecord{ID: "cpa_jp", Data: map[string]any{"id": "cpa_jp", "name": "公認会計士", "description": "CPA Japan", "status": "active"}})
	recscertification.Items = append(recscertification.Items, seedRecord{ID: "takkenshi", Data: map[string]any{"id": "takkenshi", "name": "宅建士", "description": "Real estate broker", "status": "active"}})
	def.Records = append(def.Records, recscertification)
	return def
}

func ShinsaGapSeeds() seedDef {
	def := seedDef{Domain: "shinsa_process", Nanoid: "shin0756", DID: "did:web:shinsa.etzhayyim.com"}
	recsassessment := seedCollection{Collection: "ai.gftd.apps.shinsa.assessment"}
	domains := []struct {
		key, title string
	}{
		{"credit", "信用スコア審査"},
		{"loan", "融資審査"},
		{"visa", "ビザ審査"},
		{"insurance", "保険引受審査"},
		{"kyc_aml", "KYC/AML審査"},
		{"procurement", "調達入札審査"},
		{"tax", "税務監査審査"},
		{"environment", "環境影響審査"},
		{"construction", "建築許認可審査"},
		{"welfare", "給付適格審査"},
		{"education", "教育助成審査"},
		{"energy", "エネルギー補助審査"},
	}
	regions := []string{
		"tokyo", "osaka", "nagoya", "fukuoka", "sapporo", "sendai", "hiroshima", "naha", "kyoto", "kobe",
		"yokohama", "saitama", "chiba", "shizuoka", "kanazawa", "niigata", "kumamoto", "nagasaki", "matsuyama", "okinawa",
	}
	levels := []string{"L1", "L2", "L3", "L4", "L5", "L6"}
	for _, d := range domains {
		for _, r := range regions {
			for _, l := range levels {
				id := d.key + "_" + r + "_" + l
				name := d.title + " " + r + " " + l
				def.DIDs = append(def.DIDs, seedDID{
					Path:        "assessment:" + id,
					DisplayName: name,
					Description: d.key,
				})
				recsassessment.Items = append(recsassessment.Items, seedRecord{ID: id, Data: map[string]any{
					"id": id, "name": name, "category": d.key, "region": r, "review_level": l, "status": "active",
				}})
			}
		}
	}
	def.Records = append(def.Records, recsassessment)
	return def
}

func ShinshiGapSeeds() seedDef {
	def := seedDef{Domain: "shinshi", Nanoid: "sh1n5h1x", DID: "did:web:shinshi.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "content:age_gate", DisplayName: "年齢認証ゲート", Description: "Age verification gate"})
	def.DIDs = append(def.DIDs, seedDID{Path: "verification:id_check", DisplayName: "本人確認", Description: "ID verification"})
	def.DIDs = append(def.DIDs, seedDID{Path: "performer:model_001", DisplayName: "パフォーマー001", Description: "Content creator"})
	def.DIDs = append(def.DIDs, seedDID{Path: "platform:platform_001", DisplayName: "プラットフォーム001", Description: "Content platform"})
	def.DIDs = append(def.DIDs, seedDID{Path: "studio:studio_001", DisplayName: "スタジオ001", Description: "Production studio"})
	def.DIDs = append(def.DIDs, seedDID{Path: "listing:listing_001", DisplayName: "リスティング001", Description: "Service listing"})
	def.DIDs = append(def.DIDs, seedDID{Path: "item:restricted_001", DisplayName: "制限コンテンツ001", Description: "Restricted content"})
	recscontent := seedCollection{Collection: "ai.gftd.apps.shinshi.content"}
	recscontent.Items = append(recscontent.Items, seedRecord{ID: "age_gate", Data: map[string]any{"id": "age_gate", "name": "年齢認証ゲート", "description": "Age verification gate", "status": "active"}})
	def.Records = append(def.Records, recscontent)
	recsverification := seedCollection{Collection: "ai.gftd.apps.shinshi.verification"}
	recsverification.Items = append(recsverification.Items, seedRecord{ID: "id_check", Data: map[string]any{"id": "id_check", "name": "本人確認", "description": "ID verification", "status": "active"}})
	def.Records = append(def.Records, recsverification)
	recsperformer := seedCollection{Collection: "ai.gftd.apps.shinshi.performer"}
	recsperformer.Items = append(recsperformer.Items, seedRecord{ID: "model_001", Data: map[string]any{"id": "model_001", "name": "パフォーマー001", "description": "Content creator", "status": "active"}})
	def.Records = append(def.Records, recsperformer)
	recsplatform := seedCollection{Collection: "ai.gftd.apps.shinshi.platform"}
	recsplatform.Items = append(recsplatform.Items, seedRecord{ID: "platform_001", Data: map[string]any{"id": "platform_001", "name": "プラットフォーム001", "description": "Content platform", "status": "active"}})
	def.Records = append(def.Records, recsplatform)
	recsstudio := seedCollection{Collection: "ai.gftd.apps.shinshi.studio"}
	recsstudio.Items = append(recsstudio.Items, seedRecord{ID: "studio_001", Data: map[string]any{"id": "studio_001", "name": "スタジオ001", "description": "Production studio", "status": "active"}})
	def.Records = append(def.Records, recsstudio)
	recslisting := seedCollection{Collection: "ai.gftd.apps.shinshi.listing"}
	recslisting.Items = append(recslisting.Items, seedRecord{ID: "listing_001", Data: map[string]any{"id": "listing_001", "name": "リスティング001", "description": "Service listing", "status": "active"}})
	def.Records = append(def.Records, recslisting)
	recsitem := seedCollection{Collection: "ai.gftd.apps.shinshi.item"}
	recsitem.Items = append(recsitem.Items, seedRecord{ID: "restricted_001", Data: map[string]any{"id": "restricted_001", "name": "制限コンテンツ001", "description": "Restricted content", "status": "active"}})
	def.Records = append(def.Records, recsitem)
	return def
}

func ShisanGapSeeds() seedDef {
	def := seedDef{Domain: "shisan", Nanoid: "sh4sn01", DID: "did:web:shisan.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "record:depreciation_001", DisplayName: "減価償却記録001", Description: "Depreciation record"})
	def.DIDs = append(def.DIDs, seedDID{Path: "entry:useful_life_001", DisplayName: "耐用年数001", Description: "Useful life entry"})
	def.DIDs = append(def.DIDs, seedDID{Path: "record:asset_lifecycle_001", DisplayName: "資産ライフサイクル001", Description: "Asset lifecycle"})
	recsrecord := seedCollection{Collection: "ai.gftd.apps.shisan.record"}
	recsrecord.Items = append(recsrecord.Items, seedRecord{ID: "depreciation_001", Data: map[string]any{"id": "depreciation_001", "name": "減価償却記録001", "description": "Depreciation record", "status": "active"}})
	recsrecord.Items = append(recsrecord.Items, seedRecord{ID: "asset_lifecycle_001", Data: map[string]any{"id": "asset_lifecycle_001", "name": "資産ライフサイクル001", "description": "Asset lifecycle", "status": "active"}})
	def.Records = append(def.Records, recsrecord)
	recsentry := seedCollection{Collection: "ai.gftd.apps.shisan.entry"}
	recsentry.Items = append(recsentry.Items, seedRecord{ID: "useful_life_001", Data: map[string]any{"id": "useful_life_001", "name": "耐用年数001", "description": "Useful life entry", "status": "active"}})
	def.Records = append(def.Records, recsentry)
	return def
}

func ShizenGapSeeds() seedDef {
	def := seedDef{Domain: "shizen", Nanoid: "shzn3k01", DID: "did:web:shizen.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "ecoregion:amazon", DisplayName: "アマゾン熱帯雨林", Description: "Amazon tropical rainforest"})
	def.DIDs = append(def.DIDs, seedDID{Path: "ecoregion:coral_triangle", DisplayName: "コーラルトライアングル", Description: "Coral Triangle marine"})
	def.DIDs = append(def.DIDs, seedDID{Path: "ecoregion:taiga_siberia", DisplayName: "シベリアタイガ", Description: "Siberian taiga"})
	def.DIDs = append(def.DIDs, seedDID{Path: "area:yellowstone", DisplayName: "イエローストーン", Description: "Yellowstone National Park"})
	def.DIDs = append(def.DIDs, seedDID{Path: "river:amazon", DisplayName: "アマゾン川", Description: "Amazon River"})
	def.DIDs = append(def.DIDs, seedDID{Path: "river:nile", DisplayName: "ナイル川", Description: "Nile River"})
	def.DIDs = append(def.DIDs, seedDID{Path: "station:tokyo_kishou", DisplayName: "東京気象台", Description: "Tokyo Weather Station"})
	recsecoregion := seedCollection{Collection: "ai.gftd.apps.shizen.ecoregion"}
	recsecoregion.Items = append(recsecoregion.Items, seedRecord{ID: "amazon", Data: map[string]any{"id": "amazon", "name": "アマゾン熱帯雨林", "description": "Amazon tropical rainforest", "status": "active"}})
	recsecoregion.Items = append(recsecoregion.Items, seedRecord{ID: "coral_triangle", Data: map[string]any{"id": "coral_triangle", "name": "コーラルトライアングル", "description": "Coral Triangle marine", "status": "active"}})
	recsecoregion.Items = append(recsecoregion.Items, seedRecord{ID: "taiga_siberia", Data: map[string]any{"id": "taiga_siberia", "name": "シベリアタイガ", "description": "Siberian taiga", "status": "active"}})
	def.Records = append(def.Records, recsecoregion)
	recsarea := seedCollection{Collection: "ai.gftd.apps.shizen.area"}
	recsarea.Items = append(recsarea.Items, seedRecord{ID: "yellowstone", Data: map[string]any{"id": "yellowstone", "name": "イエローストーン", "description": "Yellowstone National Park", "status": "active"}})
	def.Records = append(def.Records, recsarea)
	recsriver := seedCollection{Collection: "ai.gftd.apps.shizen.river"}
	recsriver.Items = append(recsriver.Items, seedRecord{ID: "amazon", Data: map[string]any{"id": "amazon", "name": "アマゾン川", "description": "Amazon River", "status": "active"}})
	recsriver.Items = append(recsriver.Items, seedRecord{ID: "nile", Data: map[string]any{"id": "nile", "name": "ナイル川", "description": "Nile River", "status": "active"}})
	def.Records = append(def.Records, recsriver)
	recsstation := seedCollection{Collection: "ai.gftd.apps.shizen.station"}
	recsstation.Items = append(recsstation.Items, seedRecord{ID: "tokyo_kishou", Data: map[string]any{"id": "tokyo_kishou", "name": "東京気象台", "description": "Tokyo Weather Station", "status": "active"}})
	def.Records = append(def.Records, recsstation)
	return def
}

func ShohinGapSeeds() seedDef {
	def := seedDef{Domain: "shohin", Nanoid: "sh4hn01", DID: "did:web:shohin.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "product:iphone_15", DisplayName: "iPhone 15", Description: "Apple smartphone"})
	def.DIDs = append(def.DIDs, seedDID{Path: "product:ps5", DisplayName: "PlayStation 5", Description: "Sony game console"})
	def.DIDs = append(def.DIDs, seedDID{Path: "product:switch_2", DisplayName: "Nintendo Switch 2", Description: "Nintendo game console"})
	def.DIDs = append(def.DIDs, seedDID{Path: "product:dyson_v15", DisplayName: "Dyson V15", Description: "Cordless vacuum cleaner"})
	def.DIDs = append(def.DIDs, seedDID{Path: "product:airpods_pro", DisplayName: "AirPods Pro", Description: "Apple earbuds"})
	recsproduct := seedCollection{Collection: "ai.gftd.apps.shohin.product"}
	recsproduct.Items = append(recsproduct.Items, seedRecord{ID: "iphone_15", Data: map[string]any{"id": "iphone_15", "name": "iPhone 15", "description": "Apple smartphone", "status": "active"}})
	recsproduct.Items = append(recsproduct.Items, seedRecord{ID: "ps5", Data: map[string]any{"id": "ps5", "name": "PlayStation 5", "description": "Sony game console", "status": "active"}})
	recsproduct.Items = append(recsproduct.Items, seedRecord{ID: "switch_2", Data: map[string]any{"id": "switch_2", "name": "Nintendo Switch 2", "description": "Nintendo game console", "status": "active"}})
	recsproduct.Items = append(recsproduct.Items, seedRecord{ID: "dyson_v15", Data: map[string]any{"id": "dyson_v15", "name": "Dyson V15", "description": "Cordless vacuum cleaner", "status": "active"}})
	recsproduct.Items = append(recsproduct.Items, seedRecord{ID: "airpods_pro", Data: map[string]any{"id": "airpods_pro", "name": "AirPods Pro", "description": "Apple earbuds", "status": "active"}})
	def.Records = append(def.Records, recsproduct)
	return def
}

func ShokuhinAnzenGapSeeds() seedDef {
	def := seedDef{Domain: "shokuhin-anzen", Nanoid: "shokdb1b", DID: "did:web:shokuhin-anzen.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "inspection:pesticide_test", DisplayName: "残留農薬検査", Description: "Pesticide residue test"})
	def.DIDs = append(def.DIDs, seedDID{Path: "inspection:bacteria_test", DisplayName: "細菌検査", Description: "Bacterial contamination test"})
	def.DIDs = append(def.DIDs, seedDID{Path: "inspection:additive_test", DisplayName: "食品添加物検査", Description: "Food additive inspection"})
	def.DIDs = append(def.DIDs, seedDID{Path: "inspection:allergen_test", DisplayName: "アレルゲン検査", Description: "Allergen test"})
	def.DIDs = append(def.DIDs, seedDID{Path: "inspection:haccp_audit", DisplayName: "HACCP監査", Description: "HACCP audit"})
	recsinspection := seedCollection{Collection: "ai.gftd.apps.shokuhinanzen.inspection"}
	recsinspection.Items = append(recsinspection.Items, seedRecord{ID: "pesticide_test", Data: map[string]any{"id": "pesticide_test", "name": "残留農薬検査", "description": "Pesticide residue test", "status": "active"}})
	recsinspection.Items = append(recsinspection.Items, seedRecord{ID: "bacteria_test", Data: map[string]any{"id": "bacteria_test", "name": "細菌検査", "description": "Bacterial contamination test", "status": "active"}})
	recsinspection.Items = append(recsinspection.Items, seedRecord{ID: "additive_test", Data: map[string]any{"id": "additive_test", "name": "食品添加物検査", "description": "Food additive inspection", "status": "active"}})
	recsinspection.Items = append(recsinspection.Items, seedRecord{ID: "allergen_test", Data: map[string]any{"id": "allergen_test", "name": "アレルゲン検査", "description": "Allergen test", "status": "active"}})
	recsinspection.Items = append(recsinspection.Items, seedRecord{ID: "haccp_audit", Data: map[string]any{"id": "haccp_audit", "name": "HACCP監査", "description": "HACCP audit", "status": "active"}})
	def.Records = append(def.Records, recsinspection)
	return def
}

func SnsGapSeeds() seedDef {
	def := seedDef{Domain: "sns", Nanoid: "sns888c", DID: "did:web:sns.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "account:twitter_sample", DisplayName: "Twitter Account", Description: "X/Twitter account"})
	def.DIDs = append(def.DIDs, seedDID{Path: "account:instagram_sample", DisplayName: "Instagram Account", Description: "Instagram account"})
	def.DIDs = append(def.DIDs, seedDID{Path: "account:tiktok_sample", DisplayName: "TikTok Account", Description: "TikTok account"})
	def.DIDs = append(def.DIDs, seedDID{Path: "account:youtube_sample", DisplayName: "YouTube Channel", Description: "YouTube channel"})
	def.DIDs = append(def.DIDs, seedDID{Path: "account:linkedin_sample", DisplayName: "LinkedIn Profile", Description: "LinkedIn account"})
	recsaccount := seedCollection{Collection: "ai.gftd.apps.sns.account"}
	recsaccount.Items = append(recsaccount.Items, seedRecord{ID: "twitter_sample", Data: map[string]any{"id": "twitter_sample", "name": "Twitter Account", "description": "X/Twitter account", "status": "active"}})
	recsaccount.Items = append(recsaccount.Items, seedRecord{ID: "instagram_sample", Data: map[string]any{"id": "instagram_sample", "name": "Instagram Account", "description": "Instagram account", "status": "active"}})
	recsaccount.Items = append(recsaccount.Items, seedRecord{ID: "tiktok_sample", Data: map[string]any{"id": "tiktok_sample", "name": "TikTok Account", "description": "TikTok account", "status": "active"}})
	recsaccount.Items = append(recsaccount.Items, seedRecord{ID: "youtube_sample", Data: map[string]any{"id": "youtube_sample", "name": "YouTube Channel", "description": "YouTube channel", "status": "active"}})
	recsaccount.Items = append(recsaccount.Items, seedRecord{ID: "linkedin_sample", Data: map[string]any{"id": "linkedin_sample", "name": "LinkedIn Profile", "description": "LinkedIn account", "status": "active"}})
	def.Records = append(def.Records, recsaccount)
	return def
}

func SoftwareGapSeeds() seedDef {
	def := seedDef{Domain: "software", Nanoid: "sw4r3k7m", DID: "did:web:software.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "app:vscode", DisplayName: "Visual Studio Code", Description: "Microsoft code editor"})
	def.DIDs = append(def.DIDs, seedDID{Path: "app:chrome", DisplayName: "Google Chrome", Description: "Web browser"})
	def.DIDs = append(def.DIDs, seedDID{Path: "vendor:microsoft", DisplayName: "Microsoft", Description: "Software vendor"})
	def.DIDs = append(def.DIDs, seedDID{Path: "vendor:adobe", DisplayName: "Adobe", Description: "Creative software vendor"})
	def.DIDs = append(def.DIDs, seedDID{Path: "service:github", DisplayName: "GitHub", Description: "SaaS code hosting"})
	def.DIDs = append(def.DIDs, seedDID{Path: "package:lodash", DisplayName: "lodash", Description: "JS utility library"})
	def.DIDs = append(def.DIDs, seedDID{Path: "extension:react_devtools", DisplayName: "React DevTools", Description: "Browser extension"})
	def.DIDs = append(def.DIDs, seedDID{Path: "patch:windows_kb001", DisplayName: "Windows KB001", Description: "Security patch"})
	def.DIDs = append(def.DIDs, seedDID{Path: "subscription:office365", DisplayName: "Microsoft 365", Description: "SaaS subscription"})
	def.DIDs = append(def.DIDs, seedDID{Path: "key:license_001", DisplayName: "License Key 001", Description: "Software license key"})
	def.DIDs = append(def.DIDs, seedDID{Path: "review:vscode_review", DisplayName: "VS Code Review", Description: "App store review"})
	def.DIDs = append(def.DIDs, seedDID{Path: "game:steam_game_001", DisplayName: "Steam Game 001", Description: "PC game"})
	def.DIDs = append(def.DIDs, seedDID{Path: "document:eula_ms", DisplayName: "Microsoft EULA", Description: "End user license"})
	def.DIDs = append(def.DIDs, seedDID{Path: "item:iap_gems", DisplayName: "Gems Pack", Description: "In-app purchase item"})
	def.DIDs = append(def.DIDs, seedDID{Path: "software:photoshop", DisplayName: "Adobe Photoshop", Description: "Desktop software"})
	recsapp := seedCollection{Collection: "ai.gftd.apps.software.app"}
	recsapp.Items = append(recsapp.Items, seedRecord{ID: "vscode", Data: map[string]any{"id": "vscode", "name": "Visual Studio Code", "description": "Microsoft code editor", "status": "active"}})
	recsapp.Items = append(recsapp.Items, seedRecord{ID: "chrome", Data: map[string]any{"id": "chrome", "name": "Google Chrome", "description": "Web browser", "status": "active"}})
	def.Records = append(def.Records, recsapp)
	recsvendor := seedCollection{Collection: "ai.gftd.apps.software.vendor"}
	recsvendor.Items = append(recsvendor.Items, seedRecord{ID: "microsoft", Data: map[string]any{"id": "microsoft", "name": "Microsoft", "description": "Software vendor", "status": "active"}})
	recsvendor.Items = append(recsvendor.Items, seedRecord{ID: "adobe", Data: map[string]any{"id": "adobe", "name": "Adobe", "description": "Creative software vendor", "status": "active"}})
	def.Records = append(def.Records, recsvendor)
	recsservice := seedCollection{Collection: "ai.gftd.apps.software.service"}
	recsservice.Items = append(recsservice.Items, seedRecord{ID: "github", Data: map[string]any{"id": "github", "name": "GitHub", "description": "SaaS code hosting", "status": "active"}})
	def.Records = append(def.Records, recsservice)
	recspackage := seedCollection{Collection: "ai.gftd.apps.software.package"}
	recspackage.Items = append(recspackage.Items, seedRecord{ID: "lodash", Data: map[string]any{"id": "lodash", "name": "lodash", "description": "JS utility library", "status": "active"}})
	def.Records = append(def.Records, recspackage)
	recsextension := seedCollection{Collection: "ai.gftd.apps.software.extension"}
	recsextension.Items = append(recsextension.Items, seedRecord{ID: "react_devtools", Data: map[string]any{"id": "react_devtools", "name": "React DevTools", "description": "Browser extension", "status": "active"}})
	def.Records = append(def.Records, recsextension)
	recspatch := seedCollection{Collection: "ai.gftd.apps.software.patch"}
	recspatch.Items = append(recspatch.Items, seedRecord{ID: "windows_kb001", Data: map[string]any{"id": "windows_kb001", "name": "Windows KB001", "description": "Security patch", "status": "active"}})
	def.Records = append(def.Records, recspatch)
	recssubscription := seedCollection{Collection: "ai.gftd.apps.software.subscription"}
	recssubscription.Items = append(recssubscription.Items, seedRecord{ID: "office365", Data: map[string]any{"id": "office365", "name": "Microsoft 365", "description": "SaaS subscription", "status": "active"}})
	def.Records = append(def.Records, recssubscription)
	recskey := seedCollection{Collection: "ai.gftd.apps.software.key"}
	recskey.Items = append(recskey.Items, seedRecord{ID: "license_001", Data: map[string]any{"id": "license_001", "name": "License Key 001", "description": "Software license key", "status": "active"}})
	def.Records = append(def.Records, recskey)
	recsreview := seedCollection{Collection: "ai.gftd.apps.software.review"}
	recsreview.Items = append(recsreview.Items, seedRecord{ID: "vscode_review", Data: map[string]any{"id": "vscode_review", "name": "VS Code Review", "description": "App store review", "status": "active"}})
	def.Records = append(def.Records, recsreview)
	recsgame := seedCollection{Collection: "ai.gftd.apps.software.game"}
	recsgame.Items = append(recsgame.Items, seedRecord{ID: "steam_game_001", Data: map[string]any{"id": "steam_game_001", "name": "Steam Game 001", "description": "PC game", "status": "active"}})
	def.Records = append(def.Records, recsgame)
	recsdocument := seedCollection{Collection: "ai.gftd.apps.software.document"}
	recsdocument.Items = append(recsdocument.Items, seedRecord{ID: "eula_ms", Data: map[string]any{"id": "eula_ms", "name": "Microsoft EULA", "description": "End user license", "status": "active"}})
	def.Records = append(def.Records, recsdocument)
	recsitem := seedCollection{Collection: "ai.gftd.apps.software.item"}
	recsitem.Items = append(recsitem.Items, seedRecord{ID: "iap_gems", Data: map[string]any{"id": "iap_gems", "name": "Gems Pack", "description": "In-app purchase item", "status": "active"}})
	def.Records = append(def.Records, recsitem)
	recssoftware := seedCollection{Collection: "ai.gftd.apps.software.software"}
	recssoftware.Items = append(recssoftware.Items, seedRecord{ID: "photoshop", Data: map[string]any{"id": "photoshop", "name": "Adobe Photoshop", "description": "Desktop software", "status": "active"}})
	def.Records = append(def.Records, recssoftware)
	return def
}

func SoudenGapSeeds() seedDef {
	def := seedDef{Domain: "souden", Nanoid: "sd4en01", DID: "did:web:souden.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "asset:tepco_500kv", DisplayName: "東電500kV送電線", Description: "500kV transmission line"})
	def.DIDs = append(def.DIDs, seedDID{Path: "asset:kansai_275kv", DisplayName: "関電275kV送電線", Description: "275kV transmission line"})
	def.DIDs = append(def.DIDs, seedDID{Path: "asset:chubu_substation", DisplayName: "中部電力変電所", Description: "Substation"})
	def.DIDs = append(def.DIDs, seedDID{Path: "asset:tohoku_66kv", DisplayName: "東北電力66kV配電", Description: "66kV distribution line"})
	def.DIDs = append(def.DIDs, seedDID{Path: "asset:kyushu_transformer", DisplayName: "九州電力変圧器", Description: "Power transformer"})
	recsasset := seedCollection{Collection: "ai.gftd.apps.souden.asset"}
	recsasset.Items = append(recsasset.Items, seedRecord{ID: "tepco_500kv", Data: map[string]any{"id": "tepco_500kv", "name": "東電500kV送電線", "description": "500kV transmission line", "status": "active"}})
	recsasset.Items = append(recsasset.Items, seedRecord{ID: "kansai_275kv", Data: map[string]any{"id": "kansai_275kv", "name": "関電275kV送電線", "description": "275kV transmission line", "status": "active"}})
	recsasset.Items = append(recsasset.Items, seedRecord{ID: "chubu_substation", Data: map[string]any{"id": "chubu_substation", "name": "中部電力変電所", "description": "Substation", "status": "active"}})
	recsasset.Items = append(recsasset.Items, seedRecord{ID: "tohoku_66kv", Data: map[string]any{"id": "tohoku_66kv", "name": "東北電力66kV配電", "description": "66kV distribution line", "status": "active"}})
	recsasset.Items = append(recsasset.Items, seedRecord{ID: "kyushu_transformer", Data: map[string]any{"id": "kyushu_transformer", "name": "九州電力変圧器", "description": "Power transformer", "status": "active"}})
	def.Records = append(def.Records, recsasset)
	return def
}

func SozaiGapSeeds() seedDef {
	def := seedDef{Domain: "sozai", Nanoid: "sz4ai01", DID: "did:web:sozai.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "grade:steel_ss400", DisplayName: "SS400鋼材", Description: "General structural steel"})
	def.DIDs = append(def.DIDs, seedDID{Path: "grade:aluminum_6061", DisplayName: "A6061アルミ", Description: "6061 aluminum alloy"})
	def.DIDs = append(def.DIDs, seedDID{Path: "grade:copper_c1100", DisplayName: "C1100純銅", Description: "Tough pitch copper"})
	def.DIDs = append(def.DIDs, seedDID{Path: "grade:titanium_gr2", DisplayName: "Ti Gr2チタン", Description: "Grade 2 titanium"})
	def.DIDs = append(def.DIDs, seedDID{Path: "grade:abs_resin", DisplayName: "ABS樹脂", Description: "ABS plastic"})
	def.DIDs = append(def.DIDs, seedDID{Path: "grade:cotton_organic", DisplayName: "オーガニックコットン", Description: "Organic cotton fiber"})
	def.DIDs = append(def.DIDs, seedDID{Path: "grade:silicon_wafer", DisplayName: "シリコンウェハー", Description: "300mm Si wafer"})
	recsgrade := seedCollection{Collection: "ai.gftd.apps.sozai.grade"}
	recsgrade.Items = append(recsgrade.Items, seedRecord{ID: "steel_ss400", Data: map[string]any{"id": "steel_ss400", "name": "SS400鋼材", "description": "General structural steel", "status": "active"}})
	recsgrade.Items = append(recsgrade.Items, seedRecord{ID: "aluminum_6061", Data: map[string]any{"id": "aluminum_6061", "name": "A6061アルミ", "description": "6061 aluminum alloy", "status": "active"}})
	recsgrade.Items = append(recsgrade.Items, seedRecord{ID: "copper_c1100", Data: map[string]any{"id": "copper_c1100", "name": "C1100純銅", "description": "Tough pitch copper", "status": "active"}})
	recsgrade.Items = append(recsgrade.Items, seedRecord{ID: "titanium_gr2", Data: map[string]any{"id": "titanium_gr2", "name": "Ti Gr2チタン", "description": "Grade 2 titanium", "status": "active"}})
	recsgrade.Items = append(recsgrade.Items, seedRecord{ID: "abs_resin", Data: map[string]any{"id": "abs_resin", "name": "ABS樹脂", "description": "ABS plastic", "status": "active"}})
	recsgrade.Items = append(recsgrade.Items, seedRecord{ID: "cotton_organic", Data: map[string]any{"id": "cotton_organic", "name": "オーガニックコットン", "description": "Organic cotton fiber", "status": "active"}})
	recsgrade.Items = append(recsgrade.Items, seedRecord{ID: "silicon_wafer", Data: map[string]any{"id": "silicon_wafer", "name": "シリコンウェハー", "description": "300mm Si wafer", "status": "active"}})
	def.Records = append(def.Records, recsgrade)
	return def
}

func SportsGapSeeds() seedDef {
	def := seedDef{Domain: "sports", Nanoid: "sp4rt01", DID: "did:web:sports.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "club:urawa_reds", DisplayName: "浦和レッドダイヤモンズ", Description: "J.League football club"})
	def.DIDs = append(def.DIDs, seedDID{Path: "club:yomiuri_giants", DisplayName: "読売ジャイアンツ", Description: "NPB baseball club"})
	def.DIDs = append(def.DIDs, seedDID{Path: "match:j1_final_2024", DisplayName: "J1リーグ最終節2024", Description: "J.League final matchday"})
	def.DIDs = append(def.DIDs, seedDID{Path: "club:real_madrid", DisplayName: "Real Madrid", Description: "La Liga football club"})
	def.DIDs = append(def.DIDs, seedDID{Path: "club:lakers", DisplayName: "LA Lakers", Description: "NBA basketball team"})
	recsclub := seedCollection{Collection: "ai.gftd.apps.sports.club"}
	recsclub.Items = append(recsclub.Items, seedRecord{ID: "urawa_reds", Data: map[string]any{"id": "urawa_reds", "name": "浦和レッドダイヤモンズ", "description": "J.League football club", "status": "active"}})
	recsclub.Items = append(recsclub.Items, seedRecord{ID: "yomiuri_giants", Data: map[string]any{"id": "yomiuri_giants", "name": "読売ジャイアンツ", "description": "NPB baseball club", "status": "active"}})
	recsclub.Items = append(recsclub.Items, seedRecord{ID: "real_madrid", Data: map[string]any{"id": "real_madrid", "name": "Real Madrid", "description": "La Liga football club", "status": "active"}})
	recsclub.Items = append(recsclub.Items, seedRecord{ID: "lakers", Data: map[string]any{"id": "lakers", "name": "LA Lakers", "description": "NBA basketball team", "status": "active"}})
	def.Records = append(def.Records, recsclub)
	recsmatch := seedCollection{Collection: "ai.gftd.apps.sports.match"}
	recsmatch.Items = append(recsmatch.Items, seedRecord{ID: "j1_final_2024", Data: map[string]any{"id": "j1_final_2024", "name": "J1リーグ最終節2024", "description": "J.League final matchday", "status": "active"}})
	def.Records = append(def.Records, recsmatch)
	return def
}

func SupplyChainGapSeeds() seedDef {
	def := seedDef{Domain: "supply-chain", Nanoid: "sc0v3nd1", DID: "did:web:supply-chain.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "vendor:foxconn", DisplayName: "Foxconn", Description: "Electronics manufacturing"})
	def.DIDs = append(def.DIDs, seedDID{Path: "vendor:bosch", DisplayName: "Robert Bosch", Description: "Automotive supplier"})
	def.DIDs = append(def.DIDs, seedDID{Path: "vendor:tsmc", DisplayName: "TSMC", Description: "Semiconductor foundry"})
	def.DIDs = append(def.DIDs, seedDID{Path: "vendor:maersk", DisplayName: "Maersk", Description: "Container shipping"})
	def.DIDs = append(def.DIDs, seedDID{Path: "vendor:dhl_logistics", DisplayName: "DHL Supply Chain", Description: "Logistics provider"})
	recsvendor := seedCollection{Collection: "ai.gftd.apps.supplychain.vendor"}
	recsvendor.Items = append(recsvendor.Items, seedRecord{ID: "foxconn", Data: map[string]any{"id": "foxconn", "name": "Foxconn", "description": "Electronics manufacturing", "status": "active"}})
	recsvendor.Items = append(recsvendor.Items, seedRecord{ID: "bosch", Data: map[string]any{"id": "bosch", "name": "Robert Bosch", "description": "Automotive supplier", "status": "active"}})
	recsvendor.Items = append(recsvendor.Items, seedRecord{ID: "tsmc", Data: map[string]any{"id": "tsmc", "name": "TSMC", "description": "Semiconductor foundry", "status": "active"}})
	recsvendor.Items = append(recsvendor.Items, seedRecord{ID: "maersk", Data: map[string]any{"id": "maersk", "name": "Maersk", "description": "Container shipping", "status": "active"}})
	recsvendor.Items = append(recsvendor.Items, seedRecord{ID: "dhl_logistics", Data: map[string]any{"id": "dhl_logistics", "name": "DHL Supply Chain", "description": "Logistics provider", "status": "active"}})
	def.Records = append(def.Records, recsvendor)
	return def
}

func SyosetsuGapSeeds() seedDef {
	def := seedDef{Domain: "syosetsu", Nanoid: "sy3w9p4m", DID: "did:web:syosetsu.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "title:mushoku_tensei", DisplayName: "無職転生", Description: "Isekai light novel"})
	def.DIDs = append(def.DIDs, seedDID{Path: "title:sao", DisplayName: "ソードアート・オンライン", Description: "SAO light novel"})
	def.DIDs = append(def.DIDs, seedDID{Path: "title:overlord", DisplayName: "オーバーロード", Description: "Overlord light novel"})
	def.DIDs = append(def.DIDs, seedDID{Path: "title:rezero", DisplayName: "Re:ゼロ", Description: "Re:Zero light novel"})
	def.DIDs = append(def.DIDs, seedDID{Path: "title:konosuba", DisplayName: "このすば", Description: "KonoSuba light novel"})
	recstitle := seedCollection{Collection: "ai.gftd.apps.syosetsu.title"}
	recstitle.Items = append(recstitle.Items, seedRecord{ID: "mushoku_tensei", Data: map[string]any{"id": "mushoku_tensei", "name": "無職転生", "description": "Isekai light novel", "status": "active"}})
	recstitle.Items = append(recstitle.Items, seedRecord{ID: "sao", Data: map[string]any{"id": "sao", "name": "ソードアート・オンライン", "description": "SAO light novel", "status": "active"}})
	recstitle.Items = append(recstitle.Items, seedRecord{ID: "overlord", Data: map[string]any{"id": "overlord", "name": "オーバーロード", "description": "Overlord light novel", "status": "active"}})
	recstitle.Items = append(recstitle.Items, seedRecord{ID: "rezero", Data: map[string]any{"id": "rezero", "name": "Re:ゼロ", "description": "Re:Zero light novel", "status": "active"}})
	recstitle.Items = append(recstitle.Items, seedRecord{ID: "konosuba", Data: map[string]any{"id": "konosuba", "name": "このすば", "description": "KonoSuba light novel", "status": "active"}})
	def.Records = append(def.Records, recstitle)
	return def
}

func TaxiGapSeeds() seedDef {
	def := seedDef{Domain: "taxi", Nanoid: "tx4xi01", DID: "did:web:taxi.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "vehicle:nihon_kotsu_01", DisplayName: "日本交通01", Description: "Nihon Kotsu taxi"})
	def.DIDs = append(def.DIDs, seedDID{Path: "vehicle:daichi_01", DisplayName: "第一交通01", Description: "Daiichi Kotsu taxi"})
	def.DIDs = append(def.DIDs, seedDID{Path: "vehicle:kmtaxi_01", DisplayName: "kmタクシー01", Description: "KM taxi"})
	def.DIDs = append(def.DIDs, seedDID{Path: "vehicle:uber_black", DisplayName: "Uber Black", Description: "Premium ride service"})
	def.DIDs = append(def.DIDs, seedDID{Path: "vehicle:goto_taxi", DisplayName: "GOタクシー", Description: "GO taxi app"})
	recsvehicle := seedCollection{Collection: "ai.gftd.apps.taxi.vehicle"}
	recsvehicle.Items = append(recsvehicle.Items, seedRecord{ID: "nihon_kotsu_01", Data: map[string]any{"id": "nihon_kotsu_01", "name": "日本交通01", "description": "Nihon Kotsu taxi", "status": "active"}})
	recsvehicle.Items = append(recsvehicle.Items, seedRecord{ID: "daichi_01", Data: map[string]any{"id": "daichi_01", "name": "第一交通01", "description": "Daiichi Kotsu taxi", "status": "active"}})
	recsvehicle.Items = append(recsvehicle.Items, seedRecord{ID: "kmtaxi_01", Data: map[string]any{"id": "kmtaxi_01", "name": "kmタクシー01", "description": "KM taxi", "status": "active"}})
	recsvehicle.Items = append(recsvehicle.Items, seedRecord{ID: "uber_black", Data: map[string]any{"id": "uber_black", "name": "Uber Black", "description": "Premium ride service", "status": "active"}})
	recsvehicle.Items = append(recsvehicle.Items, seedRecord{ID: "goto_taxi", Data: map[string]any{"id": "goto_taxi", "name": "GOタクシー", "description": "GO taxi app", "status": "active"}})
	def.Records = append(def.Records, recsvehicle)
	return def
}

func TentaiGapSeeds() seedDef {
	def := seedDef{Domain: "tentai", Nanoid: "tnt4ib0d", DID: "did:web:tentai.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "star:sun", DisplayName: "太陽 (Sun)", Description: "G2V main sequence star"})
	def.DIDs = append(def.DIDs, seedDID{Path: "star:proxima_centauri", DisplayName: "プロキシマ・ケンタウリ", Description: "Nearest star 4.24 ly"})
	def.DIDs = append(def.DIDs, seedDID{Path: "exoplanet:proxima_b", DisplayName: "プロキシマb", Description: "Habitable zone exoplanet"})
	def.DIDs = append(def.DIDs, seedDID{Path: "galaxy:milky_way", DisplayName: "天の川銀河", Description: "Our galaxy"})
	def.DIDs = append(def.DIDs, seedDID{Path: "galaxy:andromeda", DisplayName: "アンドロメダ銀河", Description: "Nearest large galaxy"})
	def.DIDs = append(def.DIDs, seedDID{Path: "asteroid:bennu", DisplayName: "ベンヌ", Description: "Near-Earth asteroid"})
	def.DIDs = append(def.DIDs, seedDID{Path: "comet:halley", DisplayName: "ハレー彗星", Description: "Periodic comet 76yr"})
	def.DIDs = append(def.DIDs, seedDID{Path: "moon:luna", DisplayName: "月 (Moon)", Description: "Earth's natural satellite"})
	recsstar := seedCollection{Collection: "ai.gftd.apps.tentai.star"}
	recsstar.Items = append(recsstar.Items, seedRecord{ID: "sun", Data: map[string]any{"id": "sun", "name": "太陽 (Sun)", "description": "G2V main sequence star", "status": "active"}})
	recsstar.Items = append(recsstar.Items, seedRecord{ID: "proxima_centauri", Data: map[string]any{"id": "proxima_centauri", "name": "プロキシマ・ケンタウリ", "description": "Nearest star 4.24 ly", "status": "active"}})
	def.Records = append(def.Records, recsstar)
	recsexoplanet := seedCollection{Collection: "ai.gftd.apps.tentai.exoplanet"}
	recsexoplanet.Items = append(recsexoplanet.Items, seedRecord{ID: "proxima_b", Data: map[string]any{"id": "proxima_b", "name": "プロキシマb", "description": "Habitable zone exoplanet", "status": "active"}})
	def.Records = append(def.Records, recsexoplanet)
	recsgalaxy := seedCollection{Collection: "ai.gftd.apps.tentai.galaxy"}
	recsgalaxy.Items = append(recsgalaxy.Items, seedRecord{ID: "milky_way", Data: map[string]any{"id": "milky_way", "name": "天の川銀河", "description": "Our galaxy", "status": "active"}})
	recsgalaxy.Items = append(recsgalaxy.Items, seedRecord{ID: "andromeda", Data: map[string]any{"id": "andromeda", "name": "アンドロメダ銀河", "description": "Nearest large galaxy", "status": "active"}})
	def.Records = append(def.Records, recsgalaxy)
	recsasteroid := seedCollection{Collection: "ai.gftd.apps.tentai.asteroid"}
	recsasteroid.Items = append(recsasteroid.Items, seedRecord{ID: "bennu", Data: map[string]any{"id": "bennu", "name": "ベンヌ", "description": "Near-Earth asteroid", "status": "active"}})
	def.Records = append(def.Records, recsasteroid)
	recscomet := seedCollection{Collection: "ai.gftd.apps.tentai.comet"}
	recscomet.Items = append(recscomet.Items, seedRecord{ID: "halley", Data: map[string]any{"id": "halley", "name": "ハレー彗星", "description": "Periodic comet 76yr", "status": "active"}})
	def.Records = append(def.Records, recscomet)
	recsmoon := seedCollection{Collection: "ai.gftd.apps.tentai.moon"}
	recsmoon.Items = append(recsmoon.Items, seedRecord{ID: "luna", Data: map[string]any{"id": "luna", "name": "月 (Moon)", "description": "Earth's natural satellite", "status": "active"}})
	def.Records = append(def.Records, recsmoon)
	return def
}

func TorihikiGapSeeds() seedDef {
	def := seedDef{Domain: "torihiki", Nanoid: "toriaf63", DID: "did:web:torihiki.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "order:buy_7203", DisplayName: "トヨタ買注文", Description: "Toyota stock buy order"})
	def.DIDs = append(def.DIDs, seedDID{Path: "order:sell_6758", DisplayName: "ソニー売注文", Description: "Sony stock sell order"})
	def.DIDs = append(def.DIDs, seedDID{Path: "order:fx_usdjpy", DisplayName: "USD/JPY注文", Description: "FX trade order"})
	def.DIDs = append(def.DIDs, seedDID{Path: "order:bond_jgb", DisplayName: "JGB注文", Description: "Government bond order"})
	def.DIDs = append(def.DIDs, seedDID{Path: "order:etf_topix", DisplayName: "TOPIX ETF注文", Description: "ETF trade order"})
	recsorder := seedCollection{Collection: "ai.gftd.apps.torihiki.order"}
	recsorder.Items = append(recsorder.Items, seedRecord{ID: "buy_7203", Data: map[string]any{"id": "buy_7203", "name": "トヨタ買注文", "description": "Toyota stock buy order", "status": "active"}})
	recsorder.Items = append(recsorder.Items, seedRecord{ID: "sell_6758", Data: map[string]any{"id": "sell_6758", "name": "ソニー売注文", "description": "Sony stock sell order", "status": "active"}})
	recsorder.Items = append(recsorder.Items, seedRecord{ID: "fx_usdjpy", Data: map[string]any{"id": "fx_usdjpy", "name": "USD/JPY注文", "description": "FX trade order", "status": "active"}})
	recsorder.Items = append(recsorder.Items, seedRecord{ID: "bond_jgb", Data: map[string]any{"id": "bond_jgb", "name": "JGB注文", "description": "Government bond order", "status": "active"}})
	recsorder.Items = append(recsorder.Items, seedRecord{ID: "etf_topix", Data: map[string]any{"id": "etf_topix", "name": "TOPIX ETF注文", "description": "ETF trade order", "status": "active"}})
	def.Records = append(def.Records, recsorder)
	return def
}

func ToshokanGapSeeds() seedDef {
	def := seedDef{Domain: "toshokan", Nanoid: "ts4kn01", DID: "did:web:toshokan.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "library:ndl", DisplayName: "国立国会図書館", Description: "National Diet Library"})
	def.DIDs = append(def.DIDs, seedDID{Path: "library:nypl", DisplayName: "New York Public Library", Description: "NYPL"})
	def.DIDs = append(def.DIDs, seedDID{Path: "library:british_library", DisplayName: "British Library", Description: "UK national library"})
	def.DIDs = append(def.DIDs, seedDID{Path: "library:bnf", DisplayName: "Bibliothèque nationale de France", Description: "BnF"})
	def.DIDs = append(def.DIDs, seedDID{Path: "library:osaka_central", DisplayName: "大阪市立中央図書館", Description: "Osaka Central Library"})
	recslibrary := seedCollection{Collection: "ai.gftd.apps.toshokan.library"}
	recslibrary.Items = append(recslibrary.Items, seedRecord{ID: "ndl", Data: map[string]any{"id": "ndl", "name": "国立国会図書館", "description": "National Diet Library", "status": "active"}})
	recslibrary.Items = append(recslibrary.Items, seedRecord{ID: "nypl", Data: map[string]any{"id": "nypl", "name": "New York Public Library", "description": "NYPL", "status": "active"}})
	recslibrary.Items = append(recslibrary.Items, seedRecord{ID: "british_library", Data: map[string]any{"id": "british_library", "name": "British Library", "description": "UK national library", "status": "active"}})
	recslibrary.Items = append(recslibrary.Items, seedRecord{ID: "bnf", Data: map[string]any{"id": "bnf", "name": "Bibliothèque nationale de France", "description": "BnF", "status": "active"}})
	recslibrary.Items = append(recslibrary.Items, seedRecord{ID: "osaka_central", Data: map[string]any{"id": "osaka_central", "name": "大阪市立中央図書館", "description": "Osaka Central Library", "status": "active"}})
	def.Records = append(def.Records, recslibrary)
	return def
}

func TraditionGapSeeds() seedDef {
	def := seedDef{Domain: "tradition", Nanoid: "trdtn001", DID: "did:web:tradition.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "tradition:bushido", DisplayName: "武士道", Description: "Samurai code of conduct"})
	def.DIDs = append(def.DIDs, seedDID{Path: "tradition:chado", DisplayName: "茶道", Description: "Japanese tea ceremony"})
	def.DIDs = append(def.DIDs, seedDID{Path: "tradition:ikebana", DisplayName: "華道", Description: "Japanese flower arrangement"})
	def.DIDs = append(def.DIDs, seedDID{Path: "tradition:confucian_filial", DisplayName: "儒教孝道", Description: "Confucian filial piety"})
	def.DIDs = append(def.DIDs, seedDID{Path: "tradition:ubuntu_africa", DisplayName: "Ubuntu", Description: "African communal philosophy"})
	recstradition := seedCollection{Collection: "ai.gftd.apps.tradition.tradition"}
	recstradition.Items = append(recstradition.Items, seedRecord{ID: "bushido", Data: map[string]any{"id": "bushido", "name": "武士道", "description": "Samurai code of conduct", "status": "active"}})
	recstradition.Items = append(recstradition.Items, seedRecord{ID: "chado", Data: map[string]any{"id": "chado", "name": "茶道", "description": "Japanese tea ceremony", "status": "active"}})
	recstradition.Items = append(recstradition.Items, seedRecord{ID: "ikebana", Data: map[string]any{"id": "ikebana", "name": "華道", "description": "Japanese flower arrangement", "status": "active"}})
	recstradition.Items = append(recstradition.Items, seedRecord{ID: "confucian_filial", Data: map[string]any{"id": "confucian_filial", "name": "儒教孝道", "description": "Confucian filial piety", "status": "active"}})
	recstradition.Items = append(recstradition.Items, seedRecord{ID: "ubuntu_africa", Data: map[string]any{"id": "ubuntu_africa", "name": "Ubuntu", "description": "African communal philosophy", "status": "active"}})
	def.Records = append(def.Records, recstradition)
	return def
}

func TrustGapSeeds() seedDef {
	def := seedDef{Domain: "trust", Nanoid: "tr5tc0r3", DID: "did:web:trust.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "did:high_trust", DisplayName: "High Trust DID", Description: "Trust score >= 0.9"})
	def.DIDs = append(def.DIDs, seedDID{Path: "did:medium_trust", DisplayName: "Medium Trust DID", Description: "Trust score 0.5-0.9"})
	def.DIDs = append(def.DIDs, seedDID{Path: "did:new_entity", DisplayName: "New Entity DID", Description: "Trust score pending"})
	def.DIDs = append(def.DIDs, seedDID{Path: "did:verified_org", DisplayName: "Verified Org DID", Description: "Organization verified"})
	def.DIDs = append(def.DIDs, seedDID{Path: "did:flagged", DisplayName: "Flagged DID", Description: "Trust score < 0.3"})
	recsdid := seedCollection{Collection: "ai.gftd.apps.trust.did"}
	recsdid.Items = append(recsdid.Items, seedRecord{ID: "high_trust", Data: map[string]any{"id": "high_trust", "name": "High Trust DID", "description": "Trust score >= 0.9", "status": "active"}})
	recsdid.Items = append(recsdid.Items, seedRecord{ID: "medium_trust", Data: map[string]any{"id": "medium_trust", "name": "Medium Trust DID", "description": "Trust score 0.5-0.9", "status": "active"}})
	recsdid.Items = append(recsdid.Items, seedRecord{ID: "new_entity", Data: map[string]any{"id": "new_entity", "name": "New Entity DID", "description": "Trust score pending", "status": "active"}})
	recsdid.Items = append(recsdid.Items, seedRecord{ID: "verified_org", Data: map[string]any{"id": "verified_org", "name": "Verified Org DID", "description": "Organization verified", "status": "active"}})
	recsdid.Items = append(recsdid.Items, seedRecord{ID: "flagged", Data: map[string]any{"id": "flagged", "name": "Flagged DID", "description": "Trust score < 0.3", "status": "active"}})
	def.Records = append(def.Records, recsdid)
	return def
}

func TsukanGapSeeds() seedDef {
	def := seedDef{Domain: "tsukan", Nanoid: "hk4bt01", DID: "did:web:tsukan.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "declaration:import_001", DisplayName: "輸入通関申告001", Description: "Import customs declaration"})
	def.DIDs = append(def.DIDs, seedDID{Path: "declaration:export_001", DisplayName: "輸出通関申告001", Description: "Export customs declaration"})
	def.DIDs = append(def.DIDs, seedDID{Path: "declaration:transit_001", DisplayName: "通過通関001", Description: "Transit declaration"})
	def.DIDs = append(def.DIDs, seedDID{Path: "declaration:bonded_001", DisplayName: "保税申告001", Description: "Bonded warehouse declaration"})
	def.DIDs = append(def.DIDs, seedDID{Path: "declaration:ata_carnet", DisplayName: "ATAカルネ", Description: "ATA Carnet temporary import"})
	recsdeclaration := seedCollection{Collection: "ai.gftd.apps.tsukan.declaration"}
	recsdeclaration.Items = append(recsdeclaration.Items, seedRecord{ID: "import_001", Data: map[string]any{"id": "import_001", "name": "輸入通関申告001", "description": "Import customs declaration", "status": "active"}})
	recsdeclaration.Items = append(recsdeclaration.Items, seedRecord{ID: "export_001", Data: map[string]any{"id": "export_001", "name": "輸出通関申告001", "description": "Export customs declaration", "status": "active"}})
	recsdeclaration.Items = append(recsdeclaration.Items, seedRecord{ID: "transit_001", Data: map[string]any{"id": "transit_001", "name": "通過通関001", "description": "Transit declaration", "status": "active"}})
	recsdeclaration.Items = append(recsdeclaration.Items, seedRecord{ID: "bonded_001", Data: map[string]any{"id": "bonded_001", "name": "保税申告001", "description": "Bonded warehouse declaration", "status": "active"}})
	recsdeclaration.Items = append(recsdeclaration.Items, seedRecord{ID: "ata_carnet", Data: map[string]any{"id": "ata_carnet", "name": "ATAカルネ", "description": "ATA Carnet temporary import", "status": "active"}})
	def.Records = append(def.Records, recsdeclaration)
	return def
}

func UchuGapSeeds() seedDef {
	def := seedDef{Domain: "uchu", Nanoid: "uch4m1s1", DID: "did:web:uchu.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "launch:falcon9_001", DisplayName: "Falcon 9 Launch 001", Description: "SpaceX LEO launch"})
	def.DIDs = append(def.DIDs, seedDID{Path: "launch:h3_001", DisplayName: "H3ロケット001", Description: "JAXA H3 launch"})
	def.DIDs = append(def.DIDs, seedDID{Path: "launch:ariane6", DisplayName: "Ariane 6", Description: "ESA launch vehicle"})
	def.DIDs = append(def.DIDs, seedDID{Path: "debris:cosmos_2251", DisplayName: "Cosmos 2251 Debris", Description: "LEO debris cloud"})
	def.DIDs = append(def.DIDs, seedDID{Path: "debris:fengyun_1c", DisplayName: "Fengyun-1C Debris", Description: "ASAT test debris"})
	recslaunch := seedCollection{Collection: "ai.gftd.apps.uchu.launch"}
	recslaunch.Items = append(recslaunch.Items, seedRecord{ID: "falcon9_001", Data: map[string]any{"id": "falcon9_001", "name": "Falcon 9 Launch 001", "description": "SpaceX LEO launch", "status": "active"}})
	recslaunch.Items = append(recslaunch.Items, seedRecord{ID: "h3_001", Data: map[string]any{"id": "h3_001", "name": "H3ロケット001", "description": "JAXA H3 launch", "status": "active"}})
	recslaunch.Items = append(recslaunch.Items, seedRecord{ID: "ariane6", Data: map[string]any{"id": "ariane6", "name": "Ariane 6", "description": "ESA launch vehicle", "status": "active"}})
	def.Records = append(def.Records, recslaunch)
	recsdebris := seedCollection{Collection: "ai.gftd.apps.uchu.debris"}
	recsdebris.Items = append(recsdebris.Items, seedRecord{ID: "cosmos_2251", Data: map[string]any{"id": "cosmos_2251", "name": "Cosmos 2251 Debris", "description": "LEO debris cloud", "status": "active"}})
	recsdebris.Items = append(recsdebris.Items, seedRecord{ID: "fengyun_1c", Data: map[string]any{"id": "fengyun_1c", "name": "Fengyun-1C Debris", "description": "ASAT test debris", "status": "active"}})
	def.Records = append(def.Records, recsdebris)
	return def
}

func UnkouGapSeeds() seedDef {
	def := seedDef{Domain: "unkou", Nanoid: "unko05af", DID: "did:web:unkou.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "service:tokaido_shinkansen", DisplayName: "東海道新幹線運行", Description: "Tokaido Shinkansen service"})
	def.DIDs = append(def.DIDs, seedDID{Path: "service:yamanote_line", DisplayName: "山手線運行", Description: "Yamanote Line service"})
	def.DIDs = append(def.DIDs, seedDID{Path: "service:haneda_flights", DisplayName: "羽田空港発着", Description: "Haneda Airport flights"})
	def.DIDs = append(def.DIDs, seedDID{Path: "service:tomei_highway", DisplayName: "東名高速交通情報", Description: "Tomei highway traffic"})
	def.DIDs = append(def.DIDs, seedDID{Path: "service:tokyo_metro", DisplayName: "東京メトロ運行", Description: "Tokyo Metro service"})
	recsservice := seedCollection{Collection: "ai.gftd.apps.unkou.service"}
	recsservice.Items = append(recsservice.Items, seedRecord{ID: "tokaido_shinkansen", Data: map[string]any{"id": "tokaido_shinkansen", "name": "東海道新幹線運行", "description": "Tokaido Shinkansen service", "status": "active"}})
	recsservice.Items = append(recsservice.Items, seedRecord{ID: "yamanote_line", Data: map[string]any{"id": "yamanote_line", "name": "山手線運行", "description": "Yamanote Line service", "status": "active"}})
	recsservice.Items = append(recsservice.Items, seedRecord{ID: "haneda_flights", Data: map[string]any{"id": "haneda_flights", "name": "羽田空港発着", "description": "Haneda Airport flights", "status": "active"}})
	recsservice.Items = append(recsservice.Items, seedRecord{ID: "tomei_highway", Data: map[string]any{"id": "tomei_highway", "name": "東名高速交通情報", "description": "Tomei highway traffic", "status": "active"}})
	recsservice.Items = append(recsservice.Items, seedRecord{ID: "tokyo_metro", Data: map[string]any{"id": "tokyo_metro", "name": "東京メトロ運行", "description": "Tokyo Metro service", "status": "active"}})
	def.Records = append(def.Records, recsservice)
	return def
}

func UnspscGapSeeds() seedDef {
	def := seedDef{Domain: "unspsc", Nanoid: "unspe5a7", DID: "did:web:unspsc.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "commodity:desktop_pc", DisplayName: "Desktop PC", Description: "UNSPSC 43211500"})
	def.DIDs = append(def.DIDs, seedDID{Path: "commodity:office_paper", DisplayName: "Office Paper", Description: "UNSPSC 14111500"})
	def.DIDs = append(def.DIDs, seedDID{Path: "commodity:safety_helmet", DisplayName: "Safety Helmet", Description: "UNSPSC 46181500"})
	def.DIDs = append(def.DIDs, seedDID{Path: "commodity:cleaning_supply", DisplayName: "Cleaning Supplies", Description: "UNSPSC 47131500"})
	def.DIDs = append(def.DIDs, seedDID{Path: "commodity:catering", DisplayName: "Catering Services", Description: "UNSPSC 90101600"})
	recscommodity := seedCollection{Collection: "ai.gftd.apps.unspsc.commodity"}
	recscommodity.Items = append(recscommodity.Items, seedRecord{ID: "desktop_pc", Data: map[string]any{"id": "desktop_pc", "name": "Desktop PC", "description": "UNSPSC 43211500", "status": "active"}})
	recscommodity.Items = append(recscommodity.Items, seedRecord{ID: "office_paper", Data: map[string]any{"id": "office_paper", "name": "Office Paper", "description": "UNSPSC 14111500", "status": "active"}})
	recscommodity.Items = append(recscommodity.Items, seedRecord{ID: "safety_helmet", Data: map[string]any{"id": "safety_helmet", "name": "Safety Helmet", "description": "UNSPSC 46181500", "status": "active"}})
	recscommodity.Items = append(recscommodity.Items, seedRecord{ID: "cleaning_supply", Data: map[string]any{"id": "cleaning_supply", "name": "Cleaning Supplies", "description": "UNSPSC 47131500", "status": "active"}})
	recscommodity.Items = append(recscommodity.Items, seedRecord{ID: "catering", Data: map[string]any{"id": "catering", "name": "Catering Services", "description": "UNSPSC 90101600", "status": "active"}})
	def.Records = append(def.Records, recscommodity)
	return def
}

func VehicleGapSeeds() seedDef {
	def := seedDef{Domain: "vehicle", Nanoid: "vh1cl3rk", DID: "did:web:vehicle.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "vehicle:toyota_camry", DisplayName: "Toyota Camry", Description: "Mid-size sedan"})
	def.DIDs = append(def.DIDs, seedDID{Path: "vehicle:tesla_model3", DisplayName: "Tesla Model 3", Description: "Electric sedan"})
	def.DIDs = append(def.DIDs, seedDID{Path: "vehicle:ford_f150", DisplayName: "Ford F-150", Description: "Pickup truck"})
	def.DIDs = append(def.DIDs, seedDID{Path: "vehicle:bmw_3series", DisplayName: "BMW 3 Series", Description: "Luxury sedan"})
	def.DIDs = append(def.DIDs, seedDID{Path: "vehicle:vw_golf", DisplayName: "VW Golf", Description: "Compact hatchback"})
	def.DIDs = append(def.DIDs, seedDID{Path: "vehicle:hyundai_ioniq5", DisplayName: "Hyundai IONIQ 5", Description: "Electric SUV"})
	recsvehicle := seedCollection{Collection: "ai.gftd.apps.vehicle.vehicle"}
	recsvehicle.Items = append(recsvehicle.Items, seedRecord{ID: "toyota_camry", Data: map[string]any{"id": "toyota_camry", "name": "Toyota Camry", "description": "Mid-size sedan", "status": "active"}})
	recsvehicle.Items = append(recsvehicle.Items, seedRecord{ID: "tesla_model3", Data: map[string]any{"id": "tesla_model3", "name": "Tesla Model 3", "description": "Electric sedan", "status": "active"}})
	recsvehicle.Items = append(recsvehicle.Items, seedRecord{ID: "ford_f150", Data: map[string]any{"id": "ford_f150", "name": "Ford F-150", "description": "Pickup truck", "status": "active"}})
	recsvehicle.Items = append(recsvehicle.Items, seedRecord{ID: "bmw_3series", Data: map[string]any{"id": "bmw_3series", "name": "BMW 3 Series", "description": "Luxury sedan", "status": "active"}})
	recsvehicle.Items = append(recsvehicle.Items, seedRecord{ID: "vw_golf", Data: map[string]any{"id": "vw_golf", "name": "VW Golf", "description": "Compact hatchback", "status": "active"}})
	recsvehicle.Items = append(recsvehicle.Items, seedRecord{ID: "hyundai_ioniq5", Data: map[string]any{"id": "hyundai_ioniq5", "name": "Hyundai IONIQ 5", "description": "Electric SUV", "status": "active"}})
	def.Records = append(def.Records, recsvehicle)
	return def
}

func VesselGapSeeds() seedDef {
	def := seedDef{Domain: "vessel", Nanoid: "vs8jn4lc", DID: "did:web:vessel.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "vessel:ever_given", DisplayName: "Ever Given", Description: "Ultra-large container ship"})
	def.DIDs = append(def.DIDs, seedDID{Path: "vessel:yamato_tanker", DisplayName: "大和タンカー", Description: "VLCC crude tanker"})
	def.DIDs = append(def.DIDs, seedDID{Path: "vessel:queen_mary2", DisplayName: "Queen Mary 2", Description: "Ocean liner"})
	def.DIDs = append(def.DIDs, seedDID{Path: "vessel:maersk_mc_kinney", DisplayName: "Maersk Mc-Kinney Moller", Description: "Triple-E container ship"})
	def.DIDs = append(def.DIDs, seedDID{Path: "vessel:lng_carrier_01", DisplayName: "LNG Carrier 01", Description: "Q-Max LNG carrier"})
	def.DIDs = append(def.DIDs, seedDID{Path: "vessel:bulk_carrier_01", DisplayName: "Cape-size Bulk Carrier", Description: "Iron ore bulk carrier"})
	def.DIDs = append(def.DIDs, seedDID{Path: "vessel:fishing_vessel_01", DisplayName: "遠洋マグロ漁船", Description: "Deep-sea tuna fishing vessel"})
	def.DIDs = append(def.DIDs, seedDID{Path: "vessel:icebreaker_shirase", DisplayName: "しらせ", Description: "Antarctic icebreaker"})
	recsvessel := seedCollection{Collection: "ai.gftd.apps.vessel.vessel"}
	recsvessel.Items = append(recsvessel.Items, seedRecord{ID: "ever_given", Data: map[string]any{"id": "ever_given", "name": "Ever Given", "description": "Ultra-large container ship", "status": "active"}})
	recsvessel.Items = append(recsvessel.Items, seedRecord{ID: "yamato_tanker", Data: map[string]any{"id": "yamato_tanker", "name": "大和タンカー", "description": "VLCC crude tanker", "status": "active"}})
	recsvessel.Items = append(recsvessel.Items, seedRecord{ID: "queen_mary2", Data: map[string]any{"id": "queen_mary2", "name": "Queen Mary 2", "description": "Ocean liner", "status": "active"}})
	recsvessel.Items = append(recsvessel.Items, seedRecord{ID: "maersk_mc_kinney", Data: map[string]any{"id": "maersk_mc_kinney", "name": "Maersk Mc-Kinney Moller", "description": "Triple-E container ship", "status": "active"}})
	recsvessel.Items = append(recsvessel.Items, seedRecord{ID: "lng_carrier_01", Data: map[string]any{"id": "lng_carrier_01", "name": "LNG Carrier 01", "description": "Q-Max LNG carrier", "status": "active"}})
	recsvessel.Items = append(recsvessel.Items, seedRecord{ID: "bulk_carrier_01", Data: map[string]any{"id": "bulk_carrier_01", "name": "Cape-size Bulk Carrier", "description": "Iron ore bulk carrier", "status": "active"}})
	recsvessel.Items = append(recsvessel.Items, seedRecord{ID: "fishing_vessel_01", Data: map[string]any{"id": "fishing_vessel_01", "name": "遠洋マグロ漁船", "description": "Deep-sea tuna fishing vessel", "status": "active"}})
	recsvessel.Items = append(recsvessel.Items, seedRecord{ID: "icebreaker_shirase", Data: map[string]any{"id": "icebreaker_shirase", "name": "しらせ", "description": "Antarctic icebreaker", "status": "active"}})
	def.Records = append(def.Records, recsvessel)
	return def
}

func VisaGapSeeds() seedDef {
	def := seedDef{Domain: "visa", Nanoid: "vs4ia01", DID: "did:web:visa.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "visa:jp_tourist", DisplayName: "日本観光ビザ", Description: "Japan tourist visa"})
	def.DIDs = append(def.DIDs, seedDID{Path: "visa:us_b1b2", DisplayName: "US B1/B2", Description: "US business/tourist visa"})
	def.DIDs = append(def.DIDs, seedDID{Path: "visa:schengen", DisplayName: "シェンゲンビザ", Description: "Schengen area visa"})
	def.DIDs = append(def.DIDs, seedDID{Path: "visa:jp_work", DisplayName: "日本就労ビザ", Description: "Japan work visa"})
	def.DIDs = append(def.DIDs, seedDID{Path: "visa:uk_tier2", DisplayName: "UK Skilled Worker", Description: "UK work visa"})
	recsvisa := seedCollection{Collection: "ai.gftd.apps.visa.visa"}
	recsvisa.Items = append(recsvisa.Items, seedRecord{ID: "jp_tourist", Data: map[string]any{"id": "jp_tourist", "name": "日本観光ビザ", "description": "Japan tourist visa", "status": "active"}})
	recsvisa.Items = append(recsvisa.Items, seedRecord{ID: "us_b1b2", Data: map[string]any{"id": "us_b1b2", "name": "US B1/B2", "description": "US business/tourist visa", "status": "active"}})
	recsvisa.Items = append(recsvisa.Items, seedRecord{ID: "schengen", Data: map[string]any{"id": "schengen", "name": "シェンゲンビザ", "description": "Schengen area visa", "status": "active"}})
	recsvisa.Items = append(recsvisa.Items, seedRecord{ID: "jp_work", Data: map[string]any{"id": "jp_work", "name": "日本就労ビザ", "description": "Japan work visa", "status": "active"}})
	recsvisa.Items = append(recsvisa.Items, seedRecord{ID: "uk_tier2", Data: map[string]any{"id": "uk_tier2", "name": "UK Skilled Worker", "description": "UK work visa", "status": "active"}})
	def.Records = append(def.Records, recsvisa)
	return def
}

func WarehouseGapSeeds() seedDef {
	def := seedDef{Domain: "warehouse", Nanoid: "wh2cn7gd", DID: "did:web:warehouse.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "warehouse:amazon_nrt1", DisplayName: "Amazon NRT1", Description: "Amazon fulfillment center Ichikawa"})
	def.DIDs = append(def.DIDs, seedDID{Path: "warehouse:rakuten_chiba", DisplayName: "楽天千葉倉庫", Description: "Rakuten warehouse Chiba"})
	def.DIDs = append(def.DIDs, seedDID{Path: "warehouse:yamato_atsugi", DisplayName: "ヤマト厚木ベース", Description: "Yamato sort center"})
	def.DIDs = append(def.DIDs, seedDID{Path: "warehouse:cold_storage_tokyo", DisplayName: "冷蔵倉庫東京", Description: "Cold storage Tokyo"})
	def.DIDs = append(def.DIDs, seedDID{Path: "warehouse:bonded_yokohama", DisplayName: "横浜保税倉庫", Description: "Bonded warehouse Yokohama"})
	recswarehouse := seedCollection{Collection: "ai.gftd.apps.warehouse.warehouse"}
	recswarehouse.Items = append(recswarehouse.Items, seedRecord{ID: "amazon_nrt1", Data: map[string]any{"id": "amazon_nrt1", "name": "Amazon NRT1", "description": "Amazon fulfillment center Ichikawa", "status": "active"}})
	recswarehouse.Items = append(recswarehouse.Items, seedRecord{ID: "rakuten_chiba", Data: map[string]any{"id": "rakuten_chiba", "name": "楽天千葉倉庫", "description": "Rakuten warehouse Chiba", "status": "active"}})
	recswarehouse.Items = append(recswarehouse.Items, seedRecord{ID: "yamato_atsugi", Data: map[string]any{"id": "yamato_atsugi", "name": "ヤマト厚木ベース", "description": "Yamato sort center", "status": "active"}})
	recswarehouse.Items = append(recswarehouse.Items, seedRecord{ID: "cold_storage_tokyo", Data: map[string]any{"id": "cold_storage_tokyo", "name": "冷蔵倉庫東京", "description": "Cold storage Tokyo", "status": "active"}})
	recswarehouse.Items = append(recswarehouse.Items, seedRecord{ID: "bonded_yokohama", Data: map[string]any{"id": "bonded_yokohama", "name": "横浜保税倉庫", "description": "Bonded warehouse Yokohama", "status": "active"}})
	def.Records = append(def.Records, recswarehouse)
	return def
}

func WaterGapSeeds() seedDef {
	def := seedDef{Domain: "water", Nanoid: "wt7fm2qs", DID: "did:web:water.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "utility:thames_water", DisplayName: "Thames Water", Description: "London water utility"})
	def.DIDs = append(def.DIDs, seedDID{Path: "utility:veolia_paris", DisplayName: "Veolia Paris", Description: "Paris water service"})
	def.DIDs = append(def.DIDs, seedDID{Path: "utility:tokyo_waterworks", DisplayName: "東京都水道局", Description: "Tokyo water supply"})
	def.DIDs = append(def.DIDs, seedDID{Path: "utility:suez_global", DisplayName: "SUEZ", Description: "Global water utility"})
	def.DIDs = append(def.DIDs, seedDID{Path: "utility:american_water", DisplayName: "American Water", Description: "US water utility"})
	recsutility := seedCollection{Collection: "ai.gftd.apps.water.utility"}
	recsutility.Items = append(recsutility.Items, seedRecord{ID: "thames_water", Data: map[string]any{"id": "thames_water", "name": "Thames Water", "description": "London water utility", "status": "active"}})
	recsutility.Items = append(recsutility.Items, seedRecord{ID: "veolia_paris", Data: map[string]any{"id": "veolia_paris", "name": "Veolia Paris", "description": "Paris water service", "status": "active"}})
	recsutility.Items = append(recsutility.Items, seedRecord{ID: "tokyo_waterworks", Data: map[string]any{"id": "tokyo_waterworks", "name": "東京都水道局", "description": "Tokyo water supply", "status": "active"}})
	recsutility.Items = append(recsutility.Items, seedRecord{ID: "suez_global", Data: map[string]any{"id": "suez_global", "name": "SUEZ", "description": "Global water utility", "status": "active"}})
	recsutility.Items = append(recsutility.Items, seedRecord{ID: "american_water", Data: map[string]any{"id": "american_water", "name": "American Water", "description": "US water utility", "status": "active"}})
	def.Records = append(def.Records, recsutility)
	return def
}

func WebpageGapSeeds() seedDef {
	def := seedDef{Domain: "webpage", Nanoid: "cr4wl3r0", DID: "did:web:webpage.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "page:google_com", DisplayName: "google.com", Description: "Search engine homepage"})
	def.DIDs = append(def.DIDs, seedDID{Path: "page:wikipedia_en", DisplayName: "en.wikipedia.org", Description: "English Wikipedia"})
	def.DIDs = append(def.DIDs, seedDID{Path: "page:github_com", DisplayName: "github.com", Description: "Code hosting platform"})
	def.DIDs = append(def.DIDs, seedDID{Path: "page:amazon_co_jp", DisplayName: "amazon.co.jp", Description: "Japan e-commerce"})
	def.DIDs = append(def.DIDs, seedDID{Path: "page:yahoo_co_jp", DisplayName: "yahoo.co.jp", Description: "Japan portal"})
	recspage := seedCollection{Collection: "ai.gftd.apps.webpage.page"}
	recspage.Items = append(recspage.Items, seedRecord{ID: "google_com", Data: map[string]any{"id": "google_com", "name": "google.com", "description": "Search engine homepage", "status": "active"}})
	recspage.Items = append(recspage.Items, seedRecord{ID: "wikipedia_en", Data: map[string]any{"id": "wikipedia_en", "name": "en.wikipedia.org", "description": "English Wikipedia", "status": "active"}})
	recspage.Items = append(recspage.Items, seedRecord{ID: "github_com", Data: map[string]any{"id": "github_com", "name": "github.com", "description": "Code hosting platform", "status": "active"}})
	recspage.Items = append(recspage.Items, seedRecord{ID: "amazon_co_jp", Data: map[string]any{"id": "amazon_co_jp", "name": "amazon.co.jp", "description": "Japan e-commerce", "status": "active"}})
	recspage.Items = append(recspage.Items, seedRecord{ID: "yahoo_co_jp", Data: map[string]any{"id": "yahoo_co_jp", "name": "yahoo.co.jp", "description": "Japan portal", "status": "active"}})
	def.Records = append(def.Records, recspage)
	return def
}

func ZeimuGapSeeds() seedDef {
	def := seedDef{Domain: "zeimu", Nanoid: "zeimaeb7", DID: "did:web:zeimu.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "return:shotoku_2024", DisplayName: "令和6年所得税確定申告", Description: "2024 income tax return"})
	def.DIDs = append(def.DIDs, seedDID{Path: "return:houjin_2024", DisplayName: "法人税申告2024", Description: "2024 corporate tax return"})
	def.DIDs = append(def.DIDs, seedDID{Path: "return:shouhizei_2024", DisplayName: "消費税申告2024", Description: "2024 consumption tax return"})
	def.DIDs = append(def.DIDs, seedDID{Path: "return:us_1040_2024", DisplayName: "US Form 1040 2024", Description: "US individual tax return"})
	def.DIDs = append(def.DIDs, seedDID{Path: "return:vat_uk_2024", DisplayName: "UK VAT Return 2024", Description: "UK VAT return"})
	recsreturn := seedCollection{Collection: "ai.gftd.apps.zeimu.return"}
	recsreturn.Items = append(recsreturn.Items, seedRecord{ID: "shotoku_2024", Data: map[string]any{"id": "shotoku_2024", "name": "令和6年所得税確定申告", "description": "2024 income tax return", "status": "active"}})
	recsreturn.Items = append(recsreturn.Items, seedRecord{ID: "houjin_2024", Data: map[string]any{"id": "houjin_2024", "name": "法人税申告2024", "description": "2024 corporate tax return", "status": "active"}})
	recsreturn.Items = append(recsreturn.Items, seedRecord{ID: "shouhizei_2024", Data: map[string]any{"id": "shouhizei_2024", "name": "消費税申告2024", "description": "2024 consumption tax return", "status": "active"}})
	recsreturn.Items = append(recsreturn.Items, seedRecord{ID: "us_1040_2024", Data: map[string]any{"id": "us_1040_2024", "name": "US Form 1040 2024", "description": "US individual tax return", "status": "active"}})
	recsreturn.Items = append(recsreturn.Items, seedRecord{ID: "vat_uk_2024", Data: map[string]any{"id": "vat_uk_2024", "name": "UK VAT Return 2024", "description": "UK VAT return", "status": "active"}})
	def.Records = append(def.Records, recsreturn)
	return def
}

// ── 2026-04-17 coverage expansion: chemical analysis + genomics domain ──

func MsSpecGapSeeds() seedDef {
	def := seedDef{Domain: "msSpec", Nanoid: "ms9spec2", DID: "did:web:ms-spec.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "technique:gc_ms", DisplayName: "GC-MS", Description: "Gas chromatography mass spectrometry"})
	def.DIDs = append(def.DIDs, seedDID{Path: "technique:lc_ms", DisplayName: "LC-MS", Description: "Liquid chromatography mass spectrometry"})
	def.DIDs = append(def.DIDs, seedDID{Path: "technique:maldi_tof", DisplayName: "MALDI-TOF", Description: "Matrix-assisted laser desorption/ionization"})
	def.DIDs = append(def.DIDs, seedDID{Path: "technique:esi_qtof", DisplayName: "ESI-QTOF", Description: "Electrospray quadrupole time-of-flight"})
	def.DIDs = append(def.DIDs, seedDID{Path: "technique:icp_ms", DisplayName: "ICP-MS", Description: "Inductively coupled plasma mass spectrometry"})
	recstechnique := seedCollection{Collection: "ai.gftd.apps.msSpec.technique"}
	recstechnique.Items = append(recstechnique.Items, seedRecord{ID: "gc_ms", Data: map[string]any{"id": "gc_ms", "name": "GC-MS", "description": "Gas chromatography mass spectrometry", "status": "active"}})
	recstechnique.Items = append(recstechnique.Items, seedRecord{ID: "lc_ms", Data: map[string]any{"id": "lc_ms", "name": "LC-MS", "description": "Liquid chromatography mass spectrometry", "status": "active"}})
	recstechnique.Items = append(recstechnique.Items, seedRecord{ID: "maldi_tof", Data: map[string]any{"id": "maldi_tof", "name": "MALDI-TOF", "description": "Matrix-assisted laser desorption/ionization", "status": "active"}})
	recstechnique.Items = append(recstechnique.Items, seedRecord{ID: "esi_qtof", Data: map[string]any{"id": "esi_qtof", "name": "ESI-QTOF", "description": "Electrospray quadrupole time-of-flight", "status": "active"}})
	recstechnique.Items = append(recstechnique.Items, seedRecord{ID: "icp_ms", Data: map[string]any{"id": "icp_ms", "name": "ICP-MS", "description": "Inductively coupled plasma mass spectrometry", "status": "active"}})
	def.Records = append(def.Records, recstechnique)
	return def
}

func NmrSpecGapSeeds() seedDef {
	def := seedDef{Domain: "nmrSpec", Nanoid: "nm4rsp3c", DID: "did:web:nmr-spec.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "nucleus:1h", DisplayName: "1H NMR", Description: "Proton nuclear magnetic resonance"})
	def.DIDs = append(def.DIDs, seedDID{Path: "nucleus:13c", DisplayName: "13C NMR", Description: "Carbon-13 nuclear magnetic resonance"})
	def.DIDs = append(def.DIDs, seedDID{Path: "nucleus:31p", DisplayName: "31P NMR", Description: "Phosphorus-31 nuclear magnetic resonance"})
	def.DIDs = append(def.DIDs, seedDID{Path: "experiment:cosy", DisplayName: "COSY", Description: "Correlation spectroscopy (2D)"})
	def.DIDs = append(def.DIDs, seedDID{Path: "experiment:hsqc", DisplayName: "HSQC", Description: "Heteronuclear single quantum coherence"})
	recsnucleus := seedCollection{Collection: "ai.gftd.apps.nmrSpec.nucleus"}
	recsnucleus.Items = append(recsnucleus.Items, seedRecord{ID: "1h", Data: map[string]any{"id": "1h", "name": "1H NMR", "description": "Proton nuclear magnetic resonance", "status": "active"}})
	recsnucleus.Items = append(recsnucleus.Items, seedRecord{ID: "13c", Data: map[string]any{"id": "13c", "name": "13C NMR", "description": "Carbon-13 nuclear magnetic resonance", "status": "active"}})
	recsnucleus.Items = append(recsnucleus.Items, seedRecord{ID: "31p", Data: map[string]any{"id": "31p", "name": "31P NMR", "description": "Phosphorus-31 nuclear magnetic resonance", "status": "active"}})
	def.Records = append(def.Records, recsnucleus)
	recsexperiment := seedCollection{Collection: "ai.gftd.apps.nmrSpec.experiment"}
	recsexperiment.Items = append(recsexperiment.Items, seedRecord{ID: "cosy", Data: map[string]any{"id": "cosy", "name": "COSY", "description": "Correlation spectroscopy (2D)", "status": "active"}})
	recsexperiment.Items = append(recsexperiment.Items, seedRecord{ID: "hsqc", Data: map[string]any{"id": "hsqc", "name": "HSQC", "description": "Heteronuclear single quantum coherence", "status": "active"}})
	def.Records = append(def.Records, recsexperiment)
	return def
}

func ChromatoGapSeeds() seedDef {
	def := seedDef{Domain: "chromato", Nanoid: "chr0m4t0", DID: "did:web:chromato.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "technique:hplc", DisplayName: "HPLC", Description: "High-performance liquid chromatography"})
	def.DIDs = append(def.DIDs, seedDID{Path: "technique:uhplc", DisplayName: "UHPLC", Description: "Ultra-high-performance liquid chromatography"})
	def.DIDs = append(def.DIDs, seedDID{Path: "technique:gc", DisplayName: "GC", Description: "Gas chromatography"})
	def.DIDs = append(def.DIDs, seedDID{Path: "technique:tlc", DisplayName: "TLC", Description: "Thin-layer chromatography"})
	def.DIDs = append(def.DIDs, seedDID{Path: "technique:ion_chrom", DisplayName: "Ion Chromatography", Description: "IC for ionic species"})
	recstechnique := seedCollection{Collection: "ai.gftd.apps.chromato.technique"}
	recstechnique.Items = append(recstechnique.Items, seedRecord{ID: "hplc", Data: map[string]any{"id": "hplc", "name": "HPLC", "description": "High-performance liquid chromatography", "status": "active"}})
	recstechnique.Items = append(recstechnique.Items, seedRecord{ID: "uhplc", Data: map[string]any{"id": "uhplc", "name": "UHPLC", "description": "Ultra-high-performance liquid chromatography", "status": "active"}})
	recstechnique.Items = append(recstechnique.Items, seedRecord{ID: "gc", Data: map[string]any{"id": "gc", "name": "GC", "description": "Gas chromatography", "status": "active"}})
	recstechnique.Items = append(recstechnique.Items, seedRecord{ID: "tlc", Data: map[string]any{"id": "tlc", "name": "TLC", "description": "Thin-layer chromatography", "status": "active"}})
	recstechnique.Items = append(recstechnique.Items, seedRecord{ID: "ion_chrom", Data: map[string]any{"id": "ion_chrom", "name": "Ion Chromatography", "description": "IC for ionic species", "status": "active"}})
	def.Records = append(def.Records, recstechnique)
	return def
}

func XrdXrfGapSeeds() seedDef {
	def := seedDef{Domain: "xrdXrf", Nanoid: "xr5xrf82", DID: "did:web:xrd-xrf.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "technique:powder_xrd", DisplayName: "Powder XRD", Description: "Powder X-ray diffraction"})
	def.DIDs = append(def.DIDs, seedDID{Path: "technique:single_crystal_xrd", DisplayName: "Single Crystal XRD", Description: "Single crystal X-ray diffraction"})
	def.DIDs = append(def.DIDs, seedDID{Path: "technique:ed_xrf", DisplayName: "ED-XRF", Description: "Energy-dispersive X-ray fluorescence"})
	def.DIDs = append(def.DIDs, seedDID{Path: "technique:wd_xrf", DisplayName: "WD-XRF", Description: "Wavelength-dispersive X-ray fluorescence"})
	def.DIDs = append(def.DIDs, seedDID{Path: "phase:quartz", DisplayName: "石英 (Quartz)", Description: "SiO2 alpha-quartz reference phase"})
	recstechnique := seedCollection{Collection: "ai.gftd.apps.xrdXrf.technique"}
	recstechnique.Items = append(recstechnique.Items, seedRecord{ID: "powder_xrd", Data: map[string]any{"id": "powder_xrd", "name": "Powder XRD", "description": "Powder X-ray diffraction", "status": "active"}})
	recstechnique.Items = append(recstechnique.Items, seedRecord{ID: "single_crystal_xrd", Data: map[string]any{"id": "single_crystal_xrd", "name": "Single Crystal XRD", "description": "Single crystal X-ray diffraction", "status": "active"}})
	recstechnique.Items = append(recstechnique.Items, seedRecord{ID: "ed_xrf", Data: map[string]any{"id": "ed_xrf", "name": "ED-XRF", "description": "Energy-dispersive X-ray fluorescence", "status": "active"}})
	recstechnique.Items = append(recstechnique.Items, seedRecord{ID: "wd_xrf", Data: map[string]any{"id": "wd_xrf", "name": "WD-XRF", "description": "Wavelength-dispersive X-ray fluorescence", "status": "active"}})
	def.Records = append(def.Records, recstechnique)
	recsphase := seedCollection{Collection: "ai.gftd.apps.xrdXrf.phase"}
	recsphase.Items = append(recsphase.Items, seedRecord{ID: "quartz", Data: map[string]any{"id": "quartz", "name": "石英 (Quartz)", "description": "SiO2 alpha-quartz reference phase", "status": "active"}})
	def.Records = append(def.Records, recsphase)
	return def
}

func IrUvSpecGapSeeds() seedDef {
	def := seedDef{Domain: "irUvSpec", Nanoid: "irv8sp3c", DID: "did:web:ir-uv-spec.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "technique:ftir", DisplayName: "FTIR", Description: "Fourier-transform infrared"})
	def.DIDs = append(def.DIDs, seedDID{Path: "technique:atr", DisplayName: "ATR-IR", Description: "Attenuated total reflectance IR"})
	def.DIDs = append(def.DIDs, seedDID{Path: "technique:uv_vis", DisplayName: "UV-Vis", Description: "Ultraviolet-visible spectroscopy"})
	def.DIDs = append(def.DIDs, seedDID{Path: "band:carbonyl", DisplayName: "Carbonyl C=O", Description: "1650-1800 cm-1 stretch"})
	def.DIDs = append(def.DIDs, seedDID{Path: "band:hydroxyl", DisplayName: "Hydroxyl O-H", Description: "3200-3600 cm-1 stretch"})
	recstechnique := seedCollection{Collection: "ai.gftd.apps.irUvSpec.technique"}
	recstechnique.Items = append(recstechnique.Items, seedRecord{ID: "ftir", Data: map[string]any{"id": "ftir", "name": "FTIR", "description": "Fourier-transform infrared", "status": "active"}})
	recstechnique.Items = append(recstechnique.Items, seedRecord{ID: "atr", Data: map[string]any{"id": "atr", "name": "ATR-IR", "description": "Attenuated total reflectance IR", "status": "active"}})
	recstechnique.Items = append(recstechnique.Items, seedRecord{ID: "uv_vis", Data: map[string]any{"id": "uv_vis", "name": "UV-Vis", "description": "Ultraviolet-visible spectroscopy", "status": "active"}})
	def.Records = append(def.Records, recstechnique)
	recsband := seedCollection{Collection: "ai.gftd.apps.irUvSpec.band"}
	recsband.Items = append(recsband.Items, seedRecord{ID: "carbonyl", Data: map[string]any{"id": "carbonyl", "name": "Carbonyl C=O", "description": "1650-1800 cm-1 stretch", "status": "active"}})
	recsband.Items = append(recsband.Items, seedRecord{ID: "hydroxyl", Data: map[string]any{"id": "hydroxyl", "name": "Hydroxyl O-H", "description": "3200-3600 cm-1 stretch", "status": "active"}})
	def.Records = append(def.Records, recsband)
	return def
}

func GenomeRefGapSeeds() seedDef {
	def := seedDef{Domain: "genomeRef", Nanoid: "gn0m3r3f", DID: "did:web:genome-ref.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "assembly:grch38", DisplayName: "GRCh38", Description: "Human reference genome (2013)"})
	def.DIDs = append(def.DIDs, seedDID{Path: "assembly:t2t_chm13", DisplayName: "T2T-CHM13", Description: "Telomere-to-telomere human (2022)"})
	def.DIDs = append(def.DIDs, seedDID{Path: "gene:brca1", DisplayName: "BRCA1", Description: "Breast cancer 1, chr17"})
	def.DIDs = append(def.DIDs, seedDID{Path: "gene:tp53", DisplayName: "TP53", Description: "Tumor protein p53, chr17"})
	def.DIDs = append(def.DIDs, seedDID{Path: "gene:egfr", DisplayName: "EGFR", Description: "Epidermal growth factor receptor, chr7"})
	recsassembly := seedCollection{Collection: "ai.gftd.apps.genomeRef.assembly"}
	recsassembly.Items = append(recsassembly.Items, seedRecord{ID: "grch38", Data: map[string]any{"id": "grch38", "name": "GRCh38", "description": "Human reference genome (2013)", "status": "active"}})
	recsassembly.Items = append(recsassembly.Items, seedRecord{ID: "t2t_chm13", Data: map[string]any{"id": "t2t_chm13", "name": "T2T-CHM13", "description": "Telomere-to-telomere human (2022)", "status": "active"}})
	def.Records = append(def.Records, recsassembly)
	recsgene := seedCollection{Collection: "ai.gftd.apps.genomeRef.gene"}
	recsgene.Items = append(recsgene.Items, seedRecord{ID: "brca1", Data: map[string]any{"id": "brca1", "name": "BRCA1", "description": "Breast cancer 1, chr17", "status": "active"}})
	recsgene.Items = append(recsgene.Items, seedRecord{ID: "tp53", Data: map[string]any{"id": "tp53", "name": "TP53", "description": "Tumor protein p53, chr17", "status": "active"}})
	recsgene.Items = append(recsgene.Items, seedRecord{ID: "egfr", Data: map[string]any{"id": "egfr", "name": "EGFR", "description": "Epidermal growth factor receptor, chr7", "status": "active"}})
	def.Records = append(def.Records, recsgene)
	return def
}

func VariantClinGapSeeds() seedDef {
	def := seedDef{Domain: "variantClin", Nanoid: "v4r14ntc", DID: "did:web:variant-clin.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "variant:brca1_185delag", DisplayName: "BRCA1 185delAG", Description: "Ashkenazi founder pathogenic variant"})
	def.DIDs = append(def.DIDs, seedDID{Path: "variant:braf_v600e", DisplayName: "BRAF V600E", Description: "Melanoma/colorectal oncogenic mutation"})
	def.DIDs = append(def.DIDs, seedDID{Path: "variant:cftr_f508del", DisplayName: "CFTR F508del", Description: "Cystic fibrosis pathogenic variant"})
	def.DIDs = append(def.DIDs, seedDID{Path: "variant:hbb_glu6val", DisplayName: "HBB Glu6Val", Description: "Sickle cell anemia variant"})
	def.DIDs = append(def.DIDs, seedDID{Path: "variant:apoe4", DisplayName: "APOE ε4", Description: "Alzheimer's risk allele"})
	recsvariant := seedCollection{Collection: "ai.gftd.apps.variantClin.variant"}
	recsvariant.Items = append(recsvariant.Items, seedRecord{ID: "brca1_185delag", Data: map[string]any{"id": "brca1_185delag", "name": "BRCA1 185delAG", "description": "Ashkenazi founder pathogenic variant", "status": "active"}})
	recsvariant.Items = append(recsvariant.Items, seedRecord{ID: "braf_v600e", Data: map[string]any{"id": "braf_v600e", "name": "BRAF V600E", "description": "Melanoma/colorectal oncogenic mutation", "status": "active"}})
	recsvariant.Items = append(recsvariant.Items, seedRecord{ID: "cftr_f508del", Data: map[string]any{"id": "cftr_f508del", "name": "CFTR F508del", "description": "Cystic fibrosis pathogenic variant", "status": "active"}})
	recsvariant.Items = append(recsvariant.Items, seedRecord{ID: "hbb_glu6val", Data: map[string]any{"id": "hbb_glu6val", "name": "HBB Glu6Val", "description": "Sickle cell anemia variant", "status": "active"}})
	recsvariant.Items = append(recsvariant.Items, seedRecord{ID: "apoe4", Data: map[string]any{"id": "apoe4", "name": "APOE ε4", "description": "Alzheimer's risk allele", "status": "active"}})
	def.Records = append(def.Records, recsvariant)
	return def
}

func GeneOntologyGapSeeds() seedDef {
	def := seedDef{Domain: "geneOntology", Nanoid: "gn0nt0l7", DID: "did:web:gene-ontology.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "go:0006915", DisplayName: "apoptotic process", Description: "GO:0006915 biological process"})
	def.DIDs = append(def.DIDs, seedDID{Path: "go:0008152", DisplayName: "metabolic process", Description: "GO:0008152 biological process"})
	def.DIDs = append(def.DIDs, seedDID{Path: "kegg:hsa04110", DisplayName: "Cell cycle", Description: "KEGG pathway hsa04110"})
	def.DIDs = append(def.DIDs, seedDID{Path: "reactome:r_hsa_69278", DisplayName: "Cell Cycle (Mitotic)", Description: "Reactome R-HSA-69278"})
	def.DIDs = append(def.DIDs, seedDID{Path: "msigdb:hallmark_p53", DisplayName: "Hallmark P53 Pathway", Description: "MSigDB hallmark gene set"})
	recsgo := seedCollection{Collection: "ai.gftd.apps.geneOntology.go"}
	recsgo.Items = append(recsgo.Items, seedRecord{ID: "0006915", Data: map[string]any{"id": "0006915", "name": "apoptotic process", "description": "GO:0006915 biological process", "status": "active"}})
	recsgo.Items = append(recsgo.Items, seedRecord{ID: "0008152", Data: map[string]any{"id": "0008152", "name": "metabolic process", "description": "GO:0008152 biological process", "status": "active"}})
	def.Records = append(def.Records, recsgo)
	recspathway := seedCollection{Collection: "ai.gftd.apps.geneOntology.pathway"}
	recspathway.Items = append(recspathway.Items, seedRecord{ID: "hsa04110", Data: map[string]any{"id": "hsa04110", "name": "Cell cycle", "description": "KEGG pathway hsa04110", "status": "active"}})
	recspathway.Items = append(recspathway.Items, seedRecord{ID: "r_hsa_69278", Data: map[string]any{"id": "r_hsa_69278", "name": "Cell Cycle (Mitotic)", "description": "Reactome R-HSA-69278", "status": "active"}})
	recspathway.Items = append(recspathway.Items, seedRecord{ID: "hallmark_p53", Data: map[string]any{"id": "hallmark_p53", "name": "Hallmark P53 Pathway", "description": "MSigDB hallmark gene set", "status": "active"}})
	def.Records = append(def.Records, recspathway)
	return def
}

func ProteomeGapSeeds() seedDef {
	def := seedDef{Domain: "proteome", Nanoid: "pr0t30m3", DID: "did:web:proteome.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "uniprot:p04637", DisplayName: "TP53 (P04637)", Description: "Cellular tumor antigen p53"})
	def.DIDs = append(def.DIDs, seedDID{Path: "uniprot:p38398", DisplayName: "BRCA1 (P38398)", Description: "Breast cancer type 1 susceptibility protein"})
	def.DIDs = append(def.DIDs, seedDID{Path: "uniprot:p00533", DisplayName: "EGFR (P00533)", Description: "Epidermal growth factor receptor"})
	def.DIDs = append(def.DIDs, seedDID{Path: "pdb:1tup", DisplayName: "PDB 1TUP", Description: "P53 tumor suppressor-DNA complex"})
	def.DIDs = append(def.DIDs, seedDID{Path: "pfam:pf00870", DisplayName: "Pfam P53", Description: "P53 DNA-binding domain family"})
	recsuniprot := seedCollection{Collection: "ai.gftd.apps.proteome.uniprot"}
	recsuniprot.Items = append(recsuniprot.Items, seedRecord{ID: "p04637", Data: map[string]any{"id": "p04637", "name": "TP53 (P04637)", "description": "Cellular tumor antigen p53", "status": "active"}})
	recsuniprot.Items = append(recsuniprot.Items, seedRecord{ID: "p38398", Data: map[string]any{"id": "p38398", "name": "BRCA1 (P38398)", "description": "Breast cancer type 1 susceptibility protein", "status": "active"}})
	recsuniprot.Items = append(recsuniprot.Items, seedRecord{ID: "p00533", Data: map[string]any{"id": "p00533", "name": "EGFR (P00533)", "description": "Epidermal growth factor receptor", "status": "active"}})
	def.Records = append(def.Records, recsuniprot)
	recsstructure := seedCollection{Collection: "ai.gftd.apps.proteome.structure"}
	recsstructure.Items = append(recsstructure.Items, seedRecord{ID: "1tup", Data: map[string]any{"id": "1tup", "name": "PDB 1TUP", "description": "P53 tumor suppressor-DNA complex", "status": "active"}})
	def.Records = append(def.Records, recsstructure)
	recsdomain := seedCollection{Collection: "ai.gftd.apps.proteome.domain"}
	recsdomain.Items = append(recsdomain.Items, seedRecord{ID: "pf00870", Data: map[string]any{"id": "pf00870", "name": "Pfam P53", "description": "P53 DNA-binding domain family", "status": "active"}})
	def.Records = append(def.Records, recsdomain)
	return def
}

func KinshipGapSeeds() seedDef {
	def := seedDef{Domain: "kinship", Nanoid: "k1nsh1p8", DID: "did:web:kinship.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "method:king", DisplayName: "KING", Description: "Kinship-based INference for Gwas"})
	def.DIDs = append(def.DIDs, seedDID{Path: "method:plink_ibd", DisplayName: "PLINK IBD", Description: "Identity-by-descent via PLINK"})
	def.DIDs = append(def.DIDs, seedDID{Path: "method:ibdseq", DisplayName: "IBDSeq", Description: "IBD detection in sequence data"})
	def.DIDs = append(def.DIDs, seedDID{Path: "relation:parent_child", DisplayName: "Parent-child", Description: "Expected kinship 0.25"})
	def.DIDs = append(def.DIDs, seedDID{Path: "relation:second_degree", DisplayName: "2nd degree", Description: "Grandparent/uncle/half-sibling (expected 0.125)"})
	recsmethod := seedCollection{Collection: "ai.gftd.apps.kinship.method"}
	recsmethod.Items = append(recsmethod.Items, seedRecord{ID: "king", Data: map[string]any{"id": "king", "name": "KING", "description": "Kinship-based INference for Gwas", "status": "active"}})
	recsmethod.Items = append(recsmethod.Items, seedRecord{ID: "plink_ibd", Data: map[string]any{"id": "plink_ibd", "name": "PLINK IBD", "description": "Identity-by-descent via PLINK", "status": "active"}})
	recsmethod.Items = append(recsmethod.Items, seedRecord{ID: "ibdseq", Data: map[string]any{"id": "ibdseq", "name": "IBDSeq", "description": "IBD detection in sequence data", "status": "active"}})
	def.Records = append(def.Records, recsmethod)
	recsrelation := seedCollection{Collection: "ai.gftd.apps.kinship.relation"}
	recsrelation.Items = append(recsrelation.Items, seedRecord{ID: "parent_child", Data: map[string]any{"id": "parent_child", "name": "Parent-child", "description": "Expected kinship 0.25", "status": "active"}})
	recsrelation.Items = append(recsrelation.Items, seedRecord{ID: "second_degree", Data: map[string]any{"id": "second_degree", "name": "2nd degree", "description": "Grandparent/uncle/half-sibling (expected 0.125)", "status": "active"}})
	def.Records = append(def.Records, recsrelation)
	return def
}

func PharmacoGxGapSeeds() seedDef {
	def := seedDef{Domain: "pharmacoGx", Nanoid: "phrm4cgx", DID: "did:web:pharmaco-gx.etzhayyim.com"}
	def.DIDs = append(def.DIDs, seedDID{Path: "allele:cyp2d6_star4", DisplayName: "CYP2D6 *4", Description: "Null allele, poor metabolizer"})
	def.DIDs = append(def.DIDs, seedDID{Path: "allele:cyp2c19_star2", DisplayName: "CYP2C19 *2", Description: "Loss-of-function, clopidogrel response"})
	def.DIDs = append(def.DIDs, seedDID{Path: "allele:hla_b_5701", DisplayName: "HLA-B*57:01", Description: "Abacavir hypersensitivity risk"})
	def.DIDs = append(def.DIDs, seedDID{Path: "allele:tpmt_star3a", DisplayName: "TPMT *3A", Description: "Thiopurine toxicity risk"})
	def.DIDs = append(def.DIDs, seedDID{Path: "allele:dpyd_star2a", DisplayName: "DPYD *2A", Description: "5-FU toxicity risk"})
	recsallele := seedCollection{Collection: "ai.gftd.apps.pharmacoGx.allele"}
	recsallele.Items = append(recsallele.Items, seedRecord{ID: "cyp2d6_star4", Data: map[string]any{"id": "cyp2d6_star4", "name": "CYP2D6 *4", "description": "Null allele, poor metabolizer", "status": "active"}})
	recsallele.Items = append(recsallele.Items, seedRecord{ID: "cyp2c19_star2", Data: map[string]any{"id": "cyp2c19_star2", "name": "CYP2C19 *2", "description": "Loss-of-function, clopidogrel response", "status": "active"}})
	recsallele.Items = append(recsallele.Items, seedRecord{ID: "hla_b_5701", Data: map[string]any{"id": "hla_b_5701", "name": "HLA-B*57:01", "description": "Abacavir hypersensitivity risk", "status": "active"}})
	recsallele.Items = append(recsallele.Items, seedRecord{ID: "tpmt_star3a", Data: map[string]any{"id": "tpmt_star3a", "name": "TPMT *3A", "description": "Thiopurine toxicity risk", "status": "active"}})
	recsallele.Items = append(recsallele.Items, seedRecord{ID: "dpyd_star2a", Data: map[string]any{"id": "dpyd_star2a", "name": "DPYD *2A", "description": "5-FU toxicity risk", "status": "active"}})
	def.Records = append(def.Records, recsallele)
	return def
}

// gapSeedRegistry returns all gap seed definitions for coverage filling.
func gapSeedRegistry() []seedDef {
	return []seedDef{
		AircraftGapSeeds(),
		AnimaGapSeeds(),
		ApiGapSeeds(),
		ApparelGapSeeds(),
		ArtGapSeeds(),
		BankGapSeeds(),
		BankruptcyGapSeeds(),
		BimGapSeeds(),
		BouekiGapSeeds(),
		BusGapSeeds(),
		CarbonGapSeeds(),
		CasGapSeeds(),
		CellerGapSeeds(),
		CharacterGapSeeds(),
		ChizaiGapSeeds(),
		ChotatsuGapSeeds(),
		ChuushajouGapSeeds(),
		CicdGapSeeds(),
		CloudGapSeeds(),
		CommunitiesGapSeeds(),
		ContainerGapSeeds(),
		CreditcardGapSeeds(),
		CtMonitorGapSeeds(),
		DbGapSeeds(),
		DcGapSeeds(),
		DemaeGapSeeds(),
		DenkiGapSeeds(),
		DenshiBuhinGapSeeds(),
		DerivativeGapSeeds(),
		DevGapSeeds(),
		DnsGapSeeds(),
		DojoGapSeeds(),
		DouroGapSeeds(),
		DroneGapSeeds(),
		EnergyGapSeeds(),
		EpisodeGapSeeds(),
		EquipmentGapSeeds(),
		EthicsGapSeeds(),
		EvGapSeeds(),
		EventGapSeeds(),
		FactoryGapSeeds(),
		FarmGapSeeds(),
		FestivalGapSeeds(),
		FleamarketGapSeeds(),
		FoodGapSeeds(),
		FudosanGapSeeds(),
		GakurekiGapSeeds(),
		GasGapSeeds(),
		GasStationGapSeeds(),
		GenomeGapSeeds(),
		GovGapSeeds(),
		GtinGapSeeds(),
		HaikibutsuGapSeeds(),
		HakubutsukanGapSeeds(),
		HanzaiGapSeeds(),
		HinshuGapSeeds(),
		HoureiGapSeeds(),
		IndustryStandardGapSeeds(),
		InsuranceGapSeeds(),
		InvoiceGapSeeds(),
		IotGapSeeds(),
		IpaddressGapSeeds(),
		IryoGapSeeds(),
		IsbnGapSeeds(),
		IsinGapSeeds(),
		IssnGapSeeds(),
		JidoshaBuhinGapSeeds(),
		JikoGapSeeds(),
		JinushiGapSeeds(),
		JouchoGapSeeds(),
		K8sGapSeeds(),
		KachikuGapSeeds(),
		KaguGapSeeds(),
		KaigoGapSeeds(),
		KeiyakuGapSeeds(),
		KensetsuGapSeeds(),
		KenzaiGapSeeds(),
		KessaiGapSeeds(),
		KikaiBuhinGapSeeds(),
		KiseiGapSeeds(),
		KosekiGapSeeds(),
		KoutsuuGapSeeds(),
		KurumaGapSeeds(),
		KyokaGapSeeds(),
		LegalEntityGapSeeds(),
		LifeEventGapSeeds(),
		LoanGapSeeds(),
		MacGapSeeds(),
		MapsGapSeeds(),
		MediaAnimeGapSeeds(),
		MediaGamersGapSeeds(),
		MenkyoGapSeeds(),
		MineGapSeeds(),
		MinpakuGapSeeds(),
		NaturalPersonGapSeeds(),
		NdcGapSeeds(),
		NijisousakuGapSeeds(),
		NimotsuGapSeeds(),
		NirinGapSeeds(),
		NougyouGapSeeds(),
		NpoGapSeeds(),
		OmatsuriGapSeeds(),
		OtoshimonoGapSeeds(),
		PassportGapSeeds(),
		PatentGapSeeds(),
		PharmaGapSeeds(),
		PhonenumberGapSeeds(),
		PhotosGapSeeds(),
		PortGapSeeds(),
		PropertyGapSeeds(),
		RailwayGapSeeds(),
		ReceiptGapSeeds(),
		RecycleGapSeeds(),
		RepoGapSeeds(),
		RoadGapSeeds(),
		RonbunGapSeeds(),
		SaigaiGapSeeds(),
		SanctionsGapSeeds(),
		SatelliteGapSeeds(),
		SbomGapSeeds(),
		SecuritiesGapSeeds(),
		SeibiGapSeeds(),
		SeiyakuGapSeeds(),
		SeizoGapSeeds(),
		SenkyoGapSeeds(),
		SerialGapSeeds(),
		SetaiGapSeeds(),
		ShikakuGapSeeds(),
		ShinsaGapSeeds(),
		ShinshiGapSeeds(),
		ShisanGapSeeds(),
		ShizenGapSeeds(),
		ShohinGapSeeds(),
		ShokuhinAnzenGapSeeds(),
		SnsGapSeeds(),
		SoftwareGapSeeds(),
		SoudenGapSeeds(),
		SozaiGapSeeds(),
		SportsGapSeeds(),
		SupplyChainGapSeeds(),
		SyosetsuGapSeeds(),
		TaxiGapSeeds(),
		TentaiGapSeeds(),
		TorihikiGapSeeds(),
		ToshokanGapSeeds(),
		TraditionGapSeeds(),
		TrustGapSeeds(),
		TsukanGapSeeds(),
		UchuGapSeeds(),
		UnkouGapSeeds(),
		UnspscGapSeeds(),
		VehicleGapSeeds(),
		VesselGapSeeds(),
		VisaGapSeeds(),
		WarehouseGapSeeds(),
		WaterGapSeeds(),
		WebpageGapSeeds(),
		ZeimuGapSeeds(),
		// 2026-04-17 coverage expansion: chemical analysis + genomics
		MsSpecGapSeeds(),
		NmrSpecGapSeeds(),
		ChromatoGapSeeds(),
		XrdXrfGapSeeds(),
		IrUvSpecGapSeeds(),
		GenomeRefGapSeeds(),
		VariantClinGapSeeds(),
		GeneOntologyGapSeeds(),
		ProteomeGapSeeds(),
		KinshipGapSeeds(),
		PharmacoGxGapSeeds(),
	}
}
