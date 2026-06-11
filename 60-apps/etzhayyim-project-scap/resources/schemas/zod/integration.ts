/**
 * @fileoverview Integration Zod schema
 * Zod schema as the single source of truth for Integration validation
 *
 * @context
 * {
 *   "@context": "https://schema.org",
 *   "@type": "SoftwareApplication",
 *   "name": "Integration Zod Schema",
 *   "description": "Zod schema for Integration validation"
 * }
 */

import { z } from "zod";

/**
 * Integration Type schema
 */
export const integrationTypeSchema = z.enum([
  "aws",
  "gcp",
  "azure",
  "github",
  "gitlab",
]);

/**
 * Integration Status schema
 */
export const integrationStatusSchema = z.enum(["active", "inactive"]);

/**
 * Integration schema
 * Type inference: z.infer<typeof integrationSchema>
 */
export const integrationSchema = z.object({
  id: z.string().min(1),
  type: integrationTypeSchema,
  name: z.string().min(1),
  status: integrationStatusSchema.default("active"),
  config: z.record(z.any()),
  createdAt: z.coerce.date().optional(),
  updatedAt: z.coerce.date().optional(),
});

export type Integration = z.infer<typeof integrationSchema>;

