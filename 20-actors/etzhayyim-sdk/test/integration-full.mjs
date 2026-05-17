// End-to-end integration smoke for the kisha+goji SDK against Anvil.
//
// Exercises the full PR-#1..#9 surface:
//   1. _baseJoin against EtzhayyimMembership (Stage 1 of bi.join)
//   2. AdherentRegistry.join via officer (manual; mirrors the eventual
//      officer-relayer call inside cfg.officerRelayer)
//   3. AdherentRegistry.attest → isActive true
//   4. bi.propose (uses SDK encoding of Constitution.setMutable)
//   5. bi.vote
//   6. bi.proposalState across the lifecycle (Active → Succeeded →
//      Queued → Executed)
//   7. Confirm Constitution.getMutable reflects the new value
//
// Prereqs:
//   - anvil running on :8545 with the standard 10 test accounts
//   - Deploy.runInternal already broadcast (addresses below)
//   - EtzhayyimMembership deployed (address below)
//   - Constitution.bindGovernance(governance) already called
//
// Usage:
//   cd 20-actors/etzhayyim-sdk && pnpm build && node test/integration-full.mjs

import {createPublicClient, createWalletClient, http, keccak256, toHex} from "viem";
import {privateKeyToAccount} from "viem/accounts";

import {
  CONSTITUTION_ABI,
  ADHERENT_REGISTRY_ABI,
  ETZHAYYIM_MEMBERSHIP_ABI,
  GOVERNANCE_ABI,
} from "../dist/abi.js";
import {join, propose, vote, proposalState} from "../dist/bi.js";

const RPC = "http://localhost:8545";

// Deployed addresses (from forge script output, kept inline so the
// script self-describes its dependencies).
const ADDR = {
  Constitution: "0x5FbDB2315678afecb367f032d93F642f64180aa3",
  AdherentRegistry: "0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512",
  KishaStream: "0x9fE46736679d2D9a65F0992F2272dE9f3c7fa6e0",
  Phenotype: "0xCf7Ed3AccA5a467e9e704C703E8D87F634fB0Fc9",
  AnchorBridge: "0xDc64a140Aa3E981100a9becA4E685f962f0cF6C9",
  Governance: "0x5FC8d32690cc91D4c39d9d3abcBD16989F875707",
  TreasuryMirror: "0x0165878A594ca255338adfa4d48449f69242Eb8F",
  CorpusRegistry: "0xa513E6E4b8f2a923D98304ec87F64353C4D5C853",
  HoldingAttestation: "0x2279B7A0a67DB372996a5FaB50D91eAA73d2eBe6",
  EtzhayyimMembership: "0x610178dA211FEF7D417bC0e6FeD39F05609AD788",
};

// Anvil default account #0 — the founder officer for this run.
const OFFICER_PK = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80";
const officer = privateKeyToAccount(OFFICER_PK);

const transport = http(RPC);
const wallet = createWalletClient({account: officer, transport});
const pub = createPublicClient({transport});

const oathText =
  "我、etzhayyim の信者として、生命の樹 (עץ חיים) の支柱の一として、自らの行いと意思を、永続的な公開記録 (blockchain と github) として残すことを誓う。";
const oathHash = keccak256(new TextEncoder().encode(oathText));

const cfg = {
  privateRpcUrl: RPC,
  baseRpcUrl: RPC,
  constitutionAddress: ADDR.Constitution,
  registryAddress: ADDR.AdherentRegistry,
  kishaStreamAddress: ADDR.KishaStream,
  membershipAddress: ADDR.EtzhayyimMembership,
  baseWalletClient: wallet,
  privateWalletClient: wallet,
};

const log = (...args) => console.log("•", ...args);
const fail = (msg, ctx) => {
  console.error("✘", msg, ctx ?? "");
  process.exit(1);
};

// ─── Step 1: bi.join (Stage 1 only — no PDS agent so fullyEnrolled=false) ───
log("Step 1 — bi.join Stage 1 (Base EtzhayyimMembership.join)");
const joinResult = await join(
  {
    did: "did:web:officer1.etzhayyim.com",
    holder: officer.address,
    oathHash,
    githubUsername: "officer1",
  },
  cfg
);
log("  membershipTxHash:", joinResult.membershipTxHash);
log("  fullyEnrolled:   ", joinResult.fullyEnrolled, "(expected false — no pdsAgent / officerRelayer wired)");
if (joinResult.fullyEnrolled !== false) fail("expected fullyEnrolled=false (no PDS / relayer wired)");

// Verify the Joined event landed on Membership.
const member = await pub.readContract({
  address: ADDR.EtzhayyimMembership,
  abi: ETZHAYYIM_MEMBERSHIP_ABI,
  functionName: "members",
  args: [officer.address],
});
log("  members[officer1] level =", Number(member[4]), "(expected 1)");
if (Number(member[4]) !== 1) fail("Membership level != 1", member);

