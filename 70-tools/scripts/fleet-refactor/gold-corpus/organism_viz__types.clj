;; ported from 60-apps/etzhayyim-organism-viz/web/src/lib/types.ts — gold reference (Fable)
;; organism-viz の型定義。TS interface は Clojure では「データ shape の仕様」になる。
;; defrecord ではなく、namespaced-keyword の plain map + コンストラクタ + 既定値で表す
;; (kotoba は data-oriented; nominal type ではなく shape で扱う)。
(ns organism-viz.types)

(def entity-kinds
  #{:axis :cell :app :adr :organism :ecosystem :fruit :seed})

(defn entity
  "Entity shape のコンストラクタ。欠けたフィールドは既定値で埋める。"
  [{:keys [id kind title state activity chat-invite neighbors pruning-severity]}]
  {:id id
   :kind kind
   :title title
   :state (or state {})
   :activity (or activity [])
   :chat-invite (or chat-invite "")
   :neighbors (or neighbors [])
   :pruning-severity (or pruning-severity 0)})

(defn alive-tuple
  "Wellbecoming の生存度タプル M/D/C/P/G。"
  [{:keys [m-motion d-diversity c-coupling p-pruning g-generational
           timestamp notes]}]
  {:m-motion m-motion
   :d-diversity d-diversity
   :c-coupling c-coupling
   :p-pruning p-pruning
   :g-generational g-generational
   :timestamp timestamp
   :notes (or notes [])})

(defn pruning-candidate
  [{:keys [id kind path idle-days severity reasons]}]
  {:id id :kind kind :path path
   :idle-days idle-days :severity severity
   :reasons (or reasons [])})

(defn node-pos
  "力学レイアウト用のノード位置 (x/y/速度/視覚半径/呼吸位相)。"
  [{:keys [id kind x y vx vy r phase]}]
  {:id id :kind kind
   :x x :y y :vx vx :vy vy
   :r r          ; visual radius (shape sizing + collisions)
   :phase phase}) ; breathing phase
