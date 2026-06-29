(ns junkan.cell
  "junkan 循環 cell entry — kotodama-cell-runner contract (ADR-2605192415 §7.1).

  Registered in 50-infra/cluster/murakumo/cell-runner/cells.edn as
  JunkanDemographyHeartbeatCell (node dan, cron 58 * * * *, healthz 13094) — DECLARED in
  20-actors/junkan/manifest.edn :actor/heartbeat-cells and folded into the fleet registry by
  `bb gen:cells` (no per-actor deploy; deploy-fleet picks it up). `fire` runs ONE
  deterministic DEMOGRAPHIC-DYNAMICS heartbeat (the second junkan analysis lens,
  ADR-2605290927; pattern 2606091000):

      load the China one-child levers + the peer low-fertility societies (KR/JP/IT/SG)
      → run the analysis-only system-dynamics read-off (China single-pool + cross-society
      contrast) → APPEND the findings datoms as ONE content-addressed tx to the actor-local
      kotoba commit-DAG, but ONLY when they CHANGE (idempotent-by-content) → resume-safe.

  NO external I/O, NO held key (no-server-key): it appends to a LOCAL ledger only.
  ANALYSIS-ONLY — junkan only looks, never touches (G4); every loop/regime is a disclosed
  HYPOTHESIS (G5); the summary is aggregate-only (per-society regime + binding stock + head
  CID), never a per-person datum (G6); anti-coercion (never prescribes who should reproduce,
  G11). The Murakumo digest narration + any live-engine bridge stay operator/Council-gated."
  (:require [junkan.methods.junkan-edn :as je]
            [junkan.methods.autorun :as autorun]
            [junkan.methods.kotoba :as k]
            #?(:clj [clojure.java.io :as io])))

#?(:clj
   (defn- actor-dir
     "20-actors/junkan, resolved from this namespace's classpath location (runs from any cwd)."
     []
     (-> (io/resource "junkan/cell.cljc") io/file .getParentFile)))

#?(:clj
   (def log-default
     (delay (io/file (actor-dir) "data" "persisted" "junkan.demography.kotoba.edn"))))

#?(:clj
   (defn fire
     "One demographic-dynamics heartbeat. Idempotent per log state (cycle derives from log
     length); an unchanged read-off is a no-op (`:appended false :reason :no-change`)."
     ([] (fire nil))
     ([log-path]
      (let [dir        (actor-dir)
            china-seed (str (io/file dir "kotoba" "seed.china-one-child.edn"))
            soc-seed   (str (io/file dir "kotoba" "seed.low-fertility-societies.edn"))
            levers     (vec (concat (je/instruments china-seed) (je/instruments soc-seed)))
            target     (str (or log-path @log-default))
            n          (count (k/read-log target))
            r (autorun/demography-beat {:levers levers :log-path target
                                        :tx-id (str "junkan-demog-" n) :as-of (str "as-of:" n)})]
        (println (str "JunkanDemographyHeartbeatCell cycle " n
                      ": societies=" (pr-str (:societies r))
                      " datoms=" (:count r)
                      " appended=" (:appended r) (when (:reason r) (str " (" (name (:reason r)) ")"))
                      " head=" (some-> (:head r) (subs 0 (min 16 (count (:head r)))))))
        r))))
