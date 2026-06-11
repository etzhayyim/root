// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 etzhayyim. Licensed under Apache 2.0 — see LICENSE at repo root.
//
// open-otology-uhl-r — XRPC AppView for the uhl-right-neural Pregel langserver.
//
// Single XRPC method:
//   jp.etzhayyim.med.uhl.institution.matchQuery (query)
//     in:  { substrateClass, localeCountry, dfnb9Confirmed?, topN? }
//     out: { substrateClass, candidates[], requiresHumanReview: true,
//            ethicsCommitteeRequired: true, dataExportRequiresReview: true }
//
// Wraps the langserver at lg-uhl-right-neural.mitama-udf.svc:8080.
// Lexicon contract: 00-contracts/lexicons/jp/etzhayyim/med/uhl/institution/matchQuery.json
//
// `jp.etzhayyim.med.uhl.institution.matchAudit` is already declared.

import {
  createWorkerExport,
  nsid,
  parseLexiconInput,
} from "@etzhayyim/kotodama-host-sdk";
import { getAgent, createRecord } from "@etzhayyim/sdk/pds";

import {
  InvalidInputError,
  NSID_MATCH,
  NSID_AUDIT,
  RegistryUnavailableError,
  handleMatchQuery,
  type MatchInput,
} from "./handler.js";

export default createWorkerExport((sdk) => {
  sdk.app.query(nsid(NSID_MATCH), async (ctx, body) => {
    const input = parseLexiconInput(NSID_MATCH, body) as unknown as MatchInput;

    let result;
    try {
      result = await handleMatchQuery(input);
    } catch (err) {
      if (
        err instanceof InvalidInputError ||
        err instanceof RegistryUnavailableError
      ) {
        throw err;
      }
      throw new RegistryUnavailableError(
        `${(err as Error).message ?? "unknown langserver error"}`,
      );
    }

    // P1: Emit audit record (no PII)
    const pdsHandle = ctx.env.ETZ_PDS_HANDLE as string | undefined;
    const pdsPassword = ctx.env.ETZ_PDS_PASSWORD as string | undefined;
    const pdsDid = ctx.env.ETZ_PDS_DID as string | undefined;
    if (pdsHandle && pdsPassword && pdsDid) {
      try {
        const agent = await getAgent({ handle: pdsHandle, password: pdsPassword });
        await createRecord(agent, pdsDid, NSID_AUDIT, {
          substrateClass: input.substrateClass,
          localeCountry: input.localeCountry,
          dfnb9Confirmed: input.dfnb9Confirmed ?? false,
          candidateCount: result.candidates.length,
          timestamp: new Date().toISOString()
        });
      } catch (e) {
        console.error("Failed to emit audit record:", e);
      }
    }

    return JSON.stringify(result);
  });
});
