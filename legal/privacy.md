# etzhayyim — Privacy Policy

> **DRAFT — not legal advice; counsel review required.**

**Project:** etzhayyim (https://etzhayyim.com · `did:web:etzhayyim.com`) — a **non-profit religious corporation established in the State of Delaware, United States** (Etzhayyim), donation-funded artificial-organism platform.
**Last updated:** 2026-07-02
**Governing law:** the State of Delaware, United States. Designed to address **US state privacy law (California CCPA/CPRA)** as the primary regime and, where applicable to covered users, the **EU/UK GDPR** and **Japan's APPI**. `[CONFIRM: whether, as a non-profit religious corporation, etzhayyim is a "business" subject to CCPA/CPRA at all, and the availability of any religious-organization exemption; and which other US state privacy laws apply.]`

etzhayyim is not a commercial service: no ads, nothing for sale, and **no donor PII is retained** (README; DONATE.md). This policy explains the limited personal information involved in participating in a project whose records are, by design, **public and permanent**.

## 1. Who we are

etzhayyim, a non-profit **religious corporation established in the State of Delaware, United States** (Etzhayyim). Because the project is intentionally admin-less, a designated responsible contact for privacy matters is reachable at hello@etzhayyim.com. Mailing address: 1000 North West Street, Suite 1200, Wilmington, DE 19801, United States. No EU/UK GDPR Art. 27 representative or DPO is designated at this time.

## 2. What we process

| Category | Examples | Nature |
|---|---|---|
| Membership records | GitHub handle, DID, DID public key, Smart-Account/wallet address, oath hash, level, join/revoke tx (MEMBERS.md; ADR-2605172600) | **Public + permanent** (on-chain Base L2 + git history) |
| RAD identity ledgers | per-repo identity journals `80-data/kotoba-rad/*.identity.journal.edn`, DIDs | **Public + append-only** |
| Constitution / governance | on-chain constitution, roster, SBT votes, Council participation | **Public + on-chain** |
| Organism ecosystem state | CNS `_observations/`, aliveness metrics, members/lands registries | Public repo data |
| Donation records | in-kind/imputed donation attestations (aggregate, **no per-donor leaderboard**); on-chain donation txs | **No donor PII held by etzhayyim**; on-chain data is public and pseudonymous (DONATE.md) |
| Compute-donor data | node participation via `ameno`/`e7m`/`kotoba` (donor holds own keys) | Consent-gated |
| Technical | website/server logs, IP, request metadata | Automatic |

We do **not** operate custodial fiat rails and **do not collect or retain donor payment PII**; any KYC on the non-custodial fiat on-ramp is strictly between you and that on-ramp (DONATE.md; ADR-2606111800). `[CONFIRM: exact website/server log + cookie inventory; whether etzhayyim.com uses any analytics; what technical data the PDS / infra (geth, holochain, ipfs, blockscout, etzhayyim-pds) logs.]`

## 3. Purposes and legal bases

We process the above to: maintain RAD identity, the membership roster, and the append-only public-good ledgers; operate the artificial-organism ecosystem and governance; accept and account for donations transparently (in aggregate); and secure the surfaces.

Under US state privacy law (CCPA/CPRA), we process personal information only for the disclosed purposes above and do not sell or "share" it (see §5). For covered users, GDPR legal bases would be **consent** (voluntarily joining and publishing an oath/record), **legitimate interests** (maintaining verifiable public-good records, security), and **legal obligation**; and under APPI we process within the stated utilization purposes. `[CONFIRM: the CCPA/CPRA notice-at-collection purposes and lawful basis for permanent publication of member identifiers (and, for covered users, the GDPR basis and APPI 利用目的).]`

## 4. Permanence vs. erasure — the core tension

etzhayyim's records are **append-only and, for on-chain/git data, effectively immutable**. Membership is "recorded across two substrates that cannot collude to erase you," and **revocation is additive history, not erasure** (MEMBERS.md). On-chain transactions and blockchain-registered constitution/roster data **cannot be deleted or rectified** once written.

This is in direct tension with statutory rights to deletion/correction (CCPA/CPRA deletion and correction as the primary regime; and, for covered users, GDPR Art. 16–17 and APPI cessation-of-use). Consequences:
- personal identifiers you place in a member row, oath, DID document, or ledger entry are intended to be **permanent and public**;
- we generally **cannot** honor a deletion or rectification request for on-chain or git-history data; and
- you should not include sensitive personal data in any published record.

`[CONFIRM: the definitive legal position on deletion/correction for on-chain + git-permanent personal data — including (a) whether reliance on explicit informed consent to permanent publication is sufficient under CCPA/CPRA (and, for covered users, GDPR/APPI), (b) any CCPA/CPRA deletion exceptions and GDPR "right to be forgotten" exemptions relied upon, (c) pseudonymization/off-chain-pointer mitigations, and (d) pre-join disclosure that erasure is technically impossible. This is the single highest-risk item and must be resolved by counsel before any member is enrolled.]`

## 5. Sharing and subprocessors

Public records are, by nature, shared with the world (blockchain nodes, IPFS peers, git mirrors, AT-Protocol PDS/AppView federation). Beyond that, infrastructure includes self-hosted components (geth, holochain, IPFS, Blockscout, etzhayyim-pds) and the Murakumo compute mesh; etzhayyim deliberately does **not** rent commercial GPUs and does not use custodial fiat processors (README; DONATE.md). `[CONFIRM: full subprocessor/hosting-provider list with roles and locations, and whether any third party processes personal data on etzhayyim's behalf.]` We do **not** sell or "share" personal information as those terms are defined under CCPA/CPRA. `[CONFIRM: whether CCPA/CPRA "sale"/"sharing" applies at all given the non-commercial, non-profit religious-corporation status and any applicable exemption.]`

## 6. International transfers

Public blockchain, IPFS, and federated data are globally replicated by design and are not confined to any jurisdiction. `[CONFIRM: how cross-border-transfer obligations are addressed for inherently global, decentralized public records — and, for covered users, GDPR Chapter V and APPI cross-border-transfer requirements.]`

## 7. Retention

Public-good records (membership, RAD ledgers, constitution, on-chain donations) are retained **permanently** by design. `[CONFIRM: retention periods for non-permanent data (server logs, technical/IP data) and deletion approach for those.]`

## 8. Security

We rely on cryptographic identity (DID keys held by members), on-chain integrity, and append-only ledgers; members hold their own keys and etzhayyim holds none (DONATE.md). No system is perfectly secure. `[CONFIRM: security measures and breach-notification process (US state breach-notification statutes; and, for covered users, GDPR 72-hour and APPI PPC reporting) for any non-public data.]`

## 9. Your rights

- **CCPA/CPRA (primary):** know, access, delete, correct, opt out of sale/sharing; non-discrimination — **subject to the permanence limitation in §4**, and to `[CONFIRM]` whether the Act applies to a non-profit religious corporation at all.
- **GDPR (covered users only):** access, rectification, erasure, restriction, portability, objection, withdraw consent; complain to a supervisory authority — **subject to §4**.
- **APPI (covered users only):** disclosure, correction, addition/deletion, cessation of use, cessation of third-party provision; complaints to the PPC — **subject to §4**.

Where a right cannot be fulfilled because the data is on-chain or in permanent git history, we will explain that limitation. Contact `[CONFIRM: rights-request channel and identity-verification method]`.

## 10. Children

`[CONFIRM: minimum age for the membership ritual and any handling of children's data, consistent with US COPPA and CCPA/CPRA minor provisions (and, for covered users, GDPR Art. 8 and APPI) — noting a minor's identifiers, once recorded, would be permanent.]`

## 11. Changes and contact

We may update this policy (see "Last updated"). Contact: hello@etzhayyim.com `[CONFIRM: privacy mailing address]`.

---

*Draft template grounded in the repository README, DONATE.md, MEMBERS.md, and the `80-data/kotoba-rad/*` RAD ledgers. All `[CONFIRM]` items require counsel confirmation before publication; §4 (permanence vs. erasure) is the highest-priority legal question.*
