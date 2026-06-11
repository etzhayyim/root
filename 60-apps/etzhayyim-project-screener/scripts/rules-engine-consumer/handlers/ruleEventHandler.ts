import { getCurrentConfig, updateConfig } from "../config/rules"

// This defines the structure of the event payload we expect
interface RuleChangeEvent {
  eventType: "RuleConfigurationChanged"
  payload: {
    ruleType: "TRANSACTION_MONITORING" | "NAME_SCREENING" | "COUNTRY_RISK"
    [key: string]: any
  }
}

export async function handleRuleEvent(event: RuleChangeEvent) {
  console.log(`Processing event type: ${event.eventType} for rule: ${event.payload.ruleType}`)

  const oldConfig = JSON.parse(JSON.stringify(getCurrentConfig())) // Deep copy for logging

  switch (event.payload.ruleType) {
    case "TRANSACTION_MONITORING":
      const newThreshold = event.payload.singleTransactionThreshold
      if (typeof newThreshold === "number") {
        console.log(`  -> Updating Single Transaction Threshold.`)
        console.log(`     Old value: ${oldConfig.transactionMonitoring.singleTransactionThreshold}`)
        console.log(`     New value: ${newThreshold}`)
        updateConfig({
          transactionMonitoring: { singleTransactionThreshold: newThreshold },
        })
      }
      break

    // Add cases for other rule types here
    // case 'NAME_SCREENING':
    //   ...
    //   break;

    default:
      console.warn(`  -> Unknown ruleType received: ${event.payload.ruleType}. No action taken.`)
      break
  }

  console.log("--- Current Live Configuration ---")
  console.log(JSON.stringify(getCurrentConfig(), null, 2))
  console.log("----------------------------------")
}
