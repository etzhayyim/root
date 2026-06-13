(ns yoro-ui.components.post-card
  "Post card component — port of the Svelte FeedTimeline post row."
  (:require [reagent.core :as r]
            [re-frame.core :as rf]
            [yoro-ui.router :as router]))

;; ---------------------------------------------------------------------------
;; Helpers

(defn- format-count [n]
  (cond
    (>= n 1000000) (str (.toFixed (/ n 1000000) 1) "M")
    (>= n 1000) (str (.toFixed (/ n 1000) 1) "K")
    :else (str n)))

(defn- relative-time [iso-str]
  (when iso-str
    (let [now (.now js/Date)
          then (try (.-getTime (js/Date. iso-str)) (catch js/Error _ now))
          diff-ms (- now then)
          diff-s (/ diff-ms 1000)
          diff-m (/ diff-s 60)
          diff-h (/ diff-m 60)
          diff-d (/ diff-h 24)]
      (cond
        (< diff-s 60) "たった今"
        (< diff-m 60) (str (js/Math.floor diff-m) "分前")
        (< diff-h 24) (str (js/Math.floor diff-h) "時間前")
        (< diff-d 7) (str (js/Math.floor diff-d) "日前")
        :else (subs iso-str 0 10)))))

(defn- extract-text [record]
  (or (:text record)
      (get-in record ["text"])
      ""))

;; ---------------------------------------------------------------------------
;; Avatar

(defn avatar [{:keys [src display-name size]
               :or {size 44}}]
  (let [fallback-char (when display-name (first display-name))]
    [:div {:style {:width size :height size}
           :class "flex-shrink-0"}
     (if src
       [:img {:src src
              :alt display-name
              :class "rounded-full object-cover"
              :style {:width size :height size}}]
       [:div {:class "rounded-full bg-[#1CB0F6] flex items-center justify-center text-white font-bold"
              :style {:width size :height size
                      :font-size (/ size 2.2)}}
        fallback-char])]))

;; ---------------------------------------------------------------------------
;; Action buttons

(defn- action-btn [{:keys [icon count active? on-click color]}]
  [:button {:class (str "flex items-center gap-1.5 text-[13px] font-semibold "
                        "transition-all duration-75 touch-manipulation "
                        (if active?
                          (str color " scale-110")
                          "text-gv2-text-muted hover:text-gv2-text-primary"))
            :on-click (when on-click #(do (.stopPropagation %) (on-click)))}
   [:span {:class "text-[16px]"} icon]
   (when (pos? count)
     [:span (format-count count)])])

;; ---------------------------------------------------------------------------
;; Embed images

(defn- embed-images [images]
  (when (seq images)
    (let [n (count images)]
      [:div {:class (str "mt-2 rounded-xl overflow-hidden grid gap-0.5 "
                         (case n
                           1 "grid-cols-1"
                           2 "grid-cols-2"
                           3 "grid-cols-2"
                           "grid-cols-2"))}
       (for [{:keys [thumb fullsize alt]} (take 4 images)]
         ^{:key (or thumb fullsize)}
         [:img {:src thumb
                :alt (or alt "")
                :class "w-full object-cover"
                :style {:max-height (if (= n 1) "360px" "180px")}}])])))

;; ---------------------------------------------------------------------------
;; Post card

(defn post-card
  "Renders a single post. Props map:
   {:uri :cid :author {:handle :displayName :avatar}
    :record {:text :createdAt} :like-count :repost-count
    :reply-count :view-count :indexed-at}"
  [{:keys [uri cid author record like-count repost-count reply-count
           view-count indexed-at reason-type reason-by]}]
  (let [liked? @(rf/subscribe [:feed/liked-uris])
        is-liked? (contains? (or liked? #{}) uri)
        text (extract-text record)
        images (get-in record [:embed :images])
        handle (or (:handle author) "")
        display-name (or (:displayName author) handle)
        avatar-url (:avatar author)]
    [:div {:class "px-4 py-3 border-b border-gv2-border/40 hover:bg-gv2-bg-card/30 transition-colors duration-100 cursor-pointer"
           :on-click #(router/navigate! (str "/profile/" handle "/post/" (last (clojure.string/split uri #"/"))))}

     ;; Repost reason header
     (when (= reason-type "app.bsky.feed.defs#reasonRepost")
       [:div {:class "flex items-center gap-1.5 text-[12px] text-gv2-text-muted mb-1.5 pl-11"}
        [:span "🔁"]
        [:span (:displayName reason-by) " がリポスト"]])

     [:div {:class "flex gap-3"}
      ;; Avatar
      [:div {:on-click #(do (.stopPropagation %)
                            (router/navigate! (str "/profile/" handle)))}
       [avatar {:src avatar-url :display-name display-name :size 44}]]

      ;; Content
      [:div {:class "flex-1 min-w-0"}
       ;; Author + time
       [:div {:class "flex items-center gap-1.5 mb-0.5"}
        [:span {:class "font-bold text-[14px] text-gv2-text-primary truncate"
                :on-click #(do (.stopPropagation %)
                               (router/navigate! (str "/profile/" handle)))}
         display-name]
        [:span {:class "text-[12px] text-gv2-text-muted truncate"}
         (str "@" handle)]
        [:span {:class "text-[12px] text-gv2-text-muted ml-auto flex-shrink-0"}
         (relative-time indexed-at)]]

       ;; Post text
       (when (seq text)
         [:p {:class "text-[14px] leading-relaxed text-gv2-text-primary whitespace-pre-wrap break-words"}
          text])

       ;; Embedded images
       (embed-images images)

       ;; Action bar
       [:div {:class "flex items-center gap-5 mt-2.5"}
        [action-btn {:icon "💬" :count (or reply-count 0)
                     :color "text-[#1185FE]"
                     :on-click nil}]
        [action-btn {:icon "🔁" :count (or repost-count 0)
                     :color "text-[#00BA7C]"
                     :on-click nil}]
        [action-btn {:icon (if is-liked? "❤️" "🤍")
                     :count (or like-count 0)
                     :active? is-liked?
                     :color "text-[#F91880]"
                     :on-click #(rf/dispatch [:feed/toggle-like {:uri uri :cid cid}])}]
        (when (pos? view-count)
          [:div {:class "flex items-center gap-1 text-[12px] text-gv2-text-muted ml-auto"}
           [:span "👁"]
           [:span (format-count view-count)]])]]]]))

;; ---------------------------------------------------------------------------
;; Skeleton loader

(defn post-skeleton []
  [:div {:class "px-4 py-3 border-b border-gv2-border/40"}
   [:div {:class "flex gap-3"}
    [:div {:class "w-11 h-11 rounded-full bg-gv2-border/40 flex-shrink-0 animate-pulse"}]
    [:div {:class "flex-1"}
     [:div {:class "h-3 bg-gv2-border/40 rounded w-1/3 mb-2 animate-pulse"}]
     [:div {:class "h-3 bg-gv2-border/40 rounded w-full mb-1 animate-pulse"}]
     [:div {:class "h-3 bg-gv2-border/40 rounded w-4/5 animate-pulse"}]]]])
