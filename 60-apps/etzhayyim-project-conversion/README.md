# etzhayyim-project-conversion

Society6 加入のための改宗・宣誓・KYC・ブロックチェーン公開記録を統合する App。

- Public URL: `https://conversion.etzhayyim.com`
- Runtime: App (kotodama runtime)
- Data: LanceDB (performer/lancedbrest)

## Workflow

1. **宣誓 (Oath)**: 加入希望者が Society6 の理念・原則への宣誓を提出
2. **KYC 検証**: eKYC プロジェクト経由で本人確認を実施
3. **ブロックチェーン記録**: 宣誓内容と検証結果をブロックチェーンに記録・公開
4. **メンバーシップ発行**: 全ステップ完了後に Society6 membership を付与

## Component

- `wasm/etzhayyim-wasm-conversion-cv8m3k2p/` — 改宗・宣誓・KYC・blockchain attestation App
