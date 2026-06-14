;; standard.clj — matsurigoto 政 COFOG-based e-Government Service Standard loader/validator/coverage.
;;
;; Clojure port of standard.py (ADR-2606062300), Wave 1 of the clj-native migration
;; (ADR-2606142300) — the final matsurigoto module, completing the actor's clj surface. Reads
;; data/cofog-standard.kotoba.edn (the universal, spec-derived service standard on the UN COFOG
;; backbone) and (1) VALIDATES it (structural integrity + the charter invariants), (2) emits an
;; HONEST COVERAGE report. clojure.edn reads the standard + per-country profiles natively.
;;
;; Charter invariants checked here:
;;   G1 no-server-authority  — every service :invariants {:server-held-authority false}
;;   G2 spec-derived-only    — every service cites a non-empty :spec-basis ({:spec-derived true})
;;   G3 authority-separation — every profile names a legitimate :operated-by + :authority-mode;
;;                             the Kingdom's polities are Council/sovereign, adopters state/supplied.
;;
;; POSTURE: matsurigoto SUPPLIES the standard to governments; it never operates as one. stdlib only.
(ns matsurigoto.methods.standard
  (:require [clojure.edn :as edn]
            [clojure.string :as str]
            [clojure.java.io :as io]))

(def default-std "20-actors/matsurigoto/data/cofog-standard.kotoba.edn")
(def profiles-dir "20-actors/matsurigoto/data/profiles")

