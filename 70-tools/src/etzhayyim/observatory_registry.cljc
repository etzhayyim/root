(ns etzhayyim.observatory-registry
  "kotoba-genome W4-live (R0) — regenerate the namespace entity registry from the
  ADR-2606042330 KEYLESS mirror handles into FIRST-PARTY, disclosure-honest,
  self-evolving, posting observatory actors (ADR-2606302205 D4).

  Reads the generated keyless handles (src/registry/entity-handles.<ns>.gen.ts —
  the `[handle, subject]` pairs), maps each to a first-party observatory actor on
  the W3 runtime (own present-only member-CACAO-leashed did:key, voiceOf=etzhayyim,
  isObservatory), runs a DRY-RUN GROWTH beat (genome learn + a prepared observatory
  post), and emits the first-party registry + a summary.

  R0 SAFETY: everything is DRY-RUN. The live did.json regeneration (verificationMethod
  gains the present-only key) AND live posting AS an observatory of a real entity are
  Council/operator-gated (seed-and-grow, ADR-2606281500). `--live` is REFUSED here —
  this generator produces the first-party representation + dry-run proof only; nothing
  is published AS any real entity, and no real entity is impersonated (voiceOf=
  etzhayyim on every actor)."
  (:require [etzhayyim.observatory :as obs]
            [etzhayyim.actor :as actor]
            [etzhayyim.channel :as channel]
            [clojure.string :as str]
            [clojure.java.io :as io]
            [babashka.fs :as fs]))

(def ^:private ns-glyph
  {"cable" "綿津綱" "station" "綿津綱" "craft" "渡り" "gov" "公" "corp" "兜"})

(def ^:private gen-dir "50-infra/etzhayyim-did-web/src/registry")

(defn entity-entries
  "Parse the [handle, subject] pairs from entity-handles.<ns>.gen.ts (the keyless
  mirror registry). Returns a seq of [handle subject]; [] if the file is absent."
  [ns]
  (let [f (str gen-dir "/entity-handles." ns ".gen.ts")]
    (if (fs/exists? f)
      (->> (re-seq #"\[\"([^\"]+)\",\s*\"((?:[^\"\\]|\\.)*)\"\]" (slurp f))
           (mapv (fn [[_ h d]] [h d])))
      [])))

(defn regen-ns
  "Regenerate one namespace's keyless mirrors as FIRST-PARTY observatory actors
  (dry-run growth). Returns {:ns :total :sampled :actors [...]}. Bounded by :limit."
  [ns & {:keys [limit] :or {limit 25}}]
  (let [glyph   (ns-glyph ns)
        entries (entity-entries ns)
        sample  (take limit entries)]
    {:ns ns :total (count entries) :sampled (count sample)
     :actors
     (mapv (fn [[handle subject]]
             (let [o (obs/make-observatory {:ns ns :handle handle :subject subject :glyph glyph})
                   g (obs/grow! o 1 (str subject ": public-record observatory online (R0)"))]
               {:handle handle :subject subject
                :did (:did (actor/identity-of o))
                :voiceOf "etzhayyim" :isObservatory true :keyed :present-only-leashed
                :was :keyless-mirror :now :first-party-observatory
                :grew? (= 1 (get-in g [:actor :state :beat]))
                :postEmitted (boolean (get-in g [:post :emitted]))
                :postDryRun (boolean (get-in g [:post :dry-run]))
                :recommendation (get-in g [:recommendation :mechanism])}))
           sample)}))

(defn- flag [args k default] (or (second (drop-while #(not= % k) args)) default))

(defn -regen
  "bb entrypoint. Args: [--ns small|all|<ns>] [--limit N] [--out PATH] [--live]
  --live is REFUSED at R0 (Council/operator-gated)."
  [& args]
  (when (some #{"--live"} args)
    (println "[observatory] --live REFUSED at R0 — live did.json regeneration + live posting AS an observatory of a real entity is Council/operator-gated (seed-and-grow, ADR-2606281500). R0 is dry-run only.")
    (System/exit 2))
  (channel/default-registry!)   ; register the W1 dry-run drivers so the dry-run posts route
  (let [ns-arg (flag args "--ns" "small")
        limit  (Integer/parseInt (str (flag args "--limit" "25")))
        out    (flag args "--out" "80-data/observatory/registry.r0.edn")
        nss    (case ns-arg
                 "all"   ["cable" "station" "craft" "gov" "corp"]
                 "small" ["cable" "station" "craft"]
                 [ns-arg])
        results (mapv #(regen-ns % :limit limit) nss)
        summary {:generatedFrom "src/registry/entity-handles.<ns>.gen.ts (ADR-2606042330 keyless mirrors)"
                 :adr "2606302205 D4 — retires the keyless observational mirror"
                 :mode :R0-dry-run
                 :note "FIRST-PARTY disclosure-honest observatory actors (voiceOf=etzhayyim, isObservatory, present-only leashed did:key). NO impersonation, NO live posting — live is Council/operator-gated."
                 :namespaces (mapv (fn [r] {:ns (:ns r) :total (:total r) :sampled (:sampled r)
                                            :allDryRun (every? :postDryRun (:actors r))
                                            :allGrew (every? :grew? (:actors r))
                                            :allDisclosed (every? #(= "etzhayyim" (:voiceOf %)) (:actors r))}) results)
                 :registry results}]
    (io/make-parents out)
    (spit out (pr-str summary))
    (println (format "[observatory] R0 regen — %d namespace(s), %d first-party observatory actors (DRY-RUN); wrote %s"
                     (count nss) (reduce + (map :sampled results)) out))
    (doseq [r results]
      (println (format "  %-7s %5d keyless mirrors → %3d first-party observatory actors (dry-run · all grew=%s · all voiceOf=etzhayyim=%s)"
                       (:ns r) (:total r) (:sampled r)
                       (every? :grew? (:actors r))
                       (every? #(= "etzhayyim" (:voiceOf %)) (:actors r)))))
    summary))
