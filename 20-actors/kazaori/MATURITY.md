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
