/**
 * @fileoverview CVE Data Zod schema
 * Zod schema as the single source of truth for CVE Data validation
 *
 * @context
 * {
 *   "@context": "https://schema.org",
 *   "@type": "SoftwareApplication",
 *   "name": "CVE Data Zod Schema",
 *   "description": "Zod schema for CVE Data validation"
 * }
 */

import { z } from "zod";

/**
 * CVE Severity schema
 */
export const cveSeveritySchema = z.enum(["low", "medium", "high", "critical"]);

/**
 * CVE Status schema
 */
export const cveStatusSchema = z.enum(["published", "modified", "rejected"]);

/**
 * CVE Reference schema
 */
export const cveReferenceSchema = z.object({
  url: z.string().url(),
  source: z.string(),
  tags: z.array(z.string()),
});

/**
 * CVE Affected Product schema
 */
export const cveAffectedProductSchema = z.object({
  vendor: z.string(),
  product: z.string(),
  versions: z.array(z.string()),
});

/**
 * CVE Data schema
 * Type inference: z.infer<typeof cveDataSchema>
 */
export const cveDataSchema = z.object({
  cveId: z.string().min(1),
  description: z.string().min(1),
  publishedDate: z.coerce.date(),
  lastModifiedDate: z.coerce.date(),
  cvssScore: z.number().min(0).max(10).optional(),
  cvssVector: z.string().optional(),
  severity: cveSeveritySchema,
  cweIds: z.array(z.string()),
  references: z.array(cveReferenceSchema),
  affectedProducts: z.array(cveAffectedProductSchema),
  status: cveStatusSchema.default("published"),
  createdAt: z.coerce.date().optional(),
  updatedAt: z.coerce.date().optional(),
});

export type CVEData = z.infer<typeof cveDataSchema>;

