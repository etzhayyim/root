(ns yoro-ui.components.streak-badge
  "Port of svelte/src/lib/components/StreakBadge.svelte"
  (:require [reagent.core :as r]
            [yoro-ui.interop.sound :as snd]))

(def storage-key "yoro_streak")

(defn- today-str []
  (subs (.toISOString (js/Date.)) 0 10))

(defn- init-streak []
  (let [raw (if (exists? js/localStorage)
              (try (.getItem js/localStorage storage-key) (catch js/Error _ nil))
              nil)
        data (if raw (js->clj (js/JSON.parse raw) :keywordize-keys true)
                 {:count 0 :lastDate "" :xp 0})
        today (today-str)
        yesterday (subs (.toISOString (js/Date. (- (.now js/Date) 86400000))) 0 10)]
    (cond
      (= (:lastDate data) today) data
      (= (:lastDate data) yesterday)
      {:count (inc (:count data)) :lastDate today :xp (+ (:xp data) 10)}
      :else
      {:count 1 :lastDate today :xp (+ (or (:xp data) 0) 10)})))

(defn- save-streak! [streak]
  (when (exists? js/localStorage)
    (try
      (.setItem js/localStorage storage-key (js/JSON.stringify (clj->js streak)))
      (catch js/Error _))))

(defonce streak-state (r/atom nil))
(defonce just-leveled-up (r/atom false))

(defn add-xp! [amount]
  (let [curr @streak-state
        new-streak (assoc curr :xp (+ (:xp curr) amount))]
    (reset! streak-state new-streak)
    (save-streak! new-streak)))

(defn streak-badge
  "Form-2 reagent component — setup body runs once per mount (svelte onMount
   equivalent). React hooks must not be used here: reagent renders this as a
   class component, so useEffect would throw and blank the whole tree."
  [_props]
  (let [init-data (init-streak)]
    (reset! streak-state init-data)
    (when (and (pos? (:count init-data)) (zero? (mod (:count init-data) 7)))
      (reset! just-leveled-up true)
      (snd/play-level-up!)
      (js/setTimeout #(reset! just-leveled-up false) 2000))
    (save-streak! init-data))
  (fn [{:keys [class]}]
    (let [streak @streak-state
          lvl-up @just-leveled-up
          cnt (:count streak 0)
          xp (:xp streak 0)
          flame-color (cond
                        (>= cnt 30) "text-purple-400"
                        (>= cnt 14) "text-orange-400"
                        (>= cnt 7)  "text-yellow-400"
                        :else       "text-orange-300")]
      [:div {:class (str "flex items-center gap-3 " class)}
       [:div.flex.items-center.gap-1
        [:span {:class (str "text-[20px] " (when lvl-up "animate-spin"))
                :title (str cnt " 日連続！")}
         "🔥"]
        [:span {:class (str "text-[14px] font-bold " flame-color)} cnt]]
       [:div.flex.items-center.gap-1
        [:span {:class "text-[16px]"} "⚡"]
        [:span {:class "text-[13px] font-semibold text-yellow-400"} (str xp " XP")]]])))
