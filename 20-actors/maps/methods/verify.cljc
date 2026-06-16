(ns maps.methods.verify
  "verify.py — kotoba read-surface readiness verifier (ADR-2606064500 R1).
  1:1 Clojure port of `methods/verify.py`.

  The operator readiness check for the R1 cut-over: confirm ALL four kotoba-native reads return
  (chunk · search · reverse · transit). Fail-soft: each read degrades to ok=false (never raises).

  _ring-cells needs h3 (absent on this host → []), so chunk reports h3-unavailable, exactly like
  the Python except-branch. The __main__ CLI/stdout printing is omitted."
  (:require [maps.methods.chunk :as chunk]
            [maps.methods.search :as search]
            [maps.methods.reverse :as reverse]
            [maps.methods.transit :as transit]))

;; Tokyo Station anchor — the maps-3d walkable default.
(def default-params {"lat" 35.6812 "lon" 139.7671 "res" 10 "ring" 2
                     "query" "tok" "stop_id" "f.station.tokyo"})

(defn- ring-cells
  "h3 grid_disk around the point; [] when h3 is unavailable (this host)."
  [_lat _lon _res _ring]
  [])

(defn verify-reads
  "Returns { chunk:{ok,count}, search:{ok,count}, reverse:{ok,nearest}, transit:{ok,count}, allOk }."
  ([endpoint opts]
   (let [{:keys [lat lon res ring query stop-id] :or {res 10 ring 2 query "" stop-id ""}} opts
         cells (ring-cells lat lon res ring)
         ch (if (seq cells) (chunk/get-chunk endpoint cells res) {"total" 0})
         chunk-rep {"ok" (> (get ch "total" 0) 0) "count" (get ch "total" 0)
                    "note" (if (seq cells) nil "h3 unavailable — cannot probe cells")}
         sr (if (seq query) (search/search-places endpoint query) [])
         search-rep {"ok" (> (count sr) 0) "count" (count sr)}
         rg (reverse/reverse-geocode endpoint lat lon {:res res :ring ring})
         reverse-rep {"ok" (> (count rg) 0) "nearest" (when (seq rg) (get (first rg) "id"))}
         td (if (seq stop-id) (transit/next-departures-at-stop endpoint stop-id) [])
         transit-rep {"ok" (> (count td) 0) "count" (count td)}
         report {"chunk" chunk-rep "search" search-rep "reverse" reverse-rep "transit" transit-rep}
         all-ok (every? (fn [[_ v]] (get v "ok")) report)]
     (assoc report "allOk" all-ok))))
