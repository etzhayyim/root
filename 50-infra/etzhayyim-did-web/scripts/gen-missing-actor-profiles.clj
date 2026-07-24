#!/usr/bin/env bb
;;
;; gen-missing-actor-profiles.clj — one-shot generator that reads each
;; missing repo's manifest.jsonld and produces EDN entries for
;; actor-profile-seed.kotoba.edn.
;;
;; Usage:
;;   bb gen-missing-actor-profiles.clj            ;; print to stdout
;;   bb gen-missing-actor-profiles.clj --append   ;; append to seed directly
;;
(ns gen-missing-actor-profiles
  (:require [clojure.string :as str]
            [clojure.edn :as edn]
            [cheshire.core :as json]
            [clojure.java.io :as io]))

(def script-dir (str (io/file *file*)))
(def here (io/file *file*))
(def repo-root (.getParentFile (.getParentFile (.getParentFile (.getParentFile here)))))
(def seed-path (str (io/file repo-root "00-contracts/schemas/actor-profile-seed.kotoba.edn")))
(def etzhayyim-dir (str (io/file (.getParentFile (.getParentFile repo-root)) "etzhayyim")))

;; ── read existing handles from seed ────────────────────────────────────────
(defn read-existing-handles []
  (let [seed (slurp seed-path)]
    (->> (re-seq #":actor/handle\s+\"([^\"]+)\"" seed)
         (map second)
         set)))

;; ── read all com-etzhayyim-* repos ────────────────────────────────────────
(binding [*out* *err*]
  (println "repo-root:" (str repo-root))
  (println "seed-path:" seed-path "exists:" (.exists (io/file seed-path)))
  (println "etzhayyim-dir:" etzhayyim-dir "exists:" (.exists (io/file etzhayyim-dir))))
(defn read-all-repos []
  (->> (.listFiles (io/file etzhayyim-dir))
       (filter #(.isDirectory %))
       (map #(.getName %))
       (filter #(.startsWith ^String % "com-etzhayyim-"))
       (map #(str/replace ^String % #"^com-etzhayyim-" ""))
       sort))

;; ── read manifest.jsonld or actor-manifest.jsonld ──────────────────────────
(defn read-manifest [handle]
  (let [repo-dir (str (io/file etzhayyim-dir (str "com-etzhayyim-" handle)))
        json-file (or (when (.exists (io/file repo-dir "manifest.jsonld"))
                        "manifest.jsonld")
                      (when (.exists (io/file repo-dir "actor-manifest.jsonld"))
                        "actor-manifest.jsonld"))]
    (cond
      json-file
      (try {:data (json/parse-string (slurp (str (io/file repo-dir json-file))) true)
            :file json-file}
           (catch Exception e
             {:raw (slurp (str (io/file repo-dir json-file))) :file json-file}))

      (.exists (io/file repo-dir "manifest.edn"))
      (try {:data (edn/read-string (slurp (str (io/file repo-dir "manifest.edn"))))
            :file "manifest.edn"}
           (catch Exception e
             {:raw (slurp (str (io/file repo-dir "manifest.edn"))) :file "manifest.edn"}))

      :else nil)))

;; ── extract fields from manifest ───────────────────────────────────────────
(defn extract-adr [d]
  (cond
    (string? (:adr d))
    [(str/replace (:adr d) #"^ADR-?" "")]

    (map? (:adr d))
    (let [master (when (:master (:adr d))
                   (str/replace (str (:master (:adr d))) #"^etzhayyim:adr:" ""))
          r0 (when (:r0 (:adr d))
               (str/replace (str (:r0 (:adr d))) #"^etzhayyim:adr:" ""))
          r1 (when (:r1 (:adr d))
               (str/replace (str (:r1 (:adr d))) #"^etzhayyim:adr:" ""))]
      (remove nil? [master r0 r1]))

    :else []))

(defn extract-fields [manifest handle]
  (let [d (or (:data manifest) {})
        h (or (:name d) (:id d) handle)
        display-name (or (:displayName d) (:label d)
                        (when-let [desc (:description d)]
                          (first (str/split desc #" — "))))
        glyph (or (:glyph d) (:kanji d)
                  (when display-name (first (str/split display-name #" — "))))
        desc (or (:description d) (:purpose d) (:label d) "")
        desc (if (> (count desc) 500) (str (subs desc 0 497) "...") desc)
        lexicon (or (:primaryLexicon d)
                    (when (and (vector? (:lexicons d)) (seq (:lexicons d)))
                      (first (:lexicons d)))
                    (str "com.etzhayyim." handle))
        schema (or (:primarySchema d) (:primary-schema d))
        adr (extract-adr d)
        tier (or (:tier d) "Tier-B")
        created-at (if (seq adr)
                     (let [m (re-find #"^(\d{2})(\d{2})(\d{2})" (first adr))]
                       (if m (str "20" (second m) "-" (nth m 2) "-" (nth m 3)) "2026-06-01"))
                     "2026-06-01")]
    {:handle h :glyph glyph
     :display-name-ja (or (:displayName d) display-name)
     :display-name-en (or (:label d) display-name)
     :desc desc :lexicon lexicon :schema schema
     :adr adr :tier tier :created-at created-at}))

;; ── escape string for EDN ──────────────────────────────────────────────────
(defn edn-str [s]
  (if (nil? s) "\"\""
      (str "\"" (-> (str s)
                    (str/replace "\\" "\\\\")
                    (str/replace "\"" "\\\"")
                    (str/replace "\n" " ")) "\"")))

;; ── generate one EDN entry ─────────────────────────────────────────────────
(defn gen-service-vec [did]
  (let [pds-id (str did "#atproto_pds")
        p2p-id (str did "#xrpc-libp2p")
        pds-line (str "   :actor/service [{\"id\" \"" pds-id "\""
                       " \"type\" \"AtprotoPersonalDataServer\" \"serviceEndpoint\" \"https://pds.etzhayyim.com\"}")
        p2p-line (str "                   {\"id\" \"" p2p-id "\""
                       " \"type\" \"AtprotoXrpc\" \"serviceEndpoint\" \"/dnsaddr/etzhayyim.com/p2p/12D3KooWGRnHP5hHAxSnPQE5gopDqAzWkZ2NAFi2ZZ6o85FnAiEc\"}]}")]
    [pds-line p2p-line]))

(defn gen-entry [f]
  (let [handle (:handle f)
        did (str "did:web:etzhayyim.com:actor:" handle)
        [svc1 svc2] (gen-service-vec did)
        lines (remove nil?
                [(format "  {:actor/handle %s" (edn-str handle))
                 (format "   :actor/did %s" (edn-str did))
                 "   :actor/kind :tier-b"
                 "   :actor/tier \"B\""
                 "   :actor/status :r0"
                 (when (:glyph f) (format "   :actor/glyph %s" (edn-str (:glyph f))))
                 (when (:display-name-ja f) (format "   :actor/display-name-ja %s" (edn-str (:display-name-ja f))))
                 (when (:display-name-en f) (format "   :actor/display-name-en %s" (edn-str (:display-name-en f))))
                 "   :actor/performer-type :system"
                 "   :actor/ui-type :appview"
                 (format "   :actor/description %s" (edn-str (or (:desc f) (:display-name-en f) handle)))
                 (format "   :actor/primary-lexicon %s" (edn-str (:lexicon f)))
                 (when (:schema f) (format "   :actor/primary-schema %s" (edn-str (:schema f))))
                 (when (seq (:adr f))
                   (format "   :actor/adr [%s]" (str/join " " (map edn-str (:adr f)))))
                 (format "   :actor/created-at %s" (edn-str (:created-at f)))
                 "   :actor/vm []"
                 svc1
                 svc2])]
    (str/join "\n" lines)))

;; ── main ───────────────────────────────────────────────────────────────────
(defn -main [& args]
  (let [existing (read-existing-handles)
        all-repos (read-all-repos)
        missing (remove #(contains? existing %) all-repos)]
    (binding [*out* *err*]
      (println (format "[gen-missing-actor-profiles] %d repos missing profiles (of %d total)"
                       (count missing) (count all-repos))))
    (let [entries (doall
                    (for [handle missing]
                      (if-let [manifest (read-manifest handle)]
                        (gen-entry (extract-fields manifest handle))
                        (do
                          (binding [*out* *err*]
                            (println (format "  SKIP %s: no manifest found" handle)))
                          nil))))
          entries (remove nil? entries)]
      (binding [*out* *err*]
        (println (format "[gen-missing-actor-profiles] generated %d entries" (count entries))))
      (if (some #(= % "--append") args)
        (let [seed (slurp seed-path)
              close-idx (.lastIndexOf seed "]}")
              _ (assert (>= close-idx 0) "cannot find closing ]} in seed")
              header "\n  ;; ── auto-generated missing actor profiles (gen-missing-actor-profiles.clj) ──\n"
              body (str (str/join "\n\n" entries) "\n")
              out (str (subs seed 0 close-idx) header body (subs seed close-idx))]
          (spit seed-path out)
          (binding [*out* *err*]
            (println (format "[gen-missing-actor-profiles] appended %d entries to seed" (count entries)))))
        (println (str/join "\n\n" entries))))))

(apply -main *command-line-args*)
