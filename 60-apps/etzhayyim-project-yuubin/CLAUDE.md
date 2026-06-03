# etzhayyim-project-yuubin — 日本郵便 Web ゆうびん 自動化 actor

**URL**: `https://yuubin.etzhayyim.com` / `https://y00b1nx9.etzhayyim.com`
**DID**: `did:web:yuubin.etzhayyim.com`
**nanoid**: `y00b1nx9`

## Purpose

裁判所申立書・差押命令申立書・第三者情報取得手続申立書・内容証明郵便など、司法・行政文書の自前郵送を Web ゆうびん 自動化で完結させる。`fax.etzhayyim.com` (新件申立書 FAX 不可) と `mailer.etzhayyim.com` (電子メール) の中間レイヤを埋める。

## ⚠ CRITICAL: Web ゆうびん 自動投函は F5 ASM + iframe CDP 非互換で断念 (2026-04-20)

**技術的判定**: Web ゆうびん の edge は以下 2 防御機構で puppeteer-based 自動化を阻止する:

1. **F5 BIG-IP ASM bot detection** — CF Browser Rendering (puppeteer-cloudflare) の headless Chrome fingerprint を検出。TS cookie (`TS0157ba2f`/`TS01f3b24f`/`TS0176c857`) の prefix が puppeteer 経由だと全て `01676585ca...` に固定化され、login POST が silently reject される (HTTP 200 with top-page HTML、redirect なし、credentials は valid でも通らない)。
2. **iframe + 同期 XHR + CDP 非互換** — file upload が ThickBox iframe で行われ、その中の `saveAndSubmit('DYFR920.upload')` 同期 XHR が実行中 CDP `Runtime.evaluate` が 45s+ timeout する。**`Claude-in-Chrome` (real Chrome) でも同様に freeze する** ため、CF Browser Rendering 固有ではなく CDP + iframe 固有のバグ。

**実機検証内容**:
- login 自動化: ✅ 動作 (DO alarm + page.type + UA spoof で突破)
- iframe 開封: ✅ 動作 (`TB_iframeContent.contentFrame()` でアクセス可)
- DataTransfer File 注入: ✅ 動作 (CORS blob fetch + `input.files = dt.files`)
- `exeAction()` 呼出 → server 処理: ⚠ F5 ASM で 200 + top page (login reject)
- real Chrome iframe upload: ⚠ tab freeze (CDP timeout)

**結論**: Web ゆうびん 自動投函を bypass するには以下のいずれかが必要:
- Commercial anti-bot service (ScrapingBee / ZenRows, 月額 $49-199)
- 専用 VM + residential proxy + stealth Playwright (月額 $20 + 保守)
- Japan Post 法人 B2B API 契約 (要問合せ)

**現状の yuubin actor の有効活用範囲**:
- `normalizeDocx` / `validatePdf` XRPC — **preprocessing として他 actor でも使える** (A4 検証、pandoc 既定 US Letter → A4 変換)
- F5 ASM で保護されていない他の投函サービス (海外郵便 API, 民間配送業者 API)
- OCR + 書類索引 (evidence packaging)

**commons-ag-litigation 具体ルート**: Phase 0.5 / 1 / 2 の投函は全て **レターパックプラス 600円 + 河崎宅手動投函** で完結 (2-3 ヶ月で 35,772,961円 + 遅延損害金 回収見込)。

## Topology

```
Caller (kaisya/lawfirm/agent)
  ↓ XRPC /xrpc/com.etzhayyim.apps.yuubin.composeAndPost
yuubin actor
  ├─ uploadDocument → CDN R2 (SHA-256 keyed, dedup)
  ├─ Tier 1 composeAndPost
  │    ├─ provider="auto" → CF Browser Rendering puppeteer →
  │    │    Web ゆうびん login → menu select → file upload → 宛先入力 → 決済 → 申込番号
  │    └─ fallback → manual-handoff (mailer.etzhayyim.com → Teams/email)
  ├─ Tier 1 submitNaiyoShomei → e内容証明 (現状 manual-handoff)
  └─ confirmManualPost (operator が完了報告)
```

## XRPC Endpoints

