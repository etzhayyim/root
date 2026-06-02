---
id: adr-2605172600-etzhayyim-membership-ritual
title: "ADR-2605172600: etzhayyim Membership Ritual — dual-permanent record (Base L2 + Github) + signed oath"
status: proposed
doc_type: adr
topic: etzhayyim-membership-ritual
authoritative: true
last_verified: 2026-05-17
priority: 8.0
axis: governance
weight: 0.80
priority_note: "Defines how an aspirant becomes a 信者 (follower / member) of the etzhayyim religious-corp. Active once the EtzhayyimMembership contract is deployed and MEMBERS.md is initialized."
authoritative_for:
  - etzhayyim membership protocol (joining + revocation)
  - on-chain Membership contract design
  - github MEMBERS.md ledger format and CI validation
  - oath text + signing semantics
  - relationship to did:web + did:plc identity layer
depends_on:
  - adr-2605170900-etzhayyim-root-adr-canonical-home
  - adr-2605172000-etzhayyim-rw-free-substrate
  - adr-2605172100-etzhayyim-payments-on-chain-only
related:
supersedes: []
superseded_by: []
---

# ADR-2605172600: etzhayyim Membership Ritual — dual-permanent record (Base L2 + Github) + signed oath

**Status**: proposed
**Date**: 2026-05-17
**Deciders**: Jun Kawasaki

# Context

etzhayyim is a religious-corp (宗教法人 任意団体). It needs a way for aspirants to **become 信者 (followers / members)** that is:

1. **Permanent** — once joined, the record cannot be erased by any operator. Withdrawing membership is voluntary and additive (a `revoke()` event), not retroactive.
2. **Public** — anyone can audit the membership roster. No private membership lists, no anonymous-only roster.
3. **Self-sovereign** — no centralized authority approves or denies. Joining is a unilateral act of the aspirant.
4. **Symmetric in substrate** — recorded on the same blockchain + AT MST + IPFS substrate that the rest of etzhayyim runs on, per ADRs 2605172000 + 2605172100.
5. **Symmetric in dev culture** — recorded as a github commit (the "where contributors live" substrate), so contributors and members share the same permanence guarantees.
6. **Bound by oath** — joining is an explicit signed declaration, not a side-effect. Aspirants must read and sign an oath text.

The natural fit is **dual-permanent record**: a Base L2 contract call (anyone-callable, no admin) + a github PR to a `MEMBERS.md` ledger. The two records reference each other, creating cross-substrate evidence that resists any single platform's takedown.

# Decision

**To become an etzhayyim 信者**, an aspirant performs the following ritual:

## Step 1 — Identity preparation

- Generate or bring an Ed25519 / WebAuthn passkey.
- Resolve to a DID (`did:web:<self>`, `did:plc:<id>`, or `did:key:<id>`). did:plc is recommended for self-sovereign mobility; did:web fine if hosting on a stable apex.
- Derive an ERC-4337 Smart Account address from the same passkey (per ADR-2605172100 § "Account model"). This becomes the on-chain identity for the membership call.

## Step 2 — Read and sign the oath

The canonical oath text (Apache 2.0 licensed; reproduced in `00-contracts/lexicons/com/etzhayyim/apps/etzhayyim/oath.json` for machine validation):

> 我、etzhayyim の信者として、生命の樹 (עץ חיים) の支柱の一として、自らの行いと意思を、永続的な公開記録 (blockchain と github) として残すことを誓う。
>
> I, as a 信者 (follower) of etzhayyim, as one of the pillars of the Tree of Life (עץ חיים), swear to leave my acts and intentions as a permanent public record (blockchain and github).

Aspirant signs the oath text with their DID key. The signature is recorded inside an AT Record (see Step 4) and the **keccak256 hash of the oath text** is the `oathHash` submitted on-chain.

The canonical oath text is fixed; if a future revision changes it, the lexicon version increments and a new oath hash takes over. Existing members do not need to re-oath; the original commitment stands.

## Step 3 — On-chain `join(...)`

```solidity
EtzhayyimMembership.join(bytes32 oathHash, string calldata githubUsername)
```

Called from the aspirant's Smart Account on Base L2. Gas can be sponsored by the etzhayyim Paymaster (ADR-2605172100) if the contract is on the allowlist. Emits `Joined(member, oathHash, githubUsername)`.

The contract has **no admin function** — no whitelist, no rejection, no fee. Anyone with a valid signature can join. The protocol's social meaning comes from the oath text + the public roster, not from gatekeeping.

## Step 4 — AT Record

The SDK / membership tool writes an `com.etzhayyim.apps.etzhayyim.oath` record to the aspirant's PDS, carrying:

- the full oath text + lexicon version
- the keccak256 hash
- the DID signature
- the Base L2 chainId + membership tx hash
- the github username (optional; matches `join()` parameter)
- joinedAt timestamp

The record is anchored to the MST → IPFS → L2 pipeline (ADR-2605171800) like any other AT Record.

