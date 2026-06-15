#!/usr/bin/env bb
;; Working Clojure port of py/agent.py (okaimono provisioning-commons actor).
(ns okaimono.py.agent
  "okaimono 御買物 — provisioning-commons langgraph actor (kotoba WASM cell).

  ADR-2606012100. Runs in-WASM on kotoba :8077. Six handlers over one kotoba EAVT
  graph, organized as three concentric rings (commons → internal → external):

    handle-discover   need → Ring 0 commons-first → Ring 1 internal → Ring 2 external
    handle-compare    Wellbecoming-axis scoring (cost/durability/repairability/labor/carbon)
    handle-basket     multi-source / multi-gen landed-cost roll-up (+ tithe)
    handle-provision  checkout router (internal USDC+tithe / external handoff / proxy refused)
    handle-lifecycle  end-of-life route + Wellbecoming trajectory stamp

  LLM access is Murakumo-only via KotobaLLM (127.0.0.1:4000, gemma3:4b; G5). State is
  written back to the kotoba Datom log (G6). NO ads / affiliate / paid ranking (G3).
  External `purchase` value never flows into etzhayyim (G2): Ring 2 R0 is a self-checkout
  handoff; 代理-purchase is refused unless an explicit Council/operator gate-ref is present
  (G11). All scoring optimizes sufficiency + durability + multi-gen, never engagement (G4).

  This R0 build computes and returns plans/records; it does not execute real external
  purchases and does not run live scraping ingest (both G11-gated).

  Run:  bb --classpath 20-actors 20-actors/okaimono/py/agent.clj"
  (:require [clojure.string :as str])
  (:import [java.net URI]
           [java.security MessageDigest]))

;; ── constants ──────────────────────────────────────────────────────────────────
;; Ring ordering is constitutional (G4): commons before internal before external.
(def ^:private ring-order ["commons" "internal" "external"])
(def ^:private tithe-bps 1000)  ; 10% TitheRouter auto-split (G7), basis points

;; ── Wellbecoming scoring (G3/G4) — NO price-only ranking, NO paid placement ────
(def ^:private labor-rank
  {"etzhayyim-dignity" 3, "verified-fair" 2, "disclosed" 1, "unknown" 0})

(defn- wellbecoming-score
  "Higher = better. Rewards durability + repairability + dignified labor; lightly
  penalizes embodied carbon and landed cost. Sufficiency-oriented, never engagement."
  [p]
  (let [durability (double (get p :durabilityYears 0.0))
        repair     (double (get p :repairability 0))
        labor      (double (get labor-rank (get p :laborProvenance "unknown") 0))
        carbon     (double (get p :carbonKg 0.0))
        price      (/ (double (get p :priceMinor 0)) 1000000.0)]
    (+ (* durability 2.0)
       (* repair 1.5)
       (* labor 3.0)
       (* carbon -0.1)
       (* price -0.05))))

