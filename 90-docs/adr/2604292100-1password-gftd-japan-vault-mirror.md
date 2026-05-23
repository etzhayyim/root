---
id: 2604292100-1password-gftd-japan-vault-mirror
title: 1Password "Gftd Japan株式会社" vault as the org-share mirror of gftd.* Keychain credentials
status: active
doc_type: adr
topic: credential-distribution
authoritative: true
last_verified: 2026-04-29
authoritative_for:
  - 1Password vault layout for gftd.* operator credentials
  - keychain → 1Password mirror policy
related:
  - 2604231811-atproto-extension-service-layers
supersedes: []
superseded_by: []
---

# Context

Two existing root rules already define how secrets are handled:

- **Local Secret Storage = macOS Keychain (CRITICAL)** — runtime SSoT for an
  individual operator's gftd.* credentials. Naming: `service=gftd.{provider}`,
  `account={KEY_NAME}`. Synced across the operator's Apple devices via iCloud
  Keychain.
- **Credential Sharing = gftd Vault + Bitwarden (CRITICAL)** — `vault.etzhayyim.com`
  (zero-knowledge, ECIES-shared) is the *runtime* org-share path. Bitwarden
  is the supplementary external-service vault. Slack/Teams/email/code 内の
  raw key 記載は禁止。

The 1Password "Private" account has been used ad-hoc as a long-term backup
for one-off secrets (e.g. `ai-gftd-pds-repo-signing-kek-adr0010` per
`50-infra/.../adr0010`). It has *not* had an authoritative role for the
day-to-day `gftd.{provider}/{KEY_NAME}` set the operator already keeps in
Keychain.

The "Gftd Japan株式会社" 1Password vault (id `dk3qlcuqumtoml2oaxrs5mwiji`)
already contained ~50 `gftd.*/...`-titled items — a partial mirror that grew
organically. As of 2026-04-28 the live Keychain held 9 services × 14 accounts
under `gftd.*`, and the partial mirror diverged: 4 vault items existed as
empty title-only stubs, 10 keychain entries had no vault counterpart at all.

# Decision

Adopt 1Password "Gftd Japan株式会社" (`dk3qlcuqumtoml2oaxrs5mwiji`) as the
**human/operator-facing share view** of every `gftd.*` Generic Password the
operator stores in macOS Keychain.

- **Title convention**: `gftd.<service>/<account>` (matches the existing 50+
  items). One 1Password item per (service, account) pair. Category =
  `PASSWORD`. Single `password` field, exact verbatim copy of the Keychain
  value with the trailing newline (if any) stripped — same policy
  `find-generic-password -w` already applies on read.
- **SSoT precedence is unchanged**:
  - Keychain remains the runtime SSoT for the operator's local environment.
    Scripts and BPMN workers continue to read from Keychain, never from
    1Password.
  - `vault.etzhayyim.com` remains the *workload* org-share path (zero-knowledge,
    ECIES, programmatic access by Workers / pyzeebe).
  - 1Password "Gftd Japan株式会社" is **operator UI only** — readable in
    the desktop app, browser extension, and `op` CLI by Gftd Japan members
    who already have access to that vault. It is not a runtime read source.
- **Mirror direction is one-way (Keychain → 1Password)**. If a value
  changes, update Keychain first; the next mirror run propagates. Do not
  edit the 1Password copy in isolation; it will be overwritten or flagged
  as DIFF by the next sync.
- **Conservative write policy**:
  - new title (no item exists) → CREATE.
  - title exists, value matches → SKIP.
  - title exists, value is the empty string → FILL (treat as a stub).
  - title exists, value differs and is non-empty → REPORT, do not
    overwrite. Operator decides which side is canonical.
- **Verification reads must use `op item get --format=json`**, not
  `op item get --fields password`. The latter CSV-escapes any value that
  contains `"`, `,`, or newlines (every internal `"` becomes `""`, the
  whole value is wrapped in `"..."`). This produces false-negatives for
  JSON-blob credentials like `gftd.identity/junkawasaki.com`. See
  convention `op-item-get-csv-escape-quirk`.

