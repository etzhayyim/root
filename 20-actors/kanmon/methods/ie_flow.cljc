#!/usr/bin/env bb
;; kanmon 関門 — ie-flow energy-flow: rectify barrier-load disorder → wellbecoming order.
(ns kanmon.methods.ie-flow
  "ie_flow.cljc — kanmon 関門 ENERGY-FLOW leg (ADR-2606291500 §ie-flow; embeds the
  SHARED etzhayyim.ie-flow.metrics order-calculus, ADR-2606211200/2606212030).

  The design ask: take the exam-gate CAUSALITY and turn it into wellbecoming via an
  energy flow. kanmon is a dissipative RECTIFIER (整流器): scattered barrier-load
  (disorder — diffuse harm to students' wellbecoming) flows in, and kanmon concentrates
  it onto a few high-leverage OPENING interventions that serve 子孫 wellbecoming, which
  feed downstream actors (shiori 栞 relief / shinan 指南 scaffold / danjo 弾正 disclosure
  / kaname 要 leverage). The measured order-index = how much disorder was rectified into
  wellbecoming-order; η = exported wellbecoming-order ÷ consumed assessment (≫1 = a 利得,
  not a 課金される魔法陣).

  kanmon moves INFORMATION-energy (a prioritized OPENING map), never students or money;
  the actual openings are enacted by ossekai/Council. PURE + deterministic — folds through
  the shared metrics; no wall clock, no randomness."
  (:require [clojure.string :as str]
            [etzhayyim.ie-flow.metrics :as ie]
            [kanmon.methods.analyze :as az]))

;; route → how much it serves WELLBECOMING (deeper-leverage openings export more order)
(def route->wb-weight
  {:destake 1.0 :open-pathway 0.9 :equity-watch 0.8 :transparency-gap 0.7 :monitor 0.1})

;; route → the downstream WELLBECOMING sink actor (the system of systems)
(def route->sink
  {:destake "shiori"          ;; 栞 — relief from one-shot life-gating harm
   :open-pathway "shinan"     ;; 指南 — open scaffold along the alternative pathway
   :equity-watch "shiori"     ;; 栞 — relief for access-disadvantaged cohorts
   :transparency-gap "danjo"  ;; 弾正 — disclosure / accountability
   :monitor "kaname"})        ;; 要 — leverage synthesis / observe

(def ^:private assess-cost 0.02)  ;; kanmon's cheap information-assessment cost per exam

(defn flow-events
  "Project a kanmon assessment (the \"exams\" rows) into ie-flow EVENT maps. Each exam's
   barrier-load is the scattered ENERGY entering the rectifier; its value = barrier-load ×
   wellbecoming-weight of its OPENING route (concentrating energy onto high-leverage
   openings). kanmon is the agent doing the rectification (:agent? true)."
  [exam-rows]
  (mapv (fn [{:keys [exam route barrier-load]}]
          (let [w (get route->wb-weight route 0.1)]
            {:source (:id exam)
             :target (str "open:" (name route))
             :type :opening
             :volume (double barrier-load)          ;; disorder in
             :value (* (double barrier-load) w)     ;; wellbecoming-order out
             :cost assess-cost
             :risk 0.0
             :agent? true
             :actor "kanmon"
             :sink (get route->sink route "kaname")}))
        exam-rows))

