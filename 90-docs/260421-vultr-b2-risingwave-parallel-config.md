# Vultr + B2 Kotoba/Datomic 並行構成設計

作成: 2026-04-21
ステータス: 提案

## 目的

現在の Linode LKE + Linode Object Storage 構成を維持しつつ、**Vultr + Backblaze B2** をセカンダリ/移行候補として並行稼働させる。B2 公式パートナーである Vultr との組み合わせにより、Egress 無料 + ストレージ単価 70% 削減が見込める。

---

## 1. 現行構成 (Linode / Singapore)

| 項目 | 値 | 月額 |
|---|---|---|
| クラスタ | Linode LKE sg-sin-2 (Kubernetes 1.32) | — |
| ノード | g6-dedicated-16 (16 vCPU / 32 GB RAM Dedicated) | $192 |
| Object Storage | Linode sg-sin-1 `etzhayyim-iceberg` 7.63 TB | ~$152 |
| Block Storage (PVC) | 30 GiB (metastore 10 + state 20) | ~$15 |
| B2 DR レプリカ | rclone sync 15min (backup only) | ~$5 |
| **合計** | | **~$364/月** |

**主要エンドポイント:**
- Kotoba/Datomic PG wire: `172.236.132.11:4566`
- Hyperdrive binding: `e84c0a2babe44fc7b74818e394b4b896`
- Hummock state: `hummock+s3://etzhayyim-iceberg/kotoba/state`
- S3 endpoint: `https://sg-sin-1.linodeobjects.com`

**S3 互換ワークアラウンド (Linode 固有):**
```
AWS_REQUEST_CHECKSUM_CALCULATION=WHEN_REQUIRED
OPENDAL_S3_CHECKSUM_ALGORITHM=""
is_force_path_style=true
```

---

## 2. 提案構成 (Vultr + B2 / Singapore)

### 2-1. コンポーネント構成

```
Cloudflare Workers
  └── Hyperdrive (新 binding)
        └── Vultr VKE LoadBalancer :4566
              └── Kotoba/Datomic Pod (Vultr VKE)
                    └── Hummock state store
                          └── Backblaze B2 ap-southeast-001
                                └── bucket: etzhayyim-iceberg-b2
```

### 2-2. Vultr インスタンス選定

| 用途 | 推奨プラン | vCPU | RAM | 月額 |
|---|---|---|---|---|
| **並行テスト** | High Performance AMD | 8 | 16 GB | $96 |
| **本番同等 (コスト優先)** | High Performance AMD | 16 | 32 GB | ~$192 ※ |
| **本番同等 (Dedicated)** | CPU Optimized | 16 | 32 GB | $320 |

※ Vultr High Performance 16vCPU/32GB は Linode g6-dedicated-16 と同額だが **Shared vCPU**。
Kotoba/Datomic の streaming workload では Dedicated が望ましい。
初期並行テストは 8vCPU/16GB ($96) で問題ない。

**VKE (Vultr Kubernetes Engine):** コントロールプレーン無料。ワーカーノード費用のみ。

### 2-3. Backblaze B2 設定

| 項目 | 値 |
|---|---|
| リージョン | `us-west-004` (US West — B2 に AP リージョン未存在) |
| バケット名 | `etzhayyim-nats` (既存 DR バックアップバケット流用) |
| S3 エンドポイント | `https://s3.us-west-004.backblazeb2.com` |
| Hummock state path | `hummock+s3://etzhayyim-nats/vultr/kotoba/state` |
| Application Key ID | B2 アプリキーID (Keychain: `etzhayyim.b2`) |
| Application Key | B2 アプリキー (Keychain: `etzhayyim.b2`) |

**B2 S3 互換設定 (Linode のワークアラウンド不要):**
```
# 削除してよい項目:
# AWS_REQUEST_CHECKSUM_CALCULATION=WHEN_REQUIRED
# OPENDAL_S3_CHECKSUM_CALCULATION_WHEN_REQUIRED
# OPENDAL_S3_CHECKSUM_ALGORITHM=""

# B2 では標準 S3 SDK 設定で動作
is_force_path_style: false  # B2 は virtual-hosted style 対応
```

### 2-4. Kotoba/Datomic 環境変数差分

```yaml
# 変更箇所のみ (その他は現行 values.yaml を継承)
env:
  - name: RW_STATE_STORE
    value: "hummock+s3://etzhayyim-iceberg-b2/kotoba/state"
  - name: AWS_REGION
    value: "ap-southeast-001"  # B2 region
  - name: AWS_ENDPOINT_URL
    value: "https://s3.ap-southeast-001.backblazeb2.com"
  - name: AWS_ACCESS_KEY_ID
    valueFrom:
      secretKeyRef:
        name: b2-credentials
        key: AWS_ACCESS_KEY_ID
  - name: AWS_SECRET_ACCESS_KEY
    valueFrom:
      secretKeyRef:
        name: b2-credentials
        key: AWS_SECRET_ACCESS_KEY
  # 削除: OPENDAL_S3_CHECKSUM_ALGORITHM
  # 削除: AWS_REQUEST_CHECKSUM_CALCULATION
```

