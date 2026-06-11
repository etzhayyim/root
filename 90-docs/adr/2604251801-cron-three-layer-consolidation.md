---
id: adr-2604251801-cron-three-layer-consolidation
title: "ADR: 定期実行は k8s CronJob / Zeebe BPMN timer / Python worker の 3 レイヤーに集約、CF Worker triggers.crons / GH Actions schedule / launchd / ansible crontab を deprecate"
status: proposed
doc_type: adr
topic: scheduled-execution
authoritative: true
last_verified: 2026-04-25
authoritative_for:
  - cron-implementation-layer
related:
  - adr-0056-bpmn-as-actor
  - adr-2604240946-yoro-autonomous-actor-hybrid-loop
  - adr-2604250836-langgraph-as-zeebe-servicetask
supersedes: []
superseded_by: []
amends: []
---

# Context

リポジトリ全体の cron / 定期実行を全件棚卸し (2026-04-25 session) すると、
**6 つの実装レイヤー** が並走している:

1. **Cloudflare Worker `triggers.crons`** — 18 worker
2. **Kubernetes `CronJob`** — 10 job (vultr / linode)
3. **Zeebe BPMN timer-start** — 32 process (`R/PT*` + cron 表記)
4. **GitHub Actions `schedule`** — 3 workflow
5. **macOS launchd plist** — 1 (legacy-trust-tally、5/8 で expire)
6. **Murakumo fleet ansible/crontab (goose)** — 3 entry

レイヤー間の使い分けに一貫した基準が無く、同種ジョブが 1〜3 が場所で
実装される drift が観測される (例: yoro autonomous loop は BPMN 化済みだが
murakumo 上の goose crontab にも `yoro-persona-cron` が残存)。
ADR-0056 (BPMN-as-actor) と ADR-2604250836 (LangGraph as Zeebe ServiceTask)
で Zeebe を業務 orchestration の SSoT に決めた以上、cron 実装層も
Shannon η の観点で集約する必要がある。

# Decision

定期実行は次の **3 レイヤー** に限定する。新規ジョブはこのいずれかで
実装する。既存の他レイヤージョブは順次移行する。

## 1. k8s CronJob — infra / batch / backup

**役割**: クラスタ内部リソース (Kotoba/Datomic / B2 / OSM / 医療データ) を
直接触る、長尺バッチ・バックアップ・大容量 ingest。

**選定基準**:
- 実行時間が 30s 以上 / メモリ 512MB 以上を要する
- k8s native リソース (Secret, PVC, NetworkPolicy) に依存
- CF Worker の 30s/128MB 制約を超える

**現行該当**: medical-coverage-ingester, maps-osm-ingest,
gyosei-source-archiver, maps-coverage-ticker ×2, rw-meta-backup ×2,
data-collection, b2-replication, shinka-tick (helm `enabled=false` 扱い)

## 2. Zeebe BPMN timer-start — business orchestration

**役割**: 業務プロセスとして可視化すべき定期 actor 起動。
`R/PT*` または cron 表記の timer-start event。

**選定基準**:
- 1 actor = 1 NSID にマップされる業務行為
- 失敗・retry・compensation を BPMN で記述したい
- `etzhayyim-root/00-contracts/bpmn/com/etzhayyim/<project>/<method>.bpmn` の DSL で表現可

