#!/usr/bin/env bb
;; shinogi 鎬 — wellbecoming ENERGY-FLOW design (clj-native, pure stdlib).
(ns shinogi.methods.energy-flow
  "energy_flow.cljc — shinogi 鎬 designs the EFFORT-ENERGY FLOW that turns the
  involution causality into WELLBECOMING (ADR-2606291200, §1.13 Wellbecoming).

  THE IDEA (the uzu 渦 dissipative-energy view, ADR-2606211500, applied to the
  exam society). A society pours an enormous EFFORT-ENERGY flow (hours / spend /
  striving) into the system. Today most of it flows into the ZERO-SUM channels of
  the involution — the 内卷 arms race, credential chasing — where it DISSIPATES:
  effort goes in, the ranking is unchanged, wellbeing erodes, and almost no
  aggregate wellbecoming comes out (the 鎬を削る waste). The vicious reinforcing
  loops ARE the dissipative channels; the balancing loops + intrinsic learning ARE
  the productive ones.

  So shinogi designs a RE-ROUTING of the SAME effort-energy from dissipative
  channels into wellbecoming-yielding ones — maximizing wellbecoming per unit
  effort, conserving the total flow, gradually (a structural DESIGN, never coercing
  any individual). The output also yields drive-overrides that simulate.cljc rolls
  forward to show the vicious→virtuous flip.

  TWO LEDGERS, NEVER THE SAME UNIT (uzu G1/G2): EFFORT-ENERGY is a conserved FLOW
  (allocation fractions sum to 1.0); WELLBECOMING is a separate dynamic INDEX
  (§1.13 trajectory). `:yield` is wellbecoming-per-unit-effort — a REFERENCE
  coupling, never an identity; the two are never summed into one unit.

  DISCIPLINE: this is a DESIGN / CANDIDATE (G11, `:prescription? false`), a
  STRUCTURAL re-routing (§1.4 — it changes systemic effort allocation, it never
  directs a person), a relief MAP (G7+G8), no outward channel (G4). Deterministic;
  pure; no I/O."
  (:require [clojure.string :as str]))

;; ── the effort-energy CHANNELS (DISCLOSED + auditable) ───────────────────────
;; :yield  = wellbecoming per unit effort (reference coupling; can be negative = dissipative)
;; :current= today's share of the effort-energy flow (the channels sum to 1.0)
;; :floor/:ceiling = how far the share may move (gradual, never to 0 or 1)
;; :relieves = which pressure stocks a wellbecoming-ward move on this channel relieves
(def channels
  [{:id :zero-sum-ranking   :label "内卷 zero-sum ranking scramble" :yield -0.30 :current 0.45 :floor 0.12 :ceiling 0.60
    :relieves {:effort-inflation 0.6 :positional-scarcity 0.4}}
   {:id :credential-chase   :label "文凭 credential chasing (考研/考公)" :yield -0.10 :current 0.20 :floor 0.06 :ceiling 0.30
    :relieves {:credential-signaling 1.0}}
   {:id :alternative-pathways :label "代替経路 (vocational / multiple routes; manabi+de-dual)" :yield 0.50 :current 0.10 :floor 0.05 :ceiling 0.40
    :relieves {:positional-scarcity 0.5 :failure-penalty 0.5}}
   {:id :wellbeing-protection :label "ウェルビーイング保護 (rest / health / balance; 双减)" :yield 0.60 :current 0.08 :floor 0.04 :ceiling 0.35
    :relieves {:wellbeing-erosion 1.0}}
   {:id :labor-absorption   :label "労働吸収 (job creation / grassroots / decouple from one exam)" :yield 0.45 :current 0.07 :floor 0.04 :ceiling 0.35
    :relieves {:labor-absorption-deficit 1.0}}
   {:id :intrinsic-learning :label "内発的学び (learning for capability & meaning, not ranking; manabi)" :yield 0.70 :current 0.10 :floor 0.05 :ceiling 0.40
    :relieves {:effort-efficacy-collapse 0.5 :effort-inflation 0.5}}])

(def ^:private max-shift 0.40)        ;; total effort re-routed (gradualism / non-coercion)
(def ^:private route-scale 0.8)       ;; effort-shift → stock-relief scaling
(defn- round3 [x] (/ (Math/round (* (double x) 1000.0)) 1000.0))

(defn wellbecoming
  "Σ allocation·yield over channels — the wellbecoming INDEX of an allocation
  {channel-id share}. (Index units, NOT energy units — uzu G2.)"
  [alloc]
  (round3 (reduce + (map (fn [c] (* (double (get alloc (:id c))) (:yield c))) channels))))

