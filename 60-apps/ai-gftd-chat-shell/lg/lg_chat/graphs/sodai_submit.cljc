(ns lg-chat.graphs.sodai-submit
  "lg-chat `sodai_submit` graph — 渋谷区 粗大ごみ 公式フォーム自動入力 (langgraph-clj port).

  Faithful port of lg_chat/graphs/sodai_submit.py (ADR-2606280030) with the
  safety invariants intact. The human gate (最終送信は人間ゲート) is modelled
  idiomatically as a langgraph `interrupt-before` on the :submit-click node — a
  structural improvement over the Python's inline flag check, AND the env
  SODAI_ALLOW_SUBMIT + human_approved double-gate is preserved inside the node.

  Topology:
    START → :validate → :drive → route → (:submit-click | END)
    :submit-click → END           (compiled with :interrupt-before #{:submit-click})

  DEVIATION (noted): the actual browser drive is Playwright (python-only). There
  is no clj/bb browser driver, so :drive degrades to status \"browser_missing\"
  — the exact analogue of the Python's \"playwright_missing\" path. The mode
  validation, the shibuya field-map/CAPTCHA SSoT, the route topology, and the
  submit double-gate are all faithfully ported and verifiable; live form-fill
  stays on the Python graph."
  (:require [langgraph.graph :as g]
            [clojure.string :as str]
            [lg-chat.sodai-fields :as sf]))

(def DEFAULT-CONFIG {:allow-submit? false})
(defn- host-config [state] (merge DEFAULT-CONFIG (or (:host-config state) {})))

;; ── nodes ──────────────────────────────────────────────────────────────
(defn node-validate [state]
  (let [mode (-> (or (:mode state) "prefill") str str/lower-case)
        app (or (:application state) {})]
    (cond
      (not (#{"discover" "prefill" "submit"} mode))
      {:status "error" :error (str "unknown mode: " mode)}

      (and (not= mode "discover") (not (map? app)))
      {:status "error" :error "application must be an object"}

      :else
      {:mode mode :submitted false :captcha-detected false})))

(defn node-drive
  "Browser drive. No clj browser driver under bb → degrades to browser_missing,
  the analogue of the Python playwright_missing path (DEVIATION, noted)."
  [state]
  (if (= (:status state) "error")
    {}
    {:status "browser_missing"
     :filled []
     :discovered-fields []
     :error (str "ブラウザ自動操作 (Playwright) は python 専用で、この clj/bb ポートには "
                 "未移植です。実フォーム入力は python の sodai_submit graph を使ってください。")}))

(defn node-submit-click
  "最終送信 — reached only past the human interrupt-before gate. Still enforces
  an explicit host capability + human_approved double-gate."
  [state]
  (let [human-ok (boolean (:human-approved state))]
    (if (and human-ok (:allow-submit? (host-config state)))
      {:submitted true :status "ok"}
      {:submitted false
       :error (str "送信は実行しませんでした。human_approved=true かつ "
                   "host からの allow-submit capability の両方が必要です（人間ゲート）。")})))

(defn route-after-drive
  "Route to :submit-click only when mode=submit AND human_approved AND drive ok."
  [state]
  (if (and (= (:mode state) "submit")
           (boolean (:human-approved state))
           (= (:status state) "ok"))
    :submit-click
    g/END))

;; ── graph ──────────────────────────────────────────────────────────────
(defn build
  "Compile the sodai_submit StateGraph. The submit click is gated by a human
  interrupt-before (HITL); pass {} to disable."
  ([] (build {:interrupt-before #{:submit-click}}))
  ([opts]
   (-> (g/state-graph)
       (g/add-node :validate node-validate)
       (g/add-node :drive node-drive)
       (g/add-node :submit-click node-submit-click)
       (g/add-edge :validate :drive)
       (g/add-conditional-edges :drive route-after-drive
                                {:submit-click :submit-click g/END g/END})
       (g/add-edge :submit-click g/END)
       (g/set-entry-point :validate)
       (g/compile-graph opts))))

(def GRAPH (build))
