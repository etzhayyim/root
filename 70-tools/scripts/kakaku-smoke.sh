#!/usr/bin/env bash
set -euo pipefail

APP_ID="${APP_ID:-k4k4kux1}"

echo "==> register merchant: yodobashi"
gftd xrpc ai.gftd.apps.kakaku.registerMerchant \
  -d '{"merchantName":"Yodobashi","domain":"www.yodobashi.com","baseCurrency":"JPY","shippingPolicy":"standard","reputationScore":0.95}' \
  --app "$APP_ID"

echo "==> register merchant: biccamera"
gftd xrpc ai.gftd.apps.kakaku.registerMerchant \
  -d '{"merchantName":"BicCamera","domain":"www.biccamera.com","baseCurrency":"JPY","shippingPolicy":"standard","reputationScore":0.92}' \
  --app "$APP_ID"

echo "==> register product: Nintendo Switch 2"
gftd xrpc ai.gftd.apps.kakaku.registerProduct \
  -d '{"name":"Nintendo Switch 2","brand":"Nintendo","model":"Switch 2","jan":"4902370553023","category":"game_console"}' \
  --app "$APP_ID"

echo "==> upsert offer: yodobashi"
gftd xrpc ai.gftd.apps.kakaku.upsertOffer \
  -d '{"productId":"jan_4902370553023","name":"Nintendo Switch 2","brand":"Nintendo","model":"Switch 2","jan":"4902370553023","merchantName":"Yodobashi","domain":"www.yodobashi.com","merchantSku":"4902370553023","price":49980,"shippingFee":0,"currency":"JPY","availability":"in_stock","deliveryEta":"P2D","productUrl":"https://www.yodobashi.com/product/4902370553023/","observedAt":"2026-04-11T00:00:00Z"}' \
  --app "$APP_ID"

echo "==> upsert offer: biccamera"
gftd xrpc ai.gftd.apps.kakaku.upsertOffer \
  -d '{"productId":"jan_4902370553023","name":"Nintendo Switch 2","brand":"Nintendo","model":"Switch 2","jan":"4902370553023","merchantName":"BicCamera","domain":"www.biccamera.com","merchantSku":"4902370553023","price":49780,"shippingFee":550,"currency":"JPY","availability":"in_stock","deliveryEta":"P1D","productUrl":"https://www.biccamera.com/product/4902370553023/","observedAt":"2026-04-11T00:05:00Z"}' \
  --app "$APP_ID"

echo "==> compare offers"
gftd xrpc ai.gftd.apps.kakaku.compareOffers \
  -d '{"productId":"jan_4902370553023","limit":10}' \
  --app "$APP_ID"

echo "==> get price history"
gftd xrpc ai.gftd.apps.kakaku.getPriceHistory \
  -d '{"productId":"jan_4902370553023","limit":20}' \
  --app "$APP_ID"
