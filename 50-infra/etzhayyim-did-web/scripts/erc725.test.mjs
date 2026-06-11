// erc725 chain-mirror unit tests (ADR-2606015200): keccak256 known vectors,
// dweb-handle node derivation, and the active-key → verificationMethod mapping.
// The eth_call itself is best-effort/gated (no live contract) so it isn't tested.
//   node --experimental-strip-types --test scripts/erc725.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import { keccak256, dwebHandleNode, activeKeyToVm } from "../src/erc725.ts";

const hex = (b) => [...b].map((x) => x.toString(16).padStart(2, "0")).join("");

test("keccak256 matches known vectors", () => {
  assert.equal(hex(keccak256(new Uint8Array(0))), "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470");
  assert.equal(hex(keccak256(new TextEncoder().encode("abc"))), "4e03657aea45a94fc7d47ba826c8d667c0d1e6e33a64a036ec44f58fa12d6c45");
});

test("dwebHandleNode is keccak256(<handle>.etzhayyim.com)", () => {
  const got = dwebHandleNode("tsumugi");
  const want = "0x" + hex(keccak256(new TextEncoder().encode("tsumugi.etzhayyim.com")));
  assert.equal(got, want);
  assert.match(got, /^0x[0-9a-f]{64}$/);
});

test("activeKeyToVm: zero key → [], real key → one secp256k1 vm", () => {
  const did = "did:web:etzhayyim.com:actor:tsumugi";
  assert.equal(activeKeyToVm(did, "0xabc", "0x0").length, 0);
  assert.equal(activeKeyToVm(did, "0xabc", "0x").length, 0);
  const vm = activeKeyToVm(did, "0xCONTRACT", "0x02aabbccdd");
  assert.equal(vm.length, 1);
  assert.equal(vm[0].type, "EcdsaSecp256k1VerificationKey2019");
  assert.equal(vm[0].controller, did);
  assert.match(String(vm[0].chainRef), /^did:erc725:base:/);
});
