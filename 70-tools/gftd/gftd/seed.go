// seed.go — gftd seed: DID registration + domain record seeding via PDS XRPC.
//
// Writes records via com.atproto.repo.applyWrites and registers DIDs via
// ai.gftd.kagami.sql Sql MERGE. This is the authoritative path for
// getting COLLECTED > 0 in gftd coverage.
package main

import (
	"bytes"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"strings"
	"time"
)

// ── Seed data types ──

type seedDID struct {
	Path        string // e.g. "track:kawaguchi"
	DisplayName string
	Description string
}

type seedRecord struct {
	ID   string
	Data map[string]any
}

type seedCollection struct {
	Collection string
	Items      []seedRecord
}

type seedDef struct {
	Domain  string // e.g. "autorace"
	Nanoid  string
	DID     string // e.g. "did:web:autorace.etzhayyim.com"
	DIDs    []seedDID
	Records []seedCollection
}

// setWriteAuthHeaders applies standard auth headers and then optionally
// overrides Authorization with a scoped service token for write endpoints.
func setWriteAuthHeaders(req *http.Request, writeToken string) {
	setAuthHeaders(req)
	if t := strings.TrimSpace(writeToken); t != "" {
		req.Header.Set("Authorization", "Bearer "+t)
	}
}

func logSeedDIDWrite(w map[string]any) {
	v, ok := w["value"].(map[string]any)
	if !ok || v == nil {
		return
	}
	id := strings.TrimSpace(toStr(v["id"]))
	name := strings.TrimSpace(toStr(v["display_name"]))
	if id == "" {
		return
	}
	if name == "" {
		name = strings.TrimSpace(toStr(v["displayName"]))
	}
	if name == "" {
		name = "-"
	}
	fmt.Printf("  DID: %s (%s)\n", id, name)
}

// ── Seed registry ──

func buildSeedRegistry() []seedDef {
	base := []seedDef{
		autoraceSeeds(),
		keirinSeeds(),
		kyoteiSeeds(),
		hanreiSeeds(),
		handotaiSeeds(),
		keibaSeeds(),
		fundSeeds(),
		sovereignSeeds(),
		iscoSeeds(),
		isicSeeds(),
		treatySeeds(),
		blockchainSeeds(),
		religiousSeeds(),
		customarySeeds(),
		communityAuthoritySeeds(),
		familyAuthoritySeeds(),
		culturalAuthoritySeeds(),
		professionalAuthoritySeeds(),
		academicAuthoritySeeds(),
		industryAuthoritySeeds(),
		suidoSeeds(),
		cpcSeeds(),
		commoditiesSeeds(),
		cofogSeeds(),
		govSeeds(),
		telecomSeeds(),
		society6Seeds(),
		casinoSeeds(),
		pachinkoSeeds(),
		i18nSeeds(),
		shinsaSeeds(),
	}
	return append(base, gapSeedRegistry()...)
}

func autoraceSeeds() seedDef {
	tracks := []struct {
		id, name, nameJa, pref string
		length                 int
	}{
		{"kawaguchi", "Kawaguchi", "川口", "Saitama", 500},
		{"isesaki", "Isesaki", "伊勢崎", "Gunma", 500},
		{"hamamatsu", "Hamamatsu", "浜松", "Shizuoka", 500},
		{"iizuka", "Iizuka", "飯塚", "Fukuoka", 500},
		{"sanyo", "Sanyo", "山陽", "Yamaguchi", 500},
	}
	racers := []struct {
		id, name, rank, branch string
		winRate, top2Rate      float64
	}{
		{"r001", "青山周平", "S", "伊勢崎", 38.5, 52.3},
		{"r002", "鈴木圭一郎", "S", "浜松", 36.2, 50.1},
		{"r003", "荒尾聡", "S", "飯塚", 33.8, 47.5},
		{"r004", "永井大介", "S", "川口", 31.5, 45.2},
		{"r005", "佐藤摩弥", "A", "川口", 28.3, 42.1},
		{"r006", "高橋貢", "S", "伊勢崎", 35.1, 49.8},
		{"r007", "中村雅人", "S", "川口", 30.2, 44.5},
		{"r008", "森且行", "A", "川口", 22.5, 35.8},
		{"r009", "篠原睦", "S", "飯塚", 27.1, 40.3},
		{"r010", "早川清太郎", "S", "伊勢崎", 29.8, 43.6},
	}

	def := seedDef{
		Domain: "autorace", Nanoid: "zcv937fk", DID: "did:web:autorace.etzhayyim.com",
	}
	// Track DIDs + records
	trackRecs := seedCollection{Collection: "ai.gftd.apps.autorace.race_track"}
	for _, t := range tracks {
		def.DIDs = append(def.DIDs, seedDID{Path: "track:" + t.id, DisplayName: t.nameJa, Description: t.name + " Autorace Track"})
		trackRecs.Items = append(trackRecs.Items, seedRecord{ID: t.id, Data: map[string]any{
			"id": t.id, "name": t.name, "name_ja": t.nameJa, "prefecture": t.pref,
			"track_length_m": t.length, "status": "active",
		}})
	}
	// Racer DIDs + records
	racerRecs := seedCollection{Collection: "ai.gftd.apps.autorace.race_result"}
	for _, r := range racers {
		def.DIDs = append(def.DIDs, seedDID{Path: "racer:" + r.id, DisplayName: r.name, Description: r.rank + "級 " + r.branch})
		racerRecs.Items = append(racerRecs.Items, seedRecord{ID: r.id, Data: map[string]any{
			"id": r.id, "name": r.name, "rank": r.rank, "branch": r.branch,
			"win_rate": r.winRate, "top2_rate": r.top2Rate,
		}})
	}
	// Analyst DID
	def.DIDs = append(def.DIDs, seedDID{Path: "analyst:prediction", DisplayName: "AI予想", Description: "Autorace AI Prediction"})
	def.Records = append(def.Records, trackRecs, racerRecs)
	return def
}