;; NOTE: this standard's EDN stores keyword-like enum VALUES as ":"-prefixed STRINGS
;; (":division" / ":taxation" / ":etzhayyim-council"), matching the Python _edn representation —
;; so we match strings here. Structural map KEYS and the :invariants map use real keywords/booleans.
(def required-domains #{":taxation" ":civil-registry" ":corp-registry" ":identity-credential"})
(def required-invariants {:server-held-authority false :spec-derived true})  ; G1 + G2 (real kw keys)
(def allowed-operated-by #{":etzhayyim-council" ":adopting-government"})      ; G3
(def allowed-authority-mode #{":sovereign-governance" ":supplied-to-state"}) ; G3

(defn- read-edn [f] (edn/read-string (slurp (io/file f))))

(defn load-profiles
  ([] (load-profiles profiles-dir))
  ([dir]
   (let [d (io/file dir)]
     (if-not (.exists d)
       []
       (->> (.listFiles d)
            (filter #(.endsWith (.getName %) ".edn"))
            (sort-by #(.getName %))
            (map read-edn)
            (filter map?)
            vec)))))

(defn load-standard
  "Read the standard + merge external per-country profiles (deduped by iso3; inline wins)."
  ([] (load-standard default-std))
  ([path]
   (let [doc    (read-edn path)
         _      (when-not (map? doc) (throw (ex-info "standard root must be a map" {})))
         inline (vec (:country-profiles doc))
         seen   (set (map :country-profile/iso3 inline))]
     (assoc doc :country-profiles
            (reduce (fn [acc p]
                      (if (contains? (set (map :country-profile/iso3 acc)) (:country-profile/iso3 p))
                        acc
                        (conj acc p)))
                    inline
                    (remove #(seen (:country-profile/iso3 %)) (load-profiles)))))))

(defn cofog-index [doc] (into {} (map (juxt :cofog/code identity) (:cofog doc))))
(defn module-index [doc] (into {} (map (juxt :egov.module/id identity) (:modules doc))))

(defn- validate-profile [p kind ns-pfx service-ids]
  (let [k        (fn [suffix] (keyword ns-pfx suffix))
        name     (get p (k (if (= kind "polity") "id" "iso3")) "<no-id>")
        ob       (get p (k "operated-by"))
        am       (get p (k "authority-mode"))]
    (cond-> []
      (not (allowed-operated-by ob))
      (conj (str kind " " name ": :operated-by " (pr-str ob) " not allowed"))
      (not (allowed-authority-mode am))
      (conj (str kind " " name ": :authority-mode " (pr-str am) " not allowed"))
      (and (= kind "polity") (not= [ob am] [":etzhayyim-council" ":sovereign-governance"]))
      (conj (str "polity " name ": must be :etzhayyim-council/:sovereign-governance"))
      (and (= kind "country") (not= [ob am] [":adopting-government" ":supplied-to-state"]))
      (conj (str "country " name ": must be :adopting-government/:supplied-to-state"))
      :always
      (into (for [b (get p (k "bindings")) :when (not (service-ids (:bind/service b)))]
              (str kind " " name ": binding to unknown service " (pr-str (:bind/service b))))))))

(defn validate
  "Return a vector of validation errors (empty = valid)."
  [doc]
  (let [cofog    (cofog-index doc)
        modules  (module-index doc)
        services (:services doc)
        ids      (set (map :egov.service/id services))]
    (cond-> []
      (empty? services) (conj "no :services in standard")
      :always
      (into (mapcat
             (fn [s]
               (let [sid   (:egov.service/id s "<no-id>")
                     code  (:egov.service/cofog s)
                     mod   (:egov.service/module s)
                     specs (:egov.service/spec-basis s)
                     inv   (:egov.service/invariants s {})]
                 (cond-> []
                   (not (contains? cofog code))   (conj (str sid ": COFOG class " (pr-str code) " not in backbone"))
                   (not (contains? modules mod))  (conj (str sid ": unknown module " (pr-str mod)))
                   (empty? specs)                 (conj (str sid ": G2 violation — empty :spec-basis"))
                   :always
                   (into (for [[ik want] required-invariants :when (not= (get inv ik) want)]
                           (str sid ": invariant " ik " must be " (pr-str want) ", got " (pr-str (get inv ik))))))))
             services))
      :always
      (into (let [n (count (filter #(= ":division" (:cofog/level %)) (:cofog doc)))]
              (when (not= n 10) [(str "COFOG backbone must have 10 divisions, found " n)])))
      :always
      (into (mapcat #(validate-profile % "polity" "polity-profile" ids) (:polity-profiles doc)))
      :always
      (into (mapcat #(validate-profile % "country" "country-profile" ids) (:country-profiles doc))))))

(defn coverage
  "Compute honest coverage figures."
  [doc]
  (let [cofog       (:cofog doc)
        divisions   (filter #(= ":division" (:cofog/level %)) cofog)
        groups      (filter #(= ":group" (:cofog/level %)) cofog)
        services    (:services doc)
        div-of      (fn [code] (first (str/split (str code) #"\.")))
        freq        (fn [kw] (frequencies (map #(get % kw "?") services)))
        by-domain   (freq :egov.service/domain)
        country-profiles (:country-profiles doc)]
    {:divisions-total   (count divisions)
     :divisions-covered (count (set (map #(div-of (:egov.service/cofog %)) services)))
     :groups-total      (count groups)
     :groups-covered    (count (set (map :egov.service/cofog services)))
     :services-total    (count services)
     :by-domain         by-domain
     :by-module         (freq :egov.service/module)
     :by-maturity       (freq :egov.service/maturity)
     :required-domains-covered (vec (sort (filter (set (keys by-domain)) required-domains)))
     :required-domains-missing (vec (sort (remove (set (keys by-domain)) required-domains)))
     :executable-services (get (freq :egov.service/maturity) ":executable" 0)
     :countries         (count country-profiles)
     :localization      (frequencies (mapcat (fn [p] (map :bind/service (:country-profile/bindings p)))
                                             country-profiles))}))

(defn render-report
  [doc cov errors]
  (let [std (:standard doc)]
    (str/join "\n"
      (concat
       [(str "# " (:standard/title-en std "e-gov standard") " — coverage")
        ""
        (str "- standard: `" (:standard/id std) "` v" (:standard/version std))
        (str "- validation: " (if (empty? errors) "✅ PASS" (str "❌ " (count errors) " error(s)")))
        ""
        "## COFOG function-space coverage (honest)"
        (str "- divisions covered: **" (:divisions-covered cov) "/" (:divisions-total cov) "**")
        (str "- groups covered: **" (:groups-covered cov) "/" (:groups-total cov) "**")
        (str "- standardized services: **" (:services-total cov) "**")
        (str "- executable (module .solve runs): **" (:executable-services cov)
             "** (R0 — all modules raise; deployment Council+operator gated)")
        ""
        "## Named transactional domains"
        (str "- covered: " (or (seq (str/join ", " (:required-domains-covered cov))) "—"))
        (str "- missing: " (or (seq (str/join ", " (:required-domains-missing cov))) "— (all covered)"))
        (str "- country adopters: " (:countries cov))]
       (when (seq errors) (concat ["" "## Validation errors"] (map #(str "- ❌ " %) errors)))))))

(defn -main [& args]
  (let [doc    (load-standard (or (first (remove #{"--out"} args)) default-std))
        errors (validate doc)
        cov    (coverage doc)]
    (println (render-report doc cov errors))
    (when (seq errors) (System/exit 1))))
