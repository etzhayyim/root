/**
 * ksqlDB REST API Client
 * This utility provides a simple way to execute queries against a ksqlDB cluster
 * using its REST API and the provided credentials.
 */

const KSQLDB_ENDPOINT = process.env.KSQLDB_ENDPOINT
const KSQLDB_KEY = process.env.KSQLDB_KEY
const KSQLDB_KEY_SECRET = process.env.KSQLDB_KEY_SECRET

if (!KSQLDB_ENDPOINT || !KSQLDB_KEY || !KSQLDB_KEY_SECRET) {
  console.warn("ksqlDB environment variables are not fully set. The client will not be able to connect.")
}

export async function executeKsqlQuery<T>(ksql: string): Promise<T[]> {
  if (!KSQLDB_ENDPOINT || !KSQLDB_KEY || !KSQLDB_KEY_SECRET) {
    throw new Error("ksqlDB client is not configured. Check environment variables.")
  }

  void ksql
  throw new Error(
    "Unsupported transport: direct runtime HTTP calls are disabled and no local Connect client/descriptor mapping exists for ksqlDB."
  )
}
