# 80-data/manimani/ — manimani intake (LOCAL, PII tier-3)

> **This directory is gitignored except this README** (`.gitignore`:
> `/80-data/manimani/* ` + `!README.md`). See ADR-2606302038 (manimani CLI +
> secure storage tiers) and ADR-2605291100 §D5 (PII boundary).

`manimani.etzhayyim.com` is the personal knowledge router (「随に / まにまに」).
This folder is its **interim Phase-0 plaintext hot tier** on the owner's machine:
the `bb e7m manimani` CLI writes intake / project / artifact / todo **EAVT datoms**
here as append-only EDN journals while the kotoba `QuadStore` backend is unbuilt.

## Why local-only

`etzhayyim/root` is a **public** repo. manimani intake carries real Gmail / PC
correspondence (subjects, counterparties, legal & tax detail) = **PII tier-3 /
confidential** (ADR-2605181100). Committing it would leak it. So the journals
stay local and are never pushed. The eventual production store replaces this with:

```
local hot tier (this dir, plaintext index)          ← you are here (Phase 0)
   → kotoba QuadStore: EAVT datoms, bodies = SecureVault blobs (XChaCha20-Poly1305,
     CID-over-ciphertext) → IPFS local Kubo block tier
        → kotobase.net  (canonical remote pin — CIPHERTEXT BLOCKS ONLY, cannot read)
           → Backblaze B2 / DataLad (colder archival)
```

kotobase.net is **secure-by-construction**: it only ever holds AEAD ciphertext
addressed by its own hash; the read-cap (symmetric key + nonce) never leaves the
owner's Keychain. Confidentiality is by encryption (暗号化≠忘却), not by trusting
the pin host.

## Files (local, untracked)

| file | contents |
|---|---|
| `intake.journal.edn` | append-only 5-tuple datoms `[e a v tx op]` — intakes, projects, artifacts, todos |

Never commit `*.journal.edn` / `*.datoms.kotoba.edn` from this directory.
