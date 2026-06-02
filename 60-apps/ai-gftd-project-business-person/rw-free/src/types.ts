/**
 * business-person rw-free — public business-person registry record types.
 *
 * Per ADR-2606011400. business-person is a PUBLIC registry of corporate
 * officers / executives / board members (name + public role + company
 * affiliation), sourced from official disclosures (corporate registries / XBRL /
 * Wikipedia). Registry on AT PDS records (replaces RW). ADR-2605172000 RW-free.
 *
 * PII BOUNDARY (ADR-0014): only **Tier-1 public** role/appointment data lives
 * on-substrate here. Private contact info / non-public history is **Tier-3** and
 * is delegated to natural-person.etzhayyim.com via `naturalPersonDid` — it MUST
 * NOT be written to these public records.
 *
 * AXIS NOTE (ADR-2605172400): axis-clean public open-data — no private-PII
 * custody (delegated), no settlement, no fulfillment liability.
 *
 * Identity hierarchy:
 *   did:web:business-person.etzhayyim.com                          — controller
 *   did:web:business-person.etzhayyim.com:bp:{slug}                — a person
 *   did:web:business-person.etzhayyim.com:appt:{appointmentId}     — an appointment
 */

export const BP_DID_PREFIX = "did:web:business-person.etzhayyim.com:" as const;

export const PERSON_COLLECTION = "com.etzhayyim.apps.businessPerson.person";
export const APPOINTMENT_COLLECTION = "com.etzhayyim.apps.businessPerson.appointment";

export type PrimaryRole =
  | "ceo"
  | "cfo"
  | "coo"
  | "cto"
  | "chairman"
  | "president"
  | "vice-president"
  | "director"
  | "founder"
  | "secretary"
  | "treasurer";

export const ROLES: ReadonlySet<string> = new Set([
  "ceo", "cfo", "coo", "cto", "chairman", "president",
  "vice-president", "director", "founder", "secretary", "treasurer",
]);

// ─── Person ─────────────────────────────────────────────────────────

export interface PersonRecord {
  did: string;
  /** URL-safe slug, canonical key. */
  slug: string;
  fullName: string;
  primaryRole: PrimaryRole;
  /** DID of the primary legal-entity (cross-app ref), optional. */
  primaryEntityDid?: string;
  /** Link to the Tier-3 PII custodian (natural-person), optional. */
  naturalPersonDid?: string;
  /** ISO 3166-1 alpha-2 nationality (public), optional. */
  nationality?: string;
  /** Public source URL (disclosure / Wikipedia / registry). */
  sourceUrl?: string;
  createdAt: string;
}
export interface PersonView extends PersonRecord {
  personUri: string;
}
export interface RegisterPersonInput {
  slug: string;
  fullName: string;
  primaryRole: PrimaryRole;
  primaryEntityDid?: string;
  naturalPersonDid?: string;
  nationality?: string;
  sourceUrl?: string;
}
export interface RegisterPersonOutput {
  status: "registered" | "alreadyExists" | "rejected";
  personUri?: string;
  did?: string;
  slug?: string;
  error?: string;
}
export interface GetPersonInput {
  slug: string;
}
export interface GetPersonOutput {
  person?: PersonView;
  error?: string;
}
export interface ListPersonsInput {
  primaryRole?: PrimaryRole;
  nationality?: string;
  /** App-layer substring match over fullName (AT PDS has no text search). */
  q?: string;
  limit?: number;
  cursor?: string;
}
export interface ListPersonsOutput {
  items: PersonView[];
  cursor?: string;
  total: number;
}

// ─── Appointment ────────────────────────────────────────────────────

export interface AppointmentRecord {
  did: string;
  appointmentId: string;
  /** FK → person slug. */
  personSlug: string;
  /** DID of the company / legal-entity (cross-app ref). */
  entityDid: string;
  role: PrimaryRole;
  startDate?: string;
  endDate?: string;
  current: boolean;
  createdAt: string;
}
export interface AppointmentView extends AppointmentRecord {
  appointmentUri: string;
}
export interface AddAppointmentInput {
  appointmentId: string;
  personSlug: string;
  entityDid: string;
  role: PrimaryRole;
  startDate?: string;
  endDate?: string;
  current?: boolean;
}
export interface AddAppointmentOutput {
  status: "added" | "alreadyExists" | "rejected" | "personNotFound";
  appointmentUri?: string;
  did?: string;
  appointmentId?: string;
  error?: string;
}
export interface EndAppointmentInput {
  appointmentId: string;
  endDate: string;
}
export interface EndAppointmentOutput {
  status: "ended" | "notFound" | "rejected";
  appointmentId?: string;
  error?: string;
}
export interface ListAppointmentsInput {
  personSlug?: string;
  entityDid?: string;
  role?: PrimaryRole;
  current?: boolean;
  limit?: number;
  cursor?: string;
}
export interface ListAppointmentsOutput {
  items: AppointmentView[];
  cursor?: string;
  total: number;
}

// ─── Coverage ───────────────────────────────────────────────────────

export interface CoverageInput {
  maxScan?: number;
}
export interface CoverageOutput {
  personCount?: number;
  appointmentCount?: number;
  personsByRole?: Record<string, number>;
  currentAppointments?: number;
  truncated?: boolean;
  error?: string;
}

// ─── Validation + helpers ───────────────────────────────────────────

export function isSlug(s: string): boolean {
  return /^[a-z0-9][a-z0-9-]{0,63}$/.test(s);
}

export function personDidFor(slug: string): string {
  return `${BP_DID_PREFIX}bp:${slug.toLowerCase()}`;
}
export function personRkey(slug: string): string {
  return `person-${slug.toLowerCase()}`;
}
export function appointmentDidFor(id: string): string {
  return `${BP_DID_PREFIX}appt:${id.toLowerCase()}`;
}
export function appointmentRkey(id: string): string {
  return `appt-${id.toLowerCase()}`;
}