**現行該当**: yoro/platformPulse, animeka/autopilot, kotodama/shinkaCronTick,
shinka/manualTick, kouza/syncDueConnections, maps/* (6 process),
tsukuru/* (21 業種), purge/* (7 PII purge), patent/* (3 process)

## 3. Python worker (kotodama / pyzeebe job worker) — actor primitive

**役割**: BPMN ServiceTask から呼ばれる primitive 実装、または
Zeebe runtime に常駐するカスタム job worker。

**選定基準**:
- BPMN から呼び出される atomic operation
- Python エコシステム (pandas / RDKit / playwright / scrapy 等) が必要
- 単独 cron ではなく、BPMN timer から triggered job として動く

**現行該当**: kotodama dispatcher (F5 watcher),
generic.{db,pds,agent,llm}.* primitives,
defence cluster watcher

# Deprecated layers

以下 4 レイヤーは新規追加を **禁止**、既存は順次 1〜3 に移行する。

## 4-A. CF Worker `triggers.crons` (deprecated, 18 worker 該当)

**理由**:
- 30s/128MB 上限、cold start lottery、observability が CF dashboard 限定
- BPMN orchestration から外れた "見えない" 定期実行が増殖
- Zeebe BPMN timer + ServiceTask (CF Worker XRPC 呼び出し) で等価実装可

**移行先**:
- M365 token refresh (calendar/contacts/cowork/docs/drive/gmail/meet/sheets/slides/tasks の `*/15` or `*/30`)
  → BPMN `R/PT15M` timer + `m365TokenRefresh.bpmn` ServiceTask が
  該当 worker の token endpoint を叩く
- atproto / graph / kotodama / murakumo (`*/5`, `* * * * *`) → 内部
  state housekeeping。BPMN timer + 該当 worker の `/_cron/tick` XRPC へ
- bluesky / bpmn / public-malak / kg-curator → 同上、BPMN timer 化
- **例外**: CF Worker の `scheduled()` handler 自体は残してよいが、
  起動 trigger は CF cron ではなく Zeebe timer 経由とする

## 4-B. GitHub Actions `schedule` (deprecated, 3 workflow)

**理由**: CI レポジトリ操作を含むジョブを除き、業務 cron を Actions に
置くと観測点が分散する。

**移行先**:
- coverage-site (`15 */6 * * *`) / cohort-coverage (`17 18 * * 0`) /
  domain-coverage-health (`12 20 * * *`)
  → k8s CronJob (Hummock 直読 + B2 write が自然) または BPMN timer
  (coverage 系は既に BPMN actor 化済み — `maps/refreshCoverageStats`)

**例外**: PR 操作 / CI artifact 生成 / docs registry lint 等、
リポジトリ操作が本質のジョブは GH Actions に残す (今回の 3 つは
Hummock 集計が本質なので移行対象)。

## 4-C. macOS launchd (deprecated, 1 plist)

**理由**: 単一マシン (mac-mini) 依存で HA 不可。

**移行先**:
- `com.etzhayyim.legacy-trust-tally.plist` (γ2 cutover tally, 9:17 daily)
  は 2026-05-08 に自動 cleanup する短命 job。**移行不要、消化待ち**。

**今後**: etzhayyim 個人 mac の launchd は agent-token / vault
unlock 等の **session-bound** 用途のみに限定する (cron 化しない)。

## 4-D. Murakumo fleet ansible/crontab — goose recipes (deprecated, 3 entry)

**理由**: yoro autonomous loop は ADR-2604240946 で BPMN R/PT4H 化
されているにもかかわらず、murakumo 側 goose crontab に冗長な
yoro-* recipe が残っている。

**移行先**:
- `yoro-profile-heartbeat` (`*/15`) → BPMN timer or PDS write の側に
  heartbeat collection を生やす
- `yoro-persona-cron` (`0 */4`) → ADR-2604240946 の `platformPulse` に
  統合済みの可能性。重複なら停止
- `yoro-mention-drain` (`*/15`) → `respondToMention.bpmn` が
  XRPC-triggered で代替済み。停止可能性高い

**今後**: goose 自体は LangGraph に置換予定 (ADR-2604250836 の延長線)、
mac-mini fleet 上の cron は撤廃する。

# Rationale

| 軸 | k8s CronJob | Zeebe BPMN | Python worker | (deprecated) CF cron | (deprecated) GH cron |
|---|---|---|---|---|---|
| Observability | k8s metrics + tail | Zeebe Operate UI | Zeebe job log | CF dashboard | GH Actions log |
| Retry / compensation | restartPolicy のみ | 完全 (boundary event) | BPMN 経由で得る | なし | re-run only |
| HA | k8s scheduler | Zeebe broker cluster | Zeebe worker pool | CF edge | GH runner |
| 上限 | node リソース | 数十秒-数日 | 自由 | 30s/128MB | 6h |
| 業務可視化 | × | ◎ | ○ (BPMN 経由) | × | × |

3 レイヤーで全 cron use case を覆える。重複層を排除することで
"どこで動いているか" の探索コストが下がり、ADR-0056 / ADR-2604240946
の宣言済み topology と整合する。

# Exceptions

- **GH Actions schedule** — repo 操作 (docs registry lint / link-check /
  PR triage) が本質のジョブは残す
- **launchd** — session-bound (vault unlock / agent-token refresh) は残す。
  cron 化しない
- **CF Worker `scheduled()` handler** — handler 実装は残してよい。
  trigger を CF cron ではなく Zeebe timer 経由 XRPC に切り替える
- **個人 mac の crontab / launchd** — etzhayyim 個人運用ツール
  (ローカル backup 等) は対象外

# Migration

具体的な移行タスクは `deps.toml [[migrations]]` に分割登録する:
- `cf-worker-cron-to-zeebe-timer-2026-04-25` — CF Worker 18 cron → BPMN timer
- `gh-actions-schedule-to-k8s-cronjob-2026-04-25` — GH Actions 3 schedule → k8s CronJob
- `goose-crontab-retirement-2026-04-25` — Murakumo goose 3 recipe 停止

launchd `legacy-trust-tally` は 5/8 自動 cleanup につき migration 不要。

# References

- ADR-0056 BPMN-as-actor
- ADR-2604240946 yoro autonomous BPMN R/PT4H cadence
- ADR-2604250836 LangGraph as Zeebe ServiceTask
- root `CLAUDE.md` §Scope Notes (Future Work Classification Rule)
