(ns matsurigoto.methods.standard
  "standard.py — matsurigoto 政 COFOG-based e-Government Service Standard loader/validator/coverage.
  1:1 Clojure port of `methods/standard.py` (ADR-2606062300).

  Reads data/cofog-standard.kotoba.edn (the universal, spec-derived service standard built on the
  UN COFOG function backbone) and:
    1. VALIDATES the standard (structural integrity + the charter invariants G1/G2/G3).
    2. Emits a HONEST COVERAGE report (out/coverage.md).

  POSTURE: matsurigoto is the EXECUTION sibling of ooyake's observation atlas. It SUPPLIES the
  standard to governments; it never operates as a government (G1/G3).

  House style: ':…' keyword strings stay strings; data maps stay string-/keyword-string-keyed
  exactly as the EDN reader produces; pure fns; file I/O only behind #?(:clj ...). The Python
  __main__ / main() CLI entry is provided as -main behind #?(:clj ...)."
  (:require [matsurigoto.methods._edn :as edn]
            [clojure.string :as str]
            [clojure.set :as set]
            #?(:clj [clojure.java.io :as io])))

;; The named transactional domains the e-gov standard must cover.
(def REQUIRED-DOMAINS
  #{":taxation" ":civil-registry" ":corp-registry" ":identity-credential"})

;; The universal service-level invariants (G1 + G2).
(def REQUIRED-INVARIANTS
  {":server-held-authority" false   ; G1
   ":spec-derived" true})           ; G2

;; G3 authority-bearing.
(def ALLOWED-OPERATED-BY #{":etzhayyim-council" ":adopting-government"})
(def ALLOWED-AUTHORITY-MODE #{":sovereign-governance" ":supplied-to-state"})

#?(:clj
   (defn- here []
     ;; pathlib.Path(__file__).resolve().parent  → methods/
     (-> *file* io/file .getParentFile)))

#?(:clj
   (defn- default-std []
     (-> (here) .getParentFile (io/file "data" "cofog-standard.kotoba.edn"))))

#?(:clj
   (defn- profiles-dir []
     (-> (here) .getParentFile (io/file "data" "profiles"))))

#?(:clj
   (defn load-profiles
     "Load every per-country profile from data/profiles/*.edn (one map per file)."
     ([] (load-profiles (profiles-dir)))
     ([directory]
      (let [dir (io/file directory)]
        (if-not (.exists dir)
          []
          (->> (.listFiles dir)
               (filter #(str/ends-with? (.getName ^java.io.File %) ".edn"))
               (sort-by #(.getName ^java.io.File %))
               (reduce (fn [out f]
                         (let [p (edn/load-edn f)]
                           (if (map? p) (conj out p) out)))
                       [])))))))

#?(:clj
   (defn load-standard
     "Read the standard EDN and merge external per-country profiles, deduped by iso3."
     ([] (load-standard (default-std)))
     ([path]
      (let [doc (edn/load-edn path)]
        (when-not (map? doc)
          (throw (ex-info "standard root must be a map" {})))
        (let [inline (vec (get doc ":country-profiles" []))
              seen0 (set (map #(get % ":country-profile/iso3") inline))
              [merged _]
              (reduce (fn [[acc seen] p]
                        (if (contains? seen (get p ":country-profile/iso3"))
                          [acc seen]
                          [(conj acc p) (conj seen (get p ":country-profile/iso3"))]))
                      [inline seen0]
                      (load-profiles))]
          (assoc doc ":country-profiles" merged))))))

(defn cofog-index [doc]
  (into {} (map (fn [row] [(get row ":cofog/code") row]) (get doc ":cofog" []))))

(defn module-index [doc]
  (into {} (map (fn [m] [(get m ":egov.module/id") m]) (get doc ":modules" []))))

(defn- validate-profile
  [p kind prefix service-ids]
  (let [name (get p (str prefix (if (= kind "polity") "id" "iso3")) "<no-id>")
        ob (get p (str prefix "operated-by"))
        am (get p (str prefix "authority-mode"))
        errs (cond-> []
               (not (contains? ALLOWED-OPERATED-BY ob))
               (conj (str kind " " name ": :operated-by " (pr-str ob) " not in " ALLOWED-OPERATED-BY))
               (not (contains? ALLOWED-AUTHORITY-MODE am))
               (conj (str kind " " name ": :authority-mode " (pr-str am) " not in " ALLOWED-AUTHORITY-MODE))
               (and (= kind "polity") (not= [ob am] [":etzhayyim-council" ":sovereign-governance"]))
               (conj (str "polity " name ": must be governed by :etzhayyim-council/:sovereign-governance"))
               (and (= kind "country") (not= [ob am] [":adopting-government" ":supplied-to-state"]))
               (conj (str "country " name ": must be :adopting-government/:supplied-to-state")))]
    (reduce (fn [errs b]
              (if-not (contains? service-ids (get b ":bind/service"))
                (conj errs (str kind " " name ": binding to unknown service "
                                (pr-str (get b ":bind/service"))))
                errs))
            errs
            (get p (str prefix "bindings") []))))

(defn validate
  "Return a list of validation errors (empty = valid)."
  [doc]
  (let [cofog (cofog-index doc)
        modules (module-index doc)
        services (get doc ":services" [])
        ;; collect service errors + the seen-ids set in one pass (Python builds seen_ids while looping)
        init {:errors (if (empty? services) ["no :services in standard"] [])
              :seen #{}}
        {svc-errors :errors seen-ids :seen}
        (reduce
         (fn [{:keys [errors seen]} s]
           (let [sid (get s ":egov.service/id" "<no-id>")
                 errors (cond-> errors
                          (contains? seen sid) (conj (str sid ": duplicate service id")))
                 seen (conj seen sid)
                 code (get s ":egov.service/cofog")
                 errors (cond-> errors
                          (not (contains? cofog code))
                          (conj (str sid ": COFOG class " (pr-str code) " not in backbone")))
                 mod (get s ":egov.service/module")
                 errors (cond-> errors
                          (not (contains? modules mod))
                          (conj (str sid ": unknown module " (pr-str mod))))
                 specs (or (get s ":egov.service/spec-basis") [])
                 errors (cond-> errors
                          (empty? specs)
                          (conj (str sid ": G2 violation — empty :spec-basis (spec-derived-only)")))
                 inv (or (get s ":egov.service/invariants") {})
                 errors (reduce (fn [errs [k want]]
                                  (if (not= (get inv k) want)
                                    (conj errs (str sid ": invariant " k " must be " (pr-str want)
                                                    ", got " (pr-str (get inv k))))
                                    errs))
                                errors
                                REQUIRED-INVARIANTS)]
             {:errors errors :seen seen}))
         init
         services)
        ;; COFOG backbone sanity: 10 divisions present
        divisions (filter #(= (get % ":cofog/level") ":division") (get doc ":cofog" []))
        errors (cond-> svc-errors
                 (not= (count divisions) 10)
                 (conj (str "COFOG backbone must have 10 divisions, found " (count divisions))))
        errors (reduce (fn [errs p] (into errs (validate-profile p "polity" ":polity-profile/" seen-ids)))
                       errors (get doc ":polity-profiles" []))
        errors (reduce (fn [errs p] (into errs (validate-profile p "country" ":country-profile/" seen-ids)))
                       errors (get doc ":country-profiles" []))]
    errors))

(defn- count-by
  "Mirror the Python `d[k] = d.get(k,0)+1` accumulation. Insertion order tracked via a vector
  pair (since render-report only ever iterates these via sorted keys, order is immaterial)."
  [items keyfn default]
  (reduce (fn [m it] (let [k (keyfn it default)] (update m k (fnil inc 0)))) {} items))

(defn coverage
  "Compute honest coverage figures."
  [doc]
  (let [cofog (get doc ":cofog" [])
        divisions (filter #(= (get % ":cofog/level") ":division") cofog)
        groups (filter #(= (get % ":cofog/level") ":group") cofog)
        services (get doc ":services" [])
        div-of (fn [code] (first (str/split code #"\.")))
        covered-divs (set (map #(div-of (get % ":egov.service/cofog")) services))
        covered-groups (set (map #(get % ":egov.service/cofog") services))
        by-domain (count-by services #(get %1 ":egov.service/domain" %2) "?")
        by-module (count-by services #(get %1 ":egov.service/module" %2) "?")
        by-maturity (count-by services #(get %1 ":egov.service/maturity" %2) "?")
        polity-cov (mapv (fn [p]
                           {"id" (get p ":polity-profile/id")
                            "name" (get p ":polity-profile/name")
                            "operated_by" (get p ":polity-profile/operated-by")
                            "authority_mode" (get p ":polity-profile/authority-mode")
                            "bound" (count (get p ":polity-profile/bindings" []))})
                         (get doc ":polity-profiles" []))
        profiles (get doc ":country-profiles" [])
        [profile-cov localization]
        (reduce (fn [[pc loc] p]
                  (let [binds (get p ":country-profile/bindings" [])
                        loc (reduce (fn [loc b]
                                      (update loc (get b ":bind/service") (fnil inc 0)))
                                    loc binds)]
                    [(conj pc {"iso3" (get p ":country-profile/iso3")
                               "name" (get p ":country-profile/name")
                               "operated_by" (get p ":country-profile/operated-by")
                               "sourcing" (get p ":country-profile/sourcing")
                               "bound" (count binds)})
                     loc]))
                [[] {}]
                profiles)]
    {"divisions_total" (count divisions)
     "divisions_covered" (count covered-divs)
     "groups_total" (count groups)
     "groups_covered" (count covered-groups)
     "services_total" (count services)
     "by_domain" by-domain
     "by_module" by-module
     "by_maturity" by-maturity
     "required_domains_covered" (vec (sort (set/intersection REQUIRED-DOMAINS (set (keys by-domain)))))
     "required_domains_missing" (vec (sort (set/difference REQUIRED-DOMAINS (set (keys by-domain)))))
     "executable_services" (get by-maturity ":executable" 0)
     "polities" polity-cov
     "profiles" profile-cov
     "countries" (count profile-cov)
     "localization" localization}))

(defn render-report
  "Build the coverage markdown report (byte-for-byte the Python render_report)."
  [doc cov errors]
  (let [std (get doc ":standard" {})
        L (transient [])
        P (fn [s] (conj! L s))]
    (P (str "# " (get std ":standard/title-en" "e-gov standard") " — coverage"))
    (P "")
    (P (str "- standard: `" (get std ":standard/id") "` v" (get std ":standard/version")))
    (P (str "- backbone: " (get std ":standard/backbone")))
    (P (str "- validation: " (if (empty? errors) "✅ PASS" (str "❌ " (count errors) " error(s)"))))
    (P "")
    (P "## COFOG function-space coverage (honest)")
    (P "")
    (P (str "- divisions covered: **" (get cov "divisions_covered") "/" (get cov "divisions_total") "**"))
    (P (str "- groups covered: **" (get cov "groups_covered") "/" (get cov "groups_total") "**"))
    (P (str "- standardized services: **" (get cov "services_total") "**"))
    (P (str "- executable (module .solve runs): **" (get cov "executable_services") "** "
            "(R0 — all modules raise; deployment Council+operator gated)"))
    (P "")
    (P "## Named transactional domains (user request)")
    (P "")
    (P (str "- covered: " (let [c (str/join ", " (get cov "required_domains_covered"))]
                            (if (= c "") "—" c))))
    (P (str "- missing: " (let [m (str/join ", " (get cov "required_domains_missing"))]
                            (if (= m "") "— (all covered)" m))))
    (P "")
    (P "## Services by domain")
    (P "")
    (doseq [k (sort (keys (get cov "by_domain")))]
      (P (str "- " k ": " (get-in cov ["by_domain" k]))))
    (P "")
    (P "## Services by maturity")
    (P "")
    (doseq [k (sort (keys (get cov "by_maturity")))]
      (P (str "- " k ": " (get-in cov ["by_maturity" k]))))
    (P "")
    (P "## Polity profiles (principal A — the Kingdom's own 統治機構)")
    (P "")
    (if (seq (get cov "polities"))
      (doseq [p (get cov "polities")]
        (P (str "- " (get p "name") ": " (get p "bound") " organs bound "
                "[" (get p "operated_by") " / " (get p "authority_mode") "]")))
      (P "- none yet"))
    (P "")
    (P (str "## Country profiles (principal B — " (get cov "countries") " nation-state adopters)"))
    (P "")
    (if (seq (get cov "profiles"))
      (doseq [p (get cov "profiles")]
        (P (str "- " (get p "iso3") " (" (get p "name") "): " (get p "bound") " services bound "
                "[" (get p "operated_by") " / sourcing " (get p "sourcing") "]")))
      (P "- none yet"))
    (P "")
    (P "## Per-service localization (各国調整 — how many countries localize each service)")
    (P "")
    (let [services (into {} (map (fn [s] [(get s ":egov.service/id") s]) (get doc ":services" [])))
          loc (get cov "localization")
          ;; sorted(services, key=lambda x: (-loc.get(x,0), x))
          sids (sort-by (fn [x] [(- (get loc x 0)) x]) (keys services))]
      (doseq [sid sids]
        (let [n (get loc sid 0)
              ja (get-in services [sid ":egov.service/ja"] "")]
          (P (str "- `" sid "` (" ja "): **" n "** / " (get cov "countries") " countries")))))
    (P "")
    (when (seq errors)
      (P "## Validation errors")
      (P "")
      (doseq [e errors] (P (str "- ❌ " e)))
      (P ""))
    (str/join "\n" (persistent! L))))

#?(:clj
   (defn -main
     "CLI entry: validate the standard + write out/coverage.md."
     [& argv]
     (let [args (vec argv)
           [args outdir] (if-let [i (some #(when (= (nth args %) "--out") %) (range (count args)))]
                           [(into (subvec args 0 i) (subvec args (+ i 2)))
                            (io/file (nth args (inc i)))]
                           [args (io/file (here) "out")])
           path (if (seq args) (io/file (first args)) (default-std))
           doc (load-standard path)
           errors (validate doc)
           cov (coverage doc)
           report (render-report doc cov errors)]
       (.mkdirs outdir)
       (spit (io/file outdir "coverage.md") report)
       (println report)
       (println (str "\n[written] " (io/file outdir "coverage.md")))
       (if (seq errors) 1 0))))
