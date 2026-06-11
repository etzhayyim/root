import { NextResponse } from "next/server";
import { auth } from "@clerk/nextjs/server";

export const dynamic = 'force-dynamic';

/**
 * Resend APIから受信メール一覧を取得
 * GET /api/admin/resend-emails
 */
export async function GET(request: Request) {
	try {
		// 認証チェック
		const { userId } = await auth();
		if (!userId) {
			return NextResponse.json(
				{ error: "Unauthorized" },
				{ status: 401 },
			);
		}

		// クエリパラメータからlimitを取得
		const { searchParams } = new URL(request.url);
		const limit = searchParams.get("limit") || "100";
		const after = searchParams.get("after") || undefined;
		const before = searchParams.get("before") || undefined;

		// Resend APIから受信メールを取得
		const queryParams = new URLSearchParams({
			limit: limit,
		});
		if (after) {
			queryParams.append("after", after);
		}
		if (before) {
			queryParams.append("before", before);
		}

		return NextResponse.json({
			success: false,
			error: "Unsupported: direct Resend API fetch is disabled. Use a descriptor-backed Connect endpoint.",
			limit,
			after,
			before,
			query: queryParams.toString(),
		}, { status: 501 });
	} catch (error) {
		console.error("Error listing Resend emails:", error);
		return NextResponse.json(
			{
				error: "Failed to list emails",
				message: error instanceof Error ? error.message : "Unknown error",
			},
			{ status: 500 },
		);
	}
}
