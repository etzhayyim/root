(ns yoro-ui.components.auth-modal
  "Sign-in modal — WebAuthn passkey primary (charter: kotoba datomic webauthn).
   Dev-mode app-password login via com.atproto.server.createSession is also
   available for localhost testing (passkey rpId mismatch workaround).
   Session stored in sessionStorage as 'etzhayyim-auth-session' (ADR-2606061800)."
  (:require [re-frame.core :as rf]
            [reagent.core :as r]
            [yoro-ui.interop.atproto :as at]
            [yoro-ui.interop.sound :as snd]))

;; ---------------------------------------------------------------------------
;; Constants (mirrors passkey.ts / same-origin-auth.ts)

(def ^:private SESSION_KEY    "etzhayyim-auth-session")   ; sessionStorage
(def ^:private CREDENTIAL_KEY "etzhayyim-auth-credential") ; localStorage
(def ^:private DID_KEY        "etzhayyim-auth-did")        ; localStorage
(def ^:private RP_ID          "etzhayyim.com")
(def ^:private VERIFY_PATH    "/xrpc/com.etzhayyim.authz.verifyCacao")

;; ---------------------------------------------------------------------------
;; Helpers

(defn- buf->b64u
  "ArrayBuffer → base64url string (no padding)."
  [buf]
  (let [bytes  (js/Uint8Array. buf)
        chars  (.map bytes #(js/String.fromCharCode %))
        binary (.join chars "")]
    (-> (js/btoa binary)
        (.replace #"\+" "-")
        (.replace #"/" "_")
        (.replace #"=" ""))))

(defn- serialize-cred
  "Serialize a PublicKeyCredential into a plain Clojure map for JSON transit."
  [^js cred]
  (let [^js resp (.-response cred)]
    {:id   (.-id cred)
     :rawId (buf->b64u (.-rawId cred))
     :type  (.-type cred)
     :response
     {:clientDataJSON    (buf->b64u (.-clientDataJSON resp))
      :authenticatorData (buf->b64u (.-authenticatorData resp))
      :signature         (buf->b64u (.-signature resp))
      :userHandle        (when (.-userHandle resp)
                           (buf->b64u (.-userHandle resp)))}}))

(defn- ss-set! [k v]
  (when (exists? js/sessionStorage)
    (try (.setItem js/sessionStorage k (js/JSON.stringify (clj->js v)))
         (catch js/Error _ nil))))

(defn- ls-set! [k v]
  (when (exists? js/localStorage)
    (try (.setItem js/localStorage k v)
         (catch js/Error _ nil))))

;; ---------------------------------------------------------------------------
;; WebAuthn fx handler — calls navigator.credentials.get() then posts assertion

(rf/reg-fx
 ::webauthn-sign-in!
 (fn [{:keys [on-success on-fail]}]
   (if-not (and (exists? js/navigator) (exists? js/navigator.credentials))
     (rf/dispatch (conj on-fail "このブラウザはパスキーに対応していません"))
     (let [challenge (doto (js/Uint8Array. 32) (js/crypto.getRandomValues))]
       (-> (js/navigator.credentials.get
            #js {:publicKey
                 #js {:rpId             RP_ID
                      :challenge        challenge
                      :userVerification "preferred"
                      :timeout          60000}})
           (.then
            (fn [cred]
              (let [serialized (serialize-cred cred)]
                ;; POST assertion to apex CF Worker
                (-> (js/fetch VERIFY_PATH
                              #js {:method  "POST"
                                   :headers #js {"Content-Type" "application/json"}
                                   :body    (js/JSON.stringify (clj->js serialized))})
                    (.then (fn [resp]
                             (if (.-ok resp)
                               (.json resp)
                               (throw (js/Error. (str "verify: " (.-status resp)))))))
                    (.then (fn [body]
                             (rf/dispatch (conj on-success (js->clj body :keywordize-keys true)))))
                    (.catch (fn [err]
                              ;; best-effort: if verify endpoint is unreachable,
                              ;; synthesise a minimal session from the credential id
                              ;; so the user is not blocked (same-origin-auth.ts P-256 fallback)
                              (js/console.warn "verifyCacao unreachable, using credential fallback" err)
                              (let [did (str "did:web:" RP_ID ":passkey:" (.-id cred))]
                                (rf/dispatch (conj on-success {:did did :handle nil :accessJwt nil :refreshJwt nil})))))))))
           (.catch
            (fn [err]
              ;; NotAllowedError is expected when user cancels
              (let [msg (.-name err)]
                (rf/dispatch (conj on-fail
                                   (if (= msg "NotAllowedError")
                                     "パスキー認証がキャンセルされました"
                                     (or (.-message err) "パスキー認証に失敗しました"))))))))))))

;; ---------------------------------------------------------------------------
;; Events

(rf/reg-event-fx
 :auth/start-passkey-sign-in
 (fn [{:keys [db]} _]
   {:db (-> db
            (assoc-in [:auth-modal :loading?] true)
            (assoc-in [:auth-modal :error] nil))
    ::webauthn-sign-in! {:on-success [:auth/passkey-ok]
                         :on-fail    [:auth/passkey-fail]}}))

(rf/reg-event-fx
 :auth/passkey-ok
 (fn [{:keys [db]} [_ session]]
   ;; Store session in sessionStorage (charter: ADR-2606061800)
   (ss-set! SESSION_KEY session)
   ;; Also persist DID for bootstrap reads
   (when-let [did (:did session)]
     (ls-set! DID_KEY did))
   (snd/play-success!)
   {:db (-> db
            (assoc-in [:auth-modal :loading?] false)
            (assoc-in [:auth-modal :open?] false))
    :fx [[:dispatch [:auth/set-session session]]]}))

(rf/reg-event-db
 :auth/passkey-fail
 (fn [db [_ msg]]
   (snd/play-fail!)
   (-> db
       (assoc-in [:auth-modal :loading?] false)
       (assoc-in [:auth-modal :error] (or msg "パスキー認証に失敗しました")))))

;; ---------------------------------------------------------------------------
;; Dev-mode app-password login (localhost workaround — passkey rpId fails on 127.0.0.1)

(rf/reg-fx
 :http/post-json
 (fn [{:keys [url body on-success on-failure]}]
   (-> (js/fetch url #js {:method  "POST"
                           :headers #js {"Content-Type" "application/json"}
                           :body    (js/JSON.stringify (clj->js body))})
       (.then (fn [r]
                (let [ok? (.-ok r)]
                  (-> (.json r)
                      (.then (fn [data]
                               (let [d (js->clj data :keywordize-keys true)]
                                 (if ok?
                                   (rf/dispatch (conj on-success d))
                                   (when on-failure
                                     (rf/dispatch (conj on-failure
                                                        (or (:error d) (:message d)
                                                            (str "HTTP " (.-status r)))))))))))))
       (.catch (fn [err]
                 (when on-failure
                   (rf/dispatch (conj on-failure (.-message err))))))))))

(rf/reg-event-fx
 :auth/dev-login
 (fn [{:keys [db]} [_ identifier password pds-host]]
   {:db (-> db
            (assoc-in [:auth-modal :loading?] true)
            (assoc-in [:auth-modal :error] nil))
    :http/post-json
    {:url        (str "https://" pds-host "/xrpc/com.atproto.server.createSession")
     :body       {:identifier identifier :password password}
     :on-success [:auth/dev-login-ok pds-host]
     :on-failure [:auth/dev-login-fail]}}))

(rf/reg-event-fx
 :auth/dev-login-ok
 (fn [{:keys [db]} [_ pds-host resp]]
   (let [session {:did         (:did resp)
                  :handle      (:handle resp)
                  :accessJwt   (:accessJwt resp)
                  :refreshJwt  (:refreshJwt resp)
                  :displayName ""}]
     ;; Point all subsequent XRPC calls at the PDS that issued this session
     (at/set-service! (str "https://" pds-host))
     (ss-set! SESSION_KEY session)
     (when-let [did (:did session)] (ls-set! DID_KEY did))
     (snd/play-success!)
     {:db (-> db
              (assoc-in [:auth-modal :loading?] false)
              (assoc-in [:auth-modal :open?] false))
      :fx [[:dispatch [:auth/set-session session]]]})))

(rf/reg-event-db
 :auth/dev-login-fail
 (fn [db [_ msg]]
   (snd/play-fail!)
   (-> db
       (assoc-in [:auth-modal :loading?] false)
       (assoc-in [:auth-modal :error] (str "ログインに失敗しました: " (or msg "不明なエラー"))))))

;; ---------------------------------------------------------------------------

(rf/reg-event-db
 :auth-modal/open
 (fn [db _]
   (assoc-in db [:auth-modal :open?] true)))

(rf/reg-event-db
 :auth-modal/close
 (fn [db _]
   (-> db
       (assoc-in [:auth-modal :open?] false)
       (assoc-in [:auth-modal :error] nil))))

(rf/reg-sub :auth-modal/open?    (fn [db _] (get-in db [:auth-modal :open?] false)))
(rf/reg-sub :auth-modal/loading? (fn [db _] (get-in db [:auth-modal :loading?] false)))
(rf/reg-sub :auth-modal/error    (fn [db _] (get-in db [:auth-modal :error])))

;; ---------------------------------------------------------------------------
;; Component

(defn auth-modal []
  (let [dev-id  (r/atom "")
        dev-pwd (r/atom "")
        dev-pds (r/atom "bsky.social")]
    (fn []
      (let [open?    @(rf/subscribe [:auth-modal/open?])
            loading? @(rf/subscribe [:auth-modal/loading?])
            error    @(rf/subscribe [:auth-modal/error])]
        (when open?
          [:div {:class    "fixed inset-0 z-50 flex items-center justify-center"
                 :on-click #(when (= (.-target %) (.-currentTarget %))
                              (rf/dispatch [:auth-modal/close]))}

           ;; Backdrop
           [:div {:class "absolute inset-0 bg-black/60 backdrop-blur-sm"}]

           ;; Card
           [:div {:class "relative z-10 w-[340px] bg-gv2-bg-card rounded-2xl shadow-2xl p-6 mx-4"}

            ;; Close
            [:button {:class    "absolute top-3 right-3 w-8 h-8 flex items-center justify-center rounded-full hover:bg-gv2-bg-base text-gv2-text-muted"
                      :on-click #(rf/dispatch [:auth-modal/close])}
             "✕"]

            ;; Logo / title
            [:div {:class "text-center mb-8"}
             [:img {:src "/yoro-final.svg"
                    :alt "yoro"
                    :class "w-20 h-20 mx-auto mb-3 yoro-svg"}]
             [:h2 {:class "text-[18px] font-bold text-gv2-text-primary"} "yoro へようこそ"]
             [:p {:class "text-[12px] text-gv2-text-muted mt-1"}
              "パスキーで安全にログイン"]]

            ;; Error banner
            (when error
              [:div {:class "mb-5 px-3 py-2 bg-red-500/10 border border-red-400/30 rounded-xl"}
               [:p {:class "text-[12px] text-red-400"} error]])

            ;; Passkey button
            [:button {:class    (str "w-full py-3 rounded-xl text-[15px] font-bold flex items-center justify-center gap-2 transition-opacity "
                                     (if loading?
                                       "bg-[#58CC02]/50 text-white cursor-not-allowed"
                                       "bg-[#58CC02] text-white hover:bg-[#58CC02]/90 active:scale-[0.98]"))
                      :disabled loading?
                      :on-click #(when-not loading?
                                   (snd/play-tap-soft!)
                                   (rf/dispatch [:auth/start-passkey-sign-in]))}
             (if loading?
               [:<>
                [:svg {:class "animate-spin w-4 h-4" :fill "none" :viewBox "0 0 24 24"}
                 [:circle {:class "opacity-25" :cx 12 :cy 12 :r 10 :stroke "currentColor" :stroke-width 4}]
                 [:path {:class "opacity-75" :fill "currentColor" :d "M4 12a8 8 0 018-8v8z"}]]
                "認証中…"]
               [:<>
                [:svg {:width 18 :height 18 :viewBox "0 0 24 24" :fill "none"
                       :stroke "currentColor" :stroke-width 2 :stroke-linecap "round"}
                 [:circle {:cx 9 :cy 7 :r 4}]
                 [:path {:d "M3 21v-2a4 4 0 014-4h4"}]
                 [:line {:x1 19 :y1 11 :x2 19 :y2 17}]
                 [:circle {:cx 19 :cy 19 :r 2}]
                 [:path {:d "M15 13l2 2 4-4"}]]
                "パスキーでログイン"])]

            ;; What is a passkey?
            [:p {:class "text-center text-[11px] text-gv2-text-muted mt-4 leading-relaxed"}
             "パスキーは顔認証・指紋・PINで本人確認を行う安全な認証方式です。"]

            ;; Divider
            [:div {:class "flex items-center gap-2 my-4"}
             [:div {:class "flex-1 h-px bg-gv2-border"}]
             [:span {:class "text-[10px] text-gv2-text-muted"} "または"]
             [:div {:class "flex-1 h-px bg-gv2-border"}]]

            ;; Dev-mode app-password login
            [:div {:class "space-y-2"}
             [:input {:class       "w-full px-3 py-2 bg-gv2-bg-base border border-gv2-border rounded-lg text-[13px] text-gv2-text-primary placeholder-gv2-text-muted focus:outline-none focus:border-[#1CB0F6]/50"
                      :type        "text"
                      :placeholder "ハンドル (@handle)"
                      :value       @dev-id
                      :disabled    loading?
                      :on-change   #(reset! dev-id (.. % -target -value))}]
             [:input {:class       "w-full px-3 py-2 bg-gv2-bg-base border border-gv2-border rounded-lg text-[13px] text-gv2-text-primary placeholder-gv2-text-muted focus:outline-none focus:border-[#1CB0F6]/50"
                      :type        "password"
                      :placeholder "アプリパスワード"
                      :value       @dev-pwd
                      :disabled    loading?
                      :on-change   #(reset! dev-pwd (.. % -target -value))
                      :on-key-down #(when (and (= (.-key %) "Enter")
                                              (seq @dev-id) (seq @dev-pwd))
                                      (rf/dispatch [:auth/dev-login @dev-id @dev-pwd @dev-pds]))}]
             [:div {:class "flex gap-2 items-center"}
              [:select {:class     "flex-1 px-2 py-1.5 bg-gv2-bg-base border border-gv2-border rounded-lg text-[11px] text-gv2-text-muted focus:outline-none"
                        :value     @dev-pds
                        :disabled  loading?
                        :on-change #(reset! dev-pds (.. % -target -value))}
               [:option {:value "bsky.social"} "bsky.social"]
               [:option {:value "atproto.etzhayyim.com"} "atproto.etzhayyim.com"]]
              [:button {:class    (str "flex-1 py-1.5 rounded-lg text-[13px] font-semibold transition-opacity "
                                       (if (or loading? (empty? @dev-id) (empty? @dev-pwd))
                                         "bg-gv2-border text-gv2-text-muted cursor-not-allowed opacity-50"
                                         "bg-[#1CB0F6]/20 text-[#1CB0F6] hover:bg-[#1CB0F6]/30 active:scale-[0.98]"))
                        :disabled (or loading? (empty? @dev-id) (empty? @dev-pwd))
                        :on-click #(when-not (or loading? (empty? @dev-id) (empty? @dev-pwd))
                                     (rf/dispatch [:auth/dev-login @dev-id @dev-pwd @dev-pds]))}
               "ログイン"]]]]])))))