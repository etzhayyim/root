/**
 * webya kotoba — kotoba-E2E split for the AI homepage-generation app
 * (企業・士業 HP 自動生成). Founder directive 2026-06-03: front everything that
 * can move; only the irreducible regulated EXECUTION stays etzhayyim.
 *
 * Per ADR-2606011400 (Consensys product-front / infra-back) + ADR-2605172400
 * (3-axis OR-test) + ADR-2605181100 (kotoba E2E encrypted-record envelope).
 *
 * SPLIT (designed from vertex_webya_* schema):
 *   PLAINTEXT (public AT records via sdk.write / sdk.read) — the published web
 *   presence IS public by definition:
 *     • siteCatalog   — site name / profession / status / subdomain / customDomain
 *     • template      — profession-keyed page-set + html skeleton reference
 *     • page          — rendered page (slug / title / html / Schema.org JSON-LD)
 *     • generationJob — ops timeline (status / llmCalls / revisions) — public facts
 *     • domain        — domain↔site mapping + public-DNS proof tokens (TXT
 *                       name/value the customer publishes in DNS, CNAME target,
 *                       ssl_status, ownership_verified) — all public, NOT secret.
 *
 *   E2E (kotoba envelope via sdk.encryptedWrite / sdk.encryptedRead; read-cap =
 *   owner DID + explicit recipients) — confidential / per-person:
 *     • clientContact   — representative name + address + email + phone + org DID
 *                         (business + personal contact PII)
 *     • legalDisclosure — 士業 registration number + association + representative
 *                         name (per-person regulated identity credentials).
 *                         Public site rendering still reaches visitors via the
 *                         plaintext page.htmlContent; encrypting the structured
 *                         source-of-truth does not break public display.
 *
 *   STAYS etzhayyim (consumed via consent-capability, NOT a collection) — the
 *   irreducible regulated EXECUTION:
 *     • LLM/LangGraph site-generation INFERENCE (assistant site/content/HTML)
 *     • CF-for-SaaS custom-hostname provisioning CALL + CF_API_TOKEN credential
 *       custody (the provisioning ACT, not the resulting domain DATA record).
 *
 * AT-Lexicon: no float — webya is all-integer (llmCallsCount / version /
 * revisionCount / severity-free). No money fields.
 */

// ─── Plaintext collections ──────────────────────────────────────────
export const SITE_CATALOG_COLLECTION = "com.etzhayyim.apps.webya.siteCatalog";
export const TEMPLATE_COLLECTION = "com.etzhayyim.apps.webya.template";
export const PAGE_COLLECTION = "com.etzhayyim.apps.webya.page";
export const GENERATION_JOB_COLLECTION = "com.etzhayyim.apps.webya.generationJob";
export const DOMAIN_COLLECTION = "com.etzhayyim.apps.webya.domain";

// ─── E2E inner-type NSIDs (body shape inside the encrypted envelope) ─
export const CLIENT_CONTACT_INNER_TYPE = "com.etzhayyim.apps.webya.clientContact";
export const LEGAL_DISCLOSURE_INNER_TYPE = "com.etzhayyim.apps.webya.legalDisclosure";

export const WEBYA_DID_PREFIX = "did:web:webya.etzhayyim.com:" as const;

export type ProfessionKind =
  | "law_firm"
  | "accounting_firm"
  | "judicial_scrivener"
  | "admin_scrivener"
  | "general_company";

export type SiteStatus = "draft" | "generating" | "published" | "failed";
export type JobStatus = "pending" | "running" | "succeeded" | "failed";
export type SslStatus = "none" | "pending" | "active";

// ─── Site catalog (PLAINTEXT, public presence metadata) ─────────────

export interface SiteCatalogRecord {
  did: string;
  siteId: string;
  siteName: string;
  professionKind: ProfessionKind;
  status: SiteStatus;
  subdomain: string;
  customDomain?: string;
  sslStatus: SslStatus;
  publishedAt?: string;
  createdAt: string;
}
export interface SiteCatalogView extends SiteCatalogRecord {
  siteUri: string;
}
export interface RegisterSiteInput {
  siteId: string;
  siteName: string;
  professionKind: ProfessionKind;
  subdomain: string;
  status?: SiteStatus;
  customDomain?: string;
  sslStatus?: SslStatus;
  publishedAt?: string;
}
export interface RegisterSiteOutput {
  status: "recorded" | "alreadyExists" | "rejected";
  siteUri?: string;
  did?: string;
  siteId?: string;
  error?: string;
}
export interface GetSiteInput {
  siteId: string;
}
export interface GetSiteOutput {
  site?: SiteCatalogView;
  error?: string;
}
export interface ListSitesInput {
  professionKind?: ProfessionKind;
  status?: SiteStatus;
  limit?: number;
  cursor?: string;
}
export interface ListSitesOutput {
  items: SiteCatalogView[];
  cursor?: string;
  total: number;
}