func keirinSeeds() seedDef {
	velodromes := []struct {
		id, name, nameEn, pref string
		bankLen                int
	}{
		{"hakodate", "函館", "Hakodate", "北海道", 400}, {"aomori", "青森", "Aomori", "青森", 400},
		{"iwaki_taira", "いわき平", "Iwaki-Taira", "福島", 400}, {"maebashi", "前橋", "Maebashi", "群馬", 335},
		{"tachikawa", "立川", "Tachikawa", "東京", 400}, {"matsudo", "松戸", "Matsudo", "千葉", 333},
		{"chiba", "千葉", "Chiba", "千葉", 335}, {"kawasaki", "川崎", "Kawasaki", "神奈川", 400},
		{"hiratsuka", "平塚", "Hiratsuka", "神奈川", 400}, {"odawara", "小田原", "Odawara", "神奈川", 333},
		{"ito", "伊東", "Ito", "静岡", 333}, {"shizuoka", "静岡", "Shizuoka", "静岡", 400},
		{"nagoya", "名古屋", "Nagoya", "愛知", 400}, {"gifu", "岐阜", "Gifu", "岐阜", 400},
		{"toyohashi", "豊橋", "Toyohashi", "愛知", 400}, {"yokkaichi", "四日市", "Yokkaichi", "三重", 400},
		{"tsu", "津", "Tsu", "三重", 400}, {"fukui", "福井", "Fukui", "福井", 400},
		{"toyama", "富山", "Toyama", "富山", 333}, {"matsumoto", "松本", "Matsumoto", "長野", 333},
		{"nara", "奈良", "Nara", "奈良", 333}, {"wakayama", "和歌山", "Wakayama", "和歌山", 400},
		{"kishiwada", "岸和田", "Kishiwada", "大阪", 400}, {"tamano", "玉野", "Tamano", "岡山", 400},
		{"hiroshima", "広島", "Hiroshima", "広島", 400}, {"bosoh", "防府", "Hofu", "山口", 333},
		{"takamatsu", "高松", "Takamatsu", "香川", 400}, {"matsuyama", "松山", "Matsuyama", "愛媛", 400},
		{"kochi", "高知", "Kochi", "高知", 333}, {"kokura", "小倉", "Kokura", "福岡", 400},
		{"kurume", "久留米", "Kurume", "福岡", 400}, {"takeo", "武雄", "Takeo", "佐賀", 400},
		{"sasebo", "佐世保", "Sasebo", "長崎", 400}, {"beppu", "別府", "Beppu", "大分", 400},
		{"kumamoto", "熊本", "Kumamoto", "熊本", 400}, {"omuta", "大牟田", "Omuta", "福岡", 400},
		{"miyazaki", "宮崎", "Miyazaki", "宮崎", 400}, {"keio_tama", "京王閣", "Keio-kaku", "東京", 400},
		{"omiya", "大宮", "Omiya", "埼玉", 500}, {"nishigonoi", "西武園", "Seibu-en", "埼玉", 400},
		{"utsunomiya", "宇都宮", "Utsunomiya", "栃木", 400}, {"toride", "取手", "Toride", "茨城", 400},
		{"mito", "水戸", "Mito", "茨城", 400},
	}
	def := seedDef{Domain: "keirin", Nanoid: "zub804qz", DID: "did:web:keirin.etzhayyim.com"}
	recs := seedCollection{Collection: "ai.gftd.apps.keirin.race_track"}
	for _, v := range velodromes {
		def.DIDs = append(def.DIDs, seedDID{Path: "velodrome:" + v.id, DisplayName: v.name + "競輪場", Description: v.nameEn + " Velodrome — " + v.pref})
		recs.Items = append(recs.Items, seedRecord{ID: v.id, Data: map[string]any{
			"id": v.id, "name": v.name, "name_en": v.nameEn, "prefecture": v.pref,
			"bank_length": v.bankLen, "status": "active",
		}})
	}
	def.Records = append(def.Records, recs)
	return def
}

func kyoteiSeeds() seedDef {
	venues := []struct{ id, name, nameEn, pref, water string }{
		{"kiryu", "桐生", "Kiryu", "群馬", "freshwater"}, {"toda", "戸田", "Toda", "埼玉", "freshwater"},
		{"edogawa", "江戸川", "Edogawa", "東京", "brackish"}, {"heiwajima", "平和島", "Heiwajima", "東京", "seawater"},
		{"tamagawa", "多摩川", "Tamagawa", "東京", "freshwater"}, {"hamanako", "浜名湖", "Hamanako", "静岡", "brackish"},
		{"gamagori", "蒲郡", "Gamagori", "愛知", "seawater"}, {"tokoname", "常滑", "Tokoname", "愛知", "seawater"},
		{"tsu", "津", "Tsu", "三重", "seawater"}, {"mikuni", "三国", "Mikuni", "福井", "freshwater"},
		{"biwako", "びわこ", "Biwako", "滋賀", "freshwater"}, {"suminoe", "住之江", "Suminoe", "大阪", "freshwater"},
		{"amagasaki", "尼崎", "Amagasaki", "兵庫", "seawater"}, {"naruto", "鳴門", "Naruto", "徳島", "seawater"},
		{"marugame", "丸亀", "Marugame", "香川", "seawater"}, {"kojima", "児島", "Kojima", "岡山", "seawater"},
		{"miyajima", "宮島", "Miyajima", "広島", "seawater"}, {"tokuyama", "徳山", "Tokuyama", "山口", "seawater"},
		{"shimonoseki", "下関", "Shimonoseki", "山口", "seawater"}, {"wakamatsu", "若松", "Wakamatsu", "福岡", "seawater"},
		{"ashiya", "芦屋", "Ashiya", "福岡", "freshwater"}, {"fukuoka", "福岡", "Fukuoka", "福岡", "seawater"},
		{"karatsu", "唐津", "Karatsu", "佐賀", "seawater"}, {"omura", "大村", "Omura", "長崎", "seawater"},
	}
	def := seedDef{Domain: "kyotei", Nanoid: "qv8yed1k", DID: "did:web:kyotei.etzhayyim.com"}
	recs := seedCollection{Collection: "ai.gftd.apps.kyotei.race_track"}
	for _, v := range venues {
		def.DIDs = append(def.DIDs, seedDID{Path: "venue:" + v.id, DisplayName: v.name + "競艇場", Description: v.nameEn + " Boat Race — " + v.pref + " (" + v.water + ")"})
		recs.Items = append(recs.Items, seedRecord{ID: v.id, Data: map[string]any{
			"id": v.id, "name": v.name, "name_en": v.nameEn, "prefecture": v.pref,
			"water_type": v.water, "status": "active",
		}})
	}
	def.Records = append(def.Records, recs)
	return def
}

