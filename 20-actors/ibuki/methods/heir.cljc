(ns ibuki.methods.heir
  "moyai heir-decay — the organism's Wellbecoming gradient flows forward to 子・孫 (ADR-2606172000).

  §1.10 of the Charter inverts ordinary discounting: the objective function maximizes the
  wellbecoming of 子・孫 and beyond, OVER the present generation's static wellbeing. So when the
  organism becomes-well (a positive Wellbecoming `net`, wellbecoming.cljc), it does NOT consume
  all of that reward now — it keeps only a subsistence floor (§1.16) and MINTS the rest forward
  to heir generations with a per-generation decay. The decay is across GENERATIONS (child →
  grandchild → …), not wall-clock time: value reaches descendants but attenuates (the infinite
  future cannot be perfectly provisioned), while the present generation is structurally NOT the
  terminus of value.

  moyai semantics are preserved (ADR-2606082100): the shares are non-transferable, decaying,
  cash≡0 reciprocity credit minted to LINEAGE EDGES (`:heir/*`), never a per-soul balance or
  score (edge-primary; yir'ah no-score-of-soul). A declining organism mints nothing (you cannot
  gift a gain you did not make). Pure, deterministic, stdlib."
  (:require [ibuki.methods.datoms :as d]))

(def defaults
  "self-floor = the subsistence fraction the present keeps (§1.16 floor; small — 子孫 priority).
   decay      = per-generation attenuation of the forward flow (child gets most, then less).
   generations = how many heir generations downstream receive a share (child, grandchild, …)."
  {:self-floor 0.2 :decay 0.5 :generations 3})

(defn heir-shares
  "Split a Wellbecoming `net` gain into {:self f0 :heirs [{:generation g :share s} …]}.
   net ≤ 0 → no mint (nothing to give). The forward flow (1 − self-floor)·net is distributed
   over `generations` with weights decay^(g-1), normalized so the heirs together receive exactly
   the forward flow (no value created or lost — circular, 非終末論)."
  ([net] (heir-shares net defaults))
  ([net {:keys [self-floor decay generations] :as opts}]
   (if (<= net 0)
     {:self 0.0 :heirs [] :minted 0.0}
     (let [self (* self-floor net)
           forward (- net self)
           weights (map (fn [g] (Math/pow decay g)) (range generations))
           total-w (reduce + weights)
           heirs (map-indexed
                  (fn [i w] {:generation (inc i)
                             :share (* forward (/ w total-w))})
                  weights)]
       {:self self :heirs (vec heirs) :minted forward}))))

(defn heir-datoms
  "Mint the forward flow as `:heir/*` LINEAGE-EDGE datoms (new entity per generation per beat;
   append-only). Non-transferable, decaying, cash≡0 — and pointedly NO per-soul balance/score
   attribute (edge-primary, §1.10 + yir'ah)."
  [of net {:keys [beat as-of] :as ctx} & [opts]]
  (let [{:keys [heirs minted]} (heir-shares net (merge defaults opts))]
    (into []
          (mapcat (fn [{:keys [generation share]}]
                    (let [e (str "heir-" of "-" beat "-g" generation)]
                      [(d/add e ":heir/of" of)
                       (d/add e ":heir/beat" beat)
                       (d/add e ":heir/as-of" as-of)
                       (d/add e ":heir/generation" generation)   ;; 1=子 2=孫 3=曾孫 …
                       (d/add e ":heir/share" share)
                       (d/add e ":heir/non-transferable" true)]))
                  heirs))))
