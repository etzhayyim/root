/**
 * @fileoverview SCAP Data Source Zod schema
 * Zod schema as the single source of truth for SCAP Data Source validation
 *
 * @context
 * {
 *   "@context": "https://schema.org",
 *   "@type": "SoftwareApplication",
 *   "name": "SCAP Data Source Zod Schema",
 *   "description": "Zod schema for SCAP Data Source validation"
 * }
 */

import { z } from "zod";

/**
 * SCAP Content Type schema (re-exported)
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
 * SCAP Data Source Type schema
 */
export const scapDataSourceTypeSchema = z.enum([
  "nist",
  "mitre",
  "oval",
  "custom",
]);

/**
 * SCAP Data Source Status schema
 */
export const scapDataSourceStatusSchema = z.enum(["active", "inactive"]);

/**
 * SCAP Data Source Update Frequency schema
 */
export const scapDataSourceUpdateFrequencySchema = z.enum([
  "hourly",
  "daily",
  "weekly",
  "monthly",
]);

/**
 * SCAP Data Source schema
 * Type inference: z.infer<typeof scapDataSourceSchema>
 */
export const scapDataSourceSchema = z.object({
  id: z.string().min(1),
  name: z.string().min(1),
  type: scapDataSourceTypeSchema,
  url: z.string().url(),
  updateFrequency: scapDataSourceUpdateFrequencySchema.default("daily"),
  status: scapDataSourceStatusSchema.default("active"),
  contentTypes: z.array(scapContentTypeSchema),
  lastSync: z.coerce.date().optional(),
  createdAt: z.coerce.date().optional(),
  updatedAt: z.coerce.date().optional(),
});

export type SCAPDataSource = z.infer<typeof scapDataSourceSchema>;

