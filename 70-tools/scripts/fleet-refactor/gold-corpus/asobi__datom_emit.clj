;; ported from 20-actors/asobi/methods/datom_emit.py — gold reference (Fable)
;; asobi 遊び — kotoba Datom-log emitter (canonical EAVT state, ADR-2605312345).
;; freed-time play/expression graph を append-only kotoba Datom [e a v tx op] へ射影する。
;;
;;   GROUND (durable, op :add) — node + 縁 datoms。これが Datom log そのもの。
;;   DERIVED (transient, :bond/is-transient) — openness/enclosure 積分。READ 時計算で
;;     永続化しない (N1/G2)。
;;
;; Clojure では文字列を組み立てず、データ (datom ベクタの列) を返すのが正準。
;; 直列化が要るときだけ呼び出し側が pr-str する。
(ns asobi.methods.datom-emit)

(def node-attrs
  [:organism/kind :organism/label :organism/sourcing
   :work/medium :work/access :practice/domain :practice/body?
   :venue/kind :venue/open? :enclosure/kind :enclosure/links])

(def edge-attrs
  [:en/from :en/to :en/kind :en/access-load :en/sourcing])

(defn- node-datoms
  "1 ノードの GROUND datom 群。nil 値属性は出さない。"
  [eid node tx]
  (for [a node-attrs
        :let [v (get node a)]
        :when (some? v)]
    [eid a v tx :add]))

(defn- edge-id
  "縁の決定的 entity-id。:en/kind の先頭 ':' は剥がす。"
  [edge]
  (let [k (name (:en/kind edge))]
    (str "en." (:en/from edge) "." k "." (:en/to edge))))

(defn- edge-datoms [edge tx]
  (let [eid (edge-id edge)]
    (for [a edge-attrs
          :let [v (get edge a)]
          :when (some? v)]
      [eid a v tx :add])))

(defn- derived-datoms
  "DERIVED 読み出し (transient): {eid value} を降順で :derived datom 群へ。"
  [attr m tx]
  (for [[eid v] (sort-by (comp - val) m)]
    [eid attr v tx :derived]))

(defn emit
  "nodes {eid node} / edges [edge…] / res {:openness… :enclosure… :enclosure-out…}
  → GROUND + DERIVED datom のベクタ。直列化は呼び出し側の責務。"
  ([nodes edges res] (emit nodes edges res 1))
  ([nodes edges res tx]
   (vec
    (concat
     (mapcat (fn [[eid node]] (node-datoms eid node tx)) nodes)
     (mapcat #(edge-datoms % tx) edges)
     (derived-datoms :bond/participation-openness (:openness res) tx)
     (derived-datoms :bond/enclosure-load (:enclosure res) tx)
     (derived-datoms :bond/enclosure-imposed (:enclosure-out res) tx)))))
