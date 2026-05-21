/**
 * This module holds the in-memory configuration for the screening rules.
 * It is updated by the event handler when new rule change events are consumed.
 * Any part of the application that performs screening will read from this config.
 */

interface RuleConfig {
  transactionMonitoring: {
    singleTransactionThreshold: number
  }
  nameScreening: {
    alertThreshold: number
  }
  countryRisk: {
    highRiskCountries: string[]
  }
}

// Default configuration
const config: RuleConfig = {
  transactionMonitoring: {
    singleTransactionThreshold: 10000, // Default value
  },
  nameScreening: {
    alertThreshold: 90,
  },
  countryRisk: {
    highRiskCountries: ["North Korea", "Iran"],
  },
}

export function getCurrentConfig(): Readonly<RuleConfig> {
  return config
}

export function updateConfig(newConfig: Partial<RuleConfig>) {
  // A more robust implementation might use a deep merge library
  if (newConfig.transactionMonitoring) {
    config.transactionMonitoring = { ...config.transactionMonitoring, ...newConfig.transactionMonitoring }
  }
  if (newConfig.nameScreening) {
    config.nameScreening = { ...config.nameScreening, ...newConfig.nameScreening }
  }
  if (newConfig.countryRisk) {
    config.countryRisk = { ...config.countryRisk, ...newConfig.countryRisk }
  }
  console.log("In-memory configuration updated.")
}
