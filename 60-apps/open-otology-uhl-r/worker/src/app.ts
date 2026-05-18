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
// P0 MVP: this Worker only exposes the matchQuery surface. P1 will add the
// auditable at:// record emission for every match request (no PII, per
// ADR-2605181040 §PII zero). The audit lexicon
// `jp.etzhayyim.med.uhl.institution.matchAudit` is already declared.

import {
  createWorkerExport,
  nsid,
  parseLexiconInput,
  type LexiconOutput,
} from "@gftd/magatama-host-sdk";

import {
  InvalidInputError,
  NSID_MATCH,
  RegistryUnavailableError,
  handleMatchQuery,
  type MatchInput,
} from "./handler.js";

export default createWorkerExport((sdk) => {
  sdk.app.query(nsid(NSID_MATCH), async (_ctx, body) => {
    const input = parseLexiconInput(NSID_MATCH, body) as unknown as MatchInput;
    try {
      const output = await handleMatchQuery(input);
      return JSON.stringify(output) satisfies string &
        LexiconOutput<typeof NSID_MATCH>;
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
  });
});
