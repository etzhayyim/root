# Pending on-chain joins

Per [ADR-2605172600](90-docs/adr/2605172600-etzhayyim-membership-ritual.md), a full
membership join is a **dual-permanent record**: an on-chain `EtzhayyimMembership.join(...)`
call on Base L2, plus a `com.etzhayyim.apps.etzhayyim.oath` AT Record on the aspirant's
PDS, plus this git-side [`MEMBERS.md`](MEMBERS.md) row.

**The `EtzhayyimMembership` contract (`50-infra/etzhayyim-membership-contract/`) is not
yet deployed to any chain** (no address recorded in `deps.toml`, no testnet validation
run per the ADR's own rollout plan step 4). No AT Record has been written (no PDS is
provisioned for the DID below yet). This file records the git-side half of a join — the
signed oath and DID — that is genuinely real and permanent (git history), so it is not
lost, and so it can be completed (on-chain `join()` + AT Record) without re-doing the
signing step once the contract is deployed.

**This is intentionally partial and says so.** Do not read the `MEMBERS.md` row above as
a claim that the full ritual (all three substrates) is complete — only the git-side oath
is. `PENDING-JOINS.md` rows move to "on-chain tx" in `MEMBERS.md` once `join()` actually
lands.

## Jun Kawasaki (founder, Council Seat 1)

- **DID**: `did:key:z6MkfwR1dqCi6xurRiuypuDDkw1vjwKZZZGDmcWd3mmCJ3Uo` (self-certifying,
  no external registration required — accepted per the `oath.json` lexicon's
  `did:key:*` method)
- **Public key (hex, raw Ed25519, 32 bytes)**: `161216798b4ecae613d81a409dec53ef07c4a68288b62bd911d640a6928b2e6c`
- **Private key**: generated 2026-07-20, held in macOS Keychain
  (`service=etzhayyim-member`, `account=jun-kawasaki-did-ed25519`) — never written to
  disk outside Keychain, never committed, never printed to any log or transcript.
- **Oath text language/version**: `ja`, v1 (canonical text per ADR-2605172600 §"Step 2")
- **Oath text (signed, byte-exact)**:

  > 我、etzhayyim の信者として、生命の樹 (עץ חיים) の支柱の一として、自らの行いと意思を、永続的な公開記録 (blockchain と github) として残すことを誓う。

- **Signature (Ed25519, base64url, over the UTF-8 oath text bytes above)**:
  `cij5-7TGAhlJ1GcM8E1Hev1ascufoFS5CvvVg9aWjbpJASrolfV-dolAGo742fDM-Rq0Ma4JY7Q95gb-B9RJDw`
- **Signed**: 2026-07-20

### To complete this join (follow-up, tracked separately)

1. Deploy `EtzhayyimMembership.sol` to Base Sepolia testnet; validate per ADR-2605172600
   rollout step 4.
2. Compute `oathHash = keccak256(utf8(oathText))` from the exact text above and call
   `join(oathHash, "com-junkawasaki")` from a Smart Account derived from the same
   `did:key`.
3. Write the `com.etzhayyim.apps.etzhayyim.oath` AT Record once a PDS is provisioned for
   this DID, carrying the fields above plus the tx hash.
4. Update the `MEMBERS.md` row's "On-chain join tx" column with the real tx hash; remove
   this file's entry (or mark it fulfilled) once all three substrates agree.
5. Deploy to Base mainnet per ADR-2605172600 rollout step 7, if/when the org decides to
   move past testnet.