func hanreiSeeds() seedDef {
	def := seedDef{Domain: "hanrei", Nanoid: "h4nr31jp", DID: "did:web:hanrei.etzhayyim.com"}
	// JP court DIDs
	courts := []struct{ id, name, desc string }{
		{"supreme", "最高裁判所", "Supreme Court of Japan"},
		{"ip_high", "知的財産高等裁判所", "Intellectual Property High Court"},
		{"high", "高等裁判所", "High Court"},
		{"district", "地方裁判所", "District Court"},
		{"family", "家庭裁判所", "Family Court"},
		{"summary_court", "簡易裁判所", "Summary Court"},
	}
	for _, c := range courts {
		def.DIDs = append(def.DIDs, seedDID{Path: "court:" + c.id, DisplayName: c.name, Description: c.desc})
	}
	// JP source DIDs
	def.DIDs = append(def.DIDs,
		seedDID{Path: "source:kanpo", DisplayName: "官報", Description: "Official Gazette of Japan"},
		seedDID{Path: "source:egov", DisplayName: "e-Gov法令検索", Description: "e-Gov Legislation Search"},
	)
	// Landmark cases
	cases := seedCollection{Collection: "ai.gftd.apps.hanrei.court_case"}
	landmarks := []struct{ id, title, court, date string }{
		{"sunagawa", "砂川事件", "supreme", "1959-12-16"},
		{"makuhari", "マクリーン事件", "supreme", "1978-10-04"},
		{"yosano", "与謝野晶子著作権事件", "ip_high", "2005-03-24"},
		{"hatoyama", "一票の格差訴訟", "supreme", "2013-11-20"},
		{"aum", "オウム真理教事件", "supreme", "2011-11-21"},
	}
	for _, l := range landmarks {
		cases.Items = append(cases.Items, seedRecord{ID: l.id, Data: map[string]any{
			"id": l.id, "title": l.title, "court": l.court, "date": l.date,
			"country": "jpn", "legal_system": "civil_law", "status": "published",
		}})
	}
	// Jurisdiction records (top 10)
	jurisdictions := seedCollection{Collection: "ai.gftd.apps.hanrei.legal_entity"}
	for _, j := range []struct{ iso3, name, system string }{
		{"jpn", "Japan", "civil_law"}, {"usa", "United States", "common_law"},
		{"gbr", "United Kingdom", "common_law"}, {"deu", "Germany", "civil_law"},
		{"fra", "France", "civil_law"}, {"chn", "China", "civil_law"},
		{"kor", "South Korea", "civil_law"}, {"ind", "India", "common_law"},
		{"bra", "Brazil", "civil_law"}, {"aus", "Australia", "common_law"},
	} {
		def.DIDs = append(def.DIDs, seedDID{Path: "jurisdiction:" + j.iso3, DisplayName: j.name, Description: j.system + " jurisdiction"})
		jurisdictions.Items = append(jurisdictions.Items, seedRecord{ID: j.iso3, Data: map[string]any{
			"id": j.iso3, "iso3": j.iso3, "name": j.name, "legal_system": j.system, "status": "active",
		}})
	}
	def.Records = append(def.Records, cases, jurisdictions)
	return def
}

func handotaiSeeds() seedDef {
	def := seedDef{Domain: "handotai", Nanoid: "dtyy44cr", DID: "did:web:handotai.etzhayyim.com"}
	// Writer DIDs
	writers := []struct{ id, name, lang, cat string }{
		{"pcw", "PC Watch", "ja", "fabrication"},
		{"itm", "ITmedia NEWS", "ja", "market"},
		{"pubk", "Publickey", "ja", "design"},
		{"semia", "SemiAnalysis", "en", "market"},
		{"semie", "Semiconductor Engineering", "en", "design"},
		{"eet", "EE Times", "en", "market"},
	}
	for _, w := range writers {
		def.DIDs = append(def.DIDs, seedDID{Path: "writer:" + w.id, DisplayName: w.name, Description: w.cat + " (" + w.lang + ")"})
	}
	// Source records
	sources := seedCollection{Collection: "ai.gftd.apps.handotai.article"}
	for _, w := range writers {
		sources.Items = append(sources.Items, seedRecord{ID: w.id, Data: map[string]any{
			"source_id": w.id, "name": w.name, "language": w.lang, "category": w.cat,
			"source_type": "rss", "enabled": true,
		}})
	}
	def.Records = append(def.Records, sources)
	return def
}

// ── Command implementation ──

