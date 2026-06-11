/**
 * Kyber Inbox worker — aggregates Outlook/OneDrive/Gmail signals into kyber ERP dept streams.
 *
 * Subscribes: com.etzhayyim.apps.kyber.inbox.{emailSignal,calendarSignal,documentSignal}
 * Writes: vertex_email_message / vertex_calendar_event / vertex_office_document + edge_kyber_routed
 *
 * This is a Phase-0 reactive ingestion shell. On each PDS commit in any inbox
 * collection, we derive the matching RisingWave row via Kysely and upsert through
 * the Hyperdrive PG wire. Classification (signal/noise/kyberDept) is assumed to
 * be pre-computed upstream by the email-service-adapter / onedrive-sync job.
 */
import {
  createKyselyDb,
  createWorkerExport,
} from '@etzhayyim/kotodama-host-sdk';
import type { Database } from '@etzhayyim/graph-schema';

interface Env {
  HYPERDRIVE: Hyperdrive;
  PDS_SERVICE: Fetcher;
  PDS_RPC: unknown;
}

type Commit = {
  repo: string;
  collection: string;
  rkey: string;
  record: Record<string, unknown>;
  ts?: string;
  seq?: number;
};

const ACCOUNT_DID_BY_REPO = (repo: string) => repo.startsWith('did:') ? repo : `did:web:${repo}`;

async function onEmailSignal(db: ReturnType<typeof createKyselyDb<Database>>, c: Commit) {
  const r = c.record as Record<string, string | number | boolean>;
  const vid = `email_msg:${r.messageIdHash}`;
  await db.insertInto('vertex_email_message').values({
    vertex_id: vid,
    owner_did: ACCOUNT_DID_BY_REPO(c.repo),
    sensitivity_ord: (r.sensitivityOrd as number) ?? 3,
    created_date: ((r.receivedAt as string) || '').slice(0, 10) || null,
    message_id: r.messageIdHash as string,
    message_id_hash: r.messageIdHash as string,
    conversation_id: (r.conversationHash as string) ?? null,
    account_did: r.accountDid as string,
    folder: (r.folder as string) ?? 'inbox',
    received_at: r.receivedAt as string,
    from_address: (r.fromAddress as string) ?? null,
    from_domain: r.fromDomain as string,
    sender_kind: (r.senderKind as string) ?? 'external',
    subject_enc: (r.subjectEnc as string) ?? null,
    subject_hash: (r.subjectHash as string) ?? null,
    body_preview_enc: (r.bodyPreviewEnc as string) ?? null,
    importance: (r.importance as string) ?? 'normal',
    is_read: r.isRead ? 1 : 0,
    is_flagged: r.isFlagged ? 1 : 0,
    has_attachments: r.hasAttachments ? 1 : 0,
    noise_score: (r.noiseScore as number) ?? 0,
    signal_class: r.signalClass as string,
    kyber_dept: r.kyberDept as string,
    status: 'active',
    collection: c.collection,
  }).execute();

  await db.insertInto('edge_kyber_routed').values({
    edge_id: `kr:m:${r.messageIdHash}`,
    src_vid: vid,
    dst_vid: `kyber_dept:${r.kyberDept}`,
    owner_did: ACCOUNT_DID_BY_REPO(c.repo),
    sensitivity_ord: 2,
    created_date: ((r.receivedAt as string) || '').slice(0, 10) || null,
    label: 'email',
    dept_code: r.kyberDept as string,
    signal_class: r.signalClass as string,
    confidence: (r.signalClass === 'noise' ? 0.95 : 0.6),
    routed_at: r.receivedAt as string,
  }).execute();
}

