# iriai 入会 — global lifeline-commons (電気 / 水道 / ガス / 通信)

The non-profit operator of the four lifelines (ライフライン) **as one commons**. 入会 (iriai) =
the traditional Japanese commons — collectively-held rights of use over a shared resource. The
lifelines are held as a commons right of use (**入会権**), delivered **§1.16 social-security
in-kind** (cash ≡ 0), governed **1 SBT = 1 vote**. The charter-clean inversion of the for-profit
utility — and of utility-as-coercion (a lifeline is never withheld as leverage).

iriai is the **System-of-Systems umbrella** over the producers — 電気→**hikari 光** · 水道→**mizuho
水穂** · ガス→**kamado 竈** · 通信→**noroshi 烽** — covering **infra + 資金 (funding) + 管理
(management)** in one heartbeat. It **never produces and never actuates** a lifeline
(ASSESSMENT + R0 DESIGN ONLY).

`did:web:etzhayyim.com:iriai` · `com.etzhayyim.iriai.*` · **ADR-2606272100** · clj-native R0
(40 tests / 311 assertions green).

## Three layers

| layer | what | output |
|---|---|---|
| **infra** | edge-primary commons-gap `(1−coverage)·essentiality·vulnerability` + resilience (SPOF / N-1) per region × lifeline | verdict ∈ `{await-consent provision reinforce redundancy maintain monitor}` — a coverage map, **never a shut-off list** |
| **資金 fund** | each provision/reinforce/redundancy → §1.16 in-kind proposal (donation→tithe→Public Fund→grant/escrow/in-kind) | **cash ≡ 0** to the consumer; imputed market-equivalent value (transparency-only); advisory, decided 1 SBT = 1 vote |
| **管理 manage** | governance envelope: 1 SBT=1 vote (20%/50%/48h) + Council Lv6+/Lv7+; actuation-class **:intent**; no-server-key | a commons governed by its members, never a sovereign operator |

## Gates

**G1** commons-map-not-shutoff-list · **G2** commons-not-a-market (cash≡0, give-only) ·
**G3** steward-not-sovereign · **G4** non-profit-rails-only · **G5** assessment-only (:intent) ·
**G6** no-server-key · **G7** kotoba-EAVT · **G8** synthetic-seed. The strongest gates are
*structural* — the forbidden acts (shutoff / tariff / actuate / self-fund) have no attribute to
express them, proven by `gates/forbidden-absent?` over the whole datom stream.

## Run

```bash
bb 20-actors/iriai/run_tests.clj                              # all suites
bb --classpath 20-actors 20-actors/iriai/methods/infra.cljc   # coverage + resilience map
bb --classpath 20-actors 20-actors/iriai/methods/fund.cljc    # §1.16 in-kind funding plan
bb --classpath 20-actors 20-actors/iriai/methods/manage.cljc  # 1 SBT=1 vote governance ledger
bb --classpath 20-actors 20-actors/iriai/methods/autorun.cljc # heartbeat → commons ledger
```

Apache 2.0 + etzhayyim Charter Compliance Rider v3.5.
