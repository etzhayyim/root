;; ported from 70-tools/e7m-sim/scenes/sarutahiko-factory-r0/ifc_export.py — real
;; 1:1 port replacing the unit_refactor stage-0 "TODO: port-failed" stubs.
;; sarutahiko-factory-r0 — IFC4 (ISO-10303-21 / STEP) export.
;;
;; Converts the scene SSoT into `factory.ifc` — a structurally-valid IFC4 model.
;; Every element is a box (IfcExtrudedAreaSolid over IfcRectangleProfile) wired
;; into IfcProject → IfcSite → IfcBuilding → IfcBuildingStorey, tagged with a
;; property set carrying 企業名/機器名/調達もと from building.edn.
;;
;; SELF-CONTAINED: the Python `box_element` calls `procurement.enrich_part`; that
;; sibling helper is inlined verbatim here (`enrich-part`) so this file requires
;; no sibling stub ns. `ifc_guid` uses MD5; scene maps stay string-keyed exactly
;; as Python json.loads produced. Host I/O (the file write in `export-ifc`, plus
;; the `__main__` demo) lives behind #?(:clj ...). The Python `main` (which reads
;; factory.scene.json + building.edn) is provided as `-main` on :clj only.
(ns e7m-sim.scenes.sarutahiko-factory-r0.ifc-export
  (:require [clojure.string :as str]
            #?(:clj [cheshire.core :as json])))

(def ^:private guid-chars
  "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_$")

;; ── deterministic 22-char IFC GUID from a stable key ──────────────────────────
;; num = int(md5(key).hexdigest(), 16); 21×6-bit digits + 1×2-bit, MSB first.
(defn ifc-guid [^String k]
  #?(:clj
     (let [bytes (.digest (java.security.MessageDigest/getInstance "MD5")
                          (.getBytes k "UTF-8"))
           num (reduce (fn [^java.math.BigInteger acc b]
                         (.add (.shiftLeft acc 8)
                               (java.math.BigInteger/valueOf (bit-and b 0xff))))
                       java.math.BigInteger/ZERO
                       bytes)
           sixty-three (java.math.BigInteger/valueOf 63)
           three (java.math.BigInteger/valueOf 3)
           [digits _] (loop [i 0, n num, ds []]
                        (if (< i 21)
                          (recur (inc i) (.shiftRight n 6)
                                 (conj ds (.intValue (.and n sixty-three))))
                          [(conj ds (.intValue (.and n three))) n]))
           ordered (reverse digits)]
       (apply str (map #(nth guid-chars %) ordered)))
     :default (throw (ex-info "ifc-guid needs an MD5 impl on this host" {:key k}))))

;; ── tiny STEP writer (the Python `Ifc` class) as an atom of {:lines :n} ───────
(defn- mk-ifc [] (atom {:lines [] :n 0}))

(defn- ifc-add!
  "Append `body` as `#<n>=<body>;`; return the new entity id (n)."
  [f ^String body]
  (let [{:keys [n]} (swap! f (fn [{:keys [lines n]}]
                               (let [n' (inc n)]
                                 {:lines (conj lines (str "#" n' "=" body ";")) :n n'})))]
    n))

(defn- reflist [ids]
  (str "(" (str/join "," (map #(str "#" %) ids)) ")"))

(defn- aabb-box [a]
  [(* 0.5 (+ (nth a 0) (nth a 2)))
   (* 0.5 (+ (nth a 1) (nth a 3)))
   (max (- (nth a 2) (nth a 0)) 0.05)
   (max (- (nth a 3) (nth a 1)) 0.05)])

;; Python f"{x:.4f}" — fixed 4-decimal formatting.
(defn- f4 [x] #?(:clj (format "%.4f" (double x)) :default (str x)))

;; ── inlined procurement.enrich_part (verbatim port; supplier/origin used) ─────
(def ^:private supplier-table
  {"JFE Steel" ["メタルワン (商社)" "JP" 8 "distributor"]
   "Nippon Steel" ["伊藤忠丸紅鉄鋼 (商社)" "JP" 10 "distributor"]
   "Nisshin Steel" ["阪和興業 (商社)" "JP" 8 "distributor"]
   "Hilti" ["ヒルティ・ジャパン (直販)" "LI/CN" 3 "direct"]
   "IG Kogyo" ["アイジー工業 特約店" "JP" 6 "distributor"]
   "Bunka Shutter" ["文化シヤッター 直需" "JP" 7 "direct"]
   "Sankyo Tateyama" ["三協アルミ建材代理店" "JP" 5 "distributor"]
   "Lonseal" ["ロンシール工業 特約店" "JP" 4 "distributor"]
   "Nitto Kogyo" ["因幡電機産業 (電材商社)" "JP" 6 "distributor"]
   "Hitachi" ["日立産機システム 代理店" "JP" 10 "distributor"]
   "Panasonic" ["因幡電機産業 (電材商社)" "JP" 4 "distributor"]
   "Kawamura" ["河村電器 特約店" "JP" 5 "distributor"]
   "Nichido Denko" ["ネグロス/日動電工 商社" "JP" 4 "distributor"]
   "Furukawa Electric" ["古河電工 → 電線商社" "JP" 6 "distributor"]
   "Fujikura" ["フジクラ → 電線商社" "JP" 5 "distributor"]
   "Denyo" ["デンヨー 代理店" "JP" 6 "distributor"]
   "Iwasaki Electric" ["岩崎電気 特約店" "JP" 4 "distributor"]
   "Kubota" ["クボタケミックス → 橋本総業" "JP" 4 "distributor"]
   "Sekisui" ["積水化学 → 橋本総業 (管材商社)" "JP" 3 "distributor"]
   "Ebara" ["荏原製作所 代理店" "JP" 6 "distributor"]
   "Mitsubishi" ["三菱電機 住環境 代理店" "JP" 5 "distributor"]
   "TOTO" ["TOTO → 住設商社 (橋本総業)" "JP" 4 "distributor"]
   "Hinode Suido" ["日之出水道機器 代理店" "JP" 5 "distributor"]
   "Aichi Tokei" ["愛知時計電機 代理店" "JP" 6 "distributor"]
   "Yazaki" ["矢崎エナジーシステム 代理店" "JP" 5 "distributor"]
   "Daikin" ["ダイキン工業 → 空調設備業者" "JP" 8 "distributor"]
   "SMC" ["SMC → エア機器商社 (山善)" "JP" 4 "distributor"]
   "Hochiki" ["ホーチキ → 消防設備業者" "JP" 8 "distributor"]
   "Morita Miyata" ["モリタ宮田工業 代理店" "JP" 3 "distributor"]
   "Senju Sprinkler" ["千住スプリンクラー → 消防設備業者" "JP" 8 "distributor"]
   "DMG Mori" ["DMG森精機 (直販)" "JP/DE" 16 "direct"]
   "Okuma" ["オークマ (直販)" "JP" 14 "direct"]
   "Mitutoyo" ["ミツトヨ (直販)" "JP" 10 "direct"]
   "Okura Yusoki" ["オークラ輸送機 直需" "JP" 12 "direct"]
   "Daifuku" ["ダイフク 直需" "JP" 18 "direct"]
   "Komatsu" ["コマツ産機 (直販)" "JP" 28 "direct"]
   "Taikisha" ["大気社 (直販, 塗装プラント)" "JP" 30 "direct"]
   "Meidensha" ["明電舎 (直販, ダイナモ)" "JP" 20 "direct"]
   "Sankin" ["三協立山/サンキン 代理店" "JP" 4 "distributor"]
   "Saga Tekkohsho" ["佐賀鉄工所 代理店" "JP" 4 "distributor"]
   "Landes" ["ランデス 特約店" "JP" 4 "distributor"]
   "NIPPO" ["NIPPO 合材プラント (地場)" "JP" 1 "local"]
   "NTT" ["NTT東日本/西日本 (引込工事)" "JP" 8 "direct"]
   "Sika" ["シーカ・ジャパン 代理店" "JP/CH" 3 "distributor"]
   "Nippon Paint" ["日本ペイント → 塗料商社" "JP" 3 "distributor"]
   "ABC Trading" ["ABC商会 (直販)" "JP" 3 "direct"]})

(def ^:private local-hints ["近隣" "地場" "水道局" "Tokyo Gas" "JIS"])

(defn enrich-part
  "Extra procurement claims for one building.edn part map (1:1 port of
  procurement.enrich_part). Returns a string-keyed map."
  [part]
  (let [mfr (get part "part/manufacturer" "")
        proc (get part "part/procurement" "")]
    (cond
      (and (= proc "custom-fab") (= mfr ""))
      {"part/supplier" "施工JV / 専門工事業者 (発注)"
       "part/origin" "JP (on-site fab)"
       "part/leadTime" "施工計画依存"
       "part/channel" "subcontract"}

      :else
      (let [entry (get supplier-table mfr)]
        (cond
          (and (nil? entry) (some #(str/includes? mfr %) local-hints))
          {"part/supplier" (str mfr " (地場プラント/指定業者)")
           "part/origin" "JP"
           "part/leadTime" "1-2 週"
           "part/channel" "local"}

          (nil? entry)
          {"part/supplier" (if (not= mfr "") (str mfr " 代理店 (要確認)") "要選定")
           "part/origin" "要確認"
           "part/leadTime" "要見積"
           "part/channel" "distributor"}

          :else
          (let [[supplier origin weeks channel] entry]
            {"part/supplier" supplier
             "part/origin" origin
             "part/leadTime" (str weeks " 週 (代表値)")
             "part/channel" channel}))))))

;; ── export ────────────────────────────────────────────────────────────────
;; Returns {"entities" n "elements" m "psets" p}. When `path` is non-nil and
;; we're on a :clj host, also writes the .ifc file (host I/O edge).
(defn export-ifc [scene parts path]
  (let [f (mk-ifc)
        ;; link a BOM part to a render-element id via part/sim-feature
        by-feat (reduce (fn [acc p]
                          (let [sf (get p "part/sim-feature")]
                            (if (and sf (not (contains? acc sf)))
                              (assoc acc sf p) acc)))
                        {} parts)
        ;; ── shared geometry context ──
        _org (ifc-add! f "IFCORGANIZATION($,'etzhayyim','Sarutahiko factory R0 (kami-engine)',$,$)")
        person (ifc-add! f "IFCPERSON($,'kami-app-sarutahiko-factory',$,$,$,$,$,$)")
        pando (ifc-add! f (str "IFCPERSONANDORGANIZATION(#" person ",#" _org ",$)"))
        app (ifc-add! f (str "IFCAPPLICATION(#" _org ",'R0','kotoba-sarutahiko-factory','sarutahiko-factory')"))
        owner (ifc-add! f (str "IFCOWNERHISTORY(#" pando ",#" app ",$,.ADDED.,$,$,$,0)"))
        p0 (ifc-add! f "IFCCARTESIANPOINT((0.,0.,0.))")
        dz (ifc-add! f "IFCDIRECTION((0.,0.,1.))")
        dx (ifc-add! f "IFCDIRECTION((1.,0.,0.))")
        axis3 (ifc-add! f (str "IFCAXIS2PLACEMENT3D(#" p0 ",#" dz ",#" dx ")"))
        wcs (ifc-add! f (str "IFCAXIS2PLACEMENT3D(#" p0 ",#" dz ",#" dx ")"))
        ctx (ifc-add! f (str "IFCGEOMETRICREPRESENTATIONCONTEXT($,'Model',3,1.E-05,#" wcs ",$)"))
        lu (ifc-add! f "IFCSIUNIT(*,.LENGTHUNIT.,$,.METRE.)")
        au (ifc-add! f "IFCSIUNIT(*,.AREAUNIT.,$,.SQUARE_METRE.)")
        vu (ifc-add! f "IFCSIUNIT(*,.VOLUMEUNIT.,$,.CUBIC_METRE.)")
        pa (ifc-add! f "IFCSIUNIT(*,.PLANEANGLEUNIT.,$,.RADIAN.)")
        units (ifc-add! f (str "IFCUNITASSIGNMENT((#" lu ",#" au ",#" vu ",#" pa "))"))
        proj (ifc-add! f (str "IFCPROJECT('" (ifc-guid "project") "',#" owner ",'sarutahiko-factory-r0',"
                              "'Sarutahiko robot manufacturing plant R0',$,$,$,(#" ctx "),#" units ")"))
        ;; ── spatial hierarchy ──
        placement (fn [parent-id x y z]
                    (let [pt (ifc-add! f (str "IFCCARTESIANPOINT((" (f4 x) "," (f4 y) "," (f4 z) "))"))
                          a3 (ifc-add! f (str "IFCAXIS2PLACEMENT3D(#" pt ",#" dz ",#" dx ")"))]
                      (if (nil? parent-id)
                        (ifc-add! f (str "IFCLOCALPLACEMENT($,#" a3 ")"))
                        (ifc-add! f (str "IFCLOCALPLACEMENT(#" parent-id ",#" a3 ")")))))
        site-pl (placement nil 0.0 0.0 0.0)
        site (ifc-add! f (str "IFCSITE('" (ifc-guid "site") "',#" owner ",'Site',$,$,#" site-pl ",$,$,"
                              ".ELEMENT.,$,$,$,$,$)"))
        bldg-pl (placement site-pl 0.0 0.0 0.0)
        bldg (ifc-add! f (str "IFCBUILDING('" (ifc-guid "bldg") "',#" owner ",'Plant',$,$,#" bldg-pl ",$,$,"
                              ".ELEMENT.,$,$,$)"))
        storey-pl (placement bldg-pl 0.0 0.0 0.0)
        storey (ifc-add! f (str "IFCBUILDINGSTOREY('" (ifc-guid "storey") "',#" owner ",'GF',$,$,#" storey-pl ","
                                "$,$,.ELEMENT.,0.)"))
        _ (ifc-add! f (str "IFCRELAGGREGATES('" (ifc-guid "agg-proj") "',#" owner ",$,$,#" proj ",(#" site "))"))
        _ (ifc-add! f (str "IFCRELAGGREGATES('" (ifc-guid "agg-site") "',#" owner ",$,$,#" site ",(#" bldg "))"))
        _ (ifc-add! f (str "IFCRELAGGREGATES('" (ifc-guid "agg-bldg") "',#" owner ",$,$,#" bldg ",(#" storey "))"))
        contained (atom [])
        rel-psets (atom [])
        box-element
        (fn [ifc-class eid name cx cy cz sx sy sz]
          (let [prof-pos (ifc-add! f (str "IFCAXIS2PLACEMENT2D(#" (ifc-add! f "IFCCARTESIANPOINT((0.,0.))") ","
                                          "#" (ifc-add! f "IFCDIRECTION((1.,0.))") ")"))
                prof (ifc-add! f (str "IFCRECTANGLEPROFILEDEF(.AREA.,$,#" prof-pos "," (f4 sx) "," (f4 sy) ")"))
                solid (ifc-add! f (str "IFCEXTRUDEDAREASOLID(#" prof ",#" axis3 ",#" dz "," (f4 sz) ")"))
                shape (ifc-add! f (str "IFCSHAPEREPRESENTATION(#" ctx ",'Body','SweptSolid',(#" solid "))"))
                pds (ifc-add! f (str "IFCPRODUCTDEFINITIONSHAPE($,$,(#" shape "))"))
                pl (placement storey-pl cx cy (- cz (/ sz 2.0)))
                nm (str/replace name "'" "")
                e (ifc-add! f (str "IFC" ifc-class "('" (ifc-guid eid) "',#" owner ",'" nm "',$,$,#"
                                   pl ",#" pds ",'" eid "',$)"))]
            (swap! contained conj e)
            (when-let [part (get by-feat eid)]
              (let [proc (enrich-part part)
                    props (reduce
                           (fn [acc [label val]]
                             (if (and val (not= val ""))
                               (let [sval (str/replace (str val) "'" "")]
                                 (conj acc (ifc-add! f (str "IFCPROPERTYSINGLEVALUE('" label "',$,IFCTEXT('" sval "'),$)"))))
                               acc))
                           []
                           [["企業名/Manufacturer" (get part "part/manufacturer" "")]
                            ["機器名/Model" (get part "part/product" "")]
                            ["型番/MPN" (get part "part/mpn" "")]
                            ["調達もと/Supplier" (get proc "part/supplier" "")]
                            ["原産国/Origin" (get proc "part/origin" "")]
                            ["part-id" (get part "part/id" "")]])]
                (when (seq props)
                  (let [ps (ifc-add! f (str "IFCPROPERTYSET('" (ifc-guid (str "ps-" eid)) "',#" owner ","
                                            "'Pset_SarutahikoProcurement',$," (reflist props) ")"))]
                    (swap! rel-psets conj [e ps eid])))))
            e))]
    ;; structure
    (doseq [c (get scene "columns" [])]
      (box-element "COLUMN" (get c "id") "Column" (get c "x") (get c "y") (/ (get c "height") 2)
                   (get c "w") (get c "w") (get c "height")))
    (doseq [b (get scene "beams" [])]
      (let [[y0 y1] (sort (get b "span_y"))]
        (box-element "BEAM" (get b "id") "Roof beam" (get b "x") (* 0.5 (+ y0 y1)) (get b "z")
                     (get b "section") (- y1 y0) (get b "section"))))
    (doseq [w (get scene "walls" [])]
      (let [[cx cy sx sy] (aabb-box (get w "aabb"))]
        (box-element "WALL" (get w "id") "Wall" cx cy (/ (get w "height") 2) sx sy (get w "height"))))
    ;; floor slab
    (let [bb (get scene "bbox_m")]
      (box-element "SLAB" "floor" "Ground slab" (* 0.5 (+ (nth bb 0) (nth bb 2))) (* 0.5 (+ (nth bb 1) (nth bb 3)))
                   0.0 (- (nth bb 2) (nth bb 0)) (- (nth bb 3) (nth bb 1)) 0.2))
    ;; zones → IfcBuildingElementProxy
    (doseq [z (get scene "zones" [])]
      (let [[cx cy sx sy] (aabb-box (get z "rect"))]
        (box-element "BUILDINGELEMENTPROXY" (get z "id") (str "Zone " (get z "label")) cx cy 0.1
                     sx sy 0.2)))
    ;; machines + service nodes → IfcBuildingElementProxy
    (doseq [m (get scene "machines" [])]
      (let [[cx cy sx sy] (aabb-box (get m "aabb"))]
        (box-element "BUILDINGELEMENTPROXY" (get m "id") (get m "kind") cx cy (/ (get m "height") 2)
                     sx sy (get m "height"))))
    (doseq [nb (get scene "service_nodes" [])]
      (let [[cx cy sx sy] (aabb-box (get nb "aabb"))]
        (box-element "BUILDINGELEMENTPROXY" (get nb "id") (get nb "kind") cx cy (/ (get nb "height") 2)
                     sx sy (get nb "height"))))
    ;; utilities → IfcFlowSegment (one box per polyline segment)
    (doseq [u (get scene "utilities" [])]
      (let [pts (get u "path")
            hw (max (get u "width") 0.12)]
        (doseq [i (range (dec (count pts)))]
          (let [[x0 y0] (nth pts i)
                [x1 y1] (nth pts (inc i))
                cx (* 0.5 (+ x0 x1))
                cy (* 0.5 (+ y0 y1))
                sx (max (Math/abs (double (- x1 x0))) hw)
                sy (max (Math/abs (double (- y1 y0))) hw)]
            (box-element "FLOWSEGMENT" (str (get u "id") "_" i) (get u "kind") cx cy (get u "z")
                         sx sy hw)))))
    (when (seq @contained)
      (ifc-add! f (str "IFCRELCONTAINEDINSPATIALSTRUCTURE('" (ifc-guid "contain") "',#" owner ",$,$,"
                       (reflist @contained) ",#" storey ")")))
    (doseq [[e ps eid] @rel-psets]
      (ifc-add! f (str "IFCRELDEFINESBYPROPERTIES('" (ifc-guid (str "rdp-" eid)) "',#" owner ",$,$,"
                       "(#" e "),#" ps ")")))
    (let [body (str/join "\n" (:lines @f))
          header (str "ISO-10303-21;\n"
                      "HEADER;\n"
                      "FILE_DESCRIPTION(('ViewDefinition [ReferenceView_V1.2]'),'2;1');\n"
                      "FILE_NAME('factory.ifc','2026-05-31T00:00:00',('etzhayyim'),('etzhayyim'),"
                      "'kotoba-sarutahiko-factory','kami-app-sarutahiko-factory','');\n"
                      "FILE_SCHEMA(('IFC4'));\n"
                      "ENDSEC;\n"
                      "DATA;\n")
          footer "\nENDSEC;\nEND-ISO-10303-21;\n"]
      #?(:clj (when path (spit (str path) (str header body footer))))
      {"entities" (:n @f) "elements" (count @contained) "psets" (count @rel-psets)})))

#?(:clj
   (defn read-scene-json
     "Decode the string-keyed scene document with the declared host codec."
     [text]
     (json/parse-string text)))

#?(:clj
   (defn -main
     "Faithful port of the Python main(): read factory.scene.json (JSON) +
     building.edn, export factory.ifc, print a summary."
     [& _args]
     (let [here (str (.getParent (java.io.File. (str *file*))))
           scene (read-scene-json (slurp (str here "/factory.scene.json")))
           ;; building.edn parsed by the sibling sbom-gen EDN reader if loadable,
           ;; else clojure.edn (the file is plain EDN data).
           doc (clojure.edn/read-string (slurp (str here "/building.edn")))
           parts (get doc "bom/parts")
           res (export-ifc scene parts (str here "/factory.ifc"))]
       (println (str "wrote factory.ifc — " (get res "entities") " STEP entities, "
                     (get res "elements") " elements, " (get res "psets") " property sets")))))
