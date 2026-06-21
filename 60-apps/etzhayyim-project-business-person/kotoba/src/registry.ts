/**
 * business-person kotoba — person + appointment registries + coverage.
 * AT PDS records (no RW). Appointments FK-reference an existing person.
 * Tier-1 public-disclosure data only; private PII stays in natural-person.
 */

import type { Etzhayyim } from "@etzhayyim/sdk";
import {
  APPOINTMENT_COLLECTION,
  PERSON_COLLECTION,
  ROLES,
  appointmentDidFor,
  appointmentRkey,
  isSlug,
  personDidFor,
  personRkey,
  type AddAppointmentInput,
  type AddAppointmentOutput,
  type AppointmentRecord,
  type AppointmentView,
  type CoverageInput,
  type CoverageOutput,
  type EndAppointmentInput,
  type EndAppointmentOutput,
  type GetPersonInput,
  type GetPersonOutput,
  type ListAppointmentsInput,
  type ListAppointmentsOutput,
  type ListPersonsInput,
  type ListPersonsOutput,
  type PersonRecord,
  type PersonView,
  type RegisterPersonInput,
  type RegisterPersonOutput,
} from "./types.js";

const PAGE_LIMIT = 100;
const DEFAULT_MAX_SCAN = 10_000;

async function exists(e: Etzhayyim, collection: string, rkey: string): Promise<boolean> {
  const resp = await e.read({ collection, rkey }).catch(() => ({ records: [] }));
  return Boolean(resp.records[0]?.value);
}

// ─── Person ─────────────────────────────────────────────────────────