func runSeed(args []string) error {
	if len(args) > 0 && args[0] == "oil-backbone" {
		return runSeedOilBackbone(args[1:])
	}
	if len(args) > 0 && args[0] == "naphtha-supply" {
		return runSeedNaphthaSupply(args[1:])
	}

	fs := flag.NewFlagSet("seed", flag.ContinueOnError)
	pdsURL := fs.String("pds", defaultPDSURL, "PDS base URL")
	app := fs.String("app", "", "filter by app domain (comma-separated, e.g. autorace,keirin)")
	dryRun := fs.Bool("dry-run", false, "show what would be written without writing")
	verbose := fs.Bool("verbose", false, "print each DID write (can be very noisy)")
	timeoutSec := fs.Int("timeout-sec", 180, "HTTP timeout seconds for seed writes")
	retries := fs.Int("retries", 3, "applyWrites retry attempts per batch")
	retryWaitMs := fs.Int("retry-wait-ms", 1200, "wait milliseconds between applyWrites retries")
	throttleMs := fs.Int("throttle-ms", 0, "wait milliseconds between each batch request (rate limit avoidance)")
	kagamiDirect := fs.Bool("kagami-direct", false, "write directly to kagami graph.query XRPC (Sql MERGE, bypass PDS applyWrites)")
	maxItems := fs.Int("max-items", 0, "limit seeded DID/record items per domain (0 = unlimited)")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	token := resolveGFTDToken()
	if token == "" && !*dryRun {
		return fmt.Errorf("auth required — run 'gftd auth login' first")
	}

	client := &http.Client{Timeout: time.Duration(*timeoutSec) * time.Second}
	writeToken := token
	if !*dryRun && token != "" {
		svcTok, err := getServiceAuthToken(client, strings.TrimRight(*pdsURL, "/"), token, "com.atproto.repo.applyWrites")
		if err != nil {
			// Some deployments do not expose getServiceAuth.
			// Fall back to base token and let applyWrites authorization decide.
			fmt.Fprintf(os.Stderr, "warn: service-auth unavailable, falling back to base token: %v\n", err)
		} else if strings.TrimSpace(svcTok) == "" {
			fmt.Fprintf(os.Stderr, "warn: service-auth returned empty token, falling back to base token\n")
		} else {
			writeToken = strings.TrimSpace(svcTok)
			fmt.Println("Using required service-auth token for applyWrites")
		}
	}
	if !*dryRun && writeToken == "" {
		return fmt.Errorf("seed applyWrites: missing write token")
	}
	// graph.query requires the regular session/internal token; service-auth token
	// scoped to applyWrites must not be used in kagami-direct mode.
	kagamiToken := token
	if *kagamiDirect && strings.TrimSpace(kagamiToken) == "" && !*dryRun {
		return fmt.Errorf("kagami-direct: missing auth token")
	}
	registry := buildSeedRegistry()

	// Filter by app
	filter := map[string]bool{}
	if *app != "" {
		for _, a := range strings.Split(*app, ",") {
			filter[strings.TrimSpace(a)] = true
		}
	}

	totalDIDs := 0
	totalRecords := 0

	for _, sd := range registry {
		if len(filter) > 0 && !filter[sd.Domain] {
			continue
		}
		if *maxItems > 0 {
			if len(sd.DIDs) > *maxItems {
				sd.DIDs = sd.DIDs[:*maxItems]
			}
			for i := range sd.Records {
				if len(sd.Records[i].Items) > *maxItems {
					sd.Records[i].Items = sd.Records[i].Items[:*maxItems]
				}
			}
		}

		fmt.Printf("\n=== %s (%s) ===\n", sd.Domain, sd.Nanoid)

		// ── kagami-direct mode: write directly to kagami graph.query XRPC (Sql MERGE) ──
		if *kagamiDirect {
			nanoidDID := strings.TrimSpace(sd.DID)
			if nanoidDID == "" {
				nanoidDID = fmt.Sprintf("did:web:%s.etzhayyim.com", sd.Nanoid)
			}
			for _, d := range sd.DIDs {
				did := nanoidDID + ":" + strings.ReplaceAll(d.Path, ":", ":")
				if *dryRun {
					fmt.Printf("  [dry-run] kagami DID: %s (%s)\n", did, d.DisplayName)
					totalDIDs++
					continue
				}
				sql := `MERGE (n:Identity {vertex_id: $vertex_id}) SET n._alive = true, n.rkey = $rkey, n.repo = $repo, n.did = $did, n.collection = $collection, n.owner_did = $owner_did, n.app_id = $app_id, n.visibility = $visibility, n.sensitivity_ord = $sensitivity_ord, n.display_name = $display_name, n.description = $description, n.status = 'active', n.controller = $controller, n.domain_kind = $domain_kind`
				cmdPayload, _ := json.Marshal(map[string]any{
					"sql": sql,
					"params": map[string]any{
						"vertex_id":       did,
						"rkey":            seedStableRKey("did:" + d.Path),
						"repo":            nanoidDID,
						"did":             did,
						"collection":      "ai.gftd.identity.did",
						"owner_did":       nanoidDID,
						"app_id":          sd.Nanoid,
						"visibility":      "public",
						"sensitivity_ord": 0,
						"display_name":    d.DisplayName,
						"description":     d.Description,
						"controller":      sd.DID,
						"domain_kind":     sd.Domain,
					},
				})
				req, _ := http.NewRequest("POST", *pdsURL+"/xrpc/ai.gftd.kagami.sql", bytes.NewReader(cmdPayload))
				req.Header.Set("Content-Type", "application/json")
				setWriteAuthHeaders(req, kagamiToken)
				resp, err := client.Do(req)
				if err != nil {
					fmt.Fprintf(os.Stderr, "  warn: kagami graph.query DID: %v\n", err)
				} else {
					resp.Body.Close()
					if resp.StatusCode < 400 {
						totalDIDs++
						fmt.Printf("  DID: %s (%s)\n", did, d.DisplayName)
					} else {
						fmt.Fprintf(os.Stderr, "  warn: kagami graph.query DID HTTP %d\n", resp.StatusCode)
					}
				}
				if *throttleMs > 0 {
					time.Sleep(time.Duration(*throttleMs) * time.Millisecond)
				}
			}
			for _, coll := range sd.Records {
				label := collectionToLabelGo(coll.Collection)
				for _, item := range coll.Items {
					entityID := strings.TrimSpace(item.ID)
					if entityID == "" {
						entityID = seedStableRKey(coll.Collection)
					}
					valJSON, _ := json.Marshal(item.Data)
					sql := fmt.Sprintf(
						`MERGE (n:%s {vertex_id: $vertex_id}) SET n._alive = true, n.rkey = $rkey, n.repo = $repo, n.collection = $collection, n.owner_did = $owner_did, n.app_id = $app_id, n.visibility = $visibility, n.sensitivity_ord = $sensitivity_ord, n.val = $val`,
						label,
					)
					cmdPayload, _ := json.Marshal(map[string]any{
						"sql": sql,
						"params": map[string]any{
							"vertex_id":       entityID,
							"rkey":            seedStableRKey(entityID),
							"repo":            nanoidDID,
							"collection":      coll.Collection,
							"owner_did":       nanoidDID,
							"app_id":          sd.Nanoid,
							"visibility":      "public",
							"sensitivity_ord": 0,
							"val":             string(valJSON),
						},
					})
					req, _ := http.NewRequest("POST", *pdsURL+"/xrpc/ai.gftd.kagami.sql", bytes.NewReader(cmdPayload))
					req.Header.Set("Content-Type", "application/json")
					setWriteAuthHeaders(req, kagamiToken)
					resp, err := client.Do(req)
					if err != nil {
						fmt.Fprintf(os.Stderr, "  warn: kagami graph.query record: %v\n", err)
					} else {
						resp.Body.Close()
						if resp.StatusCode < 400 {
							totalRecords++
						} else {
							fmt.Fprintf(os.Stderr, "  warn: kagami graph.query record HTTP %d\n", resp.StatusCode)
						}
					}
					if *throttleMs > 0 {
						time.Sleep(time.Duration(*throttleMs) * time.Millisecond)
					}
				}
				if !*dryRun {
					fmt.Printf("  %d records → %s (label: %s)\n", len(coll.Items), coll.Collection, label)
				}
			}

			// ── Social data: Post + Like per actor ──
			if !*dryRun {
				now := time.Now().UTC()
				postRkey := "seed-post-" + sd.Nanoid
				postText := fmt.Sprintf("Hello from %s! Domain: %s. Seed data loaded.", sd.Domain, sd.Domain)
				postSql := `MERGE (n:Post {vertex_id: $vertex_id}) SET n._alive = true, n.rkey = $rkey, n.repo = $repo, n.collection = $collection, n.owner_did = $owner_did, n.app_id = $app_id, n.visibility = $visibility, n.val = $val`
				postPayload, _ := json.Marshal(map[string]any{
					"sql": postSql,
					"params": map[string]any{
						"vertex_id":  postRkey,
						"rkey":       postRkey,
						"repo":       nanoidDID,
						"collection": "app.bsky.feed.post",
						"owner_did":  nanoidDID,
						"app_id":     sd.Nanoid,
						"visibility": "public",
						"val":        fmt.Sprintf(`{"text":"%s","createdAt":"%s","$type":"app.bsky.feed.post"}`, postText, now.Format(time.RFC3339)),
					},
				})
				req, _ := http.NewRequest("POST", *pdsURL+"/xrpc/ai.gftd.kagami.sql", bytes.NewReader(postPayload))
				req.Header.Set("Content-Type", "application/json")
				setWriteAuthHeaders(req, kagamiToken)
				if resp, err := client.Do(req); err == nil {
					resp.Body.Close()
					if resp.StatusCode < 400 {
						fmt.Printf("  1 Post (seed)\n")
					}
				}
				if *throttleMs > 0 {
					time.Sleep(time.Duration(*throttleMs) * time.Millisecond)
				}

				// Like (self-like to register engagement)
				likeRkey := "seed-like-" + sd.Nanoid
				likeSql := `MERGE (n:Like {vertex_id: $vertex_id}) SET n._alive = true, n.rkey = $rkey, n.repo = $repo, n.collection = $collection, n.owner_did = $owner_did, n.app_id = $app_id, n.val = $val`
				likePayload, _ := json.Marshal(map[string]any{
					"sql": likeSql,
					"params": map[string]any{
						"vertex_id":  likeRkey,
						"rkey":       likeRkey,
						"repo":       nanoidDID,
						"collection": "app.bsky.feed.like",
						"owner_did":  nanoidDID,
						"app_id":     sd.Nanoid,
						"val":        fmt.Sprintf(`{"subject":{"uri":"at://%s/app.bsky.feed.post/%s"},"createdAt":"%s"}`, nanoidDID, postRkey, now.Format(time.RFC3339)),
					},
				})
				req2, _ := http.NewRequest("POST", *pdsURL+"/xrpc/ai.gftd.kagami.sql", bytes.NewReader(likePayload))
				req2.Header.Set("Content-Type", "application/json")
				setWriteAuthHeaders(req2, kagamiToken)
				if resp, err := client.Do(req2); err == nil {
					resp.Body.Close()
					if resp.StatusCode < 400 {
						fmt.Printf("  1 Like (seed)\n")
					}
				}
				if *throttleMs > 0 {
					time.Sleep(time.Duration(*throttleMs) * time.Millisecond)
				}
			}

			continue
		}

		// 0. Register domain app via com.atproto.admin.registerApp (canonical path for Profile + App + graph ops)
		appDID := strings.TrimSpace(sd.DID)
		if appDID == "" {
			appDID = fmt.Sprintf("did:web:%s.etzhayyim.com", sd.Nanoid)
		}
		appDisplayName := sd.Domain
		if len(sd.DIDs) > 0 {
			appDisplayName = sd.Domain + " (" + fmt.Sprintf("%d entities", len(sd.DIDs)) + ")"
		}
		if !*dryRun {
			regPayload, _ := json.Marshal(map[string]any{
				"nanoid":        sd.Nanoid,
				"displayName":   appDisplayName,
				"description":   sd.Domain + " domain — " + fmt.Sprintf("%d DIDs, %d collections", len(sd.DIDs), len(sd.Records)),
				"did":           appDID,
				"performerType": "service",
				"contentMode":   "timeline",
				"sensitivity":   "public",
			})
			req, _ := http.NewRequest("POST", *pdsURL+"/xrpc/com.atproto.admin.registerApp", bytes.NewReader(regPayload))
			req.Header.Set("Content-Type", "application/json")
			setAuthHeaders(req)
			resp, err := client.Do(req)
			if err != nil {
				fmt.Fprintf(os.Stderr, "  warn: registerApp: %v\n", err)
			} else {
				resp.Body.Close()
				if resp.StatusCode >= 400 {
					fmt.Fprintf(os.Stderr, "  warn: registerApp HTTP %d\n", resp.StatusCode)
				}
			}
		}

		// 1. Register DIDs via applyWrites (PDS mergeRecord creates :DID nodes in yata)
		// Also write app.bsky.actor.profile for each sub-DID so they appear as :Actor
		// nodes in RisingWave vertex_actor (identity.did records don't propagate to graph).
		didWrites := make([]map[string]any, 0, len(sd.DIDs)*2)
		for _, d := range sd.DIDs {
			did := sd.DID + ":" + strings.ReplaceAll(d.Path, ":", ":")
			if *dryRun {
				fmt.Printf("  [dry-run] DID: %s (%s)\n", did, d.DisplayName)
				totalDIDs++
				continue
			}
			didWrites = append(didWrites, map[string]any{
				"action":     "update",
				"collection": "ai.gftd.identity.did",
				"rkey":       seedStableRKey("did:" + d.Path),
				"value": map[string]any{
					"id": did, "display_name": d.DisplayName, "description": d.Description,
					"status": "active", "controller": sd.DID,
					"org_id": "anon", "user_id": "anon", "actor_id": sd.Nanoid,
					"actorDid":          sd.DID,
					"domainKind":        sd.Domain,
					"sourceType":        "seed",
					"sourceId":          "seed:" + sd.Domain,
					"canonicalEntityId": did,
					"heartbeatAt":       time.Now().UTC().Format(time.RFC3339),
					"created_at":        time.Now().UTC().Format(time.RFC3339),
				},
			})
			// Mirror as actor.profile so PDS commit pipeline writes to vertex_profile
			didWrites = append(didWrites, map[string]any{
				"action":     "update",
				"collection": "app.bsky.actor.profile",
				"rkey":       seedStableRKey("profile:" + d.Path),
				"value": map[string]any{
					"did":          did,
					"repo":         sd.DID,
					"display_name": d.DisplayName,
					"description":  d.Description + " [" + sd.Domain + "]",
					"sensitivity":  "public",
				},
			})
		}
		if !*dryRun && len(didWrites) > 0 {
			for i := 0; i < len(didWrites); i += 50 {
				end := i + 50
				if end > len(didWrites) {
					end = len(didWrites)
				}
				batch := didWrites[i:end]
				payload, _ := json.Marshal(map[string]any{"repo": sd.DID, "writes": batch})
				req, _ := http.NewRequest("POST", *pdsURL+"/xrpc/com.atproto.repo.applyWrites", bytes.NewReader(payload))
				req.Header.Set("Content-Type", "application/json")
				setWriteAuthHeaders(req, writeToken)
				resp, body, err := doApplyWritesWithRetry(client, req, *retries, time.Duration(*retryWaitMs)*time.Millisecond)
				if err != nil {
					fmt.Fprintf(os.Stderr, "  warn: DID applyWrites: %v\n", err)
					continue
				}
				if resp.StatusCode == 429 {
					fmt.Fprintf(os.Stderr, "  warn: DID applyWrites HTTP 429 — sleeping 10s...\n")
					time.Sleep(10 * time.Second)
					// Re-send same batch after cooldown
					req2, _ := http.NewRequest("POST", *pdsURL+"/xrpc/com.atproto.repo.applyWrites", bytes.NewReader(payload))
					req2.Header.Set("Content-Type", "application/json")
					setWriteAuthHeaders(req2, writeToken)
					resp2, body2, err2 := doApplyWritesWithRetry(client, req2, *retries, time.Duration(*retryWaitMs)*time.Millisecond)
					if err2 == nil && resp2.StatusCode < 400 {
						totalDIDs += len(batch)
						if *verbose {
							for _, w := range batch {
								logSeedDIDWrite(w)
							}
						}
					} else {
						msg := ""
						if err2 != nil {
							msg = err2.Error()
						} else {
							msg = fmt.Sprintf("HTTP %d: %s", resp2.StatusCode, truncStr(string(body2), 200))
						}
						fmt.Fprintf(os.Stderr, "  warn: DID applyWrites retry failed: %s\n", msg)
					}
				} else if resp.StatusCode >= 400 {
					fmt.Fprintf(os.Stderr, "  warn: DID applyWrites HTTP %d: %s\n", resp.StatusCode, truncStr(string(body), 200))
					continue
				} else {
					totalDIDs += len(batch)
					if *verbose {
						for _, w := range batch {
							logSeedDIDWrite(w)
						}
					}
				}
				if *throttleMs > 0 {
					time.Sleep(time.Duration(*throttleMs) * time.Millisecond)
				}
			}
		}

		// 2. Write domain records via applyWrites
		for _, coll := range sd.Records {
			writes := make([]map[string]any, 0, len(coll.Items))
			for _, item := range coll.Items {
				entityID := strings.TrimSpace(item.ID)
				if entityID == "" {
					entityID = seedStableRKey(coll.Collection)
				}
				rec := map[string]any{
					"org_id": "anon", "user_id": "anon", "actor_id": sd.Nanoid,
					"created_at":        time.Now().UTC().Format(time.RFC3339),
					"actorDid":          sd.DID,
					"domainKind":        sd.Domain,
					"sourceType":        "seed",
					"sourceId":          "seed:" + sd.Domain,
					"canonicalEntityId": entityID,
					"heartbeatAt":       time.Now().UTC().Format(time.RFC3339),
				}
				for k, v := range item.Data {
					rec[k] = v
				}
				if _, ok := rec["id"]; !ok {
					rec["id"] = entityID
				}
				if _, ok := rec["canonicalEntityId"]; !ok {
					rec["canonicalEntityId"] = entityID
				}
				writes = append(writes, map[string]any{
					"action":     "update",
					"collection": coll.Collection,
					"rkey":       seedStableRKey(entityID),
					"value":      rec,
				})
			}

			if *dryRun {
				fmt.Printf("  [dry-run] %d records → %s\n", len(writes), coll.Collection)
				totalRecords += len(writes)
				continue
			}

			// Batch in groups of 50
			for i := 0; i < len(writes); i += 50 {
				end := i + 50
				if end > len(writes) {
					end = len(writes)
				}
				batch := writes[i:end]
				payload, _ := json.Marshal(map[string]any{"repo": sd.DID, "writes": batch})

				req, _ := http.NewRequest("POST", *pdsURL+"/xrpc/com.atproto.repo.applyWrites", bytes.NewReader(payload))
				req.Header.Set("Content-Type", "application/json")
				setWriteAuthHeaders(req, writeToken)

				resp, body, err := doApplyWritesWithRetry(client, req, *retries, time.Duration(*retryWaitMs)*time.Millisecond)
				if err != nil {
					fmt.Fprintf(os.Stderr, "  warn: applyWrites %s: %v\n", coll.Collection, err)
					continue
				}

				if resp.StatusCode == 429 {
					fmt.Fprintf(os.Stderr, "  warn: applyWrites %s HTTP 429 — sleeping 10s...\n", coll.Collection)
					time.Sleep(10 * time.Second)
					req2, _ := http.NewRequest("POST", *pdsURL+"/xrpc/com.atproto.repo.applyWrites", bytes.NewReader(payload))
					req2.Header.Set("Content-Type", "application/json")
					setWriteAuthHeaders(req2, writeToken)
					resp2, body2, err2 := doApplyWritesWithRetry(client, req2, *retries, time.Duration(*retryWaitMs)*time.Millisecond)
					if err2 == nil && resp2.StatusCode < 400 {
						totalRecords += len(batch)
						fmt.Printf("  %d records → %s\n", len(batch), coll.Collection)
					} else {
						msg := ""
						if err2 != nil {
							msg = err2.Error()
						} else {
							msg = fmt.Sprintf("HTTP %d: %s", resp2.StatusCode, truncStr(string(body2), 200))
						}
						fmt.Fprintf(os.Stderr, "  warn: applyWrites %s retry failed: %s\n", coll.Collection, msg)
					}
				} else if resp.StatusCode >= 400 {
					fmt.Fprintf(os.Stderr, "  warn: applyWrites %s HTTP %d: %s\n", coll.Collection, resp.StatusCode, truncStr(string(body), 200))
					continue
				} else {
					totalRecords += len(batch)
					fmt.Printf("  %d records → %s\n", len(batch), coll.Collection)
				}
				if *throttleMs > 0 {
					time.Sleep(time.Duration(*throttleMs) * time.Millisecond)
				}
			}
		}

		// 3. Social data: Post + Like per actor via applyWrites
		if !*dryRun {
			now := time.Now().UTC().Format(time.RFC3339)
			postRkey := "seed-post-" + sd.Nanoid
			socialWrites := []map[string]any{
				{
					"action": "update", "collection": "app.bsky.feed.post", "rkey": postRkey,
					"value": map[string]any{
						"$type":     "app.bsky.feed.post",
						"text":      fmt.Sprintf("Hello from %s! Domain data loaded.", sd.Domain),
						"createdAt": now,
					},
				},
				{
					"action": "update", "collection": "app.bsky.feed.like", "rkey": "seed-like-" + sd.Nanoid,
					"value": map[string]any{
						"$type":     "app.bsky.feed.like",
						"subject":   map[string]any{"uri": fmt.Sprintf("at://%s/app.bsky.feed.post/%s", sd.DID, postRkey)},
						"createdAt": now,
					},
				},
			}
			payload, _ := json.Marshal(map[string]any{"repo": sd.DID, "writes": socialWrites})
			req, _ := http.NewRequest("POST", *pdsURL+"/xrpc/com.atproto.repo.applyWrites", bytes.NewReader(payload))
			req.Header.Set("Content-Type", "application/json")
			setWriteAuthHeaders(req, writeToken)
			resp, _, err := doApplyWritesWithRetry(client, req, *retries, time.Duration(*retryWaitMs)*time.Millisecond)
			if err == nil && resp.StatusCode < 400 {
				fmt.Printf("  1 Post + 1 Like (social seed)\n")
			} else if resp != nil && resp.StatusCode == 429 {
				fmt.Fprintf(os.Stderr, "  warn: social seed HTTP 429\n")
			}
			if *throttleMs > 0 {
				time.Sleep(time.Duration(*throttleMs) * time.Millisecond)
			}
		}
	}

	fmt.Printf("\n=== Summary ===\n  DIDs: %d\n  Records: %d\n", totalDIDs, totalRecords)
	if *dryRun {
		fmt.Println("  (dry-run — nothing written)")
	}
	return nil
}

