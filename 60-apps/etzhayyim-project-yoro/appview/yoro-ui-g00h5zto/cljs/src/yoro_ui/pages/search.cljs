(ns yoro-ui.pages.search
  "Search page — actor and post search."
  (:require [reagent.core :as r]
            [re-frame.core :as rf]
            [yoro-ui.components.actor-card :refer [actor-card actor-skeleton]]
            [yoro-ui.components.post-card :refer [post-card post-skeleton]]))

(defn- tab-btn [label k active-tab]
  [:button {:class (str "px-4 py-2.5 text-[13px] font-bold transition-colors "
                        (if (= k active-tab)
                          "text-[#1CB0F6] border-b-2 border-[#1CB0F6]"
                          "text-gv2-text-muted hover:text-gv2-text-primary"))
            :on-click #(rf/dispatch [:search/set-tab k])}
   label])

(defn search-page []
  (let [input-val (r/atom "")]
    (fn []
      (let [query @(rf/subscribe [:search/query])
            tab @(rf/subscribe [:search/tab])
            actors @(rf/subscribe [:search/actors])
            posts @(rf/subscribe [:search/posts])
            loading? @(rf/subscribe [:search/loading?])
            end? @(rf/subscribe [:search/end?])]
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
           (empty? query)
           [:div {:class "flex flex-col items-center justify-center py-20 text-center px-6"}
            [:div {:class "text-5xl mb-4"} "🔍"]
            [:p {:class "text-[14px] text-gv2-text-muted"}
             "Actor 名または投稿テキストを検索"]]

           (and loading? (empty? (if (= tab :actors) actors posts)))
           (case tab
             :actors (for [i (range 6)] ^{:key i} [actor-skeleton])
             :posts  (for [i (range 4)] ^{:key i} [post-skeleton]))

           (= tab :actors)
           [:div
            (if (empty? actors)
              [:div {:class "py-12 text-center text-[13px] text-gv2-text-muted"}
               (str "\"" query "\" の検索結果なし")]
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
                           ]))))
