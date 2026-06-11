---
id: adr-2604251210-credential-sharing-vault-bitwarden
title: "ADR: Credential sharing via etzhayyim Vault (primary) + Bitwarden (auxiliary)"
status: active
doc_type: adr
topic: credential-sharing
authoritative: true
last_verified: 2026-04-25
authoritative_for:
  - team-shared API key / credential storage
  - Claude Connector key custody
  - prohibited credential channels
related:
  - adr-2604251200-vault-zero-knowledge-invariant
  - adr-2604251205-local-secret-keychain-storage
supersedes: []
superseded_by: []
---

# Context

ローカル端末の secret は ADR-2604251205 (macOS Keychain) でカバーされる。
複数 member で共有する API key (Anthropic / OpenAI / SaaS) や Claude
Connector の組織キーは、Slack/Teams 添付や Notion 平文化が常態化していた。
本 ADR で共有経路を限定する。

# Decision

## D1. Primary = etzhayyim Vault (`vault.etzhayyim.com`)

メンバー間共有 credential は **etzhayyim Vault** に保存する。Zero-knowledge
invariant (ADR-2604251200) により server breach 耐性を確保。

- 個人 Claude Connector キーは `etzhayyim-claude-connector` フォルダに保存
- Anthropic / OpenAI / SaaS API key は項目別に share 設定 (per-member ECIES)
- CLI: `etzhayyim vault add` / `etzhayyim vault share` / `etzhayyim vault run`

## D2. Auxiliary = Bitwarden

外部 SaaS の login credential (browser password / 2FA seed 等) は Bitwarden
Vault を補助利用。Claude Code MCP integration:
- server: `bitwarden` (`@bitwarden/mcp-server`, stdio transport)
- session: `BW_SESSION` を `etzhayyim.bitwarden` Keychain entry から取得

## D3. Claude.ai org connector

- URL: `https://mcp.etzhayyim.com/mcp`
- 組織共有キー (`sk_live_org_*`) は org connector 設定済み
- 個人キーは etzhayyim Vault `etzhayyim-claude-connector` フォルダ参照

## D4. Forbidden channels

- Slack / Teams / メール本文への raw key 記載 (URL preview / 全文検索 index 化)
- `.env` / `.envrc` の commit (gitleaks pre-commit で gate)
- ソースコード / wrangler.jsonc / dockerfile へのハードコード
- Notion / Google Doc / Confluence の平文添付

# Consequences

- 共有 credential の audit trail が `vault.etzhayyim.com` に集約 (ADR-0010 audit log)。
- Member off-board 時は wrapped key を revoke するだけで該当 member の復号権を
  失効可能。
- Bitwarden は SaaS login のみ — API key は Vault 一元管理で散逸を防ぐ。

# Alternatives Considered

- **AWS Secrets Manager / GCP Secret Manager**: 管理者のみ復号可、zero-
  knowledge ではないため最終的に server breach で全件流出する。却下。
- **Bitwarden を primary に昇格**: org plan は per-seat 課金 + audit log は
  Enterprise tier 限定。zero-knowledge は満たすが etzhayyim Vault の AT Protocol
  native integration (ECIES via `com.etzhayyim.signal.getPrekeyBundle`) を捨てる
  ことになるため、auxiliary に留める。

# References

- `60-apps/etzhayyim-project-vault/CLAUDE.md`
- ADR-2604251200 (Vault Zero-Knowledge Invariant)
- ADR-2604251205 (Local Secret Storage)
- Bitwarden MCP: `@bitwarden/mcp-server`
