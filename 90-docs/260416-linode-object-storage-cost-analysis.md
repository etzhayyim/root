# Linode Object Storage コスト分析と最適化 (2026-04-16)

## 背景

2026-04-13 に S3 Object Versioning を有効化した直後、`etzhayyim-iceberg` バケットが 38 GB → 18.74 TB (4日間) に急膨張。本ドキュメントは原因・対処・コスト比較の学びを記録する。

---

## 原因分析: Versioning × Hummock LSM の相性

RisingWave Hummock は S3 を LSM-tree の永続層として使う。コンパクション時に古い SSTable (SST) を S3 DELETE で削除しながら新しい SST を PUT し続ける。

| 設定 | 動作 |
|---|---|
| Versioning **無効** | DELETE = 物理削除。ストレージ = 現時点の live SST のみ |
| Versioning **有効** | DELETE = Delete Marker 作成。旧 SST は noncurrent version として残り続ける |

結果: 4日間で ~3.2 TB/day のコンパクションチャーンが noncurrent として積み上がり **12.8 TB** の不要データが生成された。

### hummock_min_sst_retention_time_sec との関係

`hummock_min_sst_retention_time_sec` (デフォルト 86400 = 24h) は **RisingWave 内部** のガベージコレクション抑制パラメータであり、S3 versioning とは完全に独立。この値は「RW が自分で削除リクエストを出すまでの最低待機時間」であり、S3 側の Lifecycle ルールとは別の概念。

---

## 対処: Lifecycle ルール最適化 + 手動 Purge

### Lifecycle 変更 (2026-04-16)

| ルール | 変更前 | 変更後 | 根拠 |
|---|---|---|---|
| `sst-noncurrent-*days` | NoncurrentDays=30 → 3 | **NoncurrentDays=1** | B2 rclone sync */15min が current state を全量複製。Linode versioning は DR として不要 |
| `backup-snapshot-*days` | Expiration.Days=30 | **Expiration.Days=7** | B2 に複製済みのため 30 日は過剰 |
| `abort-incomplete-multipart` | なし | DaysAfterInitiation=7 | ゴミ防止 |

### 手動 Purge 結果

```
削除オブジェクト数: 1,304,267
削除データ量:      ~12.8 TB
実行後バケットサイズ: 7.63 TB (18.74 TB → 7.63 TB)
```

スクリプト: `list_object_versions` + `delete_objects` 500件バッチ、5リトライ指数バックオフ。  
Linode が大量削除時に `InternalError: failed authorization` を返す（レートリミット）ため、バッチサイズとリトライが重要。

---

## B2 Latency ベンチマーク (2026-04-16 実測)

### 測定環境

| シナリオ | 測定元 | バケット先 |
|---|---|---|
| **A: Same-region** | Linode SG (sg-sin-2) | Linode Object Storage sg-sin-1 |
| **B: Cross-region** | Linode SG (sg-sin-2) | B2 us-west-004 (Sacramento/Fremont) |
| **C: B2 same-region** | Linode US West (nanode) | B2 us-west-004 |

### PUT レイテンシ (ms, REPS=5 + warmup)

| オブジェクトサイズ | A (SG same) | B (SG→B2 cross) | C (US West→B2) |
|---|---|---|---|
| 4 KB | ~2ms | ~220ms | ~8ms |
| 256 KB | ~5ms | ~250ms | ~15ms |
| 4 MB | ~25ms | ~310ms | ~45ms |
| 64 MB | ~350ms | ~900ms | ~420ms |

### GET レイテンシ (ms)

| オブジェクトサイズ | A (SG same) | B (SG→B2 cross) | C (US West→B2) |
|---|---|---|---|
| 4 KB | ~2ms | ~46ms | ~7ms |
| 256 KB | ~4ms | ~52ms | ~10ms |
| 4 MB | ~20ms | ~120ms | ~30ms |
| 64 MB | ~280ms | ~890ms | ~310ms |

### 評価

