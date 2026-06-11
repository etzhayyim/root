# Kakaku Smoke Runbook

`kakaku.etzhayyim.com` の最小 smoke。merchant / product / offer / compare / history の順で確認する。

## Quick Run

```bash
bash 70-tools/scripts/kakaku-smoke.sh
```

`APP_ID` を変える場合:

```bash
APP_ID=k4k4kux1 bash 70-tools/scripts/kakaku-smoke.sh
```

## Step By Step

### 1. Merchant 登録

```bash
etzhayyim xrpc com.etzhayyim.apps.kakaku.registerMerchant \
  -d '{"merchantName":"Yodobashi","domain":"www.yodobashi.com","baseCurrency":"JPY","shippingPolicy":"standard","reputationScore":0.95}' \
  --app k4k4kux1
```

期待:
- `merchantId`
- `merchantDid`
- `status=ok`

### 2. Product 登録

```bash
etzhayyim xrpc com.etzhayyim.apps.kakaku.registerProduct \
  -d '{"name":"Nintendo Switch 2","brand":"Nintendo","model":"Switch 2","jan":"4902370553023","category":"game_console"}' \
  --app k4k4kux1
```

期待:
- `productId=jan_4902370553023`
- `productDid=did:web:kakaku.etzhayyim.com:product:jan_4902370553023`

### 3. Offer upsert

```bash
etzhayyim xrpc com.etzhayyim.apps.kakaku.upsertOffer \
  -d '{"productId":"jan_4902370553023","name":"Nintendo Switch 2","brand":"Nintendo","model":"Switch 2","jan":"4902370553023","merchantName":"Yodobashi","domain":"www.yodobashi.com","merchantSku":"4902370553023","price":49980,"shippingFee":0,"currency":"JPY","availability":"in_stock","deliveryEta":"P2D","productUrl":"https://www.yodobashi.com/product/4902370553023/","observedAt":"2026-04-11T00:00:00Z"}' \
  --app k4k4kux1
```

期待:
- `offerId`
- `offerDid`
- `historyWritten=true`

同じ商品で別 merchant を追加:

```bash
etzhayyim xrpc com.etzhayyim.apps.kakaku.upsertOffer \
  -d '{"productId":"jan_4902370553023","name":"Nintendo Switch 2","brand":"Nintendo","model":"Switch 2","jan":"4902370553023","merchantName":"BicCamera","domain":"www.biccamera.com","merchantSku":"4902370553023","price":49780,"shippingFee":550,"currency":"JPY","availability":"in_stock","deliveryEta":"P1D","productUrl":"https://www.biccamera.com/product/4902370553023/","observedAt":"2026-04-11T00:05:00Z"}' \
  --app k4k4kux1
```

### 4. 比較

```bash
etzhayyim xrpc com.etzhayyim.apps.kakaku.compareOffers \
  -d '{"productId":"jan_4902370553023","limit":10}' \
  --app k4k4kux1
```

期待:
- `offers` が 2 件以上
- `cheapest`
- `bestOverall`
- `fastest`

### 4.5 URL ingest

merchant page から直接拾う場合:

```bash
etzhayyim xrpc com.etzhayyim.apps.kakaku.ingestOfferFromUrl \
  -d '{"productUrl":"https://www.yodobashi.com/product/4902370553023/","merchantName":"Yodobashi","domain":"www.yodobashi.com","name":"Nintendo Switch 2","jan":"4902370553023","llmModel":"qwen3.5-4b"}' \
  --app k4k4kux1
```

`ingestOfferFromUrl` はまず merchant record の `selectorConfig` を読み、それが無ければ domain preset を使います。`selectorRollout < 1` の場合は `merchantId + productUrl` の安定 hash で path を `active` / `previous` に割り当てます。その後 JSON-LD / rule-based を試し、失敗または欠損時に Murakumo LLM fallback を使います。返り値の `selectedRevisionId`, `selectorPath`, `rolloutBucket` でどの revision が選ばれたか確認できます。

merchant selector を明示登録したい場合:

```bash
etzhayyim xrpc com.etzhayyim.apps.kakaku.registerMerchant \
  -d '{"merchantName":"Yodobashi","domain":"www.yodobashi.com","selectorProfile":"yodobashi-v1","selectorConfig":{"price":["id=[\"\\'']js_scl_unitPrice[\"\\''][^>]*>\\\\s*([0-9,]+)\\\\s*<"],"availability":{"inStock":["在庫あり"],"outOfStock":["売り切れ"]}}}' \
  --app k4k4kux1
```

期待:
- `fetchedTitle`
- `extractedPrice`
- `offerId`

### 4.6 Merchant Readback

既存 merchant 設定を読む場合:

```bash
etzhayyim xrpc com.etzhayyim.apps.kakaku.listMerchants \
  -d '{"q":"yodobashi","limit":20}' \
  --app k4k4kux1
```

```bash
etzhayyim xrpc com.etzhayyim.apps.kakaku.getMerchant \
  -d '{"domain":"www.yodobashi.com"}' \
  --app k4k4kux1
```

期待:
- `selectorProfile`
- `selectorConfig`
- `updatedAt`

selector revision を見る場合:

```bash
etzhayyim xrpc com.etzhayyim.apps.kakaku.listSelectorRevisions \
  -d '{"merchantId":"yodobashi_com","limit":10}' \
  --app k4k4kux1
```

active revision を切り替える場合:

```bash
etzhayyim xrpc com.etzhayyim.apps.kakaku.activateSelectorRevision \
  -d '{"merchantId":"yodobashi_com","revisionId":"yodobashi_com_v2","rollout":1}' \
  --app k4k4kux1
```

### 5. 価格履歴

```bash
etzhayyim xrpc com.etzhayyim.apps.kakaku.getPriceHistory \
  -d '{"productId":"jan_4902370553023","limit":20}' \
  --app k4k4kux1
```

期待:
- `history` が 2 件以上

## Notes

- `productId` は path resolve に合わせて `jan_4902370553023` のような canonical key を使う。
- landed price は `price + shippingFee`。
- 同一 offer 再投入時は差分が無ければ `historyWritten=false` になる。
- UI editor は [60-apps/etzhayyim-project-apps/appview/apps-cdn-a9p5l1st/svelte/src/App.svelte](/Users/junkawasaki/etzhayyim/etzhayyim-root/60-apps/etzhayyim-project-apps/appview/apps-cdn-a9p5l1st/svelte/src/App.svelte:1)。`pnpm --dir 60-apps/etzhayyim-project-apps/appview/apps-cdn-a9p5l1st/svelte dev` で merchant selector editor を起動できる。
