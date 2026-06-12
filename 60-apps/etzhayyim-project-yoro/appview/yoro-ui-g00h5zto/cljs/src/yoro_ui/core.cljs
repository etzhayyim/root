(ns yoro-ui.core
  (:require [reagent.core :as r]
            [reagent.dom.client :as rdc]
            [re-frame.core :as rf]
            [yoro-ui.state.history]
            [yoro-ui.state.hitl]
            [yoro-ui.state.convos]
            [yoro-ui.state.topology :as topology]
            [yoro-ui.state.inference-consent :as consent]
            [yoro-ui.components.streak-badge :refer [streak-badge]]
            [yoro-ui.components.brainrot-mascot :refer [brainrot-mascot]]
            [yoro-ui.components.kami-yoro-mascot :refer [kami-yoro-mascot]]
            [yoro-ui.components.header-yoro-animation :refer [header-yoro-animation]]
            [yoro-ui.components.nondual-experience-guide :refer [nondual-experience-guide]]
            [yoro-ui.components.inference-consent :refer [inference-consent]]
            [yoro-ui.components.no-cookie-banner :refer [no-cookie-banner]]))

;; ---------------------------------------------------------------------------
;; app shell state

(rf/reg-event-db
 :app/initialize
 (fn [db _]
   (if (seq db) db {:app {:active-tab :components}})))

(rf/reg-sub
 :app/active-tab
 (fn [db _]
   (get-in db [:app :active-tab] :components)))

(rf/reg-event-db
 :app/set-tab
 (fn [db [_ tab]]
   (assoc-in db [:app :active-tab] tab)))

(rf/reg-sub
 :app/guide-visible?
 (fn [db _]
   (get-in db [:app :guide-visible?] false)))

(rf/reg-event-db
 :app/set-guide-visible
 (fn [db [_ v]]
   (assoc-in db [:app :guide-visible?] v)))

;; ---------------------------------------------------------------------------
;; views

(def section-card "p-4 border border-gv2-border rounded-xl bg-gv2-bg-card mb-4")
(def button-cls "px-3 py-1.5 rounded-lg bg-[#1CB0F6] text-white text-[13px] font-bold hover:opacity-90 active:translate-y-px")
(def button-muted-cls "px-3 py-1.5 rounded-lg bg-gv2-border text-gv2-text-primary text-[13px] font-bold hover:opacity-90")

