# manabi (学び) — Maturity Ledger

`/loop` の進捗台帳。各イテレーションで **1項目** だけ成熟度を上げ、ここに記録する。
honest framing (G8): できていないことは「未」と明記する。

- Actor: `did:web:etzhayyim.com:manabi` · ADR-2605261045 · **R0 scaffold**
- 不変条件(全イテレーション厳守): R0 では cell 非実行(import時 RuntimeError) ·
  ANTI-CREDENTIALISM(degrees/transcripts/GPA 発行禁止, skillAttestation のみ — G7 + §2(e)) ·
  anti-addiction UX(streaks/leaderboards/badges 禁止 — G3 + §2(d)) · minor privacy
  aggregate-only(G6) · comparative-religion(G14) · Murakumo-only · G8 非捏造 ·
  open-education resource は ROUTE のみ(accredit/grade/rank しない) · コミットはユーザー明示時のみ

## イテレーション記録

### 2026-06-02 — open-education resource registry hardening
**`registry/resources.seed.json` の fail-closed 機械床 + G14 検証ワークフローを追加。**
新規 `70-tools/scripts/audit/test_manabi_registry_seed.py`(8 invariants: parse +
unique resourceId + 全件 unverified-seed(G14) + accessUrl/https-provenance/lastVerified +
12+ jurisdictions + 許可 resourceKind 語彙 + notes の anti-credentialism/open-resource
境界 + top-level integer freshnessWindowDays)を作成、green(8 passed)。
`registry/VERIFICATION.md`(G14 三層チェックリスト: per-field license + free-access 検証 +
worldwide per-jurisdiction official/recognized-source provenance fail-closed +
ANTI-CREDENTIALISM 境界 re-check; 機械床として test を引用)を追加。honest: **0 verified**。
