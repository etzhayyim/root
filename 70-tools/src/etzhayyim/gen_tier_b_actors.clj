;; etzhayyim.gen-tier-b-actors — `bb gen:tier-b-actors`
;;
;; clj/bb port of the legacy 70-tools/scripts/entity-actors/gen-tier-b-actors.mjs
;; (repo "Operational code = clj/bb over the kotoba Datom log" rule). Behaviour is
;; byte-identical to the mjs it replaces.
;;
;; Scans 20-actors/<a>/ for `Tier-B` actors NOT already hand-authored in
;; infra-actors.ts and emits
;;   50-infra/etzhayyim-did-web/src/registry/tier-b-actors.gen.ts
;; as a Record<string, InfraActorEntry> merged into INFRA_ACTORS. This makes every
;; designed Tier-B actor resolve `did:web:etzhayyim.com:actor:<handle>` and appear
;; in /search — the named-actor counterpart to the entity-mirror registries.
;;
;; Manifest precedence (the SoT migration handle, ADR-2606042330 follow-up): the
;; canonical actor manifest is moving JSON-LD -> EDN (`manifest.edn`, Gen-3
;; kotoba-native). This generator reads `manifest.jsonld` when present (the
;; currently-populated registry source) and FALLS BACK to `manifest.edn`. As the
;; jsonld-deletion wave removes each actor's manifest.jsonld, this generator
;; auto-sources that actor from manifest.edn with no further change here.
;;
;; Regenerate:  bb gen:tier-b-actors

(ns etzhayyim.gen-tier-b-actors
  (:require [clojure.string :as str]
            [clojure.edn :as edn]
            [clojure.java.io :as io]
            [cheshire.core :as json]))

(def ^:private actors-dir "20-actors")
(def ^:private infra-ts "50-infra/etzhayyim-did-web/src/registry/infra-actors.ts")
(def ^:private out-ts "50-infra/etzhayyim-did-web/src/registry/tier-b-actors.gen.ts")
(def ^:private generated-at "2026-06-04T00:00:00+00:00")

