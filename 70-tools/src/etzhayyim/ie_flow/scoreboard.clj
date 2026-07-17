#!/usr/bin/env bb
;; ie-flow SoS scoreboard — score every embedded actor + fold into the organism reward.
;; Run from repo root:
;;   bb -cp "20-actors:70-tools/src:20-actors/kotodama/src" \
;;      70-tools/src/etzhayyim/ie_flow/scoreboard.clj [--write]
;; ADR-2606212200. Pure read of real flow-states; --write commits the snapshot.
(ns etzhayyim.ie-flow.scoreboard
  (:require [clojure.edn :as edn]
            [clojure.java.io :as io]
            [clojure.string :as str]
            [etzhayyim.ie-flow.score :as score]
            [etzhayyim.ie-flow.embed :as embed]
            [etzhayyim.ie-flow.ledger :as ledger]
            [ibuki.methods.metabolism :as metab]
            [kafun.methods.kafun-edn :as ke]
            [kafun.methods.ie-flow :as kafun-ief]
            [ugachi.methods.ugachi-edn :as ue]
            [ugachi.methods.ie-flow :as ugachi-ief]
            [kaname.methods.ie-flow :as kaname-ief]
            [tsumugi.methods.ie-flow :as tsumugi-ief]
            [shionome.methods.ie-flow :as shionome-ief]
            [inochi.methods.ie-flow :as inochi-ief]
            [hokorobi.methods.ie-flow :as hokorobi-ief]
            [hoshimori.methods.ie-flow :as hoshimori-ief]
            [tsugite.methods.ie-flow :as tsugite-ief]
            [asobi.methods.ie-flow :as asobi-ief]
            [kotoba.datom :as kd]))

(def registry-path "80-data/ie-flow/registry.edn")
(def snapshot-path "80-data/ie-flow/scoreboard.edn")

(defn- safe [f] (try (f) (catch Exception _ nil)))

(def busshi-flow-state-paths
  "Flat-west artifact locations, with an explicit override for detached/root-only runs."
  (remove nil?
          [(System/getenv "BUSSHI_FLOW_STATE_PATH")
           "../com-etzhayyim-busshi/out/ie-flow-state.edn"
           "orgs/etzhayyim/com-etzhayyim-busshi/out/ie-flow-state.edn"]))

