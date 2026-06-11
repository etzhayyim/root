/**
 * Kubo provider tests — unit-level coverage of the dag/import + pin/add
 * round-trip against a mocked `fetch` so the tests run with no Kubo
 * dependency.
 */

import { test } from "node:test";
import assert from "node:assert/strict";

import { __testing } from "./providers/kubo.js";

type FetchArgs = [input: string | URL, init?: RequestInit];

interface MockResponse {
  ok: boolean;
  status?: number;
  text?: string;
  json?: unknown;
}

function installFetch(handler: (...args: FetchArgs) => MockResponse): {
  calls: FetchArgs[];
  restore: () => void;
} {
  const original = globalThis.fetch;
  const calls: FetchArgs[] = [];
  globalThis.fetch = (async (...args: FetchArgs) => {
    calls.push(args);
    const resp = handler(...args);
    return {
      ok: resp.ok,
      status: resp.status ?? (resp.ok ? 200 : 500),
      async text() {
        return resp.text ?? "";
      },
      async json() {
        return resp.json ?? {};
      },
    } as Response;
  }) as typeof fetch;
  return {
    calls,
    restore: () => {
      globalThis.fetch = original;
    },
  };
}

const ROOT_CID =
  "bafyreigh2akiscaildc7obb6q3vbiqd5gukvvr44e7lsdgowf2c5sb6e44";

test("postCarToDagImport parses NDJSON roots[]", async () => {
  const ndjson = [
    JSON.stringify({ Root: { Cid: { "/": ROOT_CID } } }),
    JSON.stringify({ Stats: { BlockCount: 3, BlockBytesCount: 1234 } }),
  ].join("\n");
  const { calls, restore } = installFetch(() => ({ ok: true, text: ndjson }));
  try {
    const roots = await __testing.postCarToDagImport(
      "http://kubo.local:5001",
      new Uint8Array([1, 2, 3]),
    );
    assert.deepEqual(roots, [ROOT_CID]);
    assert.equal(calls.length, 1);
    const [url, init] = calls[0];
    assert.equal(
      url.toString(),
      "http://kubo.local:5001/api/v0/dag/import?pin-roots=true",
    );
    assert.equal(init?.method, "POST");
  } finally {
    restore();
  }
});

test("postCarToDagImport throws when no Root lines parse", async () => {
  const { restore } = installFetch(() => ({
    ok: true,
    text: JSON.stringify({ Stats: {} }),
  }));
  try {
    await assert.rejects(
      __testing.postCarToDagImport("http://kubo.local:5001", new Uint8Array()),
      /no roots/,
    );
  } finally {
    restore();
  }
});

test("postCarToDagImport propagates upstream errors", async () => {
  const { restore } = installFetch(() => ({
    ok: false,
    status: 500,
    text: "boom",
  }));
  try {
    await assert.rejects(
      __testing.postCarToDagImport("http://kubo.local:5001", new Uint8Array()),
      /dag\/import failed: 500/,
    );
  } finally {
    restore();
  }
});

test("pinAddRecursive returns true when CID is in Pins[]", async () => {
  const { calls, restore } = installFetch(() => ({
    ok: true,
    json: { Pins: [ROOT_CID] },
  }));
  try {
    const ok = await __testing.pinAddRecursive(
      "http://kubo.local:5001/",
      ROOT_CID,
    );
    assert.equal(ok, true);
    assert.equal(calls.length, 1);
    const [url] = calls[0];
    assert.equal(
      url.toString(),
      `http://kubo.local:5001/api/v0/pin/add?arg=${encodeURIComponent(ROOT_CID)}&recursive=true`,
    );
  } finally {
    restore();
  }
});

test("pinAddRecursive returns false when CID is missing from Pins[]", async () => {
  const { restore } = installFetch(() => ({
    ok: true,
    json: { Pins: ["bafy-other-cid"] },
  }));
  try {
    const ok = await __testing.pinAddRecursive(
      "http://kubo.local:5001",
      ROOT_CID,
    );
    assert.equal(ok, false);
  } finally {
    restore();
  }
});