- **Option A (現行)**: GET が最速。Hummock の高頻度コンパクション読み取りに最適。
- **Option B (SG→B2)**: GET が 23x 遅い。Hummock プライマリとして非現実的。
- **Option C (US West + B2)**: SG からの移行なしで検討可能。Linode ノードを US West に移せば viable。ただし現行 SG ユーザーへのレイテンシ影響あり。

---

## B2 3-region Global Replica コスト分析

### 現行コスト (Linode Object Storage, Singapore)

| 項目 | 計算 | 月額 |
|---|---|---|
| Storage (8.21 TB) | 8.21 × $20/TB | $164 |
| Egress (RisingWave reads) | 同一DC = 無料 | $0 |
| **合計** | | **~$164/月** |

### B2 3-region をプライマリにした場合

| 項目 | 計算 | 月額 |
|---|---|---|
| Storage (3 replicas × 8.21 TB) | 3 × 8.21 × $6/TB | $148 |
| Egress: RisingWave → B2 reads | X TB × $10/TB | **$10X/月** |
| Cross-region replication egress | server-side でも課金される可能性 | 要確認 |

**ストレージ節約額: $16/月。しかし Hummock の S3 GET エグレスが支配的になる。**

### Hummock コンパクション read 量の見積もり

実測チャーン: ~3.2 TB/day の SST 作成・削除 = 月間 ~96 TB の S3 PUT。  
コンパクション時の S3 GET は PUT と同程度〜2倍程度（マージ元読み取り）。

| Foyer キャッシュヒット率 | 月間 S3 GET | B2 Egress 費 |
|---|---|---|
| 90% (Foyer 効果大) | ~9.6 TB | **$96/月** |
| 80% | ~19.2 TB | $192/月 |
| 70% | ~28.8 TB | $288/月 |

B2 プライマリ合計: $148 (storage) + $96〜$288 (egress) = **$244〜$436/月**

### 結論

```
B2 3-region primary への移行は「コスト増」
Linode same-DC egress 無料の優位性を egress 課金が上回る
```

Hummock のような高チャーン LSM workload には **同一 DC に egress 無料のストレージを置く**のが最適。B2 のコスト優位は storage 単価のみであり、read-heavy workload では逆転する。

---

## 最適アーキテクチャ (決定)

```
RisingWave (Linode SG, sg-sin-2)
  ↕ free egress (同一DC)
Linode Object Storage etzhayyim-iceberg (PRIMARY, sg-sin-1)
  ↓ rclone linode-to-b2-replication CronJob */15min (write-only, ingress free)
B2 us-west-004 etzhayyim-nats/linode/etzhayyim-iceberg (DR replica)
  └ hard_delete=false → B2 側も hidden version 保持
```

| 役割 | 月額 |
|---|---|
| Linode Object Storage (PRIMARY) | ~$153 (7.63 TB × $20/TB) |
| B2 DR replica (storage only, reads ほぼなし) | ~$46 (7.63 TB × $6/TB) |
| **合計** | **~$199/月** |

`kagami-graphar` (Common Crawl parquet, 0.58 TB, write-once) については B2 移行は有効 ($3.5/月 vs $11.6/月, $8/月節約)。ただし額が小さいため優先度低。

---

## Linode S3 API 注意点

Linode Object Storage は AWS Chunked Encoding を拒否する。boto3 から PutObject する際に必須:

```bash
export AWS_REQUEST_CHECKSUM_CALCULATION=WHEN_REQUIRED
export AWS_RESPONSE_CHECKSUM_VALIDATION=WHEN_REQUIRED
```

これがないと `AccessDenied` または `400 Bad Request` が返る。

---

## 関連

- `50-infra/linode/risingwave-iceberg/deps.toml` — バケット設定・lifecycle rules・B2 レプリケーション設定
- `50-infra/linode/risingwave-iceberg/kustomize/base/b2-replication-cronjob.yaml` — rclone CronJob
- `50-infra/linode/risingwave-iceberg/paths/backup-restore.md` — バックアップ/リストア手順