// execSql sends a Sql statement to PDS via ai.gftd.kagami.sql.
func execSql(client *http.Client, pdsURL, token, sql string, params map[string]any) error {
	payload, _ := json.Marshal(map[string]any{"statement": sql, "parameters": params})

	endpoints := []string{
		"/xrpc/ai.gftd.kagami.sql",
	}
	var lastErr error
	for _, ep := range endpoints {
		req, _ := http.NewRequest("POST", pdsURL+ep, bytes.NewReader(payload))
		req.Header.Set("Content-Type", "application/json")
		setWriteAuthHeaders(req, token)
		resp, err := client.Do(req)
		if err != nil {
			lastErr = err
			continue
		}
		body, _ := io.ReadAll(resp.Body)
		resp.Body.Close()
		if resp.StatusCode == 404 {
			lastErr = fmt.Errorf("endpoint %s not found", ep)
			continue
		}
		if resp.StatusCode >= 400 {
			return fmt.Errorf("HTTP %d: %s", resp.StatusCode, truncStr(string(body), 200))
		}
		return nil
	}
	return lastErr
}

func getServiceAuthToken(client *http.Client, pdsURL, baseToken, lxm string) (string, error) {
	pdsAud := "did:web:mod.etzhayyim.com"
	if u, err := url.Parse(strings.TrimSpace(pdsURL)); err == nil {
		if host := strings.TrimSpace(u.Hostname()); host != "" {
			pdsAud = "did:web:" + host
		}
	}
	type attempt struct {
		aud         string
		includeDID  bool
		includeOrg  bool
		description string
	}
	attempts := []attempt{
		{aud: pdsAud, includeDID: true, includeOrg: true, description: "host-aud+active-did"},
		{aud: pdsAud, includeDID: false, includeOrg: true, description: "host-aud"},
		{aud: "did:web:mod.etzhayyim.com", includeDID: false, includeOrg: true, description: "mod-aud"},
	}
	var lastErr error
	for _, at := range attempts {
		body, _ := json.Marshal(map[string]any{
			"aud": at.aud,
			"lxm": lxm,
		})
		req, _ := http.NewRequest("POST", pdsURL+"/xrpc/com.atproto.server.getServiceAuth", bytes.NewReader(body))
		req.Header.Set("Content-Type", "application/json")
		req.Header.Set("Authorization", "Bearer "+baseToken)
		if at.includeDID {
			if did := resolveActiveDID(); did != "" {
				req.Header.Set("X-Active-DID", did)
			}
		}
		if at.includeOrg {
			if org := resolveOrgHint(); org != "" {
				req.Header.Set("X-Gftd-Org-Id", org)
			}
		}
		resp, err := client.Do(req)
		if err != nil {
			lastErr = err
			continue
		}
		raw, _ := io.ReadAll(resp.Body)
		resp.Body.Close()
		if resp.StatusCode >= 400 {
			lastErr = fmt.Errorf("%s: HTTP %d: %s", at.description, resp.StatusCode, truncStr(string(raw), 200))
			continue
		}
		var out struct {
			Token string `json:"token"`
		}
		if err := json.Unmarshal(raw, &out); err != nil {
			lastErr = err
			continue
		}
		if out.Token == "" {
			lastErr = fmt.Errorf("%s: empty token", at.description)
			continue
		}
		return out.Token, nil
	}
	return "", lastErr
}