(defn- agent-costs
  "Agent cost vector computed from the RAW events (the shared aggregate-flows drops the
   :agent? flag, so η must be fed explicitly): kanmon's exported wellbecoming-order vs the
   cheap assessment it consumed."
  [events]
  {:gross-profit (reduce + 0.0 (map #(double (:value % 0)) events))
   :api-cost     (reduce + 0.0 (map #(double (:cost % 0)) events))
   :human-cost   0.0
   :failure-cost (reduce + 0.0 (map #(double (:risk % 0)) events))})

(defn flow-state
  "Fold the events through the SHARED order calculus → the IE-flow state vector
   (η fed from the raw events, see agent-costs)."
  [exam-rows]
  (let [evs (flow-events exam-rows)]
    (ie/flow-state evs {:agent-costs (agent-costs evs)})))

(defn metrics
  "The wellbecoming readout: order-index (rectification), net-gain (Φ), η (export÷consume),
   entropy before/after, parasitic?."
  [exam-rows]
  (let [evs (flow-events exam-rows)
        st (ie/flow-state evs {:agent-costs (agent-costs evs)})
        vol (map :volume evs)
        val (map :value evs)
        hb (ie/entropy (ie/normalize vol))
        ha (ie/entropy (ie/normalize val))]
    {:throughput (Math/round (double (:throughput st)))
     :order-index (/ (Math/round (* (double (:order-index st)) 1000.0)) 1000.0)
     :net-gain (/ (Math/round (* (double (:net-gain st)) 1000.0)) 1000.0)
     :eta (let [e (double (:agent-efficiency st))]
            (if (Double/isInfinite e) e (/ (Math/round (* e 100.0)) 100.0)))
     :h-before (/ (Math/round (* hb 1000.0)) 1000.0)
     :h-after (/ (Math/round (* ha 1000.0)) 1000.0)
     :parasitic? (:parasitic? st)
     :wellbecoming-served (not (:parasitic? st))}))

;; ── 4-column system-of-systems viz model (sources → 整流 → openings → sinks) ──
(defn viz-model [exam-rows]
  (let [evs (flow-events exam-rows)
        m (metrics exam-rows)
        by-route (group-by :route exam-rows)
        route-keys (vec (keys by-route))]
    {:actor "kanmon" :glyph "関"
     :title "kanmon 関門 — how the actor turns exam-gate causality into wellbecoming (ie · system of systems)"
     :subtitle "散在する barrier-load (disorder · 子孫 wellbecoming への拡散的害) → kanmon 整流 → 高レバレッジ OPENING (order) → 下流 wellbecoming アクター"
     :metrics m
     :gate {:id "kanmon" :label "kanmon 関門 整流器"}
     :columns
     [{:id "sources" :label "入試ゲート (barrier-load)"
       :nodes (mapv (fn [{:keys [exam barrier-load]}]
                      {:id (:id exam) :label (:id exam)
                       :country (str (:country exam)) :weight (double barrier-load)})
                    exam-rows)}
      {:id "gate" :label "kanmon 整流" :nodes [{:id "kanmon" :label "関門"}]}
      {:id "openings" :label "OPENING (高レバレッジ介入)"
       :nodes (mapv (fn [r] {:id (str "open:" (name r))
                             :label (name r)
                             :wb-weight (get route->wb-weight r 0.1)
                             :count (count (get by-route r))})
                    route-keys)}
      {:id "sinks" :label "下流 wellbecoming アクター (SoS)"
       :nodes (mapv (fn [a] {:id a :label a})
                    (distinct (map #(get route->sink % "kaname") route-keys)))}]
     :links
     (concat
      (mapv (fn [e] {:from (:source e) :to "kanmon" :v (:volume e) :kind :in}) evs)
      (mapv (fn [e] {:from "kanmon" :to (:target e) :v (:value e) :kind :rectified}) evs)
      (mapv (fn [e] {:from (:target e) :to (:sink e) :v (:value e) :kind :export}) evs))}))

;; ── self-contained HTML viz (model inlined; no external fetch) ───────────────
(defn- json-esc [s] (-> (str s) (str/replace "\\" "\\\\") (str/replace "\"" "\\\"")))
(defn ->json [v]
  (cond
    (map? v) (str "{" (str/join "," (map (fn [[k vv]] (str "\"" (json-esc (if (keyword? k) (name k) k)) "\":" (->json vv))) v)) "}")
    (sequential? v) (str "[" (str/join "," (map ->json v)) "]")
    (keyword? v) (str "\"" (name v) "\"")
    (string? v) (str "\"" (json-esc v) "\"")
    (boolean? v) (if v "true" "false")
    (number? v) (if (and (number? v) (Double/isInfinite (double v))) "\"∞\"" (str v))
    (nil? v) "null"
    :else (str "\"" (json-esc v) "\"")))

(defn render-html [model]
  (str "<!doctype html><html lang=\"ja\"><head><meta charset=\"utf-8\">\n"
       "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">\n"
       "<title>kanmon 関門 — energy-flow (ie SoS)</title>\n"
       "<style>:root{--bg:#0d1117;--fg:#e6edf3;--mut:#8b949e;--card:#161b22;--line:#30363d}"
       "*{box-sizing:border-box}html,body{margin:0;background:var(--bg);color:var(--fg);"
       "font-family:-apple-system,'Hiragino Sans','Noto Sans JP',system-ui,sans-serif}"
       ".wrap{max-width:1280px;margin:0 auto;padding:20px}h1{font-size:18px;margin:0 0 2px}"
       ".sub{color:var(--mut);font-size:13px;margin:0 0 14px}.metrics{display:flex;flex-wrap:wrap;gap:10px;margin:0 0 16px}"
       ".m{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:9px 13px;min-width:120px}"
       ".m .k{color:var(--mut);font-size:11px}.m .v{font-size:19px;font-weight:650;margin-top:2px}.m .v.good{color:#3fb950}"
       "canvas{width:100%;height:auto;background:var(--card);border:1px solid var(--line);border-radius:12px}"
       ".note{color:var(--mut);font-size:12px;line-height:1.6;margin-top:12px;border-top:1px solid var(--line);padding-top:12px}</style>\n"
       "</head><body><div class=\"wrap\">\n"
       "<h1>kanmon 関門 — how the actor turns exam-gate causality into wellbecoming (ie · system of systems)</h1>\n"
       "<p class=\"sub\">散在する barrier-load (disorder) → kanmon 整流 (rectifier) → 高レバレッジ OPENING (order) → 下流 wellbecoming アクター</p>\n"
       "<div class=\"metrics\" id=\"metrics\"></div>\n"
       "<canvas id=\"c\" width=\"1240\" height=\"560\"></canvas>\n"
       "<div class=\"note\"><b>整流 (rectification)</b>: order-index = 1 − H(after)/H(before) — kanmon が散在した barrier-load を"
       " 高レバレッジ OPENING (脱・一発勝負 / 代替経路 / 開示 / 公平) へ集中させた度合い。<b>η = 輸出 ÷ 消費</b> ="
       " kanmon が安価な観測で生む wellbecoming-order の倍率 (子孫軸; ≫1 = 利得)。kanmon は学生も金も動かさない —"
       " 動かすのは<b>情報-エネルギー</b> (OPENING 地図) であり、実際の開放は ossekai/Council。これが <b>system of systems</b>。</div>\n"
       "<script>\nconst M=" (->json model) ";\n"
       "const mc=document.getElementById('metrics');"
       "[['order-index',M.metrics['order-index'],true],['η (export÷consume)',M.metrics.eta],['net-gain',M.metrics['net-gain'],true],"
       "['throughput',M.metrics.throughput],['H before→after',M.metrics['h-before']+'→'+M.metrics['h-after']]]"
       ".forEach(([k,v,g])=>{const d=document.createElement('div');d.className='m';"
       "d.innerHTML='<div class=\\'k\\'>'+k+'</div><div class=\\'v'+(g?' good':'')+'\\'>'+v+'</div>';mc.appendChild(d);});\n"
       "const cv=document.getElementById('c'),x=cv.getContext('2d');const W=1240,H=560;"
       "const cols=M.columns;const cx=[80,420,760,1120];x.font='12px sans-serif';"
       "cols.forEach((col,ci)=>{x.fillStyle='#8b949e';x.fillText(col.label,cx[ci]-40,24);"
       "col.nodes.forEach((n,ni)=>{const y=60+ni*34;n._x=cx[ci];n._y=y;x.fillStyle='#1f6feb';"
       "x.fillRect(cx[ci]-36,y-10,72,18);x.fillStyle='#e6edf3';x.fillText((n.label||n.id).slice(0,9),cx[ci]-33,y+3);});});\n"
       "function find(id){for(const c of cols)for(const n of c.nodes)if(n.id===id)return n;return null;}"
       "M.links.forEach(l=>{const a=find(l.from),b=find(l.to);if(!a||!b)return;x.strokeStyle=l.kind==='export'?'#3fb950':'#30363d';"
       "x.globalAlpha=0.5;x.beginPath();x.moveTo(a._x+36,a._y);x.lineTo(b._x-36,b._y);x.stroke();x.globalAlpha=1;});\n"
       "</script></div></body></html>\n"))

;; ── record to the shared ie-flow ledger (heartbeat/operator step) ────────────
#?(:clj
   (defn record-flow!
     "Append the measured flow summary to the shared ie-flow ledger (gitignored).
      Returns the summary map."
     [exam-rows log-path]
     (let [m (metrics exam-rows)
           f (clojure.java.io/file log-path)]
       (when-let [p (.getParentFile f)] (.mkdirs p))
       (spit f (str (pr-str {:actor "kanmon" :metrics m
                             :summary (ie/summary-line (flow-state exam-rows))}) "\n")
             :append true)
       m)))

#?(:clj
   (defn -main [& args]
     (let [seed (or (first args) "20-actors/kanmon/kotoba/seed.edn")
           out (or (second args) "20-actors/kanmon/viz/energy-flow.html")
           exams (vec (filter #(= (:type %) :exam) (clojure.edn/read-string (slurp seed))))
           rows (get (az/assess exams) "exams")
           model (viz-model rows)]
       (spit out (render-html model))
       (println (ie/summary-line (flow-state rows)))
       (println (str "wellbecoming-served=" (:wellbecoming-served (metrics rows))
                     " order-index=" (:order-index (metrics rows))
                     " η=" (:eta (metrics rows))))
       (println (str "viz → " out)))))

#?(:clj
   (when (= *file* (System/getProperty "babashka.file"))
     (apply -main *command-line-args*)))
