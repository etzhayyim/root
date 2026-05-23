import { NextResponse } from "next/server";
import { analyzeEmail } from "@/lib/services/email-analyzer";
import { routeRecord } from "@/lib/services/record-router";

/**
 * Resend Webhook Handler
 * Resendから受信したメールをLLMで分析し、レコードに自動振り分け・追加・更新
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
		// Resend Webhook署名検証
		const signature = headersList.get("resend-signature") || null;
		if (!signature) {
			return NextResponse.json(
				{ error: "Missing signature header" },
				{ status: 400 },
			);
		}

		// リクエストボディを取得
		const body = await request.json();

		// 署名検証（Resendの署名検証メカニズム）
		// 注意: Resendの実際の署名検証方法は公式ドキュメントを参照してください
		// ここでは簡易的な実装とします
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

		// イベントタイプを確認
		const eventType = body.type;
		if (eventType !== "email.received") {
			// メール受信イベント以外は無視
			return NextResponse.json({ received: true });
		}

		// メールデータを抽出
		const emailData = body.data;
		if (!emailData) {
			return NextResponse.json(
				{ error: "Missing email data" },
				{ status: 400 },
			);
		}

		const emailContent = {
			from: emailData.from || "",
			to: emailData.to || "",
			subject: emailData.subject || "",
			html: emailData.html || "",
			text: emailData.text || "",
			date: emailData.date || new Date().toISOString(),
		};

		// メールを分析
		const analysisResult = await analyzeEmail(emailContent);
		if (!analysisResult.success) {
			console.error("Email analysis failed:", analysisResult.error);
			return NextResponse.json({
				received: true,
				error: "Analysis failed",
				message: analysisResult.error || "Unknown error",
			});
		}

		// レコードに振り分け
		const routingResult = await routeRecord(analysisResult);
		if (!routingResult.success) {
			console.error("Record routing failed:", routingResult.error);
			return NextResponse.json({
				received: true,
				error: "Routing failed",
				message: routingResult.error || "Unknown error",
			});
		}

		// Check if this is a reply to an existing email conversation
		// Analyze the reply using EmailAgentService if it's a reply
		try {
			const { getEmailAgentServiceClient } = await import("@/lib/connect/server-client");
			const emailAgentClient = await getEmailAgentServiceClient();
			const { create } = await import("@bufbuild/protobuf");
			const { AnalyzeEmailReplyRequestSchema } = await import("@/gen/proto/hrse/v1/emailAgentPb");

			// Analyze email reply
			const replyAnalysis = await emailAgentClient.analyzeEmailReply(
				create(AnalyzeEmailReplyRequestSchema, {
					subject: emailContent.subject,
					bodyHtml: emailContent.html,
					bodyText: emailContent.text,
				})
			);

			// If this is a reply (intent is "reply", "scheduleMeeting", "negotiateConditions", etc.)
			// and it's related to an existing conversation, save it to emailMessages table
			if (replyAnalysis.intent !== "other" && replyAnalysis.intent !== "requestInfo") {
				console.log("Email reply analyzed:", {
					intent: replyAnalysis.intent,
					confidence: replyAnalysis.confidence,
					extractedData: replyAnalysis.extractedData,
				});

				// In production, you would:
				// 1. Find the conversationId based on the email thread (In-Reply-To header, etc.)
				// 2. Create an inbound emailMessages entry with status 'pendingReview'
				// 3. Generate a reply email using GenerateReplyEmail if needed
			}
		} catch (error) {
			// Log error but don't fail the webhook processing
			console.error("Failed to analyze email reply:", error);
		}

		return NextResponse.json({
			received: true,
			message: "Email processed successfully",
			action: routingResult.action,
			'entityType': routingResult.entityType,
			'entityId': routingResult.entityId,
		});
	} catch (error) {
		console.error("Resend webhook error:", error);
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
 * Resend Webhook署名検証
 * 注意: 実際のResendの署名検証方法は公式ドキュメントを参照してください
 * ここでは簡易的な実装とします
 */
async function verifyResendSignature(
	payload: string,
	secret: string,
): Promise<string> {
	// 実際のResendの署名検証ロジックを実装
	// 現在は簡易的な実装として、HMAC-SHA256を使用
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