async function onCalendarSignal(db: ReturnType<typeof createKyselyDb<Database>>, c: Commit) {
  const r = c.record as Record<string, string | number | boolean>;
  const vid = `cal_event:${r.eventIdHash}`;
  await db.insertInto('vertex_calendar_event').values({
    vertex_id: vid,
    owner_did: ACCOUNT_DID_BY_REPO(c.repo),
    sensitivity_ord: (r.sensitivityOrd as number) ?? 3,
    created_date: ((r.startAt as string) || '').slice(0, 10) || null,
    event_id: r.eventIdHash as string,
    account_did: r.accountDid as string,
    subject_enc: (r.subjectEnc as string) ?? null,
    subject_hash: (r.subjectHash as string) ?? null,
    start_at: r.startAt as string,
    end_at: r.endAt as string,
    duration_min: (r.durationMin as number) ?? 0,
    organizer_address: (r.organizerAddress as string) ?? null,
    location: (r.location as string) ?? null,
    show_as: (r.showAs as string) ?? null,
    is_cancelled: r.isCancelled ? 1 : 0,
    attendee_count: (r.attendeeCount as number) ?? 0,
    internal_attendee_count: (r.internalAttendeeCount as number) ?? 0,
    external_attendee_count: (r.externalAttendeeCount as number) ?? 0,
    kyber_dept: r.kyberDept as string,
    signal_class: r.signalClass as string,
    status: 'active',
    collection: c.collection,
  }).execute();

  await db.insertInto('edge_kyber_routed').values({
    edge_id: `kr:e:${r.eventIdHash}`,
    src_vid: vid,
    dst_vid: `kyber_dept:${r.kyberDept}`,
    owner_did: ACCOUNT_DID_BY_REPO(c.repo),
    sensitivity_ord: 2,
    created_date: ((r.startAt as string) || '').slice(0, 10) || null,
    label: 'event',
    dept_code: r.kyberDept as string,
    signal_class: r.signalClass as string,
    confidence: 0.7,
    routed_at: r.startAt as string,
  }).execute();
}

async function onDocumentSignal(db: ReturnType<typeof createKyselyDb<Database>>, c: Commit) {
  const r = c.record as Record<string, string | number | boolean>;
  const vid = `office_doc:${r.driveItemIdHash}`;
  await db.insertInto('vertex_office_document').values({
    vertex_id: vid,
    owner_did: ACCOUNT_DID_BY_REPO(c.repo),
    sensitivity_ord: (r.sensitivityOrd as number) ?? 3,
    created_date: ((r.modifiedAt as string) || '').slice(0, 10) || null,
    drive_item_id: r.driveItemIdHash as string,
    drive_item_id_hash: r.driveItemIdHash as string,
    account_did: r.accountDid as string,
    path_hash: (r.pathHash as string) ?? null,
    name_enc: (r.nameEnc as string) ?? null,
    name_hash: (r.nameHash as string) ?? null,
    extension: r.extension as string,
    mime_type: (r.mimeType as string) ?? null,
    size_bytes: (r.sizeBytes as number) ?? 0,
    created_at: (r.createdAt as string) ?? null,
    modified_at: (r.modifiedAt as string) ?? null,
    author_address: (r.authorAddress as string) ?? null,
    last_modified_by: (r.lastModifiedBy as string) ?? null,
    sheet_count: (r.sheetCount as number) ?? 0,
    page_count: (r.pageCount as number) ?? 0,
    word_count: (r.wordCount as number) ?? 0,
    extracted: r.extracted ? 1 : 0,
    extract_engine: (r.extractEngine as string) ?? null,
    kyber_dept: r.kyberDept as string,
    signal_class: r.signalClass as string,
    noise_score: (r.noiseScore as number) ?? 0,
    status: 'active',
    collection: c.collection,
  }).execute();

  await db.insertInto('edge_kyber_routed').values({
    edge_id: `kr:d:${r.driveItemIdHash}`,
    src_vid: vid,
    dst_vid: `kyber_dept:${r.kyberDept}`,
    owner_did: ACCOUNT_DID_BY_REPO(c.repo),
    sensitivity_ord: 2,
    created_date: ((r.modifiedAt as string) || '').slice(0, 10) || null,
    label: 'document',
    dept_code: r.kyberDept as string,
    signal_class: r.signalClass as string,
    confidence: 0.8,
    routed_at: (r.modifiedAt as string) ?? null,
  }).execute();
}

const ROUTES: Record<string, (db: ReturnType<typeof createKyselyDb<Database>>, c: Commit) => Promise<void>> = {
  'com.etzhayyim.apps.kyber.inbox.emailSignal':    onEmailSignal,
  'com.etzhayyim.apps.kyber.inbox.calendarSignal': onCalendarSignal,
  'com.etzhayyim.apps.kyber.inbox.documentSignal': onDocumentSignal,
};

export default createWorkerExport<Env>({
  async onCommit(env, commit) {
    const handler = ROUTES[commit.collection];
    if (!handler) return;
    const db = createKyselyDb<Database>(env.HYPERDRIVE);
    await handler(db, commit as Commit);
  },
  async fetch(_req, _env) {
    return new Response(JSON.stringify({
      name: 'kyber-inbox',
      status: 'active',
      collections: Object.keys(ROUTES),
    }), { headers: { 'content-type': 'application/json' } });
  },
});
