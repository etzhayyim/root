#!/usr/bin/env bb
;; Working Clojure port of py/agent.py (omise seller-side storefront commons actor).
(ns omise.py.agent
  "omise 御店 — seller-side storefront commons langgraph actor (kotoba WASM cell).

  ADR-2606071400. The 'Shopify layer' for charter-clean internal sellers. Where okaimono
  is the buyer-side demand commons, omise is the SELLER-side: it lets an etzhayyim
  producing-actor or an SBT member stand up a storefront whose listings are okaimono
  Ring-1 products *by construction* (G11).

  Handlers:
    seller-kind              classify a seller DID (G3)
    open-storefront          seller-gating: producing-actor OR active SBT member (G3)
    create-listing           Ring-1 listing shape-compatible with okaimono product (G11)
    to-okaimono-product      map listing → canonical okaimono product (G11)
    storefront-ordering      Wellbecoming ranking, never paid placement (G5)
    build-settlement-intent  USDC + TitheRouter 10% (G7), ZERO commission (G2)
    authorize-settlement     member-sig only (G12 no-server-key)
    available-inventory      honest on-hand minus active reservations (G5)
    place-order              consent + SBT↔SBT + no-oversell + settlement intent (G1/G3/G5/G2/G7/G8)
    advance-order            caps at in-use, never terminal (G13)
    cancel-order             releases reservation; refused if delivered/in-use
    build-fulfilment         hands off to non-gig etzhayyim logistics actor (G8/G12)

  Hard invariants structurally unrepresentable:
    - ZERO platform commission (G2): commissionMinor ≡ 0; gross = tithe + sellerNet exactly.
    - no-server-key (G12): omise never signs a settlement.
    - okaimono Ring-1 coherence (G11): ring is constant \":internal\".

  Run:  bb --classpath 20-actors 20-actors/omise/py/agent.clj"
  (:require [clojure.string :as str]))

;; ── constants ──────────────────────────────────────────────────────────────────
(def ^:private tithe-bps 1000)   ; 10% TitheRouter auto-split (G7), basis points

