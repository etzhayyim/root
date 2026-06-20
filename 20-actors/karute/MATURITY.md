# karute (カルテ) — Maturity Ledger

`/loop` 進捗台帳。各イテレーションで **1項目** だけ成熟度を上げ、ここに記録する。
honest framing: できていないことは「未」と明記する。

- Actor: `did:web:karute.etzhayyim.com` · ADR-2605231100 (EMR Phase 1) · DID-worker LIVE
- **二層構造**: (1) この `20-actors/karute/` = kotoba-native **charter surface** — 11 FHIR
  Lexicons + 憲法ゲートテスト; (2) EMR の実装 (Svelte SuperApp + lg-karute pod + did-worker) は
  `60-apps/etzhayyim-project-karute/` + `50-infra/karute-did-web/` 側(`actor.edn` の deploy stages)。
  この台帳は **(1) の charter surface** の成熟度のみを追う(実 EMR は別レイヤ)。
- 不変条件(厳守): 全 PHI は `com.etzhayyim.encrypted.record` envelope のみ(平文 PHI を MST に
  書かない) · consent = `com.etzhayyim.consent.capability`(Ed25519 member-signed, no-server-key
  ADR-2605231525) · 3軸 split clean(payoff/custody/settlement = etzhayyim) · 患者識別子 =
  DID(`patientDid`)、平文氏名/MRN を連結キーにしない。

## 成熟度チェックリスト

| # | 項目 | 状態 | 完了イテレーション |
|---|---|---|---|
| 1 | ADR-2605231100 (EMR Phase 1) | ✅ | init |
| 2 | actor-manifest.jsonld + actor.edn(deploy pipeline)+ CLAUDE.md + NOTICE | ✅ | init |
| 3 | 11 FHIR Lexicons (`com.etzhayyim.karute.*` — patient/encounter/condition/observation/medicationRequest/serviceRequest/carePlan/dispenseRecord/soapNote/homecareEpisode/homeVisit) | ✅ | init |
| 4 | did:web:karute.etzhayyim.com worker LIVE(`50-infra/karute-did-web`) | ✅ | init |
| 5 | **charter-gate テスト** (`methods/test_charter_gates.cljc` — 4 tests / 35 assertions) | ✅ | **iter (this)** |
| 6 | run_tests.sh が charter-gate suite を実行(actor reflex に wired) | ✅ | **iter (this)** |
| 7 | encrypted-envelope 規律をスキーマ層で機械強制(`additionalProperties:false` + 平文 PHI フィールド拒否、R1) | 未 | — |
| 8 | consent.capability の Ed25519 検証テスト(member-signed / server-refused) | 未 | — |
| 9 | 患者 DID = 30日 rotating pseudonym(ADR-2605181200)の構造検証 | 未 | — |
| 10 | kotoba EAVT への FHIR inner-type 投影(public graph = meta only)の検証 | 未 | — |
| 11 | iryo(レセプト)への hand-off boundary テスト(karute → iryo consent-capability) | 未 | — |

## イテレーション記録

### iter (this) — 2026-06-18
**上げた項目: #5 + #6 — charter surface のテスト被覆をゼロから確立。**
`methods/test_charter_gates.cljc` を新規作成(4 deftests / 35 assertions、green)。central FHIR
lexicons を cheshire で読み、charter が依存する**構造的不変条件**を pin した(誤った no-plaintext-PHI
主張はしない — これらは encrypted-envelope の inner-type であり、PHI 機密は envelope 層で強制される):
- **interop** — 全 11 resource が `fhirResourceType` const を pin(Patient/Encounter/Condition/
  Observation/MedicationRequest/ServiceRequest/CarePlan/MedicationDispense/Composition/EpisodeOfCare)。
- **DID-centric identity** — 全 clinical resource(10/11)が `patientDid` を required;患者は DID
  束縛で、平文氏名/MRN を連結キーにしない(subject-DID custody, ADR-2605172400)。
- **accountability** — `soapNote.authorDid` required;prescriber/performer/pharmacist/requester/
  recordedBy は DID フィールド(無名/自由記述の著者は表現不能)。
- **closed clinical vocabularies** — encounter/observation/medicationRequest の status・class・
  category・intent は閉じた FHIR value set。
`bb.edn test:charter` に `karute.methods.test-charter-gates` を登録。`run_tests.sh` が charter
suite を実行するよう確認(actor reflex に wired)。ゲートは一切弱めず、assert のみ。
