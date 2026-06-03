/**
 * @fileoverview Supabase Realtime implementation for SCAP messaging
 * Replaces Kafka producer functionality with Supabase Realtime
 *
 * @context
 * {
 *   "@context": "https://schema.org",
 *   "@type": "SoftwareApplication",
 *   "name": "Supabase Realtime Client",
 *   "description": "Realtime messaging for SCAP data using Supabase Realtime",
 *   "applicationCategory": "Messaging"
 * }
 */

import { supabaseAdmin } from "./client"
import {
  type SCAPContentUpdateMessage,
  type SCAPScanRequestMessage,
  type SCAPFindingMessage,
  type SCAPComplianceReportMessage,
} from "./types"

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
 * Send SCAP content update message via Realtime
 */
export async function sendSCAPContentUpdate(
  message: SCAPContentUpdateMessage
): Promise<void> {
  try {
    const status = await supabaseAdmin.channel(
      REALTIME_CHANNELS.SCAP_CONTENT_UPDATES
    ).send({
      type: "broadcast",
      event: "scapContentUpdate",
      payload: message,
    })

    if (status !== "ok") {
      throw new Error(`Failed to send SCAP content update: ${status}`)
    }
  } catch (error) {
    console.error("Error sending SCAP content update:", error)
    throw error
  }
}

/**
 * Send scan request message via Realtime
 */
export async function sendScanRequest(
  message: SCAPScanRequestMessage
): Promise<void> {
  try {
    const status = await supabaseAdmin.channel(
      REALTIME_CHANNELS.SCAN_REQUESTS
    ).send({
      type: "broadcast",
      event: "scanRequest",
      payload: message,
    })

    if (status !== "ok") {
      throw new Error(`Failed to send scan request: ${status}`)
    }
  } catch (error) {
    console.error("Error sending scan request:", error)
    throw error
  }
}

/**
 * Send finding message via Realtime
 */
export async function sendFinding(message: SCAPFindingMessage): Promise<void> {
  try {
    const status = await supabaseAdmin.channel(
      REALTIME_CHANNELS.FINDINGS
    ).send({
      type: "broadcast",
      event: "finding",
      payload: message,
    })

    if (status !== "ok") {
      throw new Error(`Failed to send finding: ${status}`)
    }
  } catch (error) {
    console.error("Error sending finding:", error)
    throw error
  }
}

/**
 * Send compliance report message via Realtime
 */
export async function sendComplianceReport(
  message: SCAPComplianceReportMessage
): Promise<void> {
  try {
    const status = await supabaseAdmin.channel(
      REALTIME_CHANNELS.COMPLIANCE_REPORTS
    ).send({
      type: "broadcast",
      event: "complianceReport",
      payload: message,
    })

    if (status !== "ok") {
      throw new Error(`Failed to send compliance report: ${status}`)
    }
  } catch (error) {
    console.error("Error sending compliance report:", error)
    throw error
  }
}

/**
 * Send batch messages to a specific channel
 */
export async function sendBatch(
  channel: string,
  messages: unknown[]
): Promise<void> {
  try {
    const channelInstance = supabaseAdmin.channel(channel)

    for (const message of messages) {
      const status = await channelInstance.send({
        type: "broadcast",
        event: "batchMessage",
        payload: message,
      })

      if (status !== "ok") {
        console.error(`Failed to send batch message to ${channel}:`, status)
      }
    }
  } catch (error) {
    console.error(`Error sending batch to ${channel}:`, error)
    throw error
  }
}

/**
 * Supabase Realtime Producer (replaces Kafka producer)
 */
export const scapRealtimeProducer = {
  sendSCAPContentUpdate,
  sendScanRequest,
  sendFinding,
  sendComplianceReport,
  sendBatch,
}
