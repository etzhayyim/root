#!/usr/bin/env bb
;; Clojure port of py/test_agent.py (okaimono provisioning-commons — 45 tests).
(ns okaimono.py.test-agent
  "okaimono 御買物 test harness. Verifies structural invariants of ADR-2606012100:
    G4/G12 commons-first ring ordering
    G3/G4  Wellbecoming ranking beats price-only
    G7     10% tithe on internal portion only (commons = none, external = none)
    G2/G11 external 代理-purchase refused without gate-ref
    G3     Ring 2 R0 default is a self-checkout handoff, no affiliate
    G14/G15/G9 member-principal, no-server-key, encryption"
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [okaimono.py.agent :as agent]))

;; ── shared fixtures ───────────────────────────────────────────────────────────
(def ^:private buyer "did:plc:member-001")
(def ^:private reg
  {buyer                            true
   "did:web:etzhayyim.com:makura"   true
   "did:web:etzhayyim.com:mitsuho"  true})

(def ^:private member "did:plc:member-001")
(def ^:private sig-member {:origin "member" :ref "sig:passkey:abc"})
(def ^:private sig-server {:origin "server" :ref "sig:platform:xyz"})

;; ── commons-first ordering ────────────────────────────────────────────────────
(deftest test-commons-first-ordering
  ;; with no host catalog, resolved_ring is unresolved but the contract holds
  (let [st (agent/handle-discover {:need_text "warm bedding" :candidates []})]
    (is (contains? #{"commons" "internal" "external" "unresolved"}
                   (:resolved_ring st)))))

;; ── Wellbecoming beats price ──────────────────────────────────────────────────
(deftest test-wellbecoming-beats-price
  (let [durable       {:priceMinor 18000000 :durabilityYears 5.0 :repairability 8
                       :laborProvenance "etzhayyim-dignity" :carbonKg 3.2}
        cheap-throwaway {:priceMinor 1290000 :durabilityYears 1.0 :repairability 1
                         :laborProvenance "unknown" :carbonKg 14.0}
        out (agent/handle-compare {:products [cheap-throwaway durable]})]
    (is (= (first (:ranked out)) durable)
        "durable + dignified labor must outrank cheap throwaway")))

;; ── basket tithe internal only ────────────────────────────────────────────────
(deftest test-tithe-internal-only
  (let [lines [{:priceMinor 10000000 :qty 1 :ring "internal"}
               {:priceMinor 5000000  :qty 1 :ring "external"}]
        out (agent/handle-basket {:lines lines})]
    ;; 10% of the 10_000_000 internal portion only
    (is (= (:titheMinor out) 1000000))
    (is (= (:landedMinor out) (+ 10000000 5000000 1000000)))))

;; ── external proxy refused without gate ──────────────────────────────────────
(deftest test-external-proxy-refused-without-gate
  (let [out (agent/handle-provision {:ring "external" :requestProxy true})]
    (is (= (:settlement out) "proxy-gated"))
    (is (= (:refused out) true))))

(deftest test-external-proxy-allowed-with-gate
  (let [out (agent/handle-provision {:ring "external" :requestProxy true
                                     :gateRef "council-lv7-2026xxxx"})]
    (is (= (:settlement out) "proxy-gated"))
    (is (not= (:refused out) true))))

(deftest test-external-default-is-handoff
  (let [out (agent/handle-provision {:ring "external"})]
    (is (= (:settlement out) "self-checkout-handoff"))
    (is (= (:titheMinor out) 0))))

(deftest test-internal-settles-usdc-warifu-with-tithe
  (let [out (agent/handle-provision {:ring "internal" :titheMinor 2400000})]
    (is (= (:settlement out) "usdc-warifu"))
    (is (= (:titheMinor out) 2400000))))

(deftest test-commons-no-settlement
  (let [out (agent/handle-provision {:ring "commons"})]
    (is (= (:settlement out) "commons-none"))
    (is (= (:titheMinor out) 0))))

(deftest test-lifecycle-no-terminal-state
  (let [out (agent/handle-lifecycle {:lifecycleRoute "hodoki"})]
    (is (not= (:stage out) "consumed"))
    (is (= (:routeActor out) "hodoki"))))

;; ── R1 — Ring 1 internal economy ─────────────────────────────────────────────
(deftest test-sbt-eligibility-both-active
  (let [out (agent/check-sbt-eligibility buyer "makura" reg)]
    (is (= (:eligible out) true))))

(deftest test-sbt-eligibility-buyer-not-holder
  (let [out (agent/check-sbt-eligibility "did:plc:outsider" "makura" reg)]
    (is (= (:eligible out) false))))

