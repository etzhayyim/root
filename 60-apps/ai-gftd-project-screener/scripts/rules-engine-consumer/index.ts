/**
 * Main entry point for the Rules Engine Consumer Service.
 * This service is a long-running process that listens for rule changes
 * on a Kafka topic and updates its internal configuration in real-time.
 */
import { startConsumer } from "./kafka/consumer"

async function main() {
  console.log("Starting Rules Engine Consumer Service...")
  try {
    await startConsumer()
    console.log("Consumer started successfully and is listening for messages.")
  } catch (error) {
    console.error("Failed to start the consumer service:", error)
    process.exit(1) // Exit with an error code
  }
}

main()

// Graceful shutdown
process.on("SIGINT", () => {
  console.log("Shutting down consumer service...")
  // Here you would add logic to gracefully disconnect the consumer
  process.exit(0)
})