func doApplyWritesWithRetry(client *http.Client, req *http.Request, retries int, retryWait time.Duration) (*http.Response, []byte, error) {
	if retries < 1 {
		retries = 1
	}
	var lastErr error
	var lastStatus int
	var lastBody []byte
	for attempt := 1; attempt <= retries; attempt++ {
		cloned := req.Clone(req.Context())
		if req.GetBody != nil {
			body, err := req.GetBody()
			if err != nil {
				return nil, nil, err
			}
			cloned.Body = body
		}

		resp, err := client.Do(cloned)
		if err != nil {
			lastErr = err
		} else {
			body, _ := io.ReadAll(resp.Body)
			resp.Body.Close()
			lastStatus = resp.StatusCode
			lastBody = body
			if resp.StatusCode < 500 {
				// return 2xx/4xx as-is; caller handles 4xx warnings.
				return resp, body, nil
			}
			lastErr = fmt.Errorf("HTTP %d: %s", resp.StatusCode, truncStr(string(body), 200))
		}

		if attempt < retries {
			time.Sleep(retryWait)
		}
	}
	if lastErr != nil {
		return nil, nil, lastErr
	}
	return nil, nil, fmt.Errorf("HTTP %d: %s", lastStatus, truncStr(string(lastBody), 200))
}