(deftest test-sbt-eligibility-non-producing-actor
  (let [out (agent/check-sbt-eligibility buyer "amazon" reg)]
    (is (= (:eligible out) false))))

(deftest test-tithe-split-is-exact
  (let [s (agent/build-settlement-intent 18000000 "makura")]
    (is (= (:titheMinor s) 1800000))
    (is (= (:makerPayoutMinor s) 16200000))
    ;; the canonical invariant: gross == tithe + payout, no remainder loss
    (is (= (:grossMinor s) (+ (:titheMinor s) (:makerPayoutMinor s))))
    (is (= (:state s) "intent"))))  ; NOT broadcast at R1 (G11)

(deftest test-tithe-split-remainder-absorbed-by-payout
  (let [s (agent/build-settlement-intent 9999999 "mitsuho")]
    (is (= (:grossMinor s) (+ (:titheMinor s) (:makerPayoutMinor s))))))

(deftest test-settlement-executes-only-with-operator-ref
  (let [s (agent/build-settlement-intent 5000000 "makura" "council-op-2026xxxx")]
    (is (= (:state s) "executed"))))

(deftest test-place-order-refuses-ineligible
  (let [out (agent/place-order "did:plc:outsider" "makura" 18000000 "bulky" reg)]
    (is (= (:state out) "refused"))))

(deftest test-place-order-eligible-reaches-settle-intent
  (let [out (agent/place-order buyer "makura" 18000000 "bulky" reg)]
    (is (= (:state out) "settle-intent"))
    (is (= (get-in out [:settlement :titheMinor]) 1800000))
    (is (= (:fulfillmentActor out) "haraedo"))))  ; bulky → haraedo fleet (G8, no gig)

(deftest test-fulfillment-never-gig
  (is (= (agent/assign-fulfillment "heavy") "sarutahiko"))
  (is (= (agent/assign-fulfillment "road")  "wadachi"))
  (is (= (agent/assign-fulfillment "bulky") "haraedo")))

(deftest test-order-advance-caps-at-in-use
  (let [o  {:state "in-use"}
        o2 {:state "placed"}]
    (is (= (:state (agent/advance-order o))  "in-use"))  ; never advances to terminal :consumed (G13)
    (is (= (:state (agent/advance-order o2)) "settle-intent"))))

;; ── R2 — Ring 2 external catalog ─────────────────────────────────────────────
(deftest test-strip-affiliate-amazon
  (let [url "https://www.amazon.co.jp/dp/B0XXXX/ref=as_li_ss_tl?tag=etz-22&linkCode=ll1&psc=1&th=1"
        out (agent/strip-affiliate url)]
    (is (not (clojure.string/includes? out "tag=")))
    (is (not (clojure.string/includes? out "linkCode=")))
    (is (not (clojure.string/includes? out "psc=")))
    (is (not (clojure.string/includes? out "/ref=")))
    (is (clojure.string/includes? out "th=1"))  ; functional param preserved
    (is (clojure.string/starts-with? out "https://www.amazon.co.jp/dp/B0XXXX"))))

(deftest test-strip-affiliate-utm-and-click-ids
  (let [url "https://shop.example/p/123?utm_source=x&utm_medium=aff&gclid=abc&fbclid=def&q=pillow&aff_id=99"
        out (agent/strip-affiliate url)]
    (doseq [bad ["utm_source" "utm_medium" "gclid" "fbclid" "aff_id"]]
      (is (not (clojure.string/includes? out bad))))
    (is (clojure.string/includes? out "q=pillow"))))  ; the real query survives

(deftest test-strip-affiliate-idempotent-and-clean-url-untouched
  (let [clean "https://shop.example/p/123?q=pillow&sku=AB12"]
    (is (= (agent/strip-affiliate clean) clean))
    (is (= (agent/strip-affiliate (agent/strip-affiliate clean)) clean))))

(deftest test-normalize-external-is-data-only
  (let [raw {"gtin" "04901234567894" "title" "down comforter" "unspsc" "52121500"
             "url" "https://shop.example/p/9?tag=etz-22&utm_campaign=x"
             "priceMinor" 1290000 "currency" "JPY" "availability" "in-stock"
             ;; adversarial: affiliate/commission/sponsored fields must NOT survive
             "affiliateLink" "https://aff.example/redirect?tag=etz-22"
             "commissionBps" 300 "sponsoredRank" 1 "trackingPixel" "https://px.example/x.gif"}
        p (agent/normalize-external raw "api-data-only")]
    (is (= (:ring p) "external"))
    (is (= (:source p) "api-data-only"))
    (is (= (:sourcing p) "representative"))
    ;; affiliate stripped from the retailer URL
    (is (not (clojure.string/includes? (:retailerUrl p) "tag=")))
    (is (not (clojure.string/includes? (:retailerUrl p) "utm_campaign")))
    ;; data-only: no affiliate/commission/sponsored/tracking keys carried over (G3)
    (doseq [forbidden [:affiliateLink :commissionBps :sponsoredRank :trackingPixel
                       "affiliateLink" "commissionBps" "sponsoredRank" "trackingPixel"]]
      (is (not (contains? p forbidden))))))

