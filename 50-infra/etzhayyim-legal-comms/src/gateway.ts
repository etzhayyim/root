/**
 * etzhayyim-legal-comms — counsel-operated comms gateway (ADR-2605302345 §D2).
 *
 * Bridges fax / email / e-filing for the legal-services platform. It is a
 * TRANSPORT, not a practitioner. The hard rule (G18):
 *
 *   Every outbound artifact that constitutes a LEGAL ACT (court filing,
 *   pleading / 準備書面, formal notice / 内容証明, demand / representation
 *   letter) MUST be actuated and signed by a human lawyer LICENSED in the
 *   destination jurisdiction, using their OWN credential. etzhayyim holds
 *   no signing key, seal or credential for any legal act
 *   (no-server-key ADR-2605231525, extended to the legal surface).
 *
 * The corp orchestrates; counsel acts. Autonomous (lawyer-absent) filing is
 * UPL in every jurisdiction surveyed in ADR-2605302200 and is impossible by
 * construction here: `sendLegalAct` throws without a valid counselActuation.
 */

export type Transport = "fax" | "email" | "e-filing" | "secure-message" | "postal";

export type ArtifactClass =
  | "court-filing"
  | "pleading"
  | "formal-notice"
  | "demand-letter"
  | "representation-letter"
  | "appeal-document";

/** Maps com.etzhayyim.legal.outboundLegalAct#counselActuation. */
export interface CounselActuation {
  counselDid: string;            // DID of the actuating licensed lawyer
  licenseJurisdiction: string;   // MUST equal the artifact's destinationJurisdiction
  counselSignatureRef: string;   // ref to the lawyer's OWN signature on the artifact
  actuatedAt: string;            // ISO datetime
}

export interface LegalActArtifact {
  destinationJurisdiction: string;
  artifactClass: ArtifactClass;
  transport: Transport;
  payloadCid: string;            // content-addressed artifact body
  destinationEndpoint: string;   // court/party endpoint (from judiciary.court)
}

export interface TransmitReceipt {
  ok: true;
  transport: Transport;
  counselDid: string;
  transmittedAt: string;
}

/**
 * G18 gate. Verifies a human licensed-counsel actuation, then transmits.
 * Throws (never silently degrades) if actuation is missing or mismatched.
 */
export async function sendLegalAct(
  artifact: LegalActArtifact,
  actuation: CounselActuation | undefined,
  transports: TransportAdapters,
): Promise<TransmitReceipt> {
  // (1) actuation MUST be present — no legal act leaves without counsel.
  if (!actuation) {
    throw new Error(
      `G18: legal act '${artifact.artifactClass}' has no counselActuation. ` +
      `Every legal act requires a human licensed lawyer's actuation.`,
    );
  }
  // (2) the lawyer must be licensed in the DESTINATION jurisdiction.
  if (actuation.licenseJurisdiction !== artifact.destinationJurisdiction) {
    throw new Error(
      `G18: actuating counsel is licensed in '${actuation.licenseJurisdiction}' ` +
      `but the act targets '${artifact.destinationJurisdiction}'.`,
    );
  }
  // (3) the signature is the LAWYER'S OWN. The platform holds no key, so a
  //     missing signature reference cannot be substituted by the corp.
  if (!actuation.counselDid || !actuation.counselSignatureRef) {
    throw new Error(
      `G18: counselActuation requires counselDid + counselSignatureRef ` +
      `(the lawyer signs with their own credential; the corp holds none).`,
    );
  }

  const adapter = transports[artifact.transport];
  if (!adapter) throw new Error(`unsupported transport '${artifact.transport}'`);

  await adapter.transmit({
    endpoint: artifact.destinationEndpoint,
    payloadCid: artifact.payloadCid,
    counselSignatureRef: actuation.counselSignatureRef, // lawyer's signature rides along
  });

  return {
    ok: true,
    transport: artifact.transport,
    counselDid: actuation.counselDid,
    transmittedAt: new Date().toISOString(),
  };
}

/**
 * Non-legal-act transport (scheduling confirmations, adherent-authored
 * document delivery). No counsel actuation required — these are not legal
 * acts. The classifier of what IS a legal act is the ArtifactClass enum
 * above; anything in that enum MUST go through `sendLegalAct`.
 */
export async function transmitNonLegalAct(
  kind: "appointment" | "document-delivery" | "scheduling",
  transport: Transport,
  endpoint: string,
  payloadCid: string,
  transports: TransportAdapters,
): Promise<TransmitReceipt> {
  const adapter = transports[transport];
  if (!adapter) throw new Error(`unsupported transport '${transport}'`);
  await adapter.transmit({ endpoint, payloadCid });
  return { ok: true, transport, counselDid: "", transmittedAt: new Date().toISOString() };
}

export interface TransportAdapter {
  transmit(msg: {
    endpoint: string;
    payloadCid: string;
    counselSignatureRef?: string;
  }): Promise<void>;
}

export type TransportAdapters = Partial<Record<Transport, TransportAdapter>>;
