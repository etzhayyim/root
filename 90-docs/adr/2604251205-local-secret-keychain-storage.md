---
id: adr-2604251205-local-secret-keychain-storage
title: "ADR: Local secret storage = macOS Keychain primary, 1Password mirror, with .env fallback"
status: active
doc_type: adr
topic: local-secret-storage
authoritative: true
last_verified: 2026-04-29
authoritative_for:
  - local API key / OAuth token / credential storage
  - keychain naming convention (service / account)
  - 1Password mirror naming convention
  - delegated OAuth refresh flow
related:
  - adr-2604251200-vault-zero-knowledge-invariant
  - adr-2604251210-credential-sharing-vault-bitwarden
supersedes: []
superseded_by: []
---

# Context

開発者ローカル端末で扱う API key / OAuth token / SDK secret は dotfiles や
shell history に流出する事例が多い。CLAUDE.md は当初 Root-Only Rule として
Apple Keychain 必須を規定していたが、登録 service 名や delegated token 自動
更新の手順が散逸している。本 ADR で SSoT 化する。

# Decision

## D1. Storage hierarchy

1. **Primary** = macOS Keychain (`security` コマンド)。iCloud Keychain で
   Apple device 間自動同期。
2. **Mirror / backup** = 1Password `etzhayyim Japan株式会社` vault。Keychain の
   `service/account` を同一値のまま item title `{service}/{account}` に保存する。
   ローカル repo の秘密ファイルは Document item `repo-file/{repo-relative-path}`、
   repo が依存する SSH key は Document item `repo-ssh/{~/.ssh/path}` に保存する。
3. **Fallback** = `~/.etzhayyim/*.env` (chmod 600)。Keychain が利用不能な
   environment (Linux dev box / CI) 専用。
4. **Forbidden** = repo 内 `.env` commit / shell script ハードコード /
   shell history へ secret 値を露出する `op` assignment の手入力。

## D2. Naming convention

```
service = etzhayyim.{provider}
account = {KEY_NAME}
```

登録例:
```bash
security add-generic-password \
  -s "etzhayyim.m365" -a "CLIENT_SECRET" -w "$VALUE" -U
```

読み取り:
```bash
security find-generic-password -s "etzhayyim.m365" -a "CLIENT_SECRET" -w
```

## D3. Registered services (2026-04-25 時点)

| service | accounts |
|---|---|
| `etzhayyim.m365` | `TENANT_ID` / `CLIENT_ID` / `CLIENT_SECRET` / `DELEGATED_REFRESH_TOKEN` |
| `etzhayyim.r2` | `ACCOUNT_ID` / `ACCESS_KEY_ID` / `SECRET_ACCESS_KEY` |
| `etzhayyim.rw` | `ROOT_URL` / `KAISYA_URL` |
| `etzhayyim.bitwarden` | `BW_SESSION` |

正本: `deps.toml [etzhayyim_agent.keychain]`

## D3b. 1Password mirror registry (2026-04-29)

Vault: `etzhayyim Japan株式会社`

Mirrored and hash-verified without printing secret values:

| source | 1Password title convention | count |
|---|---:|---:|
| macOS Keychain `etzhayyim.*` Generic Password | `{service}/{account}` | 54 |
| macOS Keychain legacy `etzhayyim-*` Generic Password | `{service}/{account}` | 7 |
| repo-local secret files | `repo-file/{repo-relative-path}` | 11 |
| repo-dependent SSH keys | `repo-ssh/{~/.ssh/path}` | 2 |

Operational notes:

- `op item create/edit` for Password items must use assignment statements
  (`password[password]=...`) for the concealed password value. The JSON template
  path can create empty `PASSWORD` values with 1Password CLI 2.34.0 and must not
  be used for this import path.
- `op document create/edit <path>` is used for local secret files and SSH keys.
  Stdin-based document creation is unreliable in the Codex PTY environment.
- Empty local files are skipped; at verification time
  `50-infra/vultr/geth-private/.local-secrets/tunnel.token` was empty and was
  not mirrored.

## D4. Loader

`~/.local/outlook-cache/load-credentials.mjs` が全 `etzhayyim.*` service を環境
変数化し process に inject する。Node script はこの loader を `import` する
だけで env を取得可。

## D5. Delegated OAuth auto-refresh

Microsoft Graph (delegated permission) は 90-day refresh token を要する。
`DELEGATED_REFRESH_TOKEN` を Keychain に保存し、
`~/.local/outlook-cache/get-delegated-token.mjs` が refresh を transparent
に実行する。Device code 再認証は token 無効時のみ。

## D6. 2026-04-29 mirror execution record

The 1Password mirror was refreshed with `op` 2.34.0 into vault
`etzhayyim Japan株式会社`. Secret values were not printed; verification compared
hashes only.

Verified groups:

- `etzhayyim.*` Keychain Generic Password entries: 54/54 matched.
- Legacy Keychain Generic Password entries: 7/7 matched
  (`etzhayyim-m365/*`, `etzhayyim-r2/*`, `etzhayyim-rw/ROOT_URL`).
- Repo-local secret files: 11/11 matched as Document items.
- Repo-dependent SSH keys: 2/2 matched as Document items
  (`~/.ssh/id_ed25519`, `~/.ssh/id_ed25519.pub`).

Repo references that were not present in Keychain at verification time were not
created in 1Password. Examples: `etzhayyim.hf/HF_TOKEN`, `etzhayyim.cf/*`,
`etzhayyim.mapillary/ACCESS_TOKEN`, `etzhayyim.murakumo/API_KEY`,
`etzhayyim.copernicus/*`, `etzhayyim.flightoffer/*`.

# Consequences

- ローカル secret が iCloud Keychain で自動同期 → 新マシン setup が `etzhayyim
  init` 1 行で完結。
- Repo / dotfiles に secret が混入しない (gitleaks scan で false positive 0)。
- Linux dev / CI は `~/.etzhayyim/*.env` fallback で同等動作可能。

# Alternatives Considered

- **1Password CLI (`op`) primary**: macOS 以外でも動作するが、local runtime
  loader は Keychain 前提で十分。1Password は company backup / transfer
  mirror とし、runtime loader の primary にはしない。
- **Direnv + .env**: `.env` の commit risk が消えない。fallback に降格。

# References

- `deps.toml [etzhayyim_agent.keychain]`
- `~/.local/outlook-cache/load-credentials.mjs`
- `~/.local/outlook-cache/get-delegated-token.mjs`
- 1Password vault `etzhayyim Japan株式会社` (mirror / backup)
- ADR-2604251200 (Vault ZK — server-side counterpart)
- ADR-2604251210 (Credential Sharing — team-shared counterpart)
