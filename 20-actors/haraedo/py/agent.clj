#!/usr/bin/env bb
;; Working Clojure port of py/agent.py (haraedo bulky-waste disposal actor).
(ns haraedo.py.agent
  "haraedo 祓戸 — bulky-waste disposal langgraph actor (kotoba WASM cell).

  ADR-2606010200. Runs in-WASM on kotoba :8077. Two graphs over one kotoba EAVT graph.

  Run:  bb --classpath 20-actors 20-actors/haraedo/py/agent.clj"
  (:require [clojure.string :as str]))

;; ── rebindable kotoba datalog seam ───────────────────────────────────────────
;; Tests rebind with (binding [*datalog* fake-dl] ...).
;; A fake-dl is a map {:q (fn [query & args] ...) :transact (fn [datoms] ...)}.
(def ^:dynamic *datalog* nil)

;; ── helpers ───────────────────────────────────────────────────────────────────

(defn haversine-km
  "Great-circle distance in km (R0)."
  ^double [a-lat a-lon b-lat b-lon]
  (let [r    6371.0
        p1   (Math/toRadians a-lat)
        p2   (Math/toRadians b-lat)
        dphi (Math/toRadians (- b-lat a-lat))
        dlmb (Math/toRadians (- b-lon a-lon))
        h    (+ (* (Math/sin (/ dphi 2)) (Math/sin (/ dphi 2)))
                (* (Math/cos p1) (Math/cos p2)
                   (Math/sin (/ dlmb 2)) (Math/sin (/ dlmb 2))))]
    (* 2.0 r (Math/asin (Math/sqrt h)))))

(defn route-length
  "Total tour length from start ([lat lon]) through order (seq of point ids)."
  ^double [order coords start]
  (loop [total 0.0 cur start pts order]
    (if (empty? pts)
      total
      (let [pid (first pts)
            nxt (get coords pid)]
        (recur (+ total (haversine-km (first cur) (second cur) (first nxt) (second nxt)))
               nxt (rest pts))))))

