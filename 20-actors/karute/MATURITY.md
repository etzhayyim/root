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
| 11 | iryo(レセプト)への hand-off boundary テスト(karute → iryo consent-capability) | 🟡 部分(受理境界のみ) | **iter 2026-07-08** |

## イテレーション記録

### iter 2026-07-08
**上げた項目: #11 — iryo 側の受理境界(intake boundary)を実装 + テスト。honest framing: 部分達成。**
karute の `requestIryoBilling` は `agent.invoke` で iryo の `ingestKaruteEncounterForBilling`
を呼ぶが(`actor-manifest.jsonld` forwardToIryo step)、**iryo 側には受け皿が全く無かった**
(このイテレーション以前は 20-actors/iryo に該当ハンドラ0件)。`orgs/etzhayyim/root/20-actors/
iryo/methods/handoff.cljc` (+ `methods/test_handoff.cljc`, 16 tests / 37 assertions, green)
がその受理境界を実装した:
- **PHI-free intake gate (iryo G2)** — karute が転送する wire フィールド
  (patientDid/encounterDid/facilityDid/serviceRequestUris/medicationRequestUris/
  consentCapabilityUri) を allow-list 検証。DID/AT-URI prefix チェック + 全 string leaf の
  ASCII-only チェック(smuggled PHI を fail-closed で拒否)。
- **consent.capability 構造ゲート (iryo G1/G7)** — 解決済み capability record に対し
  purpose=insurance-billing / granteeDid=iryo自身 / granterDid=patientDid一致 / 未失効 /
  未期限切れ / scope・resourceUris 充足 を検証。
- **結果語彙の規律 (iryo G3/G5)** — 受理成功は `iryoStatus:"pending"` のみ(draft キュー投入、
  オンライン送信はしない);ゲート不合格は `iryoStatus:"needs-info"` のみを返す —
  `"accepted"`/`"rejected"` は審査支払機関の査定語彙であり iryo は使わない(non-adjudicating
  discipline を hand-off 境界にも一貫させた)。
- **honest framing — 未達のまま残るもの**: (a) capability の **Ed25519 署名検証**は行わない
  (karute 側の項目 #8 がそもそも未、こちらも同じく未 — このイテレーションが検証するのは
  構造/ビジネスロジックのゲートであって暗号署名ではない);(b) `consentCapabilityUri` /
  各 AT-URI の **実際の PDS 解決**は行わない(`@etzhayyim/sdk` 依存、cross-repo、karute
  アプリ側の責務);(c) 受理後の実レセプト計算(`iryo.methods.agent/handle-rezept`)への
  自動接続は無い(実データはまだ流れない、intake の受理/拒否境界のみ)。したがって
  「karute → iryo consent-capability」の hand-off boundary は **受理境界のみ完了**であり、
  end-to-end(署名検証 + PDS 解決 + 実際のレセプト計算までの自動フロー)は依然未。
- テスト: `20-actors/iryo/run_tests.sh` に `iryo.methods.test-handoff` を追加registered(12
  suites, 全 green)。`20-actors/iryo/methods/test_e2e.cljc` に agent.cljc 経由の配線確認
  テストを1本追加(`test-handle-ingest-billing-is-wired-through-agent`)。karute 側の
  `run_tests.sh`(charter-gate suite, 4 tests / 35 assertions)は無変更のまま green を確認。

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