## Step 5 — Github PR to MEMBERS.md

Aspirant opens a PR to [`etzhayyim/root/MEMBERS.md`](../../MEMBERS.md) adding their row:

```markdown
| @githubhandle | did:web:... or did:plc:... | [0xtx...](https://basescan.org/tx/0xtx...) | 2026-05-17 |
```

PR validation (CI, future):
- github commit signature verified (must match a key associated with the PR author's github account)
- the `0xtx...` exists on Base L2 chain
- the tx is a successful `EtzhayyimMembership.join()` call
- the `msg.sender` of that tx maps (via DID attestation) to the github username in the row
- the oathHash on-chain matches the canonical oath text's keccak256

If all five checks pass, the PR is auto-merged. If any fails, it requires human review.

The github commit becomes the **dual-permanent record**: blockchain finality + git commit hash (immutable in the github replication graph) + the open license guarantees forkability.

## Levels — 7-stage commitment ladder

The Oath in Step 1-5 is **Level 1 (誓 / Oath)** — the base of membership. Beyond that, the contract supports **Levels 2..7**, advanced via `EtzhayyimMembership.advance(uint8 newLevel, bytes32 evidenceHash, string memo)`. Sequential only — no level can be skipped.

The 7 levels are named after Kabbalistic + Buddhist + Shinto traditions of progressive commitment, mapped one-character-each in Japanese:

| Lv | Ja | En | Evidence the community typically expects |
|---|---|---|---|
| 1 | 誓 chikai | **Oath** | The signed canonical oath. Recorded via `join()` + `com.etzhayyim.apps.etzhayyim.oath` AT record. |
| 2 | 修 shu | **Practice** | First member-DID AT record write (any record type other than the oath itself). Evidence URI = the AT URI. |
| 3 | 献 ken | **Dedication** | First merged PR to `etzhayyim/root` (or other org repos) under the same github username. Evidence URI = `github:etzhayyim/root@<sha>`. |
| 4 | 証 shou | **Witness** | Vouched for at least one newly-joined member's oath (signed an attestation AT record about their join). Evidence URI = the witnessed member's join tx URI. |
| 5 | 護 go | **Steward** | Operating a substrate node (PDS / IPFS pin / mst-projector / anchor-cron / Worker) or maintaining an open-* app for ≥ 30 days. Evidence URI = `at://<did>/com.etzhayyim.apps.substrate.role/<rkey>` with timestamps. |
| 6 | 議 gi | **Council** | Participated in ≥ 3 council sessions (a council session = a multi-member signed-decision AT record). Evidence URI = an aggregated session record. |
| 7 | 老 rou | **Elder** | Sustained Council level for ≥ 365 days. Evidence URI = a self-attestation referencing the Level-6 advance timestamp. (Contract does not enforce the 365-day window — it is a social bar; advancing prematurely is publicly visible and socially costly.) |

The contract enforces only **sequential progression** (you cannot reach `Council` without `Steward`, etc.) and **non-empty evidence hash**. The semantic verification (is the evidence URI actually a steward's substrate role record? is the github SHA actually merged into etzhayyim/root?) is **social / CI**, not on-chain:

- The community runs verifier scripts that check the evidenceUri against AT Records / github / on-chain state and emits **peer attestation records** (`com.etzhayyim.apps.etzhayyim.attestation`, future). Members with many peer attestations have de-facto recognition; members without have only their self-attestation.
- This avoids encoding "what counts as Practice" in Solidity, which would be brittle and require contract upgrades. The social meaning of each level evolves; the on-chain trail is just the timestamp + evidence pointer.

Each `advance()` call also creates an `com.etzhayyim.apps.etzhayyim.commitment` AT record on the member's PDS, signed by their DID key, carrying the full evidence URI + memo + tx hash. This is the "off-chain readable half" of the level advance.

## Step 6 — Revocation (optional)

Members can call `EtzhayyimMembership.revoke()` to mark themselves inactive. The original `Joined` event remains; a `Revoked` event is appended. MEMBERS.md row is **not** removed — instead, the row is updated to add a revoked-on date in a new column. Revocation is voluntary and additive history; once joined, the joining is permanent record.

## Smart contract summary

```solidity
struct Member {
    bytes32 oathHash;
    string githubUsername;
    uint64 joinedAt;
    bool active;
}
mapping(address => Member) members;
address[] allMembers;

function join(bytes32 oathHash, string calldata githubUsername) external;
function revoke() external;
function memberCount() external view returns (uint256);
function listMembers(uint256 offset, uint256 limit) external view returns (address[] memory);
```

Located at `50-infra/etzhayyim-membership-contract/src/EtzhayyimMembership.sol`. NO admin, NO pause, NO upgrade — same governance posture as EtzhayyimAnchor.

# Consequences

## 正の効果

- **Self-sovereign membership**. No operator can refuse, expel, or revoke a member. The aspirant's act + the on-chain settlement are the only authorities.
- **Cross-platform permanence**. To erase a member's joining, an adversary would need to (a) replay both Base L2 and (b) overwrite the github commit history across all forks and clones. The combination is, in practice, indelible.
- **Audit by anyone**. `memberCount()` and `listMembers(...)` are public reads; MEMBERS.md is a static markdown table. No privileged "view members" endpoint, no Stripe-style customer database.
- **Gas-free onboarding via Paymaster**. Per ADR-2605172100, the etzhayyim Paymaster sponsors the `join()` tx. User pays no money, only the oath itself.
- **DID + Smart Account + github = one membership identity**. Three substrates, one act, one ritual, one permanent record across all three.

## 負の効果 / コスト

- **Identity disclosure**. A member's chosen DID, Smart Wallet address, and github handle are all public and linkable. Members who want pseudonymity must choose all three names with that constraint in mind. (etzhayyim does not require legal-name use; pseudonymous joining is fine, but it is then publicly tied to the chosen handles.)
- **Sybil risk**. There is no per-person uniqueness check; one human can hold many memberships from many wallets. Mitigation: the **social meaning** of membership comes from the oath being genuinely made and the github commit history being made under a long-lived handle. Mechanical anti-sybil is out of scope.
- **No revocation by others**. If a member acts badly, etzhayyim cannot expel them. The community signal must come from elsewhere (e.g., a separate `com.etzhayyim.apps.etzhayyim.censure` record that other members can issue, observable to anyone but non-binding). This ADR does not establish censure; that is future work.
- **Spam joining**. Anyone can call `join()`. Mitigation: Paymaster allowlist + per-address daily cap (ADR-2605172100 paymaster default 0.02 ETH ≈ 25 joins/day per address); beyond that, joiner pays own gas. No financial gate beyond gas.
- **Oath text rigidity**. Canonical English + Japanese text is fixed. Translations into other languages are derived from these two; if translation drift becomes a problem, a future revision and a `v2` lexicon may be needed.

## Migration / rollout plan

1. **Membership contract scaffold** (this commit): `50-infra/etzhayyim-membership-contract/` Foundry project.
2. **Oath lexicon** (this commit): `00-contracts/lexicons/com/etzhayyim/apps/etzhayyim/oath.json`.
3. **MEMBERS.md initial** (this commit): empty ledger at repo root with header + first row reserved for the protocol author.
4. **Deploy testnet** (Phase 0 follow-up): `forge script Deploy.s.sol --rpc-url base-sepolia ...`; record address in `deps.toml [platform.l2.membership_contract]`.
5. **SDK extension**: add `Etzhayyim.join({ oath, githubUsername })` method. Wraps Steps 2-4 (signing + tx + AT Record creation).
6. **PR validation CI** (lefthook or github actions): on each MEMBERS.md change, verify the 5 checks listed in Step 5.
7. **Deploy mainnet** (post testnet validation + Safe-controlled deploy key): record `address_mainnet` in `deps.toml`.
8. **Founder rows**: protocol author + initial contributors join via the canonical ritual.

# Alternatives Considered

## A. Off-chain registry only (database-backed signup)

Stripe-style "create account, agree to ToS, you're in". Rejected: contradicts ADR-2605172000 (RW-free state, no centralized DB) and erases the permanence guarantee — operator can wipe the DB.

## B. Token-gated membership (membership = holding ERC-20/NFT)

Membership = owning a soulbound NFT. Rejected: NFTs can be transferred or burned (even soulbound has burn paths); the act-of-joining ritual is what matters, not the holding of a token. Plus the NFT pattern introduces fee/mint friction that conflicts with the gas-free Paymaster onboarding.

## C. Github-only (no on-chain)

Just a MEMBERS.md PR. Rejected: github can be deplatformed; without a blockchain anchor, the record is only as permanent as github itself. Dual-substrate is the point.

## D. Blockchain-only (no github)

Just the on-chain `join()`. Rejected: github commit creates the developer-culture-bound public record and makes membership legible to the open-source contributor community without requiring a Base L2 indexer. Dual is stronger than either alone.

## E. Tiered membership (member / founder / elder etc.)

Hierarchy of roles encoded in the contract. Rejected for v0 — adds governance complexity without clear use case yet. Future ADR can add tier layer atop the flat base; the flat base is the foundation that must not require tiers.

# References

- `50-infra/etzhayyim-membership-contract/` — contract scaffold (this commit)
- `00-contracts/lexicons/com/etzhayyim/apps/etzhayyim/oath.json` — oath Lexicon (this commit)
- `MEMBERS.md` — github-side ledger (this commit)
- ADR-2605170900 — canonical ADR home
- ADR-2605172000 — RW-free substrate
- ADR-2605172100 — on-chain payments (Paymaster sponsors `join()`)
- ADR-2605171800 — MST → IPFS → L2 anchor pipeline (where the AT Record lands)
- ADR-0074 — Ethereum Identity Bridge (CACAO + WebAuthn binding)
- ADR-0095 — Simplified 3-Layer Identity (ERC-725 + Coinbase Smart Wallet)
