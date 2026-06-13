(ns yoro-ui.pages.search
  "Search page — etzhayyim actor registry + AT Protocol actor/post search."
  (:require [reagent.core :as r]
            [re-frame.core :as rf]
            [yoro-ui.components.actor-card :refer [actor-card actor-skeleton]]
            [yoro-ui.components.post-card :refer [post-card post-skeleton]]))

;; ---------------------------------------------------------------------------
;; Tab button

(defn- tab-btn [label k active-tab]
  [:button {:class (str "px-4 py-2.5 text-[13px] font-bold transition-colors "
                        (if (= k active-tab)
                          "text-[#1CB0F6] border-b-2 border-[#1CB0F6]"
                          "text-gv2-text-muted hover:text-gv2-text-primary"))
            :on-click #(rf/dispatch [:search/set-tab k])}
   label])

;; ---------------------------------------------------------------------------
;; etzhayyim actor card (compact grid tile)

(defn- ez-actor-chip [{:keys [displayName glyph handle description _etzhayyim]}]
  (let [tier (get _etzhayyim :tier "")
        status (get _etzhayyim :status "")]
    [:a {:href (str "/profile/" handle)
         :class "flex flex-col gap-1 p-3 rounded-xl bg-gv2-bg-card border border-gv2-border hover:border-[#1CB0F6]/50 transition-colors"}
     [:div {:class "flex items-center gap-2"}
      ;; Glyph badge
      (when (seq glyph)
        [:span {:class "w-8 h-8 rounded-lg bg-[#1CB0F6]/10 flex items-center justify-center text-[16px] flex-shrink-0"}
         glyph])
      [:div {:class "min-w-0"}
       [:div {:class "text-[12px] font-bold text-gv2-text-primary truncate"} displayName]
       [:div {:class "text-[10px] text-gv2-text-muted truncate"} (str "@" handle)]]]
     (when (seq description)
       [:p {:class "text-[11px] text-gv2-text-muted line-clamp-2 leading-snug"} description])
     (when (or (seq tier) (seq status))
       [:div {:class "flex gap-1 flex-wrap"}
        (when (seq tier)
          [:span {:class "text-[9px] px-1.5 py-0.5 rounded bg-[#1CB0F6]/10 text-[#1CB0F6] font-bold"}
           (str "Tier-" tier)])
        (when (seq status)
          [:span {:class "text-[9px] px-1.5 py-0.5 rounded bg-gv2-bg-base text-gv2-text-muted font-mono"}
           status])])]))

;; ---------------------------------------------------------------------------
;; Discover section (shown when query is empty)

(defn- discover-section [actors]
  [:div {:class "px-4 py-4"}
   [:h2 {:class "text-[11px] font-bold text-gv2-text-muted uppercase tracking-widest mb-3"}
    "etzhayyim actors"]
   [:div {:class "grid grid-cols-1 gap-2"}
    (for [a actors]
      ^{:key (or (:handle a) (:did a))}
      [ez-actor-chip a])]])

;; ---------------------------------------------------------------------------
;; etzhayyim match section (shown above AT results when query is non-empty)

(defn- ez-match-section [actors]
  (when (seq actors)
    [:div
     [:div {:class "px-4 pt-4 pb-1"}
      [:span {:class "text-[11px] font-bold text-gv2-text-muted uppercase tracking-widest"}
       "etzhayyim"]]
     [:div {:class "px-4 pb-2 grid grid-cols-1 gap-2"}
      (for [a actors]
        ^{:key (or (:handle a) (:did a))}
        [ez-actor-chip a])]
     [:div {:class "border-b border-gv2-border mx-4 mb-2"}]]))

;; ---------------------------------------------------------------------------
;; Page

(defn search-page []
  (let [input-val (r/atom "")]
    (r/create-class
     {:display-name "search-page"
      :component-did-mount
      (fn [_] (rf/dispatch [:etzhayyim/load-actors]))
      :reagent-render
      (fn []
        (let [query @(rf/subscribe [:search/query])
              tab @(rf/subscribe [:search/tab])
              actors @(rf/subscribe [:search/actors])
              posts @(rf/subscribe [:search/posts])
              loading? @(rf/subscribe [:search/loading?])
              end? @(rf/subscribe [:search/end?])
              ez-actors @(rf/subscribe [:etzhayyim/actors-filtered])]
          [:div {:class "flex flex-col"}

           ;; Search bar
           [:div {:class "px-4 py-3 border-b border-gv2-border sticky top-0 z-10 bg-gv2-bg-base"}
            [:div {:class "relative"}
             [:span {:class "absolute left-3 top-1/2 -translate-y-1/2 text-gv2-text-muted text-[16px]"}
              "🔍"]
             [:input {:type "search"
                      :placeholder "Actor / 投稿を検索..."
                      :value @input-val
                      :class "w-full pl-9 pr-4 py-2 rounded-xl bg-gv2-bg-card border border-gv2-border text-[14px] text-gv2-text-primary placeholder:text-gv2-text-muted focus:outline-none focus:border-[#1CB0F6]"
                      :on-change #(reset! input-val (.. % -target -value))
                      :on-key-press (fn [e]
                                      (when (= (.-key e) "Enter")
                                        (rf/dispatch [:search/run @input-val])))}]]]

           ;; Tab bar
           [:div {:class "flex border-b border-gv2-border sticky top-[57px] z-10 bg-gv2-bg-base"}
            [tab-btn "Actors" :actors tab]
            [tab-btn "投稿" :posts tab]]

           ;; Results
           (cond
             ;; Empty query — show etzhayyim actors discover panel
             (empty? query)
             [discover-section ez-actors]

             ;; Loading with no results yet
             (and loading? (empty? (if (= tab :actors) actors posts)))
             (case tab
               :actors (for [i (range 6)] ^{:key i} [actor-skeleton])
               :posts  (for [i (range 4)] ^{:key i} [post-skeleton]))

             ;; Actors tab
             (= tab :actors)
             [:div
              ;; etzhayyim matches at the top
              [ez-match-section ez-actors]
              ;; AT Protocol results
              (when (seq actors)
                [:div {:class "px-4 pt-2 pb-1"}
                 [:span {:class "text-[11px] font-bold text-gv2-text-muted uppercase tracking-widest"}
                  "Bluesky"]])
              (if (empty? actors)
                (when (empty? ez-actors)
                  [:div {:class "py-12 text-center text-[13px] text-gv2-text-muted"}
                   (str "\"" query "\" の検索結果なし")])
                (for [a actors]
                  ^{:key (or (:did a) (:handle a))}
                  [actor-card {:did (:did a)
                               :handle (:handle a)
                               :display-name (:displayName a)
                               :description (:description a)
                               :avatar-url (:avatar a)
                               :indexed-at (:indexedAt a)}]))
              (when (and (seq actors) (not end?))
                [:button {:class "w-full py-4 text-[13px] text-[#1CB0F6] font-semibold hover:bg-gv2-bg-card/30"
                          :on-click #(rf/dispatch [:search/load-more-actors])}
                 (if loading? "読み込み中…" "さらに表示")])]

             ;; Posts tab
             (= tab :posts)
             (if (empty? posts)
               [:div {:class "py-12 text-center text-[13px] text-gv2-text-muted"}
                (str "\"" query "\" の投稿なし")]
               (for [p posts]
                 ^{:key (or (:uri p) (:cid p))}
                 [post-card {:uri (:uri p)
                             :cid (:cid p)
                             :author (:author p)
                             :record (:record p)
                             :like-count (:likeCount p 0)
                             :repost-count (:repostCount p 0)
                             :reply-count (:replyCount p 0)
                             :indexed-at (:indexedAt p)}])))
           ]))})))