export async function registerPerson(e: Etzhayyim, input: RegisterPersonInput): Promise<RegisterPersonOutput> {
  if (!input.slug || !input.fullName) return { status: "rejected", error: "missingRequiredFields" };
  const slug = input.slug.toLowerCase();
  if (!isSlug(slug)) return { status: "rejected", error: "invalidSlug" };
  if (!ROLES.has(input.primaryRole)) return { status: "rejected", error: "invalidPrimaryRole" };
  if (input.primaryEntityDid && !input.primaryEntityDid.startsWith("did:")) return { status: "rejected", error: "invalidPrimaryEntityDid" };
  if (input.naturalPersonDid && !input.naturalPersonDid.startsWith("did:")) return { status: "rejected", error: "invalidNaturalPersonDid" };
  const rkey = personRkey(slug);
  const existing = await e.read<PersonRecord>({ collection: PERSON_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", personUri: existing.records[0].uri, did: existing.records[0].value.did, slug };
  }
  const did = personDidFor(slug);
  const record: PersonRecord = {
    did,
    slug,
    fullName: input.fullName,
    primaryRole: input.primaryRole,
    primaryEntityDid: input.primaryEntityDid,
    naturalPersonDid: input.naturalPersonDid,
    nationality: input.nationality?.toUpperCase(),
    sourceUrl: input.sourceUrl,
    createdAt: new Date().toISOString(),
  };
  const receipt = await e.write({ collection: PERSON_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "registered", personUri: receipt.uri, did, slug };
}

export async function getPerson(e: Etzhayyim, input: GetPersonInput): Promise<GetPersonOutput> {
  if (!input.slug) return { error: "invalidSlug" };
  const resp = await e.read<PersonRecord>({ collection: PERSON_COLLECTION, rkey: personRkey(input.slug.toLowerCase()) }).catch(() => ({ records: [] }));
  const r = resp.records[0];
  if (!r) return { error: "notFound" };
  return { person: { ...r.value, personUri: r.uri } };
}

export async function listPersons(e: Etzhayyim, input: ListPersonsInput = {}): Promise<ListPersonsOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<PersonRecord>({ collection: PERSON_COLLECTION, cursor: input.cursor, limit });
  const q = input.q?.toLowerCase();
  const nationality = input.nationality?.toUpperCase();
  const items: PersonView[] = resp.records
    .filter((r) => {
      const v = r.value;
      if (input.primaryRole && v.primaryRole !== input.primaryRole) return false;
      if (nationality && v.nationality !== nationality) return false;
      if (q && !v.fullName.toLowerCase().includes(q)) return false;
      return true;
    })
    .map((r) => ({ ...r.value, personUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Appointment ────────────────────────────────────────────────────

export async function addAppointment(e: Etzhayyim, input: AddAppointmentInput): Promise<AddAppointmentOutput> {
  if (!input.appointmentId || !input.personSlug || !input.entityDid) return { status: "rejected", error: "missingRequiredFields" };
  if (!input.entityDid.startsWith("did:")) return { status: "rejected", error: "invalidEntityDid" };
  if (!ROLES.has(input.role)) return { status: "rejected", error: "invalidRole" };
  const personSlug = input.personSlug.toLowerCase();
  if (!(await exists(e, PERSON_COLLECTION, personRkey(personSlug)))) {
    return { status: "personNotFound", error: `personNotFound:${personSlug}` };
  }
  const rkey = appointmentRkey(input.appointmentId);
  const existing = await e.read<AppointmentRecord>({ collection: APPOINTMENT_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", appointmentUri: existing.records[0].uri, did: existing.records[0].value.did, appointmentId: input.appointmentId };
  }
  const did = appointmentDidFor(input.appointmentId);
  const record: AppointmentRecord = {
    did,
    appointmentId: input.appointmentId,
    personSlug,
    entityDid: input.entityDid,
    role: input.role,
    startDate: input.startDate,
    endDate: input.endDate,
    current: input.current ?? !input.endDate,
    createdAt: new Date().toISOString(),
  };
  const receipt = await e.write({ collection: APPOINTMENT_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "added", appointmentUri: receipt.uri, did, appointmentId: input.appointmentId };
}

export async function endAppointment(e: Etzhayyim, input: EndAppointmentInput): Promise<EndAppointmentOutput> {
  if (!input.appointmentId || !input.endDate) return { status: "rejected", error: "missingRequiredFields" };
  const rkey = appointmentRkey(input.appointmentId);
  const resp = await e.read<AppointmentRecord>({ collection: APPOINTMENT_COLLECTION, rkey }).catch(() => ({ records: [] }));
  const appt = resp.records[0]?.value;
  if (!appt) return { status: "notFound", error: "appointmentNotFound" };
  if (!appt.current) return { status: "rejected", error: "alreadyEnded" };
  await e.write({ collection: APPOINTMENT_COLLECTION, record: { ...appt, endDate: input.endDate, current: false } as unknown as Record<string, unknown>, rkey });
  return { status: "ended", appointmentId: input.appointmentId };
}

export async function listAppointments(e: Etzhayyim, input: ListAppointmentsInput = {}): Promise<ListAppointmentsOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<AppointmentRecord>({ collection: APPOINTMENT_COLLECTION, cursor: input.cursor, limit });
  const personSlug = input.personSlug?.toLowerCase();
  const items: AppointmentView[] = resp.records
    .filter((r) => {
      const v = r.value;
      if (personSlug && v.personSlug !== personSlug) return false;
      if (input.entityDid && v.entityDid !== input.entityDid) return false;
      if (input.role && v.role !== input.role) return false;
      if (input.current !== undefined && v.current !== input.current) return false;
      return true;
    })
    .map((r) => ({ ...r.value, appointmentUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Coverage ───────────────────────────────────────────────────────

async function countAll<T>(e: Etzhayyim, collection: string, maxScan: number, onRow: (v: T) => void): Promise<number> {
  let cursor: string | undefined;
  let scanned = 0;
  while (scanned < maxScan) {
    const page = await e.read<T>({ collection, cursor, limit: PAGE_LIMIT });
    for (const r of page.records) {
      if (scanned >= maxScan) break;
      onRow(r.value);
      scanned += 1;
    }
    if (scanned >= maxScan || !page.cursor || page.records.length < PAGE_LIMIT) break;
    cursor = page.cursor;
  }
  return scanned;
}

export async function coverage(e: Etzhayyim, input: CoverageInput = {}): Promise<CoverageOutput> {
  const maxScan = Math.min(input.maxScan ?? DEFAULT_MAX_SCAN, DEFAULT_MAX_SCAN);
  const personsByRole: Record<string, number> = {};
  const personCount = await countAll<PersonRecord>(e, PERSON_COLLECTION, maxScan, (v) => {
    personsByRole[v.primaryRole] = (personsByRole[v.primaryRole] ?? 0) + 1;
  });
  let currentAppointments = 0;
  const appointmentCount = await countAll<AppointmentRecord>(e, APPOINTMENT_COLLECTION, maxScan, (v) => {
    if (v.current) currentAppointments += 1;
  });
  return {
    personCount,
    appointmentCount,
    personsByRole,
    currentAppointments,
    truncated: personCount >= maxScan || appointmentCount >= maxScan,
  };
}
