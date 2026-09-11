;; ported from 20-actors/maps/methods/transit.py — gold reference (Fable)
;; maps — kotoba-native transit reads (ADR-2606064500 R2 aux)。
;; legacy RisingWave reads の kotoba-native 後継: 各クエリは Datom log への単一 AVET probe + client-side sort。
;;   next-departures-at-stop: AVET(:transit.stop-time/stop, stop-id) → filter dep≥after → sort → top N。
;;   trips-on-route:          AVET(:transit.trip/route, route-id) → trips。
;; GTFS departure_time は 24:00:00 超 (past-midnight) があり得るが、テキストのまま service-day 内で
;; 正しくソートされる。Fail-soft: any error → 空 list。
;;
;; HTTP/JSON は host capability 注入 (caps {:http-fn :json-write :json-read})。
(ns maps.methods.transit
  (:require [clojure.string :as str]))

(def query-nsid "com.etzhayyim.apps.kotoba.graph.sparql")

(defn- avet
  "AVET predicate+object probe 1 回 → entity map の列 {:id :claims [{:pred :value}…]}。"
  [caps endpoint predicate objects limit]
  (let [{:keys [http-fn json-write json-read]} caps
        body (json-write {:index "avet" :predicate predicate
                          :objects (vec objects) :limit limit})]
    (try
      (let [resp (http-fn {:url (str (str/replace endpoint #"/+$" "")
                                     "/xrpc/" query-nsid)
                           :method :post
                           :headers {"content-type" "application/json"}
                           :body body})]
        (if (= 200 (:status resp))
          (:entities (json-read (:body resp)) [])
          []))
      (catch Exception _ []))))

(defn- claims
  "entity の :claims を {pred value} map へ。"
  [entity]
  (into {} (for [c (:claims entity) :when (:pred c)] [(:pred c) (:value c)])))

(defn next-departures-at-stop
  "stop での次の発車を departure-time 昇順で。after 以降のみ、top limit 件。"
  [caps endpoint stop-id & {:keys [after limit] :or {after "00:00:00" limit 10}}]
  (->> (avet caps endpoint "transit.stop-time/stop" [stop-id] 2000)
       (keep (fn [e]
               (let [c (claims e)
                     dep (get c "transit.stop-time/departure-time")]
                 (when (and dep (>= (compare dep after) 0))
                   {:stop-time (:id e)
                    :trip (get c "transit.stop-time/trip")
                    :departure dep
                    :arrival (get c "transit.stop-time/arrival-time")
                    :headsign (get c "transit.stop-time/headsign")
                    :sequence (get c "transit.stop-time/sequence")}))))
       (sort-by :departure)                          ; text sort は service-day 内で正しい
       (take limit)
       vec))

(defn trips-on-route
  "route 上の全 trip。"
  [caps endpoint route-id & {:keys [limit] :or {limit 2000}}]
  (->> (avet caps endpoint "transit.trip/route" [route-id] limit)
       (mapv (fn [e]
               (let [c (claims e)]
                 {:trip (:id e)
                  :headsign (get c "transit.trip/headsign")
                  :service (get c "transit.trip/service")
                  :direction (get c "transit.trip/direction")})))))
