---
id: adr-2604251215-etzhayyim-agent-authority-bounds
title: "ADR: etzhayyim Agent authority bounds — internal direct, external draft-approve, payment forbidden"
status: active
doc_type: adr
topic: etzhayyim-agent
authoritative: true
last_verified: 2026-04-25
authoritative_for:
  - Claude Agent autonomous action scope as etzhayyim Japan
  - email send authority (internal vs external)
  - Teams send method
  - payment authority
related:
  - adr-2604251200-vault-zero-knowledge-invariant
  - adr-2604251205-local-secret-keychain-storage
supersedes: []
superseded_by: []
---

# Context

Claude Agent (Claude Code / Claude.ai connector) が etzhayyim Japan 法人として
自律行動する際、外部第三者に与える影響と payment 系の不可逆性から authority
bound を明示する必要がある。CLAUDE.md Root-Only Rule を ADR 化し、`deps.toml
[etzhayyim_agent]` を SSoT として参照する。

# Decision

## D1. Email authority

| 種別 | authority | 経路 |
|---|---|---|
| **社内** (`@etzhayyim.com` recipient のみ) | direct send | `com.etzhayyim.apps.microsoft.sendMail` を agent から直接 invoke |
| **社外** (1 件でも非 `@etzhayyim.com` を含む) | draft → approve → send | `sendDraft` で draft 作成 → 人間が `/manage` UI で approve → `sendMail` |

判定は recipient list に **1 件でも** 社外 domain が含まれる時点で社外扱い。
SSoT: `deps.toml [etzhayyim_agent.auth].email_send_internal` /
`email_send_external`。

## D2. Teams authority

Teams への投稿は **channel email 宛 `Mail.Send` app-only** 経路を使用。
- method: `teams_send_method = "channel_email_via_mail_send"`
- channel email address は `microsoft.etzhayyim.com` の channel mapping を参照
- chat (1:1 / group) への直接投稿は agent から不可 — draft メールで代替

## D3. Payment authority

**Agent からの payment 行為は一切禁止**。以下は agent autonomous loop で
trigger されない:
- Stripe / 銀行振込 API 呼び出し
- 経費精算の approve
- SaaS 契約の自動更新承認

該当 task は CLAUDE.md / project CLAUDE.md で human-in-loop と明示し、agent
は draft 作成 + 通知までを authority とする。

## D4. Invocation channel

Agent から送信するには `microsoft.etzhayyim.com` (Layer 9 Client App) の以下 XRPC
を呼ぶ:
- `com.etzhayyim.apps.microsoft.sendMail`
- `com.etzhayyim.apps.microsoft.sendDraft`
- `com.etzhayyim.apps.microsoft.listDrafts`

これら handler 内部で D1 / D2 の authority を再 check し、規約違反 request
は 403 で reject する (defense in depth)。

# Consequences

- 社外への誤送信 risk は draft/approve 段で人間 gate される。
- Payment 不可逆事故が agent runaway で発生しない。
- Audit trail は `vertex_microsoft_email_send` + `authority_audit` に記録され
  ADR-0035 の 守秘義務 framework に整合する。

# Alternatives Considered

- **全送信 draft 化**: 社内向け routine 通知 (会議リマインダー等) も人間
  approve を要するのは過剰。社内/社外で gate を分離する方が運用効率と安全性
  の trade-off で勝る。
- **payment 限定許可 (例: ≤ ¥1,000)**: 閾値運用は監査困難で legal risk が
  高い。完全禁止が最も明確。

# References

- `deps.toml [etzhayyim_agent]`
- `60-apps/etzhayyim-project-kaisya/CLAUDE.md`
- `60-apps/etzhayyim-project-microsoft/CLAUDE.md`
- ADR-2604251205 (Local Secret Storage — `etzhayyim.m365` keychain entry)