| NSID | Tier | 用途 |
|---|---|---|
| `com.etzhayyim.apps.yuubin.composeAndPost` | 1 | 通常便/レターパック自動投函 |
| `com.etzhayyim.apps.yuubin.submitNaiyoShomei` | 1 | 電子内容証明 |
| `com.etzhayyim.apps.yuubin.confirmManualPost` | 1 | manual handoff 完了記録 |
| `com.etzhayyim.apps.yuubin.uploadDocument` | 2 | PDF base64 → B2 content-addressed |

## Bindings (wrangler.jsonc)

| Type | Name | Source |
|---|---|---|
| browser | `HEADLESS_BROWSER` | CF Browser Rendering (puppeteer) |
| b2 (S3 SigV4, ADR-0048) | `B2_KEY_ID` / `B2_APPLICATION_KEY` | bucket `etzhayyim-yuubin` (rendered PDF + screenshot, content-addressed) |
| hyperdrive | `HYPERDRIVE` | RisingWave shared |
| service | `PDS_SERVICE` / `PDS_RPC` | etzhayyim-pds-2603241700 |
| secret | `SS_WEBYUBIN_USERNAME` | etzhayyim.webyubin keychain |
| secret | `SS_WEBYUBIN_PASSWORD` | etzhayyim.webyubin keychain |
| secret | `SS_WEBYUBIN_PAYMENT_CARD_LAST4` | 決済確認用末尾 4 桁 |

## Bootstrap Steps (deploy 前に必要)

### 1. Web ゆうびん 法人アカウント開設

- Web フォーム: <https://webyubin.jpi.post.japanpost.jp/> から法人登録
- 必要書類: 法人番号 + 代表者氏名 + 連絡先 + 本人確認 + 請求先情報
- 決済方法: クレジットカード (法人カード推奨) or 月締請求
- Tier: 法人 my page で決済方法・差出人住所をプリセット保存

### 2. 認証情報を Keychain に保存

```bash
security add-generic-password -s "etzhayyim.webyubin" -a "USERNAME" -w "<法人ID>" -U
security add-generic-password -s "etzhayyim.webyubin" -a "PASSWORD" -w "<password>" -U
security add-generic-password -s "etzhayyim.webyubin" -a "PAYMENT_CARD_LAST4" -w "<末尾4桁>" -U
```

### 3. Cloudflare Secrets Store に同期

```bash
USERNAME=$(security find-generic-password -s etzhayyim.webyubin -a USERNAME -w)
PASSWORD=$(security find-generic-password -s etzhayyim.webyubin -a PASSWORD -w)
echo "$USERNAME" | wrangler secret put webyubin_username --secret-store 1824561668fe47cc9127d493961885af
echo "$PASSWORD" | wrangler secret put webyubin_password --secret-store 1824561668fe47cc9127d493961885af
```

### 4. Browser Rendering を Cloudflare Account で有効化

```bash
# Cloudflare Dashboard → Workers & Pages → Browser Rendering → Enable
# (有料プラン必須、Worker Paid: $5/月で含まれる)
```

### 5. Deploy

```bash
cd 60-apps/etzhayyim-project-yuubin/etzhayyim-wasm-yuubin-y00b1nx9
pnpm install
etzhayyim deploy
```

### 6. Selector Live Validation

Web ゆうびん の DOM 構造は予告なく変わるため、初回 deploy 前に Claude in Chrome 経由で
実際の login → menu → upload → form フローを録画して `selectors.json` 化する作業が必要。
現在の `src/app.ts` の selector 群は **typical pattern の placeholder**。本番投入前に必ず再検証。

## Operational Modes

| provider | 動作 | 失敗時 |
|---|---|---|
| `auto` (DEFAULT) | puppeteer 自動投函 | 失敗時 manual-handoff にフォールバック |
| `puppeteer` | 強制 puppeteer (失敗即 fail) | エラー返却 |
| `manual` | Teams/email handoff のみ (puppeteer skip) | operator が手動投函 → confirmManualPost |

## Cross-Actor Integration

- **Caller**: `kaisya.etzhayyim.com` (case 起点) / `lawfirm.etzhayyim.com` (matter 起点) / Claude agent (MCP)
- **Notifier**: `mailer.etzhayyim.com` (manual-handoff 通知)
- **Audit**: `vertex_collection_procedure` (RW) に `procedure_kind: postalSubmission` で記録予定 (kaisya 連携)

## Cost Estimate (per 投函)

