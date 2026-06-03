import { headers } from "next/headers";
import { NextResponse } from "next/server";
import { Webhook } from "svix";

/**
 * Clerk Webhook Handler
 * Clerkからのサブスクリプション・支払いイベントを受信
 *
 * 注意: TypeScript側から直接データベースを使用しないため、
 * このWebhookハンドラーは現在無効化されています。
 * 将来的に Connect-Go API 経由で契約・支払いトランザクションを更新する
 * サービスが実装された際に、このハンドラーを有効化してください。
 */
export async function POST(request: Request) {
	const headersList = await headers();
	const webhookSecret = process.env.CLERK_WEBHOOK_SECRET;

	if (!webhookSecret) {
		return NextResponse.json(
			{ error: "Webhook secret not configured" },
			{ status: 500 },
		);
	}

	// Webhook署名検証
	const svixId = headersList.get("svix-id");
	const svixTimestamp = headersList.get("svix-timestamp");
	const svixSignature = headersList.get("svix-signature");

	if (!svixId || !svixTimestamp || !svixSignature) {
		return NextResponse.json(
			{ error: "Missing svix headers" },
			{ status: 400 },
		);
	}

	// リクエストボディを取得（署名検証用に文字列として保持）
	const body = await request.text();

	try {
		// svixで署名検証
		const wh = new Webhook(webhookSecret);
		const payload = wh.verify(body, {
			"svix-id": svixId,
			"svix-timestamp": svixTimestamp,
			"svix-signature": svixSignature,
		}) as {
			type: string;
			data: {
				id: string;
				userId?: string;
				subscriptionId?: string;
				amount?: number;
				currency?: string;
				status?: string;
			};
		};

		const eventType = payload.type;

		console.log(`Received Clerk webhook event: ${eventType}`, payload.data);

		// 署名検証が成功したことを返す
		return NextResponse.json({ received: true, eventType });
	} catch (error) {
		console.error("Webhook error:", error);
		// 署名検証エラーの場合は400、その他のエラーは500
		const errorMessage = error instanceof Error ? error.message : String(error);
		if (errorMessage.toLowerCase().includes("verification") || errorMessage.toLowerCase().includes("signature")) {
			return NextResponse.json({ error: "Invalid signature" }, { status: 400 });
		}
		return NextResponse.json(
			{ error: "Webhook processing failed" },
			{ status: 500 },
		);
	}
}