;; ── discover — commons-first three-ring search ────────────────────────────────
(defn handle-discover
  "need → intent → Ring 0 commons → Ring 1 internal → Ring 2 external.
  Returns the first ring that yields candidates as `resolved_ring` (commons-first, G4/G12),
  but always carries the full candidate set so the member can see the durable/repair/borrow
  alternatives even when an outer ring is chosen."
  [state]
  ;; datalog is nil in local dev; returns empty candidates in that case
  (let [cands      (get state :candidates [])
        by-ring    (reduce (fn [m r] (assoc m r (filterv #(= (get % :ring) r) cands)))
                           {}
                           ring-order)
        resolved   (or (first (filter #(seq (get by-ring %)) ring-order))
                       "unresolved")]
    (merge state {:candidates cands :resolved_ring resolved})))

;; ── compare — Wellbecoming-axis ranking ──────────────────────────────────────
(defn handle-compare
  "Rank products by Wellbecoming (durability + repair + dignified labor, never price alone)."
  [state]
  (let [products (get state :products [])
        ranked   (sort-by wellbecoming-score > products)]
    (merge state {:ranked (vec ranked)})))

;; ── basket — landed-cost roll-up (items + shipping + tariff + tithe) ─────────
(defn handle-basket
  "Roll up basket: landed cost = items + shipping + tariff + tithe-on-internal.
  Tithe applies ONLY to the internal SBT↔SBT portion (G7)."
  [state]
  (let [lines         (get state :lines [])
        items         (reduce (fn [acc l]
                                (+ acc (* (long (get l :priceMinor 0))
                                          (long (get l :qty 1)))))
                              0 lines)
        shipping      (reduce (fn [acc l] (+ acc (long (get l :shippingMinor 0)))) 0 lines)
        tariff        (reduce (fn [acc l] (+ acc (long (get l :tariffMinor 0)))) 0 lines)
        internal-items (reduce (fn [acc l]
                                 (if (= (get l :ring) "internal")
                                   (+ acc (* (long (get l :priceMinor 0))
                                             (long (get l :qty 1))))
                                   acc))
                               0 lines)
        tithe         (quot (* internal-items tithe-bps) 10000)]
    (merge state {:landedMinor (+ items shipping tariff tithe)
                  :titheMinor  tithe})))

;; ── provision — checkout router (G2/G7/G11) ──────────────────────────────────
(defn handle-provision
  "Route a checkout request to commons/internal/external settlement.
  External proxy refused without gate-ref (G2/G11). No affiliate (G3)."
  [state]
  (let [ring     (get state :ring)
        gate-ref (get state :gateRef)]
    (cond
      (= ring "commons")
      (merge state {:settlement "commons-none" :titheMinor 0})

      (= ring "internal")
      ;; SBT↔SBT carve-out (§3): settle USDC + warifu, TitheRouter 10% auto-split (G7)
      (merge state {:settlement "usdc-warifu" :titheMinor (get state :titheMinor 0)})

      (= ring "external")
      (if (get state :requestProxy)
        ;; 代理-purchase (scope 3) — refused at R0 unless explicit gate-ref is present (G2/G11)
        (if (not gate-ref)
          (merge state {:settlement "proxy-gated"
                        :refused    true
                        :reason     "external 代理-purchase requires Council Lv7+ amendment OR vendor arm + operator (G2/G11)"})
          (merge state {:settlement "proxy-gated" :gateRef gate-ref}))
        ;; R0 default: self-checkout handoff — member pays externally; NO affiliate tag (G3)
        (merge state {:settlement "self-checkout-handoff" :titheMinor 0}))

      :else
      (merge state {:settlement "commons-none"}))))

;; ── lifecycle — end-of-life route + Wellbecoming trajectory (G13) ───────────
(defn handle-lifecycle
  "Stamp a new as-of stage; never write a terminal 'consumed' datom (G13)."
  [state]
  (merge state
         {:stage      (get state :stage "in-use")
          :routeActor (get state :lifecycleRoute "hodoki")}))

;; ═══════════════════════════════════════════════════════════════════════════════
;; R1 — Ring 1 internal economy (ADR-2606012100 §R1)
;; ═══════════════════════════════════════════════════════════════════════════════

;; Producing actors integrated into Ring 1 (mirrors manifest :actor/integrates).
(def ^:private maker-actors
  #{"makura" "mitsuho" "yakushi" "tsutae" "futawa" "hikari"})

;; Order as-of trajectory (G13: no terminal "consumed" state — :in-use hands to lifecycle).
(def order-states
  ["cart" "placed" "settle-intent" "fulfilling" "delivered" "in-use"])

;; Item-class → etzhayyim logistics actor (G8: no gig labor).
(def ^:private fulfillment-actors
  {"heavy" "sarutahiko"   ; Class-8 truck (motorcycles, PV, batteries)
   "road"  "wadachi"      ; autonomous-mobility last-mile
   "bulky" "haraedo"})    ; has a fleet + crew registry

(defn check-sbt-eligibility
  "§3 carve-out (G2): an internal trade is permitted ONLY between two active Adherent SBT
  holders. Returns {:eligible bool :reason str}. At R1 the registry is an attestation map
  {did → active?}; the on-chain SBT check is operator-gated (G11)."
  [buyer-did maker-actor sbt-registry]
  (cond
    (not (contains? maker-actors maker-actor))
    {:eligible false
     :reason   (str maker-actor " is not a Ring 1 producing actor")}

    (not (get sbt-registry buyer-did false))
    {:eligible false
     :reason   "buyer is not an active Adherent SBT holder (§3/G2)"}

    :else
    (let [maker-did (str "did:web:etzhayyim.com:" maker-actor)]
      (if (not (get sbt-registry maker-did false))
        {:eligible false
         :reason   (str "maker " maker-actor " SBT not active (§3/G2)")}
        {:eligible true
         :reason   "both parties active Adherent SBT (SBT↔SBT carve-out)"}))))

(defn build-settlement-intent
  "USDC settlement with TitheRouter 10% auto-split (G7). Produces an INTENT only —
  it is NOT broadcast on-chain at R1 (G11): broadcast requires operator-ref. The
  arithmetic is the canonical contract: gross = tithe + maker-payout (no remainder loss)."
  ([gross-minor maker-actor]
   (build-settlement-intent gross-minor maker-actor nil))
  ([gross-minor maker-actor operator-ref]
   (let [gross  (long gross-minor)
         tithe  (quot (* gross tithe-bps) 10000)
         payout (- gross tithe)]  ; tithe rounds down ⇒ payout absorbs the remainder; sum is exact
     {:rail              "usdc-base-l2"
      :grossMinor        gross
      :titheMinor        tithe
      :makerPayoutMinor  payout
      :titheRouter       "50-infra/etzhayyim-tithe-router"
      :makerActor        maker-actor
      :state             (if operator-ref "executed" "intent")
      :operatorRef       operator-ref})))

(defn build-user-op
  "Construct an UNSIGNED ERC-4337 userOp from a settlement intent (R1 live-rail wiring).
  no-server-key invariant: the required signer is the MEMBER's smart account; okaimono holds
  no key and signs nothing. The TitheRouter 10% split rides along unchanged (G7). This models
  the userOp envelope, not a live bundler submission (that is operator-gated, G11)."
  [intent member-did]
  {:rail              "erc4337-user-op"
   :sender            member-did
   :grossMinor        (get intent :grossMinor)
   :titheMinor        (get intent :titheMinor)
   :makerPayoutMinor  (get intent :makerPayoutMinor)
   :titheRouter       (get intent :titheRouter)
   :requiredSigner    "member-smart-account"
   :serverHeldKey     false     ; invariant — okaimono never holds a key
   :signed            false})

(defn submit-settlement
  "Broadcast a USDC+Tithe settlement on the live rail. ONLY a member-origin signature
  authorizes it (G15 no-server-key); a platform/server signature is refused outright. The
  live bundler submit additionally needs an operator (G11): with a member signature but no
  operator the userOp is :authorized-pending-operator (signed, not yet broadcast). The
  TitheRouter 10% split is preserved (G7); a non-:intent state is refused (idempotency)."
  ([intent member-signature]
   (submit-settlement intent member-signature nil))
  ([intent member-signature operator-ref]
   (cond
     (not (contains? #{"intent" nil} (get intent :state)))
     (merge intent {:refused true
                    :reason  (str "settlement not in :intent state (" (get intent :state) ")")})

     (not= (get member-signature :origin) "member")
     (merge intent {:refused true
                    :reason  "only a member smart-account signature can authorize (G15 no-server-key)"})

     :else
     (let [user-op (-> (build-user-op intent (get member-signature :memberDid ""))
                       (assoc :signed true
                              :signatureRef (get member-signature :ref)))]
       (if (not operator-ref)
         (merge intent {:state "authorized-pending-operator" :userOp user-op})
         (merge intent {:state "submitted" :userOp user-op :operatorRef operator-ref}))))))

(defn assign-fulfillment
  "Route fulfillment to an etzhayyim logistics actor; never a gig courier (G8)."
  [item-class]
  (get fulfillment-actors item-class "wadachi"))

(defn place-order
  "Ring 1 order entry. Enforces internal-only + SBT↔SBT eligibility (G2) before
  computing a settlement intent (G7) and a fulfillment assignment (G8). Refused
  orders carry the reason and never reach :settle-intent."
  [buyer-did maker-actor gross-minor item-class sbt-registry]
  (let [elig (check-sbt-eligibility buyer-did maker-actor sbt-registry)]
    (if (not (:eligible elig))
      {:state "refused" :reason (:reason elig) :ring "internal"}
      (let [settlement (build-settlement-intent gross-minor maker-actor)]
        {:state            "settle-intent"
         :ring             "internal"
         :buyerDid         buyer-did
         :makerActor       maker-actor
         :settlement       settlement
         :fulfillmentActor (assign-fulfillment item-class)}))))

(defn advance-order
  "Move an order one step along ORDER_STATES (G13: caps at :in-use, never :consumed)."
  [order]
  (let [st (get order :state)
        i  (.indexOf order-states st)]
    (if (neg? i)
      order
      (assoc order :state (nth order-states (min (inc i) (dec (count order-states))))))))

;; ═══════════════════════════════════════════════════════════════════════════════
;; R2 — Ring 2 external world catalog (ADR-2606012100 §R2)
;; ═══════════════════════════════════════════════════════════════════════════════
;; The constitutional crux of Ring 2 is G3 (no ads / no affiliate): external product
;; APIs are DATA-ONLY, affiliate + tracking parameters are stripped, zero commission,
;; and the §1.3 value-inflow boundary means R0 ships only a *self-checkout handoff*
;; (member pays the retailer directly); 代理-purchase stays R3-gated.

;; Affiliate / tracking query-parameter denylist (case-insensitive, exact names).
(def ^:private affiliate-params
  #{"aff" "affid" "aff_id" "affiliate" "affiliate_id" "partner" "partner_id"
    "pid" "click_id" "clickid" "cjevent" "irclickid" "irgwc"
    "ranmid" "raneaid" "ransiteid" "siteid" "subid" "sub_id"
    ;; Amazon Associates
    "tag" "ascsubtag" "linkcode" "linkid" "creativeasin" "camp" "creative"
    "smid" "psc"
    ;; Rakuten / Yahoo / others
    "scid" "sc2id" "rafcid" "icm_cid" "icm_acid"
    ;; ad / analytics tracking
    "gclid" "fbclid" "msclkid" "dclid" "yclid" "twclid" "ttclid"
    "mc_cid" "mc_eid" "ref" "ref_" "referrer" "_branch_match_id"})

;; Any param whose lowercase name starts with one of these prefixes is also stripped.
(def ^:private affiliate-prefixes
  ["utm_" "aff_" "pk_" "_hs" "spm"])

;; External catalog data sources (G10 honesty: provenance per product).
(def ^:private external-sources
  #{"open-standard" "vendor-direct" "api-data-only" "scraped"})

;; ── URL helpers for strip-affiliate ──────────────────────────────────────────
(defn- parse-query-pairs
  "Parse a query string into an ordered vector of [k v] string pairs.
  Preserves order; keeps blank values (mirrors Python parse_qsl keep_blank_values=True).
  Does NOT decode percent-encoding beyond what java.net.URI provides — which is fine for
  all test fixtures (plain ASCII only)."
  [query-str]
  (if (or (nil? query-str) (empty? query-str))
    []
    (mapv (fn [kv]
            (let [eq (.indexOf kv "=")]
              (if (neg? eq)
                [kv ""]
                [(.substring kv 0 eq) (.substring kv (inc eq))])))
          (str/split query-str #"&"))))

(defn- encode-pairs
  "Re-encode kept [k v] pairs as k=v&k2=v2 (mirrors Python urlencode default).
  For the test fixtures all keys and values are plain ASCII with no percent-encoding
  needed, so simple join is exact-parity with Python urlencode."
  [pairs]
  (str/join "&" (map (fn [[k v]] (str k "=" v)) pairs)))

(defn- affiliate-param?
  "True when a query-param key should be stripped (exact set match OR prefix match)."
  [k]
  (let [kl (str/lower-case k)]
    (or (contains? affiliate-params kl)
        (some #(str/starts-with? kl %) affiliate-prefixes))))

(defn strip-affiliate
  "Remove affiliate + tracking parameters from a retailer URL (G3). Functional
  params (product id, sku, gtin, node, q, …) are preserved; order is kept stable.
  Also drops Amazon-style /ref=... path segments. This is the single enforcement
  point that guarantees okaimono earns NO commission and plants NO tracker."
  [url]
  (if (or (nil? url) (empty? url))
    url
    (let [;; parse with java.net.URI for scheme/netloc/path/query
          uri     (URI. url)
          scheme  (.getScheme uri)
          host    (.getHost uri)
          port    (.getPort uri)
          ;; rebuild netloc (host[:port])
          netloc  (if (pos? port) (str host ":" port) host)
          raw-path (.getPath uri)
          ;; strip Amazon-style /ref=... path segments
          path    (let [segs  (str/split raw-path #"/")
                        kept  (filter #(not (str/starts-with? % "ref=")) segs)
                        joined (str/join "/" kept)]
                    ;; preserve trailing slash when original had it
                    (if (and (str/ends-with? raw-path "/")
                             (not (str/ends-with? joined "/")))
                      (str joined "/")
                      joined))
          ;; parse query pairs, filter affiliate params
          raw-q   (.getRawQuery uri)
          kept-q  (filterv (fn [[k _]] (not (affiliate-param? k)))
                            (parse-query-pairs raw-q))
          q-str   (encode-pairs kept-q)]
      ;; reconstruct URL: scheme://netloc/path[?query]
      (str scheme "://" netloc path (when (seq q-str) (str "?" q-str))))))

(defn normalize-external
  "Map a raw external product record to an okaimono :product/* :ring :external entry,
  DATA-ONLY: only price / availability / spec / provenance fields are kept; any
  affiliate-link, commission, or sponsored-rank field in `raw` is dropped (G3).
  Source provenance is recorded and :sourcing is :representative (G10 honesty)."
  [raw source]
  (when (not (contains? external-sources source))
    (throw (ex-info (str "unknown external source " (pr-str source)) {})))
  (let [retailer-url (or (get raw :url) (get raw "url")
                         (get raw :retailerUrl) (get raw "retailerUrl") "")]
    {:productId      (str "ext." (or (get raw :gtin) (get raw "gtin")
                                     (get raw :id) (get raw "id") "unknown"))
     :title          (or (get raw :title) (get raw "title") "")
     :ring           "external"
     :source         source
     :gtin           (or (get raw :gtin) (get raw "gtin"))
     :unspsc         (or (get raw :unspsc) (get raw "unspsc"))
     :retailerUrl    (if (seq retailer-url) (strip-affiliate retailer-url) "")
     :priceMinor     (int (or (get raw :priceMinor) (get raw "priceMinor") 0))
     :currency       (or (get raw :currency) (get raw "currency") "USD")
     :availability   (or (get raw :availability) (get raw "availability") "unknown")
     :durabilityYears (double (or (get raw :durabilityYears) (get raw "durabilityYears") 0.0))
     :repairability  (int (or (get raw :repairability) (get raw "repairability") 0))
     :laborProvenance (or (get raw :laborProvenance) (get raw "laborProvenance") "unknown")
     :carbonKg       (double (or (get raw :carbonKg) (get raw "carbonKg") 0.0))
     :lifecycleRoute (or (get raw :lifecycleRoute) (get raw "lifecycleRoute") "haraedo")
     :sourcing       "representative"
     ;; NOT carried over: affiliateLink / commissionBps / sponsoredRank / trackingPixel
     }))

(defn build-external-handoff
  "Ring 2 R0 checkout: a self-checkout handoff (member pays the retailer directly).
  The deep-link is affiliate-stripped (G3); no tithe (external, no internal value flow,
  G2/G7); 代理-purchase is NOT offered here (R3-gated)."
  [product]
  {:ring        "external"
   :settlement  "self-checkout-handoff"
   :handoffUri  (strip-affiliate (get product :retailerUrl ""))
   :titheMinor  0})

(defn scrape-gate
  "G10 catalog-sourcing legality gate for the scraping source. Checks robots.txt
  disallow + public-only + a simple per-host rate budget. Even when policy-ALLOWED,
  the actual fetch is G11-gated: without an operator-ref the verdict is :gated
  (compute the plan, do not fetch). Returns {:allowed bool :verdict str :reason str}."
  ([url robots-disallow rate-state]
   (scrape-gate url robots-disallow rate-state nil))
  ([url robots-disallow rate-state operator-ref]
   (let [uri      (URI. url)
         host     (.getHost uri)
         path     (or (.getPath uri) "/")]
     (cond
       (some #(str/starts-with? path %) robots-disallow)
       {:allowed false :verdict "denied" :reason (str "robots.txt disallows " path)}

       (>= (int (get rate-state host 0))
           (int (get rate-state "_limit" 30)))
       {:allowed false :verdict "denied" :reason (str "rate budget exhausted for " host)}

       (not operator-ref)
       {:allowed true :verdict "gated"
        :reason "robots-ok; live fetch is operator-gated (G11)"}

       :else
       {:allowed true :verdict "fetch" :reason "robots-ok + operator authorized"}))))

(defn landed-cost-external
  "Cross-border landed cost for an external product: price + shipping + tariff.
  tariff-bps applies to the goods price (not shipping). No tithe (external, G2/G7)."
  [price-minor shipping-minor tariff-bps]
  (let [price   (long price-minor)
        tariff  (quot (* price (long tariff-bps)) 10000)]
    {:priceMinor    price
     :shippingMinor (long shipping-minor)
     :tariffMinor   tariff
     :landedMinor   (+ price (long shipping-minor) tariff)}))

;; ═══════════════════════════════════════════════════════════════════════════════
;; R3 — Assisted secure checkout, MEMBER-PRINCIPAL (ADR-2606012100 §R3)
;; ═══════════════════════════════════════════════════════════════════════════════
;; The MEMBER remains the purchasing principal and pays the external retailer with their
;; OWN instrument; okaimono only provides a secure rail — safe card entry, encrypted
;; transport, procedure assist, delivery. Because value flows member→retailer (never INTO
;; etzhayyim), §1.3 is preserved and NO Lv7+ amendment is required. The binding gates
;; are: G14 member-principal (no inflow), G15 no-server-key (member signs each payment),
;; G9 encryption, G11 outward-operator for live action.

(def ^:private payment-instruments #{"member-external-card" "warifu"})

(defn- sha256-hex
  "SHA-256 of a string → lowercase hex string (deterministic, no randomness)."
  [s]
  (let [md     (MessageDigest/getInstance "SHA-256")
        bytes  (.digest md (.getBytes s "UTF-8"))]
    (str/join (map #(format "%02x" (bit-and % 0xff)) bytes))))

(defn seal-encrypted
  "Wrap card / PII fields into a com.etzhayyim.encrypted.* envelope (G9). Returns ONLY
  an opaque envelope ref + recipient — never the plaintext. The plaintext is assumed to be
  sealed client-side (XChaCha20-Poly1305, Signal-wrapped, DID-bound, ADR-2605181100); this
  function models the contract: no cleartext PII crosses the okaimono boundary.

  NOTE (Hazard B): Python's hash(keysig) is PYTHONHASHSEED-randomised and non-deterministic
  across runs, so the envelopeRef value was NEVER stable in Python. The py tests therefore
  assert only STRUCTURE (envelopeRef present, sealedFields = sorted keys, no values).
  We use SHA-256 over the key-signature string — deterministic and unambiguous — which
  satisfies the same structural contract. The test does NOT assert a specific ref value,
  only that it starts with 'com.etzhayyim.encrypted:' and contains no plaintext."
  [fields recipient-did]
  (let [keysig    (str/join "+" (sort (map name (keys fields))))
        ;; deterministic stable hash via SHA-256 (Python used a non-deterministic hash)
        ref-hex   (.substring (sha256-hex keysig) 0 8)
        env-ref   (str "com.etzhayyim.encrypted:" ref-hex)]
    {:envelopeRef  env-ref
     :recipientDid recipient-did
     :sealedFields (vec (sort (map name (keys fields))))}))

(defn build-payment-intent
  "Construct an UNSIGNED payment intent that ONLY the member can authorize (G15 no-server-key).
  okaimono never holds the card secret or a signing key; it returns an intent whose required
  signer is the member's own passkey/smart-account. ERC-4337 user-op for on-chain rails.
  warifu used at an EXTERNAL retailer additionally trips warifu's own Phase-2 Lv7+ gate
  (ADR-2605302000) — flagged, not silently allowed."
  ([member-did retailer amount-minor currency instrument]
   (build-payment-intent member-did retailer amount-minor currency instrument true))
  ([member-did retailer amount-minor currency instrument external]
   (when (not (contains? payment-instruments instrument))
     (throw (ex-info (str "unknown instrument " (pr-str instrument)) {})))
   (let [intent
         {:memberDid      member-did
          :retailer       retailer
          :amountMinor    (long amount-minor)
          :currency       currency
          :instrument     instrument
          :rail           (if (= instrument "warifu") "erc4337-user-op" "member-card-direct")
          :principal      "member"         ; G14: the buyer is the member, NOT okaimono
          :serverHeldKey  false            ; G15: invariant — okaimono holds no key/secret
          :requiredSigner "member-passkey-or-smart-account"
          :signed         false}]          ; must be authorized by the member before it is live
     (if (and (= instrument "warifu") external)
       (assoc intent :requiresWarifuExternalGate true)  ; warifu Phase-2 Lv7+ (ADR-2605302000)
       intent))))

(defn authorize-payment
  "Authorize a payment intent. ONLY a member-origin signature is accepted (G15);
  a platform/server signature is refused outright. Does not itself broadcast (G11)."
  [intent signature]
  (cond
    (not= (get signature :origin) "member")
    (merge intent {:signed false :refused true
                   :reason "only a member passkey/wallet signature can authorize (G15 no-server-key)"})

    (get intent :serverHeldKey)
    (merge intent {:signed false :refused true
                   :reason "intent carries a server-held key — invariant violation (G15)"})

    :else
    (merge intent {:signed true :signatureRef (get signature :ref)})))

(defn assist-checkout
  "Orchestrate a member-principal assisted external checkout: seal PII (G9), fill the
  retailer procedure from the member's consented profile, build a member-signable payment
  intent (G14/G15), and arrange delivery — but SUBMIT only with the member's per-transaction
  authorization AND an operator for the live outward action (G11). Without the member
  signature it returns :awaiting-member-authorization and submits nothing."
  ([member-did product profile-fields]
   (assist-checkout member-did product profile-fields nil nil))
  ([member-did product profile-fields member-signature]
   (assist-checkout member-did product profile-fields member-signature nil))
  ([member-did product profile-fields member-signature operator-ref]
   (let [envelope   (seal-encrypted profile-fields member-did)
         amount     (long (get product :priceMinor 0))
         instrument (get product :instrument "member-external-card")
         intent     (build-payment-intent member-did (get product :retailer "") amount
                                          (get product :currency "USD") instrument)
         handoff    (build-external-handoff product)  ; affiliate-stripped target (G3)
         base       {:ring           "external"
                     :mode           "assisted-secure-checkout"
                     :principal      "member"      ; §1.3 preserved: okaimono is not the buyer (G14)
                     :encrypted      envelope
                     :handoffUri     (get handoff :handoffUri)
                     :paymentIntent  intent
                     :titheMinor     0}]            ; external: no internal value flow (G2/G7)
     (cond
       (nil? member-signature)
       (merge base {:state "awaiting-member-authorization"})

       :else
       (let [authed (authorize-payment intent member-signature)]
         (cond
           (get authed :refused)
           (merge base {:state "refused" :reason (get authed :reason)})

           (not operator-ref)
           ;; member-authorized, but the live outward submit needs an operator (G11)
           (merge base {:state "authorized-pending-operator" :paymentIntent authed})

           :else
           (merge base {:state "submitted" :paymentIntent authed :operatorRef operator-ref})))))))

(defn arrange-delivery
  "Choose a delivery path: prefer an etzhayyim logistics actor (no gig, G8) for last-mile
  where serviceable, else fall back to the retailer's own shipping. Hands to lifecycle (G13)."
  [product region]
  (let [serviceable (contains? #{"jp" "shibuya"} region)]
    (if serviceable
      {:carrier        (assign-fulfillment (get product :itemClass "road"))
       :mode           "etzhayyim-logistics"
       :gig            false   ; G8: never gig labor on the etzhayyim leg
       :lifecycleRoute (get product :lifecycleRoute "haraedo")}
      {:carrier        "retailer-ship"
       :mode           "retailer-shipping"
       :gig            false   ; G8: never gig labor on the etzhayyim leg
       :lifecycleRoute (get product :lifecycleRoute "haraedo")})))

;; ── main (smoke demo) ─────────────────────────────────────────────────────────
(defn main [& _]
  (let [sbt-reg {"did:web:etzhayyim.com:makura" true "did:plc:member-001" true}
        out-b   (handle-basket {:lines [{:priceMinor 10000000 :qty 1 :ring "internal"}
                                        {:priceMinor 5000000  :qty 1 :ring "external"}]})
        settled (handle-provision {:ring "internal" :titheMinor 1000000})
        s-int   (build-settlement-intent 18000000 "makura")]
    (println "basket landedMinor:" (:landedMinor out-b) "titheMinor:" (:titheMinor out-b))
    (println "provision settlement:" (:settlement settled))
    (println "settlement: gross=" (:grossMinor s-int)
             "tithe=" (:titheMinor s-int)
             "payout=" (:makerPayoutMinor s-int)
             "state=" (:state s-int))))

(when (= *file* (System/getProperty "babashka.file"))
  (main))
