# hagukumi (育み) — Maturity Ledger

`/loop` の進捗台帳。各イテレーションで **1項目** だけ成熟度を上げ、ここに記録する。
honest framing (G8): できていないことは「未」と明記する。

- Actor: `did:web:etzhayyim.com:hagukumi` · ADR-2605261030 · **R0 scaffold**
- 不変条件(全イテレーション厳守): R0 では cell 非実行(import時 RuntimeError) ·
  PII平文禁止(G6) · 録画/監視なし(G2/N7) · 人間-in-loop(G9) · Murakumo-only(G7) ·
  **eligibility/benefit 判定なし + 非provider 境界** · G8 非捏造 · G14 verified-only ·
  コミットはユーザー明示時のみ

## イテレーション記録

### iter-1 (2026-06-02)
**care-support registry の fail-closed 監査固定 + 検証ワークフロー。** `registry/programs.seed.json`(172件 / 32管轄 / 全件 `unverified-seed`)に対し `70-tools/scripts/audit/test_hagukumi_registry_seed.py`(8 invariants: parse+非空 / programId一意 / 全件 unverified-seed(G14) / accessUrl+provenance+lastVerified 非空 http(s) / >=12管轄 / careKind taxonomy / 全 notes に「no eligibility/benefit determination」+「NOT a licensed care provider」境界 / freshnessWindowDays integer)を新規作成し green。`registry/VERIFICATION.md`(G14 三層 human/Council チェックリスト; eligibility・amounts はここで判定しない=authority で確認 を foreground; per-jurisdiction official-source provenance fail-closed; honest: **0 verified**)を新規作成。

### 2026-06-17 (loop) — manifest+lexicon charter-gate test (構造ゲート pin)
新設 `methods/test_charter_gates.cljc`(**6 tests green**)で manifest G1–G14 + 4 lexicon のケアゲートを固定: G3/G2 careSession が consentRecordCid + encryptedPayloadCid 必須(per-session consent + 録画なし暗号化)/ G4 caregiverAttestation が councilVettingAttestations + trainingCertCid 必須(Council vetting)/ consentRecord が careRecipientAgeBucket{under-14-guardian-consent, 14-17-co-consent, adult-self-consent, elder-self-consent-with-capacity-attestation} + validUntil 必須 / cellName={child_daily_care, elder_companionship, chronic_continuity, respite_support} / G14 silenCareReview に cohort-ratio audit scope。`run_tests.sh` 新設。working-tree edits only。

> **2026-06-17 substrate-native migration (ADR-2606160842):** the charter-gate test above was ported Python→Clojure (`methods/test_charter_gates.py` → `methods/test_charter_gates.cljc`, ns `hagukumi.methods.test-charter-gates`, reads the lexicons via cheshire/edn) and the Python was pruned. Run via `./run_tests.sh` (now `exec bb`) or `bb run test:charter` (all 34 charter suites; 244 tests / 924 assertions green). Assertions unchanged (1:1 port).

### 2026-07-10 (loop) — registry spot-check: 10/172 entries checked against live public sources (1 dead link found + fixed, no status flip)

**Honest framing (G8): this is NOT a formal verification pass.** Per `registry/VERIFICATION.md`, flipping any entry to `maintainer-verified` requires the R1 gate (Council ratification + a registered care-program-verification maintainer DID) — **not yet met**. All 172 entries remain `verificationStatus: unverified-seed`, including the one fixed below. What this iteration *did* do: fetched the `accessUrl` (+ secondary `provenance` links) of 10 entries spanning 8 jurisdictions and compared live page content against each entry's `title`/`summary`/`authority`.

Checked: `jpn-jido-teate-child-allowance`, `usa-child-tax-credit`, `gbr-child-benefit`, `deu-kindergeld-child-benefit`, `kor-adong-sudang-child-allowance`, `aus-family-tax-benefit-child-allowance`, `zaf-child-support-grant-csg`, `can-canada-child-benefit-ccb`, `ken-ct-ovc-orphans-vulnerable-children`, `fra-paje-prestation-accueil-jeune-enfant`.

Results:
- **6 live + content-matches the entry** (no change needed): `jpn-jido-teate-child-allowance` (cfa.go.jp), `usa-child-tax-credit` (irs.gov), `gbr-child-benefit` (gov.uk), `ken-ct-ovc-orphans-vulnerable-children` (socialprotection.go.ke — mentions Inua Jamii), `kor-adong-sudang-child-allowance` (bokjiro.go.kr portal, HTTP 200), `fra-paje-prestation-accueil-jeune-enfant` (caf.fr, HTTP 200).
- **1 confirmed dead link, fixed**: `deu-kindergeld-child-benefit`'s `accessUrl`/leading `provenance` (`arbeitsagentur.de/familie-und-kinder/kindergeld-verstehen`) returned HTTP 404 (confirmed via both an AI page-fetch and a direct `curl` with a browser UA). Replaced with the current live path `arbeitsagentur.de/familie-und-kinder/infos-rund-um-kindergeld` (HTTP 200, content confirmed to describe Kindergeld/Familienkasse). The two secondary `provenance` URLs (familienportal.de, handbookgermany.de) were already live and untouched. `verificationStatus` stays `unverified-seed` — this was a link-liveness/content-sanity fix, not the full 10-point maintainer checklist.
- **3 inconclusive (not confirmed live or dead — flagged for a human/browser recheck)**: `aus-family-tax-benefit-child-allowance` (servicesaustralia.gov.au — valid TLS cert matching the domain, but HTTP/2 stream reset on both the AI fetch and `curl`, consistent with anti-bot/WAF blocking of automated clients, not necessarily a dead page) · `can-canada-child-benefit-ccb` (canada.ca — same pattern: valid cert, WebFetch got HTTP 403, `curl` got an HTTP/2 stream reset) · `zaf-child-support-grant-csg` (sassa.gov.za — connection timed out repeatedly on this specific host, while `gov.za` root resolved fine at HTTP 200, so inconclusive rather than confirmed down).

**Next-iteration candidates**: (1) manually re-check the 3 inconclusive links from a real browser session (not an automated fetcher) and update `accessUrl`/`provenance` if actually stale; (2) continue the spot-check pass through more of the remaining 162 unchecked entries, a handful at a time; (3) do not attempt to flip any entry to `maintainer-verified` until the R1 gate (Council ratification + registered maintainer DID) actually lands — that is a governance precondition, not a link-checking one.
