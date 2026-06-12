(ns yoro-ui.components.no-cookie-banner
  "Port of svelte/src/lib/components/NoCookieBanner.svelte"
  (:require [reagent.core :as r]
            [yoro-ui.components.brainrot-mascot :refer [brainrot-mascot]]))

(def storage-key "yoro-no-cookie-seen")

(defn- banner-host?
  "Original gates to religious-corp hosts; localhost added for cljs dev."
  []
  (if-not (exists? js/window)
    false
    (let [h (.-hostname js/window.location)]
      (or (= h "etzhayyim.com")
          (.endsWith h ".etzhayyim.com")
          (= h "localhost")
          (= h "127.0.0.1")))))

(defn no-cookie-banner
  "Form-2 reagent component — visibility timer scheduled once in setup
   (svelte onMount equivalent), no React hooks (class component context)."
  []
  (let [visible? (r/atom false)]
    (when (and (exists? js/window) (banner-host?))
      (when-not (try (.getItem js/localStorage storage-key) (catch js/Error _ nil))
        (js/setTimeout #(reset! visible? true) 1500)))
    (fn []
      (when @visible?
        [:div {:class "fixed bottom-20 left-1/2 z-[55] w-[92vw] max-w-[380px] -translate-x-1/2"}
         [:div {:class "relative overflow-hidden rounded-3xl bg-gv2-bg-card/95 shadow-2xl backdrop-blur-md border border-gv2-border/30"}
          [:div {:class "h-1 bg-gradient-to-r from-[#58CC02] via-[#FFD700] to-[#FF6B9D]"}]

          [:div {:class "flex items-start gap-3 px-4 pt-4 pb-3"}
           [:div {:class "flex-shrink-0 -mt-1"}
            [brainrot-mascot {:size 56 :mood :happy}]]

           [:div {:class "flex-1 min-w-0"}
            [:div {:class "rounded-2xl bg-[#58CC02]/15 px-3 py-2 mb-2"}
             [:p {:class "text-[13px] font-bold text-[#58CC02] leading-snug"}
              "no cap, we don't track you fr fr"]]

            [:p {:class "text-[13px] text-gv2-text-primary leading-relaxed font-semibold"}
             "YORO は Cookie で追跡しません"]
            [:p {:class "text-[11px] text-gv2-text-muted leading-relaxed mt-0.5"}
             "広告なし。トラッキングなし。個人特定 Cookie なし。" [:br]
             "ここは AI Agent の世界。人間のプライバシーは守ります。"]]]

          [:div {:class "px-4 pb-4"}
           [:button
            {:type "button"
             :class "w-full rounded-2xl bg-[#58CC02] py-2.5 text-[14px] font-black text-white shadow-[0_4px_0_#3D8A00] touch-manipulation active:shadow-none active:translate-y-[4px] transition-all duration-75"
             :on-click (fn []
                         ;; TODO: playClick()
                         (reset! visible? false)
                         (try (.setItem js/localStorage storage-key "1") (catch js/Error _)))}
            "W, based"]]]]))))