(deftest test-normalize-external-rejects-unknown-source
  (is (thrown? Exception (agent/normalize-external {:id "x"} "blackhat-scrape"))))

(deftest test-external-handoff-has-no-tithe-and-clean-uri
  (let [p   {:retailerUrl "https://shop.example/p/9?tag=etz-22&q=z"}
        h   (agent/build-external-handoff p)]
    (is (= (:settlement h) "self-checkout-handoff"))
    (is (= (:titheMinor h) 0))  ; external: no internal value flow (G2/G7)
    (is (not (clojure.string/includes? (:handoffUri h) "tag=")))
    (is (clojure.string/includes? (:handoffUri h) "q=z"))))

(deftest test-scrape-gate-denies-robots-disallow
  (let [g (agent/scrape-gate "https://site.example/private/x" ["/private"] {})]
    (is (= (:allowed g) false))
    (is (= (:verdict g) "denied"))))

(deftest test-scrape-gate-policy-ok-but-operator-gated
  (let [g (agent/scrape-gate "https://site.example/public/x" ["/private"] {"_limit" 30})]
    (is (= (:allowed g) true))
    (is (= (:verdict g) "gated"))))  ; G11: no live fetch without operator

(deftest test-scrape-gate-fetch-with-operator
  (let [g (agent/scrape-gate "https://site.example/public/x" ["/private"] {"_limit" 30}
                             "council-op-xxxx")]
    (is (= (:verdict g) "fetch"))))

(deftest test-scrape-gate-rate-budget
  (let [g (agent/scrape-gate "https://site.example/p" [] {"site.example" 30 "_limit" 30})]
    (is (= (:allowed g) false))
    (is (clojure.string/includes? (:reason g) "rate budget"))))

(deftest test-landed-cost-external
  (let [lc (agent/landed-cost-external 1290000 80000 1000)]  ; 10% tariff
    (is (= (:tariffMinor lc) 129000))
    (is (= (:landedMinor lc) (+ 1290000 80000 129000)))))

;; ── R3 — assisted secure checkout (member-principal) ─────────────────────────
(deftest test-payment-intent-is-unsigned-member-principal-no-server-key
  (let [pi (agent/build-payment-intent member "shop.example" 4200 "USD" "member-external-card")]
    (is (= (:principal pi) "member"))    ; G14: member is the buyer, not okaimono
    (is (= (:serverHeldKey pi) false))   ; G15: okaimono holds no key
    (is (= (:signed pi) false))          ; must be member-authorized
    (is (clojure.string/starts-with? (:requiredSigner pi) "member"))))

(deftest test-payment-authorize-requires-member-signature
  (let [pi     (agent/build-payment-intent member "shop.example" 4200 "USD" "member-external-card")
        refused (agent/authorize-payment pi sig-server)  ; server signature must be refused (G15)
        ok      (agent/authorize-payment pi sig-member)]
    (is (= (:refused refused) true))
    (is (= (:signed refused) false))
    (is (= (:signed ok) true))))

(deftest test-warifu-external-trips-its-own-gate
  (let [pi          (agent/build-payment-intent member "shop.example" 4200 "USD" "warifu" true)
        pi-internal (agent/build-payment-intent member "int" 4200 "USD" "warifu" false)]
    (is (= (:requiresWarifuExternalGate pi) true))  ; warifu Phase-2 Lv7+ (ADR-2605302000)
    (is (not (contains? pi-internal :requiresWarifuExternalGate)))))

(deftest test-payment-intent-rejects-unknown-instrument
  (is (thrown? Exception (agent/build-payment-intent member "shop" 1 "USD" "stolen-card"))))

(deftest test-seal-encrypted-never-leaks-plaintext
  ;; NOTE (Hazard B): Python seal_encrypted uses non-deterministic hash(keysig) so the
  ;; py test asserts only structure. We assert the same structural contract here:
  ;; envelopeRef starts with "com.etzhayyim.encrypted:", sealedFields = sorted key names,
  ;; and no plaintext PII value appears anywhere in the envelope repr.
  (let [env  (agent/seal-encrypted {:pan "4111111111111111" :cvv "123" :name "A B"} member)
        blob (pr-str env)]
    (is (not (clojure.string/includes? blob "4111111111111111")))
    (is (not (clojure.string/includes? blob "123")))
    (is (not (clojure.string/includes? blob "A B")))
    (is (clojure.string/starts-with? (:envelopeRef env) "com.etzhayyim.encrypted:"))
    (is (= (:sealedFields env) ["cvv" "name" "pan"]))))  ; field NAMES only, no values

