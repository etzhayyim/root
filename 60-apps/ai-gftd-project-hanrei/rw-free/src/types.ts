/**
 * hanrei rw-free — record types.
 *
 * Japanese case-law corpus. Per ADR-2605203000 Option B (PDS XRPC).
 * Replaces vendor's vertex_hanrei_jurisdiction / vertex_hanrei_court /
 * vertex_hanrei_case_record with AT PDS records.
 *
 * Identity hierarchy (per hanrei CLAUDE.md):
 *   did:web:hanrei.etzhayyim.com                       — controller
 *   did:web:hanrei.etzhayyim.com:jurisdiction:{iso3}   — country / region
 *   did:web:hanrei.etzhayyim.com:court:{jurisdiction}:{courtId}
 *   did:web:hanrei.etzhayyim.com:case:{caseId}
 *   did:web:hanrei.etzhayyim.com:law:{lawId}
 */

export interface JurisdictionRecord {
  did: string;
  iso3: string;
  name: string;
  nameLocal?: string;
  legalSystem?: "civil-law" | "common-law" | "religious-law" | "mixed";
  courts?: string[];
  primaryLanguage?: string;
  caseLawSource?: string;
  createdAt: string;
}

export interface JurisdictionView extends JurisdictionRecord {
  jurisdictionUri: string;
}

export interface RegisterJurisdictionInput {
  iso3: string;
  name: string;
  nameLocal?: string;
  legalSystem?: JurisdictionRecord["legalSystem"];
  courts?: string[];
  primaryLanguage?: string;
  caseLawSource?: string;
}

export interface RegisterJurisdictionOutput {
  status: "registered" | "alreadyExists" | "rejected";
  jurisdictionUri?: string;
  did?: string;
  iso3?: string;
  error?: string;
}

export interface GetJurisdictionInput {
  iso3: string;
}

export interface GetJurisdictionOutput {
  jurisdiction?: JurisdictionView;
  error?: string;
}

export interface ListJurisdictionsInput {
  legalSystem?: JurisdictionRecord["legalSystem"];
  limit?: number;
  cursor?: string;
}

export interface ListJurisdictionsOutput {
  items: JurisdictionView[];
  cursor?: string;
  total: number;
}

export const HANREI_DID_PREFIX = "did:web:hanrei.etzhayyim.com:" as const;

export function jurisdictionDid(iso3: string): string {
  return `${HANREI_DID_PREFIX}jurisdiction:${iso3.toLowerCase()}`;
}

export function jurisdictionRkey(iso3: string): string {
  return `jurisdiction-${iso3.toLowerCase()}`;
}
