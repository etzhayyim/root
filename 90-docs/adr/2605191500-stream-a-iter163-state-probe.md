---
id: adr-2605191500-stream-a-iter163-state-probe
title: Stream A iter163 state probe + Backblaze B2 billing CRITICAL
status: active
doc_type: adr
topic: revenue-ops
authoritative: true
last_verified: 2026-05-19
authoritative_for:
  - stream-a-iter163-state
  - backblaze-b2-billing-critical
related:
  - 90-docs/adr/0048-risingwave-vultr-b2-primary.md
  - adr-2605181400-bpmn-extract-to-etzhayyim-root
  - _working/etzhayyim-revenue/DECISION-LOG.md
  - _working/etzhayyim-revenue/stream-a-activation-runbook.md
supersedes: []
superseded_by: []
---

# Context

iter163 (2026-05-19) を Stream A (lawfirm.etzhayyim.com 集客 reactivation,
Y1 USD 175K baseline) の状態 probe + 次アクション決定のために立てた。

iter144 で BPMN を etzhayyim-root に物理移管 (ADR-2605181400) し、
12,315 commits の filter-repo orphan を `git reset --hard origin/main`
で除去した結果、Stream A の outbox/runbook が一時的に lost。orphan
commit `2a75644aa1b` から 4 件 (outbox/11-13 + runbook) を `git show`
で復元済。

iter163 ではこの復元後の状態確認 + Stream A の進行状況を inbox
listInbox で確認した。

# Decision

## D1: Stream A 進行状況

| Signal | State | Verdict |
|---|---|---|
| **Bakshi (BCI counsel)** | Teams `GJ/CE/Legal` channel reply | engaged, reschedule |
| **Nakamura (Stripe-in)** | Silent (top-200 inbox) | needs follow-up |
| **Backblaze B2 billing** | $121.46 May 15 failed | **CRITICAL** |
| **Saiki (MoD context)** | Adjacent thread, not Stream A | informational |
| **lawfirm.etzhayyim.com SPA** | HTTP 200 live | SPA up |
| **lawfirm intakeSubmit XRPC** | timeout | API degraded |
| **sk_live getServiceAuth** | 401 (iter161 と同じ) | auth bug 未解決 |
| **sk_live listInbox** | 200 (Worker-internal M365 app-only) | works |

Bakshi の返信原文 (Teams `バクシ・クナル さんが GJ/CE/Legal で返信しました`):

> 私用で少し立て込んでおりまして、明日のミーティングが難しい状況です。
> 別日でお話しさせていただくことは可能でしょうか。

→ Stream A engagement は alive、ただし鈴木→Bakshi BCI Rule 36
counsel session は再 schedule 必要。

## D2: iter163 action 優先度

1. **B2 billing 解消 (CEO-only, critical, infra-fatal risk)**
2. **Bakshi 再 schedule (Teams 経由, 2-3 slot 提示)**
3. **Nakamura Stripe-in follow-up (revised deadline + escalation option)**
4. sk_live getServiceAuth 401 投資調査は iter164+

優先度根拠:
- B2 は RisingWave 唯一の storage provider (ADR-0048)。suspend で
  vertex_repo_* + PDS commit log + firehose 全断。
- Bakshi engagement window は 1 週間以内に return しないと cold に
  なるため、24h 以内に reschedule 提示が望ましい。
- Nakamura silent は escalation cost が低い (現状 daily ping で十分)。

## D3: Backblaze B2 billing CRITICAL 扱い

`deps.toml [[migrations]] backblaze-b2-billing-failed-2026-05-19`
status="open" severity="critical"。

Blast radius:
- RW MV refresh stalls (SST checkpoint 不可)
- vertex_repo_record / vertex_repo_commit append-only log halts
- AT Protocol PDS reads degrade to in-memory cache only
- All XRPC `com.etzhayyim.apps.*` query methods 500 once cache evicts
- BPMN dispatcher (replicas=0) 無影響
- lawfirm.etzhayyim.com SPA (HTML/SPA only) 無影響

CEO-only action (etzhayyim agent は `[etzhayyim_agent]` 決済=禁止):
1. Backblaze portal に owner credential で login
2. payment method update (expired or declined card)
3. $121.46 settle
4. 次 cycle 2026-06-15 succeed verify

Mitigation if B2 suspends:
- ADR-0048 §incident_2026_04_25 の rate-limit defense で ~24h grace
- `data_refill_levels=0-6` cache settings で SST eviction まで猶予
- Fallback: cold-start RW from Iceberg S3 (R2 mirror, not wired yet)

## D4: sk_live auth bug は iter163 範囲外

`getServiceAuth` 401 は iter161 から再現。listInbox は 200 を返すため
Worker-internal route は健全、user-scoped service auth flow のみ broken。
Stream A 進行に必須でないため iter164+ に deferred。

# Consequences

**Positive**
- Stream A engagement window (Bakshi) を捉えた状態で reschedule 可
- B2 billing CRITICAL を顕在化、ADR-0048 invariant の崩壊予防
- iter144 BPMN extract 後の状態 baseline を確立 (orphan 復元 + probe)

**Negative**
- B2 billing 解消は CEO 手作業必須 (etzhayyim agent 範囲外)
- sk_live auth bug 未解決のまま iter164+ に carry-over
- Nakamura Stripe-in pending が継続 (Stripe-in 完了なしでは Y1
  USD 175K revenue commitment 履行不可)

**Followups (iter164+)**
- B2 billing resolve 後、payment method 変更を `etzhayyim Vault` に記録
- Stripe-in 状態を Nakamura から確証取れたら ADR-2605191500 を
  superseded_by で 後継 ADR にバトン渡し
- sk_live getServiceAuth 401 root cause 調査 (iter161 から carry)

# Alternatives Considered

- **A. B2 billing を放置して Stream A 集客に集中**: B2 suspend で
  全 RW 死、Stream A SPA 以外の全 XRPC 500。**却下**。
- **B. Stream A iter163 で sk_live auth bug も同時調査**: scope 過大、
  iter144 復旧直後の不安定状態で複数変更を混ぜるとロールバック困難。
  **却下** — auth bug は iter164+ に分離。
- **C. Bakshi 待ちで Nakamura ping 後回し**: revenue critical path は
  Stripe-in が gate になっており Bakshi BCI counsel は parallel work
  なので Nakamura ping を停めるとボトルネック増幅。**却下**。

# References

- iter161 (Stream A activation, outbox/13 CEO status)
- iter144 (BPMN extract to etzhayyim-root, ADR-2605181400)
- ADR-0048 (RisingWave Vultr+B2 primary)
- `_working/etzhayyim-revenue/DECISION-LOG.md` iter163
- `_working/etzhayyim-revenue/stream-a-activation-runbook.md`
- `_working/etzhayyim-revenue/outbox/11-13` (Stream A artifacts)
- Backblaze inbox notice 2026-05-19 ($121.46 May 15 due, failed)
- Teams GJ/CE/Legal channel (Bakshi reply)