// ─── Step 2: AdherentRegistry.join (manual officer mint) ───
log("Step 2 — AdherentRegistry.join (officer self-mint, mirrors officerRelayer)");
const adherentTx = await wallet.writeContract({
  account: officer,
  chain: null,
  address: ADDR.AdherentRegistry,
  abi: ADHERENT_REGISTRY_ABI,
  functionName: "join",
  args: [officer.address, "did:web:officer1.etzhayyim.com", oathHash],
});
await pub.waitForTransactionReceipt({hash: adherentTx});
const tokenId = await pub.readContract({
  address: ADDR.AdherentRegistry,
  abi: ADHERENT_REGISTRY_ABI,
  functionName: "tokenOf",
  args: [officer.address],
});
log("  tokenId:", tokenId, "(expected 1)");
if (tokenId !== 1n) fail("tokenId != 1", tokenId);

// ─── Step 3: attest → isActive true ───
log("Step 3 — AdherentRegistry.attest");
const attestTx = await wallet.writeContract({
  account: officer,
  chain: null,
  address: ADDR.AdherentRegistry,
  abi: ADHERENT_REGISTRY_ABI,
  functionName: "attest",
  args: [tokenId, keccak256(new TextEncoder().encode("prayer")), "0x" + "00".repeat(32)],
});
await pub.waitForTransactionReceipt({hash: attestTx});
const isActive = await pub.readContract({
  address: ADDR.AdherentRegistry,
  abi: ADHERENT_REGISTRY_ABI,
  functionName: "isActive",
  args: [tokenId, 30n * 86400n],
});
log("  isActive:", isActive, "(expected true)");
if (!isActive) fail("isActive false");

// ─── Step 4: bi.propose ───
log("Step 4 — bi.propose: kisha_base_rate 1 USDC/day → 2 USDC/day");
const proposalId = await propose(
  {
    change: "kisha_base_rate",
    from: 1_000_000n,
    to: 2_000_000n,
    rationale: "raise kisha to 2 USDC/day",
  },
  cfg
);
log("  proposalId:", proposalId);

// ─── Step 5: bi.proposalState (Active) ───
let state = await proposalState(proposalId, cfg);
log("  state after propose:", state, "(expected Active)");
if (state !== "Active") fail("expected Active");

// ─── Step 6: bi.vote ───
log("Step 6 — bi.vote for");
await vote(proposalId, "for", cfg);

// Roll past voting period (3 days)
log("  evm_increaseTime +3 days + 1");
await fetch(RPC, {
  method: "POST",
  headers: {"Content-Type": "application/json"},
  body: JSON.stringify({jsonrpc: "2.0", method: "evm_increaseTime", params: [3 * 86400 + 1], id: 1}),
});
await fetch(RPC, {
  method: "POST",
  headers: {"Content-Type": "application/json"},
  body: JSON.stringify({jsonrpc: "2.0", method: "evm_mine", params: [], id: 1}),
});

state = await proposalState(proposalId, cfg);
log("  state after vote+warp:", state, "(expected Succeeded)");
if (state !== "Succeeded") fail("expected Succeeded", state);

// ─── Step 7: queue + warp timelock + execute ───
log("Step 7 — queue, warp 72h, execute");
await wallet.writeContract({
  account: officer,
  chain: null,
  address: ADDR.Governance,
  abi: GOVERNANCE_ABI,
  functionName: "queue",
  args: [proposalId],
});
state = await proposalState(proposalId, cfg);
log("  state after queue:", state, "(expected Queued)");
if (state !== "Queued") fail("expected Queued");

await fetch(RPC, {
  method: "POST",
  headers: {"Content-Type": "application/json"},
  body: JSON.stringify({jsonrpc: "2.0", method: "evm_increaseTime", params: [72 * 3600 + 1], id: 1}),
});
await fetch(RPC, {
  method: "POST",
  headers: {"Content-Type": "application/json"},
  body: JSON.stringify({jsonrpc: "2.0", method: "evm_mine", params: [], id: 1}),
});

await wallet.writeContract({
  account: officer,
  chain: null,
  address: ADDR.Governance,
  abi: GOVERNANCE_ABI,
  functionName: "execute",
  args: [proposalId],
  value: 0n,
});
state = await proposalState(proposalId, cfg);
log("  state after execute:", state, "(expected Executed)");
if (state !== "Executed") fail("expected Executed");

// ─── Step 8: Constitution.getMutable confirms the change landed ───
log("Step 8 — verify Constitution.getMutable(\"kisha_base_rate\")");
const newRate = await pub.readContract({
  address: ADDR.Constitution,
  abi: CONSTITUTION_ABI,
  functionName: "getMutable",
  args: [keccak256(new TextEncoder().encode("kisha_base_rate"))],
});
const newRateBigInt = BigInt(newRate);
log("  new rate (bytes32 as bigint):", newRateBigInt, "(expected 2000000)");
if (newRateBigInt !== 2_000_000n) fail("setMutable did not land", newRateBigInt);

console.log("\n✓ e2e PASS — full bi flow (join + propose + vote + queue + execute) lands on-chain");
