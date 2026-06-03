/**
 * @fileoverview Zod schema index
 * Exports all Zod schemas and types
 *
 * @context
 * {
 *   "@context": "https://schema.org",
 *   "@type": "SoftwareApplication",
 *   "name": "Zod Schema Index",
 *   "applicationCategory": "Validation"
 * }
 */

export * from "./scapContent";
export * from "./cveData";
export * from "./ovalDefinition";
export * from "./scapScanResult";
export * from "./integration";
export {
  scapDataSourceSchema,
  scapDataSourceTypeSchema,
  scapDataSourceStatusSchema,
  scapDataSourceUpdateFrequencySchema,
} from "./scapDataSource";
export type { SCAPDataSource } from "./scapDataSource";
