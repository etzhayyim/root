(ns etzhayyim.explorer.visual.react-loop
  "Visual test REACT loop for the etzhayyim explorer SPA (ADR-2606201610).

   The loop, per route:
     navigate → screenshot (computer-use-clj IComputer) → judge (Ollama gemma
     vision) → REACT (on a failed/inconclusive verdict, reload + settle longer
     and re-judge, up to :max-react times) → record the verdict.

   'React' = the loop reacts to what the vision model SEES — a visual feedback
   loop, not a one-shot assertion. Capabilities are injected (capture/navigate/
   judge) so the same loop runs against the real macOS desktop + live Ollama, or
   against offline stubs in --smoke mode.

   Each verdict is appended to a kotoba Datom log via the canonical kotoba.datom
   codec — content-addressed + chain-verifiable, the SAME codec the /explorer
   view verifies in the browser. The visual test thus writes a real kotoba
   commit-DAG of its own results."
  (:require [clojure.string :as str]
            [computeruse.computer :as c]
            [computeruse.macos :as macos]
            [kotoba.datom :as kd]
            [etzhayyim.explorer.visual.vision :as vision])
  (:gen-class))

;; ── the visual checks (one per explorer route) ──────────────────────────────
(def checks
  [{:route "/"
    :name "organism"
    :criterion (str "The page shows an 'Organism' view of a living system: a "
                    "tree-of-life / bonsai style diagram and/or an aliveness "
                    "panel with labelled metrics (Motion/Diversity/Coupling/...). "
                    "It is NOT an empty page or a raw error.")}
   {:route "/explorer"
    :name "explorer"
    :criterion (str "The page shows a blockchain/ledger explorer: a 'chain "
                    "verification' or 'commit-DAG' panel, a list of transactions "
                    "with long hash-like CID strings, and/or an entity/EAVT "
                    "browser. It is NOT an empty page or a raw error.")}
   {:route "/nodes"
    :name "nodes"
    :criterion (str "The page shows a node-distribution view: a graph/mesh of "
                    "many small coloured node dots and/or summary cards counting "
                    "cells (alive/dormant/stub). It is NOT an empty page or a raw "
                    "error.")}])

;; ── the loop (capability-injected, host-agnostic) ───────────────────────────
(defn run-check
  "Run one check with react/retry. caps = {:capture :navigate :judge :settle-ms
   :max-react}. Returns {:name :route :pass :saw :attempts :ok}."
  [{:keys [navigate capture judge settle-ms max-react] :or {settle-ms 1500 max-react 1}}
   {:keys [route name criterion]}]
  (loop [attempt 0]
    (navigate route (> attempt 0))            ; reload on a react attempt
    (Thread/sleep (long (* settle-ms (inc attempt))))   ; settle longer each react
    (let [shot (capture)
          {:keys [pass saw ok]} (judge shot criterion)
          done? (or pass (>= attempt max-react))]
      (println (format "  [%s] %s/%d %s — %s"
                       name route attempt
                       (cond pass "PASS" ok "FAIL" :else "INCONCLUSIVE")
                       saw))
      (if done?
        {:name name :route route :pass (boolean pass) :saw saw :ok ok :attempts (inc attempt)}
        (do (println (format "  [%s] reacting (reload + re-look)…" name))
            (recur (inc attempt)))))))

(defn run-loop
  "Run every check; returns the vector of result maps."
  [caps]
  (mapv (partial run-check caps) checks))

;; ── kotoba Datom log of results (reuses the canonical codec) ─────────────────
(defn results->datoms [results]
  (vec (mapcat
        (fn [{:keys [name route pass saw attempts]}]
          (let [e (str "visualcheck." name)]
            [(kd/add e :visual/route route)
             (kd/add e :visual/pass pass)
             (kd/add e :visual/attempts attempts)
             (kd/add e :visual/saw saw)]))
        results)))

(defn write-log!
  "Append ONE tx (all results) to a kotoba Datom log; returns {:cid :head :ok}."
  [results log-path]
  (let [prev (kd/head-cid log-path)
        tx (kd/make-tx (results->datoms results)
                       {:tx-id (inc (count (kd/read-log log-path)))
                        :as-of (count results) :prev-cid prev})
        cid (kd/append-tx! tx log-path)
        v (kd/verify-chain log-path)]
    {:cid cid :head (kd/head-cid log-path) :ok (:ok v) :length (:length v)}))

;; ── real adapters (macOS host + `open` navigation + Ollama vision) ──────────
(defn- sh [& args]
  (let [p (.start (ProcessBuilder. ^java.util.List (vec args)))]
    (slurp (.getInputStream p)) (.waitFor p)))