// collectionToLabelGo converts an AT Protocol collection to a PascalCase label.
// Mirrors the TS collectionToLabel: take last segment, PascalCase each [-_] part.
func collectionToLabelGo(collection string) string {
	parts := strings.Split(collection, ".")
	last := parts[len(parts)-1]
	segs := strings.FieldsFunc(last, func(r rune) bool { return r == '-' || r == '_' })
	var b strings.Builder
	for _, seg := range segs {
		if len(seg) > 0 {
			b.WriteString(strings.ToUpper(seg[:1]) + seg[1:])
		}
	}
	return b.String()
}

func seedStableRKey(in string) string {
	s := strings.TrimSpace(strings.ToLower(in))
	if s == "" {
		return "seed"
	}
	var b strings.Builder
	b.Grow(len(s))
	lastDash := false
	for _, r := range s {
		ok := (r >= 'a' && r <= 'z') || (r >= '0' && r <= '9') || r == '.' || r == '_' || r == '~' || r == '-'
		if ok {
			b.WriteRune(r)
			lastDash = false
			continue
		}
		if !lastDash {
			b.WriteByte('-')
			lastDash = true
		}
	}
	out := strings.Trim(b.String(), "-")
	if out == "" {
		return "seed"
	}
	if len(out) > 512 {
		out = out[:512]
	}
	return out
}
