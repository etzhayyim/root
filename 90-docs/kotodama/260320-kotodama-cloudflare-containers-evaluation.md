---
id: 260320-kotodama-cloudflare-containers-evaluation
title: Kotodama vs Cloudflare Containers Evaluation
status: active
doc_type: explanation
topic: runtime-selection
authoritative: true
last_verified: 2026-03-20
authoritative_for:
  - kotodama runtime default vs container fallback
related:
  - 260320-kotodama-cloudflare-containers-evaluation
  - 260320-kotodama-cloudflare-worker-rpc-optimization
supersedes: []
superseded_by: []
---

# Kotodama vs Cloudflare Containers Evaluation

Date: 2026-03-20

## Goal

`kotodama` の現行 default である **split Workers**

- frontend: Svelte / AppShell Worker
- backend: TS native Worker

と、Cloudflare の `Static Frontend, Container Backend` 例に近い **frontend Worker + container backend** を比較し、`kotodama` 全体設計としてどちらを標準に置くべきかを評価する。

この文書は「Cloudflare Containers を使うべきか」を一般論で語るものではない。`kotodama` の app topology と traffic shape を前提に判断する。

## Scope

比較対象は次の 2 方式である。

### A. Current default: split Workers

```text
Browser
  -> frontend Worker
     -> Service Binding / Workers RPC
        -> backend TS native Worker
           -> yata / internal Workers services
```

### B. Alternative: Worker + container backend

```text
Browser
  -> frontend Worker
     -> Durable Object / Container control path
        -> container backend
           -> native process / filesystem
```

## Executive Summary

`kotodama` 全体の標準としては、**split Workers を維持するべき**である。

Cloudflare Containers は有用だが、`kotodama` の primary workload である次の特性とは相性がよくない。

- 小さい payload の command/query が多い
- app-to-app / service-to-service の internal typed call が多い
- miniapp/backend 間の低レイテンシ fan-out が多い
- app 数が増えるほど per-app fixed overhead を抑えたい

一方で Containers は、次の要件では妥当な fallback になる。

- native Wasmtime host が必要
- Linux filesystem が必要
- Worker では扱いにくい CPU / memory / disk が必要
- Signal / evolution / vector search のように process-heavy な runtime を持ちたい

## Decision

### Platform default

- **Default**: split Workers
- **Fallback**: Cloudflare Containers

### Why

1. `kotodama` の通常 app は control-plane heavy であり、Workers RPC / Service Binding の locality を活かしやすい
2. Containers は Worker 課金に加え、Container resource と Durable Object の課金が積み上がる
3. Containers は cold start と placement の不確実性が大きく、一般 app backend の標準にするには不利
4. Containers は 2026-03-20 時点で Beta であり、運用前提の安定性は Workers より弱い

## Comparison

