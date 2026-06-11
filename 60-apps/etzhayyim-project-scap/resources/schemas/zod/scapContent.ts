/**
 * @fileoverview SCAP Content Zod schema
 * Zod schema as the single source of truth for SCAP Content validation
 *
 * @context
 * {
 *   "@context": "https://schema.org",
 *   "@type": "SoftwareApplication",
 *   "name": "SCAP Content Zod Schema",
 *   "description": "Zod schema for SCAP Content validation"
 * }
 */

import { z } from "zod";

/**
 * SCAP Content Type schema
 */
export const scapContentTypeSchema = z.enum([
  "cve",
  "oval",
  "xccdf",
  "cce",
  "cpe",
  "scap-benchmark",
  "stig",
]);

/**
 * SCAP Status schema
 */
export const scapStatusSchema = z.enum(["active", "inactive", "deprecated"]);

/**
 * SCAP Content Metadata schema
 */
export const scapContentMetadataSchema = z.object({
  publisher: z.string().min(1),
  severity: z.enum(["low", "medium", "high", "critical"]).optional(),
  platforms: z.array(z.string()),
  tags: z.array(z.string()),
  references: z.array(
    z.object({
      url: z.string().url(),
      source: z.string(),
      tags: z.array(z.string()),
    })
  ),
});

/**
 * SCAP Content Content schema
 */
export const scapContentContentSchema = z.object({
  raw: z.string(),
  parsed: z.any(),
  checksum: z.string(),
  size: z.number().int().nonnegative(),
});

/**
 * SCAP Content schema
 * Type inference: z.infer<typeof scapContentSchema>
 */
export const scapContentSchema = z.object({
  id: z.string().min(1),
  title: z.string().min(1),
  description: z.string().min(1),
  type: scapContentTypeSchema,
  version: z.string().min(1),
  status: scapStatusSchema.default("active"),
  source: z.string().min(1),
  publishedDate: z.coerce.date(),
  lastUpdated: z.coerce.date(),
  metadata: scapContentMetadataSchema,
  content: scapContentContentSchema,
  createdAt: z.coerce.date().optional(),
  updatedAt: z.coerce.date().optional(),
});

export type SCAPContent = z.infer<typeof scapContentSchema>;