# Consequences

- Org members get a browseable, audit-logged share view of operator
  credentials without giving them shell access to the operator's Mac.
- The runtime hot path is untouched. No Worker / BPMN / pyzeebe primitive
  starts reading from 1Password. ADR-0044 (UDF strategy), ADR-0023
  (Auth 4-Layer), and the **Vault Zero-Knowledge Invariant** continue to
  hold — this ADR adds a *parallel* operator-facing view, not a new
  read path.
- Stale 1Password items become detectable: any DIFF between Keychain and
  1Password is reported by the mirror script, surfacing drift.
- The CSV-escape quirk is now codified — future verification tooling
  cannot silently false-negative on JSON-blob values.

# Alternatives Considered

- **Make 1Password the runtime SSoT instead of Keychain**. Rejected:
  requires `op` CLI on every shell invocation (adds biometric prompts to
  hot paths), conflicts with the existing CRITICAL rule that names
  Keychain as the local SSoT, and would force a session token (`op
  signin`) into BPMN worker pods that currently authenticate via Service
  Auth JWT only.
- **Mirror Keychain into `vault.etzhayyim.com` (gftd Vault) instead**. Rejected:
  gftd Vault is zero-knowledge with ECIES shares; it is the *workload*
  share path (Workers / pyzeebe / browser via WebAuthn PRF). Adding a
  second purpose ("operator UI mirror") would dilute the zero-knowledge
  invariant and force every operator to maintain a member-device key
  just to *read* their own credentials in a GUI.
- **Two-way sync**. Rejected: doubles the failure surface (which side
  wins on conflict?) and there is no operator workflow that needs to
  edit 1Password as the primary write path.

# Coverage as of 2026-04-29

14 (service, account) pairs, 9 services, all live in vault
`dk3qlcuqumtoml2oaxrs5mwiji`:

| Service | Account |
|---|---|
| gftd.b2 | BUCKET_NAME, APPLICATION_KEY_ID, APPLICATION_KEY, ENDPOINT, REGION |
| gftd.civitai | API_KEY |
| gftd.hf | HF_TOKEN |
| gftd.identity | junkawasaki.com |
| gftd.r2 | ACCOUNT_ID |
| gftd.runpod | RUNPOD_API_KEY |
| gftd.rw | ROOT_URL |
| gftd.shiharai.tokyo-waterworks | primary |
| gftd.vultr | VULTR_API_KEY, API_KEY |

10 created, 4 stubs filled (b2/REGION, r2/ACCOUNT_ID, rw/ROOT_URL,
vultr/API_KEY). 14/14 round-trip verified via `--format=json` read,
sha256[:12] + length match.

Other `gftd.*/*` items already in the vault (gftd.cloudflare/*,
gftd.private-chain/*, gftd.safe-owners/*, gftd.m365/*, gftd.bitwarden/*,
gftd.webyubin/*, gftd.ipfs/*, gftd.murakumo.k3s/*, gftd.rego-arbiter/*,
etzhayyim.com/pulumi/*, gftd.linode/*) are **not** in the operator's Keychain
and remain 1Password-only. They are out of scope for the keychain-mirror
policy until added to Keychain.

# References

- `deps.toml [etzhayyim_agent.keychain]` — Keychain SSoT rules and
  registry of currently-stored services.
- `deps.toml [[conventions]] op-item-get-csv-escape-quirk` —
  verification gotcha codified.
- `deps.toml [[migrations]] gftd-keychain-1password-mirror-20260429` —
  mirror operation log entry.
- ADR-2604231811 — AT Protocol 15-Layer Service Taxonomy (places
  `vault.etzhayyim.com` as Layer "Secret Vault").
- Root rule **Vault Zero-Knowledge Invariant (CRITICAL)** in
  `CLAUDE.md`.
