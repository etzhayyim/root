---
id: adr-2606112301-tate-citizen-legal-defense-concierge-r0
title: "ADR-2606112301: tate 盾 — citizen legal-defense concierge (不利条項スキャン + 法的手続き応答支援), Tier-B actor R0"
status: proposed
doc_type: adr
topic: tate-citizen-legal-defense
authoritative: true
last_verified: 2026-06-11
priority: 5.0
axis: architecture
weight: 0.50
priority_note: "second leg of the 縁切り wave (ADR-2606112201): from severing unused ties to defending against disadvantageous terms + incoming legal procedures"
authoritative_for:
  - tate-actor-charter
  - clause-pattern-registry
  - procedure-response-registry
depends_on:
  - adr-2606112201 # kaiyaku 縁切り executor (route target)
  - adr-2605262700 # chigiri legal-procedure substrate (UPL prior art)
  - adr-2605231525 # no-server-key
  - adr-2605215000 # Murakumo-only inference
  - adr-2605312345 # kotoba Datom log = canonical state
related:
  - adr-2605312500 # kurashimori (クーリングオフ/返金 rights — route target)
  - adr-2606060900 # tasuke (架空請求/詐欺 victim support — fake-guard route)
  - adr-2605312030 # toritsugi (default-self-submit pattern)
  - adr-2605181100 # encrypted consent envelope
supersedes: []
superseded_by: []
---

# ADR-2606112301: tate 盾 — citizen legal-defense concierge, Tier-B actor R0

**Status**: proposed
**Date**: 2026-06-11
**Deciders**: Jun Kawasaki

# Context

Extending the 縁切り initiative (ADR-2606112201), the founder asked for two further
member-protection surfaces: **(a)** 不要な支払い・クレジットカードの契約・利用規約や
法人契約のなかに**不利な契約**をしていないかの検出, and **(b)** 少額訴訟・政府・企業
からの**法的手続きへの個人としての対応支援**.

Roster survey: kurashimori owns クーリングオフ/返金 *rights* (explicitly NOT 解約);
toritsugi owns *proactive* government procedures; tasuke owns cybercrime *victim
recovery*; chigiri is the legal-procedure *substrate* (R0, UPL-prohibited); kaiyaku
(just landed) owns *severance execution*. **Nobody owns** (a) contract-terms review or
(b) the defensive response to an incoming 支払督促 / 少額訴訟呼出 / 訴状 / 行政処分 /
内容証明 — including the 架空請求 discrimination problem (fake "court" SMS).

# Decision

Create **tate 盾** (`20-actors/tate/`, `did:web:etzhayyim.com:actor:tate`) — the
**defensive paper layer** for a member as a private individual. 盾 = shield: it only
defends; an offensive leg (drafting claims against others) is a non-goal by
construction. R0 ships pure-stdlib pywasm-ready methods + coded registries + synthetic
seeds + 17 tests green.

## 1. 不利条項スキャン (terms_scan)

Coded clause-pattern registry (`data/clause-patterns.edn`, `:representative`, 14
shapes) over three contexts — `:consumer` ToS, `:card` member agreements, `:b2b`
法人契約: 自動更新トラップ / 過大違約金 / 全部免責 / 年14.6%超遅延損害金 / 専属管轄 /
一方的変更権 / リボ自動設定 / 支払停止の抗弁の放棄 / 年会費自動課金 / 無限賠償 /
競業避止 / 長期支払サイト (下請法60日) / 知財包括譲渡 / 最低期間+更新ロック. A flag =
**pattern + DISCLOSED statutory anchor** (消費者契約法8条・9条1号・9条2号・10条 /
民法548条の2・90条 / 割賦販売法30条の2の3・30条の4 / 下請法2条の2・4条2項3号 /
独禁法) + risk + **route** `:kurashimori | :kaiyaku | :referral | :info`. **G2
non-adjudicating**: never a validity verdict; every entry `:verify-current-law true`.
**G5 context honesty**: consumer anchors structurally never fire on `:b2b` docs.

## 2. 法的手続き応答支援 (respond_plan)

Coded procedure registry (`data/procedure-registry.edn`) for notices an individual
RECEIVES: 支払督促 (督促異議 2週間 — 民訴391・393条), 少額訴訟呼出 (答弁書 — 159条;
通常移行申述 — 373条; 異議 — 378条; ceiling 60万円 — 368条), 訴状 (答弁書/欠席判決 —
159条3項・254条), 行政処分 (審査請求 3月 — 行審法18条1項; 取消訴訟 6箇月 — 行訴法14条
1項), 内容証明 (法定期限なし — 書面対応). Plans carry deadline **rules** (G4: never a
computed date; `verify_service_date` always true), options (G3 UPL: `:self-submit` /
`:self-decide` only, **representation unrepresentable** — `_make_option` raises), a
self-submit checklist, and referral triggers (G7: 本訴 / >60万 / 執行段階 → 法テラス
0570-078374 / 弁護士会 / 認定司法書士).

