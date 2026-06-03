/**
 * @fileoverview SCAP Scan Result Zod schema
 * Zod schema as the single source of truth for SCAP Scan Result validation
 *
 * @context
 * {
 *   "@context": "https://schema.org",
 *   "@type": "SoftwareApplication",
 *   "name": "SCAP Scan Result Zod Schema",
 *   "description": "Zod schema for SCAP Scan Result validation"
 * }
 */

import { z } from "zod";

/**
 * SCAP Scan Status schema
 */
export const scapScanStatusSchema = z.enum([
  "pending",
  "running",
  "completed",
  "failed",
]);

/**
 * SCAP Target Type schema
 */
export const scapTargetTypeSchema = z.enum([
  "host",
  "container",
  "configuration",
]);

/**
 * SCAP Test Result schema
 */
export const scapTestResultSchema = z.object({
  ruleId: z.string(),
  result: z.enum(["pass", "fail", "error", "unknown", "notapplicable"]),
  score: z.number().min(0).max(100),
  message: z.string().optional(),
  details: z.string().optional(),
  timestamp: z.coerce.date(),
});

/**
 * SCAP Scan Summary schema
 */
export const scapScanSummarySchema = z.object({
  totalRules: z.number().int().nonnegative(),
  passedRules: z.number().int().nonnegative(),
  failedRules: z.number().int().nonnegative(),
  errorRules: z.number().int().nonnegative(),
  unknownRules: z.number().int().nonnegative(),
  notApplicableRules: z.number().int().nonnegative(),
  compliancePercentage: z.number().min(0).max(100),
});

/**
 * SCAP Scan Result Metadata schema
 */
export const scapScanResultMetadataSchema = z.object({
  priority: z.enum(["low", "medium", "high"]).optional(),
  requestedAt: z.coerce.date().optional(),
});

/**
 * SCAP Scan Result schema
 * Type inference: z.infer<typeof scapScanResultSchema>
 */
export const scapScanResultSchema = z.object({
  id: z.string().min(1),
  scanId: z.string().min(1),
  integrationId: z.string().min(1),
  targetId: z.string().min(1),
  targetType: scapTargetTypeSchema,
  scapContentId: z.string().min(1),
  executedAt: z.coerce.date(),
  completedAt: z.coerce.date().optional(),
  status: scapScanStatusSchema.default("pending"),
  results: z.array(scapTestResultSchema),
  summary: scapScanSummarySchema,
  metadata: scapScanResultMetadataSchema.optional(),
  createdAt: z.coerce.date().optional(),
  updatedAt: z.coerce.date().optional(),
});

export type SCAPScanResult = z.infer<typeof scapScanResultSchema>;

