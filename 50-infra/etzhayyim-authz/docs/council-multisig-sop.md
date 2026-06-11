# Council Multisig SOP — etzhayyim authz root provisioning

**Status**: Phase α operational guide
**Audience**: Council bootstrap members (5 seats per ADR-2605192300)
**Authority**: ADR-2605212030 §D3 (cutover phases), ADR-2605192300 (Council)
**Tool**: Safe (https://app.safe.global) on Base Sepolia / Base mainnet

## Overview

EtzhayyimAuthz is owner-controlled. The owner is the Council 5-of-7 Safe. Three owner-only operations exist:

| Operation | When to use | Quorum |
|---|---|---|
| `provisionRoot(dwebHandleHash, activeKey)` | greenfield: a new actor (no vendor history) opts into etzhayyim identity | 5-of-7 |
| `mirrorVendorRoot(dwebHandleHash, newActiveKey, predecessorVendorRootHash, predecessorVendorAddr)` | Phase P2: existing vendor-issued root migrates to etzhayyim | 5-of-7 |
| `deactivateRoot(rootId)` | breakage / lost key / legal request — root must stop being accepted | 5-of-7 |
| `setOwner(newSafe)` | Council key rotation or upgrade to a new multisig | 5-of-7 (governance event) |

`rotateKey(rootId, newKey, sigOldKey)` is **not** owner-gated — the active-key holder rotates their own key.

## Standard provisioning flow (greenfield, `provisionRoot`)

1. **Off-chain validation**.
   - Verify the requested `dwebHandle` is policy-compliant (no impersonation, no reserved names, complies with naming policy).
   - Verify the supplied `activeKey` (0x-address) is reachable / controlled by the requesting actor (e.g. by asking the actor to sign a randomly issued challenge with that key out-of-band).
2. **Compute inputs**:
   ```bash
   DWEB_HASH=$(cast keccak "alice.etzhayyim.com")           # 0x-prefixed bytes32
   ACTIVE_KEY=0x...                                          # actor's signing address
   AUTHZ=<deployed EtzhayyimAuthz address>
   ```
3. **Propose the tx in Safe UI**.
   - Open https://app.safe.global → Council Safe (on the target chain).
   - "New transaction" → "Contract interaction".
   - Contract address: `$AUTHZ`.
   - ABI: paste from `out/EtzhayyimAuthz.sol/EtzhayyimAuthz.json`'s `abi` array.
   - Method: `provisionRoot`.
   - `dwebHandleHash` = `$DWEB_HASH`.
   - `activeKey` = `$ACTIVE_KEY`.
   - "Simulate" and confirm the function returns a non-zero rootId.
4. **Collect 5-of-7 signatures**. Each Council member signs in the Safe UI. Tracked via the Safe transaction history; an email / Signal ping per signer is acceptable for nudging.
5. **Execute**. Any signer (including the 5th) can press "Execute" once threshold is met. Pays gas — gas cost is reimbursable to the executor from the etzhayyim treasury (record txHash in the monthly treasury report).
6. **Read back the rootId** from the `RootProvisioned` event in the tx receipt.
7. **Record** in the etzhayyim authz off-chain registry (KV / D1 / postgres replica — TBD by the XRPC handler implementation): `dwebHandle → rootId → activeKey → block`.
8. **Notify the actor** with both DID forms:
   - `did:web:<dwebHandle>` (public-facing)
   - `did:erc725:base:<authz-address>#<rootIdHex>` (cryptographic root)

## Vendor mirror flow (`mirrorVendorRoot`, Phase P2)

Existing vendor-issued root (`did:erc725:etzhayyim:260425:0x...`) → new etzhayyim root.

Additional pre-flight on top of greenfield:

1. **Verify the continuity proof off-chain**.
   - Vendor key signs:
     `keccak256("etzhayyim-vendor-continuity" || vendorRootDid || dwebHandleHash || newActiveKey)`
   - Recover the signer address from the signature; it must equal the known `predecessorVendorAddr` (= the vendor key publicly associated with the vendor root).
   - Tool: `cast wallet verify --address $VENDOR_ADDR <message> <signature>`.

2. **Verify the vendor root is real**.
   - Query vendor authz: `etzhayyim authz get-root --did $VENDOR_ROOT_DID` (or equivalent).
   - Confirm the vendor root is *active* and that `vendorAddr` is the current signer per vendor records.

3. **Compute inputs**:
   ```bash
   VENDOR_ROOT_HASH=$(cast keccak "did:erc725:etzhayyim:260425:0xVENDORROOTID")
   ```

4. **Proceed with Safe-proposed `mirrorVendorRoot(dwebHandleHash, newActiveKey, $VENDOR_ROOT_HASH, $VENDOR_ADDR)`** as in greenfield steps 3–8.

5. **Notify vendor** to mark `predecessorVendorRootHash`'s vendor-side record as "mirrored to etzhayyim — read-only" so vendor stops accepting key rotations on the legacy root.

## Deactivation flow (`deactivateRoot`)

Triggers (any one):
- Actor reports lost/compromised key and cannot rotate (no longer has the old key to sign rotation digest).
- Charter Compliance Council attestation revokes the actor's adherent status, and policy says revoked actors lose their DID.
- Legal subpoena / court order (extreme rare case; transparent on-chain).

Procedure:
1. **Document the trigger** in an etzhayyim audit AT Record (`com.etzhayyim.apps.etzhayyim.authzDeactivationRequest`).
2. **Propose `deactivateRoot(rootId)` in Safe**, 5-of-7 threshold.
3. **Execute**.
4. **Record** in the off-chain registry: actor's status = `deactivated`, with reason + timestamp + tx hash.

**Deactivation is irreversible.** To rebind the same `dwebHandle` after deactivation, the actor must request a new root via `provisionRoot` — they will receive a new rootId.

## Council ownership rotation (`setOwner`)

Rare (once per Council generation change, or in response to Safe compromise).

1. **Deploy and provision the new Safe** (5-of-7 with new signer set) on the target chain.
2. **Verify the new Safe**:
   - signer addresses match the new Council roster (COUNCIL.md).
   - threshold = 5.
   - module / guard configuration matches the prior Safe (or document any diff).
3. **Propose `setOwner(newSafe)`** from the current Safe, 5-of-7.
4. **Execute**. After execution the old Safe loses all authz authority.
5. **Update SSoT pointers** — `deps.toml`, README, all SDKs that hard-code the current Safe address.

## Daily / weekly cadence

- **Daily**: any signer monitors the Safe transaction queue. SLA for response: 24h on weekdays, 72h on weekends.
- **Weekly**: Council secretary publishes a tx digest in the weekly Council notes — list of executed authz txs + pending queue.
- **Monthly**: treasury reconciliation — total gas paid by Council members for executions, reimbursable from etzhayyim Public Fund.

## Security notes

- **Never** add a `mirrorVendorRoot` proposal without verifying the continuity proof off-chain. The contract does NOT verify the proof signature — the Safe is the authority. A bad proposal = a forged vendor migration.
- **Always** simulate the tx before signing — verify `dwebHandleHash` is what you expected (it's a hash; copy-paste errors are silent).
- **Two-factor in Safe** — each signer should use a hardware wallet (Ledger / Trezor) or a passkey-bound smart wallet for their Safe signer key.
- **Quorum can vote against a proposal** — if a Council member sees a proposal they believe is non-compliant (impersonation, non-policy handle, suspect vendor proof), do not sign and surface the concern to the rest of Council.