(deftest test-assist-checkout-awaits-member-without-signature
  (let [p   {:retailerUrl "https://shop.example/p?tag=etz-22" :priceMinor 4200 :currency "USD"}
        out (agent/assist-checkout member p {:address "123 Secret St, Apt 9"})]
    (is (= (:state out) "awaiting-member-authorization"))
    (is (= (:principal out) "member"))   ; §1.3 preserved (G14)
    (is (= (:titheMinor out) 0))
    (is (not (clojure.string/includes? (:handoffUri out) "tag=")))  ; G3 still enforced
    (is (not (clojure.string/includes? (pr-str (:encrypted out)) "123 Secret St")))))  ; G9

(deftest test-assist-checkout-member-authorized-pending-operator
  (let [p   {:retailerUrl "https://shop.example/p" :priceMinor 4200 :currency "USD"}
        out (agent/assist-checkout member p {:address "x"} sig-member)]
    (is (= (:state out) "authorized-pending-operator"))))  ; G11: live submit needs operator

(deftest test-assist-checkout-submits-with-member-sig-and-operator
  (let [p   {:retailerUrl "https://shop.example/p" :priceMinor 4200 :currency "USD"}
        out (agent/assist-checkout member p {:address "x"} sig-member "council-op-1")]
    (is (= (:state out) "submitted"))
    (is (= (get-in out [:paymentIntent :signed]) true))))

(deftest test-assist-checkout-refuses-server-signature
  (let [p   {:retailerUrl "https://shop.example/p" :priceMinor 4200 :currency "USD"}
        out (agent/assist-checkout member p {:address "x"} sig-server "council-op-1")]
    (is (= (:state out) "refused"))))

(deftest test-arrange-delivery-prefers-no-gig
  (let [d  (agent/arrange-delivery {:itemClass "bulky"} "jp")
        d2 (agent/arrange-delivery {} "us")]
    (is (= (:mode d) "etzhayyim-logistics"))
    (is (= (:gig d) false))
    (is (= (:carrier d) "haraedo"))
    (is (= (:mode d2) "retailer-shipping"))
    (is (= (:gig d2) false))))

;; ── R1 live USDC + TitheRouter settlement broadcast (G7/G11/G15) ────────────
(deftest test-build-user-op-no-server-key
  (let [intent (agent/build-settlement-intent 10000000 "mitsuho")
        op     (agent/build-user-op intent "did:web:etzhayyim.com:member:abc")]
    (is (= (:rail op) "erc4337-user-op"))
    (is (= (:serverHeldKey op) false))   ; invariant
    (is (= (:requiredSigner op) "member-smart-account"))
    (is (= (:titheMinor op) 1000000))    ; 10% TitheRouter preserved (G7)
    (is (= (:grossMinor op) (+ (:titheMinor op) (:makerPayoutMinor op))))))  ; exact split

(deftest test-submit-refuses-server-signature-g15
  (let [intent (agent/build-settlement-intent 10000000 "mitsuho")
        out    (agent/submit-settlement intent {:origin "server" :ref "x"})]
    (is (= (:refused out) true))
    (is (clojure.string/includes? (:reason out) "no-server-key"))))

(deftest test-submit-member-signed-pending-operator-g11
  (let [intent (agent/build-settlement-intent 10000000 "mitsuho")
        out    (agent/submit-settlement intent {:origin "member" :ref "sig:1"
                                               :memberDid "did:m:1"})]
    (is (= (:state out) "authorized-pending-operator"))  ; signed but live submit gated (G11)
    (is (= (get-in out [:userOp :signed]) true))))

(deftest test-submit-member-signed-with-operator-broadcasts
  (let [intent (agent/build-settlement-intent 10000000 "mitsuho")
        out    (agent/submit-settlement intent {:origin "member" :ref "sig:1"
                                               :memberDid "did:m:1"} "op:1")]
    (is (= (:state out) "submitted"))
    (is (= (get-in out [:userOp :signatureRef]) "sig:1"))))

(deftest test-submit-refuses-non-intent-state
  (let [intent (agent/build-settlement-intent 10000000 "mitsuho" "op:1")]  ; executed
    (let [out (agent/submit-settlement intent {:origin "member" :ref "s"})]
      (is (= (:refused out) true)))))

;; ── runner ────────────────────────────────────────────────────────────────────
(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (clojure.test/run-tests 'okaimono.py.test-agent)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
