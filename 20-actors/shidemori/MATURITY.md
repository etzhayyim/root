# shidemori (死出守) — Maturity Ledger

`/loop` 進捗台帳。各イテレーションで成熟度を上げ、ここに記録する。honest framing:
できていないことは「未」と明記する。

- Actor: `did:web:shidemori.etzhayyim.com` · ADR-2605263800 · **R0 scaffold**
- 不変条件(全イテレーション厳守): R0 では cell 非実行 · dispatch なし ·
  NON-mortuary / non-commercial / non-legal-advice 境界(G14, ADR-2605263800) ·
  PII平文禁止 · Murakumo-only · G8 非捏造 · コミットはユーザー明示時のみ

## イテレーション記録

- 2026-06-02 registry hardening: WROTE fail-closed seed invariants test `70-tools/scripts/audit/test_shidemori_registry_seed.py` (8 tests, `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest … -q` → green) pinning the death-registration seed (`registry/registries.seed.json`, 130 entries / 31 jurisdictions): JSON parse + non-empty `registries`, unique `registryId`, all `unverified-seed` (G14), non-empty `accessUrl`+`provenance`+`lastVerified`, ≥12 distinct jurisdictions, `recordKind` ∈ {death-registration-authority, death-certificate-issuer, burial-cremation-permit, civil-registry-office, intl-guidance}, every `notes` non-empty + references the NON-mortuary/non-commercial boundary, top-level integer `freshnessWindowDays`. WROTE `registry/VERIFICATION.md` — G14 three-tier human checklist foregrounding re-verification of the statutory registration DEADLINE against the cited law (a wrong deadline is harmful), per-jurisdiction official-source provenance (fail-closed), non-mortuary/non-commercial boundary re-check; honest (G8): 0 entries verified. Provenance check requires http(s) (not https-only) because two genuine official sources (koreanlii.or.kr, home-affairs.gov.za) are http — real data not masked.
