/**
 * solvency — checkSolvency + emitSolvencyWarning unit tests.
 *
 * viem mocked at the module boundary: a fake PublicClient with a single
 * `getBalance` method drives the test. We assert on:
 *   - the EOA address derived from the signer key matches viem
 *   - balance >= floor → ok=true, no stderr noise
 *   - balance < floor → ok=false, structured warning line emitted
 */
import {beforeEach, describe, expect, it, vi} from "vitest";

const getBalanceMock = vi.fn<(args: {address: string}) => Promise<bigint>>();
const privateKeyToAccountMock = vi.fn();

vi.mock("viem", () => ({
  createPublicClient: () => ({getBalance: getBalanceMock}),
  http: () => ({}),
}));

vi.mock("viem/accounts", () => ({
  privateKeyToAccount: privateKeyToAccountMock,
}));

const {checkSolvency, emitSolvencyWarning} = await import(
  "../src/solvency.js"
);

const FAKE_SIGNER = "0xabcdef0123456789abcdef0123456789abcdef01" as `0x${string}`;
const FAKE_KEY =
  "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80" as `0x${string}`;

beforeEach(() => {
  getBalanceMock.mockReset();
  privateKeyToAccountMock.mockReset();
  privateKeyToAccountMock.mockReturnValue({address: FAKE_SIGNER});
});

describe("checkSolvency", () => {
  it("returns ok=true when balance >= floor", async () => {
    getBalanceMock.mockResolvedValue(2_000_000_000_000_000_000n); // 2 ETH
    const out = await checkSolvency({
      rpcUrl: "http://localhost:8545",
      signerKey: FAKE_KEY,
      warnBelowWei: 1_000_000_000_000_000_000n, // 1 ETH
    });
    expect(out.signer).toBe(FAKE_SIGNER);
    expect(out.balanceWei).toBe(2_000_000_000_000_000_000n);
    expect(out.ok).toBe(true);
    expect(out.warnBelowWei).toBe(1_000_000_000_000_000_000n);
  });

  it("returns ok=false when balance < floor", async () => {
    getBalanceMock.mockResolvedValue(500_000_000_000_000_000n); // 0.5 ETH
    const out = await checkSolvency({
      rpcUrl: "http://localhost:8545",
      signerKey: FAKE_KEY,
      warnBelowWei: 1_000_000_000_000_000_000n,
    });
    expect(out.ok).toBe(false);
    expect(out.balanceWei).toBe(500_000_000_000_000_000n);
  });

  it("treats exact-equality as ok=true (gte semantics)", async () => {
    getBalanceMock.mockResolvedValue(1_000_000_000_000_000_000n);
    const out = await checkSolvency({
      rpcUrl: "http://localhost:8545",
      signerKey: FAKE_KEY,
      warnBelowWei: 1_000_000_000_000_000_000n,
    });
    expect(out.ok).toBe(true);
  });
});

describe("emitSolvencyWarning", () => {
  it("is a no-op when status.ok is true", () => {
    const errSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    emitSolvencyWarning({
      signer: FAKE_SIGNER,
      balanceWei: 2n,
      ok: true,
      warnBelowWei: 1n,
    });
    expect(errSpy).not.toHaveBeenCalled();
    errSpy.mockRestore();
  });

  it("emits a single structured stderr line when ok=false", () => {
    const errSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    emitSolvencyWarning({
      signer: FAKE_SIGNER,
      balanceWei: 500n,
      ok: false,
      warnBelowWei: 1000n,
    });
    expect(errSpy).toHaveBeenCalledTimes(1);
    const line = errSpy.mock.calls[0][0] as string;
    expect(line).toContain("[anchor-cron] solvency:");
    expect(line).toContain(`signer=${FAKE_SIGNER}`);
    expect(line).toContain("balanceWei=500");
    expect(line).toContain("warnBelowWei=1000");
    expect(line).toContain("action=top-up-required");
    errSpy.mockRestore();
  });
});