(defn nearest-neighbour
  "Greedy NN tour over point ids starting nearest to start ([lat lon])."
  [points coords start]
  (loop [remaining (vec points) order [] cur start]
    (if (empty? remaining)
      order
      (let [nxt (apply min-key
                       (fn [p]
                         (let [c (get coords p)]
                           (haversine-km (first cur) (second cur) (first c) (second c))))
                       remaining)]
        (recur (filterv #(not= % nxt) remaining)
               (conj order nxt)
               (get coords nxt))))))

(defn two-opt
  "2-opt local search. Improvement test: cand_len + 1e-9 < best_len (epsilon, mirrors py)."
  [order coords start]
  (loop [best (vec order) best-len (route-length order coords start)]
    (let [n (count best)
          result
          (loop [i 0 best best best-len best-len improved false]
            (if (>= i (dec n))
              [best best-len improved]
              (let [[best best-len improved]
                    (loop [k (inc i) best best best-len best-len improved improved]
                      (if (>= k n)
                        [best best-len improved]
                        (let [cand     (vec (concat (subvec best 0 i)
                                                    (rseq (subvec best i (inc k)))
                                                    (subvec best (inc k))))
                              cand-len (route-length cand coords start)]
                          (if (< (+ cand-len 1e-9) best-len)
                            (recur (inc k) cand cand-len true)
                            (recur (inc k) best best-len improved)))))]
                (recur (inc i) best best-len improved))))]
      (let [[best2 best-len2 improved?] result]
        (if improved? (recur best2 best-len2) [best2 best-len2])))))

(defn or-opt
  "Or-opt: relocate chains of length 1..3. Breaks out of seg loop on first improvement."
  [order coords start]
  (loop [best (vec order) best-len (route-length order coords start)]
    (let [n (count best)
          [best2 best-len2 improved?]
          (loop [seg 1 best best best-len best-len improved false]
            (if (or (> seg 3) (>= seg n))
              [best best-len improved]
              (let [[best best-len improved]
                    (loop [i 0 best best best-len best-len improved improved]
                      (if (> i (- n seg))
                        [best best-len improved]
                        (let [chain (subvec best i (+ i seg))
                              rest- (vec (concat (subvec best 0 i) (subvec best (+ i seg))))
                              rlen  (count rest-)
                              [best best-len improved]
                              (loop [j 0 best best best-len best-len improved improved]
                                (if (> j rlen)
                                  [best best-len improved]
                                  (let [cand     (vec (concat (subvec rest- 0 j) chain (subvec rest- j)))
                                        cand-len (route-length cand coords start)]
                                    (if (< (+ cand-len 1e-9) best-len)
                                      (recur (inc j) cand cand-len true)
                                      (recur (inc j) best best-len improved)))))]
                          (recur (inc i) best best-len improved))))]
                (if improved
                  [best best-len true]
                  (recur (inc seg) best best-len false)))))]
      (if improved? (recur best2 best-len2) [best2 best-len2]))))

(defn local-search
  "R2 route polish: alternate 2-opt and Or-opt until neither improves."
  [order coords start]
  (let [cur-len (route-length order coords start)]
    (loop [cur (vec order) cur-len cur-len]
      (let [[cur2 _]       (two-opt cur coords start)
            [cur3 new-len] (or-opt cur2 coords start)]
        (if (>= (+ new-len 1e-9) cur-len)
          [cur3 new-len]
          (recur cur3 new-len))))))

(defn route-eta
  "VRPTW arrival clock (R2). Returns list of [stop-id eta-min] pairs."
  [order coords depot & {:keys [start-min speed-kmh service-min]
                         :or   {start-min 480 speed-kmh 20.0 service-min 10}}]
  (loop [etas [] cur depot t (double start-min) pts order]
    (if (empty? pts)
      etas
      (let [s   (first pts)
            nxt (get coords s)
            t2  (+ t (* (/ (haversine-km (first cur) (second cur) (first nxt) (second nxt))
                           speed-kmh) 60.0))
            eta (/ (Math/round (* t2 10.0)) 10.0)]
        (recur (conj etas [s eta]) nxt (+ t2 (double service-min)) (rest pts))))))

(defn clarke-wright
  "Capacitated VRP (Clarke-Wright savings) → list of capacity-feasible routes."
  [stops demand coords depot cap]
  (if (empty? stops)
    []
    (let [stops  (vec stops)
          dij    (fn [a b]
                   (haversine-km (first (get coords a)) (second (get coords a))
                                 (first (get coords b)) (second (get coords b))))
          ddep   (fn [a]
                   (haversine-km (first depot) (second depot)
                                 (first (get coords a)) (second (get coords a))))
          rload  (fn [r] (reduce + 0 (map #(get demand % 0) r)))
          routes (atom (mapv vector stops))
          savings (sort-by (fn [[s _ _]] (- s))
                            (for [i (range (count stops))
                                  j (range (inc i) (count stops))
                                  :let [a (stops i) b (stops j)]]
                              [(+ (ddep a) (ddep b) (- (dij a b))) a b]))
          find-r  (fn [x] (first (filter #(some #{x} %) @routes)))]
      (doseq [[_ a b] savings]
        (let [ra (find-r a) rb (find-r b)]
          (when (and ra rb (not= ra rb))
            (when (and (some #{a} [(first ra) (last ra)])
                       (some #{b} [(first rb) (last rb)]))
              (when (<= (+ (rload ra) (rload rb)) cap)
                (let [ra2 (if (= (first ra) a) (vec (reverse ra)) ra)
                      rb2 (if (= (last rb) b)  (vec (reverse rb)) rb)
                      merged (vec (concat ra2 rb2))]
                  (swap! routes (fn [rs]
                                  (conj (filterv #(and (not= % ra) (not= % rb)) rs)
                                        merged)))))))))
      (mapv (fn [r] (first (local-search r coords depot))) @routes))))

;; ── kotoba entity-attribute helpers ──────────────────────────────────────────

(defn- dl-q
  "Invoke :q on *datalog* (a map with :q fn), return rows."
  [query & args]
  (when *datalog*
    (apply (:q *datalog*) query args)))

(defn- q1 [query & args]
  (let [rows (apply dl-q query args)]
    (when (and rows (seq rows)) (first (first rows)))))

(defn- dl-transact [datoms]
  (when *datalog*
    ((:transact *datalog*) datoms)))

(defn- attr [id-attr id-val attr-name]
  (q1 (str "[:find ?v :in $ ?k :where [?e :" id-attr " ?k] [?e :" attr-name " ?v]]") id-val))

(defn- to-int
  ([v] (to-int v 0))
  ([v default]
   (try (long (double v))
        (catch Exception _ default))))

;; ── intake graph (citizen side) ───────────────────────────────────────────────

(defn classify-node
  "G3 hazardous-boundary: split items into accepted vs licensed-handler."
  [state]
  (let [items (get state "items" [])]
    (reduce (fn [{:strs [accepted_items rejected_items]} code]
              (let [hazardous
                    (if *datalog*
                      (boolean
                       (let [rows (dl-q "[:find ?h :in $ ?c :where [?e :item-category/code ?c] [?e :item-category/hazardous ?h]]" code)]
                         (and (seq rows) (first (first rows)))))
                      false)]
                (if hazardous
                  {"accepted_items" accepted_items "rejected_items" (conj rejected_items code)}
                  {"accepted_items" (conj accepted_items code) "rejected_items" rejected_items})))
            {"accepted_items" [] "rejected_items" []}
            items)))

(defn quote-node
  "Quote fee per the jurisdiction's fee model (R1, G14)."
  [state]
  (if (nil? *datalog*)
    {"fee" 0}
    (let [juris (get state "jurisdiction" "")
          items (get state "accepted_items" [])
          model (-> (or (attr "jurisdiction/id" juris "jurisdiction/bulky-fee-model") "")
                    (str/replace #"^:" ""))
          fee   (cond
                  (= model "free")
                  0
                  (= model "per-sticker")
                  (* (count items) (to-int (attr "jurisdiction/id" juris "jurisdiction/fee-per-sticker")))
                  (= model "per-weight")
                  (let [kg (reduce + 0 (map #(to-int (attr "item-category/code" % "item-category/est-weight-kg")) items))]
                    (* kg (to-int (attr "jurisdiction/id" juris "jurisdiction/fee-per-kg"))))
                  (= model "flat")
                  (to-int (attr "jurisdiction/id" juris "jurisdiction/fee-flat"))
                  :else
                  (reduce + 0 (map #(to-int (attr "item-category/code" % "item-category/base-fee")) items)))]
      {"fee" fee})))

(defn match-facility-node
  "G14/G15: choose a facility in-jurisdiction that accepts all items & has capacity."
  [state]
  (if (nil? *datalog*)
    {"facility" ""}
    (let [facs (dl-q "[:find ?id ?cap ?load :in $ ?j :where [?f :facility/jurisdiction ?j] [?f :facility/id ?id] [?f :facility/capacity-tonnes-day ?cap] [?f :facility/load-tonnes-today ?load]]"
                     (get state "jurisdiction"))]
      (or (some (fn [[fid cap load]]
                  (let [accepts    (dl-q "[:find ?cat :in $ ?id :where [?f :facility/id ?id] [?f :facility/accepted-categories ?cat]]" fid)
                        accepted-s (set (map first accepts))]
                    (when (and (> cap load)
                               (every? #(contains? accepted-s %) (get state "accepted_items" [])))
                      {"facility" fid})))
                facs)
          {"facility" ""}))))

(defn schedule-node
  "Resolve + book the earliest open collection slot (R1, G15 capacity-honest)."
  [state]
  (if (nil? *datalog*)
    {"scheduled_date" (get state "scheduled_date" "") "slot_id" ""}
    (let [area    (attr "collection-point/id" (get state "collection_point") "collection-point/service-area")
          desired (or (get state "scheduled_date") "")
          rows    (dl-q "[:find ?id ?date ?cap ?booked ?win :in $ ?j ?a :where [?s :slot/jurisdiction ?j] [?s :slot/service-area ?a] [?s :slot/id ?id] [?s :slot/date ?date] [?s :slot/capacity ?cap] [?s :slot/booked ?booked] [?s :slot/window ?win]]"
                        (get state "jurisdiction") area)
          winrank {":am" 0 "am" 0 ":allday" 0 "allday" 0 ":pm" 1 "pm" 1}
          cand    (sort (for [[sid d cap b w] rows
                              :let [bi (to-int b) ci (to-int cap)]
                              :when (and (< bi ci) (or (empty? desired) (>= (compare d desired) 0)))]
                          [d (get winrank (str w) 2) sid bi]))]
      (if (empty? cand)
        {"scheduled_date" "" "slot_id" ""}
        (let [[d _ sid booked] (first cand)]
          (dl-transact [{":slot/id" sid ":slot/booked" (inc booked)}])
          {"scheduled_date" d "slot_id" sid})))))

(defn sticker-node
  "Issue a deterministic sticker id and persist the application (G1 consent required)."
  [state]
  (if (not (seq (get state "consent_sig")))
    {"sticker_id" ""}
    (let [juris-parts (str/split (get state "jurisdiction" "") #"\.")
          juris       (str/upper-case (subs (last juris-parts) 0 (min 3 (count (last juris-parts)))))
          date        (str/replace (or (get state "scheduled_date") "") "-" "")
          member      (get state "member_did" "")
          sticker     (format "%s-%s-%05d" juris date (mod (Math/abs (.hashCode ^String member)) 100000))]
      (when *datalog*
        (let [app-id (str (get state "jurisdiction") ".app." date "-" sticker)]
          (dl-transact [{":application/id"               app-id
                         ":application/member-did"       member
                         ":application/jurisdiction"     (get state "jurisdiction")
                         ":application/items"            (vec (get state "accepted_items" []))
                         ":application/collection-point" (get state "collection_point")
                         ":application/scheduled-date"   (get state "scheduled_date" "")
                         ":application/fee"              (get state "fee")
                         ":application/sticker-id"       sticker
                         ":application/consent-sig"      (get state "consent_sig")
                         ":application/slot-id"          (get state "slot_id" "")
                         ":application/state"            ":scheduled"}])))
      {"sticker_id" sticker})))

;; ── dispatch graph (operator side) ────────────────────────────────────────────

(defn gather-node
  "Gather scheduled applications for jurisdiction + date."
  [state]
  (if (nil? *datalog*)
    {"applications" []}
    (let [rows (dl-q "[:find ?id ?cp :in $ ?j ?d :where [?a :application/jurisdiction ?j] [?a :application/scheduled-date ?d] [?a :application/id ?id] [?a :application/collection-point ?cp]]"
                     (get state "jurisdiction") (get state "date"))]
      {"applications" (mapv (fn [[aid cp]] {"app_id" aid "collection_point" cp}) rows)})))

(defn cluster-node
  "Cluster stops; load coordinates + per-stop demand (kg) + time windows (R2 VRPTW)."
  [state]
  (let [coords    (atom {})
        demand    (atom {})
        window-of (atom {})
        load-kg   (atom 0)]
    (when *datalog*
      (doseq [app (get state "applications" [])]
        (let [cp (get app "collection_point")]
          (let [rows (dl-q "[:find ?lat ?lon :in $ ?cp :where [?p :collection-point/id ?cp] [?p :collection-point/lat ?lat] [?p :collection-point/lon ?lon]]" cp)]
            (when (seq rows)
              (swap! coords assoc cp [(first (first rows)) (second (first rows))])))
          (let [items (dl-q "[:find ?w :in $ ?aid :where [?a :application/id ?aid] [?a :application/items ?c] [?e :item-category/code ?c] [?e :item-category/est-weight-kg ?w]]"
                             (get app "app_id"))
                kg    (long (reduce + 0 (map first items)))]
            (swap! demand update cp (fnil + 0) kg)
            (swap! load-kg + kg))
          (let [srow (dl-q "[:find ?win ?ws ?we :in $ ?aid :where [?a :application/id ?aid] [?a :application/slot-id ?sid] [?s :slot/id ?sid] [?s :slot/window ?win] [?s :slot/window-start ?ws] [?s :slot/window-end ?we]]"
                            (get app "app_id"))]
            (when (seq srow)
              (swap! window-of assoc cp {"window" (str (first (first srow)))
                                         "start"  (int (second (first srow)))
                                         "end"    (int (nth (first srow) 2))}))))))
    {"coords" @coords "demand" @demand "window_of" @window-of "load_kg" @load-kg}))

(defn build-routes-node
  "R1 capacitated multi-vehicle plan (Clarke-Wright VRP + R3 inter-window reuse).
  Routes with no feasible vehicle go to unassigned (G15)."
  [state]
  (let [coords   (get state "coords" {})
        demand   (get state "demand" {})
        stops    (vec (keys coords))]
    (if (empty? stops)
      {"routes" [] "unassigned" []}
      (let [vehs      (atom [])
            depot     (atom [35.66 139.70])
            facility  (atom "")
            drivers   (atom [])
            loaders   (atom [])]
        (when *datalog*
          (let [raw (dl-q "[:find ?id ?cap :in $ ?j :where [?v :vehicle/jurisdiction ?j] [?v :vehicle/status :available] [?v :vehicle/id ?id] [?v :vehicle/capacity-kg ?cap]]"
                           (get state "jurisdiction"))]
            (reset! vehs (sort-by first (mapv (fn [[vid c]] [(to-int c) vid]) raw))))
          (when (seq @vehs)
            (let [d (dl-q "[:find ?lat ?lon :in $ ?v :where [?x :vehicle/id ?v] [?x :vehicle/depot-lat ?lat] [?x :vehicle/depot-lon ?lon]]"
                           (second (first @vehs)))]
              (when (seq d) (reset! depot [(first (first d)) (second (first d))]))))
          (let [facs  (dl-q "[:find ?id ?cap ?load :in $ ?j :where [?f :facility/jurisdiction ?j] [?f :facility/id ?id] [?f :facility/capacity-tonnes-day ?cap] [?f :facility/load-tonnes-today ?load]]"
                              (get state "jurisdiction"))
                spare (filterv (fn [[_ cap load]] (> cap load)) facs)]
            (reset! facility (if (seq spare) (first (first spare)) "")))
          (let [crew (dl-q "[:find ?id ?role :in $ ?j :where [?c :crew/jurisdiction ?j] [?c :crew/shift :early] [?c :crew/id ?id] [?c :crew/role ?role]]"
                             (get state "jurisdiction"))]
            (reset! drivers (mapv first (filterv #(let [r (second %)] (or (= r ":driver") (= r "driver"))) crew)))
            (reset! loaders (mapv first (filterv #(let [r (second %)] (or (= r ":loader") (= r "loader"))) crew)))))
        (let [cap       (if (seq @vehs) (first (last @vehs)) 4000)
              window-of (get state "window_of" {})
              speed     20.0 service 10
              groups    (reduce (fn [g s]
                                  (let [w (get window-of s {"window" "allday" "start" 480 "end" 1020})]
                                    (update g [(get w "window") (get w "start") (get w "end")]
                                            (fnil conj []) s)))
                                {} stops)
              pool      (atom (mapv (fn [[c vid]] {"cap" c "vid" vid "free_at" Double/NEGATIVE_INFINITY}) @vehs))
              routes    (atom [])
              unassigned (atom [])]
          (doseq [[[win w-start w-end] gstops]
                  (sort-by (fn [[[_ ws _] _]] ws) groups)]
            (doseq [order (clarke-wright gstops demand coords @depot cap)]
              (let [load (reduce + 0 (map #(get demand % 0) order))
                    cand (first (filter (fn [p] (and (>= (get p "cap") load)
                                                      (<= (get p "free_at") w-start)))
                                        @pool))]
                (if (nil? cand)
                  (swap! unassigned conj {"stop_order" order "load_kg" (int load) "window" win
                                           "reason" "no vehicle free (capacity ≥ load AND back by window start) — G15"})
                  (let [reused    (> (get cand "free_at") Double/NEGATIVE_INFINITY)
                        etas      (route-eta order coords @depot :start-min w-start :speed-kmh speed :service-min service)
                        ret-min   (if (seq order)
                                    (* (/ (haversine-km (first (get coords (last order)))
                                                         (second (get coords (last order)))
                                                         (first @depot) (second @depot))
                                           speed) 60.0)
                                    0.0)
                        last-eta  (if (seq etas) (second (last etas)) (double w-start))
                        free-at   (+ last-eta service ret-min)
                        d         (if (seq @drivers) [(first @drivers)] [])
                        _         (when (seq @drivers) (swap! drivers rest))
                        l         (vec (take 2 @loaders))
                        _         (swap! loaders #(drop 2 %))
                        crewset   (vec (concat d l))
                        tw-viols  (filterv (fn [[_ e]] (> e w-end)) etas)]
                    (swap! pool (fn [p] (mapv #(if (= (get % "vid") (get cand "vid"))
                                                 (assoc % "free_at" free-at) %) p)))
                    (swap! routes conj
                           {"vehicle"        (get cand "vid")
                            "stop_order"     order
                            "load_kg"        (int load)
                            "distance_km"    (/ (Math/round (* (route-length order coords @depot) 100.0)) 100.0)
                            "facility"       @facility
                            "crew"           crewset
                            "window"         win
                            "window_start"   w-start
                            "window_end"     w-end
                            "etas"           etas
                            "tw_violations"  (mapv (fn [[s e]] {"stop" s "eta_min" e}) tw-viols)
                            "vehicle_reused" reused}))))))
          {"routes" @routes "unassigned" @unassigned})))))

(defn assign-vehicle-node
  "G15: pick smallest available vehicle whose capacity covers the load."
  [state]
  (if (nil? *datalog*)
    {"vehicle" ""}
    (let [vehs    (dl-q "[:find ?id ?cap :in $ ?j :where [?v :vehicle/jurisdiction ?j] [?v :vehicle/status :available] [?v :vehicle/id ?id] [?v :vehicle/capacity-kg ?cap]]"
                        (get state "jurisdiction"))
          load-kg (get state "load_kg" 0)
          feasible (sort-by first (filterv (fn [[c _]] (>= (to-int c) load-kg)) (mapv (fn [[vid c]] [(to-int c) vid]) vehs)))]
      {"vehicle" (if (seq feasible) (second (first feasible)) "")})))

(defn assign-crew-node
  "Assign one driver + loaders on the early shift (G5 labor-dignity)."
  [state]
  (if (nil? *datalog*)
    {"crew" []}
    (let [crew    (dl-q "[:find ?id ?role :in $ ?j :where [?c :crew/jurisdiction ?j] [?c :crew/shift :early] [?c :crew/id ?id] [?c :crew/role ?role]]"
                         (get state "jurisdiction"))
          drivers (mapv first (filterv #(let [r (second %)] (or (= r ":driver") (= r "driver"))) crew))
          loaders (mapv first (filterv #(let [r (second %)] (or (= r ":loader") (= r "loader"))) crew))
          assigned (if (seq drivers)
                     (vec (concat (take 1 drivers) (take 2 loaders)))
                     (vec (take 2 loaders)))]
      {"crew" assigned})))

(defn optimize-route-node
  "NN + 2-opt over collection points, starting from the vehicle depot."
  [state]
  (let [coords (get state "coords" {})
        points (vec (keys coords))]
    (if (empty? points)
      {"stop_order" [] "distance_km" 0.0}
      (let [start (atom [35.66 139.70])]
        (when (and *datalog* (get state "vehicle"))
          (let [d (dl-q "[:find ?lat ?lon :in $ ?v :where [?x :vehicle/id ?v] [?x :vehicle/depot-lat ?lat] [?x :vehicle/depot-lon ?lon]]"
                        (get state "vehicle"))]
            (when (seq d) (reset! start [(first (first d)) (second (first d))]))))
        (let [nn            (nearest-neighbour points coords @start)
              [order length] (two-opt nn coords @start)]
          {"stop_order"  order
           "distance_km" (/ (Math/round (* length 100.0)) 100.0)})))))

(defn select-facility-node
  "G14/G15: destination facility with spare capacity accepting the loads."
  [state]
  (if (nil? *datalog*)
    {"facility" ""}
    (let [facs  (dl-q "[:find ?id ?cap ?load :in $ ?j :where [?f :facility/jurisdiction ?j] [?f :facility/id ?id] [?f :facility/capacity-tonnes-day ?cap] [?f :facility/load-tonnes-today ?load]]"
                       (get state "jurisdiction"))
          spare (filterv (fn [[_ cap load]] (> cap load)) facs)]
      {"facility" (if (seq spare) (first (first spare)) "")})))

(defn emit-plan-node
  "Persist every capacitated route to kotoba (state :planned — G11 design-only)."
  [state]
  (let [area         (get state "service_area" "all")
        date-compact (str/replace (get state "date" "") "-" "")
        written      (atom [])]
    (doseq [[n r] (map-indexed #(vector (inc %1) %2) (get state "routes" []))]
      (let [rid (format "%s.route.%s-%s-%02d" (get state "jurisdiction") date-compact area n)]
        (when (and *datalog* (get r "vehicle"))
          (dl-transact [{":route/id"                  rid
                          ":route/jurisdiction"        (get state "jurisdiction")
                          ":route/date"                (get state "date")
                          ":route/vehicle"             (get r "vehicle")
                          ":route/crew"                (vec (get r "crew" []))
                          ":route/stops"               (vec (get r "stop_order" []))
                          ":route/stop-order"          (pr-str (get r "stop_order" []))
                          ":route/facility-destination" (get r "facility")
                          ":route/distance-km"         (get r "distance_km")
                          ":route/load-kg"             (int (get r "load_kg" 0))
                          ":route/window"              (str ":" (get r "window" "allday"))
                          ":route/state"               ":planned"}]))
        (swap! written conj (merge r {"route_id" rid "state" ":planned"}))))
    {"plan" {"routes" @written "unassigned" (get state "unassigned" [])}}))

;; ── handlers ─────────────────────────────────────────────────────────────────

(defn handle-intake [event]
  (-> event
      (#(merge % (classify-node %)))
      (#(merge % (quote-node %)))
      (#(merge % (match-facility-node %)))
      (#(merge % (schedule-node %)))
      (#(merge % (sticker-node %)))))

(defn handle-dispatch [event]
  (-> event
      (#(merge % (gather-node %)))
      (#(merge % (cluster-node %)))
      (#(merge % (build-routes-node %)))
      (#(merge % (emit-plan-node %)))))

(defn handle [event]
  (if (= (get event "kind") "dispatch")
    (handle-dispatch event)
    (handle-intake event)))

(defn -main [& _]
  (println "intake:" (handle-intake {"member_did"       "did:web:example"
                                      "consent_sig"      "sig"
                                      "jurisdiction"     "jp.shibuya"
                                      "items"            ["furniture" "bedding"]
                                      "collection_point" "jp.shibuya.cp.udagawa-1"
                                      "scheduled_date"   "2026-06-05"}))
  (println "dispatch:" (handle-dispatch {"kind"         "dispatch"
                                          "jurisdiction" "jp.shibuya"
                                          "date"         "2026-06-05"
                                          "service_area" "shibuya-north"})))

(when (= *file* (System/getProperty "babashka.file"))
  (-main))
