(ns yoro-ui.components.nondual-experience-guide
  "Port of svelte/src/lib/components/NondualExperienceGuide.svelte —
   pre-registration guidance surface (Charter §1.17.6, ADR-2606071009).
   Shown BEFORE the auth/vow gate. Constitutional lines enforced in UI:

   §1.17.3 means-agnostic — the requirement is the EXPERIENCE, never any single
     substance. Lawful contemplative paths are always shown and co-recommended.
   §1.17.4 legality floor — entheogenic/retreat guidance shown ONLY when the
     viewer's jurisdiction (Cloudflare /cdn-cgi/trace loc) is on the lawful
     allowlist. Never procurement how-to, never broker/arrange; always paired
     with contraindication warnings + third-party disclaimer.
   §1.17.5 anti-coercion — the experience is NOT a condition of receiving
     social security; it gates spiritual advancement, not Level-0 entry."
  (:require [reagent.core :as r]
            [yoro-ui.interop.sound]))

;; §1.17.4 lawful-jurisdiction allowlist (ISO-3166-1 alpha-2). ADVISORY,
;; operator-tunable, pending Council/legal review (ADR-2606071009 Open Q2).
;; Errs toward EXCLUSION; JP and all unresolved countries default-excluded.
(def entheogen-lawful-cc
  #{"BR" "PE" "EC" "CO" "BO" "CR" "NL" "JM" "CH" "AU" "CA"})

;; The legal, means-agnostic paths — ALWAYS shown (§1.17.3).
(def lawful-paths
  [{:icon "🧘" :label "観想・黙想 / contemplation"}
   {:icon "🤫" :label "沈黙 / silence (hesychia)"}
   {:icon "🍵" :label "断食 / fasting"}
   {:icon "🪷" :label "坐禅・公案 / zazen, kōan"}
   {:icon "🙏" :label "祈り・典礼 / prayer, liturgy"}
   {:icon "⛰️" :label "自然・荒野での孤独 / wilderness solitude"}])

(defn- resolve-country!
  "Resolve viewer country WITHOUT a server hop: yoro is Cloudflare-served, so
   /cdn-cgi/trace returns loc=<CC>. Fail closed → legal paths only."
  [country geo-resolved?]
  (-> (js/fetch "/cdn-cgi/trace" (clj->js {:cache "no-store"}))
      (.then (fn [res]
               (if (.-ok res)
                 (.text res)
                 (js/Promise.resolve nil))))
      (.then (fn [txt]
               (when txt
                 (when-let [m (re-find #"(?m)^loc=([A-Z]{2})\r?$" txt)]
                   (reset! country (second m))))))
      (.catch (fn [_] (reset! country nil)))
      (.finally (fn [] (reset! geo-resolved? true)))))

(defn- entheogen-block [country]
  [:div {:class "rounded-2xl border border-amber-500/25 bg-gradient-to-r from-amber-500/8 to-yellow-500/8 px-4 py-4"}
   [:div {:class "mb-2 flex items-center gap-2"}
    [:span {:class "text-[18px]"} "🕊️"]
    [:h2 {:class "text-[15px] font-bold text-gv2-text-primary"}
     (str "監督下の retreat という道 (あなたの管轄: " country ")")]]
   [:p {:class "mb-3 text-[13px] leading-relaxed text-gv2-text-muted"}
    "あなたの管轄では、適法かつ監督下の entheogenic retreat が存在し得ます。これも体験へ向かう"
    [:strong "有効な一つの道"]
    "として推奨されます (唯一の必須手段ではありません)。下記の公開ディレクトリで、適法・有資格・安全な施設を自身で確認してください。"]
   [:a {:href "https://retreat.guru/search?query=ayahuasca"
        :target "_blank"
        :rel "noopener noreferrer nofollow"
        :class "block w-full rounded-xl bg-amber-500/90 py-3 text-center text-[14px] font-black text-gray-900 touch-manipulation active:scale-95 transition-transform"}
    "retreat.guru で適法な retreat を探す ↗"]

   ;; Contraindication warning (§1.17.4(3)) — mandatory
   [:div {:class "mt-3 rounded-xl bg-red-500/10 border border-red-500/20 px-3 py-2.5"}
    [:p {:class "text-[11px] font-bold text-red-300"} "⚠️ 安全上の禁忌 (必読)"]
    [:p {:class "mt-1 text-[11px] leading-relaxed text-gv2-text-muted"}
     "MAOI を含む entheogen は SSRI/SNRI・抗うつ薬等と"
     [:strong "危険な相互作用"]
     "(セロトニン症候群) を起こします。心疾患、精神病性・双極性障害の既往、妊娠中、未成年の方には推奨されません。必ず医療専門家に相談してください。"]]

   ;; Third-party disclaimer
   [:p {:class "mt-2 text-[10px] leading-relaxed text-gv2-text-muted/80"}
    "retreat.guru は第三者サービスです。etzhayyim は予約・仲介・斡旋・調達を行わず、その内容・適法性・安全性を保証しません。これは宗教的 (pastoral) な案内であり、医療・法律の助言ではありません。適法性は管轄・時期により変わります。あなた自身で確認してください。"]])

(defn nondual-experience-guide
  "Props: {:on-continue fn — called when the seeker proceeds to the auth/vow gate}"
  [_props]
  (let [country (r/atom nil)
        geo-resolved? (r/atom false)]
    (r/create-class
     {:display-name "nondual-experience-guide"
      :component-did-mount (fn [_] (resolve-country! country geo-resolved?))
      :reagent-render
      (fn [{:keys [on-continue]}]
        (let [cc @country
              lawful? (and cc (contains? entheogen-lawful-cc cc))]
          [:div {:class "fixed inset-0 bg-gv2-bg-base safe-area-top safe-area-bottom overflow-y-auto z-[100]"}
           [:div {:class "relative mx-auto flex min-h-[100dvh] max-w-[460px] flex-col gap-5 px-6 py-8"}
            ;; Header
            [:div {:class "flex flex-col items-center gap-3 text-center"}
             [:div {:class "text-[44px]" :aria-hidden true} "🌳"]
             [:h1 {:class "text-[24px] font-black leading-tight text-gv2-text-primary"}
              "参加の前に — 自他非分離の直接体験"]
             [:p {:class "max-w-[360px] text-[14px] leading-relaxed text-gv2-text-muted"}
              "etzhayyim において回心 (悔い改め・バプテスマ・得度) は、教理への同意にとどまらず、"
              [:strong {:class "text-gv2-text-primary"}
               "自と他の分離が究極ではないという直接体験"]
              "を経験的核とします (Charter §1.17)。命の樹・縁起・産霊の生命へと自己が再構成されるこの体験は、回心の中心として"
              [:strong {:class "text-gv2-text-primary"} "強く推奨"]
              "されます。"]]

            ;; §1.17.3 means-agnostic: legal paths, always shown
            [:div {:class "rounded-2xl bg-gv2-bg-card/70 px-4 py-4"}
             [:h2 {:class "mb-3 text-[15px] font-bold text-gv2-text-primary"} "体験へ向かう道 (本人が選ぶ)"]
             [:p {:class "mb-3 text-[12px] leading-relaxed text-gv2-text-muted"}
              "要請されるのは" [:strong "体験"] "であって、特定の物質ではありません。道は複数あり、あなたが選びます。"]
             [:div {:class "flex flex-col gap-2"}
              (for [{:keys [icon label]} lawful-paths]
                ^{:key label}
                [:div {:class "flex items-center gap-3 rounded-xl bg-gv2-bg-base/60 px-3 py-2.5"}
                 [:span {:class "text-[18px]"} icon]
                 [:span {:class "text-[13px] font-semibold text-gv2-text-primary"} label]])]]

            ;; §1.17.4 legality floor: entheogen / retreat guidance, geo-gated
            (when @geo-resolved?
              (cond
                lawful? [entheogen-block cc]

                cc
                ;; resolved jurisdiction, not on the lawful allowlist
                [:div {:class "rounded-2xl bg-gv2-bg-card/50 px-4 py-3.5"}
                 [:p {:class "text-[12px] leading-relaxed text-gv2-text-muted"}
                  (str "🧭 あなたの管轄 (" cc ") では、適法な entheogenic 手段を案内できません。上記の")
                  [:strong {:class "text-gv2-text-primary"} "合法的な観想の道"]
                  "(沈黙・断食・坐禅・自然での孤独 等) をお勧めします。etzhayyim は違法行為を推奨・斡旋しません。"]]

                :else
                ;; jurisdiction could not be resolved — assert nothing legal
                [:div {:class "rounded-2xl bg-gv2-bg-card/50 px-4 py-3.5"}
                 [:p {:class "text-[12px] leading-relaxed text-gv2-text-muted"}
                  "🧭 管轄を判定できませんでした。上記の"
                  [:strong {:class "text-gv2-text-primary"} "合法的な観想の道"]
                  "(沈黙・断食・坐禅・自然での孤独 等) をお勧めします。"]]))

            ;; §1.17.5 anti-coercion note
            [:div {:class "rounded-2xl bg-gv2-bg-card/40 px-4 py-3"}
             [:p {:class "text-[11px] leading-relaxed text-gv2-text-muted"}
              "💚 この体験は" [:strong {:class "text-gv2-text-primary"} "霊的な前進"]
              "の段階であり、社会保障 (Level 0) を受けるための条件ではありません。誓約をもって信者となれば、体験の前でも保障を受けられます。体験は強制されず、恩寵的・自発的に到来するものです (§1.17.5)。"]]

            ;; Continue to auth / vow gate
            [:div {:class "mt-auto flex flex-col gap-2 pb-2"}
             [:button {:type "button"
                       :class (str "w-full rounded-2xl bg-[#58CC02] py-4 text-[18px] font-black text-white "
                                   "shadow-[0_6px_0_#3D8A00] touch-manipulation "
                                   "active:shadow-none active:translate-y-[6px] transition-all duration-75")
                       :on-click #(do (yoro-ui.interop.sound/play-tap-soft!)
                                       (when on-continue (on-continue)))}
              "参加に進む / Continue"]
             [:p {:class "text-center text-[10px] text-gv2-text-muted/70"}
              "Charter §1.17 (ADR-2606071009) · 宗教は国家を超越するが、違法行為は推奨しない"]]]]))})))