(defn design
  "Greedy re-routing: drain effort from the lowest-yield channels (down to floor) into
  the highest-yield channels (up to ceiling), conserving the total flow, bounded by
  max-shift. Returns the current vs designed allocation, the wellbecoming gain, the
  per-channel moves, and drive-overrides for simulate.cljc. A DESIGN/CANDIDATE (G11)."
  []
  (let [cur (into {} (map (juxt :id :current) channels))
        ;; donors: yield ascending (drain worst first); receivers: yield descending
        donors (sort-by :yield channels)
        receivers (reverse (sort-by :yield channels))
        ;; pull budget from donors down toward floor (cap total at max-shift)
        [alloc1 budget]
        (reduce (fn [[a left] c]
                  (if (<= left 0) [a left]
                      (let [avail (max 0.0 (- (get a (:id c)) (:floor c)))
                            take (min avail left)]
                        [(update a (:id c) - take) (- left take)])))
                [cur max-shift] donors)
        pulled (- max-shift budget)
        ;; push the pulled budget into receivers up toward ceiling
        [alloc2 _]
        (reduce (fn [[a left] c]
                  (if (<= left 0) [a left]
                      (let [room (max 0.0 (- (:ceiling c) (get a (:id c))))
                            put (min room left)]
                        [(update a (:id c) + put) (- left put)])))
                [alloc1 pulled] receivers)
        designed alloc2
        moves (vec (for [c channels
                         :let [d (round3 (- (get designed (:id c)) (:current c)))]]
                     {:id (:id c) :label (:label c) :yield (:yield c)
                      :current (:current c) :designed (round3 (get designed (:id c)))
                      :delta d}))
        ;; wellbecoming-ward magnitude per channel: positive-yield up OR negative-yield down
        relief-mag (fn [c]
                     (let [d (- (get designed (:id c)) (:current c))]
                       (cond (and (pos? (:yield c)) (pos? d)) d
                             (and (neg? (:yield c)) (neg? d)) (- d)
                             :else 0.0)))
        overrides (reduce (fn [acc c]
                            (let [m (relief-mag c)]
                              (reduce (fn [a [stock w]]
                                        (update a stock (fnil - 0.0) (* route-scale m (double w))))
                                      acc (:relieves c))))
                          {} channels)]
    {:current-allocation (into {} (map (fn [[k v]] [(name k) (round3 v)]) cur))
     :designed-allocation (into {} (map (fn [[k v]] [(name k) (round3 v)]) designed))
     :current-wellbecoming (wellbecoming cur)
     :designed-wellbecoming (wellbecoming designed)
     :wellbecoming-gain (round3 (- (wellbecoming designed) (wellbecoming cur)))
     :effort-re-routed (round3 pulled)
     :moves moves
     :drive-overrides (into {} (map (fn [[k v]] [k (round3 v)]) overrides))
     :two-ledger-note "EFFORT-ENERGY is a conserved FLOW (shares sum to 1.0); WELLBECOMING is a separate INDEX (§1.13). :yield is wellbecoming-per-unit-effort — a reference coupling, never an identity (uzu G1/G2); the two units are never summed."
     :prescription? false
     :hypothesis? true}))

;; ── datom emission (append-only EAVT; DESIGN/CANDIDATE; HYPOTHESIS) ───────────
(defn- add [e a v] [":db/add" e a v])

(defn datoms
  "Append-only EAVT datoms for the energy-flow design (per-channel moves + the gain).
  Carries :prescription? false (G11 candidate, never a directive)."
  [d]
  (vec (concat
        [(add "shinogi-energy:design" ":shinogi.exam.energy/current-wellbecoming" (:current-wellbecoming d))
         (add "shinogi-energy:design" ":shinogi.exam.energy/designed-wellbecoming" (:designed-wellbecoming d))
         (add "shinogi-energy:design" ":shinogi.exam.energy/wellbecoming-gain" (:wellbecoming-gain d))
         (add "shinogi-energy:design" ":shinogi.exam.energy/effort-re-routed" (:effort-re-routed d))
         (add "shinogi-energy:design" ":shinogi/prescription" ":false")
         (add "shinogi-energy:design" ":shinogi/hypothesis" ":true")
         (add "shinogi-energy:design" ":shinogi/derived" true)]
        (for [m (:moves d)]
          (add (str "shinogi-energy-channel:" (name (:id m)))
               ":shinogi.exam.energy/delta" (:delta m))))))

(defn render-report [d]
  (str
   "## Wellbecoming ENERGY-FLOW design — re-routing the involution's effort (HYPOTHESIS, G5; CANDIDATE, G11)\n\n"
   "_社会が注ぐ努力エネルギーは今、内卷の零和チャネルで**散逸**している(効力ゼロ、ウェルビーイング低下)。"
   "同じエネルギーを wellbecoming を生むチャネルへ**再配線**する設計。**二つの台帳は決して同一単位にしない**"
   "(uzu G1/G2): 努力=保存される流れ(合計1.0)、wellbecoming=別の指標(§1.13)。これは構造的 DESIGN であって"
   "個人への指令ではない(§1.4 / G11)。_\n\n"
   "- current wellbecoming: **" (:current-wellbecoming d) "** → designed: **" (:designed-wellbecoming d) "**"
   " (**gain " (:wellbecoming-gain d) "**; effort re-routed " (:effort-re-routed d) ")\n\n"
   "| channel | yield (wb/effort) | current | designed | Δ |\n|---|---|---|---|---|\n"
   (str/join "\n"
             (for [m (:moves d)]
               (str "| " (:label m) " | " (:yield m) " | " (:current m)
                    " | " (:designed m) " | " (:delta m) " |")))
   "\n\n_負の yield チャネル(散逸)から正の yield チャネル(wellbecoming 生成)へ effort を移す。"
   "drive-overrides を simulate.cljc に渡すと vicious→virtuous の反転が時系列で見える。_\n"))

;; ── CLI (bb) ─────────────────────────────────────────────────────────────────
#?(:clj
   (defn -main [& _]
     (println (render-report (design)))))

#?(:clj
   (when (= *file* (System/getProperty "babashka.file"))
     (apply -main *command-line-args*)))