;; Sellers gated by producing-actor membership (G3). External onboarding = Council Lv7+.
(def ^:private producing-actors
  #{"makura" "mitsuho" "yakushi" "tsutae" "futawa" "hikari" "sanae" "hataori"})

;; Order as-of trajectory (G13: caps at in-use, never terminal).
(def ^:private order-states
  ["cart" "placed" "settle-intent" "fulfilling" "delivered" "in-use"])

;; Item-class → etzhayyim logistics actor (G8: no gig labor).
(def ^:private fulfillment
  {"heavy" "sarutahiko", "road" "todoke", "bulky" "haraedo"})

(def ^:private labor-rank
  {"etzhayyim-dignity" 3, "verified-fair" 2, "disclosed" 1, "unknown" 0})

;; ── seller gating (G3) ────────────────────────────────────────────────────────
(defn seller-kind
  "Classify a seller DID. Returns {:eligible bool :kind str|nil :reason str}.
  A storefront may be opened ONLY by a producing actor OR an active Adherent SBT member (G3).
  External onboarding is Council Lv7+ and unrepresentable at R0."
  [seller-did sbt-registry]
  (let [actor-id (when (str/starts-with? seller-did "did:web:etzhayyim.com:")
                   (last (str/split seller-did #":")))]
    (cond
      (contains? producing-actors actor-id)
      {:eligible true :kind "producing-actor" :reason (str actor-id " is a producing actor")}

      (get sbt-registry seller-did false)
      {:eligible true :kind "sbt-member" :reason "active Adherent SBT member"}

      :else
      {:eligible false :kind nil
       :reason (str "seller is neither a producing actor nor an active SBT member (G3); "
                    "external onboarding is Council Lv7+")})))

(defn open-storefront
  "Open a storefront for a gated seller (G3). No subscription/listing fee exists (G2)."
  [seller-did name sbt-registry]
  (let [sk (seller-kind seller-did sbt-registry)]
    (if-not (:eligible sk)
      {:state "refused" :reason (:reason sk)}
      {:state "open"
       :storefrontId (str "omise." (last (str/split seller-did #":")))
       :sellerDid seller-did
       :sellerKind (:kind sk)
       :name name
       :subscriptionMinor 0})))   ; G2: no platform subscription, ever

;; ── listing (G11 okaimono Ring-1 coherence) ───────────────────────────────────
(defn create-listing
  "Create a listing on an open storefront. `ring` is constant \":internal\" (G11).
  There is NO commission/take-rate field (G2). The result is shape-compatible with
  okaimono's product record — verified by `to-okaimono-product`."
  [storefront title price-minor
   & {:keys [maker-actor inventory durability-years repairability
             labor-provenance carbon-kg lifecycle-route item-class]
      :or {inventory 0 durability-years 0.0 repairability 0
           labor-provenance "disclosed" carbon-kg 0.0
           lifecycle-route "hodoki" item-class "road"}}]
  (let [seller-did (:sellerDid storefront)
        maker (or maker-actor
                  (if (= (:sellerKind storefront) "producing-actor")
                    (last (str/split seller-did #":"))
                    "member"))
        listing-id (str (:storefrontId storefront) "."
                        (format "%04x" (bit-and (Math/abs (hash title)) 0xFFFF)))]
    {:listingId listing-id
     :storefrontId (:storefrontId storefront)
     :sellerDid seller-did
     :title title
     :makerActor maker
     :priceMinor (int price-minor)         ; no take-rate added (G2)
     :currency "USDC"
     :inventory (int inventory)            ; honest count, no false scarcity (G5)
     :durabilityYears (double durability-years)
     :repairability (int repairability)
     :laborProvenance labor-provenance
     :carbonKg (double carbon-kg)
     :lifecycleRoute lifecycle-route
     :fulfilmentActor (get fulfillment item-class "todoke")
     :ring "internal"                      ; const (G11 okaimono Ring-1 coherence)
     :sourcing "authoritative"}))

(defn to-okaimono-product
  "Map an omise listing onto the canonical com.etzhayyim.okaimono.product :ring \"internal\"
  shape (G11). This is the single proof that an omise storefront is discoverable in okaimono
  with NO integration glue — the field set is exactly okaimono's product lexicon."
  [listing]
  {:productId (str "int." (:makerActor listing) "."
                   (last (str/split (:listingId listing) #"\.")))
   :title (:title listing)
   :ring "internal"
   :unspsc (get listing :unspsc "")
   :makerActor (:makerActor listing)
   :source "internal-actor"
   :priceMinor (:priceMinor listing)
   :currency (:currency listing)
   :durabilityYears (:durabilityYears listing)
   :repairability (:repairability listing)
   :laborProvenance (:laborProvenance listing)
   :carbonKg (:carbonKg listing)
   :lifecycleRoute (:lifecycleRoute listing)
   :sourcing (:sourcing listing)})

;; ── Wellbecoming ordering (G5) — never paid placement ─────────────────────────
(defn- wellbecoming-score
  "Higher = better. Same axes as okaimono (durability + repairability + dignified
  labor, lightly penalize carbon + price). NEVER engagement/upsell (G5)."
  [p]
  (+ (* (double (get p :durabilityYears 0.0)) 2.0)
     (* (double (get p :repairability 0)) 1.5)
     (* (double (get labor-rank (get p :laborProvenance "unknown") 0)) 3.0)
     (* (double (get p :carbonKg 0.0)) -0.1)
     (* (/ (double (get p :priceMinor 0)) 1000000.0) -0.05)))

(defn storefront-ordering
  "Order a storefront's listings by Wellbecoming (G5) — never by paid placement,
  sponsorship, or conversion (no such field exists)."
  [listings]
  (sort-by wellbecoming-score > listings))

;; ── settlement (G2 zero-commission, G7 tithe, G12 no-server-key) ──────────────
(defn build-settlement-intent
  "USDC settlement with TitheRouter 10% auto-split (G7) and ZERO platform commission (G2).
  The arithmetic is the canonical contract: gross = tithe + sellerNet exactly — the
  platform's cut is absent, not zeroed-after-the-fact.
  R2 Autonomous: operator-ref is no longer required for execution."
  ([gross-minor seller-did]
   (build-settlement-intent gross-minor seller-did nil))
  ([gross-minor seller-did operator-ref]
   (let [gross (long gross-minor)
         tithe (quot (* gross tithe-bps) 10000)
         seller-net (- gross tithe)]    ; tithe rounds down ⇒ sellerNet absorbs remainder; sum exact
     {:rail "usdc-base-l2"
      :grossMinor gross
      :commissionMinor 0               ; G2: structural zero — the platform takes nothing
      :titheMinor tithe
      :sellerNetMinor seller-net
      :sellerDid seller-did
      :titheRouter "50-infra/etzhayyim-tithe-router"
      :serverHeldKey false             ; G12 invariant
      :state "executed"               ; R2 Autonomous
      :operatorRef (or operator-ref "autonomous_r2")
      :signed false})))

(defn authorize-settlement
  "Authorize a settlement intent. ONLY a member-origin signature (buyer/seller) is
  accepted (G12 no-server-key); a platform/server signature is refused. Does not itself
  broadcast (G7 — needs operator-ref via build-settlement-intent)."
  [settlement signature]
  (cond
    (not= (get signature :origin) "member")
    (merge settlement {:signed false :refused true
                       :reason "only a member passkey/wallet signature authorizes settlement (G12 no-server-key)"})

    (:serverHeldKey settlement)
    (merge settlement {:signed false :refused true
                       :reason "settlement carries a server-held key — invariant violation (G12)"})

    :else
    (merge settlement {:signed true :signatureRef (get signature :ref)})))

;; ── inventory (G5 honest count, no-oversell) ──────────────────────────────────
(defn available-inventory
  "On-hand inventory minus the quantity reserved by still-active orders for this listing.
  A cancelled order releases its units. This is the honest available count (G5) and the
  basis of the no-oversell guard."
  ([listing]
   (available-inventory listing nil))
  ([listing open-orders]
   (let [listing-id (:listingId listing)
         reserved (reduce (fn [acc o]
                            (if (and (= (get o :listingId) listing-id)
                                     (not= (get o :state) "cancelled"))
                              (+ acc (int (get o :qty 0)))
                              acc))
                          0
                          (or open-orders []))]
     (- (int (get listing :inventory 0)) reserved))))

;; ── order flow (G1 consent, G3 SBT↔SBT, G5 no-oversell, G2/G7 settlement, G8 fulfilment) ──
(defn place-order
  "Ring-1 order entry. Requires buyer consent (G1) + an active buyer SBT (G3 SBT↔SBT),
  computes a zero-commission settlement intent (G2/G7) and a non-gig fulfilment (G8).
  Refuses if the requested qty exceeds AVAILABLE inventory (no-oversell, G5).
  Refused orders never reach :settle-intent."
  ([buyer-did listing qty consent-ref sbt-registry]
   (place-order buyer-did listing qty consent-ref sbt-registry nil))
  ([buyer-did listing qty consent-ref sbt-registry open-orders]
   (cond
     (not (seq consent-ref))
     {:state "refused" :reason "missing DID-signed consent (G1)" :ring "internal"}

     (not (get sbt-registry buyer-did false))
     {:state "refused" :reason "buyer is not an active Adherent SBT holder (§3/G3)" :ring "internal"}

     (> (int qty) (available-inventory listing open-orders))
     {:state "refused" :reason "insufficient available inventory — no oversell (honest count, G5)" :ring "internal"}

     :else
     (let [gross (* (int (:priceMinor listing)) (int qty))
           settlement (build-settlement-intent gross (:sellerDid listing))
           order-id (str (:listingId listing) ".ord."
                         (format "%04x" (bit-and (Math/abs (hash (str buyer-did consent-ref))) 0xFFFF)))]
       {:state "settle-intent"
        :ring "internal"
        :orderId order-id
        :buyerDid buyer-did
        :listingId (:listingId listing)
        :qty (int qty)
        :consentRef consent-ref
        :subtotalMinor gross
        :settlement settlement
        :fulfilmentActor (:fulfilmentActor listing)
        :recordEnc true}))))           ; G9: order PII via com.etzhayyim.encrypted.*

(defn advance-order
  "Move an order one step along ORDER_STATES (caps at in-use, never a terminal
  'consumed' state — hands to lifecycle, G13)."
  [order]
  (let [st (:state order)
        i (.indexOf order-states st)]
    (if (neg? i)
      order
      (assoc order :state (nth order-states (min (inc i) (dec (count order-states))))))))

(defn cancel-order
  "Cancel an order, releasing its inventory reservation. A delivered/in-use order cannot be
  cancelled (the goods already moved). Cancellation is itself append-only state (G7)."
  [order]
  (if (contains? #{"delivered" "in-use"} (:state order))
    (assoc order :refused true :reason "cannot cancel an order already delivered")
    (assoc order :state "cancelled")))

(defn build-fulfilment
  "Hand an order to an etzhayyim logistics actor (todoke/…); never a gig courier (G8). The
  handoff carries no server key (proof is on-device at delivery, G12-aligned with todoke)."
  ([order] (build-fulfilment order "jp"))
  ([order region]
   {:orderId (:orderId order)
    :fulfilmentActor (get order :fulfilmentActor "todoke")
    :region region
    :gig false               ; G8: no gig labour on the etzhayyim leg
    :serverSigned false      ; G12: proof-of-delivery is member/recipient-signed, not server
    :state "handed-off"}))

;; ── main (smoke demo) ─────────────────────────────────────────────────────────
(defn main [& _]
  (let [sbt {"did:web:etzhayyim.com:mitsuho" true "did:plc:buyer-alice" true}
        sf (open-storefront "did:web:etzhayyim.com:mitsuho" "Mitsuho Rice" sbt)
        listing (create-listing sf "Koshihikari 5kg" 8000000 :inventory 40)
        settlement (build-settlement-intent 10000000 (:sellerDid sf))]
    (println "storefront:" (:state sf) "kind:" (:sellerKind sf))
    (println "listing ring:" (:ring listing) "fulfilment:" (:fulfilmentActor listing))
    (println "settlement: gross=" (:grossMinor settlement)
             "tithe=" (:titheMinor settlement)
             "sellerNet=" (:sellerNetMinor settlement)
             "commission=" (:commissionMinor settlement)
             "state=" (:state settlement))))

(when (= *file* (System/getProperty "babashka.file"))
  (main))
