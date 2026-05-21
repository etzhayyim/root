import { NextResponse } from "next/server"
import { executeKsqlQuery } from "@/lib/ksqldb-client"

interface Transaction {
  transactionId: string
  amount: number
  currency: string
  customerId: string
}

interface TransactionRule {
  RULE_TYPE: string
  THRESHOLD: number
}

/**
 * This API endpoint simulates a transaction screening service.
 * It receives transaction data, fetches the latest rule threshold from ksqlDB,
 * and then applies the rule to screen the transaction.
 */
export async function POST(request: Request) {
  try {
    const transaction: Transaction = await request.json()

    if (!transaction.transactionId || !transaction.amount) {
      return NextResponse.json({ message: "Invalid transaction data provided." }, { status: 400 })
    }

    // 1. Define the ksqlDB query to get the latest rule.
    // We assume you have a TABLE named 'currentRules' as designed previously.
    const ksql = `SELECT THRESHOLD FROM currentRules WHERE RULE_TYPE = 'TRANSACTION_MONITORING';`

    console.log(`Executing ksqlDB query to fetch transaction threshold: ${ksql}`)

    // 2. Execute the query using our client
    const results = await executeKsqlQuery<TransactionRule>(ksql)

    // 3. Extract the threshold from the query result.
    // Use a default value if the rule is not found for any reason.
    const threshold = results.length > 0 ? results[0].THRESHOLD : 10000 // Default threshold
    console.log(`Current live transaction threshold is: ${threshold}`)

    // 4. Apply the rule to the incoming transaction
    let isFlagged = false
    let reason = "Transaction amount is within the acceptable limit."

    if (transaction.amount > threshold) {
      isFlagged = true
      reason = `Transaction amount of ${transaction.amount} exceeds the current threshold of ${threshold}.`
    }

    // 5. Return the screening result
    const screeningResult = {
      transactionId: transaction.transactionId,
      isFlagged,
      reason,
      appliedThreshold: threshold,
      timestamp: new Date().toISOString(),
    }

    return NextResponse.json(screeningResult)
  } catch (error) {
    console.error("An error occurred during transaction screening:", error)
    return NextResponse.json({ message: "Internal Server Error during screening." }, { status: 500 })
  }
}