(defn- consent-demo []
  (let [resolved? (r/atom false)]
    (fn []
      [:div
       [:div {:class "flex gap-2 flex-wrap"}
        [:button {:class button-cls
                  :on-click (fn []
                              (reset! resolved? false)
                              (-> (consent/request-consent!)
                                  (.then #(reset! resolved? true))))}
         "推論に参加 (request-consent!)"]
        [:button {:class button-muted-cls
                  :on-click #(do (consent/revoke-consent!) (reset! resolved? false))}
         "同意を取り消す (revoke)"]]
       [:p {:class "text-[12px] text-gv2-text-muted mt-2"}
        (cond
          @resolved? "✓ consent resolved — モデルロードへ進める状態"
          (consent/has-consent?) "同意済み (localStorage) — request は即 resolve"
          :else "未同意 — request でモーダルが開く (スクロール→チェック→同意)")]])))

(defn components-view []
  [:div
   [:div {:class section-card}
    [:h3 {:class "font-bold mb-2"} "StreakBadge"]
    [streak-badge {:class "justify-start"}]]
   [:div {:class section-card}
    [:h3 {:class "font-bold mb-2"} "KamiYoroMascot — WebGPU iframe + SVG fallback"]
    [:div {:class "flex items-end gap-6 flex-wrap"}
     [kami-yoro-mascot {:width 160 :height 176}]
     [:p {:class "text-[12px] text-gv2-text-muted max-w-[320px]"}
      "SVG を即表示し、WebGPU 環境では /kami-web/embed.html の KAMI Engine 3D に
       切替 (dev server には embed が無いので SVG fallback のまま)。クリックでバウンス。"]]]
   [:div {:class section-card}
    [:h3 {:class "font-bold mb-2"} "InferenceConsent — TOS 同意ゲート"]
    [consent-demo]]
   [:div {:class section-card}
    [:h3 {:class "font-bold mb-2"} "HeaderYoroAnimation — 8 patterns"]
    [:div {:class "flex items-center gap-4"}
     [:span {:class "text-[18px] font-black"} "YORO" [header-yoro-animation {:class "ml-1"}]]
     [:p {:class "text-[12px] text-gv2-text-muted"}
      "6-10s でパターンをローテーション。クリックで次のパターンへ。ヘッダー右上にも常駐。"]]]
   [:div {:class section-card}
    [:h3 {:class "font-bold mb-2"} "NondualExperienceGuide — Charter §1.17 ガイダンス"]
    [:button {:class button-cls :on-click #(rf/dispatch [:app/set-guide-visible true])}
     "ガイドを開く (geo gate は fail-closed)"]]
   [:div {:class section-card}
    [:h3 {:class "font-bold mb-3"} "BrainrotMascot — 6 characters"]
    [:div {:class "flex flex-wrap gap-4 items-end"}
     (for [ch [:yoro :skibidi :sigma :ohio :rizz :gyatt]]
       ^{:key (name ch)}
       [:div {:class "flex flex-col items-center gap-1"}
        [brainrot-mascot {:size 72 :character ch}]
        [:span {:class "text-[11px] text-gv2-text-muted"} (name ch)]])]]
   [:div {:class section-card}
    [:h3 {:class "font-bold mb-2"} "NoCookieBanner"]
    [:p {:class "text-[12px] text-gv2-text-muted"}
     "1.5s 後に画面下部へ表示 (localStorage `yoro-no-cookie-seen` で抑制)。"]
    [:button {:class button-muted-cls
              :on-click #(do (try (.removeItem js/localStorage "yoro-no-cookie-seen")
                                  (catch js/Error _))
                             (.reload js/window.location))}
     "既読フラグをリセットして再表示"]]])

(defn history-view []
  (let [entries @(rf/subscribe [:history/entries])
        loading? @(rf/subscribe [:history/is-loading?])]
    [:div
     [:div {:class section-card}
      [:h3 {:class "font-bold mb-2"} "閲覧履歴 (state/history — re-frame port)"]
      [:div {:class "flex gap-2 mb-3 flex-wrap"}
       [:button {:class button-cls
                 :on-click #(rf/dispatch [:history/record-visit
                                          {:path (str "/profile/demo-" (rand-int 100))
                                           :title "Demo Profile"
                                           :history_type "profile"}])}
        "プロフィール閲覧を記録"]
       [:button {:class button-cls
                 :on-click #(rf/dispatch [:history/record-visit
                                          {:path "/search?q=kotoba"
                                           :title "検索: kotoba"
                                           :history_type "search"}])}
        "検索を記録"]
       [:button {:class button-muted-cls :on-click #(rf/dispatch [:history/load])}
        (if loading? "読み込み中…" "PDS から読込 (stub)")]
       [:button {:class button-muted-cls :on-click #(rf/dispatch [:history/clear])}
        "全削除"]]
      (if (empty? entries)
        [:p {:class "text-[13px] text-gv2-text-muted"} "履歴なし"]
        [:ul
         (for [{:keys [path title visitedAt history_type]} entries]
           ^{:key path}
           [:li {:class "flex items-center justify-between py-1.5 border-b border-gv2-border/50 text-[13px]"}
            [:span
             [:span {:class "font-semibold mr-2"} title]
             [:span {:class "text-gv2-text-muted mr-2"} path]
             [:span {:class "text-[11px] text-gv2-text-muted"} (str history_type " · " visitedAt)]]
            [:button {:class "text-gv2-text-muted hover:text-red-400 px-2"
                      :on-click #(rf/dispatch [:history/remove-entry path])}
             "×"]])])]]))

(defn hitl-view []
  (let [pending @(rf/subscribe [:hitl/pending])
        pregel @(rf/subscribe [:hitl/pregel-pending])]
    [:div {:class section-card}
     [:h3 {:class "font-bold mb-2"} "HITL ポーリング (state/hitl — re-frame port)"]
     [:div {:class "flex gap-6 mb-3"}
      [:div
       [:div {:class "text-[24px] font-black"} pending]
       [:div {:class "text-[11px] text-gv2-text-muted"} "hitl pending"]]
      [:div
       [:div {:class "text-[24px] font-black"} pregel]
       [:div {:class "text-[11px] text-gv2-text-muted"} "pregel pending"]]]
     [:div {:class "flex gap-2"}
      [:button {:class button-cls :on-click #(rf/dispatch [:hitl/start])} "ポーリング開始 (10s)"]
      [:button {:class button-muted-cls :on-click #(rf/dispatch [:hitl/stop])} "停止"]
      [:button {:class button-muted-cls :on-click #(rf/dispatch [:hitl/poll])} "1 回ポーリング"]]
     [:p {:class "text-[11px] text-gv2-text-muted mt-2"}
      "dev server には /api/hitl が無いため 404 → count 0 にフォールバックします。"]]))

(defn convos-view []
  (let [convos @(rf/subscribe [:convos/list])
        loading? @(rf/subscribe [:convos/is-loading?])]
    [:div {:class section-card}
     [:h3 {:class "font-bold mb-2"} "Convos (state/convos — re-frame port)"]
     [:button {:class button-cls :on-click #(rf/dispatch [:convos/refresh])}
      (if loading? "更新中…" "リフレッシュ (stub)")]
     (if (empty? convos)
       [:p {:class "text-[13px] text-gv2-text-muted mt-2"}
        "convo なし — $lib/atproto-agent interop は未移植 (stub)。"]
       [:ul (for [c convos] ^{:key (:id c)} [:li (:id c)])])]))

(defn topology-view []
  (let [tick (r/atom 0)
        topic-input (r/atom "")
        iv (atom nil)]
    (r/create-class
     {:component-did-mount (fn [_] (reset! iv (js/setInterval #(swap! tick inc) 1000)))
      :component-will-unmount (fn [_] (when @iv (js/clearInterval @iv)))
      :reagent-render
      (fn []
        @tick ; re-render every second for dwellMs
        (let [{:keys [echoPersistence distinctTopics dwellMs sampleSize]} (topology/get-session-topology)]
          [:div {:class section-card}
           [:h3 {:class "font-bold mb-2"} "Session Topology (state/topology port)"]
           [:div {:class "grid grid-cols-2 gap-3 mb-3 max-w-[420px]"}
            [:div [:div {:class "text-[20px] font-black"} (.toFixed (* 100 echoPersistence) 1) "%"]
             [:div {:class "text-[11px] text-gv2-text-muted"} "echo persistence"]]
            [:div [:div {:class "text-[20px] font-black"} distinctTopics]
             [:div {:class "text-[11px] text-gv2-text-muted"} "distinct topics"]]
            [:div [:div {:class "text-[20px] font-black"} (js/Math.floor (/ dwellMs 1000)) "s"]
             [:div {:class "text-[11px] text-gv2-text-muted"} "dwell"]]
            [:div [:div {:class "text-[20px] font-black"} sampleSize]
             [:div {:class "text-[11px] text-gv2-text-muted"} "samples"]]]
           [:div {:class "flex gap-2 items-center flex-wrap"}
            [:input {:class "px-3 py-1.5 rounded-lg bg-gv2-bg-base border border-gv2-border text-[13px]"
                     :placeholder "topic 名"
                     :value @topic-input
                     :on-change #(reset! topic-input (.. % -target -value))}]
            [:button {:class button-cls
                      :on-click #(do (topology/record-topic-visit @topic-input)
                                     (reset! topic-input "")
                                     (swap! tick inc))}
             "topic 訪問を記録"]
            [:button {:class button-muted-cls
                      :on-click #(do (topology/reset-session-topology) (swap! tick inc))}
             "セッションをリセット"]]
           [:p {:class "text-[11px] text-gv2-text-muted mt-2"}
            (if (topology/is-doom-scrolling?)
              "⚠️ doom-scrolling 判定: true"
              "doom-scrolling 判定: false")]]))})))

(def tabs
  [[:components "Components"]
   [:history "History"]
   [:hitl "HITL"]
   [:convos "Convos"]
   [:topology "Topology"]])

(defn ui []
  (let [active @(rf/subscribe [:app/active-tab])]
    [:div {:class "min-h-screen bg-gv2-bg-base text-gv2-text-primary p-4 pb-32"}
     [:div {:class "flex items-center justify-between mb-1 max-w-[860px] mx-auto"}
      [:h1 {:class "text-2xl font-bold flex items-center gap-1"}
       "Yoro ClojureScript Refactor"
       [header-yoro-animation]]
      [streak-badge]]
     [:p {:class "mb-4 text-gv2-text-muted max-w-[860px] mx-auto"}
      "svelte → cljs (reagent + re-frame) 移行ハーネス"]

     [:div {:class "flex gap-1 mb-4 border-b border-gv2-border max-w-[860px] mx-auto"}
      (for [[k label] tabs]
        ^{:key (name k)}
        [:button {:class (str "px-3 py-2 text-[13px] font-bold rounded-t-lg "
                              (if (= k active)
                                "bg-gv2-bg-card text-[#1CB0F6] border border-gv2-border border-b-0"
                                "text-gv2-text-muted hover:text-gv2-text-primary"))
                  :on-click #(rf/dispatch [:app/set-tab k])}
         label])]

     [:div {:class "max-w-[860px] mx-auto"}
      (case active
        :components [components-view]
        :history    [history-view]
        :hitl       [hitl-view]
        :convos     [convos-view]
        :topology   [topology-view]
        [components-view])]

     (when @(rf/subscribe [:app/guide-visible?])
       [nondual-experience-guide {:on-continue #(rf/dispatch [:app/set-guide-visible false])}])
     [inference-consent]
     [no-cookie-banner]]))

;; React 18 root — defonce so shadow-cljs hot reload reuses the same root
(defonce react-root
  (delay (rdc/create-root (.getElementById js/document "app"))))

(defn mount-root []
  (rdc/render @react-root [ui]))

(defn init! []
  (rf/dispatch-sync [:app/initialize])
  (mount-root))