| Axis | Split Workers | Worker + Container backend | Verdict for `kotodama` |
|---|---|---|---|
| Cost | Worker request/CPU 中心 | Worker + Container + Durable Object | split Workers |
| p50/p95 latency | 小 payload internal call で有利 | DO/container path が増える | split Workers |
| **RPC transport** | **Workers RPC zero-copy (Cap'n Proto, 16B overhead, same-thread)** | **HTTP fetch only (~1-5ms same-colo)。Container は V8 isolate 外 (gVisor sandbox) のため Workers RPC 不可** | **split Workers** |
| Cold start | 小さい | 2-3s 級がありうる | split Workers |
| Runtime capability | Worker 制約あり | full filesystem / native runtime 可 | container |
| Operational maturity | 高い | Beta | split Workers |
| Best fit | standard app backend | heavy native runtime | split Workers as default |

## Cost Evaluation

## Split Workers

`kotodama` default path は、主に次の課金で成立する。

- Workers requests
- Workers CPU duration

Cloudflare Workers Paid plan では、月額 `$5` に以下が含まれる。

- 10M requests / month
- 30M CPU ms / month

超過分は 2026-03-20 時点で次の単価である。

- `$0.30 / million requests`
- `$0.02 / million CPU ms`

このため、小さい internal call を多数さばく app 群では、split Workers はかなりコスト効率がよい。

## Containers

Cloudflare Containers は、Workers Paid plan 上で追加課金される。Containers 自体の billing は次の通り。

- memory: 25 GiB-hours / month included, then `$0.0000025 / GiB-second`
- CPU: 375 vCPU-minutes / month included, then `$0.000020 / vCPU-second`
- disk: 200 GB-hours / month included, then `$0.00000007 / GB-second`

加えて Cloudflare は、Containers 利用時は次も課金対象だと明記している。

- Worker usage
- Durable Object usage

したがって、`kotodama` のような app 数の多い platform では、container backend を標準にすると **per-app の固定的なコスト要素が増えやすい**。

## Cost conclusion

通常の App backend では、**container backend を標準化すると高くつきやすい**。特に:

- 軽量 command/query が主体
- 多数の app を横並びで運用
- bursty traffic が多い

という条件では split Workers の方が有利である。

## Performance Evaluation

## Split Workers path

Cloudflare Service Bindings は Worker 間接続の標準であり、Cloudflare は同一サーバ・同一スレッド実行になりうることを説明している。Workers RPC も internal typed call の標準であり、Cloudflare docs では大半の use case で推奨されている。

`kotodama` では次の path が多い。

- frontend Worker -> backend Worker
- backend Worker -> yata Worker
- backend Worker -> internal capability worker

この構造は、`kotodama` の control-plane heavy な設計に合っている。

## Container path

Cloudflare Containers は、Worker のコードから Durable Object 経由で container instance を制御する設計である。Cloudflare docs では、現時点で Durable Object と associated container instance は co-located することもあるが、しばしばそうではないと説明している。

これは `kotodama` では次の問題を生む。

- internal call path が 1 段深くなる
- DO/container placement が latency variance を増やす
- small typed call の積み重ねで不利になる

また Cloudflare docs では、container cold start は **2-3 seconds** 程度になりうるとされる。これは通常の App backend の API 応答としては重い。

## Performance conclusion

small payload の internal command/query を高頻度で行う `kotodama` では、**split Workers の方が基本的に速い**。container backend は、low-latency typed internal API の標準には向かない。

## Stability Evaluation

Cloudflare Containers は 2026-03-20 時点で **Beta** である。

この前提で、一般 app backend の標準に採用すると次の不確実性が残る。

- placement / routing policy の今後の変更余地
- autoscaling / latency-aware behavior の進化余地
- DO/container orchestration 自体の仕様変化
- cold start / image prefetch / sleep behavior の運用読みづらさ

一方、split Workers は Cloudflare platform の中心的な実行形態であり、現時点では設計のベースラインとしてこちらの方が安定している。

## Stability conclusion

**全体標準は split Workers、container は例外的 fallback** が妥当である。

## Container Scaling (Verified Platform Facts, 2026-03-24)

| Mechanism | Implementation | Status |
|---|---|---|
| **`getByName(name)`** | DO 標準 API。名前 → deterministic DO ID → stub。**存在しなければ初回 `fetch()` で自動作成** | GA (DO API) |
| **`getRandom(env, N)`** | `Math.floor(Math.random() * N)` → `"instance-{id}"` → `getByName()`。**ランダム選択のみ (LB ロジックなし)** | Temporary stopgap |
| **`loadBalance(env, N)`** | **`getRandom` の deprecated alias** (中身同一) | Deprecated |
| **`getContainer(env, name?)`** | 名前指定で特定 instance 取得 (default: singleton) | Beta |
| **Scale up** | 新しい名前で `getByName()` を呼ぶだけ → 自動作成 | Manual/code |
| **Scale down** | `sleepAfter` 経過で自動 sleep ($0)。`stop()`/`destroy()` も可 | Automatic |
| **Discovery API** | **存在しない** — 自分で名前スキーム + partition count を管理する必要あり | — |
| **`max_instances`** | `wrangler.jsonc` のハードキャップ | Config |
| **Auto-scaling** | **未リリース** — `autoscale = true` (CPU/memory ベース) が計画中 | Planned |

### Scaling Design Implications

- **Partition URL を Cypher/B2 に保存する必要はない** — `getByName("partition-{i}")` で CF が routing 解決 (DO naming)
- **Discovery 不要** — partition count (`YATA_PARTITION_COUNT`) さえ知っていれば `0..N` で全 instance にアクセス可能
- **動的 scale = redeploy** — partition count 変更は env var 変更 + redeploy が現状唯一の方法
- **Container 間直接通信は構造的に不可能** — `getByName()` は TS companion Worker からのみ使用可能。Container binary (Rust) から他 Container DO に直接アクセスする API は CF が提供していない
- **TS companion Worker は thin router として不可避** — DO routing (`getByName`) + `fetch()` proxy が CF の構造的制約。Routing 判断 (hash, label hints) と merge は Rust binary 側で強化可能

## When Containers Are Justified

次の条件がある場合にのみ、container backend を積極的に選んでよい。

- native Wasmtime host が必要
- Linux filesystem / process model が必要
- Worker 制約を超える memory / disk / parallel CPU が必要
- cold start を吸収できる workload である
- per-app resource overhead を受け入れられる

`kotodama` では、代表例は次である。

- Signal-heavy runtime
- evolution runtime
- vector search / native index
- native helper binary を伴う app

## What This Means for Kotodama

### Standard architecture

```text
Browser
  -> frontend Worker
     -> Service Binding / Workers RPC
        -> backend TS native Worker
           -> yata / internal workers
```

### Container policy

- container backend を default にしない
- app の runtime requirement が Worker 上限を超える場合のみ選ぶ
- container backend は `kotodama-server` 系 runtime 用 fallback として維持する

この評価は repo の既存方針と一致する。

- [40-engine/kotoba/crates/kotoba-kotodama/CLAUDE.md](/Users/junkawasaki/github/etzhayyim-root/40-engine/kotoba/crates/kotoba-kotodama/CLAUDE.md)
- [60-apps/CLAUDE.md](/Users/junkawasaki/etzhayyim/etzhayyim-root/60-apps/CLAUDE.md)
- [90-docs/260320-kotodama-cloudflare-worker-rpc-optimization.md](/Users/junkawasaki/etzhayyim/etzhayyim-root/90-docs/260320-kotodama-cloudflare-worker-rpc-optimization.md)
- [90-docs/260320-kotodama-runtime-dual-backend-design.md](/Users/junkawasaki/etzhayyim/etzhayyim-root/90-docs/260320-kotodama-runtime-dual-backend-design.md)

## LLM-Friendly Documentation Pattern

この種の分析を、あとで LLM が理解しやすく蓄積するなら、各文書を次の固定構造で揃えるのがよい。

### 1. Front matter equivalent

文書冒頭に最低限次を固定順で置く。

- title
- date
- decision status
- scope
- related docs

### 2. First-screen summary

冒頭 10-20 行で次を明示する。

- question
- conclusion
- default
- fallback
- non-goals

LLM は先頭要約を強く使うため、ここに設計判断の正規化結果を置く。

### 3. Stable section order

設計文書は毎回同じ見出し順にする。

1. Goal
2. Scope
3. Executive Summary
4. Decision
5. Comparison
6. Rationale
7. Exceptions
8. Consequences
9. References

見出し順を固定すると、複数文書をまとめるときに機械的に要約しやすい。

### 4. Separate facts from policy

各文書で次を混ぜない。

- platform facts
- repo policy
- local inference

最低でも次の 3 区分を明示する。

- Verified Platform Facts
- Kotodama Policy
- Inference / Evaluation

LLM は「事実」と「判断」を混同しやすいため、ここを分けるだけで再利用性が上がる。

### 5. Normalize decisions into explicit fields

文中で曖昧に書かず、決定事項を短い箇条書きで固定化する。

- Default:
- Allowed when:
- Avoid when:
- Not allowed:

この形式にすると、後で decision table を自動抽出しやすい。

### 6. Add a compact decision table

長文説明だけでなく、必ず 1 個の比較表を入れる。

- axis
- option A
- option B
- verdict

LLM は表をそのまま feature matrix として再利用しやすい。

### 7. Keep one document to one question

1 文書 1 論点を維持する。

- Worker RPC 最適化
- Container 採用可否
- dual-backend contract

を 1 つに混ぜない。クロスリンクでつなぐ。

### 8. End with machine-friendly references

末尾に次を置く。

- related internal docs
- external canonical URLs
- as-of date

これで「この判断はいつ時点の何に依存していたか」を後で追える。

## References

As of 2026-03-20.

- Cloudflare Containers overview: <https://developers.cloudflare.com/containers/>
- Cloudflare Containers example: <https://developers.cloudflare.com/containers/examples/container-backend/>
- Cloudflare Containers pricing: <https://developers.cloudflare.com/containers/pricing/>
- Cloudflare Containers architecture / lifecycle: <https://developers.cloudflare.com/containers/platform-details/architecture/>
- Cloudflare Containers scaling and routing: <https://developers.cloudflare.com/containers/scaling-and-routing/>
- Cloudflare Workers pricing: <https://developers.cloudflare.com/workers/platform/pricing/>
- Cloudflare Durable Objects pricing: <https://developers.cloudflare.com/durable-objects/platform/pricing/>
- Cloudflare Service Bindings: <https://developers.cloudflare.com/workers/runtime-apis/bindings/service-bindings/>
- Cloudflare Workers RPC: <https://developers.cloudflare.com/workers/runtime-apis/rpc/>
