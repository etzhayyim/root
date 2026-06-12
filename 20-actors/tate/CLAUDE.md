# tate 盾 — citizen legal-defense concierge

**DID**: `did:web:etzhayyim.com:actor:tate` · **Tier**: B · **Status**: 🟡 R0 ·
**ADR**: 2606112301 · **depends**: 2606112201 (kaiyaku) · 2605312500 (kurashimori) ·
2605262700 (chigiri UPL prior art) · 2606060900 (tasuke) · 2605231525 (no-server-key) ·
2605215000 (Murakumo-only) · 2605312345 (Datom = canonical state)

## What this is

The **defensive paper layer** for a member as a private individual (盾 = shield — it only
ever defends). Two legs over the member's OWN documents:

1. **不利条項スキャン** (`methods/terms_scan.py`) — the member's consumer ToS /
   credit-card member agreements / B2B 法人契約 matched against a coded clause-pattern
   registry (`data/clause-patterns.edn`): 自動更新トラップ, 過大違約金, 全部免責,
   年14.6%超の遅延損害金, 専属管轄, リボ自動設定, 支払停止の抗弁の放棄, 無限賠償,
   競業避止, 長期支払サイト, 知財包括譲渡, 最低期間+自動更新ロック. Each flag =
   **pattern + DISCLOSED statutory anchor** (消費者契約法8–10条 / 民法548条の2 /
   割賦販売法 / 下請法 / 独禁法) + **route**: `:kurashimori` (rights) / `:kaiyaku`
   (sever the tie) / `:referral` (professional) / `:info`. **Never a validity verdict.**
2. **法的手続き応答支援** (`methods/respond_plan.py`) — notices an individual RECEIVES
   (支払督促 / 少額訴訟呼出 / 訴状 / 行政処分 / 内容証明) classified against a coded
   procedure registry (`data/procedure-registry.edn`) → DISCLOSED deadline **rules**
   (民訴391・393条 督促異議 2週間, 373条 通常移行, 378条 異議, 159条 擬制自白;
   行審法18条1項 3月; 行訴法14条1項 6箇月) + response options (督促異議 / 答弁書 /
   通常移行申述 / 審査請求 / 書面回答) + self-submit checklist + referral triggers.

**架空請求 guard (G6)**: genuine 支払督促/訴状 arrive by **特別送達 only**. Court
vocabulary on SMS / email / 普通郵便 → `:suspected-fake`: the plan's first step is
`do-not-contact-sender`, evidence is preserved, and the member routes to **tasuke 助 /
警察相談 #9110 / 消費者ホットライン 188**. No deadlines or options are offered on a fake.

## Hard gates (constitutional — read before any change)

- **G1 member-principal, own documents only.** R0 seeds are fully `:synthetic`; live
  member docs are consent-bound + encrypted (`com.etzhayyim.encrypted.*`).
- **G2 non-adjudicating.** A flag is a pointer to a disclosed statute
  (`:verify-current-law true` everywhere — statutes amend), never "this clause is
  invalid". Report language stays 可能性/専門家確認 (test-enforced).
- **G3 UPL (弁護士法72条).** No representation — `_make_option` **raises** on
  `:representation`; every option is `:self-submit` / `:self-decide`,
  `submitted_by: member`. No individualized legal judgment; options come verbatim
  from the coded registry.
- **G4 deadline honesty.** tate **never computes a calendar date** — it emits the
  disclosed rule text + anchor + `verify_service_date: true`; the member confirms
  when they were actually served.
- **G5 context honesty.** Consumer anchors never fire on `:b2b` docs (disjoint by
  construction in `scan_doc`); B2B routes referral-forward instead.
- **G7 referral-forward.** 本訴 / claim >¥600,000 (少額訴訟 ceiling, 民訴368条) /
  執行段階 / 重大処分 always carry 法テラス 0570-078374 / 弁護士会 / 認定司法書士.

## Non-goals

N1 not a law firm / no advice · **N2 defensive only** — never drafts claims/suits
AGAINST others, no 取立 · N3 no evasion of lawful obligations (genuine debt/deadline
surfaced honestly) · N4 never scores the counterparty (clauses are flagged, companies/
persons are not — no blacklist, 反個人主義) · N5 kurashimori owns クーリングオフ/返金,
toritsugi owns proactive 行政手続 — tate owns the defensive response surface ·
N6 刑事 out of scope → immediate 弁護士 referral.

## Boundaries (who owns what)

| Concern | Owner |
|---|---|
| 不利条項の検出 + 法的手続きへの応答 (防御) | **tate** (this actor) |
| クーリングオフ / 返金 / 消費者庁 escalation (rights) | **kurashimori** |
| 解約 / 退会の実行 (縁切り executor) | **kaiyaku** (tate routes `:kaiyaku` hits there) |
| 架空請求 / 詐欺被害の回復 | **tasuke** (G6 fake-guard routes there) |
| proactive 政府手続き concierge | **toritsugi** |
| legal-procedure substrate (registry 基盤) | **chigiri** |

## Layout

```
20-actors/tate/
├── CLAUDE.md                      # this file
├── manifest.edn                   # actor manifest (5 cells, 9 gates, 6 non-goals)
├── data/
│   ├── clause-patterns.edn        # coded clause-pattern registry (:representative)
│   ├── procedure-registry.edn     # coded procedure registry (disclosed rules)
│   └── seed-member-docs.edn       # SYNTHETIC member contracts + notices (G1)
├── methods/                       # pure-stdlib → kotoba pywasm-runnable
│   ├── terms_scan.py              # 不利条項 scanner (non-adjudicating flags)
│   ├── respond_plan.py            # response planner + 架空請求 guard
│   └── datom_emit.py              # kotoba Datom-log (EAVT) emitter
├── tests/                         # 17 tests, pure stdlib
│   ├── test_terms.py
│   └── test_respond.py
└── out/                           # GENERATED — do not hand-edit
    ├── clause-readout.md
    ├── response-plans.md
    └── tate-datoms.kotoba.edn
```

## Run

```bash
cd 20-actors/tate
python3 methods/terms_scan.py      # → out/clause-readout.md
python3 methods/respond_plan.py    # → out/response-plans.md (dry-run)
python3 methods/datom_emit.py      # → out/tate-datoms.kotoba.edn (EAVT)
python3 tests/test_terms.py && python3 tests/test_respond.py   # 17 green
```

## Do not

- Do not emit a validity verdict, drop a statutory anchor, or apply a consumer-law
  anchor to a `:b2b` document — G2 / G5 (tests enforce).
- Do not add a `:representation` option kind or any claim-drafting / offensive leg —
  G3 / N2 (`_make_option` raises; tests enforce).
- Do not compute a calendar deadline or offer options on a `:suspected-fake` notice —
  G4 / G6 (tests enforce: fake plans have no deadlines/options and open with
  do-not-contact-sender).
- Do not score or blacklist counterparties — N4.
- Do not ingest real member documents into `data/` — seeds stay `:synthetic`; live
  docs are consent-gated + encrypted (ADR-2605181100).
- Statutory rules in the registries carry `:verify-current-law true` — when amending
  them, cite the current statute text, never memory.