// ─── Template (PLAINTEXT, public reference catalog) ──────────────────

export interface TemplateRecord {
  did: string;
  templateId: string;
  professionKind: ProfessionKind;
  pages: string[];
  htmlSkeleton: string;
  version: number;
  active: boolean;
  createdAt: string;
}
export interface TemplateView extends TemplateRecord {
  templateUri: string;
}
export interface RegisterTemplateInput {
  templateId: string;
  professionKind: ProfessionKind;
  pages: string[];
  htmlSkeleton: string;
  version?: number;
  active?: boolean;
}
export interface RegisterTemplateOutput {
  status: "recorded" | "alreadyExists" | "rejected";
  templateUri?: string;
  did?: string;
  templateId?: string;
  error?: string;
}
export interface ListTemplatesInput {
  professionKind?: ProfessionKind;
  limit?: number;
  cursor?: string;
}
export interface ListTemplatesOutput {
  items: TemplateView[];
  cursor?: string;
  total: number;
}

// ─── Page (PLAINTEXT, published page content) ───────────────────────

export interface PageRecord {
  did: string;
  pageId: string;
  siteId: string;
  slug: string;
  title: string;
  metaDescription?: string;
  htmlContent?: string;
  jsonLd?: string;
  status: SiteStatus;
  updatedAt: string;
}
export interface PageView extends PageRecord {
  pageUri: string;
}
export interface RegisterPageInput {
  pageId: string;
  /** FK → siteCatalog.siteId; verified via exists(). */
  siteId: string;
  slug: string;
  title: string;
  metaDescription?: string;
  htmlContent?: string;
  jsonLd?: string;
  status?: SiteStatus;
}
export interface RegisterPageOutput {
  status: "recorded" | "alreadyExists" | "rejected";
  pageUri?: string;
  did?: string;
  pageId?: string;
  error?: string;
}
export interface ListPagesInput {
  siteId?: string;
  limit?: number;
  cursor?: string;
}
export interface ListPagesOutput {
  items: PageView[];
  cursor?: string;
  total: number;
}

// ─── Generation job (PLAINTEXT, public ops timeline) ────────────────

export interface GenerationJobRecord {
  did: string;
  jobId: string;
  siteId: string;
  status: JobStatus;
  llmCallsCount: number;
  revisionCount: number;
  startedAt: string;
  completedAt?: string;
}
export interface GenerationJobView extends GenerationJobRecord {
  jobUri: string;
}
export interface RegisterJobInput {
  jobId: string;
  siteId: string;
  status?: JobStatus;
  llmCallsCount?: number;
  revisionCount?: number;
  startedAt?: string;
  completedAt?: string;
}
export interface RegisterJobOutput {
  status: "recorded" | "alreadyExists" | "rejected";
  jobUri?: string;
  did?: string;
  jobId?: string;
  error?: string;
}
export interface ListJobsInput {
  siteId?: string;
  status?: JobStatus;
  limit?: number;
  cursor?: string;
}
export interface ListJobsOutput {
  items: GenerationJobView[];
  cursor?: string;
  total: number;
}

// ─── Domain (PLAINTEXT, public DNS mapping + proof tokens) ──────────

export interface DomainRecord {
  did: string;
  domainId: string;
  siteId: string;
  domain: string;
  sslStatus: SslStatus;
  ownershipVerified: boolean;
  cnameTarget: string;
  /** Proof token the customer publishes in public DNS — public, not secret. */
  verificationTxtName?: string;
  verificationTxtValue?: string;
  provisionedAt?: string;
  createdAt: string;
}
export interface DomainView extends DomainRecord {
  domainUri: string;
}
export interface RegisterDomainInput {
  domainId: string;
  siteId: string;
  domain: string;
  sslStatus?: SslStatus;
  ownershipVerified?: boolean;
  cnameTarget?: string;
  verificationTxtName?: string;
  verificationTxtValue?: string;
  provisionedAt?: string;
}
export interface RegisterDomainOutput {
  status: "recorded" | "alreadyExists" | "rejected";
  domainUri?: string;
  did?: string;
  domainId?: string;
  error?: string;
}
export interface ListDomainsInput {
  siteId?: string;
  sslStatus?: SslStatus;
  limit?: number;
  cursor?: string;
}
export interface ListDomainsOutput {
  items: DomainView[];
  cursor?: string;
  total: number;
}

// ─── Client contact (E2E-ENCRYPTED, contact PII) ────────────────────

