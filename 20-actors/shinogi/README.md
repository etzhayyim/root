# shinogi 鎬 — exam-competition involution (内卷) system-dynamics observer

> *鎬を削る* — to grind the ridge of one's blade against another's. The idiom for fierce
> mutual competition that wears everyone down for no relative gain. That **is** 内卷
> (involution): effort inflates, the ranking is unchanged, the blades grow thin.

`shinogi` is the **junkan 循環 system-dynamics method** (ADR-2605290927) pointed at one
domain: **high-stakes examination systems** — China's 高考 first, with Korea 수능 / Japan
受験 / India JEE-NEET / Finland / Germany as comparative siblings. From **passive, public,
aggregate** facts it reads which feedback loops are spinning **悪循環 / 好循環**, foregrounds
the **受験失敗 (exam-failure) cycle**, and surfaces **Meadows leverage candidates** — under
one discipline: **it may only look, never touch.**

## What it models — the whole involution LIFECYCLE (the spiral doesn't end at the exam)

Each **driver** (a concrete policy / institution / practice / norm) feeds one of **nine
pressure stocks** with a polarity (`:intensify` / `:relieve` / `:ambiguous`), across three
coupled phases:

| phase | stock | 日本語 |
|---|---|---|
| **1 EXAM** | A `positional-scarcity` | 選抜の希少性（ゼロサムの椅子取り） |
| | B `effort-inflation` | 努力の軍拡（内卷の核） |
| | C `credential-signaling` | 学歴シグナル依存（文凭インフレ） |
| | D `wellbeing-erosion` | 心身ウェルビーイングの侵食 |
| | E `family-capture` | 家計資源の捕獲 |
| | F `failure-penalty` | 失敗ペナルティ（敗者復活の欠如） |
| **2 LABOR** | G `labor-absorption-deficit` | 労働吸収力の不足（**卒業即失業** = graduate unemployment） |
| **3 WITHDRAWAL** | H `effort-efficacy-collapse` | 努力効力感の崩壊（**頑張れない** — structural, not laziness） |
| | I `withdrawal-prevalence` | 離脱の広がり（**躺平/寝そべり** lying flat） |

Drivers: the gaokao itself, 985/211 tiering, 户籍 quotas, 双减, 复读, 衡水模式, 内卷/躺平 norms,
普职分流, one-child legacy, 考研/考公, 高校扩招 (massification), 毕业即失业, 学历贬值, 35岁现象, 996,
慢就业, 全职儿女, 摆烂, 润, 985废物 — plus the lost-generation precedents 就職氷河期/さとり世代/
ひきこもり (JP) and N포세대/헬조선 (KR).

…joined by **ten structural loops** (HYPOTHESES, G5):

- `R-involution-arms-race` — scarce seats → more effort → higher baseline → effective scarcity persists (内卷)
- `R-credential-inflation` — 文凭インフレ
- `R-family-capture` — status anxiety → shadow-education spend → arms-race
- **`R-failure-despair`** — 受験失敗 → stigma → wellbeing erosion → lost opportunity → reinforced penalty *(the failure cycle; routed to relief)*
- `B-alternative-pathways` — de-stigmatized vocational / multiple attempts / decoupling jobs from one exam
- `B-wellbeing-protection` — 双減 / stakes-lowering / study-hour caps / mental-health support
- `R-degree-devaluation` — degree massification → graduate oversupply → 卒業即失業 → chase more credentials *(exam involution leaks into the labor market)*
- **`R-effort-futility`** — no absorbing job despite maximal effort → **頑張れない** (effort efficacy collapses) *(structural, §1.4 — not laziness)*
- **`R-lying-flat-spiral`** — collapsed efficacy → **躺平/寝そべり** withdrawal → less participation → further collapse *(symptom AND self-protective relief valve; never pathologized)*
- `B-labor-absorption` — job creation / youth-employment programs / decoupling careers from one credential

Two sober relief read-offs are foregrounded: the **受験失敗 cycle** and the **卒業後 (頑張れない
& 躺平) cycle** — both routed to RELIEF (kokoro 心 / shiori 栞 / manabi 学び), never amplified or
moralized.

## The discipline (gates)

- **G4 ANALYSIS-ONLY** — no outward channel (no post/mention/email/tx); enforced by *absence*.
- **G5** every loop/regime is a hypothesis, never proven causation.
- **G6** aggregate + institutional only — **no per-student record, no exam score of any person, no PII**.
- **G7** the failure cycle is stated **soberly** and **routed to relief** (kokoro 心 / shiori 栞), never despair-amplified.
- **G8** a relief/leverage **MAP** — never a student/school/country **shame-ranking**.
- **G11** Meadows leverage points are **candidates with uncertainty**, never directives.

`:shinogi/actuate`, `:shinogi/dispatch`, `:shinogi.exam.driver/person`,
`:shinogi.exam.student/score`, `:shinogi.exam.student/ranking`,
`:shinogi.exam.loop/proven-cause`, `:shinogi/prescription` are **structurally
unrepresentable** (negative space, test-enforced).

## Run

```bash
# the analysis-only read-off (markdown report + driver/stock/loop/failure-cycle datoms)
bb --classpath 20-actors 20-actors/shinogi/methods/analyze.cljc

# one autonomous heartbeat → append findings to the local content-addressed ledger
bb --classpath 20-actors 20-actors/shinogi/methods/autorun.cljc

# tests
bb 20-actors/shinogi/run_tests.clj      # 27 tests / 408 assertions green
```

## Files

- `kotoba/ontology.shinogi-exam.edn` — EAVT schema · 9 stocks (exam/labor/withdrawal) · 10 loops · Meadows 12 · negative space
- `kotoba/seed.exam-involution.edn` — 33 drivers / 6 jurisdictions (China-primary lifecycle: exam→labor→withdrawal; grows each /loop)
- `methods/shinogi_edn.cljc` — loader/classify
- `methods/analyze.cljc` — analysis-only read-off (stocks + loops + the two **failure / withdrawal cycles** + leverage + coverage + EAVT datoms + sober report). No outward channel (G4 by absence).
- `methods/kotoba.cljc` — content-addressed append-only findings ledger (commit-DAG, verify-chain, no-server-key, local file only)
- `methods/autorun.cljc` — deterministic idempotent-by-content heartbeat
- `run_tests.clj` — bb-native test runner

## Boundaries (who shinogi is NOT)

Not **ossekai** (which intervenes). Not a **test-prep / coaching** service (N2 — it never helps anyone
*win* the involution). Not a **forecaster** (N3) or **prescriber** (N4). Not a **student profiler** (N5).
Not a **clinical/crisis** service — the failure cycle is *routed* to kokoro/shiori (N6).

ADR: [`90-docs/adr/2606291200-shinogi-exam-competition-involution-system-dynamics-observatory.md`](../../90-docs/adr/2606291200-shinogi-exam-competition-involution-system-dynamics-observatory.md).
Parent method: junkan 循環 (ADR-2605290927). Charter: ADR-2605192100 §1.13 Wellbecoming / §1.15 non-eschatological.
