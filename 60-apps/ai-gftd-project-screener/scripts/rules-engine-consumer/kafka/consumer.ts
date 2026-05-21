import { Kafka, logLevel } from "kafkajs"
import { handleRuleEvent } from "../handlers/ruleEventHandler"

// In a real environment, these would come from environment variables
const KAFKA_BROKERS = process.env.KAFKA_BROKERS?.split(",") || ["localhost:9092"]
const KAFKA_TOPIC = "aml.rules.configuration.events"

// Initialize the Kafka client
const kafka = new Kafka({
  clientId: "rules-engine-consumer-service",
  brokers: KAFKA_BROKERS,
  logLevel: logLevel.INFO, // Adjust log level as needed
})

const consumer = kafka.consumer({ groupId: "rules-engine-service-group" })

export async function startConsumer() {
  await consumer.connect()
  console.log(`Connected to Kafka brokers: ${KAFKA_BROKERS.join(", ")}`)

  await consumer.subscribe({ topic: KAFKA_TOPIC, fromBeginning: true })
  console.log(`Subscribed to topic: ${KAFKA_TOPIC}`)

  await consumer.run({
    eachMessage: async ({ topic, partition, message }) => {
      if (!message.value) {
        console.warn("Received message with no value.")
        return
      }

      console.log(`\n--- New Message Received from topic: ${topic} ---`)
      try {
        const event = JSON.parse(message.value.toString())

        // Delegate processing to the event handler
        await handleRuleEvent(event)
      } catch (error) {
        console.error("Error processing message:", error)
        // In a real system, you might move this message to a dead-letter queue
      }
    },
  })
}