## 3. 架空請求 guard (G6)

Channel discrimination is structural: genuine 支払督促/訴状 arrive by **特別送達
only** (`:proc/genuine-channel`). Court vocabulary on SMS/email/普通郵便 →
`:suspected-fake`: the plan opens with `do-not-contact-sender`, preserves evidence,
offers **no deadlines or options**, and routes to tasuke 助 / 警察相談 #9110 /
消費者ホットライン 188. Test-enforced: the same 支払督促 text is `:genuine` via
特別送達 and `:suspected-fake` via email.

## 4. Gates / non-goals / boundaries

G1 member-principal own-documents-only (R0 seeds `:synthetic`; live docs encrypted) ·
G2 non-adjudicating · G3 UPL self-submit-only · G4 deadline-honesty · G5
context-honesty · G6 架空請求 guard · G7 referral-forward · G8 kotoba-EAVT audit
(ground = registries + docs; transient = flags/plans) · G9 Murakumo-only. Non-goals:
N2 **defensive only** (no offensive litigation support, no 取立), N3 no evasion of
lawful obligations, N4 no counterparty scoring/blacklist (反個人主義), N6 刑事 →
immediate referral. Boundaries: tate detects/responds; kurashimori exercises rights;
kaiyaku severs; tasuke recovers; toritsugi proacts; chigiri is substrate.

## R0 scope (this ADR)

`manifest.edn` + `CLAUDE.md` + 2 coded registries + synthetic member-docs seed +
`terms_scan.py` / `respond_plan.py` / `datom_emit.py` + 17 tests green. Cells are
manifest-declared scaffolds; live member-doc ingest (encrypted, consent-bound),
Murakumo notice classification, and template rendering are R1+ follow-ups behind
their gates.

# Consequences

- The two asked-for surfaces now exist with test-enforced honesty: contract risk is
  *pointed at* (anchor), never *adjudicated*; procedure deadlines are *rules to
  verify*, never computed dates; fakes are *guarded against contact* before anything
  else.
- The 縁切り wave composes: tate `:kaiyaku` routes feed the severance ledger
  (auto-renewal windows → kaiyaku notice-days), `:kurashimori` routes feed rights
  exercise.
- Statutory registry entries are a maintenance liability — every entry carries
  `:verify-current-law true` and amendments must cite current statute text.
- UPL exposure is bounded the same way as chigiri/toritsugi/kurashimori/tasuke:
  free, generic registry shapes, member self-submit, referral-forward.

# Alternatives Considered

1. **Extend kurashimori.** Rejected: kurashimori is rights-exercise (クーリングオフ/
   返金); terms-review + procedure-defense is a different surface with different
   gates (deadline honesty, fake-guard), and kurashimori's ADR explicitly bounds its
   scope.
2. **Extend chigiri.** Rejected: chigiri is the *substrate* registry; tate is a
   member-facing concierge composed over it (same relation as toritsugi).
3. **Two actors (terms-scan vs procedure-response).** Rejected for R0: both legs are
   "the member's own defensive paper", share G1–G5, and shiori precedent allows
   fused analyse+route actors; split later if either leg grows live legs.
4. **LLM-based clause detection at R0.** Rejected: coded keyword registry first —
   deterministic, testable, pywasm-ready; Murakumo classification is an R1+ assist
   behind G9.

# References

- `20-actors/tate/` (this actor) · ADR-2606112201 (kaiyaku) · ADR-2605312500
  (kurashimori) · ADR-2605262700 (chigiri) · ADR-2606060900 (tasuke) · ADR-2605312030
  (toritsugi) · ADR-2605312345 (Datom canonical state) · ADR-2605231525
  (no-server-key) · ADR-2605215000 (Murakumo-only) · ADR-2605181100 (encrypted
  envelope)
- Statutory anchors referenced (all `:verify-current-law`): 消費者契約法8–10条,
  民法90条・548条の2・548条の4, 割賦販売法30条の2の3・30条の4, 下請法2条の2・4条2項
  3号, 民事訴訟法159条・254条・368条・373条・378条・391条・393条, 行政不服審査法18条
  1項, 行政事件訴訟法14条1項, 弁護士法72条
