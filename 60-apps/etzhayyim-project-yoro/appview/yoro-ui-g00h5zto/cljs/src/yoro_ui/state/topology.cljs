(ns yoro-ui.state.topology
  (:require [re-frame.core :as rf]))

(def buffer-size 50)
(def storage-key "yoro-session-topology-v1")

(defn load-persisted []
  (if (not (exists? js/sessionStorage))
    {:sessionStart (.now js/Date) :topics []}
    (try
      (let [raw (.getItem js/sessionStorage storage-key)]
        (if-not raw
          {:sessionStart (.now js/Date) :topics []}
          (let [parsed (js->clj (js/JSON.parse raw) :keywordize-keys true)
                start (:sessionStart parsed)
                topics (:topics parsed)]
            {:sessionStart (if (number? start) start (.now js/Date))
             :topics (if (coll? topics)
                       (take-last buffer-size (filter string? topics))
                       [])})))
      (catch js/Error _
        {:sessionStart (.now js/Date) :topics []}))))

(defn save-persisted [state]
  (when (exists? js/sessionStorage)
    (try
      (.setItem js/sessionStorage storage-key (js/JSON.stringify (clj->js state)))
      (catch js/Error _))))

;; We use a defonce atom for local fast synchronous access
(defonce state (atom (load-persisted)))

(defn record-topic-visit [topic]
  ;; TS original rejects falsy "" — cljs "" is truthy, so check length explicitly
  (when (and topic (pos? (count (str topic))))
    (let [t (subs (str topic) 0 (min (count (str topic)) 64))
          curr-state @state
          topics (:topics curr-state)
          new-topics (take-last buffer-size (concat topics [t]))
          new-state (assoc curr-state :topics new-topics)]
      (reset! state new-state)
      (save-persisted new-state))))

(defn reset-session-topology []
  (let [new-state {:sessionStart (.now js/Date) :topics []}]
    (reset! state new-state)
    (save-persisted new-state)))

(defn get-session-topology []
  (let [curr-state @state
        topics (:topics curr-state)
        total (count topics)
        distinct (count (set topics))
        echo-persistence (if (zero? total) 0 (- 1 (/ distinct total)))]
    {:echoPersistence echo-persistence
     :distinctTopics distinct
     :dwellMs (max 0 (- (.now js/Date) (:sessionStart curr-state)))
     :sampleSize total}))

(defn is-doom-scrolling? [& {:keys [night-mode stress-idx]
                             :or {night-mode false stress-idx 0}}]
  (let [limit (if night-mode (* 20 60 1000) (* 45 60 1000))
        snap (get-session-topology)]
    (and (> (:dwellMs snap) limit)
         (or (> stress-idx 70) night-mode))))
