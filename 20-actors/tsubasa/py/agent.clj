#!/usr/bin/env bb
;; tsubasa 翼 — flight discovery commons langgraph actor (kotoba WASM cell).
;;
;; ADR-2606072802. The Skyscanner inversion. Honest fare/route meta-search; every
;; onward link is affiliate-stripped and the member self-books on the airline's own
;; site (no inflow). Handlers over one kotoba EAVT graph:
;;
;;   search-fares      query → honest ranked options (total cost + emissions SURFACED, G4)
;;   compare           cheapest / greenest / fastest — emissions is a first-class axis
;;   self-book-handoff affiliate-stripped handoff to the airline's OWN page (G1)
;;
;; Hard invariants:
;;   - no-affiliate-no-inflow (G1): strip-affiliate removes tracking/affiliate params
;;   - emissions-honest (G4): every result carries co2Kg; compare exposes greenest
;;   - anti-dark (G3): no urgency / "price will rise" / scarcity field
;;   - no-person-tracking (G5): search takes query + fares only, nothing about searcher
;;
;; Run: bb --classpath 20-actors 20-actors/tsubasa/py/agent.clj
(ns tsubasa.py.agent
  (:require [clojure.string :as str])
  (:import [java.net URI]))

;; ── Affiliate / tracking params stripped from onward airline links (G1) ──────
;; Mirrors _AFFILIATE_PARAMS in agent.py exactly.
(def ^:private affiliate-params
  #{"aff" "affid" "affiliate" "partner" "partner_id" "clickid" "click_id" "subid"
    "tag" "ref" "referrer" "gclid" "fbclid" "msclkid" "irclickid" "ranmid" "siteid"})

;; Mirrors _AFFILIATE_PREFIXES in agent.py exactly.
(def ^:private affiliate-prefixes
  ["utm_" "aff_" "pk_"])

;; ── URL helpers for strip-affiliate (verbatim from okaimono pattern) ─────────
(defn- parse-query-pairs
  "Parse a query string into an ordered vector of [k v] string pairs.
  Preserves order; keeps blank values (mirrors Python parse_qsl keep_blank_values=True)."
  [query-str]
  (if (or (nil? query-str) (empty? query-str))
    []
    (mapv (fn [kv]
            (let [eq (.indexOf kv "=")]
              (if (neg? eq)
                [kv ""]
                [(.substring kv 0 eq) (.substring kv (inc eq))])))
          (str/split query-str #"&"))))

(defn- encode-pairs
  "Re-encode kept [k v] pairs as k=v&k2=v2 (mirrors Python urlencode default)."
  [pairs]
  (str/join "&" (map (fn [[k v]] (str k "=" v)) pairs)))

(defn- affiliate-param?
  "True when a query-param key should be stripped (exact set match OR prefix match)."
  [k]
  (let [kl (str/lower-case k)]
    (or (contains? affiliate-params kl)
        (some #(str/starts-with? kl %) affiliate-prefixes))))

(defn strip-affiliate
  "Remove affiliate + tracking parameters from an airline URL (G1) — tsubasa earns no
  referral. Functional params (flight, date, cabin) are preserved; order is kept stable.
  Mirrors Python urllib: urlsplit → parse_qsl → filter → urlencode → urlunsplit."
  [url]
  (if (or (nil? url) (empty? url))
    url
    (let [uri      (URI. url)
          scheme   (.getScheme uri)
          host     (.getHost uri)
          port     (.getPort uri)
          netloc   (if (pos? port) (str host ":" port) host)
          raw-path (.getPath uri)
          raw-q    (.getRawQuery uri)
          kept-q   (filterv (fn [[k _]] (not (affiliate-param? k)))
                             (parse-query-pairs raw-q))
          q-str    (encode-pairs kept-q)]
      (str scheme "://" netloc raw-path (when (seq q-str) (str "?" q-str))))))

;; ── total-cost-minor ─────────────────────────────────────────────────────────
(defn total-cost-minor
  "True total cost a traveller pays: base fare + checked-bag fee (G4 honesty —
  never just the headline fare)."
  [fare]
  (+ (int (get fare :fareMinor (get fare "fareMinor" 0)))
     (int (get fare :baggageMinor (get fare "baggageMinor" 0)))))

;; ── _SORTS equivalent ────────────────────────────────────────────────────────
(def ^:private sorts
  {"total"     total-cost-minor
   "emissions" (fn [f] (double (get f :co2Kg (get f "co2Kg" 0.0))))
   "duration"  (fn [f] (int (get f :durationMin (get f "durationMin" 0))))})

;; ── search-fares ─────────────────────────────────────────────────────────────
(defn search-fares
  "Return matching fares, each annotated with totalMinor + co2Kg (G4 — emissions on
  every option), ranked by sort-key (total cost default; or emissions / duration).
  No manufactured scarcity, no per-searcher state (G3/G5). Unknown sort → total."
  ([origin destination depart-date fares]
   (search-fares origin destination depart-date fares "total"))
  ([origin destination depart-date fares sort]
   (let [key-fn (get sorts sort total-cost-minor)
         matches (for [f fares
                       :when (and (= (get f :origin (get f "origin")) origin)
                                  (= (get f :destination (get f "destination")) destination)
                                  (= (get f :departDate (get f "departDate")) depart-date))]
                   (assoc f
                          :totalMinor (total-cost-minor f)
                          :co2Kg (double (get f :co2Kg (get f "co2Kg" 0.0)))))]
     (sort-by key-fn (vec matches)))))

;; ── compare ──────────────────────────────────────────────────────────────────
(defn compare
  "Expose cheapest, greenest, and fastest options together so emissions is a
  first-class axis (G4) — a low-fare/high-CO₂ option cannot be presented while
  hiding a greener one."
  [fares]
  (if (empty? fares)
    {:cheapest nil :greenest nil :fastest nil}
    {:cheapest (apply min-key total-cost-minor fares)
     :greenest (apply min-key (fn [f] (double (get f :co2Kg (get f "co2Kg" 0.0)))) fares)
     :fastest  (apply min-key (fn [f] (int (get f :durationMin (get f "durationMin" 0)))) fares)}))

;; ── self-book-handoff ─────────────────────────────────────────────────────────
(defn self-book-handoff
  "Hand the member to the airline's OWN booking page, affiliate-stripped (G1).
  tsubasa is not the merchant-of-record: no commission, no tithe (external, no
  internal value flow), principal is the member."
  [fare]
  {:mode            "self-book-handoff"
   :principal       "member"
   :carrier         (get fare :carrier (get fare "carrier"))
   :bookUrl         (strip-affiliate (get fare :bookUrl (get fare "bookUrl" "")))
   :commissionMinor 0
   :titheMinor      0})

;; ── main ─────────────────────────────────────────────────────────────────────
(defn -main [& _args]
  (println "tsubasa 翼 agent ready — ADR-2606072802"))

(when (= *file* (System/getProperty "babashka.file"))
  (-main))
