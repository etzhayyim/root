# etzhayyim-project-saiban

裁判 intelligence platform (`saiban.etzhayyim.com`).

## App Identity

| Key | Value |
|---|---|
| **AT bot DID** | `did:web:saiban.etzhayyim.com` |
| **nanoid** | `sb4n0j1c` |
| **Runtime** | **TS Native** (`src/app.ts` + `@etzhayyim/kotodama-host-sdk`) |
| **Data store** | W Protocol Event Stream |
| **UI mode** | `appview` (yoro) |

## Court-Level DID Coverage (5 jurisdictions, 33 courts)

| Jurisdiction | Count | Court DIDs |
|---|---|---|
| **Japan** | 8 | summary, district, family, high, supreme, administrative, arbitration, mediation |
| **USA** | 5 | scotus, circuit, district, bankruptcy, tax |
| **UK** | 6 | uksc, appeal, high, crown, magistrates, tribunal |
| **Germany** | 8 | bverfg, bgh, bverwg, bag, bsg, bfh, lg, ag |
| **France** | 6 | cc, cass, ce, ca, tgi, ta |

### DID Pattern

```
did:web:saiban.etzhayyim.com:court:{level}           # JP generic
did:web:saiban.etzhayyim.com:court:{iso3}:{court-id}  # Global (US/UK/DE/FR)
```

## Writer DIDs (12 categories)

| Entity | DID Pattern | Description |
|---|---|---|
| **裁判官 (Judge)** | `judge:register` | Judge profile registry (restricted, privacy) |
| **民事事件** | `jiken:civil` | Civil cases |
| **刑事事件** | `jiken:criminal` | Criminal cases |
| **行政事件** | `jiken:administrative` | Administrative cases |
| **家事事件** | `jiken:family` | Family cases |
| **破産事件** | `jiken:bankruptcy` | Bankruptcy cases |
| **労働事件** | `jiken:labor` | Labor cases |
| **商事事件** | `jiken:corporate` | Corporate/commercial cases |
| **知的財産事件** | `jiken:ip` | IP cases |
| **入管事件** | `jiken:immigration` | Immigration cases |
| **租税事件** | `jiken:tax` | Tax cases |
| **不動産事件** | `jiken:real-estate` | Real estate cases |

## Connected Actors

| Actor | Relation | Description |
|---|---|---|
| `hanrei.etzhayyim.com` | jiken → 判例 citation | 事件 DID から判例・判決 DID への citation graph |
| `lawfirm.etzhayyim.com` | jiken ← case-management | lawfirm の legal-case が saiban の jiken を参照 |
| `legal-entity.etzhayyim.com` | court → 法人登記 | 裁判所の法人情報 |
| `natural-person.etzhayyim.com` | judge → 人物 | 裁判官の人物情報 (restricted) |
| `bankruptcy.etzhayyim.com` | jiken:bankruptcy → 破産手続 | 破産事件の手続種別連携 |

## Graph Labels

| Collection | SQL Label |
|---|---|
| `com.etzhayyim.apps.saiban.court` | `Court` |
| `com.etzhayyim.apps.saiban.judge` | `Judge` |
| `com.etzhayyim.apps.saiban.jiken` | `Jiken` |
| `com.etzhayyim.apps.saiban.trialEvent` | `TrialEvent` |
| `com.etzhayyim.apps.saiban.jurisdictionMap` | `JurisdictionMap` |

## Build & Deploy

```bash
cd 60-apps/etzhayyim-project-saiban/wasm/etzhayyim-wasm-saiban-sb4n0j1c
etzhayyim deploy
```
