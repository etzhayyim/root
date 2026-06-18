# kazaori (風折) — Maturity Ledger

`/loop` の進捗台帳。各イテレーションで **1項目** だけ成熟度を上げ、ここに記録する。
honest framing (G8): できていないことは「未」と明記する。

- Actor: `did:web:kazaori.etzhayyim.com` · ADR-2605263200 · **R0 scaffold**
- 不変条件(全イテレーション厳守): R0 では cell 非実行(import時 RuntimeError) ·
  emergency declaration/dispatch なし · **CIVILIAN-ONLY**(G5+N1、武力行動と協調しない、
  force authorization は ADR-2605192315 で分離) · **OBSERVATIONAL directory**(自前の
  alert 発信なし・response 指揮なし・公式 emergency service ではない) · no surveillance(G6) ·
  時限カーブアウトは declared emergency 中のみ(G8) · Council Lv6+ ≥4/7 declaration(G10) ·
  Murakumo-only inference · コミットはユーザー明示時のみ

## イテレーション記録

- 2026-06-02 registry hardening: `registry/agencies.seed.json`(worldwide 民間災害対策機関ディレクトリ)に fail-closed invariants test `70-tools/scripts/audit/test_kazaori_registry_seed.py`(8 test、緑)を新設 — JSON parse + `agencies` 非空 / `agencyId` 一意 / 全件 `verificationStatus="unverified-seed"`(G14)/ 全件 非空 http(s) `accessUrl`+`provenance`+ISO-8601 `lastVerified` / ≥12 distinct jurisdictions / `agencyKind` が許可タクソノミ {disaster-management-agency, early-warning-system, official-alert-channel, civilian-relief-coordination, intl-disaster-body} 内 / `notes` 非空かつ CIVILIAN-ONLY+OBSERVATIONAL 境界を再宣言 / top-level 整数 `freshnessWindowDays`。併せて `registry/VERIFICATION.md`(G14 三層 + 10項目人手チェックリスト、civilian-only/observational 再確認、provenance 公式性 fail-closed、honest: 0 verified)を新設。test-only・network-free・cell 非実行で R0 ceiling 不変。

### 2026-06-17 (loop) — manifest+lexicon charter-gate test (構造ゲート pin)
既存 registry-seed テストが被覆していなかった **manifest G1–G12 + 6 lexicon の災害対応ゲート**を新設 `methods/test_charter_gates.cljc`(**7 tests green**, standalone・network-free)で固定: (1) manifest 厳密に G1–G12。(2) **G10/G5** emergencyDeclaration const `civilianOnlyAttested=true` + councilAttestations + autoLiftAtUtc + initialDurationDays(Council宣言・自動解除)。(3) **G6/G4** silenKazaoriReview const surveillancePenetrationPct=0 + commercialDisasterMgmtSoftwarePenetrationPct=0 + civilianOnlyCompliance=true + reviewCompletedWithin90DaysOfLifting=true。(4) **G9 Sphere** review が sphereCompliance + water/food/health/shelter/protection attested。(5) **G8** emergencyCarveOutLog が autoRevokeAtUtc + councilAttestations + carveOutJustificationCid + gateCarved(時限carve-out)。(6) supply dispatch が carve-out gated。(7) **G6** evacuationCheckIn が encryptedPayloadCid + memberSignature。`run_tests.sh` 新設。working-tree edits only。

> **2026-06-17 substrate-native migration (ADR-2606160842):** the charter-gate test above was ported Python→Clojure (`methods/test_charter_gates.py` → `methods/test_charter_gates.cljc`, ns `kazaori.methods.test-charter-gates`, reads the lexicons via cheshire/edn) and the Python was pruned. Run via `./run_tests.sh` (now `exec bb`) or `bb run test:charter` (all 34 charter suites; 244 tests / 924 assertions green). Assertions unchanged (1:1 port).