;; Hand-authored handles already in INFRA_ACTORS — never override these.
(defn- hand-authored []
  (let [src (slurp infra-ts)]
    (->> (re-seq #"(?m)^ {2}\"?([a-z][a-z0-9-]*)\"?:\s*\{" src)
         (map second)
         set)))

;; Split a displayName like "早苗 — Field-Agriculture Robotics" into {glyph,label}.
;; Mirrors the mjs splitDisplay: glyph = leading CJK run of the first segment.
(defn- split-display [dn]
  (if (str/blank? (str dn))
    {:glyph nil :label dn}
    (let [head (-> (str/split dn #"\s+[—–-]\s+") first str/trim)
          m    (re-find #"^[　-鿿豈-﫿々〆〤ヶ]+" head)]
      {:glyph m :label dn})))

;; Pull 8–12-digit ADR ids out of an EDN adr value (vector / scalar), in order.
(defn- adr-ids [adr]
  (let [vals (cond
               (sequential? adr) adr
               (some? adr)       [adr]
               :else             [])]
    (->> vals
         (keep #(second (re-find #"(\d{8,12})" (str %))))
         distinct
         vec)))

;; jsonld `adr` may be an OBJECT whose insertion order is meaningful (mjs used
;; Object.values). cheshire returns an unordered PersistentHashMap, so extract
;; the ids from the raw JSON substring in document order instead — flat object /
;; array / string values only (no nesting in these manifests).
(defn- jsonld-adr-ids [raw]
  (let [seg (some-> (re-find #"\"adr\"\s*:\s*(\{[^}]*\}|\[[^\]]*\]|\"[^\"]*\")" raw)
                    second)]
    (->> (re-seq #"\d{8,12}" (or seg ""))
         distinct
         vec)))

;; JS-string escaping identical to JSON.stringify(String(s ?? "")).
(defn- js-esc [s] (json/generate-string (str (or s ""))))

(def ^:private handle-re #"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")

;; Normalize one actor dir -> registry record, or nil to skip.
;; jsonld is preferred when present; manifest.edn is the fallback source.
(defn- read-record [a hand]
  (let [dir   (io/file actors-dir a)
        jf    (io/file dir "manifest.jsonld")
        ef    (io/file dir "manifest.edn")
        ;; Unified manifest view with mjs-equivalent keys.
        m     (cond
                (.exists jf)
                (try (let [raw (slurp jf)
                           j (json/parse-string raw)]
                       {:tier (get j "tier")
                        :name (get j "name")
                        :display-name (get j "displayName")
                        :purpose (get j "purpose")
                        :primary-lexicon (get j "primaryLexicon")
                        :adrs (jsonld-adr-ids raw)})
                     (catch Exception _ nil))

                (.exists ef)
                (try (let [e (edn/read-string (slurp ef))
                           tier (:actor/tier e)]
                       {:tier (if (keyword? tier)
                                (when (= tier :tier-b) "Tier-B")
                                tier)
                        :name (:actor/id e)
                        :display-name (:actor/display-name e)
                        :glyph (:actor/glyph e)
                        :purpose (:actor/purpose e)
                        :primary-lexicon (:actor/primary-lexicon e)
                        :adrs (adr-ids (or (:actor/adr e) (:actor/related e)))})
                     (catch Exception _ nil)))]
    (when (and m (= (:tier m) "Tier-B"))
      (let [handle (str/lower-case (str (or (:name m) a)))]
        (when (and (not (hand handle))
                   (re-matches handle-re handle))
          (let [{:keys [glyph label]} (split-display (:display-name m))
                ;; jsonld actors carry displayName -> glyph via split; edn-only
                ;; (Gen-3) actors carry :actor/glyph directly and may lack a
                ;; display-name, so fall back to the edn glyph.
                glyph (or glyph (:glyph m))
                desc (-> (or (:purpose m) label handle)
                         (str/replace #"\s+" " ")
                         str/trim)]
            {:handle handle
             :glyph glyph
             :displayName (or label handle)
             :description desc
             :primaryLexicon (when (string? (:primary-lexicon m)) (:primary-lexicon m))
             :adrs (:adrs m)}))))))

(defn- entry->ts [e]
  (let [lines (cond-> [(str "  " (js-esc (:handle e)) ": {")
                       (str "    description: " (js-esc (:description e)) ",")]
                (:glyph e) (conj (str "    glyph: " (js-esc (:glyph e)) ","))
                :always    (conj (str "    displayName: " (js-esc (:displayName e)) ","))
                (:primaryLexicon e) (conj (str "    primaryLexicon: " (js-esc (:primaryLexicon e)) ","))
                :always    (into [(str "    adrs: [" (str/join ", " (map js-esc (:adrs e))) "],")
                                  "    service: ["
                                  "      {"
                                  (str "        id: \"did:web:etzhayyim.com:actor:" (:handle e) "#atproto_pds\",")
                                  "        type: \"AtprotoPersonalDataServer\","
                                  "        serviceEndpoint: \"https://pds.etzhayyim.com\","
                                  "      },"
                                  "    ],"
                                  "  },"]))]
    (str/join "\n" lines)))

(defn render [entries]
  (let [body (str/join "\n" (map entry->ts entries))]
    (str "// AUTOGENERATED — do not edit.\n"
         "// Source: 20-actors/<handle>/manifest.jsonld (tier == \"Tier-B\"), falling\n"
         "// back to manifest.edn (Gen-3 kotoba-native) as the jsonld-deletion wave\n"
         "// removes each actor's jsonld.\n"
         "// Regenerate: bb gen:tier-b-actors\n"
         "// ADR-2606042330 — register every designed Tier-B actor so its DID resolves and\n"
         "// it appears in /search (the named-actor counterpart to the entity mirrors).\n"
         "//\n"
         "// Merged into INFRA_ACTORS (infra-actors.ts). Hand-authored entries win on a\n"
         "// handle clash. State is kotoba-native; verificationMethod stays empty\n"
         "// (no-server-key, ADR-2605231525) — the DID trust root is did:web TLS.\n"
         "\n"
         "import type { InfraActorEntry } from \"./infra-actors\";\n"
         "\n"
         "export const TIER_B_GENERATED_AT = " (js-esc generated-at) ";\n"
         "export const TIER_B_TOTAL_COUNT = " (count entries) ";\n"
         "\n"
         "export const TIER_B_ACTORS: Readonly<Record<string, InfraActorEntry>> = {\n"
         body "\n"
         "};\n")))

(defn collect []
  (let [hand (hand-authored)]
    (->> (sort (map #(.getName %) (.listFiles (io/file actors-dir))))
         (keep #(try (read-record % hand) (catch Exception _ nil)))
         (sort-by :handle)
         vec)))

(defn -main [& _]
  (let [entries (collect)]
    (spit out-ts (render entries))
    (println (str "tier-b-actors.gen.ts: " (count entries)
                  " Tier-B actors registered (" out-ts ")"))
    (doseq [e entries]
      (println (str "  " (or (:glyph e) "  ") " " (:handle e))))))
