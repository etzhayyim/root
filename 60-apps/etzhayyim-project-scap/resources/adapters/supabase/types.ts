/**
 * @fileoverview Supabase types and Realtime message types
 *
 * @context
 * {
 *   "@context": "https://schema.org",
 *   "@type": "SoftwareApplication",
 *   "name": "Supabase Types",
 *   "description": "Type definitions for Supabase database and Realtime messages"
 * }
 */

import type { SCAPContentType } from "@/ports/types/types"

/**
 * Database schema types
 * This will be extended with actual schema types from Supabase
 */
export type Database = {
  public: {
    Tables: {
      'scapContents': {
        Row: Record<string, unknown>
        Insert: Record<string, unknown>
        Update: Record<string, unknown>
      }
      'cveData': {
        Row: Record<string, unknown>
        Insert: Record<string, unknown>
        Update: Record<string, unknown>
      }
      'ovalDefinitions': {
        Row: Record<string, unknown>
        Insert: Record<string, unknown>
        Update: Record<string, unknown>
      }
      'scapScanResults': {
        Row: Record<string, unknown>
        Insert: Record<string, unknown>
        Update: Record<string, unknown>
      }
      integrations: {
        Row: Record<string, unknown>
        Insert: Record<string, unknown>
        Update: Record<string, unknown>
      }
      'scapDataSources': {
        Row: Record<string, unknown>
        Insert: Record<string, unknown>
        Update: Record<string, unknown>
      }
    }
  }
}

/**
 * Realtime channel names
 */
export const REALTIME_CHANNELS = {
  SCAP_CONTENT_UPDATES: "scapContentUpdates",
  SCAN_REQUESTS: "scanRequests",
  FINDINGS: "findings",
  COMPLIANCE_REPORTS: "complianceReports",
} as const

/**
 * Base Realtime message type
 */
export interface SCAPRealtimeMessage {
  messageType: string
  timestamp: string
  source: string
}

/**
 * SCAP Content Update message
 */
export interface SCAPContentUpdateMessage extends SCAPRealtimeMessage {
  messageType: "scapContentUpdate"
  data: {
    contentId: string
    contentType: SCAPContentType
    action: "created" | "updated" | "deleted"
    content: unknown
  }
}

/**
 * Scan Request message
 */
export interface SCAPScanRequestMessage extends SCAPRealtimeMessage {
  messageType: "scanRequest"
  data: {
    integrationId: string
    targetId: string
    scapContentIds: string[]
    priority: "low" | "medium" | "high"
  }
}

/**
 * Finding message
 */
export interface SCAPFindingMessage extends SCAPRealtimeMessage {
  messageType: "finding"
  data: {
    findingId: string
    scanResultId: string
    integrationId: string
    severity: "low" | "medium" | "high" | "critical"
    ruleId: string
    title: string
    description: string
    remediation: string
    affectedResources: string[]
    complianceFrameworks: string[]
  }
}

/**
 * Compliance Report message
 */
export interface SCAPComplianceReportMessage extends SCAPRealtimeMessage {
  messageType: "complianceReport"
  data: {
    reportId: string
    timestamp: string
    statistics: unknown
    dataSourceStatus: unknown[]
    recommendations: string[]
  }
}

/**
 * Union type for all Realtime messages
 */
export type SCAPRealtimeMessageUnion =
  | SCAPContentUpdateMessage
  | SCAPScanRequestMessage
  | SCAPFindingMessage
  | SCAPComplianceReportMessage

