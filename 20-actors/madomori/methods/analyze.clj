;; madomori 窓守 — end-to-end façade window-cleaning analyzer (orchestrator).
;;
;; Loads the building seed and runs the R0 sim pipeline:
;;   1. plan the façade coverage path (boustrophedon) over the pane grid + budget;
;;   2. assess the wind/sway safety envelope + fall-arrest redundancy (★ G5);
;;   3. assess the suction adhesion factor-of-safety on the surface (★ G7).
;;
;; The report carries a top-level :go? = (envelope permitted? AND adhesion safe?):
;; a descent is planned only if BOTH safety gates pass.
;;
;; Pure Clojure, no deps → babashka-runnable AND kotoba-pywasm-portable.
;; Per ADR-2606142020 (madomori R0).
(ns madomori.methods.analyze
  (:require [clojure.edn :as edn]
            [madomori.methods.facade-path :as fp]
            [madomori.methods.wind-envelope :as we]
            [madomori.methods.adhesion :as ad]))

(defn load-seed
  "Read the building façade EDN seed into a Clojure map."
  [path]
  (edn/read-string (slurp path)))

(defn run
  "Run the full R0 analysis over a loaded seed map. Returns a report map."
  [seed]
  (let [face (:face seed)
        robot (:robot seed)
        wind (:wind seed)
        anchors (:anchors seed)
        ;; 1. coverage path + budget
        coverage (fp/plan face robot)
        ;; 2. wind/sway safety envelope (★ G5)
        envelope (we/assess face wind robot anchors)
        ;; 3. adhesion factor-of-safety (★ G7)
        adhesion (ad/assess robot (:surface face))]
    {:facility (:id (:facility seed))
     :face {:id (:id face) :rows (:rows face) :cols (:cols face)
            :panes (* (:rows face) (:cols face)) :surface (:surface face)}
     :coverage coverage
     :envelope envelope
     :adhesion adhesion
     ;; a descent is planned only if BOTH safety gates pass
     :go? (boolean (and (:permitted? envelope) (:safe? adhesion)))}))

(defn report-str
  "Human-readable report (for out/ and Murakumo narration input, G6)."
  [res]
  (str ";; madomori 窓守 — façade window-cleaning R0 analysis\n"
       "face: " (get-in res [:face :id]) " "
       (get-in res [:face :rows]) "×" (get-in res [:face :cols]) " panes ("
       (get-in res [:face :panes]) " total, " (name (get-in res [:face :surface])) ")\n"
       "coverage complete?: " (get-in res [:coverage :coverage :complete?]) "\n"
       "path length (m): " (format "%.1f" (get-in res [:coverage :length-m])) "\n"
       "water (L): " (format "%.1f" (get-in res [:coverage :budget :water-l]))
       "  agent (mL): " (format "%.1f" (get-in res [:coverage :budget :agent-ml])) "\n"
       "peak wind (m/s): " (format "%.1f" (get-in res [:envelope :peak-wind-mps]))
       " / stop " (format "%.1f" (get-in res [:envelope :stop-threshold-mps])) "\n"
       "sway amplitude (m): " (format "%.3f" (get-in res [:envelope :sway-amplitude-m])) "\n"
       "fall-arrest redundant?: " (get-in res [:envelope :fall-arrest-redundant?])
       " (" (get-in res [:envelope :independent-anchors]) " anchors)\n"
       "wind work-permitted?: " (get-in res [:envelope :permitted?]) "\n"
       "adhesion FoS: " (format "%.2f" (get-in res [:adhesion :factor-of-safety]))
       " / required " (format "%.2f" (get-in res [:adhesion :required-fos]))
       " → safe?: " (get-in res [:adhesion :safe?]) "\n"
       "GO (both gates pass)?: " (:go? res) "\n"))

(defn -main [& args]
  (let [path (or (first args) "20-actors/madomori/data/facade.edn")
        res (run (load-seed path))]
    (print (report-str res))
    (flush)))
