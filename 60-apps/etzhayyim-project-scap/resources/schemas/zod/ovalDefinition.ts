/**
 * @fileoverview OVAL Definition Zod schema
 * Zod schema as the single source of truth for OVAL Definition validation
 *
 * @context
 * {
 *   "@context": "https://schema.org",
 *   "@type": "SoftwareApplication",
 *   "name": "OVAL Definition Zod Schema",
 *   "description": "Zod schema for OVAL Definition validation"
 * }
 */

import { z } from "zod";

/**
 * OVAL Class schema
 */
export const ovalClassSchema = z.enum([
  "vulnerability",
  "compliance",
  "inventory",
]);

/**
 * OVAL Criterion schema
 */
export const ovalCriterionSchema = z.object({
  testRef: z.string(),
  comment: z.string(),
});

/**
 * OVAL Criteria schema
 */
export const ovalCriteriaSchema = z.object({
  operator: z.enum(["AND", "OR"]),
  criterion: z.array(ovalCriterionSchema),
});

/**
 * OVAL Affected schema
 */
export const ovalAffectedSchema = z.object({
  family: z.string(),
  platforms: z.array(z.string()),
});

/**
 * OVAL Metadata schema
 */
export const ovalMetadataSchema = z.object({
  title: z.string(),
  affected: z.array(ovalAffectedSchema),
  description: z.string(),
});

/**
 * OVAL Definition schema
 * Type inference: z.infer<typeof ovalDefinitionSchema>
 */
export const ovalDefinitionSchema = z.object({
  id: z.string().min(1),
  title: z.string().min(1),
  description: z.string().min(1),
  class: ovalClassSchema,
  affectedProducts: z.array(z.string()),
  criteria: ovalCriteriaSchema,
  metadata: ovalMetadataSchema,
  createdAt: z.coerce.date().optional(),
  updatedAt: z.coerce.date().optional(),
});

export type OVALDefinition = z.infer<typeof ovalDefinitionSchema>;

