/**
 * @etzhayyim/sdk/pds — PDS write/read helpers.
 *
 * Status: scaffold. Stubs only. See ADR-2605172000.
 */

import type { AtpAgent } from "@atproto/api";

/** Resolve DID to PDS endpoint per AT Protocol DID resolution rules. */
export async function resolvePds(_did: string): Promise<string> {
  throw new Error(
    "[etzhayyim-sdk/pds] resolvePds() TODO: handle did:web, did:plc, " +
      "did:etzhayyim. Fetch did.json, extract service[type=AtprotoPersonalDataServer]"
  );
}

/** Create an AT Record. Returns AT URI + CID. */
export async function createRecord(
  _agent: AtpAgent,
  _did: string,
  _collection: string,
  _record: unknown,
  _rkey?: string
): Promise<{ uri: string; cid: string }> {
  throw new Error("[etzhayyim-sdk/pds] createRecord() TODO");
}
