/**
 * hrse rw-free — barrel.
 *
 * Per ADR-2606011400 (Consensys pattern, per-function). Public cybersecurity
 * freelance JOB-BOARD catalog on the etzhayyim substrate (AT PDS records; no RW).
 *
 *   company    : registerCompany / getCompany / listCompanies (name search)
 *   jobPosting : addJobPosting (FK→company, category/seniority/engagement enums,
 *                comp decimal-strings, remote bool) / listJobPostings (title+skill search)
 *   coverage
 *
 * (c) MIXED SPLIT: the public browse surface migrates. The marketplace backend —
 * freelancer profiles + applications (job-seeker PII), matching engine,
 * evaluation, Clerk subscription/billing (Settlement), placement (liability) —
 * STAYS etzhayyim via consent-capability. Job postings carry NO applicant PII.
 */

export * from "./types.js";
export {
  registerCompany,
  getCompany,
  listCompanies,
  addJobPosting,
  listJobPostings,
  coverage,
} from "./registry.js";
