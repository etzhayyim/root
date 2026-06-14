;; org_actor.clj — 実在の日本財政組織を keyless mirror-actor 化 (entity-as-actor, ADR-2606042330).
;; danjo 弾正, ADR-2605301600.
;;
;; 1 公的組織 = 1 keyless mirror-actor (`did:web:etzhayyim.com:actor:jp-<handle>`). etzhayyim は
;; 鍵を持たず (no-server-key, verificationMethod 空) その組織を代理・代表しない — 観測ミラーのみ。
;; このモジュールは各組織の担当スライスを kotoba EAVT (`:gov.org/*`) に射影し、組織別ビュー
;; (徴収する税 / 所管する会計 / それぞれの per-yen 追跡可否) を返す。
;;
;; 徴収機関 (国税庁/税関) と会計所管機関 (復興庁/資源エネルギー庁/財務省理財局・主計局) を
;; 税レジストリ (taxes.clj) と突合して接続する。Pure + JVM stdlib; bb / clojure 両対応。
(ns root.danjo.methods.org-actor
  (:require [clojure.edn :as edn]
            [clojure.java.io :as io]
            [clojure.string :as str]))

(load-file "taxes.clj")
(alias 't  'root.danjo.methods.taxes)
(alias 'rl 'root.danjo.methods.revenue-ledger)

(defn load-orgs
  ([] (load-orgs nil))
  ([path]
   (let [f (io/file (or path "20-actors/danjo/data/jp-fiscal-orgs.edn"))
         f (if (.exists f) f (io/file "../data/jp-fiscal-orgs.edn"))]
     (edn/read-string (slurp f)))))

(defn- collects [org taxes]
  "Tax ids this org collects (from the tax registry's :collected-by)."
  (->> taxes (filter #(= (:id org) (:collected-by %))) (map :id) vec))

(defn- administers-taxes [org taxes]
  "Tax ids whose special-account this org administers (the earmarked taxes it ultimately spends)."
  (let [accts (set (:administers org))]
    (->> taxes (filter #(contains? accts (:special-account %))) (map :id) vec)))

(defn- add [e a v] [:db/add e a v])

(defn org-datoms
  "Flatten the org registry → append-only EAVT `:gov.org/*`. Each org is keyless
   (`:gov.org/keyless true` — no-server-key, ADR-2605231525). Collection + administration edges
   are resolved against the tax registry."
  [registry tax-registry]
  (let [taxes (:taxes tax-registry)]
    (vec
     (mapcat
      (fn [org]
        (let [e (str "org:" (:handle org))]
          (concat
           [(add e :gov.org/did (:did org))
            (add e :gov.org/ja (:ja org))
            (add e :gov.org/en (:en org))
            (add e :gov.org/role (:role org))
            (add e :gov.org/keyless true)                 ; no-server-key (verificationMethod 空)
            (add e :gov.org/sourcing :representative)]
           (when (:parent org) [(add e :gov.org/parent (:parent org))])
           (for [tid (collects org taxes)] (add e :gov.org/collects (str "tax:jp:" (name tid))))
           (for [acc (:administers org)]   (add e :gov.org/administers (str (subs (str acc) 1))))
           (for [tid (administers-taxes org taxes)] (add e :gov.org/spends (str "tax:jp:" (name tid)))))))
      (:orgs registry)))))

(defn org-view
  "Per-organization fiscal view: what it COLLECTS / ADMINISTERS, with honest per-yen flags +
   amounts. This is the org-actor's own slice of the national tax graph."
  [org-id org-registry tax-registry]
  (let [org   (->> (:orgs org-registry) (filter #(= org-id (:id %))) first)
        taxes (:taxes tax-registry)]
    (when-not org (throw (ex-info "no such org" {:org-id org-id})))
    (let [coll (->> taxes (filter #(= org-id (:collected-by %))) (map t/classify))
          adm  (->> taxes (filter #(contains? (set (:administers org)) (:special-account %))) (map t/classify))]
      {:org-id org-id :did (:did org) :ja (:ja org) :role (:role org) :keyless true
       :collects {:count (count coll)
                  :amount-jpy (reduce + 0 (map :fy2024-amount-jpy coll))
                  :per-yen-traceable (mapv :id (filter :per-yen? coll))
                  :fungible          (mapv :id (remove :per-yen? coll))
                  :taxes (mapv (fn [c] (select-keys c [:id :ja :earmark-kind :per-yen? :fy2024-amount-jpy])) coll)}
       :administers {:accounts (vec (:administers org))
                     :spends-taxes (mapv :id adm)
                     :amount-jpy (reduce + 0 (map :fy2024-amount-jpy adm))}})))

(defn -main [& args]
  (let [orgs  (load-orgs (first args))
        taxes (t/load-taxes nil)]
    (doseq [org (:orgs orgs)]
      (let [v (org-view (:id org) orgs taxes)]
        (println (:did v) "—" (:ja v) "(" (name (:role v)) ", keyless)")
        (when (pos? (:count (:collects v)))
          (println "   collects" (:count (:collects v)) "taxes," (:amount-jpy (:collects v)) "JPY;"
                   "per-yen追跡可:" (:per-yen-traceable (:collects v))))
        (when (seq (:accounts (:administers v)))
          (println "   administers" (:accounts (:administers v)) "— spends taxes" (:spends-taxes (:administers v))))))))
