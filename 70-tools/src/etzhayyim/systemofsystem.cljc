;; etzhayyim.systemofsystem — System-of-Systems (SoS) analysis (cljc port, wave-4b).
;;
;; Pure-logic port of 70-tools/etzhayyim-py/src/etzhayyim/systemofsystem.py
;; (no click, no subprocess, no network I/O — _scan_workspace leg is deferred).
;;
;; API:
;;   (cohesion             cluster)       → float 0..1
;;   (cluster-layer        cluster-name)  → "identity" | "interface" | "infra" | "inference" | "data" | "app"
;;   (build-nanoid-map     clusters)      → {nanoid → cluster-name}
;;   (coupling-score       edges nanoid-map) → float 0..100
;;   (cohesion-score       edges nanoid-map) → float 0..100
;;   (sos-health-verdict   coupling cohesion) → "HEALTHY" | "ACCEPTABLE" | "NEEDS ATTENTION"
;;   (sos-health           clusters apps edges) → {:clusters :actors :edges :coupling_score
;;                                                  :cohesion_score :verdict}
;;   (cross-cluster-pairs  clusters edges)  → sorted [{:from :to :edge_count}]
;;   (layer-groups         clusters)        → {layer-str [cluster-name ...]}
;;
;; Cluster map keys: :name :nanoids :internal_edges :external_edges
;; Edge map keys: :from_nanoid :to_nanoid
;; App map keys: :nanoid
;;
;; IO leg (deferred): _scan_workspace + kotodama.jsonld walk live fs.
;;   cluster-by-project is not ported (it requires fs access + HaisenReport).
;;   At runtime: supply clusters built externally and call the pure fns above.
;;
;; bb usage (classpath 70-tools/src):
;;   (require '[etzhayyim.systemofsystem :as sos])
;;   (sos/cluster-layer "murakumo")

(ns etzhayyim.systemofsystem
  (:require [clojure.string :as str]))

;; ── cohesion ──────────────────────────────────────────────────────────────────

(defn cohesion
  "Compute cluster cohesion = internal-edges / (internal + external).
   Mirrors SoSCluster.cohesion property in systemofsystem.py."
  [{:keys [internal_edges external_edges]}]
  (let [total (+ (or internal_edges 0) (or external_edges 0))]
    (/ (double (or internal_edges 0)) (max total 1))))

;; ── layer mapping ─────────────────────────────────────────────────────────────

(def ^:private layer-map
  "Ordered list of [keywords-that-match layer-name].
   Mirrors _LAYER_MAP in systemofsystem.py."
  [[["auth" "authn" "authz"]    "identity"]
   [["yoro" "chat" "ui"]       "interface"]
   [["pds" "infra" "deploy"]   "infra"]
   [["murakumo" "inference" "llm"] "inference"]
   [["data" "graph" "db"]      "data"]])

(defn cluster-layer
  "Classify a cluster name into an architectural layer.
   Mirrors _cluster_layer in systemofsystem.py."
  [cluster-name]
  (or (some (fn [[keywords layer]]
              (when (some #(str/includes? cluster-name %) keywords)
                layer))
            layer-map)
      "app"))

;; ── nanoid → cluster lookup ───────────────────────────────────────────────────

(defn build-nanoid-map
  "Build a {nanoid → cluster-name} lookup from a seq of cluster maps.
   clusters – seq of {:name :nanoids ...}
   Mirrors nanoid_to_cluster in sos_scan / sos_health / sos_interfaces."
  [clusters]
  (into {} (for [{:keys [name nanoids]} clusters
                 n nanoids]
             [n name])))

;; ── coupling / cohesion scores ────────────────────────────────────────────────

(defn coupling-score
  "cross-cluster-edges / total-edges × 100, rounded to 1 dp.
   edges      – seq of {:from_nanoid :to_nanoid}
   nanoid-map – {nanoid → cluster-name} from build-nanoid-map"
  [edges nanoid-map]
  (let [total      (max (count edges) 1)
        cross      (count (filter (fn [{:keys [from_nanoid to_nanoid]}]
                                    (not= (nanoid-map from_nanoid)
                                          (nanoid-map to_nanoid)))
                                  edges))]
    (-> (* (/ (double cross) total) 100.0) (* 10) Math/round (/ 10.0))))

(defn cohesion-score
  "intra-cluster-edges / total-edges × 100, rounded to 1 dp."
  [edges nanoid-map]
  (let [total  (max (count edges) 1)
        intra  (count (filter (fn [{:keys [from_nanoid to_nanoid]}]
                                (= (nanoid-map from_nanoid)
                                   (nanoid-map to_nanoid)))
                              edges))]
    (-> (* (/ (double intra) total) 100.0) (* 10) Math/round (/ 10.0))))

;; ── health verdict ────────────────────────────────────────────────────────────

(defn sos-health-verdict
  "Classify coupling/cohesion into a health verdict string.
   Mirrors sos_health logic in systemofsystem.py."
  [coupling cohesion]
  (cond
    (and (< coupling 20) (> cohesion 60)) "HEALTHY"
    (and (< coupling 40) (> cohesion 40)) "ACCEPTABLE"
    :else                                  "NEEDS ATTENTION"))

(defn sos-health
  "Compute full SoS health stats map.
   clusters – seq of {:name :nanoids :internal_edges :external_edges}
   apps     – seq of {:nanoid}
   edges    – seq of {:from_nanoid :to_nanoid}
   Mirrors sos_health command in systemofsystem.py."
  [clusters apps edges]
  (let [nanoid-map  (build-nanoid-map clusters)
        coupling    (coupling-score edges nanoid-map)
        coh         (cohesion-score edges nanoid-map)
        verdict     (sos-health-verdict coupling coh)]
    {:clusters      (count clusters)
     :actors        (count apps)
     :edges         (count edges)
     :coupling_score coupling
     :cohesion_score  coh
     :verdict        verdict}))

;; ── cross-cluster interface pairs ────────────────────────────────────────────

(defn cross-cluster-pairs
  "Aggregate inter-cluster edge counts by (from-cluster, to-cluster) pair.
   Returns sorted list of {:from :to :edge_count}.
   Mirrors sos_interfaces command in systemofsystem.py."
  [clusters edges]
  (let [nanoid-map (build-nanoid-map clusters)
        pair-counts
        (reduce (fn [acc {:keys [from_nanoid to_nanoid]}]
                  (let [fc (nanoid-map from_nanoid)
                        tc (nanoid-map to_nanoid)]
                    (if (and fc tc (not= fc tc))
                      (update acc [fc tc] (fnil inc 0))
                      acc)))
                {}
                edges)]
    (sort-by #(- (:edge_count %))
             (map (fn [[[from to] cnt]]
                    {:from from :to to :edge_count cnt})
                  pair-counts))))

;; ── layer groups ─────────────────────────────────────────────────────────────

(defn layer-groups
  "Group cluster names by architectural layer.
   clusters – seq of {:name ...}
   Returns {layer-string [cluster-name ...]} sorted by layer name.
   Mirrors sos_layers command in systemofsystem.py."
  [clusters]
  (reduce (fn [acc {:keys [name]}]
            (let [layer (cluster-layer name)]
              (update acc layer (fnil conj []) name)))
          {}
          clusters))