export interface ClientContactBody {
  clientId: string;
  siteId: string;
  representativeName: string;
  address: string;
  email?: string;
  phone?: string;
  orgDid?: string;
  recordedAt: string;
}
export interface ClientContactView extends ClientContactBody {
  uri: string;
  sender: string;
  createdAt: string;
}
export interface RecordClientContactInput {
  clientId: string;
  siteId: string;
  representativeName: string;
  address: string;
  email?: string;
  phone?: string;
  orgDid?: string;
  recordedAt?: string;
  /** Extra DIDs to grant read-cap (owner always included). */
  recipients?: string[];
}
export interface RecordClientContactOutput {
  status: "recorded" | "rejected";
  uri?: string;
  keyId?: string;
  clientId?: string;
  error?: string;
}
export interface ListClientContactsInput {
  siteId?: string;
  limit?: number;
  cursor?: string;
}
export interface ListClientContactsOutput {
  items: ClientContactView[];
  cursor?: string;
  total: number;
}
export interface GetClientContactInput {
  clientId: string;
}
export interface GetClientContactOutput {
  contact?: ClientContactView;
  error?: string;
}

// ─── Legal disclosure (E2E-ENCRYPTED, per-person regulated credentials) ─

export type DisclosureType =
  | "registration_number"
  | "association_name"
  | "corporate_number";

export interface LegalDisclosureBody {
  disclosureId: string;
  siteId: string;
  professionKind: ProfessionKind;
  disclosureType: DisclosureType;
  disclosureValue: string;
  representativeName: string;
  verifiedAt?: string;
  recordedAt: string;
}
export interface LegalDisclosureView extends LegalDisclosureBody {
  uri: string;
  sender: string;
  createdAt: string;
}
export interface RecordDisclosureInput {
  disclosureId: string;
  siteId: string;
  professionKind: ProfessionKind;
  disclosureType: DisclosureType;
  disclosureValue: string;
  representativeName: string;
  verifiedAt?: string;
  recordedAt?: string;
  recipients?: string[];
}
export interface RecordDisclosureOutput {
  status: "recorded" | "rejected";
  uri?: string;
  keyId?: string;
  disclosureId?: string;
  error?: string;
}
export interface ListDisclosuresInput {
  siteId?: string;
  limit?: number;
  cursor?: string;
}
export interface ListDisclosuresOutput {
  items: LegalDisclosureView[];
  cursor?: string;
  total: number;
}
export interface GetDisclosureInput {
  disclosureId: string;
}
export interface GetDisclosureOutput {
  disclosure?: LegalDisclosureView;
  error?: string;
}

// ─── Coverage rollup ────────────────────────────────────────────────

export interface CoverageInput {
  maxScan?: number;
}
export interface CoverageOutput {
  siteCatalogCount?: number;
  templateCount?: number;
  pageCount?: number;
  generationJobCount?: number;
  domainCount?: number;
  clientContactCount?: number;
  legalDisclosureCount?: number;
  sitesByStatus?: Record<string, number>;
  truncated?: boolean;
  error?: string;
}

// ─── Validation + helpers ───────────────────────────────────────────

const PROFESSION_KINDS: ReadonlySet<string> = new Set<ProfessionKind>([
  "law_firm",
  "accounting_firm",
  "judicial_scrivener",
  "admin_scrivener",
  "general_company",
]);
const DISCLOSURE_TYPES: ReadonlySet<string> = new Set<DisclosureType>([
  "registration_number",
  "association_name",
  "corporate_number",
]);

export function isUint(n: unknown): n is number {
  return typeof n === "number" && Number.isInteger(n) && n >= 0;
}
export function isProfessionKind(v: unknown): v is ProfessionKind {
  return typeof v === "string" && PROFESSION_KINDS.has(v);
}
export function isDisclosureType(v: unknown): v is DisclosureType {
  return typeof v === "string" && DISCLOSURE_TYPES.has(v);
}
export function webyaDidFor(kind: string, id: string): string {
  return `${WEBYA_DID_PREFIX}${kind}:${id.toLowerCase()}`;
}
export function siteRkey(id: string): string {
  return `site-${slugId(id)}`;
}
export function templateRkey(id: string): string {
  return `tpl-${slugId(id)}`;
}
export function pageRkey(id: string): string {
  return `page-${slugId(id)}`;
}
export function jobRkey(id: string): string {
  return `job-${slugId(id)}`;
}
export function domainRkey(id: string): string {
  return `dom-${slugId(id)}`;
}
export function clientContactRkey(id: string): string {
  return `client-${slugId(id)}`;
}
export function disclosureRkey(id: string): string {
  return `disc-${slugId(id)}`;
}
function slugId(id: string): string {
  return id.toLowerCase().replace(/[^a-z0-9]+/g, "-");
}