(def ^:private browser (or (System/getenv "VISUAL_BROWSER") "Google Chrome"))

(defn- browser-nav!
  "Drive the browser via AppleScript: raise it ABOVE the terminal/editor
   (activate), load the route in the front tab, and size the window large so the
   SPA fills the screenshot. This is what makes the visual judgement see the app
   rather than whatever was frontmost."
  [url]
  (sh "osascript" "-e"
      (str "tell application \"" browser "\"\n"
           "  activate\n"
           "  if (count of windows) = 0 then make new window\n"
           "  set URL of active tab of front window to \"" url "\"\n"
           "  set bounds of front window to {0, 22, 1440, 900}\n"
           "end tell")))

(defn- b64 [path]
  (.encodeToString (java.util.Base64/getEncoder)
                   (java.nio.file.Files/readAllBytes
                    (java.nio.file.Paths/get path (make-array String 0)))))

(defn display-computer
  "A custom IComputer host that screenshots a SPECIFIC display (multi-monitor
   setups: the shipped macos host always captures the main display). Implements
   the same image-block contract; optionally saves a copy for inspection.
   This is the library's 'injected host capability' extended for our box."
  [display & [{:keys [save-prefix model-width] :or {model-width 1280}}]]
  (let [n (atom 0)]
    (reify c/IComputer
      (-screenshot [_]
        (let [path (str "/tmp/cuse-d" display "-" (System/nanoTime) ".png")]
          (sh "screencapture" "-x" "-t" "png" "-D" (str display) path)
          (sh "sips" "-Z" (str model-width) path)
          (when save-prefix
            (sh "cp" path (str save-prefix "-" (swap! n inc) ".png")))
          [{:type "image" :source {:type "base64" :media_type "image/png"
                                   :data (b64 path)}}]))
      (-key! [_ _] "noop") (-type! [_ _] "noop")
      (-mouse-move! [_ _ _] "noop") (-click! [_ _ _ _] "noop")
      (-scroll! [_ _ _ _ _] "noop") (-cursor-position [_] [0 0]))))

(defn real-caps [{:keys [base ollama display save-prefix]
                  :or {base "http://localhost:8710"}}]
  (let [display (or display
                    (some-> (System/getenv "VISUAL_DISPLAY") Integer/parseInt))
        computer (if display
                   (display-computer display {:save-prefix save-prefix})
                   (macos/macos-computer))]
    {:navigate (fn [route _reload?] (browser-nav! (str base route)))
     :capture  (fn [] (c/-screenshot computer))
     :judge    (fn [shot criterion] (vision/judge (or ollama {}) shot criterion))
     :settle-ms 2200
     :max-react 1}))

;; ── offline smoke adapters (mock computer + deterministic judge) ─────────────
(defn- mock-shot [label]
  [{:type "image" :source {:type "base64" :media_type "image/png" :data "ZmFrZQ=="}
    :mock-label label}])

(defn smoke-caps []
  (let [seen (atom nil)]
    {:navigate (fn [route _reload?] (reset! seen route))
     :capture  (fn [] (mock-shot @seen))
     ;; deterministic judge: every route 'passes' on the first look — exercises
     ;; the loop/log wiring with no desktop or Ollama.
     :judge    (fn [shot _criterion]
                 {:ok true :pass true
                  :saw (str "stub render of " (:mock-label (first shot)))})
     :settle-ms 0
     :max-react 1}))

(defn -main [& args]
  (let [smoke? (some #{"--smoke"} args)
        log-path (or (System/getenv "VISUAL_LOG")
                     "/tmp/etzhayyim-visual-test.kotoba.edn")
        _ (println (str "\netzhayyim visual react loop — "
                        (if smoke? "SMOKE (offline)" "REAL (macOS + Ollama gemma)")))
        caps (if smoke?
               (smoke-caps)
               (let [ok? (vision/alive? {})]
                 (when-not ok?
                   (println "  ! Ollama not reachable at" vision/default-url
                            "— verdicts will be inconclusive."))
                 (real-caps {:save-prefix "/tmp/etzhayyim-visual"})))
        results (run-loop caps)
        passed (count (filter :pass results))
        log (write-log! results log-path)]
    (println (format "\n%d/%d checks passed." passed (count results)))
    (println (format "kotoba Datom log: %s  (head %s, chain %s, %d tx)"
                     log-path (subs (:head log) 0 (min 18 (count (:head log))))
                     (if (:ok log) "verified ✓" "BROKEN ✗") (:length log)))
    (when-not (= passed (count results))
      (System/exit 1))))