### 2-5. Cloudflare Hyperdrive 追加 binding

現行 Linode binding と**並行して**新規 binding を作成:

```jsonc
// wrangler.jsonc (graph worker / pds worker に追加)
"hyperdrive": [
  {
    "binding": "HYPERDRIVE",
    "id": "e84c0a2babe44fc7b74818e394b4b896"  // 既存 Linode
  },
  {
    "binding": "HYPERDRIVE_VULTR",
    "id": "<新規作成>",                        // 新 Vultr endpoint
    "localConnectionString": "postgresql://root@<vultr-lb-ip>:4566/dev"
  }
]
```

切り替え時は `HYPERDRIVE_VULTR` → `HYPERDRIVE` にリネームするだけ。

---

## 3. コスト比較

| 項目 | Linode 現行 | Vultr + B2 (並行テスト) | Vultr + B2 (本番同等) |
|---|---|---|---|
| Compute | $192 (16vCPU/32GB Ded.) | $96 (8vCPU/16GB HP) | $192–$320 |
| Object Storage (7.63 TB) | $152 (Linode $20/TB) | **$46** (B2 $6/TB) | **$46** |
| Block Storage (PVC) | $15 | $15 | $15 |
| Egress (Vultr↔B2) | $5 (B2 repl.) | **$0** (公式パートナー) | **$0** |
| **合計** | **$364** | **$157** | **$253–$381** |
| **差額** | — | **-$207** | **-$111〜+$17** |

> **ストレージだけで $106/月削減**。Vultr High Performance 16vCPU/32GB が ~$192 なら本番同等でも $111/月のコスト削減。

---

## 4. B2 Egress 無料の適用範囲

Vultr は B2 の **Bandwidth Ally** 公式パートナー。以下が無料:

- Vultr Worker (VKE pod) → B2 ダウンロード (Hummock read)
- Vultr → B2 アップロードは元々無料 (write は B2 課金なし)
- B2 の free egress 3x ルール: 月平均保存量の 3 倍まで無料 (7.63 TB → 22.9 TB/月まで)

---

## 5. 並行稼働の方針

### Phase 1: Vultr + B2 でテスト稼働 (並行)

1. Vultr VKE クラスタ作成 (Singapore、ワーカー 1 node: High Performance 8vCPU/16GB)
2. B2 バケット `etzhayyim-iceberg-b2` 作成 (ap-southeast-001)
3. B2 Application Key 発行 → macOS Keychain `etzhayyim.b2` に登録
4. Kubernetes Secret `b2-credentials` 作成
5. Kotoba/Datomic Helm デプロイ (B2 endpoint に向ける)
6. Hyperdrive 新規 binding 作成 → `HYPERDRIVE_VULTR` として worker に追加
7. Linode B2 rclone バックアップから初期データリストア
8. 読み書き動作確認 (psql + Hyperdrive)

### Phase 2: 本番切り替え (判断ポイント)

- Vultr High Performance 16vCPU/32GB の実コスト確認後に判断
- `HYPERDRIVE_VULTR` → `HYPERDGLE` にリネームして deploy
- Linode 構成を DR に降格 or 廃止

---

## 6. ファイル配置計画

```
50-infra/
  vultr/
    kotoba/
      values.yaml          # Helm values (B2 endpoint 差分のみ)
      deploy.sh            # VKE デプロイスクリプト
      b2-secret.sh         # B2 credentials → K8s Secret 作成
      deps.toml            # 構成値 SSoT
```

---

## 7. 注意事項・リスク

| リスク | 対処 |
|---|---|
| B2 の AP リージョン不在 | B2 は US West / US East / EU Central / CA East のみ。Vultr SGP → B2 US West は ~150ms だが Hummock は非同期フラッシュ主体のため影響小 |
| Hummock の S3 互換性 | B2 は AWS S3 API 完全互換。Linode 固有のワークアラウンド不要 |
| Vultr HP は Shared vCPU | Kotoba/Datomic compute は CPU バースト依存。本番は Dedicated ($320) を検討 |
| 初期データ投入 | Linode B2 DR バックアップ (rclone) から直接リストア可 → 既に B2 に 7.63 TB 存在 |
| Foyer キャッシュ | emptyDir 32 GiB → VKE でも同様に設定可 |
