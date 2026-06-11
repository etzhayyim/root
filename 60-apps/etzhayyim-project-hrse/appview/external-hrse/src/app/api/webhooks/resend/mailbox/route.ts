import { NextResponse } from "next/server";
import { getMailboxServiceClient } from "@/lib/connect/server-client";
import { create } from "@bufbuild/protobuf";
import {
	GetMailboxByEmailRequestSchema,
	CreateMessageThreadRequestSchema,
	ListThreadsRequestSchema,
	CreateMailboxMessageRequestSchema,
	GetLLMSuggestionRequestSchema,
	type MessageThread,
} from "@/gen/proto/hrse/v1/mailbox_pb";

/**
 * Resend Mailbox Webhook Handler
 * Processes inbound emails to mailbox addresses and creates threads/messages
 */
export async function POST(request: Request) {
	const headersList = request.headers;
	const webhookSecret = process.env.RESEND_WEBHOOK_SECRET;

	if (!webhookSecret) {
		console.error("RESEND_WEBHOOK_SECRET is not configured");
		return NextResponse.json(
			{ error: "Webhook secret not configured" },
			{ status: 500 },
		);
	}

	try {
		// Resend Webhook signature verification
		const signature = headersList.get("resend-signature") || null;
		if (!signature) {
			return NextResponse.json(
				{ error: "Missing signature header" },
				{ status: 400 },
			);
		}

		// Get request body
		const body = await request.json();

		// Signature verification (simplified - adjust per Resend docs)
		const expectedSignature = await verifyResendSignature(
			JSON.stringify(body),
			webhookSecret,
		);

		if (signature !== expectedSignature) {
			return NextResponse.json(
				{ error: "Invalid signature" },
				{ status: 401 },
			);
		}

		// Check event type
		const eventType = body.type;
		if (eventType !== "email.received") {
			// Ignore non-receive events
			return NextResponse.json({ received: true });
		}

		// Extract email data
		const emailData = body.data;
		if (!emailData) {
			return NextResponse.json(
				{ error: "Missing email data" },
				{ status: 400 },
			);
		}

		const toEmail = emailData.to || "";
		const fromEmail = emailData.from || "";
		const subject = emailData.subject || "";
		const html = emailData.html || "";
		const text = emailData.text || "";

		// Extract email address from "To" field (handle "Name <email@domain.com>" format)
		const toEmailMatch = toEmail.match(/<([^>]+)>/) || toEmail.match(/([^\s<]+@[^\s>]+)/);
		const targetEmail = toEmailMatch ? toEmailMatch[1] : toEmail;

		// Check if this is a mailbox address (@mail.etzhayyim.com)
		if (!targetEmail.includes("@mail.etzhayyim.com")) {
			// Not a mailbox email, ignore
			return NextResponse.json({ received: true, message: "Not a mailbox email" });
		}

		// Get mailbox by email address
		const mailboxClient = await getMailboxServiceClient();
		const mailboxResponse = await mailboxClient.getMailboxByEmail(
			create(GetMailboxByEmailRequestSchema, {
				emailAddress: targetEmail,
			}),
		);

		if (!mailboxResponse.mailbox) {
			console.error(`Mailbox not found for email: ${targetEmail}`);
			return NextResponse.json(
				{ error: "Mailbox not found" },
				{ status: 404 },
			);
		}

		const mailboxId = mailboxResponse.mailbox.id;

		// Check if this is a reply to an existing thread (check In-Reply-To header)
		const inReplyTo = emailData.headers?.["in-reply-to"] || emailData.headers?.["In-Reply-To"];
		let threadId: string | undefined;

		if (inReplyTo) {
			// Try to find existing thread by message ID or subject
			// For now, we'll search by subject prefix (Re:)
			const subjectPrefix = subject.replace(/^Re:\s*/i, "").trim();
			const threadsResponse = await mailboxClient.listThreads(
				create(ListThreadsRequestSchema, {
					mailboxId,
					limit: 10,
					offset: 0,
				}),
			);

			// Find thread with matching subject
			const matchingThread = threadsResponse.threads.find(
				(t: MessageThread) => t.subject.toLowerCase().includes(subjectPrefix.toLowerCase()) ||
					subjectPrefix.toLowerCase().includes(t.subject.toLowerCase()),
			);

			if (matchingThread) {
				threadId = matchingThread.id;
			}
		}

		// If no existing thread, create a new one
		if (!threadId) {
			// Classify email using LLM (talent or job)
			const classification = await classifyEmail(subject, text || html);

			// Create new thread
			const threadResponse = await mailboxClient.createMessageThread(
				create(CreateMessageThreadRequestSchema, {
					mailboxId,
					subject: subject || "(No Subject)",
					classification: classification || undefined,
				}),
			);

			threadId = threadResponse.thread.id;

			// Generate LLM suggestion for new thread
			try {
				await mailboxClient.getLLMSuggestion(
					create(GetLLMSuggestionRequestSchema, {
						threadId,
					}),
				);
			} catch (error) {
				console.error("Failed to generate LLM suggestion:", error);
				// Continue without suggestion
			}
		}

		// Create message record
		const messageResponse = await mailboxClient.createMailboxMessage(
			create(CreateMailboxMessageRequestSchema, {
				threadId,
				direction: "inbound",
				fromEmail,
				toEmail: targetEmail,
				subject: subject || undefined,
				bodyHtml: html || undefined,
				bodyText: text || undefined,
			}),
		);

		// Update thread lastMessageAt
		// (This is handled by the service, but we can also trigger it here)

		return NextResponse.json({
			received: true,
			message: "Email processed successfully",
			mailboxId,
			threadId,
			messageId: messageResponse.message.id,
		});
	} catch (error) {
		console.error("Mailbox webhook error:", error);
		return NextResponse.json(
			{
				error: "Webhook processing failed",
				message: error instanceof Error ? error.message : "Unknown error",
			},
			{ status: 500 },
		);
	}
}

/**
 * Classify email as "talent" or "job" using LLM
 */
async function classifyEmail(
	subject: string,
	body: string,
): Promise<"talent" | "job" | null> {
	try {
		void subject;
		void body;

		console.warn(
			"Unsupported: direct LLM chat completion fetch is disabled in webhook classifier. Classification fallback is null."
		);
		return null;
	} catch (error) {
		console.error("Email classification error:", error);
		return null;
	}
}

/**
 * Resend Webhook signature verification
 */
async function verifyResendSignature(
	payload: string,
	secret: string,
): Promise<string> {
	const encoder = new TextEncoder();
	const keyData = encoder.encode(secret);
	const messageData = encoder.encode(payload);

	const cryptoKey = await crypto.subtle.importKey(
		"raw",
		keyData,
		{ name: "HMAC", hash: "SHA-256" },
		false,
		["sign"],
	);

	const signature = await crypto.subtle.sign("HMAC", cryptoKey, messageData);
	const hashArray = Array.from(new Uint8Array(signature));
	const hashHex = hashArray.map((b) => b.toString(16).padStart(2, "0")).join("");

	return hashHex;
}

