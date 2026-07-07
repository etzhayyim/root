# kotoba-rad — actor sovereign-identity journals

per-actor append-only identity journal (`<actor>.identity.journal.edn`)。
tooling: `70-tools/src/etzhayyim/kotoba_rad.cljc`（pure）+
`kotoba_rad_sign.clj`（no-server-key: 署名は Keychain/1Password の member 鍵
でのみ、platform は署名しない）。ADR-2606231200。

## 正規手順（署名付き発行 — minidrama で実証済み 2026-07-07）

```bash
# 1) actor member 鍵 (Keychain service etzhayyim.kotoba-rad / account <actor>)
bb actor:keygen <actor> --apply

# 2) 署名付き genesis journal
bb -e "(require '[etzhayyim.kotoba-rad :as rad] '[etzhayyim.kotoba-rad-sign :as sign])
       (rad/publish-identity! \"<actor>\"
         (rad/genesis-block {:name \"<actor>\"
                             :did-web \"did:web:etzhayyim.com:actor:<actor>\"  ; 現行スキーム (ADR-2606231200 addendum 2026-07-02)
                             :repo \"github.com/etzhayyim/com-etzhayyim-<actor>\"
                             :threshold 1
                             :pds \"https://pds.aozora.app\"
                             :collection \"com.etzhayyim.apps.<actor>\"})
         {:sign-fn (sign/sign-fn-for-actor \"<actor>\")})"

# 既存 journal の did:web を現行スキームへ移行する場合 (RID 温存、tashikame/minidrama 前例):
#   (rad/update-did-web! "<actor>" "did:web:etzhayyim.com:actor:<actor>"
#                        {:sign-fn (sign/sign-fn-for-actor "<actor>")})
```

- `did:web:etzhayyim.com:actor:<name>` は 50-infra/etzhayyim-did-web worker が
  **free-form で解決**する（journal/registry 登録不要で 200）。registry 列挙
  （INFRA_ACTORS/tier-b）に載せるには `20-actors/<name>/manifest.{jsonld,edn}`
  が別途必要。
- `publish-identity!` は **RID 冪等**: 既存 journal に同じ genesis があれば
  datom は増えず fresh sigref だけ追記（= 未署名 journal の署名化に使える）。

## 棚卸し (2026-07-07 実測)

- journal 総数: **321**
- **署名付き (:rad/sig あり): minidrama, yomi の 2 件のみ。** 残り ~319 件は
  歴史的に sign-fn 無しで発行された未署名 journal（`:rad/by` はあるが
  `:rad/sig` が無い — tashikame 含む）。
- **journal 自体が無い actor（ADR 上 deferred と記録）**: sng, kyoninka,
  com-google-ads, tomoshibi — いずれも上記の正規手順（keygen →
  publish-identity!）でそのまま解消可能。deferred の根拠だった「signing
  tooling 待ち」は 2026-07-07 時点で解消済み（tooling 実在・minidrama で実証）。
- 未署名 journal の署名化: 各 actor の member 鍵を `actor:keygen --apply` で
  発行 → `publish-identity!` を再実行（冪等、fresh signed sigref が付く）。
  鍵の発行主体は member/operator の判断（no-server-key — 一括自動発行はしない）。