(defn external-busshi-flow-state []
  (when-let [path (first (filter #(.isFile (io/file %)) busshi-flow-state-paths))]
    (let [contract (edn/read-string (slurp path))]
      (when-not (= :busshi/ie-flow-state (:contract/id contract))
        (throw (ex-info "invalid busshi ie-flow contract" {:path path :contract contract})))
      (:state contract))))

(defn real-flow-states
  "Build {actor flow-state} for every embedded actor that has a REAL measured flow available:
   - kafun: its live adapter over the seed (information-energy rectification)
   - repo-git + any actor with a committed/recorded flow.kotoba.edn ledger: embed/measure
   Actors with no measured flow yet are returned in :pending (listed, not scored)."
  []
  (let [kafun-state (safe #(kafun-ief/flow-state (ke/stands "20-actors/kafun/kotoba/seed.edn")))
        ugachi-state (safe #(ugachi-ief/flow-state (ue/projects "20-actors/ugachi/kotoba/seed.edn")))
        busshi-state (external-busshi-flow-state)
        kaname-state (safe #(kaname-ief/flow-state))
        tsumugi-state (safe #(tsumugi-ief/flow-state))
        shionome-state (safe #(shionome-ief/flow-state))
        inochi-state (safe #(inochi-ief/flow-state))
        hokorobi-state (safe #(hokorobi-ief/flow-state))
        hoshimori-state (safe #(hoshimori-ief/flow-state))
        tsugite-state (safe #(tsugite-ief/flow-state))
        asobi-state (safe #(asobi-ief/flow-state))
        measured (fn [actor] (safe #(let [st (embed/measure actor)]
                                      (when (pos? (:flows-n st 0)) st))))
        candidates (cond-> {}
                     kafun-state (assoc "kafun" kafun-state)
                     ugachi-state (assoc "ugachi" ugachi-state)
                     busshi-state (assoc "busshi" busshi-state)
                     kaname-state (assoc "kaname" kaname-state)
                     tsumugi-state (assoc "tsumugi" tsumugi-state)
                     shionome-state (assoc "shionome" shionome-state)
                     inochi-state (assoc "inochi" inochi-state)
                     hokorobi-state (assoc "hokorobi" hokorobi-state)
                     hoshimori-state (assoc "hoshimori" hoshimori-state)
                     tsugite-state (assoc "tsugite" tsugite-state)
                     asobi-state (assoc "asobi" asobi-state))
        ;; actors scored via their live adapter above are not re-read from a ledger here
        with-ledgers (reduce (fn [m a]
                               (if-let [st (measured a)] (assoc m a st) m))
                             candidates
                             ["repo-git" "ibuki" "okaimono"])]
    with-ledgers))

(defn descendant-opts
  "Per-actor {:descendant w} from registry.edn (:adopted + :measured-sources). Default applied
  by the score lib when absent."
  []
  (let [reg (edn/read-string (slurp registry-path))
        rows (concat (:adopted reg) (:measured-sources reg))]
    (into {} (for [r rows :when (:descendant r)]
               [(or (:actor r) (:name r)) {:descendant (:descendant r)}]))))

(defn pending-adopters
  "Adopted actors (registry.edn :adopted) that have NO measured flow yet — honest coverage:
  the colony has more :adopted members than the scoreboard scores. Returns [{:actor :note}…]
  sorted, carrying each one's registry note (why it is pending / what shape it needs)."
  [scored-actors]
  (let [reg (edn/read-string (slurp registry-path))
        scored (set scored-actors)]
    (->> (:adopted reg)
         (remove #(scored (:actor %)))
         (mapv (fn [r] {:actor (:actor r) :note (:note r)}))
         (sort-by :actor)
         vec)))

(defn build []
  (let [states (real-flow-states)
        opts (descendant-opts)
        board (score/score-roster states opts)
        reward (score/colony-reward board)
        ;; the organism-reward integration: intake WITHOUT vs WITH the colony-order source
        env-base {:compute-hours 2 :members 1}
        intake-base (metab/intake-of env-base)
        intake-with (metab/intake-of (merge env-base (score/as-env-source board)))]
    {:as-of "scoreboard"
     :adr "2606212200"
     :scored (mapv #(select-keys % [:actor :score :throughput :vetoed? :components]) board)
     :pending (pending-adopters (map :actor board))
     :colony reward
     :organism {:env-source (score/as-env-source board)
                :intake-without-colony intake-base
                :intake-with-colony intake-with
                :delta (- intake-with intake-base)
                :note "intake-with − intake-without = the free-energy the colony's information-control adds to the organism's Φ (→ reserves → survival). The reward integration, ADR-2606212200."}}))

;; ── human-readable report (pure: snapshot → markdown) ───────────────────────

(defn render-md
  "Render a build snapshot into a human-readable markdown SoS report (pure). Operators read
  the colony's information-control state without parsing EDN. Each actor's score is its
  active-inference 利得; colony-order is the negentropy SOURCE the organism's metabolism draws on."
  [snap]
  (let [scored (:scored snap)
        pending (:pending snap)
        c (:colony snap)
        org (:organism snap)
        fmt (fn [x] (format "%.3f" (double x)))
        comp (fn [r k] (fmt (get-in r [:components k] 0)))]
    (str
     "# ie-flow SoS scoreboard — the colony's information-control\n\n"
     "_Generated by `scoreboard.clj` (ADR-2606212200). DO NOT hand-edit._ "
     "Each actor is an **information-control actor**: it RECTIFIES (整流) scattered flow into "
     "returned order. Its score is its active-inference **利得** (∈ 0..1, gated by 子孫 wellbecoming; "
     "0 = vetoed). The colony aggregate is a **negentropy SOURCE** fed to the artificial organism's "
     "metabolism (Φ → reserves → survival).\n\n"
     "**" (count scored) " actors with measured flow** · colony-reward **" (fmt (:colony-reward c))
     "** · colony-order **" (:colony-order c) "** · mean score **" (fmt (:mean-score c)) "**"
     (when (pos? (:vetoed-n c 0)) (str " · " (:vetoed-n c) " vetoed"))
     (when (seq pending) (str " · **" (count pending) " adopted pending an adapter**")) "\n\n"
     "| actor | score | throughput | rectify | η | Φ | efficiency | surprise |\n"
     "|---|---|---|---|---|---|---|---|\n"
     (str/join "\n"
               (for [r scored]
                 (str "| " (:actor r) (when (:vetoed? r) " ⚠")
                      " | **" (fmt (:score r)) "** | " (str (:throughput r))
                      " | " (comp r :rectify) " | " (comp r :eta) " | " (comp r :phi)
                      " | " (comp r :efficiency) " | " (comp r :surprise) " |")))
     "\n\n## Organism reward (the SoS → ibuki metabolism)\n\n"
     "The colony's aggregate information-control feeds the organism's free-energy intake as the "
     "`:colony-order` negentropy source:\n\n"
     "```\n"
     "intake  " (:intake-without-colony org) " → " (:intake-with-colony org)
     "   (+" (:delta org) " from colony-order)\n"
     "```\n\n"
     "_Each actor's 利得 is the organism's nutrient: a parasitic / 子孫-harming actor is vetoed to 0 "
     "and feeds the organism nothing (it cannot sustain survival by predation). "
     "Active inference at the colony scale._\n"
     (when (seq pending)
       (str "\n## Adopted, pending an adapter\n\n"
            "These actors are in the ie-flow `:adopted` registry but produce no measured flow yet "
            "(no per-actor adapter), so they do not score. Honest coverage: the colony of intent is "
            "larger than the colony of measure.\n\n"
            "| actor | why pending |\n|---|---|\n"
            (str/join "\n" (for [p pending]
                             (str "| " (:actor p) " | " (or (:note p) "—") " |"))))))))

(def report-path "80-data/ie-flow/scoreboard.md")

(defn -main [& args]
  (let [snap (build)
        write? (some #{"--write"} args)]
    (println (str "ie-flow SoS scoreboard (" (count (:scored snap)) " actors with measured flow)"))
    (doseq [r (:scored snap)]
      (println (format "  %-10s score=%.3f  throughput=%-6s %s"
                       (:actor r) (double (:score r)) (str (:throughput r))
                       (if (:vetoed? r) "[VETOED]" ""))))
    (println (str "colony: " (score/summary-line (:colony snap))))
    (println (str "organism intake: " (get-in snap [:organism :intake-without-colony])
                  " → " (get-in snap [:organism :intake-with-colony])
                  "  (+" (get-in snap [:organism :delta]) " from colony-order = the SoS reward)"))
    (when (seq (:pending snap))
      (println (str "adopted, pending an adapter (" (count (:pending snap)) "): "
                    (str/join " " (map :actor (:pending snap))))))
    (when write?
      (spit snapshot-path
            (str ";; ie-flow SoS scoreboard snapshot (generated by scoreboard.clj). ADR-2606212200.\n"
                 ";; Each actor's score = its active-inference 利得 (information-control); colony-order =\n"
                 ";; the negentropy SOURCE the artificial organism's metabolism draws on. DO NOT hand-edit.\n"
                 (with-out-str (clojure.pprint/pprint snap))))
      (spit report-path (render-md snap))
      (println (str "wrote " snapshot-path " + " report-path)))))

(when (= *file* (System/getProperty "babashka.file"))
  (apply -main *command-line-args*))
