(ns yoro-ui.components.inference-consent
  "Port of svelte/src/lib/components/InferenceConsent.svelte —
   full-screen TOS modal gate for browser inference participation.

   3 gates before acceptance:
   1. scroll the TOS text to the bottom
   2. check the agreement checkbox (disabled until scrolled)
   3. click accept (disabled until checked)

   The inner modal is a separate component mounted only while visible, so its
   local r/atoms reset on each open (the svelte $effect-on-visible equivalent)."
  (:require [reagent.core :as r]
            [re-frame.core :as rf]
            [yoro-ui.legal.content :refer [inference-consent-document]]))

(defn- modal []
  (let [scrolled-to-bottom? (r/atom false)
        checked? (r/atom false)
        handle-scroll
        (fn [e]
          (let [el (.-target e)]
            (when (>= (+ (.-scrollTop el) (.-clientHeight el))
                      (- (.-scrollHeight el) 40))
              (reset! scrolled-to-bottom? true))))]
    (fn []
      (let [{:keys [title summary sections last-updated]} inference-consent-document
            ready? (and @scrolled-to-bottom? @checked?)]
        [:<>
         ;; Backdrop
         [:div {:class "fixed inset-0 z-[200] bg-black/80 backdrop-blur-sm"
                :role "presentation"}]
         ;; Modal
         [:div {:class "fixed inset-0 z-[201] flex items-center justify-center p-4"
                :role "dialog"
                :aria-modal true
                :aria-labelledby "inference-tos-title"}
          [:div {:class "flex max-h-[90vh] w-full max-w-[560px] flex-col overflow-hidden rounded-3xl border border-gv2-border/40 bg-gv2-bg-card shadow-2xl"}
           ;; Header
           [:div {:class "flex-shrink-0 border-b border-gv2-border/30 px-6 pt-5 pb-4"}
            [:div {:class "flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-amber-400"}
             [:svg {:class "h-4 w-4" :view-box "0 0 24 24" :fill "currentColor"}
              [:path {:d "M12 2L1 21h22L12 2zm0 4l7.53 13H4.47L12 6zm-1 5v4h2v-4h-2zm0 6v2h2v-2h-2z"}]]
             [:span "Important Notice Regarding Inference Participation"]]
            [:h2 {:id "inference-tos-title"
                  :class "mt-2 text-xl font-bold tracking-tight text-gv2-text-primary"}
             title]
            [:p {:class "mt-1.5 text-[12px] leading-relaxed text-gv2-text-muted"}
             summary]]

           ;; Scrollable content
           [:div {:class "flex-1 overflow-y-auto overscroll-contain px-6 py-4"
                  :on-scroll handle-scroll}
            [:div {:class "space-y-5"}
             (for [{:keys [heading body]} sections]
               ^{:key heading}
               [:div
                [:h3 {:class "text-[13px] font-bold text-gv2-text-primary"} heading]
                [:div {:class "mt-1.5 space-y-2"}
                 (for [[i paragraph] (map-indexed vector body)]
                   ^{:key i}
                   [:p {:class "text-[12px] leading-[1.7] text-gv2-text-muted"} paragraph])]])]
            (when-not @scrolled-to-bottom?
              [:div {:class "sticky bottom-0 flex justify-center pt-3 pb-1"}
               [:div {:class "rounded-full bg-gv2-bg-card/80 px-3 py-1 text-[11px] font-medium text-gv2-text-muted backdrop-blur-sm border border-gv2-border/40"}
                "Please scroll to the bottom"]])]

           ;; Footer
           [:div {:class "flex-shrink-0 border-t border-gv2-border/30 px-6 py-4"}
            [:label {:class "flex items-start gap-3 cursor-pointer select-none"}
             [:input {:type "checkbox"
                      :checked @checked?
                      :disabled (not @scrolled-to-bottom?)
                      :on-change #(reset! checked? (.. % -target -checked))
                      :class "mt-0.5 h-5 w-5 rounded border-2 border-gv2-border accent-[#58CC02] disabled:opacity-30"}]
             [:span {:class (str "text-[12px] leading-relaxed text-gv2-text-primary"
                                 (when-not @scrolled-to-bottom? " opacity-40"))}
              "I have read, understood, and agree to all provisions of the Browser Inference Participation Terms above, including device resource usage, disclaimers, and indemnification clauses."]]

            [:div {:class "mt-4 flex gap-3"}
             [:button {:type "button"
                       :class (str "flex-1 rounded-2xl border border-gv2-border py-3 text-[13px] font-bold text-gv2-text-muted "
                                   "touch-manipulation active:bg-gv2-bg-base transition-all duration-75")
                       ;; TODO: playClick() sound interop
                       :on-click #(rf/dispatch [:inference-consent/decline])}
              "Decline"]
             [:button {:type "button"
                       :class (str "flex-1 rounded-2xl py-3 text-[13px] font-black text-white "
                                   "shadow-[0_4px_0_#3D8A00] touch-manipulation "
                                   "active:shadow-none active:translate-y-[4px] transition-all duration-75 "
                                   "disabled:opacity-30 disabled:shadow-none disabled:cursor-not-allowed "
                                   (if ready? "bg-[#58CC02]" "bg-gv2-border"))
                       :disabled (not ready?)
                       :on-click #(rf/dispatch [:inference-consent/accept])}
              "Agree and Join Inference"]]

            [:p {:class "mt-3 text-center text-[10px] text-gv2-text-muted"}
             (str "Last updated: " last-updated " | ")
             [:a {:href "/terms" :class "text-[#1185FE] underline"} "Terms of Use"]
             " | "
             [:a {:href "/privacy" :class "text-[#1185FE] underline"} "Privacy Policy"]]]]]]))))

(defn inference-consent []
  (when @(rf/subscribe [:inference-consent/visible?])
    [modal]))