| 配送方法 | 料金 (税込) | 追跡 | 備考 |
|---|---|---|---|
| Web ゆうびん 通常便 | 84 円〜 (重量別) | × | 一般信書扱い |
| レターパックライト | 430 円 | ✓ | 投函のみ、4cm まで |
| レターパックプラス | 600 円 | ✓ | 対面渡し、厚さ制限なし |
| 電子内容証明 (e内容証明) | 1,540 円 + α (謄本料・配達証明) | ✓ | 法的証拠力 |
| 速達 | +260 円 | ✓ | 追加オプション |

## Document Preprocessing (Web ゆうびん 制約対応)

Web ゆうびん は以下を厳格にチェックして拒否するため、submit 前に preprocess を噛ませる。

| チェック | 拒否メッセージ | 対応 |
|---|---|---|
| PDF フォント埋込 + 仕様 | 「PDFの作成方法を変更してください」 | `scripts/render-a4-pdf.sh` で `pandoc --pdf-engine=xelatex -V papersize=a4 -V CJKmainfont=...` (Mac-local, 要 BasicTeX + collection-langjapanese)。Chrome headless `--print-to-pdf` の PDF は拒否される |
| .docx A4 | 「ファイルのページサイズがA4(210x297,297x210)ではなかった」 | `scripts/normalize-a4-docx.sh` (Mac-local) or `com.etzhayyim.apps.yuubin.normalizeDocx` XRPC (CF Worker runtime) |
| .docx ≤ 1MB | "ファイルサイズは１回のアップロードあたり１ＭＢまで" | caller 側で分割 |
| 1 page ≤ A4 横 or 縦のみ | (上記に含まれる) | normalize-a4-docx が対応 |

### Local preprocessing

```bash
# Bootstrap (one-time)
brew install pandoc
brew install --cask basictex
eval "$(/usr/libexec/path_helper)"
sudo tlmgr update --self
sudo tlmgr install collection-langjapanese haranoaji

# Render markdown → A4 PDF (embedded CJK fonts)
scripts/render-a4-pdf.sh input.md output.pdf

# Normalize .docx to A4 (pandoc 既定の US Letter → A4)
scripts/normalize-a4-docx.sh input.docx output-a4.docx
```

### Worker-side preprocessing (XRPC)

```
POST https://yuubin.etzhayyim.com/xrpc/com.etzhayyim.apps.yuubin.normalizeDocx
{ "blobKey": "<sha256 hex of docx in CDN_R2>" }
→ { "normalizedBlobKey": "<new sha256>", "normalizedPublicUrl": "..." }

POST https://yuubin.etzhayyim.com/xrpc/com.etzhayyim.apps.yuubin.validatePdf
{ "blobKey": "<sha256 hex of PDF in CDN_R2>" }
→ { "isA4": true/false, "pages": N, "sampleSize": [w, h], "warning": "..." }
```

Dependencies: `fflate` for zip manipulation (pure JS, CF Worker compatible).

## TODO

- [ ] ~~Web ゆうびん 法人アカウント開設~~ — **既存 GJ 法人アカウント発見済 (Bitwarden → keychain `etzhayyim.webyubin`)**
- [ ] Cloudflare Secrets Store に `webyubin_username` / `webyubin_password` 同期 (keychain → `wrangler secret put`)
- [ ] Browser Rendering 有効化 ($5/月 Workers Paid プラン確認)
- [ ] Selector live validation — **部分済** (login / DYFR410 Webレター flow / 登録情報変更 は検証済、e内容証明 は multi-tab detection でブロック)
- [ ] e内容証明 実行経路 — Japan Post e内容証明 は意図的に自動化対策 (multi-tab 検出) 実装。**ユーザー手動 + confirmManualPost** で audit 完結
- [ ] 送り状発行 API 連携 (法人契約後、レターパック PDF 自動生成)
- [ ] kaisya `vertex_collection_procedure` への自動連携 (postalSubmission kind)
- [ ] 投函済アイテム status polling cron (申込→印刷→発送→配達 状態追跡)

## Related

- `60-apps/etzhayyim-project-fax/` — FAX gateway (Dropbox Fax UI manual handoff)
- `60-apps/etzhayyim-project-mailer/` — Email gateway (Microsoft Graph)
- `60-apps/etzhayyim-project-kaisya/` — case management (commons-ag-litigation 等)
- ADR-0019 (atproto-native identifier topology)
- 民事執行法 207 条 (第三者からの情報取得手続申立、本 actor の主要送付対象)
