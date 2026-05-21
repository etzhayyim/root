import { NextResponse } from "next/server";
import { auth } from "@clerk/nextjs/server";

export const dynamic = 'force-dynamic';
import { analyzeEmail } from "@/lib/services/email-analyzer";
import { routeRecord } from "@/lib/services/record-router";
import type { EmailContent } from "@/lib/services/email-analyzer";

/**
 * Resendから取得したメールを分類・分析
 * POST /api/admin/classify-emails
 * Body: { emails: ResendReceivedEmail[] }
 */
export async function POST(request: Request) {
	try {
		// 認証チェック
		const { userId } = await auth();
		if (!userId) {
			return NextResponse.json(
				{ error: "Unauthorized" },
				{ status: 401 },
			);
		}

		const body = await request.json();
		const emails = body.emails || [];

		if (!Array.isArray(emails) || emails.length === 0) {
			return NextResponse.json(
				{ error: "No emails provided" },
				{ status: 400 },
			);
		}

		const results = [];

		// 各メールを処理
		for (const email of emails) {
			try {
				// Resendのメール形式をEmailContentに変換
				const emailContent: EmailContent = {
					from: email.from || "",
					to: Array.isArray(email.to) ? email.to[0] || "" : email.to || "",
					subject: email.subject || "",
					html: email.html || null,
					text: email.text || null,
					date: email.createdAt || new Date().toISOString(),
				};

				// メールを分析
				const analysisResult = await analyzeEmail(emailContent);

				if (!analysisResult.success) {
					results.push({
						emailId: email.id,
						success: false,
						error: analysisResult.error || "Analysis failed",
						analysis: null,
						routing: null,
					});
					continue;
				}

				// レコードに振り分け
				const routingResult = await routeRecord(analysisResult);

				results.push({
					emailId: email.id,
					success: true,
					error: null,
					analysis: {
						'entityType': analysisResult.entityType,
						confidence: analysisResult.confidence,
						'extractedData': analysisResult.extractedData,
					},
					routing: {
						success: routingResult.success,
						action: routingResult.action,
						'entityType': routingResult.entityType,
						'entityId': routingResult.entityId,
						message: routingResult.message,
						error: routingResult.error,
					},
				});
			} catch (error) {
				results.push({
					emailId: email.id,
					success: false,
					error: error instanceof Error ? error.message : "Unknown error",
					analysis: null,
					routing: null,
				});
			}
		}

		const successCount = results.filter((r) => r.success).length;
		const failureCount = results.filter((r) => !r.success).length;

		return NextResponse.json({
			success: true,
			processed: emails.length,
			successCount,
			failureCount,
			results,
		});
	} catch (error) {
		console.error("Error classifying emails:", error);
		return NextResponse.json(
			{
				error: "Failed to classify emails",
				message: error instanceof Error ? error.message : "Unknown error",
			},
			{ status: 500 },
		);
	}
}
